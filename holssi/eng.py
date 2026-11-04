# -*- coding: utf-8 -*-
"""
홀씨 (HOLSSI) -- painterly render engine.
Layers (premultiplied RGBA) -> per-layer depth blur + haze + brush texture -> composite -> light -> grade -> grain.
Static layers are painted once per shot (cached) and re-framed per frame; dynamic layers are drawn each frame.
"""
import cairo, numpy as np, math, cv2

cv2.setNumThreads(1)
W, H = 1920, 1040
OH = 1080
BAR = (OH - H) // 2
FPS = 24
F32 = np.float32
TAU = 2 * math.pi

# ------------------------------------------------------------------ math
def sm(a, b, t):
    if b == a:
        return 1.0 if t >= b else 0.0
    x = min(1.0, max(0.0, (t - a) / (b - a)))
    return x * x * (3 - 2 * x)

def lin(a, b, t):
    return min(1.0, max(0.0, (t - a) / (b - a)))

def lerp(a, b, u):
    return a + (b - a) * u

def lc(c1, c2, u):
    return tuple(a + (b - a) * u for a, b in zip(c1, c2))

def cm(c, k):
    return tuple(min(1.0, x * k) for x in c)

def ease(u):
    u = min(1.0, max(0.0, u))
    return u * u * (3 - 2 * u)

def kf(t, keys):
    if t <= keys[0][0]:
        return keys[0][1]
    for (ta, va), (tb, vb) in zip(keys[:-1], keys[1:]):
        if t <= tb:
            u = ease((t - ta) / (tb - ta)) if tb > ta else 1.0
            if isinstance(va, tuple):
                return tuple(a + (b - a) * u for a, b in zip(va, vb))
            return va + (vb - va) * u
    return keys[-1][1]

def nz(t, s=0.0):
    return 0.5 * math.sin(t * 1.7 + s * 3.1) + 0.3 * math.sin(t * 3.9 + s * 1.3) + 0.2 * math.sin(t * 7.3 + s * 5.7)

# ------------------------------------------------------------------ palette
CREAM = (0.99, 0.94, 0.82)
PEACH = (0.98, 0.83, 0.63)
GOLD = (1.0, 0.80, 0.45)
SKYB = (0.62, 0.75, 0.82)
SKYT = (0.48, 0.63, 0.74)
LAV = (0.72, 0.66, 0.78)
LAV_D = (0.50, 0.47, 0.60)
SAGE = (0.62, 0.70, 0.46)
LEAF = (0.47, 0.60, 0.33)
MOSS = (0.36, 0.48, 0.28)
FOREST = (0.17, 0.31, 0.25)
TEAL_D = (0.10, 0.21, 0.21)
SEA = (0.42, 0.58, 0.64)
SEA_D = (0.26, 0.42, 0.50)
RUST = (0.72, 0.32, 0.20)
ASH = (0.58, 0.57, 0.55)
ASH_D = (0.36, 0.35, 0.35)
CHAR = (0.15, 0.14, 0.14)
YEL = (0.99, 0.80, 0.22)
INK = (0.13, 0.15, 0.13)
WHITE = (1.0, 0.99, 0.96)

# ------------------------------------------------------------------ canvas
class Canvas:
    def __init__(self, w=W, h=H):
        self.w, self.h = w, h
        self.s = cairo.ImageSurface(cairo.FORMAT_ARGB32, w, h)
        self.c = cairo.Context(self.s)
        self.c.set_line_cap(cairo.LINE_CAP_ROUND)
        self.c.set_line_join(cairo.LINE_JOIN_ROUND)

    def rgba(self):
        """premultiplied float RGBA (h,w,4)"""
        self.s.flush()
        a = np.ndarray((self.h, self.w, 4), np.uint8, self.s.get_data())
        return a[..., [2, 1, 0, 3]].astype(F32) * F32(1 / 255.0)

    def rgba_u8(self):
        self.s.flush()
        a = np.ndarray((self.h, self.w, 4), np.uint8, self.s.get_data())
        return a[..., [2, 1, 0, 3]].copy()

# ------------------------------------------------------------------ primitive helpers
def src(c, col, a=1.0):
    c.set_source_rgba(col[0], col[1], col[2], a)

def poly(c, pts, close=True):
    c.move_to(*pts[0])
    for p in pts[1:]:
        c.line_to(*p)
    if close:
        c.close_path()

def fillc(c, col, a=1.0):
    src(c, col, a)
    c.fill()

def strokec(c, col, w, a=1.0):
    src(c, col, a)
    c.set_line_width(w)
    c.stroke()

def line(c, x0, y0, x1, y1, w, col, a=1.0):
    c.move_to(x0, y0)
    c.line_to(x1, y1)
    strokec(c, col, w, a)

def vgrad(c, x0, y0, x1, y1, stops):
    pat = cairo.LinearGradient(0, y0, 0, y1)
    for p, col in stops:
        if len(col) == 4:
            pat.add_color_stop_rgba(p, *col)
        else:
            pat.add_color_stop_rgb(p, *col)
    c.set_source(pat)
    c.rectangle(x0, y0, x1 - x0, y1 - y0)
    c.fill()

