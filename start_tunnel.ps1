# =============================================================================
# start_tunnel.ps1 — Jalankan Obsidian Vault + Cloudflare Tunnel otomatis
# =============================================================================
# Cara pakai:
#   1. Buka PowerShell di folder project ini
#   2. Jalankan: .\start_tunnel.ps1
#   3. Tunggu URL tunnel muncul, lalu buka di HP
#
# Pertama kali: script akan cek cloudflared, jika belum ada akan otomatis download.
# =============================================================================

$ErrorActionPreference = "Stop"
$ProjectDir   = $PSScriptRoot
$EnvFile      = Join-Path $ProjectDir ".env"
$VenvPython   = Join-Path $ProjectDir "venv\Scripts\python.exe"
$VenvStreamlit= Join-Path $ProjectDir "venv\Scripts\streamlit.exe"
$CloudflaredExe = Join-Path $ProjectDir "cloudflared.exe"

# ── Warna output ──────────────────────────────────────────────────────────────
function Write-Step($msg)  { Write-Host "`n  ► $msg" -ForegroundColor Cyan }
function Write-Ok($msg)    { Write-Host "  ✓ $msg"   -ForegroundColor Green }
function Write-Warn($msg)  { Write-Host "  ⚠ $msg"   -ForegroundColor Yellow }
function Write-Err($msg)   { Write-Host "  ✗ $msg"   -ForegroundColor Red }
function Write-Banner($msg){ Write-Host $msg -ForegroundColor Blue }

Write-Banner @"

  ╔══════════════════════════════════════════════════╗
  ║         OBSIDIAN VAULT — TUNNEL LAUNCHER         ║
  ╚══════════════════════════════════════════════════╝
"@

# ── 1. Cek / download cloudflared ─────────────────────────────────────────────
Write-Step "Memeriksa cloudflared..."

$cfAvailable = $false

# Cek di PATH dulu
$cfInPath = Get-Command cloudflared -ErrorAction SilentlyContinue
if ($cfInPath) {
    $CloudflaredExe = $cfInPath.Source
    $cfAvailable    = $true
    Write-Ok "cloudflared ditemukan di PATH: $CloudflaredExe"
}
# Cek di folder project
elseif (Test-Path $CloudflaredExe) {
    $cfAvailable = $true
    Write-Ok "cloudflared ditemukan di folder project."
}
# Tidak ada — download otomatis
else {
    Write-Warn "cloudflared tidak ditemukan. Mengunduh otomatis..."
    $downloadUrl = "https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-windows-amd64.exe"
    try {
        Write-Host "    Mengunduh dari: $downloadUrl" -ForegroundColor DarkGray
        Invoke-WebRequest -Uri $downloadUrl -OutFile $CloudflaredExe -UseBasicParsing
        $cfAvailable = $true
        Write-Ok "cloudflared berhasil diunduh ke: $CloudflaredExe"
    }
    catch {
        Write-Err "Gagal mengunduh cloudflared: $_"
        Write-Host @"

  Download manual dari:
  https://github.com/cloudflare/cloudflared/releases/latest
  → Pilih: cloudflared-windows-amd64.exe
  → Simpan di folder project ini, ganti nama jadi: cloudflared.exe

"@ -ForegroundColor Yellow
        exit 1
    }
}

# ── 2. Cek Python venv ────────────────────────────────────────────────────────
Write-Step "Memeriksa virtual environment Python..."
if (-not (Test-Path $VenvPython)) {
    Write-Err "venv tidak ditemukan di: $VenvPython"
    Write-Host "  Jalankan dulu: python -m venv venv && .\venv\Scripts\pip install -r requirements.txt" -ForegroundColor Yellow
    exit 1
}
Write-Ok "venv ditemukan."

# ── 3. Cek .env ───────────────────────────────────────────────────────────────
Write-Step "Memeriksa file .env..."
if (-not (Test-Path $EnvFile)) {
    Write-Warn ".env tidak ada, membuat dari .env.example..."
    Copy-Item (Join-Path $ProjectDir ".env.example") $EnvFile
}

# Baca isi .env saat ini
$envContent = Get-Content $EnvFile -Raw

