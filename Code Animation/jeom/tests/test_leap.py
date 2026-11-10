"""〈점〉 표현 시험: 그림 속 용이 그대로 움직여 종이에서 솟아오른다(4.5초, 960×540, 투스).
원칙: 날아가는 용은 새로 만든 모델이 아니라 본편 그림의 획 그 자체다.
  - 모든 획의 제어점을 그림 속 등뼈(SPINE) 기준 좌표(s: 등뼈 길이, a: 접선 방향, d: 법선 방향)로 바꿔 둔다.
    머리 획은 s=0(목) 틀에 단단히 붙인다.
  - 새 등뼈 = '머리가 지나온 길'. t=0에는 그 길이 그림 속 등뼈 자체라서 화면은 그림과 똑같다.
    머리가 앞으로 나가면 몸은 자기가 그려진 곡선을 따라 미끄러져 나오고, 그다음 머리가 지나간 3D 길을 따라간다.
  - 회전 최소 틀(RMF)로 등뼈를 따라 틀을 옮겨, 획 평면이 3D 공간에서 자연스럽게 기울고 원근으로 줄고 커진다.
  - 종이에는 섬유에 스민 먹이 옅은 용(유령)으로 남는다. 몸에서 풀린 먹은 2D 유체로 흘러내린다.
"""
import sys, os, math, copy, subprocess
HERE = os.path.dirname(os.path.abspath(__file__)); JE = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(JE, 'engine'))
import numpy as np, cv2
from paper import View, paper_layers, paper_rgb
from brush import Stroke, Wash, render_strokes
from look import INK_ABS, light, film, letterbox
import dragon

F32 = np.float32
from scale import S, W, H, SUF
FPS = 12; DUR = 6.6                 # C17은 12번 프레임부터 5.5초를 쓴다 → 끝까지 움직이게 6.6초
F = 640.0 * S; CX, CY = W / 2, H / 2
PC = np.array((400.0, 215.0))        # 화면 가운데에 오는 종이 좌표(mm)
U = 1 / 50.0                         # mm → 월드
Z0 = F * U / (W / 600.0)             # 종이 평면 깊이: 종이 600mm가 화면 폭
CACHE = os.path.join(JE, 'cache', 'leap' + SUF); os.makedirs(CACHE, exist_ok=True)
rng = np.random.default_rng(3)

def ease(u): return u * u * (3 - 2 * u)
def ramp(t, a, b): return float(np.clip((t - a) / (b - a), 0, 1))

def paper_to_world(xy):
    xy = np.asarray(xy, float)
    return np.stack([(xy[..., 0] - PC[0]) * U, -(xy[..., 1] - PC[1]) * U, np.full(xy.shape[:-1], Z0)], -1)

CAM = {'pos': np.zeros(3), 'tilt': 0.0}
def cam_at(t):
    u = ease(ramp(t, 1.4, 4.8))
    sh = 0.0
    if 3.4 < t < 4.0:                                                    # 머리가 가까이 지날 때 흔들림
        sh = 0.03 * math.sin(t * 61) * (1 - (t - 3.4) / 0.6)
    return np.array((sh, -0.2 * u, -1.5 * u)), 0.0                       # 위에서 본 채 살짝 물러난다
def project(P):
    c, ti = CAM['pos'], CAM['tilt']
    Q = np.asarray(P, float) - c
    ct, st_ = math.cos(ti), math.sin(ti)
    y = Q[..., 1] * ct - Q[..., 2] * st_; z = Q[..., 1] * st_ + Q[..., 2] * ct      # 위로 젖힘: 위쪽이 화면 가운데로
    z = np.maximum(z, 0.12)
    return np.stack([CX + F * Q[..., 0] / z, CY - F * y / z], -1), z

# ---------------------------------------------------------------- 그림 속 용 → 등뼈 좌표
SP = dragon.SPINE; SS = dragon._S; SL = dragon.SPINE_L
_T = np.gradient(SP, axis=0); _T /= np.linalg.norm(_T, axis=1, keepdims=True)
_N = np.stack([-_T[:, 1], _T[:, 0]], 1)
HEAD_NAMES = {'head_wash', 'topline', 'bridge', 'nose', 'lipcurl', 'lip', 'jaw', 'fang', 'cheek', 'beard', 'eye_up', 'eye_low',
              'brow', 'horn1', 'horn1b', 'horn2', 'mane', 'whisker1', 'whisker2'}

