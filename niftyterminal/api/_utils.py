"""
Shared utilities for XBRL parsing and fetching.

Common helpers used across stocks.py and fundamentals.py to avoid duplication.
"""

import random
import httpx


def parse_number(value_str: str):
    """
    Convert a number string to a float.

    Handles:
      - Commas: "29,26,400.00" → 2926400.0
      - Parenthesized negatives: "(2,68,600.00)" → -268600.0
      - Scientific notation: "1.92388E7" → 19238800.0
      - Dashes: "-" → None
      - Empty / null → None
    """
    if not value_str:
        return None

    s = value_str.strip()
    if not s or s.lower() == "null" or s == "-":
        return None

    negative = False
    if s.startswith("(") and s.endswith(")"):
        negative = True
        s = s[1:-1]

    s = s.replace(",", "").replace("\xa0", "").strip()
    if not s:
        return None

    try:
        val = float(s)
        return -val if negative else val
    except ValueError:
        return None


def has_valid_xbrl(filing: dict) -> bool:
    """Check if a filing has a valid XBRL URL (not the placeholder '-' URL)."""
    xbrl = filing.get("xbrl", "")
    return bool(xbrl) and not xbrl.endswith("/-") and not xbrl.endswith("/-\"")


XBRL_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Encoding": "gzip, deflate",
    "Connection": "keep-alive",
    "Referer": "https://www.nseindia.com/",
}


async def fetch_with_backoff(url: str, timeout: int = 15) -> str:
    """
    Fetch raw content with exponential backoff on rate-limit responses (429/503).

    Retries up to 3 times. On 429/503, waits 2^attempt * jitter seconds before
    retrying. On other errors, waits a short random delay.
    """
    import asyncio

    for attempt in range(3):
        try:
            async with httpx.AsyncClient(
                headers=XBRL_HEADERS, follow_redirects=True
            ) as client:
                resp = await client.get(url, timeout=timeout)
                if resp.status_code in (429, 503):
                    wait = (2 ** attempt) * random.uniform(1.0, 2.0)
                    await asyncio.sleep(wait)
                    continue
                if resp.status_code == 200:
                    return resp.text
        except Exception:
            if attempt < 2:
                await asyncio.sleep(random.uniform(0.5, 1.0))
    return ""
