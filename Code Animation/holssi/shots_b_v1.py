# -*- coding: utf-8 -*-
"""홀씨 -- group B: C6 (over the cliff edge), C7 (the fishing village from above), C8 (swallows)."""
from shots_a import *

# ================================================================== C6  vertigo: the cliff falls away to the sea
C6W, C6H = 3200, 2700

def _c6_cliff_line(y):
    """x of the cliff face outer edge at height y (face runs from top-left down)"""
    return 820 + 0.18 * y + 60 * math.sin(y * 0.004) + 25 * math.sin(y * 0.013)

def c6_sea(w, h, rng):
    cv = Canvas(w, h); c = cv.c
    vgrad(c, 0, 0, w, h, [(0, (0.44, 0.60, 0.66)), (0.5, (0.30, 0.47, 0.56)), (1, (0.22, 0.38, 0.48))])
    for _ in range(1600):
        x = rng.uniform(0, w); y = rng.uniform(0, h)
        L = rng.uniform(20, 70); a = rng.uniform(-0.25, 0.25)
        c.move_to(x - L / 2, y)
        c.curve_to(x - L / 4, y - 4, x + L / 4, y - 4, x + L / 2, y + 2 * math.sin(a))
        strokec(c, (0.80, 0.88, 0.90), rng.uniform(1.4, 3.0), rng.uniform(0.15, 0.45))
    for _ in range(700):
        x = rng.uniform(0, w); y = rng.uniform(0, h)
        c.arc(x, y, rng.uniform(1, 2.2), 0, TAU)
        fillc(c, (1, 0.97, 0.88), rng.uniform(0.3, 0.8))
    return cv.rgba()

def _lip(x):
    return 210 + 50 * math.sin(x * 0.006) + (x / 1000) * 120

def c6_cliff(w, h, rng):
    def face(c, r):
        c.move_to(-50, -50)
        c.line_to(_c6_cliff_line(-50), -50)
        for y in range(-50, h + 60, 20):
            c.line_to(_c6_cliff_line(y), y)
        c.line_to(-50, h + 60)
        c.close_path()
        c.fill()
    m = mask_draw(w, h, face, rng)
    xs = np.arange(w, dtype=F32)[None, :]
    yy = np.arange(h, dtype=F32)[:, None]
    edge = 820 + 0.18 * yy + 60 * np.sin(yy * 0.004) + 25 * np.sin(yy * 0.013)
    dist = np.clip((edge - xs) / 900, 0, 1)
    # ledges (strata) run roughly along the face, cracks run down it
    strata = 0.12 * np.sin(xs * 0.045 + np.sin(yy * 0.004) * 3) + 0.06 * np.sin(xs * 0.11 + yy * 0.01)
    cracks = -0.10 * (np.sin(yy * 0.02 + np.sin(xs * 0.03) * 2) > 0.92)
    depth = np.clip(yy / h, 0, 1)
    v = 0.18 - 0.30 * dist ** 0.7 + strata + cracks - depth * 0.12
    arr = celpaint_h(m * 0.5, m, [(0.30, 0.26, 0.27), (0.48, 0.40, 0.35), (0.66, 0.56, 0.44), (0.88, 0.76, 0.58)],
                     light=(0.6, -0.8), step=4, gain=1.0, seed=61, blotch=0.10, extra=v, cuts=(0.30, 0.45, 0.62))
    cv = Canvas(w, h); c = cv.c
    # moss and grass tufts clinging to ledges
    for _ in range(70):
        y = rng.uniform(250, h); x = _c6_cliff_line(y) - rng.uniform(10, 700)
        for k in range(rng.integers(3, 9)):
            r = rng.uniform(3, 9) * (1 - 0.5 * y / h)
            c.save(); c.translate(x + rng.uniform(-22, 22), y + rng.uniform(-8, 8)); c.scale(1.7, 1.0)
            c.arc(0, 0, r, 0, TAU); c.restore()
            fillc(c, lc((0.30, 0.42, 0.27), (0.52, 0.62, 0.36), rng.random()), 0.8)
    # pale streaks down the face
    for _ in range(60):
        x0 = rng.uniform(100, 1200); y0 = rng.uniform(250, h * 0.7)
        if x0 > _c6_cliff_line(y0) - 20:
            continue
        L = rng.uniform(60, 220)
        line(c, x0, y0, x0 + L * 0.18, y0 + L, rng.uniform(2, 5), (0.92, 0.88, 0.80), rng.uniform(0.15, 0.35))
    # foam where the sea meets the cliff base
    for y in np.arange(0, h, 6):
        x = _c6_cliff_line(y)
        for k in range(3):
            c.arc(x + rng.uniform(0, 26) + k * 8, y + rng.uniform(-4, 4), rng.uniform(2, 6), 0, TAU)
            fillc(c, (0.95, 0.97, 0.96), rng.uniform(0.4, 0.9) * (0.3 + 0.7 * min(1, y / 900)))
    # grassy lip along the top, following the cliff edge
    lip_end = _c6_cliff_line(_lip(1100)) + 20
    c.move_to(-40, -40)
    for x in np.arange(-40, lip_end, 10):
        c.line_to(x, _lip(x))
    c.curve_to(lip_end + 30, _lip(lip_end) - 10, lip_end + 40, _lip(lip_end) - 60, lip_end + 20, -40)
    c.close_path()
    fillc(c, (0.42, 0.54, 0.33))
    for x in np.arange(-40, lip_end + 20, 3):
        y = _lip(min(x, lip_end))
        blade(c, x, y - 6, rng.uniform(16, 40), rng.uniform(-10, 14), 2.2,
              lc((0.30, 0.44, 0.28), (0.85, 0.82, 0.55), rng.random() ** 1.3), 0.95)
    for _ in range(170):
        x = rng.uniform(0, lip_end); y = rng.uniform(0, _lip(x) - 8)
        c.arc(x, y, rng.uniform(2, 4), 0, TAU)
        fillc(c, (1, 0.97, 0.88) if rng.random() < 0.7 else (0.84, 0.78, 0.96), 0.9)
    return over(arr, cv.rgba())

