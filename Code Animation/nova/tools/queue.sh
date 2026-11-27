#!/bin/bash
# 렌더 대기열: 대기열 파일의 줄을 위에서부터 하나씩 처리(한 번에 한 편). 줄 형식: nova <이름> | scale <이름>
# 사용: nohup bash tools/queue.sh > $WORK/queue.log 2>&1 &   (반드시 하나만 띄운다: pgrep -af queue.sh)
# 대화 세션에서는 턴이 끝나면 백그라운드가 죽을 수 있으니, 렌더 중에는 턴 안에서 sleep으로 기다리며 확인한다.
WORK=${NOVA_WORK:-/home/claude/work/nova}; Q=$WORK/queue.txt
HERE="$(cd "$(dirname "$0")/.." && pwd)"; NOVA="$HERE"; SCALE="$HERE/../scale"
touch $Q
while true; do
  line=$(head -1 $Q 2>/dev/null)
  if [ -z "$line" ]; then sleep 20; continue; fi
  set -- $line
  if [ "$1" = nova ]; then (cd "$NOVA" && ./make.sh $2); elif [ "$1" = scale ]; then (cd "$SCALE" && ./make_all.sh $2); fi
  sed -i '1d' $Q
  echo "QDONE $line $(date +%H:%M:%S)"
done
