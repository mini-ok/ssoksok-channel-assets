"""〈가만히 있어도〉 — 1970년대 옵셋 인쇄(크림 종이, 별색 3판, 망점, 판 어긋남), 소리는 사각파 신스 아르페지오.
사실(Britannica "What is Earth's velocity?"): 적도의 자전 속도 465.1 m/s = 1,674 km/h, 위도에 따라 × cos(위도).
공전 평균 29,784.8 m/s = 107,225 km/h. 서울(북위 37.57°) ≈ 1,327 km/h(계산). 소리 속도 약 1,235 km/h(20°C, 343 m/s).
"""
import math, numpy as np, cv2, cairo
from base import *
import sfx as S

PAPER = np.array((0.80, 0.90, 0.95), np.float32)          # BGR 크림
INK = {'teal': (0.20, 0.55, 0.58), 'orange': (0.93, 0.42, 0.18), 'brown': (0.24, 0.15, 0.10)}   # RGB
ANG = {'teal': 15, 'orange': 75, 'brown': 45}
T_EQ = 4.4; T_ORB = 8.8; T_ODO = 14.2; T_CODA = 23.0
V_ORB = 29.7848                                              # km/s

_yy, _xx = np.mgrid[0:H, 0:W].astype(np.float32)
def _screen(a, p):
    c, s = math.cos(math.radians(a)), math.sin(math.radians(a)); u = _xx * c + _yy * s; v = -_xx * s + _yy * c
    return 0.5 + 0.25 * (np.cos(2 * np.pi * u / p) + np.cos(2 * np.pi * v / p))
SCR = {k: _screen(a, 9.0 * SC) for k, a in ANG.items()}
_r = np.random.default_rng(2)
GRAIN = cv2.GaussianBlur(_r.standard_normal((H, W)).astype(np.float32), (0, 0), 1.2 * SC) * 0.03

def plates():
    out = {}
    for k in INK:
        s, cr = surf(); out[k] = (s, cr)
    return out

def cov(s):
    return arr(s)[..., 3]

def globe(P, t, cx, cy, R, a=1.0, spin=0.0):
    tl, tc = P['teal'][1], P['brown'][1]
    tl.set_source_rgba(0, 0, 0, 0.5 * a); tl.arc(cx, cy, R, 0, 6.283); tl.fill()
    tc.set_source_rgba(0, 0, 0, 0.9 * a); tc.set_line_width(5); tc.arc(cx, cy, R, 0, 6.283); tc.stroke()
    tc.save(); tc.arc(cx, cy, R, 0, 6.283); tc.clip()
    lands = [(0.2, 0.6, 0.55), (0.9, -0.3, 0.5), (2.2, 0.35, 0.65), (3.3, -0.5, 0.45), (4.4, 0.2, 0.6), (5.4, 0.7, 0.4)]
    for lon, lat, r in lands:
        z = math.cos(lat) * math.cos(lon - spin)
        if z <= -0.2: continue
        x = cx + R * math.cos(lat) * math.sin(lon - spin); y = cy - R * math.sin(lat)
        tc.save(); tc.translate(x, y); tc.scale(max(0.05, z), 1); tc.set_source_rgba(0, 0, 0, 0.75 * a * min(1, (z + 0.2) * 3))
        tc.arc(0, 0, R * r * 0.55, 0, 6.283); tc.fill(); tc.restore()
    for k in range(-2, 3):                                     # 위도선
        lat = k * 0.5; yy = cy - R * math.sin(lat); w = R * math.cos(lat)
        tc.set_source_rgba(0, 0, 0, 0.35 * a); tc.set_line_width(2); tc.save(); tc.translate(cx, yy); tc.scale(w, w * 0.12)
        tc.arc(0, 0, 1, 0, math.pi); tc.restore(); tc.stroke()
    for k in range(6):                                         # 경도선(돈다)
        lon = k * math.pi / 6 - spin % (math.pi / 6) * 0 - (spin % (math.pi / 3))
        sx = math.sin(lon)
        tc.save(); tc.translate(cx, cy); tc.scale(R * abs(sx) + 0.01, R); tc.arc(0, 0, 1, 0, 6.283); tc.restore()
        tc.set_source_rgba(0, 0, 0, 0.18 * a); tc.set_line_width(1.6); tc.stroke()
    tc.restore()

