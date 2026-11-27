"""〈장단 JANGDAN〉 그림 — frame(t, W, H)는 시간의 순수 함수(상태 없음). 숫자는 nums.py에서만 읽는다.
종이 구간: 안료별 '양 지도'를 그려 vfx.ink.composite(종이 × exp(−흡광))로 합친다.
칠흑 구간: 같은 양 지도를 만화경으로 접어 빛(가산)으로 합친다 — 한 재료, 두 가지 합성."""
import math, os, sys
import numpy as np, cv2
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, '..', '_kit'))
import nums as N
from vfx import ink, post
from PIL import Image, ImageDraw, ImageFont

B = N.B
K = {n: ink.pigment(N.PIG[n]) for n in N.ORDER}
FONT = '/usr/share/fonts/opentype/noto/NotoSerifCJK-Bold.ttc'

def sstep(a, b, x): x = np.clip((x - a) / (b - a + 1e-9), 0, 1); return x * x * (3 - 2 * x)
def ease(x): x = min(1.0, max(0.0, x)); return x * x * (3 - 2 * x)
def eout(x): x = min(1.0, max(0.0, x)); return 1 - (1 - x) ** 3

# ---- 세계에 고정된 결(디자인 좌표 1920×1080) --------------------------------------------
_c = {}
def tex():
    if 't' in _c: return _c['t']
    rng = np.random.default_rng(5); h, w = N.DH, N.DW
    fib = np.zeros((h, w), np.float32)
    for ang, ln in [(0.2, 61), (1.1, 45), (2.0, 71), (2.7, 37)]:           # 섬유: 방향이 다른 긴 흐림 네 겹
        k = np.zeros((ln, ln), np.float32); c = ln // 2
        cv2.line(k, (int(c - c * math.cos(ang)), int(c - c * math.sin(ang))), (int(c + c * math.cos(ang)), int(c + c * math.sin(ang))), 1.0, 1)
        fib += cv2.filter2D(rng.random((h, w)).astype(np.float32), -1, k / k.sum())
    fib = (fib - fib.min()) / (fib.max() - fib.min())
    fib = np.clip((fib - 0.5) * 3.2 + 0.5, 0, 1)
    blot = cv2.GaussianBlur(rng.random((h, w)).astype(np.float32), (0, 0), 90); blot = (blot - blot.min()) / (blot.max() - blot.min())
    fine = cv2.GaussianBlur(rng.random((h, w)).astype(np.float32), (0, 0), 1.2); fine = (fine - fine.min()) / (fine.max() - fine.min())
    paper = np.empty((h, w, 3), np.float32); paper[:] = N.PAPER[::-1]
    paper *= (0.955 + 0.06 * blot + 0.03 * (fine - 0.5))[..., None]
    paper = ink.fibres(paper, sstep(0.62, 0.95, fib), 0.5)
    streak = rng.random(4096).astype(np.float32)                           # 마른 붓 결(반지름 방향 1차원)
    streak = np.convolve(streak, np.ones(3) / 3, 'same')
    _c['t'] = (fib, paper, streak); return _c['t']

def cam(t):
    ks = N.CAM
    for (t0, x0, y0, z0), (t1, x1, y1, z1) in zip(ks, ks[1:]):
        if t <= t1:
            u = ease((t - t0) / (t1 - t0)); return x0 + (x1 - x0) * u, y0 + (y1 - y0) * u, z0 * (z1 / z0) ** u
    return ks[-1][1:]

def mat(c, W, H):
    cx, cy, z = c; s = W / N.DW * z
    return np.array([[s, 0, W / 2 - cx * s], [0, s, H / 2 - cy * s]], np.float32), s

def warp(img, M, W, H): return cv2.warpAffine(img, M, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)

