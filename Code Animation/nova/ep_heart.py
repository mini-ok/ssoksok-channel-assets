"""〈평생 심장은 몇 번 뛸까〉 다시 만들기 — 마티스풍 색종이 오려 붙이기(가위 자국 가장자리, 종이 그림자, 해초·별 모양), 소리는 큰북 심장 소리와 피치카토 현악.
가정: 분당 70회(성인 안정 시 정상 60~100회, American Heart Association). 1시간 4,200 / 하루 100,800 / 1년 약 3,680만 / 80년 약 29억 5천만(≈ 30억).
"""
import math, numpy as np, cv2, cairo
from base import *
import sfx as S

CREAM = (0.96, 0.94, 0.88); RED = (0.86, 0.16, 0.14); BLUE = (0.10, 0.25, 0.62); YEL = (0.98, 0.76, 0.12)
GRN = (0.12, 0.55, 0.38); PINK = (0.96, 0.55, 0.62); ORA = (0.96, 0.45, 0.12); INK = (0.12, 0.10, 0.10)
T0 = 3.2; SEG = 2.7
STEPS = [(70, '1 minute', '1분', '70 beats', '70번', BLUE), (4200, '1 hour', '1시간', '4,200 beats', '4,200번', GRN),
         (100800, '1 day', '하루', '100,800 beats', '10만 800번', ORA), (36.8e6, '1 year', '1년', '36.8 million', '3,680만 번', PINK),
         (2.95e9, '80 years', '80년', '≈ 2.9 billion', '약 29억 번', RED)]
