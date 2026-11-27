"""〈각설탕 하나가 산만큼〉 — 리소그래프(분홍·청록 두 색 판, 판 어긋남, 망점 결, 겹친 곳은 진한 남색), 소리는 펄서처럼 규칙적인 삑 소리와 FM 종.
사실: 중성자별은 무거운 별의 중심핵이 붕괴해 생긴다. 각설탕 하나 분량이 지구에서 약 10억 톤, 산 하나만큼(NASA Imagine the Universe; NASA Science).
지름은 약 20 km로 도시 하나 크기인데 질량은 해의 약 1.5배(National Geographic). 대부분 펄서로 관측된다(NASA).
"""
import math, numpy as np, cv2, cairo
from base import *
import sfx as S

PAPERR = np.array((0.97, 0.94, 0.88)[::-1], np.float32)
PINK = np.array((1.0, 0.28, 0.56)[::-1], np.float32); TEAL = np.array((0.0, 0.62, 0.66)[::-1], np.float32)
T_CITY = 4.2; T_CUBE = 9.8; T_PULSE = 15.2; T_CODA = 20.6
_r = np.random.default_rng(1967)
yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
def _dots(ang, period):
    ca, sa = math.cos(ang), math.sin(ang); u = (xx * ca + yy * sa) / period; v = (-xx * sa + yy * ca) / period
    return ((np.sin(u * 2 * np.pi) * np.sin(v * 2 * np.pi)) * 0.5 + 0.5).astype(np.float32)
DOT_P = _dots(0.26, 7 * SC); DOT_T = _dots(1.31, 7 * SC)
PGRAIN = np.clip(1 + cv2.GaussianBlur(_r.normal(0, 1, (H, W)).astype(np.float32), (0, 0), 0.8) * 0.25, 0.4, 1.4)

def ink(layer, dots):
    """잉크 양(0..1) → 망점: 양이 많을수록 점이 커진다."""
    return np.clip((layer * 1.15 - dots) * 6 + 0.5, 0, 1) * PGRAIN

