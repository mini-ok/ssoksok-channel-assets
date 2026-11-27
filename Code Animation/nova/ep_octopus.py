"""〈심장이 셋인 동물〉 — 심해 생물발광 선화(검푸른 바다, 빛나는 선, 가산 합성), 소리는 수중 저음·소나·거품·세 박 심장 소리.
사실: 문어는 심장이 셋(아가미 심장 2, 체순환 심장 1). 피는 구리 기반 헤모시아닌이라 푸르다.
체순환 심장은 헤엄칠 때 뛰기를 멈춘다 → 헤엄은 지치게 해서 기어 다니기를 더 한다.
(Smithsonian Magazine "Ten Wild Facts About Octopuses"; Shedd Aquarium; Live Science — Kirt Onthank 인터뷰)
"""
import math, numpy as np, cv2, cairo
from base import *
import sfx as S

BG_T = np.array((0.10, 0.05, 0.015), np.float32); BG_B = np.array((0.025, 0.008, 0.0), np.float32)   # BGR
CY = (0.35, 0.95, 1.0); BL = (0.25, 0.45, 1.0); MG = (1.0, 0.35, 0.75); AMB = (1.0, 0.78, 0.35)

T_HEART = 3.8; T_BLOOD = 8.4; T_SWIM = (13.6, 17.0); T_CRAWL = 18.8; T_CODA = 23.0

def _bg():
    y = np.linspace(0, 1, H, dtype=np.float32)[:, None, None]
    return np.broadcast_to(BG_T * (1 - y) + BG_B * y, (H, W, 3)).copy()
BG = _bg()
_r = np.random.default_rng(5)
SNOW = np.stack([_r.uniform(0, DW, 260), _r.uniform(0, DH, 260), _r.uniform(0.5, 2.2, 260), _r.uniform(0, 6.283, 260)], 1)

def swim(t):
    """0 = 바닥에 있음, 1 = 헤엄치는 중."""
    return smooth(ramp(t, T_SWIM[0], T_SWIM[0] + 0.6)) * (1 - smooth(ramp(t, T_SWIM[1], T_SWIM[1] + 0.9)))

def body_pos(t):
    sw = swim(t); up = smooth(ramp(t, T_SWIM[0], T_SWIM[1])) * (1 - smooth(ramp(t, T_SWIM[1], T_SWIM[1] + 1.4)))
    x = 540 + 30 * math.sin(t * 0.4) + 60 * smooth(ramp(t, T_CRAWL, T_CODA)) * math.sin((t - T_CRAWL) * 0.9)
    y = 920 - 260 * up + 6 * math.sin(t * 1.3)
    return x, y, sw

def beat(t, period, phase=0.0):
    u = ((t + phase) % period) / period
    return math.exp(-((u - 0.05) / 0.05) ** 2) + 0.45 * math.exp(-((u - 0.22) / 0.05) ** 2)

def systemic_on(t): return 0.0 if T_SWIM[0] + 0.4 < t < T_SWIM[1] + 0.2 else 1.0

def arm_pts(t, i, cx, cy, sw):
    th = math.radians(lerp(-160, -20, i / 7)); th = lerp(th, math.radians(-90 + (i - 3.5) * 3), sw)
    dx, dy = math.cos(th), -math.sin(th)
    L = lerp(430 + 40 * math.sin(i * 1.7), 520, sw)
    s = np.linspace(0, 1, 48); amp = lerp(70, 16, sw) * s
    wv = np.sin(s * 5.5 - t * lerp(2.0, 6.0, sw) + i * 0.9)
    curl = lerp(1.0, 0.1, sw) * s ** 3 * 90 * (1 if i < 4 else -1)
    bx, by = cx + (i - 3.5) * 22, cy + 210
    px = bx + dx * L * s - dy * (amp * wv + curl); py = by + dy * L * s + dx * (amp * wv + curl)
    return np.stack([px, py], 1)

