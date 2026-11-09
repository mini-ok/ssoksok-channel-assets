"""〈파루〉 무음 움직임 시험 8초 — 자격루 단면도(의궤 도설풍 선화 + 담채).

0~4초: 정상 연쇄. 물이 차오르며 거북 부력체의 살대가 올라가 걸쇠를 밀면, 보통 구슬이 홈을 굴러 지렛대를 치고,
       지렛대가 큰 구슬을 밀어 보내고, 큰 구슬이 연결대를 눌러 시보 인형이 징을 친다.
5~8초: 주인공(혼자 작은 구슬)의 차례. 구멍에서 헐겁게 덜컥거리다 굴러 나와, 보통 구슬은 넘어가는 틈에 빠진다.
       틈 가장자리에서 세 번 흔들리고(망설임), 빈 홀드, 그리고 아래로 떨어진다.
모든 것은 t의 순수 함수. 투스(12fps)로 그린다.
"""
import sys, os, math, subprocess
import numpy as np, cv2, cairo
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'jeom'))
from ink import fbm, make_fibers

F32 = np.float32
W, H = 1920, 1080
INK = (0.17, 0.12, 0.09)

# ------------------------------------------------------------ 손그림 선
def resample(pts, step=3.0, closed=False):
    P = np.array(pts, float)
    if closed:
        P = np.vstack([P, P[:1]])
    seg = np.linalg.norm(np.diff(P, axis=0), axis=1)
    s = np.concatenate([[0], np.cumsum(seg)]); L = s[-1]
    n = max(2, int(L / step))
    t = np.linspace(0, L, n)
    return np.stack([np.interp(t, s, P[:, 0]), np.interp(t, s, P[:, 1])], 1), t, L


def lowfreq(t, seed, period=130.0):
    r = np.random.default_rng(seed)
    ph = r.uniform(0, 6.28, 3); k = r.uniform(0.7, 1.3, 3)
    return (np.sin(t / period * 6.28 * k[0] + ph[0]) * 0.6 + np.sin(t / period * 3.1 * k[1] + ph[1]) * 0.3
            + np.sin(t / period * 11.0 * k[2] + ph[2]) * 0.1)


BOIL = [0]


def hand(ctx, pts, w=2.2, seed=0, closed=False, color=INK, wob=0.9):
    P, t, L = resample(pts, 2.5, closed)
    if len(P) < 2:
        return
    d = np.gradient(P, axis=0); n = np.stack([-d[:, 1], d[:, 0]], 1)
    n /= (np.linalg.norm(n, axis=1, keepdims=True) + 1e-9)
    off = lowfreq(t, seed) * wob
    rb = np.random.default_rng(seed * 7 + BOIL[0])
    off = off + rb.normal(0, 0.18) + 0.18 * np.sin(t / 37 + rb.uniform(0, 6))
    C = P + n * off[:, None]
    u = t / max(L, 1e-6)
    prof = w * (0.82 + 0.3 * lowfreq(t, seed + 3, 90))
    if not closed:
        prof = prof * np.clip(np.minimum(u, 1 - u) / 0.08, 0.25, 1)
    Lf = C + n * prof[:, None] * 0.5; Rt = C - n * prof[:, None] * 0.5
    ctx.set_source_rgb(*color)
    ctx.move_to(*Lf[0])
    for p in Lf[1:]:
        ctx.line_to(*p)
    for p in Rt[::-1]:
        ctx.line_to(*p)
    ctx.close_path(); ctx.fill()


def circ(cx, cy, r, n=None, a0=0.0):
    n = n or max(16, int(r * 1.2))
    a = np.linspace(0, 2 * math.pi, n, endpoint=False) + a0
    return np.stack([cx + r * np.cos(a), cy + r * np.sin(a)], 1)


def rect(x0, y0, x1, y1):
    return [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]


def rot(pts, cx, cy, ang):
    c, s = math.cos(ang), math.sin(ang)
    P = np.array(pts, float) - (cx, cy)
    return np.stack([P[:, 0] * c - P[:, 1] * s, P[:, 0] * s + P[:, 1] * c], 1) + (cx, cy)


def fillpoly(ctx, pts, rgb, a=1.0):
    ctx.set_source_rgba(*rgb, a)
    ctx.move_to(*pts[0])
    for p in pts[1:]:
        ctx.line_to(*p)
    ctx.close_path(); ctx.fill()


