"""
core/auth/kdf.py — Key Derivation Functions: Argon2id, HKDF-SHA256.
"""

import os
import hashlib
from typing import Optional

from argon2 import PasswordHasher, exceptions as argon2_exc
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives import hashes


# ── Argon2id ──────────────────────────────────────────────────────────────────
_PH = PasswordHasher(
    time_cost=3,
    memory_cost=65536,   # 64 MiB
    parallelism=2,
    hash_len=32,
    salt_len=16,
)


def hash_pin(pin: str) -> str:
    """Hash PIN/passphrase dengan Argon2id. Kembalikan string encoded."""
    return _PH.hash(pin)


def verify_pin(pin: str, stored_hash: str) -> bool:
    """Verifikasi PIN terhadap hash tersimpan. Kembalikan bool."""
    try:
        _PH.verify(stored_hash, pin)
        return True
    except argon2_exc.VerifyMismatchError:
        return False
    except argon2_exc.VerificationError:
        return False


def derive_master_key(secret: bytes, salt: bytes) -> bytes:
    """
    Turunkan master key 32 byte dari secret (hasil login) dan salt tersimpan
    menggunakan HKDF-SHA256.
    """
    hkdf = HKDF(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        info=b"obsidian-vault-master-key",
    )
    return hkdf.derive(secret)


def hkdf_derive(master_key: bytes, info: bytes, length: int = 32) -> bytes:
    """
    Turunkan sub-kunci dari master_key dengan label (info) unik.
    Gunakan untuk domain separation antar modul.

    Contoh:
        key_vigenere = hkdf_derive(master_key, b"text-vigenere", 16)
        key_aes      = hkdf_derive(master_key, b"text-aes",      32)
    """
    hkdf = HKDF(
        algorithm=hashes.SHA256(),
        length=length,
        salt=None,
        info=info,
    )
    return hkdf.derive(master_key)


def generate_salt(length: int = 16) -> bytes:
    """Buat salt acak sejumlah `length` byte."""
    return os.urandom(length)
