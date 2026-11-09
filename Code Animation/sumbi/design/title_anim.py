# -*- coding: utf-8 -*-
"""C34 title: '숨비' is brushed in left to right, then the breath line leaves the last letter like a 숨비소리 and ends in a small orange 테왁."""
import math, subprocess, numpy as np, cv2
from design import load, text_mask, dry_brush, put, fbm, W, H, OH, BAR
FPS, DUR = 24, 4.0
cv0 = load('plate.png')
m = dry_brush(text_mask('숨비', 330, fam='east-sea-dokdo'), 7, amt=0.35)
h, w = m.shape; x, y = 210, 70
halo = cv2.GaussianBlur(m, (0, 0), 10)
L = np.zeros((H, W), np.float32); x0, y0 = x + w + 10, y + int(h * 0.55); pts = []
for i in range(160):
    t = i / 159; pts.append((int(x0 + t * 760), int(y0 - 60 * math.sin(t * math.pi * 1.2) * (1 - t * 0.5) + 30 * t)))
order = np.zeros((H, W), np.float32)             # stroke progress per pixel for the breath line
for i in range(len(pts) - 1):
    wd = max(1, int(14 * (1 - i / len(pts)) ** 1.4))
    cv2.line(L, pts[i], pts[i + 1], 1.0, wd, lineType=cv2.LINE_AA); cv2.line(order, pts[i], pts[i + 1], (i + 1) / len(pts), wd + 2)
L = dry_brush(L, 9, amt=0.6)
edge = fbm(h, w, 40, 3) if False else (np.random.default_rng(5).random((h, w)).astype(np.float32))
edge = cv2.GaussianBlur(edge, (0, 0), 6); edge = (edge - edge.min()) / (edge.max() - edge.min())
xs = np.linspace(0, 1, w, dtype=np.float32)[None, :] + 0.08 * (edge - 0.5)
def ss(a, b, t): u = min(1, max(0, (t - a) / (b - a))); return u * u * (3 - 2 * u)
def frame(i):
    t = math.floor(i / 2) * 2 / FPS                 # on twos
    cv = cv0.copy()
    p = ss(0.25, 1.55, t) * 1.12
    reveal = np.clip((p - xs) / 0.06, 0, 1)
    put(cv, halo * reveal, x + 6, y + 10, (0.98, 0.96, 0.90), 0.55)
    put(cv, m * reveal, x, y, (0.10, 0.16, 0.30))
    q = ss(1.6, 2.9, t)
    put(cv, L * ((order > 0) & (order <= q + 1e-3)).astype(np.float32), 0, 0, (0.10, 0.16, 0.30), 0.9)
    if t >= 2.95:
        ex, ey = pts[-1]; pop = min(1.0, (t - 2.95) / 0.17); r = int(13 * (0.6 + 0.4 * pop) * (1 + 0.15 * math.sin((t - 2.95) * 9) * (1 - pop)))
        cv2.circle(cv, (ex + 22, ey + int(2 * math.sin(t * 4))), r, (0.96, 0.46, 0.12), -1, lineType=cv2.LINE_AA)
    out = np.zeros((OH, W, 3), np.uint8); out[BAR:BAR + H] = (np.clip(cv, 0, 1) * 255).astype(np.uint8)
    return out
p = subprocess.Popen(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{OH}', '-r', str(FPS), '-i', '-',
                      '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '18', '-pix_fmt', 'yuv420p', 'title_anim.mp4'], stdin=subprocess.PIPE)
for i in range(int(DUR * FPS)):
    f = frame(i); p.stdin.write(f.tobytes())
    if i == 90: cv2.imwrite('title_anim_090.png', f[..., ::-1])
p.stdin.close(); p.wait(); print('ok')
