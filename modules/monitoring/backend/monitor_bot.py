from core.logger import get_logger
from modules.monitoring.services.monitor_service import save_event_sync
logger = get_logger("MonitorBot")

class MonitorBot:
    name = "monitor"

    def run(self, interval: int = 5):
        logger.info(f"[Monitor] run with interval {interval}")
        # demo: store simple event
        save_event_sync({"info": f"checked interval {interval}"})
        return {"status": "ok", "interval": interval}
