import os
import json
import asyncio
import logging
from datetime import datetime
from typing import List, Dict, Any

import httpx
from apscheduler.schedulers.asyncio import AsyncIOScheduler

# --- import theo dự án bạn đang có ---
from config import BOT_TOKEN, TELEGRAM_CHAT_ID, TIMEZONE, MAX_CONCURRENCY
from wallet_loader import load_wallets
from faucet import run_airdrop
# --------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)

TELEGRAM_API = "https://api.telegram.org"

# ========= helper =========
def chunk(text: str, size: int = 3500) -> List[str]:
    return [text[i:i+size] for i in range(0, len(text), size)]

async def send_telegram(text: str, parse_mode: str | None = None):
    """Gửi tin nhắn Telegram, tự chia nhỏ nếu quá dài."""
    if not BOT_TOKEN or not TELEGRAM_CHAT_ID:
        logging.warning("Thiếu BOT_TOKEN/TELEGRAM_CHAT_ID → bỏ qua gửi Telegram.")
        return
    url = f"{TELEGRAM_API}/bot{BOT_TOKEN}/sendMessage"
    async with httpx.AsyncClient(timeout=20) as client:
        for part in chunk(text, 3500):
            data = {"chat_id": TELEGRAM_CHAT_ID, "text": part}
            if parse_mode:
                data["parse_mode"] = parse_mode
            try:
                await client.post(url, data=data)
            except Exception as e:
                logging.error(f"send_telegram error: {e}")

def load_airdrops(path: str = "airdrops.json") -> List[Dict[str, Any]]:
    """Đọc danh sách airdrop; trả [] nếu lỗi."""
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, list):
            logging.error("airdrops.json: format phải là list.")
            return []
        return data
    except FileNotFoundError:
        logging.error("Không tìm thấy airdrops.json.")
        return []
    except Exception as e:
        logging.error(f"Đọc airdrops.json lỗi: {e}")
        return []

# ========= core =========
async def process_airdrops():
    wallets = load_wallets()
    if not wallets:
        msg = "❗ Không có ví để chạy. Hãy tạo ví (wallet_gen.py) hoặc tải wallets.txt."
        logging.error(msg)
        await send_telegram(msg)
        return

    airdrops = load_airdrops()
    if not airdrops:
        msg = "❗ Không có airdrop trong airdrops.json."
        logging.error(msg)
        await send_telegram(msg)
        return

    limits = httpx.Limits(
        max_connections=MAX_CONCURRENCY,
        max_keepalive_connections=MAX_CONCURRENCY
    )
    timeout = httpx.Timeout(25, connect=10)

    async with httpx.AsyncClient(timeout=timeout, limits=limits) as client:
        sem = asyncio.Semaphore(MAX_CONCURRENCY)

        async def worker(airdrop, wallet):
            async with sem:
                return await run_airdrop(airdrop, wallet, client)

        tasks: List[asyncio.Task] = []
        for w in wallets:
            for air in airdrops:
                tasks.append(asyncio.create_task(worker(air, w)))

        logging.info(
            f"Chạy {len(tasks)} tác vụ "
            f"(wallets={len(wallets)}, airdrops={len(airdrops)}, concurrency={MAX_CONCURRENCY})…"
        )

        results = await asyncio.gather(*tasks, return_exceptions=True)

    ok, warn_or_fail = 0, 0
    lines: List[str] = []
    for r in results:
        if isinstance(r, Exception):
            warn_or_fail += 1
            lines.append(f"❌ {type(r).__name__}: {r}")
        else:
            lines.append(r)
            if "✅" in r:
                ok += 1
            elif "⚠️" in r or "❌" in r:
                warn_or_fail += 1

    header = (
        f"⏱ {datetime.now().isoformat(timespec='seconds')}\n"
        f"📊 Kết quả: ✅ {ok} | ⚠️/❌ {warn_or_fail}\n"
        f"🧪 Ví: {len(wallets)} | Airdrop: {len(airdrops)} | CC: {MAX_CONCURRENCY}\n"
    )
    body = "\n".join(lines[:60])
    report = header + body

    print(report[:4000])
    await send_telegram(report[:4000])

async def main():
    # Cho phép chỉnh tần suất qua ENV nếu muốn
    interval_minutes = int(os.getenv("RUN_EVERY_MIN", "0") or "0")
    interval_hours = int(os.getenv("RUN_EVERY_H", "6") or "6")

    scheduler = AsyncIOScheduler(timezone=TIMEZONE)

    if interval_minutes > 0:
        scheduler.add_job(
            process_airdrops,
            "interval",
            minutes=interval_minutes,
            id="airdrop_job",
            replace_existing=True
        )
        freq_str = f"{interval_minutes} phút/lần"
    else:
        scheduler.add_job(
            process_airdrops,
            "interval",
            hours=interval_hours,
            id="airdrop_job",
            replace_existing=True
        )
        freq_str = f"{interval_hours} giờ/lần"

    scheduler.start()
    hello = (
        f"🤖 Bot khởi động.\n"
        f"TZ: {TIMEZONE} | Concurrency: {MAX_CONCURRENCY}\n"
        f"Lịch chạy: {freq_str}\n"
        f"→ Dùng ENV RUN_EVERY_MIN hoặc RUN_EVERY_H để đổi tần suất."
    )
    print(hello)
    await send_telegram(hello)

    # chạy ngay 1 lượt khi khởi động (tùy chọn)
    if os.getenv("RUN_ON_START", "1") == "1":
        await process_airdrops()

    # giữ event loop sống
    await asyncio.Event().wait()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Stopped by user.")
