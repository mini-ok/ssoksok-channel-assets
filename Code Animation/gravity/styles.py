"""〈Gravity〉 화풍 모음(〈꺾기〉에서 가져와 곡의 타격 시각을 읽도록 고친 판) — 그림 — frame(t, W, H)는 시간의 순수 함수. 같은 뼈대 동작을 화풍 아홉 가지가 번갈아 그린다.
ink 먹·종이 / cel 셀·망점 / blue 청사진 / neon 네온·잔상 / part 입자 / typo 글자 / kal 만화경 / glitch 깨짐 / grid 분할."""
import math, os, sys, bisect
import numpy as np, cv2
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, '..', '_kit'))
import nums as N, fig as F
from vfx import ink, post
from PIL import Image, ImageDraw, ImageFont
B = N.B; BL = N.BL
FONT = '/usr/share/fonts/opentype/noto/NotoSerifCJK-Bold.ttc'
def bgr(c): return np.array(c[::-1], np.float32)
C_RED, C_BLUE, C_GOLD, C_GREEN, C_INK, C_PAPER = [bgr(c) for c in (N.RED, N.BLUE, N.GOLD, N.GREEN, N.INK, N.PAPER)]
PAL = [C_RED, C_BLUE, C_GOLD, C_GREEN]
K_SUMI, K_RED, K_BLUE, K_GOLD, K_MUD = [ink.pigment(c) for c in (N.INK, N.RED, N.BLUE, N.GOLD, N.MUD)]
CTX = dict(mud=False)
def sstep(a, b, x): x = np.clip((x - a) / (b - a + 1e-9), 0, 1); return x * x * (3 - 2 * x)
def eout(x): x = min(1.0, max(0.0, x)); return 1 - (1 - x) ** 3
def beat_i(t): return N.beat_i(t)
def bfrac(t): return min(1.0, max(0.0, t - N.last_hit(t)) / 0.6)
def hrand(*k): return (math.sin(sum((i + 1) * 12.9898 * v for i, v in enumerate(k)) + 78.233) * 43758.5453) % 1.0

# ---- 샷·시야 -----------------------------------------------------------------------------
_ST = [s[0] * BL for s in N.SHOTS]
def shot(t): i = max(0, bisect.bisect_right(_ST, t + 1e-6) - 1); return i, N.SHOTS[i]

class View:
    def __init__(s, W, H, zoom=1.0, ox=0, oy=0, tilt=0, punch=1.0):
        s.W, s.H = W, H; s.s = min(W / N.DW, H / N.DH) * zoom * punch; s.k = min(W / N.DW, H / N.DH)
        a = math.radians(tilt); s.R = np.array([[math.cos(a), -math.sin(a)], [math.sin(a), math.cos(a)]], np.float32)
        s.o = np.array([W / 2 + ox * s.k, H * 0.56 + oy * s.k], np.float32)
    def __call__(s, p): q = s.R @ ((np.asarray(p, np.float32) - (N.DW / 2, 600)) * s.s) + s.o; return (int(round(float(q[0]))), int(round(float(q[1]))))
    def J(s, t): J, i, tau = F.joints(t); return {k: (s(v) if k[0] != '_' else v) for k, v in J.items()}, i, tau

BONES = [('SL', 'EL', 34), ('EL', 'HL', 28), ('SR', 'ER', 34), ('ER', 'HR', 28), ('PL', 'KL', 42), ('KL', 'FL', 34), ('PR', 'KR', 42), ('KR', 'FR', 34), ('FL', 'TL', 26), ('FR', 'TR', 26), ('C', 'N', 26)]
LINES = [('P', 'C'), ('C', 'N'), ('N', 'H'), ('SL', 'SR'), ('SL', 'EL'), ('EL', 'HL'), ('SR', 'ER'), ('ER', 'HR'), ('PL', 'PR'), ('PL', 'KL'), ('KL', 'FL'), ('FL', 'TL'), ('PR', 'KR'), ('KR', 'FR'), ('FR', 'TR')]
def head_poly(J, v, w=92, h=80):
    a = math.radians(J['_ha'] + math.degrees(math.atan2(v.R[1, 0], v.R[0, 0]))); ux = np.array([math.cos(a), math.sin(a)]); uy = np.array([-math.sin(a), math.cos(a)])
    c = np.array(J['H'], np.float32); hw, hh = w * v.s / 2, h * v.s / 2
    return c, ux, uy, np.array([c - ux * hw - uy * hh, c + ux * hw - uy * hh, c + ux * hw + uy * hh, c - ux * hw + uy * hh], np.int32)

