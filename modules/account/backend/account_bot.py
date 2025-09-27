from core.logger import get_logger
from modules.account.services.account_service import create_user_sync
logger = get_logger("AccountBot")

class AccountBot:
    name = "account"

    def run(self, email: str, password: str = "pass"):
        logger.info(f"[Account] create {email}")
        uid = create_user_sync(email, password)
        return {"status": "created", "id": uid}
