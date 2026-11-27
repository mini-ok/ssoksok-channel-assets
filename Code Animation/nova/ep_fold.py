"""〈종이를 42번 접으면〉 — 청사진(파란 바탕, 흰 제도선, 치수선·화살표, 모눈, 도면 표제란), 소리는 FM 신스 아르페지오와 낮은 펄스.
계산: 두께 0.1 mm 종이를 반으로 접을 때마다 두 배. 42번 → 0.1 mm × 2^42 ≈ 439,805 km, 달까지 평균 384,400 km보다 멀다(계산).
103번 → 약 1.0 × 10^27 m, 관측 가능한 우주 지름(약 8.8 × 10^26 m)보다 크다(계산).
사실: 실제로 가장 많이 접은 기록은 12번(Britney Gallivan, 2002년, 길이 약 1.2 km 휴지)(Guinness World Records).
"""
import math, numpy as np, cv2, cairo
from base import *
import sfx as S

BP = (0.06, 0.24, 0.52); BPL = (0.10, 0.32, 0.62); LINE = (0.92, 0.96, 1.0); ACC = (1.0, 0.82, 0.30)
T_EXP = 4.2; T_MOON = 9.8; T_REAL = 15.2; T_CODA = 20.6

def bg(cr):
    cr.set_source_rgb(*BP); cr.paint()
    cr.set_line_width(1)
    for k in range(0, 1080, 40):
        cr.set_source_rgba(*LINE, 0.10 if k % 200 else 0.22); cr.move_to(k, 0); cr.line_to(k, 1920); cr.stroke()
    for k in range(0, 1920, 40):
        cr.set_source_rgba(*LINE, 0.10 if k % 200 else 0.22); cr.move_to(0, k); cr.line_to(1080, k); cr.stroke()
    cr.set_source_rgba(*LINE, 0.8); cr.set_line_width(3); cr.rectangle(40, 40, 1000, 1840); cr.stroke()
    cr.rectangle(640, 1740, 400, 140); cr.stroke(); cr.move_to(640, 1800); cr.line_to(1040, 1800); cr.stroke()
    txt(cr, 'DWG No. 42 · FOLD', 840, 1785, 28, LINE, 0.8, fam=BOLD)
    txt(cr, 'SCALE: LOG', 840, 1850, 28, LINE, 0.8, fam=BOLD)

def dim(cr, x, y0, y1, label, a, col=LINE):
    cr.set_source_rgba(*col, a); cr.set_line_width(2)
    cr.move_to(x, y0); cr.line_to(x, y1); cr.stroke()
    for y, d in ((y0, 1), (y1, -1)):
        cr.move_to(x, y); cr.line_to(x - 10, y + 18 * d); cr.line_to(x + 10, y + 18 * d); cr.close_path(); cr.fill()
        cr.move_to(x - 30, y); cr.line_to(x + 30, y); cr.stroke()
    txt(cr, label, x + 40, (y0 + y1) / 2 + 12, 36, col, a, fam=BOLD, anchor='l')

def fmt(mm):
    if mm < 10: return f'{mm:.1f} mm'
    if mm < 1000: return f'{mm/10:.1f} cm'
    if mm < 1e6: return f'{mm/1000:,.1f} m'
    return f'{mm/1e6:,.0f} km'

