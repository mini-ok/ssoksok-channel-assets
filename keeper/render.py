#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""빛지기 (THE KEEPER) -- driver: dissolves, title, fades, parallel chunked encode."""
import sys, os, time, subprocess
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from engine import W, H, OH, BAR, FPS, F32, develop, finalize, sm
from shots import shot_at, c13, c14

DUR = 60.0
NF = int(DUR * FPS)
FONT = '/usr/share/fonts/opentype/noto/NotoSerifCJK-SemiBold.ttc'
FONT_L = '/usr/share/fonts/opentype/noto/NotoSerifCJK-Light.ttc'

def text_mask(s, font_path, size, track, index=1):
    font = ImageFont.truetype(font_path, size, index=index)
    widths = [font.getlength(ch) for ch in s]
    total = int(sum(widths) + track * (len(s) - 1)) + size
    im = Image.new('L', (total, int(size * 1.6)), 0)
    d = ImageDraw.Draw(im)
    x = size * 0.5
    for ch, w in zip(s, widths):
        d.text((x, size * 0.15), ch, font=font, fill=255)
        x += w + track
    return np.asarray(im, F32) / 255.0

TITLE = text_mask('빛지기', FONT, 116, 34)
SUB = text_mask('THE KEEPER', FONT_L, 26, 16)
CRED = text_mask('GoXoN × Claude  ·  every frame is code', FONT_L, 19, 4)

def put_text(img, mask, cx, cy, col, alpha, glow=0.6):
    import cv2
    if alpha <= 0.003:
        return
    h, w = mask.shape
    x0, y0 = int(cx - w / 2), int(cy - h / 2)
    x1, y1 = x0 + w, y0 + h
    xs0, ys0 = max(x0, 0), max(y0, 0)
    xs1, ys1 = min(x1, W), min(y1, H)
    m = mask[ys0 - y0:ys1 - y0, xs0 - x0:xs1 - x0] * F32(alpha)
    sh = cv2.GaussianBlur(m, (0, 0), 6)[..., None] * F32(0.45)
    g = cv2.GaussianBlur(m, (0, 0), 14)[..., None] * F32(glow)
    sub = img[ys0:ys1, xs0:xs1]
    sub = sub * (1 - sh)
    a = m[..., None]
    img[ys0:ys1, xs0:xs1] = sub * (1 - a) + a * np.array(col, F32) + g * np.array((1.0, 0.75, 0.5), F32) * 0.25

def overlays(img, t):
    if t >= 57.7:
        a = sm(57.8, 58.7, t)
        put_text(img, TITLE, 760, 190, (1.0, 0.97, 0.92), a, glow=0.5)
        put_text(img, SUB, 760, 278, (1.0, 0.93, 0.86), sm(57.9, 58.8, t) * 0.9, glow=0.2)
        put_text(img, CRED, 960, 770, (0.98, 0.90, 0.86), sm(58.4, 59.1, t) * 0.75, glow=0.1)

def render_frame(i):
    t = i / FPS
    if 44.3 <= t < 45.3:
        a = sm(44.3, 45.3, t)
        img = develop(c13(t)) * F32(1 - a) + develop(c14(t)) * F32(a)
    else:
        img = develop(shot_at(t)(t))
    overlays(img, t)
    fade = sm(0, 0.6, t) * (1 - sm(59.2, 60.0, t))
    return finalize(img, i, fade)

def render_chunk(args):
    i0, i1, path = args
    cmd = ['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{OH}',
           '-r', str(FPS), '-i', '-', '-c:v', 'libx264', '-preset', 'medium', '-crf', '16', '-pix_fmt', 'yuv420p',
           '-colorspace', 'bt709', '-color_primaries', 'bt709', '-color_trc', 'bt709', '-g', '60', path]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    t0 = time.time()
    for i in range(i0, i1):
        p.stdin.write(render_frame(i).tobytes())
    p.stdin.close()
    p.wait()
    return i0, i1, time.time() - t0

if __name__ == '__main__':
    mode = sys.argv[1]
    if mode == 'test':
        os.makedirs('test', exist_ok=True)
        for tt in sys.argv[2:]:
            ts = float(tt)
            i = min(int(round(ts * FPS)), NF - 1)
            t0 = time.time()
            fr = render_frame(i)
            Image.fromarray(fr).resize((960, 540), Image.LANCZOS).save(f'test/k_{ts:05.2f}.png')
            print(f't={ts:.2f}  {time.time() - t0:.2f}s', flush=True)
    elif mode == 'full':
        import multiprocessing as mp
        os.makedirs('chunks', exist_ok=True)
        cs = 120
        jobs = [(a, min(a + cs, NF), f'chunks/c{a // cs:02d}.mp4') for a in range(0, NF, cs)]
        t0 = time.time()
        with mp.Pool(2) as pool:
            for r in pool.imap_unordered(render_chunk, jobs):
                print(f'chunk {r[0]}-{r[1]} {r[2]:.0f}s (total {time.time() - t0:.0f}s)', flush=True)
        with open('chunks/list.txt', 'w') as f:
            for j in jobs:
                f.write(f"file '{os.path.basename(j[2])}'\n")
        print('ALL DONE', flush=True)