def glow(cr_draw):
    s, cr = surf(); cr_draw(cr); a = arr(s)[..., :3]
    return a + cv2.GaussianBlur(a, (0, 0), 9 * SC) * 1.7 + cv2.GaussianBlur(a, (0, 0), 30 * SC) * 0.9

def draw(t):
    L = []
    def T_(*a, **k): L.append((a, k))
    cx, cy, sw = body_pos(t)
    reveal = smooth(ramp(t, 0.2, 2.6)); xr = smooth(ramp(t, T_HEART, T_HEART + 0.8)) * (1 - 0.4 * ramp(t, T_CODA, T_CODA + 1))
    def lines(cr):
        # 바다 눈(마린 스노)
        for x, y, r, ph in SNOW:
            yy = (y + t * 14 * r) % DH; xx = x + 8 * math.sin(t * 0.5 + ph)
            cr.set_source_rgba(0.55, 0.75, 0.85, 0.10 + 0.06 * r); cr.arc(xx, yy, r * 1.1, 0, 6.283); cr.fill()
        # 팔 8개(끝으로 갈수록 가늘게, 빨판 점)
        for i in range(8):
            P = arm_pts(t, i, cx, cy, sw); n = int(len(P) * reveal)
            for k in range(1, n):
                w = lerp(13, 1.5, k / len(P)); cr.set_line_width(w * 0.55)
                cr.set_source_rgba(*CY, 0.9); cr.move_to(*P[k - 1]); cr.line_to(*P[k]); cr.stroke()
            for k in range(4, n, 4):
                q = P[k]; d = P[k] - P[k - 1]; nn = np.array([-d[1], d[0]]) / (np.hypot(*d) + 1e-6)
                cr.set_source_rgba(*CY, 0.45); cr.set_line_width(1.3); cr.arc(*(q + nn * lerp(7, 2, k / len(P))), lerp(4.5, 1.2, k / len(P)), 0, 6.283); cr.stroke()
        # 외투막(머리처럼 보이는 몸통)
        if reveal > 0:
            squash = 1 + 0.12 * sw
            cr.save(); cr.translate(cx, cy); cr.scale(1 / squash, squash)
            cr.set_source_rgba(*CY, reveal); cr.set_line_width(4.5)
            cr.move_to(-120, 150); cr.curve_to(-200, -40, -150, -230, 0, -240); cr.curve_to(150, -230, 200, -40, 120, 150)
            cr.curve_to(95, 205, -95, 205, -120, 150); cr.stroke()
            for k in range(1, 6):                                   # 등 무늬
                cr.set_source_rgba(*CY, 0.25 * reveal); cr.set_line_width(1.5); cr.arc(0, -40, 40 + k * 26, math.radians(205), math.radians(335)); cr.stroke()
            cr.restore()
            for sx in (-1, 1):                                      # 눈
                ex, ey = cx + sx * 78, cy + 150
                cr.set_source_rgba(*AMB, reveal); cr.set_line_width(3); cr.arc(ex, ey, 22, 0, 6.283); cr.stroke()
                cr.rectangle(ex - 12, ey - 3, 24, 6); cr.fill()
        # 투시: 심장 셋 + 아가미 + 피 흐름
        if xr > 0:
            br = [beat(t, 0.95, 0.0), beat(t, 0.95, 0.0)]; sy = beat(t, 0.95, -0.18) * systemic_on(t)
            for j, sx in enumerate((-1, 1)):
                gx, gy = cx + sx * 95, cy - 10
                cr.set_source_rgba(*CY, 0.55 * xr); cr.set_line_width(2)          # 아가미(깃털)
                for k in range(7):
                    yy = gy - 60 + k * 16; cr.move_to(gx + sx * 10, yy); cr.line_to(gx + sx * (40 + 6 * math.sin(k)), yy - 10); cr.stroke()
                hx, hy = cx + sx * 70, cy + 50; r = 17 * (1 + 0.28 * br[j])
                cr.set_source_rgba(*BL, 0.9 * xr); cr.arc(hx, hy, r, 0, 6.283); cr.fill()
            hx, hy = cx, cy + 95; r = 30 * (1 + 0.3 * sy)
            cr.set_source_rgba(*MG, (0.35 + 0.6 * (0.3 + 0.7 * systemic_on(t))) * xr); cr.arc(hx, hy, r, 0, 6.283); cr.fill()
            bl = ramp(t, T_BLOOD, T_BLOOD + 0.6) * xr
            if bl > 0:                                               # 피 알갱이: 체순환 → 몸 → 아가미 심장 → 아가미 → 체순환
                for sx in (-1, 1):
                    path = np.array([(cx, cy + 95), (cx + sx * 20, cy + 230), (cx + sx * 150, cy + 250), (cx + sx * 70, cy + 50), (cx + sx * 120, cy - 50), (cx + sx * 40, cy + 20), (cx, cy + 95)])
                    seg = np.hypot(*np.diff(path, axis=0).T); cum = np.r_[0, np.cumsum(seg)]
                    for k in range(14):
                        d = ((t - T_BLOOD) * 120 * (0.25 + 0.75 * systemic_on(t)) + k * cum[-1] / 14) % cum[-1]
                        j = np.searchsorted(cum, d) - 1; f = (d - cum[j]) / seg[j]; p = path[j] + (path[j + 1] - path[j]) * f
                        oxy = 1.0 if j >= 4 or j == 0 else 0.45
                        cr.set_source_rgba(BL[0] * oxy + 0.2, BL[1] * oxy + 0.3 * oxy, BL[2], bl); cr.arc(*p, 5, 0, 6.283); cr.fill()
            la = xr * (1 - ramp(t, T_BLOOD - 0.3, T_BLOOD))
            if la > 0:
                T_('Gill hearts ×2', cx - 330, cy + 40, 32, BL, la, fam=BOLD); T_('아가미 심장 2개', cx - 330, cy + 80, 30, BL, la, fam=BOLD)
                T_('Body heart ×1', cx + 330, cy + 120, 32, MG, la, fam=BOLD); T_('온몸 심장 1개', cx + 330, cy + 160, 30, MG, la, fam=BOLD)
        # 구리 vs 철
        ca = ramp(t, T_BLOOD + 0.4, T_BLOOD + 0.9) * (1 - ramp(t, T_SWIM[0] - 0.6, T_SWIM[0] - 0.2))
        if ca > 0:
            for k, (sym, nm, col, xx) in enumerate((('Fe', 'iron → red · 철 → 붉은 피 (우리)', (1.0, 0.3, 0.3), 270), ('Cu', 'copper → blue · 구리 → 푸른 피 (문어)', BL, 810))):
                cr.set_source_rgba(*col, ca); cr.set_line_width(4); cr.arc(xx, 1560, 62, 0, 6.283); cr.stroke()
                T_(sym, xx, 1584, 60, col, ca, fam=BLK); T_(nm, xx, 1680, 28, col, ca, fam=BOLD, maxw=500)
        # 체순환 심장 심전도
        ea = ramp(t, T_SWIM[0] - 0.4, T_SWIM[0]) * (1 - ramp(t, T_CODA - 0.4, T_CODA))
        if ea > 0:
            x0, x1, y0 = 140, 940, 1640; cr.set_line_width(4); cr.set_source_rgba(*MG, ea)
            for k in range(120):
                x = lerp(x0, x1, k / 119); tt = t - (1 - k / 119) * 2.4
                yv = y0 - 80 * beat(tt, 0.95, -0.18) * systemic_on(tt)
                (cr.move_to if k == 0 else cr.line_to)(x, yv)
            cr.stroke()
            on = systemic_on(t); T_('Body heart · 온몸 심장', 540, 1730, 32, MG, ea, fam=BOLD)
            if on < 0.5: T_('STOPPED while swimming · 헤엄칠 땐 멈춤', 540, 1790, 34, (1, 1, 1), ea, fam=BLK)
    g = glow(lines)
    s2, c2 = surf()
    for a, k in L: txt(c2, *a, **k)
    return over(BG + g * 0.9, s2)

