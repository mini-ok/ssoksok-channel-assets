# -*- coding: utf-8 -*-
"""
빛지기 (THE KEEPER) -- render engine.
Two layers per frame: scene (cairo vector) + emission (cairo additive + float blobs) -> bloom -> grade.
Everything is a pure function of time.
"""
import cairo, numpy as np, math, cv2

cv2.setNumThreads(1)
W, H = 1920, 804          # 2.39:1 picture area
OH = 1080
BAR = (OH - H) // 2       # letterbox bars
FPS = 30
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
    return tuple(x * k for x in c)

def hx(h):
    h = h.lstrip('#')
    return tuple(int(h[i:i + 2], 16) / 255 for i in (0, 2, 4))

def nz(t, seed=0.0):
    return (0.5 * math.sin(t * 1.7 + seed * 3.1) + 0.3 * math.sin(t * 3.9 + seed * 1.3)
            + 0.2 * math.sin(t * 7.3 + seed * 5.7))

def aim(sx, sy, tx, ty):
    """limb angle (deg) from straight-down toward target"""
    return math.degrees(math.atan2(tx - sx, ty - sy))

def ease_io(u):
    u = min(1.0, max(0.0, u))
    return u * u * (3 - 2 * u)

# ------------------------------------------------------------------ palette
AMBER = (1.0, 0.62, 0.24)
AMBER_L = (1.0, 0.80, 0.52)
FLAME_IN = (1.0, 0.95, 0.80)
TOYLIGHT = (1.0, 0.90, 0.66)
TIN = (0.42, 0.48, 0.56)
TIN_D = (0.27, 0.31, 0.38)
TIN_DD = (0.16, 0.19, 0.24)
TIN_L = (0.62, 0.68, 0.75)
BRASS = (0.72, 0.54, 0.26)
BRASS_D = (0.44, 0.31, 0.15)
RED = (0.80, 0.20, 0.16)
RED_D = (0.55, 0.12, 0.10)
RED_L = (0.92, 0.36, 0.30)
COAT = (0.18, 0.24, 0.37)
COAT_D = (0.11, 0.15, 0.24)
SKIN = (0.94, 0.72, 0.58)
SKIN_D = (0.80, 0.55, 0.44)
BOOT = (0.12, 0.10, 0.11)
TOY = (0.98, 0.78, 0.16)
TOY_D = (0.80, 0.55, 0.08)
WOOD = (0.40, 0.25, 0.15)
WOOD_D = (0.24, 0.15, 0.09)
WOOD_L = (0.58, 0.40, 0.24)
IRON = (0.10, 0.11, 0.14)
IRON_L = (0.20, 0.22, 0.27)

# ------------------------------------------------------------------ frame
class Frame:
    def __init__(self, t):
        self.t = t
        self.s = cairo.ImageSurface(cairo.FORMAT_RGB24, W, H)
        self.e = cairo.ImageSurface(cairo.FORMAT_RGB24, W, H)
        self.c = cairo.Context(self.s)
        self.g = cairo.Context(self.e)
        for ctx in (self.c, self.g):
            ctx.set_source_rgb(0, 0, 0)
            ctx.paint()
            ctx.set_line_cap(cairo.LINE_CAP_ROUND)
            ctx.set_line_join(cairo.LINE_JOIN_ROUND)
        self.g.set_operator(cairo.OPERATOR_ADD)
        self.blobs = []
        self.streaks = []
        self.beams = []
        self.flash = 0.0
        self.flash_col = (1, 1, 1)
        self.lift = (0.004, 0.006, 0.014)
        self.gain = (1.0, 1.0, 1.0)
        self.sat = 1.0
        self.bloom = 1.0
        self.egain = 1.0
        self.vig = 0.45
        self.post = []        # callables(img) applied to float image after bloom
        self.zoom = 1.0

    # transforms on both layers
    def _both(self, name, *a):
        getattr(self.c, name)(*a)
        getattr(self.g, name)(*a)

    def save(self): self._both('save')
    def restore(self): self._both('restore')
    def translate(self, x, y): self._both('translate', x, y)
    def rotate(self, a): self._both('rotate', a)

    def scale(self, sx, sy=None):
        self._both('scale', sx, sx if sy is None else sy)

    def identity(self): self._both('identity_matrix')

    def camera(self, cx, cy, zoom=1.0, rot=0.0, sx=0.0, sy=0.0):
        self.identity()
        self.translate(W / 2 + sx, H / 2 + sy)
        self.rotate(rot)
        self.scale(zoom)
        self.translate(-cx, -cy)
        self.zoom = zoom

    def dev(self, x, y):
        return self.c.user_to_device(x, y)

    def dlen(self, d):
        dx, dy = self.c.user_to_device_distance(d, 0)
        return math.hypot(dx, dy)

    def blob(self, x, y, sig, col, amp):
        if amp <= 0.003:
            return
        X, Y = self.dev(x, y)
        self.blobs.append((X, Y, max(self.dlen(sig), 0.6), col, amp))

    def streak(self, x, y, length, thick, col, amp, vertical=False):
        if amp <= 0.003:
            return
        X, Y = self.dev(x, y)
        self.streaks.append((X, Y, self.dlen(length), max(self.dlen(thick), 0.8), col, amp, vertical))


# ------------------------------------------------------------------ primitive helpers
def poly(ctx, pts, close=True):
    ctx.move_to(*pts[0])
    for p in pts[1:]:
        ctx.line_to(*p)
    if close:
        ctx.close_path()

def rrect(ctx, x, y, w, h, r):
    r = min(r, w / 2, h / 2)
    ctx.new_sub_path()
    ctx.arc(x + w - r, y + r, r, -TAU / 4, 0)
    ctx.arc(x + w - r, y + h - r, r, 0, TAU / 4)
    ctx.arc(x + r, y + h - r, r, TAU / 4, TAU / 2)
    ctx.arc(x + r, y + r, r, TAU / 2, 3 * TAU / 4)
    ctx.close_path()

def fillc(ctx, col, a=1.0):
    ctx.set_source_rgba(col[0], col[1], col[2], a)
    ctx.fill()

def strokec(ctx, col, w, a=1.0):
    ctx.set_source_rgba(col[0], col[1], col[2], a)
    ctx.set_line_width(w)
    ctx.stroke()

def seg(ctx, x0, y0, x1, y1, w, col, a=1.0):
    ctx.move_to(x0, y0)
    ctx.line_to(x1, y1)
    strokec(ctx, col, w, a)

def limb_end(x, y, a, l):
    r = math.radians(a)
    return x + l * math.sin(r), y + l * math.cos(r)

def glow(fr, x, y, r, col, a):
    """soft additive radial glow on the emission layer (user coords)"""
    if a <= 0.003:
        return
    g = fr.g
    pat = cairo.RadialGradient(x, y, 0, x, y, r)
    pat.add_color_stop_rgba(0, col[0], col[1], col[2], min(1.0, a))
    pat.add_color_stop_rgba(0.3, col[0], col[1], col[2], min(1.0, a * 0.4))
    pat.add_color_stop_rgba(1, col[0], col[1], col[2], 0)
    g.set_source(pat)
    g.arc(x, y, r, 0, TAU)
    g.fill()

def cone(fr, x0, y0, ang, L, w0, w1, col, I, register=True):
    """volumetric light cone (smooth mesh gradient) on emission layer"""
    if I <= 0.003 or L < 2:
        return
    g = fr.g
    dx, dy = math.cos(ang), math.sin(ang)
    px, py = -dy, dx
    a0 = min(1.0, 0.85 * I)
    across = [(1.0, 0.0), (0.55, 0.30), (0.0, 1.0)]
    along = [(0.0, 1.0), (0.35, 0.5), (1.0, 0.0)]
    mesh = cairo.MeshPattern()
    for side in (1, -1):
        for (fa, aa), (fb, ab) in zip(across[:-1], across[1:]):
            for (la, va), (lb, vb) in zip(along[:-1], along[1:]):
                wa = w0 + (w1 - w0) * la
                wb = w0 + (w1 - w0) * lb
                ax_, ay_ = x0 + dx * L * la, y0 + dy * L * la
                bx_, by_ = x0 + dx * L * lb, y0 + dy * L * lb
                mesh.begin_patch()
                mesh.move_to(ax_ + px * wa * fa * side, ay_ + py * wa * fa * side)
                mesh.line_to(bx_ + px * wb * fa * side, by_ + py * wb * fa * side)
                mesh.line_to(bx_ + px * wb * fb * side, by_ + py * wb * fb * side)
                mesh.line_to(ax_ + px * wa * fb * side, ay_ + py * wa * fb * side)
                mesh.set_corner_color_rgba(0, col[0], col[1], col[2], a0 * aa * va)
                mesh.set_corner_color_rgba(1, col[0], col[1], col[2], a0 * aa * vb)
                mesh.set_corner_color_rgba(2, col[0], col[1], col[2], a0 * ab * vb)
                mesh.set_corner_color_rgba(3, col[0], col[1], col[2], a0 * ab * va)
                mesh.end_patch()
    g.set_source(mesh)
    g.paint()
    if register:
        X0, Y0 = fr.dev(x0, y0)
        X1, Y1 = fr.dev(x0 + dx * L, y0 + dy * L)
        fr.beams.append((X0, Y0, X1, Y1, fr.dlen(w0), fr.dlen(w1), col, I))

