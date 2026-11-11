# OBSIDIAN VAULT

> **Brankas digital pribadi** — pesan rahasia, berkas, gambar, dan aset penting yang diamankan dengan kriptografi modern.

---

## Fitur

| Fitur | Algoritma | Persyaratan |
|---|---|---|
| Login Biometrik | ECDSA P-256 (WebAuthn/Passkey) | R1 |
| Keamanan Login | Argon2id + HMAC-SHA256 + HKDF | R2 |
| Super Enkripsi Teks | Vigenère → Columnar Transposition → AES-256-GCM | R3 |
| Enkripsi File | ChaCha20-Poly1305 chunked + key wrapping | R4 |
| Database Terenkripsi | AES-256-GCM per kolom sensitif | R5 |
| Steganografi Gambar | LSB PNG/BMP + AES-256-GCM | R6 |
| Blockchain Aset | SHA-256 + HMAC-SHA256 + PoW | R7 |
| UI Hitam-Biru | Golden Ratio + CSS animasi | R8 |

---

## Instalasi

### Prasyarat
- Python 3.11+
- pip

### Langkah

```bash
# 1. Klon repositori
git clone <url-repo>
cd obsidian-vault

# 2. Buat virtual environment (disarankan)
python -m venv venv
venv\Scripts\activate        # Windows
# atau: source venv/bin/activate  (Linux/Mac)

# 3. Install dependensi
pip install -r requirements.txt

# 4. Konfigurasi environment
copy .env.example .env
# Edit .env sesuai kebutuhan (lihat bagian Konfigurasi di bawah)

# 5. Jalankan aplikasi
streamlit run app.py
```

---

## Konfigurasi `.env`

```env
DEV_MODE=false          # true = mode pengembangan (login passphrase tanpa biometrik)
RP_ID=localhost          # Relying Party ID WebAuthn (ganti dengan domain Anda)
RP_NAME=Obsidian Vault
ORIGIN=http://localhost:8501   # URL asal (harus cocok dengan browser)
SESSION_SECRET=<hex 64 karakter acak>
```

### Generate SESSION_SECRET

```python
import os, secrets
print(secrets.token_hex(32))   # 64 karakter hex
```

---

## Mode DEV (Pengembangan Lokal)

Set `DEV_MODE=true` di `.env` untuk mengaktifkan login passphrase tanpa WebAuthn.
Aplikasi akan menampilkan **banner merah** sebagai peringatan. **Jangan gunakan di produksi.**

---

## Demo WebAuthn di HP (Mode Produksi)

WebAuthn **memerlukan HTTPS**. Untuk demo di HP lokal, gunakan tunnel HTTPS:

### Menggunakan cloudflared

```bash
# Install cloudflared (https://developers.cloudflare.com/cloudflare-one/connections/connect-apps/install-and-setup/)
cloudflared tunnel --url http://localhost:8501
```

Catat URL tunnel (contoh: `https://abc123.trycloudflare.com`), lalu perbarui `.env`:

```env
RP_ID=abc123.trycloudflare.com
ORIGIN=https://abc123.trycloudflare.com
```

### Skenario Demo Lengkap

1. **Registrasi Passkey**: buka aplikasi di browser HP → klik "Daftarkan Biometrik" → ikuti prompt sidik jari/Face ID
2. **Login Biometrik**: buka ulang → klik "Buka dengan Biometrik" → verifikasi sidik jari
3. **Enkripsi Teks**: buka halaman Pesan Teks → tulis pesan → klik "Preview Tahapan" (lihat Vigenère → Transposisi → AES) → simpan
4. **Enkripsi File**: upload file → enkripsi → unduh `.vault` → coba dekripsi
5. **Lihat DB mentah**: buka `data/vault.db` dengan DB Browser for SQLite → kolom `body_enc` tidak terbaca
6. **Steganografi**: upload PNG → sembunyikan pesan → unduh stego-image → ekstrak kembali
7. **Blockchain**: daftarkan aset → mining → verifikasi aset asli vs modifikasi
8. **Demo Tamper**: di tab Validasi → rusak blok → validasi chain → lihat blok bermasalah disorot

---

## Pengujian

```bash
pytest -q
# Hasil yang diharapkan: 42 passed
```

---

## Struktur Proyek

```
obsidian-vault/
├── app.py                    # Entry point + halaman login
├── config.py                 # Konstanta global
├── requirements.txt
├── .env.example
├── .streamlit/config.toml    # Tema hitam-biru
├── core/
│   ├── auth/                 # WebAuthn, KDF, session
│   ├── crypto/               # Klasik, modern, super enkripsi, file
│   ├── stego/                # LSB steganografi
│   ├── blockchain/           # Blok, chain, PoW
│   └── db/                   # SQLite + enkripsi kolom
├── ui/                       # Styles, layout, components
├── pages/                    # Halaman-halaman Streamlit
├── tests/                    # Unit test (42 test)
├── data/                     # vault.db + file .vault (di .gitignore)
└── docs/                     # Dokumentasi algoritma
```

---

## Keamanan

- ✅ Tidak ada kunci/rahasia di-hardcode
- ✅ Nonce/IV acak unik setiap enkripsi (`os.urandom`)
- ✅ Semua enkripsi modern menggunakan AEAD (integritas + kerahasiaan)
- ✅ `master_key` hanya hidup di session_state, dihapus saat logout/timeout
- ✅ Parameterized query (tidak ada SQL injection)
- ✅ Semua halaman wajib memanggil `require_auth()`

---

## Keterbatasan

- Streamlit tidak mengakses biometrik langsung — biometrik ditangani browser/OS via WebAuthn
- Algoritma klasik (Vigenère, Transposisi) tidak aman mandiri; keamanan nyata dari AES-GCM
- LSB steganografi rentan steganalisis; kerahasiaan dijaga karena payload sudah dienkripsi
- Blockchain ini single-node (tamper-evident, bukan terdesentralisasi)

---

## Pembagian Tugas (Saran)

| Anggota | Modul |
|---|---|
| Anggota 1 | Auth/WebAuthn + DB + keamanan session |
| Anggota 2 | Super enkripsi teks + enkripsi file + steganografi |
| Anggota 3 | Blockchain + UI/UX + animasi + dokumentasi |
