"""
Core session management for NSE India API requests.

This module provides the core fetch function that handles:
- Session creation with cookie warmup
- Session reuse for batch operations
- Browser-like headers to avoid anti-bot detection
- Robust error handling for network and JSON failures
"""

import time
import random
import requests
from typing import Optional
from concurrent.futures import ThreadPoolExecutor, as_completed

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


def _create_session() -> requests.Session:
    """
    Create a new requests session with browser-like headers.
    
    Returns:
        A configured requests.Session object.
    """
    session = requests.Session()
    session.headers.update(HEADERS)
    return session


def _warmup_session(session: requests.Session, timeout: int = 10, fast: bool = False) -> bool:
    """
    Warm up the session by visiting NSE homepage.
    
    This is necessary to obtain the required cookies for API access.
    NSE blocks direct API calls without proper session cookies.
    
    Args:
        session: The requests session to warm up.
        timeout: Request timeout in seconds.
        fast: If True, use minimal delays (for batch operations).
        
    Returns:
        True if warmup succeeded, False otherwise.
    """
    # Use different headers for the initial page visit (HTML, not JSON)
    warmup_headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Encoding": "gzip, deflate",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none",
        "Sec-Fetch-User": "?1",
        "Cache-Control": "max-age=0",
    }
    
    try:
        # Visit homepage first to get initial cookies
        response = session.get(
            NSE_HOMEPAGE, 
            headers=warmup_headers,
            timeout=timeout
        )
        response.raise_for_status()
        
        # Minimal delay for fast mode, otherwise normal delay
        if fast:
            time.sleep(random.uniform(WARMUP_DELAY_MIN, WARMUP_DELAY_MAX))
        else:
            time.sleep(random.uniform(0.3, 0.5))
        
        return True
    except requests.RequestException:
        return False


def _fetch_with_session(session: requests.Session, url: str, timeout: int = 10, params: Optional[dict] = None) -> dict:
    """
    Fetch data using an existing session (no warmup).
    
    Args:
        session: Pre-warmed requests session.
        url: The full URL of the NSE API endpoint to fetch.
        timeout: Request timeout in seconds.
        params: Optional query parameters.
        
    Returns:
        The JSON response as a dictionary, or empty dict on error.
    """
    try:
        response = session.get(
            url, 
            timeout=timeout, 
            params=params,
            headers={
                "Referer": NSE_OPTION_CHAIN,
            }
        )
        response.raise_for_status()
        return response.json()
    except (requests.RequestException, ValueError):
        return {}


class NSESession:
    """
    A reusable NSE session for batch operations.
    
    Use this class when making multiple API calls to avoid
    repeated session warmups. The session is warmed up once
    and reused for all subsequent calls.
    
    Example:
        >>> with NSESession() as nse:
        ...     data1 = nse.fetch("https://www.nseindia.com/api/marketStatus")
        ...     data2 = nse.fetch("https://www.nseindia.com/api/allIndices")
    """
    
    def __init__(self, timeout: int = 10):
        self.timeout = timeout
        self.session = None
        self._warmed_up = False
    
    def __enter__(self):
        self.session = _create_session()
        self._warmed_up = _warmup_session(self.session, timeout=self.timeout, fast=True)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            self.session.close()
        return False
    
    def fetch(self, url: str, params: Optional[dict] = None, retries: int = 1) -> dict:
        """
        Fetch data using the reusable session.
        
        Args:
            url: The full URL of the NSE API endpoint.
            params: Optional query parameters.
            retries: Number of retry attempts on failure.
            
        Returns:
            The JSON response as a dictionary, or empty dict on error.
        """
        if not self._warmed_up:
            self._warmed_up = _warmup_session(self.session, timeout=self.timeout, fast=True)
        
        for attempt in range(retries + 1):
            result = _fetch_with_session(self.session, url, self.timeout, params)
            if result:
                return result
            
            # Re-warmup and retry
            if attempt < retries:
                time.sleep(random.uniform(0.2, 0.4))
                self._warmed_up = _warmup_session(self.session, timeout=self.timeout, fast=True)
        
        return {}
    
    def fetch_parallel(self, urls: list[str], max_workers: int = 2) -> list[dict]:
        """
        Fetch multiple URLs in parallel using the same session.
        
        Args:
            urls: List of URLs to fetch.
            max_workers: Number of parallel workers.
            
        Returns:
            List of JSON responses (in same order as urls).
        """
        results = [{}] * len(urls)
        
        def fetch_url(url_index: tuple[int, str]) -> tuple[int, dict]:
            idx, url = url_index
            return (idx, self.fetch(url))
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = [executor.submit(fetch_url, (i, url)) for i, url in enumerate(urls)]
            for future in as_completed(futures):
                idx, data = future.result()
                results[idx] = data
        
        return results