def hatch(ctx, poly, spacing=9, seed=0, ang=0.8):
    ctx.save()
    ctx.move_to(*poly[0])
    for p in poly[1:]:
        ctx.line_to(*p)
    ctx.close_path(); ctx.clip()
    xs = [p[0] for p in poly]; ys = [p[1] for p in poly]
    x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys)
    k = 0
    for c in np.arange(x0 - (y1 - y0), x1 + spacing, spacing):
        hand(ctx, [(c, y1), (c + (y1 - y0) * ang, y0)], 0.9, seed + k, wob=0.5); k += 1
    ctx.restore()


# ------------------------------------------------------------ 종이
_r = np.random.default_rng(3)
FIB = cv2.GaussianBlur(make_fibers(W, H, 21, 7000, 25, 140), (0, 0), 0.6)
MOT = fbm(W, H, 22, 5, 3)
FLK = make_fibers(W, H, 23, 300, 3, 14, 2)
PAPER = (np.array((0.90, 0.85, 0.74), F32) * (1 + 0.03 * MOT[..., None])
         + 0.03 * FIB[..., None] - 0.08 * FLK[..., None] * np.array((0.5, 0.65, 0.85), F32))
WASH_MOT = fbm(W, H, 24, 4, 9)
yy_, xx_ = np.mgrid[0:H, 0:W].astype(F32)
VIG = 1 - 0.20 * (((xx_ - W / 2) / (W / 2)) ** 2 + ((yy_ - H / 2) / (H / 2)) ** 2)

# 색
BRONZE = (0.80, 0.62, 0.33)
BRONZE_D = (0.55, 0.40, 0.20)
WOOD = (0.78, 0.60, 0.40)
WATER = (0.60, 0.74, 0.78)
RED = (0.78, 0.28, 0.20)
SKIN = (0.93, 0.80, 0.62)
STONE = (0.72, 0.70, 0.64)

# ------------------------------------------------------------ 장치 배치
CYL = (150, 560, 340, 1040)         # 수수호 단면 바깥
WALL = 16
ROD_X = 245
def water_y(t): return 1000 - 45 * t
def tip_y(t): return water_y(t) - 425

PLATE_X = 268                       # 걸쇠 판
LATCH_Y = [535, 355, 215, 150]      # 1: 보통, 2: 주인공(작음), 3·4: 보통(정지)
BALL_R = [16, 10.5, 16, 16]
def latch_open(i, t):
    """살대 끝이 걸쇠를 지나면 걸쇠가 위로 젖혀진다(0 → 1)."""
    tt = (LATCH_Y[i] - 580) / -45      # tip_y(tt) = LATCH_Y
    if t < tt:
        return 0.0
    return min(1.0, (t - tt) / 0.16)
T_OPEN = [(y - 580) / -45 for y in LATCH_Y]

C1A, C1B = np.array((300.0, 548.0)), np.array((1000.0, 738.0))
GAP = (688.0, 714.0)                # 홈 틈(x 범위): 보통 구슬은 넘어가고 작은 구슬은 빠진다
CH2A, CH2B = np.array((300.0, 368.0)), np.array((500.0, 602.0))   # 주인공 슈트 → C1 합류
LEV_P = np.array((1035.0, 772.0))   # 지렛대 받침
C2A, C2B = np.array((1120.0, 742.0)), np.array((1520.0, 878.0))
BIG_R = 30
TRIG = np.array((1548.0, 890.0))
PUP = np.array((1640.0, 660.0))     # 인형 발 위치(받침 위)
SHOULDER = PUP + (0, -150)
GONG = np.array((1810.0, 480.0))


def line_pos(A, B, s, r):
    d = B - A; L = np.linalg.norm(d); u = d / L
    n = np.array((u[1], -u[0]))      # 위쪽 법선
    return A + u * s + n * r, L


def roll(A, B, t0, v0, a, t, r):
    """경사 위를 구르는 공. (중심, 진행 거리, 끝났는가, 끝난 시각, 끝 속도)"""
    L = np.linalg.norm(B - A)
    dt = max(0.0, t - t0)
    # s = v0 dt + a dt^2/2 → 끝 시각
    tend = (-v0 + math.sqrt(v0 * v0 + 2 * a * L)) / a
    if dt >= tend:
        return None, L, True, t0 + tend, v0 + a * tend
    s = v0 * dt + 0.5 * a * dt * dt
    c, _ = line_pos(A, B, s, r)
    return c, s, False, None, v0 + a * dt


