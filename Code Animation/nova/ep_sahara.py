"""〈사하라가 초록이던 때〉 — 샌드 아트(빛 상자 위 모래: 따뜻한 역광, 모래 두께만큼 어두워지는 실루엣, 손가락으로 그은 가장자리의 알갱이), 소리는 레인스틱과 네이 피리.
사실: 약 11,000~5,000년 전 '초록 사하라'(아프리카 습윤기): 초원·호수·강이 있었고(deMenocal & Tierney 2012, Nature Education),
비는 지금의 약 10배(Tierney et al. 2017, Science Advances). 약 5,000년 전 비교적 짧은 기간에 끝났다(MIT Technology Review 2013).
지구 자전축의 세차 운동 때문에 대략 2만 년마다 되풀이된다(Eos). 고베로 유적에서 호숫가 사람들의 작살·생선뼈(Sereno, U. Chicago).
"""
import math, numpy as np, cv2, cairo
from base import *
import sfx as S

LIGHT1 = np.array((0.98, 0.86, 0.58)[::-1], np.float32); LIGHT2 = np.array((0.92, 0.55, 0.28)[::-1], np.float32)
SAND = np.array((0.16, 0.10, 0.06)[::-1], np.float32)
T_GREEN = 4.2; T_RAIN = 9.6; T_DRY = 14.8; T_CODA = 20.4
_r = np.random.default_rng(11000)
yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
GLOW = np.clip(1 - np.hypot((xx - W / 2) / W, (yy - H * 0.55) / H) * 1.1, 0, 1)[..., None]
BOX = LIGHT2 * (1 - GLOW) + LIGHT1 * GLOW
GRAIN = np.clip(1 + _r.normal(0, 0.35, (H, W)).astype(np.float32), 0.2, 1.8)
GRAIN2 = cv2.GaussianBlur(_r.normal(0, 1, (H, W)).astype(np.float32), (0, 0), 2.5)

def dunes(cr, a, y0=1450, bump=1.0):
    cr.set_source_rgba(0, 0, 0, a); cr.move_to(0, y0)
    for k in range(5):
        x = k * 270; cr.curve_to(x + 90, y0 - bump * (140 - 40 * (k % 2)), x + 180, y0 - 120 * bump, x + 270, y0 - 30 * (k % 2) * bump)
    cr.line_to(1080, 1920); cr.line_to(0, 1920); cr.fill()

def hippo(cr, x, y, sc, a):
    cr.save(); cr.translate(x, y); cr.scale(sc, sc); cr.set_source_rgba(0, 0, 0, a)
    cr.save(); cr.scale(1.6, 1); cr.arc(0, 0, 50, 0, 6.283); cr.restore(); cr.fill()
    cr.save(); cr.translate(95, -10); cr.scale(1.2, 0.8); cr.arc(0, 0, 32, 0, 6.283); cr.restore(); cr.fill()
    for lx in (-50, -20, 30, 55): cr.rectangle(lx, 30, 18, 34); cr.fill()
    cr.arc(84, -38, 8, 0, 6.283); cr.fill(); cr.restore()

def giraffe(cr, x, y, sc, a):
    cr.save(); cr.translate(x, y); cr.scale(sc, sc); cr.set_source_rgba(0, 0, 0, a)
    cr.save(); cr.scale(1.5, 0.8); cr.arc(0, 0, 40, 0, 6.283); cr.restore(); cr.fill()
    cr.move_to(35, -20); cr.line_to(95, -190); cr.line_to(115, -185); cr.line_to(60, 0); cr.close_path(); cr.fill()
    cr.save(); cr.translate(118, -195); cr.scale(1.5, 0.8); cr.arc(0, 0, 16, 0, 6.283); cr.restore(); cr.fill()
    for lx in (-45, -25, 25, 45): cr.rectangle(lx, 15, 10, 110); cr.fill()
    cr.restore()

def person(cr, x, y, sc, a):
    cr.save(); cr.translate(x, y); cr.scale(sc, sc); cr.set_source_rgba(0, 0, 0, a)
    cr.arc(0, -120, 16, 0, 6.283); cr.fill(); cr.move_to(-14, -100); cr.line_to(14, -100); cr.line_to(18, -30); cr.line_to(-18, -30); cr.fill()
    cr.rectangle(-14, -30, 10, 60); cr.fill(); cr.rectangle(4, -30, 10, 60); cr.fill()
    cr.set_line_width(5); cr.move_to(12, -90); cr.line_to(70, -150); cr.stroke(); cr.restore()        # 작살

