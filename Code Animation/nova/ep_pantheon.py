"""〈1,900년 된 콘크리트 지붕〉 — 로마 모자이크(네모난 돌 조각, 줄눈, 조각마다 다른 색과 기울기, 제한된 돌 색), 소리는 해머 덜시머와 낮은 드론.
사실: 판테온은 하드리아누스 때 완공·봉헌(서기 125~126년경). 지름 43.3 m 콘크리트 돔은 지금도 세계에서 가장 큰 무근(철근 없는) 콘크리트 돔.
돔 꼭대기까지 높이와 내부 지름이 같아 지름 43 m 공이 꼭 맞게 들어간다. 꼭대기에 하늘로 열린 구멍(오쿨루스), 우물 반자(격자 홈)가 무게를 줄인다.
"""
import math, numpy as np, cv2, cairo
from base import *
import sfx as S

TS = 16                                                     # 조각 크기(설계 px)
PAL = np.array([(0.93, 0.89, 0.80), (0.82, 0.74, 0.60), (0.62, 0.52, 0.40), (0.42, 0.34, 0.27), (0.20, 0.17, 0.15), (0.70, 0.32, 0.22),
                (0.52, 0.20, 0.15), (0.25, 0.38, 0.55), (0.45, 0.60, 0.75), (0.80, 0.62, 0.25), (0.35, 0.45, 0.30), (0.98, 0.95, 0.88)], np.float32)
CREAM, SAND, OCHRE, BROWN, DARK, TERRA, WINE, BLUE, SKYB, GOLD, OLIVE, WHITE = [tuple(c) for c in PAL]
T_DOME = 3.8; T_BALL = 8.8; T_COFF = 13.6; T_CODA = 18.8
GW, GH = DW // TS, DH // TS
_r = np.random.default_rng(37)

