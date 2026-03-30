"""
niftyterminal CLI — NSE India market data at your fingertips.

Usage:
    niftyterminal [--json] <group> <command> [args...]

Groups:
    market      Market status
    index       Index data (list, quote, stocks, history)
    stock       Stock data (list, quote, financials, balance-sheet, cash-flow, annual-report)
    etf         ETF data (list, history)
    vix         India VIX (history)
    commodity   Commodity spot prices (list, history)
"""

import asyncio
import json
import sys
from datetime import date, timedelta
from typing import Any

import click

try:
    from rich.console import Console
    from rich.table import Table
    from rich import box
    from rich.text import Text
    from rich.panel import Panel
    from rich.columns import Columns
    from rich.padding import Padding

    HAS_RICH = True
    console = Console()
    err_console = Console(stderr=True)
except ImportError:
    HAS_RICH = False
    console = None  # type: ignore[assignment]
    err_console = None  # type: ignore[assignment]

import niftyterminal
from niftyterminal.exceptions import NiftyTerminalError


# ─── Async runner ─────────────────────────────────────────────────────────────

def _run(coro):
    """Run an async coroutine in a new event loop."""
    return asyncio.run(coro)


# ─── Formatting helpers ────────────────────────────────────────────────────────

def _num(val, decimals: int = 2) -> str:
    """Format a number with commas. Returns 'N/A' if val is None or invalid."""
    if val is None or val == "":
        return "N/A"
    try:
        f = float(val)
        if decimals == 0:
            return f"{f:,.0f}"
        return f"{f:,.{decimals}f}"
    except (TypeError, ValueError):
        return str(val)


def _s(val) -> str:
    """Safe string conversion."""
    return str(val) if val is not None else "N/A"


def _bool_icon(val: bool) -> str:
    return "✓" if val else ""


def _change(value, pct=None) -> Any:
    """
    Return a colored rich Text for a change value, or a plain string.
    Green for positive, red for negative.
    """
    try:
        v = float(value)
    except (TypeError, ValueError):
        return "N/A"

    sign = "+" if v >= 0 else ""
    color = "green" if v >= 0 else "red"

    if pct is not None:
        try:
            p = float(pct)
            psign = "+" if p >= 0 else ""
            s = f"{sign}{v:,.2f} ({psign}{p:.2f}%)"
        except (TypeError, ValueError):
            s = f"{sign}{v:,.2f}"
    else:
        s = f"{sign}{v:,.2f}"

    if HAS_RICH:
        return Text(s, style=color)
    return s


def _pct(val) -> Any:
    """Return a colored percentage string."""
    try:
        v = float(val)
    except (TypeError, ValueError):
        return "N/A"
    sign = "+" if v >= 0 else ""
    color = "green" if v >= 0 else "red"
    s = f"{sign}{v:.2f}%"
    if HAS_RICH:
        return Text(s, style=color)
    return s


def _die(msg: str):
    """Print error message to stderr and exit with code 1."""
    if HAS_RICH and err_console:
        err_console.print(f"[bold red]Error:[/bold red] {msg}")
    else:
        click.echo(f"Error: {msg}", err=True)
    sys.exit(1)


# ─── Table helpers ─────────────────────────────────────────────────────────────

def _col(name: str, style: str = "", justify: str = "left", no_wrap: bool = False):
    """Column spec dict."""
    return {"name": name, "style": style, "justify": justify, "no_wrap": no_wrap}


def _print_rich_table(title: str, columns: list, rows: list):
    """Build and print a rich Table, or fall back to tab-separated plain text."""
    if HAS_RICH and console:
        table = Table(
            title=title,
            box=box.SIMPLE_HEAVY,
            show_header=True,
            header_style="bold cyan",
            title_style="bold white",
            show_lines=False,
            pad_edge=True,
        )
        for col in columns:
            table.add_column(
                col["name"],
                style=col.get("style", ""),
                justify=col.get("justify", "left"),
                no_wrap=col.get("no_wrap", False),
            )
        for row in rows:
            table.add_row(*[
                cell if (HAS_RICH and isinstance(cell, Text)) else str(cell)
                for cell in row
            ])
        console.print(table)
    else:
        # Plain-text fallback
        col_names = [c["name"] for c in columns]
        click.echo(f"\n{title}")
        click.echo("─" * 60)
        click.echo("\t".join(col_names))
        click.echo("─" * 60)
        for row in rows:
            click.echo("\t".join(
                cell.plain if (HAS_RICH and isinstance(cell, Text)) else str(cell)
                for cell in row
            ))


