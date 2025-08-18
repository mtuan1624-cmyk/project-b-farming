import asyncio
import httpx
from typing import Any, Dict, Optional

# ---- helpers ----
def _short(addr: str) -> str:
    """Rút gọn hiển thị địa chỉ ví"""
    return addr[:8] + "…" + addr[-4:]

def _jitter(base: float = 0.05, spread: float = 0.15) -> float:
    """Thêm delay ngẫu nhiên để tránh spam server"""
    import random
    return max(0.0, base + random.random() * spread)

def _render(value: Any, wallet: str) -> Any:
    """Thay {wallet} trong chuỗi/payload bằng địa chỉ ví"""
    if isinstance(value, str):
        return value.replace("{wallet}", wallet)
    if isinstance(value, dict):
        return {k: _render(v, wallet) for k, v in value.items()}
    if isinstance(value, list):
        return [_render(v, wallet) for v in value]
    return value

# ---- core ----
async def run_airdrop(
    airdrop: Dict[str, Any],
    wallet: str,
    client: Optional[httpx.AsyncClient] = None
) -> str:
    """
    Chạy 1 airdrop/faucet cho 1 ví.

    airdrop = {
      "name": "Tên nhiệm vụ",
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
    ok_mark = airdrop.get("success_contains")

    if not url:
        return f"[{name}] {_short(wallet)} ❌ thiếu URL"

    close_after = False
    if client is None:
        client = httpx.AsyncClient(
            timeout=httpx.Timeout(20, connect=10),
            follow_redirects=True
        )
        close_after = True

    # Nếu chưa có UA thì thêm mặc định
    headers = {"User-Agent": headers.get("User-Agent") or "Mozilla/5.0 ProjectB/1.0", **headers}

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
                msg = f"[{name}] {_short(wallet)} ✅ {r.status_code}"
            else:
                msg = f"[{name}] {_short(wallet)} ⚠️ {r.status_code} / body không khớp"

            if close_after:
                await client.aclose()
            return msg

        except Exception as e:
            if attempt == tries:
                if close_after:
                    await client.aclose()
                return f"[{name}] {_short(wallet)} ❌ lỗi: {e}"
            await asyncio.sleep(0.8 * attempt)

    if close_after:
        await client.aclose()
    return f"[{name}] {_short(wallet)} ❌ không rõ"
