"""〈흰긴수염고래의 심장〉 — 우키요에풍 목판 인쇄(평평한 남색·쪽빛·크림, 검은 윤곽선, 물결 줄무늬, 화지 결, 붉은 낙관), 소리는 고토와 샤쿠하치.
사실(NOAA Fisheries "Big-Hearted Blue Whale"): 몸길이 최대 약 33 m(110 ft), 심장 약 180 kg(400 lb, 스튜디오 피아노 무게),
심장 소리는 약 3 km(2 mi) 밖에서도 들린다. 한 번 뛸 때 약 227 L(60 gal)를 보낸다(사람은 약 70 mL, 2.4 oz).
"""
import math, numpy as np, cv2, cairo
from base import *
import sfx as S

CREAM = (0.94, 0.89, 0.78); INDIGO = (0.12, 0.20, 0.38); PRUS = (0.16, 0.36, 0.58); SKY = (0.80, 0.84, 0.82); RED = (0.75, 0.20, 0.15); INK = (0.08, 0.07, 0.08)
WHALE = (0.36, 0.44, 0.55)
T_HEART = 3.8; T_SOUND = 8.8; T_PUMP = 13.6; T_CODA = 18.8
_r = np.random.default_rng(17)
_f = cv2.GaussianBlur(_r.random((H, W)).astype(np.float32), (0, 0), sigmaX=0.6 * SC, sigmaY=6 * SC)
WASHI = (0.93 + 0.1 * _f)[..., None]

def outline(cr, w=4): cr.set_source_rgba(*INK, 1); cr.set_line_width(w); cr.stroke()

def waves(cr, y0, t, amp=24, n=6, col=PRUS):
    for k in range(n):
        y = y0 + k * 46; ph = t * (0.6 + 0.1 * k) + k
        cr.move_to(0, DH); cr.line_to(0, y)
        for x in range(0, DW + 20, 20): cr.line_to(x, y + amp * math.sin(x / 90 + ph) * (1 - k * 0.1))
        cr.line_to(DW, DH); cr.close_path()
        cr.set_source_rgb(*(col if k % 2 == 0 else INDIGO)); cr.fill_preserve(); outline(cr, 3)
        for x in range(30, DW, 120):                           # 거품 갈퀴
            yy = y + amp * math.sin(x / 90 + ph) * (1 - k * 0.1)
            if math.sin(x / 90 + ph) > 0.6:
                for j in range(3): cr.set_source_rgb(*CREAM); cr.arc(x + j * 12, yy - 4 - j * 3, 7 - j, 0, 6.283); cr.fill()

def whale(cr, x, y, s, a=1.0, t=0.0):
    cr.save(); cr.translate(x, y); cr.scale(s, s); cr.rotate(0.03 * math.sin(t * 0.7))
    cr.move_to(-300, 0); cr.curve_to(-280, -60, -120, -80, 60, -70); cr.curve_to(200, -60, 280, -30, 330, -20)
    cr.curve_to(360, -60, 400, -80, 430, -70); cr.curve_to(410, -30, 400, -10, 430, 30); cr.curve_to(390, 20, 360, 0, 330, 10)
    cr.curve_to(250, 40, 100, 60, -60, 55); cr.curve_to(-200, 50, -290, 40, -300, 0); cr.close_path()
    cr.set_source_rgba(*WHALE, a); cr.fill_preserve(); outline(cr, 4 / s)
    cr.set_source_rgba(*CREAM, a); cr.set_line_width(2 / s)
    for k in range(6): cr.move_to(-260 + k * 8, 20 + k * 4); cr.line_to(-60 + k * 10, 46 + k * 1); cr.stroke()          # 목 주름
    for k in range(14): cr.arc(-150 + (k * 37) % 380, -40 + (k * 13) % 50, 4, 0, 6.283); cr.fill()                   # 얼룩
    cr.set_source_rgba(*INK, a); cr.arc(-230, -10, 6, 0, 6.283); cr.fill()
    cr.move_to(-20, 40); cr.curve_to(10, 90, 50, 110, 80, 110); cr.curve_to(60, 80, 40, 60, 20, 45); cr.set_source_rgba(*WHALE, a); cr.fill_preserve(); outline(cr, 3 / s)
    cr.restore()

def heart(cr, x, y, s, beat=0.0):
    k = s * (1 + 0.08 * beat)
    cr.move_to(x, y + 30 * k); cr.curve_to(x - 70 * k, y - 10 * k, x - 50 * k, y - 70 * k, x, y - 40 * k); cr.curve_to(x + 50 * k, y - 70 * k, x + 70 * k, y - 10 * k, x, y + 30 * k)
    cr.set_source_rgb(*RED); cr.fill_preserve(); outline(cr, 4)

