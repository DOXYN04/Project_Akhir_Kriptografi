"""
pages/7_Passkey.py — Manajemen Passkey / WebAuthn (hanya setelah login).
Diperbarui untuk pendaftaran biometrik otomatis via browser API.
"""

import streamlit as st
import json
import time
import config
from core.auth.session import require_auth, get_current_user_id
from ui.styles import inject_global_css, dev_mode_banner
from ui.components import quick_menu, page_header, navbar, footer

st.set_page_config(
    page_title=f"Passkey — {config.APP_NAME}",
    page_icon="🔐",
    layout="wide",
)

require_auth()
inject_global_css()
navbar("passkey")

if config.DEV_MODE:
    dev_mode_banner()

user_id: int = get_current_user_id()

page_header(
    "Manajemen Passkey",
    "Daftarkan atau kelola passkey biometrik / FIDO2 Anda",
    icon_bi="fingerprint",
)

st.markdown("---")

if config.DEV_MODE:
    st.info(
        "Fitur Passkey tidak tersedia di DEV MODE. "
        "Untuk menggunakan biometrik, matikan DEV_MODE di file `.env`.",
        icon="ℹ️",
    )
else:
    from core.auth import webauthn_service as wa
    from core.db import models as db_models
    from core.db.database import get_connection
    from ui.webauthn_component import webauthn_widget, read_webauthn_result, get_pending_mode, inject_listener

    inject_listener()

    conn = get_connection()
    try:
        user_row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
        user = dict(user_row) if user_row else None
    finally:
        conn.close()

    col_l, col_r = st.columns(2)

    with col_l:
        st.markdown(
            '<div class="h3" style="margin-bottom:16px">'
            '<i class="bi bi-plus-circle-fill" style="color:var(--primary);margin-right:8px"></i>'
            'Daftarkan Passkey Baru'
            '</div>',
            unsafe_allow_html=True,
        )
        st.markdown(
            '<p style="font-size:14px;color:var(--muted);margin-bottom:20px">'
            'Klik tombol di bawah untuk mendaftarkan biometrik (sidik jari/wajah) perangkat Anda.'
            '</p>',
            unsafe_allow_html=True,
        )

        username = user.get("username", "user") if user else "user"

        if get_pending_mode() == "register":
            reg_result = read_webauthn_result()
            if reg_result:
                try:
                    if isinstance(reg_result, str):
                        reg_result = json.loads(reg_result)
                        
                    cred_id, pub_key = wa.verify_registration(user_id, reg_result)
                    db_models.update_webauthn_credential(user_id, cred_id, pub_key)
                    st.session_state.pop("page_passkey_reg_opts", None)
                    st.success("🎉 Passkey biometrik berhasil didaftarkan!")
                    time.sleep(1.5)
                    st.rerun()
                except Exception as exc:
                    print(f"\n[ERROR PAGE PASSKEY] {exc}\n")
                    st.error(f"Gagal mendaftarkan Passkey: {exc}")
                    st.session_state.pop("page_passkey_reg_opts", None)

        if "page_passkey_reg_opts" not in st.session_state:
            st.session_state["page_passkey_reg_opts"] = wa.generate_registration_options(username, user_id)

        webauthn_widget(mode="register", options_json=st.session_state["page_passkey_reg_opts"])

    with col_r:
        st.markdown(
            '<div class="h3" style="margin-bottom:16px">'
            '<i class="bi bi-shield-check-fill" style="color:var(--primary);margin-right:8px"></i>'
            'Status Passkey'
            '</div>',
            unsafe_allow_html=True,
        )
        if user and user.get("credential_id") and user.get("public_key") not in (b"PENDING", b"DEV_MODE"):
            st.markdown(
                '<div style="background:var(--surface);border:1px solid var(--border);'
                'border-radius:12px;padding:20px">'
                '<div style="display:flex;align-items:center;gap:12px;margin-bottom:12px">'
                '<i class="bi bi-check-circle-fill" style="color:var(--success);font-size:24px"></i>'
                '<span style="font-weight:600">Passkey Aktif</span>'
                '</div>'
                '<p style="font-size:13px;color:var(--muted);margin:0">'
                'Akun Anda sudah terhubung dengan biometrik hardware/FIDO2.'
                '</p>'
                '</div>',
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                '<div style="background:var(--surface);border:1px solid var(--border);'
                'border-radius:12px;padding:20px">'
                '<div style="display:flex;align-items:center;gap:12px;margin-bottom:12px">'
                '<i class="bi bi-exclamation-triangle-fill" style="color:var(--danger);font-size:24px"></i>'
                '<span style="font-weight:600">Belum Ada Passkey</span>'
                '</div>'
                '<p style="font-size:13px;color:var(--muted);margin:0">'
                'Daftarkan Passkey biometrik agar dapat login tanpa passphrase.'
                '</p>'
                '</div>',
                unsafe_allow_html=True,
            )

quick_menu()
footer()