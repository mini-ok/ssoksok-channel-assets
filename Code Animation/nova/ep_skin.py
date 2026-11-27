"""〈한 달마다 새 피부〉 — 조각보(모시 조각을 이어 붙인 보자기: 뒤에서 비치는 빛, 겹쳐 진해진 솔기, 올이 보이는 천, 쪽·치자·소목 천연 염색 빛깔), 소리는 뜯는 현(가야금 결)과 낮은 지속음.
규칙 2판(rules=2) 첫 편: 30~70초, 긴 여운, 끝 화면 구독·좋아요 권유, 본편 글자는 맨 아래 띠를 피하되 균형이 먼저.
사실: 사람은 1분마다 죽은 피부 세포 약 30,000~40,000개를 떨어뜨린다(KidsHealth/Nemours; Skin Cancer Foundation은 "1분에 30,000개").
      새 세포가 겉까지 올라오는 데 약 한 달, 나이가 들면 6~8주까지 느려진다(Skin Cancer Foundation).
계산: 80년 ÷ 약 한 달 ≈ 1,000번(나이가 들수록 느려지므로 실제로는 이보다 조금 적다 → 화면에는 "천 번 가까이").
"""
import math, numpy as np, cv2, cairo
from base import *
import sfx as S

WALL = (0.95, 0.91, 0.82); ROD = (0.36, 0.24, 0.16); INKJ = (0.24, 0.17, 0.13); HI = (0.72, 0.26, 0.24)
DYES = [(0.97, 0.95, 0.89), (0.97, 0.95, 0.89), (0.93, 0.90, 0.80), (0.58, 0.71, 0.82), (0.30, 0.42, 0.62), (0.68, 0.82, 0.74),
        (0.94, 0.81, 0.46), (0.91, 0.62, 0.63), (0.74, 0.54, 0.38), (0.64, 0.44, 0.57)]
FRESH = [(0.99, 0.90, 0.80), (0.98, 0.78, 0.72), (0.96, 0.84, 0.60), (0.80, 0.90, 0.80)]
T_SHED = 4.8; T_RISE = 10.8; T_LIFE = 17.2; T_CODA = 23.6
X0, X1, Y0, Y1 = 110, 970, 716, 1500
_r = np.random.default_rng(28)

# ---- 바탕: 벽 + 뒤에서 비치는 빛, 천의 올(세계에 고정)
yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
GLOW = np.clip(1.08 - np.hypot((xx - W * 0.5) / (W * 0.9), (yy - H * 0.55) / (H * 0.62)) * 0.42, 0.82, 1.1)[..., None]
BGI = (np.array(WALL[::-1], np.float32)[None, None] * GLOW * (1 + 0.012 * cv2.GaussianBlur(_r.normal(0, 1, (H, W)).astype(np.float32), (0, 0), 1.2)[..., None])).astype(np.float32)
_p = 4.2 * SC
WEAVE = (1 + 0.045 * np.sin(xx * 2 * np.pi / _p) * 1.0 + 0.045 * np.sin(yy * 2 * np.pi / (_p * 1.15))
         + 0.05 * cv2.GaussianBlur(_r.normal(0, 1, (H, W)).astype(np.float32), (0, 0), 0.7))[..., None].astype(np.float32)

def _subdivide(x, y, w, h, depth, out):
    if depth > 5 or (w < 190 and h < 170) or (depth > 2 and _r.random() < 0.14):
        out.append([x, y, w, h, int(_r.integers(len(DYES)))]); return
    f = float(_r.uniform(0.34, 0.66))
    if w * _r.uniform(0.8, 1.25) > h: _subdivide(x, y, w * f, h, depth + 1, out); _subdivide(x + w * f, y, w * (1 - f), h, depth + 1, out)
    else: _subdivide(x, y, w, h * f, depth + 1, out); _subdivide(x, y + h * f, w, h * (1 - f), depth + 1, out)
PATCH = []; _subdivide(X0, Y0, X1 - X0, Y1 - Y0, 0, PATCH)
_top = sorted([i for i, p in enumerate(PATCH) if p[1] < Y0 + 300], key=lambda i: (PATCH[i][1], PATCH[i][0]))
SHED_T = {i: T_SHED + 0.7 + k * (4.4 / max(1, len(_top) - 1)) for k, i in enumerate(_top)}
SHED_NEW = {i: FRESH[k % len(FRESH)] for k, i in enumerate(_top)}

