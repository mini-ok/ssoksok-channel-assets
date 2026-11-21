"""〈해의 달력〉 — 24절기를 해가 15°씩 나아가는 걸음으로 보여 주는 종이 오림 키네틱 모션그래픽(약 60초).
frame(t) → BGR(0..1). 모든 프레임은 t의 순수 함수.
"""
# 주의(2026-11-21): 이 파일의 글자 크기는 옛 기준(한글 크게, 영어 작게)이다. 새 쇼츠로 복사할 때는
# 영어를 위·한글을 아래에 두고 크기를 비슷하게(영어 = 한글 + 4px) 다시 잡는다 → _channel/shorts_playbook.md B-2a.
import os, sys, math
import numpy as np, cv2, cairo

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'jamo28'))
os.environ.setdefault('MG_SCALE', os.environ.get('HD_SCALE', '1'))
from mg import clamp, ramp, smooth, expo_out, expo_in_out, back_out, spring, lerp   # noqa: E402
from paper import W, H, SC, VERT, Level, composite, groove, grain, hexc, tex             # noqa: E402
import shapes as S                                                                   # noqa: E402

FPS = 30
SERIF = 'Noto Serif CJK KR'
R, RS = 318, 392                               # 해가 다니는 홈 반지름, 메달(절기 자리) 반지름
# 자리표: (x, y, 크기, 맞춤). 가로(1920×1080)와 세로 숏폼(1080×1920)
if not VERT:
    CX, CY = 960, 540
    LY = dict(q1=(760, 430, 92, 'r'), q2=(760, 560, 92, 'r'), sub=(760, 640, 30, 'r'), qm=(1480, 400, 70, 'l'),
              moon=(1360, 470), moon_in=-200, moon_out=(900, -260), sun0=(1100, 1250), sunh=(1230, 470),
              loop=(150, 520, 56, 'l'), r1=(150, 470, 84, 'l'), r2=(150, 570, 84, 'l'), r3=(150, 670, 84, 'l'),
              r4=(1770, 520, 40, 'r'), r5=(1770, 580, 40, 'r'),
              name=(150, 520, 150, 'l'), han=(160, 600, 48, 'l'), mean=(160, 670, 36, 'l'), deg=(160, 730, 28, 'l'),
              cnt=(1770, 520, 120, 'r'), cnt2=(1770, 580, 34, 'r'), season=(1770, 680, 44, 'r'),
              p1=(150, 480, 110, 'l'), p2=(150, 580, 64, 'l'), p3=(1770, 480, 52, 'r'), p4=(1770, 580, 88, 'r'),
              sheet_r=1500, end_dy=-40, credit=('br', 1650, 860, 90), hook=1.0, endsc=0.6, cfont=15)
else:
    CX, CY = 540, 1000
    LY = dict(q1=(540, 330, 100, 'c'), q2=(540, 465, 100, 'c'), sub=(540, 540, 36, 'c'), qm=(700, 880, 80, 'l'),
              moon=(610, 1000), moon_in=-200, moon_out=(700, -420), sun0=(560, 2150), sunh=(480, 1000),
              loop=(540, 420, 66, 'c'), r1=(540, 320, 104, 'c'), r2=(540, 435, 104, 'c'), r3=(540, 550, 104, 'c'),
              r4=(540, 1580, 46, 'c'), r5=(540, 1645, 46, 'c'),
              name=(540, 300, 168, 'c'), han=(540, 378, 52, 'c'), mean=(540, 448, 42, 'c'), deg=(540, 505, 30, 'c'),
              cnt=(540, 1575, 104, 'c'), cnt2=(540, 1625, 34, 'c'), season=(540, 1700, 48, 'c'),
              p1=(540, 330, 124, 'c'), p2=(540, 450, 72, 'c'), p3=(540, 1560, 56, 'c'), p4=(540, 1670, 100, 'c'),
              sheet_r=2300, end_dy=-120, credit=('bc', 540, 1400, 110), hook=1.45, endsc=0.72, cfont=19)
UNIT = 205                                    # 가운데 그림 크기

TERMS = [  # 이름, 한자, 뜻, 황경
    ('입춘', '立春', '봄의 시작', 315), ('우수', '雨水', '눈이 녹아 비', 330), ('경칩', '驚蟄', '겨울잠 깬 개구리', 345),
    ('춘분', '春分', '낮과 밤 같음', 0), ('청명', '淸明', '맑고 밝음', 15), ('곡우', '穀雨', '봄비로 곡식 윤택', 30),
    ('입하', '立夏', '여름의 시작', 45), ('소만', '小滿', '만물이 차오름', 60), ('망종', '芒種', '씨 뿌리기', 75),
    ('하지', '夏至', '낮이 가장 긴 날', 90), ('소서', '小暑', '작은 더위', 105), ('대서', '大暑', '큰 더위', 120),
    ('입추', '立秋', '가을의 시작', 135), ('처서', '處暑', '더위가 멈춤', 150), ('백로', '白露', '이슬이 맺힘', 165),
    ('추분', '秋分', '낮과 밤 같음', 180), ('한로', '寒露', '찬 이슬', 195), ('상강', '霜降', '서리가 내림', 210),
    ('입동', '立冬', '겨울의 시작', 225), ('소설', '小雪', '첫눈', 240), ('대설', '大雪', '큰 눈', 255),
    ('동지', '冬至', '밤이 가장 긴 날', 270), ('소한', '小寒', '작은 추위', 285), ('대한', '大寒', '큰 추위', 300)]
KEY = {3, 9, 15, 21}
SEASON = ['봄', '여름', '가을', '겨울']; SEASON_H = ['春', '夏', '秋', '冬']

def P(*h): return [hexc(x) for x in h]
# bg, c1, c2, c3, dark, light
PAL = [P('#CFE5C3', '#E8899C', '#4E9A57', '#F2CF5E', '#2B4632', '#FFF8EE'),
       P('#2C8790', '#F27C5E', '#A6D96E', '#F7E2A0', '#123A3E', '#FDF4E3'),
       P('#E2AE48', '#D2572A', '#7A4A2A', '#F7E8C4', '#4A2A12', '#FFF6E6'),
       P('#1E2A4E', '#FFFFFF', '#9DB7DE', '#E25B6A', '#0E1530', '#F4F1EA')]
