"""〈점〉 표현 시험: 떨리는 손(7.5초, 960×540, 투스).
위에서 본 종이 한 화면에 눈자리와 구석이 함께. 등잔은 왼쪽 아래 낮은 곳 → 손 그림자가 오른쪽 위로 길게 드리워진다.
붓끝이 내려갈수록 그림자가 붓끝으로 모인다(높이 = 그림자 거리). 떨림은 손 위치의 고주파 흔들림(가까울수록 커짐).
여백 오른쪽 아래에는 미리 찍힌 '떨린 점'(실패한 연습 점) 셋.
"""
import sys, os, math, subprocess
HERE = os.path.dirname(os.path.abspath(__file__)); JE = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(JE, 'engine'))
import numpy as np, cv2
from paper import View
from brush import Stroke, Wash, render_strokes
from look import INK_ABS, light, film, letterbox
sys.path.insert(0, JE)
os.environ.setdefault('JEOM_RES', '0.5')
import animatic as A

W, H = 960, 540
F32 = np.float32
E = (300.0, 112.0); CORNER = (38.0, 392.0)
view = View(250, 238, 620, W, H)
X, Y = view.grid_mm()
plate = A.plate_for('C5')          # 종이 + 용 (whole 판)
rgb0, fib0, drg0 = plate.sample(X, Y)

# 실패한 연습 점(떨린 점): 짧게 눌렀다 떨며 뗀 자국 — 동그랗지 않고 지그재그 꼬리
def tremor_dot(x, y, seed, size=4.0):
    r = np.random.default_rng(seed)
    pts = [(x, y)]
    for k in range(5):
        pts.append((x + r.normal(0, 1.2) + k * 0.9, y + r.normal(0, 1.2) + k * 0.6))
    return Stroke(pts, size, load=1.4, dry=0.4, seed=seed, head='press', tail='taper', wet=0.5, name='tremor')
TAPS = [(2.25, (276, 160), 11), (4.25, (250, 206), 12)]      # (시각, 위치, 시드): 흠칫 미끄러진 붓끝이 닿은 자국
tap_d = [render_strokes(view, [tremor_dot(p[0], p[1], sd, 6.0)], fib0) for (_, p, sd) in TAPS]
offpaper = ((X < 0) | (X > 640) | (Y < 0) | (Y > 420)).astype(F32)
floor = np.zeros((H, W, 3), F32) + np.array((0.20, 0.13, 0.08), F32)

def ramp(t, a, b): return float(np.clip((t - a) / (b - a), 0, 1))
def ease(u): return u * u * (3 - 2 * u)

def hand_state(t):
    """손끝(붓끝) 위치(mm), 높이(mm), 떨림 세기. 두 번 시도 → 두 번 다 흠칫 미끄러져 엉뚱한 곳에 닿음 → 물러나다 구석 위에서 방울이 떨어짐."""
    start = (330, 520); hover = (E[0] + 2, E[1] + 6); corner = (CORNER[0] + 4, CORNER[1] - 6); exitp = (-80, 520)
    T1, T2 = TAPS[0][1], TAPS[1][1]
    def lerp(a, b, u): return (a[0] + (b[0] - a[0]) * u, a[1] + (b[1] - a[1]) * u)
    if t < 1.2:
        u = ease(t / 1.2); p = lerp(start, hover, u); h = 40 - 15 * u; tr = 0.5
    elif t < 2.25:
        u = (t - 1.2) / 1.05; p = hover; h = 25 - 20 * ease(min(1, u)); tr = 0.6 + 2.2 * u
    elif t < 2.42:                                       # 흠칫: 붓끝이 미끄러져 닿음
        p = T1; h = 0.5; tr = 0.3
    elif t < 3.3:
        u = ease((t - 2.42) / 0.88); p = lerp(T1, hover, u); h = 0.5 + 24 * min(1, u * 2); tr = 1.4
    elif t < 4.25:
        u = (t - 3.3) / 0.95; p = hover; h = 25 - 20 * ease(min(1, u)); tr = 0.8 + 2.8 * u
    elif t < 4.42:
        p = T2; h = 0.5; tr = 0.3
    elif t < 5.2:
        u = ease((t - 4.42) / 0.78); p = T2; h = 0.5 + 28 * u; tr = 2.2      # 들어 올린 채 떨림(낙담)
    elif t < 6.6:
        u = ease((t - 5.2) / 1.4); p = lerp(T2, corner, u); h = 28 - 6 * u; tr = 1.3
    elif t < 7.6:
        p = corner; h = 22; tr = 0.9
    else:
        u = ease(min(1, (t - 7.6) / 1.2)); p = lerp(corner, exitp, u); h = 22 + 10 * u; tr = 0.7
    r = np.random.default_rng(int(t * 12) * 13 + 7)
    return (p[0] + r.normal(0, tr), p[1] + r.normal(0, tr)), h, tr

