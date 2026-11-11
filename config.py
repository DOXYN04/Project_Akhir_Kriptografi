"""
config.py — Konstanta global Obsidian Vault.
Semua rahasia runtime berasal dari .env, bukan file ini.
"""

import os
from dotenv import load_dotenv

load_dotenv()

# ── Identitas Aplikasi ────────────────────────────────────────────────────────
APP_NAME: str = "OBSIDIAN VAULT"

# ── Golden Ratio & Fibonacci ──────────────────────────────────────────────────
PHI: float = 1.618
FIB: list[int] = [8, 13, 21, 34, 55]

# ── Sesi & Autentikasi ────────────────────────────────────────────────────────
SESSION_TIMEOUT: int = 600          # idle timeout (detik)
MAX_LOGIN_ATTEMPTS: int = 5         # percobaan sebelum dikunci
LOCKOUT_SECONDS: int = 60           # durasi kunci setelah gagal berulang

# ── File & Enkripsi ───────────────────────────────────────────────────────────
MAX_FILE_MB: int = 50               # batas upload (MB)
CHUNK_SIZE: int = 64 * 1024         # 64 KiB per chunk enkripsi file

# ── Blockchain ────────────────────────────────────────────────────────────────
POW_DIFFICULTY: int = 3             # jumlah digit nol awal pada hash PoW

# ── Basis Data ────────────────────────────────────────────────────────────────
DB_PATH: str = "data/vault.db"

# ── WebAuthn / Environment ────────────────────────────────────────────────────
DEV_MODE: bool = os.getenv("DEV_MODE", "false").lower() == "true"
RP_ID: str = os.getenv("RP_ID", "localhost")
RP_NAME: str = os.getenv("RP_NAME", APP_NAME)
ORIGIN: str = os.getenv("ORIGIN", "http://localhost:8501")
SESSION_SECRET: str = os.getenv("SESSION_SECRET", "")

# ── Palet Warna (referensi Python) ────────────────────────────────────────────
COLOR = {
    "bg": "#05070D",
    "surface": "#0B1220",
    "surface2": "#111B30",
    "border": "#1B2A4A",
    "primary": "#2F6BFF",
    "glow": "#5B8CFF",
    "text": "#E8EEFF",
    "muted": "#8A98B8",
    "success": "#2DD4A0",
    "danger": "#FF4D6A",
}
