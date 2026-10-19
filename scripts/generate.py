# Generates character reference images and Omni video shots from story.json.
#
# Needs GOOGLE_API_KEY + GOOGLE_GENAI_USE_ENTERPRISE=true (Express Mode),
# or GOOGLE_CLOUD_PROJECT + ADC.
#
#   python scripts/generate.py refs --ep ep02              # character portraits -> refs/
#   python scripts/generate.py shots --ep ep02 --only s01  # one shot (cost check)
#   python scripts/generate.py shots --ep ep02             # all missing shots -> remotion/public/shots/ep02/
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
SHOTS_ROOT = ROOT / "remotion" / "public" / "shots"
IMAGE_MODEL = "gemini-3-pro-image"
OMNI_MODEL = "gemini-omni-1.1-flash-preview"


# Appended to every shot so stray labels or invented lines never sneak in.
SHOT_RULES = (
    "Strict rules: absolutely no on-screen text of any kind (no name labels, no character "
    "name tags, no lower-third titles, no captions, no subtitles, no watermarks, no logos, "
    "no readable writing on phones, papers or signs). Only the characters or narrator described in this shot "
    "speak, and they say only the exact Japanese lines quoted here; if no line is quoted, "
    "nobody speaks. No background voices saying words, no background music, only ambient sound."
)


def load_story(ep):
    return json.loads((ROOT / "episodes" / ep / "story.json").read_text(encoding="utf-8"))


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


def make_shots(client, story, only, ep):
    SHOTS = SHOTS_ROOT / ep
    SHOTS.mkdir(parents=True, exist_ok=True)
    for shot in story["shots"]:
        out = SHOTS / f"{shot['id']}.mp4"
        if (only and shot["id"] not in only) or out.exists():
            continue
        refs = [REFS / f"{r}.png" for r in shot["refs"] if (REFS / f"{r}.png").exists()]
        names = ", ".join(f"{r} = {story['characters'][r]['name']}" for r in shot["refs"])
        prompt = (f"{story['style']} Setting: {story['location']} "
                  f"Characters in the reference images: {names}. {shot['prompt']} {SHOT_RULES}")
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
    ap.add_argument("--ep", required=True)
    ap.add_argument("--only", nargs="*", default=[])
    a = ap.parse_args()
    client = genai.Client()
    story = load_story(a.ep)
    if a.what == "refs":
        make_refs(client, story, set(a.only))
    else:
        make_shots(client, story, set(a.only), a.ep)


if __name__ == "__main__":
    main()
