"""
Market status API functions.

This module provides functions to fetch market status information from NSE India.
"""

from niftyterminal.core import fetch

# NSE Market Status API endpoint
MARKET_STATUS_URL = "https://www.nseindia.com/api/marketStatus"


def get_market_status() -> dict:
    """
    Get the current Capital Market status from NSE India.
    
    This function fetches the market status and returns only the
    Capital Market information in a clean, simplified format.
    
    Returns:
        A dictionary with exactly two keys:
        - marketStatus: The current market status (e.g., "Open", "Closed")
        - marketStatusMessage: The detailed status message
        
        Returns empty dict {} if the API call fails or Capital Market
        data is not found.
        
    Example:
        >>> from niftyterminal import get_market_status
        >>> status = get_market_status()
        >>> print(status)
        {'marketStatus': 'Open', 'marketStatusMessage': 'Normal Market is Open'}
    """
    data = fetch(MARKET_STATUS_URL)
    
    if not data:
        return {}
    
    # Look for Capital Market in the marketState array
    market_state = data.get("marketState", [])
    
    for market in market_state:
        if market.get("market") == "Capital Market":
            return {
                "marketStatus": market.get("marketStatus", ""),
                "marketStatusMessage": market.get("marketStatusMessage", ""),
            }
    
    # Capital Market not found in response
    return {}