# ---- 양 지도 ------------------------------------------------------------------------------
def amounts(t, c, W, H, upto=None):
    """안료별 양 지도(0..1) 사전. c = (중심x, 중심y, 배율). 방울·획·살을 그린다."""
    M, s = mat(c, W, H); fib = warp(tex()[0], M, W, H); streak = tex()[2]
    ox, oy = M[0, 2], M[1, 2]
    F = {n: np.zeros((H, W), np.float32) for n in N.ORDER}                 # 방울 원뿔 장(가장자리 문턱용)
    wet = {n: np.zeros((H, W), np.float32) for n in N.ORDER}               # 갓 떨어진 젖은 먹(더 진함)
    for i, (t0, x, y, R, pg) in enumerate(N.DROPS):
        age = t - t0
        if age <= 0 or (upto is not None and i >= upto): continue
        r = R * s * (0.30 + 0.70 * (1 - math.exp(-age / 0.45))) * (1 + 0.10 * math.exp(-age / 0.08))
        px, py = x * s + ox, y * s + oy; m = int(r + 3)
        x0, x1, y0, y1 = max(0, int(px) - m), min(W, int(px) + m + 1), max(0, int(py) - m), min(H, int(py) + m + 1)
        if x0 >= x1 or y0 >= y1: continue
        yy, xx = np.mgrid[y0:y1, x0:x1].astype(np.float32)
        cone = np.clip(1 - np.hypot(xx - px, yy - py) / r, 0, 1)
        F[pg][y0:y1, x0:x1] = np.maximum(F[pg][y0:y1, x0:x1], cone)
        wet[pg][y0:y1, x0:x1] = np.maximum(wet[pg][y0:y1, x0:x1], cone * math.exp(-age / 0.5))
        for j in range(5):                                                 # 튄 먹 점
            a = i * 2.4 + j * 1.9; d = r * (1.25 + 0.5 * ((i * 7 + j * 3) % 5) / 5) * eout(age / 0.18)
            cv2.circle(F[pg], (int(px + d * math.cos(a)), int(py + d * math.sin(a))), max(1, int(R * s * 0.045)), 0.5, -1, cv2.LINE_AA)
    out = {}
    for n in N.ORDER:
        e = F[n] + 0.26 * (fib - 0.5) * (F[n] > 0)
        a = sstep(0.03, 0.13, e)
        rim = np.exp(-((e - 0.13) / 0.07) ** 2)                            # 테두리 얼룩
        out[n] = a * (0.50 + 0.30 * sstep(0.45, 1.0, F[n]) + 0.30 * rim + 0.45 * wet[n])
    # 붓 획(원호): 압력은 굵기로, 마름은 반지름 결로
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    rr = np.hypot(xx - (N.CX * s + ox), yy - (N.CY * s + oy)) / s
    th = np.arctan2(yy - (N.CY * s + oy), xx - (N.CX * s + ox))
    sk_r = streak[np.clip((rr * 2.2).astype(np.int32), 0, 4095)]
    for (t0, dur, R, a0, sw, wd, pg) in N.STROKES:
        if t <= t0: continue
        p = eout((t - t0) / dur); nseg = max(8, int(abs(sw) * p * R * s / 5))
        body = np.zeros((H, W), np.float32); dry = np.zeros((H, W), np.float32)
        for k in range(nseg):
            u0, u1 = k / nseg * p, (k + 1) / nseg * p
            a_0, a_1 = a0 + sw * u0, a0 + sw * u1
            press = (0.35 + 0.65 * math.sin(math.pi * min(1, u0 * 1.15 + 0.08)) ** 0.6)
            p0 = (int((N.CX + R * math.cos(a_0)) * s + ox), int((N.CY + R * math.sin(a_0)) * s + oy))
            p1 = (int((N.CX + R * math.cos(a_1)) * s + ox), int((N.CY + R * math.sin(a_1)) * s + oy))
            th_px = max(1, int(wd * s * press))
            cv2.line(body, p0, p1, 1.0, th_px, cv2.LINE_AA); cv2.line(dry, p0, p1, float(u0 ** 1.6), th_px, cv2.LINE_AA)
        body = cv2.GaussianBlur(body, (0, 0), max(0.6, 0.9 * s))
        soak = sstep(0.25, 0.6, body + 0.35 * (fib - 0.5))
        gaps = sstep(0.35, 0.75, sk_r + 0.9 * dry - 0.55)                   # 끝으로 갈수록 비백
        out[pg] = np.maximum(out[pg], soak * (1 - 0.92 * gaps) * (0.62 + 0.38 * body))
    for (t0, ang, r0, r1, wd, pg) in N.SPOKES:
        if t <= t0: continue
        p = eout((t - t0) / 0.22); body = np.zeros((H, W), np.float32)
        q0 = (int((N.CX + r0 * math.cos(ang)) * s + ox), int((N.CY + r0 * math.sin(ang)) * s + oy))
        re = r0 + (r1 - r0) * p
        q1 = (int((N.CX + re * math.cos(ang)) * s + ox), int((N.CY + re * math.sin(ang)) * s + oy))
        cv2.line(body, q0, q1, 1.0, max(1, int(wd * s)), cv2.LINE_AA)
        body = cv2.GaussianBlur(body, (0, 0), max(0.6, 0.8 * s))
        d = np.abs(np.sin(th - ang)) * rr                                   # 획 축에서 벗어난 거리 → 결
        sk = streak[np.clip((d * 5 + 900).astype(np.int32), 0, 4095)]
        gaps = sstep(0.35, 0.75, sk + 0.9 * sstep(r0, r1, rr) ** 1.5 - 0.55)
        out[pg] = np.maximum(out[pg], sstep(0.25, 0.6, body + 0.35 * (fib - 0.5)) * (1 - 0.9 * gaps) * 0.9)
    return out, M