def beam_light(fr, X, Y):
    """brightness of registered beams at device points (arrays) -> (N,3)"""
    out = np.zeros((len(X), 3), F32)
    for (X0, Y0, X1, Y1, w0, w1, col, I) in fr.beams:
        ax, ay = X1 - X0, Y1 - Y0
        L2 = ax * ax + ay * ay + 1e-6
        L = math.sqrt(L2)
        u = ((X - X0) * ax + (Y - Y0) * ay) / L2
        perp = np.abs((X - X0) * ay - (Y - Y0) * ax) / L
        hw = w0 + (w1 - w0) * np.clip(u, 0, 1)
        b = np.where((u > 0) & (u < 1), (1 - np.clip(u, 0, 1)) ** 0.6 * np.clip(1 - perp / hw, 0, 1) ** 0.7, 0)
        out += (b * I)[:, None] * np.array(col, F32)[None, :]
    return out

def lightning_amp(t, events):
    """events: list of (t0, amp). double-strike flicker"""
    f = 0.0
    for t0, a in events:
        d = t - t0
        if -0.01 <= d < 0.9:
            d = max(d, 0)
            f += a * (math.exp(-d / 0.07) + 0.75 * math.exp(-((d - 0.17) / 0.045) ** 2)
                      + 0.35 * math.exp(-((d - 0.33) / 0.06) ** 2))
    return f

# ------------------------------------------------------------------ atmosphere
def sky(fr, stops, y0=-300, y1=H + 300, x0=-600, x1=W + 600):
    c = fr.c
    pat = cairo.LinearGradient(0, y0, 0, y1)
    for p, col in stops:
        pat.add_color_stop_rgb(p, *col)
    c.set_source(pat)
    c.rectangle(x0, y0, x1 - x0, y1 - y0)
    c.fill()

def clouds(fr, t, x0, x1, y0, y1, n, rmin, rmax, dark, light, seed=1, lit=0.0, drift=8.0, alpha=1.0,
           litcol=(0.80, 0.84, 1.0), underlit=None, stretch=1.9):
    """soft stretched cloud bank. underlit: (x, y, r, col, a) warm underside light (beam)"""
    c = fr.c
    rng = np.random.default_rng(seed)
    n2 = int(n * 2.2)
    xs = rng.random(n2) * (x1 - x0) + x0
    ys = y0 + (y1 - y0) * rng.random(n2) ** 0.9
    rs = (rmin + (rmax - rmin) * rng.random(n2) ** 1.6) * 0.8
    order = np.argsort(ys)
    span = (x1 - x0)
    # base veil
    pat = cairo.LinearGradient(0, y0 - rmax * 0.3, 0, y1 + rmax * 0.4)
    pat.add_color_stop_rgba(0, dark[0], dark[1], dark[2], 0.0)
    pat.add_color_stop_rgba(0.35, dark[0], dark[1], dark[2], 0.85 * alpha)
    pat.add_color_stop_rgba(0.8, dark[0], dark[1], dark[2], 0.6 * alpha)
    pat.add_color_stop_rgba(1, dark[0], dark[1], dark[2], 0.0)
    c.set_source(pat)
    c.rectangle(x0 - 800, y0 - rmax, span + 1600, (y1 - y0) + rmax * 2)
    c.fill()
    top = lc(light, litcol, min(1.0, lit))
    mid = lc(dark, top, 0.30 + 0.5 * min(1.0, lit))
    for i in order:
        x = (xs[i] + drift * t * (0.6 + 0.6 * (ys[i] - y0) / (y1 - y0 + 1e-6)) - x0) % span + x0
        y = ys[i]
        r = rs[i]
        c.save()
        c.translate(x, y)
        c.scale(stretch, 1.0)
        pat = cairo.RadialGradient(-r * 0.15, -r * 0.45, r * 0.05, 0, 0, r)
        pat.add_color_stop_rgba(0, top[0], top[1], top[2], 0.9 * alpha)
        pat.add_color_stop_rgba(0.45, mid[0], mid[1], mid[2], 0.85 * alpha)
        pat.add_color_stop_rgba(0.8, dark[0], dark[1], dark[2], 0.6 * alpha)
        pat.add_color_stop_rgba(1, dark[0], dark[1], dark[2], 0.0)
        c.set_source(pat)
        c.arc(0, 0, r, 0, TAU)
        c.fill()
        c.restore()
        if underlit is not None:
            ux, uy, ur, ucol, ua = underlit
            d = math.hypot(x - ux, y - uy)
            k = max(0.0, 1 - d / ur)
            if k > 0.01:
                fr.g.save()
                fr.g.translate(x, y + r * 0.35)
                fr.g.scale(stretch, 0.7)
                pg = cairo.RadialGradient(0, 0, 0, 0, 0, r)
                pg.add_color_stop_rgba(0, ucol[0], ucol[1], ucol[2], ua * k)
                pg.add_color_stop_rgba(1, ucol[0], ucol[1], ucol[2], 0)
                fr.g.set_source(pg)
                fr.g.arc(0, 0, r, 0, TAU)
                fr.g.fill()
                fr.g.restore()

def rain(fr, t, n, seed=7, speed=1500, ang=0.20, length=42, alpha=0.20, col=(0.66, 0.74, 0.88), width=1.3,
         sparkle=1.0):
    """screen-space rain; drops inside registered beams glint on the emission layer"""
    if n <= 0 or alpha <= 0.002:
        return
    rng = np.random.default_rng(seed)
    x0 = rng.random(n) * (W + 600) - 300
    y0 = rng.random(n) * (H + 300)
    d = 0.35 + 0.65 * rng.random(n)
    sp = speed * d
    y = (y0 + sp * t) % (H + 300) - 150
    x = (x0 + sp * t * math.tan(ang)) % (W + 600) - 300
    L = length * d
    dx = L * math.sin(ang)
    dy = L * math.cos(ang)
    c = fr.c
    c.save()
    c.identity_matrix()
    for lo, hi, a, w in ((0.35, 0.6, alpha * 0.45, width * 0.7), (0.6, 0.82, alpha * 0.75, width),
                         (0.82, 1.01, alpha, width * 1.45)):
        m = np.where((d >= lo) & (d < hi))[0]
        for i in m:
            c.move_to(x[i], y[i])
            c.line_to(x[i] + dx[i], y[i] + dy[i])
        strokec(c, col, w, a)
    c.restore()
    if fr.beams and sparkle > 0:
        mx = x + dx * 0.5
        my = y + dy * 0.5
        b = beam_light(fr, mx, my) * sparkle
        bl = b.max(axis=1)
        g = fr.g
        g.save()
        g.identity_matrix()
        for lo, hi in ((0.06, 0.2), (0.2, 0.45), (0.45, 0.8), (0.8, 99)):
            m = np.where((bl >= lo) & (bl < hi))[0]
            if len(m) == 0:
                continue
            col_m = b[m].mean(axis=0) / max(bl[m].mean(), 1e-6)
            for i in m:
                g.move_to(x[i], y[i])
                g.line_to(x[i] + dx[i], y[i] + dy[i])
            lvl = min(0.75, (lo + min(hi, 1.4)) * 0.4)
            g.set_source_rgba(col_m[0], col_m[1], col_m[2], lvl)
            g.set_line_width(width * 1.1)
            g.stroke()
        g.restore()

def bolt_points(x0, y0, x1, y1, seed, disp=70, depth=7):
    rng = np.random.default_rng(seed)
    pts = [(x0, y0), (x1, y1)]
    for _ in range(depth):
        new = [pts[0]]
        for (ax, ay), (bx, by) in zip(pts[:-1], pts[1:]):
            mx = (ax + bx) / 2 + rng.normal() * disp
            my = (ay + by) / 2 + rng.normal() * disp * 0.25
            new += [(mx, my), (bx, by)]
        pts = new
        disp *= 0.55
    return pts

def bolt(fr, x0, y0, x1, y1, seed, I, width=1.0):
    if I <= 0.01:
        return
    g = fr.g
    rng = np.random.default_rng(seed + 100)
    paths = [bolt_points(x0, y0, x1, y1, seed)]
    for k in range(3):
        p = paths[0][int(len(paths[0]) * (0.25 + 0.5 * rng.random()))]
        ex = p[0] + rng.normal() * 160
        ey = p[1] + abs(rng.normal()) * 140 + 60
        paths.append(bolt_points(p[0], p[1], ex, ey, seed + 10 + k, disp=35, depth=5))
    for pi, pts in enumerate(paths):
        f = 1.0 if pi == 0 else 0.45
        for w, a, col in ((16, 0.06, (0.55, 0.55, 1.0)), (6, 0.22, (0.75, 0.75, 1.0)), (2.0, 1.0, (1, 1, 1))):
            poly(g, pts, close=False)
            g.set_source_rgba(col[0], col[1], col[2], min(1.0, a * I * f))
            g.set_line_width(w * width * (1 if pi == 0 else 0.6))
            g.stroke()

