"""〈햇빛은 8분 20초 전의 빛〉 — 아르데코 포스터(검정·금·크림, 계단형 햇살, 가는 금선 장식, 세리프 글씨), 소리는 업라이트 베이스 워킹과 브러시 스네어.
사실(Smithsonian 'How Things Fly'; UCAR): 해와 지구 사이 평균 1억 5천만 km, 빛으로 약 8분 20초. 해가 사라져도 8분 남짓은 모른다.
달빛은 약 1.3초 전(계산: 384,400 km ÷ 299,792 km/s). 가장 가까운 별(알파 센타우리)은 4년 넘게 전의 빛.
"""
import math, numpy as np, cv2, cairo
from base import *
import sfx as S

BLACK = (0.04, 0.04, 0.05); GOLD = (0.86, 0.68, 0.33); GOLD2 = (0.62, 0.47, 0.20); CREAM = (0.95, 0.90, 0.78); TEAL = (0.20, 0.48, 0.50)
T_TRIP = 3.8; T_MOON = 8.8; T_GONE = 13.6; T_CODA = 18.8
SUN = (540, 760); EARTH = (540, 1520)

def sunburst(cr, x, y, r, a, rays=24, rot=0.0):
    for k in range(rays):
        a0 = rot + k * 6.283 / rays
        L = r * (2.6 if k % 2 == 0 else 1.9)
        cr.set_source_rgba(*(GOLD if k % 2 == 0 else GOLD2), a * 0.85)
        cr.move_to(x + r * 1.08 * math.cos(a0 - 0.05), y + r * 1.08 * math.sin(a0 - 0.05)); cr.line_to(x + L * math.cos(a0), y + L * math.sin(a0))
        cr.line_to(x + r * 1.08 * math.cos(a0 + 0.05), y + r * 1.08 * math.sin(a0 + 0.05)); cr.close_path(); cr.fill()
    for k, rr in enumerate((r, r * 0.8, r * 0.6)):
        cr.set_source_rgba(*(GOLD if k % 2 == 0 else CREAM), a); cr.arc(x, y, rr, 0, 6.283); cr.fill()
    cr.set_source_rgba(*BLACK, a); cr.set_line_width(3)
    for k in range(1, 4): cr.arc(x, y, r * (1 - k * 0.2) + 1, 0, 6.283); cr.stroke()

def frame(cr, a):
    cr.set_source_rgba(*GOLD, a); cr.set_line_width(3); cr.rectangle(40, 40, DW - 80, DH - 80); cr.stroke(); cr.set_line_width(1.5); cr.rectangle(58, 58, DW - 116, DH - 116); cr.stroke()
    for (x, y, sx, sy) in ((58, 58, 1, 1), (DW - 58, 58, -1, 1), (58, DH - 58, 1, -1), (DW - 58, DH - 58, -1, -1)):   # 계단 모서리
        for k in range(4): cr.rectangle(x + sx * k * 14 - (14 if sx < 0 else 0), y + sy * k * 14 - (14 if sy < 0 else 0), 14 * (4 - k), 3) if False else None
        cr.move_to(x, y + sy * 70); cr.line_to(x + sx * 20, y + sy * 70); cr.line_to(x + sx * 20, y + sy * 50); cr.line_to(x + sx * 40, y + sy * 50); cr.line_to(x + sx * 40, y + sy * 30)
        cr.line_to(x + sx * 60, y + sy * 30); cr.line_to(x + sx * 60, y + sy * 10); cr.line_to(x + sx * 70, y + sy * 10); cr.stroke()

def earth(cr, x, y, r, a, lit=1.0):
    cr.set_source_rgba(*TEAL, a); cr.arc(x, y, r, 0, 6.283); cr.fill()
    cr.set_source_rgba(*GOLD, a); cr.set_line_width(3); cr.arc(x, y, r, 0, 6.283); cr.stroke()
    for k in range(-2, 3): cr.set_line_width(1.5); cr.save(); cr.translate(x, y + k * r * 0.35); cr.scale(math.sqrt(max(0.01, 1 - (k * 0.35) ** 2)) * r, r * 0.08); cr.arc(0, 0, 1, 0, math.pi); cr.restore(); cr.stroke()
    if lit > 0:
        cr.save(); cr.arc(x, y, r, 0, 6.283); cr.clip(); g = cairo.LinearGradient(x, y - r, x, y + r)
        g.add_color_stop_rgba(0, *CREAM, 0.55 * lit * a); g.add_color_stop_rgba(0.55, *CREAM, 0); cr.set_source(g); cr.paint(); cr.restore()