CREAM = hexc('#EFE6D2'); INK = hexc('#1C1A18'); SUN = hexc('#E0442E'); MOON = hexc('#F2E3A6')

# ---------------------------------------------------------------- 시간표
T_RULE, T_TERMS = 6.0, 9.0
DURS = [2.8 if i in KEY else 1.6 for i in range(24)]
T0 = [T_TERMS + sum(DURS[:i]) for i in range(24)]
T_PAY = T_TERMS + sum(DURS)                   # 해가 한 바퀴를 마치는 때
T_END = T_PAY + 5.3
DUR = T_END + 2.7
HOP = 0.42                                    # 해가 한 칸(15°) 뛰는 시간
def season_of(i): return i // 6
def term_at(t):
    k = -1
    for i in range(24):
        if t >= T0[i]: k = i
    return k

def rad(deg): return math.radians(deg)
def on_ring(deg, r=R): return CX + r * math.cos(rad(deg)), CY - r * math.sin(rad(deg))

def sun_deg(t):
    """해의 황경(도). 갈고리: 처음엔 고리 그리며 한 바퀴, 절기마다 15° 톡 뛰어 자리 잡기."""
    if t < 4.0: return 315.0
    if t < 5.6: return 315.0 + 360.0 * expo_in_out(ramp(t, 4.0, 5.6))
    if t < T_TERMS: return 315.0 - 15.0 * expo_in_out(ramp(t, 8.4, T_TERMS))   # 첫 걸음 직전 한 칸 뒤로 물러섬
    k = term_at(t)
    if t >= T_PAY: return 300.0 + 15.0 * back_out(ramp(t, T_PAY, T_PAY + HOP), 1.8)   # 대한 → 다시 입춘 자리: 한 바퀴
    L = TERMS[k][3]
    return L - 15.0 + 15.0 * back_out(ramp(t, T0[k], T0[k] + HOP), 1.8)

def sun_r(t): return 44.0


# ---------------------------------------------------------------- 그리기 도구
def slide_text(cr, s, x, y, size, rgb, u_in, u_out, weight=cairo.FONT_WEIGHT_NORMAL, anchor='l', font=SERIF):
    """칼집(가로 틈)에서 밀려 올라오고 위로 빠지는 글자."""
    if u_in <= 0 or u_out >= 1: return
    cr.save()
    cr.select_font_face(font, cairo.FONT_SLANT_NORMAL, weight); cr.set_font_size(size)
    ext = cr.text_extents(s)
    dx = {'l': 0, 'c': -ext.x_advance / 2, 'r': -ext.x_advance}[anchor]
    cr.rectangle(x + dx - 20, y - size * 1.05, ext.x_advance + 40, size * 1.35); cr.clip()
    off = (1 - expo_out(u_in)) * size * 1.15 - expo_in_out(u_out) * size * 1.15
    cr.move_to(x + dx, y + off); cr.text_path(s)
    cr.set_source_rgb(*rgb); cr.fill()
    cr.restore()

def sl(cr, s, key, rgb, u_in, u_out, weight=cairo.FONT_WEIGHT_NORMAL):
    x, y, size, anc = LY[key]; slide_text(cr, s, x, y, size, rgb, u_in, u_out, weight, anc)

EN_TERMS = ['Start of Spring', 'Rain Water', 'Awakening of Insects', 'Spring Equinox · day = night', 'Clear and Bright', 'Grain Rain',
            'Start of Summer', 'Lesser Fullness of Grain', 'Grain in Ear', 'Summer Solstice · longest day', 'Minor Heat', 'Major Heat',
            'Start of Autumn', 'End of Heat', 'White Dew', 'Autumn Equinox · day = night', 'Cold Dew', "Frost's Descent",
            'Start of Winter', 'Minor Snow', 'Major Snow', 'Winter Solstice · longest night', 'Minor Cold', 'Major Cold']
SEASON_EN = ['Spring', 'Summer', 'Autumn', 'Winter']

def en(cr, key, s, rgb, u_in, u_out, size=30):
    """세로 숏폼: 한글 줄 바로 아래 영어 한 줄(같은 칼집 움직임)."""
    if not VERT: return
    x, y, sz, anc = LY[key]
    slide_text(cr, s, x, y + sz * 0.42 + size * 1.05, size, rgb, u_in, u_out, cairo.FONT_WEIGHT_NORMAL, anc)

def text_at(cr, s, x, y, size, rgb, a=1.0, weight=cairo.FONT_WEIGHT_NORMAL, anchor='l'):
    cr.save(); cr.select_font_face(SERIF, cairo.FONT_SLANT_NORMAL, weight); cr.set_font_size(size)
    ext = cr.text_extents(s); dx = {'l': 0, 'c': -ext.x_advance / 2, 'r': -ext.x_advance}[anchor]
    cr.move_to(x + dx, y); cr.text_path(s); cr.set_source_rgba(*rgb, a); cr.fill(); cr.restore()


def daynight(cr, f, pal, rot, day=None, night=None):
    """낮·밤 원판: 지평선 위가 낮, 아래가 밤. f(낮의 비율)가 클수록 지평선이 내려간다. rot: 지평선 기울기(등장 때 흔들림)."""
    day = day or pal[5]; night = night or (0.10, 0.13, 0.26)
    y0 = -math.cos(math.pi * f)
    cr.save(); S.circle(cr, 0, 0, 1.0); cr.clip()
    S.circle(cr, 0, 0, 1.0); S.fill(cr, day)
    cr.rotate(rot); cr.rectangle(-1.6, y0, 3.2, 2.0); S.fill(cr, night)
    S.circle(cr, 0.0, y0 - 0.28, 0.16); S.fill(cr, SUN)                 # 지평선 위 작은 해
    cr.restore()


