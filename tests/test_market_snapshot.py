from orion.market_snapshot import snapshot


def test_price_observation_and_missing_data():
    def fetch(url):
        if "aapl.us" in url:
            return "Symbol,Date,Time,Open,High,Low,Close,Volume\nAAPL.US,2026-09-25,22:00:00,100,101,99,100.5,1000\n"
        return "Symbol,Date,Time,Open,High,Low,Close,Volume\nBAD.US,N/D,N/D,N/D,N/D,N/D,N/D,N/D\n"

    result = snapshot(["aapl.us", "bad.us"], fetch)
    assert result["results"][0]["close"] == 100.5
    assert result["results"][1]["status"] == "unavailable"
    assert result["kind"] == "price_observation_only"
