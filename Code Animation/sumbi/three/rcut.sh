#!/bin/bash
# rcut.sh CUT [DUR]  -> pass/cN (all passes) then fin/cN (finished frames)
cut=$1; dur=$(node -e "global.window={CUTS:{}};" 2>/dev/null; python3 - "$cut" <<'P'
import re,sys
c=sys.argv[1]
for f in ['cuts_s1.js','cuts_s2.js','cuts_s3.js','cuts_s4.js']:
    s=open(f).read(); m=re.search(r"C\['%s'\] = \{[^\n]*dur: ([0-9.]+)"%re.escape(c), s)
    if m: print(m.group(1)); break
P
)
rm -rf pass/c$cut fin/c$cut
PASSES=color,id,normal,depth,char node render.js "film.html?cut=$cut" pass/c$cut 0 $dur 2>&1 | grep -iE "error|drawings"
python3 finish.py pass/c$cut fin/c$cut ${WORKERS:-1} | tail -1
