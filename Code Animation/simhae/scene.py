"""〈얼마나 깊을까〉 — 바다 깊이를 겹 종이로 내려가는 세로 숏폼 모션그래픽(약 54초, 1080×1920).
겹(layer)마다 시차(p)·물빛 섞임·초점 흐림·그림자 거리가 달라 입체가 생긴다. frame(t)은 t의 순수 함수.
"""
# 주의(2026-11-21): 이 파일의 글자 크기는 옛 기준(한글 크게, 영어 작게)이다. 새 쇼츠로 복사할 때는
# 영어를 위·한글을 아래에 두고 크기를 비슷하게(영어 = 한글 + 4px) 다시 잡는다 → _channel/shorts_playbook.md B-2a.
import os, sys, math
import numpy as np, cv2, cairo

HERE = os.path.dirname(os.path.abspath(__file__))
os.environ.setdefault('HD_ORIENT', 'v')
sys.path.insert(0, os.path.join(HERE, '..', 'haedal'))
sys.path.insert(0, os.path.join(HERE, '..', 'jamo28'))
os.environ.setdefault('MG_SCALE', os.environ.get('HD_SCALE', '1'))
from mg import clamp, ramp, smooth, expo_out, expo_in_out, back_out, spring, lerp   # noqa: E402
from paper import W, H, SC, Level, composite, grain, hexc, tex                     # noqa: E402
import shapes as S                                                                   # noqa: E402

FPS = 30
SERIF = 'Noto Serif CJK KR'
DW, DH = 1080, 1920
CREAM = hexc('#EFE6D2'); INK = hexc('#1C1A18'); WHITE = hexc('#F6F1E6')

# ---------------------------------------------------------------- 깊이(m) ↔ 세계 y(px): 층마다 같은 화면 길이
ZB = [0, 200, 1000, 4000, 6000, 10935]                  # 층 경계(m)
ZY = [0, 2000, 4000, 6000, 7500, 9600]                  # 세계 y
ZONES = [('햇빛층', 'SUNLIT', '0 – 200 m'), ('어스름층', 'TWILIGHT', '200 – 1,000 m'), ('한밤층', 'MIDNIGHT', '1,000 – 4,000 m'),
         ('심연층', 'ABYSS', '4,000 – 6,000 m'), ('해구', 'HADAL', '6,000 m 아래')]
ZONES_FT = ['0 – 656 ft', '656 – 3,281 ft', '3,281 – 13,123 ft', '13,123 – 19,685 ft', 'below 19,685 ft']
def d2y(d): return float(np.interp(d, ZB, ZY))
def y2d(y): return float(np.interp(y, ZY, ZB)) if y >= 0 else 0.0

# 물빛(깊이별)
WD = [0, 60, 200, 500, 1000, 2500, 4000, 6000, 10935]
WC = [hexc(h) for h in ['#7FD6D0', '#3DB0BE', '#1C82A6', '#155985', '#0F3566', '#0A1D42', '#071029', '#050A1B', '#03060F']]
def water(d):
    return tuple(float(np.interp(d, WD, [c[i] for c in WC])) for i in range(3))

# ---------------------------------------------------------------- 시간표·카메라(세계 y = 화면 가운데)
T_DIVE = 3.6
CK = [(0.0, -700), (2.6, -650), (T_DIVE, -80), (4.6, 300), (12.0, d2y(200)), (20.0, d2y(1000)), (28.0, d2y(4000)),
      (34.0, d2y(6000)), (41.6, d2y(10935) - 420), (43.6, d2y(10935) - 330)]
T_FLOOR = 41.6
T_PAY = 43.6                                      # 줌아웃 → 정답
T_END = 52.0
DUR = 55.0
def cam_y(t):
    ts = [k[0] for k in CK]; ys = [k[1] for k in CK]
    if t <= ts[0]: return ys[0]
    if t >= ts[-1]: return ys[-1]
    i = max(j for j in range(len(ts)) if ts[j] <= t)
    u = (t - ts[i]) / (ts[i + 1] - ts[i])
    # 이웃 구간 기울기로 이어지는 3차(멈추지 않고 흐름)
    def slope(j):
        if j <= 0 or j >= len(ts) - 1: return 0.0
        return (ys[j + 1] - ys[j - 1]) / (ts[j + 1] - ts[j - 1])
    h = ts[i + 1] - ts[i]; m0, m1 = slope(i) * h, slope(i + 1) * h
    h00 = 2 * u ** 3 - 3 * u ** 2 + 1; h10 = u ** 3 - 2 * u ** 2 + u; h01 = -2 * u ** 3 + 3 * u ** 2; h11 = u ** 3 - u ** 2
    return h00 * ys[i] + h10 * m0 + h01 * ys[i + 1] + h11 * m1
def cam_x(t): return 26 * math.sin(t * 0.37) + 14 * math.sin(t * 0.83 + 1)   # 옆으로 살짝 흔들림 → 가로 시차도

def depth_now(t): return y2d(cam_y(t))
def zone_of(d):
    for i in range(5):
        if d < ZB[i + 1]: return i
    return 4


# ---------------------------------------------------------------- 겹(뒤 → 앞): 시차 p, 물빛 섞임, 초점 흐림, 그림자 거리
LAYERS = [  # name, p, tint, blur, depth, shadow
    ('far', 0.55, 0.62, 2.6, 0.5, 0.18),
    ('mid', 0.80, 0.32, 1.0, 0.9, 0.26),
    ('main', 1.00, 0.10, 0.0, 1.5, 0.32),
    ('near', 1.35, 0.00, 2.2, 2.6, 0.30)]
P = {n: p for n, p, *_ in LAYERS}

def sy(wy, t, p):  # 세계 y → 화면 y
    return DH / 2 + (wy - cam_y(t)) * p
def sx(x, t, p): return x + cam_x(t) * (p - 1.0) * 1.0


