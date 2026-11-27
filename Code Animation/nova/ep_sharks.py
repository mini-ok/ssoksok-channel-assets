"""〈상어는 나무보다 먼저〉 — 흑백 목판화 화석 도감풍(먹색 면 + 흰 새김선, 붉은 한 색), 첼로 드론·낮은 북 소리.
사실: 상어(또는 아주 가까운 조상)의 비늘 화석 약 4억 5천만 년 전(논쟁 있음), 논쟁 없는 상어 비늘 약 4억 2천만 년 전,
최초의 나무 약 3억 8,500만 년 전(Natural History Museum 상어 연표; Live Science; Discover Wildlife 정리).
"""
import math, numpy as np, cv2, cairo
from base import *
import sfx as S

PAPER = (0.94, 0.91, 0.84); INKC = (0.07, 0.06, 0.06); RED = (0.74, 0.16, 0.12)

_P = {}
def paper():
    if 'v' in _P: return _P['v']
    r = np.random.default_rng(2); n = cv2.GaussianBlur(r.standard_normal((H, W)).astype(np.float32), (0, 0), 1.2)
    b = cv2.resize(r.standard_normal((H // 80 + 2, W // 80 + 2)).astype(np.float32), (W, H), interpolation=cv2.INTER_CUBIC)
    _P['v'] = solid(PAPER) * (1 + 0.03 * n + 0.03 * b)[..., None]; return _P['v']

def hatch(cr, x0, y0, x1, y1, gap=9, w=2.2, ang=0.0, wob=0.0, t=0.0):
    """현재 clip 안에 평행 새김선."""
    cr.save(); cr.set_line_width(w); L = max(x1 - x0, y1 - y0) * 1.6; cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    cr.translate(cx, cy); cr.rotate(ang); k = -L
    while k < L:
        cr.move_to(-L, k)
        for i in range(1, 25):
            xx = -L + 2 * L * i / 24; cr.line_to(xx, k + wob * math.sin(xx * 0.02 + k * 0.05 + t))
        k += gap
    cr.stroke(); cr.restore()

def shark(cr, x, y, s, a, t=0.0, flip=False, halo=False):
    s = max(s, 1e-3); cr.save(); cr.translate(x, y); cr.scale(-s if flip else s, s)
    sw = math.sin(t * 3) * 6
    def body():
        cr.move_to(-150, 0); cr.curve_to(-120, -38, -20, -46, 60, -30); cr.line_to(88, -78 + sw * 0.2); cr.line_to(100, -26)
        cr.curve_to(130, -18, 150, -8, 168, -4); cr.line_to(210, -60 + sw); cr.line_to(196, 0); cr.line_to(214, 52 + sw); cr.line_to(166, 10)
        cr.curve_to(120, 24, 60, 30, 20, 30); cr.line_to(-10, 64); cr.line_to(-30, 28); cr.curve_to(-90, 26, -140, 16, -150, 0); cr.close_path()
    if halo: body(); cr.set_source_rgba(*PAPER, a); cr.set_line_width(22); cr.stroke()
    body(); cr.set_source_rgba(*INKC, a); cr.fill()
    cr.save(); body(); cr.clip(); cr.set_source_rgba(*PAPER, a)
    cr.set_line_width(2.2)
    for k in range(10):                                         # 배쪽 새김(밝은 배)
        yk = 6 + k * 3.2; cr.move_to(-140, yk); cr.curve_to(-60, yk + 6, 60, yk + 8, 170, yk - 2); cr.stroke()
    for k in range(6):                                          # 등 곡선 새김
        yk = -30 + k * 5; cr.move_to(-100, yk); cr.curve_to(-30, yk - 6, 60, yk - 4, 150, yk + 6); cr.stroke()
    cr.restore()
    cr.set_source_rgba(*PAPER, a); cr.arc(-112, -8, 4, 0, 6.283); cr.fill()
    cr.set_line_width(2.5)
    for k in range(5): cr.move_to(-84 + k * 8, -10); cr.curve_to(-82 + k * 8, 0, -84 + k * 8, 8, -86 + k * 8, 14); cr.stroke()
    cr.restore()

def tree(cr, x, y, s, a, grow=1.0):
    if grow <= 0: return
    cr.save(); cr.translate(x, y); cr.scale(s * grow ** 0.5, s * grow)
    cr.set_source_rgba(*INKC, a); cr.move_to(-14, 0); cr.line_to(-8, -170); cr.line_to(8, -170); cr.line_to(14, 0); cr.close_path(); cr.fill()
    for (cx, cy, r) in ((0, -200, 70), (-55, -165, 52), (55, -165, 52), (-30, -250, 48), (32, -248, 46), (0, -290, 40)):
        cr.arc(cx, cy, r, 0, 6.283); cr.fill()
    cr.set_source_rgba(*PAPER, a); cr.set_line_width(2)
    r_ = np.random.default_rng(int(x))
    for _ in range(46):
        px, py = r_.uniform(-90, 90), r_.uniform(-320, -130)
        if (px / 95) ** 2 + ((py + 215) / 115) ** 2 < 0.8: cr.arc(px, py, 7, 3.6, 5.8); cr.stroke()
    for k in range(4): cr.move_to(-6 + k * 4, -10); cr.line_to(-4 + k * 3, -160); cr.stroke()
    cr.restore()

LAYERS = [(450, 'Shark-like scales', '상어 비늘 화석', '~450 Mya · 4억 5천만 년 전'), (420, 'Undisputed shark scales', '확실한 상어 비늘', '~420 Mya · 4억 2천만 년 전'),
          (385, 'First trees', '최초의 나무', '~385 Mya · 3억 8,500만 년 전'), (66, 'Dinosaurs gone', '공룡 멸종', '66 Mya · 6,600만 년 전'), (0.3, 'Humans', '인류', '~0.3 Mya · 30만 년 전')]
def sy(ma): return 1560 - (450 - ma) / 450 * 900

T_STRATA = (3.6, 11.4); T_SEA = 11.6; T_TREES = 15.8; T_CODA = 24.2

def draw(t):
    img = paper().copy(); s, cr = surf()
    # 첫 장면: 상어 대 나무
    a0 = 1 - ramp(t, 3.0, 3.6)
    if a0 > 0:
        shark(cr, 540, 760, 1.6 * back_out(ramp(t, 0.2, 0.8), 1.5), a0, t)
        tree(cr, 540, 1520, 1.3, a0, back_out(ramp(t, 0.6, 1.2), 1.4))
        txt(cr, '?', 860, 1180, 160, RED, a0 * ramp(t, 1.2, 1.5), fam=SERIF)
    # 지층 기둥
    if T_STRATA[0] - 0.4 < t < T_SEA + 0.4:
        fa = ramp(t, T_STRATA[0] - 0.4, T_STRATA[0]) * (1 - ramp(t, T_SEA - 0.2, T_SEA + 0.4))
        u = smooth(ramp(t, T_STRATA[0], T_STRATA[1] - 1.0))
        top = lerp(sy(450), sy(0), u)
        cr.save(); cr.rectangle(120, top, 220, sy(450) - top + 40); cr.clip()
        cr.set_source_rgba(*INKC, fa); cr.rectangle(120, 600, 220, 1000); cr.fill()
        cr.set_source_rgba(*PAPER, fa)
        for i in range(30):                                     # 층리 새김
            yy_ = 610 + i * 33 + 6 * math.sin(i * 1.7)
            cr.set_line_width(2 + (i % 3)); cr.move_to(120, yy_)
            for k in range(1, 12): cr.line_to(120 + k * 20, yy_ + 4 * math.sin(k * 0.9 + i))
            cr.stroke()
        cr.restore()
        for i, (ma, en, ko, sub) in enumerate(LAYERS):
            y = sy(ma); tp = T_STRATA[0] + 0.3 + i * 1.45; ly = [1530, 1330, 1130, 880, 660][i]
            if t < tp: continue
            b = fa * ramp(t, tp, tp + 0.35); col = RED if i == 2 else INKC
            cr.set_source_rgba(*col, b); cr.set_line_width(4); cr.move_to(340, y); cr.line_to(370, y); cr.line_to(400, ly); cr.line_to(420, ly); cr.stroke()
            cr.arc(340, y, 9, 0, 6.283); cr.fill()
            txt(cr, en, 440, ly - 22, 42, col, b, fam=SERIF, anchor='l', maxw=560); txt(cr, ko, 440, ly + 22, 38, col, b, anchor='l', maxw=560)
            txt(cr, sub, 440, ly + 62, 30, INKC, b * 0.8, fam=BOLD, anchor='l', maxw=560)
            if i == 0: shark(cr, 230, y - 16, 0.38, b, t)
            if i == 2: tree(cr, 230, y + 14, 0.3, b, 1)
        # 간격 괄호
        if t > T_STRATA[0] + 3.4:
            b = fa * ramp(t, T_STRATA[0] + 3.4, T_STRATA[0] + 3.8)
            cr.set_source_rgba(*RED, b); cr.set_line_width(5); x = 110
            cr.move_to(x + 10, sy(450)); cr.line_to(x, sy(450)); cr.line_to(x, sy(385)); cr.line_to(x + 10, sy(385)); cr.stroke()
    # 바다 장면: 나무 없는 땅
    if t >= T_SEA - 0.2:
        b = ramp(t, T_SEA - 0.2, T_SEA + 0.4)
        cr.save(); cr.rectangle(0, 1040, DW, DH); cr.clip(); cr.set_source_rgba(*INKC, b)
        hatch(cr, 0, 1040, DW, DH, gap=11, w=3, wob=6, t=t * 2); cr.restore()
        cr.set_source_rgba(*INKC, b); cr.move_to(0, 1040)
        for k in range(55): cr.line_to(k * 20, 1040 + 8 * math.sin(k * 0.8 + t * 2.5))
        cr.line_to(DW, 1030); cr.set_line_width(5); cr.stroke()
        cr.save(); cr.rectangle(0, 1046, DW, DH); cr.clip()
        cr.set_source_rgba(*PAPER, b); cr.rectangle(0, 1046, DW, DH); cr.fill(); cr.set_source_rgba(*INKC, b)
        hatch(cr, 0, 1046, DW, DH, gap=12, w=3.2, wob=8, t=t * 2.2); cr.restore()
        sx = lerp(-200, DW + 220, ((t - T_SEA) / 9.0) % 1.0)
        cr.save(); cr.rectangle(0, 1050, DW, DH); cr.clip()
        shark(cr, sx, 1420, 1.05, b, t, flip=True, halo=True); cr.restore()
        cr.set_source_rgba(*INKC, b); cr.move_to(0, 1010); cr.curve_to(300, 960, 700, 990, DW, 940); cr.line_to(DW, 1036); cr.line_to(0, 1036); cr.close_path(); cr.fill()
        r_ = np.random.default_rng(5)
        for k in range(40):                                     # 이끼만 있는 땅
            x = r_.uniform(20, DW - 20); y = 1000 - 40 * (x / DW) + r_.uniform(-6, 6)
            cr.arc(x, y, r_.uniform(5, 10), 3.14, 6.28); cr.fill()
        for k, x in enumerate((180, 420, 690, 900)):
            tree(cr, x, 996 - 40 * (x / DW), 0.95 - 0.1 * (k % 2), b, expo_out(ramp(t, T_TREES + 0.35 * k, T_TREES + 1.4 + 0.35 * k)))
        # 숫자판
        if t < T_CODA:
            a = b * (1 - ramp(t, T_TREES - 0.3, T_TREES))
            if a > 0:
                ma = lerp(450, 385, smooth(ramp(t, T_SEA + 0.6, T_TREES - 0.8)))
                cr.set_source_rgba(*INKC, a); cr.rectangle(0, 1760, DW, 160); cr.fill()
                txt(cr, f'{ma:.0f} million years ago', DW / 2, 1830, 50, PAPER, a, fam=SERIF)
                mi = int(round(ma)); txt(cr, f'{mi // 100}억 {(mi % 100) * 100:,}만 년 전 · 아직 나무가 없다', DW / 2, 1888, 40, PAPER, a)
    return over(img, s)

def sound(path):
    m = S.Mix(EP['DUR'], 450)
    m.put('amb', 0, S.drone([55.0, 82.4], EP['t_end'] + 1, 0.22, 'saw', vib=0.003))
    for i, (tt, f) in enumerate([(0.3, 110.0), (1.2, 130.8), (2.2, 98.0)]): m.put('mus', tt, S.drone([f], 1.8, 0.35, 'saw', vib=0.008))
    for i in range(5):
        tp = T_STRATA[0] + 0.3 + i * 1.45; m.put('fx', tp, S.kick(48, 0.55, 0.7)); m.put('mus', tp, S.drone([[73.4, 82.4, 98.0, 110.0, 123.5][i]], 1.6, 0.3, 'saw', vib=0.01))
    m.put('amb', T_SEA, S.rumble(EP['t_coda'] - T_SEA, 0.25)); m.put('fx', T_SEA, S.swoosh(1.2, 0.3, 120, 1500))
    m.put('amb', T_SEA, S.bubbles(EP['t_coda'] - T_SEA, 2, 0.12))
    for k in range(4): m.put('mus', T_TREES + 0.35 * k, S.drone([[146.8, 164.8, 196.0, 220.0][k]], 2.2, 0.28, 'saw', vib=0.006))
    tc = EP['t_coda']; m.put('mus', tc, S.drone([73.4, 110.0, 146.8], EP['t_end'] - tc, 0.4, 'saw', vib=0.005))
    for i in range(3): m.put('fx', tc + 0.8 + i * STEP, S.kick(44, 0.4, 0.9))
    m.put('mus', EP['t_end'] + 0.2, S.drone([98.0, 146.8], 2.6, 0.35, 'saw'))
    m.write(path, rev_mus=2.6, wet_mus=0.3)

EP = finalize(dict(t_coda=T_CODA, draw=draw, sound=sound, end_icon='mountain', grain=0.004,
    title_en_card='OLDER THAN TREES', title_ko_card='상어는 나무보다 먼저',
    pal=dict(hi=RED, endbg=PAPER),
    card_style=dict(box='line', ink=INKC, hi=RED, y=150, fe=SERIF, fk=BLK, se=58, sk=52, maxw=860, dx=30),
    cards=[(0.3, 3.2, ['Which came first:', 'sharks or *trees*?'], ['상어와 *나무*,', '누가 먼저일까?']),
           (3.8, 11.2, ['Shark-like scales: *~450 million* years.', 'First trees: *~385 million*.'], ['상어 비늘 화석 *약 4억 5천만 년*', '최초의 나무 *약 3억 8,500만 년*']),
           (11.8, 15.6, ['For tens of millions of years,', 'sharks swam past *treeless* land.'], ['수천만 년 동안 상어는', '*나무 한 그루 없는* 땅 곁을 헤엄쳤다']),
           (16.0, 20.0, ['Then came the first forests.'], ['그 뒤에야 첫 숲이 생겼다']),
           (20.2, 24.0, ['Sharks are still here —', 'they outlasted the *dinosaurs*.'], ['상어는 아직도 헤엄친다', '*공룡*보다 오래 살아남았다'])],
    coda=[('Long before the first forest,', '첫 숲이 생기기도 전에'), ('they were already swimming.', '그들은 이미 헤엄치고 있었다'), ('What endures quietly, lasts longest.', '묵묵히 견딘 것이 가장 오래 남는다')],
    coda_style=dict(dim=0.82, blur=8, tint=(0.94, 0.91, 0.84), ink=INKC, hi=RED, fe=SERIF, fk2=BLK),
    sources=['Natural History Museum (UK) shark timeline; Live Science, "Are sharks really older than trees?"', 'Earliest shark-like scales ~450 Mya (debated); undisputed ~420 Mya; first trees ~385 Mya.'],
    yt=dict(title_en='Sharks Are Older Than Trees #Shorts', title_ko='상어는 나무보다 먼저 지구에 있었다')))

if __name__ == '__main__': main(EP)
