"""〈딱총새우의 한 방〉 — 만화책(흑백 칸 나누기, 집중선, 스크린톤 망점, 굵은 의성어), 소리는 타이코와 날카로운 '딱' 소리, 물방울.
사실: 딱총새우가 집게를 닫으면 빠른 물줄기 속에 공동(캐비테이션) 거품이 생기고, 거품이 무너질 때 큰 소리와 짧은 빛이 난다(Versluis et al. 2000 Science; Lohse et al. 2001 Nature).
무너지는 순간 거품 속은 최소 5,000 K(약 4,700 °C)로 추정(Lohse et al. 2001). 해 표면 약 5,500 °C에 가깝다(NASA, 비교는 계산).
2차 대전 때 이 딱딱 소리가 잠수함 음파 탐지를 방해하기도 했다(Scientific American).
"""
import math, numpy as np, cv2, cairo
from base import *
import sfx as S

PAPERM = (0.97, 0.96, 0.93); INKM = (0.06, 0.06, 0.07); REDM = (0.88, 0.12, 0.10)
T_BUB = 4.0; T_HOT = 9.6; T_WAR = 15.0; T_CODA = 20.6
yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
TONE = ((np.sin(xx / (5 * SC) * math.pi) * np.sin(yy / (5 * SC) * math.pi)) > 0.35).astype(np.float32)

def speedlines(cr, cx, cy, a, n=90, r0=260):
    rr = np.random.default_rng(3)
    cr.set_source_rgba(*INKM, a)
    for k in range(n):
        q = k * 2 * math.pi / n + rr.uniform(-0.02, 0.02); w = rr.uniform(0.004, 0.014); r1 = r0 + rr.uniform(0, 160)
        cr.move_to(cx + r1 * math.cos(q), cy + r1 * math.sin(q))
        cr.line_to(cx + 1600 * math.cos(q - w), cy + 1600 * math.sin(q - w)); cr.line_to(cx + 1600 * math.cos(q + w), cy + 1600 * math.sin(q + w)); cr.close_path(); cr.fill()

def shrimp(cr, x, y, sc, claw, a=1.0):
    cr.save(); cr.translate(x, y); cr.scale(sc, sc)
    cr.set_line_width(6 / sc); cr.set_line_join(cairo.LINE_JOIN_ROUND)
    def sh(fn, fill=PAPERM):
        fn(); cr.set_source_rgba(*fill, a); cr.fill_preserve(); cr.set_source_rgba(*INKM, a); cr.stroke()
    for k in range(5):                                                   # 몸 마디
        sh(lambda k=k: (cr.save(), cr.translate(-60 - k * 48, 10 + k * 6), cr.scale(1, 0.8), cr.arc(0, 0, 44 - k * 4, 0, 6.283), cr.restore()))
    sh(lambda: (cr.move_to(-300, 40), cr.line_to(-360, 0), cr.line_to(-360, 80), cr.close_path()))
    sh(lambda: (cr.save(), cr.scale(1.4, 0.9), cr.arc(0, 0, 60, 0, 6.283), cr.restore()))
    cr.set_source_rgba(*INKM, a); cr.arc(60, -30, 9, 0, 6.283); cr.fill()
    cr.move_to(70, -40); cr.curve_to(160, -140, 260, -160, 330, -120); cr.stroke()
    cr.move_to(70, -36); cr.curve_to(170, -110, 250, -100, 320, -70); cr.stroke()
    sh(lambda: (cr.save(), cr.translate(150, 40), cr.scale(1.5, 0.8), cr.arc(0, 0, 60, 0, 6.283), cr.restore()), (0.80, 0.80, 0.80))   # 큰 집게
    open_ = 0.6 * (1 - claw)
    sh(lambda: (cr.save(), cr.translate(230, 20), cr.rotate(-open_), cr.move_to(0, 0), cr.line_to(90, -10), cr.line_to(80, 18), cr.line_to(0, 24), cr.close_path(), cr.restore()))
    sh(lambda: (cr.move_to(230, 40), cr.line_to(330, 40), cr.line_to(300, 70), cr.line_to(230, 66), cr.close_path()))
    cr.restore()

def panel(cr, x, y, w, h):
    cr.set_source_rgb(*INKM); cr.set_line_width(8); cr.rectangle(x, y, w, h); cr.stroke()