def masks(J, v):
    """몸 가림판과 강조(관절·눈가리개) 가림판(0..1)."""
    body = np.zeros((v.H, v.W), np.uint8); acc = np.zeros((v.H, v.W), np.uint8); s = v.s
    cv2.fillPoly(body, [np.array([J['SL'], J['SR'], J['PR'], J['PL']], np.int32)], 255, cv2.LINE_AA)
    cv2.line(body, J['SL'], J['SR'], 255, max(1, int(40 * s)), cv2.LINE_AA); cv2.line(body, J['PL'], J['PR'], 255, max(1, int(46 * s)), cv2.LINE_AA)
    for a, b, w in BONES: cv2.line(body, J[a], J[b], 255, max(1, int(w * s)), cv2.LINE_AA)
    for k in ('HL', 'HR'): cv2.circle(body, J[k], max(1, int(22 * s)), 255, -1, cv2.LINE_AA)
    c, ux, uy, hp = head_poly(J, v); cv2.fillPoly(body, [hp], 255, cv2.LINE_AA)
    vz = np.array([c - ux * 32 * s - uy * 14 * s, c + ux * 32 * s - uy * 14 * s, c + ux * 32 * s + uy * 4 * s, c - ux * 32 * s + uy * 4 * s], np.int32)
    cv2.fillPoly(acc, [vz], 255, cv2.LINE_AA)
    for k in ('SL', 'SR', 'EL', 'ER', 'KL', 'KR', 'PL', 'PR'): cv2.circle(acc, J[k], max(1, int(13 * s)), 255, -1, cv2.LINE_AA)
    cc = ((np.array(J['C']) * 0.62 + np.array(J['P']) * 0.38)).astype(int); cv2.circle(acc, (int(cc[0]), int(cc[1])), max(1, int(20 * s)), 255, -1, cv2.LINE_AA)
    return body.astype(np.float32) / 255, acc.astype(np.float32) / 255

def bursts(t, v, back=3):
    """최근 동작들의 (나이초, 화면 위치, 움직인 방향, 동작 번호)."""
    out = []; _, i, _ = F.pose(t)
    for j in range(max(1, i - back), i + 1):
        age = t - F._T[j]
        for k, pos, mv in F.emitters(j): out.append((age, v(pos), mv, j, k))
    return out

# ---- 결(종이·섬유) ------------------------------------------------------------------------
_c = {}
def tex(W, H):
    if (W, H) in _c: return _c[(W, H)]
    rng = np.random.default_rng(5); fib = np.zeros((H, W), np.float32)
    for ang, ln in [(0.2, 41), (1.1, 31), (2.0, 51), (2.7, 27)]:
        ln = max(5, int(ln * W / 1920) | 1); k = np.zeros((ln, ln), np.float32); c = ln // 2
        cv2.line(k, (int(c - c * math.cos(ang)), int(c - c * math.sin(ang))), (int(c + c * math.cos(ang)), int(c + c * math.sin(ang))), 1.0, 1)
        fib += cv2.filter2D(rng.random((H, W)).astype(np.float32), -1, k / k.sum())
    fib = (fib - fib.min()) / (fib.max() - fib.min()); fib = np.clip((fib - 0.5) * 3.2 + 0.5, 0, 1)
    blot = cv2.GaussianBlur(rng.random((H, W)).astype(np.float32), (0, 0), 60 * W / 1920); blot = (blot - blot.min()) / (blot.max() - blot.min())
    paper = np.empty((H, W, 3), np.float32); paper[:] = C_PAPER; paper *= (0.955 + 0.06 * blot)[..., None]
    paper = ink.fibres(paper, sstep(0.62, 0.95, fib), 0.5)
    streak = cv2.GaussianBlur(rng.random((H, 1)).astype(np.float32), (0, 0), 0.8).repeat(W, 1)      # 가로 마른 붓 결
    streak = (streak - streak.min()) / (streak.max() - streak.min())
    _c[(W, H)] = (fib, paper, streak); return _c[(W, H)]

