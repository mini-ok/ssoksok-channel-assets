"""〈남극 얼음이 다 녹으면〉 — 픽셀아트(135×240 저해상도를 그대로 키움, 제한된 색), 소리는 바람·얼음 갈라짐·낮은 패드.
사실(NASA Sea Level Change, NASA Science): 남극 얼음이 모두 녹으면 해수면 약 58 m 상승. 해마다 평균 약 1,500억 톤을 잃는다.
남극 빙상은 지구 민물의 약 60%(Shiklomanov 1993 인용). 한 층 3 m로 보면 58 m ≈ 19층(계산).
"""
import math, numpy as np, cv2, cairo
from base import *
import sfx as S

PW, PH = 135, 240; K = DW / PW                               # 픽셀 1칸 = 8 설계 px
SKY1 = (0.42, 0.62, 0.86); SKY2 = (0.70, 0.84, 0.95); SEA = (0.10, 0.32, 0.62); SEA2 = (0.18, 0.45, 0.75)
ICE = (0.92, 0.97, 1.0); ICE2 = (0.70, 0.84, 0.95); BLD = (0.36, 0.38, 0.46); WIN = (0.98, 0.86, 0.42); DARK = (0.12, 0.13, 0.20)
T_RISE = 3.8; T_FLOOR = 8.8; T_LOSS = 13.6; T_CODA = 18.8
GROUND = 214; FLOOR_PX = 6                                   # 픽셀 단위, 한 층 = 6칸(3 m)
BUILDINGS = [(8, 12, 9), (24, 16, 21), (44, 14, 14), (62, 20, 24), (86, 14, 17), (104, 22, 11)]

def low(fn):
    s = cairo.ImageSurface(cairo.FORMAT_ARGB32, PW, PH); cr = cairo.Context(s); cr.set_antialias(cairo.ANTIALIAS_NONE); fn(cr)
    a = np.ndarray((PH, PW, 4), np.uint8, s.get_data()).astype(np.float32) / 255
    return cv2.resize(a, (W, H), interpolation=cv2.INTER_NEAREST)

def rect(cr, x, y, w, h, c): cr.set_source_rgb(*c); cr.rectangle(int(x), int(y), int(w), int(h)); cr.fill()

