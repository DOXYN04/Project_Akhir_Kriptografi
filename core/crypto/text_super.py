"""
core/crypto/text_super.py — Super enkripsi pesan teks:
  Plaintext → Vigenère (byte, mod 256) → Columnar Transposition → AES-256-GCM → Base64

Format paket biner (sebelum Base64):
  version(1B) | nonce(12B) | orig_len(4B) | ciphertext+tag
  AAD = version(1B) || orig_len(4B)

Kunci diturunkan dari master_key via HKDF dengan label berbeda (domain separation).
"""

import base64
import struct

from core.auth.kdf import hkdf_derive
from core.crypto.classical import vigenere_encrypt, vigenere_decrypt
from core.crypto.classical import columnar_encrypt, columnar_decrypt
from core.crypto.modern import aes_gcm_encrypt, aes_gcm_decrypt

# Versi format paket
_VERSION: int = 1


def _derive_keys(master_key: bytes) -> tuple[bytes, bytes, bytes]:
    """Turunkan kunci Vigenère (16B), Transposisi (16B), AES (32B)."""
    key_vig   = hkdf_derive(master_key, b"text-vigenere",  16)
    key_trans = hkdf_derive(master_key, b"text-transpose", 16)
    key_aes   = hkdf_derive(master_key, b"text-aes",       32)
    return key_vig, key_trans, key_aes


def encrypt_text(plaintext: str, master_key: bytes) -> str:
    """
    Enkripsi teks dengan super enkripsi (Vigenère → Transposisi → AES-256-GCM).
    Kembalikan string Base64 yang aman untuk disimpan/ditampilkan.
    """
    key_vig, key_trans, key_aes = _derive_keys(master_key)

    # Langkah 1: Vigenère byte-mode
    raw = plaintext.encode("utf-8")
    after_vig = vigenere_encrypt(raw, key_vig)

    # Langkah 2: Columnar Transposition
    orig_len = len(after_vig)
    after_trans = columnar_encrypt(after_vig, key_trans)

    # Langkah 3: AES-256-GCM
    version_byte = struct.pack("B", _VERSION)
    orig_len_bytes = struct.pack(">I", orig_len)
    aad = version_byte + orig_len_bytes   # header sebagai AAD

    nonce, ct = aes_gcm_encrypt(key_aes, after_trans, aad)

    # Rakit paket biner
    packet = version_byte + nonce + orig_len_bytes + ct
    return base64.b64encode(packet).decode("ascii")


def decrypt_text(token: str, master_key: bytes) -> str:
    """
    Dekripsi token super enkripsi.
    Lempar ValueError bila token rusak atau kunci salah.
    """
    key_vig, key_trans, key_aes = _derive_keys(master_key)

    try:
        packet = base64.b64decode(token)
    except Exception as exc:
        raise ValueError("Token bukan Base64 valid.") from exc

    # Urai paket
    if len(packet) < 1 + 12 + 4:
        raise ValueError("Paket terlalu pendek.")

    version = struct.unpack("B", packet[0:1])[0]
    nonce = packet[1:13]
    orig_len = struct.unpack(">I", packet[13:17])[0]
    ct = packet[17:]

    # Rekonstruksi AAD
    aad = packet[0:1] + packet[13:17]

    # Langkah 3 balik: AES-256-GCM
    after_trans = aes_gcm_decrypt(key_aes, nonce, ct, aad)

    # Langkah 2 balik: Columnar Transposition
    after_vig = columnar_decrypt(after_trans, key_trans, orig_len)

    # Langkah 1 balik: Vigenère
    raw = vigenere_decrypt(after_vig, key_vig)

    try:
        return raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ValueError("Dekripsi menghasilkan data bukan UTF-8 — kunci salah?") from exc


def encrypt_text_steps(
    plaintext: str, master_key: bytes
) -> dict[str, str]:
    """
    Kembalikan dict dengan hasil tiap tahap enkripsi untuk visualisasi UI.
    Keys: 'after_vigenere', 'after_transposition', 'final_base64'
    """
    key_vig, key_trans, key_aes = _derive_keys(master_key)

    raw = plaintext.encode("utf-8")
    after_vig = vigenere_encrypt(raw, key_vig)
    orig_len = len(after_vig)
    after_trans = columnar_encrypt(after_vig, key_trans)

    version_byte = struct.pack("B", _VERSION)
    orig_len_bytes = struct.pack(">I", orig_len)
    aad = version_byte + orig_len_bytes
    nonce, ct = aes_gcm_encrypt(key_aes, after_trans, aad)
    packet = version_byte + nonce + orig_len_bytes + ct
    final = base64.b64encode(packet).decode("ascii")

    import base64 as _b64
    return {
        "after_vigenere":     _b64.b64encode(after_vig).decode("ascii"),
        "after_transposition": _b64.b64encode(after_trans).decode("ascii"),
        "final_base64":       final,
    }
