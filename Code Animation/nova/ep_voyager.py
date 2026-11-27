"""〈보이저 1호, 빛으로 하루 거리〉 — 골든 레코드 표지 같은 금선 도면(검은 바탕, 가는 금선, 점과 눈금), 소리는 전파 잡음·신호음·낮은 사인 패드.
사실(NASA, 2026-11-18): 1977년 9월 5일 발사, 49년 넘게 날아 2026년 11월 18일 지구에서 1광일(약 259억 km, 173 AU)에 도달.
신호가 가는 데 24시간, 왕복 48시간. 1990년 약 60억 km(37억 마일)에서 '창백한 푸른 점' 사진.
"""
import math, numpy as np, cv2, cairo
from base import *
import sfx as S

GOLD = (0.95, 0.76, 0.36); GOLD2 = (0.70, 0.52, 0.22); BLUEDOT = (0.55, 0.75, 1.0)
T_MAP = 4.0; T_SIG = 9.2; T_DOT = 14.2; T_CODA = 19.4
_r = np.random.default_rng(14)
STARS = np.c_[_r.uniform(0, DW, 260), _r.uniform(0, DH, 260), _r.uniform(0.4, 1.6, 260)]

def probe(cr, x, y, s, a, rot=0.0):
    if a <= 0: return
    cr.save(); cr.translate(x, y); cr.rotate(rot); cr.scale(s, s); cr.set_source_rgba(*GOLD, a); cr.set_line_width(2.2 / s)
    cr.save(); cr.scale(1, 0.38); cr.arc(0, 0, 60, 0, 6.283); cr.restore(); cr.stroke()           # 접시 안테나
    for k in (20, 40): cr.save(); cr.scale(1, 0.38); cr.arc(0, 0, k, 0, 6.283); cr.restore(); cr.stroke()
    cr.move_to(0, 0); cr.line_to(0, -40); cr.stroke(); cr.rectangle(-22, 8, 44, 26); cr.stroke()  # 몸체
    cr.move_to(22, 20); cr.line_to(150, 30); cr.stroke(); cr.move_to(-22, 22); cr.line_to(-110, 60); cr.stroke()  # 막대 두 개
    for k in range(3): cr.rectangle(-122 + k * 4, 54 + k * 8, 18, 10); cr.stroke()                   # 전원 장치
    cr.arc(150, 30, 6, 0, 6.283); cr.stroke()
    cr.arc(0, 44, 13, 0, 6.283); cr.stroke(); cr.arc(0, 44, 4, 0, 6.283); cr.fill()                 # 골든 레코드
    cr.restore()

