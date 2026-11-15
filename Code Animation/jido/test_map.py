"""〈지도〉 기술 시험: 로봇청소기의 라이다 지도가 집을 그려 간다(5초, 무음).
- 집 평면(벽·문·가구 다리)을 선분·원으로 두고, 청소기 위치에서 광선을 쏘아 맞은 점을 쌓는다.
- 맞은 점(벽) = 차가운 흰 점, 지나간 바닥 = 옅은 면, 지나온 길 = 가는 선, 움직이는 발 = 따뜻한 점 무리(남지 않음).
사용: JIDO_SCALE=0.5 python3 test_map.py out.mp4 [초]
"""
import os, sys, math, subprocess
import numpy as np, cv2

SC = float(os.environ.get('JIDO_SCALE', '1')); W, H = int(1920 * SC), int(1080 * SC)
FPS = int(os.environ.get('JIDO_FPS', '30')); DUR = float(sys.argv[2]) if len(sys.argv) > 2 else 5.0
OUT = sys.argv[1] if len(sys.argv) > 1 else 'map_test.mp4'
SS = 2                                                    # 슈퍼샘플

BG = np.array([0.055, 0.045, 0.040])                      # BGR, 깊은 남색
WALL = np.array([0.98, 0.95, 0.86])                       # 차가운 흰빛
FLOOR = np.array([0.30, 0.20, 0.13])
FOOT = np.array([0.35, 0.68, 1.00])                       # 따뜻한 호박색
LED = np.array([0.55, 1.00, 0.55])

# ---------------------------------------------------------------- 집(미터). 선분 목록 = 벽, 원 목록 = 가구 다리 등
def rect(x0, y0, x1, y1): return [((x0, y0), (x1, y0)), ((x1, y0), (x1, y1)), ((x1, y1), (x0, y1)), ((x0, y1), (x0, y0))]
SEG = []
SEG += [((0, 0), (10, 0)), ((10, 0), (10, 6.2)), ((10, 6.2), (0, 6.2)), ((0, 6.2), (0, 0))]     # 바깥벽
SEG += [((4.2, 0), (4.2, 2.3)), ((4.2, 3.2), (4.2, 6.2))]                                        # 거실 | 부엌·안방 (문 2.3–3.2)
SEG += [((4.2, 3.6), (6.6, 3.6)), ((7.5, 3.6), (10, 3.6))]                                       # 부엌 | 안방 (문 6.6–7.5)
SEG += [((0, 4.4), (1.4, 4.4)), ((2.3, 4.4), (2.6, 4.4))]                                        # 현관 칸막이
SEG += rect(0.5, 0.35, 2.9, 1.15)                                                                # 소파
SEG += rect(9.3, 0.3, 9.9, 1.2)                                                                  # 냉장고
SEG += rect(4.4, 4.1, 6.2, 6.0)                                                                  # 침대
SEG += rect(8.5, 5.4, 9.8, 6.0)                                                                  # 옷장
SEG += rect(4.3, 0.1, 7.6, 0.6)                                                                  # 싱크대
CIR = []
for (cx, cy) in [(6.2, 1.9), (7.6, 1.9), (6.2, 2.9), (7.6, 2.9)]: CIR.append((cx, cy, 0.035))   # 식탁 다리
for (cx, cy) in [(5.8, 2.1), (5.8, 2.7), (8.0, 2.1), (8.0, 2.7)]: CIR.append((cx, cy, 0.025))   # 의자 다리
for (cx, cy) in [(1.2, 2.6), (2.3, 2.6), (1.2, 3.3), (2.3, 3.3)]: CIR.append((cx, cy, 0.03))    # 낮은 탁자 다리
CIR.append((3.7, 5.6, 0.18))                                                                     # 화분
A = np.array([s[0] for s in SEG], float); B = np.array([s[1] for s in SEG], float)
CC = np.array([[c[0], c[1]] for c in CIR]); CR = np.array([c[2] for c in CIR])

