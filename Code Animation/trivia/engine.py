"""허상공방 지식 쇼츠(알쓸신잡풍) 엔진 — 에피소드 파일(episodes/<slug>.py)만 바꾸면 새 편이 나온다.

세로 1080×1920(디자인 픽셀), 30fps. 종이 오림 질감은 haedal/paper.py, 움직임 함수는 jamo28/mg.py를 쓴다.
모든 프레임은 t의 순수 함수: frame(ep, t) → BGR(0..1).

글자 원칙(사용자 지시 2026-11-21): 영어를 위, 한글을 바로 아래, 두 글자 크기를 비슷하게(영어 = 한글 + 4px).
긴 문장은 글자를 줄이기 전에 줄을 나누고, 그래도 넘치면 두 언어를 같은 비율로 줄인다(bi()가 강제).

에피소드 파일이 정의하는 것
  TITLE_EN, TITLE_KO      영상 제목에 쓰는 짧은 이름
  PALETTE                 dict(bg, ink, accent, accent2, card) — hex 문자열(생략하면 기본값)
  BEATS                   [dict(type=..., dur=초, ...)]  — 아래 BEAT 종류
  draw_<id>(L, t, u, ep)  (선택) 장면별 그림 함수. L: 층 dict('back','mid','near'), t: 장면 안 시각(초),
                          u: 들어옴 정도(0→1, 나감은 1→0으로 줄어듦). 좌표는 디자인 픽셀.
BEAT 종류
  hook     q_en, q_ko, [draw]              큰 질문 + 가운데 그림(없으면 큰 물음표)
  number   cap_en, cap_ko, value, fmt, unit_en, unit_ko, [alt]   숫자가 올라가며 세어짐. alt: 둘째 단위 문자열(예 '≈ 10,000 °F')
  compare  cap_en, cap_ko, items=[dict(en, ko, value, label, alt, color)], [note_en, note_ko]   종이 막대 비교
  steps    cap_en, cap_ko, items=[dict(head, en, ko)]   위에서 아래로 차례로 붙는 항목(연표·순서·목록)
  fact     cap_en, cap_ko, [draw], [sub_en, sub_ko]       문장 + 그림
  answer   a_en, a_ko, [sub_en, sub_ko], [draw]           정답 카드
마지막에 낙관·크레딧 카드(END초)가 자동으로 붙는다.
"""
import os, sys, math, importlib.util
import numpy as np, cv2, cairo

os.environ.setdefault('HD_ORIENT', 'v')
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, 'haedal'))
sys.path.insert(0, os.path.join(ROOT, 'jamo28'))
sys.path.insert(0, os.path.join(ROOT, '_kit'))
os.environ.setdefault('MG_SCALE', os.environ.get('HD_SCALE', '1'))
from mg import clamp, ramp, smooth, expo_out, expo_in_out, back_out, spring, lerp   # noqa: E402
from paper import W, H, SC, Level, composite, grain, hexc, tex                     # noqa: E402
import shapes as S                                                                   # noqa: E402
from vfx import post as POST                                                        # noqa: E402
from vfx.timeline import Beat                                                       # noqa: E402

FPS = 30
DW, DH = 1080, 1920
SERIF = 'Noto Serif CJK KR'
BOLD, NORMAL = cairo.FONT_WEIGHT_BOLD, cairo.FONT_WEIGHT_NORMAL
END = 4.2                     # 끝 카드 길이
TR = 0.55                     # 장면 넘김(들어옴·나감) 시간
OV = 0.35                     # 다음 장면이 앞 장면 끝과 겹쳐 들어오는 시간(빈 종이만 보이는 틈을 없앰)
BEAT = Beat(bpm=120, beats_per_bar=4, fps=FPS)   # 그림·소리가 함께 읽는 박자표(반 박 = 0.25초)
EV0 = 0.5                     # 장면 안 첫 사건 시각(박 위)
MAXW = 920                    # 글 한 줄 최대 폭
DEFAULT_PAL = dict(bg='#EFE6D2', ink='#22201C', accent='#E0442E', accent2='#2F6F8F', card='#FBF6EA', muted='#8A8172')


