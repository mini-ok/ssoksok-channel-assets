"""〈태양계에서 가장 높은 산〉 — 클레이 애니메이션(둥근 찰흙 덩어리, 부드러운 빛·그림자, 손자국 결, 초당 12장 스톱모션 떨림), 소리는 테레민과 낮은 현.
사실(NASA Photojournal; Mars Orbiter Laser Altimeter): 화성 올림푸스산 높이 21.9 km(에베레스트 8.85 km의 약 2.5배), 폭 약 600 km(미국 애리조나주만 하다).
아주 넓고 완만해서 위에 서 있으면 그냥 완만한 비탈처럼 보인다(Space.com).
"""
import math, numpy as np, cv2, cairo
from base import *
import sfx as S

T_COMP = 3.8; T_WIDE = 8.8; T_STAND = 13.6; T_CODA = 18.8
MARS = (0.80, 0.42, 0.25); MARS2 = (0.62, 0.30, 0.18); SKYC = (0.95, 0.80, 0.62); SNOW = (0.96, 0.96, 0.98); ROCK = (0.55, 0.52, 0.50); SUIT = (0.95, 0.95, 0.92)
_r = np.random.default_rng(29)
_yy, _xx = np.mgrid[0:H, 0:W].astype(np.float32) / SC
FINGER = (np.sin(np.hypot(_xx - 300, _yy - 700) * 0.9) * np.sin(np.hypot(_xx - 800, _yy - 1300) * 0.7)).astype(np.float32)
CLAYTEX = (1 + 0.015 * FINGER + 0.05 * cv2.GaussianBlur(_r.standard_normal((H, W)).astype(np.float32), (0, 0), 3 * SC))[..., None]

def blob(cr, pts, col, light=(-0.5, -0.7)):
    """찰흙 덩어리: 꼭짓점을 부드럽게 잇고 위쪽은 밝게, 아래는 어둡게."""
    P = np.asarray(pts, float); n = len(P)
    cr.move_to(*((P[0] + P[1]) / 2))
    for i in range(1, n + 1):
        a, b = P[i % n], P[(i + 1) % n]; m = (a + b) / 2; cr.curve_to(*a, *a, *m)
    cr.close_path()
    x0, y0, x1, y1 = P[:, 0].min(), P[:, 1].min(), P[:, 0].max(), P[:, 1].max()
    g = cairo.LinearGradient(x0 + (x1 - x0) * (0.5 + light[0] * 0.5), y0 + (y1 - y0) * (0.5 + light[1] * 0.5), x1, y1)
    g.add_color_stop_rgb(0, *[min(1, c * 1.22) for c in col]); g.add_color_stop_rgb(0.55, *col); g.add_color_stop_rgb(1, *[c * 0.62 for c in col])
    cr.set_source(g); cr.fill_preserve(); cr.set_source_rgba(0, 0, 0, 0.18); cr.set_line_width(3); cr.stroke()

def boil(seed, amp=2.0):
    r = np.random.default_rng(seed); return r.normal(0, amp, 2)

def mountain(cr, cx, base, w, h, col, seed, snow=False):
    j = lambda k: boil(seed * 100 + k, 1.5)
    pts = [(cx - w / 2, base), (cx - w * 0.3, base - h * 0.45), (cx - w * 0.08, base - h * 0.95), (cx + w * 0.06, base - h),
           (cx + w * 0.3, base - h * 0.5), (cx + w / 2, base)]
    pts = [np.array(p) + j(i) for i, p in enumerate(pts)]
    blob(cr, pts, col)
    if snow: blob(cr, [pts[2] + (0, 2), pts[3] + (0, 2), pts[3] + (w * 0.08, h * 0.18), pts[2] + (-w * 0.05, h * 0.2)], SNOW)

def shield(cr, cx, base, w, h, seed):
    j = lambda k: boil(seed * 100 + k, 1.5)
    pts = [(cx - w / 2, base), (cx - w * 0.42, base - h * 0.15), (cx - w * 0.25, base - h * 0.7), (cx - w * 0.08, base - h), (cx + w * 0.08, base - h),
           (cx + w * 0.25, base - h * 0.7), (cx + w * 0.42, base - h * 0.15), (cx + w / 2, base)]
    blob(cr, [np.array(p) + j(i) for i, p in enumerate(pts)], MARS)
    cr.set_source_rgba(*MARS2, 1); cr.save(); cr.translate(cx, base - h * 0.98); cr.scale(w * 0.07, h * 0.04); cr.arc(0, 0, 1, 0, 6.283); cr.restore(); cr.fill()   # 칼데라