# ---------------------------------------------------------------- 생물·지형(단위 크기 s, 오른쪽을 봄)
def fish(cr, x, y, s, col, wag=0.0, flip=1, eye=None):
    cr.save(); cr.translate(x, y); cr.scale(flip, 1)
    S.ellipse(cr, 0, 0, s, s * 0.42)
    w = 0.35 * math.sin(wag)
    S.poly(cr, [(-s * 0.8, 0), (-s * 1.55, -s * (0.45 - w * 0.4)), (-s * 1.45, s * w * 0.3), (-s * 1.55, s * (0.45 + w * 0.4))])
    S.fill(cr, col)
    if eye is not None:
        S.circle(cr, s * 0.55, -s * 0.08, s * 0.1); S.fill(cr, eye)
    cr.restore()

def turtle(cr, x, y, s, col, col2, t):
    cr.save(); cr.translate(x, y)
    f = math.sin(t * 2.4)
    for sgn, (fx, fy, a) in [(1, (0.45, -0.35, -0.6)), (1, (0.45, 0.35, 0.6)), (-1, (-0.5, -0.3, -2.4)), (-1, (-0.5, 0.3, 2.4))]:
        S.leaf(cr, fx * s, fy * s, (0.9 if sgn > 0 else 0.5) * s, 0.2 * s, a + (0.5 * f if sgn > 0 else 0.25 * f) * (1 if fy < 0 else -1))
    S.circle(cr, 0.95 * s, 0, 0.22 * s); S.fill(cr, col2)
    S.ellipse(cr, 0, 0, 0.75 * s, 0.55 * s); S.fill(cr, col)
    for hx, hy in [(0, 0), (-0.32, -0.2), (-0.32, 0.2), (0.3, -0.2), (0.3, 0.2)]:
        S.ellipse(cr, hx * s, hy * s, 0.16 * s, 0.12 * s)
    S.fill(cr, col2); cr.restore()

def jelly(cr, x, y, s, col, t, a=0.82):
    cr.save(); cr.translate(x, y)
    pulse = 1 + 0.12 * math.sin(t * 3.0)
    cr.save(); cr.scale(pulse, 1 / pulse)
    cr.new_sub_path(); cr.arc(0, 0, s, math.pi, 2 * math.pi)
    n = 7
    for k in range(n + 1):
        px = s - 2 * s * k / n; cr.line_to(px, s * 0.12 * (1 + (k % 2)))
    cr.close_path(); S.fill(cr, col, a); cr.restore()
    for k in range(6):
        x0 = -0.7 * s + 0.28 * s * k
        for j in range(10):
            yy = s * 0.2 + j * s * 0.22; xx = x0 + 0.12 * s * math.sin(t * 2 + j * 0.6 + k)
            S.circle(cr, xx, yy, s * 0.035)
    S.fill(cr, col, a * 0.8); cr.restore()

def whale(cr, x, y, s, col, t):
    cr.save(); cr.translate(x, y); cr.rotate(0.12)
    f = math.sin(t * 1.1) * 0.25
    cr.new_sub_path(); cr.move_to(1.0 * s, -0.28 * s)
    cr.curve_to(1.08 * s, 0.05 * s, 1.0 * s, 0.26 * s, 0.7 * s, 0.28 * s)
    cr.curve_to(0.1 * s, 0.32 * s, -0.5 * s, 0.2 * s, -0.95 * s, 0.04 * s)
    cr.line_to(-1.3 * s, (0.25 + f) * s); cr.line_to(-1.22 * s, (0.0 + f * 0.3) * s); cr.line_to(-1.32 * s, (-0.22 + f) * s)
    cr.line_to(-0.95 * s, -0.04 * s)
    cr.curve_to(-0.5 * s, -0.16 * s, 0.1 * s, -0.33 * s, 0.6 * s, -0.33 * s)
    cr.curve_to(0.85 * s, -0.33 * s, 0.98 * s, -0.32 * s, 1.0 * s, -0.28 * s)
    cr.close_path()
    S.leaf(cr, 0.35 * s, 0.22 * s, 0.35 * s, 0.07 * s, 1.1 + f)
    S.fill(cr, col); cr.restore()

def squid(cr, x, y, s, col, t):
    cr.save(); cr.translate(x, y); cr.rotate(-0.3)
    S.leaf(cr, -0.1 * s, 0, 1.1 * s, 0.25 * s, 0)
    for sgn in (-1, 1): S.leaf(cr, 0.75 * s, 0, 0.35 * s, 0.14 * s, sgn * 2.2)
    for k in range(8):
        a = math.pi + (k - 3.5) * 0.09 + 0.08 * math.sin(t * 3 + k)
        L = 0.9 * s if k in (3, 4) else 0.55 * s
        S.bar(cr, -0.1 * s, 0, -0.1 * s + math.cos(a) * L, math.sin(a) * L, 0.045 * s)
    S.fill(cr, col); cr.restore()

def angler(cr, x, y, s, col, tooth, t):
    cr.save(); cr.translate(x, y)
    S.circle(cr, 0, 0, s * 0.62); S.ellipse(cr, -0.55 * s, 0.05 * s, 0.5 * s, 0.3 * s)
    S.poly(cr, [(-0.9 * s, 0), (-1.35 * s, -0.35 * s), (-1.3 * s, 0.4 * s)])
    S.fill(cr, col)
    # 입(오려 낸 틈) + 이빨
    cr.new_sub_path(); cr.move_to(0.62 * s, 0.05 * s); cr.curve_to(0.3 * s, 0.35 * s, 0.0, 0.38 * s, -0.15 * s, 0.28 * s)
    cr.curve_to(0.1 * s, 0.22 * s, 0.4 * s, 0.12 * s, 0.62 * s, 0.05 * s); S.fill(cr, (0.02, 0.02, 0.04))
    for k in range(6):
        tx = 0.52 * s - k * 0.12 * s
        S.poly(cr, [(tx, 0.1 * s + k * 0.03 * s), (tx - 0.04 * s, 0.24 * s + k * 0.025 * s), (tx - 0.08 * s, 0.11 * s + k * 0.03 * s)])
    S.fill(cr, tooth)
    S.circle(cr, 0.28 * s, -0.22 * s, 0.07 * s); S.fill(cr, tooth)
    # 낚싯대
    sw = 0.15 * math.sin(t * 1.3)
    pts = [(0.1 * s + 0.6 * s * u, -0.55 * s - 0.55 * s * math.sin(u * 2.2) + sw * s * u) for u in np.linspace(0, 1, 12)]
    for a, b in zip(pts[:-1], pts[1:]): S.bar(cr, a[0], a[1], b[0], b[1], 0.035 * s)
    S.fill(cr, col); cr.restore()
    return x + pts[-1][0], y + pts[-1][1]          # 미끼 자리(빛)

