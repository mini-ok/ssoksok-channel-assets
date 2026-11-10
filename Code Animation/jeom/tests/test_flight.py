"""〈점〉 표현 시험: 폭풍 속 비행(4.5초, 960×540, 투스).
용은 그림이 아니라 3D 공간의 등뼈 곡선을 따라 움직인다(머리 경로를 몸이 뒤따름).
원근 투영으로 가까운 몸은 굵고 먼 몸은 가늘다. 몸은 붓 획 질감(붓털 결·비백·등쪽 진함·비늘 호)으로 칠한다.
머리는 본편 용의 머리 획을 그대로 렌더한 판(2D)을 진행 방향으로 돌려 붙이고, 눈에는 점(눈동자)이 있다.
몸에서 떨어지는 먹은 2D 유체(이류 + 소용돌이 강화 + 압력 투영)로 물속 먹처럼 말려 흩어진다.
빗줄기도 같은 유체 속도로 휜다. 하늘은 젖은 종이빛 회색, 먹구름은 발묵. 마지막에 종이 질감을 곱한다.
"""
import sys, os, math, subprocess
HERE = os.path.dirname(os.path.abspath(__file__)); JE = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(JE, 'engine'))
import numpy as np, cv2
from paper import View, paper_layers, paper_rgb
from brush import render_strokes, Stroke
from look import INK_ABS, film, letterbox
import dragon

F32 = np.float32
from scale import S, W, H, SUF
GS = int(2 * S); GW, GH = W // GS, H // GS
FPS = 12; DUR = 4.5
F = 640.0 * S; CX, CY = W / 2, H / 2
R_BODY = 0.50                        # 몸 반지름(월드)
LT = 2.7                             # 몸 길이 = 머리 경로 1.45초 분량
NS = 140                             # 등뼈 표본 수
rng = np.random.default_rng(7)
CACHE = os.path.join(JE, 'cache', 'flight' + SUF); os.makedirs(CACHE, exist_ok=True)

def ease(u): return u * u * (3 - 2 * u)

# ---------------------------------------------------------------- 3D 경로
def head_path(tau):
    tau = np.asarray(tau, float)
    x = 5.0 - 2.6 * tau + 1.4 * np.sin(1.9 * tau)
    y = -3.2 + 1.5 * tau + 1.3 * np.sin(1.5 * tau + 0.6)
    z = 13.0 - 1.6 * tau + 3.5 * np.sin(1.1 * tau + 0.4)
    return np.stack([x, y, z], -1)

def project(P):
    z = np.maximum(P[..., 2], 0.5)
    return np.stack([CX + F * P[..., 0] / z, CY - F * P[..., 1] / z], -1), z

def radius(s):                       # s: 0 머리 → 1 꼬리
    return R_BODY * (0.82 + 0.25 * np.sin(np.pi * np.clip(s / 0.45, 0, 1))) * np.clip((1 - s) / 0.55, 0.06, 1) ** 0.9

# ---------------------------------------------------------------- 머리 판(본편 머리 획)
HEAD_NAMES = {'head_wash', 'topline', 'bridge', 'nose', 'lipcurl', 'lip', 'jaw', 'fang', 'cheek', 'beard', 'eye_up', 'eye_low',
              'brow', 'horn1', 'horn1b', 'horn2', 'mane', 'whisker1', 'whisker2'}
NECK = np.array((338.0, 128.0)); HW0 = float(dragon.body_halfwidth(0.0))
HPPM = 6.0
def head_sprite():
    fn = os.path.join(CACHE, 'head.npz')
    if os.path.exists(fn):
        z = np.load(fn); return z['d'], tuple(z['o'])
    v = View(270, 112, 240, int(240 * HPPM), int(200 * HPPM))
    fib, _, _, X, Y = paper_layers(v)
    st = [s for s in dragon.strokes() if s.name in HEAD_NAMES]
    d = render_strokes(v, st, fib) * dragon.eye_blank(X, Y)
    # 눈동자(점): 본편의 모인 점처럼 진한 먹 + 테
    ex, ey = v.to_px(*dragon.E)
    yy, xx = np.mgrid[0:v.H, 0:v.W].astype(F32)
    r = np.hypot(xx - ex - 1.0 * HPPM, yy - ey)
    d = d + 2.4 * np.clip((4.3 * HPPM - r) / (0.8 * HPPM), 0, 1)
    ox, oy = v.to_px(*NECK)
    np.savez_compressed(fn, d=d.astype(F32), o=np.array((ox, oy)))
    return d.astype(F32), (ox, oy)
