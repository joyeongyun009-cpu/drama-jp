#!/bin/bash
# Runs the whole drama pipeline inside Google Cloud Shell, which is already
# signed in as you, so no API key is needed.
#
#   bash run_cloudshell.sh preview   # character photos + shot 1 + short preview video
#   bash run_cloudshell.sh all       # every shot + final video
set -euo pipefail
cd "$(dirname "$0")"

MODE="${1:-preview}"
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

$PY scripts/generate.py refs
if [[ "$MODE" == "preview" ]]; then
  $PY scripts/generate.py shots --only s01
else
  $PY scripts/generate.py shots
fi
$PY scripts/align.py

cd remotion
[[ -d node_modules ]] || npm ci --silent
npx remotion render Drama out/drama.mp4 --log=error
cd ..

zip -qr refs.zip refs
echo ""
echo "✅ 完成 / 완성: remotion/out/drama.mp4"
echo "   ダウンロード / 다운로드:"
echo "   cloudshell download remotion/out/drama.mp4"
echo "   cloudshell download refs.zip"