def _geom():
    c = TS * SC; yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    ti = np.clip((xx // c).astype(int), 0, GW - 1); tj = np.clip((yy // c).astype(int), 0, GH - 1)
    jx = _r.uniform(-1.6, 1.6, (GH, GW)) * SC; jy = _r.uniform(-1.6, 1.6, (GH, GW)) * SC; sh = _r.uniform(1.6, 3.2, (GH, GW)) * SC
    lx = xx - ti * c - jx[tj, ti]; ly = yy - tj * c - jy[tj, ti]; g = sh[tj, ti]
    d = np.minimum(np.minimum(lx - g / 2, c - g / 2 - lx), np.minimum(ly - g / 2, c - g / 2 - ly))
    inside = np.clip(d / (0.8 * SC) + 0.5, 0, 1)
    bevel = 1 - 0.18 * np.exp(-np.clip(d, 0, None) / (1.5 * SC))
    return ti, tj, inside.astype(np.float32), bevel.astype(np.float32)
TI, TJ, INSIDE, BEVEL = _geom()
TSHADE = _r.uniform(0.88, 1.08, (GH, GW)).astype(np.float32)
GROUT = np.array((0.55, 0.58, 0.60), np.float32)            # BGR 회색 줄눈

def facade(cr, a):
    cr.set_source_rgba(*SAND, a); cr.rectangle(160, 1060, 760, 420); cr.fill()                          # 원통 몸
    cr.set_source_rgba(*OCHRE, a); cr.arc(540, 1060, 380, math.pi, 2 * math.pi); cr.fill()             # 돔
    cr.set_source_rgba(*CREAM, a); cr.move_to(240, 1150); cr.line_to(540, 960); cr.line_to(840, 1150); cr.close_path(); cr.fill()   # 박공
    for k in range(8): cr.set_source_rgba(*WHITE, a); cr.rectangle(255 + k * 80, 1150, 34, 330); cr.fill()                        # 기둥
    cr.set_source_rgba(*DARK, a); cr.rectangle(510, 1300, 60, 180); cr.fill()

def section(cr, a, coffers=0.0, ball=0.0, beam=0.0):
    cx, base, R = 540, 1300, 340
    cr.set_source_rgba(*SAND, a); cr.rectangle(cx - R - 40, base, 2 * R + 80, 350); cr.fill()
    cr.set_source_rgba(*OCHRE, a); cr.arc(cx, base, R + 40, math.pi, 2 * math.pi); cr.fill()
    cr.set_source_rgba(*DARK, a); cr.arc(cx, base, R, math.pi, 2 * math.pi); cr.fill(); cr.rectangle(cx - R, base, 2 * R, 340); cr.fill()
    cr.set_source_rgba(*SKYB, a); cr.rectangle(cx - 30, base - R - 50, 60, 60); cr.fill()               # 오쿨루스
    if coffers > 0:
        for ring in range(5):
            for k in range(9):
                ang = math.pi + (k + 0.5) * math.pi / 9; rr = R * (0.9 - ring * 0.14)
                if rr < 80: continue
                q = 34 - ring * 5; cr.set_source_rgba(*SAND, a * coffers); cr.rectangle(cx + rr * math.cos(ang) - q / 2, base + rr * math.sin(ang) - q / 2, q, q); cr.fill()
    if ball > 0:
        cr.set_source_rgba(*GOLD, a * ball); cr.set_line_width(16); cr.arc(cx, base, R * 0.999, 0, 6.283 * smooth(ball)); cr.stroke()
    if beam > 0:
        cr.set_source_rgba(*WHITE, 0.85 * a * beam); cr.move_to(cx - 30, base - R); cr.line_to(cx + 30, base - R); cr.line_to(cx + 190, base + 200); cr.line_to(cx + 90, base + 200); cr.close_path(); cr.fill()

def draw(t):
    s, cr = surf(); cr.set_source_rgb(*SKYB if t < T_DOME else BLUE); cr.paint()
    cr.set_source_rgb(*TERRA); cr.rectangle(0, 1650, DW, 300); cr.fill()
    for k in range(DW // 64 + 1): cr.set_source_rgb(*CREAM); cr.rectangle(k * 64, 1690, 32, 32); cr.fill()      # 테두리 무늬
    if t < T_DOME: facade(cr, 1)
    else:
        section(cr, 1, coffers=ramp(t, T_COFF + 0.3, T_COFF + 1.5), ball=ramp(t, T_BALL + 0.4, T_BALL + 2.4) * (1 - ramp(t, T_COFF, T_COFF + 0.5)), beam=ramp(t, T_BALL + 2.6, T_BALL + 3.2))
    a = arr(s)
    small = cv2.resize(a, (GW, GH), interpolation=cv2.INTER_AREA)[..., :3][..., ::-1]
    d = ((small[:, :, None, :] - PAL[None, None]) ** 2).sum(-1); q = PAL[d.argmin(-1)] * TSHADE[..., None]
    col = q[TJ, TI][..., ::-1] * BEVEL[..., None]
    img = col * INSIDE[..., None] + GROUT * (1 - INSIDE[..., None])
    s2, c2 = surf(); ink = (0.98, 0.95, 0.88)
    def lab(text, y, size, a, colr=ink):
        c2.set_source_rgba(0.15, 0.10, 0.08, 0.75 * a); c2.rectangle(90, y - size * 0.95, 900, size * 1.35); c2.fill()
        txt(c2, text, 540, y, size, colr, a, fam=SERIF)
    if t < T_DOME: lab('PANTHEON · ROMA · c. AD 126', 1590, 44, ramp(t, 0.6, 1.1))
    elif t < T_BALL: lab('43.3 m across · 지름 43.3m', 1590, 44, ramp(t, T_DOME + 0.6, T_DOME + 1.0))
    elif t < T_COFF:
        lab('a 43 m sphere fits inside · 43m 공', 1520, 40, ramp(t, T_BALL + 1.6, T_BALL + 2.0))
        lab('open to the sky · 하늘로 열린 구멍', 1600, 40, ramp(t, T_BALL + 2.8, T_BALL + 3.2))
    else: lab('coffers · 무게를 줄이는 홈', 1590, 44, ramp(t, T_COFF + 0.8, T_COFF + 1.2))
    return over(img, s2)

def sound(path):
    m = S.Mix(EP['DUR'], 241); tc = EP['t_coda']; b = 60 / 84
    modes = [293.7, 329.6, 349.2, 392.0, 440.0, 466.2, 523.3, 587.3]      # 도리안 느낌
    pat = [0, 2, 4, 2, 5, 4, 2, 1, 0, 4, 7, 6, 4, 3, 2, 1]
    t = 0.3; k = 0
    while t < tc - 0.3:
        m.put('mus', t, S.dulcimer(modes[pat[k % 16]], 1.6, 0.3))
        if k % 4 == 0: m.put('mus', t, S.dulcimer(modes[0] / 2, 2.2, 0.25))
        t += b / 2; k += 1
    m.put('amb', 0, S.drone([73.4, 110.0, 146.8], EP['t_end'] + 1, 0.16, 'saw'))
    m.put('fx', T_BALL + 0.4, S.swoosh(2.0, 0.25, 200, 2000)); m.put('fx', T_BALL + 2.6, S.bell(1174.7, 3.0, 0.3))
    for k in range(9): m.put('fx', T_COFF + 0.3 + k * 0.13, S.tok(600 + 30 * k, 0.15))
    m.put('amb', tc, S.drone([73.4, 110.0, 146.8], EP['t_end'] - tc, 0.16, 'sine'))
    for i, f in enumerate([587.3, 440.0, 293.7]): m.put('mus', tc + 0.8 + i * STEP, S.dulcimer(f, 3.0, 0.35))
    m.write(path, rev_mus=3.0, wet_mus=0.42)

EP = finalize(dict(t_coda=T_CODA, draw=draw, sound=sound, end_icon='star', grain=0.0,
    title_en_card='A 1,900-YEAR-OLD ROOF', title_ko_card='1,900년 된 콘크리트 지붕',
    pal=dict(hi=TERRA, endbg=CREAM),
    card_style=dict(box='paper', bg=(0.95, 0.91, 0.82), ink=(0.20, 0.12, 0.08), hi=(0.62, 0.20, 0.12), y=150, fe=SERIF, fk=BLK),
    cards=[(0.3, 3.6, ['The Pantheon in Rome,', 'finished about *1,900 years* ago.'], ['로마 판테온,', '약 *1,900년* 전에 완공']),
           (3.8, 8.6, ['Its dome is still the *largest*', 'unreinforced concrete dome on Earth.'], ['그 돔은 지금도', '철근 없는 콘크리트 돔 중 *가장 크다*']),
           (8.8, 13.4, ['Height and width are both *43 m*:', 'a giant ball would fit perfectly.'], ['높이도 폭도 *43m*,', '거대한 공이 꼭 들어맞는다']),
           (13.6, 18.6, ['Sunken panels', 'make it *lighter*.'], ['우물 같은 홈이', '무게를 *덜어 준다*'])],
    coda=[('Built with patience,', '참을성 있게 지은 것은'), ('it has stood for nineteen centuries.', '1,900년을 버텼다'), ('What we build with care outlasts us.', '정성껏 지은 것은 우리보다 오래 남는다')],
    coda_style=dict(dim=0.6, blur=8, tint=(0.80, 0.74, 0.60), ink=(0.20, 0.12, 0.08), hi=(0.62, 0.20, 0.12), fe=SERIF),
    sources=['Pantheon completed and dedicated c. AD 125–126 under Hadrian; 43.3 m dome, still the world’s largest unreinforced concrete dome; height to the oculus equals the interior diameter (ENR; World History Encyclopedia).', 'Coffered panels lighten the dome’s weight (ENR).'],
    yt=dict(title_en='This 1,900-Year-Old Concrete Dome Is Still the Largest #Shorts', title_ko='1,900년 된 판테온 돔, 아직도 세계 최대')))

if __name__ == '__main__': main(EP)