A1 = 1500.0     # 홈 1 가속(px/s^2)

# --- 보통 구슬(1번)
def ball1(t):
    r = BALL_R[0]
    if t < T_OPEN[0] + 0.05:
        c, _ = line_pos(C1A, C1B, 14, r); return c, 0.0, True
    c, s, done, tend, vend = roll(C1A, C1B, T_OPEN[0] + 0.05, 0, A1, t, r)
    if not done:
        sx = c[0]
        if GAP[0] - 6 < sx < GAP[1] + 6:                 # 틈 위를 지날 때 살짝 내려앉음
            k = 1 - abs(sx - (GAP[0] + GAP[1]) / 2) / ((GAP[1] - GAP[0]) / 2 + 6)
            c = c + (0, 3.5 * max(0, k))
        return c, (s - 14) / r, True
    # 홈 끝 → 지렛대 왼쪽 끝으로 떨어졌다가 아래로 빠짐
    dt = t - tend
    end, _ = line_pos(C1A, C1B, np.linalg.norm(C1B - C1A), r)
    vx = vend * (C1B - C1A)[0] / np.linalg.norm(C1B - C1A)
    p = end + (vx * dt, 0.5 * 2400 * dt * dt)
    return p, (np.linalg.norm(C1B - C1A) - 14) / r + dt * 8, p[1] < H + 40


T_HIT1 = None
def _hit1():
    # 공 1이 지렛대 왼쪽 끝 높이(약 y 760)를 지나는 시각
    for k in range(4000):
        t = k / 1000.0
        c, a, v = ball1(t)
        if c[0] > 1000 and c[1] > 752:
            return t
    return 3.0
T_HIT1 = _hit1()

def lever_ang(t):
    """지렛대 각(라디안, +는 왼쪽 끝이 내려감). 계단식 키 + 오버슛, 복귀."""
    if t < T_HIT1:
        return 0.0
    keys = [(0.0, 0.0), (1 / 12, 0.34), (2 / 12, 0.48), (3 / 12, 0.40), (4 / 12, 0.42)]
    dt = t - T_HIT1
    val = keys[-1][1]
    for (kt, kv) in keys:
        if dt >= kt:
            val = kv
    # 1.6초 뒤 추가 무게로 천천히 복귀(계단 3장)
    back = [(1.6, 0.30), (1.75, 0.15), (1.9, -0.03), (2.05, 0.0)]
    for (kt, kv) in back:
        if dt >= kt:
            val = kv
    return val


T_BIG = None
def bigball(t):
    r = BIG_R
    t0 = T_HIT1 + 2 / 12
    if t < t0:
        c, _ = line_pos(C2A, C2B, 0, r); return c, 0.0, True
    c, s, done, tend, vend = roll(C2A, C2B, t0, 40, 700, t, r)
    if not done:
        return c, s / r, True
    dt = t - tend
    end, _ = line_pos(C2A, C2B, np.linalg.norm(C2B - C2A), r)
    p = end + (vend * 0.95 * dt, 0.5 * 2400 * dt * dt)
    return p, np.linalg.norm(C2B - C2A) / r + dt * 5, p[1] < H + 60

def _big_end():
    for k in range(6000):
        t = k / 1000
        c, a, v = bigball(t)
        if c[0] >= C2B[0] - 6:
            return t
    return 4.0
T_TRIG = _big_end()

def trig_depress(t):
    if t < T_TRIG:
        return 0.0
    dt = t - T_TRIG
    return 1.0 if dt < 0.9 else max(0.0, 1 - (dt - 0.9) / 0.2)

def arm_ang(t):
    """인형 팔(라디안, 0 = 앞으로 수평, +는 위로). 대기 -0.5 → 예비로 크게 들고 → 징을 침 → 되튐."""
    base = -0.5
    if t < T_TRIG:
        return base
    dt = t - T_TRIG
    keys = [(0, base), (1 / 12, 0.4), (2 / 12, 1.05), (3 / 12, 1.15), (5 / 12, 1.15),     # 들고 홀드
            (6 / 12, 0.24), (7 / 12, 0.10), (8 / 12, 0.20), (9 / 12, 0.17), (1.4, 0.17), (1.55, -0.3), (1.7, base)]
    v = base
    for kt, kv in keys:
        if dt >= kt:
            v = kv
    return v

