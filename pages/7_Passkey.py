"""
pages/7_Passkey.py — Manajemen Passkey / WebAuthn (hanya setelah login).
Fitur ini hanya tersedia untuk mode produksi (bukan DEV_MODE).
"""

import streamlit as st
import json
import os

import config
from core.auth.session import require_auth
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
    st.markdown(
        """
        <div style="background:var(--surface-2);border:1px solid var(--border);
          border-radius:12px;padding:20px 24px;margin-top:16px">
          <p style="font-size:14px;color:var(--muted);margin:0 0 12px">
            <i class="bi bi-file-text-fill" style="color:var(--primary)"></i>
            Untuk mengaktifkan WebAuthn/Passkey, edit file <code>.env</code>:
          </p>
          <pre style="background:var(--bg);border:1px solid var(--border);
            border-radius:8px;padding:12px;font-size:13px;color:var(--text);
            margin:0">DEV_MODE=false
RP_ID=localhost
RP_NAME=Obsidian Vault
ORIGIN=http://localhost:8501</pre>
        </div>
        """,
        unsafe_allow_html=True,
    )
else:
    from core.auth import webauthn_service as wa
    from core.db import models as db_models

    user = db_models.get_first_user()

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
            'Daftarkan biometrik (sidik jari/wajah) atau kunci keamanan FIDO2.'
            '</p>',
            unsafe_allow_html=True,
        )

        if st.button(
            "Generate Opsi Pendaftaran",
            use_container_width=True,
            type="primary",
            key="btn_gen_reg",
        ):
            opts_json = wa.generate_registration_options("vault-user", 1)
            st.session_state["reg_options"] = opts_json

        if "reg_options" in st.session_state:
            st.markdown(
                '<p style="font-size:12px;color:var(--muted);margin:12px 0 6px">'
                'Salin JSON di bawah ke WebAuthn client browser Anda:'
                '</p>',
                unsafe_allow_html=True,
            )
            st.code(st.session_state["reg_options"], language="json")
            reg_response = st.text_area(
                "Tempel respons registrasi (JSON)",
                height=120,
                key="reg_resp_input",
            )
            if st.button(
                "Verifikasi & Simpan Passkey",
                use_container_width=True,
                key="btn_verify_reg",
            ):
                try:
                    cred = json.loads(reg_response)
                    cred_id, pub_key = wa.verify_registration(1, cred)
                    salt = os.urandom(16)
                    db_models.create_user(
                        credential_id=cred_id,
                        public_key=pub_key,
                        kdf_salt=salt,
                    )
                    del st.session_state["reg_options"]
                    st.success("Passkey berhasil didaftarkan!")
                    st.rerun()
                except Exception as exc:
                    st.error(f"Gagal mendaftarkan passkey: {exc}")

    with col_r:
        st.markdown(
            '<div class="h3" style="margin-bottom:16px">'
            '<i class="bi bi-shield-check-fill" style="color:var(--primary);margin-right:8px"></i>'
            'Status Passkey'
            '</div>',
            unsafe_allow_html=True,
        )
        if user and user.get("credential_id"):
            st.markdown(
                '<div style="background:var(--surface);border:1px solid var(--border);'
                'border-radius:12px;padding:20px">'
                '<div style="display:flex;align-items:center;gap:12px;margin-bottom:12px">'
                '<i class="bi bi-check-circle-fill" style="color:var(--success);font-size:24px"></i>'
                '<span style="font-weight:600">Passkey Aktif</span>'
                '</div>'
                '<p style="font-size:13px;color:var(--muted);margin:0">'
                'Akun Anda sudah terlindungi dengan passkey biometrik/FIDO2.'
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
                'Daftarkan passkey untuk keamanan biometrik.'
                '</p>'
                '</div>',
                unsafe_allow_html=True,
            )

quick_menu()
footer()