def draw(t):
    s, cr = surf(); cr.set_source_rgb(0.02, 0.02, 0.03); cr.paint()
    for x, y, r in STARS:
        cr.set_source_rgba(1, 0.95, 0.85, 0.25 + 0.2 * r); cr.arc(x, y, r, 0, 6.283); cr.fill()
    a1 = ramp(t, 0.2, 0.9) * (1 - ramp(t, T_MAP - 0.4, T_MAP))
    probe(cr, 540, 1040, 2.2, a1, 0.15 * math.sin(t * 0.5))
    if a1 > 0:
        txt(cr, 'VOYAGER 1 · 1977', 540, 1400, 44, GOLD, a1, fam=SERIF); txt(cr, '1977년 9월 5일 발사', 540, 1460, 36, GOLD2, a1, fam=BOLD)
    # 지도: 해·행성 궤도·보이저 길(로그 축)
    am = ramp(t, T_MAP - 0.3, T_MAP + 0.3) * (1 - ramp(t, T_SIG - 0.3, T_SIG)) if t < T_DOT else 0
    if t >= T_MAP and t < T_DOT:
        am = ramp(t, T_MAP - 0.3, T_MAP + 0.3)
        sx, sy = 160, 1500; ex, ey = 960, 640
        def pos(au):                                        # 해에서 AU → 화면(로그)
            u = math.log10(1 + au) / math.log10(1 + 173.1); return lerp(sx, ex, u), lerp(sy, ey, u)
        cr.set_source_rgba(*GOLD, am); cr.arc(sx, sy, 14, 0, 6.283); cr.fill()
        for name, au in (('Earth 1 AU', 1), ('Jupiter', 5.2), ('Saturn', 9.5), ('Neptune', 30.1)):
            x, y = pos(au); r = math.hypot(x - sx, y - sy)
            cr.set_line_width(1.4); cr.set_source_rgba(*GOLD2, 0.7 * am); cr.arc(sx, sy, r, -1.6, 0.4); cr.stroke()
            cr.set_source_rgba(*GOLD, am); cr.arc(x, y, 5, 0, 6.283); cr.fill(); txt(cr, name, x + 14, y + 32, 30, GOLD2, am, fam=SERIF, anchor='l')
        prog = smooth(ramp(t, T_MAP + 0.4, T_MAP + 3.6)); au_now = 173.1 * prog ** 1.6
        vx, vy = pos(au_now)
        cr.set_line_width(2.5); cr.set_dash([10, 8]); cr.set_source_rgba(*GOLD, am); cr.move_to(sx, sy); cr.line_to(vx, vy); cr.stroke(); cr.set_dash([])
        probe(cr, vx, vy, 0.35, am, 0.6)
        if t < T_SIG:
            hrs = au_now * 499.0 / 3600
            txt(cr, f'{hrs:4.1f} light-hours', 540, 1700, 64, GOLD, am, fam=SERIF)
            txt(cr, f'빛으로 {hrs:4.1f}시간 거리', 540, 1770, 44, GOLD2, am, fam=BOLD)
            if prog > 0.99:
                fa = ramp(t, T_MAP + 3.7, T_MAP + 4.1)
                txt(cr, 'Nov 18, 2026 · 25.9 billion km', 540, 1840, 34, GOLD, fa, fam=SERIF)
        else:                                               # 신호: 24시간 가고 24시간 돌아온다
            u = (t - T_SIG - 0.4) / 4.2
            if u > 0:
                k = min(u, 1.0) * 2; fwd = k <= 1; f = k if fwd else 2 - k
                ex0, ey0 = pos(1)
                for j in range(6):
                    ff = f - j * 0.025
                    if 0 <= ff <= 1:
                        px, py = lerp(ex0, vx, ff), lerp(ey0, vy, ff)
                        cr.set_source_rgba(*(BLUEDOT if fwd else GOLD), 1 - j / 6); cr.arc(px, py, 9 - j, 0, 6.283); cr.fill()
                h = min(48, 48 * min(u, 1.0))
                txt(cr, f'{h:4.1f} h', 540, 1700, 90, BLUEDOT if fwd else GOLD, am, fam=SERIF)
                txt(cr, 'one way 24 h · round trip 48 h', 540, 1790, 36, GOLD, am, fam=SERIF)
                txt(cr, '가는 데 24시간, 답이 오기까지 48시간', 540, 1845, 34, GOLD2, am, fam=BOLD)
    # 창백한 푸른 점
    ad = ramp(t, T_DOT - 0.2, T_DOT + 0.6)
    if ad > 0:
        g = cairo.LinearGradient(300, 0, 780, 0)
        for st, aa in ((0, 0), (0.35, 0.18), (0.5, 0.28), (0.65, 0.18), (1, 0)): g.add_color_stop_rgba(st, *GOLD, aa * ad)
        cr.save(); cr.translate(540, 1000); cr.rotate(0.18); cr.translate(-540, -1000); cr.set_source(g); cr.rectangle(300, -200, 480, 2400); cr.fill(); cr.restore()
        pulse = 0.7 + 0.3 * math.sin(t * 2.2)
        cr.set_source_rgba(*BLUEDOT, ad * pulse); cr.arc(560, 1060, 4.5, 0, 6.283); cr.fill()
        la = ramp(t, T_DOT + 1.4, T_DOT + 2.0)
        cr.set_line_width(1.5); cr.set_source_rgba(*GOLD, la); cr.arc(560, 1060, 40, 0, 6.283); cr.stroke(); cr.move_to(590, 1090); cr.line_to(700, 1260); cr.stroke()
        txt(cr, 'Earth, 1990', 700, 1300, 40, GOLD, la, fam=SERIF); txt(cr, '60억 km 밖에서 본 지구', 700, 1350, 34, GOLD2, la, fam=BOLD)
        txt(cr, 'everyone you know is in that dot', 540, 1700, 40, GOLD, ramp(t, T_DOT + 2.6, T_DOT + 3.2), fam=SERIF)
        txt(cr, '우리가 아는 모든 사람이 저 점 안에', 540, 1760, 38, GOLD2, ramp(t, T_DOT + 2.6, T_DOT + 3.2), fam=BOLD)
    img = arr(s)[..., :3]
    return img + cv2.GaussianBlur(img, (0, 0), 6 * SC) * 0.35