def piano(cr, x, y, s):
    cr.rectangle(x - 80 * s, y - 120 * s, 160 * s, 120 * s); cr.set_source_rgb(*INK); cr.fill()
    cr.rectangle(x - 74 * s, y - 70 * s, 148 * s, 18 * s); cr.set_source_rgb(*CREAM); cr.fill()
    for k in range(10): cr.rectangle(x - 70 * s + k * 15 * s, y - 70 * s, 6 * s, 10 * s); cr.set_source_rgb(*INK); cr.fill()

def cartouche(cr, x, y, w, h, lines, a):
    cr.set_source_rgba(*CREAM, a); cr.rectangle(x, y, w, h); cr.fill(); cr.set_source_rgba(*INK, a); cr.set_line_width(3); cr.rectangle(x, y, w, h); cr.stroke()
    cr.rectangle(x + 8, y + 8, w - 16, h - 16); cr.set_line_width(1.2); cr.stroke()
    for k, (tx, sz, col) in enumerate(lines): txt(cr, tx, x + w / 2, y + 60 + k * (sz + 18), sz, col, a, fam=BLK)

def draw(t):
    s, cr = surf(); cr.set_source_rgb(*SKY); cr.paint()
    g = cairo.LinearGradient(0, 400, 0, 1100); g.add_color_stop_rgba(0, *PRUS, 0.0); g.add_color_stop_rgba(1, *PRUS, 0.55); cr.set_source(g); cr.rectangle(0, 400, DW, 700); cr.fill()
    cr.set_source_rgb(*RED); cr.arc(860, 560, 70, 0, 6.283); cr.fill()                                                 # 붉은 해
    cr.rectangle(0, 820, DW, DH - 820); cr.set_source_rgb(*PRUS); cr.fill()                                         # 바다
    for k in range(9):
        y = 840 + k * 55; cr.set_source_rgba(*INDIGO, 0.25 + 0.06 * k); cr.rectangle(0, y, DW, 55); cr.fill()
        cr.set_source_rgba(*CREAM, 0.35); cr.set_line_width(2)
        for x in range(-40, DW, 160): cr.move_to(x + (k * 50 + t * 20) % 160, y + 10); cr.curve_to(x + 40 + (k * 50 + t * 20) % 160, y, x + 80 + (k * 50 + t * 20) % 160, y + 20, x + 120 + (k * 50 + t * 20) % 160, y + 10); cr.stroke()
    beat = math.exp(-((t * 0.9) % 1 / 0.08) ** 2) if t > T_HEART else 0
    wa = 1 - ramp(t, T_HEART - 0.3, T_HEART)
    if wa > 0:
        whale(cr, 520 + 30 * math.sin(t * 0.5), 1060, lerp(0.9, 1.15, smooth(ramp(t, 0.2, 3.4))), wa, t)
    ha = ramp(t, T_HEART - 0.2, T_HEART + 0.4) * (1 - ramp(t, T_SOUND - 0.3, T_SOUND))
    if ha > 0:
        heart(cr, 380, 1050, 2.6, beat); piano(cr, 790, 1110, 1.4)
    sa = ramp(t, T_SOUND - 0.2, T_SOUND + 0.4) * (1 - ramp(t, T_PUMP - 0.3, T_PUMP))
    if sa > 0:
        whale(cr, 300, 1180, 0.55, sa, t)
        for k in range(5):
            r = ((t - T_SOUND) * 160 + k * 140) % 700
            cr.set_source_rgba(*CREAM, sa * (1 - r / 700)); cr.set_line_width(5); cr.arc(300, 1180, r, -1.2, 1.2); cr.stroke()
        cr.set_source_rgb(*INK); cr.rectangle(885, 1150, 30, 60); cr.fill(); cr.arc(900, 1132, 18, 0, 6.283); cr.fill()            # 3 km 밖 배 위의 사람
        cr.move_to(810, 1205); cr.line_to(990, 1205); cr.line_to(960, 1245); cr.line_to(840, 1245); cr.close_path(); cr.set_source_rgb(*CREAM); cr.fill_preserve(); outline(cr, 4)
    pa = ramp(t, T_PUMP - 0.2, T_PUMP + 0.4) * (1 - ramp(t, T_CODA - 0.4, T_CODA))
    if pa > 0:
        fill = smooth(ramp(t, T_PUMP + 0.6, T_PUMP + 2.8))
        for (x, w, h, f) in ((330, 300, 420, fill), (800, 40, 52, fill)):          # 227 L 통 / 70 mL 컵(높이 비는 대략)
            cr.rectangle(x - w / 2, 1300 - h, w, h); cr.set_source_rgb(*CREAM); cr.fill()
            cr.rectangle(x - w / 2, 1300 - h * f, w, h * f); cr.set_source_rgb(*RED); cr.fill()
            cr.rectangle(x - w / 2, 1300 - h, w, h); outline(cr, 4)
    waves(cr, 1330, t)
    img = arr(s)[..., :3] * WASHI
    s2, c2 = surf()
    if ha > 0: cartouche(c2, 140, 1430, 800, 230, [('≈ 180 kg · 약 180kg', 52, INK), ('as heavy as a piano · 피아노 한 대 무게', 36, INK)], ha)
    if sa > 0: cartouche(c2, 140, 1430, 800, 230, [('heard 3 km away', 52, INK), ('3km 밖에서도 들린다', 44, INK)], sa)
    if pa > 0:
        cartouche(c2, 140, 1430, 800, 230, [('227 L per beat · 한 번에 227L', 46, INK), ('you: ~70 mL · 사람은 약 70mL', 40, RED)], pa)
    c2.set_source_rgba(*RED, 0.9); c2.rectangle(930, 1780, 90, 90); c2.fill()                                         # 낙관
    txt(c2, '虛', 975, 1845, 60, CREAM, 1, fam=BLK)
    return over(img, s2)