T_END_STEPS = T0 + len(STEPS) * SEG; T_CODA = T_END_STEPS + 4.4
_r = np.random.default_rng(31)
_g = cv2.resize(_r.standard_normal((H // 3 + 1, W // 3 + 1)).astype(np.float32), (W, H)) * 0.015
PAPER = np.array(CREAM[::-1], np.float32) * (1 + _g[..., None])

def cut(pts, seed):
    """가위로 오린 듯한 가장자리: 작은 꺾임과 저주파 흔들림."""
    r = np.random.default_rng(seed); P = np.asarray(pts, float)
    if len(P) < 40:
        Q = []
        for a, b in zip(P, np.roll(P, -1, 0)):
            for k in range(16): Q.append(a + (b - a) * k / 16)
        P = np.array(Q); P = P + r.normal(0, 1.2, P.shape)
        return P
    n = len(P)
    c = P.mean(0); d = P - c
    k = np.arange(n) / n * 6.283
    wob = 1 + 0.018 * np.sin(k * 3 + r.uniform(0, 6)) + 0.01 * np.sin(k * 7 + r.uniform(0, 6))
    P = c + d * wob[:, None]
    keep = np.sort(r.choice(n, max(8, n // 3), replace=False))           # 꺾인 면(직선 토막)
    return P[keep]

def heart_pts(cx, cy, s, n=120):
    th = np.linspace(0, 6.283, n, endpoint=False)
    x = 16 * np.sin(th) ** 3; y = -(13 * np.cos(th) - 5 * np.cos(2 * th) - 2 * np.cos(3 * th) - np.cos(4 * th))
    return np.stack([cx + x * s, cy + y * s], 1)

def algae_pts(cx, cy, R, rot, seed, n=160):
    r = np.random.default_rng(seed); th = np.linspace(0, 6.283, n, endpoint=False)
    lobes = r.integers(5, 9)
    rr = R * (0.55 + 0.45 * np.abs(np.sin(lobes * th / 2 + r.uniform(0, 3))) ** 0.6) * (1 + 0.1 * np.sin(3 * th + r.uniform(0, 6)))
    x = rr * np.cos(th) * 0.55; y = rr * np.sin(th) * 1.15
    c, s = math.cos(rot), math.sin(rot)
    return np.stack([cx + x * c - y * s, cy + x * s + y * c], 1)

def star_pts(cx, cy, R, rot, k=7):
    th = np.linspace(0, 6.283, 2 * k, endpoint=False) + rot
    rr = np.where(np.arange(2 * k) % 2 == 0, R, R * 0.45)
    return np.stack([cx + rr * np.cos(th), cy + rr * np.sin(th)], 1)

def paste(cr, pts, col, a=1.0, sh=True):
    if a <= 0: return
    if sh:
        cr.set_source_rgba(0, 0, 0, 0.16 * a); cr.move_to(*(pts[0] + (5, 7))); [cr.line_to(*(p + (5, 7))) for p in pts[1:]]; cr.close_path(); cr.fill()
    cr.set_source_rgba(*col, a); cr.move_to(*pts[0]); [cr.line_to(*p) for p in pts[1:]]; cr.close_path(); cr.fill()

DECOR = []
_d = np.random.default_rng(5)
for i, (_, *_rest, col) in enumerate(STEPS):
    for j in range(3 + 2 * i):
        while True:
            ang = _d.uniform(0, 6.283); rad = _d.uniform(330, 470); xx, yy_ = 540 + rad * math.cos(ang), 860 + rad * math.sin(ang) * 1.05
            if 560 < yy_ < 1200 and 40 < xx < 1040: break
        DECOR.append((i, xx, yy_, _d.uniform(28, 62), _d.uniform(0, 6.283),
                      [BLUE, GRN, YEL, PINK, ORA][(i + j) % 5], 'star' if _d.random() < 0.35 else 'algae', int(_d.integers(1e6)), _d.uniform(0, 0.8)))

def value_at(t):
    if t < T0: return 0.0
    i = min(len(STEPS) - 1, int((t - T0) / SEG)); u = expo_out(ramp(t - T0 - i * SEG, 0, 1.6))
    v0 = STEPS[i - 1][0] if i > 0 else 1.0; v1 = STEPS[i][0]
    return math.exp(lerp(math.log(v0), math.log(v1), u)), i

def beat_phase(t):
    """심장 박동 위상: 처음엔 분당 70회, 단계마다 빨라졌다가(시간 압축) 끝나면 다시 70회."""
    if t < T0 or t > T_END_STEPS + 0.6: return (t * 70 / 60) % 1
    k = (t - T0) / (T_END_STEPS - T0)
    return (t * 70 / 60 * (1 + 7 * k * k)) % 1

def draw(t):
    s, cr = surf()
    st = None
    if t >= T0: v, st = value_at(t)
    # 장식: 단계마다 해초·별 조각이 붙는다
    for (i, x, y, R, rot, col, kind, seed, dl) in DECOR:
        t_in = T0 + i * SEG + 0.3 + dl
        if t < t_in: continue
        u = ramp(t, t_in, t_in + 0.5); k = back_out(u, 2.2)
        pts = algae_pts(x, y, R * k, rot + (1 - u) * 1.2 + 0.05 * math.sin(t * 0.8 + seed), seed) if kind == 'algae' else star_pts(x, y, R * 0.8 * k, rot + (1 - u))
        paste(cr, cut(pts, seed), col, 1.0)
    # 심장
    ph = beat_phase(t); pulse = math.exp(-((ph - 0.05) / 0.06) ** 2) + 0.6 * math.exp(-((ph - 0.28) / 0.06) ** 2)
    hs = 15.5 * (1 + 0.07 * pulse) * back_out(ramp(t, 0.2, 0.8), 1.8)
    if hs > 0.1: paste(cr, cut(heart_pts(540, 880, hs), 7), RED)
    # 단계 띠: 쌓이는 색종이 띠
    if st is not None:
        for j in range(st + 1):
            u = ramp(t, T0 + j * SEG, T0 + j * SEG + 0.4); y = 1290 + j * 0 if j == st else 1290
            if j < st: continue
            col = STEPS[j][5]; k = back_out(u, 1.6)
            w = 640 * k
            pts = cut(np.array([(540 - w / 2, 1240), (540 + w / 2, 1232), (540 + w / 2 + 6, 1330), (540 - w / 2 - 4, 1338)]), 40 + j)
            paste(cr, pts, col)
            txt(cr, f'{STEPS[j][1]} · {STEPS[j][2]}', 540, 1302, 50, CREAM, u, fam=BLK)
        # 숫자판
        pts = cut(np.array([(150, 1380), (930, 1372), (936, 1600), (144, 1606)]), 99)
        paste(cr, pts, INK, ramp(t, T0, T0 + 0.4))
        en = f'{v:,.0f}' if v < 1e6 else (f'{v / 1e6:,.1f} million' if v < 1e9 else f'{v / 1e9:,.2f} billion')
        ko = f'{v:,.0f}번' if v < 1e5 else (f'{v / 1e4:,.0f}만 번' if v < 1e8 else f'{v / 1e8:,.1f}억 번')
        txt(cr, en, 540, 1495, 96 if v < 1e6 else 80, CREAM, ramp(t, T0, T0 + 0.4), fam=BLK)
        txt(cr, ko, 540, 1570, 52, YEL, ramp(t, T0, T0 + 0.4), fam=BLK)
    if t > T_END_STEPS:                                   # 쉬지 않은 날을 세는 작은 표
        a = ramp(t, T_END_STEPS + 0.6, T_END_STEPS + 1.2)
        txt(cr, '0 days off · 쉰 날 0일', 540, 1700, 44, RED, a, fam=BLK)
    img = PAPER.copy()
    return over(img, s)

def sound(path):
    m = S.Mix(EP['DUR'], 91); tc = EP['t_coda']
    t = 0.25
    while t < tc:                                         # 쿵-쿵 심장(시간 압축 구간에선 빨라짐)
        ph_rate = 70 / 60
        if T0 <= t <= T_END_STEPS:
            k = (t - T0) / (T_END_STEPS - T0); ph_rate *= (1 + 7 * k * k)
        if t > T_END_STEPS + 0.6: ph_rate = 70 / 60
        g = 0.9 if not (T0 <= t <= T_END_STEPS) else 0.6
        m.put('fx', t, S.taiko(g, 64)); m.put('fx', t + 0.23 / max(1, ph_rate / 1.17) ** 0.5, S.taiko(g * 0.55, 74))
        t += 1 / ph_rate
    notes = [392.0, 493.9, 587.3, 659.3, 587.3, 493.9, 440.0, 392.0]
    for i in range(len(STEPS)):
        t0 = T0 + i * SEG
        for j in range(4): m.put('mus', t0 + j * 0.16, S.pizz(notes[(i * 2 + j) % 8] * (1 + 0.5 * (i >= 3)), 0.7, 0.35, seed=j))
        m.put('fx', t0, S.swoosh(0.4, 0.25, 800, 5000, seed=i))
    for j, f in enumerate([196.0, 246.9, 293.7, 392.0, 493.9]): m.put('mus', T_END_STEPS + 0.1 + j * 0.1, S.pizz(f, 1.2, 0.4, seed=j))
    m.put('amb', tc, S.drone([98.0, 146.8, 196.0], EP['t_end'] - tc, 0.18, 'saw'))
    for i, ch in enumerate([[196.0, 293.7, 392.0], [174.6, 261.6, 349.2], [196.0, 246.9, 392.0]]):
        for j, f in enumerate(ch): m.put('mus', tc + 0.8 + i * STEP + j * 0.06, S.pizz(f, 1.6, 0.35, seed=j))
    m.write(path, rev_mus=2.0, wet_mus=0.28, rev_fx=1.4, wet_fx=0.2)

EP = finalize(dict(t_coda=T_CODA, draw=draw, sound=sound, end_icon='heart', grain=0.0,
    title_en_card='HOW MANY HEARTBEATS?', title_ko_card='평생 심장은 몇 번 뛸까',
    pal=dict(hi=RED, endbg=CREAM),
    card_style=dict(box=None, ink=INK, hi=RED, y=150, fe=BLK, fk=BLK),
    cards=[(0.3, T0 + 0.2, ['How many times will', 'your heart *beat*?'], ['내 심장은 평생', '*몇 번* 뛸까?']),
           (T_END_STEPS, T_END_STEPS + 4.2, ['About *3 billion* beats,', 'never a day off.'], ['평생 약 *30억 번*,', '하루도 쉬지 않는다'])],
    coda=[("Three billion beats,", "30억 번을 뛰는 동안"), ("and it never once asked for thanks.", "한 번도 고맙다는 말을 바라지 않았다"), ("Tonight, put a hand on your chest.", "오늘 밤, 가슴에 손을 얹어 보자")],
    coda_style=dict(dim=0.7, blur=10, tint=CREAM, ink=INK, hi=RED),
    sources=['Assuming 70 beats per minute. Normal adult resting heart rate: 60–100 (American Heart Association).'],
    yt=dict(title_en='How Many Times Will Your Heart Beat? #Shorts', title_ko='내 심장은 평생 몇 번 뛸까')))

if __name__ == '__main__': main(EP)