# ---------------------------------------------------------------- 스물네 그림(단위 좌표, y는 아래가 +)
def vignette(cr, i, u, pal):
    """u: 이 그림이 나타난 뒤 흐른 시간(초). 그림 전체 등장(스프링)은 바깥에서."""
    bg, c1, c2, c3, dk, lt = pal
    sw = lambda a, f=1.0: math.sin(u * f * 2 * math.pi + a)
    if i == 0:      # 입춘: 언 땅을 뚫고 나온 싹
        S.ellipse(cr, 0, 0.75, 0.95, 0.28); S.fill(cr, dk)
        g = expo_out(ramp(u, 0.1, 0.7))
        S.bar(cr, 0, 0.62, 0, 0.62 - 0.75 * g, 0.07); S.fill(cr, c2)
        for s in (-1, 1):
            o = expo_out(ramp(u, 0.35, 1.0))
            S.leaf(cr, 0, 0.62 - 0.6 * g, 0.55 * o, 0.2 * o, -math.pi / 2 + s * (0.25 + 0.95 * o)); S.fill(cr, c2)
        S.circle(cr, 0, 0.62 - 0.78 * g, 0.09 * expo_out(ramp(u, 0.6, 1.1))); S.fill(cr, c1)
    elif i == 1:    # 우수: 구름에서 비
        for k in range(9):
            x = -0.7 + 0.175 * k; ph = (u * 1.3 + k * 0.37) % 1.0
            S.drop(cr, x, -0.15 + ph * 1.1, 0.07); S.fill(cr, c2 if k % 2 else lt, 1 - ph ** 3)
        for x, y, r in [(-0.45, -0.45, 0.32), (0.0, -0.6, 0.42), (0.45, -0.45, 0.34), (0.15, -0.35, 0.3), (-0.2, -0.35, 0.3)]:
            S.circle(cr, x, y, r)
        S.fill(cr, lt)
    elif i == 2:    # 경칩: 깨어나 뛰어오르는 개구리
        hop = (u * 0.9) % 1.0; jy = -1.1 * 4 * hop * (1 - hop); sq = 1 + 0.25 * math.exp(-((hop) / 0.08) ** 2)
        jx = -0.5 + 1.0 * ((u * 0.9) % 2.0) / 2.0 if False else 0.0
        S.ellipse(cr, 0.0, 0.85, 0.85, 0.12); S.fill(cr, dk)
        cr.save(); cr.translate(jx, 0.55 + jy); cr.scale(sq, 1 / sq)
        S.ellipse(cr, 0, 0, 0.5, 0.32); S.fill(cr, c2)
        for s in (-1, 1):
            S.ellipse(cr, s * 0.42, 0.2, 0.22, 0.1, s * 0.5); S.fill(cr, c2)
            S.circle(cr, s * 0.22, -0.3, 0.13); S.fill(cr, c2)
            S.circle(cr, s * 0.22, -0.32, 0.06); S.fill(cr, dk)
        cr.restore()
    elif i in (3, 15):   # 춘분·추분: 낮과 밤이 같다
        rot = (1 - spring(u / 0.9, 0.35, 1.6)) * (0.9 if i == 3 else -0.9)
        daynight(cr, 0.5, pal, rot)
        S.ring(cr, 0, 0, 0.98, 1.06); S.fill(cr, dk)
    elif i == 4:    # 청명: 버들가지와 제비
        for k in range(7):
            x = -0.85 + 0.28 * k; L = 0.9 + 0.25 * math.sin(k * 1.7)
            sway = 0.08 * sw(k * 0.6, 0.45)
            for j in range(6):
                y = -0.9 + j * L / 6
                S.leaf(cr, x + sway * j / 6, y, 0.16, 0.05, math.pi / 2 + 0.5 * (-1) ** j); S.fill(cr, c2)
        fx = -0.7 + 1.5 * ((u * 0.45) % 1.0); fy = -0.2 + 0.1 * sw(0, 0.7); fl = 0.35 * sw(0, 2.4)
        for s in (-1, 1):
            S.leaf(cr, fx, fy, 0.38, 0.09, math.pi + s * (0.45 + fl)); S.fill(cr, dk)
        S.ellipse(cr, fx + 0.05, fy, 0.14, 0.06); S.fill(cr, dk)
    elif i == 5:    # 곡우: 모판에 봄비
        for k in range(8):
            x = -0.84 + 0.24 * k; g = expo_out(ramp(u, 0.05 * k, 0.5 + 0.05 * k))
            for s in (-1, 1): S.leaf(cr, x, 0.8, 0.45 * g, 0.06, -math.pi / 2 + s * 0.3); S.fill(cr, c2)
        for k in range(10):
            x = -0.9 + 0.2 * k + 0.1; ph = (u * 1.6 + k * 0.29) % 1.0
            S.bar(cr, x, -0.9 + ph * 1.4, x - 0.03, -0.75 + ph * 1.4, 0.035); S.fill(cr, lt, 1 - ph)
        S.bar(cr, -0.95, 0.82, 0.95, 0.82, 0.08); S.fill(cr, dk)
    elif i == 6:    # 입하: 커다란 새잎(잎맥은 오려 낸 틈)
        g = expo_out(ramp(u, 0.0, 0.9))
        cr.save(); cr.rotate(-0.6 + 0.08 * sw(0, 0.4))
        S.leaf(cr, -0.85, 0.0, 1.75 * g, 0.62 * g, 0)
        S.bar(cr, -0.75, 0, -0.85 + 1.6 * g, 0, 0.035)
        for k in range(5):
            x = -0.55 + 0.3 * k
            if x < -0.85 + 1.6 * g:
                for s in (-1, 1): S.bar(cr, x, 0, x + 0.22, s * 0.28 * (1 - abs(k - 2) / 4), 0.03)
        S.fill(cr, c2, holes=True); cr.restore()
    elif i == 7:    # 소만: 보리 이삭이 차오름
        for s in (-0.45, 0.0, 0.45):
            S.bar(cr, s, 0.95, s + 0.05, -0.2, 0.04); S.fill(cr, c2)
            for j in range(7):
                g = back_out(ramp(u, 0.08 * j + abs(s), 0.3 + 0.08 * j + abs(s)))
                for side in (-1, 1):
                    S.ellipse(cr, s + 0.05 + side * 0.07, -0.2 - j * 0.11, 0.06 * g, 0.1 * g, side * 0.4); S.fill(cr, c3)
    elif i == 8:    # 망종: 물 위에 줄지어 심은 모
        for r in range(4):
            yy = 0.0 + r * 0.25; sc = 0.6 + 0.2 * r
            S.wave(cr, -1.0, 1.0, yy + 0.08, 0.02, 0.4, 0.05, u * 2 + r); S.fill(cr, lt, 0.8)
            for k in range(7):
                g = expo_out(ramp(u, 0.12 * r + 0.03 * k, 0.4 + 0.12 * r + 0.03 * k))
                x = (-0.75 + 0.25 * k) * sc
                for s in (-1, 0, 1): S.leaf(cr, x, yy + 0.05, 0.28 * sc * g, 0.03 * sc, -math.pi / 2 + s * 0.35); S.fill(cr, c2)
    elif i == 9:    # 하지: 낮이 가장 긴 날 — 해살이 퍼지는 원판
        rot = (1 - spring(u / 0.9, 0.35, 1.6)) * 0.9
        for k in range(16):
            a = k * math.pi / 8 + u * 0.4; g = back_out(ramp(u, 0.02 * k, 0.4 + 0.02 * k))
            S.leaf(cr, math.cos(a) * 0.95, math.sin(a) * 0.95, 0.35 * g, 0.09, a); S.fill(cr, c3)
        daynight(cr, 0.61, pal, rot, day=pal[5], night=pal[4])
        S.ring(cr, 0, 0, 0.98, 1.06); S.fill(cr, c1)
    elif i == 10:   # 소서: 연꽃이 핀다
        S.ellipse(cr, 0, 0.6, 0.95, 0.22); S.fill(cr, c2)
        o = expo_out(ramp(u, 0.1, 1.2))
        for k, (a, L) in enumerate([(-1.2, 0.6), (-0.75, 0.68), (-0.3, 0.72), (0.15, 0.72), (0.6, 0.68), (1.05, 0.6)]):
            aa = -math.pi / 2 + a * (0.4 + 0.6 * o)
            S.leaf(cr, 0, 0.45, L * (0.6 + 0.4 * o), 0.2, aa); S.fill(cr, c1 if k % 2 else lt)
    elif i == 11:   # 대서: 끓는 더위
        S.circle(cr, 0, -0.35, 0.42 * back_out(ramp(u, 0, 0.5))); S.fill(cr, c3)
        for k in range(4):
            S.wave(cr, -0.95, 0.95, 0.2 + 0.2 * k - 0.15 * ((u * 0.6) % 1.0), 0.06, 0.45, 0.07, u * 5 + k); S.fill(cr, c1 if k % 2 else c3)
    elif i == 12:   # 입추: 첫 잎이 떨어진다
        y = -0.8 + 1.4 * ramp(u, 0, 1.8); x = 0.35 * math.sin(u * 2.8)
        cr.save(); cr.translate(x, y); cr.rotate(0.9 * math.sin(u * 2.8 + 1))
        S.leaf(cr, -0.3, 0, 0.6, 0.24, 0); S.fill(cr, c1); cr.restore()
        S.bar(cr, -1.0, -0.85, 0.2, -0.95, 0.07); S.fill(cr, c2)
        for k in range(3): S.leaf(cr, -0.7 + 0.3 * k, -0.9, 0.3, 0.1, math.pi / 2 + 0.4); S.fill(cr, c2 if k else c1)
    elif i == 13:   # 처서: 고추잠자리
        hx, hy = 0.15 * math.sin(u * 1.3), 0.08 * math.sin(u * 2.1)
        cr.save(); cr.translate(hx, hy); cr.rotate(-0.15)
        fl = 0.25 * math.sin(u * 30)
        for s in (-1, 1):
            for off in (0, 0.12):
                S.ellipse(cr, -0.05 + off, s * 0.32, 0.12, 0.38, s * (0.25 + off * 2) + fl * s); S.fill(cr, lt, 0.85)
        S.bar(cr, -0.2, 0, 0.95, 0, 0.07); S.fill(cr, c1)
        S.circle(cr, -0.25, 0, 0.11); S.fill(cr, c1)
        cr.restore()
    elif i == 14:   # 백로: 풀잎에 맺힌 이슬(빛이 새는 구멍)
        for k in range(7):
            x = -0.8 + 0.27 * k; a = -math.pi / 2 + 0.25 * math.sin(k * 2.3) + 0.03 * sw(k, 0.5)
            S.leaf(cr, x, 0.95, 1.3 - 0.15 * (k % 3), 0.07, a); S.fill(cr, c2)
        for k in range(9):
            g = back_out(ramp(u, 0.1 * k, 0.35 + 0.1 * k))
            S.circle(cr, -0.75 + 0.19 * k, -0.15 + 0.45 * math.sin(k * 1.9), 0.06 * g); S.fill(cr, lt)
    elif i == 16:   # 한로: 국화
        for ring_, (n, L, col) in enumerate([(18, 0.95, c3), (14, 0.7, c1), (10, 0.45, lt)]):
            for k in range(n):
                a = k * 2 * math.pi / n + ring_ * 0.2; g = back_out(ramp(u, 0.02 * k + 0.15 * ring_, 0.4 + 0.02 * k + 0.15 * ring_))
                S.leaf(cr, 0, 0, L * g, 0.1 + 0.03 * ring_, a); S.fill(cr, col)
        S.circle(cr, 0, 0, 0.16); S.fill(cr, c2)
    elif i == 17:   # 상강: 가지 끝 감과 서리
        S.bar(cr, -1.0, -0.6, 0.6, -0.75, 0.08); S.fill(cr, c2)
        for k, x in enumerate((-0.4, 0.25)):
            g = back_out(ramp(u, 0.2 * k, 0.5 + 0.2 * k)); sy = 0.05 * math.sin(u * 2 + k)
            S.circle(cr, x, -0.2 + sy, 0.3 * g); S.fill(cr, c1)
            S.leaf(cr, x, -0.48 + sy, 0.18 * g, 0.08, -math.pi / 2 - 0.6); S.leaf(cr, x, -0.48 + sy, 0.18 * g, 0.08, -math.pi / 2 + 0.6); S.fill(cr, c2)
        for k in range(12):
            g = expo_out(ramp(u, 0.6 + 0.04 * k, 1.0 + 0.04 * k))
            S.flake(cr, -0.9 + 0.16 * k, 0.6 + 0.2 * math.sin(k * 2.7), 0.06 * g, 0.012); S.fill(cr, lt)
    elif i == 18:   # 입동: 잎 진 가지가 자란다
        def br(x, y, a, L, d, k0):
            g = expo_out(ramp(u, k0, k0 + 0.35))
            if g <= 0: return
            x1, y1 = x + math.cos(a) * L * g, y + math.sin(a) * L * g
            S.bar(cr, x, y, x1, y1, 0.07 * (0.65 ** (4 - d))); S.fill(cr, lt)
            if d > 0 and g > 0.6:
                br(x1, y1, a - 0.5, L * 0.68, d - 1, k0 + 0.18); br(x1, y1, a + 0.45, L * 0.62, d - 1, k0 + 0.24)
        br(0, 0.95, -math.pi / 2, 0.75, 4, 0.0)
    elif i in (19, 20):  # 소설·대설: 눈
        n = 7 if i == 19 else 22
        for k in range(n):
            ph = (u * 0.35 + k * 0.618) % 1.0; x = -0.9 + 1.8 * ((k * 0.381) % 1.0) + 0.08 * math.sin(u * 1.5 + k)
            S.flake(cr, x, -0.95 + 1.8 * ph, (0.14 if i == 19 else 0.09) * (0.7 + 0.3 * ((k * 0.7) % 1)), 0.02, u * 0.6 + k); S.fill(cr, lt)
        if i == 20:
            S.ellipse(cr, 0, 1.05, 1.1, 0.35 * expo_out(ramp(u, 0.2, 1.4))); S.fill(cr, lt)
    elif i == 21:   # 동지: 밤이 가장 긴 날 — 원판이 밤으로 가득
        rot = (1 - spring(u / 0.9, 0.35, 1.6)) * -0.9
        daynight(cr, 0.39, pal, rot, day=pal[5], night=pal[4])
        for k in range(10):
            g = back_out(ramp(u, 0.3 + 0.05 * k, 0.6 + 0.05 * k))
            a = 0.8 + k * 0.48
            S.flake(cr, 0.62 * math.cos(a), 0.62 * math.sin(a) * 0.9 + 0.2, 0.05 * g, 0.012); S.fill(cr, lt)
        S.ring(cr, 0, 0, 0.98, 1.06); S.fill(cr, c2)
    elif i == 22:   # 소한: 처마 끝 고드름
        S.bar(cr, -1.0, -0.85, 1.0, -0.85, 0.14); S.fill(cr, lt)
        for k in range(9):
            x = -0.85 + 0.21 * k; g = expo_out(ramp(u, 0.06 * k, 0.6 + 0.06 * k)); L = (0.4 + 0.5 * ((k * 0.618) % 1)) * g
            S.poly(cr, [(x - 0.06, -0.8), (x + 0.06, -0.8), (x, -0.8 + L)]); S.fill(cr, c2)
    elif i == 23:   # 대한: 눈 속 매화(다시 봄을 부른다)
        S.bar(cr, -0.95, 0.75, 0.0, -0.1, 0.09); S.bar(cr, 0.0, -0.1, 0.7, -0.6, 0.06); S.bar(cr, -0.3, 0.3, -0.7, -0.3, 0.05); S.fill(cr, lt)
        for k, (x, y) in enumerate([(0.0, -0.1), (0.42, -0.42), (0.7, -0.6), (-0.55, -0.1), (-0.7, -0.3), (-0.4, 0.42)]):
            g = back_out(ramp(u, 0.25 + 0.12 * k, 0.55 + 0.12 * k), 2.2)
            for p in range(5):
                a = p * 2 * math.pi / 5 + k
                S.circle(cr, x + 0.1 * g * math.cos(a), y + 0.1 * g * math.sin(a), 0.08 * g)
            S.fill(cr, c3); S.circle(cr, x, y, 0.04 * g); S.fill(cr, c3 if False else (1, 0.85, 0.4))
        for k in range(14):
            ph = (u * 0.3 + k * 0.618) % 1.0
            S.circle(cr, -0.9 + 1.8 * ((k * 0.381) % 1.0), -0.95 + 1.9 * ph, 0.025); S.fill(cr, lt)