def sound(path):
    m = S.Mix(EP['DUR'], 31); tc = EP['t_coda']
    m.put('amb', 0, S.rumble(EP['t_end'] + 1, 0.5)); m.put('amb', 0, S.drone([41.2, 61.7], EP['t_end'] + 1, 0.15, 'sine'))
    for k, t in enumerate(np.arange(0.6, tc, 3.2)): m.put('fx', t, S.sonar(1400 - 60 * (k % 3), 0.35))
    t = T_HEART
    while t < tc - 0.2:                                           # 세 박 심장: 둥·둥(아가미) + 쿵(온몸)
        m.put('fx', t, S.kick(70, 0.35, 0.18)); m.put('fx', t + 0.09, S.kick(66, 0.3, 0.18))
        if systemic_on(t + 0.18): m.put('fx', t + 0.2, S.kick(46, 0.75, 0.4))
        t += 0.95
    m.put('fx', T_SWIM[0], S.swoosh(1.2, 0.5, 200, 1800)); m.put('fx', T_SWIM[0], S.bubbles(3.0, 14, 0.5))
    m.put('fx', T_SWIM[0] + 0.45, S.ping(660, 0.25, 1.6))
    for k, f in enumerate([196.0, 233.1, 293.7, 349.2]): m.put('mus', T_BLOOD + k * 0.4, S.bell(f * 2, 2.5, 0.22))
    m.put('amb', tc, S.drone([98.0, 146.8, 196.0], EP['t_end'] - tc, 0.25, 'sine'))
    for i in range(3): m.put('mus', tc + 0.8 + i * STEP, S.bell([392.0, 466.2, 587.3][i], 3.5, 0.32))
    m.put('fx', EP['t_end'] + 0.2, S.sonar(1100, 0.4))
    m.write(path, rev_mus=3.0, wet_mus=0.4)

