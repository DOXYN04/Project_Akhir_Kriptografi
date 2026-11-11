"""
pages/5_Aset_Blockchain.py — Blockchain aset: daftarkan, verifikasi, jelajah, validasi.
"""

import streamlit as st
import json
import hashlib
import time

import config
from core.auth.session import require_auth
from ui.styles import inject_global_css, dev_mode_banner
from ui.components import quick_menu, page_header, navbar, footer
from core.blockchain.chain import Blockchain
from core.db import models as db_models

st.set_page_config(
    page_title=f"Aset Blockchain — {config.APP_NAME}",
    page_icon="🔐",
    layout="wide",
)

require_auth()
inject_global_css()
navbar("asset")

if config.DEV_MODE:
    dev_mode_banner()

# ── Page-level styles ─────────────────────────────────────────────────────────
st.markdown("""
<style>
/* Block card */
.block-card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 14px;
  padding: 18px 22px;
  margin-bottom: 12px;
  transition: border-color 180ms var(--ease);
}
.block-card:hover { border-color: var(--primary); }
.block-num {
  font-size: 13px; font-weight: 700;
  color: var(--primary); margin-bottom: 8px;
  display: flex; align-items: center; gap: 8px;
}
.block-hash {
  font-family: monospace; font-size: 11px;
  color: var(--primary); word-break: break-all;
}
.block-prev {
  font-family: monospace; font-size: 11px;
  color: var(--muted); word-break: break-all;
}
.block-meta {
  font-size: 12px; color: var(--muted);
  margin-top: 6px;
}
/* Result badge */
.result-ok   { color: var(--success); font-size: 40px; text-align: center; }
.result-fail { color: var(--danger);  font-size: 40px; text-align: center; }
/* Problem block highlight */
.problem-block {
  background: rgba(255,77,106,.08);
  border: 1px solid var(--danger);
  border-radius: 12px;
  padding: 16px 20px;
  margin: 8px 0;
}
</style>
""", unsafe_allow_html=True)

master_key: bytes = st.session_state["master_key"]

page_header(
    "Aset Blockchain",
    "Catat & verifikasi integritas aset digital menggunakan SHA-256 + HMAC + PoW",
    icon_bi="link-45deg",
)

# ── Muat blockchain (cached in session) ───────────────────────────────────────
if "blockchain" not in st.session_state:
    with st.spinner("Memuat blockchain dari database…"):
        st.session_state["blockchain"] = Blockchain(master_key)

chain: Blockchain = st.session_state["blockchain"]

# Ringkasan cepat
st.markdown(
    f'<div style="display:flex;gap:12px;flex-wrap:wrap;margin-bottom:20px">'
    f'<div style="background:var(--surface);border:1px solid var(--border);'
    f'border-radius:10px;padding:10px 18px;font-size:13px">'
    f'<i class="bi bi-boxes" style="color:var(--primary)"></i>'
    f'  <strong>{len(chain)}</strong> Blok'
    f'</div>'
    f'<div style="background:var(--surface);border:1px solid var(--border);'
    f'border-radius:10px;padding:10px 18px;font-size:13px">'
    f'<i class="bi bi-shield-check-fill" style="color:var(--success)"></i>'
    f'  Difficulty: {config.POW_DIFFICULTY} nol awal'
    f'</div>'
    f'</div>',
    unsafe_allow_html=True,
)

tab_add, tab_verify, tab_explore, tab_validate = st.tabs([
    "Daftarkan Aset",
    "Verifikasi Aset",
    "Penjelajah Chain",
    "Validasi Integritas",
])

