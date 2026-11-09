# -*- coding: utf-8 -*-
"""Underwater cel finish: cel3d ink + heavy character silhouette, then painted god rays from the surface,
a cool water grade, drifting specks (marine snow) on twos, paper, cel_finish, film_post."""
import sys, os, math, numpy as np, cv2
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cel3d import ink, rd, noise_field, WOB, PAPER, cel_finish, film_post, H, W, F32

def god_rays(t, strength=0.30):
    tq = math.floor(t * 12) / 12
    img = np.zeros((H, W), F32)
    ox, oy = W * 0.62, -700                      # the sun sits above the frame; beams fan out downward
    rng = np.random.default_rng(21)
    for k in range(9):
        a = -0.55 + k * 0.13 + 0.025 * math.sin(tq * 0.9 + k * 1.7)
        w = rng.uniform(0.012, 0.035)
        pts = []
        for s in (a - w, a + w):
            pts.append((ox + math.tan(s) * (H + 700 + 60) , H + 60))
        poly = np.array([[ox + math.tan(a - w * 0.3) * 700, 0], [ox + math.tan(a + w * 0.3) * 700, 0], pts[1], pts[0]], np.int32)
        cv2.fillPoly(img, [poly], rng.uniform(0.5, 1.0) * (0.75 + 0.25 * math.sin(tq * 1.3 + k * 2.1)))
    img = cv2.GaussianBlur(img, (0, 0), 18)
    streak = cv2.blur(np.random.default_rng(4).random((H, W)).astype(F32), (2, 45))
    img *= 0.7 + 0.6 * streak
    fall = np.linspace(1.0, 0.0, H, dtype=F32)[:, None] ** 1.3
    return img * fall * strength

SPECK = np.random.default_rng(8).random((260, 4)).astype(F32)   # x, y, size, depth
def specks(t):
    tq = math.floor(t * 12) / 12
    img = np.zeros((H, W), F32)
    for x, y, s, d in SPECK:
        px = (x * W + 25 * math.sin(tq * 0.7 + y * 20) - tq * 18 * d) % W
        py = (y * H - tq * 14 * (0.3 + d)) % H
        r = 0.8 + 2.2 * s * d
        cv2.circle(img, (int(px), int(py)), int(round(r)), float(0.35 + 0.5 * d), -1, lineType=cv2.LINE_AA)
    return cv2.GaussianBlur(img, (0, 0), 0.8)

TW = np.random.default_rng(31).random((70, 4)).astype(F32)
def twinkles(t):
    # 반짝이는 플랑크톤: 십자 별 모양이 투스마다 켜졌다 꺼짐 (빛줄기 근처에서 더 자주)
    tq = math.floor(t * 12) / 12
    img = np.zeros((H, W), F32)
    for k, (x, y, s, ph) in enumerate(TW):
        b = max(0.0, math.sin(tq * (2.0 + 3 * s) + ph * 6.28)) ** 3
        if b < 0.15: continue
        px = int((x * W + 12 * math.sin(tq * 0.5 + k) - tq * 10) % W); py = int((y * H * 0.85 - tq * 9 * (0.4 + s)) % H)
        L = int(4 + 9 * s * b)
        cv2.line(img, (px - L, py), (px + L, py), float(b), 1, cv2.LINE_AA)
        cv2.line(img, (px, py - L), (px, py + L), float(b), 1, cv2.LINE_AA)
        cv2.circle(img, (px, py), 2, float(b), -1, cv2.LINE_AA)
    return cv2.GaussianBlur(img, (0, 0), 0.7) + cv2.GaussianBlur(img, (0, 0), 5) * 0.8

def grade(img):
    # cool the water: lift shadows toward deep teal, keep warm accents (Kuruk, skin) but slightly muted
    lum = (img * np.array((0.3, 0.59, 0.11), F32)).sum(-1, keepdims=True)
    teal = np.array((0.05, 0.25, 0.32), F32)
    img = img * 0.92 + teal * 0.10 * (1 - lum)
    return img * np.array((0.96, 1.0, 1.02), F32)

def finish(d, i):
    t = i / 24
    col = rd(f'{d}/color_{i:04d}.png'); idp = rd(f'{d}/id_{i:04d}.png')
    nrm = rd(f'{d}/normal_{i:04d}.png'); dep = rd(f'{d}/depth_{i:04d}.png')
    line, lc = ink(col, idp, nrm, dep, t)
    # lines dissolve into the water with the same exp2 fog as the render (depth pass = 1 - dist/10 m)
    near = cv2.dilate(dep[..., 0], np.ones((5, 5), np.uint8))
    dist = (1 - near) * 10
    fogk = np.exp(-(0.16 * dist) ** 2)
    line = line * (0.85 * fogk)[..., None]
    cp = f'{d}/char_{i:04d}.png'
    if os.path.exists(cp):
        cm = (rd(cp)[..., 0] > 0.5).astype(np.uint8)
        edge = cv2.morphologyEx(cm, cv2.MORPH_GRADIENT, np.ones((3, 3), np.uint8)).astype(F32)
        mx, my = np.meshgrid(np.arange(W, dtype=F32), np.arange(H, dtype=F32))
        tq = int(t * 12)
        edge = cv2.remap(edge, mx + WOB[0] * 1.2 + noise_field(H, W, 40, 500 + tq) * 0.35,
                         my + WOB[1] * 1.2 + noise_field(H, W, 40, 600 + tq) * 0.35, cv2.INTER_LINEAR)
        dt = cv2.distanceTransform((edge < 0.5).astype(np.uint8), cv2.DIST_L2, 3)
        sil = np.clip(2.4 * (1 + 0.2 * noise_field(H, W, 60, 9)) - dt + 0.5, 0, 1)[..., None]
        line = np.maximum(line, sil)
        lc = np.where(sil > line * 0.99, lc * 0.8 + np.array((0.04, 0.10, 0.16), F32) * 0.2, lc)
    img = col * (1 - line) + lc * line
    img = grade(img)
    gr = god_rays(t)[..., None]
    img = img + gr * np.array((0.80, 1.0, 0.92), F32) * (1 - 0.6 * line)
    sp = specks(t)[..., None]
    img = img * (1 - sp * 0.6) + np.array((0.85, 0.97, 0.95), F32) * sp * 0.6
    tw = np.clip(twinkles(t), 0, 1)[..., None]
    img = img * (1 - tw * 0.7) + np.array((1.0, 0.97, 0.82), F32) * tw * 0.9
    img = np.clip(img * PAPER[..., None], 0, 1)
    rgba = np.concatenate([img, np.ones((H, W, 1), F32)], -1)
    img = cel_finish(rgba, t)[..., :3]
    out = film_post(np.clip(img, 0, 1), t)
    full = np.zeros((1080, W, 3), np.uint8)
    full[20:20 + H] = (np.clip(out, 0, 1) * 255).astype(np.uint8)
    return full

if __name__ == '__main__':
    from PIL import Image
    d = sys.argv[1]; out = sys.argv[2]; os.makedirs(out, exist_ok=True)
    idx = sorted(int(f[6:10]) for f in os.listdir(d) if f.startswith('color_'))
    sel = idx if len(sys.argv) < 4 else [int(x) for x in sys.argv[3].split(',')]
    for i in sel:
        f = finish(d, i)
        Image.fromarray(f).save(f'{out}/f_{i:04d}.png')
        if len(sys.argv) < 4:          # hold each drawing for two frames
            Image.fromarray(f).save(f'{out}/f_{i + 1:04d}.png')
    print('done', len(sel))
