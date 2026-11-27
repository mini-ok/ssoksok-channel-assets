"""〈나무 3조 그루〉 — 십자수(리넨 바탕, X자 실땀, 실 광택, 뜯긴 자리 바늘구멍), 소리는 나무피리와 새소리.
사실(Crowther et al., Nature 2015, Yale): 지구의 나무 약 3조 400억 그루, 한 사람에 약 422그루(당시 인구 72억 기준).
해마다 약 150억 그루 줄어듦(1인당 약 2그루). 농경 시작 뒤 나무 수가 약 46% 줄었다.
"""
import math, numpy as np, cv2, cairo
from base import *
import sfx as S

CELL = 12; GC, GR = DW // CELL, DH // CELL
GREEN = (0.20, 0.52, 0.30); GREEN2 = (0.35, 0.65, 0.32); TRUNK = (0.45, 0.28, 0.16); RED = (0.75, 0.18, 0.18); THREAD = (0.25, 0.18, 0.14)
T_MANY = 3.8; T_EACH = 8.8; T_LOSS = 13.6; T_CODA = 18.8

def _linen():
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32) / SC
    w = 0.5 + 0.25 * np.sin(xx * 2.1) * np.sin(yy * 0.3) + 0.25 * np.sin(yy * 2.1) * np.sin(xx * 0.27)
    r = np.random.default_rng(2); n = cv2.GaussianBlur(r.random((H, W)).astype(np.float32), (0, 0), 1.2 * SC)
    base = np.array((0.72, 0.84, 0.90), np.float32)                       # BGR 리넨
    return base * (0.9 + 0.08 * w[..., None] + 0.06 * n[..., None])
LINEN = _linen()

def _stitch():
    c = int(round(CELL * SC)); yy, xx = np.mgrid[0:c, 0:c].astype(np.float32) / c
    d1 = np.abs(xx - yy) / math.sqrt(2); d2 = np.abs(xx + yy - 1) / math.sqrt(2)
    w = 0.16
    m1 = np.clip((w - d1) / 0.04, 0, 1); m2 = np.clip((w - d2) / 0.04, 0, 1)
    edge = np.clip(1 - np.minimum(xx, 1 - xx) * 8, 0, 1) * np.clip(1 - np.minimum(yy, 1 - yy) * 8, 0, 1)
    m = np.maximum(m1, m2) * (1 - 0.6 * edge)
    shade = 0.75 + 0.35 * np.maximum((1 - d2 / w) * m2, 0.6 * (1 - d1 / w) * m1)          # 위에 놓인 실이 더 밝다
    hole = np.exp(-((np.minimum(xx, 1 - xx) ** 2 + np.minimum(yy, 1 - yy) ** 2) / 0.004)) * 0.0
    return m, shade, c
SM, SS, CPX = _stitch()
NY, NX = int(math.ceil(H / CPX)) + 1, int(math.ceil(W / CPX)) + 1
TILE_M = np.tile(SM, (NY, NX))[:H, :W]; TILE_S = np.tile(SS, (NY, NX))[:H, :W]
_r = np.random.default_rng(6)
CVAR = _r.uniform(0.9, 1.08, (NY, NX)).astype(np.float32)

def tree(cr, x, y, s, col=GREEN, a=1.0):
    cr.set_source_rgba(*TRUNK, a); cr.rectangle(x - s * 0.12, y - s * 0.35, s * 0.24, s * 0.35); cr.fill()
    cr.set_source_rgba(*col, a); cr.move_to(x, y - s * 1.35); cr.line_to(x + s * 0.5, y - s * 0.3); cr.line_to(x - s * 0.5, y - s * 0.3); cr.close_path(); cr.fill()

def person(cr, x, y, s, a):
    cr.set_source_rgba(*RED, a); cr.arc(x, y - s * 0.85, s * 0.16, 0, 6.283); cr.fill(); cr.rectangle(x - s * 0.2, y - s * 0.65, s * 0.4, s * 0.65); cr.fill()

