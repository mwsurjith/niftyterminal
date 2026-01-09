"""
Commodity API functions.

This module provides functions to fetch commodity-related data from NSE India.
"""

from datetime import datetime
from niftyterminal.core import afetch


# NSE Commodity API endpoints
COMMODITY_MASTER_URL = "https://www.nseindia.com/api/historical-spot-price-master"
COMMODITY_HISTORY_URL = "https://www.nseindia.com/api/historical-spot-price"


def _parse_date(date_str: str) -> str:
    """
    Convert date from DD-Mon-YYYY format to YYYY-MM-DD.
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
    """
    if not date_str:
        return ""
    
    try:
        dt = datetime.strptime(date_str.strip(), "%Y-%m-%d")
        return dt.strftime("%d-%m-%Y")
    except ValueError:
        return ""


async def get_commodity_list() -> dict:
    """
    Get the list of all commodity symbols from NSE India asynchronously.
    """
    data = await afetch(COMMODITY_MASTER_URL)
    
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


async def get_commodity_historical_data(symbol: str, start_date: str, end_date: str = None) -> dict:
    """
    Get historical spot price data for a commodity asynchronously.
    """
    import asyncio
    from datetime import timedelta
    from niftyterminal.core import AsyncNSESession
    
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
    
    # Generate date batches
    date_batches = []
    current_start = start_dt
    
    while current_start < end_dt:
        current_end = min(current_start + timedelta(days=MAX_DAYS_PER_REQUEST), end_dt)
        date_batches.append((current_start, current_end))
        current_start = current_end + timedelta(days=1)
    
    # Fetch data for each batch
    all_records = {}
    
    async with AsyncNSESession() as nse:
        tasks = []
        for batch_start, batch_end in date_batches:
            from_date = batch_start.strftime("%d-%m-%Y")
            to_date = batch_end.strftime("%d-%m-%Y")
            url = f"{COMMODITY_HISTORY_URL}?fromDate={from_date}&toDate={to_date}&symbol={symbol}"
            tasks.append(nse.fetch(url))
        
        batch_results = await asyncio.gather(*tasks)
        
        for batch_data in batch_results:
            if not batch_data:
                continue
            
            raw_data = batch_data.get("data", [])
            for item in raw_data:
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
                    all_records[parsed_date] = {
                        "symbol": item.get("Symbol", ""),
                        "unit": item.get("Unit", ""),
                        "spotPrice1": spot_price1,
                        "spotPrice2": spot_price2,
                        "date": parsed_date,
                    }
    
    if not all_records:
        return {}
    
    commodity_data = [all_records[d] for d in sorted(all_records.keys(), reverse=True)]
    
    return {
        "commodityData": commodity_data,
    }
