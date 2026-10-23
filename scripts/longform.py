# Builds remotion/src/longform.json (the 16:9 longform timeline) from a
# longform story.json plus the generated images, Omni clips and narration.
# Called by align.py when story.json has "format": "longform".
#
# Missing files never stop the build: a missing image becomes a placeholder
# card, a missing clip becomes a black card with its lines, and everything
# missing is listed at the end.
import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PUBLIC = ROOT / "remotion" / "public"
OUT = ROOT / "remotion" / "src" / "longform.json"
FPS = 30
CHAPTERS = ["intro", "ch1", "ch2", "ch3", "ch4", "ch5", "epilogue"]
LINE_CHARS = 22  # one caption line
CHUNK_CHARS = 2 * LINE_CHARS  # at most two lines on screen
MOTIONS = ["zoom_in_big", "pan_right", "zoom_out_big", "pan_left", "push_slow", "pan_up", "pan_down"]
MOTION_SFX = {"slide_in_left": "whoosh", "slide_in_right": "whoosh", "punch_zoom": "impact"}
CHAT_GAP = 0.7  # seconds between chat bubbles


def duration(path):
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                        "-of", "csv=p=0", str(path)], capture_output=True, text=True, check=True)
    return float(r.stdout.strip())


NO_LINE_START = set("、。！？」』）・ーぁぃぅぇぉっゃゅょゎァィゥェォッャュョヮん…")
PARTICLES = set("はがをにでともへやの")


def bars_zoom(path):
    """Omni sometimes bakes black bars into a 16:9 clip; return the zoom that hides them."""
    r = subprocess.run(["ffmpeg", "-v", "info", "-i", str(path), "-vf", "cropdetect=limit=24:round=2:reset=0",
                        "-f", "null", "-"], capture_output=True, text=True)
    crops = re.findall(r"crop=(\d+):(\d+):(\d+):(\d+)", r.stderr)
    probe = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
                            "stream=width,height", "-of", "csv=p=0", str(path)], capture_output=True, text=True)
    if not crops or "," not in probe.stdout:
        return 1.0
    w, h = map(int, probe.stdout.strip().split(",")[:2])
    cw, ch = int(crops[-1][0]), int(crops[-1][1])
    zoom = max(w / max(cw, 1), h / max(ch, 1))
    return round(min(zoom, 1.4), 3) if zoom > 1.03 else 1.0


def wrap(chunk):
    """Break a chunk into at most two lines at a natural place: after 、。 if one is near the
    middle, else after a particle, and never so that the second line starts with 」』、。 or a small kana."""
    if len(chunk) <= LINE_CHARS:
        return chunk
    mid = len(chunk) / 2
    best, best_score = (len(chunk) + 1) // 2, 1e9
    for cut in range(len(chunk) - LINE_CHARS, LINE_CHARS + 1):
        if cut <= 0 or cut >= len(chunk) or chunk[cut] in NO_LINE_START:
            continue
        prev = chunk[cut - 1]
        score = abs(cut - mid) + (0 if prev in "、。！？」』" else 3 if prev in PARTICLES else 8)
        score += 4 if chunk[cut] in PARTICLES else 0  # do not cut just before a particle
        if score < best_score:
            best, best_score = cut, score
    return chunk[:best] + "\n" + chunk[best:]


def chunks_of(text):
    """Split at 。、！？ and pack the pieces into chunks of at most two caption lines."""
    pieces = [p for p in re.split(r"(?<=[。、！？])", text) if p]
    out = []
    for p in pieces:
        while len(p) > CHUNK_CHARS:
            out.append(p[:CHUNK_CHARS])
            p = p[CHUNK_CHARS:]
        if out and len(out[-1]) + len(p) <= CHUNK_CHARS and not out[-1].endswith(("。", "！", "？")):
            out[-1] += p
        else:
            out.append(p)
    return out


def spread(texts, start, end, **extra):
    weights = [max(2, len(t)) for t in texts]
    total = sum(weights)
    t, out = start, []
    for text, w in zip(texts, weights):
        d = (end - start) * w / total
        out.append({"text": wrap(text), "start": round(t, 2), "end": round(t + d, 2), **extra})
        t += d
    return out


