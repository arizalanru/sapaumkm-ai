# SapaUMKM AI

SapaUMKM AI adalah prototipe layanan pelanggan berbasis AI untuk GlowMart Skincare, sebuah UMKM skincare Indonesia. Aplikasi ini menggabungkan percakapan pelanggan yang natural, jawaban berbasis data bisnis, pelacakan pesanan deterministik, dan alih layanan dua arah dari AI ke admin manusia.

## AI Builder Challenge

Proyek ini dibuat dalam konteks AI Builder Challenge untuk menunjukkan bagaimana AI dapat membantu UMKM menangani pertanyaan berulang tanpa menghilangkan peran manusia pada kasus yang sensitif. Fokus prototipe adalah pengalaman yang dapat didemonstrasikan secara utuh: pelanggan berbicara dengan Sapa, sistem mengambil pengetahuan yang relevan, dan admin mengambil alih percakapan ketika diperlukan.

## Masalah yang Diselesaikan

UMKM sering menerima pertanyaan yang sama tentang produk, harga, stok, cara pakai, pembayaran, pengiriman, dan status pesanan. Menjawab semuanya secara manual membutuhkan waktu, sedangkan chatbot tanpa grounding berisiko mengarang informasi bisnis atau memberikan keputusan yang bukan kewenangannya.

SapaUMKM AI mengatasi masalah tersebut dengan:

- mengambil produk, harga, stok, FAQ, dan pesanan dari SQLite;
- membatasi jawaban Groq pada konteks data yang ditemukan;
- menjaga pelacakan pesanan dan eskalasi tetap dikendalikan backend;
- meneruskan refund, keluhan, produk rusak, pertanyaan medis, dan permintaan admin kepada manusia;
- tetap berfungsi dengan fallback deterministik ketika Groq tidak tersedia.

## Fitur Utama

- Percakapan Bahasa Indonesia formal maupun kasual.
- Pencarian produk dan rekomendasi berdasarkan jenis kulit serta anggaran.
- Informasi produk, harga, stok, manfaat yang tercatat, dan cara pakai.
- Pelacakan pesanan dari data SQLite tanpa mengarang nomor pesanan atau resi.
- Informasi pembayaran, pengiriman, promosi, dan kebijakan dari FAQ.
- Konteks percakapan singkat untuk memahami pertanyaan lanjutan.
- Integrasi Groq melalui backend dengan respons grounded.
- Fallback deterministik ketika API key tidak tersedia atau permintaan Groq gagal.
- Penyimpanan percakapan dan pesan di SQLite.
- Human handoff dua arah dengan takeover, balasan admin, resolve, dan return-to-AI.
- Polling pesan customer dan admin tanpa kompleksitas WebSocket.
- Persistensi conversation ID di localStorage agar sesi customer dapat dipulihkan setelah refresh.
- Tampilan customer dan admin yang terpisah serta responsif.

## Route Aplikasi

| Route | Pengguna | Fungsi |
| --- | --- | --- |
| `/` | Pelanggan | Chat privat dengan Sapa atau Tim GlowMart. |
| `/admin` | Admin | Ringkasan, kotak masuk, takeover percakapan, balasan manual, produk, dan basis pengetahuan. |

API FastAPI tersedia secara lokal di `http://localhost:8000`, dengan dokumentasi interaktif di `/docs`.

## Alur Human Handoff

Percakapan menggunakan empat status yang jelas:

```text
ai_active
    -> waiting_admin     Refund, keluhan, kasus sensitif, atau permintaan admin
    -> admin_active      Admin memilih "Ambil alih"
    -> resolved          Admin menyelesaikan percakapan

admin_active/resolved
    -> ai_active         Admin memilih "Kembalikan ke AI"
```

Saat status `waiting_admin` atau `admin_active`, pesan pelanggan tetap disimpan tetapi Groq tidak dipanggil dan sistem tidak membuat balasan AI palsu. Admin hanya dapat mengirim pesan setelah takeover. Customer menerima pesan admin melalui polling dan dapat membalas pada thread yang sama.

## Arsitektur Teknis

```text
Customer / Admin UI
React + Vinext + Vite
        |
        | HTTP JSON + polling
        v
FastAPI backend
        |
        +-- Intent detection dan aturan eskalasi
        +-- Knowledge retrieval terbatas
        +-- Groq chat completions
        +-- Fallback deterministik
        |
        v
SQLite + SQLAlchemy
Products, FAQs, orders, conversations, messages
```

Prinsip grounding utama:

1. Produk, harga, stok, cara pakai, FAQ, dan pesanan berasal dari SQLite.
2. Hanya record yang relevan dimasukkan ke konteks Groq.
3. Pelacakan pesanan tidak diserahkan kepada LLM.
4. Backend tidak mengirim API key ke browser.
5. Respons Groq hanya mengambil `message.content`; reasoning model tidak dibaca, disimpan, atau ditampilkan.

Konfigurasi Cloudflare/Vinext tetap dipertahankan melalui `vite.config.ts`, plugin Cloudflare, worker, dan metadata hosting di `.openai/hosting.json`. Build lokal menggunakan `vinext build`; pipeline Sites berbasis Bash tetap tersedia melalui `npm run build:sites`.

## Technology Stack

### Frontend

- React 19
- Vinext
- Vite
- TypeScript
- Lucide React
- Cloudflare Vite Plugin

### Backend

