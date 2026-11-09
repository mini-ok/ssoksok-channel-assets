# -*- coding: utf-8 -*-
"""홀씨 -- group D: C15 (bloom), C16 (to seed head), C17 (the release), C18 (crane up, title)."""
from shots_c import *

DAWN_GRADE = dict(lift=(0.04, 0.032, 0.03), gain=(1.03, 0.99, 0.93), sat=0.95, contrast=0.94)

def dawn_bg(c, rng):
    vgrad(c, 0, 0, W, H, [(0, (0.66, 0.70, 0.80)), (0.45, (0.96, 0.84, 0.70)), (0.62, (0.72, 0.64, 0.58)),
                          (1, (0.40, 0.37, 0.36))])
    for _ in range(36):
        x, y = rng.uniform(0, W), rng.uniform(H * 0.55, H)
        radial(c, x, y, rng.uniform(60, 200), lc((0.36, 0.34, 0.33), (0.52, 0.48, 0.44), rng.random()), 0.7)
    for _ in range(22):
        x, y = rng.uniform(0, W), rng.uniform(H * 0.1, H * 0.6)
        r = rng.uniform(16, 50)
        c.arc(x, y, r, 0, TAU)
        fillc(c, (1, 0.92, 0.75), rng.uniform(0.15, 0.4))
    for _ in range(14):
        x = rng.uniform(0, W); y = rng.uniform(H * 0.55, H * 0.9)
        line(c, x, y, x + rng.uniform(-6, 6), y - rng.uniform(80, 260), rng.uniform(8, 16), (0.24, 0.22, 0.22), 0.9)
    for _ in range(9):
        x = rng.uniform(0, W); y = rng.uniform(H * 0.62, H * 0.95)
        c.arc(x, y, rng.uniform(14, 30), 0, TAU)
        fillc(c, (0.45, 0.60, 0.32), 0.85)

FC = (980, 470)        # flower centre on screen

def flower_head(c, x, y, R, open_, t, close=0.0):
    """dandelion flower seen 3/4 from the front. open_: 0 bud -> 1 open. close: 0..1 folds petals up"""
    bud_h = R * 1.1
    # green bracts cup
    c.save(); c.translate(x, y + R * 0.18); c.scale(1, 0.75)
    c.arc(0, 0, R * 0.30, 0, TAU); c.restore()
    fillc(c, (0.36, 0.52, 0.27))
    for k in range(9):
        a = math.pi * (0.12 + 0.76 * k / 8)
        bx, by = x + math.cos(a) * R * 0.26, y + R * 0.22 + math.sin(a) * R * 0.08
        dx = math.cos(a)
        c.move_to(bx, by)
        c.curve_to(bx + dx * R * 0.18, by + R * 0.05, bx + dx * R * 0.30, by + R * 0.22,
                   bx + dx * R * 0.24, by + R * (0.40 + 0.05 * (k % 2)))
        strokec(c, (0.24, 0.36, 0.19), R * 0.055, 0.6)
        c.move_to(bx, by)
        c.curve_to(bx + dx * R * 0.18, by + R * 0.05, bx + dx * R * 0.30, by + R * 0.22,
                   bx + dx * R * 0.24, by + R * (0.40 + 0.05 * (k % 2)))
        strokec(c, lc((0.36, 0.52, 0.27), (0.55, 0.68, 0.36), k % 2 * 0.6), R * 0.035)
    # florets: rings from outer to inner
    rings = 7
    for ring in range(rings):
        u = ring / (rings - 1)
        n = int(34 - 22 * u)
        L = R * (1.0 - 0.55 * u) * (0.35 + 0.65 * open_)
        lift = (1 - open_) * 1.2 + close * 1.3
        for k in range(n):
            a = TAU * (k + 0.5 * ring) / n
            # petal direction: in the image plane, ellipse for 3/4 view, then folded up by lift
            dx = math.cos(a)
            dy = math.sin(a) * 0.55
            fold = min(1.0, lift * (1 - 0.4 * u))
            ex = x + dx * L * (1 - fold * 0.85)
            ey = y + dy * L * (1 - fold * 0.85) - L * fold * 0.9
            col = lc((0.98, 0.72, 0.10), (1.0, 0.90, 0.36), u * 0.6 + 0.3 * (0.5 + 0.5 * dy))
            if dy < 0:
                col = cm(col, 0.9)
            w = R * (0.11 - 0.04 * u)
            c.move_to(x + dx * L * 0.12, y + dy * L * 0.12)
            c.line_to(ex, ey)
            strokec(c, (0.55, 0.36, 0.05), w * 1.35, 0.55)
            c.move_to(x + dx * L * 0.12, y + dy * L * 0.12)
            c.line_to(ex, ey)
            strokec(c, col, w)
            # notched tip
            c.arc(ex, ey, w * 0.45, 0, TAU)
            fillc(c, cm(col, 1.05))
    c.save(); c.translate(x, y); c.scale(1, 0.55)
    c.arc(0, 0, R * 0.22 * (0.4 + 0.6 * open_), 0, TAU); c.restore()
    fillc(c, (0.93, 0.62, 0.08))

