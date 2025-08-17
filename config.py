import os
from pydantic import BaseModel, Field, ValidationError

class Settings(BaseModel):
    BOT_TOKEN: str = Field(..., description="Telegram Bot token (BotFather)")
    TELEGRAM_CHAT_ID: str = Field(..., description="Chat ID để nhận báo cáo")
    TIMEZONE: str = "Asia/Ho_Chi_Minh"

    WALLETS_FILE: str = "wallets.txt"   # file chứa 1500 ví (mỗi dòng 1 private key / seed)
    AIRDROPS_FILE: str = "airdrops.json"

    BATCH_SIZE: int = 50               # xử lý bao nhiêu ví mỗi lượt
    REQUESTS_PER_MIN: int = 20         # rate limit an toàn

def load_settings() -> "Settings":
    try:
        return Settings(
            BOT_TOKEN=os.getenv("BOT_TOKEN", "").strip(),
            TELEGRAM_CHAT_ID=os.getenv("TELEGRAM_CHAT_ID", "").strip(),
            TIMEZONE=os.getenv("TIMEZONE", "Asia/Ho_Chi_Minh").strip(),
            WALLETS_FILE=os.getenv("WALLETS_FILE", "wallets.txt").strip(),
            AIRDROPS_FILE=os.getenv("AIRDROPS_FILE", "airdrops.json").strip(),
            BATCH_SIZE=int(os.getenv("BATCH_SIZE", "50")),
            REQUESTS_PER_MIN=int(os.getenv("REQUESTS_PER_MIN", "20")),
        )
    except ValidationError as e:
        raise RuntimeError(f"[CONFIG] Lỗi cấu hình: {e}") from e
