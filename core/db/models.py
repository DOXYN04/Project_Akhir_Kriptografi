"""
core/db/models.py — Operasi CRUD dengan enkripsi kolom sensitif (AES-256-GCM) & Isolasi User.

Kolom berakhiran _enc disimpan sebagai BLOB terenkripsi.
AAD = b"tabel:kolom:id" untuk mencegah pemindahan data antar baris.
"""

import os
from typing import Optional

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from core.auth.kdf import hkdf_derive
from core.db.database import get_connection


# ── Helper enkripsi kolom ─────────────────────────────────────────────────────

def _col_key(master_key: bytes) -> bytes:
    """Turunkan kunci AES-256 untuk enkripsi kolom DB."""
    return hkdf_derive(master_key, b"db-field", 32)


def _aad(table: str, column: str, row_id: int) -> bytes:
    """Buat AAD unik per kolom per baris."""
    return f"{table}:{column}:{row_id}".encode()


def encrypt_field(
    plaintext: bytes, master_key: bytes, table: str, column: str, row_id: int
) -> bytes:
    """
    Enkripsi bytes dengan AES-256-GCM.
    Format: nonce(12B) | ciphertext+tag
    """
    key = _col_key(master_key)
    nonce = os.urandom(12)
    aad = _aad(table, column, row_id)
    aesgcm = AESGCM(key)
    ct = aesgcm.encrypt(nonce, plaintext, aad)
    return nonce + ct


def decrypt_field(
    blob: bytes, master_key: bytes, table: str, column: str, row_id: int
) -> bytes:
    """
    Dekripsi kolom. Lempar ValueError bila tag tidak valid.
    """
    if len(blob) < 12:
        raise ValueError("Data terlalu pendek untuk didekripsi.")
    key = _col_key(master_key)
    nonce, ct = blob[:12], blob[12:]
    aad = _aad(table, column, row_id)
    aesgcm = AESGCM(key)
    try:
        return aesgcm.decrypt(nonce, ct, aad)
    except Exception as exc:
        raise ValueError("Dekripsi kolom gagal — data rusak atau kunci salah.") from exc


# ── Operasi Pengguna ──────────────────────────────────────────────────────────

def create_user(
    credential_id: bytes,
    public_key: bytes,
    kdf_salt: bytes,
    pin_hash: str,
    username: str,
    wrapped_key: Optional[bytes] = None,
) -> int:
    """Simpan pengguna baru; kembalikan id."""
    conn = get_connection()
    try:
        cur = conn.execute(
            "INSERT INTO users (credential_id, public_key, kdf_salt, pin_hash, username, wrapped_key) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (credential_id, public_key, kdf_salt, pin_hash, username, wrapped_key or b""),
        )
        conn.commit()
        return cur.lastrowid
    finally:
        conn.close()


def get_user_by_credential(credential_id: bytes) -> Optional[dict]:
    """Cari pengguna berdasarkan credential_id WebAuthn."""
    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT * FROM users WHERE credential_id = ?", (credential_id,)
        ).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def get_user_by_username(username: str) -> Optional[dict]:
    """Cari pengguna berdasarkan username (case-insensitive)."""
    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT * FROM users WHERE lower(username) = lower(?)", (username,)
        ).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def update_sign_count(user_id: int, new_count: int) -> None:
    """Perbarui sign_count setelah autentikasi WebAuthn berhasil."""
    conn = get_connection()
    try:
        conn.execute(
            "UPDATE users SET sign_count = ? WHERE id = ?", (new_count, user_id)
        )
        conn.commit()
    finally:
        conn.close()


def update_webauthn_credential(
    user_id: int, credential_id: bytes, public_key: bytes
) -> None:
    """Perbarui credential_id dan public_key setelah registrasi WebAuthn berhasil."""
    conn = get_connection()
    try:
        conn.execute(
            "UPDATE users SET credential_id = ?, public_key = ? WHERE id = ?",
            (credential_id, public_key, user_id),
        )
        conn.commit()
    finally:
        conn.close()


