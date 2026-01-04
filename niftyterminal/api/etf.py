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
        # Extract underlying index
        underlying = "NIFTY_1D_RATE"
        if 'bse' in assets_lower or 's&p bse' in assets_lower:
            underlying = "BSE_LIQUID_RATE"
        elif 'crisil' in assets_lower:
            underlying = "CRISIL_OVERNIGHT"
        
        return {
            "assetType": "Liquid",
            "underlyingAsset": underlying,
            "indexVariant": None,
        }
    
    if any(kw in assets_lower for kw in ['g-sec', 'gsec', 'gilt', 'bond', 'sdl', 'bharat bond']):
        # Parse specific debt index
        underlying = None
        if 'bharat bond' in assets_lower or 'bharat' in assets_lower:
            # Extract year if present
            year_match = re.search(r'20\d{2}', assets)
            if year_match:
                underlying = f"BHARAT_BOND_{year_match.group()}"
            else:
                underlying = "BHARAT_BOND"
        elif '10' in assets_lower or '10 yr' in assets_lower or '10 year' in assets_lower:
            underlying = "GSEC_10YR"
        elif '8-13' in assets_lower:
            underlying = "GSEC_8_13YR"
        elif '5' in assets_lower and ('yr' in assets_lower or 'year' in assets_lower):
            underlying = "GSEC_5YR"
        elif 'sdl' in assets_lower:
            underlying = "SDL"
        else:
            underlying = "GSEC"
        
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
                underlying = "NASDAQ_Q50"
            elif 'fang' in assets_lower:
                underlying = "NYSE_FANG"
            else:
                underlying = "NASDAQ_100"
        elif 'hang seng' in assets_lower:
            if 'tech' in assets_lower:
                underlying = "HANG_SENG_TECH"
            else:
                underlying = "HANG_SENG"
        elif 'nyse' in assets_lower:
            underlying = "NYSE_FANG"
        elif 's&p 500' in assets_lower:
            underlying = "SP_500"
        elif 'msci' in assets_lower:
            underlying = "MSCI_INDIA"
        
        variant = _detect_index_variant(assets)
        
        return {
            "assetType": "International",
            "underlyingAsset": underlying,
            "indexVariant": variant,
        }
    
    # 4. Shariah
    if 'shariah' in assets_lower:
        return {
            "assetType": "EquityIndex",
            "underlyingAsset": "NIFTY_SHARIAH",
            "indexVariant": None,
        }
    
    # 5. CPSE ETF
    if 'cpse' in assets_lower:
        return {
            "assetType": "EquityIndex",
            "underlyingAsset": "CPSE",
            "indexVariant": None,
        }
    
    # 6. Default: Equity Index - Parse index name
    variant = _detect_index_variant(assets)
    
    # Attempt to identify the index
    underlying = None
    
    # BSE indices
    if 'sensex' in assets_lower or 'bse' in assets_lower:
        if 'sensex next 50' in assets_lower:
            underlying = "SENSEX_NEXT_50"
        elif 'sensex next 30' in assets_lower:
            underlying = "SENSEX_NEXT_30"
        elif 'sensex' in assets_lower:
            underlying = "SENSEX"
        elif 'bse 500' in assets_lower:
            underlying = "BSE_500"
        elif 'bse 200' in assets_lower:
            underlying = "BSE_200"
        elif 'bse psu bank' in assets_lower:
            underlying = "BSE_PSU_BANK"
        elif 'bse power' in assets_lower:
            underlying = "BSE_POWER"
        elif 'bse capital' in assets_lower:
            underlying = "BSE_CAPITAL_MARKETS"
        elif 'bse infra' in assets_lower:
            underlying = "BSE_INFRASTRUCTURE"
        elif 'bse healthcare' in assets_lower or 'bse health' in assets_lower:
            underlying = "BSE_HEALTHCARE"
        elif 'bharat 22' in assets_lower:
            underlying = "BHARAT_22"
        elif 'bse ipo' in assets_lower:
            underlying = "BSE_IPO"
        elif 'bse midcap' in assets_lower:
            underlying = "BSE_MIDCAP_SELECT"
        elif 'bse dividend' in assets_lower:
            underlying = "BSE_500_DIVIDEND"
        else:
            underlying = _normalize_index_name(assets)
    
    # Nifty indices
    elif 'nifty' in assets_lower:
        # Specific patterns
        if 'nifty 50' in assets_lower and 'next' not in assets_lower:
            if 'value 20' in assets_lower:
                underlying = "NIFTY_50_VALUE_20"
            elif 'equal' in assets_lower:
                underlying = "NIFTY_50_EQUAL_WEIGHT"
            else:
                underlying = "NIFTY_50"
        elif 'nifty next 50' in assets_lower or 'nifty next50' in assets_lower:
            underlying = "NIFTY_NEXT_50"
        elif 'nifty 100' in assets_lower:
            if 'low vol' in assets_lower:
                underlying = "NIFTY_100_LOW_VOL_30"
            elif 'quality' in assets_lower:
                underlying = "NIFTY_100_QUALITY_30"
            elif 'equal' in assets_lower:
                underlying = "NIFTY_100_EQUAL_WEIGHT"
            elif 'esg' in assets_lower:
                underlying = "NIFTY_100_ESG"
            else:
                underlying = "NIFTY_100"
        elif 'nifty 200' in assets_lower:
            if 'momentum' in assets_lower:
                underlying = "NIFTY_200_MOMENTUM_30"
            elif 'quality' in assets_lower:
                underlying = "NIFTY_200_QUALITY_30"
            elif 'alpha' in assets_lower:
                underlying = "NIFTY_200_ALPHA_30"
            elif 'value' in assets_lower:
                underlying = "NIFTY_200_VALUE_30"
            else:
                underlying = "NIFTY_200"
        elif 'nifty 500' in assets_lower:
            if 'momentum 50' in assets_lower:
                underlying = "NIFTY_500_MOMENTUM_50"
            elif 'low vol' in assets_lower:
                underlying = "NIFTY_500_LOW_VOL_50"
            elif 'multicap' in assets_lower:
                underlying = "NIFTY_500_MULTICAP"
            elif 'flexicap' in assets_lower:
                underlying = "NIFTY_500_FLEXICAP_QUALITY_30"
            elif 'value' in assets_lower:
                underlying = "NIFTY_500_VALUE_50"
            else:
                underlying = "NIFTY_500"
        elif 'midcap 150' in assets_lower:
            if 'momentum' in assets_lower:
                underlying = "NIFTY_MIDCAP_150_MOMENTUM_50"
            elif 'quality' in assets_lower:
                underlying = "NIFTY_MIDCAP_150_QUALITY_50"
            else:
                underlying = "NIFTY_MIDCAP_150"
        elif 'midcap 100' in assets_lower:
            underlying = "NIFTY_MIDCAP_100"
        elif 'midcap 50' in assets_lower:
            underlying = "NIFTY_MIDCAP_50"
        elif 'smallcap 250' in assets_lower:
            if 'momentum' in assets_lower:
                underlying = "NIFTY_SMALLCAP_250_MOMENTUM_QUALITY"
            else:
                underlying = "NIFTY_SMALLCAP_250"
        elif 'smallcap 100' in assets_lower:
            underlying = "NIFTY_SMALLCAP_100"
        elif 'largemidcap' in assets_lower or 'large midcap' in assets_lower:
            underlying = "NIFTY_LARGEMIDCAP_250"
        elif 'bank' in assets_lower and 'psu' not in assets_lower and 'private' not in assets_lower:
            underlying = "NIFTY_BANK"
        elif 'psu bank' in assets_lower:
            underlying = "NIFTY_PSU_BANK"
        elif 'private bank' in assets_lower:
            underlying = "NIFTY_PRIVATE_BANK"
        elif 'financial' in assets_lower:
            if 'ex-bank' in assets_lower or 'ex bank' in assets_lower:
                underlying = "NIFTY_FINANCIAL_EX_BANK"
            else:
                underlying = "NIFTY_FINANCIAL_SERVICES"
        elif 'it' in assets_lower.split() or 'it index' in assets_lower:
            underlying = "NIFTY_IT"
        elif 'pharma' in assets_lower:
            underlying = "NIFTY_PHARMA"
        elif 'healthcare' in assets_lower or 'health' in assets_lower:
            underlying = "NIFTY_HEALTHCARE"
        elif 'auto' in assets_lower:
            underlying = "NIFTY_AUTO"
        elif 'fmcg' in assets_lower:
            underlying = "NIFTY_FMCG"
        elif 'metal' in assets_lower:
            underlying = "NIFTY_METAL"
        elif 'energy' in assets_lower:
            underlying = "NIFTY_ENERGY"
        elif 'infra' in assets_lower:
            underlying = "NIFTY_INFRA"
        elif 'realty' in assets_lower:
            underlying = "NIFTY_REALTY"
        elif 'commodities' in assets_lower:
            underlying = "NIFTY_COMMODITIES"
        elif 'consumption' in assets_lower:
            if 'new age' in assets_lower:
                underlying = "NIFTY_NEW_AGE_CONSUMPTION"
            else:
                underlying = "NIFTY_INDIA_CONSUMPTION"
        elif 'mnc' in assets_lower:
            underlying = "NIFTY_MNC"
        elif 'pse' in assets_lower:
            underlying = "NIFTY_PSE"
        elif 'dividend' in assets_lower:
            underlying = "NIFTY_DIVIDEND_50"
        elif 'alpha 50' in assets_lower:
            underlying = "NIFTY_ALPHA_50"
        elif 'alpha low' in assets_lower:
            underlying = "NIFTY_ALPHA_LOW_VOL_30"
        elif 'defence' in assets_lower:
            underlying = "NIFTY_INDIA_DEFENCE"
        elif 'digital' in assets_lower:
            underlying = "NIFTY_INDIA_DIGITAL"
        elif 'manufacturing' in assets_lower:
            underlying = "NIFTY_INDIA_MANUFACTURING"
        elif 'tourism' in assets_lower:
            underlying = "NIFTY_INDIA_TOURISM"
        elif 'railway' in assets_lower:
            underlying = "NIFTY_INDIA_RAILWAYS_PSU"
        elif 'ev' in assets_lower or 'new age auto' in assets_lower:
            underlying = "NIFTY_EV_NEW_AGE_AUTO"
        elif 'capital market' in assets_lower:
            underlying = "NIFTY_CAPITAL_MARKET"
        elif 'services' in assets_lower:
            underlying = "NIFTY_SERVICES_SECTOR"
        elif 'oil' in assets_lower or 'gas' in assets_lower:
            underlying = "NIFTY_OIL_GAS"
        elif 'chemicals' in assets_lower:
            underlying = "NIFTY_CHEMICALS"
        elif 'growth' in assets_lower:
            underlying = "NIFTY_GROWTH_SECTORS_15"
        elif 'total market' in assets_lower:
            if 'momentum' in assets_lower:
                underlying = "NIFTY_TOTAL_MARKET_MOMENTUM_QUALITY_50"
            else:
                underlying = "NIFTY_TOTAL_MARKET"
        elif 'top 10' in assets_lower:
            underlying = "NIFTY_TOP_10_EQUAL_WEIGHT"
        elif 'top 15' in assets_lower:
            underlying = "NIFTY_TOP_15_EQUAL_WEIGHT"
        elif 'top 20' in assets_lower:
            underlying = "NIFTY_TOP_20_EQUAL_WEIGHT"
        elif 'midsmallcap' in assets_lower:
            underlying = "NIFTY_MIDSMALLCAP_400_MOMENTUM_QUALITY"
        else:
            underlying = _normalize_index_name(assets)
    else:
        # Fallback: normalize the name
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
