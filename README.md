<p align="center">
  <h1 align="center">📈 Nifty Terminal</h1>
  <p align="center">
    <strong>A comprehensive Python library for NSE India market data</strong>
  </p>
  <p align="center">
    Access Index, Equity, ETF, Commodity & Historical data from official NSE India APIs
  </p>
</p>

<p align="center">
  <a href="https://pypi.org/project/niftyterminal/">
    <img src="https://img.shields.io/pypi/v/niftyterminal?color=blue&label=PyPI" alt="PyPI Version">
  </a>
  <a href="https://pypi.org/project/niftyterminal/">
    <img src="https://img.shields.io/pypi/pyversions/niftyterminal" alt="Python Versions">
  </a>
  <a href="https://github.com/mwsurjith/niftyterminal/blob/main/LICENSE">
    <img src="https://img.shields.io/badge/License-MIT-green.svg" alt="License">
  </a>
</p>

---

## ✨ Features

| Category | Features |
|----------|----------|
| 🏛️ **Market** | Market status, trading hours |
| 📊 **Indices** | List, quotes, historical OHLCV, PE/PB/DY ratios, constituents |
| 📈 **Equities** | Complete stock list, quotes, historical data |
| 💰 **ETFs** | All ETFs with smart asset categorization (Gold, Silver, Index, International) |
| 🪙 **Commodities** | Commodity list, spot prices, historical data |
| 📉 **VIX** | India VIX historical data |

---

## 🚀 Quick Start

### Installation

```bash
pip install niftyterminal
```

### Basic Usage

```python
from niftyterminal import get_market_status, get_index_historical_data

# Check if market is open
status = get_market_status()
print(f"Market is {status['marketStatus']}")

# Get NIFTY 50 historical data with PE/PB/DY
data = get_index_historical_data("NIFTY 50", "2025-01-01", "2025-12-31")
for row in data['indexData']:
    print(f"{row['date']}: Close={row['close']}, PE={row['PE']}")
```

---

## 📚 Table of Contents

