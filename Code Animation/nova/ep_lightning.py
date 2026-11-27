"""〈번개는 해보다 뜨겁다〉 — 스테인드글라스(보로노이 유리 조각, 납선, 뒤에서 비치는 빛), 소리는 파이프오르간과 천둥.
사실(NOAA SciJinks, NWS): 번개는 주변 공기를 약 30,000°C까지 달군다(해 표면의 약 5배). 해 표면(광구) 약 5,500°C(NASA).
뜨거운 통로는 몇 cm 굵기이고 순식간에 식는다. 번쩍인 뒤 천둥까지 초를 세어 3으로 나누면 대략 km.
"""
import math, numpy as np, cv2, cairo
from base import *
import sfx as S

T_TEMP = 3.8; T_WIDE = 8.8; T_COUNT = 13.4; T_CODA = 19.4
FLASHES = [1.2, 9.2, T_COUNT + 0.4]
COUNT_S = 6                                                  # 6초 → 약 2 km

def _cells():
    r = np.random.default_rng(4)
    seed = np.ones((H, W), np.uint8) * 255
    pts = np.c_[r.uniform(0, W, 900), r.uniform(0, H, 900)].astype(int)
    seed[np.clip(pts[:, 1], 0, H - 1), np.clip(pts[:, 0], 0, W - 1)] = 0
    _, lab = cv2.distanceTransformWithLabels(seed, cv2.DIST_L2, 5, labelType=cv2.DIST_LABEL_PIXEL)
    # 고정 구역(번개 몸통·온도 막대 두 개·땅)으로 조각을 나눈다
    s, cr = surf(); cr.set_source_rgba(0, 0, 0, 1)
    reg = np.zeros((H, W), np.int32)
    def mask(fn):
        s2, c2 = surf(); c2.set_source_rgba(0, 0, 0, 1); fn(c2); c2.fill(); return arr(s2)[..., 3] > 0.5
    bolt = mask(lambda c: (c.move_to(560, 470), c.line_to(500, 760), c.line_to(575, 770), c.line_to(470, 1120), c.line_to(520, 1125), c.line_to(430, 1420),
                          c.line_to(640, 1010), c.line_to(560, 1000), c.line_to(660, 720), c.line_to(590, 712), c.line_to(650, 470), c.close_path()))
    bar1 = mask(lambda c: c.rectangle(190, 560, 170, 900)); bar2 = mask(lambda c: c.rectangle(720, 560, 170, 900))
    ground = mask(lambda c: (c.move_to(0, 1560), c.curve_to(300, 1480, 700, 1600, DW, 1500), c.line_to(DW, DH), c.line_to(0, DH), c.close_path()))
    reg[ground] = 4; reg[bar1] = 2; reg[bar2] = 3; reg[bolt] = 1
    L = lab.astype(np.int64) * 8 + reg
    _, L = np.unique(L, return_inverse=True); L = L.reshape(H, W)
    edge = np.zeros((H, W), np.uint8)
    edge[:, 1:] |= (L[:, 1:] != L[:, :-1]); edge[1:, :] |= (L[1:, :] != L[:-1, :])
    lead = cv2.dilate(edge, np.ones((max(3, int(5 * SC)),) * 2, np.uint8)).astype(np.float32)
    lead = cv2.GaussianBlur(lead, (0, 0), 0.8 * SC)
    return L, lead, reg
LAB, LEAD, REG = _cells()
NL = LAB.max() + 1; CNT = np.bincount(LAB.ravel(), minlength=NL).astype(np.float32)
_r = np.random.default_rng(9)
GLASS = (0.86 + 0.14 * cv2.GaussianBlur(_r.random((H, W)).astype(np.float32), (0, 0), 6 * SC))[..., None]
CELLVAR = _r.uniform(0.82, 1.12, NL).astype(np.float32)

def flash(t):
    return max([math.exp(-max(0, t - f) / 0.12) * (t >= f) + 0.6 * math.exp(-max(0, t - f - 0.18) / 0.08) * (t >= f + 0.18) for f in FLASHES] + [0])

def paint(t):
    s, cr = surf(); fl = min(1.0, flash(t))
    g = cairo.LinearGradient(0, 0, 0, DH); g.add_color_stop_rgb(0, lerp(0.10, 0.55, fl), lerp(0.08, 0.50, fl), lerp(0.35, 0.85, fl))
    g.add_color_stop_rgb(0.7, lerp(0.25, 0.70, fl), lerp(0.12, 0.45, fl), lerp(0.45, 0.85, fl)); cr.set_source(g); cr.paint()
    pa = paint_arr = None
    return s, cr, fl