# ---------------------------------------------------------------- 에피소드 읽기
class Episode:
    def __init__(self, slug):
        p = slug if slug.endswith('.py') else os.path.join(HERE, 'episodes', slug + '.py')
        spec = importlib.util.spec_from_file_location('ep_' + os.path.basename(p)[:-3], p)
        m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
        self.m = m
        self.slug = os.path.basename(p)[:-3]
        self.pal = {k: hexc(v) for k, v in {**DEFAULT_PAL, **getattr(m, 'PALETTE', {})}.items()}
        self.beats = []
        t = 0.0
        for i, b in enumerate(m.BEATS):
            b = dict(b); b.setdefault('id', f'b{i}'); b['t0'] = t; b['t1'] = t + b['dur']; t = b['t1']
            self.beats.append(b)
        self.T_END = t
        self.DUR = t + END

    def beat_at(self, t):
        for b in self.beats:
            if b['t0'] <= t < b['t1']: return b
        return None

    def draw_fn(self, b):
        name = b.get('draw') or f"draw_{b['id']}"
        return getattr(self.m, name, None)


# ---------------------------------------------------------------- 글자
def _font(cr, size, weight):
    cr.select_font_face(SERIF, cairo.FONT_SLANT_NORMAL, weight); cr.set_font_size(size)


def wrap(cr, s, size, weight, maxw=MAXW):
    """공백 기준 줄 나눔(명시한 \\n 우선)."""
    _font(cr, size, weight)
    out = []
    for para in s.split('\n'):
        words, line = para.split(' '), ''
        for w in words:
            cand = (line + ' ' + w).strip()
            if cr.text_extents(cand).x_advance <= maxw or not line: line = cand
            else: out.append(line); line = w
        out.append(line)
    return out


def widest(cr, lines, size, weight):
    _font(cr, size, weight); return max(cr.text_extents(l).x_advance for l in lines) if lines else 0


def text_line(cr, s, x, y, size, rgb, a=1.0, weight=NORMAL, anchor='c'):
    if a <= 0 or not s: return
    cr.save(); _font(cr, size, weight)
    e = cr.text_extents(s); dx = {'l': 0, 'c': -e.x_advance / 2, 'r': -e.x_advance}[anchor]
    cr.move_to(x + dx, y); cr.text_path(s); cr.set_source_rgba(*rgb, a); cr.fill(); cr.restore()


def bi_layout(cr, en, ko, size, weight=BOLD, maxw=MAXW, max_lines=3):
    """영어(위)·한글(아래) 배치를 계산: 크기 비슷(EN=size, KO=size-4). 넘치면 같이 줄인다."""
    s = size
    while True:
        se, sk = s, max(12, s - 4)
        le = wrap(cr, en, se, weight, maxw) if en else []
        lk = wrap(cr, ko, sk, weight, maxw) if ko else []
        if (len(le) <= max_lines and len(lk) <= max_lines) or s <= 26: break
        s -= 2
    gap_l, gap_b = 0.22, 0.42                      # 줄 사이(글자 크기 비율), 두 언어 사이
    h = len(le) * se * (1 + gap_l) + (gap_b * se if le and lk else 0) + len(lk) * sk * (1 + gap_l)
    w = max(widest(cr, le, se, weight) if le else 0, widest(cr, lk, sk, weight) if lk else 0)
    return dict(le=le, lk=lk, se=se, sk=sk, h=h, w=w, weight=weight, gl=gap_l, gb=gap_b)


def bi_draw(cr, lay, x, ytop, rgb_en, rgb_ko=None, a=1.0, anchor='c'):
    rgb_ko = rgb_ko or rgb_en
    y = ytop
    for l in lay['le']:
        y += lay['se']; text_line(cr, l, x, y - lay['se'] * 0.18, lay['se'], rgb_en, a, lay['weight'], anchor); y += lay['se'] * lay['gl']
    if lay['le'] and lay['lk']: y += lay['gb'] * lay['se']
    for l in lay['lk']:
        y += lay['sk']; text_line(cr, l, x, y - lay['sk'] * 0.18, lay['sk'], rgb_ko, a, lay['weight'], anchor); y += lay['sk'] * lay['gl']
    return y


def card(cr, x, y, w, h, rgb, r=26, a=1.0):
    """종이 카드(모서리 둥근 사각형) 경로 + 칠."""
    cr.new_sub_path()
    cr.arc(x + w - r, y + r, r, -math.pi / 2, 0); cr.arc(x + w - r, y + h - r, r, 0, math.pi / 2)
    cr.arc(x + r, y + h - r, r, math.pi / 2, math.pi); cr.arc(x + r, y + r, r, math.pi, 1.5 * math.pi)
    cr.close_path(); cr.set_source_rgba(*rgb, a); cr.fill()


