"""
app.py — Obsidian Vault authentication gateway.
First page shown: Login / Register (state machine, no sidebar, no quick menu).
"""

import os
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

import config
from core.db.database import init_db
from ui.styles import inject_global_css, hide_sidebar, dev_mode_banner
from ui.components import footer

# ── One-time DB init ──────────────────────────────────────────────────────────
if "db_init" not in st.session_state:
    init_db()
    st.session_state["db_init"] = True

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title=config.APP_NAME,
    page_icon="🔐",
    layout="wide",
    initial_sidebar_state="collapsed",
)

inject_global_css()
hide_sidebar()

if config.DEV_MODE:
    dev_mode_banner()

# ── Auth page extra styles ────────────────────────────────────────────────────
st.markdown("""
<style>
/* First column = branding panel */
[data-testid="column"]:first-child {
  background: var(--surface);
  border-right: 1px solid var(--border);
}
/* Divider between passphrase form and passkey button */
.or-divider {
  display: flex; align-items: center; gap: 10px;
  margin: 18px 0; color: var(--muted); font-size: 12px;
}
.or-divider::before, .or-divider::after {
  content: ''; flex: 1;
  height: 1px; background: var(--border);
}
/* Passkey button — ghost blue border */
.passkey-btn-wrap button {
  background: transparent !important;
  border: 1px solid var(--primary) !important;
  color: var(--primary) !important;
}
.passkey-btn-wrap button:hover {
  background: rgba(47,107,255,.1) !important;
}

@keyframes slideDownForm {
  0% {
    opacity: 0;
    transform: translateY(-15px);
  }
  100% {
    opacity: 1;
    transform: translateY(0);
  }
}

.auth-form-dropdown {
  animation: slideDownForm 0.35s ease-out forwards;
}

</style>
""", unsafe_allow_html=True)

# ── Already authenticated → dashboard ────────────────────────────────────────
if st.session_state.get("auth_ok"):
    st.switch_page("pages/1_Beranda.py")
    st.stop()

# ── Auth mode state machine ───────────────────────────────────────────────────
if "auth_mode" not in st.session_state:
    st.session_state["auth_mode"] = "login"

# ── Auth imports ──────────────────────────────────────────────────────────────
from core.db import models as db_models
from core.auth.kdf import hash_pin, verify_pin, derive_master_key
from core.auth.session import create_session

# ── Inject WebAuthn postMessage listener (produksi only, height=0) ───────────
# Dipanggil di luar semua kondisi agar listener selalu aktif saat halaman dimuat.
if not config.DEV_MODE:
    from ui.webauthn_component import inject_listener
    inject_listener()

# ═════════════════════════════════════════════════════════════════════════════
# TWO-COLUMN LAYOUT  Left → Branding  |  Right → Form
# ═════════════════════════════════════════════════════════════════════════════
col_brand, col_form = st.columns([1, 1], gap="small")

# ─────────────────────────────────────────────────────────────────────────────
# LEFT — Branding panel
# ─────────────────────────────────────────────────────────────────────────────
with col_brand:
    mode      = st.session_state["auth_mode"]
    icon_name = "shield-lock-fill" if mode == "login" else "person-plus-fill"
    tagline   = (
        "Masukkan passphrase atau gunakan Passkey untuk membuka brankas."
        if mode == "login"
        else "Buat akun baru untuk mulai melindungi data Anda."
    )

    st.markdown(
        f'<div class="auth-brand">'
        f'<div class="auth-logo"><i class="bi bi-{icon_name}"></i></div>'
        f'<p class="auth-eyebrow">SISTEM KEAMANAN DIGITAL</p>'
        f'<h1 class="auth-app-title">{config.APP_NAME}</h1>'
        f'<p class="auth-tagline">{tagline}</p>',
        unsafe_allow_html=True,
    )

    features = [
        ("envelope-lock-fill",      "Enkripsi pesan berlapis (AES-256-GCM)"),
        ("file-earmark-lock2-fill", "Enkripsi file (ChaCha20-Poly1305)"),
        ("image-fill",              "Steganografi gambar (LSB + AES-GCM)"),
        ("link-45deg",              "Blockchain aset (SHA-256 + HMAC + PoW)"),
    ]
    feat_html = '<div class="feat-list">'
    for ic, txt in features:
        feat_html += (
            f'<div class="feat-item">'
            f'<i class="bi bi-{ic}"></i>'
            f'<span>{txt}</span>'
            f'</div>'
        )
    feat_html += '</div>'
    st.markdown(feat_html, unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# RIGHT — Auth form
# ─────────────────────────────────────────────────────────────────────────────
with col_form:

    # ── Tab bar: Masuk | Daftar ───────────────────────────────────────────────
    is_login = st.session_state["auth_mode"] == "login"
    is_reg   = st.session_state["auth_mode"] == "register"

    tc1, tc2 = st.columns(2)
    with tc1:
        if st.button(
            "Masuk",
            use_container_width=True,
            type="primary" if is_login else "secondary",
            key="tab_masuk",
        ):
            st.session_state["auth_mode"] = "login"
            st.rerun()
    with tc2:
        if st.button(
            "Daftar",
            use_container_width=True,
            type="primary" if is_reg else "secondary",
            key="tab_daftar",
        ):
            st.session_state["auth_mode"] = "register"
            st.rerun()

    st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)
