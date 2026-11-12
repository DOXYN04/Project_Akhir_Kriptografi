"""
pages/4_Pesan_Gambar.py — Steganografi LSB: sembunyikan & ekstrak pesan dari gambar.
Diperbarui untuk Isolasi Multi-User (T5).
"""

import streamlit as st
import io

import config
from core.auth.session import require_auth, get_current_user_id
from ui.styles import inject_global_css, dev_mode_banner
from ui.components import quick_menu, page_header, navbar, footer
from core.stego.lsb_image import embed, extract, capacity, psnr
from core.db import models as db_models

st.set_page_config(
    page_title=f"Pesan Gambar — {config.APP_NAME}",
    page_icon="🔐",
    layout="wide",
)

require_auth()
inject_global_css()
navbar("stego")

if config.DEV_MODE:
    dev_mode_banner()

user_id: int = get_current_user_id()
master_key: bytes = st.session_state["master_key"]

page_header("Pesan Gambar", "Sembunyikan pesan rahasia dalam gambar menggunakan LSB Steganografi", icon_bi="image-fill")

tab_hide, tab_extract, tab_list = st.tabs(["Sembunyikan", "Ekstrak", "Daftar Gambar"])

# ═══════════════════════════════════════════════════════════════════════════════
# Tab Sembunyikan
# ═══════════════════════════════════════════════════════════════════════════════
with tab_hide:
    col_input, col_result = st.columns([1, config.PHI])

    with col_input:
        st.markdown("#### Input")
        image_up = st.file_uploader(
            "Upload gambar (PNG/BMP)",
            type=["png", "bmp"],
            key="hide_img",
        )
        secret_msg = st.text_area(
            "Pesan rahasia",
            height=150,
            placeholder="Ketik pesan yang akan disembunyikan…",
        )
        do_embed = st.button("Sembunyikan Pesan", use_container_width=True)

        if image_up:
            img_bytes = image_up.read()
            cap = capacity(img_bytes)
            msg_bytes = len(secret_msg.encode("utf-8")) if secret_msg else 0
            st.metric("Kapasitas Gambar", f"{cap:,} byte")
            if msg_bytes:
                st.progress(min(msg_bytes / cap, 1.0), text=f"Terpakai: {msg_bytes}/{cap} byte")

    with col_result:
        st.markdown("#### Hasil")
        if do_embed:
            if not image_up:
                st.error("Upload gambar terlebih dahulu.")
            elif not secret_msg:
                st.error("Pesan tidak boleh kosong.")
            else:
                try:
                    img_bytes_fresh = image_up.getvalue()
                    stego_bytes = embed(
                        img_bytes_fresh,
                        secret_msg.encode("utf-8"),
                        master_key,
                    )
                    psnr_val = psnr(img_bytes_fresh, stego_bytes)

                    # Simpan catatan stego ke database per user
                    stego_path = f"data/stego_{image_up.name}"
                    db_models.save_stego_item(user_id, stego_path)

                    col_orig, col_stego = st.columns(2)
                    with col_orig:
                        st.markdown("**Gambar Asli**")
                        st.image(img_bytes_fresh, use_container_width=True)
                    with col_stego:
                        st.markdown("**Gambar Stego**")
                        st.image(stego_bytes, use_container_width=True)

                    st.metric(
                        "PSNR",
                        f"{psnr_val:.2f} dB" if psnr_val != float("inf") else "∞ dB",
                        help="Nilai > 50 dB: perubahan tidak terlihat secara visual",
                    )
                    st.success("Pesan berhasil disembunyikan dan catatan disimpan!")
                    st.download_button(
                        "Unduh Gambar Stego (PNG)",
                        data=stego_bytes,
                        file_name="stego_" + (image_up.name or "image.png"),
                        mime="image/png",
                    )
                except ValueError as e:
                    st.error(f"❌ Gagal: {e}")

# ═══════════════════════════════════════════════════════════════════════════════
# Tab Ekstrak
# ═══════════════════════════════════════════════════════════════════════════════
with tab_extract:
    col_in2, col_out2 = st.columns([1, config.PHI])

    with col_in2:
        st.markdown("#### Input Gambar Stego")
        stego_up = st.file_uploader(
            "Upload gambar stego (PNG/BMP)",
            type=["png", "bmp"],
            key="extract_img",
        )
        do_extract = st.button("Ekstrak Pesan", use_container_width=True)

    with col_out2:
        st.markdown("#### Pesan Tersembunyi")
        if do_extract:
            if not stego_up:
                st.error("Upload gambar stego terlebih dahulu.")
            else:
                stego_bytes_in = stego_up.read()
                try:
                    secret_bytes = extract(stego_bytes_in, master_key)
                    secret_text = secret_bytes.decode("utf-8")
                    st.success("Pesan berhasil diekstrak!")
                    st.text_area("Pesan rahasia", value=secret_text, height=200)
                except ValueError as e:
                    st.error(f"❌ Gagal: {e}")
                except UnicodeDecodeError:
                    st.warning("Pesan terekstrak bukan teks UTF-8 (mungkin data biner).")

# ═══════════════════════════════════════════════════════════════════════════════
# Tab Daftar Gambar
# ═══════════════════════════════════════════════════════════════════════════════
with tab_list:
    stego_items = db_models.list_stego_items(user_id)
    if not stego_items:
        st.info("Belum ada riwayat gambar stego tersimpan.")
    else:
        for item in stego_items:
            with st.expander(f"Item Stego #{item['id']} — {item['created_at']}"):
                st.write(f"**Path Gambar:** `{item['image_path']}`")

quick_menu()
footer()