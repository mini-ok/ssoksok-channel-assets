"""〈오후 3시의 커피〉 세로 쇼츠(1080×1920 디자인 픽셀, 30초). 굵은 글자·강한 대비의 키네틱 그래픽.

사실과 출처
- 카페인 혈중 반감기: 건강한 성인 평균 약 5시간, 범위 1.5~9.5시간.
  Institute of Medicine, "Caffeine for the Sustainment of Mental Task Performance" (NCBI Bookshelf NBK223808)
- 취침 6시간 전 카페인 400 mg → 객관 측정 총수면시간이 1시간 넘게 감소, 본인은 잘 알아채지 못함(건강한 성인 12명).
  Drake C, Roehrs T, Shambroom J, Roth T. J Clin Sleep Med 2013;9(11):1195-1200 (PMC3805807), AASM 보도자료(2013-11-14)
- 권고: 취침 최소 6시간 전부터 많은 카페인을 피한다(같은 논문 결론).
- 화면 숫자: 오후 3시 100% → 5시간 뒤 50% → 25% → 12.5% (반감기 5시간으로 계산한 값, 개인차 있음).

사용: MG_SCALE=0.5 python3 short.py still out.png t1 t2 ...   |   python3 short.py one out.png t
      MG_SCALE=1 MG_FPS=30 python3 short.py frames outdir a b
모든 프레임은 t의 순수 함수(난수 씨앗 고정).
"""
import os, sys, math
import numpy as np, cv2, cairo
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.join(HERE, '..', 'jamo28'))
import mg
SC = mg.SC
mg.W, mg.H = int(round(1080 * SC)), int(round(1920 * SC))
from mg import clamp, ramp, smooth, expo_out, expo_in_out, back_out, spring, lerp, Canvas
W, H, FPS = mg.W, mg.H, mg.FPS
DW, DH = 1080, 1920

NIGHT = (0.05, 0.045, 0.06); CREAM = (0.965, 0.93, 0.86); AMB = (1.0, 0.60, 0.10); HOT = (1.0, 0.30, 0.16)
INK = (0.085, 0.08, 0.075); SLEEP = (0.30, 0.37, 0.68)
BLK = 'Noto Sans CJK KR Black'; SANS = 'Noto Sans CJK KR'; SERIF = 'Noto Serif CJK KR'
def mix(a, b, u): return tuple(lerp(x, y, u) for x, y in zip(a, b))

# ------------------------------------------------ 시간표(초)
T_FILL = (0.15, 0.9)
T_S2 = 3.4
SWEEPS = [(4.6, 6.4, 0, 5), (8.4, 10.0, 5, 10), (13.0, 14.6, 10, 15)]     # (시작, 끝, 3시부터 몇 시간 → 몇 시간)
T_S4 = 15.6; T_LINE = 16.0; T_BAR = 16.7; T_CUT = 18.0; T_NOTICE = 19.4
T_S5 = 21.2; T_ARC = (21.8, 22.8)
T_END = 27.0; DUR = 30.0
BEATS = [0.9, 6.4, 10.0, 14.6, T_CUT + 0.05, T_ARC[1]]

def hours(t):
    h = 0.0
    for a, b, h0, h1 in SWEEPS:
        if t >= a: h = lerp(h0, h1, expo_in_out(ramp(t, a, b)))
    return h
def night(h): return smooth(ramp(h, 1.5, 6.5)) * (1 - 0.45 * smooth(ramp(h, 13.0, 15.0)))
def ang(H): return (H % 12) / 12 * 2 * math.pi - math.pi / 2

def seg_h(f):
    """원(반지름 1)에서 아래쪽 넓이 비율 f가 되는 물 높이(0..2)."""
    lo, hi = 0.0, 2.0
    for _ in range(40):
        m = (lo + hi) / 2
        a = (math.acos(1 - m) - (1 - m) * math.sqrt(max(0, 2 * m - m * m))) / math.pi
        lo, hi = (m, hi) if a < f else (lo, m)
    return (lo + hi) / 2