def sound(path):
    m = S.Mix(EP['DUR'], 131); tc = EP['t_coda']
    m.put('amb', 0, S.static(EP['t_end'] + 1, 0.12))
    m.put('amb', 0, S.drone([55.0, 82.4, 110.0], EP['t_end'] + 1, 0.2, 'sine'))
    pat = '.-.. .. --. .... - / -.. .- -.--'                  # LIGHT DAY (모스)
    t = 0.6
    for ch in pat:
        if t > T_MAP - 0.2: break
        if ch == '.': m.put('fx', t, S.beep(1200, 0.08, 0.3)); t += 0.16
        elif ch == '-': m.put('fx', t, S.beep(1200, 0.24, 0.3)); t += 0.32
        else: t += 0.25
    for k in range(9): m.put('mus', T_MAP + 0.4 + k * 0.4, S.ping(523.3 * 2 ** (k / 12 * 2), 0.18, 1.8))
    m.put('fx', T_SIG + 0.4, S.beep(1600, 0.4, 0.4)); m.put('fx', T_SIG + 2.5, S.beep(900, 0.4, 0.4)); m.put('fx', T_SIG + 4.6, S.beep(1600, 0.25, 0.35))
    m.put('mus', T_DOT, S.drone([110.0, 164.8, 220.0, 277.2], T_CODA - T_DOT, 0.22, 'sine'))
    m.put('amb', tc, S.drone([82.4, 123.5, 164.8], EP['t_end'] - tc, 0.18, 'sine'))
    for i in range(3): m.put('mus', tc + 0.8 + i * STEP, S.bell([659.3, 554.4, 493.9][i], 3.5, 0.28))
    m.write(path, rev_mus=3.5, wet_mus=0.45)

EP = finalize(dict(t_coda=T_CODA, draw=draw, sound=sound, end_icon='star', grain=0.004,
    title_en_card='ONE LIGHT-DAY AWAY', title_ko_card='보이저 1호, 빛으로 하루 거리',
    pal=dict(hi=GOLD2, endbg=(0.96, 0.93, 0.85)),
    card_style=dict(box=None, ink=(0.98, 0.95, 0.88), hi=GOLD, y=150, fe=SERIF, fk=BLK),
    cards=[(0.3, 3.8, ['Launched in *1977*.', 'Still flying.'], ['*1977년*에 떠나', '아직도 날고 있다']),
           (4.0, 9.0, ['On Nov 18, 2026, Voyager 1 became', 'the first object *one light-day* away.'], ['2026년 11월 18일,', '처음으로 *빛으로 하루* 거리에 닿았다']),
           (9.2, 14.0, ['A message takes *a full day* to arrive,', 'and two days to get a reply.'], ['말 한마디가 닿는 데 *하루*,', '대답을 듣는 데 이틀']),
           (14.2, 19.2, ['In 1990 it looked back', 'and saw us as *a pale blue dot*.'], ['1990년 뒤돌아본 지구는', '*창백한 푸른 점* 하나였다'])],
    coda=[('After forty-nine years of flight,', '49년을 날아가도'), ('it has gone just one day of light.', '빛으로는 겨우 하루 거리'), ('Every far journey is made of small days.', '모든 먼 길은 작은 하루가 쌓인 것이다')],
    coda_style=dict(dim=0.5, blur=8, tint=(0.02, 0.02, 0.03), ink=(0.98, 0.95, 0.88), hi=GOLD),
    sources=['NASA: Voyager 1 reached one light-day from Earth on Nov. 18, 2026, after more than 49 years. One light-day ≈ 25.9 billion km (173 AU).', 'Pale Blue Dot photo, 1990, from about 6 billion km (3.7 billion miles).'],
    yt=dict(title_en='Voyager 1 Is Now One Light-Day From Earth #Shorts', title_ko='보이저 1호, 빛으로 하루 거리에 닿다')))

if __name__ == '__main__': main(EP)