def draw(t):
    P = plates(); og, br, tl = P['orange'][1], P['brown'][1], P['teal'][1]
    TX = []
    # 햇살 바탕(주황판 줄무늬)
    sa = 0.35 + 0.65 * ramp(t, T_ORB, T_ORB + 0.8)
    scx, scy = (540, 1060) if t < T_ORB else (540, lerp(1060, 1120, smooth(ramp(t, T_ORB, T_ORB + 1.2))))
    for k in range(24):
        a0 = k * 6.283 / 24 + t * 0.05
        og.set_source_rgba(0, 0, 0, 0.18 * sa); og.move_to(scx, scy); og.arc(scx, scy, 1600, a0, a0 + 6.283 / 48); og.close_path(); og.fill()
    u = smooth(ramp(t, T_ORB, T_ORB + 1.4))                    # 지구 → 공전 궤도로
    if t < T_ODO + 0.6:
        fa = 1 - ramp(t, T_ODO, T_ODO + 0.6)
        R = lerp(330, 60, u); cx, cy = 540, lerp(1060, 1120, u)
        if u > 0:
            og.set_source_rgba(0, 0, 0, 0.95 * u * fa); og.arc(540, 1120, 120, 0, 6.283); og.fill()   # 해
            br.set_source_rgba(0, 0, 0, 0.6 * u * fa); br.set_line_width(4); br.set_dash([14, 14])
            br.save(); br.translate(540, 1120); br.scale(400, 240); br.arc(0, 0, 1, 0, 6.283); br.restore(); br.stroke(); br.set_dash([])
            ang = (t - T_ORB) * 1.1 + math.pi / 2
            ox, oy = 540 + 400 * math.cos(ang), 1120 + 240 * math.sin(ang)
            cx, cy = lerp(540, ox, u), lerp(1060, oy, u)
            for k in range(1, 9):                                # 속도선
                aa = ang - k * 0.07; px, py = 540 + 400 * math.cos(aa), 1120 + 240 * math.sin(aa)
                br.set_source_rgba(0, 0, 0, 0.5 * u * fa * (1 - k / 9)); br.arc(px, py, lerp(R, 8, k / 9) * 0.6, 0, 6.283); br.fill()
            if t > T_ORB + 1.0:
                la = ramp(t, T_ORB + 1.0, T_ORB + 1.5) * fa
                TX.append(('107,000 km/h', 540, 1520, 86, INK['orange'], la)); TX.append(('≈ 30 km / s', 540, 1610, 54, INK['brown'], la))
        globe(P, t, cx, cy, R, fa, spin=t * 0.9)
        if u < 0.5 and t > T_EQ - 0.2:                         # 적도·서울 표시
            ea = ramp(t, T_EQ, T_EQ + 0.5) * (1 - ramp(t, T_ORB - 0.3, T_ORB))
            og.set_source_rgba(0, 0, 0, ea); og.set_line_width(7); og.move_to(540 - 330, 1060); og.line_to(540 + 330, 1060); og.stroke()
            og.move_to(540 + 330, 1060); og.line_to(540 + 300, 1040); og.line_to(540 + 300, 1080); og.close_path(); og.fill()
            sy = 1060 - 330 * math.sin(math.radians(37.57)); sw = 330 * math.cos(math.radians(37.57))
            px = 540 + sw * math.sin(t * 0.9 % 6.283 - 1.2)
            br.set_source_rgba(0, 0, 0, ea); br.arc(px, sy, 12, 0, 6.283); br.fill()
            TX.append(('Equator · 적도  1,674 km/h', 540, 1460, 46, INK['orange'], ea))
            TX.append(('Seoul · 서울  ≈ 1,330 km/h', 540, 1530, 42, INK['brown'], ea))
            TX.append(('Sound · 소리  ≈ 1,235 km/h', 540, 1600, 36, INK['teal'], ea))
    # 주행 거리계
    if t > T_ODO:
        a = ramp(t, T_ODO + 0.2, T_ODO + 0.8)
        km = V_ORB * t
        br.set_source_rgba(0, 0, 0, 0.9 * a); rrect(br, 140, 760, 800, 260, 30); br.fill()
        TX.append((f'{km:,.0f} km', 540, 935, 140, (0.96, 0.92, 0.82), a))
        TX.append(('through space, so far · 지금까지 우주를 달린 거리', 540, 1090, 36, INK['brown'], a))
        bx0, bx1, by = 140, 940, 1300; full = V_ORB * (T_CODA - 0.2)
        tl.set_source_rgba(0, 0, 0, 0.35 * a); tl.rectangle(bx0, by - 18, bx1 - bx0, 36); tl.fill()
        og.set_source_rgba(0, 0, 0, a); og.rectangle(bx0, by - 18, (bx1 - bx0) * min(1, km / full), 36); og.fill()
        mx = bx0 + (bx1 - bx0) * 325 / full
        br.set_source_rgba(0, 0, 0, a); br.set_line_width(4); br.move_to(mx, by - 50); br.line_to(mx, by + 50); br.stroke()
        hit = ramp(t, 325 / V_ORB, 325 / V_ORB + 0.3)
        TX.append(('Seoul → Busan ≈ 325 km', mx, by + 100, 34, INK['brown'], a)); TX.append(('서울 → 부산', mx, by + 145, 32, INK['brown'], a))
        if hit > 0: TX.append(('passed · 벌써 지나침', mx, by - 70, 34, INK['orange'], a * hit))
    # 판 합성: 망점 + 판 어긋남
    img = np.broadcast_to(PAPER, (H, W, 3)).copy() + GRAIN[..., None]
    for k, (s, cr) in P.items():
        c = cov(s); off = (int(round((2.5 + 1.5 * math.sin(t * 0.7 + len(k))) * SC)), int(round(1.5 * SC)))
        c = np.roll(c, off, axis=(1, 0)) if k != 'brown' else c
        m = np.clip((c - SCR[k]) * 6 + 0.5, 0, 1) * (c > 0.02)
        col = np.array(INK[k][::-1], np.float32)
        img = img * (1 - m[..., None] * (1 - col))
    s2, c2 = surf()
    for tx in TX:
        txt(c2, tx[0], tx[1] + 3, tx[2] + 2, tx[3], (0.93, 0.42, 0.18), tx[5] * 0.5, fam=BLK); txt(c2, *tx[:5], tx[5], fam=BLK)
    return over(img, s2)

