"""
Stocks API functions.

This module provides functions to fetch stock-related data from NSE India,
including stock lists, quotes, and quarterly/annual financial results 
parsed from NSE's Integrated Filing (iXBRL) pages.
"""

import csv
import random
import httpx
from io import StringIO
from niftyterminal.core import afetch


# NSE Equity CSV URL
EQUITY_CSV_URL = "https://nsearchives.nseindia.com/content/equities/EQUITY_L.csv"

# NSE Quote API endpoints
QUOTE_SYMBOL_DATA_URL = "https://www.nseindia.com/api/NextApi/apiClient/GetQuoteApi"


def _parse_listing_date(date_str: str) -> str:
    """
    Convert date from DD-Mon-YYYY format to YYYY-MM-DD.
    """
    from datetime import datetime
    
    if not date_str:
        return ""
    
    # Handle datetime format with time
    date_part = date_str.split()[0] if " " in date_str else date_str
    
    try:
        dt = datetime.strptime(date_part.strip(), "%d-%b-%Y")
        return dt.strftime("%Y-%m-%d")
    except ValueError:
        return ""


async def _fetch_raw(url: str) -> str:
    """Fetch raw content from URL asynchronously."""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    }
    
    try:
        async with httpx.AsyncClient(headers=headers, follow_redirects=True) as client:
            response = await client.get(url, timeout=10)
            response.raise_for_status()
            return response.text
    except Exception:
        return ""


async def get_stocks_list() -> dict:
    """
    Get the complete list of all listed stocks on NSE asynchronously.
    """
    # Fetch the CSV content
    csv_content = await _fetch_raw(EQUITY_CSV_URL)
    
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
        isin = row.get(" ISIN NUMBER", "").strip()
        
        if not symbol:
            continue
        
        stock_list.append({
            "symbol": symbol,
            "companyName": company_name,
            "series": series,
            "isin": isin,
        })
    
    return {
        "stockList": stock_list,
    }


async def get_stock_quote(symbol: str) -> dict:
    """
    Get quote and detailed information for a specific stock asynchronously.
    """
    import asyncio
    from urllib.parse import quote
    
    # URLs
    symbol_data_url = f"{QUOTE_SYMBOL_DATA_URL}?functionName=getSymbolData&marketType=N&series=EQ&symbol={quote(symbol)}"
    meta_data_url = f"{QUOTE_SYMBOL_DATA_URL}?functionName=getMetaData&symbol={quote(symbol)}"
    
    # Fetch both concurrently
    symbol_response, meta_response = await asyncio.gather(
        afetch(symbol_data_url),
        afetch(meta_data_url)
    )
    
    if not symbol_response:
        return {}
    
    # Parse symbol data
    equity_data = symbol_response.get("equityResponse", [])
    if not equity_data:
        return {}
    
    data = equity_data[0]
    meta_data = data.get("metaData", {})
    trade_info = data.get("tradeInfo", {})
    sec_info = data.get("secInfo", {})
    order_book = data.get("orderBook", {})
    
    # Parse boolean flags
    def parse_bool(val):
        if isinstance(val, bool):
            return val
        if isinstance(val, str):
            return val.lower() == "true"
        return False
    
    # Build result
    result = {
        "symbol": meta_data.get("symbol", symbol),
        "companyName": meta_data.get("companyName", ""),
        "series": meta_data.get("series", ""),
        "listingDate": _parse_listing_date(sec_info.get("listingDate", "")),
        "isin": meta_data.get("isinCode", ""),
        "faceValue": trade_info.get("faceValue", 0),
        "marketCap": trade_info.get("totalMarketCap", 0),
        "secStatus": sec_info.get("secStatus", ""),
        "industry": sec_info.get("basicIndustry", ""),
        "sector": sec_info.get("sector", ""),
        "sectorPe": sec_info.get("pdSectorPe", ""),
        "industryInfo": sec_info.get("industryInfo", ""),
        "macro": sec_info.get("macro", ""),
        "tradingSegment": sec_info.get("tradingSegment", ""),
    }
    
    # Add flags
    if meta_response:
        result["isFNOSec"] = parse_bool(meta_response.get("isFNOSec", False))
        result["isCASec"] = parse_bool(meta_response.get("isCASec", False))
        result["isSLBSec"] = parse_bool(meta_response.get("isSLBSec", False))
        result["isDebtSec"] = parse_bool(meta_response.get("isDebtSec", False))
        result["isSuspended"] = parse_bool(meta_response.get("isSuspended", False))
        result["isETFSec"] = parse_bool(meta_response.get("isETFSec", False))
        result["isDelisted"] = parse_bool(meta_response.get("isDelisted", False))
        result["isMunicipalBond"] = parse_bool(meta_response.get("isMunicipalBond", False))
        result["isHybridSymbol"] = parse_bool(meta_response.get("isHybridSymbol", False))
    else:
        # Default flags
        for flag in ["isFNOSec", "isCASec", "isSLBSec", "isDebtSec", "isSuspended", 
                    "isETFSec", "isDelisted", "isMunicipalBond", "isHybridSymbol"]:
            result[flag] = False
    
    # Price data
    result["open"] = meta_data.get("open", 0)
    result["high"] = meta_data.get("dayHigh", 0)
    result["low"] = meta_data.get("dayLow", 0)
    result["ltp"] = order_book.get("lastPrice", meta_data.get("closePrice", 0))
    result["prevClose"] = meta_data.get("previousClose", 0)
    result["change"] = meta_data.get("change", 0)
    result["percentChange"] = meta_data.get("pChange", 0)
    result["pe"] = sec_info.get("pdSymbolPe", "")
    
    return result


