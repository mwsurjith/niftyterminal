"""
Market status API functions.

This module provides functions to fetch market status information from NSE India.
"""

from typing import Literal
from niftyterminal.core import afetch

# NSE Market Status API endpoint
MARKET_STATUS_URL = "https://www.nseindia.com/api/marketStatus"

# Valid market types
MarketType = Literal["Capital Market", "Currency", "Commodity", "Debt", "currencyfuture"]


async def get_market_status(market: MarketType = "Capital Market") -> dict:
    """
    Get the current market status from NSE India.
    
    This function fetches the market status for the specified market type
    and returns the status information in a clean, simplified format.
    
    Args:
        market: The market type to get status for. Valid options:
            - "Capital Market" (default) - Equity/Stock market
            - "Currency" - Currency market
            - "Commodity" - Commodity market  
            - "Debt" - Debt market
            - "currencyfuture" - Currency futures market
    
    Returns:
        A dictionary with exactly two keys:
        - marketStatus: The current market status (e.g., "Open", "Close")
        - marketStatusMessage: The detailed status message
        
        Returns empty dict {} if the API call fails or specified market
        data is not found.
        
    Example:
        >>> import asyncio
        >>> from niftyterminal import get_market_status
        >>> 
        >>> async def main():
        >>>     status = await get_market_status()
        >>>     print(status)
        >>> 
        >>> asyncio.run(main())
    """
    data = await afetch(MARKET_STATUS_URL)
    
    if not data:
        return {}
    
    # Look for specified market in the marketState array
    market_state = data.get("marketState", [])
    
    for m in market_state:
        if m.get("market") == market:
            return {
                "marketStatus": m.get("marketStatus", ""),
                "marketStatusMessage": m.get("marketStatusMessage", ""),
            }
    
    # Specified market not found in response
    return {}

