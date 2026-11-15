#!/bin/bash
# 〈심장의 휴가〉 애니매틱 합본: 컷 영상(cache/cuts/*.mp4) + 타이틀 + 소리 → cache/heart_vacation_animatic.mp4
set -e
cd "$(dirname "$0")"
CUTS="A1 C5 C6 C7 C8a C8 C9 C10 C11a C11b C11c C11d C11e C12 C13 C14 C15a C15b C15c C16"
L=cache/concat.txt; : > $L
for c in $CUTS; do echo "file 'cuts/$c.mp4'" >> $L; done
echo "file 'title.mp4'" >> $L
ffmpeg -y -loglevel error -f concat -safe 0 -i $L -c copy cache/_video.mp4
python3 sound_a1.py cache/a1.wav >/dev/null && python3 sound_all.py cache/a1.wav cache/all.wav >/dev/null
ffmpeg -y -loglevel error -i cache/_video.mp4 -i cache/all.wav -c:v copy -c:a aac -b:a 192k -shortest cache/heart_vacation_animatic.mp4
ffprobe -v error -show_entries format=duration -of csv=p=0 cache/heart_vacation_animatic.mp4
