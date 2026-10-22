"""contact_sheet.py -- thumbnail grid of rendered pages, for quick layout review."""
import pathlib
import sys

from PIL import Image, ImageDraw, ImageFont

src = pathlib.Path(sys.argv[1])
out = sys.argv[2]
pages = sorted(src.glob("page-*.png"))
if not pages:
    raise SystemExit("no pages found")

FONTS = pathlib.Path(r"C:\Windows\Fonts")
label_font = ImageFont.truetype(str(FONTS / "segoeuib.ttf"), 20)

COLS = 3 if len(pages) <= 9 else 5
THUMB_W = 700
LABEL_H = 30

images = [Image.open(p) for p in pages]
ratio = THUMB_W / images[0].width
thumb_h = int(images[0].height * ratio)
rows = (len(images) + COLS - 1) // COLS
W = COLS * THUMB_W + (COLS + 1) * 6
H = rows * (thumb_h + LABEL_H) + (rows + 1) * 6

canvas = Image.new("RGB", (W, H), (215, 219, 226))
d = ImageDraw.Draw(canvas)
for i, (path, img) in enumerate(zip(pages, images)):
    col, row = i % COLS, i // COLS
    x = 6 + col * (THUMB_W + 6)
    y = 6 + row * (thumb_h + LABEL_H + 6)
    number = int(path.stem.split("-")[1])
    d.rectangle((x, y, x + THUMB_W, y + LABEL_H - 4), fill=(40, 40, 40))
    d.text((x + 8, y + 4), f"page {number}", font=label_font, fill="white")
    canvas.paste(img.resize((THUMB_W, thumb_h), Image.LANCZOS), (x, y + LABEL_H))
canvas.save(out)
print("wrote", out, canvas.size)
