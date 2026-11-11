"""
tests/test_db_encryption.py — Verifikasi bahwa kolom sensitif tidak menyimpan plaintext.
"""

import os
import sqlite3
import pytest
import tempfile

import config


@pytest.fixture
def tmp_db(tmp_path, monkeypatch):
    """Buat DB sementara dan patch DB_PATH."""
    db_file = str(tmp_path / "vault_test.db")
    monkeypatch.setattr(config, "DB_PATH", db_file)
    # Re-import setelah patch
    from core.db.database import init_db
    init_db()
    return db_file


def test_message_body_not_plaintext(tmp_db):
    """
    Isi teks pesan tidak boleh muncul sebagai plaintext di DB.
    """
    from core.db import models as db_models
    from core.crypto.text_super import encrypt_text
    from core.auth.kdf import hkdf_derive
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    import os

    # 1. Buat user dummy di database pengujian agar memiliki user_id sah (FK)
    user_id = db_models.create_user(
        credential_id=os.urandom(16),
        public_key=b"TEST_KEY",
        kdf_salt=os.urandom(16),
        pin_hash="test_hash",
        username="test_user_encryption"
    )

    master_key = os.urandom(32)
    plaintext = "Pesan sangat rahasia tidak boleh kelihatan"

    # Enkripsi seperti yang dilakukan halaman UI
    token = encrypt_text(plaintext, master_key)
    title_key = hkdf_derive(master_key, b"db-field", 32)
    nonce_t = os.urandom(12)
    title_ct = AESGCM(title_key).encrypt(nonce_t, b"judul rahasia", b"messages:title_enc:0")
    title_blob = nonce_t + title_ct

    # 2. Sertakan user_id sebagai argumen pertama
    msg_id = db_models.save_message(user_id, title_blob, token.encode("ascii"), True)

    # Baca langsung dari SQLite tanpa dekripsi
    conn = sqlite3.connect(tmp_db)
    row = conn.execute("SELECT title_enc, body_enc FROM messages WHERE id=?", (msg_id,)).fetchone()
    conn.close()

    title_raw = row[0]
    body_raw  = row[1]

    # Pastikan plaintext tidak muncul mentah
    assert b"rahasia" not in title_raw
    assert plaintext.encode("utf-8") not in body_raw


def test_data_unreadable_without_master_key(tmp_db):
    """
    Kolom yang terenkripsi harus gagal didekripsi dengan kunci yang salah.
    """
    from core.db import models as db_models
    from core.db.models import decrypt_field
    from core.auth.kdf import hkdf_derive
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM

    master_key  = os.urandom(32)
    wrong_key   = os.urandom(32)
    plaintext   = b"data sangat rahasia"

    # Enkripsi & simpan
    from core.db.models import encrypt_field
    blob = encrypt_field(plaintext, master_key, "messages", "body_enc", 99)

    # Harus berhasil dengan kunci benar
    assert decrypt_field(blob, master_key, "messages", "body_enc", 99) == plaintext

    # Harus gagal dengan kunci salah
    with pytest.raises(ValueError):
        decrypt_field(blob, wrong_key, "messages", "body_enc", 99)
