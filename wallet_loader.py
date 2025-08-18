from typing import List
import logging
import os

DEFAULT_WALLETS_FILE = "wallets.txt"

def load_wallets(file_path: str = DEFAULT_WALLETS_FILE) -> List[str]:
    try:
        if not os.path.exists(file_path):
            logging.warning(f"[!] Không thấy {file_path}. Hãy chạy wallet_gen.py hoặc tải file lên.")
            return []

        with open(file_path, "r", encoding="utf-8") as f:
            wallets = [ln.strip() for ln in f if ln.strip()]

        # lọc định dạng 0x… dài 42
        wallets = [w for w in wallets if w.startswith("0x") and len(w) == 42]

        logging.info(f"✅ Đã load {len(wallets)} ví từ {file_path}")
        return wallets
    except Exception as e:
        logging.error(f"Lỗi khi load ví: {e}")
        return []
