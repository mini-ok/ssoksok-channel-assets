"""〈점〉 애니마틱 v3. 클라이맥스를 다시 짠 판(깨어남 → 몸부림 → 벗어남 → 창가에서 돌아봄 → 창을 넘음 →
폭풍 속 씻김 → 포효 → 하늘 접수 → 승천과 해돋이). 비는 붓으로 그린 비(engine/rain.py)로 바꿨다.
사용: python3 animatic3.py cut C13 C15 ... / all / still t... / encode
v2(animatic2.py)의 장면 함수(화실·여정·남은 그림·제목)를 가져다 쓴다.
"""
import sys, os, math, subprocess, glob, copy
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, 'engine')); sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, 'tests'))
if float(os.environ.get('JEOM_SCALE', '1')) >= 2:
    os.environ.setdefault('JEOM_RES', '0.25')                          # 최종: 번짐 격자를 촘촘하게
import numpy as np, cv2
import animatic2 as A2                                   # 여정 물길·칼집 장벽 패치, 화실·남은 그림·제목 함수
import test_leap as L                                    # 그림 그대로의 용 리그(등뼈 좌표), 종이 판
import test_flight as TF                                 # 하늘·구름·유체
from brush import render_strokes, Stroke, Wash
from paper import View
from look import INK_ABS, light, film, letterbox
from rain import InkRain
from room import POSES, mix
import dragon

F32 = np.float32
from scale import S, W, H, SUF
FPS = 12
C = os.path.join(HERE, 'cache')
OUT = os.path.join(C, 'anim3' + SUF); os.makedirs(OUT, exist_ok=True)
def ease(u): return u * u * (3 - 2 * u)
def ramp(t, a, b): return float(np.clip((t - a) / (b - a), 0, 1))
def step(u, n=6): return math.floor(u * n) / n          # 투스 계단

CUTS = [
    ('C1', 'room_paint', 0.0, 10.0),
    ('C2', 'hand_A', 10.0, 5.4),
    ('C3', 'hand_B', 15.4, 3.2),
    ('C4', 'knife', 18.6, 6.0),
    ('C5', 'room_sleep', 24.6, 8.4),
    ('C6', 'sill', 33.0, 5.0),            # 창틀 근접: 비가 창틀에 부딪혀 방 안으로 튄다
    ('J', 'journey', 38.0, 44.0),         # 점의 여정 → 눈을 뜸(여정 끝)
    ('C14', 'life', 82.0, 10.0),          # 깨어남: 숨, 수염, 발톱 / 움직이려 하나 종이에 묶임
    ('C15', 'room_cut', 92.0, 5.0),       # 잠든 화가, 비가 몰아침
    ('C16', 'struggle', 97.0, 14.0),      # 몸부림 두 번 → 바닥 → 다시 켜지는 눈
    ('C17', 'leap', 111.0, 5.5),          # 벗어남
    ('C18', 'lookback', 116.5, 6.0),      # 창가에서 잠든 화가를 돌아봄
    ('C19', 'exit', 122.5, 4.0),          # 창을 넘어 빗속으로
    ('C20', 'storm', 126.5, 22.0),        # 씻김 → 포효 → 하늘 접수
    ('C21', 'ascend', 148.5, 10.0),       # 승천, 해돋이
    ('C22', 'room_wake', 158.5, 7.0),
    ('C23', 'gaze', 165.5, 16.0),         # 화가의 시선: 그림 전체 → 눈(같은 컷 안에서 눈물)
    ('C25', 'title', 181.5, 10.0),
]
TOTAL = CUTS[-1][2] + CUTS[-1][3]

def to8(img): return (np.clip(img, 0, 1)[..., ::-1] * 255 + 0.5).astype(np.uint8)
def fin(img, t, vig=0.22): return to8(letterbox(film(img, t, H=H, W=W, vig=vig, grain=0.012, weave=0.35)))

# ---------------------------------------------------------------- 리그: 살아 있는 변형(숨·수염·발톱·턱)
BODYN = ('body', 'back', 'belly', 'scale', 'fin', 'tail')
HINGE = np.array((328.0, 132.0))
JAWN = {'jaw', 'fang', 'beard', 'whisker2'}
_jaw_cache = {}
def jaw_sad(st, ang):
    key = (id(st), round(ang, 2))
    if key not in _jaw_cache:
        c, s = math.cos(ang), math.sin(ang)
        pts = st.c if isinstance(st, Stroke) else np.array([(b[0], b[1]) for b in st.blobs])
        q = (pts - HINGE) @ np.array([[c, s], [-s, c]]) + HINGE
        _jaw_cache[key] = L.to_spine(q, head=True)
    return _jaw_cache[key]

ARMN = ('arm', 'arm_wash', 'wrist', 'claw')
ARM2 = [(k, st, np.stack([sad[:, 0] + 18.0, sad[:, 1], -sad[:, 2] * 0.85], 1)) for (k, st, sad) in L.REC if st.name in ARMN]   # 몸 건너편의 다른 팔(앞발 둘)
def live3(pts, cum, t=0.0, k_load=1.0, breathe=0.0, curl=0.0, jaw=0.0, lift=None, mir=1.0, scale=1.0, wh=1.0, fore=1.0, arms2=False):
    """L.live_strokes와 같되, 살아 있는 변형을 더한다. lift(s_world) → 카메라 쪽으로 들리는 양(월드 z)."""
    out = []; bodyw = []
    for j, (kind, st, sad) in enumerate(L.REC + (ARM2 if arms2 else [])):
        name = st.name
        if name in JAWN and jaw != 0.0:
            sad = jaw_sad(st, -jaw)
        s, a, d = sad[:, 0] * L.U, sad[:, 1] * L.U * scale, sad[:, 2] * L.U * scale
        if fore != 1.0 and name in L.HEAD_NAMES: a = a * fore                 # 머리가 카메라 쪽으로 돌 때 앞뒤 길이가 짧아 보인다
        if breathe and name.startswith(BODYN):
            d = d * (1 + 0.05 * breathe)
        if name.startswith(('whisker', 'beard')) and wh:
            ang = 0.10 * wh * math.sin(2 * math.pi * 0.6 * t + j)
            a0, d0 = a[0], d[0]; ca, sa = math.cos(ang), math.sin(ang)
            a, d = a0 + (a - a0) * ca - (d - d0) * sa, d0 + (a - a0) * sa + (d - d0) * ca
        if name == 'claw' and curl:
            a = a[0] + (a - a[0]) * (1 - 0.35 * curl); d = d[0] + (d - d[0]) * (1 - 0.35 * curl)
        P, Tq, Nq = L.frame_along(pts, cum, s * scale)
        Pw = P + (-L.TSIGN) * Tq * a[:, None] + mir * L.NSIGN * Nq * d[:, None]
        if lift is not None:
            Pw[:, 2] -= lift(s)
        S2, Z = L.project(Pw)
        k = F32(L.F * L.U / Z)
        ns = copy.copy(st)
        if kind == 'S':
            ns.c = S2; seg = np.linalg.norm(np.diff(S2, axis=0), axis=1)
            ns.s = np.concatenate([[0], np.cumsum(seg)]); ns.L = float(ns.s[-1])
            ns.width = st.width * float(np.median(k)) * scale; ns.load = st.load * k_load
            if name.startswith(BODYN): bodyw.append(Pw[::6])
        else:
            ns.blobs = [(S2[i, 0], S2[i, 1], st.blobs[i][2] * float(k[i]) * scale) for i in range(len(st.blobs))]
            ns.load = st.load * k_load
        out.append(ns)
    return out, (np.vstack(bodyw) if bodyw else np.zeros((0, 3)))

def pupil(img_dens, pts, cum, mir=1.0, amt=2.6, jaw=0.0, scale=1.0, rs=1.0):
    """눈동자(점) 밀도를 더하고 화면 위치를 돌려준다."""
    sad = L.to_spine(np.array([dragon.E]), head=True)
    P, Tq, Nq = L.frame_along(pts, cum, np.array([0.0]))
    Pe = P + (-L.TSIGN) * Tq * sad[:, 1:2] * L.U * scale + mir * L.NSIGN * Nq * sad[:, 2:3] * L.U * scale
    e2, ze = L.project(Pe); kk = L.F * L.U / ze[0] * scale
    yy, xx = np.mgrid[0:H, 0:W].astype(F32)
    r = np.hypot(xx - e2[0, 0] - 1.0 * kk, yy - e2[0, 1])
    return img_dens + amt * np.clip((4.3 * kk * rs - r) / (0.8 * kk * rs), 0, 1), e2[0], kk

def glint(img, e, kk, amt=0.6):
    yy, xx = np.mgrid[0:H, 0:W].astype(F32)
    rr = max(1.2, 0.9 * kk)
    g = np.exp(-((xx - e[0] + 0.5 * rr) ** 2 + (yy - e[1] + 0.5 * rr) ** 2) / (rr * rr))
    return img + (g * amt)[..., None]

# ---------------------------------------------------------------- 종이 위의 비: 물 번짐(맑은 물 테)
class Blooms:
    def __init__(self, seed):
        self.r = np.random.default_rng(seed); self.items = []
        self.acc = np.zeros((H, W), F32)                                    # 마른 뒤에도 남는 젖은 자국
    def add(self, t, n):
        for _ in range(n):
            self.items.append((t, self.r.uniform(0, W), self.r.uniform(0, H), self.r.uniform(4, 13) * S))
    def render(self, t):
        wet = self.acc.copy(); rim = np.zeros((H, W), F32)
        keep = []
        for (t0, x, y, R) in self.items:
            u = t - t0
            if u < 0: keep.append((t0, x, y, R)); continue
            r = R * (1 - math.exp(-u / 0.12))
            m = np.zeros((H, W), F32); cv2.circle(m, (int(x), int(y)), max(1, int(r)), 1.0, -1, cv2.LINE_AA)
            rm = np.zeros((H, W), F32); cv2.circle(rm, (int(x), int(y)), max(1, int(r)), 1.0, 1, cv2.LINE_AA)
            if u < 1.5:
                wet = np.maximum(wet, m); rim = np.maximum(rim, rm * (1 - u / 1.5)); keep.append((t0, x, y, R))
            else:
                self.acc = np.maximum(self.acc, m * 0.6)
        self.items = keep
        return cv2.GaussianBlur(wet, (0, 0), 1.0), cv2.GaussianBlur(rim, (0, 0), 0.7)

def rain_on_paper(img, wet, rim):
    img = img * (1 - 0.07 * wet[..., None])                                  # 젖은 종이는 어둡다
    return img * (1 - 0.10 * rim[..., None]) + 0.03 * rim[..., None]

# ---------------------------------------------------------------- 위에서 본 종이(리그와 같은 카메라)
def paper_view(dens_pv, cam_pos):
    L.CAM['pos'] = np.array(cam_pos, float); L.CAM['tilt'] = 0.0
    HM = L.paper_H()
    pap = L.RGB * np.exp(-dens_pv[..., None] * INK_ABS)
    return cv2.warpPerspective(pap, HM, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=(0.12, 0.08, 0.055))