def paper_comp(am, M, W, H):
    return ink.composite(warp(tex()[1], M, W, H), [(am[n], K[n]) for n in N.ORDER])

# ---- 칠흑(만화경) ------------------------------------------------------------------------
LIGHT = dict(red=(0.10, 0.22, 1.00), blue=(1.00, 0.42, 0.12), gold=(0.18, 0.70, 1.00))    # BGR
_p = {}
def particles():
    if 'p' not in _p:
        rng = np.random.default_rng(3); n = N.N_PART
        _p['p'] = (60 + 600 * rng.random(n) ** 0.7, rng.random(n) * 6.283, 0.25 + 1.2 * rng.random(n), rng.random(n) * 6.283, 0.5 + rng.random(n))
    return _p['p']

def fold_n(t):
    n = N.FOLDS[0][1]
    for tf, k in N.FOLDS:
        if t >= tf: n = k
    return n

def lacquer(t, W, H):
    s = W / N.DW; tk = t - N.T_KAL
    am, _ = amounts(t, (N.CX, N.CY, 1.0), W, H)
    src = np.dstack([am[n] for n in N.ORDER])
    nb = (t - N.T_KAL) / B.beat_len; kb = math.floor(nb); fr = nb - kb
    step = kb + 1 - math.exp(-6 * fr)                                       # 박마다 딸깍 도는 회전
    rot = 0.10 * step + 0.05 * tk; drift = 0.42 * tk + 0.12 * step
    pulse = B.pulse(t)
    col = ease((t - N.T_COL) / (N.T_DOT - N.T_COL)) if t > N.T_COL else 0.0
    shrink = (1 - col) ** 1.6 + 1e-3; rot += 4.0 * col * col
    n = fold_n(t); w = math.pi / n
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    dx, dy = xx - W / 2, yy - H / 2
    zoom = 1.18 + 0.10 * min(1.0, tk / 8.0)
    r = np.hypot(dx, dy) / (shrink * zoom) * (1 - 0.035 * pulse); a = np.arctan2(dy, dx) - rot
    a = np.abs(np.mod(a, 2 * w) - w) + drift                                # 거울 접기
    mx = (W / 2 + r * np.cos(a)).astype(np.float32); my = (H / 2 + r * np.sin(a) * 1.0).astype(np.float32)
    f = cv2.remap(src, mx, my, cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=0)
    rd = np.hypot(dx, dy) / s
    img = np.zeros((H, W, 3), np.float32); img[:] = (0.022, 0.014, 0.016)
    img += (0.05 * np.exp(-(rd / 520) ** 2))[..., None] * np.array((0.9, 0.5, 0.4), np.float32)
    ph = rd / 150 - 1.2 * tk + 3 * np.arctan2(dy, dx) * 0                   # 자개: 반지름을 따라 무지갯빛
    pearl = np.stack([0.62 + 0.38 * np.cos(6.283 * (ph + o)) for o in (0.0, 0.33, 0.67)], -1).astype(np.float32)
    img += f[..., 0:1] * pearl * 0.95
    for i, nme in enumerate(N.ORDER[1:], 1):
        img += f[..., i:i + 1] * np.array(LIGHT[nme], np.float32) * 1.25
    # 금가루
    pr, pa, pw, pp, pb = particles()
    rr = pr * shrink * (1 + 0.06 * pulse * np.sin(pp)); aa = pa + pw * (tk * 0.6 + 0.25 * step) * (220 / (pr + 80)) + 3.0 * col * col
    px = (W / 2 + rr * s * np.cos(aa)).astype(np.int32); py = (H / 2 + rr * s * np.sin(aa)).astype(np.int32)
    ok = (px >= 0) & (px < W) & (py >= 0) & (py < H)
    tw = (0.35 + 0.65 * (0.5 + 0.5 * np.sin(tk * 5 * pb + pp)) ** 3) * min(1.0, tk / 0.4)
    dots = np.zeros((H, W), np.float32); np.add.at(dots, (py[ok], px[ok]), tw[ok])
    dots = cv2.GaussianBlur(dots, (0, 0), max(0.7, 0.9 * s)) * (5.0 * s + 2.5)
    img += dots[..., None] * np.array((0.30, 0.74, 1.0), np.float32)
    lum = np.clip(img - 0.35, 0, None)
    img += 0.55 * cv2.GaussianBlur(lum, (0, 0), 9 * s) + 0.35 * cv2.GaussianBlur(lum, (0, 0), 28 * s)
    img *= 1 + 0.22 * pulse + 1.2 * col ** 3
    return img

