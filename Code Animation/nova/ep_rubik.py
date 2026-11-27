"""〈아무리 섞여도 20수〉 — 바우하우스(빨강·파랑·노랑 원색, 원·사각·삼각, 굵은 기하 산세리프, 비대칭 구성), 소리는 스틸 드럼.
사실: 루빅 큐브의 경우의 수는 43,252,003,274,489,856,000가지. 2010년 Rokicki·Kociemba·Davidson·Dethridge가 모든 상태가 20수 이하로 풀린다고 증명(cube20.org; MAA).
계산에 약 35 CPU-년(구글이 남는 계산 시간을 제공)(Popular Science; Engadget).
"""
import math, numpy as np, cv2, cairo
from base import *
import sfx as S

CREAMB = (0.94, 0.91, 0.84); RED = (0.85, 0.16, 0.12); BLUE = (0.10, 0.25, 0.62); YEL = (0.98, 0.78, 0.10); INKB = (0.08, 0.08, 0.10); WHT = (0.98, 0.98, 0.96)
GRN = (0.10, 0.55, 0.32); ORA = (0.95, 0.45, 0.10)
T_NUM = 4.0; T_TWENTY = 9.4; T_CPU = 15.0; T_CODA = 20.4
_r = np.random.default_rng(20)
SCR = _r.integers(0, 6, (3, 3, 3))
COLS = [WHT, YEL, RED, ORA, BLUE, GRN]

def iso_cube(cr, cx, cy, s, solved, a=1.0):
    """등각 큐브 세 면(cx, cy = 위쪽 뒤 꼭짓점). solved(0..1)만큼 칸이 맞춘 색으로 바뀐다."""
    ex = (0.866 * s, 0.5 * s); ey = (-0.866 * s, 0.5 * s); ez = (0, s)
    def P(o, u, v, du, dv): return (o[0] + u[0] * du + v[0] * dv, o[1] + u[1] * du + v[1] * dv)
    O = (cx, cy)
    faces = [(O, ex, ey, YEL), ((cx + 3 * ey[0], cy + 3 * ey[1]), ex, ez, BLUE), ((cx + 3 * ex[0], cy + 3 * ex[1]), ey, ez, RED)]
    for fi, (o, u, v, tgt) in enumerate(faces):
        for i in range(3):
            for j in range(3):
                done = ((i * 3 + j + fi) / 11) < solved
                col = tgt if done else COLS[SCR[fi, i, j]]
                pts = [P(o, u, v, i, j), P(o, u, v, i + 1, j), P(o, u, v, i + 1, j + 1), P(o, u, v, i, j + 1)]
                cr.move_to(*pts[0]); [cr.line_to(*q) for q in pts[1:]]; cr.close_path()
                cr.set_source_rgba(*col, a); cr.fill_preserve(); cr.set_source_rgba(*INKB, a); cr.set_line_width(6); cr.stroke()

def bauhaus_bg(cr, t):
    cr.set_source_rgb(*CREAMB); cr.paint()
    cr.set_source_rgb(*BLUE); cr.arc(170, 1700, 260, 0, 6.283); cr.fill()
    cr.set_source_rgb(*YEL); cr.move_to(1080, 1350); cr.line_to(1080, 1920); cr.line_to(640, 1920); cr.close_path(); cr.fill()
    cr.set_source_rgb(*RED); cr.rectangle(900, 520, 180, 40); cr.fill()
    cr.set_source_rgb(*INKB); cr.rectangle(60, 520, 10, 1100); cr.fill()

