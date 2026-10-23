# Checks a longform story.json before anything is generated, so mistakes are
# caught in one second instead of after an hour of images and rendering.
# Every rule here comes from a real problem on ep05.
#
#   python scripts/check.py --ep ep06        (run_cloudshell.sh runs it first)
#
# Errors (❌) stop the run; warnings (⚠) are printed and the run goes on.
import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
TYPES = {"narration", "line", "clip", "image", "title", "card", "chat", "letter", "end"}
MOTIONS = {"zoom_in_big", "zoom_out_big", "pan_left", "pan_right", "pan_up", "pan_down",
           "slide_in_left", "slide_in_right", "punch_zoom", "shake", "push_slow", "parallax"}
CHAPTERS = ["intro", "ch1", "ch2", "ch3", "ch4", "ch5", "epilogue"]
OMNI_MAX_SEC = 10


def check(story):
    err, warn = [], []
    for key in ("title", "thumbnail", "style", "bgm", "voice", "speakers", "characters", "images", "shots", "scenes"):
        if key not in story:
            err.append(f"'{key}' 항목이 없어요")
    if err:
        return err, warn

    chars = story["characters"]
    images = {im["id"]: im for im in story["images"]}
    shots = {s["id"]: s for s in story["shots"]}

    for im in story["images"]:
        if not re.fullmatch(r"img_\d{2}", im["id"]):
            err.append(f"{im['id']}: 그림 이름은 img_01 형식이어야 해요")
        for r in im.get("refs", []):
            if r not in chars:
                err.append(f"{im['id']}: 없는 인물 '{r}'")
        p = im["prompt"].lower()
        if im.get("japanese") is False:  # foreign-story scene: no "Japanese" needed
            continue
        # ep05 img_61: "children" without "Japanese" came out as foreign kids
        if re.search(r"\b(children|kids|people|relatives|students|customers|crowd)\b", p) and "japanese" not in p:
            warn.append(f"{im['id']}: 사람이 나오는데 'Japanese'가 없어요 → 외국인이 나올 수 있어요")

    vrew = story.get("narration")
    used_images = set()
    for sh in story["shots"]:
        sec = float(str(sh.get("duration", "0")).rstrip("s"))
        if sec > OMNI_MAX_SEC:
            err.append(f"{sh['id']}: Omni 영상은 {OMNI_MAX_SEC}초까지예요 ({sec:g}초) → 대사별로 나누기 (clip01a, clip01b)")
        if vrew:  # silent clips under the narration, or talking clips that replace one caption line
            pass
        elif not sh.get("lines"):
            err.append(f"{sh['id']}: lines(대사)가 없어요")
        for sp, ja in sh.get("lines", []):
            if f"「{ja}」" not in sh["prompt"]:
                err.append(f"{sh['id']}: 대사 「{ja[:15]}…」가 prompt 안에 「」로 그대로 들어 있지 않아요")
            chars_per_sec = len(ja) / max(sec, 1)
            if chars_per_sec > 6:
                warn.append(f"{sh['id']}: {sec:g}초에 {len(ja)}자는 빨라요 → 영상 길이를 늘리거나 나누기")
        if not sh.get("image"):
            warn.append(f"{sh['id']}: 'image'(바탕 그림)가 없어요 → 앞뒤 그림과 얼굴·방이 달라질 수 있어요")
        elif sh["image"] not in images:
            err.append(f"{sh['id']}: 바탕 그림 {sh['image']}이(가) images에 없어요")
        for r in sh.get("refs", []):
            if r not in chars:
                err.append(f"{sh['id']}: 없는 인물 '{r}'")

    ids, prev_motion = set(), None
    for sc in story["scenes"]:
        sid = sc.get("id", "?")
        if sid in ids:
            err.append(f"{sid}: 장면 번호가 겹쳐요")
        ids.add(sid)
        t = sc.get("type")
        if t not in TYPES:
            err.append(f"{sid}: 모르는 장면 종류 '{t}'")
            continue
        if sc.get("chapter") not in CHAPTERS:
            err.append(f"{sid}: chapter는 {', '.join(CHAPTERS)} 중 하나여야 해요")
        if t in ("narration", "line", "chat", "letter", "title", "card", "end") and not sc.get("ja") and not (vrew and t not in ("title", "card", "end")):
            err.append(f"{sid}: 일본어(ja)가 없어요")
        if t in ("image", "title", "card", "end") and not sc.get("duration") and not vrew:
            err.append(f"{sid}: duration(초)이 없어요")
        if t == "line" and sc.get("speaker") not in story["speakers"]:
            err.append(f"{sid}: speaker '{sc.get('speaker')}'가 speakers에 없어요")
        if t == "chat" and not sc.get("messages"):
            err.append(f"{sid}: 단톡방 messages가 없어요")
        if t == "clip":
            for c in sc.get("clips", []):
                if c not in shots:
                    err.append(f"{sid}: 영상 {c}이(가) shots에 없어요")
            if not sc.get("clips"):
                err.append(f"{sid}: clips가 비어 있어요")
        if "image" in sc:
            if sc["image"] not in images:
                err.append(f"{sid}: 그림 {sc['image']}이(가) images에 없어요")
            used_images.add(sc["image"])
            m = sc.get("motion", "zoom_in_big")
            if m not in MOTIONS:
                err.append(f"{sid}: 모르는 움직임 '{m}'")
            # ep05 feedback: shaking everywhere looked awkward
            if m in ("punch_zoom", "shake") and sc.get("sfx") != "impact" and sc.get("transition") != "flash":
                warn.append(f"{sid}: {m}은 충격 장면에만 (sfx: impact) — 여기서는 흔들림 없이 다가가기만 해요")
            if m == prev_motion:
                warn.append(f"{sid}: 앞 장면과 같은 움직임({m}) → 자동으로 바뀌어요")
            prev_motion = m
        else:
            prev_motion = None
        if t == "end" and "フィクション" not in sc.get("disclaimer", ""):
            err.append(f"{sid}: 마지막 화면 disclaimer에 「フィクション」이 없어요 (실화라고 하면 안 돼요)")

    if vrew:
        err += check_vrew(story, shots)

    unused = sorted(set(images) - used_images - {s.get("image") for s in story["shots"]})
    if unused:
        warn.append(f"쓰이지 않는 그림 {len(unused)}장 (만들 필요 없음): {', '.join(unused)}")
    if "実話" in story["title"] or "実話" in json.dumps(story.get("thumbnail", {}), ensure_ascii=False):
        err.append("제목/썸네일에 「実話」(실화)가 있어요 → 픽션이므로 빼기")
    th = story["thumbnail"]
    if len(th.get("lines", [])) != 2:
        err.append("thumbnail.lines는 두 줄이어야 해요 (사용자 요청)")
    for k in ("left", "right"):
        if th.get(k) not in images:
            err.append(f"thumbnail.{k} 그림 {th.get(k)}이(가) images에 없어요")
    return err, warn


