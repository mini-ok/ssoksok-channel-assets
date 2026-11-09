# -*- coding: utf-8 -*-
"""〈숨비〉 cel finish for every cut. Reads <passdir>/meta.json (env, mode, fog, DR) and picks a look:
coast/dawn · coast/day · coast/storm · forest · under. Ink from id/normal/depth, heavy character silhouette,
lines dissolve with the same fog as the render, per-look light (dawn glow, forest shafts, underwater rays),
paper, cel_finish, film_post. Writes both frames of each drawing (on twos).
usage: python3 finish.py passdir outdir [workers]"""
import sys, os, json, math, numpy as np, cv2
from multiprocessing import Pool
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cel3d import ink, rd, noise_field, WOB, PAPER, cel_finish, film_post, H, W, F32, shafts
import uw_finish as UW

def fogk_of(meta, dep):
    near = cv2.dilate(dep[..., 0], np.ones((5, 5), np.uint8))
    dist = (1 - near) * meta.get('DR', 30)
    fog = meta.get('fog', {})
    if fog.get('type') == 'lin':
        return 1 - np.clip((dist - fog['near'] * 0.5) / (fog['far'] * 0.6 - fog['near'] * 0.5), 0, 1) ** 0.7
    if fog.get('type') == 'exp2':
        return np.exp(-(fog['density'] * dist) ** 2)
    return np.ones_like(dist)

def silhouette(cp, t, width=2.5):
    cm = (rd(cp)[..., 0] > 0.5).astype(np.uint8)
    edge = cv2.morphologyEx(cm, cv2.MORPH_GRADIENT, np.ones((3, 3), np.uint8)).astype(F32)
    mx, my = np.meshgrid(np.arange(W, dtype=F32), np.arange(H, dtype=F32))
    tq = int(t * 12)
    edge = cv2.remap(edge, mx + WOB[0] * 1.2 + noise_field(H, W, 40, 500 + tq) * 0.35,
                     my + WOB[1] * 1.2 + noise_field(H, W, 40, 600 + tq) * 0.35, cv2.INTER_LINEAR)
    dt = cv2.distanceTransform((edge < 0.5).astype(np.uint8), cv2.DIST_L2, 3)
    return np.clip(width * (1 + 0.2 * noise_field(H, W, 60, 9)) - dt + 0.5, 0, 1)[..., None], cm

def glow_from(img, thr=0.78, sigma=18, k=0.22, tint=(1.0, 0.75, 0.5)):
    lum = (img * np.array((0.3, 0.59, 0.11), F32)).sum(-1)
    m = np.clip((lum - thr) / (1 - thr), 0, 1)
    return cv2.GaussianBlur(m, (0, 0), sigma)[..., None] * np.array(tint, F32) * k

def dawn_light(t):
    # low sun on the left horizon: a warm wash from the upper left, very soft
    yy, xx = np.mgrid[0:H, 0:W].astype(F32)
    d = np.sqrt(((xx + 300) / W) ** 2 + ((yy - 380) / H) ** 2)
    return np.clip(1.15 - d, 0, 1) ** 2 * 0.10

RAIN = np.random.default_rng(77).random((900, 3)).astype(F32)
def rain(t):
    tq = math.floor(t * 12) / 12
    img = np.zeros((H, W), F32)
    for x, y, s in RAIN:
        px = (x * W + tq * 300) % W; py = (y * H + tq * 2400 * (0.6 + s)) % H
        L = 18 + 30 * s
        cv2.line(img, (int(px), int(py)), (int(px - L * 0.25), int(py - L)), float(0.35 + 0.5 * s), 1, cv2.LINE_AA)
    return img