def radial(c, x, y, r, col, a, a1=0.0):
    pat = cairo.RadialGradient(x, y, 0, x, y, r)
    pat.add_color_stop_rgba(0, col[0], col[1], col[2], a)
    pat.add_color_stop_rgba(1, col[0], col[1], col[2], a1)
    c.set_source(pat)
    c.arc(x, y, r, 0, TAU)
    c.fill()

def jit(col, rng, v=0.06, warm=0.0):
    k = 1 + rng.uniform(-v, v)
    return (min(1, col[0] * k + warm), min(1, col[1] * k), min(1, col[2] * k - warm * 0.5))

def dabs(c, rng, n, xr, yr, col, v, size, ang=0.0, angv=0.6, length=2.2, alpha=(0.55, 0.95), mask=None,
         warm=0.0):
    """short brush strokes scattered in a box (xr,yr = (min,max)); mask(x,y)->bool optional"""
    xs = rng.uniform(xr[0], xr[1], n)
    ys = rng.uniform(yr[0], yr[1], n)
    for i in range(n):
        x, y = xs[i], ys[i]
        if mask is not None and not mask(x, y):
            continue
        s = size * rng.uniform(0.6, 1.4)
        a = ang + rng.uniform(-angv, angv)
        dx, dy = math.cos(a) * s * length * 0.5, math.sin(a) * s * length * 0.5
        c.move_to(x - dx, y - dy)
        c.line_to(x + dx, y + dy)
        src(c, jit(col, rng, v, warm), rng.uniform(*alpha))
        c.set_line_width(s)
        c.stroke()

def blob(c, rng, x, y, r, col, a=1.0, wob=0.18, n=11):
    pts = []
    ph = rng.uniform(0, TAU)
    for k in range(n):
        th = TAU * k / n + ph
        rr = r * (1 + rng.uniform(-wob, wob))
        pts.append((x + math.cos(th) * rr, y + math.sin(th) * rr * 0.9))
    c.move_to(*pts[0])
    for i in range(n):
        p0 = pts[i]; p1 = pts[(i + 1) % n]
        mx, my = (p0[0] + p1[0]) / 2, (p0[1] + p1[1]) / 2
        c.curve_to(p0[0], p0[1], p0[0], p0[1], mx, my)
    c.close_path()
    fillc(c, col, a)

def blade(c, x, y, h, lean, w, col, a=1.0):
    """grass blade from (x,y) upward"""
    c.move_to(x, y)
    c.curve_to(x + lean * 0.2, y - h * 0.4, x + lean * 0.6, y - h * 0.75, x + lean, y - h)
    strokec(c, col, w, a)

# ------------------------------------------------------------------ painterly paint ops
def paint_cloud(c, rng, x, y, w, h, light=CREAM, body=PEACH, shade=LAV, n=None, size=None, alpha=1.0, flat=True):
    """stylised flat-bottomed cloud built from dabs: shade underside, body, highlight top"""
    n = n or int(w * h / 90)
    size = size or max(6.0, h * 0.16)
    def m(px, py):
        u = (px - x) / (w / 2)
        if abs(u) > 1:
            return False
        top = y - h * (0.35 + 0.65 * math.sqrt(max(0, 1 - u * u))) * (0.75 + 0.25 * math.sin(px * 0.031 + y))
        return top < py < y
    dabs(c, rng, int(n * 0.5), (x - w / 2, x + w / 2), (y - h * 0.45, y + h * 0.08), shade, 0.05, size, ang=0.0,
         angv=0.25, length=3.0, alpha=(0.7 * alpha, 0.95 * alpha), mask=m)
    dabs(c, rng, n, (x - w / 2, x + w / 2), (y - h, y - h * 0.15), body, 0.05, size, ang=0.0, angv=0.35,
         length=2.6, alpha=(0.7 * alpha, 0.95 * alpha), mask=lambda px, py: m(px, py + h * 0.22))
    dabs(c, rng, int(n * 0.7), (x - w / 2, x + w / 2), (y - h, y - h * 0.4), light, 0.03, size * 0.85, ang=0.0,
         angv=0.4, length=2.4, alpha=(0.75 * alpha, 1.0 * alpha), mask=lambda px, py: m(px, py + h * 0.45))

def stars(c, rng, n, x0, x1, y0, y1, a=1.0):
    for _ in range(n):
        x, y = rng.uniform(x0, x1), rng.uniform(y0, y1)
        r = rng.uniform(0.6, 1.8) * (2.2 if rng.random() < 0.04 else 1)
        c.arc(x, y, r, 0, TAU)
        fillc(c, (1, 0.97, 0.9), a * rng.uniform(0.4, 1.0))