# ------------------------------------------------ 글자
def txt(cr, s, x, y, size, col, a=1.0, fam=SANS, bold=False, anchor='c', stroke=None, sw=10):
    if a <= 0: return 0
    cr.select_font_face(fam, cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD if bold else cairo.FONT_WEIGHT_NORMAL); cr.set_font_size(size)
    w = cr.text_extents(s).x_advance
    x0 = x - {'l': 0, 'c': w / 2, 'r': w}[anchor]
    if stroke:
        cr.move_to(x0, y); cr.text_path(s); cr.set_source_rgba(*stroke, a); cr.set_line_width(sw); cr.set_line_join(cairo.LINE_JOIN_ROUND); cr.stroke()
    cr.move_to(x0, y); cr.set_source_rgba(*col, a); cr.show_text(s); cr.new_path()
    return w

def runs(cr, s, cx, y, size, col, hi, a, fam=BLK, maxw=980):
    """'*강조*' 표시가 있는 한 줄을 가운데 정렬. 너비가 넘치면 줄인다."""
    parts = s.split('*')
    cr.select_font_face(fam, 0, 0); cr.set_font_size(size)
    w = sum(cr.text_extents(p).x_advance for p in parts)
    if w > maxw: size *= maxw / w; cr.set_font_size(size); w = maxw
    x = cx - w / 2
    for i, p in enumerate(parts):
        cr.move_to(x, y); cr.set_source_rgba(*(hi if i % 2 else col), a); cr.show_text(p); x += cr.text_extents(p).x_advance
    cr.new_path()

def card(cr, t, t0, t1, en, ko, y=215, col=CREAM, hi=AMB, se=64, sk=58):
    """위쪽 글자 카드: 영어 위·한글 아래, 크기 비슷. 쾅 하고 들어와 짧게 빠진다."""
    a = ramp(t, t0, t0 + 0.18) * (1 - ramp(t, t1 - 0.2, t1))
    if a <= 0: return
    k = 1 + 0.16 * (1 - expo_out(ramp(t, t0, t0 + 0.35)))
    cr.save(); cr.translate(DW / 2, y + 120); cr.scale(k, k); cr.translate(-DW / 2, -(y + 120))
    yy = y
    for ln in en: runs(cr, ln, DW / 2, yy, se, col, hi, a); yy += se * 1.2
    yy += 12
    for ln in ko: runs(cr, ln, DW / 2, yy, sk, col, hi, a * 0.96, fam=SANS if False else BLK); yy += sk * 1.25
    cr.restore()

# ------------------------------------------------ 바탕
_rs = np.random.default_rng(315)
STARS = [(_rs.uniform(30, 1050), _rs.uniform(30, 1890), _rs.uniform(1.2, 3.2), _rs.uniform(0, 6.28)) for _ in range(90)]
def backdrop(cr, n, t):
    g = cairo.LinearGradient(0, 0, 0, DH)
    g.add_color_stop_rgb(0, *mix((0.26, 0.12, 0.04), (0.035, 0.05, 0.14), n))
    g.add_color_stop_rgb(1, *mix((0.07, 0.04, 0.03), (0.02, 0.02, 0.045), n))
    cr.set_source(g); cr.paint()
    for x, y, r, ph in STARS:
        a = n * (0.35 + 0.35 * math.sin(t * 1.7 + ph))
        if a > 0.02: cr.set_source_rgba(*CREAM, a); cr.arc(x, y, r, 0, 6.2832); cr.fill()

def bands(cr, t, t0, c1=HOT, c2=AMB):
    """비스듬한 띠 두 장이 화면을 덮으며 지나간다(장면 넘김)."""
    for k, c in enumerate((c1, c2)):
        u = expo_in_out(ramp(t, t0 - 0.32 + 0.07 * k, t0 + 0.32 + 0.07 * k))
        if u <= 0 or u >= 1: continue
        x = lerp(-2150, 1420, u)
        cr.set_source_rgb(*c); cr.move_to(x + 260, 0); cr.line_to(x + 1960, 0); cr.line_to(x + 1700, DH); cr.line_to(x, DH); cr.close_path(); cr.fill()

