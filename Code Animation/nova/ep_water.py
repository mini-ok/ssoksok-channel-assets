"""〈지구의 물을 공 하나로〉 다시 만들기 — 번지는 수채화(냉압지 결, 가장자리 물감 고임, 번짐 꽃), 소리는 시냇물·물방울·칼림바.
사실(USGS Water Science School "How Much Water is There on Earth?"): 지구 지름 12,742 km, 모든 물 공 지름 1,385 km,
액체 민물 272.8 km, 호수·강 56.2 km.
"""
import math, numpy as np, cv2, cairo
from base import *
import sfx as S
sys.path.insert(0, os.path.join(HERE, "..", "_kit")); from vfx.ink import composite, pigment

R_E = 6371.0
def _on(ang, r): a = math.radians(ang); return (R_E + r) * math.cos(a), (R_E + r) * math.sin(a)
WX, WY = _on(50, 692.5); FX, FY = _on(66, 136.4); LX, LY = _on(72, 28.1)
CAMS = [(0, 0, 0, 15500), (3.6, 0, 0, 15500), (6.2, WX, WY, 2300), (8.8, WX, WY, 2300), (11.0, FX, FY, 470),
        (12.8, FX, FY, 470), (15.0, LX, LY, 110), (16.9, LX, LY, 110), (19.6, 600, 1900, 15500)]
SCY = 1060
K_EARTH = pigment((0.78, 0.62, 0.42)); K_GREEN = pigment((0.55, 0.68, 0.42))
K_BLUE = pigment((0.18, 0.38, 0.78)); K_FRESH = pigment((0.35, 0.62, 0.90)); K_LAKE = pigment((0.50, 0.80, 0.95))
K_INK = pigment((0.20, 0.17, 0.15))
OBJS = [dict(x=0, y=0, r=R_E, k=K_EARTH, t_in=0.0, a=0.55, seed=1, en='Earth, water removed', ko='물을 뺀 지구', s='12,742 km · 지름 1만 2,742km', lab=(0.8, 4.4)),
        dict(x=WX, y=WY, r=692.5, k=K_BLUE, t_in=4.6, a=0.85, seed=2, en='All water on Earth', ko='지구의 모든 물', s='1,385 km · 지름 1,385km', lab=(5.4, 8.6)),
        dict(x=FX, y=FY, r=136.4, k=K_FRESH, t_in=8.6, a=0.8, seed=3, en='Liquid fresh water', ko='액체 상태 민물', s='272.8 km · 지름 272.8km', lab=(9.4, 12.8)),
        dict(x=LX, y=LY, r=28.1, k=K_LAKE, t_in=12.6, a=0.85, seed=4, en='Lakes & rivers', ko='호수와 강', s='56.2 km · 지름 56.2km', lab=(13.4, 17.0))]