def c06(t, fi):
    cp = Comp(); grade(cp, WARM_GRADE)
    u = ease(lin(26.0, 30.2, t))
    cy = lerp(560, 1700, u)
    cx = lerp(1150, 1300, u)
    sea = StaticArr('c6_sea', C6W, C6H, c6_sea)
    cl = StaticArr('c6_cl', C6W, C6H, c6_cliff)
    # the sea is far below: parallax slower than the cliff
    cp.add(sea.view(cx * 0.7 + 400, cy * 0.55 + 700, 0.85), blur=0.8, haze=((0.80, 0.86, 0.88), 0.15))
    # gulls circling far below
    d = dyn(); c = d.c
    for k, (gx, gy, r) in enumerate(((1250, 820, 70), (1500, 700, 50), (1100, 600, 40))):
        a = t * (0.9 + 0.2 * k) + k * 2
        x = gx + math.cos(a) * r * 2; y = gy - (cy - 560) * 0.45 + math.sin(a) * r
        f = math.sin(t * 9 + k)
        c.move_to(x - 12, y - 5 * f); c.line_to(x, y); c.line_to(x + 12, y - 5 * f)
        strokec(c, (0.98, 0.98, 0.95), 2.4, 0.9)
        c.move_to(x - 12 + 14, y - 5 * f + 20); c.line_to(x + 14, y + 20); c.line_to(x + 12 + 14, y - 5 * f + 20)
        strokec(c, (0.12, 0.2, 0.25), 2, 0.25)
    cp.add(d.rgba())
    cp.add(cl.view(cx, cy, 1.0))
    # the seed drifts out over the drop
    d = dyn(); c = d.c
    sx = lerp(820, 1080, u) + 30 * math.sin((t - 26) * 0.7)
    sy = lerp(330, 300, u) + 12 * math.sin((t - 26) * 1.1)
    s = lerp(70, 56, u)
    seed(c, sx, sy, s, rot=0.2 * math.sin((t - 26) * 0.8), t=t, light=(1, 0.95, 0.82), rim=1.4)
    cp.add(d.rgba())
    cp.glow(sx, sy, 90, (1, 0.96, 0.85), 0.3)
    cp.glow(1800, 0, 700, (1.0, 0.9, 0.7), 0.35)
    return cp

