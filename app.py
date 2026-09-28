"""Minimal ASGI entry point for ORION's deployment status page.

The research agents are not started by web requests.
"""
from pathlib import Path

PAGE = (Path(__file__).parent / "public" / "index.html").read_bytes()

async def app(scope, receive, send):
    if scope["type"] != "http":
        return
    path = scope.get("path", "/")
    if path == "/":
        status, body, content_type = 200, PAGE, b"text/html; charset=utf-8"
    elif path == "/health":
        status, body, content_type = 200, b'{"web":"ready","research_engine":"not_live"}', b"application/json"
    else:
        status, body, content_type = 404, b"Not found", b"text/plain; charset=utf-8"
    await send({"type": "http.response.start", "status": status, "headers": [(b"content-type", content_type)]})
    await send({"type": "http.response.body", "body": body})
