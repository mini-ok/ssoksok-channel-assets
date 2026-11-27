"""〈37조 개의 나〉 — 염색한 조직을 현미경으로 보는 화풍(H&E 분홍·보라), 물방울·마림바 소리.
사실: 성인 몸 세포 약 3.72×10^13개, 그중 약 70%가 적혈구(Bianconi et al., Ann Hum Biol 2013; BioNumbers 109716).
1초에 하나씩 세면 3.72e13 / 31,557,600 ≈ 118만 년(계산). 호모 사피엔스 약 30만 년(Hublin 2017)보다 길다.
"""
import math, numpy as np, cv2, cairo
from base import *
import sfx as S

PINK = (0.93, 0.70, 0.78); LILAC = (0.45, 0.30, 0.62); NUC = (0.32, 0.18, 0.48); RBC = (0.84, 0.22, 0.28)
TILE = 1400

_T = {}
def tile():
    """세포가 빽빽한 반복 무늬(가장자리가 이어진다). 한 번 굽는다."""
    if 'v' in _T: return _T['v']
    s = cairo.ImageSurface(cairo.FORMAT_RGB24, TILE, TILE); cr = cairo.Context(s)
    cr.set_source_rgb(0.98, 0.90, 0.92); cr.paint()
    r = np.random.default_rng(37); pts = r.uniform(0, TILE, (260, 2))
    for (x, y) in pts:
        for dx in (-TILE, 0, TILE):
            for dy in (-TILE, 0, TILE):
                X, Y = x + dx, y + dy
                if -120 < X < TILE + 120 and -120 < Y < TILE + 120:
                    rr = r.uniform(42, 62) if dx == dy == 0 else 52
                    g = cairo.RadialGradient(X, Y, rr * 0.2, X, Y, rr)
                    g.add_color_stop_rgba(0, *PINK, 0.55); g.add_color_stop_rgba(0.82, *PINK, 0.75); g.add_color_stop_rgba(1, 0.78, 0.45, 0.62, 0.9)
                    cr.set_source(g); cr.save(); cr.translate(X, Y); cr.scale(1, 0.85 + 0.25 * ((x * 7 + y) % 1)); cr.arc(0, 0, rr, 0, 6.283); cr.restore(); cr.fill()
    r2 = np.random.default_rng(38)
    for (x, y) in pts:
        for dx in (-TILE, 0, TILE):
            for dy in (-TILE, 0, TILE):
                X, Y = x + dx + r2.uniform(-6, 6), y + dy + r2.uniform(-6, 6)
                if -40 < X < TILE + 40 and -40 < Y < TILE + 40:
                    cr.set_source_rgba(*NUC, 0.85); cr.save(); cr.translate(X, Y); cr.rotate(r2.uniform(0, 3)); cr.scale(1, 0.75); cr.arc(0, 0, 15, 0, 6.283); cr.restore(); cr.fill()
                    cr.set_source_rgba(0.18, 0.08, 0.3, 0.6)
                    for _ in range(5): cr.arc(X + r2.uniform(-8, 8), Y + r2.uniform(-6, 6), 2.2, 0, 6.283); cr.fill()
    s.flush(); a = np.frombuffer(s.get_data(), np.uint8).reshape(TILE, s.get_stride() // 4, 4)[:, :TILE, :3].astype(np.float32) / 255
    rr = np.random.default_rng(1); n = cv2.GaussianBlur(rr.standard_normal((TILE, TILE)).astype(np.float32), (0, 0), 6)
    a = a * (1 + 0.06 * n[..., None] / n.std())                      # 염색 얼룩
    _T['v'] = np.clip(a, 0, 1); return _T['v']

def field(zoom, cx, cy, rot=0.0):
    """zoom: 화면 1px당 무늬 px의 역수(클수록 확대). 화면 가운데가 무늬 (cx, cy)."""
    tl = tile(); k = zoom * SC
    M = np.array([[k * math.cos(rot), -k * math.sin(rot), 0], [k * math.sin(rot), k * math.cos(rot), 0]], np.float32)
    M[:, 2] = np.array([W / 2, H / 2]) - M[:, :2] @ np.array([cx, cy])
    if k < 0.5:                                                         # 많이 줄일 때는 먼저 흐려 둔다(계단 방지)
        tl = cv2.GaussianBlur(tl, (0, 0), 0.5 / k)
    return cv2.warpAffine(tl, M, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_WRAP)

# 시간표
T_ZIN = (3.6, 7.0); T_ZOUT = (9.2, 15.0); T_BIG = 15.2; T_RBC = 18.2; T_COUNT = 22.4; T_CODA = 27.2
STEPS = [(9.5, 1), (10.6, 1e3), (11.7, 1e6), (12.8, 1e9), (13.9, 1e12), (15.0, 3.72e13)]

def focus():
    p = np.random.default_rng(37).uniform(0, TILE, (260, 2)); i = int(np.argmin(np.hypot(p[:, 0] - 700, p[:, 1] - 600))); return float(p[i, 0]), float(p[i, 1])

def zoom_at(t):
    if t < T_ZIN[0]: return 1.0 + 0.02 * t
    if t < T_ZOUT[0]: return lerp(1.07, 4.2, expo_in_out(ramp(t, *T_ZIN)))
    u = smooth(ramp(t, *T_ZOUT)); return math.exp(lerp(math.log(4.2), math.log(0.16), u))

def counter(t):
    v = 1.0
    for i, (tt, val) in enumerate(STEPS):
        if t >= tt:
            prev = STEPS[i - 1][1] if i else 1
            v = 10 ** lerp(math.log10(prev), math.log10(val), expo_out(ramp(t, tt, tt + 0.9)))
    return v

_M = {}
def scope_mask():
    """현미경 원형 시야 + 가장자리 색수차 테두리."""
    if 'v' in _M: return _M['v']
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32); cx, cy, R = W / 2, H * 0.52, W * 0.47
    d = np.sqrt((xx - cx) ** 2 + (yy - cy) ** 2) / R
    m = np.clip((1.0 - d) / 0.02, 0, 1); vig = np.clip(1 - 0.55 * d ** 4, 0, 1)
    ring = np.exp(-((d - 1.0) / 0.012) ** 2)
    _M['v'] = (m[..., None] * vig[..., None], ring[..., None], cy); return _M['v']

