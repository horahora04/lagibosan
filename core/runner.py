# core/runner.py
from typing import Dict, Any
from core.logger import get_logger
import concurrent.futures
import uuid
import atexit

logger = get_logger("runner")

# registry bot dan job
BOTS: Dict[str, object] = {}
_executor = concurrent.futures.ThreadPoolExecutor(max_workers=4)
JOBS: Dict[str, concurrent.futures.Future] = {}


def register_bot(name: str, bot_instance: object):
    """Daftarkan bot ke registry"""
    BOTS[name] = bot_instance
    logger.info(f"Registered bot: {name}")


def run_bot(name: str, **kwargs) -> Dict[str, Any]:
    """Submit bot untuk dieksekusi di threadpool"""
    bot = BOTS.get(name)
    if not bot:
        raise ValueError(f"Bot '{name}' not found")
    logger.info(f"Dispatch bot {name} with kwargs={kwargs}")
    job_id = str(uuid.uuid4())
    future = _executor.submit(_run_wrapper, job_id, bot, kwargs)
    JOBS[job_id] = future
    return {"submitted": True, "bot": name, "job_id": job_id}


def _run_wrapper(job_id: str, bot, kwargs):
    """Wrapper supaya log job dan error tertangkap"""
    logger.info(f"Job {job_id} started for bot {bot.__class__.__name__}")
    try:
        res = bot.run(**kwargs)
        logger.info(f"Job {job_id} finished: {res}")
        return {"job_id": job_id, "result": res, "status": "finished"}
    except Exception as e:
        logger.exception(f"Job {job_id} failed: {e}")
        return {"job_id": job_id, "error": str(e), "status": "error"}


def job_status(job_id: str) -> Dict[str, Any]:
    """Cek status job berdasarkan job_id"""
    future = JOBS.get(job_id)
    if not future:
        return {"job_id": job_id, "status": "not_found"}
    if future.running():
        return {"job_id": job_id, "status": "running"}
    if future.done():
        res = future.result()
        return {"job_id": job_id, "status": "done", "result": res}
    return {"job_id": job_id, "status": "pending"}


def shutdown_all():
    """
    Stop semua bot ter-registrasi (panggil stop() kalau ada).
    Khusus bot 'scrape' → paksa disable_proxy juga.
    """
    logger.info("Runner: shutdown_all() called — attempting to stop all bots")
    for name, bot in BOTS.items():
        try:
            if hasattr(bot, "stop") and callable(getattr(bot, "stop")):
                logger.info(f"Runner: stopping bot '{name}' via stop()")
                try:
                    bot.stop()
                except Exception as e:
                    logger.exception(f"Runner: error while stopping bot '{name}': {e}")
            else:
                logger.info(f"Runner: bot '{name}' tidak punya stop() method — skip")

            # --- Tambahan khusus scraper ---
            if name == "scrape":
                try:
                    from modules.scrape.backend.scraper import Scraper
                    Scraper().disable_proxy()
                    logger.info("Runner: forced disable_proxy() executed")
                except Exception as e:
                    logger.warning(f"Runner: force disable_proxy failed: {e}")

        except Exception as e:
            logger.exception(f"Runner: unexpected error when shutting down bot '{name}': {e}")


# Pastikan shutdown_all selalu dipanggil walau app crash/CTRL+C
@atexit.register
def _on_exit():
    try:
        shutdown_all()
    except Exception as e:
        logger.error(f"atexit shutdown_all error: {e}")
