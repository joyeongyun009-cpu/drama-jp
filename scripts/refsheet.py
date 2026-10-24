# One small picture with this episode's character portraits (refs/<id>.png), named,
# so Claude can check faces without the big refs.zip.
#
#   python scripts/refsheet.py --ep ep07   -> remotion/out/<ep>_refs.jpg
import argparse
import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent

ap = argparse.ArgumentParser()
ap.add_argument("--ep", required=True)
ep = ap.parse_args().ep
story = json.loads((ROOT / "episodes" / ep / "story.json").read_text(encoding="utf-8"))
ids = list(story.get("characters", {}))
COLS, TW, TH = 4, 480, 480
sheet = Image.new("RGB", (COLS * TW, max(1, (len(ids) + COLS - 1) // COLS) * TH), "black")
draw = ImageDraw.Draw(sheet)
try:
    font = ImageFont.truetype("DejaVuSans-Bold.ttf", 30)
except OSError:
    font = ImageFont.load_default()
for n, cid in enumerate(ids):
    x, y = n % COLS * TW, n // COLS * TH
    path = ROOT / "refs" / f"{cid}.png"
    if path.exists():
        im = Image.open(path).convert("RGB")
        im.thumbnail((TW - 6, TH - 6))
        sheet.paste(im, (x + (TW - im.width) // 2, y + (TH - im.height) // 2))
    else:
        draw.rectangle([x + 3, y + 3, x + TW - 4, y + TH - 4], fill=(90, 0, 0))
    draw.rectangle([x + 3, y + 3, x + 16 * len(cid) + 24, y + 42], fill=(0, 0, 0))
    draw.text((x + 10, y + 6), cid, fill=(255, 225, 77), font=font)
out = ROOT / "remotion" / "out" / f"{ep}_refs.jpg"
out.parent.mkdir(parents=True, exist_ok=True)
sheet.save(out, quality=85)
print(f"🧑 인물 사진 모아보기: cloudshell download remotion/out/{ep}_refs.jpg")
