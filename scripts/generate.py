# Generates character reference images and Omni video shots from story.json.
#
# Needs GOOGLE_API_KEY + GOOGLE_GENAI_USE_ENTERPRISE=true (Express Mode),
# or GOOGLE_CLOUD_PROJECT + ADC.
#
#   python scripts/generate.py refs --ep ep02              # character portraits -> refs/
#   python scripts/generate.py shots --ep ep02 --only s01  # one shot (cost check)
#   python scripts/generate.py shots --ep ep02             # all missing shots -> remotion/public/shots/ep02/
#
# Longform episodes ("format": "longform") also have:
#   python scripts/generate.py images --ep ep05            # 16:9 still images -> remotion/public/shots/ep05/
#   python scripts/generate.py voice --ep ep05             # narration (Cloud TTS) -> remotion/public/shots/ep05/tts/
#   python scripts/generate.py samples --ep ep05           # voice samples to pick narrator voices -> voice_samples/
import argparse
import base64
import hashlib
import json
import os
import sys
import time
from pathlib import Path

from google import genai
from google.genai import interactions, types

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


def in_parallel(fn, items, workers):
    """Runs fn(item) for several items at once; one failure never stops the others."""
    from concurrent.futures import ThreadPoolExecutor
    with ThreadPoolExecutor(max_workers=workers) as pool:
        for item, fut in [(i, pool.submit(fn, i)) for i in items]:
            try:
                fut.result()
            except Exception as e:  # noqa: BLE001
                print(f"❌ {item.get('id')}: {str(e)[:200]}", file=sys.stderr, flush=True)


def make_shots(client, story, only, ep):
    SHOTS = SHOTS_ROOT / ep
    SHOTS.mkdir(parents=True, exist_ok=True)
    todo = [sh for sh in story["shots"]
            if not sh.get("card") and not sh.get("reuse") and not (only and sh["id"] not in only) and not (SHOTS / f"{sh['id']}.mp4").exists()]
    in_parallel(lambda shot: make_shot(client, story, shot, SHOTS / f"{shot['id']}.mp4"), todo, 3)


def make_shot(client, story, shot, out):
    refs = [REFS / f"{r}.png" for r in shot["refs"] if (REFS / f"{r}.png").exists()]
    names = ", ".join(f"{r} = {story['characters'][r]['name']}" for r in shot["refs"])
    setting = f" Setting: {story['location']}" if story.get("location") else ""
    # Longform: build the clip on a finished still ("image": "img_47") so faces, clothes and
    # room match the pictures around it.
    scene = SHOTS_ROOT / out.parent.name / f"{shot.get('image', '')}.png"
    if shot.get("image") and scene.exists():
        refs = [scene, *refs]
        setting += (" The first reference image is the exact scene: keep the same people, clothes, room, "
                    "lighting and camera angle, and bring it to life.")
    prompt = (f"{story['style']}{setting} "
              f"Characters in the reference images: {names}. {shot['prompt']} {SHOT_RULES}")
    task = "reference_to_video" if refs else "text_to_video"
    print(f"[shot] {shot['id']} ({task}, {shot['duration']}) ...", flush=True)
    started = client.interactions.create(
        model=OMNI_MODEL,
        input=[{"type": "text", "text": prompt}, *[image_input(p) for p in refs]],
        generation_config=interactions.GenerationConfig(
            video_config=interactions.VideoConfig(task=task)),
        response_format=interactions.VideoResponseFormat(
            aspect_ratio=story.get("aspect", "9:16"), duration=shot["duration"]),
        background=True,
    )
    it = started
    while it.status not in ("completed", "failed"):
        time.sleep(10)
        it = client.interactions.get(id=started.id)
    if it.status != "completed":
        print(f"[shot] {shot['id']} failed: {it}", file=sys.stderr)
        return
    data = [c for s in it.steps if s.type == "model_output" for c in s.content]
    out.write_bytes(base64.b64decode(data[0].data))
    print(f"[shot] saved {out.name}")