def gulper(cr, x, y, s, col, t):
    cr.save(); cr.translate(x, y)
    S.poly(cr, [(0, 0), (0.9 * s, -0.35 * s), (0.95 * s, -0.25 * s), (0.25 * s, 0.05 * s), (0.95 * s, 0.32 * s), (0.85 * s, 0.4 * s)])
    S.fill(cr, col)
    pts = [(-u * 2.6 * s, 0.18 * s * math.sin(u * 7 - t * 3) * u) for u in np.linspace(0, 1, 30)]
    for k, (a, b) in enumerate(zip(pts[:-1], pts[1:])): S.bar(cr, a[0], a[1], b[0], b[1], 0.1 * s * (1 - k / 32))
    S.fill(cr, col); cr.restore()
    return x + pts[-1][0], y + pts[-1][1]

def dumbo(cr, x, y, s, col, col2, t):
    cr.save(); cr.translate(x, y + 0.08 * s * math.sin(t * 1.6))
    f = math.sin(t * 3.2)
    for sgn in (-1, 1): S.ellipse(cr, sgn * 0.62 * s, -0.25 * s, 0.32 * s, 0.17 * s, sgn * (0.5 + 0.4 * f))
    S.fill(cr, col2)
    S.ellipse(cr, 0, -0.1 * s, 0.55 * s, 0.6 * s)
    cr.new_sub_path(); cr.move_to(-0.6 * s, 0.25 * s)
    for k in range(9):
        cr.line_to(-0.6 * s + k * 0.15 * s, (0.62 + 0.12 * (k % 2) + 0.05 * math.sin(t * 2 + k)) * s)
    cr.line_to(0.6 * s, 0.25 * s); cr.close_path(); S.fill(cr, col)
    for sgn in (-1, 1): S.circle(cr, sgn * 0.2 * s, -0.12 * s, 0.07 * s)
    S.fill(cr, (0.06, 0.05, 0.08)); cr.restore()

def snailfish(cr, x, y, s, col, t):
    cr.save(); cr.translate(x, y)
    S.ellipse(cr, 0.1 * s, 0, 0.55 * s, 0.38 * s)
    pts = [(-u * 1.3 * s, 0.1 * s * math.sin(u * 5 - t * 4)) for u in np.linspace(0, 1, 16)]
    for k, (a, b) in enumerate(zip(pts[:-1], pts[1:])): S.bar(cr, a[0], a[1], b[0], b[1], 0.42 * s * (1 - k / 17))
    S.fill(cr, col, 0.9)
    S.circle(cr, 0.4 * s, -0.08 * s, 0.07 * s); S.fill(cr, (0.1, 0.08, 0.12))
    cr.restore()

def amphipod(cr, x, y, s, col, t):
    cr.save(); cr.translate(x, y); cr.rotate(0.3 * math.sin(t * 2 + x))
    for k in range(6):
        a = -0.9 + k * 0.36
        S.ellipse(cr, math.cos(a) * 0.5 * s, math.sin(a) * 0.5 * s * 0.6, 0.2 * s, 0.14 * s, a + math.pi / 2)
    S.fill(cr, col); cr.restore()

def cliff(cr, side, y0, y1, xin, rough, seed, col):
    """해구 벽: side −1 왼쪽 / +1 오른쪽. xin(y)는 벽이 안쪽으로 나온 정도(화면 x)."""
    rng = np.random.default_rng(seed)
    ys = np.linspace(y0, y1, 60); jit = rng.uniform(-1, 1, 60) * rough
    edge = [xin(y) + j for y, j in zip(ys, jit)]
    cr.new_sub_path()
    if side < 0:
        cr.move_to(-400, y0)
        for y, x in zip(ys, edge): cr.line_to(x, y)
        cr.line_to(-400, y1)
    else:
        cr.move_to(DW + 400, y0)
        for y, x in zip(ys, edge): cr.line_to(DW - x, y)
        cr.line_to(DW + 400, y1)
    cr.close_path(); S.fill(cr, col)


# ---------------------------------------------------------------- 장면
def seeded(k): return np.random.default_rng(1000 + k)

