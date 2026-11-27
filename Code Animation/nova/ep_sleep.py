"""〈평생 잠자는 시간〉 다시 만들기 — 남색 도화지에 크레파스(종이 결 위에만 묻는 밀랍, 끊긴 낙서 칠, 손별·초승달), 소리는 첼레스타 자장가와 빗소리.
가정: 매일 밤 8시간, 80년 → 80 ÷ 3 ≈ 26.7년.
"""
import math, numpy as np, cv2, cairo
from base import *
import sfx as S

NAVY = (0.10, 0.12, 0.28); YEL = (0.99, 0.86, 0.42); VIO = (0.55, 0.52, 0.95); WHITE = (0.96, 0.95, 0.90); PINK = (0.98, 0.66, 0.72); SKY = (0.55, 0.80, 0.98)
T_DAY = 4.2; T_LIFE = 8.4; T_MOVE = 13.4; T_SUM = 18.0; T_CODA = 22.2
GX0, GY0, CELL = 150, 600, 98; COLS, ROWS = 8, 10

_r = np.random.default_rng(10)
def _n(scales):
    g = sum(cv2.resize(_r.standard_normal((max(2, H // d), max(2, W // d))).astype(np.float32), (W, H), interpolation=cv2.INTER_CUBIC) * w for d, w in scales)
    return (g - g.min()) / (g.max() - g.min())
TOOTH = _n(((1, 1.0), (2, 0.8), (4, 0.4)))                 # 도화지 결(높은 곳에만 크레파스가 묻는다)
_lo = _n(((40, 1), (200, 1)))
PAPER = (np.array(NAVY[::-1], np.float32) * (0.9 + 0.2 * _lo[..., None]) * (0.94 + 0.12 * TOOTH[..., None])).astype(np.float32)

class Crayon:
    def __init__(self): self.layers = {}
    def ctx(self, col):
        if col not in self.layers: self.layers[col] = surf()
        return self.layers[col][1]
    def compose(self, img):
        for col, (s, cr) in self.layers.items():
            a = arr(s)[..., 3]
            if col in (WHITE, PINK): c = np.clip((a * 1.25 - (1 - TOOTH) * 0.85) * 2.4, 0, 1) * np.clip(a * 3, 0, 1)
            else: c = np.clip((a * 0.72 - (1 - TOOTH)) * 4.0, 0, 1) * np.clip(a * 3, 0, 1)
            img = img * (1 - c[..., None] * 0.92) + np.array(col[::-1], np.float32) * c[..., None] * 0.92
        return img

def scribble(cr, x0, y0, w, h, a, seed, dens=1.0, ang=0.6):
    """사각 영역을 크레파스로 왔다 갔다 칠한다."""
    if a <= 0 or w <= 1 or h <= 1: return
    r = np.random.default_rng(seed); cr.save(); cr.rectangle(x0 - 2, y0 - 2, w + 4, h + 4); cr.clip()
    cr.set_source_rgba(0, 0, 0, a); cr.set_line_width(7); cr.set_line_cap(cairo.LINE_CAP_ROUND)
    n = int((w + h) / 9 * dens) + 2; dx = math.cos(ang); dy = math.sin(ang)
    pts = []
    for k in range(n):
        u = k / max(1, n - 1); off = lerp(-h, w, u)
        pa = (x0 + off - dy * 0 + r.normal(0, 2), y0 + h + 6); pb = (x0 + off + h * dx / max(dy, 0.3) + r.normal(0, 2), y0 - 6)
        pts += [pa, pb] if k % 2 == 0 else [pb, pa]
    cr.move_to(*pts[0]); [cr.line_to(*p) for p in pts[1:]]; cr.stroke(); cr.restore()

def wobble_line(cr, pts, a, w=6, seed=0):
    if a <= 0: return
    r = np.random.default_rng(seed); P = np.asarray(pts, float)
    cr.set_source_rgba(0, 0, 0, a); cr.set_line_width(w); cr.set_line_cap(cairo.LINE_CAP_ROUND)
    D = []
    for p, q in zip(P, P[1:]):
        m = max(2, int(np.hypot(*(q - p)) / 10)); D += [p + (q - p) * k / m + r.normal(0, 1.2, 2) for k in range(m)]
    D.append(P[-1]); cr.move_to(*D[0]); [cr.line_to(*d) for d in D[1:]]; cr.stroke()

def star(cr, x, y, R, a, seed):
    th = np.linspace(-math.pi / 2, 1.5 * math.pi, 11); rr = np.where(np.arange(11) % 2 == 0, R, R * 0.45)
    wobble_line(cr, np.stack([x + rr * np.cos(th), y + rr * np.sin(th)], 1), a, 4, seed)

STARS = [st for st in [(_r.uniform(40, 1040), _r.uniform(480, 1860), _r.uniform(8, 18), _r.uniform(0, 6.283)) for _ in range(40)] if not (1440 < st[1] < 1700) and not (900 < st[0] and st[1] < 600)][:24]

def cell_xy(i): return GX0 + (i % COLS) * CELL, GY0 + (i // COLS) * CELL

def draw(t):
    C = Crayon(); cw, cy_, cv, cp, cs = C.ctx(WHITE), C.ctx(YEL), C.ctx(VIO), C.ctx(PINK), C.ctx(SKY)
    for k, (x, y, R, ph) in enumerate(STARS):                   # 손별(반짝)
        if T_LIFE - 0.4 < t < T_CODA and GY0 - 30 < y < GY0 + ROWS * CELL + 30 and GX0 - 30 < x < GX0 + COLS * CELL + 30: continue
        star(cw, x, y, R * (1 + 0.15 * math.sin(t * 2 + ph)), 0.55 + 0.35 * math.sin(t * 1.3 + ph) ** 2, k)
    # 초승달
    mx, my = 985, 535
    cy_.save(); cy_.arc(mx, my, 52, 0, 6.283); cy_.arc_negative(mx + 24, my - 14, 45, 6.283, 0); cy_.clip()
    scribble(cy_, mx - 54, my - 54, 108, 108, ramp(t, 0.1, 0.8), 3, 1.4, 0.9); cy_.restore()
    # 1~2. 24시간 시계
    ca = 1 - ramp(t, T_LIFE - 0.6, T_LIFE - 0.1)
    if ca > 0:
        cx, cyy, R = 540, 1060, 330
        wobble_line(cw, [(cx + R * math.cos(a_), cyy + R * math.sin(a_)) for a_ in np.linspace(0, 6.3, 80)], ca, 7, 1)
        for h in range(24):
            a_ = h / 24 * 6.283 - math.pi / 2
            wobble_line(cw, [(cx + R * 0.88 * math.cos(a_), cyy + R * 0.88 * math.sin(a_)), (cx + R * 0.97 * math.cos(a_), cyy + R * 0.97 * math.sin(a_))], ca, 5 if h % 6 else 7, 10 + h)
            if h % 6 == 0: txt(cw, f'{h}', cx + R * 0.74 * math.cos(a_), cyy + R * 0.74 * math.sin(a_) + 16, 44, (0, 0, 0), ca, fam=BLK)
        fill = ramp(t, 1.0, 3.4)                             # 밤 23시~7시 = 8시간
        a0 = 23 / 24 * 6.283 - math.pi / 2; a1 = a0 + 8 / 24 * 6.283 * fill
        if fill > 0:
            cv.save(); cv.move_to(cx, cyy); cv.arc(cx, cyy, R * 0.86, a0, a1); cv.close_path(); cv.clip()
            scribble(cv, cx - R, cyy - R, 2 * R, 2 * R, ca, 5, 1.1); cv.restore()
        da = ramp(t, T_DAY, T_DAY + 0.6) * ca
        if da > 0:
            cy_.save(); cy_.move_to(cx, cyy); cy_.arc(cx, cyy, R * 0.86, a0 + 8 / 24 * 6.283, a0 + 6.283); cy_.close_path(); cy_.clip()
            scribble(cy_, cx - R, cyy - R, 2 * R, 2 * R, da * 0.6, 6, 0.7, 0.3); cy_.restore()
            txt(cw, '8 h asleep · 잠 8시간', 540, 1520, 46, (0, 0, 0), da, fam=BLK)
            txt(cw, '16 h awake · 깨어 있는 16시간', 540, 1590, 38, (0, 0, 0), da * 0.8, fam=BLK)
    # 3. 80년 = 80칸, 칸마다 아래 3분의 1이 잠
    if t > T_LIFE - 0.3:
        la = ramp(t, T_LIFE - 0.3, T_LIFE + 0.3)
        nshow = 80 * ramp(t, T_LIFE + 0.2, T_LIFE + 4.0)
        mv = smooth(ramp(t, T_MOVE, T_MOVE + 3.0))
        for i in range(80):
            x, y = cell_xy(i); ap = la * ramp(nshow, i, i + 1.5)
            if ap <= 0: continue
            wobble_line(cw, [(x + 6, y + 6), (x + CELL - 6, y + 6), (x + CELL - 6, y + CELL - 6), (x + 6, y + CELL - 6), (x + 6, y + 6)], ap * 0.7, 3, 200 + i)
            scribble(cy_, x + 10, y + 10, CELL - 20, (CELL - 20) * 2 / 3, ap * lerp(0.75, 0.35, mv), 300 + i, 0.8, 0.5)
            # 잠 조각: 제자리 → 모여서 26.7칸을 채운다
            j = i; tx, ty = cell_xy(j // 3); ty += 10 + (2 - j % 3) * (CELL - 20) / 3
            sx, sy = x, y + 10 + (CELL - 20) * 2 / 3
            dl = (i % 13) * 0.03; u = smooth(ramp(mv, dl, min(1, dl + 0.7)))
            px, py = lerp(sx, tx, u), lerp(sy, ty, u)
            scribble(cv, px + 10, py, CELL - 20, (CELL - 20) / 3, ap, 400 + i, 1.2, 0.7)
        txt(cw, f'year {min(80, int(nshow)):d} · {min(80, int(nshow))}년', 540, GY0 + ROWS * CELL + 80, 44, (0, 0, 0), la * (1 - ramp(t, T_MOVE, T_MOVE + 0.4)), fam=BLK)
        sa = ramp(t, T_MOVE + 3.0, T_MOVE + 3.6)
        if sa > 0:
            x, y = cell_xy(26); yy = y + CELL
            wobble_line(cp, [(GX0 - 30, GY0), (GX0 - 30, yy)], sa, 8, 501)
            for y_ in (GY0, yy): wobble_line(cp, [(GX0 - 46, y_), (GX0 - 14, y_)], sa, 8, 502)
            txt(cw, '26.7 years asleep', 540, GY0 + ROWS * CELL + 80, 56, (0, 0, 0), sa, fam=BLK)
            txt(cw, '잠든 시간 26.7년', 540, GY0 + ROWS * CELL + 145, 48, (0, 0, 0), sa, fam=BLK)
    img = C.compose(PAPER.copy())
    return img

def sound(path):
    m = S.Mix(EP['DUR'], 111); tc = EP['t_coda']; b = 60 / 66
    m.put('amb', 0, S.rain(EP['t_end'] + 1, 0.45))
    mel = [(0, 659.3, 2), (2, 587.3, 1), (3, 523.3, 2), (5, 587.3, 1), (6, 659.3, 1), (7, 659.3, 1), (8, 659.3, 2), (10, 587.3, 1), (11, 587.3, 1),
           (12, 523.3, 2), (14, 440.0, 1), (15, 392.0, 3), (18, 440.0, 1), (19, 523.3, 2), (21, 587.3, 1), (22, 523.3, 2)]   # 새로 지은 3박 자장가
    for rep in range(3):
        base = 0.4 + rep * 24 * b / 2
        for st, f, d in mel:
            tt = base + st * b / 2
            if tt < tc - 0.3: m.put('mus', tt, S.celesta(f, 1.6 + d * 0.3, 0.32))
        for k in range(8):
            tt = base + k * 3 * b / 2
            if tt < tc - 0.3: m.put('mus', tt, S.celesta([130.8, 196.0, 174.6, 196.0][k % 4] * 2, 2.4, 0.2))
    m.put('fx', T_MOVE, S.swoosh(3.0, 0.25, 300, 2500)); m.put('fx', T_MOVE + 3.0, S.bell(1046.5, 3.0, 0.3))
    m.put('amb', tc, S.drone([130.8, 196.0, 261.6], EP['t_end'] - tc, 0.12, 'sine'))
    for i, f in enumerate([659.3, 587.3, 523.3]): m.put('mus', tc + 0.8 + i * STEP, S.celesta(f, 3.0, 0.35)); m.put('mus', tc + 0.85 + i * STEP, S.celesta(f / 2, 3.0, 0.2))
    m.write(path, rev_mus=3.2, wet_mus=0.4)

EP = finalize(dict(t_coda=T_CODA, draw=draw, sound=sound, end_icon='bed', grain=0.0,
    title_en_card='YEARS OF SLEEP', title_ko_card='평생 잠자는 시간',
    pal=dict(hi=VIO, endbg=(0.93, 0.92, 0.88)),
    card_style=dict(box=None, ink=WHITE, hi=YEL, y=150, fe=BLK, fk=BLK),
    cards=[(0.3, 3.8, ['Sleep *8 hours* a night.', 'How much of your life is that?'], ['하루 *8시간* 잔다면,', '인생에서 얼마일까?']),
           (4.2, 8.0, ['That’s *1/3* of every day.'], ['하루의 *3분의 1*']),
           (8.4, 17.8, ['Over 80 years…'], ['80년을 살면…']),
           (18.0, 22.0, ['*26.7 years*', 'with your eyes closed.'], ['*26.7년*을', '눈 감고 보낸다'])],
    coda=[("We give a third of life to rest,", "인생의 3분의 1을 쉼에 내어주고"), ("and wake each morning, given another day.", "매일 아침 하루를 다시 선물 받는다"), ("Every morning is a second chance.", "아침은 날마다 오는 두 번째 기회다")],
    coda_style=dict(dim=0.6, blur=10, tint=(0.06, 0.07, 0.17), ink=WHITE, hi=YEL),
    sources=['Assuming 8 hours of sleep every night for 80 years.'],
    yt=dict(title_en='You’ll Spend 26.7 Years Asleep #Shorts', title_ko='평생 26.7년을 잠으로 보낸다')))

if __name__ == '__main__': main(EP)
