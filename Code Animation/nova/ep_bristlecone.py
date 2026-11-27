"""〈피라미드보다 오래된 나무〉 — 유화 임파스토(두꺼운 물감 결, 결을 따라 빛이 맺히는 요철, 캔버스 천), 소리는 활로 긋는 현.
사실: 므두셀라(그레이트베이슨 브리슬콘소나무)는 수령 약 4,855년(2024년 기준), 확인된 가장 오래된 비클론 나무(Guinness; Wikipedia).
캘리포니아 화이트산맥 해발 약 2,900~3,000 m. 혹독한 환경에서 느리게 자라 촘촘하고 송진 많은 목재가 썩음을 견딘다(WorldAtlas).
기자 대피라미드는 기원전 약 2560년 완공(약 4,580년 전) → 므두셀라가 더 먼저 싹텄다(계산).
"""
import math, numpy as np, cv2, cairo
from base import *
import sfx as S

SKY1 = (0.95, 0.66, 0.38); SKY2 = (0.36, 0.30, 0.52); ROCK = (0.62, 0.56, 0.50); ROCKD = (0.36, 0.32, 0.34)
BARK = (0.45, 0.30, 0.18); SILVER = (0.86, 0.80, 0.70); NEEDLE = (0.20, 0.36, 0.26); CREAMP = (0.97, 0.92, 0.80); RUST = (0.70, 0.30, 0.16)
T_AGE = 4.2; T_TIME = 9.4; T_SLOW = 15.0; T_CODA = 20.6
_r = np.random.default_rng(4855)

