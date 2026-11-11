"""
core/crypto/modern.py — Wrapper AEAD modern:
  - AES-256-GCM
  - ChaCha20-Poly1305

Semua enkripsi memakai nonce acak unik (os.urandom).
Tag otomatis diverifikasi saat dekripsi.
"""

import os
from cryptography.hazmat.primitives.ciphers.aead import AESGCM, ChaCha20Poly1305


# ── AES-256-GCM ───────────────────────────────────────────────────────────────

def aes_gcm_encrypt(
    key: bytes, plaintext: bytes, aad: bytes | None = None
) -> tuple[bytes, bytes]:
    """
    Enkripsi dengan AES-256-GCM.
    Kembalikan (nonce, ciphertext+tag).
    """
    if len(key) != 32:
        raise ValueError("Kunci AES-256-GCM harus 32 byte.")
    nonce = os.urandom(12)
    aesgcm = AESGCM(key)
    ct = aesgcm.encrypt(nonce, plaintext, aad)
    return nonce, ct


def aes_gcm_decrypt(
    key: bytes, nonce: bytes, ciphertext: bytes, aad: bytes | None = None
) -> bytes:
    """
    Dekripsi dan verifikasi tag AES-256-GCM.
    Lempar ValueError bila tag tidak valid.
    """
    if len(key) != 32:
        raise ValueError("Kunci AES-256-GCM harus 32 byte.")
    aesgcm = AESGCM(key)
    try:
        return aesgcm.decrypt(nonce, ciphertext, aad)
    except Exception as exc:
        raise ValueError("Dekripsi AES-GCM gagal — tag tidak valid atau data rusak.") from exc


# ── ChaCha20-Poly1305 ─────────────────────────────────────────────────────────

def chacha_encrypt(
    key: bytes, plaintext: bytes, aad: bytes | None = None
) -> tuple[bytes, bytes]:
    """
    Enkripsi dengan ChaCha20-Poly1305.
    Kembalikan (nonce, ciphertext+tag).
    """
    if len(key) != 32:
        raise ValueError("Kunci ChaCha20-Poly1305 harus 32 byte.")
    nonce = os.urandom(12)
    chacha = ChaCha20Poly1305(key)
    ct = chacha.encrypt(nonce, plaintext, aad)
    return nonce, ct


def chacha_decrypt(
    key: bytes, nonce: bytes, ciphertext: bytes, aad: bytes | None = None
) -> bytes:
    """
    Dekripsi dan verifikasi tag ChaCha20-Poly1305.
    Lempar ValueError bila tag tidak valid.
    """
    if len(key) != 32:
        raise ValueError("Kunci ChaCha20-Poly1305 harus 32 byte.")
    chacha = ChaCha20Poly1305(key)
    try:
        return chacha.decrypt(nonce, ciphertext, aad)
    except Exception as exc:
        raise ValueError("Dekripsi ChaCha20 gagal — tag tidak valid atau data rusak.") from exc
