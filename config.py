import os
from pydantic import BaseModel, Field, ValidationError
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseModel):
    BOT_TOKEN: str = Field(default="", description="Telegram Bot token")
    TELEGRAM_CHAT_ID: str = Field(default="", description="Telegram chat id để nhận báo cáo")
    TIMEZONE: str = Field(default="Asia/Ho_Chi_Minh", description="Múi giờ")
    MAX_CONCURRENCY: int = Field(default=50, description="Số tác vụ chạy song song tối đa")

try:
    settings = Settings(
        BOT_TOKEN=os.getenv("BOT_TOKEN", ""),
        TELEGRAM_CHAT_ID=os.getenv("TELEGRAM_CHAT_ID", ""),
        TIMEZONE=os.getenv("TIMEZONE", "Asia/Ho_Chi_Minh"),
        MAX_CONCURRENCY=int(os.getenv("MAX_CONCURRENCY", "50")),
    )
except ValidationError as e:
    raise RuntimeError(f"Config error: {e}")

BOT_TOKEN = settings.BOT_TOKEN
TELEGRAM_CHAT_ID = settings.TELEGRAM_CHAT_ID
TIMEZONE = settings.TIMEZONE
MAX_CONCURRENCY = settings.MAX_CONCURRENCY
