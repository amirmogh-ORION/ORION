"""ORION web interface: explicit on-demand scaffold reports, no market feeds."""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT / "src"))
PAGE = (ROOT / "public" / "index.html").read_bytes()

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
        return await respond(send, 200, b'{"web":"ready","research_engine":"stub_only"}', b"application/json")
    if path == "/api/cycle" and method == "POST":
        body = b""
        while True:
            event = await receive()
            body += event.get("body", b"")
            if len(body) > 2048:
                return await respond(send, 413, b'{"error":"Request too large"}', b"application/json")
            if not event.get("more_body", False):
                break
        try:
            subject = json.loads(body).get("subject", "").strip().upper()
            if not re.fullmatch(r"[A-Z0-9.\-]{1,15}", subject):
                raise ValueError()
        except (ValueError, TypeError, AttributeError):
            return await respond(send, 400, b'{"error":"Enter a ticker or symbol (1-15 letters, numbers, dots or hyphens)."}', b"application/json")
        from orion.agents import Commander, StubAgent
        from orion.runtime import run_cycle
        roles = [("opportunity_scout", "Opportunity scan"), ("fundamental_analyst", "Fundamental"),
                 ("quant_analyst", "Quantitative"), ("macro_analyst", "Macro/regime"),
                 ("risk_manager", "Risk"), ("learning_agent", "Learning")]
        result = run_cycle(Commander([StubAgent(name, role) for name, role in roles]), [subject])
        payload = {"cycle_id": result.cycle_id, "subject": subject, "mode": "stub_only",
                   "persisted": False, "reports": [report.model_dump(mode="json") for report in result.reports]}
        return await respond(send, 200, json.dumps(payload).encode(), b"application/json")
    return await respond(send, 404, b"Not found", b"text/plain; charset=utf-8")