HEAD, HEAD_O = head_sprite()
def head_mask(d):
    """머리 실루엣: 획 사이를 메워 속까지 채운 면(수염·뿔 끝은 빼고)."""
    P_ = 100
    m = (cv2.GaussianBlur(d, (0, 0), 2.5) > 0.12).astype(np.uint8)
    m = np.pad(m, P_)
    m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (61, 61)))
    ff = m.copy(); h, w = m.shape; msk = np.zeros((h + 2, w + 2), np.uint8)
    cv2.floodFill(ff, msk, (0, 0), 1); m = m | (1 - ff)
    m = cv2.morphologyEx(m, cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (45, 45)))
    m = m[P_:-P_, P_:-P_]
    return cv2.GaussianBlur(m.astype(F32), (0, 0), 4)
HMASK = head_mask(HEAD)
yy_, xx_ = np.mgrid[0:HEAD.shape[0], 0:HEAD.shape[1]].astype(F32)
HFILL = HMASK * (0.55 + 0.35 * np.clip((yy_ - HEAD_O[1] + 40) / 260, 0, 1))   # 머리 속 담묵(아래턱 쪽 진하게)
EYEV = View(270, 112, 240, int(240 * HPPM), int(200 * HPPM))
ex_, ey_ = EYEV.to_px(*dragon.E)
HFILL = HFILL * (1 - np.exp(-(((xx_ - ex_) / (11 * HPPM)) ** 2 + ((yy_ - ey_) / (6.5 * HPPM)) ** 2)) * 0.9)    # 눈자위는 희게
HCOMP = np.maximum(HFILL, HEAD)
HALPHA = np.clip(np.maximum(HMASK, HEAD * 1.6), 0, 1)
_nd = np.clip((HEAD_O[0] - xx_) / (40 * HPPM), 0, 1)           # 목(갈기) 쪽 40mm는 먹 몸으로 풀린다
HALPHA = HALPHA * (0.25 + 0.75 * _nd)
EYE_PX = None

# ---------------------------------------------------------------- 종이·하늘
def make_paper():
    fn = os.path.join(CACHE, 'paper.npz')
    if os.path.exists(fn):
        z = np.load(fn); return z['rgb'], z['fib']
    v = View(320, 210, 320, W, H)
    fib, flk, mot, X, Y = paper_layers(v)
    rgb = paper_rgb(fib, flk, mot).astype(F32)
    np.savez_compressed(fn, rgb=rgb, fib=fib.astype(F32)); return rgb, fib.astype(F32)
PAPER, FIB = make_paper()
SV = View(W / 2, H / 2, W, W, H)
_sfn = os.path.join(CACHE, 'sfib.npy')
if os.path.exists(_sfn): SFIB = np.load(_sfn)
else:
    SFIB = paper_layers(SV)[0].astype(F32); np.save(_sfn, SFIB)