# ---------------------------------------------------------------------------
# Corporates Financial Results
# ---------------------------------------------------------------------------

CORPORATES_FINANCIAL_URL = (
    "https://www.nseindia.com/api/corporates-financial-results"
)


def _parse_number(value_str: str):
    """
    Convert a number string to a float.

    Handles:
      - Commas: "29,26,400.00" → 2926400.0
      - Parenthesized negatives: "(2,68,600.00)" → -268600.0
      - Scientific notation: "1.92388E7" → 19238800.0
      - Dashes: "-" → None
      - Empty / null → None
    """
    if not value_str:
        return None

    s = value_str.strip()
    if not s or s.lower() == "null" or s == "-":
        return None

    negative = False
    if s.startswith("(") and s.endswith(")"):
        negative = True
        s = s[1:-1]

    s = s.replace(",", "").replace("\xa0", "").strip()
    if not s:
        return None

    try:
        val = float(s)
        return -val if negative else val
    except ValueError:
        return None


def _has_valid_xbrl(filing: dict) -> bool:
    """Check if a filing has a valid XBRL URL (not the placeholder '-' URL)."""
    xbrl = filing.get("xbrl", "")
    return bool(xbrl) and not xbrl.endswith("/-") and not xbrl.endswith("/-\"")


def _parse_xbrl_xml(xml_text: str) -> dict:
    """
    Parse an XBRL XML file into a structured financial results dict.

    The XML uses `in-bse-fin:` namespace tags like:
      <in-bse-fin:RevenueFromOperations contextRef="OneD" unitRef="INR">
    """
    from bs4 import BeautifulSoup, XMLParsedAsHTMLWarning
    import warnings
    warnings.filterwarnings("ignore", category=XMLParsedAsHTMLWarning)

    soup = BeautifulSoup(xml_text, "html.parser")

    def _get_val(tag_names):
        """Get float value from a simple (non-segment) XBRL tag(s)."""
        if isinstance(tag_names, str):
            tag_names = [tag_names]
        for tag_name in tag_names:
            for tag in soup.find_all(tag_name.lower()):
                ctx = tag.get("contextref", "")
                if ctx in ("OneD", "OneI"):
                    val = _parse_number(tag.get_text(strip=True))
                    if val is not None:
                        return val
        return None

    def _get_text(tag_name: str) -> str:
        """Get text value from a simple XBRL tag."""
        for tag in soup.find_all(tag_name.lower()):
            ctx = tag.get("contextref", "")
            if ctx in ("OneD", "OneI"):
                return tag.get_text(strip=True)
        return ""

    # --- General Info ---
    general_info = {
        "symbol": _get_text("in-bse-fin:symbol"),
        "fy_start": _get_text("in-bse-fin:dateofstartoffinancialyear"),
        "fy_end": _get_text("in-bse-fin:dateofendoffinancialyear"),
        "rounding_unit": _get_text("in-bse-fin:levelofroundingusedinfinancialstatements"),
        "reporting_quarter": _get_text("in-bse-fin:reportingquarter"),
        "nature": _get_text("in-bse-fin:natureofreportstandaloneconsolidated"),
        "audited": _get_text("in-bse-fin:whetherresultsareauditedorunaudited"),
        "from_date": _get_text("in-bse-fin:dateofstartofreportingperiod"),
        "to_date": _get_text("in-bse-fin:dateofendofreportingperiod"),
        "segment_type": _get_text("in-bse-fin:iscompanyreportingmultisegmentorsinglesegment"),
    }

    # --- Main Financials ---
    financials = {
        "revenue_from_operations": _get_val([
            "in-bse-fin:revenuefromoperations",
            "in-bse-fin:interestearned",          # Banking format
        ]),
        "other_income": _get_val("in-bse-fin:otherincome"),
        "total_income": _get_val(["in-bse-fin:income", "in-bse-fin:totalincome"]),
        "cost_of_materials_consumed": _get_val("in-bse-fin:costofmaterialsconsumed"),
        "purchases_of_stock_in_trade": _get_val("in-bse-fin:purchasesofstockintrade"),
        "changes_in_inventories": _get_val("in-bse-fin:changesininventoriesoffinishedgoodsworkinprogressandstockintrade"),
        "employee_benefit_expense": _get_val([
            "in-bse-fin:employeebenefitexpense",
            "in-bse-fin:paymentstoandprovisionsforemployees",
            "in-bse-fin:employeescost",            # Banking format
        ]),
        "finance_costs": _get_val([
            "in-bse-fin:financecosts",
            "in-bse-fin:interestexpended",         # Banking format
        ]),
        "depreciation": _get_val("in-bse-fin:depreciationdepletionandamortisationexpense"),
        "other_expenses": _get_val([
            "in-bse-fin:otherexpenses",
            "in-bse-fin:otheroperatingexpenses",   # Banking format
            "in-bse-fin:operatingexpenses",
        ]),
        "total_expenses": _get_val([
            "in-bse-fin:expenses",
            "in-bse-fin:totalexpenditure",
            "in-bse-fin:expenditureexcludingprovisionsandcontingencies",  # Banking format
        ]),
        "profit_before_exceptional_items_and_tax": _get_val([
            "in-bse-fin:profitbeforeexceptionalitemsandtax",
            "in-bse-fin:operatingprofitlossbeforeprovisionsandcontingencies",
            "in-bse-fin:operatingprofitbeforeprovisionandcontingencies",  # Banking format
        ]),
        "exceptional_items": _get_val([
            "in-bse-fin:exceptionalitemsbeforetax",
            "in-bse-fin:exceptionalitems",         # Banking format
        ]),
        "profit_before_tax": _get_val([
            "in-bse-fin:profitbeforetax",
            "in-bse-fin:netprofitlossbeforetax",
            "in-bse-fin:profitlossfromordinaryactivitiesbeforetax",  # Banking format
        ]),
        "current_tax": _get_val("in-bse-fin:currenttax"),
        "deferred_tax": _get_val("in-bse-fin:deferredtax"),
        "tax_expense": _get_val(["in-bse-fin:taxexpense", "in-bse-fin:provisionfortaxes"]),
        "net_profit_continuing_operations": _get_val("in-bse-fin:profitlossforperiodfromcontinuingoperations"),
        "profit_discontinued_before_tax": _get_val("in-bse-fin:profitlossfromdiscontinuedoperationsbeforetax"),
        "profit_discontinued_after_tax": _get_val("in-bse-fin:profitlossfromdiscontinuedoperationsaftertax"),
        "share_of_profit_associates": _get_val([
            "in-bse-fin:shareofprofitlossofassociatesandjointventuresaccountedforusingequitymethod",
            "in-bse-fin:shareofprofitlossofassociates",  # Banking format
        ]),
        "net_profit": _get_val([
            "in-bse-fin:profitlossforperiod",
            "in-bse-fin:netprofitlossforperiod",
            "in-bse-fin:profitlossfortheperiod",              # Banking format
            "in-bse-fin:profitlossfromordinaryactivitiesaftertax",  # Banking format alt
        ]),
        "other_comprehensive_income": _get_val("in-bse-fin:othercomprehensiveincomenetoftaxes"),
        "total_comprehensive_income": _get_val("in-bse-fin:comprehensiveincomefortheperiod"),
        "profit_attributable_to_owners": _get_val([
            "in-bse-fin:profitorlossattributabletoownersofparent",
            "in-bse-fin:profitlossaftertaxesminorityinterestandshareofprofitlossofassociates",  # Banking format
        ]),
        "profit_attributable_to_nci": _get_val([
            "in-bse-fin:profitorlossattributabletononcontrollinginterests",
            "in-bse-fin:profitlossofminorityinterest",  # Banking format
        ]),
        "comprehensive_income_owners": _get_val("in-bse-fin:comprehensiveincomefortheperiodattributabletoownersofparent"),
        "comprehensive_income_nci": _get_val("in-bse-fin:comprehensiveincomefortheperiodattributabletoownersofparentnoncontrollinginterests"),
    }

    # --- Equity ---
    equity = {
        "paid_up_capital": _get_val("in-bse-fin:paidupvalueofequitysharecapital"),
        "face_value": _get_val("in-bse-fin:facevalueofequitysharecapital"),
    }

    # --- EPS ---
    eps = {
        "basic_continuing": _get_val([
            "in-bse-fin:basicearningslossperSharefromcontinuingoperations",
            "in-bse-fin:basicearningspersharebeforeextraordinaryitems",  # Banking format
        ]),
        "diluted_continuing": _get_val([
            "in-bse-fin:dilutedearningslossperSharefromcontinuingoperations",
            "in-bse-fin:dilutedearningspersharebeforeextraordinaryitems",  # Banking format
        ]),
        "basic_discontinued": _get_val("in-bse-fin:basicearningslosspersharefromdiscontinuedoperations"),
        "diluted_discontinued": _get_val("in-bse-fin:dilutedearningslosspersharefromdiscontinuedoperations"),
        "basic_total": _get_val([
            "in-bse-fin:basicearningslosspersharefromcontinuinganddiscontinuedoperations",
            "in-bse-fin:basicearningslosspershare",
            "in-bse-fin:basicearningspershare",
            "in-bse-fin:earningsperequitysharebasic",
            "in-bse-fin:basicearningspershareafterextraordinaryitems",   # Banking format
        ]),
        "diluted_total": _get_val([
            "in-bse-fin:dilutedearningslosspersharefromcontinuinganddiscontinuedoperations",
            "in-bse-fin:dilutedearningslosspershare",
            "in-bse-fin:dilutedearningspershare",
            "in-bse-fin:earningsperequitysharediluted",
            "in-bse-fin:dilutedearningspershareafterextraordinaryitems",  # Banking format
        ]),
    }

    # Catch-all EPS parsing if exact tags weren't hit (often the case for different XML variants)
    if not eps["basic_total"]:
        for tag in soup.find_all(True):  # Find all tags
            tag_name = tag.name.lower()
            if "basic" in tag_name and ("earning" in tag_name or "eps" in tag_name):
                ctx = tag.get("contextref", "")
                if ctx in ("OneD", "OneI"):
                    val = _parse_number(tag.get_text(strip=True))
                    if val is not None:
                        eps["basic_total"] = val
                        break

    if not eps["diluted_total"]:
        for tag in soup.find_all(True):
            tag_name = tag.name.lower()
            if "diluted" in tag_name and ("earning" in tag_name or "eps" in tag_name):
                ctx = tag.get("contextref", "")
                if ctx in ("OneD", "OneI"):
                    val = _parse_number(tag.get_text(strip=True))
                    if val is not None:
                        eps["diluted_total"] = val
                        break

    # --- Segments ---
    segments = {}

    # Segment Revenue (tags: DescriptionOfReportableSegment + SegmentRevenue)
    revenue_tags = soup.find_all("in-bse-fin:segmentrevenue")
    for tag in revenue_tags:
        ctx = tag.get("contextref", "")
        if not ctx.startswith("OneReportableSegmentRevenue"):
            continue
        # Find the matching description
        desc_tags = soup.find_all("in-bse-fin:descriptionofreportablesegment")
        for d in desc_tags:
            if d.get("contextref") == ctx:
                name = d.get_text(strip=True)
                if name not in segments:
                    segments[name] = {}
                segments[name]["revenue"] = _parse_number(tag.get_text(strip=True))
                break

    # Segment Profit/Loss
    profit_tags = soup.find_all("in-bse-fin:segmentprofitlossbeforetaxandfinancecosts")
    for tag in profit_tags:
        ctx = tag.get("contextref", "")
        if not ctx.startswith("OneReportableSegmentResults"):
            continue
        desc_tags = soup.find_all("in-bse-fin:descriptionofreportablesegment")
        for d in desc_tags:
            if d.get("contextref") == ctx:
                name = d.get_text(strip=True)
                if name not in segments:
                    segments[name] = {}
                segments[name]["profit"] = _parse_number(tag.get_text(strip=True))
                break

    # Segment Assets
    asset_tags = soup.find_all("in-bse-fin:segmentassets")
    for tag in asset_tags:
        ctx = tag.get("contextref", "")
        if not ctx.startswith("OneReportableSegmentAssets"):
            continue
        desc_tags = soup.find_all("in-bse-fin:descriptionofreportablesegment")
        for d in desc_tags:
            if d.get("contextref") == ctx:
                name = d.get_text(strip=True)
                if name not in segments:
                    segments[name] = {}
                segments[name]["assets"] = _parse_number(tag.get_text(strip=True))
                break

    # Segment Liabilities (note: contextRef uses "I" suffix for instant)
    liability_tags = soup.find_all("in-bse-fin:segmentliabilities")
    for tag in liability_tags:
        ctx = tag.get("contextref", "")
        if "ReportableSegmentLiabilities" not in ctx:
            continue
        # Match description using the "D" version of the context
        d_ctx = ctx.replace("I", "D") if ctx.endswith("I") else ctx
        desc_tags = soup.find_all("in-bse-fin:descriptionofreportablesegment")
        for d in desc_tags:
            if d.get("contextref") == d_ctx:
                name = d.get_text(strip=True)
                if name not in segments:
                    segments[name] = {}
                segments[name]["liabilities"] = _parse_number(tag.get_text(strip=True))
                break

    # Inter-segment revenue
    inter_seg = _get_val("in-bse-fin:intersegmentrevenue")
    if inter_seg is not None:
        financials["inter_segment_revenue"] = inter_seg

    return {
        "general_info": general_info,
        "financials": financials,
        "equity": equity,
        "eps": eps,
        "segments": segments,
    }