T_STRIKE = None
def gong_shake(t):
    ts = T_TRIG + 6 / 12
    if t < ts:
        return 0.0, 0.0
    dt = t - ts
    return 0.045 * math.exp(-dt * 2.2) * math.cos(dt * 2 * math.pi * 1.6), dt


# --- 주인공(2번, 작은 구슬)
def ball2(t):
    r = BALL_R[1]
    t0 = T_OPEN[1]
    rest, _ = line_pos(CH2A, CH2B, 12, r)
    if t < t0:
        return rest, 0.0
    dt = t - t0
    # 1) 헐거운 구멍에서 덜컥: 3번(투스 키), 0.5초
    if dt < 0.5:
        jig = [(0, 0), (1 / 12, 3.5), (2 / 12, -1.5), (3 / 12, 2.5), (4 / 12, -0.5), (5 / 12, 1.0)]
        v = 0
        for kt, kv in jig:
            if dt >= kt:
                v = kv
        return rest + (v, -abs(v) * 0.4), v / r
    # 2) 슈트 → C1 합류 → 틈까지
    ts = t0 + 0.5
    L2 = np.linalg.norm(CH2B - CH2A) - 12
    c, s, done, tend, vend = roll(CH2A + (CH2B - CH2A) / np.linalg.norm(CH2B - CH2A) * 12, CH2B, ts, 0, 1900, t, r)
    if not done:
        return c, s / r
    # C1 위: 합류점부터 틈 앞까지
    s_join = float(np.dot(CH2B - C1A, (C1B - C1A) / np.linalg.norm(C1B - C1A)))
    s_gap = float(np.dot(np.array((GAP[0] + 3, 0)) - C1A, (C1B - C1A) / np.linalg.norm(C1B - C1A))) / ((C1B - C1A)[0] / np.linalg.norm(C1B - C1A)) * 1.0
    # x 기준으로 정확히: 틈 왼쪽 가장자리까지 진행 거리
    u = (C1B - C1A) / np.linalg.norm(C1B - C1A)
    s_gap = (GAP[0] + 4 - C1A[0]) / u[0]
    dist = s_gap - s_join
    v0 = vend * 0.85
    # 짧은 구간이라 등가속으로 근사
    a = A1 * 0.9
    tg = (-v0 + math.sqrt(v0 * v0 + 2 * a * dist)) / a
    dt2 = t - tend
    if dt2 < tg:
        ss = s_join + v0 * dt2 + 0.5 * a * dt2 * dt2
        c, _ = line_pos(C1A, C1B, ss, r)
        return c, (L2 + ss - s_join) / r
    # 3) 틈에 걸림: 건너편 가장자리 모서리에 걸쳐 멈춘다(모서리가 받침점)
    tgap = tend + tg
    corner, _ = line_pos(C1A, C1B, (GAP[1] - C1A[0]) / u[0], 0)
    base_rot = (L2 + dist) / r
    PHI0 = -2.25                              # 모서리 왼쪽 위(불안정한 균형)
    def at(phi):
        return corner + r * np.array((math.cos(phi), math.sin(phi)))
    dt3 = t - tgap
    if dt3 < 1 / 12:                           # 부딪힘: 한 장 더 밀려 올라갔다가
        return at(PHI0 + 0.35), base_rot + 0.2
    # 4) 모서리 위에서 세 번 흔들림(점점 작게) — 투스, 끝마다 홀드
    wob = [(1 / 12, -0.30), (2 / 12, 0.22), (4 / 12, 0.22), (5 / 12, -0.18), (6 / 12, 0.14), (8 / 12, 0.14),
           (9 / 12, -0.08), (10 / 12, 0.0)]
    v = 0.0
    for kt, kv in wob:
        if dt3 >= kt:
            v = kv
    HOLD_END = 10 / 12 + 0.55                  # 빈 홀드 0.55초
    if dt3 < HOLD_END:
        return at(PHI0 + v), base_rot + 0.2 + v
    # 5) 모서리에서 뒤로 넘어가 틈 아래로 떨어짐
    d4 = t - (tgap + HOLD_END)
    if d4 < 2 / 12:
        return at(PHI0 - 0.35 - 0.5 * (d4 >= 1 / 12)), base_rot - 0.4
    p0 = at(PHI0 - 1.0)
    d5 = d4 - 2 / 12
    p = p0 + (-25 * d5, 0.5 * 2400 * d5 * d5)
    return p, base_rot - 0.4 - d5 * 9