def spray(fr, x, y, t, t0, n, seed, spread=260, up=520, life=1.3, size=3.2, col=(0.80, 0.86, 0.95), alpha=0.85,
          grav=900, lit=None):
    a = t - t0
    if a < 0 or a > life:
        return
    rng = np.random.default_rng(seed)
    vx = rng.normal(0, spread * 0.5, n)
    vy = -up * (0.35 + 0.65 * rng.random(n))
    sz = size * (0.4 + rng.random(n))
    px = x + vx * a
    py = y + vy * a + 0.5 * grav * a * a
    fade = (1 - a / life) ** 1.2
    c = fr.c
    for i in range(n):
        c.arc(px[i], py[i], sz[i], 0, TAU)
        c.new_sub_path()
    fillc(c, col, alpha * fade)
    if lit is not None and lit > 0.01:
        for i in range(n):
            fr.g.arc(px[i], py[i], sz[i] * 1.6, 0, TAU)
            fr.g.new_sub_path()
        fillc(fr.g, AMBER_L, min(1.0, lit * fade))

def gulls(fr, t, items):
    """items: list of (x, y, size, phase, vx)"""
    c = fr.c
    for (x, y, s, ph, vx) in items:
        xx = x + vx * t
        f = math.sin(t * 7 + ph)
        wy = -s * 0.5 * f
        c.move_to(xx - s, y + wy)
        c.curve_to(xx - s * 0.5, y - s * 0.35 + wy * 0.3, xx - s * 0.15, y - s * 0.15, xx, y)
        c.curve_to(xx + s * 0.15, y - s * 0.15, xx + s * 0.5, y - s * 0.35 + wy * 0.3, xx + s, y + wy)
        strokec(c, (0.22, 0.17, 0.22), max(1.4, s * 0.12))


# ------------------------------------------------------------------ sea
class Sea:
    def __init__(self, horizon, bottom, far, near, n=8, amp=10.0, speed=1.0, seed=3, foam=(0.62, 0.70, 0.80),
                 foam_a=0.35, choppy=0.6, wl=1.0, x0=-700, x1=W + 700):
        self.h, self.b, self.far, self.near = horizon, bottom, far, near
        self.n, self.amp, self.speed, self.foam, self.foam_a = n, amp, speed, foam, foam_a
        self.choppy, self.wl, self.x0, self.x1 = choppy, wl, x0, x1
        rng = np.random.default_rng(seed)
        self.ph = rng.random((n, 3)) * TAU

    def yb(self, k):
        u = (k + 1) / self.n
        return self.h + (self.b - self.h) * u ** 1.6

    def edge(self, x, k, t):
        u = (k + 1) / self.n
        A = self.amp * (0.10 + 0.90 * u ** 1.4)
        f = 0.0060 / (0.22 + u) / self.wl
        p = self.ph[k]
        w = (np.sin(x * f + t * self.speed * (0.7 + 0.9 * u) + p[0])
             + 0.5 * np.sin(x * f * 2.13 - t * self.speed * (0.9 + 1.1 * u) + p[1])
             + 0.22 * np.sin(x * f * 4.7 + t * self.speed * 1.9 + p[2]))
        w = w + self.choppy * np.maximum(w, 0) ** 2 * 0.35
        return self.yb(k) - A * w, w

    def surface(self, x, k, t):
        y, _ = self.edge(np.array([x - 6.0, x, x + 6.0]), k, t)
        return float(y[1]), math.atan2(y[2] - y[0], 12.0)

    def draw(self, fr, t, k0=0, k1=None, lit=0.0, litcol=(0.9, 0.85, 0.75), foam_scale=1.0, tint=None):
        c = fr.c
        xs = np.linspace(self.x0, self.x1, 320)
        for k in range(k0, self.n if k1 is None else k1):
            u = (k + 1) / self.n
            y, w = self.edge(xs, k, t)
            col = lc(self.far, self.near, u ** 0.8)
            if lit > 0:
                col = lc(col, litcol, min(1.0, lit * (1 - 0.5 * u)))
            c.move_to(xs[0], y[0])
            for xi, yi in zip(xs[1:], y[1:]):
                c.line_to(xi, yi)
            c.line_to(self.x1, self.b + 900)
            c.line_to(self.x0, self.b + 900)
            c.close_path()
            fillc(c, col)
            # foam / crest highlights
            crest = w > 0.75
            run = False
            for i in range(len(xs)):
                if crest[i] and not run:
                    c.move_to(xs[i], y[i]); run = True
                elif crest[i] and run:
                    c.line_to(xs[i], y[i])
                elif run:
                    run = False
            fc = self.foam if tint is None else lc(self.foam, tint, 0.5)
            strokec(c, fc, 1.0 + 3.0 * u, self.foam_a * foam_scale * (0.3 + 0.7 * u))


# ------------------------------------------------------------------ characters
ROBOT_DEF = dict(lean=0.0, head=0.0, armF=(12, 18), armB=(-8, 14), legF=(0, 0), legB=(0, 0))

def _apply_lights(fr, lights, extra=()):
    """paint ATOP lighting inside the current group (device coords)"""
    c = fr.c
    c.save()
    c.identity_matrix()
    c.set_operator(cairo.OPERATOR_ATOP)
    for (X, Y, R, col, a) in list(lights) + list(extra):
        if a <= 0.004:
            continue
        pat = cairo.RadialGradient(X, Y, 0, X, Y, R)
        pat.add_color_stop_rgba(0, col[0], col[1], col[2], min(1.0, a))
        pat.add_color_stop_rgba(0.5, col[0], col[1], col[2], min(1.0, a * 0.45))
        pat.add_color_stop_rgba(1, col[0], col[1], col[2], 0)
        c.set_source(pat)
        c.paint()
    c.restore()

def dev_light(fr, x, y, r, col, a):
    """convert a light in current user coords to device-space light tuple"""
    X, Y = fr.dev(x, y)
    return (X, Y, fr.dlen(r), col, a)

def lantern_head(fr, light, inner, t, shade=1.0, door=0.0, glass_dark=(0.04, 0.05, 0.07)):
    """lantern in head-local coords (pivot at 0,0; up negative). returns flame device pos"""
    c = fr.c
    sh = shade
    # base cap
    poly(c, [(-13, -1), (13, -1), (11, -6.5), (-11, -6.5)])
    fillc(c, cm(BRASS_D, sh))
    seg(c, -12.5, -1.5, 12.5, -1.5, 1.1, cm(BRASS, sh))
    # glass interior
    warm = AMBER if inner == 'flame' else TOYLIGHT
    gcol = lc(cm(glass_dark, sh), cm(warm, 0.42), min(1.0, light * 0.55))
    rrect(c, -10.5, -27.5, 21, 21.5, 2.5)
    fillc(c, gcol)
    if light > 0.02:
        pat = cairo.RadialGradient(0, -16, 0, 0, -16, 15)
        pat.add_color_stop_rgba(0, 1, 0.88, 0.65, min(1.0, 0.45 * light))
        pat.add_color_stop_rgba(1, warm[0], warm[1], warm[2], 0.0)
        c.set_source(pat)
        rrect(c, -10.5, -27.5, 21, 21.5, 2.5)
        c.fill()
    fx, fy = 0.0, -15.5
    if inner == 'flame' and light > 0.01:
        sway = 0.9 * math.sin(t * 7.3) + 0.5 * math.sin(t * 13.1 + 1)
        hgt = 9.5 * (0.35 + 0.65 * light) * (1 + 0.08 * math.sin(t * 17.0))
        wid = 4.4 * (0.5 + 0.5 * light)
        for ctx, cols in ((c, (AMBER, FLAME_IN)), (fr.g, (cm(AMBER, 0.45 * light), cm(FLAME_IN, 0.55 * light)))):
            ctx.move_to(fx, fy + 3.5)
            ctx.curve_to(fx - wid, fy + 2, fx - wid * 0.6, fy - hgt * 0.5, fx + sway, fy - hgt)
            ctx.curve_to(fx + wid * 0.6, fy - hgt * 0.5, fx + wid, fy + 2, fx, fy + 3.5)
            ctx.set_source_rgb(*cols[0])
            ctx.fill()
            ctx.arc(fx, fy, wid * 0.55, 0, TAU)
            ctx.set_source_rgb(*cols[1])
            ctx.fill()
        fr.blob(fx, fy - 1, 3.2, FLAME_IN, 1.1 * light)
        fr.blob(fx, fy - 1, 10, AMBER, 0.28 * light)
        fr.blob(fx, fy - 1, 34, AMBER, 0.07 * light)
    elif inner == 'toy':
        # the child's toy flashlight standing inside the lantern
        rrect(c, -3.2, -20, 6.4, 13.5, 1.5)
        fillc(c, cm(TOY, sh))
        rrect(c, -3.8, -22.5, 7.6, 3.4, 1.2)
        fillc(c, cm(RED, sh))
        seg(c, -1.0, -17, -1.0, -9, 0.8, (1, 1, 1), 0.35)
        if light > 0.01:
            c.arc(0, -22.8, 2.6, 0, TAU)
            fillc(c, FLAME_IN)
            fr.g.arc(0, -22.8, 2.6, 0, TAU)
            fillc(fr.g, cm(TOYLIGHT, 0.6 * light))
            cone(fr, 0, -23, -math.pi / 2, 5.5, 2.4, 9, TOYLIGHT, 0.5 * light, register=False)
            fr.blob(0, -23, 3.0, FLAME_IN, 1.1 * light)
            fr.blob(0, -19, 10, TOYLIGHT, 0.28 * light)
            fr.blob(0, -19, 34, TOYLIGHT, 0.07 * light)
        fy = -21
    # bars + glass frame
    rrect(c, -10.5, -27.5, 21, 21.5, 2.5)
    strokec(c, cm(TIN_DD, sh), 1.6)
    for bx in (-5.2, 5.2):
        seg(c, bx, -27, bx, -7, 1.1, cm(TIN_DD, sh), 0.85)
    # glass highlight
    c.move_to(-8.3, -24.5)
    c.line_to(-8.3, -12)
    strokec(c, (1, 1, 1), 1.2, 0.18 * sh + 0.08)
    if door > 0:
        # open door: swung glass pane hinged on the left edge
        dw = 21 * math.cos(door * 1.35)
        poly(c, [(-10.5, -27.5), (-10.5 - dw * 0.55, -28.5), (-10.5 - dw * 0.55, -5.5), (-10.5, -6.0)])
        fillc(c, (0.6, 0.7, 0.8), 0.10)
        strokec(c, cm(TIN_DD, sh), 1.3)
    # top cap + ring
    poly(c, [(-11.5, -27.5), (11.5, -27.5), (7.5, -32.5), (-7.5, -32.5)])
    fillc(c, cm(BRASS_D, sh))
    c.arc(0, -33.5, 2.0, 0, TAU)
    fillc(c, cm(BRASS, sh))
    c.arc(0, -37.5, 4.0, 0, TAU)
    strokec(c, cm(BRASS, sh), 1.5)
    return fr.dev(fx, fy)

