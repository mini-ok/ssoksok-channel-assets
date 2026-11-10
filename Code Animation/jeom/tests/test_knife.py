"""〈점〉 표현 시험: 칼로 귀퉁이를 자르다 멈춤(6초, 960×540, 투스).
손은 화면 밖(붓 시험과 같은 원칙). 자는 대나무, 칼은 짧은 날 + 나무 손잡이(화가 쪽 = 화면 아래로 빠짐).
떨림 때문에 칼집 선이 자 가장자리에서 조금씩 흔들리다, 2/3쯤에서 날이 자를 벗어나 비뚤게 휜다 → 멈춘다 → 칼을 자 위에 얹는다.
칼집 = 종이가 갈라진 틈(어두운 선 + 한쪽 잘린 면의 밝은 테). 구석의 점(이미 떨어진 먹)은 잘려 나갈 조각 위에 있다.
"""
import sys, os, math, subprocess
HERE = os.path.dirname(os.path.abspath(__file__)); JE = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(JE, 'engine'))
os.environ.setdefault('JEOM_RES', '0.25')
import numpy as np, cv2
from paper import View
from look import INK_ABS, light, film, letterbox
sys.path.insert(0, JE)
import animatic as A
import inkmm

F32 = np.float32
from scale import S, W, H, SUF
FPS = 12; DUR = 6.0
V = View(62, 372, 175, W, H)
X, Y = V.grid_mm()
P0 = np.array((0.0, 318.0)); U = np.array((1.0, 1.0)) / math.sqrt(2); NRM = np.array((1.0, -1.0)) / math.sqrt(2)
S_END = 96.0                                            # 2/3 지점에서 멈춤(전체 144mm)
plate = A.plate_for('C2')
RGB, FIB, DRG = plate.sample(X, Y)
OFF = ((X < 0) | (X > 640) | (Y < 0) | (Y > 420)).astype(F32)
D = A.dot()
DOT = inkmm.sample(D.density(15.5), V, X, Y)           # 이미 떨어져 번진 점(WATERS[0])
_h = cv2.GaussianBlur(DOT, (0, 0), max(0.6, 0.3 * V.ppm))
DOT = DOT + np.clip(_h - DOT, 0, 0.6) * np.clip(FIB * 1.5 - 0.2, 0, 1.3) * 1.4

def ease(u): return u * u * (3 - 2 * u)
def ramp(t, a, b): return float(np.clip((t - a) / (b - a), 0, 1))

def tremor(t, amp, seed):
    q = math.floor(t * FPS) / FPS
    r = np.random.default_rng(int(q * FPS) * 31 + seed)
    return amp * (0.6 * math.sin(2 * math.pi * 5.3 * q + seed) + 0.4 * r.normal())

def blade_state(t):
    """칼끝 위치(자 기준 s, 법선 n mm), 높이 h(mm), 각도 흔들림."""
    if t < 0.7:                                          # 위에서 내려와 종이 가장자리에 댐
        u = ease(t / 0.7); s = -6 + 6 * u; n = -0.5; h = 18 * (1 - u)
    elif t < 3.5:                                        # 자를 따라 긋는다(점점 떨림이 커짐)
        u = (t - 0.7) / 2.8; s = S_END * 0.92 * (u ** 1.08); h = 0.0
        n = -0.4 - 0.15 * u + tremor(t, 0.25 + 0.9 * u, 3) * 0.6
    elif t < 3.85:                                       # 날이 자를 벗어나 비뚤게 휜다
        u = ease((t - 3.5) / 0.35); s = S_END * 0.92 + S_END * 0.08 * u; n = -0.9 - 3.2 * u * u; h = 0.0
    elif t < 4.7:                                        # 멈춰 든 채 떨림
        u = ease((t - 3.85) / 0.85); s = S_END + 2 * u; n = -4.1 - 2 * u; h = 9 * u
    else:                                                # 칼을 자 위에 얹는다
        u = ease(min(1.0, (t - 4.7) / 0.8)); s = S_END + 2 + 6 * u; n = -6.1 + 18 * u; h = 9 * (1 - u) + 1.5 * u
    tr = 0.0 if (0.7 <= t < 3.85) else tremor(t, 0.8, 5)
    return s, n + tr, h

