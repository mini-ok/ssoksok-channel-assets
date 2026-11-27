"""〈별에서 온 몸〉 — 검은 우주에 빛나는 입자(가산 합성·빛 번짐), 앰비언트 패드·종소리.
사실(NASA Chandra "Elements in the human body" 포스터): 몸무게 기준 산소 65%, 탄소 18%, 수소 10%, 질소 3%.
수소는 빅뱅에서(몸 질량의 약 9.5%), 나머지 대부분은 별 안에서 만들어졌다. 몸속 철의 상당 부분은 초신성 폭발에서.
"""
import math, numpy as np, cv2, cairo
from base import *
import sfx as S

N = 2600
ELEM = [('O', 'Oxygen', '산소', 0.65, (0.35, 0.85, 1.0)), ('C', 'Carbon', '탄소', 0.18, (1.0, 0.72, 0.30)),
        ('H', 'Hydrogen', '수소', 0.10, (0.85, 0.90, 1.0)), ('N', 'Nitrogen', '질소', 0.03, (1.0, 0.40, 0.85)), ('·', 'Other', '기타', 0.04, (0.55, 1.0, 0.55))]
CL = [(330, 860), (760, 760), (790, 1160), (330, 1330), (640, 1420)]

def _setup():
    r = np.random.default_rng(13)
    # 사람 실루엣 점
    s = cairo.ImageSurface(cairo.FORMAT_A8, 540, 960); cr = cairo.Context(s); cr.set_source_rgba(0, 0, 0, 1)
    cr.arc(270, 150, 78, 0, 6.283); cr.fill()
    cr.move_to(180, 250); cr.line_to(360, 250); cr.line_to(420, 560); cr.line_to(370, 570); cr.line_to(340, 420); cr.line_to(330, 900); cr.line_to(280, 900)
    cr.line_to(270, 600); cr.line_to(260, 900); cr.line_to(210, 900); cr.line_to(200, 420); cr.line_to(170, 570); cr.line_to(120, 560); cr.close_path(); cr.fill()
    s.flush(); m = np.frombuffer(s.get_data(), np.uint8).reshape(960, s.get_stride())[:, :540] > 128
    ys, xs = np.nonzero(m); idx = r.choice(len(xs), N, replace=True)
    body = np.stack([xs[idx] + 270 + r.normal(0, 2, N), ys[idx] + 520 + r.normal(0, 2, N)], 1)
    kind = np.zeros(N, int); cut = np.cumsum([e[3] for e in ELEM]) * N
    kind[:] = np.searchsorted(cut, np.arange(N), side='right'); kind = np.minimum(kind, 4); r.shuffle(kind)
    cl = np.zeros((N, 2))
    for k in range(5):
        ii = np.nonzero(kind == k)[0]; R = 26 + 210 * math.sqrt(ELEM[k][3]); ang = r.uniform(0, 6.283, len(ii)); rad = R * np.sqrt(r.uniform(0, 1, len(ii)))
        cl[ii] = np.stack([CL[k][0] + rad * np.cos(ang), CL[k][1] + rad * np.sin(ang)], 1)
    # 기원: 수소→빅뱅(왼쪽 위), 나머지→별(가운데)
    org = np.zeros((N, 2)); ang = r.uniform(0, 6.283, N); rad = np.sqrt(r.uniform(0, 1, N))
    star = (600, 1100); bb = (260, 780)
    for i in range(N):
        c = bb if kind[i] == 2 else star; RR = 120 if kind[i] == 2 else 230
        org[i] = (c[0] + RR * rad[i] * math.cos(ang[i]), c[1] + RR * rad[i] * math.sin(ang[i]))
    scatter = np.stack([r.uniform(-200, DW + 200, N), r.uniform(-200, DH + 200, N)], 1)
    delay = r.uniform(0, 0.6, N); tw = r.uniform(0, 6.283, N)
    return dict(body=body, kind=kind, cl=cl, org=org, scatter=scatter, delay=delay, tw=tw, star=star, bb=bb)
D = _setup()

T_SPLIT = (3.6, 5.8); T_ORIG = (10.4, 12.6); T_BOOM = 16.2; T_REFORM = (16.8, 19.6); T_CODA = 22.8

