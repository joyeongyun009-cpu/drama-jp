# drama-jp

**This is the ONLY way this user makes drama shorts. Never build a new pipeline, a new script, or a different method (no Veo+TTS, no Studio copy-paste, no new zip tools). Write `episodes/epNN/story.json`, push to `main`, and hand the user the commands from `쇼츠_제작_순서.md`. If something breaks, fix this repo's code — don't replace it.**

Read `쇼츠_제작_순서.md` first: the user's step-by-step guide plus "(Claude에게) 작업 메모" at the bottom (who the user is, language rules, how the pipeline runs).

- Longform (16:9) episodes use the same repo and commands: `"format": "longform"` in story.json → `scripts/longform.py` + `remotion/src/Longform.tsx`. See the 롱폼 section of `쇼츠_제작_순서.md`.
- The drama shorts pipeline is **Remotion** (`remotion/`) driven by `story.json` and `run_cloudshell.sh`. Keep using it for drama episodes.
- `.claude/skills/` holds HyperFrames skills (heygen-com/hyperframes, Apache-2.0). Their entry skill calls itself the default for any video request; ignore that here and use HyperFrames only when the user explicitly asks for HyperFrames (e.g. graphics over real footage).
- Reply to the user in simple Korean. Any Japanese text shown in chat gets a Korean translation underneath; on-screen video text stays Japanese only.
