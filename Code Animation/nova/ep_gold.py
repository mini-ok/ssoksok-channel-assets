"""〈금은 이게 전부〉 — 아이소메트릭 3D(평면 음영 + 금속 반사 띠), 미니멀 전자음(클릭·서브 베이스·사인 아르페지오).
사실(World Gold Council): 지상의 금 약 22만 톤, 녹여 정육면체로 만들면 한 변 약 22.5m.
금 밀도 19.3 t/m³ → 22만 t ≈ 11,400 m³(계산). 1인당 약 27g(세계 인구 약 82억으로 계산, 1트로이온스 31.1g보다 적다).
"""
import math, numpy as np, cv2, cairo
from base import *
import sfx as S

BG0 = (0.10, 0.11, 0.14); BG1 = (0.05, 0.05, 0.07); GRID = (0.30, 0.34, 0.42)
G1 = (1.0, 0.82, 0.35); G2 = (0.86, 0.62, 0.18); G3 = (0.62, 0.42, 0.10)
C30, S30 = math.cos(math.pi / 6), math.sin(math.pi / 6)

class Iso:
    def __init__(self, cx, cy, s): self.cx, self.cy, self.s = cx, cy, s
    def p(self, x, y, z): return self.cx + (x - y) * C30 * self.s, self.cy + (x + y) * S30 * self.s - z * self.s

def box(cr, iso, x, y, z, w, d, h, cols, a, lw=2.0, edge=(0, 0, 0)):
    P = lambda X, Y, Z: iso.p(X, Y, Z)
    top = [P(x, y, z + h), P(x + w, y, z + h), P(x + w, y + d, z + h), P(x, y + d, z + h)]
    left = [P(x, y + d, z), P(x + w, y + d, z), P(x + w, y + d, z + h), P(x, y + d, z + h)]
    right = [P(x + w, y, z), P(x + w, y + d, z), P(x + w, y + d, z + h), P(x + w, y, z + h)]
    for face, c in ((left, cols[1]), (right, cols[2]), (top, cols[0])):
        cr.move_to(*face[0]); [cr.line_to(*q) for q in face[1:]]; cr.close_path()
        cr.set_source_rgba(*c, a); cr.fill_preserve(); cr.set_source_rgba(*edge, 0.35 * a); cr.set_line_width(lw); cr.stroke()
    return top, left, right

def sheen(cr, face, u, a):
    """금속 면 위를 지나가는 밝은 띠."""
    cr.save(); cr.move_to(*face[0]); [cr.line_to(*q) for q in face[1:]]; cr.close_path(); cr.clip()
    xs = [q[0] for q in face]; ys = [q[1] for q in face]; x0, x1 = min(xs), max(xs); y0, y1 = min(ys), max(ys)
    c = lerp(x0 - 200, x1 + 200, u); g = cairo.LinearGradient(c - 120, y0, c + 120, y1)
    g.add_color_stop_rgba(0, 1, 1, 1, 0); g.add_color_stop_rgba(0.5, 1, 0.97, 0.85, 0.55 * a); g.add_color_stop_rgba(1, 1, 1, 1, 0)
    cr.set_source(g); cr.paint(); cr.restore()

def person(cr, iso, x, y, a, scale=1.0):
    X, Y = iso.p(x, y, 0); h = 1.7 * iso.s * scale
    cr.set_source_rgba(0.92, 0.94, 1.0, a); cr.arc(X, Y - h * 0.9, h * 0.1, 0, 6.283); cr.fill()
    cr.set_line_width(max(2, h * 0.12)); cr.move_to(X, Y - h * 0.78); cr.line_to(X, Y - h * 0.35); cr.stroke()
    cr.move_to(X, Y - h * 0.35); cr.line_to(X - h * 0.12, Y); cr.move_to(X, Y - h * 0.35); cr.line_to(X + h * 0.12, Y); cr.stroke()

