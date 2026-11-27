"""〈걸어서 지구 한 바퀴〉 — 스텐실 그라피티(콘크리트 벽, 스프레이 안개 가장자리, 흘러내린 물감 자국, 오려 낸 판의 다리(브리지)), 소리는 붐뱁 힙합 비트(킥·브러시·업라이트 베이스).
계산(모두 계산값): 적도 둘레 40,075 km(NASA). 시속 5 km로 쉬지 않고 → 8,015시간 ≈ 334일.
하루 8시간 걷기 → 약 1,002일 ≈ 2.7년. 하루 1만 보(보폭 0.75 m 가정, 7.5 km) → 약 5,343일 ≈ 14.6년.
"""
import math, numpy as np, cv2, cairo
from base import *
import sfx as S

T_NONSTOP = 4.2; T_8H = 9.6; T_STEPS = 15.0; T_CODA = 20.6
_r = np.random.default_rng(40075)
def _wall():
    n1 = cv2.resize(cv2.GaussianBlur(_r.normal(0, 1, (H // 8, W // 8)).astype(np.float32), (0, 0), 3), (W, H))
    n2 = cv2.GaussianBlur(_r.normal(0, 1, (H, W)).astype(np.float32), (0, 0), 1.0)
    base = np.array((0.62, 0.62, 0.60)[::-1], np.float32)
    img = base * (1 + 0.06 * n1[..., None] + 0.05 * n2[..., None])
    for y in range(0, H, int(320 * SC)): img[y:y + int(4 * SC)] *= 0.8          # 거푸집 줄눈
    return img.astype(np.float32)
WALL = _wall()
SPRAY = np.clip(cv2.GaussianBlur(_r.normal(0, 1, (H, W)).astype(np.float32), (0, 0), 0.7) * 0.5 + 0.5, 0, 1)
COLS = {'k': np.array((0.08, 0.08, 0.09)[::-1], np.float32), 'r': np.array((0.90, 0.18, 0.20)[::-1], np.float32),
        'y': np.array((0.98, 0.82, 0.12)[::-1], np.float32), 'w': np.array((0.96, 0.95, 0.92)[::-1], np.float32)}

def paint(img, mask, col, drips=True, seed=0):
    soft = cv2.GaussianBlur(mask, (0, 0), 2.2 * SC)                      # 스프레이 안개
    over_ = np.clip(soft * 1.1 + (SPRAY - 0.5) * 0.25 * (soft > 0.02), 0, 1)
    edge = np.clip(cv2.GaussianBlur(mask, (0, 0), 9 * SC) - mask, 0, 1) * 0.35 * SPRAY
    a = np.clip(np.maximum(over_, edge), 0, 1)
    if drips:
        rr = np.random.default_rng(seed); cols = np.where(mask.max(0) > 0.5)[0]
        for x in rr.choice(cols, size=min(6, len(cols)), replace=False) if len(cols) else []:
            ys = np.where(mask[:, x] > 0.5)[0]
            if len(ys) == 0: continue
            y0 = ys.max(); L = int(rr.uniform(30, 120) * SC); w = int(rr.uniform(2, 4) * SC)
            a[y0:y0 + L, max(0, x - w):x + w] = np.maximum(a[y0:y0 + L, max(0, x - w):x + w], 0.9)
    return img * (1 - a[..., None]) + col * a[..., None]

def mask_of(fn):
    s, cr = surf(); cr.set_source_rgb(1, 1, 1); fn(cr); return arr(s)[..., 3].copy()

def walker(cr, x, y, sc, ph):
    cr.save(); cr.translate(x, y); cr.scale(sc, sc)
    cr.arc(0, -330, 42, 0, 6.283); cr.fill()                               # 머리(목 브리지는 틈으로)
    cr.move_to(-40, -270); cr.line_to(40, -270); cr.line_to(30, -120); cr.line_to(-30, -120); cr.close_path(); cr.fill()
    sw = math.sin(ph) * 0.5
    for side, s_ in ((1, sw), (-1, -sw)):
        cr.save(); cr.translate(0, -115); cr.rotate(s_); cr.rectangle(-16, 0, 32, 120); cr.fill(); cr.translate(0, 124); cr.rotate(max(0, -s_) * 0.8); cr.rectangle(-14, 0, 28, 110); cr.fill(); cr.rectangle(-14, 106, 52, 18); cr.fill(); cr.restore()
        cr.save(); cr.translate(side * 8, -262); cr.rotate(-s_ * 0.9); cr.rectangle(-12, 0, 24, 140); cr.fill(); cr.restore()
    cr.restore()

def draw(t):
    img = WALL.copy()
    if t < T_NONSTOP:
        a = 1 - ramp(t, T_NONSTOP - 0.3, T_NONSTOP)
        if a > 0:
            m = mask_of(lambda cr: (cr.arc(540, 1080, 360, 0, 6.283), cr.fill()))
            img = paint(img, m * a, COLS['y'], drips=True, seed=1)
            m2 = mask_of(lambda cr: walker(cr, 540, 1330, 1.0, t * 6))
            img = paint(img, m2 * a, COLS['k'], drips=False)
    elif t < T_8H:
        a = ramp(t, T_NONSTOP, T_NONSTOP + 0.3) * (1 - ramp(t, T_8H - 0.3, T_8H))
        g = smooth(ramp(t, T_NONSTOP + 0.4, T_NONSTOP + 2.6))
        m = mask_of(lambda cr: (cr.set_line_width(46), cr.arc(540, 1050, 330, -math.pi / 2, -math.pi / 2 + 6.283 * g), cr.stroke()))
        img = paint(img, m * a, COLS['r'], drips=True, seed=2)
        m2 = mask_of(lambda cr: walker(cr, 540 + 330 * math.cos(-math.pi / 2 + 6.283 * g), 1050 + 330 * math.sin(-math.pi / 2 + 6.283 * g) + 40, 0.45, t * 8))
        img = paint(img, m2 * a, COLS['k'], drips=False)
    elif t < T_STEPS:
        a = ramp(t, T_8H, T_8H + 0.3) * (1 - ramp(t, T_STEPS - 0.3, T_STEPS))
        g = ramp(t, T_8H + 0.4, T_8H + 2.4)
        def tally(cr):
            n = int(2.7 * 10 * g)                                           # 0.1년 = 1칸
            for k in range(n):
                x = 160 + (k % 9) * 86; y = 820 + (k // 9) * 170
                cr.rectangle(x, y, 26, 120); cr.fill()
        img = paint(img, mask_of(tally) * a, COLS['w'], drips=True, seed=3)
    else:
        a = ramp(t, T_STEPS, T_STEPS + 0.3) * (1 - ramp(t, T_CODA - 0.3, T_CODA))
        g = ramp(t, T_STEPS + 0.4, T_STEPS + 3.0)
        def steps(cr):
            for k in range(int(30 * g)):
                x = 180 + (k % 6) * 130 + (40 if (k // 6) % 2 else 0); y = 1500 - (k // 6) * 150
                cr.save(); cr.translate(x, y); cr.rotate(-0.2 if k % 2 else 0.2); cr.save(); cr.scale(0.55, 1); cr.arc(0, 0, 40, 0, 6.283); cr.restore(); cr.fill(); cr.arc(0, -56, 16, 0, 6.283); cr.fill(); cr.restore()
        img = paint(img, mask_of(steps) * a, COLS['y'], drips=False)
    s2, c2 = surf(); K = (0.06, 0.06, 0.07); Wt = (0.97, 0.96, 0.92)
    def tag(text, y, size, col, a_):
        if a_ <= 0: return
        c2.set_source_rgba(*(K if col == Wt else Wt), 0.0)
        txt(c2, text, 540, y, size, col, a_, fam=BLK)
    if t < T_NONSTOP: tag('40,075 km', 1640, 96, K, ramp(t, 1.0, 1.4) * (1 - ramp(t, T_NONSTOP - 0.3, T_NONSTOP)))
    elif t < T_8H:
        a = ramp(t, T_NONSTOP + 2.4, T_NONSTOP + 2.8) * (1 - ramp(t, T_8H - 0.3, T_8H))
        tag('334 DAYS', 1080, 130, K, a); tag('5 km/h · nonstop · 쉬지 않고', 1180, 40, K, a)
    elif t < T_STEPS:
        a = ramp(t, T_8H + 2.2, T_8H + 2.6) * (1 - ramp(t, T_STEPS - 0.3, T_STEPS))
        tag('2.7 YEARS', 1500, 120, Wt, a); tag('8 h a day · 하루 8시간', 1590, 44, Wt, a)
    else:
        a = ramp(t, T_STEPS + 2.8, T_STEPS + 3.2) * (1 - ramp(t, T_CODA - 0.3, T_CODA))
        tag('14.6 YEARS', 700, 120, K, a); tag('10,000 steps a day · 하루 1만 보', 790, 44, K, a)
    if t < T_CODA:
        txt(c2, 'calculated · 계산', 540, 1820, 30, (0.12, 0.12, 0.12), 0.8 * (1 - ramp(t, T_CODA - 0.3, T_CODA)), fam=BOLD)
    return over(np.clip(img, 0, 1), s2)

def sound(path):
    m = S.Mix(EP['DUR'], 334); tc = EP['t_coda']; b = 60 / 88
    bass = [55.0, 55.0, 65.4, 61.7, 49.0, 49.0, 58.3, 55.0]
    n = int((tc - 0.3) / (b / 2))
    for k in range(n):
        t = 0.2 + k * b / 2; pos = k % 8
        if pos in (0, 3, 5): m.put('mus', t + (0.03 if pos == 3 else 0), S.kick(50, 0.55))
        if pos in (2, 6): m.put('mus', t, S.brush(0.22, 0.42, seed=k)); m.put('mus', t, S.tok(240, 0.18))
        m.put('mus', t + 0.06 * (k % 2), S.hihat(0.09, seed=k + 900))
        if pos % 2 == 0: m.put('mus', t, S.upright(bass[(k // 2) % 8], 0.5, 0.3))
    for k in range(6): m.put('fx', 0.5 + k * 0.6, S.swoosh(0.35, 0.10, 2000, 9000, seed=k))       # 스프레이
    for i, f in enumerate([220.0, 164.8, 110.0]): m.put('mus', tc + 0.8 + i * STEP, S.upright(f, 2.0, 0.32))
    m.write(path, rev_mus=1.2, wet_mus=0.2)

EP = finalize(dict(t_coda=T_CODA, draw=draw, sound=sound, end_icon='star', grain=0.0,
    title_en_card='WALK AROUND THE WORLD', title_ko_card='걸어서 지구 한 바퀴',
    pal=dict(hi=(0.85, 0.15, 0.18), endbg=(0.93, 0.93, 0.91)),
    card_style=dict(box='paper', bg=(0.97, 0.96, 0.93), ink=(0.06, 0.06, 0.07), hi=(0.85, 0.15, 0.18), y=180, fe=BLK, fk=BLK),
    cards=[(0.3, 4.0, ['Around the equator:', '*40,075 km*.'], ['적도 한 바퀴는', '*40,075km*']),
           (4.2, 9.4, ['Walking nonstop at 5 km/h:', 'about *334 days*.'], ['시속 5km로 쉬지 않고 걸으면', '약 *334일*']),
           (9.6, 14.8, ['Walking 8 hours a day:', 'about *2.7 years*.'], ['하루 8시간씩 걸으면', '약 *2.7년*']),
           (15.0, 20.4, ['Just 10,000 steps a day:', 'about *14.6 years*.'], ['하루 1만 보씩이면', '약 *14.6년*'])],
    coda=[('Ten thousand small steps a day', '하루 만 걸음의 작은 발걸음이'), ('can carry you around the world.', '세상을 한 바퀴 돌게 한다'), ('Don’t underestimate today’s steps.', '오늘의 걸음을 얕보지 말자')],
    coda_style=dict(dim=0.5, blur=8, tint=(0.50, 0.50, 0.48), ink=(0.97, 0.96, 0.92), hi=(0.98, 0.82, 0.12), fe=BLK),
    sources=['Earth’s equatorial circumference 40,075 km (NASA Earth Fact Sheet).', 'Calculated: 40,075 km ÷ 5 km/h ≈ 8,015 h ≈ 334 days; at 8 h/day ≈ 2.7 years; 10,000 steps/day with a 0.75 m stride = 7.5 km/day ≈ 14.6 years.'],
    yt=dict(title_en='How Long Would It Take to Walk Around the Earth? #Shorts', title_ko='걸어서 지구 한 바퀴, 얼마나 걸릴까')))

if __name__ == '__main__': main(EP)
