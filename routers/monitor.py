from fastapi import APIRouter
from core.runner import run_bot, register_bot
from modules.monitoring.backend.monitor_bot import MonitorBot
from modules.monitoring.services.monitor_service import get_events

router = APIRouter(prefix="/monitor", tags=["monitor"])
register_bot("monitor", MonitorBot())

@router.post("/check")
def check(interval: int = 5):
    return run_bot("monitor", interval=interval)

@router.get("/events")
def events(limit: int = 50):
    return {"items": get_events(limit)}