def draw_world(t, L, G, RAY):
    cy = cam_y(t)
    d = depth_now(t)

    # -- 수면 위 하늘(크림 한지)·물결 겹: 바다로 들어간다
    for li, (lname, col, amp, ph) in enumerate([('far', hexc('#9FDCD3'), 18, 0.0), ('mid', hexc('#5CC0C4'), 24, 1.3), ('main', hexc('#2E9DB4'), 30, 2.4), ('near', hexc('#1E7FA0'), 36, 3.1)]):
        p = P[lname]; y0 = sy(0 + li * 26, t, p)
        if y0 > DH + 200: continue
        cr = L[lname].cr
        # 물결 띠: 아래로 갈수록 물빛 속으로 사라진다(두꺼운 판이 깊은 곳까지 따라오지 않게)
        S.wave(cr, -200, DW + 200, y0, amp, 260 + 60 * li, 30, t * (0.9 + 0.2 * li) + ph, 60)
        cr.rectangle(-200, y0 + 10, DW + 400, 520)
        g = cairo.LinearGradient(0, y0, 0, y0 + 530); g.add_color_stop_rgba(0, *col, 1); g.add_color_stop_rgba(0.35, *col, 0.9); g.add_color_stop_rgba(1, *col, 0)
        cr.set_source(g); cr.set_fill_rule(cairo.FILL_RULE_WINDING); cr.fill()
    if cy < 400:   # 하늘 해
        sm = L['far'].cr; S.circle(sm, 790 + cam_x(t) * -0.45, sy(-1050, t, 0.55), 95); S.fill(sm, hexc('#E0442E'))

    # -- 햇빛 줄기(햇빛층에서만)
    ra = clamp(1 - d / 320, 0, 1) * clamp((cy + 200) / 400, 0, 1)
    if ra > 0:
        RAY.cr.save(); RAY.cr.rectangle(-100, sy(0, t, 1.0) + 30, DW + 200, 4000); RAY.cr.clip()
        for k in range(7):
            x = 80 + 150 * k + 40 * math.sin(t * 0.3 + k); w = 60 + 40 * math.sin(k * 1.7)
            sk = 0.18 + 0.05 * math.sin(t * 0.25 + k)
            S.poly(RAY.cr, [(x, -50), (x + w, -50), (x + w + sk * 2200, 2000), (x + sk * 2200 - w * 0.5, 2000)])
            S.fill(RAY.cr, hexc('#FFF6D8'), 0.10 * ra * (0.6 + 0.4 * math.sin(t * 0.7 + k * 1.3)))
        RAY.cr.restore()

    # -- 햇빛층 0–200 m
    if d < 420:
        # 먼 물고기 떼(그림자처럼)
        for k in range(26):
            r = seeded(k)
            wy = d2y(50 + r.uniform(0, 120)); x = (r.uniform(-200, 1300) + t * 40 * (0.6 + r.uniform(0, 0.4))) % 1500 - 200
            fish(L['far'].cr, sx(x, t, 0.55), sy(wy, t, 0.55), 16 + r.uniform(0, 10), hexc('#1F6E86'), t * 8 + k)
        # 소용돌이 물고기 떼
        cx, cyy = 540 + 120 * math.sin(t * 0.35), d2y(75)
        for k in range(46):
            r = seeded(100 + k)
            a = t * (0.55 + 0.1 * r.uniform()) + k * 0.43; rr = 120 + 150 * r.uniform()
            x = cx + rr * math.cos(a) * 1.3; y = cyy + rr * math.sin(a) * 0.55
            fl = -1 if math.sin(a) > 0 else 1
            fish(L['mid'].cr, sx(x, t, 0.8), sy(y, t, 0.8), 20 + 8 * r.uniform(), hexc('#F2C14E') if k % 5 == 0 else hexc('#E8F1EC'), t * 12 + k, fl, hexc('#1A4A5A'))
        # 바다거북
        tx = -260 + (t - 4.0) * 110
        turtle(L['main'].cr, sx(tx, t, 1.0), sy(d2y(130), t, 1.0), 120, hexc('#4E8F5C'), hexc('#2D5E3A'), t)
        # 해파리(가까이)
        jelly(L['near'].cr, sx(820 - (t - 5) * 18, t, 1.35), sy(d2y(165), t, 1.35), 95, hexc('#F3B8C8'), t)
        jelly(L['mid'].cr, sx(200 + (t - 5) * 10, t, 0.8), sy(d2y(185), t, 0.8), 55, hexc('#F7D2DD'), t + 1.3)

    # -- 어스름층 200–1000 m
    if 120 < d < 1500:
        whale(L['far'].cr, sx(1300 - (t - 10) * 75, t, 0.55), sy(d2y(640), t, 0.55), 420, hexc('#0E2C4C'), t)
        for k in range(9):
            r = seeded(200 + k)
            x = (r.uniform(0, 1100) - (t - 12) * (60 + 40 * r.uniform())) % 1400 - 150; y = d2y(380 + 160 * r.uniform())
            X, Y = sx(x, t, 1.0), sy(y, t, 1.0)
            fish(L['main'].cr, X, Y, 46, hexc('#24476B'), t * 10 + k, -1, hexc('#C9E7F2'))
            for j in range(5):
                S.circle(G.cr, X + (-0.6 + 0.3 * j) * 46, Y + 0.3 * 46, 4.5); S.fill(G.cr, hexc('#8FF0FF'), 0.9)
        squid(L['near'].cr, sx(860 - (t - 15) * 30, t, 1.35), sy(d2y(860), t, 1.35), 150, hexc('#B84A3E'), t)
        for k in range(5):     # 작은 해파리(빛)
            r = seeded(260 + k); X = sx(r.uniform(80, 1000), t, 0.8); Y = sy(d2y(500 + 400 * r.uniform()), t, 0.8)
            jelly(L['mid'].cr, X, Y, 26, hexc('#9FD8F0'), t + k, 0.6)
            S.circle(G.cr, X, Y - 8, 7); S.fill(G.cr, hexc('#7FE8FF'), 0.6)

    # -- 한밤층 1000–4000 m
    if 700 < d < 4600:
        lx, ly = angler(L['main'].cr, sx(560 - (t - 23) * 20, t, 1.0), sy(d2y(2050), t, 1.0), 210, hexc('#2A2233'), hexc('#E8E0D0'), t)
        S.circle(G.cr, lx, ly, 14); S.fill(G.cr, hexc('#C8FFF0'))
        S.circle(G.cr, lx, ly, 40); S.fill(G.cr, hexc('#7FFFE0'), 0.18)
        # 빗해파리: 빛 줄
        for k in range(2):
            X = sx(300 + 520 * k + 30 * math.sin(t + k), t, 0.8); Y = sy(d2y(1450 + 300 * k), t, 0.8)
            S.ellipse(L['mid'].cr, X, Y, 46, 70); S.fill(L['mid'].cr, hexc('#3A3F6A'), 0.55)
            for j in range(8):
                a = j * math.pi / 4
                hue = (t * 0.6 + j / 8) % 1.0
                col = [hexc('#FF6FB1'), hexc('#7FE8FF'), hexc('#B6FF7A'), hexc('#FFD36F')][int(hue * 4) % 4]
                for q in range(6):
                    S.circle(G.cr, X + 40 * math.sin(a) * math.sin(q / 5 * math.pi), Y - 60 + q * 24, 3.2)
                S.fill(G.cr, col, 0.8)
        gx, gy = gulper(L['main'].cr, sx(900 - (t - 25) * 30, t, 1.0), sy(d2y(3150), t, 1.0), 160, hexc('#1C1826'), t)
        S.circle(G.cr, gx, gy, 9); S.fill(G.cr, hexc('#FF7AA8'))

    # -- 심연층 4000–6000 m: 해구 가장자리가 시작
    if 3000 < d < 7000:
        dumbo(L['main'].cr, sx(380 + (t - 29) * 25, t, 1.0), sy(d2y(4700), t, 1.0), 150, hexc('#E7A27F'), hexc('#F1C3A6'), t)
        for k in range(6):
            r = seeded(400 + k)
            S.ellipse(L['far'].cr, sx(r.uniform(0, 1080), t, 0.55), sy(d2y(5200 + 600 * r.uniform()), t, 0.55), 40, 16); S.fill(L['far'].cr, hexc('#2A2F4A'))

    if 3600 < d < 6600:
        # 왕관해파리: 붉은 종 + 둘레에서 빙글 도는 경보 불빛
        X, Y = sx(700 + 30 * math.sin(t * 0.6), t, 0.8), sy(d2y(5250), t, 0.8)
        jelly(L['mid'].cr, X, Y, 70, hexc('#8E1F2C'), t, 0.92)
        for k in range(16):
            a_ = k * math.pi / 8
            on = max(0.0, math.cos(a_ - t * 4.0)) ** 6
            S.circle(G.cr, X + 74 * math.cos(a_), Y + 12 + 22 * math.sin(a_), 5); S.fill(G.cr, hexc('#7FB8FF'), 0.25 + 0.75 * on)
        # 먼 바위 턱과 해삼(먼 겹)
        for k, (bx, bd) in enumerate([(140, 5450), (930, 5650)]):
            BX, BY = sx(bx, t, 0.55), sy(d2y(bd), t, 0.55)
            S.ellipse(L['far'].cr, BX, BY, 210, 48); S.fill(L['far'].cr, hexc('#20263F'))
            for j in range(3):
                S.ellipse(L['far'].cr, BX - 60 + 55 * j, BY - 40, 26, 14, 0.2 * math.sin(t + j)); S.fill(L['far'].cr, hexc('#C98DA0'))
        # 아주 먼 불빛 무리
        for k in range(12):
            r = seeded(900 + k); tw = 0.5 + 0.5 * math.sin(t * 1.7 + k)
            S.circle(G.cr, sx(r.uniform(40, 1040), t, 0.5), sy(d2y(4300 + 1500 * r.uniform()), t, 0.5), 2.5); S.fill(G.cr, hexc('#9FD0FF'), 0.5 * tw)

    # -- 해구 벽(세 겹: 멀수록 안쪽·물빛)
    if d > 4300:
        for lname, inset, col, seed in [('far', 260, hexc('#1A2240'), 1), ('mid', 170, hexc('#121831'), 2), ('main', 95, hexc('#0B1024'), 3)]:
            p = P[lname]; y0 = sy(d2y(5800), t, p); y1 = sy(d2y(10935) + 600, t, p)
            def xin(y, inset=inset, y0=y0, y1=y1):
                u = clamp((y - y0) / max(1, y1 - y0), 0, 1)
                return inset * (0.3 + 0.9 * u) + 40 * math.sin(y * 0.006 + inset)
            for side in (-1, 1):
                cliff(L[lname].cr, side, y0, y1, xin, 28, seed * 10 + side, col)
        for k in range(10):
            r = seeded(500 + k)
            amphipod(L['mid'].cr, sx(r.uniform(260, 820), t, 0.8), sy(d2y(6600 + 1000 * r.uniform()), t, 0.8), 18, hexc('#E9D7C4'), t + k)
        snailfish(L['main'].cr, sx(480 + 40 * math.sin(t * 0.8), t, 1.0), sy(d2y(8336), t, 1.0), 120, hexc('#F2D2DA'), t)
        # 바닥
        fy = sy(d2y(10935), t, 1.0)
        if fy < DH + 100:
            S.wave(L['main'].cr, -100, DW + 100, fy, 14, 300, 30, 0.0, 40); L['main'].cr.rectangle(-100, fy + 10, DW + 200, 1500); S.fill(L['main'].cr, hexc('#2B2A33'))

    # -- 반짝이는 플랑크톤(어두운 층에서 깜빡이는 빛)
    if d > 700:
        for k in range(34):
            r = seeded(800 + k); p = r.uniform(0.6, 1.2)
            wy = cy + ((r.uniform(0, 2600) - cy * (1 - p) * 0.4) % 2600) - 1300
            tw = max(0.0, math.sin(t * r.uniform(1.0, 2.4) + k * 1.7)) ** 3
            if tw > 0.02:
                S.circle(G.cr, r.uniform(0, 1080), DH / 2 + (wy - cy) * p, 2.2 + 2.5 * r.uniform()); S.fill(G.cr, [hexc('#7FE8FF'), hexc('#B6FF7A'), hexc('#9FB6FF')][k % 3], 0.85 * tw)

    # -- 바다 눈(가까운 겹, 깊을수록 많이) + 거품(얕은 곳)
    n = int(18 + 40 * clamp(d / 3000, 0, 1))
    for k in range(n):
        r = seeded(700 + k)
        wy = cy + ((r.uniform(0, 2400) - cy * 0.35 - t * 30 * r.uniform(0.3, 1)) % 2400) - 1200
        x = r.uniform(0, 1080) + 20 * math.sin(t * 0.5 + k)
        if d < 300:
            S.circle(L['near'].cr, x, DH / 2 + (wy - cy), 3 + 6 * r.uniform()); S.fill(L['near'].cr, (0.9, 0.97, 1.0), 0.55)
        else:
            S.circle(L['near'].cr, x, DH / 2 + (wy - cy), 2 + 3 * r.uniform()); S.fill(L['near'].cr, (0.85, 0.88, 0.9), 0.7)


