# Generates character reference images and Omni video shots from story.json.
#
# Needs GOOGLE_API_KEY + GOOGLE_GENAI_USE_ENTERPRISE=true (Express Mode),
# or GOOGLE_CLOUD_PROJECT + ADC.
#
#   python scripts/generate.py refs              # character portraits -> refs/
#   python scripts/generate.py shots --only s01  # one shot (cost check)
#   python scripts/generate.py shots             # all missing shots -> remotion/public/shots/
import argparse
import base64
import json
import sys
import time
from pathlib import Path

from google import genai
from google.genai import interactions

ROOT = Path(__file__).resolve().parent.parent
REFS = ROOT / "refs"
SHOTS = ROOT / "remotion" / "public" / "shots"
IMAGE_MODEL = "gemini-3-pro-image"
OMNI_MODEL = "gemini-omni-1.1-flash-preview"


def load_story():
    return json.loads((ROOT / "story.json").read_text(encoding="utf-8"))


def make_refs(client, story, only):
    REFS.mkdir(exist_ok=True)
    for cid, ch in story["characters"].items():
        out = REFS / f"{cid}.png"
        if (only and cid not in only) or out.exists():
            continue
        print(f"[ref] {cid} ...", flush=True)
        resp = client.models.generate_content(model=IMAGE_MODEL, contents=ch["image_prompt"])
        for part in resp.parts:
            if part.inline_data is not None:
                part.as_image().save(out)
                print(f"[ref] saved {out.name}")
                break
        else:
            print(f"[ref] no image returned for {cid}", file=sys.stderr)


def image_input(path):
    return {"type": "image", "mime_type": "image/png",
            "data": base64.b64encode(path.read_bytes()).decode("utf-8")}


def make_shots(client, story, only):
    SHOTS.mkdir(parents=True, exist_ok=True)
    for shot in story["shots"]:
        out = SHOTS / f"{shot['id']}.mp4"
        if (only and shot["id"] not in only) or out.exists():
            continue
        refs = [REFS / f"{r}.png" for r in shot["refs"] if (REFS / f"{r}.png").exists()]
        names = ", ".join(f"{r} = {story['characters'][r]['name']}" for r in shot["refs"])
        prompt = (f"{story['style']} Setting: {story['location']} "
                  f"Characters in the reference images: {names}. {shot['prompt']}")
        task = "reference_to_video" if refs else "text_to_video"
        print(f"[shot] {shot['id']} ({task}, {shot['duration']}) ...", flush=True)
        started = client.interactions.create(
            model=OMNI_MODEL,
            input=[{"type": "text", "text": prompt}, *[image_input(p) for p in refs]],
            generation_config=interactions.GenerationConfig(
                video_config=interactions.VideoConfig(task=task)),
            response_format=interactions.VideoResponseFormat(
                aspect_ratio="9:16", duration=shot["duration"]),
            background=True,
        )
        it = started
        while it.status not in ("completed", "failed"):
            time.sleep(10)
            it = client.interactions.get(id=started.id)
        if it.status != "completed":
            print(f"[shot] {shot['id']} failed: {it}", file=sys.stderr)
            continue
        data = [c for s in it.steps if s.type == "model_output" for c in s.content]
        out.write_bytes(base64.b64decode(data[0].data))
        print(f"[shot] saved {out.name}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("what", choices=["refs", "shots"])
    ap.add_argument("--only", nargs="*", default=[])
    a = ap.parse_args()
    client = genai.Client()
    story = load_story()
    (make_refs if a.what == "refs" else make_shots)(client, story, set(a.only))


if __name__ == "__main__":
    main()