def finish_one(args):
    d, out, i, meta = args
    t = i / 24
    col = rd(f'{d}/color_{i:04d}.png'); idp = rd(f'{d}/id_{i:04d}.png')
    nrm = rd(f'{d}/normal_{i:04d}.png'); dep = rd(f'{d}/depth_{i:04d}.png')
    env, mode = meta.get('env'), meta.get('mode', '')
    look = meta.get('finish', env)
    line, lc = ink(col, idp, nrm, dep, t)
    line = line * fogk_of(meta, dep)[..., None] * (0.85 if look == 'under' else 1.0)
    cp = f'{d}/char_{i:04d}.png'
    if os.path.exists(cp):
        sil, cm = silhouette(cp, t, 2.4 if look == 'under' else 2.6)
        line = np.maximum(line, sil)
    img = col * (1 - line) + lc * line
    if look == 'under':
        img = UW.grade(img)
        img = img + UW.god_rays(t)[..., None] * np.array((0.80, 1.0, 0.92), F32) * (1 - 0.6 * line)
        sp = UW.specks(t)[..., None]; img = img * (1 - sp * 0.6) + np.array((0.85, 0.97, 0.95), F32) * sp * 0.6
        tw = np.clip(UW.twinkles(t), 0, 1)[..., None]; img = img * (1 - tw * 0.7) + np.array((1.0, 0.97, 0.82), F32) * tw * 0.9
    elif look == 'forest':
        cut = os.path.basename(os.path.normpath(d)).lstrip('c')
        k = {'10': 0.06, '11': 0.05, '12': 0.1, '13': 0.1, '16': 0.08, '18': 0.1, '20': 0.12, '24': 0.08, '21': 0.14}.get(cut, 0.22)
        img = img + shafts(t, k)[..., None] * np.array((1.0, 0.95, 0.78), F32) * (1 - line)
    elif look == 'coast':
        if mode == 'dawn':
            img = img + dawn_light(t)[..., None] * np.array((1.0, 0.72, 0.5), F32)
            img = img + glow_from(img, 0.82, 22, 0.25)
            img = img * np.array((1.0, 0.97, 0.95), F32)
        elif mode == 'storm':
            img = img * np.array((0.85, 0.92, 1.05), F32)
            r = rain(t)[..., None]; img = img * (1 - r * 0.35) + np.array((0.7, 0.78, 0.86), F32) * r * 0.35
            flash = meta.get('flash', [])
            for f0 in flash:
                if 0 <= t - f0 < 0.17: img = np.clip(img * 1.6 + 0.12, 0, 1)
        else:
            img = img + glow_from(img, 0.86, 20, 0.12, (1.0, 0.95, 0.85))
    img = np.clip(img * PAPER[..., None], 0, 1)
    rgba = np.concatenate([img, np.ones((H, W, 1), F32)], -1)
    img = cel_finish(rgba, t)[..., :3]
    o = film_post(np.clip(img, 0, 1), t)
    full = np.zeros((1080, W, 3), np.uint8)
    full[20:20 + H] = (np.clip(o, 0, 1) * 255).astype(np.uint8)
    cv2.imwrite(f'{out}/f_{i:04d}.png', full[..., ::-1]); cv2.imwrite(f'{out}/f_{i + 1:04d}.png', full[..., ::-1])
    return i

if __name__ == '__main__':
    d, out = sys.argv[1], sys.argv[2]; nw = int(sys.argv[3]) if len(sys.argv) > 3 else 2
    os.makedirs(out, exist_ok=True)
    meta = json.load(open(f'{d}/meta.json')) if os.path.exists(f'{d}/meta.json') else {}
    if os.environ.get('FLASH'): meta['flash'] = [float(x) for x in os.environ['FLASH'].split(',')]
    idx = sorted(int(f[6:10]) for f in os.listdir(d) if f.startswith('color_'))
    if os.environ.get('ONLY'): idx = [i for i in idx if i in [int(x) for x in os.environ['ONLY'].split(',')]]
    with Pool(nw) as p:
        for _ in p.imap_unordered(finish_one, [(d, out, i, meta) for i in idx]): pass
    print('finished', len(idx))
