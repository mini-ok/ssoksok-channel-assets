"""〈점〉 표현 시험 v2: 떨리는 손 — 손은 화면에 안 보이고 붓과 그림자로만.
v1(위에서 본 팔 전체)은 팔이 납작한 덩어리로 보이고, 결정적으로 주먹이 눈자리를 가렸다 → 버림.
v2 원칙: 붓은 화가 쪽으로 30° 기울어 있어 근접 화면에서는 손이 화면 아래 밖에 있다.
  - 높이 = 붓끝과 붓끝 그림자 사이 거리 (내려갈수록 둘이 만난다)
  - 떨림 = 붓끝 흔들림 + 붓대 그림자(긴 선)의 흔들림(위쪽일수록 크게) + 손 그림자의 흐린 덩어리
컷 A(0–5.4s) 눈 근접: 두 번 내려가다 두 번 흠칫 미끄러져 눈 옆에 자국.
컷 B(5.4–8.6s) 구석 근접: 물러나는 붓이 지나가고, 붓끝 방울이 떨어진다(방울과 방울 그림자가 만나는 순간 착지).
"""
import sys, os, math, subprocess
HERE = os.path.dirname(os.path.abspath(__file__)); JE = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(JE, 'engine'))
os.environ.setdefault('JEOM_RES', '0.5')
import numpy as np, cv2
from paper import View
from brush import Stroke, Wash, render_strokes
from look import INK_ABS, light, film, letterbox
sys.path.insert(0, JE)
import animatic as A
import inkmm

from scale import S, W, H, SUF
F32 = np.float32
E = (300.0, 112.0); CORNER = (38.0, 392.0)          # timeline WATERS[0]과 같은 자리
S_DIR = np.array((0.6, -0.8)); K = 0.45          # 그림자 방향(오른쪽 위)과 높이 1mm당 밀림
D_XY = np.array((0.42, 1.0)); D_XY /= np.hypot(*D_XY)   # 붓이 기운 방향(화가 쪽)
SHAFT_H, SHAFT_V = 90.0, 156.0                   # 붓 길이 180mm, 수직에서 30° 기울기

def ease(u): return u * u * (3 - 2 * u)
def lerp(a, b, u): return (a[0] + (b[0] - a[0]) * u, a[1] + (b[1] - a[1]) * u)

# ---------------------------------------------------------------- 판(종이+용)
PA = A.Plate('eyecu', 296, 140, 210, W / 170 * 1.05)
PB = A.plate_for('C2')                           # 'corner' 판
VA = View(296, 136, 170, W, H)
VB = View(56, 382, 150, W, H)

def tremor_dot(x, y, seed, size, ang):
    """흠칫 미끄러진 붓끝: 짧게 긁힌 획 + 떨린 꼬리."""
    r = np.random.default_rng(seed)
    pts = [(x, y)]
    for k in range(5):
        pts.append((x + math.cos(ang) * k * 1.3 + r.normal(0, 0.7), y + math.sin(ang) * k * 1.3 + r.normal(0, 0.7)))
    return Stroke(pts, size, load=1.5, dry=0.35, seed=seed, head='press', tail='taper', wet=0.6, name='tremor')

TAPS = [(2.0, (279, 133), 11, 2.6), (3.85, (318, 127), 12, 0.5)]

def setup(view, plate):
    X, Y = view.grid_mm()
    rgb, fib, drg = plate.sample(X, Y)
    off = ((X < 0) | (X > 640) | (Y < 0) | (Y > 420)).astype(F32)
    return dict(v=view, X=X, Y=Y, rgb=rgb, fib=fib, drg=drg, off=off)

SA = setup(VA, PA); SB = setup(VB, PB)
SA['taps'] = [render_strokes(VA, [tremor_dot(p[0], p[1], sd, 3.2, an)], SA['fib']) for (_, p, sd, an) in TAPS]
FLOOR = np.array((0.16, 0.10, 0.06), F32)

# ---------------------------------------------------------------- 움직임
def tremor(t, amp, seed):
    """생리적 떨림 4–7Hz를 투스로 샘플 + 약간의 불규칙."""
    q = math.floor(t * 12) / 12
    r = np.random.default_rng(int(q * 12) * 31 + seed)
    return np.array((amp * (0.6 * math.sin(2 * math.pi * 5.3 * q + seed) + 0.4 * r.normal()),
                     amp * (0.6 * math.sin(2 * math.pi * 6.1 * q + 1.7 * seed) + 0.4 * r.normal())))