# ------------------------------------------------------------------ brush textures (multiplicative)
def _make_tex(seed, w=2400, h=1400, n=30000, ang=0.0, angv=0.5, L=(8, 30), wd=(1.5, 4.0)):
    rng = np.random.default_rng(seed)
    cv = Canvas(w, h)
    c = cv.c
    c.set_source_rgb(0.5, 0.5, 0.5)
    c.paint()
    xs = rng.uniform(0, w, n); ys = rng.uniform(0, h, n)
    for i in range(n):
        a = ang + rng.uniform(-angv, angv)
        l = rng.uniform(*L)
        g = rng.uniform(0.25, 0.75)
        c.move_to(xs[i] - math.cos(a) * l / 2, ys[i] - math.sin(a) * l / 2)
        c.line_to(xs[i] + math.cos(a) * l / 2, ys[i] + math.sin(a) * l / 2)
        c.set_source_rgba(g, g, g, 0.35)
        c.set_line_width(rng.uniform(*wd))
        c.stroke()
    t = cv.rgba()[..., 0]
    t = cv2.GaussianBlur(t, (0, 0), 0.6)
    t = (t - t.mean()) / (t.std() + 1e-6)
    return t.astype(F32)

_TEX = {}
def tex(name):
    if name not in _TEX:
        cfg = {'h': dict(seed=1, ang=0.0, angv=0.35), 'd': dict(seed=2, ang=0.7, angv=0.9),
               'v': dict(seed=3, ang=math.pi / 2, angv=0.3)}[name]
        _TEX[name] = _make_tex(**cfg)
    return _TEX[name]

# ------------------------------------------------------------------ layers
class Static:
    """a layer painted once (world canvas of size w,h) and re-framed every frame"""
    _cache = {}

    def __init__(self, key, w, h, painter):
        if key not in Static._cache:
            cv = Canvas(w, h)
            painter(cv.c, np.random.default_rng(abs(hash(key)) % (2 ** 32)))
            Static._cache[key] = cv.rgba_u8()
        self.img = Static._cache[key]
        self.w, self.h = w, h

    @staticmethod
    def clear(prefix):
        for k in list(Static._cache):
            if not k.startswith(prefix):
                del Static._cache[k]

    def view(self, cx, cy, s=1.0, rot=0.0, sway=None):
        """world point (cx,cy) -> screen centre, scale s"""
        ca, sa = math.cos(rot) * s, math.sin(rot) * s
        M = np.array([[ca, -sa, W / 2 - (ca * cx - sa * cy)], [sa, ca, H / 2 - (sa * cx + ca * cy)]], F32)
        out = cv2.warpAffine(self.img, M, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT,
                             borderValue=(0, 0, 0, 0))
        out = out.astype(F32) * F32(1 / 255.0)
        if sway is not None:
            out = apply_sway(out, *sway)
        return out

_GX = np.tile(np.arange(W, dtype=F32), (H, 1))
_GY = np.tile(np.arange(H, dtype=F32)[:, None], (1, W))

def apply_sway(img, t, amp, y0, y1, k=0.012, speed=2.2):
    """wind: horizontal displacement growing upward from y1 (roots) to y0 (tips)"""
    w = np.clip((y1 - _GY) / max(1.0, (y1 - y0)), 0, 1) ** 1.5
    dx = amp * w * (np.sin(_GX * k * 0.3 + t * speed) * 0.7 + np.sin(_GX * k + t * speed * 1.7 + 1.3) * 0.3)
    return cv2.remap(img, _GX - dx, _GY, interpolation=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)

def dyn():
    return Canvas(W, H)

