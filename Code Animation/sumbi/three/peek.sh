#!/bin/bash
# peek.sh CUT t1 t2 ... -> color frames to peek/CUT_tXX.png (fast layout check)
cut=$1; shift; mkdir -p peek
fr=$(python3 -c "import sys; print(','.join(str(int(round(float(a)*24/2))*2) for a in sys.argv[1:]))" "$@")
PASSES=color FRAMES=$fr node render.js "film.html?cut=$cut" peek/c$cut 0 60 2>&1 | grep -iE "error|uncaught|meshes" | head -5
