# Nifty Terminal — Claude Project Context

## Commands

```bash
# Install library + CLI deps in editable mode
pip install -e ".[cli]"

# Install with dev deps (includes pytest, click, rich)
pip install -e ".[dev]"

# Run CLI (after install)
niftyterminal --help
niftyterminal market status
niftyterminal index quote --filter "NIFTY 50"
niftyterminal stock quote RELIANCE

# Or invoke without installing
python -m niftyterminal.cli.main --help

# Run tests
pytest tests/

# Build distribution
pip install hatchling
python -m hatchling build
```

## Architecture

```
niftyterminal/
├── niftyterminal/
│   ├── __init__.py          # Public API re-exports (all async functions)
│   ├── exceptions.py        # NiftyTerminalError, SessionError, APIError
│   ├── core/
│   │   └── session.py       # AsyncNSESession, NSESession, NiftyIndicesSession, afetch/fetch helpers
│   ├── api/
│   │   ├── market.py        # get_market_status
│   │   ├── indices.py       # get_all_index_quote, get_index_list, get_index_historical_data, get_index_stocks
│   │   ├── stocks.py        # get_stocks_list, get_stock_quote, get_stock_financials
│   │   ├── etf.py           # get_all_etfs, get_etf_historical_data
│   │   ├── vix.py           # get_vix_historical_data
│   │   ├── commodity.py     # get_commodity_list, get_commodity_historical_data
│   │   ├── fundamentals.py  # get_stock_balance_sheet, get_stock_cash_flow, get_stock_annual_report
│   │   └── _utils.py        # parse_number, has_valid_xbrl, fetch_with_backoff, XBRL_HEADERS
│   └── cli/
│       ├── __init__.py
│       └── main.py          # Click CLI entry point — all commands + rich table formatters
├── tests/
│   └── verify_async.py      # Async integration test runner (not pytest-based)
└── pyproject.toml           # hatchling build; [cli] extra = click + rich
```

## Key Patterns

### Async-first
Every public API function is `async`. The CLI wraps them with `asyncio.run()` via `_run()`. Never call public functions without `await`.

### Session management
- `afetch(url)` — shared `httpx.AsyncClient` with NSE cookie warmup, rate limiting (3 req/s), UA rotation
- `AsyncNSESession` — context manager for batch NSE requests
- `NiftyIndicesSession` — separate session for `niftyindices.com` (different cookie domain)
- Session is shared across calls and auto-refreshed every 10 minutes; 401s trigger re-warmup

### Financial data parsing
- Recent filings → XBRL XML (`in-bse-fin:` namespace) parsed with BeautifulSoup
- Pre-2018 filings → legacy HTML table parser, same output schema
- Banking taxonomy (`BANKING` in filename) vs IndAS taxonomy handled automatically in `_utils.py`

### CLI (`cli/main.py`)
- `rich` is optional — CLI degrades to tab-separated plain text if not installed
- `--json` flag on any command outputs raw dict as formatted JSON (good for piping to `jq`)
- `_run(coro)` → `asyncio.run(coro)` wrapper used by all CLI commands
- Table helpers: `_print_rich_table()`, `_print_kv()`, `_print_section()`, `_walk_dict()`

## Gotchas

- **NSE requires cookie warmup** — cold requests without session handshake return 401 or empty responses. Always use `afetch` / session helpers, never raw `httpx.get`.
- **Rate limiting is enforced at 3 req/s** in `session.py`. Don't bypass it or NSE will block the IP.
- **`get_index_historical_data` symbol** is the index name (e.g. `"NIFTY 50"`), not a short code. It maps to Nifty Indices API internally.
- **Financial results are paginated by NSE** — `get_stock_financials` fetches all available filings. For large companies this can be 100+ filings, each requiring an XBRL fetch. Use `--limit` in CLI or slice `filings[]` in code.
- **`get_all_etfs()` return structure** — returns a dict with `"etfList"` key; the CLI handles both dict and list shapes defensively.
- **Dates** — all public functions accept `YYYY-MM-DD`. Internal NSE APIs use `DD-Mon-YYYY`; conversion is done in each module.
- **`get_commodity_historical_data`** batches requests in 364-day windows to stay within NSE API limits.

## Dependencies

| Package | Purpose |
|---------|---------|
| `httpx` | Async HTTP client (primary) |
| `requests` | Sync HTTP for equity CSV download |
| `beautifulsoup4` | XBRL XML and legacy HTML parsing |
| `click` | CLI framework (optional, `[cli]` extra) |
| `rich` | Terminal tables and panels (optional, `[cli]` extra) |
