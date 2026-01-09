"""
Indices API functions.

This module provides functions to fetch index-related data from NSE India.
"""

from niftyterminal.core import afetch


# NSE All Indices API endpoint
ALL_INDICES_URL = "https://www.nseindia.com/api/allIndices"

# Sectoral indices that appear in derivatives list but should be marked as SECTORAL INDICES
SECTORAL_OVERRIDE = {"NIFTY BANK", "NIFTY FIN SERVICE"}


def _parse_date_to_ymd(date_str: str) -> str:
    """
    Convert date from DD-Mon-YYYY format to YYYY-MM-DD.
    """
    from datetime import datetime
    
    if not date_str:
        return ""
    
    try:
        dt = datetime.strptime(date_str, "%d-%b-%Y")
        return dt.strftime("%Y-%m-%d")
    except ValueError:
        return ""


def _parse_timestamp_to_date(timestamp_str: str) -> str:
    """
    Extract date from timestamp format DD-Mon-YYYY HH:MM or HH:MM:SS to YYYY-MM-DD.
    """
    from datetime import datetime
    
    if not timestamp_str:
        return ""
    
    # Try format with seconds first, then without
    for fmt in ["%d-%b-%Y %H:%M:%S", "%d-%b-%Y %H:%M"]:
        try:
            dt = datetime.strptime(timestamp_str, fmt)
            return dt.strftime("%Y-%m-%d")
        except ValueError:
            continue
    
    return ""



def _calc_percent_change(current: float, past: float) -> float:
    """
    Calculate percent change: ((current - past) / past) * 100
    Returns rounded to 2 decimal places, or 0 if past is 0.
    """
    if not past or past == 0:
        return 0
    return round(((current - past) / past) * 100, 2)


async def get_all_index_quote() -> dict:
    """
    Get comprehensive quote data for all indices from NSE India.
    
    This function fetches all indices with OHLC, valuation metrics (PE/PB/DY),
    and historical comparison data (1 week, 30 days, 365 days ago).
    
    Returns:
        A dictionary with:
        - timestamp: Data timestamp
        - indexQuote: List of index objects with:
            - indexName: Full name of the index
            - date: Trading date in YYYY-MM-DD format
            - open: Opening price
            - high: Day's high
            - low: Day's low
            - ltp: Last traded price
            - prevClose: Previous close
            - change: Absolute change from previous close
            - percentChange: Percent change from previous close
            - pe: Price to Earnings ratio
            - pb: Price to Book ratio
            - dy: Dividend Yield
            - oneWeekAgoDate: Date 1 week ago (YYYY-MM-DD)
            - oneWeekAgoVal: Value 1 week ago
            - oneWeekAgoPercentChange: Percent change from 1 week ago
            - 30dAgoDate: Date 30 days ago (YYYY-MM-DD)
            - 30dAgoVal: Value 30 days ago
            - 30dAgoPercentChange: Percent change from 30 days ago
            - 365dAgoDate: Date 365 days ago (YYYY-MM-DD)
            - 365dAgoVal: Value 365 days ago
            - 365dAgoPercentChange: Percent change from 365 days ago
        
        Returns empty dict {} if the API call fails.
        
    Example:
        >>> from niftyterminal import get_all_index_quote
        >>> data = get_all_index_quote()
        >>> print(data['indexQuote'][0]['indexName'])
        'NIFTY 50'
    """
    data = await afetch(ALL_INDICES_URL)
    
    if not data:
        return {}
    
    raw_indices = data.get("data", [])
    
    if not raw_indices:
        return {}
    
    index_list = []
    timestamp = data.get("timestamp", "")
    
    for idx in raw_indices:
        index_name = idx.get("index", "")
        ltp = idx.get("last", 0)
        
        # Get historical values
        one_week_ago_val = idx.get("oneWeekAgoVal", 0)
        one_month_ago_val = idx.get("oneMonthAgoVal", 0)
        one_year_ago_val = idx.get("oneYearAgoVal", 0)
        
        # Calculate percent changes manually
        one_week_pct = _calc_percent_change(ltp, one_week_ago_val)
        one_month_pct = _calc_percent_change(ltp, one_month_ago_val)
        one_year_pct = _calc_percent_change(ltp, one_year_ago_val)
        
        # Parse historical dates to YYYY-MM-DD
        one_week_ago_date = _parse_date_to_ymd(idx.get("oneWeekAgo", ""))
        date_30d_ago = _parse_date_to_ymd(idx.get("date30dAgo", ""))
        date_365d_ago = _parse_date_to_ymd(idx.get("date365dAgo", ""))
        
        # Get trading date from timestamp
        trade_date = _parse_timestamp_to_date(timestamp)
        
        index_list.append({
            "indexName": index_name,
            "date": trade_date,
            "open": idx.get("open", 0),
            "high": idx.get("high", 0),
            "low": idx.get("low", 0),
            "ltp": ltp,
            "prevClose": idx.get("previousClose", 0),
            "change": idx.get("variation", 0),
            "percentChange": idx.get("percentChange", 0),
            "pe": idx.get("pe", ""),
            "pb": idx.get("pb", ""),
            "dy": idx.get("dy", ""),
            "oneWeekAgoDate": one_week_ago_date,
            "oneWeekAgoVal": one_week_ago_val,
            "oneWeekAgoPercentChange": one_week_pct,
            "30dAgoDate": date_30d_ago,
            "30dAgoVal": one_month_ago_val,
            "30dAgoPercentChange": one_month_pct,
            "365dAgoDate": date_365d_ago,
            "365dAgoVal": one_year_ago_val,
            "365dAgoPercentChange": one_year_pct,
        })
    
    return {
        "timestamp": timestamp,
        "indexQuote": index_list,
    }