T_SCENE = (3.6, 6.0); T_RISE = (8.0, 12.6); T_SPIN = 12.8; T_SHARE = 17.4; T_CODA = 23.0
EDGE = 22.5

def draw(t):
    s, cr = surf()
    g = cairo.LinearGradient(0, 0, 0, DH); g.add_color_stop_rgb(0, *BG0); g.add_color_stop_rgb(1, *BG1); cr.set_source(g); cr.paint()
    zoom = 13.0 * (1 + 0.03 * math.sin(t * 0.3))
    iso = Iso(540 + 12 * math.sin(t * 0.15), 1200, zoom)
    # 바닥 격자(5m)
    ga = ramp(t, 0.1, 0.8)
    cr.set_line_width(1.5)
    for k in range(-30, 31, 5):
        a0, b0 = iso.p(k, -30, 0), iso.p(k, 30, 0); a1, b1 = iso.p(-30, k, 0), iso.p(30, k, 0)
        cr.set_source_rgba(*GRID, 0.35 * ga); cr.move_to(*a0); cr.line_to(*b0); cr.move_to(*a1); cr.line_to(*b1); cr.stroke()
    # 비교 대상: 테니스 코트(23.77 × 10.97 m), 7층 건물(약 22 m), 사람(1.7 m)
    sa = ramp(t, T_SCENE[0], T_SCENE[0] + 0.6) * (1 - 0.6 * ramp(t, T_SHARE, T_SHARE + 0.6))
    if sa > 0:
        hb = expo_out(ramp(t, T_SCENE[0] + 0.5, T_SCENE[0] + 1.8))
        if hb > 0:
            for fl in range(7):
                box(cr, iso, -13, -37, fl * 3.15 * hb, 12, 10, 3.0 * hb, ((0.42, 0.48, 0.58), (0.30, 0.34, 0.42), (0.36, 0.41, 0.50)), sa)
        pa = sa * ramp(t, T_SCENE[0] + 1.0, T_SCENE[0] + 1.4) * (1 - ramp(t, T_SHARE, T_SHARE + 0.4))
        person(cr, iso, -4, 20, pa, 1.2); X, Y = iso.p(-4, 20, 0); txt(cr, '1.7 m', X + 46, Y - 8, 26, (0.85, 0.9, 1), pa, fam=BOLD)
        X, Y = iso.p(-8, -32, 23); txt(cr, '7-story building · 7층 건물', X, Y - 24, 30, (0.85, 0.9, 1), sa * ramp(t, T_SCENE[0] + 1.6, T_SCENE[0] + 2.0) * (1 - ramp(t, T_SHARE, T_SHARE + 0.4)), fam=BOLD)
    # 금 정육면체: 금괴가 층층이 쌓인다
    if t >= T_RISE[0]:
        u = smooth(ramp(t, *T_RISE)); h = EDGE * u; ca = 1 - 0.75 * ramp(t, T_SHARE, T_SHARE + 0.8)
        top, left, right = box(cr, iso, -EDGE / 2, -EDGE / 2, 0, EDGE, EDGE, max(0.01, h), (G1, G2, G3), ca, 2.5, (0.3, 0.2, 0.05))
        cr.set_source_rgba(0.45, 0.3, 0.05, 0.35 * ca); cr.set_line_width(1.6)
        for k in range(1, int(h / 1.5) + 1):                    # 층 줄무늬(금괴 층)
            z = k * 1.5; a0, b0, c0 = iso.p(-EDGE / 2, EDGE / 2, z), iso.p(EDGE / 2, EDGE / 2, z), iso.p(EDGE / 2, -EDGE / 2, z)
            cr.move_to(*a0); cr.line_to(*b0); cr.line_to(*c0); cr.stroke()
        if t >= T_SPIN: sheen(cr, left, ((t - T_SPIN) * 0.45) % 1.3, ca); sheen(cr, right, ((t - T_SPIN) * 0.45 + 0.25) % 1.3, ca)
        X, Y = iso.p(-EDGE / 2, EDGE / 2, EDGE * 0.62); X -= 110
        lab = ramp(t, T_RISE[1] - 0.4, T_RISE[1]) * (1 - ramp(t, T_SHARE, T_SHARE + 0.4))
        txt(cr, '22.5 m', X + 30, Y + 60, 60, G1, lab); txt(cr, '한 변 22.5m', X + 30, Y + 118, 44, G1, lab, fam=BOLD)
        if T_RISE[0] < t < T_RISE[1] + 0.3:
            tt_ = 220000 * u; txt(cr, f'{tt_:,.0f} t', 540, 1700, 72, G1, ramp(t, T_RISE[0], T_RISE[0] + 0.3)); txt(cr, f'{tt_ / 10000:,.1f}만 톤', 540, 1780, 52, G1, ramp(t, T_RISE[0], T_RISE[0] + 0.3), fam=BOLD)
    if sa > 0:
        court = [iso.p(14, -14, 0), iso.p(25, -14, 0), iso.p(25, 9.77, 0), iso.p(14, 9.77, 0)]
        cr.move_to(*court[0]); [cr.line_to(*q) for q in court[1:]]; cr.close_path(); cr.set_source_rgba(0.20, 0.45, 0.62, 0.85 * sa); cr.fill_preserve()
        cr.set_source_rgba(1, 1, 1, 0.8 * sa); cr.set_line_width(2.5); cr.stroke(); m0, m1 = iso.p(14, -2.1, 0), iso.p(25, -2.1, 0); cr.move_to(*m0); cr.line_to(*m1); cr.stroke()
        X, Y = iso.p(25, 9.77, 0); txt(cr, 'Tennis court · 테니스 코트', X - 40, Y + 46, 30, (0.85, 0.9, 1), sa * ramp(t, T_SCENE[0] + 0.6, T_SCENE[0] + 1.0) * (1 - ramp(t, T_SHARE, T_SHARE + 0.4)), fam=BOLD)
    # 1인당 몫: 동전 하나
    if t >= T_SHARE:
        a = ramp(t, T_SHARE + 0.3, T_SHARE + 0.8); k = back_out(ramp(t, T_SHARE + 0.3, T_SHARE + 0.9), 1.8)
        cx, cy, r = 540, 1160, 150 * k
        g2 = cairo.RadialGradient(cx - r * 0.3, cy - r * 0.3, r * 0.1, cx, cy, r); g2.add_color_stop_rgb(0, *G1); g2.add_color_stop_rgb(0.7, *G2); g2.add_color_stop_rgb(1, *G3)
        cr.save(); cr.translate(cx, cy); cr.scale(1, 0.92); cr.translate(-cx, -cy); cr.set_source(g2); cr.arc(cx, cy, r, 0, 6.283); cr.fill()
        cr.set_source_rgba(*G3, a); cr.set_line_width(6); cr.arc(cx, cy, r * 0.82, 0, 6.283); cr.stroke(); cr.restore()
        txt(cr, '≈ 27 g', cx, cy + 26, 84, (0.35, 0.22, 0.04), a)
        txt(cr, 'per person on Earth · 1인당 약 27g', 540, 1500, 40, G1, a, fam=BOLD)
    return arr(s)[..., :3]

