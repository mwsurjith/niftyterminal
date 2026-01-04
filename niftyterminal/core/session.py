"""
Core session management for NSE India API requests.

This module provides the core fetch function that handles:
- Session creation with cookie warmup
- Browser-like headers to avoid anti-bot detection
- Robust error handling for network and JSON failures
"""

import time
import random
import requests
from typing import Optional

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


def _create_session() -> requests.Session:
    """
    Create a new requests session with browser-like headers.
    
    Returns:
        A configured requests.Session object.
    """
    session = requests.Session()
    session.headers.update(HEADERS)
    return session


def _warmup_session(session: requests.Session, timeout: int = 10) -> bool:
    """
    Warm up the session by visiting NSE homepage and option-chain page.
    
    This is necessary to obtain the required cookies for API access.
    NSE blocks direct API calls without proper session cookies.
    
    Args:
        session: The requests session to warm up.
        timeout: Request timeout in seconds.
        
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
        
        # Add a small random delay to mimic human behavior
        time.sleep(random.uniform(0.5, 1.5))
        
        # Visit option-chain page to get additional required cookies
        response = session.get(
            NSE_OPTION_CHAIN,
            headers=warmup_headers,
            timeout=timeout
        )
        response.raise_for_status()
        
        # Small delay before API call
        time.sleep(random.uniform(0.3, 0.8))
        
        return True
    except requests.RequestException:
        return False


def fetch(url: str, timeout: int = 10, params: Optional[dict] = None, retries: int = 2) -> dict:
    """
    Fetch data from an NSE API endpoint with session warmup.
    
    This function creates a new session for each call to avoid stale cookies,
    warms up the session by visiting NSE pages, and then fetches the requested URL.
    
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
            # Warm up the session to get required cookies
            if not _warmup_session(session, timeout=timeout):
                # Warmup failed, wait and retry
                if attempt < retries:
                    time.sleep(random.uniform(1, 2))
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
                time.sleep(random.uniform(1, 2))
        except ValueError as e:
            # JSON decode error
            last_error = e
            if attempt < retries:
                time.sleep(random.uniform(1, 2))
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
                time.sleep(random.uniform(1, 2))
    
    return ""


