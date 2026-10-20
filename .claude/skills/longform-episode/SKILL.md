---
name: longform-episode
description: Make the next 和子 family series LONGFORM (16:9, ~10 min) episode in this repo — write episodes/epNN/story.json from the template, check it, push to main, and walk the user through images → redo → clips → all in Cloud Shell. Use when the user says "롱폼 N편 만들자", gives a scenes.json from claude.ai, or asks about the longform steps.
---

# 롱폼 한 편 만들기 (시행착오 없이)

The user (Korean, 57, beginner, runs a Japanese-audience channel) makes videos while working, so
their hands-on time must be minutes, not hours. Everything below was learned the hard way on ep05
(2026-10-20). Reply in simple Korean; every Japanese line shown in chat gets a Korean translation.

## 1. Write the script (Claude)
1. Copy `episodes/_template_longform/story.json` to `episodes/epNN/story.json` and fill it.
   If the user brings a claude.ai `scenes.json`, convert it into this format (keep every `ja` exactly).
2. Rules the checker enforces (`python3 scripts/check.py --ep epNN` must pass, warnings fixed too):
   - **Never change `ja` text** after the user approved it. Captions are Japanese only.
   - Every image prompt with people says **Japanese** (ep05 img_61 came out with foreign kids).
     generate.py also appends "every person is Japanese" automatically.
   - Series faces: reuse `refs` ids `kazuko` (和子, **68**), `rena`, `kenta`, `sota`; new people get new ids.
   - Omni clips (`shots`): **max 10 s each, one line per clip** (split long ones: clip01a/clip01b),
     the exact line inside 「」 in the prompt, and `"image": "img_NN"` = the still it is built on.
   - `punch_zoom` / `shake` only on real shock moments, together with `"sfx": "impact"` (or a flash cut).
     Elsewhere use zoom/pan/push_slow (user: constant shaking looked awkward).
   - Motion is big on purpose (zoom to 1.6x, pans 44–50 %) — never make it smaller.
   - No speaker name tags on screen. Title/thumbnail never say 実話; the end card says フィクション.
   - `thumbnail`: left = shock image, right = calm 和子 image, **two lines** (top white, bottom yellow punchline).
   - Aim for about 40–50 images; reuse a still with a different motion instead of making near-duplicates.
3. Commit and **push to `main`** (Cloud Shell pulls main).

## 2. Hand the user these steps (one at a time, wait for each result)
```
cd ~/drama-jp && git fetch -q origin && git reset -q --hard origin/main && echo "✅ 최신으로 받음"
cd ~/drama-jp && bash run_cloudshell.sh images epNN      # 15–20 min → epNN_images.jpg overview
cd ~/drama-jp && bash run_cloudshell.sh redo epNN 12 30  # only the bad numbers, repeat until fine
cd ~/drama-jp && bash run_cloudshell.sh clips epNN       # talking clips from the finished stills
cd ~/drama-jp && bash run_cloudshell.sh all epNN         # narration + render ONCE + thumbnail
```
Downloads: `cloudshell download remotion/out/epNN_images.jpg` / `epNN_clips.zip` / `epNN.mp4` / `epNN_thumb.jpg`.
Ask the user to show you the overview picture; point out bad numbers yourself (foreign faces,
wrong person, text in the picture, extra fingers).

## 3. Known problems and the fix
| Symptom | Fix |
|---|---|
| `You do not currently have an active account` / 로그인이 풀렸어요 | `gcloud auth login` → Y → open link → allow → paste code **in the black window** (never in chat) → rerun |
| Stopped / disconnected | Rerun the same command; finished images, clips, voice and render parts are reused |
| `⚠ 아직 없는 파일` / red boxes in the overview | Run the same step again (busy errors are retried, but can still run out) |
| Download fails, 「디스크가 가득 참」 | Free space on the PC (old mp4s, empty recycle bin), or editor (pencil) → `remotion/out` → right-click → Download |
| A rerender after changing images | Unavoidable — that is why images and clips are checked before `all` |

## 4. Upload help
Give a Japanese title (quote-style like the channel's other videos, no 【実話】), description with
※フィクション and ※AI notes, tags, pinned comment — each with Korean translation — and remind:
「변경되거나 합성된 콘텐츠」→「예」.
