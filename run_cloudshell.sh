#!/bin/bash
# Runs the whole drama pipeline inside Google Cloud Shell, which is already
# signed in as you, so no API key is needed.
#
#   bash run_cloudshell.sh preview ep02   # character photos + shot 1 + short preview video
#   bash run_cloudshell.sh all ep02       # every shot + final video
#   bash run_cloudshell.sh thumb ep05     # YouTube thumbnail only (story.json "thumbnail")
#
# Longform episodes (story.json "format": "longform", 16:9) use the same two
# commands: preview = intro + chapter 1 at half size + voice samples,
# all = every image / clip / narration + the full video, rendered in
# 2-minute parts so a rerun picks up where it stopped.
set -euo pipefail
cd "$(dirname "$0")"

MODE="${1:-preview}"
EP="${2:?편 번호를 적어 주세요. 예: bash run_cloudshell.sh preview ep02}"
[[ -f "episodes/$EP/story.json" ]] || { echo "❌ episodes/$EP/story.json 이 없어요"; exit 1; }
# 썸네일만: 이미 만든 그림으로 1초 만에 만듦
if [[ "$MODE" == "thumb" ]]; then
  python3 scripts/thumbnail.py --ep "$EP"
  cd remotion && { [[ -d node_modules ]] || npm ci --silent; }
  npx remotion still Thumbnail "out/${EP}_thumb.jpg" --props="out/${EP}_thumb_props.json" --log=error
  echo "✅ 썸네일: cloudshell download remotion/out/${EP}_thumb.jpg"
  exit 0
fi
if [[ -z "$(gcloud auth list --filter=status:ACTIVE --format='value(account)' 2>/dev/null)" ]]; then
  echo "❌ Cloud Shell 로그인이 풀렸어요. 아래를 붙여넣고 안내대로 로그인한 뒤, 같은 명령어를 다시 실행하세요:"
  echo "   gcloud auth login"
  exit 1
fi
PROJECT="$(gcloud config get-value project 2>/dev/null || true)"
if [[ -z "$PROJECT" ]]; then
  PROJECT="$(gcloud projects list --format='value(projectId)' --limit=1)"
  gcloud config set project "$PROJECT" --quiet
fi
if [[ -z "$PROJECT" ]]; then
  echo "❌ 프로젝트를 찾지 못했어요: gcloud config set project <PROJECT_ID>"
  exit 1
fi
export GOOGLE_CLOUD_PROJECT="$PROJECT"
export GOOGLE_CLOUD_LOCATION=global
export GOOGLE_GENAI_USE_ENTERPRISE=true
export GOOGLE_GENAI_USE_VERTEXAI=true
echo "▶ project: $GOOGLE_CLOUD_PROJECT"

gcloud services enable aiplatform.googleapis.com --quiet
# ffmpeg for audio checks, Japanese fonts so captions never render as boxes
if ! command -v ffmpeg >/dev/null || ! fc-list | grep -qi "Noto Sans CJK"; then
  sudo apt-get update -qq && sudo apt-get install -y -qq ffmpeg fonts-noto-cjk >/dev/null
fi

if [[ ! -d .venv ]]; then
  python3 -m venv .venv
  .venv/bin/pip install -q "google-genai>=2.0.0" pillow faster-whisper
fi
PY=.venv/bin/python

$PY scripts/generate.py refs --ep "$EP"
FORMAT="$($PY -c "import json; print(json.load(open('episodes/$EP/story.json')).get('format', 'shorts'))")"
UPTO=()
if [[ "$FORMAT" == "longform" ]]; then
  # ── 롱폼 (16:9): 이미지 + 움직임 + 나레이션 + 입을 여는 영상 ──
  gcloud services enable texttospeech.googleapis.com --quiet
  if [[ "$MODE" == "preview" ]]; then
    UPTO=(--upto ch1)   # 미리보기: 인트로 + 1장만
    $PY scripts/generate.py samples --ep "$EP"
  fi
  $PY scripts/generate.py images --ep "$EP" "${UPTO[@]}"
  $PY scripts/generate.py shots --ep "$EP" "${UPTO[@]}"
  $PY scripts/generate.py voice --ep "$EP" "${UPTO[@]}"
