# Project B Farming 🚀

Dự án **auto farming** với ~1.500 ví (Dự án B)  
Hệ thống được thiết kế để:
- Tự động claim faucet/airdrop hợp lệ  
- Gom coin/token EVM về **ví mẹ**  
- Báo cáo trạng thái qua **Telegram** (log + lịch chạy)  
- Chạy gọn trên **Replit/GitHub** (điện thoại cũng OK)

## 📂 Cấu trúc
- `main.py` – file chạy chính (scheduler định kỳ)  
- `config.py` – cấu hình chung  
- `wallet_loader.py` – nạp danh sách ví  
- `wallet_gen.py` – tạo mới 1.500 ví  
- `airdrops.json` – danh sách faucet/airdrop  
- `faucet.py` – logic claim faucet/airdrop  
- `sweep.py` – gom coin/token về ví mẹ (khi cần)  
- `requirements.txt` – thư viện cần cài

> **Lưu ý branch:** code chạy ở nhánh `optimized`.  
> Nếu import từ GitHub vào Replit, nhớ chọn **branch `optimized`**.

## ⚙️ Chuẩn bị (Secrets/Environment)
Thêm các biến môi trường:
- `BOT_TOKEN` – token bot Telegram của bạn  
- `TELEGRAM_CHAT_ID` – chat id nhận báo cáo  
- `TIMEZONE` – ví dụ: `Asia/Ho_Chi_Minh`  
- (cho `sweep.py`) `RPC_URL` – URL RPC chain bạn dùng  
- (cho `sweep.py`) `MASTER_WALLET` – địa chỉ ví mẹ nhận coin  
- (tùy chọn) `GAS_PRICE_GWEI` – mặc định `2`  
- (tùy chọn) `ERC20_TOKEN` – contract token nếu gom token ERC-20 thay vì native

## 🚀 Cách chạy nhanh (Replit)
1. Mở Shell và cài thư viện:
```bash
pip install -r requirements.txt
