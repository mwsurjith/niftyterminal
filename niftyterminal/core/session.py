"""
Core session management for NSE India API requests.

This module provides the core fetch function that handles:
- Session creation with cookie warmup
- Session reuse for batch operations
- Browser-like headers to avoid anti-bot detection
- Robust error handling for network and JSON failures
"""

import time
import asyncio
import random
import httpx
from typing import Optional, Union, List, Any

# Browser-like headers to mimic real browser requests
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json, text/javascript, */*; q=0.01",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate",
    "Connection": "keep-alive",
    "X-Requested-With": "XMLHttpRequest",
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors", 
    "Sec-Fetch-Site": "same-origin",
}

# NSE URLs for session warmup
NSE_BASE_URL = "https://www.nseindia.com"
NSE_HOMEPAGE = NSE_BASE_URL
NSE_OPTION_CHAIN = f"{NSE_BASE_URL}/option-chain"

# Warmup delay settings (reduced for speed)
WARMUP_DELAY_MIN = 0.1
WARMUP_DELAY_MAX = 0.2


def _create_session(is_async: bool = False) -> Union[httpx.Client, httpx.AsyncClient]:
    """
    Create a new httpx session with browser-like headers.
    """
    if is_async:
        return httpx.AsyncClient(headers=HEADERS, follow_redirects=True)
    return httpx.Client(headers=HEADERS, follow_redirects=True)


async def _awarmup_session(session: httpx.AsyncClient, timeout: int = 10, fast: bool = False) -> bool:
    """
    Asynchronously warm up the session by visiting NSE homepage.
    """
    warmup_headers = {
        **HEADERS,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
        "Upgrade-Insecure-Requests": "1",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none",
        "Sec-Fetch-User": "?1",
        "Cache-Control": "max-age=0",
    }
    
    try:
        response = await session.get(
            NSE_HOMEPAGE, 
            headers=warmup_headers,
            timeout=timeout
        )
        response.raise_for_status()
        
        if fast:
            await asyncio.sleep(random.uniform(WARMUP_DELAY_MIN, WARMUP_DELAY_MAX))
        else:
            await asyncio.sleep(random.uniform(0.3, 0.5))
        
        return True
    except httpx.HTTPError:
        return False


def _warmup_session(session: httpx.Client, timeout: int = 10, fast: bool = False) -> bool:
    """
    Synchronously warm up the session by visiting NSE homepage.
    """
    warmup_headers = {
        **HEADERS,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
        "Upgrade-Insecure-Requests": "1",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none",
        "Sec-Fetch-User": "?1",
        "Cache-Control": "max-age=0",
    }
    
    try:
        response = session.get(
            NSE_HOMEPAGE, 
            headers=warmup_headers,
            timeout=timeout
        )
        response.raise_for_status()
        
        if fast:
            time.sleep(random.uniform(WARMUP_DELAY_MIN, WARMUP_DELAY_MAX))
        else:
            time.sleep(random.uniform(0.3, 0.5))
        
        return True
    except httpx.HTTPError:
        return False


async def _afetch_with_session(session: httpx.AsyncClient, url: str, timeout: int = 10, params: Optional[dict] = None) -> dict:
    """
    Asynchronously fetch data using an existing session.
    """
    try:
        response = await session.get(
            url, 
            timeout=timeout, 
            params=params,
            headers={"Referer": NSE_OPTION_CHAIN}
        )
        response.raise_for_status()
        return response.json()
    except (httpx.HTTPError, ValueError):
        return {}


def _fetch_with_session(session: httpx.Client, url: str, timeout: int = 10, params: Optional[dict] = None) -> dict:
    """
    Synchronously fetch data using an existing session.
    """
    try:
        response = session.get(
            url, 
            timeout=timeout, 
            params=params,
            headers={"Referer": NSE_OPTION_CHAIN}
        )
        response.raise_for_status()
        return response.json()
    except (httpx.HTTPError, ValueError):
        return {}


class AsyncNSESession:
    """
    A reusable asynchronous NSE session for batch operations.
    """
    
    def __init__(self, timeout: int = 10):
        self.timeout = timeout
        self.session = None
        self._warmed_up = False
    
    async def __aenter__(self):
        self.session = _create_session(is_async=True)
        self._warmed_up = await _awarmup_session(self.session, timeout=self.timeout, fast=True)
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.aclose()
        return False
    
    async def fetch(self, url: str, params: Optional[dict] = None, retries: int = 1) -> dict:
        """Fetch data using the reusable async session."""
        if not self._warmed_up:
            self._warmed_up = await _awarmup_session(self.session, timeout=self.timeout, fast=True)
        
        for attempt in range(retries + 1):
            result = await _afetch_with_session(self.session, url, self.timeout, params)
            if result:
                return result
            
            if attempt < retries:
                await asyncio.sleep(random.uniform(0.2, 0.4))
                self._warmed_up = await _awarmup_session(self.session, timeout=self.timeout, fast=True)
        
        return {}


class NSESession:
    """
    A reusable synchronous NSE session for batch operations.
    """
    
    def __init__(self, timeout: int = 10):
        self.timeout = timeout
        self.session = None
        self._warmed_up = False
    
    def __enter__(self):
        self.session = _create_session(is_async=False)
        self._warmed_up = _warmup_session(self.session, timeout=self.timeout, fast=True)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            self.session.close()
        return False
    
    def fetch(self, url: str, params: Optional[dict] = None, retries: int = 1) -> dict:
        """Fetch data using the reusable sync session."""
        if not self._warmed_up:
            self._warmed_up = _warmup_session(self.session, timeout=self.timeout, fast=True)
        
        for attempt in range(retries + 1):
            result = _fetch_with_session(self.session, url, self.timeout, params)
            if result:
                return result
            
            if attempt < retries:
                time.sleep(random.uniform(0.2, 0.4))
                self._warmed_up = _warmup_session(self.session, timeout=self.timeout, fast=True)
        
        return {}


async def afetch(url: str, timeout: int = 10, params: Optional[dict] = None, retries: int = 2) -> dict:
    """
    Asynchronously fetch data from an NSE API endpoint with session warmup.
    """
    for attempt in range(retries + 1):
        async with httpx.AsyncClient(headers=HEADERS, follow_redirects=True) as session:
            try:
                if not await _awarmup_session(session, timeout=timeout, fast=True):
                    if attempt < retries:
                        await asyncio.sleep(random.uniform(0.3, 0.5))
                        continue
                
                response = await session.get(
                    url, 
                    params=params,
                    timeout=timeout,
                    headers={"Referer": NSE_OPTION_CHAIN}
                )
                response.raise_for_status()
                return response.json()
            except (httpx.HTTPError, ValueError):
                if attempt < retries:
                    await asyncio.sleep(random.uniform(0.3, 0.5))
    return {}


def fetch(url: str, timeout: int = 10, params: Optional[dict] = None, retries: int = 2) -> dict:
    """
    Synchronously fetch data from an NSE API endpoint with session warmup.
    """
    for attempt in range(retries + 1):
        with httpx.Client(headers=HEADERS, follow_redirects=True) as session:
            try:
                if not _warmup_session(session, timeout=timeout, fast=True):
                    if attempt < retries:
                        time.sleep(random.uniform(0.3, 0.5))
                        continue
                
                response = session.get(
                    url, 
                    params=params, 
                    timeout=timeout,
                    headers={"Referer": NSE_OPTION_CHAIN}
                )
                response.raise_for_status()
                return response.json()
            except (httpx.HTTPError, ValueError):
                if attempt < retries:
                    time.sleep(random.uniform(0.3, 0.5))
    return {}


async def afetch_raw(url: str, timeout: int = 10, retries: int = 2) -> str:
    """
    Asynchronously fetch raw text content from a URL.
    """
    headers = {**HEADERS, "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"}
    for attempt in range(retries + 1):
        async with httpx.AsyncClient(headers=headers, follow_redirects=True) as session:
            try:
                response = await session.get(url, timeout=timeout)
                response.raise_for_status()
                return response.text
            except httpx.HTTPError:
                if attempt < retries:
                    await asyncio.sleep(random.uniform(0.3, 0.5))
    return ""


def fetch_raw(url: str, timeout: int = 10, retries: int = 2) -> str:
    """
    Synchronously fetch raw text content from a URL.
    """
    headers = {**HEADERS, "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"}
    for attempt in range(retries + 1):
        with httpx.Client(headers=headers, follow_redirects=True) as session:
            try:
                response = session.get(url, timeout=timeout)
                response.raise_for_status()
                return response.text
            except httpx.HTTPError:
                if attempt < retries:
                    time.sleep(random.uniform(0.3, 0.5))
    return ""


# Nifty Indices API configuration (niftyindices.com)
NIFTY_INDICES_HEADERS = {
    'Connection': 'keep-alive',
    'sec-ch-ua': '" Not;A Brand";v="99", "Google Chrome";v="91", "Chromium";v="91"',
    'Accept': 'application/json, text/javascript, */*; q=0.01',
    'DNT': '1',
    'X-Requested-With': 'XMLHttpRequest',
    'sec-ch-ua-mobile': '?0',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.77 Safari/537.36',
    'Content-Type': 'application/json; charset=UTF-8',
    'Origin': 'https://niftyindices.com',
    'Sec-Fetch-Site': 'same-origin',
    'Sec-Fetch-Mode': 'cors',
    'Sec-Fetch-Dest': 'empty',
    'Referer': 'https://niftyindices.com/reports/historical-data',
    'Accept-Language': 'en-US,en;q=0.9,hi;q=0.8',
}

