"""
tests/test_stego.py — Unit test steganografi LSB.
"""

import io
import os
import pytest
from PIL import Image
from core.stego.lsb_image import embed, extract, capacity, psnr


KEY = os.urandom(32)

def _make_png(w: int = 200, h: int = 200) -> bytes:
    """Buat gambar PNG merah solid berukuran w×h."""
    img = Image.new("RGB", (w, h), color=(180, 20, 20))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


class TestStego:
    def test_roundtrip_short(self):
        img = _make_png()
        secret = b"pesan rahasia"
        stego = embed(img, secret, KEY)
        assert extract(stego, KEY) == secret

    def test_roundtrip_empty_message(self):
        img = _make_png()
        stego = embed(img, b"", KEY)
        assert extract(stego, KEY) == b""

    def test_capacity_check(self):
        img = _make_png(10, 10)
        cap = capacity(img)
        # Gambar 10×10×3 = 300 bit = 37 byte kapasitas, dikurangi 8 overhead
        assert cap > 0

    def test_overflow_raises(self):
        img = _make_png(10, 10)   # gambar kecil
        secret = b"X" * 10_000    # terlalu panjang
        with pytest.raises(ValueError, match="terlalu panjang"):
            embed(img, secret, KEY)

    def test_wrong_key_fails(self):
        img = _make_png()
        stego = embed(img, b"rahasia", KEY)
        wrong_key = os.urandom(32)
        with pytest.raises(ValueError):
            extract(stego, wrong_key)

    def test_psnr_above_50(self):
        img = _make_png(400, 400)
        stego = embed(img, b"pesan pendek", KEY)
        val = psnr(img, stego)
        assert val > 50

    def test_jpeg_rejected(self):
        img = Image.new("RGB", (100, 100), color=(0, 0, 0))
        buf = io.BytesIO()
        img.save(buf, format="JPEG")
        jpeg_bytes = buf.getvalue()
        with pytest.raises(ValueError, match="JPEG"):
            embed(jpeg_bytes, b"test", KEY)
