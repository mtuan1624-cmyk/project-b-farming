# Project B Farming 🚀

Dự án **auto farming** với 1.500 ví (Dự án B).  
Hệ thống được thiết kế để:

- Tự động claim faucet/airdrop hợp lệ  
- Gom coin/token EVM về **ví mẹ**  
- Tích hợp báo cáo Telegram (log + lịch chạy)  
- Hỗ trợ chạy Replit/GitHub dễ dàng trên điện thoại  

## 📂 Cấu trúc file
- `main.py` → File chạy chính
- `config.py` → Cấu hình chung
- `wallet_loader.py` → Nạp ví đã tạo
- `wallet_gen.py` → Tạo ví mới (1.500 ví)
- `airdrops.json` → Danh sách faucet/airdrop
- `faucet.py` → Logic auto faucet/airdrop
- `requirements.txt` → Thư viện cần cài

## 🚀 Cách chạy nhanh
1. Tạo Repl Python 3.12 trên Replit.  
2. Upload toàn bộ repo này.  
3. Vào **Secrets/Environment** thêm:  
   - `BOT_TOKEN` = Token Telegram bot  
   - `CHAT_ID` = ID chat nhận báo cáo  
   - `MASTER_WALLET` = Ví mẹ (nhận coin gom về)  
4. Chạy `main.py`.  

---
✅ Tối ưu cho chạy **Replit/GitHub** trên điện thoại.
