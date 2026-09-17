"""Loopback web UI. Run with `uv run --env-file .env python app.py`."""

import json
import secrets
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from review import Review

TOKEN = secrets.token_urlsafe(32)
PORT = 4328
ORIGIN = f"http://127.0.0.1:{PORT}"
LOCK = threading.Lock()
ACTIVE = None
WORKER = None


class Handler(BaseHTTPRequestHandler):
    def send(self, status, payload, content_type="application/json"):
        content = payload.encode() if isinstance(payload, str) else json.dumps(payload).encode()
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(content)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header(
            "Content-Security-Policy",
            "default-src 'self'; script-src 'unsafe-inline'; style-src 'unsafe-inline'; frame-ancestors 'none'",
        )
        self.end_headers()
        self.wfile.write(content)

    def do_GET(self):
        if self.headers.get("Host") != f"127.0.0.1:{PORT}":
            return self.send(403, {"error": "Open the app at " + ORIGIN})
        if self.path == "/":
            html = Path(__file__).with_name("index.html").read_text().replace("__TOKEN__", TOKEN)
            return self.send(200, html, "text/html; charset=utf-8")
        if self.path in {"/api/state", "/api/report"}:
            with LOCK:
                state = ACTIVE.snapshot() if ACTIVE else {"status": "idle"}
                state["busy"] = bool(WORKER and WORKER.is_alive())
            if self.path == "/api/state":
                state.pop("packet", None)
                state.pop("rubric", None)
            return self.send(200, state)
        self.send(404, {"error": "Not found"})

    def do_POST(self):
        global ACTIVE, WORKER
        if (
            self.headers.get("Host") != f"127.0.0.1:{PORT}"
            or self.headers.get("Origin") != ORIGIN
            or self.headers.get("X-Review-Token") != TOKEN
        ):
            return self.send(403, {"error": "Local UI requests only."})
        try:
            length = int(self.headers.get("Content-Length", "0"))
            if not 0 < length < 4096:
                raise ValueError("Invalid request size.")
            body = json.loads(self.rfile.read(length))
            with LOCK:
                if self.path == "/api/cancel":
                    if ACTIVE:
                        ACTIVE.cancelled.set()
                    return self.send(
                        200, {"message": "Cancellation requested; current call will finish before cleanup."}
                    )
                if self.path != "/api/run":
                    return self.send(404, {"error": "Not found"})
                if WORKER and WORKER.is_alive():
                    return self.send(409, {"error": "A review is already running."})
                if not isinstance(body, dict) or not isinstance(body.get("url"), str):
                    raise TypeError("Enter a PR URL.")
                ACTIVE = Review(body["url"].strip(), body.get("provider", "local"))
                WORKER = threading.Thread(target=ACTIVE.run, name="review-worker")
                WORKER.start()
                return self.send(202, {"id": ACTIVE.state["id"]})
        except (ValueError, TypeError) as error:
            self.send(400, {"error": str(error)})

    def log_message(self, *_):
        pass


if __name__ == "__main__":
    server = ThreadingHTTPServer(("127.0.0.1", PORT), Handler)
    print(f"Review Lab: {ORIGIN}", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        if ACTIVE:
            ACTIVE.cancelled.set()
        print("Stopping after the current operation and removing sandboxes…", flush=True)
    finally:
        server.server_close()
        if WORKER:
            WORKER.join()
