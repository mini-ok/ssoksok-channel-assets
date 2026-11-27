#!/bin/bash
# 규모 체감 쇼츠를 차례로 1080p 렌더: 프레임(2프로세스) → 인코딩 → 소리 → 음량 → 검수. 결과는 /home/claude/work/scale/out/<이름>.mp4
cd "$(dirname "$0")"
OUT=/home/claude/work/scale; mkdir -p $OUT/out
KIT="$(pwd)/../_kit"
for e in "$@"; do
  [ -f $OUT/out/$e.mp4 ] && { echo "SKIP $e"; continue; }
  N=$(MG_SCALE=0.25 python3 run.py $e info | awk '{print $NF}'); H=$((N / 2))
  export MG_SCALE=1 MG_FPS=30
  python3 run.py $e frames $OUT/f_$e 0 $H & P1=$!
  python3 run.py $e frames $OUT/f_$e $H $N & P2=$!
  wait $P1 $P2
  ffmpeg -y -loglevel error -framerate 30 -i $OUT/f_$e/f%05d.png -c:v libx264 -preset slow -crf 18 -maxrate 14M -bufsize 28M -pix_fmt yuv420p $OUT/v_$e.mp4
  python3 audio.py $e $OUT/a_$e.wav > /dev/null
  (cd "$KIT" && python3 -m vfx.loud $OUT/a_$e.wav $OUT/out/$e.mp4 --mux $OUT/v_$e.mp4 && python3 -m vfx.qa report $OUT/out/$e.mp4 --out $OUT/qa_$e > /dev/null)
  rm -rf $OUT/f_$e $OUT/v_$e.mp4
  echo "DONE $e $(date +%H:%M:%S)"
done
echo ALLDONE