def state_A(t):
    hover = (E[0] + 1.5, E[1] + 5)
    T1, T2 = TAPS[0][1], TAPS[1][1]
    if t < 0.8:
        u = ease(t / 0.8); p = lerp((338, 205), hover, u); h = 40 - 14 * u; tr = 0.5
    elif t < 2.0:
        u = (t - 0.8) / 1.2; p = hover; h = 26 - 23 * ease(u); tr = 0.5 + 2.4 * u
    elif t < 2.17:
        p = T1; h = 0.0; tr = 0.2
    elif t < 2.9:
        u = ease((t - 2.17) / 0.73); p = lerp(T1, hover, u); h = 24 * min(1, u * 1.6); tr = 1.6
    elif t < 3.85:
        u = (t - 2.9) / 0.95; p = hover; h = 24 - 21 * ease(u); tr = 0.9 + 3.0 * u
    elif t < 4.02:
        p = T2; h = 0.0; tr = 0.2
    elif t < 4.8:
        u = ease((t - 4.02) / 0.78); p = lerp(T2, (314, 118), u); h = 30 * u; tr = 2.4     # 들어 올린 채로 떨림
    else:
        u = ease(min(1, (t - 4.8) / 0.6)); p = lerp((314, 118), (250, 215), u); h = 30 + 6 * u; tr = 1.4
    return np.array(p), h, tr

DROP_T = 6.80; FALL = 0.22          # 멈췄던 붓이 다시 움직이는 순간 털려 떨어짐
def state_B(t):
    lt = t - 5.4
    a, b = (150, 300), (-40, 470)                 # 위 오른쪽에서 들어와 왼쪽 아래로 빠짐
    over = (CORNER[0] + 1, CORNER[1])
    if lt < 1.0:
        u = ease(lt / 1.0); p = lerp(a, over, u)
    elif lt < 1.35:
        p = over
    else:
        u = ease(min(1, (lt - 1.35) / 1.0)); p = lerp(over, b, u)
    return np.array(p), 24.0, 1.2

# ---------------------------------------------------------------- 그림자
def shadow_layers(S, tip, h, top_tr):
    """붓털·붓대·손·소매의 그림자를 높이에 비례해 밀고, 높을수록 흐리게(반그림자)."""
    v = S['v']; ppm = v.ppm
    def sp(p, z): q = np.asarray(p, float) + S_DIR * K * z; return v.to_px(q[0], q[1])
    top = tip + D_XY * SHAFT_H + top_tr; ztop = h + SHAFT_V
    out = np.zeros((H, W), F32)
    # 붓털 + 붓대: 선을 몇 토막으로 나눠 토막마다 흐림을 키움
    n = 8
    for i in range(n):
        u0, u1 = i / n, (i + 1) / n
        p0 = tip + (top - tip) * u0; p1 = tip + (top - tip) * u1
        z0 = h + SHAFT_V * u0; z1 = h + SHAFT_V * u1
        m = np.zeros((H, W), F32)
        a = sp(p0, z0); b = sp(p1, z1)
        wid = (2.4 if i == 0 else 5.5 + 2.0 * u0) * ppm
        cv2.line(m, (int(a[0]), int(a[1])), (int(b[0]), int(b[1])), 1.0, max(1, int(wid)), cv2.LINE_AA)
        sig = max(0.6, (0.25 + 0.035 * (z0 + z1) / 2) * ppm)
        out = np.maximum(out, cv2.GaussianBlur(m, (0, 0), sig))
    # 손(붓대 2/3 지점)과 소매
    for (frac, rx, ry, extra) in ((0.66, 26, 20, 0), (0.95, 46, 34, 40)):
        c = tip + (top - tip) * frac; z = h + SHAFT_V * frac + extra
        cx, cy = sp(c, z)
        m = np.zeros((H, W), F32)
        ang = math.degrees(math.atan2(D_XY[1], D_XY[0]))
        cv2.ellipse(m, (int(cx), int(cy)), (int(rx * ppm), int(ry * ppm)), ang, 0, 360, 1.0, -1, cv2.LINE_AA)
        out = np.maximum(out, cv2.GaussianBlur(m, (0, 0), (0.035 * z) * ppm) * 0.9)
    return out

