# Dokumentasi Algoritma — OBSIDIAN VAULT

Dokumen ini menjelaskan algoritma kriptografi yang digunakan di tiap modul, alasan pemilihan, dan diagram alur.

---

## 1. Login Biometrik (WebAuthn / FIDO2)

### Algoritma

| Fungsi | Algoritma |
|---|---|
| Verifikasi identitas | ECDSA P-256 (ES256) |
| Cadangan PIN | Argon2id (argon2-cffi), salt 16B acak |
| Turunan kunci master | HKDF-SHA256 |
| Token sesi | HMAC-SHA256 |
| Challenge | `os.urandom(32)`, TTL 120 detik |

### Alur

```
[Browser HP/Dongle]                    [Server Python]
      │                                       │
      │── navigator.credentials.create() ───▶│
      │                                       │ generate_registration_options()
      │◀── options (challenge, rpId, …) ──────│ challenge disimpan sementara
      │                                       │
      │── respons (credential, sig) ─────────▶│
      │                                       │ verify_registration() → simpan
      │                                       │ public_key + credential_id ke DB
      │                                       │
      │    ─── LOGIN ───                       │
      │── navigator.credentials.get() ───────▶│
      │◀── challenge baru ─────────────────── │
      │── tanda tangan ECDSA ────────────────▶│
      │                                       │ verify_authentication()
      │                                       │ → HKDF → master_key
      │                                       │ → HMAC → session token
```

### Alasan Pemilihan
- **WebAuthn**: standar W3C; biometrik tidak pernah meninggalkan perangkat
- **Argon2id**: KDF terkuat saat ini (memory-hard, tahan GPU/ASIC attack)
- **HKDF**: domain separation yang bersih untuk menurunkan sub-kunci
- **HMAC-SHA256**: sederhana, cepat, cukup untuk token sesi stateless

---

## 2. Super Enkripsi Teks (R3)

### Pipeline

```
Plaintext (UTF-8)
    │
    ▼ [1] Vigenère byte-mode (mod 256)
    │     C[i] = (P[i] + K[i mod n]) mod 256
    │     Kunci: HKDF(master_key, "text-vigenere", 16B)
    │
    ▼ [2] Columnar Transposition
    │     Tulis per baris → baca per kolom sesuai permutasi kunci
    │     Kunci: HKDF(master_key, "text-transpose", 16B)
    │
    ▼ [3] AES-256-GCM
    │     nonce 12B acak; AAD = version || orig_len
    │     Kunci: HKDF(master_key, "text-aes", 32B)
    │
    ▼ Base64 URL-safe
```

### Format Paket Biner

```
version(1B) | nonce(12B) | orig_len(4B) | ciphertext+tag(var)
└─────────── AAD ───────────┘
```

### Alasan Pemilihan
- Vigenère + Transposisi: edukatif, demonstrasi algoritma klasik
- AES-256-GCM: lapisan keamanan nyata; AEAD memverifikasi integritas
- Klasik di bawah modern: modifikasi pada ciphertext AES akan langsung terdeteksi oleh GCM tag

---

## 3. Enkripsi File (R4)

### Algoritma: ChaCha20-Poly1305 (chunked, envelope encryption)

```
File asli
    │
    ├─ file_key = os.urandom(32)
    ├─ nonce_prefix = os.urandom(4)
    │
    ▼ Enkripsi per chunk 64 KiB
      nonce = nonce_prefix(4B) + counter(8B)
      AAD = "chunk:" + counter + ":last" (chunk terakhir)
      → ct+tag per chunk
    │
    ├─ wrapped_key = AES-256-GCM(master_key, file_key)   ← key wrapping
    ├─ orig_filename_enc = AES-256-GCM(name_key, filename)
    │
    ▼ Format .vault:
      "OVLT" | version | nonce_prefix | wrapped_key(60B) |
      fn_len(2B) | fn_enc | chunk_len(4B) | chunk_data | …
```

### Alasan Pemilihan
- ChaCha20 berbeda dari teks (AES-GCM) → memenuhi R4
- Chunked: mendukung file besar tanpa memuat semua ke RAM
- Counter pada nonce: mencegah nonce reuse antar chunk
- AAD `is_last`: mencegah serangan pemotongan file

