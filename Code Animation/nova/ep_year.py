"""〈지구 45억 년을 1년 달력에〉 다시 만들기 — 청사진(시아노타입: 프러시안 블루 바탕, 번지는 흰 제도선, 치수선·도면 글씨), 소리는 시계 초침과 낮은 피아노.
사실: 지구 나이 약 45억 4천만 년(USGS), 호모 사피엔스 약 30만 년(Hublin et al. 2017), 농사 약 1만 2천 년, 문자 약 5천 년(대략).
1년 = 365.25일 기준 환산: 공룡 멸종 12월 26일, 사피엔스 12월 31일 밤 11시 25분, 농사 마지막 83초, 문자 마지막 35초, 80년 인생 마지막 0.56초.
"""
import math, numpy as np, cv2, cairo
from base import *
import sfx as S

EAGE = 4.54e9; YMIN = 365.25 * 24 * 60; YSEC = YMIN * 60
SAP = 60 - 300000 / EAGE * YMIN; FARM = 60 - 12000 / EAGE * YMIN; WRIT = 60 - 5000 / EAGE * YSEC; LIFE = 60 - 80 / EAGE * YSEC
DINO = (1 - 66e6 / EAGE) * 12
MON = ['JAN', 'FEB', 'MAR', 'APR', 'MAY', 'JUN', 'JUL', 'AUG', 'SEP', 'OCT', 'NOV', 'DEC']
LV = [dict(c=3, r=4, n=12, lab=MON, t=(0.0, 9.0), fill=(0.8, 7.6), ten='4.54 BILLION YEARS = 1 YEAR', tko='45억 4천만 년 = 1년',
           pins=[(0.03, 'Earth forms · 지구 탄생', 'JAN 1'), (DINO, 'Dinosaurs gone · 공룡 멸종', 'DEC 26')]),
      dict(c=4, r=6, n=24, lab=[f'{h:02d}h' for h in range(24)], t=(9.0, 15.0), fill=(9.9, 13.0), ten='DECEMBER 31', tko='12월 31일',
           pins=[(23 + SAP / 60, 'Homo sapiens · 호모 사피엔스', '11:25 PM')]),
      dict(c=6, r=10, n=60, lab=[f':{m:02d}' for m in range(60)], t=(15.0, 21.0), fill=(15.9, 19.8), ten='11 PM → MIDNIGHT', tko='밤 11시 → 자정',
           pins=[(SAP, 'Homo sapiens · 사피엔스', '23:25'), (FARM, 'Farming · 농사', '23:58:37')]),
      dict(c=6, r=10, n=60, lab=[f'{s}s' for s in range(60)], t=(21.0, 29.0), fill=(21.9, 26.0), ten='THE LAST MINUTE', tko='마지막 1분',
           pins=[(WRIT, 'Writing · 문자', '−35 s'), (LIFE, 'Your 80 years · 나의 80년', '−0.56 s')])]
BX0, BY0, BX1, BY1 = 90, 610, 990, 1450
T_CODA = 29.2
WH = (0.93, 0.96, 1.0)