# Pastikan SESSION_SECRET sudah diganti dari default
if ($envContent -match "ganti_dengan") {
    Write-Step "Membuat SESSION_SECRET baru..."
    $secret = & $VenvPython -c "import secrets; print(secrets.token_hex(32))"
    $envContent = $envContent -replace "SESSION_SECRET=.*", "SESSION_SECRET=$secret"
    Write-Ok "SESSION_SECRET dibuat: $secret"
}

# ── 4. Matikan proses lama jika ada ───────────────────────────────────────────
Write-Step "Mematikan proses Streamlit/cloudflared lama (jika ada)..."
Get-Process -Name "streamlit" -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
Get-Process -Name "cloudflared" -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
Start-Sleep -Milliseconds 800
Write-Ok "Proses lama dihentikan."

# ── 5. Jalankan Streamlit di background ───────────────────────────────────────
Write-Step "Menjalankan Streamlit (sementara dengan config lokal)..."

# Set .env sementara agar Streamlit bisa start dulu (dengan localhost)
$tmpEnv = $envContent -replace "RP_ID=.*",    "RP_ID=localhost"
$tmpEnv = $tmpEnv     -replace "ORIGIN=.*",   "ORIGIN=http://localhost:8501"
$tmpEnv = $tmpEnv     -replace "DEV_MODE=.*", "DEV_MODE=false"
[System.IO.File]::WriteAllText($EnvFile, $tmpEnv, [System.Text.Encoding]::UTF8)

$streamlitLog = Join-Path $ProjectDir "streamlit.log"
$stProc = Start-Process -FilePath $VenvStreamlit `
    -ArgumentList "run", "app.py" `
    -WorkingDirectory $ProjectDir `
    -RedirectStandardOutput $streamlitLog `
    -RedirectStandardError  "$streamlitLog.err" `
    -PassThru -WindowStyle Hidden

Write-Ok "Streamlit berjalan (PID: $($stProc.Id)). Log: $streamlitLog"
Write-Host "  Menunggu Streamlit siap..." -ForegroundColor DarkGray
Start-Sleep -Seconds 4

# ── 6. Jalankan cloudflared dan tangkap URL ────────────────────────────────────
Write-Step "Menjalankan Cloudflare Tunnel..."

$tunnelLog = Join-Path $ProjectDir "cloudflared.log"
$cfProc = Start-Process -FilePath $CloudflaredExe `
    -ArgumentList "tunnel", "--url", "http://localhost:8501" `
    -WorkingDirectory $ProjectDir `
    -RedirectStandardOutput $tunnelLog `
    -RedirectStandardError  $tunnelLog `
    -PassThru -WindowStyle Hidden

Write-Host "  Menunggu URL tunnel (maks 30 detik)..." -ForegroundColor DarkGray

$tunnelUrl   = $null
$maxWait     = 30
$waited      = 0
$checkInterval = 1

while ($waited -lt $maxWait -and -not $tunnelUrl) {
    Start-Sleep -Seconds $checkInterval
    $waited += $checkInterval
    if (Test-Path $tunnelLog) {
        $logText = Get-Content $tunnelLog -Raw -ErrorAction SilentlyContinue
        if ($logText -match 'https://[a-zA-Z0-9\-]+\.trycloudflare\.com') {
            $tunnelUrl = $Matches[0]
        }
    }
    Write-Host "  ." -NoNewline -ForegroundColor DarkGray
}
Write-Host ""

if (-not $tunnelUrl) {
    Write-Err "URL tunnel tidak ditemukan dalam $maxWait detik."
    Write-Host "  Cek log: $tunnelLog" -ForegroundColor Yellow
    Write-Host "  Pastikan koneksi internet aktif." -ForegroundColor Yellow
    # Hentikan proses
    $stProc | Stop-Process -Force -ErrorAction SilentlyContinue
    $cfProc | Stop-Process -Force -ErrorAction SilentlyContinue
    exit 1
}

Write-Ok "URL tunnel ditemukan: $tunnelUrl"

# ── 7. Update .env dengan URL tunnel yang benar ───────────────────────────────
Write-Step "Memperbarui .env dengan URL tunnel..."

# Ekstrak domain dari URL (hapus https://)
$domain = $tunnelUrl -replace "^https://", ""

