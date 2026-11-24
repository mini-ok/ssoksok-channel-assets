"""〈42번〉 FOLD 42 — 종이를 42번 접으면 달을 지나친다. 세로 숏폼(1080×1920, 약 29초).
세로 눈금은 접은 횟수(로그 눈금): 한 번 접을 때마다 탑이 한 칸(U px) 솟는다. 겹(layer)마다 시차·하늘빛 섞임·흐림이 다르다.
frame(t)은 t의 순수 함수(난수는 씨앗 고정). 숫자는 nums.py에서만 고친다.
"""
import os, sys, math
import numpy as np, cv2, cairo

HERE = os.path.dirname(os.path.abspath(__file__))
os.environ.setdefault('HD_ORIENT', 'v')
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, '..', 'haedal'))
sys.path.insert(0, os.path.join(HERE, '..', 'jamo28'))
os.environ.setdefault('MG_SCALE', os.environ.get('HD_SCALE', '1'))
from mg import clamp, ramp, smooth, expo_out, expo_in_out, back_out, lerp           # noqa: E402
from paper import W, H, SC, Level, composite, grain, hexc, tex                      # noqa: E402
import shapes as S                                                                   # noqa: E402
import nums as N                                                                     # noqa: E402

FPS = N.FPS; DUR = N.DUR
SERIF = 'Noto Serif CJK KR'
DW, DH = 1080, 1920
U, ANCH, TX, TW = N.U, N.ANCH, N.TX, N.TW
CREAM = hexc('#EFE6D2'); INK = hexc('#1C1A18'); WHITE = hexc('#F6F1E6'); VERM = hexc('#D5412A'); TAG = hexc('#FAF5E8')
GREY = hexc('#6B655C')
BOLD = cairo.FONT_WEIGHT_BOLD; REG = cairo.FONT_WEIGHT_NORMAL

# ---------------------------------------------------------------- 시간 → 접기·카메라
_TF = [N.TF[k] for k in range(1, 43)]
def folds_done(t):
    k = 0
    for x in _TF:
        if t >= x: k += 1
        else: break
    return k
def n_top(t):
    k = folds_done(t)
    if k == 0: return 0.0
    return k - 1 + back_out(ramp(t, _TF[k - 1], _TF[k - 1] + 0.16), 2.0)
def kick(t, d=0.3):
    k = folds_done(t)
    return 0.0 if k == 0 else 1 - ramp(t, _TF[k - 1], _TF[k - 1] + d)
def cam_n(t):
    c = N.CAM0
    for k in range(3, 43):
        t0 = _TF[k - 1]
        if t < t0 - 0.03: break
        c += smooth(ramp(t, t0 - 0.03, t0 + 0.37))
    return c
def cam_x(t): return 20 * math.sin(t * 0.55) + 10 * math.sin(t * 1.13 + 1)
def Y(n, t, p=1.0): return ANCH + (cam_n(t) - n) * U * p
def X(x, t, p=1.0): return x + cam_x(t) * (p - 1.0)

LAYERS = [  # name, p, 하늘빛 섞임, 흐림, 그림자 거리, 그림자 세기
    ('deep', 0.22, 0.0, 0.0, 0.0, 0.0),
    ('far', 0.55, 0.55, 2.2, 0.5, 0.16),
    ('mid', 0.80, 0.26, 0.9, 0.9, 0.24),
    ('main', 1.00, 0.0, 0.0, 1.4, 0.30),
    ('tower', 1.00, 0.0, 0.0, 2.2, 0.34),
    ('near', 1.40, 0.0, 2.4, 3.0, 0.26)]
P = {l[0]: l[1] for l in LAYERS}

_SL = [s[0] for s in N.SKY]; _SC = [hexc(s[1]) for s in N.SKY]
def sky_rows(t):
    rows = np.arange(H) / SC
    n = cam_n(t) - (rows - ANCH) / U
    return np.stack([np.interp(n, _SL, [c[i] for c in _SC]) for i in range(3)], 1).astype(np.float32)   # RGB, 줄마다
def sky_at(n): return tuple(float(np.interp(n, _SL, [c[i] for c in _SC])) for i in range(3))
def mixc(a, b, u): return tuple(a[i] + (b[i] - a[i]) * u for i in range(3))


# ---------------------------------------------------------------- 글자
def tw(cr, s, size, weight=BOLD):
    cr.select_font_face(SERIF, cairo.FONT_SLANT_NORMAL, weight); cr.set_font_size(size); return cr.text_extents(s).x_advance
def txt(cr, s, x, y, size, rgb, a=1.0, weight=BOLD, anchor='c'):
    if a <= 0: return
    w = tw(cr, s, size, weight); dx = {'l': 0, 'c': -w / 2, 'r': -w}[anchor]
    cr.move_to(x + dx, y); cr.text_path(s); cr.set_source_rgba(*rgb, a); cr.fill()
def runs(cr, parts, x, y, size, a=1.0, weight=BOLD):
    """한 줄을 색이 다른 조각으로(가운데 정렬)."""
    ws = [tw(cr, s, size, weight) for s, _ in parts]; x0 = x - sum(ws) / 2
    for (s, rgb), w in zip(parts, ws):
        cr.move_to(x0, y); cr.text_path(s); cr.set_source_rgba(*rgb, a); cr.fill(); x0 += w
def slide(cr, s, x, y, size, rgb, u_in, u_out=0.0, weight=BOLD, anchor='c'):
    if u_in <= 0 or u_out >= 1: return
    w = tw(cr, s, size, weight); dx = {'l': 0, 'c': -w / 2, 'r': -w}[anchor]
    cr.save(); cr.rectangle(x + dx - 30, y - size * 1.05, w + 60, size * 1.38); cr.clip()
    off = (1 - expo_out(u_in)) * size * 1.2 - expo_in_out(u_out) * size * 1.2
    cr.move_to(x + dx, y + off); cr.text_path(s); cr.set_source_rgb(*rgb); cr.fill(); cr.restore()
def rrect(cr, x, y, w, h, r):
    r = min(r, w / 2, h / 2); cr.new_sub_path()
    cr.arc(x + w - r, y + r, r, -math.pi / 2, 0); cr.arc(x + w - r, y + h - r, r, 0, math.pi / 2)
    cr.arc(x + r, y + h - r, r, math.pi / 2, math.pi); cr.arc(x + r, y + r, r, math.pi, 1.5 * math.pi); cr.close_path()
def tag(cr, x, y, lines, a=1.0, pad=(26, 18)):
    """작은 종이 꼬리표: lines = [(글, 크기, 굵기, 색)]. (x, y) = 윗변 가운데."""
    a = a * smooth(ramp(y, 400, 470))
    if a <= 0: return 0
    ws = [tw(cr, s, sz, wt) for s, sz, wt, _ in lines]; w = max(ws) + pad[0] * 2
    h = sum(sz * 1.24 for _, sz, _, _ in lines) + pad[1] * 2
    x = clamp(x, w / 2 + 16, DW - w / 2 - 16)
    rrect(cr, x - w / 2, y, w, h, 16); cr.set_source_rgba(*TAG, a); cr.fill()
    yy = y + pad[1]
    for (s, sz, wt, col) in lines:
        yy += sz * 1.0; txt(cr, s, x, yy, sz, col, a, wt); yy += sz * 0.24
    return h


