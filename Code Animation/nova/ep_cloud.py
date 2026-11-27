"""〈구름 한 덩이의 무게〉 — 로코코 천장화(연분홍·하늘색 파스텔 하늘, 금박 액자 테두리와 조개 장식, 부드러운 붓 터치 구름, 리본), 소리는 하프시코드 미뉴에트.
사실: 가로·세로·높이 1 km 적운에는 물방울이 1 m³당 약 0.5 g → 약 50만 kg(110만 파운드)(USGS Water Science School).
코끼리 약 100마리 무게(EarthDate; Smithsonian How Things Fly). 물방울이 아주 작고 넓게 퍼져 있어 떠 있다(Britannica 영상).
"""
import math, numpy as np, cv2, cairo
from base import *
import sfx as S

SKY_T = (0.70, 0.84, 0.95); SKY_B = (0.98, 0.84, 0.86); GILD = (0.82, 0.66, 0.30); GILD_D = (0.55, 0.40, 0.16); CLOUDW = (1.0, 0.98, 0.96); ROSEP = (0.92, 0.58, 0.66); INKR = (0.36, 0.24, 0.20)
T_KG = 4.2; T_ELE = 9.8; T_WHY = 15.2; T_CODA = 20.6
_r = np.random.default_rng(500)
BLOBS = [(float(_r.uniform(-1, 1)), float(_r.uniform(-0.45, 0.35)), float(_r.uniform(0.25, 0.45))) for _ in range(26)]

def frame_(cr):
    cr.set_source_rgb(*GILD); cr.set_line_width(36); cr.rectangle(60, 520, 960, 1300); cr.stroke()
    cr.set_source_rgb(*GILD_D); cr.set_line_width(4); cr.rectangle(40, 500, 1000, 1340); cr.stroke(); cr.rectangle(80, 540, 920, 1260); cr.stroke()
    for (x, y, rot) in [(540, 500, 0), (540, 1840, math.pi), (40, 1170, -math.pi / 2), (1040, 1170, math.pi / 2)]:   # 조개 장식
        cr.save(); cr.translate(x, y); cr.rotate(rot)
        for k in range(7):
            q = math.pi + (k + 0.5) * math.pi / 7; cr.set_source_rgb(*(GILD if k % 2 else GILD_D))
            cr.move_to(0, 0); cr.arc(0, 0, 70, q - 0.2, q + 0.2); cr.close_path(); cr.fill()
        cr.restore()

def cloud(cr, cx, cy, sc, a=1.0, shade=1.0):
    for (bx, by, br) in BLOBS:                                           # 아래 그늘
        cr.set_source_rgba(0.80 * shade, 0.76 * shade, 0.86 * shade, 0.5 * a); cr.arc(cx + bx * sc, cy + by * sc + 0.08 * sc, br * sc, 0, 6.283); cr.fill()
    for (bx, by, br) in BLOBS:
        cr.set_source_rgba(*CLOUDW, 0.9 * a); cr.arc(cx + bx * sc, cy + by * sc, br * sc * 0.92, 0, 6.283); cr.fill()

def elephant(cr, x, y, s, a):
    cr.save(); cr.translate(x, y); cr.scale(s, s); cr.set_source_rgba(0.55, 0.52, 0.62, a)
    cr.save(); cr.scale(1.3, 1); cr.arc(0, 0, 30, 0, 6.283); cr.restore(); cr.fill()
    cr.arc(36, -12, 18, 0, 6.283); cr.fill(); cr.set_line_width(8); cr.set_source_rgba(0.55, 0.52, 0.62, a)
    cr.move_to(50, -6); cr.curve_to(60, 10, 54, 26, 46, 30); cr.stroke()
    for lx in (-26, -10, 10, 24): cr.rectangle(lx - 5, 18, 10, 18); cr.fill()
    cr.restore()

