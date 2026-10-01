"""Read-only console for persisted scheduled mission evidence."""
import json
import re
import sys
import asyncio
from datetime import datetime, timezone
from urllib.request import Request, urlopen
from pathlib import Path

ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT / "src"))
PAGE = (ROOT / "public" / "index.html").read_bytes()

def latest_mission():
    url = "https://raw.githubusercontent.com/amirmogh-ORION/ORION/orion-state/reports/mission.json"
    with urlopen(Request(url, headers={"User-Agent": "Mozilla/5.0"}), timeout=15) as response:
        report = json.load(response)
    report.pop("observations", None)
    report.pop("procurement", None)
    completed = datetime.fromisoformat(report["completed_at"])
    report["stale"] = (datetime.now(timezone.utc)-completed).total_seconds() > 8*3600
    report["source_url"] = url
    return report

async def respond(send, status, body, content_type):
    await send({"type": "http.response.start", "status": status,
                "headers": [(b"content-type", content_type), (b"cache-control", b"no-store")]})
    await send({"type": "http.response.body", "body": body})

async def app(scope, receive, send):
    if scope["type"] != "http":
        return
    path, method = scope.get("path", "/"), scope.get("method", "GET")
    if path == "/" and method == "GET":
        return await respond(send, 200, PAGE, b"text/html; charset=utf-8")
    if path == "/health" and method == "GET":
        return await respond(send, 200, b'{"web":"ready","research_engine":"scheduled_external_workers"}', b"application/json")
    if path == "/api/mission" and method == "GET":
        try:
            payload = await asyncio.to_thread(latest_mission)
            return await respond(send, 200, json.dumps(payload).encode(), b"application/json")
        except (OSError, ValueError, KeyError, TypeError):
            return await respond(send, 503, b'{"error":"Persisted mission evidence unavailable; check mission workflow."}', b"application/json")
    if path == "/api/cycle" and method == "POST":
        return await respond(send, 410, b'{"error":"Placeholder cycles retired. Use /api/mission for actual work."}', b"application/json")
    return await respond(send, 404, b"Not found", b"text/plain; charset=utf-8")
