# backend/backend_scrape.py
import subprocess, os, json, shutil, threading, atexit
from datetime import datetime
from pathlib import Path

# 📂 Path & Konfigurasi
BASE_DIR = Path(__file__).resolve().parent.parent
DOWNLOADS_PATH = BASE_DIR / "Downloads"
SCRAPER_STATUS_FILE = DOWNLOADS_PATH / "scraper_status.json"
MITM_ADDON_PATH = BASE_DIR / "mitmproxy_addons" / "scrape_mitm.py"
LOG_FILE = DOWNLOADS_PATH / "ScraperLog.txt"
URLS_FILE = DOWNLOADS_PATH / "Urls.txt"

PROXY_IP = "127.0.0.1"
PROXY_PORT = 8080

# Global untuk proses mitmdump
mitmdump_process = None

# Pastikan folder & file tersedia
DOWNLOADS_PATH.mkdir(exist_ok=True)
for f in [LOG_FILE, URLS_FILE]:
    if not f.exists():
        f.write_text("", encoding="utf-8")
SCRAPER_STATUS_FILE.write_text(json.dumps({"status": "stopped"}), encoding="utf-8")


# ================= Helper =================
def set_status(status: str):
    SCRAPER_STATUS_FILE.write_text(json.dumps({"status": status}), encoding="utf-8")


def get_status() -> str:
    if SCRAPER_STATUS_FILE.exists():
        return json.loads(SCRAPER_STATUS_FILE.read_text()).get("status", "stopped")
    return "stopped"


def read_file(file_name: str) -> str:
    fpath = DOWNLOADS_PATH / file_name
    if not fpath.exists():
        raise FileNotFoundError(f"File {file_name} tidak ditemukan.")
    return fpath.read_text(encoding="utf-8")


def append_file(file_name: str, line: str):
    fpath = DOWNLOADS_PATH / file_name
    with open(fpath, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def clear_file(file_name: str):
    (DOWNLOADS_PATH / file_name).write_text("", encoding="utf-8")


# ================= Proxy Control =================
def enable_proxy():
    subprocess.run([
        "reg", "add", r"HKCU\Software\Microsoft\Windows\CurrentVersion\Internet Settings",
        "/v", "ProxyEnable", "/t", "REG_DWORD", "/d", "1", "/f"
    ], shell=True)
    subprocess.run([
        "reg", "add", r"HKCU\Software\Microsoft\Windows\CurrentVersion\Internet Settings",
        "/v", "ProxyServer", "/t", "REG_SZ", "/d", f"{PROXY_IP}:{PROXY_PORT}", "/f"
    ], shell=True)


def disable_proxy():
    subprocess.run([
        "reg", "add", r"HKCU\Software\Microsoft\Windows\CurrentVersion\Internet Settings",
        "/v", "ProxyEnable", "/t", "REG_DWORD", "/d", "0", "/f"
    ], shell=True)


def kill_mitmdump():
    try:
        result = subprocess.run("tasklist", capture_output=True, text=True, shell=True)
        for line in result.stdout.splitlines():
            if "mitmdump.exe" in line:
                pid = line.split()[1]
                subprocess.run(f"taskkill /PID {pid} /F", shell=True)
    except:
        pass


# ================= Mitmproxy Control =================
def start_scraper():
    """
    Jalankan mitmdump di thread terpisah + baca stdout baris demi baris.
    Tidak lagi menghapus Urls.txt dan ScraperLog.txt agar sinkron dengan ekstensi.
    """
    global mitmdump_process
    stop_scraper()
    enable_proxy()

    # Optional: reset log jika terlalu besar (>5MB)
    if LOG_FILE.exists() and LOG_FILE.stat().st_size > 5 * 1024 * 1024:
        LOG_FILE.write_text("", encoding="utf-8")

    mitmdump_bin = shutil.which("mitmdump")
    if not mitmdump_bin:
        raise RuntimeError("mitmdump tidak ditemukan di PATH")

    def reader_thread(proc: subprocess.Popen):
        for line in proc.stdout:
            if "[Grab URL]:" in line:
                url = line.split("[Grab URL]:")[-1].strip()
                ts = datetime.now().strftime("%H:%M:%S")
                log_line = f"[{ts}] ✅ URL Ditangkap: {url}"
                print(log_line)
                with open(LOG_FILE, "a", encoding="utf-8") as f:
                    f.write(log_line + "\n")
        proc.stdout.close()
        proc.wait()

    mitmdump_process = subprocess.Popen(
        [mitmdump_bin, "-s", str(MITM_ADDON_PATH), "--set", "http2=false"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
        creationflags=subprocess.CREATE_NO_WINDOW
    )

    threading.Thread(target=reader_thread, args=(mitmdump_process,), daemon=True).start()
    set_status("running")


def stop_scraper():
    """Hentikan mitmdump dan matikan proxy"""
    global mitmdump_process
    if mitmdump_process and mitmdump_process.poll() is None:
        mitmdump_process.terminate()
        try:
            mitmdump_process.wait(timeout=3)
        except subprocess.TimeoutExpired:
            mitmdump_process.kill()
    mitmdump_process = None
    disable_proxy()
    set_status("stopped")


# Pastikan proxy dimatikan saat aplikasi ditutup
@atexit.register
def cleanup_on_exit():
    stop_scraper()
