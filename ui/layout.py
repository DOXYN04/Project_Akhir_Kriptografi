"""
ui/layout.py — Helper tata letak golden ratio untuk Obsidian Vault.
"""

import streamlit as st

PHI: float = 1.618
FIB: list[int] = [8, 13, 21, 34, 55]


def golden_columns(gap: str = "large"):
    """Kembalikan dua kolom dengan proporsi 1 : φ (38.2% : 61.8%)."""
    return st.columns([1, PHI], gap=gap)


def fib(n: int) -> int:
    """Kembalikan elemen ke-n dari deret Fibonacci desain (8,13,21,34,55)."""
    return FIB[max(0, min(n, len(FIB) - 1))]


def card(content_fn, key: str = "") -> None:
    """
    Render konten dalam div bergaya .card.
    content_fn: callable yang memanggil widget Streamlit di dalamnya.
    """
    st.markdown('<div class="card">', unsafe_allow_html=True)
    content_fn()
    st.markdown("</div>", unsafe_allow_html=True)


def section_spacing(level: int = 2) -> None:
    """Tambah spasi vertikal menggunakan nilai Fibonacci."""
    px = fib(level)
    st.markdown(f'<div style="height:{px}px"></div>', unsafe_allow_html=True)
