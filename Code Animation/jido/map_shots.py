"""〈지도〉 애니매틱 지도 컷들(라이다 지도 화면). 사용: python3 map_shots.py <shot> out.mp4   (shot: all 이면 전부)
화면 960×540, 24fps. 지도 좌표는 미터(집 10×6.2 m, 현관문 x 0.3–1.2 / y 6.2, 그 밖은 복도·계단).
"""
import os, sys, math, subprocess
import numpy as np, cv2

W, H, FPS, SS = 960, 540, 24, 2
IW, IH = W * SS, H * SS
BG = np.array([0.055, 0.045, 0.040], np.float32)
WALL = np.array([0.98, 0.95, 0.86], np.float32); FLOOR = np.array([0.30, 0.20, 0.13], np.float32)
AMB = np.array([0.35, 0.68, 1.00], np.float32); GRN = np.array([0.55, 1.00, 0.55], np.float32)
G = 0.035

def rect(x0, y0, x1, y1): return [((x0, y0), (x1, y0)), ((x1, y0), (x1, y1)), ((x1, y1), (x0, y1)), ((x0, y1), (x0, y0))]
SEG = [((0, 0), (10, 0)), ((10, 0), (10, 6.2)), ((10, 6.2), (1.2, 6.2)), ((0.3, 6.2), (0, 6.2)), ((0, 6.2), (0, 0)),
       ((4.2, 0), (4.2, 2.3)), ((4.2, 3.2), (4.2, 6.2)), ((4.2, 3.6), (6.6, 3.6)), ((7.5, 3.6), (10, 3.6)),
       ((0, 4.4), (1.4, 4.4)), ((2.3, 4.4), (2.6, 4.4))]
SEG += rect(0.5, 0.35, 2.9, 1.15) + rect(9.3, 0.3, 9.9, 1.2) + rect(4.4, 4.1, 6.2, 6.0) + rect(8.5, 5.4, 9.8, 6.0) + rect(4.3, 0.1, 7.6, 0.6)
CIR = [(6.2, 1.9, .035), (7.6, 1.9, .035), (6.2, 2.9, .035), (7.6, 2.9, .035), (5.8, 2.1, .025), (5.8, 2.7, .025), (8.0, 2.1, .025), (8.0, 2.7, .025),
       (1.2, 2.6, .03), (2.3, 2.6, .03), (1.2, 3.3, .03), (2.3, 3.3, .03), (3.7, 5.6, .18), (1.7, 1.55, .02), (2.1, 1.55, .02)]
DOOR_LEAF = [((0.3, 6.2), (0.3 + 0.9 * math.cos(1.25), 6.2 + 0.9 * math.sin(1.25)))]                   # 열린 현관문
CORR = [((-4.5, 7.9), (6.0, 7.9)), ((-4.5, 6.2), (-4.5, 7.9)), ((-4.5, 6.2), (0.0, 6.2))]
STAIR_X = [-2.4 - 0.28 * k for k in range(6)]
CORR += [((x, 6.35), (x, 7.75)) for x in STAIR_X]
DOCK = np.array([4.0, 5.9]); DOCK = np.array([3.2, 0.25])                                                 # 충전대(거실 아래쪽 벽)

def cast(p, ang, segs, cirs, rng):
    A = np.array([s[0] for s in segs], float); B = np.array([s[1] for s in segs], float)
    d = np.stack([np.cos(ang), np.sin(ang)], 1); e = B - A
    den = d[:, None, 0] * e[None, :, 1] - d[:, None, 1] * e[None, :, 0]; den = np.where(np.abs(den) < 1e-9, 1e-9, den)
    w = A[None] - p[None, None]
    tt = (w[..., 0] * e[None, :, 1] - w[..., 1] * e[None, :, 0]) / den
    ss = (w[..., 0] * d[:, None, 1] - w[..., 1] * d[:, None, 0]) / den
    dist = np.where((tt > 1e-4) & (ss >= 0) & (ss <= 1), tt, np.inf).min(1); kind = np.zeros(len(ang), int)
    if cirs:
        cc = np.array([[c[0], c[1]] for c in cirs]); rr = np.array([c[2] for c in cirs]); amb = np.array([c[3] if len(c) > 3 else 0 for c in cirs])
        oc = cc[None] - p[None, None]; b = (oc * d[:, None]).sum(-1); c = (oc ** 2).sum(-1) - rr[None] ** 2
        disc = b * b - c; th = b - np.sqrt(np.maximum(disc, 0)); dc = np.where((disc > 0) & (th > 1e-4), th, np.inf)
        j = dc.argmin(1); dm = dc[np.arange(len(ang)), j]; cl = dm < dist
        dist = np.where(cl, dm, dist); kind = np.where(cl, np.where(amb[j] > 0, 2, 1), 0)
    hit = dist < rng
    return p[None] + d * np.minimum(dist, rng)[:, None], kind, hit

