# Writes the Thumbnail props (images + two text lines) from story.json "thumbnail".
#
#   python scripts/thumbnail.py --ep ep05   -> remotion/out/<ep>_thumb_props.json
import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

ap = argparse.ArgumentParser()
ap.add_argument("--ep", required=True)
ep = ap.parse_args().ep
story = json.loads((ROOT / "episodes" / ep / "story.json").read_text(encoding="utf-8"))
t = story["thumbnail"]


def src(iid):
    ok = (ROOT / "remotion" / "public" / "shots" / ep / f"{iid}.png").exists()
    if not ok:
        print(f"⚠ 썸네일 그림 {iid}.png 이 없어요", file=sys.stderr)
    return f"shots/{ep}/{iid}.png" if ok else None


out = ROOT / "remotion" / "out" / f"{ep}_thumb_props.json"
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps({"left": src(t["left"]), "right": src(t["right"]), "lines": t["lines"],
                           "brand": story.get("brand", "hitano")},
                          ensure_ascii=False), encoding="utf-8")
# shorts (9:16) get the vertical cover
print("ThumbnailVertical" if story.get("aspect") == "9:16" else "Thumbnail")
