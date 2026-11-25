"""Make scanned PDFs at three degradation levels plus the ground-truth text, to measure how well the model reads
scanned pages. Usage: python3 scripts/make_noise_levels.py OUTDIR   (synthetic data only)"""
import io, json, pathlib, random, sys, textwrap
from PIL import Image, ImageDraw, ImageFont, ImageFilter

FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
LEVELS = {  # skew degrees, noise strength (lower = noisier), blur, scale, jpeg quality
    "light": dict(skew=0.6, noise=12, blur=0.5, scale=1.0, q=85),
    "medium": dict(skew=1.8, noise=45, blur=1.0, scale=0.6, q=45),
    "hard": dict(skew=3.0, noise=80, blur=1.5, scale=0.42, q=25),
}


def page_image(text, seed, p):
    rnd = random.Random(seed)
    img = Image.new("L", (1275, 1650), 255)
    d = ImageDraw.Draw(img)
    f = ImageFont.truetype(FONT, 26)
    y = 140
    for raw in text.split("\n"):
        for line in textwrap.wrap(raw, 60) or [""]:
            d.text((120, y), line, font=f, fill=20)
            y += 42
    img = img.rotate(rnd.uniform(-p["skew"], p["skew"]), fillcolor=255)
    noise = Image.effect_noise(img.size, p["noise"]).point(lambda v: 0 if v > 140 else 255)
    img = Image.composite(img, Image.new("L", img.size, 225), noise.convert("L").point(lambda v: 255 if v > 0 else 150))
    img = img.filter(ImageFilter.GaussianBlur(p["blur"]))
    if p["scale"] != 1.0:
        img = img.resize((int(img.width * p["scale"]), int(img.height * p["scale"])), Image.BILINEAR)
    b = io.BytesIO(); img.convert("RGB").save(b, format="JPEG", quality=p["q"]); b.seek(0)
    return Image.open(b).convert("RGB")


def pdf(pages, seed, p):
    imgs = [page_image(t, seed + i, p) for i, t in enumerate(pages)]
    b = io.BytesIO()
    imgs[0].save(b, format="PDF", save_all=True, append_images=imgs[1:], resolution=150 * p["scale"])
    return b.getvalue()


if __name__ == "__main__":
    sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
    from ember_ledger.synth import make_docs
    out = pathlib.Path(sys.argv[1]); out.mkdir(parents=True, exist_ok=True)
    docs = make_docs(sefa_total_stated=1_250_000, fs_revenue=1_100_000, prior_finding=True)
    (out / "truth.json").write_text(json.dumps(docs))
    for name, p in LEVELS.items():
        (out / name).mkdir(exist_ok=True)
        for slot, pages in docs.items():
            data = pdf(pages, 7, p)
            (out / name / f"{slot}.pdf").write_bytes(data)
            print(name, slot, len(data))
