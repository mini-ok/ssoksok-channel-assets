#!/bin/bash
# 새 컨테이너에서 한 번 실행: 저장소 코드를 제작 작업 폴더 구조로 배치한다.
# 사용법: bash /home/claude/assets/engine/pipeline/setup.sh   (그 뒤 docs/pipeline_notes.md 의 '실행 순서'를 따른다)
set -e
A=/home/claude/assets; W=/home/claude/work
mkdir -p $W/{ps,sit,up,ep,vid,out,cache,media} /home/claude/shorts-health
cp -r $A/engine/paper_story/* $W/ps/
cp $A/engine/pipeline/render/* $W/sit/
cp $A/engine/pipeline/upload/* $W/up/
cp $A/engine/pipeline/tts/tts.py /home/claude/shorts-health/tts.py
[ -f $A/engine/pipeline/chars_stomach_patch.py ] && cp $A/engine/pipeline/chars_stomach_patch.py $W/ps/ && echo "위 대리 패치는 chars.py 끝에 붙이거나 임포트한다(노트 6번)"
echo "ready: $W (ps=화풍 코드, sit=장면·믹스, up=업로드). 대본은 $W/sit/eps.py 만 새로 쓴다."
