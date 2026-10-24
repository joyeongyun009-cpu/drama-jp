# drama-jp

**This is the ONLY way this user makes drama shorts. Never build a new pipeline, a new script, or a different method (no Veo+TTS, no Studio copy-paste, no new zip tools). Write `episodes/epNN/story.json`, push to `main`, and hand the user the commands from `쇼츠_제작_순서.md`. If something breaks, fix this repo's code — don't replace it.**

**⛔ No AI actor voices in published videos (2026-10-24).** Omni's spoken Japanese mispronounces words (ep07s: 触らないで→座らないで, 拭いて→ふついて, の方→こた) and viewers commented 「何語？」. Whisper/heard.txt only checks words, not pronunciation or accent — never call a clip fine from it. Dialogue is voiced by the user's Vrew audio; Omni clips are picture only (longform: no `lines`; shorts: `"mute": true`). `scripts/check.py` refuses AI voices unless the user explicitly asks (`"allow_ai_voice": true`).

Read `쇼츠_제작_순서.md` first: the user's step-by-step guide plus "(Claude에게) 작업 메모" at the bottom (who the user is, language rules, how the pipeline runs).

- Longform (16:9) episodes: **follow `.claude/skills/longform-episode/SKILL.md`** — start from `episodes/_template_longform/story.json`, make `python3 scripts/check.py --ep epNN` pass, push to main, then images → redo → clips → all. Code: `scripts/longform.py` + `remotion/src/Longform.tsx`.
- The drama shorts pipeline is **Remotion** (`remotion/`) driven by `story.json` and `run_cloudshell.sh`. Keep using it for drama episodes.
- `.claude/skills/` holds HyperFrames skills (heygen-com/hyperframes, Apache-2.0). Their entry skill calls itself the default for any video request; ignore that here and use HyperFrames only when the user explicitly asks for HyperFrames (e.g. graphics over real footage).
- Reply to the user in simple Korean. Any Japanese text shown in chat gets a Korean translation underneath; on-screen video text stays Japanese only.