def body_strokes(S2, rad, ss, t):
    """몸 = 본편 용과 같은 몰골 붓 획. 보이지 않는 등뼈(S2)를 따라 매 장 다시 긋는다(시드 고정: 붓결이 몸에 붙어 다님)."""
    idx = np.linspace(0, len(S2) - 1, 26).astype(int)
    P = S2[idx]; R = rad[idx]; u = np.linspace(0, 1, len(idx))
    mr = float(R.max())
    d = np.gradient(P, axis=0); d /= np.linalg.norm(d, axis=1, keepdims=True) + 1e-9
    n = np.stack([-d[:, 1], d[:, 0]], 1)
    # 등 쪽: 화면 위쪽을 향하는 법선
    sgn = np.where(n[:, 1] < 0, 1.0, -1.0)[:, None]; nb = n * sgn
    press = lambda q, R=R, u=u, mr=mr: np.interp(q, u, R / mr)
    st = [Stroke([tuple(p) for p in P], 2.0 * mr, load=1.15, dry=0.32, seed=5, head='press', tail='taper', press=press, wet=0.55, name='body')]
    Pb = P + nb * R[:, None] * 0.55
    st.append(Stroke([tuple(p) for p in Pb[1:]], 0.55 * mr, load=1.7, dry=0.72, seed=6, head='press', tail='taper',
                     press=lambda q, R=R, u=u, mr=mr: np.interp(q, u[1:], R[1:] / mr), wet=0.3, name='back'))
    Pl = P + (-nb) * R[:, None] * 0.7
    st.append(Stroke([tuple(p) for p in Pl[2:-4]], 0.22 * mr, load=0.55, dry=0.55, seed=7, head='point', tail='taper', wet=0.3, name='belly'))
    for k in range(3, 22, 3):                                       # 등지느러미: 뒤로 쳐낸 짧은 붓 터치
        b0 = P[k] + nb[k] * R[k] * 0.9; tip = b0 + nb[k] * R[k] * 0.9 + d[k] * R[k] * 1.1
        if R[k] < 2.5: continue
        st.append(Stroke([tuple(b0), tuple((b0 + tip) / 2 + nb[k] * R[k] * 0.1), tuple(tip)], 0.35 * R[k], load=1.4, dry=0.6, seed=20 + k, head='press', tail='taper', wet=0.25, name='fin'))
    return st

