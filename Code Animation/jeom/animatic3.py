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
    ('C23', 'trace', 165.5, 9.0),
    ('C24', 'tear', 174.5, 7.0),
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

def live3(pts, cum, t=0.0, k_load=1.0, breathe=0.0, curl=0.0, jaw=0.0, lift=None, mir=1.0, scale=1.0, wh=1.0):
    """L.live_strokes와 같되, 살아 있는 변형을 더한다. lift(s_world) → 카메라 쪽으로 들리는 양(월드 z)."""
    out = []; bodyw = []
    for j, (kind, st, sad) in enumerate(L.REC):
        name = st.name
        if name in JAWN and jaw != 0.0:
            sad = jaw_sad(st, -jaw)
        s, a, d = sad[:, 0] * L.U, sad[:, 1] * L.U * scale, sad[:, 2] * L.U * scale
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

def pupil(img_dens, pts, cum, mir=1.0, amt=2.6, jaw=0.0, scale=1.0):
    """눈동자(점) 밀도를 더하고 화면 위치를 돌려준다."""
    sad = L.to_spine(np.array([dragon.E]), head=True)
    P, Tq, Nq = L.frame_along(pts, cum, np.array([0.0]))
    Pe = P + (-L.TSIGN) * Tq * sad[:, 1:2] * L.U * scale + mir * L.NSIGN * Nq * sad[:, 2:3] * L.U * scale
    e2, ze = L.project(Pe); kk = L.F * L.U / ze[0] * scale
    yy, xx = np.mgrid[0:H, 0:W].astype(F32)
    r = np.hypot(xx - e2[0, 0] - 1.0 * kk, yy - e2[0, 1])
    return img_dens + amt * np.clip((4.3 * kk - r) / (0.8 * kk), 0, 1), e2[0], kk

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
    live, e, kk = pupil(live, pts, cum)
    pap = paper_view(L.CLOUD, cam)
    if lt > 3: _bl_life.add(lt, int(_bl_life.r.integers(0, 3)))
    wet, rim = _bl_life.render(lt)
    img = rain_on_paper(ink_over(pap, live, halo=0.15 * ramp(lt, 3, 10)), wet, rim)
    img = light(img, 'night', extra=0.0)
    return glint(img, e, kk, 0.55 + 0.25 * math.sin(lt * 2.0))

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
    pap = paper_view(L.CLOUD + L.BODY_ON_PAPER * 0.25 * ramp(lt, 0.8, 1.2), cam)
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
    neck = math.pi * turn * np.clip(1 - sig / (0.24 * SLW), 0, 1) ** 1.4
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

def lookback(lt):
    """창 앞에 떠서(몸은 물결치며 숨 쉼) 창을 보다가 → 목을 꺾어 잠든 화가를 오래 돌아보고 → 다시 창으로."""
    R = A2.room()
    base = R.render(lt + 200, dict(POSES['sleep']), lamp_on=0.0, rain=1.0, flash=0.0)
    turn = ease(ramp(lt, 1.0, 2.6)) * (1 - ease(ramp(lt, 5.0, 5.9)))
    turn = step(turn, 6)
    bob = (0.0, 0.10 * math.sin(lt * 1.7))
    d, e, kk = dragon_hover(lt, turn, bob)
    img, e2, k2 = place(base, d, e, kk, W * 0.70, H * 0.31, 0.27)
    look = ramp(lt, 2.6, 3.0) * (1 - ramp(lt, 4.8, 5.0))
    return glint(img, e2, k2, 0.35 + 0.35 * look)

