import os
from typing import List

def load_wallets_from_env(env_key: str = "WALLETS_TEXT") -> List[str]:
    data = os.getenv(env_key, "").strip()
    if not data:
        return []
    lines = [ln.strip() for ln in data.splitlines() if ln.strip()]
    return lines

def load_wallets_from_file(path: str = "wallets.txt") -> List[str]:
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8") as f:
        lines = [ln.strip() for ln in f if ln.strip()]
    return lines

def load_wallets(env_key: str = "WALLETS_TEXT", fallback: str = "wallets.txt") -> list:
    wl = load_wallets_from_env(env_key)
    if wl:
        return wl
    return load_wallets_from_file(fallback)
