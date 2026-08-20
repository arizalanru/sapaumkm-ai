# SapaUMKM AI — Menjalankan Secara Lokal

Prototype ini terdiri dari frontend Vite/Vinext dan backend FastAPI. Jalankan keduanya dari dua jendela Windows PowerShell.

## Persyaratan

- Node.js 22.13 atau lebih baru
- npm
- Python 3.10 atau lebih baru (`py` tersedia di PowerShell)

## Terminal 1 — Backend

Dari folder utama repository:

```powershell
cd backend
py -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
uvicorn app.main:app --reload --port 8000
```

SQLite dan data demo dibuat otomatis saat backend pertama dijalankan. API tersedia di `http://localhost:8000` dan dokumentasi interaktif di `http://localhost:8000/docs`.

Untuk memakai Groq, buka `backend/.env` dan isi nilai berikut dengan API key milik Anda:

```dotenv
GROQ_API_KEY=
```

Jangan menaruh key di `.env` frontend atau di source code. Jika key dibiarkan kosong atau Groq gagal dihubungi, backend memakai respons fallback deterministik.

## Terminal 2 — Frontend

Dari folder utama repository:

```powershell
npm install
Copy-Item .env.example .env
npm run dev
```

Frontend biasanya tersedia di `http://localhost:5173`. Nilai default pada `.env.example` mengarahkan frontend ke backend lokal:

```dotenv
VITE_API_URL=http://localhost:8000
```

## Validasi

Dengan virtual environment backend aktif:

```powershell
cd backend
pytest
```

Build frontend lokal yang kompatibel dengan PowerShell:

```powershell
npm run build:local
```

Script `npm run build` yang sudah ada tetap dipertahankan untuk pipeline Cloudflare/Vinext berbasis Bash.

Skenario demo:

- `Rekomendasi moisturizer untuk kulit berminyak di bawah Rp100.000`
- `Cek pesanan GM-1002`
- `Bisa bayar pakai QRIS?`
- `Barang saya rusak dan ingin refund`
