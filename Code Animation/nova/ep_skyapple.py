"""〈하늘은 얼마나 얇을까〉 다시 만들기 — 옛 백과사전 동판화(세피아 선, 해칭·교차 해칭, 손으로 칠한 옅은 색), 소리는 하프시코드와 바람.
사실: 지구 평균 반지름 6,371 km(NASA), 우주의 경계 100 km(FAI 카르만 선 관례) → 반지름의 1.57%.
지구를 지름 8 cm 사과로 줄이면 100 km는 0.63 mm. 종이 한 장 0.1 mm 가정 → 약 6장.
"""
import math, numpy as np, cv2, cairo
from base import *
import sfx as S

SEPIA = np.array((0.16, 0.22, 0.30), np.float32)          # BGR 잉크
PAPER = (0.93, 0.89, 0.80)
T_PLATE = 4.6; T_APPLE = 12.8; T_LOUPE = 17.2; T_SHEETS = 19.0; T_CODA = 23.6
_yy, _xx = np.mgrid[0:H, 0:W].astype(np.float32); _xx /= SC; _yy /= SC          # 설계 좌표
_r = np.random.default_rng(12)
def _paper():
    g = sum(cv2.resize(_r.standard_normal((max(2, H // d), max(2, W // d))).astype(np.float32), (W, H), interpolation=cv2.INTER_CUBIC) * w for d, w in ((3, 0.4), (40, 0.7), (200, 1.0)))
    g = (g - g.min()) / (g.max() - g.min())
    base = np.array(PAPER[::-1], np.float32) * (0.96 + 0.06 * g[..., None])
    vig = 1 - 0.18 * (((_xx - 540) / 700) ** 2 + ((_yy - 960) / 1100) ** 2)        # 가장자리 누렇게
    return base * vig[..., None]
PAPER_IMG = _paper()

def ink_of(tone, phase, p):
    """tone(0..1)만큼 굵어지는 평행선. phase는 설계 픽셀 단위."""
    f = np.abs((phase / p) % 1.0 - 0.5) * 2
    aa = 1.6 / p
    tn = np.clip(tone, 0, 0.95)
    return np.clip((tn - f) / aa + 0.5, 0, 1) * np.clip(tn * 12, 0, 1)

def tone_of(fn):
    s, cr = surf(); fn(cr); return arr(s)[..., 3]

def engrave(tone, field='diag', c=(540, 1060), p=7.0):
    if field == 'diag': ph1 = _xx * 0.57 + _yy * 0.82
    else: ph1 = np.hypot(_xx - (c[0] - 900), _yy - (c[1] - 900))           # 둥근 물체: 휘어 감는 선
    ph2 = _xx * 0.82 - _yy * 0.57
    return np.maximum(ink_of(tone, ph1, p), ink_of(np.clip(tone * 1.6 - 0.75, 0, 1), ph2, p))

def tint(img, alpha, rgb, k=0.55):
    c = np.array(rgb[::-1], np.float32)
    return img * (1 - alpha[..., None] * k * (1 - c))

def draw(t):
    img = PAPER_IMG.copy(); lines = surf(); L, lc = lines
    lc.set_source_rgba(0.30, 0.22, 0.16, 1)
    a_glob = 1 - ramp(t, T_PLATE - 0.4, T_PLATE)
    a_plate = ramp(t, T_PLATE - 0.4, T_PLATE) * (1 - ramp(t, T_APPLE - 0.4, T_APPLE))
    a_apple = ramp(t, T_APPLE - 0.4, T_APPLE)
    ink = np.zeros((H, W), np.float32); blue = np.zeros((H, W), np.float32); red = np.zeros((H, W), np.float32); green = np.zeros((H, W), np.float32)
    # ---- 1. 지구본 판화
    if a_glob > 0:
        cx, cy, R = 540, 1080, 330
        def ocean(cr): cr.set_source_rgba(0, 0, 0, 0.32); cr.arc(cx, cy, R, 0, 6.283); cr.fill()
        def land(cr):
            rr = np.random.default_rng(3)
            for a, d, r in ((0.6, 0.55, 0.26), (2.0, 0.6, 0.22), (2.9, 0.25, 0.2), (4.1, 0.65, 0.24), (5.2, 0.45, 0.18), (3.6, 0.8, 0.14)):
                d, r = d * R, r * R
                cr.set_source_rgba(0, 0, 0, 0.78); cr.save(); cr.translate(cx + d * math.cos(a), cy + d * math.sin(a)); cr.rotate(a); cr.scale(1, 0.65); cr.arc(0, 0, r, 0, 6.283); cr.restore(); cr.fill()
            cr.set_operator(cairo.OPERATOR_DEST_IN); cr.arc(cx, cy, R, 0, 6.283); cr.fill()
        ink += engrave(tone_of(ocean), 'round', (cx, cy)) * a_glob; ink = np.maximum(ink, engrave(tone_of(land), 'diag') * a_glob)
        lc.set_line_width(4); lc.arc(cx, cy, R, 0, 6.283); lc.stroke()
        for k in range(1, 6):
            lc.set_line_width(1.2); lc.save(); lc.translate(cx, cy); lc.scale(1, 0.18 * k); lc.arc(0, 0, R, 0, 6.283); lc.restore(); lc.stroke()
        def sky(cr): cr.set_source_rgba(0, 0, 0, 1); cr.set_line_width(5.2); cr.arc(cx, cy, R + 2.6, 0, 6.283); cr.stroke()
        blue += tone_of(sky) * a_glob
    # ---- 2. 단면 도판: 땅에서 100 km까지
    G, KM = 1440, 6.0                                       # 땅 높이, 1 km = 6 px
    if a_plate > 0:
        def air(cr):
            g = cairo.LinearGradient(0, G, 0, G - 100 * KM); g.add_color_stop_rgba(0, 0, 0, 0, 0.4); g.add_color_stop_rgba(1, 0, 0, 0, 0.03)
            cr.set_source(g); cr.rectangle(0, G - 100 * KM, DW, 100 * KM); cr.fill()
        def ground(cr):
            cr.set_source_rgba(0, 0, 0, 0.7); cr.rectangle(0, G, DW, 170); cr.fill()
            cr.move_to(300, G); cr.line_to(330, G - 8.85 * KM); cr.line_to(352, G); cr.close_path(); cr.fill()
        ink = np.maximum(ink, engrave(tone_of(air), 'diag', p=8.0) * a_plate); ink = np.maximum(ink, engrave(tone_of(ground), 'diag') * a_plate)
        blue += tone_of(air) * 1.6 * a_plate
        lc.set_line_width(3); lc.move_to(0, G); lc.line_to(DW, G); lc.stroke()
        lc.set_dash([12, 9]); lc.set_line_width(2.5); lc.move_to(160, G - 100 * KM); lc.line_to(1020, G - 100 * KM); lc.stroke(); lc.set_dash([])
        lc.set_line_width(2)                                    # 눈금자 0~100 km
        lc.move_to(120, G); lc.line_to(120, G - 100 * KM); lc.stroke()
        for k in range(0, 101, 10):
            lc.move_to(120, G - k * KM); lc.line_to(140 if k % 50 else 150, G - k * KM); lc.stroke()
            if k % 50 == 0: txt(lc, f'{k} km', 110, G - k * KM + 10, 26, (0.30, 0.22, 0.16), a_plate, fam=SERIF, anchor='r')
        px, py = 720, G - 11 * KM                               # 여객기
        lc.move_to(px - 26, py); lc.line_to(px + 26, py); lc.move_to(px + 2, py); lc.line_to(px - 10, py - 14); lc.move_to(px + 2, py); lc.line_to(px - 10, py + 14); lc.stroke()
        la = a_plate * ramp(t, 5.2, 5.8)
        for (x, y, en, ko, side) in ((330, G - 8.85 * KM, 'Mt. Everest · 8.8 km', '에베레스트', 1), (720, G - 11 * KM, 'Airliners · ~11 km', '여객기', -1),
                                    (380, G - 100 * KM, 'Edge of space · 100 km', '우주의 경계', 1)):
            ly = {'Mt': G - 190, 'Ai': G - 400, 'Ed': y - 90}[en[:2]]
            bx = x + side * 40; anc = 'l' if side > 0 else 'r'
            lc.set_line_width(1.8); lc.set_source_rgba(0.30, 0.22, 0.16, la); lc.move_to(x, y - 6); lc.line_to(bx, ly + 50); lc.stroke()
            lc.select_font_face(SERIF); lc.set_font_size(38); w = max(lc.text_extents(en).x_advance, 300)
            x0 = bx if side > 0 else bx - w - 30
            lc.set_source_rgba(*PAPER, 0.92 * la); lc.rectangle(x0 - 6, ly - 40, w + 36, 104); lc.fill()
            lc.set_source_rgba(0.30, 0.22, 0.16, la); lc.set_line_width(1.5); lc.rectangle(x0 - 6, ly - 40, w + 36, 104); lc.stroke()
            txt(lc, en, x0 + 12, ly, 38, (0.30, 0.22, 0.16), la, fam=SERIF, anchor='l')
            txt(lc, ko, x0 + 12, ly + 46, 34, (0.30, 0.22, 0.16), la, fam=SERIF, anchor='l')
            lc.set_source_rgba(0.30, 0.22, 0.16, 1)
        ba = a_plate * ramp(t, 9.0, 9.6)                        # 반지름 막대 비교
        if ba > 0:
            lc.set_line_width(2); lc.rectangle(90, 1700, 900, 22); lc.stroke()
            def bar(cr): cr.set_source_rgba(0, 0, 0, 0.6 * ba); cr.rectangle(90, 1700, 900 * smooth(ramp(t, 9.0, 10.2)), 22); cr.fill()
            ink = np.maximum(ink, engrave(tone_of(bar), 'diag', p=5))
            w100 = 900 * 100 / 6371; blue += tone_of(lambda cr: (cr.set_source_rgba(0, 0, 0, ba), cr.rectangle(990 - w100, 1660, w100, 22), cr.fill()))
            txt(lc, 'Earth’s radius 6,371 km · 지구 반지름', 90, 1770, 30, (0.30, 0.22, 0.16), ba, fam=SERIF, anchor='l')
            txt(lc, '100 km = 1.6%', 990, 1645, 32, (0.25, 0.35, 0.55), ba, fam=SERIF, anchor='r')
        txt(lc, 'PLATE I.  THE THICKNESS OF THE SKY', 540, 1640 if ba <= 0 else 1880, 28, (0.30, 0.22, 0.16), a_plate * 0.8, fam=SERIF)
    # ---- 3. 사과 판화 + 돋보기
    if a_apple > 0:
        cx, cy, R = 470, 1000, 270
        def apple_shape(cr):
            cr.move_to(cx, cy - R * 0.78)
            cr.curve_to(cx + R * 0.5, cy - R * 1.12, cx + R * 1.12, cy - R * 0.62, cx + R * 0.98, cy + R * 0.12)
            cr.curve_to(cx + R * 0.9, cy + R * 0.8, cx + R * 0.35, cy + R * 1.05, cx, cy + R * 0.9)
            cr.curve_to(cx - R * 0.35, cy + R * 1.05, cx - R * 0.9, cy + R * 0.8, cx - R * 0.98, cy + R * 0.12)
            cr.curve_to(cx - R * 1.12, cy - R * 0.62, cx - R * 0.5, cy - R * 1.12, cx, cy - R * 0.78); cr.close_path()
        def shade(cr):
            apple_shape(cr); cr.clip()
            g = cairo.RadialGradient(cx - R * 0.35, cy - R * 0.4, R * 0.1, cx + R * 0.2, cy + R * 0.3, R * 1.3)
            g.add_color_stop_rgba(0, 0, 0, 0, 0.0); g.add_color_stop_rgba(0.5, 0, 0, 0, 0.35); g.add_color_stop_rgba(1, 0, 0, 0, 0.85); cr.set_source(g); cr.paint()
        sh = tone_of(shade); ink = np.maximum(ink, engrave(sh, 'round', (cx, cy), p=6.5) * a_apple)
        red += tone_of(lambda cr: (apple_shape(cr), cr.set_source_rgba(0, 0, 0, 1), cr.fill())) * a_apple
        lc.set_line_width(3.5); apple_shape(lc); lc.stroke()
        lc.set_line_width(6); lc.move_to(cx, cy - R * 0.75); lc.curve_to(cx + 6, cy - R * 0.95, cx + 20, cy - R * 1.05, cx + 30, cy - R * 1.12); lc.stroke()
        def leaf(cr):
            cr.move_to(cx + 22, cy - R * 1.02); cr.curve_to(cx + 90, cy - R * 1.35, cx + 190, cy - R * 1.2, cx + 230, cy - R * 1.08)
            cr.curve_to(cx + 160, cy - R * 0.92, cx + 80, cy - R * 0.92, cx + 22, cy - R * 1.02); cr.close_path()
        green += tone_of(lambda cr: (leaf(cr), cr.set_source_rgba(0, 0, 0, 1), cr.fill())) * a_apple
        lc.set_line_width(2.5); leaf(lc); lc.stroke(); lc.set_line_width(1.2)
        for k in range(1, 7): lc.move_to(cx + 22 + 30 * k, cy - R * 1.02 - 8 * math.sin(k / 2.2)); lc.line_to(cx + 40 + 30 * k, cy - R * 1.12 - 4 * k * 0.6); lc.stroke()
        sa = ramp(t, T_APPLE + 0.8, T_APPLE + 1.4)
        blue += tone_of(lambda cr: (apple_shape(cr), cr.set_source_rgba(0, 0, 0, 1), cr.set_line_width(4.2), cr.stroke())) * sa
        txt(lc, 'Earth as an 8 cm apple · 지름 8cm 사과만 한 지구', 540, 1330, 34, (0.30, 0.22, 0.16), a_apple * ramp(t, T_APPLE + 0.4, T_APPLE + 1.0), fam=SERIF)
        la = ramp(t, T_LOUPE, T_LOUPE + 0.7)
        if la > 0:                                             # 돋보기: 하늘 0.63 mm vs 종이 6장
            lx, ly, lr = 700, 1610, 250; ex, ey = cx + R * 0.98, cy + R * 0.12
            lc.set_line_width(2); lc.move_to(ex, ey); lc.line_to(lx - lr * 0.6, ly - lr * 0.8); lc.stroke()
            lc.arc(ex, ey, 14, 0, 6.283); lc.stroke()
            PX = 120.0                                          # 1 mm = 120 px
            base_y = ly + 70
            def flesh(cr):
                cr.arc(lx, ly, lr, 0, 6.283); cr.clip(); cr.set_source_rgba(0, 0, 0, 0.6 * la); cr.rectangle(lx - lr, base_y, 2 * lr, lr); cr.fill()
            ink = np.maximum(ink, engrave(tone_of(flesh), 'diag', p=6))
            red += tone_of(lambda cr: (cr.arc(lx, ly, lr, 0, 6.283), cr.clip(), cr.set_source_rgba(0, 0, 0, la), cr.rectangle(lx - lr, base_y, 2 * lr, lr), cr.fill()))
            blue += tone_of(lambda cr: (cr.arc(lx, ly, lr, 0, 6.283), cr.clip(), cr.set_source_rgba(0, 0, 0, la), cr.rectangle(lx - lr, base_y - 0.63 * PX, lr, 0.63 * PX), cr.fill()))
            na = ramp(t, T_SHEETS, T_SHEETS + 2.4)
            lc.save(); lc.arc(lx, ly, lr, 0, 6.283); lc.clip(); lc.set_line_width(1.6)
            for k in range(6):
                if na * 6 < k + 0.2: break
                y = base_y - (k + 1) * 0.1 * PX
                lc.rectangle(lx + 8, y, lr - 10, 0.1 * PX - 2); lc.stroke()
            lc.move_to(lx - lr, base_y); lc.line_to(lx + lr, base_y); lc.stroke(); lc.restore()
            lc.set_line_width(5); lc.arc(lx, ly, lr, 0, 6.283); lc.stroke(); lc.set_line_width(14); lc.move_to(lx + lr * 0.72, ly + lr * 0.72); lc.line_to(lx + lr * 1.05, ly + lr * 1.05); lc.stroke()
            txt(lc, 'sky 0.63 mm', lx - lr * 0.5, ly - 120, 36, (0.25, 0.35, 0.55), la, fam=SERIF); txt(lc, '하늘 0.63mm', lx - lr * 0.5, ly - 78, 34, (0.25, 0.35, 0.55), la, fam=SERIF)
            if na > 0: txt(lc, f'paper ×{min(6, int(na * 6 + 0.8))}', lx + lr * 0.5, ly - 120, 36, (0.30, 0.22, 0.16), la, fam=SERIF); txt(lc, '종이 장', lx + lr * 0.5, ly - 78, 34, (0.30, 0.22, 0.16), la * na, fam=SERIF)
    img = tint(img, np.clip(blue, 0, 1), (0.45, 0.62, 0.85), 0.6)
    img = tint(img, np.clip(red, 0, 1), (0.88, 0.40, 0.33), 0.55)
    img = tint(img, np.clip(green, 0, 1), (0.55, 0.70, 0.42), 0.55)
    img = img * (1 - np.clip(ink, 0, 1)[..., None] * 0.85) + np.clip(ink, 0, 1)[..., None] * 0.85 * SEPIA
    return over(img, L)

def sound(path):
    m = S.Mix(EP['DUR'], 71); tc = EP['t_coda']; b = 60 / 92
    prog = [[220.0, 261.6, 329.6], [146.8, 220.0, 293.7], [196.0, 246.9, 293.7], [130.8, 196.0, 261.6], [174.6, 220.0, 261.6], [164.8, 207.7, 246.9]]
    t = 0.3; k = 0
    while t < tc - 0.1:
        ch = prog[(k // 8) % 6]; pat = [0, 1, 2, 1, 0, 2, 1, 2]
        m.put('mus', t, S.harpsichord(ch[pat[k % 8]] * 2, 1.0, 0.22, seed=k % 7))
        if k % 8 == 0: m.put('mus', t, S.harpsichord(ch[0], 2.0, 0.28, seed=3))
        t += b / 2; k += 1
    m.put('amb', T_PLATE - 0.3, S.breath(T_APPLE - T_PLATE, 0.35, seed=4))
    m.put('fx', T_PLATE - 0.4, S.swoosh(0.8, 0.3, 400, 3000)); m.put('fx', T_APPLE - 0.4, S.swoosh(0.8, 0.3, 400, 3000))
    m.put('fx', T_LOUPE, S.ping(1318.5, 0.3, 1.6))
    for i in range(6): m.put('fx', T_SHEETS + i * 0.4, S.tok(1500 + 60 * i, 0.25))
    for i, ch in enumerate([[220.0, 329.6, 440.0], [174.6, 261.6, 349.2], [196.0, 293.7, 392.0]]):
        for j, f in enumerate(ch): m.put('mus', tc + 0.8 + i * STEP + j * 0.08, S.harpsichord(f, 2.5, 0.25, seed=j))
    m.put('amb', tc, S.drone([110.0, 164.8], EP['t_end'] - tc, 0.12, 'sine'))
    m.write(path, rev_mus=2.4, wet_mus=0.3)

EP = finalize(dict(t_coda=T_CODA, draw=draw, sound=sound, end_icon='globe', grain=0.0,
    title_en_card='HOW THIN IS THE SKY?', title_ko_card='하늘은 얼마나 얇을까',
    pal=dict(hi=(0.25, 0.40, 0.65), endbg=PAPER),
    card_style=dict(box=None, ink=(0.30, 0.22, 0.16), hi=(0.70, 0.25, 0.18), y=150, fe=SERIF, fk=SERIF),
    cards=[(0.3, 3.8, ['If Earth were an apple,', 'how thick is *the sky*?'], ['지구가 사과라면', '*하늘*은 얼마나 두꺼울까?']),
           (4.2, 8.4, ['By a common definition,', 'space begins at *100 km*.'], ['흔히 쓰는 기준으로', '우주는 *100km* 위부터']),
           (8.8, 12.6, ['That’s only *1.6%*', 'of Earth’s radius.'], ['지구 반지름의', '*1.6%*밖에 안 된다']),
           (13.4, 18.6, ['Shrink Earth to an *8 cm* apple:', 'the sky is *0.63 mm* thick.'], ['지구를 *8cm* 사과로 줄이면', '하늘 두께는 *0.63mm*']),
           (19.0, 23.4, ['About *6 sheets of paper*.', 'All the air we breathe is in there.'], ['종이 *6장* 두께.', '우리가 숨 쉬는 공기는 다 그 안에'])],
    coda=[("Every breath you have ever taken", "당신이 쉰 모든 숨은"), ("came from a sky thinner than paper.", "종이보다 얇은 하늘에서 왔다"), ("Breathe slowly. It is borrowed.", "천천히 쉬자, 빌려 쉬는 숨이니까")],
    coda_style=dict(dim=0.75, blur=8, tint=PAPER, ink=(0.30, 0.22, 0.16), hi=(0.70, 0.25, 0.18), fe=SERIF, fk=SERIF),
    sources=['Earth mean radius 6,371 km (NASA). Kármán line 100 km (FAI convention).', 'Paper assumed 0.1 mm thick.'],
    yt=dict(title_en='If Earth Were an Apple, the Sky Would Be 0.6 mm Thick #Shorts', title_ko='지구가 사과라면 하늘 두께는 0.6mm')))

if __name__ == '__main__': main(EP)
