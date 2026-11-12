"""
ui/webauthn_component/__init__.py
WebAuthn widget dengan fallback input manual yang stabil dan andal.
"""

from __future__ import annotations
import json
import streamlit as st
import streamlit.components.v1 as components

def inject_listener() -> None:
    pass

def get_pending_mode() -> str | None:
    return st.session_state.get("manual_wa_mode")

def read_webauthn_result() -> dict | None:
    """Membaca hasil dari input manual yang dimasukkan pengguna."""
    raw = st.session_state.get("manual_wa_result")
    if not raw:
        return None
    try:
        if isinstance(raw, str):
            return json.loads(raw)
        return raw
    except Exception:
        return None

def webauthn_widget(mode: str, options_json: str, height: int = 140) -> None:
    """
    Widget WebAuthn yang menampilkan tombol pemindaian biometrik 
    sekaligus kotak input JSON manual sebagai jembatan bypass sandbox.
    """
    st.session_state["manual_wa_mode"] = mode

    html_code = f"""<!DOCTYPE html>
<html lang="id">
<head>
  <meta charset="UTF-8">
  <script src="https://cdn.jsdelivr.net/npm/@simplewebauthn/browser/dist/bundle/index.umd.min.js"></script>
  <style>
    body {{
      font-family: sans-serif;
      background: transparent;
      color: #E8EEFF;
      margin: 0; padding: 4px;
    }}
    button {{
      background: #2F6BFF; color: #fff; border: none;
      border-radius: 10px; padding: 12px 20px;
      font-size: 15px; font-weight: 600; cursor: pointer;
      width: 100%; transition: background 200ms;
    }}
    button:hover {{ background: #5B8CFF; }}
    #status {{ font-size: 13px; color: #8A98B8; margin-top: 6px; text-align: center; }}
    textarea {{ width: 100%; height: 50px; background: #111; color: #0f0; font-family: monospace; font-size: 10px; margin-top: 4px; border-radius: 6px; padding: 4px; }}
  </style>
</head>
<body>
  <button id="btn">{"📲 Mulai Pemindaian Biometrik" if mode == "register" else "🔑 Login dengan Passkey"}</button>
  <div id="status">Klik tombol lalu ikuti prompt sidik jari/wajah.</div>
  <textarea id="output" placeholder="JSON hasil biometrik akan muncul di sini..."></textarea>

<script>
  const {{ startRegistration, startAuthentication }} = SimpleWebAuthnBrowser;
  const MODE = "{mode}";
  const OPTIONS = {options_json};

  document.getElementById('btn').addEventListener('click', async () => {{
    const statusEl = document.getElementById('status');
    const outEl = document.getElementById('output');
    statusEl.textContent = "Memproses permintaan biometrik...";

    try {{
      let cred;
      if (MODE === 'register') {{
        cred = await startRegistration(OPTIONS);
      }} else {{
        cred = await startAuthentication(OPTIONS);
      }}

      statusEl.textContent = "✅ Berhasil! Salin teks di bawah ini:";
      statusEl.style.color = "#2DD4A0";
      
      const jsonStr = JSON.stringify(cred);
      outEl.value = jsonStr;
      outEl.select();
      navigator.clipboard.writeText(jsonStr);

    }} catch (err) {{
      statusEl.textContent = "❌ Gagal: " + (err.message || "Dibatalkan");
      statusEl.style.color = "#FF4D6A";
    }}
  }});
</script>
</body>
</html>"""
    
    components.html(html_code, height=height, scrolling=False)

    # Kotak input Streamlit pendamping agar user bisa paste JSON dengan mudah
    st.markdown("---")
    user_json_input = st.text_area(
        "Salin & Tempel (Paste) JSON Respons Biometrik di Sini:",
        placeholder='Tempel teks JSON yang muncul di kotak hitam HP Anda di sini...',
        key=f"input_json_{mode}"
    )
    if st.button("Verifikasi & Simpan Passkey", use_container_width=True, key=f"btn_verify_{mode}"):
        if user_json_input:
            st.session_state["manual_wa_result"] = user_json_input
            st.rerun()
        else:
            st.warning("Kotak input JSON masih kosong. Lakukan scan biometrik lalu salin teksnya ke sini.")