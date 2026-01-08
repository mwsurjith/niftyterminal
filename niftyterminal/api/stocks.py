"""
Stocks API functions.

This module provides functions to fetch stock-related data from NSE India.
"""

import csv
from io import StringIO
from niftyterminal.core import fetch


# NSE Equity CSV URL
EQUITY_CSV_URL = "https://nsearchives.nseindia.com/content/equities/EQUITY_L.csv"

# NSE Quote API endpoints
QUOTE_SYMBOL_DATA_URL = "https://www.nseindia.com/api/NextApi/apiClient/GetQuoteApi"


def _parse_listing_date(date_str: str) -> str:
    """
    Convert date from DD-Mon-YYYY format to YYYY-MM-DD.
    e.g., "06-OCT-2008" -> "2008-10-06"
    or "06-Oct-2008 00:00:00" -> "2008-10-06"
    """
    from datetime import datetime
    
    if not date_str:
        return ""
    
    # Handle datetime format with time
    date_part = date_str.split()[0] if " " in date_str else date_str
    
    try:
        dt = datetime.strptime(date_part.strip(), "%d-%b-%Y")
        return dt.strftime("%Y-%m-%d")
    except ValueError:
        return ""


def _fetch_raw(url: str) -> str:
    """Fetch raw content from URL."""
    import requests
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        return response.text
    except Exception:
        return ""


def get_stocks_list() -> dict:
    """
    Get the complete list of all listed stocks on NSE.
    
    This function fetches the official EQUITY_L.csv from NSE archives
    which contains all listed equity securities.
    
    Returns:
        A dictionary with:
        - stockList: List of stock objects with:
            - symbol: Stock ticker symbol
            - companyName: Full company name
            - series: Trading series (e.g., "EQ", "BE", "BZ")
            - isin: ISIN code
        
        Returns empty dict {} if the API call fails.
        
    Example:
        >>> from niftyterminal import get_stocks_list
        >>> data = get_stocks_list()
        >>> print(f"Total stocks: {len(data['stockList'])}")
    """
    # Fetch the CSV content
    csv_content = _fetch_raw(EQUITY_CSV_URL)
    
    if not csv_content:
        return {}
    
    stock_list = []
    
    # Parse CSV
    reader = csv.DictReader(StringIO(csv_content))
    
    for row in reader:
        # Column names from CSV header
        symbol = row.get("SYMBOL", "").strip()
        company_name = row.get("NAME OF COMPANY", "").strip()
        series = row.get(" SERIES", "").strip()  # Note: space before SERIES in header
        isin = row.get(" ISIN NUMBER", "").strip()
        
        if not symbol:
            continue
        
        stock_list.append({
            "symbol": symbol,
            "companyName": company_name,
            "series": series,
            "isin": isin,
        })
    
    return {
        "stockList": stock_list,
    }


