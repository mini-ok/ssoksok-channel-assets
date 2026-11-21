"""〈벌집은 왜 육각형일까〉 — 종이 오림 키네틱 모션그래픽(세로 숏폼 1080×1920, 약 52초).
원으로 채우면 빈틈 → 빈틈 없는 정다각형은 셋 → 넓이가 같을 때 둘레가 가장 짧은 것은 육각형 → 2천 년 묵은 추측, 1999년 증명 → 벌집.
frame(t)은 t의 순수 함수.
"""
import os, sys, math
import numpy as np, cv2, cairo

HERE = os.path.dirname(os.path.abspath(__file__))
os.environ.setdefault('HD_ORIENT', 'v')
sys.path.insert(0, os.path.join(HERE, '..', 'haedal'))
sys.path.insert(0, os.path.join(HERE, '..', 'jamo28'))
os.environ.setdefault('MG_SCALE', os.environ.get('HD_SCALE', '1'))
from mg import clamp, ramp, smooth, expo_out, expo_in_out, back_out, spring, lerp   # noqa: E402
from paper import W, H, SC, Level, composite, grain, hexc, tex                     # noqa: E402
import shapes as S                                                                   # noqa: E402

FPS = 30
SERIF = 'Noto Serif CJK KR'
DW, DH = 1080, 1920
CX, CY = 540, 980
CREAM = hexc('#EFE6D2'); INK = hexc('#2A1A10'); RED = hexc('#E0442E')
HONEY = hexc('#E9A23B'); HONEY2 = hexc('#F5C451'); WAX = hexc('#F3DC94'); WAX2 = hexc('#D9B25E'); BROWN = hexc('#5A3418')
TRI, SQU, HEXC = hexc('#8FB8C9'), hexc('#E7A37E'), HONEY

# 같은 넓이(1)일 때 둘레 — 계산값
PER = {'tri': 3 * math.sqrt(4 / math.sqrt(3)), 'sq': 4.0, 'hex': 6 * math.sqrt(2 / (3 * math.sqrt(3)))}   # 4.559, 4.000, 3.722
GAP = 1 - math.pi / (2 * math.sqrt(3))                                                                   # 원을 가장 빽빽이: 9.3% 빈틈

# 시간표
T_B, T_C, T_D, T_E, T_F, T_END = 4.5, 12.5, 21.5, 32.0, 39.0, 49.5
DUR = 52.5


# ---------------------------------------------------------------- 도형
def hexpath(cr, x, y, r, rot=0.0):
    cr.new_sub_path()
    for k in range(6):
        a = rot + math.pi / 6 + k * math.pi / 3
        (cr.move_to if k == 0 else cr.line_to)(x + r * math.cos(a), y + r * math.sin(a))
    cr.close_path()

def tripath(cr, x, y, s, up=True):
    h = s * math.sqrt(3) / 2
    if up: S.poly(cr, [(x, y - h * 2 / 3), (x + s / 2, y + h / 3), (x - s / 2, y + h / 3)])
    else: S.poly(cr, [(x, y + h * 2 / 3), (x + s / 2, y - h / 3), (x - s / 2, y - h / 3)])

def bee(cr, x, y, s, t, rot=0.0):
    cr.save(); cr.translate(x, y); cr.rotate(rot)
    fl = math.sin(t * 60)
    for sgn in (-1, 1):
        S.ellipse(cr, -0.1 * s, sgn * (0.35 + 0.1 * fl) * s * -1, 0.42 * s, 0.2 * s, sgn * (-0.5 - 0.35 * fl))
    S.fill(cr, (0.97, 0.97, 1.0), 0.75)
    S.ellipse(cr, 0, 0, 0.62 * s, 0.38 * s); S.fill(cr, HONEY2)
    for k in range(3):
        cr.save(); S.ellipse(cr, 0, 0, 0.62 * s, 0.38 * s); cr.clip()
        cr.rectangle((-0.3 + 0.24 * k) * s, -s, 0.11 * s, 2 * s); S.fill(cr, INK); cr.restore()
    S.circle(cr, 0.68 * s, 0, 0.24 * s); S.fill(cr, INK)
    S.poly(cr, [(-0.62 * s, -0.06 * s), (-0.85 * s, 0), (-0.62 * s, 0.06 * s)]); S.fill(cr, INK)
    cr.restore()

