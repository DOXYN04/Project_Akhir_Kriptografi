"""
core/crypto/classical.py — Algoritma kriptografi klasik:
  - Vigenère byte-mode (mod 256)
  - Columnar Transposition

Diimplementasikan sendiri untuk tujuan edukatif.
"""

import math
from typing import Union


# ── Vigenère (byte-mode, mod 256) ─────────────────────────────────────────────

def vigenere_encrypt(data: bytes, key: bytes) -> bytes:
    """
    Enkripsi Vigenère byte-mode: C[i] = (P[i] + K[i mod len(K)]) mod 256.
    Aman untuk UTF-8 apapun karena beroperasi pada byte.
    """
    if not key:
        raise ValueError("Kunci Vigenère tidak boleh kosong.")
    n = len(key)
    return bytes((b + key[i % n]) % 256 for i, b in enumerate(data))


def vigenere_decrypt(data: bytes, key: bytes) -> bytes:
    """
    Dekripsi Vigenère byte-mode: P[i] = (C[i] - K[i mod len(K)]) mod 256.
    """
    if not key:
        raise ValueError("Kunci Vigenère tidak boleh kosong.")
    n = len(key)
    return bytes((b - key[i % n]) % 256 for i, b in enumerate(data))


# ── Columnar Transposition ────────────────────────────────────────────────────

def _key_order(key: bytes) -> list[int]:
    """
    Ubah key bytes menjadi urutan kolom berdasarkan nilai byte yang diurutkan.
    Contoh: key = b"\\x03\\x01\\x02" → [1, 2, 0] (kolom paling kecil duluan).
    """
    indexed = sorted(range(len(key)), key=lambda i: key[i])
    order = [0] * len(key)
    for rank, col in enumerate(indexed):
        order[col] = rank
    return order


def columnar_encrypt(data: bytes, key: bytes) -> bytes:
    """
    Enkripsi Columnar Transposition.
    Padding nol di akhir bila data tidak habis dibagi len(key).
    Panjang asli TIDAK disimpan di sini — ditangani oleh caller (text_super).
    """
    if not key:
        raise ValueError("Kunci transposisi tidak boleh kosong.")
    ncols = len(key)
    nrows = math.ceil(len(data) / ncols)
    # Padding
    padded = data + b"\x00" * (nrows * ncols - len(data))
    # Tulis per baris, baca per kolom sesuai urutan kunci
    order = _key_order(key)
    grid = [padded[r * ncols: (r + 1) * ncols] for r in range(nrows)]
    # Susun kolom berdasarkan rank
    col_order = sorted(range(ncols), key=lambda c: order[c])
    result = bytearray()
    for c in col_order:
        for r in range(nrows):
            result.append(grid[r][c])
    return bytes(result)


def columnar_decrypt(data: bytes, key: bytes, orig_len: int) -> bytes:
    """
    Dekripsi Columnar Transposition.
    orig_len diperlukan untuk menghapus padding.
    """
    if not key:
        raise ValueError("Kunci transposisi tidak boleh kosong.")
    ncols = len(key)
    nrows = math.ceil(orig_len / ncols)
    total = nrows * ncols

    order = _key_order(key)
    col_order = sorted(range(ncols), key=lambda c: order[c])

    # Panjang tiap kolom
    full_cols = total - nrows * ncols + ncols  # selalu == ncols (sudah padded)
    col_len = nrows

    # Pisahkan data ke kolom
    cols: dict[int, bytes] = {}
    pos = 0
    for c in col_order:
        cols[c] = data[pos: pos + col_len]
        pos += col_len

    # Baca per baris
    result = bytearray()
    for r in range(nrows):
        for c in range(ncols):
            result.append(cols[c][r])

    return bytes(result[:orig_len])
