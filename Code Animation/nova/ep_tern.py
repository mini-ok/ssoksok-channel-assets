"""〈100g 새가 달까지 세 번〉 — 종이접기(색종이 다각형, 접힌 면마다 다른 명암, 접은 자국 격자), 소리는 오르골.
사실: 북극제비갈매기는 그린란드·아이슬란드 번식 개체가 해마다 평균 약 70,900 km를 왕복(Egevang et al. 2010, PNAS).
30년 넘게 살아 평생 2,400,000 km를 넘을 수 있어 달 왕복 약 세 번(같은 논문). 몸무게 약 100 g.
"""
import math, numpy as np, cv2, cairo
from base import *
import sfx as S

BG = (0.93, 0.90, 0.84); PAPER_W = (0.98, 0.97, 0.94); GREY = (0.70, 0.72, 0.75); RED = (0.86, 0.22, 0.18); BLK_ = (0.13, 0.13, 0.15)
SEA = (0.30, 0.55, 0.72); ICE = (0.92, 0.95, 0.98); LAND = (0.55, 0.70, 0.45); MOONC = (0.80, 0.80, 0.76); NIGHT = (0.16, 0.20, 0.32)
T_MAP = 4.2; T_KM = 9.6; T_MOON = 14.8; T_CODA = 20.6
_r = np.random.default_rng(709)

def _crease():
    img = np.ones((H, W, 3), np.float32) * np.array(BG[::-1], np.float32)
    s, cr = surf()
    cr.set_line_width(2)
    for k in range(-20, 20):                                      # 대각선 접힘 자국
        a = 0.05 + 0.04 * (k % 3 == 0)
        cr.set_source_rgba(0, 0, 0, a); cr.move_to(k * 135, 0); cr.line_to(k * 135 + 1920, 1920); cr.stroke()
        cr.set_source_rgba(1, 1, 1, a * 1.5); cr.move_to(k * 135 + 3, 0); cr.line_to(k * 135 + 1923, 1920); cr.stroke()
    n = cv2.GaussianBlur(_r.normal(0, 1, (H, W)).astype(np.float32), (0, 0), 1.0) * 0.012
    return over(img * (1 + n[..., None]), s)
BGI = _crease()

FA = [1.0]
def facet(cr, pts, col, shade):
    c = tuple(min(1, max(0, v * shade)) for v in col)
    cr.move_to(*pts[0]); [cr.line_to(*p) for p in pts[1:]]; cr.close_path()
    cr.set_source_rgba(*c, FA[0]); cr.fill_preserve(); cr.set_source_rgba(0, 0, 0, 0.18 * FA[0]); cr.set_line_width(1.5); cr.stroke()

def tern(cr, x, y, sc, flap, a=1.0, ang=0.0):
    cr.save(); cr.translate(x, y); cr.rotate(ang); cr.scale(sc, sc)
    up = math.sin(flap)
    if a < 1: cr.push_group()
    # 뒤 날개
    facet(cr, [(-20, -8), (10, -30 - 60 * up), (-60, -50 - 120 * up)], GREY, 0.70)
    facet(cr, [(-20, -8), (-60, -50 - 120 * up), (30, -6)], GREY, 0.60)
    # 몸통
    facet(cr, [(-80, 0), (0, -18), (60, -6), (0, 12)], PAPER_W, 1.0)
    facet(cr, [(-80, 0), (0, 12), (60, -6), (10, 22)], PAPER_W, 0.86)
    facet(cr, [(-80, 0), (-150, -30), (-110, 4)], PAPER_W, 0.92)       # 갈라진 꼬리
    facet(cr, [(-80, 0), (-155, 18), (-110, 6)], PAPER_W, 0.80)
    facet(cr, [(55, -6), (90, -20), (82, 2)], BLK_, 1.0)               # 검은 머리 모자
    facet(cr, [(88, -14), (130, -6), (88, -4)], RED, 1.0)              # 붉은 부리
    # 앞 날개
    facet(cr, [(-5, -6), (35, -30 - 80 * up), (-40, -60 - 150 * up)], GREY, 1.05)
    facet(cr, [(-5, -6), (-40, -60 - 150 * up), (45, -4)], GREY, 0.88)
    if a < 1: cr.pop_group_to_source(); cr.paint_with_alpha(a)
    cr.restore()

