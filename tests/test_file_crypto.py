"""
tests/test_file_crypto.py — Unit test enkripsi file ChaCha20-Poly1305.
"""

import os
import pytest
from core.crypto.file_crypto import encrypt_file, decrypt_file, file_sha256


MASTER_KEY = os.urandom(32)


class TestFileCrypto:
    def test_roundtrip_text_file(self):
        data = b"Ini file teks biasa.\n" * 100
        vault = encrypt_file(data, "test.txt", MASTER_KEY)
        recovered, name = decrypt_file(vault, MASTER_KEY)
        assert recovered == data
        assert name == "test.txt"

    def test_roundtrip_empty_file(self):
        data = b""
        vault = encrypt_file(data, "empty.bin", MASTER_KEY)
        recovered, name = decrypt_file(vault, MASTER_KEY)
        assert recovered == data
        assert name == "empty.bin"

    def test_roundtrip_unicode_filename(self):
        data = b"konten"
        vault = encrypt_file(data, "berkas saya (tes).pdf", MASTER_KEY)
        recovered, name = decrypt_file(vault, MASTER_KEY)
        assert name == "berkas saya (tes).pdf"

    def test_hash_preserved(self):
        data = os.urandom(1024 * 50)  # 50 KB acak
        vault = encrypt_file(data, "rand.bin", MASTER_KEY)
        recovered, _ = decrypt_file(vault, MASTER_KEY)
        assert file_sha256(recovered) == file_sha256(data)

    def test_tampered_vault_fails(self):
        data = b"rahasia"
        vault = bytearray(encrypt_file(data, "a.txt", MASTER_KEY))
        vault[-1] ^= 0xFF   # ubah byte terakhir
        with pytest.raises(ValueError):
            decrypt_file(bytes(vault), MASTER_KEY)

    def test_truncated_vault_fails(self):
        data = b"rahasia panjang" * 100
        vault = encrypt_file(data, "b.txt", MASTER_KEY)
        with pytest.raises(ValueError):
            decrypt_file(vault[:len(vault)//2], MASTER_KEY)

    def test_wrong_magic_fails(self):
        with pytest.raises(ValueError, match="magic"):
            decrypt_file(b"BAAD" + b"\x00" * 100, MASTER_KEY)

    def test_wrong_key_fails(self):
        data = b"kunci salah"
        vault = encrypt_file(data, "c.txt", MASTER_KEY)
        wrong_key = os.urandom(32)
        with pytest.raises(ValueError):
            decrypt_file(vault, wrong_key)