# ------------------------------------------------ 시계 고리 + 카페인 원
C = (540, 1010); R = 352; RL = 246
def ring(cr, a, col=CREAM, nums=True, R=R):
    cr.set_source_rgba(*col, 0.22 * a); cr.set_line_width(5); cr.arc(*C, R, 0, 6.2832); cr.stroke()
    for i in range(60):
        th = i / 60 * 6.2832; big = i % 5 == 0
        r0 = R - (26 if big else 12)
        cr.set_source_rgba(*col, (0.75 if big else 0.28) * a); cr.set_line_width(5 if big else 2.5)
        cr.move_to(C[0] + r0 * math.cos(th), C[1] + r0 * math.sin(th)); cr.line_to(C[0] + (R - 4) * math.cos(th), C[1] + (R - 4) * math.sin(th)); cr.stroke()
    if nums:
        for Hh in (12, 3, 6, 9):
            th = ang(Hh); txt(cr, str(Hh), C[0] + (R + 44) * math.cos(th), C[1] + (R + 44) * math.sin(th) + 14, 38, col, 0.5 * a, fam=BLK)

def liquid(cr, cx, cy, r, f, t, a=1.0, wave=1.0):
    """넓이 비율 f만큼 찬 원. 윗면은 출렁인다."""
    cr.save(); cr.arc(cx, cy, r, 0, 6.2832); cr.clip()
    cr.set_source_rgba(0.10, 0.085, 0.09, 0.92 * a); cr.paint()
    if f > 0.001:
        top = cy + r - seg_h(clamp(f, 0, 1)) * r
        amp = r * 0.035 * wave
        cr.move_to(cx - r, cy + r)
        for i in range(41):
            x = cx - r + 2 * r * i / 40
            cr.line_to(x, top + amp * math.sin(i * 0.42 + t * 3.1) + amp * 0.5 * math.sin(i * 0.9 - t * 4.3))
        cr.line_to(cx + r, cy + r); cr.close_path()
        g = cairo.LinearGradient(0, top - amp, 0, cy + r)
        g.add_color_stop_rgba(0, 1.0, 0.72, 0.20, a); g.add_color_stop_rgba(1, 0.86, 0.36, 0.05, a)
        cr.set_source(g); cr.fill()
    cr.restore()
    cr.set_source_rgba(*CREAM, 0.9 * a); cr.set_line_width(max(3, r * 0.028)); cr.arc(cx, cy, r, 0, 6.2832); cr.stroke()

def pct_str(f): p = f * 100; return f'{p:.1f}%' if p < 20 and abs(p - round(p)) > 0.05 else f'{p:.0f}%'
def clock_label(h):
    Hh = int(round(15 + h)) % 24
    en = f'{(Hh - 1) % 12 + 1} {"AM" if Hh < 12 else "PM"}'
    pre = '새벽' if Hh < 5 else '아침' if Hh < 12 else '오후' if Hh < 18 else '저녁' if Hh < 21 else '밤'
    return en, f'{pre} {(Hh - 1) % 12 + 1}시'

