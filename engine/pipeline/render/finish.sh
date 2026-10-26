#!/bin/bash
# $1 = variant, $2 = output filename
set -e
V=$1; OUT=$2
cd /home/claude/work/sit
D=/home/claude/work/vid
: > $D/list_$V.txt
for p in 0 1 2 3; do echo "file '$D/v_${V}_$p.mp4'" >> $D/list_$V.txt; done
ffmpeg -y -v error -f concat -safe 0 -i $D/list_$V.txt -c copy $D/cat_$V.mp4
/usr/bin/python3 -I mix.py $V > $D/mix_$V.json
ffmpeg -y -v error -i $D/cat_$V.mp4 -i /home/claude/work/ep/$V/mix.wav -map 0:v:0 -map 1:a:0 \
  -af "loudnorm=I=-13.2:TP=-1.5:LRA=11" -ar 48000 -c:v copy -c:a aac -b:a 192k -movflags +faststart -shortest "/home/claude/work/out/$OUT"
ffprobe -v error -show_entries format=duration:stream=width,height -of default=nw=1 "/home/claude/work/out/$OUT"
