"""Price observation only. No trading signal or investment recommendation."""
import csv
import io
import json
import os
from datetime import datetime, timezone
from urllib.parse import urlencode
from urllib.request import Request, urlopen


def snapshot(symbols, fetch=None):
    fetch = fetch or (lambda url: urlopen(Request(url, headers={"User-Agent": "ORION/0.1"}), timeout=15).read().decode())
    results = []
    for symbol in symbols:
        symbol = symbol.strip().lower()
        if not symbol or not all(c.isalnum() or c in ".-" for c in symbol):
            results.append({"symbol": symbol, "status": "invalid_symbol"})
            continue
        url = "https://stooq.com/q/l/?" + urlencode({"s": symbol, "f": "sd2t2ohlcv", "h": "", "e": "csv"})
        try:
            row = next(csv.DictReader(io.StringIO(fetch(url))))
            close = float(row["Close"])
            if close <= 0 or row["Date"] == "N/D":
                raise ValueError("Missing or invalid price")
            results.append({"symbol": symbol, "status": "observed", "date": row["Date"],
                            "close": close, "source": url})
        except (OSError, ValueError, KeyError, StopIteration, TypeError) as exc:
            results.append({"symbol": symbol, "status": "unavailable", "error": str(exc)})
    return {"observed_at": datetime.now(timezone.utc).isoformat(),
            "kind": "price_observation_only", "results": results}


def main():
    symbols = (os.environ.get("ORION_WATCHLIST") or "aapl.us,msft.us,spy.us").split(",")
    report = snapshot(symbols)
    os.makedirs("reports", exist_ok=True)
    with open("reports/latest.json", "w", encoding="utf-8") as output:
        json.dump(report, output, indent=2)
    print(json.dumps(report))
    if not any(item["status"] == "observed" for item in report["results"]):
        raise SystemExit("No market prices available")


if __name__ == "__main__":
    main()
