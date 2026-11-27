"""〈물에 뜨는 행성〉 — 1960년대 사이키델릭 포스터(물결치는 동심 띠, 주황·자홍·청록·노랑 고채도, 둥글게 부푼 글자 느낌, 천천히 흐르는 줄무늬), 소리는 퍼지한 오르간 코드와 느긋한 그루브.
사실: 토성 평균 밀도 0.687 g/cm³, 물(약 1 g/cm³)보다 낮다. 질량은 지구의 약 95배지만 부피는 750배 이상(Sky at Night; Universe Today; NASA).
지구 밀도 5.51 g/cm³(Universe Today). 실제로 담글 물은 있을 수 없는 사고 실험이다(IFLScience).
"""
import math, numpy as np, cv2, cairo
from base import *
import sfx as S

ORG = (0.98, 0.45, 0.10); MAG = (0.88, 0.12, 0.52); TEALP = (0.05, 0.62, 0.62); YELP = (1.0, 0.86, 0.12); PURP = (0.30, 0.10, 0.42); CRMP = (1.0, 0.96, 0.86)
T_MASS = 4.2; T_DENS = 9.8; T_TUB = 15.2; T_CODA = 20.6
yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
RAD = np.hypot(xx - W / 2, yy - H * 0.55) / SC
ANG = np.arctan2(yy - H * 0.55, xx - W / 2)
PAL = np.array([ORG, MAG, YELP, TEALP, PURP], np.float32)[:, ::-1]

def bands(t):
    """흐르는 동심 물결 띠(바탕)."""
    r = RAD + 18 * np.sin(ANG * 5 + t * 0.6) + 10 * np.sin(RAD / 60 - t * 0.8)
    k = ((r - t * 30) / 70).astype(np.int32) % 5
    img = PAL[k]
    return img * 0.85 + 0.15

def saturn(cr, x, y, R, a=1.0):
    cr.save(); cr.translate(x, y)
    cr.set_source_rgba(*PURP, a); cr.set_line_width(R * 0.13); cr.save(); cr.scale(1, 0.28); cr.arc(0, 0, R * 1.85, math.pi, 2 * math.pi); cr.restore(); cr.stroke()
    for k, c in enumerate([YELP, ORG, YELP, MAG, YELP]):
        cr.save(); cr.arc(0, 0, R, 0, 6.283); cr.clip()
        cr.set_source_rgba(*c, a); cr.rectangle(-R, -R + k * 2 * R / 5, 2 * R, 2 * R / 5 + 1); cr.fill(); cr.restore()
    cr.set_source_rgba(*PURP, a); cr.set_line_width(8); cr.arc(0, 0, R, 0, 6.283); cr.stroke()
    cr.set_source_rgba(*CRMP, a); cr.set_line_width(R * 0.09); cr.save(); cr.scale(1, 0.28); cr.arc(0, 0, R * 1.85, 0, math.pi); cr.restore(); cr.stroke()
    cr.set_source_rgba(*PURP, a); cr.set_line_width(R * 0.04); cr.save(); cr.scale(1, 0.28); cr.arc(0, 0, R * 1.62, 0, math.pi); cr.restore(); cr.stroke()
    cr.restore()

def bubble(cr, text, y, size, col, a):
    txt(cr, text, 540 + 4, y + 5, size, PURP, a, fam=BLK); txt(cr, text, 540, y, size, col, a, fam=BLK)