def cell(cr_rim, cr_in, x, y, r, fill_honey=0.0, t=0.0, shade=1.0):
    """육각 방 하나: 밀랍 테(위층) + 안쪽 벽 그늘 + 바닥(꿀). 위층과 아래층으로 나눠 그림자가 깊이를 만든다."""
    # 바닥(안쪽 층)
    hexpath(cr_in, x, y, r * 0.88)
    g = cairo.LinearGradient(x - r, y - r, x + r, y + r)
    if fill_honey > 0:
        c1 = tuple(lerp(a, b, fill_honey) for a, b in zip(WAX2, HONEY)); c2 = tuple(lerp(a, b, fill_honey) for a, b in zip(BROWN, (0.62, 0.33, 0.08)))
    else:
        c1, c2 = WAX2, BROWN
    g.add_color_stop_rgb(0, *[v * shade for v in c2]); g.add_color_stop_rgb(1, *[v * shade for v in c1])
    cr_in.set_source(g); cr_in.fill()
    if fill_honey > 0.3:   # 꿀 윤기
        S.ellipse(cr_in, x - r * 0.25, y - r * 0.3, r * 0.28, r * 0.12, -0.6); S.fill(cr_in, (1, 0.95, 0.75), 0.35 * (fill_honey - 0.3))
    # 테(위층): 바깥 육각 − 안쪽 육각
    hexpath(cr_rim, x, y, r); hexpath(cr_rim, x, y, r * 0.84)
    S.fill(cr_rim, tuple(v * shade for v in WAX), holes=True)


# ---------------------------------------------------------------- 글자
def slide_text(cr, s, x, y, size, rgb, u_in, u_out, weight=cairo.FONT_WEIGHT_NORMAL, anchor='c'):
    if u_in <= 0 or u_out >= 1: return
    cr.save(); cr.select_font_face(SERIF, cairo.FONT_SLANT_NORMAL, weight); cr.set_font_size(size)
    ext = cr.text_extents(s); dx = {'l': 0, 'c': -ext.x_advance / 2, 'r': -ext.x_advance}[anchor]
    cr.rectangle(x + dx - 30, y - size * 1.05, ext.x_advance + 60, size * 1.35); cr.clip()
    off = (1 - expo_out(u_in)) * size * 1.15 - expo_in_out(u_out) * size * 1.15
    cr.move_to(x + dx, y + off); cr.text_path(s); cr.set_source_rgb(*rgb); cr.fill(); cr.restore()

def text_at(cr, s, x, y, size, rgb, a=1.0, weight=cairo.FONT_WEIGHT_NORMAL, anchor='c'):
    if a <= 0: return
    cr.save(); cr.select_font_face(SERIF, cairo.FONT_SLANT_NORMAL, weight); cr.set_font_size(size)
    ext = cr.text_extents(s); dx = {'l': 0, 'c': -ext.x_advance / 2, 'r': -ext.x_advance}[anchor]
    cr.move_to(x + dx, y); cr.text_path(s); cr.set_source_rgba(*rgb, a); cr.fill(); cr.restore()

def title(cr, l1, l2, t0, t1, c2=INK, y1=250, y2=360, s1=84, s2=84):
    slide_text(cr, l1, 540, y1, s1, INK, ramp(t_glob, t0, t0 + 0.5), ramp(t_glob, t1 - 0.3, t1), cairo.FONT_WEIGHT_BOLD)
    if l2: slide_text(cr, l2, 540, y2, s2, c2, ramp(t_glob, t0 + 0.2, t0 + 0.7), ramp(t_glob, t1 - 0.25, t1 + 0.05), cairo.FONT_WEIGHT_BOLD)

