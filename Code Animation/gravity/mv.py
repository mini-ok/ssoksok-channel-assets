"""〈Gravity〉 뮤직비디오 — frame(t, W, H)는 시간의 순수 함수. 곡에서 잰 타격 시각과 가사 시각표(nums.py)를 읽는다.
새 화풍: orbit 궤도 / sterile 무균 진공(유리 금) / fall 추락 / press 짓누르는 글자 / mud 진흙. 나머지는 styles.py(〈꺾기〉 판)."""
import math, os, sys, bisect
import numpy as np, cv2
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import nums as N, fig as F, styles as S
from styles import View, masks, sstep, eout, hrand, text_img, paste, bgr, glow, C_PAPER, C_INK, C_RED, C_BLUE, C_GOLD, C_GREEN, PAL
from vfx import post
from PIL import Image, ImageDraw, ImageFont
SANS = '/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc'; BLACK = '/usr/share/fonts/opentype/noto/NotoSansCJK-Black.ttc'; LIGHT = '/usr/share/fonts/opentype/noto/NotoSansCJK-Light.ttc'
_tx = {}
def timg(s, px, font=SANS, track=0):
    key = (s, int(px), font, track)
    if key not in _tx:
        f = ImageFont.truetype(font, int(px), index=1); ws = [f.getlength(c) + track for c in s]; w = int(sum(ws)) + 8; im = Image.new('L', (w, int(px * 1.5)), 0); d = ImageDraw.Draw(im); x = 4
        for c, cw in zip(s, ws): d.text((x, 0), c, 255, font=f); x += cw
        _tx[key] = np.asarray(im, np.float32) / 255
    return _tx[key]

_LT = [l[0] for l in N.LYR]
def cur_line(t):
    i = bisect.bisect_right(_LT, t) - 1
    if i < 0 or t > N.LYR[i][1] + 0.25: return None
    return N.LYR[i]
def cur_word(t):
    """지금 불리는 낱말: (낱말, 나이, 번호, 줄의 낱말들)."""
    l = cur_line(t)
    if not l: return None
    ws = l[2].replace(',', '').split(); span = max(0.3, l[1] - l[0] - 0.4); k = min(len(ws) - 1, int((t - l[0]) / span * len(ws)))
    return ws[k], t - (l[0] + k * span / len(ws)), k, ws