# ------------------------------------------------------------------ compositing
class Comp:
    def __init__(self, base=(0, 0, 0)):
        self.img = np.zeros((H, W, 3), F32)
        self.img[:] = base
        self.glows = []
        self.lift = (0.0, 0.0, 0.0)
        self.gain = (1.0, 1.0, 1.0)
        self.sat = 1.0
        self.contrast = 1.0
        self.vig = 0.35
        self.post = []
        self.fade = 1.0

    def add(self, rgba, blur=0.0, haze=None, tx=None, tamp=0.10, toff=(0, 0), alpha=1.0):
        """rgba: premultiplied float. haze: (col, amount). tx: texture name"""
        if rgba is None:
            return
        L = rgba
        if tx is not None and tamp > 0:
            T = tex(tx)
            ox, oy = int(toff[0]) % 400, int(toff[1]) % 300
            t = T[oy:oy + H, ox:ox + W]
            L = L.copy()
            L[..., :3] *= (1 + F32(tamp) * t)[..., None]
        if haze is not None and haze[1] > 0:
            hc, ha = haze
            L = L.copy() if L is rgba else L
            L[..., :3] = L[..., :3] * F32(1 - ha) + np.array(hc, F32) * L[..., 3:4] * F32(ha)
        if blur > 0.4:
            if blur > 6:
                sc = 4 if blur > 14 else 2
                d = cv2.resize(L, (W // sc, H // sc), interpolation=cv2.INTER_AREA)
                d = cv2.GaussianBlur(d, (0, 0), blur / sc)
                L = cv2.resize(d, (W, H), interpolation=cv2.INTER_LINEAR)
            else:
                L = cv2.GaussianBlur(L, (0, 0), blur)
        a = L[..., 3:4] * F32(alpha)
        self.img = L[..., :3] * F32(alpha) + self.img * (1 - a)

    def glow(self, x, y, r, col, amp):
        self.glows.append((x, y, r, col, amp))

    def finish(self, fi):
        img = self.img
        for (x, y, r, col, amp) in self.glows:
            gx = (_GX - x) / r
            gy = (_GY - y) / r
            g = np.exp(-(gx * gx + gy * gy) * 2.0) * F32(amp)
            img = 1 - (1 - img) * (1 - g[..., None] * np.array(col, F32))
        for fn in self.post:
            img = fn(img)
        img = np.array(self.lift, F32) + img * np.array(self.gain, F32)
        if self.contrast != 1.0:
            img = 0.5 + (img - 0.5) * F32(self.contrast)
        if self.sat != 1.0:
            lum = (img * np.array((0.3, 0.59, 0.11), F32)).sum(axis=2, keepdims=True)
            img = lum + (img - lum) * F32(self.sat)
        img = img * (1 - F32(self.vig) * VIG[..., None])
        img = np.clip(img, 0, 1) * F32(self.fade)
        img = img + GRAIN[fi % len(GRAIN)][..., None] * F32(0.011)
        out = np.zeros((OH, W, 3), np.uint8)
        out[BAR:BAR + H] = np.clip(img * 255 + 0.5, 0, 255).astype(np.uint8)
        return out

_r = np.random.default_rng(7)
GRAIN = []
for _ in range(6):
    g = _r.normal(0, 1, (H // 2, W // 2)).astype(F32)
    g = cv2.resize(g, (W, H), interpolation=cv2.INTER_LINEAR) * 0.7 + _r.normal(0, 0.5, (H, W)).astype(F32)
    GRAIN.append(g)
VIG = np.clip(((_GX - W / 2) / (W / 2)) ** 2 * 0.6 + ((_GY - H / 2) / (H / 2)) ** 2 * 0.8, 0, 1.6) ** 1.3

# ------------------------------------------------------------------ the seed (홀씨)
def seed(c, x, y, s, rot=0.0, wet=0.0, t=0.0, dew=0.0, rng=None, light=CREAM, rim=1.0, ink=1.0, nfil=34,
         achene=True, beak=1.0):
    """dandelion seed at pappus centre (x,y), size s = pappus radius in px. rot: tilt (rad, 0 = upright).
    wet: 0..1 filaments clump and droop."""
    rng = rng or np.random.default_rng(11)
    c.save()
    c.translate(x, y)
    c.rotate(rot)
    blen = s * 1.25 * beak
    # beak (stalk) and achene
    line(c, 0, 0, 0, blen, max(0.8, s * 0.028), (0.62, 0.58, 0.48), 0.95)
    if achene:
        c.save()
        c.translate(0, blen + s * 0.19)
        c.scale(1, 4.0)
        c.arc(0, 0, max(1.6, s * 0.048), 0, TAU)
        c.restore()
        fillc(c, (0.56, 0.42, 0.28))
        c.save()
        c.translate(0, blen + s * 0.19)
        c.scale(1, 4.0)
        c.arc(0, 0, max(1.6, s * 0.048), 0, TAU)
        c.restore()
        strokec(c, INK, max(0.6, s * 0.012), 0.6 * ink)
        for k in range(4):
            yy = blen + s * (0.08 + 0.08 * k)
            line(c, -s * 0.05, yy, s * 0.05, yy + s * 0.02, max(0.5, s * 0.008), (0.32, 0.22, 0.14), 0.7)
    # filaments
    fr = np.random.default_rng(int(s * 10) % 997 + 3)
    angs = np.linspace(-math.pi * 0.98, 0.0 - math.pi * 0.02, nfil) + fr.uniform(-0.05, 0.05, nfil)
    full = np.concatenate([angs, angs + math.pi])  # full circle (front + back)
    lw = max(1.0, s * 0.010)
    for k, a0 in enumerate(full):
        back = k >= nfil
        droop = wet * 1.1
        a = a0
        # wet: rotate filaments toward downward (pi/2) bundle
        target = -math.pi / 2 + (a - (-math.pi / 2)) * (1 - 0.85 * wet)
        a = target
        L = s * (0.92 + 0.08 * math.sin(k * 2.3)) * (1 - 0.35 * wet)
        flutter = 0.035 * math.sin(t * 9 + k * 1.7) * (1 - wet)
        a += flutter
        ex, ey = math.cos(a) * L, math.sin(a) * L
        mx, my = math.cos(a) * L * 0.5, math.sin(a) * L * 0.5 + droop * s * 0.12
        col = lc((0.92, 0.90, 0.84), light, 0.4) if not back else (0.80, 0.80, 0.78)
        if ink > 0 and not back:
            c.move_to(0, 0)
            c.curve_to(mx * 0.6, my * 0.6, mx, my, ex, ey + droop * s * 0.2)
            strokec(c, (0.30, 0.30, 0.28), lw * 2.4, 0.16 * ink)
        c.move_to(0, 0)
        c.curve_to(mx * 0.6, my * 0.6, mx, my, ex, ey + droop * s * 0.2)
        strokec(c, col, lw, (0.55 if back else 0.9) * (1 - 0.3 * wet))
        # branchlets near the tip
        if s > 25 and wet < 0.6:
            for j in range(5 if s > 80 else 3):
                u = 0.45 + 0.11 * j
                bx, by = math.cos(a) * L * u, math.sin(a) * L * u + droop * s * 0.2 * u
                for sg in (-1, 1):
                    ba = a + sg * 0.55
                    bl = L * 0.10 * (1.2 - u * 0.5)
                    line(c, bx, by, bx + math.cos(ba) * bl, by + math.sin(ba) * bl, lw * 0.6, col,
                         (0.4 if back else 0.75))
        if dew > 0 and s > 60 and (k % 5 == 2) and not back:
            u = 0.55 + 0.35 * ((k * 0.37) % 1)
            dx_, dy_ = math.cos(a) * L * u, math.sin(a) * L * u
            r = s * (0.020 + 0.012 * ((k * 0.61) % 1)) * dew
            c.arc(dx_, dy_, r, 0, TAU)
            fillc(c, (0.80, 0.88, 0.90), 0.55)
            c.arc(dx_ - r * 0.3, dy_ - r * 0.35, r * 0.35, 0, TAU)
            fillc(c, WHITE, 0.95)
            c.arc(dx_, dy_, r, 0, TAU)
            strokec(c, (0.35, 0.45, 0.48), max(0.5, r * 0.15), 0.5)
    # rim light on the crown
    if rim > 0 and wet < 0.5:
        pat = cairo.RadialGradient(0, -s * 0.2, 0, 0, -s * 0.2, s * 1.1)
        pat.add_color_stop_rgba(0, light[0], light[1], light[2], 0.18 * rim)
        pat.add_color_stop_rgba(1, light[0], light[1], light[2], 0.0)
        c.set_source(pat)
        c.arc(0, 0, s * 1.1, math.pi, TAU)
        c.fill()
    c.arc(0, 0, max(1.0, s * 0.035), 0, TAU)
    fillc(c, (0.85, 0.82, 0.72))
    c.restore()

def tiny_seed(c, x, y, s, rot, col=(1, 0.98, 0.92), a=0.9):
    """distant seed sprite"""
    c.save()
    c.translate(x, y)
    c.rotate(rot)
    line(c, 0, 0, 0, s * 1.3, max(0.6, s * 0.06), (0.7, 0.66, 0.56), a)
    for k in range(9):
        an = -math.pi + math.pi * k / 8
        line(c, 0, 0, math.cos(an) * s, math.sin(an) * s * 0.8, max(0.5, s * 0.05), col, a * 0.85)
    c.restore()

# ------------------------------------------------------------------ ladybug
def ladybug(c, x, y, s, ang=0.0, wings=0.0, t=0.0, legs=1.0):
    """ladybug centred at (x,y), body length 2s, heading ang (rad, 0 = pointing up)"""
    c.save()
    c.translate(x, y)
    c.rotate(ang)
    # legs
    if legs > 0:
        for k, yy in enumerate((-0.35, 0.05, 0.45)):
            sw = 0.25 * math.sin(t * 14 + k * 2.1) * legs
            for sg in (-1, 1):
                line(c, sg * s * 0.55, yy * s, sg * s * (1.05 + sw), (yy + 0.25 + sw * sg * 0.3) * s,
                     max(0.8, s * 0.07), INK, 0.9)
    # membrane wings
    if wings > 0.05:
        for sg in (-1, 1):
            c.save()
            c.translate(sg * s * 0.2, -s * 0.2)
            c.rotate(sg * (0.35 + 0.55 * wings))
            c.scale(0.5, 1.0)
            c.arc(0, s * 1.2 * wings, s * 1.3 * wings, 0, TAU)
            c.restore()
            fillc(c, (0.88, 0.92, 0.92), 0.45 * wings)
            c.save()
            c.translate(sg * s * 0.2, -s * 0.2)
            c.rotate(sg * (0.35 + 0.55 * wings))
            c.scale(0.5, 1.0)
            c.arc(0, s * 1.2 * wings, s * 1.3 * wings, 0, TAU)
            c.restore()
            strokec(c, (0.5, 0.55, 0.55), max(0.6, s * 0.03), 0.6 * wings)
    # head
    c.arc(0, -s * 0.85, s * 0.42, 0, TAU)
    fillc(c, INK)
    c.arc(-s * 0.18, -s * 0.95, s * 0.09, 0, TAU)
    fillc(c, WHITE)
    c.arc(s * 0.18, -s * 0.95, s * 0.09, 0, TAU)
    fillc(c, WHITE)
    # elytra
    for sg in (-1, 1):
        c.save()
        open_a = sg * wings * 0.55
        c.translate(0, -s * 0.5)
        c.rotate(open_a)
        c.translate(0, s * 0.5)
        c.move_to(0, -s * 0.55)
        c.curve_to(sg * s * 1.0, -s * 0.6, sg * s * 1.05, s * 0.8, 0, s * 0.95)
        c.close_path()
        pat = cairo.RadialGradient(sg * s * 0.3, -s * 0.2, s * 0.05, 0, 0, s * 1.1)
        pat.add_color_stop_rgb(0, 0.98, 0.42, 0.28)
        pat.add_color_stop_rgb(1, 0.72, 0.13, 0.10)
        c.set_source(pat)
        c.fill_preserve()
        strokec(c, INK, max(0.7, s * 0.06), 0.85)
        for (sx, sy, sr) in ((0.45, -0.15, 0.17), (0.55, 0.4, 0.14), (0.22, 0.65, 0.12)):
            c.arc(sg * s * sx, s * sy, s * sr, 0, TAU)
            fillc(c, INK)
        c.arc(sg * s * 0.28, -s * 0.28, s * 0.12, 0, TAU)
        fillc(c, WHITE, 0.55)
        c.restore()
    c.restore()

# ------------------------------------------------------------------ swallow
def swallow(c, x, y, s, heading=0.0, flap=0.0, col=(0.13, 0.16, 0.22)):
    c.save()
    c.translate(x, y)
    c.rotate(heading)
    w = math.sin(flap)
    # body (pointing +x)
    c.move_to(s * 1.0, 0)
    c.curve_to(s * 0.6, -s * 0.22, -s * 0.4, -s * 0.18, -s * 0.8, 0)
    c.curve_to(-s * 0.4, s * 0.18, s * 0.6, s * 0.22, s * 1.0, 0)
    fillc(c, col)
    # forked tail
    poly(c, [(-s * 0.7, 0), (-s * 1.6, -s * 0.35), (-s * 1.0, 0), (-s * 1.6, s * 0.35)])
    fillc(c, col)
    # wings
    for sg in (-1, 1):
        tipy = sg * s * (1.3 * (0.35 + 0.65 * abs(w)))
        c.move_to(s * 0.3, 0)
        c.curve_to(s * 0.1, tipy * 0.6, -s * 0.5, tipy * 0.9, -s * 0.9, tipy)
        c.curve_to(-s * 0.4, tipy * 0.5, -s * 0.1, sg * s * 0.1, -s * 0.1, 0)
        fillc(c, col)
    c.arc(s * 0.75, -s * 0.03, s * 0.07, 0, TAU)
    fillc(c, (0.75, 0.30, 0.20))
    c.restore()

# ------------------------------------------------------------------ dandelion pieces
def stem(c, pts, w, col=(0.42, 0.55, 0.30), ink=0.7):
    poly(c, pts, close=False)
    strokec(c, INK, w + 2.2, 0.55 * ink)
    poly(c, pts, close=False)
    strokec(c, col, w)
    poly(c, pts, close=False)
    strokec(c, lc(col, CREAM, 0.35), max(0.7, w * 0.25), 0.6)

def receptacle(c, x, y, r, rng):
    """bald dandelion head after the seeds left"""
    c.save()
    c.translate(x, y)
    c.scale(1, 0.75)
    c.arc(0, 0, r, 0, TAU)
    c.restore()
    fillc(c, (0.78, 0.74, 0.58))
    for _ in range(int(r * 2.5)):
        a = rng.uniform(0, TAU); d = r * math.sqrt(rng.random()) * 0.9
        c.arc(x + math.cos(a) * d, y + math.sin(a) * d * 0.75, max(0.6, r * 0.06), 0, TAU)
        fillc(c, (0.55, 0.50, 0.38), 0.7)
    c.save()
    c.translate(x, y)
    c.scale(1, 0.75)
    c.arc(0, 0, r, 0, TAU)
    c.restore()
    strokec(c, INK, max(0.8, r * 0.08), 0.6)
    # bracts curling down and outward, irregular
    br = np.random.default_rng(int(r * 7) + 5)
    if r < 22:
        for k in range(6):
            a = math.pi * (0.15 + 0.7 * k / 5) + br.uniform(-0.1, 0.1)
            bx, by = x + math.cos(a) * r * 0.8, y + math.sin(a) * r * 0.4
            line(c, bx, by, bx + math.cos(a) * r * 0.35, by + r * br.uniform(0.5, 0.8), max(0.8, r * 0.13),
                 (0.36, 0.48, 0.26), 0.95)
        return
    for k in range(11):
        a = math.pi * (0.06 + 0.88 * k / 10) + br.uniform(-0.08, 0.08)
        L = r * br.uniform(0.9, 1.6)
        bx, by = x + math.cos(a) * r * 0.85, y + math.sin(a) * r * 0.45
        ox = math.cos(a) * L
        for wdt, col, al in ((max(1.2, r * 0.16), INK, 0.35), (max(0.9, r * 0.11), (0.38, 0.50, 0.27), 0.95)):
            c.move_to(bx, by)
            c.curve_to(bx + ox * 0.6, by + L * 0.15, bx + ox * 1.1, by + L * 0.6, bx + ox * 0.9 - math.cos(a) * L * 0.1,
                       by + L * (0.95 + br.uniform(-0.1, 0.1)))
            strokec(c, col, wdt, al)

# ------------------------------------------------------------------ cel-paint: mask -> volume -> painted tones
def noise_tile(w, h, name='d', scale=1.0):
    T = tex(name)
    th, tw = T.shape
    if scale != 1.0:
        T = cv2.resize(T, (int(tw * scale), int(th * scale)), interpolation=cv2.INTER_LINEAR)
        th, tw = T.shape
    reps = (h // th + 1, w // tw + 1)
    return np.tile(T, reps)[:h, :w]

def _smooth(a, b, x):
    k = np.clip((x - a) / (b - a), 0, 1)
    return k * k * (3 - 2 * k)

_FBM = {}
def fbm(w, h, seed=0, octaves=5, base=6):
    key = (w, h, seed)
    if key not in _FBM:
        rng = np.random.default_rng(seed + 100)
        out = np.zeros((h, w), F32); amp = 1.0; tot = 0
        for o in range(octaves):
            gh = base * 2 ** o; gw = max(2, int(gh * w / h))
            r = rng.random((gh + 1, gw + 1)).astype(F32)
            out += cv2.resize(r, (w, h), interpolation=cv2.INTER_CUBIC) * amp
            tot += amp; amp *= 0.5
        out = out / tot
        out = (out - out.mean()) / (out.std() + 1e-6)
        _FBM[key] = out
    return _FBM[key]

def celpaint(mask, palette, light=(-0.35, -0.94), sigma=24, cuts=(0.42, 0.55, 0.70), soft=0.04, namp=0.07,
             ntex='d', nscale=1.0, hmix=0.5, gain=3.2, edge=1.0, extra=None, sigma2=None, blotch=0.07, seed=0):
    """mask: float (h,w) 0..1. palette: 4 colours shadow..highlight. returns premultiplied float RGBA"""
    h_, w_ = mask.shape
    def relief(sg):
        hg = cv2.GaussianBlur(mask, (0, 0), sg)
        s = sg * 0.9
        M = np.float32([[1, 0, light[0] * s], [0, 1, light[1] * s]])
        return cv2.warpAffine(hg, M, (w_, h_), borderMode=cv2.BORDER_REFLECT) - hg, hg
    r1, hgt = relief(sigma)
    v = 0.5 + r1 * gain + (hgt - 0.5) * hmix
    if sigma2:
        r2, _ = relief(sigma2)
        v = v + r2 * gain * 0.6
    if extra is not None:
        v = v + extra
    if blotch > 0:
        v = v + fbm(w_, h_, seed) * F32(blotch)
    if namp > 0:
        v = v + noise_tile(w_, h_, ntex, nscale) * F32(namp)
    pal = [np.array(p, F32) for p in palette]
    out = np.empty((h_, w_, 3), F32)
    out[:] = pal[0]
    for i, cut in enumerate(cuts):
        k = _smooth(cut - soft, cut + soft, v)[..., None]
        out = out * (1 - k) + pal[i + 1] * k
    a = cv2.GaussianBlur(mask, (0, 0), edge) if edge > 0 else mask
    a = np.clip(a, 0, 1)
    return np.dstack([out * a[..., None], a]).astype(F32)

def mask_draw(w, h, fn, rng):
    cv = Canvas(w, h)
    cv.c.set_source_rgba(1, 1, 1, 1)
    fn(cv.c, rng)
    return cv.rgba()[..., 3].copy()

class StaticArr:
    """like Static but the painter returns a premultiplied float RGBA array directly"""
    _cache = {}

    def __init__(self, key, w, h, painter):
        if key not in StaticArr._cache:
            arr = painter(w, h, np.random.default_rng(abs(hash(key)) % (2 ** 32)))
            StaticArr._cache[key] = np.clip(arr * 255 + 0.5, 0, 255).astype(np.uint8)
        self.img = StaticArr._cache[key]
        self.w, self.h = w, h

    view = Static.view

def over(dst, src_):
    """premultiplied over (arrays)"""
    a = src_[..., 3:4]
    return src_ + dst * (1 - a)

def cloud_lumps(c, rng, x, y, w, h, rows=2):
    """union-of-circles cumulus silhouette with a soft wavy flat-ish bottom at y"""
    n = max(4, int(w / h * 2.2) + 3)
    c.save()
    c.move_to(x - w, y - h * 3)
    c.line_to(x + w, y - h * 3)
    ph = rng.uniform(0, TAU)
    for k in range(41):
        xx = x + w - 2 * w * k / 40
        c.line_to(xx, y + h * 0.05 * math.sin(xx * 0.02 + ph) + h * 0.03 * math.sin(xx * 0.057))
    c.close_path()
    c.clip()
    for r_ in range(rows):
        nn = n if r_ == 0 else max(2, n // 2)
        span = 1.0 if r_ == 0 else 0.6
        for i in range(nn):
            u = (i / (nn - 1) * 2 - 1) * span + rng.uniform(-0.08, 0.08)
            env = math.sqrt(max(0.0, 1 - u * u))
            r = h * (0.26 + 0.66 * env) * rng.uniform(0.6, 1.15) * (1 if r_ == 0 else 0.8)
            cx = x + u * w / 2 * 0.92
            cy = y - r * (0.55 if r_ == 0 else 1.25) - (h * 0.25 * r_)
            c.new_sub_path()
            c.arc(cx, cy, r, 0, TAU)
    c.fill()
    c.restore()

# ------------------------------------------------------------------ dome height fields (lumpy volumes)
def dome_field(w, h, circles, clip=None):
    """circles: list of (x, y, r, amp). returns (height, mask) floats. clip(c) optional path for clipping"""
    cv = Canvas(w, h)
    c = cv.c
    c.set_source_rgb(0, 0, 0)
    c.paint()
    if clip is not None:
        clip(c)
        c.clip()
    c.set_operator(cairo.OPERATOR_LIGHTEN)
    for (x, y, r, amp) in circles:
        pat = cairo.RadialGradient(x, y, 0, x, y, r)
        for p, v in ((0, 1.0), (0.45, 0.89), (0.7, 0.71), (0.85, 0.53), (0.95, 0.31), (1.0, 0.0)):
            g = v * amp
            pat.add_color_stop_rgb(p, g, g, g)
        c.set_source(pat)
        c.arc(x, y, r, 0, TAU)
        c.fill()
    hgt = cv.rgba()[..., 0].copy()
    mask = np.clip(hgt / 0.04, 0, 1)
    return hgt, mask

def celpaint_h(hgt, mask, palette, light=(-0.35, -0.94), step=8.0, cuts=(0.42, 0.56, 0.70), soft=0.035, gain=6.0,
               hmix=0.25, blotch=0.06, namp=0.02, ntex='d', seed=0, edge=0.8, smooth=2.0, extra=None):
    """shade a dome height field. step = px offset toward the light for the relief"""
    h_, w_ = hgt.shape
    hs = cv2.GaussianBlur(hgt, (0, 0), smooth) if smooth > 0 else hgt
    M = np.float32([[1, 0, light[0] * step], [0, 1, light[1] * step]])
    hl = cv2.warpAffine(hs, M, (w_, h_), borderMode=cv2.BORDER_REFLECT)
    v = 0.5 + (hl - hs) * gain + (hs - 0.5) * hmix
    if extra is not None:
        v = v + extra
    if blotch > 0:
        v = v + fbm(w_, h_, seed) * F32(blotch)
    if namp > 0:
        v = v + noise_tile(w_, h_, ntex) * F32(namp)
    pal = [np.array(p, F32) for p in palette]
    out = np.empty((h_, w_, 3), F32)
    out[:] = pal[0]
    for i, cut in enumerate(cuts):
        k = _smooth(cut - soft, cut + soft, v)[..., None]
        out = out * (1 - k) + pal[i + 1] * k
    a = cv2.GaussianBlur(mask, (0, 0), edge) if edge > 0 else mask
    a = np.clip(a, 0, 1)
    return np.dstack([out * a[..., None], a]).astype(F32)

def cloud_circles(rng, x, y, w, h, rows=3):
    out = []
    n = max(4, int(w / h * 2.4) + 3)
    for r_ in range(rows):
        nn = n if r_ == 0 else max(2, int(n * (0.6 if r_ == 1 else 0.35)))
        span = (1.0, 0.7, 0.45)[min(r_, 2)]
        for i in range(nn):
            u = ((i / max(1, nn - 1)) * 2 - 1) * span + rng.uniform(-0.1, 0.1)
            env = math.sqrt(max(0.0, 1 - min(1, abs(u)) ** 2))
            r = h * (0.24 + 0.6 * env) * rng.uniform(0.65, 1.15) * (1, 0.85, 0.7)[min(r_, 2)]
            cx = x + u * w / 2 * 0.9
            cy = y - r * 0.5 - h * 0.32 * r_ + rng.uniform(-0.05, 0.05) * h
            out.append((cx, cy, r, 0.55 + 0.45 * r / h))
    return out

def flat_bottom_clip(x0, x1, y_of):
    def clip(c):
        c.move_to(x0, -10000)
        c.line_to(x1, -10000)
        for k in range(61):
            xx = x1 - (x1 - x0) * k / 60
            c.line_to(xx, y_of(xx))
        c.close_path()
    return clip
