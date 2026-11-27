"""〈달은 해마다 3.8cm씩 멀어진다〉 — 그림자극(등잔 빛이 비치는 한지 막, 검은 오린 인형, 구멍 뚫린 무늬, 막대), 소리는 핸드팬.
사실(NASA; Live Science; EarthSky): 달은 해마다 약 3.8 cm 멀어진다(손톱 자라는 속도쯤). 아폴로가 1969년 달에 둔 반사판에 레이저를 쏴 잰다.
평균 거리 384,400 km. 80년이면 약 3 m(계산: 3.8 × 80 = 304 cm).
"""
import math, numpy as np, cv2, cairo
from base import *
import sfx as S

T_NAIL = 3.8; T_LIFE = 8.8; T_LASER = 13.6; T_CODA = 18.8
INK = (0.06, 0.03, 0.02)
_r = np.random.default_rng(16)
def _screen():
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32) / SC
    d = np.hypot((xx - 540) / 820, (yy - 900) / 1150)
    glow = np.clip(1.15 - d, 0.15, 1.0)
    fib = cv2.GaussianBlur(_r.random((H, W)).astype(np.float32), (0, 0), sigmaX=0.7 * SC, sigmaY=5 * SC)
    base = np.stack([0.18 + 0.30 * glow, 0.42 + 0.40 * glow, 0.75 + 0.25 * glow], -1)          # BGR 주황빛
    return (base * (0.92 + 0.16 * fib[..., None])).astype(np.float32)
SCREEN = _screen()

def stick(cr, x, y, a, sway=0.0):
    cr.set_source_rgba(*INK, a * 0.85); cr.set_line_width(5); cr.move_to(x, y); cr.line_to(x + sway, DH + 20); cr.stroke()

def earth(cr, x, y, r, a):
    cr.set_source_rgba(*INK, a); cr.arc(x, y, r, 0, 6.283); cr.fill()
    cr.set_operator(cairo.OPERATOR_CLEAR)                       # 오려낸 무늬(대륙 자리)
    for ang, d, rr in ((0.6, 0.45, 0.22), (2.3, 0.5, 0.18), (3.9, 0.35, 0.2), (5.2, 0.55, 0.15)):
        cr.save(); cr.translate(x + math.cos(ang) * d * r, y + math.sin(ang) * d * r); cr.rotate(ang); cr.scale(1, 0.6); cr.arc(0, 0, rr * r, 0, 6.283); cr.restore(); cr.fill()
    for k in range(12): a_ = k * 6.283 / 12; cr.arc(x + math.cos(a_) * r * 0.82, y + math.sin(a_) * r * 0.82, r * 0.04, 0, 6.283); cr.fill()
    cr.set_operator(cairo.OPERATOR_OVER)

def moon(cr, x, y, r, a):
    cr.set_source_rgba(*INK, a); cr.arc(x, y, r, 0, 6.283); cr.fill()
    cr.set_operator(cairo.OPERATOR_CLEAR)
    for dx, dy, rr in ((-0.3, -0.2, 0.18), (0.25, 0.1, 0.22), (-0.1, 0.4, 0.12), (0.35, -0.4, 0.1)):
        cr.arc(x + dx * r, y + dy * r, rr * r, 0, 6.283); cr.fill()
    cr.set_operator(cairo.OPERATOR_OVER)

def hand(cr, x, y, s, a, flex=0.0):
    cr.save(); cr.translate(x, y); cr.scale(s, s); cr.set_source_rgba(*INK, a)
    cr.move_to(-60, 200); cr.curve_to(-70, 80, -80, 20, -40, -10); cr.line_to(40, -10); cr.curve_to(70, 30, 60, 120, 50, 200); cr.close_path(); cr.fill()
    for k, (fx, L) in enumerate(((-38, 120), (-12, 150), (14, 140), (38, 110))):
        cr.save(); cr.translate(fx, -5); cr.rotate((k - 1.5) * 0.05 + flex * 0.1); cr.rectangle(-11, -L, 22, L); cr.fill(); cr.arc(0, -L, 11, math.pi, 0); cr.fill(); cr.restore()
    cr.save(); cr.translate(-55, 60); cr.rotate(-0.9); cr.rectangle(-11, -90, 22, 90); cr.fill(); cr.arc(0, -90, 11, math.pi, 0); cr.fill(); cr.restore()
    cr.set_operator(cairo.OPERATOR_CLEAR); cr.save(); cr.translate(-12, -5); cr.rotate(-0.025 + flex * 0.1); cr.rectangle(-6, -146, 12, 22); cr.fill(); cr.restore()   # 손톱 자리
    cr.set_operator(cairo.OPERATOR_OVER); cr.restore()

