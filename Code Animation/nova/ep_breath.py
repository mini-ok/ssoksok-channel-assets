"""〈하루 2만 번의 숨〉 — 한지 위 수묵(먹 번짐 고리, 일원상 붓질, 마른 붓 비백), 거문고·북·숨소리.
사실: 성인 안정 시 호흡수 분당 12~20회(American Lung Association; NCBI StatPearls NBK537306).
하루 17,280~28,800회, 80년이면 약 5억~8억 회(계산).
"""
import math, numpy as np, cv2, cairo
from base import *
import sfx as S

HANJI = (0.95, 0.93, 0.87); MUK = (0.08, 0.075, 0.07); SEAL = (0.72, 0.16, 0.12)
_P = {}
def hanji():
    if 'v' in _P: return _P['v']
    r = np.random.default_rng(21); f = np.zeros((H, W), np.float32)
    for _ in range(int(9000 * SC * SC) + 600):
        x, y = r.uniform(0, W), r.uniform(0, H); a = r.uniform(0, 3.14); L = r.uniform(8, 40) * SC
        cv2.line(f, (int(x), int(y)), (int(x + L * math.cos(a)), int(y + L * math.sin(a))), float(r.uniform(0.3, 1)), 1, cv2.LINE_AA)
    f = cv2.GaussianBlur(f, (0, 0), 0.7 * max(SC, .6)); b = cv2.resize(r.standard_normal((H // 70 + 2, W // 70 + 2)).astype(np.float32), (W, H), interpolation=cv2.INTER_CUBIC)
    _P['v'] = solid(HANJI) * (1 - 0.06 * f + 0.025 * b)[..., None]; return _P['v']

def blot(cr, x, y, r, a, wet=1.0):
    """먹 한 점: 가운데는 옅고 가장자리에 먹이 모인다(번짐 테)."""
    g = cairo.RadialGradient(x, y, 0, x, y, r)
    g.add_color_stop_rgba(0, *MUK, 0.35 * a); g.add_color_stop_rgba(0.75, *MUK, 0.45 * a * wet); g.add_color_stop_rgba(0.93, *MUK, 0.75 * a * wet); g.add_color_stop_rgba(1, *MUK, 0)
    cr.set_source(g); cr.arc(x, y, r, 0, 6.283); cr.fill()

def enso(cr, cx, cy, R, u, a, seed=0, w=60):
    """붓으로 긋는 원(일원상). 붓털 9가닥을 각각 선으로 긋고, 끝으로 갈수록 마른 붓(끊김)."""
    r = np.random.default_rng(seed); n = int(420 * u)
    if n < 2: return
    offs = np.linspace(-1, 1, 11); gaps = r.random((11, 420))
    for bi, o in enumerate(offs):
        cr.set_source_rgba(*MUK, (0.34 + 0.16 * (1 - abs(o))) * a)
        drawing = False
        for i in range(n):
            f = i / 420; ang = -1.9 + f * 2 * math.pi * 0.94
            press = (0.55 + 0.45 * math.sin(math.pi * min(1, f * 1.3))) * (1 - 0.45 * f)
            rr = R + 8 * math.sin(f * 9 + seed) + o * w * press * 0.5
            x, y = cx + rr * math.cos(ang), cy + rr * math.sin(ang)
            dry = f > 0.55 and gaps[bi, i] < (f - 0.55) * 1.4 * (0.5 + abs(o))
            if dry:
                if drawing: cr.stroke(); drawing = False
                continue
            if not drawing: cr.move_to(x, y); drawing = True
            else: cr.line_to(x, y)
        if drawing:
            cr.set_line_width(w * 0.2); cr.stroke()

T_RING = (3.6, 9.4); T_DAY = (9.6, 15.4); T_LIFE = 15.6; T_CODA = 21.6
BREATH = 4.0                                                    # 화면 속 한 호흡(초)

def draw(t):
    img = hanji().copy(); s, cr = surf()
    if t < T_RING[0] + 0.3:
        a = 1 - ramp(t, T_RING[0] - 0.2, T_RING[0] + 0.3); enso(cr, 540, 1000, 300, ramp(t, 0.3, 3.0), a, 3, 70)
    if T_RING[0] - 0.2 < t < T_DAY[0] + 0.5:                    # 숨마다 번지는 고리
        a = ramp(t, T_RING[0] - 0.2, T_RING[0] + 0.3) * (1 - ramp(t, T_DAY[0], T_DAY[0] + 0.5))
        for k in range(4):
            t0 = T_RING[0] + k * 1.45; u = ramp(t, t0, t0 + 1.4)
            if u <= 0: continue
            blot(cr, 540, 1000, 60 + 360 * expo_out(u), a * (1 - 0.65 * u), 1.0)
        ph = ((t - T_RING[0]) % 1.45) / 1.45
        txt(cr, ['Breathe in · 들이쉬고', 'Breathe out · 내쉬고'][int(ph * 2) % 2], 540, 1520, 46, MUK, a * 0.85, fam=SERIF)
    if T_DAY[0] - 0.2 < t < T_LIFE + 0.6:                       # 하루: 점이 빼곡히
        a = ramp(t, T_DAY[0] - 0.2, T_DAY[0] + 0.3) * (1 - ramp(t, T_LIFE, T_LIFE + 0.6))
        n = int(720 * smooth(ramp(t, T_DAY[0], T_DAY[1] - 0.8))); r = np.random.default_rng(5)
        cols, rows = 24, 30
        for i in range(n):
            c, rw = i % cols, i // cols; x = 80 + c * 38 + r.uniform(-4, 4); y = 560 + rw * 36 + r.uniform(-4, 4)
            blot(cr, x, y, 12 + r.uniform(-4, 5), a * r.uniform(0.6, 1.0), r.uniform(0.5, 1.2))
        b2 = a * ramp(t, T_DAY[1] - 1.2, T_DAY[1] - 0.7)
        txt(cr, '17,000 – 29,000 a day', 540, 1720, 56, MUK, b2, fam=SERIF); txt(cr, '하루 1만 7천 ~ 2만 9천 번', 540, 1790, 48, SEAL, b2)
    if t >= T_LIFE:                                             # 평생: 큰 일원상
        a = ramp(t, T_LIFE, T_LIFE + 0.4)
        enso(cr, 540, 1050, 360, ramp(t, T_LIFE + 0.2, T_LIFE + 3.2), a, 9, 110)
        txt(cr, '500–800 million', 540, 1080, 70, MUK, a * ramp(t, T_LIFE + 2.0, T_LIFE + 2.6), fam=SERIF)
        txt(cr, '평생 5억~8억 번', 540, 1160, 58, SEAL, a * ramp(t, T_LIFE + 2.2, T_LIFE + 2.8))
    s.flush(); L = arr(s); L = cv2.GaussianBlur(L, (0, 0), 1.3 * SC)
    img = img * (1 - L[..., 3:4]) + L[..., :3]
    return img

def sound(path):
    m = S.Mix(EP['DUR'], 21); tc = EP['t_coda']
    m.put('mus', 0.3, S.geomungo(73.4, 3.2, 0.6, seed=1)); m.put('fx', 0.3, S.swoosh(2.7, 0.12, 300, 3000))
    for k in range(4):
        t0 = T_RING[0] + k * 1.45; m.put('amb', t0, S.breath(1.45, 0.35, k)); m.put('mus', t0, S.geomungo([98.0, 110.0, 130.8, 110.0][k], 2.0, 0.45, seed=10 + k))
    for k in range(int((T_DAY[1] - T_DAY[0]) / 0.5)):
        m.put('fx', T_DAY[0] + k * 0.5, S.tok(500 + 30 * (k % 5), 0.12))
    m.put('amb', T_DAY[0], S.breath(3.0, 0.3, 20)); m.put('amb', T_DAY[0] + 3, S.breath(3.0, 0.3, 21))
    m.put('fx', T_LIFE, S.buk(0.7, 52, 1.8, seed=30)); m.put('mus', T_LIFE + 0.1, S.geomungo(65.4, 3.5, 0.7, bend_end=-1.0, seed=31))
    m.put('fx', T_LIFE + 0.2, S.swoosh(3.0, 0.2, 200, 2500))
    m.put('amb', tc, S.breath(4.0, 0.4, 40)); m.put('amb', tc + 4.2, S.breath(4.5, 0.4, 41))
    for i in range(3): m.put('mus', tc + 0.8 + i * STEP, S.geomungo([110.0, 98.0, 73.4][i], 3.0, 0.5, seed=50 + i))
    m.put('fx', EP['t_end'] + 0.2, S.buk(0.6, 60, 1.6, seed=60))
    m.write(path, rev_mus=2.2, wet_mus=0.3)

EP = finalize(dict(t_coda=T_CODA, draw=draw, sound=sound, end_icon='drop', grain=0.004,
    title_en_card='20,000 BREATHS A DAY', title_ko_card='하루 2만 번의 숨',
    pal=dict(hi=SEAL, endbg=HANJI),
    card_style=dict(box=None, ink=MUK, hi=SEAL, y=170, fe=SERIF, fk=SERIF, se=62, sk=56),
    cards=[(0.3, 3.4, ['How many times', 'do you *breathe* in a day?'], ['나는 하루에', '몇 번 *숨을 쉴까*?']),
           (3.8, 9.4, ['At rest: *12 to 20*', 'breaths a minute.'], ['가만히 있을 때', '1분에 *12~20번*']),
           (9.8, 15.4, ['That’s *17,000 to 29,000*', 'breaths a day.'], ['하루 *1만 7천~2만 9천 번*']),
           (15.8, 21.4, ['Over 80 years:', '*500 to 800 million*.'], ['80년이면', '*5억~8억 번*'])],
    coda=[('About twenty thousand times a day,', '하루 2만 번 남짓,'), ('you breathe without being asked.', '시키지 않아도 숨은 쉬어진다'), ('Take the next one on purpose.', '다음 한 번은, 일부러 깊게')],
    coda_style=dict(dim=0.75, blur=6, tint=HANJI, ink=MUK, hi=SEAL, fe=SERIF, fk=SERIF, fk2=SERIF),
    sources=['Adult resting respiratory rate 12–20 breaths per minute (American Lung Association; NCBI StatPearls).', 'Daily and lifetime totals calculated from that range.'],
    yt=dict(title_en='You Take About 20,000 Breaths a Day #Shorts', title_ko='나는 하루 약 2만 번 숨을 쉰다')))

if __name__ == '__main__': main(EP)