def puffball(c, x, y, R, t, gone=None, wind=0.0, rng_seed=7, n=150):
    """seed head: seeds on a sphere. gone(i, pos) -> offset dict or None (still attached)"""
    rng = np.random.default_rng(rng_seed)
    pts = []
    ga = math.pi * (3 - math.sqrt(5))
    for i in range(n):
        zf = 1 - 2 * (i + 0.5) / n
        r = math.sqrt(1 - zf * zf)
        th = ga * i
        pts.append((math.cos(th) * r, zf, math.sin(th) * r, i))
    pts.sort(key=lambda p: p[2])  # back to front
    flying = []
    # receptacle
    receptacle(c, x, y + R * 0.02, R * 0.12, np.random.default_rng(rng_seed))
    for (px, py, pz, i) in pts:
        if gone is not None:
            g = gone(i, px, py, pz)
            if g is not None:
                flying.append(g)
                continue
        bx, by = x + px * R * 0.12, y + py * R * 0.12
        ex, ey = x + px * R * 0.62, y + py * R * 0.62
        depth = 0.55 + 0.45 * (pz + 1) / 2
        line(c, bx, by, ex, ey, max(0.6, R * 0.006), lc((0.55, 0.50, 0.40), (0.85, 0.82, 0.72), depth), 0.8 * depth)
        # pappus: small fan perpendicular-ish, drawn as a starburst
        pr = R * 0.36
        nf = 12
        for k in range(nf):
            a = TAU * k / nf + i
            fx = ex + math.cos(a) * pr * (0.5 + 0.5 * abs(px)) + px * pr * 0.6
            fy = ey + math.sin(a) * pr * (0.5 + 0.5 * abs(py)) + py * pr * 0.6
            c.move_to(ex, ey)
            c.line_to(fx, fy)
        strokec(c, lc((0.78, 0.78, 0.74), (1, 0.98, 0.94), depth), max(0.6, R * 0.004), 0.55 + 0.35 * depth)
    return flying

# ================================================================== C14 ending + C15  the bloom
def c15(t, fi):
    cp = Comp(); grade(cp, DAWN_GRADE)
    bg = Static('c15_bg', W, H, dawn_bg)
    cp.add(bg.view(W / 2, H / 2), blur=22)
    d = dyn(); c = d.c
    sway = 5 * math.sin(t * 1.1)
    # stem and two leaves
    stem(c, stem_path((FC[0] + 30, H + 40), (FC[0] + sway, FC[1] + 60), -30), 22)
    jag_leaf(c, FC[0] + 40, H + 30, -2.5, 620, 95, col=(0.42, 0.58, 0.30), curl=0.2)
    jag_leaf(c, FC[0] + 40, H + 30, -0.55, 560, 85, col=(0.38, 0.54, 0.28), curl=0.2)
    o = ease(lin(76.0, 78.6, t))
    flower_head(c, FC[0] + sway, FC[1], 260, o, t)
    # the ladybug lands at 78.6
    a = (t - 78.0) / 0.7
    if a > 0:
        land = ease(min(1, a))
        lx = lerp(FC[0] + 700, FC[0] + 140 + sway, land)
        ly = lerp(FC[1] - 420, FC[1] - 30, land) - 60 * math.sin(math.pi * min(1, a))
        ladybug(c, lx, ly, 34, ang=lerp(-1.0, -0.3, land), t=t, wings=1.0 - sm(78.55, 78.9, t), legs=sm(78.6, 79.0, t))
    cp.add(d.rgba(), tx='d', tamp=0.04)
    cp.glow(FC[0] + sway, FC[1], 420, (1.0, 0.86, 0.45), 0.35 * o)
    cp.glow(1650, 60, 700, (1.0, 0.88, 0.65), 0.5)
    return cp

