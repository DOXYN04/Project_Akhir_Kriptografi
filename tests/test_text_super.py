"""
tests/test_text_super.py — Unit test super enkripsi teks.
"""

import os
import pytest
from core.crypto.text_super import encrypt_text, decrypt_text


MASTER_KEY = os.urandom(32)


class TestTextSuper:
    def test_roundtrip_simple(self):
        pt = "Halo dunia!"
        assert decrypt_text(encrypt_text(pt, MASTER_KEY), MASTER_KEY) == pt

    def test_roundtrip_empty(self):
        pt = ""
        assert decrypt_text(encrypt_text(pt, MASTER_KEY), MASTER_KEY) == pt

    def test_roundtrip_unicode(self):
        pt = "テスト 🔐 한국어 العربية"
        assert decrypt_text(encrypt_text(pt, MASTER_KEY), MASTER_KEY) == pt

    def test_roundtrip_long(self):
        pt = "A" * 200_000
        assert decrypt_text(encrypt_text(pt, MASTER_KEY), MASTER_KEY) == pt

    def test_different_nonce(self):
        """Dua enkripsi plaintext sama harus menghasilkan ciphertext berbeda."""
        pt = "sama"
        t1 = encrypt_text(pt, MASTER_KEY)
        t2 = encrypt_text(pt, MASTER_KEY)
        assert t1 != t2

    def test_tampered_ciphertext_fails(self):
        """Mengubah 1 byte ciphertext harus gagal saat dekripsi."""
        import base64, struct
        pt = "rahasia"
        token = encrypt_text(pt, MASTER_KEY)
        raw = bytearray(base64.b64decode(token))
        raw[-1] ^= 0xFF   # ubah byte terakhir
        tampered = base64.b64encode(bytes(raw)).decode("ascii")
        with pytest.raises(ValueError):
            decrypt_text(tampered, MASTER_KEY)

    def test_wrong_key_fails(self):
        pt = "kunci berbeda"
        token = encrypt_text(pt, MASTER_KEY)
        wrong_key = os.urandom(32)
        with pytest.raises(ValueError):
            decrypt_text(token, wrong_key)