def to_spine(p, head=False):
    p = np.asarray(p, float)
    if head:
        i = np.zeros(len(p), int)
    else:
        d2 = ((p[:, None, :] - SP[None, :, :]) ** 2).sum(-1); i = d2.argmin(1)
    r = p - SP[i]
    return np.stack([SS[i], (r * _T[i]).sum(1), (r * _N[i]).sum(1)], 1)

ALL = [s for s in dragon.strokes() if not s.name.startswith('cloud')]
REC = []
for st in ALL:
    head = st.name in HEAD_NAMES
    if isinstance(st, Stroke):
        REC.append(('S', st, to_spine(st.c, head)))
    else:
        REC.append(('W', st, to_spine(np.array([(b[0], b[1]) for b in st.blobs]), head)))

# ---------------------------------------------------------------- 머리의 길(3D)
HEAD0 = paper_to_world(SP[0])
KEYS = np.array([HEAD0,
                 (-2.4, 2.0, 7.6),
                 (-3.2, 0.9, 7.0),
                 (-2.8, -1.4, 6.0),
                 (-1.0, -2.0, 4.6),
                 (0.8, -1.0, 3.4),
                 (1.6, 0.6, 2.6),
                 (2.0, 2.0, 2.4),
                 (2.6, 4.0, 2.6),
                 (3.0, 6.0, 3.0),
                 (3.3, 8.5, 3.5),
                 (3.5, 11.5, 4.0),
                 (3.6, 15.0, 4.5)], float)
KT = np.array([0.0, 0.5, 1.0, 1.5, 1.95, 2.35, 2.75, 3.15, 3.6, 4.1, 4.7, 5.4, 6.2])   # 머리가 위로 빠진 뒤에도 몸·꼬리가 끝까지 따라 나간다
MIRROR = {'m': 1.0, 'p': 0.0}       # m: 목표(+1/−1), p: 구르기 진행(0 → 1이면 뒤집힘). 뒤집기는 0.45초 동안 몸을 굴려서
def head_path(tau):
    """그림 속 방향(왼쪽 위)으로 미끄러져 나오다 → 카메라 쪽으로 솟아 크게 다가오고 → 오른쪽으로 휘감아 → 위로 빠진다."""
    tau = np.atleast_1d(np.asarray(tau, float))
    P = np.vstack([KEYS[:1] * 2 - KEYS[1:2], KEYS, KEYS[-1:] * 2 - KEYS[-2:-1]])
    i = np.clip(np.searchsorted(KT, tau, side='right') - 1, 0, len(KT) - 2)
    u = ((tau - KT[i]) / (KT[i + 1] - KT[i]))[:, None]
    p0, p1, p2, p3 = P[i], P[i + 1], P[i + 2], P[i + 3]
    return 0.5 * ((2 * p1) + (-p0 + p2) * u + (2 * p0 - 5 * p1 + 4 * p2 - p3) * u ** 2 + (-p0 + 3 * p1 - 3 * p2 + p3) * u ** 3)

def trail(t_leave):
    """머리가 지나온 길: 그림 속 등뼈(꼬리→목) + 떠난 뒤의 3D 길. 호 길이로 다시 표본."""
    painted = paper_to_world(SP[::-1])
    if t_leave > 0:
        taus = np.linspace(0, t_leave, max(2, int(t_leave * 90)))
        path = head_path(taus)[1:]
        pts = np.vstack([painted, path])
    else:
        pts = painted
    seg = np.linalg.norm(np.diff(pts, axis=0), axis=1); cum = np.concatenate([[0], np.cumsum(seg)])
    return pts, cum

