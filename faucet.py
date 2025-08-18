# faucet.py
import asyncio
import json
import random
from typing import Any, Dict, Optional, Union, List

import httpx


# ---------- helpers ----------
def _short(addr: str) -> str:
    return f"{addr[:8]}…{addr[-4:]}"


def _jitter(base: float = 0.05, spread: float = 0.15) -> float:
    """Ngủ ngẫu nhiên ngắn để tránh bùng nổ request."""
    return max(0.0, base + random.random() * spread)


def _render(value: Any, wallet: str) -> Any:
    """Thay {wallet} vào chuỗi / dict / list đệ quy."""
    if isinstance(value, str):
        return value.replace("{wallet}", wallet)
    if isinstance(value, dict):
        return {k: _render(v, wallet) for k, v in value.items()}
    if isinstance(value, list):
        return [_render(v, wallet) for v in value]
    return value


def _ok_by_marker(text: str, marker: Union[str, List[str], None]) -> bool:
    if marker is None:
        return True
    text_low = text.lower()
    if isinstance(marker, str):
        return marker.lower() in text_low
    return any(m.lower() in text_low for m in marker)


# ---------- core ----------
async def run_airdrop(
    airdrop: Dict[str, Any],
    wallet: str,
    client: Optional[httpx.AsyncClient] = None,
) -> str:
    """
    airdrop = {
      "name": "Example",
      "method": "GET" | "POST",
      "url": "https://... ?address={wallet}",
      "headers": {"User-Agent": "xxx"},
      "payload": {"address": "{wallet}"},
      "success_contains": "ok" | ["ok", "success"]
    }
    """
    name = airdrop.get("name", "airdrop")
    method = (airdrop.get("method") or "GET").upper()
    url = _render(airdrop.get("url", ""), wallet)
    if not url:
        return f"[{name}] {_short(wallet)} ❌ thiếu URL"

    headers_in = airdrop.get("headers") or {}
    ua = headers_in.get("User-Agent") if isinstance(headers_in, dict) else None
    headers = {"User-Agent": ua or "Mozilla/5.0 RotChainBot/1.0", **(headers_in or {})}

    payload = _render(airdrop.get("payload"), wallet)
    ok_marker = airdrop.get("success_contains")
    tries = int(airdrop.get("retries", 3))

    async def _do(c: httpx.AsyncClient) -> str:
        for attempt in range(1, tries + 1):
            try:
                await asyncio.sleep(_jitter())
                if method == "POST":
                    r = await c.post(url, json=payload, headers=headers)
                else:
                    r = await c.get(url, headers=headers)

                text = r.text[:2000]  # cắt ngắn log
                ok = (r.status_code < 400) and _ok_by_marker(text, ok_marker)
                if ok:
                    return f"[{name}] {_short(wallet)} ✅ {r.status_code}"
                # body không khớp marker
                msg = f"[{name}] {_short(wallet)} ⚠️ {r.status_code} / body không khớp"
            except Exception as e:
                msg = f"[{name}] {_short(wallet)} ❌ lỗi: {e}"
            # nếu chưa hết lượt thử → chờ rồi thử lại
            if attempt < tries:
                await asyncio.sleep(0.8 * attempt)
            else:
                return msg
        return msg  # fallback (thực tế không tới đây)

    if client is None:
        # đảm bảo đóng client dù bất kỳ nhánh return nào
        timeout = httpx.Timeout(20.0, connect=10.0)
        async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as c:
            return await _do(c)
    else:
        return await _do(client)    }
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
        client = httpx.AsyncClient(timeout=httpx.Timeout(20, connect=10), follow_redirects=True)
        close_after = True

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
                msg = f"[{name}] {_short(wallet)} ✅ {r.status_code}"
            else:
                msg = f"[{name}] {_short(wallet)} ⚠️ {r.status_code} / body không khớp"
            return msg
        except Exception as e:
            if attempt == tries:
                return f"[{name}] {_short(wallet)} ❌ lỗi: {e}"
            await asyncio.sleep(0.8 * attempt)
    if close_after:
        await client.aclose()
    return f"[{name}] {_short(wallet)} ❌ không rõ"
