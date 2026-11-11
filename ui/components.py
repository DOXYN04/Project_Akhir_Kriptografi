"""
ui/components.py — Reusable UI components for Obsidian Vault.

Public API:
  navbar(page_key)  — fixed header bar; app name navigates to Beranda;
                      back button appears on every page except Beranda.
  footer()          — copyright footer (all pages including auth).
  quick_menu()      — FAB speed-dial (authenticated pages only).
  stat_card(...)    — metric card for Beranda dashboard.
  page_header(...)  — section heading inside a page.
  badge(...)        — small pill label.
"""

import streamlit as st
import config

# ── Page metadata ──────────────────────────────────────────────────────────────
_PAGES = {
    # key: (bootstrap-icon-name, display-title, page-file)
    "beranda":  ("house-fill",             "Beranda",          "pages/1_Beranda.py"),
    "message":  ("envelope-lock-fill",     "Pesan Teks",       "pages/2_Pesan_Teks.py"),
    "file":     ("file-earmark-lock2-fill","Enkripsi File",     "pages/3_Pesan_File.py"),
    "stego":    ("image-fill",             "Pesan Gambar",      "pages/4_Pesan_Gambar.py"),
    "asset":    ("link-45deg",             "Aset Blockchain",   "pages/5_Aset_Blockchain.py"),
    "settings": ("gear-fill",             "Pengaturan",        "pages/6_Pengaturan.py"),
    "passkey":  ("fingerprint",            "Passkey",           "pages/7_Passkey.py"),
}


def navbar(page_key: str = "beranda") -> None:
    """
    Render a fixed header bar at the top of every authenticated page.

    Left  : [← Back] [🛡 APP_NAME]  — APP_NAME always links to Beranda.
             Back button only shown when page_key != "beranda".
    Center: [icon] Page Title
    Right : [user avatar] username

    Navigation is handled via Streamlit query params so it survives reruns.
    """
    icon, title, _ = _PAGES.get(page_key, ("shield-fill", config.APP_NAME, "app.py"))
    show_back = page_key != "beranda"
    username  = st.session_state.get("auth_username", "")

    # ── Handle incoming query params FIRST (before rendering) ──────────────────
    nav_target = st.query_params.get("nav", "")
    if nav_target and nav_target in _PAGES:
        st.query_params.clear()
        st.switch_page(_PAGES[nav_target][2])
        st.stop()

    # ── Build HTML pieces (kept small to avoid Streamlit truncation) ───────────
    back_btn = ""
    if show_back:
        back_btn = (
            '<a class="nav-back" href="?nav=beranda" title="Kembali ke Beranda">'
            '<i class="bi bi-arrow-left-short nav-back-icon"></i>'
            '<span>Kembali</span>'
            '</a>'
        )

    brand = (
        f'<a class="nav-brand" href="?nav=beranda" title="Beranda">'
        f'<i class="bi bi-shield-lock-fill nav-brand-icon"></i>'
        f'<span class="nav-brand-text">{config.APP_NAME}</span>'
        f'</a>'
    )

    center = (
        f'<div class="nav-center">'
        f'<i class="bi bi-{icon} nav-page-icon"></i>'
        f'<span class="nav-page-title">{title}</span>'
        f'</div>'
    )

    user_badge = ""
    if username:
        user_badge = (
            f'<span class="nav-user">'
            f'<i class="bi bi-person-circle"></i> {username}'
            f'</span>'
        )

    st.markdown(
        f'<header class="app-navbar">'
        f'  <div class="nav-left">{back_btn}{brand}</div>'
        f'  {center}'
        f'  <div class="nav-right">{user_badge}</div>'
        f'</header>'
        f'<div class="navbar-spacer"></div>',
        unsafe_allow_html=True,
    )


def footer() -> None:
    """Copyright footer — shown on every page including the auth page."""
    st.markdown(
        '<footer class="app-footer">'
        '<div class="footer-inner">'

        '<div class="footer-brand">'
        '<i class="bi bi-shield-lock-fill"></i>'
        '<span>OBSIDIAN VAULT</span>'
        '</div>'

        '<div class="footer-tagline">'
        'Proyek Tugas Akhir &mdash; Mata Kuliah Kriptografi'
        '</div>'

        '<div class="footer-authors">'
        '<span>Ghazian Muhammad Al Faruq</span>'
        '<span class="footer-nim">123240013</span>'
        '<span class="footer-sep">&bull;</span>'
        '<span>M. Diandra AlFashya Munandar</span>'
        '<span class="footer-nim">123240022</span>'
        '</div>'

        '<div class="footer-copy">'
        '&copy; 2025 &mdash; Semua data dienkripsi secara lokal di perangkat Anda'
        '</div>'

        '</div>'
        '</footer>',
        unsafe_allow_html=True,
    )


