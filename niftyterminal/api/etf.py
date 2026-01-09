"""
ETF API functions.

This module provides functions to fetch ETF-related data from NSE India.
"""

import re
from niftyterminal.core import fetch


# NSE ETF API endpoint
ETF_URL = "https://www.nseindia.com/api/etf"


def _normalize_index_name(name: str) -> str:
    """
    Normalize index name to uppercase with underscores.
    e.g., "Nifty 50" -> "NIFTY_50"
    """
    # Remove common prefixes/suffixes
    name = re.sub(r'\bIndex\b', '', name, flags=re.IGNORECASE)
    name = re.sub(r'\bETF\b', '', name, flags=re.IGNORECASE)
    name = re.sub(r'\bTotal Return\b', '', name, flags=re.IGNORECASE)
    name = re.sub(r'\bTRI\b', '', name, flags=re.IGNORECASE)
    name = re.sub(r'\bEqual Weight\b', '', name, flags=re.IGNORECASE)
    
    # Clean up and normalize
    name = re.sub(r'[^\w\s]', ' ', name)  # Remove special chars
    name = re.sub(r'\s+', ' ', name).strip()  # Collapse spaces
    name = name.upper().replace(' ', '_')
    
    # Remove trailing underscores
    name = re.sub(r'_+$', '', name)
    name = re.sub(r'^_+', '', name)
    
    return name if name else None


def _detect_index_variant(assets: str) -> str:
    """
    Detect index variant from asset string.
    """
    assets_lower = assets.lower()
    
    if 'total return' in assets_lower or ' tri' in assets_lower or assets_lower.endswith('tri'):
        return "TRI"
    if 'equal weight' in assets_lower:
        return "EqualWeight"
    if 'momentum' in assets_lower:
        return "Momentum"
    if 'quality' in assets_lower:
        return "Quality"
    if 'value' in assets_lower:
        return "Value"
    if 'low vol' in assets_lower or 'low volatility' in assets_lower:
        return "LowVol"
    if 'alpha' in assets_lower:
        return "Alpha"
    
    return None


