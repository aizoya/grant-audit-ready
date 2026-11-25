"""Make image-only (scanned-looking) PDFs from synthetic text pages. Slight skew and noise, no text layer.
Usage: python3 scripts/make_scanned_fixture.py OUTDIR   (synthetic data only)"""
import io, random, sys, pathlib
from PIL import Image, ImageDraw, ImageFont, ImageFilter

FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"


def page_image(text: str, seed: int = 0) -> Image.Image:
    rnd = random.Random(seed)
    img = Image.new("L", (1275, 1650), 255)  # letter at 150 dpi
    d = ImageDraw.Draw(img)
    f = ImageFont.truetype(FONT, 26)
    y = 140
    import textwrap
    for raw in text.split("\n"):
        for line in textwrap.wrap(raw, 60) or [""]:
            d.text((120, y), line, font=f, fill=20)
            y += 42
    img = img.rotate(rnd.uniform(-0.6, 0.6), expand=False, fillcolor=255)
    noise = Image.effect_noise(img.size, 12).point(lambda v: 0 if v > 140 else 255)
    img = Image.composite(img, Image.new("L", img.size, 235), noise.convert("L").point(lambda v: 255 if v > 0 else 200))
    return img.filter(ImageFilter.GaussianBlur(0.5))


def scanned_pdf(pages: list[str], seed: int = 0) -> bytes:
    imgs = [page_image(p, seed + i).convert("RGB") for i, p in enumerate(pages)]
    b = io.BytesIO()
    imgs[0].save(b, format="PDF", save_all=True, append_images=imgs[1:], resolution=150)
    return b.getvalue()


if __name__ == "__main__":
    sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
    from ember_ledger.synth import make_docs
    out = pathlib.Path(sys.argv[1]); out.mkdir(parents=True, exist_ok=True)
    docs = make_docs(sefa_total_stated=1_250_000, fs_revenue=1_100_000, prior_finding=True)
    for k, pages in docs.items():
        (out / f"{k}.pdf").write_bytes(scanned_pdf(pages))
        print(k, (out / f"{k}.pdf").stat().st_size, "bytes")
