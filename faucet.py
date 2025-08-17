import time
from typing import Dict, Any, List
import httpx

def send_telegram(bot_token: str, chat_id: str, text: str) -> None:
    if not bot_token or not chat_id:
        return
    try:
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        payload = {"chat_id": chat_id, "text": text, "parse_mode": "HTML", "disable_web_page_preview": True}
        with httpx.Client(timeout=10) as cli:
            cli.post(url, json=payload)
    except Exception:
        pass

def do_airdrop_for_wallet(wallet: str, task: Dict[str, Any]) -> bool:
    """
    Hàm thực thi kèo cho 1 ví.
    Tạm thời demo: giả lập request nhẹ (hoặc ping endpoint),
    sau bạn cắm logic thật vào đây (ký giao dịch, call API dự án…).
    Trả về True nếu coi là thành công.
    """
    try:
        # ví dụ: ping URL (nếu có)
        url = task.get("url")
        if url:
            with httpx.Client(timeout=10) as cli:
                cli.head(url)  # ping nhanh
        # giả lập delay nhỏ để tôn trọng rate limit
        time.sleep(0.2)
        return True
    except Exception:
        return False

def run_batch(wallets: List[str], task: Dict[str, Any], rpm: int) -> Dict[str, int]:
    """
    Chạy 1 lượt cho danh sách ví (batch nhỏ).
    rpm: requests-per-minute để giới hạn tốc độ an toàn.
    """
    ok = fail = 0
    interval = max(60.0 / max(rpm, 1), 0.05)  # giãn cách giữa ví
    for w in wallets:
        ok |= do_airdrop_for_wallet(w, task)
        if not ok:
            fail += 1
        time.sleep(interval)
    return {"ok": ok, "fail": fail}