def _parse_asset(assets: str) -> dict:
    """
    Parse the inconsistent 'assets' field into structured assetType, 
    underlyingAsset, and indexVariant.
    
    underlyingAsset for equity indices will match the indexSymbol format 
    from get_index_list (e.g., "NIFTY 50", "NIFTY BANK").
    """
    if not assets:
        return {
            "assetType": None,
            "underlyingAsset": None,
            "indexVariant": None,
        }
    
    assets_lower = assets.lower()
    
    # 1. Commodity Detection (Gold/Silver)
    if any(kw in assets_lower for kw in ['silver', 'gold', 'commodity']):
        if 'silver' in assets_lower:
            return {
                "assetType": "Commodity",
                "underlyingAsset": "SILVER",
                "indexVariant": None,
            }
        else:
            return {
                "assetType": "Commodity",
                "underlyingAsset": "GOLD",
                "indexVariant": None,
            }
    
    # 2. Liquid/Debt Detection
    if any(kw in assets_lower for kw in ['liquid', '1d rate', 'overnight']):
        underlying = "NIFTY 1D RATE INDEX"
        if 'bse' in assets_lower or 's&p bse' in assets_lower:
            underlying = "BSE LIQUID RATE"
        elif 'crisil' in assets_lower:
            underlying = "CRISIL OVERNIGHT"
        
        return {
            "assetType": "Liquid",
            "underlyingAsset": underlying,
            "indexVariant": None,
        }
    
    if any(kw in assets_lower for kw in ['g-sec', 'gsec', 'gilt', 'bond', 'sdl', 'bharat bond']):
        underlying = None
        if 'bharat bond' in assets_lower or 'bharat' in assets_lower:
            year_match = re.search(r'20(\d{2})', assets)
            if year_match:
                underlying = f"BHARATBOND-APR{year_match.group(1)}"
            else:
                underlying = "BHARATBOND"
        elif '10' in assets_lower or '10 yr' in assets_lower or '10 year' in assets_lower:
            underlying = "NIFTY GS 10YR"
        elif '8-13' in assets_lower:
            underlying = "NIFTY GS 8 13YR"
        elif '5' in assets_lower and ('yr' in assets_lower or 'year' in assets_lower):
            underlying = "NIFTY GS 5YR"
        elif 'sdl' in assets_lower:
            underlying = "NIFTY SDL"
        else:
            underlying = "NIFTY GSEC"
        
        return {
            "assetType": "DebtIndex",
            "underlyingAsset": underlying,
            "indexVariant": None,
        }
    
    # 3. International Index Detection
    if any(kw in assets_lower for kw in ['nasdaq', 'hang seng', 'nyse', 's&p 500', 'msci']):
        underlying = None
        if 'nasdaq' in assets_lower:
            if 'q-50' in assets_lower:
                underlying = "NASDAQ Q50"
            elif 'fang' in assets_lower:
                underlying = "NYSE FANG"
            else:
                underlying = "NASDAQ 100"
        elif 'hang seng' in assets_lower:
            if 'tech' in assets_lower:
                underlying = "HANG SENG TECH"
            else:
                underlying = "HANG SENG"
        elif 'nyse' in assets_lower:
            underlying = "NYSE FANG"
        elif 's&p 500' in assets_lower:
            underlying = "SP 500"
        elif 'msci' in assets_lower:
            underlying = "MSCI INDIA"
        
        variant = _detect_index_variant(assets)
        
        return {
            "assetType": "International",
            "underlyingAsset": underlying,
            "indexVariant": variant,
        }
    
    # 4. Shariah
    if 'shariah' in assets_lower:
        if '50' in assets_lower:
            return {
                "assetType": "EquityIndex",
                "underlyingAsset": "NIFTY50 SHARIAH",
                "indexVariant": None,
            }
        elif '500' in assets_lower:
            return {
                "assetType": "EquityIndex",
                "underlyingAsset": "NIFTY500 SHARIAH",
                "indexVariant": None,
            }
        else:
            return {
                "assetType": "EquityIndex",
                "underlyingAsset": "NIFTY SHARIAH 25",
                "indexVariant": None,
            }
    
    # 5. CPSE ETF
    if 'cpse' in assets_lower:
        return {
            "assetType": "EquityIndex",
            "underlyingAsset": "NIFTY CPSE",
            "indexVariant": None,
        }
    
    # 6. Default: Equity Index - Parse index name
    variant = _detect_index_variant(assets)
    underlying = None
    
    # BSE indices
    if 'sensex' in assets_lower or 'bse' in assets_lower:
        if 'sensex next 50' in assets_lower:
            underlying = "SENSEX NEXT 50"
        elif 'sensex next 30' in assets_lower:
            underlying = "SENSEX NEXT 30"
        elif 'sensex' in assets_lower:
            underlying = "SENSEX"
        elif 'bse 500' in assets_lower:
            underlying = "BSE 500"
        elif 'bse 200' in assets_lower:
            underlying = "BSE 200"
        elif 'bse psu bank' in assets_lower:
            underlying = "BSE PSU BANK"
        elif 'bse power' in assets_lower:
            underlying = "BSE POWER"
        elif 'bse capital' in assets_lower:
            underlying = "BSE CAPITAL MARKETS"
        elif 'bse infra' in assets_lower:
            underlying = "BSE INFRASTRUCTURE"
        elif 'bse healthcare' in assets_lower or 'bse health' in assets_lower:
            underlying = "BSE HEALTHCARE"
        elif 'bharat 22' in assets_lower:
            underlying = "BHARAT 22"
        elif 'bse ipo' in assets_lower:
            underlying = "BSE IPO"
        elif 'bse midcap' in assets_lower:
            underlying = "BSE MIDCAP SELECT"
        elif 'bse dividend' in assets_lower:
            underlying = "BSE 500 DIVIDEND"
        else:
            underlying = _normalize_index_name(assets)
    
    # Nifty indices - Match actual indexSymbol format from get_index_list
    elif 'nifty' in assets_lower:
        if 'nifty 50' in assets_lower and 'next' not in assets_lower:
            if 'value 20' in assets_lower:
                underlying = "NIFTY50 VALUE 20"
            elif 'equal' in assets_lower:
                underlying = "NIFTY50 EQL WGT"
            else:
                underlying = "NIFTY 50"
        elif 'nifty next 50' in assets_lower or 'nifty next50' in assets_lower:
            underlying = "NIFTY NEXT 50"
        elif 'nifty 100' in assets_lower:
            if 'low vol' in assets_lower:
                underlying = "NIFTY100 LOWVOL30"
            elif 'quality' in assets_lower:
                underlying = "NIFTY100 QUALTY30"
            elif 'equal' in assets_lower:
                underlying = "NIFTY100 EQL WGT"
            elif 'esg' in assets_lower:
                if 'enhanced' in assets_lower:
                    underlying = "NIFTY100 ENH ESG"
                else:
                    underlying = "NIFTY100 ESG"
            elif 'alpha' in assets_lower:
                underlying = "NIFTY100 ALPHA 30"
            else:
                underlying = "NIFTY 100"
        elif 'nifty 200' in assets_lower:
            if 'momentum' in assets_lower:
                underlying = "NIFTY200MOMENTM30"
            elif 'quality' in assets_lower:
                underlying = "NIFTY200 QUALITY 30"
            elif 'alpha' in assets_lower:
                underlying = "NIFTY200 ALPHA 30"
            elif 'value' in assets_lower:
                underlying = "NIFTY200 VALUE 30"
            else:
                underlying = "NIFTY 200"
        elif 'nifty 500' in assets_lower:
            if 'momentum 50' in assets_lower:
                underlying = "NIFTY500MOMENTM50"
            elif 'low vol' in assets_lower:
                underlying = "NIFTY500 LOWVOL50"
            elif 'multicap' in assets_lower:
                if 'momentum' in assets_lower or 'quality' in assets_lower:
                    underlying = "NIFTY MULTI MQ 50"
                else:
                    underlying = "NIFTY500 MULTICAP"
            elif 'flexicap' in assets_lower:
                underlying = "NIFTY500 FLEXICAP"
            elif 'value' in assets_lower:
                underlying = "NIFTY500 VALUE 50"
            elif 'quality' in assets_lower:
                underlying = "NIFTY500 QLTY50"
            elif 'equal' in assets_lower:
                underlying = "NIFTY500 EW"
            elif 'health' in assets_lower:
                underlying = "NIFTY500 HEALTH"
            else:
                underlying = "NIFTY 500"
        elif 'midcap 150' in assets_lower:
            if 'momentum' in assets_lower:
                underlying = "NIFTYM150MOMNTM50"
            elif 'quality' in assets_lower:
                underlying = "NIFTY M150 QLTY50"
            else:
                underlying = "NIFTY MIDCAP 150"
        elif 'midcap 100' in assets_lower:
            underlying = "NIFTY MIDCAP 100"
        elif 'midcap 50' in assets_lower:
            underlying = "NIFTY MIDCAP 50"
        elif 'midcap select' in assets_lower:
            underlying = "NIFTY MID SELECT"
        elif 'smallcap 250' in assets_lower:
            if 'momentum' in assets_lower:
                underlying = "NIFTYSML250MQ 100"
            elif 'quality' in assets_lower:
                underlying = "NIFTY SML250 Q50"
            else:
                underlying = "NIFTY SMLCAP 250"
        elif 'smallcap 100' in assets_lower:
            underlying = "NIFTY SMLCAP 100"
        elif 'largemidcap' in assets_lower or 'large midcap' in assets_lower:
            underlying = "NIFTY LARGEMID250"
        elif 'bank' in assets_lower and 'psu' not in assets_lower and 'private' not in assets_lower:
            underlying = "NIFTY BANK"
        elif 'psu bank' in assets_lower:
            underlying = "NIFTY PSU BANK"
        elif 'private bank' in assets_lower:
            underlying = "NIFTY PVT BANK"
        elif 'financial' in assets_lower:
            if 'ex-bank' in assets_lower or 'ex bank' in assets_lower:
                underlying = "NIFTY FINSEREXBNK"
            elif '25/50' in assets_lower or '25 50' in assets_lower:
                underlying = "NIFTY FINSRV25 50"
            else:
                underlying = "NIFTY FIN SERVICE"
        elif 'it' in assets_lower.split() or 'it index' in assets_lower:
            underlying = "NIFTY IT"
        elif 'pharma' in assets_lower:
            underlying = "NIFTY PHARMA"
        elif 'healthcare' in assets_lower or 'health' in assets_lower:
            underlying = "NIFTY HEALTHCARE"
        elif 'auto' in assets_lower:
            underlying = "NIFTY AUTO"
        elif 'fmcg' in assets_lower:
            underlying = "NIFTY FMCG"
        elif 'metal' in assets_lower:
            underlying = "NIFTY METAL"
        elif 'energy' in assets_lower:
            underlying = "NIFTY ENERGY"
        elif 'infra' in assets_lower:
            if 'logistics' in assets_lower:
                underlying = "NIFTY INFRALOG"
            else:
                underlying = "NIFTY INFRA"
        elif 'realty' in assets_lower:
            underlying = "NIFTY REALTY"
        elif 'commodities' in assets_lower:
            underlying = "NIFTY COMMODITIES"
        elif 'consumption' in assets_lower:
            if 'new age' in assets_lower:
                underlying = "NIFTY NEW CONSUMP"
            else:
                underlying = "NIFTY CONSUMPTION"
        elif 'mnc' in assets_lower:
            underlying = "NIFTY MNC"
        elif 'pse' in assets_lower:
            underlying = "NIFTY PSE"
        elif 'dividend' in assets_lower:
            underlying = "NIFTY DIV OPPS 50"
        elif 'alpha 50' in assets_lower:
            underlying = "NIFTY ALPHA 50"
        elif 'alpha low' in assets_lower:
            underlying = "NIFTY ALPHALOWVOL"
        elif 'defence' in assets_lower:
            underlying = "NIFTY IND DEFENCE"
        elif 'digital' in assets_lower:
            underlying = "NIFTY IND DIGITAL"
        elif 'manufacturing' in assets_lower:
            underlying = "NIFTY INDIA MFG"
        elif 'tourism' in assets_lower:
            underlying = "NIFTY IND TOURISM"
        elif 'railway' in assets_lower:
            underlying = "NIFTY INDIA RAILWAYS PSU"
        elif 'ev' in assets_lower or 'new age auto' in assets_lower:
            underlying = "NIFTY EV"
        elif 'capital market' in assets_lower:
            underlying = "NIFTY CAPITAL MKT"
        elif 'services' in assets_lower:
            underlying = "NIFTY SERV SECTOR"
        elif 'oil' in assets_lower or 'gas' in assets_lower:
            underlying = "NIFTY OIL AND GAS"
        elif 'chemicals' in assets_lower:
            underlying = "NIFTY CHEMICALS"
        elif 'growth' in assets_lower:
            underlying = "NIFTY GROWSECT 15"
        elif 'total market' in assets_lower:
            if 'momentum' in assets_lower:
                underlying = "NIFTY TMMQ 50"
            else:
                underlying = "NIFTY TOTAL MKT"
        elif 'top 10' in assets_lower:
            underlying = "NIFTY TOP 10 EW"
        elif 'top 15' in assets_lower:
            underlying = "NIFTY TOP 15 EW"
        elif 'top 20' in assets_lower:
            underlying = "NIFTY TOP 20 EW"
        elif 'midsmallcap' in assets_lower or 'mid small' in assets_lower:
            if 'momentum' in assets_lower or 'quality' in assets_lower:
                underlying = "NIFTYMS400 MQ 100"
            else:
                underlying = "NIFTY MIDSML 400"
        elif 'low vol' in assets_lower:
            if '50' in assets_lower:
                underlying = "NIFTY LOW VOL 50"
            else:
                underlying = "NIFTY QLTY LV 30"
        elif 'quality' in assets_lower:
            underlying = "NIFTY100 QUALTY30"
        elif 'high beta' in assets_lower:
            underlying = "NIFTY HIGHBETA 50"
        else:
            underlying = _normalize_index_name(assets)
    else:
        underlying = _normalize_index_name(assets)
    
    return {
        "assetType": "EquityIndex",
        "underlyingAsset": underlying,
        "indexVariant": variant,
    }


