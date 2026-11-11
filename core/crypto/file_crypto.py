"""
core/crypto/file_crypto.py — Enkripsi file dengan ChaCha20-Poly1305 (chunked).

Format .vault:
  magic(4B "OVLT") | version(1B) | nonce_prefix(4B) | wrapped_key(60B) |
  orig_filename_enc_len(2B) | orig_filename_enc | chunks...

Setiap chunk:
  chunk_len(4B) | nonce(12B) | ciphertext+tag
  nonce = nonce_prefix(4B) | counter(8B)
  AAD chunk = b"chunk:" | counter(8B) | b":last" jika chunk terakhir

Wrapped key: file key 32B dibungkus dengan AES-256-GCM master_key.
  Format: nonce(12B) + ct+tag(48B) = 60B
"""

import os
import struct
import hashlib
from pathlib import Path
from typing import Iterator

from cryptography.hazmat.primitives.ciphers.aead import AESGCM, ChaCha20Poly1305

from core.auth.kdf import hkdf_derive

MAGIC = b"OVLT"
VERSION = 1
CHUNK_SIZE = 64 * 1024   # 64 KiB


def _wrap_key(file_key: bytes, master_key: bytes) -> bytes:
    """Bungkus file_key dengan AES-256-GCM menggunakan master_key."""
    wrap_key = hkdf_derive(master_key, b"file-wrap", 32)
    nonce = os.urandom(12)
    aesgcm = AESGCM(wrap_key)
    ct = aesgcm.encrypt(nonce, file_key, None)
    return nonce + ct   # 12 + 48 = 60 byte


def _unwrap_key(wrapped: bytes, master_key: bytes) -> bytes:
    """Lepas bungkus file_key; lempar ValueError bila gagal."""
    wrap_key = hkdf_derive(master_key, b"file-wrap", 32)
    nonce, ct = wrapped[:12], wrapped[12:]
    aesgcm = AESGCM(wrap_key)
    try:
        return aesgcm.decrypt(nonce, ct, None)
    except Exception as exc:
        raise ValueError("Gagal membuka kunci file — master key salah?") from exc


def encrypt_file(
    data: bytes, orig_filename: str, master_key: bytes
) -> bytes:
    """
    Enkripsi data file lengkap.
    Kembalikan bytes format .vault.
    """
    # Buat file key acak
    file_key = os.urandom(32)
    nonce_prefix = os.urandom(4)
    chacha = ChaCha20Poly1305(file_key)

    # Enkripsi nama file asli
    wrap_key_fn = hkdf_derive(master_key, b"file-name", 32)
    aesgcm_fn = AESGCM(wrap_key_fn)
    nonce_fn = os.urandom(12)
    fn_ct = aesgcm_fn.encrypt(nonce_fn, orig_filename.encode("utf-8"), None)
    fn_enc = nonce_fn + fn_ct

    # Bungkus file key
    wrapped = _wrap_key(file_key, master_key)

    # Header
    header = MAGIC + struct.pack("B", VERSION) + nonce_prefix + wrapped
    header += struct.pack(">H", len(fn_enc)) + fn_enc

    # Enkripsi chunk
    chunks = bytearray()
    total = len(data)
    counter = 0
    offset = 0
    while offset < total or total == 0:
        chunk = data[offset: offset + CHUNK_SIZE]
        offset += CHUNK_SIZE
        is_last = offset >= total
        counter_bytes = struct.pack(">Q", counter)
        nonce = nonce_prefix + counter_bytes
        aad = b"chunk:" + counter_bytes + (b":last" if is_last else b"")
        ct = chacha.encrypt(nonce, chunk, aad)
        chunks += struct.pack(">I", len(ct)) + ct
        counter += 1
        if is_last:
            break

    return bytes(header) + bytes(chunks)


def decrypt_file(vault_data: bytes, master_key: bytes) -> tuple[bytes, str]:
    """
    Dekripsi file .vault.
    Kembalikan (plaintext_bytes, orig_filename).
    Lempar ValueError bila format salah atau tag tidak valid.
    """
    pos = 0

    # Magic + version + nonce_prefix + wrapped_key
    if vault_data[:4] != MAGIC:
        raise ValueError("Bukan file .vault yang valid (magic tidak cocok).")
    pos += 4
    version = struct.unpack("B", vault_data[pos:pos+1])[0]
    pos += 1
    nonce_prefix = vault_data[pos:pos+4]
    pos += 4
    wrapped = vault_data[pos:pos+60]
    pos += 60

    # Nama file
    fn_enc_len = struct.unpack(">H", vault_data[pos:pos+2])[0]
    pos += 2
    fn_enc = vault_data[pos:pos+fn_enc_len]
    pos += fn_enc_len

    # Dekripsi nama file
    wrap_key_fn = hkdf_derive(master_key, b"file-name", 32)
    aesgcm_fn = AESGCM(wrap_key_fn)
    try:
        orig_filename = aesgcm_fn.decrypt(fn_enc[:12], fn_enc[12:], None).decode("utf-8")
    except Exception as exc:
        raise ValueError("Gagal mendekripsi nama file.") from exc

    # Buka bungkus file key
    file_key = _unwrap_key(wrapped, master_key)
    chacha = ChaCha20Poly1305(file_key)

    # Dekripsi chunk
    plaintext = bytearray()
    counter = 0
    while pos < len(vault_data):
        ct_len = struct.unpack(">I", vault_data[pos:pos+4])[0]
        pos += 4
        ct = vault_data[pos:pos+ct_len]
        pos += ct_len
        # Tentukan apakah ini chunk terakhir
        is_last = pos >= len(vault_data)
        counter_bytes = struct.pack(">Q", counter)
        nonce = nonce_prefix + counter_bytes
        aad = b"chunk:" + counter_bytes + (b":last" if is_last else b"")
        try:
            plaintext += chacha.decrypt(nonce, ct, aad)
        except Exception as exc:
            raise ValueError(
                f"Dekripsi chunk {counter} gagal — file terpotong atau diubah."
            ) from exc
        counter += 1

    return bytes(plaintext), orig_filename


def file_sha256(data: bytes) -> str:
    """Hitung SHA-256 hex dari data."""
    return hashlib.sha256(data).hexdigest()
