"""〈1분에 1,260번 뛰는 심장〉 — 아르누보(채찍처럼 휘는 덩굴선, 굵은 윤곽, 둥근 후광, 금빛·올리브·자주 평면 색, 장식 테두리), 소리는 하프처럼 뜯는 현 아르페지오와 빠른 심장 박.
사실: 벌새 심장은 날 때 분당 최대 약 1,260번(블루스로티드벌새 측정)(San Diego Zoo; Audubon은 활동 시 약 1,200번).
날갯짓은 종에 따라 초당 약 10~80번(Bob Vila/Audubon 계열 자료, Ole Miss). 밤에는 휴면(torpor)으로 심박을 분당 약 50번까지 낮춘다(Ole Miss).
사람 안정 시 심박 약 60~100번 → 벌새가 10배 이상 빠르다(계산).
"""
import math, numpy as np, cv2, cairo
from base import *
import sfx as S

CRM = (0.95, 0.90, 0.78); GOLDN = (0.80, 0.62, 0.25); OLIVE = (0.42, 0.48, 0.26); PLUM = (0.48, 0.20, 0.36); INKN = (0.18, 0.12, 0.10)
EMER = (0.12, 0.52, 0.42); ROSE = (0.86, 0.42, 0.42); NIGHTN = (0.16, 0.18, 0.30)
T_HEART = 4.2; T_WING = 9.8; T_NIGHT = 15.2; T_CODA = 20.6

def border(cr, a=1.0):
    cr.set_source_rgba(*INKN, a); cr.set_line_width(8); cr.rectangle(50, 50, 980, 1820); cr.stroke()
    cr.set_line_width(5)
    for side in (1, -1):                                               # 채찍 덩굴
        x0 = 540 - side * 460
        cr.move_to(x0, 1860)
        cr.curve_to(x0 + side * 140, 1500, x0 - side * 60, 1250, x0 + side * 90, 980)
        cr.curve_to(x0 + side * 200, 760, x0 - side * 40, 640, x0 + side * 60, 520); cr.stroke()
        for k, (lx, ly) in enumerate([(x0 + side * 120, 1420), (x0 + side * 40, 1150), (x0 + side * 140, 860)]):
            cr.set_source_rgba(*OLIVE, a); cr.save(); cr.translate(lx, ly); cr.rotate(side * 0.6); cr.scale(60, 22); cr.arc(0, 0, 1, 0, 6.283); cr.restore(); cr.fill_preserve()
            cr.set_source_rgba(*INKN, a); cr.stroke()

def halo(cr, cx, cy, R, a=1.0, col=GOLDN):
    cr.set_source_rgba(*col, a); cr.arc(cx, cy, R, 0, 6.283); cr.fill()
    cr.set_source_rgba(*INKN, a); cr.set_line_width(6); cr.arc(cx, cy, R, 0, 6.283); cr.stroke()
    cr.set_line_width(2); cr.arc(cx, cy, R - 24, 0, 6.283); cr.stroke()

def bird(cr, x, y, sc, wing, a=1.0):
    cr.save(); cr.translate(x, y); cr.scale(sc, sc)
    def shape(fn, col):
        fn(); cr.set_source_rgba(*col, a); cr.fill_preserve(); cr.set_source_rgba(*INKN, a); cr.set_line_width(4 / sc); cr.stroke()
    w = wing
    shape(lambda: (cr.move_to(-10, -10), cr.curve_to(-60, -80 - 90 * w, -140, -150 - 40 * w, -170, -120 - 120 * w), cr.curve_to(-120, -60, -60, -10, -10, 10), cr.close_path()), EMER)
    shape(lambda: (cr.move_to(-90, 20), cr.curve_to(-40, -40, 50, -40, 70, -10), cr.curve_to(60, 30, -20, 50, -90, 20), cr.close_path()), EMER)
    shape(lambda: (cr.move_to(-90, 20), cr.line_to(-170, 40), cr.line_to(-150, 10), cr.line_to(-180, 0), cr.line_to(-90, 5), cr.close_path()), OLIVE)
    shape(lambda: cr.arc(70, -20, 30, 0, 6.283), EMER)
    shape(lambda: (cr.move_to(52, 0), cr.curve_to(60, 20, 80, 22, 90, 6), cr.line_to(70, -4), cr.close_path()), ROSE)    # 붉은 목
    cr.set_source_rgba(*INKN, a); cr.set_line_width(5 / sc); cr.move_to(98, -24); cr.line_to(200, -14); cr.stroke()   # 부리
    cr.arc(78, -26, 5, 0, 6.283); cr.fill()
    shape(lambda: (cr.move_to(-5, -5), cr.curve_to(40, -90 - 60 * w, 10, -170 - 30 * w, -20, -190 - 60 * w), cr.curve_to(-50, -120, -40, -40, -5, 5), cr.close_path()), (0.22, 0.62, 0.50))
    cr.restore()

