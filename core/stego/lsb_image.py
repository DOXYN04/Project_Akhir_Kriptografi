"""
core/stego/lsb_image.py — Steganografi LSB pada gambar PNG/BMP (lossless).

Alur Embed:
  Pesan → enkripsi AES-256-GCM → payload = "STG1" | length(4B) | nonce | ct+tag
  → bit stream → sisipkan ke LSB kanal R,G,B urutan piksel
  → simpan PNG

Gunakan numpy untuk operasi vektor (bukan loop per piksel).
"""

import os
import struct
import io
from typing import Union

import numpy as np
from PIL import Image

from core.auth.kdf import hkdf_derive
from core.crypto.modern import aes_gcm_encrypt, aes_gcm_decrypt

MAGIC = b"STG1"
SUPPORTED_FORMATS = {"PNG", "BMP"}


def _stego_key(key: bytes) -> bytes:
    """Turunkan kunci AES untuk steganografi."""
    return hkdf_derive(key, b"stego", 32)


def capacity(image_bytes: bytes) -> int:
    """
    Kembalikan kapasitas maksimum payload (byte) yang bisa disisipkan.
    Kapasitas = (w × h × 3) // 8 − 8  (dikurangi 8 byte untuk magic+length)
    """
    img = Image.open(io.BytesIO(image_bytes))
    w, h = img.size
    return (w * h * 3) // 8 - 8


def _validate_format(image_bytes: bytes) -> Image.Image:
    """Buka gambar dan pastikan format lossless. Lempar ValueError untuk JPEG."""
    img = Image.open(io.BytesIO(image_bytes))
    fmt = img.format or ""
    if fmt.upper() == "JPEG" or fmt.upper() == "JPG":
        raise ValueError(
            "Format JPEG tidak didukung karena kompresi lossy merusak bit LSB. "
            "Gunakan PNG atau BMP."
        )
    return img


def embed(image_bytes: bytes, secret: bytes, key: bytes) -> bytes:
    """
    Sembunyikan `secret` dalam gambar.
    Kembalikan PNG bytes gambar stego.
    Lempar ValueError bila kapasitas tidak cukup.
    """
    img = _validate_format(image_bytes)
    img = img.convert("RGB")

    # Enkripsi payload
    aes_key = _stego_key(key)
    nonce, ct = aes_gcm_encrypt(aes_key, secret)
    inner = nonce + ct                          # nonce(12) + ct+tag
    payload = MAGIC + struct.pack(">I", len(inner)) + inner
    payload_bits = np.unpackbits(np.frombuffer(payload, dtype=np.uint8))

    # Validasi kapasitas
    cap = capacity(image_bytes)
    if len(payload) > cap:
        raise ValueError(
            f"Pesan terlalu panjang ({len(payload)} byte) untuk gambar ini "
            f"(kapasitas {cap} byte)."
        )

    # Sisipkan ke piksel
    pixels = np.array(img, dtype=np.uint8)
    flat = pixels.reshape(-1)   # view 1D atas kanal R,G,B

    # Timpa LSB piksel pertama sejumlah bit payload
    n_bits = len(payload_bits)
    flat[:n_bits] = (flat[:n_bits] & 0xFE) | payload_bits
    pixels = flat.reshape(pixels.shape)

    # Simpan sebagai PNG
    out_img = Image.fromarray(pixels, "RGB")
    buf = io.BytesIO()
    out_img.save(buf, format="PNG")
    return buf.getvalue()


def extract(stego_bytes: bytes, key: bytes) -> bytes:
    """
    Ekstrak dan dekripsi pesan tersembunyi dari gambar stego.
    Lempar ValueError bila magic tidak cocok atau dekripsi gagal.
    """
    img = Image.open(io.BytesIO(stego_bytes)).convert("RGB")
    pixels = np.array(img, dtype=np.uint8)
    flat = pixels.reshape(-1)

    # Baca header: magic(4B) + length(4B) = 8 byte = 64 bit
    header_bits = flat[:64] & 1
    header_bytes = np.packbits(header_bits).tobytes()

    if header_bytes[:4] != MAGIC:
        raise ValueError(
            "Magic tidak ditemukan — gambar ini mungkin tidak mengandung pesan "
            "tersembunyi atau telah dimodifikasi."
        )

    inner_len = struct.unpack(">I", header_bytes[4:8])[0]
    total_payload = 8 + inner_len

    # Baca seluruh payload
    n_bits = total_payload * 8
    all_bits = flat[:n_bits] & 1
    all_bytes = np.packbits(all_bits).tobytes()
    inner = all_bytes[8: 8 + inner_len]

    # Dekripsi
    if len(inner) < 12:
        raise ValueError("Data stego terlalu pendek.")
    nonce, ct = inner[:12], inner[12:]
    aes_key = _stego_key(key)
    return aes_gcm_decrypt(aes_key, nonce, ct)


def psnr(original_bytes: bytes, stego_bytes: bytes) -> float:
    """
    Hitung PSNR antara gambar asli dan gambar stego (dB).
    Nilai tinggi (>50 dB) berarti perubahan tidak terlihat secara visual.
    """
    orig = np.array(Image.open(io.BytesIO(original_bytes)).convert("RGB"), dtype=np.float64)
    steg = np.array(Image.open(io.BytesIO(stego_bytes)).convert("RGB"), dtype=np.float64)
    mse = np.mean((orig - steg) ** 2)
    if mse == 0:
        return float("inf")
    return 20 * np.log10(255.0 / np.sqrt(mse))