TREES = [(1 + (i % 22) * 4, 50 + (i // 22) * 4) for i in range(422)]          # 칸 좌표
GONE = set(np.random.default_rng(8).permutation(422)[:194].tolist()); GONE_ORDER = {k: j for j, k in enumerate(np.random.default_rng(8).permutation(422)[:194].tolist())}
LOST = [3, 47, 120, 205, 300, 388, 61, 170, 240, 333, 410, 15]

def scene(t):
    s, cr = surf()
    a1 = 1 - ramp(t, T_MANY - 0.3, T_MANY)
    if a1 > 0:                                                 # 한 그루를 수놓는다
        tree(cr, 540, 1350, 520 * smooth(ramp(t, 0.2, 2.6)) + 1, GREEN, a1)
    am = ramp(t, T_MANY - 0.2, T_MANY + 0.3) * (1 - ramp(t, T_EACH - 0.3, T_EACH))
    if am > 0:                                                 # 숲: 점점 빽빽해진다
        r = np.random.default_rng(3); n = int(900 * smooth(ramp(t, T_MANY, T_MANY + 3.5)))
        pts = np.c_[r.uniform(60, 1020, 900), r.uniform(560, 1560, 900)]
        for x, y in sorted(pts[:n].tolist(), key=lambda p: p[1]): tree(cr, x, y, r.uniform(26, 44), GREEN if r.random() < 0.6 else GREEN2, am)
    ae = ramp(t, T_EACH - 0.2, T_EACH + 0.3)
    if ae > 0:
        person(cr, 540, 590, 120, ae)
        n = 422 * smooth(ramp(t, T_EACH + 0.3, T_EACH + 3.6))
        loss = smooth(ramp(t, T_LOSS + 1.6, T_LOSS + 4.2))
        for i, (x, y) in enumerate(TREES):
            if i >= n: break
            gone = i in GONE and loss * 194 > GONE_ORDER[i]
            if gone: continue                                  # 뽑힌 땀(약 46%)
            c = GREEN if i % 3 else GREEN2
            for dx, dy, cc in ((1, 0, c), (0, 1, c), (1, 1, c), (2, 1, c), (1, 2, TRUNK)):
                cr.set_source_rgba(*cc, ae); cr.rectangle((x + dx) * CELL + 1, (y + dy) * CELL + 1, CELL - 2, CELL - 2); cr.fill()
    return s

def draw(t):
    s = scene(t)
    a = arr(s)                                                 # 칸마다 평균색
    small = cv2.resize(a, (GC, GR), interpolation=cv2.INTER_AREA)
    rgb = small[..., :3] / np.maximum(small[..., 3:4], 1e-4); al = np.clip((small[..., 3] - 0.35) * 4, 0, 1)
    up_c = cv2.resize(rgb, (W, H), interpolation=cv2.INTER_NEAREST); up_a = cv2.resize(al, (W, H), interpolation=cv2.INTER_NEAREST)
    var = cv2.resize(CVAR, (NX * CPX, NY * CPX), interpolation=cv2.INTER_NEAREST)[:H, :W]
    cov = (TILE_M * up_a)[..., None]
    img = LINEN * (1 - cov * 0.97) + up_c * TILE_S[..., None] * var[..., None] * cov
    sh = cv2.GaussianBlur(cov[..., 0], (0, 0), 1.5 * SC)[..., None]                     # 실 그림자
    img = img * (1 - 0.18 * np.clip(sh - cov, 0, 1))
    s2, c2 = surf()
    ink = (0.25, 0.18, 0.14)
    if T_MANY < t < T_EACH:
        a2 = ramp(t, T_MANY + 0.3, T_MANY + 0.8) * (1 - ramp(t, T_EACH - 0.3, T_EACH)); n = 3.04 * smooth(ramp(t, T_MANY, T_MANY + 3.5))
        txt(c2, f'{n:.2f} trillion', 540, 1700, 84, ink, a2, fam=BLK); txt(c2, f'{n:.2f}조 그루', 540, 1790, 56, ink, a2, fam=BLK)
    if t > T_EACH:
        a3 = ramp(t, T_EACH + 0.4, T_EACH + 0.8) * (1 - ramp(t, T_CODA - 0.4, T_CODA))
        txt(c2, 'you · 나', 590, 545, 44, RED, a3, fam=BLK, anchor='l')
        if t < T_LOSS + 1.4: txt(c2, f'{min(422, int(422 * smooth(ramp(t, T_EACH + 0.3, T_EACH + 3.6))))} trees · 그루', 540, 1700, 64, ink, a3, fam=BLK)
        else:
            la = ramp(t, T_LOSS + 1.6, T_LOSS + 2.2) * a3
            txt(c2, '≈ 46% gone since farming began', 540, 1700, 48, RED, la, fam=BLK); txt(c2, '농사가 시작된 뒤 약 46%가 사라졌다', 540, 1770, 44, RED, la, fam=BLK)
    return over(img, s2)

def sound(path):
    m = S.Mix(EP['DUR'], 141); tc = EP['t_coda']
    r = np.random.default_rng(5)
    for t in np.arange(0.5, tc, 1.3): m.put('amb', t + r.uniform(0, 0.8), S.bird(0.18, int(t * 10)))
    mel = [(0.4, 587.3, 1.0), (1.4, 659.3, 0.6), (2.0, 784.0, 1.4), (3.8, 880.0, 0.8), (4.6, 784.0, 0.6), (5.2, 659.3, 1.6), (7.2, 587.3, 0.6), (7.8, 523.3, 0.6),
           (8.6, 587.3, 2.0), (11.0, 784.0, 0.8), (11.8, 880.0, 0.6), (12.4, 987.8, 1.4), (14.2, 880.0, 1.0), (15.2, 784.0, 0.8), (16.0, 659.3, 2.2)]
    for st, f, d in mel: m.put('mus', st, S.woodflute(f, d + 0.3, 0.32, seed=int(st)))
    for t in np.arange(0.4, tc, 2.4): m.put('mus', t, S.koto(196.0 if int(t / 2.4) % 2 == 0 else 220.0, 2.4, 0.18, seed=int(t)))
    for k in range(10): m.put('fx', T_LOSS + 1.7 + k * 0.25, S.tok(300 + 20 * k, 0.12))
    m.put('amb', tc, S.drone([146.8, 220.0, 293.7], EP['t_end'] - tc, 0.15, 'sine'))
    for i, f in enumerate([587.3, 523.3, 440.0]): m.put('mus', tc + 0.8 + i * STEP, S.woodflute(f, 2.4, 0.3, seed=i))
    m.write(path, rev_mus=2.6, wet_mus=0.35)

EP = finalize(dict(t_coda=T_CODA, draw=draw, sound=sound, end_icon='tree', grain=0.0,
    title_en_card='422 TREES EACH', title_ko_card='한 사람에 나무 422그루',
    pal=dict(hi=GREEN, endbg=(0.92, 0.87, 0.75)),
    card_style=dict(box=None, ink=(0.22, 0.16, 0.12), hi=(0.18, 0.48, 0.26), y=150, fe=BLK, fk=BLK),
    cards=[(0.3, 3.6, ['How many trees', 'are there on Earth?'], ['지구에 나무는', '몇 그루나 있을까?']),
           (3.8, 8.6, ['About *3 trillion*,', 'more than stars in our galaxy.'], ['약 *3조* 그루,', '우리 은하의 별보다 많다']),
           (8.8, 13.4, ['That is *422 trees*', 'for every person.'], ['한 사람에', '*422그루*씩']),
           (13.6, 18.6, ['But we lose about *15 billion* a year,', '*two* for each of us.'], ['그런데 해마다 *150억* 그루,', '한 사람에 *두 그루*씩 사라진다'])],
    coda=[('Four hundred trees for each of us,', '한 사람에 나무 422그루'), ('and two of them gone every year.', '해마다 그중 두 그루가 사라진다'), ('Plant a tree whose shade you’ll never sit in.', '그늘에 앉지 못할 나무도 심자')],
    coda_style=dict(dim=0.65, blur=10, tint=(0.92, 0.87, 0.75), ink=(0.22, 0.16, 0.12), hi=(0.18, 0.48, 0.26)),
    sources=['Crowther et al., Nature 525, 201–205 (2015): ~3.04 trillion trees, ~422 per person; ~15 billion lost each year; ~46% fewer since the start of agriculture.', 'Nature news: more trees than stars in the Milky Way.'],
    yt=dict(title_en='There Are 422 Trees for Every Person on Earth #Shorts', title_ko='지구의 나무, 한 사람에 422그루')))

if __name__ == '__main__': main(EP)