def get_stock_quote(symbol: str) -> dict:
    """
    Get quote and detailed information for a specific stock.
    
    This function fetches comprehensive stock data including current price,
    company info, market cap, sector classification, and trading status.
    
    Args:
        symbol: Stock ticker symbol (e.g., "RELIANCE", "TCS", "20MICRONS")
    
    Returns:
        A dictionary with:
        - symbol: Stock ticker symbol
        - companyName: Full company name
        - series: Trading series (e.g., "EQ")
        - listingDate: Date of listing in YYYY-MM-DD format
        - isin: ISIN code
        - faceValue: Face value of the stock
        - marketCap: Total market capitalization
        - secStatus: Security status (e.g., "Listed")
        - industry: Basic industry classification
        - sector: Sector classification
        - sectorPe: Sector PE ratio
        - industryInfo: Industry information
        - macro: Macro category
        - tradingSegment: Trading segment
        - isFNOSec: If eligible for F&O trading
        - isCASec: If corporate action security
        - isSLBSec: If eligible for SLB
        - isDebtSec: If debt security
        - isSuspended: If trading is suspended
        - isETFSec: If ETF security
        - isDelisted: If delisted
        - isMunicipalBond: If municipal bond
        - isHybridSymbol: If hybrid symbol
        - open: Opening price
        - high: Day high
        - low: Day low
        - ltp: Last traded price
        - prevClose: Previous close
        - change: Price change
        - percentChange: Percentage change
        - pe: Stock PE ratio
        
        Returns empty dict {} if the API call fails.
        
    Example:
        >>> from niftyterminal import get_stock_quote
        >>> data = get_stock_quote("RELIANCE")
        >>> print(f"LTP: {data['ltp']}, Change: {data['percentChange']}%")
    """
    from urllib.parse import quote
    
    # Fetch symbol data (for market cap, listing date, sector info, price data)
    symbol_data_url = f"{QUOTE_SYMBOL_DATA_URL}?functionName=getSymbolData&marketType=N&series=EQ&symbol={quote(symbol)}"
    symbol_response = fetch(symbol_data_url)
    
    # Fetch metadata (for FNO, SLB, etc. flags)
    meta_data_url = f"{QUOTE_SYMBOL_DATA_URL}?functionName=getMetaData&symbol={quote(symbol)}"
    meta_response = fetch(meta_data_url)
    
    if not symbol_response:
        return {}
    
    # Parse symbol data
    equity_data = symbol_response.get("equityResponse", [])
    if not equity_data:
        return {}
    
    data = equity_data[0]
    meta_data = data.get("metaData", {})
    trade_info = data.get("tradeInfo", {})
    sec_info = data.get("secInfo", {})
    order_book = data.get("orderBook", {})
    
    # Parse boolean flags from metadata response
    def parse_bool(val):
        if isinstance(val, bool):
            return val
        if isinstance(val, str):
            return val.lower() == "true"
        return False
    
    # Build result with existing fields
    result = {
        "symbol": meta_data.get("symbol", symbol),
        "companyName": meta_data.get("companyName", ""),
        "series": meta_data.get("series", ""),
        "listingDate": _parse_listing_date(sec_info.get("listingDate", "")),
        "isin": meta_data.get("isinCode", ""),
        "faceValue": trade_info.get("faceValue", 0),
        "marketCap": trade_info.get("totalMarketCap", 0),
        "secStatus": sec_info.get("secStatus", ""),
        "industry": sec_info.get("basicIndustry", ""),
        "sector": sec_info.get("sector", ""),
        "sectorPe": sec_info.get("pdSectorPe", ""),
        "industryInfo": sec_info.get("industryInfo", ""),
        "macro": sec_info.get("macro", ""),
        "tradingSegment": sec_info.get("tradingSegment", ""),
    }
    
    # Add flags from metadata response
    if meta_response:
        result["isFNOSec"] = parse_bool(meta_response.get("isFNOSec", False))
        result["isCASec"] = parse_bool(meta_response.get("isCASec", False))
        result["isSLBSec"] = parse_bool(meta_response.get("isSLBSec", False))
        result["isDebtSec"] = parse_bool(meta_response.get("isDebtSec", False))
        result["isSuspended"] = parse_bool(meta_response.get("isSuspended", False))
        result["isETFSec"] = parse_bool(meta_response.get("isETFSec", False))
        result["isDelisted"] = parse_bool(meta_response.get("isDelisted", False))
        result["isMunicipalBond"] = parse_bool(meta_response.get("isMunicipalBond", False))
        result["isHybridSymbol"] = parse_bool(meta_response.get("isHybridSymbol", False))
    else:
        # Default values if metadata not available
        result["isFNOSec"] = False
        result["isCASec"] = False
        result["isSLBSec"] = False
        result["isDebtSec"] = False
        result["isSuspended"] = False
        result["isETFSec"] = False
        result["isDelisted"] = False
        result["isMunicipalBond"] = False
        result["isHybridSymbol"] = False
    
    # Add price/trade fields from metaData
    result["open"] = meta_data.get("open", 0)
    result["high"] = meta_data.get("dayHigh", 0)
    result["low"] = meta_data.get("dayLow", 0)
    result["ltp"] = order_book.get("lastPrice", meta_data.get("closePrice", 0))
    result["prevClose"] = meta_data.get("previousClose", 0)
    result["change"] = meta_data.get("change", 0)
    result["percentChange"] = meta_data.get("pChange", 0)
    result["pe"] = sec_info.get("pdSymbolPe", "")
    
    return result