def _print_kv(pairs: list, title: str = ""):
    """Print a list of (key, value) pairs as a panel or plain text."""
    if HAS_RICH and console:
        lines = []
        for k, v in pairs:
            if isinstance(v, Text):
                line = Text()
                line.append(f"  {k}: ", style="dim")
                line.append_text(v)
                lines.append(line)
            else:
                lines.append(Text.assemble(
                    Text(f"  {k}: ", style="dim"),
                    Text(str(v) if v is not None else "N/A"),
                ))
        panel_content = Text("\n").join(lines)
        console.print(Panel(panel_content, title=f"[bold]{title}[/bold]", border_style="cyan") if title else panel_content)
    else:
        if title:
            click.echo(f"\n{title}")
            click.echo("─" * 40)
        for k, v in pairs:
            vstr = v.plain if (HAS_RICH and isinstance(v, Text)) else str(v) if v is not None else "N/A"
            click.echo(f"  {k}: {vstr}")


def _print_section(title: str, pairs: list):
    """Print a named section of key-value pairs."""
    if HAS_RICH and console:
        table = Table(box=box.MINIMAL, show_header=False, padding=(0, 1))
        table.add_column("Key", style="dim", width=32)
        table.add_column("Value", style="white")
        for k, v in pairs:
            table.add_row(k, v if (HAS_RICH and isinstance(v, Text)) else str(v) if v is not None else "N/A")
        console.print(Panel(table, title=f"[bold cyan]{title}[/bold cyan]", border_style="dim"))
    else:
        click.echo(f"\n── {title} ──")
        for k, v in pairs:
            vstr = v.plain if (HAS_RICH and isinstance(v, Text)) else str(v) if v is not None else "N/A"
            click.echo(f"  {k:<32} {vstr}")


# ─── Root CLI group ────────────────────────────────────────────────────────────

@click.group()
@click.option(
    "--json", "json_mode",
    is_flag=True, default=False,
    help="Output raw JSON instead of formatted tables.",
)
@click.version_option(
    version=niftyterminal.__version__,
    prog_name="niftyterminal",
    message="niftyterminal %(version)s",
)
@click.pass_context
def cli(ctx, json_mode):
    """NSE India market data at your fingertips.

    Fetch live and historical data from NSE India — indices, stocks, ETFs,
    VIX, commodities, and financial statements.

    \b
    Examples:
      niftyterminal market status
      niftyterminal index quote --filter "NIFTY 50"
      niftyterminal stock quote RELIANCE
      niftyterminal index history "NIFTY 50" --from 2025-01-01
      niftyterminal vix history --from 2025-01-01 --to 2025-03-31
      niftyterminal commodity history GOLD1G --from 2025-01-01
      niftyterminal --json stock quote RELIANCE
    """
    ctx.ensure_object(dict)
    ctx.obj["json"] = json_mode


# ─── market ───────────────────────────────────────────────────────────────────

@cli.group()
def market():
    """Market status commands."""


@market.command("status")
@click.option(
    "--market-type", "-m",
    default="Capital Market",
    type=click.Choice(
        ["Capital Market", "Currency", "Commodity", "Debt", "currencyfuture"],
        case_sensitive=False,
    ),
    show_default=True,
    help="Market segment to query.",
)
@click.pass_context
def market_status(ctx, market_type):
    """Show current market open/close status."""
    try:
        data = _run(niftyterminal.get_market_status(market_type))
    except NiftyTerminalError as e:
        _die(str(e))

    if not data:
        _die("No data returned from API.")

    if ctx.obj["json"]:
        click.echo(json.dumps(data, indent=2))
        return

    status = data.get("marketStatus", "Unknown")
    msg = data.get("marketStatusMessage", "")

    if HAS_RICH and console:
        color = "green" if status.lower() == "open" else "red"
        console.print(Panel(
            f"[bold {color}]{status}[/bold {color}]\n[dim]{msg}[/dim]",
            title=f"[bold]{market_type}[/bold]",
            border_style=color,
            expand=False,
        ))
    else:
        click.echo(f"Market Type : {market_type}")
        click.echo(f"Status      : {status}")
        click.echo(f"Message     : {msg}")


# ─── index ────────────────────────────────────────────────────────────────────

@cli.group()
def index():
    """Index data commands."""


