# main.py
import ccxt
import time
import math

# === HARD-CODED KEYS (you asked) ===
API_KEY = "YrmVq9oV24FwbtxdzTG0Wg4slA248moV18vTXfwIP91yrKKDQJkf5BQaWiD1x3mY"
API_SECRET = "KrPWIn7tJvwwwRFLD60t7EX5yQ0ueleoN7bkWfXx92tQy8Lixz91ROOP7vLwyaXE"

# === CONFIG ===
SYMBOL = "BTC/USDT"         # pair to trade (use uppercase, slash OK for ccxt)
LEVERAGE = 5                # change as needed (13x is very risky)
USDT_TO_RISK = 10.0         # USD value to use for this market order (use small amount)
TEST_ORDER = False          # Set True to only simulate (no create order) - for debugging

# === Initialize exchange for USDT-M futures ===
exchange = ccxt.binanceusdm({
    "apiKey": API_KEY,
    "secret": API_SECRET,
    "enableRateLimit": True,
    "options": {"defaultType": "future"},
})

def set_leverage(symbol: str, leverage: int):
    # symbol needs to be without slash when calling this endpoint, e.g. BTCUSDT
    sym = symbol.replace("/", "")
    try:
        exchange.fapiPrivate_post_leverage({"symbol": sym, "leverage": int(leverage)})
        print(f"[OK] Leverage set to {leverage}x for {sym}")
    except Exception as e:
        print(f"[WARN] Could not set leverage for {sym}: {e}")

def truncate_qty(symbol: str, qty: float):
    # try to respect market precision
    markets = exchange.load_markets()
    m = markets.get(symbol)
    if not m:
        return qty
    prec = m.get("precision", {}).get("amount")
    if prec is None:
        return qty
    factor = 10 ** prec
    return math.floor(qty * factor) / factor

def place_market_long(symbol: str, usdt_amount: float):
    # fetch price
    ticker = exchange.fetch_ticker(symbol)
    price = float(ticker["last"])
    # compute base asset qty = usdt_amount / price  (note: for futures with leverage margin differs,
    # but creating a market order sized by base qty is okay for small test)
    qty = usdt_amount / price
    qty = truncate_qty(symbol, qty)
    if qty <= 0:
        raise ValueError("Computed qty <= 0, reduce precision/amount")
    print(f"Placing market BUY {qty} {symbol} at ~{price} (USDT used ~{usdt_amount})")
    if TEST_ORDER:
        print("TEST_ORDER=True -> not placing order (simulation mode)")
        return None
    order = exchange.create_market_buy_order(symbol, qty)
    return order

def main():
    print("Starting minimal futures market-order script...")
    # verify credentials by fetching account (will raise if auth missing)
    try:
        balance = exchange.fetch_balance()
        print("Fetched balance snapshot (futures):")
        print(balance.get("total", {}))
    except Exception as e:
        print("Authentication / connectivity error:", e)
        return

    # set leverage (best-effort)
    set_leverage(SYMBOL, LEVERAGE)

    # Small wait to ensure leverage is applied
    time.sleep(1)

    try:
        order = place_market_long(SYMBOL, USDT_TO_RISK)
        print("Order response:")
        print(order)
    except Exception as e:
        print("Order failed:", e)

if __name__ == "__main__":
    main()