# ═════════════════════════════════════════════════════════════════════════════
# TAB 1 — Daftarkan Aset
# ═════════════════════════════════════════════════════════════════════════════
with tab_add:
    col_in, col_out = st.columns([1, 1], gap="medium")

    with col_in:
        st.markdown(
            '<div class="section-title" style="font-size:16px">'
            '<i class="bi bi-plus-circle-fill" style="color:var(--primary)"></i>'
            ' Input Aset'
            '</div>',
            unsafe_allow_html=True,
        )
        asset_type = st.radio(
            "Jenis aset", ["File", "Teks"], horizontal=True, key="add_type"
        )
        asset_name = st.text_input(
            "Nama aset",
            placeholder="Contoh: Laporan Keuangan 2025.pdf",
        )

        asset_content = None
        if asset_type == "File":
            asset_file = st.file_uploader(
                "Upload file aset",
                key="chain_file",
                help="Semua jenis file didukung",
            )
            if asset_file:
                asset_content = asset_file.read()
                st.caption(f"Ukuran: {len(asset_content):,} byte")
        else:
            asset_text = st.text_area(
                "Isi teks aset",
                height=120,
                placeholder="Masukkan teks yang ingin didaftarkan…",
            )
            if asset_text:
                asset_content = asset_text.encode("utf-8")

        do_add = st.button(
            "Mining & Daftarkan ke Blockchain",
            use_container_width=True,
            type="primary",
        )

    with col_out:
        st.markdown(
            '<div class="section-title" style="font-size:16px">'
            '<i class="bi bi-cpu-fill" style="color:var(--primary)"></i>'
            ' Hasil Mining'
            '</div>',
            unsafe_allow_html=True,
        )

        if do_add:
            if not asset_name.strip():
                st.error("Nama aset wajib diisi.")
            elif not asset_content:
                st.error("Konten aset wajib diisi (upload file atau isi teks).")
            else:
                with st.spinner("Menjalankan Proof of Work…"):
                    block = chain.add_asset(asset_name.strip(), asset_content)

                st.success(f"Blok #{block.index} berhasil ditambang!")
                sha_preview = block.data.get("sha256", "")
                st.markdown(
                    f'<div class="block-card">'
                    f'<div class="block-num">'
                    f'<i class="bi bi-cube-fill"></i> Blok #{block.index}'
                    f'</div>'
                    f'<div style="font-size:12px;color:var(--muted);margin-bottom:6px">'
                    f'{time.strftime("%Y-%m-%d %H:%M:%S")}'
                    f'</div>'
                    f'<div style="margin-bottom:4px">'
                    f'<strong style="font-size:12px">Hash:</strong>'
                    f'</div>'
                    f'<div class="block-hash">{block.hash}</div>'
                    f'<div style="margin:8px 0 4px">'
                    f'<strong style="font-size:12px">SHA-256 Aset:</strong>'
                    f'</div>'
                    f'<div class="block-hash" style="color:var(--success)">'
                    f'{sha_preview[:48]}…'
                    f'</div>'
                    f'<div class="block-meta">'
                    f'Nonce: {block.nonce} &nbsp;|&nbsp; '
                    f'Aset: {block.data.get("asset_name","?")}'
                    f'</div>'
                    f'</div>',
                    unsafe_allow_html=True,
                )
        else:
            st.markdown(
                '<div style="text-align:center;padding:40px 20px;'
                'color:var(--muted);font-size:13px">'
                '<i class="bi bi-cpu" style="font-size:40px;display:block;'
                'margin-bottom:12px;color:var(--border)"></i>'
                'Hasil mining akan tampil di sini'
                '</div>',
                unsafe_allow_html=True,
            )