def draw(t):
    def scene(cr):
        for y in range(PH):                                  # 띠진 하늘
            c = SKY1 if y < 60 else (SKY2 if y < 130 else (0.80, 0.90, 0.97)); rect(cr, 0, y, PW, 1, c)
        a1 = 1 - ramp(t, T_RISE - 0.4, T_RISE)
        if a1 > 0.5:                                         # 남극 빙상
            rect(cr, 0, 150, PW, 90, SEA)
            for x in range(10, 126):
                h = int(40 + 18 * math.sin(x * 0.07) + 6 * math.sin(x * 0.31)); rect(cr, x, 150 - h, 1, h, ICE if (x // 3) % 5 else ICE2)
            rect(cr, 10, 150, 116, 6, ICE2)
            for k in range(6):
                x = 20 + k * 17 + int(2 * math.sin(t * 2 + k)); rect(cr, x, 160 + (k % 2) * 8, 3, 2, ICE)
        else:
            for x0, w, fl in BUILDINGS:                        # 해안 도시
                top = GROUND - fl * FLOOR_PX; rect(cr, x0, top, w, fl * FLOOR_PX, BLD)
                for f in range(fl):
                    for wx in range(x0 + 2, x0 + w - 2, 4): rect(cr, wx, GROUND - f * FLOOR_PX - 4, 2, 2, WIN if (wx + f) % 3 else DARK)
            rect(cr, 0, GROUND, PW, PH - GROUND, (0.45, 0.42, 0.36))
            lvl = 58 / 3 * FLOOR_PX * smooth(ramp(t, T_RISE + 0.6, T_FLOOR + 2.0))       # 58 m = 116칸
            wy = GROUND - lvl + 1.5 * math.sin(t * 2)
            rect(cr, 0, wy, PW, PH - wy, SEA)
            for x in range(0, PW, 6): rect(cr, x + int(t * 6) % 6, int(wy), 3, 1, SEA2)
            if t > T_LOSS - 0.4:                             # 떨어져 나가는 얼음 덩어리
                for k in range(5):
                    u = ((t - T_LOSS) * 0.6 + k * 0.2) % 1
                    x = 10 + k * 25; y = int(wy - 6 + u * 20)
                    rect(cr, x, y, 10, 6, ICE); rect(cr, x, y + 6, 10, 2, ICE2)
            # 눈금: 왼쪽 기둥
            for f in range(0, 20, 5): rect(cr, 2, GROUND - f * FLOOR_PX, 4, 1, DARK)
    img = low(scene)[..., :3]
    s2, c2 = surf(); ink = (0.08, 0.10, 0.20)
    def lab(text, x, y, size, a, col=(1, 1, 1), anchor='c'):
        txt(c2, text, x + 4, y + 4, size, ink, a * 0.9, fam=BLK, anchor=anchor); txt(c2, text, x, y, size, col, a, fam=BLK, anchor=anchor)
    if t < T_RISE:
        a = ramp(t, 0.6, 1.1) * (1 - ramp(t, T_RISE - 0.4, T_RISE))
        lab('~60% of Earth’s fresh water', 540, 1560, 46, a); lab('지구 민물의 약 60%', 540, 1625, 44, a, (0.8, 0.92, 1.0))
    else:
        u = smooth(ramp(t, T_RISE + 0.6, T_FLOOR + 2.0)); m = 58 * u
        a = ramp(t, T_RISE + 0.4, T_RISE + 0.8) * (1 - ramp(t, T_CODA - 0.4, T_CODA))
        lab(f'+{m:4.1f} m', 540, 1740, 110, a)
        lab(f'≈ {int(m / 3)} floors · {int(m / 3)}층', 540, 1840, 50, a * ramp(t, T_FLOOR, T_FLOOR + 0.4), (0.8, 0.92, 1.0))
        if t > T_LOSS: lab('−150 billion t / yr · 해마다 1,500억 톤', 540, 1580, 40, a * ramp(t, T_LOSS, T_LOSS + 0.4), (1, 1, 1))
    return over(img, s2)

def sound(path):
    m = S.Mix(EP['DUR'], 161); tc = EP['t_coda']
    m.put('amb', 0, S.breath(EP['t_end'] + 1, 0.3, seed=2))
    m.put('amb', 0, S.drone([55.0, 82.4, 110.0, 164.8], EP['t_end'] + 1, 0.22, 'sine'))
    for t in (1.2, 2.6, T_RISE - 0.2): m.put('fx', t, S.icecrack(0.6, int(t * 10)))
    for k in range(20):
        t = T_RISE + 0.6 + k * (T_FLOOR + 1.4 - T_RISE) / 20
        m.put('fx', t, S.drop(300 + 40 * k, 0.25))
    for t in np.arange(T_LOSS + 0.2, T_CODA - 0.4, 1.0): m.put('fx', t, S.icecrack(0.5, int(t * 7))); m.put('fx', t + 0.4, S.drop(180, 0.4))
    for i, f in enumerate([220.0, 261.6, 329.6, 293.7]): m.put('mus', T_FLOOR + i * 1.0, S.bell(f * 2, 3.0, 0.22))
    m.put('amb', tc, S.drone([110.0, 164.8, 220.0], EP['t_end'] - tc, 0.18, 'sine'))
    for i, f in enumerate([659.3, 587.3, 440.0]): m.put('mus', tc + 0.8 + i * STEP, S.bell(f, 3.5, 0.28))
    m.write(path, rev_mus=3.5, wet_mus=0.45)

EP = finalize(dict(t_coda=T_CODA, draw=draw, sound=sound, end_icon='drop', grain=0.0,
    title_en_card='IF ANTARCTICA MELTED', title_ko_card='남극 얼음이 다 녹으면',
    pal=dict(hi=SEA, endbg=(0.92, 0.96, 1.0)),
    card_style=dict(box=None, ink=(0.06, 0.10, 0.22), hi=(0.85, 0.20, 0.20), y=150, fe=BLK, fk=BLK),
    cards=[(0.3, 3.6, ['Antarctica holds about *60%*', 'of the world’s fresh water.'], ['남극 얼음은 지구 민물의', '약 *60%*']),
           (3.8, 8.6, ['If it all melted,', 'seas would rise *58 metres*.'], ['모두 녹으면', '바다가 *58m* 높아진다']),
           (8.8, 13.4, ['That is a *19-story* building', 'underwater.'], ['*19층* 건물이', '물에 잠기는 높이']),
           (13.6, 18.6, ['It is losing about', '*150 billion tonnes* a year.'], ['지금도 해마다', '*1,500억 톤*씩 줄고 있다'])],
    coda=[('Ice holds the sea in place,', '얼음은 바다를 붙잡고 있다'), ('quietly, for millions of years.', '수백만 년 동안 묵묵히'), ('Care for what quietly holds you up.', '묵묵히 나를 받쳐 주는 것을 돌보자')],
    coda_style=dict(dim=0.55, blur=8, tint=(0.70, 0.84, 0.95), ink=(0.06, 0.10, 0.22), hi=(0.85, 0.20, 0.20)),
    sources=['NASA Sea Level Change: the Antarctic ice sheet could raise global mean sea level by 58 m if it all melted; it loses ~150 billion tonnes a year.', 'Antarctic ice ≈ 60% of world fresh water (Shiklomanov 1993). 19 floors assumes 3 m per floor.'],
    yt=dict(title_en='If Antarctica Melted, Seas Would Rise 58 Meters #Shorts', title_ko='남극 얼음이 다 녹으면 바다가 58m 높아진다')))

if __name__ == '__main__': main(EP)