# ---------------------------------------------------------------- 글자
def slide_text(cr, s, x, y, size, rgb, u_in, u_out, weight=cairo.FONT_WEIGHT_NORMAL, anchor='c'):
    if u_in <= 0 or u_out >= 1: return
    cr.save(); cr.select_font_face(SERIF, cairo.FONT_SLANT_NORMAL, weight); cr.set_font_size(size)
    ext = cr.text_extents(s); dx = {'l': 0, 'c': -ext.x_advance / 2, 'r': -ext.x_advance}[anchor]
    cr.rectangle(x + dx - 30, y - size * 1.05, ext.x_advance + 60, size * 1.35); cr.clip()
    off = (1 - expo_out(u_in)) * size * 1.15 - expo_in_out(u_out) * size * 1.15
    cr.move_to(x + dx, y + off); cr.text_path(s); cr.set_source_rgb(*rgb); cr.fill(); cr.restore()

def text_at(cr, s, x, y, size, rgb, a=1.0, weight=cairo.FONT_WEIGHT_NORMAL, anchor='c'):
    cr.save(); cr.select_font_face(SERIF, cairo.FONT_SLANT_NORMAL, weight); cr.set_font_size(size)
    ext = cr.text_extents(s); dx = {'l': 0, 'c': -ext.x_advance / 2, 'r': -ext.x_advance}[anchor]
    cr.move_to(x + dx, y); cr.text_path(s); cr.set_source_rgba(*rgb, a); cr.fill(); cr.restore()

