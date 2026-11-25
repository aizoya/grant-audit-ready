"""POST /api/batch: token-gated batch over generated synthetic packages. Disabled unless BATCH_TOKEN is set."""
import hmac
import json
import os
import sys
from http.server import BaseHTTPRequestHandler

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from ember_ledger.adapter import LiveAdapter  # noqa: E402
from ember_ledger.batch import MAX_PACKS, run_batch  # noqa: E402


class handler(BaseHTTPRequestHandler):
    def _send(self, status, body):
        data = json.dumps(body).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_POST(self):
        expected = os.environ.get("BATCH_TOKEN", "")
        given = self.headers.get("x-batch-token", "")
        if not expected or not hmac.compare_digest(expected.encode(), given.encode()):
            return self._send(404, {"ok": False})
        if os.environ.get("LIVE_DISABLED"):
            return self._send(503, {"ok": False, "error": "disabled"})
        try:
            p = json.loads(self.rfile.read(int(self.headers.get("Content-Length", "0"))) or b"{}")
            n, seed = min(int(p.get("n", 14)), MAX_PACKS), int(p.get("seed", 1000))
        except Exception:
            return self._send(400, {"ok": False, "error": "bad_request"})
        try:
            out = run_batch(n, seed, lambda led: LiveAdapter(led))
        except RuntimeError:
            return self._send(503, {"ok": False, "error": "live_unavailable"})
        self._send(200, {"ok": True, "model": "muse-ember-1.0", **out})

    def log_message(self, *a):
        pass
