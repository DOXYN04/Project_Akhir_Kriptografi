"""
pages/3_Pesan_File.py — Enkripsi & dekripsi file dengan ChaCha20-Poly1305.
Diperbarui untuk Isolasi Multi-User (T5).
"""

import streamlit as st
import io
import json
import os
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

import config
from core.auth.session import require_auth, get_current_user_id
from ui.styles import inject_global_css, dev_mode_banner
from ui.components import quick_menu, page_header, navbar, footer
from ui.layout import golden_columns
from core.crypto.file_crypto import encrypt_file, decrypt_file, file_sha256
from core.db import models as db_models
from core.auth.kdf import hkdf_derive

st.set_page_config(
    page_title=f"Enkripsi File — {config.APP_NAME}",
    page_icon="🔐",
    layout="wide",
)

require_auth()
inject_global_css()
navbar("file")

if config.DEV_MODE:
    dev_mode_banner()

user_id: int = get_current_user_id()
master_key: bytes = st.session_state["master_key"]

page_header("Enkripsi File", "Enkripsi file apapun dengan ChaCha20-Poly1305", icon_bi="file-earmark-lock2-fill")

tab_enc, tab_dec, tab_list = st.tabs(["Enkripsi File", "Dekripsi File", "Daftar File"])

# ═══════════════════════════════════════════════════════════════════════════════
# Tab Enkripsi
# ═══════════════════════════════════════════════════════════════════════════════
with tab_enc:
    left, right = golden_columns()

    with left:
        st.markdown("#### Upload File")
        uploaded = st.file_uploader(
            "Pilih file untuk dienkripsi",
            help=f"Maksimum {config.MAX_FILE_MB} MB",
        )
        do_encrypt = st.button("Enkripsi File", use_container_width=True)

    with right:
        st.markdown("#### Hasil")
        if do_encrypt:
            if not uploaded:
                st.error("Pilih file terlebih dahulu.")
            else:
                data = uploaded.read()
                if len(data) > config.MAX_FILE_MB * 1024 * 1024:
                    st.error(f"File melebihi batas {config.MAX_FILE_MB} MB.")
                else:
                    with st.spinner("Mengenkripsi…"):
                        vault_bytes = encrypt_file(data, uploaded.name, master_key)
                        orig_hash = file_sha256(data)

                        # Simpan metadata terenkripsi ke DB
                        meta = json.dumps({
                            "orig_name": uploaded.name,
                            "size": len(data),
                            "sha256": orig_hash,
                        }).encode("utf-8")
                        meta_key = hkdf_derive(master_key, b"db-field", 32)
                        nonce_m = os.urandom(12)
                        meta_ct = AESGCM(meta_key).encrypt(nonce_m, meta, b"files:meta_enc:0")
                        meta_enc = nonce_m + meta_ct

                        vault_path = f"data/{uploaded.name}.vault"
                        db_models.save_file_record(user_id, vault_path, meta_enc)

                        st.success(f"File dienkripsi ({len(vault_bytes):,} byte).")
                        st.metric("SHA-256 Asli", orig_hash[:32] + "…")
                        st.download_button(
                            "Unduh .vault",
                            data=vault_bytes,
                            file_name=uploaded.name + ".vault",
                            mime="application/octet-stream",
                        )

# ═══════════════════════════════════════════════════════════════════════════════
# Tab Dekripsi
# ═══════════════════════════════════════════════════════════════════════════════
with tab_dec:
    left2, right2 = golden_columns()

    with left2:
        st.markdown("#### Upload File .vault")
        vault_up = st.file_uploader("Pilih file .vault", key="vault_upload")
        do_decrypt = st.button("Dekripsi File", use_container_width=True)

    with right2:
        st.markdown("#### Hasil")
        if do_decrypt:
            if not vault_up:
                st.error("Pilih file .vault terlebih dahulu.")
            else:
                vault_data = vault_up.read()
                with st.spinner("Mendekripsi…"):
                    try:
                        plaintext, orig_name = decrypt_file(vault_data, master_key)
                        recovered_hash = file_sha256(plaintext)
                        st.success(f"Dekripsi berhasil! Nama asli: **{orig_name}**")
                        st.metric("SHA-256 Terpulihkan", recovered_hash[:32] + "…")
                        st.download_button(
                            f"Unduh {orig_name}",
                            data=plaintext,
                            file_name=orig_name,
                            mime="application/octet-stream",
                        )
                    except ValueError as e:
                        st.error(f"❌ Dekripsi gagal: {e}")

# ═══════════════════════════════════════════════════════════════════════════════
# Tab Daftar File
# ═══════════════════════════════════════════════════════════════════════════════
with tab_list:
    files = db_models.list_files(user_id)
    if not files:
        st.info("Belum ada file terenkripsi.")
    else:
        meta_key = hkdf_derive(master_key, b"db-field", 32)
        for f in files:
            with st.expander(f"File #{f['id']} — {f['created_at']}"):
                try:
                    blob = f["meta_enc"]
                    plain_meta = AESGCM(meta_key).decrypt(blob[:12], blob[12:], b"files:meta_enc:0")
                    meta = json.loads(plain_meta)
                    st.write(f"**Nama:** {meta.get('orig_name','?')}")
                    st.write(f"**Ukuran:** {meta.get('size',0):,} byte")
                    st.write(f"**SHA-256:** `{meta.get('sha256','?')[:32]}…`")
                except Exception as e:
                    st.warning(f"Metadata tidak bisa dibaca: {e}")
                if st.button(f"Hapus #{f['id']}", key=f"del_file_{f['id']}"):
                    db_models.delete_file_record(user_id, f["id"])
                    st.rerun()

quick_menu()
footer()