def draw(t):
    s, cr = surf(); bauhaus_bg(cr, t)
    if t < T_NUM:
        a = 1 - ramp(t, T_NUM - 0.3, T_NUM)
        iso_cube(cr, 540, 760, 125, 0.0, a)
    elif t < T_TWENTY:                                                  # 큰 수
        a = ramp(t, T_NUM, T_NUM + 0.3) * (1 - ramp(t, T_TWENTY - 0.3, T_TWENTY))
        digits = '43,252,003,274,489,856,000'
        n = int(len(digits) * smooth(ramp(t, T_NUM + 0.4, T_NUM + 2.6)))
        rows = [digits[:10], digits[10:18], digits[18:]]
        shown = digits[:n]; idx = 0
        for r_, row in enumerate(rows):
            part = shown[idx: idx + len(row)]; idx += len(row)
            txt(cr, part, 120, 820 + r_ * 150, 128, INKB, a, fam=BLK, anchor='l')
        cr.set_source_rgba(*RED, a); cr.arc(860, 1290, 70, 0, 6.283); cr.fill()
        txt(cr, '43 quintillion · 4300경', 120, 1310, 52, BLUE, a * ramp(t, T_NUM + 2.6, T_NUM + 3.0), fam=BLK, anchor='l')
    elif t < T_CPU:                                                     # 20수 이하
        a = ramp(t, T_TWENTY, T_TWENTY + 0.3) * (1 - ramp(t, T_CPU - 0.3, T_CPU))
        p = ramp(t, T_TWENTY + 0.4, T_TWENTY + 4.0)
        iso_cube(cr, 540, 600, 95, p, a)
        for k in range(20):
            on = k / 20 < p; x = 120 + (k % 10) * 86; y = 1220 + (k // 10) * 100
            shape = k % 3; col = [RED, BLUE, YEL][k % 3] if on else (0.80, 0.78, 0.72)
            cr.set_source_rgba(*col, a)
            if shape == 0: cr.arc(x + 32, y + 32, 32, 0, 6.283)
            elif shape == 1: cr.rectangle(x, y, 64, 64)
            else: cr.move_to(x + 32, y); cr.line_to(x + 64, y + 64); cr.line_to(x, y + 64); cr.close_path()
            cr.fill()
        txt(cr, f'{min(20, int(p * 20 + 0.999))} / 20', 540, 1480, 80, INKB, a, fam=BLK)
    else:                                                               # 35 CPU-년
        a = ramp(t, T_CPU, T_CPU + 0.3) * (1 - ramp(t, T_CODA - 0.3, T_CODA))
        g = smooth(ramp(t, T_CPU + 0.4, T_CPU + 3.0))
        for k in range(35):
            if k / 35 > g: break
            x = 140 + (k % 7) * 118; y = 600 + (k // 7) * 118
            cr.set_source_rgba(*[RED, BLUE, YEL, INKB][k % 4], a); cr.rectangle(x, y, 96, 96); cr.fill()
        txt(cr, '35 CPU-years', 540, 1360, 96, INKB, a * ramp(t, T_CPU + 2.6, T_CPU + 3.0), fam=BLK)
        txt(cr, 'proved in 2010 · 2010년 증명', 540, 1440, 44, BLUE, a * ramp(t, T_CPU + 3.0, T_CPU + 3.4), fam=BLK)
    return np.ascontiguousarray(arr(s)[..., :3])

def sound(path):
    m = S.Mix(EP['DUR'], 43); tc = EP['t_coda']; b = 60 / 108
    sc = [261.6, 293.7, 329.6, 392.0, 440.0, 523.3, 587.3, 659.3]
    mel = [0, 2, 4, 5, 4, 2, 3, 1, 0, 4, 6, 5, 7, 5, 3, 4]
    t = 0.3; k = 0
    while t < tc - 0.3:
        m.put('mus', t, S.steeldrum(sc[mel[k % 16]], 1.2, 0.28))
        if k % 2 == 0: m.put('mus', t, S.steeldrum(sc[0] / 2 if (k // 8) % 2 == 0 else sc[3] / 2, 1.4, 0.2))
        t += b / 2; k += 1
    for k in range(20): m.put('fx', T_TWENTY + 0.4 + k * 3.6 / 20, S.tok(700 + 15 * k, 0.12))
    m.put('fx', T_TWENTY + 4.0, S.bell(1046.5, 2.4, 0.24))
    for i, f in enumerate([523.3, 392.0, 261.6]): m.put('mus', tc + 0.8 + i * STEP, S.steeldrum(f, 2.4, 0.32))
    m.write(path, rev_mus=2.0, wet_mus=0.32)

EP = finalize(dict(t_coda=T_CODA, draw=draw, sound=sound, end_icon='star', grain=0.0,
    title_en_card='NEVER MORE THAN 20 MOVES', title_ko_card='아무리 섞여도 20수',
    pal=dict(hi=RED, endbg=CREAMB),
    card_style=dict(box='paper', bg=(0.99, 0.98, 0.95), ink=INKB, hi=RED, y=180, fe=BLK, fk=BLK),
    cards=[(0.3, 3.8, ['A scrambled', 'Rubik’s Cube.'], ['마구 섞인', '루빅 큐브']),
           (4.0, 9.2, ['It can be mixed into', '*43 quintillion* different states.'], ['섞일 수 있는 상태는', '*4300경* 가지가 넘는다']),
           (9.4, 14.8, ['Yet every single one', 'can be solved in *20 moves* or fewer.'], ['그런데 어떤 상태든', '*20수* 안에 풀린다']),
           (15.0, 20.2, ['Proving it took', 'about *35 years* of computer time.'], ['증명하는 데 컴퓨터 시간으로', '약 *35년*이 걸렸다'])],
    coda=[('Even the worst tangle', '가장 엉킨 상태도'), ('is never more than twenty turns from order.', '질서에서 스무 수 이상 떨어져 있지 않다'), ('Untangle it one turn at a time.', '한 번에 한 수씩 풀어 가자')],
    coda_style=dict(dim=0.5, blur=8, tint=(0.88, 0.85, 0.78), ink=INKB, hi=RED, fe=BLK),
    sources=['Rubik’s Cube has 43,252,003,274,489,856,000 positions; in July 2010 Rokicki, Kociemba, Davidson and Dethridge proved every position is solvable in 20 moves or fewer (cube20.org; MAA).', 'About 35 CPU-years of computing time, donated by Google (Popular Science; Engadget).'],
    yt=dict(title_en='Every Rubik’s Cube Can Be Solved in 20 Moves #Shorts', title_ko='어떤 루빅 큐브든 20수면 풀린다')))

if __name__ == '__main__': main(EP)