MARKS = [(0, 3.4), (5, 6.4), (10, 10.0), (15, 14.6)]       # (시간, 도착 시각)
def hero(cr, t):
    h = hours(t); f = 0.5 ** (h / 5)
    a_ring = ramp(t, T_S2, T_S2 + 0.5)
    fill = expo_out(ramp(t, *T_FILL))
    pop = 1.0
    for bt in (0.9, 6.4, 10.0, 14.6): pop += 0.045 * math.exp(-max(0, t - bt) * 9) * (t >= bt)
    # 배경의 큰 숫자
    ga = ramp(t, T_S2 + 0.3, T_S2 + 1.0)
    if ga > 0:
        cr.save(); cr.translate(540, 1100); cr.rotate(-0.21); txt(cr, '5h', 0, 300, 1100, CREAM, 0.045 * ga, fam=BLK); cr.restore()
    ring(cr, a_ring)
    # 지나온 구간: 고리 위의 호
    if a_ring > 0 and h > 0:
        for a, b, h0, h1 in SWEEPS:
            if h <= h0: continue
            cur = h < h1 or (h == h1 and t < b + 0.01)
            cr.set_source_rgba(*AMB, (0.95 if h < h1 + 1e-6 and t <= b + 0.6 else 0.38) * a_ring); cr.set_line_width(16); cr.set_line_cap(cairo.LINE_CAP_ROUND)
            cr.arc(*C, R, ang(15 + h0), ang(15 + h0) + (min(h, h1) - h0) / 12 * 6.2832); cr.stroke()
    for hm, tm in MARKS:
        if t >= tm and a_ring > 0:
            th = ang(15 + hm); k = back_out(ramp(t, tm, tm + 0.3), 2.5)
            cr.set_source_rgba(*CREAM, a_ring); cr.arc(C[0] + R * math.cos(th), C[1] + R * math.sin(th), 13 * k, 0, 6.2832); cr.fill()
            u = ramp(t, tm, tm + 0.7)
            if 0 < u < 1 and hm:
                cr.set_source_rgba(*AMB, 0.7 * (1 - u)); cr.set_line_width(5); cr.arc(*C, RL + 30 + 150 * expo_out(u), 0, 6.2832); cr.stroke()
    if a_ring > 0:                                           # 지금 시각을 가리키는 점
        th = ang(15 + h)
        cr.set_source_rgba(*AMB, a_ring); cr.arc(C[0] + R * math.cos(th), C[1] + R * math.sin(th), 24, 0, 6.2832); cr.fill()
        cr.set_source_rgba(*NIGHT, a_ring); cr.arc(C[0] + R * math.cos(th), C[1] + R * math.sin(th), 9, 0, 6.2832); cr.fill()
    # 카페인 원
    cr.save(); cr.translate(*C); cr.scale(pop, pop); cr.translate(-C[0], -C[1])
    liquid(cr, C[0], C[1], RL, f * fill, t)
    if t >= 0.5:
        txt(cr, pct_str(f), C[0], C[1] + 52, 150, CREAM, ramp(t, 0.5, 0.8), fam=BLK, stroke=NIGHT, sw=16)
    cr.restore()
    # 해·달
    n = night(h)
    if a_ring > 0:
        sx, sy = 905, 560
        cr.set_source_rgba(*AMB, (1 - n) * a_ring * 0.95); cr.arc(sx, sy, 34, 0, 6.2832); cr.fill()
        if n > 0.02:
            cr.push_group(); cr.set_source_rgba(*CREAM, 1); cr.arc(sx, sy, 34, 0, 6.2832); cr.fill()
            cr.set_operator(cairo.OPERATOR_CLEAR); cr.arc(sx + 18, sy - 10, 29, 0, 6.2832); cr.fill(); cr.set_operator(cairo.OPERATOR_OVER)
            cr.pop_group_to_source(); cr.paint_with_alpha(n * a_ring)
    # 시각 이름표
    a_lab = ramp(t, 0.9, 1.2)
    if a_lab > 0:
        en, ko = clock_label(h)
        txt(cr, en, 540, 1535, 104, CREAM, a_lab, fam=BLK)
        txt(cr, ko, 540, 1632, 84, AMB, a_lab, fam=BLK)
    # 아래 기록 칩
    for i, (hm, tm) in enumerate(MARKS):
        if t < tm: continue
        k = back_out(ramp(t, tm, tm + 0.35), 1.8); x = 165 + i * 250; y = 1752
        fm = 0.5 ** (hm / 5)
        cr.save(); cr.translate(x, y); cr.scale(k, k); cr.translate(-x, -y)
        liquid(cr, x, y, 48, fm, t, wave=0.6)
        cr.restore()
        txt(cr, pct_str(fm), x, y + 96, 36, CREAM, k, fam=BLK)
        txt(cr, clock_label(hm)[0], x, y - 66, 28, CREAM, 0.7 * k, fam=BLK)