t_glob = 0.0

def en(cr, s, y, t0, t1, size=34):
    """제목 아래 영어 한 줄."""
    slide_text(cr, s, 540, y, size, INK, ramp(t_glob, t0 + 0.3, t0 + 0.8), ramp(t_glob, t1 - 0.3, t1))


# ---------------------------------------------------------------- 장면
R0 = 62                                                   # 원·육각 반지름(중간 장면)
def hex_centers(r, nx, ny, cx=CX, cy=CY):
    """뾰족한 쪽이 위(pointy-top) 육각 격자 중심."""
    w = math.sqrt(3) * r; out = []
    for j in range(-ny, ny + 1):
        for i in range(-nx, nx + 1):
            out.append((cx + w * (i + 0.5 * (j % 2)), cy + 1.5 * r * j, i, j))
    return out

def draw(t, L):
    global t_glob; t_glob = t
    ty, back, rim, inn, near, gl = L['type'].cr, L['back'].cr, L['rim'].cr, L['in'].cr, L['near'].cr, L['glow'].cr

    # ── A 질문 + 벌
    if t < T_B + 0.4:
        title(ty, '벌집은 왜', '육각형일까?', 0.3, T_B, HONEY, 300, 420, 100, 100)
        en(ty, 'Why are honeycombs hexagons?', 492, 0.45, T_B)
        u = spring(ramp(t, 1.2, 2.0), 0.4, 1.5)
        if u > 0:
            rim.save(); rim.translate(CX, CY); rim.scale(u, u); rim.rotate(0.3 * (1 - u)); rim.translate(-CX, -CY)
            inn.save(); inn.translate(CX, CY); inn.scale(u, u); inn.rotate(0.3 * (1 - u)); inn.translate(-CX, -CY)
            cell(rim, inn, CX, CY, 170, smooth(ramp(t, 2.6, 3.8)), t); rim.restore(); inn.restore()
        bx = lerp(-150, CX + 260 * math.sin(t * 1.4), smooth(ramp(t, 0.2, 1.4))); by = CY - 300 + 120 * math.sin(t * 2.8)
        bx = bx + 900 * expo_in_out(ramp(t, T_B - 0.6, T_B + 0.3))
        bee(near, bx, by, 70, t, 0.25 * math.cos(t * 1.4))

    # ── B 원으로 채우면 빈틈
    if T_B - 0.2 < t < T_C + 0.4:
        uo = ramp(t, T_C - 0.4, T_C + 0.2)
        title(ty, '동그라미로 지으면?', None, T_B, T_C, s1=78)
        en(ty, 'What if bees built circles?', 308, T_B + 0.1, T_C)
        cs = [c for c in hex_centers(R0, 4, 6) if abs(c[0] - CX) < 470 and abs(c[1] - CY + 40) < 400]
        RC = R0 * math.sqrt(3) / 2 * 0.995                    # 이웃과 꼭 맞닿는 원
        for k, (x, y, i, j) in enumerate(sorted(cs, key=lambda c: (c[1], c[0]))):
            t0 = T_B + 0.4 + 0.022 * k
            u = clamp(ramp(t, t0, t0 + 0.55), 0, 1)
            if u <= 0: continue
            yy = y - 700 * (1 - expo_out(u)) ** 2 + 18 * math.sin(min(1, u) * math.pi * 2) * (1 - u)   # 떨어져 톡 튐
            sc = 1 - uo
            S.circle(rim, CX + (x - CX) * (1 + 0.2 * uo), CY + (yy - CY) * (1 + 0.2 * uo), RC * sc)
        S.fill(rim, WAX)
        # 빈틈을 붉게: 원 사이 세모 틈
        ga = smooth(ramp(t, 8.2, 8.9)) * (1 - uo)
        if ga > 0:
            pos = {(i, j): (x, y) for (x, y, i, j) in cs}
            inn.save()
            for (i, j), (x, y) in pos.items():
                o = j % 2
                for tri_ in [((i, j), (i + 1, j), (i + o, j + 1)), ((i + 1, j), (i + o, j + 1), (i + o + 1, j + 1))]:
                    if all(q in pos for q in tri_): S.poly(inn, [pos[q] for q in tri_])
            inn.set_fill_rule(cairo.FILL_RULE_WINDING); inn.clip()
            inn.rectangle(0, 0, DW, DH)
            for (x, y, i, j) in cs: S.circle(inn, x, y, RC)
            S.fill(inn, RED, ga * (0.75 + 0.25 * math.sin(t * 6)), holes=True); inn.restore()
            text_at(ty, f'빈틈 {GAP * 100 * smooth(ramp(t, 8.4, 9.6)):.1f}%', 540, 1700, 110, RED, ga, cairo.FONT_WEIGHT_BOLD)
            text_at(ty, '가장 빽빽이 놓아도', 540, 1560, 44, INK, ga)
            text_at(ty, 'Even packed as tightly as possible: 9.3% empty', 540, 1765, 32, RED, ga)

    # ── C 빈틈 없이 채우는 정다각형은 셋뿐
    rows = [('tri', '정삼각형 · triangle', TRI), ('sq', '정사각형 · square', SQU), ('hex', '정육각형 · hexagon', HEXC)]
    ys = [700, 1060, 1420]
    if T_C - 0.2 < t < T_E + 0.2:
        title(ty, '빈틈없이 덮는 정다각형은', '딱 셋', T_C, T_D - 0.2 if False else T_E - 0.2, RED, 230, 340, 64, 92)
        en(ty, 'Only three regular polygons tile a plane with no gaps', 400, T_C + 0.1, T_E - 0.2, 30)
        for ri, (key, name, col) in enumerate(rows):
            y0 = ys[ri]
            t0 = T_C + 0.6 + ri * 0.9
            fold = expo_in_out(ramp(t, T_D, T_D + 0.8))          # D로 넘어가면 타일이 하나로 모임
            n_show = 0
            s = 74
            tiles = []
            if key == 'sq':
                for i in range(-7, 8):
                    for j in range(-1, 2): tiles.append((540 + i * s, y0 + j * s, i, j))
            elif key == 'tri':
                for i in range(-14, 15):
                    for j in range(-1, 2): tiles.append((540 + i * s * 0.5, y0 + j * s * 0.866, i, j))   # 가운데(무게중심 아님) 기준
            else:
                for (x, y, i, j) in hex_centers(s * 0.58, 7, 1, 540, y0): tiles.append((x, y, i, j))
            clip_h = 125
            back.save(); back.rectangle(0, y0 - clip_h, DW, clip_h * 2); back.clip()
            for k, (x, y, i, j) in enumerate(sorted(tiles, key=lambda q: abs(q[0] - 540) + abs(q[1] - y0) * 0.5)):
                tk = t0 + 0.012 * k
                u = ramp(t, tk, tk + 0.35)
                if u <= 0: continue
                flip = abs(math.cos((1 - expo_out(u)) * math.pi / 2))           # 카드 뒤집듯 펼쳐짐
                keep = (k == 0)
                a = (1.0 if t < T_D else 0.0) if keep else (1 - fold)
                if a <= 0: continue
                back.save(); back.translate(x, y); back.scale(max(flip, 0.02), 1)
                if key == 'sq': back.rectangle(-s / 2 + 2, -s / 2 + 2, s - 4, s - 4)
                elif key == 'tri':
                    hh = (s - 5) * 0.866; ss = s - 5
                    if (i + j) % 2 == 0: S.poly(back, [(0, -hh / 2), (ss / 2, hh / 2), (-ss / 2, hh / 2)])
                    else: S.poly(back, [(0, hh / 2), (ss / 2, -hh / 2), (-ss / 2, -hh / 2)])
                else: hexpath(back, 0, 0, s * 0.58 - 2.5)
                back.restore()
                S.fill(back, col if keep else tuple(lerp(c, 1, 0.25) for c in col), a)
            back.restore()
            slide_text(ty, name, 120, y0 - 135, 40, INK, ramp(t, t0, t0 + 0.4), ramp(t, T_D - 0.1, T_D + 0.3), cairo.FONT_WEIGHT_BOLD, 'l')

    # ── D 넓이가 같으면 둘레는?  실(둘레)이 풀려 막대가 된다
    if T_D - 0.2 < t < T_E + 0.4:
        uo = ramp(t, T_E - 0.4, T_E + 0.2)
        slide_text(ty, '넓이가 같다면', 540, 1590, 48, INK, ramp(t, T_D + 0.6, T_D + 1.0), uo)
        slide_text(ty, '벽(둘레)이 가장 짧은 건?', 540, 1670, 56, INK, ramp(t, T_D + 0.8, T_D + 1.2), uo, cairo.FONT_WEIGHT_BOLD)
        slide_text(ty, 'Same area — which shape has the shortest wall?', 540, 1724, 32, INK, ramp(t, T_D + 0.9, T_D + 1.3), uo)
        A = 74 * 74                                            # 같은 넓이(정사각형 한 칸)
        U = 74 * 1.0                                           # 둘레 1단위 → 길이(px/ (√넓이))
        for ri, (key, name, col) in enumerate(rows):
            y0 = ys[ri]; xs0 = 200
            ux = expo_in_out(ramp(t, T_D + 0.5, T_D + 1.2))
            cx_ = lerp(540, xs0, ux)
            per = PER[key] * U                                  # 같은 넓이에서의 둘레(px)
            # 도형(같은 넓이)
            back.save(); back.translate(cx_, y0)
            if key == 'sq': back.rectangle(-37, -37, 74, 74)
            elif key == 'tri':
                s = math.sqrt(4 * A / math.sqrt(3)); tripath(back, 0, 0, s, True)
            else:
                r = math.sqrt(2 * A / (3 * math.sqrt(3))); hexpath(back, 0, 0, r)
            back.restore(); S.fill(back, col, 1 - uo)
            # 실이 둘레를 감았다가 오른쪽으로 곧게 풀림
            tr = ramp(t, T_D + 1.3 + 0.35 * ri, T_D + 2.3 + 0.35 * ri)   # 감기
            un = expo_in_out(ramp(t, T_D + 3.2 + 0.2 * ri, T_D + 4.6 + 0.2 * ri))   # 풀기
            if tr > 0:
                L0 = per * tr
                # 풀린 부분은 오른쪽 막대, 남은 부분은 도형 둘레
                straight = L0 * un
                bx0 = cx_ + 80
                rim.set_line_width(7); rim.set_line_cap(cairo.LINE_CAP_ROUND)
                if straight > 1:
                    rim.move_to(bx0, y0); rim.line_to(bx0 + straight * 1.25, y0)
                    rim.set_source_rgba(*RED, 1 - uo); rim.stroke()
                rest = L0 * (1 - un)
                if rest > 1:
                    pts = outline(key, cx_, y0, A)
                    poly_partial(rim, pts, rest)
                    rim.set_source_rgba(*RED, 1 - uo); rim.stroke()
                if un > 0.95:
                    v = PER[key] * smooth(ramp(t, T_D + 4.4 + 0.2 * ri, T_D + 5.4 + 0.2 * ri))
                    win = key == 'hex'
                    text_at(ty, f'{v:.2f}', bx0 + straight * 1.25 + 24, y0 + 18, 56 if win else 46, RED if win else INK, 1 - uo, cairo.FONT_WEIGHT_BOLD, 'l')
            if key == 'hex':
                hw = smooth(ramp(t, T_D + 6.4, T_D + 7.0)) * (1 - uo)
                if hw > 0:
                    S.ring(gl, xs0, y0, 70, 78); S.fill(gl, (1.0, 0.75, 0.3), 0.6 * hw * (0.7 + 0.3 * math.sin(t * 5)))
                    text_at(ty, '가장 짧다!', 915, y0 - 20, 46, RED, hw, cairo.FONT_WEIGHT_BOLD)
                    text_at(ty, 'the shortest!', 915, y0 + 22, 30, RED, hw)

    # ── E 2천 년 묵은 추측 → 1999년 증명
    if T_E - 0.2 < t < T_F + 0.3:
        uo = ramp(t, T_F - 0.4, T_F + 0.1)
        slide_text(ty, '기원전 36년 무렵', 540, 420, 64, INK, ramp(t, T_E + 0.2, T_E + 0.6), uo, cairo.FONT_WEIGHT_BOLD)
        slide_text(ty, '로마의 바로가 적은 추측', 540, 500, 44, INK, ramp(t, T_E + 0.4, T_E + 0.8), uo)
        slide_text(ty, 'c. 36 BC — a guess written by Varro of Rome', 540, 552, 32, INK, ramp(t, T_E + 0.5, T_E + 0.9), uo)
        # 연도 바퀴: −36 → 1999
        yr = lerp(-36, 1999, expo_in_out(ramp(t, T_E + 1.2, T_E + 3.6)))
        a = smooth(ramp(t, T_E + 1.0, T_E + 1.3)) * (1 - uo)
        lab = f'{int(round(yr))}' if yr >= 1 else f'BC {int(round(-yr)) if yr < 0 else 1}'
        text_at(ty, lab, 540, 1020, 190, RED if yr > 1990 else INK, a, cairo.FONT_WEIGHT_BOLD)
        # 시간 줄(종이 띠)이 감김
        bw = 800 * expo_in_out(ramp(t, T_E + 1.2, T_E + 3.6))
        rim.rectangle(140, 1090, bw, 16); S.fill(rim, HONEY, 1 - uo)
        slide_text(ty, '토머스 헤일스가 증명', 540, 1300, 62, INK, ramp(t, T_E + 3.8, T_E + 4.2), uo, cairo.FONT_WEIGHT_BOLD)
        slide_text(ty, '약 2,000년 만에', 540, 1390, 48, RED, ramp(t, T_E + 4.2, T_E + 4.6), uo, cairo.FONT_WEIGHT_BOLD)
        slide_text(ty, 'Proven by Thomas Hales — about 2,000 years later', 540, 1442, 32, INK, ramp(t, T_E + 4.3, T_E + 4.7), uo)
        for k in range(3):
            bee(near, lerp(-120, 1200, ramp(t, T_E + 0.5 + k * 1.6, T_E + 3.2 + k * 1.6)), 1560 + 60 * math.sin(t * 2 + k), 40, t + k, 0.1)

    # ── F 벌집: 육각이 퍼지고, 깊이가 생기고, 꿀이 찬다
    if t > T_F - 0.2:
        zoom = lerp(1.6, 0.85, expo_in_out(ramp(t, T_F, T_END - 1.0)))
        pan = 60 * math.sin(t * 0.4)
        r = 58
        for layer, cr_r, cr_i, sh, pz in [('back', back, back, 0.62, 0.6), ('main', rim, inn, 1.0, 1.0)]:
            cs = hex_centers(r * (0.75 if layer == 'back' else 1.0), 12, 22, CX, CY)
            zz = zoom * (pz * 0.6 + 0.4) if layer == 'back' else zoom
            for (x, y, i, j) in cs:
                dist = math.hypot(x - CX, y - CY) / (r * 1.73)
                tk = T_F + 0.15 * dist
                u = back_out(ramp(t, tk, tk + 0.45), 1.6)
                if u <= 0: continue
                X = CX + (x - CX) * zz + pan * pz; Y = CY + (y - CY) * zz
                if X < -100 or X > DW + 100 or Y < -100 or Y > DH + 100: continue
                rr = r * (0.75 if layer == 'back' else 1.0) * zz * u
                hn = smooth(ramp(t, T_F + 3.0 + 0.08 * dist + 0.3 * ((i * 7 + j * 3) % 5) / 5, T_F + 4.2 + 0.08 * dist))
                if layer == 'back':
                    hexpath(cr_r, X, Y, rr); hexpath(cr_r, X, Y, rr * 0.84); S.fill(cr_r, tuple(lerp(c, 1, 0.35) for c in WAX2), holes=True)
                else:
                    cell(cr_r, cr_i, X, Y, rr, hn, t)
        for k in range(4):
            ph = t * 0.5 + k * 1.6
            bee(near, CX + 420 * math.sin(ph) * (1 if k % 2 else -1), 520 + 320 * k + 90 * math.sin(ph * 2), 88, t + k, 0.4 * math.cos(ph))
        slide_text(ty, '같은 넓이를', 540, 230, 68, INK, ramp(t, T_F + 2.2, T_F + 2.7), ramp(t, T_END - 0.4, T_END), cairo.FONT_WEIGHT_BOLD)
        slide_text(ty, '가장 짧은 벽으로', 540, 330, 80, RED, ramp(t, T_F + 2.5, T_F + 3.0), ramp(t, T_END - 0.4, T_END), cairo.FONT_WEIGHT_BOLD)
        slide_text(ty, 'Equal areas, with the shortest walls', 540, 392, 34, INK, ramp(t, T_F + 2.6, T_F + 3.1), ramp(t, T_END - 0.4, T_END))
        # 글자 받침(읽히게)
        a = smooth(ramp(t, T_F + 2.0, T_F + 2.5)) * (1 - ramp(t, T_END - 0.4, T_END))
        if a > 0:
            near.rectangle(0, 150, DW, 270); S.fill(near, CREAM, 0.9 * a)


