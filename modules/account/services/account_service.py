from core.db import get_db
from passlib.context import CryptContext

pwd = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_pw(pw: str) -> str:
    return pwd.hash(pw)

def create_user_sync(email: str, password: str):
    db = get_db()
    doc = {"email": email, "password": hash_pw(password)}
    res = db.accounts.insert_one(doc)
    return str(res.inserted_id)

def find_user_by_email(email: str):
    db = get_db()
    return db.accounts.find_one({"email": email})
