"""〈지구가 1cm 구슬이라면〉 다시 만들기 — 칠판 분필 그림(지운 자국, 손 떨림 선, 분필 가루 결), 소리는 분필 긁는 소리·발걸음·업라이트 피아노.
사실(NASA): 해 지름 1,392,700 km, 지구 12,742 km, 달 3,474.8 km, 지구-해 149,597,871 km, 지구-달 384,400 km.
지구 = 1 cm로 줄이면 달 2.7 mm·30 cm 거리, 해 지름 1.09 m·117 m 거리. 축구장 길이 약 105 m.
"""
import math, numpy as np, cv2, cairo
from base import *
import sfx as S

E = 12742.0
SUN_D = 1392700 / E; AU = 149597871 / E; MOON_D = 3474.8 / E; MOON = 384400 / E          # cm
CAMS = [(0.0, 0, 120), (3.8, 0, 120), (6.4, 15, 25), (9.4, 15, 25), (14.4, 6300, 0.095), (18.8, 6300, 0.095), (21.2, AU + 25, 3.6)]
SCY = 1060
WHITE = (0.94, 0.94, 0.90); BLUE = (0.55, 0.78, 0.95); YEL = (0.98, 0.86, 0.45); PINK = (0.95, 0.62, 0.70); GRN = (0.65, 0.88, 0.62)
T_WALK = 9.6; T_PITCH = 13.0; T_SUN = 14.6; T_ZOOM = 19.0; T_CODA = 23.2