def astronaut(cr, x, y, s, seed):
    o = boil(seed, 1.2)
    blob(cr, [(x - 14 * s, y), (x - 16 * s, y - 50 * s), (x - 10 * s, y - 70 * s), (x + 10 * s, y - 70 * s), (x + 16 * s, y - 50 * s), (x + 14 * s, y)], SUIT)
    cr.set_source_rgb(*SUIT); cr.arc(x + o[0], y - 84 * s + o[1], 17 * s, 0, 6.283); cr.fill()
    cr.set_source_rgb(0.25, 0.35, 0.55); cr.save(); cr.translate(x + 4 * s + o[0], y - 85 * s + o[1]); cr.scale(11 * s, 8 * s); cr.arc(0, 0, 1, 0, 6.283); cr.restore(); cr.fill()

def draw(t0):
    t = math.floor(t0 * 12) / 12; fr = int(t0 * 12)                # 스톱모션: 초당 12장
    s, cr = surf()
    g = cairo.LinearGradient(0, 0, 0, DH); g.add_color_stop_rgb(0, *SKYC); g.add_color_stop_rgb(1, 0.85, 0.62, 0.45); cr.set_source(g); cr.paint()
    cr.set_source_rgba(1, 0.95, 0.85, 0.8); cr.arc(860, 520, 40, 0, 6.283); cr.fill()                # 작은 해
    blob(cr, [(-50, 1560), (300, 1500), (700, 1530), (1130, 1490), (1130, 2000), (-50, 2000)], MARS2)  # 땅
    if t < T_COMP:
        u = smooth(ramp(t, 0.3, 3.0))
        shield(cr, 540, 1520, 900 * u + 1, 360 * u + 1, fr)
    elif t < T_WIDE:                                              # 높이 비교: 1 km = 40 px
        u = smooth(ramp(t, T_COMP + 0.3, T_COMP + 2.6)); K = 44
        mountain(cr, 250, 1520, 300, 8.85 * K, ROCK, fr, snow=True)
        shield(cr, 700, 1520, 640, 21.9 * K * u + 1, fr + 7)
        for x, hkm in ((250, 8.85), (700, 21.9 * u)):
            cr.set_source_rgba(0.15, 0.08, 0.05, 0.85); cr.set_line_width(4); cr.move_to(x + 180 if x > 500 else x - 190, 1520); cr.line_to(x + 180 if x > 500 else x - 190, 1520 - hkm * K); cr.stroke()
    elif t < T_STAND:                                             # 폭 비교(위에서 본 모습)
        u = smooth(ramp(t, T_WIDE + 0.3, T_WIDE + 2.4))
        cx, cy, R = 540, 1050, 330 * u + 1
        for k in range(6, 0, -1): blob(cr, [(cx + R * k / 6 * math.cos(a) * 1.05, cy + R * k / 6 * math.sin(a)) for a in np.linspace(0, 6.28, 14, endpoint=False)], [MARS, MARS2][k % 2])
        cr.set_source_rgba(0.95, 0.95, 1.0, 0.85 * ramp(t, T_WIDE + 2.4, T_WIDE + 3.0)); cr.set_line_width(5); cr.set_dash([14, 10])
        az = [(-0.62, -0.62), (0.58, -0.62), (0.6, 0.35), (0.35, 0.62), (-0.2, 0.66), (-0.62, 0.55)]                   # 애리조나 윤곽(대략)
        cr.move_to(cx + az[0][0] * 360, cy + az[0][1] * 380); [cr.line_to(cx + x * 360, cy + y * 380) for x, y in az[1:]]; cr.close_path(); cr.stroke(); cr.set_dash([])
    else:                                                         # 그 위에 서면: 완만한 비탈
        blob(cr, [(-60, 1250), (500, 1120), (1140, 980), (1140, 2000), (-60, 2000)], MARS)
        astronaut(cr, 470, 1140, 2.2, fr)
        cr.set_source_rgba(0.3, 0.15, 0.08, 0.5); cr.set_line_width(3); cr.set_dash([10, 8]); cr.move_to(80, 1230); cr.line_to(1040, 1010); cr.stroke(); cr.set_dash([])
    img = arr(s)[..., :3] * CLAYTEX
    s2, c2 = surf(); ink = (0.25, 0.10, 0.05)
    def lab(text, x, y, size, a, col=ink):
        txt(c2, text, x, y, size, col, a, fam=BLK)
    if T_COMP <= t < T_WIDE:
        a = ramp(t, T_COMP + 0.5, T_COMP + 0.9)
        lab('Everest', 250, 1640, 44, a); lab('8.85 km', 250, 1700, 40, a)
        lab('Olympus Mons', 700, 1640, 44, a); lab(f'{21.9 * smooth(ramp(t, T_COMP + 0.3, T_COMP + 2.6)):.1f} km', 700, 1700, 40, a)
        lab('× 2.5', 540, 1820, 70, ramp(t, T_COMP + 2.6, T_COMP + 3.0), (0.65, 0.15, 0.05))
    if T_WIDE <= t < T_STAND:
        a = ramp(t, T_WIDE + 2.4, T_WIDE + 3.0)
        lab('~600 km wide', 540, 1580, 60, a); lab('폭 약 600km, 애리조나주만 하다', 540, 1655, 44, a)
    if t >= T_STAND:
        a = ramp(t, T_STAND + 0.6, T_STAND + 1.2) * (1 - ramp(t, T_CODA - 0.4, T_CODA))
        lab('just a gentle slope', 540, 1580, 56, a); lab('그저 완만한 비탈처럼 보인다', 540, 1650, 46, a)
    return over(img, s2)