def frame_along(pts, cum, s_world):
    """머리에서 s_world만큼 뒤의 위치와 회전 최소 틀(T, N, B). 그림 속에서는 N이 종이 평면의 법선 방향(그림의 _N)과 같다."""
    Ltot = cum[-1]
    # 틀을 trail 전체에 대해 한 번 계산(회전 최소 틀)
    T = np.gradient(pts, axis=0); T /= np.linalg.norm(T, axis=1, keepdims=True) + 1e-9
    T = -T                                                           # 머리 쪽(끝)을 향하도록: 원래 trail은 꼬리→머리
    # 그림 평면이 늘 카메라를 보게(빌보드 띠): N = 시선 × T, 이웃과 부호를 이어 붙인다
    vd = pts - CAM['pos']; vd /= np.linalg.norm(vd, axis=1, keepdims=True) + 1e-9
    Ns = np.cross(vd, T); Ns /= np.linalg.norm(Ns, axis=1, keepdims=True) + 1e-9
    for k in range(1, len(pts)):
        if Ns[k] @ Ns[k - 1] < 0:
            Ns[k] = -Ns[k]
    q = np.clip(Ltot - s_world, 0, Ltot)
    idx = np.clip(np.searchsorted(cum, q) , 1, len(cum) - 1)
    w = ((q - cum[idx - 1]) / (cum[idx] - cum[idx - 1] + 1e-9))[:, None]
    P = pts[idx - 1] * (1 - w) + pts[idx] * w
    Tq = T[idx - 1] * (1 - w) + T[idx] * w; Nq = Ns[idx - 1] * (1 - w) + Ns[idx] * w
    return P, Tq, Nq

# 그림의 _N과 RMF의 N이 같은 쪽을 보게 부호를 맞춘다(t=0 기준)
_p, _c = trail(0)
_P, _Tq, _Nq = frame_along(_p, _c, np.array([0.0, 1.0]) * 0 + np.array([SS[5] * U, SS[5] * U]))
_nw = paper_to_world(SP[5] + _N[5]) - paper_to_world(SP[5])
NSIGN = 1.0 if (_Nq[0] @ _nw) > 0 else -1.0
_tw = paper_to_world(SP[5] - _T[5]) - paper_to_world(SP[5])         # 그림 _T(목→꼬리)의 반대 = 머리 쪽
TSIGN = 1.0 if (_Tq[0] @ _tw) > 0 else -1.0

def live_strokes(t_leave, k_load=1.0):
    pts, cum = trail(t_leave)
    hs, _ = project(pts[-6:])
    hx = hs[-1, 0] - hs[0, 0]
    if MIRROR['m'] > 0 and hx > 25: MIRROR['m'] = -1.0                  # 오른쪽으로 돌면 몸을 굴려 등이 위로 오게
    elif MIRROR['m'] < 0 and hx < -25: MIRROR['m'] = 1.0
    tgt = 0.0 if MIRROR['m'] > 0 else 1.0
    step = 1.0 / (0.45 * FPS)
    MIRROR['p'] += np.clip(tgt - MIRROR['p'], -step, step)
    mir = math.cos(math.pi * ease(MIRROR['p']))                         # +1 → 0(옆으로 누움) → −1: 끊김 없이 구른다
    MIRROR['mir'] = mir
    out = []; bodyw = []
    for kind, st, sad in REC:
        s, a, d = sad[:, 0] * U, sad[:, 1] * U, sad[:, 2] * U
        P, Tq, Nq = frame_along(pts, cum, s)
        Pw = P + (-TSIGN) * Tq * a[:, None] + mir * NSIGN * Nq * d[:, None]
        S2, Z = project(Pw)
        k = F * U / Z                                                  # 그 점의 px/mm
        if kind == 'S':
            ns = copy.copy(st)
            ns.c = S2; seg = np.linalg.norm(np.diff(S2, axis=0), axis=1)
            ns.s = np.concatenate([[0], np.cumsum(seg)]); ns.L = float(ns.s[-1])
            ns.width = st.width * float(np.median(k)); ns.load = st.load * k_load
            out.append(ns)
            if st.name.startswith(('body', 'back', 'tail', 'belly', 'fin')):
                bodyw.append(Pw[::6])
        else:
            ns = copy.copy(st)
            ns.blobs = [(S2[j, 0], S2[j, 1], st.blobs[j][2] * float(k[j])) for j in range(len(st.blobs))]
            ns.load = st.load * k_load
            out.append(ns)
    return out, pts, cum, (np.vstack(bodyw) if bodyw else np.zeros((0, 3)))

