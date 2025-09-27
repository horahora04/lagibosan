# routers/scrape.py
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from core.runner import run_bot, register_bot, job_status
from modules.scrape.backend.scraper import Scraper
from modules.scrape.services import scraper_service

router = APIRouter(prefix="/scrape", tags=["scrape"])

# ----------------- inisialisasi bot -----------------
# daftar bot "scrape" saat router di-load
register_bot("scrape", Scraper())

# ----------------- kontrol scraper -----------------
@router.post("/start")
def start():
    """Mulai proses scraping (mitmdump + proxy)."""
    try:
        return run_bot("scrape", action="start")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/stop")
def stop():
    """Hentikan proses scraping (matikan mitmdump + disable proxy)."""
    try:
        return run_bot("scrape", action="stop")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/status")
def status():
    """Cek status scraper (running / stopped / error)."""
    try:
        return run_bot("scrape", action="status")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ----------------- monitoring -----------------
@router.get("/logs")
def logs(limit: int | None = None):
    """
    Baca log scraper (ScraperLog.txt).
    Param optional: ?limit=50 untuk ambil 50 baris terakhir.
    """
    return {"lines": scraper_service.read_logs(limit)}

@router.get("/job/{job_id}")
def job(job_id: str):
    """Cek status job yang sedang berjalan berdasarkan job_id."""
    return job_status(job_id)

@router.get("/raw-status")
def raw_status():
    """Ambil status langsung dari file scraper_status.json."""
    return {"status": scraper_service.get_status()}

# ----------------- integrasi Chrome Extension -----------------
@router.get("/urls")
def get_urls():
    """Ambil daftar URL produk (Urls.txt)."""
    return "\n".join(scraper_service.read_urls())

@router.post("/urls/clear")
def clear_urls():
    """Kosongkan Urls.txt."""
    scraper_service.write_urls([])
    return {"cleared": True}

class LogLine(BaseModel):
    line: str

@router.post("/log")
def write_log(data: LogLine):
    """Tulis satu baris log tambahan (dipanggil dari content.js)."""
    scraper_service.save_log(data.line)
    return {"ok": True}