# ------------------------------------------------ 근거: 잠이 1시간 넘게 줄었다
def rrect(cr, x, y, w, h, r):
    r = min(r, w / 2, h / 2); cr.new_sub_path()
    cr.arc(x + w - r, y + r, r, -math.pi / 2, 0); cr.arc(x + w - r, y + h - r, r, 0, math.pi / 2)
    cr.arc(x + r, y + h - r, r, math.pi / 2, math.pi); cr.arc(x + r, y + r, r, math.pi, 1.5 * math.pi); cr.close_path()

def evidence(cr, t):
    # 카페인 ─ 6시간 ─ 취침
    u = expo_out(ramp(t, T_LINE, T_LINE + 0.6)); y = 700
    if u > 0:
        x1 = lerp(200, 880, u)
        cr.set_source_rgba(*CREAM, 0.55); cr.set_line_width(6); cr.set_dash([18, 14]); cr.move_to(200, y); cr.line_to(x1, y); cr.stroke(); cr.set_dash([])
        cr.set_source_rgba(*AMB, 1); cr.arc(200, y, 30, 0, 6.2832); cr.fill()
        txt(cr, 'Caffeine', 200, y - 112, 44, AMB, u, fam=BLK); txt(cr, '카페인', 200, y - 60, 42, AMB, u, fam=BLK)
        b = ramp(t, T_LINE + 0.45, T_LINE + 0.7)
        if b > 0:
            cr.set_source_rgba(*CREAM, b); cr.arc(880, y, 30 * back_out(b, 2.5), 0, 6.2832); cr.fill()
            txt(cr, 'Bedtime', 880, y - 112, 44, CREAM, b, fam=BLK); txt(cr, '취침', 880, y - 60, 42, CREAM, b, fam=BLK)
            txt(cr, '6 h', 540, y - 30, 76, CREAM, b, fam=BLK)
            txt(cr, '6시간 전', 540, y + 70, 42, CREAM, 0.8 * b, fam=BLK)
    # 잠 막대
    g = expo_out(ramp(t, T_BAR, T_BAR + 0.7)); bx, by, bw, bh = 120, 900, 840, 190; cw = 150
    if g > 0:
        cut = t >= T_CUT
        wmain = (bw - cw if cut else bw) * g
        cr.set_source_rgba(*SLEEP, 1); rrect(cr, bx, by, wmain, bh, 34); cr.fill()
        txt(cr, 'Sleep', bx + 44, by + 88, 58, CREAM, g, fam=BLK, anchor='l'); txt(cr, '잠', bx + 44, by + 152, 54, CREAM, 0.9 * g, fam=BLK, anchor='l')
        for i in range(14):                                       # 달·별 무늬 대신 얇은 눈금
            x = bx + 300 + i * 38
            if x < bx + wmain - 30: cr.set_source_rgba(*CREAM, 0.16); cr.set_line_width(4); cr.move_to(x, by + 40); cr.line_to(x, by + bh - 40); cr.stroke()
        if cut:
            v = t - T_CUT
            cr.set_source_rgba(*HOT, 0.75); cr.set_line_width(4); cr.set_dash([12, 10]); rrect(cr, bx + bw - cw + 8, by, cw - 8, bh, 30); cr.stroke(); cr.set_dash([])
            dx = 60 * v; dy = 1500 * v * v; rot = 1.1 * v
            if dy < 1100:
                cr.save(); cr.translate(bx + bw - cw / 2 + dx, by + bh / 2 + dy); cr.rotate(rot)
                cr.set_source_rgba(*HOT, 1); rrect(cr, -cw / 2 + 8, -bh / 2, cw - 8, bh, 30); cr.fill(); cr.restore()
            k = 1 + 0.5 * (1 - expo_out(ramp(v, 0.08, 0.45))); a = ramp(v, 0.08, 0.2)
            cr.save(); cr.translate(540, 1370); cr.scale(k, k)
            txt(cr, '−1h+', 0, 0, 250, HOT, a, fam=BLK)
            cr.restore()
            a2 = ramp(v, 0.5, 0.8)
            txt(cr, 'of sleep, gone', 540, 1468, 54, CREAM, a2, fam=BLK); txt(cr, '잠이 1시간 넘게 사라졌다', 540, 1540, 50, CREAM, 0.92 * a2, fam=BLK)
    s = ramp(t, T_BAR + 0.5, T_BAR + 1.0)
    txt(cr, '400 mg caffeine · 12 healthy adults', 540, 1668, 30, CREAM, 0.7 * s)
    txt(cr, '카페인 400mg · 건강한 성인 12명', 540, 1712, 30, CREAM, 0.7 * s)
    txt(cr, 'Drake et al., J Clin Sleep Med, 2013', 540, 1756, 28, CREAM, 0.55 * s)

