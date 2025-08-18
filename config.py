# config.py
import os
from pydantic import BaseModel, Field, ValidationError
from dotenv import load_dotenv

# Load biến môi trường từ .env (Replit/GitHub Secrets cũng vào được qua os.getenv)
load_dotenv()


class Settings(BaseModel):
    # Báo cáo Telegram
    BOT_TOKEN: str = Field(default="", description="Telegram Bot token")
    TELEGRAM_CHAT_ID: str = Field(default="", description="Chat ID nhận báo cáo")

    # Lịch & song song
    TIMEZONE: str = Field(default="Asia/Ho_Chi_Minh", description="Múi giờ chạy bot")
    MAX_CONCURRENCY: int = Field(default=50, description="Số tác vụ chạy song song tối đa")

    # Sweep (gom coin)
    RPC_URL: str = Field(default="", description="RPC URL của chain (ví dụ Sepolia/Polygon/BNB…) ")
    MASTER_WALLET: str = Field(default="", description="Địa chỉ ví mẹ để gom coin")

    # Tuỳ chọn phí & token
    GAS_PRICE_GWEI: int = Field(default=2, description="Gas price mặc định (GWEI)")
    ERC20_TOKEN: str = Field(default="", description="Contract ERC-20 nếu sweep token thay vì native")


def _coerce_int(env_key: str, default: int) -> int:
    try:
        return int(os.getenv(env_key, str(default)))
    except ValueError:
        return default


try:
    settings = Settings(
        BOT_TOKEN=os.getenv("BOT_TOKEN", ""),
        TELEGRAM_CHAT_ID=os.getenv("TELEGRAM_CHAT_ID", ""),
        TIMEZONE=os.getenv("TIMEZONE", "Asia/Ho_Chi_Minh"),
        MAX_CONCURRENCY=_coerce_int("MAX_CONCURRENCY", 50),
        RPC_URL=os.getenv("RPC_URL", ""),
        MASTER_WALLET=os.getenv("MASTER_WALLET", ""),
        GAS_PRICE_GWEI=_coerce_int("GAS_PRICE_GWEI", 2),
        ERC20_TOKEN=os.getenv("ERC20_TOKEN", ""),
    )
except ValidationError as e:
    raise RuntimeError(f"Config error: {e}")


# Xuất hằng số dùng ở các module khác
BOT_TOKEN: str = settings.BOT_TOKEN
TELEGRAM_CHAT_ID: str = settings.TELEGRAM_CHAT_ID
TIMEZONE: str = settings.TIMEZONE
MAX_CONCURRENCY: int = settings.MAX_CONCURRENCY

RPC_URL: str = settings.RPC_URL
MASTER_WALLET: str = settings.MASTER_WALLET
GAS_PRICE_GWEI: int = settings.GAS_PRICE_GWEI
ERC20_TOKEN: str = settings.ERC20_TOKEN


def validate_required_for_runtime(mode: str = "main") -> None:
    """
    Gọi hàm này ở đầu chương trình để đảm bảo đủ biến môi trường tối thiểu.
    mode="main"  -> yêu cầu Telegram (để báo cáo)
    mode="sweep" -> yêu cầu RPC_URL + MASTER_WALLET (gom coin)
    """
    if mode == "main":
        if not BOT_TOKEN or not TELEGRAM_CHAT_ID:
            raise RuntimeError("Thiếu BOT_TOKEN hoặc TELEGRAM_CHAT_ID trong Secrets/Environment.")
    if mode == "sweep":
        if not RPC_URL or not MASTER_WALLET:
            raise RuntimeError("Thiếu RPC_URL hoặc MASTER_WALLET trong Secrets/Environment.")


__all__ = [
    "BOT_TOKEN",
    "TELEGRAM_CHAT_ID",
    "TIMEZONE",
    "MAX_CONCURRENCY",
    "RPC_URL",
    "MASTER_WALLET",
    "GAS_PRICE_GWEI",
    "ERC20_TOKEN",
    "validate_required_for_runtime",
]
