from typing import List

WALLETS_FILE = "wallets.txt"

def load_wallets() -> List[str]:
    try:
        with open(WALLETS_FILE, "r", encoding="utf-8") as f:
            wallets = [ln.strip() for ln in f.readlines() if ln.strip()]
        # lọc định dạng 0x… dài 42
        wallets = [w for w in wallets if w.startswith("0x") and len(w) == 42]
        return wallets
    except FileNotFoundError:
        print(f"[!] Không thấy {WALLETS_FILE}. Hãy tạo ví (wallet_gen.py) hoặc tải lên file này.")
        return []