# ---- 새 화풍 -------------------------------------------------------------------------------
def fig_outline(img, J, v, body, col, fill=None, th=2):
    if fill is not None: img[:] = img * (1 - body[..., None]) + np.asarray(fill, np.float32) * body[..., None]
    cnt, _ = cv2.findContours((body > 0.5).astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    cv2.drawContours(img, cnt, -1, [float(c) for c in col], max(1, int(th * v.k)), cv2.LINE_AA)

def st_orbit(t, v):
    W, H = v.W, v.H; k = v.k; J, i, tau = v.J(t); body, acc = masks(J, v)
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    img = np.empty((H, W, 3), np.float32); img[:] = (0.13, 0.06, 0.03); img *= (1.25 - 0.7 * np.hypot((xx - W / 2) / W, (yy - H / 2) / H))[..., None]
    rng = np.random.default_rng(4); sx = rng.random(260) * W; sy = rng.random(260) * H; sp = rng.random(260)
    for a, b, c in zip(sx, sy, sp):
        tw = 0.35 + 0.65 * (0.5 + 0.5 * math.sin(t * (0.6 + 2 * c) + c * 40)); cv2.circle(img, (int((a - t * 3 * c * k) % W), int(b)), 1 if c < 0.85 else 2, (tw, tw, tw * 0.9), -1, cv2.LINE_AA)
    c0 = (W // 2, int(H * 0.52)); grow = eout(t / 6.0)
    for n in range(6):                                                       # 계산된 궤도: 타원·눈금·위성
        a, b = int((230 + 150 * n) * v.s), int((84 + 56 * n) * v.s); ang = -12 + 4 * n; end = 360 * min(1.0, grow * 1.6 - n * 0.1)
        if end <= 0: continue
        cv2.ellipse(img, c0, (a, b), ang, 0, end, (0.75, 0.55, 0.25) if n != 2 else (1.0, 0.9, 0.6), 1, cv2.LINE_AA)
        ph = t * (0.5 - 0.06 * n) + n * 1.7; r = math.radians(ang)
        for q in range(24):
            aa = q * math.pi / 12; ex, ey = a * math.cos(aa), b * math.sin(aa); px, py = c0[0] + ex * math.cos(r) - ey * math.sin(r), c0[1] + ex * math.sin(r) + ey * math.cos(r)
            if aa * 57.3 < end: cv2.line(img, (int(px), int(py)), (int(px + 5 * k * math.cos(aa)), int(py + 5 * k * math.sin(aa))), (0.6, 0.45, 0.2), 1, cv2.LINE_AA)
        ex, ey = a * math.cos(ph), b * math.sin(ph); cv2.circle(img, (int(c0[0] + ex * math.cos(r) - ey * math.sin(r)), int(c0[1] + ex * math.sin(r) + ey * math.cos(r))), max(2, int(5 * v.s)), (1, 0.95, 0.8), -1, cv2.LINE_AA)
    cv2.line(img, (c0[0], 0), (c0[0], H), (0.3, 0.2, 0.08), 1); cv2.line(img, (0, c0[1]), (W, c0[1]), (0.3, 0.2, 0.08), 1)
    px, py = J['P']; cv2.circle(img, (px, py), int(300 * v.s), (0.5, 0.4, 0.2), 1, cv2.LINE_AA)       # 몸을 가둔 원
    for q in range(0, 360, 15): cv2.ellipse(img, (px, py), (int(318 * v.s),) * 2, t * 20, q, q + 5, (0.5, 0.4, 0.2), 1, cv2.LINE_AA)
    fig_outline(img, J, v, body, (1.0, 0.97, 0.9), fill=(0.20, 0.12, 0.07), th=2.5)
    img = img * (1 - acc[..., None]) + np.array((1.0, 0.85, 0.5), np.float32) * acc[..., None] * (0.6 + 0.4 * math.sin(t * 2) ** 2)
    return img + 0.35 * cv2.GaussianBlur(img, (0, 0), 8 * k)

_crk = {}
def cracks(W, H, origin, seed, n=17):
    key = (W, H, seed)
    if key not in _crk:
        rng = np.random.default_rng(seed); rays = []
        for q in range(n):
            a = q * 6.283 / n + rng.normal(0, 0.12); p = np.array(origin, np.float32); pts = [p.copy()]
            for st in range(26):
                a += rng.normal(0, 0.22); p = p + np.array([math.cos(a), math.sin(a)]) * W * 0.035 * (0.6 + rng.random()); pts.append(p.copy())
            rays.append(np.array(pts))
        _crk[key] = rays
    return _crk[key]
def draw_cracks(img, W, H, origin, seed, p, k, dark=True):
    rays = cracks(W, H, origin, seed)
    for ri, pts in enumerate(rays):
        m = max(2, int(len(pts) * p)); q = pts[:m].astype(np.int32)
        cv2.polylines(img, [q + 2], False, (1, 1, 1), max(1, int(2 * k)), cv2.LINE_AA); cv2.polylines(img, [q], False, (0.08, 0.07, 0.07) if dark else (1, 1, 1), max(1, int((3 if ri % 3 else 5) * k)), cv2.LINE_AA)
        if p > 0.5 and ri % 2 == 0:                                          # 금 사이를 잇는 가로 금
            o = rays[(ri + 1) % len(rays)]; j = 4 + (ri * 3) % 14
            if j < m: cv2.line(img, tuple(q[j]), tuple(o[j].astype(int)), (0.1, 0.1, 0.1) if dark else (1, 1, 1), max(1, int(2 * k)), cv2.LINE_AA)

def st_sterile(t, v):
    W, H = v.W, v.H; k = v.k; J, i, tau = v.J(t); body, acc = masks(J, v)
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    img = np.empty((H, W, 3), np.float32); img[:] = (0.95, 0.94, 0.93); img *= (1.03 - 0.16 * np.hypot((xx - W / 2) / W, (yy - H / 2) / H))[..., None]
    g = 80 * v.s
    for x in np.arange((W / 2) % g, W, g): cv2.line(img, (int(x), 0), (int(x), H), (0.86, 0.85, 0.84), 1)
    for y in np.arange((H / 2) % g, H, g): cv2.line(img, (0, int(y)), (W, int(y)), (0.86, 0.85, 0.84), 1)
    cv2.circle(img, (W // 2, H // 2), int(420 * v.s), (0.80, 0.79, 0.78), 1, cv2.LINE_AA)
    dryness = float(np.clip((t - 35.0) / 8.0, 0, 1))                         # 말라 간다: 몸에서 부스러기가 떠오른다
    pts = np.zeros((H, W), np.float32); keys = ['H', 'C', 'P', 'HL', 'HR', 'EL', 'ER', 'KL', 'KR', 'FL', 'FR']
    for n in range(int(40 + 420 * dryness)):
        ph = (t * (0.25 + 0.4 * hrand(n, 1)) + hrand(n, 2)) % 1.0; j = J[keys[n % len(keys)]]
        x = j[0] + (hrand(n, 3) - 0.5) * 90 * v.s + 30 * v.s * math.sin(ph * 6 + n); y = j[1] - ph * 420 * v.s + (hrand(n, 4) - 0.5) * 60 * v.s
        if 0 <= x < W and 0 <= y < H: pts[int(y), int(x)] += (1 - ph) * 1.0
    pts = cv2.GaussianBlur(pts, (0, 0), max(0.7, 1.3 * k)) * 3
    img *= (1 - np.clip(pts, 0, 0.75))[..., None]
    sh = cv2.GaussianBlur(cv2.warpAffine(body, np.float32([[1, 0, 0], [0, 1, 26 * k]]), (W, H)), (0, 0), 14 * k); img *= (1 - 0.16 * sh)[..., None]
    fillc = np.array((0.90, 0.89, 0.88), np.float32) * (1 - 0.25 * dryness)
    fig_outline(img, J, v, body, (0.25, 0.24, 0.24), fill=fillc, th=2.5)
    img = img * (1 - acc[..., None]) + np.array((0.62, 0.60, 0.58), np.float32) * acc[..., None]
    for (tc, seed) in ((43.5, 1), (45.0, 2)):                                # 유리에 금
        if t >= tc:
            Jc, _, _ = v.J(tc + 0.09); draw_cracks(img, W, H, Jc['HR'], seed, eout((t - tc) / 0.25) * (0.55 if seed == 1 else 1.0), k)
            if t - tc < 0.1: img = img + (1 - img) * (1 - (t - tc) / 0.1)
    return img

def st_fall(t, v):
    W, H = v.W, v.H; k = v.k; J, i, tau = v.J(t); body, acc = masks(J, v); bi = N.beat_i(t)
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    top, bot = np.array((0.20, 0.07, 0.10), np.float32), np.array((0.10, 0.22, 0.75), np.float32)
    img = top + (bot - top) * (yy / H)[..., None] ** 1.6
    st = np.zeros((H, W), np.float32)
    for n in range(90):                                                      # 위로 스치는 선: 떨어지는 속도
        x = int(hrand(n, 1) * W); sp = 1.5 + 3 * hrand(n, 2); L_ = int((80 + 380 * hrand(n, 3)) * k); y = int((1 - ((t * sp + hrand(n, 4)) % 1.0)) * (H + L_)) - L_
        cv2.line(st, (x, y), (x, y + L_), 0.25 + 0.75 * hrand(n, 5), max(1, int((1 + 3 * hrand(n, 6)) * k)), cv2.LINE_AA)
    img += st[..., None] * np.array((1.0, 0.9, 0.8), np.float32) * 0.55
    w = cur_word(t)
    if w:                                                                    # 낱말이 하나씩 화면을 친다
        g = timg(w[0], 400 * k, BLACK); sc = min(1.0, 0.86 * W / g.shape[1]) * (1 + 0.5 * (1 - eout(w[1] / 0.12)))
        g = cv2.resize(g, None, fx=sc, fy=sc); m = np.zeros((H, W), np.float32); paste(m, g, W / 2, H * 0.46 - 60 * k * eout(w[1] / 0.5))
        img = img * (1 - m[..., None]) + PAL[(w[2] + 2) % 4] * m[..., None] * 1.15
    for q in range(5, 0, -1):                                                # 위에 남는 잔상
        Jg, _, _ = v.J(t - q * 0.035); gb, _ = masks(Jg, v); gb = cv2.warpAffine(gb, np.float32([[1, 0, 0], [0, 1, -q * 46 * k]]), (W, H))
        img = img * (1 - 0.22 * gb[..., None]) + C_PAPER * 0.22 * gb[..., None] * (1 - q / 7)
    ol = cv2.dilate(body, np.ones((max(3, int(9 * k)) | 1,) * 2, np.uint8)); img = img * (1 - ol[..., None]) + C_INK * ol[..., None]
    img = img * (1 - body[..., None]) + C_PAPER * body[..., None]; img = img * (1 - acc[..., None]) + C_RED * acc[..., None]
    return img

def st_press(t, v):
    W, H = v.W, v.H; k = v.k; J, i, tau = v.J(t); body, acc = masks(J, v)
    l = cur_line(t) or N.LYR[13]; t0 = l[0]; a = t - t0
    img = np.empty((H, W, 3), np.float32); img[:] = (0.07, 0.065, 0.07)
    gy = v((0, N.GROUND))[1]; cv2.line(img, (0, gy), (W, gy), [float(c) for c in C_PAPER], max(1, int(4 * k)))
    rows = ['온몸을', '짓누르는', '이 낯선', '무게감']; cols = [C_GOLD, C_PAPER, C_RED, C_PAPER]
    ys, xs = np.where(body > 0.5); top = ys.min() if len(ys) else H // 2
    nvis = sum(1 for r in range(4) if a - r * 0.75 > 0); rh = int(104 * k)        # 새 줄이 몸 바로 위에 떨어지고, 먼저 온 줄은 위로 밀린다
    for r in range(nvis):
        ta = a - r * 0.75; g = timg(rows[r], 150 * k, BLACK); g = g[int(g.shape[0] * 0.2):int(g.shape[0] * 0.95)]
        sc = min(1.6, 0.62 * W / g.shape[1]); g = cv2.resize(g, None, fx=sc, fy=rh / g.shape[0])
        tn = a - (nvis - 1) * 0.75; slot = (nvis - 1 - r) - (1 - eout(tn / 0.12)) * (1 if r < nvis - 1 else 0)
        drop = (1 - eout(ta / 0.14)) * H * 0.7 if r == nvis - 1 else 0
        m = np.zeros((H, W), np.float32); paste(m, g, W / 2 + (hrand(r, int(t * 30)) - 0.5) * 16 * k * math.exp(-tn / 0.1), top - int(10 * k) - rh / 2 - slot * rh - drop)
        img = img * (1 - m[..., None]) + cols[r] * m[..., None]
    img = img * (1 - body[..., None]) + C_PAPER * body[..., None]; img = img * (1 - acc[..., None]) + C_RED * acc[..., None]
    for n in range(40):                                                      # 눌릴 때 바닥에서 이는 먼지
        hh = N.last_hit(t); ag = t - hh; x = W / 2 + (hrand(n, hh) - 0.5) * W * 0.9 * eout(ag / 0.4); cv2.circle(img, (int(x), gy - int(hrand(n, 2) * 60 * k * eout(ag / 0.3))), max(1, int(3 * k)), (0.6, 0.6, 0.6), -1)
    return img

def st_mud(t, v):
    S.CTX['mud'] = True
    try: return S.st_ink(t, v)
    finally: S.CTX['mud'] = False

STY = dict(S.STYLES); STY.update(orbit=st_orbit, sterile=st_sterile, fall=st_fall, press=st_press, mud=st_mud)
S.STYLES.update(STY)
DARK = {'orbit', 'neon', 'part', 'kal', 'fall', 'press', 'blue', 'glitch', 'cel', 'typo', 'grid'}

# ---- 가사 자막 ----------------------------------------------------------------------------
def subtitle(img, t, style, W, H):
    l = cur_line(t)
    if not l: return img
    k = min(W / N.DW, H / N.DH); ws = l[2].split(); span = max(0.3, l[1] - l[0] - 0.4)
    font, px, tr = (LIGHT, 56, 10) if l[3] in ('v1', 'v2') else (SANS, 64, 2)
    parts = [timg(w, px * k, font, int(tr * k)) for w in ws]; gap = int(22 * k); tw = sum(p.shape[1] for p in parts) + gap * (len(ws) - 1)
    m = np.zeros((H, W), np.float32); x = W / 2 - tw / 2; fade = min(1.0, max(0.0, (l[1] + 0.25 - t) / 0.25))
    for j, p in enumerate(parts):
        a = eout((t - (l[0] + j * span / len(ws))) / 0.18)
        if a > 0:
            dy = (1 - a) * 26 * k if l[3] not in ('v1', 'v2') else math.sin(t * 1.3 + j) * 5 * k        # 절: 떠다님 / 그 밖: 아래에서 올라와 박힘
            tmp = np.zeros((H, W), np.float32); paste(tmp, p * a * fade, x + p.shape[1] / 2, H * 0.875 + dy); m = np.maximum(m, tmp)
        x += p.shape[1] + gap
    halo = np.clip(cv2.GaussianBlur(cv2.dilate(m, np.ones((max(3, int(7 * k)) | 1,) * 2, np.uint8)), (0, 0), 3 * k) * 1.4, 0, 1)
    if style in DARK: img = img * (1 - 0.72 * halo[..., None]); return img * (1 - m[..., None]) + np.array((0.97, 0.98, 1.0), np.float32) * m[..., None]
    img = img + (C_PAPER - img) * 0.75 * halo[..., None]; return img * (1 - m[..., None]) + C_INK * m[..., None]

# ---- 프레임 -------------------------------------------------------------------------------
_ST = [s[0] for s in N.SHOTS]
def shot(t): i = max(0, bisect.bisect_right(_ST, t + 1e-6) - 1); return i, N.SHOTS[i]
S.shot = shot; S._ST = _ST
def render_shot(si, t, W, H, punch=1.0):
    _, style, zoom, ox, oy, tilt, _, lyr = N.SHOTS[si]; t0 = _ST[si]
    zoom *= 1 + 0.02 * min(8.0, t - t0)
    v = View(W, H, zoom, ox, oy, tilt, punch)
    img = S.st_ink(t, v, title=(si == len(N.SHOTS) - 1)) if style == 'ink' else STY[style](t, v)
    return subtitle(img, t, style, W, H) if lyr == 'sub' else img

def raw(t, W, H):
    si, sh = shot(t); t0 = _ST[si]; a = t - t0; tr = sh[6]
    punch = 1 + 0.03 * N.pulse(t) + (0.22 * (1 - eout(a / 0.16)) if tr == 'punch' else 0)
    img = render_shot(si, t, W, H, punch)
    if si > 0 and tr in ('bars', 'iris', 'whip', 'fade2') and a < (0.6 if tr == 'fade2' else 0.17):
        old = render_shot(si - 1, t, W, H); p = eout(a / 0.17); yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
        if tr == 'bars': m = ((xx / W * 10) % 1 < p).astype(np.float32)
        elif tr == 'iris': m = (np.hypot(xx - W / 2, yy - H / 2) < p * W * 0.62).astype(np.float32)
        elif tr == 'fade2': m = np.full((H, W), a / 0.6, np.float32)
        else:
            sx = int(W * (1 - p)); cat = np.concatenate([old, img], 1)[:, W - sx:2 * W - sx]
            return cv2.blur(cat, (max(1, int(90 * (1 - p) * W / 960)) | 1, 1))
        img = old * (1 - m[..., None]) + img * m[..., None]
    if tr == 'flash' and a < 0.1: img = img + (1 - img) * (1 - a / 0.1) ** 1.5
    if tr == 'invert' and a < 0.05: img = 1 - img
    for ti in (56.56, 111.4):                                                # 바닥에 부딪힌 순간 화면이 흔들린다
        d = t - ti
        if 0 <= d < 0.5:
            amp = 34 * W / 1920 * math.exp(-d / 0.12); fr = int(t * 30)
            img = cv2.warpAffine(img, np.float32([[1, 0, (hrand(fr, 1) - 0.5) * 2 * amp], [0, 1, (hrand(fr, 2) - 0.5) * 2 * amp]]), (W, H), borderMode=cv2.BORDER_REFLECT)
    return img

def fast(t):
    _, i, tau = F.pose(t); a = t - _ST[shot(t)[0]]; D = N.SEQ[i][2]
    return 4 if ((D <= 0.45 and tau < D) or a < 0.17 or any(m == 'fall' and a_ <= t < b_ for a_, b_, m in N.AIR)) else 1

def frame(t, W=960, H=540, k=0):
    n = fast(t)
    img = post.subframes(lambda tt: raw(max(0, tt), W, H), t, fps=N.FPS, n=n) if n > 1 else raw(t, W, H)
    img = post.grade(img, grain=0.010, seed=k)
    fd = min(1.0, t / 1.5) * min(1.0, max(0.0, (N.DUR - t) / 2.0))
    return np.clip(img * fd, 0, 1)
