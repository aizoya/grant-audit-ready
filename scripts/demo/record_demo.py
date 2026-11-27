"""Records the 3-minute judging demo (silent screen capture + captions) from the local public/ folder.
Samples shown are real recorded Muse Ember runs on synthetic packages (public/demo-runs.json). No real filings, no keys.
Usage: python3 scripts/demo/record_demo.py OUTDIR [durations.json]   (durations.json: {"s1": seconds, ...} from the voice clips)"""
import asyncio, json, pathlib, re, sys, threading, http.server, functools, time
from playwright.async_api import async_playwright

ROOT = pathlib.Path(__file__).resolve().parents[2]
NARR = json.loads((ROOT / "docs" / "DEMO_NARRATION.json").read_text())["segments"]
out = pathlib.Path(sys.argv[1]); out.mkdir(parents=True, exist_ok=True)
dur = {s["id"]: s["sec"] for s in NARR}
if len(sys.argv) > 2:
    dur.update(json.loads(pathlib.Path(sys.argv[2]).read_text()))

CAP_JS = """
(()=>{if(window.__capInit)return;window.__capInit=true;
const mk=()=>{const b=document.createElement('div');b.id='__cap';b.style.cssText='position:fixed;left:0;right:0;bottom:0;z-index:99999;padding:18px 48px 22px;background:rgba(18,16,12,.88);color:#fff;font:600 28px/1.35 Georgia,serif;text-align:center;min-height:84px';document.documentElement.appendChild(b);
const g=document.createElement('div');g.id='__badge';g.textContent='Built during the Muse Ember Hackathon \\u00b7 synthetic documents only \\u00b7 recorded Muse Ember runs';g.style.cssText='position:fixed;bottom:104px;right:14px;z-index:99999;background:rgba(18,16,12,.82);color:#f3e9d2;font:600 15px/1 system-ui,sans-serif;padding:8px 12px;border-radius:8px';document.documentElement.appendChild(g)};
if(document.body)mk();else document.addEventListener('DOMContentLoaded',mk);
window.__cap=t=>{const b=document.getElementById('__cap');if(b)b.textContent=t}})();
"""

def serve():
    h = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(ROOT / "public"))
    h.log_message = lambda *a, **k: None
    s = http.server.ThreadingHTTPServer(("127.0.0.1", 8765), h)
    threading.Thread(target=s.serve_forever, daemon=True).start()
    return s

def sentences(t):
    return [x.strip() for x in re.split(r"(?<=[.:])\s+", t) if x.strip()]

async def captions(pg, seg, t0):
    """Show each sentence for a time proportional to its length across the segment duration."""
    ss = sentences(seg["text"]); total = sum(len(x) for x in ss); d = dur[seg["id"]]
    for x in ss:
        await pg.evaluate("t=>window.__cap&&window.__cap(t)", x)
        await asyncio.sleep(d * len(x) / total)

async def main():
    srv = serve()
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path="/usr/bin/google-chrome", args=["--no-sandbox"])
        c = await b.new_context(viewport={"width": 1920, "height": 1080}, record_video_dir=str(out), record_video_size={"width": 1920, "height": 1080})
        await c.add_init_script(CAP_JS)
        pg = await c.new_page()
        t0 = time.monotonic(); timeline = {}
        base = "http://127.0.0.1:8765/"
        seg = {s["id"]: s for s in NARR}
        async def scene(sid, acts):
            timeline[sid] = round(time.monotonic() - t0, 3)
            t = asyncio.create_task(captions(pg, seg[sid], 0))
            await acts()
            await t
        # s1: front page hero
        await pg.goto(base + "index.html"); await pg.wait_for_timeout(500)
        async def a1(): await asyncio.sleep(0.1)
        await scene("s1", a1)
        # s2: app page, pick the arithmetic sample
        await pg.goto(base + "app.html"); await pg.wait_for_timeout(600)
        async def a2():
            await pg.evaluate("document.getElementById('try').scrollIntoView({behavior:'smooth'})"); await asyncio.sleep(dur["s2"] * 0.45)
            await pg.click('.scn[data-id="arithmetic"]'); await asyncio.sleep(dur["s2"] * 0.4)
        await scene("s2", a2)
        # s3: click the finding, quote highlights in the source page
        async def a3():
            await asyncio.sleep(dur["s3"] * 0.25)
            await pg.click(".finding"); await asyncio.sleep(dur["s3"] * 0.7)
        await scene("s3", a3)
        # s4: cost meter, then the clean package
        async def a4():
            await pg.evaluate("document.getElementById('meter').scrollIntoView({block:'center',behavior:'smooth'})"); await asyncio.sleep(dur["s4"] * 0.45)
            await pg.click('.scn[data-id="clean"]'); await asyncio.sleep(dur["s4"] * 0.4)
        await scene("s4", a4)
        # s5: scanned mode: upload section text (live runs only), no fabricated scanned result
        async def a5():
            await pg.evaluate("document.getElementById('upload').scrollIntoView({behavior:'smooth'})"); await asyncio.sleep(dur["s5"] * 0.9)
        await scene("s5", a5)
        # s6: at scale, then measured results
        async def a6():
            await pg.evaluate("document.getElementById('scale').scrollIntoView({behavior:'smooth'})"); await asyncio.sleep(dur["s6"] * 0.5)
            await pg.evaluate("document.getElementById('proof').scrollIntoView({behavior:'smooth'})"); await asyncio.sleep(dur["s6"] * 0.45)
        await scene("s6", a6)
        # s7: wordmark and URL
        await pg.goto(base + "index.html"); await pg.wait_for_timeout(300)
        async def a7(): await asyncio.sleep(0.1)
        await scene("s7", a7)
        timeline["end"] = round(time.monotonic() - t0, 3)
        (out / "timeline.json").write_text(json.dumps(timeline))
        await pg.screenshot(path=str(out / "poster.png"))
        await c.close(); await b.close()
    srv.shutdown()
asyncio.run(main())