def cap_card(L, ep, en, ko, ytop, size=60, pad=34, u=1.0):
    """위쪽 설명 카드(카드는 mid 층, 글자는 type 층). 높이 반환."""
    cr = L['type']; lay = bi_layout(cr, en, ko, size)
    w, h = min(DW - 80, lay['w'] + pad * 2), lay['h'] + pad * 2
    x = (DW - w) / 2
    card(L['card'], x, ytop, w, h, ep.pal['card'])
    bi_draw(cr, lay, DW / 2, ytop + pad, ep.pal['ink'])
    return h


def fmt_num(v, fmt):
    if callable(fmt): return fmt(v)
    return fmt.format(v)


# ---------------------------------------------------------------- 장면 넘김
def enter_exit(b, t, first=False):
    """들어옴 u_in(0→1), 나감 u_out(0→1). 첫 장면이 아니면 앞 장면 끝 OV초 전부터 들어온다."""
    lt = t - b['t0']; d = b['dur']
    u_in = clamp(lt / TR) if first else clamp((lt + OV) / TR)
    u_out = clamp((lt - (d - TR * 0.8)) / (TR * 0.8))
    return u_in, u_out


def slide_dx(u_in, u_out):
    return (1 - spring(u_in, zeta=0.55, freq=1.6)) * 1150 - expo_in_out(u_out) * 1150


# ---------------------------------------------------------------- 장면 그리기
def draw_hook(L, ep, b, lt, u):
    h = cap_card(L, ep, b['q_en'], b['q_ko'], 230, size=b.get('size', 72), pad=40)
    fn = ep.draw_fn(b)
    if fn: fn(L, lt, u, ep)
    else:
        cr = L['near']; s = 1 + 0.04 * math.sin(lt * 3)
        cr.save(); cr.translate(DW / 2, 1130); cr.scale(s, s)
        text_line(cr, '?', 0, 170, 520, ep.pal['accent'], 1.0, BOLD); cr.restore()
    tag = L['type']
    text_line(tag, 'Dreamloom Studio · 허상공방', DW / 2, 160, 28, ep.pal['muted'], 0.9)


def draw_number(L, ep, b, lt, u):
    cap_card(L, ep, b['cap_en'], b['cap_ko'], 230, size=b.get('size', 60))
    fn = ep.draw_fn(b)
    if fn: fn(L, lt, u, ep)
    k = expo_out(clamp((lt - 0.5) / max(0.6, b.get('count', 1.8))))
    v = b['value'] * k
    cy = b.get('y', 1250); ns = b.get('num_size', 190)
    lay = bi_layout(L['type'], b.get('unit_en', ''), b.get('unit_ko', ''), 46)
    y_unit = cy + 40; y_alt = y_unit + lay['h'] + 52
    bottom = (y_alt + 16) if b.get('alt') else (y_unit + lay['h'] + 10)
    card(L['card'], 110, cy - ns * 0.95, DW - 220, bottom - (cy - ns * 0.95) + 44, ep.pal['card'])
    text_line(L['type'], fmt_num(v, b.get('fmt', '{:,.0f}')), DW / 2, cy, ns, ep.pal['accent'], 1.0, BOLD)
    bi_draw(L['type'], lay, DW / 2, y_unit, ep.pal['ink'], a=smooth(ramp(lt, 0.8, 1.3)))
    if b.get('alt'):
        text_line(L['type'], b['alt'], DW / 2, y_alt, 42, ep.pal['muted'], smooth(ramp(lt, 1.6, 2.1)), BOLD)