def positions(t):
    P = D['scatter'].copy(); d = D['delay']
    def go(A, B, a, b):
        u = np.clip((t - a - d) / (b - a), 0, 1); u = u * u * (3 - 2 * u); return A + (B - A) * u[:, None]
    P = go(D['scatter'], D['body'], 0.0, 1.6)
    if t >= T_SPLIT[0]: P = go(D['body'], D['cl'], *T_SPLIT)
    if t >= T_ORIG[0]: P = go(D['cl'], D['org'], *T_ORIG)
    if t >= T_BOOM:                                             # 초신성: 별 쪽 입자만 밖으로
        u = np.clip((t - T_BOOM) / 0.9, 0, 1); out = D['org'] + (D['org'] - np.array(D['star'])) * (6 * (1 - (1 - u) ** 3))
        isH = D['kind'] == 2; P = np.where(isH[:, None], D['org'], out)
    if t >= T_REFORM[0]:
        src = np.where((D['kind'] == 2)[:, None], D['org'], D['org'] + (D['org'] - np.array(D['star'])) * 6)
        P = go(src, D['body'], *T_REFORM)
    P = P + np.stack([np.sin(t * 1.3 + D['tw']), np.cos(t * 1.1 + D['tw'] * 1.7)], 1) * 3
    return P

