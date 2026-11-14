#!/bin/bash
# Blender 렌더 컷(mp4) + 타이틀 + 소리 → cache/heart_vacation_blender.mp4
# 사용: ./assemble_blender.sh <컷 mp4 폴더>
set -e
cd "$(dirname "$0")"
D="$1"
CUTS="A1 C5 C6 C7 C8a C8 C9 C10 C11a C11b C11c C11d C11e C12 C13 C14 C15a C15b C15c C16"
TITLE_SCALE=1.3333334 python3 title.py cache/title720.mp4 >/dev/null
args=(); fc=""; i=0
for c in $CUTS; do args+=(-i "$D/$c.mp4"); fc+="[$i:v]fps=24,scale=1280:720,setsar=1,format=yuv420p[v$i];"; i=$((i+1)); done
args+=(-i cache/title720.mp4); fc+="[$i:v]fps=24,scale=1280:720,setsar=1,format=yuv420p[v$i];"; i=$((i+1))
for ((k=0;k<i;k++)); do fc+="[v$k]"; done; fc+="concat=n=$i:v=1:a=0[out]"
python3 sound_a1.py cache/a1.wav >/dev/null && python3 sound_all.py cache/a1.wav cache/all.wav >/dev/null
ffmpeg -y -loglevel error "${args[@]}" -i cache/all.wav -filter_complex "$fc" -map "[out]" -map $i:a -c:v libx264 -preset veryfast -crf 18 -c:a aac -b:a 192k -shortest cache/heart_vacation_blender.mp4
ffprobe -v error -show_entries format=duration -of csv=p=0 cache/heart_vacation_blender.mp4
