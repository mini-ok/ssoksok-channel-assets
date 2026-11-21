"""모션그래픽 엔진(pycairo): 이징·스프링, 획 모핑, 카메라, 서브프레임 모션 블러.
좌표는 1920×1080 기준 '디자인 픽셀'. 실제 출력 배율은 MG_SCALE(기본 1 = 1920×1080, 0.5 = 960×540 시험).
모든 프레임은 t의 순수 함수다.
"""
import math, os
import numpy as np
import cairo

SC = float(os.environ.get('MG_SCALE', '1'))
W, H = int(round(1920 * SC)), int(round(1080 * SC))
FPS = int(os.environ.get('MG_FPS', '60'))

# ---------------------------------------------------------------- 색
PAPER = (0.925, 0.900, 0.840)      # 한지 아이보리
INK = (0.085, 0.080, 0.075)        # 먹
VERM = (0.835, 0.255, 0.165)       # 주홍(점)
GRID = (0.62, 0.58, 0.50)          # 레이아웃 그리드 선

# ---------------------------------------------------------------- 이징
def clamp(x, a=0.0, b=1.0): return a if x < a else b if x > b else x
def ramp(t, a, b): return clamp((t - a) / (b - a)) if b > a else float(t >= a)
def smooth(u): u = clamp(u); return u * u * (3 - 2 * u)
def expo_out(u): u = clamp(u); return 1.0 if u >= 1 else 1 - 2 ** (-10 * u)
def expo_in_out(u):
    u = clamp(u)
    if u <= 0: return 0.0
    if u >= 1: return 1.0
    return 2 ** (20 * u - 10) / 2 if u < 0.5 else (2 - 2 ** (-20 * u + 10)) / 2
def cubic_in_out(u): u = clamp(u); return 4 * u ** 3 if u < 0.5 else 1 - (-2 * u + 2) ** 3 / 2
def back_out(u, s=1.70158):
    u = clamp(u) - 1; return 1 + u * u * ((s + 1) * u + s)
def spring(u, zeta=0.32, freq=2.6):
    """0→1 감쇠 진동(오버슈트). u는 정규 시간(0~1이 주 움직임, 이후 여진)."""
    if u <= 0: return 0.0
    w = 2 * math.pi * freq
    wd = w * math.sqrt(max(1e-6, 1 - zeta ** 2))
    return 1 - math.exp(-zeta * w * u) * (math.cos(wd * u) + zeta * w / wd * math.sin(wd * u))
def lerp(a, b, u): return a + (b - a) * u
def lerp2(p, q, u): return (p[0] + (q[0] - p[0]) * u, p[1] + (q[1] - p[1]) * u)

# ---------------------------------------------------------------- 획
# 글자는 획 목록: ('line', [(x,y),...], closed) 또는 ('dot', (x,y), r) 또는 ('ring', (x,y), r)
# 단위 상자 0..1 좌표. 모핑을 위해 모든 선은 N점으로 다시 표본한다.
NPT = 48
def resample(pts, n=NPT, closed=False):
    P = np.array(pts, float)
    if closed: P = np.vstack([P, P[:1]])
    seg = np.linalg.norm(np.diff(P, axis=0), axis=1); cum = np.concatenate([[0], np.cumsum(seg)])
    if cum[-1] < 1e-9: return np.repeat(P[:1], n, 0)
    q = np.linspace(0, cum[-1], n)
    return np.stack([np.interp(q, cum, P[:, 0]), np.interp(q, cum, P[:, 1])], 1)

def ring_pts(c, r, n=NPT, a0=-math.pi / 2):
    a = a0 + np.linspace(0, 2 * math.pi, n)
    return np.stack([c[0] + r * np.cos(a), c[1] + r * np.sin(a)], 1)