_tp = {}
def trail_pv():
    """여정이 끝난 상태(88초)의 점이 지나온 길과 눈에 맺힌 먹(덩어리)을 위에서 본 종이 판(L.PV)에. 엔딩(after.py)과 같은 원천.
    test_leap.py가 읽도록 cache/trail_pv{SUF}.npz에도 저장한다."""
    if 't' not in _tp:
        fn = os.path.join(C, f'trail_pv{SUF}.npz')
        if os.path.exists(fn):
            z = np.load(fn); _tp['t'], _tp['p'] = z['trail'], z['pupil']
        else:
            import inkmm
            A2.build_dot(); D = A2.A.dot(); dg = D.density(88.0); pup = D.pupil
            X, Y = L.PV.grid_mm()
            _tp['t'] = inkmm.sample(dg - (pup if pup is not None else 0), L.PV, X, Y).astype(F32)
            _tp['p'] = (inkmm.sample(pup, L.PV, X, Y) if pup is not None else 0 * X).astype(F32)
            np.savez(fn, trail=_tp['t'], pupil=_tp['p'])
    return _tp['t'], _tp['p']

def ink_over(img, live, k=1.0, halo=0.0):
    """종이 위에 붙은 먹(살아 있는 획). halo: 젖어서 번지는 정도."""
    if halo > 0:
        hb = cv2.GaussianBlur(live, (0, 0), (1.0 + 6.0 * halo) * S)
        live = live + np.clip(hb - live, 0, None) * 0.9 * halo
    return img * np.exp(-(live * k)[..., None] * INK_ABS)

# ---------------------------------------------------------------- C6 창틀 근접
_rain_sill = None; _sill_r = np.random.default_rng(31); _splash = []
def sill(lt):
    global _rain_sill
    if _rain_sill is None: _rain_sill = InkRain(W, int(H * 0.62), angle=-16, seed=41, fib=TF.FIB[:int(H * 0.62)], scale=S)
    img = np.zeros((H, W, 3), F32)
    hs = int(H * 0.62)
    # 바깥: 밤 비(먹색 하늘 위 붓 비)
    sky = TF.sky(min(lt + 1.0, 6.0))[:hs] * 0.8
    rn = _rain_sill.render(lt, amount=ramp(lt, 0, 0.6), gust=0.8)
    fx = math.exp(-(lt - 3.2) / 0.12) if lt >= 3.2 else 0.0
    dens = sky * (1 - 0.6 * fx) + rn * 0.6
    out = TF.PAPER[:hs] * np.exp(-dens[..., None] * INK_ABS)
    img[:hs] = out
    # 창틀: 양옆 기둥, 문지방 윗면(원근, 젖어 번들거림)과 앞면
    yy, xx = np.mgrid[0:H, 0:W].astype(F32)
    grain = np.sin(xx / (6.0 * S) + 2.5 * np.sin(yy / (31.0 * S) + xx / (140.0 * S)))
    top0, top1, front1 = hs, hs + int(46 * S), hs + int(112 * S)
    topm = (yy >= top0) & (yy < top1)
    frontm = (yy >= top1) & (yy < front1)
    tw = np.array((0.30, 0.20, 0.12), F32) * (0.85 + 0.12 * grain[..., None])
    img[topm] = tw[topm]
    img[frontm] = (tw * 0.55)[frontm]
    wetsheen = np.exp(-((yy - top0 - 8 * S) / (6.0 * S)) ** 2) * (0.6 + 0.4 * np.sin(xx / (37.0 * S)) ** 2)
    img = img + (wetsheen * topm * 0.20)[..., None] * np.array((0.75, 0.8, 0.9), F32)
    for x0 in (0, W - int(70 * S)):
        post = (xx >= x0) & (xx < x0 + int(70 * S)) & (yy < front1)
        img[post] = (np.array((0.20, 0.13, 0.08), F32) * (0.85 + 0.12 * grain[..., None]))[post]
    room = yy >= front1
    img[room] = np.array((0.045, 0.036, 0.03), F32)
    # 서안 위 종이 귀퉁이(창빛에 희미하게)
    pap = (yy >= H - 66 * S) & (xx > 180 * S + (yy - (H - 66 * S)) * 0.8)
    pcol = TF.PAPER * np.array((0.42, 0.44, 0.50), F32)
    img[pap] = pcol[pap]
    # 빗방울: 문지방에 부딪혀 왕관처럼 튀고, 물방울이 방 안(화면 아래·앞)으로, 앞모서리에서 물이 떨어진다
    q = math.floor(lt * FPS) / FPS
    if lt > 0.4:
        for _ in range(int(_sill_r.integers(1, 4) * min(1, lt / 1.2) + 1)):
            _splash.append((q, _sill_r.uniform(90 * S, W - 90 * S), _sill_r.uniform(top0 + 4 * S, top1 - 6 * S), _sill_r.uniform(-1, 1), _sill_r.uniform(0.7, 1.4) * S))
    sp = np.zeros((H, W), F32); drops = np.zeros((H, W), F32)
    for (t0, x, y, side, sz) in _splash:
        u = q - t0
        if u < 0 or u > 1.2: continue
        dep = 0.6 + 0.8 * (y - top0) / (top1 - top0)                         # 가까울수록 크게(sz에 배율 포함)
        if u < 0.25:
            rs_ = np.random.default_rng(int(x * 7 + t0 * 100))
            for k in range(int(rs_.integers(4, 8))):
                a_ = -math.pi / 2 + rs_.uniform(-1.25, 1.25) + side * 0.15
                L1 = (8 + 46 * (u / 0.25) ** 0.6) * sz * dep * rs_.uniform(0.35, 1.0)
                p0 = (x + math.cos(a_) * 4 * S, y + math.sin(a_) * 2 * S); p1 = (x + math.cos(a_) * L1, y + math.sin(a_) * L1 * 0.9)
                cv2.line(sp, (int(p0[0]), int(p0[1])), (int(p1[0]), int(p1[1])), 1.0 - u * 2, max(1, int(2.5 * dep * S)), cv2.LINE_AA)
                cv2.circle(sp, (int(p1[0]), int(p1[1])), max(1, int(2.2 * dep * S)), 1.0 - u * 2, -1, cv2.LINE_AA)
        for k in range(3):                                                  # 방 안으로 튀는 물방울: 앞으로 올수록 커진다
            vx = (k - 1) * 70 * sz + side * 40 * S; vy = (-120 + k * 35) * S
            px = x + vx * u; py = y + vy * u + 560 * S * u * u
            r = (2 + 6 * u) * dep * S
            if py < H: cv2.ellipse(drops, (int(px), int(py)), (max(1, int(r * 0.7)), max(1, int(r * 1.2))), 0, 0, 360, 1.0, -1, cv2.LINE_AA)
    for j in range(14):                                                     # 앞모서리에서 떨어지는 물
        x = (110 + j * 57 + 9 * math.sin(j * 3.1)) * S
        ph = (q * 1.6 + j * 0.37) % 1.0
        py = front1 + ph * ph * 160 * S
        cv2.ellipse(drops, (int(x), int(py)), (int(2 * S), int((3 + 5 * ph) * S)), 0, 0, 360, 0.8, -1, cv2.LINE_AA)
    sp = cv2.GaussianBlur(sp, (0, 0), 0.6 * S)
    img = img * (1 - 0.30 * sp[..., None]) + 0.45 * sp[..., None] * np.array((0.70, 0.76, 0.86), F32)
    img = img * (1 - 0.30 * drops[..., None]) + 0.32 * drops[..., None] * np.array((0.75, 0.8, 0.9), F32)
    img = light(img, 'night', extra=fx) * 0.5 + light(img, 'silver', extra=fx) * 0.6
    return img

# ---------------------------------------------------------------- C14 깨어남
_bl_life = Blooms(5)
def life(lt):
    cam = (-1.3, 1.2, 3.4)                                                  # 머리·앞몸 근접(위에서)
    pts, cum = L.trail(0.0)
    breathe = math.sin(2 * math.pi * 0.45 * lt) * ramp(lt, 0, 1.0)
    curl = 0.5 + 0.5 * math.sin(2 * math.pi * 0.3 * lt - 1)
    # 움직이려 함: 6~9초에 머리가 앞으로 끌리다 고무줄처럼 되돌아온다(종이에 묶임)
    pull = 0.10 * math.sin(math.pi * ramp(lt, 6.0, 7.4)) + 0.06 * math.sin(math.pi * ramp(lt, 8.0, 9.2))
    if pull > 0:
        pts, cum = L.trail(pull)
    L.CAM['pos'] = np.array(cam); L.CAM['tilt'] = 0.0
    sts, _ = live3(pts, cum, t=lt, breathe=breathe, curl=curl, wh=1.0)
    live = render_strokes(L.SV, sts, L.SFIB)
    # 눈에 맺힌 먹(여정 끝의 번진 덩어리)이 2~4.2초에 안쪽으로 모여 또렷한 둥근 눈동자가 된다. 종이엔 10%가 흔적으로 남는다(엔딩과 같음)
    g = ease(ramp(lt, 2.0, 4.2))
    if g > 0:
        live, e, kk = pupil(live, pts, cum, amt=2.6 * g ** 0.7, rs=1.0 + 0.9 * (1 - g))
    else:
        _, e, kk = pupil(np.zeros((H, W), F32), pts, cum)
    trl, blob = trail_pv()
    pap = paper_view(L.CLOUD + trl + blob * (0.10 + 2.3 * (1 - g)), cam)       # 여정 끝 근접처럼 짙은 먹 덩어리 → 모여서 눈동자, 10%만 흔적
    if lt > 3: _bl_life.add(lt, int(_bl_life.r.integers(0, 3)))
    wet, rim = _bl_life.render(lt)
    img = rain_on_paper(ink_over(pap, live, halo=0.15 * ramp(lt, 3, 10)), wet, rim)
    img = light(img, 'night', extra=0.0)
    return glint(img, e, kk, (0.55 + 0.25 * math.sin(lt * 2.0)) * (0.35 + 0.65 * g))

