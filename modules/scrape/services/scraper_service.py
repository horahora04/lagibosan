# modules/scrape/services/scraper_service.py
from pathlib import Path
import json
from typing import List, Dict, Optional
from datetime import datetime
from core.config import SCRAPE_DIR, LOGS_DIR
from core.logger import get_logger

logger = get_logger("scraper_service")

# -------------------- Paths --------------------
LOG_FILE = SCRAPE_DIR / "ScraperLog.txt"
URLS_FILE = SCRAPE_DIR / "Urls.txt"
SCRAPER_STATUS_FILE = SCRAPE_DIR / "scraper_status.json"

# pastikan file exist
SCRAPE_DIR.mkdir(parents=True, exist_ok=True)
for p in (LOG_FILE, URLS_FILE):
    if not p.exists():
        p.write_text("", encoding="utf-8")
if not SCRAPER_STATUS_FILE.exists():
    SCRAPER_STATUS_FILE.write_text(json.dumps({"status": "stopped"}), encoding="utf-8")

# -------------------- File-based Logs --------------------
def save_log(line: str):
    """Append a line to ScraperLog.txt"""
    ts = datetime.now().strftime("%H:%M:%S")
    entry = f"[{ts}] {line}"
    with LOG_FILE.open("a", encoding="utf-8") as f:
        f.write(entry + "\n")
    logger.debug(f"Log appended: {entry}")


def read_logs(limit: Optional[int] = None) -> List[str]:
    """Read ScraperLog.txt, optionally limit last N lines"""
    if not LOG_FILE.exists():
        return []
    lines = LOG_FILE.read_text(encoding="utf-8").splitlines()
    return lines[-limit:] if limit else lines


def clear_logs():
    """Clear ScraperLog.txt"""
    LOG_FILE.write_text("", encoding="utf-8")
    logger.info("Scraper logs cleared")


# -------------------- Status Control --------------------
def set_status(status: str):
    SCRAPER_STATUS_FILE.write_text(json.dumps({"status": status}), encoding="utf-8")
    logger.info(f"Scraper status set to {status}")


def get_status() -> str:
    if SCRAPER_STATUS_FILE.exists():
        try:
            return json.loads(SCRAPER_STATUS_FILE.read_text()).get("status", "stopped")
        except Exception as e:
            logger.warning(f"Failed to parse status file: {e}")
            return "stopped"
    return "stopped"


# -------------------- URL Helpers --------------------
def write_urls(urls: List[str]):
    """Replace Urls.txt with given list"""
    with URLS_FILE.open("w", encoding="utf-8") as f:
        f.write("\n".join(urls))
    logger.info(f"{len(urls)} URLs written to {URLS_FILE}")


def read_urls() -> List[str]:
    if not URLS_FILE.exists():
        return []
    return URLS_FILE.read_text(encoding="utf-8").splitlines()


# -------------------- DB Helpers (Optional) --------------------
def insert_record_sync(doc: Dict, collection: str = "scrape_records") -> str:
    """
    Insert record ke MongoDB.
    Kalau tidak pakai DB, return "" saja.
    """
    try:
        from modules.scrape.services.db_scrape import get_db
        db = get_db()
        doc["created_at"] = doc.get("created_at", datetime.now())
        doc["updated_at"] = datetime.now()
        res = db[collection].insert_one(doc)
        logger.info(f"Record inserted into {collection}: {res.inserted_id}")
        return str(res.inserted_id)
    except Exception as e:
        logger.warning(f"Insert record failed: {e}")
        return ""
