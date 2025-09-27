# routes/scrape.py
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import PlainTextResponse
from backend.backend_scrape import (
    start_scraper,
    stop_scraper,
    get_status,
    read_file,
    append_file,
    clear_file,
)

router = APIRouter()

# ========== Endpoint untuk File I/O ==========
@router.get("/read/{file_name}", response_class=PlainTextResponse)
async def read_text_file(file_name: str):
    """
    Membaca isi file dari folder Downloads.
    Hanya file yang diijinkan: pageURL.txt, Urls.txt, ScraperLog.txt
    """
    allowed_files = ["pageURL.txt", "Urls.txt", "ScraperLog.txt"]
    if file_name not in allowed_files:
        raise HTTPException(status_code=400, detail="Invalid file requested.")
    try:
        return read_file(file_name)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"File '{file_name}' not found.")

@router.post("/write/log-line", response_class=PlainTextResponse)
async def write_log_line(request: Request):
    """
    Tambahkan 1 baris log ke ScraperLog.txt
    Dipakai oleh content.js untuk mencatat URL kategori dan produk yang sedang dibuka.
    """
    data = await request.json()
    line = data.get("line")
    if not line:
        raise HTTPException(status_code=400, detail="Missing 'line'")
    append_file("ScraperLog.txt", line)
    return f"✅ Log ditambahkan: {line}"

@router.get("/read/scraper-log", response_class=PlainTextResponse)
async def read_scraper_log():
    """Mengembalikan seluruh isi ScraperLog.txt (untuk live log di dashboard)."""
    return read_file("ScraperLog.txt")

@router.post("/clear-scraper-log")
async def clear_scraper_log_file():
    """Mengosongkan ScraperLog.txt (tombol 'Clear Log' di dashboard)."""
    clear_file("ScraperLog.txt")
    return {"status": "cleared"}

# === Baru: ekstensi yang berhak clear Urls.txt setelah 1 halaman selesai ===
@router.post("/clear-urls")
async def clear_urls_file():
    try:
        clear_file("Urls.txt")
        return {"status": "cleared"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Gagal clear Urls.txt: {e}")

# ========== Endpoint untuk Kontrol Scraper ==========
@router.post("/start-scrape")
async def start_scrape():
    """
    Mulai scraping:
    - Mengaktifkan proxy Windows (HKCU)
    - Menjalankan mitmdump dengan addon scrape_mitm.py
    - Mengubah status menjadi 'running'
    (Tidak menghapus Urls.txt agar bisa resume jika perlu)
    """
    try:
        start_scraper()
        return {"status": "running"}
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/stop-scrape")
async def stop_scrape():
    """
    Hentikan scraping:
    - Menghentikan proses mitmdump (jika ada)
    - Mematikan proxy Windows
    - Mengubah status menjadi 'stopped'
    """
    stop_scraper()
    return {"status": "stopped"}

@router.get("/get-scrape-status")
async def get_scrape_status():
    """Mengembalikan status scraper (running/stopped) untuk polling content.js."""
    return {"status": get_status()}