# ---- 제목 --------------------------------------------------------------------------------
def title_maps():
    if 'm' in _c: return _c['m']
    im = Image.new('L', (N.DW, N.DH), 0); d = ImageDraw.Draw(im)
    f1 = ImageFont.truetype(FONT, 84, index=0); f2 = ImageFont.truetype(FONT, 78, index=0)
    en = 'JANGDAN'; x = N.CX - 310
    for ch in en:                                                           # 자간을 넓혀 한 자씩
        wch = d.textlength(ch, font=f1); d.text((x + (88 - wch) / 2, N.CY + 150), ch, 255, font=f1); x += 88
    d.text((N.CX - 90, N.CY + 262), '장 단', 255, font=f2)
    txt = cv2.GaussianBlur(np.asarray(im, np.float32) / 255, (0, 0), 0.8)
    seal = cv2.resize(np.load(os.path.join(HERE, '..', '_shared', 'seal_baimun3.npy')).astype(np.float32), (92, 92), interpolation=cv2.INTER_AREA)[..., [2, 1, 0, 3]]
    _c['m'] = (txt, seal); return _c['m']

def title_frame(t, W, H):
    c = cam(t); M, s = mat(c, W, H); fib = warp(tex()[0], M, W, H)
    age = t - N.T_DOT
    R = 78 * s * (0.30 + 0.70 * (1 - math.exp(-age / 0.6))) * (1 + 0.12 * math.exp(-age / 0.08))
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    px, py = N.CX * s + M[0, 2], (N.CY - 60) * s + M[1, 2]
    cone = np.clip(1 - np.hypot(xx - px, yy - py) / R, 0, 1)
    e = cone + 0.26 * (fib - 0.5) * (cone > 0)
    dot = sstep(0.03, 0.13, e) * (0.62 + 0.3 * sstep(0.4, 1, cone) + 0.3 * np.exp(-((e - 0.13) / 0.07) ** 2) + 0.4 * cone * math.exp(-age / 0.6))
    txt, seal = title_maps(); tx = warp(txt, M, W, H)
    tt = t - (N.T_TITLE + B.beat_len * 2)                                   # 제목은 한 점 뒤 두 박에 스민다
    rev = sstep(0, 1, np.float32(tt / 1.2) * 1.6 - (xx / W) * 0.6 + 0.25 * (fib - 0.5)) if tt > 0 else 0.0
    img = ink.composite(warp(tex()[1], M, W, H), [(dot, K['sumi']), (tx * rev * 0.92, K['sumi'])])
    if t > N.T_SEAL:
        a = eout((t - N.T_SEAL) / 0.12); sz = int(92 * s); sl = cv2.resize(seal, (sz, sz), interpolation=cv2.INTER_AREA)
        x0, y0 = int((N.CX + 130) * s + M[0, 2]), int((N.CY + 272) * s + M[1, 2])
        red = np.clip((sl[..., 2:3] - sl[..., 1:2]) * 4, 0, 1); al = sl[..., 3:4] * a * red
        sub = img[y0:y0 + sz, x0:x0 + sz]; img[y0:y0 + sz, x0:x0 + sz] = sub * (1 - al + al * sl[..., :3])
    return img

