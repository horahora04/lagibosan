from pathlib import Path
import os

ROOT = Path(__file__).resolve().parents[1]  # project_root/core -> up 1
# Bisa override via ENV var
DOWNLOADS_DIR = Path(os.getenv("DOWNLOADS_DIR", ROOT / "Downloads"))

# Useful subfolders
LOGS_DIR = DOWNLOADS_DIR / "logs"
SCRAPE_DIR = DOWNLOADS_DIR / "scrape"

# ensure dirs exist
for d in (DOWNLOADS_DIR, LOGS_DIR, SCRAPE_DIR):
    d.mkdir(parents=True, exist_ok=True)