def sway(x, y, t):
    return x + 13 * math.sin(t * 0.9 + y / 420) * (y - Y0) / (Y1 - Y0), y

def piece(cr, x, y, w, h, col, a, t, seam=True):
    """조각 하나: 천 면 + 겹쳐 진해진 솔기 + 홈질 땀."""
    if a <= 0 or w < 1 or h < 1: return
    pts = [sway(x, y, t), sway(x + w, y, t), sway(x + w, y + h, t), sway(x, y + h, t)]
    cr.move_to(*pts[0]); [cr.line_to(*q) for q in pts[1:]]; cr.close_path()
    cr.set_source_rgba(*col, 0.94 * a); cr.fill_preserve()
    if seam:
        cr.save(); cr.clip_preserve(); cr.set_source_rgba(col[0] * 0.62, col[1] * 0.60, col[2] * 0.58, 0.85 * a); cr.set_line_width(13); cr.stroke()
        cr.restore()
        if min(w, h) > 40:
            cr.set_source_rgba(1, 1, 1, 0.55 * a); cr.set_line_width(1.6); cr.set_dash([5, 6])
            q = [sway(x + 4, y + 4, t), sway(x + w - 4, y + 4, t), sway(x + w - 4, y + h - 4, t), sway(x + 4, y + h - 4, t)]
            cr.move_to(*q[0]); [cr.line_to(*v) for v in q[1:]]; cr.close_path(); cr.stroke(); cr.set_dash([])
    else: cr.new_path()

def rod(cr, a):
    cr.set_source_rgba(*ROD, a); rrect(cr, 70, 694, 940, 20, 10); cr.fill()
    for x in (150, 540, 930):
        cr.set_source_rgba(*HI, a); cr.set_line_width(5); cr.move_to(x - 9, 690); cr.line_to(x - 9, 718); cr.move_to(x + 9, 690); cr.line_to(x + 9, 718); cr.stroke()

def flakes(cr, cx, cy, u, col, seed, a):
    """떨어져 나가는 비늘: 위로 흩어지며 사라진다."""
    if u <= 0 or u >= 1: return
    rr = np.random.default_rng(seed)
    for k in range(11):
        q = rr.uniform(-2.6, -0.5); d = rr.uniform(90, 300) * u; s_ = rr.uniform(10, 22) * (1 - 0.5 * u)
        x = cx + rr.uniform(-40, 40) + math.cos(q) * d + 18 * math.sin(u * 5 + k); y = cy + math.sin(q) * d
        cr.save(); cr.translate(x, y); cr.rotate(u * rr.uniform(-3, 3)); cr.set_source_rgba(*col, a * (1 - u) ** 1.2); cr.rectangle(-s_ / 2, -s_ / 2, s_, s_); cr.fill(); cr.restore()

def tag(cr, s_, x, y, a, size=30, col=INKJ):
    cr.select_font_face(BOLD, 0, 1); cr.set_font_size(size); w = cr.text_extents(s_).x_advance
    cr.set_source_rgba(0.99, 0.97, 0.91, 0.93 * a); rrect(cr, x - 16, y - size - 6, w + 32, size + 26, 12); cr.fill()
    txt(cr, s_, x, y, size, col, a, fam=BOLD, anchor='l')