def _parse_legacy_html(html: str) -> dict:
    """
    Parse a legacy NSE financial results HTML page (pre-2018 format).

    These pages have a simple two-column table: Description | Amount (Rs. in lakhs)
    and optionally a Segment Reporting table.
    """
    from bs4 import BeautifulSoup
    import re as _re

    # Handle MHTML: extract HTML portion if needed
    if html.strip().startswith("From:") or "MultipartBoundary" in html[:500]:
        match = _re.search(
            r'Content-Location:.*?\.html\r?\n\r?\n(.*?)(?:------MultipartBoundary|$)',
            html, _re.DOTALL
        )
        if match:
            raw = match.group(1)
            import quopri
            html = quopri.decodestring(raw.encode("utf-8", errors="replace")).decode("utf-8", errors="replace")

    soup = BeautifulSoup(html, "html.parser")

    # --- Parse the header table for general info ---
    general_info = {}
    header_table = soup.find("table", class_="table")
    if header_table:
        for tr in header_table.find_all("tr"):
            cells = tr.find_all("td")
            i = 0
            while i < len(cells) - 1:
                label = cells[i].get_text(strip=True).lower()
                value = cells[i + 1].get_text(strip=True)
                if "symbol" in label and "symbol" not in general_info:
                    general_info["symbol"] = value
                elif "company" in label:
                    general_info["company_name"] = value
                elif "audited" in label:
                    general_info["audited"] = value
                elif "consolidated" in label:
                    general_info["nature"] = value
                elif "period ended" in label:
                    general_info["to_date"] = value
                elif "financial year" in label:
                    general_info["financial_year"] = value
                elif "relating to" in label:
                    general_info["reporting_quarter"] = value
                i += 2

    general_info["rounding_unit"] = "Lakhs"  # Legacy format is always in Lakhs

    # --- Parse all tables ---
    tables = soup.find_all("table", class_="table")

    financials = {}
    equity = {}
    eps = {}
    segments = {}

    # Key mappings for the main financial table
    financial_key_map = {
        "net sales/income from operations": "revenue_from_operations",
        "other operating income": "other_operating_income",
        "total income from operations": "revenue_from_operations",
        "other income": "other_income",
        "total income": "total_income",
        "cost of materials consumed": "cost_of_materials_consumed",
        "purchases of stock-in-trade": "purchases_of_stock_in_trade",
        "purchases of stock in trade": "purchases_of_stock_in_trade",
        "changes in inventories": "changes_in_inventories",
        "employee benefits expense": "employee_benefit_expense",
        "employee benefit expense": "employee_benefit_expense",
        "depreciation and amortisation": "depreciation",
        "depreciation": "depreciation",
        "finance costs": "finance_costs",
        "other expenses": "other_expenses",
        "total expenses": "total_expenses",
        "profit / (loss) from before exceptional": "profit_before_exceptional_items_and_tax",
        "exceptional items": "exceptional_items",
        "profit / (loss) from ordinary activities before tax": "profit_before_tax",
        "profit before tax": "profit_before_tax",
        "tax expense": "tax_expense",
        "profit (loss) for the period from continuing operations": "net_profit_continuing_operations",
        "profit/(loss) from discontinued operations": "profit_discontinued_before_tax",
        "profit/(loss) from discontinued operations (after tax)": "profit_discontinued_after_tax",
        "net profit / (loss) for the period": "net_profit",
        "net profit/(loss) for the period": "net_profit",
        "consolidated net profit/loss": "net_profit",
        "share of profit / (loss) of associates": "share_of_profit_associates",
        "minority interest": "profit_attributable_to_nci",
        "other comprehensive income": "other_comprehensive_income",
        "total comprehensive income": "total_comprehensive_income",
    }

    eps_key_map = {
        "basic eps  for continuing operations": "basic_continuing",
        "basic eps for continuing operations": "basic_continuing",
        "diluted eps  for continuing operations": "diluted_continuing",
        "diluted eps for continuing operations": "diluted_continuing",
        "basic eps  for discontinued operations": "basic_discontinued",
        "basic eps for discontinued operations": "basic_discontinued",
        "diluted eps  for discontinued operations": "diluted_discontinued",
        "diluted eps for discontinued operations": "diluted_discontinued",
        "basic eps  for continued and discontinued": "basic_total",
        "basic eps for continued and discontinued": "basic_total",
        "diluted eps for continued and discontinued": "diluted_total",
        "diluted eps  for continued and discontinued": "diluted_total",
    }

    for table in tables:
        rows = table.find_all("tr")
        # Detect if this is the segment table
        header_text = table.get_text(strip=True).lower()
        is_segment = "segment" in header_text and "revenue" in header_text

        if is_segment:
            # Parse segment reporting table
            current_section = None  # revenue, results, assets, liabilities
            for tr in rows:
                cells = tr.find_all("td")
                text = tr.get_text(strip=True).lower()

                if "segment revenue" in text and len(cells) <= 2:
                    current_section = "revenue"
                    continue
                elif "segment results" in text and len(cells) <= 2:
                    current_section = "profit"
                    continue
                elif "segment assets" in text and len(cells) <= 2:
                    current_section = "assets"
                    continue
                elif "segment liabilit" in text and len(cells) <= 2:
                    current_section = "liabilities"
                    continue

                if len(cells) == 2 and current_section:
                    label = cells[0].get_text(strip=True)
                    value = _parse_number(cells[1].get_text(strip=True))

                    # Skip totals and inter-segment lines
                    low = label.lower()
                    if any(skip in low for skip in [
                        "total", "inter segment", "less:", "net sales",
                        "interest", "un-allocable", "unallocable"
                    ]):
                        continue

                    if label and current_section and value is not None:
                        if label not in segments:
                            segments[label] = {}
                        segments[label][current_section] = value
        else:
            # Parse financial results table
            for tr in rows:
                cells = tr.find_all("td")
                if len(cells) < 2:
                    continue

                label = cells[0].get_text(strip=True).lower()
                val_text = cells[-1].get_text(strip=True)

                # Skip section headers (Part I, Expenses, etc.)
                if len(cells) == 1 or not val_text:
                    continue

                # Try financial keys
                for pattern, key in financial_key_map.items():
                    if pattern in label:
                        val = _parse_number(val_text)
                        if val is not None:
                            financials[key] = val
                        break

                # Try EPS keys
                for pattern, key in eps_key_map.items():
                    if pattern in label:
                        eps[key] = _parse_number(val_text)
                        break

                # Equity
                if "paid-up equity share capital" in label or "paid up equity" in label:
                    equity["paid_up_capital"] = _parse_number(val_text)
                elif "face value" in label:
                    equity["face_value"] = _parse_number(val_text)

    return {
        "general_info": general_info,
        "financials": financials,
        "equity": equity,
        "eps": eps,
        "segments": segments,
    }


