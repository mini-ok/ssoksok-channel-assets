"""눈 없는 수묵 용 (종이 mm 좌표). 머리는 위쪽 가운데 왼편, 왼쪽을 본다. 눈자리 E는 비워 둔다.
모든 획은 이 함수에서만 나온다(모델 유지). 몸통 획은 척추 곡선의 매개변수로 정의해, C11에서 몸 선을 따라 밀 수 있다.
"""
import math
import numpy as np
from brush import Stroke, Wash, catmull

E = (300.0, 112.0)          # 눈자리 중심
E_R = 7.0

SPINE = catmull([(338, 128), (395, 146), (448, 186), (478, 246), (462, 306), (498, 356), (566, 366), (612, 326), (624, 282)], 80)
_seg = np.linalg.norm(np.diff(SPINE, axis=0), axis=1)
_S = np.concatenate([[0], np.cumsum(_seg)]); SPINE_L = float(_S[-1])


def spine_at(s):
    s = np.clip(s, 0, SPINE_L)
    x = np.interp(s, _S, SPINE[:, 0]); y = np.interp(s, _S, SPINE[:, 1])
    dx = np.interp(np.minimum(s + 1, SPINE_L), _S, SPINE[:, 0]) - np.interp(np.maximum(s - 1, 0), _S, SPINE[:, 0])
    dy = np.interp(np.minimum(s + 1, SPINE_L), _S, SPINE[:, 1]) - np.interp(np.maximum(s - 1, 0), _S, SPINE[:, 1])
    n = np.hypot(dx, dy) + 1e-9
    return x, y, dx / n, dy / n


def body_halfwidth(s):
    u = np.clip(s / SPINE_L, 0, 1)
    return 15.0 * (1 - 0.15 * u) * np.clip((1 - u) / 0.35, 0.12, 1) ** 0.8 * np.clip(0.75 + u * 4, 0, 1)


def along_body(s0, s1, off, n=8):
    """척추 s0..s1 구간, 법선 방향 off(반폭 배수; +는 바깥/등 쪽)의 점들."""
    ss = np.linspace(s0, s1, n)
    x, y, tx, ty = spine_at(ss)
    hw = body_halfwidth(ss)
    return list(zip(x + (-ty) * off * hw, y + tx * off * hw))


