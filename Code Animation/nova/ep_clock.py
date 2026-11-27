"""〈지구의 하루 중 인류는 6초〉 — 무성영화(흑백, 필름 결, 비네트, 세로 긁힘, 프레임 흔들림, 장식 테두리 자막), 소리는 래그타임 피아노와 영사기 소리.
계산: 지구 나이 약 45억 4천만 년(USGS)을 24시간으로 줄이면
- 공룡 멸종(약 6,600만 년 전) → 자정 약 21분 전(23:39)
- 호모 사피엔스(약 30만 년 전, Jebel Irhoud, Max Planck) → 자정 약 5.7초 전
- 문자 기록(약 5,000년 전) → 자정 약 0.1초 전 (모두 계산)
"""
import math, numpy as np, cv2, cairo
from base import *
import sfx as S

T_DINO = 4.2; T_HUMAN = 9.8; T_WRITE = 15.0; T_CODA = 20.6
_r = np.random.default_rng(454)
yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
VIG = (1 - 0.55 * np.clip(np.hypot((xx - W / 2) / (W * 0.62), (yy - H / 2) / (H * 0.6)), 0, 1) ** 2.2)[..., None]
GRAINS = [cv2.GaussianBlur(_r.normal(0, 1, (H, W)).astype(np.float32), (0, 0), 1.1) for _ in range(6)]
W_ = (0.93, 0.92, 0.88); G_ = (0.55, 0.55, 0.53); K_ = (0.08, 0.08, 0.08)

def clock(cr, cx, cy, R, hand_h, a=1.0, zoom_label=None):
    cr.set_source_rgba(*W_, a); cr.arc(cx, cy, R, 0, 6.283); cr.fill()
    cr.set_source_rgba(*K_, a); cr.set_line_width(10); cr.arc(cx, cy, R, 0, 6.283); cr.stroke()
    for k in range(24):
        q = -math.pi / 2 + k * 2 * math.pi / 24; L = 40 if k % 6 == 0 else 18
        cr.set_line_width(6 if k % 6 == 0 else 3)
        cr.move_to(cx + (R - 14) * math.cos(q), cy + (R - 14) * math.sin(q)); cr.line_to(cx + (R - 14 - L) * math.cos(q), cy + (R - 14 - L) * math.sin(q)); cr.stroke()
        if k % 6 == 0: txt(cr, f'{k:02d}', cx + (R - 90) * math.cos(q), cy + (R - 90) * math.sin(q) + 18, 52, K_, a, fam=SERIF)
    q = -math.pi / 2 + hand_h / 24 * 2 * math.pi
    cr.set_source_rgba(*K_, a); cr.set_line_width(12); cr.move_to(cx, cy); cr.line_to(cx + (R - 70) * math.cos(q), cy + (R - 70) * math.sin(q)); cr.stroke()
    cr.arc(cx, cy, 16, 0, 6.283); cr.fill()

def sliver(cr, cx, cy, R, h0, h1, col, a):
    q0 = -math.pi / 2 + h0 / 24 * 2 * math.pi; q1 = -math.pi / 2 + h1 / 24 * 2 * math.pi
    cr.set_source_rgba(*col, a); cr.move_to(cx, cy); cr.arc(cx, cy, R - 12, q0, q1); cr.close_path(); cr.fill()

def dino(cr, x, y, sc, a):
    cr.save(); cr.translate(x, y); cr.scale(sc, sc); cr.set_source_rgba(*K_, a)
    cr.move_to(-120, 0); cr.curve_to(-60, -60, 40, -70, 80, -40); cr.curve_to(110, -120, 120, -170, 150, -175)
    cr.curve_to(175, -175, 180, -150, 160, -140); cr.curve_to(140, -120, 120, -60, 110, -10); cr.curve_to(60, 20, -40, 20, -120, 0); cr.fill()
    for lx in (-20, 50): cr.rectangle(lx, 0, 22, 60); cr.fill()
    cr.restore()

