"""〈Gravity〉 v3 — 실사 사진(NASA·Unsplash) + 모션. 샘플 구간 43~86.6초.
사진 목록·출처·라이선스는 photos.md. 화면은 frame(t) 순수함수, 박자는 beats.json의 타격 시각."""
import math, os, bisect
import numpy as np, cv2
import nums as N, mv as M
from styles import sstep, eout, hrand, paste
from vfx import post

PHD = os.environ.get('GV_PHOTOS', '/home/claude/work/gv/ph')
FILES = dict(earth1='nasa/iss061e003491', earth2='nasa/s116e06645', limb='nasa/iss020e047807', lakes='nasa/iss031e123071',
             night='nasa/iss030e062540', cloudA='us/cloudday2', cloudB='us/cloudsun2', cloudC='us/cloudday', cloudD='us/cloudsun',
             crack1='us/crack1', crack2='us/crack2', crack3='us/crack3', mud='us/mudlegs', sand='us/sandprint', path1='us/path1', path2='us/path2')
COOL, WARM = (1.12, 1.0, 0.82), (0.82, 1.0, 1.16)          # BGR 곱
MUDC = np.array((0.11, 0.19, 0.30), np.float32)
_c = {}


def photo(name, W, H):
    k = (name, W, H)
    if k not in _c:
        im = cv2.imread(f'{PHD}/{FILES[name]}.jpg'); h, w = im.shape[:2]; s = 1.5 * max(W / w, H / h)
        im = cv2.resize(im, (int(w * s) + 1, int(h * s) + 1), interpolation=cv2.INTER_AREA if s < 1 else cv2.INTER_CUBIC)
        _c[k] = im.astype(np.float32) / 255
    return _c[k]


def view(name, W, H, zoom=1.0, cx=0.5, cy=0.5, rot=0.0, dx=0.0, dy=0.0):
    src = photo(name, W, H); h, w = src.shape[:2]; s = max(W / w, H / h) * zoom
    c, sn = math.cos(rot) * s, math.sin(rot) * s
    A = np.float32([[c, -sn, 0], [sn, c, 0]])
    A[0, 2] = W / 2 + dx - (A[0, 0] * cx * w + A[0, 1] * cy * h); A[1, 2] = H / 2 + dy - (A[1, 0] * cx * w + A[1, 1] * cy * h)
    return cv2.warpAffine(src, A, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)


def tone(img, sat=1.0, mul=(1, 1, 1), gam=1.0, exp=1.0):
    g = img.mean(2, keepdims=True); img = g + (img - g) * sat
    return np.clip(img * np.asarray(mul, np.float32) * exp, 0, 1) ** gam


def vig(img, a):
    H, W = img.shape[:2]; y, x = np.mgrid[0:H, 0:W].astype(np.float32); r = np.sqrt(((x - W / 2) / (W / 2)) ** 2 + ((y - H / 2) / (H / 2)) ** 2)
    return img * (1 - a * np.clip(r - 0.35, 0, 1.2)[..., None] ** 1.4)


