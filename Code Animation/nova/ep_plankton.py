"""〈숨 두 번에 한 번은 바다에서〉 — 규조류 만화경(유리 껍데기 같은 방사 대칭 무늬, 12겹 거울, 무지갯빛 색 이동), 소리는 글라스 하모니카와 물방울.
사실(NOAA Ocean Service): 지구 산소 생산의 약 절반이 바다에서, 대부분 플랑크톤. 프로클로로코쿠스 하나가 생물권 산소의 최대 20%(열대우림 전체보다 많다).
WHOI: 규조류가 우리 숨 다섯 번 중 한 번의 산소를 만든다고 추정.
"""
import math, numpy as np, cv2, cairo
from base import *
import sfx as S

T_HALF = 3.8; T_TINY = 8.8; T_DIATOM = 13.6; T_CODA = 18.8
CX, CY = 540, 1020

def hsv(h, s, v):
    i = int(h * 6) % 6; f = h * 6 - int(h * 6); p, q, w = v * (1 - s), v * (1 - f * s), v * (1 - (1 - f) * s)
    return [(v, w, p), (q, v, p), (p, v, w), (p, q, v), (w, p, v), (v, p, q)][i]

def diatom(cr, x, y, r, kind, hue, a):
    cr.save(); cr.translate(x, y)
    if kind == 0:                                              # 둥근 규조(중심형)
        for k in range(5, 0, -1):
            cr.set_source_rgba(*hsv((hue + k * 0.03) % 1, 0.55, 0.95), a * 0.35); cr.arc(0, 0, r * k / 5, 0, 6.283); cr.fill()
        cr.set_source_rgba(1, 1, 1, a * 0.7); cr.set_line_width(1.2)
        for k in range(24): ang = k * 6.283 / 24; cr.move_to(r * 0.2 * math.cos(ang), r * 0.2 * math.sin(ang)); cr.line_to(r * math.cos(ang), r * math.sin(ang)); cr.stroke()
        cr.arc(0, 0, r, 0, 6.283); cr.stroke()
    else:                                                      # 길쭉한 규조(깃형)
        cr.scale(1, 0.32); cr.set_source_rgba(*hsv(hue, 0.5, 0.95), a * 0.4); cr.arc(0, 0, r, 0, 6.283); cr.fill()
        cr.restore(); cr.save(); cr.translate(x, y); cr.set_source_rgba(1, 1, 1, a * 0.7); cr.set_line_width(1.2)
        for k in range(-8, 9): xx = k * r / 9; hh = r * 0.32 * math.sqrt(max(0, 1 - (xx / r) ** 2)); cr.move_to(xx, -hh); cr.line_to(xx, hh); cr.stroke()
        cr.move_to(-r, 0); cr.line_to(r, 0); cr.stroke()
    cr.restore()

def wedge(t, hue0):
    """만화경 한 조각(30°)을 그린다."""
    s, cr = surf()
    r = np.random.default_rng(7)
    for k in range(26):
        rad = r.uniform(60, 760); ang = r.uniform(0.02, 0.5) + 0.03 * math.sin(t * 0.4 + k)
        rr = r.uniform(20, 70) * (1 + 0.06 * math.sin(t * 1.3 + k)); kind = int(r.random() < 0.45)
        diatom(cr, CX + rad * math.cos(ang - 1.5708), CY + rad * math.sin(ang - 1.5708), rr, kind, (hue0 + rad / 1600) % 1, 0.9)
    return arr(s)

def kaleido(img, rot):
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    dx, dy = xx - CX * SC, yy - CY * SC
    ang = (np.arctan2(dy, dx) + math.pi / 2 - rot) % (math.pi / 3); ang = np.where(ang > math.pi / 6, math.pi / 3 - ang, ang)
    rad = np.hypot(dx, dy)
    mx = (CX * SC + rad * np.cos(ang - math.pi / 2)).astype(np.float32); my = (CY * SC + rad * np.sin(ang - math.pi / 2)).astype(np.float32)
    return cv2.remap(img, mx, my, cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT)

