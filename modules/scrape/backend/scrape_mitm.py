from mitmproxy import http
from pathlib import Path
from datetime import datetime
import json
from modules.scrape.services.db_scrape import save_product  # pakai service
from core.config import SCRAPE_DIR, LOGS_DIR

DEBUG_LOG = LOGS_DIR / "mitm_debug.log"
URLS_FILE = SCRAPE_DIR / "Urls.txt"

# ====== Helper ======
def debug_log(message: str):
    ts = datetime.now().strftime("%H:%M:%S")
    with open(DEBUG_LOG, "a", encoding="utf-8") as f:
        f.write(f"[{ts}] {message}\n")

def write_urls(urls: list[str]):
    try:
        with open(URLS_FILE, "w", encoding="utf-8") as f:
            f.write("\n".join(urls))
        debug_log(f"✅ Menulis {len(urls)} URL ke Urls.txt")
    except Exception as e:
        debug_log(f"❌ Gagal menulis Urls.txt: {e}")


# ====== Mitmproxy Response Handler ======
def response(flow: http.HTTPFlow):
    url = flow.request.url
    try:
        # === 1) Tangkap list produk dari Terlaris ===
        if url.startswith("https://shopee.co.id/api/v4/search/search_items"):
            debug_log(f"[DEBUG] Menerima response search_items (len={len(flow.response.content)}B)")
            try:
                data = json.loads(flow.response.text)
                items = data.get("items", [])
                urls = []
                for it in items:
                    model = it.get("item_basic", {})
                    name = model.get("name")
                    shopid = model.get("shopid")
                    itemid = model.get("itemid")
                    if name and shopid and itemid:
                        slug = name.replace(" ", "-")
                        urls.append(f"https://shopee.co.id/{slug}-i.{shopid}.{itemid}")
                if urls:
                    write_urls(urls)
                else:
                    debug_log("⚠️ Tidak ada item ditemukan di search_items")
            except json.JSONDecodeError as e:
                debug_log(f"❌ JSONDecodeError search_items: {e}")

        # === 2) Tangkap list produk dari Popular ===
        elif url.startswith("https://shopee.co.id/api/v4/recommend/recommend_v2"):
            debug_log(f"[DEBUG] Menerima response recommend_v2")
            try:
                data = json.loads(flow.response.text)
                units = data.get("data", {}).get("units", [])
                urls = []
                for unit in units:
                    item = unit.get("item", {})
                    card = item.get("item_card_displayed_asset", {})
                    item_data = item.get("item_data", {})
                    name = card.get("name")
                    shopid = item_data.get("shopid")
                    itemid = item_data.get("itemid")
                    if name and shopid and itemid:
                        slug = name.replace(" ", "-")
                        product_url = f"https://shopee.co.id/{slug}-i.{shopid}.{itemid}"
                        urls.append(product_url)
                        # Simpan ringkas ke DB
                        product_data = {
                            "_id": product_url,
                            "title": name,
                            "price_max": item_data.get("item_card_display_price", {}).get("price"),
                            "images": card.get("images", []),
                            "created_at": datetime.now()
                        }
                        save_product(product_data)
                if urls:
                    write_urls(urls)
                else:
                    debug_log("⚠️ Tidak ada unit ditemukan di recommend_v2")
            except json.JSONDecodeError as e:
                debug_log(f"❌ JSONDecodeError recommend_v2: {e}")

        # === 3) Tangkap detail produk ===
        elif url.startswith("https://shopee.co.id/api/v4/pdp/get_pc"):
            debug_log(f"[DEBUG] Menerima response get_pc")
            try:
                data = json.loads(flow.response.text)
                item = data.get("data", {}).get("item")
                if item:
                    title = item.get("title")
                    shop_id = item.get("shop_id")
                    item_id = item.get("item_id")
                    if title and shop_id and item_id:
                        slug = title.replace(" ", "-")
                        product_url = f"https://shopee.co.id/{slug}-i.{shop_id}.{item_id}"
                        product_data = {
                            "_id": product_url,
                            "title": title,
                            "description": item.get("description"),
                            "price_max": item.get("price_max", 0),
                            "images": item.get("images", []),
                            "categories": [c.get("display_name") for c in item.get("categories", [])],
                            "created_at": datetime.now()
                        }
                        save_product(product_data)
            except json.JSONDecodeError as e:
                debug_log(f"❌ JSONDecodeError get_pc: {e}")

    except Exception as e:
        debug_log(f"❌ Gagal memproses flow: {e}")