# ═════════════════════════════════════════════════════════════════════════════
# TAB 2 — Verifikasi Aset
# ═════════════════════════════════════════════════════════════════════════════
with tab_verify:
    col_v1, col_v2 = st.columns([1, 1], gap="medium")

    with col_v1:
        st.markdown(
            '<div class="section-title" style="font-size:16px">'
            '<i class="bi bi-search" style="color:var(--primary)"></i>'
            ' Upload Aset untuk Diverifikasi'
            '</div>',
            unsafe_allow_html=True,
        )
        vtype = st.radio(
            "Jenis", ["File", "Teks"], horizontal=True, key="vtype"
        )

        vcontent = None
        if vtype == "File":
            vfile = st.file_uploader("Upload file", key="verify_file")
            if vfile:
                vcontent = vfile.read()
                st.caption(f"Ukuran: {len(vcontent):,} byte")
        else:
            vtext = st.text_area(
                "Teks aset", height=120,
                placeholder="Tempel teks yang ingin diverifikasi…",
                key="vtext",
            )
            if vtext:
                vcontent = vtext.encode("utf-8")

        do_verify = st.button(
            "Verifikasi Keaslian Aset",
            use_container_width=True,
            type="primary",
        )

    with col_v2:
        st.markdown(
            '<div class="section-title" style="font-size:16px">'
            '<i class="bi bi-patch-check-fill" style="color:var(--primary)"></i>'
            ' Hasil Verifikasi'
            '</div>',
            unsafe_allow_html=True,
        )

        if do_verify:
            if not vcontent:
                st.error("Isi aset tidak boleh kosong.")
            else:
                sha = hashlib.sha256(vcontent).hexdigest()
                found = chain.verify_asset(vcontent)

                if found:
                    st.markdown(
                        '<div class="result-ok">'
                        '<i class="bi bi-check-circle-fill"></i>'
                        '</div>',
                        unsafe_allow_html=True,
                    )
                    st.success(
                        f"Aset **asli** — tercatat di Blok #{found.index}  \n"
                        f"Nama: **{found.data.get('asset_name', '?')}**"
                    )
                    st.code(sha, language=None)
                else:
                    st.markdown(
                        '<div class="result-fail">'
                        '<i class="bi bi-x-circle-fill"></i>'
                        '</div>',
                        unsafe_allow_html=True,
                    )
                    st.error(
                        "Aset **tidak ditemukan** di blockchain.  \n"
                        "Kemungkinan belum didaftarkan atau telah dimodifikasi."
                    )
                    st.code(sha, language=None)
        else:
            st.markdown(
                '<div style="text-align:center;padding:40px 20px;'
                'color:var(--muted);font-size:13px">'
                '<i class="bi bi-patch-question" style="font-size:40px;display:block;'
                'margin-bottom:12px;color:var(--border)"></i>'
                'Hasil verifikasi akan tampil di sini'
                '</div>',
                unsafe_allow_html=True,
            )

# ═════════════════════════════════════════════════════════════════════════════
# TAB 3 — Penjelajah Chain
# ═════════════════════════════════════════════════════════════════════════════
with tab_explore:
    st.markdown(
        f'<div class="section-title" style="font-size:16px;margin-bottom:16px">'
        f'<i class="bi bi-diagram-3-fill" style="color:var(--primary)"></i>'
        f' Rantai Blok &mdash; {len(chain)} Blok Total'
        f'</div>',
        unsafe_allow_html=True,
    )

    for block in reversed(chain.chain):
        is_genesis = block.index == 0
        ts = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(block.timestamp))
        genesis_badge = (
            '<span style="background:var(--surface-2);border:1px solid var(--border);'
            'border-radius:20px;padding:2px 10px;font-size:11px;color:var(--muted);'
            'margin-left:8px">GENESIS</span>'
            if is_genesis else ""
        )
        asset_row = (
            f'<div class="block-meta" style="margin-top:6px">'
            f'<i class="bi bi-box-seam-fill" style="color:var(--primary)"></i>'
            f' Aset: <strong>{block.data.get("asset_name","?")}</strong>'
            f'</div>'
            if not is_genesis else ""
        )

        st.markdown(
            f'<div class="block-card">'

            f'<div class="block-num">'
            f'<i class="bi bi-cube-fill"></i>'
            f' Blok #{block.index}{genesis_badge}'
            f'</div>'

            f'<div class="block-meta" style="margin-bottom:8px">'
            f'<i class="bi bi-clock"></i> {ts}'
            f' &nbsp;|&nbsp; Nonce: {block.nonce}'
            f'</div>'

            f'<div style="font-size:11px;color:var(--muted);margin-bottom:2px">'
            f'Hash:</div>'
            f'<div class="block-hash">{block.hash}</div>'

            f'<div style="font-size:11px;color:var(--muted);margin:6px 0 2px">'
            f'Hash Blok Sebelumnya:</div>'
            f'<div class="block-prev">{block.prev_hash}</div>'

            f'{asset_row}'
            f'</div>',
            unsafe_allow_html=True,
        )