def flower(cr, x, y, a=1.0):
    cr.set_source_rgba(*PLUM, a); cr.move_to(x, y); cr.curve_to(x + 40, y + 30, x + 50, y + 120, x + 20, y + 200); cr.line_to(x - 20, y + 200)
    cr.curve_to(x - 50, y + 120, x - 40, y + 30, x, y); cr.close_path(); cr.fill_preserve(); cr.set_source_rgba(*INKN, a); cr.set_line_width(4); cr.stroke()
    cr.move_to(x, y + 200); cr.curve_to(x + 20, y + 300, x - 30, y + 380, x + 10, y + 460); cr.stroke()

def heart_icon(cr, x, y, s_, col, a):
    cr.save(); cr.translate(x, y); cr.scale(s_, s_); cr.move_to(0, 30); cr.curve_to(-60, -10, -40, -60, 0, -30); cr.curve_to(40, -60, 60, -10, 0, 30); cr.close_path()
    cr.restore(); cr.set_source_rgba(*col, a); cr.fill_preserve(); cr.set_source_rgba(*INKN, a); cr.set_line_width(4); cr.stroke()

def draw(t):
    s, cr = surf()
    night = ramp(t, T_NIGHT, T_NIGHT + 0.8) * (1 - ramp(t, T_CODA - 0.3, T_CODA))
    cr.set_source_rgb(*[CRM[i] * (1 - night) + NIGHTN[i] * night for i in range(3)]); cr.paint()
    border(cr)
    if t < T_HEART:
        a = 1 - ramp(t, T_HEART - 0.3, T_HEART)
        halo(cr, 540, 1000, 320, a); flower(cr, 820, 900, a)
        bird(cr, 520 + 10 * math.sin(t * 3), 1020, 1.5, math.sin(t * 2 * math.pi * 6), a)
    elif t < T_WING:                                                   # 심장 박 비교
        a = ramp(t, T_HEART, T_HEART + 0.3) * (1 - ramp(t, T_WING - 0.3, T_WING))
        hb = 0.5 + 0.5 * math.cos(t * 2 * math.pi * 21.0)              # 1,260/60 = 21 Hz → 깜박임 방지로 아래에서 줄인다
        hb = 0.5 + 0.5 * math.cos(t * 2 * math.pi * 3.5)               # 화면에서는 6배 느리게(표시)
        hh = 0.5 + 0.5 * math.cos(t * 2 * math.pi * 70 / 60 / 6 * 6 / 6)
        halo(cr, 340, 900, 160, a, GOLDN); halo(cr, 740, 900, 160, a, (0.82, 0.74, 0.60))
        heart_icon(cr, 340, 900, 1.6 + 0.35 * hb, ROSE, a); heart_icon(cr, 740, 900, 1.6 + 0.35 * (0.5 + 0.5 * math.cos(t * 2 * math.pi * 70 / 60 / 18 * 3.5 * 18 / 21)), PLUM, a)
        txt(cr, '1,260', 340, 1200, 84, INKN, a, fam=SERIF); txt(cr, 'hummingbird · 벌새', 340, 1255, 34, INKN, a, fam=SERIF)
        txt(cr, '~70', 740, 1200, 84, INKN, a, fam=SERIF); txt(cr, 'you · 사람', 740, 1255, 34, INKN, a, fam=SERIF)
        txt(cr, 'beats per minute · 분당 박동', 540, 1380, 40, PLUM, a * ramp(t, T_HEART + 1.0, T_HEART + 1.4), fam=SERIF)
        txt(cr, '(heart animation slowed · 화면은 느리게)', 540, 1440, 28, INKN, a * 0.7, fam=SERIF)
    elif t < T_NIGHT:                                                  # 날갯짓 80/s
        a = ramp(t, T_WING, T_WING + 0.3) * (1 - ramp(t, T_NIGHT - 0.3, T_NIGHT))
        halo(cr, 540, 1000, 320, a); flower(cr, 820, 980, a)
        for k in range(5):                                             # 잔상(날개가 번져 보임)
            bird(cr, 480, 1040, 1.5, math.sin(k * 1.25), a * (0.25 if k else 0.9))
        txt(cr, 'up to ~80 wingbeats / s', 540, 1520, 44, INKN, a * ramp(t, T_WING + 1.0, T_WING + 1.4), fam=SERIF)
        txt(cr, '초당 최대 약 80번 날갯짓', 540, 1580, 38, PLUM, a * ramp(t, T_WING + 1.0, T_WING + 1.4), fam=SERIF)
    else:                                                              # 밤: 휴면
        a = ramp(t, T_NIGHT, T_NIGHT + 0.3) * (1 - ramp(t, T_CODA - 0.3, T_CODA))
        halo(cr, 540, 960, 300, a, (0.90, 0.86, 0.66))
        cr.set_source_rgba(*NIGHTN, a); cr.arc(640, 900, 260, 0, 6.283); cr.fill()      # 초승달
        cr.save(); cr.translate(500, 1090); cr.scale(1.3, 1.3)
        cr.set_source_rgba(*EMER, a); cr.save(); cr.scale(1.0, 0.75); cr.arc(0, 0, 70, 0, 6.283); cr.restore(); cr.fill_preserve(); cr.set_source_rgba(*INKN, a); cr.set_line_width(3); cr.stroke()
        cr.set_source_rgba(*EMER, a); cr.arc(60, -30, 30, 0, 6.283); cr.fill_preserve(); cr.set_source_rgba(*INKN, a); cr.stroke()
        cr.move_to(85, -30); cr.line_to(170, -10); cr.stroke(); cr.move_to(66, -36); cr.line_to(80, -32); cr.stroke()
        cr.restore()
        cr.set_source_rgba(*INKN, a); cr.set_line_width(6); cr.move_to(200, 1170); cr.curve_to(400, 1150, 700, 1190, 900, 1160); cr.stroke()
        bpm = int(1260 - (1260 - 50) * smooth(ramp(t, T_NIGHT + 0.6, T_NIGHT + 3.4)))
        txt(cr, f'{bpm:,} → 50', 540, 1440, 90, (0.95, 0.90, 0.78), a, fam=SERIF)
        txt(cr, 'night torpor · 밤의 휴면', 540, 1510, 40, (0.95, 0.90, 0.78), a, fam=SERIF)
    return np.ascontiguousarray(arr(s)[..., :3])