def draw(t):
    z = zoom_at(t); cx, cy = TILE * 0.42 + 6 * t, TILE * 0.37 + 3 * t
    if t >= T_ZIN[0] - 0.01 and t < T_ZOUT[1]:
        u = expo_in_out(ramp(t, *T_ZIN)); fx_, fy_ = focus()
        cx, cy = lerp(TILE * 0.42 + 6 * t, fx_, u), lerp(TILE * 0.37 + 3 * t, fy_, u)
    img = field(z, cx, cy, 0.03 * math.sin(t * 0.3)).copy()
    s, cr = surf()
    # 적혈구가 떠다닌다
    if t >= T_RBC - 0.5:
        a = ramp(t, T_RBC - 0.5, T_RBC + 0.6); r = np.random.default_rng(70)
        for i in range(70):
            x0, y0, sp, ph = r.uniform(-100, DW + 100), r.uniform(250, 1700), r.uniform(20, 60), r.uniform(0, 6)
            x = (x0 + sp * (t - T_RBC)) % (DW + 200) - 100; y = y0 + 20 * math.sin(t * 0.8 + ph); rr = r.uniform(26, 40)
            cr.save(); cr.translate(x, y); cr.rotate(ph); cr.scale(1, r.uniform(0.6, 1.0))
            g = cairo.RadialGradient(0, 0, 0, 0, 0, rr)
            g.add_color_stop_rgba(0, *RBC, 0.45 * a); g.add_color_stop_rgba(0.55, *RBC, 0.62 * a); g.add_color_stop_rgba(0.85, 0.7, 0.1, 0.16, 0.95 * a); g.add_color_stop_rgba(1, 0.6, 0.05, 0.1, 0)
            cr.set_source(g); cr.arc(0, 0, rr, 0, 6.283); cr.fill(); cr.restore()
    img = over(img, s)
    m, ring, ycen = scope_mask()
    dark = solid((0.05, 0.03, 0.06))
    img = img * m + dark * (1 - m) + ring * np.array([0.9, 0.4, 0.3], np.float32) * 0.25
    # 숫자판
    s, cr = surf()
    if T_ZOUT[0] - 0.3 < t < T_CODA:
        v = counter(t); a = ramp(t, T_ZOUT[0] - 0.3, T_ZOUT[0])
        en = SE.en_num(v) if v < 3.7e13 else '37.2 trillion'; ko = SE.ko_num(v) if v < 3.7e13 else '37조 2천억'
        cr.set_source_rgba(0.05, 0.03, 0.06, 0.75 * a); rrect(cr, 150, 1650, DW - 300, 190, 95); cr.fill()
        txt(cr, en + ' cells', DW / 2, 1735, 58, (0.98, 0.9, 0.93), a, maxw=740)
        txt(cr, '세포 ' + ko + '개', DW / 2, 1808, 50, (0.95, 0.55, 0.72), a, maxw=740)
    if t >= T_COUNT:
        a = ramp(t, T_COUNT, T_COUNT + 0.4)
        cr.set_source_rgba(0.05, 0.03, 0.06, 0.8 * a); rrect(cr, 120, 1290, DW - 240, 270, 40); cr.fill()
        txt(cr, '1 per second → 1.18 million years', DW / 2, 1385, 46, (0.98, 0.9, 0.93), a, maxw=780)
        txt(cr, '1초에 하나씩 세면 → 118만 년', DW / 2, 1460, 46, (0.95, 0.55, 0.72), a, maxw=780)
    return over(img, s)