# ---------------------------------------------------------------- 판
SV = View(W / 2, H / 2, W, W, H)
PV = View(320, 210, 900, int(1440 * S), int(810 * S))                                   # 종이 전체 + 책상(1.6px/mm)
def plates():
    fn = os.path.join(CACHE, 'plates.npz')
    if os.path.exists(fn):
        z = np.load(fn); return z['rgb'], z['fib'], z['drg'], z['sfib']
    fib, flk, mot, X, Y = paper_layers(PV)
    rgb = paper_rgb(fib, flk, mot).astype(F32)
    off = ((X < 0) | (X > 640) | (Y < 0) | (Y > 420))
    rgb[off] = np.array((0.16, 0.11, 0.075), F32)                     # 책상
    drg = (render_strokes(PV, dragon.strokes(), fib) * dragon.eye_blank(X, Y)).astype(F32)
    sfib = paper_layers(SV)[0].astype(F32)
    np.savez_compressed(fn, rgb=rgb, fib=fib.astype(F32), drg=drg, sfib=sfib)
    return rgb, fib.astype(F32), drg, sfib
RGB, FIB, DRG, SFIB = plates()
def paper_H():
    """종이 판(PV 픽셀) → 화면 호모그래피(카메라 따라)."""
    cs = np.array([[0, 0], [PV.W, 0], [PV.W, PV.H], [0, PV.H]], F32)
    mm = np.stack([(cs[:, 0] - PV.W / 2) / PV.ppm + PV.cx, (cs[:, 1] - PV.H / 2) / PV.ppm + PV.cy], 1)
    sc, _ = project(paper_to_world(mm))
    return cv2.getPerspectiveTransform(cs, sc.astype(F32))
# 그림 속 구름만 따로(종이에 그대로 남는다)
CLOUD = render_strokes(PV, [s for s in dragon.strokes() if s.name.startswith('cloud')], FIB)
BODY_ON_PAPER = np.clip(DRG - CLOUD, 0, None)


# ---------------------------------------------------------------- 유체(풀려 흐르는 먹) — 화면 공간
GS = int(2 * S); GW, GH = W // GS, H // GS
class Fluid:
    def __init__(s):
        s.u = np.zeros((GH, GW), F32); s.v = np.zeros((GH, GW), F32); s.d = np.zeros((GH, GW), F32)
        s.gx, s.gy = np.meshgrid(np.arange(GW, dtype=F32), np.arange(GH, dtype=F32))
    def adv(s, f, dt):
        return cv2.remap(f, s.gx - s.u * dt, s.gy - s.v * dt, cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT)
    def step(s, dt):
        w = (np.roll(s.v, -1, 1) - np.roll(s.v, 1, 1) - np.roll(s.u, -1, 0) + np.roll(s.u, 1, 0)) * 0.5
        aw = np.abs(w); nx = (np.roll(aw, -1, 1) - np.roll(aw, 1, 1)) * 0.5; ny = (np.roll(aw, -1, 0) - np.roll(aw, 1, 0)) * 0.5
        nn = np.hypot(nx, ny) + 1e-5
        s.u += dt * 4.0 * (ny / nn * w); s.v += dt * 4.0 * (-nx / nn * w)
        s.v += dt * 60.0 * np.tanh(s.d * 0.8)
        s.u, s.v = s.adv(s.u, dt), s.adv(s.v, dt)
        div = (np.roll(s.u, -1, 1) - np.roll(s.u, 1, 1) + np.roll(s.v, -1, 0) - np.roll(s.v, 1, 0)) * 0.5
        p = np.zeros_like(div)
        for _ in range(25):
            p = (np.roll(p, 1, 1) + np.roll(p, -1, 1) + np.roll(p, 1, 0) + np.roll(p, -1, 0) - div) * 0.25
        s.u -= (np.roll(p, -1, 1) - np.roll(p, 1, 1)) * 0.5; s.v -= (np.roll(p, -1, 0) - np.roll(p, 1, 0)) * 0.5
        s.d = s.adv(s.d, dt) * 0.965; s.u *= 0.99; s.v *= 0.99
    def add(s, dens_src, amt, vx, vy):
        src = cv2.resize(dens_src, (GW, GH), interpolation=cv2.INTER_AREA)
        s.d += src * amt
        m = np.clip(src * 2, 0, 1)
        s.u += m * (vx / GS - s.u) * 0.5; s.v += m * (vy / GS - s.v) * 0.5

# ---------------------------------------------------------------- 시간표
T_LEAVE = 1.0                         # 머리가 움직이기 시작
def t_leave(t):
    if t < T_LEAVE: return 0.0
    u = t - T_LEAVE
    return u * u / 1.0 if u < 0.5 else (0.25 + (u - 0.5) * 1.0)        # 천천히 떼다가 가속

