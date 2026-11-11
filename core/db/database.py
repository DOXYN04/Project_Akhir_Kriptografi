"""
core/db/database.py — Koneksi SQLite + migrasi skema untuk Obsidian Vault.
"""

import sqlite3
import os
from pathlib import Path

import config


def get_connection() -> sqlite3.Connection:
    """
    Buka dan kembalikan koneksi SQLite ke vault.db.
    Membuat direktori data/ bila belum ada.
    """
    Path(config.DB_PATH).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(config.DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA foreign_keys=ON;")
    return conn


def _migrate(conn: sqlite3.Connection) -> None:
    """
    Jalankan migrasi inkremental aman per kolom (idempoten).
    """
    migrations = [
        "ALTER TABLE users ADD COLUMN username TEXT",
        "ALTER TABLE users ADD COLUMN wrapped_key BLOB",
        "ALTER TABLE messages ADD COLUMN user_id INTEGER REFERENCES users(id) ON DELETE CASCADE",
        "ALTER TABLE files ADD COLUMN user_id INTEGER REFERENCES users(id) ON DELETE CASCADE",
        "ALTER TABLE stego_items ADD COLUMN user_id INTEGER REFERENCES users(id) ON DELETE CASCADE",
        "ALTER TABLE blocks ADD COLUMN user_id INTEGER REFERENCES users(id) ON DELETE CASCADE",
    ]
    for sql in migrations:
        try:
            conn.execute(sql)
            conn.commit()
        except sqlite3.OperationalError:
            pass


def init_db() -> None:
    """
    Buat tabel-tabel vault bila belum ada, lalu jalankan migrasi.
    """
    conn = get_connection()
    try:
        conn.executescript("""
            -- Pengguna & Passkey WebAuthn
            CREATE TABLE IF NOT EXISTS users (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                username      TEXT UNIQUE NOT NULL,
                credential_id BLOB UNIQUE,
                public_key    BLOB,
                sign_count    INTEGER NOT NULL DEFAULT 0,
                kdf_salt      BLOB NOT NULL,
                pin_hash      TEXT NOT NULL,
                wrapped_key   BLOB,
                created_at    TEXT NOT NULL DEFAULT (datetime('now'))
            );

            -- Temporary state registrasi WebAuthn (T2)
            CREATE TABLE IF NOT EXISTS pending_registrations (
                reg_token   TEXT PRIMARY KEY,
                username    TEXT NOT NULL,
                pin_hash    TEXT NOT NULL,
                kdf_salt    BLOB NOT NULL,
                wrapped_key BLOB NOT NULL,
                expires_at  REAL NOT NULL
            );

            -- Pesan teks (terenkripsi per user - T5)
            CREATE TABLE IF NOT EXISTS messages (
                id           INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id      INTEGER NOT NULL,
                title_enc    BLOB NOT NULL,
                body_enc     BLOB NOT NULL,
                is_important INTEGER NOT NULL DEFAULT 0,
                created_at   TEXT NOT NULL DEFAULT (datetime('now')),
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            );

            -- File terenkripsi (T5)
            CREATE TABLE IF NOT EXISTS files (
                id           INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id      INTEGER NOT NULL,
                vault_path   TEXT NOT NULL,
                meta_enc     BLOB NOT NULL,
                created_at   TEXT NOT NULL DEFAULT (datetime('now')),
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            );

            -- Item steganografi (T5)
            CREATE TABLE IF NOT EXISTS stego_items (
                id           INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id      INTEGER NOT NULL,
                image_path   TEXT NOT NULL,
                note_enc     BLOB,
                created_at   TEXT NOT NULL DEFAULT (datetime('now')),
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            );

            -- Blok blockchain (T5)
            CREATE TABLE IF NOT EXISTS blocks (
                idx          INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id      INTEGER NOT NULL,
                timestamp    REAL NOT NULL,
                data_json    TEXT NOT NULL,
                prev_hash    TEXT NOT NULL,
                nonce        INTEGER NOT NULL,
                hash         TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            );
        """)
        conn.commit()
        _migrate(conn)
    finally:
        conn.close()