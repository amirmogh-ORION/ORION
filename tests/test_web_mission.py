import asyncio
import importlib.util
from pathlib import Path

spec = importlib.util.spec_from_file_location("orion_web", Path(__file__).parents[1]/"app.py")
web = importlib.util.module_from_spec(spec)
spec.loader.exec_module(web)


def request(path, method="GET"):
    sent = []
    async def send(event):
        sent.append(event)
    async def receive():
        return {"type": "http.request", "body": b""}
    asyncio.run(web.app({"type": "http", "path": path, "method": method}, receive, send))
    return sent


def test_console_uses_actual_mission_and_retires_stub_cycle():
    assert request("/api/cycle", "POST")[0]["status"] == 410
    page = request("/")[1]["body"]
    assert b"/api/mission" in page and b"Prototype:" not in page


def test_missing_evidence_fails_explicitly(monkeypatch):
    def failed():
        raise OSError("offline")
    monkeypatch.setattr(web, "latest_mission", failed)
    result = request("/api/mission")
    assert result[0]["status"] == 503
    assert b"unavailable" in result[1]["body"]


def test_persisted_cycle_is_served_without_stub_generation(monkeypatch):
    monkeypatch.setattr(web, "latest_mission", lambda: {"cycle_id": "verified", "stale": False})
    result = request("/api/mission")
    assert result[0]["status"] == 200 and b"verified" in result[1]["body"]