# ================================================================== C16  from flower to seed head (same framing)
def c16(t, fi):
    cp = Comp(); grade(cp, DAWN_GRADE)
    bg = Static('c15_bg', W, H, dawn_bg)
    cp.add(bg.view(W / 2, H / 2), blur=22)
    d = dyn(); c = d.c
    sway = 5 * math.sin(t * 1.1)
    stem(c, stem_path((FC[0] + 30, H + 40), (FC[0] + sway, FC[1] + 60), -30), 22)
    jag_leaf(c, FC[0] + 40, H + 30, -2.5, 620, 95, col=(0.42, 0.58, 0.30), curl=0.2)
    jag_leaf(c, FC[0] + 40, H + 30, -0.55, 560, 85, col=(0.38, 0.54, 0.28), curl=0.2)
    close = ease(lin(80.0, 81.3, t))
    puff = ease(lin(81.5, 82.9, t))
    if puff < 0.02:
        flower_head(c, FC[0] + sway, FC[1], 260, 1.0, t, close=close)
    else:
        # closed bud splits open into the sphere
        c.push_group()
        puffball(c, FC[0] + sway, FC[1] - 60 * puff, 330 * (0.35 + 0.65 * puff), t)
        c.pop_group_to_source()
        c.paint_with_alpha(puff)
        if puff < 0.6:
            c.push_group()
            flower_head(c, FC[0] + sway, FC[1], 260, 1.0, t, close=1.0)
            c.pop_group_to_source()
            c.paint_with_alpha(1 - puff / 0.6)
    cp.add(d.rgba(), tx='d', tamp=0.04)
    cp.glow(FC[0] + sway, FC[1] - 60 * puff, 460, (1.0, 0.92, 0.75), 0.35 * puff)
    cp.glow(1650, 60, 700, (1.0, 0.88, 0.65), 0.5)
    return cp

# ================================================================== C17  the wind returns: release
PB = (900, 560)
PB_R = 470

def release_time(i, px, py, pz):
    # upwind side (left, x<0) leaves first; jitter
    j = ((i * 0.6180339) % 1.0)
    return 83.55 + (px + 1) * 0.9 + j * 0.5

