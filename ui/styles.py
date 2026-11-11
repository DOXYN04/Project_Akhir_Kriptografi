"""
ui/styles.py — Global CSS + Bootstrap Icons injection for Obsidian Vault.
"""

import streamlit as st
import streamlit.components.v1 as components

# ── CDN Bootstrap Icons ───────────────────────────────────────────────────────
_BI_CDN = "https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/font/bootstrap-icons.min.css"

# Inject via iframe bridge so <link> bypasses Streamlit's HTML sanitizer
_BI_INJECT = f"""
<link rel="stylesheet" href="{_BI_CDN}">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<script>
(function(){{
  // Also push to parent document (Streamlit host)
  var p = (window.parent || window).document;
  if (!p.getElementById('bi-cdn')) {{
    var l = p.createElement('link');
    l.id  = 'bi-cdn';
    l.rel = 'stylesheet';
    l.href = '{_BI_CDN}';
    (p.head || p.body).appendChild(l);
  }}
  if (!p.querySelector('meta[name=viewport]')) {{
    var m = p.createElement('meta');
    m.name    = 'viewport';
    m.content = 'width=device-width, initial-scale=1.0';
    (p.head || p.body).appendChild(m);
  }}
}})();
</script>
"""

# ── Global CSS ────────────────────────────────────────────────────────────────
_CSS = """
<style>
/* ═══════════════════════════════════════════════
   Design tokens
═══════════════════════════════════════════════ */
:root {
  --bg:        #05070D;
  --surface:   #0B1220;
  --surface-2: #111B30;
  --border:    #1B2A4A;
  --primary:   #2F6BFF;
  --glow:      #5B8CFF;
  --text:      #E8EEFF;
  --muted:     #8A98B8;
  --success:   #2DD4A0;
  --danger:    #FF4D6A;
  --ease:      cubic-bezier(.22,1,.36,1);
  --radius:    12px;
  --navbar-h:  56px;
}

/* ═══════════════════════════════════════════════
   App shell
═══════════════════════════════════════════════ */
.stApp {
  background: var(--bg) !important;
  color: var(--text) !important;
  font-family: -apple-system, "Segoe UI", system-ui, sans-serif !important;
}
.stApp > header,
.stApp > footer,
#MainMenu { display: none !important; }

/* Content container */
.block-container {
  max-width: 1200px !important;
  padding: 16px clamp(12px, 3vw, 48px) 40px !important;
}

/* ═══════════════════════════════════════════════
   Animations
═══════════════════════════════════════════════ */
@keyframes fadeUp {
  from { opacity: 0; transform: translateY(14px); }
  to   { opacity: 1; transform: none; }
}
@keyframes pulse {
  0%,100% { box-shadow: 0 0 0 0   rgba(47,107,255,.45); }
  50%     { box-shadow: 0 0 0 18px rgba(47,107,255,0);   }
}

/* ═══════════════════════════════════════════════
   Buttons
═══════════════════════════════════════════════ */
.stButton > button {
  background:    var(--primary) !important;
  color:         #fff !important;
  border:        1px solid transparent !important;
  border-radius: var(--radius) !important;
  padding:       10px 24px !important;
  font-weight:   600 !important;
  font-size:     14px !important;
  transition:    all 180ms var(--ease) !important;
}
.stButton > button:hover {
  background:  var(--glow) !important;
  transform:   translateY(-2px) !important;
  box-shadow:  0 6px 20px rgba(47,107,255,.45) !important;
}
.stButton > button:active { transform: scale(.97) !important; }

[data-testid="baseButton-secondary"] {
  background:  transparent !important;
  border:      1px solid var(--border) !important;
  color:       var(--muted) !important;
  box-shadow:  none !important;
}
[data-testid="baseButton-secondary"]:hover {
  border-color: var(--primary) !important;
  color:        var(--primary) !important;
  background:   rgba(47,107,255,.08) !important;
}

/* ═══════════════════════════════════════════════
   Inputs
═══════════════════════════════════════════════ */
.stTextInput > div > div > input,
.stTextArea  > div > div > textarea {
  background:    var(--surface-2) !important;
  border:        1px solid var(--border) !important;
  border-radius: var(--radius) !important;
  color:         var(--text) !important;
  font-size:     14px !important;
  transition:    border-color 140ms var(--ease) !important;
}
.stTextInput > div > div > input:focus,
.stTextArea  > div > div > textarea:focus {
  border-color: var(--primary) !important;
  box-shadow:   0 0 0 3px rgba(47,107,255,.18) !important;
}
.stTextInput label,
.stTextArea  label {
  color:          var(--muted) !important;
  font-size:      11px !important;
  font-weight:    700 !important;
  letter-spacing: .05em !important;
  text-transform: uppercase !important;
}

/* ═══════════════════════════════════════════════
   Cards
═══════════════════════════════════════════════ */
.card {
  background:    var(--surface);
  border:        1px solid var(--border);
  border-radius: 16px;
  padding:       24px;
  transition:    all 180ms var(--ease);
}
.card:hover {
  border-color: var(--primary);
  transform:    translateY(-2px);
  box-shadow:   0 8px 28px rgba(47,107,255,.13);
}

/* ═══════════════════════════════════════════════
   Sidebar
═══════════════════════════════════════════════ */
[data-testid="stSidebar"] {
  background:   var(--surface) !important;
  border-right: 1px solid var(--border) !important;
}

/* ═══════════════════════════════════════════════
   Alerts
═══════════════════════════════════════════════ */
.stAlert { border-radius: var(--radius) !important; }

/* ═══════════════════════════════════════════════
   ─── NAVBAR ────────────────────────────────────
═══════════════════════════════════════════════ */
.app-navbar {
  position:       fixed;
  top: 0; left: 0; right: 0;
  z-index:        1000;
  height:         var(--navbar-h);
  background:     var(--surface);
  border-bottom:  1px solid var(--border);
  display:        flex;
  align-items:    center;
  padding:        0 clamp(12px,3vw,32px);
  gap:            12px;
  backdrop-filter: blur(16px);
}
.navbar-spacer { height: var(--navbar-h); }

/* Left zone */
.nav-left {
  display:     flex;
  align-items: center;
  gap:         8px;
  flex:        1;
  min-width:   0;
}

/* App name — clickable, goes to Beranda */
.nav-brand {
  display:         inline-flex;
  align-items:     center;
  gap:             8px;
  text-decoration: none;
  cursor:          pointer;
  padding:         4px 8px;
  border-radius:   8px;
  transition:      background 160ms var(--ease);
  white-space:     nowrap;
}
.nav-brand:hover { background: var(--surface-2); }
.nav-brand-icon {
  font-size: 20px;
  color:     var(--primary);
  flex-shrink: 0;
}
.nav-brand-text {
  font-size:      13px;
  font-weight:    700;
  letter-spacing: .06em;
  color:          var(--muted);
  text-transform: uppercase;
}

/* Back button */
.nav-back {
  display:         inline-flex;
  align-items:     center;
  gap:             4px;
  padding:         5px 10px;
  border-radius:   8px;
  background:      var(--surface-2);
  border:          1px solid var(--border);
  color:           var(--text);
  font-size:       13px;
  font-weight:     600;
  text-decoration: none;
  cursor:          pointer;
  transition:      all 160ms var(--ease);
  white-space:     nowrap;
  flex-shrink:     0;
}
.nav-back:hover {
  background:   var(--primary);
  border-color: var(--primary);
  color:        #fff;
}
.nav-back-icon { font-size: 18px; line-height: 1; }

/* Center zone — page title */
.nav-center {
  display:     flex;
  align-items: center;
  gap:         7px;
  font-size:   15px;
  font-weight: 600;
  color:       var(--text);
  white-space: nowrap;
}
.nav-page-icon { color: var(--primary); font-size: 16px; }

/* Right zone — username */
.nav-right {
  display:         flex;
  align-items:     center;
  gap:             6px;
  flex:            1;
  justify-content: flex-end;
  min-width:       0;
}
.nav-user {
  display:     inline-flex;
  align-items: center;
  gap:         5px;
  font-size:   12px;
  color:       var(--muted);
  white-space: nowrap;
  overflow:    hidden;
  text-overflow: ellipsis;
  max-width:   140px;
}

/* ═══════════════════════════════════════════════
   ─── FOOTER ────────────────────────────────────
═══════════════════════════════════════════════ */
.app-footer {
  margin-top:  48px;
  border-top:  1px solid var(--border);
  background:  var(--surface);
  padding:     28px clamp(16px,4vw,48px);
}
.footer-inner {
  max-width:       900px;
  margin:          0 auto;
  display:         flex;
  flex-direction:  column;
  align-items:     center;
  gap:             8px;
  text-align:      center;
}
.footer-brand {
  display:     inline-flex;
  align-items: center;
  gap:         8px;
  font-size:   13px;
  font-weight: 700;
  letter-spacing: .07em;
  color:       var(--text);
}
.footer-brand i { color: var(--primary); font-size: 17px; }
.footer-tagline {
  font-size:  12px;
  color:      var(--muted);
  margin:     2px 0;
}
.footer-authors {
  display:         flex;
  flex-wrap:       wrap;
  align-items:     center;
  justify-content: center;
  gap:             4px 10px;
  font-size:       12px;
  color:           var(--text);
  font-weight:     500;
}
.footer-nim {
  font-size:   11px;
  color:       var(--primary);
  font-weight: 700;
  background:  rgba(47,107,255,.13);
  padding:     1px 7px;
  border-radius: 20px;
}
.footer-sep   { color: var(--border); }
.footer-copy  { font-size: 11px; color: var(--muted); margin-top: 4px; }

/* ═══════════════════════════════════════════════
   ─── STAT CARD ──────────────────────────────────
═══════════════════════════════════════════════ */
.stat-card {
  background:    var(--surface);
  border:        1px solid var(--border);
  border-radius: 14px;
  padding:       16px 20px;
  display:       flex;
  align-items:   center;
  gap:           14px;
  transition:    all 180ms var(--ease);
  animation:     fadeUp 300ms var(--ease) both;
}
.stat-card:hover {
  border-color: var(--primary);
  transform:    translateY(-2px);
  box-shadow:   0 6px 20px rgba(47,107,255,.12);
}
.stat-icon {
  width:           46px; height: 46px;
  background:      var(--surface-2);
  border:          1px solid var(--border);
  border-radius:   11px;
  display:         flex;
  align-items:     center;
  justify-content: center;
  flex-shrink:     0;
}
.stat-label { font-size: 12px; color: var(--muted); margin-bottom: 3px; }
.stat-value { font-size: 22px; font-weight: 700; color: var(--text); line-height: 1; }

/* ═══════════════════════════════════════════════
   ─── SECTION HEADING ────────────────────────────
═══════════════════════════════════════════════ */
.section-title {
  font-size:   21px;
  font-weight: 700;
  color:       var(--text);
  margin:      8px 0 4px;
}
.section-sub {
  font-size:     13px;
  color:         var(--muted);
  margin-bottom: 18px;
}

/* ═══════════════════════════════════════════════
   ─── FAB QUICK MENU ─────────────────────────────
═══════════════════════════════════════════════ */
.fab-container {
  position:        fixed;
  bottom:          24px; right: 24px;
  z-index:         999;
  display:         flex;
  flex-direction:  column-reverse;
  align-items:     flex-end;
  gap:             8px;
}
.fab-main {
  width:        50px; height: 50px;
  border-radius: 50%;
  background:   var(--primary);
  border:       none;
  color:        #fff;
  font-size:    22px;
  cursor:       pointer;
  box-shadow:   0 4px 16px rgba(47,107,255,.5);
  transition:   all 200ms var(--ease);
  display:      flex;
  align-items:  center;
  justify-content: center;
}
.fab-main:hover { transform: scale(1.08); }
.fab-items {
  display:        flex;
  flex-direction: column-reverse;
  gap:            6px;
  align-items:    flex-end;
}
.fab-item {
  background:      var(--surface);
  border:          1px solid var(--border);
  border-radius:   50px;
  padding:         8px 16px;
  color:           var(--text);
  text-decoration: none;
  font-size:       13px;
  white-space:     nowrap;
  transition:      all 180ms var(--ease);
  display:         inline-flex;
  align-items:     center;
  gap:             7px;
  animation:       fadeUp 200ms var(--ease) both;
}
.fab-item:hover {
  background:   var(--primary);
  border-color: var(--primary);
  color:        #fff;
}

/* ═══════════════════════════════════════════════
   ─── AUTH PAGE ──────────────────────────────────
═══════════════════════════════════════════════ */
.auth-root {
  display:     flex;
  min-height:  calc(100vh - 60px);
}
.auth-brand {
  flex:            1;
  background:      var(--surface);
  border-right:    1px solid var(--border);
  display:         flex;
  flex-direction:  column;
  align-items:     center;
  justify-content: center;
  padding:         48px 36px;
  text-align:      center;
}
.auth-form-side {
  flex:            1;
  display:         flex;
  flex-direction:  column;
  align-items:     center;
  justify-content: center;
  padding:         48px 36px;
}
.auth-logo {
  width:           80px; height: 80px;
  border-radius:   50%;
  background:      var(--bg);
  border:          2px solid var(--primary);
  display:         flex;
  align-items:     center;
  justify-content: center;
  font-size:       34px;
  color:           var(--primary);
  margin-bottom:   24px;
  animation:       pulse 2.4s ease-in-out infinite;
}
.auth-eyebrow {
  font-size:      10px;
  letter-spacing: .3em;
  color:          var(--muted);
  text-transform: uppercase;
  margin:         0 0 8px;
}
.auth-app-title {
  font-size:   clamp(26px, 4vw, 40px);
  font-weight: 800;
  line-height: 1.1;
  color:       var(--text);
  margin:      0 0 10px;
}
.auth-tagline {
  font-size:  14px;
  color:      var(--muted);
  line-height: 1.7;
  max-width:  300px;
  margin:     0 auto 32px;
}
.feat-list {
  display:        flex;
  flex-direction: column;
  gap:            8px;
  width:          100%;
  max-width:      300px;
  margin:         0 auto;
}
.feat-item {
  display:       flex;
  align-items:   center;
  gap:           12px;
  background:    var(--surface-2);
  border:        1px solid var(--border);
  border-radius: 10px;
  padding:       10px 14px;
}
.feat-item i { color: var(--primary); font-size: 16px; flex-shrink: 0; }
.feat-item span { font-size: 12px; color: var(--muted); line-height: 1.4; }

.auth-form-card {
  width:     100%;
  max-width: 400px;
}
.form-heading {
  font-size:   22px;
  font-weight: 700;
  color:       var(--text);
  margin:      0 0 4px;
  display:     flex;
  align-items: center;
  gap:         8px;
}
.form-heading i { color: var(--primary); }
.form-sub {
  font-size:     13px;
  color:         var(--muted);
  margin-bottom: 24px;
}

/* Tab switcher */
.auth-tab-bar {
  display:      flex;
  border-bottom: 2px solid var(--border);
  margin-bottom: 20px;
}

.tips-box {
  background:    var(--surface-2);
  border:        1px solid var(--border);
  border-radius: 10px;
  padding:       13px 16px;
  margin-top:    14px;
}
.tips-box p {
  font-size:      11px;
  font-weight:    700;
  color:          var(--muted);
  letter-spacing: .05em;
  text-transform: uppercase;
  margin:         0 0 7px;
}
.tips-box ul {
  font-size:  12px;
  color:      var(--muted);
  margin:     0;
  padding-left: 16px;
  line-height: 1.9;
}

/* ═══════════════════════════════════════════════
   ─── DEV BANNER ─────────────────────────────────
═══════════════════════════════════════════════ */
.dev-banner {
  background:   var(--danger);
  color:        #fff;
  text-align:   center;
  padding:      6px 20px;
  font-weight:  700;
  font-size:    12px;
  letter-spacing: .06em;
  position:     fixed;
  top:          0; left: 0; right: 0;
  z-index:      99999;
}
.dev-spacer { height: 30px; }

/* ═══════════════════════════════════════════════
   ─── RESPONSIVE WEB DESIGN ──────────────────────
═══════════════════════════════════════════════ */

/* Tablet ≤ 1024 */
@media (max-width: 1024px) {
  .block-container { max-width: 100% !important; }
  .nav-brand-text   { display: none; }
  .section-title    { font-size: 19px; }
}

/* Mobile ≤ 768 */
@media (max-width: 768px) {
  :root { --navbar-h: 50px; }
  .block-container { padding: 8px 12px 32px !important; }
  .app-navbar      { padding: 0 12px; }
  .nav-center      { font-size: 13px; }
  .nav-page-title  { display: none; }
  .nav-back        { padding: 5px 8px; }
  .nav-back span   { display: none; }  /* hide text, keep icon */
  .stat-card       { padding: 12px 14px; }
  .stat-value      { font-size: 19px; }
  .fab-container   { bottom: 16px; right: 16px; }
  .app-footer      { padding: 20px 12px; }
  .footer-authors  { flex-direction: column; gap: 4px; }
  .footer-sep      { display: none; }
  /* Auth — stack vertically */
  .auth-brand      { display: none; }   /* hide brand panel on mobile */
  .auth-form-side  { padding: 24px 16px; }
}

/* Small phone ≤ 480 */
@media (max-width: 480px) {
  .nav-center      { display: none; }
  .nav-brand-icon  { font-size: 22px; }
  .section-title   { font-size: 17px; }
  .stat-icon       { width: 40px; height: 40px; }
  .stat-value      { font-size: 17px; }
  .auth-form-card  { max-width: 100%; }
}

/* ═══════════════════════════════════════════════
   Accessibility
═══════════════════════════════════════════════ */
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after { animation: none !important; transition: none !important; }
}
</style>
"""


