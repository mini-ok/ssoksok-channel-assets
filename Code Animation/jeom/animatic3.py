"""〈점〉 애니마틱 v3. 클라이맥스를 다시 짠 판(깨어남 → 몸부림 → 벗어남 → 창가에서 돌아봄 → 창을 넘음 →
폭풍 속 씻김 → 포효 → 하늘 접수 → 승천과 해돋이). 비는 붓으로 그린 비(engine/rain.py)로 바꿨다.
사용: python3 animatic3.py cut C13 C15 ... / all / still t... / encode
v2(animatic2.py)의 장면 함수(화실·여정·남은 그림·제목)를 가져다 쓴다.
"""
import sys, os, math, subprocess, glob, copy
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, 'engine')); sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, 'tests'))
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
W, H, FPS = 960, 540, 12
C = os.path.join(HERE, 'cache')
OUT = os.path.join(C, 'anim3'); os.makedirs(OUT, exist_ok=True)
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
    ('C25', 'title', 181.5, 5.5),
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
            self.items.append((t, self.r.uniform(0, W), self.r.uniform(0, H), self.r.uniform(4, 13)))
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
        hb = cv2.GaussianBlur(live, (0, 0), 1.0 + 6.0 * halo)
        live = live + np.clip(hb - live, 0, None) * 0.9 * halo
    return img * np.exp(-(live * k)[..., None] * INK_ABS)

# ---------------------------------------------------------------- C6 창틀 근접
_rain_sill = None; _sill_r = np.random.default_rng(31); _splash = []
def sill(lt):
    global _rain_sill
    if _rain_sill is None: _rain_sill = InkRain(W, int(H * 0.62), angle=-16, seed=41, fib=TF.FIB[:int(H * 0.62)])
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
    grain = np.sin(xx / 6.0 + 2.5 * np.sin(yy / 31.0 + xx / 140.0))
    top0, top1, front1 = hs, hs + 46, hs + 112
    topm = (yy >= top0) & (yy < top1)
    frontm = (yy >= top1) & (yy < front1)
    tw = np.array((0.30, 0.20, 0.12), F32) * (0.85 + 0.12 * grain[..., None])
    img[topm] = tw[topm]
    img[frontm] = (tw * 0.55)[frontm]
    wetsheen = np.exp(-((yy - top0 - 8) / 6.0) ** 2) * (0.6 + 0.4 * np.sin(xx / 37.0) ** 2)
    img = img + (wetsheen * topm * 0.20)[..., None] * np.array((0.75, 0.8, 0.9), F32)
    for x0 in (0, W - 70):
        post = (xx >= x0) & (xx < x0 + 70) & (yy < front1)
        img[post] = (np.array((0.20, 0.13, 0.08), F32) * (0.85 + 0.12 * grain[..., None]))[post]
    room = yy >= front1
    img[room] = np.array((0.045, 0.036, 0.03), F32)
    # 서안 위 종이 귀퉁이(창빛에 희미하게)
    pap = (yy >= H - 66) & (xx > 180 + (yy - (H - 66)) * 0.8)
    pcol = TF.PAPER * np.array((0.42, 0.44, 0.50), F32)
    img[pap] = pcol[pap]
    # 빗방울: 문지방에 부딪혀 왕관처럼 튀고, 물방울이 방 안(화면 아래·앞)으로, 앞모서리에서 물이 떨어진다
    q = math.floor(lt * FPS) / FPS
    if lt > 0.4:
        for _ in range(int(_sill_r.integers(1, 4) * min(1, lt / 1.2) + 1)):
            _splash.append((q, _sill_r.uniform(90, W - 90), _sill_r.uniform(top0 + 4, top1 - 6), _sill_r.uniform(-1, 1), _sill_r.uniform(0.7, 1.4)))
    sp = np.zeros((H, W), F32); drops = np.zeros((H, W), F32)
    for (t0, x, y, side, sz) in _splash:
        u = q - t0
        if u < 0 or u > 1.2: continue
        dep = 0.6 + 0.8 * (y - top0) / (top1 - top0)                         # 가까울수록 크게
        if u < 0.25:
            rs_ = np.random.default_rng(int(x * 7 + t0 * 100))
            for k in range(int(rs_.integers(4, 8))):
                a_ = -math.pi / 2 + rs_.uniform(-1.25, 1.25) + side * 0.15
                L1 = (8 + 46 * (u / 0.25) ** 0.6) * sz * dep * rs_.uniform(0.35, 1.0)
                p0 = (x + math.cos(a_) * 4, y + math.sin(a_) * 2); p1 = (x + math.cos(a_) * L1, y + math.sin(a_) * L1 * 0.9)
                cv2.line(sp, (int(p0[0]), int(p0[1])), (int(p1[0]), int(p1[1])), 1.0 - u * 2, max(1, int(2.5 * dep)), cv2.LINE_AA)
                cv2.circle(sp, (int(p1[0]), int(p1[1])), max(1, int(2.2 * dep)), 1.0 - u * 2, -1, cv2.LINE_AA)
        for k in range(3):                                                  # 방 안으로 튀는 물방울: 앞으로 올수록 커진다
            vx = (k - 1) * 70 * sz + side * 40; vy = -120 + k * 35
            px = x + vx * u; py = y + vy * u + 560 * u * u
            r = (2 + 6 * u) * dep
            if py < H: cv2.ellipse(drops, (int(px), int(py)), (max(1, int(r * 0.7)), max(1, int(r * 1.2))), 0, 0, 360, 1.0, -1, cv2.LINE_AA)
    for j in range(14):                                                     # 앞모서리에서 떨어지는 물
        x = 110 + j * 57 + 9 * math.sin(j * 3.1)
        ph = (q * 1.6 + j * 0.37) % 1.0
        py = front1 + ph * ph * 160
        cv2.ellipse(drops, (int(x), int(py)), (2, 3 + int(5 * ph)), 0, 0, 360, 0.8, -1, cv2.LINE_AA)
    sp = cv2.GaussianBlur(sp, (0, 0), 0.6)
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
        _smear = np.maximum(_smear * 0.995, cv2.GaussianBlur(_prev_live, (0, 0), 3.0) * 0.22)
    _prev_live = live.copy()
    pap = paper_view(L.CLOUD + L.BODY_ON_PAPER * 0.25 * ramp(lt, 0.8, 1.2), cam)
    _bl_str.add(lt, int(_bl_str.r.integers(1, 4)))
    wet, rim = _bl_str.render(lt)
    img = rain_on_paper(pap * np.exp(-_smear[..., None] * INK_ABS), wet, rim)
    # 들린 부분은 그림자를 드리운다
    hgt = (l1 + l2) / 3.6
    if hgt > 0.02:
        sh = cv2.GaussianBlur(np.clip(live, 0, 1.5), (0, 0), 3 + 10 * hgt)
        sh = np.roll(np.roll(sh, int(14 * hgt), 1), int(20 * hgt), 0)
        img = img * (1 - 0.3 * np.clip(sh, 0, 1) * hgt)[..., None]
    img = ink_over(img, live, halo=0.35 * wetness)
    fx = 0.9 * math.exp(-(lt - 11.6) / 0.15) if lt >= 11.6 else 0
    img = light(img, 'night', extra=fx)
    g = 0.15 if 8.4 < lt < 11.6 else (0.55 + 0.6 * ramp(lt, 11.6, 12.0))
    return glint(img, e, kk, g)

