<p align="center">
  <img src="https://raw.githubusercontent.com/mwsurjith/niftyterminal/main/.github/logo.png" alt="Nifty Terminal Logo" width="120" onerror="this.src='https://em-content.zobj.net/source/microsoft-teams/363/chart-increasing_1f4c8.png'; this.width=80;">
  <h1 align="center">Nifty Terminal</h1>
  <p align="center">
    <strong>The Pythonic gateway to Indian Market Data</strong>
  </p>
  <p align="center">
    High-fidelity Index, Equity, ETF, and Fundamental data directly from NSE India APIs — as a Python library and a CLI tool.
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

## Why Nifty Terminal?

Most NSE scrapers break due to strict session requirements, Akamai protection, or inconsistent API responses. **Nifty Terminal** solves these problems:

- **Zero-Config Session Handling** — automatically manages cookies and session handshakes for NSE India and Nifty Indices.
- **Async-First Architecture** — built on `httpx` and `asyncio` for high-performance concurrent fetching.
- **Unified Fundamentals** — normalizes modern XBRL and legacy HTML filings into consistent JSON objects.
- **Smart ETF Categorization** — auto-tags ETFs by asset class (Gold, Silver, Index) and variants (TRI, Alpha, Value).
- **Built-in CLI** — fetch market data directly from your terminal without writing a single line of Python.

---

## Installation

Library only:

```bash
pip install niftyterminal
```

With CLI support (adds `click` and `rich`):

```bash
pip install "niftyterminal[cli]"
```

---

## CLI Usage

Once installed with `[cli]`, the `niftyterminal` command is available globally.

```
niftyterminal [--json] [--version] <group> <command> [args...]
```

Pass `--json` to any command to get raw JSON output suitable for piping to `jq`.

### Market

```bash
# Check if the market is open
niftyterminal market status

# Check a specific segment
niftyterminal market status --market-type Currency
```

### Indices

```bash
# List all NSE indices
niftyterminal index list

# Filter by name or type
niftyterminal index list --filter "NIFTY" --type "Sectoral"

# Live quotes for all indices
niftyterminal index quote

# Show only top 10, filter by name
niftyterminal index quote --filter "BANK" --top 10

# Constituent stocks of an index
niftyterminal index stocks "NIFTY 50"

# Historical OHLC + PE/PB/DivYield + Total Returns Index
niftyterminal index history "NIFTY 50" --from 2025-01-01
niftyterminal index history "NIFTY BANK" --from 2025-01-01 --to 2025-03-31
```

### Stocks

```bash
# List all NSE-listed stocks (search by name or symbol)
niftyterminal stock list --search "reliance"
niftyterminal stock list --series EQ --top 20

# Detailed quote with sector, flags, and market cap
niftyterminal stock quote RELIANCE
niftyterminal stock quote TCS

# Quarterly financial results (P&L, EPS, segments)
niftyterminal stock financials RELIANCE
niftyterminal stock financials TCS --period Annual --consolidated --limit 4

# Balance sheet
niftyterminal stock balance-sheet RELIANCE

# Cash flow statement
niftyterminal stock cash-flow HDFCBANK

# Full annual report (P&L + Balance Sheet + Cash Flow)
niftyterminal stock annual-report INFY --standalone
```

### ETFs

```bash
# List all ETFs with asset type and underlying asset
niftyterminal etf list
niftyterminal etf list --asset-type Gold
niftyterminal etf list --search "nifty"

# Historical OHLCV
niftyterminal etf history NIFTYBEES --from 2025-01-01
```

### VIX

```bash
niftyterminal vix history --from 2025-01-01
niftyterminal vix history --from 2025-01-01 --to 2025-03-31
```

### Commodities

```bash
# See all available commodity symbols
niftyterminal commodity list

# Historical spot prices
niftyterminal commodity history GOLD1G --from 2025-01-01
niftyterminal commodity history SILVER1KG --from 2025-01-01 --to 2025-03-31
```

### JSON output

Any command can output raw JSON by prepending `--json`:

```bash
niftyterminal --json stock quote RELIANCE | jq '.ltp'
niftyterminal --json index history "NIFTY 50" --from 2025-01-01 > nifty50.json
```

---

## Python Library Usage

All functions are **async**. Use `asyncio.run()` or `await` inside an async context.