# ---------- 유리 ----------
_sh = {}
def shards(W, H):
    if (W, H) in _sh: return _sh[(W, H)]
    n = 34; cx0, cy0 = W * 0.5, H * 0.45
    pts = np.array([(cx0 + (hrand(i, 4) ** 1.6) * 0.62 * W * math.cos(hrand(i, 3) * 6.283), cy0 + (hrand(i, 4) ** 1.6) * 0.62 * W * math.sin(hrand(i, 3) * 6.283) * 0.75) for i in range(n)], np.float32)
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32); best = np.full((H, W), 1e18, np.float32); lab = np.zeros((H, W), np.int32)
    for i, (px, py) in enumerate(pts):
        d = (xx - px) ** 2 + (yy - py) ** 2; m = d < best; best[m] = d[m]; lab[m] = i
    edge = np.zeros((H, W), bool); edge[:, 1:] |= lab[:, 1:] != lab[:, :-1]; edge[1:, :] |= lab[1:, :] != lab[:-1, :]
    edge = cv2.dilate(edge.astype(np.uint8), np.ones((2, 2), np.uint8)).astype(bool)
    dist = np.hypot(pts[:, 0] - cx0, pts[:, 1] - cy0); order = np.argsort(dist); rank = np.empty(n, int); rank[order] = np.arange(n)
    K = [h for h in N.HITS if 46.0 <= h <= 50.9]; brk = np.array([K[min(len(K) - 1, int(rank[i] * len(K) / n))] for i in range(n)])
    tcr = 43.3 + dist / dist.max() * 2.4
    masks = [(lab == i).astype(np.float32) for i in range(n)]
    cent = [(float(xx[lab == i].mean()), float(yy[lab == i].mean())) if (lab == i).any() else (0, 0) for i in range(n)]
    _sh[(W, H)] = dict(lab=lab, edge=edge, brk=brk, tcr=tcr, masks=masks, cent=cent, n=n); return _sh[(W, H)]


def sc_glass(t, W, H):
    s = shards(W, H); lab = s['lab']; a = t - 43.0
    A = tone(view('earth1', W, H, 1.08 + 0.03 * a / 8.5 + 0.04 * N.pulse(t, 6), 0.5, 0.5), 0.5, COOL, 1.0, 0.9)
    nb = float((s['brk'] <= t).mean())
    B = tone(view('cloudC', W, H, 1.0 + 0.035 * a, 0.5, 0.72), 0.95, (1.02, 1.0, 0.95), 1.0, 0.55 + 0.6 * nb)
    broken = (s['brk'] <= t)[lab]; out = np.where(broken[..., None], B, A)
    show = (s['tcr'] < t)[lab] & s['edge'] & ~broken
    glow = np.clip(1 - (t - s['tcr'][lab]) / 0.2, 0, 1) * show
    out = out + (np.array((1.0, 0.97, 0.9), np.float32) - out) * (show * 0.55 + glow * 0.4)[..., None]
    k = H / 1080
    for i in range(s['n']):
        dt = t - s['brk'][i]
        if dt <= 0 or dt > 1.1: continue
        px, py = s['cent'][i]; ang = (hrand(i, 5) - 0.5) * 2.4 * dt; mx = (hrand(i, 6) - 0.5) * 300 * k * dt; my = 0.5 * 3200 * k * dt ** 2
        if py + my > H * 1.3: continue
        Mx = cv2.getRotationMatrix2D((px, py), -math.degrees(ang), 1.0); Mx[0, 2] += mx; Mx[1, 2] += my
        m = s['masks'][i]; pm = cv2.warpAffine(np.dstack([A * m[..., None], m]), Mx, (W, H), flags=cv2.INTER_LINEAR)
        al = pm[..., 3:4]; sh_ = cv2.warpAffine(m, Mx, (W, H)); out = out * (1 - 0.0 * al) + (pm[..., :3] / np.maximum(al, 1e-3) - out) * al
    return out


# ---------- 낙하 ----------
def sc_fall(t, W, H):
    p = (t - 51.5) / 5.06; z = math.exp(3.0 * p ** 1.7); H_ = H
    img = tone(view('cloudC', W, H, z, 0.5, 0.72 - 0.1 * p), 0.95 - 0.35 * p, (1.0, 1.0, 0.96), 1.0, 1.0 - 0.15 * p)
    c2 = tone(view('cloudA', W, H, z * 1.8, 0.45, 0.6), 0.9, COOL, 1.0, 0.95); al = sstep(0.2, 0.7, p) * 0.45
    img = img * (1 - al) + c2 * al
    g = max(0.0, (p - 0.55) / 0.45)
    if g > 0:
        gr = tone(view('crack3', W, H, 1.0 + 6.5 * g ** 2, 0.5, 0.5), 0.45, COOL, 1.0, 0.9); a2 = sstep(0.0, 0.3, g); img = img * (1 - a2) + gr * a2
    ov = np.zeros((H, W), np.float32)
    for i in range(46):
        ang = hrand(i, 1) * 6.283; r0 = (0.1 + 0.4 * hrand(i, 2)) * W; r1 = r0 + (0.25 + 0.6 * p) * W * hrand(i, 3)
        cv2.line(ov, (int(W / 2 + math.cos(ang) * r0), int(H / 2 + math.sin(ang) * r0 * 0.6)), (int(W / 2 + math.cos(ang) * r1), int(H / 2 + math.sin(ang) * r1 * 0.6)), 1.0, max(1, int(2 * W / 1920)))
    ov = cv2.GaussianBlur(ov, (0, 0), 0.8); img = img + (1 - img) * (ov * 0.28 * sstep(0.1, 0.5, p))[..., None]
    return vig(img, 0.35 + 0.3 * p)