def fetch(url: str, timeout: int = 10, params: Optional[dict] = None, retries: int = 2) -> dict:
    """
    Fetch data from an NSE API endpoint with session warmup.
    
    This function creates a new session for each call to avoid stale cookies,
    warms up the session by visiting NSE pages, and then fetches the requested URL.
    
    For batch operations, use NSESession context manager instead.
    
    Args:
        url: The full URL of the NSE API endpoint to fetch.
        timeout: Request timeout in seconds (default: 10).
        params: Optional query parameters to pass to the request.
        retries: Number of retry attempts on failure (default: 2).
        
    Returns:
        The JSON response as a dictionary.
        Returns an empty dict {} if JSON decoding fails or on any error.
        
    Example:
        >>> data = fetch("https://www.nseindia.com/api/marketStatus")
        >>> print(data)
        {'marketState': [...], 'marketcap': {...}}
    """
    last_error = None
    
    for attempt in range(retries + 1):
        # Create a fresh session for each attempt
        session = _create_session()
        
        try:
            # Warm up the session to get required cookies (fast mode)
            if not _warmup_session(session, timeout=timeout, fast=True):
                # Warmup failed, wait and retry
                if attempt < retries:
                    time.sleep(random.uniform(0.3, 0.5))
                    continue
            
            # Make the actual API request with JSON headers
            response = session.get(
                url, 
                timeout=timeout, 
                params=params,
                headers={
                    "Referer": NSE_OPTION_CHAIN,
                }
            )
            response.raise_for_status()
            
            # Try to parse JSON response
            return response.json()
            
        except requests.RequestException as e:
            last_error = e
            # Wait before retry
            if attempt < retries:
                time.sleep(random.uniform(0.3, 0.5))
        except ValueError as e:
            # JSON decode error
            last_error = e
            if attempt < retries:
                time.sleep(random.uniform(0.3, 0.5))
        finally:
            # Always close the session
            session.close()
    
    # All retries failed
    return {}


def fetch_raw(url: str, timeout: int = 10, retries: int = 2) -> str:
    """
    Fetch raw text content from a URL (for CSV, etc.).
    
    This function is simpler than fetch() as it doesn't require session warmup
    for public archival URLs like nsearchives.nseindia.com.
    
    Args:
        url: The full URL to fetch.
        timeout: Request timeout in seconds (default: 10).
        retries: Number of retry attempts on failure (default: 2).
        
    Returns:
        The raw text content.
        Returns an empty string "" on any error.
        
    Example:
        >>> csv_content = fetch_raw("https://nsearchives.nseindia.com/content/equities/EQUITY_L.csv")
    """
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Encoding": "gzip, deflate",
        "Connection": "keep-alive",
    }
    
    for attempt in range(retries + 1):
        try:
            response = requests.get(url, headers=headers, timeout=timeout)
            response.raise_for_status()
            return response.text
        except requests.RequestException:
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
    
    This class provides methods to fetch historical index data from 
    niftyindices.com which often has more complete data than NSE India.
    
    Example:
        >>> with NiftyIndicesSession() as session:
        ...     history = session.fetch_history("NIFTY 50", "01-Jan-2024", "31-Dec-2024")
        ...     pe_pb = session.fetch_pe_pb_div("NIFTY 50", "01-Jan-2024", "31-Dec-2024")
    """
    
    def __init__(self, timeout: int = 30):
        self.timeout = timeout
        self.session = None
    
    def __enter__(self):
        self.session = requests.Session()
        self.session.headers.update(NIFTY_INDICES_HEADERS)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            self.session.close()
        return False
    
    def _build_cinfo(self, index_symbol: str, start_date: str, end_date: str) -> dict:
        """
        Build the cinfo payload for Nifty Indices API.
        
        Args:
            index_symbol: Name of the index (e.g., "NIFTY 50")
            start_date: Start date in DD-Mon-YYYY format (e.g., "01-Jan-2024")
            end_date: End date in DD-Mon-YYYY format (e.g., "31-Dec-2024")
            
        Returns:
            Dictionary with cinfo payload.
        """
        cinfo = f"{{'name':'{index_symbol}','startDate':'{start_date}','endDate':'{end_date}','indexName':'{index_symbol}'}}"
        return {"cinfo": cinfo}
    
    def _post(self, url: str, data: dict) -> list:
        """
        Make a POST request to Nifty Indices API.
        
        Args:
            url: The API endpoint URL.
            data: The JSON payload.
            
        Returns:
            Parsed list of data items, or empty list on error.
        """
        import json
        
        try:
            response = self.session.post(url, json=data, timeout=self.timeout)
            if response.status_code == 200:
                result = response.json()
                return json.loads(result.get("d", "[]"))
        except Exception:
            pass
        return []
    
    def fetch_history(self, index_symbol: str, start_date: str, end_date: str) -> list:
        """
        Fetch historical OHLC data for an index.
        
        Args:
            index_symbol: Name of the index (e.g., "NIFTY 50")
            start_date: Start date in DD-Mon-YYYY format
            end_date: End date in DD-Mon-YYYY format
            
        Returns:
            List of historical data records.
        """
        payload = self._build_cinfo(index_symbol, start_date, end_date)
        return self._post(NIFTY_INDEX_HISTORY_URL, payload)
    
    def fetch_pe_pb_div(self, index_symbol: str, start_date: str, end_date: str) -> list:
        """
        Fetch PE, PB, and Dividend Yield data for an index.
        
        Args:
            index_symbol: Name of the index (e.g., "NIFTY 50")
            start_date: Start date in DD-Mon-YYYY format
            end_date: End date in DD-Mon-YYYY format
            
        Returns:
            List of PE/PB/DivYield records.
        """
        payload = self._build_cinfo(index_symbol, start_date, end_date)
        return self._post(NIFTY_INDEX_PE_PB_DIV_URL, payload)
    
    def fetch_total_returns(self, index_symbol: str, start_date: str, end_date: str) -> list:
        """
        Fetch Total Returns Index data for an index.
        
        Args:
            index_symbol: Name of the index (e.g., "NIFTY 50")
            start_date: Start date in DD-Mon-YYYY format
            end_date: End date in DD-Mon-YYYY format
            
        Returns:
            List of Total Returns Index records.
        """
        payload = self._build_cinfo(index_symbol, start_date, end_date)
        return self._post(NIFTY_INDEX_TOTAL_RETURNS_URL, payload)