def grass(cr, x0, x1, y, h, a, seed):
    rr = np.random.default_rng(seed); cr.set_source_rgba(0, 0, 0, a); cr.set_line_width(4)
    for k in range(int((x1 - x0) / 9)):
        x = x0 + k * 9 + rr.uniform(-3, 3); hh = h * rr.uniform(0.5, 1.2); lean = rr.uniform(-14, 14)
        cr.move_to(x, y); cr.curve_to(x, y - hh * 0.5, x + lean * 0.5, y - hh * 0.8, x + lean, y - hh); cr.stroke()

def draw(t):
    s, cr = surf()
    green = ramp(t, T_GREEN, T_GREEN + 2.0) * (1 - ramp(t, T_DRY, T_DRY + 2.4))
    dunes(cr, 1.0, 1450 + 240 * green, 1 - 0.85 * green)
    # 물결 모래 줄
    if t < T_GREEN + 1.0 or t > T_DRY + 1.0:
        a = 1 - green
        for k in range(6):
            cr.set_source_rgba(0, 0, 0, 0.35 * a); cr.set_line_width(5); cr.move_to(80, 1600 + k * 50)
            cr.curve_to(400, 1580 + k * 50, 700, 1630 + k * 50, 1000, 1600 + k * 50); cr.stroke()
    if green > 0:
        cr.set_operator(cairo.OPERATOR_CLEAR)                                  # 모래를 걷어 낸 호수 = 빛
        cr.save(); cr.translate(600, 1790); cr.scale(360 * green, 60 * green); cr.arc(0, 0, 1, 0, 6.283); cr.restore(); cr.fill()
        cr.set_operator(cairo.OPERATOR_OVER)
        grass(cr, 40, 1040, 1690, 110 * green, green, 7)
        cr.set_source_rgba(0, 0, 0, green); cr.set_line_width(14)               # 아카시아
        cr.move_to(190, 1690); cr.line_to(205, 1450); cr.stroke()
        cr.save(); cr.translate(205, 1435); cr.scale(170, 45); cr.arc(0, 0, 1, 0, 6.283); cr.restore(); cr.fill()
        hippo(cr, 600, 1580, 0.9, green * ramp(t, T_GREEN + 1.4, T_GREEN + 2.2))
        giraffe(cr, 850, 1560, 1.0, green * ramp(t, T_GREEN + 2.0, T_GREEN + 2.8))
        person(cr, 380, 1660, 1.0, green * ramp(t, T_GREEN + 2.6, T_GREEN + 3.4))
    if T_RAIN <= t < T_DRY + 1.0:                                              # 비: 위에서 긁어 낸 빛줄
        a = ramp(t, T_RAIN, T_RAIN + 0.6) * (1 - ramp(t, T_DRY, T_DRY + 0.8))
        cr.set_source_rgba(0, 0, 0, 0.9 * a)
        cr.save(); cr.translate(540, 720); cr.scale(420, 80); cr.arc(0, 0, 1, 0, 6.283); cr.restore(); cr.fill()
        for k in range(5):
            cr.arc(220 + k * 160, 680 - 40 * (k % 2), 100, 0, 6.283); cr.fill()
        cr.set_line_width(5)
        for k in range(26):
            x = 160 + (k * 97) % 780; ph = ((t - T_RAIN) * 1.4 + k * 0.37) % 1
            cr.move_to(x, 800 + ph * 260); cr.line_to(x - 8, 850 + ph * 260); cr.stroke()
        cr.set_source_rgba(0, 0, 0, a);
        txt(cr, 'today · 지금', 110, 1198, 42, (0, 0, 0), a, fam=BOLD, anchor='l')
        cr.rectangle(400, 1165, 52, 40); cr.fill()
        txt(cr, 'then · 그때', 110, 1298, 42, (0, 0, 0), a, fam=BOLD, anchor='l')
        g = ramp(t, T_RAIN + 0.8, T_RAIN + 2.6)
        cr.rectangle(400, 1265, 440 * g, 40); cr.fill()
        txt(cr, '×10', 1000, 1305, 64, (0, 0, 0), a * ramp(t, T_RAIN + 2.6, T_RAIN + 3.0), fam=BLK, anchor='r')
    if t >= T_DRY + 1.4:                                                        # 세차: 기울어진 팽이 지구
        a = ramp(t, T_DRY + 1.4, T_DRY + 2.0) * (1 - ramp(t, T_CODA - 0.4, T_CODA))
        cx, cy = 540, 800; ang = (t - T_DRY) * 0.8
        cr.set_source_rgba(0, 0, 0, a); cr.arc(cx, cy, 150, 0, 6.283); cr.fill()
        cr.set_line_width(8); tx, ty = math.sin(ang) * 70, -230
        cr.move_to(cx - tx, cy - ty); cr.line_to(cx + tx, cy + ty); cr.stroke()
        cr.set_line_width(4); cr.save(); cr.translate(cx, cy - 230); cr.scale(70, 18); cr.arc(0, 0, 1, 0, 6.283); cr.restore(); cr.stroke()
        txt(cr, '~20,000 years', 540, 1110, 60, (0, 0, 0), a, fam=BLK)
    d = arr(s)[..., 3]                                                          # 모래 두께
    d = np.clip(d + 0.25 * d * GRAIN2, 0, 1)
    edge = cv2.GaussianBlur(d, (0, 0), 3) - d
    thick = np.clip(d * GRAIN + np.clip(edge, 0, 1) * GRAIN * 1.2, 0, 1.6)
    trans = np.exp(-2.6 * thick)[..., None]
    img = BOX * trans + SAND * (1 - trans) * 0.5
    return np.clip(img, 0, 1).astype(np.float32)

