# routers/scrape.py
from fastapi import APIRouter, HTTPException
from core.runner import run_bot, register_bot, job_status
from modules.scrape.backend.scraper import Scraper
from modules.scrape.services.scraper_service import read_logs, get_status

router = APIRouter(prefix="/scrape", tags=["scrape"])

# daftar bot "scrape" saat router di-load
register_bot("scrape", Scraper())

# ----------------- kontrol scraper -----------------
@router.post("/start")
def start():
    try:
        return run_bot("scrape", action="start")
    except Exception as e:
        raise HTTPException(500, str(e))

@router.post("/stop")
def stop():
    try:
        return run_bot("scrape", action="stop")
    except Exception as e:
        raise HTTPException(500, str(e))

@router.get("/status")
def status():
    try:
        return run_bot("scrape", action="status")
    except Exception as e:
        raise HTTPException(500, str(e))

# ----------------- monitoring -----------------
@router.get("/logs")
def logs():
    """Baca log scraper (ScraperLog.txt)"""
    return {"lines": read_logs()}

@router.get("/job/{job_id}")
def job(job_id: str):
    """Cek status job yang sedang jalan"""
    return job_status(job_id)

# (opsional) tambahan: status file JSON langsung
@router.get("/raw-status")
def raw_status():
    return {"status": get_status()}