def draw(t):
    sp, cp = surf(); st, ct = surf()                                    # 분홍 판, 청록 판
    def both(fn, wp=1.0, wt=1.0):
        cp.save(); fn(cp, wp); cp.restore(); ct.save(); fn(ct, wt); ct.restore()
    if t < T_CITY:                                                      # 별이 무너진다
        a = 1 - ramp(t, T_CITY - 0.3, T_CITY)
        g = smooth(ramp(t, 0.8, 3.4)); R = 380 * (1 - g) + 40 * g
        def star(c, w):
            c.set_source_rgba(1, 1, 1, w * a); c.arc(540, 1050, R, 0, 6.283); c.fill()
        both(star, 0.55 + 0.45 * g, 0.9)
        def ring(c, w):
            c.set_source_rgba(1, 1, 1, w * a * ramp(t, 3.0, 3.4) * (1 - ramp(t, 3.4, 4.0))); c.set_line_width(30); c.arc(540, 1050, 120 + 400 * ramp(t, 3.0, 4.0), 0, 6.283); c.stroke()
        both(ring, 1.0, 0.0)
    elif t < T_CUBE:                                                    # 도시만 한 별
        a = ramp(t, T_CITY, T_CITY + 0.3) * (1 - ramp(t, T_CUBE - 0.3, T_CUBE))
        def city(c, w):
            c.set_source_rgba(1, 1, 1, w * a)
            for k, h in enumerate([220, 340, 180, 420, 300, 260, 380, 200, 320, 240]):
                c.rectangle(80 + k * 92, 1500 - h, 80, h)
            c.fill()
        both(city, 0.0, 0.85)
        def ns(c, w):
            c.set_source_rgba(1, 1, 1, w * a); c.arc(540, 1080, 460 * smooth(ramp(t, T_CITY + 0.3, T_CITY + 1.6)), 0, 6.283); c.fill()
        both(ns, 0.8, 0.3)
        def ruler(c, w):
            c.set_source_rgba(1, 1, 1, w * a); c.set_line_width(6); c.move_to(80, 1600); c.line_to(1000, 1600); c.stroke()
        both(ruler, 1.0, 1.0)
    elif t < T_PULSE:                                                   # 각설탕 = 산
        a = ramp(t, T_CUBE, T_CUBE + 0.3) * (1 - ramp(t, T_PULSE - 0.3, T_PULSE))
        u = max(0.0, t - T_CUBE - 0.8); tilt = 0.30 * math.exp(-u * 1.3) * math.cos(u * 4.0) if t > T_CUBE + 0.8 else 0.30
        def scale_(c, w):
            c.set_source_rgba(1, 1, 1, w * a); c.set_line_width(14)
            c.move_to(540, 760); c.line_to(540, 1500); c.stroke(); c.rectangle(380, 1500, 320, 40); c.fill()
            c.save(); c.translate(540, 780); c.rotate(-tilt)
            c.move_to(-380, 0); c.line_to(380, 0); c.stroke()
            for side in (-1, 1):
                c.move_to(side * 380, 0); c.line_to(side * 380 - 90, 220); c.move_to(side * 380, 0); c.line_to(side * 380 + 90, 220); c.stroke()
                c.rectangle(side * 380 - 120, 220, 240, 18); c.fill()
            c.restore()
        both(scale_, 0.4, 1.0)
        lx, ly = 540 - 380 * math.cos(tilt), 780 + 380 * math.sin(tilt); rx, ry = 540 + 380 * math.cos(tilt), 780 - 380 * math.sin(tilt)
        def cube(c, w):
            c.set_source_rgba(1, 1, 1, w * a); c.rectangle(lx - 30, ly + 160, 60, 60); c.fill()
        both(cube, 1.0, 0.6)
        def mountain(c, w):
            c.set_source_rgba(1, 1, 1, w * a * ramp(t, T_CUBE + 0.4, T_CUBE + 0.8))
            c.move_to(rx - 110, ry + 220); c.line_to(rx - 30, ry + 60); c.line_to(rx + 10, ry + 120); c.line_to(rx + 50, ry + 40); c.line_to(rx + 110, ry + 220); c.close_path(); c.fill()
        both(mountain, 0.2, 0.9)
    else:                                                               # 펄서 등대
        a = ramp(t, T_PULSE, T_PULSE + 0.3) * (1 - ramp(t, T_CODA - 0.3, T_CODA))
        ang = (t - T_PULSE) * 2 * math.pi * 0.9
        def beams(c, w):
            c.set_source_rgba(1, 1, 1, w * a)
            for d in (0, math.pi):
                q = ang + d; c.move_to(540, 1080)
                c.line_to(540 + 1400 * math.cos(q - 0.12), 1080 + 1400 * math.sin(q - 0.12) * 0.55)
                c.line_to(540 + 1400 * math.cos(q + 0.12), 1080 + 1400 * math.sin(q + 0.12) * 0.55); c.close_path(); c.fill()
        both(beams, 0.75, 0.0)
        def core(c, w):
            c.set_source_rgba(1, 1, 1, w * a); c.arc(540, 1080, 70, 0, 6.283); c.fill()
        both(core, 1.0, 1.0)
    P = arr(sp)[..., 3]; T = arr(st)[..., 3]
    off = 6 * SC                                                       # 판 어긋남
    T = np.roll(np.roll(T, int(off), 1), int(off * 0.6), 0)
    ip = ink(P, DOT_P)[..., None]; it = ink(T, DOT_T)[..., None]
    img = PAPERR * (1 - ip * (1 - PINK)) * (1 - it * (1 - TEAL))           # 곱하기 섞기(겹치면 남색)
    s2, c2 = surf()
    navy = (0.14, 0.14, 0.32)
    if T_CITY <= t < T_CUBE:
        a = ramp(t, T_CITY + 1.4, T_CITY + 1.8) * (1 - ramp(t, T_CUBE - 0.3, T_CUBE))
        txt(c2, '~20 km', 540, 1680, 80, navy, a, fam=BLK); txt(c2, 'about one city · 도시 하나', 540, 1750, 40, navy, a, fam=BOLD)
        txt(c2, '1.5 × Sun’s mass', 540, 800, 64, navy, a * ramp(t, T_CITY + 2.2, T_CITY + 2.6), fam=BLK)
    if T_CUBE <= t < T_PULSE:
        a = ramp(t, T_CUBE + 2.0, T_CUBE + 2.4) * (1 - ramp(t, T_PULSE - 0.3, T_PULSE))
        txt(c2, '1 sugar cube ≈ 1 mountain', 540, 1680, 52, navy, a, fam=BLK)
        txt(c2, '≈ 1,000,000,000 t on Earth · 지구에서 약 10억 톤', 540, 1750, 36, navy, a, fam=BOLD)
    if t >= T_PULSE:
        a = ramp(t, T_PULSE + 1.0, T_PULSE + 1.4) * (1 - ramp(t, T_CODA - 0.3, T_CODA))
        txt(c2, 'PULSAR · 펄서', 540, 1700, 72, navy, a, fam=BLK)
    return over(np.clip(img, 0, 1), s2)

