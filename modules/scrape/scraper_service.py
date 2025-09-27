from pathlib import Path
from core.db import get_db
from typing import Dict, List

DOWNLOADS = Path("Downloads")
DOWNLOADS.mkdir(exist_ok=True)
LOG_FILE = DOWNLOADS / "ScraperLog.txt"

def save_log(line: str):
    with LOG_FILE.open("a", encoding="utf-8") as f:
        f.write(line + "\n")

def read_logs() -> List[str]:
    if not LOG_FILE.exists():
        return []
    return LOG_FILE.read_text(encoding="utf-8").splitlines()

def insert_record_sync(doc: Dict) -> str:
    db = get_db()
    res = db.scrape_records.insert_one(doc)
    return str(res.inserted_id)

def get_recent_records(limit: int = 50):
    db = get_db()
    cursor = db.scrape_records.find().sort("_id", -1).limit(limit)
    return list(cursor)
