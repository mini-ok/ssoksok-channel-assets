"""〈Gravity〉 뮤직비디오 2안 — 로봇 없이 발·손·작은 실루엣과 글자만으로. frame(t, W, H)는 시간의 순수 함수.
선의 세계(무중력: 가는 선·그림자 없음) → 물질의 세계(중력: 종이·먹·진흙·그림자). 타격 시각은 곡에서 잰 nums.HITS."""
import math, os, sys, bisect
import numpy as np, cv2
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import nums as N, fig as F, styles as S, mv as M
from styles import sstep, eout, hrand, paste, C_PAPER, C_INK, C_RED, C_BLUE, C_GOLD, C_GREEN, PAL
from mv import timg, cur_line, cur_word, BLACK, SANS
from vfx import post, ink
C_MUD = np.array(N.MUD[::-1], np.float32)
def hits(a, b): return [h for h in N.HITS if a <= h < b]
def rot(p, a): c, s = math.cos(a), math.sin(a); return (p[0] * c - p[1] * s, p[0] * s + p[1] * c)

# ---- 모양: 발바닥 자국, 옆에서 본 발, 손바닥 ------------------------------------------------
def sole(m, cx, cy, s, left=True, ang=0.0, val=255):
    f = -1 if left else 1
    def P(x, y): q = rot((x * f * s, y * s), ang); return (int(cx + q[0]), int(cy + q[1]))
    def E(x, y, rx, ry): cv2.ellipse(m, P(x, y), (max(1, int(rx * s)), max(1, int(ry * s))), math.degrees(ang), 0, 360, val, -1, cv2.LINE_AA)
    E(0.0, 0.34, 0.15, 0.19); E(0.02, -0.12, 0.21, 0.25)
    cv2.fillPoly(m, [np.array([P(-0.13, 0.30), P(-0.17, -0.05), P(0.10, -0.05), P(0.14, 0.30)], np.int32)], val, cv2.LINE_AA)
    for j, (x, y, r) in enumerate([(0.17, -0.46, 0.085), (0.04, -0.50, 0.062), (-0.07, -0.47, 0.055), (-0.16, -0.42, 0.048), (-0.23, -0.34, 0.042)]): E(x, y, r, r * 1.15)

FOOT = np.array([(-0.13, -3.0), (-0.12, -0.45), (-0.35, -0.22), (-0.72, -0.11), (-0.82, -0.05), (-0.80, 0.0), (-0.30, 0.0), (-0.15, -0.035), (0.05, 0.0), (0.20, 0.0), (0.26, -0.08), (0.21, -0.30), (0.14, -0.52), (0.19, -1.3), (0.17, -3.0)], np.float32)
def side_foot(m, cx, gy, s, flip=False, sq=1.0, val=255):
    p = FOOT.copy(); p[:, 0] *= (-1 if flip else 1) * (2 - sq); p[:, 1] *= sq
    cv2.fillPoly(m, [(p * s + (cx, gy)).astype(np.int32)], val, cv2.LINE_AA)

def palm(m, cx, cy, s, val=255, th=-1):
    cv2.ellipse(m, (int(cx), int(cy + 0.1 * s)), (int(0.30 * s), int(0.34 * s)), 0, 0, 360, val, th, cv2.LINE_AA)
    for a, L_, w in [(-1.15, 0.50, 0.075), (-0.42, 0.72, 0.07), (-0.08, 0.78, 0.072), (0.26, 0.72, 0.068), (0.62, 0.56, 0.06)]:
        bx, by = cx + 0.24 * s * math.sin(a * 0.9), cy - 0.14 * s * math.cos(a * 0.6)
        cv2.line(m, (int(bx), int(by)), (int(bx + L_ * s * math.sin(a)), int(by - L_ * s * math.cos(a))), val, max(1, int(w * 2 * s)) if th < 0 else max(1, th), cv2.LINE_AA)

def person(m, t, cx, cy, sc, val=255):
    """작은 사람 실루엣(뼈대는 fig의 추락 자세를 빌린다)."""
    J, _, _ = F.joints(t); c = np.array(J['P'])
    q = {k: (int(cx + (v[0] - c[0]) * sc), int(cy + (v[1] - c[1]) * sc)) for k, v in J.items() if k[0] != '_'}
    for a, b, w in [('SL', 'EL', 30), ('EL', 'HL', 24), ('SR', 'ER', 30), ('ER', 'HR', 24), ('PL', 'KL', 40), ('KL', 'FL', 30), ('PR', 'KR', 40), ('KR', 'FR', 30), ('C', 'P', 96), ('SL', 'SR', 44), ('N', 'H', 26)]:
        cv2.line(m, q[a], q[b], val, max(1, int(w * sc)), cv2.LINE_AA)
    cv2.circle(m, q['H'], max(1, int(44 * sc)), val, -1, cv2.LINE_AA)