def draw(t):
    s, cr = surf(); cr.set_source_rgb(*G_); cr.paint()
    jit = (_r_j[int(t * 12) % 64])
    cx, cy, R = 540 + jit[0], 1060 + jit[1], 380
    if t < T_DINO:
        a = 1 - ramp(t, T_DINO - 0.3, T_DINO)
        clock(cr, cx, cy, R, 24 * smooth(ramp(t, 0.4, 3.6)), a)
        txt(cr, '4,540,000,000 years = 24 h', 540, 1560, 50, W_, a, fam=SERIF)
    elif t < T_HUMAN:
        a = ramp(t, T_DINO, T_DINO + 0.3) * (1 - ramp(t, T_HUMAN - 0.3, T_HUMAN))
        clock(cr, cx, cy, R, 23.65, a)
        sliver(cr, cx, cy, R, 24 - 21 / 60 * ramp(t, T_DINO + 0.4, T_DINO + 1.6), 24, (0.30, 0.30, 0.30), a)
        dino(cr, 230, 1740, 0.9, a * ramp(t, T_DINO + 1.0, T_DINO + 1.6))
        txt(cr, '23:39', 760, 1600, 120, W_, a * ramp(t, T_DINO + 1.6, T_DINO + 2.0), fam=SERIF)
        txt(cr, 'dinosaurs gone · 공룡 멸종', 760, 1670, 36, W_, a * ramp(t, T_DINO + 1.6, T_DINO + 2.0), fam=SERIF)
    elif t < T_WRITE:                                                     # 마지막 1분을 확대
        a = ramp(t, T_HUMAN, T_HUMAN + 0.3) * (1 - ramp(t, T_WRITE - 0.3, T_WRITE))
        cr.set_source_rgba(*W_, a); cr.arc(cx, cy, R, 0, 6.283); cr.fill()
        cr.set_source_rgba(*K_, a); cr.set_line_width(10); cr.arc(cx, cy, R, 0, 6.283); cr.stroke()
        for k in range(60):
            q = -math.pi / 2 + k * 2 * math.pi / 60; L = 40 if k % 5 == 0 else 16; cr.set_line_width(5 if k % 5 == 0 else 2)
            cr.move_to(cx + (R - 14) * math.cos(q), cy + (R - 14) * math.sin(q)); cr.line_to(cx + (R - 14 - L) * math.cos(q), cy + (R - 14 - L) * math.sin(q)); cr.stroke()
        txt(cr, 'THE LAST MINUTE · 마지막 1분', 540, cy - R - 40, 42, W_, a, fam=SERIF)
        g = ramp(t, T_HUMAN + 0.6, T_HUMAN + 2.0)
        q0 = -math.pi / 2 - 5.7 / 60 * 2 * math.pi * g
        cr.set_source_rgba(0.25, 0.25, 0.25, a); cr.move_to(cx, cy); cr.arc(cx, cy, R - 12, q0, -math.pi / 2); cr.close_path(); cr.fill()
        txt(cr, '5.7 s', cx, cy + 90, 130, K_, a * ramp(t, T_HUMAN + 2.0, T_HUMAN + 2.4), fam=SERIF)
        txt(cr, 'Homo sapiens · 인류', cx, cy + 160, 40, K_, a * ramp(t, T_HUMAN + 2.0, T_HUMAN + 2.4), fam=SERIF)
        txt(cr, 'calculated · 계산', 540, 1590, 34, W_, a * ramp(t, T_HUMAN + 2.4, T_HUMAN + 2.8), fam=SERIF)
    else:                                                                 # 기록된 역사 0.1초
        a = ramp(t, T_WRITE, T_WRITE + 0.3) * (1 - ramp(t, T_CODA - 0.3, T_CODA))
        g = ramp(t, T_WRITE + 0.4, T_WRITE + 2.4)
        x0, x1, y = 120, 960, 1000
        cr.set_source_rgba(*W_, a); cr.rectangle(x0, y - 30, x1 - x0, 60); cr.fill()
        cr.set_source_rgba(*K_, a); cr.rectangle(x1 - (x1 - x0) * 0.1 / 5.7 * g - 2, y - 30, (x1 - x0) * 0.1 / 5.7 * g + 4, 60); cr.fill()
        txt(cr, '← 5.7 s of humans →', 540, y - 70, 40, W_, a, fam=SERIF)
        txt(cr, '0.1 s', x1, y + 120, 110, W_, a * ramp(t, T_WRITE + 2.0, T_WRITE + 2.4), fam=SERIF, anchor='r')
        txt(cr, 'all written history · 기록된 역사 전부', 540, y + 200, 38, W_, a * ramp(t, T_WRITE + 2.4, T_WRITE + 2.8), fam=SERIF)
    img = np.ascontiguousarray(arr(s)[..., :3])
    gray = img.mean(-1, keepdims=True)
    k = int(t * 12) % 6
    gray = gray * (1 + 0.10 * GRAINS[k][..., None]) * VIG * (0.97 + 0.03 * math.sin(t * 37))
    xs = _r_s[int(t * 12) % 64]
    for x in xs:
        if 0 <= x < W: gray[:, x:x + 2] *= 0.75
    return np.clip(np.repeat(gray, 3, -1) * np.array([0.96, 0.99, 1.02], np.float32)[::-1], 0, 1)
