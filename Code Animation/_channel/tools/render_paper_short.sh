#!/bin/bash
# 종이 오림 지식 쇼츠(haedal·simhae·hive 등) 렌더 → 구간 mp4 → 소리 합성 → 최종 mp4.
# 사용:  render_paper_short.sh <작품폴더> <길이초> [작업폴더]
#   예:  render_paper_short.sh haedal 60.2 /home/claude/work/haedal_v
# - 구간(SEG초)마다 PNG를 렌더하고 바로 mp4로 묶은 뒤 PNG를 지운다(디스크가 작아서).
# - 이미 있는 구간 mp4는 건너뛰므로 중간에 끊겨도 다시 돌리면 이어진다.
# - 세로(1080×1920): HD_ORIENT=v. haedal은 가로·세로 둘 다 되고, simhae·hive는 세로 전용.
# - 최종 크기: HD_SCALE=1 → 1080×1920(디자인 픽셀 그대로).
set -e
NAME=$1; DUR=$2; WORK=${3:-/home/claude/work/${NAME}_short}; SEG=${SEG:-10}
HERE="$(cd "$(dirname "$0")/../.." && pwd)"          # Code Animation/
mkdir -p "$WORK"; cd "$WORK"
: > list.txt
a=0
while python3 -c "import sys; sys.exit(0 if $a < $DUR else 1)"; do
  b=$(python3 -c "print(min($a+$SEG, $DUR))")
  seg=seg_$(printf %03d $a).mp4
  if [ ! -f $seg ]; then
    HD_ORIENT=${HD_ORIENT:-v} HD_SCALE=${HD_SCALE:-1} python3 "$HERE/$NAME/render.py" fr_$a $a $b > /dev/null
    k0=$(python3 -c "print(int(round($a*30)))")
    ffmpeg -y -loglevel error -framerate 30 -start_number $k0 -i fr_$a/f%05d.png \
      -c:v libx264 -preset slow -crf 12 -pix_fmt yuv420p $seg && rm -rf fr_$a
    echo "seg $a done"
  fi
  echo "file '$WORK/$seg'" >> list.txt
  a=$(python3 -c "print($a+$SEG)")
done
python3 "$HERE/$NAME/audio.py" "$WORK/audio.wav"
ffmpeg -y -loglevel error -f concat -safe 0 -i list.txt -i audio.wav -map 0:v -map 1:a \
  -c:v libx264 -preset slow -crf 18 -pix_fmt yuv420p -c:a aac -b:a 192k -shortest -movflags +faststart \
  "$WORK/${NAME}_short_1080x1920.mp4"
echo "-> $WORK/${NAME}_short_1080x1920.mp4"