# ================================================================== C7  the fishing village from above
C7W, C7H = 3400, 2200
ROOF_COLS = [((0.74, 0.36, 0.24), (0.52, 0.24, 0.18)), ((0.30, 0.55, 0.56), (0.20, 0.38, 0.42)),
             ((0.82, 0.62, 0.36), (0.58, 0.42, 0.26)), ((0.55, 0.56, 0.62), (0.38, 0.39, 0.45)),
             ((0.85, 0.80, 0.70), (0.62, 0.58, 0.52))]

def c7_ground(w, h, rng):
    cv = Canvas(w, h); c = cv.c
    vgrad(c, 0, 0, w, h, [(0, (0.68, 0.64, 0.48)), (1, (0.62, 0.58, 0.44))])
    dabs(c, rng, 9000, (0, w), (0, h), (0.58, 0.60, 0.42), 0.10, 7, ang=0.4, angv=1.4, length=2.0, alpha=(0.2, 0.5))
    # harbour water (bottom-right)
    c.move_to(w, h * 0.45)
    c.curve_to(w * 0.8, h * 0.55, w * 0.62, h * 0.75, w * 0.55, h)
    c.line_to(w, h)
    c.close_path()
    pat = cairo.LinearGradient(w * 0.6, h * 0.5, w, h)
    pat.add_color_stop_rgb(0, 0.36, 0.58, 0.62)
    pat.add_color_stop_rgb(1, 0.24, 0.44, 0.52)
    c.set_source(pat)
    c.fill()
    for _ in range(500):
        x = rng.uniform(w * 0.6, w); y = rng.uniform(h * 0.5, h)
        if y < h * 0.45 + (w - x) * 0.4:
            continue
        line(c, x, y, x + rng.uniform(10, 30), y, 2, (0.75, 0.88, 0.90), rng.uniform(0.2, 0.5))
    # lanes
    for (pts, wd) in (([(0, 900), (700, 820), (1300, 1000), (2000, 900), (2600, 1150)], 46),
                      ([(1100, 0), (1150, 600), (1300, 1000), (1250, 1600), (1500, h)], 38),
                      ([(2000, 900), (2100, 500), (2400, 0)], 30)):
        c.move_to(*pts[0])
        for k in range(1, len(pts) - 1):
            mx, my = (pts[k][0] + pts[k + 1][0]) / 2, (pts[k][1] + pts[k + 1][1]) / 2
            c.curve_to(pts[k][0], pts[k][1], pts[k][0], pts[k][1], mx, my)
        c.line_to(*pts[-1])
        strokec(c, (0.86, 0.80, 0.66), wd)
    return cv.rgba()

def _house(c, rng, x, y, w, h, ang, cols):
    lit, dark = cols
    c.save(); c.translate(x, y); c.rotate(ang)
    # cast shadow (sun upper-left)
    c.rectangle(-w / 2 + 14, -h / 2 + 18, w, h)
    fillc(c, (0.20, 0.22, 0.20), 0.35)
    # roof halves along the ridge (long axis = w)
    c.rectangle(-w / 2, -h / 2, w, h / 2)
    fillc(c, lit)
    c.rectangle(-w / 2, 0, w, h / 2)
    fillc(c, dark)
    for k in range(1, int(w / 9)):
        xx = -w / 2 + k * 9
        line(c, xx, -h / 2, xx, 0, 1.2, cm(lit, 0.82), 0.6)
        line(c, xx, 0, xx, h / 2, 1.2, cm(dark, 0.8), 0.6)
    line(c, -w / 2, 0, w / 2, 0, 3, cm(dark, 0.7), 0.9)
    c.rectangle(-w / 2, -h / 2, w, h)
    strokec(c, INK, 1.6, 0.5)
    if rng.random() < 0.5:
        c.rectangle(w * 0.2, -h * 0.35, w * 0.1, h * 0.18)
        fillc(c, (0.45, 0.40, 0.36))
    c.restore()