def inject_bootstrap_icons() -> None:
    """Inject Bootstrap Icons & viewport meta via iframe bridge."""
    components.html(_BI_INJECT, height=0, scrolling=False)


def inject_global_css() -> None:
    """Inject global CSS + Bootstrap Icons."""
    inject_bootstrap_icons()
    st.markdown(_CSS, unsafe_allow_html=True)


def hide_sidebar() -> None:
    """Hide Streamlit sidebar (used on auth pages)."""
    st.markdown(
        """
        <style>
        [data-testid="stSidebar"],
        [data-testid="collapsedControl"],
        [data-testid="stSidebarNav"] { display: none !important; }
        .block-container { padding-top: 0 !important; }
        </style>
        """,
        unsafe_allow_html=True,
    )


def dev_mode_banner() -> None:
    """Red DEV MODE banner."""
    st.markdown(
        '<div class="dev-banner">'
        '&#9888;&#xFE0E; DEV MODE — autentikasi biometrik dinonaktifkan'
        '</div>'
        '<div class="dev-spacer"></div>',
        unsafe_allow_html=True,
    )


def bi(icon: str, cls: str = "") -> str:
    """Return Bootstrap Icon HTML string."""
    return f'<i class="bi bi-{icon}{" " + cls if cls else ""}"></i>'