@index.command("list")
@click.option("--filter", "-f", "filter_text", default=None, help="Filter by name (case-insensitive substring).")
@click.option("--type", "-t", "type_filter", default=None, help="Filter by subType (e.g. 'Sectoral').")
@click.pass_context
def index_list(ctx, filter_text, type_filter):
    """List all NSE indices with symbols and categories."""
    try:
        data = _run(niftyterminal.get_index_list())
    except NiftyTerminalError as e:
        _die(str(e))

    if not data:
        _die("No data returned.")

    if ctx.obj["json"]:
        click.echo(json.dumps(data, indent=2))
        return

    indices = data.get("indexList", [])

    if filter_text:
        indices = [i for i in indices if filter_text.lower() in i.get("indexName", "").lower()]
    if type_filter:
        indices = [i for i in indices if type_filter.lower() in i.get("subType", "").lower()]

    if not indices:
        click.echo("No indices match the filter.")
        return

    columns = [
        _col("Index Name", style="bold white", no_wrap=True),
        _col("Symbol", style="cyan"),
        _col("Type", style="dim"),
        _col("F&O", justify="center", style="green"),
    ]
    rows = [
        (
            i.get("indexName", ""),
            i.get("indexSymbol", ""),
            i.get("subType", ""),
            _bool_icon(i.get("derivativesEligiblity", False)),
        )
        for i in indices
    ]
    _print_rich_table(f"NSE Indices ({len(indices)})", columns, rows)


@index.command("quote")
@click.option("--filter", "-f", "filter_text", default=None, help="Filter by index name (case-insensitive).")
@click.option("--top", "-n", type=int, default=None, help="Show only the first N results.")
@click.pass_context
def index_quote(ctx, filter_text, top):
    """Get live quotes for all NSE indices."""
    try:
        data = _run(niftyterminal.get_all_index_quote())
    except NiftyTerminalError as e:
        _die(str(e))

    if not data:
        _die("No data returned.")

    if ctx.obj["json"]:
        click.echo(json.dumps(data, indent=2))
        return

    quotes = data.get("indexQuote", [])
    timestamp = data.get("timestamp", "")

    if filter_text:
        quotes = [q for q in quotes if filter_text.lower() in q.get("indexName", "").lower()]
    if top:
        quotes = quotes[:top]

    if not quotes:
        click.echo("No quotes found.")
        return

    columns = [
        _col("Index", style="bold white", no_wrap=True),
        _col("LTP", justify="right", style="bold yellow"),
        _col("Change", justify="right"),
        _col("Open", justify="right"),
        _col("High", justify="right"),
        _col("Low", justify="right"),
        _col("PE", justify="right"),
        _col("PB", justify="right"),
        _col("DY%", justify="right"),
        _col("1W%", justify="right"),
        _col("1M%", justify="right"),
        _col("1Y%", justify="right"),
    ]
    rows = [
        (
            q.get("indexName", ""),
            _num(q.get("ltp")),
            _change(q.get("change"), q.get("percentChange")),
            _num(q.get("open")),
            _num(q.get("high")),
            _num(q.get("low")),
            _num(q.get("pe")),
            _num(q.get("pb")),
            _num(q.get("dy")),
            _pct(q.get("oneWeekAgoPercentChange")),
            _pct(q.get("30dAgoPercentChange")),
            _pct(q.get("365dAgoPercentChange")),
        )
        for q in quotes
    ]
    title = f"Index Quotes — {timestamp}" if timestamp else f"Index Quotes ({len(quotes)})"
    _print_rich_table(title, columns, rows)


@index.command("stocks")
@click.argument("name")
@click.pass_context
def index_stocks(ctx, name):
    """List constituent stocks of an index.

    \b
    Example:
      niftyterminal index stocks "NIFTY 50"
      niftyterminal index stocks "NIFTY BANK"
    """
    try:
        data = _run(niftyterminal.get_index_stocks(name))
    except NiftyTerminalError as e:
        _die(str(e))

    if not data:
        _die(f"No data returned for index '{name}'.")

    if ctx.obj["json"]:
        click.echo(json.dumps(data, indent=2))
        return

    index_name = data.get("indexName", name)
    trade_date = data.get("date", "")
    stocks = data.get("stockList", [])

    if not stocks:
        click.echo(f"No stocks found for '{index_name}'.")
        return

    columns = [
        _col("#", justify="right", style="dim"),
        _col("Symbol", style="bold cyan", no_wrap=True),
        _col("Company Name", style="white"),
        _col("ISIN", style="dim"),
    ]
    rows = [
        (str(i + 1), s.get("symbol", ""), s.get("companyName", ""), s.get("isin", ""))
        for i, s in enumerate(stocks)
    ]
    title = f"{index_name} — {len(stocks)} stocks" + (f" (as of {trade_date})" if trade_date else "")
    _print_rich_table(title, columns, rows)


