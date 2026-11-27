"""〈아기는 뼈가 더 많다〉 — 엑스레이 필름(검푸른 필름 바탕, 뼈만 희뿌옇게 빛나는 투과광, 필름 가장자리 번호·L 표식, 판독등 줄무늬), 소리는 유리 하프와 낮은 판독등 웅웅 소리.
사실: 신생아 뼈는 약 275~300개, 어른은 보통 206개. 자라면서 작은 뼈가 서로 붙는다(Cleveland Clinic; Britannica).
신생아는 큰 머리뼈 5개 사이에 숫구멍이 있다(Cleveland Clinic). 어른 뼈는 몸무게의 약 15%, 몸 칼슘의 약 99%를 저장(Healthline).
"""
import math, numpy as np, cv2, cairo
from base import *
import sfx as S

FILM = np.array((0.05, 0.09, 0.13)[::-1], np.float32); GLOW = np.array((0.80, 0.93, 1.0)[::-1], np.float32)
T_FUSE = 4.2; T_ADULT = 9.8; T_STORE = 15.2; T_CODA = 20.6
_r = np.random.default_rng(206)

def body_mask(cx, cy, sc):
    s, cr = surf(); cr.set_source_rgb(1, 1, 1)
    cr.save(); cr.translate(cx, cy); cr.scale(sc, sc)
    cr.arc(0, -330, 95, 0, 6.283); cr.fill()                                 # 머리
    cr.rectangle(-110, -230, 220, 330); cr.fill()                            # 몸통
    for sx in (-1, 1):
        cr.save(); cr.translate(sx * 125, -210); cr.rotate(sx * 0.18); cr.rectangle(-28, 0, 56, 330); cr.fill(); cr.restore()   # 팔
        cr.rectangle(sx * 60 - 34, 100, 68, 380); cr.fill()                  # 다리
    cr.restore()
    return arr(s)[..., 3] > 0.5

def sample(mask, n, seed):
    rr = np.random.default_rng(seed); ys, xs = np.where(mask)
    idx = rr.choice(len(xs), min(len(xs), n * 6), replace=False); pts = np.stack([xs[idx], ys[idx]], 1).astype(np.float32)
    keep = [pts[0]]
    for p in pts[1:]:                                                        # 고르게 퍼지게
        if len(keep) >= n: break
        if np.min(np.hypot(*(np.array(keep) - p).T)) > 16 * SC: keep.append(p)
    while len(keep) < n: keep.append(pts[rr.integers(len(pts))])
    return np.array(keep[:n]) / SC