def exitw(lt):
    R = A2.room()
    base = R.render(lt + 210, dict(POSES['sleep']), lamp_on=0.0, rain=1.0, flash=0.7 * math.exp(-(lt - 2.2) / 0.12) if lt >= 2.2 else 0)
    u = ease(ramp(lt, 0.2, 3.2))
    d, e, kk = dragon_hover(lt + 6.0, 0.0, (0.0, 0.0))
    cx = W * (0.70 + 0.05 * u); cy = H * (0.31 - 0.07 * u); s_ = 0.27 * (1 - 0.8 * u)
    yy, xx = np.mgrid[0:H, 0:W].astype(F32)
    win = ((xx > W * 0.565) & (xx < W * 0.835) & (yy > H * 0.145) & (yy < H * 0.495)).astype(F32)
    clip = np.clip(win + (1 - ramp(lt, 1.0, 1.6)), 0, 1)
    img, e2, k2 = place(base, d, e, kk, cx, cy, s_, clip=clip)
    return img

# ---------------------------------------------------------------- C20 폭풍 / C21 승천·해돋이
_storm = {}
def storm_init():
    if _storm: return
    _storm['rain'] = InkRain(W, H, angle=-12, seed=7, fib=TF.FIB, scale=S)
    _storm['fl'] = TF.Fluid()
    _storm['prev'] = None
KS = np.array([(-7, -9, 9), (-4, -5.5, 8.5), (-1.5, -2.5, 8.2), (1.8, -0.5, 8.6), (2.6, 1.6, 9.4), (0.4, 2.4, 10.2),
               (-2.4, 1.4, 10.6), (-2.6, -0.4, 10.4), (-0.8, -1.2, 9.6), (1.4, -0.2, 9.2), (1.2, 1.4, 9.8), (-0.6, 1.8, 10.6),
               (-1.6, 0.6, 11.0), (0.0, 0.0, 10.4), (0.0, 0.2, 10.0), (0.0, 3.0, 11.0), (0.0, 9.0, 13.0), (0.0, 20.0, 16.0)], float)
KST = np.array([-3.0, -1.5, 0.0, 2.0, 4.0, 6.0, 8.0, 10.0, 12.0, 13.5, 15.0, 16.5, 18.0, 19.5, 22.0, 25.0, 28.5, 31.5])
def storm_path(tau):
    tau = np.atleast_1d(np.asarray(tau, float))
    P = np.vstack([KS[:1] * 2 - KS[1:2], KS, KS[-1:] * 2 - KS[-2:-1]])
    i = np.clip(np.searchsorted(KST, tau, side='right') - 1, 0, len(KST) - 2)
    u = np.clip((tau - KST[i]) / (KST[i + 1] - KST[i]), 0, 1.5)[:, None]
    p0, p1, p2, p3 = P[i], P[i + 1], P[i + 2], P[i + 3]
    return 0.5 * ((2 * p1) + (-p0 + p2) * u + (2 * p0 - 5 * p1 + 4 * p2 - p3) * u ** 2 + (-p0 + 3 * p1 - 3 * p2 + p3) * u ** 3)

