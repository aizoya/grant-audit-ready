"""Local dev server: static public/ plus POST /api/check. Run: python3 serve.py [port]"""
import json, os, sys
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from ember_ledger.webapi import handle_check

class H(SimpleHTTPRequestHandler):
    def __init__(self, *a, **k): super().__init__(*a, directory="public", **k)
    def _send(self, st, body):
        raw = json.dumps(body).encode()
        self.send_response(st); self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(raw))); self.end_headers(); self.wfile.write(raw)
    def do_GET(self):
        if self.path.startswith("/api/check"): return self._send(200, {"ok": True, "live": bool(os.environ.get("META_MODEL_API_KEY"))})
        super().do_GET()
    def do_POST(self):
        n = int(self.headers.get("Content-Length", 0))
        if n > 4_400_000: return self._send(413, {"ok": False, "error": "too_large", "message": "Upload too large."})
        try: payload = json.loads(self.rfile.read(n) or b"{}")
        except ValueError: return self._send(400, {"ok": False, "error": "bad_request", "message": "Invalid JSON."})
        st, body = handle_check(payload, ip=self.client_address[0]); self._send(st, body)

if __name__ == "__main__":
    ThreadingHTTPServer(("127.0.0.1", int(sys.argv[1]) if len(sys.argv) > 1 else 8000), H).serve_forever()
