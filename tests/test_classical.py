"""
tests/test_classical.py — Unit test algoritma kriptografi klasik.
Uji round-trip dan ketepatan Vigenère + Columnar Transposition.
"""

import pytest
from core.crypto.classical import (
    vigenere_encrypt, vigenere_decrypt,
    columnar_encrypt, columnar_decrypt,
)


# ── Vigenère ──────────────────────────────────────────────────────────────────

class TestVigenere:
    def test_roundtrip_ascii(self):
        key = b"secretkey"
        plaintext = b"Hello World!"
        assert vigenere_decrypt(vigenere_encrypt(plaintext, key), key) == plaintext

    def test_roundtrip_utf8(self):
        key = b"kunci123"
        plaintext = "Pesan rahasia 🔐 dengan emoji".encode("utf-8")
        assert vigenere_decrypt(vigenere_encrypt(plaintext, key), key) == plaintext

    def test_roundtrip_empty(self):
        key = b"k"
        assert vigenere_decrypt(vigenere_encrypt(b"", key), key) == b""

    def test_roundtrip_long(self):
        key = b"a" * 17
        plaintext = b"X" * 100_000
        assert vigenere_decrypt(vigenere_encrypt(plaintext, key), key) == plaintext

    def test_different_key_fails(self):
        key1 = b"rightkey"
        key2 = b"wrongkey"
        plaintext = b"test"
        ct = vigenere_encrypt(plaintext, key1)
        assert vigenere_decrypt(ct, key2) != plaintext

    def test_empty_key_raises(self):
        with pytest.raises(ValueError):
            vigenere_encrypt(b"data", b"")


# ── Columnar Transposition ────────────────────────────────────────────────────

class TestColumnarTransposition:
    def test_roundtrip_exact_fit(self):
        key = b"\x02\x00\x01"   # 3 kolom
        plaintext = b"ABCDEF"   # 2 baris × 3 kolom
        ct = columnar_encrypt(plaintext, key)
        assert columnar_decrypt(ct, key, len(plaintext)) == plaintext

    def test_roundtrip_with_padding(self):
        key = b"\x01\x02\x00"
        plaintext = b"ABCDE"    # 5 byte, perlu padding ke 6
        ct = columnar_encrypt(plaintext, key)
        assert columnar_decrypt(ct, key, len(plaintext)) == plaintext

    def test_roundtrip_single_byte(self):
        key = b"\x00"
        plaintext = b"\xff"
        ct = columnar_encrypt(plaintext, key)
        assert columnar_decrypt(ct, key, 1) == plaintext

    def test_empty_data(self):
        key = b"\x00\x01"
        ct = columnar_encrypt(b"", key)
        assert columnar_decrypt(ct, key, 0) == b""

    def test_empty_key_raises(self):
        with pytest.raises(ValueError):
            columnar_encrypt(b"data", b"")