def zone_times():
    """층에 들어서는 시각(카메라가 경계를 지날 때)."""
    out = []
    for i in range(5):
        y = d2y(ZB[i]) if i else 0
        tt = next((x / 100 for x in range(0, int(DUR * 100)) if cam_y(x / 100) >= y + (0 if i else 200)), DUR)
        out.append(tt)
    return out
ZT = zone_times()
ZT0_TITLE = next(x / 100 for x in range(0, int(DUR * 100)) if depth_now(x / 100) > 60)

def draw_type(t, ty):
    d = depth_now(t); z = zone_of(d)
    light = d > 300
    col = WHITE if light else hexc('#0E3A44')
    # 처음 물음
    if t < T_DIVE + 1.0:
        uo = ramp(t, T_DIVE - 0.6, T_DIVE)
        slide_text(ty, '바다는', 540, 330, 104, INK, ramp(t, 0.3, 0.9), uo, cairo.FONT_WEIGHT_BOLD)
        slide_text(ty, '얼마나 깊을까?', 540, 470, 104, INK, ramp(t, 0.55, 1.15), uo, cairo.FONT_WEIGHT_BOLD)
        slide_text(ty, 'How deep is the ocean?', 540, 545, 36, INK, ramp(t, 0.7, 1.3), uo)
    # 층 이름
    if T_DIVE < t < T_PAY:
        for i in range(5):
            t0 = ZT0_TITLE if i == 0 else ZT[i]; t1 = min(ZT[i + 1] if i < 4 else T_PAY - 0.2, t0 + 3.6)
            if t0 - 0.1 < t < t1 + 0.4:
                ui, uo = ramp(t, t0, t0 + 0.45), ramp(t, t1 - 0.1, t1 + 0.3)
                c = WHITE if i >= 1 else hexc('#0E3A44')
                slide_text(ty, ZONES[i][0], 540, 300, 120, c, ui, uo, cairo.FONT_WEIGHT_BOLD)
                slide_text(ty, ZONES[i][1], 540, 370, 38, c, ramp(t, t0 + 0.08, t0 + 0.5), uo)
                slide_text(ty, ZONES[i][2], 540, 430, 40, c, ramp(t, t0 + 0.15, t0 + 0.6), uo, cairo.FONT_WEIGHT_BOLD)
                slide_text(ty, ZONES_FT[i], 540, 478, 30, c, ramp(t, t0 + 0.2, t0 + 0.65), uo)
    # 깊이 계기(아래 가운데)
    if T_DIVE + 0.4 < t < T_PAY + 0.6:
        a = smooth(ramp(t, T_DIVE + 0.4, T_DIVE + 1.0)) * (1 - smooth(ramp(t, T_PAY, T_PAY + 0.6)))
        dc = min(10935, y2d(cam_y(t) + 420 * smooth(ramp(t, 34.0, T_FLOOR))))
        text_at(ty, f'{int(round(dc)):,} m', 540, 1580, 96, col, a, cairo.FONT_WEIGHT_BOLD)
        text_at(ty, '수심 · DEPTH', 540, 1470, 34, col, a * 0.85)
        text_at(ty, f'{int(round(dc / 0.3048)):,} ft', 540, 1640, 34, col, a * 0.85)
    # 깊이에 붙은 이름표
    for dd, label, eng in [(8336, '물고기가 찍힌 가장 깊은 곳 · 8,336 m', 'Deepest fish ever filmed · 27,349 ft'), (10935, '챌린저 해연 · 10,935 m', 'Challenger Deep · 35,876 ft')]:
        y = sy(d2y(dd), t, 1.0)
        if -100 < y < DH + 100 and t < T_PAY:
            a = clamp(1 - abs(y - (DH / 2 + (120 if dd == 8336 else -180))) / 700, 0, 1)
            yy = (y - 150) if dd == 8336 else (y - 100)
            text_at(ty, label, 540, yy, 40, WHITE, a, cairo.FONT_WEIGHT_BOLD)
            text_at(ty, eng, 540, yy + 46, 32, WHITE, a * 0.9)


# ---------------------------------------------------------------- 정답: 비례 기둥 + 거꾸로 선 에베레스트
COLX, COLW, COLT, COLB = 250, 300, 380, 1700           # 기둥(화면)
def col_y(d, lin):
    """lin 0: 층마다 같은 높이(내려온 그대로), 1: 실제 비례."""
    yp = np.interp(d, ZB, np.linspace(COLT, COLB, 6)); yl = COLT + (COLB - COLT) * d / 10935
    return lerp(yp, yl, lin)