def storm_trail(t):
    taus = np.linspace(t - 6.0, t, 600)
    pts = storm_path(taus)
    seg = np.linalg.norm(np.diff(pts, axis=0), axis=1); cum = np.concatenate([[0], np.cumsum(seg)])
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
    sts, bodyw = live3(pts, cum, t=T, k_load=k_load, breathe=math.sin(T * 3), curl=0.6, jaw=jaw, scale=scale, wh=1.6)
    live = render_strokes(L.SV, sts, L.SFIB)
    live, e, kk = pupil(live, pts, cum, scale=scale)
    vis = 1.0
    if ascend:
        vis = 1.0 - ease(ramp(T, 26.0, 28.0))
    live = live * vis
    # 유체: 씻겨 내리는 먹(무거워 아래로 흐름), 몸의 움직임이 공기를 끈다
    S2, Z = L.project(pts[-80::4])
    if _storm['prev'] is not None:
        v = (S2[-1] - _storm['prev']) * FPS
        for j in range(0, len(S2), 2):
            fl.splat(S2[j][0], S2[j][1] + 10 * S, (0.02 + 0.22 * wash) * vis, v[0] * 0.4, v[1] * 0.4 + 140 * S * wash, 18 * S)
    _storm['prev'] = S2[-1].copy()
    center = (W * 0.5, H * 0.44)
    if take > 0:
        DX, DY = xxS - center[0], yyS - center[1]; RR = np.hypot(DX, DY) + 1e-3
        wv = 70 * S * take * (1 - ramp(T, 21, 24))
        fl.u += cv2.resize((-DY / RR) * wv * np.exp(-RR / (300 * S)), (TF.GW, TF.GH)) / TF.GS * 0.02
        fl.v += cv2.resize((DX / RR) * wv * np.exp(-RR / (300 * S)), (TF.GW, TF.GH)) / TF.GS * 0.02
    for _ in range(2): fl.step(1 / (FPS * 2))
    smoke = 0.9 * np.tanh(np.clip(cv2.resize(fl.d, (W, H), interpolation=cv2.INTER_CUBIC), 0, None) * 1.2)
    clear = 0.2 * ease(ramp(T, 22.5, 26.5)) if ascend else 0.0
    swirl = 2.6 * take
    roar_r = (80 + 900 * roar) * S if 8.6 <= T < 11.5 else None
    part = ease(ramp(T, 22.0, 27.0)) if ascend else 0.0
    cl = clouds_take(T, swirl, take, clear, center, roar_r, part)
    if part > 0:
        hole = np.exp(-(np.hypot(xxS - center[0], (yyS - center[1] + 20) * 1.6) / (50 + 150 * part)) ** 2)
        cl = cl * (1 - 0.75 * hole * part)
    # 비: 붓 비. 포효 때 빗줄기가 바깥으로 튕긴다(유체 변위), 접수하며 줄고, 승천 때 멎는다
    rain_amt = (1.0 - 0.5 * take) * (1 - ease(ramp(T, 21.5, 24.0)) if ascend else 1.0 - 0.5 * take)
    fdx = np.zeros((H, W), F32); fdy = np.zeros((H, W), F32)                 # 비는 거의 곧게(유체로 휘게 하면 마블링처럼 보였다)
    if roar_r is not None:
        DX, DY = xxS - e[0], yyS - e[1]; RR = np.hypot(DX, DY) + 1e-3
        push = 30 * S * np.exp(-((RR - roar_r) / (60.0 * S)) ** 2)
        fdx = fdx + push * DX / RR; fdy = fdy + push * DY / RR
    rn = _storm['rain'].render(T + 100, amount=rain_amt, gust=0.8, flow=(fdx, fdy))
    fx = 0.0
    for tf, a in ((1.2, 0.8), (5.0, 0.6), (8.7, 1.0), (8.85, 0.6), (14.0, 0.7)):
        if T >= tf: fx = max(fx, a * math.exp(-(T - tf) / 0.12))
    dens = cl * (1 - 0.6 * fx) + smoke + rn * 0.55
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
        sun = ease(ramp(T, 23.0, 27.5))
        sc = (center[0], center[1] - 10 * S + 70 * S * (1 - sun))
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
        rimc = np.clip(np.abs(cv2.Laplacian(cl.astype(F32), cv2.CV_32F, ksize=5)) * 0.10, 0, 1) * np.exp(-(r / (520 * S)) ** 2) * sun
        img = img + rimc[..., None] * gold * 0.8                           # 해를 향한 구름 가장자리가 금빛으로
        img = img * (1 - core[..., None] * 0.6) + core[..., None] * np.array((1.0, 0.95, 0.82), F32) * 1.05 * np.clip(1 - occl, 0.25, 1)[..., None]
    a_ = np.clip(live * 1.5, 0, 1)[..., None]
    lit = light(TF.PAPER * np.exp(-live[..., None] * INK_ABS), 'silver', extra=fx) * 1.1
    img = img * (1 - a_) + lit * a_
    img = glint(img, e, kk, 0.6 + 0.6 * roar * (1 - roar))
    return img

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

