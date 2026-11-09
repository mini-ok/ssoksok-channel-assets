# -*- coding: utf-8 -*-
"""Cel finish for three.js renders: hand ink lines from id/normal/depth passes, coloured held lines,
line boil on twos, painted light shafts, cel_finish + film_post (from the scarecrow engine)."""
import sys, os, math, numpy as np, cv2
sys.path.insert(0, '/home/claude/scarecrow')
from cel import cel_finish, film_post, INK_C, INK_W
from painter import paint

F32 = np.float32
H, W = 1040, 1920

def rd(p):
    return cv2.imread(p, cv2.IMREAD_COLOR)[..., ::-1].astype(F32) / 255

def noise_field(h, w, scale, seed):
    r = np.random.default_rng(seed)
    n = r.random(((h // scale) + 3, (w // scale) + 3)).astype(F32)
    return cv2.resize(n, (w + 3 * scale, h + 3 * scale), interpolation=cv2.INTER_CUBIC)[:h, :w] * 2 - 1

# low-frequency wobble field is fixed (the drawing's shape); a tiny per-drawing jitter gives line boil
WOB = (noise_field(H, W, 140, 11), noise_field(H, W, 140, 12))

def edges(col, idp, nrm, dep):
    idk = (idp * 255).astype(np.int32)
    key = idk[..., 0] * 65536 + idk[..., 1] * 256 + idk[..., 2]
    e = np.zeros((H, W), bool)
    for dy, dx in ((0, 1), (1, 0), (1, 1)):
        a = key[:H - dy, :W - dx]; b = key[dy:, dx:]
        d = a != b
        e[:H - dy, :W - dx] |= d
    # creases: normal discontinuity inside one object
    n = nrm * 2 - 1
    dot = (n[:, :-1] * n[:, 1:]).sum(-1)
    e[:, :-1] |= dot < 0.15
    dot = (n[:-1] * n[1:]).sum(-1)
    e[:-1] |= dot < 0.15
    # depth jumps
    d = dep[..., 0]
    gx = np.abs(cv2.Sobel(d, cv2.CV_32F, 1, 0, ksize=3)); gy = np.abs(cv2.Sobel(d, cv2.CV_32F, 0, 1, ksize=3))
    e |= (gx + gy) > 0.06
    return e.astype(F32)

def ink(col, idp, nrm, dep, t, light=(-0.55, -0.83)):
    e = edges(col, idp, nrm, dep)
    tq = int(t * 12)
    jit = (noise_field(H, W, 40, 100 + tq) * 0.35, noise_field(H, W, 40, 200 + tq) * 0.35)
    mx, my = np.meshgrid(np.arange(W, dtype=F32), np.arange(H, dtype=F32))
    e = cv2.remap(e, mx + WOB[0] * 1.2 + jit[0], my + WOB[1] * 1.2 + jit[1], cv2.INTER_LINEAR)
    # width: near = thick, far = thin (depth pass: near is bright), pressure noise along the stroke
    near = np.clip(dep[..., 0] * 1.6 - 0.2, 0, 1)
    press = 1 + 0.25 * noise_field(H, W, 60, 7)
    wpx = (1.0 + 1.4 * near) * press
    dt = cv2.distanceTransform((e < 0.5).astype(np.uint8), cv2.DIST_L2, 3)
    line = np.clip(wpx - dt + 0.5, 0, 1)
    line *= 0.6 + 0.4 * near ** 0.5                  # far lines fade into the haze
    # coloured held line: darker local colour, cool on the shadow side, warm on the lit side
    lum = (col * np.array((0.3, 0.59, 0.11), F32)).sum(-1, keepdims=True)
    base = cv2.dilate(col, np.ones((3, 3), np.uint8))
    shade_side = np.clip(0.55 - lum, 0, 1) * 2
    lc = base * 0.28
    lc = lc * (1 - 0.5 * shade_side) + np.array(INK_C, F32) * 0.5 * shade_side
    lc = lc * (1 - 0.25 * (1 - shade_side)) + np.array(INK_W, F32) * 0.25 * (1 - shade_side) * 0.6
    return line[..., None], lc

def shafts(t, strength=0.22):
    """painted light shafts: soft diagonal beams with a dry-brush edge, slow parallax on twos"""
    tq = math.floor(t * 12) / 12
    img = np.zeros((H, W), F32)
    for k, (x0, w0) in enumerate(((380, 90), (860, 140), (1240, 70), (1600, 120))):
        x = x0 - tq * 40 * (0.6 + 0.2 * k)
        pts = np.array([[x, -40], [x + w0, -40], [x + w0 + 520, H + 40], [x + 260, H + 40]], np.int32)
        cv2.fillPoly(img, [pts], 1.0)
    img = cv2.GaussianBlur(img, (0, 0), 22)
    streak = cv2.blur(np.random.default_rng(3).random((H, W)).astype(F32), (3, 61))
    img *= 0.75 + 0.5 * streak
    fall = np.linspace(1.0, 0.35, H, dtype=F32)[:, None]
    return img * fall * strength

def paper(h, w):
    r = np.random.default_rng(5)
    fib = cv2.blur(r.random((h, w)).astype(F32), (31, 2))
    return 1 + (fib - 0.5) * 0.05 + noise_field(h, w, 200, 9) * 0.02

PAPER = paper(H, W)

def finish(d, i, painterly=False):
    t = i / 24
    col = rd(f'{d}/color_{i:04d}.png'); idp = rd(f'{d}/id_{i:04d}.png')
    nrm = rd(f'{d}/normal_{i:04d}.png'); dep = rd(f'{d}/depth_{i:04d}.png')
    if painterly:
        col = paint(col, radii=(12, 6, 3), thresh=(0, 0.06, 0.10), maxlen=(6, 5, 3), seed=3, detail=0.5,
                    lenmul=np.ones((H, W), F32) * 1.4)
    line, lc = ink(col, idp, nrm, dep, t)
    cp = f'{d}/char_{i:04d}.png'
    if os.path.exists(cp):
        # characters get a heavier outer contour (the silhouette is the strongest line on a cel)
        cm = (rd(cp)[..., 0] > 0.5).astype(np.uint8)
        edge = cv2.morphologyEx(cm, cv2.MORPH_GRADIENT, np.ones((3, 3), np.uint8)).astype(F32)
        mx, my = np.meshgrid(np.arange(W, dtype=F32), np.arange(H, dtype=F32))
        tq = int(t * 12)
        edge = cv2.remap(edge, mx + WOB[0] * 1.2 + noise_field(H, W, 40, 500 + tq) * 0.35,
                         my + WOB[1] * 1.2 + noise_field(H, W, 40, 600 + tq) * 0.35, cv2.INTER_LINEAR)
        dt = cv2.distanceTransform((edge < 0.5).astype(np.uint8), cv2.DIST_L2, 3)
        sil = np.clip(2.6 * (1 + 0.2 * noise_field(H, W, 60, 9)) - dt + 0.5, 0, 1)[..., None]
        line = np.maximum(line, sil)
    img = col * (1 - line) + lc * line
    sh = shafts(t)[..., None]
    img = img + sh * np.array((1.0, 0.95, 0.78), F32) * (1 - line)
    img = np.clip(img * PAPER[..., None], 0, 1)
    rgba = np.concatenate([img, np.ones((H, W, 1), F32)], -1)
    img = cel_finish(rgba, t)[..., :3] if cel_finish is not None else img
    out = film_post(np.clip(img, 0, 1), t)
    full = np.zeros((1080, W, 3), np.uint8)
    full[20:20 + H] = (np.clip(out, 0, 1) * 255).astype(np.uint8)
    return full

if __name__ == '__main__':
    d = sys.argv[1]; i = int(sys.argv[2]); mode = sys.argv[3] if len(sys.argv) > 3 else 'cel'
    from PIL import Image
    Image.fromarray(finish(d, i, painterly=(mode == 'paint'))).save(f'test_{mode}_{i:04d}.png')
    print('ok')
