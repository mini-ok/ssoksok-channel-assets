"""〈하루에 91cm〉 — 스위스 국제주의 포스터(엄격한 격자, 굵은 산세리프, 빨강·검정·흰색, 비대칭 배치), 소리는 미니멀 테크노(킥·하이햇·사인 베이스).
사실: 어떤 대나무 종은 하루 최대 91 cm 자란다(Guinness World Records). 시간당 약 3.8 cm(계산).
새 순이 땅 위로 나오기 전, 땅속 뿌리줄기 망이 몇 달에서 몇 해 동안 양분을 모은다(Bambu Batu). 열대에서 기록된 가장 큰 대나무 약 40 m(Guinness).
"""
import math, numpy as np, cv2, cairo
from base import *
import sfx as S

PAPERW = (0.95, 0.94, 0.91); REDS = (0.89, 0.12, 0.10); INKS = (0.08, 0.08, 0.08); GREENS = (0.10, 0.50, 0.30)
T_HOUR = 4.2; T_TALL = 9.6; T_ROOT = 15.0; T_CODA = 20.6
BPM = 124; B = 60 / BPM

def grid(cr):
    cr.set_source_rgba(*INKS, 0.08); cr.set_line_width(1)
    for k in range(1, 6): cr.move_to(k * 180, 0); cr.line_to(k * 180, 1920); cr.stroke()
    for k in range(1, 12): cr.move_to(0, k * 160); cr.line_to(1080, k * 160); cr.stroke()