# ---------------------------------------------------------------- 종이 조각(오림) 모양
def rng(k): return np.random.default_rng(4200 + k)

def fillfade(cr, col, ya, yb, a=1.0):
    """위는 불투명, ya → yb 사이에서 옅은 안개로 풀리며 사라지는 칠(띠의 아랫자락)."""
    g = cairo.LinearGradient(0, ya, 0, yb); m = mixc(col, (0.96, 0.97, 1.0), 0.45)
    g.add_color_stop_rgba(0, col[0], col[1], col[2], a); g.add_color_stop_rgba(0.55, m[0], m[1], m[2], a * 0.42); g.add_color_stop_rgba(1, m[0], m[1], m[2], 0.0)
    cr.set_fill_rule(cairo.FILL_RULE_WINDING); cr.set_source(g); cr.fill()

def ridge(cr, t, p, n_top_lvl, amp, seed, col, jag=True, count=13, x0=-140, x1=1220, fade=(300, 700), peak=None):
    """능선 띠: 꼭대기 높이 n_top_lvl 근처에서 오르내리고, 아랫자락은 안개로 사라진다. peak=(x, n) 이면 그 점을 꼭 지난다."""
    r = rng(seed); xs = np.linspace(x0, x1, count); pts = []; y0 = Y(n_top_lvl, t, p)
    for i, x in enumerate(xs):
        pts.append([X(x + r.uniform(-30, 30), t, p), y0 + r.uniform(0, 1) * amp])
    if peak is not None:
        i = int(np.argmin([abs(q[0] - X(peak[0], t, p)) for q in pts])); py = Y(peak[1], t, p)
        pts[i] = [X(peak[0], t, p), py]
        for j, f in ((i - 1, 0.42), (i + 1, 0.50), (i - 2, 0.80), (i + 2, 0.86)):
            if 0 <= j < len(pts): pts[j][1] = py + amp * f + (pts[j][1] - y0) * 0.25
    raw = [list(q) for q in pts]
    if not jag:   # 부드러운 언덕: 점 사이를 코사인으로
        sm = []
        for a, b in zip(pts[:-1], pts[1:]):
            for u in np.linspace(0, 1, 8, endpoint=False):
                v = (1 - math.cos(math.pi * u)) / 2; sm.append([a[0] + (b[0] - a[0]) * u, a[1] + (b[1] - a[1]) * v])
        pts = sm + [pts[-1]]
    yb = y0 + amp + fade[1] + 40
    S.poly(cr, [(pts[0][0], yb)] + [tuple(q) for q in pts] + [(pts[-1][0], yb)]); fillfade(cr, col, y0 + amp + fade[0], y0 + amp + fade[1])
    return raw

def skyline(cr, t, p, lvl, seed, col, wr=(46, 110), hr=260, fade=(260, 640), win=None):
    r = rng(seed); x = -160.0; yb = Y(lvl, t, p); bl = []
    while x < 1240:
        w = r.uniform(*wr); h = r.uniform(0.15, 1.0) ** 1.6 * hr
        cr.new_sub_path(); cr.rectangle(X(x, t, p), yb - h, w + 1, h + fade[1] + 40)
        if r.uniform() < 0.25: cr.rectangle(X(x, t, p) + w * 0.4, yb - h - 26, w * 0.14, 30)
        bl.append((X(x, t, p), yb - h, w)); x += w
    fillfade(cr, col, yb + fade[0], yb + fade[1])
    if win is not None:
        for (bx, by, w) in bl:
            nx = max(1, int((w - 14) / 24))
            for i in range(nx):
                for j in range(int((yb + fade[0] - by - 20) / 34)):
                    if (i * 7 + j * 3 + int(w)) % 4 == 0: continue
                    cr.new_sub_path(); cr.rectangle(bx + 10 + i * 24, by + 16 + j * 34, 11, 17)
        S.fill(cr, win, 0.8)

def tree(cr, x, yb, s, col, trunk, fir=False):
    S.bar(cr, x, yb, x, yb - s * 0.55, s * 0.11); S.fill(cr, trunk)
    if fir:
        for k in range(3): S.poly(cr, [(x - s * (0.42 - k * 0.09), yb - s * (0.3 + k * 0.28)), (x, yb - s * (0.85 + k * 0.28)), (x + s * (0.42 - k * 0.09), yb - s * (0.3 + k * 0.28))])
    else:
        for dx, dy, rr in [(0, -0.82, 0.36), (-0.26, -0.62, 0.27), (0.27, -0.64, 0.28), (0.02, -1.08, 0.25)]: S.circle(cr, x + dx * s, yb + dy * s, rr * s)
    S.fill(cr, col)

def cloud(cr, x, y, s, seed):
    r = rng(seed); n = 6
    for i in range(n):
        u = i / (n - 1); rr = s * (0.20 + 0.20 * math.sin(math.pi * u) + r.uniform(-0.03, 0.05))
        S.circle(cr, x + (u - 0.5) * s * 1.7, y - rr * 0.55, rr)
    rrect(cr, x - s * 1.02, y - s * 0.22, s * 2.04, s * 0.30, s * 0.15)

def pencil(cr, x, y, s):                 # 윗변이 y(굵기 = 높이). 누워 있음
    h = s * 0.16; L = s
    cr.new_sub_path(); cr.rectangle(x - L / 2, y, L * 0.72, h); S.fill(cr, hexc('#E9B63E'))
    cr.new_sub_path(); cr.rectangle(x - L / 2, y + h * 0.36, L * 0.72, h * 0.12); S.fill(cr, hexc('#C99528'))
    rrect(cr, x - L / 2 - L * 0.11, y, L * 0.12, h, h * 0.3); S.fill(cr, hexc('#E58C8C'))
    cr.new_sub_path(); cr.rectangle(x - L / 2 - L * 0.02, y, L * 0.05, h); S.fill(cr, hexc('#B9B4AC'))
    S.poly(cr, [(x + L * 0.22, y), (x + L * 0.42, y + h / 2), (x + L * 0.22, y + h)]); S.fill(cr, hexc('#E8CFA5'))
    S.poly(cr, [(x + L * 0.36, y + h * 0.35), (x + L * 0.42, y + h / 2), (x + L * 0.36, y + h * 0.65)]); S.fill(cr, INK)
    return h

def cup(cr, x, y, s, t):                 # 윗변이 y
    w, h = s * 0.62, s * 0.66
    S.ring(cr, x + w * 0.52, y + h * 0.46, h * 0.17, h * 0.29); S.fill(cr, hexc('#D5412A'))
    rrect(cr, x - w / 2, y, w, h, w * 0.16); S.fill(cr, hexc('#D5412A'))
    S.ellipse(cr, x, y + h * 0.07, w * 0.42, h * 0.055); S.fill(cr, hexc('#5A3A28'))
    for k in (-1, 1):
        pts = [(x + k * w * 0.16 + 9 * math.sin(t * 2.2 + j * 0.9 + k), y - 18 - j * 16) for j in range(6)]
        for (ax, ay), (bx, by) in zip(pts[:-1], pts[1:]): S.bar(cr, ax, ay, bx, by, 7)
    S.fill(cr, WHITE, 0.75)
    return h

