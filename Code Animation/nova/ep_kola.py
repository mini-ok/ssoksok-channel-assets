"""〈인류가 판 가장 깊은 구멍〉 — 스크래치보드(검은 판을 긁어 드러난 흰 선, 평행 해칭·교차 해칭으로 명암), 소리는 금속 드론과 드릴.
사실: 콜라 초심부 시추공 SG-3, 1970년 5월 24일 시작, 1989년 12,262 m 도달, 지금도 가장 깊은 인공 구멍. 지름 23 cm(Wikipedia; Earthdate).
바닥 온도 약 180 °C로 예상(약 100 °C)보다 높았고, 발트 대륙 지각의 약 3분의 1까지 뚫었다(Atlas Obscura).
에베레스트 높이 8,849 m보다 깊다, 지구 반지름 6,371 km의 약 0.19%(계산).
"""
import math, numpy as np, cv2, cairo
from base import *
import sfx as S

WHITE = (0.96, 0.94, 0.90); RED = (0.92, 0.36, 0.22); BLACK = (0.04, 0.04, 0.05)
T_DEPTH = 4.0; T_CRUST = 9.6; T_EARTH = 15.0; T_CODA = 20.6

def hatch(cr, path_fn, ang, gap, w=2.0, col=WHITE, a=1.0, wobble=0.0):
    cr.save(); path_fn(); cr.clip()
    ca, sa = math.cos(ang), math.sin(ang); cr.set_source_rgba(*col, a); cr.set_line_width(w)
    n_ = int(1800 / gap) + 1
    for k in range(-n_, n_):
        d = k * gap
        x0, y0 = 540 + ca * -1600 - sa * d, 960 + sa * -1600 + ca * d
        x1, y1 = 540 + ca * 1600 - sa * d, 960 + sa * 1600 + ca * d
        cr.move_to(x0, y0)
        if wobble:
            for s_ in range(1, 9):
                u = s_ / 8; cr.line_to(x0 + (x1 - x0) * u + wobble * math.sin(k * 1.7 + s_), y0 + (y1 - y0) * u)
        else: cr.line_to(x1, y1)
    cr.stroke(); cr.restore()

def rig(cr, a):
    cr.set_source_rgba(*WHITE, a); cr.set_line_width(4)
    for (x0, y0, x1, y1) in [(470, 760, 520, 420), (610, 760, 560, 420), (520, 420, 560, 420), (480, 700, 600, 700), (490, 620, 590, 620), (500, 540, 580, 540)]:
        cr.move_to(x0, y0); cr.line_to(x1, y1); cr.stroke()
    for (x0, y0, x1, y1) in [(480, 700, 590, 620), (600, 700, 490, 620), (490, 620, 580, 540), (590, 620, 500, 540)]:
        cr.move_to(x0, y0); cr.line_to(x1, y1); cr.stroke()
    hatch(cr, lambda: cr.rectangle(380, 760, 320, 70), 0.6, 9, 2, WHITE, a)
    cr.set_source_rgba(*RED, a); cr.rectangle(536, 760, 8, 1100); cr.fill()