def draw(t):
    s, cr = surf(); bg(cr)
    if t < T_EXP:                                                         # 한 장 → 몇 번 접기
        a = 1 - ramp(t, T_EXP - 0.3, T_EXP)
        n = min(7, int(ramp(t, 0.6, 3.6) * 7.999))
        w = 700 / (2 ** (n / 2)); h = 26 * (2 ** n) ** 0.0 + 6 * (2 ** n)
        h = min(6 * 2 ** n, 760)
        cr.set_source_rgba(*LINE, a); cr.set_line_width(3)
        for k in range(min(2 ** n, 64)):
            yy = 1400 - (k + 1) * h / max(1, min(2 ** n, 64))
            cr.move_to(540 - w / 2, yy); cr.line_to(540 + w / 2, yy); cr.stroke()
        cr.rectangle(540 - w / 2, 1400 - h, w, h); cr.stroke()
        dim(cr, 540 + w / 2 + 50, 1400 - h, 1400, fmt(0.1 * 2 ** n), a, ACC)
        txt(cr, f'FOLDS: {n}', 540, 1520, 64, LINE, a, fam=BLK)
    elif t < T_MOON:                                                      # 접을 때마다 두 배 — 로그 눈금
        a = ramp(t, T_EXP, T_EXP + 0.3) * (1 - ramp(t, T_MOON - 0.3, T_MOON))
        p = ramp(t, T_EXP + 0.3, T_MOON - 1.0); n = int(p * 42.999)
        top, bot = 560, 1660
        marks = [(0.1, 'paper'), (1e3, '1 m'), (1e6, '1 km'), (8.849e6, 'Everest'), (4e8, 'ISS orbit'), (3.844e11, 'Moon')]
        lo, hi = math.log10(0.1), math.log10(3.844e11 * 1.4)
        Y = lambda mm: bot - (bot - top) * (math.log10(mm) - lo) / (hi - lo)
        cr.set_source_rgba(*LINE, a); cr.set_line_width(3); cr.move_to(300, top); cr.line_to(300, bot); cr.stroke()
        for mm, lab in marks:
            y = Y(mm); cr.move_to(280, y); cr.line_to(320, y); cr.stroke()
            txt(cr, lab, 260, y + 12, 32, LINE, a, fam=BOLD, anchor='r')
        cur = 0.1 * 2 ** n; y = Y(cur)
        cr.set_source_rgba(*ACC, a); cr.rectangle(300, y, 60, bot - y); cr.fill()
        txt(cr, f'{n} folds', 400, y + 4, 52, ACC, a, fam=BLK, anchor='l')
        txt(cr, fmt(cur), 400, y + 56, 40, LINE, a, fam=BOLD, anchor='l')
    elif t < T_REAL:                                                      # 42번 = 달 너머
        a = ramp(t, T_MOON, T_MOON + 0.3) * (1 - ramp(t, T_REAL - 0.3, T_REAL))
        g = smooth(ramp(t, T_MOON + 0.3, T_MOON + 2.6))
        ex, mx, y = 160, 820, 1050
        cr.set_source_rgba(*LINE, a); cr.set_line_width(4); cr.arc(ex, y, 70, 0, 6.283); cr.stroke()
        for k in range(-2, 3): cr.move_to(ex - 70, y + k * 25); cr.line_to(ex + 70, y + k * 25); cr.stroke()
        cr.arc(mx, y, 26, 0, 6.283); cr.stroke()
        txt(cr, 'MOON 384,400 km', mx, y - 60, 34, LINE, a, fam=BOLD)
        L = (mx - ex) * 439805 / 384400
        cr.set_source_rgba(*ACC, a); cr.rectangle(ex + 70, y + 110, (L - 70) * g, 30); cr.fill()
        txt(cr, '42 folds ≈ 439,805 km', 540, y + 220, 52, ACC, a * ramp(t, T_MOON + 2.4, T_MOON + 2.8), fam=BLK)
        txt(cr, 'calculated (0.1 mm paper) · 계산', 540, y + 280, 30, LINE, a * ramp(t, T_MOON + 2.4, T_MOON + 2.8), fam=BOLD)
        txt(cr, '103 folds > observable universe', 540, y + 400, 40, LINE, a * ramp(t, T_MOON + 3.4, T_MOON + 3.8), fam=BOLD)
    else:                                                                 # 실제 기록 12번
        a = ramp(t, T_REAL, T_REAL + 0.3) * (1 - ramp(t, T_CODA - 0.3, T_CODA))
        g = smooth(ramp(t, T_REAL + 0.4, T_REAL + 3.0))
        cr.set_source_rgba(*LINE, a); cr.set_line_width(3)
        for k in range(12):
            on = k / 12 < g; cr.set_source_rgba(*(ACC if on else LINE), a * (1 if on else 0.3))
            cr.rectangle(200 + (k % 6) * 115, 700 + (k // 6) * 160, 90, 120); cr.stroke() if not on else cr.fill()
        txt(cr, 'WORLD RECORD: 12', 540, 1120, 72, ACC, a * ramp(t, T_REAL + 3.0, T_REAL + 3.4), fam=BLK)
        txt(cr, '2002 · 1.2 km of tissue paper', 540, 1190, 38, LINE, a * ramp(t, T_REAL + 3.4, T_REAL + 3.8), fam=BOLD)
    return np.ascontiguousarray(arr(s)[..., :3])

def sound(path):
    m = S.Mix(EP['DUR'], 42); tc = EP['t_coda']; b = 60 / 118
    arp = [220.0, 261.6, 329.6, 392.0, 440.0, 392.0, 329.6, 261.6]
    t = 0.2; k = 0
    while t < tc - 0.3:
        oct_ = 2 if (T_EXP < t < T_MOON and k % 16 >= 8) else 1
        m.put('mus', t, S.fm(arp[k % 8] * oct_, 0.5, 0.16, 2.0, 2.5, 6.0))
        if k % 4 == 0: m.put('mus', t, S.drone([55.0], b * 1.8, 0.2, 'sine'))
        t += b / 2; k += 1
    for k in range(7): m.put('fx', 0.6 + k * 3.0 / 7, S.tok(500 + 60 * k, 0.14))
    m.put('fx', T_MOON + 2.6, S.bell(880.0, 2.4, 0.22)); m.put('fx', T_REAL + 3.0, S.bell(659.3, 2.4, 0.2))
    for i, f in enumerate([440.0, 329.6, 220.0]): m.put('mus', tc + 0.8 + i * STEP, S.fm(f, 2.6, 0.24, 1.0, 1.6, 1.5))
    m.write(path, rev_mus=2.2, wet_mus=0.35)

EP = finalize(dict(t_coda=T_CODA, draw=draw, sound=sound, end_icon='star', grain=0.0,
    title_en_card='FOLD IT 42 TIMES', title_ko_card='종이를 42번 접으면',
    pal=dict(hi=(0.85, 0.55, 0.05), endbg=(0.90, 0.94, 0.99)),
    card_style=dict(box='paper', bg=(0.92, 0.96, 1.0), ink=(0.04, 0.14, 0.34), hi=(0.80, 0.45, 0.02), y=180, fe=BOLD, fk=BLK),
    cards=[(0.3, 4.0, ['Each fold doubles', 'the thickness of paper.'], ['종이를 한 번 접을 때마다', '두께는 두 배']),
           (4.2, 9.6, ['Doubling grows', '*faster than you expect*.'], ['두 배씩 커지는 것은', '*생각보다 훨씬 빠르다*']),
           (9.8, 15.0, ['42 folds of 0.1 mm paper', 'would reach *past the Moon*.'], ['0.1mm 종이를 42번 접으면', '*달 너머*까지 닿는다']),
           (15.2, 20.4, ['In reality, the record is *12*,', 'set in 2002.'], ['실제 기록은 *12번*,', '2002년'])],
    coda=[('Small steps, doubled,', '작은 걸음도 두 배씩 쌓이면'), ('can reach the Moon.', '달에 닿는다'), ('Keep folding today into tomorrow.', '오늘을 내일에 계속 겹쳐 가자')],
    coda_style=dict(dim=0.5, blur=8, tint=(0.10, 0.28, 0.56), ink=(0.95, 0.97, 1.0), hi=(1.0, 0.82, 0.30), fe=BOLD),
    sources=['0.1 mm × 2^42 ≈ 439,805 km, beyond the Moon’s average distance of 384,400 km; 0.1 mm × 2^103 ≈ 10^27 m, larger than the observable universe (~8.8 × 10^26 m) (calculated).', 'Record: 12 folds by Britney Gallivan, 27 Jan 2002, with ~1.2 km of tissue paper (Guinness World Records).'],
    yt=dict(title_en='Fold Paper 42 Times and It Reaches the Moon #Shorts', title_ko='종이를 42번 접으면 달에 닿는다')))

if __name__ == '__main__': main(EP)
