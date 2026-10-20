# Times each shot's caption chunks to the speech in its clip and writes
# remotion/src/shots.json for the video.
#
#   python scripts/align.py --ep ep02
#
# Chunks come from story.json ("／"-separated). Where Whisper finds speech, the
# chunks are spread over the spoken span in proportion to their length; shots
# without speech (narration captions) spread them over the whole clip.
import argparse
import json
import subprocess
from pathlib import Path

import numpy as np
from faster_whisper import WhisperModel

ROOT = Path(__file__).resolve().parent.parent
SHOTS_ROOT = ROOT / "remotion" / "public" / "shots"
OUT = ROOT / "remotion" / "src" / "shots.json"


def duration(path):
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                        "-of", "csv=p=0", str(path)], capture_output=True, text=True, check=True)
    return float(r.stdout.strip())


def audio16k(path):
    r = subprocess.run(["ffmpeg", "-v", "error", "-i", str(path), "-ac", "1", "-ar", "16000",
                        "-f", "f32le", "-"], capture_output=True, check=True)
    return np.frombuffer(r.stdout, np.float32)


def spread(chunks, start, end):
    weights = [max(2, len(c)) for c in chunks]
    total = sum(weights)
    t, out = start, []
    for c, w in zip(chunks, weights):
        d = (end - start) * w / total
        out.append({"text": c, "start": round(t, 2), "end": round(t + d, 2)})
        t += d
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ep", required=True)
    ap.add_argument("--upto", help="longform preview: last chapter to include (e.g. ch1)")
    args = ap.parse_args()
    ep = args.ep
    SHOTS = SHOTS_ROOT / ep
    story = json.loads((ROOT / "episodes" / ep / "story.json").read_text(encoding="utf-8"))
    if story.get("format") == "longform":
        import longform
        longform.build(story, ep, args.upto)
        return
    model = WhisperModel("small", device="cpu", compute_type="int8")
    result = []
    for shot in story["shots"]:
        clip = SHOTS / f"{shot['id']}.mp4"
        if not clip.exists():
            print(f"skip {shot['id']} (no clip)")
            continue
        dur = duration(clip)
        chunks = [c for c in shot["captions"].split("／") if c]
        segs, _ = model.transcribe(audio16k(clip), language="ja", vad_filter=True)
        segs = [s for s in segs if s.text.strip()]
        if shot.get("speech") is False:  # silent shot: ignore anything Whisper thinks it heard
            segs = []
        if segs:
            start, end = segs[0].start, min(dur - 0.1, segs[-1].end + 0.2)
            heard = "".join(s.text for s in segs)
        else:
            start, end = 0.4, dur - 0.4
            heard = ""
        result.append({"id": shot["id"], "file": f"shots/{ep}/{clip.name}", "duration": round(dur, 3),
                       "captions": spread(chunks, start, end), "heard": heard})
        print(f"{shot['id']} {dur:.1f}s heard: {heard or '(no speech)'}")
    ending = story["ending"]
    bgm = story.get("bgm")
    if bgm and not (ROOT / "remotion" / "public" / bgm["file"]).exists():
        print(f"⚠ BGM 파일이 없어요 (remotion/public/{bgm['file']}) → 음악 없이 만듭니다")
        bgm = None
    OUT.write_text(json.dumps({"shots": result, "ending": ending, "bgm": bgm}, ensure_ascii=False, indent=1),
                   encoding="utf-8")


if __name__ == "__main__":
    main()