# ---------------------------------------------------------------- 청소기 길(거실을 돌아 부엌으로) — 캣멀-롬
KEY = np.array([(3.5, 1.7), (3.2, 2.4), (2.6, 2.0), (1.6, 1.75), (0.7, 2.0), (0.6, 3.0), (1.0, 3.9), (2.2, 3.95),
                (3.4, 3.6), (3.9, 2.8), (4.7, 2.75), (5.4, 2.35), (6.0, 1.45), (7.2, 1.25), (8.6, 1.6), (8.9, 2.8)])
def path(u):
    n = len(KEY) - 1; x = min(max(u, 0), 0.9999) * n; i = int(x); f = x - i
    p0, p1, p2, p3 = KEY[max(i - 1, 0)], KEY[i], KEY[min(i + 1, n)], KEY[min(i + 2, n)]
    return 0.5 * ((2 * p1) + (-p0 + p2) * f + (2 * p0 - 5 * p1 + 4 * p2 - p3) * f * f + (-p0 + 3 * p1 - 3 * p2 + p3) * f ** 3)
def ease(u): u = min(max(u, 0), 1); return u * u * (3 - 2 * u)
def pos(t): return path(0.04 + 0.94 * (t / DUR) ** 0.92)

def feet(t):
    """할머니의 두 슬리퍼: 창가에서 부엌 쪽으로 천천히 걷다 멈춤."""
    u = ease(min(t / (DUR * 0.85), 1.0)); cx = 1.6 + 2.0 * u; cy = 5.2 - 1.0 * u
    step = math.sin(t * 5.5) * 0.12 * (1 - ease(max(0, (t - DUR * 0.75) / (DUR * 0.2))))
    d = np.array([2.0, -1.0]) / math.hypot(2, 1); nrm = np.array([-d[1], d[0]])
    return [np.array([cx, cy]) + nrm * 0.11 + d * step, np.array([cx, cy]) - nrm * 0.11 - d * step]

# ---------------------------------------------------------------- 광선
NR = 900
RANGE = 2.4                                                                       # 감지 거리(m): 지도가 청소기 둘레에서 조금씩 자라게
def cast(p, ang, fts):
    d = np.stack([np.cos(ang), np.sin(ang)], 1)                                 # (N,2)
    e = B - A                                                                    # (M,2)
    den = d[:, None, 0] * e[None, :, 1] - d[:, None, 1] * e[None, :, 0]
    w = A[None] - p[None, None]
    tt = (w[..., 0] * e[None, :, 1] - w[..., 1] * e[None, :, 0]) / np.where(np.abs(den) < 1e-9, 1e-9, den)
    ss = (w[..., 0] * d[:, None, 1] - w[..., 1] * d[:, None, 0]) / np.where(np.abs(den) < 1e-9, 1e-9, den)
    ok = (tt > 1e-4) & (ss >= 0) & (ss <= 1)
    dist = np.where(ok, tt, np.inf).min(1)
    kind = np.zeros(len(ang), int)
    cs = np.vstack([CC] + [f[None] for f in fts]); rs = np.concatenate([CR, [0.07, 0.07]])
    oc = cs[None] - p[None, None]                                                 # (1,K,2)
    b = (oc * d[:, None]).sum(-1); c = (oc ** 2).sum(-1) - rs[None] ** 2
    disc = b * b - c; th = b - np.sqrt(np.maximum(disc, 0))
    hit = (disc > 0) & (th > 1e-4)
    dc = np.where(hit, th, np.inf); j = dc.argmin(1); dmin = dc[np.arange(len(ang)), j]
    closer = dmin < dist
    dist = np.where(closer, dmin, dist); kind = np.where(closer & (j >= len(CR)), 2, np.where(closer, 1, 0))
    dist = np.minimum(dist, RANGE)
    return p[None] + d * dist[:, None], kind, dist