# ── Operasi Pesan ─────────────────────────────────────────────────────────────

def save_message(
    user_id: int, title_enc: bytes, body_enc: bytes, is_important: bool = False
) -> int:
    """Simpan pesan terenkripsi khusus user_id; kembalikan id."""
    conn = get_connection()
    try:
        cur = conn.execute(
            "INSERT INTO messages (user_id, title_enc, body_enc, is_important) VALUES (?, ?, ?, ?)",
            (user_id, title_enc, body_enc, int(is_important)),
        )
        conn.commit()
        return cur.lastrowid
    finally:
        conn.close()


def list_messages(user_id: int) -> list[dict]:
    """Kembalikan semua baris pesan milik user_id."""
    conn = get_connection()
    try:
        rows = conn.execute(
            "SELECT * FROM messages WHERE user_id = ? ORDER BY created_at DESC",
            (user_id,)
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def delete_message(user_id: int, msg_id: int) -> None:
    """Hapus pesan milik user_id berdasarkan id."""
    conn = get_connection()
    try:
        conn.execute("DELETE FROM messages WHERE id = ? AND user_id = ?", (msg_id, user_id))
        conn.commit()
    finally:
        conn.close()


# ── Operasi File ──────────────────────────────────────────────────────────────

def save_file_record(user_id: int, vault_path: str, meta_enc: bytes) -> int:
    """Simpan catatan file terenkripsi milik user_id; kembalikan id."""
    conn = get_connection()
    try:
        cur = conn.execute(
            "INSERT INTO files (user_id, vault_path, meta_enc) VALUES (?, ?, ?)",
            (user_id, vault_path, meta_enc),
        )
        conn.commit()
        return cur.lastrowid
    finally:
        conn.close()


def list_files(user_id: int) -> list[dict]:
    """Kembalikan semua catatan file milik user_id."""
    conn = get_connection()
    try:
        rows = conn.execute(
            "SELECT * FROM files WHERE user_id = ? ORDER BY created_at DESC",
            (user_id,)
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def delete_file_record(user_id: int, file_id: int) -> None:
    """Hapus catatan file milik user_id berdasarkan id."""
    conn = get_connection()
    try:
        conn.execute("DELETE FROM files WHERE id = ? AND user_id = ?", (file_id, user_id))
        conn.commit()
    finally:
        conn.close()


# ── Operasi Stego ─────────────────────────────────────────────────────────────

def save_stego_item(user_id: int, image_path: str, note_enc: Optional[bytes] = None) -> int:
    """Simpan catatan item stego milik user_id; kembalikan id."""
    conn = get_connection()
    try:
        cur = conn.execute(
            "INSERT INTO stego_items (user_id, image_path, note_enc) VALUES (?, ?, ?)",
            (user_id, image_path, note_enc),
        )
        conn.commit()
        return cur.lastrowid
    finally:
        conn.close()


def list_stego_items(user_id: int) -> list[dict]:
    """Kembalikan semua item stego milik user_id."""
    conn = get_connection()
    try:
        rows = conn.execute(
            "SELECT * FROM stego_items WHERE user_id = ? ORDER BY created_at DESC",
            (user_id,)
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


# ── Operasi Blockchain ────────────────────────────────────────────────────────

def save_block(user_id: int, block_dict: dict) -> None:
    """Simpan satu blok ke tabel blocks milik user_id."""
    conn = get_connection()
    data = dict(block_dict)
    data["user_id"] = user_id
    try:
        conn.execute(
            "INSERT OR REPLACE INTO blocks "
            "(user_id, timestamp, data_json, prev_hash, nonce, hash) "
            "VALUES (:user_id, :timestamp, :data_json, :prev_hash, :nonce, :hash)",
            data,
        )
        conn.commit()
    finally:
        conn.close()


def load_blocks(user_id: int) -> list[dict]:
    """Muat semua blok milik user_id berurutan berdasarkan idx."""
    conn = get_connection()
    try:
        rows = conn.execute(
            "SELECT * FROM blocks WHERE user_id = ? ORDER BY idx ASC",
            (user_id,)
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()