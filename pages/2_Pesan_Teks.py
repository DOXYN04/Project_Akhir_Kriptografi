"""
pages/2_Pesan_Teks.py — Super enkripsi pesan teks (Vigenère + Transposisi + AES-GCM).
Diperbarui untuk Isolasi Multi-User (T5).
"""

import streamlit as st

import config
from core.auth.session import require_auth, get_current_user_id
from ui.styles import inject_global_css, dev_mode_banner
from ui.components import quick_menu, page_header, navbar, footer
from ui.layout import golden_columns
from core.crypto.text_super import encrypt_text, decrypt_text, encrypt_text_steps
from core.db import models as db_models
from core.auth.kdf import hkdf_derive

st.set_page_config(
    page_title=f"Pesan Teks — {config.APP_NAME}",
    page_icon="🔐",
    layout="wide",
)

require_auth()
inject_global_css()
navbar("message")

if config.DEV_MODE:
    dev_mode_banner()

user_id: int = get_current_user_id()
master_key: bytes = st.session_state["master_key"]

page_header("Pesan Teks", "Enkripsi & dekripsi pesan dengan super enkripsi", icon_bi="envelope-lock-fill")

tab_enc, tab_dec, tab_list = st.tabs(["Enkripsi", "Dekripsi", "Daftar Pesan"])

# ═══════════════════════════════════════════════════════════════════════════════
# Tab Enkripsi
# ═══════════════════════════════════════════════════════════════════════════════
with tab_enc:
    left, right = golden_columns()

    with left:
        st.markdown("#### Input")
        title = st.text_input("Judul pesan", placeholder="Rahasia penting…")
        plaintext = st.text_area("Teks pesan", height=200, placeholder="Tulis pesan rahasia di sini…")
        is_important = st.checkbox("Tandai sebagai penting 🔴")
        col_a, col_b = st.columns(2)
        do_encrypt = col_a.button("Enkripsi & Simpan", use_container_width=True)
        do_preview = col_b.button("Preview Tahapan", use_container_width=True)

    with right:
        st.markdown("#### Hasil")

        if do_preview and plaintext:
            steps = encrypt_text_steps(plaintext, master_key)
            with st.expander("Visualisasi Tahapan Enkripsi", expanded=True):
                st.markdown("**Setelah Vigenère (byte-mode, mod 256):**")
                st.code(steps["after_vigenere"][:200] + ("…" if len(steps["after_vigenere"]) > 200 else ""), language=None)
                st.markdown("**Setelah Columnar Transposition:**")
                st.code(steps["after_transposition"][:200] + ("…" if len(steps["after_transposition"]) > 200 else ""), language=None)
                st.markdown("**Hasil Akhir (Base64 setelah AES-256-GCM):**")
                st.code(steps["final_base64"][:200] + ("…" if len(steps["final_base64"]) > 200 else ""), language=None)

        if do_encrypt:
            if not title or not plaintext:
                st.error("Judul dan teks pesan wajib diisi.")
            else:
                try:
                    # Enkripsi judul & isi
                    token = encrypt_text(plaintext, master_key)
                    title_key = hkdf_derive(master_key, b"db-field", 32)
                    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
                    import os
                    nonce_t = os.urandom(12)
                    title_ct = AESGCM(title_key).encrypt(
                        nonce_t, title.encode("utf-8"),
                        b"messages:title_enc:0"
                    )
                    title_blob = nonce_t + title_ct

                    msg_id = db_models.save_message(
                        user_id=user_id,
                        title_enc=title_blob,
                        body_enc=token.encode("ascii"),
                        is_important=is_important,
                    )
                    st.success(f"Pesan disimpan (ID #{msg_id}).")
                    st.code(token[:300] + ("…" if len(token) > 300 else ""), language=None)
                except Exception as e:
                    st.error(f"Enkripsi gagal: {e}")


# ═══════════════════════════════════════════════════════════════════════════════
# Tab Dekripsi
# ═══════════════════════════════════════════════════════════════════════════════
with tab_dec:
    left2, right2 = golden_columns()

    with left2:
        st.markdown("#### Input Token")
        token_in = st.text_area(
            "Tempel token Base64",
            height=180,
            placeholder="AQAAAAAAAAAAAAAAAAaaaa…",
        )
        do_decrypt = st.button("Dekripsi", use_container_width=True)

    with right2:
        st.markdown("#### Hasil Dekripsi")
        if do_decrypt:
            if not token_in.strip():
                st.error("Token tidak boleh kosong.")
            else:
                try:
                    result = decrypt_text(token_in.strip(), master_key)
                    st.success("Dekripsi berhasil!")
                    st.text_area("Plaintext", value=result, height=200)
                except ValueError as e:
                    st.error(f"❌ Dekripsi gagal: {e}")


# ═══════════════════════════════════════════════════════════════════════════════
# Tab Daftar Pesan
# ═══════════════════════════════════════════════════════════════════════════════
with tab_list:
    rows = db_models.list_messages(user_id)
    if not rows:
        st.info("Belum ada pesan tersimpan.")
    else:
        for row in rows:
            with st.expander(f"Pesan #{row['id']} — {row['created_at']}" +
                             (" 🔴" if row["is_important"] else "")):
                try:
                    body_token = row["body_enc"].decode("ascii") if isinstance(row["body_enc"], bytes) else row["body_enc"]
                    decrypted = decrypt_text(body_token, master_key)
                    st.text_area(f"Isi pesan #{row['id']}", value=decrypted, height=120)
                except Exception as e:
                    st.warning(f"Tidak bisa dekripsi: {e}")
                if st.button(f"Hapus #{row['id']}", key=f"del_msg_{row['id']}"):
                    db_models.delete_message(user_id, row["id"])
                    st.rerun()

quick_menu()
footer()