# ---------- 착지 ----------
IMP_CUTS = [(56.56, 'crack3', 3.0, 0.5, 0.5), (57.04, 'mud', 1.0, 0.5, 0.55), (58.51, 'crack2', 1.1, 0.45, 0.5), (59.58, 'sand', 1.0, 0.5, 0.5), (61.67, 'mud', 2.1, 0.58, 0.62)]
_IT = [c[0] for c in IMP_CUTS]


def sc_impact(t, W, H):
    a = t - 56.56; i = bisect.bisect_right(_IT, t) - 1; t0, nm, z0, cx, cy = IMP_CUTS[i]; b = t - t0
    if i == 0: z = 3.0 + 4.5 * math.exp(-a / 0.15)
    else: z = z0 * (1 + 0.28 * math.exp(-b / 0.16)) + 0.05 * b
    img = view(nm, W, H, z, cx, cy, 0.0, 0.0, (math.exp(-b / 0.2)) * 40 * H / 1080 if i else 0.0)
    w_ = float(sstep(0.0, 0.9, a)); img = tone(img, 0.35 + 0.85 * w_, tuple((1 - w_) * np.array(COOL) * 0.9 + w_ * np.array((1.0, 1.0, 1.0))), 1.0, 1.0)
    k = W / 1920; c = (W // 2, int(H * 0.55)); ov = np.zeros((H, W), np.float32)
    for d0 in (0.0, 0.12):
        r = (a - d0) * W * 2.3
        if 0 < r < W * 1.6 and a - d0 < 0.55: cv2.circle(ov, c, int(r), float(1 - (a - d0) / 0.55), max(2, int(9 * k)))
    img = img + (1 - img) * (cv2.GaussianBlur(ov, (0, 0), 1.2) * 0.5)[..., None]
    if a < 1.4:
        pm = np.zeros((H, W), np.float32)
        for j in range(90):
            ang = (hrand(j, 1) * 0.9 + 0.05) * math.pi; sp = (300 + 900 * hrand(j, 2)) * k * 1.3; vx = math.cos(ang) * sp * (hrand(j, 3) - 0.5) * 4.5
            pos = lambda aa: (c[0] + vx * aa, c[1] - math.sin(ang) * sp * aa + 0.5 * 2200 * k * aa * aa)
            (x, y), (x0, y0) = pos(a), pos(max(0.0, a - 0.04)); r = (5 + 13 * hrand(j, 4)) * k * 2.0 * max(0.0, 1 - a / 1.4)
            if r > 0.8: cv2.line(pm, (int(x0), int(y0)), (int(x), int(y)), 1.0, max(1, int(r * 0.8))); cv2.circle(pm, (int(x), int(y)), int(r), 1.0, -1)
        pm = cv2.GaussianBlur(pm, (0, 0), 1.4); tex = tone(view('crack2', W, H, 2.6, 0.5, 0.5), 0.45, (1.0, 1.0, 1.0), 1.0, 0.42) * 0.55 + np.array((0.045, 0.065, 0.10), np.float32)
        sh_ = cv2.GaussianBlur(pm, (0, 0), 6 * k); img = img * (1 - 0.35 * sh_[..., None]); al = np.clip(pm * 1.3, 0, 1)[..., None] * 0.95; img = img * (1 - al) + tex * al
    if a < 0.07: img = img + (1 - img) * 0.55 * (1 - a / 0.07)
    amp = 36 * k * math.exp(-a / 0.14) if a < 0.6 else 0.0
    if amp > 0.5:
        fr = int(t * 30); img = cv2.warpAffine(img, np.float32([[1, 0, (hrand(fr, 1) - 0.5) * 2 * amp], [0, 1, (hrand(fr, 2) - 0.5) * 2 * amp]]), (W, H), borderMode=cv2.BORDER_REFLECT)
    return vig(img, 0.3)


# ---------- 무게 ----------
WT_CUTS = [(62.2, 'crack2', 1.0), (63.55, 'crack1', 1.2), (65.43, 'crack3', 1.1)]
_WT = [c[0] for c in WT_CUTS]


def sc_weight(t, W, H):
    i = bisect.bisect_right(_WT, t) - 1; t0, nm, z0 = WT_CUTS[i]; b = t - t0; pl = N.pulse(t, 4.0)
    img = view(nm, W, H, z0 + 0.1 * b + 0.04 * pl, 0.5, 0.5, 0.0, 0.0, 22 * pl * H / 540 + 6 * b)
    img = tone(img, 0.75, (1.02, 0.98, 0.96), 1.15, 0.8 - 0.1 * pl)
    sq = 1 - 0.05 * pl; img = cv2.warpAffine(img, np.float32([[1, 0, 0], [0, sq, H * (1 - sq) * 0.5]]), (W, H), borderMode=cv2.BORDER_REFLECT)
    return vig(img, 0.6 + 0.2 * pl)


# ---------- 번짐(먹 마스크) ----------
_nz = {}
def bloom_field(W, H, seed):
    if (W, H, seed) not in _nz:
        rng = np.random.RandomState(seed); n = sum(cv2.resize(cv2.GaussianBlur(rng.rand(H // s + 2, W // s + 2).astype(np.float32), (0, 0), 1.2), (W, H)) * w for s, w in ((60, 1.0), (24, 0.6), (9, 0.3)))
        n = (n - n.min()) / (n.max() - n.min()); y, x = np.mgrid[0:H, 0:W].astype(np.float32); d = np.sqrt(((x - W / 2) / W) ** 2 + ((y - H / 2) / H) ** 2) / 0.62
        _nz[(W, H, seed)] = 0.5 * d + 0.5 * n
    return _nz[(W, H, seed)]


def bloom(base, top, f, thr):
    m = sstep(thr - 0.04, thr + 0.02, -f + 2 * thr - 0.0) if False else 1 - sstep(thr - 0.03, thr + 0.03, f)
    rim = np.exp(-((f - thr) / 0.035) ** 2) * (thr > 0.02) * (thr < 1.05)
    out = base * (1 - m[..., None]) + top * m[..., None]
    return out * (1 - 0.65 * rim[..., None])


def sc_alive(t, W, H):
    f1 = bloom_field(W, H, 7); f2 = bloom_field(W, H, 11); pl = N.pulse(t, 5)
    base = tone(view('crack3', W, H, 1.1 + 0.04 * (t - 66.8), 0.5, 0.5), 0.5, COOL, 1.1, 0.7)
    sun = tone(view('cloudD', W, H, 1.05 + 0.03 * (t - 66.8) + 0.03 * pl, 0.5, 0.45), 0.85, (0.9, 1.0, 1.08), 1.1, 0.95)
    img = bloom(base, sun, f1, 1.15 * eout((t - 66.9) / 2.4) * 1.0)
    mud = tone(view('mud', W, H, 1.1 + 0.05 * (t - 70.18) + 0.03 * pl, 0.5, 0.6), 1.15, WARM, 1.0, 1.0)
    if t >= 70.18: img = bloom(img, mud, f2, 1.15 * eout((t - 70.18) / 1.5))
    return vig(img, 0.35)


# ---------- 간주 ----------
POOL = ['limb', 'cloudD', 'crack3', 'night', 'mud', 'cloudC', 'lakes', 'crack1', 'sand', 'earth2', 'path1', 'cloudB']
KS = []
for _h in N.HITS:
    if 72.0 <= _h < 86.6 and (not KS or _h - KS[-1] >= 0.3): KS.append(_h)
LET = [72.30, 73.48, 74.13, 74.64, 75.09, 75.42, 75.73]
_ts = {}


def collage_photo(i, W, H, t):
    nm = POOL[i % len(POOL)]; hz = hrand(i, 9); tn = i % 3
    img = view(nm, W, H, 1.1 + 0.35 * hz + 0.05 * (t - KS[max(i, 0)]), 0.3 + 0.4 * hrand(i, 8), 0.3 + 0.4 * hrand(i, 7))
    return tone(img, (1.05, 0.8, 1.1)[tn], (WARM, COOL, (1, 1, 1))[tn], 1.0, (1.0, 0.85, 1.0)[tn])


def sc_inter(t, W, H):
    j = bisect.bisect_right(KS, t) - 1
    if j < 0: return sc_alive(72.0 - 1e-3, W, H)
    a = t - KS[j]; e = eout(a / 0.16)
    cur = collage_photo(j, W, H, t); prev = collage_photo(j - 1, W, H, KS[j]) if j > 0 else sc_alive(71.99, W, H)
    pat = j % 4; out = prev.copy()
    if pat == 0:
        n = 8
        for s in range(n):
            x0, x1 = s * W // n, (s + 1) * W // n; es = eout((a - 0.012 * s) / 0.16); dy = int((1 - es) * H * (1 if s % 2 else -1)); st = np.roll(cur[:, x0:x1], dy, axis=0)
            if dy > 0: st[:dy] = prev[:dy, x0:x1]
            elif dy < 0: st[dy:] = prev[dy:, x0:x1]
            out[:, x0:x1] = st
    elif pat == 1:
        n = 6
        for s in range(n):
            y0, y1 = s * H // n, (s + 1) * H // n; es = eout((a - 0.014 * s) / 0.16); dx = int((1 - es) * W * (1 if s % 2 else -1)); st = np.roll(cur[y0:y1], dx, axis=1)
            if dx > 0: st[:, :dx] = prev[y0:y1, :dx]
            elif dx < 0: st[:, dx:] = prev[y0:y1, dx:]
            out[y0:y1] = st
    elif pat == 2:
        R, C = 3, 4
        for r in range(R):
            for c in range(C):
                y0, y1, x0, x1 = r * H // R, (r + 1) * H // R, c * W // C, (c + 1) * W // C; sc = eout((a - 0.012 * (r + c)) / 0.16); w = max(1, int((x1 - x0) * sc))
                if sc >= 0.999: out[y0:y1, x0:x1] = cur[y0:y1, x0:x1]
                else:
                    tile = cv2.resize(cur[y0:y1, x0:x1], (w, y1 - y0)); xs = x0 + (x1 - x0 - w) // 2; out[y0:y1, xs:xs + w] = tile
    else:
        y, x = np.mgrid[0:H, 0:W].astype(np.float32); d = (x / W) * 0.6 + (y / H) * 0.4; m = (d < e * 1.1 - 0.05).astype(np.float32); m = cv2.GaussianBlur(m, (0, 0), 2)[..., None]
        z = 1.25 - 0.25 * e; cz = cv2.warpAffine(cur, cv2.getRotationMatrix2D((W / 2, H / 2), 0, z), (W, H), borderMode=cv2.BORDER_REFLECT); out = prev * (1 - m) + cz * m
    fl = 0.14 * math.exp(-a / 0.04); out = out + (1 - out) * fl
    # 마지막 구간: 진흙 발 사진으로 번져 들어감(브리지로 이어짐)
    if t >= 83.4:
        mud = tone(view('mud', W, H, 1.7 - 0.5 * eout((t - 83.4) / 3.2), 0.5, 0.45), 1.1, WARM, 1.0, 1.0); out = bloom(out, mud, bloom_field(W, H, 5), 1.15 * eout((t - 83.5) / 2.8))
    out = vig(out, 0.3)
    # 글자
    px = 0.19 * W; k = W / 1920; ws = [M.timg(c, px, M.SANS, int(4 * k)) for c in 'GRAVITY']; gap = int(6 * k); tw = sum(w.shape[1] for w in ws) + gap * 6
    x = W / 2 - tw / 2; msk = np.zeros((H, W), np.float32)
    for i, w in enumerate(ws):
        cx = x + w.shape[1] / 2; x += w.shape[1] + gap; dy = None
        if t < 75.9:
            if t >= LET[i]: aa = t - LET[i]; dy = -(1 - eout(aa / 0.17)) * H * 0.75 + (math.sin(aa * 38) * 7 * k * math.exp(-aa / 0.07) if aa < 0.3 else 0)
        elif t < 77.4: aa = t - 75.9; dy = math.sin(min(aa, 0.1) * 30) * 6 * k * math.exp(-aa / 0.1) + (-3 * k * N.pulse(t, 6))
        elif t < 81.4:
            aa = t - 77.4 - 0.03 * i; dy = 0.5 * 2600 * k * aa * aa if aa > 0 else 0
            if t > 77.4 + 0.03 * i + 0.9: dy = None
        elif t < 83.0: aa = t - 81.4 - 0.02 * i; dy = -(1 - eout(aa / 0.14)) * H * 0.8 if aa < 0.14 else (math.sin(aa * 36) * 5 * k * math.exp(-aa / 0.08) - 3 * k * N.pulse(t, 6)) if aa >= 0 else None
        else:
            aa = t - 83.0 - 0.03 * i; dy = 0.5 * 2600 * k * aa * aa if aa > 0 else 0
            if aa > 0.9: dy = None
        if dy is None or (t >= 81.4 and t - 81.4 - 0.02 * i < 0): continue
        paste(msk, w, cx, H * 0.46 + dy)
    if msk.max() > 0:
        halo = np.clip(cv2.GaussianBlur(cv2.dilate(msk, np.ones((max(3, int(9 * k)) | 1,) * 2, np.uint8)), (0, 0), 5 * k) * 1.5, 0, 1)
        out = out * (1 - 0.6 * halo[..., None]); out = out * (1 - msk[..., None]) + np.array((0.97, 0.98, 1.0), np.float32) * msk[..., None]
    z = 1 + 0.03 * N.pulse(t, 8); return cv2.warpAffine(out, cv2.getRotationMatrix2D((W / 2, H / 2), 0, z), (W, H), borderMode=cv2.BORDER_REFLECT)


SC = [(43.0, sc_glass, True), (51.5, sc_fall, True), (56.56, sc_impact, True), (62.2, sc_weight, True), (66.8, sc_alive, True), (72.0, sc_inter, False), (86.6, sc_inter, True)]
_T0 = [s[0] for s in SC]


def raw(t, W, H):
    i = max(0, bisect.bisect_right(_T0, t + 1e-6) - 1); t0, fn, sub = SC[i]
    img = fn(min(t, 86.59) if i == 6 else t, W, H)
    if sub: img = M.subtitle(img, t, 'neon', W, H)
    a = t - t0
    if 0 < i < 6 and a < 0.08: img = img + (1 - img) * 0.3 * (1 - a / 0.08)
    return img


def frame(t, W=960, H=540, k=0):
    n = 3 if (51.5 <= t < 56.56 or 0 <= t - N.last_hit(t) < 0.08) else 1
    img = post.subframes(lambda tt: raw(max(43.0, tt), W, H), t, fps=N.FPS, n=n) if n > 1 else raw(t, W, H)
    return np.clip(post.grade(img, grain=0.010, seed=k), 0, 1)