# ------------------------------------------------------------ 그리기
def draw_ball(ink, wash, c, r, ang, seed):
    pts = circ(c[0], c[1], r, a0=0.3)
    fillpoly(wash, pts, BRONZE)
    # 그늘(오른쪽 아래)과 하이라이트(왼쪽 위): 평면 셀 2톤
    sh = circ(c[0] + r * 0.18, c[1] + r * 0.2, r * 0.82)
    wash.save()
    wash.arc(c[0], c[1], r, 0, 2 * math.pi); wash.clip()
    fillpoly(wash, sh, BRONZE_D, 0.55)
    wash.restore()
    fillpoly(wash, circ(c[0] - r * 0.38, c[1] - r * 0.4, r * 0.22), (1.0, 0.95, 0.8), 0.9)
    hand(ink, pts, 1.9, seed, closed=True)
    # 주조 이음선: 굴러가는 것이 보이게
    a = ang
    p1 = (c[0] + math.cos(a) * r * 0.85, c[1] + math.sin(a) * r * 0.85)
    p2 = (c[0] + math.cos(a + 0.9) * r * 0.6, c[1] + math.sin(a + 0.9) * r * 0.6)
    hand(ink, [p1, ((p1[0] + p2[0]) / 2 + math.cos(a + 0.4) * r * 0.1, (p1[1] + p2[1]) / 2), p2], 1.1, seed + 9, wob=0.2)


def draw_channel(ink, wash, A, B, depth=14, seed=0, gap=None):
    d = B - A; L = np.linalg.norm(d); u = d / L; n = np.array((-u[1], u[0]))
    top = [A, B]; bot = [A + n * depth, B + n * depth]
    if gap is None:
        fillpoly(wash, [A, B, B + n * depth, A + n * depth], WOOD)
        hatch(wash if False else ink, [tuple(A), tuple(B), tuple(B + n * depth), tuple(A + n * depth)], 11, seed)
        hand(ink, top, 2.0, seed); hand(ink, bot, 1.6, seed + 1)
        return
    sg0 = (gap[0] - A[0]) / u[0]; sg1 = (gap[1] - A[0]) / u[0]
    for (s0, s1, k) in ((0, sg0, 0), (sg1, L, 1)):
        P0 = A + u * s0; P1 = A + u * s1
        fillpoly(wash, [P0, P1, P1 + n * depth, P0 + n * depth], WOOD)
        hatch(ink, [tuple(P0), tuple(P1), tuple(P1 + n * depth), tuple(P0 + n * depth)], 11, seed + 10 * k)
        hand(ink, [P0, P1], 2.0, seed + 2 * k); hand(ink, [P0 + n * depth, P1 + n * depth], 1.6, seed + 2 * k + 1)
        hand(ink, [P0, P0 + n * depth], 1.6, seed + 30 + k); hand(ink, [P1, P1 + n * depth], 1.6, seed + 40 + k)


def turtle(ink, wash, cx, wy, seed):
    shell = [(cx - 62 + 124 * k / 30, wy - 4 - 46 * math.sin(math.pi * k / 30) ** 0.8) for k in range(31)]
    shell_poly = shell + [(cx + 62, wy + 10), (cx - 62, wy + 10)]
    fillpoly(wash, shell_poly, (0.55, 0.62, 0.42))
    hand(ink, shell_poly, 2.2, seed, closed=True)
    for k in (-1, 0, 1):        # 등딱지 무늬
        hand(ink, [(cx + k * 32 - 14, wy - 24 + abs(k) * 6), (cx + k * 32, wy - 34 + abs(k) * 8), (cx + k * 32 + 14, wy - 24 + abs(k) * 6),
                   (cx + k * 32 + 10, wy - 8), (cx + k * 32 - 10, wy - 8), (cx + k * 32 - 14, wy - 24 + abs(k) * 6)], 1.1, seed + 5 + k)
    head = circ(cx + 68, wy - 6, 12)
    fillpoly(wash, head, (0.62, 0.68, 0.48)); hand(ink, head, 1.8, seed + 20, closed=True)
    fillpoly(ink, circ(cx + 72, wy - 9, 2.0), INK)
    for sx in (-1, 1):
        fl = [(cx + sx * 40, wy + 6), (cx + sx * 66, wy + 18), (cx + sx * 46, wy + 20)]
        fillpoly(wash, fl, (0.62, 0.68, 0.48)); hand(ink, fl, 1.5, seed + 30 + sx, closed=True)


