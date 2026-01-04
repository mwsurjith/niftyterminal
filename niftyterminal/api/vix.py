"""
VIX API functions.

This module provides functions to fetch India VIX data from NSE India.
"""

from niftyterminal.core import fetch


# NSE VIX Historical Data API endpoint
VIX_HISTORY_URL = "https://www.nseindia.com/api/historicalOR/vixhistory"

# Maximum days per API request (NSE limit is ~365 days)
MAX_DAYS_PER_REQUEST = 364


def _normalize_date(date_str: str) -> str:
    """
    Normalize date from DD-MMM-YYYY to YYYY-MM-DD format.
    """
    from datetime import datetime
    
    if not date_str:
        return ""
    
    # Try DD-MMM-YYYY format (API response format)
    try:
        dt = datetime.strptime(date_str.upper(), "%d-%b-%Y")
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


def get_vix_historical_data(
    start_date: str,
    end_date: str = None
) -> dict:
    """
    Get historical India VIX data from NSE India.
    
    This function fetches historical VIX OHLC data.
    For date ranges > 365 days, it automatically fetches in batches
    and stitches the results together.
    
    Args:
        start_date: Start date in YYYY-MM-DD format (e.g., "2024-01-01")
        end_date: End date in YYYY-MM-DD format (e.g., "2024-12-31").
                  If not provided, defaults to today's date.
    
    Returns:
        A dictionary with:
        - vixData: List of historical VIX data points with:
            - indexName: Name of the index ("INDIA VIX")
            - date: Date in YYYY-MM-DD format
            - open: Opening value
            - high: Highest value
            - low: Lowest value
            - close: Closing value
        
        Returns empty dict {} if the API call fails.
        
    Example:
        >>> from niftyterminal import get_vix_historical_data
        >>> data = get_vix_historical_data("2025-01-01", "2025-04-16")
        >>> print(data['vixData'][0])
        {'indexName': 'INDIA VIX', 'date': '2025-04-16', 'open': 16.125, ...}
    """
    from datetime import datetime, timedelta
    
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
    
    # Generate date batches if range > MAX_DAYS_PER_REQUEST
    date_batches = []
    current_start = start_dt
    
    while current_start < end_dt:
        current_end = min(current_start + timedelta(days=MAX_DAYS_PER_REQUEST), end_dt)
        date_batches.append((current_start, current_end))
        current_start = current_end + timedelta(days=1)
    
    # Fetch VIX data for each batch
    vix_data = {}  # date -> {indexName, open, high, low, close}
    
    for batch_start, batch_end in date_batches:
        # Format dates for API (DD-MM-YYYY)
        from_date = batch_start.strftime("%d-%m-%Y")
        to_date = batch_end.strftime("%d-%m-%Y")
        
        # Build URL
        url = f"{VIX_HISTORY_URL}?from={from_date}&to={to_date}"
        
        batch_data = fetch(url)
        
        if batch_data and "data" in batch_data:
            for item in batch_data["data"]:
                raw_date = item.get("EOD_TIMESTAMP", "")
                normalized_date = _normalize_date(raw_date)
                
                if normalized_date:
                    vix_data[normalized_date] = {
                        "indexName": item.get("EOD_INDEX_NAME", ""),
                        "open": item.get("EOD_OPEN_INDEX_VAL", 0),
                        "high": item.get("EOD_HIGH_INDEX_VAL", 0),
                        "low": item.get("EOD_LOW_INDEX_VAL", 0),
                        "close": item.get("EOD_CLOSE_INDEX_VAL", 0),
                    }
    
    if not vix_data:
        return {}
    
    # Build output sorted by date (newest first)
    all_data = []
    
    for date_key in sorted(vix_data.keys(), reverse=True):
        data = vix_data[date_key]
        all_data.append({
            "indexName": data["indexName"],
            "date": date_key,
            "open": data["open"],
            "high": data["high"],
            "low": data["low"],
            "close": data["close"],
        })
    
    return {
        "vixData": all_data,
    }