def read_srt(path):
    """[(start, end, text)] from a Vrew .srt file."""
    def sec(t):
        h, m, rest = t.strip().replace(",", ".").split(":")
        return int(h) * 3600 + int(m) * 60 + float(rest)
    out = []
    for block in re.split(r"\n\s*\n", path.read_text(encoding="utf-8-sig").strip()):
        rows = block.strip().splitlines()
        if len(rows) >= 3 and "-->" in rows[1]:
            a, b = rows[1].split("-->")
            out.append((sec(a), sec(b), "".join(rows[2:]).strip()))
    return out


def vrew_times(story, keep):
    """Vrew narration: each scene covers SRT lines "srt": [first, last]. Scenes start exactly where
    their first line starts, so pictures change in step with the recorded voice."""
    srt = read_srt(ROOT / story["narration"]["srt"])
    audio = duration(PUBLIC / story["narration"]["audio"])
    scenes = story["scenes"]  # whole story, so a preview stops where its last scene really ends
    starts = [0.0 if i == 0 else srt[sc["srt"][0] - 1][0] for i, sc in enumerate(scenes)]
    out = {}
    for i, sc in enumerate(scenes):
        a, b = sc["srt"]
        t0 = starts[i]
        t1 = starts[i + 1] if i + 1 < len(scenes) else max(audio, srt[b - 1][1]) + float(sc.get("duration", 0))
        lines = [{"text": wrap(x[2]), "start": round(x[0] - t0, 2), "end": round(min(x[1], t1) - t0, 2)}
                 for x in srt[a - 1:b]]
        if sc["chapter"] in keep:
            out[sc["id"]] = (round(t0 * FPS), round(t1 * FPS), lines)
    return out


