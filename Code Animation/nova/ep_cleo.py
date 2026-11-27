"""〈클레오파트라와 달〉 — 파피루스 벽화풍(검은 윤곽, 황토·테라코타·청금석), 프레임드럼·현 뜯는 소리(히자즈 음계).
사실: 대피라미드 완공 약 기원전 2560년, 클레오파트라 7세 기원전 69~30년, 아폴로 11호 달 착륙 1969년.
피라미드→클레오파트라 출생 2,491년, 출생→달 착륙 2,038년(계산; 피라미드 연대는 문헌에 따라 2580~2510년 범위).
"""
import math, numpy as np, cv2, cairo
from base import *
import sfx as S

PAP = (0.90, 0.81, 0.60); OCH = (0.80, 0.55, 0.20); TER = (0.70, 0.27, 0.15); LAP = (0.12, 0.27, 0.55); BLKC = (0.10, 0.08, 0.06); GOLD = (0.88, 0.68, 0.22)
Y0, Y1 = -2560, 1969
def yy(year): return 1560 - (year - Y0) / (Y1 - Y0) * 1000      # 아래가 과거, 위가 현재
X = 300

_P = {}
def papyrus():
    if 'v' in _P: return _P['v']
    r = np.random.default_rng(9)
    base = solid(PAP)
    hl = cv2.resize(r.standard_normal((H, 18)).astype(np.float32), (W, H), interpolation=cv2.INTER_LINEAR)
    vl = cv2.resize(r.standard_normal((14, W)).astype(np.float32), (W, H), interpolation=cv2.INTER_LINEAR)
    fib = cv2.GaussianBlur(r.standard_normal((H, W)).astype(np.float32), (0, 0), sigmaX=1.0, sigmaY=0.4)
    blot = cv2.resize(r.standard_normal((H // 120 + 2, W // 120 + 2)).astype(np.float32), (W, H), interpolation=cv2.INTER_CUBIC)
    tex = 1 + 0.035 * hl + 0.03 * vl + 0.05 * fib + 0.05 * blot
    yv, xv = np.mgrid[0:H, 0:W].astype(np.float32)
    edge = 1 - 0.25 * np.clip(1 - np.minimum.reduce([xv, W - xv, yv, H - yv]) / (60 * SC), 0, 1) ** 2
    _P['v'] = (base * (tex * edge)[..., None]).astype(np.float32); return _P['v']

def borders(cr, a=1.0):
    for x0 in (18, DW - 58):
        cr.set_source_rgba(*BLKC, a); cr.rectangle(x0, 0, 40, DH); cr.fill()
        cols = [LAP, TER, OCH, (0.25, 0.5, 0.45)]
        for i in range(0, DH, 46):
            cr.set_source_rgba(*cols[(i // 46) % 4], a); cr.rectangle(x0 + 5, i + 5, 30, 36); cr.fill()
    cr.set_source_rgba(*BLKC, a); cr.set_line_width(4)
    for y in (1700, 1712):
        cr.move_to(70, y); cr.line_to(DW - 70, y); cr.stroke()
    for k in range(20):                                         # 물결 띠
        x = 90 + k * 46; cr.move_to(x, 1745)
        cr.curve_to(x + 11, 1730, x + 23, 1760, x + 34, 1745); cr.stroke()

def pyramid(cr, x, y, s, a):
    s = max(s, 1e-3); cr.save(); cr.translate(x, y); cr.scale(s, s)
    cr.move_to(-100, 0); cr.line_to(0, -110); cr.line_to(100, 0); cr.close_path()
    cr.set_source_rgba(*OCH, a); cr.fill_preserve(); cr.set_source_rgba(*BLKC, a); cr.set_line_width(5); cr.stroke()
    cr.set_line_width(2)
    for k in range(1, 8):
        yk = -k * 13.7; wk = 100 * (1 - k * 13.7 / 110); cr.move_to(-wk, yk); cr.line_to(wk, yk); cr.stroke()
    cr.set_source_rgba(*TER, a); cr.arc(0, -150, 22, 0, 6.283); cr.fill()
    cr.restore()

def queen(cr, x, y, s, a):
    """이집트 벽화식 옆얼굴(양식화한 창작 도안)."""
    s = max(s, 1e-3); cr.save(); cr.translate(x, y); cr.scale(s, s)
    cr.set_source_rgba(*LAP, a)                                 # 머리 장식
    cr.move_to(-40, -40); cr.curve_to(-40, -100, 30, -110, 40, -60); cr.line_to(30, 30); cr.line_to(-50, 40); cr.close_path(); cr.fill()
    cr.set_source_rgba(*(0.72, 0.48, 0.30), a)                   # 얼굴
    cr.move_to(10, -55); cr.curve_to(40, -55, 44, -30, 52, -14); cr.line_to(40, -8); cr.curve_to(44, 0, 40, 10, 32, 14)
    cr.curve_to(30, 30, 10, 34, 0, 30); cr.line_to(-5, -40); cr.close_path(); cr.fill()
    cr.set_source_rgba(*BLKC, a); cr.set_line_width(3)
    cr.move_to(18, -30); cr.curve_to(26, -36, 34, -34, 38, -28); cr.stroke()           # 눈선
    cr.arc(28, -28, 3.5, 0, 6.283); cr.fill()
    cr.set_source_rgba(*GOLD, a); cr.arc(-5, -90, 9, 0, 6.283); cr.fill()               # 이마 장식
    cr.set_line_width(6); cr.move_to(-30, 50); cr.curve_to(-10, 64, 20, 64, 34, 44); cr.stroke()  # 목걸이
    cr.restore()

def moon(cr, x, y, s, a):
    s = max(s, 1e-3); cr.save(); cr.translate(x, y); cr.scale(s, s)
    cr.set_source_rgba(0.95, 0.93, 0.85, a); cr.arc(0, 0, 70, 0, 6.283); cr.fill_preserve(); cr.set_source_rgba(*BLKC, a); cr.set_line_width(5); cr.stroke()
    cr.set_source_rgba(0.75, 0.72, 0.65, a)
    for cx, cy, r in ((-25, -15, 14), (22, 10, 10), (-5, 30, 8), (30, -30, 7)): cr.arc(cx, cy, r, 0, 6.283); cr.fill()
    cr.set_source_rgba(*BLKC, a); cr.set_line_width(4)          # 착륙선
    cr.rectangle(-18, -110, 36, 22); cr.fill(); cr.move_to(-18, -88); cr.line_to(-30, -68); cr.move_to(18, -88); cr.line_to(30, -68); cr.stroke()
    cr.restore()

T_LINE1 = (3.8, 8.2); T_CLEO = 8.2; T_LINE2 = (9.6, 13.2); T_MOON = 13.2; T_BARS = 15.0; T_CODA = 24.0

def draw(t):
    img = papyrus().copy()
    s, cr = surf(); borders(cr)
    # 처음: 피라미드와 달이 나란히
    a0 = 1 - ramp(t, 3.2, 3.8)
    if a0 > 0:
        k = back_out(ramp(t, 0.2, 0.8), 1.6); pyramid(cr, 320, 1150, 1.6 * k, a0); moon(cr, 760, 1000, 1.3 * back_out(ramp(t, 0.5, 1.1), 1.6), a0)
        txt(cr, 'VS', DW / 2, 1080, 70, TER, a0 * ramp(t, 0.9, 1.2))
    # 세로 연대표
    if t >= 3.4 and t < T_BARS + 0.6:
        fa = ramp(t, 3.4, 3.8) * (1 - ramp(t, T_BARS, T_BARS + 0.6))
        u1 = expo_in_out(ramp(t, *T_LINE1)); u2 = expo_in_out(ramp(t, *T_LINE2))
        ycl = yy(-69); y_end = lerp(yy(Y0), ycl, u1) if u2 == 0 else lerp(ycl, yy(Y1), u2)
        cr.set_source_rgba(*OCH, fa); cr.set_line_width(26); cr.set_line_cap(cairo.LINE_CAP_BUTT)
        cr.move_to(X, yy(Y0)); cr.line_to(X, lerp(yy(Y0), ycl, u1)); cr.stroke()
        if u2 > 0: cr.set_source_rgba(*LAP, fa); cr.move_to(X, ycl); cr.line_to(X, lerp(ycl, yy(Y1), u2)); cr.stroke()
        cr.set_source_rgba(*BLKC, fa); cr.set_line_width(3)
        for c in range(-26, 20):                                # 100년 눈금
            y = yy(c * 100)
            if y >= min(y_end, yy(Y0)) - 1: cr.move_to(X - (22 if c % 5 == 0 else 14), y); cr.line_to(X - 13, y); cr.stroke()
        pyramid(cr, X + 150, yy(Y0) + 20, 1.0, fa)
        txt(cr, '~2560 BC', X + 300, yy(Y0) - 70, 44, BLKC, fa, anchor='l'); txt(cr, 'Great Pyramid', X + 300, yy(Y0) - 24, 36, TER, fa, anchor='l', maxw=420); txt(cr, '대피라미드', X + 300, yy(Y0) + 18, 36, TER, fa, anchor='l', maxw=420)
        if t >= T_CLEO:
            b = ramp(t, T_CLEO, T_CLEO + 0.4) * fa; queen(cr, X + 150, ycl - 10, 1.25 * back_out(ramp(t, T_CLEO, T_CLEO + 0.4), 1.8), b)
            txt(cr, '69 BC', X + 300, ycl - 50, 44, BLKC, b, anchor='l'); txt(cr, 'Cleopatra born', X + 300, ycl - 4, 36, TER, b, anchor='l', maxw=420); txt(cr, '클레오파트라 출생', X + 300, ycl + 38, 36, TER, b, anchor='l', maxw=420)
        if t >= T_MOON:
            b = ramp(t, T_MOON, T_MOON + 0.4) * fa; moon(cr, X + 150, yy(Y1) + 30, 0.95 * back_out(ramp(t, T_MOON, T_MOON + 0.4), 1.8), b)
            txt(cr, '1969', X + 300, yy(Y1) - 20, 44, BLKC, b, anchor='l'); txt(cr, 'Moon landing', X + 300, yy(Y1) + 26, 36, LAP, b, anchor='l', maxw=420); txt(cr, '달 착륙', X + 300, yy(Y1) + 68, 36, LAP, b, anchor='l', maxw=420)
        # 흐르는 햇수
        if T_LINE1[0] < t < T_LINE2[1] + 1.5:
            n = 2491 * u1 if u2 == 0 else 2038 * u2; col = OCH if u2 == 0 else LAP
            txt(cr, f'{n:,.0f} years · {n:,.0f}년', X + 140, (yy(Y0) + ycl) / 2 + 20 if u2 == 0 else (ycl + yy(Y1)) / 2 + 20, 44, col, fa * ramp(t, T_LINE1[0], T_LINE1[0] + 0.3), anchor='l')
    # 막대 비교
    if t >= T_BARS:
        b = ramp(t, T_BARS + 0.2, T_BARS + 0.6)
        for i, (n, col, en, ko) in enumerate(((2491, OCH, 'Pyramid → Cleopatra', '피라미드 → 클레오파트라'), (2038, LAP, 'Cleopatra → Moon', '클레오파트라 → 달'))):
            w = 820 * n / 2491 * expo_out(ramp(t, T_BARS + 0.3 + 0.5 * i, T_BARS + 1.3 + 0.5 * i)); y = 760 + i * 330
            cr.set_source_rgba(*col, b); cr.rectangle(130, y, w, 110); cr.fill(); cr.set_source_rgba(*BLKC, b); cr.set_line_width(5); cr.rectangle(130, y, w, 110); cr.stroke()
            txt(cr, en, 130, y - 52, 42, BLKC, b, anchor='l'); txt(cr, ko, 130, y - 12, 36, TER, b, anchor='l')
            txt(cr, f'{n:,} yrs · {n:,}년', 150, y + 72, 48, (0.98, 0.95, 0.88), b * ramp(t, T_BARS + 1.0 + 0.5 * i, T_BARS + 1.3 + 0.5 * i), anchor='l')
    return over(img, s)

def sound(path):
    m = S.Mix(EP['DUR'], 69); hij = [146.8, 155.6, 185.0, 196.0, 220.0, 233.1, 261.6, 293.7]
    m.put('amb', 0, S.drone([73.4, 110.0], EP['t_end'] + 1, 0.12, 'saw', vib=0.002))
    beat = 0.42; t = 0.2
    while t < EP['t_coda'] - 0.2:                              # 둠–텍–텍 둠–텍
        k = round((t - 0.2) / beat) % 8
        if k in (0, 3, 6): m.put('fx', t, S.frame_drum(0.55, True, seed=int(t * 10)))
        if k in (2, 5, 7): m.put('fx', t, S.frame_drum(0.25, False, seed=int(t * 10)))
        t += beat
    mel = [0, 2, 3, 4, 3, 2, 1, 0]
    for i, tt in enumerate([0.5, 0.9, 1.3, 1.7, 2.3, 2.7, 3.1]): m.put('mus', tt, S.pluck(hij[mel[i % 8]] * 2, 1.2, 0.5, 0.45))
    for i in range(8): m.put('mus', T_LINE1[0] + i * 0.55, S.pluck(hij[i] * 2, 0.9, 0.35, 0.5))
    m.put('fx', T_CLEO, S.bell(587.3, 2.5, 0.35)); m.put('mus', T_CLEO, S.pluck(293.7, 2.0, 0.6, 0.4))
    for i in range(7): m.put('mus', T_LINE2[0] + i * 0.5, S.pluck(hij[7 - i] * 2, 0.9, 0.35, 0.5))
    m.put('fx', T_MOON, S.ping(1175, 0.4, 2.2)); m.put('fx', T_MOON, S.kick(50, 0.5))
    m.put('fx', T_BARS + 0.3, S.swoosh(0.9, 0.25, 300, 4000)); m.put('fx', T_BARS + 0.8, S.swoosh(0.9, 0.25, 400, 5000))
    tc = EP['t_coda']; m.put('amb', tc, S.drone([146.8, 220.0, 293.7], EP['t_end'] - tc, 0.2, 'saw', vib=0.004))
    for i in range(3): m.put('mus', tc + 0.8 + i * STEP, S.pluck(hij[[0, 4, 7][i]] * 2, 2.5, 0.5, 0.4))
    m.put('mus', EP['t_end'] + 0.2, S.pluck(293.7, 2.5, 0.5, 0.4)); m.put('fx', EP['t_end'] + 0.2, S.frame_drum(0.6, True, 1))
    m.write(path, rev_mus=1.8, wet_mus=0.3)

EP = finalize(dict(t_coda=T_CODA, draw=draw, sound=sound, end_icon='scroll', grain=0.005,
    title_en_card='CLEOPATRA & THE MOON', title_ko_card='클레오파트라와 달',
    pal=dict(hi=TER, endbg=(0.93, 0.86, 0.68)),
    card_style=dict(box='band', bg=BLKC, ink=(0.96, 0.9, 0.74), hi=GOLD, y=150, fe=SERIF, fk=BLK),
    cards=[(0.3, 3.4, ['Was Cleopatra closer to', 'the *pyramids* or the *Moon landing*?'], ['클레오파트라는 *피라미드*와 *달 착륙* 중', '어느 쪽에 더 가까울까?']),
           (3.8, 8.0, ['The Great Pyramid', 'was finished ~2560 BC.'], ['대피라미드는', '기원전 2560년쯤 완공']),
           (8.3, 13.0, ['Cleopatra was born', '*2,491 years* later.'], ['클레오파트라는', '그로부터 *2,491년 뒤* 태어났다']),
           (13.3, 14.9, ['The Moon: *2,038 years* after her.'], ['달 착륙은 그녀 출생 *2,038년 뒤*']),
           (15.1, 19.4, ['She is *closer to us*', 'than to the pyramid builders.'], ['그녀는 피라미드를 쌓은 사람들보다', '*우리에게 더 가깝다*']),
           (19.6, 23.8, ['To her, the pyramids', 'were *already ancient ruins*.'], ['그녀에게도 피라미드는', '*이미 오래된 유적*이었다'])],
    coda=[('What we call ancient', '우리가 고대라 부르는 것도'), ('was once somebody’s ordinary today.', '한때는 누군가의 평범한 오늘이었다'), ('Live today as if it will be remembered.', '오늘을 기억될 하루처럼 살자')],
    coda_style=dict(dim=0.7, blur=10, tint=(0.12, 0.08, 0.04), ink=(0.97, 0.91, 0.75), hi=GOLD, fe=SERIF),
    sources=['Great Pyramid ~2560 BC (estimates 2580–2510 BC); Cleopatra VII 69–30 BC; Apollo 11, 1969.'],
    yt=dict(title_en='Cleopatra Lived Closer to the Moon Landing Than to the Pyramids #Shorts', title_ko='클레오파트라는 피라미드보다 달 착륙에 더 가깝다')))

if __name__ == '__main__': main(EP)
