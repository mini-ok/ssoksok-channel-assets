"""〈먼저 살다 간 사람들〉 — 점묘화(보색 붓점을 겹쳐 찍은 캔버스), 소리는 합창 패드와 아주 작은 점 소리.
사실(PRB, Kaneda & Haub "How Many People Have Ever Lived on Earth?" 2022 갱신): 기원전 190,000년 이후 태어난 사람 약 1,170억 명.
2022년 인구 약 79.6억 = 태어난 사람의 6.8%. 지금 사는 한 사람당 먼저 산 사람 약 13.7명(계산: (117 − 8) ÷ 8).
"""
import math, numpy as np, cv2, cairo
from base import *
import sfx as S

COLS, ROWS = 30, 39; N = COLS * ROWS; LIVE = 80            # 점 하나 = 1억 명
X0, Y0, SP = 134, 525, 28.0
T_FILL = (3.8, 9.4); T_LIVE = 9.8; T_ONE = 15.0; T_CODA = 23.0
GOLD = (1.0, 0.72, 0.22); BLUE = (0.30, 0.42, 0.75); VIO = (0.55, 0.40, 0.70)
_r = np.random.default_rng(8)

def _canvas():
    """점묘 바탕: 크림·하늘·보라·연두 붓점을 겹쳐 찍은 캔버스(한 번만 그림)."""
    s, cr = surf(); cr.set_source_rgb(0.93, 0.90, 0.82); cr.paint()
    pal = [(0.85, 0.80, 0.66), (0.70, 0.78, 0.86), (0.80, 0.72, 0.84), (0.78, 0.84, 0.66), (0.95, 0.86, 0.62)]
    for k in range(26000):
        x, y = _r.uniform(0, DW), _r.uniform(0, DH); c = pal[_r.integers(len(pal))]
        cr.set_source_rgba(*c, 0.55); cr.save(); cr.translate(x, y); cr.rotate(_r.uniform(0, 3.14)); cr.scale(1, 0.6); cr.arc(0, 0, _r.uniform(3, 6), 0, 6.283); cr.restore(); cr.fill()
    return arr(s)[..., :3].copy()