def sound(path):
    m = S.Mix(EP['DUR'], 41); tc = EP['t_coda']; b = 60 / 120
    prog = [[220.0, 277.2, 329.6, 440.0], [196.0, 246.9, 293.7, 392.0], [174.6, 220.0, 261.6, 349.2], [196.0, 246.9, 293.7, 392.0]]
    t = 0.3; k = 0
    while t < tc - 0.1:
        ch = prog[(k // 16) % 4]; f = ch[k % 4] * (2 if (k // 4) % 2 else 1)
        m.put('mus', t, S.square(f, 0.16, 0.11 if t > T_EQ else 0.07, duty=0.25) * np.exp(-np.arange(int(0.16 * S.SR)) / S.SR * 14))
        if k % 8 == 0: m.put('mus', t, S.square(ch[0] / 2, b * 3.5, 0.09) * np.exp(-np.arange(int(b * 3.5 * S.SR)) / S.SR * 1.2))
        if k % 4 == 0: m.put('fx', t, S.kick(60, 0.35, 0.3))
        if k % 4 == 2: m.put('fx', t, S.shaker(0.08, 0.2, k))
        t += b / 4 * 2; k += 1
    m.put('fx', T_ORB, S.swoosh(1.4, 0.6, 300, 6000)); m.put('fx', T_ORB + 1.0, S.bell(1318.5, 2.0, 0.3))
    for i in range(int((tc - T_ODO) / 0.25)): m.put('fx', T_ODO + 0.3 + i * 0.25, S.tok(1800 + 200 * (i % 2), 0.12))
    m.put('fx', 325 / V_ORB, S.ping(1568, 0.4, 1.2))
    m.put('amb', tc, S.drone([110.0, 164.8, 220.0], EP['t_end'] - tc, 0.2, 'saw'))
    for i in range(3): m.put('mus', tc + 0.8 + i * STEP, S.square([440.0, 554.4, 659.3][i], 2.0, 0.08) * np.exp(-np.arange(int(2.0 * S.SR)) / S.SR * 1.5))
    m.put('fx', EP['t_end'] + 0.2, S.ping(1760, 0.4, 2.0))
    m.write(path, rev_mus=1.6, wet_mus=0.25)

EP = finalize(dict(t_coda=T_CODA, draw=draw, sound=sound, end_icon='star', grain=0.004,
    title_en_card='NEVER STILL', title_ko_card='가만히 있어도',
    pal=dict(hi=INK['orange'], endbg=(0.95, 0.90, 0.80)),
    card_style=dict(box=None, ink=INK['brown'], hi=INK['orange'], y=150, fe=BLK, fk=BLK),
    cards=[(0.3, 4.2, ['Sitting still?', 'You’re moving *faster than sound.*'], ['가만히 앉아 있다고?', '지금 당신은 *소리보다 빠르다*']),
           (4.4, 8.6, ['Earth spins *1,674 km/h* at the equator.', 'Seoul: about *1,330 km/h.*'], ['적도에서 지구는 시속 *1,674km*로 돈다', '서울은 시속 약 *1,330km*']),
           (8.8, 14.0, ['And it circles the Sun at *107,000 km/h*.', 'About *30 km every second.*'], ['태양 둘레는 시속 *10만 7천km*', '1초에 약 *30km*']),
           (14.2, 22.8, ['Since this video began,', 'you’ve traveled this far:'], ['이 영상이 시작된 뒤로', '당신이 지나온 거리'])],
    coda=[('You feel perfectly still.', '가만히 있는 것 같아도'), ('You have never stopped moving.', '우리는 한 번도 멈춘 적이 없다'), ('Stillness is a feeling, not a fact.', '멈춤은 느낌일 뿐, 삶은 흐르고 있다')],
    coda_style=dict(dim=0.82, blur=10, tint=(0.95, 0.90, 0.80), ink=INK['brown'], hi=INK['orange']),
    sources=['Britannica, "What is Earth’s velocity?": equator 465.1 m/s (1,674 km/h); orbit 29,784.8 m/s (107,225 km/h).', 'Seoul (37.57°N) ≈ 1,674 × cos 37.57° ≈ 1,327 km/h (calculated). Speed of sound ≈ 343 m/s at 20 °C.'],
    yt=dict(title_en='You’re Moving Faster Than Sound Right Now #Shorts', title_ko='가만히 있어도 당신은 소리보다 빠르다')))

if __name__ == '__main__': main(EP)