def make_images(client, story, only, ep):
    out_dir = SHOTS_ROOT / ep
    out_dir.mkdir(parents=True, exist_ok=True)
    todo = [im for im in story.get("images", [])
            if not (only and im["id"] not in only) and not (out_dir / f"{im['id']}.png").exists()]
    if not todo:
        return
    print(f"[image] {len(todo)}장 만들기 (4장씩 동시에)", flush=True)
    in_parallel(lambda im: make_image(client, story, im, out_dir / f"{im['id']}.png"), todo, 4)


def make_image(client, story, im, out):
    refs = [REFS / f"{r}.png" for r in im["refs"] if (REFS / f"{r}.png").exists()]
    names = ", ".join(f"{r} = {story['characters'][r]['name']}" for r in im["refs"])
    text = im["prompt"]
    if refs:
        text = (f"Keep each person's face, hair and age exactly like the reference photos ({names}). "
                f"{text}")
    text += " The story takes place in Japan: every person in the picture is Japanese (East Asian), in a Japanese setting."
    contents = [text, *[types.Part.from_bytes(data=p.read_bytes(), mime_type="image/png") for p in refs]]
    print(f"[image] {im['id']} ...", flush=True)
    saved = False
    for attempt in range(6):  # busy / quota errors come in bursts: wait and try again
        size = "2K" if attempt < 5 else None  # last try: default size rather than nothing
        try:
            cfg = types.GenerateContentConfig(
                response_modalities=["IMAGE"],
                image_config=types.ImageConfig(aspect_ratio=story.get("aspect", "16:9"), **({"image_size": size} if size else {})))
            resp = client.models.generate_content(model=IMAGE_MODEL, contents=contents, config=cfg)
        except Exception as e:  # noqa: BLE001 - one bad image must not stop the other 63
            wait = min(120, 20 * (attempt + 1))
            print(f"[image] {im['id']} 잠시 후 다시 ({wait}초): {str(e)[:120]}", flush=True)
            time.sleep(wait)
            continue
        for part in resp.parts or []:
            if part.inline_data is not None:
                part.as_image().save(out)
                print(f"[image] saved {out.name}", flush=True)
                saved = True
                break
        if saved:
            break
        reason = resp.candidates[0].finish_reason if resp.candidates else resp.prompt_feedback
        print(f"[image] {im['id']} 그림이 안 나옴 ({reason}) → 다시", flush=True)
    if not saved:
        print(f"[image] ❌ {im['id']} 못 만듦 (나중에 같은 명령어로 다시 시도)", flush=True)


def tts(session, project, text, voice, rate, out):
    """Google Cloud Text-to-Speech -> mp3. Same text + voice + rate is never generated twice."""
    if out.exists():
        return
    body = {"input": {"text": text}, "voice": {"languageCode": "ja-JP", "name": voice},
            "audioConfig": {"audioEncoding": "MP3", "speakingRate": rate}}
    url = "https://texttospeech.googleapis.com/v1/text:synthesize"
    headers = {"x-goog-user-project": project}
    r = session.post(url, json=body, headers=headers)
    if r.status_code == 400 and "speak" in r.text.lower():  # voice without speed control
        body["audioConfig"].pop("speakingRate")
        r = session.post(url, json=body, headers=headers)
    r.raise_for_status()
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(base64.b64decode(r.json()["audioContent"]))


def tts_name(text, voice, rate):
    return hashlib.sha1(f"{voice}|{rate}|{text}".encode("utf-8")).hexdigest()[:16] + ".mp3"