_r = np.random.default_rng(21)
def _noise(scales):
    return sum(cv2.resize(_r.standard_normal((max(2, H // d), max(2, W // d))).astype(np.float32), (W, H), interpolation=cv2.INTER_CUBIC) * w for d, w in scales)
_n = _noise(((60, 1.0), (180, 1.2))); _n = (_n - _n.min()) / (_n.max() - _n.min())
BOARD = np.stack([0.17 + 0.05 * _n, 0.21 + 0.05 * _n, 0.15 + 0.04 * _n], -1).astype(np.float32)            # BGR
_s = _noise(((1, 1.0), (2, 0.6))); _s = (_s - _s.min()) / (_s.max() - _s.min())
_str = cv2.GaussianBlur(_r.random((H, W)).astype(np.float32), (0, 0), sigmaX=0.6 * SC, sigmaY=4 * SC)
CHALK = np.clip(0.55 + 0.8 * _s * (0.6 + 0.6 * _str), 0, 1)                  # 분필 가루 결

def cam(t):
    for (t0, y0, s0), (t1, y1, s1) in zip(CAMS, CAMS[1:]):
        if t <= t1:
            u = 0.5 - 0.5 * math.cos(math.pi * ramp(t, t0, t1))
            s = math.exp(lerp(math.log(s0), math.log(s1), u))
            f = (math.log(s) - math.log(s0)) / (math.log(s1) - math.log(s0)) if abs(s1 - s0) > 1e-9 else u
            return lerp(y0, y1, f), s
    return CAMS[-1][1:]

def wl(cr, pts, col, a, w=4.0, seed=0, jit=1.6):
    """손 떨림 분필 선."""
    if a <= 0: return
    r = np.random.default_rng(seed); P = np.asarray(pts, float)
    dense = []
    for p, q in zip(P, P[1:]):
        n = max(2, int(np.hypot(*(q - p)) / 8))
        for k in range(n): dense.append(p + (q - p) * k / n)
    dense.append(P[-1]); D = np.array(dense)
    D = D + np.cumsum(r.normal(0, jit * 0.35, D.shape), 0) * 0.3 + r.normal(0, jit * 0.3, D.shape)
    cr.set_source_rgba(*col, a); cr.set_line_width(w); cr.set_line_cap(cairo.LINE_CAP_ROUND)
    cr.move_to(*D[0]); [cr.line_to(*d) for d in D[1:]]; cr.stroke()

def circ(cr, x, y, r, col, a, w=4, seed=0, fill=None, fa=0.0, prog=1.0):
    n = max(24, int(r * 0.8)); th = np.linspace(-math.pi / 2, -math.pi / 2 + 6.283 * prog * 1.04, n)
    rr = np.random.default_rng(seed)
    pts = [(x + r * (1 + rr.normal(0, 0.01)) * math.cos(a_), y + r * (1 + rr.normal(0, 0.01)) * math.sin(a_)) for a_ in th]
    if fill and fa > 0:
        for k in range(int(r / 3) + 2):                       # 비스듬한 분필 칠
            yy = y - r + k * 2 * r / (int(r / 3) + 1); hw = math.sqrt(max(0, r * r - (yy - y) ** 2))
            wl(cr, [(x - hw, yy + 4), (x + hw, yy - 4)], fill, fa * 0.55, w=max(2, min(6, r / 3)), seed=seed + k, jit=0.6)
    wl(cr, pts, col, a, w, seed, jit=1.0)

def arrow_dim(cr, x, y0, y1, col, a, seed=0):
    wl(cr, [(x, y0), (x, y1)], col, a, 3, seed)
    for yy, d in ((y0, 1), (y1, -1)): wl(cr, [(x - 12, yy + d * 16), (x, yy), (x + 12, yy + d * 16)], col, a, 3, seed + 3)

def person(cr, x, yb, h, col, a, seed=0):
    wl(cr, [(x, yb - h * 0.15), (x, yb - h * 0.55)], col, a, 5, seed)
    wl(cr, [(x - h * 0.12, yb), (x, yb - h * 0.15), (x + h * 0.12, yb)], col, a, 5, seed + 1)
    wl(cr, [(x - h * 0.16, yb - h * 0.32), (x, yb - h * 0.5), (x + h * 0.16, yb - h * 0.32)], col, a, 5, seed + 2)
    circ(cr, x, yb - h * 0.64, h * 0.09, col, a, 5, seed + 3)

def draw(t):
    cy, s = cam(t)
    Y = lambda ycm: SCY + (cy - ycm) * s
    sf, cr = surf()
    # 지구
    ey = Y(0); er = max(5, 0.5 * s)
    circ(cr, 540, ey, er, BLUE, ramp(t, 0.3, 1.0), w=4 if er > 10 else 3, seed=1, fill=BLUE if er > 8 else None, fa=ramp(t, 0.8, 1.4))
    if s > 60:
        a = ramp(t, 1.0, 1.5) * (1 - ramp(t, 3.8, 4.4))
        arrow_dim(cr, 540 + er + 40, ey - er, ey + er, WHITE, a, 7)
        txt(cr, '1 cm', 540 + er + 70, ey + 12, 44, WHITE, a, fam=BOLD, anchor='l')
        txt(cr, 'Earth · 지구', 540, ey + er + 80, 40, BLUE, ramp(t, 1.2, 1.7) * (1 - ramp(t, 3.8, 4.4)), fam=BOLD)
    # 달
    ma = ramp(t, 4.4, 5.2) * (1 - ramp(t, 11.0, 12.0))
    if ma > 0:
        my = Y(MOON); mr = max(3.5, MOON_D / 2 * s)
        circ(cr, 540, my, mr, WHITE, ma, 3, seed=5, fill=WHITE if mr > 6 else None, fa=ma)
        da = ramp(t, 5.6, 6.6) * (1 - ramp(t, 9.6, 10.4))
        arrow_dim(cr, 700, my, ey, WHITE, da, 11)
        txt(cr, '30 cm', 730, (my + ey) / 2, 44, WHITE, da, fam=BOLD, anchor='l')
        txt(cr, 'Moon 2.7 mm · 달', 600, my - 30, 36, WHITE, da, fam=BOLD, anchor='l')
    # 걷기: 발자국과 거리
    if t > T_WALK:
        walk = smooth(ramp(t, T_WALK, T_SUN - 0.2)); dist = AU * walk
        for k in range(int(dist / 650)):
            yk = Y(k * 650 + 200)
            if -40 < yk < H / SC + 40:
                side = -1 if k % 2 else 1; fx = 540 + side * 18
                cr.save(); cr.translate(fx, yk); cr.scale(0.6, 1); circ(cr, 0, 0, 12, WHITE, 0.6, 3, seed=100 + k); cr.restore()
        if t < T_ZOOM:
            a = ramp(t, T_WALK, T_WALK + 0.4)
            m = dist / 100
            txt(cr, f'{max(0.3, m):,.0f} m' if m >= 10 else f'{max(0.15, m):,.1f} m', 540, 1780, 76, YEL, a, fam=BLK)
            txt(cr, 'from Earth · 지구에서', 540, 1840, 34, YEL, a, fam=BOLD)
    # 축구장(105 × 68 m)
    pa = ramp(t, T_PITCH, T_PITCH + 1.2) * (1 - ramp(t, T_ZOOM, T_ZOOM + 0.6))
    if pa > 0:
        L, Wd = 10500, 6800; y0, y1 = Y(0), Y(L); hw = Wd / 2 * s
        prog = ramp(t, T_PITCH, T_PITCH + 1.4)
        pts = [(540 - hw, y0), (540 + hw, y0), (540 + hw, y1), (540 - hw, y1), (540 - hw, y0)]
        wl(cr, pts[:2 + int(prog * 3)], GRN, pa, 4, 31)
        if prog > 0.8:
            ym = Y(L / 2); wl(cr, [(540 - hw, ym), (540 + hw, ym)], GRN, pa, 3, 32); circ(cr, 540, ym, 915 * s, GRN, pa, 3, 33)
        txt(cr, 'Soccer pitch ~105 m', 540, Y(L * 0.25) - 10, 36, GRN, pa * ramp(t, T_PITCH + 1.2, T_PITCH + 1.7), fam=BOLD)
        txt(cr, '축구장 길이 약 105m', 540, Y(L * 0.25) + 34, 32, GRN, pa * ramp(t, T_PITCH + 1.2, T_PITCH + 1.7), fam=BOLD)
    # 해
    sa = ramp(t, T_SUN - 0.6, T_SUN + 0.4)
    if sa > 0:
        sy = Y(AU); sr = max(6, SUN_D / 2 * s)
        circ(cr, 540, sy, sr, YEL, sa, 5 if sr > 20 else 3, seed=41, fill=YEL, fa=sa * 0.9)
        if sr > 40:
            for k in range(12):
                a_ = k * 6.283 / 12 + 0.2
                wl(cr, [(540 + (sr + 18) * math.cos(a_), sy + (sr + 18) * math.sin(a_)), (540 + (sr + 60) * math.cos(a_), sy + (sr + 60) * math.sin(a_))], YEL, sa, 4, 50 + k)
        la = ramp(t, T_SUN + 0.4, T_SUN + 1.0) * (1 - ramp(t, T_ZOOM, T_ZOOM + 0.4))
        txt(cr, 'Sun · 해', 540 + sr + 24, sy + 14, 42, YEL, la, fam=BLK, anchor='l')
        za = ramp(t, T_ZOOM + 1.6, T_ZOOM + 2.4)
        if za > 0:
            person(cr, 540 + sr + 170, sy + sr, 170 * s, WHITE, za, 61)
            txt(cr, 'you · 1.7 m', 540 + sr + 170, sy + sr + 50, 34, WHITE, za, fam=BOLD)
            arrow_dim(cr, 540 - sr - 50, sy - sr, sy + sr, WHITE, za, 63)
            txt(cr, '1.1 m', 540 - sr - 70, sy + 12, 44, YEL, za, fam=BLK, anchor='r')
            txt(cr, 'Earth: 1 cm, 117 m that way ↓', 540, min(1840, sy + sr + 150), 32, BLUE, za, fam=BOLD)
            txt(cr, '지구는 1cm, 117m 아래', 540, min(1885, sy + sr + 192), 30, BLUE, za, fam=BOLD)
    a = arr(sf)
    a = a * CHALK[..., None]
    img = BOARD * (1 - a[..., 3:4]) + a[..., :3]
    return img

def sound(path):
    m = S.Mix(EP['DUR'], 81); tc = EP['t_coda']; b = 60 / 76
    mel = [392.0, 440.0, 493.9, 587.3, 523.3, 493.9, 440.0, 392.0, 349.2, 392.0, 440.0, 392.0]
    bass = [196.0, 164.8, 130.8, 146.8]
    t = 0.3; k = 0
    while t < tc - 0.2:
        if k % 2 == 0: m.put('mus', t, S.piano(mel[(k // 2) % len(mel)], 1.8, 0.3))
        if k % 4 == 0: m.put('mus', t, S.piano(bass[(k // 8) % 4], 2.6, 0.3)); m.put('mus', t, S.piano(bass[(k // 8) % 4] * 1.5, 2.6, 0.18))
        t += b / 2; k += 1
    for t0, d in ((0.3, 0.8), (0.9, 0.6), (4.4, 0.7), (5.6, 1.0), (T_PITCH, 1.4), (T_SUN - 0.6, 1.0), (T_ZOOM + 1.6, 0.9)):
        m.put('fx', t0, S.chalk(d, 0.35, seed=int(t0 * 10)))
    t = T_WALK; i = 0
    while t < T_SUN - 0.2:
        m.put('fx', t, S.step(0.5, i)); t += 0.42; i += 1
    m.put('fx', T_SUN + 0.1, S.bell(784, 2.5, 0.35))
    for i, ch in enumerate([[196.0, 293.7, 392.0], [164.8, 246.9, 329.6], [130.8, 261.6, 329.6]]):
        for j, f in enumerate(ch): m.put('mus', tc + 0.8 + i * STEP + j * 0.05, S.piano(f, 3.0, 0.3))
    m.write(path, rev_mus=1.6, wet_mus=0.25)

EP = finalize(dict(t_coda=T_CODA, draw=draw, sound=sound, end_icon='sun', grain=0.0,
    title_en_card='IF EARTH WERE A 1 CM BEAD', title_ko_card='지구가 1cm 구슬이라면',
    pal=dict(hi=YEL, endbg=(0.93, 0.93, 0.88)),
    card_style=dict(box=None, ink=WHITE, hi=YEL, y=150, fe=BLK, fk=BLK),
    cards=[(0.3, 3.6, ['Shrink Earth to a *1 cm* bead.', 'Where is *the Sun*?'], ['지구를 *1cm* 구슬로 줄이면', '*해*는 어디에 있을까?']),
           (4.2, 9.2, ['The Moon: a *2.7 mm* crumb,', '*30 cm* away.'], ['달은 *2.7mm* 부스러기,', '*30cm* 떨어져 있다']),
           (9.6, 14.2, ['Now keep walking…'], ['이제 계속 걸어가 보자…']),
           (14.6, 18.8, ['*117 m* away —', 'longer than a soccer pitch.'], ['*117m* 떨어진 곳,', '축구장 길이보다 멀다']),
           (19.2, 23.0, ['The Sun: a *1.1 m* ball.'], ['해는 지름 *1.1m*짜리 공'])],
    coda=[("Between us and the Sun:", "해와 우리 사이에는"), ("almost nothing but empty space.", "거의 텅 빈 공간뿐"), ("That we are here at all is a miracle.", "우리가 여기 있다는 것 자체가 기적이다")],
    coda_style=dict(dim=0.6, blur=10, tint=(0.10, 0.13, 0.11), ink=WHITE, hi=YEL),
    sources=['NASA: Sun 1,392,700 km, Earth 12,742 km, Moon 3,475 km wide; Earth–Sun 149.6 million km, Earth–Moon 384,400 km.', 'Scaled so Earth = 1 cm.'],
    yt=dict(title_en='If Earth Were a 1 cm Bead, the Sun Would Be 117 m Away #Shorts', title_ko='지구가 1cm 구슬이면 해는 117m 밖에')))

if __name__ == '__main__': main(EP)