_r_j = [(float(_r.normal(0, 1.5)), float(_r.normal(0, 2.0))) for _ in range(64)]
_r_s = [[int(v) for v in _r.uniform(0, W, int(_r.integers(0, 3)))] for _ in range(64)]

def sound(path):
    m = S.Mix(EP['DUR'], 1906); tc = EP['t_coda']; b = 60 / 104
    bass = [130.8, 196.0, 110.0, 164.8, 146.8, 220.0, 98.0, 146.8]
    chords = [[261.6, 329.6, 392.0], [220.0, 261.6, 329.6], [293.7, 349.2, 440.0], [246.9, 293.7, 392.0]]
    mel = [523.3, 587.3, 659.3, 523.3, 784.0, 659.3, 587.3, 523.3, 440.0, 523.3, 587.3, 698.5, 659.3, 587.3, 523.3, 493.9]
    n = int((tc - 0.3) / (b / 2))
    for k in range(n):
        t = 0.2 + k * b / 2
        if k % 2 == 0: m.put('mus', t, S.piano(bass[(k // 2) % 8], 0.5, 0.26))
        else:
            for f in chords[(k // 4) % 4]: m.put('mus', t, S.piano(f, 0.35, 0.12))
        if k % 2 == 0 or k % 8 == 3: m.put('mus', t + (b / 4 if k % 4 == 3 else 0), S.piano(mel[(k // 2) % 16], 0.5, 0.2))
    m.put('amb', 0, S.static(EP['t_end'] + 1, 0.05, seed=3))
    for k in range(int(EP['t_end'] * 4)): m.put('amb', k / 4, S.tick(0.04, hi=(k % 2 == 0)))
    m.put('fx', T_DINO + 1.0, S.thunder(2.0, 0.2, seed=6)); m.put('fx', T_HUMAN + 2.0, S.bell(880.0, 2.0, 0.2))
    for i, f in enumerate([523.3, 392.0, 261.6]): m.put('mus', tc + 0.8 + i * STEP, S.piano(f, 2.6, 0.3))
    m.write(path, rev_mus=1.4, wet_mus=0.22)

EP = finalize(dict(t_coda=T_CODA, draw=draw, sound=sound, end_icon='star', grain=0.0,
    title_en_card='HUMANS: THE LAST 6 SECONDS', title_ko_card='지구의 하루 중 인류는 6초',
    pal=dict(hi=(0.30, 0.30, 0.30), endbg=(0.92, 0.91, 0.88)),
    card_style=dict(box='paper', bg=(0.10, 0.10, 0.10), ink=(0.94, 0.93, 0.90), hi=(0.98, 0.98, 0.98), y=180, fe=SERIF, fk=BLK),
    cards=[(0.3, 4.0, ['Squeeze Earth’s 4.54 billion years', 'into *one day*.'], ['지구의 45억 년을', '*하루*로 줄이면']),
           (4.2, 9.6, ['Dinosaurs vanish', 'at *23:39*.'], ['공룡은', '*밤 11시 39분*에 사라진다']),
           (9.8, 14.8, ['Humans appear in the last', '*5.7 seconds* before midnight.'], ['인류는 자정 전', '마지막 *5.7초*에 나타난다']),
           (15.0, 20.4, ['All written history:', 'the last *0.1 second*.'], ['기록된 역사 전부는', '마지막 *0.1초*'])],
    coda=[('We arrived in the last seconds', '우리는 마지막 몇 초에 왔다'), ('of a very long day.', '아주 긴 하루의'), ('Live your seconds well.', '주어진 몇 초를 잘 살자')],
    coda_style=dict(dim=0.5, blur=8, tint=(0.30, 0.30, 0.30), ink=(0.95, 0.94, 0.90), hi=(1.0, 1.0, 1.0), fe=SERIF),
    sources=['Earth ~4.54 billion years old (USGS); Homo sapiens ~300,000 years (Jebel Irhoud, Max Planck Society, 2017); non-avian dinosaur extinction ~66 million years ago; writing ~5,000 years ago.', 'Times on a 24-hour clock calculated: 66 Myr → ~21 min, 300 kyr → ~5.7 s, 5 kyr → ~0.1 s before midnight.'],
    yt=dict(title_en='If Earth Were One Day, Humans Showed Up 6 Seconds Ago #Shorts', title_ko='지구의 하루 중 인류는 마지막 6초')))

if __name__ == '__main__': main(EP)