EP = finalize(dict(t_coda=T_CODA, draw=draw, sound=sound, end_icon='heart', grain=0.006,
    title_en_card='THREE HEARTS', title_ko_card='심장이 셋인 동물',
    pal=dict(hi=BL, endbg=(0.92, 0.95, 0.98)),
    card_style=dict(box=None, ink=(0.9, 0.97, 1.0), hi=CY, y=150, fe=BLK, fk=BLK),
    cards=[(0.3, 3.6, ['An octopus has', '*three hearts.*'], ['문어의 심장은 *세 개*']),
           (3.8, 8.2, ['Two pump blood through the gills.', 'One pumps it to the body.'], ['둘은 아가미로 피를 보내고', '하나는 온몸으로 보낸다']),
           (8.4, 13.2, ['And the blood is *blue*:', 'copper, not iron, carries its oxygen.'], ['피는 *파랗다*', '철 대신 구리가 산소를 나른다']),
           (13.4, 18.6, ['When it swims,', 'the body heart *stops beating.*'], ['헤엄칠 때는', '온몸 심장이 *멈춘다*']),
           (18.8, 22.8, ['Swimming wears it out.', 'So it would rather *crawl.*'], ['헤엄은 문어를 지치게 한다', '그래서 문어는 *기어서* 간다'])],
    coda=[('Three hearts. Blue blood.', '심장 셋, 푸른 피'), ('Built differently, not wrongly.', '다르게 만들어졌을 뿐, 틀린 게 아니다'), ('Go the way your heart can keep beating.', '심장이 멈추지 않는 속도로 가자')],
    coda_style=dict(dim=0.55, blur=8, tint=(0.0, 0.02, 0.06), ink=(0.9, 0.97, 1.0), hi=CY),
    sources=['Smithsonian Magazine, "Ten Wild Facts About Octopuses" (three hearts; systemic heart stops while swimming; copper-based blue blood).', 'Shedd Aquarium; Live Science (Kirt Onthank, Walla Walla University).'],
    yt=dict(title_en='An Octopus Has Three Hearts, and One Stops When It Swims #Shorts', title_ko='문어의 심장은 셋, 헤엄칠 땐 하나가 멈춘다')))

if __name__ == '__main__': main(EP)
