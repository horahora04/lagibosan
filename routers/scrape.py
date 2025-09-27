from fastapi import APIRouter, HTTPException
from core.runner import run_bot, register_bot, job_status
from modules.scrape.backend.scraper import Scraper
from modules.scrape.services.scraper_service import read_logs, get_recent_records

router = APIRouter(prefix="/scrape", tags=["scrape"])
register_bot("scrape", Scraper())

@router.post("/run")
def run_scrape(url: str):
    try:
        return run_bot("scrape", url=url)
    except Exception as e:
        raise HTTPException(500, str(e))

@router.get("/logs")
def logs():
    return {"lines": read_logs()}

@router.get("/records")
def records(limit: int = 50):
    return {"items": get_recent_records(limit)}

@router.get("/job/{job_id}")
def job(job_id: str):
    return job_status(job_id)
