# wallet_gen.py
from eth_account import Account
Account.enable_unaudited_hdwallet_features()
import secrets

N = 1500                     # đổi nếu bạn muốn
WALLETS_FILE = "wallets.txt"
PRIVATE_KEYS_FILE = "private_keys.txt"

def main():
    addrs, pks = [], []
    for _ in range(N):
        pk = "0x" + secrets.token_hex(32)
        acct = Account.from_key(pk)
        addrs.append(acct.address)
        pks.append(pk)

    with open(WALLETS_FILE, "w") as f:
        f.write("\n".join(addrs))
    with open(PRIVATE_KEYS_FILE, "w") as f:
        f.write("\n".join(pks))

    print(f"✅ Đã tạo {N} ví.")
    print(f"- Địa chỉ: {WALLETS_FILE}")
    print(f"- Private keys: {PRIVATE_KEYS_FILE} (ĐỪNG commit lên GitHub!)")

if __name__ == "__main__":
    main()