def robot(fr, x, y, s, P=None, light=1.0, inner='flame', facing=1, lights=(), t=0.0, shade=1.0, door=0.0,
          prop=None, self_light=1.0):
    """x,y = hip (pelvis) in parent coords. returns dict of device points."""
    P = dict(ROBOT_DEF, **(P or {}))
    c = fr.c
    out = {}
    c.push_group()
    fr.save()
    fr.translate(x, y)
    fr.scale(s * facing, s)
    sh = shade

    def leg(hx, hip, knee, col):
        kx, ky = limb_end(hx, 0, hip, 19)
        fx, fy = limb_end(kx, ky, hip + knee, 19)
        seg(c, hx, 0, kx, ky, 6.6, col)
        seg(c, kx, ky, fx, fy, 5.6, col)
        c.arc(kx, ky, 3.7, 0, TAU)
        fillc(c, lc(col, (0, 0, 0), 0.3))
        c.save()
        c.translate(fx, fy)
        c.rotate(math.radians(-(hip + knee)) * 0.6)
        rrect(c, -4.5, -1.5, 13, 5, 2.2)
        fillc(c, lc(col, (0, 0, 0), 0.25))
        c.restore()

    def arm(sx, sy, sha, ela, col):
        ex, ey = limb_end(sx, sy, sha, 13)
        hx_, hy_ = limb_end(ex, ey, sha + ela, 12)
        seg(c, sx, sy, ex, ey, 5.6, col)
        seg(c, ex, ey, hx_, hy_, 5.0, col)
        c.arc(ex, ey, 3.2, 0, TAU)
        fillc(c, lc(col, (0, 0, 0), 0.3))
        # pincer hand
        a = math.radians(sha + ela)
        dx, dy = math.sin(a), math.cos(a)
        px, py = -dy, dx
        c.arc(hx_, hy_, 3.4, 0, TAU)
        fillc(c, lc(col, (0, 0, 0), 0.15))
        for side in (-1, 1):
            seg(c, hx_ + px * 1.6 * side, hy_ + py * 1.6 * side,
                hx_ + dx * 4.6 + px * 2.6 * side, hy_ + dy * 4.6 + py * 2.6 * side, 1.7, lc(col, (0, 0, 0), 0.2))
        return hx_, hy_

    leg(-5, P['legB'][0], P['legB'][1], cm(TIN_DD, sh))
    fr.save()
    fr.rotate(math.radians(P['lean']))
    hb = arm(-13, -25, P['armB'][0], P['armB'][1], cm(TIN_DD, sh))
    out['handB'] = fr.dev(*hb)
    fr.restore()
    leg(5, P['legF'][0], P['legF'][1], cm(TIN_D, sh))
    fr.save()
    fr.rotate(math.radians(P['lean']))
    # torso
    rrect(c, -17, -33, 34, 34, 8)
    pat = cairo.LinearGradient(-17, 0, 17, 0)
    pat.add_color_stop_rgb(0, *cm(TIN_L, sh))
    pat.add_color_stop_rgb(0.45, *cm(TIN, sh))
    pat.add_color_stop_rgb(1, *cm(TIN_D, sh))
    c.set_source(pat)
    c.fill()
    rrect(c, -11, -25, 22, 17, 4)
    fillc(c, cm(TIN_D, sh))
    c.arc(0, -16.5, 4.8, 0, TAU)
    fillc(c, cm(BRASS, sh))
    c.arc(0, -16.5, 3.4, 0, TAU)
    fillc(c, cm((0.9, 0.86, 0.72), sh))
    na = math.radians(200 + 40 * math.sin(t * 0.7))
    seg(c, 0, -16.5, 2.8 * math.sin(na), -16.5 + 2.8 * math.cos(na), 0.8, (0.2, 0.1, 0.05))
    for rx, ry in ((-13, -29), (13, -29), (-13, -3), (13, -3)):
        c.arc(rx, ry, 1.2, 0, TAU)
        fillc(c, cm(TIN_L, sh))
    # neck
    rrect(c, -3.6, -38, 7.2, 6, 1.5)
    fillc(c, cm(TIN_DD, sh))
    # head
    fr.save()
    fr.translate(0, -35)
    fr.rotate(math.radians(P['head']))
    fpos = lantern_head(fr, light, inner, t, shade=sh, door=door)
    out['flame'] = fpos
    out['head'] = fr.dev(0, -16)
    if prop == 'scope':
        # brass telescope held to the lantern
        seg(fr.c, 9, -17, 40, -21, 6.5, cm(BRASS_D, sh))
        seg(fr.c, 24, -19, 40, -21, 8.0, cm(BRASS, sh))
        seg(fr.c, 38, -21, 42, -21.4, 9.0, cm(BRASS_D, sh))
    fr.restore()
    hf = arm(13, -25, P['armF'][0], P['armF'][1], cm(TIN, sh))
    out['handF'] = fr.dev(*hf)
    fr.restore()
    fr.restore()
    selfl = []
    if light > 0.01 and self_light > 0:
        col = AMBER if inner == 'flame' else TOYLIGHT
        selfl = [(fpos[0], fpos[1], 55 * s, col, 0.22 * light * self_light)]
    _apply_lights(fr, lights, selfl)
    c.pop_group_to_source()
    c.paint()
    return out

CHILD_DEF = dict(mode='sit', lean=0.0, head=0.0, armF=(95, 10), armB=(20, 30), legF=(85, -80), legB=(80, -75),
                 brow=0.0, eyes=1.0, mouth=0, fl_on=0.0, fl_len=420, fl_w=55, look=0.0)