def person(cr, x, y, s):                 # 정수리가 y. 단순한 종이 인형(픽토그램)
    hr = s * 0.095
    S.circle(cr, x, y + hr, hr); S.fill(cr, hexc('#E7C3A0'))
    S.poly(cr, [(x - s * 0.13, y + s * 0.23), (x + s * 0.13, y + s * 0.23), (x + s * 0.17, y + s * 0.62), (x - s * 0.17, y + s * 0.62)]); S.fill(cr, VERM)
    S.bar(cr, x - s * 0.15, y + s * 0.26, x - s * 0.24, y + s * 0.55, s * 0.06); S.bar(cr, x + s * 0.15, y + s * 0.26, x + s * 0.24, y + s * 0.55, s * 0.06); S.fill(cr, VERM)
    S.bar(cr, x - s * 0.07, y + s * 0.6, x - s * 0.08, y + s, s * 0.085); S.bar(cr, x + s * 0.07, y + s * 0.6, x + s * 0.08, y + s, s * 0.085); S.fill(cr, hexc('#2F3E5C'))
    return s

def eiffel(cr, x, y, s, col):            # 꼭대기가 y, 높이 s
    def side(k):
        return [(x + k * s * 0.012, y), (x + k * s * 0.03, y + s * 0.42), (x + k * s * 0.075, y + s * 0.68), (x + k * s * 0.24, y + s)]
    L, R = side(-1), side(1)
    cr.new_sub_path(); cr.move_to(*L[0])
    cr.curve_to(L[1][0], L[1][1], L[2][0], L[2][1], L[3][0], L[3][1]); cr.line_to(x - s * 0.15, y + s)
    cr.curve_to(x - s * 0.10, y + s * 0.80, x + s * 0.10, y + s * 0.80, x + s * 0.15, y + s); cr.line_to(*R[3])
    cr.curve_to(R[2][0], R[2][1], R[1][0], R[1][1], R[0][0], R[0][1]); cr.close_path()
    cr.rectangle(x - s * 0.105, y + s * 0.70, s * 0.21, s * 0.035); cr.rectangle(x - s * 0.055, y + s * 0.44, s * 0.11, s * 0.028)
    cr.rectangle(x - s * 0.006, y - s * 0.06, s * 0.012, s * 0.07)
    S.fill(cr, col)

def burj(cr, x, y, s, col, col2):        # 꼭대기가 y, 높이 s
    steps = [(0.0, 0.006), (0.16, 0.012), (0.30, 0.03), (0.44, 0.05), (0.58, 0.072), (0.72, 0.095), (0.86, 0.12), (1.0, 0.14)]
    for k, (a, w) in enumerate(steps[:-1]):
        b = steps[k + 1][0]; off = (k % 3 - 1) * s * 0.012
        cr.new_sub_path(); cr.rectangle(x - s * w + off, y + s * a, s * w * 2, s * (1 - a))
    S.fill(cr, col)
    for k in range(1, 7): cr.new_sub_path(); cr.rectangle(x - s * 0.004 + (k % 3 - 1) * s * 0.03, y + s * (0.3 + k * 0.09), s * 0.008, s * (0.7 - k * 0.09))
    S.fill(cr, col2)

def jet(cr, x, y, s):                    # 옆모습, 오른쪽으로 난다. 윗변 근처가 y
    cy = y + s * 0.16
    for k in (0.10, 0.2): cr.new_sub_path(); cr.rectangle(x - s * 2.2, cy + s * (k - 0.19), s * 1.7, s * 0.035)
    S.fill(cr, WHITE, 0.55)
    S.ellipse(cr, x, cy, s * 0.52, s * 0.085); S.fill(cr, hexc('#F7F5EE'))
    S.poly(cr, [(x - s * 0.50, cy), (x - s * 0.60, cy - s * 0.22), (x - s * 0.46, cy - s * 0.22), (x - s * 0.34, cy - s * 0.03)]); S.fill(cr, VERM)
    S.poly(cr, [(x + s * 0.08, cy), (x - s * 0.20, cy + s * 0.26), (x - s * 0.06, cy + s * 0.26), (x + s * 0.22, cy + s * 0.02)]); S.fill(cr, hexc('#DAD6CC'))
    for k in range(7): S.circle(cr, x + s * (0.34 - k * 0.09), cy - s * 0.02, s * 0.014)
    S.fill(cr, hexc('#33507F'))

def iss(cr, x, y, s):
    cy = y + s * 0.3
    cr.new_sub_path(); cr.rectangle(x - s * 0.75, cy - s * 0.02, s * 1.5, s * 0.04); S.fill(cr, hexc('#C9CCD2'))
    for k in (-0.68, -0.48, 0.48, 0.68):
        cr.new_sub_path(); cr.rectangle(x + k * s - s * 0.075, cy - s * 0.30, s * 0.15, s * 0.26); cr.rectangle(x + k * s - s * 0.075, cy + s * 0.04, s * 0.15, s * 0.26)
    S.fill(cr, hexc('#E0A840'))
    for k in (-0.68, -0.48, 0.48, 0.68):
        for j in range(4): cr.new_sub_path(); cr.rectangle(x + k * s - s * 0.075, cy - s * 0.30 + j * s * 0.075, s * 0.15, s * 0.008); cr.rectangle(x + k * s - s * 0.075, cy + s * 0.07 + j * s * 0.075, s * 0.15, s * 0.008)
    S.fill(cr, hexc('#9A6E1E'))
    rrect(cr, x - s * 0.22, cy - s * 0.06, s * 0.44, s * 0.12, s * 0.05); rrect(cr, x - s * 0.05, cy - s * 0.2, s * 0.1, s * 0.42, s * 0.04); S.fill(cr, hexc('#F0EEE8'))
    for k in (-0.18, 0.18): cr.new_sub_path(); cr.rectangle(x + k * s - s * 0.07, cy + s * 0.10, s * 0.14, s * 0.07)
    S.fill(cr, hexc('#DADDE2'))

def satellite(cr, x, y, s):
    cy = y + s * 0.3
    cr.save(); cr.translate(x, cy); cr.rotate(-0.35)
    for k in (-1, 1): cr.new_sub_path(); cr.rectangle(k * s * 0.42 - s * 0.26, -s * 0.11, s * 0.52, s * 0.22)
    S.fill(cr, hexc('#3E6FD0'))
    for k in (-1, 1):
        for j in range(1, 4): cr.new_sub_path(); cr.rectangle(k * s * 0.42 - s * 0.26 + j * s * 0.13, -s * 0.11, s * 0.008, s * 0.22)
    S.fill(cr, hexc('#1E3F8E'))
    rrect(cr, -s * 0.15, -s * 0.17, s * 0.3, s * 0.34, s * 0.04); S.fill(cr, hexc('#E9D9A6'))
    S.sector(cr, 0, s * 0.2, s * 0.17, math.pi * 1.0, math.pi * 2.0); S.fill(cr, hexc('#F0EEE8'))
    cr.restore()

