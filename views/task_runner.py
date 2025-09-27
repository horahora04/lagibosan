from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from backend_login_checker import LoginChecker
from backend_chat_scraper import ChatScraper
# import class lain sesuai kebutuhan...

templates = Jinja2Templates(directory="templates")
router = APIRouter()

TOOLS = {
    "login_checker": LoginChecker,
    "chat_scraper": ChatScraper,
    # Tambah sesuai nama tool
}

@router.get("/run-checker", response_class=HTMLResponse)
async def run_checker(request: Request, tool: str = "login_checker"):
    log_list = []

    def log_callback(msg, end='\n'):
        log_list.append(msg + end)

    if tool in TOOLS:
        instance = TOOLS[tool](log_callback=log_callback, multiple_thread=1)
        instance.stop_event.set()  # atau panggil fungsi sesuai class
    else:
        log_list.append("❌ Tool tidak ditemukan.")

    return templates.TemplateResponse("log_output.html", {"request": request, "logs": log_list})