def trace(lt):
    rgb, fib, dens, pv, X, Y = after_plate('trace', TP)
    if 'trace_img' not in _after:
        _after['trace_img'] = (rgb * np.exp(-dens[..., None] * INK_ABS)).astype(F32)
    pap = _after['trace_img']
    u = ease(ramp(lt, 2.2, 5.4))
    cx, cy, wmm = 320 + (110 - 320) * u, 215 + (360 - 215) * u, 700 + (260 - 700) * u
    sc = TP.ppm * wmm / W
    M = np.array([[sc, 0, (cx - TP.cx) * TP.ppm + TP.W / 2 - sc * W / 2], [0, sc, (cy - TP.cy) * TP.ppm + TP.H / 2 - sc * H / 2]], F32)
    img = cv2.warpAffine(pap, M, (W, H), flags=cv2.WARP_INVERSE_MAP | cv2.INTER_AREA, borderValue=(0.12, 0.08, 0.055))
    view = View(cx, cy, wmm, W, H)
    img = A2.slit(img, view)
    P0 = np.array((0.0, 318.0)); Uu = np.array((1.0, 1.0)) / math.sqrt(2); N = np.array((1.0, -1.0)) / math.sqrt(2)
    # 밤새 그대로 놓여 있던 대나무 자(C4와 같은 자리·결)
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
    img = img * (1 - rm[..., None]) + rcol * rm[..., None]
    base = P0 + Uu * 110 + N * 8; hover = P0 + Uu * 112 - N * 3; away = np.array((-60.0, 470.0))
    away = base + np.array((40.0, 30.0))                                      # 거둬서 종이 밖(책상)에 내려놓는다
    if lt < 5.6: pos, h = base, 0.0
    elif lt < 6.4: pos, h = base + (hover - base) * ease(ramp(lt, 5.6, 6.4)), 12 * ease(ramp(lt, 5.6, 6.4))
    elif lt < 7.6: pos, h = hover + np.array(A2.trem(lt, 0.9)), 12.0
    else: pos, h = hover + (away - hover) * ease(ramp(lt, 7.6, 8.8)), 12 * (1 - ease(ramp(lt, 7.6, 8.8)))
    f_ = Uu; g_ = -N
    blade = [pos, pos + f_ * 30 + g_ * 0.8, pos + f_ * 30 + g_ * 9.5, pos + f_ * 13 + g_ * 9.5]
    handle = [pos + f_ * 30 + g_ * 0.2, pos + f_ * 115 + g_ * 0.6, pos + f_ * 115 + g_ * 10.2, pos + f_ * 30 + g_ * 10.0]
    def pp(pts, off=(0, 0)):
        a_ = np.array(pts) + np.array(off); x, y = view.to_px(a_[:, 0], a_[:, 1]); return np.stack([x, y], 1).astype(np.int32)
    sh = np.zeros((H, W), F32); off = np.array((-0.6, 0.5)) * (h + 4)
    cv2.fillPoly(sh, [pp(blade, off)], 1.0); cv2.fillPoly(sh, [pp(handle, off * 1.2)], 1.0)
    handle = [pos + f_ * 30 + g_ * 0.2, pos + f_ * 170 + g_ * 0.6, pos + f_ * 170 + g_ * 10.2, pos + f_ * 30 + g_ * 10.0]   # 자루는 화면 밖(손)까지
    if 5.4 < lt < 9.0:                                                        # 칼을 쥔 손·소매 그림자(창빛: 오른쪽 위 → 왼쪽 아래로 드리움)
        hm = np.zeros((H, W), F32)
        for along, z, rx, ry in ((125, 40 + h, 22, 16), (185, 70 + h, 44, 28)):
            c_ = pos + f_ * along + np.array((-0.6, 0.5)) * 0.4 * z; px_, py_ = view.to_px(c_[0], c_[1])
            cv2.ellipse(hm, (int(px_), int(py_)), (int(rx * view.ppm), int(ry * view.ppm)), 45, 0, 360, 1.0, -1, cv2.LINE_AA)
        sh = np.maximum(sh, cv2.GaussianBlur(hm, (0, 0), 3 * view.ppm) * 0.8 * ramp(lt, 5.4, 5.8) * (1 - ramp(lt, 8.6, 9.0)))
    img = img * (1 - 0.4 * cv2.GaussianBlur(sh, (0, 0), 1 + 0.15 * h * view.ppm)[..., None])
    lay = np.zeros_like(img); m = np.zeros((H, W), F32)
    cv2.fillPoly(lay, [pp(handle)], (0.30, 0.19, 0.12)); cv2.fillPoly(m, [pp(handle)], 1.0)
    cv2.fillPoly(lay, [pp(blade)], (0.68, 0.70, 0.72)); cv2.fillPoly(m, [pp(blade)], 1.0)
    m = cv2.GaussianBlur(m, (0, 0), 0.7 * S)[..., None]
    img = img * (1 - m) + lay * m
    return morning_light(img)