def moon(cr, x, y, r):
    cr.save(); S.circle(cr, x, y, r); cr.clip()
    cr.rectangle(x - r, y - r, 2 * r, 2 * r); S.fill(cr, hexc('#E4DDCB'))
    q = rng(77)
    for (mx, my, mr) in [(-0.30, -0.28, 0.34), (0.12, -0.42, 0.26), (0.34, -0.05, 0.24), (-0.05, 0.10, 0.30), (-0.42, 0.25, 0.18), (0.2, 0.45, 0.2)]:
        S.ellipse(cr, x + mx * r, y + my * r, mr * r, mr * r * q.uniform(0.7, 0.95), q.uniform(0, 3))
    S.fill(cr, hexc('#BDB5A2'))
    for k in range(24):
        a = q.uniform(0, 2 * math.pi); d = q.uniform(0, 0.92) ** 0.6 * r; cr_ = q.uniform(0.03, 0.09) * r
        cx, cy = x + math.cos(a) * d, y + math.sin(a) * d
        S.circle(cr, cx + cr_ * 0.2, cy + cr_ * 0.22, cr_ * 1.1); S.fill(cr, hexc('#F6F1E2'))
        S.circle(cr, cx, cy, cr_); S.fill(cr, hexc('#A59E8D'))
    # 그늘진 쪽(오른쪽 아래 초승달 모양)
    cr.new_path(); cr.rectangle(x - 2 * r, y - 2 * r, 4 * r, 4 * r); cr.new_sub_path(); cr.arc_negative(x - r * 0.34, y - r * 0.36, r * 1.12, 2 * math.pi, 0)
    cr.set_fill_rule(cairo.FILL_RULE_WINDING); cr.set_source_rgba(0.10, 0.11, 0.20, 0.42); cr.fill()
    cr.restore()

def earth(cr, x, y, r):
    cr.save(); S.circle(cr, x, y, r); cr.clip()
    cr.rectangle(x - r, y - r, 2 * r, 2 * r); S.fill(cr, hexc('#2D6DB8'))
    q = rng(55)
    for k in range(9):
        a = q.uniform(0, 2 * math.pi); d = q.uniform(0.05, 0.85) * r
        cx, cy = x + math.cos(a) * d, y + math.sin(a) * d
        for j in range(5): S.ellipse(cr, cx + q.uniform(-0.2, 0.2) * r, cy + q.uniform(-0.14, 0.14) * r, q.uniform(0.07, 0.2) * r, q.uniform(0.05, 0.13) * r, q.uniform(0, 3))
        S.fill(cr, hexc('#5FA86C') if k % 3 else hexc('#CDB77F'))
    for k in range(11):
        a = q.uniform(0, 2 * math.pi); d = q.uniform(0.0, 0.9) * r; cx, cy = x + math.cos(a) * d, y + math.sin(a) * d
        for j in range(5): S.ellipse(cr, cx + (j - 2) * 0.075 * r, cy + math.sin(j * 1.7) * 0.02 * r, q.uniform(0.07, 0.12) * r, q.uniform(0.035, 0.06) * r, 0.1)
    S.fill(cr, WHITE, 0.9)
    cr.new_path(); cr.rectangle(x - 2 * r, y - 2 * r, 4 * r, 4 * r); cr.new_sub_path(); cr.arc_negative(x - r * 0.25, y - r * 0.3, r * 1.1, 2 * math.pi, 0)
    cr.set_fill_rule(cairo.FILL_RULE_WINDING); cr.set_source_rgba(0.02, 0.04, 0.16, 0.5); cr.fill()
    cr.restore()


# ---------------------------------------------------------------- 이정표 그리기
ICON = {'pencil': 230, 'cup': 200, 'person': 250, 'eiffel': 330, 'burj': 430, 'jet': 190, 'iss': 210, 'geo': 150}
def mark_x(side): return 232 if side == 'L' else 848

def label_lines(m, dark):
    c1 = INK; return [(m[2], 44, BOLD, c1), (m[3], 40, BOLD, c1), (f'{m[4]} · {m[5]}', 32, REG, GREY)]

def level_line(cr, t, lvl, x_to, light):
    y = Y(lvl, t); col = WHITE if light else INK
    x0 = TX + (TW / 2 + 14) * (1 if x_to > TX else -1)
    cr.save(); cr.set_dash([14, 12]); cr.set_line_width(4); cr.set_source_rgba(*col, 0.75)
    cr.move_to(x0, y); cr.line_to(x_to, y); cr.stroke(); cr.restore()


