"""
test_orders.py — Test the Binance Futures client with multiple quantities.
Run: python test_orders.py
Credentials are read from BINANCE_API_KEY / BINANCE_API_SECRET env vars.
"""

import os
import sys
import json
import time

# Make sure the project root is importable
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from bot.client import BinanceFuturesClient, BinanceClientError

# ── Credentials ───────────────────────────────────────────────────────────────
API_KEY    = os.getenv("BINANCE_API_KEY", "").strip()
API_SECRET = os.getenv("BINANCE_API_SECRET", "").strip()

if not API_KEY or not API_SECRET:
    print("ERROR: Set BINANCE_API_KEY and BINANCE_API_SECRET environment variables.")
    sys.exit(1)

if len(API_KEY) != 64 or len(API_SECRET) != 64:
    print(f"WARNING: Expected 64-char keys. Got key={len(API_KEY)}, secret={len(API_SECRET)}")

client = BinanceFuturesClient(api_key=API_KEY, api_secret=API_SECRET)

SYMBOL = "BTCUSDT"
SEPARATOR = "=" * 75

# ── Quantities to test ────────────────────────────────────────────────────────
BUY_QUANTITIES  = [0.001, 0.005, 0.010, 0.020]
SELL_QUANTITIES = [0.001, 0.005, 0.010, 0.020]

results = []  # list of dicts for final summary table

def place_and_record(side: str, qty: float):
    print(f"\n{SEPARATOR}")
    print(f"  Testing {side:4s} MARKET  |  Symbol: {SYMBOL}  |  Qty: {qty}")
    print(SEPARATOR)
    try:
        resp = client.place_order(
            symbol=SYMBOL,
            side=side,
            order_type="MARKET",
            quantity=qty,
        )
        order_id  = resp.get("orderId", "N/A")
        status    = resp.get("status", "N/A")
        orig_qty  = resp.get("origQty", "N/A")
        exec_qty  = resp.get("executedQty", "N/A")
        avg_price = resp.get("avgPrice", "N/A")

        print(f"  ✅ SUCCESS")
        print(f"     Order ID     : {order_id}")
        print(f"     Status       : {status}")
        print(f"     Ordered Qty  : {orig_qty}")
        print(f"     Executed Qty : {exec_qty}")
        print(f"     Avg Price    : {avg_price} USDT")
        print()
        print("  Full response:")
        print(json.dumps(resp, indent=4))

        results.append({
            "Side": side, "Qty": qty,
            "Result": "SUCCESS", "OrderId": order_id,
            "Status": status, "OrigQty": orig_qty,
            "ExecQty": exec_qty, "Detail": "",
        })

    except BinanceClientError as e:
        err = str(e)
        print(f"  ❌ FAILED: {err}")

        # Human-friendly hint
        if "-2019" in err:
            hint = "Margin insufficient — top up demo account at testnet.binancefuture.com"
        elif "-1022" in err:
            hint = "Signature invalid — re-check your API secret (must be 64 chars)"
        elif "-4164" in err:
            hint = "Order too small — minimum notional is 50 USDT"
        elif "-4120" in err:
            hint = "Order type not supported on demo API"
        elif "-2015" in err:
            hint = "Invalid API key / missing Futures permission"
        else:
            hint = err

        results.append({
            "Side": side, "Qty": qty,
            "Result": "FAILED", "OrderId": "—",
            "Status": "—", "OrigQty": "—",
            "ExecQty": "—", "Detail": hint,
        })

    # Small delay to avoid rate-limit
    time.sleep(0.5)


# ── Ping first ────────────────────────────────────────────────────────────────
print(f"\n{'='*75}")
print("  BINANCE FUTURES DEMO ORDER TEST")
print(f"{'='*75}")
print(f"  API key  : {API_KEY[:8]}...{API_KEY[-4:]}  (len={len(API_KEY)})")
print(f"  API secret: ****...{API_SECRET[-4:]}  (len={len(API_SECRET)})")
print(f"  Symbol   : {SYMBOL}")
print()

is_up = client.ping()
print(f"  API reachable: {'✅ YES' if is_up else '❌ NO'}")
if not is_up:
    print("  Cannot reach demo API. Check network connection.")
    sys.exit(1)

# ── BUY orders ────────────────────────────────────────────────────────────────
print(f"\n{'='*75}")
print("  BUY MARKET ORDERS")
print(f"{'='*75}")
for qty in BUY_QUANTITIES:
    place_and_record("BUY", qty)

# ── SELL orders ───────────────────────────────────────────────────────────────
print(f"\n{'='*75}")
print("  SELL MARKET ORDERS")
print(f"{'='*75}")
for qty in SELL_QUANTITIES:
    place_and_record("SELL", qty)

# ── Summary table ─────────────────────────────────────────────────────────────
print(f"\n\n{'='*75}")
print("  RESULTS SUMMARY")
print(f"{'='*75}")
print(f"  {'Side':<6} {'Qty':>8}  {'Result':<10} {'OrderId':<15} {'OrigQty':<10} {'ExecQty':<10} Detail")
print(f"  {'-'*6} {'-'*8}  {'-'*10} {'-'*15} {'-'*10} {'-'*10} {'-'*30}")
for r in results:
    flag = "✅" if r["Result"] == "SUCCESS" else "❌"
    print(
        f"  {r['Side']:<6} {str(r['Qty']):>8}  {flag} {r['Result']:<8} "
        f"{str(r['OrderId']):<15} {str(r['OrigQty']):<10} {str(r['ExecQty']):<10} "
        f"{r['Detail']}"
    )

print(f"\n  Total: {len(results)} tests | "
      f"Passed: {sum(1 for r in results if r['Result']=='SUCCESS')} | "
      f"Failed: {sum(1 for r in results if r['Result']=='FAILED')}")
print(f"{'='*75}\n")