def draw(t):
    a = wedge(t, (t * 0.02) % 1)
    k = kaleido(a, t * 0.06)
    g = cairo
    bgy = np.linspace(0, 1, H, dtype=np.float32)[:, None, None]
    bg = np.array((0.22, 0.16, 0.03), np.float32) * (1 - bgy) + np.array((0.12, 0.06, 0.01), np.float32) * bgy        # BGR 짙은 바다
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    vign = np.clip(1.2 - np.hypot(xx - CX * SC, yy - CY * SC) / (900 * SC), 0, 1)[..., None]
    img = bg + k[..., :3] * vign * 1.1
    img = img + cv2.GaussianBlur(img, (0, 0), 8 * SC) * 0.3
    yd = np.linspace(0, DH, H, dtype=np.float32)
    shade = np.clip(np.minimum((yd - 300) / 300, (1640 - yd) / 260) , 0.35, 1)[:, None, None]
    img = bg + (img - bg) * shade
    s2, c2 = surf(); w = (0.92, 0.98, 1.0); hi = (0.55, 1.0, 0.85)
    def lab(text, y, size, a, col=w, fam=BLK):
        txt(c2, text, 543, y + 3, size, (0, 0, 0), a * 0.8, fam=fam); txt(c2, text, 540, y, size, col, a, fam=fam)
    if T_HALF <= t < T_TINY:
        a1 = ramp(t, T_HALF + 0.3, T_HALF + 0.7) * (1 - ramp(t, T_TINY - 0.3, T_TINY))
        for j, (en, ko, col) in enumerate((('ocean', '바다', hi), ('land', '육지', (0.9, 0.85, 0.6)))):
            x = 340 + j * 400; c2.set_source_rgba(0, 0, 0, 0.45 * a1); c2.arc(x, 1600, 120, 0, 6.283); c2.fill()
            c2.set_source_rgba(*col, a1); c2.set_line_width(4); c2.arc(x, 1600, 120, 0, 6.283); c2.stroke()
            txt(c2, f'breath {j + 1}', x, 1580, 34, col, a1, fam=BLK); txt(c2, ko, x, 1640, 40, col, a1, fam=BLK)
    if T_TINY <= t < T_DIATOM:
        a2 = ramp(t, T_TINY + 0.3, T_TINY + 0.7) * (1 - ramp(t, T_DIATOM - 0.3, T_DIATOM))
        lab('Prochlorococcus', 1600, 56, a2, hi, SERIF); lab('up to 20% of the world’s oxygen', 1680, 40, a2); lab('세계 산소의 최대 20%, 열대우림 전체보다 많다', 1740, 36, a2)
    if T_DIATOM <= t < T_CODA:
        a3 = ramp(t, T_DIATOM + 0.3, T_DIATOM + 0.7) * (1 - ramp(t, T_CODA - 0.4, T_CODA))
        lab('diatoms: algae in glass shells', 1620, 44, a3, hi); lab('유리 껍데기를 입은 규조류', 1690, 40, a3)
        lab('1 in 5 breaths · 숨 다섯 번에 한 번', 1770, 40, a3)
    return over(img, s2)

def sound(path):
    m = S.Mix(EP['DUR'], 201); tc = EP['t_coda']
    chords = [[523.3, 659.3, 784.0], [440.0, 554.4, 659.3], [493.9, 587.3, 740.0], [392.0, 493.9, 587.3]]
    t = 0.2; k = 0
    while t < tc - 0.5:
        for j, f in enumerate(chords[k % 4]): m.put('mus', t + j * 0.35, S.glassharp(f, 3.6, 0.22))
        t += 3.0; k += 1
    r = np.random.default_rng(3)
    for t in np.arange(0.5, tc, 0.6): m.put('fx', t + r.uniform(0, 0.4), S.drop(r.uniform(900, 2400), 0.18))
    m.put('amb', 0, S.drone([65.4, 98.0], EP['t_end'] + 1, 0.14, 'sine'))
    for i in range(2): m.put('fx', T_HALF + 0.4 + i * 0.9, S.breath(0.8, 0.4, seed=i))
    m.put('amb', tc, S.drone([130.8, 196.0, 261.6], EP['t_end'] - tc, 0.14, 'sine'))
    for i, f in enumerate([784.0, 659.3, 523.3]): m.put('mus', tc + 0.8 + i * STEP, S.glassharp(f, 3.5, 0.3))
    m.write(path, rev_mus=3.5, wet_mus=0.45)

EP = finalize(dict(t_coda=T_CODA, draw=draw, sound=sound, end_icon='drop', grain=0.003,
    title_en_card='EVERY OTHER BREATH', title_ko_card='숨 두 번에 한 번은 바다에서',
    pal=dict(hi=(0.10, 0.45, 0.50), endbg=(0.90, 0.97, 0.97)),
    card_style=dict(box=None, ink=(0.95, 0.99, 1.0), hi=(0.55, 1.0, 0.85), y=150, fe=BLK, fk=BLK),
    cards=[(0.3, 3.6, ['Where does the air', 'you breathe come from?'], ['내가 쉬는 공기는', '어디서 왔을까?']),
           (3.8, 8.6, ['About *half* of Earth’s oxygen', 'is made in *the ocean*.'], ['지구 산소의 약 *절반*은', '*바다*에서 만들어진다']),
           (8.8, 13.4, ['Mostly by life', '*too small to see*.'], ['대부분', '*눈에 보이지 않는* 생물이']),
           (13.6, 18.6, ['These glassy algae alone:', 'about *1 in 5* breaths.'], ['유리 같은 규조류만으로도', '숨 *다섯 번에 한 번*'])],
    coda=[('Every other breath you take', '당신이 쉬는 숨 두 번에 한 번은'), ('was made by life you will never see.', '평생 보지 못할 생명이 만들었다'), ('Give thanks for unseen hands.', '보이지 않는 손에 감사하자')],
    coda_style=dict(dim=0.55, blur=10, tint=(0.02, 0.08, 0.12), ink=(0.95, 0.99, 1.0), hi=(0.55, 1.0, 0.85)),
    sources=['NOAA Ocean Service, “How much oxygen comes from the ocean?”: roughly half of Earth’s oxygen production; Prochlorococcus up to 20% of the biosphere’s oxygen.', 'WHOI: diatoms supply the oxygen in about one of every five breaths (estimate).'],
    yt=dict(title_en='Half the Oxygen You Breathe Comes From the Ocean #Shorts', title_ko='숨 두 번에 한 번은 바다가 만든 산소')))

if __name__ == '__main__': main(EP)