def draw_world(t, L):
    c = cam_n(t); lo, hi = c - 4.4, c + 3.2           # 화면에 걸리는 높이 범위(주 겹 기준)
    far, mid, main, near, glow, ty, deep, stars = (L[k].cr for k in ('far', 'mid', 'main', 'near', 'glow', 'type', 'deep', 'stars'))
    def vis(a, b, m=1.5): return b > lo - m and a < hi + m

    # ---- 책상(0 아래)
    if vis(-6, 0.5):
        y0 = Y(0, t)
        main.new_sub_path(); main.rectangle(-60, y0, 1200, 2400); S.fill(main, hexc('#B88356'))
        main.new_sub_path(); main.rectangle(-60, y0, 1200, 16); S.fill(main, hexc('#D9AE7C'))
        q = rng(1)
        for k in range(16):
            yy = y0 + 60 + k * 62 + q.uniform(-14, 14); main.new_sub_path(); main.rectangle(q.uniform(-60, 500), yy, q.uniform(300, 900), 5)
        S.fill(main, hexc('#A97648'))
    # ---- 책상 위 빛·종이 조각(먼 겹)
    if vis(0, 12):
        q = rng(2)
        for k in range(30):
            lv = q.uniform(0.6, 12.5); x = q.uniform(-40, 1120); s = q.uniform(26, 90); a = q.uniform(0, 3)
            lay = far if k % 3 else mid; p = P['far'] if k % 3 else P['mid']
            col = [hexc('#F9D9A0'), hexc('#F4C7A6'), hexc('#FDF3DC'), hexc('#E9D2A8')][k % 4]
            lay.save(); lay.translate(X(x, t, p), Y(lv, t, p)); lay.rotate(a + t * 0.25 * (1 if k % 2 else -1) * 0.4)
            if k % 2: S.poly(lay, [(-s, -s * 0.3), (s * 0.8, -s * 0.55), (s, s * 0.4), (-s * 0.7, s * 0.5)])
            else: S.circle(lay, 0, 0, s * 0.6)
            S.fill(lay, col); lay.restore()
    # 선반 + 연필 / 커피잔
    for key, drawer in (('pencil', pencil), ('cup', cup)):
        lv = N.mlev(key)
        if not vis(lv - 1.6, lv + 0.3): continue
        m = N.MK[key]; x = mark_x(m[6]); y = Y(lv, t); s = ICON[key]
        hh = drawer(main, x, y, s) if key == 'pencil' else drawer(main, x, y, s, t)
        x0 = -60 if m[6] == 'L' else x - 190
        main.new_sub_path(); main.rectangle(x0, y + hh, (x + 190 - x0) if m[6] == 'L' else 600, 26); S.fill(main, hexc('#C4915F'))
        main.new_sub_path(); main.rectangle(x0, y + hh, (x + 190 - x0) if m[6] == 'L' else 600, 7); S.fill(main, hexc('#DDB382'))
        level_line(ty, t, lv, x + (s * 0.45 if m[6] == 'R' else -s * 0.3) * 0 + (-40 if m[6] == 'R' else 40) * 0 + (x - s * 0.36 if m[6] == 'R' else x + s * 0.55), False)
        tag(ty, x, y + hh + 50, label_lines(m, False))

    # ---- 산·구름(23.5 ~ 27.5) — 위 띠부터 그린다(아래 띠가 앞)
    if vis(22.6, 27.6, 2.5):
        ridge(far, t, P['far'], 25.3, 280, 31, hexc('#A9BDE0'), count=11, fade=(260, 640))
        ridge(mid, t, P['mid'], 25.7, 280, 32, hexc('#8198C6'), count=12, fade=(260, 640))
        lv = N.mlev('everest'); m = N.MK['everest']; x = mark_x('R') - 18
        pts = ridge(main, t, 1.0, lv - 0.25, 420, 33, hexc('#53648F'), count=10, fade=(260, 620), peak=(x, lv))
        py = Y(lv, t)
        for i in range(1, len(pts) - 1):                                      # 종이 접힌 면(밝은 비탈)
            a_, b_, c_ = pts[i - 1], pts[i], pts[i + 1]
            if b_[1] < a_[1] and b_[1] < c_[1]:
                S.poly(main, [tuple(b_), (a_[0] + (b_[0] - a_[0]) * 0.1, a_[1] + 420), (b_[0] + 40, b_[1] + 700)]); fillfade(main, hexc('#6477A6'), b_[1] + 300, b_[1] + 660)
        S.poly(main, [(x, py), (x - 86, py + 150), (x - 52, py + 132), (x - 26, py + 176), (x + 8, py + 128), (x + 40, py + 170), (x + 74, py + 138), (x + 104, py + 176)]); S.fill(main, hexc('#F4F6FA'))
        fr = ridge(main, t, 1.0, lv - 1.45, 260, 35, hexc('#3F4F7E'), count=9, fade=(120, 460))
        level_line(ty, t, lv, x - 8, True)
        tag(ty, x - 4, py + 230, label_lines(m, False))
        q = rng(34)
        for k in range(11):
            lv2 = q.uniform(24.4, 27.2); x2 = q.uniform(-200, 1280); s2 = q.uniform(120, 250)
            lay, p = [(far, P['far']), (mid, P['mid']), (near, P['near'])][k % 3]
            if lay is near: s2 *= 1.7
            xx = (x2 + t * (10 + 6 * (k % 4)) * (1 if k % 2 else -1) + 300) % 1700 - 300
            cloud(lay, X(xx, t, p), Y(lv2, t, p), s2, 340 + k); S.fill(lay, hexc('#FBFBF7'), 0.97)
        lv = N.mlev('jet'); m = N.MK['jet']; s = ICON['jet']; x = mark_x('L') + 14 * math.sin(t * 0.8) + (t - N.TF[27]) * 16; y = Y(lv, t)
        jet(main, x, y, s)
        level_line(ty, t, lv, x + s * 0.6, True)
        tag(ty, mark_x('L'), y + 96, label_lines(m, False))

    # ---- 도시(18.5 ~ 23.5)
    if vis(18.5, 24):
        skyline(far, t, P['far'], 20.7, 21, hexc('#B9D2E6'), hr=300)
        skyline(mid, t, P['mid'], 21.3, 22, hexc('#93B5D5'), hr=340)
        skyline(mid, t, P['mid'], 19.6, 26, hexc('#9DBDD9'), hr=260)
    lv = N.mlev('burj')
    if vis(lv - 2.6, lv + 0.4):
        m = N.MK['burj']; x = mark_x('L'); y = Y(lv, t); s = ICON['burj']
        skyline(main, t, 1.0, lv - (s - 10) / U, 24, hexc('#5E8DB6'), wr=(50, 104), hr=150, fade=(170, 420), win=hexc('#D6E6F3'))
        burj(main, x, y, s, hexc('#F1F5F8'), hexc('#B9CBDA'))
        level_line(ty, t, lv, x + 16, False)
        tag(ty, x + 20, y + s + 40, label_lines(m, False))
    lv = N.mlev('eiffel')
    if vis(lv - 2.4, lv + 0.4):
        m = N.MK['eiffel']; x = mark_x('R'); y = Y(lv, t); s = ICON['eiffel']
        skyline(main, t, 1.0, lv - (s + 30) / U, 23, hexc('#6C9AC0'), wr=(54, 120), hr=110, fade=(170, 420), win=hexc('#DCEAF5'))
        eiffel(main, x, y, s, hexc('#5A4636'))
        level_line(ty, t, lv, x - 20, False)
        tag(ty, x, y + s + 50, label_lines(m, False))

    # ---- 언덕·나무(14 ~ 19)
    if vis(13.5, 19.6):
        for (lay, p, lvl, seed, col, tc) in [(far, P['far'], 18.3, 14, hexc('#C4E0BC'), hexc('#5FA676')), (mid, P['mid'], 17.4, 15, hexc('#A9D3A1'), hexc('#4F9A67')),
                                             (far, P['far'], 16.3, 11, hexc('#B9D9B2'), hexc('#5FA676')), (mid, P['mid'], 15.5, 12, hexc('#98C891'), hexc('#3F8259'))]:
            pts = ridge(lay, t, p, lvl, 150, seed, col, jag=False, fade=(170, 470))
            q = rng(seed + 100)
            for i, pt in enumerate(pts):
                if abs(pt[0] - TX) < 150 or q.uniform() < 0.3: continue
                tree(lay, pt[0], pt[1] + 14, q.uniform(150, 250), tc, hexc('#7A5A3C'), fir=(i % 3 == 0))
    lv = N.mlev('person')
    if vis(lv - 2, lv + 0.3):
        m = N.MK['person']; x = mark_x('L'); y = Y(lv, t); s = ICON['person']
        pts = [(xx, y + s + 6 + 60 * (1 - math.cos((xx - x) / 420))) for xx in range(-80, 1200, 40)]
        S.poly(main, [(-80, y + s + 700)] + pts + [(1180, y + s + 700)]); fillfade(main, hexc('#79B77B'), y + s + 250, y + s + 560)
        tree(main, 900, y + s + 30, 230, hexc('#3F8259'), hexc('#7A5A3C')); tree(main, 760, y + s + 16, 150, hexc('#4F9A67'), hexc('#7A5A3C'), fir=True)
        person(main, x, y, s)
        level_line(ty, t, lv, x + 60, False)
        tag(ty, x, y + s + 60, label_lines(m, False))

    # ---- 높은 하늘: 새털구름
    if vis(27.3, 29.5):
        q = rng(41)
        for k in range(9):
            lv2 = q.uniform(27.6, 29.2); x2 = q.uniform(-100, 1100); w2 = q.uniform(240, 520)
            S.ellipse(far, X(x2, t, P['far']), Y(lv2, t, P['far']), w2, 10 + 8 * (k % 3), -0.08)
        S.fill(far, WHITE, 0.55)

    # ---- 별(28.5부터)
    a_star = smooth(ramp(c, 28.3, 31.0))
    if a_star > 0:
        q = rng(51); ps = 0.30
        for k in range(360):
            x = q.uniform(0, DW); lv2 = q.uniform(27, 60); rr = q.uniform(1.4, 4.2) * (1.6 if k % 23 == 0 else 1); tw_ = 0.75 + 0.25 * math.sin(t * 3 + k)
            yy = ANCH + (c - lv2) * U * ps
            yy = (yy % 2600) - 340
            S.circle(stars, X(x, t, 0.3), yy, rr); S.fill(stars, mixc(WHITE, hexc('#BFD3FF'), (k % 5) / 4), a_star * tw_ * (0.55 + 0.45 * ((k * 7) % 10) / 10))
    # ---- 지구(깊은 겹): 가장자리 → 공
    if c > 28.6:
        top = float(np.interp(c, [28.6, 30, 32, 37, 42], [2000, 1580, 1330, 1420, 1560]))
        R = float(np.interp(c, [28.6, 32, 37, 42], [1900, 1500, 720, 270]))
        ex = 540 + cam_x(t) * -0.6
        for k, a in ((1.05, 0.10), (1.025, 0.16), (1.010, 0.22)): S.ring(glow, ex, top + R, R * 0.995, R * k); S.fill(glow, hexc('#3C8DFF'), a)
        earth(deep, ex, top + R, R)
    # ---- 우주의 시작(100 km): 오로라
    lv = N.mlev('karman')
    if vis(lv - 0.8, lv + 2.4):
        q = rng(61); pa = 0.8
        for k in range(26):
            x = q.uniform(-60, 1140); h = q.uniform(260, 620); wv = q.uniform(26, 60); b = q.uniform(29.95, 30.5)
            xx = X(x, t, pa) + 26 * math.sin(t * 0.9 + k); yb = Y(b, t, pa)
            g = cairo.LinearGradient(0, yb - h, 0, yb)
            cc = hexc('#49E7A0') if k % 4 else hexc('#B06CFF')
            g.add_color_stop_rgba(0, cc[0], cc[1], cc[2], 0.0); g.add_color_stop_rgba(0.55, cc[0], cc[1], cc[2], 0.16); g.add_color_stop_rgba(1, cc[0], cc[1], cc[2], 0.0)
            glow.new_sub_path(); glow.rectangle(xx - wv / 2, yb - h, wv, h); glow.set_source(g); glow.fill()
        m = N.MK['karman']; y = Y(lv, t); x = mark_x('R')
        ty.save(); ty.set_dash([22, 16]); ty.set_line_width(4); ty.set_source_rgba(*WHITE, 0.7); ty.move_to(0, y); ty.line_to(TX - TW / 2 - 14, y); ty.move_to(TX + TW / 2 + 14, y); ty.line_to(DW, y); ty.stroke(); ty.restore()
        tag(ty, x, y + 34, label_lines(m, True))
    # ---- 우주정거장
    lv = N.mlev('iss')
    if vis(lv - 1.5, lv + 0.6):
        m = N.MK['iss']; s = ICON['iss']; y = Y(lv, t); x = mark_x('L') + 12 * math.sin(t * 0.7) + 34
        iss(main, x, y, s)
        level_line(ty, t, lv, x + s * 0.8, True)
        tag(ty, mark_x('L') + 10, y + s * 0.62 + 30, label_lines(m, True))
    # ---- 정지궤도 위성
    lv = N.mlev('geo')
    if vis(lv - 1.5, lv + 0.6):
        m = N.MK['geo']; s = ICON['geo']; y = Y(lv, t); x = mark_x('R') + 8 * math.sin(t * 0.9)
        satellite(main, x, y, s)
        level_line(ty, t, lv, x - s * 0.72, True)
        tag(ty, mark_x('R') - 24, y + s * 0.62 + 34, label_lines(m, True))
    # ---- 달
    lv = N.mlev('moon')
    if vis(lv - 1.8, lv + 1.2):
        m = N.MK['moon']; r = 226; x = 240; y = Y(lv, t)
        for k, a in ((1.22, 0.05), (1.10, 0.08), (1.04, 0.12)): S.ring(glow, x, y, r * 0.99, r * k); S.fill(glow, hexc('#FFF4D6'), a)
        moon(main, x, y, r)
        ty.save(); ty.set_dash([14, 12]); ty.set_line_width(4); ty.set_source_rgba(*WHITE, 0.8); ty.move_to(TX - TW / 2 - 14, y); ty.line_to(x + r + 8, y) if x + r + 8 < TX - TW / 2 - 14 else None; ty.stroke(); ty.restore()
        tag(ty, x, y + r + 30, label_lines(m, True))