def draw(t):
    s, cr = surf(); cr.set_source_rgb(*BLACK); cr.paint(); frame(cr, 1)
    gone = smooth(ramp(t, T_GONE + 0.4, T_GONE + 1.2))
    sa = 1 - gone * 0.9
    sunburst(cr, SUN[0], SUN[1], 105, sa, rot=t * 0.05)
    # 금선 궤도와 빛 알갱이
    cr.set_source_rgba(*GOLD2, 0.8); cr.set_line_width(1.5); cr.set_dash([4, 10]); cr.move_to(SUN[0], SUN[1] + 150); cr.line_to(EARTH[0], EARTH[1] - 110); cr.stroke(); cr.set_dash([])
    if T_TRIP <= t < T_MOON:
        u = smooth(ramp(t, T_TRIP + 0.4, T_TRIP + 3.8)); y = lerp(SUN[1] + 150, EARTH[1] - 110, u)
        for k in range(8):
            yy = y - k * 14
            if yy > SUN[1] + 140: cr.set_source_rgba(*CREAM, 1 - k / 8); cr.arc(540, yy, 10 - k, 0, 6.283); cr.fill()
        secs = 500 * u
        txt(cr, f'{int(secs // 60)}:{int(secs % 60):02d}', 800, 1060, 96, CREAM, ramp(t, T_TRIP + 0.2, T_TRIP + 0.5), fam=SERIF)
        txt(cr, '150 million km · 1억 5천만 km', 540, 1760, 36, GOLD, ramp(t, T_TRIP + 0.2, T_TRIP + 0.5), fam=SERIF)
    earth(cr, EARTH[0], EARTH[1], 100, 1, lit=1.0 if t < T_GONE + 0.4 + 8.33 * 0.6 else 1 - ramp(t, T_GONE + 3.5, T_GONE + 4.5))
    if T_MOON <= t < T_GONE:                                   # 빛의 나이 표
        a = ramp(t, T_MOON, T_MOON + 0.4) * (1 - ramp(t, T_GONE - 0.4, T_GONE))
        rows = [('Moonlight', '달빛', '1.3 s'), ('Sunlight', '햇빛', '8 min 20 s'), ('Nearest star', '가장 가까운 별', '4+ years')]
        for k, (en, ko, v) in enumerate(rows):
            ra = a * ramp(t, T_MOON + 0.3 + k * 0.6, T_MOON + 0.7 + k * 0.6); y = 1000 + k * 140
            cr.set_source_rgba(*BLACK, ra * 0.85); cr.rectangle(150, y - 70, 780, 120); cr.fill()
            cr.set_source_rgba(*GOLD, ra); cr.set_line_width(2); cr.rectangle(150, y - 70, 780, 120); cr.stroke()
            txt(cr, en, 180, y - 12, 40, CREAM, ra, fam=SERIF, anchor='l'); txt(cr, ko, 180, y + 34, 36, GOLD, ra, fam=BOLD, anchor='l')
            txt(cr, v, 900, y + 12, 50, GOLD, ra, fam=SERIF, anchor='r')
    if t >= T_GONE:
        a = ramp(t, T_GONE + 0.2, T_GONE + 0.6) * (1 - ramp(t, T_CODA - 0.4, T_CODA))
        u = ramp(t, T_GONE + 0.4, T_GONE + 0.4 + 4.0); y = lerp(SUN[1] + 150, EARTH[1] - 110, u)
        cr.set_source_rgba(*CREAM, 0.9 * a); cr.rectangle(536, y - 300, 8, 300); cr.fill()                   # 마지막 빛 무리가 아직 오는 중
        txt(cr, 'Earth is still lit…', 540, 1720, 48, CREAM, a, fam=SERIF); txt(cr, '해가 사라져도 지구는 아직 밝다', 540, 1785, 40, GOLD, a, fam=BOLD)
    img = arr(s)[..., :3]
    return img + cv2.GaussianBlur(img, (0, 0), 10 * SC) * 0.25

