#!/bin/bash
# Runs the whole drama pipeline inside Google Cloud Shell, which is already
# signed in as you, so no API key is needed.
#
#   bash run_cloudshell.sh preview ep02   # character photos + shot 1 + short preview video
#   bash run_cloudshell.sh all ep02       # every shot + final video
#   bash run_cloudshell.sh thumb ep05     # YouTube thumbnail only (story.json "thumbnail")
#   bash run_cloudshell.sh clean ep07     # delete older episodes' images/clips/videos (keeps refs)
#
# Longform episodes (story.json "format": "longform", 16:9), step by step:
#   bash run_cloudshell.sh images ep06          # 1. all images + one numbered overview picture
#   bash run_cloudshell.sh redo ep06 12 30      # 2. remake only images 12 and 30 (or clip01a ...)
#   bash run_cloudshell.sh clips ep06           # 3. talking clips, made from the finished images
#   bash run_cloudshell.sh all ep06             # 4. narration + the full video + thumbnail (once)
# preview = intro + chapter 1 at half size + voice samples. The video is
# rendered in 2-minute parts so a rerun picks up where it stopped.
set -euo pipefail
cd "$(dirname "$0")"

MODE="${1:-preview}"
EP="${2:?편 번호를 적어 주세요. 예: bash run_cloudshell.sh preview ep02}"
shift 2
REDO=("$@")
[[ -f "episodes/$EP/story.json" ]] || { echo "❌ episodes/$EP/story.json 이 없어요"; exit 1; }
# 대본 점검 (롱폼): 문제가 있으면 아무것도 만들기 전에 멈춤
python3 scripts/check.py --ep "$EP"
# 정리: 이번 편(epNN, epNNs) 말고 지난 편들의 그림·영상·완성본·임시 파일을 지워 공간 확보 (인물 사진 refs는 남김)
if [[ "$MODE" == "clean" ]]; then
  for D in remotion/public/shots/*/; do
    N="$(basename "$D")"; [[ "$N" == "$EP" || "$N" == "${EP}s" ]] || rm -rf "$D"
  done
  find remotion/out -maxdepth 1 -mindepth 1 ! -name "${EP}*" -exec rm -rf {} + 2>/dev/null || true
  rm -rf ~/.cache/pip ~/.npm/_cacache ~/drama-jp*.zip refs.zip preview.mp4
  echo "✅ 정리 끝. 남은 공간:"; df -h ~ | tail -1
  exit 0
fi
# 썸네일만: 이미 만든 그림으로 1초 만에 만듦
if [[ "$MODE" == "thumb" ]]; then
  COMP="$(python3 scripts/thumbnail.py --ep "$EP")"
  cd remotion && { [[ -d node_modules ]] || npm ci --silent; }
  npx remotion still "$COMP" "out/${EP}_thumb.jpg" --props="out/${EP}_thumb_props.json" --log=error
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
PY="$PWD/.venv/bin/python"  # absolute: later steps run inside remotion/

$PY scripts/generate.py refs --ep "$EP"
FORMAT="$($PY -c "import json; print(json.load(open('episodes/$EP/story.json')).get('format', 'shorts'))")"
UPTO=()
# ── 단계별 (쇼츠·롱폼 공통): images → redo → clips → all ──
SHOTS_DIR="remotion/public/shots/$EP"
CLIPS_STARTED=""
if [[ "$MODE" == "redo" ]]; then
  # 다시 만들 그림·영상 지우기: 12 → img_12, s05a / clip01a → 그 영상
  # 영상 단계를 이미 시작했으면(영상이 하나라도 있으면) 고친 그림을 쓰는 영상도 같이 다시 만듦
  CLIPS_STARTED="$(ls "$SHOTS_DIR"/*.mp4 >/dev/null 2>&1 && echo yes || true)"
  for X in "${REDO[@]}"; do
    [[ "$X" =~ ^[0-9]+$ ]] && X="img_$(printf %02d "$((10#$X))")"
    rm -f "$SHOTS_DIR/$X.png" "$SHOTS_DIR/$X.mp4" && echo "▶ 다시 만들기: $X"
    if [[ -n "$CLIPS_STARTED" && "$X" == img_* ]]; then
      for C in $($PY -c "import json; print(' '.join(s['id'] for s in json.load(open('episodes/$EP/story.json'))['shots'] if s.get('image') == '$X'))"); do
        rm -f "$SHOTS_DIR/$C.mp4" && echo "▶ 다시 만들기: $C (이 그림으로 만든 영상)"
      done
    fi
  done
fi
if [[ "$MODE" == "images" || "$MODE" == "redo" ]]; then
  $PY scripts/generate.py images --ep "$EP"
  # 그림 단계에서는 영상을 만들지 않음 (영상은 clips 단계에서)
  [[ "$MODE" == "redo" && -n "$CLIPS_STARTED" ]] && $PY scripts/generate.py shots --ep "$EP"
  $PY scripts/sheet.py --ep "$EP"
  echo "✅ 그림 단계 끝. 이상한 그림 번호를 Claude에게 알려 주거나, 괜찮으면 다음: bash run_cloudshell.sh clips $EP"
  exit 0
fi
if [[ "$MODE" == "clips" ]]; then
  $PY scripts/generate.py shots --ep "$EP"
  mkdir -p remotion/out && rm -f "remotion/out/${EP}_clips.zip"
  for C in $($PY -c "import json; print(' '.join(s['id'] for s in json.load(open('episodes/$EP/story.json'))['shots']))"); do
    [[ -f "$SHOTS_DIR/$C.mp4" ]] && zip -qj "remotion/out/${EP}_clips.zip" "$SHOTS_DIR/$C.mp4"
  done
  # 말하는 영상의 대사를 Whisper로 듣고 글로 적어 zip에 함께 넣음 (Claude가 대사 확인용으로 읽음)
  $PY scripts/heard.py --ep "$EP" && zip -qj "remotion/out/${EP}_clips.zip" "remotion/out/${EP}_heard.txt"
  echo "✅ 영상 단계 끝. 확인: cloudshell download remotion/out/${EP}_clips.zip"
  echo "   괜찮으면 다음: bash run_cloudshell.sh all $EP"
  exit 0
fi
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
  $PY scripts/generate.py images --ep "$EP"
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
  rm -rf "$PARTS"  # parts are only for resuming; free the Cloud Shell disk (5 GB)
fi
# 썸네일 (롱폼·쇼츠 모두, story.json에 "thumbnail"이 있으면)
if [[ "$MODE" != "preview" ]] && $PY -c "import json,sys; sys.exit(0 if 'thumbnail' in json.load(open('../episodes/$EP/story.json')) else 1)"; then
  COMP="$(cd .. && $PY scripts/thumbnail.py --ep "$EP")"
  npx remotion still "$COMP" "out/${EP}_thumb.jpg" --props="out/${EP}_thumb_props.json" --log=error
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
