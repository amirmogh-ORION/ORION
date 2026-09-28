import json
from orion.market_snapshot import snapshot


def test_price_observation_and_missing_data():
    def fetch(url):
        if "AAPL" in url:
            return json.dumps({"chart": {"error": None, "result": [{
                "timestamp": [1790370000, 1790456400],
                "indicators": {"quote": [{"close": [100.0, 100.5]}]}
            }]}})
        return json.dumps({"chart": {"error": {"code": "Not Found"}, "result": None}})

    result = snapshot(["aapl.us", "bad.us"], fetch)
    assert result["results"][0]["close"] == 100.5
    assert result["results"][0]["symbol"] == "AAPL"
    assert result["results"][1]["status"] == "unavailable"
    assert result["kind"] == "price_observation_only"