def draw(t):
    s, cr = surf(); cr.set_source_rgb(*BLACK); cr.paint()
    if t < T_DEPTH:                                                     # 지상: 시추탑과 지층
        a = 1 - ramp(t, T_DEPTH - 0.4, T_DEPTH)
        hatch(cr, lambda: cr.rectangle(0, 1030, 1080, 900), -0.5, 14, 2, WHITE, 0.55 * a, wobble=3)
        cr.save(); cr.translate(0, 200); rig(cr, a); cr.restore()
        txt(cr, 'Ø 23 cm', 700, 1200, 56, WHITE, a * ramp(t, 1.4, 1.8), fam=BOLD, anchor='l')
        cr.set_source_rgba(*WHITE, a * ramp(t, 1.4, 1.8)); cr.set_line_width(3); cr.move_to(560, 1190); cr.line_to(690, 1190); cr.stroke()
    elif t < T_CRUST:                                                   # 깊이 계기 + 뒤집은 에베레스트
        a = ramp(t, T_DEPTH, T_DEPTH + 0.4) * (1 - ramp(t, T_CRUST - 0.4, T_CRUST))
        g = smooth(ramp(t, T_DEPTH + 0.5, T_DEPTH + 4.0)); top, bot = 660, 1720
        sc = (bot - top) / 12262
        ev = 8849 * sc
        hatch(cr, lambda: (cr.move_to(320, top), cr.line_to(140, top + ev), cr.line_to(500, top), cr.close_path()), 0.9, 10, 2, WHITE, 0.7 * a)
        txt(cr, 'Everest 8,849 m', 320, top + ev + 60, 36, WHITE, a * ramp(t, T_DEPTH + 2.0, T_DEPTH + 2.4), fam=BOLD)
        cr.set_source_rgba(*WHITE, a); cr.set_line_width(3); cr.move_to(80, top); cr.line_to(1000, top); cr.stroke()
        cr.set_source_rgba(*RED, a); cr.rectangle(700, top, 12, (bot - top) * g); cr.fill()
        for k in range(0, 13):
            y = top + k * 1000 * sc; cr.set_source_rgba(*WHITE, a * 0.7); cr.set_line_width(2); cr.move_to(730, y); cr.line_to(760, y); cr.stroke()
            if k % 2 == 0: txt(cr, f'{k} km', 780, y + 12, 28, WHITE, a * 0.8, fam=BOLD, anchor='l')
        txt(cr, f'{int(12262 * g):,} m', 680, top + (bot - top) * g + 20, 60, RED, a, fam=BLK, anchor='r')
        txt(cr, '1970 → 1989', 706, top - 30, 40, WHITE, a, fam=BOLD)
    elif t < T_EARTH:                                                   # 지각 단면
        a = ramp(t, T_CRUST, T_CRUST + 0.4) * (1 - ramp(t, T_EARTH - 0.4, T_EARTH))
        top, bot = 600, 1700
        hatch(cr, lambda: cr.rectangle(80, top, 920, (bot - top) * 0.85), 0.4, 12, 2, WHITE, 0.5 * a, wobble=2)
        hatch(cr, lambda: cr.rectangle(80, top, 920, (bot - top) * 0.85), -0.4, 18, 1.5, WHITE, 0.3 * a)
        hatch(cr, lambda: cr.rectangle(80, top + (bot - top) * 0.85, 920, (bot - top) * 0.15), 0.0, 6, 3, RED, 0.7 * a)
        txt(cr, 'crust · 지각 (~35–40 km)', 770, top + 60, 38, WHITE, a, fam=BOLD)
        txt(cr, 'mantle · 맨틀', 540, bot - 30, 38, WHITE, a, fam=BOLD)
        g = smooth(ramp(t, T_CRUST + 0.4, T_CRUST + 2.0)); dep = (bot - top) * 0.85 / 3
        cr.set_source_rgba(*RED, a); cr.rectangle(536, top, 8, dep * g); cr.fill()
        cr.set_source_rgba(*BLACK, a); cr.rectangle(560, top + dep - 50, 420, 110); cr.fill()
        txt(cr, '~1/3 · 180 °C', 580, top + dep + 20, 56, RED, a * ramp(t, T_CRUST + 2.0, T_CRUST + 2.4), fam=BLK, anchor='l')
    else:                                                               # 지구 전체에서는 긁힌 자국 하나
        a = ramp(t, T_EARTH, T_EARTH + 0.4) * (1 - ramp(t, T_CODA - 0.4, T_CODA))
        cx, cy, R = 540, 1220, 380
        def disc(): cr.arc(cx, cy, R, 0, 6.283)
        hatch(cr, disc, 0.7, 11, 2, WHITE, 0.6 * a, wobble=2)
        def core(): cr.arc(cx, cy, R * 0.55, 0, 6.283)
        hatch(cr, core, -0.7, 9, 2, RED, 0.6 * a)
        cr.set_source_rgba(*WHITE, a); cr.set_line_width(4); disc(); cr.stroke()
        hole = R * 12.262 / 6371
        cr.set_source_rgba(*RED, a); cr.rectangle(cx - 3, cy - R, 6, max(hole, 1.5)); cr.fill()
        cr.set_line_width(3); cr.arc(cx, cy - R, 40, 0, 6.283); cr.stroke()
        cr.move_to(cx + 30, cy - R - 30); cr.line_to(cx + 160, cy - R - 120); cr.stroke()
        txt(cr, '0.19%', cx + 170, cy - R - 130, 72, RED, a * ramp(t, T_EARTH + 1.0, T_EARTH + 1.4), fam=BLK, anchor='l')
        txt(cr, 'of the way to the center · 중심까지의', 540, cy + R + 90, 34, WHITE, a * ramp(t, T_EARTH + 1.4, T_EARTH + 1.8), fam=BOLD)
    a = arr(s)
    return np.ascontiguousarray(a[..., :3])