def c7_town(w, h, rng):
    cv = Canvas(w, h); c = cv.c
    for _ in range(120):
        x = rng.uniform(0, w * 0.75); y = rng.uniform(0, h)
        if y > h * 0.45 + (w - x) * 0.4 and x > w * 0.55:
            continue
        hw = rng.uniform(70, 150); hh = rng.uniform(50, 90)
        _house(c, rng, x, y, hw, hh, rng.choice([0.0, 0.08, -0.08, math.pi / 2 + 0.05]), ROOF_COLS[rng.integers(0, 5)])
    # laundry lines
    for _ in range(14):
        x = rng.uniform(0, w * 0.7); y = rng.uniform(0, h)
        L = rng.uniform(80, 160)
        line(c, x, y, x + L, y + 10, 1.2, (0.3, 0.3, 0.3), 0.7)
        for k in range(5):
            xx = x + L * (k + 0.5) / 5
            c.rectangle(xx - 6, y + 10 * (k + 0.5) / 5, 12, 16)
            fillc(c, [(0.95, 0.95, 0.9), (0.80, 0.30, 0.25), (0.35, 0.55, 0.75), YEL][rng.integers(0, 4)], 0.9)
    # boats in the harbour
    for _ in range(9):
        x = rng.uniform(w * 0.72, w * 0.95); y = rng.uniform(h * 0.62, h * 0.95)
        c.save(); c.translate(x, y); c.rotate(rng.uniform(-0.4, 0.4))
        c.move_to(-40, 0); c.curve_to(-20, -16, 30, -14, 44, 0); c.curve_to(30, 14, -20, 16, -40, 0)
        fillc(c, (0.96, 0.95, 0.90))
        c.move_to(-40, 0); c.curve_to(-20, -16, 30, -14, 44, 0); c.curve_to(30, 14, -20, 16, -40, 0)
        strokec(c, (0.75, 0.25, 0.20), 3)
        c.restore()
    return cv.rgba()

def c7_trees(w, h, rng):
    circ = []
    for _ in range(60):
        cx_, cy_ = rng.uniform(0, w * 0.8), rng.uniform(0, h)
        for k in range(rng.integers(3, 8)):
            circ.append((cx_ + rng.uniform(-40, 40), cy_ + rng.uniform(-30, 30), rng.uniform(22, 46), 0.7))
    hh, m = dome_field(w, h, circ)
    arr = celpaint_h(hh, m, [(0.16, 0.28, 0.22), (0.28, 0.44, 0.28), (0.44, 0.58, 0.32), (0.70, 0.74, 0.44)],
                     light=(-0.6, -0.8), step=6, gain=5.0, seed=71)
    # tree shadows
    sh = np.zeros_like(arr)
    M = np.float32([[1, 0, 16], [0, 1, 20]])
    a = cv2.warpAffine(arr[..., 3], M, (w, h))
    sh[..., 3] = a * 0.35
    return over(sh, arr)

def c07(t, fi):
    cp = Comp(); grade(cp, WARM_GRADE)
    u = (t - 31.0) / 5.0
    cx, cy = lerp(1300, 1750, u), lerp(950, 1150, u)
    z = 1.12
    g = StaticArr('c7_g', C7W, C7H, c7_ground)
    tw = StaticArr('c7_t', C7W, C7H, c7_town)
    tr = StaticArr('c7_tr', C7W, C7H, c7_trees)
    cp.add(g.view(cx, cy, z), tx='d', tamp=0.06)
    cp.add(tw.view(cx, cy, z), tx='d', tamp=0.05)
    cp.add(tr.view(cx, cy, z))
    # the seed and its tiny shadow cross the roofs
    d = dyn(); c = d.c
    sx = lerp(420, 1560, ease(u)) + 20 * math.sin(t * 1.3)
    sy = lerp(260, 640, ease(u)) + 14 * math.sin(t * 0.9)
    c.save(); c.translate(sx + 110, sy + 160); c.scale(1.6, 1.0)
    c.arc(0, 0, 18, 0, TAU); c.restore()
    fillc(c, (0.1, 0.12, 0.1), 0.30)
    seed(c, sx, sy, 66, rot=0.4 * math.sin(t * 0.8) - 0.3, t=t, light=(1, 0.96, 0.85), rim=1.3)
    cp.add(d.rgba())
    cp.glow(sx, sy, 90, (1, 0.97, 0.88), 0.4)
    cp.glow(0, 0, 900, (1.0, 0.9, 0.7), 0.3)
    return cp