# ---------------------------------------------------------------- C16 몸부림
_bl_str = Blooms(9); _smear = None; _prev_live = None
def struggle(lt):
    global _smear, _prev_live
    cam = (0.0, 0.2, -0.6)
    # 시도 1(0.8~3.4): 머리·목이 들렸다 떨어짐 / 시도 2(4.6~8.4): 몸통 절반까지 들렸다 떨어짐(더 높이, 더 오래)
    # 바닥(8.4~11.6): 멈춤, 옅어짐 / 11.6~: 눈의 빛이 다시 켜짐, 숨이 커짐
    def bump(a, b, peak):
        u = ramp(lt, a, b); return peak * math.sin(math.pi * u) ** 0.8 if 0 < u < 1 else 0.0
    l1 = bump(0.8, 3.4, 1.9); l2 = bump(4.6, 8.4, 3.6)
    reach1, reach2 = 2.2, 5.5
    def lift(s):
        return l1 * np.clip(1 - s / reach1, 0, 1) ** 1.6 + l2 * np.clip(1 - s / reach2, 0, 1) ** 1.3
    shake = 0.05 * math.sin(lt * 31) * (l1 + l2)                             # 몸부림: 좌우로 비틂
    pts, cum = L.trail(0.0)
    pts = pts + np.array((shake, 0, 0))
    L.CAM['pos'] = np.array(cam); L.CAM['tilt'] = 0.0
    wetness = ramp(lt, 0, 9.5)
    k_load = 1.0 - 0.42 * ease(ramp(lt, 2.0, 10.0))                         # 몸부림칠수록 먹이 씻겨 옅어진다
    breathe = math.sin(2 * math.pi * 0.9 * lt) * (1 - ramp(lt, 8.4, 9.0)) + math.sin(2 * math.pi * 0.5 * lt) * 1.4 * ramp(lt, 11.6, 13.0)
    sts, _ = live3(pts, cum, t=lt, k_load=k_load, breathe=breathe, curl=0.7 * (l1 + l2) / 3.6, lift=lift, wh=1.5 * (1 - ramp(lt, 8.4, 9.0)) + ramp(lt, 11.6, 12.5))
    live = render_strokes(L.SV, sts, L.SFIB)
    live, e, kk = pupil(live, pts, cum, amt=2.6 * k_load)
    if _smear is None: _smear = np.zeros((H, W), F32)
    if _prev_live is not None and (l1 + l2) > 0.05:                        # 종이에 붙은 채 끌린 자리마다 먹이 문질러 남는다
        _smear = np.maximum(_smear * 0.995, cv2.GaussianBlur(_prev_live, (0, 0), 3.0 * S) * 0.22)
    _prev_live = live.copy()
    trl, blob = trail_pv()
    pap = paper_view(L.CLOUD + L.BODY_ON_PAPER * 0.25 * ramp(lt, 0.8, 1.2) + trl * (1.0 - 0.1 * ramp(lt, 0, 14)) + blob * 0.10, cam)   # 점이 지나온 길은 남아 있다(비에 조금씩 옅어짐)
    _bl_str.add(lt, int(_bl_str.r.integers(1, 4)))
    wet, rim = _bl_str.render(lt)
    img = rain_on_paper(pap * np.exp(-_smear[..., None] * INK_ABS), wet, rim)
    # 들린 부분은 그림자를 드리운다
    hgt = (l1 + l2) / 3.6
    if hgt > 0.02:
        sh = cv2.GaussianBlur(np.clip(live, 0, 1.5), (0, 0), (3 + 10 * hgt) * S)
        sh = np.roll(np.roll(sh, int(14 * hgt * S), 1), int(20 * hgt * S), 0)
        img = img * (1 - 0.3 * np.clip(sh, 0, 1) * hgt)[..., None]
    img = ink_over(img, live, halo=0.35 * wetness)
    fx = 0.9 * math.exp(-(lt - 11.6) / 0.15) if lt >= 11.6 else 0
    img = light(img, 'night', extra=fx)
    g = 0.15 if 8.4 < lt < 11.6 else (0.55 + 0.6 * ramp(lt, 11.6, 12.0))
    return glint(img, e, kk, g)

# ---------------------------------------------------------------- C18 창가에서 돌아봄 / C19 창을 넘음
SLW = dragon.SPINE_L * L.U                                               # 몸 길이(월드)
def hover_trail(t, turn, drift=(0.0, 0.0)):
    """공중에 떠 있는 용의 등뼈(꼬리 → 머리). turn 0: 머리가 오른쪽(창)을 봄, 1: 목을 꺾어 왼쪽(화가)을 돌아봄.
    몸에는 꼬리 쪽으로 흘러가는 물결(헤엄치듯 떠 있음), 목은 U자로 꺾인다."""
    n = 320
    sig = np.linspace(0, SLW, n)                                           # 머리에서 꼬리 쪽으로
    env = np.clip(sig / (0.18 * SLW), 0, 1)
    wave = 0.50 * np.sin(2 * np.pi * (sig / (0.55 * SLW)) - 2.0 * t) * env
    neck = math.pi * turn * np.clip(1 - sig / (0.17 * SLW), 0, 1) ** 1.2
    phi = 0.25 + wave + neck                                               # 머리 쪽으로 향하는 방향각(월드, y 위)
    d = np.stack([np.cos(phi), np.sin(phi)], 1)
    ds = np.diff(sig, prepend=0)[:, None]
    p = -np.cumsum(d * ds, axis=0)                                          # 머리(0)에서 꼬리 쪽으로
    p = p - (p.max(0) + p.min(0)) / 2 + np.array(drift)                     # 가운데 정렬
    pts3 = np.concatenate([p, np.full((n, 1), L.Z0)], 1)[::-1]             # 꼬리 → 머리
    seg = np.linalg.norm(np.diff(pts3, axis=0), axis=1); cum = np.concatenate([[0], np.cumsum(seg)])
    return pts3, cum

def dragon_hover(t, turn, drift=(0.0, 0.0)):
    L.CAM['pos'] = np.zeros(3); L.CAM['tilt'] = 0.0
    pts, cum = hover_trail(t, turn, drift)
    mir = -math.cos(math.pi * turn)                                         # 오른쪽을 볼 때 −1, 왼쪽을 볼 때 +1(등이 위로)
    mir = math.copysign(max(0.12, abs(mir)), mir if mir != 0 else 1)
    sts, _ = live3(pts, cum, t=t, breathe=math.sin(t * 2.4), curl=0.4 + 0.3 * math.sin(t * 1.3), wh=1.4, mir=mir)
    d = render_strokes(L.SV, sts, L.SFIB)
    d, e, kk = pupil(d, pts, cum, mir=mir)
    return d, e, kk

def place(room_img, d, e, kk, cx, cy, s, clip=None, k_load=1.0):
    M = np.array([[s, 0, cx - s * W / 2], [0, s, cy - s * H / 2]], F32)
    dd = cv2.warpAffine(d, M, (W, H))
    if clip is not None: dd = dd * clip
    img = room_img * np.exp(-(dd * k_load)[..., None] * INK_ABS * 1.4)
    e2 = (e[0] * s + cx - s * W / 2, e[1] * s + cy - s * H / 2)
    return img, e2, kk * s

# C18·C19는 한 줄기의 움직임(τ = C18 시작부터 초): 종이(책상)에서 솟아올라 → 방 안, 창 앞에 떠서 화가를 돌아보고
# → 창으로 헤엄쳐 들어가 빗속 위로 멀어진다. 몸은 머리가 지나온 길을 따라가고(뱀처럼), 떠 있을 때만 제자리 물결(hover_trail).
RD_SC = 0.52                                                              # 화면 배치 배율(가운데 기준)
RD_C = (0.60, 0.42)                                                       # 떠 있을 때 몸 가운데(화면 비)
DESK_Y = 0.646                                                            # 책상 위 종이 윗변(이 아래는 아직 종이 속)
WIN_IN = (0.562, 0.838, 0.140, 0.500)                                     # 창 안쪽(문살·창틀 안)
def scr2w(fx, fy, zf):
    z = L.Z0 * zf
    return np.array(((fx * W - W / 2) * z / (RD_SC * L.F), -(fy * H - H / 2) * z / (RD_SC * L.F), z))
def w2scr(P):
    q, z = L.project(P)
    return W / 2 + RD_SC * (q[..., 0] - W / 2), H / 2 + RD_SC * (q[..., 1] - H / 2), z
def hover_shape(t, turn):
    pts, _ = hover_trail(t, turn)
    c = scr2w(RD_C[0], RD_C[1], 1.0)
    return pts + np.array((c[0], c[1], 0.0))
def cr_path(keys, tau):
    """Catmull-Rom: keys = [(τ, P3)], 끝은 그대로 이어 늘인다."""
    T = np.array([k[0] for k in keys]); P = np.array([k[1] for k in keys])
    P = np.vstack([P[:1] * 2 - P[1:2], P, P[-1:] * 2 - P[-2:-1]])
    tau = np.clip(np.atleast_1d(tau), T[0], T[-1])
    i = np.clip(np.searchsorted(T, tau, side='right') - 1, 0, len(T) - 2)
    u = ((tau - T[i]) / (T[i + 1] - T[i]))[:, None]
    p0, p1, p2, p3 = P[i], P[i + 1], P[i + 2], P[i + 3]
    return 0.5 * ((2 * p1) + (-p0 + p2) * u + (2 * p0 - 5 * p1 + 4 * p2 - p3) * u ** 2 + (-p0 + 3 * p1 - 3 * p2 + p3) * u ** 3)
def tail_of(poly, n=320):
    """꼬리→머리 폴리라인에서 머리 쪽 SLW 길이만 잘라 n점으로 다시 표본."""
    seg = np.linalg.norm(np.diff(poly, axis=0), axis=1); cum = np.concatenate([[0], np.cumsum(seg)])
    q = np.linspace(max(0.0, cum[-1] - SLW), cum[-1], n)
    out = np.stack([np.interp(q, cum, poly[:, k]) for k in range(3)], 1)
    seg = np.linalg.norm(np.diff(out, axis=0), axis=1)
    return out, np.concatenate([[0], np.cumsum(seg)])
_rd = {}
def rd_keys():
    if _rd: return _rd
    H0 = hover_shape(2.1, 0.0)[-1]                                        # 떠 있을 때 머리 자리(τ=2.1)
    hx, hy, _ = w2scr(H0[None])
    hx, hy = float(hx[0]) / W, float(hy[0]) / H
    _rd['rise'] = [(0.0, scr2w(hx - 0.04, 0.86, 1.0)), (0.5, scr2w(hx - 0.10, 0.60, 1.0)), (1.0, scr2w(hx - 0.13, 0.44, 1.0)),
                   (1.5, scr2w(hx - 0.08, hy - 0.02, 1.0)), (2.1, H0)]        # 솟으며 왼쪽으로 휘었다가 창 쪽으로 감아 돈다
    _rd['hx'] = (hx, hy)
    return _rd
def rd_shape(tau):
    """τ에서의 등뼈(꼬리→머리, 월드)와 turn·mir·exit 정보."""
    K = rd_keys()
    turn = ease(ramp(tau, 2.4, 3.3)) * (1 - ease(ramp(tau, 4.7, 5.4)))
    turn = step(turn, 6)
    if tau < 2.1:
        taus = np.linspace(0, tau, max(2, int(tau * 120)))
        path = cr_path(K['rise'], taus)
        base = np.stack([np.full(60, path[0, 0]), np.linspace(path[0, 1] - SLW * 1.2, path[0, 1], 60), np.full(60, path[0, 2])], 1)
        tr, _ = tail_of(np.vstack([base, path[1:]]))
        w = ease(ramp(tau, 1.3, 2.1))
        pts = tr * (1 - w) + hover_shape(tau, 0.0) * w
    elif tau < 5.6:
        pts = hover_shape(tau, turn)
    else:
        P0 = hover_shape(5.6, 0.0)
        keys = [(5.6, P0[-1]), (6.5, scr2w(K['hx'][0] - 0.02, K['hx'][1] - 0.02, 1.2)), (7.3, scr2w(0.72, 0.31, 1.7)),
                (8.1, scr2w(0.71, 0.22, 2.2)), (8.9, scr2w(0.70, 0.10, 2.6)), (9.6, scr2w(0.70, -0.05, 3.0)), (10.4, scr2w(0.70, -0.25, 3.3))]
        # 창으로 들어가(깊이) → 빗속에서 위로 솟구쳐 처마(창 윗변) 너머로 사라진다. 몸은 머리가 간 길을 그대로 따라 나간다.
        taus = np.linspace(5.6, tau, max(2, int((tau - 5.6) * 120)))
        pts, _ = tail_of(np.vstack([P0, cr_path(keys, taus)[1:]]))
    seg = np.linalg.norm(np.diff(pts, axis=0), axis=1)
    return pts, np.concatenate([[0], np.cumsum(seg)]), turn

def rimlight(img, dd, amt, L_dir=(0.55, -0.83)):
    """젖은 먹 몸의 창 쪽 가장자리에 비치는 푸른 창빛(어두운 벽 앞에서도 몸이 읽히게)."""
    lv = cv2.GaussianBlur(np.clip(dd, 0, 2).astype(F32), (0, 0), 1.6 * S)
    gx = cv2.Sobel(lv, cv2.CV_32F, 1, 0, ksize=5); gy = cv2.Sobel(lv, cv2.CV_32F, 0, 1, ksize=5)
    rim = np.clip(-(gx * L_dir[0] + gy * L_dir[1]) * 0.09 / S, 0, 1) * np.clip(lv * 3, 0, 1)
    rim = cv2.GaussianBlur(rim, (0, 0), 0.6 * S)
    rim = rim * np.clip(1.6 - img.mean(-1) * 4.0, 0, 1)                    # 밝은 창 앞에서는 실루엣 그대로(테두리 빛 없음)
    return img + (rim * amt)[..., None] * np.array((0.50, 0.58, 0.74), F32)