def draw(t):
    s, cr = surf()
    g = cairo.LinearGradient(0, 520, 0, 1820); g.add_color_stop_rgb(0, *SKY_T); g.add_color_stop_rgb(1, *SKY_B)
    cr.set_source_rgb(0.97, 0.93, 0.88); cr.paint(); cr.set_source(g); cr.rectangle(80, 540, 920, 1260); cr.fill()
    drift = 12 * math.sin(t * 0.5)
    if t < T_KG:
        a = 1 - ramp(t, T_KG - 0.3, T_KG)
        cloud(cr, 540 + drift, 1060, 300, a)
    elif t < T_ELE:                                                      # 1 km 정육면체와 무게
        a = ramp(t, T_KG, T_KG + 0.3) * (1 - ramp(t, T_ELE - 0.3, T_ELE))
        cloud(cr, 540 + drift, 1000, 280, a)
        cr.set_source_rgba(*INKR, a * 0.8); cr.set_line_width(4); cr.set_dash([14, 10])
        cr.rectangle(300, 760, 480, 480); cr.stroke(); cr.set_dash([])
        txt(cr, '1 km × 1 km × 1 km', 540, 730, 38, INKR, a, fam=SERIF)
        txt(cr, '0.5 g / m³', 540, 1320, 48, INKR, a * ramp(t, T_KG + 0.8, T_KG + 1.2), fam=SERIF)
        n = int(500000 * smooth(ramp(t, T_KG + 1.4, T_KG + 3.4)))
        txt(cr, f'{n:,} kg', 540, 1460, 96, (0.72, 0.28, 0.40), a * ramp(t, T_KG + 1.4, T_KG + 1.6), fam=SERIF)
    elif t < T_WHY:                                                      # 코끼리 100마리
        a = ramp(t, T_ELE, T_ELE + 0.3) * (1 - ramp(t, T_WHY - 0.3, T_WHY))
        cloud(cr, 540 + drift, 820, 220, a)
        g2 = ramp(t, T_ELE + 0.4, T_ELE + 3.4)
        for k in range(int(100 * g2)):
            x = 170 + (k % 10) * 82; y = 1140 + (k // 10) * 58
            elephant(cr, x, y, 0.62, a)
        txt(cr, '≈ 100 elephants', 540, 1760, 54, INKR, a * ramp(t, T_ELE + 3.2, T_ELE + 3.6), fam=SERIF)
    else:                                                                # 왜 떠 있나: 아주 작은 물방울
        a = ramp(t, T_WHY, T_WHY + 0.3) * (1 - ramp(t, T_CODA - 0.3, T_CODA))
        z = smooth(ramp(t, T_WHY + 0.3, T_WHY + 2.0))
        cloud(cr, 540, 1060, 300 * (1 + 2.5 * z), a * (1 - z))
        rr = np.random.default_rng(7)
        for k in range(160):
            x = 120 + rr.uniform(0, 840); y = 600 + rr.uniform(0, 1150) + 20 * math.sin(t * 0.8 + k)
            cr.set_source_rgba(0.55, 0.70, 0.90, a * z); cr.arc(x, y, 5, 0, 6.283); cr.fill()
        txt(cr, 'tiny droplets, far apart', 540, 1500, 50, INKR, a * ramp(t, T_WHY + 2.0, T_WHY + 2.4), fam=SERIF)
        txt(cr, '아주 작은 물방울이 멀리 떨어져 있다', 540, 1570, 38, INKR, a * ramp(t, T_WHY + 2.0, T_WHY + 2.4), fam=SERIF)
    frame_(cr)
    img = np.ascontiguousarray(arr(s)[..., :3])
    soft = cv2.GaussianBlur(img, (0, 0), 1.2 * SC)                        # 붓 터치처럼 살짝 부드럽게
    return np.clip(img * 0.55 + soft * 0.45, 0, 1)

def sound(path):
    m = S.Mix(EP['DUR'], 551); tc = EP['t_coda']; b = 60 / 120
    mel = [659.3, 587.3, 523.3, 587.3, 659.3, 659.3, 659.3, 0, 587.3, 587.3, 587.3, 0, 659.3, 784.0, 784.0, 0,
           659.3, 587.3, 523.3, 587.3, 659.3, 659.3, 659.3, 659.3, 587.3, 587.3, 659.3, 587.3, 523.3, 0, 0, 0]
    bass = [130.8, 196.0, 164.8, 196.0]
    t = 0.3; k = 0
    while t < tc - 0.3:
        f = mel[k % len(mel)]
        if f: m.put('mus', t, S.harpsichord(f, 0.9, 0.22, seed=k))
        if k % 3 == 0: m.put('mus', t, S.harpsichord(bass[(k // 3) % 4], 1.2, 0.18, seed=k + 300))
        t += b; k += 1
    m.put('fx', T_KG + 1.4, S.bell(784.0, 2.0, 0.16)); m.put('fx', T_WHY + 0.3, S.swoosh(1.8, 0.14, 1500, 6000))
    for i, f in enumerate([523.3, 392.0, 261.6]): m.put('mus', tc + 0.8 + i * STEP, S.harpsichord(f, 2.4, 0.3, seed=500 + i))
    m.write(path, rev_mus=2.2, wet_mus=0.35)

EP = finalize(dict(t_coda=T_CODA, draw=draw, sound=sound, end_icon='star', grain=0.0,
    title_en_card='A CLOUD WEIGHS 500 TONNES', title_ko_card='구름 한 덩이의 무게',
    pal=dict(hi=(0.80, 0.42, 0.52), endbg=(0.98, 0.94, 0.92)),
    card_style=dict(box='paper', bg=(0.99, 0.96, 0.94), ink=INKR, hi=(0.80, 0.40, 0.50), y=180, fe=SERIF, fk=BLK),
    cards=[(0.3, 4.0, ['A fluffy cumulus cloud', 'looks weightless.'], ['몽실몽실한 뭉게구름,', '무게가 없어 보인다']),
           (4.2, 9.6, ['A 1 km cloud holds about', '*500,000 kg* of water.'], ['1km 크기 구름 속 물은', '약 *50만 kg*']),
           (9.8, 15.0, ['That is about', 'the weight of *100 elephants*.'], ['코끼리 *100마리*', '무게쯤']),
           (15.2, 20.4, ['It floats because the droplets', 'are *tiny* and spread out.'], ['그래도 뜨는 건 물방울이', '*아주 작고* 흩어져 있어서'])],
    coda=[('Even heavy things can float', '무거운 것도 떠 있을 수 있다'), ('when they are spread out gently.', '부드럽게 나누어 지면'), ('Share the weight you carry.', '내가 진 무게를 나누자')],
    coda_style=dict(dim=0.5, blur=8, tint=(0.90, 0.86, 0.90), ink=INKR, hi=(0.80, 0.40, 0.50), fe=SERIF),
    sources=['A 1 km³ cumulus cloud at ~0.5 g of water per m³ holds ~500,000 kg (1.1 million lb) (USGS Water Science School).', 'About the weight of 100 elephants (EarthDate; Smithsonian How Things Fly). Droplets are tiny and spread out, so updrafts keep them aloft (Britannica).'],
    yt=dict(title_en='A Fluffy Cloud Weighs as Much as 100 Elephants #Shorts', title_ko='뭉게구름 하나가 코끼리 100마리 무게')))

if __name__ == '__main__': main(EP)