def draw(t):
    s, cr, fl = paint(t)
    img = arr(s)[..., :3]
    regcol = {1: (0.95, 0.95, 0.75) if fl > 0.15 else (0.28, 0.20, 0.48), 4: (0.10, 0.28, 0.18)}
    col = img.copy()
    for rg, c in regcol.items():
        m = REG == rg; col[m] = np.array(c[::-1], np.float32) * (1 if rg == 1 else lerp(1, 1.8, fl))
    # 온도 막대: 해 5,500°C / 번개 30,000°C
    ta = ramp(t, T_TEMP, T_TEMP + 0.5) * (1 - ramp(t, T_WIDE - 0.3, T_WIDE))
    if ta > 0:
        yy = np.arange(H)[:, None] / SC
        for rg, frac, cc in ((2, 5500 / 30000, (1.0, 0.55, 0.10)), (3, 1.0, (0.85, 0.95, 1.0))):
            lvl = 1460 - 900 * frac * smooth(ramp(t, T_TEMP + 0.4, T_TEMP + 2.2))
            m = (REG == rg)
            fill = m & (yy > lvl); empty = m & ~(yy > lvl)
            col[fill] = col[fill] * (1 - ta) + np.array(cc[::-1], np.float32) * ta
            col[empty] = col[empty] * (1 - ta) + np.array((0.25, 0.18, 0.15), np.float32) * ta
    # 충격파 고리(천둥이 되는 공기의 폭발)
    wa = ramp(t, T_WIDE + 0.4, T_WIDE + 0.8) * (1 - ramp(t, T_COUNT - 0.3, T_COUNT))
    if wa > 0:
        yy, xx = np.mgrid[0:H, 0:W].astype(np.float32) / SC
        d = np.hypot(xx - 520, yy - 1000)
        for k in range(3):
            rr = ((t - T_WIDE - 0.4) * 260 + k * 120) % 600
            ring = np.exp(-((d - rr) / 30) ** 2) * wa * (1 - rr / 600)
            col = col + ring[..., None] * np.array((0.5, 0.8, 1.0), np.float32) * 2.2
    # 조각마다 평균색 → 유리
    flat = col.reshape(-1, 3)
    mean = np.stack([np.bincount(LAB.ravel(), flat[:, c], NL) / CNT for c in range(3)], 1) * CELLVAR[:, None]
    glass = mean[LAB] * GLASS
    glass = glass + cv2.GaussianBlur(np.clip(glass - 0.7, 0, 1), (0, 0), 18 * SC) * 1.2      # 빛 번짐
    out = glass * (1 - LEAD[..., None]) + np.array((0.06, 0.06, 0.07), np.float32) * LEAD[..., None]
    # 글자판
    s2, c2 = surf()
    def lab(text, x, y, size, a, colr=(1, 1, 1), fam=BLK):
        if a <= 0: return
        txt(c2, text, x + 3, y + 3, size, (0, 0, 0), a * 0.8, fam=fam); txt(c2, text, x, y, size, colr, a, fam=fam)
    if ta > 0:
        lab('Sun surface', 275, 1535, 44, ta); lab('해 표면 5,500°C', 275, 1595, 40, ta, (1.0, 0.75, 0.4))
        lab('Lightning', 805, 1535, 44, ta); lab('번개 30,000°C', 805, 1595, 40, ta, (0.8, 0.9, 1.0))
        lab('×5', 540, 1300, 110, ta * ramp(t, T_TEMP + 2.2, T_TEMP + 2.6), (1, 0.95, 0.6))
    if wa > 0:
        lab('a channel a few cm wide', 540, 1650, 50, wa); lab('몇 cm 굵기의 공기가 터진다 = 천둥', 540, 1715, 44, wa, (1, 0.9, 0.6))
    if T_COUNT < t < T_CODA:
        ca = ramp(t, T_COUNT, T_COUNT + 0.3) * (1 - ramp(t, T_CODA - 0.4, T_CODA))
        n = int(np.clip((t - FLASHES[2]) / 0.75, 0, COUNT_S))
        lab(f'{n}', 540, 1330, 220, ca * (t > FLASHES[2] + 0.2), (1, 1, 1))
        if t > FLASHES[2] + COUNT_S * 0.75:
            da = ramp(t, FLASHES[2] + COUNT_S * 0.75, FLASHES[2] + COUNT_S * 0.75 + 0.4) * ca
            lab('6 s ÷ 3 ≈ 2 km', 540, 1660, 66, da, (1, 0.9, 0.5)); lab('6초 ÷ 3 = 약 2km', 540, 1740, 54, da, (1, 1, 1))
    return over(out, s2)