_txt = {}
def text_img(s, px):
    key = (s, int(px))
    if key not in _txt:
        f = ImageFont.truetype(FONT, int(px), index=0); w = int(f.getlength(s)) + 8; im = Image.new('L', (w, int(px * 1.45)), 0)
        ImageDraw.Draw(im).text((4, 0), s, 255, font=f); _txt[key] = np.asarray(im, np.float32) / 255
    return _txt[key]
def paste(dst, src, cx, cy):
    h, w = src.shape; x0, y0 = int(cx - w / 2), int(cy - h / 2); X0, Y0 = max(0, x0), max(0, y0); X1, Y1 = min(dst.shape[1], x0 + w), min(dst.shape[0], y0 + h)
    if X0 < X1 and Y0 < Y1: dst[Y0:Y1, X0:X1] = np.maximum(dst[Y0:Y1, X0:X1], src[Y0 - y0:Y1 - y0, X0 - x0:X1 - x0])

# ---- 화풍 ---------------------------------------------------------------------------------
def st_ink(t, v, title=False):
    W, H = v.W, v.H; fib, paper, streak = tex(W, H); J, i, tau = v.J(t); body, acc = masks(J, v); k = v.k
    m = cv2.GaussianBlur(body, (0, 0), max(0.6, 1.4 * k))
    soak = sstep(0.28, 0.6, m + 0.36 * (fib - 0.5)); dry = sstep(0.55, 0.9, streak + 0.4 * fib - 0.25)
    sumi = soak * (0.86 - 0.5 * dry) * (1 - 0.95 * acc); red = sstep(0.3, 0.6, cv2.GaussianBlur(acc, (0, 0), max(0.5, k)) + 0.3 * (fib - 0.5)) * 0.9
    Jg, _, _ = v.J(t - 0.07); g, _ = masks(Jg, v); sumi = np.maximum(sumi, cv2.GaussianBlur(g, (0, 0), 3 * k) * 0.16 * (tau < 0.2))   # 지나간 자리의 담묵
    wash = np.zeros((H, W), np.float32); blue = np.zeros((H, W), np.float32); gold = np.zeros((H, W), np.float32)
    bi = beat_i(t); 
    for q in range(max(0, bi - 5), bi + 1):                                 # 박마다 뒤에서 그어지는 굵은 붓 획
        age = t - N.HITS[q]; p = eout(age / 0.16); y = int(H * (0.14 + 0.72 * hrand(q, 1))); th = int((34 + 70 * hrand(q, 2)) * k); dr = hrand(q, 3) > 0.5
        x0, x1 = (0, int(W * p)) if dr else (int(W * (1 - p)), W); band = np.zeros((H, W), np.float32); band[max(0, y - th):y + th, x0:x1] = 1
        band = cv2.GaussianBlur(band, (0, 0), 2 * k) * sstep(0.3, 0.7, streak * 0.9 + 0.5 * fib - 0.1 + 0.25) * (1 - sstep(0.35, 0.9, streak))
        tgt = [wash, blue, gold, wash][q % 4]; np.maximum(tgt, band * (0.30 if q % 4 in (0, 3) else 0.75) * max(0.25, 1 - 0.14 * (bi - q)), out=tgt)
    spl = np.zeros((H, W), np.uint8)
    for age, pos, mv, j, kk in bursts(t, v, back=6):                        # 꺾일 때 끝점에서 튀는 먹
        nm = np.hypot(*mv) + 1e-6
        for n in range(16):
            a = math.atan2(mv[1], mv[0]) + (hrand(j, n, 5) - 0.5) * 1.9; dd = (30 + 260 * hrand(j, n, 6)) * eout(age / 0.2) * min(1.6, nm / 120) * v.s
            cv2.circle(spl, (int(pos[0] + dd * math.cos(a)), int(pos[1] + dd * math.sin(a))), max(1, int((3 + 11 * hrand(j, n, 7) ** 2) * v.s)), 255, -1, cv2.LINE_AA)
    sumi = np.maximum(sumi, sstep(0.3, 0.6, cv2.GaussianBlur(spl.astype(np.float32) / 255, (0, 0), max(0.5, 0.8 * k)) + 0.3 * (fib - 0.5)) * 0.8)
    if N.SIDE[0] <= t < N.SIDE[1]:                                          # 걷는 구간: 지나온 발자국이 뒤로 밀려난다
        fp = np.zeros((H, W), np.uint8); gy = v((0, N.GROUND))[1]
        for (ts, nm, D, _) in N.SEQ:
            if nm in ('walkA', 'walkB') and ts < t: cv2.ellipse(fp, (int(W / 2 + (v.o[0] - W / 2) - (t - ts) * 190 * v.s), gy + int((6 if nm == 'walkA' else 16) * v.s)), (int(30 * v.s), int(9 * v.s)), 0, 0, 360, 255, -1, cv2.LINE_AA)
        sumi = np.maximum(sumi, sstep(0.3, 0.6, cv2.GaussianBlur(fp.astype(np.float32) / 255, (0, 0), max(0.5, k)) + 0.3 * (fib - 0.5)) * 0.6)
    layers = [(sumi + wash, K_SUMI), (red, K_RED), (blue, K_BLUE), (gold, K_GOLD)]
    if CTX['mud']: layers = [(sumi, K_SUMI), (wash * 2.4 + gold * 0.6 + blue * 0.5, K_MUD), (red, K_RED)]
    if title and t > N.T_TITLE:
        tm = np.zeros((H, W), np.float32); paste(tm, text_img('GRAVITY', 124 * k), W * 0.72, H * 0.38); paste(tm, text_img('중력 아래', 96 * k), W * 0.72, H * 0.56)
        yy, xx = np.mgrid[0:H, 0:W].astype(np.float32); rev = sstep(0, 1, (t - N.T_TITLE) / 0.5 * 1.6 - (xx / W - 0.4) * 1.2 + 0.25 * (fib - 0.5))
        layers.append((sstep(0.3, 0.6, tm + 0.25 * (fib - 0.5)) * rev * 0.92, K_SUMI))
    img = ink.composite(paper, layers)
    if title and t > N.T_SEAL:
        sz = int(110 * k); sl = cv2.resize(np.load(os.path.join(HERE, '..', '_shared', 'seal_baimun3.npy')).astype(np.float32), (sz, sz), interpolation=cv2.INTER_AREA)[..., [2, 1, 0, 3]]
        x0, y0 = int(W * 0.84), int(H * 0.60); al = sl[..., 3:4] * eout((t - N.T_SEAL) / 0.1) * np.clip((sl[..., 2:3] - sl[..., 1:2]) * 4, 0, 1)
        img[y0:y0 + sz, x0:x0 + sz] = img[y0:y0 + sz, x0:x0 + sz] * (1 - al + al * sl[..., :3])
    return post.grade(img, sat=1.05, s_curve=0.25, vignette=0.2)