# ---------------------------------------------------------------- 붓(실물)
def draw_brush(img, S, tip, h, top_tr, lampfall, bead=True):
    v = S['v']; ppm = v.ppm
    top = tip + D_XY * SHAFT_H + top_tr
    a = np.array(v.to_px(*tip)); b = np.array(v.to_px(*top))
    d = b - a; L = np.hypot(*d); d = d / L; n = np.array((-d[1], d[0]))
    yy, xx = np.mgrid[0:H, 0:W].astype(F32)
    u = (xx - a[0]) * d[0] + (yy - a[1]) * d[1]               # 붓끝에서 위로 px
    w = (xx - a[0]) * n[0] + (yy - a[1]) * n[1]
    umm = u / ppm
    # 반폭(mm): 붓털 0–17mm(배가 부른 송곳), 쇠테 17–22, 붓대 22–(위로 갈수록 카메라에 가까워 굵어짐)
    hw = np.where(umm < 17, 1.95 * np.clip(umm / 12, 0, 1) ** 0.6 * (1 - 0.15 * np.clip((umm - 12) / 5, 0, 1)),
         np.where(umm < 22, 2.3, 2.6 + 0.012 * (umm - 22)))
    hw = hw * ppm
    vv = w / np.maximum(hw, 1e-3)
    m = ((umm >= -0.2) & (np.abs(vv) <= 1)).astype(F32)
    m = cv2.GaussianBlur(m, (0, 0), 0.6)
    L_DIR = np.array((-0.6, 0.8))                              # 화면에서 등잔 쪽(왼쪽 아래)
    sgn = 1.0 if (n @ L_DIR) > 0 else -1.0
    lit = np.clip(0.5 + 0.5 * vv * sgn, 0, 1)
    cyl = np.sqrt(np.clip(1 - vv * vv, 0, 1))
    shade = 0.25 + 0.75 * (0.35 * cyl + 0.65 * lit)
    bamboo = np.array((0.70, 0.54, 0.30), F32)
    col = bamboo[None, None, :] * shade[..., None]
    nodes = np.exp(-((umm - 22) % 44 - 40) ** 2 / 1.2)          # 대나무 마디
    col = col * (1 - 0.35 * nodes[..., None])
    spec = np.exp(-((vv * sgn - 0.55) / 0.12) ** 2)
    col = col + (spec * 0.18)[..., None]
    fer = ((umm >= 17) & (umm < 22)).astype(F32)               # 쇠테(검은 옻칠)
    col = col * (1 - fer[..., None]) + fer[..., None] * (np.array((0.10, 0.06, 0.04), F32) * shade[..., None] + spec[..., None] * 0.35)
    hair = (umm < 17).astype(F32)                              # 먹 먹은 붓털: 검고 젖은 빛
    hcol = np.array((0.025, 0.022, 0.025), F32) * (0.6 + 0.4 * lit[..., None]) + (np.exp(-((vv * sgn - 0.4) / 0.15) ** 2) * 0.10)[..., None]
    col = col * (1 - hair[..., None]) + hcol * hair[..., None]
    img = img * (1 - m[..., None]) + col * lampfall[..., None] * m[..., None]
    if bead:                                                   # 붓끝에 맺힌 먹방울
        bx, by = a + d * 0.7 * ppm
        cv2.ellipse(img, (int(bx), int(by)), (max(2, int(0.8 * ppm)), max(2, int(0.9 * ppm))), 0, 0, 360, (0.02, 0.02, 0.025), -1, cv2.LINE_AA)
        hx, hy = bx - 0.35 * ppm, by + 0.35 * ppm                 # 등잔 쪽 반짝임
        g = np.exp(-((xx - hx) ** 2 + (yy - hy) ** 2) / (0.22 * ppm) ** 2)
        img = img + (g * 0.22)[..., None] * np.array((1.0, 0.8, 0.55), F32)
    return img

# ---------------------------------------------------------------- 프레임
yy, xx = np.mgrid[0:H, 0:W].astype(F32)
LAMPFALL = np.clip(1.18 - 0.55 * (((xx + 260) / W) ** 2 + ((yy - H * 1.25) / H) ** 2) ** 0.5, 0.42, 1.1)

def base(S, dens):
    img = S['rgb'] * np.exp(-dens[..., None] * INK_ABS)
    return img * (1 - S['off'][..., None]) + FLOOR * S['off'][..., None]