def sound(path):
    m = S.Mix(EP['DUR'], 37); tc = EP['t_coda']
    m.put('amb', 0, S.drone([110, 165, 220], EP['t_end'] + 1, 0.10, 'sine'))
    for i, tt in enumerate([0.6, 1.4, 2.1, 2.9]): m.put('fx', tt, S.drop(700 + 150 * i, 0.35))
    m.put('fx', T_ZIN[0], S.swoosh(T_ZIN[1] - T_ZIN[0], 0.18, 200, 3000))
    pent = [261.6, 293.7, 329.6, 392.0, 440.0, 523.3, 587.3, 659.3]
    for i, (tt, v) in enumerate(STEPS):
        m.put('mus', tt, S.marimba(pent[i + 1], 1.4, 0.55)); m.put('fx', tt, S.drop(900 + 120 * i, 0.4))
    m.put('fx', T_ZOUT[0], S.swoosh(T_ZOUT[1] - T_ZOUT[0], 0.14, 300, 6000))
    for j, f in enumerate([523.3, 659.3, 784.0]): m.put('mus', T_BIG + 0.05 * j, S.marimba(f, 2.0, 0.6))
    m.put('fx', T_BIG, S.kick(60, 0.6))
    for k in range(10): m.put('fx', T_RBC + 0.35 * k, S.drop(500 + 40 * (k % 4), 0.22))
    m.put('mus', T_COUNT, S.marimba(392.0, 1.6, 0.5)); m.put('mus', T_COUNT + 0.3, S.marimba(523.3, 1.6, 0.45))
    for i in range(3): m.put('mus', tc + 0.8 + i * STEP, S.bell([523.3, 587.3, 659.3][i], 3.2, 0.4))
    m.put('amb', tc, S.drone([130.8, 196.0, 261.6], EP['t_end'] - tc, 0.18, 'sine'))
    for j, f in enumerate([523.3, 659.3, 784.0]): m.put('mus', EP['t_end'] + 0.15 + 0.07 * j, S.marimba(f, 2.0, 0.5))
    m.write(path, rev_mus=2.4, wet_mus=0.32)

EP = finalize(dict(t_coda=T_CODA, draw=draw, sound=sound, end_icon='brain', grain=0.006,
    title_en_card='37 TRILLION OF YOU', title_ko_card='37조 개의 나',
    pal=dict(hi=hexc('#c2477d'), endbg=(0.97, 0.93, 0.94)),
    card_style=dict(box='paper', bg=(0.99, 0.95, 0.96), ink=(0.22, 0.10, 0.25), hi=hexc('#c2477d'), y=150),
    cards=[(0.3, 3.5, ['How many cells', 'make *you*?'], ['나를 이루는 세포는', '*몇 개*일까?']),
           (3.8, 9.0, ['Start with *one*.'], ['*하나*에서 시작해 보자']),
           (15.2, 18.0, ['About *37.2 trillion*.'], ['약 *37조 2천억 개*']),
           (18.3, 22.2, ['About *70%* of them', 'are red blood cells.'], ['그중 약 *70%*는', '적혈구']),
           (22.5, 27.0, ['Counting them one by one would take', 'longer than *humans have existed*.'], ['하나씩 세면', '*인류가 존재한 시간보다* 오래 걸린다'])],
    coda=[('Trillions of tiny lives', '37조 개의 작은 생명이'), ('working as one, without a word,', '말없이 하나처럼 일한다'), ('so that you can be you.', '당신이 당신일 수 있도록')],
    coda_style=dict(dim=0.72, blur=14, ink=(0.98, 0.93, 0.95), hi=(0.98, 0.62, 0.78), tint=(0.15, 0.03, 0.1)),
    sources=['Bianconi et al., Ann Hum Biol 2013: ≈3.72×10¹³ cells in an adult body; ~70% red blood cells (BioNumbers).', 'Homo sapiens ≈ 300,000 years (Hublin et al., Nature 2017).'],
    yt=dict(title_en='You Are Made of 37 Trillion Cells #Shorts', title_ko='나는 세포 37조 개로 이루어져 있다')))

if __name__ == '__main__': main(EP)