def puppet(ink, wash, t, seed):
    fx, fy = PUP
    # 받침
    base = rect(fx - 70, fy, fx + 90, fy + 26)
    fillpoly(wash, base, WOOD); hand(ink, base, 2.0, seed, closed=True)
    hatch(ink, base, 12, seed + 3)
    # 몸(붉은 도포, 사다리꼴) — 나무 인형이라 뻣뻣하다
    body = [(fx - 34, fy), (fx + 34, fy), (fx + 22, fy - 140), (fx - 22, fy - 140)]
    fillpoly(wash, body, RED); hand(ink, body, 2.2, seed + 1, closed=True)
    hand(ink, [(fx, fy - 140), (fx - 6, fy - 70), (fx + 4, fy)], 1.2, seed + 2)
    # 머리 + 관모
    hc = (fx, fy - 170)
    head = circ(hc[0], hc[1], 26)
    fillpoly(wash, head, SKIN); hand(ink, head, 2.0, seed + 4, closed=True)
    hat = [(hc[0] - 30, hc[1] - 18), (hc[0] + 30, hc[1] - 18), (hc[0] + 20, hc[1] - 44), (hc[0] - 20, hc[1] - 44)]
    fillpoly(wash, hat, (0.2, 0.18, 0.18)); hand(ink, hat, 1.8, seed + 5, closed=True)
    for ex in (-9, 9):
        fillpoly(ink, circ(hc[0] + ex, hc[1] + 2, 2.6), INK)
    hand(ink, [(hc[0] - 5, hc[1] + 13), (hc[0] + 5, hc[1] + 13)], 1.2, seed + 6)
    # 팔 + 방망이
    a = arm_ang(t)
    sx, sy = SHOULDER[0] + 18, SHOULDER[1] + 18
    L = 92
    ex, ey = sx + math.cos(-a) * L, sy + math.sin(-a) * L
    arm = rot(rect(0, -9, L, 9), 0, 0, -a) + (sx, sy)
    fillpoly(wash, arm, RED); hand(ink, arm, 1.9, seed + 7, closed=True)
    hand_c = circ(ex, ey, 10)
    fillpoly(wash, hand_c, SKIN); hand(ink, hand_c, 1.6, seed + 8, closed=True)
    # 방망이: 손에서 아래로(팔과 직각)
    mal = rot(rect(0, -4, 52, 4), 0, 0, -a) + (ex, ey)
    fillpoly(wash, mal, WOOD); hand(ink, mal, 1.6, seed + 9, closed=True)
    mh = rot([(58, 0)], 0, 0, -a)[0] + (ex, ey)
    knob = circ(mh[0], mh[1], 11)
    fillpoly(wash, knob, (0.45, 0.32, 0.22)); hand(ink, knob, 1.7, seed + 10, closed=True)


def gong(ink, wash, t, seed):
    sh, _ = gong_shake(t)
    # 틀
    frame_ = [(GONG[0] - 110, GONG[1] - 150), (GONG[0] + 110, GONG[1] - 150)]
    post1 = rect(GONG[0] - 100, GONG[1] - 160, GONG[0] - 86, PUP[1] + 26)
    post2 = rect(GONG[0] + 86, GONG[1] - 160, GONG[0] + 100, PUP[1] + 26)
    for p in (post1, post2):
        fillpoly(wash, p, WOOD); hand(ink, p, 1.9, seed + len(p), closed=True)
    beam = rect(GONG[0] - 112, GONG[1] - 172, GONG[0] + 112, GONG[1] - 150)
    fillpoly(wash, beam, WOOD); hand(ink, beam, 2.0, seed + 2, closed=True)
    pv = (GONG[0], GONG[1] - 150)
    c = rot([GONG], pv[0], pv[1], sh)[0]
    for dx in (-34, 34):
        hand(ink, [(pv[0] + dx * 0.4, pv[1]), (c[0] + dx, c[1] - 68)], 1.2, seed + 3 + dx)
    g = circ(c[0], c[1], 70)
    fillpoly(wash, g, BRONZE); hand(ink, g, 2.4, seed + 5, closed=True)
    hand(ink, circ(c[0], c[1], 56), 1.2, seed + 6, closed=True)
    boss = circ(c[0], c[1], 20)
    fillpoly(wash, boss, BRONZE_D, 0.7); hand(ink, boss, 1.6, seed + 7, closed=True)
    fillpoly(wash, circ(c[0] - 30, c[1] - 30, 9), (1.0, 0.95, 0.8), 0.8)