# ------------------------------------------------ 결론: 6시간 선
def takeaway(cr, t):
    a = ramp(t, T_S5 + 0.1, T_S5 + 0.5)
    ring(cr, a, R=330)
    u = expo_in_out(ramp(t, *T_ARC)); a0 = ang(17); R2 = 330
    if u > 0:
        cr.set_source_rgba(*HOT, 0.95); cr.set_line_width(44); cr.set_line_cap(cairo.LINE_CAP_BUTT)
        cr.arc(*C, R2, a0, a0 + u * math.pi); cr.stroke()
    tt = t - T_ARC[1] - 0.3
    if tt > 0:                                                  # 여섯 시간이 흐르는 점(읽는 동안 화면이 멈춰 있지 않게)
        u2 = (tt % 1.7) / 1.7; th = a0 + smooth(u2) * math.pi
        cr.set_source_rgba(*CREAM, math.sin(math.pi * u2) ** 0.6); cr.arc(C[0] + R2 * math.cos(th), C[1] + R2 * math.sin(th), 13, 0, 6.2832); cr.fill()
    for Hh, tm, en, ko, col in ((17, T_ARC[0], 'Last cup 5 PM', '마지막 잔 · 오후 5시', AMB), (23, T_ARC[1], 'Bed 11 PM', '취침 · 밤 11시', CREAM)):
        k = back_out(ramp(t, tm, tm + 0.3), 2.2)
        if k <= 0: continue
        th = ang(Hh); x, y = C[0] + R2 * math.cos(th), C[1] + R2 * math.sin(th)
        cr.set_source_rgba(*col, 1); cr.arc(x, y, 30 * k, 0, 6.2832); cr.fill()
        cr.set_source_rgba(*NIGHT, 1); cr.arc(x, y, 11 * k, 0, 6.2832); cr.fill()
        lx, ly = C[0] + (R2 + 30) * math.cos(th), C[1] + (R2 + 118) * math.sin(th)
        lx = clamp(lx + (70 if math.cos(th) > 0 else -70), 240, 840)
        txt(cr, en, lx, ly, 44, col, min(1, k), fam=BLK, stroke=NIGHT, sw=10); txt(cr, ko, lx, ly + 52, 40, col, min(1, k), fam=BLK, stroke=NIGHT, sw=10)
    b = ramp(t, T_ARC[0] + 0.3, T_ARC[0] + 0.6); kk = 1 + 0.3 * (1 - expo_out(ramp(t, T_ARC[0] + 0.3, T_ARC[0] + 0.7)))
    cr.save(); cr.translate(C[0], C[1] + 40); cr.scale(kk, kk)
    txt(cr, '6h', 0, 30, 230, CREAM, b, fam=BLK)
    cr.restore()
    txt(cr, 'no caffeine', C[0], C[1] + 130, 40, HOT, b, fam=BLK); txt(cr, '카페인 없이', C[0], C[1] + 180, 38, HOT, b, fam=BLK)
    f = ramp(t, T_ARC[1] + 0.6, T_ARC[1] + 1.1)
    g = ramp(t, T_ARC[1] + 0.1, T_ARC[1] + 0.4)
    runs(cr, 'Bed at *11 PM*? Last cup by *5 PM*.', 540, 1560, 52, CREAM, AMB, g); runs(cr, '*밤 11시*에 잔다면, 커피는 *오후 5시*까지', 540, 1630, 48, CREAM, AMB, g)
    txt(cr, 'Half-life averages about 5 hours (1.5–9.5 h, varies by person).', 540, 1730, 29, CREAM, 0.7 * f)
    txt(cr, '반감기는 평균 약 5시간, 사람에 따라 1.5~9.5시간.', 540, 1774, 29, CREAM, 0.7 * f)