# Nifty Indices API endpoints
NIFTY_INDEX_HISTORY_URL = "https://niftyindices.com/Backpage.aspx/getHistoricaldatatabletoString"
NIFTY_INDEX_PE_PB_DIV_URL = "https://niftyindices.com/Backpage.aspx/getpepbHistoricaldataDBtoString"
NIFTY_INDEX_TOTAL_RETURNS_URL = "https://niftyindices.com/Backpage.aspx/getTotalReturnIndexString"


class NiftyIndicesSession:
    """
    Session for fetching data from Nifty Indices (niftyindices.com).
    """
    
    def __init__(self, timeout: int = 30):
        self.timeout = timeout
        self.session = None
        self.asession = None

    def __enter__(self):
        self.session = httpx.Client(headers=NIFTY_INDICES_HEADERS, timeout=self.timeout)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            self.session.close()
        return False

    async def __aenter__(self):
        self.asession = httpx.AsyncClient(headers=NIFTY_INDICES_HEADERS, timeout=self.timeout)
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.asession:
            await self.asession.aclose()
        return False
    
    def _build_cinfo(self, index_symbol: str, start_date: str, end_date: str) -> dict:
        cinfo = f"{{'name':'{index_symbol}','startDate':'{start_date}','endDate':'{end_date}','indexName':'{index_symbol}'}}"
        return {"cinfo": cinfo}
    
    def _post(self, url: str, data: dict) -> list:
        import json
        try:
            response = self.session.post(url, json=data)
            if response.status_code == 200:
                result = response.json()
                return json.loads(result.get("d", "[]"))
        except Exception:
            pass
        return []

    async def _apost(self, url: str, data: dict) -> list:
        import json
        try:
            response = await self.asession.post(url, json=data)
            if response.status_code == 200:
                result = response.json()
                return json.loads(result.get("d", "[]"))
        except Exception:
            pass
        return []
    
    def fetch_history(self, index_symbol: str, start_date: str, end_date: str) -> list:
        return self._post(NIFTY_INDEX_HISTORY_URL, self._build_cinfo(index_symbol, start_date, end_date))

    async def afetch_history(self, index_symbol: str, start_date: str, end_date: str) -> list:
        return await self._apost(NIFTY_INDEX_HISTORY_URL, self._build_cinfo(index_symbol, start_date, end_date))
    
    def fetch_pe_pb_div(self, index_symbol: str, start_date: str, end_date: str) -> list:
        return self._post(NIFTY_INDEX_PE_PB_DIV_URL, self._build_cinfo(index_symbol, start_date, end_date))

    async def afetch_pe_pb_div(self, index_symbol: str, start_date: str, end_date: str) -> list:
        return await self._apost(NIFTY_INDEX_PE_PB_DIV_URL, self._build_cinfo(index_symbol, start_date, end_date))
    
    def fetch_total_returns(self, index_symbol: str, start_date: str, end_date: str) -> list:
        return self._post(NIFTY_INDEX_TOTAL_RETURNS_URL, self._build_cinfo(index_symbol, start_date, end_date))

    async def afetch_total_returns(self, index_symbol: str, start_date: str, end_date: str) -> list:
        return await self._apost(NIFTY_INDEX_TOTAL_RETURNS_URL, self._build_cinfo(index_symbol, start_date, end_date))
