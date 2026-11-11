"""
pages/6_Pengaturan.py — Pengaturan vault: timeout, difficulty PoW, kelola passkey, ekspor/hapus.
"""

import streamlit as st

import config
from core.auth.session import require_auth, logout
from ui.styles import inject_global_css, dev_mode_banner
from ui.components import quick_menu, page_header, navbar, footer

st.set_page_config(
    page_title=f"Pengaturan — {config.APP_NAME}",
    page_icon="🔐",
    layout="wide",
)

require_auth()
inject_global_css()
navbar("settings")

if config.DEV_MODE:
    dev_mode_banner()

page_header("Pengaturan", "Konfigurasi vault Anda", icon_bi="gear-fill")

col_l, col_r = st.columns([1, config.PHI])

# ── Kolom kiri: Pengaturan sesi & PoW ────────────────────────────────────────
with col_l:
    st.markdown("#### Sesi")

    timeout_minutes = st.slider(
        "Timeout idle (menit)",
        min_value=1,
        max_value=60,
        value=config.SESSION_TIMEOUT // 60,
        step=1,
    )
    if st.button("Simpan Timeout", use_container_width=True):
        # Perbarui nilai runtime (berlaku untuk sesi ini saja)
        config.SESSION_TIMEOUT = timeout_minutes * 60
        st.success(f"Timeout diperbarui: {timeout_minutes} menit.")

    st.markdown("---")
    st.markdown("#### Blockchain")

    difficulty = st.slider(
        "PoW Difficulty (jumlah nol awal)",
        min_value=2,
        max_value=4,
        value=config.POW_DIFFICULTY,
    )
    if st.button("Simpan Difficulty", use_container_width=True):
        config.POW_DIFFICULTY = difficulty
        # Reset blockchain cache agar difficulty baru digunakan
        if "blockchain" in st.session_state:
            del st.session_state["blockchain"]
        st.success(f"Difficulty diperbarui: {difficulty}")

    st.markdown("---")
    st.markdown("#### Keluar")
    if st.button("Kunci & Logout", type="primary", use_container_width=True):
        logout()

# ── Kolom kanan: Informasi & statistik ───────────────────────────────────────
with col_r:
    st.markdown("#### Informasi Sistem")

    import platform, sys
    st.markdown(
        f"""
        <div class="card" style="aspect-ratio:unset">
          <table style="width:100%;border-collapse:collapse;color:var(--text)">
            <tr><td style="padding:8px 0;color:var(--muted)">Aplikasi</td>
                <td><strong>{config.APP_NAME}</strong></td></tr>
            <tr><td style="padding:8px 0;color:var(--muted)">Python</td>
                <td>{sys.version.split()[0]}</td></tr>
            <tr><td style="padding:8px 0;color:var(--muted)">Platform</td>
                <td>{platform.system()} {platform.release()}</td></tr>
            <tr><td style="padding:8px 0;color:var(--muted)">DEV MODE</td>
                <td>{"<span style='color:var(--danger)'>Aktif ⚠️</span>" if config.DEV_MODE else "<span style='color:var(--success)'>Nonaktif ✅</span>"}</td></tr>
            <tr><td style="padding:8px 0;color:var(--muted)">RP_ID</td>
                <td><code>{config.RP_ID}</code></td></tr>
            <tr><td style="padding:8px 0;color:var(--muted)">DB Path</td>
                <td><code>{config.DB_PATH}</code></td></tr>
          </table>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("---")
    st.markdown("#### Ekspor & Hapus Data")
    st.warning(
        "Hapus data akan menghapus **seluruh pesan, file, stego, dan blockchain** dari database. "
        "Tindakan ini **tidak dapat dibatalkan**.",
        icon="⚠️",
    )
    confirm = st.checkbox("Saya memahami risiko penghapusan data")
    if st.button("Hapus Semua Data", disabled=not confirm, use_container_width=True):
        from core.db.database import get_connection
        with get_connection() as conn:
            conn.execute("DELETE FROM messages")
            conn.execute("DELETE FROM files")
            conn.execute("DELETE FROM stego_items")
            conn.execute("DELETE FROM blocks")
            conn.commit()
        if "blockchain" in st.session_state:
            del st.session_state["blockchain"]
        st.success("Semua data vault telah dihapus.")
        st.rerun()

quick_menu()
footer()
