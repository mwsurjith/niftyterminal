# Nifty Terminal

Nifty Terminal is a comprehensive python library to get Index, Equity, Latest Quote & Historical data from official NSE India website's public APIs and provides it in a structured format for easy developer experience.

## Disclaimer

- This library is not affiliated with, endorsed by, or associated with the National Stock Exchange of India (NSE) or any other financial institution. NSE retains all rights over its proprietary data, trademarks, and services.
- It does not provide financial, trading, or investment advice. Users should verify data independently before making any financial decisions.
- It only retrieves publicly available data from the official website without requiring authentication, login credentials, or bypassing any security measures. It does not scrape private, restricted, or real-time tick-by-tick data.
- Users are responsible for ensuring their use complies with applicable laws, regulations, and the terms of service of the data provider. The author assumes no liability for any misuse or consequences arising from the use of this tool.
- Use it at your own risk.

## Installation

```bash
pip install niftyterminal
```

---

## API Reference

### `get_market_status()`

Get the current Capital Market status from NSE India.

```python
from niftyterminal import get_market_status

status = get_market_status()
print(status)
```

**Output:**
```json
{
  "marketStatus": "Close",
  "marketStatusMessage": "Market is Closed"
}
```

| Field | Description |
|-------|-------------|
| `marketStatus` | Current status: "Open", "Close", etc. |
| `marketStatusMessage` | Detailed status message |

---

### `get_index_list()`

Get the master list of all indices with their category and derivatives eligibility.

```python
from niftyterminal import get_index_list

data = get_index_list()
print(data)
```

**Output:**
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
    },
    {
      "indexName": "NIFTY FINANCIAL SERVICES",
      "subType": "Broad Market Indices",
      "derivativesEligiblity": true
    }
  ]
}
```

| Field | Description |
|-------|-------------|
| `indexName` | Full name of the index |
| `subType` | Category: Broad Market, Sectoral, Thematic, Strategy, Fixed Income |
| `derivativesEligiblity` | `true` if eligible for F&O trading |

---

### `get_all_index_quote()`

Get comprehensive quote data for all indices including OHLC, valuation metrics (PE/PB/DY), and historical comparison data.


```python
from niftyterminal import get_all_index_quote

data = get_all_index_quote()
print(data)
```

**Output:**
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
      "oneWeekAgoDate": "2025-12-26",
      "oneWeekAgoVal": 26042.3,
      "oneWeekAgoPercentChange": 1.1,
      "30dAgoDate": "2025-12-02",
      "30dAgoVal": 26032.2,
      "30dAgoPercentChange": 1.14,
      "365dAgoDate": "2025-01-01",
      "365dAgoVal": 23742.9,
      "365dAgoPercentChange": 10.89
    }
  ]
}
```

| Field | Description |
|-------|-------------|
| `indexName` | Full name of the index |
| `date` | Trading date (YYYY-MM-DD) |
| `ltp` | Last traded price |
| `change` | Absolute change from previous close |
| `percentChange` | Percentage change |
| `pe` / `pb` / `dy` | PE ratio, PB ratio, Dividend Yield |
| `oneWeekAgoPercentChange` | Percent change from 1 week ago |
| `30dAgoPercentChange` | Percent change from 30 days ago |
| `365dAgoPercentChange` | Percent change from 365 days ago |

---


### `get_index_historical_data(index_symbol, start_date, end_date)`

Get historical OHLC and valuation data (PE, PB, Dividend Yield) for any index.

**Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `index_symbol` | str | Yes | Index name (e.g., "NIFTY 50", "NIFTY BANK") |
| `start_date` | str | Yes | Start date in YYYY-MM-DD format |
| `end_date` | str | No | End date in YYYY-MM-DD format (defaults to today) |

```python
from niftyterminal import get_index_historical_data

# With date range
data = get_index_historical_data("NIFTY 50", "2025-01-01", "2026-01-03")

# Without end date (defaults to today)
data = get_index_historical_data("NIFTY BANK", "2024-01-01")
```

**Output:**
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
| `date` | Trading date in YYYY-MM-DD format |
| `open` | Opening price |
| `high` | Day's high |
| `low` | Day's low |
| `close` | Closing price |
| `volume` | Total traded volume |
| `PE` | Price to Earnings ratio |
| `PB` | Price to Book ratio |
| `divYield` | Dividend Yield (%)


---


### `get_index_stocks(index_name)`

Get the list of constituent stocks for an index.

**Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `index_name` | str | Yes | Index name (e.g., "NIFTY 50", "NIFTY BANK") |

```python
from niftyterminal import get_index_stocks

data = get_index_stocks("NIFTY 50")
```

