#!/usr/bin/env python3
"""
POTA Alert — web UI.

A tiny single-file HTTP server (stdlib only) that:
  - Serves pota_web.html (a single-page React UI).
  - Proxies https://api.pota.app/spot/activator at /api/spots
    (so the browser doesn't have to deal with CORS).
  - Reads/writes watchlist.txt (shared with pota_alert.py and
    pota_alert_menubar.py) via /api/watchlist.

Run:   python3 pota_web.py
Open:  http://127.0.0.1:5656/  (also opens automatically)
Stop:  Ctrl-C

The UI itself handles polling, dedup, park-change detection, QRT
removal, notifications, and per-day "seen" state (stored in the
browser's localStorage). Just leave the tab open.
"""

import http.server
import socketserver
import sys
import urllib.error
import urllib.request
import webbrowser
from pathlib import Path

PORT = 5656 
HERE = Path(__file__).resolve().parent
POTA_API = "https://api.pota.app/spot/activator"
HTML_FILE = HERE / "pota_web.html"
WATCHLIST_PATH = HERE / "watchlist.txt"
WATCHLIST_EXAMPLE = HERE / "watchlist.example.txt"

# Fallback used only if watchlist.example.txt is missing too.
DEFAULT_WATCHLIST = (
    "# POTA Alert watchlist — one callsign per line.\n"
    "# Base call (F5MQU) matches all suffixes;\n"
    "# F5MQU/P matches only that specific form.\n"
)


def _ensure_watchlist() -> None:
    """Create watchlist.txt on first run by copying the shipped example.
    Falls back to DEFAULT_WATCHLIST if the example file is also missing."""
    if WATCHLIST_PATH.exists():
        return
    if WATCHLIST_EXAMPLE.exists():
        WATCHLIST_PATH.write_text(WATCHLIST_EXAMPLE.read_text())
    else:
        WATCHLIST_PATH.write_text(DEFAULT_WATCHLIST)


class Handler(http.server.BaseHTTPRequestHandler):
    server_version = "pota-web/0.1"

    def do_GET(self) -> None:
        if self.path.startswith("/api/spots"):
            self._proxy_spots()
        elif self.path.startswith("/api/watchlist"):
            self._get_watchlist()
        elif self.path in ("/", ""):
            self._serve_html()
        else:
            self.send_error(404, "Not found")

    def do_PUT(self) -> None:
        if self.path.startswith("/api/watchlist"):
            self._put_watchlist()
        else:
            self.send_error(404, "Not found")

    # --- route handlers ---------------------------------------------------

    def _serve_html(self) -> None:
        if not HTML_FILE.exists():
            self.send_error(500, f"Missing {HTML_FILE.name}")
            return
        body = HTML_FILE.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _proxy_spots(self) -> None:
        try:
            req = urllib.request.Request(
                POTA_API, headers={"User-Agent": "pota-web/0.1"}
            )
            with urllib.request.urlopen(req, timeout=15) as resp:
                body = resp.read()
        except (urllib.error.URLError, TimeoutError) as e:
            self.send_error(502, f"Upstream error: {e}")
            return
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _get_watchlist(self) -> None:
        _ensure_watchlist()
        body = WATCHLIST_PATH.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _put_watchlist(self) -> None:
        try:
            length = int(self.headers.get("Content-Length") or 0)
            raw = self.rfile.read(length)
            text = raw.decode("utf-8", errors="replace")
            WATCHLIST_PATH.write_text(text)
        except (OSError, ValueError) as e:
            self.send_error(500, f"Write failed: {e}")
            return
        self.send_response(204)
        self.end_headers()

    def log_message(self, fmt: str, *args) -> None:
        print(f"[{self.log_date_time_string()}] {fmt % args}", flush=True)


def main() -> None:
    if not HTML_FILE.exists():
        print(
            f"Error: {HTML_FILE.name} is missing from {HERE}.",
            file=sys.stderr,
        )
        sys.exit(1)
    with socketserver.TCPServer(("127.0.0.1", PORT), Handler) as httpd:
        url = f"http://127.0.0.1:{PORT}/"
        print(f"POTA Web UI serving at {url}")
        print("Press Ctrl-C to stop.")
        try:
            webbrowser.open(url)
        except Exception:
            pass
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nStopped.")


if __name__ == "__main__":
    main()