def draw(t):
    BOIL[0] = int(math.floor(t * 12))
    ink_s = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H)
    wash_s = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H)
    ink = cairo.Context(ink_s); wash = cairo.Context(wash_s)
    for c in (ink, wash):
        c.set_antialias(cairo.ANTIALIAS_GOOD)

    # --- 수수호(단면) + 물 + 거북 + 살대
    x0, y0, x1, y1 = CYL
    wy = water_y(t)
    fillpoly(wash, rect(x0 + WALL, wy, x1 - WALL, y1 - WALL), WATER, 0.85)
    for k in range(4):
        yy = wy + 40 + k * 70
        if yy < y1 - WALL - 10:
            hand(ink, [(x0 + WALL + 12, yy), (x0 + WALL + 60, yy + 2), (x1 - WALL - 50, yy - 1)], 0.9, 400 + k, wob=0.6)
    hand(ink, [(x0 + WALL, wy), (x1 - WALL, wy)], 1.5, 401)
    for wall in (rect(x0, y0, x0 + WALL, y1), rect(x1 - WALL, y0, x1, y1), rect(x0, y1 - WALL, x1, y1)):
        fillpoly(wash, wall, BRONZE_D, 0.75)
        hatch(ink, wall, 8, 410)
        hand(ink, wall, 1.8, 420 + int(wall[0][0]), closed=True)
    turtle(ink, wash, ROD_X - 0, wy, 430)
    rod = rect(ROD_X - 6, tip_y(t), ROD_X + 6, wy - 30)
    fillpoly(wash, rod, WOOD); hand(ink, rod, 1.8, 440, closed=True)
    # 살대 안내 고리
    for gy in (y0 - 8, 470, 300):
        g = rect(ROD_X - 16, gy - 5, ROD_X + 16, gy + 5)
        fillpoly(wash, g, BRONZE_D, 0.8); hand(ink, g, 1.5, 450 + gy, closed=True)

    # --- 걸쇠 판 + 걸쇠 + 정지된 구슬들
    plate = rect(PLATE_X - 6, 130, PLATE_X + 6, 560)
    fillpoly(wash, plate, WOOD); hand(ink, plate, 1.8, 460, closed=True)
    for i, ly in enumerate(LATCH_Y):
        o = latch_open(i, t)
        tab = rot(rect(PLATE_X - 30, ly - 3, PLATE_X + 24, ly + 3), PLATE_X, ly, o * 0.55)
        fillpoly(wash, tab, BRONZE_D); hand(ink, tab, 1.4, 470 + i, closed=True)
        pv = circ(PLATE_X, ly, 3.5); fillpoly(ink, pv, INK)
        if i >= 2:      # 위쪽의 차례 기다리는 보통 구슬들(정지)
            sh_a = np.array((PLATE_X + 8.0, ly + 10)); sh_b = sh_a + (60, 16)
            hand(ink, [sh_a, sh_b], 2.0, 480 + i)
            c, _ = line_pos(sh_a, sh_b, 22, BALL_R[i])
            draw_ball(ink, wash, c, BALL_R[i], 0.0, 490 + i)

    # --- 홈들
    draw_channel(ink, wash, C1A, C1B, 14, 500, gap=GAP)
    draw_channel(ink, wash, CH2A, CH2B, 12, 520)
    # 지렛대
    la = lever_ang(t)
    lev = rot(rect(LEV_P[0] - 50, LEV_P[1] - 6, LEV_P[0] + 110, LEV_P[1] + 6), LEV_P[0], LEV_P[1], -la)
    fillpoly(wash, lev, BRONZE); hand(ink, lev, 1.9, 540, closed=True)
    tri = [(LEV_P[0], LEV_P[1] + 4), (LEV_P[0] - 18, LEV_P[1] + 40), (LEV_P[0] + 18, LEV_P[1] + 40)]
    fillpoly(wash, tri, WOOD); hand(ink, tri, 1.8, 541, closed=True)
    fillpoly(ink, circ(LEV_P[0], LEV_P[1], 4), INK)
    # 큰 구슬 받침 홈
    draw_channel(ink, wash, C2A, C2B, 16, 560)
    # 트리거 + 연결대 → 인형 팔
    dep = trig_depress(t)
    trg = rect(TRIG[0] - 14, TRIG[1] - 4 + dep * 8, TRIG[0] + 14, TRIG[1] + 6 + dep * 8)
    fillpoly(wash, trg, BRONZE); hand(ink, trg, 1.6, 570, closed=True)
    hand(ink, [(TRIG[0], TRIG[1] + 6 + dep * 8), (TRIG[0], PUP[1] + 60), (PUP[0] - 40, PUP[1] + 60), (PUP[0] - 40, PUP[1] + 26)], 2.0, 571)

    # --- 인형, 징
    gong(ink, wash, t, 600)
    puppet(ink, wash, t, 650)

    # --- 구슬들
    c, a, vis = ball1(t)
    if vis:
        draw_ball(ink, wash, c, BALL_R[0], a, 700)
    c, a, vis = bigball(t)
    if vis:
        draw_ball(ink, wash, c, BIG_R, a, 710)
    c, a = ball2(t)
    if c[1] < H + 30:
        draw_ball(ink, wash, c, BALL_R[1], a, 720)

    # --- 글씨(도설 표기): 확인된 명칭만
    ink.select_font_face('Noto Serif CJK KR', cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)
    ink.set_font_size(30); ink.set_source_rgb(*INK)
    ink.move_to(CYL[0] - 10, CYL[1] - 24); ink.show_text('受水壺')

    return ink_s, wash_s