# ---------------------------------------------------------------- C18 창가에서 돌아봄 / C19 창을 넘음
_dragon_sprite = {}
def dragon_sprite(t, mir=1.0, bob=0.0, scale_px=0.33, curl=0.4):
    """그림 자세 그대로의 용을 화면 공간에 그려 RGBA처럼 쓰는 판(먹 밀도). 머리는 왼쪽(화가 쪽)을 본다."""
    L.CAM['pos'] = np.zeros(3); L.CAM['tilt'] = 0.0
    pts, cum = L.trail(0.0)
    off = np.array((0.0, bob, 0.0))
    sts, _ = live3(pts + off, cum, t=t, breathe=math.sin(t * 2.6), curl=curl, wh=1.2)
    d = render_strokes(L.SV, sts, L.SFIB)
    d, e, kk = pupil(d, pts + off, cum)
    return d, e, kk

def place(room_img, d, e, kk, cx, cy, s, clip=None, k_load=1.0):
    """화면 크기의 용 밀도 d를 방 화면에 s배로 줄여 (cx, cy)를 중심으로 놓는다."""
    M = np.array([[s, 0, cx - s * W / 2], [0, s, cy - s * H / 2]], F32)
    dd = cv2.warpAffine(d, M, (W, H))
    if clip is not None: dd = dd * clip
    img = room_img * np.exp(-(dd * k_load)[..., None] * INK_ABS * 1.4)
    e2 = (e[0] * s + cx - s * W / 2, e[1] * s + cy - s * H / 2)
    return img, e2, kk * s