_XBRL_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Encoding": "gzip, deflate",
    "Connection": "keep-alive",
    "Referer": "https://www.nseindia.com/",
}


async def _fetch_with_backoff(url: str, timeout: int = 15) -> str:
    """
    Fetch raw content with exponential backoff on rate-limit responses (429/503).

    Retries up to 3 times. On 429/503, waits 2^attempt * jitter seconds before
    retrying. On other errors, waits a short random delay.
    """
    import asyncio

    for attempt in range(3):
        try:
            async with httpx.AsyncClient(
                headers=_XBRL_HEADERS, follow_redirects=True
            ) as client:
                resp = await client.get(url, timeout=timeout)
                if resp.status_code in (429, 503):
                    wait = (2 ** attempt) * random.uniform(1.0, 2.0)
                    await asyncio.sleep(wait)
                    continue
                if resp.status_code == 200:
                    return resp.text
        except Exception:
            if attempt < 2:
                await asyncio.sleep(random.uniform(0.5, 1.0))
    return ""


async def _fetch_financial_detail(filing: dict) -> dict:
    """
    Fetch and parse financial detail for a single filing.

    Tries XBRL XML first (if valid URL), then falls back to
    resultDetailedDataLink HTML.
    """
    # Try XBRL XML first
    if _has_valid_xbrl(filing):
        xbrl_url = filing["xbrl"]
        xml_text = await _fetch_with_backoff(xbrl_url, timeout=15)
        if xml_text:
            return _parse_xbrl_xml(xml_text)

    # Fall back to legacy HTML
    html_url = filing.get("resultDetailedDataLink")
    if html_url:
        html = await _fetch_with_backoff(html_url, timeout=15)
        if html:
            return _parse_legacy_html(html)

    return {}


