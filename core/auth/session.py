"""
core/auth/session.py — Manajemen sesi HMAC + gerbang autentikasi.
Diperbarui untuk mendukung getter user_id multi-user.
"""

import hmac
import hashlib
import time
import os
import streamlit as st

import config


def _sign_token(payload: str, secret: bytes) -> str:
    """Buat HMAC-SHA256 atas payload."""
    return hmac.new(secret, payload.encode(), hashlib.sha256).hexdigest()


def create_session(user_id: int, master_key: bytes) -> None:
    """
    Buat sesi baru setelah login berhasil.
    Simpan token HMAC, waktu mulai, dan master_key di session_state.
    """
    secret = config.SESSION_SECRET.encode() or os.urandom(32)
    issued = time.time()
    payload = f"{user_id}:{issued}"
    token = _sign_token(payload, secret)

    s = st.session_state
    s["auth_ok"] = True
    s["auth_user_id"] = user_id
    s["auth_issued"] = issued
    s["auth_token"] = token
    s["auth_payload"] = payload
    s["master_key"] = master_key
    s["last_activity"] = issued


def get_current_user_id() -> int:
    """Mengembalikan user_id dari sesi pengguna yang sedang login."""
    return st.session_state.get("auth_user_id", 1)


def session_expired(s: dict) -> bool:
    """Kembalikan True bila sesi sudah melewati SESSION_TIMEOUT."""
    last = s.get("last_activity", 0)
    return (time.time() - last) > config.SESSION_TIMEOUT


def touch_session() -> None:
    """Perbarui waktu aktivitas terakhir sesi."""
    if st.session_state.get("auth_ok"):
        st.session_state["last_activity"] = time.time()


def _clear_session() -> None:
    """Hapus semua data sesi sensitif dari session_state."""
    sensitive = [
        "auth_ok", "auth_user_id", "auth_issued", "auth_token",
        "auth_payload", "master_key", "last_activity", "auth_username",
        "blockchain", "blockchain_user_id", "passkey_auth_opts",
        "passkey_reg_opts", "pending_reg", "pending_reg_user_id"
    ]
    for k in sensitive:
        if k in st.session_state:
            if k == "master_key":
                # Timpa kunci master dengan nol sebelum dihapus
                try:
                    st.session_state[k] = bytes(len(st.session_state[k]))
                except Exception:
                    pass
            del st.session_state[k]


def require_auth() -> None:
    """
    Gerbang autentikasi — panggil di baris pertama setiap halaman.
    Bila tidak ada sesi sah atau sesi habis waktu, arahkan ke login.
    """
    s = st.session_state
    if not s.get("auth_ok"):
        st.switch_page("app.py")
        st.stop()
    if session_expired(s):
        _clear_session()
        st.switch_page("app.py")
        st.stop()
    touch_session()


def logout() -> None:
    """Logout manual: hapus sesi dan kembali ke login."""
    _clear_session()
    st.switch_page("app.py")
    st.stop()