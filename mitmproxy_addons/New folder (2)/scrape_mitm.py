# mitmproxy_addons/scrape_mitm.py
from mitmproxy import http
import json
from datetime import datetime
from pathlib import Path
from pymongo import MongoClient
from colorama import Fore, Style, init

# Inisialisasi colorama (untuk output console)
init(autoreset=True)

# 📂 Path file output
BASE_DIR = Path(__file__).resolve().parent.parent
DOWNLOADS_PATH = BASE_DIR / "Downloads"
URLS_FILE = DOWNLOADS_PATH / "Urls.txt"
LOG_FILE = DOWNLOADS_PATH / "ScraperLog.txt"

# Pastikan folder ada
DOWNLOADS_PATH.mkdir(exist_ok=True)

# 🔧 MongoDB
client = MongoClient("mongodb://localhost:27017/")
db = client["shopee_db"]
collection = db["products"]

def log_line(text: str):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"[{ts}] {text}\n")

def write_urls(urls: list[str]):
    try:
        with open(URLS_FILE, "w", encoding="utf-8") as f:
            f.write("\n".join(urls))
    except Exception as e:
        log_line(f"❌ Gagal menulis Urls.txt: {e}")

def response(flow: http.HTTPFlow):
    try:
        url = flow.request.url

        # 🎯 1) Tangkap list produk (search_items)
        if url.startswith("https://shopee.co.id/api/v4/search/search_items"):
            try:
                data = json.loads(flow.response.text)
                items = data.get("items", [])
                if not items:
                    log_line("⚠️ Tidak ada items pada search_items.")
                    return

                urls = []
                for it in items:
                    model = it.get("item_basic", {})
                    name = model.get("name")
                    shopid = model.get("shopid")
                    itemid = model.get("itemid")
                    if not (name and shopid and itemid):
                        continue
                    slug = name.replace(" ", "-")
                    product_url = f"https://shopee.co.id/{slug}-i.{shopid}.{itemid}"
                    urls.append(product_url)
                    print(f"[Grab URL]: {product_url}")  # penting untuk backend_scrape

                if urls:
                    write_urls(urls)
                    log_line(f"✅ {len(urls)} URL produk ditulis ke Urls.txt")

            except Exception as e:
                log_line(f"❌ Error parsing search_items: {e}")

        # 🎯 2) Tangkap detail produk (pdp/get_pc)
        elif url.startswith("https://shopee.co.id/api/v4/pdp/get_pc"):
            try:
                data = json.loads(flow.response.text)
                item = data.get("data", {}).get("item", {})
                if not item:
                    return

                name = item.get("title")
                shop_id = item.get("shop_id")
                item_id = item.get("item_id")
                if not (name and shop_id and item_id):
                    return

                slug = name.replace(" ", "-")
                detail_url = f"https://shopee.co.id/{slug}-i.{shop_id}.{item_id}"

                # Simpan ke MongoDB
                try:
                    collection.replace_one({"_id": detail_url}, {
                        "_id": detail_url,
                        "title": name,
                        "description": item.get("description", ""),
                        "price_max": item.get("price_max"),
                        "images": item.get("images", []),
                        "categories": [c.get("display_name") for c in item.get("categories", [])],
                        "created_at": datetime.now()
                    }, upsert=True)
                except Exception as db_e:
                    log_line(f"⚠️ Gagal menyimpan MongoDB: {db_e}")

                log_line(f"ℹ️ Detail produk: {detail_url}")
                print(f"[Grab URL]: {detail_url}")

            except Exception as e:
                log_line(f"❌ Error parsing detail produk: {e}")

    except Exception as e:
        log_line(f"❌ Gagal memproses flow: {e}")
