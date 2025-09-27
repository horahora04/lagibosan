# modules/scrape/services/db_service.py
from pymongo import MongoClient, errors
from datetime import datetime
import time
from core.logger import get_logger

logger = get_logger("db_service")

# --- Konfigurasi ---
MONGO_URI = "mongodb://localhost:27017/"
DB_NAME = "shopee_db"

# --- Global client ---
_client = None
_db = None


def get_db():
    """
    Pastikan koneksi Mongo aktif.
    Kalau belum ada atau sudah putus, buat ulang client.
    """
    global _client, _db
    if _client is None:
        try:
            _client = MongoClient(
                MONGO_URI,
                serverSelectionTimeoutMS=5000,  # cepat gagal kalau server mati
                socketTimeoutMS=60000,          # timeout socket
            )
            _client.server_info()  # test koneksi
            _db = _client[DB_NAME]
            logger.info("✅ MongoDB connected")
        except errors.ServerSelectionTimeoutError as e:
            logger.error(f"❌ MongoDB connection failed: {e}")
            raise
    return _db


def save_product(data: dict, collection: str = "products", retries: int = 3, delay: float = 1.0):
    """
    Simpan produk ke MongoDB dengan retry.
    Upsert berdasarkan _id (product_url).
    """
    db = get_db()
    col = db[collection]

    # Tambahkan timestamp
    now = datetime.now()
    data["updated_at"] = now
    if "created_at" not in data:  # hanya set sekali
        data["created_at"] = now

    for attempt in range(1, retries + 1):
        try:
            col.replace_one({"_id": data["_id"]}, data, upsert=True)
            logger.info(f"💾 Produk disimpan: {data['_id']}")
            return {"ok": True, "_id": data["_id"]}
        except errors.PyMongoError as e:
            logger.warning(f"⚠️ Gagal simpan produk (attempt {attempt}): {e}")
            time.sleep(delay)
            # Reset client agar next attempt reconnect
            global _client, _db
            _client = None
            _db = None

    return {"ok": False, "_id": data.get("_id")}


def get_products(filter_query: dict = None, limit: int = 50, collection: str = "products") -> list:
    """
    Ambil produk dari MongoDB.
    Gunakan list() agar cursor tidak timeout.
    """
    db = get_db()
    col = db[collection]
    try:
        cursor = col.find(filter_query or {}).sort("updated_at", -1).limit(limit)
        return list(cursor)
    except errors.PyMongoError as e:
        logger.error(f"❌ Gagal ambil produk: {e}")
        return []
