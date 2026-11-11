"""
ui/webauthn_component/__init__.py
WebAuthn widget tanpa declare_component (tidak butuh PyArrow).

Mekanisme komunikasi JS → Python:
  1. Widget iframe memanggil WebAuthn browser API
  2. Hasil dikirim ke parent via window.parent.postMessage()
  3. Listener (inject_listener) yang berjalan di parent menangkap pesan
     dan melakukan navigasi URL ke ?wa_result=...&wa_mode=...
  4. Streamlit reload → Python baca st.query_params dan verifikasi
"""

from __future__ import annotations
import base64
import json


# ── HTML untuk tombol WebAuthn (berjalan di dalam iframe) ────────────────────

def _build_widget_html(mode: str, options_json: str) -> str:
    """HTML tombol WebAuthn yang berjalan di dalam iframe st.components.v1.html."""
    opts_escaped = options_json.replace("\\", "\\\\").replace("`", "\\`")
    icon  = "📲" if mode == "register" else "🔑"
    label = ("Daftarkan Passkey / Biometrik" if mode == "register"
             else "Login dengan Passkey / Biometrik")

    return f"""<!DOCTYPE html>
<html lang="id">
<head><meta charset="UTF-8">
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{
    font-family: -apple-system, "Segoe UI", system-ui, sans-serif;
    background: transparent;
    color: #E8EEFF;
    display: flex;
    flex-direction: column;
    align-items: stretch;
    padding: 4px 2px 8px;
  }}
  button {{
    background: #2F6BFF; color: #fff; border: none;
    border-radius: 10px; padding: 12px 20px;
    font-size: 15px; font-weight: 600; cursor: pointer;
    width: 100%; transition: background 200ms, transform 150ms;
  }}
  button:hover:not(:disabled) {{ background: #5B8CFF; transform: translateY(-1px); }}
  button:active:not(:disabled) {{ transform: translateY(0); }}
  button:disabled {{ opacity: 0.45; cursor: not-allowed; }}
  #status {{
    font-size: 13px; color: #8A98B8;
    margin-top: 8px; text-align: center; min-height: 18px;
  }}
  .success {{ color: #2DD4A0 !important; }}
  .error   {{ color: #FF4D6A !important; }}
  @keyframes spin {{ to {{ transform: rotate(360deg); }} }}
  .spinner {{
    display: inline-block; width: 13px; height: 13px;
    border: 2px solid rgba(255,255,255,0.3); border-top-color: #fff;
    border-radius: 50%; animation: spin 0.7s linear infinite;
    vertical-align: middle; margin-right: 5px;
  }}
</style>
</head>
<body>
  <button id="btn">{icon} {label}</button>
  <div id="status">Klik tombol lalu ikuti prompt biometrik.</div>
<script>
  const MODE         = {json.dumps(mode)};
  const OPTIONS_JSON = `{opts_escaped}`;
  const ICON_LABEL   = {json.dumps(icon + " " + label)};

  function b64urlToBuffer(b64url) {{
    const b64 = b64url.replace(/-/g, '+').replace(/_/g, '/');
    const bin = atob(b64);
    const arr = new Uint8Array(bin.length);
    for (let i = 0; i < bin.length; i++) arr[i] = bin.charCodeAt(i);
    return arr.buffer;
  }}
  function bufferToB64url(buf) {{
    const arr = new Uint8Array(buf);
    let bin = '';
    arr.forEach(b => bin += String.fromCharCode(b));
    return btoa(bin).replace(/\\+/g, '-').replace(/\\//g, '_').replace(/=/g, '');
  }}

  const btn      = document.getElementById('btn');
  const statusEl = document.getElementById('status');

  btn.addEventListener('click', async () => {{
    btn.disabled  = true;
    btn.innerHTML = '<span class="spinner"></span> Memproses\u2026';
    statusEl.textContent = 'Menunggu respons biometrik\u2026';
    statusEl.className   = '';

    try {{
      let result;
      if (MODE === 'register') {{
        const opts = JSON.parse(OPTIONS_JSON);
        opts.challenge = b64urlToBuffer(opts.challenge);
        opts.user.id   = b64urlToBuffer(opts.user.id);
        if (opts.excludeCredentials) {{
          opts.excludeCredentials = opts.excludeCredentials.map(c => ({{
            ...c, id: b64urlToBuffer(c.id),
          }}));
        }}
        const cred = await navigator.credentials.create({{ publicKey: opts }});
        result = {{
          type: 'public-key', id: cred.id,
          rawId: bufferToB64url(cred.rawId),
          response: {{
            clientDataJSON:    bufferToB64url(cred.response.clientDataJSON),
            attestationObject: bufferToB64url(cred.response.attestationObject),
          }},
        }};
      }} else {{
        const opts = JSON.parse(OPTIONS_JSON);
        opts.challenge = b64urlToBuffer(opts.challenge);
        if (opts.allowCredentials) {{
          opts.allowCredentials = opts.allowCredentials.map(c => ({{
            ...c, id: b64urlToBuffer(c.id),
          }}));
        }}
        const cred = await navigator.credentials.get({{ publicKey: opts }});
        result = {{
          type: 'public-key', id: cred.id,
          rawId: bufferToB64url(cred.rawId),
          response: {{
            clientDataJSON:    bufferToB64url(cred.response.clientDataJSON),
            authenticatorData: bufferToB64url(cred.response.authenticatorData),
            signature:         bufferToB64url(cred.response.signature),
            userHandle: cred.response.userHandle
              ? bufferToB64url(cred.response.userHandle) : null,
          }},
        }};
      }}

      statusEl.textContent = '\u2705 Berhasil! Memverifikasi\u2026';
      statusEl.className   = 'success';

      // Kirim ke top window via postMessage (bukan ubah location langsung)
      window.top.postMessage({{
        type:    'wa_done',
        mode:    MODE,
        encoded: btoa(JSON.stringify(result)),
      }}, '*');

    }} catch (err) {{
      const msg =
        err.name === 'NotAllowedError'  ? 'Dibatalkan atau tidak diizinkan. Coba lagi.' :
        err.name === 'InvalidStateError'? 'Passkey sudah terdaftar sebelumnya.' :
        (err.message || 'Terjadi kesalahan tidak dikenal.');
      statusEl.textContent = '\u274C ' + msg;
      statusEl.className   = 'error';
      btn.disabled  = false;
      btn.innerHTML = ICON_LABEL;
    }}
  }});
</script>
</body></html>"""