def draw_compare(L, ep, b, lt, u):
    h = cap_card(L, ep, b['cap_en'], b['cap_ko'], 230, size=b.get('size', 58))
    items = b['items']; n = len(items)
    base_y, top_y = b.get('base_y', 1560), 230 + h + 230
    vmax = max(it['value'] for it in items)
    span = DW - 200; bw = min(250, span / n * 0.62)
    for i, it in enumerate(items):
        cx = 100 + span * (i + 0.5) / n
        t0 = EV0 + i * b.get('stagger', 1.5)
        g = spring(clamp((lt - t0) / 1.1), zeta=0.6, freq=1.4)
        hh = (base_y - top_y) * it['value'] / vmax * g
        col = hexc(it['color']) if isinstance(it.get('color'), str) else (it.get('color') or (ep.pal['accent'] if i == n - 1 else ep.pal['accent2']))
        if hh > 1:
            card(L['mid'], cx - bw / 2, base_y - hh, bw, hh + 18, col, r=18)
        # 값(막대 위)
        a = smooth(ramp(lt, t0 + 0.3, t0 + 0.8))
        v = it['value'] * expo_out(clamp((lt - t0) / 1.1))
        text_line(L['type'], fmt_num(v, it.get('fmt', b.get('fmt', '{:,.0f}'))), cx, base_y - hh - 64, it.get('vsize', 56), ep.pal['ink'], a, BOLD)
        if it.get('alt'): text_line(L['type'], it['alt'], cx, base_y - hh - 22, 32, ep.pal['muted'], a)
        # 이름(막대 아래, 영·한 같은 크기)
        lay = bi_layout(L['type'], it['en'], it['ko'], it.get('lsize', 40), maxw=span / n - 20, max_lines=2)
        bi_draw(L['type'], lay, cx, base_y + 40, ep.pal['ink'], a=smooth(ramp(lt, t0, t0 + 0.4)))
    # 바닥 띠
    card(L['mid'], 70, base_y + 4, DW - 140, 16, ep.pal['ink'], r=8, a=0.85)
    if b.get('note_en') or b.get('note_ko'):
        a = smooth(ramp(lt, b.get('note_t', b['dur'] - 2.4), b.get('note_t', b['dur'] - 2.4) + 0.5))
        if a > 0:
            lay = bi_layout(L['type'], b.get('note_en', ''), b.get('note_ko', ''), 56)
            y = base_y + 230
            card(L['near'], (DW - lay['w']) / 2 - 30, y - 24, lay['w'] + 60, lay['h'] + 48, ep.pal['accent'], a=a)
            bi_draw(L['type'], lay, DW / 2, y, (1, 1, 1), a=a)
    fn = ep.draw_fn(b)
    if fn: fn(L, lt, u, ep)


def draw_steps(L, ep, b, lt, u):
    h = cap_card(L, ep, b['cap_en'], b['cap_ko'], 230, size=b.get('size', 58))
    items = b['items']; n = len(items)
    y = 230 + h + 90; gap = b.get('gap', 40)
    x_head = 150
    for i, it in enumerate(items):
        t0 = EV0 + i * b.get('stagger', 1.5)
        a = smooth(ramp(lt, t0, t0 + 0.45))
        if a <= 0: break
        off = (1 - expo_out(ramp(lt, t0, t0 + 0.6))) * 60
        lay = bi_layout(L['type'], it['en'], it['ko'], it.get('size', 44), weight=NORMAL, maxw=DW - 420, max_lines=3)
        hh = max(lay['h'], 90) + 50
        card(L['card'], 80, y + off, DW - 160, hh, ep.pal['card'], a=a)
        S.circle(L['mid'], x_head, y + off + hh / 2, 52); S.fill(L['mid'], ep.pal['accent'] if i == n - 1 else ep.pal['accent2'], a)
        text_line(L['type'], str(it.get('head', i + 1)), x_head, y + off + hh / 2 + 15, it.get('head_size', 40), (1, 1, 1), a, BOLD)
        bi_draw(L['type'], lay, 240, y + off + (hh - lay['h']) / 2, ep.pal['ink'], a=a, anchor='l')
        y += hh + gap
    fn = ep.draw_fn(b)
    if fn: fn(L, lt, u, ep)


def draw_fact(L, ep, b, lt, u):
    h = cap_card(L, ep, b['cap_en'], b['cap_ko'], 230, size=b.get('size', 58))
    fn = ep.draw_fn(b)
    if fn: fn(L, lt, u, ep)
    if b.get('sub_en') or b.get('sub_ko'):
        a = smooth(ramp(lt, b.get('sub_t', 1.2), b.get('sub_t', 1.2) + 0.5))
        lay = bi_layout(L['type'], b.get('sub_en', ''), b.get('sub_ko', ''), b.get('sub_size', 46), weight=NORMAL)
        y = b.get('sub_y', 1560)
        card(L['card'], (DW - lay['w']) / 2 - 30, y - 26, lay['w'] + 60, lay['h'] + 52, ep.pal['card'], a=a)
        bi_draw(L['type'], lay, DW / 2, y, ep.pal['ink'], a=a)