def sound(path):
    m = S.Mix(EP['DUR'], 1260); tc = EP['t_coda']; b = 60 / 88
    chords = [[293.7, 370.0, 440.0, 587.3], [246.9, 293.7, 370.0, 493.9], [196.0, 246.9, 293.7, 392.0], [220.0, 277.2, 329.6, 440.0]]
    t = 0.3; k = 0
    while t < tc - 0.4:
        ch = chords[(k // 8) % 4]; f = ch[k % 4] * (2 if (k % 8) >= 4 else 1)
        m.put('mus', t, S.pluck(f, 1.6, 0.22, bright=0.35, seed=k)); t += b / 4; k += 1
    tt = T_HEART + 0.3
    while tt < T_WING - 0.3: m.put('fx', tt, S.kick(70, 0.18, 0.12)); tt += 60 / 1260 * 6     # 표시와 같은 6배 느린 박
    m.put('fx', T_WING + 0.2, S.swoosh(4.0, 0.12, 80, 400, seed=5))
    tt = T_NIGHT + 0.6; gap = 60 / 1260 * 6
    while tt < T_CODA - 0.4: m.put('fx', tt, S.kick(60, 0.16, 0.14)); tt += gap; gap = min(1.2, gap * 1.18)
    for i, f in enumerate([587.3, 440.0, 293.7]): m.put('mus', tc + 0.8 + i * STEP, S.pluck(f, 3.0, 0.3, bright=0.3, seed=90 + i))
    m.write(path, rev_mus=2.6, wet_mus=0.4)

EP = finalize(dict(t_coda=T_CODA, draw=draw, sound=sound, end_icon='star', grain=0.0,
    title_en_card='1,260 BEATS A MINUTE', title_ko_card='1분에 1,260번 뛰는 심장',
    pal=dict(hi=PLUM, endbg=CRM),
    card_style=dict(box='paper', bg=(0.97, 0.93, 0.83), ink=INKN, hi=PLUM, y=180, fe=SERIF, fk=BLK),
    cards=[(0.3, 4.0, ['A hummingbird', 'weighs just a few grams.'], ['벌새,', '몸무게는 몇 그램']),
           (4.2, 9.6, ['In flight its heart beats', 'up to *1,260 times* a minute.'], ['날 때 심장은', '분당 최대 *1,260번* 뛴다']),
           (9.8, 15.0, ['Its wings beat', 'up to *80 times* a second.'], ['날개는', '초당 최대 *80번*']),
           (15.2, 20.4, ['At night it rests in torpor:', 'heart down to about *50*.'], ['밤에는 휴면에 들어', '심장이 약 *50번*으로 느려진다'])],
    coda=[('Even the fastest heart', '가장 빠른 심장도'), ('slows down to rest at night.', '밤이면 쉬어 간다'), ('Rest is part of flying.', '쉬는 것도 나는 일의 일부다')],
    coda_style=dict(dim=0.5, blur=8, tint=(0.30, 0.30, 0.42), ink=(0.97, 0.93, 0.83), hi=(0.95, 0.75, 0.40), fe=SERIF),
    sources=['Hummingbird heart rate up to ~1,260 bpm in flight (blue-throated hummingbird; San Diego Zoo Wildlife Alliance); Audubon cites ~1,200 bpm when active.', 'Wingbeats ~10–80 per second depending on species; nightly torpor drops heart rate to ~50 bpm (Ole Miss hummingbird facts; Bob Vila). Human resting 60–100 bpm.'],
    yt=dict(title_en='A Hummingbird’s Heart Beats 1,260 Times a Minute #Shorts', title_ko='1분에 1,260번 뛰는 벌새의 심장')))

if __name__ == '__main__': main(EP)
