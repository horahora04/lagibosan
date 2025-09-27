from fastapi import APIRouter
from core.runner import run_bot, register_bot
from modules.account.backend.account_bot import AccountBot
from modules.account.services.account_service import find_user_by_email

router = APIRouter(prefix="/account", tags=["account"])
register_bot("account", AccountBot())

@router.post("/create")
def create(email: str, password: str = "pass"):
    return run_bot("account", email=email, password=password)

@router.get("/get")
def get_user(email: str):
    return {"user": find_user_by_email(email)}