### Quick start

```python
import asyncio
from niftyterminal import get_index_historical_data

async def main():
    data = await get_index_historical_data("NIFTY 50", "2025-01-01", "2025-03-31")
    for day in data['indexData']:
        print(f"{day['date']}: {day['close']}  PE={day['PE']}")

asyncio.run(main())
```

### Market status

```python
from niftyterminal import get_market_status

status = await get_market_status("Capital Market")
# {"marketStatus": "Open", "marketStatusMessage": "..."}
```

### Index quotes

```python
from niftyterminal import get_all_index_quote

data = await get_all_index_quote()
for q in data['indexQuote']:
    print(q['indexName'], q['ltp'], q['percentChange'])
```

### Stock quote

```python
from niftyterminal import get_stock_quote

q = await get_stock_quote("RELIANCE")
print(q['companyName'], q['ltp'], q['marketCap'])
```

### Financial results

```python
from niftyterminal import get_stock_financials

data = await get_stock_financials("TCS", consolidated=True, period="Quarterly")
for filing in data['filings'][:4]:
    fin = filing['financial_data']['financials']
    print(filing['to_date'], fin.get('net_profit'))
```

### Annual report (P&L + Balance Sheet + Cash Flow)

```python
from niftyterminal import get_stock_annual_report

report = await get_stock_annual_report("INFY")
```

### ETF & VIX

```python
from niftyterminal import get_all_etfs, get_etf_historical_data, get_vix_historical_data

etfs = await get_all_etfs()
gold_etfs = [e for e in etfs['etfList'] if e['assetType'] == 'Gold']

vix = await get_vix_historical_data("2025-01-01")
```

### Commodities

```python
from niftyterminal import get_commodity_list, get_commodity_historical_data

symbols = await get_commodity_list()
history = await get_commodity_historical_data("GOLD1G", "2025-01-01")
```

---

## API Reference

| Function | Description |
|----------|-------------|
| `get_market_status(market)` | Market open/close status |
| `get_all_index_quote()` | Live quotes for all indices with PE/PB/DY |
| `get_index_list()` | Master list of all indices |
| `get_index_historical_data(symbol, start, end)` | OHLC + valuation + TRI history |
| `get_index_stocks(index_name)` | Constituent stocks of an index |
| `get_stocks_list()` | All NSE-listed stocks |
| `get_stock_quote(symbol)` | Detailed quote with sector, flags, market cap |
| `get_stock_financials(symbol, consolidated, period)` | Quarterly/annual P&L from XBRL |
| `get_stock_balance_sheet(symbol)` | Balance sheet from annual filings |
| `get_stock_cash_flow(symbol)` | Cash flow statement |
| `get_stock_annual_report(symbol, consolidated)` | Full annual report |
| `get_all_etfs()` | All ETFs with smart categorization |
| `get_etf_historical_data(symbol, start, end)` | ETF OHLCV history |
| `get_vix_historical_data(start, end)` | India VIX history |
| `get_commodity_list()` | Available commodity symbols |
| `get_commodity_historical_data(symbol, start, end)` | Commodity spot prices |

> [!NOTE]
> All functions are `async` and must be awaited. Dates use `YYYY-MM-DD` format throughout.

---

## Technical Highlights

### Robust session management

NSE India requires a warm-up phase to acquire cookies before API requests are accepted. Nifty Terminal implements an automated session that:

1. Performs a headless handshake with `nseindia.com`.
2. Maintains persistent cookies with a shared `httpx` client (auto-refreshed every 10 minutes).
3. Applies rate limiting (3 req/s) and User-Agent rotation to avoid detection.
4. Falls back gracefully on 401 errors by re-establishing the session.

### Financial data normalization

Filing formats change over time. Parsers handle both:

- **XBRL (post-2018):** High-precision extraction using BSE's `in-bse-fin:` taxonomy.
- **Legacy HTML (pre-2018):** Intelligent key mapping to the same normalized schema.

Banking and non-banking (IndAS) taxonomies are both supported.

---

## Disclaimer

This library is for **educational and research purposes only**. It is not affiliated with, maintained, or endorsed by NSE India. Use market data responsibly and adhere to the [NSE Terms of Service](https://www.nseindia.com/terms-of-use).

---

<p align="center">Built with ❤️ for Indian Quants.</p>