# ---- 장면 3: 아래에서 올라오는 줄
NS = 7
def Ys(s_): s_ = min(max(s_, 0.0), NS); return Y1 - (176 * s_ - (124 / NS) * s_ * s_ / 2)
def rows(cr, t, a):
    ph = (t - T_RISE) * 0.52 + 0.4
    cr.save(); cr.rectangle(X0 - 20, Y0 - 40, X1 - X0 + 40, Y1 - Y0 + 40); cr.clip()
    for j in range(-int(ph) - 2, NS + 1):
        s0 = j + ph
        if s0 + 1 <= 0 or s0 >= NS: continue
        yb, yt = Ys(s0), Ys(s0 + 1); rr = np.random.default_rng(1000 + j); n = int(rr.integers(4, 8)); ws = rr.uniform(0.6, 1.5, n); ws = ws / ws.sum() * (X1 - X0)
        pale = min(1.0, max(0.0, (s0 + 0.5) / NS)); al = a * (1 - ramp(s0, NS - 1.35, NS - 0.35)); x = X0
        for k in range(n):
            base = FRESH[int(rr.integers(len(FRESH)))] if rr.random() < 0.5 else DYES[int(rr.integers(3, len(DYES)))]
            col = tuple(lerp(base[q] * (1.0 if pale > 0.15 else 1.02), (0.96, 0.94, 0.88)[q], pale ** 1.3 * 0.82) for q in range(3))
            piece(cr, x, yt, ws[k], yb - yt, col, al, t)
            if s0 > NS - 1.35: flakes(cr, x + ws[k] / 2, yt, ramp(s0, NS - 1.35, NS - 0.2), (0.78, 0.70, 0.62), 77 + j * 13 + k, a)
            x += ws[k]
    cr.restore()

# ---- 장면 4: 조각 천 개
GC, GR = 40, 25; GW = (X1 - X0) / GC; GY0 = 770
GCOL = _r.integers(0, len(DYES), GC * GR); GORD = np.argsort(_r.random(GC * GR) + np.repeat(np.arange(GR)[::-1], GC) * 0.9)