class _GcloudSession:
    """Calls Google APIs with the Cloud Shell login, refreshing the token every 30 minutes.
    google.auth.default() fails in Cloud Shell ("service account info is missing 'email' field")."""

    def __init__(self):
        import requests
        self.http = requests.Session()
        self.token, self.at = None, 0.0

    def _token(self):
        # 1) Cloud Shell's metadata server hands out the signed-in user's token directly.
        try:
            r = self.http.get("http://metadata.google.internal/computeMetadata/v1/instance/service-accounts/"
                              "default/token", headers={"Metadata-Flavor": "Google"}, timeout=5)
            if r.ok and r.json().get("access_token"):
                return r.json()["access_token"]
        except Exception:  # noqa: BLE001 - fall back to gcloud
            pass
        # 2) gcloud, a few tries (it can briefly fail after a long run)
        import subprocess
        for _ in range(3):
            r = subprocess.run(["gcloud", "auth", "print-access-token"], capture_output=True, text=True)
            if r.returncode == 0 and r.stdout.strip():
                return r.stdout.strip()
            print(r.stderr.strip(), file=sys.stderr)
            time.sleep(5)
        sys.exit("❌ 로그인이 풀렸어요. `gcloud auth login` 을 붙여넣어 로그인한 뒤, 같은 명령어를 다시 실행하세요.")

    def post(self, url, json, headers):
        if time.time() - self.at > 1800:
            self.token = self._token()
            self.at = time.time()
        for attempt in range(4):  # a stuck or dropped request is retried instead of hanging the run
            try:
                r = self.http.post(url, json=json, headers={**headers, "Authorization": f"Bearer {self.token}"},
                                   timeout=(10, 40))
                if r.status_code not in (429, 500, 502, 503, 504):
                    return r
            except Exception as e:  # noqa: BLE001
                if attempt == 3:
                    raise
                print(f"[voice] 다시 시도 ({e.__class__.__name__})", flush=True)
            time.sleep(5 * (attempt + 1))
        return r


def tts_session():
    return _GcloudSession(), os.environ["GOOGLE_CLOUD_PROJECT"]


def make_voice(story, only, ep):
    session, project = tts_session()
    v = story["voice"]
    for sc in story["scenes"]:
        if "ja" not in sc or sc["type"] in ("title", "card", "end") or (only and sc["id"] not in only):
            continue
        voice = v["letter"] if sc["type"] == "letter" else v["narrator"]
        out = SHOTS_ROOT / ep / "tts" / tts_name(sc["ja"], voice, v["speaking_rate"])
        if not out.exists():
            print(f"[voice] {sc['id']} ...", flush=True)
        tts(session, project, sc["ja"], voice, v["speaking_rate"], out)


SAMPLE_VOICES = ["Gacrux", "Kore", "Sulafat", "Vindemiatrix", "Achernar", "Aoede"]


def make_samples(story):
    session, project = tts_session()
    first = next(sc["ja"] for sc in story["scenes"] if sc["type"] == "narration")
    for name in SAMPLE_VOICES:
        out = ROOT / "voice_samples" / f"{name}.mp3"
        tts(session, project, first, f"ja-JP-Chirp3-HD-{name}", story["voice"]["speaking_rate"], out)
        print(f"[sample] {out.name}")


def needed_upto(story, upto):
    """Image, clip and scene ids used by the longform chapters up to `upto`."""
    order = [sc["chapter"] for sc in story["scenes"]]
    last = max(i for i, ch in enumerate(order) if ch == upto)
    ids = set()
    for sc in story["scenes"][: last + 1]:
        ids.add(sc["id"])
        ids.update([sc["image"]] if "image" in sc else [])
        ids.update(sc.get("clips", []))
    return ids


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("what", choices=["refs", "shots", "images", "voice", "samples"])
    ap.add_argument("--ep", required=True)
    ap.add_argument("--only", nargs="*", default=[])
    ap.add_argument("--upto", help="longform preview: only what chapters up to this one need (e.g. ch1)")
    a = ap.parse_args()
    story = load_story(a.ep)
    if a.upto and not a.only:
        a.only = needed_upto(story, a.upto)
    if a.what == "voice":
        return make_voice(story, set(a.only), a.ep)
    if a.what == "samples":
        return make_samples(story)
    client = genai.Client()
    if a.what == "refs":
        make_refs(client, story, set(a.only))
    elif a.what == "images":
        make_images(client, story, set(a.only), a.ep)
    else:
        make_shots(client, story, set(a.only), a.ep)


if __name__ == "__main__":
    main()