# ═════════════════════════════════════════════════════════════════════════════
# TAB 4 — Validasi Integritas
# ═════════════════════════════════════════════════════════════════════════════
with tab_validate:
    col_ctrl, col_res = st.columns([1, 1], gap="medium")

    with col_ctrl:
        st.markdown(
            '<div class="section-title" style="font-size:16px">'
            '<i class="bi bi-shield-fill-check" style="color:var(--primary)"></i>'
            ' Validasi Chain'
            '</div>',
            unsafe_allow_html=True,
        )
        st.markdown(
            '<p style="font-size:13px;color:var(--muted);margin-bottom:16px">'
            'Periksa apakah seluruh rantai blok masih utuh dan '
            'tidak ada yang dimanipulasi.'
            '</p>',
            unsafe_allow_html=True,
        )
        do_validate = st.button(
            "Validasi Seluruh Chain",
            use_container_width=True,
            type="primary",
        )

        st.markdown("---")
        st.markdown(
            '<div class="section-title" style="font-size:14px">'
            '<i class="bi bi-exclamation-triangle-fill" style="color:var(--danger)"></i>'
            ' Demo Tamper (Presentasi)'
            '</div>',
            unsafe_allow_html=True,
        )
        st.warning(
            "Tombol ini **merusak data blok di memory** untuk demonstrasi. "
            "Tidak mengubah database. Reload halaman untuk reset.",
            icon="⚠️",
        )
        max_idx = max(1, len(chain) - 1)
        tamper_idx = st.number_input(
            "Indeks blok yang akan dirusak",
            min_value=1, max_value=max_idx, value=min(1, max_idx),
        )
        do_tamper = st.button(
            "Simulasi Tamper pada Blok",
            use_container_width=True,
        )

    with col_res:
        st.markdown(
            '<div class="section-title" style="font-size:16px">'
            '<i class="bi bi-activity" style="color:var(--primary)"></i>'
            ' Hasil'
            '</div>',
            unsafe_allow_html=True,
        )

        if do_validate:
            valid, problems = chain.is_valid()
            if valid:
                st.markdown(
                    '<div class="result-ok">'
                    '<i class="bi bi-check-circle-fill"></i>'
                    '</div>',
                    unsafe_allow_html=True,
                )
                st.success(
                    f"Chain valid.  \n"
                    f"Semua **{len(chain)}** blok utuh dan terhubung dengan benar."
                )
            else:
                st.markdown(
                    '<div class="result-fail">'
                    '<i class="bi bi-x-circle-fill"></i>'
                    '</div>',
                    unsafe_allow_html=True,
                )
                st.error(
                    f"Chain **RUSAK** — ditemukan {len(problems)} blok bermasalah."
                )
                for idx in problems:
                    b = chain.chain[idx]
                    st.markdown(
                        f'<div class="problem-block">'
                        f'<strong style="color:var(--danger)">'
                        f'<i class="bi bi-exclamation-triangle-fill"></i>'
                        f' Blok #{idx} Bermasalah'
                        f'</strong>'
                        f'<div style="font-size:12px;color:var(--muted);margin-top:8px">'
                        f'Hash tersimpan: '
                        f'<code style="color:var(--text)">{b.hash[:40]}…</code>'
                        f'</div>'
                        f'<div style="font-size:12px;color:var(--muted)">'
                        f'Hash dihitung ulang: '
                        f'<code style="color:var(--danger)">'
                        f'{b.compute_hash()[:40]}…'
                        f'</code>'
                        f'</div>'
                        f'</div>',
                        unsafe_allow_html=True,
                    )

        if do_tamper:
            idx = int(tamper_idx)
            if idx < len(chain.chain):
                chain.chain[idx].data["sha256"] = "0" * 64
                st.warning(
                    f"Blok #{idx} telah dirusak di memory.  \n"
                    "Klik **Validasi Seluruh Chain** untuk melihat hasilnya."
                )
            else:
                st.error("Indeks blok tidak valid.")

        if not do_validate and not do_tamper:
            st.markdown(
                '<div style="text-align:center;padding:40px 20px;'
                'color:var(--muted);font-size:13px">'
                '<i class="bi bi-shield" style="font-size:40px;display:block;'
                'margin-bottom:12px;color:var(--border)"></i>'
                'Klik "Validasi Seluruh Chain" untuk memulai'
                '</div>',
                unsafe_allow_html=True,
            )

quick_menu()
footer()