# ── HTML listener yang berjalan di parent (luar iframe) ──────────────────────

_LISTENER_HTML = """<!DOCTYPE html><html><head><meta charset="UTF-8"></head>
<body style="margin:0;padding:0;background:transparent;">
<script>
(function() {
  if (window.top._wa_listener_active) return;
  window.top._wa_listener_active = true;
  window.top.addEventListener('message', function(e) {
    if (!e.data || e.data.type !== 'wa_done') return;
    var url = new URL(window.top.location.href);
    url.searchParams.set('wa_result', e.data.encoded);
    url.searchParams.set('wa_mode',   e.data.mode);
    window.top.location.href = url.toString();
  });
})();
</script>
</body></html>"""


# ── Public API ────────────────────────────────────────────────────────────────

def inject_listener() -> None:
    """
    Inject listener postMessage ke halaman parent (WAJIB dipanggil sekali
    sebelum webauthn_widget, di luar kondisi apapun agar selalu aktif).
    Menggunakan st.components.v1.html dengan height=0 agar tidak terlihat.
    """
    import streamlit.components.v1 as components
    components.html(_LISTENER_HTML, height=0, scrolling=False)


def webauthn_widget(mode: str, options_json: str, height: int = 90) -> None:
    """
    Tampilkan tombol WebAuthn yang langsung memanggil browser API.
    Tidak butuh PyArrow / declare_component.

    Pastikan inject_listener() sudah dipanggil sebelumnya di halaman yang sama.
    Hasil tersedia di st.query_params["wa_result"] setelah rerun.
    """
    import streamlit.components.v1 as components
    html = _build_widget_html(mode, options_json)
    components.html(html, height=height, scrolling=False)


def read_webauthn_result() -> dict | None:
    """
    Baca hasil WebAuthn dari query params (setelah rerun).
    Kembalikan dict credential atau None jika belum ada.
    Membersihkan query params setelah dibaca.
    """
    import streamlit as st
    raw = st.query_params.get("wa_result")
    if not raw:
        return None
    try:
        result = json.loads(base64.b64decode(raw))
        st.query_params.clear()
        return result
    except Exception:
        st.query_params.clear()
        return None


def get_pending_mode() -> str | None:
    """Kembalikan mode WebAuthn yang pending ('register'/'authenticate'/None)."""
    import streamlit as st
    return st.query_params.get("wa_mode")