def child(fr, x, y, s, P=None, facing=1, lights=(), t=0.0, shade=1.0, flashlight=True):
    """x,y = hip/seat point. faces +x when facing=1."""
    P = dict(CHILD_DEF, **(P or {}))
    c = fr.c
    out = {}
    sh = shade
    c.push_group()
    fr.save()
    fr.translate(x, y)
    fr.scale(s * facing, s)

    def leg(hx, hip, knee, col):
        kx, ky = limb_end(hx, 0, hip, 10)
        fx, fy = limb_end(kx, ky, hip + knee, 10.5)
        seg(c, hx, 0, kx, ky, 6.0, col)
        seg(c, kx, ky, fx, fy, 5.4, col)
        c.save()
        c.translate(fx, fy)
        rrect(c, -2.8, -3.5, 7.5, 5, 2)
        fillc(c, cm(BOOT, sh))
        c.restore()

    leg(-1.5, P['legB'][0], P['legB'][1], cm(COAT_D, sh))
    leg(1.5, P['legF'][0], P['legF'][1], cm(COAT, sh))
    fr.save()
    fr.rotate(math.radians(P['lean']))
    # back arm
    sx, sy = -1.5, -17.5
    ex, ey = limb_end(sx, sy, P['armB'][0], 8.5)
    hx_, hy_ = limb_end(ex, ey, P['armB'][0] + P['armB'][1], 8)
    seg(c, sx, sy, ex, ey, 4.8, cm(COAT_D, sh))
    seg(c, ex, ey, hx_, hy_, 4.4, cm(COAT_D, sh))
    c.arc(hx_, hy_, 2.3, 0, TAU)
    fillc(c, cm(SKIN_D, sh))
    out['handB'] = fr.dev(hx_, hy_)
    # coat body
    long = 6 if P['mode'] == 'stand' else 2.5
    c.move_to(-9.5, long)
    c.curve_to(-9, -6, -7.5, -16, -5.5, -20.5)
    c.line_to(5.5, -20.5)
    c.curve_to(7.5, -16, 9.5, -6, 10, long)
    c.close_path()
    pat = cairo.LinearGradient(-9, 0, 10, 0)
    pat.add_color_stop_rgb(0, *cm(lc(COAT, (1, 1, 1), 0.08), sh))
    pat.add_color_stop_rgb(1, *cm(COAT_D, sh))
    c.set_source(pat)
    c.fill()
    seg(c, 3.5, -19, 4.5, long - 1, 0.9, cm(COAT_D, sh))
    for by in (-14, -9, -4):
        c.arc(5.6, by, 0.9, 0, TAU)
        fillc(c, cm(TOY, sh))
    # collar
    poly(c, [(-6, -20.5), (6, -20.5), (4.5, -17.5), (0, -19), (-4.5, -17.5)])
    fillc(c, cm(COAT_D, sh))
    # head
    fr.save()
    fr.translate(0, -21)
    fr.rotate(math.radians(P['head']))
    c.arc(0.8, -9.2, 8.8, 0, TAU)
    fillc(c, cm(SKIN, sh))
    # hair tuft under hat
    c.arc(-5.8, -8.5, 3.6, 0, TAU)
    fillc(c, cm((0.18, 0.11, 0.08), sh))
    # eyes / brows / mouth  (face toward +x)
    ex1, ex2, ey_ = 3.0 + P['look'], 7.0 + P['look'], -9.4
    if P['eyes'] > 0.3:
        for exx in (ex1, ex2):
            c.arc(exx, ey_, 1.15, 0, TAU)
            fillc(c, cm((0.10, 0.07, 0.07), sh))
    else:
        for exx in (ex1, ex2):
            c.move_to(exx - 1.2, ey_)
            c.curve_to(exx - 0.5, ey_ + 0.8, exx + 0.5, ey_ + 0.8, exx + 1.2, ey_)
        strokec(c, cm((0.10, 0.07, 0.07), sh), 0.8)
    b = P['brow']
    for exx, sgn in ((ex1, -1), (ex2, 1)):
        c.move_to(exx - 1.4, ey_ - 2.6 + sgn * b * 0.7)
        c.line_to(exx + 1.4, ey_ - 2.6 - sgn * b * 0.7)
    strokec(c, cm((0.18, 0.11, 0.08), sh), 0.7, 0.85)
    c.arc(7.6, -6.3, 1.8, 0, TAU)
    fillc(c, (0.95, 0.45, 0.45), 0.35)
    if P['mouth'] == 1:
        c.move_to(4.2, -5.0)
        c.curve_to(5.0, -3.6, 6.6, -3.6, 7.4, -5.0)
        strokec(c, cm((0.35, 0.12, 0.10), sh), 0.8)
    elif P['mouth'] == -1:
        c.arc(5.8, -4.3, 0.9, 0, TAU)
        fillc(c, cm((0.35, 0.12, 0.10), sh))
    else:
        seg(c, 4.6, -4.6, 6.8, -4.6, 0.7, cm((0.35, 0.12, 0.10), sh))
    # red knit hat
    c.move_to(-9.6, -10.5)
    c.curve_to(-10, -20, 10.5, -22, 10.8, -10.5)
    c.close_path()
    fillc(c, cm(RED, sh))
    for k in range(-3, 4):
        c.move_to(k * 2.6, -11.5)
        c.curve_to(k * 2.4, -15, k * 2.0, -18, k * 1.6, -19.5)
    strokec(c, cm(RED_D, sh), 0.6, 0.6)
    rrect(c, -10.2, -12.4, 21.4, 4.2, 1.6)
    fillc(c, cm(RED_D, sh))
    bob = math.sin(t * 6.0) * 0.6
    c.arc(0.4 + bob, -21.6, 3.5, 0, TAU)
    fillc(c, cm(RED_L, sh))
    out['head'] = fr.dev(1, -10)
    fr.restore()
    # front arm with flashlight
    sx, sy = 1.5, -17.5
    ex, ey = limb_end(sx, sy, P['armF'][0], 8.5)
    fa = P['armF'][0] + P['armF'][1]
    hx_, hy_ = limb_end(ex, ey, fa, 8)
    seg(c, sx, sy, ex, ey, 4.8, cm(COAT, sh))
    seg(c, ex, ey, hx_, hy_, 4.4, cm(COAT, sh))
    if flashlight:
        a = math.radians(fa)
        dx, dy = math.sin(a), math.cos(a)
        tx, ty = hx_ + dx * 7.5, hy_ + dy * 7.5
        seg(c, hx_ - dx * 2, hy_ - dy * 2, tx, ty, 3.6, cm(TOY, sh))
        seg(c, tx - dx * 1.2, ty - dy * 1.2, tx + dx * 0.6, ty + dy * 0.6, 4.6, cm(RED, sh))
        if P['fl_on'] > 0.01:
            ang = math.atan2(dy, dx)
            fr.g.arc(tx, ty, 2.4, 0, TAU)
            fillc(fr.g, cm(TOYLIGHT, P['fl_on']))
            cone(fr, tx + dx, ty + dy, ang, P['fl_len'], 2.0, P['fl_w'], TOYLIGHT, 0.32 * P['fl_on'])
            fr.blob(tx, ty, 1.8, FLAME_IN, 1.4 * P['fl_on'])
            fr.blob(tx, ty, 8, TOYLIGHT, 0.3 * P['fl_on'])
        out['fl'] = fr.dev(tx, ty)
    c.arc(hx_, hy_, 2.4, 0, TAU)
    fillc(c, cm(SKIN, sh))
    out['handF'] = fr.dev(hx_, hy_)
    fr.restore()
    fr.restore()
    _apply_lights(fr, lights)
    c.pop_group_to_source()
    c.paint()
    return out

def boat(fr, x, y, s, roll, lights=(), childP=None, t=0.0, shade=1.0, facing=1, with_child=True, tiller=0.0):
    """x,y = waterline centre. bow on the left (local -x)."""
    c = fr.c
    out = {}
    c.push_group()
    fr.save()
    fr.translate(x, y)
    fr.rotate(roll)
    fr.scale(s * facing, s)
    sh = shade
    # tiller (behind child arm)
    ta = math.radians(-30 + tiller)
    seg(c, 56, -12, 56 - 26 * math.cos(ta), -12 + 26 * math.sin(ta), 2.6, cm(WOOD_D, sh))
    if with_child:
        out = child(fr, 10, -9, 1.0, childP, facing=-1, t=t, shade=sh)
    # hull
    c.move_to(-70, -21)
    c.curve_to(-58, -12, -40, -10, 0, -10)
    c.line_to(55, -11)
    c.line_to(58, -14)
    c.line_to(55, 3)
    c.curve_to(30, 9, -20, 10, -40, 5)
    c.curve_to(-55, 0, -65, -10, -70, -21)
    c.close_path()
    pat = cairo.LinearGradient(0, -14, 0, 9)
    pat.add_color_stop_rgb(0, *cm(WOOD_L, sh))
    pat.add_color_stop_rgb(0.35, *cm(WOOD, sh))
    pat.add_color_stop_rgb(1, *cm(WOOD_D, sh))
    c.set_source(pat)
    c.fill()
    for off in (5, 10):
        c.move_to(-64 + off * 0.6, -18 + off)
        c.curve_to(-50, -9 + off * 0.9, -30, -8 + off * 0.8, 54, -9 + off * 0.9)
        strokec(c, cm(WOOD_D, sh), 0.9, 0.7)
    c.move_to(-70, -21)
    c.curve_to(-58, -12, -40, -10, 0, -10)
    c.line_to(57, -12)
    strokec(c, cm(WOOD_L, sh), 2.6)
    # oarlock + oar
    c.arc(-18, -11.5, 1.6, 0, TAU)
    fillc(c, cm(BRASS_D, sh))
    out['bow'] = fr.dev(-70, -21)
    fr.restore()
    _apply_lights(fr, lights)
    c.pop_group_to_source()
    c.paint()
    return out