def lookback(lt):
    R = A2.room()
    pose = dict(POSES['sleep'])
    base = R.render(lt + 200, pose, lamp_on=0.0, rain=1.0, flash=0.0)
    # 용: 창 앞(서안 위)에 떠서, 처음엔 창 쪽을 보다가(오른쪽) 몸을 돌려 화가를 본다(왼쪽)
    turn = ease(ramp(lt, 1.0, 2.4)); turn = step(turn, 4)
    mir = 1.0 - 2.0 * (1 - turn)                                           # −1(창을 봄) → +1(화가를 봄)
    mir = math.copysign(max(0.15, abs(mir)), mir)
    d, e, kk = dragon_sprite(lt, mir=mir, bob=0.08 * math.sin(lt * 1.8))
    img, e2, k2 = place(base, d, e, kk, W * 0.70, H * 0.31, 0.30)
    # 화가를 보는 동안(2.4~5.0) 눈빛이 조금 오래 머문다
    img = glint(img, e2, k2, 0.5 if 2.4 < lt < 5.2 else 0.3)
    return img

def exitw(lt):
    R = A2.room()
    base = R.render(lt + 210, dict(POSES['sleep']), lamp_on=0.0, rain=1.0, flash=0.7 * math.exp(-(lt - 2.2) / 0.12) if lt >= 2.2 else 0)
    u = ease(ramp(lt, 0.3, 3.2))
    d, e, kk = dragon_sprite(lt, mir=-1.0, bob=0.0)
    cx = W * (0.70 + 0.04 * u); cy = H * (0.31 - 0.06 * u); s = 0.30 * (1 - 0.75 * u)
    yy, xx = np.mgrid[0:H, 0:W].astype(F32)
    win = ((xx > W * 0.565) & (xx < W * 0.835) & (yy > H * 0.145) & (yy < H * 0.495)).astype(F32)
    clip = np.clip(win + (1 - ramp(lt, 1.2, 1.8)), 0, 1)                    # 창을 넘으면 창틀 밖(하늘)만 보인다
    img, e2, k2 = place(base, d, e, kk, cx, cy, s, clip=clip)
    return img

