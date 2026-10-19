#!/bin/bash
# Runs the whole drama pipeline inside Google Cloud Shell, which is already
# signed in as you, so no API key is needed.
#
#   bash run_cloudshell.sh preview ep02   # character photos + shot 1 + short preview video
#   bash run_cloudshell.sh all ep02       # every shot + final video
set -euo pipefail
cd "$(dirname "$0")"

MODE="${1:-preview}"
EP="${2:?편 번호를 적어 주세요. 예: bash run_cloudshell.sh preview ep02}"
[[ -f "episodes/$EP/story.json" ]] || { echo "❌ episodes/$EP/story.json 이 없어요"; exit 1; }
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
if [[ "$MODE" == "preview" ]]; then
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
$PY scripts/align.py --ep "$EP"

cd remotion
[[ -d node_modules ]] || npm ci --silent
npx remotion render Drama "out/$EP.mp4" --log=error
# 유튜브 권장 음량(-14 LUFS)으로 맞춤 (영상은 그대로, 소리만)
ffmpeg -y -v error -i "out/$EP.mp4" -c:v copy -af loudnorm=I=-14:TP=-1.5:LRA=11 -ar 48000 -c:a aac -b:a 192k "out/$EP.loud.mp4" \
  && mv "out/$EP.loud.mp4" "out/$EP.mp4"
cd ..

zip -qr refs.zip refs
echo ""
echo "✅ 完成 / 완성: remotion/out/$EP.mp4"
echo "   ダウンロード / 다운로드:"
echo "   cloudshell download remotion/out/$EP.mp4"
echo "   cloudshell download refs.zip"