CUT = []                                                 # 칼집 자취(mm)
def cut_layers(tip):
    """칼집: 종이가 실제로 갈라져 틈이 벌어진다. 틈 사이로 아래 깔개(모전)가 보이고, 잘린 조각 쪽 가장자리는 살짝 들려 빛을 받는다.
    틈 폭은 칼끝에서 멀어질수록 벌어진다(0.15 → 0.7mm)."""
    gap = np.zeros((H * 2, W * 2), F32); lipm = np.zeros_like(gap); shd = np.zeros_like(gap)
    if len(CUT) < 2: return gap[::2, ::2], lipm[::2, ::2], shd[::2, ::2]
    pts = np.array(CUT)
    px, py = V.to_px(pts[:, 0], pts[:, 1]); q = np.stack([px, py], 1) * 2
    dist = np.linalg.norm(pts - np.array(tip), axis=1) if tip is not None else np.full(len(pts), 99.0)
    flapn = np.array((-1.0, 1.0)) / math.sqrt(2) * V.ppm * 2            # 잘린 조각(구석) 쪽 화면 방향
    for i in range(len(pts) - 1):
        w = 0.15 + 0.55 * min(1.0, dist[i] / 14.0)                        # mm
        a_, b_ = q[i], q[i + 1]
        cv2.line(gap, tuple(a_.astype(int)), tuple(b_.astype(int)), 1.0, max(1, int(w * V.ppm * 2)), cv2.LINE_AA)
        o = flapn * (w * 0.5 + 0.18)
        cv2.line(lipm, tuple((a_ + o).astype(int)), tuple((b_ + o).astype(int)), 1.0, max(1, int(0.22 * V.ppm * 2)), cv2.LINE_AA)
        o2 = -flapn * (w * 0.5 + 0.35)
        cv2.line(shd, tuple((a_ + o2).astype(int)), tuple((b_ + o2).astype(int)), 1.0, max(1, int(0.6 * V.ppm * 2)), cv2.LINE_AA)
    r = lambda m: cv2.resize(m, (W, H), interpolation=cv2.INTER_AREA)
    return r(gap), r(lipm), cv2.GaussianBlur(r(shd), (0, 0), 1.2)

def poly_px(pts, off=(0, 0)):
    pts = np.array(pts, float) + np.array(off)
    px, py = V.to_px(pts[:, 0], pts[:, 1]); return np.stack([px, py], 1).astype(np.int32)

def knife_polys(s, n):
    """서도용 종이칼: 넓고 납작한 외날, 비스듬히 깎인 칼끝. 자를 따라 몸 쪽(+U, 화면 오른쪽 아래)으로 당기므로
    칼등은 자 쪽에 붙고, 손잡이는 당기는 방향(화가 쪽)으로 뻗는다."""
    tip = P0 + U * s + NRM * n
    f = U; g = -NRM                                                   # f: 손잡이 쪽, g: 잘린 조각 쪽(칼날 폭)
    blade = [tip, tip + f * 30 + g * 0.8, tip + f * 30 + g * 9.5, tip + f * 13 + g * 9.5]
    handle = [tip + f * 30 + g * 0.2, tip + f * 160 + g * 0.6, tip + f * 160 + g * 10.2, tip + f * 30 + g * 10.0]
    return blade, handle, tip

