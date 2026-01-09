"""
Nifty Terminal - A clean Python library for fetching Indian stock market data from NSE India.

This library provides easy-to-use functions to fetch market data from NSE India's public APIs
with built-in session management, cookie warmup, and robust error handling.
"""

__version__ = "0.2.1"
__author__ = "Surjith"

# Public API exports
from niftyterminal.api.market import get_market_status
from niftyterminal.api.indices import (
    get_all_index_quote,
    get_index_list,
    get_index_historical_data,
    get_index_stocks,
)
from niftyterminal.api.vix import get_vix_historical_data
from niftyterminal.api.etf import get_all_etfs, get_etf_historical_data
from niftyterminal.api.stocks import get_stocks_list, get_stock_quote
from niftyterminal.api.commodity import get_commodity_list, get_commodity_historical_data
from niftyterminal.exceptions import (
    NiftyTerminalError,
    SessionError,
    APIError,
)

__all__ = [
    # Version
    "__version__",
    # API functions
    "get_market_status",
    "get_all_index_quote",
    "get_index_list",
    "get_index_historical_data",
    "get_index_stocks",
    "get_vix_historical_data",
    "get_all_etfs",
    "get_etf_historical_data",
    "get_stocks_list",
    "get_stock_quote",
    "get_commodity_list",
    "get_commodity_historical_data",
    # Exceptions
    "NiftyTerminalError",
    "SessionError",
    "APIError",
]