# ------------------------------------------------ 끝 화면
_seal = {}
def seal_img():
    if not _seal:
        sz = int(round(120 * SC))
        s = np.load(os.path.join(HERE, '..', '_shared', 'seal_baimun3.npy')).astype(np.float32)
        _seal['v'] = (cv2.resize(s, (sz, sz), interpolation=cv2.INTER_AREA)[..., [2, 1, 0, 3]], sz)
    return _seal['v']

def ending(cr, t):
    cr.set_source_rgb(*CREAM); cr.paint()
    a = ramp(t, T_END + 0.15, T_END + 0.5); k = 1 + 0.12 * (1 - expo_out(ramp(t, T_END + 0.15, T_END + 0.6)))
    liquid(cr, 540, 600, 96, 0.5, t, a)
    cr.set_source_rgba(*INK, a); cr.set_line_width(5); cr.arc(540, 600, 96, 0, 6.2832); cr.stroke()
    cr.save(); cr.translate(540, 840); cr.scale(k, k)
    txt(cr, 'THE 3 PM COFFEE', 0, 0, 92, INK, a, fam=BLK); txt(cr, '오후 3시의 커피', 0, 104, 84, INK, a, fam=BLK)
    cr.restore()
    b = ramp(t, T_END + 1.0, T_END + 1.5)
    txt(cr, 'Created & Coded by L.S.M.', 540, 1330, 36, INK, 0.9 * b, fam=SERIF); txt(cr, '허상공방 虛像工房 Project', 540, 1384, 36, INK, 0.9 * b, fam=SERIF)
    txt(cr, 'Sources: Institute of Medicine (NCBI Bookshelf NBK223808)', 540, 1700, 26, INK, 0.6 * b)
    txt(cr, 'Drake et al., J Clin Sleep Med, 2013', 540, 1740, 26, INK, 0.6 * b)

def stamp_seal(img, t):
    if t < T_END + 0.7: return img
    s, sz = seal_img(); a1 = smooth(ramp(t, T_END + 0.7, T_END + 0.9))
    xs, ys = int(round(540 * SC)) - sz // 2, int(round(1140 * SC))
    red = np.clip((s[..., 2:3] - s[..., 1:2]) * 4, 0, 1); al = s[..., 3:4] * a1 * red
    sub = img[ys:ys + sz, xs:xs + sz]; img[ys:ys + sz, xs:xs + sz] = sub * (1 - al + al * s[..., :3])
    return img