def sound(path):
    m = S.Mix(EP['DUR'], 1967); tc = EP['t_coda']
    t = 0.3; k = 0
    while t < tc - 0.2:                                                  # 펄서 박
        rate = 0.55 if t < T_PULSE else 1 / 1.8
        m.put('mus', t, S.beep(1320.0 if k % 4 == 0 else 990.0, 0.06, 0.12)); t += rate; k += 1
    for i, f in enumerate([110.0, 98.0, 87.3, 82.4]): m.put('mus', 0.3 + i * 5.0, S.fm(f, 5.4, 0.2, 1.41, 1.2, 0.35))
    m.put('fx', 3.0, S.thunder(2.5, 0.28, seed=9)); m.put('fx', T_CUBE + 0.8, S.swoosh(1.4, 0.18, 200, 1200))
    for i, f in enumerate([440.0, 329.6, 220.0]): m.put('mus', tc + 0.8 + i * STEP, S.fm(f, 3.0, 0.25, 3.5, 2.0, 1.2))
    m.write(path, rev_mus=2.8, wet_mus=0.42)

EP = finalize(dict(t_coda=T_CODA, draw=draw, sound=sound, end_icon='star', grain=0.0,
    title_en_card='A SUGAR CUBE THAT WEIGHS A MOUNTAIN', title_ko_card='각설탕 하나가 산만큼',
    pal=dict(hi=(0.85, 0.15, 0.45), endbg=(0.97, 0.94, 0.88)),
    card_style=dict(box='paper', bg=(0.99, 0.96, 0.92), ink=(0.14, 0.14, 0.32), hi=(0.88, 0.18, 0.46), y=180, fe=BOLD, fk=BLK),
    cards=[(0.3, 4.0, ['When a giant star dies,', 'its core *collapses*.'], ['거대한 별이 죽으면', '중심이 *무너져 내린다*']),
           (4.2, 9.6, ['What is left: a neutron star,', 'about *20 km* wide.'], ['남는 것은 중성자별,', '지름 약 *20km*']),
           (9.8, 15.0, ['A sugar cube of it would weigh', 'about *a billion tons* on Earth.'], ['그 각설탕 하나가 지구에서', '약 *10억 톤*']),
           (15.2, 20.4, ['Many spin and flash', 'like *lighthouses*.'], ['많은 중성자별은 돌며', '*등대*처럼 깜박인다'])],
    coda=[('Even when a star collapses,', '별이 무너져도'), ('what remains can shine for ages.', '남은 것은 오래도록 빛난다'), ('Your hardest days can make you dense with light.', '가장 힘든 날도 나를 단단히 빛나게 한다')],
    coda_style=dict(dim=0.5, blur=8, tint=(0.95, 0.85, 0.85), ink=(0.14, 0.14, 0.32), hi=(0.88, 0.18, 0.46), fe=BOLD),
    sources=['A sugar cube of neutron-star material would weigh about 1 trillion kg (1 billion tons) on Earth; most neutron stars are observed as pulsars (NASA Imagine the Universe; NASA Science).', 'About 20 km across with ~1.5 solar masses (National Geographic).'],
    yt=dict(title_en='A Sugar Cube of This Star Weighs a Billion Tons #Shorts', title_ko='각설탕 하나가 10억 톤, 중성자별')))

if __name__ == '__main__': main(EP)