def culm(cr, x, y0, h, w, col, a=1.0):
    cr.set_source_rgba(*col, a); cr.rectangle(x - w / 2, y0 - h, w, h); cr.fill()
    seg = 120
    for k in range(int(h // seg)):
        cr.set_source_rgba(*PAPERW, a); cr.rectangle(x - w / 2, y0 - (k + 1) * seg, w, 6); cr.fill()

def draw(t):
    s, cr = surf(); cr.set_source_rgb(*PAPERW); cr.paint(); grid(cr)
    beat = (t / B) % 1; pulse = math.exp(-beat * 6)
    if t < T_HOUR:
        a = 1 - ramp(t, T_HOUR - 0.3, T_HOUR)
        h = 1120 * smooth(ramp(t, 0.2, 3.4))
        culm(cr, 810, 1800, h, 90, GREENS, a)
        cr.set_source_rgba(*REDS, a); cr.rectangle(0, 1800, 1080, 120); cr.fill()
        txt(cr, '91', 90, 1240, 380, INKS, a * ramp(t, 0.6, 1.0), fam=BLK, anchor='l')
        txt(cr, 'cm / day', 100, 1360, 80, REDS, a * ramp(t, 1.0, 1.4), fam=BLK, anchor='l')
        txt(cr, 'HARI · 하루', 100, 1440, 40, INKS, a * ramp(t, 1.4, 1.8) * 0, fam=BOLD, anchor='l')
        for k in range(10):                                                 # 눈금 자
            y = 1800 - k * 112; cr.set_source_rgba(*INKS, a); cr.rectangle(900, y - 3, 40 if k % 5 == 0 else 22, 3); cr.fill()
    elif t < T_TALL:                                                        # 시계 한 바퀴 = 3.8 cm
        a = ramp(t, T_HOUR, T_HOUR + 0.3) * (1 - ramp(t, T_TALL - 0.3, T_TALL))
        cx, cy, R = 380, 1100, 250
        cr.set_source_rgba(*INKS, a); cr.arc(cx, cy, R, 0, 6.283); cr.fill()
        ph = smooth(ramp(t, T_HOUR + 0.5, T_TALL - 1.0))
        cr.set_source_rgba(*REDS, a); cr.move_to(cx, cy); cr.arc(cx, cy, R, -math.pi / 2, -math.pi / 2 + 6.283 * ph); cr.close_path(); cr.fill()
        for k in range(12):
            q = k * math.pi / 6; cr.set_source_rgba(*PAPERW, a); cr.set_line_width(6)
            cr.move_to(cx + (R - 30) * math.cos(q), cy + (R - 30) * math.sin(q)); cr.line_to(cx + (R - 6) * math.cos(q), cy + (R - 6) * math.sin(q)); cr.stroke()
        txt(cr, '1 h', cx, cy + 30, 110, PAPERW, a, fam=BLK)
        h = 600 + 380 * ph
        culm(cr, 850, 1800, h, 90, GREENS, a)
        cr.set_source_rgba(*REDS, a); cr.rectangle(780, 1800 - h - 6, 140, 12); cr.fill()
        txt(cr, '+3.8 cm', 780, 1800 - h + 10, 56, REDS, a * ramp(t, T_HOUR + 1.0, T_HOUR + 1.4), fam=BLK, anchor='r')
        txt(cr, 'calculated · 계산', 780, 1800 - h + 56, 28, INKS, a * ramp(t, T_HOUR + 1.0, T_HOUR + 1.4), fam=BOLD, anchor='r')
    elif t < T_ROOT:                                                        # 40 m 기록, 건물과 나란히
        a = ramp(t, T_TALL, T_TALL + 0.3) * (1 - ramp(t, T_ROOT - 0.3, T_ROOT))
        sc = 1060 / 40; g = smooth(ramp(t, T_TALL + 0.4, T_TALL + 2.6))
        culm(cr, 300, 1800, 40 * sc * g, 70, GREENS, a)
        cr.set_source_rgba(*INKS, a); cr.rectangle(560, 1800 - 13 * 3.0 * sc, 220, 13 * 3.0 * sc); cr.fill()   # 13층 ≈ 39 m(층 3 m 가정)
        for r_ in range(13):
            for c_ in range(3):
                cr.set_source_rgba(*PAPERW, a); cr.rectangle(585 + c_ * 65, 1800 - (r_ + 1) * 3.0 * sc + 25, 40, 40); cr.fill()
        txt(cr, '40 m', 300, 1800 - 40 * sc * g - 30, 80, REDS, a * ramp(t, T_TALL + 2.4, T_TALL + 2.8), fam=BLK)
        txt(cr, '≈ 13 floors · 13층', 670, 1800 - 39 * sc - 30, 38, INKS, a * ramp(t, T_TALL + 2.8, T_TALL + 3.2), fam=BOLD)
        cr.set_source_rgba(*REDS, a); cr.rectangle(0, 1800, 1080, 120); cr.fill()
    else:                                                                   # 땅속 뿌리줄기
        a = ramp(t, T_ROOT, T_ROOT + 0.3) * (1 - ramp(t, T_CODA - 0.3, T_CODA))
        cr.set_source_rgba(*INKS, a); cr.rectangle(0, 1040, 1080, 880); cr.fill()
        g = smooth(ramp(t, T_ROOT + 0.3, T_ROOT + 3.4))
        cr.set_source_rgba(*PAPERW, a); cr.set_line_width(10)
        for row, y in enumerate([1200, 1360, 1520]):
            L = 1000 * min(1, max(0, g * 1.3 - row * 0.15))
            cr.move_to(40, y); cr.line_to(40 + L, y); cr.stroke()
            for k in range(int(L // 90)):
                x = 80 + k * 90; cr.set_line_width(3); cr.move_to(x, y); cr.line_to(x - 20, y + 60); cr.move_to(x, y); cr.line_to(x + 20, y + 60); cr.stroke(); cr.set_line_width(10)
        sh = 260 * ramp(t, T_ROOT + 3.4, T_ROOT + 4.6)
        cr.set_source_rgba(*GREENS, a); cr.move_to(700, 1040); cr.line_to(730, 1040 - sh); cr.line_to(760, 1040); cr.close_path(); cr.fill()
        txt(cr, 'years underground · 땅속의 몇 해', 540, 1760, 46, PAPERW, a * ramp(t, T_ROOT + 1.0, T_ROOT + 1.4), fam=BLK)
    if t < T_CODA:                                                          # 박자에 맞춘 빨간 점
        cr.set_source_rgba(*REDS, 0.9 * (1 - ramp(t, T_CODA - 0.3, T_CODA))); cr.arc(990, 560, 18 + 10 * pulse, 0, 6.283); cr.fill()
    return np.ascontiguousarray(arr(s)[..., :3])

def sound(path):
    m = S.Mix(EP['DUR'], 91); tc = EP['t_coda']
    n = int((tc - 0.2) / B)
    bass = [55.0, 55.0, 65.4, 49.0]
    for k in range(n):
        t = k * B
        m.put('mus', t, S.kick(52, 0.5))
        m.put('mus', t + B / 2, S.hihat(0.18, seed=k, open_=(k % 4 == 3)))
        if t > T_HOUR: m.put('mus', t + B / 4, S.hihat(0.08, seed=k + 500))
        if k % 2 == 0: m.put('mus', t + B / 2, S.drone([bass[(k // 8) % 4]], B * 0.9, 0.22, 'sine'))
    m.put('fx', T_TALL + 2.4, S.bell(880.0, 1.6, 0.18)); m.put('fx', T_ROOT + 3.4, S.swoosh(1.2, 0.2, 300, 3000))
    for i, f in enumerate([440.0, 329.6, 220.0]): m.put('mus', tc + 0.8 + i * STEP, S.bell(f, 2.6, 0.24))
    m.write(path, rev_mus=1.6, wet_mus=0.25)

EP = finalize(dict(t_coda=T_CODA, draw=draw, sound=sound, end_icon='star', grain=0.0,
    title_en_card='91 CM A DAY', title_ko_card='하루에 91cm',
    pal=dict(hi=REDS, endbg=PAPERW),
    card_style=dict(box='paper', bg=(0.99, 0.99, 0.97), ink=INKS, hi=REDS, y=180, fe=BLK, fk=BLK),
    cards=[(0.3, 4.0, ['Some bamboo grows', 'up to *91 cm* in a single day.'], ['어떤 대나무는', '하루에 *91cm*까지 자란다']),
           (4.2, 9.4, ['That is about *3.8 cm*', 'every hour.'], ['한 시간에', '약 *3.8cm*']),
           (9.6, 14.8, ['The tallest recorded:', 'about *40 m*.'], ['가장 큰 기록은', '약 *40m*']),
           (15.0, 20.4, ['But first, its roots spread', 'underground for *months or years*.'], ['그 전에 땅속에서 *몇 달, 몇 해*', '뿌리를 넓힌다'])],
    coda=[('Growth too slow to see', '눈에 보이지 않는 성장도'), ('is still growth.', '여전히 성장이다'), ('Keep going, even when no one can tell.', '아무도 몰라줘도 계속 가자')],
    coda_style=dict(dim=0.5, blur=8, tint=(0.92, 0.90, 0.86), ink=INKS, hi=REDS, fe=BLK),
    sources=['Some bamboo species grow up to 91 cm per day; tallest recorded about 40 m in the tropics (Guinness World Records). 91/24 ≈ 3.8 cm per hour (calculated).', 'A rhizome network spends months or years storing energy before new shoots emerge (Bambu Batu). Building comparison assumes ~3 m per floor (calculated).'],
    yt=dict(title_en='Bamboo Can Grow 91 cm in a Single Day #Shorts', title_ko='하루에 91cm 자라는 대나무')))

if __name__ == '__main__': main(EP)
