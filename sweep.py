# sweep.py
import argparse
import json
import time
from pathlib import Path
from typing import List, Tuple, Optional

from web3 import Web3
from web3.middleware import geth_poa_middleware
from eth_account import Account

from config import (
    RPC_URL,
    MASTER_WALLET,
    GAS_PRICE_GWEI,
    ERC20_TOKEN,
    validate_required_for_runtime,
)

# ----- Cấu hình nhẹ nhàng -----
WALLETS_FILE = "wallets.txt"         # mỗi dòng 1 địa chỉ 0x...
PRIVATE_KEYS_FILE = "private_keys.txt"  # mỗi dòng 1 private key (0x...)
SLEEP_BETWEEN_TX = 0.6               # giãn nhịp để tránh rate-limit
MIN_NATIVE_KEEP_WEI = Web3.to_wei("0.00002", "ether")  # để lại chút dust
TX_TIMEOUT = 180                      # giây chờ receipt
RETRY = 2                             # số lần thử lại khi lỗi tạm thời
# --------------------------------

validate_required_for_runtime("sweep")

w3 = Web3(Web3.HTTPProvider(RPC_URL, request_kwargs={"timeout": 30}))
# Nếu là BSC/Polygon testnet v.v. cần POA middleware:
w3.middleware_onion.inject(geth_poa_middleware, layer=0)
CHAIN_ID = int(w3.eth.chain_id)

def load_wallets() -> List[Tuple[str, str]]:
    addrs = [x.strip() for x in Path(WALLETS_FILE).read_text().splitlines() if x.strip()]
    pks = [x.strip() for x in Path(PRIVATE_KEYS_FILE).read_text().splitlines() if x.strip()]
    if len(addrs) != len(pks):
        raise RuntimeError("Số dòng wallets.txt và private_keys.txt không khớp.")
    return list(zip(addrs, pks))

def gas_price_wei() -> int:
    # dùng cố định theo GAS_PRICE_GWEI để chủ động
    return Web3.to_wei(GAS_PRICE_GWEI, "gwei")

# --- ERC20 helper ---
ERC20_ABI = json.loads("""
[
  {"constant":true,"inputs":[{"name":"a","type":"address"}],"name":"balanceOf","outputs":[{"name":"","type":"uint256"}],"type":"function"},
  {"constant":true,"inputs":[],"name":"decimals","outputs":[{"name":"","type":"uint8"}],"type":"function"},
  {"constant":false,"inputs":[{"name":"to","type":"address"},{"name":"amount","type":"uint256"}],"name":"transfer","outputs":[{"name":"","type":"bool"}],"type":"function"}
]
""")

def wait_receipt(tx_hash: bytes) -> Optional[dict]:
    try:
        return w3.eth.wait_for_transaction_receipt(tx_hash, timeout=TX_TIMEOUT)
    except Exception:
        return None

def send_raw_and_wait(signed) -> Optional[str]:
    tx_hash = w3.eth.send_raw_transaction(signed.rawTransaction)
    rcpt = wait_receipt(tx_hash)
    if rcpt and rcpt.get("status", 0) == 1:
        return tx_hash.hex()
    return None

def sweep_native(addr: str, pk: str) -> Optional[str]:
    bal = w3.eth.get_balance(addr)
    gp = gas_price_wei()
    fee = 21000 * gp
    sendable = bal - fee - MIN_NATIVE_KEEP_WEI
    if sendable <= 0:
        print(f"[SKIP] {addr[:8]}… balance thấp.")
        return None

    nonce = w3.eth.get_transaction_count(addr)
    tx = {
        "to": Web3.to_checksum_address(MASTER_WALLET),
        "value": int(sendable),
        "gas": 21000,
        "gasPrice": gp,
        "nonce": nonce,
        "chainId": CHAIN_ID,
    }
    signed = w3.eth.account.sign_transaction(tx, pk)
    for i in range(RETRY + 1):
        try:
            h = send_raw_and_wait(signed)
            if h:
                print(f"[OK] Native {addr[:8]}… -> master | tx: {h}")
                return h
        except Exception as e:
            print(f"[RETRY {i}] Native {addr[:8]}… err: {e}")
            time.sleep(1.2)
    print(f"[FAIL] Native {addr[:8]}…")
    return None

def sweep_erc20(addr: str, pk: str, token: str) -> Optional[str]:
    token = Web3.to_checksum_address(token)
    cs = Web3.to_checksum_address(MASTER_WALLET)
    c = w3.eth.contract(address=token, abi=ERC20_ABI)
    bal = c.functions.balanceOf(addr).call()
    if bal == 0:
        print(f"[SKIP] {addr[:8]}… token=0")
        return None

    # ước lượng gas
    gp = gas_price_wei()
    nonce = w3.eth.get_transaction_count(addr)
    tx = c.functions.transfer(cs, bal).build_transaction({
        "from": addr,
        "nonce": nonce,
        "gasPrice": gp,
        # 'gas' để w3 tự estimate; fallback nếu RPC không estimate được:
    })
    try:
        est = w3.eth.estimate_gas(tx)
        tx["gas"] = int(est * 1.15)
    except Exception:
        tx["gas"] = 120000  # fallback an toàn

    signed = w3.eth.account.sign_transaction(tx, pk)
    for i in range(RETRY + 1):
        try:
            h = send_raw_and_wait(signed)
            if h:
                print(f"[OK] ERC20 {addr[:8]}… -> master | tx: {h}")
                return h
        except Exception as e:
            print(f"[RETRY {i}] ERC20 {addr[:8]}… err: {e}")
            time.sleep(1.2)
    print(f"[FAIL] ERC20 {addr[:8]}…")
    return None

def main(dry_run: bool = False, limit: int = 0):
    wallets = load_wallets()
    if limit > 0:
        wallets = wallets[:limit]

    print(f"Chain ID: {CHAIN_ID} | RPC: {RPC_URL}")
    print(f"Master: {MASTER_WALLET}")
    mode = "ERC20" if ERC20_TOKEN else "NATIVE"
    print(f"Mode sweep: {mode} | Gas price: {GAS_PRICE_GWEI} GWEI")
    if dry_run:
        print("== DRY RUN: chỉ liệt kê không gửi ==")

    for addr, pk in wallets:
        addr = Web3.to_checksum_address(addr)
        if dry_run:
            if ERC20_TOKEN:
                bal = Web3.to_int(hexstr=w3.eth.contract(Web3.to_checksum_address(ERC20_TOKEN), abi=ERC20_ABI).functions.balanceOf(addr).call().to_bytes(32, "big").hex())
                print(f"[DRY] {addr[:8]}… token balance={bal}")
            else:
                bal = w3.eth.get_balance(addr)
                print(f"[DRY] {addr[:8]}… native balance={Web3.from_wei(bal,'ether')} ")
        else:
            if ERC20_TOKEN:
                sweep_erc20(addr, pk, ERC20_TOKEN)
            else:
                sweep_native(addr, pk)
            time.sleep(SLEEP_BETWEEN_TX)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Sweep native/erc20 về ví mẹ.")
    parser.add_argument("--dry-run", action="store_true", help="Chạy thử, không gửi giao dịch.")
    parser.add_argument("--limit", type=int, default=0, help="Giới hạn số ví xử lý (0=all).")
    args = parser.parse_args()
    main(dry_run=args.dry_run, limit=args.limit)