def outline(key, cx, cy, A):
    if key == 'sq':
        s = math.sqrt(A); return [(cx - s / 2, cy - s / 2), (cx + s / 2, cy - s / 2), (cx + s / 2, cy + s / 2), (cx - s / 2, cy + s / 2), (cx - s / 2, cy - s / 2)]
    if key == 'tri':
        s = math.sqrt(4 * A / math.sqrt(3)); h = s * math.sqrt(3) / 2
        p = [(cx, cy - h * 2 / 3), (cx + s / 2, cy + h / 3), (cx - s / 2, cy + h / 3)]; return p + [p[0]]
    r = math.sqrt(2 * A / (3 * math.sqrt(3)))
    p = [(cx + r * math.cos(math.pi / 6 + k * math.pi / 3), cy + r * math.sin(math.pi / 6 + k * math.pi / 3)) for k in range(6)]
    return p + [p[0]]

def poly_partial(cr, pts, L):
    """꼭짓점 목록을 따라 길이 L만큼만(실이 감긴 만큼). 끝에서부터 남김 — 풀린 쪽은 시작점."""
    seg = list(zip(pts[:-1], pts[1:]))[::-1]
    cr.move_to(*seg[0][1]); left = L
    for a, b in seg:
        d = math.hypot(b[0] - a[0], b[1] - a[1])
        if left >= d: cr.line_to(*a); left -= d
        else:
            u = left / d; cr.line_to(b[0] + (a[0] - b[0]) * u, b[1] + (a[1] - b[1]) * u); break


