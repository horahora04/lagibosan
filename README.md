# 🧭 Dokumentasi Alur Program -- Shopee Scraper + URL Opener (Final)

## 1️⃣ Persiapan

**File Utama:** - `pageURL.txt` → daftar kategori Shopee. - `Urls.txt` →
diisi otomatis oleh mitmproxy untuk setiap halaman kategori. -
`ScraperLog.txt` → menyimpan riwayat kategori, halaman, dan produk yang
telah dibuka.

**Backend FastAPI:**

-   **Endpoint Kontrol:**
    -   `/start-scrape` & `/stop-scrape`
    -   `/get-scrape-status`
-   **Endpoint File:**
    -   `/read/pageURL.txt`, `/read/Urls.txt`, `/read/ScraperLog.txt`
    -   `/write/log-line` → mencatat log.
    -   `/clear-scraper-log` → reset log.

------------------------------------------------------------------------

## 2️⃣ Alur Eksekusi (Rinci)

### 🟢 Start

1.  Klik **"Mulai Scrape"** di dashboard → backend set
    `status = running`.
2.  `content.js` polling `/get-scrape-status` setiap 3 detik →
    mendeteksi status berubah menjadi `running`.
3.  Ekstensi memulai proses scraping.

### 🔄 Loop Kategori

Untuk setiap kategori di `pageURL.txt`: 1. Buka kategori di **tab
utama** (tab tetap digunakan sampai kategori selesai). 2. Tunggu
sebentar (delay awal) → memberi waktu mitmproxy menangkap data. 3.
**Mitmproxy mengisi `Urls.txt`** (daftar produk pada halaman kategori).
4. Jalankan **loop produk** (lihat di bawah). 5. Setelah produk di
halaman ini selesai → lanjut ke **pagination berikutnya**. 6. Ulangi
langkah 3--5 sampai halaman terakhir kategori. 7. Setelah kategori habis
→ lanjut ke kategori berikutnya.

### 📦 Loop Produk

Untuk setiap produk di `Urls.txt`: 1. **Buka produk** di tab baru
(foreground). 2. **Tunggu delay acak 5--20 detik** → agar mirip perilaku
manusia. 3. **Tutup tab produk**. 4. Lanjut ke produk berikutnya sampai
`Urls.txt` habis.

### ↪️ Loop Pagination

Setelah semua produk di halaman selesai: 1. Klik tombol **next
pagination** di tab kategori. 2. Tunggu halaman selesai dimuat. 3.
Kembali ke langkah "Mitmproxy mengisi Urls.txt" → ulangi sampai
pagination habis.

### 🛑 Stop

1.  Klik **"Hentikan Scrape"** di dashboard → backend set
    `status = stopped`.
2.  `content.js` mendeteksi status berubah → menghentikan loop
    (kategori, pagination, atau produk) di titik saat itu.
3.  **Log terakhir** tetap tersimpan di `ScraperLog.txt`.

------------------------------------------------------------------------

## 3️⃣ Live Log & Monitoring

-   Semua aksi tercatat di `ScraperLog.txt` dengan format:

        https://shopee.co.id/cat.11044364?page=1 | https://shopee.co.id/item/123

-   **Dashboard (`scrape.html`) menampilkan log secara real-time:**

    -   **Hijau** → kategori + halaman.
    -   **Biru** → URL produk.

-   Memudahkan **resume** jika terjadi gangguan (mati listrik, captcha,
    crash).

------------------------------------------------------------------------

## 4️⃣ Alur Keseluruhan (Ringkas)

``` text
Klik Mulai Scrape →
  content.js polling status →
    Buka kategori 1 di tab utama →
      Mitmproxy isi Urls.txt →
         Loop produk → buka, delay, tutup →
      Klik pagination → ulangi proses sampai halaman terakhir →
    Lanjut kategori berikutnya
Klik Hentikan Scrape → hentikan loop aktif
```

------------------------------------------------------------------------

## 5️⃣ Kelebihan

✅ **Sequential & Terkontrol** → hanya satu tab produk aktif pada satu
waktu.\
✅ **Tahan Gangguan** → bisa melanjutkan dari log jika proses terputus.\
✅ **Monitoring Real-Time** → status & log terlihat di dashboard.\
✅ **Terintegrasi Mitmproxy** → data produk selalu fresh sesuai halaman.
