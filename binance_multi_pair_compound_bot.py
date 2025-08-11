"""
Binance Multi-Pair Compound Trading Bot
Author: ChatGPT
Description: Live trading bot for Binance Futures with multiple trading pairs.
WARNING: Trading is risky. Use at your own risk.
"""

import os
import time
import ccxt
import pandas as pd
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("BINANCE_API_KEY")
API_SECRET = os.getenv("BINANCE_API_SECRET")
TRADING_PAIRS = os.getenv("TRADING_PAIRS", "BTC/USDT,ETH/USDT").split(",")
LEVERAGE = int(os.getenv("LEVERAGE", 5))
RISK_PER_TRADE = float(os.getenv("RISK_PER_TRADE", 0.01))
STOPLOSS_PCT = float(os.getenv("STOPLOSS_PCT", 0.01))
TAKE_PROFIT_PCT = float(os.getenv("TAKE_PROFIT_PCT", 0.02))
TIMEFRAME = os.getenv("TIMEFRAME", "5m")
POLL_INTERVAL = int(os.getenv("POLL_INTERVAL", 60))

exchange = ccxt.binance({
    "apiKey": API_KEY,
    "secret": API_SECRET,
    "enableRateLimit": True,
    "options": {"defaultType": "future"}
})

def set_leverage(pair, leverage):
    try:
        market = exchange.market(pair)
        exchange.fapiPrivate_post_leverage({"symbol": market["id"], "leverage": leverage})
        print(f"Leverage set to {leverage}x for {pair}")
    except Exception as e:
        print(f"Error setting leverage for {pair}: {e}")

def get_signal(df):
    if df["close"].iloc[-1] > df["close"].iloc[-2]:
        return "buy"
    elif df["close"].iloc[-1] < df["close"].iloc[-2]:
        return "sell"
    return None

def place_order(pair, side, amount):
    try:
        order = exchange.create_market_order(pair, side, amount)
        print(f"Order placed: {side} {amount} {pair}")
        return order
    except Exception as e:
        print(f"Error placing order: {e}")
        return None

def run_bot():
    balance = exchange.fetch_balance()
    usdt_balance = balance["total"]["USDT"]
    print(f"USDT Balance: {usdt_balance}")

    for pair in TRADING_PAIRS:
        set_leverage(pair, LEVERAGE)
        ohlcv = exchange.fetch_ohlcv(pair, TIMEFRAME, limit=3)
        df = pd.DataFrame(ohlcv, columns=["time", "open", "high", "low", "close", "volume"])
        signal = get_signal(df)
        if signal:
            risk_amount = usdt_balance * RISK_PER_TRADE
            last_price = df["close"].iloc[-1]
            amount = round(risk_amount / last_price, 3)
            place_order(pair, signal, amount)

if __name__ == "__main__":
    while True:
        run_bot()
        time.sleep(POLL_INTERVAL)
