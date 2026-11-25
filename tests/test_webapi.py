import base64, io
from reportlab.pdfgen import canvas
from ember_ledger import webapi
from ember_ledger.fakes import RegexAdapter

def pdf(lines):
    b = io.BytesIO(); c = canvas.Canvas(b); y = 800
    for l in lines:
        c.drawString(40, y, l); y -= 18
    c.showPage(); c.save(); return base64.b64encode(b.getvalue()).decode()

TEXT = ["Schedule of Expenditures of Federal Awards for the year ended June 30, 2025"] + [f"Line {i} text for padding the page" for i in range(6)]

def payload(**over):
    d = {s: pdf(TEXT) for s in webapi.SLOTS}; d.update(over); return {"docs": d}

def setup_function(_): webapi._hits.clear()

def test_bad_request():
    assert webapi.handle_check({}, env={})[0] == 400

def test_missing_slot():
    p = payload(); del p["docs"]["prior"]
    st, b = webapi.handle_check(p, env={}); assert st == 400 and "prior" in b["message"]

def test_not_pdf():
    st, b = webapi.handle_check(payload(sefa=base64.b64encode(b"hello").decode()), env={}); assert st == 400

def test_bad_base64():
    st, _ = webapi.handle_check(payload(sefa="***"), env={}); assert st == 400

def test_too_big():
    big = base64.b64encode(b"%PDF" + b"0" * (webapi.MAX_FILE_BYTES + 1)).decode()
    assert webapi.handle_check(payload(sefa=big), env={})[0] == 413

def test_no_key_503(monkeypatch):
    monkeypatch.delenv("META_MODEL_API_KEY", raising=False); monkeypatch.delenv("MODEL_API_KEY", raising=False)
    st, b = webapi.handle_check(payload(), env={}); assert st == 503 and b["error"] == "live_unavailable"

def test_rate_limit():
    for _ in range(webapi.RATE_LIMIT[0]): webapi._rate_ok("1.1.1.1")
    st, b = webapi.handle_check(payload(), env={}, ip="1.1.1.1"); assert st == 429

def test_roundtrip_with_recorded_docs():
    import json, pathlib
    run = json.loads(pathlib.Path("public/demo-runs.json").read_text())[1]  # arithmetic scenario
    p = {"docs": {k: pdf([ln for pg in v for ln in pg.splitlines()]) for k, v in run["docs"].items()}}
    st, b = webapi.handle_check(p, env={}, adapter_factory=lambda led: RegexAdapter(led))
    assert st == 200 and b["ok"] and set(b["docs"]) == set(webapi.SLOTS)
    assert "sefa_total" in [f["code"] for f in b["report"]["findings"]]
    assert b["report"]["cost_usd"] < 0.05
