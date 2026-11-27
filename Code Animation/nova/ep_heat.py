"""〈사람은 전구 하나만큼 따뜻하다〉 — 열화상 카메라(철 팔레트, 십자선·온도 눈금 HUD, 센서 잡음), 소리는 아날로그 FM 신스 패드와 낮은 맥박.
사실: 쉬고 있는 사람은 약 100 W의 열을 낸다(Illinois Physics Van "A normal person emits about 100 Watts of heat";
추정은 60~100 W로 갈린다). 500명이 모인 극장이면 약 50 kW(Big Think).
"""
import math, numpy as np, cv2, cairo
from base import *
import sfx as S

T_BULB = 3.8; T_CROWD = 8.8; T_HUG = 13.6; T_CODA = 18.8
_P = np.array([(0.00, 0, 0, 0.02), (0.15, 0.20, 0.0, 0.35), (0.35, 0.55, 0.0, 0.50), (0.55, 0.85, 0.15, 0.20), (0.75, 1.0, 0.55, 0.0), (0.9, 1.0, 0.85, 0.3), (1.0, 1.0, 1.0, 0.95)])
LUT = np.stack([np.interp(np.linspace(0, 1, 256), _P[:, 0], _P[:, c]) for c in (3, 2, 1)], 1).astype(np.float32)   # BGR
_r = np.random.default_rng(31)

def person(cr, x, y, s, heat=1.0):
    cr.set_source_rgba(1, 1, 1, 0.92 * heat); cr.arc(x, y - 150 * s, 55 * s, 0, 6.283); cr.fill()
    cr.set_source_rgba(1, 1, 1, 0.75 * heat)
    cr.move_to(x - 95 * s, y + 220 * s); cr.curve_to(x - 110 * s, y - 40 * s, x - 70 * s, y - 85 * s, x, y - 85 * s)
    cr.curve_to(x + 70 * s, y - 85 * s, x + 110 * s, y - 40 * s, x + 95 * s, y + 220 * s); cr.close_path(); cr.fill()
    cr.set_source_rgba(1, 1, 1, 0.98 * heat); cr.arc(x, y - 30 * s, 32 * s, 0, 6.283); cr.fill()          # 가슴(가장 따뜻함)

def bulb(cr, x, y, s, heat=1.0):
    cr.set_source_rgba(1, 1, 1, heat); cr.arc(x, y, 70 * s, 0, 6.283); cr.fill()
    cr.set_source_rgba(1, 1, 1, 0.5 * heat); cr.rectangle(x - 30 * s, y + 60 * s, 60 * s, 60 * s); cr.fill()