def draw(t):
    P = positions(t)
    s = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H); cr = cairo.Context(s); cr.scale(SC, SC)
    cr.set_source_rgb(0.012, 0.014, 0.03); cr.paint(); cr.set_operator(cairo.OPERATOR_ADD)
    r = np.random.default_rng(4)
    for _ in range(260):                                        # 먼 별
        x, y, b = r.uniform(0, DW), r.uniform(0, DH), r.uniform(0.15, 0.6)
        cr.set_source_rgba(1, 1, 1, b * (0.7 + 0.3 * math.sin(t * 2 + x))); cr.arc(x, y, 1.6, 0, 6.283); cr.fill()
    # 별(용광로)과 빅뱅 표시
    if T_ORIG[0] - 0.3 < t < T_BOOM + 0.6:
        a = ramp(t, T_ORIG[0] - 0.3, T_ORIG[0] + 0.6) * (1 - ramp(t, T_BOOM, T_BOOM + 0.6)); sx, sy_ = D['star']
        g = cairo.RadialGradient(sx, sy_, 0, sx, sy_, 330); g.add_color_stop_rgba(0, 1, 0.85, 0.55, 0.55 * a); g.add_color_stop_rgba(0.5, 1, 0.45, 0.15, 0.25 * a); g.add_color_stop_rgba(1, 1, 0.3, 0.1, 0)
        cr.set_source(g); cr.arc(sx, sy_, 330, 0, 6.283); cr.fill()
        bx, by = D['bb']; g = cairo.RadialGradient(bx, by, 0, bx, by, 170); g.add_color_stop_rgba(0, 0.8, 0.85, 1, 0.4 * a); g.add_color_stop_rgba(1, 0.5, 0.6, 1, 0)
        cr.set_source(g); cr.arc(bx, by, 170, 0, 6.283); cr.fill()
    if T_BOOM <= t < T_BOOM + 1.2:                              # 폭발 섬광
        u = (t - T_BOOM) / 1.2; sx, sy_ = D['star']; g = cairo.RadialGradient(sx, sy_, 0, sx, sy_, 200 + 1400 * u)
        g.add_color_stop_rgba(0, 1, 0.95, 0.8, 0.9 * (1 - u)); g.add_color_stop_rgba(1, 1, 0.5, 0.2, 0); cr.set_source(g); cr.paint()
    for k in range(5):
        col = ELEM[k][4]; ii = np.nonzero(D['kind'] == k)[0]; cr.set_source_rgba(*col, 0.85)
        for i in ii:
            x, y = P[i]; cr.arc(x, y, 3.2, 0, 6.283); cr.fill()
    s.flush(); a = np.frombuffer(s.get_data(), np.uint8).reshape(H, s.get_stride() // 4, 4)[:, :W, :3].astype(np.float32) / 255
    glow = cv2.GaussianBlur(a, (0, 0), 9 * SC) * 1.6 + cv2.GaussianBlur(a, (0, 0), 30 * SC) * 1.2
    img = a + glow
    s2, cr2 = surf()
    if T_SPLIT[1] - 0.6 < t < T_ORIG[0] + 0.3:                  # 원소 이름표
        b = ramp(t, T_SPLIT[1] - 0.6, T_SPLIT[1]) * (1 - ramp(t, T_ORIG[0] - 0.2, T_ORIG[0] + 0.3))
        for k, (sym, en, ko, sh, col) in enumerate(ELEM):
            x, y = CL[k]; R = 26 + 210 * math.sqrt(sh)
            for dx_, dy_ in ((3, 3), (-3, 3), (3, -3), (-3, -3)): txt(cr2, f'{sh * 100:.0f}%', x + dx_, y + 22 + dy_, 64 if sh > 0.1 else 44, (0.02, 0.02, 0.05), b * 0.8)
            txt(cr2, f'{sh * 100:.0f}%', x, y + 22, 64 if sh > 0.1 else 44, (1, 1, 1), b)
            txt(cr2, f'{en} · {ko}', x, y + R + 44, 34, col, b, fam=BOLD, maxw=360)
    if T_ORIG[1] - 0.6 < t < T_BOOM:
        b = ramp(t, T_ORIG[1] - 0.6, T_ORIG[1]) * (1 - ramp(t, T_BOOM - 0.4, T_BOOM))
        txt(cr2, 'Big Bang · 빅뱅', D['bb'][0], D['bb'][1] - 170, 40, (0.75, 0.82, 1), b, fam=BOLD)
        txt(cr2, 'Inside stars · 별 속에서', D['star'][0], D['star'][1] + 330, 44, (1, 0.7, 0.4), b, fam=BOLD)
    return over(img, s2)

def sound(path):
    m = S.Mix(EP['DUR'], 7); tc = EP['t_coda']
    m.put('amb', 0, S.drone([110, 164.8, 220, 277.2], EP['t_end'] + 1, 0.22, 'sine', vib=0.003))
    for i, f in enumerate([880, 1318.5, 1174.7, 1760]): m.put('mus', 0.4 + 0.45 * i, S.bell(f, 3.0, 0.25))
    m.put('fx', T_SPLIT[0], S.swoosh(2.2, 0.25, 800, 9000))
    for k in range(5): m.put('mus', T_SPLIT[1] - 0.2 + 0.25 * k, S.bell([659.3, 784.0, 987.8, 1174.7, 1318.5][k], 2.4, 0.3))
    m.put('fx', T_ORIG[0], S.swoosh(2.2, 0.25, 300, 6000)); m.put('amb', T_ORIG[0], S.rumble(T_BOOM - T_ORIG[0] + 0.5, 0.35))
    m.put('fx', T_BOOM, S.kick(40, 1.0, 1.6)); m.put('fx', T_BOOM, S.swoosh(2.5, 0.7, 60, 9000)); m.put('fx', T_BOOM + 0.05, S.rumble(3.0, 0.6))
    for j, f in enumerate([440, 554.4, 659.3, 880]): m.put('mus', T_REFORM[1] - 0.6 + 0.12 * j, S.bell(f, 3.2, 0.35))
    m.put('amb', tc, S.drone([82.4, 123.5, 164.8, 246.9], EP['t_end'] - tc, 0.28, 'sine', vib=0.004))
    for i in range(3): m.put('mus', tc + 0.8 + i * STEP, S.bell([1318.5, 1174.7, 1760.0][i], 3.5, 0.3))
    for j, f in enumerate([659.3, 987.8, 1318.5]): m.put('mus', EP['t_end'] + 0.15 + 0.08 * j, S.bell(f, 3.0, 0.3))
    m.write(path, rev_mus=3.2, wet_mus=0.42, rev_fx=2.2, wet_fx=0.3)

EP = finalize(dict(t_coda=T_CODA, draw=draw, sound=sound, end_icon='star', grain=0.006,
    title_en_card='MADE IN STARS', title_ko_card='별에서 온 몸',
    pal=dict(hi=(1.0, 0.62, 0.28), endbg=(0.95, 0.93, 0.9)),
    card_style=dict(box=None, ink=(0.95, 0.97, 1.0), hi=(1.0, 0.72, 0.35), y=170, fe=SERIF, fk=BLK, se=64, sk=56),
    cards=[(0.3, 3.4, ['What are you', '*made of*?'], ['나는 무엇으로', '*만들어졌을까*?']),
           (3.8, 10.2, ['By mass: *65%* oxygen,', '*18%* carbon, *10%* hydrogen.'], ['몸무게로 따지면 산소 *65%*,', '탄소 *18%*, 수소 *10%*']),
           (10.6, 16.0, ['Hydrogen came from the *Big Bang*.', 'The rest was forged *inside stars*.'], ['수소는 *빅뱅*에서,', '나머지는 *별 속에서* 만들어졌다']),
           (16.6, 22.6, ['About *90%* of your mass', 'was made in stars.'], ['내 몸무게의 약 *90%*는', '별에서 만들어졌다'])],
    coda=[('The iron in your blood', '당신 피 속의 철은'), ('was forged in stars that died long ago.', '오래전 죽어 간 별에서 왔다'), ('You are stardust that learned to wonder.', '당신은 궁금해할 줄 아는 별먼지다')],
    coda_style=dict(dim=0.55, blur=10, tint=(0.0, 0.0, 0.02), ink=(0.95, 0.96, 1.0), hi=(1.0, 0.72, 0.35)),
    sources=['NASA/Chandra, "Elements in the human body" (Year of the Periodic Table 2019): O 65%, C 18%, H 10%, N 3% by mass;', 'hydrogen from the Big Bang (~9.5% of body mass), most other elements from stars.'],
    yt=dict(title_en='About 90% of Your Body Was Made Inside Stars #Shorts', title_ko='내 몸의 약 90%는 별에서 만들어졌다')))

if __name__ == '__main__': main(EP)