# ---------------------------------------------------------------- 합성
LEVELS = [('back', 0.6, 0.20), ('in', 0.5, 0.25), ('rim', 1.4, 0.32), ('near', 2.4, 0.28), ('type', 0.6, 0.22)]

def frame(t, samples=3, shutter=0.5):
    names = [n for n, *_ in LEVELS] + ['glow']
    acc = {}
    for si in range(samples):
        tt = t + ((si + 0.5) / samples - 0.5) * shutter / FPS if samples > 1 else t
        L = {n: Level() for n in names}
        draw(tt, L)
        for n in names:
            a = L[n].array(); acc[n] = a if n not in acc else acc[n] + a
    for n in acc: acc[n] /= samples
    base = np.empty((H, W, 3), np.float32); base[:] = np.array(CREAM[::-1], np.float32)
    base *= tex()[..., None]
    for n, dep, sh in LEVELS:
        lay = acc[n]
        if n == 'back' and t > T_F: lay = cv2.GaussianBlur(lay, (0, 0), 2.2 * SC)          # 뒤 벌집은 초점 밖
        if n == 'near' and t > T_F: lay = cv2.GaussianBlur(lay, (0, 0), 1.2 * SC)
        base = composite(base, lay, dep, sh)
        if n == 'rim':
            g = acc['glow']
            if g[..., 3].max() > 1e-4:
                base = np.clip(base + g[..., :3] + cv2.GaussianBlur(g[..., :3], (0, 0), 8 * SC), 0, 1.3)
    return np.clip(base, 0, 1)


