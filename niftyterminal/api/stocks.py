"""
Stocks API functions.

This module provides functions to fetch stock-related data from NSE India.
"""

import csv
from io import StringIO
from niftyterminal.core import fetch_raw


# NSE Equity CSV URL
EQUITY_CSV_URL = "https://nsearchives.nseindia.com/content/equities/EQUITY_L.csv"


def _parse_listing_date(date_str: str) -> str:
    """
    Convert date from DD-Mon-YYYY format to YYYY-MM-DD.
    e.g., "06-OCT-2008" -> "2008-10-06"
    """
    from datetime import datetime
    
    if not date_str:
        return ""
    
    try:
        dt = datetime.strptime(date_str.strip(), "%d-%b-%Y")
        return dt.strftime("%Y-%m-%d")
    except ValueError:
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
            - listingDate: Date of listing in YYYY-MM-DD format
            - isin: ISIN code
            - faceValue: Face value of the stock
        
        Returns empty dict {} if the API call fails.
        
    Example:
        >>> from niftyterminal import get_stocks_list
        >>> data = get_stocks_list()
        >>> print(f"Total stocks: {len(data['stockList'])}")
    """
    # Fetch the CSV content
    csv_content = fetch_raw(EQUITY_CSV_URL)
    
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
        listing_date = row.get(" DATE OF LISTING", "").strip()
        isin = row.get(" ISIN NUMBER", "").strip()
        face_value = row.get(" FACE VALUE", "").strip()
        
        if not symbol:
            continue
        
        # Parse face value as int
        try:
            face_value_int = int(float(face_value)) if face_value else 0
        except (ValueError, TypeError):
            face_value_int = 0
        
        stock_list.append({
            "symbol": symbol,
            "companyName": company_name,
            "series": series,
            "listingDate": _parse_listing_date(listing_date),
            "isin": isin,
            "faceValue": face_value_int,
        })
    
    return {
        "stockList": stock_list,
    }
