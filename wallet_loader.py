import os
from typing import List

def load_wallets_from_env(env_key: str) -> List[str]:
    data = os.getenv(env_key, "")
    if not data:
        return []
    # hỗ trợ nhiều dòng hoặc dạng "key1,key2,..."
    if "\n" in data:
        lines = [ln.strip() for ln in data.splitlines() if ln.strip()]
    else:
        lines = [p.strip() for p in data.split(",") if p.strip()]
    return list(dict.fromkeys(lines))  # unique & giữ thứ tự

def load_wallets_from_file(path: str) -> List[str]:
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8") as f:
        lines = [ln.strip() for ln in f if ln.strip()]
    return list(dict.fromkeys(lines))

def load_wallets(env_key: str, path: str) -> List[str]:
    wl = load_wallets_from_env(env_key)
    if wl:
        return wl
    return load_wallets_from_file(path)
