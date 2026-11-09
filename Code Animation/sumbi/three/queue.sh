#!/bin/bash
# queue.sh cut cut ... : render+finish sequentially, skipping cuts already finished
for c in "$@"; do
  if [ -f fin/c$c/.done ]; then continue; fi
  echo "== C$c $(date +%T)"; ./rcut.sh $c && touch fin/c$c/.done
done
