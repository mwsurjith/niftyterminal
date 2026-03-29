<p align="center">
  <img src="https://raw.githubusercontent.com/mwsurjith/niftyterminal/main/.github/logo.png" alt="Nifty Terminal Logo" width="120" onerror="this.src='https://em-content.zobj.net/source/microsoft-teams/363/chart-increasing_1f4c8.png'; this.width=80;">
  <h1 align="center">Nifty Terminal</h1>
  <p align="center">
    <strong>The Pythonic gateway to Indian Market Data</strong>
  </p>
  <p align="center">
    High-fidelity Index, Equity, ETF, and Fundamental data directly from NSE India APIs.
  </p>
</p>

<p align="center">
  <a href="https://pypi.org/project/niftyterminal/">
    <img src="https://img.shields.io/pypi/v/niftyterminal?color=007ec6&style=for-the-badge" alt="PyPI Version">
  </a>
  <a href="https://pypi.org/project/niftyterminal/">
    <img src="https://img.shields.io/pypi/pyversions/niftyterminal?color=3776ab&style=for-the-badge" alt="Python Versions">
  </a>
  <a href="https://github.com/mwsurjith/niftyterminal/blob/main/LICENSE">
    <img src="https://img.shields.io/github/license/mwsurjith/niftyterminal?color=4caf50&style=for-the-badge" alt="License">
  </a>
</p>

---

## ✨ Why Nifty Terminal?

Most NSE scrapers break due to strict session requirements, Akamai protection, or inconsistent API responses. **Nifty Terminal** is built to solve these problems specifically:

- 🛡️ **Zero-Config Session Handling:** Automatically manages cookies and session handshakes for NSE India and Nifty Indices.
- ⚡ **Async-First Architecture:** Built on top of `httpx` and `asyncio` for high-performance concurrent data fetching.
- 📊 **Unified Fundamentals:** Normalizes modern XBRL and legacy HTML filings into consistent JSON objects.
- 🏷️ **Smart Categorization:** Automatically tags ETFs by asset class (Gold, Silver, Index) and variants (TRI, Alpha, Value).

---

## 📦 Installation

```bash
pip install niftyterminal
```

---

## ⚡ Quick Start

Almost all functions in `niftyterminal` are **asynchronous**. Here's how to fetch NIFTY 50 historical data with PE ratios:

```python
import asyncio
from niftyterminal import get_index_historical_data

async def main():
    # Fetch NIFTY 50 history for Q1 2025
    data = await get_index_historical_data("NIFTY 50", "2025-01-01", "2025-03-31")
    
    for day in data['indexData']:
        print(f"{day['date']}: {day['close']} (PE: {day['PE']})")

if __name__ == "__main__":
    asyncio.run(main())
```

---

## 📖 API Reference

### 🏛️ Market & Indices

#### `get_market_status()`
Get current Capital Market status (Open/Closed/Halt).

#### `get_all_index_quote()`
Quotes for all indices including OHLC, PE/PB/DY, and historical comparisons.

<details>
<summary><b>📤 View Sample Output</b></summary>

```json
{
  "timestamp": "02-Jan-2026 15:30",
  "indexQuote": [
    {
      "indexName": "NIFTY 50",
      "date": "2026-01-02",
      "open": 26155.1,
      "high": 26340,
      "ltp": 26328.55,
      "pe": "22.92",
      "pb": "3.58",
      "dy": "1.28",
      "oneWeekAgoPercentChange": 1.1
    }
  ]
}
```
</details>

#### `get_index_historical_data(symbol, start, end)`
Historical OHLC and Valuation data from Nifty Indices.

| Param | Type | Required | Description |
|-------|------|----------|-------------|
| `symbol` | `str` | Yes | e.g., `"NIFTY 50"`, `"NIFTY BANK"` |
| `start` | `str` | Yes | `YYYY-MM-DD` |
| `end` | `str` | No | Defaults to today |

---

### 📈 Equities & ETFs

#### `get_stock_quote(symbol)`
Detailed metadata, price, and sector info for a specific stock.

#### `get_all_etfs()`
Lists all ETFs with smart metadata for easy filtering.

> [!TIP]
> Filter ETFs by `underlyingAsset` (e.g., `GOLD`) or `indexVariant` (e.g., `TRI`) to find exactly what you need.

#### `get_etf_historical_data(symbol, start, end)`
Historical price data specifically for ETFs.

---

### 🏦 Fundamentals & Financials

> [!IMPORTANT]
> Financial data is extracted from Integrated Filing XBRL sources, ensuring the highest accuracy for fundamental analysis.

#### `get_stock_financials(symbol, consolidated, period)`
Quarterly or Annual P&L with segment-wise breakdown. Handles modern and legacy filings seamlessly.

#### `get_stock_annual_report(symbol, consolidated)`
Unified call to fetch Profit & Loss, Balance Sheet, and Cash Flow in one go.

<details>
<summary><b>📤 View Financial Data Model</b></summary>

```json
{
  "symbol": "RELIANCE",
  "filings": [
    {
      "period": "Quarterly",
      "financial_data": {
        "financials": {
          "revenue_from_operations": 2438650000000.0,
          "net_profit": 219300000000.0
        },
        "segments": { ... }
      }
    }
  ]
}
```
</details>

---

### 🪙 Specialized Data

- **`get_vix_historical_data()`**: India VIX historical trends.
- **`get_commodity_historical_data()`**: Spot prices for Gold/Silver/etc. on NSE.

---

## 🛠️ Technical Highlights

### Robust Session Management
NSE India requires a "warm-up" phase where initial cookies are obtained from the homepage before API requests are accepted. `niftyterminal` implements an automated `BypassSession` that:
1. Performs a headless handshake with NSE.
2. Manages persistent cookies across requests.
3. Automatically switches between `nseindia.com` and `niftyindices.com` sessions.

### Data Normalization
Stock market filing formats change over time. Our parsers are trained on:
- **New Format (XBRL):** High-precision extraction of line items.
- **Old Format (HTML):** Intelligent mapping to the new schema for historical continuity.

---

## ⚠️ Disclaimer

This library is for **educational and research purposes only**. It is not affiliated with, maintained, or endorsed by NSE India. Use market data responsibly and adhere to the [NSE Terms of Service](https://www.nseindia.com/terms-of-use).

---

<p align="center">
  Built with ❤️ for Indian Quants.
</p>