# ── Quick-access FAB ──────────────────────────────────────────────────────────
_FAB_HTML = """
<div class="fab-container" id="fab-container">
  <button class="fab-main" onclick="toggleFab()"
          title="Menu Cepat" aria-label="Buka menu cepat">
    <i class="bi bi-plus-lg"></i>
  </button>
  <div class="fab-items" id="fab-items" style="display:none"
       role="menu" aria-label="Navigasi cepat">
    <a class="fab-item" href="?go=lock"    role="menuitem">
      <i class="bi bi-lock-fill"></i> Kunci Sesi
    </a>
    <a class="fab-item" href="?go=settings" role="menuitem">
      <i class="bi bi-gear-fill"></i> Pengaturan
    </a>
    <a class="fab-item" href="?go=passkey" role="menuitem">
      <i class="bi bi-fingerprint"></i> Passkey
    </a>
    <a class="fab-item" href="?go=message" role="menuitem">
      <i class="bi bi-envelope-fill"></i> Pesan Teks
    </a>
    <a class="fab-item" href="?go=file"    role="menuitem">
      <i class="bi bi-file-earmark-lock-fill"></i> Enkripsi File
    </a>
    <a class="fab-item" href="?go=stego"   role="menuitem">
      <i class="bi bi-image-fill"></i> Stego Gambar
    </a>
    <a class="fab-item" href="?go=asset"   role="menuitem">
      <i class="bi bi-link-45deg"></i> Blockchain
    </a>
  </div>
</div>
<script>
function toggleFab(){
  var el  = document.getElementById('fab-items');
  var btn = document.querySelector('.fab-main');
  var open = el.style.display !== 'none';
  el.style.display    = open ? 'none' : 'flex';
  btn.style.transform = open ? ''     : 'rotate(45deg) scale(1.08)';
}
document.addEventListener('click', function(e){
  var c = document.getElementById('fab-container');
  if (c && !c.contains(e.target)) {
    var el  = document.getElementById('fab-items');
    var btn = document.querySelector('.fab-main');
    if (el)  el.style.display    = 'none';
    if (btn) btn.style.transform = '';
  }
});
</script>
"""

_FAB_ROUTES = {
    "message":  "pages/2_Pesan_Teks.py",
    "file":     "pages/3_Pesan_File.py",
    "stego":    "pages/4_Pesan_Gambar.py",
    "asset":    "pages/5_Aset_Blockchain.py",
    "passkey":  "pages/7_Passkey.py",
    "settings": "pages/6_Pengaturan.py",
}


def quick_menu() -> None:
    """Render FAB + handle navigation query params."""
    st.markdown(_FAB_HTML, unsafe_allow_html=True)
    dest = st.query_params.get("go", "")
    if dest == "lock":
        for k in list(st.session_state.keys()):
            del st.session_state[k]
        st.query_params.clear()
        st.switch_page("app.py")
    elif dest in _FAB_ROUTES:
        st.query_params.clear()
        st.switch_page(_FAB_ROUTES[dest])


# ── Stat card ─────────────────────────────────────────────────────────────────
def stat_card(label: str, value: str, icon_bi: str = "") -> None:
    """Metric card for the Beranda dashboard."""
    icon_html = (
        f'<i class="bi bi-{icon_bi}" style="font-size:24px;color:var(--primary)"></i>'
        if icon_bi else ""
    )
    st.markdown(
        f'<div class="stat-card">'
        f'  <div class="stat-icon">{icon_html}</div>'
        f'  <div>'
        f'    <div class="stat-label">{label}</div>'
        f'    <div class="stat-value">{value}</div>'
        f'  </div>'
        f'</div>',
        unsafe_allow_html=True,
    )


# ── Section heading ───────────────────────────────────────────────────────────
def page_header(title: str, subtitle: str = "", icon_bi: str = "") -> None:
    """Section heading inside a page (rendered below the navbar)."""
    icon_html = (
        f'<i class="bi bi-{icon_bi}" style="color:var(--primary);margin-right:8px"></i>'
        if icon_bi else ""
    )
    st.markdown(
        f'<div class="section-title">{icon_html}{title}</div>',
        unsafe_allow_html=True,
    )
    if subtitle:
        st.markdown(
            f'<div class="section-sub">{subtitle}</div>',
            unsafe_allow_html=True,
        )


# ── Badge ─────────────────────────────────────────────────────────────────────
def badge(text: str, color: str = "var(--primary)") -> None:
    """Small colored pill label."""
    st.markdown(
        f'<span style="background:{color};color:#fff;border-radius:50px;'
        f'padding:3px 12px;font-size:12px;font-weight:600">{text}</span>',
        unsafe_allow_html=True,
    )