- Python
- FastAPI
- SQLAlchemy
- SQLite
- Pydantic
- HTTPX
- python-dotenv
- Groq Chat Completions API

### Testing

- pytest
- FastAPI TestClient
- Node.js test runner
- Vinext production build validation

## Menjalankan Secara Lokal di Windows PowerShell

### Prasyarat

- Node.js 22.13 atau lebih baru
- npm
- Python 3.10 atau lebih baru
- Windows PowerShell

Gunakan dua terminal dari folder utama repository.

### Terminal 1: Backend

```powershell
cd backend
py -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
uvicorn app.main:app --reload --port 8000
```

SQLite dan data demo dibuat otomatis ketika backend pertama dijalankan.

### Terminal 2: Frontend

```powershell
npm install
Copy-Item .env.example .env
npm run dev
```

Frontend tersedia di `http://localhost:5173` dan backend di `http://localhost:8000`.

## Environment Variables

Jangan menaruh API key di frontend atau source code. Buat file lokal dari `.env.example`, lalu ganti placeholder sesuai lingkungan Anda.

### `backend/.env`

```dotenv
GROQ_API_KEY=<YOUR_GROQ_API_KEY>
GROQ_MODEL=<YOUR_GROQ_MODEL_NAME>
FRONTEND_URL=<YOUR_FRONTEND_ORIGIN>
```

### `.env`

```dotenv
VITE_API_URL=<YOUR_BACKEND_ORIGIN>
```

Contoh origin lokal dijelaskan pada file `.env.example`. Jika `GROQ_API_KEY` kosong, aplikasi tetap dapat didemonstrasikan dengan fallback deterministik.

## Testing dan Validasi

### Backend

```powershell
cd backend
.venv\Scripts\Activate.ps1
python -m pytest -q
```

### Regresi sesi customer

```powershell
npm run test:customer-chat
```

### Build produksi frontend

```powershell
npm run build
```

### Validasi terakhir

- Backend: **67 tests passed**.
- Regresi sesi customer: **7 tests passed**.
- Frontend production build: **passed** untuk route `/` dan `/admin`.
- Rendered HTML validation: **passed**.

Hasil tersebut adalah validasi pengembangan lokal, bukan metrik produksi.

## Skenario Demo

1. **Jelajah produk**  
   Kirim: `Jual produk apa saja yang tersedia?`

2. **Rekomendasi grounded**  
   Kirim: `Rekomendasi moisturizer untuk kulit berminyak di bawah Rp100.000.`

3. **Pembayaran**  
   Kirim: `Bisa bayar pakai QRIS atau BCA?`

4. **Pelacakan deterministik**  
   Kirim: `Cek pesanan GM-1002.`

5. **Pertanyaan lanjutan**  
   Mulai dengan kebutuhan kulit dan anggaran, lalu tanyakan produk termurah dan cara pakainya.

6. **Human handoff dua arah**  
   - Di `/`, kirim: `Barang saya rusak dan ingin refund.`
   - Di `/admin`, buka filter **Butuh admin** dan pilih percakapan.
   - Klik **Ambil alih**, lalu kirim balasan sebagai Tim GlowMart.
   - Pastikan pesan muncul di customer tanpa refresh.
   - Balas dari customer, kemudian pilih **Selesaikan** atau **Kembalikan ke AI**.

7. **Pemulihan sesi**  
   Refresh route `/` setelah percakapan dimulai dan pastikan conversation ID serta riwayat yang sama dipulihkan.

## Estimasi Dampak Bisnis

> Semua angka pada bagian ini adalah **estimasi ilustratif**, bukan hasil produksi atau klaim performa aktual.

Dengan asumsi sebuah UMKM menerima 500 percakapan per bulan, 60% pertanyaan dapat ditangani otomatis, dan setiap respons manual membutuhkan rata-rata 2 menit:

```text
500 percakapan x 60% x 2 menit = 600 menit
Estimasi waktu yang dapat dialihkan = 10 jam per bulan
```

Potensi dampak kualitatif:

- admin memusatkan waktu pada refund, keluhan, dan kasus sensitif;
- jawaban harga dan stok lebih konsisten karena berasal dari katalog;
- pelanggan mendapatkan respons awal lebih cepat untuk pertanyaan berulang;
- riwayat handoff mengurangi kebutuhan pelanggan mengulang konteks.

Estimasi harus divalidasi dengan volume chat, tingkat otomatisasi, dan waktu penanganan nyata sebelum digunakan untuk keputusan bisnis.

## Batasan Prototipe

- Tidak ada checkout atau pembuatan order baru.
- Tidak ada verifikasi pembayaran atau konfirmasi bahwa transaksi berhasil.
- Tidak ada pembuatan pengiriman atau nomor resi baru.
- AI tidak menyetujui refund; keputusan tetap dilakukan admin.
- Admin belum memiliki autentikasi, role, identitas operator, atau audit log produksi.
- Sinkronisasi pesan menggunakan polling sekitar dua detik, bukan WebSocket.
- SQLite cocok untuk prototipe lokal, bukan deployment multi-instance berskala besar.
- Retrieval berbasis keyword dan konteks singkat, tanpa vector database.
- Conversation ID customer disimpan per browser dan origin melalui localStorage.
- Belum tersedia observability, rate limiting, backup, dan hardening keamanan produksi lengkap.
- Jawaban LLM tetap dapat gagal; fallback deterministik menjaga demo tetap berjalan tetapi lebih terbatas.

## Author

**Arizal Anru — AI Builder Candidate**