def draw(t):
    s, cr = surf(); cr.set_source_rgba(1, 1, 1, 0.12); cr.paint()                       # 방 온도(차가움)
    a1 = 1 - ramp(t, T_BULB - 0.3, T_BULB)
    if a1 > 0: person(cr, 540, 1150, 2.2, a1 * smooth(ramp(t, 0.2, 1.6)))
    a2 = ramp(t, T_BULB - 0.2, T_BULB + 0.3) * (1 - ramp(t, T_CROWD - 0.3, T_CROWD))
    if a2 > 0: person(cr, 360, 1180, 1.6, a2); bulb(cr, 790, 1060, 1.5, a2 * smooth(ramp(t, T_BULB + 0.4, T_BULB + 1.6)))
    a3 = ramp(t, T_CROWD - 0.2, T_CROWD + 0.3) * (1 - ramp(t, T_HUG - 0.3, T_HUG))
    if a3 > 0:
        n = int(500 * smooth(ramp(t, T_CROWD + 0.2, T_CROWD + 3.0)))
        for i in range(n):
            x = 70 + (i % 25) * 39; y = 560 + (i // 25) * 52 + (i % 2) * 10
            cr.set_source_rgba(1, 1, 1, 0.8 * a3); cr.arc(x, y, 13, 0, 6.283); cr.fill(); cr.set_source_rgba(1, 1, 1, 0.5 * a3); cr.rectangle(x - 14, y + 12, 28, 26); cr.fill()
    a4 = ramp(t, T_HUG - 0.2, T_HUG + 0.3) * (1 - ramp(t, T_CODA - 0.4, T_CODA))
    if a4 > 0:
        d = lerp(260, 120, smooth(ramp(t, T_HUG + 0.3, T_HUG + 2.5)))
        person(cr, 540 - d, 1180, 1.8, a4); person(cr, 540 + d, 1180, 1.8, a4)
    temp = arr(s)[..., 3]
    temp = cv2.GaussianBlur(temp, (0, 0), 22 * SC) * 0.55 + cv2.GaussianBlur(temp, (0, 0), 6 * SC) * 0.45
    noise = cv2.GaussianBlur(_r.standard_normal((H, W)).astype(np.float32), (0, 0), 1.0 * SC) * 0.02 + _r.standard_normal((H, W)).astype(np.float32) * 0.008
    idx = np.clip((temp * 0.95 + noise + 0.03) * 255, 0, 255).astype(np.uint8)
    img = LUT[idx]
    # HUD
    s2, c2 = surf(); hud = (0.95, 0.95, 0.95)
    c2.set_source_rgba(*hud, 0.8); c2.set_line_width(2)
    for x, y in ((80, 520), (1000, 520), (80, 1560), (1000, 1560)):
        sx = 1 if x < 540 else -1; sy = 1 if y < 1000 else -1
        c2.move_to(x, y + sy * 40); c2.line_to(x, y); c2.line_to(x + sx * 40, y); c2.stroke()
    c2.move_to(510, 1000); c2.line_to(570, 1000); c2.move_to(540, 970); c2.line_to(540, 1030); c2.stroke()
    tread = 18.0 + 18.5 * float(temp[int(1000 * SC), int(540 * SC)])
    txt(c2, f'{tread:4.1f}°C', 600, 990, 34, hud, 0.9, fam=BOLD, anchor='l')
    for k in range(60):                                              # 온도 눈금 막대
        c = LUT[int(k / 59 * 255)][::-1]; c2.set_source_rgba(*c, 1); c2.rectangle(1010, 1500 - k * 14, 26, 14); c2.fill()
    txt(c2, '37°', 1022, 640, 26, hud, 0.9, fam=BOLD); txt(c2, '18°', 1022, 1540, 26, hud, 0.9, fam=BOLD)
    def lab(text, y, size, a, col=hud):
        txt(c2, text, 543, y + 3, size, (0, 0, 0), a * 0.8, fam=BLK); txt(c2, text, 540, y, size, col, a, fam=BLK)
    if a2 > 0: lab('≈ 100 W', 1600, 90, a2 * ramp(t, T_BULB + 1.0, T_BULB + 1.4), (1.0, 0.85, 0.4)); lab('you  =  a 100 W bulb · 나 = 100W 전구', 1700, 40, a2 * ramp(t, T_BULB + 1.0, T_BULB + 1.4))
    if a3 > 0:
        n = int(500 * smooth(ramp(t, T_CROWD + 0.2, T_CROWD + 3.0)))
        lab(f'{n} people · {n}명', 1620, 56, a3); lab(f'≈ {n * 0.1:.0f} kW', 1710, 70, a3, (1.0, 0.85, 0.4))
    return over(img, s2)

def sound(path):
    m = S.Mix(EP['DUR'], 221); tc = EP['t_coda']
    chords = [[110.0, 164.8, 220.0, 277.2], [98.0, 146.8, 196.0, 246.9], [87.3, 130.8, 174.6, 220.0], [98.0, 146.8, 196.0, 261.6]]
    for k in range(int(tc / 4.6) + 1):
        t0 = k * 4.6
        if t0 >= tc: break
        m.put('mus', t0, S.drone(chords[k % 4], min(4.9, tc - t0 + 0.3), 0.22, 'saw'))
    t = 0.4; k = 0
    while t < tc - 0.3:
        m.put('mus', t, S.fm([440.0, 554.4, 659.3, 554.4, 493.9, 587.3, 659.3, 739.9][k % 8], 0.8, 0.14, 1.0, 2.0, 0.35)); t += 0.6; k += 1
    t = 0.5
    while t < tc: m.put('fx', t, S.kick(52, 0.35, 0.25)); m.put('fx', t + 0.22, S.kick(48, 0.2, 0.2)); t += 1.0
    m.put('fx', T_BULB + 1.0, S.ping(1046.5, 0.3, 2.0))
    for i in range(12): m.put('fx', T_CROWD + 0.2 + i * 0.23, S.click(0.12, i))
    m.put('amb', tc, S.drone([110.0, 164.8, 220.0], EP['t_end'] - tc, 0.18, 'sine'))
    for i, f in enumerate([659.3, 554.4, 440.0]): m.put('mus', tc + 0.8 + i * STEP, S.fm(f, 2.5, 0.3, 1.0, 1.5, 1.2))
    m.write(path, rev_mus=2.6, wet_mus=0.35)

EP = finalize(dict(t_coda=T_CODA, draw=draw, sound=sound, end_icon='heart', grain=0.0,
    title_en_card='YOU ARE A HEATER', title_ko_card='사람은 전구 하나만큼 따뜻하다',
    pal=dict(hi=(0.85, 0.35, 0.10), endbg=(0.98, 0.94, 0.88)),
    card_style=dict(box=None, ink=(0.98, 0.98, 0.98), hi=(1.0, 0.80, 0.35), y=150, fe=BLK, fk=BLK),
    cards=[(0.3, 3.6, ['Your body is', 'always giving off heat.'], ['내 몸은 늘', '열을 내고 있다']),
           (3.8, 8.6, ['At rest, about *100 watts*:', 'like an old light bulb.'], ['가만히 있어도 약 *100W*,', '백열전구 하나만큼']),
           (8.8, 13.4, ['A theater of 500 people', 'gives off about *50 kW*.'], ['500명이 모인 극장은', '약 *50kW*를 낸다']),
           (13.6, 18.6, ['That is why standing close', 'keeps us *warm*.'], ['그래서 가까이 있으면', '*따뜻하다*'])],
    coda=[('Just by being here,', '그저 곁에 있는 것만으로'), ('you warm the room for someone.', '당신은 누군가의 방을 데운다'), ('Never doubt your warmth.', '당신의 온기를 의심하지 말자')],
    coda_style=dict(dim=0.55, blur=10, tint=(0.05, 0.0, 0.08), ink=(0.98, 0.98, 0.98), hi=(1.0, 0.80, 0.35)),
    sources=['University of Illinois Physics Van: a normal person emits about 100 W of heat (estimates range ~60–100 W at rest).', 'Big Think: 500 people at ~100 W each ≈ 50 kW.'],
    yt=dict(title_en='Your Body Gives Off as Much Heat as a 100 W Bulb #Shorts', title_ko='사람은 100W 전구만큼 열을 낸다')))

if __name__ == '__main__': main(EP)