def person(cr, x, y, s, a):
    cr.set_source_rgba(*INK, a); cr.arc(x, y - s * 0.88, s * 0.11, 0, 6.283); cr.fill()
    cr.move_to(x - s * 0.15, y - s * 0.74); cr.line_to(x + s * 0.15, y - s * 0.74); cr.line_to(x + s * 0.1, y - s * 0.32); cr.line_to(x + s * 0.12, y)
    cr.line_to(x + 0.02 * s, y); cr.line_to(x, y - s * 0.3); cr.line_to(x - 0.02 * s, y); cr.line_to(x - s * 0.12, y); cr.line_to(x - s * 0.1, y - s * 0.32); cr.close_path(); cr.fill()

def draw(t):
    s, cr = surf(); sw = 6 * math.sin(t * 0.9)
    a1 = 1 - ramp(t, T_NAIL - 0.4, T_NAIL)
    if a1 > 0:
        md = lerp(300, 380, smooth(ramp(t, 0.6, 3.6)))
        earth(cr, 540 + sw, 1260, 170, a1); stick(cr, 540 + sw, 1430, a1, -20)
        moon(cr, 540 + sw * 0.6, 1260 - md - 170, 55, a1); stick(cr, 600 + sw * 0.6, 1260 - md - 140, a1 * 0.7, 120)
    an = ramp(t, T_NAIL - 0.3, T_NAIL + 0.3) * (1 - ramp(t, T_LIFE - 0.4, T_LIFE))
    if an > 0:
        hand(cr, 360 + sw, 1180, 2.0, an, math.sin(t * 1.4) * 0.2); stick(cr, 360 + sw, 1560, an, 30)
        g = smooth(ramp(t, T_NAIL + 0.6, T_NAIL + 3.0))
        cr.set_source_rgba(*INK, an); x0 = 720; cr.rectangle(x0, 1500 - 380 * g, 70, 380 * g); cr.fill()      # 3.8 cm 막대(확대)
        for k in range(5): cr.rectangle(x0 + 70, 1500 - k * 95, 26, 5); cr.fill()
        stick(cr, x0 + 35, 1500, an, -10)
    al = ramp(t, T_LIFE - 0.3, T_LIFE + 0.3) * (1 - ramp(t, T_LASER - 0.4, T_LASER))
    if al > 0:
        u = smooth(ramp(t, T_LIFE + 0.4, T_LIFE + 3.8))
        person(cr, 300 + sw, 1500, 300 * lerp(0.6, 1.0, u), al); stick(cr, 300 + sw, 1500, al, 0)
        moon(cr, 720 + sw * 0.5, lerp(820, 560, u), 70, al); stick(cr, 740 + sw * 0.5, lerp(880, 620, u), al * 0.7, 60)
        cr.set_source_rgba(*INK, al); cr.set_line_width(5); cr.set_dash([16, 12]); cr.move_to(720, 900); cr.line_to(720, 900 + 300 * u); cr.stroke(); cr.set_dash([])
    aa = ramp(t, T_LASER - 0.3, T_LASER + 0.3) * (1 - ramp(t, T_CODA - 0.6, T_CODA))
    if aa > 0:
        cr.set_source_rgba(*INK, aa); cr.move_to(200, 1560); cr.line_to(360, 1560); cr.line_to(330, 1440); cr.line_to(230, 1440); cr.close_path(); cr.fill()   # 망원경 집
        cr.save(); cr.translate(280, 1430); cr.rotate(-0.95); cr.rectangle(-30, -200, 60, 220); cr.fill(); cr.restore()
        moon(cr, 820 + sw * 0.4, 700, 120, aa); stick(cr, 820 + sw * 0.4, 820, aa * 0.7, 40)
        cr.rectangle(800, 690, 34, 24); cr.set_operator(cairo.OPERATOR_CLEAR); cr.fill(); cr.set_operator(cairo.OPERATOR_OVER)   # 반사판 구멍
        u = (t - T_LASER - 0.8) % 1.6 / 1.6
        if t > T_LASER + 0.8:
            x0, y0, x1, y1 = 400, 1260, 815, 702; f = u * 2 if u < 0.5 else 2 - u * 2
            px, py = lerp(x0, x1, f), lerp(y0, y1, f)
            cr.set_operator(cairo.OPERATOR_CLEAR); cr.set_line_width(7); cr.move_to(lerp(x0, x1, max(0, f - 0.12)), lerp(y0, y1, max(0, f - 0.12))); cr.line_to(px, py); cr.stroke()
            cr.set_operator(cairo.OPERATOR_OVER)
    a = arr(s); a = cv2.GaussianBlur(a, (0, 0), 1.6 * SC)                   # 막에 닿은 그림자의 흐린 가장자리
    img = SCREEN * (1 - a[..., 3:4] * 0.93)
    s2, c2 = surf(); ink = (0.10, 0.05, 0.03)
    if an > 0:
        txt(c2, '3.8 cm / year', 760, 1640, 52, ink, an, fam=BLK); txt(c2, '1년에 3.8cm', 760, 1705, 44, ink, an, fam=BLK)
        txt(c2, '= fingernail growth · 손톱 자라는 속도', 540, 1800, 40, ink, an * ramp(t, T_NAIL + 3.0, T_NAIL + 3.5), fam=BLK)
    if al > 0:
        u = smooth(ramp(t, T_LIFE + 0.4, T_LIFE + 3.8))
        txt(c2, f'{3.8 * 80 * u / 100:.1f} m', 860, 1100, 80, ink, al * ramp(t, T_LIFE + 0.4, T_LIFE + 0.8), fam=BLK)
        txt(c2, 'in 80 years · 80년 동안', 860, 1180, 38, ink, al * ramp(t, T_LIFE + 0.4, T_LIFE + 0.8), fam=BLK)
    if aa > 0:
        txt(c2, 'mirrors left by Apollo, 1969', 540, 1700, 42, ink, aa * ramp(t, T_LASER + 1.0, T_LASER + 1.5), fam=BLK)
        txt(c2, '1969년 아폴로가 두고 온 반사판에 빛을 쏴 잰다', 540, 1765, 36, ink, aa * ramp(t, T_LASER + 1.0, T_LASER + 1.5), fam=BLK)
    return over(img, s2)

