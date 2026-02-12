import requests
import pandas as pd
import time

BASE_URL = "https://api.binance.com/api/v3/klines"
TIMEFRAME = "5m"
CANDLES = 50

def load_pairs():
    with open("pairs.txt", "r") as f:
        return [line.strip() for line in f if line.strip()]

def fetch_candles(symbol):
    params = {
        "symbol": symbol,
        "interval": TIMEFRAME,
        "limit": CANDLES
    }
    r = requests.get(BASE_URL, params=params, timeout=10)
    r.raise_for_status()
    data = r.json()

    df = pd.DataFrame(data, columns=[
        "time","open","high","low","close","volume",
        "_","_","_","_","_","_"
    ])

    df = df.astype({
        "open": float,
        "high": float,
        "low": float,
        "close": float,
        "volume": float
    })

    return df

def analyse(df):
    price_change = (df["close"].iloc[-1] - df["open"].iloc[0]) / df["open"].iloc[0] * 100

    candle_ranges = (df["high"] - df["low"]) / df["open"] * 100
    avg_candle = candle_ranges.mean()

    volume_mean = df["volume"].mean()
    volume_std = df["volume"].std()

    liquidity_thin = volume_std > volume_mean * 0.8
    volatility_spike = candle_ranges.iloc[-1] > avg_candle * 2

    risk = (
        abs(price_change) * 0.4 +
        avg_candle * 40 +
        (20 if volatility_spike else 0) +
        (20 if liquidity_thin else 0)
    )

    return {
        "Δ%": round(price_change, 2),
        "AvgCandle%": round(avg_candle, 2),
        "VolSpike": volatility_spike,
        "ThinLiquidity": liquidity_thin,
        "Risk": round(min(risk, 100), 1)
    }

def main():
    pairs = load_pairs()
    results = []

    for pair in pairs:
        try:
            df = fetch_candles(pair)
            analysis = analyse(df)
            analysis["Pair"] = pair
            results.append(analysis)
            time.sleep(0.1)
        except Exception as e:
            print(f"{pair}: error ({e})")

    table = pd.DataFrame(results)
    table = table.sort_values("Risk", ascending=False)

    print("\nMarket Noise Filter\n")
    print(table.to_string(index=False))

if __name__ == "__main__":
    main()
