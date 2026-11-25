import asyncio,sys,json,pathlib
from playwright.async_api import async_playwright
out=pathlib.Path(sys.argv[1]);out.mkdir(exist_ok=True)
async def main():
  async with async_playwright() as p:
    b=await p.chromium.launch(executable_path="/usr/bin/google-chrome",args=["--no-sandbox"])
    c=await b.new_context(viewport={"width":1280,"height":720},record_video_dir=str(out),record_video_size={"width":1280,"height":720})
    pg=await c.new_page();await pg.goto("file://"+str(pathlib.Path("film.html").resolve()))
    await pg.evaluate("start()");await pg.wait_for_function("window.done===true",timeout=70000)
    await pg.screenshot(path=str(out/"poster.png"));
    await pg.evaluate("document.getElementById('cap').textContent=''")
    await c.close();await b.close()
asyncio.run(main())