# NSE Equity Master API endpoint (for index list)
INDEX_MASTER_URL = "https://www.nseindia.com/api/equity-masterOR"

# Categories to skip (not actual indices)
SKIP_CATEGORIES = {"Others"}

# Manual symbol overrides for indices where NSE API returns truncated/wrong symbols
# that don't work with Nifty Indices API
SYMBOL_OVERRIDES = {
    "NIFTY200 QUALITY 30": "NIFTY200 QUALITY 30",  # NSE returns "NIFTY200 QUALTY30" which doesn't work
}

# Manual subType overrides for indices incorrectly categorized by NSE API
SUBTYPE_OVERRIDES = {
    "NIFTY BANK": "Sectoral Market Indices",
    "NIFTY FINANCIAL SERVICES": "Sectoral Market Indices",
}


async def get_index_list() -> dict:
    """
    Get the master list of all indices from NSE India.
    """
    import asyncio
    
    # Fetch both concurrently
    all_indices_data, data = await asyncio.gather(
        afetch(ALL_INDICES_URL),
        afetch(INDEX_MASTER_URL)
    )
    
    # Build mapping: indexName -> indexSymbol
    symbol_map = {}
    if all_indices_data and "data" in all_indices_data:
        for item in all_indices_data["data"]:
            index_name = item.get("index", "")
            index_symbol = item.get("indexSymbol", "")
            if index_name and index_symbol:
                symbol_map[index_name] = index_symbol
    
    if not data:
        return {}
    
    # Get the list of derivatives-eligible indices
    derivatives_list = set(data.get("Indices Eligible in Derivatives", []))
    
    index_list = []
    seen_indices = set()  # Track to avoid duplicates
    
    # Process each category
    for category, indices in data.items():
        # Skip non-index categories
        if category in SKIP_CATEGORIES:
            continue
        
        # Skip the derivatives list itself (we use it for eligibility checking)
        if category == "Indices Eligible in Derivatives":
            # Add these indices with "Broad Market Indices" as subType
            # (they're the major tradeable indices)
            for index_name in indices:
                if index_name not in seen_indices:
                    seen_indices.add(index_name)
                    # Use override if available, otherwise use symbol_map
                    resolved_symbol = SYMBOL_OVERRIDES.get(index_name, symbol_map.get(index_name, index_name))
                    # Use subType override if available
                    resolved_subtype = SUBTYPE_OVERRIDES.get(index_name, "Broad Market Indices")
                    index_list.append({
                        "indexName": index_name,
                        "indexSymbol": resolved_symbol,
                        "subType": resolved_subtype,
                        "derivativesEligiblity": True,
                    })
            continue
        
        # Process regular categories
        for index_name in indices:
            if index_name not in seen_indices:
                seen_indices.add(index_name)
                # Use override if available, otherwise use symbol_map
                resolved_symbol = SYMBOL_OVERRIDES.get(index_name, symbol_map.get(index_name, index_name))
                index_list.append({
                    "indexName": index_name,
                    "indexSymbol": resolved_symbol,
                    "subType": category,
                    "derivativesEligiblity": index_name in derivatives_list,
                })
    
    return {
        "indexList": index_list,
    }


