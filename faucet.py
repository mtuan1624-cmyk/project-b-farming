# faucet.py
import asyncio
from typing import Any, Dict, Optional, Union
import httpx

# -------- helpers --------
def _short(addr: str) -> str:
    return addr[:8] + "…" + addr[-4:]

def _jitter(base: float = 0.05, spread: float = 0.15) -> float:
    # nghỉ ngắn để giảm bùng nổ request
    import random
    return max(0.0, base + random.random() * spread)

def _render(value: Any, wallet: str) -> Any:
    """Thay {wallet} trong chuỗi/payload theo địa chỉ ví"""
    if isinstance(value, str):
        return value.replace("{wallet}", wallet)
    if isinstance(value, dict):
        return {k: _render(v, wallet) for k, v in value.items()}
    if isinstance(value, list):
        return [_render(v, wallet) for v in value]
    return value

# -------- core --------
async def run_airdrop(
    airdrop: Dict[str, Any],
    wallet: str,
    client: Optional[httpx.AsyncClient] = None
) -> str:
    """
    airdrop = {
      "name": "Tên",
      "method": "GET" | "POST",
      "url": "https://…?address={wallet}",
      "headers": {"User-Agent": "xxx"},
      "payload": {"address": "{wallet}"},
      "success_contains": "ok" | ["ok","success"]
    }
    """
    name = airdrop.get("name", "airdrop")
    method = (airdrop.get("method") or "GET").upper()
    url = _render(airdrop.get("url", ""), wallet)
    headers = airdrop.get("headers") or {}
    payload = _render(airdrop.get("payload"), wallet)
    ok_mark: Union[str, list, None] = airdrop.get("success_contains")

    if not url:
        return f"[{name}] {_short(wallet)} ❌ thiếu URL"

    created_client = False
    if client is None:
        client = httpx.AsyncClient(
            timeout=httpx.Timeout(20, connect=10),
            follow_redirects=True,
        )
        created_client = True

    # Thêm UA đơn giản nếu thiếu
    headers = {"User-Agent": headers.get("User-Agent") or "Mozilla/5.0 RotChainBot/1.0", **headers}

    tries = 3
    for attempt in range(1, tries + 1):
        try:
            await asyncio.sleep(_jitter())
            if method == "POST":
                r = await client.post(url, json=payload, headers=headers)
            else:
                r = await client.get(url, headers=headers)

            text = r.text[:2000]  # cắt tránh log dài
            if ok_mark:
                if isinstance(ok_mark, str):
                    ok = ok_mark.lower() in text.lower()
                else:
                    ok = any(m.lower() in text.lower() for m in ok_mark)
            else:
                ok = r.status_code < 400

            if ok:
                return f"[{name}] {_short(wallet)} ✅ {r.status_code}"
            else:
                return f"[{name}] {_short(wallet)} ⚠️ {r.status_code} / body không khớp"

        except Exception as e:
            if attempt == tries:
                return f"[{name}] {_short(wallet)} ❌ lỗi: {e}"
            await asyncio.sleep(0.8 * attempt)

    # đóng client nếu do hàm này tạo
    if created_client:
        await client.aclose()

    return f"[{name}] {_short(wallet)} ❌ không rõ"