def draw(t):
    s, cr = surf()
    if t < T_MAP:
        a = 1 - ramp(t, T_MAP - 0.4, T_MAP)
        tern(cr, 540 + 30 * math.sin(t * 0.8), 980 + 20 * math.sin(t * 1.7), 2.6, t * 5.0, a)
        txt(cr, '~100 g', 540, 1400, 64, BLK_, a * ramp(t, 1.2, 1.6), fam=BOLD)
    elif t < T_KM:                                                 # 접은 종이 지도 위 극에서 극으로
        a = ramp(t, T_MAP, T_MAP + 0.4) * (1 - ramp(t, T_KM - 0.4, T_KM))
        x0, y0, x1, y1 = 190, 560, 890, 1500
        FA[0] = a
        cols = [ICE, SEA, SEA, SEA, SEA, SEA, ICE]
        for k in range(7):                                         # 병풍 접기 띠
            yA = y0 + (y1 - y0) * k / 7; yB = y0 + (y1 - y0) * (k + 1) / 7
            facet(cr, [(x0, yA), (x1, yA), (x1, yB), (x0, yB)], cols[k], 1.0 if k % 2 == 0 else 0.86)
        for (lx, ly, lw, lh) in [(560, 600, 200, 110), (240, 760, 180, 300), (600, 900, 220, 380), (260, 1120, 120, 200)]:
            facet(cr, [(lx, ly), (lx + lw, ly + 20), (lx + lw - 30, ly + lh), (lx + 20, ly + lh - 10)], LAND, 1.0)
        txt(cr, 'GREENLAND', 660, 690, 30, BLK_, a, fam=BOLD); txt(cr, 'WEDDELL SEA', 540, 1470, 30, BLK_, a, fam=BOLD)
        p = smooth(ramp(t, T_MAP + 0.6, T_KM - 0.8))
        pts = [(640, 640), (520, 860), (470, 1080), (500, 1300), (560, 1440)]
        def at(u):
            u = min(max(u, 0), 1) * (len(pts) - 1); i = min(int(u), len(pts) - 2); f = u - i
            return pts[i][0] + (pts[i + 1][0] - pts[i][0]) * f, pts[i][1] + (pts[i + 1][1] - pts[i][1]) * f
        cr.set_source_rgba(*RED, a); cr.set_line_width(6); cr.set_dash([18, 12]); cr.move_to(*pts[0])
        for k in range(1, 41):
            if k / 40 > p: break
            cr.line_to(*at(k / 40))
        cr.stroke(); cr.set_dash([])
        bx, by = at(p); tern(cr, bx, by, 0.7, t * 7, a, ang=math.pi / 2.2)
    elif t < T_MOON:                                               # 한 해 거리 → 평생 거리
        a = ramp(t, T_KM, T_KM + 0.4) * (1 - ramp(t, T_MOON - 0.4, T_MOON))
        g = smooth(ramp(t, T_KM + 0.4, T_KM + 2.0)); g2 = smooth(ramp(t, T_KM + 2.4, T_MOON - 0.8))
        FA[0] = a
        txt(cr, f'{int(70900 * g):,} km', 540, 900, 96, BLK_, a, fam=BLK)
        txt(cr, 'every year · 해마다', 540, 980, 40, BLK_, a, fam=BOLD)
        for k in range(30):                                        # 30년 = 종이 조각 30장
            if k / 30 > g2: break
            c, r_ = k % 10, k // 10
            facet(cr, [(170 + c * 76, 1120 + r_ * 90), (230 + c * 76, 1120 + r_ * 90), (200 + c * 76, 1180 + r_ * 90)], RED if k % 2 else GREY, 1.0)
        txt(cr, f'× {int(30 * g2)} years', 540, 1450, 52, RED, a * ramp(t, T_KM + 2.4, T_KM + 2.8), fam=BLK)
    else:                                                          # 지구-달 세 번 왕복
        a = ramp(t, T_MOON, T_MOON + 0.4) * (1 - ramp(t, T_CODA - 0.4, T_CODA))
        FA[0] = a
        facet(cr, [(80, 500), (1000, 500), (1000, 1520), (80, 1520)], NIGHT, 1.0)
        for k in range(40):
            sx, sy = _r_st[k]; cr.set_source_rgba(1, 1, 1, 0.6 * a); cr.arc(sx, sy, 3, 0, 6.283); cr.fill()
        ex, mx, yy = 220, 860, 1000
        for k in range(8):                                         # 접은 지구·달
            q0, q1 = k * math.pi / 4, (k + 1) * math.pi / 4
            facet(cr, [(ex, yy), (ex + 90 * math.cos(q0), yy + 90 * math.sin(q0)), (ex + 90 * math.cos(q1), yy + 90 * math.sin(q1))], SEA if k % 3 else LAND, 0.85 + 0.15 * (k % 2))
            facet(cr, [(mx, yy), (mx + 34 * math.cos(q0), yy + 34 * math.sin(q0)), (mx + 34 * math.cos(q1), yy + 34 * math.sin(q1))], MOONC, 0.85 + 0.15 * (k % 2))
        p = ramp(t, T_MOON + 0.6, T_CODA - 1.2) * 6                 # 왕복 6구간
        for k in range(3):
            yk = yy - 160 + k * 160
            for half in range(2):
                seg = k * 2 + half; f = min(max(p - seg, 0), 1)
                if f <= 0: continue
                xa, xb = (ex + 100, mx - 44) if half == 0 else (mx - 44, ex + 100)
                cr.set_source_rgba(*(RED if half == 0 else GREY), a); cr.set_line_width(6)
                cr.move_to(xa, yk + half * 24); cr.line_to(xa + (xb - xa) * f, yk + half * 24); cr.stroke()
            txt(cr, f'{k + 1}', 960, yk + 18, 44, PAPER_W, a * ramp(p, k * 2 + 1.8, k * 2 + 2.0), fam=BLK)
        txt(cr, '2,400,000 km+', 540, 1380, 72, PAPER_W, a * ramp(p, 5.6, 6.0), fam=BLK)
        idx = min(int(p), 5); f = p - idx
        xa, xb = (ex + 100, mx - 44) if idx % 2 == 0 else (mx - 44, ex + 100)
        if p < 6: tern(cr, xa + (xb - xa) * f, yy - 160 + (idx // 2) * 160 - 30, 0.45, t * 9, a, ang=0 if idx % 2 == 0 else math.pi)
    FA[0] = 1.0
    return over(BGI, s)
_r_st = [(float(_r.uniform(100, 980)), float(_r.uniform(520, 1500))) for _ in range(40)]

def sound(path):
    m = S.Mix(EP['DUR'], 70900); tc = EP['t_coda']; b = 60 / 96
    sc = [523.3, 587.3, 659.3, 784.0, 880.0, 1046.5, 1174.7, 1318.5]
    mel = [0, 2, 4, 3, 5, 4, 2, 3, 1, 3, 5, 4, 6, 5, 3, 4]
    t = 0.3; k = 0
    while t < tc - 0.3:
        m.put('mus', t, S.musicbox(sc[mel[k % 16]], 2.0, 0.3))
        if k % 4 == 0: m.put('mus', t, S.musicbox(sc[0] / 2, 2.4, 0.22))
        t += b; k += 1
    for k in range(6): m.put('fx', T_MOON + 0.6 + k * (T_CODA - 1.8 - T_MOON) / 6, S.swoosh(0.6, 0.12, 800, 4000, seed=k))
    m.put('fx', T_KM + 2.0, S.bell(1568.0, 2.0, 0.2))
    for i, f in enumerate([1046.5, 784.0, 523.3]): m.put('mus', tc + 0.8 + i * STEP, S.musicbox(f, 3.0, 0.35))
    m.write(path, rev_mus=2.4, wet_mus=0.4)

EP = finalize(dict(t_coda=T_CODA, draw=draw, sound=sound, end_icon='star', grain=0.0,
    title_en_card='TO THE MOON, THREE TIMES', title_ko_card='100g 새가 달까지 세 번',
    pal=dict(hi=RED, endbg=BG),
    card_style=dict(box='paper', bg=(0.99, 0.98, 0.95), ink=BLK_, hi=RED, y=180, fe=BOLD, fk=BLK),
    cards=[(0.3, 4.0, ['The Arctic tern', 'weighs about *100 grams*.'], ['북극제비갈매기,', '몸무게는 *100g* 남짓']),
           (4.2, 9.4, ['Every year it flies', 'from the Arctic to *Antarctica* and back.'], ['해마다 북극에서', '*남극*까지 갔다 돌아온다']),
           (9.6, 14.6, ['About *70,900 km* a year,', 'for 30 years or more.'], ['한 해 약 *70,900km*,', '30년 넘게']),
           (14.8, 20.4, ['Over *2.4 million km* in a lifetime:', 'the Moon and back, *three times*.'], ['평생 *240만km* 이상,', '달까지 *세 번* 왕복'])],
    coda=[('Small wings, endless sky.', '작은 날개, 끝없는 하늘'), ('It just keeps following the light.', '그저 빛을 따라 날아갈 뿐'), ('Follow your light, however far.', '아무리 멀어도 내 빛을 따라가자')],
    coda_style=dict(dim=0.55, blur=8, tint=(0.85, 0.82, 0.76), ink=BLK_, hi=RED, fe=BOLD),
    sources=['Egevang et al. 2010, PNAS: Arctic terns from Greenland/Iceland average ~70,900 km per year; lifetime may exceed 2.4 million km, about three return trips to the Moon.', 'Bird weighs just over 100 g (Egevang, quoted by British Antarctic Survey / PhysOrg).'],
    yt=dict(title_en='This 100 g Bird Flies to the Moon and Back Three Times #Shorts', title_ko='100g 새가 평생 달까지 세 번 왕복')))

if __name__ == '__main__': main(EP)
