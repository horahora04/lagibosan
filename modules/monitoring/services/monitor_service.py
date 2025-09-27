from core.db import get_db
from typing import Dict, List

def save_event_sync(doc: Dict):
    db = get_db()
    db.monitor_events.insert_one(doc)

def get_events(limit: int = 50) -> List[Dict]:
    db = get_db()
    return list(db.monitor_events.find().sort("_id", -1).limit(limit))