def draw_payoff(t, L, ty, base_only=False):
    u0 = expo_in_out(ramp(t, T_PAY, T_PAY + 1.3))      # 화면 → 기둥으로 줄어듦
    lin = expo_in_out(ramp(t, T_PAY + 1.5, T_PAY + 2.6))
    cr = L['main'].cr
    x0 = lerp(-40, COLX, u0); x1 = lerp(DW + 40, COLX + COLW, u0)
    for i in range(5):
        ya = col_y(ZB[i], lin); yb = col_y(ZB[i + 1], lin)
        ya = lerp(lerp(-40, DH, i / 5), ya, u0); yb = lerp(lerp(-40, DH, (i + 1) / 5), yb, u0)
        cr.rectangle(x0, ya, x1 - x0, yb - ya + 0.5); S.fill(cr, water((ZB[i] + ZB[i + 1]) / 2))
    # 수면선·바닥
    a = smooth(ramp(t, T_PAY + 1.0, T_PAY + 1.6))
    for i in range(6):
        y = col_y(ZB[i], lin)
        if a > 0:
            lab = ['0 m', '200 m', '1,000 m', '4,000 m', '6,000 m', '10,935 m'][i]
            text_at(ty, lab, COLX - 24, y + 12, 30 if i not in (0, 5) else 34, INK, a * (1 - lin if i == 1 else 1), cairo.FONT_WEIGHT_BOLD if i == 5 else cairo.FONT_WEIGHT_NORMAL, 'r')
    # 거꾸로 에베레스트(8,849 m): 수면에서 내려와 꼭대기가 멈춤
    ue = back_out(ramp(t, T_PAY + 3.0, T_PAY + 4.4), 1.2)
    if ue > 0:
        tip = col_y(8849, 1.0); top = col_y(0, 1.0)
        h = (tip - top)
        oy = -h * (1 - ue)
        mc = L['near'].cr
        cx = COLX + COLW / 2
        rng = np.random.default_rng(88)
        # 능선 윤곽(위가 밑동, 아래로 뾰족): 가운데 봉우리 + 양옆 어깨
        prof = []
        for u in np.linspace(-1, 1, 41):
            hgt = (1 - abs(u)) ** 0.9 * 0.86 + 0.14 * math.exp(-(u / 0.07) ** 2)
            hgt += 0.07 * (abs(math.sin(u * 23 + 1.3)) - 0.5) * (1 - abs(u)) + 0.05 * math.exp(-((u + 0.42) / 0.08) ** 2) + 0.04 * math.exp(-((u - 0.3) / 0.07) ** 2)
            prof.append((cx + u * (COLW / 2 + 90), top + oy + h * clamp(hgt, 0.02, 1.0) + rng.uniform(-8, 8) * (abs(u) < 0.95)))
        pts = [(COLX - 90, top + oy - 6)] + prof + [(COLX + COLW + 90, top + oy - 6)]
        S.poly(mc, pts); S.fill(mc, hexc('#8C8478'))
        shade = [(cx, top + oy - 6)] + [p_ for p_ in prof if p_[0] >= cx] + [(COLX + COLW + 90, top + oy - 6)]
        S.poly(mc, shade); S.fill(mc, hexc('#6F685E'))
        snow = [p_ for p_ in prof if abs(p_[0] - cx) < 46]
        snow = [p_ for p_ in prof if abs(p_[0] - cx) < 70]
        S.poly(mc, snow + [(cx + 45, top + oy + h * 0.74), (cx + 10, top + oy + h * 0.80), (cx - 20, top + oy + h * 0.73), (cx - 50, top + oy + h * 0.76)]); S.fill(mc, WHITE)
        a2 = smooth(ramp(t, T_PAY + 4.3, T_PAY + 4.8))
        text_at(ty, '에베레스트 8,849 m', COLX + COLW + 40, top + h * 0.55, 40, INK, a2, cairo.FONT_WEIGHT_BOLD, 'l')
        text_at(ty, '(거꾸로 · upside down)', COLX + COLW + 40, top + h * 0.55 + 50, 30, INK, a2, anchor='l')
        text_at(ty, '29,032 ft', COLX + COLW + 40, top + h * 0.55 + 88, 30, INK, a2, anchor='l')
        # 남은 물
        a3 = smooth(ramp(t, T_PAY + 4.9, T_PAY + 5.4))
        if a3 > 0:
            yb = col_y(10935, 1.0)
            for yy in (tip, yb): S.bar(ty, COLX + COLW + 20, yy, COLX + COLW + 60, yy, 4)
            S.bar(ty, COLX + COLW + 40, tip, COLX + COLW + 40, tip + (yb - tip) * a3, 4); S.fill(ty, hexc('#E0442E'), a3)
            text_at(ty, '아직 2,086 m', COLX + COLW + 80, (tip + yb) / 2 + 14, 46, hexc('#E0442E'), a3, cairo.FONT_WEIGHT_BOLD, 'l')
            text_at(ty, 'still 6,844 ft of water', COLX + COLW + 80, (tip + yb) / 2 + 56, 30, hexc('#E0442E'), a3, anchor='l')
    # 위 제목
    slide_text(ty, '가장 깊은 바다에', 540, 170, 64, INK, ramp(t, T_PAY + 1.2, T_PAY + 1.7), ramp(t, T_END - 0.4, T_END), cairo.FONT_WEIGHT_BOLD)
    slide_text(ty, '에베레스트를 거꾸로 넣으면', 540, 255, 56, INK, ramp(t, T_PAY + 2.6, T_PAY + 3.1), ramp(t, T_END - 0.4, T_END))
    slide_text(ty, 'Drop Everest upside down into the deepest sea…', 540, 310, 32, INK, ramp(t, T_PAY + 2.7, T_PAY + 3.2), ramp(t, T_END - 0.4, T_END))
    slide_text(ty, '꼭대기 위로 아직 2 km', 540, 1790, 58, hexc('#E0442E'), ramp(t, T_PAY + 5.6, T_PAY + 6.1), ramp(t, T_END - 0.4, T_END), cairo.FONT_WEIGHT_BOLD)
    slide_text(ty, '…its peak is still 2 km (1.3 mi) under water', 540, 1842, 32, hexc('#E0442E'), ramp(t, T_PAY + 5.7, T_PAY + 6.2), ramp(t, T_END - 0.4, T_END))


# ---------------------------------------------------------------- 합성
def water_bg(t):
    """물빛: 화면 줄마다 그 높이의 깊이 색(+ 한지 결)."""
    cy = cam_y(t)
    rows = np.arange(H) / SC
    wy = cy + (rows - DH / 2)
    dd = np.interp(wy, ZY, ZB)
    cols = np.stack([np.interp(dd, WD, [c[i] for c in WC]) for i in range(3)], 1)      # RGB
    sky = wy < -20
    cols[sky] = CREAM
    img = np.repeat(cols[:, None, ::-1], W, 1).astype(np.float32)
    return img * tex()[..., None]