def medc(s, u=1.0):
    """자리 메달 바탕: 계절 바탕보다 조금 밝게(겨울 남색 위에서도 보이게)."""
    bg, lt = PAL[s][0], PAL[s][5]; m = 0.10 if s != 3 else 0.2
    return tuple(b + (l - b) * m * u for b, l in zip(bg, lt))


def place_vig(cr, i, u, pal, cx, cy, unit, alpha=1.0):
    cr.save(); cr.translate(cx, cy); cr.scale(unit, unit)
    cr.arc(0, 0, 1.08 / 0.92, 0, 2 * math.pi); cr.clip()          # 그림은 제 원판 안에서만
    cr.push_group(); vignette(cr, i, u, pal); cr.pop_group_to_source(); cr.paint_with_alpha(alpha)
    cr.restore()


# ---------------------------------------------------------------- 한 장면(층별로 그림)
def bg_color(t):
    """바닥 종이 색과 지금 넘어가는 새 계절 종이(부채꼴로 덮임)."""
    if t < T_TERMS: return CREAM, None, 0
    k = term_at(t); s = season_of(k)
    if t >= T_END:                                # 끝: 한지 종이가 다시 덮이고 꽃만 남는다
        w = expo_in_out(ramp(t, T_END, T_END + 0.9))
        return (PAL[3][0], CREAM, w) if w < 1 else (CREAM, None, 0)
    if t >= T_PAY + 0.6: return PAL[3][0], None, 0
    t_s = T0[s * 6]
    wipe = expo_in_out(ramp(t, t_s, t_s + 0.9))
    old = CREAM if s == 0 else PAL[s - 1][0]
    if wipe >= 1: return PAL[s][0], None, 0
    return old, PAL[s][0], wipe