@index.command("history")
@click.argument("symbol")
@click.option("--from", "from_date", required=True, metavar="YYYY-MM-DD", help="Start date.")
@click.option("--to", "to_date", default=None, metavar="YYYY-MM-DD", help="End date (default: today).")
@click.pass_context
def index_history(ctx, symbol, from_date, to_date):
    """Get historical OHLC + valuation data for an index.

    \b
    Example:
      niftyterminal index history "NIFTY 50" --from 2025-01-01
      niftyterminal index history "NIFTY BANK" --from 2025-01-01 --to 2025-03-31
    """
    try:
        data = _run(niftyterminal.get_index_historical_data(symbol, from_date, to_date))
    except NiftyTerminalError as e:
        _die(str(e))

    if not data:
        _die(f"No historical data for '{symbol}'. Check the symbol and date range.")

    if ctx.obj["json"]:
        click.echo(json.dumps(data, indent=2))
        return

    rows_data = data.get("indexData", [])
    if not rows_data:
        click.echo("No data rows returned.")
        return

    columns = [
        _col("Date", style="dim", no_wrap=True),
        _col("Open", justify="right"),
        _col("High", justify="right"),
        _col("Low", justify="right"),
        _col("Close", justify="right", style="bold yellow"),
        _col("PE", justify="right"),
        _col("PB", justify="right"),
        _col("DivYield", justify="right"),
        _col("TRI", justify="right"),
    ]
    rows = [
        (
            r.get("date", ""),
            _num(r.get("open")),
            _num(r.get("high")),
            _num(r.get("low")),
            _num(r.get("close")),
            _num(r.get("PE")),
            _num(r.get("PB")),
            _num(r.get("divYield")),
            _num(r.get("totalReturnsIndex")),
        )
        for r in rows_data
    ]
    title = f"{symbol} — Historical Data ({len(rows_data)} days)"
    _print_rich_table(title, columns, rows)


# ─── stock ────────────────────────────────────────────────────────────────────

@cli.group()
def stock():
    """Stock data commands."""


@stock.command("list")
@click.option("--search", "-s", default=None, help="Search by symbol or company name (case-insensitive).")
@click.option("--series", default=None, help="Filter by series (e.g. EQ, BE, SM).")
@click.option("--top", "-n", type=int, default=None, help="Show only first N results.")
@click.pass_context
def stock_list(ctx, search, series, top):
    """List all NSE-listed stocks."""
    try:
        data = _run(niftyterminal.get_stocks_list())
    except NiftyTerminalError as e:
        _die(str(e))

    if not data:
        _die("No data returned.")

    if ctx.obj["json"]:
        click.echo(json.dumps(data, indent=2))
        return

    stocks = data.get("stockList", [])

    if search:
        q = search.lower()
        stocks = [s for s in stocks if q in s.get("symbol", "").lower() or q in s.get("companyName", "").lower()]
    if series:
        stocks = [s for s in stocks if s.get("series", "").upper() == series.upper()]
    if top:
        stocks = stocks[:top]

    if not stocks:
        click.echo("No stocks match the filter.")
        return

    columns = [
        _col("Symbol", style="bold cyan", no_wrap=True),
        _col("Company Name", style="white"),
        _col("Series", justify="center"),
        _col("ISIN", style="dim"),
    ]
    rows = [
        (s.get("symbol", ""), s.get("companyName", ""), s.get("series", ""), s.get("isin", ""))
        for s in stocks
    ]
    _print_rich_table(f"NSE Stocks ({len(stocks)})", columns, rows)


