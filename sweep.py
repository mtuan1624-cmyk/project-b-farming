import os
import time
from dotenv import load_dotenv
from web3 import Web3
from eth_account import Account

load_dotenv()

RPC_URL = os.getenv("RPC_URL")                      # ví dụ: https://rpc.ankr.com/eth_sepolia
DESTINATION = os.getenv("MASTER_WALLET")            # ví mẹ
GAS_PRICE_GWEI = float(os.getenv("GAS_PRICE_GWEI", "2"))
ERC20_TOKEN = os.getenv("ERC20_TOKEN", "").strip()  # để trống nếu chỉ sweep native
PRIVATE_KEYS_FILE = "private_keys.txt"

ERC20_ABI = [
  {"constant":True,"inputs":[{"name":"_owner","type":"address"}],
   "name":"balanceOf","outputs":[{"name":"balance","type":"uint256"}],"type":"function"},
  {"constant":False,"inputs":[{"name":"_to","type":"address"},{"name":"_value","type":"uint256"}],
   "name":"transfer","outputs":[{"name":"","type":"bool"}],"type":"function"},
  {"constant":True,"inputs":[],"name":"decimals","outputs":[{"name":"","type":"uint8"}],"type":"function"}
]

w3 = Web3(Web3.HTTPProvider(RPC_URL)) if RPC_URL else None

def load_private_keys():
    with open(PRIVATE_KEYS_FILE, "r", encoding="utf-8") as f:
        return [x.strip() for x in f if x.strip()]

def short(x: str) -> str:
    return x[:8] + "…" + x[-4:]

def sweep_native(pk: str):
    acct = Account.from_key(pk)
    addr = acct.address

    gas_price = w3.to_wei(GAS_PRICE_GWEI, "gwei")
    nonce = w3.eth.get_transaction_count(addr)

    balance = w3.eth.get_balance(addr)
    fee = 21000 * gas_price
    amount = balance - fee
    if amount <= 0:
        return f"{short(addr)}: balance quá thấp ({balance})"

    tx = {
        "to": DESTINATION,
        "value": amount,
        "nonce": nonce,
        "gas": 21000,
        "gasPrice": gas_price,
        "chainId": w3.eth.chain_id
    }
    signed = w3.eth.account.sign_transaction(tx, pk)
    txh = w3.eth.send_raw_transaction(signed.rawTransaction).hex()
    return f"{short(addr)} → native ok: {txh}"

def sweep_erc20(pk: str, token_addr: str):
    acct = Account.from_key(pk)
    addr = acct.address
    token = w3.eth.contract(address=Web3.to_checksum_address(token_addr), abi=ERC20_ABI)

    bal = token.functions.balanceOf(addr).call()
    if bal == 0:
        return f"{short(addr)}: token 0"

    gas_price = w3.to_wei(GAS_PRICE_GWEI, "gwei")
    nonce = w3.eth.get_transaction_count(addr)

    tx = token.functions.transfer(DESTINATION, bal).build_transaction({
        "from": addr,
        "nonce": nonce,
        "gasPrice": gas_price
    })
    tx["gas"] = w3.eth.estimate_gas(tx)

    signed = w3.eth.account.sign_transaction(tx, pk)
    txh = w3.eth.send_raw_transaction(signed.rawTransaction).hex()
    return f"{short(addr)} → token ok: {txh}"

def main():
    if not RPC_URL or not DESTINATION or not w3:
        print("⚠️ Thiếu RPC_URL hoặc MASTER_WALLET")
        return
    keys = load_private_keys()
    print(f"🔄 Sweep {len(keys)} ví… (gas {GAS_PRICE_GWEI} gwei)")
    for i, pk in enumerate(keys, 1):
        try:
            if ERC20_TOKEN:
                msg = sweep_erc20(pk, ERC20_TOKEN)
            else:
                msg = sweep_native(pk)
            print(f"{i:04d}. {msg}")
        except Exception as e:
            print(f"{i:04d}. lỗi: {e}")
        time.sleep(0.3)

if __name__ == "__main__":
    main()