_VIG = None
def vignette_mask():
    global _VIG
    if _VIG is None:
        y, x = np.mgrid[0:H, 0:W].astype(np.float32)
        r = np.hypot((x - W / 2) / (W / 2), (y - H / 2) / (H / 2))
        _VIG = (1 - 0.2 * np.clip(r - 0.5, 0, 1) ** 1.4)[..., None].astype(np.float32)
    return _VIG


CREDIT = ['Created & Coded by L.S.M.', '허상공방 虛像工房 Project']
T_SEAL = T_END + 0.5
_credit = {}
def credit_layer():
    if _credit: return _credit['v']
    from PIL import Image, ImageDraw, ImageFont
    S2 = 2.0 * SC
    fnt = ImageFont.truetype('/usr/share/fonts/opentype/noto/NotoSerifCJK-Regular.ttc', int(19 * S2), index=1)
    sz = int(round(110 * SC)); cx, cy = 540, 820
    xs, ys = int(round(cx * SC)) - sz // 2, int(round(cy * SC))
    im = Image.new('L', (W, H), 0); d = ImageDraw.Draw(im)
    d.text((int(cx * SC), ys + sz + int(30 * S2)), CREDIT[0], font=fnt, fill=255, anchor='mm')
    d.text((int(cx * SC), ys + sz + int(60 * S2)), CREDIT[1], font=fnt, fill=255, anchor='mm')
    tm = cv2.GaussianBlur(np.asarray(im, np.float32) / 255, (0, 0), 0.35 * S2)
    seal = np.load(os.path.join(HERE, '..', '_shared', 'seal_baimun3.npy')).astype(np.float32)
    seal = cv2.resize(seal, (sz, sz), interpolation=cv2.INTER_AREA)[..., [2, 1, 0, 3]]
    _credit['v'] = (tm, seal, xs, ys, sz); return _credit['v']