def c17(t, fi):
    cp = Comp(); grade(cp, DAWN_GRADE)
    bg = Static('c15_bg', W, H, dawn_bg)
    cp.add(bg.view(W / 2 - 80, H / 2 - 100, 1.25), blur=28)
    d = dyn(); c = d.c
    gust = sm(83.4, 83.9, t)
    sway = 6 * math.sin(t * 1.1) + 30 * gust
    stem(c, stem_path((PB[0] + 60, H + 60), (PB[0] + sway, PB[1] + 60), -40 + sway * 0.5), 30)
    def gone(i, px, py, pz):
        tr = release_time(i, px, py, pz)
        if t < tr:
            return None
        return (i, px, py, pz, t - tr)
    flying = puffball(c, PB[0] + sway, PB[1], PB_R, t, gone=gone, n=170)
    cp.add(d.rgba(), tx='d', tamp=0.03)
    # flying seeds: drift right and up, rotate, glint
    d = dyn(); c = d.c
    for (i, px, py, pz, a) in flying:
        r_ = np.random.default_rng(i)
        sx0 = PB[0] + sway + px * PB_R * 0.62
        sy0 = PB[1] + py * PB_R * 0.62
        vx = 520 + r_.uniform(0, 380)
        vy = -160 - r_.uniform(0, 260)
        x = sx0 + vx * a + 40 * math.sin(a * 2 + i)
        y = sy0 + vy * a + 30 * math.sin(a * 1.4 + i * 2)
        s = 70 * (0.7 + 0.5 * (pz + 1) / 2)
        if x > W + 200 or y < -200:
            continue
        seed(c, x, y, s, rot=0.35 + 0.25 * math.sin(a * 2.5 + i), t=t,
             light=(1, 0.95, 0.82), rim=1.3, nfil=18)
    cp.add(d.rgba())
    # motes
    if gust > 0:
        d = dyn(); c = d.c
        rng = np.random.default_rng(171)
        for k in range(50):
            x = (rng.uniform(-300, W) + 700 * (t - 83.4)) % (W + 300) - 150
            y = rng.uniform(0, H) - 120 * (t - 83.4)
            c.arc(x, y, rng.uniform(1.5, 3.5), 0, TAU)
            fillc(c, (1, 0.95, 0.82), 0.6 * gust)
        cp.add(d.rgba(), blur=1.5)
    cp.glow(1600, 80, 800, (1.0, 0.88, 0.65), 0.55)
    return cp

# ================================================================== C18  crane up: the plain is greening, seeds rise
C18W, C18H = 2400, 2600
C18_HOR = 1250

def c18_sky(c, rng):
    vgrad(c, 0, 0, C18W, C18_HOR + 20, [(0, (0.46, 0.58, 0.74)), (0.45, (0.84, 0.80, 0.80)),
                                         (0.82, (1.0, 0.86, 0.64)), (1, (1.0, 0.80, 0.56))])
    radial(c, 1500, C18_HOR - 30, 700, (1.0, 0.90, 0.68), 0.6)
    c.arc(1500, C18_HOR - 20, 40, 0, TAU)
    fillc(c, (1, 0.96, 0.86))

def c18_clouds(w, h, rng):
    groups = []
    for (x, y, cw, ch) in ((400, 500, 700, 110), (1300, 420, 900, 130), (2100, 560, 700, 100), (800, 860, 700, 70),
                           (1800, 940, 640, 60), (300, 1080, 500, 40), (1400, 1120, 520, 36)):
        groups.append((cloud_circles(rng, x, y, cw, ch), rect_clip(x - cw, x + cw, y, ch * 0.04, x)))
    hh, m = domes_union(w, h, groups)
    arr = celpaint_h(hh, m, [(0.74, 0.62, 0.70), (0.96, 0.78, 0.66), (1.0, 0.88, 0.72), (1.0, 0.96, 0.86)],
                     light=(0.5, -0.86), step=9, gain=5.0, cuts=(0.40, 0.53, 0.66), seed=181)
    far = np.clip((np.arange(h, dtype=F32)[:, None] - 500) / 650, 0, 1)
    arr[..., :3] = arr[..., :3] * (1 - 0.45 * far[..., None]) + np.array((1.0, 0.84, 0.64), F32) * arr[..., 3:4] * (
        0.45 * far[..., None])
    return arr