def sound(path):
    m = S.Mix(EP['DUR'], 22); tc = EP['t_coda']; bpm = 112; b = 60 / bpm
    m.put('amb', 0, S.drone([55.0, 82.4], EP['t_end'] + 1, 0.12, 'sine'))
    t = 0.2; k = 0; arp = [220.0, 277.2, 329.6, 440.0, 329.6, 277.2]
    while t < tc - 0.1:
        m.put('fx', t, S.click(0.25 if k % 4 else 0.45, k))
        if k % 4 == 0: m.put('fx', t, S.kick(48, 0.55, 0.4))
        if t > T_SCENE[0]: m.put('mus', t, S.marimba(arp[k % 6] * (2 if t > T_RISE[0] else 1), 0.5, 0.18))
        t += b / 2; k += 1
    for i in range(7): m.put('fx', T_SCENE[0] + 0.5 + i * 0.2, S.tok(420 + 40 * i, 0.25))
    n = int((T_RISE[1] - T_RISE[0]) * S.SR); tt = np.arange(n) / S.SR
    m.put('fx', T_RISE[0], 0.2 * np.sin(2 * np.pi * np.cumsum(60 + 200 * (tt / tt[-1]) ** 2) / S.SR) * np.minimum(1, tt / 0.3))
    m.put('fx', T_RISE[1], S.kick(40, 0.9, 1.0)); m.put('mus', T_RISE[1], S.bell(880, 3.0, 0.5)); m.put('mus', T_RISE[1] + 0.05, S.bell(1318.5, 3.0, 0.35))
    m.put('fx', T_SHARE + 0.3, S.ping(2093, 0.5, 2.5)); m.put('fx', T_SHARE + 0.35, S.tok(1600, 0.4))
    m.put('amb', tc, S.drone([110.0, 164.8, 220.0], EP['t_end'] - tc, 0.25, 'sine'))
    for i in range(3): m.put('mus', tc + 0.8 + i * STEP, S.bell([659.3, 587.3, 880.0][i], 3.0, 0.35))
    m.put('fx', EP['t_end'] + 0.2, S.ping(1760, 0.4, 2.5))
    m.write(path, rev_mus=2.0, wet_mus=0.28)