def _parse_timestamp_to_date(timestamp_str: str) -> str:
    """
    Extract date from timestamp format DD-Mon-YYYY HH:MM:SS to YYYY-MM-DD.
    """
    from datetime import datetime
    
    if not timestamp_str:
        return ""
    
    for fmt in ["%d-%b-%Y %H:%M:%S", "%d-%b-%Y %H:%M"]:
        try:
            dt = datetime.strptime(timestamp_str, fmt)
            return dt.strftime("%Y-%m-%d")
        except ValueError:
            continue
    
    return ""


def get_all_etfs() -> dict:
    """
    Get list of all ETFs from NSE India with cleaned asset categorization.
    
    This function fetches all ETFs and structures the inconsistent 'assets' field
    into clean categories for easy filtering.
    
    Returns:
        A dictionary with:
        - date: Trading date in YYYY-MM-DD format
        - etfs: List of ETF objects with:
            - symbol: ETF ticker symbol
            - companyName: Full name of the ETF
            - segment: Market segment (e.g., "EQUITY")
            - assetType: Category - "Commodity", "EquityIndex", "DebtIndex", "Liquid", "International"
            - underlyingAsset: Specific underlying asset (e.g., "GOLD", "NIFTY_50")
            - indexVariant: Variant - "TRI", "EqualWeight", "Momentum", etc. (null if N/A)
            - activeSeries: Active trading series
            - listingDate: Date of listing
            - isin: ISIN code
            - slb_isin: SLB ISIN code (if available)
            - debtSeries: Debt series (null if N/A)
            - isFNOSec, isCASec, isSLBSec, isDebtSec, isSuspended, isETFSec, 
              isDelisted, isMunicipalBond, isHybridSymbol: Boolean flags
        
        Returns empty dict {} if the API call fails.
        
    Example:
        >>> from niftyterminal import get_all_etfs
        >>> data = get_all_etfs()
        >>> # Filter for Gold ETFs
        >>> gold_etfs = [e for e in data['etfs'] if e['underlyingAsset'] == 'GOLD']
    """
    data = fetch(ETF_URL)
    
    if not data:
        return {}
    
    raw_etfs = data.get("data", [])
    timestamp = data.get("timestamp", "")
    
    if not raw_etfs:
        return {}
    
    date = _parse_timestamp_to_date(timestamp)
    etf_list = []
    
    for etf in raw_etfs:
        meta = etf.get("meta", {})
        
        if not meta:
            continue
        
        # Parse asset info
        asset_info = _parse_asset(etf.get("assets", ""))
        
        # Get active series as string
        active_series = meta.get("activeSeries", [])
        active_series_str = active_series[0] if active_series else None
        
        # Get debt series
        debt_series = meta.get("debtSeries", [])
        debt_series_str = debt_series[0] if debt_series else None
        
        etf_entry = {
            "symbol": meta.get("symbol", ""),
            "companyName": meta.get("companyName", ""),
            "segment": meta.get("segment", ""),
            "assetType": asset_info["assetType"],
            "underlyingAsset": asset_info["underlyingAsset"],
            "indexVariant": asset_info["indexVariant"],
            "activeSeries": active_series_str,
            "listingDate": meta.get("listingDate", ""),
            "isin": meta.get("isin", ""),
            "debtSeries": debt_series_str,
            "isFNOSec": meta.get("isFNOSec", False),
            "isCASec": meta.get("isCASec", False),
            "isSLBSec": meta.get("isSLBSec", False),
            "isDebtSec": meta.get("isDebtSec", False),
            "isSuspended": meta.get("isSuspended", False),
            "isETFSec": meta.get("isETFSec", False),
            "isDelisted": meta.get("isDelisted", False),
            "isMunicipalBond": meta.get("isMunicipalBond", False),
            "isHybridSymbol": meta.get("isHybridSymbol", False),
        }
        
        # Add slb_isin only if it exists
        slb_isin = meta.get("slb_isin")
        if slb_isin:
            etf_entry["slb_isin"] = slb_isin
        
        etf_list.append(etf_entry)
    
    return {
        "date": date,
        "etfs": etf_list,
    }