def draw(t):
    s, cr = surf(); cr.set_source_rgb(*PAPERM); cr.paint()
    tone_s, tone_c = surf()                                              # 스크린톤 칠할 곳
    if t < T_BUB:                                                        # 집게가 닫힌다
        a = 1 - ramp(t, T_BUB - 0.3, T_BUB)
        snap = ramp(t, 2.4, 2.55)
        panel(cr, 80, 560, 920, 1200)
        tone_c.set_source_rgba(1, 1, 1, a); tone_c.rectangle(80, 1400, 920, 360); tone_c.fill()
        if snap > 0: cr.save(); cr.rectangle(80, 560, 920, 1200); cr.clip(); speedlines(cr, 760, 1180, a * snap * (1 - ramp(t, 2.9, 3.6))); cr.restore()
        shrimp(cr, 520, 1200, 1.1, snap, a)
        if snap > 0:
            txt(cr, 'SNAP!', 600, 900, 170 * (0.8 + 0.2 * snap), REDM, a * (1 - ramp(t, 3.4, 3.9)), fam=BLK)
            txt(cr, '딱!', 840, 1000, 110, INKM, a * (1 - ramp(t, 3.4, 3.9)), fam=BLK)
    elif t < T_HOT:                                                      # 거품이 생기고 무너진다
        a = ramp(t, T_BUB, T_BUB + 0.3) * (1 - ramp(t, T_HOT - 0.3, T_HOT))
        panel(cr, 80, 560, 440, 560); panel(cr, 560, 560, 440, 560); panel(cr, 80, 1160, 920, 600)
        g = ramp(t, T_BUB + 0.4, T_BUB + 1.4); c = ramp(t, T_BUB + 1.6, T_BUB + 2.0)
        cr.set_source_rgba(*INKM, a); cr.set_line_width(6); cr.arc(300, 840, 40 + 120 * g, 0, 6.283); cr.stroke()
        txt(cr, 'bubble', 300, 1080, 40, INKM, a, fam=BOLD)
        R = (160 * (1 - c)) + 6
        cr.arc(780, 840, R, 0, 6.283); cr.stroke()
        if c > 0.9:
            cr.save(); cr.rectangle(560, 560, 440, 560); cr.clip(); speedlines(cr, 780, 840, a, n=50, r0=40); cr.restore()
            cr.set_source_rgba(1, 1, 0.8, a); cr.arc(780, 840, 30, 0, 6.283); cr.fill()
        txt(cr, 'collapse', 780, 1080, 40, INKM, a, fam=BOLD)
        tone_c.set_source_rgba(1, 1, 1, a); tone_c.rectangle(80, 1160, 920, 600); tone_c.fill()
        txt(cr, 'BANG + FLASH', 540, 1430, 96, REDM, a * ramp(t, T_BUB + 2.0, T_BUB + 2.3), fam=BLK)
        txt(cr, '소리와 빛', 540, 1540, 64, INKM, a * ramp(t, T_BUB + 2.0, T_BUB + 2.3), fam=BLK)
    elif t < T_WAR:                                                      # 해 표면과 비교
        a = ramp(t, T_HOT, T_HOT + 0.3) * (1 - ramp(t, T_WAR - 0.3, T_WAR))
        panel(cr, 80, 560, 920, 1200)
        g = smooth(ramp(t, T_HOT + 0.4, T_HOT + 2.2))
        for i, (lab, v, col) in enumerate([('inside the bubble · 거품 속', 4700, REDM), ('Sun’s surface · 해 표면', 5500, INKM)]):
            y = 860 + i * 380; L = 780 * v / 5800 * g
            cr.set_source_rgba(*col, a); cr.rectangle(150, y, L, 90); cr.fill()
            txt(cr, f'~{int(v * g):,} °C', 150, y - 24, 64, col, a, fam=BLK, anchor='l')
            txt(cr, lab, 150, y + 150, 38, INKM, a, fam=BOLD, anchor='l')
            if i == 0:
                tone_c.set_source_rgba(1, 1, 1, a); tone_c.rectangle(150, y, L, 90); tone_c.fill()
        txt(cr, 'for a split second · 아주 잠깐', 540, 1640, 40, INKM, a * ramp(t, T_HOT + 2.4, T_HOT + 2.8), fam=BOLD)
    else:                                                                # 잠수함 음파 방해
        a = ramp(t, T_WAR, T_WAR + 0.3) * (1 - ramp(t, T_CODA - 0.3, T_CODA))
        panel(cr, 80, 560, 920, 1200)
        cr.set_source_rgba(0.16, 0.18, 0.24, a); cr.rectangle(80, 560, 920, 1200); cr.fill()
        cr.set_source_rgba(0.02, 0.02, 0.03, a); cr.save(); cr.translate(540, 900); cr.scale(2.6, 1); cr.arc(0, 0, 90, 0, 6.283); cr.restore(); cr.fill()
        cr.rectangle(480, 760, 90, 70); cr.fill()
        cr.set_source_rgba(0.75, 0.85, 1.0, a); cr.arc(330, 900, 12, 0, 6.283); cr.fill()
        for k in range(4):
            cr.set_source_rgba(0.75, 0.85, 1.0, a * 0.8); cr.set_line_width(5)
            cr.arc(780, 900, 60 + k * 50, -0.6, 0.6); cr.stroke()
        rr = np.random.default_rng(int(t * 6))
        for k in range(14):
            x = rr.uniform(150, 930); y = rr.uniform(1150, 1700)
            txt(cr, '딱', x, y, rr.uniform(40, 80), PAPERM, a, fam=BLK)
        txt(cr, 'WWII SONAR · 잠수함 음파 방해', 540, 1100, 46, PAPERM, a, fam=BLK)
    paper = np.ascontiguousarray(arr(s)[..., :3])
    tmask = arr(tone_s)[..., 3:4]
    img = paper * (1 - tmask * TONE[..., None] * 0.55)
    return np.clip(img, 0, 1)