# ------------------------------------------------------------------ lighthouse (exterior)
def island(fr, x, gy, h, col, rim=None, seed=21):
    c = fr.c
    rng = np.random.default_rng(seed)
    n = 26
    xs = np.linspace(x - 1.05 * h, x + 0.95 * h, n)
    prof = []
    for i, xx in enumerate(xs):
        u = (xx - x) / h
        top = gy + h * (0.02 + 0.20 * min(1, abs(u) ** 1.5)) - h * 0.03 * rng.random()
        if abs(u) < 0.22:
            top = gy + h * 0.01 * rng.random()
        prof.append((xx, top))
    base = gy + h * 0.34
    poly(c, [(xs[0], base)] + prof + [(xs[-1], base)])
    fillc(c, col)
    if rim is not None:
        rc, ra = rim
        c.move_to(*prof[0])
        for p in prof[1:n // 2 + 2]:
            c.line_to(*p)
        strokec(c, rc, 2.2, ra)
    return base

def lighthouse(fr, x, gy, h, t, lamp=0.0, dot=0.0, dawn=0.0, lit=0.0, figures=None, dot_col=AMBER):
    """x = tower centre, gy = tower base. returns lamp centre."""
    c = fr.c
    night_white = (0.28, 0.31, 0.40)
    day_white = (0.95, 0.86, 0.80)
    white = lc(night_white, day_white, dawn)
    white = lc(white, (0.75, 0.78, 0.92), lit * 0.6)
    shadow = cm(white, 0.55)
    redc = lc((0.24, 0.07, 0.08), (0.75, 0.24, 0.20), dawn)
    rockc = lc((0.010, 0.012, 0.018), (0.20, 0.13, 0.15), dawn)
    rockc = lc(rockc, (0.3, 0.32, 0.42), lit * 0.5)
    rim = ((1.0, 0.75, 0.55), 0.55) if dawn > 0.5 else ((0.30, 0.36, 0.48), 0.45 + 0.5 * lit)
    base = island(fr, x - 0.05 * h, gy, h, rockc, rim=rim)
    bw, tw = 0.17 * h, 0.115 * h
    gal = gy - 0.74 * h
    pat = cairo.LinearGradient(x - bw / 2, 0, x + bw / 2, 0)
    pat.add_color_stop_rgb(0, *lc(white, shadow, 0.15))
    pat.add_color_stop_rgb(0.35, *white)
    pat.add_color_stop_rgb(1, *shadow)
    poly(c, [(x - bw / 2, gy), (x - tw / 2, gal), (x + tw / 2, gal), (x + bw / 2, gy)])
    c.set_source(pat)
    c.fill()
    # red band
    b0, b1 = gy - 0.58 * h, gy - 0.66 * h
    def wat(yy):
        u = (gy - yy) / (gy - gal)
        return bw + (tw - bw) * u
    poly(c, [(x - wat(b0) / 2, b0), (x - wat(b1) / 2, b1), (x + wat(b1) / 2, b1), (x + wat(b0) / 2, b0)])
    fillc(c, redc)
    # door + windows
    rrect(c, x - 0.025 * h, gy - 0.07 * h, 0.05 * h, 0.07 * h, 0.02 * h)
    fillc(c, cm(shadow, 0.4))
    for wy in (gy - 0.30 * h, gy - 0.46 * h):
        rrect(c, x - 0.012 * h, wy, 0.024 * h, 0.04 * h, 0.01 * h)
        fillc(c, cm(shadow, 0.35))
    # gallery
    gw = tw * 1.75
    rrect(c, x - gw / 2, gal - 0.018 * h, gw, 0.022 * h, 2)
    fillc(c, cm(IRON, 1 + dawn * 1.5))
    rail_top = gal - 0.075 * h
    seg(c, x - gw / 2, rail_top, x + gw / 2, rail_top, max(1.2, 0.006 * h), cm(IRON, 1 + dawn * 1.5))
    for k in range(9):
        xx = x - gw / 2 + gw * k / 8
        seg(c, xx, gal - 0.018 * h, xx, rail_top, max(0.8, 0.003 * h), cm(IRON, 1 + dawn * 1.5))
    # lantern room
    lw, lh = tw * 0.95, 0.12 * h
    ly0 = gal - 0.018 * h - lh
    inner = lc((0.02, 0.025, 0.04), (0.55, 0.45, 0.42), dawn * 0.6)
    inner = lc(inner, (1.0, 0.85, 0.55), min(1.0, lamp))
    rrect(c, x - lw / 2, ly0, lw, lh, 2)
    fillc(c, inner)
    for k in range(4):
        xx = x - lw / 2 + lw * k / 3
        seg(c, xx, ly0, xx, ly0 + lh, max(1.0, 0.006 * h), cm(IRON, 1 + dawn * 1.5))
    lamp_c = (x, ly0 + lh * 0.5)
    if lamp > 0.01:
        fr.g.rectangle(x - lw / 2, ly0, lw, lh)
        fillc(fr.g, cm(AMBER_L, min(1.0, lamp)))
        fr.blob(lamp_c[0], lamp_c[1], 0.03 * h, AMBER_L, 2.2 * lamp)
    if dot > 0.01:
        fr.blob(x - lw * 0.18, ly0 + lh * 0.68, 0.012 * h, dot_col, 2.0 * dot)
        fr.blob(x - lw * 0.18, ly0 + lh * 0.68, 0.05 * h, dot_col, 0.3 * dot)
    # dome
    c.move_to(x - lw * 0.62, ly0)
    c.curve_to(x - lw * 0.55, ly0 - 0.07 * h, x + lw * 0.55, ly0 - 0.07 * h, x + lw * 0.62, ly0)
    c.close_path()
    fillc(c, lc((0.10, 0.04, 0.05), (0.45, 0.14, 0.14), dawn))
    c.arc(x, ly0 - 0.062 * h, 0.012 * h, 0, TAU)
    fillc(c, cm(IRON, 1 + dawn * 1.5))
    seg(c, x, ly0 - 0.07 * h, x, ly0 - 0.11 * h, max(0.8, 0.003 * h), cm(IRON, 1 + dawn * 1.5))
    if figures is not None:
        figures(fr, x, gal - 0.018 * h, h)
    return lamp_c, base

def lh_beam(fr, lx, ly, phi, I, L=1500, col=AMBER_L, w1=150, tilt=0.025):
    """rotating lighthouse beam seen from the side"""
    if I <= 0.005:
        return
    for k in (0, 1):
        p = phi + k * math.pi
        cx, sz = math.cos(p), math.sin(p)
        length = L * abs(cx) ** 0.85
        if length > 15:
            ang = (0.0 + tilt) if cx > 0 else (math.pi - tilt)
            cone(fr, lx, ly, ang, length, 5, w1 * (0.35 + 0.65 * abs(cx)), col, I * (0.5 + 0.5 * abs(cx)))
        if sz > 0:
            fr.blob(lx, ly, 18 + 90 * sz ** 6, col, I * 2.8 * sz ** 14)
    fr.blob(lx, ly, 6, (1, 0.95, 0.85), I * 2.0)
    fr.blob(lx, ly, 26, col, I * 0.5)


# ------------------------------------------------------------------ lamp room (interior)
def room(fr, t, dawn=0.0, flash=0.0, rain_a=1.0, x0=-300, x1=W + 900, sun=0.0, lens_light=0.0):
    """window wall, ledge, outside sky through panes"""
    c = fr.c
    top, wbot = -60, 560
    # outside sky through windows
    nightA, nightB = (0.04, 0.055, 0.10), (0.09, 0.11, 0.19)
    dawnA, dawnB = (0.55, 0.45, 0.66), (0.98, 0.72, 0.58)
    A = lc(nightA, dawnA, dawn)
    B = lc(nightB, dawnB, dawn)
    A = lc(A, (0.62, 0.66, 0.85), min(1, flash * 0.8))
    B = lc(B, (0.80, 0.84, 1.0), min(1, flash * 0.9))
    pat = cairo.LinearGradient(0, top, 0, wbot)
    pat.add_color_stop_rgb(0, *A)
    pat.add_color_stop_rgb(1, *B)
    c.set_source(pat)
    c.rectangle(x0, top, x1 - x0, wbot - top)
    c.fill()
    # distant storm clouds / dawn clouds
    if dawn < 1:
        clouds(fr, t, x0, x1, top + 40, wbot - 160, 26, 60, 160, lc((0.05, 0.06, 0.10), A, flash * 0.5),
               lc((0.12, 0.14, 0.22), B, flash), seed=31, lit=flash * 0.35, drift=30, alpha=1 - dawn)
    if dawn > 0:
        # sea line + sun glow
        seg(c, x0, wbot - 120, x1, wbot - 120, 2, (1.0, 0.85, 0.70), 0.5 * dawn)
        c.rectangle(x0, wbot - 120, x1 - x0, 120)
        fillc(c, lc((0.45, 0.40, 0.62), (0.98, 0.70, 0.55), 0.4), dawn)
        if sun > 0:
            fr.blob(240, wbot - 125, 40, (1.0, 0.85, 0.6), 1.6 * sun)
            fr.blob(240, wbot - 125, 160, (1.0, 0.65, 0.45), 0.35 * sun)
    if lens_light > 0:
        c.rectangle(x0, top, x1 - x0, wbot - top)
        fillc(c, AMBER, 0.06 * lens_light)
    # rain streaks on glass
    if rain_a > 0.01:
        rng = np.random.default_rng(5)
        n = 160
        rx = rng.random(n) * (x1 - x0) + x0
        sp = 60 + 220 * rng.random(n)
        ry = (rng.random(n) * (wbot - top) + sp * t) % (wbot - top) + top
        ln = 10 + 50 * rng.random(n)
        for i in range(n):
            c.move_to(rx[i], ry[i] - ln[i])
            c.line_to(rx[i] + 1.5, ry[i])
        strokec(c, lc((0.5, 0.58, 0.72), (1, 1, 1), flash * 0.5), 1.6, 0.22 * rain_a)
        for i in range(0, n, 2):
            c.arc(rx[i] + 1.5, ry[i], 2.2, 0, TAU)
            c.new_sub_path()
        fillc(c, (0.7, 0.78, 0.9), 0.25 * rain_a)
    # mullions
    frame = lc(IRON, (0.30, 0.22, 0.24), dawn * 0.6)
    for k in range(-2, 9):
        xx = 120 + k * 380
        c.rectangle(xx - 14, top, 28, wbot - top)
        fillc(c, frame)
        seg(c, xx - 10, top, xx - 10, wbot, 1.5, lc(IRON_L, (0.9, 0.7, 0.6), dawn * 0.5), 0.6)
    c.rectangle(x0, 180, x1 - x0, 18)
    fillc(c, frame)
    # wall below windows
    pat = cairo.LinearGradient(0, wbot, 0, H + 200)
    pat.add_color_stop_rgb(0, *lc((0.07, 0.075, 0.10), (0.34, 0.24, 0.24), dawn))
    pat.add_color_stop_rgb(1, *lc((0.025, 0.028, 0.04), (0.16, 0.11, 0.12), dawn))
    c.set_source(pat)
    c.rectangle(x0, wbot, x1 - x0, H + 400)
    c.fill()
    seg(c, x0, wbot + 2, x1, wbot + 2, 4, lc(IRON_L, (0.6, 0.45, 0.4), dawn), 0.8)
    for k in range(-2, 26):
        c.arc(k * 110 + 30, wbot + 22, 2.4, 0, TAU)
        c.new_sub_path()
    fillc(c, lc(IRON_L, (0.6, 0.45, 0.4), dawn), 0.7)
    # sun shafts
    if sun > 0:
        g = fr.g
        for k, (sx, w) in enumerate(((-120, 210), (260, 170), (640, 230))):
            pat = cairo.LinearGradient(sx, top, sx + 700, H + 100)
            pat.add_color_stop_rgba(0, 1.0, 0.78, 0.55, 0.10 * sun)
            pat.add_color_stop_rgba(1, 1.0, 0.78, 0.55, 0.0)
            g.set_source(pat)
            poly(g, [(sx, top), (sx + w, top), (sx + w + 900, H + 200), (sx + 900, H + 200)])
            g.fill()
        rng = np.random.default_rng(77)
        n = 90
        mx = (rng.random(n) * 1600 - 100 + 8 * t) % 1700 - 100
        my = (rng.random(n) * 700 + 5 * np.sin(t * 0.6 + rng.random(n) * 6)) % 760
        for i in range(n):
            g.arc(mx[i], my[i], 1.2 + 1.4 * rng.random(), 0, TAU)
            g.new_sub_path()
        fillc(g, (1.0, 0.85, 0.65), 0.25 * sun)

def ledge(fr, y, x0, x1, dawn=0.0, ladder_x=None, ladder_bot=1100, ladder_w=70):
    c = fr.c
    col = lc((0.09, 0.10, 0.13), (0.30, 0.22, 0.22), dawn)
    c.rectangle(x0, y, x1 - x0, 22)
    fillc(c, col)
    seg(c, x0, y + 1, x1, y + 1, 2.4, lc(IRON_L, (0.85, 0.65, 0.55), dawn), 0.9)
    c.rectangle(x0, y + 22, x1 - x0, 900)
    fillc(c, cm(col, 0.55))
    for k in range(int(x0 // 60), int(x1 // 60) + 1):
        seg(c, k * 60, y + 22, k * 60, y + 160, 1.2, cm(col, 1.2), 0.6)
    if ladder_x is not None:
        lw = ladder_w
        for sx in (ladder_x - lw / 2, ladder_x + lw / 2):
            seg(c, sx, y - 40, sx, ladder_bot, 6, lc(IRON_L, (0.6, 0.45, 0.4), dawn))
        for ry in np.arange(y - 10, ladder_bot, lw * 0.66):
            seg(c, ladder_x - lw / 2, ry, ladder_x + lw / 2, ry, 4.5, lc(IRON_L, (0.6, 0.45, 0.4), dawn))

LENS = dict(cx=1360, top=20, w=560, h=560)

def _barrel(ctx, cx, top, w, h):
    bot = top + h
    ctx.move_to(cx - w * 0.36, top)
    ctx.curve_to(cx - w * 0.50, top + h * 0.16, cx - w * 0.52, top + h * 0.34, cx - w * 0.505, top + h * 0.5)
    ctx.curve_to(cx - w * 0.52, top + h * 0.66, cx - w * 0.50, top + h * 0.84, cx - w * 0.37, bot)
    ctx.line_to(cx + w * 0.37, bot)
    ctx.curve_to(cx + w * 0.50, top + h * 0.84, cx + w * 0.52, top + h * 0.66, cx + w * 0.505, top + h * 0.5)
    ctx.curve_to(cx + w * 0.52, top + h * 0.34, cx + w * 0.50, top + h * 0.16, cx + w * 0.36, top)
    ctx.close_path()

def _hw(w, u):
    return w * (0.365 + 0.14 * math.sin(math.pi * u))

def lens(fr, t, on=0.0, bulb=0.0, broken=False, orb=0.0, sweep=None, dawn=0.0, glint=0.0, L=LENS, ring_on=None):
    """Fresnel lens barrel. on: 0..1, sweep: phase of rotation highlight"""
    c = fr.c
    cx, top, w, h = L['cx'], L['top'], L['w'], L['h']
    bot = top + h
    brass_d = lc(BRASS_D, BRASS, 0.15 + 0.4 * dawn)
    brass = lc(BRASS_D, BRASS, 0.6 + 0.4 * dawn)
    # pedestal
    poly(c, [(cx - w * 0.2, bot), (cx + w * 0.2, bot), (cx + w * 0.28, bot + 300), (cx - w * 0.28, bot + 300)])
    fillc(c, lc((0.06, 0.065, 0.085), (0.25, 0.18, 0.18), dawn))
    # glass body
    glass_a = lc((0.06, 0.10, 0.115), (0.42, 0.34, 0.34), dawn * 0.75)
    glass_b = lc((0.015, 0.03, 0.04), (0.20, 0.15, 0.17), dawn * 0.75)
    _barrel(c, cx, top, w, h)
    pat = cairo.LinearGradient(cx - w / 2, 0, cx + w / 2, 0)
    pat.add_color_stop_rgb(0, *glass_b)
    pat.add_color_stop_rgb(0.32, *glass_a)
    pat.add_color_stop_rgb(0.5, *lc(glass_a, glass_b, 0.4))
    pat.add_color_stop_rgb(1, *glass_b)
    c.set_source(pat)
    c.fill()
    hl = lc((0.30, 0.42, 0.45), (1.0, 0.82, 0.66), dawn * 0.75)
    groove = lc((0.01, 0.02, 0.025), (0.15, 0.10, 0.12), dawn * 0.75)
    # prism rings, upper and lower tiers
    nrib = 10
    for tier, (u0, u1) in enumerate(((0.035, 0.33), (0.67, 0.965))):
        for i in range(nrib):
            u = u0 + (u1 - u0) * i / (nrib - 1)
            yy = top + h * u
            hw = _hw(w, u) * 0.985
            sag = h * 0.018 * (1 if tier == 0 else -1)
            for ctx_, col_, wd, a_, dy_ in ((c, groove, 4.0, 0.8, 3), (c, hl, 2.2, 0.55, 0)):
                ctx_.move_to(cx - hw, yy + dy_)
                ctx_.curve_to(cx - hw * 0.4, yy + sag + dy_, cx + hw * 0.4, yy + sag + dy_, cx + hw, yy + dy_)
                strokec(ctx_, col_, wd, a_)
            if on > 0.01:
                k = (nrib - 1 - i) if tier == 0 else i
                lvl = on if ring_on is None else ring_on[min(len(ring_on) - 1, 5 + k // 2)]
                fr.g.move_to(cx - hw, yy)
                fr.g.curve_to(cx - hw * 0.4, yy + sag, cx + hw * 0.4, yy + sag, cx + hw, yy)
                strokec(fr.g, AMBER_L, 3.2, min(1.0, 0.5 * lvl))
    # central bullseye
    by = top + h * 0.5
    R = w * 0.215
    c.arc(cx, by, R * 1.08, 0, TAU)
    fillc(c, lc(glass_b, glass_a, 0.5))
    for k in range(6, 0, -1):
        r = R * k / 6
        c.arc(cx, by, r, 0, TAU)
        strokec(c, groove, 4.0, 0.7)
        c.arc(cx, by, r - 2, 0, TAU)
        strokec(c, hl, 1.8, 0.35 + 0.07 * k)
        if on > 0.01:
            lvl = on if ring_on is None else ring_on[min(len(ring_on) - 1, k - 1)]
            fr.g.arc(cx, by, r, 0, TAU)
            strokec(fr.g, AMBER_L, 3.0, min(1.0, 0.6 * lvl))
    # cylinder highlight
    c.save()
    _barrel(c, cx, top, w, h)
    c.clip()
    pat = cairo.LinearGradient(cx - w * 0.32, 0, cx - w * 0.14, 0)
    pat.add_color_stop_rgba(0, 1, 1, 1, 0)
    pat.add_color_stop_rgba(0.5, 1, 1, 1, 0.06 + 0.06 * dawn)
    pat.add_color_stop_rgba(1, 1, 1, 1, 0)
    c.set_source(pat)
    c.paint()
    c.restore()
    # brass bands + thin posts
    for u in (0.345, 0.655):
        yy = top + h * u
        hw = _hw(w, u)
        sag = h * 0.01 * (1 if u < 0.5 else -1)
        c.move_to(cx - hw, yy)
        c.curve_to(cx - hw * 0.4, yy + sag, cx + hw * 0.4, yy + sag, cx + hw, yy)
        strokec(c, brass_d, 9)
        c.move_to(cx - hw, yy - 2)
        c.curve_to(cx - hw * 0.4, yy + sag - 2, cx + hw * 0.4, yy + sag - 2, cx + hw, yy - 2)
        strokec(c, brass, 2, 0.6)
    for fx in (-0.27, 0.27):
        seg(c, cx + w * fx, top + h * 0.03, cx + w * fx * 1.1, top + h * 0.33, 3, brass_d, 0.8)
        seg(c, cx + w * fx * 1.1, top + h * 0.67, cx + w * fx, top + h * 0.97, 3, brass_d, 0.8)
    _barrel(c, cx, top, w, h)
    strokec(c, brass_d, 6)
    # dome cap and base ring
    c.move_to(cx - w * 0.37, top + 2)
    c.curve_to(cx - w * 0.30, top - h * 0.075, cx + w * 0.30, top - h * 0.075, cx + w * 0.37, top + 2)
    c.close_path()
    fillc(c, brass_d)
    c.arc(cx, top - h * 0.062, w * 0.03, 0, TAU)
    fillc(c, brass)
    rrect(c, cx - w * 0.40, bot - 4, w * 0.80, h * 0.045, 4)
    fillc(c, brass_d)
    seg(c, cx - w * 0.39, bot - 2, cx + w * 0.39, bot - 2, 2, brass, 0.6)
    # bulb or orb at the centre
    if bulb != 0 or broken:
        c.arc(cx, by + 6, 9, 0, TAU)
        fillc(c, (0.25, 0.22, 0.18))
        if not broken:
            c.arc(cx, by - 8, 16, 0, TAU)
            fillc(c, lc((0.35, 0.36, 0.38), (1.0, 0.95, 0.8), max(0, bulb)), 0.85)
            seg(c, cx - 5, by - 8, cx + 5, by - 8, 1.5, (0.5, 0.3, 0.1))
            if bulb > 0:
                fr.blob(cx, by - 8, 10, FLAME_IN, 2.4 * bulb)
                fr.blob(cx, by - 8, 70, AMBER, 0.6 * bulb)
        else:
            poly(c, [(cx - 8, by - 2), (cx - 5, by - 12), (cx - 1, by - 5), (cx + 3, by - 14), (cx + 8, by - 2)])
            fillc(c, (0.45, 0.48, 0.52), 0.6)
    c.arc(cx, by, 22, 0, TAU)
    strokec(c, brass_d, 5)
    if orb > 0.01:
        c.arc(cx, by, 15, 0, TAU)
        fillc(c, lc(AMBER, FLAME_IN, 0.6))
        fr.blob(cx, by, 9, FLAME_IN, 3.0 * orb)
        fr.blob(cx, by, 40, AMBER, 0.9 * orb)
    if on > 0.01:
        fr.blob(cx, by, 120, AMBER, 0.55 * on)
        fr.blob(cx, by, 30, FLAME_IN, 1.8 * on)
    if sweep is not None and on > 0.01:
        g = fr.g
        g.save()
        _barrel(g, cx, top, w, h)
        g.clip()
        bx = cx + w * 0.5 * math.sin(sweep)
        pat = cairo.LinearGradient(bx - 90, 0, bx + 90, 0)
        pat.add_color_stop_rgba(0, 1, 0.8, 0.5, 0)
        pat.add_color_stop_rgba(0.5, 1, 0.85, 0.6, min(1.0, 0.8 * on * abs(math.cos(sweep))))
        pat.add_color_stop_rgba(1, 1, 0.8, 0.5, 0)
        g.set_source(pat)
        g.rectangle(cx - w, top, 2 * w, h)
        g.fill()
        g.restore()
    return (cx, by)


# ------------------------------------------------------------------ post
_rg = np.random.default_rng(2026)
GRAIN = [(_rg.random((H, W)).astype(F32) + _rg.random((H, W)).astype(F32) - 1.0) for _ in range(5)]
_yy, _xx = np.mgrid[0:H, 0:W].astype(F32)
_VR = (((_xx - W / 2) / (W / 2)) ** 2 * 0.65 + ((_yy - H / 2) / (H / 2)) ** 2 * 0.9)

def add_blob(L, x, y, sig, col, amp):
    R = int(sig * 4) + 2
    x0 = int(round(x)); y0 = int(round(y))
    xs0, xs1 = max(x0 - R, 0), min(x0 + R + 1, W)
    ys0, ys1 = max(y0 - R, 0), min(y0 + R + 1, H)
    if xs0 >= xs1 or ys0 >= ys1:
        return
    xx = np.arange(xs0, xs1, dtype=F32) - F32(x)
    yy = np.arange(ys0, ys1, dtype=F32) - F32(y)
    d2 = (yy[:, None] ** 2 + xx[None, :] ** 2) / F32(sig * sig)
    gm = np.maximum(np.exp(-0.5 * d2) - F32(math.exp(-8)), 0)
    L[ys0:ys1, xs0:xs1] += gm[..., None] * (np.asarray(col, F32) * F32(amp))

def add_streak(L, x, y, length, thick, col, amp, vertical=False):
    R = int(length * 5) + 2
    T = int(thick * 4) + 2
    x0 = int(round(x)); y0 = int(round(y))
    if vertical:
        xs0, xs1, ys0, ys1 = max(x0 - T, 0), min(x0 + T + 1, W), max(y0 - R, 0), min(y0 + R + 1, H)
    else:
        xs0, xs1, ys0, ys1 = max(x0 - R, 0), min(x0 + R + 1, W), max(y0 - T, 0), min(y0 + T + 1, H)
    if xs0 >= xs1 or ys0 >= ys1:
        return
    xx = np.arange(xs0, xs1, dtype=F32) - F32(x)
    yy = np.arange(ys0, ys1, dtype=F32) - F32(y)
    if vertical:
        a = np.exp(-np.abs(yy) / F32(length))[:, None] * np.exp(-(xx / F32(thick)) ** 2)[None, :]
    else:
        a = np.exp(-(yy / F32(thick)) ** 2)[:, None] * np.exp(-np.abs(xx) / F32(length))[None, :]
    L[ys0:ys1, xs0:xs1] += a[..., None] * (np.asarray(col, F32) * F32(amp))

def to_np(surf):
    surf.flush()
    a = np.ndarray((H, W, 4), np.uint8, surf.get_data())
    return a[..., [2, 1, 0]].astype(F32) * F32(1 / 255.0)

def develop(fr):
    """scene + emission -> graded float image (H,W,3)"""
    Sc = to_np(fr.s)
    E = to_np(fr.e) * F32(fr.egain)
    for b in fr.blobs:
        add_blob(E, *b)
    for st in fr.streaks:
        add_streak(E, *st)
    D = cv2.resize(E, (W // 4, H // 4), interpolation=cv2.INTER_AREA)
    B = (cv2.GaussianBlur(D, (0, 0), 2.0) * 0.45 + cv2.GaussianBlur(D, (0, 0), 7) * 0.55
         + cv2.GaussianBlur(D, (0, 0), 22) * 0.65)
    img = Sc + E + cv2.resize(B, (W, H), interpolation=cv2.INTER_LINEAR) * F32(fr.bloom)
    if fr.flash > 0:
        img += F32(fr.flash) * np.array(fr.flash_col, F32)
    img = np.array(fr.lift, F32) + img * np.array(fr.gain, F32)
    if fr.sat != 1.0:
        lum = img.mean(axis=2, keepdims=True)
        img = lum + (img - lum) * F32(fr.sat)
    # soft shoulder
    hi = img > 0.82
    img = np.where(hi, 0.82 + 0.18 * (1 - np.exp(-(img - 0.82) / 0.18)), img).astype(F32)
    for fn in fr.post:
        img = fn(img)
    img *= (1 - F32(fr.vig) * np.clip(_VR, 0, 1.6) ** 1.25)[..., None]
    return np.clip(img, 0, 1)

def finalize(img, fi, fade=1.0):
    img = img * F32(fade)
    img = img + GRAIN[fi % len(GRAIN)][..., None] * F32(0.012)
    out = np.zeros((OH, W, 3), np.uint8)
    out[BAR:BAR + H] = np.clip(img * 255 + 0.5, 0, 255).astype(np.uint8)
    return out
