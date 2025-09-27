from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import PlainTextResponse
from pathlib import Path
import json

router = APIRouter()

# 📂 Path ke folder Downloads
BASE_DIR = Path(__file__).resolve().parent.parent
DOWNLOADS_PATH = BASE_DIR / "Downloads"
SCRAPER_STATUS_FILE = DOWNLOADS_PATH / "scraper_status.json"

# ✅ Hanya file yang dipakai (pageURL, Urls, ScraperLog)
FILES = ["pageURL.txt", "Urls.txt", "ScraperLog.txt"]

# Pastikan file selalu ada
for fname in FILES:
    file_path = DOWNLOADS_PATH / fname
    if not file_path.exists():
        file_path.write_text("", encoding="utf-8")

# ========== Helper Functions ==========
def read_file(file_name: str) -> str:
    file_path = DOWNLOADS_PATH / file_name
    if not file_path.exists():
        raise HTTPException(status_code=404, detail=f"File '{file_name}' not found.")
    return file_path.read_text(encoding="utf-8")

def append_file(file_name: str, line: str):
    file_path = DOWNLOADS_PATH / file_name
    with open(file_path, "a", encoding="utf-8") as f:
        f.write(line + "\n")

def set_status(status: str):
    SCRAPER_STATUS_FILE.write_text(json.dumps({"status": status}), encoding="utf-8")

def get_status():
    if not SCRAPER_STATUS_FILE.exists():
        return "stopped"
    return json.loads(SCRAPER_STATUS_FILE.read_text()).get("status", "stopped")

# ========== Endpoint Baca File ==========
@router.get("/read/{file_name}", response_class=PlainTextResponse)
async def read_text_file(file_name: str):
    if file_name not in FILES:
        raise HTTPException(status_code=400, detail="Invalid file requested.")
    return read_file(file_name)

# ========== Kontrol Status ==========
@router.post("/start-scrape")
async def start_scrape():
    set_status("running")
    return {"status": "running"}

@router.post("/stop-scrape")
async def stop_scrape():
    set_status("stopped")
    return {"status": "stopped"}

@router.get("/get-scrape-status")
async def get_scrape_status():
    return {"status": get_status()}

# ========== Scraper Log ==========
@router.post("/write/log-line", response_class=PlainTextResponse)
async def write_log_line(request: Request):
    data = await request.json()
    line = data.get("line")
    if not line:
        raise HTTPException(status_code=400, detail="Missing 'line'")
    append_file("ScraperLog.txt", line)
    return f"✅ Log ditambahkan: {line}"

@router.get("/read/scraper-log", response_class=PlainTextResponse)
async def read_scraper_log():
    return read_file("ScraperLog.txt")

@router.post("/clear-scraper-log")
async def clear_scraper_log_file():
    (DOWNLOADS_PATH / "ScraperLog.txt").write_text("", encoding="utf-8")
    return {"status": "cleared"}
