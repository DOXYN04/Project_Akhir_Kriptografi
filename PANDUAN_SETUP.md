# 📖 PANDUAN SETUP & MENJALANKAN — OBSIDIAN VAULT

> Dokumen ini berisi semua yang perlu disiapkan, langkah instalasi, cara menjalankan, serta tips demo dan troubleshooting. Berbeda dari `README.md` yang ringkas, dokumen ini ditujukan untuk **anggota kelompok** yang pertama kali menyiapkan proyek.

---

## 📋 Daftar Isi

1. [Yang Harus Disiapkan](#1-yang-harus-disiapkan)
2. [Instalasi Dependensi](#2-instalasi-dependensi)
3. [Konfigurasi File .env](#3-konfigurasi-file-env)
4. [Menjalankan Aplikasi](#4-menjalankan-aplikasi)
5. [Alur Penggunaan Pertama Kali](#5-alur-penggunaan-pertama-kali)
6. [Panduan Fitur per Halaman](#6-panduan-fitur-per-halaman)
7. [Demo untuk Presentasi](#7-demo-untuk-presentasi)
8. [Menjalankan Unit Test](#8-menjalankan-unit-test)
9. [Demo WebAuthn di HP (Biometrik)](#9-demo-webauthn-di-hp-biometrik)
10. [Troubleshooting](#10-troubleshooting)
11. [Checklist Sebelum Presentasi](#11-checklist-sebelum-presentasi)

---

## 1. Yang Harus Disiapkan

### 1.1 Perangkat Lunak (Wajib)

| Perangkat Lunak | Versi Minimum | Link Download |
|---|---|---|
| **Python** | 3.11+ | https://python.org/downloads |
| **pip** | sudah termasuk Python | — |
| **Browser modern** | Chrome 120+ / Edge 120+ / Firefox 120+ | — |

> ⚠️ Saat install Python di Windows, centang **"Add Python to PATH"** agar `python` dan `pip` bisa dijalankan dari terminal mana pun.

### 1.2 Perangkat Keras (Opsional — untuk Demo Biometrik)

| Perangkat | Keterangan |
|---|---|
| Smartphone Android/iOS | Demo sidik jari / Face ID via WebAuthn |
| YubiKey / dongle FIDO2 | Demo kunci keamanan hardware |
| Koneksi internet | Untuk tunnel HTTPS (ngrok/cloudflared) jika demo di HP |

### 1.3 Layanan Opsional (untuk Demo Biometrik di HP)

Pilih salah satu:
- **Cloudflare Tunnel** (`cloudflared`) — gratis, tanpa akun: https://developers.cloudflare.com/cloudflare-one/connections/connect-apps/install-and-setup/installation/
- **ngrok** — gratis dengan akun: https://ngrok.com

### 1.4 Struktur Folder yang Harus Ada

Setelah download/clone project, pastikan folder terlihat seperti ini:

```
Project_Akhir_Kriptografi/
├── app.py
├── config.py
├── requirements.txt
├── .env.example        ← template konfigurasi (WAJIB ada)
├── PANDUAN_SETUP.md    ← file ini
├── README.md
├── .streamlit/
│   └── config.toml
├── core/
│   ├── auth/
│   ├── crypto/
│   ├── stego/
│   ├── blockchain/
│   └── db/
├── pages/
│   ├── 1_Beranda.py
│   ├── 2_Pesan_Teks.py
│   ├── 3_Pesan_File.py
│   ├── 4_Pesan_Gambar.py
│   ├── 5_Aset_Blockchain.py
│   └── 6_Pengaturan.py
├── ui/
├── tests/
└── docs/
    └── ALGORITMA.md
```

---

## 2. Instalasi Dependensi

### Langkah 2.1 — Buka Terminal di Folder Project

**Windows — PowerShell:**
```powershell
cd "C:\dokumen diandra\kuliah\semester5\kriptografi\Project_Akhir_Kriptografi"
```

**Atau:** klik kanan di folder di File Explorer → *"Open in Terminal"* / *"Open PowerShell window here"*

### Langkah 2.2 — (Disarankan) Buat Virtual Environment

Virtual environment mencegah konflik antara paket proyek ini dengan paket Python lain di komputer.

```bash
# Buat virtual environment bernama "venv"
python -m venv venv

# Aktifkan di Windows (PowerShell)
.\venv\Scripts\Activate.ps1

# Aktifkan di Windows (CMD)
venv\Scripts\activate.bat

# Aktifkan di Linux/Mac
source venv/bin/activate
```

Setelah aktif, terminal menampilkan `(venv)` di awal:
```
(venv) PS C:\...\Project_Akhir_Kriptografi>
```

> Untuk menonaktifkan virtual environment: ketik `deactivate`

### Langkah 2.3 — Install Semua Paket

```bash
pip install -r requirements.txt
```

Paket yang akan terinstall:
- `streamlit` ≥ 1.40 — framework UI
- `cryptography` ≥ 43 — AES-GCM, ChaCha20, HKDF
- `argon2-cffi` ≥ 23 — KDF Argon2id
- `webauthn` ≥ 2.2 — verifikasi WebAuthn/FIDO2
- `Pillow` ≥ 10 — manipulasi gambar
- `numpy` ≥ 1.26 — operasi piksel vektor (steganografi)
- `python-dotenv` ≥ 1.0 — membaca file `.env`
- `pytest` ≥ 8 — menjalankan unit test

**Estimasi waktu:** 2–5 menit (tergantung kecepatan internet)

### Langkah 2.4 — Verifikasi Instalasi

```bash
python -c "import streamlit, cryptography, argon2, webauthn, PIL, numpy; print('✅ Semua paket OK')"
```

Jika muncul `✅ Semua paket OK` → lanjut ke langkah berikutnya.

---

## 3. Konfigurasi File `.env`

### Langkah 3.1 — Salin Template

```bash
# Windows (PowerShell / CMD)
copy .env.example .env

# Linux / Mac
cp .env.example .env
```

### Langkah 3.2 — Edit File `.env`

Buka file `.env` dengan teks editor (Notepad, VS Code, dll.) dan isi:

```env
# ── MODE APLIKASI ─────────────────────────────────────────────────────────────
# true  = DEV MODE: login passphrase tanpa biometrik (untuk pengembangan & ujicoba)
# false = Produksi: login WebAuthn biometrik (demo presentasi resmi)
DEV_MODE=true

# ── WEBAUTHN (hanya relevan jika DEV_MODE=false) ──────────────────────────────
# Sesuaikan dengan domain tunnel HTTPS Anda
RP_ID=localhost
RP_NAME=Obsidian Vault
ORIGIN=http://localhost:8501

# ── KEAMANAN SESI ─────────────────────────────────────────────────────────────
# Ganti dengan string hex 64 karakter acak (WAJIB diganti sebelum demo)
SESSION_SECRET=isi_dengan_hasil_perintah_di_bawah
```

### Langkah 3.3 — Generate SESSION_SECRET

Jalankan perintah ini untuk menghasilkan secret yang aman:

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

Contoh output: `a3f8c1d2e4b5069781234abcdef567890fedcba9876543210abcdef1234567890`

Salin seluruh output tersebut ke nilai `SESSION_SECRET` di `.env`.

> ⚠️ **PENTING:** File `.env` sudah masuk `.gitignore` — tidak akan ter-commit ke Git. Jangan pernah share file ini atau taruh di tempat publik.

---

## 4. Menjalankan Aplikasi

### 4.1 Mode DEV (Paling Mudah — Tanpa Biometrik)

Pastikan `.env` berisi `DEV_MODE=true`, lalu:

```bash
streamlit run app.py
```

Browser akan **otomatis terbuka** di `http://localhost:8501`.

Tanda DEV MODE aktif: **banner merah** di bagian atas halaman.

### 4.2 Mode Produksi (WebAuthn / Biometrik)

Pastikan `.env` berisi `DEV_MODE=false` dan tunnel HTTPS sudah aktif (lihat [Bagian 9](#9-demo-webauthn-di-hp-biometrik)), lalu:

```bash
streamlit run app.py
```

### 4.3 Opsi Tambahan

```bash
# Gunakan port berbeda (jika 8501 sudah dipakai)
streamlit run app.py --server.port 8502

# Jalankan tanpa buka browser otomatis
streamlit run app.py --server.headless true

# Izinkan akses dari jaringan lokal (HP di WiFi yang sama)
streamlit run app.py --server.address 0.0.0.0
```

### 4.4 Menghentikan Aplikasi

Tekan `Ctrl + C` di terminal.

---

## 5. Alur Penggunaan Pertama Kali

### 5.1 Dengan DEV_MODE=true (Login Passphrase)

```
1. Buka http://localhost:8501 di browser
2. Klik tab "Daftar Akun Baru"
3. Isi:
   - Nama Pengguna: terserah (contoh: "diandra")
   - Passphrase: buat yang kuat (contoh: "RahasiaBrankas2025!")
   - Konfirmasi Passphrase: ketik ulang yang sama
4. Klik tombol "Buat Akun"
   → Muncul pesan hijau "Akun berhasil dibuat"
5. Pindah ke tab "Login"
6. Masukkan Passphrase yang sama tadi
7. Klik "Masuk"
   → Langsung masuk ke halaman Beranda
```

> ⚠️ Akun hanya bisa dibuat **sekali**. Jika ingin reset, hapus file `data/vault.db` (atau lewat halaman Pengaturan → Hapus Semua Data).

### 5.2 Dengan DEV_MODE=false (WebAuthn)

```
1. Pastikan tunnel HTTPS aktif dan URL sudah diset di .env
2. Restart aplikasi: Ctrl+C → streamlit run app.py
3. Buka URL tunnel di browser HP

── Registrasi (pertama kali) ──────────────────────────────────────
4. Buka tab "Daftar", isi nama pengguna dan passphrase → klik "Buat Akun"
5. Tombol "📲 Daftarkan Passkey / Biometrik" muncul otomatis
6. Klik tombol → browser langsung meminta sidik jari / Face ID
7. Ikuti prompt biometrik di HP
   → Muncul pesan "✅ Passkey berhasil didaftarkan!"

── Login (selanjutnya) ─────────────────────────────────────────────
8. Buka tab "Masuk"
9. Klik "🔑 Login dengan Passkey / Biometrik"
10. Ikuti prompt biometrik → langsung masuk ke Beranda
```

> ℹ️ Tidak ada lagi langkah copy-paste JSON. Tombol langsung memanggil
> WebAuthn API di browser secara otomatis.

---

## 6. Panduan Fitur per Halaman

### 🏠 Beranda

- Statistik jumlah pesan, file, gambar stego, dan blok blockchain
- Kartu pintasan ke semua halaman
- Status sesi: sisa waktu sebelum otomatis logout
- **Quick Menu FAB** → tombol `＋` di pojok kanan bawah:
  - 🔒 Kunci (logout)
  - ✉ Pesan Baru
  - 📁 Enkripsi File
  - 🖼 Stego
  - ⛓ Aset

---

### ✉️ Pesan Teks

**Tab Enkripsi:**
1. Isi **Judul** dan **Teks Pesan**
2. Klik **"👁 Preview Tahapan"** → visualisasi 3 tahap:
   - Setelah Vigenère (Base64 dari byte terenkripsi)
   - Setelah Transposisi (urutan byte diacak)
   - Final AES-GCM (ciphertext akhir)
3. Klik **"🔒 Enkripsi & Simpan"** → tersimpan di database

**Tab Dekripsi:**
1. Tempel token Base64 dari enkripsi
2. Klik **"🔓 Dekripsi"** → plaintext muncul

**Tab Daftar Pesan:**
- Semua pesan ditampilkan dalam expander, didekripsi otomatis
- Tombol 🗑 Hapus per pesan

---

### 📁 Enkripsi File

**Tab Enkripsi File:**
1. Klik "Browse files" → pilih file (maks 50 MB, semua format)
2. Klik **"🔒 Enkripsi File"**
3. Lihat SHA-256 file asli
4. Klik **"⬇️ Unduh .vault"** → simpan file `.vault`

**Tab Dekripsi File:**
1. Upload file `.vault`
2. Klik **"🔓 Dekripsi File"**
3. Nama file asli dipulihkan otomatis
4. Klik **"⬇️ Unduh [nama_file]"**

> Algoritma yang digunakan (**ChaCha20-Poly1305**) **berbeda** dari enkripsi teks (AES-256-GCM) — memenuhi syarat R4.

---

### 🖼️ Pesan Gambar — Steganografi

**Tab Sembunyikan:**
1. Upload gambar **PNG atau BMP** (JPEG akan ditolak otomatis)
2. Lihat **indikator kapasitas** — pastikan pesan muat
3. Ketik pesan rahasia
4. Klik **"🙈 Sembunyikan Pesan"**
5. Lihat:
   - Gambar asli vs stego berdampingan
   - Nilai **PSNR** (harusnya > 50 dB → tidak terlihat berbeda)
6. Klik **"⬇️ Unduh Gambar Stego (PNG)"**

**Tab Ekstrak:**
1. Upload gambar stego (yang sudah disisipi pesan)
2. Klik **"🔍 Ekstrak Pesan"**
3. Pesan rahasia muncul (hanya bisa diekstrak dengan kunci master yang sama)

---

### ⛓️ Aset Blockchain

**Tab Daftarkan Aset:**
1. Pilih jenis: **File** atau **Teks**
2. Beri nama aset
3. Upload file / ketik teks
4. Klik **"⛏️ Mining & Daftarkan"** → tunggu animasi mining
5. Blok baru tampil dengan hash, prev_hash, nonce

**Tab Verifikasi Aset:**
1. Upload ulang file / ketik teks yang sama
2. Klik **"✅ Verifikasi"**
   - ✅ Asli → hash cocok di blok tertentu
   - ❌ Tidak ditemukan → file pernah dimodifikasi atau belum pernah didaftarkan

**Tab Penjelajah Chain:**
- Semua blok ditampilkan dari terbaru ke genesis

**Tab Validasi & Demo Tamper:**
1. Klik **"🔍 Validasi Seluruh Chain"** → semua blok valid
2. Masukkan nomor blok → **"💥 Rusak Blok"** (di memory, bukan DB)
3. Klik Validasi lagi → blok bermasalah disorot merah dengan detail

---

### ⚙️ Pengaturan

- **Timeout Sesi**: geser slider 1–60 menit → simpan
- **PoW Difficulty**: geser 2–4 → simpan (blockchain di-reset agar pakai difficulty baru)
- **Ekspor & Hapus Data**: centang konfirmasi → hapus semua data vault
- **Kunci & Logout**: hapus sesi dan kembali ke halaman login

---

## 7. Demo untuk Presentasi

Urutan yang disarankan (≈ 15–20 menit):

```
① Login (2 menit)
   DEV_MODE: daftar → login passphrase
   PRODUKSI: buka di HP → daftar passkey → login sidik jari

② Pesan Teks — Super Enkripsi (3 menit)
   → Ketik pesan → klik "Preview Tahapan"
   → Jelaskan tiap tahap: Vigenère → Transposisi → AES-GCM
   → Simpan → buka Daftar Pesan → dekripsi → plaintext muncul

③ Enkripsi File (2 menit)
   → Upload file PDF/gambar → enkripsi → unduh .vault
   → Upload .vault → dekripsi → nama file asli kembali
   → Tunjukkan: file .vault tidak bisa dibuka dengan aplikasi lain

④ Database Terenkripsi (1 menit)
   → Buka data/vault.db dengan DB Browser for SQLite
   → Tampilkan tabel messages → kolom body_enc: hanya data biner
   → "Data ini tidak bisa dibaca tanpa master key"

⑤ Steganografi (3 menit)
   → Upload gambar PNG → sembunyikan pesan → unduh stego
   → Tunjukkan PSNR > 50 dB (perubahan tidak terlihat)
   → Upload stego → ekstrak → pesan sama persis
   → Coba ekstrak dengan kunci salah → error

⑥ Blockchain (4 menit)
   → Daftarkan file asli → mining → blok baru
   → Verifikasi file asli → ✅ ditemukan di blok #n
   → Buka file di editor → ubah 1 karakter → simpan
   → Verifikasi file modifikasi → ❌ tidak ditemukan
   → Demo tamper: rusak blok #1 → validasi → merah

⑦ Logout & Keamanan Sesi (1 menit)
   → Tunjukkan timeout sesi
   → Klik "Kunci & Logout" → kembali ke halaman login
```

---

## 8. Menjalankan Unit Test

```bash
# Jalankan semua test (42 test)
pytest -v

# Ringkas tanpa output detail
pytest -q

# Test per modul
pytest tests/test_classical.py -v        # Vigenère + Transposisi
pytest tests/test_text_super.py -v       # Super enkripsi teks
pytest tests/test_file_crypto.py -v      # Enkripsi file
pytest tests/test_stego.py -v            # Steganografi LSB
pytest tests/test_blockchain.py -v       # Blockchain
pytest tests/test_db_encryption.py -v    # Enkripsi database

# Lihat output verbose + durasi tiap test
pytest -v --tb=short --durations=10
```

**Output yang diharapkan:**
```
42 passed in x.xx s
```

---

## 9. Demo WebAuthn di HP (Biometrik)

> Diperlukan hanya jika ingin demo biometrik sungguhan (`DEV_MODE=false`).

### Opsi A — Cloudflared (Gratis, Tanpa Akun)

```bash
# Download dari: https://developers.cloudflare.com/.../installation/
# Jalankan tunnel (Streamlit harus sudah berjalan di port 8501)
cloudflared tunnel --url http://localhost:8501
```

Output contoh:
```
https://random-words-here.trycloudflare.com
```

### Opsi B — ngrok

```bash
# Setelah daftar akun di ngrok.com dan install ngrok:
ngrok http 8501
```

### Langkah Setelah Mendapat URL Tunnel

1. Salin URL tunnel (contoh: `https://abc123.trycloudflare.com`)
2. Edit `.env`:
   ```env
   DEV_MODE=false
   RP_ID=abc123.trycloudflare.com
   ORIGIN=https://abc123.trycloudflare.com
   ```
3. **Restart** Streamlit: `Ctrl+C` lalu `streamlit run app.py`
4. Buka URL tunnel di **browser HP**
5. Daftarkan passkey → ikuti prompt sidik jari / Face ID

> ⚠️ URL tunnel berubah setiap sesi baru → perbarui `.env` setiap kali.

---

## 10. Troubleshooting

### ❌ `ModuleNotFoundError: No module named 'streamlit'`

Virtual environment tidak aktif atau instalasi belum selesai.
```bash
# Aktifkan venv dulu
.\venv\Scripts\Activate.ps1   # Windows
source venv/bin/activate       # Linux/Mac

# Lalu install ulang
pip install -r requirements.txt
```

---

### ❌ `streamlit: command not found` / `'streamlit' is not recognized`

```bash
python -m streamlit run app.py
```

---

### ❌ Halaman login tidak muncul, hanya error import

Pastikan menjalankan dari folder yang benar:
```bash
cd "C:\...\Project_Akhir_Kriptografi"
streamlit run app.py
```

---

### ❌ File `.env` tidak terbaca / DEV_MODE selalu false

File `.env` belum dibuat dari template:
```bash
copy .env.example .env      # Windows
cp .env.example .env        # Linux/Mac
```
Lalu edit dan set `DEV_MODE=true`.

---

### ❌ `Database is locked` (error SQLite)

Ada program lain (seperti DB Browser for SQLite) yang membuka `data/vault.db`.
- Tutup DB Browser for SQLite
- Restart Streamlit

---

### ❌ Upload gambar ditolak dengan pesan "JPEG tidak didukung"

Ini **bukan bug** — steganografi LSB memang tidak bisa digunakan pada JPEG (format lossy).
- Gunakan gambar **PNG** atau **BMP**
- Konversi: buka gambar di Paint → Simpan Sebagai → pilih format PNG

---

### ❌ WebAuthn error: `NotAllowedError` / `InvalidStateError`

- Pastikan mengakses via HTTPS (bukan HTTP) kecuali di localhost
- Pastikan `RP_ID` dan `ORIGIN` di `.env` sesuai dengan domain yang diakses di browser
- Coba di browser yang berbeda (Chrome / Edge direkomendasikan)

---

### ❌ Port 8501 sudah dipakai

```bash
streamlit run app.py --server.port 8502
```

---

### ❌ Akun sudah terdaftar, ingin reset

**Cara 1** — Lewat aplikasi (jika bisa login):
- Buka halaman **Pengaturan** → **Hapus Semua Data**

**Cara 2** — Manual:
```bash
# Hapus database (semua data hilang)
del data\vault.db    # Windows
rm data/vault.db     # Linux/Mac
```
Aplikasi akan membuat database baru saat dijalankan ulang.

---

## 11. Checklist Sebelum Presentasi

### ✅ Persiapan Teknis

- [ ] `pytest -q` → **42 passed**, tidak ada merah
- [ ] `streamlit run app.py` berjalan tanpa error di terminal
- [ ] Bisa login dan masuk ke Beranda
- [ ] Data demo sebelumnya sudah dihapus (Pengaturan → Hapus Semua Data)
- [ ] File `data/vault.db` ada (dibuat otomatis setelah pertama login)

### ✅ Fitur yang Harus Dicoba Sebelum Demo

- [ ] Enkripsi teks → Preview Tahapan → 3 tahap tampil dengan benar
- [ ] Enkripsi file → unduh `.vault` → dekripsi → file identik (bandingkan SHA-256)
- [ ] Gambar PNG → sembunyikan pesan → PSNR > 50 dB → ekstrak → pesan sama
- [ ] Daftarkan aset → verifikasi file asli ✅ → modifikasi 1 byte → verifikasi ❌
- [ ] Demo tamper blockchain → validasi → blok bermasalah muncul merah
- [ ] Buka `data/vault.db` di DB Browser → kolom `body_enc` tidak readable

### ✅ Jika Demo Biometrik (WebAuthn)

- [ ] Tunnel HTTPS aktif sebelum presentasi dimulai
- [ ] `.env` sudah diupdate dengan URL tunnel terbaru
- [ ] Aplikasi sudah di-restart setelah `.env` diubah
- [ ] Uji di browser HP — bisa buka URL tunnel
- [ ] Registrasi passkey berhasil dari HP (coba sehari sebelumnya!)
- [ ] Login biometrik berhasil (sidik jari / Face ID)
- [ ] Siapkan dongle FIDO2 jika ingin demo itu juga

### ✅ Dokumen

- [ ] `README.md` lengkap
- [ ] `docs/ALGORITMA.md` lengkap dengan diagram dan tabel pemetaan R1–R8
- [ ] Laporan mencantumkan **keterbatasan** yang jujur (Bagian 14 di AGENTS.md)

---

## 📁 Lokasi File Penting

| File / Folder | Keterangan |
|---|---|
| `app.py` | Entry point aplikasi |
| `config.py` | Semua konstanta konfigurasi |
| `.env` | Rahasia runtime (buat dari `.env.example`) |
| `data/vault.db` | Database SQLite (dibuat otomatis) |
| `requirements.txt` | Daftar paket Python |
| `tests/` | 42 unit test |
| `docs/ALGORITMA.md` | Dokumentasi algoritma lengkap |
| `README.md` | Panduan singkat (untuk repo/laporan) |
| `PANDUAN_SETUP.md` | File ini — panduan lengkap setup & demo |

---

*Dibuat sebagai panduan lengkap untuk anggota kelompok — Tugas Akhir Kriptografi*