@stock.command("quote")
@click.argument("symbol")
@click.pass_context
def stock_quote(ctx, symbol):
    """Get a detailed quote for a stock.

    \b
    Example:
      niftyterminal stock quote RELIANCE
      niftyterminal stock quote TCS
    """
    try:
        data = _run(niftyterminal.get_stock_quote(symbol.upper()))
    except NiftyTerminalError as e:
        _die(str(e))

    if not data:
        _die(f"No data found for symbol '{symbol.upper()}'. Is the symbol correct?")

    if ctx.obj["json"]:
        click.echo(json.dumps(data, indent=2))
        return

    if not HAS_RICH or not console:
        # Plain text output
        for k, v in data.items():
            click.echo(f"  {k:<24} {v}")
        return

    # ── Rich layout ──
    sym = data.get("symbol", symbol.upper())
    company = data.get("companyName", "")
    ltp = data.get("ltp", 0)
    change = data.get("change", 0)
    pct = data.get("percentChange", 0)

    # Header panel
    try:
        v = float(change)
        color = "green" if v >= 0 else "red"
        sign = "+" if v >= 0 else ""
        pct_f = float(pct)
        psign = "+" if pct_f >= 0 else ""
        change_str = f"[{color}]{sign}{v:,.2f}  ({psign}{pct_f:.2f}%)[/{color}]"
    except (TypeError, ValueError):
        change_str = "N/A"
        color = "white"

    header = (
        f"[bold white]{company}[/bold white]  [dim]({sym})[/dim]\n"
        f"[bold {color}]{_num(ltp)}[/bold {color}]  {change_str}"
    )
    console.print(Panel(header, border_style=color, expand=False))

    # Price info
    _print_section("Price", [
        ("Open", _num(data.get("open"))),
        ("High", _num(data.get("high"))),
        ("Low", _num(data.get("low"))),
        ("Prev Close", _num(data.get("prevClose"))),
        ("PE (Stock)", _num(data.get("pe"))),
        ("PE (Sector)", _num(data.get("sectorPe"))),
        ("Market Cap", f"₹{_num(data.get('marketCap'))} Cr"),
    ])

    # Company info
    _print_section("Company Info", [
        ("ISIN", _s(data.get("isin"))),
        ("Series", _s(data.get("series"))),
        ("Face Value", _num(data.get("faceValue"), decimals=0)),
        ("Listing Date", _s(data.get("listingDate"))),
        ("Industry", _s(data.get("industry"))),
        ("Sector", _s(data.get("sector"))),
        ("Macro", _s(data.get("macro"))),
        ("Status", _s(data.get("secStatus"))),
        ("Segment", _s(data.get("tradingSegment"))),
    ])

    # Flags
    flags = []
    flag_map = {
        "isFNOSec": "F&O",
        "isCASec": "Corp Action",
        "isSLBSec": "SLB",
        "isDebtSec": "Debt",
        "isSuspended": "Suspended",
        "isETFSec": "ETF",
        "isDelisted": "Delisted",
        "isMunicipalBond": "Muni Bond",
        "isHybridSymbol": "Hybrid",
    }
    for key, label in flag_map.items():
        if data.get(key):
            flags.append(label)

    if flags:
        _print_section("Flags", [(f, "✓") for f in flags])


@stock.command("financials")
@click.argument("symbol")
@click.option(
    "--period", "-p",
    type=click.Choice(["Quarterly", "Annual", "Both"], case_sensitive=False),
    default="Quarterly",
    show_default=True,
    help="Reporting period.",
)
@click.option("--consolidated", "nature", flag_value="consolidated", default=None, help="Consolidated filings only.")
@click.option("--standalone", "nature", flag_value="standalone", help="Standalone filings only.")
@click.option("--limit", "-l", type=int, default=8, show_default=True, help="Max filings to show.")
@click.pass_context
def stock_financials(ctx, symbol, period, nature, limit):
    """Get quarterly/annual financial results for a stock.

    \b
    Example:
      niftyterminal stock financials RELIANCE
      niftyterminal stock financials TCS --period Annual --consolidated
      niftyterminal stock financials HDFCBANK --limit 4
    """
    consolidated_flag = None
    if nature == "consolidated":
        consolidated_flag = True
    elif nature == "standalone":
        consolidated_flag = False

    try:
        data = _run(niftyterminal.get_stock_financials(
            symbol.upper(),
            consolidated=consolidated_flag,
            period=period.capitalize(),
        ))
    except NiftyTerminalError as e:
        _die(str(e))

    if not data:
        _die(f"No financial data for '{symbol.upper()}'.")

    if ctx.obj["json"]:
        click.echo(json.dumps(data, indent=2))
        return

    filings = data.get("filings", [])
    company = data.get("company_name", symbol.upper())
    total = data.get("total_filings", len(filings))

    if not filings:
        click.echo("No filings found.")
        return

    # Limit display
    show = filings[:limit]

    columns = [
        _col("Period", style="dim", no_wrap=True),
        _col("Nature", style="dim"),
        _col("Audited"),
        _col("Revenue", justify="right", style="white"),
        _col("PBT", justify="right"),
        _col("Net Profit", justify="right", style="bold yellow"),
        _col("EPS Basic", justify="right"),
        _col("EPS Diluted", justify="right"),
    ]

    rows = []
    for f in show:
        fd = f.get("financial_data", {})
        fin = fd.get("financials", {})
        eps = fd.get("eps", {})
        gi = fd.get("general_info", {})

        period_label = f"{f.get('from_date', '')} → {f.get('to_date', '')}"
        nat = f.get("nature", "")
        aud = f.get("audited", "")

        revenue = fin.get("revenue_from_operations") or fin.get("total_income")
        pbt = fin.get("profit_before_tax")
        net = fin.get("net_profit")
        eps_b = eps.get("basic_total")
        eps_d = eps.get("diluted_total")

        # Colour net profit
        net_cell = _change(net) if net is not None else "N/A"

        rows.append((
            period_label,
            nat,
            aud,
            _num(revenue),
            _num(pbt),
            net_cell,
            _num(eps_b),
            _num(eps_d),
        ))

    title = f"{company} ({symbol.upper()}) — {period} Financials ({len(show)}/{total} filings)"
    _print_rich_table(title, columns, rows)

    if len(filings) > limit:
        click.echo(f"  [Showing {limit} of {total}. Use --limit to see more, or --json for full data.]")


