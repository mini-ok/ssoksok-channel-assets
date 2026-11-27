"""〈빛은 1초에 지구를 7.5바퀴〉 — 초록 형광 CRT 터미널(고정폭 글씨, 주사선, 번짐, 가장자리 어둠), 소리는 모뎀 접속음과 FM 신스 삑삑이.
사실: 빛의 속도 299,792.458 km/s(정의값). 지구 둘레 40,075 km → 1초에 약 7.48바퀴(계산). 달까지 384,400 km → 약 1.3초(계산).
유리 광섬유 속에서는 굴절률(약 1.47) 때문에 약 3분의 2 속도 → 지구 반 바퀴(약 2만 km)에 약 0.1초(계산).
"""
import math, numpy as np, cv2, cairo
from base import *
import sfx as S

MONO = 'DejaVu Sans Mono'
GRN = (0.35, 1.0, 0.45); DIM = (0.12, 0.45, 0.18)
T_LAPS = 3.8; T_FIBER = 8.8; T_LIMIT = 13.6; T_CODA = 18.8
yy = np.arange(H, dtype=np.float32)[:, None]
SCAN = (0.78 + 0.22 * (np.sin(yy / SC * math.pi / 2.2) ** 2))[..., None]
_yy, _xx = np.mgrid[0:H, 0:W].astype(np.float32)
VIG = np.clip(1.25 - (((_xx / W - 0.5) * 2) ** 4 + ((_yy / H - 0.5) * 2) ** 4) ** 0.5 * 0.6, 0, 1)[..., None]

def term(cr, text, x, y, size, n, col=GRN, a=1.0):
    cr.select_font_face(MONO, cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD); cr.set_font_size(size); cr.set_source_rgba(*col, a)
    cr.move_to(x, y); cr.show_text(text[:max(0, int(n))])
    if 0 <= n < len(text) + 4 and int(n * 2) % 2 == 0:
        e = cr.text_extents(text[:max(0, int(n))]).x_advance; cr.rectangle(x + e + 4, y - size * 0.8, size * 0.55, size * 0.9); cr.fill()

def draw(t):
    s, cr = surf(); cps = 26
    lines = ['> c = speed_of_light()', '  299,792 km/s']
    for k, ln in enumerate(lines):
        term(cr, ln, 90, 560 + k * 64, 42, (t - 0.3 - k * 1.2) * cps, GRN if k else DIM)
    if T_LAPS - 0.2 < t:
        term(cr, '> run circle_earth --time 1.0s', 90, 720, 36, (t - T_LAPS + 0.2) * cps, DIM)
    if T_LAPS <= t < T_FIBER:
        cx, cy, R = 540, 1160, 300; u = ramp(t, T_LAPS + 0.6, T_LAPS + 4.2); laps = 7.48 * u
        for k in range(72):                                            # 점으로 그린 지구
            a_ = k * 6.283 / 72; cr.set_source_rgba(*DIM, 1); cr.arc(cx + R * math.cos(a_), cy + R * math.sin(a_), 4, 0, 6.283); cr.fill()
        cr.select_font_face(MONO); cr.set_font_size(48); cr.set_source_rgba(*GRN, 0.7)
        for j, row in enumerate(['   ..::##::..   ', ' .:####::###:. ', ':###::....:####', ' :##:...::##: ', '   ..:::::..   ']):
            cr.move_to(cx - 225, cy - 120 + j * 62); cr.show_text(row)
        ph = laps * 6.283 - math.pi / 2
        for k in range(30):
            a_ = ph - k * 0.06; cr.set_source_rgba(*GRN, 1 - k / 30); cr.arc(cx + R * math.cos(a_), cy + R * math.sin(a_), 12 - k * 0.3, 0, 6.283); cr.fill()
        term(cr, f't = {u:0.2f} s', 90, 1580, 52, 99); term(cr, f'laps = {laps:0.2f}', 90, 1660, 52, 99)
    if T_FIBER <= t < T_LIMIT:
        rows = [('> moon', '384,400 km', '1.28 s'), ('> fibre, half the world', '20,000 km', '≈0.10 s'), ('> sun', '150,000,000 km', '8 m 20 s')]
        for k, (a, b, c) in enumerate(rows):
            n = (t - T_FIBER - 0.3 - k * 1.1) * cps
            term(cr, a, 90, 860 + k * 200, 40, n, DIM); term(cr, b, 120, 920 + k * 200, 40, n - 10); term(cr, c, 700, 920 + k * 200, 44, n - 20)
        term(cr, '* light in glass ≈ 2/3 speed', 90, 1500, 30, (t - T_FIBER - 3.0) * cps, DIM)
    if T_LIMIT <= t < T_CODA:
        u = smooth(ramp(t, T_LIMIT + 0.4, T_LIMIT + 3.0)); w = 900
        term(cr, '> try go_faster()', 90, 900, 40, (t - T_LIMIT) * cps, DIM)
        cr.set_source_rgba(*GRN, 1); cr.set_line_width(3); cr.rectangle(90, 1000, w, 60); cr.stroke(); cr.rectangle(96, 1006, (w - 12) * u * 0.999, 48); cr.fill()
        term(cr, f'{u * 99.99:5.2f}% of c', 90, 1140, 44, 99)
        if u > 0.98: term(cr, 'ERROR: limit reached', 90, 1240, 44, (t - T_LIMIT - 3.0) * cps, (1.0, 0.45, 0.35))
    a = arr(s)[..., :3]
    glow = cv2.GaussianBlur(a, (0, 0), 5 * SC) * 0.9 + cv2.GaussianBlur(a, (0, 0), 18 * SC) * 0.5
    img = (np.array((0.02, 0.05, 0.02), np.float32) + a + glow) * SCAN * VIG
    flick = 1 + 0.015 * math.sin(t * 60)
    return img * flick