elif [[ "$MODE" == "preview" ]]; then
  $PY scripts/generate.py shots --ep "$EP" --only s01
else
  $PY scripts/generate.py shots --ep "$EP"
fi
# BGM: story.json의 "bgm" 파일이 없으면, 홈 폴더에 올린 가장 최근 mp3를 그 이름으로 복사
BGM="$($PY -c "import json,sys; b=json.load(open('episodes/$EP/story.json')).get('bgm'); print(b['file'] if b else '')")"
if [[ -n "$BGM" && ! -f "remotion/public/$BGM" ]]; then
  NEWEST="$(ls -t ~/*.mp3 2>/dev/null | head -1 || true)"
  if [[ -n "$NEWEST" ]]; then
    mkdir -p "remotion/public/$(dirname "$BGM")"
    cp "$NEWEST" "remotion/public/$BGM"
    echo "▶ BGM: $(basename "$NEWEST")"
  fi
fi
$PY scripts/align.py --ep "$EP" "${UPTO[@]}"

cd remotion
[[ -d node_modules ]] || npm ci --silent
if [[ "$FORMAT" != "longform" ]]; then
  npx remotion render Drama "out/$EP.mp4" --log=error
elif [[ "$MODE" == "preview" ]]; then
  npx remotion render Longform "out/$EP.mp4" --scale=0.5 --log=error
else
  # 2분씩 나눠서 만들고 이어 붙임 → 끊겨도 같은 명령어로 이어서 만듦
  TOTAL="$(node -e "console.log(require('./src/longform.json').total)")"
  PARTS="out/${EP}_parts"
  SUM="$(sha1sum src/longform.json | cut -c1-16)"
  [[ "$(cat "$PARTS/.sum" 2>/dev/null)" == "$SUM" ]] || { rm -rf "$PARTS"; mkdir -p "$PARTS"; echo "$SUM" > "$PARTS/.sum"; }
  CHUNK=3600
  : > "$PARTS/list.txt"
  for ((A = 0; A < TOTAL; A += CHUNK)); do
    B=$(( A + CHUNK - 1 < TOTAL - 1 ? A + CHUNK - 1 : TOTAL - 1 ))
    PART="$PARTS/p$(printf %06d "$A").mp4"
    if [[ ! -f "$PART" ]]; then
      echo "▶ 렌더링 $(( A * 100 / TOTAL ))% ..."
      npx remotion render Longform "$PART.tmp.mp4" --frames="$A-$B" --log=error
      mv "$PART.tmp.mp4" "$PART"
    fi
    echo "file '$(basename "$PART")'" >> "$PARTS/list.txt"
  done
  ffmpeg -y -v error -f concat -safe 0 -i "$PARTS/list.txt" -c copy "out/$EP.mp4"
  if $PY -c "import json,sys; sys.exit(0 if 'thumbnail' in json.load(open('../episodes/$EP/story.json')) else 1)"; then
    (cd .. && $PY scripts/thumbnail.py --ep "$EP" >/dev/null)
    npx remotion still Thumbnail "out/${EP}_thumb.jpg" --props="out/${EP}_thumb_props.json" --log=error
  fi
fi
# 유튜브 권장 음량(-14 LUFS)으로 맞춤 (영상은 그대로, 소리만)
ffmpeg -y -v error -i "out/$EP.mp4" -c:v copy -af loudnorm=I=-14:TP=-1.5:LRA=11 -ar 48000 -c:a aac -b:a 192k "out/$EP.loud.mp4" \
  && mv "out/$EP.loud.mp4" "out/$EP.mp4"
cd ..

zip -qr refs.zip refs $( [[ -d voice_samples ]] && echo voice_samples )
echo ""
echo "✅ 完成 / 완성: remotion/out/$EP.mp4"
echo "   ダウンロード / 다운로드:"
echo "   cloudshell download remotion/out/$EP.mp4"
echo "   cloudshell download refs.zip"
[[ -f "remotion/out/${EP}_thumb.jpg" ]] && echo "   cloudshell download remotion/out/${EP}_thumb.jpg   (썸네일)"