DROP_T = 6.25                       # 구석 위를 지날 때 방울이 떨어짐

def _curve(pts, n=60):
    pts = np.array(pts, float); out = []
    P = np.vstack([pts[:1], pts, pts[-1:]])
    for i in range(1, len(P) - 2):
        p0, p1, p2, p3 = P[i - 1], P[i], P[i + 1], P[i + 2]
        for u in np.linspace(0, 1, n // (len(P) - 3), endpoint=False):
            out.append(0.5 * ((2 * p1) + (-p0 + p2) * u + (2 * p0 - 5 * p1 + 4 * p2 - p3) * u * u + (-p0 + 3 * p1 - 3 * p2 + p3) * u ** 3))
    out.append(P[-2]); return np.array(out)

def arm_parts(tip, h):
    """mm 좌표 다각형들: 붓대, 손(주먹+엄지), 소매(넓은 도포 소매, 늘어진 단). 붓은 화가 쪽(아래)으로 약간 기울어 손은 붓끝보다 아래에 있다."""
    tx, ty = tip
    top = np.array((tx + 10, ty + 34))                       # 붓대 위끝(손 속)
    hand = top + (4, 6)
    d = np.array((0.42, 1.0)); d /= np.hypot(*d); n = np.array((-d[1], d[0]))
    wrist = hand + d * 22
    hem = wrist + d * 26
    # 도포 소매: 손목에서 넓게 퍼지며 화면 아래로 — 오른쪽(바깥)으로 처진 단
    sl = [wrist + n * 12, hem + n * 36, hem + n * 44 + d * 60, hem + n * 30 + d * 220,
          hem - n * 46 + d * 220, hem - n * 40 + d * 40, hem - n * 30 + d * 4, wrist - n * 12]
    fist = [hand + n * 13 - d * 6, hand + n * 15 + d * 8, hand + n * 6 + d * 18, hand - n * 9 + d * 17,
            hand - n * 15 + d * 4, hand - n * 12 - d * 9, hand - n * 2 - d * 13]
    thumb = [hand + n * 11 - d * 4, hand + n * 4 - d * 15, hand - n * 1 - d * 17, hand + n * 2 - d * 9]
    return dict(shaft=(np.array((tx, ty)), top), fist=fist, thumb=thumb, sleeve=sl, hand=hand, d=d, n=n)

def arm_mask(tip, h, shadow=False, part=None):
    A_ = arm_parts(tip, h)
    off = np.array((0.55, -0.85)) * h if shadow else np.zeros(2)
    m = np.zeros((H, W), F32)
    def P(pts, lift):
        pts = np.asarray(pts, float) + off * lift
        px, py = view.to_px(pts[:, 0], pts[:, 1]); return np.stack([px, py], 1).astype(np.int32)
    if part in (None, 'shaft'):
        a, b = A_['shaft']
        q = P([a, b], 1.0); q[1] = P([b], 1.7)[0]
        cv2.line(m, tuple(q[0]), tuple(q[1]), 1.0, max(2, int(2.6 * view.ppm)), cv2.LINE_AA)
    if part in (None, 'sleeve'):
        c = _curve(A_['sleeve'] + [A_['sleeve'][0]], 120)
        cv2.fillPoly(m, [P(c, 2.3)], 1.0, cv2.LINE_AA)
    if part in (None, 'fist'):
        for poly in (A_['fist'], A_['thumb']):
            c = _curve(list(poly) + [poly[0]], 60)
            cv2.fillPoly(m, [P(c, 1.8)], 1.0, cv2.LINE_AA)
    return m

yy, xx = np.mgrid[0:H, 0:W].astype(F32)
cloth = cv2.GaussianBlur(np.random.default_rng(41).standard_normal((H, W)).astype(F32), (0, 0), 9); cloth /= cloth.std()

def shade_arm(img, tip, h, lampfall):
    """실루엣 위주: 거의 검은 옷감 + 등잔 쪽(왼쪽 아래) 테두리빛. 손은 어두운 살빛, 붓대는 대나무빛 + 먹 붓털."""
    sl = arm_mask(tip, h, part='sleeve'); fi = arm_mask(tip, h, part='fist'); sh = arm_mask(tip, h, part='shaft')
    def rim(m, k=4):
        shifted = np.roll(np.roll(m, k, 1), -k, 0)               # 빛 반대쪽으로 민 마스크와의 차 = 등잔 쪽 테두리
        return np.clip(m - cv2.GaussianBlur(shifted, (0, 0), 1.6), 0, 1) * m
    out = img.copy()
    # 소매
    base = np.array((0.055, 0.050, 0.060), F32)
    fold = 0.75 + 0.25 * np.sin((xx * 0.55 - yy * 0.25) / 9.0 + cloth * 3.0)
    col = base * fold[..., None] + rim(sl, 5)[..., None] * np.array((0.62, 0.38, 0.15), F32)
    a = cv2.GaussianBlur(sl, (0, 0), 0.7)[..., None]
    out = out * (1 - a) + col * a * lampfall[..., None]
    # 손
    col = np.array((0.30, 0.20, 0.14), F32) * (0.85 + 0.15 * cloth[..., None]) + rim(fi, 3)[..., None] * np.array((0.75, 0.48, 0.25), F32)
    # 손가락 사이 골(어둡게)
    A_ = arm_parts(tip, h); g = np.zeros((H, W), F32)
    for kk in (-6, 0, 6):
        p0 = A_['hand'] + A_['n'] * kk + A_['d'] * 4; p1 = A_['hand'] + A_['n'] * kk * 1.2 + A_['d'] * 16
        q0 = view.to_px(*p0); q1 = view.to_px(*p1)
        cv2.line(g, (int(q0[0]), int(q0[1])), (int(q1[0]), int(q1[1])), 1.0, 1, cv2.LINE_AA)
    col = col * (1 - 0.6 * cv2.GaussianBlur(g, (0, 0), 0.6)[..., None])
    a = cv2.GaussianBlur(fi, (0, 0), 0.7)[..., None]
    out = out * (1 - a) + col * a * lampfall[..., None]
    # 붓대 + 붓털
    col = np.array((0.55, 0.42, 0.24), F32) + rim(sh, 1)[..., None] * 0.3
    a = (sh * (1 - fi))[..., None]
    out = out * (1 - a) + col * a * lampfall[..., None]
    tx, ty = tip; dd = A_['shaft'][1] - A_['shaft'][0]; dd = dd / np.hypot(*dd); nn = np.array((-dd[1], dd[0]))
    hair = [np.array((tx, ty)), np.array((tx, ty)) + dd * 14 + nn * 2.4, np.array((tx, ty)) + dd * 16, np.array((tx, ty)) + dd * 14 - nn * 2.4]
    q = np.stack(view.to_px(np.array([p[0] for p in hair]), np.array([p[1] for p in hair])), 1).astype(np.int32)
    hm = np.zeros((H, W), F32); cv2.fillPoly(hm, [q], 1.0, cv2.LINE_AA)
    out = out * (1 - hm[..., None]) + hm[..., None] * np.array((0.03, 0.03, 0.035), F32)
    return out

FR = []
for k in range(int(9.0 * 12)):
    t = k / 12
    tip, h, tr = hand_state(t)
    dens = drg0.copy()
    for (tt, p, sd), dd in zip(TAPS, tap_d):
        if t >= tt:
            dens = dens + dd
    # 떨어진 먹: 구석에 방울 → 번짐(간단한 원형 번짐 + 섬유 가장자리)
    if t >= DROP_T + 0.17:
        u = 1 - math.exp(-(t - DROP_T - 0.17) / 0.25)
        R = 2.5 + 4.0 * u
        wb = Wash([(CORNER[0], CORNER[1], R), (CORNER[0] + 1.0, CORNER[1] - 0.6, R * 0.8)], load=1.6, soft=0.25, seed=9, rim=0.4)
        tmp = np.zeros((H, W), F32); wb.render(view, tmp, fib0); dens = dens + tmp
    img = rgb0 * np.exp(-dens[..., None] * INK_ABS)
    img = img * (1 - offpaper[..., None]) + floor * offpaper[..., None]
    # 손 그림자(부드럽게, 높이가 높을수록 흐림)
    sh = arm_mask(tip, h, shadow=True)
    sh = cv2.GaussianBlur(sh, (0, 0), 1.5 + h * 0.18 * view.ppm / 3)
    img = img * (1 - 0.55 * sh[..., None])
    # 등잔빛
    img = light(img, 'lamp')
    lampfall = np.clip(1.15 - 0.55 * (((xx + 200) / W) ** 2 + ((yy - H * 1.2) / H) ** 2) ** 0.5, 0.45, 1.1)
    img = img * lampfall[..., None]
    img = shade_arm(img, tip, h, lampfall)
    # 붓끝의 먹 방울(떨어지기 전) / 떨어지는 방울
    px, py = view.to_px(*tip)
    if t < DROP_T:
        cv2.circle(img, (int(px), int(py + 2)), max(2, int(1.6 * view.ppm)), (0.03, 0.03, 0.04), -1)
    elif t < DROP_T + 0.17:
        cx, cy = view.to_px(*CORNER)
        u = (t - DROP_T) / 0.17; px2, py2 = view.to_px(CORNER[0] + 6 * (1 - u), CORNER[1] - 8 * (1 - u))
        cv2.ellipse(img, (int(px2), int(py2)), (max(2, int(1.3 * view.ppm)), max(2, int(1.9 * view.ppm))), 30, 0, 360, (0.04, 0.04, 0.05), -1, cv2.LINE_AA)
    img = film(img, t, H=H, W=W, vig=0.22, grain=0.012, weave=0.35)
    img = letterbox(img)
    FR.append((np.clip(img, 0, 1)[..., ::-1] * 255 + 0.5).astype(np.uint8))

out = os.path.join(JE, 'cache', 'hand_test'); os.makedirs(out, exist_ok=True)
for i, f in enumerate(FR):
    cv2.imwrite(os.path.join(out, f'h{i:04d}.png'), f)
subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-framerate', '12', '-i', os.path.join(out, 'h%04d.png'),
                '-vf', 'fps=24', '-c:v', 'libx264', '-crf', '20', '-pix_fmt', 'yuv420p', os.path.join(JE, 'cache', 'hand_test.mp4')])
sheet = np.vstack([np.hstack([FR[i] for i in (10, 25, 29, 50)]), np.hstack([FR[i] for i in (58, 72, 77, 100)])])
cv2.imwrite(os.path.join(JE, 'cache', 'hand_test_sheet.png'), cv2.resize(sheet, (1920, 540)))
print('ok')