def draw_answer(L, ep, b, lt, u):
    fn = ep.draw_fn(b)
    if fn: fn(L, lt, u, ep)
    lay = bi_layout(L['type'], b['a_en'], b['a_ko'], b.get('size', 80))
    y = b.get('y', 640)
    pop = back_out(clamp((lt - 0.25) / 0.5))
    w, h = lay['w'] + 90, lay['h'] + 90
    cr = L['near']; cr.save(); cr.translate(DW / 2, y + h / 2); cr.scale(pop, pop); cr.translate(-DW / 2, -(y + h / 2))
    card(cr, (DW - w) / 2, y, w, h, ep.pal['accent'])
    cr.restore()
    ty = L['type']; ty.save(); ty.translate(DW / 2, y + h / 2); ty.scale(pop, pop); ty.translate(-DW / 2, -(y + h / 2))
    bi_draw(ty, lay, DW / 2, y + 45, (1, 1, 1)); ty.restore()
    if b.get('sub_en') or b.get('sub_ko'):
        a = smooth(ramp(lt, 1.0, 1.5))
        lay2 = bi_layout(L['type'], b.get('sub_en', ''), b.get('sub_ko', ''), 46, weight=NORMAL)
        y2 = y + h + 70
        card(L['card'], (DW - lay2['w']) / 2 - 30, y2 - 26, lay2['w'] + 60, lay2['h'] + 52, ep.pal['card'], a=a)
        bi_draw(L['type'], lay2, DW / 2, y2, ep.pal['ink'], a=a)


DRAW = dict(hook=draw_hook, number=draw_number, compare=draw_compare, steps=draw_steps, fact=draw_fact, answer=draw_answer)


# ---------------------------------------------------------------- 배경(떠다니는 종이 조각)
def draw_bg(L, ep, t):
    rng = np.random.default_rng(5)
    cr = L['back']
    for k in range(14):
        x0, y0 = rng.uniform(0, DW), rng.uniform(0, DH)
        r = rng.uniform(14, 40); sp = rng.uniform(6, 18); ph = rng.uniform(0, 6.3)
        x = (x0 + 12 * math.sin(t * 0.4 + ph)) % DW
        y = (y0 - sp * t) % (DH + 100) - 50
        col = [ep.pal['accent'], ep.pal['accent2'], ep.pal['muted']][k % 3]
        if k % 2: S.circle(cr, x, y, r)
        else:
            a = t * 0.3 + ph
            S.poly(cr, [(x + r * math.cos(a + j * 2.094), y + r * math.sin(a + j * 2.094)) for j in range(3)])
        S.fill(cr, col, 0.22)


# ---------------------------------------------------------------- 합성
LEVELS = [('back', 0.4, 0.14), ('mid', 1.2, 0.30), ('card', 0.9, 0.26), ('near', 1.8, 0.30), ('type', 0.25, 0.16)]


def draw_all(ep, t, L):
    Lc = {n: L[n].cr for n in L}
    draw_bg(Lc, ep, t)
    names = [n for n, *_ in LEVELS if n != 'back']
    par = {'mid': 1.0, 'card': 1.0, 'near': 1.15, 'type': 1.0}
    for k, b in enumerate(ep.beats):
        first = k == 0
        if not ((b['t0'] - (0 if first else OV)) <= t < b['t1']): continue
        lt = t - b['t0']
        u_in, u_out = enter_exit(b, t, first)
        dx = -expo_in_out(u_out) * 1150 + (0 if first else (1 - back_out(u_in, 0.9)) * 1150)
        dy = (1 - back_out(u_in, 0.9)) * 260 if first else 0
        for n in names: L[n].cr.save(); L[n].cr.translate(dx * par[n], dy)
        DRAW[b['type']](Lc, ep, b, lt, u_in * (1 - u_out))
        for n in names: L[n].cr.restore()


def in_transition(ep, t):
    """장면이 들어오거나 나가는 중인가(빠른 움직임 → 하위 프레임을 늘려 모션 블러)."""
    for k, b in enumerate(ep.beats):
        if (b['t0'] - (0 if k == 0 else OV)) <= t < b['t0'] + TR or (b['t1'] - TR * 0.8) <= t < b['t1']: return True
    return False


def frame(ep, t, samples=None, shutter=0.5):
    if samples is None: samples = 6 if in_transition(ep, t) else 1       # 멈춘 화면은 1장, 넘김은 6장 평균
    names = [n for n, *_ in LEVELS]
    acc = {}
    for si in range(samples):
        tt = t + ((si + 0.5) / samples - 0.5) * shutter / FPS if samples > 1 else t
        L = {n: Level() for n in names}
        draw_all(ep, tt, L)
        for n in names:
            a = L[n].array(); acc[n] = a if n not in acc else acc[n] + a
    for n in acc: acc[n] /= samples
    base = np.empty((H, W, 3), np.float32); base[:] = np.array(ep.pal['bg'][::-1], np.float32)
    base *= tex()[..., None]
    for n, dep, sh in LEVELS:
        base = composite(base, acc[n], dep, sh)
    return np.clip(base, 0, 1)