def st_cel(t, v):
    W, H = v.W, v.H; J, i, tau = v.J(t); body, acc = masks(J, v); k = v.k; bi = beat_i(t)
    bgc = PAL[bi % 4]; fg = PAL[(bi + 2) % 4]
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32); cx, cy = J['C']
    rd = np.hypot(xx - cx, yy - cy) / (W * 0.6); pitch = 26 * k; ang = 0.5
    u = (xx * math.cos(ang) + yy * math.sin(ang)) / pitch; w = (-xx * math.sin(ang) + yy * math.cos(ang)) / pitch
    dots = (np.hypot(u - np.round(u), w - np.round(w)) < 0.62 * np.clip(rd * 1.1 - 0.12 + 0.1 * B.pulse(t), 0, 0.75)).astype(np.float32)
    img = np.empty((H, W, 3), np.float32); img[:] = bgc; img = img * (1 - 0.32 * dots[..., None])
    for age, pos, mv, j, kk in bursts(t, v, back=4):                        # 딱딱한 고리와 네모
        r = int((40 + 420 * eout(age / 0.3)) * v.s); th = max(1, int(16 * v.s * max(0, 1 - age / 0.45)))
        if th > 1:
            if j % 2: cv2.circle(img, pos, r, [float(c) for c in C_PAPER], th, cv2.LINE_AA)
            else:
                a = age * 5 + j; pts = np.array([[pos[0] + r * math.cos(a + q * math.pi / 2), pos[1] + r * math.sin(a + q * math.pi / 2)] for q in range(4)], np.int32)
                cv2.polylines(img, [pts], True, [float(c) for c in fg], th, cv2.LINE_AA)
    if tau < 0.1:                                                           # 꺾이는 순간의 집중선
        sl = np.zeros((H, W), np.uint8)
        for n in range(26):
            a = hrand(i, n) * 6.283; r0 = (260 + 160 * hrand(i, n, 2)) * v.s; r1 = W; da = 0.012 + 0.03 * hrand(i, n, 3)
            cv2.fillPoly(sl, [np.array([[cx + r0 * math.cos(a), cy + r0 * math.sin(a)], [cx + r1 * math.cos(a - da), cy + r1 * math.sin(a - da)], [cx + r1 * math.cos(a + da), cy + r1 * math.sin(a + da)]], np.int32)], 255, cv2.LINE_AA)
        img = img + (C_PAPER - img) * (sl.astype(np.float32) / 255)[..., None]
    d = int(20 * k); M = np.float32([[1, 0, d], [0, 1, d]]); sh = cv2.warpAffine(body, M, (W, H)); img *= (1 - 0.45 * sh)[..., None]
    ol = cv2.dilate(body, np.ones((max(3, int(9 * k)) | 1,) * 2, np.uint8))
    img = img * (1 - ol[..., None]) + C_INK * ol[..., None]
    img = img * (1 - body[..., None]) + C_PAPER * body[..., None]
    img = img * (1 - acc[..., None]) + fg * acc[..., None]
    return img