def strokes(s_shift=0.0):
    """s_shift: C11에서 몸 전체를 척추를 따라 앞으로 미는 양(mm). 0이면 그림 그대로."""
    S = []
    k = [100]

    def add(pts, w, **kw):
        k[0] += 1
        S.append(Stroke(pts, w, seed=k[0], **kw))

    def wash(blobs, load, **kw):
        k[0] += 1
        S.append(Wash(blobs, load=load, seed=k[0], **kw))

    r = np.random.default_rng(7)
    # ---- 몸통: 몰골법. 큰 마른 붓을 눕혀 한 번에 쓸어 비백이 곧 비늘 결이 되게
    add(along_body(0, SPINE_L * 0.55, -0.05, 10), 32, load=0.95, dry=0.74, head='press', tail='fly', wet=0.35, name='body1')
    add(along_body(SPINE_L * 0.42, SPINE_L, 0.0, 10), 27, load=0.92, dry=0.78, head='press', tail='taper', wet=0.3, name='body2')
    # 등 쪽 진한 덧획(마른)
    add(along_body(4, SPINE_L * 0.5, -0.75, 9), 8, load=1.4, dry=0.8, head='press', tail='fly', wet=0.1, name='back1')
    add(along_body(SPINE_L * 0.52, SPINE_L * 0.95, -0.7, 8), 7, load=1.35, dry=0.8, head='press', tail='fly', wet=0.1, name='back2')
    # 배 선(가늘고 젖게, 끊어서)
    add(along_body(8, SPINE_L * 0.32, 1.0, 7), 2.4, load=1.2, dry=0.35, head='point', tail='taper', wet=0.3, name='belly')
    add(along_body(SPINE_L * 0.36, SPINE_L * 0.7, 1.0, 7), 2.0, load=1.15, dry=0.4, head='point', tail='taper', wet=0.3, name='belly')
    # 비늘 강조: 목 쪽에만 크기가 다른 굵은 반원 몇 개
    for s0, row, scl in ((18, -0.2, 1.1), (30, 0.35, 0.9), (44, -0.35, 1.25), (58, 0.2, 1.0), (75, -0.15, 1.15),
                         (92, 0.4, 0.8), (150, -0.3, 1.0), (205, 0.25, 0.9), (262, -0.2, 0.85)):
        x, y, tx, ty = spine_at(s0)
        hw = float(body_halfwidth(s0)); nx, ny = -ty, tx
        cx, cy = x + nx * row * hw, y + ny * row * hw
        sc = hw * 0.42 * scl
        pts = [(cx + nx * sc * math.cos(a) * 0.8 + tx * sc * math.sin(a), cy + ny * sc * math.cos(a) * 0.8 + ty * sc * math.sin(a))
               for a in np.linspace(-1.7, 1.9, 6)]
        add(pts, max(1.4, sc * 0.38), load=1.35, dry=0.55, head='press', tail='taper', wet=0.15, name='scale')
    # 등지느러미: 갈고리 모양 굵은 가시, 간격 들쭉날쭉
    s = 8.0
    while s < SPINE_L * 0.78:
        x, y, tx, ty = spine_at(s)
        hw = float(body_halfwidth(s))
        bx, by = x + ty * hw * 0.95, y - tx * hw * 0.95
        h = hw * (0.55 + r.uniform(0, 0.35))
        add([(bx - tx * 4, by - ty * 4), (bx + ty * h * 0.7 + tx * 1, by - tx * h * 0.7 + ty * 1), (bx + ty * h + tx * 6, by - tx * h + ty * 6)],
            2.6, load=1.35, dry=0.55, head='press', tail='taper', wet=0.1, name='fin')
        s += r.uniform(12, 22)

    # ---- 머리(눈자리 E, 왼쪽을 봄): 머리 덩어리 담묵 → 윗선 한 획 → 코·입·턱 → 볼로 뒤를 닫음
    ex, ey = E
    wash([(224, 121, 11), (240, 123, 14), (258, 124, 16), (276, 125, 18), (294, 126, 19), (312, 126, 19), (330, 128, 16), (286, 140, 13), (262, 140, 11)], 0.24, soft=0.6, rim=0.25, name='head_wash')
    add([(344, 98), (304, 93), (264, 99), (234, 107), (212, 114)], 9.5, load=1.35, dry=0.62, head='press', tail='taper', wet=0.25, name='topline')
    add([(262, 101), (242, 106)], 12, load=1.2, dry=0.75, head='press', tail='fly', wet=0.15, name='bridge')
    add([(222, 111), (212, 108), (204, 114), (208, 122), (217, 121)], 4.2, load=1.5, dry=0.3, head='press', tail='taper', wet=0.2, name='nose')
    add([(206, 122), (213, 130), (226, 128)], 5.0, load=1.4, dry=0.35, head='press', tail='taper', wet=0.2, name='lipcurl')
    add([(214, 126), (238, 129), (264, 127), (282, 131)], 4.6, load=1.35, dry=0.45, head='press', tail='taper', wet=0.2, name='lip')
    add([(218, 142), (246, 151), (282, 150), (310, 142), (328, 132)], 9.0, load=1.3, dry=0.68, head='press', tail='fly', wet=0.2, name='jaw')
    for (fx, fy, dd, L) in ((228, 129, 1, 10), (254, 130, 1, 12), (240, 147, -1, 9), (268, 149, -1, 10)):
        add([(fx, fy), (fx - 2, fy + L * 0.6 * dd), (fx - 4.5, fy + L * dd)], 3.2, load=1.45, dry=0.25, head='press', tail='taper', wet=0.1, name='fang')
    add([(336, 102), (346, 116), (348, 132), (338, 148)], 7.0, load=1.3, dry=0.78, head='press', tail='fly', wet=0.15, name='cheek')
    add([(258, 152), (264, 170), (256, 188)], 5.5, load=1.2, dry=0.9, head='press', tail='fly', wet=0.1, name='beard')
    add([(292, 148), (306, 168), (304, 186)], 4.5, load=1.2, dry=0.9, head='press', tail='fly', wet=0.1, name='beard')
    # 눈(가운데 비움)
    add([(ex - 13, ey + 1), (ex - 5, ey - 7), (ex + 7, ey - 7), (ex + 14, ey - 1)], 3.6, load=1.55, dry=0.25, head='press', tail='taper', wet=0.2, name='eye_up')
    add([(ex - 12, ey + 3), (ex - 2, ey + 8), (ex + 9, ey + 6.5), (ex + 14, ey + 1)], 2.0, load=1.45, dry=0.3, head='point', tail='taper', wet=0.15, name='eye_low')
    add([(ex - 16, ey - 13), (ex - 2, ey - 20), (ex + 18, ey - 21), (ex + 34, ey - 32)], 9.0, load=1.35, dry=0.85, head='press', tail='fly', wet=0.1, name='brow')
    # 뿔(사슴뿔처럼 갈래)
    add([(326, 90), (346, 72), (370, 58), (398, 54)], 7.5, load=1.3, dry=0.72, head='press', tail='taper', wet=0.15, name='horn1')
    add([(354, 68), (362, 50), (358, 38)], 4.0, load=1.3, dry=0.6, head='press', tail='taper', wet=0.1, name='horn1b')
    add([(340, 102), (368, 94), (396, 88), (420, 94)], 5.5, load=1.25, dry=0.78, head='press', tail='taper', wet=0.12, name='horn2')
    # 갈기: 뒤로 날리는 불꽃 획 5개
    for i in range(5):
        y0 = 104 + i * 11
        add([(336, y0), (356, y0 - 6 + i), (380, y0 - 2 + i * 2), (402 + i * 3, y0 + 8 + i * 3)],
            8.0 - i * 0.8, load=1.25, dry=0.88, head='press', tail='fly', wet=0.1, name='mane')
    # 수염
    add([(208, 112), (188, 96), (164, 90), (142, 100), (124, 90), (114, 72)], 2.4, load=1.35, dry=0.3, head='press', tail='taper', wet=0.15, name='whisker1')
    add([(214, 136), (194, 154), (170, 160), (150, 150), (134, 160), (126, 178)], 2.2, load=1.3, dry=0.3, head='press', tail='taper', wet=0.15, name='whisker2')

    # ---- 앞발: 목 아래 배 쪽에서 나와 왼쪽 아래로, 손목에 마디, 발톱 넷이 갈고리
    add([(380, 160), (356, 184), (328, 201), (302, 212), (290, 216)], 11, load=1.2, dry=0.5, head='press', tail='fly', wet=0.25, name='arm')
    wash([(374, 168, 10), (360, 180, 10), (346, 190, 9), (332, 198, 8)], 0.2, soft=0.55, rim=0.2, name='arm_wash')
    add([(304, 211), (292, 215), (286, 219)], 8.5, load=1.35, dry=0.5, head='press', tail='taper', wet=0.2, name='wrist')
    for pts in (((288, 214), (276, 213), (266, 219), (263, 228)),
                ((289, 217), (281, 225), (275, 235), (278, 243)),
                ((292, 218), (291, 230), (289, 241), (294, 248)),
                ((296, 217), (303, 227), (307, 237), (313, 241))):
        add(list(pts), 4.6, load=1.5, dry=0.35, head='press', tail='taper', wet=0.15, name='claw')
    # ---- 꼬리 털
    for i in range(5):
        a = -1.45 + i * 0.3
        add([(622, 286), (622 + math.cos(a) * 14, 284 + math.sin(a) * 14), (628 + math.cos(a) * 30, 280 + math.sin(a) * 28)],
            3.0, load=1.25, dry=0.9, head='press', tail='fly', wet=0.1, name='tail')
    # ---- 구름: 발묵(몸 일부를 가림) + 소용돌이 선
    wash([(440, 236, 16), (470, 226, 22), (504, 236, 20), (530, 252, 14), (462, 256, 15), (496, 262, 13)], 0.20, soft=0.5, rim=0.35, name='cloud')
    wash([(560, 352, 14), (590, 344, 20), (618, 356, 16), (600, 372, 12)], 0.18, soft=0.5, rim=0.35, name='cloud')
    wash([(150, 44, 14), (180, 36, 18), (212, 42, 15), (236, 52, 10)], 0.13, soft=0.55, rim=0.3, name='cloud')
    add([(446, 240), (470, 222), (500, 228), (494, 246), (478, 240)], 3.0, load=0.7, dry=0.5, head='point', tail='taper', wet=0.4, name='cloud_line')
    add([(572, 352), (596, 340), (620, 350), (612, 364), (600, 358)], 3.0, load=0.7, dry=0.5, head='point', tail='taper', wet=0.4, name='cloud_line')
    return S


def eye_blank(X, Y):
    """눈자리 안쪽은 비워 둔 종이(먹을 거의 지움). 1 = 남김, 0 = 지움."""
    ang = np.arctan2(Y - E[1], X - E[0])
    wob = 1 + 0.07 * np.sin(ang * 3 + 0.7) + 0.05 * np.sin(ang * 5 + 2.1) + 0.03 * np.sin(ang * 9 + 0.3)
    d = (((X - E[0]) / 10.5) ** 2 + ((Y - E[1] - 0.5) / 5.4) ** 2) / wob ** 2
    return np.clip((d - 0.8) / 0.35, 0, 1).astype(np.float32) * 0.9 + 0.1