def _impasto():
    """세계에 고정된 붓 결 높이 지도: 짧은 획 수천 개, 방향은 완만한 흐름장."""
    h = np.zeros((H // 2, W // 2), np.float32)
    hh, ww = h.shape
    for _ in range(9000):
        x, y = _r.uniform(0, ww), _r.uniform(0, hh)
        ang = 0.6 * math.sin(x / 90) + 0.5 * math.cos(y / 140) + _r.normal(0, 0.25)
        L = _r.uniform(10, 26); w = _r.uniform(2.5, 5.5)
        p0 = (int(x - L * math.cos(ang)), int(y - L * math.sin(ang))); p1 = (int(x + L * math.cos(ang)), int(y + L * math.sin(ang)))
        cv2.line(h, p0, p1, float(_r.uniform(0.5, 1.0)), int(w), cv2.LINE_AA)
    h = cv2.GaussianBlur(h, (0, 0), 1.3); h = cv2.resize(h, (W, H))
    gx = cv2.Sobel(h, cv2.CV_32F, 1, 0, ksize=3); gy = cv2.Sobel(h, cv2.CV_32F, 0, 1, ksize=3)
    light = np.clip(1 + 0.45 * (-gx * 0.7 - gy * 0.7), 0.85, 1.15)                  # 왼쪽 위 빛
    yy, xx = np.mgrid[0:H, 0:W]
    canvas = 1 + 0.025 * (((xx // 3) % 2) ^ ((yy // 3) % 2)) - 0.0125
    return (light * canvas).astype(np.float32)
LIGHT = _impasto()

def tree(cr, x, y, sc, a=1.0):
    cr.save(); cr.translate(x, y); cr.scale(sc, sc)
    def limb(pts, w, col):
        cr.set_source_rgba(*col, a); cr.set_line_width(w); cr.set_line_cap(cairo.LINE_CAP_ROUND)
        cr.move_to(*pts[0]); cr.curve_to(*pts[1], *pts[2], *pts[3]); cr.stroke()
    limb([(0, 0), (-20, -120), (40, -200), (-10, -320)], 110, BARK)               # 비틀린 줄기
    limb([(-14, 0), (-30, -110), (24, -190), (-20, -310)], 34, SILVER)               # 죽은 쪽 은빛 결
    limb([(-10, -300), (-80, -350), (-150, -330), (-200, -400)], 30, SILVER)       # 죽은 가지
    limb([(0, -250), (60, -300), (130, -290), (170, -360)], 34, BARK)
    for (cx, cy, r) in [(170, -380, 60), (120, -330, 46), (-20, -350, 50), (30, -400, 44)]:
        for j in range(40):
            q = j * 2.4; rr = r * math.sqrt((j + 0.5) / 40)
            cr.set_source_rgba(*(NEEDLE if j % 3 else (0.32, 0.48, 0.30)), a)
            cr.save(); cr.translate(cx + rr * math.cos(q), cy + rr * math.sin(q)); cr.rotate(q); cr.scale(1, 0.45); cr.arc(0, 0, 18, 0, 6.283); cr.restore(); cr.fill()
    cr.restore()

def mountain(cr, a=1.0):
    cr.set_source_rgba(*ROCKD, a); cr.move_to(0, 1300); cr.line_to(260, 1050); cr.line_to(520, 1180); cr.line_to(800, 980); cr.line_to(1080, 1150); cr.line_to(1080, 1920); cr.line_to(0, 1920); cr.fill()
    cr.set_source_rgba(*ROCK, a); cr.move_to(0, 1560); cr.curve_to(300, 1480, 700, 1500, 1080, 1440); cr.line_to(1080, 1920); cr.line_to(0, 1920); cr.fill()

def draw(t):
    s, cr = surf()
    g = cairo.LinearGradient(0, 0, 0, 1500); g.add_color_stop_rgb(0, *SKY2); g.add_color_stop_rgb(1, *SKY1); cr.set_source(g); cr.paint()
    cr.set_source_rgb(0.99, 0.86, 0.55); cr.arc(800, 1020, 70, 0, 6.283); cr.fill()
    mountain(cr)
    tree(cr, 470, 1540, 1.55 + 0.04 * ramp(t, 0, T_AGE))
    base = arr(s)
    paint = cv2.medianBlur((base[..., :3] * 255).astype(np.uint8), 9).astype(np.float32) / 255
    bg = np.clip(paint * LIGHT[..., None], 0, 1)
    s, cr = surf()
    if T_AGE - 0.3 <= t < T_TIME:
        a = ramp(t, T_AGE - 0.3, T_AGE + 0.3) * (1 - ramp(t, T_TIME - 0.4, T_TIME))
        n = int(4855 * smooth(ramp(t, T_AGE + 0.3, T_AGE + 2.6)))
        cr.set_source_rgba(*CREAMP, 0.85 * a); cr.rectangle(170, 560, 740, 250); cr.fill()
        txt(cr, f'{n:,}', 540, 720, 140, RUST, a, fam=SERIF)
        txt(cr, 'years · 년', 540, 785, 40, ROCKD, a, fam=SERIF)
    if T_TIME - 0.3 <= t < T_SLOW:                                          # 연대(위에서 아래로, 먼저 일어난 일부터)
        a = ramp(t, T_TIME - 0.3, T_TIME + 0.3) * (1 - ramp(t, T_SLOW - 0.4, T_SLOW))
        cr.set_source_rgba(*CREAMP, 0.92 * a); cr.rectangle(130, 520, 820, 720); cr.fill()
        ev = [('c. 2830 BC', 'tree sprouts · 싹이 틈', RUST), ('c. 2560 BC', 'Great Pyramid · 대피라미드', ROCKD), ('753 BC', 'Rome founded · 로마 건국', ROCKD),
              ('AD 1', 'year one · 서기 1년', ROCKD), ('2026', 'still alive · 아직 살아 있다', RUST)]
        cr.set_source_rgba(*ROCKD, a); cr.set_line_width(6); cr.move_to(230, 600); cr.line_to(230, 1160); cr.stroke()
        for i, (yr, lab, col) in enumerate(ev):
            ai = a * ramp(t, T_TIME + 0.4 + i * 0.7, T_TIME + 0.8 + i * 0.7); y = 600 + i * 140
            cr.set_source_rgba(*col, ai); cr.arc(230, y, 18, 0, 6.283); cr.fill()
            txt(cr, yr, 280, y - 4, 46, col, ai, fam=SERIF, anchor='l'); txt(cr, lab, 280, y + 44, 34, ROCKD, ai, fam=SERIF, anchor='l')
    if T_SLOW - 0.3 <= t < T_CODA:                                          # 나이테
        a = ramp(t, T_SLOW - 0.3, T_SLOW + 0.3) * (1 - ramp(t, T_CODA - 0.4, T_CODA))
        cr.set_source_rgba(*CREAMP, 0.92 * a); cr.rectangle(170, 520, 740, 680); cr.fill()
        cx, cy = 540, 800; R = 220
        cr.set_source_rgba(*SILVER, a); cr.arc(cx, cy, R, 0, 6.283); cr.fill()
        nr = int(90 * smooth(ramp(t, T_SLOW + 0.4, T_SLOW + 3.5)))
        for k in range(nr):
            rr = R * (1 - k / 92); cr.set_source_rgba(*BARK, a * (0.35 + 0.3 * (k % 4 == 0))); cr.set_line_width(1.4)
            cr.save(); cr.translate(cx, cy); cr.scale(1, 0.96); cr.arc(0, 0, rr, 0, 6.283); cr.restore(); cr.stroke()
        txt(cr, 'thin rings · 아주 얇은 나이테', 540, 1080, 38, ROCKD, a * ramp(t, T_SLOW + 1.0, T_SLOW + 1.4), fam=SERIF)
        txt(cr, '~3,000 m · 해발 약 3,000m', 540, 1140, 38, RUST, a * ramp(t, T_SLOW + 1.6, T_SLOW + 2.0), fam=SERIF)
    return over(bg, s)

def _bgr(rgb): return np.ascontiguousarray(rgb[..., ::-1])

def sound(path):
    m = S.Mix(EP['DUR'], 2830); tc = EP['t_coda']
    chords = [[110.0, 164.8, 220.0, 261.6], [98.0, 146.8, 196.0, 246.9], [87.3, 130.8, 174.6, 220.0], [82.4, 123.5, 164.8, 207.7]]
    t = 0.2; k = 0
    while t < tc - 0.5:
        for j, f in enumerate(chords[k % 4]): m.put('mus', t, S.bowed(f, 5.6, 0.16 if j else 0.2, seed=k * 4 + j))
        t += 5.0; k += 1
    m.put('amb', 0, S.wind(EP['t_end'] + 1, 0.08) if hasattr(S, 'wind') else S.drone([55.0], EP['t_end'] + 1, 0.06, 'sine'))
    for i in range(5): m.put('fx', T_TIME + 0.4 + i * 0.7, S.bell(440.0 * (1 + 0.25 * i), 1.6, 0.12))
    for i, f in enumerate([220.0, 164.8, 110.0]): m.put('mus', tc + 0.8 + i * STEP, S.bowed(f, 3.6, 0.22, seed=90 + i))
    m.write(path, rev_mus=3.4, wet_mus=0.45)

EP = finalize(dict(t_coda=T_CODA, draw=draw, sound=sound, end_icon='star', grain=0.0,
    title_en_card='OLDER THAN THE PYRAMIDS', title_ko_card='피라미드보다 오래된 나무',
    pal=dict(hi=RUST, endbg=CREAMP),
    card_style=dict(box='paper', bg=(0.97, 0.92, 0.80), ink=(0.22, 0.16, 0.12), hi=RUST, y=180, fe=SERIF, fk=BLK),
    cards=[(0.3, 4.0, ['A twisted pine', 'in California’s White Mountains.'], ['캘리포니아 화이트산맥의', '비틀린 소나무 한 그루']),
           (4.2, 9.2, ['It is about *4,855 years* old.', 'Its name: Methuselah.'], ['나이 약 *4,855살*,', '이름은 므두셀라']),
           (9.4, 14.8, ['It sprouted *before*', 'the Great Pyramid was finished.'], ['대피라미드가 완성되기', '*전에* 싹을 틔웠다']),
           (15.0, 20.4, ['Cold, dry, high, poor soil.', 'It grows *very slowly*, wood dense as stone.'], ['춥고 메마른 높은 땅,', '*아주 느리게* 자라 단단해졌다'])],
    coda=[('It grew slowly, in the harshest place,', '가장 거친 곳에서 느리게 자라'), ('and outlived every empire.', '모든 제국보다 오래 살았다'), ('Slow is not weak.', '느린 것은 약한 것이 아니다')],
    coda_style=dict(dim=0.55, blur=8, tint=(0.70, 0.58, 0.50), ink=(0.22, 0.16, 0.12), hi=RUST, fe=SERIF),
    sources=['Methuselah, Great Basin bristlecone pine, ~4,855 years (as of 2024), oldest confirmed non-clonal tree; White Mountains, CA, ~2,900–3,000 m (Guinness World Records; Wikipedia).', 'Slow growth makes dense, resinous, decay-resistant wood (WorldAtlas). Great Pyramid completed c. 2560 BC, so the tree is older (calculated).'],
    yt=dict(title_en='This Tree Is Older Than the Pyramids #Shorts', title_ko='피라미드보다 오래 산 나무, 므두셀라')))

if __name__ == '__main__': main(EP)
