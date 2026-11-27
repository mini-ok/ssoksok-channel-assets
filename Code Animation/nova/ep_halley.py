"""〈한 사람의 일생에 한 번〉 — 중세 채색 필사본(양피지, 금박 테두리, 붉은·푸른 머리글자, 덩굴 무늬), 소리는 류트와 허디거디 드론.
사실: 핼리 혜성의 공전 주기는 평균 약 76년(74~79년). 마지막 근일점 1986년, 다음은 2061년 7월 28일(NASA, Britannica).
1066년 출현은 바이외 태피스트리에 기록. 사람 한 평생과 비슷한 길이라 대부분 평생 한 번 본다.
"""
import math, numpy as np, cv2, cairo
from base import *
import sfx as S

VELLUM = (0.93, 0.87, 0.72); INKB = (0.22, 0.14, 0.08); RED = (0.66, 0.14, 0.10); BLUE = (0.14, 0.24, 0.55)
GOLD = (0.83, 0.64, 0.22); GREEN = (0.24, 0.42, 0.24)
T_ORBIT = 4.0; T_YEARS = 9.4; T_LIFE = 14.6; T_CODA = 19.8
_r = np.random.default_rng(76)

def _vellum():
    n = cv2.GaussianBlur(_r.normal(0, 1, (H // 4, W // 4)).astype(np.float32), (0, 0), 6)
    n = cv2.resize(n, (W, H)); n /= np.abs(n).max() + 1e-6
    f = cv2.GaussianBlur(_r.normal(0, 1, (H, W)).astype(np.float32), (0, 0), 1.2)
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    edge = np.clip(1 - (np.maximum(np.abs(xx / W - 0.5), np.abs(yy / H - 0.5)) - 0.36) * 3.5, 0.55, 1)
    base = np.array(VELLUM[::-1], np.float32)
    img = base[None, None] * (1 + 0.05 * n[..., None] + 0.015 * f[..., None]) * edge[..., None]
    return img.astype(np.float32)
VEL = _vellum()

def border(cr):
    cr.set_source_rgb(*GOLD); cr.set_line_width(10); cr.rectangle(60, 60, DW - 120, DH - 120); cr.stroke()
    cr.set_source_rgb(*RED); cr.set_line_width(3); cr.rectangle(80, 80, DW - 160, DH - 160); cr.stroke()
    for side in range(4):                                          # 덩굴 무늬
        for k in range(14):
            if side < 2: x = 110 + k * (DW - 220) / 13; y = 100 if side == 0 else DH - 100
            else: y = 140 + k * (DH - 280) / 13; x = 100 if side == 2 else DW - 100
            cr.set_source_rgb(*(GREEN if k % 2 else BLUE)); cr.arc(x, y, 9, 0, 6.283); cr.fill()
            cr.set_source_rgb(*GOLD); cr.arc(x, y, 4, 0, 6.283); cr.fill()

def comet(cr, x, y, ang, L, a=1.0):
    ca, sa = math.cos(ang), math.sin(ang)
    for k in range(7):                                             # 필사본식 물결 꼬리
        off = (k - 3) * 9; cr.set_source_rgba(*(RED if k % 2 else GOLD), a); cr.set_line_width(5)
        cr.move_to(x - sa * off * 0.4, y + ca * off * 0.4)
        for s in range(1, 11):
            d = L * s / 10; w = math.sin(s * 1.3 + k) * 6 * s / 10
            cr.line_to(x - ca * d - sa * (off * (1 + s / 8) + w), y - sa * d + ca * (off * (1 + s / 8) + w))
        cr.stroke()
    for k in range(8):                                             # 별 머리
        q = k * math.pi / 4; rr = 34 if k % 2 == 0 else 16
        cr.line_to(x + rr * math.cos(q), y + rr * math.sin(q)) if k else cr.move_to(x + rr, y)
    cr.close_path(); cr.set_source_rgba(*GOLD, a); cr.fill_preserve(); cr.set_source_rgba(*INKB, a); cr.set_line_width(3); cr.stroke()

def sun(cr, x, y, r):
    cr.set_source_rgb(*GOLD); cr.arc(x, y, r, 0, 6.283); cr.fill()
    for k in range(16):
        q = k * math.pi / 8; cr.set_source_rgb(*RED); cr.set_line_width(4)
        cr.move_to(x + (r + 6) * math.cos(q), y + (r + 6) * math.sin(q)); cr.line_to(x + (r + 26) * math.cos(q), y + (r + 26) * math.sin(q)); cr.stroke()
    cr.set_source_rgb(*INKB); cr.set_line_width(3); cr.arc(x, y, r, 0, 6.283); cr.stroke()

def draw(t):
    s, cr = surf(); border(cr)
    cx, cy = 540, 1100
    if t < T_YEARS:                                                 # 궤도: 해 근처는 빠르게, 멀리선 느리게
        a = 1 - ramp(t, T_YEARS - 0.5, T_YEARS)
        cr.set_source_rgba(*INKB, a); cr.set_line_width(3); cr.set_dash([12, 10])
        cr.save(); cr.translate(cx + 40, cy); cr.scale(330, 110); cr.arc(0, 0, 1, 0, 6.283); cr.restore(); cr.stroke(); cr.set_dash([])
        sun(cr, cx - 271, cy, 30)
        for k, (nm, rr) in enumerate([('', 70), ('', 110)]):
            cr.set_source_rgba(*BLUE, 0.6 * a); cr.set_line_width(2); cr.arc(cx - 271, cy, rr * 0.7, 0, 6.283); cr.stroke()
        ph = ((t - 0.5) / 5.0) % 1.0                              # 대략 케플러 운동처럼 보이게
        E = 2 * math.pi * ph; E = E - 0.85 * math.sin(E) * 0.0
        M = 2 * math.pi * ph
        for _ in range(6): E = E - (E - 0.94 * math.sin(E) - M) / (1 - 0.94 * math.cos(E))
        px = cx + 40 - 330 * math.cos(E); py = cy + 110 * math.sin(E)
        ang = math.atan2(py - cy, px - (cx - 271)) + math.pi
        dist = math.hypot(px - (cx - 271), py - cy)
        comet(cr, px, py, ang, 20 + 9000 / max(dist, 60), a)
        txt(cr, 'ORBITA · 76 ANNI', 540, 1420, 40, RED, a, fam=SERIF)
    if t >= T_YEARS - 0.3:                                         # 연대 두루마리
        a = ramp(t, T_YEARS - 0.3, T_YEARS + 0.3) * (1 - ramp(t, T_LIFE - 0.4, T_LIFE))
        yrs = [1066, 1835, 1910, 1986, 2061]
        for i, yv in enumerate(yrs):
            ai = a * ramp(t, T_YEARS + 0.3 + i * 0.6, T_YEARS + 0.7 + i * 0.6)
            y = 760 + i * 150
            cr.set_source_rgba(*(BLUE if yv == 2061 else RED), ai); cr.rectangle(190, y - 60, 90, 90); cr.fill()
            txt(cr, str(yv)[0], 235, y + 8, 64, GOLD, ai, fam=SERIF)
            txt(cr, str(yv), 310, y + 4, 64, INKB, ai, fam=SERIF, anchor='l')
            note = {1066: 'Bayeux', 1835: 'Twain born', 1910: 'Twain died', 1986: 'Giotto', 2061: 'next · 다음'}[yv]
            txt(cr, note, 900, y + 4, 38, GREEN if yv != 2061 else BLUE, ai, fam=SERIF, anchor='r')
            if i < len(yrs) - 1:
                cr.set_source_rgba(*GOLD, ai); cr.set_line_width(4); cr.move_to(235, y + 34); cr.line_to(235, y + 86); cr.stroke()
    if t >= T_LIFE - 0.3:                                          # 사람 한 평생과 나란히
        a = ramp(t, T_LIFE - 0.3, T_LIFE + 0.3) * (1 - ramp(t, T_CODA - 0.4, T_CODA))
        g = smooth(ramp(t, T_LIFE + 0.5, T_LIFE + 3.0))
        x0, x1 = 170, 910
        for row, (lab, col, L) in enumerate([('comet · 혜성 76', GOLD, 76), ('life · 한 평생 ~80', RED, 80)]):
            y = 980 + row * 220
            cr.set_source_rgba(*INKB, a); cr.set_line_width(3); cr.rectangle(x0, y - 30, x1 - x0, 60); cr.stroke()
            cr.set_source_rgba(*col, a); cr.rectangle(x0 + 4, y - 26, (x1 - x0 - 8) * g * L / 82, 52); cr.fill()
            txt(cr, lab, 540, y - 55, 40, INKB, a, fam=SERIF)
        if g > 0.98:
            comet(cr, x0 + (x1 - x0) * 76 / 82, 900, math.pi, 60, a * ramp(t, T_LIFE + 3.0, T_LIFE + 3.4))
    img = over(VEL, s)
    return img

def sound(path):
    m = S.Mix(EP['DUR'], 1066); tc = EP['t_coda']; b = 60 / 72
    D = [146.8, 164.8, 174.6, 196.0, 220.0, 233.1, 261.6, 293.7, 329.6, 349.2]     # D 도리안
    mel = [4, 3, 4, 6, 7, 6, 4, 3, 2, 3, 4, 2, 1, 0, 1, 2]
    t = 0.4; k = 0
    while t < tc - 0.4:
        m.put('mus', t, S.lute(D[mel[k % 16]], 1.8, 0.33, seed=k))
        if k % 2 == 0: m.put('mus', t + b / 2, S.lute(D[mel[k % 16]] / 2, 1.4, 0.18, seed=k + 99))
        t += b; k += 1
    m.put('amb', 0, S.gurdy([73.4, 110.0], EP['t_end'] + 1, 0.12))
    m.put('fx', T_YEARS + 0.3, S.bell(587.3, 2.5, 0.2))
    for i in range(5): m.put('fx', T_YEARS + 0.3 + i * 0.6, S.tok(500 + 80 * i, 0.18))
    m.put('fx', T_LIFE + 3.0, S.bell(880.0, 3.0, 0.28))
    for i, f in enumerate([293.7, 220.0, 146.8]): m.put('mus', tc + 0.8 + i * STEP, S.lute(f, 3.0, 0.35, seed=200 + i))
    m.write(path, rev_mus=2.6, wet_mus=0.38)

EP = finalize(dict(t_coda=T_CODA, draw=draw, sound=sound, end_icon='star', grain=0.0,
    title_en_card='ONCE IN A LIFETIME', title_ko_card='한 사람의 일생에 한 번',
    pal=dict(hi=RED, endbg=VELLUM),
    card_style=dict(box='paper', bg=(0.96, 0.91, 0.78), ink=INKB, hi=RED, y=200, fe=SERIF, fk=BLK),
    cards=[(0.3, 3.8, ['Halley’s Comet', 'swings past the Sun'], ['핼리 혜성은', '해 곁을 스쳐 지나간다']),
           (4.0, 9.2, ['…once every *76 years*', 'on average.'], ['평균 *76년*에', '한 번씩']),
           (9.4, 14.4, ['Last seen in 1986.', 'Next: *July 2061*.'], ['마지막은 1986년,', '다음은 *2061년 7월*']),
           (14.6, 19.6, ['About the length of', '*one human life*.'], ['사람 *한 평생*과', '거의 같은 길이'])],
    coda=[('It comes once in a lifetime.', '평생 한 번 찾아온다'), ('Some chances will not return.', '어떤 기회는 다시 오지 않는다'), ('Look up when the sky offers you something.', '하늘이 무언가를 보여줄 때 고개를 들자')],
    coda_style=dict(dim=0.55, blur=8, tint=(0.80, 0.72, 0.55), ink=INKB, hi=RED, fe=SERIF),
    sources=['Halley’s Comet: average period ~76 years (74–79); last perihelion 1986, next 28 July 2061 (NASA Science; Britannica).', '1066 appearance recorded in the Bayeux Tapestry; Mark Twain born 1835, died 1910, both Halley years.'],
    yt=dict(title_en='Halley’s Comet Returns Only Once in a Lifetime #Shorts', title_ko='핼리 혜성, 평생 한 번')))

if __name__ == '__main__': main(EP)