def draw_tower(t, cr, ty):
    nt = n_top(t); yb = Y(0, t); yt = Y(nt, t); k = folds_done(t); kk = kick(t, 0.22)
    yt = min(yt, yb - 7)                                      # 한 장일 때도 보이게
    w = TW * (1 - 0.08 * kk)
    yb2 = min(yb, DH + 80)
    rrect(cr, TX - w / 2, yt, w, yb2 - yt + (40 if yb2 < yb else 0), 20 if yb - yt > 40 else 3)
    cr.rectangle(TX - w / 2, min(yt + 24, yb2), w, max(0, yb2 - yt - 24)); S.fill(cr, hexc('#F6F0E2'))
    # 옆면 그늘
    cr.new_sub_path(); cr.rectangle(TX + w / 2 - 16, yt + 14, 16, max(0, yb2 - yt - 14)); S.fill(cr, hexc('#DCD3BF'))
    # 종이 결(낱장이 쌓인 선): 세계에 고정
    cr.save(); cr.rectangle(TX - w / 2, yt + 10, w - 16, max(0, yb2 - yt - 10)); cr.clip()
    c = cam_n(t); step = 15.0
    j0 = int(math.floor((ANCH + (c - 0) * U - DH - 40) / step)); j1 = int(math.ceil((ANCH + c * U + 40) / step))
    for j in range(max(j0, 1), j1):
        yy = yb - j * step
        if yy < yt + 8 or yy > DH + 20: continue
        cr.new_sub_path(); cr.rectangle(TX - w / 2, yy, w, 2.2 if j % 4 else 3.4)
    S.fill(cr, hexc('#D3C8B0'), 0.75)
    cr.restore()
    # 접은 자리 + 번호
    for f in range(max(1, int(c - 5)), k + 1):
        yy = Y(f, t)
        if f > nt + 0.02 or yy > DH + 30 or yy < -40: continue
        if f < k or nt >= k - 0.02:
            cr.new_sub_path(); cr.rectangle(TX - w / 2, yy - 3 + (24 if f == k else 0) * 0, w, 6); S.fill(cr, VERM, 0.85 if f == k else 0.5)
        if f < k: txt(cr, str(f), TX - 8, yy + 52, 36, hexc('#A89F8C'), 1.0, BOLD)
    # ×2
    if k >= 1:
        u = ramp(t, _TF[k - 1], _TF[k - 1] + 0.34)
        if u < 1:
            a = 1 - smooth(ramp(u, 0.55, 1.0)); s = 78 * (0.6 + 0.4 * back_out(ramp(u, 0, 0.45)))
            light = c > 27.2
            txt(ty, '×2', TX + TW / 2 + 92, yt + 30 - 46 * expo_out(u), s, VERM if not light else hexc('#FF7A5C'), a, BOLD)


def draw_hud(t, ty, a=1.0):
    if a <= 0: return
    k = folds_done(t); h = N.thick(k); kk = kick(t, 0.26)
    rrect(ty, 120, 92, 840, 300, 34); ty.set_source_rgba(*TAG, a); ty.fill()
    num = str(k); size = 170 * (1 + 0.10 * kk * kk)
    wn = tw(ty, num, size)
    wl = max(tw(ty, 'folds', 54), tw(ty, '번 접음', 50)); tot = wn + 26 + wl; x0 = 540 - tot / 2
    txt(ty, num, x0, 252 + (size - 170) * 0.3, size, INK, a, BOLD, 'l')
    txt(ty, 'folds', x0 + wn + 26, 182, 54, INK, a, BOLD, 'l'); txt(ty, '번 접음', x0 + wn + 26, 246, 50, INK, a, BOLD, 'l')
    runs(ty, [(N.fmt_metric(h), VERM), ('   ' + N.fmt_imperial(h), GREY)], 540, 350, 60, a, BOLD)