M = body_mask(W // 2, int(1120 * SC), 1.05 * SC)
P300 = sample(M, 300, 1)
_order = _r.permutation(300); KEEP = np.sort(_order[:206]); GONE = np.sort(_order[206:])
TARGET = {}
for g in GONE:
    d = np.hypot(*(P300[KEEP] - P300[g]).T); TARGET[g] = KEEP[int(np.argmin(d))]
ANGS = _r.uniform(0, math.pi, 300)

def bone(cr, x, y, ang, L, a):
    cr.save(); cr.translate(x, y); cr.rotate(ang); cr.set_source_rgba(1, 1, 1, a)
    cr.rectangle(-L / 2, -3.5, L, 7); cr.fill()
    for e in (-L / 2, L / 2):
        cr.arc(e, -4, 5, 0, 6.283); cr.fill(); cr.arc(e, 4, 5, 0, 6.283); cr.fill()
    cr.restore()

def draw(t):
    s, cr = surf()
    f = smooth(ramp(t, T_FUSE + 0.4, T_FUSE + 4.0))                         # 붙는 정도
    if t < T_STORE:
        a = 1 - ramp(t, T_STORE - 0.3, T_STORE)
        grow = 0.78 + 0.22 * smooth(ramp(t, T_FUSE, T_ADULT))
        cx, cy = 540, 1120
        n_show = 300 if t >= 2.6 else int(300 * smooth(ramp(t, 0.4, 2.6)))
        for i in range(n_show):
            x, y = P300[i]
            if i in TARGET:
                tx, ty = P300[TARGET[i]]; x, y = x + (tx - x) * f, y + (ty - y) * f; ai = a * (1 - f * 0.95)
            else: ai = a
            x = cx + (x - cx) * grow; y = cy + (y - cy) * grow
            bone(cr, x, y, ANGS[i], 16 + 8 * f * (i not in TARGET), ai)
        count = int(300 - 94 * f) if t >= T_FUSE else n_show
        txt(cr, f'{count}', 900, 620, 110, (0.85, 0.95, 1.0), a, fam=BLK, anchor='r')
        txt(cr, 'bones · 뼈', 900, 670, 36, (0.75, 0.88, 1.0), a, fam=BOLD, anchor='r')
        txt(cr, 'NEWBORN' if t < T_ADULT else 'ADULT', 180, 620, 48, (0.75, 0.88, 1.0), a, fam=BLK, anchor='l')
    else:                                                                   # 몸무게 15%, 칼슘 99%
        a = ramp(t, T_STORE, T_STORE + 0.3) * (1 - ramp(t, T_CODA - 0.3, T_CODA))
        g = smooth(ramp(t, T_STORE + 0.4, T_STORE + 2.4))
        for i, (lab, v) in enumerate([('of body weight · 몸무게', 15), ('of body calcium · 몸속 칼슘', 99)]):
            y = 820 + i * 420; R = 150
            cr.set_source_rgba(1, 1, 1, 0.25 * a); cr.arc(300, y, R, 0, 6.283); cr.fill()
            cr.set_source_rgba(1, 1, 1, a); cr.move_to(300, y); cr.arc(300, y, R, -math.pi / 2, -math.pi / 2 + 6.283 * v / 100 * g); cr.close_path(); cr.fill()
            txt(cr, f'~{int(v * g)}%', 500, y + 20, 110, (0.85, 0.95, 1.0), a, fam=BLK, anchor='l')
            txt(cr, lab, 500, y + 80, 36, (0.75, 0.88, 1.0), a, fam=BOLD, anchor='l')
    lum = arr(s)[..., 3]
    glow = cv2.GaussianBlur(lum, (0, 0), 6 * SC) * 0.7 + cv2.GaussianBlur(lum, (0, 0), 1.2 * SC) * 0.8
    yy = np.linspace(0, 1, H, dtype=np.float32)[:, None]
    light = 0.9 + 0.1 * np.cos(yy * 6.283 * 3)                              # 판독등 줄
    img = FILM * light[..., None] + GLOW * np.clip(glow, 0, 1.2)[..., None]
    s2, c2 = surf()
    c2.set_source_rgba(0.9, 0.95, 1.0, 0.75); txt(c2, 'L', 140, 1780, 90, (0.92, 0.96, 1.0), 0.8, fam=BLK)
    txt(c2, '300 → 206 · AP VIEW', 940, 1790, 30, (0.7, 0.82, 0.92), 0.7, fam=BOLD, anchor='r')
    return over(np.clip(img, 0, 1), s2)

def sound(path):
    m = S.Mix(EP['DUR'], 206); tc = EP['t_coda']
    m.put('amb', 0, S.drone([60.0, 120.0], EP['t_end'] + 1, 0.06, 'sine'))
    notes = [523.3, 659.3, 784.0, 987.8, 784.0, 659.3, 587.3, 698.5, 880.0, 698.5, 587.3, 523.3]
    t = 0.4; k = 0
    while t < tc - 0.6:
        m.put('mus', t, S.glassharp(notes[k % len(notes)], 2.4, 0.18)); t += 0.85; k += 1
    for k in range(20): m.put('fx', T_FUSE + 0.4 + k * 3.6 / 20, S.tok(900 - 20 * k, 0.08))
    m.put('fx', T_ADULT, S.bell(659.3, 2.4, 0.2))
    for i, f in enumerate([784.0, 587.3, 392.0]): m.put('mus', tc + 0.8 + i * STEP, S.glassharp(f, 3.0, 0.25))
    m.write(path, rev_mus=3.0, wet_mus=0.45)

EP = finalize(dict(t_coda=T_CODA, draw=draw, sound=sound, end_icon='star', grain=0.0,
    title_en_card='BABIES HAVE MORE BONES', title_ko_card='아기는 뼈가 더 많다',
    pal=dict(hi=(0.20, 0.45, 0.70), endbg=(0.90, 0.95, 0.98)),
    card_style=dict(box='paper', bg=(0.92, 0.96, 0.99), ink=(0.05, 0.10, 0.16), hi=(0.15, 0.45, 0.75), y=180, fe=BOLD, fk=BLK),
    cards=[(0.3, 4.0, ['A newborn has about', '*300* bones.'], ['갓난아기의 뼈는', '약 *300개*']),
           (4.2, 9.6, ['As we grow,', 'small bones *fuse* together.'], ['자라면서', '작은 뼈들이 *서로 붙는다*']),
           (9.8, 15.0, ['An adult usually has', '*206* bones.'], ['어른의 뼈는', '보통 *206개*']),
           (15.2, 20.4, ['Bones are about *15%* of body weight', 'and hold *99%* of its calcium.'], ['뼈는 몸무게의 약 *15%*,', '몸속 칼슘의 *99%*를 품는다'])],
    coda=[('We grow by joining,', '우리는 이어지며 자란다'), ('not by adding more.', '더 많이 갖는 것이 아니라'), ('Let what is scattered in you become one.', '흩어진 나를 하나로 이어 가자')],
    coda_style=dict(dim=0.5, blur=8, tint=(0.10, 0.16, 0.22), ink=(0.92, 0.96, 1.0), hi=(0.70, 0.88, 1.0), fe=BOLD),
    sources=['Newborns have about 275–300 bones; most adults have 206, as small bones fuse while growing (Cleveland Clinic; Britannica).', 'Bones make up about 15% of body weight and store about 99% of the body’s calcium (Healthline). Bone dots are illustrative, not anatomical positions.'],
    yt=dict(title_en='Babies Have Almost 100 More Bones Than Adults #Shorts', title_ko='아기는 어른보다 뼈가 100개 가까이 많다')))

if __name__ == '__main__': main(EP)