@stock.command("balance-sheet")
@click.argument("symbol")
@click.pass_context
def stock_balance_sheet(ctx, symbol):
    """Get the latest balance sheet for a stock.

    \b
    Example:
      niftyterminal stock balance-sheet RELIANCE
    """
    try:
        data = _run(niftyterminal.get_stock_balance_sheet(symbol.upper()))
    except NiftyTerminalError as e:
        _die(str(e))

    if not data:
        _die(f"No balance sheet data for '{symbol.upper()}'.")

    if ctx.obj["json"]:
        click.echo(json.dumps(data, indent=2))
        return

    _print_financial_statement(data, symbol.upper(), "Balance Sheet")


@stock.command("cash-flow")
@click.argument("symbol")
@click.pass_context
def stock_cash_flow(ctx, symbol):
    """Get the latest cash flow statement for a stock.

    \b
    Example:
      niftyterminal stock cash-flow RELIANCE
    """
    try:
        data = _run(niftyterminal.get_stock_cash_flow(symbol.upper()))
    except NiftyTerminalError as e:
        _die(str(e))

    if not data:
        _die(f"No cash flow data for '{symbol.upper()}'.")

    if ctx.obj["json"]:
        click.echo(json.dumps(data, indent=2))
        return

    _print_financial_statement(data, symbol.upper(), "Cash Flow Statement")


@stock.command("annual-report")
@click.argument("symbol")
@click.option("--consolidated", "nature", flag_value="consolidated", default=None, help="Consolidated only.")
@click.option("--standalone", "nature", flag_value="standalone", help="Standalone only.")
@click.pass_context
def stock_annual_report(ctx, symbol, nature):
    """Get the complete annual report (P&L + Balance Sheet + Cash Flow).

    \b
    Example:
      niftyterminal stock annual-report RELIANCE
      niftyterminal stock annual-report TCS --consolidated
    """
    consolidated_flag = None
    if nature == "consolidated":
        consolidated_flag = True
    elif nature == "standalone":
        consolidated_flag = False

    try:
        data = _run(niftyterminal.get_stock_annual_report(symbol.upper(), consolidated=consolidated_flag))
    except NiftyTerminalError as e:
        _die(str(e))

    if not data:
        _die(f"No annual report data for '{symbol.upper()}'.")

    if ctx.obj["json"]:
        click.echo(json.dumps(data, indent=2))
        return

    _print_financial_statement(data, symbol.upper(), "Annual Report")


def _print_financial_statement(data: dict, symbol: str, title: str):
    """
    Generic pretty-printer for balance sheet / cash flow / annual report.
    Walks the dict tree and prints sections recursively.
    """
    if HAS_RICH and console:
        console.print(f"\n[bold white]{symbol} — {title}[/bold white]\n")
    else:
        click.echo(f"\n{symbol} — {title}\n")

    _walk_dict(data, depth=0)


def _walk_dict(d: dict, depth: int = 0):
    """
    Recursively walk and display a nested dict.
    - Dicts become sections/panels
    - Leaf values (numbers, strings) become key-value rows
    """
    if not isinstance(d, dict):
        return

    # Collect leaf items and sub-dicts separately
    leaves = [(k, v) for k, v in d.items() if not isinstance(v, (dict, list))]
    sub_dicts = [(k, v) for k, v in d.items() if isinstance(v, dict)]
    lists = [(k, v) for k, v in d.items() if isinstance(v, list)]

    # Print leaf key-values as a table
    if leaves:
        if HAS_RICH and console:
            table = Table(box=box.MINIMAL, show_header=False, padding=(0, 1), expand=False)
            table.add_column("Key", style="dim", min_width=36)
            table.add_column("Value", style="white", justify="right")
            for k, v in leaves:
                label = k.replace("_", " ").title()
                val_str = f"{float(v):,.2f}" if isinstance(v, (int, float)) else _s(v)
                table.add_row(label, val_str)
            console.print(Padding(table, (0, 0, 0, depth * 2)))
        else:
            for k, v in leaves:
                label = k.replace("_", " ").title()
                val_str = f"{float(v):,.2f}" if isinstance(v, (int, float)) else _s(v)
                click.echo(f"{'  ' * depth}{label:<36} {val_str}")

    # Print lists (e.g. array of records)
    for k, lst in lists:
        label = k.replace("_", " ").title()
        if HAS_RICH and console:
            console.print(f"\n[bold cyan]{label}[/bold cyan]")
        else:
            click.echo(f"\n{label}")
        for item in lst:
            if isinstance(item, dict):
                _walk_dict(item, depth + 1)
            else:
                click.echo(f"  {item}")

    # Recurse into sub-dicts
    for k, sub in sub_dicts:
        label = k.replace("_", " ").title()
        if HAS_RICH and console:
            console.print(f"\n[bold cyan]{label}[/bold cyan]")
            _walk_dict(sub, depth + 1)
        else:
            click.echo(f"\n── {label} ──")
            _walk_dict(sub, depth + 1)