---

## 4. Basis Data Terenkripsi (R5)

### Skema Enkripsi Kolom

```
encrypt_field(plaintext, master_key, table, column, row_id):
    key = HKDF(master_key, "db-field", 32B)
    AAD = f"{table}:{column}:{row_id}".encode()
    nonce = os.urandom(12)
    ct = AES-256-GCM(key, plaintext, AAD)
    return nonce(12B) + ct+tag
```

AAD unik per baris mencegah copy-paste ciphertext antar baris.

### Kolom yang Dienkripsi

| Tabel | Kolom |
|---|---|
| messages | title_enc, body_enc |
| files | meta_enc |
| stego_items | note_enc |

---

## 5. Steganografi Gambar (R6)

### Algoritma: LSB (Least Significant Bit)

```
Pesan teks (bytes)
    │
    ▼ AES-256-GCM (kunci: HKDF(master_key, "stego", 32B))
    │
    ▼ payload = "STG1"(4B) | length(4B) | nonce(12B) | ct+tag
    │
    ▼ np.unpackbits() → bit stream
    │
    ▼ Timpa LSB piksel R,G,B secara berurutan
      flat[:n_bits] = (flat[:n_bits] & 0xFE) | payload_bits
    │
    ▼ Simpan PNG (lossless)
```

### Mengapa PNG/BMP Saja?

JPEG menggunakan kompresi lossy (DCT) yang mengubah nilai piksel, merusak LSB yang disisipkan. PNG dan BMP menyimpan piksel tepat seperti aslinya.

### PSNR

PSNR > 50 dB berarti perubahan LSB tidak terlihat secara visual (SNR sangat tinggi).

---

## 6. Blockchain Aset (R7)

### Struktur Blok

```python
Block:
    index       : int
    timestamp   : float
    data        : dict  # {"asset_id","asset_name","sha256","action","owner_sig"}
    prev_hash   : str   # SHA-256 blok sebelumnya
    nonce       : int   # hasil PoW
    hash        : str   # SHA-256(index|timestamp|data_json|prev_hash|nonce)
```

### Proof of Work

```
target = "0" * DIFFICULTY
while not block.hash.startswith(target):
    block.nonce += 1
    block.hash = SHA-256(...)
```

Difficulty default 3 → rata-rata 4.096 iterasi.

### Tanda Tangan Kepemilikan

```
owner_sig = HMAC-SHA256(HKDF(master_key, "blockchain-sign"), data_json)
```

Membuktikan bahwa blok dibuat oleh pemilik vault ini.

### Tamper Detection

Mengubah `data` atau `hash` blok manapun → `compute_hash()` menghasilkan nilai berbeda → `is_valid()` mengembalikan `False` dan mengidentifikasi indeks bermasalah.

---

## 7. Pemetaan Kebutuhan → Implementasi

| ID | Kebutuhan | File Utama | Fungsi/Kelas |
|---|---|---|---|
| R1 | Login biometrik | `core/auth/webauthn_service.py` | `verify_registration()`, `verify_authentication()` |
| R2 | Kriptografi login | `core/auth/kdf.py` | `hash_pin()`, `derive_master_key()`, `hkdf_derive()` |
| R2 | Token sesi | `core/auth/session.py` | `create_session()`, `require_auth()` |
| R3 | Super enkripsi teks | `core/crypto/text_super.py` | `encrypt_text()`, `decrypt_text()` |
| R3 | Algoritma klasik | `core/crypto/classical.py` | `vigenere_*()`, `columnar_*()` |
| R4 | Enkripsi file | `core/crypto/file_crypto.py` | `encrypt_file()`, `decrypt_file()` |
| R5 | DB terenkripsi | `core/db/models.py` | `encrypt_field()`, `decrypt_field()` |
| R6 | Steganografi | `core/stego/lsb_image.py` | `embed()`, `extract()` |
| R7 | Blockchain | `core/blockchain/chain.py` | `add_asset()`, `is_valid()`, `verify_asset()` |
| R8 | UI hitam-biru | `ui/styles.py`, `ui/layout.py` | `inject_global_css()`, `golden_columns()` |