def c18_plain(w, h, rng):
    gh = h - C18_HOR
    tall = gh * 4
    n1 = fbm(w, tall, seed=41, octaves=6, base=5)
    ys = np.arange(gh, dtype=F32)
    v = (ys / gh) ** 1.8 * (tall - 1)
    mapy = np.tile(v[:, None], (1, w)).astype(F32)
    mapx = np.tile(np.arange(w, dtype=F32)[None, :], (gh, 1))
    p1 = cv2.remap(n1, mapx, mapy, cv2.INTER_LINEAR)
    m = np.zeros((h, w), F32); m[C18_HOR:] = 1
    ex = np.zeros((h, w), F32)
    yy = np.arange(h, dtype=F32)[:, None]
    far = np.clip(1 - (yy - C18_HOR) / 300, 0, 1)
    ex[C18_HOR:] = p1 * 0.08 - (ys[:, None] / gh) * 0.12
    pal = [(0.36, 0.32, 0.32), (0.52, 0.46, 0.43), (0.68, 0.60, 0.54), (0.86, 0.74, 0.62)]
    arr = celpaint_h(m * 0.5, m, pal, light=(0.4, -0.9), step=1, gain=0.0, seed=182, blotch=0.0, namp=0.0,
                     extra=ex * 1.6 + far * 0.25, cuts=(0.38, 0.50, 0.63), soft=0.05)
    cv = Canvas(w, h); c = cv.c
    # charred stands, sparse
    for _ in range(40):
        gx = rng.uniform(0, w); gy = C18_HOR + 6 + (rng.random() ** 1.3) * (gh - 60)
        k = 0.12 + 1.6 * ((gy - C18_HOR) / gh) ** 1.3
        for j in range(rng.integers(4, 18)):
            x = gx + rng.normal(0, 60 * k); y = gy + rng.normal(0, 10 * k)
            ht = rng.uniform(30, 90) * k
            line(c, x, y, x + rng.uniform(-3, 3) * k, y - ht, max(0.8, 2.8 * k), (0.20, 0.17, 0.17), 0.9)
    # green rosettes and yellow flowers scattered: the seeds of earlier years
    for _ in range(420):
        y = C18_HOR + 4 + (rng.random() ** 1.15) * gh
        k = 0.1 + 1.6 * ((y - C18_HOR) / gh) ** 1.2
        x = rng.uniform(0, w)
        for j in range(5):
            a = -math.pi * rng.uniform(0.05, 0.95)
            line(c, x, y, x + math.cos(a) * 22 * k, y + math.sin(a) * 7 * k, max(1, 7 * k),
                 lc((0.36, 0.54, 0.28), (0.56, 0.70, 0.36), rng.random()), 0.95)
        if rng.random() < 0.55:
            hy = y - 26 * k
            line(c, x, y, x + 2 * k, hy, max(0.8, 2 * k), (0.40, 0.55, 0.30), 0.95)
            c.arc(x + 2 * k, hy, max(1.2, 6 * k), 0, TAU)
            fillc(c, YEL if rng.random() < 0.7 else (1, 0.98, 0.94))
    arr = over(arr, cv.rgba())
    hz = np.exp(-((yy - C18_HOR) / 150) ** 2) * 0.55
    arr[..., :3] = arr[..., :3] * (1 - hz[..., None]) + np.array((0.98, 0.84, 0.66), F32) * hz[..., None] * arr[..., 3:4]
    return arr