def setview(t):
    """카메라가 칼끝을 따라간다(손잡이는 늘 화면 오른쪽 아래 밖으로 — 손은 화면 밖에서 쥐고 있다)."""
    global V, X, Y, RGB, FIB, DRG, OFF, DOT
    ts = np.linspace(max(0.0, t - 0.5), t, 6)
    tips = []
    for tt in ts:
        s_, n_, h_ = blade_state(tt); tips.append(P0 + U * s_ + NRM * n_)
    c = np.mean(tips, 0)
    V = View(c[0] + 10, c[1] + 6, 112, W, H)
    X, Y = V.grid_mm()
    RGB, FIB, DRG = plate.sample(X, Y)
    OFF = ((X < 0) | (X > 640) | (Y < 0) | (Y > 420)).astype(F32)
    d = inkmm.sample(D.density(15.5), V, X, Y)
    hh = cv2.GaussianBlur(d, (0, 0), max(0.6, 0.3 * V.ppm))
    DOT = d + np.clip(hh - d, 0, 0.6) * np.clip(FIB * 1.5 - 0.2, 0, 1.3) * 1.4

def hand_shadow(tip, h):
    """화면 밖에서 칼자루를 쥔 손과 소매의 그림자(등잔이 왼쪽 아래 낮은 곳 → 오른쪽 위로 드리움, 높을수록 흐림)."""
    m = np.zeros((H, W), F32)
    S_DIR = np.array((0.6, -0.8))
    for (along, z, rx, ry, wgt) in ((120, 40 + h, 24, 17, 1.0), (175, 70 + h, 46, 30, 0.8)):
        c = tip + U * along + S_DIR * 0.45 * z
        px, py = V.to_px(c[0], c[1])
        mm = np.zeros((H, W), F32)
        cv2.ellipse(mm, (int(px), int(py)), (int(rx * V.ppm), int(ry * V.ppm)), 45, 0, 360, 1.0, -1, cv2.LINE_AA)
        m = np.maximum(m, cv2.GaussianBlur(mm, (0, 0), 0.06 * z * V.ppm) * wgt)
    return m