def flash(t):
    f = 0.0
    for tf, a in ((0.85, 1.0), (1.0, 0.5), (2.3, 0.8), (2.45, 0.4)):
        if t >= tf: f = max(f, a * math.exp(-(t - tf) / 0.12))
    return f

# ---------------------------------------------------------------- 먹방울(날며 뿌린 먹)·빗방울
def splat_mm(dens, x, y, r, seed, spray=True, ang=None):
    """종이에 떨어진 먹방울: 날아온 방향(ang)으로 늘어진 몸 + 앞쪽으로 튄 꼬리 방울 + 고운 안개 점."""
    rr = np.random.default_rng(seed)
    ang = rr.uniform(0, 2 * np.pi) if ang is None else ang
    ca, sa = math.cos(ang), math.sin(ang)
    blobs = []
    for j in range(5):                                              # 늘어진 몸(뒤가 굵고 앞이 가늘다)
        f = j / 4
        blobs.append((x + ca * r * 1.6 * f + rr.normal(0, r * 0.12), y + sa * r * 1.6 * f + rr.normal(0, r * 0.12), r * (1.0 - 0.55 * f) * rr.uniform(0.85, 1.1)))
    if spray:
        for j in range(int(rr.integers(3, 8))):                     # 앞으로 튄 방울(부채꼴)
            a2 = ang + rr.normal(0, 0.45); dd = r * rr.uniform(2.2, 6.0)
            blobs.append((x + math.cos(a2) * dd, y + math.sin(a2) * dd, r * rr.uniform(0.10, 0.32)))
        for j in range(int(rr.integers(4, 12))):                    # 고운 안개 점
            a2 = rr.uniform(0, 2 * np.pi); dd = r * rr.uniform(1.5, 4.0)
            blobs.append((x + math.cos(a2) * dd, y + math.sin(a2) * dd, r * rr.uniform(0.05, 0.12)))
    Wash(blobs[:5], load=rr.uniform(1.1, 1.7), soft=0.18, seed=int(seed), rim=0.5).render(PV, dens, FIB)
    if len(blobs) > 5:
        for j, bb in enumerate(blobs[5:]):
            Wash([bb], load=rr.uniform(0.9, 1.5), soft=0.15, seed=int(seed) + j + 1, rim=0.3).render(PV, dens, FIB)

DRIPS = []                                  # [t0, 낙하시간, 세계 시작점, 착지 mm, 반지름 mm, seed]
SPLAT = np.zeros((PV.H, PV.W), F32)
WETS = np.zeros((PV.H, PV.W), F32)
WETS_MM = []                                # 젖은 자국(mm): 엔딩 종이를 다른 배율로 다시 그릴 때 쓴다
RAIN_SP = np.random.default_rng(91)
NRAIN = 260
RAIN_XY = RAIN_SP.uniform(0, 1, (NRAIN, 2)); RAIN_PH = RAIN_SP.uniform(0, 1, NRAIN)

def rain_streaks(t):
    """위에서 내려다본 비: 빗줄기는 소실점(시선 방향)으로 모이는 짧은 선."""
    m = np.zeros((H, W), F32)
    vp, _ = project(np.array([[CAM['pos'][0], CAM['pos'][1], CAM['pos'][2] + 1e4]]))
    vp = vp[0]
    q = math.floor(t * FPS) / FPS
    for i in range(NRAIN):
        ph = (RAIN_PH[i] + q * 2.3) % 1.0
        p = np.array((RAIN_XY[i, 0] * W, RAIN_XY[i, 1] * H))
        d = p - vp
        a = vp + d * (1.25 - 0.45 * ph); b = vp + d * (1.25 - 0.45 * ph - 0.06)
        cv2.line(m, (int(a[0]), int(a[1])), (int(b[0]), int(b[1])), 0.5, 1, cv2.LINE_AA)
    return m