EP = finalize(dict(t_coda=T_CODA, draw=draw, sound=sound, end_icon='star', grain=0.004,
    title_en_card='ALL THE GOLD', title_ko_card='세상의 금은 이게 전부',
    pal=dict(hi=G2, endbg=(0.95, 0.93, 0.88)),
    card_style=dict(box=None, ink=(0.93, 0.95, 1.0), hi=G1, y=170, fe=BLK, fk=BLK),
    cards=[(0.3, 3.4, ['All the gold ever mined.', '*How big is it?*'], ['인류가 캐낸 금을 다 모으면', '*얼마나 클까?*']),
           (3.8, 7.8, ['A tennis court, a 7-story building,', 'and a person, to scale.'], ['테니스 코트, 7층 건물,', '사람 하나를 같은 축척으로']),
           (8.0, 12.6, ['About *220,000 tonnes*', 'of gold above ground…'], ['땅 위에 있는 금 약 *22만 톤*을', '녹여 모으면…']),
           (12.8, 17.2, ['…one cube, *22.5 m* a side.', 'About the height of 7 floors.'], ['한 변 *22.5m* 정육면체 하나', '7층 건물 높이쯤']),
           (17.6, 22.8, ['Shared by everyone on Earth:', 'about *27 g* each.'], ['지구 사람 모두가 나누면', '1인당 약 *27g*'])],
    coda=[('Everything we ever fought over', '인류가 다투어 온 금은'), ('fits in a single small cube.', '작은 상자 하나에 다 들어간다'), ('What can’t be melted down is worth more.', '녹일 수 없는 것이 더 귀하다')],
    coda_style=dict(dim=0.6, blur=10, tint=(0.03, 0.03, 0.04), ink=(0.95, 0.95, 1.0), hi=G1),
    sources=['World Gold Council: ~220,000 t of gold above ground; as a cube ~22.5 m (74 ft) a side.', 'Per person ≈ 27 g (calculated with ~8.2 billion people).'],
    yt=dict(title_en='All the Gold Ever Mined Fits in One 22.5 m Cube #Shorts', title_ko='인류가 캔 금을 다 모으면 한 변 22.5m 정육면체')))

if __name__ == '__main__': main(EP)
