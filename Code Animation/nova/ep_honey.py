"""〈꿀 한 숟갈〉 — 따뜻한 그림책 과슈(흔들리는 손그림 윤곽, 붓 결, 크림 종이), 어쿠스틱 기타·셰이커·벌 날갯소리.
사실: 일벌 한 마리가 평생 만드는 꿀은 약 1/12 티스푼(PBS NOVA "The Buzz About Bees" 외 다수, 대략값).
그래서 1 티스푼 ≈ 일벌 12마리의 일생(계산).
"""
import math, numpy as np, cv2, cairo
from base import *
import sfx as S

CREAM = (0.98, 0.93, 0.80); HONEY = (0.95, 0.62, 0.12); HONEY2 = (0.99, 0.80, 0.30); BROWN = (0.33, 0.20, 0.12)
SKY = (0.62, 0.82, 0.88); GRASS = (0.52, 0.72, 0.38); GRASS2 = (0.40, 0.60, 0.30); PINK = (0.95, 0.55, 0.62); WHITE = (1, 0.98, 0.94)

_P = {}
def paper():
    if 'v' in _P: return _P['v']
    r = np.random.default_rng(12)
    f = cv2.GaussianBlur(r.standard_normal((H, W)).astype(np.float32), (0, 0), 2.0 * max(SC, .5))
    b = cv2.resize(r.standard_normal((H // 50 + 2, W // 50 + 2)).astype(np.float32), (W, H), interpolation=cv2.INTER_CUBIC)
    _P['v'] = (1 + 0.05 * f / f.std() + 0.04 * b)[..., None].astype(np.float32); return _P['v']

def wob(pts, amp, seed, t=0.0):
    r = np.random.default_rng(abs(int(seed)) + 1); n = len(pts); ph = r.uniform(0, 6.28, n)
    return [(x + amp * math.sin(ph[i] + t * 6), y + amp * math.cos(ph[i] * 1.3 + t * 6)) for i, (x, y) in enumerate(pts)]
def blob(cr, cx, cy, rx, ry, col, a=1.0, seed=0, t=0.0, line=True, n=28):
    pts = [(cx + rx * math.cos(2 * math.pi * k / n), cy + ry * math.sin(2 * math.pi * k / n)) for k in range(n)]
    pts = wob(pts, max(1.5, min(rx, ry) * 0.04), seed, math.floor(t * 8) / 8)      # 8장/초로 흔들림(손그림 떨림)
    cr.move_to(*pts[0])
    for i in range(n):
        p0, p1 = pts[i], pts[(i + 1) % n]; mx, my = (p0[0] + p1[0]) / 2, (p0[1] + p1[1]) / 2; cr.curve_to(p0[0], p0[1], p0[0], p0[1], mx, my)
    cr.close_path(); cr.set_source_rgba(*col, a)
    if line: cr.fill_preserve(); cr.set_source_rgba(*BROWN, a); cr.set_line_width(4.5); cr.stroke()
    else: cr.fill()

def bee(cr, x, y, s, a, t, seed=0, face=1):
    cr.save(); cr.translate(x, y); cr.scale(s * face, s)
    flap = math.sin(t * 60 + seed) * 0.5 + 0.5
    for dx in (-8, 12):
        blob(cr, dx, -36 - 6 * flap, 22, 30 - 12 * flap, (0.92, 0.97, 1.0), 0.85 * a, seed + dx, t)
    blob(cr, 0, 0, 46, 34, (0.99, 0.80, 0.18), a, seed, t)
    cr.save(); cr.arc(0, 0, 44, 0, 6.283); cr.clip(); cr.set_source_rgba(*BROWN, a)
    for k in (-14, 8): cr.rectangle(k, -40, 12, 80); cr.fill()
    cr.restore()
    cr.set_source_rgba(*BROWN, a); cr.arc(30, -6, 5, 0, 6.283); cr.fill()
    cr.set_line_width(3); cr.arc(30, 6, 8, 0.3, 2.4); cr.stroke()
    cr.restore()

def flower(cr, x, y, s, col, a, seed, t):
    cr.set_source_rgba(*GRASS2, a); cr.set_line_width(7); cr.move_to(x, y); cr.line_to(x + 4, y + 160 * s); cr.stroke()
    for k in range(6):
        ang = k * math.pi / 3 + 0.2; blob(cr, x + 34 * s * math.cos(ang), y + 34 * s * math.sin(ang), 26 * s, 20 * s, col, a, seed + k, t)
    blob(cr, x, y, 20 * s, 20 * s, HONEY2, a, seed + 9, t)

def spoon(cr, x, y, s, fill, a, t):
    s = max(s, 1e-3); cr.save(); cr.translate(x, y); cr.scale(s, s)
    cr.set_source_rgba(0.78, 0.76, 0.72, a); cr.set_line_width(26); cr.move_to(150, 20); cr.line_to(430, 90); cr.stroke()
    blob(cr, 0, 0, 160, 105, (0.86, 0.85, 0.82), a, 77, t)
    if fill > 0:
        cr.save(); cr.arc(0, 0, 140, 0, 6.283); cr.clip()
        blob(cr, 0, 95 - 190 * fill, 150, 95, HONEY, a, 78, t, line=False)
        cr.restore()
        cr.set_source_rgba(1, 1, 1, 0.55 * a * min(1, fill * 3)); cr.arc(-60, -40, 18, 0, 6.283); cr.fill()
    cr.restore()

T_FLY = (3.6, 9.2); T_FILL = (9.4, 15.0); T_HIVE = 15.2; T_CODA = 21.6
def draw(t):
    s, cr = surf()
    g = cairo.LinearGradient(0, 0, 0, DH); g.add_color_stop_rgb(0, *SKY); g.add_color_stop_rgb(0.62, *CREAM); g.add_color_stop_rgb(1, *CREAM); cr.set_source(g); cr.paint()
    blob(cr, 540, 2250, 900, 620, GRASS, 1, 3, t * 0.2)
    blob(cr, 150, 2150, 500, 560, GRASS2, 1, 4, t * 0.2)
    blob(cr, 870, 330, 90, 90, (1.0, 0.86, 0.40), 1, 5, t, line=False)
    # 꽃밭
    fl = [(160, 1480, PINK), (330, 1560, WHITE), (520, 1500, (0.98, 0.78, 0.35)), (720, 1570, PINK), (900, 1490, WHITE)]
    for i, (x, y, c) in enumerate(fl): flower(cr, x, y + 6 * math.sin(t * 1.5 + i), 0.9, c, 1, 20 + i * 10, t)
    # 처음: 숟가락 하나
    if t < T_FLY[0] + 0.3:
        a = 1 - ramp(t, T_FLY[0] - 0.3, T_FLY[0] + 0.3)
        spoon(cr, 420, 980, 1.1 * back_out(ramp(t, 0.2, 0.7), 1.5), 1.0, a, t)
    # 벌 한 마리의 일생: 꽃마다 들른다
    if T_FLY[0] - 0.2 < t < T_FILL[0] + 0.4:
        a = ramp(t, T_FLY[0] - 0.2, T_FLY[0] + 0.3) * (1 - ramp(t, T_FILL[0] - 0.1, T_FILL[0] + 0.4))
        u = ramp(t, *T_FLY) * (len(fl) - 1); i = min(len(fl) - 2, int(u)); f = smooth(u - i)
        x0, y0 = fl[i][0], fl[i][1] - 90; x1, y1 = fl[i + 1][0], fl[i + 1][1] - 90
        bx = lerp(x0, x1, f); by = lerp(y0, y1, f) - 160 * math.sin(math.pi * f)
        bee(cr, bx, by + 6 * math.sin(t * 9), 1.2, a, t, face=1)
        # 평생 모은 한 방울
        d = ramp(t, *T_FLY); blob(cr, 540, 980, 10 + 34 * d, 12 + 40 * d, HONEY, a, 31, t)
        txt(cr, '1/12 teaspoon · 티스푼의 1/12', 540, 1110, 44, BROWN, a * ramp(t, T_FLY[1] - 1.5, T_FLY[1] - 1.0))
    # 열두 마리가 한 숟갈
    if t >= T_FILL[0]:
        a = ramp(t, T_FILL[0], T_FILL[0] + 0.4) * (1 - ramp(t, T_HIVE - 0.2, T_HIVE + 0.4))
        n = int(clamp((t - T_FILL[0] - 0.4) / ((T_FILL[1] - T_FILL[0] - 1.2) / 12), 0, 12))
        spoon(cr, 420, 1080, 1.0, n / 12, a, t)
        for k in range(12):
            if k >= n: continue
            bx = 120 + (k % 6) * 168; by = 660 + (k // 6) * 150
            bee(cr, bx, by + 5 * math.sin(t * 8 + k), 0.75, a * ramp(t, T_FILL[0] + 0.4 + k * 0.38, T_FILL[0] + 0.7 + k * 0.38), t, seed=k)
        txt(cr, f'{n} bees · 꿀벌 {n}마리', 540, 1330, 60, BROWN, a)
    # 벌집 앞, 셀 수 없이 많은 벌
    if t >= T_HIVE:
        a = ramp(t, T_HIVE, T_HIVE + 0.5)
        blob(cr, 540, 1050, 230, 290, (0.86, 0.62, 0.28), a, 90, t)
        cr.set_source_rgba(*BROWN, a); cr.set_line_width(6)
        for k in range(5): cr.move_to(330, 860 + k * 80); cr.curve_to(450, 840 + k * 80, 630, 880 + k * 80, 750, 860 + k * 80); cr.stroke()
        blob(cr, 540, 1250, 50, 36, BROWN, a, 91, t, line=False)
        r = np.random.default_rng(3)
        for k in range(46):
            ang = r.uniform(0, 6.28); rad = r.uniform(300, 520); sp = r.uniform(0.3, 0.8) * (1 if k % 2 else -1)
            x = 540 + rad * math.cos(ang + sp * (t - T_HIVE)); y = 1050 + rad * 0.9 * math.sin(ang + sp * (t - T_HIVE))
            bee(cr, x, y, r.uniform(0.35, 0.55), a * ramp(t, T_HIVE + k * 0.04, T_HIVE + 0.3 + k * 0.04), t, seed=k, face=1 if sp > 0 else -1)
    s.flush(); img = arr(s)[..., :3] * paper()
    return img

def sound(path):
    m = S.Mix(EP['DUR'], 12); G = [196.0, 246.9, 293.7, 392.0, 329.6, 293.7, 246.9, 293.7]
    beat = 0.36; t = 0.2; k = 0
    while t < EP['t_coda']:
        chord = [196.0, 246.9, 293.7] if (k // 8) % 2 == 0 else [164.8, 220.0, 261.6]
        m.put('mus', t, S.guitar([chord[0], chord[1], chord[2], chord[1] * 2, chord[2], chord[1], chord[0] * 2, chord[1]][k % 8], 1.4, 0.38))
        if k % 2 == 1: m.put('fx', t, S.shaker(0.1, 0.10, k))
        t += beat; k += 1
    n = int((T_FLY[1] - T_FLY[0]) * S.SR); tt = np.arange(n) / S.SR
    buzz = np.sin(2 * np.pi * np.cumsum(230 + 18 * np.sin(2 * np.pi * 3 * tt)) / S.SR); buzz = S.band(np.sign(buzz) * 0.5 + buzz, 150, 2500)
    m.put('fx', T_FLY[0], 0.10 * S.norm(buzz) * np.minimum(1, tt / 0.5) * np.minimum(1, (tt[-1] - tt) / 0.5))
    for k in range(4): m.put('fx', T_FLY[0] + (k + 1) * (T_FLY[1] - T_FLY[0]) / 4.2, S.drop(1300, 0.25))
    for k in range(12): m.put('mus', T_FILL[0] + 0.4 + k * 0.38, S.marimba(G[k % 8] * 2, 0.8, 0.35)); m.put('fx', T_FILL[0] + 0.4 + k * 0.38, S.drop(800 + 40 * k, 0.25))
    n2 = int(5.5 * S.SR); tt = np.arange(n2) / S.SR
    hive = sum(np.sin(2 * np.pi * np.cumsum(f * (1 + 0.01 * np.sin(2 * np.pi * r * tt))) / S.SR) for f, r in ((210, 3), (240, 4.1), (262, 2.7), (190, 3.5)))
    m.put('fx', T_HIVE, 0.12 * S.norm(S.band(hive, 120, 2000)) * np.minimum(1, tt / 0.8) * np.minimum(1, (tt[-1] - tt) / 0.8))
    tc = EP['t_coda']
    for i in range(3): m.put('mus', tc + 0.8 + i * STEP, S.guitar([392.0, 329.6, 293.7][i], 2.6, 0.5)); m.put('mus', tc + 0.8 + i * STEP, S.guitar([196.0, 164.8, 146.8][i], 2.6, 0.4))
    m.put('amb', tc, S.drone([98, 146.8, 196], EP['t_end'] - tc, 0.12, 'sine'))
    for j, f in enumerate([392.0, 493.9, 587.3]): m.put('mus', EP['t_end'] + 0.15 + 0.1 * j, S.guitar(f, 2.2, 0.45))
    m.write(path, rev_mus=1.4, wet_mus=0.2)

EP = finalize(dict(t_coda=T_CODA, draw=draw, sound=sound, end_icon='drop', grain=0.005,
    title_en_card='ONE SPOONFUL', title_ko_card='꿀 한 숟갈',
    pal=dict(hi=HONEY, endbg=CREAM),
    card_style=dict(box='paper', bg=(1.0, 0.97, 0.88), ink=BROWN, hi=(0.86, 0.45, 0.05), y=150, r=40, fe=BLK, fk=BLK),
    cards=[(0.3, 3.4, ['How many bees does it take', 'to fill *one spoonful*?'], ['꿀 *한 숟갈*에는', '벌이 몇 마리나 필요할까?']),
           (3.8, 9.2, ['One worker bee, her whole life:', 'about *1/12 of a teaspoon*.'], ['일벌 한 마리가 평생 모으는 꿀은', '티스푼의 *12분의 1*']),
           (9.6, 15.0, ['One teaspoon:', 'the lives of *12 bees*.'], ['티스푼 하나는', '꿀벌 *12마리*의 일생']),
           (15.4, 21.4, ['Every jar holds the work', 'of *hundreds* of tiny lives.'], ['꿀 한 병에는', '*수백* 마리의 일생이 담겨 있다'])],
    coda=[('Twelve small lives', '작은 생명 열둘이'), ('became one spoonful of sweetness.', '한 숟갈의 단맛이 되었다'), ('Taste slowly. Nothing sweet is small.', '천천히 맛보자, 작은 단맛은 없다')],
    coda_style=dict(dim=0.68, blur=12, tint=(0.25, 0.14, 0.04), ink=(1.0, 0.96, 0.86), hi=(1.0, 0.78, 0.35), fe=SERIF),
    sources=['A worker bee makes about 1/12 teaspoon of honey in her lifetime (PBS NOVA, "The Buzz About Bees"; approximate).'],
    yt=dict(title_en='One Spoonful of Honey Is the Life of 12 Bees #Shorts', title_ko='꿀 한 숟갈은 꿀벌 12마리의 일생')))

if __name__ == '__main__': main(EP)