# NSE ETF Historical Data API endpoint
ETF_HISTORY_URL = "https://www.nseindia.com/api/historicalOR/generateSecurityWiseHistoricalData"


def _parse_date_dmy(date_str: str) -> str:
    """
    Convert date from DD-Mon-YYYY format to YYYY-MM-DD.
    e.g., "08-Jan-2026" -> "2026-01-08"
    """
    from datetime import datetime
    
    if not date_str:
        return ""
    
    try:
        dt = datetime.strptime(date_str.strip(), "%d-%b-%Y")
        return dt.strftime("%Y-%m-%d")
    except ValueError:
        return ""


def get_etf_historical_data(symbol: str, start_date: str, end_date: str = None) -> dict:
    """
    Get historical OHLCV data for an ETF.
    
    For date ranges exceeding 1 year, data is fetched in batches and stitched together.
    Uses a single session for all batch requests to improve performance.
    
    Args:
        symbol: ETF symbol (e.g., "MONQ50", "NIFTYBEES", "GOLDBEES")
        start_date: Start date in YYYY-MM-DD format
        end_date: End date in YYYY-MM-DD format (defaults to today)
    
    Returns:
        A dictionary with:
        - etfData: List of price records with:
            - symbol: ETF symbol
            - date: Date in YYYY-MM-DD format
            - open: Opening price
            - high: Day high price
            - low: Day low price
            - close: Closing price
            - volume: Total traded quantity
        
        Returns empty dict {} if the API call fails.
        
    Example:
        >>> from niftyterminal import get_etf_historical_data
        >>> data = get_etf_historical_data("MONQ50", "2025-12-01", "2026-01-08")
        >>> print(data['etfData'][0])
        {'symbol': 'MONQ50', 'date': '2026-01-08', 'open': 88.3, 'high': 88.3, 'low': 85.26, 'close': 85.89, 'volume': 112552}
    """
    from datetime import datetime, timedelta
    from niftyterminal.core.session import NSESession
    
    # Maximum days per API request (NSE limit is ~365 days)
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
    
    # Fetch data for each batch using single session
    all_records = {}  # Use dict to deduplicate by date
    
    with NSESession() as nse:
        for batch_start, batch_end in date_batches:
            # Format dates for API (DD-MM-YYYY)
            from_date = batch_start.strftime("%d-%m-%Y")
            to_date = batch_end.strftime("%d-%m-%Y")
            
            # Build URL
            url = f"{ETF_HISTORY_URL}?from={from_date}&to={to_date}&symbol={symbol}&type=priceVolumeDeliverable&series=ALL"
            
            data = nse.fetch(url)
            
            if not data:
                continue
            
            raw_data = data.get("data", [])
            
            for item in raw_data:
                # Skip non-EQ series (e.g., BL - Block deals)
                series = item.get("CH_SERIES", "")
                if series != "EQ":
                    continue
                
                # Parse date
                parsed_date = _parse_date_dmy(item.get("mTIMESTAMP", ""))
                
                if not parsed_date:
                    continue
                
                # Extract prices
                try:
                    open_price = float(item.get("CH_OPENING_PRICE", 0))
                except (ValueError, TypeError):
                    open_price = 0.0
                
                try:
                    high_price = float(item.get("CH_TRADE_HIGH_PRICE", 0))
                except (ValueError, TypeError):
                    high_price = 0.0
                
                try:
                    low_price = float(item.get("CH_TRADE_LOW_PRICE", 0))
                except (ValueError, TypeError):
                    low_price = 0.0
                
                try:
                    close_price = float(item.get("CH_CLOSING_PRICE", 0))
                except (ValueError, TypeError):
                    close_price = 0.0
                
                try:
                    volume = int(item.get("CH_TOT_TRADED_QTY", 0))
                except (ValueError, TypeError):
                    volume = 0
                
                # Use date as key to avoid duplicates
                all_records[parsed_date] = {
                    "symbol": item.get("CH_SYMBOL", symbol),
                    "date": parsed_date,
                    "open": open_price,
                    "high": high_price,
                    "low": low_price,
                    "close": close_price,
                    "volume": volume,
                }
    
    if not all_records:
        return {}
    
    # Sort by date descending (most recent first)
    etf_data = [all_records[d] for d in sorted(all_records.keys(), reverse=True)]
    
    return {
        "etfData": etf_data,
    }