def cells(P): return {(int(round(x / G)), int(round(y / G))) for x, y in P}

# 집 전체 지도(완성본): 집 안 여러 자리에서 쏴서 모음
def full_map(segs, cirs, spots):
    S = set(); rng = np.random.default_rng(1)
    for p in spots:
        ang = np.linspace(0, 2 * np.pi, 1400, endpoint=False) + rng.uniform(0, 0.004)
        P, k, h = cast(np.array(p, float), ang, segs, cirs, 3.5); S |= cells(P[h & (k != 2)])
    return np.array(sorted(S), float) * G
SPOTS = [(x, y) for x in np.arange(0.3, 10, 0.55) for y in np.arange(0.3, 6.0, 0.55)
         if not any(a[0] - .05 < x < b[0] + .05 and a[1] - .05 < y < b[1] + .05 for a, b in [((0.5, 0.35), (2.9, 1.15)), ((9.3, 0.3), (9.9, 1.2)), ((4.4, 4.1), (6.2, 6.0)), ((8.5, 5.4), (9.8, 6.0)), ((4.3, 0.1), (7.6, 0.6))])]
FULL = full_map(SEG, CIR, SPOTS)
HOME_FLOOR = [np.array([(0, 0), (10, 0), (10, 6.2), (0, 6.2)], float)]

# ---------------------------------------------------------------- 그리기
class View:
    def __init__(s, z, c): s.z = z * SS; s.c = np.array(c, float)
    def px(s, P): return ((np.asarray(P, float) - s.c) * np.array([1, -1]) * s.z + np.array([IW / 2, IH / 2])).astype(np.float32)
def lerp(a, b, u): return a + (b - a) * u
def cl(u): return min(1.0, max(0.0, u))
def sm(u): u = cl(u); return u * u * (3 - 2 * u)
def ramp(t, a, b): return cl((t - a) / (b - a))