class Shape:
    """정규화된 획: kind in {'line','dot'}. line은 (NPT,2) 점, dot은 중심·반지름."""
    def __init__(self, kind, pts=None, c=None, r=0.0, closed=False):
        self.kind, self.pts, self.c, self.r, self.closed = kind, pts, c, r, closed
    @staticmethod
    def make(spec):
        k = spec[0]
        if k == 'line': return Shape('line', resample(spec[1], closed=spec[2] if len(spec) > 2 else False), closed=spec[2] if len(spec) > 2 else False)
        if k == 'ring': return Shape('line', ring_pts(spec[1], spec[2]), closed=True)
        if k == 'dot': return Shape('dot', c=spec[1], r=spec[2])
        raise ValueError(k)
    def center(self):
        return np.array(self.c) if self.kind == 'dot' else self.pts.mean(0)
    def collapsed(self):
        """모핑 상대가 없을 때: 제자리에서 길이 0으로 오그라든 모양."""
        if self.kind == 'dot': return Shape('dot', c=self.c, r=0.0)
        m = self.pts.mean(0); return Shape('line', np.repeat(m[None], NPT, 0), closed=self.closed)

def morph_shape(a, b, u):
    if a.kind == b.kind == 'dot':
        return Shape('dot', c=lerp2(a.c, b.c, u), r=lerp(a.r, b.r, u))
    if a.kind == 'dot' or b.kind == 'dot':
        # 점 ↔ 선: 점을 아주 짧은 선으로 보고 선 쪽으로 늘린다(굵기는 draw에서 r로)
        dot, ln, uu = (a, b, u) if a.kind == 'dot' else (b, a, 1 - u)
        P = np.repeat(np.array(dot.c, float)[None], NPT, 0)
        s = Shape('line', P * (1 - uu) + ln.pts * uu, closed=ln.closed)
        s.dot_r = dot.r * (1 - uu)
        return s
    return Shape('line', a.pts * (1 - u) + b.pts * u, closed=a.closed and b.closed and u > 0.5)

def morph(A, B, u):
    """글자 A → B. 획 수가 다르면 가까운 짝을 찾고, 남는 획은 제자리에서 오그라들거나 자라난다."""
    A, B = list(A), list(B)
    out = []
    usedB = set()
    for a in A:
        best, bd = None, 1e9
        for j, b in enumerate(B):
            if j in usedB: continue
            d = np.linalg.norm(a.center() - b.center()) + (0.25 if a.kind != b.kind else 0)
            if d < bd: best, bd = j, d
        if best is None:
            out.append(morph_shape(a, a.collapsed(), u))
        else:
            usedB.add(best); out.append(morph_shape(a, B[best], u))
    for j, b in enumerate(B):
        if j not in usedB: out.append(morph_shape(b.collapsed(), b, u))
    return out

# ---------------------------------------------------------------- 그리기
class Canvas:
    def __init__(self):
        self.surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H)
        self.cr = cairo.Context(self.surf)
    def begin(self, bg=PAPER):
        cr = self.cr
        cr.identity_matrix(); cr.scale(SC, SC)
        cr.set_source_rgb(*bg); cr.paint()
        return cr
    def array(self):
        self.surf.flush()
        a = np.ndarray((H, W, 4), np.uint8, self.surf.get_data(), strides=(self.surf.get_stride(), 4, 1))
        return a[..., :3].astype(np.float32) / 255.0      # BGR