VE = View(dragon.E[0] + 2, dragon.E[1] + 1, 74, W, H)
def tear(lt):
    """같은 아침 종이(after)의 눈 근접. 눈물 → 남은 점의 흔적이 녹아 테로 모임(test_tear와 같은 방식)."""
    rgb, fib, dens, pv, X, Y = after_plate('tear', VE)
    Cc = np.array(dragon.E) + np.array((1.0, 0.0))
    R = np.hypot(X - Cc[0], Y - Cc[1]).astype(F32); ANG = np.arctan2(Y - Cc[1], X - Cc[0])
    WOB = 1 + 0.035 * np.sin(ANG * 3 + 1.1) + 0.015 * np.sin(ANG * 5 + 0.4) + 0.02 * (fib - 0.3)
    OLD = pv * 0.10                                                          # 눈동자였던 점의 흔적(종이 dens 안에 이미 들어 있음)
    T_DROP, FALL, R_MAX = 2.6, 0.30, 4.5
    land = T_DROP + FALL
    if lt < land: r, w, g = 0.0, 0.0, 0.0
    else:
        uu = lt - land; r = R_MAX * (1 - math.exp(-uu / 0.18)); w = 1.0 - ramp(lt, land + 1.2, land + 3.6) * 0.85; g = ease(ramp(lt, land + 0.25, land + 3.4))
    inside = np.clip((r * WOB - R) / 0.25, 0, 1) if r > 0 else np.zeros_like(R)
    mass = float((OLD * inside).sum())
    d2 = dens - OLD * inside * g * 0.8
    if r > 0:
        q = np.clip(R / (r * WOB), 0, 1.2)
        prof = (inside * q ** 7 + 0.55 * np.exp(-((R - r * WOB) / 0.28) ** 2)) * (0.75 + 0.5 * fib)
        ring = prof * (mass * 0.8 * g / (float(prof.sum()) + 1e-6)) + prof * 0.75 * g
        d2 = d2 + cv2.GaussianBlur(ring.astype(F32), (0, 0), 0.6 * S)
    img = rgb * np.exp(-d2[..., None] * INK_ABS)
    img = img * (1 - 0.05 * (inside * w)[..., None])
    hx, hy = Cc[0] + 13 + 0.6 * math.sin(lt * 1.3), Cc[1] - 15
    shd = np.exp(-(((X - hx) / 15) ** 2 + ((Y - hy) / 12) ** 2) * 1.5) + np.exp(-(((X - hx - 14) / 20) ** 2 + ((Y - hy + 12) / 18) ** 2) * 1.5)
    img = img * (1 - 0.30 * np.clip(shd, 0, 1)[..., None])
    if T_DROP - 0.6 <= lt < land:
        hgt = 40.0 if lt < T_DROP else 40.0 * (1 - ((lt - T_DROP) / FALL) ** 2)
        sm = np.exp(-(((X - Cc[0] - 0.275 * hgt) ** 2 + (Y - Cc[1] + 0.425 * hgt) ** 2) / (1.1 + 0.03 * hgt) ** 2))
        img = img * (1 - 0.35 * sm[..., None])
        if lt >= T_DROP:
            rr = 1.3 * (1 + 0.15 * (1 - (lt - T_DROP) / FALL)); dd = np.hypot(X - Cc[0], Y - Cc[1])
            edge = np.exp(-((dd - rr) / 0.25) ** 2); core = np.clip((rr - dd) / 0.4, 0, 1)
            img = img * (1 - 0.25 * edge[..., None]) + 0.12 * core[..., None] * np.exp(-((X - Cc[0] + 0.4) ** 2 + (Y - Cc[1] + 0.4) ** 2) / 0.3)[..., None]
    if r > 0:
        hl = np.exp(-(((X - Cc[0] + 0.35 * r) ** 2 + (Y - Cc[1] + 0.35 * r) ** 2) / (0.35 * r + 0.3) ** 2)) * w * inside
        img = img + (hl * 0.35)[..., None]
    out = morning_light(img)
    _after['last_tear'] = out
    return out