def rd_flash(tau):
    f = 0.0
    for tf, a in ((0.15, 0.9), (0.32, 0.45), (8.2, 0.7), (8.35, 0.3)):
        if tau >= tf: f = max(f, a * math.exp(-(tau - tf) / 0.12))
    return f

def room_dragon(tau):
    R = A2.room()
    fx = rd_flash(tau)
    base = R.render(tau + 200, dict(POSES['sleep']), lamp_on=0.0, rain=1.0, flash=fx)
    L.CAM['pos'] = np.zeros(3); L.CAM['tilt'] = 0.0
    pts, cum, turn = rd_shape(tau)
    mir = -math.cos(math.pi * turn); mir = math.copysign(max(0.12, abs(mir)), mir if mir != 0 else 1)
    # 배율을 그리기 전에 적용(등뼈 x·y와 단면·굵기를 함께 줄임) → 화면 밖으로 잘리지 않고 최종 크기로 바로 그린다
    ps = pts * np.array((RD_SC, RD_SC, 1.0)); cs = np.concatenate([[0], np.cumsum(np.linalg.norm(np.diff(ps, axis=0), axis=1))])
    sts, _ = live3(ps, cs, t=tau, breathe=math.sin(tau * 2.4), curl=0.4 + 0.3 * math.sin(tau * 1.3), wh=1.4, mir=mir, scale=RD_SC,
                   fore=max(0.3, abs(math.cos(math.pi * turn))))
    dd = render_strokes(L.SV, sts, L.SFIB)
    dd, e2, k2 = pupil(dd, ps, cs, mir=mir, scale=RD_SC)
    yy, xx = np.mgrid[0:H, 0:W].astype(F32)
    # 아직 종이 속인 부분(책상 윗변 아래)은 보이지 않는다
    vis = np.clip((DESK_Y * H - yy) / (1.5 * S), 0, 1) if tau < 2.4 else np.ones((H, W), F32)
    # 창을 넘은 부분: 창 안에서만 보이고(창틀·벽 뒤로 가려짐) 멀수록 빗속에 흐려진다
    ZC = 1.9 * L.Z0
    sx, sy, z = w2scr(pts)
    outside = z > ZC
    if outside.any():
        # 아직 방 안인 몸(꼬리 쪽)의 넉넉한 띠만 '안'으로 두고, 나머지(머리·수염·넘어간 몸)는 모두 '밖'
        m_in = np.zeros((H, W), F32)
        for k in range(len(pts) - 1):
            if outside[k]: continue
            th = max(2, int(3.0 * L.F / z[k] * RD_SC))
            cv2.line(m_in, (int(sx[k]), int(sy[k])), (int(sx[k + 1]), int(sy[k + 1])), 1.0, th, cv2.LINE_AA)
        m_in = cv2.GaussianBlur(m_in, (0, 0), 3 * S)
        w_out = 1 - np.clip(m_in, 0, 1)
        x0, x1, y0, y1 = WIN_IN
        win = np.clip((xx - x0 * W) / S, 0, 1) * np.clip((x1 * W - xx) / S, 0, 1) * np.clip((yy - y0 * H) / S, 0, 1) * np.clip((y1 * H - yy) / S, 0, 1)
        zo = float(np.median(z[outside]))
        fog = 0.5 * np.clip((zo / L.Z0 - 1.9) / 1.5, 0, 1)
        vis = vis * (1 - w_out + w_out * win * (1 - fog))
    else:
        w_out = np.zeros((H, W), F32)
    fade = 1 - 0.5 * ease(ramp(tau, 9.4, 10.0))
    dd = dd * vis * fade
    img = base * np.exp(-dd[..., None] * INK_ABS * 1.4)
    img = rimlight(img, dd * (1 - w_out), 0.45 + 0.8 * fx)
    eye_out = bool(z[-1] > ZC)
    ga = (0.35 + 0.35 * ramp(tau, 3.6, 4.0) * (1 - ramp(tau, 4.4, 4.6))) * (0.25 if eye_out else 1.0) * fade
    if tau < 2.4 and e2[1] > DESK_Y * H: ga = 0.0
    return glint(img, e2, k2, ga)

def lookback(lt): return room_dragon(lt)
def exitw(lt): return room_dragon(6.0 + lt)

# ---------------------------------------------------------------- C20 폭풍 / C21 승천·해돋이
_storm = {}
def storm_init():
    if _storm: return
    if STORM_MODE in ('up', 'down'):
        from rain import RadialRain
        _storm['rain'] = RadialRain(W, H, (W / 2, H / 2), seed=7, fib=TF.FIB, scale=S, toward=(STORM_MODE == 'up'))
    else:
        _storm['rain'] = InkRain(W, H, angle=-12, seed=7, fib=TF.FIB, scale=S)
    _storm['fl'] = TF.Fluid()
    if STORM_MODE in ('up', 'down'):
        _storm['fl'].grav = (TF.GW / 2, TF.GH / 2, 1.0 if STORM_MODE == 'up' else -1.0)
    _storm['prev'] = None
KS = np.array([(-7, -9, 9), (-4, -5.5, 8.5), (-1.5, -2.5, 8.2), (1.8, -0.5, 8.6), (2.6, 1.6, 9.4), (0.4, 2.4, 10.2),
               (-2.4, 1.4, 10.6), (-2.6, -0.4, 10.4), (-0.8, -1.2, 9.6), (1.4, -0.2, 9.2), (1.2, 1.4, 9.8), (-0.6, 1.8, 10.6),
               (-1.6, 0.6, 11.0), (0.0, 0.0, 10.4), (0.0, 0.2, 10.0), (0.0, 3.0, 11.0), (0.0, 9.0, 13.0), (0.0, 20.0, 16.0)], float)
KST = np.array([-3.0, -1.5, 0.0, 2.0, 4.0, 6.0, 8.0, 10.0, 12.0, 13.5, 15.0, 16.5, 18.0, 19.5, 22.0, 25.0, 28.5, 31.5])
# 원근 폭풍(시안): 'up' = 하늘을 올려다봄(비가 쏟아져 오고 용은 소용돌이 눈으로 멀어지며 승천),
#                  'down' = 내려다봄(비가 아래로 빨려 들고 용은 폭풍 속에서 카메라 쪽으로 솟구침)
STORM_MODE = os.environ.get('JEOM_STORM', 'up')                       # 확정: 올려다봄(2026-11-10)
KS_UP = KS.copy(); KS_UP[0] = (-3.0, -9.0, 3.0); KS_UP[1] = (-2.5, -5.0, 4.5); KS_UP[2] = (-1.5, -2.5, 7.0)
KS_UP[-4] = (3.0, 1.2, 13.0); KS_UP[-3] = (-3.4, 2.6, 19.0); KS_UP[-2] = (-2.4, -4.2, 30.0); KS_UP[-1] = (2.6, -2.4, 48.0)   # 승천: 소용돌이 눈을 감아 돌며 멀어진다(곧장 멀어지면 몸이 한 점으로 눌림)
# 올려다봄 승천: 감아 돌다가 마지막에 소실점(화면 가운데)으로 곧장 높이·빠르게 — 사라진 그 자리에서 해가 뜬다
KS_UP = np.vstack([KS_UP[:14], [(2.6, 1.0, 11.5), (-2.6, 2.0, 14.0), (-1.6, -2.2, 21.0), (0.4, -0.8, 55.0), (0.0, 0.0, 180.0), (0.0, 0.0, 520.0)]])
KST_UP = np.concatenate([KST[:14], [21.5, 23.0, 24.2, 24.9, 25.4, 26.5]])
ASC_VANISH, ASC_SUN = 4.5, 5.5                                             # C21 시각: 용이 한 점으로 사라짐(정적 시작) → 해가 터져 나옴(화음)
KS_DOWN = np.array([(0.5, 0.3, 34), (0.9, -0.2, 27), (1.4, -0.8, 21), (2.6, 0.6, 16), (0.4, 2.4, 13.5), (-2.4, 1.4, 12.0),
                    (-2.6, -0.6, 11.0), (-0.8, -1.4, 10.0), (1.4, -0.4, 9.4), (1.4, 1.4, 9.6), (-0.6, 1.8, 10.0),
                    (-1.6, 0.6, 10.2), (0.0, 0.0, 9.6), (0.0, 0.2, 9.0), (0.0, 0.3, 6.5), (0.0, 0.4, 3.6), (0.0, 0.5, 1.4), (0.0, 0.6, -1.5)], float)
def storm_path(tau):
    tau = np.atleast_1d(np.asarray(tau, float))
    KSm = KS_UP if STORM_MODE == 'up' else (KS_DOWN if STORM_MODE == 'down' else KS)
    KT_ = KST_UP if STORM_MODE == 'up' else KST
    P = np.vstack([KSm[:1] * 2 - KSm[1:2], KSm, KSm[-1:] * 2 - KSm[-2:-1]])
    i = np.clip(np.searchsorted(KT_, tau, side='right') - 1, 0, len(KT_) - 2)
    u = np.clip((tau - KT_[i]) / (KT_[i + 1] - KT_[i]), 0, 1.5)[:, None]
    p0, p1, p2, p3 = P[i], P[i + 1], P[i + 2], P[i + 3]
    return 0.5 * ((2 * p1) + (-p0 + p2) * u + (2 * p0 - 5 * p1 + 4 * p2 - p3) * u ** 2 + (-p0 + 3 * p1 - 3 * p2 + p3) * u ** 3)

def storm_trail(t):
    """머리가 지나온 길. 느리게 감아 돌 때도 몸 길이(배율 포함)보다 길게 잡는다(짧으면 몸이 시작점에 뭉쳐 엉킨다)."""
    Lb = SLW * 1.5
    for back in (6.0, 10.0, 16.0, 24.0):
        taus = np.linspace(t - back, t, int(back * 100))
        pts = storm_path(taus)
        seg = np.linalg.norm(np.diff(pts, axis=0), axis=1); cum = np.concatenate([[0], np.cumsum(seg)])
        if cum[-1] >= Lb: break
    return pts, cum

