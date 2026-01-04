"""
Commodity API functions.

This module provides functions to fetch commodity-related data from NSE India.
"""

from datetime import datetime
from niftyterminal.core import fetch


# NSE Commodity API endpoints
COMMODITY_MASTER_URL = "https://www.nseindia.com/api/historical-spot-price-master"
COMMODITY_HISTORY_URL = "https://www.nseindia.com/api/historical-spot-price"


def _parse_date(date_str: str) -> str:
    """
    Convert date from DD-Mon-YYYY format to YYYY-MM-DD.
    e.g., "02-JAN-2026" -> "2026-01-02"
    """
    if not date_str:
        return ""
    
    try:
        dt = datetime.strptime(date_str.strip(), "%d-%b-%Y")
        return dt.strftime("%Y-%m-%d")
    except ValueError:
        return ""


def _format_date_for_api(date_str: str) -> str:
    """
    Convert date from YYYY-MM-DD to DD-MM-YYYY format for API.
    e.g., "2026-01-02" -> "02-01-2026"
    """
    if not date_str:
        return ""
    
    try:
        dt = datetime.strptime(date_str.strip(), "%Y-%m-%d")
        return dt.strftime("%d-%m-%Y")
    except ValueError:
        return ""


def get_commodity_list() -> dict:
    """
    Get the list of all commodity symbols from NSE India.
    
    Returns:
        A dictionary with:
        - commodityList: List of commodity objects with:
            - symbol: Commodity symbol (e.g., "GOLD", "SILVER", "CRUDEOIL")
        
        Returns empty dict {} if the API call fails.
        
    Example:
        >>> from niftyterminal import get_commodity_list
        >>> data = get_commodity_list()
        >>> print([c['symbol'] for c in data['commodityList']])
        ['ALUMINI', 'ALUMINIUM', 'BRCRUDE', 'COPPER', 'CRUDEOIL', ...]
    """
    data = fetch(COMMODITY_MASTER_URL)
    
    if not data:
        return {}
    
    # API returns a list directly
    if not isinstance(data, list):
        return {}
    
    commodity_list = []
    
    for item in data:
        symbol = item.get("Symbol", "")
        if symbol:
            commodity_list.append({
                "symbol": symbol,
            })
    
    return {
        "commodityList": commodity_list,
    }


def get_commodity_historical_data(symbol: str, start_date: str, end_date: str = None) -> dict:
    """
    Get historical spot price data for a commodity.
    
    For date ranges exceeding 1 year, data is fetched in batches and stitched together.
    
    Args:
        symbol: Commodity symbol (e.g., "GOLD", "SILVER", "CRUDEOIL")
        start_date: Start date in YYYY-MM-DD format
        end_date: End date in YYYY-MM-DD format (defaults to today)
    
    Returns:
        A dictionary with:
        - commodityData: List of price records with:
            - symbol: Commodity symbol
            - unit: Unit of measurement (e.g., "1 Grams", "1 Kg")
            - spotPrice1: First spot price
            - spotPrice2: Second spot price
            - date: Date in YYYY-MM-DD format
        
        Returns empty dict {} if the API call fails.
        
    Example:
        >>> from niftyterminal import get_commodity_historical_data
        >>> data = get_commodity_historical_data("GOLD1G", "2025-12-28", "2026-01-04")
        >>> print(data['commodityData'][0])
        {'symbol': 'GOLD1G', 'unit': '1 Grams', 'spotPrice1': 13318, 'spotPrice2': 13355, 'date': '2026-01-02'}
    """
    from datetime import timedelta
    
    # Maximum days per API request (NSE limit)
    MAX_DAYS_PER_REQUEST = 364
    
    # Parse dates
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
    
    # Fetch data for each batch
    all_records = {}  # Use dict to deduplicate by date
    
    for batch_start, batch_end in date_batches:
        # Format dates for API (DD-MM-YYYY)
        from_date = batch_start.strftime("%d-%m-%Y")
        to_date = batch_end.strftime("%d-%m-%Y")
        
        # Build URL
        url = f"{COMMODITY_HISTORY_URL}?fromDate={from_date}&toDate={to_date}&symbol={symbol}"
        
        data = fetch(url)
        
        if not data:
            continue
        
        raw_data = data.get("data", [])
        
        for item in raw_data:
            # Parse spot prices as integers
            try:
                spot_price1 = int(item.get("SpotPrice1", "0"))
            except (ValueError, TypeError):
                spot_price1 = 0
            
            try:
                spot_price2 = int(item.get("SpotPrice2", "0"))
            except (ValueError, TypeError):
                spot_price2 = 0
            
            parsed_date = _parse_date(item.get("UpdatedDate", ""))
            
            if parsed_date:
                # Use date as key to avoid duplicates
                all_records[parsed_date] = {
                    "symbol": item.get("Symbol", ""),
                    "unit": item.get("Unit", ""),
                    "spotPrice1": spot_price1,
                    "spotPrice2": spot_price2,
                    "date": parsed_date,
                }
    
    if not all_records:
        return {}
    
    # Sort by date descending (most recent first)
    commodity_data = [all_records[d] for d in sorted(all_records.keys(), reverse=True)]
    
    return {
        "commodityData": commodity_data,
    }