def c18(t, fi):
    cp = Comp(); grade(cp, DAWN_GRADE)
    u = ease(lin(86.0, 89.4, t))
    cx, cy = 1250, lerp(2050, 1080, u)
    z = lerp(1.25, 1.0, u)
    sky = Static('c18_sky', C18W, C18H, c18_sky)
    cl = StaticArr('c18_cl', C18W, C18H, c18_clouds)
    pl = StaticArr('c18_pl', C18W, C18H, c18_plain)
    cp.add(sky.view(cx, cy, z))
    cp.add(cl.view(cx - 6 * (t - 86), cy, z))
    cp.add(pl.view(cx, cy, z))
    # the parent plant, lower-left, now a bare receptacle
    d = dyn(); c = d.c
    c.translate(W / 2 - cx * z, H / 2 - cy * z); c.scale(z, z)
    px, py = 900, 2350
    stem(c, stem_path((px + 30, py + 300), (px, py), -30), 16)
    receptacle(c, px, py, 30, np.random.default_rng(5))
    for k in range(3):
        jag_leaf(c, px + 30, py + 300, [-2.6, -0.5, -2.0][k], 380, 60, col=(0.40, 0.56, 0.30), curl=0.2)
    cp.add(d.rgba())
    # the drifting seeds: a river of them rising toward the sun (looping phases)
    d = dyn(); c = d.c
    rng = np.random.default_rng(1818)
    n = 260
    P0, P1, P2 = (900, 2330), (1000, 1500), (1700, 700)
    for i in range(n):
        ph = (rng.uniform(0, 1) + (t - 86.0) * rng.uniform(0.10, 0.18)) % 1.0
        q = ph
        wx = (1 - q) ** 2 * P0[0] + 2 * (1 - q) * q * P1[0] + q * q * P2[0]
        wy = (1 - q) ** 2 * P0[1] + 2 * (1 - q) * q * P1[1] + q * q * P2[1]
        spread = 40 + 520 * q
        wx += rng.normal(0, 1) * spread + 40 * math.sin(t * 0.9 + i)
        wy += rng.normal(0, 1) * spread * 0.45 + 25 * math.sin(t * 1.3 + i * 2)
        sx = W / 2 + (wx - cx) * z
        sy = H / 2 + (wy - cy) * z
        if -100 < sx < W + 100 and -100 < sy < H + 100:
            near = rng.uniform(0.5, 1.6)
            sc = (24 - 14 * q) * near * z
            tiny_seed(c, sx, sy, sc, rot=0.5 * math.sin(t * 1.5 + i), col=(1, 0.97, 0.88), a=0.95)
            c.arc(sx, sy - sc * 0.15, sc * 0.45, 0, TAU)
            fillc(c, (1, 0.98, 0.92), 0.55)
    cp.add(d.rgba())
    # swallows weave through the seeds (no longer a threat)
    d = dyn(); c = d.c
    for k in range(5):
        a = t - 87.0 - k * 0.18
        x = -150 + 900 * a + 40 * math.sin(a * 3 + k)
        y = H * 0.30 + k * 26 + 50 * math.sin(a * 2.2 + k)
        if -200 < x < W + 200:
            swallow(c, x, y, 22 - k * 1.5, heading=0.08 * math.cos(a * 2.2 + k), flap=t * 15 + k, col=(0.22, 0.20, 0.26))
    cp.add(d.rgba())
    cp.glow(W / 2 + (1500 - cx) * z, H / 2 + (C18_HOR - 30 - cy) * z, 520, (1.0, 0.90, 0.68), 0.55)
    cp.post.append(lambda img, t=t: title_overlay(img, t))
    return cp

_TITLE = {}
def _text_mask(s, size, track, weight='SemiBold'):
    key = (s, size, track, weight)
    if key not in _TITLE:
        from PIL import Image, ImageDraw, ImageFont
        path = {'SemiBold': '/usr/share/fonts/opentype/noto/NotoSerifCJK-SemiBold.ttc',
                'Light': '/usr/share/fonts/opentype/noto/NotoSerifCJK-Light.ttc'}[weight]
        font = ImageFont.truetype(path, size, index=1)
        ws = [font.getlength(ch) for ch in s]
        tw = int(sum(ws) + track * (len(s) - 1) + size)
        im = Image.new('L', (tw, int(size * 1.6)), 0)
        dr = ImageDraw.Draw(im)
        x = size * 0.5
        for ch, w in zip(s, ws):
            dr.text((x, size * 0.15), ch, font=font, fill=255)
            x += w + track
        _TITLE[key] = np.asarray(im, F32) / 255.0
    return _TITLE[key]

def _put(img, m, cx_, cy_, col, a):
    if a <= 0.003:
        return img
    h_, w_ = m.shape
    x0, y0 = int(cx_ - w_ / 2), int(cy_ - h_ / 2)
    sub = img[y0:y0 + h_, x0:x0 + w_]
    mm = m[:sub.shape[0], :sub.shape[1]] * F32(a)
    sh = cv2.GaussianBlur(mm, (0, 0), 7)[..., None] * F32(0.35)
    sub = sub * (1 - sh)
    img[y0:y0 + h_, x0:x0 + w_] = sub * (1 - mm[..., None]) + mm[..., None] * np.array(col, F32)
    return img

def title_overlay(img, t):
    if t < 87.4:
        return img
    img = img.copy()
    img = _put(img, _text_mask('홀씨', 150, 40), 960, 150, (1.0, 0.98, 0.94), sm(87.5, 88.6, t))
    img = _put(img, _text_mask('HOLSSI', 26, 18, 'Light'), 960, 258, (1.0, 0.95, 0.88), 0.9 * sm(88.0, 88.9, t))
    return img
