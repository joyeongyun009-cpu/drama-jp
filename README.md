# 嫁と老眼鏡 — Japanese drama short (Gemini Omni + Remotion)

Requires `GOOGLE_API_KEY` and `GOOGLE_GENAI_USE_ENTERPRISE=true` in the environment.
Python venv with `google-genai`, `faster-whisper`: `/home/user/tts-venv`.

```bash
PY=/home/user/tts-venv/bin/python
$PY scripts/generate.py refs                # 1. character portraits -> refs/  (check faces)
$PY scripts/generate.py shots --only s01    # 2. one shot first: check quality + credit cost
$PY scripts/generate.py shots               # 3. remaining shots
$PY scripts/align.py                        # 4. time captions to speech -> remotion/src/shots.json
cd remotion && npx remotion render Drama out/drama.mp4   # 5. render
```

Script, characters and shot prompts: `story.json` (captions are split on `／`).