def frame(t):
    setview(t)
    s, n, h = blade_state(t)
    if 0.7 <= t < 3.85 and h == 0.0:
        p = P0 + U * s + NRM * n
        if not CUT or np.linalg.norm(p - CUT[-1]) > 0.3:
            CUT.append(p)
    dens = DRG + DOT
    img = RGB * np.exp(-dens[..., None] * INK_ABS)
    img = img * (1 - OFF[..., None]) + np.array((0.16, 0.10, 0.065), F32) * OFF[..., None]
    # 칼집: 갈라진 틈(어둡게) + 잘린 면 한쪽 테(밝게)
    tip_now = (P0 + U * s + NRM * n) if (0.7 <= t < 3.85 and h == 0.0) else None
    gap, lipm, shd = cut_layers(tip_now)
    img = img * (1 - 0.18 * shd[..., None])                                   # 들린 조각이 드리운 얇은 그림자
    img = img * (1 - gap[..., None]) + gap[..., None] * np.array((0.13, 0.13, 0.12), F32)   # 틈 사이로 보이는 모전
    img = img + 0.09 * np.clip(lipm - gap, 0, 1)[..., None]                   # 잘린 가장자리가 등잔빛을 받는다
    # 자(대나무) — 지킬 쪽(NRM)에 놓임
    ruler = [P0 + U * -40, P0 + U * 200, P0 + U * 200 + NRM * 24, P0 + U * -40 + NRM * 24]
    sh = np.zeros((H, W), F32)
    cv2.fillPoly(sh, [poly_px(ruler, (1.6, 2.4))], 1.0)
    blade, handle, tip = knife_polys(s, n)
    hoff = np.array((0.55, -0.85)) * (h + 6)           # 칼 그림자(등잔: 왼쪽 아래)
    cv2.fillPoly(sh, [poly_px(blade, hoff * 0.5)], 1.0); cv2.fillPoly(sh, [poly_px(handle, hoff * 1.3)], 1.0)
    sh = cv2.GaussianBlur(sh, (0, 0), 1.2 * V.ppm)
    img = img * (1 - 0.45 * sh[..., None])
    img = img * (1 - 0.5 * hand_shadow(P0 + U * s + NRM * n, h)[..., None])
    lay = np.zeros_like(img); m = np.zeros((H, W), F32)
    # 대나무 자: 결(길이 방향 가는 줄), 마디, 모서리 빛 — 납작한 면처럼 보이지 않게
    ac = (X - P0[0]) * NRM[0] + (Y - P0[1]) * NRM[1]; al = (X - P0[0]) * U[0] + (Y - P0[1]) * U[1]
    rm = ((ac >= 0) & (ac <= 24) & (al >= -40) & (al <= 200)).astype(F32)
    gr = 0.05 * np.sin(ac * 9.0 + 0.7 * np.sin(al * 0.07)) + 0.03 * np.sin(ac * 23.0 + al * 0.02) + 0.04 * (FIB - 0.3)
    nd = np.zeros_like(ac)
    for k in range(-20, 200, 46):
        nd = np.maximum(nd, np.exp(-((al - k) / 0.9) ** 2))
    bev = np.exp(-(ac / 0.9) ** 2) * 0.18 - np.exp(-((24 - ac) / 1.2) ** 2) * 0.15
    rcol = np.array((0.74, 0.61, 0.38), F32)[None, None, :] * (1 + gr + bev - 0.28 * nd)[..., None]
    lay = lay * (1 - rm[..., None]) + rcol * rm[..., None]; m = np.maximum(m, rm)

    cv2.fillPoly(lay, [poly_px(handle)], (0.30, 0.19, 0.12)); cv2.fillPoly(m, [poly_px(handle)], 1.0)
    cv2.fillPoly(lay, [poly_px(blade)], (0.66, 0.68, 0.70)); cv2.fillPoly(m, [poly_px(blade)], 1.0)
    # 날의 반사(등잔빛 한 줄)
    q = poly_px([tip + U * 2 + (-NRM) * 1.2, blade[1] + (-NRM) * 1.2])        # 칼등을 따라 반사광 한 줄
    cv2.line(lay, tuple(q[0]), tuple(q[1]), (0.95, 0.86, 0.66), max(1, int(V.ppm * 0.5)), cv2.LINE_AA)
    q = poly_px([tip, blade[3]])                                                # 비스듬한 칼끝 날
    cv2.line(lay, tuple(q[0]), tuple(q[1]), (0.85, 0.86, 0.88), max(1, int(V.ppm * 0.3)), cv2.LINE_AA)
    m = cv2.GaussianBlur(m, (0, 0), 0.7)[..., None]
    img = img * (1 - m) + lay * m
    img = light(img, 'lamp')
    yy, xx = np.mgrid[0:H, 0:W].astype(F32)
    img = img * np.clip(1.15 - 0.5 * (((xx + 200) / W) ** 2 + ((yy - H * 1.2) / H) ** 2) ** 0.5, 0.45, 1.1)[..., None]
    img = film(img, t, H=H, W=W, vig=0.22, grain=0.012, weave=0.35)
    img = letterbox(img)
    return (np.clip(img, 0, 1)[..., ::-1] * 255 + 0.5).astype(np.uint8)

if __name__ == '__main__':
    out = os.path.join(JE, 'cache', 'knife_test' + SUF); os.makedirs(out, exist_ok=True)
    FR = []
    for k in range(int(DUR * FPS)):
        f = frame(k / FPS); FR.append(f); cv2.imwrite(os.path.join(out, f'k{k:04d}.png'), f)
    np.save(os.path.join(JE, 'cache', 'knife_cut.npy'), np.array(CUT))                # 칼집 자취(애니마틱·번짐 장벽에 쓴다)
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-framerate', str(FPS), '-i', os.path.join(out, 'k%04d.png'),
                    '-vf', 'fps=24', '-c:v', 'libx264', '-crf', '18', '-pix_fmt', 'yuv420p', os.path.join(JE, 'cache', 'knife_test.mp4')])
    pick = [4, 20, 36, 43, 50, 71]
    cv2.imwrite(os.path.join(JE, 'cache', 'knife_test_sheet.jpg'),
                cv2.resize(np.vstack([np.hstack([FR[i] for i in pick[:3]]), np.hstack([FR[i] for i in pick[3:]])]), (1440, 540)), [cv2.IMWRITE_JPEG_QUALITY, 90])
    print('ok')
