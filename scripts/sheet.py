# One picture with every image of an episode, numbered, so bad ones can be
# spotted in a minute instead of watching the whole video.
#
#   python scripts/sheet.py --ep ep06    -> remotion/out/<ep>_images.jpg
import argparse
import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
COLS, TW, TH = 8, 400, 225

ap = argparse.ArgumentParser()
ap.add_argument("--ep", required=True)
ep = ap.parse_args().ep
story = json.loads((ROOT / "episodes" / ep / "story.json").read_text(encoding="utf-8"))
ids = [im["id"] for im in story["images"]]
rows = (len(ids) + COLS - 1) // COLS
sheet = Image.new("RGB", (COLS * TW, rows * TH), "black")
draw = ImageDraw.Draw(sheet)
try:
    font = ImageFont.truetype("DejaVuSans-Bold.ttf", 34)
except OSError:
    font = ImageFont.load_default()
missing = []
for n, iid in enumerate(ids):
    x, y = n % COLS * TW, n // COLS * TH
    path = ROOT / "remotion" / "public" / "shots" / ep / f"{iid}.png"
    if path.exists():
        sheet.paste(Image.open(path).convert("RGB").resize((TW - 4, TH - 4)), (x + 2, y + 2))
    else:
        missing.append(iid)
        draw.rectangle([x + 2, y + 2, x + TW - 3, y + TH - 3], fill=(90, 0, 0))
    label = iid.replace("img_", "")
    draw.rectangle([x + 2, y + 2, x + 70, y + 46], fill=(0, 0, 0))
    draw.text((x + 10, y + 6), label, fill=(255, 225, 77), font=font)
out = ROOT / "remotion" / "out" / f"{ep}_images.jpg"
out.parent.mkdir(parents=True, exist_ok=True)
sheet.save(out, quality=85)
print(f"\n🖼  모아보기: cloudshell download remotion/out/{ep}_images.jpg")
if missing:
    print(f"⚠ 아직 없는 그림 {len(missing)}장 (빨간 칸): {', '.join(missing)}")
    print(f"   → 같은 명령어를 한 번 더 넣으면 빠진 것만 다시 만들어요")