def build(story, ep, upto=None):
    from generate import tts_name  # same cache names as the voice step

    shots_dir = PUBLIC / "shots" / ep
    v = story["voice"]
    speakers = story.get("speakers", {})
    images = {im["id"]: im for im in story["images"]}
    clips = {c["id"]: c for c in story["shots"]}
    keep = CHAPTERS[: CHAPTERS.index(upto) + 1] if upto else CHAPTERS
    missing, warnings = [], []
    whisper = None
    vrew = vrew_times(story, keep) if story.get("narration") else None

    def image_src(iid):
        if (shots_dir / f"{iid}.png").exists():
            try:
                from PIL import Image
                w, h = Image.open(shots_dir / f"{iid}.png").size
                if w < 1600:
                    warnings.append(f"{iid}: 해상도가 낮아요 ({w}x{h}) → 크게 확대하면 흐릴 수 있어요")
            except ImportError:
                pass
            return f"shots/{ep}/{iid}.png"
        if f"{iid}.png" not in missing:
            missing.append(f"{iid}.png")
        return None

    def clip_part(cid, trim_tight):
        nonlocal whisper
        c = clips[cid]
        path = shots_dir / f"{cid}.mp4"
        lines = c["lines"]
        texts = [(sp, ch) for sp, ja in lines for ch in chunks_of(ja)]
        if not path.exists():
            missing.append(f"{cid}.mp4")
            dur = float(c["duration"].rstrip("s"))
            caps = spread([t for _, t in texts], 0.4, dur - 0.4)
            return {"file": None, "id": cid, "from": 0, "seconds": dur,
                    "captions": [dict(x, speaker=sp, color=speakers.get(sp, "#888")) for x, (sp, _) in zip(caps, texts)],
                    "speech": [0.4, dur - 0.4]}
        dur = duration(path)
        if whisper is None:
            from align import WhisperModel
            whisper = WhisperModel("small", device="cpu", compute_type="int8")
        from align import audio16k
        segs, _ = whisper.transcribe(audio16k(path), language="ja", vad_filter=True)
        segs = [s for s in segs if s.text.strip()]
        start, end = (segs[0].start, min(dur - 0.1, segs[-1].end + 0.2)) if segs else (0.4, dur - 0.4)
        heard = "".join(s.text for s in segs)
        print(f"  {cid} {dur:.1f}s heard: {heard or '(no speech)'}")
        cut_in, cut_out = (max(0, start - 0.3), min(dur, end + 0.5)) if trim_tight else (0, dur)
        zoom = bars_zoom(path)
        if zoom > 1:
            print(f"  {cid}: 위아래/옆 검은 띠 → {zoom:.2f}배 확대해서 없앰")
        caps = spread([t for _, t in texts], start - cut_in, end - cut_in)
        return {"file": f"shots/{ep}/{cid}.mp4", "id": cid, "from": round(cut_in, 2), "zoom": zoom,
                "seconds": round(cut_out - cut_in, 2),
                "captions": [dict(x, speaker=sp, color=speakers.get(sp, "#888")) for x, (sp, _) in zip(caps, texts)],
                "speech": [round(start - cut_in, 2), round(end - cut_in, 2)]}

    def vrew_clip(cid, seconds):
        """Silent clip: the Vrew narration plays over it (slowed down if too short).
        Talking clip ("lines"): the actor's own voice plays instead of the narration, starting
        where the speech starts so it fits the slot of that caption line."""
        nonlocal whisper
        path = shots_dir / f"{cid}.mp4"
        if not path.exists():
            missing.append(f"{cid}.mp4")
            return {"file": None, "id": cid, "from": 0, "seconds": seconds, "captions": [], "speech": [0, 0]}
        dur = duration(path)
        zoom = bars_zoom(path)
        part = {"file": f"shots/{ep}/{cid}.mp4", "id": cid, "from": 0, "zoom": zoom, "seconds": seconds,
                "rate": round(min(1.0, dur / seconds), 3), "muted": True, "captions": [], "speech": [0, 0]}
        if clips[cid].get("lines"):
            if whisper is None:
                from align import WhisperModel
                whisper = WhisperModel("small", device="cpu", compute_type="int8")
            from align import audio16k
            segs, _ = whisper.transcribe(audio16k(path), language="ja", vad_filter=True)
            segs = [x for x in segs if x.text.strip()]
            start = segs[0].start if segs else 0.4
            print(f"  {cid} {dur:.1f}s heard: {''.join(x.text for x in segs) or '(no speech)'}")
            if segs and segs[-1].end - start > seconds:
                warnings.append(f"{cid}: 대사({segs[-1].end - start:.1f}초)가 자리({seconds:.1f}초)보다 길어 끝이 잘려요 → redo ep06 {cid}")
            part.update(rate=1.0, muted=False, **{"from": round(max(0.0, min(start - 0.2, dur - seconds)), 2)})
        return part

    scenes, prev_motion = [], None
    for sc in story["scenes"]:
        if sc["chapter"] not in keep:
            continue
        out = {"id": sc["id"], "type": sc["type"], "chapter": sc["chapter"],
               "transition": sc.get("transition", "cut"), "sfx": [], "captions": [], "speech": []}
        if sc.get("sfx"):
            out["sfx"].append(sc["sfx"])
        if "image" in sc:
            out["image"] = image_src(sc["image"])
            out["imageId"] = sc["image"]
            out["imagePrompt"] = images.get(sc["image"], {}).get("prompt", "")[:90]
            motion = sc.get("motion", "zoom_in_big")
            if motion == "parallax":  # no automatic cut-out in this pipeline
                motion = "zoom_in_big"
            if motion == prev_motion:
                alt = next(m for m in MOTIONS if m != prev_motion)
                warnings.append(f"{sc['id']}: 앞 장면과 같은 움직임({motion}) → {alt}로 바꿈")
                motion = alt
            prev_motion = motion
            # Only scenes the script marks as a shock (impact sound / flash cut) get the shake;
            # everywhere else the moves stay smooth (user: constant shaking looked awkward).
            strong = sc.get("sfx") == "impact" or sc.get("transition") == "flash"
            out.update(motion=motion, focus=sc.get("focus"), filter=sc.get("filter"), strong=strong)
            if MOTION_SFX.get(motion) and (motion != "punch_zoom" or strong):
                out["sfx"].append(MOTION_SFX[motion])
        else:
            prev_motion = None

        t = sc["type"]
        seconds = float(sc.get("duration", 0))
        if vrew:
            f0, f1, lines = vrew[sc["id"]]
            seconds = (f1 - f0) / FPS
            if t != "end":
                out["captions"] = lines
            out["speech"] = [[x["start"], x["end"]] for x in lines]
            if t == "line":
                out["speaker"] = sc["speaker"]
                out["color"] = speakers.get(sc["speaker"], "#888")
            elif t == "chat":
                out["group"] = sc["group"]
                out["messages"] = [{"name": n, "text": m, "at": round(0.6 + i * CHAT_GAP, 2),
                                    "color": speakers.get(n, "#888")} for i, (n, m) in enumerate(sc["messages"])]
            elif t == "clip":
                out["clips"] = [vrew_clip(cid, seconds / len(sc["clips"])) for cid in sc["clips"]]
                out["talk"] = any(clips[c].get("lines") for c in sc["clips"])  # narration off, bubble captions
                if out["talk"]:
                    out["speaker"] = clips[sc["clips"][0]]["lines"][0][0]
                    out["color"] = speakers.get(out["speaker"], "#888")
            elif t in ("title", "card", "end"):
                out["text"] = sc["ja"]
                out["disclaimer"] = sc.get("disclaimer", "")
        elif t in ("narration", "line", "chat", "letter"):
            voice = v["letter"] if t == "letter" else v["narrator"]
            mp3 = shots_dir / "tts" / tts_name(sc["ja"], voice, v["speaking_rate"])
            if mp3.exists():
                audio = duration(mp3)
                out["audio"] = f"shots/{ep}/tts/{mp3.name}"
            else:
                missing.append(f"{sc['id']} 나레이션")
                audio = max(2.0, len(sc["ja"]) / 6.5)  # about how long it will be
            seconds = max(audio + v["padding_sec"], v["min_scene_sec"])
            out["speech"] = [[0.0, round(audio, 2)]]
            if t == "letter":
                lines = [p for p in re.split(r"(?<=。)", sc["ja"]) if p]
                out["letterLines"] = spread(lines, 0.0, audio)
                seconds += 1.0
            else:
                out["captions"] = spread(chunks_of(sc["ja"]), 0.05, audio)
            if t == "line":
                out["speaker"] = sc["speaker"]
                out["color"] = speakers.get(sc["speaker"], "#888")
            if t == "chat":
                out["group"] = sc["group"]
                out["messages"] = [{"name": n, "text": m, "at": round(0.6 + i * CHAT_GAP, 2),
                                    "color": speakers.get(n, "#888")} for i, (n, m) in enumerate(sc["messages"])]
                seconds = max(seconds, 0.6 + len(sc["messages"]) * CHAT_GAP + 1.5)
        elif t == "clip":
            parts = [clip_part(cid, sc["chapter"] == "intro") for cid in sc["clips"]]
            t0 = 0.0
            for p in parts:
                out["speech"].append([round(t0 + p["speech"][0], 2), round(t0 + p["speech"][1], 2)])
                t0 += p["seconds"]
            out["clips"] = parts
            seconds = t0
        elif t in ("title", "card"):
            out["text"] = sc["ja"]
        elif t == "end":
            out["text"] = sc["ja"]
            out["disclaimer"] = sc.get("disclaimer", "")
        out["sfx"] = list(dict.fromkeys(out["sfx"]))  # one sound of each kind
        out["frames"] = max(1, round(seconds * FPS))
        if vrew:
            out["frames"] = vrew[sc["id"]][1] - vrew[sc["id"]][0]
        scenes.append(out)

    start = 0
    for s in scenes:
        s["start"] = start
        start += s["frames"]
    total = start
    narration = {"file": story["narration"]["audio"]} if vrew else None

    bgm = story.get("bgm")
    if bgm and (PUBLIC / bgm["file"]).exists():
        bgm = dict(bgm, seconds=round(duration(PUBLIC / bgm["file"]), 2))
    elif bgm:
        print(f"⚠ BGM 파일이 없어요 (remotion/public/{bgm['file']}) → 음악 없이 만듭니다")
        bgm = None

    OUT.write_text(json.dumps({"total": total, "scenes": scenes, "bgm": bgm, "narration": narration}, ensure_ascii=False, indent=1),
                   encoding="utf-8")

    # Report (in Korean, for the user)
    print("\n── 장별 길이 ──")
    for ch in keep:
        f = sum(s["frames"] for s in scenes if s["chapter"] == ch)
        if f:
            print(f"  {ch:9s} {f // FPS // 60:2d}분 {f // FPS % 60:02d}초")
    print(f"  전체      {total // FPS // 60:2d}분 {total // FPS % 60:02d}초  (장면 {len(scenes)}개)")
    for w in warnings:
        print(f"⚠ {w}")
    if missing:
        print(f"⚠ 아직 없는 파일 {len(missing)}개 (임시 화면으로 들어감): {', '.join(missing)}")
    return total