# ═════════════════════════════════════════════════════════════════════════
    # MODE: LOGIN
    # ═════════════════════════════════════════════════════════════════════════
    if st.session_state["auth_mode"] == "login":
        st.markdown('<div class="auth-form-dropdown">', unsafe_allow_html=True)

        st.markdown(
            '<div class="form-heading">'
            '<i class="bi bi-box-arrow-in-right"></i> Masuk ke Brankas'
            '</div>'
            '<p class="form-sub">'
            'Masukkan nama pengguna dan passphrase, '
            'atau gunakan Passkey biometrik Anda.'
            '</p>',
            unsafe_allow_html=True,
        )

        # ── Form passphrase ───────────────────────────────────────────────────
        with st.form("form_login", clear_on_submit=False):
            uname_in = st.text_input(
                "Nama Pengguna",
                placeholder="Contoh: diandra",
                value=st.session_state.get("prefill_username", ""),
            )
            pass_in = st.text_input(
                "Passphrase",
                type="password",
                placeholder="Masukkan passphrase Anda",
            )
            login_btn = st.form_submit_button(
                "Masuk dengan Passphrase",
                use_container_width=True,
            )

        if login_btn:
            u = uname_in.strip()
            if not u or not pass_in:
                st.error("Nama pengguna dan passphrase wajib diisi.")
            else:
                user = db_models.get_user_by_username(u)
                if not user:
                    st.error(
                        "Akun tidak ditemukan. "
                        "Buka tab **Daftar** untuk membuat akun baru."
                    )
                elif not user.get("pin_hash"):
                    st.error("Akun ini tidak mendukung login passphrase.")
                elif verify_pin(pass_in, user["pin_hash"]):
                    master_key = derive_master_key(
                        pass_in.encode("utf-8"),
                        user["kdf_salt"],
                    )
                    create_session(user["id"], master_key)
                    st.session_state["auth_username"] = u
                    st.session_state.pop("prefill_username", None)
                    st.success("Login berhasil! Membuka brankas…")
                    st.rerun()
                else:
                    st.error("Passphrase salah. Coba lagi.")

        # ── Divider ───────────────────────────────────────────────────────────
        st.markdown(
            '<div class="or-divider">atau</div>',
            unsafe_allow_html=True,
        )

        # ── Tombol Passkey ────────────────────────────────────────────────────
        if config.DEV_MODE:
            # DEV MODE: passkey hardware tidak tersedia, tampilkan info
            st.markdown('<div class="passkey-btn-wrap">', unsafe_allow_html=True)
            if st.button(
                "Masuk dengan Passkey / Biometrik",
                use_container_width=True,
                key="btn_passkey_login",
            ):
                st.info(
                    "**Passkey tidak tersedia di DEV MODE.**  \n"
                    "Untuk menggunakan biometrik (sidik jari / wajah / FIDO2), "
                    "set `DEV_MODE=false` di file `.env` dan restart aplikasi.",
                    icon="ℹ️",
                )
            st.markdown('</div>', unsafe_allow_html=True)
        else:
            # PRODUKSI: alur WebAuthn langsung via browser API (tanpa PyArrow)
            from core.auth import webauthn_service as wa
            from ui.webauthn_component import webauthn_widget, read_webauthn_result, get_pending_mode

            user_row = db_models.get_first_user()
            if not user_row:
                st.warning(
                    "Belum ada akun dengan Passkey terdaftar. "
                    "Buka tab **Daftar** terlebih dahulu.",
                    icon="⚠️",
                )
            else:
                # Cek apakah ada hasil WebAuthn yang baru kembali via query params
                if get_pending_mode() == "authenticate":
                    auth_result = read_webauthn_result()
                    if auth_result:
                        try:
                            new_count = wa.verify_authentication(
                                user_row["id"],
                                auth_result,
                                user_row["public_key"],
                                user_row["sign_count"],
                            )
                            db_models.update_sign_count(user_row["id"], new_count)
                            master_key = derive_master_key(
                                user_row["credential_id"],
                                user_row["kdf_salt"],
                            )
                            create_session(user_row["id"], master_key)
                            st.session_state["auth_username"] = (
                                user_row.get("username") or "user"
                            )
                            st.session_state.pop("passkey_auth_opts", None)
                            st.success("Autentikasi Passkey berhasil!")
                            st.rerun()
                        except Exception as exc:
                            st.error(f"Verifikasi gagal: {exc}")
                            st.session_state.pop("passkey_auth_opts", None)

                # Generate opsi sekali per sesi
                if "passkey_auth_opts" not in st.session_state:
                    st.session_state["passkey_auth_opts"] = wa.generate_authentication_options(
                        user_row["id"], user_row["credential_id"]
                    )

                # Tampilkan tombol — klik langsung trigger biometrik di browser
                webauthn_widget(
                    mode="authenticate",
                    options_json=st.session_state["passkey_auth_opts"],
                )

        # Penutup container animasi Mode Login (diletakkan di luar `if/else` DEV_MODE)
        st.markdown('</div>', unsafe_allow_html=True)

    # ═════════════════════════════════════════════════════════════════════════
    # MODE: REGISTER
    # ═════════════════════════════════════════════════════════════════════════
    else:
        st.markdown('<div class="auth-form-dropdown">', unsafe_allow_html=True)
        st.markdown(
            '<div class="form-heading">'
            '<i class="bi bi-person-plus-fill"></i> Buat Akun Baru'
            '</div>'
            '<p class="form-sub">'
            'Isi formulir berikut untuk mendaftarkan akun brankas terenkripsi Anda.'
            '</p>',
            unsafe_allow_html=True,
        )

        with st.form("form_register", clear_on_submit=True):
            uname_reg = st.text_input(
                "Nama Pengguna",
                placeholder="Minimal 3 karakter",
            )
            pass_reg = st.text_input(
                "Passphrase",
                type="password",
                placeholder="Minimal 8 karakter",
            )
            pass_reg2 = st.text_input(
                "Konfirmasi Passphrase",
                type="password",
                placeholder="Ulangi passphrase di atas",
            )
            reg_btn = st.form_submit_button(
                "Buat Akun",
                use_container_width=True,
            )

        if reg_btn:
            u   = uname_reg.strip()
            err = None
            if   not u:                err = "Nama pengguna wajib diisi."
            elif len(u) < 3:           err = "Nama pengguna minimal 3 karakter."
            elif not pass_reg:         err = "Passphrase wajib diisi."
            elif len(pass_reg) < 8:    err = "Passphrase minimal 8 karakter."
            elif pass_reg != pass_reg2: err = "Passphrase tidak cocok."

            if err:
                st.error(err)
            elif db_models.get_user_by_username(u):
                st.error(f"Nama pengguna **{u}** sudah digunakan.")
            else:
                try:
                    pin_hash = hash_pin(pass_reg)
                    salt     = os.urandom(16)
                    if config.DEV_MODE:
                        # DEV MODE: simpan langsung tanpa WebAuthn
                        db_models.create_user(
                            credential_id=os.urandom(16),
                            public_key=b"DEV_MODE",
                            kdf_salt=salt,
                            pin_hash=pin_hash,
                            username=u,
                        )
                        st.success(f"Akun **{u}** berhasil dibuat!")
                        st.info(
                            "Passphrase di-hash dengan Argon2id — tidak bisa dibaca balik.  \n"
                            "Klik tab **Masuk** untuk login."
                        )
                        st.session_state["prefill_username"] = u
                    else:
                        # PRODUKSI: simpan data sementara, lanjut ke pendaftaran passkey
                        st.session_state["pending_reg"] = {
                            "username": u,
                            "pin_hash": pin_hash,
                            "kdf_salt": salt,
                        }
                        st.rerun()
                except Exception as exc:
                    st.error(f"Gagal membuat akun: {exc}")

        # ── Langkah 2 pendaftaran produksi: daftarkan Passkey ─────────────────
        if not config.DEV_MODE and "pending_reg" in st.session_state:
            from core.auth import webauthn_service as wa
            from ui.webauthn_component import webauthn_widget, read_webauthn_result, get_pending_mode

            pending = st.session_state["pending_reg"]
            u       = pending["username"]

            # Buat user sementara di DB jika belum ada (butuh ID untuk challenge)
            if "pending_reg_user_id" not in st.session_state:
                tmp_id = db_models.create_user(
                    credential_id=os.urandom(16),
                    public_key=b"PENDING",
                    kdf_salt=pending["kdf_salt"],
                    pin_hash=pending["pin_hash"],
                    username=u,
                )
                st.session_state["pending_reg_user_id"] = tmp_id

            user_id = st.session_state["pending_reg_user_id"]

            # Cek apakah ada hasil registrasi yang baru kembali via query params
# ── Footer ────────────────────────────────────────────────────────────────────
footer()