def surf_to_np(s):
    a = np.ndarray((H, W, 4), np.uint8, s.get_data()).astype(F32) / 255
    return a   # BGRA premultiplied


def composite(t):
    ink_s, wash_s = draw(t)
    ink = surf_to_np(ink_s); wash = surf_to_np(wash_s)
    # 담채: 선보다 1~2px 밀리고 살짝 번진 물감, 가장자리에 물감이 고인다
    wa = wash[..., 3]
    M = np.float32([[1, 0, 1.6], [0, 1, 1.1]])
    wash = cv2.warpAffine(wash, M, (W, H))
    wash = cv2.GaussianBlur(wash, (0, 0), 0.9)
    wa = wash[..., 3:4]
    col = np.where(wa > 1e-3, wash[..., :3] / np.maximum(wa, 1e-3), 0)[..., ::-1]
    edge = np.clip(wa - cv2.GaussianBlur(wa, (0, 0), 4)[..., None], 0, 1)
    col = col * (1 + 0.07 * WASH_MOT[..., None]) * (1 - 0.6 * edge)
    a = wa * 0.82
    img = PAPER * (1 - a) + PAPER * col * a                  # 종이에 곱하기(종이 결이 비침)
    ia = ink[..., 3:4]
    icol = np.where(ia > 1e-3, ink[..., :3] / np.maximum(ia, 1e-3), 0)[..., ::-1]
    img = img * (1 - ia * 0.92) + icol * PAPER * ia * 0.92
    img = img * VIG[..., None]
    rg = np.random.default_rng(int(math.floor(t * 12)) * 7 + 3)
    gr = cv2.resize(rg.standard_normal((H // 2, W // 2)).astype(F32), (W, H))
    img = img + 0.010 * gr[..., None]
    r2 = np.random.default_rng(int(math.floor(t * 12)) * 31 + 5)
    Mw = np.float32([[1, 0, r2.normal(0, 0.5)], [0, 1, r2.normal(0, 0.35)]])
    img = cv2.warpAffine(img, Mw, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
    return np.clip(img, 0, 1)


if __name__ == '__main__':
    print('T_HIT1', T_HIT1, 'T_TRIG', T_TRIG, 'T_OPEN', T_OPEN)
    if len(sys.argv) > 1 and sys.argv[1] == 'still':
        for ts in sys.argv[2:]:
            img = composite(float(ts))
            cv2.imwrite(f'still_{ts}.png', (img[..., ::-1] * 255 + 0.5).astype(np.uint8))
        sys.exit()
    os.makedirs('frames', exist_ok=True)
    FPS, DUR = 24, 9.0
    last = None
    for fi in range(int(DUR * FPS)):
        t = fi / FPS; th = math.floor(t * 12) / 12
        if last is None or last[0] != th:
            img = composite(th)
            last = (th, (img[..., ::-1] * 255 + 0.5).astype(np.uint8))
        cv2.imwrite(f'frames/f{fi:04d}.png', last[1])
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-framerate', '24', '-i', 'frames/f%04d.png',
                    '-c:v', 'libx264', '-crf', '18', '-pix_fmt', 'yuv420p',
                    '-vf', 'colorspace=all=bt709:iall=bt709', 'paru_test_9s.mp4'])
