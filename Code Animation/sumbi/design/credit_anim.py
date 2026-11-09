# -*- coding: utf-8 -*-
"""Ending credit: two lines typed like a code editor (blinking cursor), then the 虛像工房 白文 seal is stamped beside them."""
import math, os, subprocess, numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont
from scipy.io import wavfile
from design import load, seal_baimun, on_paper, scale_rgba, put_rgba, W, OH, H, BAR

FPS = 24
DUR = 7.0
LINES = ['Created & Coded by L.S.M.', '허상공방 虛像工房 Project']
FONTSET = os.environ.get('CFONT', 'd2')
if FONTSET == 'jb':        # JetBrains Mono + Noto Sans Mono CJK KR
    SIZE = 30
    JB = ImageFont.truetype('fonts/jbmono-latin-400-normal.ttf', SIZE)
    CJK = ImageFont.truetype('/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc', SIZE, index=6)
elif FONTSET == 'd2':      # D2Coding (Naver coding font: Latin + Hangul + Hanja in one)
    SIZE = 29
    JB = CJK = ImageFont.truetype('fonts/d2coding-full.ttf', SIZE)
else:                      # Galmuri Mono 11 (pixel), size = 3 x 11 for crisp pixels
    SIZE = 33
    JB = CJK = ImageFont.truetype('fonts/GalmuriMono11.ttf', SIZE)
CELL = JB.getlength('M')
Y1, GAP, MARGIN, SGAP = H - 205, 50, 110, 30
COL = (246, 240, 226)

def is_wide(ch):
    return ord(ch) > 0x2E7F

def char_xs(line):
    xs, x = [], 0.0
    for ch in line:
        xs.append(x); x += (CJK.getlength(ch) + 1) if is_wide(ch) else CELL
    return xs, x

# typing schedule (seconds when each char appears)
rng = np.random.default_rng(4)
times = []
t = 0.45
for li, line in enumerate(LINES):
    row = []
    for ch in line:
        row.append(t)
        t += (0.055 if ch != ' ' else 0.09) + rng.uniform(0, 0.05)
    times.append(row)
    t += 0.38
TYPE_END = t - 0.38
LSM_END = times[0][-1]
STAMP = TYPE_END + 0.30
FADE0 = 6.2

base = load('plate.png')
yy = np.linspace(0, 1, H, dtype=np.float32)[:, None]
xx = np.linspace(0, 1, W, dtype=np.float32)[None, :]
shade = np.clip(1 - 0.62 * np.clip((yy - 0.45) / 0.55, 0, 1) * np.clip(xx + 0.25, 0, 1), 0, 1)
base = base * shade[..., None]

maxw = max(char_xs(l)[1] for l in LINES)
block_h = GAP + SIZE + 14
seal = on_paper(seal_baimun(seed=3), 3)
seal = scale_rgba(seal, block_h / seal.shape[0])
SX = int(W - MARGIN - seal.shape[1]); SY = int(Y1 - 8)
X0 = SX - SGAP - maxw                      # text block sits left of the seal, longest line ending at the gap

def text_layer(tt):
    im = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    cur = None
    for li, line in enumerate(LINES):
        xs, _ = char_xs(line)
        y = Y1 + li * GAP
        shown = 0
        for i, ch in enumerate(line):
            if tt >= times[li][i]:
                f = CJK if is_wide(ch) else JB
                dy = -4 if is_wide(ch) else 0
                d.text((X0 + xs[i] + 2, y + 2 + dy), ch, font=f, fill=(4, 12, 20, 150))
                d.text((X0 + xs[i], y + dy), ch, font=f, fill=COL + (255,))
                shown = i + 1
        if shown > 0 or li == 0:
            if shown < len(line) or li == len(LINES) - 1 or tt < times[li + 1][0]:
                cx = X0 + (xs[shown] if shown < len(line) else char_xs(line)[1])
                if li == 0 or shown > 0 or tt >= times[li][0] - 0.38:
                    cur = (cx, y)
    if cur is not None:
        typing = tt < TYPE_END + 0.1
        on = typing or (int((tt - TYPE_END) * 2) % 2 == 0)
        if on:
            d.rectangle((cur[0] + 2, cur[1] + 4, cur[0] + CELL - 1, cur[1] + SIZE + 6), fill=COL + (215,))
    a = np.array(im, np.float32) / 255
    return a

def frame(i):
    tt = i / FPS
    cv = base.copy()
    lay = text_layer(tt)
    # faint phosphor glow under the glyphs
    glow = cv2.GaussianBlur(lay[..., 3], (0, 0), 6)[..., None]
    cv = cv + glow * np.array((0.10, 0.10, 0.08), np.float32)
    a = lay[..., 3:4]
    cv = cv * (1 - a) + lay[..., :3] * a
    t0s = times[0][0] + 0.4
    al = min(1.0, max(0.0, (tt - t0s) / (LSM_END - t0s)))   # fully in when 'L.S.M.' is typed
    al = al * al * (3 - 2 * al)
    if al > 0:
        s2 = seal.copy(); s2[..., 3] *= al
        put_rgba(cv, s2, SX, SY)
    fade = min(1.0, max(0.0, (DUR - tt) / (DUR - FADE0)))
    cv = np.clip(cv * fade, 0, 1)
    out = np.zeros((OH, W, 3), np.uint8)
    out[BAR:BAR + H] = (cv * 255).astype(np.uint8)
    return out

def audio():
    sr = 44100; n = int(DUR * sr); x = np.zeros(n)
    r = np.random.default_rng(2)
    from scipy.signal import butter, sosfilt
    for row in times:
        for t0 in row:
            d = 0.035; m = int(d * sr)
            c = r.normal(0, 1, m) * np.exp(-np.arange(m) / (sr * 0.006))
            f = r.uniform(1800, 3200)
            c = sosfilt(butter(2, [f * 0.6, f * 1.4], btype='band', fs=sr, output='sos'), c)
            i = int(t0 * sr); x[i:i + m] += c * 0.12
    m = int(0.25 * sr); tt = np.arange(m) / sr
    thud = np.sin(2 * np.pi * (60 + 90 * np.exp(-tt / 0.03)) * tt) * np.exp(-tt / 0.07) * 0.5
    thud += sosfilt(butter(2, 900, fs=sr, output='sos'), r.normal(0, 1, m)) * np.exp(-tt / 0.02) * 0.2
    fade = np.clip((DUR - np.arange(n) / sr) / (DUR - FADE0), 0, 1)
    x *= fade
    wavfile.write('credit.wav', sr, (np.stack([x, x], -1) / max(1e-6, np.abs(x).max()) * 0.6 * 32767).astype(np.int16))

if __name__ == '__main__':
    audio()
    nf = int(DUR * FPS)
    p = subprocess.Popen(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{OH}', '-r', str(FPS),
                          '-i', '-', '-i', 'credit.wav', '-c:v', 'libx264', '-crf', '18', '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-shortest',
                          f'credit_typing_{FONTSET}.mp4'], stdin=subprocess.PIPE)
    for i in range(nf):
        f = frame(i)
        p.stdin.write(f.tobytes())
        if i in (int(2.5 * FPS), int(5.4 * FPS)):
            Image.fromarray(f).save(f'credit_{FONTSET}_{i:03d}.png')
    p.stdin.close(); p.wait()
    print('ok', TYPE_END, STAMP)