def _normalize_nifty_date(date_str: str) -> str:
    """
    Normalize date from Nifty Indices API format to YYYY-MM-DD.
    
    Handles:
    - DD MMM YYYY (e.g., "03 Jan 2025") -> "2025-01-03"
    - DD-MMM-YYYY (e.g., "03-Jan-2025") -> "2025-01-03"
    - Already in YYYY-MM-DD -> returns as-is
    """
    from datetime import datetime
    
    if not date_str:
        return ""
    
    # Try "DD MMM YYYY" format first (Nifty Indices API response format)
    try:
        dt = datetime.strptime(date_str.strip(), "%d %b %Y")
        return dt.strftime("%Y-%m-%d")
    except ValueError:
        pass
    
    # Try "DD-MMM-YYYY" format 
    try:
        dt = datetime.strptime(date_str.strip().upper(), "%d-%b-%Y")
        return dt.strftime("%Y-%m-%d")
    except ValueError:
        pass
    
    # Already in YYYY-MM-DD format
    try:
        datetime.strptime(date_str, "%Y-%m-%d")
        return date_str
    except ValueError:
        pass
    
    return date_str


async def get_index_historical_data(
    index_symbol: str,
    start_date: str,
    end_date: str = None
) -> dict:
    """
    Get historical OHLC, valuation, and total returns data for an index.
    """
    import asyncio
    from datetime import datetime
    from niftyterminal.core import NiftyIndicesSession
    
    # Parse dates (YYYY-MM-DD format)
    try:
        start_dt = datetime.strptime(start_date, "%Y-%m-%d")
    except ValueError:
        return {}
    
    if end_date:
        try:
            end_dt = datetime.strptime(end_date, "%Y-%m-%d")
        except ValueError:
            return {}
    else:
        end_dt = datetime.now()
    
    # Validate date range
    if start_dt > end_dt:
        return {}
    
    # Convert to Nifty Indices API date format (DD-Mon-YYYY)
    nifty_start_date = start_dt.strftime("%d-%b-%Y")
    nifty_end_date = end_dt.strftime("%d-%b-%Y")
    
    # Data containers
    history_data = {}
    pe_pb_div_data = {}
    total_returns_data = {}
    
    # Fetch all three data sources in parallel using NiftyIndicesSession
    async with NiftyIndicesSession() as session:
        # Fetch concurrently
        results = await asyncio.gather(
            session.afetch_history(index_symbol, nifty_start_date, nifty_end_date),
            session.afetch_pe_pb_div(index_symbol, nifty_start_date, nifty_end_date),
            session.afetch_total_returns(index_symbol, nifty_start_date, nifty_end_date),
            return_exceptions=True
        )
        
        # Process history
        if not isinstance(results[0], Exception) and results[0]:
            for item in results[0]:
                raw_date = item.get("HistoricalDate", "")
                normalized_date = _normalize_nifty_date(raw_date)
                if normalized_date:
                    history_data[normalized_date] = {
                        "open": item.get("OPEN", 0),
                        "high": item.get("HIGH", 0),
                        "low": item.get("LOW", 0),
                        "close": item.get("CLOSE", 0),
                    }
        
        # Process PE/PB/Div
        if not isinstance(results[1], Exception) and results[1]:
            for item in results[1]:
                # PE/PB API uses "DATE" field
                raw_date = item.get("DATE", "")
                normalized_date = _normalize_nifty_date(raw_date)
                if normalized_date:
                    pe_pb_div_data[normalized_date] = {
                        "PE": item.get("pe", None),
                        "PB": item.get("pb", None),
                        "divYield": item.get("divYield", None),
                    }
        
        # Process Total Returns
        if not isinstance(results[2], Exception) and results[2]:
            for item in results[2]:
                # Total Returns API uses "Date" field
                raw_date = item.get("Date", "")
                normalized_date = _normalize_nifty_date(raw_date)
                if normalized_date:
                    total_returns_data[normalized_date] = {
                        "totalReturnsIndex": item.get("TotalReturnsIndex", None),
                    }
    
    if not history_data:
        return {}
    
    # Merge all data by date
    all_data = []
    
    for date_key in sorted(history_data.keys(), reverse=True):
        history = history_data[date_key]
        pe_pb = pe_pb_div_data.get(date_key, {})
        total_ret = total_returns_data.get(date_key, {})
        
        all_data.append({
            "indexSymbol": index_symbol,
            "date": date_key,
            "open": history["open"],
            "high": history["high"],
            "low": history["low"],
            "close": history["close"],
            "PE": pe_pb.get("PE"),
            "PB": pe_pb.get("PB"),
            "divYield": pe_pb.get("divYield"),
            "totalReturnsIndex": total_ret.get("totalReturnsIndex"),
        })
    
    return {
        "indexData": all_data,
    }