# ─── etf ──────────────────────────────────────────────────────────────────────

@cli.group()
def etf():
    """ETF data commands."""


@etf.command("list")
@click.option("--search", "-s", default=None, help="Search by symbol or company name.")
@click.option("--asset-type", "-a", default=None, help="Filter by asset type (e.g. Equity, Gold, Debt).")
@click.option("--top", "-n", type=int, default=None, help="Show first N results.")
@click.pass_context
def etf_list(ctx, search, asset_type, top):
    """List all NSE ETFs with smart asset categorization."""
    try:
        data = _run(niftyterminal.get_all_etfs())
    except NiftyTerminalError as e:
        _die(str(e))

    if not data:
        _die("No ETF data returned.")

    if ctx.obj["json"]:
        click.echo(json.dumps(data, indent=2))
        return

    # get_all_etfs returns a dict with 'etfList' key or a list directly
    etfs = data.get("etfList", data) if isinstance(data, dict) else data
    if not isinstance(etfs, list):
        etfs = list(etfs.values()) if isinstance(etfs, dict) else []

    if search:
        q = search.lower()
        etfs = [e for e in etfs if q in e.get("symbol", "").lower() or q in e.get("companyName", "").lower()]
    if asset_type:
        etfs = [e for e in etfs if asset_type.lower() in (e.get("assetType") or "").lower()]
    if top:
        etfs = etfs[:top]

    if not etfs:
        click.echo("No ETFs match the filter.")
        return

    columns = [
        _col("Symbol", style="bold cyan", no_wrap=True),
        _col("Company Name", style="white"),
        _col("Asset Type", style="yellow"),
        _col("Underlying Asset", style="dim"),
        _col("Variant", style="dim"),
        _col("Listing Date", style="dim"),
    ]
    rows = [
        (
            e.get("symbol", ""),
            e.get("companyName", ""),
            e.get("assetType", "") or "",
            e.get("underlyingAsset", "") or "",
            e.get("indexVariant", "") or "",
            e.get("listingDate", "") or "",
        )
        for e in etfs
    ]
    _print_rich_table(f"NSE ETFs ({len(etfs)})", columns, rows)


@etf.command("history")
@click.argument("symbol")
@click.option("--from", "from_date", required=True, metavar="YYYY-MM-DD", help="Start date.")
@click.option("--to", "to_date", default=None, metavar="YYYY-MM-DD", help="End date (default: today).")
@click.pass_context
def etf_history(ctx, symbol, from_date, to_date):
    """Get historical OHLCV data for an ETF.

    \b
    Example:
      niftyterminal etf history NIFTYBEES --from 2025-01-01
    """
    try:
        data = _run(niftyterminal.get_etf_historical_data(symbol.upper(), from_date, to_date))
    except NiftyTerminalError as e:
        _die(str(e))

    if not data:
        _die(f"No historical data for ETF '{symbol.upper()}'.")

    if ctx.obj["json"]:
        click.echo(json.dumps(data, indent=2))
        return

    rows_data = data.get("etfData", [])
    if not rows_data:
        click.echo("No data rows.")
        return

    columns = [
        _col("Date", style="dim", no_wrap=True),
        _col("Open", justify="right"),
        _col("High", justify="right"),
        _col("Low", justify="right"),
        _col("Close", justify="right", style="bold yellow"),
        _col("Volume", justify="right", style="cyan"),
    ]
    rows = [
        (
            r.get("date", ""),
            _num(r.get("open")),
            _num(r.get("high")),
            _num(r.get("low")),
            _num(r.get("close")),
            _num(r.get("volume"), decimals=0),
        )
        for r in rows_data
    ]
    _print_rich_table(f"{symbol.upper()} — ETF History ({len(rows_data)} days)", columns, rows)