def end_card(img, t):
    if t < T_END: return img
    u = smooth(ramp(t, T_END, T_END + 0.8))
    paper = np.array(CREAM[::-1], np.float32) * tex()[..., None]
    img = img * (1 - u) + paper * u
    if t < T_SEAL: return img
    tm, seal, xs, ys, sz = credit_layer()
    a1 = smooth(ramp(t, T_SEAL, T_SEAL + 0.2))
    red = np.clip((seal[..., 2:3] - seal[..., 1:2]) * 4, 0, 1)
    al = seal[..., 3:4] * a1 * red
    sub = img[ys:ys + sz, xs:xs + sz]; img[ys:ys + sz, xs:xs + sz] = sub * (1 - al + al * seal[..., :3])
    a2 = smooth(ramp(t, T_SEAL + 0.5, T_SEAL + 1.4)); k = (tm * a2 * 0.92)[..., None]
    return img * (1 - k) + np.array(INK[::-1], np.float32) * k


def final(t, samples=3):
    img = frame(t, samples) * vignette_mask()
    img = end_card(img, t)
    return grain(img, int(round(t * FPS)), 0.008)


if __name__ == '__main__':
    out = sys.argv[1]; os.makedirs(out, exist_ok=True)
    for ts in sys.argv[2:]:
        t = float(ts); img = final(t)
        cv2.imwrite(os.path.join(out, f't{t:05.2f}.png'), np.clip(img * 255, 0, 255).astype(np.uint8))
        print('wrote', t, flush=True)
