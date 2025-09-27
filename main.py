from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import os

app = FastAPI()

# ✅ CORS agar bisa diakses dari Shopee (https://shopee.co.id)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # bisa dipersempit ["https://shopee.co.id"]
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ✅ Register router scraping
from routes import scrape
app.include_router(scrape.router)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATES_DIR = os.path.join(BASE_DIR, "templates")
STATIC_DIR = os.path.join(BASE_DIR, "static")

templates = Jinja2Templates(directory=TEMPLATES_DIR)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/scrape", response_class=HTMLResponse)
async def scrape_page(request: Request):
    return templates.TemplateResponse("scrape.html", {"request": request})
