# main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import scrape, monitor, account
from core import runner

app = FastAPI(title="Lagibosan API (full-api)", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # change to specific origin in production
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(scrape)
app.include_router(monitor)
app.include_router(account)

@app.get("/")
def root():
    return {"message": "Lagibosan API (full-api)", "endpoints": ["/scrape", "/monitor", "/account"]}

# ----------------- shutdown hook -----------------
@app.on_event("shutdown")
def _shutdown():
    """
    Dipanggil saat uvicorn/FastAPI proses berhenti (Ctrl+C, kill, atau graceful shutdown).
    Kita stop semua bot ter-registrasi supaya mitmdump & proxy dimatikan.
    """
    try:
        runner.shutdown_all()
    except Exception as e:
        # Jangan crash di shutdown hook; hanya log
        print("Error while shutting down bots:", e)
