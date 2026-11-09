#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""홀씨 (HOLSSI) -- driver: cut table, parallel chunked encode."""
import sys, os, time, subprocess
import numpy as np
from PIL import Image
import eng
from shots_d import *

FPS = 24
DUR = 90.0
NF = int(DUR * FPS)
CUTS = [(0, 7, c01), (7, 12, c02), (12, 17, c03), (17, 20, c04), (20, 26, c05), (26, 31, c06), (31, 36, c07),
        (36, 40, c08), (40, 48, c09), (48, 52, c10), (52, 56, c11), (56, 60, c12), (60, 64, c13), (64, 76, c14),
        (76, 80, c15), (80, 83, c16), (83, 86, c17), (86, 90.1, c18)]
_cur = [None]

def shot(t):
    for a, b, f in CUTS:
        if a <= t < b:
            return f
    return CUTS[-1][2]

def render_frame(i):
    t = i / FPS
    f = shot(t)
    if _cur[0] is not f:
        eng.Static._cache.clear(); eng.StaticArr._cache.clear()
        _cur[0] = f
    cp = f(t, i)
    cp.fade *= sm(0, 1.2, t) * (1 - sm(89.0, 90.0, t))
    return cp.finish(i)

def render_chunk(args):
    i0, i1, path = args
    cmd = ['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{eng.W}x{eng.OH}',
           '-r', str(FPS), '-i', '-', '-c:v', 'libx264', '-preset', 'medium', '-crf', '16', '-pix_fmt', 'yuv420p',
           '-colorspace', 'bt709', '-color_primaries', 'bt709', '-color_trc', 'bt709', '-g', '48', path]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    t0 = time.time()
    for i in range(i0, i1):
        p.stdin.write(render_frame(i).tobytes())
    p.stdin.close(); p.wait()
    return i0, i1, time.time() - t0

if __name__ == '__main__':
    if sys.argv[1] == 'test':
        for a in sys.argv[2:]:
            t = float(a); i = min(int(round(t * FPS)), NF - 1)
            Image.fromarray(render_frame(i)).save(f'test/r_{t:05.2f}.png')
            print(t, flush=True)
    else:
        import multiprocessing as mp
        os.makedirs('chunks', exist_ok=True)
        cs = 96
        jobs = [(a, min(a + cs, NF), f'chunks/c{a // cs:02d}.mp4') for a in range(0, NF, cs)]
        t0 = time.time()
        with mp.Pool(2, maxtasksperchild=1) as pool:
            for r in pool.imap_unordered(render_chunk, jobs):
                print(f'chunk {r[0]}-{r[1]} {r[2]:.0f}s (total {time.time()-t0:.0f}s)', flush=True)
        with open('chunks/list.txt', 'w') as f:
            for j in jobs:
                f.write(f"file '{os.path.basename(j[2])}'\n")
        print('ALL DONE', flush=True)