# ------------------------------------------------ 장면
def scene(t):
    cv = Canvas(); cr = cv.begin(NIGHT)
    sh = 0.0
    for bt in BEATS:
        if bt <= t < bt + 0.3: sh = max(sh, math.exp(-(t - bt) * 14))
    cr.save(); cr.translate(9 * sh * math.sin(t * 173), 12 * sh * math.cos(t * 151))
    if t < T_S4:
        h = hours(t); backdrop(cr, night(h), t); hero(cr, t)
        card(cr, t, 0.55, T_S2, ['Half of your *3 PM coffee*', 'is still in you at *8 PM*.'], ['*오후 3시* 커피의 절반은', '*저녁 8시*에도 몸에 남아 있다'])
        card(cr, t, T_S2 + 0.1, 7.9, ["Caffeine's half-life:", '*about 5 hours*'], ['카페인 반감기', '*약 5시간*'], se=70, sk=64)
        card(cr, t, 8.0, 10.3, ['Every 5 hours,', 'it only *halves*.'], ['5시간이 지나도', '*절반*만 사라진다'], se=70, sk=64)
        card(cr, t, 10.4, 12.9, ['*1 AM*: a quarter', 'is still on duty.'], ['*새벽 1시*에도', '4분의 1이 남아 있다'], se=70, sk=64)
        card(cr, t, 13.0, T_S4 + 0.05, ['*6 AM*: 12.5%', 'is still there.'], ['*아침 6시*에도', '12.5%가 남는다'], se=70, sk=64)
    elif t < T_S5:
        backdrop(cr, 1.0, t); evidence(cr, t)
        card(cr, t, T_S4 + 0.15, T_NOTICE - 0.05, ['Caffeine *6 hours* before bed', 'cut sleep by *over an hour*.'], ['잠들기 *6시간 전* 카페인에도', '잠이 *1시간 넘게* 줄었다'], hi=HOT, se=60, sk=56)
        card(cr, t, T_NOTICE, T_S5 + 0.05, ['And they *didn\'t even notice*.'], ['정작 본인은 *눈치채지 못했다*'], y=250, hi=HOT, se=62, sk=58)
    elif t < T_END:
        backdrop(cr, 0.8, t); takeaway(cr, t)
        card(cr, t, T_S5 + 0.2, T_END + 0.05, ['Last coffee: *6+ hours*', 'before bed.'], ['마지막 커피는', '잠들기 *6시간 전*까지'], hi=HOT, se=70, sk=64)
    else:
        ending(cr, t)
    cr.restore()
    for bt in BEATS:                                              # 박자마다 짧은 섬광
        if bt <= t < bt + 0.2: cr.set_source_rgba(*CREAM, 0.16 * math.exp(-(t - bt) * 22)); cr.paint()
    bands(cr, t, T_S4); bands(cr, t, T_S5, AMB, HOT); bands(cr, t, T_END, HOT, CREAM)
    return cv.array()

def render_frame(t, smp=3):
    img = mg.render(scene, t, samples=smp)
    img = stamp_seal(img, t)
    return mg.grain(img, t, amt=0.010)

if __name__ == '__main__':
    cmd = sys.argv[1]
    if cmd == 'still':
        out = sys.argv[2]; ims = []
        for tt in map(float, sys.argv[3:]):
            im = (render_frame(tt, 1) * 255).astype(np.uint8)
            cv2.putText(im, f'{tt:.1f}', (10, int(60 * SC)), 0, 1.6 * SC, (0, 255, 0), 2); ims.append(im)
        while len(ims) % 4: ims.append(np.zeros_like(ims[0]))
        cv2.imwrite(out, np.vstack([np.hstack(ims[i:i + 4]) for i in range(0, len(ims), 4)]))
    elif cmd == 'one':
        cv2.imwrite(sys.argv[2], (render_frame(float(sys.argv[3]), 2) * 255).astype(np.uint8))
    elif cmd == 'frames':
        od = sys.argv[2]; os.makedirs(od, exist_ok=True); a, b = int(sys.argv[3]), int(sys.argv[4])
        for k in range(a, b):
            fn = os.path.join(od, f'f{k:05d}.png')
            if not os.path.exists(fn): cv2.imwrite(fn, (render_frame(k / FPS) * 255 + 0.5).astype(np.uint8))