def check_vrew(story, shots):
    """Vrew narration: scenes must cover the .srt lines 1..N in order, with no gap and no overlap."""
    from longform import read_srt
    err = []
    srt_path = ROOT / story["narration"]["srt"]
    if not srt_path.exists():
        return [f"자막 파일이 없어요: {story['narration']['srt']}"]
    if not (ROOT / "remotion" / "public" / story["narration"]["audio"]).exists():
        err.append(f"나레이션 파일이 없어요: remotion/public/{story['narration']['audio']}")
    srt = read_srt(srt_path)
    want = 1
    for sc in story["scenes"]:
        a, b = sc.get("srt", [0, 0])
        if a != want or b < a:
            err.append(f"{sc['id']}: srt는 [{want}, …]로 시작해야 해요 (지금 {sc.get('srt')})")
        want = b + 1
        if sc.get("type") == "clip":
            sec = srt[min(b, len(srt)) - 1][1] - srt[min(a, len(srt)) - 1][0]
            talking = [c for c in sc.get("clips", []) if shots.get(c, {}).get("lines")]
            if talking:
                said = "".join(ja for c in talking for _, ja in shots[c]["lines"])
                heard = "".join(x[2] for x in srt[a - 1:b]).strip("「」")
                if said != heard:
                    err.append(f"{sc['id']}: 말하는 영상 대사가 자막과 달라요 (자막: {heard})")
            for c in sc.get("clips", []):
                if c in shots and float(shots[c]["duration"].rstrip("s")) < sec:
                    err.append(f"{sc['id']}: 영상 {c}이(가) 장면({sec:.1f}초)보다 짧아요")
    if want - 1 != len(srt):
        err.append(f"장면이 자막 {want - 1}줄까지만 덮어요 (자막은 {len(srt)}줄)")
    return err