# ---- 프레임 ------------------------------------------------------------------------------
def raw(t, W, H):
    if t < N.T_KAL:
        am, M = amounts(t, cam(t), W, H, upto=N.N_INTRO); img = paper_comp(am, M, W, H); mode = 'paper'
    elif t < N.T_DOT:
        img = lacquer(t, W, H); mode = 'lacquer'
    else:
        img = title_frame(t, W, H); mode = 'paper'
    return img, mode

def fast(t):
    if N.T_KAL <= t < N.T_DOT: return 5
    for (t0, dur, *_r) in N.STROKES:
        if t0 <= t < t0 + dur * 0.7: return 4
    for sp in N.SPOKES:
        if sp[0] <= t < sp[0] + 0.25: return 4
    return 1

def frame(t, W=960, H=540, k=0):
    n = fast(t)
    img = post.subframes(lambda tt: raw(tt, W, H)[0], t, fps=N.FPS, n=n) if n > 1 else raw(t, W, H)[0]
    mode = 'lacquer' if N.T_KAL <= t < N.T_DOT else 'paper'
    ev = sum(post.flash_dip(t, tf) for tf in N.FLASHES)
    if mode == 'paper':
        img = post.grade(img, exposure=ev * 0.55, sat=1.04, split=((0.0, 0.01, 0.03), (0.03, 0.015, -0.01), 0.5), s_curve=0.25, vignette=0.22, grain=0.012, seed=k)
    else:
        img = post.grade(img, exposure=ev + 0.1, tonemap='aces', sat=1.08, s_curve=0.2, vignette=0.35, grain=0.010, seed=k)
    for tf in (N.T_KAL, N.T_DOT):                                           # 합성 방식이 바뀌는 두 곳: 두 프레임 흰빛
        wv = max(0.0, 1 - abs(t - tf - 0.5 / N.FPS) / 0.075)
        if wv > 0: img = img + (np.array((0.93, 0.97, 1.0), np.float32) - img) * wv ** 0.7
    fd = min(1.0, t / 0.5) * min(1.0, max(0.0, (N.DUR - t) / 0.7))
    return np.clip(img * fd + (1 - fd) * 0.0, 0, 1)