def sound(path):
    m = S.Mix(EP['DUR'], 5000); tc = EP['t_coda']
    m.put('amb', 0, S.stream(EP['t_end'] + 1, 0.06, seed=1))
    for k in range(int(tc / 0.7)): m.put('amb', 0.3 + k * 0.7 + (0.1 if k % 3 == 0 else 0), S.tok(2400 + 200 * (k % 4), 0.05))
    m.put('fx', 2.4, S.taiko(0.8)); m.put('fx', 2.4, S.icecrack(0.5, seed=2) if hasattr(S, 'icecrack') else S.tok(3000, 0.5))
    m.put('fx', T_BUB + 1.9, S.taiko(0.6)); m.put('fx', T_BUB + 1.9, S.swoosh(0.4, 0.3, 3000, 9000))
    for k in range(8): m.put('mus', T_HOT + 0.3 + k * 0.6, S.taiko(0.25 + 0.03 * k))
    rr = np.random.default_rng(9)
    for k in range(40): m.put('fx', T_WAR + 0.2 + rr.uniform(0, 5.0), S.tok(rr.uniform(2000, 4000), 0.12))
    m.put('amb', T_WAR, S.beep(880.0, 0.3, 0.12)); m.put('amb', T_WAR + 1.6, S.beep(880.0, 0.3, 0.1))
    for i, g in enumerate([0.5, 0.4, 0.6]): m.put('mus', tc + 0.8 + i * STEP, S.taiko(g))
    m.write(path, rev_mus=1.6, wet_mus=0.3)

EP = finalize(dict(t_coda=T_CODA, draw=draw, sound=sound, end_icon='star', grain=0.0,
    title_en_card='THE SHRIMP THAT SNAPS', title_ko_card='딱총새우의 한 방',
    pal=dict(hi=REDM, endbg=PAPERM),
    card_style=dict(box='paper', bg=(1.0, 1.0, 0.98), ink=INKM, hi=REDM, y=180, fe=BLK, fk=BLK),
    cards=[(0.3, 3.8, ['The pistol shrimp', 'snaps its claw shut.'], ['딱총새우가', '집게를 탁 닫는다']),
           (4.0, 9.4, ['A bubble forms and *collapses*', 'with a bang and a flash.'], ['거품이 생겼다 *무너지며*', '소리와 빛이 터진다']),
           (9.6, 14.8, ['Inside, it reaches about *4,700 °C*,', 'close to the Sun’s surface.'], ['그 속은 약 *4,700°C*,', '해 표면에 가깝다']),
           (15.0, 20.4, ['In WWII, their crackling', 'even *jammed submarine sonar*.'], ['2차 대전 때는 그 소리가', '*잠수함 음파 탐지*를 방해했다'])],
    coda=[('The smallest creature', '가장 작은 생물도'), ('can make the loudest sound.', '가장 큰 소리를 낼 수 있다'), ('Never measure power by size.', '힘을 크기로 재지 말자')],
    coda_style=dict(dim=0.5, blur=8, tint=(0.80, 0.80, 0.78), ink=INKM, hi=REDM, fe=BLK),
    sources=['Snapping shrimp claw closure creates a cavitation bubble whose collapse makes the snap and a flash of light (Versluis et al. 2000, Science; Lohse et al. 2001, Nature).', 'At least 5,000 K (~4,700 °C) inside the collapsing bubble (Lohse et al. 2001); Sun’s surface ~5,500 °C (NASA). WWII sonar interference (Scientific American).'],
    yt=dict(title_en='This Shrimp Makes a Bubble Nearly as Hot as the Sun #Shorts', title_ko='해만큼 뜨거운 거품을 만드는 딱총새우')))

if __name__ == '__main__': main(EP)