yyS, xxS = np.mgrid[0:H, 0:W].astype(F32)
def clouds_take(t, swirl, take, clear, center, roar_r=None, part=0.0):
    """먹구름. swirl: 소용돌이, take: 용에게 빨려 들어간 정도(구름이 옅어짐), roar_r: 포효 충격파 반지름(px)."""
    DX, DY = xxS - center[0], yyS - center[1]
    RR = np.hypot(DX, DY) + 1e-3; TH = np.arctan2(DY, DX)
    rot = swirl * np.exp(-RR / (230.0 * S))
    rs = RR * (1 + 1.2 * take * np.exp(-RR / (420.0 * S)))
    if part > 0:                                                           # 구름이 갈라진다: 가운데가 바깥 구름으로 밀려남
        rs = rs * (1 - 0.6 * part * np.exp(-RR / (260.0 * S)))
    if roar_r is not None:                                                 # 충격파: 고리 바깥으로 구름이 밀린다
        rs = rs - 40 * S * np.exp(-((RR - roar_r) / (40.0 * S)) ** 2)
    sx = center[0] + rs * np.cos(TH + rot) + 30 * S * t; sy = center[1] + rs * np.sin(TH + rot) + 10 * S * t
    a = cv2.remap(TF.CL1, (sx + 200 * S).astype(F32), (sy + 100 * S).astype(F32), cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
    b = cv2.remap(TF.CL2, (sx * 0.8 + 200 * S).astype(F32), (sy * 0.8 + 100 * S).astype(F32), cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
    base = 0.10 + 0.12 * (yyS / H)
    far = TF.wash(b + 0.35, 0.40) * 0.55
    near = TF.wash(a + 0.25 * b + 0.30, 0.55) * 0.95
    d = base + (far + near) * (0.75 + 0.5 * np.clip(TF.FIB * 1.3, 0, 1.3)) * (1 - 0.75 * take * (1 - 0.6 * part)) * (1 - 0.9 * clear)
    return d * (1 - 0.6 * clear) + 0.03 * clear

def storm_frame(t, phase_t, total_t, ascend=False):
    storm_init()
    fl = _storm['fl']
    # 단계(C20 기준 시각 t): 상승·씻김 0~8, 포효 8~12, 하늘 접수 12~20, (C21) 승천 20~
    T = t
    wash = ease(ramp(T, 0.5, 8.0)) * (1 - ease(ramp(T, 12.0, 18.0)))       # 몸에서 먹이 씻겨 옅어짐 → 접수하며 다시 진해짐
    take = ease(ramp(T, 12.0, 19.5))
    k_load = 1.0 - 0.5 * wash + 0.35 * take
    scale = 1.0 + 0.45 * take
    roar = ramp(T, 8.6, 11.0)
    jaw = 0.0
    if 8.2 <= T < 11.4: jaw = 0.42 * math.sin(math.pi * ramp(T, 8.2, 11.4)) ** 0.6
    L.CAM['pos'] = np.array((0.04 * math.sin(T * 47) * math.exp(-(T - 8.7) / 0.6) if T > 8.7 else 0.0, 0, 0)); L.CAM['tilt'] = 0.0
    pts, cum = storm_trail(T)
    whip = 0.0
    if ascend and STORM_MODE == 'up' and WHIP[0] <= phase_t < WHIP[1]:      # 승천하며 꼬리로 화면을 한 번 '탁' 치고 올라간다
        ph = (phase_t - WHIP[0]) / (WHIP[1] - WHIP[0]); whip = math.sin(math.pi * ph)
        sfh = cum[-1] - cum                                                    # 머리에서 잰 길이 → 몸의 꼬리 쪽 40%만 휜다
        Lb = SLW * (1.0 + 0.45 * ease(ramp(T, 12.0, 19.5)))
        fq = np.clip((sfh - 0.55 * Lb) / (0.45 * Lb), 0, 1)                 # 0: 꼬리 마디 시작 … 1: 꼬리 끝
        wgt = fq ** 0.6
        dirm = np.array((0.87, 0.48))                                         # 왼쪽 아래 → 오른쪽 위로 쓸고 지나감
        base = np.array(((-1.0 + 2.0 * ph) * 0.9 * dirm[0], (-1.0 + 2.0 * ph) * 0.9 * dirm[1], 0.75 + 1.6 * (1 - whip)))   # 가운데(치는 순간)에서 렌즈에 가장 가깝다
        # 꼬리 끝은 카메라 바로 앞을 옆으로 가로지르고(옆으로 누워야 보인다), 꼬리 뿌리 쪽은 깊이로 몸에 이어진다
        tgt = base[None, :] + (1 - fq)[:, None] * np.array((-0.9 * dirm[0], -0.9 * dirm[1], 3.0))[None, :] \
            + fq[:, None] * np.array((-0.35 * dirm[1], 0.35 * dirm[0], 0.0))[None, :] * math.sin(ph * math.pi * 2)
        pts = pts * (1 - (whip * wgt)[:, None]) + tgt * (whip * wgt)[:, None]
        # cum은 휘기 전 길이 그대로 둔다: 몸의 각 마디가 같은 매개변수 자리를 따라가 꼬리 끝까지 휘어 나온다(늘어난 길이에 몸이 모자라지 않게)
    sts, bodyw = live3(pts, cum, t=T, k_load=k_load, breathe=math.sin(T * 3), curl=0.6, jaw=jaw, scale=scale, wh=1.6, arms2=(STORM_MODE == 'up'))
    live = render_strokes(L.SV, sts, L.SFIB)
    live, e, kk = pupil(live, pts, cum, scale=scale)
    vis = 1.0
    if ascend:
        vis = 1.0 - (ease(ramp(phase_t, ASC_VANISH - 0.25, ASC_VANISH)) if STORM_MODE == 'up' else ease(ramp(T, 26.0, 28.0)))
    live = live * vis
    # 유체: 씻겨 내리는 먹(무거워 아래로 흐름), 몸의 움직임이 공기를 끈다
    S2, Z = L.project(pts[-80::4])
    if _storm['prev'] is not None:
        v = (S2[-1] - _storm['prev']) * FPS
        for j in range(0, len(S2), 2):
            if STORM_MODE in ('up', 'down'):                                # 씻긴 먹은 땅 쪽으로: 올려다보면 바깥(카메라)으로, 내려다보면 소실점으로
                rx, ry = S2[j][0] - W / 2, S2[j][1] - H / 2; rn_ = math.hypot(rx, ry) + 1e-3
                g_ = 140 * S * wash * (1 if STORM_MODE == 'up' else -1)
                fl.splat(S2[j][0], S2[j][1], (0.02 + 0.22 * wash) * vis, v[0] * 0.4 + g_ * rx / rn_, v[1] * 0.4 + g_ * ry / rn_, 18 * S)
            else:
                fl.splat(S2[j][0], S2[j][1] + 10 * S, (0.02 + 0.22 * wash) * vis, v[0] * 0.4, v[1] * 0.4 + 140 * S * wash, 18 * S)
    _storm['prev'] = S2[-1].copy()
    center = (W * 0.5, H * 0.5) if STORM_MODE in ('up', 'down') else (W * 0.5, H * 0.44)
    if take > 0:
        DX, DY = xxS - center[0], yyS - center[1]; RR = np.hypot(DX, DY) + 1e-3
        wv = 70 * S * take * (1 - ramp(T, 21, 24))
        fl.u += cv2.resize((-DY / RR) * wv * np.exp(-RR / (300 * S)), (TF.GW, TF.GH)) / TF.GS * 0.02
        fl.v += cv2.resize((DX / RR) * wv * np.exp(-RR / (300 * S)), (TF.GW, TF.GH)) / TF.GS * 0.02
    for _ in range(2): fl.step(1 / (FPS * 2))
    smoke = 0.9 * np.tanh(np.clip(cv2.resize(fl.d, (W, H), interpolation=cv2.INTER_CUBIC), 0, None) * 1.2)
    if ascend and STORM_MODE == 'up': smoke = smoke * (1 - ease(ramp(phase_t, 3.4, ASC_VANISH)))   # 해가 뜰 자리에 먹 얼룩이 남지 않게
    clear = (0.2 * ease(ramp(phase_t, ASC_SUN, ASC_SUN + 3.0)) if STORM_MODE == 'up' else 0.2 * ease(ramp(T, 22.5, 26.5))) if ascend else 0.0
    swirl = 2.6 * take
    roar_r = (80 + 900 * roar) * S if 8.6 <= T < 11.5 else None
    part = (ease(ramp(phase_t, ASC_SUN, ASC_SUN + 3.5)) if STORM_MODE == 'up' else ease(ramp(T, 22.0, 27.0))) if ascend else 0.0
    cl = clouds_take(T, swirl, take, clear, center, roar_r, part)
    if part > 0:
        oy = 0.0 if STORM_MODE == 'up' else 20.0                           # 올려다볼 때는 용이 사라진 바로 그 점에서 갈라진다
        hole = np.exp(-(np.hypot(xxS - center[0], (yyS - center[1] + oy) * (1.0 if STORM_MODE == 'up' else 1.6)) / (50 + 150 * part)) ** 2)
        cl = cl * (1 - 0.75 * hole * part)
    # 비: 붓 비. 포효 때 빗줄기가 바깥으로 튕긴다(유체 변위), 접수하며 줄고, 승천 때 멎는다
    if ascend and STORM_MODE == 'up': rain_amt = (1.0 - 0.5 * take) * (1 - ease(ramp(phase_t, 3.3, ASC_VANISH - 0.2)))
    else: rain_amt = (1.0 - 0.5 * take) * (1 - ease(ramp(T, 21.5, 24.0)) if ascend else 1.0 - 0.5 * take)
    fdx = np.zeros((H, W), F32); fdy = np.zeros((H, W), F32)                 # 비는 거의 곧게(유체로 휘게 하면 마블링처럼 보였다)
    if roar_r is not None:
        DX, DY = xxS - e[0], yyS - e[1]; RR = np.hypot(DX, DY) + 1e-3
        push = 30 * S * np.exp(-((RR - roar_r) / (60.0 * S)) ** 2)
        fdx = fdx + push * DX / RR; fdy = fdy + push * DY / RR
    if STORM_MODE in ('up', 'down'):
        rn = _storm['rain'].render(T + 100, amount=rain_amt, gust=0.8)
        if ascend: rn = rn * (1 - ease(ramp(phase_t, 3.3, ASC_VANISH - 0.2)))   # 용이 사라지기 직전에 비가 완전히 멎는다(결이 문턱 때문에 남지 않게)
    else:
        rn = _storm['rain'].render(T + 100, amount=rain_amt, gust=0.8, flow=(fdx, fdy))
    fx = 0.0
    for tf, a in ((1.2, 0.8), (5.0, 0.6), (8.7, 1.0), (8.85, 0.6), (14.0, 0.7)):
        if T >= tf: fx = max(fx, a * math.exp(-(T - tf) / 0.12))
    dens = cl * (1 - 0.6 * fx) + smoke + rn * (0.85 if STORM_MODE == 'up' else 0.55)   # 올려다볼 때는 쏟아지는 비가 주인공
    img = TF.PAPER * np.exp(-dens[..., None] * INK_ABS)
    img = img * (1 + 0.35 * fx)
    img = light(img, 'night', extra=fx) * 0.45 + light(img, 'silver', extra=fx) * 0.75
    if roar_r is not None:                                                 # 포효가 눈에 보이게: 입에서 퍼지는 고리 세 겹이 화면 전체를 밀어낸다
        DX, DY = xxS - e[0], yyS - e[1]; RR = np.hypot(DX, DY) + 1e-3
        disp = np.zeros_like(RR); ringd = np.zeros_like(RR)
        for kq in range(3):
            Rk = roar_r - kq * 150 * S
            if Rk <= 0: continue
            g = np.exp(-((RR - Rk) / (26.0 * S)) ** 2) * (1 - roar) * (1 - 0.25 * kq)
            disp += 14 * S * g; ringd += g
        img = cv2.remap(img.astype(F32), (xxS - disp * DX / RR).astype(F32), (yyS - disp * DY / RR).astype(F32), cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
        img = img * (1 - 0.10 * ringd[..., None])
    if ascend:                                                              # 해돋이: 구름 사이로 금빛 해, 빛줄기, 구름 테 — 원반 하나로 끝내지 않는다
        if STORM_MODE == 'up':
            sun = ease(ramp(phase_t, ASC_SUN, ASC_SUN + 2.1)); sc = center
        else:
            sun = ease(ramp(T, 23.0, 27.5)); sc = (center[0], center[1] - 10 * S + 70 * S * (1 - sun))
        r = np.hypot(xxS - sc[0], yyS - sc[1])
        yv = yyS / H
        dawn_sky = np.stack([0.30 + 0.62 * yv, 0.30 + 0.45 * yv, 0.34 + 0.22 * yv], -1).astype(F32)   # 위는 서늘한 먹빛, 아래로 갈수록 금빛
        img = img * (1 - 0.7 * sun) + img * dawn_sky * 1.6 * 0.7 * sun
        core = np.exp(-(r / (34 * S)) ** 4) * sun
        halo = (np.exp(-(r / (120 * S)) ** 2) * 0.55 + np.exp(-(r / (420 * S)) ** 2) * 0.35) * sun
        occl = np.clip(cl - 0.18, 0, 1) * 1.6                               # 해를 가리는 구름
        bright = np.clip(core + halo * 0.6, 0, 1.4) * np.clip(1 - occl, 0, 1)
        rays = bright.copy()                                                # 빛줄기: 해 중심으로 반복 방사 흐림
        for scl in (1.04, 1.08, 1.16, 1.32, 1.64):
            M = np.array([[1 / scl, 0, sc[0] * (1 - 1 / scl)], [0, 1 / scl, sc[1] * (1 - 1 / scl)]], F32)
            rays = np.maximum(rays, cv2.warpAffine(rays, M, (W, H)) * 0.93)
        rays = cv2.GaussianBlur(rays, (0, 0), 3 * S) * np.clip(1 - occl * 0.6, 0, 1)
        gold = np.array((1.0, 0.86, 0.60), F32); amber = np.array((1.0, 0.62, 0.30), F32)
        img = img + (halo * (1 - 0.5 * occl))[..., None] * amber * 0.45 + rays[..., None] * gold * 0.45
        clb = cv2.GaussianBlur(cl.astype(F32), (0, 0), 3.0 * S)              # 종이 결 잡음까지 금빛으로 반짝이지 않게 구름 덩어리만
        rimc = np.clip(np.abs(cv2.Laplacian(clb, cv2.CV_32F, ksize=5)) * 0.10 * (3.0 * S) ** 1.2, 0, 1) * np.exp(-(r / (520 * S)) ** 2) * sun
        img = img + rimc[..., None] * gold * 0.8                           # 해를 향한 구름 가장자리가 금빛으로
        img = img * (1 - core[..., None] * 0.6) + core[..., None] * np.array((1.0, 0.95, 0.82), F32) * 1.05 * np.clip(1 - occl, 0.25, 1)[..., None]
        if STORM_MODE == 'up' and phase_t >= ASC_VANISH - 0.1:              # 용이 사라진 자리에 빛의 '점' 하나 → 정적 1초 → 해가 터져 나온다
            pt = ease(ramp(phase_t, ASC_VANISH - 0.1, ASC_VANISH + 0.15)) * (1 - sun)
            rp = (2.5 + 4.0 * ramp(phase_t, ASC_VANISH, ASC_SUN)) * S
            dot = np.exp(-(r / rp) ** 2) + 0.35 * np.exp(-(r / (rp * 5)) ** 2)
            img = img + (dot * pt)[..., None] * np.array((1.0, 0.93, 0.78), F32)
            if phase_t >= ASC_SUN:
                ub = phase_t - ASC_SUN
                Rb = (40 + 1400 * ub ** 0.7) * S                            # 터지는 빛의 고리(한 번)
                ring = np.exp(-((r - Rb) / (60 * S)) ** 2) * math.exp(-ub / 0.5)
                img = img + (ring * 0.35)[..., None] * np.array((1.0, 0.88, 0.62), F32) + 0.25 * math.exp(-ub / 0.18)
    a_ = np.clip(live * 1.5, 0, 1)[..., None]
    lit = light(TF.PAPER * np.exp(-live[..., None] * INK_ABS), 'silver', extra=fx) * 1.1
    img = img * (1 - a_) + lit * a_
    img = glint(img, e, kk, 0.6 + 0.6 * roar * (1 - roar))
    if ascend and STORM_MODE == 'up' and phase_t >= WHIP[2]:               # 꼬리가 렌즈를 친 자국: 흐린 먹 방울이 렌즈에 남았다가 흘러내리며 옅어짐
        u_ = phase_t - WHIP[2]
        if u_ < 2.4:
            lens = _whip_splat()
            M = np.float32([[1, 0, 0], [0, 1, 60 * S * u_ ** 1.6]])
            lens = cv2.warpAffine(lens, M, (W, H))
            img = img * np.exp(-(lens * (1 - ease(ramp(u_, 0.4, 1.8))))[..., None] * INK_ABS)
            if u_ < 0.35:                                                  # 맞는 순간: 흔들림 + 번쩍
                dx_ = int(14 * S * math.sin(u_ * 90) * (1 - u_ / 0.35)); dy_ = int(9 * S * math.cos(u_ * 70) * (1 - u_ / 0.35))
                img = np.roll(np.roll(img, dx_, 1), dy_, 0)
                img = img * (1 + 0.5 * math.exp(-u_ / 0.06))
    return img

WHIP = (0.55, 1.45, 1.0)                                                   # C21 시각: 꼬리 휘두름 시작, 끝, 렌즈를 치는 순간
_ws = {}
def _whip_splat():
    if 'm' not in _ws:
        r = np.random.default_rng(77); m = np.zeros((H, W), F32)
        for _ in range(5):                                                  # 꼬리가 쓸고 간 방향(왼쪽 아래 → 오른쪽 위)으로 흩뿌려진 몇 방울
            f_ = r.uniform(0.1, 0.9); cx, cy = (0.12 + 0.76 * f_) * W + r.normal(0, 0.05 * W), (0.72 - 0.40 * f_) * H + r.normal(0, 0.06 * H)
            rad = r.uniform(10, 34) * S
            cv2.ellipse(m, (int(cx), int(cy)), (int(rad * 1.5), int(rad)), -25, 0, 360, float(r.uniform(0.5, 0.9)), -1, cv2.LINE_AA)
            for _ in range(int(r.integers(2, 6))):
                a_ = math.radians(-25) + r.normal(0, 0.5); dd = rad * r.uniform(1.6, 3.2)
                cv2.circle(m, (int(cx + math.cos(a_) * dd), int(cy + math.sin(a_) * dd)), max(1, int(rad * r.uniform(0.1, 0.25))), 0.6, -1, cv2.LINE_AA)
        _ws['m'] = cv2.GaussianBlur(m, (0, 0), 5 * S) * 0.9                 # 렌즈 위라 초점이 안 맞아 흐림
    return _ws['m']

# ---------------------------------------------------------------- 아침의 종이(남은 그림) — C23·C24가 같은 상태
import after as AF
_after = {}
def after_data():
    if 'z' not in _after:
        _after['z'] = np.load(os.path.join(C, 'leap' + SUF, 'after.npz'))
    z = _after['z']
    return z['drips'], z['wets_mm']

def after_plate(key, view):
    fn = os.path.join(C, f'after_{key}{SUF}.npz')
    if key not in _after and os.path.exists(fn):
        z = np.load(fn); _after[key] = (z['rgb'], z['fib'], z['dens'], z['pv'], z['X'], z['Y'])
    if key not in _after:
        from paper import paper_layers, paper_rgb
        fib, flk, mot, X, Y = paper_layers(view)
        rgb = paper_rgb(fib, flk, mot).astype(F32)
        off = ((X < 0) | (X > 640) | (Y < 0) | (Y > 420))
        rgb[off] = np.array((0.16, 0.11, 0.075), F32)
        drips, wets = after_data()
        dens, pv = AF.after_density(view, fib.astype(F32), X, Y, A2.A.dot(), drips, wets)
        _after[key] = (rgb, fib.astype(F32), dens, pv, X, Y)
        np.savez(fn, rgb=rgb, fib=fib.astype(F32), dens=dens, pv=pv, X=X, Y=Y)
    return _after[key]

TP = View(320, 210, 760, int(760 * 3.8 * S), int(760 * 3.8 * S * 9 / 16))  # 남은 그림 판(가까이 다가가도 선명하게)
def morning_light(img, X=None):
    img = light(img, 'morning')
    yy, xx = np.mgrid[0:H, 0:W].astype(F32)
    warm = np.clip(1.0 - np.hypot(xx / W - 0.85, yy / H - 0.05) / 1.3, 0, 1)   # 창(오른쪽 위)에서 드는 햇살
    return img * (0.90 + 0.22 * warm[..., None] * np.array((1.0, 0.93, 0.80), F32))

# ---------------------------------------------------------------- C23 화가의 시선(그림 전체 → 눈, 눈물) / C25 제목
# 같은 아침 종이를 세 배율의 판으로 그려 두고(먼 판 TP → 중간 MP → 눈 EP) 카메라 폭에 맞는 판에서 잘라 쓴다.
EYEC = (dragon.E[0] + 2.0, dragon.E[1] + 1.0)
PAINT_C, PAINT_W, EYE_W = (320.0, 212.0), 620.0, 74.0                    # 그림 전체(종이 안쪽만 — 양옆에 책상이 비치지 않게) ↔ 눈
_kz = EYE_W / PAINT_W
ZOOM_P = ((EYEC[0] - _kz * PAINT_C[0]) / (1 - _kz), (EYEC[1] - _kz * PAINT_C[1]) / (1 - _kz))   # 이 한 점을 중심으로 한 번에 줌(움직임이 중간에 바뀌지 않게)
def zoom_center(wmm):
    f = wmm / PAINT_W
    return ZOOM_P[0] + (PAINT_C[0] - ZOOM_P[0]) * f, ZOOM_P[1] + (PAINT_C[1] - ZOOM_P[1]) * f
_mc = zoom_center(220.0); _ec = zoom_center(95.0)
MP = View(_mc[0], _mc[1], 300, int(W * 300 / 110), int(W * 300 / 110 * 9 / 16))
EP = View(_ec[0], _ec[1], 120, int(W * 120 / 74), int(W * 120 / 74 * 9 / 16))

def ring_state(X, Y, fib, pv, dens, lt):
    """눈물 상태(눈 근접 test_tear 방식). lt: 눈물 시계(2.6에 떨어지기 시작, 2.9에 닿음). 밀도와 젖은 정도(w, 안쪽, r)를 돌려준다."""
    Cc = np.array(dragon.E) + np.array((1.0, 0.0))
    R = np.hypot(X - Cc[0], Y - Cc[1]).astype(F32); ANG = np.arctan2(Y - Cc[1], X - Cc[0])
    WOB = 1 + 0.035 * np.sin(ANG * 3 + 1.1) + 0.015 * np.sin(ANG * 5 + 0.4) + 0.02 * (fib - 0.3)
    OLD = pv * 0.10
    T_DROP, FALL, R_MAX = 2.6, 0.30, 4.5
    land = T_DROP + FALL
    if lt < land: return dens, 0.0, None, 0.0, R, Cc
    uu = lt - land; r = R_MAX * (1 - math.exp(-uu / 0.18)); w = 1.0 - ramp(lt, land + 1.2, land + 3.6) * 0.85; g = ease(ramp(lt, land + 0.25, land + 3.4))
    inside = np.clip((r * WOB - R) / 0.25, 0, 1)
    mass = float((OLD * inside).sum())
    d2 = dens - OLD * inside * g * 0.8
    q = np.clip(R / (r * WOB), 0, 1.2)
    prof = (inside * q ** 7 + 0.55 * np.exp(-((R - r * WOB) / 0.28) ** 2)) * (0.75 + 0.5 * fib)
    ring = prof * (mass * 0.8 * g / (float(prof.sum()) + 1e-6)) + prof * 0.75 * g
    ppm = X.shape[1] / float(X[0, -1] - X[0, 0])                             # 판의 px/mm(테 번짐 0.046mm는 어느 판에서나 같게)
    d2 = d2 + cv2.GaussianBlur(ring.astype(F32), (0, 0), max(0.5, 0.046 * ppm))
    return d2, w, inside, r, R, Cc

def plate_img(key, view, lt_tear=None, title_ink=None):
    """판 하나의 그림(빛 전). lt_tear가 있으면 눈 둘레만 잘라 눈물 상태를 덧그린다(어느 판에서나 같은 테 — 물러날 때도 남는다)."""
    rgb, fib, dens, pv, X, Y = after_plate(key, view)
    bk = (key, None if title_ink is None else round(title_ink.amount, 3))
    if _after.get('pbase_key', {}).get(key) != bk:
        d = dens if title_ink is None else dens + title_ink(view, fib)
        _after.setdefault('pbase', {})[key] = (rgb * np.exp(-d[..., None] * INK_ABS)).astype(F32)
        _after.setdefault('pbase_key', {})[key] = bk
    base = _after['pbase'][key]
    if lt_tear is None or lt_tear < 2.9: return base
    ck = (bk, round(lt_tear * 12))
    if _after.get('pimg_key', {}).get(key) == ck: return _after['pimg'][key]
    Cc = np.array(dragon.E) + np.array((1.0, 0.0))
    px0, py0 = view.to_px(Cc[0] - 12, Cc[1] - 12); px1, py1 = view.to_px(Cc[0] + 12, Cc[1] + 12)
    x0, y0 = max(0, int(px0)), max(0, int(py0)); x1, y1 = min(view.W, int(px1) + 2), min(view.H, int(py1) + 2)
    img = base.copy()
    sl = (slice(y0, y1), slice(x0, x1))
    Xc, Yc, fc, pc, dc = X[sl], Y[sl], fib[sl], pv[sl], dens[sl]
    d, w, inside, r, R, Cc = ring_state(Xc, Yc, fc, pc, dc, lt_tear)
    if title_ink is not None: d = d + title_ink(view, fib)[sl]
    sub = rgb[sl] * np.exp(-d[..., None] * INK_ABS)
    if inside is not None:
        sub = sub * (1 - 0.05 * (inside * w)[..., None])
        hl = np.exp(-(((Xc - Cc[0] + 0.35 * r) ** 2 + (Yc - Cc[1] + 0.35 * r) ** 2) / (0.35 * r + 0.3) ** 2)) * w * inside
        sub = sub + (hl * 0.35)[..., None]
    img[sl] = sub
    _after.setdefault('pimg', {})[key] = img; _after.setdefault('pimg_key', {})[key] = ck
    return img

def cam_cut(img_plate, view, cx, cy, wmm):
    sc = view.ppm * wmm / W
    M = np.array([[sc, 0, (cx - view.cx) * view.ppm + view.W / 2 - sc * W / 2], [0, sc, (cy - view.cy) * view.ppm + view.H / 2 - sc * H / 2]], F32)
    return cv2.warpAffine(img_plate, M, (W, H), flags=cv2.WARP_INVERSE_MAP | cv2.INTER_AREA, borderValue=(0.12, 0.08, 0.055))

def paper_cam(cx, cy, wmm, lt_tear=None, title_ink=None):
    """카메라 폭에 맞는 판을 골라(경계에서는 겹쳐 넘김) 화면을 만든다."""
    out = None
    stages = [('trace', TP, 235, 210), ('mid', MP, 112, 96), ('eye', EP, 0, 0)]
    for i, (key, view, hi, lo) in enumerate(stages):
        prev_lo = stages[i - 1][3] if i else 1e9; prev_hi = stages[i - 1][2] if i else 1e9
        # 이 판이 쓰이는 폭: (lo .. prev_hi), 위 경계 prev_hi~prev_lo에서 서서히 들어오고 아래 경계 hi~lo에서 서서히 나감
        a_in = 1.0 if i == 0 else float(np.clip((prev_hi - wmm) / (prev_hi - prev_lo), 0, 1))
        a_out = 1.0 if hi == 0 else float(np.clip((wmm - lo) / (hi - lo), 0, 1))
        a = min(a_in, a_out) if i else a_out
        if a <= 0: continue
        im = cam_cut(plate_img(key, view, lt_tear, title_ink if key == 'trace' else None), view, cx, cy, wmm)
        out = im if out is None else out * (1 - a) + im * a
    return out

def ruler_and_slit(img, view):
    img = A2.slit(img, view)
    P0 = np.array((0.0, 318.0)); Uu = np.array((1.0, 1.0)) / math.sqrt(2); N = np.array((1.0, -1.0)) / math.sqrt(2)
    x0, y0, x1, y1 = view.bbox_mm(0)
    if x0 > 200 or y1 < 280: return img                                     # 자가 화면 밖
    Xv, Yv = view.grid_mm()
    ac = (Xv - P0[0]) * N[0] + (Yv - P0[1]) * N[1]; al = (Xv - P0[0]) * Uu[0] + (Yv - P0[1]) * Uu[1]
    rm = ((ac >= 0) & (ac <= 24) & (al >= -40) & (al <= 200)).astype(F32)
    nd = np.zeros_like(ac)
    for kq in range(-20, 200, 46): nd = np.maximum(nd, np.exp(-((al - kq) / 0.9) ** 2))
    gr = 0.05 * np.sin(ac * 9.0 + 0.7 * np.sin(al * 0.07)) + 0.03 * np.sin(ac * 23.0 + al * 0.02)
    bev = np.exp(-(ac / 0.9) ** 2) * 0.18 - np.exp(-((24 - ac) / 1.2) ** 2) * 0.15
    rsh = np.zeros((H, W), F32)
    rq = np.array([P0 + Uu * -40, P0 + Uu * 200, P0 + Uu * 200 + N * 24, P0 + Uu * -40 + N * 24]) + np.array((-1.6, 2.0))
    px_, py_ = view.to_px(rq[:, 0], rq[:, 1]); cv2.fillPoly(rsh, [np.stack([px_, py_], 1).astype(np.int32)], 1.0)
    img = img * (1 - 0.35 * cv2.GaussianBlur(rsh, (0, 0), 1.2 * view.ppm)[..., None])
    rcol = np.array((0.74, 0.61, 0.38), F32)[None, None, :] * (1 + gr + bev - 0.28 * nd)[..., None]
    return img * (1 - rm[..., None]) + rcol * rm[..., None]

def logzoom(u, w0, w1): return w0 * (w1 / w0) ** u
PUSH = (0.8, 11.6)                                                         # 응시: 그림 전체 → 눈(서두르지 않고)
TEAR_OFS = 9.8                                                             # 응시 컷 시각 − 눈물 시계(12.4초에 눈물이 떨어지기 시작)
def gaze_cam(lt):
    u = ease(ramp(lt, *PUSH))
    wmm = logzoom(u, PAINT_W, EYE_W)
    cx, cy = zoom_center(wmm)
    return cx, cy, wmm

def gaze(lt):
    """깨어난 화가가 자기 그림을 가만히 바라본다: 그림 전체에서 아주 천천히 눈으로 다가가고, 같은 컷 안에서 눈물이 떨어진다."""
    cx, cy, wmm = gaze_cam(lt)
    lt_t = lt - TEAR_OFS
    img = paper_cam(cx, cy, wmm, lt_tear=lt_t)
    view = View(cx, cy, wmm, W, H)
    img = A2.slit(img, view)                                                # 자는 화면에 두지 않는다(시선은 그림에만)
    X, Y = view.grid_mm()
    Cc = np.array(dragon.E) + np.array((1.0, 0.0))
    # 몸을 숙인 화가의 머리 그림자(창빛: 오른쪽 위에서) — 가까이 갈수록 짙어진다
    hx, hy = Cc[0] + 13 + 0.6 * math.sin(lt * 1.3), Cc[1] - 15
    shd = np.exp(-(((X - hx) / 15) ** 2 + ((Y - hy) / 12) ** 2) * 1.5) + np.exp(-(((X - hx - 14) / 20) ** 2 + ((Y - hy + 12) / 18) ** 2) * 1.5)
    img = img * (1 - 0.30 * ramp(lt, 8.0, 11.5) * np.clip(shd, 0, 1)[..., None])
    # 떨어지는 눈물: 화가의 눈(= 카메라 바로 앞)에서 떨어지므로 화면에서는 착지점 바로 아래에서 크게·흐리게 나타나
    # 착지점으로 모이며 작아진다. 종이에는 착지하기 전까지 아무것도 생기지 않는다(그림자만 착지점으로 다가옴).
    T_FALL0, LAND = 2.35, 2.9
    drop = None
    if T_FALL0 <= lt_t < LAND:
        uq = ((lt_t - T_FALL0) / (LAND - T_FALL0)) ** 2                    # 점점 빨라짐
        ex, ey = view.to_px(Cc[0], Cc[1])
        rs = (0.15 * H) * (1 - uq) + 1.3 * view.ppm * uq                    # 화면 반지름(가까울수록 크다)
        dx_, dy_ = ex + 0.02 * W * (1 - uq), ey + 0.26 * H * (1 - uq)
        sh_off = 40.0 * (1 - uq)                                              # 그림자: 높이만큼 왼쪽 아래로 밀림, 높을수록 흐리고 옅음
        sm = np.exp(-(((X - Cc[0] + 0.55 * sh_off) ** 2 + (Y - Cc[1] - 0.80 * sh_off) ** 2) / (1.2 + 0.25 * sh_off) ** 2))
        img = img * (1 - (0.10 + 0.25 * uq) * sm[..., None])
        drop = (dx_, dy_, rs, uq)
    out = morning_light(img)
    if drop is not None:
        dx_, dy_, rs, uq = drop
        yy, xx = np.mgrid[0:H, 0:W].astype(F32)
        rr = np.hypot(xx - dx_, (yy - dy_) * 1.08)
        inside = np.clip((rs - rr) / max(1.0, 0.06 * rs), 0, 1)
        q = np.clip(rr / rs, 0, 1)
        mag = 0.55 + 0.25 * q ** 2                                            # 물방울 렌즈: 가운데가 확대되고 뒤집혀 보임
        lens = cv2.remap(out.astype(F32), (dx_ - (xx - dx_) * mag).astype(F32), (dy_ - (yy - dy_) * mag).astype(F32), cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
        lens = lens * (0.92 + 0.08 * (1 - q))[..., None]
        rim = np.exp(-((rr - rs * 0.93) / (0.07 * rs + 0.6)) ** 2)
        spec = np.exp(-((xx - dx_ - 0.35 * rs) ** 2 + (yy - dy_ + 0.40 * rs) ** 2) / (0.12 * rs + 0.8) ** 2)
        a_ = (inside * (0.55 + 0.45 * uq))[..., None]
        drop_img = lens * (1 - 0.30 * rim[..., None]) + (spec * 0.55)[..., None]
        blur = (1 - uq) * 0.04 * H                                           # 눈앞이라 초점이 안 맞음
        if blur > 1.0:
            drop_img = cv2.GaussianBlur(drop_img, (0, 0), blur * 0.35); a_ = cv2.GaussianBlur(a_[..., 0], (0, 0), blur * 0.5)[..., None]
        out = out * (1 - a_) + drop_img * a_
    _after['last_gaze'] = out
    return out

# ---- 제목: 우리 붓 엔진으로 쓴 '점'(종이에 스며드는 먹) + 좌하단 허상공방 낙관과 크레딧(명조, 타자 효과·소리 없음)
TITLE_BOX = (500.0, 58.0, 100.0)                                           # 종이 mm: 왼쪽 위 x, y, 글자 크기
def title_strokes():
    x0, y0, sz = TITLE_BOX
    q = lambda pts: [(x0 + px * sz / 100, y0 + py * sz / 100) for px, py in pts]
    k = sz / 100
    def pr(*v):                                                            # 압력 곡선(u 0~1에 고르게 놓인 값)
        return lambda u: np.interp(u, np.linspace(0, 1, len(v)), v)
    return [
        Stroke(q([(4, 15), (17, 11), (31, 10), (44, 12)]), 11 * k, load=1.35, dry=0.22, seed=401, press=pr(1.0, 0.8, 0.72, 0.75, 0.95), wet=0.3),       # ㅈ 가로(끝을 눌러 멈춤)
        Stroke(q([(33, 15), (29, 25), (20, 37), (6, 49)]), 12 * k, load=1.35, dry=0.35, seed=402, press=pr(1.0, 0.95, 0.8, 0.5, 0.12), wet=0.3),       # ㅈ 삐침(빠지며 갈라짐)
        Stroke(q([(24, 30), (33, 36), (42, 42), (51, 48)]), 13 * k, load=1.3, dry=0.28, seed=403, press=pr(0.4, 0.7, 0.95, 1.05, 0.85), wet=0.3),      # ㅈ 파임(끝을 눌러 뻗음)
        Stroke(q([(53, 31), (61, 31.5), (70, 32)]), 10 * k, load=1.3, dry=0.2, seed=404, press=pr(0.95, 0.8, 0.85), wet=0.3),                          # ㅓ 짧은 가로
        Stroke(q([(75, 1), (74.5, 20), (74, 41), (73, 62)]), 14 * k, load=1.4, dry=0.42, seed=405, press=pr(1.05, 0.92, 0.88, 0.75, 0.3), wet=0.3),    # ㅓ 세로(비백)
        Stroke(q([(18, 69), (19, 84), (20, 98)]), 11 * k, load=1.3, dry=0.22, seed=406, press=pr(1.0, 0.85, 0.85, 0.8), wet=0.3),                      # ㅁ 왼 세로
        Stroke(q([(19, 69), (47, 67), (77, 67)]), 11 * k, load=1.3, dry=0.25, seed=407, press=pr(0.95, 0.75, 0.75, 1.0), wet=0.3),                     # ㅁ 위
        Stroke(q([(78, 66), (79, 72), (78, 86), (77, 99)]), 11.5 * k, load=1.3, dry=0.3, seed=409, press=pr(1.05, 0.9, 0.85, 0.85), wet=0.3),          # ㅁ 오른(꺾어 내림)
        Stroke(q([(21, 97), (48, 96), (77, 96.5)]), 10.5 * k, load=1.3, dry=0.3, seed=408, press=pr(0.9, 0.8, 0.75), wet=0.3),                         # ㅁ 아래
    ]

def title_ink_fn(amount):
    def f(view, fib):
        key = ('title_d', view.W)
        if key not in _after: _after[key] = render_strokes(view, title_strokes(), fib)
        d = _after[key]
        if amount >= 0.999: return d
        bl = cv2.GaussianBlur(d, (0, 0), max(1.0, 1.4 * view.ppm))        # 스며드는 동안: 흐린 먹 → 선명한 먹
        return (bl * (1 - amount) + d * amount) * ease(min(1.0, amount * 1.6))
    f.amount = amount
    return f

CREDIT = ['Created & Coded by L.S.M.', '허상공방 虛像工房 Project']
def credit_layer():
    if 'credit' in _after: return _after['credit']
    from PIL import Image, ImageDraw, ImageFont
    fnt = ImageFont.truetype('/usr/share/fonts/opentype/noto/NotoSerifCJK-Medium.ttc', int(15 * S), index=1)   # Noto Serif CJK KR
    sz = int(46 * S); x_seal, y_seal = int(W * 0.06), int(H * 0.845 - sz / 2)
    im = Image.new('L', (W, H), 0); d = ImageDraw.Draw(im)
    tx = x_seal + sz + int(15 * S)
    d.text((tx, y_seal + int(1 * S)), CREDIT[0], font=fnt, fill=255)
    d.text((tx, y_seal + sz - int(21 * S)), CREDIT[1], font=fnt, fill=255)
    tm = np.asarray(im, F32) / 255
    tm = cv2.GaussianBlur(tm, (0, 0), 0.35 * S)
    seal = cv2.resize(A2.A.seal_rgba(), (sz, sz), interpolation=cv2.INTER_AREA)
    _after['credit'] = (tm, seal, x_seal, y_seal, sz)
    return _after['credit']

def title(lt):
    """눈물로 찍힌 눈에서 천천히 물러나 그림 전체를 보이고, '점'이 종이에 스며든 뒤 낙관과 크레딧."""
    u = ease(ramp(lt, 0.5, 4.6))
    wmm = logzoom(u, EYE_W, PAINT_W)
    cx, cy = zoom_center(wmm)
    a_t = ease(ramp(lt, 4.7, 6.2))
    img = paper_cam(cx, cy, wmm, lt_tear=16.0 - TEAR_OFS + lt, title_ink=title_ink_fn(a_t) if a_t > 0 else None)
    img = A2.slit(img, View(cx, cy, wmm, W, H))
    img = morning_light(img)
    base = _after.get('last_gaze')
    if base is not None and lt < 0.5:
        k = ease(ramp(lt, 0.0, 0.5)); img = base * (1 - k) + img * k
    if lt > 6.4:
        tm, seal, xs, ys, sz = credit_layer()
        a1 = ease(ramp(lt, 6.4, 6.6))                                       # 낙관: 찍힌다
        al = seal[..., 3:4] * a1 * np.clip((seal[..., 0:1] - seal[..., 1:2]) * 4, 0, 1)   # 인주가 묻은 곳만(흰 바탕 테두리 없이)
        sub = img[ys:ys + sz, xs:xs + sz]; img[ys:ys + sz, xs:xs + sz] = sub * (1 - al + al * seal[..., :3])       # 인주: 종이에 곱해짐(흰 바탕은 그대로)
        a2 = ease(ramp(lt, 6.9, 7.9))                                       # 크레딧: 먹이 스며들 듯
        img = img * np.exp(-(tm * 1.9 * a2)[..., None] * INK_ABS)
    return img * (1 - ease(ramp(lt, 8.8, 10.0)))

def storm(lt): return storm_frame(lt, lt, 22.0)
def ascend(lt): return storm_frame(20.0 + lt * 0.85, lt, 10.0, ascend=True) if False else storm_frame(22.0 + lt * 0.75, lt, 10.0, ascend=True)

# ---------------------------------------------------------------- 렌더
def frame(k):
    t = k / FPS
    for name, kind, t0, d in CUTS:
        if t0 <= t < t0 + d: break
    lt = t - t0; kk = int(round(lt * FPS))
    if kind == 'room_paint': f8 = fin(A2.room_paint(lt), t)
    elif kind == 'room_sleep': f8 = fin(A2.room_sleep(lt), t)
    elif kind == 'room_cut': f8 = fin(A2.room_cut(lt), t)
    elif kind == 'room_wake': f8 = fin(A2.room_wake(lt * 10 / 7), t)
    elif kind == 'hand_A': f8 = A2.borrowed(os.path.join(C, 'hand_test2' + SUF, 'h*.png'), kk)
    elif kind == 'hand_B': f8 = A2.borrowed(os.path.join(C, 'hand_test2' + SUF, 'h*.png'), 65 + kk)
    elif kind == 'knife': f8 = A2.borrowed(os.path.join(C, 'knife_test' + SUF, 'k*.png'), kk)
    elif kind == 'sill': f8 = fin(sill(lt), t)
    elif kind == 'journey':
        img = A2.A.frame(A2.J_OLD[0] + lt * (A2.J_OLD[1] - A2.J_OLD[0]) / 44.0)
        f8 = to8(img); name = A2.J_NAMES.get(A2.TL.cut_at(math.floor((A2.J_OLD[0] + lt * 66 / 44) * 12) / 12)[0], 'J')
        name = {'C6': 'C7', 'C7': 'C8', 'C8': 'C9', 'C9': 'C10', 'C10': 'C11', 'C11': 'C12', 'C12': 'C13'}.get(name, name)
    elif kind == 'life': f8 = fin(life(lt), t)
    elif kind == 'struggle': f8 = fin(struggle(lt), t)
    elif kind == 'leap': f8 = A2.borrowed(os.path.join(C, 'leap' + SUF, 'f*.png'), 12 + kk)
    elif kind == 'lookback': f8 = fin(lookback(lt), t)
    elif kind == 'exit': f8 = fin(exitw(lt), t)
    elif kind == 'storm': f8 = fin(storm(lt), t, vig=0.26)
    elif kind == 'ascend': f8 = fin(ascend(lt), t, vig=0.24)
    elif kind == 'gaze': f8 = fin(gaze(lt), t)
    elif kind == 'title': f8 = fin(title(lt), t, vig=0.15)
    return A2.lab(f8, name, t) if S == 1 else f8                            # 최종(배율 2)에는 컷 이름표 없음

def run(names):
    A2.build_dot()
    for name, kind, t0, d in CUTS:
        if name not in names: continue
        for k in range(int(round(t0 * FPS)), int(round((t0 + d) * FPS))):
            fn = os.path.join(OUT, f'a{k:05d}.png')
            if os.path.exists(fn): continue
            cv2.imwrite(fn, frame(k))
        print('done', name, flush=True)

def encode():
    import anim_audio3
    wav = os.path.join(C, 'animatic3.wav'); anim_audio3.build(wav, TOTAL)
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-framerate', str(FPS), '-i', os.path.join(OUT, 'a%05d.png'), '-i', wav,
                    '-vf', 'fps=24', '-c:v', 'libx264', '-crf', '22', '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-b:a', '192k',
                    '-shortest', os.path.join(C, 'jeom_animatic_v3.mp4')])

if __name__ == '__main__':
    cmd = sys.argv[1]
    if cmd == 'cut': run(sys.argv[2:])
    elif cmd == 'all': run([c[0] for c in CUTS])
    elif cmd == 'encode': encode()
    elif cmd == 'still':                                                    # 컷 하나의 여러 시각(컷 상대 시각)을 순서대로 렌더(상태가 있는 컷 대비)
        A2.build_dot()
        cut = sys.argv[2]; ts = list(map(float, sys.argv[3:]))
        c = [x for x in CUTS if x[0] == cut][0]
        last = max(ts); ims = []
        for k in range(0, int(round(last * FPS)) + 1):
            f = frame(int(round(c[2] * FPS)) + k)
            if any(abs(k / FPS - tt) < 1e-6 for tt in ts):
                ims.append(f); cv2.imwrite(os.path.join(C, f'a3_{cut}_{len(ims)}.png'), f)
        cv2.imwrite(os.path.join(C, f'a3_{cut}.jpg'), cv2.resize(np.vstack([np.hstack(ims[i:i + 3]) for i in range(0, len(ims) - len(ims) % 3 or 3, 3)]), None, fx=0.5, fy=0.5), [cv2.IMWRITE_JPEG_QUALITY, 88])