_ov = {}
def _lbl(img, s, p, k, col=(1, 0.95, 0.6)): cv2.putText(_ov['o'], s, (int(p[0]), int(p[1])), cv2.FONT_HERSHEY_SIMPLEX, 0.42 * max(0.8, k * 2), [int(c * 255) for c in col], 1, cv2.LINE_AA)
def st_blue(t, v):
    W, H = v.W, v.H; J, i, tau = v.J(t); body, acc = masks(J, v); k = v.k
    img = np.empty((H, W, 3), np.float32); img[:] = (0.30, 0.13, 0.05); _ov['o'] = np.zeros((H, W, 3), np.uint8)
    g = 60 * v.s; ox = (t * 40 * k) % g
    for x in np.arange(-ox, W, g): cv2.line(img, (int(x), 0), (int(x), H), (0.50, 0.28, 0.12), 1)
    for y in np.arange(0, H, g): cv2.line(img, (0, int(y)), (W, int(y)), (0.50, 0.28, 0.12), 1)
    cnt, _ = cv2.findContours((body > 0.5).astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    img += body[..., None] * np.array((0.22, 0.14, 0.05), np.float32); cv2.drawContours(img, cnt, -1, (1.0, 0.9, 0.55), max(2, int(3 * k)), cv2.LINE_AA)
    for a, b in LINES: cv2.line(img, J[a], J[b], (1, 1, 1), 1, cv2.LINE_AA)
    for kk in ('SL', 'SR', 'EL', 'ER', 'KL', 'KR', 'PL', 'PR', 'HL', 'HR', 'FL', 'FR'): cv2.circle(img, J[kk], max(2, int(9 * v.s)), (0.3, 0.9, 1.0), 1, cv2.LINE_AA)
    for (a, b, c) in [('SL', 'EL', 'HL'), ('SR', 'ER', 'HR'), ('PL', 'KL', 'FL'), ('PR', 'KR', 'FR')]:      # 관절 각도
        a0 = math.degrees(math.atan2(J[a][1] - J[b][1], J[a][0] - J[b][0])); a1 = math.degrees(math.atan2(J[c][1] - J[b][1], J[c][0] - J[b][0]))
        dlt = (a1 - a0 + 180) % 360 - 180
        cv2.ellipse(img, J[b], (int(34 * v.s),) * 2, 0, a0, a0 + dlt, (0.3, 0.9, 1.0), 1, cv2.LINE_AA); _lbl(img, f'{abs(dlt):.0f}', (J[b][0] + int(16 * v.s), J[b][1] - int(14 * v.s)), k)
    for kk in ('HL', 'HR'):
        x, y = J[kk]; L_ = int(26 * v.s); cv2.line(img, (x - L_, y), (x + L_, y), (0.4, 0.5, 1.0), 1); cv2.line(img, (x, y - L_), (x, y + L_), (0.4, 0.5, 1.0), 1)
        _lbl(img, f'x{x:04d} y{y:04d}', (x + L_ + 4, y + 4), k, (0.5, 0.6, 1.0))
    ys, xs = np.where(body > 0.5)
    if len(xs):
        x0, x1, y0, y1 = xs.min() - int(20 * k), xs.max() + int(20 * k), ys.min() - int(20 * k), ys.max() + int(20 * k); c = int(22 * k)
        for (px, py, sx, sy) in [(x0, y0, 1, 1), (x1, y0, -1, 1), (x0, y1, 1, -1), (x1, y1, -1, -1)]:
            cv2.line(img, (px, py), (px + sx * c, py), (1, 1, 1), 1); cv2.line(img, (px, py), (px, py + sy * c), (1, 1, 1), 1)
        _lbl(img, f'POSE {i:02d}  T {t:06.2f}  {N.SEQ[i][1].upper()}', (x0, y0 - int(10 * k)), k, (1, 1, 1))
    for age, pos, mv, j, kk in bursts(t, v, back=3):
        for q in range(2):
            r = int((30 + 70 * q + 200 * eout(age / 0.35)) * v.s); a0 = (age * 200 + q * 40) % 360; f = max(0.0, 1 - age / 0.6)
            for seg in range(0, 360, 45): cv2.ellipse(img, pos, (r, r), a0, seg, seg + 20, (0.75 * f + 0.3, 0.55 * f + 0.13, 0.25 * f + 0.05), 1, cv2.LINE_AA)
    img = np.maximum(img, _ov['o'].astype(np.float32) / 255)
    return img * (1 + 0.5 * math.exp(-tau / 0.05))

NEON = [np.array(c, np.float32) for c in [(1.0, 0.25, 0.9), (1.0, 0.8, 0.1), (0.2, 0.4, 1.0), (0.3, 1.0, 0.5)]]
def neon_fig(t, v, floor=True):
    W, H = v.W, v.H; img = np.zeros((H, W, 3), np.float32); k = v.k; bi = beat_i(t)
    if floor:
        hz = int(H * 0.60)
        for n in range(14):
            y = hz + (H - hz) * (((n + (t * 1.6) % 1) / 14) ** 2); cv2.line(img, (0, int(y)), (W, int(y)), (0.5, 0.12, 0.35), 1, cv2.LINE_AA)
        for n in range(-12, 13): cv2.line(img, (W // 2 + int(n * 30 * k), hz), (W // 2 + int(n * 260 * k), H), (0.5, 0.12, 0.35), 1, cv2.LINE_AA)
        img *= 0.6 + 0.6 * B.pulse(t)
    for q in range(7, -1, -1):                                              # 잔상: 조금씩 늦은 뼈대
        J, i, tau = v.J(t - q * 0.045); col = NEON[(bi + q) % 4] * (1.0 if q == 0 else 0.55 * (1 - q / 8))
        for a, b in LINES: cv2.line(img, J[a], J[b], [float(c) for c in col], max(1, int((7 if q == 0 else 3) * v.s)), cv2.LINE_AA)
        if q == 0:
            c, ux, uy, hp = head_poly(J, v); cv2.polylines(img, [hp], True, [float(c_) for c_ in col], max(1, int(6 * v.s)), cv2.LINE_AA)
            for a, b in LINES: cv2.line(img, J[a], J[b], (1, 1, 1), max(1, int(2 * v.s)), cv2.LINE_AA)
    for age, pos, mv, j, kk in bursts(t, v, back=3):
        r = int((20 + 380 * eout(age / 0.35)) * v.s); f = max(0, 1 - age / 0.5)
        if f > 0: cv2.circle(img, pos, r, [float(c) * f for c in NEON[j % 4]], max(1, int(5 * v.s * f)), cv2.LINE_AA)
    return img
def glow(img, k, a=0.9, b=0.6): return img + a * cv2.GaussianBlur(img, (0, 0), 6 * k) + b * cv2.GaussianBlur(img, (0, 0), 22 * k)
def st_neon(t, v): return post.grade(glow(neon_fig(t, v), v.k) + (0.03, 0.01, 0.02), tonemap='aces', sat=1.1)

_pt = {}
def st_part(t, v):
    W, H = v.W, v.H; k = v.k; n = 7000
    if 'p' not in _pt:
        rng = np.random.default_rng(9); _pt['p'] = (rng.integers(0, len(BONES) + 4, n), rng.random(n), rng.normal(0, 1, n), rng.integers(0, 6, n), rng.random(n) * 6.283, rng.random(n))
    bone, u, off, dl, pa, pr = _pt['p']; _, i, tau = F.pose(t)
    segs = BONES + [('SL', 'PL', 30), ('SR', 'PR', 30), ('SL', 'SR', 40), ('H', 'N', 80)]
    px = np.zeros(n, np.float32); py = np.zeros(n, np.float32)
    for q in range(6):
        J, _, _ = v.J(t - q * 0.03); sel = dl == q
        A = np.array([J[s[0]] for s in segs], np.float32)[bone[sel]]; Bp = np.array([J[s[1]] for s in segs], np.float32)[bone[sel]]; wd = np.array([s[2] for s in segs], np.float32)[bone[sel]]
        dv = Bp - A; ln = np.hypot(dv[:, 0], dv[:, 1])[:, None] + 1e-6; nv = np.stack([-dv[:, 1], dv[:, 0]], 1) / ln
        p = A + dv * u[sel][:, None] + nv * (off[sel] * wd * 0.28 * v.s)[:, None]; px[sel] = p[:, 0]; py[sel] = p[:, 1]
    ex = 150 * v.s * math.exp(-tau / 0.09) * pr ** 2 + 7 * v.s * np.sin(t * 9 + pa)                     # 꺾일 때 터졌다 모인다
    px += ex * np.cos(pa); py += ex * np.sin(pa)
    ok = (px >= 0) & (px < W - 1) & (py >= 0) & (py < H - 1); acc = np.zeros((H, W), np.float32); warm = np.zeros((H, W), np.float32)
    np.add.at(acc, (py[ok].astype(int), px[ok].astype(int)), 1.0); np.add.at(warm, (py[ok].astype(int), px[ok].astype(int)), pr[ok])
    acc = cv2.GaussianBlur(acc, (0, 0), max(0.6, 0.8 * k)); warm = cv2.GaussianBlur(warm, (0, 0), max(0.6, 0.8 * k))
    img = acc[..., None] * np.array((0.25, 0.6, 1.0), np.float32) * 1.6 + warm[..., None] * np.array((1.0, 0.7, 0.4), np.float32) * 1.2
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    img += (0.05 * (np.sin(xx / (38 * k) + t * 3) * np.sin(yy / (38 * k) - t * 2) > 0.92))[..., None] * np.array((0.6, 0.5, 0.3), np.float32)
    return post.grade(glow(img, k, 0.7, 0.5) + (0.03, 0.015, 0.01), tonemap='aces', sat=1.1)

def st_typo(t, v):
    W, H = v.W, v.H; J, i, tau = v.J(t); body, acc = masks(J, v); k = v.k; hb = 0; bi = beat_i(t)
    a, b = PAL[bi % 4], C_PAPER
    if bi % 2: a, b = C_INK, PAL[(bi + 1) % 4]
    word = N.WORDS[hb % len(N.WORDS)]; fr = min(1.0, max(0.0, t - N.last_hit(t)) / 0.3); sc = 1 + 0.35 * (1 - eout(fr / 0.35))
    g = text_img(word, 520 * k); g = cv2.resize(g, None, fx=sc * min(1.0, 0.92 * W / g.shape[1]), fy=sc * min(1.0, 0.92 * W / g.shape[1]), interpolation=cv2.INTER_LINEAR)
    m = np.zeros((H, W), np.float32); paste(m, g, W / 2, H * 0.47)
    band = text_img('GRAVITY   중력 아래   GRAVITY   살아있다는 감각   ', 54 * k); bw = band.shape[1]; sh = int(t * 420 * k) % bw
    row = np.tile(band, (1, W // bw + 3))
    m[int(H * 0.03):int(H * 0.03) + band.shape[0]] = np.maximum(m[int(H * 0.03):int(H * 0.03) + band.shape[0]], row[:, sh:sh + W])
    m[H - int(H * 0.03) - band.shape[0]:H - int(H * 0.03)] = np.maximum(m[H - int(H * 0.03) - band.shape[0]:H - int(H * 0.03)], row[:, bw - sh:bw - sh + W])
    x = np.abs(m - body)                                                     # 몸이 글자를 뒤집는다
    img = a * (1 - x[..., None]) + b * x[..., None]
    return img * (1 - acc[..., None]) + PAL[(bi + 2) % 4] * acc[..., None]

def st_kal(t, v):
    W, H = v.W, v.H; src = neon_fig(t, v, floor=False); bi = beat_i(t); nf = [6, 8, 5, 10][bi % 4]; w = math.pi / nf
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32); dx, dy = xx - W / 2, yy - H / 2
    step = bi + 1 - math.exp(-6 * bfrac(t)); r = np.hypot(dx, dy) * (1 - 0.05 * B.pulse(t)); a = np.arctan2(dy, dx) - 0.35 * step
    a = np.abs(np.mod(a, 2 * w) - w) - math.pi / 2 - w / 2
    cx, cy = v(( N.DW / 2, 560))
    f = cv2.remap(src, (cx + r * np.cos(a)).astype(np.float32), (cy + r * np.sin(a) * 1.0).astype(np.float32), cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
    return post.grade(glow(f, v.k) + (0.03, 0.01, 0.03), tonemap='aces', sat=1.15)

def st_glitch(t, v):
    W, H = v.W, v.H; img = st_cel(t, v) if beat_i(t) % 2 == 0 else st_neon(t, v); q = int(t * 15)
    out = img.copy(); d = int((6 + 26 * B.pulse(t)) * v.k)
    out[..., 2] = np.roll(img[..., 2], d, 1); out[..., 0] = np.roll(img[..., 0], -d, 1)
    for n in range(7):
        y0 = int(hrand(q, n) * H); h = int((8 + 60 * hrand(q, n, 2)) * v.k); sx = int((hrand(q, n, 3) - 0.5) * 260 * v.k)
        out[y0:y0 + h] = np.roll(out[y0:y0 + h], sx, 1)
        if hrand(q, n, 4) > 0.75: out[y0:y0 + h] = 1 - out[y0:y0 + h]
    out *= (0.86 + 0.14 * (np.arange(H) % 3 > 0))[:, None, None]
    return out

def st_grid(t, v0):
    W, H = v0.W, v0.H; out = np.zeros((H, W, 3), np.float32); names = ['cel', 'neon', 'blue', 'ink', 'typo', 'part']; w, h = W // 3, H // 2
    for n, nm in enumerate(names):
        if t - _ST[shot(t)[0]] < n * 0.1: continue                       # 칸이 차례로 켜진다
        vv = View(w, h, 1.9, 0, 60); out[(n // 3) * h:(n // 3) * h + h, (n % 3) * w:(n % 3) * w + w] = STYLES[nm](t - n * 0.05, vv)
    g = max(1, int(3 * v0.k)); out[h - g:h + g] = 0; out[:, w - g:w + g] = 0; out[:, 2 * w - g:2 * w + g] = 0
    return out

STYLES = dict(ink=st_ink, cel=st_cel, blue=st_blue, neon=st_neon, part=st_part, typo=st_typo, kal=st_kal, glitch=st_glitch, grid=st_grid)