# ─── vix ──────────────────────────────────────────────────────────────────────

@cli.group()
def vix():
    """India VIX (volatility index) commands."""


@vix.command("history")
@click.option("--from", "from_date", required=True, metavar="YYYY-MM-DD", help="Start date.")
@click.option("--to", "to_date", default=None, metavar="YYYY-MM-DD", help="End date (default: today).")
@click.pass_context
def vix_history(ctx, from_date, to_date):
    """Get historical India VIX data.

    \b
    Example:
      niftyterminal vix history --from 2025-01-01
      niftyterminal vix history --from 2025-01-01 --to 2025-03-31
    """
    try:
        data = _run(niftyterminal.get_vix_historical_data(from_date, to_date))
    except NiftyTerminalError as e:
        _die(str(e))

    if not data:
        _die("No VIX data returned. Check your date range.")

    if ctx.obj["json"]:
        click.echo(json.dumps(data, indent=2))
        return

    rows_data = data.get("vixData", [])
    if not rows_data:
        click.echo("No VIX data rows.")
        return

    columns = [
        _col("Date", style="dim", no_wrap=True),
        _col("Open", justify="right"),
        _col("High", justify="right"),
        _col("Low", justify="right"),
        _col("Close", justify="right", style="bold yellow"),
    ]
    rows = [
        (
            r.get("date", ""),
            _num(r.get("open")),
            _num(r.get("high")),
            _num(r.get("low")),
            _num(r.get("close")),
        )
        for r in rows_data
    ]
    _print_rich_table(f"India VIX — History ({len(rows_data)} days)", columns, rows)


# ─── commodity ────────────────────────────────────────────────────────────────

@cli.group()
def commodity():
    """Commodity spot price commands."""


@commodity.command("list")
@click.pass_context
def commodity_list(ctx):
    """List all available commodity symbols."""
    try:
        data = _run(niftyterminal.get_commodity_list())
    except NiftyTerminalError as e:
        _die(str(e))

    if not data:
        _die("No commodity data returned.")

    if ctx.obj["json"]:
        click.echo(json.dumps(data, indent=2))
        return

    items = data.get("commodityList", [])
    if not items:
        click.echo("No commodities found.")
        return

    columns = [
        _col("#", justify="right", style="dim"),
        _col("Symbol", style="bold cyan"),
    ]
    rows = [(str(i + 1), c.get("symbol", "")) for i, c in enumerate(items)]
    _print_rich_table(f"Commodities ({len(items)})", columns, rows)


@commodity.command("history")
@click.argument("symbol")
@click.option("--from", "from_date", required=True, metavar="YYYY-MM-DD", help="Start date.")
@click.option("--to", "to_date", default=None, metavar="YYYY-MM-DD", help="End date (default: today).")
@click.pass_context
def commodity_history(ctx, symbol, from_date, to_date):
    """Get historical spot price data for a commodity.

    \b
    Example:
      niftyterminal commodity list
      niftyterminal commodity history GOLD1G --from 2025-01-01
      niftyterminal commodity history SILVER1KG --from 2025-01-01 --to 2025-03-31
    """
    try:
        data = _run(niftyterminal.get_commodity_historical_data(symbol.upper(), from_date, to_date))
    except NiftyTerminalError as e:
        _die(str(e))

    if not data:
        _die(f"No data for commodity '{symbol.upper()}'. Use 'commodity list' to see valid symbols.")

    if ctx.obj["json"]:
        click.echo(json.dumps(data, indent=2))
        return

    rows_data = data.get("commodityData", [])
    if not rows_data:
        click.echo("No data rows.")
        return

    # Get unit from first row
    unit = rows_data[0].get("unit", "") if rows_data else ""
    unit_label = f" ({unit})" if unit else ""

    columns = [
        _col("Date", style="dim", no_wrap=True),
        _col(f"Spot Price 1{unit_label}", justify="right", style="bold yellow"),
        _col(f"Spot Price 2{unit_label}", justify="right"),
    ]
    rows = [
        (
            r.get("date", ""),
            _num(r.get("spotPrice1"), decimals=0),
            _num(r.get("spotPrice2"), decimals=0),
        )
        for r in rows_data
    ]
    _print_rich_table(
        f"{symbol.upper()} — Spot Price History ({len(rows_data)} days)",
        columns, rows,
    )


# ─── Entry point ──────────────────────────────────────────────────────────────

def main():
    """Entry point for the niftyterminal CLI."""
    cli(obj={})


if __name__ == "__main__":
    main()