- [Market](#get_market_status)
- [Indices](#index-functions)
  - [Get Index List](#get_index_list)
  - [Get All Index Quote](#get_all_index_quote)
  - [Get Index Historical Data](#get_index_historical_dataindex_symbol-start_date-end_date)
  - [Get Index Stocks](#get_index_stocksindex_name)
- [VIX](#get_vix_historical_datastart_date-end_date)
- [ETFs](#get_all_etfs)
- [Equities](#get_stocks_list)
- [Commodities](#commodity-functions)
  - [Get Commodity List](#get_commodity_list)
  - [Get Commodity Historical Data](#get_commodity_historical_datasymbol-start_date-end_date)
- [Disclaimer](#disclaimer)
- [License](#license)

---

## 📖 API Reference

### `get_market_status()`

Get the current Capital Market status from NSE India.

```python
from niftyterminal import get_market_status

status = get_market_status()
print(status)
```

<details>
<summary><b>📤 Output</b></summary>

```json
{
  "marketStatus": "Close",
  "marketStatusMessage": "Market is Closed"
}
```

| Field | Description |
|-------|-------------|
| `marketStatus` | Current status: `"Open"`, `"Close"`, etc. |
| `marketStatusMessage` | Detailed status message |

</details>

---

## Index Functions

### `get_index_list()`

Get the master list of all indices with their category and derivatives eligibility.

```python
from niftyterminal import get_index_list

data = get_index_list()
```

<details>
<summary><b>📤 Output</b></summary>

```json
{
  "indexList": [
    {
      "indexName": "NIFTY 50",
      "subType": "Broad Market Indices",
      "derivativesEligiblity": true
    },
    {
      "indexName": "NIFTY BANK",
      "subType": "Broad Market Indices",
      "derivativesEligiblity": true
    }
  ]
}
```

| Field | Description |
|-------|-------------|
| `indexName` | Full name of the index |
| `subType` | Category: `Broad Market`, `Sectoral`, `Thematic`, `Strategy`, `Fixed Income` |
| `derivativesEligiblity` | `true` if eligible for F&O trading |

</details>

---

### `get_all_index_quote()`

Get comprehensive quote data for all indices including OHLC, valuation metrics (PE/PB/DY), and historical comparison data.

```python
from niftyterminal import get_all_index_quote

data = get_all_index_quote()
```

<details>
<summary><b>📤 Output</b></summary>

```json
{
  "timestamp": "02-Jan-2026 15:30",
  "indexQuote": [
    {
      "indexName": "NIFTY 50",
      "date": "2026-01-02",
      "open": 26155.1,
      "high": 26340,
      "low": 26118.4,
      "ltp": 26328.55,
      "prevClose": 26146.55,
      "change": 182,
      "percentChange": 0.7,
      "pe": "22.92",
      "pb": "3.58",
      "dy": "1.28",
      "oneWeekAgoPercentChange": 1.1,
      "30dAgoPercentChange": 1.14,
      "365dAgoPercentChange": 10.89
    }
  ]
}
```

| Field | Description |
|-------|-------------|
| `ltp` | Last traded price |
| `percentChange` | Percentage change from previous close |
| `pe` / `pb` / `dy` | PE ratio, PB ratio, Dividend Yield |
| `oneWeekAgoPercentChange` | Percent change from 1 week ago |
| `30dAgoPercentChange` | Percent change from 30 days ago |
| `365dAgoPercentChange` | Percent change from 365 days ago |

</details>

---

### `get_index_historical_data(index_symbol, start_date, end_date)`

Get historical OHLC and valuation data (PE, PB, Dividend Yield) for any index.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `index_symbol` | str | ✅ | Index name (e.g., `"NIFTY 50"`, `"NIFTY BANK"`) |
| `start_date` | str | ✅ | Start date in `YYYY-MM-DD` format |
| `end_date` | str | ❌ | End date in `YYYY-MM-DD` format (defaults to today) |

```python
from niftyterminal import get_index_historical_data

# With date range
data = get_index_historical_data("NIFTY 50", "2025-01-01", "2026-01-03")

# Without end date (defaults to today)
data = get_index_historical_data("NIFTY BANK", "2024-01-01")
```

<details>
<summary><b>📤 Output</b></summary>

```json
{
  "indexData": [
    {
      "indexName": "NIFTY 50",
      "date": "2025-01-10",
      "open": 23551.9,
      "high": 23596.6,
      "low": 23344.35,
      "close": 23431.5,
      "volume": 261022434,
      "PE": 21.59,
      "PB": 3.49,
      "divYield": 1.28
    }
  ]
}
```

| Field | Description |
|-------|-------------|
| `date` | Trading date in `YYYY-MM-DD` format |
| `open` / `high` / `low` / `close` | OHLC prices |
| `volume` | Total traded volume |
| `PE` / `PB` / `divYield` | Valuation metrics |

</details>

---

### `get_index_stocks(index_name)`

Get the list of constituent stocks for an index.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `index_name` | str | ✅ | Index name (e.g., `"NIFTY 50"`, `"NIFTY BANK"`) |

```python
from niftyterminal import get_index_stocks

data = get_index_stocks("NIFTY 50")
```

<details>
<summary><b>📤 Output</b></summary>

```json
{
  "indexName": "NIFTY 50",
  "date": "2026-01-02",
  "stockList": [
    {
      "symbol": "COALINDIA",
      "companyName": "Coal India Limited",
      "industry": "Coal",
      "listingDate": "2010-11-04",
      "isin": "INE522F01014",
      "isFNOSec": true,
      "isSLBSec": true
    }
  ]
}
```

| Field | Description |
|-------|-------------|
| `symbol` | Stock ticker symbol |
| `companyName` | Full company name |
| `industry` | Industry sector |
| `isFNOSec` | Eligible for F&O trading |

</details>

---

### `get_vix_historical_data(start_date, end_date)`

Get historical India VIX data.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `start_date` | str | ✅ | Start date in `YYYY-MM-DD` format |
| `end_date` | str | ❌ | End date in `YYYY-MM-DD` format (defaults to today) |

```python
from niftyterminal import get_vix_historical_data

data = get_vix_historical_data("2025-01-01", "2025-04-16")
```

<details>
<summary><b>📤 Output</b></summary>

```json
{
  "vixData": [
    {
      "indexName": "INDIA VIX",
      "date": "2025-04-11",
      "open": 21.43,
      "high": 21.43,
      "low": 18.855,
      "close": 20.11
    }
  ]
}
```

| Field | Description |
|-------|-------------|
| `date` | Trading date in `YYYY-MM-DD` format |
| `open` / `high` / `low` / `close` | VIX OHLC values |

</details>

---

### `get_all_etfs()`

Get list of all ETFs with smart asset categorization for easy filtering.

```python
from niftyterminal import get_all_etfs

data = get_all_etfs()

# Filter by asset type
gold_etfs = [e for e in data['etfs'] if e['underlyingAsset'] == 'GOLD']
nifty_50_etfs = [e for e in data['etfs'] if e['underlyingAsset'] == 'NIFTY_50']
```

<details>
<summary><b>📤 Output</b></summary>

```json
{
  "date": "2026-01-02",
  "etfs": [
    {
      "symbol": "NIFTYBEES",
      "companyName": "Nippon India ETF Nifty BeES",
      "assetType": "EquityIndex",
      "underlyingAsset": "NIFTY_50",
      "indexVariant": "TRI",
      "listingDate": "2002-01-08",
      "isFNOSec": true
    }
  ]
}
```

| Field | Values |
|-------|--------|
| `assetType` | `Commodity`, `EquityIndex`, `DebtIndex`, `Liquid`, `International` |
| `underlyingAsset` | `GOLD`, `SILVER`, `NIFTY_50`, `SENSEX`, `NASDAQ_100`, etc. |
| `indexVariant` | `TRI`, `EqualWeight`, `Momentum`, `Quality`, `Value`, `LowVol`, `Alpha` |

</details>

---

### `get_stocks_list()`

Get the complete list of all listed stocks on NSE.

```python
from niftyterminal import get_stocks_list

data = get_stocks_list()
print(f"Total stocks: {len(data['stockList'])}")
```

<details>
<summary><b>📤 Output</b></summary>

```json
{
  "stockList": [
    {
      "symbol": "20MICRONS",
      "companyName": "20 Microns Limited",
      "series": "EQ",
      "listingDate": "2008-10-06",
      "isin": "INE144J01027",
      "faceValue": 5
    }
  ]
}
```

| Field | Description |
|-------|-------------|
| `symbol` | Stock ticker symbol |
| `companyName` | Full company name |
| `series` | Trading series: `EQ`, `BE`, `BZ` |
| `listingDate` | Date of listing (`YYYY-MM-DD`) |
| `faceValue` | Face value of share |

</details>

---

## Commodity Functions

### `get_commodity_list()`

Get the list of all commodity symbols from NSE.

```python
from niftyterminal import get_commodity_list

data = get_commodity_list()
print([c['symbol'] for c in data['commodityList']])
# Output: ['ALUMINI', 'GOLD', 'SILVER', 'CRUDEOIL', ...]
```

---

### `get_commodity_historical_data(symbol, start_date, end_date)`

Get historical spot price data for a commodity.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `symbol` | str | ✅ | Commodity symbol (e.g., `"GOLD1G"`, `"SILVER"`) |
| `start_date` | str | ✅ | Start date in `YYYY-MM-DD` format |
| `end_date` | str | ❌ | End date (defaults to today) |

```python
from niftyterminal import get_commodity_historical_data

data = get_commodity_historical_data("GOLD1G", "2025-12-28", "2026-01-04")
```

<details>
<summary><b>📤 Output</b></summary>

```json
{
  "commodityData": [
    {
      "symbol": "GOLD1G",
      "unit": "1 Grams",
      "spotPrice1": 13442,
      "spotPrice2": 13460,
      "date": "2026-01-02"
    }
  ]
}
```

| Field | Description |
|-------|-------------|
| `symbol` | Commodity symbol |
| `unit` | Unit of measurement |
| `spotPrice1` / `spotPrice2` | Spot prices |
| `date` | Date (`YYYY-MM-DD`) |

</details>

---

## ⚠️ Disclaimer

> [!CAUTION]
> - This library is **not affiliated with, endorsed by, or associated with** the National Stock Exchange of India (NSE) or any other financial institution.
> - It **does not provide** financial, trading, or investment advice. Verify data independently before making financial decisions.
> - It only retrieves **publicly available data** without authentication or bypassing security measures.
> - Users are responsible for ensuring compliance with applicable laws and the data provider's terms of service.
> - **Use at your own risk.**

---

## 📄 License

[MIT License](LICENSE) © 2025

---

<p align="center">
  Made with ❤️ for the Indian trading community
</p>