def sound(path):
    m = S.Mix(EP['DUR'], 181); tc = EP['t_coda']
    m.put('amb', 0, S.stream(EP['t_end'] + 1, 0.2, seed=4))
    hira = [293.7, 311.1, 392.0, 440.0, 466.2, 587.3]           # 일본 음계(히라조시 계열)
    seq = [0, 2, 3, 4, 3, 2, 1, 0, 2, 4, 5, 4, 3, 2]
    for k, i in enumerate(seq):
        t = 0.4 + k * 0.85
        if t < tc - 0.5: m.put('mus', t, S.koto(hira[i], 2.0, 0.3, seed=k))
    for st, f, d in ((1.0, 587.3, 2.2), (4.6, 440.0, 2.6), (9.4, 466.2, 2.0), (12.0, 392.0, 2.4), (15.0, 587.3, 3.0)):
        m.put('mus', st, S.shakuhachi(f, d, 0.28, seed=int(st)))
    t = T_HEART
    while t < T_PUMP + 4:
        m.put('fx', t, S.kick(38, 0.75, 0.5)); t += 1 / 0.9 * 2.2       # 아주 느린 심장
    for k in range(5): m.put('fx', T_SOUND + 0.2 + k * 0.85, S.sonar(300, 0.15))
    m.put('fx', T_PUMP + 0.6, S.bubbles(2.0, 10, 0.3))
    m.put('amb', tc, S.drone([73.4, 110.0, 146.8], EP['t_end'] - tc, 0.15, 'sine'))
    for i, f in enumerate([587.3, 466.2, 392.0]): m.put('mus', tc + 0.8 + i * STEP, S.koto(f, 3.0, 0.32, seed=i))
    m.put('mus', tc + 0.4, S.shakuhachi(293.7, 5.0, 0.22, seed=9))
    m.write(path, rev_mus=2.8, wet_mus=0.38)

EP = finalize(dict(t_coda=T_CODA, draw=draw, sound=sound, end_icon='heart', grain=0.0,
    title_en_card='THE BIGGEST HEART', title_ko_card='가장 큰 심장',
    pal=dict(hi=INDIGO, endbg=CREAM),
    card_style=dict(box=None, ink=INK, hi=RED, y=150, fe=BLK, fk=BLK),
    cards=[(0.3, 3.6, ['The blue whale: the largest animal', '*ever* to live on Earth.'], ['흰긴수염고래는 지구에 산', '*역대 가장 큰* 동물']),
           (3.8, 8.6, ['Its heart weighs about *180 kg*,', 'as much as a piano.'], ['심장 무게만 약 *180kg*,', '피아노 한 대만 하다']),
           (8.8, 13.4, ['Its heartbeat can be heard', '*3 km* away.'], ['심장 소리가', '*3km* 밖에서도 들린다']),
           (13.6, 18.6, ['Each beat pushes *227 litres*.', 'Yours: about 70 mL.'], ['한 번 뛸 때 *227L*,', '사람은 약 70mL'])],
    coda=[('The biggest heart on Earth', '지구에서 가장 큰 심장은'), ('beats slowly, deep in the dark sea.', '깊고 어두운 바다에서 느리게 뛴다'), ('A great heart does not need to be loud.', '큰마음은 시끄럽지 않다')],
    coda_style=dict(dim=0.6, blur=10, tint=(0.80, 0.84, 0.82), ink=INK, hi=RED),
    sources=['NOAA Fisheries, “Big-Hearted Blue Whale”: largest animals ever; heart ~400 lb (≈180 kg), heartbeat heard 2 miles (≈3 km) away; ~60 gallons (≈227 L) per beat vs 2.4 oz (≈70 mL) for a human.'],
    yt=dict(title_en='A Blue Whale’s Heart Weighs as Much as a Piano #Shorts', title_ko='흰긴수염고래의 심장은 피아노 한 대 무게')))

if __name__ == '__main__': main(EP)