def title(lt):
    """눈물로 찍힌 눈에서 천천히 물러나 그림 전체(밤사이의 흔적 + 눈)를 보여 주고, 제목과 허상공방 낙관."""
    rgb, fib, dens, pv, X, Y = after_plate('trace', TP)
    if 'final_img' not in _after:
        Cc = np.array(dragon.E) + np.array((1.0, 0.0))
        R = np.hypot(X - Cc[0], Y - Cc[1]).astype(F32)
        ring = np.exp(-((R - 4.4) / 0.35) ** 2) * 1.3 + np.clip(R / 4.4, 0, 1) ** 7 * (R < 4.4) * 0.5
        _after['final_img'] = (rgb * np.exp(-(dens + ring)[..., None] * INK_ABS)).astype(F32)
    pap = _after['final_img']
    u = ease(ramp(lt, 0.4, 4.0))
    cx, cy, wmm = dragon.E[0] + 2 + (330 - dragon.E[0] - 2) * u, dragon.E[1] + 1 + (212 - dragon.E[1] - 1) * u, 150 * (1 - u) + 690 * u
    sc = TP.ppm * wmm / W
    M = np.array([[sc, 0, (cx - TP.cx) * TP.ppm + TP.W / 2 - sc * W / 2], [0, sc, (cy - TP.cy) * TP.ppm + TP.H / 2 - sc * H / 2]], F32)
    img = cv2.warpAffine(pap, M, (W, H), flags=cv2.WARP_INVERSE_MAP | cv2.INTER_AREA, borderValue=(0.12, 0.08, 0.055))
    img = morning_light(img)
    base = _after.get('last_tear')
    if base is not None and lt < 1.0:                                       # 눈물 장면에서 이어지게 겹쳐 넘김
        k = ease(ramp(lt, 0.0, 1.0)); img = base * (1 - k) + img * k
    tm = A2.A.text_mask('점', int(120 * S))
    a = ease(ramp(lt, 4.2, 5.0))
    img = img * np.exp(-(tm * 2.4 * a)[..., None] * INK_ABS)
    if lt > 5.6:
        rgba = A2.A.seal_rgba(); sz = int(62 * S)
        sm = cv2.resize(rgba, (sz, sz), interpolation=cv2.INTER_AREA)
        al = sm[..., 3:4] * ease(ramp(lt, 5.6, 5.9)); y0, x0 = int(H * 0.10 + 150 * S), int(W * 0.66 + 10 * S)
        sub = img[y0:y0 + sz, x0:x0 + sz]; img[y0:y0 + sz, x0:x0 + sz] = sub * (1 - al) + sub * sm[..., :3] * 1.15 * al
    return img * (1 - ease(ramp(lt, 8.6, 10.0)))

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
    elif kind == 'trace': f8 = fin(trace(lt), t)
    elif kind == 'tear': f8 = fin(tear(lt), t)
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