# NSE Index Stocks API endpoint
INDEX_STOCKS_URL = "https://www.nseindia.com/api/equity-stockIndices"


def _parse_date(date_str: str) -> str:
    """
    Parse date from timestamp format to YYYY-MM-DD.
    
    Handles: "02-Jan-2026 16:00:00" -> "2026-01-02"
    """
    from datetime import datetime
    
    if not date_str:
        return ""
    
    try:
        # Parse "DD-Mon-YYYY HH:MM:SS" format
        dt = datetime.strptime(date_str.split()[0], "%d-%b-%Y")
        return dt.strftime("%Y-%m-%d")
    except (ValueError, IndexError):
        return ""


async def get_index_stocks(index_name: str) -> dict:
    """
    Get the list of stocks in an index from NSE India.
    """
    from urllib.parse import quote
    
    # Build URL with URL-encoded index name
    url = f"{INDEX_STOCKS_URL}?index={quote(index_name)}"
    
    data = await afetch(url)
    
    if not data:
        return {}
    
    index_name_resp = data.get("name", "")
    timestamp = data.get("timestamp", "")
    raw_stocks = data.get("data", [])
    
    if not raw_stocks:
        return {}
    
    # Parse date from timestamp
    date = _parse_date(timestamp)
    
    # Process stocks (skip first item which is the index summary)
    stock_list = []
    
    for item in raw_stocks:
        # Skip the index summary row (it has same symbol as index name)
        if item.get("symbol") == index_name_resp:
            continue
        
        meta = item.get("meta", {})
        
        if not meta:
            continue
        
        stock_list.append({
            "symbol": meta.get("symbol", ""),
            "companyName": meta.get("companyName", ""),
            "isin": meta.get("isin", ""),
        })
    
    return {
        "indexName": index_name_resp,
        "date": date,
        "stockList": stock_list,
    }