def sound(path):
    m = S.Mix(EP['DUR'], 12262); tc = EP['t_coda']
    m.put('amb', 0, S.metaldrone(tc + 0.5, 0.18, seed=1))
    m.put('fx', 0.6, S.drill(3.0, 0.22, seed=2)); m.put('fx', T_DEPTH + 0.5, S.drill(3.6, 0.26, seed=3))
    for k in range(13): m.put('fx', T_DEPTH + 0.5 + k * 3.5 / 13, S.tok(300 - 12 * k, 0.12))
    m.put('fx', T_CRUST + 2.0, S.thunder(2.5, 0.25, seed=4) if hasattr(S, 'thunder') else S.kick(40, 0.4))
    m.put('fx', T_EARTH + 1.0, S.bell(220.0, 3.0, 0.22))
    m.put('amb', tc, S.drone([55.0, 82.4], EP['t_end'] - tc, 0.12, 'sine'))
    for i, f in enumerate([220.0, 164.8, 110.0]): m.put('mus', tc + 0.8 + i * STEP, S.bell(f, 3.0, 0.25))
    m.write(path, rev_mus=3.0, wet_mus=0.45)

EP = finalize(dict(t_coda=T_CODA, draw=draw, sound=sound, end_icon='star', grain=0.0,
    title_en_card='THE DEEPEST HOLE', title_ko_card='인류가 판 가장 깊은 구멍',
    pal=dict(hi=RED, endbg=(0.94, 0.92, 0.88)),
    card_style=dict(box='paper', bg=(0.96, 0.94, 0.90), ink=(0.06, 0.06, 0.07), hi=(0.75, 0.22, 0.12), y=180, fe=BOLD, fk=BLK),
    cards=[(0.3, 3.8, ['In 1970, the USSR began', 'drilling a hole *23 cm* wide.'], ['1970년 소련이 지름 *23cm*', '구멍을 뚫기 시작했다']),
           (4.0, 9.4, ['By 1989 it reached *12,262 m*,', 'still the deepest hole ever dug.'], ['1989년 *12,262m*,', '지금도 가장 깊은 구멍']),
           (9.6, 14.8, ['Yet it went only about *1/3*', 'through the crust. It was 180 °C.'], ['그래도 지각의 약 *3분의 1*,', '바닥은 180°C']),
           (15.0, 20.4, ['On the whole Earth', 'it is just a *scratch*.'], ['지구 전체로 보면', '*긁힌 자국* 하나'])],
    coda=[('Twenty years of drilling', '20년을 파 내려가'), ('reached only the skin of the Earth.', '겨우 지구의 껍질에 닿았다'), ('Know how little we know, and keep digging.', '모르는 게 많음을 알고, 계속 파 보자')],
    coda_style=dict(dim=0.6, blur=8, tint=(0.20, 0.20, 0.22), ink=WHITE, hi=RED, fe=BOLD),
    sources=['Kola Superdeep Borehole SG-3: drilling began 24 May 1970, reached 12,262 m in 1989, deepest human-made hole; 23 cm diameter (Wikipedia; Earthdate).', 'Bottom ~180 °C vs ~100 °C expected; about a third through the Baltic continental crust (Atlas Obscura). 12.262/6,371 km ≈ 0.19% (calculated).'],
    yt=dict(title_en='20 Years of Drilling Barely Scratched the Earth #Shorts', title_ko='인류가 판 가장 깊은 구멍, 콜라 시추공')))

if __name__ == '__main__': main(EP)