def fbm(shape, seed, scales=(64, 32, 16, 8), amps=(1, .55, .3, .16)):
    r = np.random.default_rng(seed); out = np.zeros(shape, F32)
    for s, a in zip(scales, amps):
        n = r.standard_normal((shape[0] // s + 3, shape[1] // s + 3)).astype(F32)
        out += a * cv2.resize(n, (shape[1] + 3 * s, shape[0] + 3 * s), interpolation=cv2.INTER_CUBIC)[:shape[0], :shape[1]]
    return out / sum(amps)
CLOUD_A = fbm((H + 200, W + 400), 11); CLOUD_B = fbm((H + 200, W + 400), 12, scales=(128, 64, 32, 16))

CL1 = fbm((H + int(200 * S), W + int(400 * S)), 11, scales=tuple(int(v * S) for v in (256, 128, 64, 24)), amps=(1, .6, .3, .12))
CL2 = fbm((H + int(200 * S), W + int(400 * S)), 12, scales=tuple(int(v * S) for v in (320, 160, 80, 32)), amps=(1, .5, .25, .1))
def wash(c, thr):
    m = np.clip((c - thr) * 2.2, 0, None)
    m = np.tanh(m * 1.2)
    rim = np.clip(m - cv2.GaussianBlur(m, (0, 0), 6 * S), 0, None) * 1.6     # 마르며 생긴 가장자리 테
    return m * 0.55 + rim
def sky(t):
    yy = np.linspace(0, 1, H, dtype=F32)[:, None]
    base = 0.06 + 0.10 * yy
    ox = int(30 * t); oy = int(10 * t)
    a = CL1[oy:oy + H, ox:ox + W]; b = CL2[100 - oy:100 - oy + H, 200 - ox // 2:200 - ox // 2 + W]
    xx = np.linspace(-1, 1, W, dtype=F32)[None, :]; edge = np.clip(0.35 * (xx ** 2) + 0.9 * (1 - yy) ** 3 - 0.15, 0, 1)
    far = wash(b + 0.5 * edge, 0.45) * 0.45
    near = wash(a + 0.25 * b + 0.6 * edge, 0.75) * 0.8
    return base + (far + near) * (0.75 + 0.5 * np.clip(FIB * 1.3, 0, 1.3))

# ---------------------------------------------------------------- 유체(먹물 연기)
class Fluid:
    def __init__(s):
        s.u = np.zeros((GH, GW), F32); s.v = np.zeros((GH, GW), F32); s.d = np.zeros((GH, GW), F32)
        s.gx, s.gy = np.meshgrid(np.arange(GW, dtype=F32), np.arange(GH, dtype=F32))
        psi = fbm((GH, GW), 31, scales=(32, 16, 8, 4), amps=(1, .6, .35, .2))
        s.cu = (np.roll(psi, -1, 0) - np.roll(psi, 1, 0)) * 0.5 * 6; s.cv = -(np.roll(psi, -1, 1) - np.roll(psi, 1, 1)) * 0.5 * 6
    def adv(s, f, dt):
        return cv2.remap(f, s.gx - s.u * dt, s.gy - s.v * dt, cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT)
    def step(s, dt):
        # 소용돌이 강화(가는 소용돌이를 살린다)
        w = (np.roll(s.v, -1, 1) - np.roll(s.v, 1, 1) - np.roll(s.u, -1, 0) + np.roll(s.u, 1, 0)) * 0.5
        aw = np.abs(w)
        nx = (np.roll(aw, -1, 1) - np.roll(aw, 1, 1)) * 0.5; ny = (np.roll(aw, -1, 0) - np.roll(aw, 1, 0)) * 0.5
        nn = np.hypot(nx, ny) + 1e-5; nx /= nn; ny /= nn
        eps = 5.0
        s.u += dt * eps * (ny * w); s.v += dt * eps * (-nx * w)
        s.u += dt * s.cu * 14; s.v += dt * s.cv * 14
        g = getattr(s, 'grav', None)                    # (cx, cy, 부호): 원근 화면에서는 '아래'가 소실점 쪽(−) 또는 바깥(+)
        if g is None:
            s.v += dt * 55.0 * np.tanh(s.d * 0.8)      # 먹은 무겁다: 짙은 곳은 아래로 흘러내린다
        else:
            rx, ry = s.gx - g[0], s.gy - g[1]; rn = np.hypot(rx, ry) + 1e-3
            f = dt * 55.0 * np.tanh(s.d * 0.8) * g[2]
            s.u += f * rx / rn; s.v += f * ry / rn
        s.u, s.v = s.adv(s.u, dt), s.adv(s.v, dt)
        # 압력 투영(Jacobi)
        div = (np.roll(s.u, -1, 1) - np.roll(s.u, 1, 1) + np.roll(s.v, -1, 0) - np.roll(s.v, 1, 0)) * 0.5
        p = np.zeros_like(div)
        for _ in range(30):
            p = (np.roll(p, 1, 1) + np.roll(p, -1, 1) + np.roll(p, 1, 0) + np.roll(p, -1, 0) - div) * 0.25
        s.u -= (np.roll(p, -1, 1) - np.roll(p, 1, 1)) * 0.5; s.v -= (np.roll(p, -1, 0) - np.roll(p, 1, 0)) * 0.5
        s.d = s.adv(s.d, dt) * 0.955
        s.u *= 0.992; s.v *= 0.992
    def splat(s, x, y, amt, vx, vy, rad):
        gx, gy = x / GS, y / GS; rr = max(1.2, rad / GS)
        x0, x1 = int(max(0, gx - 3 * rr)), int(min(GW, gx + 3 * rr + 1)); y0, y1 = int(max(0, gy - 3 * rr)), int(min(GH, gy + 3 * rr + 1))
        if x0 >= x1 or y0 >= y1: return
        g = np.exp(-((s.gx[y0:y1, x0:x1] - gx) ** 2 + (s.gy[y0:y1, x0:x1] - gy) ** 2) / (rr * rr))
        s.d[y0:y1, x0:x1] += amt * g
        s.u[y0:y1, x0:x1] += g * (vx / GS - s.u[y0:y1, x0:x1]) * 0.6
        s.v[y0:y1, x0:x1] += g * (vy / GS - s.v[y0:y1, x0:x1]) * 0.6

# ---------------------------------------------------------------- 몸(붓 획)
STREAK = fbm((1, 4096), 21, scales=(16, 8, 4, 2), amps=(1, .7, .5, .35))[0]
def body_layer(pts, rad, zs, ss, dens, alpha):
    """pts: 화면 좌표 (n,2), rad: 화면 반지름, zs: 깊이, ss: 몸 매개변수. 먼 토막부터 덮어 칠한다."""
    order = np.argsort(-(zs[:-1] + zs[1:]))
    for i in order:
        a, b = pts[i], pts[i + 1]; ra, rb = rad[i], rad[i + 1]
        d = b - a; L = np.hypot(*d)
        if L < 1e-3: continue
        d = d / L; n = np.array((-d[1], d[0]))
        m = max(ra, rb) + 2
        x0, x1 = int(max(0, min(a[0], b[0]) - m)), int(min(W, max(a[0], b[0]) + m + 1))
        y0, y1 = int(max(0, min(a[1], b[1]) - m)), int(min(H, max(a[1], b[1]) + m + 1))
        if x0 >= x1 or y0 >= y1: continue
        yy, xx = np.mgrid[y0:y1, x0:x1].astype(F32)
        u = ((xx - a[0]) * d[0] + (yy - a[1]) * d[1]) / L
        uc = np.clip(u, 0, 1)
        r = ra + (rb - ra) * uc
        vv = ((xx - a[0]) * n[0] + (yy - a[1]) * n[1]) / np.maximum(r, 0.5)
        # 둥근 이음매: 끝을 넘으면 원
        ex = np.where(u < 0, -u * L / np.maximum(r, .5), np.where(u > 1, (u - 1) * L / np.maximum(r, .5), 0))
        q = np.sqrt(vv * vv + ex * ex)
        cov = np.clip((1 - q) * r / 1.3, 0, 1)
        if cov.max() <= 0: continue
        s = ss[i] + (ss[i + 1] - ss[i]) * uc
        cyl = np.sqrt(np.clip(1 - vv * vv, 0, 1))
        core = 0.75 + 0.55 * cyl                                   # 담묵 몸통(가운데 진하게)
        idx = ((vv + 1.2) * 300 + s * 40 + 37).astype(np.int32) % 4096
        st = STREAK[idx]
        ridge = np.exp(-((vv + 0.62) / 0.22) ** 2)                 # 등줄기: 진한 갈필 한 획
        rdry = np.clip((st + 0.6 - 0.9 * np.clip((s - 0.3) / 0.7, 0, 1)) * 2.5, 0, 1)
        belly = np.exp(-((vv - 0.7) / 0.18) ** 2) * (0.5 + 0.5 * np.clip(np.cos(s * 60 * np.pi), 0, 1))   # 배비늘 마디
        scale = np.clip(np.cos((s * 26 + 0.8 * vv * vv) * 2 * np.pi), 0, 1) ** 24 * 0.45 * (vv < 0.35) * (vv > -0.45) * (STREAK[(s * 900).astype(np.int32) % 4096] > -0.2)
        edge = np.clip((np.abs(vv) - 0.82) / 0.18, 0, 1) * (0.5 + 0.5 * st)   # 가장자리는 풀어진다
        val = (core + 1.1 * ridge * rdry + 0.35 * belly + scale - 0.6 * edge) * (1.0 - 0.3 * np.clip((s - 0.65) / 0.35, 0, 1))
        cov = cov * (1 - 0.55 * edge)
        sl = (slice(y0, y1), slice(x0, x1))
        dens[sl] = dens[sl] * (1 - cov) + val * cov
        alpha[sl] = np.maximum(alpha[sl], cov)

def spikes(pts, rad, ss, dens):
    """등지느러미: 등 쪽(−n)으로, 뒤로 기운 짧은 붓 터치."""
    m = np.zeros((H, W), F32)
    for k in range(4, len(pts) - 6, 4):
        a, b = pts[k], pts[k + 1]; d = b - a; L = np.hypot(*d) + 1e-6; d /= L; n = np.array((-d[1], d[0]))
        r = rad[k]
        if r < 2: continue
        base = a - n * r * 0.85
        tip = base - n * r * 0.75 + d * r * 0.9
        poly = np.array([base - d * r * 0.35, tip, base + d * r * 0.45]).astype(np.int32)
        cv2.fillConvexPoly(m, poly, 1.0, cv2.LINE_AA)
    m = cv2.GaussianBlur(m, (0, 0), 0.7)
    return np.maximum(dens, m * 1.5), m

# ---------------------------------------------------------------- 머리 붙이기
def place_head(dens, alpha, pos, ang, scale_px_per_mm, squash=1.0):
    hs = scale_px_per_mm / HPPM
    c, s_ = math.cos(ang + math.pi), math.sin(ang + math.pi)     # 원본 머리는 −x를 본다
    Mrot = np.array([[c, -s_], [s_, c]]) * hs @ np.array([[squash, 0], [0, 1.0]])
    o = np.array(HEAD_O)
    t = np.array(pos) - Mrot @ o
    M = np.hstack([Mrot, t[:, None]]).astype(np.float32)
    hd = cv2.warpAffine(HCOMP, M, (W, H), flags=cv2.INTER_LINEAR, borderValue=0)
    a = cv2.warpAffine(HALPHA, M, (W, H), flags=cv2.INTER_LINEAR, borderValue=0)
    out = dens * (1 - a) + hd * a
    # 눈 위치(반사광용)
    e = Mrot @ np.array((ex_, ey_)) + t
    return out, np.maximum(alpha, a), e

# ---------------------------------------------------------------- 비
NR = 1600
RX = rng.uniform(-100, W + 100, NR).astype(F32); RY = rng.uniform(-100, H + 100, NR).astype(F32)
RZ = rng.uniform(0.3, 1.0, NR).astype(F32)                      # 가까울수록 길고 빠름

def rain(t, fl):
    img = np.zeros((H, W), F32)
    q = math.floor(t * FPS)
    sp = 900 * RZ
    base_dx, base_dy = -0.32, 1.0
    x = (RX + base_dx * sp * t) % (W + 200) - 100; y = (RY + base_dy * sp * t) % (H + 200) - 100
    gx = np.clip((x / GS).astype(int), 0, GW - 1); gy = np.clip((y / GS).astype(int), 0, GH - 1)
    fu = fl.u[gy, gx] * GS * FPS; fv = fl.v[gy, gx] * GS * FPS          # 유체 속도(px/s)
    vx = base_dx * sp + fu * 1.6; vy = base_dy * sp + fv * 1.6
    L = 0.035 * RZ
    for i in range(NR):
        cv2.line(img, (int(x[i]), int(y[i])), (int(x[i] - vx[i] * L[i]), int(y[i] - vy[i] * L[i])), float(0.25 + 0.5 * RZ[i]), 1, cv2.LINE_AA)
    return img

# ---------------------------------------------------------------- 번개
def flash(t):
    f = 0.0
    for tf, a in ((1.35, 1.0), (1.55, 0.6), (3.2, 0.8)):
        if t >= tf:
            f = max(f, a * math.exp(-(t - tf) / 0.12))
    return f

# ---------------------------------------------------------------- 프레임
def render():
    fl = Fluid()
    frames = []
    prev = None
    sub = 3
    for k in range(int(DUR * FPS)):
        t = k / FPS
        ss = np.linspace(0, 1, NS)
        P = head_path(t - ss * LT)
        # 헤엄치듯 몸을 따라 흐르는 물결(진행 방향과 시선에 수직)
        tg = np.gradient(P, axis=0); tg /= np.linalg.norm(tg, axis=1, keepdims=True) + 1e-9
        side = np.cross(tg, np.array((0, 0, 1.0))); side /= np.linalg.norm(side, axis=1, keepdims=True) + 1e-9
        P = P + side * (0.55 * np.sin(2 * np.pi * (1.6 * ss - 1.3 * t)) * np.clip(ss / 0.15, 0, 1))[:, None]
        S2, Z = project(P)
        rad = F * radius(ss) / Z
        vel = (S2 - prev) * FPS if prev is not None else np.zeros_like(S2)
        prev = S2.copy()
        # 몸 = 먹물 자체: 보이지 않는 등뼈를 따라 먹을 풀어 넣고, 몸의 움직임이 물(공기)을 끈다
        for _ in range(sub):
            for i in range(1, NS):
                spd = np.hypot(*vel[i])
                amt = 0.07 * (1 - ss[i]) ** 1.2 * (0.35 + 0.65 * min(1.0, spd / 350)) * (0.55 + 0.45 * math.sin(ss[i] * 31 + t * 9)) / sub
                jit = rng.normal(0, 0.25, 2) * rad[i]
                fl.splat(S2[i][0] + jit[0], S2[i][1] + jit[1], amt, vel[i][0] * 0.8, vel[i][1] * 0.8, rad[i] * 0.9)
            fl.step(1.0 / (FPS * sub))
        smoke = cv2.resize(fl.d, (W, H), interpolation=cv2.INTER_CUBIC)
        smoke = np.clip(smoke, 0, None)
        # 먹 연기는 섬유를 따라 가장자리가 조금 진하다(번짐 테)
        sm_edge = np.clip(np.abs(cv2.Laplacian(smoke, cv2.CV_32F, ksize=3)) * 3.0, 0, 0.3)
        sharp = np.clip(smoke + 0.9 * (smoke - cv2.GaussianBlur(smoke, (0, 0), 3)), 0, None)
        smoke_d = 1.0 * np.tanh(sharp * 1.0) + sm_edge * np.clip(FIB * 1.3, 0, 1.2)
        fx = flash(t)
        sky_d = sky(t) * (1 - 0.65 * fx)
        dens = sky_d + smoke_d * (1 - 0.35 * fx)
        rn = rain(t, fl)
        dens = dens + rn * 0.30 * (1 - fx) - rn * 0.25 * fx            # 번개 때는 빗줄기가 희게 빛난다
        # 몸
        bd = np.zeros((H, W), F32)
        for stv in body_strokes(S2, rad, ss, t):
            stv.render(SV, bd, SFIB)
        ba = np.clip(bd * 1.4, 0, 1)
        # 머리
        d0 = S2[1] - S2[0]; ang = math.atan2(-d0[1], -d0[0])         # 진행 방향(머리 쪽)
        hpx = F * R_BODY * 0.62 / Z[0] / HW0                      # 목 반폭이 몸 반지름과 맞게
        tz = (P[0] - P[3]); tz = tz / (np.linalg.norm(tz) + 1e-9)
        bd, ba, eye = place_head(bd, ba, S2[0], ang, hpx, squash=max(0.55, math.sqrt(1 - min(0.9, tz[2] ** 2))))
        ox = int(30 * t); oy = int(10 * t)
        fc = np.clip((CL1[oy + 40:oy + 40 + H, ox + 120:ox + 120 + W] - 0.85) * 3.0, 0, 1)       # 앞 구름(몸을 삼킨다)
        fc = cv2.GaussianBlur(fc, (0, 0), 10)
        dens = dens * (1 - ba) + bd * ba
        dens = dens * (1 - 0.8 * fc) + (sky_d * 0.9 + 0.35) * 0.8 * fc
        img = PAPER * np.exp(-dens[..., None] * INK_ABS)
        img = img * (1 + 0.35 * fx)
        # 눈 반사광(살아 있음)
        yy, xx = np.mgrid[0:H, 0:W].astype(F32)
        rr = max(1.5, 0.9 * hpx)
        g = np.exp(-((xx - eye[0] + 0.5 * rr) ** 2 + (yy - eye[1] + 0.5 * rr) ** 2) / (rr * rr))
        img = img + (g * (0.5 + 0.4 * fx))[..., None] * np.array((0.9, 0.92, 1.0), F32)
        img = img * np.array((0.93, 0.96, 1.02), F32)               # 폭풍의 차가운 빛
        img = film(img, t, H=H, W=W, vig=0.28, grain=0.014, weave=0.6)
        img = letterbox(img)
        f8 = (np.clip(img, 0, 1)[..., ::-1] * 255 + 0.5).astype(np.uint8)
        frames.append(f8)
        cv2.imwrite(os.path.join(CACHE, f'f{k:04d}.png'), f8)
    return frames

if __name__ == '__main__':
    FR = render()
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-framerate', str(FPS), '-i', os.path.join(CACHE, 'f%04d.png'),
                    '-vf', 'fps=24', '-c:v', 'libx264', '-crf', '18', '-pix_fmt', 'yuv420p', os.path.join(JE, 'cache', 'flight_test.mp4')])
    pick = [2, 8, 14, 20, 26, 32, 38, 44, 52]
    pick = [p for p in pick if p < len(FR)]
    rows = [np.hstack([FR[i] for i in pick[r * 3:(r + 1) * 3]]) for r in range(len(pick) // 3)]
    cv2.imwrite(os.path.join(JE, 'cache', 'flight_test_sheet.jpg'), cv2.resize(np.vstack(rows), (1440, 270 * len(rows))), [cv2.IMWRITE_JPEG_QUALITY, 90])
    print('ok', len(FR))