_r = np.random.default_rng(3)
def _paper():
    g = sum(cv2.resize(_r.standard_normal((max(2, H // d), max(2, W // d))).astype(np.float32), (W, H), interpolation=cv2.INTER_CUBIC) * w
            for d, w in ((2, 0.5), (6, 0.8), (24, 0.6), (90, 0.5)))
    return (g - g.min()) / (g.max() - g.min())
GRAIN = _paper()
PAPER = np.stack([0.90 + 0.05 * GRAIN, 0.95 + 0.03 * GRAIN, 0.97 + 0.02 * GRAIN], -1).astype(np.float32)   # BGR
_yy, _xx = np.mgrid[0:H, 0:W].astype(np.float32)

def cam(t):
    for (t0, x0, y0, w0), (t1, x1, y1, w1) in zip(CAMS, CAMS[1:]):
        if t <= t1:
            u = 0.5 - 0.5 * math.cos(math.pi * ramp(t, t0, t1))
            lw = lerp(math.log(w0), math.log(w1), u); wa = math.exp(lw)
            # 중심은 화면 비율로 보간(줌과 이동이 따로 놀지 않게)
            f = (wa - w0) / (w1 - w0) if abs(w1 - w0) > 1e-6 else u
            return lerp(x0, x1, f), lerp(y0, y1, f), wa
    return CAMS[-1][1:]

def wobble(theta, seed, n=7):
    r = np.random.default_rng(seed); out = 0
    for k in range(2, 2 + n):
        out = out + np.sin(k * theta + r.uniform(0, 6.283)) * r.uniform(0.3, 1) / k
    return out

def wash(o, t, cx, cy, sc):
    """한 덩어리 물감: 고른 바탕 + 종이 결 + 가장자리 고임 + 안쪽 번짐 꽃."""
    gp = ramp(t, o['t_in'], o['t_in'] + 1.2)
    if gp <= 0: return None
    px = (o['x'] - cx) * sc * SC + W / 2; py = SCY * SC - (o['y'] - cy) * sc * SC
    rp = o['r'] * sc * SC * lerp(0.75, 1.0, expo_out(gp))
    if rp < 0.6 * SC or px + rp < -50 or px - rp > W + 50 or py + rp < -50 or py - rp > H + 50: return None
    x0, x1 = int(max(0, px - rp * 1.1 - 4)), int(min(W, px + rp * 1.1 + 4)); y0, y1 = int(max(0, py - rp * 1.1 - 4)), int(min(H, py + rp * 1.1 + 4))
    if x1 <= x0 or y1 <= y0: return None
    X = _xx[y0:y1, x0:x1] - px; Y = _yy[y0:y1, x0:x1] - py
    d = np.hypot(X, Y); th = np.arctan2(Y, X)
    re = rp * (1 + 0.025 * wobble(th, o['seed']) + 0.012 * wobble(th * 3, o['seed'] + 9))
    soft = min(3 * SC, max(1.2 * SC, rp * 0.01))
    m = np.clip((re - d) / soft, 0, 1)
    ew = min(16 * SC, max(3 * SC, rp * 0.045))
    edge = np.exp(-((re - d) / ew) ** 2) * m
    g = GRAIN[y0:y1, x0:x1]
    amt = o['a'] * gp * (m * (0.55 + 0.35 * g) + 0.7 * edge)
    # 번짐 꽃: 물체에 붙은 자리에서 물감이 밀려난 밝은 자국
    rr = np.random.default_rng(o['seed'] + 50)
    for _ in range(4):
        ang = rr.uniform(0, 6.283); dist = rr.uniform(0.2, 0.7) * rp; br = rr.uniform(0.12, 0.25) * rp
        bx, by = math.cos(ang) * dist, math.sin(ang) * dist
        db = np.hypot(X - bx, Y - by) / br; bth = np.arctan2(Y - by, X - bx)
        rb = 1 + 0.15 * wobble(bth * 2, int(ang * 100))
        inside = np.clip((rb - db) * 4, 0, 1); ring = np.exp(-((db - rb) / 0.08) ** 2)
        amt = amt * (1 - 0.45 * inside) + 0.25 * ring * m * o['a'] * gp
    full = np.zeros((H, W), np.float32); full[y0:y1, x0:x1] = amt
    return full, (px, py, rp)

def continents(t, cx, cy, sc, o_amt):
    """지구 위 초록 물감 번짐(세계 좌표에 고정)."""
    out = np.zeros((H, W), np.float32)
    rr = np.random.default_rng(77)
    for _ in range(9):
        ang = rr.uniform(0, 6.283); dist = rr.uniform(0.1, 0.8) * R_E; r = rr.uniform(0.12, 0.3) * R_E
        x, y = math.cos(ang) * dist, math.sin(ang) * dist
        px = (x - cx) * sc * SC + W / 2; py = SCY * SC - (y - cy) * sc * SC; rp = r * sc * SC
        if rp < 2 or px + rp < 0 or px - rp > W or py + rp < 0 or py - rp > H: continue
        x0, x1 = int(max(0, px - rp * 1.2)), int(min(W, px + rp * 1.2)); y0, y1 = int(max(0, py - rp * 1.2)), int(min(H, py + rp * 1.2))
        if x1 <= x0 or y1 <= y0: continue
        X = _xx[y0:y1, x0:x1] - px; Y = _yy[y0:y1, x0:x1] - py; d = np.hypot(X, Y); th = np.arctan2(Y, X)
        re = rp * (1 + 0.18 * wobble(th, int(ang * 1000)))
        m = np.clip((re - d) / max(1.5, rp * 0.03), 0, 1); edge = np.exp(-((re - d) / max(2, rp * 0.06)) ** 2) * m
        out[y0:y1, x0:x1] += 0.45 * m * (0.6 + 0.4 * GRAIN[y0:y1, x0:x1]) + 0.35 * edge
    return out * o_amt

def draw(t):
    cx, cy, w = cam(t); sc = DW / w
    layers = []; geo = []
    for i, o in enumerate(OBJS):
        r = wash(o, t, cx, cy, sc)
        if r is None: geo.append(None); continue
        amt, g = r; layers.append((amt, o['k'])); geo.append(g)
        if i == 0: layers.append((continents(t, cx, cy, sc, ramp(t, 0.4, 1.6)) * (amt > 0.05), K_GREEN))
    img = composite(PAPER, layers)
    # 펜 지시선과 손글씨 이름
    s, cr = surf()
    for o, g in zip(OBJS, geo):
        a = ramp(t, *o['lab'][:1], ) if False else ramp(t, o['lab'][0], o['lab'][0] + 0.5) * (1 - ramp(t, o['lab'][1] - 0.4, o['lab'][1]))
        if a <= 0 or g is None: continue
        px, py, rp = (v / SC for v in g)
        ty = 1560; tx = 540
        ex, ey = px, py + rp
        if ey > ty - 90: ex, ey = px - rp * 0.7, py + rp * 0.7
        cr.set_source_rgba(0.2, 0.17, 0.15, 0.8 * a); cr.set_line_width(2.4)
        cr.move_to(ex, ey); cr.curve_to(ex, ey + 60, tx, ty - 140, tx, ty - 70); cr.stroke()
        cr.arc(ex, ey, 5, 0, 6.283); cr.fill()
        txt(cr, o['en'], tx, ty, 50, (0.20, 0.17, 0.15), a, fam=BOLD); txt(cr, o['ko'], tx, ty + 62, 46, (0.20, 0.17, 0.15), a, fam=BOLD)
        txt(cr, o['s'], tx, ty + 122, 34, (0.25, 0.40, 0.65), a, fam=BOLD)
    if 17.6 < t < EP_TC:
        a = ramp(t, 17.8, 18.4) * (1 - ramp(t, EP_TC - 0.4, EP_TC))
        g = geo[3]
        if g is not None:
            px, py, rp = (v / SC for v in g)
            cr.set_source_rgba(0.25, 0.40, 0.65, a); cr.set_line_width(3); cr.arc(px, py, max(16, rp + 12), 0, 6.283); cr.stroke()
    return over(img, s)

EP_TC = 22.2

def sound(path):
    m = S.Mix(EP['DUR'], 61); tc = EP['t_coda']; b = 60 / 84
    m.put('amb', 0, S.stream(EP['t_end'] + 1, 0.35))
    pent = [523.3, 587.3, 659.3, 784.0, 880.0, 1046.5]; r = np.random.default_rng(4)
    t = 0.4; k = 0
    while t < tc - 0.3:
        if r.random() < 0.7: m.put('mus', t, S.kalimba(pent[[0, 2, 4, 3, 1, 3, 5, 2][k % 8]] * (0.5 if k % 16 >= 8 else 1), 1.6, 0.30))
        if k % 4 == 0: m.put('mus', t, S.kalimba(pent[0] / 2 if (k // 8) % 2 == 0 else pent[3] / 2, 2.0, 0.22))
        t += b / 2; k += 1
    for o in OBJS:
        m.put('fx', o['t_in'] + 0.1, S.drop(700 + 300 * o['seed'], 0.6))
        for j, f in enumerate([392.0, 523.3, 659.3, 784.0]): m.put('mus', o['t_in'] + 0.15 + j * 0.07, S.pluck(f, 1.6, 0.18, 0.7, seed=j))
    m.put('fx', 17.8, S.drop(2200, 0.5)); m.put('fx', 18.1, S.drop(1800, 0.3))
    m.put('amb', tc, S.drone([130.8, 196.0, 261.6], EP['t_end'] - tc, 0.15, 'sine'))
    for i in range(3): m.put('mus', tc + 0.8 + i * STEP, S.kalimba([784.0, 659.3, 523.3][i], 3.0, 0.35))
    m.put('fx', EP['t_end'] + 0.2, S.drop(1400, 0.5))
    m.write(path, rev_mus=2.6, wet_mus=0.35)

EP = finalize(dict(t_coda=EP_TC, draw=draw, sound=sound, end_icon='drop', grain=0.0,
    title_en_card='ALL THE WATER ON EARTH', title_ko_card='지구의 물을 공 하나로',
    pal=dict(hi=(0.18, 0.38, 0.78), endbg=(0.97, 0.95, 0.90)),
    card_style=dict(box=None, ink=(0.20, 0.17, 0.15), hi=(0.18, 0.40, 0.80), y=150, fe=BLK, fk=BLK),
    cards=[(0.3, 3.8, ["All of Earth's water", 'in one ball. *How big?*'], ['지구의 물을 전부 모으면', '*얼마나 클까?*']),
           (4.9, 8.6, ['Oceans, ice, groundwater,', 'clouds — *all of it*.'], ['바다·얼음·지하수·구름까지', '*전부* 합쳐도 이만하다']),
           (9.0, 12.8, ['Liquid fresh water:', 'just *272.8 km* across.'], ['그중 액체 상태 민물은', '지름 *272.8km*']),
           (13.0, 17.0, ['Lakes and rivers:', 'a *56 km* drop.'], ['호수와 강의 물은', '지름 *56km* 물방울 하나']),
           (17.4, 22.0, ['Most of the water we use', 'every day comes from *that speck*.'], ['우리가 매일 쓰는 물은', '대부분 *저 작은 점*에서 온다'])],
    coda=[("Eight billion people", "80억 명이"), ("share that one small drop.", "저 작은 물방울 하나를 나눠 마신다"), ("Every glass of water is a gift.", "물 한 잔은 선물이다")],
    coda_style=dict(dim=0.7, blur=10, tint=(0.97, 0.95, 0.90), ink=(0.20, 0.17, 0.15), hi=(0.18, 0.40, 0.80)),
    sources=['Source: USGS Water Science School, "How Much Water is There on Earth?"'],
    yt=dict(title_en='All of Earth’s Water in One Ball — It’s Tiny #Shorts', title_ko='지구의 물을 공 하나로 모으면')))

if __name__ == '__main__': main(EP)
