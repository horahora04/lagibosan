# modules/scrape/backend/scraper.py
import threading
import subprocess
import shutil
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any

from core.logger import get_logger
from modules.scrape.services.scraper_service import (
    save_log, set_status, get_status, insert_record_sync
)

logger = get_logger("Scraper")

class Scraper:
    name = "scrape"

    def __init__(self, mitm_addon_path: Optional[Path] = None, proxy_ip: str = "127.0.0.1", proxy_port: int = 8080):
        # mitm addon path (if None, try default location relative to project)
        self.BASE_DIR = Path(__file__).resolve().parents[2]  # project_root/modules/scrape/backend -> up 2
        #self.MITM_ADDON_PATH = Path(mitm_addon_path) if mitm_addon_path else (self.BASE_DIR / "backend" / "scrape_mitm.py")
        self.MITM_ADDON_PATH = Path(mitm_addon_path) if mitm_addon_path else (self.BASE_DIR / "scrape" / "backend" / "scrape_mitm.py")
        self.PROXY_IP = proxy_ip
        self.PROXY_PORT = proxy_port

        self._proc: Optional[subprocess.Popen] = None
        self._reader_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()

    # ------------ proxy control (Windows) --------------
    def enable_proxy(self):
        """Enable system proxy on Windows via registry. Requires appropriate privileges."""
        try:
            subprocess.run([
                "reg", "add", r"HKCU\Software\Microsoft\Windows\CurrentVersion\Internet Settings",
                "/v", "ProxyEnable", "/t", "REG_DWORD", "/d", "1", "/f"
            ], shell=True, check=True)
            subprocess.run([
                "reg", "add", r"HKCU\Software\Microsoft\Windows\CurrentVersion\Internet Settings",
                "/v", "ProxyServer", "/t", "REG_SZ", "/d", f"{self.PROXY_IP}:{self.PROXY_PORT}", "/f"
            ], shell=True, check=True)
        except Exception as e:
            logger.exception("enable_proxy failed: %s", e)
            raise

    def disable_proxy(self):
        try:
            subprocess.run([
                "reg", "add", r"HKCU\Software\Microsoft\Windows\CurrentVersion\Internet Settings",
                "/v", "ProxyEnable", "/t", "REG_DWORD", "/d", "0", "/f"
            ], shell=True, check=True)
        except Exception as e:
            logger.exception("disable_proxy failed: %s", e)

    # ------------ mitmdump reader --------------
    def _reader(self, proc: subprocess.Popen):
        """Read stdout line by line and log URLs"""
        try:
            for raw in proc.stdout:
                if not raw:
                    continue
                line = raw.strip()
                if "[Grab URL]:" in line:
                    url = line.split("[Grab URL]:")[-1].strip()
                    ts = datetime.now().strftime("%H:%M:%S")
                    log_line = f"[{ts}] ✅ URL Ditangkap: {url}"
                    logger.info(log_line)
                    save_log(log_line)
            # wait for process to exit
            proc.stdout.close()
            proc.wait()
        except Exception as e:
            logger.exception("reader thread error: %s", e)

    # ------------ start / stop / status --------------
    def start(self) -> Dict[str, Any]:
        """Start mitmdump and proxy. Returns basic metadata."""
        # Stop any existing
        self.stop()

        # reset status
        set_status("starting")

        # rotate log if too big
        if self.MITM_ADDON_PATH.exists() is False:
            raise RuntimeError(f"Mitm addon not found: {self.MITM_ADDON_PATH}")

        # find mitmdump bin
        mitmdump_bin = shutil.which("mitmdump")
        if not mitmdump_bin:
            set_status("error")
            raise RuntimeError("mitmdump not found in PATH")

        # Optionally clear large logs
        try:
            log_file = Path(self.BASE_DIR) / "Downloads" / "ScraperLog.txt"
            if log_file.exists() and log_file.stat().st_size > 5 * 1024 * 1024:
                log_file.write_text("", encoding="utf-8")
        except Exception:
            pass

        # enable system proxy (Windows) — may raise if lacks privilege
        try:
            self.enable_proxy()
        except Exception:
            # still try to start mitmdump, but warn
            logger.warning("Proceeding without proxy changes (enable_proxy failed)")

        # start process
        cmd = [mitmdump_bin, "-s", str(self.MITM_ADDON_PATH), "--set", "http2=false"]
        try:
            # creationflags only available on Windows; if not, ignore
            creationflags = subprocess.CREATE_NO_WINDOW if hasattr(subprocess, "CREATE_NO_WINDOW") else 0
            self._proc = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                creationflags=creationflags
            )
        except Exception as e:
            set_status("error")
            logger.exception("Failed to start mitmdump: %s", e)
            raise

        # start reader thread
        self._reader_thread = threading.Thread(target=self._reader, args=(self._proc,), daemon=True)
        self._reader_thread.start()

        set_status("running")
        return {"status": "running"}

    def stop(self) -> Dict[str, Any]:
        """Stop mitmdump and disable proxy."""
        if self._proc and self._proc.poll() is None:
            try:
                self._proc.terminate()
                try:
                    self._proc.wait(timeout=3)
                except subprocess.TimeoutExpired:
                    self._proc.kill()
            except Exception:
                logger.exception("Error stopping mitmdump process")
        self._proc = None
        # disable proxy (best-effort)
        try:
            self.disable_proxy()
        except Exception:
            logger.exception("disable_proxy failed")
        set_status("stopped")
        return {"status": "stopped"}

    def status(self) -> Dict[str, Any]:
        return {"status": get_status()}

    # compatibility: run() used by runner
    def run(self, action: str = "start", **kwargs) -> Dict[str, Any]:
        """
        action: "start" | "stop" | "status"
        For start, accept optional 'url' param but scraping is performed by mitm + extension.
        """
        if action == "start":
            return self.start()
        elif action == "stop":
            return self.stop()
        elif action == "status":
            return self.status()
        else:
            raise ValueError("Unknown action: " + str(action))
