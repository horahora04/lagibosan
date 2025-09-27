from typing import Dict, Any
from core.logger import get_logger
import concurrent.futures
import uuid

logger = get_logger("runner")
BOTS: Dict[str, object] = {}
_executor = concurrent.futures.ThreadPoolExecutor(max_workers=4)
JOBS: Dict[str, concurrent.futures.Future] = {}

def register_bot(name: str, bot_instance: object):
    BOTS[name] = bot_instance
    logger.info(f"Registered bot: {name}")

def run_bot(name: str, **kwargs) -> Dict[str, Any]:
    bot = BOTS.get(name)
    if not bot:
        raise ValueError(f"Bot '{name}' not found")
    logger.info(f"Dispatch bot {name} with kwargs={kwargs}")
    # submit to threadpool so FastAPI threads remain responsive
    job_id = str(uuid.uuid4())
    future = _executor.submit(_run_wrapper, job_id, bot, kwargs)
    JOBS[job_id] = future
    return {"submitted": True, "bot": name, "job_id": job_id}

def _run_wrapper(job_id: str, bot, kwargs):
    logger.info(f"Job {job_id} started for bot {bot.__class__.__name__}")
    try:
        res = bot.run(**kwargs)
        logger.info(f"Job {job_id} finished: {res}")
        return {"job_id": job_id, "result": res, "status": "finished"}
    except Exception as e:
        logger.exception(f"Job {job_id} failed: {e}")
        return {"job_id": job_id, "error": str(e), "status": "error"}

def job_status(job_id: str) -> Dict[str, Any]:
    future = JOBS.get(job_id)
    if not future:
        return {"job_id": job_id, "status": "not_found"}
    if future.running():
        return {"job_id": job_id, "status": "running"}
    if future.done():
        res = future.result()
        return {"job_id": job_id, "status": "done", "result": res}
    return {"job_id": job_id, "status": "pending"}