# ---------------------------------------------------------------- 첫 물음(0 ~ 2.95): 종이가 반으로 접힌다
HOOK_FOLDS = [(0.55, 'v'), (1.15, 'h'), (1.75, 'v')]
WOOD = hexc('#B88356')
def draw_hook(t, L):
    bg, main, ty = L['bg'].cr, L['main'].cr, L['type'].cr
    u_out = smooth(ramp(t, N.T_XF[0], N.T_XF[1])); dy = 260 * u_out; a = 1 - u_out
    q = rng(3)                                                        # 책상 나뭇결(위에서 본 책상)
    for k in range(34):
        yy = 20 + k * 57 + q.uniform(-16, 16); bg.new_sub_path(); bg.rectangle(q.uniform(-200, 500), yy, q.uniform(320, 1000), 5)
    S.fill(bg, hexc('#A97648'))
    for k in range(4): bg.new_sub_path(); bg.rectangle(-10, 430 + k * 480, 1100, 4)
    S.fill(bg, hexc('#96673D'))
    x0, y0, x1, y1 = 260.0, 640.0, 820.0, 1430.0
    done = 0; mv = None
    for tf, ax in HOOK_FOLDS:
        u = ramp(t, tf, tf + 0.34)
        if u >= 1:
            if ax == 'v': y0 = (y0 + y1) / 2
            else: x1 = (x0 + x1) / 2
            done += 1
        elif u > 0: mv = (ax, expo_in_out(u)); break
    ox = lerp(0, 150, smooth(ramp(t, 0.5, 2.1))); oy = lerp(0, -130, smooth(ramp(t, 0.5, 2.1))) + dy
    paper_c, back_c = hexc('#FBF8F0'), hexc('#EDE6D4')
    def R(ax0, ay0, ax1, ay1, col, lay=main):
        lay.new_sub_path(); lay.rectangle(ax0 + ox, ay0 + oy, ax1 - ax0, ay1 - ay0); S.fill(lay, col)
    lay2 = L['tower'].cr                                             # 접히는 날개는 한 겹 위(그림자)
    fx0, fy0, fx1, fy1 = x0, y0, x1, y1                              # 가만히 있는 반쪽
    if mv is not None:
        if mv[0] == 'v': fy0 = (y0 + y1) / 2
        else: fx1 = (x0 + x1) / 2
    for j in range(min(2 ** done - 1, 4), 0, -1): R(fx0 + 5 * j, fy0 + 5 * j, fx1 + 5 * j, fy1 + 5 * j, hexc('#D9D0BC') if j % 2 else hexc('#F1EBDC'))
    R(fx0, fy0, fx1, fy1, paper_c)
    if mv is not None:
        ax, u = mv; cs = math.cos(math.pi * u); flip = u > 0.5; bul = 0.07 * math.sin(math.pi * u)
        if ax == 'v':
            ym = fy0; hh = fy1 - fy0; ye = ym - hh * cs; ex = (x1 - x0) * bul
            S.poly(lay2, [(x0 + ox, ym + oy), (x1 + ox, ym + oy), (x1 + ex + ox, ye + oy), (x0 - ex + ox, ye + oy)]); S.fill(lay2, back_c if flip else paper_c)
        else:
            xm = fx1; hw = fx1 - fx0; xe = xm + hw * cs; ey = (y1 - y0) * bul
            S.poly(lay2, [(xm + ox, y0 + oy), (xm + ox, y1 + oy), (xe + ox, y1 + ey + oy), (xe + ox, y0 - ey + oy)]); S.fill(lay2, back_c if flip else paper_c)
    # 물음 카드(영어 위, 한글 아래, 비슷한 크기) — 뒤에 접기 카운터 카드로 이어진다
    rrect(ty, 120, 92, 840, lerp(440, 300, u_out), 34); S.fill(ty, TAG)
    e = 0.94 + 0.06 * expo_out(ramp(t, 0, 0.4))
    ty.save(); ty.translate(540, 300); ty.scale(e, e); ty.translate(-540, -300)
    txt(ty, 'Fold a sheet of paper', 540, 206, 74, INK, a)
    txt(ty, '42 times.', 540, 316, 100, VERM, a)
    runs(ty, [('종이 한 장을 ', INK), ('42번', VERM), (' 접으면?', INK)], 540, 448, 70, a); ty.restore()
    # 두께 ×2 → ×4 → ×8
    n_ = done + (1 if (mv and mv[1] > 0.5) else 0)
    if n_ >= 1:
        tf = HOOK_FOLDS[n_ - 1][0] + 0.17; u = ramp(t, tf, tf + 0.3)
        txt(ty, f'×{2 ** n_}', 540, 1640 + dy, 150 * (0.7 + 0.3 * back_out(u)), WHITE, a)
        txt(ty, 'thickness · 두께', 540, 1722 + dy, 50, WHITE, a * smooth(ramp(t, 0.8, 1.1)))


# ---------------------------------------------------------------- 실제 기록(T_TWIST ~)
def draw_twist(t, L):
    main, ty = L['main'].cr, L['type'].cr; t0 = N.T_TWIST
    slide(ty, 'The real-world record', 540, 300, 64, INK, ramp(t, t0 + 0.35, t0 + 0.8))
    slide(ty, '실제 세계 기록은', 540, 386, 60, INK, ramp(t, t0 + 0.45, t0 + 0.9))
    u = ramp(t, t0 + 0.8, t0 + 1.25)
    if u > 0:
        s = 330 * (0.7 + 0.3 * back_out(u)); wn = tw(ty, '12', s); wl = max(tw(ty, 'folds', 80), tw(ty, '번', 76)); x0 = 540 - (wn + 30 + wl) / 2
        txt(ty, '12', x0, 740, s, VERM, min(1, u * 2), BOLD, 'l')
        txt(ty, 'folds', x0 + wn + 30, 630, 80, INK, min(1, u * 2), BOLD, 'l'); txt(ty, '번', x0 + wn + 30, 728, 76, INK, min(1, u * 2), BOLD, 'l')
    # 12번 접힌 종이 뭉치(옆모습): 겹겹이 말린 선
    v = expo_out(ramp(t, t0 + 0.5, t0 + 1.1))
    if v > 0:
        cx, cy = 540, 1060 + (1 - v) * 80; ww, hh = 430, 210
        rrect(main, cx - ww / 2, cy - hh / 2, ww, hh, 70); S.fill(main, hexc('#FBF8F0'))
        cr = main; cr.save(); rrect(cr, cx - ww / 2, cy - hh / 2, ww, hh, 70); cr.clip()
        for j in range(1, 9):
            d = j * 11.5; cr.new_path(); rrect(cr, cx - ww / 2 + d, cy - hh / 2 + d, ww - 2 * d + 240, hh - 2 * d, max(6, 70 - d)); cr.set_line_width(3.2); cr.set_source_rgba(*hexc('#B9AE96'), 0.9); cr.stroke()
        cr.restore()
        txt(ty, '4,096 layers · 4,096겹', cx, cy + hh / 2 + 84, 46, GREY, v, BOLD)
    slide(ty, 'Britney Gallivan, 2002 —', 540, 1380, 48, INK, ramp(t, t0 + 1.5, t0 + 1.9))
    slide(ty, '1.2 km (4,000 ft) of tissue paper', 540, 1444, 48, INK, ramp(t, t0 + 1.6, t0 + 2.0))
    slide(ty, '2002년, 1.2km 길이 화장지로 세운 기록', 540, 1520, 44, INK, ramp(t, t0 + 1.7, t0 + 2.1))
    slide(ty, 'Paper assumed 0.1 mm thick.  종이 두께 0.1mm 기준.', 540, 1700, 32, GREY, ramp(t, t0 + 2.2, t0 + 2.6), 0, REG)