def sound(path):
    m = S.Mix(EP['DUR'], 121); tc = EP['t_coda']
    chords = [[65.4, 98.0, 130.8, 196.0], [61.7, 92.5, 123.5, 185.0], [55.0, 82.4, 110.0, 164.8], [58.3, 87.3, 116.5, 174.6]]
    t0 = 0.0
    for k in range(int(tc / 4.6) + 1):
        if t0 >= tc: break
        d = min(4.8, tc - t0 + 0.3); m.put('mus', t0, S.organ(chords[k % 4], d, 0.32)); t0 += 4.6
    m.put('amb', 0, S.rain(EP['t_end'] + 1, 0.25, seed=3))
    m.put('fx', FLASHES[0] + 0.25, S.thunder(4.0, 0.9, 1)); m.put('fx', FLASHES[1] + 0.05, S.thunder(4.0, 1.0, 2))
    m.put('fx', FLASHES[2] + COUNT_S * 0.75 + 0.05, S.thunder(4.5, 1.0, 3))
    for i in range(1, COUNT_S + 1): m.put('fx', FLASHES[2] + i * 0.75, S.tick(0.35))
    m.put('fx', T_TEMP + 2.3, S.bell(1046.5, 2.5, 0.3))
    m.put('mus', tc, S.organ([65.4, 98.0, 130.8, 164.8, 196.0], EP['t_end'] - tc + 1.5, 0.35))
    for i in range(3): m.put('mus', tc + 0.8 + i * STEP, S.bell([523.3, 659.3, 784.0][i], 3.0, 0.25))
    m.write(path, rev_mus=3.5, wet_mus=0.45)

EP = finalize(dict(t_coda=T_CODA, draw=draw, sound=sound, end_icon='bolt', grain=0.0,
    title_en_card='HOTTER THAN THE SUN', title_ko_card='번개는 해보다 뜨겁다',
    pal=dict(hi=(0.35, 0.25, 0.70), endbg=(0.94, 0.93, 0.98)),
    card_style=dict(box=None, ink=(1, 1, 1), hi=(1.0, 0.88, 0.45), y=150, fe=BLK, fk=BLK),
    cards=[(0.3, 3.6, ['A bolt of lightning is', '*hotter than the Sun*.'], ['번개 한 줄기는', '*해보다 뜨겁다*']),
           (3.8, 8.6, ['About *30,000°C*:', '*5 times* the Sun’s surface.'], ['약 *3만°C*,', '해 표면의 *5배*']),
           (8.8, 13.2, ['The air explodes outward.', 'That bang is *thunder*.'], ['달궈진 공기가 터져 나간다', '그 소리가 *천둥*']),
           (13.4, 19.2, ['Count from flash to thunder,', 'divide by *3* = km away.'], ['번쩍인 뒤 천둥까지 초를 세서', '*3*으로 나누면 거리(km)'])],
    coda=[('Five times hotter than the Sun,', '해보다 다섯 배 뜨거워도'), ('it is gone in the blink of an eye.', '눈 깜박할 새에 사라진다'), ('Treasure the moment while it shines.', '빛날 때 그 순간을 아끼자')],
    coda_style=dict(dim=0.55, blur=10, tint=(0.05, 0.04, 0.12), ink=(1, 1, 1), hi=(1.0, 0.88, 0.45)),
    sources=['NOAA SciJinks: lightning heats the air to about 30,000°C (54,000°F), five times hotter than the Sun’s surface. NWS: 50,000°F.', 'Flash-to-bang: seconds ÷ 3 ≈ kilometres (sound ≈ 343 m/s).'],
    yt=dict(title_en='Lightning Is 5 Times Hotter Than the Sun #Shorts', title_ko='번개는 해 표면보다 5배 뜨겁다')))

if __name__ == '__main__': main(EP)