_r = np.random.default_rng(19)
def _cyan():
    g = sum(cv2.resize(_r.standard_normal((max(2, H // d), max(2, W // d))).astype(np.float32), (W, H), interpolation=cv2.INTER_CUBIC) * w for d, w in ((2, 0.3), (12, 0.5), (80, 1.0), (300, 1.2)))
    g = (g - g.min()) / (g.max() - g.min())
    b = np.stack([0.50 + 0.12 * g, 0.24 + 0.08 * g, 0.07 + 0.04 * g], -1)       # BGR 프러시안 블루
    return b.astype(np.float32)
CYAN = _cyan()

def grid_lines(cr, a):
    cr.set_source_rgba(*WH, 0.07 * a); cr.set_line_width(1)
    for x in range(0, DW, 30): cr.move_to(x, 0); cr.line_to(x, DH)
    for y in range(0, DH, 30): cr.move_to(0, y); cr.line_to(DW, y)
    cr.stroke()

def cell_rect(L, i, box):
    x0, y0, x1, y1 = box; c, r = L['c'], L['r']; w, h = (x1 - x0) / c, (y1 - y0) / r
    return x0 + (i % c) * w, y0 + (i // c) * h, w, h

def level(cr, L, box, a, fillv, t, show_pins=True):
    if a <= 0: return
    x0, y0, x1, y1 = box; sc = (x1 - x0) / (BX1 - BX0)
    cr.set_line_width(max(1, 2.2 * min(1, sc))); cr.set_source_rgba(*WH, 0.9 * a)
    for i in range(L['n']):
        cx, cy, w, h = cell_rect(L, i, box)
        f = np.clip(fillv - i, 0, 1)
        if f > 0:                                          # 지나간 시간: 빗금
            cr.set_source_rgba(*WH, 0.16 * a); cr.rectangle(cx + 3 * sc, cy + 3 * sc, (w - 6 * sc) * f, h - 6 * sc); cr.fill()
            cr.save(); cr.rectangle(cx, cy, w * f, h); cr.clip(); cr.set_source_rgba(*WH, 0.45 * a); cr.set_line_width(max(1, 1.4 * min(1, sc)))
            for k in range(-int(h / 9) - 2, int(w / 9) + 2): cr.move_to(cx + k * 9 * max(sc, 0.2), cy); cr.line_to(cx + k * 9 * max(sc, 0.2) + h, cy + h)
            cr.stroke(); cr.restore(); cr.set_source_rgba(*WH, 0.9 * a); cr.set_line_width(max(1, 2.2 * min(1, sc)))
        cr.rectangle(cx + 3 * sc, cy + 3 * sc, w - 6 * sc, h - 6 * sc); cr.stroke()
        if sc > 0.4:
            fs = min(w, h) * (0.24 if L['n'] <= 24 else 0.28)
            txt(cr, L['lab'][i], cx + 10 * sc, cy + fs + 8 * sc, fs, WH, 0.85 * a, fam=BOLD, anchor='l')
    if show_pins:
        for (p, lab, when) in L['pins']:
            pa = a * ramp(fillv, p, p + 0.4)
            if pa <= 0: continue
            i = min(L['n'] - 1, int(p)); cx, cy, w, h = cell_rect(L, i, box); px = cx + w * (p - i); py = cy + h * 0.62
            cr.set_source_rgba(*WH, pa); cr.arc(px, py, 9, 0, 6.283); cr.fill()
            ly = BY1 + 80 + 115 * L['pins'].index((p, lab, when))
            cr.set_line_width(2); cr.move_to(px, py); cr.line_to(px, ly - 50); cr.line_to(540, ly - 50); cr.stroke()
            txt(cr, lab, 540, ly, 42, WH, pa, fam=BLK); txt(cr, when, 540, ly + 50, 36, (0.75, 0.88, 1.0), pa, fam=BOLD)

def draw(t):
    s, cr = surf(); grid_lines(cr, 1)
    li = 0
    for k, L in enumerate(LV):
        if t >= L['t'][0]: li = k
    L = LV[li]; fillv = L['n'] * ramp(t, *L['fill'])
    zt = ramp(t, L['t'][1] - 0.9, L['t'][1]) if li < 3 else 0
    if zt > 0:                                              # 마지막 칸이 커지며 다음 달력이 된다
        u = smooth(zt); cx, cy, w, h = cell_rect(L, L['n'] - 1, (BX0, BY0, BX1, BY1))
        fx0 = lerp(BX0, BX0 - (cx - BX0) * (BX1 - BX0) / w, u); fy0 = lerp(BY0, BY0 - (cy - BY0) * (BY1 - BY0) / h, u)
        k = lerp(1, (BX1 - BX0) / w, u); ky = lerp(1, (BY1 - BY0) / h, u)
        cr.save(); cr.rectangle(BX0 - 4, BY0 - 4, BX1 - BX0 + 8, BY1 - BY0 + 8); cr.clip()
        level(cr, L, (fx0, fy0, fx0 + (BX1 - BX0) * k, fy0 + (BY1 - BY0) * ky), 1, fillv, t, show_pins=False)
        nx0, ny0 = lerp(cx, BX0, u), lerp(cy, BY0, u); nx1, ny1 = lerp(cx + w, BX1, u), lerp(cy + h, BY1, u)
        level(cr, LV[li + 1], (nx0, ny0, nx1, ny1), ramp(zt, 0.3, 1), 0, t, show_pins=False)
        cr.restore()
    else:
        level(cr, L, (BX0, BY0, BX1, BY1), ramp(t, L['t'][0], L['t'][0] + 0.3) if li > 0 else ramp(t, 0.1, 0.6), fillv, t)
    # 도면 표제란
    ta = 1 - zt
    cr.set_line_width(2); cr.set_source_rgba(*WH, 0.8); cr.rectangle(BX0, BY0 - 92, BX1 - BX0, 70); cr.stroke()
    txt(cr, L['ten'], BX0 + 20, BY0 - 46, 34, WH, ta, fam=BLK, anchor='l'); txt(cr, L['tko'], BX1 - 20, BY0 - 46, 32, WH, ta, fam=BOLD, anchor='r')
    # 치수선(바깥 눈금)
    cr.set_line_width(1.5); cr.set_source_rgba(*WH, 0.6)
    cr.move_to(BX0 - 30, BY0); cr.line_to(BX0 - 30, BY1); cr.stroke()
    for yy in (BY0, BY1): cr.move_to(BX0 - 42, yy); cr.line_to(BX0 - 18, yy); cr.stroke()
    if li == 3:
        la = ramp(t, 26.2, 26.8)
        if la > 0:                                          # 마지막 0.56초를 크게 표시
            cx, cy, w, h = cell_rect(L, 59, (BX0, BY0, BX1, BY1))
            cr.set_source_rgba(1.0, 0.92, 0.55, la); cr.rectangle(cx + w * (1 - 0.556), cy + 3, w * 0.556 - 3, h - 6); cr.fill()
            cr.set_line_width(3); cr.arc(cx + w * 0.72, cy + h * 0.5, max(w, h) * 0.75, 0, 6.283); cr.stroke()
    img = CYAN * 1.0
    a = arr(s)
    glow = cv2.GaussianBlur(a, (0, 0), 1.6 * SC)                # 감광액 번짐
    a = np.maximum(a, glow * 0.8)
    return img * (1 - a[..., 3:4]) + a[..., :3]

def sound(path):
    m = S.Mix(EP['DUR'], 101); tc = EP['t_coda']
    t = 0.0; k = 0
    while t < tc - 0.3:
        m.put('fx', t, S.tick(0.35, k % 2 == 0)); t += 0.5; k += 1
    notes = [(0.5, 146.8), (2.5, 220.0), (4.5, 196.0), (6.5, 174.6), (9.8, 130.8), (11.8, 196.0), (15.8, 146.8), (17.8, 220.0), (21.8, 110.0), (23.8, 164.8)]
    for tt, f in notes: m.put('mus', tt, S.piano(f, 3.2, 0.42)); m.put('mus', tt + 0.02, S.piano(f * 1.5, 3.0, 0.2))
    for L in LV[:3]: m.put('fx', L['t'][1] - 0.9, S.swoosh(0.9, 0.45, 200, 4000, seed=int(L['t'][1])))
    for L in LV:
        for p, *_ in L['pins']:
            tp = L['fill'][0] + (L['fill'][1] - L['fill'][0]) * p / L['n']
            m.put('fx', tp, S.bell(1046.5 if p > L['n'] - 2 else 784.0, 2.4, 0.3))
    m.put('fx', 26.3, S.ping(1568, 0.5, 2.5))
    m.put('amb', tc, S.drone([110.0, 164.8, 220.0], EP['t_end'] - tc, 0.18, 'sine'))
    for i, ch in enumerate([[220.0, 329.6, 440.0], [196.0, 293.7, 392.0], [174.6, 261.6, 349.2]]):
        for j, f in enumerate(ch): m.put('mus', tc + 0.8 + i * STEP + j * 0.05, S.piano(f, 3.2, 0.3))
    m.write(path, rev_mus=2.8, wet_mus=0.35)

EP = finalize(dict(t_coda=T_CODA, draw=draw, sound=sound, end_icon='calendar', grain=0.0,
    title_en_card="EARTH'S HISTORY IN ONE YEAR", title_ko_card='지구 45억 년을 1년 달력에',
    pal=dict(hi=(0.10, 0.25, 0.50), endbg=(0.93, 0.96, 1.0)),
    card_style=dict(box=None, ink=WH, hi=(1.0, 0.90, 0.55), y=150, fe=BLK, fk=BLK),
    cards=[(0.3, 3.8, ["Squeeze Earth's *4.54 billion years*", 'into one calendar year.'], ['지구 *45억 4천만 년*을', '1년 달력에 넣으면']),
           (9.2, 14.8, ['Humans appear on', '*Dec 31, 11:25 PM*.'], ['인류는 *12월 31일*', '*밤 11시 25분*에 등장']),
           (15.2, 20.8, ['Farming: the last *83 seconds*.'], ['농사는 마지막 *83초*']),
           (21.2, 26.4, ['Writing: the last *35 seconds*.'], ['문자는 마지막 *35초*']),
           (26.6, 29.0, ['Your whole life:', '*half a second*.'], ['나의 80년 인생은', '*0.56초*'])],
    coda=[("Half a second", "1년 중 0.56초"), ("out of a whole year.", "그것이 우리의 한평생"), ("Life is short. Spend it on what matters.", "삶은 짧다, 소중한 것에 쓰자")],
    coda_style=dict(dim=0.55, blur=10, tint=(0.05, 0.15, 0.32), ink=WH, hi=(1.0, 0.90, 0.55)),
    sources=['USGS: Earth ≈ 4.54 billion years old. Hublin et al., Nature 2017: Homo sapiens ≈ 300,000 years.', 'Farming ≈ 12,000 and writing ≈ 5,000 years ago (approximate).'],
    yt=dict(title_en='Earth’s History in One Year: Your Life Is Half a Second #Shorts', title_ko='지구 45억 년을 1년으로: 내 인생은 0.56초')))

if __name__ == '__main__': main(EP)