def draw(t):
    s, cr = surf()
    a1 = 1 - ramp(t, T_RISE - 0.35, T_RISE + 0.15)
    if a1 > 0:                                                         # 장면 1·2: 걸려 있는 조각보
        rod(cr, a1)
        for i, (x, y, w, h, c) in enumerate(PATCH):
            if i in SHED_T:
                u = ramp(t, SHED_T[i], SHED_T[i] + 1.5)
                piece(cr, x, y, w, h, SHED_NEW[i], a1 * smooth(ramp(u, 0.0, 0.7)), t)                 # 밑에서 올라온 새 조각
                if u < 1:
                    cr.save(); cx, cy = sway(x + w / 2, y + h / 2, t); cr.translate(cx, cy - 46 * u * u); cr.rotate(0.10 * u * (1 if i % 2 else -1)); cr.translate(-cx, -cy)
                    piece(cr, x, y, w, h, tuple(lerp(DYES[c][q], 0.93, 0.5) for q in range(3)), a1 * (1 - u) ** 1.5, t); cr.restore()
                    flakes(cr, cx, y + h * 0.3, u, (0.78, 0.70, 0.62), 500 + i, a1)
            else: piece(cr, x, y, w, h, DYES[c], a1, t)
        for k in range(16):                                            # 처음부터 조금씩 떨어져 오르는 비늘(눈에 안 띄던 것이 2장면에서 드러난다)
            u = (t * 0.27 + k * 0.137) % 1.0; hx = (k * 0.6180339) % 1.0; hy = (k * 0.3819660) % 1.0; sz = 9 + 9 * hy
            fx, fy = sway(X0 + 40 + hx * (X1 - X0 - 80), Y0 + 20 + hy * 420, t)
            cr.save(); cr.translate(fx + 34 * math.sin(u * 5 + k), fy - 300 * u); cr.rotate(u * 3 + k); cr.set_source_rgba(0.78, 0.70, 0.62, a1 * math.sin(math.pi * u) * (0.55 if t < T_SHED else 0.85)); cr.rectangle(-sz / 2, -sz / 2, sz, sz); cr.fill(); cr.restore()
        if t >= T_SHED:
            a = a1 * ramp(t, T_SHED + 0.5, T_SHED + 1.0)
            txt(cr, '30,000+', DW / 2, 612, 96, HI, a, fam=BLK); txt(cr, 'cells every minute · 1분마다 떨어지는 세포', DW / 2, 664, 32, INKJ, a, fam=BOLD)
    a3 = ramp(t, T_RISE - 0.1, T_RISE + 0.4) * (1 - ramp(t, T_LIFE - 0.35, T_LIFE + 0.15))
    if a3 > 0:                                                         # 장면 3: 아래에서 올라오는 새 줄
        rows(cr, t, a3)
        g = ramp(t, T_RISE + 0.6, T_LIFE - 1.0)
        txt(cr, 'about one month to the surface · 겉까지 약 한 달', DW / 2, 596, 34, INKJ, a3, fam=BOLD)
        for k in range(28):                                             # 홈질 스물여덟 땀 = 날짜
            on = k / 28 < g; cr.set_source_rgba(*(HI if on else INKJ), a3 * (1.0 if on else 0.28)); cr.set_line_width(6)
            x = 204 + k * 24.9; cr.move_to(x, 632); cr.line_to(x + 13, 652); cr.stroke()
        tag(cr, 'old · 묵은 세포', 136, 796, a3); tag(cr, 'new · 새 세포', 136, 1356, a3, col=HI)
        cr.set_source_rgba(*HI, 0.9 * a3); cr.set_line_width(6); cr.move_to(86, 1330); cr.line_to(86, 800); cr.stroke()
        cr.move_to(86, 780); cr.line_to(72, 812); cr.line_to(100, 812); cr.close_path(); cr.fill()
    a4 = ramp(t, T_LIFE - 0.1, T_LIFE + 0.4) * (1 - ramp(t, T_CODA - 0.3, T_CODA + 0.6) * 0.0)
    if a4 > 0:                                                         # 장면 4: 조각 천 개로 이은 한 사람의 시간
        g = smooth(ramp(t, T_LIFE + 0.5, T_LIFE + 4.6)); n = int(GC * GR * g)
        for k in GORD[:n]:
            r_, c_ = divmod(int(k), GC); col = DYES[GCOL[k]]
            cr.set_source_rgba(*col, 0.95 * a4); cr.rectangle(X0 + c_ * GW + 1.2, GY0 + r_ * GW + 1.2, GW - 2.4, GW - 2.4); cr.fill()
        cr.set_source_rgba(*INKJ, 0.25 * a4); cr.set_line_width(2); cr.rectangle(X0 - 6, GY0 - 6, X1 - X0 + 12, GR * GW + 12); cr.stroke()
        al4 = a4 * (1 - ramp(t, T_CODA - 0.2, T_CODA + 0.5))             # 여운이 시작되면 글자는 비키고 조각만 남는다
        txt(cr, f'≈ {int(round(1000 * g / 10) * 10):,}', DW / 2, 640, 100, HI, al4, fam=BLK)
        txt(cr, 'new skins in 80 years · 80년 동안의 새 피부', DW / 2, 700, 32, INKJ, al4, fam=BOLD)
        txt(cr, 'calculated · 계산 (80 years ÷ about 1 month)', DW / 2, GY0 + GR * GW + 62, 26, INKJ, 0.8 * al4 * ramp(t, T_LIFE + 1.0, T_LIFE + 1.5), fam=BOLD)
    cloth = arr(s); al = cloth[..., 3:4]
    lit = cloth[..., :3] * WEAVE * (0.84 + 0.20 * GLOW)                    # 올 + 뒤에서 비치는 빛(알파가 곱해진 색)
    img = BGI * (1 - al) + lit
    return np.clip(img + 0.05 * cv2.GaussianBlur(img, (0, 0), 9 * SC) - 0.04, 0, 1)