def draw(t, L):
    k = term_at(t); s = season_of(k) if k >= 0 else 0
    pal = PAL[s]
    txt = pal[4] if s in (0, 2) else pal[5]
    if t < T_TERMS: txt = INK

    # -- 계절 종이 넘김(부채꼴, 해 자리에서 시작해 반시계로)
    old, new, wipe = bg_color(t)
    if new is not None and L.get('_sheet', True):
        a0 = rad(TERMS[s * 6][3] - 15) if t < T_END else rad(315)
        S.sector(L['sheet'].cr, CX, CY, LY['sheet_r'], a0, a0 + 2 * math.pi * wipe); S.fill(L['sheet'].cr, new)

    # -- 홈: 해의 길 + 24 눈금
    g = L['groove'].cr; g.set_line_width(3.2)
    if t >= T_END: g.push_group()
    if t >= 4.0:
        sweep = 2 * math.pi * expo_in_out(ramp(t, 4.0, 5.6))
        a0 = rad(315)
        n = max(2, int(sweep / 0.01))
        for j in range(n + 1):
            a = a0 + sweep * j / n; x, y = CX + R * math.cos(a), CY - R * math.sin(a)
            (g.move_to if j == 0 else g.line_to)(x, y)
        g.set_source_rgb(1, 1, 1); g.stroke()
    for j in range(24):
        tj = T_RULE + 0.25 + 0.055 * j
        if t < tj: continue
        gg = back_out(ramp(t, tj, tj + 0.25), 2.0)
        d = TERMS[j][3]; L1 = 14 * gg
        x0, y0 = on_ring(d, R - L1); x1, y1 = on_ring(d, R + L1)
        g.set_line_width(4.0 if j in KEY else 2.6); g.move_to(x0, y0); g.line_to(x1, y1); g.set_source_rgb(1, 1, 1); g.stroke()

    if t >= T_END: g.pop_group_to_source(); g.paint_with_alpha(1 - smooth(ramp(t, T_END, T_END + 0.8)))

    # -- 처음: 달과 물음 → 해가 밀어냄 → 제목
    ty = L['type'].cr; vg = L['vig'].cr; sn = L['sun'].cr
    if t < 6.2:
        mx = lerp(LY['moon_in'], LY['moon'][0], expo_out(ramp(t, 0.2, 1.4))) + LY['moon_out'][0] * expo_in_out(ramp(t, 2.55, 3.2))
        my = LY['moon'][1] + 10 * math.sin(t * 2.2) + LY['moon_out'][1] * expo_in_out(ramp(t, 2.55, 3.2))
        if t < 3.3:
            vg.save(); vg.translate(mx, my); vg.rotate(-0.3 + 1.6 * expo_in_out(ramp(t, 2.55, 3.2)))
            vg.scale(LY['hook'], LY['hook'])
            S.circle(vg, 0, 0, 92); S.fill(vg, MOON)
            S.circle(vg, 38, -22, 76); S.fill(vg, hexc('#D9C88A'))     # 그믐 그림자(한 장 더 덧댄 종이)
            vg.restore()
        q_out = ramp(t, 3.9, 4.4)
        sl(ty, '24절기는', 'q1', INK, ramp(t, 0.35, 1.0), q_out, cairo.FONT_WEIGHT_BOLD)
        sl(ty, '음력일까?', 'q2', INK, ramp(t, 0.6, 1.25), max(ramp(t, 2.6, 3.0), q_out), cairo.FONT_WEIGHT_BOLD)
        en(ty, 'q2', 'Are the 24 solar terms lunar?', INK, ramp(t, 0.7, 1.35), max(ramp(t, 2.6, 3.0), q_out))
        sl(ty, '해의 달력', 'q2', SUN, ramp(t, 3.0, 3.5), q_out, cairo.FONT_WEIGHT_BOLD)
        sl(ty, '해의 길을 15°씩 나눈 것', 'sub', INK, ramp(t, 3.2, 3.7), q_out)
        en(ty, 'sub', 'A calendar of the sun — its path cut every 15°', INK, ramp(t, 3.3, 3.8), q_out, 28)
        if 0.6 < t < 3.0:
            text_at(ty, '?', LY['qm'][0], LY['qm'][1], LY['qm'][2], INK, smooth(ramp(t, 1.2, 1.5)) * (1 - ramp(t, 2.5, 2.7)), cairo.FONT_WEIGHT_BOLD)
        sl(ty, '해가 한 바퀴 = 1년', 'loop', INK, ramp(t, 4.3, 4.8), ramp(t, 5.9, 6.3), cairo.FONT_WEIGHT_BOLD)
        en(ty, 'loop', 'One lap of the sun = one year', INK, ramp(t, 4.4, 4.9), ramp(t, 5.9, 6.3))

    # -- 규칙: 360 ÷ 24 = 15
    if T_RULE - 0.2 < t < T_TERMS + 0.4:
        uo = ramp(t, T_TERMS - 0.3, T_TERMS + 0.2)
        sl(ty, '360°', 'r1', INK, ramp(t, T_RULE, T_RULE + 0.4), uo, cairo.FONT_WEIGHT_BOLD)
        sl(ty, '÷ 24', 'r2', INK, ramp(t, T_RULE + 0.5, T_RULE + 0.9), uo, cairo.FONT_WEIGHT_BOLD)
        sl(ty, '= 15°', 'r3', SUN, ramp(t, T_RULE + 1.6, T_RULE + 2.0), uo, cairo.FONT_WEIGHT_BOLD)
        sl(ty, '절기 하나', 'r4', INK, ramp(t, T_RULE + 1.9, T_RULE + 2.3), uo)
        sl(ty, '해의 한 걸음', 'r5', INK, ramp(t, T_RULE + 2.1, T_RULE + 2.5), uo)
        en(ty, 'r5', 'One solar term = one step of the sun', INK, ramp(t, T_RULE + 2.2, T_RULE + 2.6), uo)

    # -- 절기 자리(메달): 지나온 절기는 고리 바깥 자리에 남는다
    md = L['med'].cr
    fsc = lerp(1.0, LY['endsc'], expo_in_out(ramp(t, T_END, T_END + 1.2)))
    md.save(); md.translate(CX, CY + LY['end_dy'] * (1 - fsc) / (1 - LY['endsc'])); md.scale(fsc, fsc); md.translate(-CX, -CY)
    for j in range(24):
        if k < 0 or j > k: break
        tf = T0[j + 1] - 0.35 if j < 23 else T_PAY - 0.35
        if t < tf: continue                                    # 아직 가운데에 떠 있음
        u = expo_in_out(ramp(t, tf, tf + 0.45))
        d = TERMS[j][3]; mx_, my_ = on_ring(d, RS)
        pj = PAL[season_of(j)]
        pay = expo_in_out(ramp(t, T_PAY + 0.7, T_PAY + 1.9))
        if pay > 0:                                          # 끝: 메달이 꽃잎이 되어 해를 감싼다
            rr = lerp(RS, 205, pay); mx_, my_ = on_ring(d + 360 * 0.04 * pay, rr)
            S.leaf(md, CX + (mx_ - CX) * 0.35, CY + (my_ - CY) * 0.35, lerp(0, 230, pay) + 1e-3, lerp(40, 46, pay), -rad(d + 360 * 0.04 * pay))
            S.fill(md, pj[1] if j % 2 else pj[3] if season_of(j) != 3 else pj[2])
        rr_ = lerp(UNIT, 38, u) * (1 - pay)
        cx_, cy_ = lerp(CX, mx_, u), lerp(CY, my_, u)
        if rr_ > 1:
            S.circle(md, cx_, cy_, rr_ * 1.08); S.fill(md, medc(season_of(j), u))
            place_vig(md, j, t - T0[j] - HOP, pj, cx_, cy_, rr_ * 0.92)

    md.restore()

    # -- 지금 절기: 가운데 그림 + 왼쪽 이름 + 오른쪽 계절/번호
    if 0 <= k and t < T_PAY:
        tl = T0[k] + HOP * 0.7                                 # 해가 자리 잡는 순간
        tf = (T0[k + 1] if k < 23 else T_PAY) - 0.35
        if t < tf:
            pop = spring(ramp(t, tl, tl + 0.55) * 1.0, 0.42, 1.4)
            if t >= tl:
                vg.save(); vg.translate(CX, CY); vg.scale(max(pop, 1e-3), max(pop, 1e-3)); vg.translate(-CX, -CY)
                S.circle(vg, CX, CY, UNIT * 1.08); S.fill(vg, medc(s))
                place_vig(vg, k, t - T0[k] - HOP, pal, CX, CY, UNIT * 0.92)
                vg.restore()
        name, han, mean, deg = TERMS[k]
        nt = T0[k + 1] if k < 23 else T_PAY
        u_in = ramp(t, tl - 0.05, tl + 0.35); u_out = ramp(t, nt - 0.05, nt + 0.3)
        sl(ty, name, 'name', txt, u_in, u_out, cairo.FONT_WEIGHT_BOLD)
        sl(ty, han, 'han', txt, ramp(t, tl + 0.05, tl + 0.4), u_out)
        sl(ty, mean, 'mean', (SUN if s in (0, 2) else pal[3]) if k in KEY else txt, ramp(t, tl + 0.12, tl + 0.5), u_out, cairo.FONT_WEIGHT_BOLD if k in KEY else cairo.FONT_WEIGHT_NORMAL)
        sl(ty, f'황경 {deg}°', 'deg', txt, ramp(t, tl + 0.18, tl + 0.55), u_out)
        en(ty, 'deg', EN_TERMS[k], (SUN if s in (0, 2) else pal[3]) if k in KEY else txt, ramp(t, tl + 0.22, tl + 0.6), u_out, 32)
        sl(ty, f'{k + 1:02d}', 'cnt', txt, u_in, u_out, cairo.FONT_WEIGHT_BOLD)
        sl(ty, '/ 24', 'cnt2', txt, u_in, u_out)
        so = ramp(t, T0[s * 6], T0[s * 6] + 0.5); se = ramp(t, (T0[s * 6 + 6] if s < 3 else T_PAY) - 0.05, (T0[s * 6 + 6] if s < 3 else T_PAY) + 0.3)
        sl(ty, f'{SEASON[s]} {SEASON_H[s]}', 'season', txt, so, se, cairo.FONT_WEIGHT_BOLD)
        en(ty, 'season', SEASON_EN[s], txt, so, se)

    # -- 끝: 1년 = 해 한 바퀴
    if t >= T_PAY:
        w = PAL[3][5]
        sl(ty, '1년', 'p1', w, ramp(t, T_PAY + 1.3, T_PAY + 1.7), ramp(t, T_END - 0.4, T_END))
        sl(ty, '= 해 한 바퀴', 'p2', w, ramp(t, T_PAY + 1.5, T_PAY + 1.9), ramp(t, T_END - 0.4, T_END), cairo.FONT_WEIGHT_BOLD)
        en(ty, 'p2', 'One year = one lap of the sun', w, ramp(t, T_PAY + 1.6, T_PAY + 2.0), ramp(t, T_END - 0.4, T_END), 34)
        sl(ty, '24절기는', 'p3', w, ramp(t, T_PAY + 2.2, T_PAY + 2.6), ramp(t, T_END - 0.4, T_END))
        sl(ty, '해의 달력', 'p4', SUN, ramp(t, T_PAY + 2.4, T_PAY + 2.8), ramp(t, T_END - 0.4, T_END), cairo.FONT_WEIGHT_BOLD)
        en(ty, 'p4', 'The 24 solar terms: a calendar of the sun', w, ramp(t, T_PAY + 2.5, T_PAY + 2.9), ramp(t, T_END - 0.4, T_END), 32)

    # -- 해
    if t >= 1.9:
        d = sun_deg(t)
        if t < 4.0:      # 아래에서 솟아 달을 밀고 → 고리 시작점으로
            u1 = back_out(ramp(t, 1.9, 2.6), 1.4); x0, y0 = LY['sun0']
            x1, y1 = LY['sunh']
            x2, y2 = on_ring(315)
            u2 = expo_in_out(ramp(t, 3.3, 4.0))
            x = lerp(lerp(x0, x1, u1), x2, u2); y = lerp(lerp(y0, y1, u1), y2, u2); r = lerp(70 * LY['hook'], sun_r(t), u2)
        else:
            x, y = on_ring(d); r = sun_r(t)
            pay = expo_in_out(ramp(t, T_PAY + 0.7, T_PAY + 1.9))
            if pay > 0: x, y, r = lerp(x, CX, pay), lerp(y, CY, pay), lerp(r, 120, pay)
        # 하지에는 해 뒤로 햇살 조각
        if k == 9 and t < T0[10]:
            rg = back_out(ramp(t, T0[9] + HOP, T0[9] + HOP + 0.5))
            for j in range(12):
                a = j * math.pi / 6 + t * 0.6
                S.leaf(sn, x + math.cos(a) * r * 1.05, y + math.sin(a) * r * 1.05, 34 * rg, 9, a)
            S.fill(sn, PAL[1][3])
        if t >= T_END:
            fsc = lerp(1.0, LY['endsc'], expo_in_out(ramp(t, T_END, T_END + 1.2)))
            x, y, r = CX + (x - CX) * fsc, CY + LY['end_dy'] * (1 - fsc) / (1 - LY['endsc']) + (y - CY) * fsc, r * fsc
        S.circle(sn, x, y, r); S.fill(sn, SUN)
        # 착지 반짝임(눈금이 울림)
        if k >= 0 and t < T_PAY:
            tl = T0[k] + HOP * 0.7; e = ramp(t, tl, tl + 0.5)
            if 0 < e < 1:
                S.ring(L['groove'].cr, x, y, r + 6 + 40 * expo_out(e), r + 9 + 40 * expo_out(e))
                L['groove'].cr.set_source_rgba(1, 1, 1, 1 - e); L['groove'].cr.fill()