def draw_glyph(cr, shapes, x, y, size, width, color, alpha=1.0, dot_color=None):
    """단위 상자 글자를 (x, y) 왼쪽 위, size 크기로. width: 획 굵기(단위 상자 비)."""
    cr.save(); cr.translate(x, y); cr.scale(size, size)
    cr.set_line_width(width); cr.set_line_cap(cairo.LINE_CAP_BUTT); cr.set_line_join(cairo.LINE_JOIN_MITER)
    for s in shapes:
        if s.kind == 'dot':
            if s.r <= 1e-4: continue
            c = dot_color or color
            cr.set_source_rgba(*c, alpha); cr.arc(s.c[0], s.c[1], s.r, 0, 2 * math.pi); cr.fill()
            continue
        P = s.pts
        L = float(np.linalg.norm(np.diff(P, axis=0), axis=1).sum())
        dr = getattr(s, 'dot_r', 0.0)
        if dr > 1e-4 and L < 1e-3:
            c = dot_color or color
            cr.set_source_rgba(*c, alpha); cr.arc(P[0, 0], P[0, 1], dr, 0, 2 * math.pi); cr.fill(); continue
        if L < 1e-3: continue
        cr.set_source_rgba(*color, alpha)
        cr.move_to(*P[0])
        for p in P[1:]: cr.line_to(*p)
        if s.closed: cr.close_path()
        cr.stroke()
        if dr > 1e-4:                                   # 점 → 선으로 바뀌는 중: 끝에 남은 둥근 덩이
            c = dot_color or color
            cr.set_source_rgba(*c, alpha); cr.arc(P[0, 0], P[0, 1], dr, 0, 2 * math.pi); cr.fill()
    cr.restore()

def text(cr, s, x, y, size, color=INK, alpha=1.0, font='Noto Serif CJK KR', weight=cairo.FONT_WEIGHT_NORMAL, anchor='l'):
    cr.save()
    cr.select_font_face(font, cairo.FONT_SLANT_NORMAL, weight); cr.set_font_size(size)
    ext = cr.text_extents(s)
    dx = {'l': 0, 'c': -ext.x_advance / 2, 'r': -ext.x_advance}[anchor]
    cr.move_to(x + dx, y); cr.set_source_rgba(*color, alpha); cr.show_text(s)
    cr.restore()

def render(scene, t, samples=6, shutter=0.5):
    """서브프레임 모션 블러: 프레임 시간 앞뒤 shutter 비율(180° = 0.5) 안에서 samples번 그려 평균."""
    acc = None
    for i in range(samples):
        tt = t + ((i + 0.5) / samples - 0.5) * shutter / FPS if samples > 1 else t
        img = scene(tt)
        acc = img if acc is None else acc + img
    return acc / samples

def grain(img, t, amt=0.012):
    rng = np.random.default_rng(int(t * FPS) * 7 + 3)
    n = rng.standard_normal((img.shape[0] // 2 + 1, img.shape[1] // 2 + 1)).astype(np.float32)
    n = np.repeat(np.repeat(n, 2, 0), 2, 1)[:img.shape[0], :img.shape[1]]
    return np.clip(img + amt * n[..., None], 0, 1)

# ---------------------------------------------------------------- 트림 패스(획을 거두고 다시 긋기)
def trim(s, a, b):
    """선 Shape를 길이 비율 a..b 구간만 남긴다(점은 그대로)."""
    if s.kind == 'dot' or b <= a + 1e-4:
        return s if s.kind == 'dot' else Shape('line', s.pts[:1].repeat(2, 0))
    P = s.pts if not s.closed else np.vstack([s.pts, s.pts[:1]])
    seg = np.linalg.norm(np.diff(P, axis=0), axis=1); cum = np.concatenate([[0], np.cumsum(seg)]); L = cum[-1]
    if L < 1e-9: return Shape('line', P[:2].copy())
    ts = np.linspace(a * L, b * L, NPT)
    x = np.interp(ts, cum, P[:, 0]); y = np.interp(ts, cum, P[:, 1])
    return Shape('line', np.stack([x, y], 1))
def morph_trim(A, B, u):
    """A의 획이 끝에서부터 거둬지고(0..0.5), B의 획이 시작에서부터 그어진다(0.5..1). 점은 모핑."""
    out = []
    la = [a for a in A if a.kind == 'line']; lb = [b for b in B if b.kind == 'line']
    if u < 0.5:
        k = expo_in_out(u / 0.5)
        out += [trim(a, 0, 1 - k) for a in la]
    else:
        k = expo_in_out((u - 0.5) / 0.5)
        out += [trim(b, 0, k) for b in lb]
    da = [a for a in A if a.kind == 'dot']; db = [b for b in B if b.kind == 'dot']
    out += morph(da, db, back_out(u, 1.3)) if (da or db) else []
    return out
