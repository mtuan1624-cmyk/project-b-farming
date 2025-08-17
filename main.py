import os
import json
import asyncio
import logging
from datetime import datetime
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from config import BOT_TOKEN, TELEGRAM_CHAT_ID, TIMEZONE, MAX_CONCURRENCY
from wallet_loader import load_wallets
from faucet import run_airdrop
import httpx

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)

async def send_telegram(text: str):
    if not BOT_TOKEN or not TELEGRAM_CHAT_ID:
        logging.warning("Thiếu BOT_TOKEN/TELEGRAM_CHAT_ID → bỏ qua gửi Telegram.")
        return
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    async with httpx.AsyncClient(timeout=20) as client:
        await client.post(url, data={"chat_id": TELEGRAM_CHAT_ID, "text": text})

async def process_airdrops():
    wallets = load_wallets()
    if not wallets:
        logging.error("Không có ví để chạy.")
        return

    with open("airdrops.json", "r", encoding="utf-8") as f:
        airdrops = json.load(f)

    limits = httpx.Limits(max_connections=MAX_CONCURRENCY, max_keepalive_connections=MAX_CONCURRENCY)
    async with httpx.AsyncClient(timeout=httpx.Timeout(25, connect=10), limits=limits) as client:
        sem = asyncio.Semaphore(MAX_CONCURRENCY)

        async def worker(air, w):
            async with sem:
                return await run_airdrop(air, w, client)

        tasks = []
        for w in wallets:
            for air in airdrops:
                tasks.append(worker(air, w))

        logging.info(f"Chạy {len(tasks)} tác vụ (wallets={len(wallets)}, airdrops={len(airdrops)}, concurrency={MAX_CONCURRENCY})…")
        results = await asyncio.gather(*tasks, return_exceptions=True)

    ok, fail = 0, 0
    lines = []
    for r in results:
        if isinstance(r, Exception):
            fail += 1
            lines.append(f"❌ {r}")
        else:
            lines.append(r)
            if "✅" in r:
                ok += 1
            elif "⚠️" in r or "❌" in r:
                fail += 1

    report = f"⏱ {datetime.now().isoformat(timespec='seconds')}\n✅ OK: {ok} | ❌ Lỗi/Cảnh báo: {fail}\n" + "\n".join(lines[:50])
    print(report[:3500])
    await send_telegram(report[:3500])

async def main():
    scheduler = AsyncIOScheduler(timezone=TIMEZONE)
    # 2 lần/ngày; đổi hours=6 (4 lần/ngày) hoặc minutes=30 nếu muốn dày hơn
    scheduler.add_job(process_airdrops, "interval", hours=12, id="airdrop_job", replace_existing=True)
    scheduler.start()
    print(f"Bot đã khởi động (TZ={TIMEZONE}, concurrency={MAX_CONCURRENCY}). Đợi lịch chạy…")
    await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(main())
