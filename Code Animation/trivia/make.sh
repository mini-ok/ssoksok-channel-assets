#!/bin/bash
# 지식 쇼츠 한 편 만들기:  ./make.sh <에피소드 slug> [작업폴더]
# 4초 구간마다 PNG → mp4(PNG 바로 지움, 끊기면 이어서) → 소리 합성 → 합치기(-14 LUFS) → <작업폴더>/<slug>.mp4
set -e
SLUG=$1; WORK=${2:-/home/claude/work/trivia/$SLUG}
HERE="$(cd "$(dirname "$0")" && pwd)"
mkdir -p "$WORK"; cd "$WORK"
DUR=$(cd "$HERE" && python3 -c "import engine as E; print(E.Episode('$SLUG').DUR)")
SEG=${SEG:-4}; : > list.txt; a=0   # 4초 = PNG 약 360MB(디스크가 작음)
while python3 -c "import sys; sys.exit(0 if $a < $DUR else 1)"; do
  b=$(python3 -c "print(min($a+$SEG, $DUR))"); seg=seg_$(printf %03d $a).mp4
  if [ ! -f $seg ]; then
    python3 "$HERE/render.py" "$SLUG" fr_$a $a $b > /dev/null
    k0=$(python3 -c "print(int(round($a*30)))"); k1=$(python3 -c "print(int(round($b*30)))")
    ffmpeg -y -loglevel error -framerate 30 -start_number $k0 -i fr_$a/f%05d.png -frames:v $((k1-k0)) -c:v libx264 -preset slow -crf 14 -pix_fmt yuv420p $seg
    rm -rf fr_$a; echo "seg $a done"
  fi
  echo "file '$WORK/$seg'" >> list.txt; a=$(python3 -c "print($a+$SEG)")
done
python3 "$HERE/audio.py" "$SLUG" audio.wav
ffmpeg -y -loglevel error -f concat -safe 0 -i list.txt -i audio.wav -map 0:v -map 1:a \
  -af loudnorm=I=-14:TP=-1.5:LRA=11 -ar 48000 -c:v libx264 -preset slow -crf 18 -pix_fmt yuv420p \
  -c:a aac -b:a 192k -shortest -movflags +faststart "$SLUG.mp4"
ffprobe -v error -show_entries format=duration:stream=width,height -of compact "$SLUG.mp4"
echo "-> $WORK/$SLUG.mp4"