async def get_stock_financials(symbol: str, consolidated: bool = None) -> dict:
    """
    Get quarterly/annual financial results for a stock.

    Fetches filing metadata from NSE's Corporates Financial Results API,
    then downloads and parses each financial report (XBRL XML for recent
    filings, legacy HTML for older ones).

    Args:
        symbol: NSE stock symbol (e.g. "RELIANCE", "HINDALCO").
        consolidated:
            None  → fetch both standalone and consolidated filings (default)
            True  → fetch only consolidated filings
            False → fetch only standalone filings

    Returns:
        {
            "symbol": "RELIANCE",
            "company_name": "Reliance Industries Limited",
            "total_filings": 100,
            "filings": [
                {
                    "from_date": "01-Oct-2024",
                    "to_date": "31-Dec-2024",
                    "nature": "Non-Consolidated",
                    "audited": "Un-Audited",
                    "period": "Quarterly",
                    "relating_to": "Third Quarter",
                    "financial_year": "01-Apr-2024 To 31-Mar-2025",
                    "format": "New",
                    "financial_data": {
                        "general_info": { ... },
                        "financials": { ... },
                        "equity": { ... },
                        "eps": { ... },
                        "segments": { ... },
                    }
                },
                ...
            ]
        }
    """
    import asyncio
    from urllib.parse import quote

    # Fetch the filing list — issuer is derived from symbol via the API
    url = (
        f"{CORPORATES_FINANCIAL_URL}"
        f"?index=equities"
        f"&symbol={quote(symbol)}"
        f"&period=Quarterly"
    )

    response = await afetch(url, timeout=15)

    if not response:
        return {}

    # The API returns a list directly (not wrapped in a "data" key)
    filings_raw = response if isinstance(response, list) else response.get("data", [])

    if not filings_raw:
        return {}

    # Filter by consolidated/standalone
    if consolidated is True:
        filings_raw = [f for f in filings_raw if f.get("consolidated") == "Consolidated"]
    elif consolidated is False:
        filings_raw = [
            f for f in filings_raw
            if f.get("consolidated") in ("Non-Consolidated", "Standalone")
        ]

    if not filings_raw:
        return {}

    company_name = filings_raw[0].get("companyName", "")

    # Fetch & parse all filings concurrently, with a semaphore to prevent NSE rate-limiting
    sem = asyncio.Semaphore(2)

    async def _process_filing(filing: dict) -> dict:
        async with sem:
            await asyncio.sleep(random.uniform(0.5, 1.5))
            financial_data = await _fetch_financial_detail(filing)

        return {
            "seq_number": filing.get("seqNumber"),
            "from_date": filing.get("fromDate", ""),
            "to_date": filing.get("toDate", ""),
            "nature": filing.get("consolidated", ""),
            "audited": filing.get("audited", ""),
            "period": filing.get("period", ""),
            "relating_to": filing.get("relatingTo", ""),
            "financial_year": filing.get("financialYear", ""),
            "format": filing.get("format", ""),
            "ind_as": filing.get("indAs", ""),
            "filing_date": filing.get("filingDate", ""),
            "xbrl_url": filing.get("xbrl", ""),
            "html_url": filing.get("resultDetailedDataLink", ""),
            "financial_data": financial_data,
        }

    tasks = [_process_filing(f) for f in filings_raw]
    filings = await asyncio.gather(*tasks)

    return {
        "symbol": symbol,
        "company_name": company_name,
        "total_filings": len(filings),
        "filings": list(filings),
    }


