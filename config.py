import os
from pydantic import BaseModel, Field, ValidationError

class Settings(BaseModel):
    BOT_TOKEN: str = Field(..., description="Telegram Bot token")
    TELEGRAM_CHAT_ID: str = Field(..., description="Chat ID để nhận báo cáo")
    TIMEZONE: str = "Asia/Ho_Chi_Minh"

    WALLETS_FILE: str = "wallets.txt"     # fallback nếu không dùng env
    WALLETS_TEXT_ENV: str = "WALLETS_TEXT" # dùng Secrets của Replit
    AIRDROPS_FILE: str = "airdrops.json"

    BATCH_WALLETS: int = 50           # tối đa ví xử lý / chu kỳ
    LOOP_MINUTES: int = 30            # mỗi 30’ chạy 1 vòng
    TELEGRAM_SILENT: bool = False     # True = báo cáo ít

def load_settings() -> Settings:
    try:
        return Settings(
            BOT_TOKEN=os.getenv("BOT_TOKEN"),
            TELEGRAM_CHAT_ID=os.getenv("TELEGRAM_CHAT_ID"),
            TIMEZONE=os.getenv("TIMEZONE", "Asia/Ho_Chi_Minh"),
        )
    except ValidationError as e:
        raise RuntimeError(
            "❌ Thiếu BOT_TOKEN hoặc TELEGRAM_CHAT_ID trong môi trường!"
        ) from e

SETTINGS = load_settings()