def check_shorts(story):
    """Promo / drama shorts made the step-by-step way (images → clips)."""
    err, warn = [], []
    images = {im["id"] for im in story.get("images", [])}
    ids = set()
    for sh in story["shots"]:
        sid = sh["id"]
        if sid in ids:
            err.append(f"{sid}: 영상 번호가 겹쳐요")
        ids.add(sid)
        if sh.get("card"):
            continue
        if sh.get("reuse"):
            if sh["reuse"] not in ids:
                err.append(f"{sid}: 다시 쓰는 영상 {sh['reuse']}이(가) 앞에 없어요")
            continue
        sec = float(str(sh.get("duration", "0")).rstrip("s"))
        if not 5 <= sec <= OMNI_MAX_SEC:
            err.append(f"{sid}: Omni 영상은 5~{OMNI_MAX_SEC}초예요 ({sec:g}초)")
        for sp, ja in sh.get("lines", []):
            if f"「{ja}」" not in sh["prompt"]:
                err.append(f"{sid}: 대사 「{ja[:15]}…」가 prompt 안에 「」로 그대로 들어 있지 않아요")
            if "".join(sh.get("captions", "").split("／")) != ja:
                warn.append(f"{sid}: 자막(captions)이 대사와 달라요 — 줄바꿈(／)만 넣었는지 확인")
            if len(ja) / max(sec, 1) > 6:
                warn.append(f"{sid}: {sec:g}초에 {len(ja)}자는 빨라요")
        if images:
            if sh.get("image") not in images:
                err.append(f"{sid}: 바탕 그림(image)이 없거나 images에 없어요")
        for r in sh.get("refs", []):
            if r not in story["characters"]:
                err.append(f"{sid}: 없는 인물 '{r}'")
    for im in story.get("images", []):
        p = im["prompt"].lower()
        if "japanese" not in p:
            warn.append(f"{im['id']}: 'Japanese'가 없어요 → 외국인이 나올 수 있어요")
    e = story.get("ending", {})
    if "フィクション" not in e.get("note", ""):
        err.append("ending.note에 「フィクション」이 없어요")
    if "実話" in story.get("title", ""):
        err.append("제목에 「実話」(실화)가 있어요 → 빼기")
    return err, warn


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ep", required=True)
    ep = ap.parse_args().ep
    story = json.loads((ROOT / "episodes" / ep / "story.json").read_text(encoding="utf-8"))
    if story.get("format") == "longform":
        err, warn = check(story)
    elif story.get("images"):
        err, warn = check_shorts(story)
    else:
        return
    for w in warn:
        print(f"⚠ {w}")
    for e in err:
        print(f"❌ {e}")
    if err:
        sys.exit(f"\n❌ 대본(story.json)에 고칠 곳이 {len(err)}개 있어요. 이 화면을 Claude에게 보여 주세요.")
    print(f"✅ 대본 점검 통과 (그림 {len(story.get('images', []))}장, 영상 {len(story['shots'])}개)")


if __name__ == "__main__":
    main()
