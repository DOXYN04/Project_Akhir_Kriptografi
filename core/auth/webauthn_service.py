"""
core/auth/webauthn_service.py — Registrasi & verifikasi WebAuthn (py_webauthn).
"""

import os
import time
import base64
from typing import Optional

import webauthn
from webauthn.helpers.structs import (
    AttestationConveyancePreference,
    AuthenticatorSelectionCriteria,
    ResidentKeyRequirement,
    UserVerificationRequirement,
)
from webauthn.helpers import bytes_to_base64url, base64url_to_bytes

import config
from core.db import database as db


# ── Penyimpanan challenge sementara (in-memory, per sesi) ─────────────────────
# Di produksi gunakan Redis/DB; di sini cukup dict dengan TTL sederhana.
_pending_challenges: dict[str, tuple[bytes, float]] = {}


def _store_challenge(key: str, challenge: bytes) -> None:
    """Simpan challenge dengan TTL 120 detik."""
    _pending_challenges[key] = (challenge, time.time() + 120)


def _pop_challenge(key: str) -> Optional[bytes]:
    """Ambil dan hapus challenge; kembalikan None bila tidak ada atau kadaluarsa."""
    entry = _pending_challenges.pop(key, None)
    if entry is None:
        return None
    challenge, expires = entry
    if time.time() > expires:
        return None
    return challenge


# ── Registrasi ────────────────────────────────────────────────────────────────

def generate_registration_options(user_name: str, user_id: int) -> dict:
    """
    Buat opsi registrasi WebAuthn dan simpan challenge.
    Kembalikan dict yang bisa di-JSON-kan untuk dikirim ke frontend.
    """
    challenge = os.urandom(32)
    _store_challenge(f"reg:{user_id}", challenge)

    opts = webauthn.generate_registration_options(
        rp_id=config.RP_ID,
        rp_name=config.RP_NAME,
        user_name=user_name,
        user_id=str(user_id).encode(),
        challenge=challenge,
        attestation=AttestationConveyancePreference.NONE,
        authenticator_selection=AuthenticatorSelectionCriteria(
            resident_key=ResidentKeyRequirement.PREFERRED,
            user_verification=UserVerificationRequirement.REQUIRED,
        ),
    )
    return webauthn.options_to_json(opts)


def verify_registration(user_id: int, credential: dict) -> tuple[bytes, bytes]:
    """
    Verifikasi respons registrasi dari browser.
    Kembalikan (credential_id, public_key_bytes).
    Lempar ValueError bila verifikasi gagal.
    """
    challenge = _pop_challenge(f"reg:{user_id}")
    if challenge is None:
        raise ValueError("Challenge tidak ditemukan atau sudah kadaluarsa.")

    try:
        verification = webauthn.verify_registration_response(
            credential=credential,
            expected_challenge=challenge,
            expected_rp_id=config.RP_ID,
            expected_origin=config.ORIGIN,
            require_user_verification=True,
        )
    except Exception as exc:
        raise ValueError(f"Registrasi ditolak: {exc}") from exc

    return (
        verification.credential_id,
        verification.credential_public_key,
    )


# ── Authentication ────────────────────────────────────────────────────────────

def generate_authentication_options(user_id: int, credential_id: bytes) -> dict:
    """Buat opsi autentikasi WebAuthn dan simpan challenge."""
    challenge = os.urandom(32)
    _store_challenge(f"auth:{user_id}", challenge)

    opts = webauthn.generate_authentication_options(
        rp_id=config.RP_ID,
        challenge=challenge,
        allow_credentials=[
            webauthn.helpers.structs.PublicKeyCredentialDescriptor(id=credential_id)
        ],
        user_verification=UserVerificationRequirement.REQUIRED,
    )
    return webauthn.options_to_json(opts)


def verify_authentication(
    user_id: int,
    credential: dict,
    stored_public_key: bytes,
    sign_count: int,
) -> int:
    """
    Verifikasi respons autentikasi.
    Kembalikan sign_count baru.
    Lempar ValueError bila verifikasi gagal.
    """
    challenge = _pop_challenge(f"auth:{user_id}")
    if challenge is None:
        raise ValueError("Challenge tidak ditemukan atau sudah kadaluarsa.")

    try:
        verification = webauthn.verify_authentication_response(
            credential=credential,
            expected_challenge=challenge,
            expected_rp_id=config.RP_ID,
            expected_origin=config.ORIGIN,
            credential_public_key=stored_public_key,
            credential_current_sign_count=sign_count,
            require_user_verification=True,
        )
    except Exception as exc:
        raise ValueError(f"Autentikasi ditolak: {exc}") from exc

    return verification.new_sign_count