def draw(t):
    bg = bands(t).astype(np.float32)
    s, cr = surf()
    cr.set_source_rgba(*CRMP, 0.92); cr.rectangle(70, 560, 940, 1220); cr.fill()      # 포스터 창
    cr.set_source_rgba(*PURP, 1); cr.set_line_width(10); cr.rectangle(70, 560, 940, 1220); cr.stroke()
    if t < T_MASS:
        a = 1 - ramp(t, T_MASS - 0.3, T_MASS)
        saturn(cr, 540, 1150 + 14 * math.sin(t * 2), 230, a)
    elif t < T_DENS:                                                   # 질량 95배, 부피 750배
        a = ramp(t, T_MASS, T_MASS + 0.3) * (1 - ramp(t, T_DENS - 0.3, T_DENS))
        g = smooth(ramp(t, T_MASS + 0.4, T_MASS + 2.4))
        cr.set_source_rgba(*TEALP, a); cr.arc(240, 960, 26, 0, 6.283); cr.fill()
        bubble(cr, '×95 mass', 790, 64, MAG, a);
        txt(cr, 'Earth', 240, 1020, 32, PURP, a, fam=BOLD)
        for k in range(int(95 * g)):
            cr.set_source_rgba(*MAG, a); cr.arc(330 + (k % 19) * 32, 900 + (k // 19) * 32, 12, 0, 6.283); cr.fill()
        g2 = smooth(ramp(t, T_MASS + 2.4, T_MASS + 4.4))
        saturn(cr, 540, 1440, 150 * (0.2 + 0.8 * g2), a * ramp(t, T_MASS + 2.4, T_MASS + 2.6))
        bubble(cr, '×750+ volume', 1720, 56, ORG, a * ramp(t, T_MASS + 3.0, T_MASS + 3.4))
    elif t < T_TUB:                                                    # 밀도 막대
        a = ramp(t, T_DENS, T_DENS + 0.3) * (1 - ramp(t, T_TUB - 0.3, T_TUB))
        g = smooth(ramp(t, T_DENS + 0.4, T_DENS + 2.4)); base = 1650; sc = 160
        for i, (lab, v, c) in enumerate([('Earth', 5.51, TEALP), ('water', 1.0, (0.20, 0.45, 0.85)), ('Saturn', 0.687, ORG)]):
            x = 180 + i * 260; h = min(v * sc, 900) * g
            cr.set_source_rgba(*c, a); cr.rectangle(x, base - h, 200, h); cr.fill()
            cr.set_source_rgba(*PURP, a); cr.set_line_width(6); cr.rectangle(x, base - h, 200, h); cr.stroke()
            txt(cr, lab, x + 100, base + 60, 40, PURP, a, fam=BLK); txt(cr, f'{v}', x + 100, base - h - 24, 48, PURP, a * g, fam=BLK)
        cr.set_source_rgba(*MAG, a); cr.set_line_width(4); cr.set_dash([16, 10]); cr.move_to(140, base - sc); cr.line_to(960, base - sc); cr.stroke(); cr.set_dash([])
        txt(cr, 'g/cm³', 540, 690, 40, PURP, a, fam=BOLD)
    else:                                                              # 거대한 욕조
        a = ramp(t, T_TUB, T_TUB + 0.3) * (1 - ramp(t, T_CODA - 0.3, T_CODA))
        wl = 1300
        cr.set_source_rgba(0.25, 0.55, 0.90, a); cr.rectangle(110, wl, 860, 380); cr.fill()
        bob = 18 * math.sin((t - T_TUB) * 2.2) * math.exp(-(t - T_TUB) * 0.3)
        drop = smooth(ramp(t, T_TUB + 0.2, T_TUB + 1.4))
        sy = 760 + (wl + 58 - 760) * drop + bob    # 약 69% 잠김(밀도 0.687): 물 높이가 중심보다 약 0.29R 위
        saturn(cr, 540, sy, 200, a)
        cr.set_source_rgba(0.25, 0.55, 0.90, 0.55 * a); cr.rectangle(110, wl, 860, 380); cr.fill()
        cr.set_source_rgba(*PURP, a); cr.set_line_width(12); cr.move_to(100, 1180); cr.line_to(130, 1690); cr.line_to(950, 1690); cr.line_to(980, 1180); cr.stroke()
        for k in range(4): cr.arc(200 + k * 230, 1720, 26, 0, 6.283)
        cr.fill()
        txt(cr, 'only in theory · 이론상으로만', 540, 680, 38, PURP, a * ramp(t, T_TUB + 2.0, T_TUB + 2.4), fam=BOLD)
    out = over(bg, s)
    return out

def sound(path):
    m = S.Mix(EP['DUR'], 687); tc = EP['t_coda']; b = 60 / 92
    prog = [[146.8, 220.0, 261.6, 329.6], [130.8, 196.0, 246.9, 329.6], [116.5, 174.6, 233.1, 293.7], [110.0, 164.8, 220.0, 277.2]]
    t = 0.3; k = 0
    while t < tc - 0.6:
        m.put('mus', t, S.organ(prog[k % 4], b * 4 * 0.98, 0.18)); t += b * 4; k += 1
    n = int((tc - 0.3) / (b / 2))
    for j in range(n):
        tt = 0.3 + j * b / 2; pos = j % 8
        if pos in (0, 5): m.put('mus', tt, S.kick(52, 0.45))
        if pos in (2, 6): m.put('mus', tt, S.brush(0.2, 0.3, seed=j))
        if pos % 2 == 1: m.put('mus', tt, S.hihat(0.07, seed=j))
        if pos in (0, 3, 6): m.put('mus', tt, S.upright(prog[(j // 8) % 4][0] / 2, 0.45, 0.26))
    m.put('fx', T_TUB + 0.9, S.swoosh(1.2, 0.25, 200, 1200)); m.put('fx', T_TUB + 1.3, S.stream(2.5, 0.2) if hasattr(S, 'stream') else S.swoosh(1.0, 0.1))
    m.put('mus', tc + 0.8, S.organ([146.8, 220.0, 293.7], 5.5, 0.2))
    m.write(path, rev_mus=2.0, wet_mus=0.3)

EP = finalize(dict(t_coda=T_CODA, draw=draw, sound=sound, end_icon='star', grain=0.0,
    title_en_card='THE PLANET THAT FLOATS', title_ko_card='물에 뜨는 행성',
    pal=dict(hi=MAG, endbg=CRMP),
    card_style=dict(box='paper', bg=(1.0, 0.97, 0.88), ink=PURP, hi=MAG, y=180, fe=BLK, fk=BLK),
    cards=[(0.3, 4.0, ['Saturn is the second-largest', 'planet in the Solar System.'], ['토성은 태양계에서', '두 번째로 큰 행성']),
           (4.2, 9.6, ['It has *95 times* Earth’s mass,', 'spread over *750+ times* the volume.'], ['질량은 지구의 *95배*,', '부피는 *750배* 이상']),
           (9.8, 15.0, ['So its density is just *0.687*:', 'lower than water.'], ['그래서 밀도는 *0.687*,', '물보다 낮다']),
           (15.2, 20.4, ['In a big enough bathtub', 'it would *float* (in theory).'], ['아주 큰 욕조가 있다면', '*둥둥 뜬다* (이론상)'])],
    coda=[('Even a giant can float', '거인도 물에 뜰 수 있다'), ('when it is not too full of itself.', '스스로를 꽉 채우지 않는다면'), ('Leave a little room inside.', '마음속에 조금의 빈자리를 두자')],
    coda_style=dict(dim=0.55, blur=8, tint=(0.95, 0.70, 0.40), ink=PURP, hi=MAG, fe=BLK),
    sources=['Saturn mean density 0.687 g/cm³, less than water; ~95 Earth masses over >750 times Earth’s volume (BBC Sky at Night; Universe Today; NASA).', 'Earth 5.51 g/cm³ (Universe Today). The bathtub is a thought experiment; such water could not exist as a still pool (IFLScience).'],
    yt=dict(title_en='Saturn Would Float in a Giant Bathtub #Shorts', title_ko='물에 뜨는 행성, 토성')))

if __name__ == '__main__': main(EP)