def sound(path):
    m = S.Mix(EP['DUR'], 171); tc = EP['t_coda']; b = 60 / 108
    walk = [98.0, 110.0, 123.5, 130.8, 146.8, 130.8, 123.5, 110.0, 87.3, 98.0, 110.0, 116.5, 130.8, 116.5, 110.0, 98.0]
    t = 0.3; k = 0
    while t < tc - 0.2:
        if not (T_GONE + 0.5 < t < T_GONE + 3.0): m.put('mus', t, S.upright(walk[k % 16], 0.7, 0.45))
        if k % 2 == 1: m.put('fx', t, S.brush(0.22, 0.25, k))
        m.put('fx', t, S.brush(0.08, 0.08, k + 100))
        if k % 8 == 0: [m.put('mus', t, S.ping(f, 0.14, 1.6)) for f in ((392.0, 493.9, 587.3, 740.0) if (k // 8) % 2 == 0 else (349.2, 440.0, 523.3, 659.3))]
        t += b; k += 1
    for i in range(9): m.put('fx', T_TRIP + 0.4 + i * 0.4, S.tick(0.25, i % 2 == 0))
    m.put('fx', T_GONE + 0.4, S.swoosh(1.0, 0.4, 3000, 200))
    m.put('amb', tc, S.drone([98.0, 146.8, 196.0], EP['t_end'] - tc, 0.15, 'sine'))
    for i in range(3):
        m.put('mus', tc + 0.8 + i * STEP, S.upright([98.0, 87.3, 73.4][i], 1.5, 0.45))
        for f in ([392.0, 493.9, 587.3], [349.2, 440.0, 523.3], [293.7, 370.0, 440.0])[i]: m.put('mus', tc + 0.82 + i * STEP, S.ping(f, 0.13, 2.4))
    m.write(path, rev_mus=1.8, wet_mus=0.25)

EP = finalize(dict(t_coda=T_CODA, draw=draw, sound=sound, end_icon='sun', grain=0.004,
    title_en_card='EIGHT MINUTES OLD', title_ko_card='햇빛은 8분 전의 빛',
    pal=dict(hi=GOLD2, endbg=(0.96, 0.92, 0.82)),
    card_style=dict(box=None, ink=CREAM, hi=GOLD, y=150, fe=SERIF, fk=BLK),
    cards=[(0.3, 3.6, ['The sunlight on your face', 'is *8 minutes old*.'], ['얼굴에 닿은 햇빛은', '*8분 전*의 빛이다']),
           (3.8, 8.6, ['It left the Sun', '*8 minutes 20 seconds* ago.'], ['해를 떠난 지', '*8분 20초*']),
           (8.8, 13.4, ['Everything you see', 'is a little bit *in the past*.'], ['눈에 보이는 모든 것은', '조금씩 *과거*다']),
           (13.6, 18.6, ['If the Sun vanished,', 'we wouldn’t know for *8 minutes*.'], ['해가 사라져도', '*8분* 동안은 모른다'])],
    coda=[('The light on your face', '얼굴에 닿은 햇빛은'), ('left the Sun eight minutes ago.', '8분 전에 해를 떠났다'), ('What you see is already the past. Live now.', '보이는 건 이미 과거다, 지금을 살자')],
    coda_style=dict(dim=0.6, blur=10, tint=(0.04, 0.04, 0.05), ink=CREAM, hi=GOLD),
    sources=['Smithsonian “How Things Fly”: the Sun is ~150 million km away, so light takes ~8 min 20 s. UCAR: 8⅓ minutes.', 'Moonlight ≈ 1.3 s (384,400 km ÷ 299,792 km/s, calculated). Alpha Centauri ≈ 4.3 light-years.'],
    yt=dict(title_en='The Sunlight You See Is 8 Minutes Old #Shorts', title_ko='지금 보는 햇빛은 8분 20초 전의 빛')))

if __name__ == '__main__': main(EP)