def blurm(m, s): return cv2.GaussianBlur(m.astype(np.float32) / 255 if m.dtype == np.uint8 else m, (0, 0), max(0.5, s))
def over(img, m, col, a=1.0): return img * (1 - a * m[..., None]) + np.asarray(col, np.float32) * a * m[..., None]

# ---- 바탕 ---------------------------------------------------------------------------------
def space_bg(t, W, H, broken=0.0):
    k = W / N.DW; yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    img = np.empty((H, W, 3), np.float32); img[:] = (0.15, 0.07, 0.035); img *= (1.25 - 0.7 * np.hypot((xx - W / 2) / W, (yy - H / 2) / H))[..., None]
    rng = np.random.default_rng(4); sx = rng.random(240) * W; sy = rng.random(240) * H; sp = rng.random(240)
    for a, b, c in zip(sx, sy, sp): cv2.circle(img, (int(a), int(b)), 1 if c < 0.85 else 2, (0.5 + 0.5 * c,) * 3, -1, cv2.LINE_AA)
    c0 = (W // 2, int(H * 0.52))
    for n in range(6):
        a, b = int((240 + 150 * n) * k), int((90 + 58 * n) * k); ang = -12 + 4 * n
        if broken <= 0: cv2.ellipse(img, c0, (a, b), ang, 0, 360, (0.8, 0.6, 0.3), max(1, int(1.5 * k)), cv2.LINE_AA)
        else:                                                               # 궤도가 끊어져 흩어진다
            for q in range(12):
                d = broken * (40 + 260 * hrand(n, q)) * k; aa = math.radians(q * 30 + 15 + ang)
                cv2.ellipse(img, (int(c0[0] + d * math.cos(aa)), int(c0[1] + d * math.sin(aa) + 300 * k * broken ** 2 * hrand(n, q, 2))), (a, b), ang + broken * 60 * (hrand(n, q, 3) - 0.5), q * 30 + 2, q * 30 + 28 - 14 * broken, (0.8, 0.6, 0.3), max(1, int(1.5 * k)), cv2.LINE_AA)
    return img

def earth_bg(t, W, H, a=0.0, b=999.0, dark=False):
    """종이 바탕 + 타격마다 그어지는 굵은 붓 획(a~b초 사이의 타격만)."""
    fib, paper, streak = S.tex(W, H); k = W / N.DW; hs = hits(a, min(b, t + 1e-6))[-7:]
    lay = {0: np.zeros((H, W), np.float32), 1: np.zeros((H, W), np.float32), 2: np.zeros((H, W), np.float32), 3: np.zeros((H, W), np.float32)}
    for q, h in enumerate(hs):
        idx = N.HITS.index(h); age = t - h; p = eout(age / 0.14); y = int(H * (0.08 + 0.62 * hrand(idx, 1))); th = int((40 + 80 * hrand(idx, 2)) * k); dr = hrand(idx, 3) > 0.5
        x0, x1 = (0, int(W * p)) if dr else (int(W * (1 - p)), W); band = np.zeros((H, W), np.float32); band[max(0, y - th):y + th, x0:x1] = 1
        band = cv2.GaussianBlur(band, (0, 0), 2 * k) * sstep(0.3, 0.7, streak * 0.9 + 0.5 * fib + 0.15) * (1 - sstep(0.35, 0.9, streak))
        np.maximum(lay[idx % 4], band * (0.35 if idx % 4 == 0 else 0.8), out=lay[idx % 4])
    img = ink.composite(paper, [(lay[0], S.K_SUMI), (lay[1], S.K_RED), (lay[2], S.K_BLUE), (lay[3], S.K_GOLD)])
    return img

def splat(m, cx, cy, age, seed, k, n=26, spread=420, up=True):
    for j in range(n):
        a = (-math.pi * hrand(seed, j)) if up else 6.283 * hrand(seed, j); d = (40 + spread * hrand(seed, j, 2)) * eout(age / 0.22) * k
        g = 500 * k * age * age * (1 if up else 0)
        cv2.circle(m, (int(cx + d * math.cos(a)), int(cy + d * math.sin(a) * 0.8 + g)), max(1, int((3 + 15 * hrand(seed, j, 3) ** 2) * k)), 255, -1, cv2.LINE_AA)

def inked(mask_f, W, H, amt=0.9):
    fib = S.tex(W, H)[0]; return sstep(0.3, 0.6, mask_f + 0.32 * (fib - 0.5)) * amt

# ---- 장면 ---------------------------------------------------------------------------------
def sectors(W, H, O):
    rays = M.cracks(W, H, O, 7, n=15); out = []
    for i in range(len(rays)):
        a, b = rays[i], rays[(i + 1) % len(rays)]
        ea = a[-1] + (a[-1] - np.array(O)) * 3; eb = b[-1] + (b[-1] - np.array(O)) * 3
        out.append(np.vstack([a, [ea], [eb], b[::-1]]).astype(np.int32))
    return rays, out
_sec = {}
def sc_glass(t, W, H):
    k = W / N.DW; O = (int(W * 0.5), int(H * 0.47))
    if (W, H) not in _sec:
        rays, polys = sectors(W, H, O); ms = []
        for p in polys: m = np.zeros((H, W), np.uint8); cv2.fillPoly(m, [p], 255); ms.append(m.astype(np.float32) / 255)
        _sec[(W, H)] = (rays, polys, ms)
    rays, polys, ms = _sec[(W, H)]
    front = space_bg(t, W, H, broken=eout((t - 45.0) / 1.6) if t > 45.0 else 0.0)
    for th_, sc_ in ((43.5, 0.42), (45.0, 0.5)):                              # 유리를 치는 손바닥: 김 서린 자국
        if t >= th_:
            pm = np.zeros((H, W), np.uint8); palm(pm, O[0] + (0 if sc_ < 0.45 else 40 * k), O[1] + 20 * k, H * sc_ * (1 + 0.12 * math.exp(-(t - th_) / 0.05)))
            front = over(front, blurm(pm, 9 * k), (0.9, 0.85, 0.8), 0.20); front = over(front, blurm(pm, 1.5 * k) * (1 - blurm(cv2.erode(pm, np.ones((int(9 * k) | 1,) * 2, np.uint8)), 1.5 * k)), (1, 0.97, 0.92), 0.8)
    for th_, pr in ((43.5, 0.5), (45.0, 1.0)):
        if t >= th_:
            p = eout((t - th_) / 0.2) * pr if pr < 1 else 0.5 + 0.5 * eout((t - th_) / 0.2)
            for ri, pts in enumerate(rays):
                q = pts[:max(2, int(len(pts) * p))].astype(np.int32); cv2.polylines(front, [q], False, (1, 1, 1), max(1, int((2 if ri % 3 else 4) * k)), cv2.LINE_AA)
            if t - th_ < 0.09: front = front + (1 - front) * (1 - (t - th_) / 0.09)
    # 뒤: 진짜 세계(새벽 하늘 + 바람)
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    back = np.array((0.75, 0.50, 0.25), np.float32) + (np.array((0.35, 0.62, 0.98), np.float32) - (0.75, 0.50, 0.25)) * (yy / H)[..., None] ** 1.3
    wl = np.zeros((H, W), np.float32)
    for n in range(70):
        y = int(hrand(n, 1) * H); sp = 1.2 + 2.5 * hrand(n, 2); L_ = int((120 + 500 * hrand(n, 3)) * k); x = int(((t * sp + hrand(n, 4)) % 1.0) * (W + L_)) - L_
        cv2.line(wl, (x, y), (x + L_, y + int(L_ * 0.08)), 0.3 + 0.7 * hrand(n, 5), max(1, int((1 + 3 * hrand(n, 6)) * k)), cv2.LINE_AA)
    back = back + wl[..., None] * 0.5
    hs = hits(46.0, 51.45); img = back.copy()
    for i in range(len(ms)):                                                 # 조각이 타격마다 떨어져 나간다
        tf = hs[(i * 5) % len(ms) * len(hs) // len(ms)] if hs else 99; tf = min(tf, 51.3); age = t - tf
        if age <= 0: img = img * (1 - ms[i][..., None]) + front * ms[i][..., None]
        elif age < 1.3:
            a = (hrand(i, 9) - 0.5) * 1.6 * age; dy = 2600 * k * age * age; dx = (hrand(i, 8) - 0.5) * 500 * k * age
            Mx = cv2.getRotationMatrix2D((float(polys[i][:, 0].mean()), float(polys[i][:, 1].mean())), math.degrees(a), 1 + 0.25 * age); Mx[0, 2] += dx; Mx[1, 2] += dy
            fm = cv2.warpAffine(ms[i], Mx, (W, H)); ff = cv2.warpAffine(front, Mx, (W, H)); img = img * (1 - fm[..., None]) + (ff * 1.15 + 0.06) * fm[..., None]
    if t > 46.0:                                                             # 차가운 공기: 숨이 김으로 퍼진다
        for h in hits(46.0, 48.8):
            ag = t - h
            if 0 < ag < 1.2: fog = np.zeros((H, W), np.float32); cv2.circle(fog, (W // 2, int(H * 0.55)), int((60 + 520 * eout(ag / 1.0)) * k), 1.0, -1); img = img + blurm(fog, 50 * k)[..., None] * 0.35 * (1 - ag / 1.2)
    return img

def sc_fall(t, W, H):
    k = W / N.DW; u = (t - 51.5) / (56.56 - 51.5); yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    top = np.array((0.75, 0.50, 0.25), np.float32) * (1 - 0.5 * u); bot = np.array((0.30, 0.55, 1.0), np.float32)
    img = top + (bot - top) * (yy / H)[..., None] ** 1.4
    st = np.zeros((H, W), np.float32)
    for n in range(110):
        x = int(hrand(n, 1) * W); sp = 1.8 + 3.5 * hrand(n, 2); L_ = int((80 + 420 * hrand(n, 3)) * k); y = int((1 - ((t * sp + hrand(n, 4)) % 1.0)) * (H + L_)) - L_
        cv2.line(st, (x, y), (x, y + L_), 0.25 + 0.75 * hrand(n, 5), max(1, int((1 + 3 * hrand(n, 6)) * k)), cv2.LINE_AA)
    img = img + st[..., None] * 0.6
    sh = np.zeros((H, W), np.uint8)
    for n in range(22):                                                      # 같이 떨어지는 유리 조각
        x = hrand(n, 11) * W; y = (1 - ((t * (0.5 + 0.6 * hrand(n, 12)) + hrand(n, 13)) % 1.0)) * (H + 200) - 100; a = t * (2 + 4 * hrand(n, 14)); r = (18 + 50 * hrand(n, 15)) * k
        cv2.fillPoly(sh, [np.array([(x + r * math.cos(a + q * 2.3), y + r * math.sin(a + q * 2.3)) for q in range(3)], np.int32)], 255, cv2.LINE_AA)
    img = over(img, sh.astype(np.float32) / 255, (0.35, 0.18, 0.08), 0.75)
    w = cur_word(t)
    if w:
        g = timg(w[0], 420 * k, BLACK); sc = min(1.0, 0.9 * W / g.shape[1]) * (1 + 0.6 * (1 - eout(w[1] / 0.1)))
        g = cv2.resize(g, None, fx=sc, fy=sc); m = np.zeros((H, W), np.float32); paste(m, g, W / 2, H * 0.47 - 90 * k * eout(w[1] / 0.6)); img = over(img, m, [C_PAPER, C_GOLD, C_RED, C_PAPER][w[2] % 4])
    cx, cy = W / 2 + 60 * k * math.sin(t * 2.2), H * (0.42 + 0.1 * math.sin(t * 1.3)); sc_ = (0.42 + 0.5 * u * u) * k
    for q in range(6, 0, -1):
        gm = np.zeros((H, W), np.uint8); person(gm, t - q * 0.03, cx, cy - q * 44 * k, sc_); img = over(img, gm.astype(np.float32) / 255, C_INK, 0.13)
    pm = np.zeros((H, W), np.uint8); person(pm, t, cx, cy, sc_); pf = pm.astype(np.float32) / 255
    ol = cv2.dilate(pf, np.ones((int(7 * k) | 1,) * 2, np.uint8)); img = over(img, ol, C_PAPER); img = over(img, pf, C_INK * (1 - u) + np.array((0.12, 0.10, 0.09), np.float32) * u)
    if u > 0.86: gy = int(H * (1.0 - 0.26 * (u - 0.86) / 0.14)); img[gy:] = S.tex(W, H)[1][gy:] * 0.9      # 땅이 올라온다
    return img

def ground_scene(t, W, H, a, b, gy):
    img = earth_bg(t, W, H, a, b); k = W / N.DW
    img[gy:] = img[gy:] * np.array((0.55, 0.62, 0.72), np.float32)           # 흙
    cv2.line(img, (0, gy), (W, gy), (0.09, 0.09, 0.09), max(2, int(5 * k)), cv2.LINE_AA)
    return img

def feet_on(img, W, H, gy, t0, t, k, sink=0.0, spread=250):
    age = t - t0; sq = 1 - 0.22 * math.exp(-age / 0.06) * math.cos(age * 40) if age >= 0 else 1
    sh = np.zeros((H, W), np.uint8); g = eout(age / 0.5)                     # 처음 생긴 그림자
    cv2.ellipse(sh, (W // 2, gy + int(26 * k)), (int((520 * g + 60) * k), int((34 * g + 6) * k)), 0, 0, 360, 255, -1, cv2.LINE_AA); img = over(img, blurm(sh, 10 * k), (0.05, 0.05, 0.06), 0.55)
    fm = np.zeros((H, W), np.uint8); s = 300 * k
    side_foot(fm, W // 2 - spread * k, gy + sink, s, False, sq); side_foot(fm, W // 2 + (spread + 40) * k, gy + sink, s * 0.96, False, sq)
    return over(img, inked(blurm(fm, 1.2 * k), W, H, 1.0), (0.07, 0.065, 0.06), 0.97)

def sc_impact(t, W, H):
    k = W / N.DW; t0 = 56.56; age = t - t0
    if t < 59.3:
        gy = int(H * 0.72); img = ground_scene(t, W, H, t0, 59.3, gy); sp = np.zeros((H, W), np.uint8)
        for j, h in enumerate(hits(t0, 59.3)):
            ag = t - h
            if ag > 0: splat(sp, W // 2 + (0 if j == 0 else (hrand(j, 5) - 0.5) * 900 * k), gy, ag, j + 3, k, n=46 if j == 0 else 14, spread=900 if j == 0 else 380)
        img = over(img, inked(blurm(sp, k), W, H), (0.07, 0.065, 0.06), 0.95)
        for q in range(9):                                                   # 바닥에 가는 금
            x = W / 2 + (q - 4) * 150 * k; pts = [(x, gy)]
            for st in range(int(1 + 6 * eout(age / 0.25))): pts.append((pts[-1][0] + (hrand(q, st) - 0.5) * 90 * k, pts[-1][1] + (12 + 26 * hrand(q, st, 2)) * k))
            cv2.polylines(img, [np.array(pts, np.int32)], False, (0.08, 0.08, 0.08), max(1, int(3 * k)), cv2.LINE_AA)
        r = eout(age / 0.45); cv2.ellipse(img, (W // 2, gy), (int(1200 * r * k), int(150 * r * k)), 0, 180, 360, (0.08, 0.08, 0.08), max(1, int(10 * k * (1 - r))) if r < 1 else 1, cv2.LINE_AA)
        return feet_on(img, W, H, gy, t0, t, k)
    # 위에서 본 진흙 발자국: 내 세상의 바닥
    img = earth_bg(t, W, H, 59.3, 62.2) * np.array((0.62, 0.74, 0.88), np.float32); sp = np.zeros((H, W), np.uint8); pr = np.zeros((H, W), np.uint8)
    for j, (h, x, left) in enumerate([(59.3, 0.36, True), (N.near_hit(60.6), 0.64, False)]):
        ag = t - h
        if ag > 0: sc = 1 + 0.5 * (1 - eout(ag / 0.09)); sole(pr, W * x, H * 0.5, H * 0.78 * sc, left, (-0.12 if left else 0.12)); splat(sp, W * x, H * 0.5, ag, 30 + j, k, n=40, spread=560, up=False)
    img = over(img, inked(blurm(sp, k), W, H), C_MUD * 0.6, 0.9); img = over(img, inked(blurm(pr, 2 * k), W, H, 1.0), C_MUD * 0.42, 0.95)
    return img

ROWS = ['온몸을', '짓누르는', '이 낯선', '무게감']
def sc_weight(t, W, H):
    k = W / N.DW; t0 = 62.2; a = t - t0; step = (66.7 - t0) / 4; r = min(3, int(a / step)); ta = a - r * step
    img = np.empty((H, W, 3), np.float32); img[:] = (0.065, 0.06, 0.065); gy0 = int(H * 0.86); cols = [C_GOLD, C_PAPER, C_RED, C_PAPER]
    for q in range(r):                                                       # 먼저 떨어진 줄은 눌려 지층이 된다
        y = gy0 - int((q + 1) * 26 * k) + int(26 * k * (1 - eout(ta / 0.1)) * 0); img[y:y + int(22 * k)] = cols[q] * (0.85 if q % 2 else 1.0)
    gy = gy0 - int(r * 26 * k) - int(4 * k)
    g = timg(ROWS[r], 330 * k, BLACK); g = g[int(g.shape[0] * 0.18):int(g.shape[0] * 0.96)]; sc = min(1.4, 0.92 * W / g.shape[1])
    land = eout(ta / 0.11); sqz = 1 - 0.3 * math.exp(-max(0, ta - 0.11) / 0.05) * (ta > 0.11)
    crush = sstep(step - 0.12, step, ta) if r < 3 else 0.0                   # 다음 줄이 오기 직전 납작해진다
    hh = max(4, int(g.shape[0] * sc * sqz * (1 - 0.92 * crush))); g2 = cv2.resize(g, (int(g.shape[1] * sc * (1 + 0.15 * (1 - sqz))), hh))
    m = np.zeros((H, W), np.float32); paste(m, g2, W / 2, gy - hh / 2 - (1 - land) * H * 0.9); img = over(img, m, cols[r])
    cv2.line(img, (0, gy0), (W, gy0), [float(c) for c in C_PAPER], max(1, int(3 * k)))
    if 0.11 < ta < 0.6:
        d = np.zeros((H, W), np.uint8); splat(d, W / 2, gy, ta - 0.11, 50 + r, k, n=40, spread=1100); img = over(img, d.astype(np.float32) / 255, C_PAPER, 0.8)
        amp = 26 * k * math.exp(-(ta - 0.11) / 0.1); fr = int(t * 30); img = cv2.warpAffine(img, np.float32([[1, 0, (hrand(fr, 1) - 0.5) * amp], [0, 1, (hrand(fr, 2) - 0.2) * 2 * amp]]), (W, H), borderMode=cv2.BORDER_REFLECT)
    return img

def sc_alive(t, W, H):
    k = W / N.DW; t0 = 66.8; gy = int(H * 0.80); img = ground_scene(t, W, H, t0, 72.0, gy); hs = hits(t0, t + 1e-6)
    layers = {i: np.zeros((H, W), np.uint8) for i in range(4)}
    for j, h in enumerate(hs):                                               # 타격마다 발밑에서 뻗어 나오는 획: 살아 있다는 감각
        ag = t - h; nn = 9 + 3 * j; big = h >= 69.9
        for q in range(nn):
            a = -math.pi * (q + 0.5 + 0.4 * hrand(j, q)) / nn; r0 = (150 + 95 * j) * k; r1 = r0 + (90 + 170 * hrand(j, q, 2) + (500 if big else 0)) * k * eout(ag / 0.18)
            cv2.line(layers[(j + q) % 4], (int(W / 2 + r0 * math.cos(a)), int(gy + r0 * math.sin(a))), (int(W / 2 + r1 * math.cos(a)), int(gy + r1 * math.sin(a))), 255, max(2, int((10 + 16 * hrand(j, q, 3)) * k)), cv2.LINE_AA)
    for i, (kk, amt) in enumerate([(S.K_SUMI, 0.5), (S.K_RED, 0.9), (S.K_BLUE, 0.9), (S.K_GOLD, 0.95)]):
        img = ink.composite(img, [(inked(blurm(layers[i], 1.2 * k), W, H, amt), kk)])
    ag = t - N.last_hit(t); r = eout(ag / 0.4)
    cv2.ellipse(img, (W // 2, gy), (int(1300 * r * k), int(1300 * r * k)), 0, 180, 360, (0.1, 0.1, 0.1), max(1, int(8 * k * (1 - r))), cv2.LINE_AA)
    img = feet_on(img, W, H, gy, t0 - 5, t, k, spread=150)
    if 0 <= t - 70.0 < 0.12: img = img + (1 - img) * (1 - (t - 70.0) / 0.12)
    return img

def flat(W, H, c): img = np.empty((H, W, 3), np.float32); img[:] = c; return img
BGS = [(C_INK, C_PAPER), (C_RED, C_PAPER), (C_PAPER, C_INK), (C_BLUE, C_GOLD), (C_GOLD, C_INK), (C_GREEN, C_PAPER)]
def sc_inter(t, W, H, a=72.0, word_t=(75.9, 81.4), b=86.6):
    """간주: 타격마다 무언가 떨어져 바닥에 찍힌다. 글자 → 큰 낱말 → 발자국 → 낱말 → 쏟아지는 먹."""
    k = W / N.DW; hs = hits(a, b); i = max(0, bisect.bisect_right(hs, t) - 1); h = hs[i] if hs and t >= hs[0] else a; ag = t - h
    bg, fg = BGS[(i + (0 if t < word_t[0] else 2)) % len(BGS)]; img = flat(W, H, bg); gy = int(H * 0.74); L_ = 'GRAVITY'
    seg = (word_t[0] - a, 2.5, word_t[1] - word_t[0] - 2.5, 2.1)
    if t < word_t[0]:                                                        # 1) 글자가 타격마다 하나씩 떨어진다
        hs1 = hits(a, word_t[0]); cw = W * 0.9 / 7
        for j, ch in enumerate(L_):
            tj = hs1[j] if j < len(hs1) else word_t[0] - 0.05 * (7 - j); aj = t - tj
            if aj <= 0: continue
            g = timg(ch, 430 * k, BLACK); g = g[int(g.shape[0] * 0.2):int(g.shape[0] * 0.93)]; sq = 1 - 0.35 * math.exp(-max(0, aj - 0.08) / 0.05) * (aj > 0.08); g = cv2.resize(g, None, fx=min(1.0, cw * 0.98 / g.shape[1]) * (1 + 0.2 * (1 - sq)), fy=sq)
            m = np.zeros((H, W), np.float32); paste(m, g, W * 0.05 + cw * (j + 0.5), gy - g.shape[0] * 0.5 - (1 - eout(aj / 0.08)) * H); img = over(img, m, fg if j % 2 == 0 else PAL[(j + i) % 4])
        cv2.line(img, (0, gy), (W, gy), [float(c) for c in fg], max(2, int(6 * k)))
        d = np.zeros((H, W), np.uint8); jn = min(6, i); splat(d, W * 0.05 + cw * (jn + 0.5), gy, max(0, ag - 0.08), 70 + i, k, n=22, spread=500); img = over(img, d.astype(np.float32) / 255, fg, 0.9 * (ag > 0.08))
    elif (word_t[0] <= t < word_t[0] + seg[1]) or (word_t[1] <= t < word_t[1] + seg[3]):      # 2) 낱말 전체가 화면을 친다
        w0 = word_t[0] if t < word_t[1] else word_t[1]; aw = t - w0; second = t >= word_t[1]
        g = timg(L_, 420 * k, BLACK, 0); sc = (0.94 * W / g.shape[1]) * (1 + 0.55 * (1 - eout(aw / 0.1))) * (1 + 0.05 * N.pulse(t, 7))
        g = cv2.resize(g, None, fx=sc, fy=sc * (1.0 if not second else 1.9))
        for q in range(4 if second else 1):                                  # 두 번째는 세로로 길게, 잔상이 겹쳐 떨어진다
            m = np.zeros((H, W), np.float32); paste(m, g, W / 2, H * 0.5 - q * 46 * k * (1 + 3 * math.exp(-ag / 0.1)) + (hrand(int(t * 30), q) - 0.5) * 30 * k * math.exp(-ag / 0.06))
            img = over(img, m, fg if q == 0 else PAL[(q + i) % 4], 1.0 if q == 0 else 0.55)
        if not second:
            for q in range(14): x = int(W * hrand(i, q)); cv2.line(img, (x, 0), (x, int(H * eout(ag / 0.12))), [float(c) for c in fg], max(1, int((2 + 10 * hrand(i, q, 2)) * k)))
        if aw < 0.1: img = 1 - img
    elif t < word_t[1]:                                                      # 3) 발자국이 타격마다 찍히며 다가온다
        hs3 = hits(word_t[0] + seg[1], word_t[1]); j = max(0, bisect.bisect_right(hs3, t) - 1); pr = np.zeros((H, W), np.uint8); sp = np.zeros((H, W), np.uint8)
        for q in range(j + 1):
            aq = t - hs3[q] if hs3 else 0; left = q % 2 == 0; s = H * (0.34 + 0.2 * q) * (1 + 0.6 * (1 - eout(aq / 0.08))); x = W * (0.5 + (-0.17 if left else 0.17) * (1 + 0.25 * q)); y = H * (0.78 - 0.1 * q)
            sole(pr, x, y, s, left, -0.1 if left else 0.1, 255 if q == j else 120)
            if q == j: splat(sp, x, y, aq, 90 + q, k, n=36, spread=700, up=False)
        img = over(img, sp.astype(np.float32) / 255, fg, 0.9); img = over(img, (pr == 120).astype(np.float32), fg, 0.35); img = over(img, blurm((pr == 255).astype(np.uint8) * 255, k), fg, 1.0)
        r = eout(ag / 0.3); cv2.circle(img, (W // 2, H // 2), int(W * 0.8 * r), [float(c) for c in fg], max(1, int(30 * k * (1 - r))), cv2.LINE_AA)
    else:                                                                    # 4) 쏟아진다: 먹 기둥이 타격마다 바닥을 친다
        hs4 = hits(word_t[1] + seg[3], b); gy = int(H * 0.86); cv2.line(img, (0, gy), (W, gy), [float(c) for c in fg], max(2, int(6 * k)))
        for q, hq in enumerate(hs4):
            aq = t - hq
            if aq <= 0: continue
            for c in range(5 + 3 * q):
                x = int(W * hrand(q, c, 4)); wdt = int((24 + 130 * hrand(q, c, 5)) * k); y1 = int(gy * eout(aq / 0.07)); keep = (0.25 + 0.75 * hrand(q, c, 6)) if aq > 0.07 else 1.0
                cv2.rectangle(img, (x - wdt // 2, int(y1 - gy * keep * 1.0)), (x + wdt // 2, y1), [float(v) for v in (fg if c % 2 else PAL[(q + c) % 4])], -1)
                if aq > 0.07: cv2.ellipse(img, (x, gy), (int((wdt + 300 * eout((aq - 0.07) / 0.25)) * 1), int(20 * k)), 0, 180, 360, [float(v) for v in fg], max(1, int(6 * k * max(0.0, 1 - aq / 0.4)) + 1), cv2.LINE_AA)
        if b - t < 0.12: img = img + (1 - img) * (1 - (b - t) / 0.12)
    if ag < 0.2 and t >= (hs[0] if hs else a):                               # 타격마다 화면이 내려앉는다
        img = cv2.warpAffine(img, np.float32([[1, 0, 0], [0, 1, 22 * k * math.exp(-ag / 0.05)]]), (W, H), borderMode=cv2.BORDER_REPLICATE)
    return img

SCENES = [(43.0, sc_glass, True), (51.5, sc_fall, None), (56.56, sc_impact, False), (62.2, sc_weight, None), (66.8, sc_alive, False), (72.0, sc_inter, None), (86.6, None, None)]
_T0 = [s[0] for s in SCENES]
def raw(t, W, H):
    i = max(0, bisect.bisect_right(_T0, t + 1e-6) - 1); t0, fn, sub = SCENES[i]
    if fn is None: return np.zeros((H, W, 3), np.float32)
    img = fn(t, W, H); a = t - t0
    if sub is not None: img = M.subtitle(img, t, 'neon' if sub else 'ink', W, H)
    z = 1 + 0.035 * N.pulse(t, 8) + (0.2 * (1 - eout(a / 0.15)) if i > 0 else 0)
    img = cv2.warpAffine(img, cv2.getRotationMatrix2D((W / 2, H / 2), 0, z), (W, H), borderMode=cv2.BORDER_REFLECT)
    if i > 0 and a < 0.09: img = img + (1 - img) * (1 - a / 0.09) ** 1.5
    d = t - 56.56
    if 0 <= d < 0.5: amp = 40 * W / 1920 * math.exp(-d / 0.12); fr = int(t * 30); img = cv2.warpAffine(img, np.float32([[1, 0, (hrand(fr, 1) - 0.5) * 2 * amp], [0, 1, (hrand(fr, 2) - 0.5) * 2 * amp]]), (W, H), borderMode=cv2.BORDER_REFLECT)
    return img

def frame(t, W=960, H=540, k=0):
    n = 3 if (51.5 <= t < 56.56 or t - N.last_hit(t) < 0.1) else 1
    img = post.subframes(lambda tt: raw(max(43.0, tt), W, H), t, fps=N.FPS, n=n) if n > 1 else raw(t, W, H)
    return np.clip(post.grade(img, grain=0.010, seed=k), 0, 1)