DEPTH = [('sheet', 0.5, 0.30), ('med', 0.9, 0.30), ('vig', 1.6, 0.34), ('type', 0.7, 0.30), ('sun', 2.2, 0.36)]


def frame(t, samples=3, shutter=0.5):
    acc = {}
    for si in range(samples):
        tt = t + ((si + 0.5) / samples - 0.5) * shutter / FPS if samples > 1 else t
        L = {n: Level(d, sh) for n, d, sh in DEPTH}; L['groove'] = Level(0, 0)
        L['_sheet'] = (si == samples // 2)          # 큰 종이 넘김은 한 번만(겹쳐 그리면 줄무늬)
        draw(tt, L)
        L.pop('_sheet')
        for n, lv in L.items():
            a = lv.array(); acc[n] = a if n not in acc else acc[n] + a
    for n in acc: acc[n] /= samples
    acc['sheet'] *= samples                      # 종이 넘김은 가운데 한 번만 그렸으므로
    old, new, wipe = bg_color(t)
    base = np.empty((H, W, 3), np.float32); base[:] = np.array(old[::-1], np.float32)
    base *= tex()[..., None]
    base = composite(base, acc['sheet'], 0.5, 0.30)
    base = groove(base, acc['groove'][..., 3])
    for n, d, sh in DEPTH[1:]:
        base = composite(base, acc[n], d, sh)
    # 가장자리 살짝 어둡게(시선 모음)
    return base


_VIG = None
def vignette_mask():
    global _VIG
    if _VIG is None:
        y, x = np.mgrid[0:H, 0:W].astype(np.float32)
        r = np.hypot((x - W / 2) / (W / 2), (y - H / 2) / (H / 2))
        _VIG = (1 - 0.18 * np.clip(r - 0.55, 0, 1) ** 1.5)[..., None].astype(np.float32)
    return _VIG


CREDIT = ['Created & Coded by L.S.M.', '허상공방 虛像工房 Project']
T_SEAL = T_END + 1.1
_credit = {}
def credit_layer():
    if _credit: return _credit['v']
    from PIL import Image, ImageDraw, ImageFont
    S2 = 2.0 * SC
    fnt = ImageFont.truetype('/usr/share/fonts/opentype/noto/NotoSerifCJK-Regular.ttc', int(LY['cfont'] * S2), index=1)
    mode, cx, cy, sz0 = LY['credit']; sz = int(round(sz0 * SC))
    im = Image.new('L', (W, H), 0); d = ImageDraw.Draw(im)
    if mode == 'br':                       # 가로: 오른쪽 아래, 글줄은 인장 왼쪽(〈스물여덟 자〉 자리)
        xs, ys = int(round(cx * SC)), int(round(cy * SC)); tr = xs - int(15 * S2)
        d.text((tr, ys + int(1 * S2)), CREDIT[0], font=fnt, fill=255, anchor='ra')
        d.text((tr, ys + sz - int(21 * S2)), CREDIT[1], font=fnt, fill=255, anchor='ra')
    else:                                  # 세로: 꽃 아래 가운데, 인장 아래 두 줄
        xs, ys = int(round(cx * SC)) - sz // 2, int(round(cy * SC))
        d.text((int(cx * SC), ys + sz + int(30 * S2)), CREDIT[0], font=fnt, fill=255, anchor='mm')
        d.text((int(cx * SC), ys + sz + int(60 * S2)), CREDIT[1], font=fnt, fill=255, anchor='mm')
    tm = cv2.GaussianBlur(np.asarray(im, np.float32) / 255, (0, 0), 0.35 * S2)
    seal = np.load(os.path.join(HERE, '..', '_shared', 'seal_baimun3.npy')).astype(np.float32)
    seal = cv2.resize(seal, (sz, sz), interpolation=cv2.INTER_AREA)[..., [2, 1, 0, 3]]
    _credit['v'] = (tm, seal, xs, ys, sz)
    return _credit['v']

def apply_credit(img, t):
    if t < T_SEAL: return img
    tm, seal, xs, ys, sz = credit_layer()
    a1 = smooth(ramp(t, T_SEAL, T_SEAL + 0.2))
    red = np.clip((seal[..., 2:3] - seal[..., 1:2]) * 4, 0, 1)
    al = seal[..., 3:4] * a1 * red
    sub = img[ys:ys + sz, xs:xs + sz]; img[ys:ys + sz, xs:xs + sz] = sub * (1 - al + al * seal[..., :3])
    a2 = smooth(ramp(t, T_SEAL + 0.5, T_SEAL + 1.4))
    k = (tm * a2 * 0.92)[..., None]
    return img * (1 - k) + np.array(INK[::-1], np.float32) * k


def final(t, samples=3):
    img = frame(t, samples) * vignette_mask()
    img = apply_credit(img, t)
    return grain(img, int(round(t * FPS)), 0.008)


if __name__ == '__main__':
    out = sys.argv[1]; os.makedirs(out, exist_ok=True)
    for ts in sys.argv[2:]:
        t = float(ts); img = final(t)
        cv2.imwrite(os.path.join(out, f't{t:05.2f}.png'), np.clip(img * 255, 0, 255).astype(np.uint8))
        print('wrote', t, flush=True)