_VIG = None
def vignette():
    global _VIG
    if _VIG is None:
        y, x = np.mgrid[0:H, 0:W].astype(np.float32)
        r = np.hypot((x - W / 2) / (W / 2), (y - H / 2) / (H / 2))
        _VIG = (1 - 0.18 * np.clip(r - 0.55, 0, 1) ** 1.4)[..., None].astype(np.float32)
    return _VIG


CREDIT = ['Created & Coded by L.S.M.', 'Dreamloom Studio · 허상공방 虛像工房']
_credit = {}
def credit_layer():
    if _credit: return _credit['v']
    from PIL import Image, ImageDraw, ImageFont
    S2 = 2.0 * SC
    fnt = ImageFont.truetype('/usr/share/fonts/opentype/noto/NotoSerifCJK-Regular.ttc', int(19 * S2), index=1)
    sz = int(round(130 * SC)); cx, cy = 540, 800
    xs, ys = int(round(cx * SC)) - sz // 2, int(round(cy * SC))
    im = Image.new('L', (W, H), 0); d = ImageDraw.Draw(im)
    d.text((int(cx * SC), ys + sz + int(32 * S2)), CREDIT[0], font=fnt, fill=255, anchor='mm')
    d.text((int(cx * SC), ys + sz + int(62 * S2)), CREDIT[1], font=fnt, fill=255, anchor='mm')
    tm = cv2.GaussianBlur(np.asarray(im, np.float32) / 255, (0, 0), 0.35 * S2)
    seal = np.load(os.path.join(ROOT, '_shared', 'seal_baimun3.npy')).astype(np.float32)
    seal = cv2.resize(seal, (sz, sz), interpolation=cv2.INTER_AREA)[..., [2, 1, 0, 3]]
    _credit['v'] = (tm, seal, xs, ys, sz); return _credit['v']


def end_card(ep, img, t):
    T = ep.T_END
    if t < T - 0.3: return img
    u = smooth(ramp(t, T - 0.3, T + 0.5))
    paper = np.array(ep.pal['bg'][::-1], np.float32) * tex()[..., None]
    img = img * (1 - u) + paper * u
    ts = T + 0.6
    if t < ts: return img
    tm, seal, xs, ys, sz = credit_layer()
    a1 = smooth(ramp(t, ts, ts + 0.2))
    red = np.clip((seal[..., 2:3] - seal[..., 1:2]) * 4, 0, 1)
    al = seal[..., 3:4] * a1 * red
    sub = img[ys:ys + sz, xs:xs + sz]; img[ys:ys + sz, xs:xs + sz] = sub * (1 - al + al * seal[..., :3])
    a2 = smooth(ramp(t, ts + 0.5, ts + 1.4)); k = (tm * a2 * 0.92)[..., None]
    return img * (1 - k) + np.array(ep.pal['ink'][::-1], np.float32) * k


LOOK = dict(sat=1.06, split=((0.03, 0.012, -0.012), (-0.008, 0.004, 0.02), 0.5), s_curve=0.18, vignette=0.14, grain=0.008)


def final(ep, t, samples=None, look=True):
    img = frame(ep, t, samples)
    img = end_card(ep, img, t)
    if not look: return grain(img * vignette(), int(t * FPS), 0.008)
    return POST.grade(img, seed=int(t * FPS), **{**LOOK, **getattr(ep.m, 'LOOK', {})})


def beat_marks(ep):
    """소리용 시각표: [(시각, 종류, beat)]."""
    out = []
    for b in ep.beats:
        out.append((b['t0'], 'in', b))
        if b['type'] == 'compare':
            for i, it in enumerate(b['items']): out.append((b['t0'] + EV0 + i * b.get('stagger', 1.5), 'grow', b))
            if b.get('note_en') or b.get('note_ko'): out.append((b['t0'] + b.get('note_t', b['dur'] - 2.4), 'hit', b))
        elif b['type'] == 'number': out.append((b['t0'] + 0.5, 'count', b))
        elif b['type'] == 'steps':
            for i in range(len(b['items'])): out.append((b['t0'] + EV0 + i * b.get('stagger', 1.5), 'tick', b))
        elif b['type'] == 'answer': out.append((b['t0'] + 0.25, 'hit', b))
    out.append((ep.T_END + 0.6, 'seal', None))
    return out
