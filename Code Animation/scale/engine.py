"""허상공방 규모 체감 쇼츠 엔진(세로 1080×1920 디자인 픽셀). 겹 종이 질감: 층마다 그림자, 종이 결, 윗가장자리 밝은 선.

틀 세 가지
- Ladder : 로그 눈금을 따라 종이 탑이 자라며 올라간다(시간·개수·거리).
- Spheres: 같은 축척의 원(구)을 놓고 카메라가 줌한다(크기 비교).
- Tiles  : 칸(달·시간·분·초, 해) 격자를 채우고 마지막 칸으로 파고든다.

모든 프레임은 t의 순수 함수(씨앗 고정). 에피소드 정의는 episodes.py.
"""
import os, math
import numpy as np, cv2, cairo

SC = float(os.environ.get('MG_SCALE', '1')); FPS = int(os.environ.get('MG_FPS', '30'))
DW, DH = 1080, 1920
W, H = int(round(DW * SC)), int(round(DH * SC))
CACHE = '/home/claude/work/cache'; os.makedirs(CACHE, exist_ok=True)
BLK = 'Noto Sans CJK KR Black'; BOLD = 'Noto Sans CJK KR'; SERIF = 'Noto Serif CJK KR'
INK = (0.12, 0.11, 0.10)


# ------------------------------------------------ 시간 곡선
def clamp(x, a=0.0, b=1.0): return a if x < a else b if x > b else x
def ramp(t, a, b): return clamp((t - a) / (b - a)) if b > a else float(t >= a)
def smooth(u): return u * u * (3 - 2 * u)
def expo_out(u): return 1 - 2 ** (-10 * u) if u < 1 else 1.0
def expo_in_out(u):
    if u <= 0: return 0.0
    if u >= 1: return 1.0
    return 2 ** (20 * u - 10) / 2 if u < 0.5 else (2 - 2 ** (-20 * u + 10)) / 2
def back_out(u, s=1.7): u -= 1; return 1 + (s + 1) * u ** 3 + s * u ** 2
def lerp(a, b, u): return a + (b - a) * u
def sine_io(u): u = clamp(u); return 0.5 - 0.5 * math.cos(math.pi * u)
def mix(a, b, u): return tuple(lerp(x, y, u) for x, y in zip(a, b))
def hexc(h): h = h.lstrip('#'); return tuple(int(h[i:i + 2], 16) / 255 for i in (0, 2, 4))


