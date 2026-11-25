"""Vercel Python function: POST /api/check, GET /api/check (health)."""
import json
import os
import sys
from http.server import BaseHTTPRequestHandler

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from ember_ledger.webapi import handle_check  # noqa: E402


class handler(BaseHTTPRequestHandler):
    def _send(self, status, body):
        data = json.dumps(body).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        self._send(200, {"ok": True, "live": bool(os.environ.get("META_MODEL_API_KEY") or os.environ.get("MODEL_API_KEY"))})

    def do_POST(self):
        try:
            n = int(self.headers.get("Content-Length", "0"))
            if n > 4_400_000:
                return self._send(413, {"ok": False, "error": "too_large", "message": "Upload is too large."})
            payload = json.loads(self.rfile.read(n) or b"{}")
        except Exception:
            return self._send(400, {"ok": False, "error": "bad_request", "message": "Invalid JSON."})
        ip = (self.headers.get("x-forwarded-for") or "unknown").split(",")[0].strip()
        status, body = handle_check(payload, ip=ip)
        self._send(status, body)

    def log_message(self, *a):  # no request logging (no document content in logs)
        pass