CANVAS = _canvas()
POS = np.array([(X0 + (i % COLS) * SP, Y0 + (i // COLS) * SP) for i in range(N)], np.float32)
JIT = _r.uniform(0, 6.283, (N, 5)); DAB = _r.uniform(0.5, 1.0, (N, 5))
YOU = N - 41                                                  # 살아 있는 점 하나 = "당신"
BEFORE = _r.choice(N - LIVE, 14, replace=False); BEFORE_S = set(BEFORE.tolist())

def dot(cr, x, y, r, cols, a, i):
    for k in range(5):                                        # 한 점 = 붓점 다섯
        c = cols[k % len(cols)]; ang = JIT[i, k]; d = r * 0.45 * DAB[i, k]
        cr.set_source_rgba(*c, a); cr.arc(x + d * math.cos(ang), y + d * math.sin(ang), r * 0.55, 0, 6.283); cr.fill()

def draw(t):
    s, cr = surf()
    zoom = 1 - smooth(ramp(t, 1.4, T_FILL[0] + 0.4))          # 처음엔 "당신" 한 점을 크게
    fill = ramp(t, *T_FILL); live = smooth(ramp(t, T_LIVE, T_LIVE + 1.0)); one = smooth(ramp(t, T_ONE, T_ONE + 1.0))
    yx, yy = POS[YOU]
    sc = lerp(1, 9, zoom); ox, oy = lerp(0, 540 - yx * 9, zoom), lerp(0, 1100 - yy * 9, zoom)
    cr.save(); cr.translate(ox, oy); cr.scale(sc, sc)
    for i in range(N):
        x, y = POS[i]; alive = i >= N - LIVE
        if i == YOU: a = 1.0
        else:
            ap = ramp(fill * N, i - 30, i)                     # 시간 순서로 하나씩 찍힘
            if ap <= 0: continue
            a = ap
        if alive:
            cols = [GOLD, (1.0, 0.55, 0.25), (1.0, 0.85, 0.45)]; a *= lerp(0.55, 1.0, live)
        else:
            cols = [BLUE, VIO, (0.35, 0.60, 0.70)]; a *= lerp(0.85, 0.45, live)
            if one > 0 and i in BEFORE_S: a = lerp(a, 1.0, one); cols = [VIO, (0.75, 0.35, 0.80), (0.95, 0.55, 0.85)] if one > 0.3 else cols
        r = 11.5 * (1 + (0.25 * math.sin(t * 3 + i) if i == YOU else 0) + (0.5 * one if i in BEFORE_S else 0))
        dot(cr, x, y, r, cols, a, i)
    if one > 0:                                               # 당신 한 사람과 먼저 산 14명
        for j, b in enumerate(BEFORE):
            u = ramp(t, T_ONE + 0.1 * j, T_ONE + 0.1 * j + 0.5)
            if u <= 0: continue
            bx, by = POS[b]; cr.set_source_rgba(*VIO, 0.55 * u); cr.set_line_width(1.6)
            cr.move_to(yx, yy); cr.line_to(lerp(yx, bx, u), lerp(yy, by, u)); cr.stroke()
    if one > 0:
        cr.set_source_rgba(0.75, 0.40, 0.05, one); cr.set_line_width(3); cr.arc(yx, yy, 20, 0, 6.283); cr.stroke()
    cr.restore()
    # "당신" 표시와 숫자
    if t < T_FILL[0] + 0.3:
        a = ramp(t, 0.4, 0.9) * (1 - ramp(t, T_FILL[0] - 0.2, T_FILL[0] + 0.3))
        txt(cr, 'you · 당신', 540, 1100 + 150, 46, (0.35, 0.25, 0.15), a, fam=BLK)
    fa = ramp(t, T_FILL[0], T_FILL[0] + 0.5) * (1 - ramp(t, T_CODA - 0.5, T_CODA))
    if fa > 0:
        txt(cr, '190,000 BCE', X0, Y0 - 40, 28, (0.30, 0.32, 0.50), fa, fam=BOLD, anchor='l')
        txt(cr, '2022', X0 + (COLS - 1) * SP, Y0 + ROWS * SP + 30, 28, (0.75, 0.45, 0.12), fa * ramp(fill, 0.95, 1), fam=BOLD, anchor='r')
        n = 117.0 * min(1, fill)
        txt(cr, f'{n:,.0f} billion · {n * 10:,.0f}억 명', 540, 1760, 54, (0.25, 0.25, 0.45), fa * (1 - live), fam=BLK)
        txt(cr, '8 billion alive · 지금 사는 80억 명 = 6.8%', 540, 1760, 46, (0.70, 0.40, 0.08), fa * live * (1 - one), fam=BLK)
        txt(cr, '1 alive : ~14 before · 한 사람 : 앞서 산 약 14명', 540, 1760, 42, (0.40, 0.28, 0.55), fa * one, fam=BLK)
    img = CANVAS * 1.0
    return over(img, s)

def sound(path):
    m = S.Mix(EP['DUR'], 51); tc = EP['t_coda']
    ch = [[130.8, 196.0, 261.6, 329.6], [110.0, 164.8, 220.0, 261.6], [116.5, 174.6, 233.1, 293.7], [130.8, 196.0, 261.6, 392.0]]
    for k, t0 in enumerate([0.0, T_FILL[0], T_LIVE, T_ONE]):
        dur = [T_FILL[0], T_LIVE, T_ONE, tc][k] - t0 + 1.0
        m.put('mus', t0, S.choir(ch[k], dur, 0.35, 'a' if k % 2 else 'o', seed=k))
    m.put('fx', 0.5, S.marimba(523.3, 1.5, 0.4))
    n = 0
    for i in range(120):                                       # 점이 찍히는 작은 소리(점 10개마다 하나)
        t = T_FILL[0] + (T_FILL[1] - T_FILL[0]) * i / 120
        m.put('fx', t, S.click(0.12, i)); n += 1
    m.put('fx', T_LIVE, S.bell(784.0, 3.0, 0.35)); m.put('fx', T_LIVE + 0.1, S.bell(1174.7, 3.0, 0.2))
    for j in range(14): m.put('fx', T_ONE + 0.1 * j, S.pluck(392.0 * (1 + 0.06 * (j % 5)), 0.6, 0.12, seed=j))
    m.put('mus', tc, S.choir([98.0, 146.8, 196.0, 246.9], EP['t_end'] - tc + 1.5, 0.4, 'o', seed=9))
    for i in range(3): m.put('mus', tc + 0.8 + i * STEP, S.bell([587.3, 659.3, 784.0][i], 3.0, 0.28))
    m.put('fx', EP['t_end'] + 0.2, S.bell(1568, 2.0, 0.3))
    m.write(path, rev_mus=3.5, wet_mus=0.45)

EP = finalize(dict(t_coda=T_CODA, draw=draw, sound=sound, end_icon='heart', grain=0.005,
    title_en_card='BEFORE US', title_ko_card='먼저 살다 간 사람들',
    pal=dict(hi=GOLD, endbg=(0.93, 0.90, 0.82)),
    card_style=dict(box='paper', bg=(0.97, 0.95, 0.90), ink=(0.22, 0.20, 0.32), hi=(0.85, 0.50, 0.10), y=110, fe=BLK, fk=BLK),
    cards=[(0.3, 3.6, ['How many people', 'have *ever* been born?'], ['지금까지 태어난 사람은', '*모두* 몇 명일까?']),
           (3.8, 9.6, ['About *117 billion*.', 'Each dot = 100 million people.'], ['약 *1,170억 명*', '점 하나 = 1억 명']),
           (9.8, 14.8, ['Everyone alive today: *8 billion*.', 'Just *7%* of them.'], ['지금 살아 있는 사람 모두 *80억*', '겨우 *7%*']),
           (15.0, 22.8, ['For each of us alive,', 'about *14* lived before.'], ['지금 사는 한 사람마다', '앞서 산 사람이 약 *14명*'])],
    coda=[('Over a hundred billion lived before us.', '우리보다 먼저 천억이 넘는 사람이 살았다'), ('Each of them had one turn.', '모두에게 차례는 한 번뿐이었다'), ('Live the turn you were given.', '주어진 차례를 살자')],
    coda_style=dict(dim=0.78, blur=10, tint=(0.93, 0.90, 0.82), ink=(0.22, 0.20, 0.32), hi=(0.80, 0.45, 0.08)),
    sources=['Population Reference Bureau, Kaneda & Haub, "How Many People Have Ever Lived on Earth?" (2022 update): ~117 billion ever born; 2022 population ≈ 6.8% of them.', '“About 14 before” = (117 − 8) ÷ 8 ≈ 13.6 (calculated).'],
    yt=dict(title_en='117 Billion People Have Ever Lived. You Are One of the 7% #Shorts', title_ko='지금까지 태어난 사람 1,170억 명, 살아 있는 건 7%')))

if __name__ == '__main__': main(EP)
