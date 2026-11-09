# -*- coding: utf-8 -*-
"""Cut the film together: fin/cN frames (C1–C33) + title (C34) + credit (C35) + the mix -> sumbi.mp4
usage: python3 assemble.py [out.mp4] [first_cut last_cut]  (a range makes a preview without the cards)"""
import json, os, subprocess, sys
CUTS = [('1', 7), ('2', 5), ('3', 4), ('4', 3), ('5', 5), ('6', 5), ('7', 3), ('8', 3), ('9', 5), ('10', 4), ('11', 4), ('12', 3), ('13', 2.8),
        ('14', 2), ('15', 6), ('16', 2), ('17', 4), ('18', 5), ('19', 4), ('20', 4), ('21', 3), ('22', 4), ('23', 4), ('24', 4), ('25', 6),
        ('26', 2), ('27', 5), ('28', 7), ('29', 8), ('30', 22), ('31', 5), ('32', 4), ('33', 6)]
out = sys.argv[1] if len(sys.argv) > 1 else 'sumbi.mp4'
rng = (sys.argv[2], sys.argv[3]) if len(sys.argv) > 3 else None
ids = [c for c, _ in CUTS]
sel = CUTS if not rng else CUTS[ids.index(rng[0]): ids.index(rng[1]) + 1]
lines, t0 = [], 0.0
starts = {}; acc = 0.0
for c, d in CUTS: starts[c] = acc; acc += d
for c, d in sel:
    n = int(round(d * 24))
    for i in range(n):
        f = f'fin/c{c}/f_{i:04d}.png'
        if not os.path.exists(f):            # missing (not rendered yet): hold the last available drawing
            k = i
            while k > 0 and not os.path.exists(f'fin/c{c}/f_{k:04d}.png'): k -= 1
            f = f'fin/c{c}/f_{k:04d}.png' if os.path.exists(f'fin/c{c}/f_{k:04d}.png') else 'black.png'
        lines.append(f"file '{os.path.abspath(f)}'\nduration {1/24:.6f}")
if not os.path.exists('black.png'):
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'lavfi', '-i', 'color=c=black:s=1920x1080', '-frames:v', '1', 'black.png'], check=True)
open('frames.txt', 'w').write('ffconcat version 1.0\n' + '\n'.join(lines) + '\n')
subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'concat', '-safe', '0', '-i', 'frames.txt', '-r', '24', '-c:v', 'libx264', '-preset', 'veryfast',
                '-crf', '17', '-pix_fmt', 'yuv420p', 'body.mp4'], check=True)
AUD = '../audio/sumbi_mix.wav'
if rng:
    a0 = starts[sel[0][0]]; dur = sum(d for _, d in sel)
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-i', 'body.mp4', '-ss', str(a0), '-t', str(dur), '-i', AUD, '-map', '0:v', '-map', '1:a',
                    '-c:v', 'copy', '-c:a', 'aac', '-b:a', '256k', '-shortest', out], check=True)
else:
    for src, dst in (('../design/title_anim.mp4', 'title.mp4'), ('../design/credit_typing_d2.mp4', 'credit.mp4')):
        subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-i', src, '-an', '-r', '24', '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '17',
                        '-pix_fmt', 'yuv420p', dst], check=True)
    open('parts.txt', 'w').write("file 'body.mp4'\nfile 'title.mp4'\nfile 'credit.mp4'\n")
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'concat', '-safe', '0', '-i', 'parts.txt', '-c', 'copy', 'picture.mp4'], check=True)
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-i', 'picture.mp4', '-i', AUD, '-map', '0:v', '-map', '1:a', '-c:v', 'copy', '-c:a', 'aac',
                    '-b:a', '256k', '-shortest', out], check=True)
print('ok', out)