def sound(path):
    m = S.Mix(EP['DUR'], 151); tc = EP['t_coda']; b = 60 / 72
    scale = [146.8, 220.0, 233.1, 261.6, 293.7, 349.2, 392.0, 440.0]
    seq = [0, 4, 3, 5, 2, 4, 1, 3, 0, 4, 6, 5, 3, 4, 2, 1]
    t = 0.4; k = 0
    while t < tc - 0.4:
        m.put('mus', t, S.handpan(scale[seq[k % 16]], 2.4, 0.32 if k % 2 == 0 else 0.22))
        if k % 4 == 0: m.put('mus', t, S.handpan(scale[0] / 2, 3.0, 0.25))
        if k % 2: m.put('fx', t, S.shaker(0.1, 0.08, k))
        t += b / 2; k += 1
    for i in range(int((T_LASER - T_LIFE) / 0.5)): pass
    for t in np.arange(T_LASER + 0.8, T_CODA - 0.6, 1.6): m.put('fx', t, S.ping(1760, 0.18, 0.6)); m.put('fx', t + 0.8, S.ping(1318.5, 0.12, 0.6))
    m.put('amb', tc, S.drone([73.4, 110.0, 146.8], EP['t_end'] - tc, 0.15, 'sine'))
    for i, f in enumerate([440.0, 392.0, 293.7]): m.put('mus', tc + 0.8 + i * STEP, S.handpan(f, 3.0, 0.35))
    m.write(path, rev_mus=2.8, wet_mus=0.38)

EP = finalize(dict(t_coda=T_CODA, draw=draw, sound=sound, end_icon='moon', grain=0.0,
    title_en_card='THE MOON IS LEAVING', title_ko_card='달은 조금씩 멀어진다',
    pal=dict(hi=(0.55, 0.30, 0.10), endbg=(0.98, 0.90, 0.75)),
    card_style=dict(box=None, ink=(0.10, 0.05, 0.03), hi=(0.55, 0.18, 0.05), y=150, fe=BLK, fk=BLK),
    cards=[(0.3, 3.6, ['The Moon is slowly', '*moving away* from us.'], ['달은 조금씩', '*멀어지고* 있다']),
           (3.8, 8.6, ['About *3.8 cm* a year:', 'as fast as your *fingernails* grow.'], ['1년에 약 *3.8cm*,', '*손톱*이 자라는 속도']),
           (8.8, 13.4, ['Over a lifetime,', 'about *3 metres*.'], ['한평생이면', '약 *3m*']),
           (13.6, 18.6, ['We know because we bounce', 'lasers off *mirrors on the Moon*.'], ['*달에 둔 거울*에 레이저를 쏴서', '알아낸 사실'])],
    coda=[('Even the Moon is slowly leaving.', '달도 조금씩 떠나고 있다'), ('Nothing we love stays exactly where it is.', '사랑하는 것도 늘 제자리에 있지는 않다'), ('Hold it gently while it is near.', '가까이 있을 때 다정하게 붙잡자')],
    coda_style=dict(dim=0.6, blur=10, tint=(0.75, 0.55, 0.35), ink=(0.10, 0.05, 0.03), hi=(0.55, 0.18, 0.05)),
    sources=['NASA (via Live Science, EarthSky): the Moon recedes about 3.8 cm (1.5 in) per year, roughly the rate fingernails grow; measured with laser reflectors placed during Apollo.', '80-year total ≈ 3 m (calculated).'],
    yt=dict(title_en='The Moon Moves 3.8 cm Away Every Year #Shorts', title_ko='달은 해마다 3.8cm씩 멀어진다')))

if __name__ == '__main__': main(EP)
