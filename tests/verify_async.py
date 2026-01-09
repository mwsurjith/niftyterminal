import asyncio
import sys
from datetime import datetime, timedelta
import niftyterminal

async def run_test(name, coro):
    print(f"Testing {name}...", end=" ", flush=True)
    try:
        start_time = datetime.now()
        result = await coro
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        if result and (isinstance(result, dict) or isinstance(result, list)):
            print(f"✅ PASS ({duration:.2f}s)")
            return True
        else:
            print(f"❌ FAIL (Empty response) ({duration:.2f}s)")
            return False
    except Exception as e:
        print(f"❌ FAIL (Exception: {e})")
        return False

async def main():
    print(f"Starting Async Verification Suite for niftyterminal v{niftyterminal.__version__}")
    print("-" * 60)
    
    today = datetime.now().strftime("%Y-%m-%d")
    last_week = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
    
    tests = [
        ("get_market_status", niftyterminal.get_market_status()),
        ("get_all_index_quote", niftyterminal.get_all_index_quote()),
        ("get_index_list", niftyterminal.get_index_list()),
        ("get_index_stocks (NIFTY 50)", niftyterminal.get_index_stocks("NIFTY 50")),
        ("get_index_historical_data (NIFTY 50)", niftyterminal.get_index_historical_data("NIFTY 50", last_week)),
        ("get_vix_historical_data", niftyterminal.get_vix_historical_data(last_week)),
        ("get_all_etfs", niftyterminal.get_all_etfs()),
        ("get_etf_historical_data (NIFTYBEES)", niftyterminal.get_etf_historical_data("NIFTYBEES", last_week)),
        ("get_stocks_list", niftyterminal.get_stocks_list()),
        ("get_stock_quote (RELIANCE)", niftyterminal.get_stock_quote("RELIANCE")),
        ("get_commodity_list", niftyterminal.get_commodity_list()),
        ("get_commodity_historical_data (GOLD1G)", niftyterminal.get_commodity_historical_data("GOLD1G", last_week)),
    ]
    
    results = []
    for name, coro in tests:
        # Avoid hitting rate limits by small delay
        await asyncio.sleep(0.5)
        results.append(await run_test(name, coro))
    
    print("-" * 60)
    passed = sum(results)
    total = len(results)
    print(f"Summary: {passed}/{total} tests passed")
    
    if passed < total:
        print("FAILED: Some functions are not working correctly.")
        sys.exit(1)
    else:
        print("SUCCESS: All functions are working correctly in async mode.")
        sys.exit(0)

if __name__ == "__main__":
    asyncio.run(main())