# ------------------------------------------------ 종이 결
_TEX = {}
def paper_tex():
    if 'v' in _TEX: return _TEX['v']
    fn = f'{CACHE}/scale_tex_{W}x{H}.npy'
    if os.path.exists(fn): _TEX['v'] = np.load(fn); return _TEX['v']
    rng = np.random.default_rng(7)
    fine = cv2.GaussianBlur(rng.standard_normal((H, W)).astype(np.float32), (0, 0), max(0.6, 0.8 * SC))
    blot = cv2.resize(rng.standard_normal((H // 90 + 3, W // 90 + 3)).astype(np.float32), (W, H), interpolation=cv2.INTER_CUBIC)
    fib = np.zeros((H, W), np.float32)
    for _ in range(int(5200 * SC * SC) + 400):
        x, y = rng.uniform(0, W), rng.uniform(0, H); a = rng.uniform(0, math.pi); L = rng.uniform(6, 26) * SC
        cv2.line(fib, (int(x), int(y)), (int(x + L * math.cos(a)), int(y + L * math.sin(a))), float(rng.uniform(0.3, 1)), 1, cv2.LINE_AA)
    fib = cv2.GaussianBlur(fib, (0, 0), 0.6 * max(SC, 0.6))
    tex = (1 + 0.045 * fine / fine.std() * 0.5 + 0.022 * blot / blot.std() - 0.05 * fib).astype(np.float32)
    np.save(fn, tex); _TEX['v'] = tex; return tex


# ------------------------------------------------ 층(종이 한 장)
class Layer:
    def __init__(self, depth=1.0):
        self.depth = depth
        self.surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H)
        self.cr = cairo.Context(self.surf); self.cr.scale(SC, SC)
        self.cr.set_line_join(cairo.LINE_JOIN_ROUND); self.cr.set_line_cap(cairo.LINE_CAP_ROUND)

    def arr(self):
        self.surf.flush(); st = self.surf.get_stride()
        a = np.frombuffer(self.surf.get_data(), np.uint8).reshape(H, st // 4, 4)[:, :W]
        return a.astype(np.float32) / 255.0                     # BGRA, 미리 곱한 알파


def composite(base, layer):
    a = layer.arr(); al = a[..., 3]
    if al.max() <= 0: return base
    d = layer.depth
    if d > 0:
        sig = max(0.8, d * 6.5 * SC)
        sh = cv2.GaussianBlur(al, (0, 0), sig)
        dx, dy = int(round(d * 3 * SC)), int(round(d * 8 * SC))
        sh = np.roll(np.roll(sh, dy, 0), dx, 1)
        base = base * (1 - 0.40 * np.minimum(1, sh * 1.1))[..., None]
    base = base * (1 - al[..., None]) + a[..., :3]
    if d > 0:                                                   # 잘린 종이 윗가장자리의 밝은 선
        k = max(1, int(round(1.6 * SC)))
        edge = np.clip(al - np.roll(al, k, 0), 0, 1)
        base = base + edge[..., None] * 0.10
    return base


def finish(img, t):
    img = img * paper_tex()[..., None]
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    if 'vig' not in _TEX:
        r = np.sqrt(((xx - W / 2) / (W * 0.62)) ** 2 + ((yy - H / 2) / (H * 0.62)) ** 2)
        _TEX['vig'] = (1 - 0.16 * np.clip(r - 0.55, 0, 1) ** 1.4)[..., None].astype(np.float32)
    img = img * _TEX['vig']
    rng = np.random.default_rng(int(t * FPS) + 11)
    img = img + rng.standard_normal((H, W, 1)).astype(np.float32) * 0.008
    return np.clip(img, 0, 1)


# ------------------------------------------------ 글자
def txt(cr, s, x, y, size, col, a=1.0, fam=BLK, anchor='c', maxw=None):
    if a <= 0 or not s: return 0
    cr.select_font_face(fam, cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD if fam == BOLD else cairo.FONT_WEIGHT_NORMAL)
    cr.set_font_size(size); w = cr.text_extents(s).x_advance
    if maxw and w > maxw: size *= maxw / w; cr.set_font_size(size); w = maxw
    x0 = x - {'l': 0, 'c': w / 2, 'r': w}[anchor]
    cr.move_to(x0, y); cr.set_source_rgba(*col, a); cr.show_text(s); cr.new_path()
    return w

def runs(cr, s, cx, y, size, col, hi, a, fam=BLK, maxw=960):
    """'*강조*'가 섞인 한 줄을 가운데 정렬."""
    if a <= 0: return
    parts = s.split('*'); cr.select_font_face(fam, 0, 0); cr.set_font_size(size)
    w = sum(cr.text_extents(p).x_advance for p in parts)
    if w > maxw: size *= maxw / w; cr.set_font_size(size); w = maxw
    x = cx - w / 2
    for i, p in enumerate(parts):
        cr.move_to(x, y); cr.set_source_rgba(*(hi if i % 2 else col), a); cr.show_text(p); x += cr.text_extents(p).x_advance
    cr.new_path()

def rrect(cr, x, y, w, h, r):
    r = max(0.1, min(r, w / 2, h / 2)); cr.new_sub_path()
    cr.arc(x + w - r, y + r, r, -math.pi / 2, 0); cr.arc(x + w - r, y + h - r, r, 0, math.pi / 2)
    cr.arc(x + r, y + h - r, r, math.pi / 2, math.pi); cr.arc(x + r, y + r, r, math.pi, 1.5 * math.pi); cr.close_path()

def card_alpha(t, t0, t1): return ramp(t, t0, t0 + 0.22) * (1 - ramp(t, t1 - 0.22, t1))

def draw_card(cr, t, c, pal):
    """c = (t0, t1, [영어 줄], [한글 줄], y). 종이 띠 위에 영어 위·한글 아래, 크기 비슷."""
    t0, t1, en, ko = c[:4]; y = c[4] if len(c) > 4 else 170
    a = card_alpha(t, t0, t1)
    if a <= 0: return
    se = 62 if len(en) > 1 else 66; sk = 56 if len(ko) > 1 else 60
    hgt = 44 + len(en) * se * 1.18 + 14 + len(ko) * sk * 1.22
    k = expo_out(ramp(t, t0, t0 + 0.4))
    cr.save(); cr.translate(0, (1 - k) * -40)
    cr.set_source_rgba(*pal['card'], 0.94 * a); rrect(cr, 50, y - 4, DW - 100, hgt, 26); cr.fill()
    yy = y + se + 14
    for ln in en: runs(cr, ln, DW / 2, yy, se, pal['cardink'], pal['hi'], a); yy += se * 1.18
    yy += 8
    for ln in ko: runs(cr, ln, DW / 2, yy, sk, pal['cardink'], pal['hi'], a); yy += sk * 1.22
    cr.restore()


# ------------------------------------------------ 그림 글자(아이콘): 중심 (x, y), 크기 s
def icon(cr, name, x, y, s, col, bg):
    cr.save(); cr.translate(x, y); cr.scale(s / 100, s / 100); cr.set_source_rgb(*col); cr.set_line_width(9)
    def circ(cx, cy, r, fill=True):
        cr.arc(cx, cy, r, 0, 2 * math.pi); cr.fill() if fill else cr.stroke()
    if name == 'clock':
        circ(0, 0, 40, False); cr.move_to(0, 0); cr.line_to(0, -26); cr.move_to(0, 0); cr.line_to(18, 8); cr.stroke()
    elif name == 'calendar':
        rrect(cr, -38, -30, 76, 68, 10); cr.stroke(); cr.rectangle(-38, -30, 76, 18); cr.fill()
        for i in range(3):
            for j in range(2): cr.rectangle(-24 + i * 18, 0 + j * 16, 10, 10); cr.fill()
    elif name == 'heart':
        cr.move_to(0, 36); cr.curve_to(-60, -4, -30, -52, 0, -18); cr.curve_to(30, -52, 60, -4, 0, 36); cr.fill()
    elif name == 'person':
        circ(0, -26, 15); rrect(cr, -20, -6, 40, 46, 16); cr.fill()
    elif name == 'people':
        for dx, sz in ((-26, 0.8), (26, 0.8), (0, 1.0)):
            circ(dx, -24 * sz, 12 * sz); rrect(cr, dx - 16 * sz, -6 * sz, 32 * sz, 40 * sz, 13 * sz); cr.fill()
    elif name == 'globe':
        circ(0, 0, 40, False); cr.save(); cr.scale(0.45, 1); circ(0, 0, 40, False); cr.restore()
        cr.move_to(-40, 0); cr.line_to(40, 0); cr.stroke()
    elif name == 'moon':
        cr.push_group(); circ(0, 0, 38); cr.set_operator(cairo.OPERATOR_CLEAR); circ(18, -12, 32); cr.pop_group_to_source(); cr.paint()
    elif name == 'sun':
        circ(0, 0, 22)
        for i in range(8):
            a = i * math.pi / 4; cr.move_to(32 * math.cos(a), 32 * math.sin(a)); cr.line_to(44 * math.cos(a), 44 * math.sin(a))
        cr.stroke()
    elif name == 'star':
        for i in range(10):
            r = 42 if i % 2 == 0 else 18; a = -math.pi / 2 + i * math.pi / 5
            (cr.move_to if i == 0 else cr.line_to)(r * math.cos(a), r * math.sin(a))
        cr.close_path(); cr.fill()
    elif name == 'brain':
        for cx, cy, r in ((-16, -8, 22), (14, -12, 22), (-4, 14, 22), (22, 12, 16)): circ(cx, cy, r)
        cr.set_source_rgb(*bg); cr.set_line_width(5); cr.move_to(0, -30); cr.curve_to(-8, -6, 8, 6, 0, 32); cr.stroke()
    elif name == 'ant':
        for cx, r in ((-28, 11), (0, 13), (30, 17)): circ(cx, 0, r)
        cr.set_line_width(5)
        for dx in (-6, 2, 10):
            cr.move_to(dx, 0); cr.line_to(dx - 14, -26); cr.move_to(dx, 0); cr.line_to(dx - 14, 26)
        cr.move_to(-34, -8); cr.line_to(-46, -28); cr.stroke()
    elif name == 'bolt':
        for i, (px, py) in enumerate(((8, -44), (-22, 6), (-2, 6), (-10, 44), (22, -8), (2, -8))): (cr.move_to if i == 0 else cr.line_to)(px, py)
        cr.close_path(); cr.fill()
    elif name == 'scroll':
        rrect(cr, -30, -36, 60, 72, 8); cr.stroke()
        for i in range(4): cr.move_to(-18, -18 + i * 14); cr.line_to(18, -18 + i * 14)
        cr.stroke()
    elif name == 'wheat':
        cr.move_to(0, 44); cr.line_to(0, -40); cr.stroke()
        for i in range(4):
            yy = -30 + i * 16
            for sgn in (-1, 1):
                cr.save(); cr.translate(sgn * 10, yy); cr.rotate(sgn * 0.6); cr.scale(0.5, 1); circ(0, 0, 11); cr.restore()
    elif name == 'dino':
        cr.move_to(-44, 26); cr.curve_to(-30, -4, -6, -10, 10, -8); cr.line_to(22, -34); cr.line_to(40, -34); cr.line_to(40, -22); cr.line_to(26, -18)
        cr.curve_to(30, 6, 18, 18, 8, 20); cr.line_to(8, 36); cr.line_to(-2, 36); cr.line_to(-4, 22); cr.line_to(-18, 22); cr.line_to(-20, 36)
        cr.line_to(-30, 36); cr.line_to(-28, 24); cr.close_path(); cr.fill()
    elif name == 'bed':
        cr.rectangle(-44, 4, 88, 18); cr.fill(); cr.rectangle(-44, -24, 10, 54); cr.fill(); circ(-20, -6, 10); rrect(cr, -8, -12, 50, 16, 8); cr.fill()
    elif name == 'drop':
        cr.move_to(0, -42); cr.curve_to(30, -4, 34, 14, 26, 26); cr.curve_to(14, 44, -14, 44, -26, 26); cr.curve_to(-34, 14, -30, -4, 0, -42); cr.fill()
    elif name == 'rocket':
        cr.move_to(0, -44); cr.curve_to(22, -20, 18, 18, 12, 28); cr.line_to(-12, 28); cr.curve_to(-18, 18, -22, -20, 0, -44); cr.fill()
        cr.move_to(-12, 14); cr.line_to(-26, 34); cr.line_to(-10, 28); cr.fill(); cr.move_to(12, 14); cr.line_to(26, 34); cr.line_to(10, 28); cr.fill()
    elif name == 'plane':
        cr.move_to(-44, 0); cr.line_to(44, 0); cr.set_line_width(12); cr.stroke()
        cr.move_to(4, 0); cr.line_to(-14, -34); cr.line_to(-4, -34); cr.line_to(22, 0); cr.line_to(-4, 34); cr.line_to(-14, 34); cr.close_path(); cr.fill()
    elif name == 'mountain':
        cr.move_to(-46, 34); cr.line_to(-8, -34); cr.line_to(10, -6); cr.line_to(22, -20); cr.line_to(46, 34); cr.close_path(); cr.fill()
    elif name == 'house':
        cr.move_to(-40, -2); cr.line_to(0, -38); cr.line_to(40, -2); cr.close_path(); cr.fill(); cr.rectangle(-28, -4, 56, 40); cr.fill()
    elif name == 'field':
        cr.rectangle(-44, -28, 88, 56); cr.stroke(); cr.move_to(0, -28); cr.line_to(0, 28); cr.stroke(); circ(0, 0, 12, False)
    cr.restore()


def tag(cr, x, y, side, ic, en, ko, sub_en, sub_ko, pal, a, k=1.0, w=440):
    """종이 꼬리표: 아이콘 원 + 영어/한글 이름 + 보조 숫자. side=-1 왼쪽, +1 오른쪽."""
    if a <= 0: return
    cr.save(); cr.translate(x, y); cr.scale(k, k)
    x0 = 0 if side > 0 else -w
    hh = 100 if sub_en else 78
    cr.set_source_rgba(*pal['tag'], a); rrect(cr, x0, -hh, w, 2 * hh, 24); cr.fill()
    cx = x0 + 70 if side > 0 else -70
    cr.set_source_rgba(*pal['tagdisc'], a); cr.arc(cx, 0, 50, 0, 2 * math.pi); cr.fill()
    cr.push_group(); icon(cr, ic, cx, 0, 60, pal['tagicon'], pal['tagdisc']); cr.pop_group_to_source(); cr.paint_with_alpha(a)
    tx = x0 + 136 if side > 0 else -w + 22; tw = w - 160
    if sub_en:
        txt(cr, en, tx, -48, 36, pal['tagink'], a, anchor='l', maxw=tw)
        txt(cr, ko, tx, -8, 34, pal['tagink'], a, anchor='l', maxw=tw)
        txt(cr, sub_en, tx, 38, 30, pal['hi2'], a, anchor='l', maxw=tw)
        txt(cr, sub_ko, tx, 76, 30, pal['hi2'], a, anchor='l', maxw=tw)
    else:
        txt(cr, en, tx, -10, 36, pal['tagink'], a, anchor='l', maxw=tw)
        txt(cr, ko, tx, 32, 34, pal['tagink'], a, anchor='l', maxw=tw)
    cr.restore()
    cr.set_source_rgba(*pal['tag'], a); cr.set_line_width(5)
    cr.move_to(x, y); cr.line_to(x - side * 26, y); cr.stroke()


# ------------------------------------------------ 숫자 표기
def en_num(n):
    if n < 1e4: return f'{n:,.0f}' if n >= 10 or n == int(n) else f'{n:.1f}'
    for v, u in ((1e15, 'quadrillion'), (1e12, 'trillion'), (1e9, 'billion'), (1e6, 'million')):
        if n >= v: x = n / v; return f'{x:,.0f} {u}' if x >= 100 else f'{x:.1f} {u}' if x < 10 else f'{x:,.0f} {u}'
    return f'{n:,.0f}'

def ko_num(n):
    if n < 1e4: return f'{n:,.0f}'
    for v, u in ((1e16, '경'), (1e12, '조'), (1e8, '억'), (1e4, '만')):
        if n >= v: x = n / v; return f'{x:,.0f}{u}' if x >= 10 or abs(x - round(x)) < 0.05 else f'{x:.1f}{u}'
    return f'{n:,.0f}'


# ------------------------------------------------ 끝 화면(공통)
_SEAL = {}
def end_card(img, t, ep, t_end):
    """종이 바탕 + 제목 + 인장 + 크레딧 + 출처. img는 BGR float."""
    if t < t_end: return img
    pal = ep['pal']
    L = Layer(0); cr = L.cr
    u = smooth(ramp(t, t_end, t_end + 0.5))
    cr.set_source_rgba(*pal['endbg'], u); cr.paint()
    a = ramp(t, t_end + 0.25, t_end + 0.7); k = 1 + 0.12 * (1 - expo_out(ramp(t, t_end + 0.25, t_end + 0.8)))
    cr.save(); cr.translate(DW / 2, 720); cr.scale(k, k)
    icon(cr, ep['end_icon'], 0, -150, 130, pal['hi'], pal['endbg'])
    txt(cr, ep['title_en_card'], 0, 30, 84, INK, a, maxw=940)
    txt(cr, ep['title_ko_card'], 0, 132, 76, INK, a, maxw=940)
    cr.restore()
    b = ramp(t, t_end + 0.9, t_end + 1.4)
    txt(cr, 'Created & Coded by L.S.M.', DW / 2, 1290, 34, INK, 0.9 * b, fam=SERIF)
    txt(cr, '허상공방 虛像工房 Project', DW / 2, 1342, 34, INK, 0.9 * b, fam=SERIF)
    for i, s in enumerate(ep['sources']):
        txt(cr, s, DW / 2, 1660 + i * 40, 25, INK, 0.62 * b, fam=BOLD, maxw=980)
    lay = L.arr(); al = lay[..., 3:4]
    img = img * (1 - al) + lay[..., :3]
    if t >= t_end + 0.6:
        if 'v' not in _SEAL:
            sz = int(round(116 * SC))
            s = np.load(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '_shared', 'seal_baimun3.npy')).astype(np.float32)
            _SEAL['v'] = (cv2.resize(s, (sz, sz), interpolation=cv2.INTER_AREA)[..., [2, 1, 0, 3]], sz)
        s, sz = _SEAL['v']; a1 = smooth(ramp(t, t_end + 0.6, t_end + 0.8))
        xs, ys = int(round(DW / 2 * SC)) - sz // 2, int(round(1080 * SC))
        red = np.clip((s[..., 2:3] - s[..., 1:2]) * 4, 0, 1); al = s[..., 3:4] * a1 * red
        sub = img[ys:ys + sz, xs:xs + sz]; img[ys:ys + sz, xs:xs + sz] = sub * (1 - al + al * s[..., :3])
    return img


# ================================================ 틀 1: Ladder
class Ladder:
    """ep['steps'] = [(값, 아이콘, 영어, 한글, 보조영어, 보조한글)]. 로그 눈금으로 올라간다."""
    U = 330; ANCH = 1000

    def __init__(self, ep):
        self.ep = ep; s = ep['steps']
        self.t0 = ep.get('t_start', 3.2); self.seg = ep.get('seg', 2.3)
        self.times = [self.t0 + i * self.seg for i in range(len(s))]
        self.t_last = self.times[-1] + self.seg
        self.lv0 = math.log10(ep['v0'])
        self.events = [(tt + self.seg * 0.62, 'pop', i) for i, tt in enumerate(self.times)] + [(tt, 'move', i) for i, tt in enumerate(self.times)]

    def cam(self, t):
        """카메라가 보는 로그값(탑 꼭대기)."""
        lv = self.lv0; s = self.ep['steps']
        for i, tt in enumerate(self.times):
            prev = self.lv0 if i == 0 else math.log10(s[i - 1][0])
            u = sine_io(ramp(t, tt, tt + self.seg * 0.62))
            if t >= tt: lv = lerp(prev, math.log10(s[i][0]), u)
        zo = self.ep.get('zoom_out')
        if zo and t > self.t_last:                              # 끝에서 전체를 한눈에
            pass
        return lv

    def value(self, t): return 10 ** self.cam(t)

    def ys(self, lv, cam, k=1.0): return self.ANCH - (lv - cam) * self.U * k

    def draw(self, t, layers, pal):
        far, mid, front, top = layers; cam = self.cam(t); ep = self.ep
        # 하늘 띠: 단계마다 색이 바뀐다
        stops = pal['sky']; n = len(stops) - 1
        lvmax = math.log10(ep['steps'][-1][0])
        u = clamp((cam - self.lv0) / max(1e-6, lvmax - self.lv0)) * n
        i = min(n - 1, int(u)); f = smooth(u - i)
        c0 = mix(stops[i], stops[i + 1], f); c1 = mix(c0, (0, 0, 0), 0.25)
        g = cairo.LinearGradient(0, 0, 0, DH); g.add_color_stop_rgb(0, *c1); g.add_color_stop_rgb(1, *c0)
        far.cr.set_source(g); far.cr.paint()
        # 먼 층: 10배마다 가로 띠(시차 0.55)
        cr = far.cr
        for d in range(int(self.lv0) - 2, int(lvmax) + 3):
            y = self.ys(d, cam, 0.55)
            if -40 < y < DH + 40:
                cr.set_source_rgba(1, 1, 1, 0.06); cr.rectangle(0, y - 1.5, DW, 3); cr.fill()
        # 중간 층: 종이 구름·언덕 조각(시차 0.8), 씨앗 고정
        rng = np.random.default_rng(ep['seed'])
        cr = mid.cr
        for j in range(int((lvmax - self.lv0 + 4) * 2.2)):
            lv = self.lv0 - 1 + j / 2.2 + rng.uniform(-0.2, 0.2); x = rng.uniform(-60, DW + 60); r = rng.uniform(40, 110)
            y = self.ys(lv, cam, 0.8)
            if -150 < y < DH + 150:
                cr.set_source_rgba(*mix(c0, (1, 1, 1), 0.22), 0.55)
                for q in range(3): cr.arc(x + (q - 1) * r * 0.8, y + (q % 2) * r * 0.25, r * (0.75 + 0.25 * (q % 2)), 0, 2 * math.pi); cr.fill()
        # 바닥(시작점)
        yb = self.ys(self.lv0, cam)
        if yb < DH + 300:
            cr = mid.cr; cr.set_source_rgb(*pal['ground']); cr.rectangle(0, yb + 60, DW, DH); cr.fill()
        # 앞 층: 종이 탑(10배마다 색을 번갈아)
        cr = front.cr; tx, tw = DW / 2, 150
        ytop = self.ys(cam, cam)
        lvlo = self.lv0
        d = math.floor(lvlo)
        while d < cam:
            a_, b_ = max(lvlo, d), min(cam, d + 1)
            y0, y1 = self.ys(a_, cam), self.ys(b_, cam)
            if y0 > -50 and y1 < DH + 50:
                cr.set_source_rgb(*(pal['tower'] if d % 2 == 0 else pal['tower2']))
                cr.rectangle(tx - tw / 2, y1, tw, y0 - y1 + 1); cr.fill()
                cr.set_source_rgba(0, 0, 0, 0.12)
                for q in range(1, 10):
                    yq = self.ys(d + math.log10(q + 1) if d + math.log10(q + 1) < cam else cam, cam)
                    if a_ <= d + math.log10(q + 1) <= b_: cr.rectangle(tx - tw / 2, yq, tw * (0.35 if q != 4 else 0.6), 3); cr.fill()
            d += 1
        if yb < DH + 300:
            cr.set_source_rgb(*pal['tower2']); cr.rectangle(tx - tw / 2 - 30, yb, tw + 60, 60); cr.fill()
        # 꼭대기 덮개(박자마다 튐)
        pulse = 0
        for (te, kind, i) in self.events:
            if kind == 'pop' and te <= t: pulse = max(pulse, math.exp(-(t - te) * 7))
        cr.set_source_rgb(*pal['hi']); rrect(cr, tx - tw / 2 - 14 - pulse * 10, ytop - 26 - pulse * 6, tw + 28 + pulse * 20, 30 + pulse * 6, 10); cr.fill()
        # 10의 거듭제곱 눈금(왼쪽)
        cr = top.cr
        for dd in range(int(self.lv0), int(lvmax) + 2):
            y = self.ys(dd, cam)
            if 520 < y < 1600:
                cr.set_source_rgba(*pal['tick'], 0.55); cr.rectangle(tx - tw / 2 - 38, y - 2, 26, 4); cr.fill()
                xe = tx - tw / 2 - 48
                ew = txt(cr, str(dd), xe, y - 2, 20, pal['tick'], 0.6, fam=BOLD, anchor='r')
                txt(cr, '10', xe - ew - 2, y + 12, 30, pal['tick'], 0.6, fam=BOLD, anchor='r')
        # 꼬리표
        for i, st in enumerate(ep['steps']):
            v, ic, en, ko, sen, sko = st
            tp = self.times[i] + self.seg * 0.62
            if t < tp - 0.05: continue
            y = self.ys(math.log10(v), cam); side = 1 if i % 2 == 0 else -1
            a = ramp(t, tp - 0.05, tp + 0.15) * clamp((y - 470) / 120) * clamp((1700 - y) / 120)
            k = back_out(ramp(t, tp - 0.05, tp + 0.35), 2.0)
            tag(front.cr, tx + side * (tw / 2 + 36), y, side, ic, en, ko, sen, sko, pal, a, k, w=400)

    def hud(self, t, cr, pal):
        ep = self.ep; a = ramp(t, self.t0 - 0.4, self.t0)
        if a <= 0: return
        v = self.value(t); f = ep.get('hud', lambda v: (en_num(v), ko_num(v)))
        en, ko = f(v)
        cr.set_source_rgba(*pal['card'], 0.95 * a); rrect(cr, 110, 1640, DW - 220, 200, 30); cr.fill()
        txt(cr, en, DW / 2, 1722, 64, pal['cardink'], a, maxw=820)
        txt(cr, ko, DW / 2, 1800, 56, pal['hi'], a, maxw=820)


# ================================================ 틀 2: Spheres
class Spheres:
    """ep['objs'] = [dict(x, y, r, col, kind, label..., t_in)], ep['cams'] = [(t, cx, cy, 화면폭에 담을 단위 길이)]"""
    def __init__(self, ep):
        self.ep = ep; self.events = [(o['t_in'], 'pop', i) for i, o in enumerate(ep['objs'])] + [(c[0], 'move', i) for i, c in enumerate(ep['cams'][1:])]

    def cam(self, t):
        cs = self.ep['cams']; cx, cy, span = cs[0][1:4]
        for i in range(1, len(cs)):
            ta, tb = cs[i - 1][0], cs[i][0]
            if t >= ta:
                u = sine_io(ramp(t, ta, tb))
                ls = lerp(math.log(cs[i - 1][3]), math.log(cs[i][3]), u)
                # 줌 중에는 중심 이동을 화면 비율로 보간(멀미 방지)
                cx = lerp(cs[i - 1][1], cs[i][1], u); cy = lerp(cs[i - 1][2], cs[i][2], u); span = math.exp(ls)
        return cx, cy, span

    def draw(self, t, layers, pal):
        far, mid, front, top = layers; ep = self.ep
        cx, cy, span = self.cam(t); ppu = 900 / span; ox, oy = DW / 2, ep.get('screen_cy', 1060)
        def S(x, y): return ox + (x - cx) * ppu, oy - (y - cy) * ppu
        g = cairo.LinearGradient(0, 0, 0, DH); g.add_color_stop_rgb(0, *pal['bg0']); g.add_color_stop_rgb(1, *pal['bg1'])
        far.cr.set_source(g); far.cr.paint()
        rng = np.random.default_rng(ep['seed'])
        for _ in range(110):
            x, y, r = rng.uniform(0, DW), rng.uniform(0, DH), rng.uniform(1.5, 3.5)
            far.cr.set_source_rgba(1, 1, 1, 0.25 * pal.get('stars', 0)); far.cr.arc(x, y, r, 0, 6.283); far.cr.fill()
        for i, o in enumerate(ep['objs']):
            a = ramp(t, o['t_in'], o['t_in'] + 0.3) * (1 - ramp(t, o.get('t_out', 1e9), o.get('t_out', 1e9) + 0.3))
            if a <= 0: continue
            X, Y = S(o['x'], o['y']); R = max(o.get('rmin', 0), o['r'] * ppu)
            k = back_out(ramp(t, o['t_in'], o['t_in'] + 0.45), 1.8)
            L = front if o.get('layer', 'front') == 'front' else mid
            cr = L.cr
            if X + R < -200 or X - R > DW + 200 or Y + R < -200 or Y - R > DH + 200:
                pass
            elif o['kind'] == 'ball':
                cr.push_group()
                cr.set_source_rgb(*o['col']); cr.arc(X, Y, R * k, 0, 2 * math.pi); cr.fill()
                if o.get('blobs'):
                    rb = np.random.default_rng(o['blobs'])
                    cr.arc(X, Y, R * k, 0, 2 * math.pi); cr.clip()
                    cr.set_source_rgb(*o['col2'])
                    for _ in range(9):
                        bx, by = rb.uniform(-0.8, 0.8), rb.uniform(-0.8, 0.8); br = rb.uniform(0.12, 0.32)
                        cr.save(); cr.translate(X + bx * R, Y + by * R); cr.scale(1, rb.uniform(0.5, 1.2))
                        cr.arc(0, 0, br * R, 0, 2 * math.pi); cr.restore(); cr.fill()
                    cr.reset_clip()
                gsh = cairo.RadialGradient(X - R * 0.35, Y - R * 0.4, R * 0.1, X, Y, R * k)
                gsh.add_color_stop_rgba(0, 1, 1, 1, 0.22); gsh.add_color_stop_rgba(0.7, 1, 1, 1, 0); gsh.add_color_stop_rgba(1, 0, 0, 0, 0.18)
                cr.set_source(gsh); cr.arc(X, Y, R * k, 0, 2 * math.pi); cr.fill()
                cr.pop_group_to_source(); cr.paint_with_alpha(a)
            elif o['kind'] == 'ring':                           # 두께가 있는 띠(대기, 껍질)
                ri = o['ri'] * ppu
                cr.set_source_rgba(*o['col'], a); cr.set_line_width(max(1.5, R - ri)); cr.arc(X, Y, (R + ri) / 2, 0, 2 * math.pi); cr.stroke()
            elif o['kind'] == 'tick':                           # 거리 눈금(세로 길 옆)
                cr.set_source_rgba(*pal['tick'], a * 0.8); cr.rectangle(X - 30, Y - 2.5, 60, 5); cr.fill()
            elif o['kind'] == 'path':                           # 두 점 사이 점선
                X2, Y2 = S(o['x2'], o['y2'])
                cr.set_source_rgba(*pal['tick'], a * 0.6); cr.set_line_width(5); cr.set_dash([16, 14]); cr.move_to(X, Y); cr.line_to(X2, Y2); cr.stroke(); cr.set_dash([])
            if o.get('en') and a > 0:
                li_ = o.get('lab_in', o['t_in'] + 0.25); la = a * ramp(t, li_, li_ + 0.3) * (1 - ramp(t, o.get('lab_out', 1e9), o.get('lab_out', 1e9) + 0.3))
                side = o.get('side', 1); dist = o.get('ldist', 30)
                lx = X + side * (R + dist); ly = Y + o.get('ldy', 0)
                lx = clamp(lx, 470, 610) if False else lx
                if side > 0: lx = min(lx, DW - 470)
                else: lx = max(lx, 470)
                if la > 0:
                    tag(top.cr, lx, ly, side, o.get('icon', 'globe'), o['en'], o['ko'], o.get('sen', ''), o.get('sko', ''), pal, la, 1.0, w=o.get('tagw', 430))
                    if abs(lx - X) > R + dist + 8:          # 꼬리표가 밀렸으면 가는 선으로 연결
                        top.cr.set_source_rgba(*pal['tag'], la * 0.8); top.cr.set_line_width(4)
                        top.cr.move_to(X + side * R, Y); top.cr.line_to(lx, ly); top.cr.stroke()

    def hud(self, t, cr, pal):
        f = self.ep.get('hud')
        if not f: return
        r = f(t)
        if not r: return
        en, ko, a = r
        if a <= 0: return
        cr.set_source_rgba(*pal['card'], 0.95 * a); rrect(cr, 110, 1640, DW - 220, 200, 30); cr.fill()
        txt(cr, en, DW / 2, 1722, 64, pal['cardink'], a, maxw=820)
        txt(cr, ko, DW / 2, 1800, 56, pal['hi'], a, maxw=820)


# ================================================ 틀 3: Tiles
class Tiles:
    """ep['levels'] = [dict(t0, t1, cols, rows, labels=[...], fill=(값0, 값1), pins=[(위치, 아이콘, 영어, 한글)], title_en, title_ko, zoom_from=칸번호)]"""
    BOX = (80, 660, 920, 930)

    def __init__(self, ep):
        self.ep = ep; self.events = []
        for li, L in enumerate(ep['levels']):
            self.events.append((L['t0'], 'move', li))
            for p in L.get('pins', []): self.events.append((self.pin_t(L, p[0]), 'pop', li))

    def pin_t(self, L, pos):
        f0, f1 = L.get('fill', (0, 1)); n = L['cols'] * L['rows']
        u = clamp((pos / n - f0) / max(1e-6, f1 - f0))
        return lerp(L['t0'] + 0.5, L['t1'] - 1.0, u) + 0.05

    def cell(self, L, i):
        x, y, w, h = self.BOX; c, r = L['cols'], L['rows']; g = 10
        cw, ch = (w - g * (c - 1)) / c, (h - g * (r - 1)) / r
        return x + (i % c) * (cw + g), y + (i // c) * (ch + g), cw, ch

    def draw(self, t, layers, pal):
        far, mid, front, top = layers; ep = self.ep
        g = cairo.LinearGradient(0, 0, 0, DH); g.add_color_stop_rgb(0, *pal['bg0']); g.add_color_stop_rgb(1, *pal['bg1'])
        far.cr.set_source(g); far.cr.paint()
        for li, L in enumerate(ep['levels']):
            lastL = li == len(ep['levels']) - 1
            if not (L['t0'] - 0.01 <= t < (1e9 if lastL else L['t1'] + 0.6)): continue
            # 들어오기: 앞 단계의 칸에서 커지며 / 나가기: 다음 단계로 사라짐
            u_in = expo_in_out(ramp(t, L['t0'], L['t0'] + 0.7)); u_out = 0.0 if lastL else ramp(t, L['t1'], L['t1'] + 0.5)
            if li == 0: u_in = 1
            zf = L.get('zoom_from')
            cr = front.cr; cr.save()
            if zf is not None and li > 0 and u_in < 1:
                px, py, pw, ph = self.cell(ep['levels'][li - 1], zf); bx, by, bw, bh = self.BOX
                sx, sy = lerp(pw / bw, 1, u_in), lerp(ph / bh, 1, u_in)
                cr.translate(lerp(px, bx, u_in), lerp(py, by, u_in)); cr.scale(sx, sy); cr.translate(-bx, -by)
            a = min(1, u_in * 2) * (1 - u_out)
            n = L['cols'] * L['rows']; f0, f1 = L.get('fill', (0, 1))
            fu = smooth(ramp(t, L['t0'] + 0.5, L['t1'] - 1.0)); fill = lerp(f0, f1, fu) * n
            for i in range(n):
                x, y, w, h = self.cell(L, i)
                base = L.get('cell_col', lambda i: pal['tile'])(i)
                cr.set_source_rgba(*base, a); rrect(cr, x, y, w, h, min(w, h) * 0.14); cr.fill()
                q = clamp(fill - i)
                if q > 0:
                    cr.save(); rrect(cr, x, y, w, h, min(w, h) * 0.14); cr.clip()
                    cr.set_source_rgba(*L.get('fill_col', pal['fill']), a); cr.rectangle(x, y, w * q, h); cr.fill(); cr.restore()
                lab = L.get('labels')
                if lab and i < len(lab) and lab[i]:
                    txt(cr, lab[i], x + w / 2, y + h / 2 + min(w, h) * 0.13, min(w, h) * L.get('lab_k', 0.34), pal['tileink'], a * 0.9, fam=BOLD, maxw=w * 0.9)
            cr.restore()
            # 핀(사건)
            pins = L.get('pins', [])
            for pi, p in enumerate(pins):
                pos, ic, en, ko, sen, sko = (list(p) + ['', ''])[:6]
                tp = self.pin_t(L, pos)
                if t < tp: continue
                nxt = self.pin_t(L, pins[pi + 1][0]) if pi + 1 < len(pins) else 1e9
                ii = min(n - 1, int(pos)); x, y, w, h = self.cell(L, ii)
                X = x + w * (pos - ii); Y = y + h / 2
                pa = a * ramp(t, tp, tp + 0.15); k = back_out(ramp(t, tp, tp + 0.35), 2.2)
                ta_ = pa * (1 - ramp(t, nxt - 0.05, nxt + 0.15))
                cr2 = top.cr
                cr2.set_source_rgba(*pal['hi'], pa); cr2.arc(X, Y, 18 * k, 0, 2 * math.pi); cr2.fill()
                cr2.set_source_rgba(*pal['card'], pa); cr2.arc(X, Y, 7 * k, 0, 2 * math.pi); cr2.fill()
                side = p[6] if len(p) > 6 else (1 if X < DW / 2 else -1)
                ly = p[7] if len(p) > 7 else 1730
                tx_ = DW / 2 - side * 230
                tag(cr2, tx_, ly, side, ic, en, ko, sen, sko, pal, ta_, k, w=460)
                cr2.set_source_rgba(*pal['hi'], ta_ * 0.8); cr2.set_line_width(4); cr2.move_to(X, Y + 18); cr2.line_to(tx_ + side * 70, ly - 78); cr2.stroke()
            # 단계 제목(격자 위)
            ta = a * ramp(t, L['t0'] + 0.2, L['t0'] + 0.5)
            txt(top.cr, L['title_en'], DW / 2, 572, 46, pal['ink'], ta, maxw=900)
            txt(top.cr, L['title_ko'], DW / 2, 630, 42, pal['hi'], ta, maxw=900)

    def hud(self, t, cr, pal):
        f = self.ep.get('hud')
        if not f: return
        r = f(t)
        if not r: return
        en, ko, a = r
        if a <= 0: return
        cr.set_source_rgba(*pal['card'], 0.95 * a); rrect(cr, 110, 1640, DW - 220, 200, 30); cr.fill()
        txt(cr, en, DW / 2, 1722, 64, pal['cardink'], a, maxw=820)
        txt(cr, ko, DW / 2, 1800, 56, pal['hi'], a, maxw=820)


KINDS = dict(ladder=Ladder, spheres=Spheres, tiles=Tiles)


# ================================================ 한 프레임
def scene(ep, eng, t):
    pal = ep['pal']
    layers = [Layer(0), Layer(0.6), Layer(1.0), Layer(0.45)]
    eng.draw(t, layers, pal)
    top = layers[3]
    eng.hud(t, top.cr, pal)
    for c in ep['cards']: draw_card(top.cr, t, c, pal)
    base = np.zeros((H, W, 3), np.float32)
    for L in layers: base = composite(base, L)
    # 박자 섬광·띠 넘김
    for bt in ep.get('flash', []):
        if bt <= t < bt + 0.25: base = base + 0.10 * math.exp(-(t - bt) * 18)
    return base

def bands(img, t, t0, c1, c2):
    L = Layer(0); cr = L.cr; drew = False
    for k, c in enumerate((c1, c2)):
        u = expo_in_out(ramp(t, t0 - 0.32 + 0.07 * k, t0 + 0.32 + 0.07 * k))
        if 0 < u < 1:
            x = lerp(-2150, 1420, u); drew = True
            cr.set_source_rgb(*c); cr.move_to(x + 260, 0); cr.line_to(x + 1960, 0); cr.line_to(x + 1700, DH); cr.line_to(x, DH); cr.close_path(); cr.fill()
    if not drew: return img
    a = L.arr(); return img * (1 - a[..., 3:4]) + a[..., :3]

def speed_px(eng, t):
    """한 프레임 동안 화면이 움직이는 대략의 픽셀 수(하위 프레임 수를 정한다)."""
    dt = 1 / FPS
    if isinstance(eng, Ladder): return abs(eng.cam(t + dt / 2) - eng.cam(t - dt / 2)) * eng.U * 1.4
    if isinstance(eng, Spheres):
        a, b = eng.cam(t - dt / 2), eng.cam(t + dt / 2)
        return abs(math.log(b[2] / a[2])) * 900 + math.hypot(b[0] - a[0], b[1] - a[1]) * 900 / max(a[2], b[2])
    if isinstance(eng, Tiles):
        return 40 if any(L['t0'] <= t <= L['t0'] + 0.7 for L in eng.ep['levels'][1:]) else 0
    return 0

CODA_STEP = 1.9; CODA_HOLD = 2.8
def coda_len(ep): return len(ep['coda']) * CODA_STEP + CODA_HOLD

def coda(img, t, ep):
    """마무리: 장면이 흐려지며 가라앉고, 문장이 한 줄씩 떠오른다. 마지막 줄은 강조색."""
    if 'coda' not in ep or t < ep['t_coda']: return img
    t0 = ep['t_coda']; u = smooth(ramp(t, t0, t0 + 1.2))
    sig = max(0.1, 14 * SC * u)
    img = cv2.GaussianBlur(img, (0, 0), sig) * (1 - 0.78 * u)
    L = Layer(0); cr = L.cr; lines = ep['coda']; n = len(lines)
    y0 = 960 - (n * 210) / 2 + 70
    for i, (en, ko) in enumerate(lines):
        ti = t0 + 0.7 + i * CODA_STEP; a = smooth(ramp(t, ti, ti + 0.9))
        if a <= 0: continue
        last = i == n - 1; dy = (1 - expo_out(ramp(t, ti, ti + 1.2))) * 30
        col = ep['pal']['hi'] if last else (0.97, 0.95, 0.90)
        se, sk = (74, 66) if last else (60, 54)
        y = y0 + i * 210 + dy
        txt(cr, en, DW / 2, y, se, col, a, fam=SERIF, maxw=960)
        txt(cr, ko, DW / 2, y + sk + 22, sk, col, a * 0.95, fam=BLK if last else BOLD, maxw=960)
    la = L.arr()
    return img * (1 - la[..., 3:4]) + la[..., :3]

def render(ep, eng, t, samples=2):
    dt = 1 / FPS
    v = speed_px(eng, t)
    samples = 1 if samples <= 1 else int(clamp(math.ceil(v / 5), 1, 10))
    acc = None
    for s in range(samples):
        tt = t + ((s + 0.5) / samples - 0.5) * dt * 0.6
        img = scene(ep, eng, tt)
        acc = img if acc is None else acc + img
    img = acc / samples
    img = coda(img, t, ep)
    for w_ in ep.get('wipes', []): img = bands(img, t, w_, ep['pal']['hi'], ep['pal']['tower'])
    img = bands(img, t, ep['t_end'], ep['pal']['hi'], ep['pal']['endbg'])
    img = end_card(img, t, ep, ep['t_end'])
    return finish(img, t)