**Output:**
```json
{
  "indexName": "NIFTY 50",
  "date": "2026-01-02",
  "stockList": [
    {
      "symbol": "COALINDIA",
      "companyName": "Coal India Limited",
      "industry": "Coal",
      "segment": "EQUITY",
      "listingDate": "2010-11-04",
      "isin": "INE522F01014",
      "slb_isin": "INE522F01014",
      "isFNOSec": true,
      "isCASec": false,
      "isSLBSec": true,
      "isDebtSec": false,
      "isSuspended": false,
      "isETFSec": false,
      "isDelisted": false,
      "isMunicipalBond": false,
      "isHybridSymbol": false
    }
  ]
}
```

| Field | Description |
|-------|-------------|
| `symbol` | Stock ticker symbol |
| `companyName` | Full company name |
| `industry` | Industry sector |
| `listingDate` | Date of listing (YYYY-MM-DD) |
| `isin` | ISIN code |
| `isFNOSec` | Eligible for F&O trading |

---

### `get_vix_historical_data(start_date, end_date)`

Get historical India VIX data.


**Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `start_date` | str | Yes | Start date in YYYY-MM-DD format |
| `end_date` | str | No | End date in YYYY-MM-DD format (defaults to today) |

```python
from niftyterminal import get_vix_historical_data

data = get_vix_historical_data("2025-01-01", "2025-04-16")
```

**Output:**
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
    },
    {
      "indexName": "INDIA VIX",
      "date": "2025-04-09",
      "open": 20.4425,
      "high": 21.7475,
      "low": 19.6975,
      "close": 21.43
    }
  ]
}
```

| Field | Description |
|-------|-------------|
| `indexName` | Name of the index ("INDIA VIX") |
| `date` | Trading date in YYYY-MM-DD format |
| `open` | Opening VIX value |
| `high` | Day's high |
| `low` | Day's low |
| `close` | Closing VIX value |

---

### `get_all_etfs()`

Get list of all ETFs with cleaned asset categorization for easy filtering.

```python
from niftyterminal import get_all_etfs

data = get_all_etfs()

# Filter by asset type
gold_etfs = [e for e in data['etfs'] if e['underlyingAsset'] == 'GOLD']
nifty_50_etfs = [e for e in data['etfs'] if e['underlyingAsset'] == 'NIFTY_50']
```

**Output:**
```json
{
  "date": "2026-01-02",
  "etfs": [
    {
      "symbol": "NIFTYBEES",
      "companyName": "Nippon India ETF Nifty BeES",
      "segment": "EQUITY",
      "assetType": "EquityIndex",
      "underlyingAsset": "NIFTY_50",
      "indexVariant": "TRI",
      "activeSeries": "EQ",
      "listingDate": "2002-01-08",
      "isin": "INF204KB14I2",
      "isFNOSec": true,
      "isSLBSec": true,
      "isETFSec": true
    }
  ]
}
```

| Field | Description |
|-------|-------------|
| `assetType` | `Commodity`, `EquityIndex`, `DebtIndex`, `Liquid`, `International` |
| `underlyingAsset` | `GOLD`, `SILVER`, `NIFTY_50`, `SENSEX`, `NASDAQ_100`, etc. |
| `indexVariant` | `TRI`, `EqualWeight`, `Momentum`, `Quality`, `Value`, `LowVol`, `Alpha` |

---

### `get_stocks_list()`

Get the complete list of all listed stocks on NSE.

```python
from niftyterminal import get_stocks_list

data = get_stocks_list()
print(f"Total stocks: {len(data['stockList'])}")
```

**Output:**
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
| `listingDate` | Date of listing (YYYY-MM-DD) |
| `isin` | ISIN code |
| `faceValue` | Face value of share |

---

### `get_commodity_list()`

Get the list of all commodity symbols from NSE.

```python
from niftyterminal import get_commodity_list

data = get_commodity_list()
print([c['symbol'] for c in data['commodityList']])
```

**Output:**
```json
{
  "commodityList": [
    {"symbol": "ALUMINI"},
    {"symbol": "GOLD"},
    {"symbol": "SILVER"},
    {"symbol": "CRUDEOIL"}
  ]
}
```

---

### `get_commodity_historical_data(symbol, start_date, end_date)`

Get historical spot price data for a commodity.

**Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `symbol` | str | Yes | Commodity symbol (e.g., "GOLD1G", "SILVER") |
| `start_date` | str | Yes | Start date in YYYY-MM-DD format |
| `end_date` | str | No | End date (defaults to today) |

```python
from niftyterminal import get_commodity_historical_data

data = get_commodity_historical_data("GOLD1G", "2025-12-28", "2026-01-04")
```

**Output:**
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
| `spotPrice1` | First spot price |
| `spotPrice2` | Second spot price |
| `date` | Date (YYYY-MM-DD) |

---

## License

MIT

