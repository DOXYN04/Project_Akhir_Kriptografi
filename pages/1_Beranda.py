"""
pages/1_Beranda.py — Halaman beranda Obsidian Vault (Isolasi Multi-User).
Menampilkan statistik dan kartu pintasan khusus user yang sedang login.
"""

import streamlit as st

import config
from core.auth.session import require_auth, get_current_user_id
from ui.styles import inject_global_css, dev_mode_banner
from ui.components import quick_menu, stat_card, page_header, navbar, footer
from core.db import models as db_models

st.set_page_config(
    page_title=f"Beranda — {config.APP_NAME}",
    page_icon="🏠",
    layout="wide",
)

require_auth()
inject_global_css()
navbar("beranda")   # tanpa tombol Back

if config.DEV_MODE:
    dev_mode_banner()

# ── Ambil User ID dari Sesi ──────────────────────────────────────────────────
user_id = get_current_user_id()

# ── Statistik Khusus User ─────────────────────────────────────────────────────
msg_count   = len(db_models.list_messages(user_id))
file_count  = len(db_models.list_files(user_id))
stego_count = len(db_models.list_stego_items(user_id))
block_count = len(db_models.load_blocks(user_id))

page_header("Beranda", "Ringkasan keamanan brankas Anda", icon_bi="house-fill")

# ── Kartu statistik ───────────────────────────────────────────────────────────
col1, col2, col3, col4 = st.columns(4)
with col1:
    stat_card("Pesan Teks", str(msg_count), icon_bi="envelope-fill")
with col2:
    stat_card("File Terenkripsi", str(file_count), icon_bi="file-earmark-lock2-fill")
with col3:
    stat_card("Gambar Stego", str(stego_count), icon_bi="image-fill")
with col4:
    stat_card("Blok Rantai", str(block_count), icon_bi="link-45deg")

st.markdown("---")

# ── Kartu pintasan ────────────────────────────────────────────────────────────
st.markdown(
    '<div class="h3" style="margin-bottom:21px">'
    '<i class="bi bi-lightning-charge-fill" style="color:var(--primary);margin-right:8px"></i>'
    'Aksi Cepat</div>',
    unsafe_allow_html=True,
)

c1, c2, c3, c4, c5 = st.columns(5)
with c1:
    if st.button("Pesan Teks", use_container_width=True):
        st.switch_page("pages/2_Pesan_Teks.py")
with c2:
    if st.button("Enkripsi File", use_container_width=True):
        st.switch_page("pages/3_Pesan_File.py")
with c3:
    if st.button("Stego Gambar", use_container_width=True):
        st.switch_page("pages/4_Pesan_Gambar.py")
with c4:
    if st.button("Aset Blockchain", use_container_width=True):
        st.switch_page("pages/5_Aset_Blockchain.py")
with c5:
    if st.button("Pengaturan", use_container_width=True):
        st.switch_page("pages/6_Pengaturan.py")

# ── Status keamanan ───────────────────────────────────────────────────────────
st.markdown("---")
st.markdown(
    '<div class="h3" style="margin-bottom:21px">'
    '<i class="bi bi-shield-check-fill" style="color:var(--primary);margin-right:8px"></i>'
    'Status Keamanan</div>',
    unsafe_allow_html=True,
)

import time
idle      = time.time() - st.session_state.get("last_activity", time.time())
timeout   = config.SESSION_TIMEOUT
remaining = max(0, int(timeout - idle))
pct       = remaining / timeout

col_s1, col_s2 = st.columns([1, config.PHI])
with col_s1:
    st.metric("Sesi aktif tersisa", f"{remaining // 60} mnt {remaining % 60} dtk")
    st.progress(pct, text=f"Timeout dalam {remaining} detik")
with col_s2:
    st.markdown(
        """
        <div class="card" style="aspect-ratio:unset">
          <div class="h3">
            <i class="bi bi-shield-fill-check" style="color:var(--success)"></i>
            Enkripsi Aktif
          </div>
          <ul style="color:var(--muted);line-height:2;margin-top:13px">
            <li>Teks: <strong style="color:var(--text)">Super Enkripsi (Vigenère + Transposisi + AES-256-GCM)</strong></li>
            <li>File: <strong style="color:var(--text)">ChaCha20-Poly1305 (chunked)</strong></li>
            <li>Gambar: <strong style="color:var(--text)">LSB Steganografi + AES-256-GCM</strong></li>
            <li>Blockchain: <strong style="color:var(--text)">SHA-256 + HMAC-SHA256 + PoW</strong></li>
            <li>Database: <strong style="color:var(--text)">AES-256-GCM per kolom</strong></li>
          </ul>
        </div>
        """,
        unsafe_allow_html=True,
    )

quick_menu()
footer()