# ---------------------------------------------------------------- C20 폭풍 / C21 승천·해돋이
_storm = {}
def storm_init():
    if _storm: return
    _storm['rain'] = InkRain(W, H, angle=-12, seed=7, fib=TF.FIB)
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
    rot = swirl * np.exp(-RR / 230.0)
    rs = RR * (1 + 1.2 * take * np.exp(-RR / 420.0))
    if part > 0:                                                           # 구름이 갈라진다: 가운데가 바깥 구름으로 밀려남
        rs = rs * (1 - 0.6 * part * np.exp(-RR / 260.0))
    if roar_r is not None:                                                 # 충격파: 고리 바깥으로 구름이 밀린다
        rs = rs - 40 * np.exp(-((RR - roar_r) / 40.0) ** 2)
    sx = center[0] + rs * np.cos(TH + rot) + 30 * t; sy = center[1] + rs * np.sin(TH + rot) + 10 * t
    a = cv2.remap(TF.CL1, (sx + 200).astype(F32), (sy + 100).astype(F32), cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
    b = cv2.remap(TF.CL2, (sx * 0.8 + 200).astype(F32), (sy * 0.8 + 100).astype(F32), cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
    base = 0.10 + 0.12 * (yyS / H)
    far = TF.wash(b + 0.35, 0.40) * 0.55
    near = TF.wash(a + 0.25 * b + 0.30, 0.55) * 0.95
    d = base + (far + near) * (0.75 + 0.5 * np.clip(TF.FIB * 1.3, 0, 1.3)) * (1 - 0.75 * take) * (1 - 0.9 * clear)
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
            fl.splat(S2[j][0], S2[j][1] + 10, (0.02 + 0.22 * wash) * vis, v[0] * 0.4, v[1] * 0.4 + 140 * wash, 18)
    _storm['prev'] = S2[-1].copy()
    center = (W * 0.5, H * 0.44)
    if take > 0:
        DX, DY = xxS - center[0], yyS - center[1]; RR = np.hypot(DX, DY) + 1e-3
        wv = 70 * take * (1 - ramp(T, 21, 24))
        fl.u += cv2.resize((-DY / RR) * wv * np.exp(-RR / 300), (TF.GW, TF.GH)) / TF.GS * 0.02
        fl.v += cv2.resize((DX / RR) * wv * np.exp(-RR / 300), (TF.GW, TF.GH)) / TF.GS * 0.02
    for _ in range(2): fl.step(1 / (FPS * 2))
    smoke = 0.9 * np.tanh(np.clip(cv2.resize(fl.d, (W, H), interpolation=cv2.INTER_CUBIC), 0, None) * 1.2)
    clear = 0.2 * ease(ramp(T, 22.5, 26.5)) if ascend else 0.0
    swirl = 2.6 * take
    roar_r = (80 + 900 * roar) if 8.6 <= T < 11.5 else None
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
        push = 30 * np.exp(-((RR - roar_r) / 60.0) ** 2)
        fdx = fdx + push * DX / RR; fdy = fdy + push * DY / RR
    rn = _storm['rain'].render(T + 100, amount=rain_amt, gust=0.8, flow=(fdx, fdy))
    fx = 0.0
    for tf, a in ((1.2, 0.8), (5.0, 0.6), (8.7, 1.0), (8.85, 0.6), (14.0, 0.7)):
        if T >= tf: fx = max(fx, a * math.exp(-(T - tf) / 0.12))
    dens = cl * (1 - 0.6 * fx) + smoke + rn * 0.55
    img = TF.PAPER * np.exp(-dens[..., None] * INK_ABS)
    img = img * (1 + 0.35 * fx)
    img = light(img, 'night', extra=fx) * 0.45 + light(img, 'silver', extra=fx) * 0.75
    if ascend:                                                              # 해돋이: 영화의 첫 색(붉은 해 + 금빛 구름 테)
        sun = ease(ramp(T, 23.0, 27.5))
        sc = (center[0], center[1] - 20 + 50 * (1 - sun))
        ang = np.arctan2(yyS - sc[1], xxS - sc[0])
        r = np.hypot(xxS - sc[0], yyS - sc[1]) * (1 + 0.012 * np.sin(ang * 5 + 1) + 0.008 * np.sin(ang * 11))
        disk = np.clip((64 - r) / 1.8, 0, 1) * sun
        glow = np.exp(-(r / 300) ** 2) * sun
        gold = np.array((1.0, 0.80, 0.50), F32); red = np.array((0.78, 0.20, 0.11), F32)
        img = img * (1 - 0.25 * glow[..., None]) + glow[..., None] * gold * 0.5
        rimc = np.clip(np.abs(cv2.Laplacian(cl.astype(F32), cv2.CV_32F, ksize=5)) * 0.08, 0, 1) * glow
        img = img + rimc[..., None] * gold * 0.7
        veil = np.clip(cl - 0.25, 0, 1)                                     # 해 앞을 지나는 엷은 구름 가닥
        paper = TF.PAPER * (0.88 + 0.12 * TF.FIB[..., None])
        shade = (0.92 + 0.12 * np.clip(1 - r / 64, 0, 1))[..., None]
        dcol = red * paper * 1.15 * shade * np.exp(-veil[..., None] * 1.2)
        img = img * (1 - disk[..., None]) + dcol * disk[..., None]
    a_ = np.clip(live * 1.5, 0, 1)[..., None]
    lit = light(TF.PAPER * np.exp(-live[..., None] * INK_ABS), 'silver', extra=fx) * 1.1
    img = img * (1 - a_) + lit * a_
    img = glint(img, e, kk, 0.6 + 0.6 * roar * (1 - roar))
    return img

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
    elif kind == 'hand_A': f8 = A2.borrowed(os.path.join(C, 'hand_test2', 'h*.png'), kk)
    elif kind == 'hand_B': f8 = A2.borrowed(os.path.join(C, 'hand_test2', 'h*.png'), 65 + kk)
    elif kind == 'knife': f8 = A2.borrowed(os.path.join(C, 'knife_test', 'k*.png'), kk)
    elif kind == 'sill': f8 = fin(sill(lt), t)
    elif kind == 'journey':
        img = A2.A.frame(A2.J_OLD[0] + lt * (A2.J_OLD[1] - A2.J_OLD[0]) / 44.0)
        f8 = to8(img); name = A2.J_NAMES.get(A2.TL.cut_at(math.floor((A2.J_OLD[0] + lt * 66 / 44) * 12) / 12)[0], 'J')
        name = {'C6': 'C7', 'C7': 'C8', 'C8': 'C9', 'C9': 'C10', 'C10': 'C11', 'C11': 'C12', 'C12': 'C13'}.get(name, name)
    elif kind == 'life': f8 = fin(life(lt), t)
    elif kind == 'struggle': f8 = fin(struggle(lt), t)
    elif kind == 'leap': f8 = A2.borrowed(os.path.join(C, 'leap', 'f*.png'), 12 + kk)
    elif kind == 'lookback': f8 = fin(lookback(lt), t)
    elif kind == 'exit': f8 = fin(exitw(lt), t)
    elif kind == 'storm': f8 = fin(storm(lt), t, vig=0.26)
    elif kind == 'ascend': f8 = fin(ascend(lt), t, vig=0.24)
    elif kind == 'trace': f8 = fin(A2.trace(lt * 10 / 9), t)
    elif kind == 'tear': f8 = A2.borrowed(os.path.join(C, 'tear', 'f', 't*.png'), kk)
    elif kind == 'title': f8 = fin(A2.title(lt * 7 / 5.5), t, vig=0.15)
    return A2.lab(f8, name, t)

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