def render():
    fl = Fluid(); FR = []; prev = None
    for k in range(int(DUR * FPS)):
        t = k / FPS
        CAM['pos'], CAM['tilt'] = cam_at(t)
        tl = t_leave(t)
        HM = paper_H()
        lift = ramp(t, T_LEAVE, T_LEAVE + 0.5)
        # 종이: 구름은 그대로, 용은 떠날수록 섬유에 스민 만큼만(25%) 남는다
        ghost = 1.0 - 0.75 * lift
        wet = np.clip(cv2.GaussianBlur(WETS, (0, 0), 1.2), 0, 1)
        dens = CLOUD + BODY_ON_PAPER * ghost * (1 - 0.15 * wet) + SPLAT + 0.05 * wet
        # 비: 종이에 젖은 자국이 쌓인다
        for _ in range(6):
            rx, ry = rng.uniform(0, 640), rng.uniform(0, 420)
            rmm = rng.uniform(1.5, 4); WETS_MM.append((rx, ry, rmm))
            px, py = PV.to_px(rx, ry); rad = rmm * PV.ppm
            cv2.circle(WETS, (int(px), int(py)), int(rad), 1.0, -1, cv2.LINE_AA)
        # 날아간 먹방울이 종이에 닿는다
        for dr in DRIPS:
            if not dr[6] and t >= dr[0] + dr[1]:
                splat_mm(SPLAT, dr[3][0], dr[3][1], dr[4], dr[5], ang=dr[7]); dr[6] = True
        # 살아 움직이는 용(그림 그대로의 획)
        live = np.zeros((H, W), F32)
        if lift > 0:
            sts, pts, cum, bodyw = live_strokes(tl)
            live = render_strokes(SV, sts, SFIB)
            # 눈동자(점)
            P, Tq, Nq = frame_along(pts, cum, np.array([0.0]))
            sad = to_spine(np.array([dragon.E]), head=True)
            Pe = P + (-TSIGN) * Tq * sad[:, 1:2] * U + MIRROR.get('mir', 1.0) * NSIGN * Nq * sad[:, 2:3] * U
            e2, ze = project(Pe); kk = F * U / ze[0]
            yy, xx = np.mgrid[0:H, 0:W].astype(F32)
            r = np.hypot(xx - e2[0, 0] - 1.0 * kk, yy - e2[0, 1])
            live = live + 2.6 * np.clip((4.3 * kk - r) / (0.8 * kk), 0, 1)
            eye = e2[0]
            # 몸에서 먹이 풀린다(움직이는 만큼)
            if prev is not None:
                mv = live - prev
                fl.add(np.clip(live, 0, 2) * 0.5, 0.05 * lift, (e2[0, 0] - eye_prev[0]) * FPS * 0.3, (e2[0, 1] - eye_prev[1]) * FPS * 0.3)
            prev = live.copy(); eye_prev = eye.copy()
            # 먹방울을 뿌린다(움직임이 클 때)
            if tl > 0.35 and len(bodyw):
                for _ in range(int(rng.integers(2, 6))):
                    P0 = bodyw[rng.integers(len(bodyw))]
                    hgt = max(0.05, Z0 - P0[2])
                    lx, ly = P0[0] / U + PC[0], -P0[1] / U + PC[1]
                    if 0 < lx < 640 and 0 < ly < 420:
                        hv = pts[-1] - pts[-4]; ang = math.atan2(-hv[1], hv[0]) + rng.normal(0, 0.4)   # 용이 날던 방향(종이 mm 좌표)
                        DRIPS.append([t, 0.12 + 0.12 * math.sqrt(hgt), P0.copy(), (lx, ly), rng.uniform(1.0, 2.8), int(rng.integers(1e6)), False, ang])
        else:
            ex, ey = PV.to_px(*dragon.E)
            yy, xx = np.mgrid[0:PV.H, 0:PV.W].astype(F32)
            kk = PV.ppm
            r = np.hypot(xx - ex - 1.0 * kk, yy - ey)
            dens = dens + 2.6 * np.clip((4.3 * kk - r) / (0.8 * kk), 0, 1)
            e2, _ = project(paper_to_world(np.array([dragon.E]))); eye = e2[0]; eye_prev = eye
        for _ in range(2):
            fl.step(1 / (FPS * 2))
        smoke = cv2.resize(fl.d, (W, H), interpolation=cv2.INTER_CUBIC)
        smoke = 0.9 * np.tanh(np.clip(smoke, 0, None) * 1.2)
        fx = flash(t)
        pap = RGB * np.exp(-dens[..., None] * INK_ABS)
        pap = cv2.warpPerspective(pap, HM, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=(0.12, 0.08, 0.055))
        img = pap * np.exp(-smoke[..., None] * INK_ABS)
        # 살아 있는 용은 종이 위로 떠 있다: 아래에 그림자(높이만큼 밀리고 흐림)
        if lift > 0:
            hgt = min(1.0, tl * 1.2)
            sh = cv2.GaussianBlur(np.clip(live, 0, 1.5), (0, 0), (2 + 14 * hgt) * S)
            sh = np.roll(np.roll(sh, int(18 * hgt * S), 1), int(26 * hgt * S), 0)
            img = img * (1 - 0.35 * np.clip(sh, 0, 1) * (1 - 0.5 * hgt))[..., None]
            # 젖은 먹: 몸 굵은 곳의 한쪽 가장자리에 번개·창빛 반사, 속은 조금 더 깊게
            lv = cv2.GaussianBlur(np.clip(live, 0, 2).astype(F32), (0, 0), 2.0)
            gx = cv2.Sobel(lv, cv2.CV_32F, 1, 0, ksize=5); gy = cv2.Sobel(lv, cv2.CV_32F, 0, 1, ksize=5)
            gl = np.clip((gx * 0.6 - gy * 0.8) * 0.06, 0, 1) * np.clip(lv - 0.6, 0, 1)
            a = np.clip(live * 1.5, 0, 1)[..., None]
            img = img * (1 - a) + (np.array((0.92, 0.90, 0.86), F32) * np.exp(-live[..., None] * 1.12 * INK_ABS)) * a   # 떠 있는 먹
            img = img + (gl * (0.35 + 0.6 * fx))[..., None] * np.array((0.85, 0.9, 1.0), F32)
        for dr in DRIPS:
            if not dr[6] and t >= dr[0]:
                u = (t - dr[0]) / dr[1]
                P = dr[2].copy(); P[2] = dr[2][2] + (Z0 - dr[2][2]) * u * u
                q2, zq = project(P[None]); kq = F * U / zq[0]
                cv2.circle(img, (int(q2[0, 0]), int(q2[0, 1])), max(1, int(dr[4] * 0.6 * kq)), (0.03, 0.03, 0.04), -1, cv2.LINE_AA)
        img = light(img, 'night', extra=fx)
        img = img * (1 + 0.4 * fx)
        yy, xx = np.mgrid[0:H, 0:W].astype(F32)
        rr = max(1.5, 0.9 * kk)
        g = np.exp(-((xx - eye[0] + 0.5 * rr) ** 2 + (yy - eye[1] + 0.5 * rr) ** 2) / (rr * rr))
        img = img + (g * 0.6)[..., None]
        img = film(img, t, H=H, W=W, vig=0.26, grain=0.013, weave=0.5)
        img = letterbox(img)
        f8 = (np.clip(img, 0, 1)[..., ::-1] * 255 + 0.5).astype(np.uint8)
        FR.append(f8); cv2.imwrite(os.path.join(CACHE, f'f{k:04d}.png'), f8)
    return FR

if __name__ == '__main__':
    FR = render()
    dr = np.array([(d[3][0], d[3][1], d[4], d[5], d[7]) for d in DRIPS if d[6]], float)
    np.savez_compressed(os.path.join(CACHE, 'after.npz'), splat=SPLAT, wets=WETS, drips=dr, wets_mm=np.array(WETS_MM, float))          # 떠난 뒤 종이에 남은 것(엔딩에 쓴다)
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-framerate', str(FPS), '-i', os.path.join(CACHE, 'f%04d.png'),
                    '-vf', 'fps=24', '-c:v', 'libx264', '-crf', '18', '-pix_fmt', 'yuv420p', os.path.join(JE, 'cache', 'leap_test.mp4')])
    pick = [26, 27, 28, 29, 30, 31, 32, 44, 64]
    pick = [p for p in pick if p < len(FR)]
    rows = [np.hstack([FR[i] for i in pick[r * 3:(r + 1) * 3]]) for r in range(len(pick) // 3)]
    cv2.imwrite(os.path.join(JE, 'cache', 'leap_test_sheet.jpg'), cv2.resize(np.vstack(rows), (1440, 270 * len(rows))), [cv2.IMWRITE_JPEG_QUALITY, 90])
    print('ok', len(FR))