$newEnv = $envContent -replace "DEV_MODE=.*", "DEV_MODE=false"
$newEnv = $newEnv     -replace "RP_ID=.*",    "RP_ID=$domain"
$newEnv = $newEnv     -replace "ORIGIN=.*",   "ORIGIN=$tunnelUrl"
[System.IO.File]::WriteAllText($EnvFile, $newEnv, [System.Text.Encoding]::UTF8)

Write-Ok ".env diperbarui:"
Write-Host "    RP_ID   = $domain"     -ForegroundColor DarkGray
Write-Host "    ORIGIN  = $tunnelUrl"  -ForegroundColor DarkGray

# ── 8. Restart Streamlit dengan .env yang sudah update ────────────────────────
Write-Step "Merestart Streamlit dengan konfigurasi tunnel..."
$stProc | Stop-Process -Force -ErrorAction SilentlyContinue
Start-Sleep -Seconds 2

$stProc2 = Start-Process -FilePath $VenvStreamlit `
    -ArgumentList "run", "app.py" `
    -WorkingDirectory $ProjectDir `
    -RedirectStandardOutput $streamlitLog `
    -RedirectStandardError  "$streamlitLog.err" `
    -PassThru -WindowStyle Hidden

Write-Ok "Streamlit restart (PID: $($stProc2.Id))"
Start-Sleep -Seconds 3

# ── 9. Tampilkan hasil ────────────────────────────────────────────────────────
Write-Host ""
Write-Banner @"

  ╔══════════════════════════════════════════════════╗
  ║               ✅  TUNNEL AKTIF!                   ║
  ╠══════════════════════════════════════════════════╣
  ║                                                  ║
"@
Write-Host ("  ║  🌐 URL: " + $tunnelUrl.PadRight(39) + "║") -ForegroundColor Green
Write-Banner @"
  ║                                                  ║
  ║  Buka URL di atas di browser HP kamu.            ║
  ║  Pastikan HP & PC terhubung internet.            ║
  ║                                                  ║
  ║  Langkah selanjutnya:                            ║
  ║  1. Buka tab "Daftar" di HP                      ║
  ║  2. Isi nama & passphrase → Buat Akun            ║
  ║  3. Klik tombol passkey → sidik jari             ║
  ║  4. Login dengan biometrik                       ║
  ║                                                  ║
  ║  Tekan Ctrl+C di sini untuk menghentikan.        ║
  ╚══════════════════════════════════════════════════╝

"@

# ── 10. Buka browser lokal juga ───────────────────────────────────────────────
try {
    Start-Process $tunnelUrl
    Write-Host "  Browser dibuka otomatis di PC." -ForegroundColor DarkGray
} catch {}

# ── 11. Tunggu sampai user tekan Ctrl+C ───────────────────────────────────────
Write-Host "  Log Streamlit: $streamlitLog" -ForegroundColor DarkGray
Write-Host "  Log Tunnel   : $tunnelLog"    -ForegroundColor DarkGray
Write-Host ""
Write-Host "  Tekan Ctrl+C untuk menghentikan semua proses..." -ForegroundColor Yellow

try {
    # Monitor dan tampilkan jika ada error
    while ($true) {
        Start-Sleep -Seconds 5
        # Cek jika Streamlit mati tak terduga
        if ($stProc2.HasExited) {
            Write-Warn "Streamlit berhenti tak terduga. Cek log: $streamlitLog"
        }
        # Cek jika cloudflared mati
        if ($cfProc.HasExited) {
            Write-Warn "Cloudflared berhenti. Tunnel tidak aktif lagi."
            break
        }
    }
} finally {
    # Cleanup saat Ctrl+C
    Write-Host "`n  Menghentikan semua proses..." -ForegroundColor Yellow
    $stProc2 | Stop-Process -Force -ErrorAction SilentlyContinue
    $cfProc  | Stop-Process -Force -ErrorAction SilentlyContinue

    # Reset .env kembali ke localhost
    Write-Step "Mereset .env ke localhost..."
    $resetEnv = $newEnv -replace "RP_ID=.*",  "RP_ID=localhost"
    $resetEnv = $resetEnv -replace "ORIGIN=.*", "ORIGIN=http://localhost:8501"
    [System.IO.File]::WriteAllText($EnvFile, $resetEnv, [System.Text.Encoding]::UTF8)
    Write-Ok ".env direset ke localhost."
    Write-Host "`n  Selesai. Sampai jumpa!" -ForegroundColor Cyan
}
