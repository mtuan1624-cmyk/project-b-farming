import json
import math
from pathlib import Path
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from dotenv import load_dotenv

from config import load_settings
from wallet_loader import load_wallets
from faucet import send_telegram, run_batch

def load_airdrops(path: str):
    p = Path(path)
    if not p.exists():
        return []
    with p.open("r", encoding="utf-8") as f:
        return json.load(f)

def chunk(lst, size):
    for i in range(0, len(lst), size):
        yield lst[i : i + size]

def main():
    load_dotenv()
    settings = load_settings()

    wallets = load_wallets("WALLETS", settings.WALLETS_FILE)
    tasks = load_airdrops(settings.AIRDROPS_FILE)

    if not wallets:
        raise RuntimeError("⚠️ Không tìm thấy ví trong ENV WALLETS hoặc file wallets.txt")
    if not tasks:
        raise RuntimeError("⚠️ Không có kèo nào trong airdrops.json")

    send_telegram(settings.BOT_TOKEN, settings.TELEGRAM_CHAT_ID,
                  f"✅ Khởi động Project B\n• Ví: {len(wallets)}\n• Kèo: {len(tasks)}\n• TZ: {settings.TIMEZONE}")

    # Lịch: mỗi 30 phút chạy 1 lần (bạn chỉnh lại theo nhu cầu)
    scheduler = BackgroundScheduler(timezone=settings.TIMEZONE)

    def job():
        now = datetime.now().strftime("%H:%M:%S")
        for task in tasks:
            name = task.get("name", "Task")
            total = len(wallets)
            ok_all = fail_all = 0
            for batch in chunk(wallets, settings.BATCH_SIZE):
                res = run_batch(batch, task, settings.REQUESTS_PER_MIN)
                ok_all += res.get("ok", 0)
                fail_all += res.get("fail", 0)
            send_telegram(
                settings.BOT_TOKEN,
                settings.TELEGRAM_CHAT_ID,
                f"🧩 <b>{name}</b> ({now})\n"
                f"Done: {ok_all}/{total} ví (fail {fail_all})"
            )

    # chạy ngay 1 lượt khi khởi động
    scheduler.add_job(job, trigger=IntervalTrigger(minutes=30), next_run_time=datetime.now())
    scheduler.start()

    # giữ tiến trình (Replit sẽ giữ console)
    try:
        import time
        while True:
            time.sleep(60)
    except KeyboardInterrupt:
        scheduler.shutdown()

if __name__ == "__main__":
    main()