def sound(path):
    m = S.Mix(EP['DUR'], 211); tc = EP['t_coda']
    m.put('amb', 0, S.drone([55.0, 82.4], EP['t_end'] + 1, 0.18, 'saw'))
    m.put('mus', 0.3, S.theremin([(0, 440), (1.2, 523.3), (2.4, 493.9), (3.4, 392.0)], 3.6, 0.3))
    m.put('mus', T_COMP + 0.2, S.theremin([(0, 293.7), (2.4, 587.3), (3.6, 554.4), (4.6, 587.3)], 4.8, 0.32))
    m.put('mus', T_WIDE + 0.2, S.theremin([(0, 392.0), (1.5, 440.0), (3.0, 349.2), (4.4, 392.0)], 4.6, 0.3))
    m.put('mus', T_STAND + 0.2, S.theremin([(0, 329.6), (2.0, 293.7), (4.0, 261.6), (5.0, 293.7)], 5.0, 0.28))
    for k in range(int(tc / 0.6)): m.put('fx', 0.3 + k * 0.6, S.pizz([110.0, 146.8, 130.8, 98.0][k % 4], 0.5, 0.25, seed=k))
    for k in range(int(tc * 2)): m.put('fx', k / 2 + 0.05, S.click(0.04, k))                # 스톱모션 셔터 같은 작은 소리
    m.put('fx', T_COMP + 2.6, S.bell(880.0, 2.5, 0.3))
    m.put('amb', tc, S.drone([110.0, 164.8, 220.0], EP['t_end'] - tc, 0.15, 'sine'))
    m.put('mus', tc + 0.5, S.theremin([(0, 523.3), (2.0, 493.9), (4.0, 440.0), (6.0, 392.0)], EP['t_end'] - tc - 0.5, 0.28))
    m.write(path, rev_mus=2.6, wet_mus=0.35)

EP = finalize(dict(t_coda=T_CODA, draw=draw, sound=sound, end_icon='star', grain=0.003,
    title_en_card='THE TALLEST MOUNTAIN', title_ko_card='태양계에서 가장 높은 산',
    pal=dict(hi=MARS2, endbg=(0.97, 0.90, 0.80)),
    card_style=dict(box=None, ink=(0.25, 0.10, 0.05), hi=(0.70, 0.18, 0.06), y=150, fe=BLK, fk=BLK),
    cards=[(0.3, 3.6, ['The tallest mountain', 'in the solar system is *on Mars*.'], ['태양계에서 가장 높은 산은', '*화성*에 있다']),
           (3.8, 8.6, ['Olympus Mons: *21.9 km* high,', '*2.5 times* Everest.'], ['올림푸스산 높이 *21.9km*,', '에베레스트의 *2.5배*']),
           (8.8, 13.4, ['About *600 km* across,', 'the size of Arizona.'], ['폭은 약 *600km*,', '미국 애리조나주만 하다']),
           (13.6, 18.6, ['Yet standing on it,', 'it would feel like *a gentle slope*.'], ['그런데 그 위에 서면', '*완만한 비탈*처럼 느껴진다'])],
    coda=[('The tallest mountain of all', '가장 높은 산도'), ('feels like a gentle slope underfoot.', '발밑에서는 완만한 비탈일 뿐'), ('Great heights are climbed one small step at a time.', '높은 곳도 작은 한 걸음씩 오른다')],
    coda_style=dict(dim=0.6, blur=10, tint=(0.95, 0.80, 0.62), ink=(0.25, 0.10, 0.05), hi=(0.70, 0.18, 0.06)),
    sources=['NASA Photojournal: Olympus Mons is 21.9 km (72,000 ft) tall; Everest 8,849 m. ~600 km wide, about the size of Arizona (NASA image comparison).', 'Space.com: so broad that standing on it would look like a gently sloping plain.'],
    yt=dict(title_en='The Tallest Mountain in the Solar System Is 2.5× Everest #Shorts', title_ko='화성 올림푸스산은 에베레스트의 2.5배')))

if __name__ == '__main__': main(EP)