def sound(path):
    m = S.Mix(EP['DUR'], 28); tc, te = EP['t_coda'], EP['t_end']; e = 0.37
    E3, G3, A3, B3, D4, E4, G4, A4, B4 = 164.8, 196.0, 220.0, 246.9, 293.7, 329.6, 392.0, 440.0, 493.9
    seq = [E4, B3, D4, A3, B3, G3, A3, E3, G4, E4, D4, B3, A3, B3, D4, E4, A4, G4, E4, D4, E4, B3, A3, G3]
    t = 0.3; k = 0; bar = 0
    while t < tc - 0.6:                                               # 여섯 박 한 마디, 1·3·4·6에 뜯는다
        for off in (0, 2, 3, 5):
            if t + off * e < tc - 0.4: m.put('mus', t + off * e, S.koto(seq[k % len(seq)], 2.2, 0.26 if off in (0, 3) else 0.18, seed=k)); k += 1
        m.put('mus', t, S.koto((82.4, 110.0, 98.0, 82.4)[bar % 4], 3.2, 0.24, seed=900 + bar)); t += 6 * e; bar += 1
    m.put('amb', 0, S.drone([82.4, 123.5], EP['DUR'], 0.07, 'sine'))
    for i, ts in sorted(SHED_T.items(), key=lambda v: v[1]): m.put('fx', ts + 0.1, S.swoosh(0.9, 0.05, 1800, 7000, seed=i))
    for k2 in range(28): m.put('fx', T_RISE + 0.6 + k2 * (T_LIFE - 1.6 - T_RISE) / 28, S.tok(1500 + 12 * k2, 0.035))
    for k2 in range(16): m.put('fx', T_LIFE + 0.5 + k2 * 4.1 / 16, S.tok(700 + 40 * k2, 0.06))
    m.put('fx', T_LIFE + 4.6, S.bell(659.3, 3.0, 0.14))
    step = EP.get('coda_step', STEP2)                                  # 여운: 줄마다 두 음, 마지막은 길게
    for i, (f1, f2) in enumerate([(E4, B3), (D4, A3), (B3, E3)]):
        m.put('mus', tc + 0.8 + i * step, S.koto(f1, 4.0, 0.30, seed=300 + i)); m.put('mus', tc + 1.9 + i * step, S.koto(f2, 5.0, 0.26, seed=320 + i))
    m.put('mus', tc + 0.8 + 3 * step + 0.6, S.koto(E3 / 2, 6.0, 0.24, seed=340))
    m.put('mus', te + 3.2, S.koto(B4, 3.0, 0.20, seed=350)); m.put('mus', te + 4.0, S.bell(987.8, 3.0, 0.10)); m.put('mus', te + 4.0, S.koto(E4, 3.5, 0.18, seed=351))
    m.write(path, rev_mus=3.6, wet_mus=0.46)

EP = finalize(dict(rules=2, t_coda=T_CODA, draw=draw, sound=sound, end_icon='star', grain=0.0,
    title_en_card='A NEW SKIN EVERY MONTH', title_ko_card='한 달마다 새 피부',
    pal=dict(hi=HI, endbg=(0.96, 0.93, 0.85)),
    card_style=dict(box='paper', bg=(0.99, 0.97, 0.91), ink=INKJ, hi=HI, y=176, fe=BOLD, fk=BLK),
    cards=[(0.3, 4.6, ['Your skin looks the same', 'every single day.'], ['피부는 날마다', '그대로인 것 같다']),
           (4.8, 10.6, ['But every minute it sheds', 'over *30,000* cells.'], ['하지만 1분마다 세포', '*3만 개 이상*이 떨어져 나간다']),
           (10.8, 17.0, ['New cells rise from below', 'and surface in about *a month*.'], ['새 세포가 아래에서 올라와', '약 *한 달*이면 겉에 닿는다']),
           (17.2, 23.4, ['In 80 years, that is close to', '*1,000* new skins.'], ['80년이면 새 피부를', '*천 번 가까이* 입는다'])],
    coda=[('You are not who you were a month ago.', '한 달 전의 나는 이미 여기 없다'),
          ('Every day you let a little go, and begin again.', '날마다 조금씩 놓아 보내고, 다시 시작한다'),
          ('Forgive yesterday. Wear today anew.', '어제를 용서하고, 오늘을 새로 입자')],
    coda_style=dict(dim=0.62, blur=10, tint=(0.97, 0.94, 0.86), ink=INKJ, hi=HI, fe=SERIF),
    cta=('Come back new tomorrow. We will be here.', '내일 새로워진 당신을, 다음 이야기로 기다릴게요'),
    sources=['About 30,000–40,000 dead skin cells are shed every minute (KidsHealth/Nemours; Skin Cancer Foundation).',
             'New cells reach the surface in about a month, slower with age (Skin Cancer Foundation). 80 years ÷ ~1 month ≈ 1,000 (calculated).'],
    yt=dict(title_en='You Wear a Brand-New Skin Every Month #Shorts', title_ko='한 달마다 새 피부를 입는다')))

if __name__ == '__main__': main(EP)