def sound(path):
    m = S.Mix(EP['DUR'], 231); tc = EP['t_coda']
    m.put('fx', 0.2, S.modem(1.6, 0.35, 1))
    r = np.random.default_rng(3)
    for t in np.arange(0.3, tc, 1 / 13):                                # 글자 칠 때 작은 소리
        if r.random() < 0.55: m.put('fx', t, S.click(0.06, int(t * 100)))
    seq = [880.0, 1318.5, 1174.7, 987.8, 880.0, 1174.7, 1318.5, 1760.0]
    for k, t in enumerate(np.arange(T_LAPS + 0.6, T_LAPS + 4.2, 3.6 / 7.48)): m.put('mus', t, S.fm(seq[k % 8], 0.4, 0.22, 3.0, 2.5, 0.2))
    m.put('amb', 0, S.drone([55.0, 110.0], EP['t_end'] + 1, 0.12, 'saw'))
    for k in range(3): m.put('fx', T_FIBER + 0.3 + k * 1.1, S.beep(1400 + k * 200, 0.12, 0.25))
    n = int((T_LIMIT + 3.0 - T_LIMIT - 0.4) / 0.08)
    for k in range(n): m.put('fx', T_LIMIT + 0.4 + k * 0.08, S.beep(400 + k * 25, 0.05, 0.15))
    m.put('fx', T_LIMIT + 3.1, S.beep(220, 0.5, 0.35))
    m.put('amb', tc, S.drone([110.0, 164.8, 220.0], EP['t_end'] - tc, 0.15, 'sine'))
    for i, f in enumerate([1318.5, 1174.7, 880.0]): m.put('mus', tc + 0.8 + i * STEP, S.fm(f, 2.4, 0.28, 2.0, 1.5, 1.0))
    m.write(path, rev_mus=2.0, wet_mus=0.3)

EP = finalize(dict(t_coda=T_CODA, draw=draw, sound=sound, end_icon='star', grain=0.0,
    title_en_card='7.5 LAPS A SECOND', title_ko_card='빛은 1초에 지구를 7.5바퀴',
    pal=dict(hi=(0.10, 0.55, 0.20), endbg=(0.92, 0.98, 0.92)),
    card_style=dict(box=None, ink=(0.80, 1.0, 0.82), hi=GRN, y=150, fe=BLK, fk=BLK),
    cards=[(0.3, 3.6, ['How fast is light?'], ['빛은 얼마나 빠를까?']),
           (3.8, 8.6, ['In one second, it circles Earth', '*7.5 times*.'], ['1초에 지구를', '*7.5바퀴* 돈다']),
           (8.8, 13.4, ['Your message across the world', 'travels in about *0.1 s*.'], ['지구 반대편으로 보낸 말은', '약 *0.1초*면 닿는다']),
           (13.6, 18.6, ['And nothing can go', '*faster than light*.'], ['그리고 무엇도', '*빛보다 빠를 수 없다*'])],
    coda=[('Even light needs time to reach us.', '빛조차 우리에게 닿는 데 시간이 걸린다'), ('Every message is a small journey.', '모든 말은 작은 여행이다'), ('Send the words worth the trip.', '먼 길을 갈 만한 말을 보내자')],
    coda_style=dict(dim=0.55, blur=8, tint=(0.0, 0.03, 0.0), ink=(0.80, 1.0, 0.82), hi=GRN),
    sources=['Speed of light 299,792.458 km/s (SI definition). Earth circumference 40,075 km → ~7.5 laps per second (calculated).', 'Moon 384,400 km → 1.28 s; light in optical fibre ≈ 2/3 c (refractive index ~1.47) → ~0.1 s for 20,000 km (calculated).'],
    yt=dict(title_en='Light Circles Earth 7.5 Times in One Second #Shorts', title_ko='빛은 1초에 지구를 7.5바퀴 돈다')))

if __name__ == '__main__': main(EP)