# ---------------------------------------------------------------- 화면 변환(미터 → 픽셀), 천천히 따라가며 당겨짐
def view(t, p):
    z = 118 + 30 * ease(t / DUR)                                                 # px/m (1080p 기준)
    c = np.array([4.6, 3.1]) * 0.55 + p * 0.45
    return z * SC * SS, c
def to_px(P, z, c): return ((P - c) * z + np.array([W * SS / 2, H * SS / 2])).astype(np.float32)

# ---------------------------------------------------------------- 시뮬레이션 + 렌더(한 프로세스, 처음부터 순서대로)
G = 0.035                                                                         # 점 격자 2 cm
hits = {}                                                                        # (i,j) -> 처음 본 시각
seen = np.zeros((int(6.2 / 0.04) + 1, int(10 / 0.04) + 1), np.uint8)             # 지나간 바닥(4 cm)
trail = []
rng = np.random.default_rng(3)

ff = subprocess.Popen(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'bgr24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-',
                       '-c:v', 'libx264', '-crf', '16', '-pix_fmt', 'yuv420p', OUT], stdin=subprocess.PIPE)
nf = int(DUR * FPS); spin0 = 0.0
for k in range(nf):
    t = k / FPS; p = pos(t); fts = feet(t); trail.append(p.copy())
    # 한 프레임 동안 라이다가 한 바퀴 돈다(시작 각도는 조금씩 밀림)
    ang = spin0 + np.linspace(0, 2 * np.pi, NR, endpoint=False) + rng.uniform(0, 2 * np.pi / NR, NR); spin0 += 0.37
    P, kind, dist = cast(p, ang, fts)
    noise = rng.normal(0, 0.006, P.shape); P = P + noise
    for (x, y), kd, ds in zip(P, kind, dist):
        if kd == 2 or ds >= RANGE - 1e-3: continue
        key = (int(round(x / G)), int(round(y / G)))
        if key not in hits: hits[key] = t
    poly = np.round(np.vstack([p, P[np.argsort(ang)]]) / 0.04).astype(np.int32)
    cv2.fillPoly(seen, [poly[1:]], 1)

    z, c = view(t, p)
    img = np.zeros((H * SS, W * SS, 3), np.float32) + BG
    # 지나간 바닥: 옅은 면 + 4 cm 격자 느낌
    sm = cv2.resize(seen.astype(np.float32), None, fx=0.04 * z, fy=0.04 * z, interpolation=cv2.INTER_LINEAR)
    M = np.float32([[1, 0, W * SS / 2 - c[0] * z], [0, 1, H * SS / 2 - c[1] * z]])
    fl = cv2.warpAffine(cv2.GaussianBlur(sm, (0, 0), 2 * SS), M, (W * SS, H * SS))
    img += fl[..., None] * FLOOR * 0.42
    gx = (np.arange(W * SS) - (W * SS / 2 - c[0] * z)) / z; gy = (np.arange(H * SS) - (H * SS / 2 - c[1] * z)) / z
    dx = np.abs(gx / 0.25 - np.round(gx / 0.25))[None, :] * 0.25 * z; dy = np.abs(gy / 0.25 - np.round(gy / 0.25))[:, None] * 0.25 * z
    dots = np.exp(-(dx ** 2 + dy ** 2) / (0.8 * SS) ** 2)
    img += (dots * fl)[..., None] * WALL * 0.10
    # 벽 점: 새로 맞은 점은 밝게 반짝였다가 가라앉음
    if hits:
        ks = np.array(list(hits.keys()), float) * G; ts = np.array(list(hits.values()))
        q = to_px(ks, z, c); age = t - ts
        jit = (np.sin(ks[:, 0] * 91.7 + ks[:, 1] * 37.3) * 0.5 + 0.5)
        br = (0.4 + 0.25 * jit) + 1.0 * np.exp(-age * 3.0) * np.clip(age * 12, 0, 1)
        lay = np.zeros((H * SS, W * SS), np.float32)
        qi = np.round(q).astype(int); ok = (qi[:, 0] >= 0) & (qi[:, 0] < W * SS) & (qi[:, 1] >= 0) & (qi[:, 1] < H * SS)
        np.maximum.at(lay, (qi[ok, 1], qi[ok, 0]), br[ok])
        lay = cv2.dilate(lay, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * SS + 1, 2 * SS + 1)))
        img += lay[..., None] * WALL * 0.85 + cv2.GaussianBlur(lay, (0, 0), 5 * SS)[..., None] * WALL * 0.9
    # 지금 이 바퀴의 광선(아주 옅게)과 발
    pp = to_px(p[None], z, c)[0]
    rays = np.zeros((H * SS, W * SS), np.float32)
    for q2 in to_px(P[::6], z, c): cv2.line(rays, tuple(np.round(pp).astype(int)), tuple(np.round(q2).astype(int)), 0.05, 1, cv2.LINE_AA)
    img += rays[..., None] * WALL
    fp = to_px(P[kind == 2], z, c)
    if len(fp):
        lf = np.zeros((H * SS, W * SS), np.float32)
        for q2 in fp: cv2.circle(lf, tuple(np.round(q2).astype(int)), 2 * SS, 1.0, -1, cv2.LINE_AA)
        img += lf[..., None] * FOOT * 0.9 + cv2.GaussianBlur(lf, (0, 0), 9 * SS)[..., None] * FOOT * 1.4
    # 지나온 길
    if len(trail) > 1:
        tr = np.zeros((H * SS, W * SS), np.float32)
        cv2.polylines(tr, [np.round(to_px(np.array(trail), z, c)).astype(np.int32)], False, 1.0, SS, cv2.LINE_AA)
        img += tr[..., None] * LED * 0.28
    # 청소기 본체 + LED(숨 쉬듯)
    r = 0.17 * z
    body = np.zeros((H * SS, W * SS), np.float32); cv2.circle(body, tuple(np.round(pp).astype(int)), int(r), 1.0, -1, cv2.LINE_AA)
    img = img * (1 - body[..., None] * 0.85) + body[..., None] * np.array([0.16, 0.15, 0.15])
    ring = np.zeros_like(body); cv2.circle(ring, tuple(np.round(pp).astype(int)), int(r), 1.0, max(1, SS), cv2.LINE_AA)
    img += ring[..., None] * WALL * 0.6
    dv = (pos(t + 0.05) - p); dv = dv / (np.linalg.norm(dv) + 1e-9)
    lp = to_px((p + dv * 0.1)[None], z, c)[0]
    led = np.zeros_like(body); cv2.circle(led, tuple(np.round(lp).astype(int)), max(2, int(0.025 * z)), 1.0, -1, cv2.LINE_AA)
    lb = 0.75 + 0.25 * math.sin(t * 3.2)
    img += led[..., None] * LED * lb + cv2.GaussianBlur(led, (0, 0), 6 * SS)[..., None] * LED * 2.5 * lb
    # 마무리: 줄이기, 톤, 비네트, 그레인
    img = cv2.resize(img, (W, H), interpolation=cv2.INTER_AREA)
    img = 1 - np.exp(-img * 1.25)
    yy, xx = np.mgrid[0:H, 0:W]; vg = 1 - 0.35 * (((xx / W - 0.5) ** 2 + (yy / H - 0.5) ** 2) * 2.2)
    img *= vg[..., None]
    img += rng.normal(0, 0.012, img.shape)
    a = np.clip(img * min(1.0, (t + 0.05) / 0.6), 0, 1)
    ff.stdin.write((a * 255 + 0.5).astype(np.uint8).tobytes())
    if k in (int(nf * 0.25), int(nf * 0.6), nf - 1): cv2.imwrite(OUT.replace('.mp4', f'_f{k:03d}.png'), (a * 255).astype(np.uint8))
ff.stdin.close(); ff.wait(); print('done', OUT)
