"""Price observation only. No trading signal or investment recommendation."""
import json
import os
from datetime import datetime, timezone
from urllib.parse import quote
from urllib.request import Request, urlopen


def _chart_observation(fetch, url):
    data = json.loads(fetch(url))
    chart = data["chart"]
    if chart.get("error"):
        raise ValueError(str(chart["error"]))
    series = chart["result"][0]
    closes = series["indicators"]["quote"][0]["close"]
    valid = [(time, price) for time, price in zip(series["timestamp"], closes)
             if price is not None and price > 0]
    if not valid:
        raise ValueError("No valid closing prices")
    return valid[-1], bool(closes and closes[-1] is None)


def snapshot(symbols, fetch=None):
    fetch = fetch or (lambda url: urlopen(Request(url, headers={"User-Agent": "Mozilla/5.0"}), timeout=15).read().decode())
    results = []
    for supplied_symbol in symbols:
        symbol = supplied_symbol.strip().upper().removesuffix(".US")
        if not symbol or not all(c.isalnum() or c in ".-" for c in symbol):
            results.append({"symbol": symbol, "status": "invalid_symbol"})
            continue
        daily_url = "https://query1.finance.yahoo.com/v8/finance/chart/" + quote(symbol) + "?range=5d&interval=1d"
        try:
            (timestamp, close), incomplete_daily_bar = _chart_observation(fetch, daily_url)
            source_url = daily_url
            if incomplete_daily_bar:
                intraday_url = "https://query1.finance.yahoo.com/v8/finance/chart/" + quote(symbol) + "?range=1d&interval=5m"
                try:
                    (intraday_timestamp, intraday_close), _ = _chart_observation(fetch, intraday_url)
                    if intraday_timestamp > timestamp:
                        timestamp, close = intraday_timestamp, intraday_close
                        source_url = intraday_url
                except (OSError, ValueError, KeyError, IndexError, TypeError):
                    pass
            results.append({"symbol": symbol, "status": "observed",
                            "date": datetime.fromtimestamp(timestamp, timezone.utc).date().isoformat(),
                            "close": round(float(close), 4), "source": source_url})
        except (OSError, ValueError, KeyError, IndexError, TypeError) as exc:
            results.append({"symbol": symbol, "status": "unavailable", "error": str(exc)})
    return {"observed_at": datetime.now(timezone.utc).isoformat(),
            "kind": "price_observation_only", "results": results}


def main():
    symbols = (os.environ.get("ORION_WATCHLIST") or "AAPL,MSFT,SPY").split(",")
    report = snapshot(symbols)
    os.makedirs("reports", exist_ok=True)
    with open("reports/latest.json", "w", encoding="utf-8") as output:
        json.dump(report, output, indent=2)
    print(json.dumps(report))
    if not any(item["status"] == "observed" for item in report["results"]):
        raise SystemExit("No market prices available")


if __name__ == "__main__":
    main()