class Frame:
    def __init__(s, bg=1.0): s.img = np.zeros((IH, IW, 3), np.float32) + BG * bg; s.glow = np.zeros((IH, IW, 3), np.float32)
    def floor(s, v, polys, a=1.0):
        m = np.zeros((IH, IW), np.float32)
        for P in polys: cv2.fillPoly(m, [np.round(v.px(P)).astype(np.int32)], 1.0, cv2.LINE_AA)
        s.img += cv2.GaussianBlur(m, (0, 0), 2 * SS)[..., None] * FLOOR * 0.42 * a
    def floor_mask(s, v, mask, res, a=1.0):
        sm_ = cv2.resize(mask.astype(np.float32), None, fx=res * v.z, fy=res * v.z, interpolation=cv2.INTER_LINEAR)[::-1]
        oy = IH / 2 - (mask.shape[0] * res - v.c[1]) * v.z; ox = IW / 2 - v.c[0] * v.z
        M = np.float32([[1, 0, ox], [0, 1, oy]]); f = cv2.warpAffine(sm_, M, (IW, IH))
        s.img += cv2.GaussianBlur(f, (0, 0), 2 * SS)[..., None] * FLOOR * 0.42 * a
    def points(s, v, P, br, col=WALL, glow=0.9):
        if len(P) == 0: return
        q = np.round(v.px(P)).astype(int); ok = (q[:, 0] >= 0) & (q[:, 0] < IW) & (q[:, 1] >= 0) & (q[:, 1] < IH)
        lay = np.zeros((IH, IW), np.float32); br = np.broadcast_to(np.asarray(br, np.float32), (len(P),))
        np.maximum.at(lay, (q[ok, 1], q[ok, 0]), br[ok])
        lay = cv2.dilate(lay, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * SS + 1, 2 * SS + 1)))
        s.img += lay[..., None] * col * 0.85; s.glow += lay[..., None] * col * glow
    def line(s, v, P, col, a=1.0, w=1, glow=0.6, dashed=False):
        if len(P) < 2: return
        lay = np.zeros((IH, IW), np.float32); q = np.round(v.px(P)).astype(np.int32)
        if dashed:
            for i in range(0, len(q) - 1, 2): cv2.line(lay, tuple(q[i]), tuple(q[i + 1]), 1.0, w * SS, cv2.LINE_AA)
        else: cv2.polylines(lay, [q], False, 1.0, w * SS, cv2.LINE_AA)
        s.img += lay[..., None] * col * a; s.glow += lay[..., None] * col * a * glow
    def dots(s, v, P, col, r=2, a=1.0, glow=1.4):
        lay = np.zeros((IH, IW), np.float32)
        for q in np.round(v.px(P)).astype(int): cv2.circle(lay, tuple(q), r * SS, 1.0, -1, cv2.LINE_AA)
        s.img += lay[..., None] * col * 0.9 * a; s.glow += lay[..., None] * col * glow * a
    def vac(s, v, p, d, t, led=GRN, a=1.0):
        q = tuple(np.round(v.px([p])[0]).astype(int)); r = int(0.17 * v.z)
        body = np.zeros((IH, IW), np.float32); cv2.circle(body, q, r, 1.0, -1, cv2.LINE_AA)
        s.img = s.img * (1 - body[..., None] * 0.85 * a) + body[..., None] * np.array([0.16, 0.15, 0.15]) * a
        ring = np.zeros_like(body); cv2.circle(ring, q, r, 1.0, SS, cv2.LINE_AA); s.img += ring[..., None] * WALL * 0.6 * a
        lq = tuple(np.round(v.px([np.asarray(p) + np.asarray(d) * 0.1])[0]).astype(int))
        led_ = np.zeros_like(body); cv2.circle(led_, lq, max(2, int(0.025 * v.z)), 1.0, -1, cv2.LINE_AA)
        b = (0.75 + 0.25 * math.sin(t * 3.2)) * a; s.img += led_[..., None] * led * b; s.glow += led_[..., None] * led * 3 * b
    def ring(s, v, p, r, col, a):
        lay = np.zeros((IH, IW), np.float32); cv2.circle(lay, tuple(np.round(v.px([p])[0]).astype(int)), int(r * v.z), 1.0, SS, cv2.LINE_AA)
        s.img += lay[..., None] * col * a; s.glow += lay[..., None] * col * a
    def out(s, fade=1.0, t=0.0):
        g = cv2.GaussianBlur(cv2.resize(s.glow, (IW // 4, IH // 4), interpolation=cv2.INTER_AREA), (0, 0), 3)
        img = cv2.resize(s.img, (W, H), interpolation=cv2.INTER_AREA) + cv2.resize(g, (W, H)) * 0.9
        img = 1 - np.exp(-img * 1.25)
        yy, xx = np.mgrid[0:H, 0:W]; img *= (1 - 0.35 * (((xx / W - .5) ** 2 + (yy / H - .5) ** 2) * 2.2))[..., None]
        img += np.random.default_rng(int(t * 1000)).normal(0, 0.012, img.shape)
        return (np.clip(img * fade, 0, 1) * 255 + 0.5).astype(np.uint8)

def feet_pts(c, face, sep=0.11):
    """라이다가 보는 두 슬리퍼: 청소기 쪽을 향한 반원 점들."""
    out = []; c = np.asarray(c, float); n = np.array([-face[1], face[0]])
    for sd in (-1, 1):
        fc = c + n * sep * 0.5 * sd
        for a in np.linspace(-1.3, 1.3, 7):
            dd = np.array([math.cos(a), math.sin(a)]); rot = np.array([[face[0], -face[1]], [face[1], face[0]]]) @ dd
            out.append(fc - rot * 0.06)
    return np.array(out)
def poly_at(P, u):
    P = np.asarray(P, float); seg = np.linalg.norm(np.diff(P, axis=0), axis=1); L = np.concatenate([[0], np.cumsum(seg)]); s = cl(u) * L[-1]
    i = min(len(seg) - 1, np.searchsorted(L, s, side='right') - 1); f = (s - L[i]) / max(seg[i], 1e-9)
    return P[i] + (P[i + 1] - P[i]) * f, (P[i + 1] - P[i]) / max(seg[i], 1e-9)
def poly_upto(P, u, n=120): return np.array([poly_at(P, k / n * u)[0] for k in range(n + 1)])

ROUTE = [(5.2, 4.9), (6.4, 3.9), (7.05, 3.3), (7.0, 2.45), (6.9, 1.5), (8.4, 1.3), (9.0, 1.9), (7.4, 3.25), (5.4, 3.0), (3.6, 2.8), (2.2, 2.1), (1.4, 1.75)]
HOME = View(84, (5.0, 3.0))

# ---------------------------------------------------------------- 컷
def shot_firstmap(T):
    """새벽: 충전대에서 출발, 지도가 청소기 둘레부터 자란다."""
    hits = {}; seen = np.zeros((int(6.5 / 0.04), int(10.5 / 0.04)), np.uint8); rng = np.random.default_rng(3); trail = []
    path = np.array([DOCK, (3.4, 0.9), (3.3, 2.0), (2.3, 2.3), (1.0, 2.0), (0.6, 3.2), (1.6, 3.9), (3.0, 3.6), (3.9, 2.8), (4.8, 2.75), (5.6, 2.3)])
    for k in range(int(T * FPS)):
        t = k / FPS; u = (t / T) ** 0.95; p, d = poly_at(path, u); trail.append(p)
        ang = np.linspace(0, 2 * np.pi, 700, endpoint=False) + rng.uniform(0, 0.009, 700) + k * 0.37
        P, kd, h = cast(p, ang, SEG, CIR, 2.4); P = P + rng.normal(0, 0.006, P.shape)
        for c in cells(P[h & (kd == 0) | h & (kd == 1)]): hits.setdefault(c, t)
        poly = np.round(np.vstack([P[np.argsort(ang)]]) / 0.04).astype(np.int32); cv2.fillPoly(seen, [poly], 1)
        v = View(lerp(150, 105, sm(t / T)), lerp(DOCK + np.array([0, 0.6]), np.array([3.6, 2.4]), sm(t / T)))
        f = Frame(); f.floor_mask(v, seen, 0.04)
        ks = np.array(list(hits.keys()), float) * G; ts = np.array(list(hits.values()))
        f.points(v, ks, 0.5 + 1.0 * np.exp(-(t - ts) * 3))
        f.line(v, np.array(trail), GRN, 0.28)
        f.vac(v, p, d, t); yield f.out(ramp(t, 0, 0.8), t)

def shot_play(T):
    """티격태격: 초록 길이 호박색 발을 쫓고, 발이 피해 다니고, 부스러기 점들."""
    path_f = [(2.2, 3.6), (2.9, 3.0), (2.4, 2.3), (1.6, 2.4), (1.5, 3.3), (2.3, 3.8), (3.2, 3.2)]
    trail = []; v = View(150, (2.4, 2.95))
    for k in range(int(T * FPS)):
        t = k / FPS; uf = t / T
        fp, fd = poly_at(path_f, uf); vp, vd = poly_at(path_f, max(0, uf - 0.09)); trail.append(vp)
        f = Frame(); f.floor(v, HOME_FLOOR); f.points(v, FULL, 0.5)
        f.line(v, np.array(trail), GRN, 0.3)
        hop = abs(math.sin(t * 6)) * 0.0
        f.dots(v, feet_pts(fp, -vd if np.linalg.norm(vd) else (1, 0)), AMB, 2)
        f.vac(v, vp, vd, t); yield f.out(1.0, t)

def shot_routine(T):
    """나날: 하루마다 같은 길(부엌→식탁→창가)이 겹쳐 닳은 길이 된다. 지도가 100%가 되는 날 고리가 퍼진다."""
    days = 12; rng = np.random.default_rng(5); daypaths = []
    for d in range(days): daypaths.append(np.array(ROUTE) + rng.normal(0, 0.05, (len(ROUTE), 2)))
    for k in range(int(T * FPS)):
        t = k / FPS; dt = T * 0.82 / days; d = min(days - 1, int(t / dt)); u = cl((t - d * dt) / (dt * 0.85))
        night = 0.5 + 0.5 * math.cos(2 * math.pi * cl((t - d * dt) / dt))
        reveal = lerp(0.7, 1.0, ramp(t, 0, T * 0.8))
        f = Frame(1 - 0.35 * (1 - night)); f.floor(HOME, HOME_FLOOR)
        sel = FULL[:, 0] < reveal * 10.4; f.points(HOME, FULL[sel], 0.5)
        worn = np.zeros((IH, IW), np.float32)
        for j in range(d):
            q = np.round(HOME.px(poly_upto(daypaths[j], 1))).astype(np.int32); cv2.polylines(worn, [q], False, 1.0, 2 * SS, cv2.LINE_AA)
            worn *= 0.985
        lay = cv2.GaussianBlur(np.minimum(worn * 0.35 * (1 + d * 0.15), 1.4), (0, 0), 1.5)
        f.img += lay[..., None] * AMB * 0.5; f.glow += lay[..., None] * AMB * 0.4
        cur = poly_upto(daypaths[d], u); f.line(HOME, cur, AMB, 0.8)
        fp, fd = poly_at(daypaths[d], u); f.dots(HOME, feet_pts(fp, fd), AMB, 2)
        f.vac(HOME, np.array([3.2, 0.42]), (0, 1), t * 0.3)
        for j in range(days): f.dots(HOME, [(0.6 + j * 0.18, -0.35)], WALL, 1, a=0.9 if j <= d else 0.15, glow=0.2)   # 날짜 눈금
        tc = T * 0.84
        if t > tc: f.ring(HOME, (5.0, 3.1), 0.5 + 6 * sm(ramp(t, tc, tc + 1.6)), GRN, 0.8 * (1 - ramp(t, tc, tc + 1.6)))
        yield f.out(ramp(t, 0, 0.4), t)

def shot_loops(T):
    """밤: 같은 자리를 세 번 맴도는 발 → 며칠이 겹치며 고리·멈춤이 늘고 현관문 앞이 밝아진다, 엉뚱한 장애물."""
    loop = [(5.4, 3.0)] + [(3.6 + 0.45 * math.cos(a), 2.8 + 0.35 * math.sin(a)) for a in np.linspace(0, 6 * math.pi, 60)] + [(3.0, 3.6)]
    rng = np.random.default_rng(8); obst = [(2.0 + rng.uniform(0, 6), 1.3 + rng.uniform(0, 3.8)) for _ in range(6)]
    for k in range(int(T * FPS)):
        t = k / FPS; f = Frame(0.55); f.floor(HOME, HOME_FLOOR, 0.7); f.points(HOME, FULL, 0.42)
        u = ramp(t, 0, T * 0.42); f.line(HOME, poly_upto(loop, u), AMB, 0.8)
        fp, fd = poly_at(loop, u); f.dots(HOME, feet_pts(fp, fd), AMB, 2)
        ov = ramp(t, T * 0.45, T * 0.95)
        if ov > 0:
            nd = int(1 + ov * 7)
            for j in range(nd):
                c = (2 + rng.uniform(0, 6), 1.2 + rng.uniform(0, 4)); rr = 0.25 + rng.uniform(0, 0.3)
                pts = [(c[0] + rr * math.cos(a), c[1] + rr * 0.8 * math.sin(a)) for a in np.linspace(0, 4 * math.pi, 40)]
                f.line(HOME, pts, AMB, 0.35)
            rng = np.random.default_rng(8); obst = [(2.0 + rng.uniform(0, 6), 1.3 + rng.uniform(0, 3.8)) for _ in range(6)]
            door = (0.75, 5.95); f.dots(HOME, [door], AMB, int(3 + 6 * ov), a=0.5 + 0.5 * ov, glow=2.5 * ov)
            for j, o in enumerate(obst[:int(ov * 6.99)]):
                ang = np.linspace(0, 2 * np.pi, 10); f.points(HOME, np.array([(o[0] + 0.07 * math.cos(a), o[1] + 0.07 * math.sin(a)) for a in ang]), 1.2, WALL, 1.4)
        f.vac(HOME, np.array([3.2, 0.42]), (0, 1), t * 0.3, led=GRN * 0.6 + AMB * 0.4)
        yield f.out(ramp(t, 0, 0.4) * (1 - ramp(t, T - 0.3, T)), t)

GHOST = [((1.0, 1.0), (1.0, 4.2)), ((1.0, 4.2), (4.8, 4.2)), ((4.8, 4.2), (4.8, 1.0)), ((4.8, 1.0), (1.0, 1.0)),
         ((2.9, 1.0), (2.9, 2.4)), ((4.8, 2.6), (8.4, 2.6)), ((8.4, 2.6), (8.4, 5.4)), ((8.4, 5.4), (4.8, 5.4)), ((4.8, 4.2), (4.8, 5.4))]
GPATH = [(1.6, 1.6), (1.6, 3.6), (4.2, 3.6), (4.2, 3.1), (6.4, 3.1), (6.4, 4.8), (7.8, 4.8), (7.8, 3.2)]
def shot_ghost(T):
    """유령 평면도: 발자취가 벽을 지나 직각으로 꺾이며 걷고, 그 길을 따라 이 집에 없는 방들이 떠오른다."""
    for k in range(int(T * FPS)):
        t = k / FPS; f = Frame(0.6); f.floor(HOME, HOME_FLOOR, 0.7); f.points(HOME, FULL, 0.42 * (1 - 0.4 * ramp(t, T * 0.5, T * 0.8)))
        u = ramp(t, 0, T * 0.6); f.line(HOME, poly_upto(GPATH, u), AMB, 0.9, 2)
        fp, fd = poly_at(GPATH, u); f.dots(HOME, feet_pts(fp, fd), AMB, 2)
        g = ramp(t, T * 0.45, T * 0.85)
        for a, b in GHOST:
            n = int(max(2, np.hypot(b[0] - a[0], b[1] - a[1]) / 0.12)); pts = np.linspace(a, b, n)
            f.line(HOME, pts, AMB, 0.55 * g, 1, glow=0.8, dashed=True)
        f.vac(HOME, np.array([3.2, 0.42]), (0, 1), t * 0.3)
        yield f.out(ramp(t, 0, 0.3), t)

def shot_reset(T):
    """초기화: 점들이 흩어지며 사라지고, 어둠."""
    rng = np.random.default_rng(2); vel = rng.normal(0, 1, FULL.shape); vel /= np.linalg.norm(vel, axis=1, keepdims=True); vel *= rng.uniform(0.5, 3, (len(FULL), 1))
    for k in range(int(T * FPS)):
        t = k / FPS; u = ramp(t, 0.6, 3.2); f = Frame(1 - 0.3 * u)
        f.floor(HOME, HOME_FLOOR, 1 - sm(ramp(t, 0.4, 1.6)))
        P = FULL + vel * (u ** 1.6) * 1.5; f.points(HOME, P, 0.55 * (1 - sm(u)) + 0.8 * (1 - sm(ramp(t, 0.6, 1.0))) * (t > 0.6))
        f.vac(HOME, np.array([3.2, 0.42]), (0, 1), t, led=AMB if t < 3.5 else GRN, a=1 - 0.5 * ramp(t, 3.5, 4.5))
        yield f.out(1 - sm(ramp(t, 3.4, T)), t)

EXITP = [(1.4, 1.75), (2.2, 3.0), (1.8, 4.0), (1.0, 5.2), (0.75, 6.0), (0.75, 6.6), (0.2, 7.05), (-1.0, 7.1)]
def live_map(f, v, p, hits, seen, t, segs, cirs, rng, rr=2.2, amber=None):
    ang = np.linspace(0, 2 * np.pi, 700, endpoint=False) + rng.uniform(0, 0.009, 700) + t * 9
    cs = list(cirs) + ([(amber[0], amber[1], 0.12, 1)] if amber is not None else [])
    P, kd, h = cast(np.asarray(p, float), ang, segs, cs, rr)
    for c in cells(P[h & (kd != 2)]): hits.setdefault(c, t)
    poly = np.round((P[np.argsort(ang)] + np.array([5, 0])) / 0.04).astype(np.int32); cv2.fillPoly(seen, [poly], 1)
    return P[h & (kd == 2)]
def draw_live(f, v, hits, seen, t):
    f.floor_mask(v, seen, 0.04, 1.0) if False else None
    if hits:
        ks = np.array(list(hits.keys()), float) * G; ts = np.array(list(hits.values())); f.points(v, ks, 0.5 + 1.0 * np.exp(-(t - ts) * 3))
def seen_floor(f, v, seen):
    m = cv2.resize(seen.astype(np.float32), None, fx=0.04 * v.z, fy=0.04 * v.z, interpolation=cv2.INTER_LINEAR)[::-1]
    oy = IH / 2 - (seen.shape[0] * 0.04 - v.c[1]) * v.z; ox = IW / 2 - (v.c[0] + 5) * v.z
    f.img += cv2.GaussianBlur(cv2.warpAffine(m, np.float32([[1, 0, ox], [0, 1, oy]]), (IW, IH)), (0, 0), 2 * SS)[..., None] * FLOOR * 0.42

def shot_exit(T):
    """지워진 지도의 밤: 빈 화면에 청소기가 새로 보는 점들만. 호박색 발이 현관문 틈으로 나가 지도 밖 어둠으로 사라진다."""
    hits = {}; seen = np.zeros((int(9 / 0.04), int(16 / 0.04)), np.uint8); rng = np.random.default_rng(4)
    segs = SEG + DOOR_LEAF + CORR; v = View(95, (2.6, 4.0))
    for k in range(int(T * FPS)):
        t = k / FPS; u = ramp(t, 0.5, T * 0.8); fp, fd = poly_at(EXITP, u)
        vp = np.array([2.4, 2.6]); vd = (fp - vp) / max(1e-6, np.linalg.norm(fp - vp))
        f = Frame(0.8); seen_floor(f, v, seen)
        live_map(f, v, vp, hits, seen, t, segs, CIR, rng, 2.4)
        draw_live(f, v, hits, seen, t)
        vis = np.linalg.norm(fp - vp) < 2.4 and fp[1] < 6.25
        if vis: f.dots(v, feet_pts(fp, fd), AMB, 2)
        else:
            fade = 1 - ramp(t, 0, 99)
        f.vac(v, vp, vd, t, led=GRN * (1 - ramp(t, T * 0.6, T * 0.8)) + AMB * ramp(t, T * 0.6, T * 0.8))
        yield f.out(ramp(t, 0, 0.4), t)

SEARCH = [(2.4, 2.6), (2.1, 3.6), (1.4, 4.8), (0.8, 5.8), (0.75, 6.6), (0.0, 7.05), (-1.2, 7.05), (-1.9, 7.0)]
FOUND = np.array([-2.15, 7.05])
def shot_search(T):
    """희미한 슬리퍼 자국을 따라 문턱을 넘고, 복도와 계단을 처음 그리며, 계단 끝의 호박색 점을 찾는다."""
    hits = {}; seen = np.zeros((int(9 / 0.04), int(16 / 0.04)), np.uint8); rng = np.random.default_rng(6)
    segs = SEG + DOOR_LEAF + CORR; resid = poly_upto(EXITP, 1, 200)
    for k in range(int(T * FPS)):
        t = k / FPS; u = ramp(t, 0.4, T * 0.82); vp, vd = poly_at(SEARCH, sm(u) * 0.85 + u * 0.15)
        v = View(lerp(100, 125, sm(u)), lerp(np.array([1.8, 4.4]), np.array([-0.9, 6.4]), sm(ramp(t, 0, T * 0.85))))
        f = Frame(0.8); seen_floor(f, v, seen)
        amb = live_map(f, v, vp, hits, seen, t, segs, CIR, rng, 2.4, amber=FOUND)
        draw_live(f, v, hits, seen, t)
        f.dots(v, resid[::4], AMB, 1, a=0.22, glow=0.5)                                  # 바닥에 남은 슬리퍼 길(먼지가 닦인 자국)
        if np.linalg.norm(FOUND - vp) < 2.4: f.dots(v, feet_pts(FOUND, (1, 0)), AMB, 2, a=1.0, glow=2.0)
        found = ramp(t, T * 0.82, T * 0.9)
        if found > 0: f.ring(v, FOUND, 0.15 + 0.6 * found, AMB, 0.8 * (1 - found))
        f.vac(v, vp, vd, t); yield f.out(ramp(t, 0, 0.3), t)

def shot_return(T):
    """함께 돌아옴: 새로 그린 복도 지도 위로 초록과 호박색 점이 나란히 집으로."""
    hits = {}; seen = np.zeros((int(9 / 0.04), int(16 / 0.04)), np.uint8); rng = np.random.default_rng(7)
    segs = SEG + DOOR_LEAF + CORR; back = SEARCH[::-1][:6]
    for p in SEARCH: live_map(None, None, p, hits, seen, 0, segs, CIR, rng, 2.4)
    v = View(105, (0.3, 5.6)); trailv, trailf = [], []
    for k in range(int(T * FPS)):
        t = k / FPS; u = sm(ramp(t, 0.2, T - 0.4))
        vp, vd = poly_at(back, u); fp, fd = poly_at(back, max(0, u - 0.07)); trailv.append(vp); trailf.append(fp)
        f = Frame(0.85); seen_floor(f, v, seen); draw_live(f, v, hits, seen, 99)
        f.line(v, np.array(trailf), AMB, 0.5); f.line(v, np.array(trailv), GRN, 0.3)
        f.dots(v, feet_pts(fp, fd), AMB, 2); f.vac(v, vp, vd, t)
        yield f.out(ramp(t, 0, 0.3) * (1 - ramp(t, T - 0.5, T)), t)

def shot_firstdot(T):
    """새 방: 검은 화면에 새 지도의 첫 점 하나."""
    v = View(150, (0, 0))
    for k in range(int(T * FPS)):
        t = k / FPS; f = Frame(1.0)
        a = sm(ramp(t, 1.0, 1.15)); f.points(v, np.array([[0.0, 0.0]]), 1.6 * a, WALL, 2.0)
        if t > 1.0: f.ring(v, (0, 0), 0.05 + 0.8 * sm(ramp(t, 1.0, 2.6)), WALL, 0.6 * (1 - ramp(t, 1.0, 2.6)))
        yield f.out(1.0, t)

SHOTS = {'firstmap': (shot_firstmap, 6), 'play': (shot_play, 8), 'routine': (shot_routine, 16), 'loops': (shot_loops, 10), 'ghost': (shot_ghost, 8),
         'reset': (shot_reset, 5), 'exit': (shot_exit, 8), 'search': (shot_search, 12), 'return': (shot_return, 5), 'firstdot': (shot_firstdot, 4)}

def render(name, out, stills=None):
    fn, T = SHOTS[name]
    if stills:
        want = {int(s * FPS) for s in stills}; ims = []
        for k, img in enumerate(fn(T)):
            if k in want: ims.append(img)
            if k >= max(want): break
        return ims
    ff = subprocess.Popen(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'bgr24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-',
                           '-c:v', 'libx264', '-crf', '20', '-pix_fmt', 'yuv420p', out], stdin=subprocess.PIPE)
    for img in fn(T): ff.stdin.write(img.tobytes())
    ff.stdin.close(); ff.wait(); print('done', name)

if __name__ == '__main__':
    name, out = sys.argv[1], sys.argv[2]
    if len(sys.argv) > 3:
        ims = render(name, out, [float(x) for x in sys.argv[3:]]); cv2.imwrite(out, np.vstack(ims))
    else: render(name, out)