def frame(t):
    if t < 5.4:
        S = SA; tip, h, tr = state_A(t)
        jt = tremor(t, tr * 0.6, 3); top_tr = tremor(t, tr * 1.0, 9)      # 떨림 크기: 붓끝 평균 1–2mm/장
        tip = tip + jt if h > 0.05 else tip
        dens = S['drg'].copy()
        for (tt, p, sd, an), dd in zip(TAPS, S['taps']):
            if t >= tt:
                dens = dens + dd
        img = base(S, dens)
        img = img * (1 - 0.5 * shadow_layers(S, tip, h, top_tr)[..., None])
        img = light(img, 'lamp') * LAMPFALL[..., None]
        img = draw_brush(img, S, tip, h, top_tr, LAMPFALL, bead=True)
    else:
        S = SB; tip, h, tr = state_B(t)
        jt = tremor(t, tr, 5); top_tr = tremor(t, tr * 1.6, 13)
        tip = tip + jt
        dens = S['drg'].copy()
        land = DROP_T + FALL
        if t >= land:
            D = A.dot(); th = 13.0 + (t - land)                     # 본편 번짐 엔진: WATERS[0]/STAGES[0]
            dd = inkmm.sample(D.density(th), S['v'], S['X'], S['Y'])
            halo = cv2.GaussianBlur(dd, (0, 0), max(0.6, 0.3 * S['v'].ppm))
            dd = dd + np.clip(halo - dd, 0, 0.6) * np.clip(S['fib'] * 1.5 - 0.2, 0, 1.3) * 1.4
            dens = dens + dd
        img = base(S, dens)
        img = img * (1 - 0.5 * shadow_layers(S, tip, h, top_tr)[..., None])
        # 떨어지는 방울: 방울은 제자리, 그림자가 방울로 모여든다
        if DROP_T <= t < land:
            u = (t - DROP_T) / FALL; z = h * (1 - u * u)
            v = S['v']; ppm = v.ppm
            sx, sy = v.to_px(*(np.array(CORNER) + S_DIR * K * z))
            sm = np.zeros((H, W), F32); cv2.circle(sm, (int(sx), int(sy)), int(1.4 * ppm), 1.0, -1, cv2.LINE_AA)
            img = img * (1 - 0.45 * cv2.GaussianBlur(sm, (0, 0), (0.3 + 0.03 * z) * ppm)[..., None])
        img = light(img, 'lamp') * LAMPFALL[..., None]
        if t < 5.4 + 2.6:
            img = draw_brush(img, S, tip, h, top_tr, LAMPFALL, bead=(t < DROP_T))
        if DROP_T <= t < land:
            u = (t - DROP_T) / FALL; v = S['v']; ppm = v.ppm
            bx, by = v.to_px(*CORNER); r = 0.85 * (1 - 0.15 * u)
            cv2.ellipse(img, (int(bx), int(by)), (max(2, int(r * ppm)), max(2, int(r * 1.15 * ppm))), 0, 0, 360, (0.02, 0.02, 0.025), -1, cv2.LINE_AA)
    img = film(img, t, H=H, W=W, vig=0.22, grain=0.012, weave=0.35)
    img = letterbox(img)
    return (np.clip(img, 0, 1)[..., ::-1] * 255 + 0.5).astype(np.uint8)

if __name__ == '__main__':
    out = os.path.join(JE, 'cache', 'hand_test2' + SUF); os.makedirs(out, exist_ok=True)
    N = int(8.6 * 12); FR = []
    for k in range(N):
        f = frame(k / 12); FR.append(f)
        cv2.imwrite(os.path.join(out, f'h{k:04d}.png'), f)
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-framerate', '12', '-i', os.path.join(out, 'h%04d.png'),
                    '-vf', 'fps=24', '-c:v', 'libx264', '-crf', '18', '-pix_fmt', 'yuv420p', os.path.join(JE, 'cache', 'hand_test2.mp4')])
    pick = (8, 22, 24, 32, 45, 47, 56, 72, 80, 82, 86, 102)
    rows = [np.hstack([FR[i] for i in pick[r * 3:(r + 1) * 3]]) for r in range(4)]
    cv2.imwrite(os.path.join(JE, 'cache', 'hand_test2_sheet.jpg'), cv2.resize(np.vstack(rows), (1440, 1080)), [cv2.IMWRITE_JPEG_QUALITY, 90])
    print('ok', N)