# ================================================================== C8  swallows: the near miss
def flock(t):
    """returns list of (x, y, size, heading, flap) for the swallows"""
    birds = []
    rng = np.random.default_rng(88)
    for k in range(9):
        t0 = 36.0 + rng.uniform(-0.4, 0.9)
        sp = rng.uniform(900, 1300)
        y0 = rng.uniform(120, 860)
        a = t - t0
        x = W + 150 - sp * a
        y = y0 + 60 * math.sin(a * 2.2 + k) + rng.uniform(-30, 30)
        s = rng.uniform(26, 44)
        heading = math.pi + 0.18 * math.cos(a * 2.2 + k)
        birds.append((x, y, s, heading, t * 16 + k))
    # the attacker: swoops at the seed
    a = (t - 37.15) / 0.9
    if -0.3 < a < 1.4:
        x = lerp(W + 200, -300, a)
        y = H * 0.48 - 260 * math.sin(math.pi * min(1, max(0, a))) * 0.0 + 380 * (a - 0.55) ** 2 - 60
        birds.append((x, y, 66, math.pi + math.atan2(-760 * (a - 0.55) * 0.5, 1200), t * 18))
    return birds

def c08(t, fi):
    cp = Comp(); grade(cp, WARM_GRADE)
    u = t - 36.0
    d = dyn(); c = d.c
    vgrad(c, 0, 0, W, H, [(0, (0.46, 0.62, 0.76)), (0.6, (0.72, 0.80, 0.84)), (1, (0.95, 0.88, 0.76))])
    cp.add(d.rgba())
    cl = StaticArr('c8_cl', C1W, C1H, c1_clouds)
    cp.add(cl.view(1150 - 40 * u, 300, 1.5), blur=5, haze=((0.95, 0.92, 0.88), 0.2))
    # the seed: tumbles in the swallow's wake
    hit = 37.62
    k = max(0.0, t - hit)
    sx = W * 0.52 - 220 * (1 - math.exp(-k * 2.5)) + 8 * nz(u, 3)
    sy = H * 0.46 + 160 * (1 - math.exp(-k * 2.0)) + 10 * math.sin(u * 1.1)
    spin = 4.2 * (1 - math.exp(-k * 1.8)) if k > 0 else 0.0
    d = dyn(); c = d.c
    birds = flock(t)
    far = [b for b in birds if b[2] < 40]
    near = [b for b in birds if b[2] >= 40]
    for (x, y, s, hd, fl) in far:
        swallow(c, x, y, s, heading=hd, flap=fl, col=(0.20, 0.24, 0.32))
    cp.add(d.rgba(), blur=1.5, haze=((0.85, 0.88, 0.90), 0.2))
    d = dyn(); c = d.c
    seed(c, sx, sy, 92, rot=0.15 * math.sin(u * 0.9) + spin, t=t, light=(1, 0.95, 0.82), rim=1.4)
    # wake: air streaks behind the near birds
    for (x, y, s, hd, fl) in near:
        for j in range(5):
            yy = y + (j - 2) * s * 0.3
            c.move_to(x + s * 1.2, yy)
            c.curve_to(x + s * 4, yy + 4, x + s * 7, yy - 6, x + s * (9 + j), yy)
            strokec(c, (1, 1, 1), 2, 0.25)
        swallow(c, x, y, s, heading=hd, flap=fl, col=(0.14, 0.17, 0.25))
    cp.add(d.rgba())
    cp.glow(sx, sy, 110, (1, 0.96, 0.85), 0.25)
    cp.glow(1700, 60, 600, (1.0, 0.92, 0.72), 0.35)
    return cp
