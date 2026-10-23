# Writes remotion/out/epNN_heard.txt: for every talking clip, the line in the
# script and what Whisper actually heard, so Claude can check the dialogue
# from the clips zip without listening.
#
#   python scripts/heard.py --ep ep06        (run_cloudshell.sh clips runs it)
import argparse
import json
from pathlib import Path

from align import WhisperModel, audio16k, duration

ROOT = Path(__file__).resolve().parent.parent


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ep", required=True)
    ep = ap.parse_args().ep
    story = json.loads((ROOT / "episodes" / ep / "story.json").read_text(encoding="utf-8"))
    shots_dir = ROOT / "remotion" / "public" / "shots" / ep
    out = ROOT / "remotion" / "out" / f"{ep}_heard.txt"
    model, rows = None, []
    for sh in story["shots"]:
        path = shots_dir / f"{sh['id']}.mp4"
        if not sh.get("lines") or not path.exists():
            continue
        model = model or WhisperModel("small", device="cpu", compute_type="int8")
        segs = [s for s in model.transcribe(audio16k(path), language="ja", vad_filter=True)[0] if s.text.strip()]
        span = f"{segs[0].start:.1f}-{segs[-1].end:.1f}s" if segs else "-"
        rows.append(f"{sh['id']} ({duration(path):.1f}s, speech {span})\n"
                    f"  script: {''.join(ja for _, ja in sh['lines'])}\n"
                    f"  heard : {''.join(s.text for s in segs) or '(no speech)'}\n")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(rows) or "(말하는 영상 없음)\n", encoding="utf-8")
    print(f"▶ 대사 확인 파일: {out.name}")


if __name__ == "__main__":
    main()