# ---------------------------------------------------------------- 합성
def tinted(rgba, f, sky):
    if f <= 0: return rgba
    out = rgba.copy(); out[..., :3] = rgba[..., :3] * (1 - f) + sky[:, None, ::-1] * rgba[..., 3:4] * f
    return out
def blur_level(rgba, s):
    if s <= 0 or rgba[..., 3].max() < 1e-4: return rgba
    return cv2.GaussianBlur(rgba, (0, 0), s * SC)
def additive(base, rgba, bloom=0.0, k=1.0):
    if rgba[..., 3].max() < 1e-4: return base
    add = rgba[..., :3] * k
    if bloom > 0: add = add + cv2.GaussianBlur(rgba[..., :3], (0, 0), bloom * SC) * 1.4 + cv2.GaussianBlur(rgba[..., :3], (0, 0), bloom * 3 * SC) * 0.7
    return np.clip(base + add, 0, 1.4)

NAMES = [l[0] for l in LAYERS] + ['stars', 'glow', 'type']
def paper_bg(): return np.array(CREAM[::-1], np.float32) * tex()[..., None]

def world_img(t, samples):
    acc = {}
    for si in range(samples):
        tt = t + ((si + 0.5) / samples - 0.5) * 0.5 / FPS if samples > 1 else t
        L = {n: Level() for n in NAMES}
        draw_world(tt, L); draw_tower(tt, L['tower'].cr, L['type'].cr)
        a_hud = smooth(ramp(tt, N.T_XF[0] + 0.1, N.T_XF[1] + 0.1))
        draw_hud(tt, L['type'].cr, a_hud)
        if tt > N.T_MOON + 0.5:
            ty = L['type'].cr
            u = ramp(tt, N.T_MOON + 0.5, N.T_MOON + 0.95); e = back_out(u, 1.2)
            ty.save(); ty.translate(540, 1446); ty.scale(0.86 + 0.14 * e, 0.86 + 0.14 * e); ty.translate(-540, -1446)
            rrect(ty, 150, 1326, 780, 250, 34); ty.set_source_rgba(*TAG, min(1, u * 3)); ty.fill()
            runs(ty, [('Past the ', INK), ('Moon.', VERM)], 540, 1434, 88, min(1, u * 3))
            runs(ty, [('달', VERM), ('을 지나칩니다.', INK)], 540, 1532, 84, min(1, u * 3)); ty.restore()
        for n in NAMES:
            a = L[n].array(); acc[n] = a if n not in acc else acc[n] + a
    for n in acc: acc[n] /= samples
    sky = sky_rows(t)
    base = np.repeat(sky[:, None, ::-1], W, 1) * tex()[..., None]
    base = additive(base, acc['stars'], bloom=4.0, k=1.0)
    base = composite(base, acc['deep'], 0, 0, edge=0.4)
    base = additive(base, acc['glow'], bloom=5.0, k=1.0)
    for n, p, tint, bl, dep, sh in LAYERS[1:]:
        base = composite(base, blur_level(tinted(acc[n], tint, sky), bl), dep, sh)
    base = composite(base, acc['type'], 0.5, 0.22)
    return np.clip(base, 0, 1)

def card_img(t, samples, which):
    acc = {}
    for si in range(samples):
        tt = t + ((si + 0.5) / samples - 0.5) * 0.5 / FPS if samples > 1 else t
        L = {n: Level() for n in ('bg', 'main', 'tower', 'type')}
        (draw_hook if which == 'hook' else draw_twist)(tt, L)
        for n in L:
            a = L[n].array(); acc[n] = a if n not in acc else acc[n] + a
    for n in acc: acc[n] /= samples
    base = paper_bg() if which != 'hook' else np.array(WOOD[::-1], np.float32) * tex()[..., None]
    base = composite(base, acc['bg'], 0, 0, edge=0.5)
    base = composite(base, acc['main'], 1.2, 0.34); base = composite(base, acc['tower'], 2.6, 0.38)
    base = composite(base, acc['type'], 0.5, 0.22 if which == 'hook' else 0.0, edge=1.0 if which == 'hook' else 0.0)
    return np.clip(base, 0, 1)

def frame(t, samples=3):
    if t < N.T_XF[0]: return card_img(t, samples, 'hook')
    if t < N.T_XF[1]:
        u = smooth(ramp(t, N.T_XF[0], N.T_XF[1])); return card_img(t, samples, 'hook') * (1 - u) + world_img(t, samples) * u
    if t < N.T_TWIST: return world_img(t, samples)
    u = expo_in_out(ramp(t, N.T_TWIST, N.T_TWIST + 0.5))
    b = card_img(t, samples, 'twist')
    if u >= 1: return b
    a = world_img(t, 1)                                         # 크림 종이가 위에서 내려 덮는다
    yc = int(H * u); out = a.copy(); out[:yc] = b[:yc]
    sh = np.clip(1 - (np.arange(H) - yc) / (60 * SC), 0, 1) * (np.arange(H) >= yc); out *= (1 - 0.35 * sh)[:, None, None]
    return out


_VIG = None
def vignette_mask():
    global _VIG
    if _VIG is None:
        y, x = np.mgrid[0:H, 0:W].astype(np.float32); r = np.hypot((x - W / 2) / (W / 2), (y - H / 2) / (H / 2))
        _VIG = (1 - 0.22 * np.clip(r - 0.5, 0, 1) ** 1.4)[..., None].astype(np.float32)
    return _VIG

CREDIT = ['Created & Coded by L.S.M.', '허상공방 虛像工房 Project']
T_END = N.T_END; T_SEAL = T_END + 0.4
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
    u = smooth(ramp(t, T_END, T_END + 0.6))
    img = img * (1 - u) + paper_bg() * u
    if t < T_SEAL: return img
    tm, seal, xs, ys, sz = credit_layer()
    a1 = smooth(ramp(t, T_SEAL, T_SEAL + 0.2))
    red = np.clip((seal[..., 2:3] - seal[..., 1:2]) * 4, 0, 1)
    al = seal[..., 3:4] * a1 * red
    sub = img[ys:ys + sz, xs:xs + sz]; img[ys:ys + sz, xs:xs + sz] = sub * (1 - al + al * seal[..., :3])
    a2 = smooth(ramp(t, T_SEAL + 0.4, T_SEAL + 1.1)); k = (tm * a2 * 0.92)[..., None]
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
        print('wrote', t, folds_done(t), round(cam_n(t), 2), flush=True)