def sound(path):
    m = S.Mix(EP['DUR'], 5000); tc = EP['t_coda']
    hij = [293.7, 311.1, 370.0, 392.0, 440.0, 466.2, 523.3, 587.3]           # 히자즈 느낌
    phrase = [(0, 2.2), (2, 1.6), (3, 1.2), (4, 3.0), (3, 1.4), (2, 1.4), (1, 2.6), (0, 3.4)]
    t = 0.6; k = 0
    while t < tc - 0.6:
        n, d = phrase[k % len(phrase)]; m.put('mus', t, S.ney(hij[n], min(d, tc - t), 0.26, seed=k)); t += d + 0.25; k += 1
    m.put('amb', 0, S.drone([73.4, 110.0], EP['t_end'] + 1, 0.10, 'sine'))
    m.put('fx', T_GREEN + 0.2, S.rainstick(3.0, 0.3, seed=1)); m.put('fx', T_RAIN, S.rainstick(5.0, 0.35, seed=2)); m.put('fx', T_DRY, S.swoosh(2.4, 0.2, 200, 1500))
    for i, f in enumerate([587.3, 440.0, 293.7]): m.put('mus', tc + 0.8 + i * STEP, S.ney(f, 2.6, 0.3, seed=50 + i))
    m.write(path, rev_mus=3.2, wet_mus=0.45)

EP = finalize(dict(t_coda=T_CODA, draw=draw, sound=sound, end_icon='star', grain=0.0,
    title_en_card='WHEN THE SAHARA WAS GREEN', title_ko_card='사하라가 초록이던 때',
    pal=dict(hi=(0.70, 0.30, 0.10), endbg=(0.98, 0.90, 0.70)),
    card_style=dict(box='paper', bg=(0.99, 0.93, 0.78), ink=(0.18, 0.10, 0.05), hi=(0.70, 0.30, 0.10), y=180, fe=BOLD, fk=BLK),
    cards=[(0.3, 4.0, ['The Sahara:', 'the largest hot desert on Earth.'], ['사하라,', '지구에서 가장 큰 더운 사막']),
           (4.2, 9.4, ['But *11,000 to 5,000* years ago', 'it had grass, lakes and hippos.'], ['그런데 *1만1천~5천 년* 전엔', '풀과 호수, 하마가 있었다']),
           (9.6, 14.6, ['It got about', '*10 times* more rain than today.'], ['비가 지금의', '약 *10배* 내렸다']),
           (14.8, 20.2, ['Earth’s wobble shifts the rains:', 'a green Sahara returns about every *20,000* years.'], ['자전축이 흔들리면서', '초록 사하라는 약 *2만 년*마다 돌아온다'])],
    coda=[('The greatest desert was once a garden.', '가장 큰 사막도 한때는 정원이었다'), ('Nothing stays as it is forever.', '어떤 것도 지금 그대로 머물지 않는다'), ('Even barren seasons can bloom again.', '메마른 계절도 다시 꽃필 수 있다')],
    coda_style=dict(dim=0.55, blur=8, tint=(0.95, 0.78, 0.50), ink=(0.18, 0.10, 0.05), hi=(0.70, 0.30, 0.10), fe=BOLD),
    sources=['Green Sahara / African Humid Period ~11,000–5,000 years ago, vegetation and lakes; paced by orbital changes ~every 20,000 years (deMenocal & Tierney 2012, Nature Education; Eos).', 'Rainfall about 10× today (Tierney et al. 2017, Science Advances). Gobero lakeside settlements with harpoons (Sereno, U. Chicago). Hippo/giraffe silhouettes illustrate Green Sahara fauna.'],
    yt=dict(title_en='The Sahara Was Green Just 6,000 Years Ago #Shorts', title_ko='사하라가 초록이던 때')))

if __name__ == '__main__': main(EP)
