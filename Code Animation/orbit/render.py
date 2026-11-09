#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ORBIT (궤도) -- 60s code-generated animation.
Every frame is a pure function of time t. No state, no assets.
"""
import numpy as np, cv2, math, os, sys, subprocess, time
from PIL import Image, ImageDraw, ImageFont

cv2.setNumThreads(1)
F32 = np.float32
W, H, FPS, DUR = 1920, 1080, 30, 60.0
NF = int(DUR * FPS)
TM = 36.0                       # merge / impact time
K = np.array([960.0, 540.0])    # constellation centre
LOG_Z_END = 0.095

def S(a, b, t):
    x = np.clip((np.asarray(t, dtype=np.float64) - a) / (b - a), 0.0, 1.0)
    return x * x * (3 - 2 * x)

COL_A = np.array([0.18, 0.50, 1.00], F32)
COL_B = np.array([1.00, 0.46, 0.12], F32)
COL_V = np.array([0.66, 0.30, 1.00], F32)

def mix(c1, c2, m):
    m = np.asarray(m, F32)[..., None]
    return (np.asarray(c1, F32) * (1 - m) + np.asarray(c2, F32) * m).astype(F32)

# ---------------------------------------------------------------- time tables
TT = np.linspace(0, DUR + 2, (int(DUR) + 2) * 600 + 1)
def _cum(om):
    return np.concatenate([[0.0], np.cumsum((om[1:] + om[:-1]) * 0.5 * np.diff(TT))])
TH_ORB = _cum(0.9 + 6.0 * S(14, 35.7, TT) ** 2)
PH5 = _cum(np.where(TT >= 44, 0.55 + 1.8 * S(52, 55, TT) ** 2, 0.0))
def theta_orb(t): return np.interp(t, TT, TH_ORB)
def phase5(t): return 2.84 + np.interp(t, TT, PH5)

# ---------------------------------------------------------------- paths
def center_C(t):
    t = np.asarray(t, float)
    return np.stack([960 + 55 * np.sin(0.21 * t), 540 + 28 * np.sin(0.17 * t + 1.0)], -1)

def R_orb(t):
    t = np.asarray(t, float)
    s = S(13, 35.6, t)
    R = 45 + 365 * (1 - s) ** 1.7
    R = R * (1 + 0.05 * np.sin(2.3 * t + 0.7)) * (1 - S(35.6, 36.0, t))
    return R

def orbit_off(t):
    t = np.asarray(t, float)
    R = R_orb(t); th = theta_orb(t); tl = 0.95 + 0.25 * np.sin(0.15 * t)
    ox = R * np.cos(th); oy = R * np.sin(th) * np.cos(tl); z = R * np.sin(th) * np.sin(tl)
    p = 1 + 0.0011 * z
    return np.stack([ox * p, oy * p], -1), z

def A_w(t):
    t = np.asarray(t, float)
    return np.stack([640 + 190 * np.sin(0.37 * t + 0.6) + 70 * np.sin(0.91 * t + 2.0),
                     560 + 130 * np.sin(0.29 * t) + 55 * np.sin(0.77 * t + 1.1)], -1)

def B_w(t):
    t = np.asarray(t, float)
    return np.stack([1320 + 170 * np.sin(0.31 * t + 2.4) + 60 * np.sin(0.83 * t + 0.3),
                     400 + 120 * np.sin(0.33 * t + 1.0) + 45 * np.sin(0.71 * t + 2.2)], -1)

CM = center_C(TM)
DIR_A = np.array([-0.976, 0.217])

def A_p5(t):
    t = np.asarray(t, float)
    R = (330 - 90 * S(46, 54, t)) * (1 - S(52.5, 55.1, t)) ** 1.2
    ph = phase5(t); rot = 0.35
    x = R * np.cos(ph); y = R * np.sin(ph) * 0.62
    xr = x * math.cos(rot) - y * math.sin(rot); yr = x * math.sin(rot) + y * math.cos(rot)
    return K + np.stack([xr, yr], -1)

def A_pos(t):
    t = np.asarray(t, float)
    off, _ = orbit_off(t)
    w12 = S(11.5, 22, t)[..., None]
    Pa = A_w(t) * (1 - w12) + (center_C(t) + off) * w12
    k = np.clip(t - TM, 0, None)
    u3 = (1 - np.exp(-0.75 * k))
    PERP_A = np.array([-DIR_A[1], DIR_A[0]])
    P3 = CM + DIR_A * 546 * u3[..., None] + PERP_A * (170 * np.sin(np.pi * u3))[..., None]
    P3 = P3 + np.stack([14 * np.sin(0.8 * t), 10 * np.sin(0.6 * t + 1)], -1) * S(37, 40, t)[..., None]
    w34 = S(41.5, 47.5, t)[..., None]
    Pb = P3 * (1 - w34) + A_p5(t) * w34
    return np.where((t < TM)[..., None], Pa, Pb)

def B_pos(t):
    t = np.asarray(t, float)
    off, _ = orbit_off(t)
    w12 = S(11.5, 22, t)[..., None]
    Pa = B_w(t) * (1 - w12) + (center_C(t) - off) * w12
    jit = np.stack([5 * np.sin(31 * t), 5 * np.cos(27 * t)], -1) * S(TM, TM + 0.3, t)[..., None]
    return np.where((t < TM)[..., None], Pa, CM + jit)

def depth_z(t):
    t = np.asarray(t, float)
    _, z = orbit_off(t)
    return np.where(t < TM, z, 0.0)

def intA(t):
    t = np.asarray(t, float)
    base = S(0.8, 3.2, t)
    dim = 1 - 0.5 * S(36.0, 37.0, t) * (1 - S(44, 50, t))
    return base * dim * (1 - S(54.7, 55.4, t))

def colA(t):
    t = np.asarray(t, float)
    m = 0.6 * S(22, 35.6, t) * (t < TM) + 0.9 * S(52.5, 55.2, t) + 0.06
    return mix(COL_A, COL_V, np.clip(m, 0, 1))

def intB(t):
    t = np.asarray(t, float)
    return S(10.0, 10.8, t) * (1 - S(36.15, 37.3, t))

def colB(t):
    t = np.asarray(t, float)
    return mix(COL_B, COL_V, 0.45 * S(22, 35.6, t))

# ---------------------------------------------------------------- galaxy
GAL_R = 7000.0
def build_galaxy():
    rng = np.random.default_rng(11)
    a, b = 380.0, 0.30
    n_arm = 70000
    u = rng.random(n_arm); r = GAL_R * u ** 1.35 + 120
    arm = rng.integers(0, 2, n_arm)
    th = np.log(r / a) / b + arm * np.pi
    th = th + rng.normal(0, 1, n_arm) * (0.16 + 0.22 * (r / GAL_R) ** 0.6)
    rr = r * (1 + rng.normal(0, 0.035, n_arm))
    g_arm = np.stack([rr * np.cos(th), rr * np.sin(th)], -1)
    c_arm = mix(np.array([1.0, 0.78, 0.52]), np.array([0.55, 0.72, 1.0]), (r / GAL_R) ** 0.6)
    w_arm = 0.10 + 0.9 * rng.random(n_arm) ** 4
    knot = rng.random(n_arm) < 0.05
    c_arm[knot] = np.array([0.95, 0.35, 0.85], F32); w_arm[knot] *= 1.8
    n_b = 28000
    g_b = rng.normal(0, 700, (n_b, 2))
    c_b = np.tile(np.array([1.0, 0.82, 0.58], F32), (n_b, 1))
    w_b = 0.12 + 0.8 * rng.random(n_b) ** 4
    n_h = 30000
    rh = GAL_R * 1.05 * np.sqrt(rng.random(n_h)); ah = rng.random(n_h) * 2 * np.pi
    g_h = np.stack([rh * np.cos(ah), rh * np.sin(ah)], -1)
    c_h = mix(np.array([0.9, 0.8, 0.7]), np.array([0.6, 0.72, 1.0]), np.clip(rh / GAL_R, 0, 1))
    w_h = 0.04 + 0.2 * rng.random(n_h)
    g = np.concatenate([g_arm, g_b, g_h]); c = np.concatenate([c_arm, c_b, c_h]).astype(F32)
    w = np.concatenate([w_arm, w_b, w_h]).astype(F32)
    phi = 0.55
    Rm = np.array([[math.cos(phi), -math.sin(phi)], [math.sin(phi), math.cos(phi)]])
    M = Rm @ np.diag([1.0, 0.58])
    rk = 4300.0; thk = math.log(rk / a) / b
    gk = np.array([rk * math.cos(thk), rk * math.sin(thk)])
    G = K - M @ gk
    Xw = (G + g @ M.T).astype(F32)
    return Xw, c, w, G

GX, GC, GW, GCEN = build_galaxy()

# ---------------------------------------------------------------- camera
def cam_zoom(t):
    t = float(t)
    if t < TM:
        z = (1.0 + 0.05 * S(0, 12, t) - 0.05 * S(12, 22, t)
             + 1.3 * S(20.25, 35.6, t) ** 1.4 + 0.15 * S(35.6, 36.0, t))
    else:
        z = 1.15 + 1.3 * math.exp(-(t - TM) / 1.3) + 0.2 * S(41, 55.5, t)
    T0, T1 = 55.9, 59.9
    if t > T0:
        zs = 1.15 + 1.3 * math.exp(-(T0 - TM) / 1.3) + 0.2 * S(41, 55.5, T0)
        u = min(1.0, (t - T0) / (T1 - T0)); u = float(S(0, 1, u)); e = 1 - (1 - u) ** 2
        z = math.exp(math.log(zs) * (1 - e) + math.log(LOG_Z_END) * e)
    return float(z)

def pull_e(t):
    T0, T1 = 55.9, 59.9
    u = min(1.0, max(0.0, (t - T0) / (T1 - T0))); u = float(S(0, 1, u))
    return 1 - (1 - u) ** 2

def cam_center(t):
    t = float(t)
    if t < TM:
        base = np.array([960 + 25 * math.sin(0.13 * t), 540 + 22 * math.cos(0.11 * t)])
        w = float(S(20, 28, t))
        c = base * (1 - w) + center_C(t) * w
    else:
        w = float(S(36.5, 41, t))
        c = CM * (1 - w) + K * w + np.array([18 * math.sin(0.2 * t), 12 * math.cos(0.17 * t)]) * w
    e = pull_e(t)
    if e > 0:
        c = c * (1 - e) + (K + 0.55 * (GCEN - K)) * e
    return c

def cam_shake(t):
    t = float(t); sx = sy = 0.0
    if t >= TM:
        a = 24 * math.exp(-(t - TM) / 0.45)
        sx += a * math.sin(61 * t); sy += a * math.cos(53 * t + 1.0)
    if t >= 55.5:
        a = 7 * math.exp(-(t - 55.5) / 0.35)
        sx += a * math.sin(47 * t); sy += a * math.cos(43 * t)
    if 35.2 < t < TM:
        a = 3.0 * S(35.2, TM, t)
        sx += a * math.sin(71 * t); sy += a * math.cos(67 * t)
    return sx, sy

# ---------------------------------------------------------------- primitives
def splat(px, py, pc):
    """bilinear additive splat of N weighted rgb points -> (H,W,3) float32"""
    x0 = np.floor(px).astype(np.int32); y0 = np.floor(py).astype(np.int32)
    fx = (px - x0).astype(F32); fy = (py - y0).astype(F32)
    idx = []; wts = []
    for dx, dy, wg in ((0, 0, (1 - fx) * (1 - fy)), (1, 0, fx * (1 - fy)),
                       (0, 1, (1 - fx) * fy), (1, 1, fx * fy)):
        xi = x0 + dx; yi = y0 + dy
        ok = (xi >= 0) & (xi < W) & (yi >= 0) & (yi < H)
        idx.append((yi[ok] * W + xi[ok]).astype(np.int64))
        wts.append(pc[ok] * wg[ok][:, None])
    idx = np.concatenate(idx); wts = np.concatenate(wts)
    out = np.empty((H * W, 3), F32)
    for ch in range(3):
        out[:, ch] = np.bincount(idx, weights=wts[:, ch], minlength=H * W)
    return out.reshape(H, W, 3)

def add_blob(L, x, y, sig, col, amp):
    R = int(sig * 4) + 2
    x0 = int(round(x)); y0 = int(round(y))
    xs0 = max(x0 - R, 0); xs1 = min(x0 + R + 1, W); ys0 = max(y0 - R, 0); ys1 = min(y0 + R + 1, H)
    if xs0 >= xs1 or ys0 >= ys1: return
    xx = np.arange(xs0, xs1, dtype=F32) - F32(x); yy = np.arange(ys0, ys1, dtype=F32) - F32(y)
    d2 = (yy[:, None] ** 2 + xx[None, :] ** 2) / F32(sig * sig)
    g = np.maximum(np.exp(-0.5 * d2) - F32(math.exp(-8)), 0)
    L[ys0:ys1, xs0:xs1] += g[..., None] * (np.asarray(col, F32) * F32(amp))

def add_streak(L, x, y, length, thick, col, amp, vertical=False):
    R = int(length * 6) + 2; T = int(thick * 4) + 2
    x0 = int(round(x)); y0 = int(round(y))
    if vertical:
        xs0 = max(x0 - T, 0); xs1 = min(x0 + T + 1, W); ys0 = max(y0 - R, 0); ys1 = min(y0 + R + 1, H)
    else:
        xs0 = max(x0 - R, 0); xs1 = min(x0 + R + 1, W); ys0 = max(y0 - T, 0); ys1 = min(y0 + T + 1, H)
    if xs0 >= xs1 or ys0 >= ys1: return
    xx = np.arange(xs0, xs1, dtype=F32) - F32(x); yy = np.arange(ys0, ys1, dtype=F32) - F32(y)
    if vertical: xx, yy = yy, xx
    along = np.maximum(np.exp(-np.abs(xx) / F32(length)) * (1 - np.abs(xx) / F32(6 * length)), 0)
    across = np.exp(-(yy / F32(thick)) ** 2)
    prof = (across[:, None] * along[None, :])
    if vertical: prof = prof.T
    L[ys0:ys1, xs0:xs1] += prof[..., None] * (np.asarray(col, F32) * F32(amp))

def ring_points(cx, cy, r, n, spread, rng_state):
    a = np.linspace(0, 2 * np.pi, n, endpoint=False) + rng_state.random(n) * (2 * np.pi / n)
    rr = r + rng_state.normal(0, spread, n)
    return cx + rr * np.cos(a), cy + rr * np.sin(a), a

# ---------------------------------------------------------------- static data
_rng = np.random.default_rng(2026)

# background dust stars
NS = 1700
S_x = _rng.random(NS) * W; S_y = _rng.random(NS) * H
S_d = 0.25 + 0.75 * _rng.random(NS)
S_w = 0.12 + 2.6 * _rng.random(NS) ** 6
S_ph = _rng.random(NS) * 6.28; S_f = 0.5 + 2.5 * _rng.random(NS)
S_col = mix(np.array([0.8, 0.88, 1.0]), np.array([1.0, 0.9, 0.78]), _rng.random(NS) ** 2)
S_dr = np.stack([4 + 6 * _rng.random(NS), 1.5 * _rng.normal(0, 1, NS)], -1)

# nebula fields (quarter-res)
def fbm(rng, h, w):
    out = np.zeros((h, w), F32); amp = 1.0
    for o in range(6):
        gh = 3 * 2 ** o; gw = int(gh * w / h) + 2
        r = rng.random((gh, gw)).astype(F32)
        out += cv2.resize(r, (w, h), interpolation=cv2.INTER_CUBIC) * amp; amp *= 0.55
    out = (out - out.min()) / (out.max() - out.min())
    return np.clip((out - 0.42) / 0.38, 0, 1) ** 1.7
_nr = np.random.default_rng(5)
NEB1 = fbm(_nr, 300, 520); NEB2 = fbm(_nr, 300, 520)

# sparks emitted by the orbs
def _make_sparks(t0, t1, dens_fn, n_seed, posfn, colfn, intfn, rng):
    g = np.linspace(t0, t1, 4000); d = dens_fn(g); c = np.cumsum(d); c /= c[-1]
    tb = np.sort(np.interp(rng.random(int(d.mean() * (t1 - t0))), c, g))
    n = len(tb)
    ang = rng.random(n) * 2 * np.pi; spd = 8 + 50 * rng.random(n)
    return dict(tb=tb, P0=posfn(tb), V=np.stack([np.cos(ang), np.sin(ang)], -1) * spd[:, None],
                life=0.8 + 1.8 * rng.random(n), w0=(0.35 + 0.65 * rng.random(n)) * intfn(tb),
                col=colfn(tb), z=depth_z(tb))
_sp_rng = np.random.default_rng(99)
SPK_A = _make_sparks(0.8, 55.3, lambda t: np.where(t < TM, 60 + 160 * S(14, 35, t), 25 + 90 * S(52.5, 55, t)),
                     0, A_pos, colA, intA, _sp_rng)
SPK_B = _make_sparks(10.0, 36.3, lambda t: 60 + 180 * S(14, 35, t), 0, B_pos, colB, intB, _sp_rng)

# dissolve (B remnants) -> constellation
ND = 2800
D_tb = TM + 2.6 * _rng.random(ND) ** 1.7
_a = _rng.random(ND) * 2 * np.pi
D_spd = 60 + 360 * _rng.random(ND) ** 1.6
D_k = 0.8 + 0.9 * _rng.random(ND)
D_o = CM + _rng.normal(0, 10, (ND, 2))
D_v = np.stack([np.cos(_a), np.sin(_a)], -1) * D_spd[:, None]
D_ph = _rng.random(ND) * 6.28
D_base = 0.25 + 0.55 * _rng.random(ND)
D_cd = 44.6 + 5.0 * _rng.random(ND); D_dur = 3.5 + 2.2 * _rng.random(ND)
D_curl = _rng.choice([-1.0, 1.0], ND)

ELL = [(380.0, 210.0, 0.42), (380.0, 210.0, -0.42)]
def ellipse_local(e, phi):
    rx, ry, rot = ELL[e]
    x = rx * np.cos(phi); y = ry * np.sin(phi)
    nx = np.cos(phi) / rx; ny = np.sin(phi) / ry; nn = np.hypot(nx, ny)
    return x, y, nx / nn, ny / nn, rot
def _rotv(x, y, rot):
    return x * math.cos(rot) - y * math.sin(rot), x * math.sin(rot) + y * math.cos(rot)
_e = _rng.integers(0, 2, ND); _phi = _rng.random(ND) * 2 * np.pi; _sg = _rng.normal(0, 1, ND) * (7 + 9 * _rng.random(ND))
D_g0 = np.zeros((ND, 2))
for i in range(2):
    m = _e == i
    x, y, nx, ny, rot = ellipse_local(i, _phi[m])
    xr, yr = _rotv(x + nx * _sg[m], y + ny * _sg[m], rot)
    D_g0[m, 0] = xr; D_g0[m, 1] = yr

# constellation main stars (12 per ellipse)
C_STAR = []; C_E = []
for e in range(2):
    base = np.linspace(0, 2 * np.pi, 12, endpoint=False) + (0.0 if e == 0 else 0.26) + _rng.normal(0, 0.07, 12)
    x, y, _, _, rot = ellipse_local(e, base)
    xr, yr = _rotv(x, y, rot)
    for j in range(12):
        C_STAR.append((xr[j], yr[j])); C_E.append(e)
C_STAR = np.array(C_STAR)                  # relative to K, index = e*12 + j
C_T = np.zeros(24)
_order = [0, 12, 1, 13, 2, 14, 3, 15, 4, 16, 5, 17, 6, 18, 7, 19, 8, 20, 9, 21, 10, 22, 11, 23]
for k, idx in enumerate(_order): C_T[idx] = 46.0 + 0.32 * k
C_W = 0.6 + 0.9 * _rng.random(24); C_PH = _rng.random(24) * 6.28
def ang_c(t): return 0.025 * max(0.0, t - 44.0)

# fixed grain pool
GRAIN = [(_rng.random((H, W)).astype(F32) + _rng.random((H, W)).astype(F32) - 1.0) for _ in range(6)]
_yy, _xx = np.mgrid[0:H, 0:W].astype(F32)
VIG = (1.0 - 0.52 * (((_xx - W / 2) / (W / 2)) ** 2 * 0.7 + ((_yy - H / 2) / (H / 2)) ** 2) ** 1.1).astype(F32)
VIG = np.clip(VIG, 0.25, 1.0)[..., None]

# ---------------------------------------------------------------- text
FONT_P = '/usr/share/fonts/opentype/noto/NotoSerifCJK-Light.ttc'
def _text_layer(s, size, track, y_center, x_center=W / 2):
    font = ImageFont.truetype(FONT_P, size, index=1)
    adv = [font.getlength(ch) + track for ch in s]
    total = sum(adv) - track
    x = x_center - total / 2
    chars = []
    for ch, a in zip(s, adv):
        if ch.strip():
            im = Image.new('L', (int(size * 2.2), int(size * 2.2)), 0)
            ImageDraw.Draw(im).text((size * 0.6, size * 0.4), ch, font=font, fill=255)
            arr = np.asarray(im, F32) / 255.0
            chars.append((arr, int(round(x - size * 0.6)), int(round(y_center - size * 1.1))))
        x += a
    return chars
TXT_SUB = _text_layer('사라진 빛은, 다른 빛이 된다.', 54, 10, 930)
TXT_TITLE = _text_layer('궤도  ·  ORBIT', 30, 14, 985)
TXT_CRED = _text_layer('GoXoN × Claude   —   every frame is code', 20, 6, 1030)

def _comp_chars(img, chars, alphas, col, glow=0.7, blur=0.0):
    """screen-blend char masks into img (float RGB 0..1)"""
    if not chars: return
    ys = [c[2] for c in chars]; xs = [c[1] for c in chars]
    ph, pw = chars[0][0].shape
    y0 = max(min(ys), 0); y1 = min(max(ys) + ph, H); x0 = max(min(xs), 0); x1 = min(max(xs) + pw, W)
    roi = np.zeros((y1 - y0, x1 - x0), F32)
    for (arr, cx, cy), a in zip(chars, alphas):
        if a <= 0.002: continue
        yy0 = cy - y0; xx0 = cx - x0
        roi[yy0:yy0 + ph, xx0:xx0 + pw] = np.maximum(roi[yy0:yy0 + ph, xx0:xx0 + pw], arr * F32(a))
    if roi.max() < 0.003: return
    if blur > 0.3: roi = cv2.GaussianBlur(roi, (0, 0), blur)
    gl = cv2.GaussianBlur(roi, (0, 0), 14) * F32(glow)
    m = np.clip(roi + gl, 0, 1)[..., None]
    sub = img[y0:y1, x0:x1]
    img[y0:y1, x0:x1] = 1 - (1 - sub) * (1 - m * np.asarray(col, F32))

def draw_text(img, t):
    # title
    if t < 8:
        al = float(S(1.2, 3.0, t) * (1 - S(5.5, 7.5, t))) * 1.0
        _comp_chars(img, TXT_TITLE, [al * float(S(1.2 + 0.05 * i, 2.6 + 0.05 * i, t)) for i in range(len(TXT_TITLE))],
                    (0.75, 0.82, 1.0), glow=0.5, blur=0.0)
    # subtitle
    t0 = 56.4
    if t > t0 - 0.2:
        n = len(TXT_SUB)
        al = [float(S(t0 + 0.11 * i, t0 + 0.11 * i + 1.0, t)) for i in range(n)]
        prog = float(S(t0, t0 + 0.11 * n + 1.0, t))
        _comp_chars(img, TXT_SUB, al, (0.97, 0.93, 1.0), glow=0.9, blur=7.0 * (1 - prog) ** 2)
    if t > 58.0:
        _comp_chars(img, TXT_CRED, [0.62 * float(S(58.2 + 0.03 * i, 59.0 + 0.03 * i, t)) for i in range(len(TXT_CRED))],
                    (0.78, 0.74, 0.95), glow=0.25)

# ---------------------------------------------------------------- frame
def render_frame(i):
    t = i / FPS
    z = cam_zoom(t); cc = cam_center(t); sx, sy = cam_shake(t)
    ox = 960 + sx - cc[0] * z; oy = 540 + sy - cc[1] * z
    def proj(P):
        P = np.asarray(P, float)
        return np.stack([P[..., 0] * z + ox, P[..., 1] * z + oy], -1)
    zs = z ** 0.5
    gal_a = float(1 - S(0.25, 0.8, z))

    PX = []; PY = []; PC = []
    def add_pts(x, y, c):
        PX.append(np.asarray(x, F32).ravel()); PY.append(np.asarray(y, F32).ravel()); PC.append(np.asarray(c, F32).reshape(-1, 3))

    # --- background dust stars (screen space w/ parallax)
    sa = float(S(0, 2.5, t)) * (1 - 0.6 * gal_a)
    px = S_x + S_dr[:, 0] * t * S_d - (cc[0] - 960) * S_d * 0.35 + sx * S_d
    py = S_y + S_dr[:, 1] * t * S_d - (cc[1] - 540) * S_d * 0.35 + sy * S_d
    sc = z ** (0.2 * S_d)
    px = (px - 960) * sc + 960; py = (py - 540) * sc + 540
    px = np.mod(px, W); py = np.mod(py, H)
    tw = 0.7 + 0.3 * np.sin(S_f * t * 2.1 + S_ph)
    add_pts(px, py, S_col * (S_w * tw * sa * (0.25 + 0.75 * S_d))[:, None])

    # --- galaxy
    if gal_a > 0.003:
        gp = proj(GX)
        ok = (gp[:, 0] > -5) & (gp[:, 0] < W + 5) & (gp[:, 1] > -5) & (gp[:, 1] < H + 5)
        add_pts(gp[ok, 0], gp[ok, 1], GC[ok] * (GW[ok] * gal_a * 0.9)[:, None])

    # --- orbit guide ellipse
    ga = float(S(20, 28, t) * (1 - S(35.6, 36.0, t)))
    if ga > 0.01:
        phs = np.linspace(0, 2 * np.pi, 900, endpoint=False)
        Rg = float(R_orb(t)); tl = 0.95 + 0.25 * math.sin(0.15 * t); Cc = center_C(t)
        gp = proj(np.stack([Cc[0] + Rg * np.cos(phs), Cc[1] + Rg * np.sin(phs) * math.cos(tl)], -1))
        dash = 0.55 + 0.45 * np.sin(18 * phs - theta_orb(t) * 3)
        add_pts(gp[:, 0], gp[:, 1], np.tile(np.array([0.5, 0.55, 0.9], F32), (900, 1)) * (0.05 * ga * dash)[:, None])

    # --- trails
    def trail(posf, intf, colf, T, gain, depthfun=None):
        n = int(T / 0.012) + 1
        ts = t - np.linspace(0, T, n)
        scr = proj(posf(ts))
        seg = np.hypot(np.diff(scr[:, 0]), np.diff(scr[:, 1]))
        cum = np.concatenate([[0.0], np.cumsum(seg + 1e-6)])
        tot = cum[-1]
        if tot < 1: return
        m = int(min(tot / 0.8, 14000)) + 2
        s = np.linspace(0, tot, m)
        x = np.interp(s, cum, scr[:, 0]); y = np.interp(s, cum, scr[:, 1])
        uu = np.interp(s, cum, np.linspace(0, 1, n))
        iv = np.interp(s, cum, intf(ts))
        cl = colf(ts)
        col = np.stack([np.interp(s, cum, cl[:, k]) for k in range(3)], -1)
        wgt = iv * (1 - uu) ** 1.8 * gain
        if depthfun is not None:
            zz = np.interp(s, cum, depthfun(ts)); wgt = wgt * np.clip(1 + 0.0012 * zz, 0.55, 1.5)
        add_pts(x, y, col * wgt[:, None])
    T_A = 3.6 + 2.0 * float(S(44, 48, t))
    trail(A_pos, intA, colA, T_A, 1.15, depth_z)
    if t > 10: trail(B_pos, intB, colB, 3.6, 1.15, lambda q: -depth_z(q))

    # --- tether between orbs
    tw_ = float(S(17, 28, t) * (1 - S(35.7, 36.0, t)))
    if tw_ > 0.01:
        a_ = proj(A_pos(t)); b_ = proj(B_pos(t))
        ln = float(np.hypot(*(b_ - a_)))
        if ln > 4:
            m = int(ln / 0.8) + 2; s = np.linspace(0, 1, m)
            d = (b_ - a_) / ln; nrm = np.array([-d[1], d[0]])
            wob = (12 * z * math.sin(math.pi * 1) ) * 0
            sag = np.sin(np.pi * s) * (16 * zs * np.sin(5 * np.pi * s - 7 * t) * np.sin(1.3 * t) + 22 * zs * np.sin(1.7 * t))
            x = a_[0] + (b_[0] - a_[0]) * s + nrm[0] * sag; y = a_[1] + (b_[1] - a_[1]) * s + nrm[1] * sag
            c = mix(colA(t), colB(t), s)[0] if False else (colA(t)[None, :] * (1 - s[:, None]) + colB(t)[None, :] * s[:, None])
            sh = 0.55 + 0.45 * np.sin(2 * np.pi * (7 * s) - 9 * t)
            add_pts(x, y, c * (0.20 * tw_ * sh * np.sin(np.pi * s) ** 0.6)[:, None])

    # --- sparks
    for SP, which in ((SPK_A, 'A'), (SPK_B, 'B')):
        tb = SP['tb']
        i0 = np.searchsorted(tb, t - 2.7); i1 = np.searchsorted(tb, t, 'right')
        if i1 > i0:
            a = t - tb[i0:i1]; life = SP['life'][i0:i1]; ok = a < life
            a = a[ok]
            if len(a):
                P0 = SP['P0'][i0:i1][ok]; V = SP['V'][i0:i1][ok]
                pos = P0 + V * ((1 - np.exp(-1.5 * a)) / 1.5)[:, None]
                w = SP['w0'][i0:i1][ok] * (1 - a / life[ok]) ** 1.5 * 3.2
                scr = proj(pos)
                add_pts(scr[:, 0], scr[:, 1], SP['col'][i0:i1][ok] * w[:, None])

    # --- dissolve particles / constellation dust
    if t >= TM:
        a = t - D_tb; vis = a >= 0
        if vis.any():
            sel = np.where(vis)[0]
            aa = a[sel]
            d = D_o[sel] + D_v[sel] * ((1 - np.exp(-D_k[sel] * aa)) / D_k[sel])[:, None]
            d = d + 5 * np.stack([np.sin(0.7 * t + D_ph[sel]), np.cos(0.6 * t + D_ph[sel] * 1.3)], -1)
            e = S(D_cd[sel], D_cd[sel] + D_dur[sel], t)
            ac = ang_c(t)
            gx, gy = _rotv(D_g0[sel, 0], D_g0[sel, 1], ac)
            g = K + np.stack([gx, gy], -1) + 2.5 * np.stack([np.sin(1.3 * t + D_ph[sel]), np.cos(1.1 * t + D_ph[sel])], -1)
            dv = g - d; dl = np.hypot(dv[:, 0], dv[:, 1]) + 1e-6
            perp = np.stack([-dv[:, 1], dv[:, 0]], -1) / dl[:, None]
            p = d * (1 - e)[:, None] + g * e[:, None] + perp * (D_curl[sel] * np.sin(np.pi * e) * 0.28 * dl)[:, None]
            hot = np.exp(-aa / 0.9)
            col = COL_B[None, :] * 1.0 + (np.array([1.0, 0.9, 0.7], F32) - COL_B)[None, :] * hot[:, None]
            col = col * np.array([1.0, 0.92, 0.85], F32)
            fin = float(S(55.4, 56.6, t)) * 0.75
            col = col * (1 - fin) + COL_V[None, :] * fin
            w = (D_base[sel] * 1.5 * (1 + 0.35 * np.sin(6.5 * t + D_ph[sel])) + 2.6 * hot) * (0.7 + 0.5 * e)
            w = w * (0.25 + 0.75 * min(1.0, z / 1.35))
            scr = proj(p)
            add_pts(scr[:, 0], scr[:, 1], col * w[:, None])

    # --- constellation stars + lines
    if t > 45.5:
        ac = ang_c(t)
        sxs, sys_ = _rotv(C_STAR[:, 0], C_STAR[:, 1], ac)
        spos = K + np.stack([sxs, sys_], -1)
        scr = proj(spos)
        act = S(C_T, C_T + 0.6, t)
        pulse = 2.2 * np.exp(-((t - (54.8 + 0.7 * np.hypot(C_STAR[:, 0], C_STAR[:, 1]) / 420.0)) ** 2) / 0.012)
        flash = 1.6 * np.exp(-np.clip(t - C_T, 0, None) / 0.5) * (t >= C_T)
        tw = 0.75 + 0.25 * np.sin(2.3 * t + C_PH)
        fin = float(S(55.4, 56.6, t)) * 0.8
        cs = (np.array([0.85, 0.92, 1.0], F32)[None, :] * (1 - fin) + COL_V[None, :] * fin)
        bw = 4.5 * C_W * act * tw * (1 + flash + pulse) * (0.35 + 0.65 * min(1.0, z / 1.35))
        add_pts(scr[:, 0], scr[:, 1], cs * bw[:, None])
        for e_ in range(2):
            for j in range(11):
                a_i = e_ * 12 + j; b_i = e_ * 12 + j + 1
                u = float(S(C_T[b_i], C_T[b_i] + 0.9, t))
                if u <= 0.01: continue
                pa = scr[a_i]; pb = scr[b_i]
                ln = float(np.hypot(*(pb - pa)))
                if ln < 2: continue
                m = int(ln * u / 0.9) + 2
                s = np.linspace(0, u, m)
                xx = pa[0] + (pb[0] - pa[0]) * s; yy = pa[1] + (pb[1] - pa[1]) * s
                add_pts(xx, yy, np.tile(cs[0], (m, 1)) * (0.085 * (0.4 + 0.6 * min(1.0, z / 1.35))))

    # --- shockwave rings (impact)
    rr_ = np.random.default_rng(i * 7 + 3)
    if TM <= t < TM + 3.2:
        a = t - TM
        c0 = proj(CM)
        for k, (delay, rate, amp) in enumerate(((0.0, 2.0, 1.0), (0.22, 1.7, 0.6), (0.5, 1.4, 0.35))):
            aa = a - delay
            if aa <= 0: continue
            r = 1300 * (1 - math.exp(-rate * 0.9 * aa))
            ampl = amp * math.exp(-aa / 1.1) * float(S(0, 0.05, aa))
            if ampl < 0.01 or r < 3: continue
            n = int(min(14000, max(600, 2 * math.pi * r / 0.9)))
            x, y, ang = ring_points(c0[0], c0[1], r, n, 2.2 + 5 * aa, rr_)
            mod = 1 + 0.35 * np.sin(5 * ang + 2 * k) * np.sin(3 * ang - k)
            colr = mix(np.array([1.0, 0.85, 0.7]), COL_V, min(1.0, aa / 1.2) * 0.7)
            add_pts(x, y, np.tile(colr, (n, 1)) * (ampl * 1.15 * mod * np.clip(2200.0 / n * 0.9, 0.18, 1.4))[:, None])

    # --- ignition rings & final pings (screen space around the new star)
    star_scr = proj(K)
    if t >= 55.5:
        a = t - 55.5
        for k, delay in enumerate((0.0, 0.3, 0.6)):
            aa = a - delay
            if aa <= 0: continue
            r = 520 * zs * (1 - math.exp(-1.7 * aa))
            ampl = (0.9 - 0.2 * k) * math.exp(-aa / 0.75)
            if ampl < 0.01 or r < 2: continue
            n = int(min(9000, max(500, 2 * math.pi * r / 1.0)))
            x, y, ang = ring_points(star_scr[0], star_scr[1], r, n, 1.8 + 3 * aa, rr_)
            add_pts(x, y, np.tile(mix(COL_V, np.array([1, 0.9, 1.0]), 0.4), (n, 1)) * (ampl * float(np.clip(2000.0 / n, 0.25, 1.3))))
    if t >= 57.4:
        per = 1.15; ph = (t - 57.4) % per; kidx = int((t - 57.4) // per)
        r = 5 + 95 * (1 - math.exp(-2.1 * ph)); ampl = 0.55 * math.exp(-ph / 0.5) * float(S(57.4, 58.2, t))
        if ampl > 0.01:
            n = 420
            x, y, ang = ring_points(star_scr[0], star_scr[1], r, n, 0.8, rr_)
            add_pts(x, y, np.tile(COL_V * 0.9 + 0.1, (n, 1)) * ampl)

    # ---- splat all points
    px = np.concatenate(PX); py = np.concatenate(PY); pc = np.concatenate(PC)
    L = splat(px, py, pc)

    # ---- orbs
    def orb(P, col, inten, depth_scale, ign=0.0):
        if inten <= 0.004: return
        x, y = proj(P)
        s = zs * depth_scale
        amp = inten * (1 + ign)
        add_blob(L, x, y, 3.0 * s, col * 0.35 + 0.65, 9.0 * amp)
        add_blob(L, x, y, 8.5 * s, col, 3.0 * amp)
        add_blob(L, x, y, 32 * s, col, 0.55 * amp)
        add_blob(L, x, y, 95 * s, col, 0.10 * amp)
        if amp > 0.4:
            add_streak(L, x, y, 70 * s, 1.6 * s, col * 0.5 + 0.5, 0.55 * amp)
            add_streak(L, x, y, 42 * s, 1.4 * s, col * 0.5 + 0.5, 0.25 * amp, vertical=True)

    # A
    iA = float(intA(t))
    pA = A_pos(t); zA = float(depth_z(t))
    dsA = float(np.clip(1 + 0.0016 * zA, 0.6, 1.6))
    pulseA = 1 + 0.08 * math.sin(3.1 * t)
    orb(pA, colA(t), iA * pulseA * np.clip(1 + 0.0009 * zA, 0.7, 1.4), dsA)
    # B
    iB = float(intB(t))
    pB = B_pos(t); zB = -zA
    dsB = float(np.clip(1 + 0.0016 * zB, 0.6, 1.6))
    ign = 4.0 * math.exp(-(t - 10.0) / 0.3) if t >= 10 else 0.0
    flick = 1.0
    if t >= TM: flick = 0.6 + 0.4 * math.sin(55 * t) * math.sin(23 * t + 1.0)
    orb(pB, colB(t), iB * flick * np.clip(1 + 0.0009 * zB, 0.7, 1.4), dsB, ign)
    if 9.95 <= t < 10.0 + 1.6:     # ignition ring for B
        a = t - 10.0
        if a > 0:
            cB = proj(B_pos(10.0)); r = 260 * zs * (1 - math.exp(-2.4 * a)); n = 900
            x, y, ang = ring_points(cB[0], cB[1], r, n, 1.4, rr_)
            pts = splat(x.astype(F32), y.astype(F32), np.tile(COL_B, (n, 1)) * F32(0.9 * math.exp(-a / 0.5)))
            L += pts
    if 0.8 <= t < 2.2:               # ignition ring for A
        a = t - 0.8
        cA = proj(A_pos(0.8)); r = 150 * zs * (1 - math.exp(-2.2 * a)); n = 700
        x, y, ang = ring_points(cA[0], cA[1], r, n, 1.2, rr_)
        L += splat(x.astype(F32), y.astype(F32), np.tile(COL_A, (n, 1)) * F32(0.6 * math.exp(-a / 0.5)))

    # impact core glow
    if TM - 0.35 <= t < TM + 3.0:
        a = t - TM
        c0 = proj(CM)
        if a < 0:
            k = float(S(TM - 0.35, TM, t))
            add_blob(L, c0[0], c0[1], 14 * zs, np.array([1, 0.85, 1.0]), 6 * k)
            add_blob(L, c0[0], c0[1], 60 * zs, COL_V, 1.2 * k)
        else:
            e1 = math.exp(-a / 0.3); e2 = math.exp(-a / 0.7)
            add_blob(L, c0[0], c0[1], 36 * zs, np.array([1, 0.9, 0.85]), 7 * e1)
            add_blob(L, c0[0], c0[1], 100 * zs, COL_B, 1.1 * e2)
            add_blob(L, c0[0], c0[1], 210 * zs, COL_B * 0.8, 0.16 * e2)

    # the new star
    if t >= 55.45:
        a = t - 55.5
        env = float(S(55.45, 55.78, t))
        burst = 1 + 7.0 * math.exp(-max(a, 0) / 0.25)
        shrink = min(1.0, z / 1.35) ** 0.35
        sx_, sy_ = star_scr
        s = max(0.35, shrink)
        add_blob(L, sx_, sy_, 4.0 * s, np.array([1, 0.9, 1.0]), 8.0 * env * burst)
        add_blob(L, sx_, sy_, 11 * s, COL_V, 3.2 * env * burst)
        bb = 1 + 1.2 * math.exp(-max(a, 0) / 0.25)
        add_blob(L, sx_, sy_, 42 * s, COL_V, 0.65 * env * bb)
        add_blob(L, sx_, sy_, 130 * s, COL_V, 0.14 * env * bb)
        add_streak(L, sx_, sy_, 140 * s, 1.8 * s, np.array([0.85, 0.7, 1.0]), 0.85 * env * burst)
        add_streak(L, sx_, sy_, 80 * s, 1.5 * s, np.array([0.85, 0.7, 1.0]), 0.4 * env * burst, vertical=True)

    # galaxy core glow
    if gal_a > 0.003:
        gc = proj(GCEN)
        add_blob(L, gc[0], gc[1], 55 * max(z / 0.1, 0.5) ** 0.5, np.array([1.0, 0.8, 0.55]), 0.75 * gal_a)
        add_blob(L, gc[0], gc[1], 190 * max(z / 0.1, 0.5) ** 0.6, np.array([0.9, 0.65, 0.5]), 0.12 * gal_a)

    # ---- bloom
    D = cv2.resize(L, (W // 4, H // 4), interpolation=cv2.INTER_AREA)
    g1 = cv2.GaussianBlur(D, (0, 0), 2.5); g2 = cv2.GaussianBlur(D, (0, 0), 9); g3 = cv2.GaussianBlur(D, (0, 0), 30)
    st = cv2.GaussianBlur(np.maximum(D - 0.9, 0), (0, 0), sigmaX=60, sigmaY=1.3)
    B = g1 * 0.42 + g2 * 0.55 + g3 * 0.75 + st * 0.9
    Lf = cv2.GaussianBlur(L, (0, 0), 0.85) + cv2.resize(B, (W, H), interpolation=cv2.INTER_LINEAR)

    # ---- nebula background
    nb_amp = 0.016 * float(S(0, 4, t)) * (1 + 0.8 * S(26, 35.8, t)) * (1 - 0.55 * gal_a)
    nb_amp *= 1 + 1.5 * math.exp(-(t - TM) / 0.6) if t >= TM else 1.0
    zn = z ** 0.1
    a_n = 0.25 / zn
    tx = 260 + 12 * math.sin(0.05 * t) - 0.02 * (cc[0] - 960) - a_n * 960
    ty = 150 + 8 * math.cos(0.04 * t) - 0.02 * (cc[1] - 540) - a_n * 540
    Mx = np.array([[a_n, 0, tx], [0, a_n, ty]], F32)
    Mx2 = np.array([[a_n * 0.9, 0, tx + 30 + 9 * math.sin(0.03 * t + 1)], [0, a_n * 0.9, ty - 10]], F32)
    n1 = cv2.warpAffine(NEB1, Mx, (W, H), flags=cv2.INTER_LINEAR | cv2.WARP_INVERSE_MAP, borderMode=cv2.BORDER_REFLECT)
    n2 = cv2.warpAffine(NEB2, Mx2, (W, H), flags=cv2.INTER_LINEAR | cv2.WARP_INVERSE_MAP, borderMode=cv2.BORDER_REFLECT)
    cA_ = mix(np.array([0.10, 0.30, 0.95]), np.array([0.45, 0.20, 0.85]), float(S(20, 35, t)))
    warm = float(S(TM - 0.1, TM + 2, t) * (1 - S(44, 52, t)))
    cB_ = mix(np.array([0.35, 0.18, 0.80]), np.array([0.95, 0.30, 0.12]), warm)
    cB_ = mix(cB_, COL_V, float(S(54.5, 57, t)))
    bg = n1[..., None] * (cA_ * F32(nb_amp)) + n2[..., None] * (cB_ * F32(nb_amp * 0.9))
    bg += np.array([0.0012, 0.0016, 0.0040], F32)
    Lf = Lf + bg

    # ---- impact flash & aberration
    if TM - 0.02 <= t < TM + 1.5:
        a = t - TM
        fl = 5.0 * math.exp(-max(a, 0) / 0.10) if a >= 0 else 0.0
        Lf += F32(fl) * np.array([1.0, 0.92, 0.95], F32)
    if 55.5 <= t < 56.6:
        a = t - 55.5
        Lf += F32(0.22 * math.exp(-a / 0.12)) * np.array([0.8, 0.6, 1.0], F32)
    ca = 0.0014 + (0.0075 * math.exp(-(t - TM) / 0.5) if t >= TM else 0.0) + (0.003 * math.exp(-(t - 55.5) / 0.4) if t >= 55.5 else 0.0)
    cxm = np.array([[1 + ca, 0, -ca * W / 2], [0, 1 + ca, -ca * H / 2]], F32)
    cbm = np.array([[1 - ca, 0, ca * W / 2], [0, 1 - ca, ca * H / 2]], F32)
    Lf[..., 0] = cv2.warpAffine(np.ascontiguousarray(Lf[..., 0]), cxm, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
    Lf[..., 2] = cv2.warpAffine(np.ascontiguousarray(Lf[..., 2]), cbm, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)

    # ---- tone map, vignette, gamma
    img = 1.0 - np.exp(-Lf * F32(1.0))
    img *= VIG
    img = cv2.sqrt(np.maximum(img, 0))
    # fades
    fade = float(S(0, 0.7, t)) * (1 - float(S(59.4, 60.0, t)))
    img *= F32(fade)

    draw_text(img, t)

    img += GRAIN[i % 6][..., None] * F32(0.010) * (0.35 + 0.65 * (1 - img.mean(axis=2, keepdims=True)))
    out = np.clip(img * 255.0 + 0.5, 0, 255).astype(np.uint8)
    return out

# ---------------------------------------------------------------- drivers
def render_chunk(args):
    i0, i1, path = args
    cmd = ['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS),
           '-i', '-', '-c:v', 'libx264', '-preset', 'medium', '-crf', '17', '-pix_fmt', 'yuv420p',
           '-vf', 'scale=out_color_matrix=bt709:out_range=tv', '-colorspace', 'bt709', '-color_primaries', 'bt709',
           '-color_trc', 'bt709', '-g', '60', path]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    t0 = time.time()
    for i in range(i0, i1):
        p.stdin.write(render_frame(i).tobytes())
    p.stdin.close(); p.wait()
    return (i0, i1, time.time() - t0)

if __name__ == '__main__':
    mode = sys.argv[1]
    if mode == 'test':
        os.makedirs('test', exist_ok=True)
        for tt in sys.argv[2:]:
            tsec = float(tt); i = int(round(tsec * FPS)); i = min(i, NF - 1)
            t0 = time.time(); fr = render_frame(i)
            Image.fromarray(fr).resize((960, 540), Image.LANCZOS).save(f'test/f_{tsec:05.1f}.png')
            print(f't={tsec} {time.time() - t0:.2f}s', flush=True)
    elif mode == 'full':
        import multiprocessing as mp
        os.makedirs('chunks', exist_ok=True)
        cs = 150
        jobs = [(a, min(a + cs, NF), f'chunks/c{a // cs:02d}.mp4') for a in range(0, NF, cs)]
        t0 = time.time()
        with mp.Pool(2) as pool:
            for r in pool.imap_unordered(render_chunk, jobs):
                print(f'chunk {r[0]}-{r[1]} done in {r[2]:.0f}s (total {time.time() - t0:.0f}s)', flush=True)
        with open('chunks/list.txt', 'w') as f:
            for j in sorted(jobs): f.write(f"file '{os.path.basename(j[2])}'\n")
        print('ALL DONE', flush=True)