def tinted(rgba, f, t):
    """먼 겹일수록 물빛에 잠긴다(premultiplied에서 섞기)."""
    if f <= 0: return rgba
    cy = cam_y(t); rows = np.arange(H) / SC
    dd = np.interp(cy + (rows - DH / 2), ZY, ZB)
    wc = np.stack([np.interp(dd, WD, [c[i] for c in WC]) for i in range(3)], 1)[:, ::-1].astype(np.float32)   # BGR
    fr = (f * np.clip((cy + (rows - DH / 2)) / 60, 0, 1)).astype(np.float32)[:, None, None]   # 하늘(물 밖)은 섞지 않음
    out = rgba.copy()
    out[..., :3] = rgba[..., :3] * (1 - fr) + wc[:, None, :] * rgba[..., 3:4] * fr
    return out

def blur_level(rgba, s):
    if s <= 0 or rgba[..., 3].max() < 1e-4: return rgba
    return cv2.GaussianBlur(rgba, (0, 0), s * SC)

def additive(base, rgba, bloom=0.0, k=1.0):
    if rgba[..., 3].max() < 1e-4: return base
    add = rgba[..., :3] * k
    if bloom > 0:
        add = add + cv2.GaussianBlur(rgba[..., :3], (0, 0), bloom * SC) * 1.6 + cv2.GaussianBlur(rgba[..., :3], (0, 0), bloom * 3 * SC) * 0.8
    return np.clip(base + add, 0, 1.4)


def frame(t, samples=3, shutter=0.5):
    names = [l[0] for l in LAYERS] + ['glow', 'ray', 'type']
    acc = {}
    for si in range(samples):
        tt = t + ((si + 0.5) / samples - 0.5) * shutter / FPS if samples > 1 else t
        L = {n: Level() for n in names}
        if tt < T_PAY:
            draw_world(tt, L, L['glow'], L['ray'])
        if tt >= T_PAY - 0.01:
            draw_payoff(tt, L, L['type'].cr)
        if tt < T_PAY + 0.8: draw_type(tt, L['type'].cr)
        for n in names:
            a = L[n].array(); acc[n] = a if n not in acc else acc[n] + a
    for n in acc: acc[n] /= samples
    if t < T_PAY:
        base = water_bg(t)
    else:
        u0 = expo_in_out(ramp(t, T_PAY, T_PAY + 1.3))
        base = water_bg(T_PAY - 0.001) * (1 - u0) + np.array(CREAM[::-1], np.float32) * tex()[..., None] * u0
    base = additive(base, acc['ray'])
    for n, p, tint, bl, dep, sh in LAYERS:
        lay = acc[n]
        if t < T_PAY: lay = blur_level(tinted(lay, tint, t), bl)
        base = composite(base, lay, dep, sh)
    base = additive(base, acc['glow'], bloom=5.0, k=0.9)
    base = composite(base, acc['type'], 0.5, 0.22)
    return np.clip(base, 0, 1)


_VIG = None
def vignette_mask():
    global _VIG
    if _VIG is None:
        y, x = np.mgrid[0:H, 0:W].astype(np.float32)
        r = np.hypot((x - W / 2) / (W / 2), (y - H / 2) / (H / 2))
        _VIG = (1 - 0.22 * np.clip(r - 0.5, 0, 1) ** 1.4)[..., None].astype(np.float32)
    return _VIG


CREDIT = ['Created & Coded by L.S.M.', '허상공방 虛像工房 Project']
T_SEAL = T_END + 0.4
_credit = {}
def credit_layer():
    if _credit: return _credit['v']
    from PIL import Image, ImageDraw, ImageFont
    S2 = 2.0 * SC
    fnt = ImageFont.truetype('/usr/share/fonts/opentype/noto/NotoSerifCJK-Regular.ttc', int(19 * S2), index=1)
    sz = int(round(110 * SC)); cx, cy = 540, 820
    xs, ys = int(round(cx * SC)) - sz // 2, int(round(cy * SC))
    im = Image.new('L', (W, H), 0); d = ImageDraw.Draw(im)
    d.text((int(cx * SC), ys + sz + int(30 * S2)), CREDIT[0], font=fnt, fill=255, anchor='mm')
    d.text((int(cx * SC), ys + sz + int(60 * S2)), CREDIT[1], font=fnt, fill=255, anchor='mm')
    tm = cv2.GaussianBlur(np.asarray(im, np.float32) / 255, (0, 0), 0.35 * S2)
    seal = np.load(os.path.join(HERE, '..', '_shared', 'seal_baimun3.npy')).astype(np.float32)
    seal = cv2.resize(seal, (sz, sz), interpolation=cv2.INTER_AREA)[..., [2, 1, 0, 3]]
    _credit['v'] = (tm, seal, xs, ys, sz); return _credit['v']

def end_card(img, t):
    if t < T_END: return img
    u = smooth(ramp(t, T_END, T_END + 0.8))
    paper = np.array(CREAM[::-1], np.float32) * tex()[..., None]
    img = img * (1 - u) + paper * u
    if t < T_SEAL: return img
    tm, seal, xs, ys, sz = credit_layer()
    a1 = smooth(ramp(t, T_SEAL, T_SEAL + 0.2))
    red = np.clip((seal[..., 2:3] - seal[..., 1:2]) * 4, 0, 1)
    al = seal[..., 3:4] * a1 * red
    sub = img[ys:ys + sz, xs:xs + sz]; img[ys:ys + sz, xs:xs + sz] = sub * (1 - al + al * seal[..., :3])
    a2 = smooth(ramp(t, T_SEAL + 0.5, T_SEAL + 1.4)); k = (tm * a2 * 0.92)[..., None]
    return img * (1 - k) + np.array(INK[::-1], np.float32) * k


def final(t, samples=3):
    img = frame(t, samples) * vignette_mask()
    img = end_card(img, t)
    return grain(img, int(round(t * FPS)), 0.008)


if __name__ == '__main__':
    out = sys.argv[1]; os.makedirs(out, exist_ok=True)
    for ts in sys.argv[2:]:
        t = float(ts); img = final(t)
        cv2.imwrite(os.path.join(out, f't{t:05.2f}.png'), np.clip(img * 255, 0, 255).astype(np.uint8))
        print('wrote', t, round(depth_now(t)), flush=True)
