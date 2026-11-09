# -*- coding: utf-8 -*-
"""홀씨 (HOLSSI) -- shots."""
from eng import *
import math
import numpy as np
import cairo

WARM_GRADE = dict(lift=(0.035, 0.032, 0.035), gain=(1.02, 0.99, 0.95), sat=0.94, contrast=0.94)

def grade(cp, g):
    cp.lift, cp.gain, cp.sat, cp.contrast = g['lift'], g['gain'], g['sat'], g['contrast']

# ================================================================== C1  dawn meadow on the cliff
C1W, C1H = 2300, 1300
C1_HORIZON = 640
C1_SUN = (900, 600)
CLOUD_PAL = [(0.70, 0.64, 0.77), (0.93, 0.79, 0.72), (1.0, 0.90, 0.78), (1.0, 0.97, 0.90)]

def domes_union(w, h, groups):
    """groups: list of (circles, clip_fn). per-group clip, max-combined"""
    H_ = np.zeros((h, w), F32)
    for circles, clip in groups:
        hh, _ = dome_field(w, h, circles, clip=clip)
        H_ = np.maximum(H_, hh)
    return H_, np.clip(H_ / 0.04, 0, 1)

def rect_clip(x0, x1, ybot, wav=0.0, ph=0.0):
    return flat_bottom_clip(x0, x1, lambda xx: ybot + wav * math.sin(xx * 0.018 + ph))

def c1_sky(c, rng):
    vgrad(c, 0, 0, C1W, C1_HORIZON + 10, [(0, (0.52, 0.66, 0.78)), (0.40, (0.78, 0.83, 0.82)),
                                           (0.78, (0.99, 0.88, 0.70)), (1, (1.0, 0.86, 0.66))])
    radial(c, C1_SUN[0], C1_SUN[1], 560, (1.0, 0.93, 0.78), 0.6)
    c.arc(C1_SUN[0], C1_SUN[1], 34, 0, TAU)
    fillc(c, (1.0, 0.97, 0.88), 0.95)

def c1_clouds(w, h, rng):
    groups = []
    for (x, y, cw, ch) in ((420, 220, 560, 100), (1180, 170, 700, 120), (1880, 250, 580, 96), (760, 380, 660, 70),
                           (1560, 420, 520, 60), (240, 470, 380, 46), (2000, 500, 360, 40), (1150, 520, 480, 40)):
        groups.append((cloud_circles(rng, x, y, cw, ch), rect_clip(x - cw, x + cw, y, ch * 0.04, x)))
    hh, m = domes_union(w, h, groups)
    far = np.clip((np.arange(h, dtype=F32)[:, None] - 160) / 380, 0, 1)
    pal = CLOUD_PAL
    arr = celpaint_h(hh, m, pal, light=(-0.2, -0.98), step=9, gain=5.0, cuts=(0.40, 0.53, 0.66), seed=1)
    # distant clouds melt into the warm haze
    arr[..., :3] = arr[..., :3] * (1 - 0.45 * far[..., None]) + np.array((1.0, 0.86, 0.70), F32) * arr[..., 3:4] * (
        0.45 * far[..., None])
    return arr

def c1_sea(c, rng):
    vgrad(c, 0, C1_HORIZON - 3, C1W, C1H, [(0, (0.95, 0.88, 0.76)), (0.08, (0.74, 0.77, 0.76)),
                                           (0.5, (0.48, 0.61, 0.66)), (1, (0.34, 0.49, 0.57))])
    dabs(c, rng, 1400, (0, C1W), (C1_HORIZON + 6, C1H), (0.56, 0.67, 0.70), 0.06, 2.5, ang=0.0, angv=0.03,
         length=12.0, alpha=(0.15, 0.35))
    dabs(c, rng, 700, (0, C1W), (C1_HORIZON + 2, C1_HORIZON + 120), (0.98, 0.92, 0.82), 0.03, 2.0, ang=0.0,
         angv=0.02, length=14.0, alpha=(0.2, 0.45))

def c1_headland(w, h, rng):
    circ = []
    for k in range(18):
        x = 40 + k * 34 + rng.uniform(-10, 10)
        r = 70 + 50 * math.sin(k / 17 * math.pi) + rng.uniform(-10, 10)
        circ.append((x, C1_HORIZON + r * 0.35, r, 0.6 + 0.4 * r / 120))
    for k in range(9):
        x = 1950 + k * 40; r = 40 + 25 * math.sin(k / 8 * math.pi)
        circ.append((x, C1_HORIZON + r * 0.5, r, 0.6))
    hh, m = dome_field(w, h, circ, clip=rect_clip(-100, w + 100, C1_HORIZON + 2))
    pal = [(0.50, 0.56, 0.64), (0.60, 0.65, 0.70), (0.72, 0.74, 0.76), (0.88, 0.84, 0.78)]
    return celpaint_h(hh, m, pal, light=(0.1, -0.99), step=8, gain=4.5, seed=2, blotch=0.05)

EDGE = 1760

def _meadow_top(x):
    return 860 - 70 * math.exp(-((x - 650) / 620) ** 2) + 14 * math.sin(x * 0.006) - 30 * (x / C1W)

def c1_meadow(w, h, rng):
    # cliff rocks
    def cliffp(c, r):
        c.move_to(EDGE - 60, _meadow_top(EDGE) - 4)
        c.curve_to(EDGE + 40, 900, EDGE + 90, 1020, EDGE + 150, h + 20)
        c.line_to(EDGE - 200, h + 20)
        c.close_path()
        c.fill()
    cm_ = mask_draw(w, h, cliffp, rng)
    xs_ = np.arange(w, dtype=F32)[None, :]
    yy_ = np.arange(h, dtype=F32)[:, None]
    strata = 0.18 * np.sin(yy_ * 0.09 + np.sin(xs_ * 0.02) * 2) + 0.25 * np.clip((xs_ - EDGE + 40) / 120, -1, 1)
    rock = celpaint_h(cm_ * 0.6, cm_, [(0.28, 0.25, 0.25), (0.44, 0.38, 0.34), (0.60, 0.52, 0.43), (0.84, 0.72, 0.56)],
                      light=(-0.5, -0.86), step=6, gain=2.0, seed=3, extra=strata, blotch=0.08)
    # the meadow body: rolling domes clipped by the crest line and the cliff lip
    circ = []
    for _ in range(26):
        x = rng.uniform(-80, EDGE + 40)
        top = _meadow_top(x)
        y = rng.uniform(top + 120, h + 200)
        r = rng.uniform(260, 520)
        circ.append((x, y, r, 0.5 + 0.5 * rng.random()))
    def clip(c):
        c.move_to(-40, h + 40)
        for x in range(-40, EDGE + 1, 10):
            c.line_to(x, _meadow_top(x))
        c.line_to(EDGE + 25, _meadow_top(EDGE) + 18)
        c.line_to(EDGE + 30, _meadow_top(EDGE) + 45)
        c.line_to(EDGE - 160, h + 40)
        c.close_path()
    hh, _ = dome_field(w, h, circ, clip=clip)
    pm = mask_draw(w, h, lambda c, r: (clip(c), c.fill()), rng)
    hh = np.maximum(hh * 0.8, pm * 0.3)
    yy = np.arange(h, dtype=F32)[:, None]
    depth = np.clip((yy - 800) / 500, 0, 1)
    grass = celpaint_h(hh, pm, [(0.24, 0.36, 0.26), (0.36, 0.49, 0.32), (0.50, 0.60, 0.38), (0.74, 0.74, 0.50)],
                       light=(0.15, -0.99), step=30, gain=2.2, hmix=0.15, cuts=(0.34, 0.50, 0.70), seed=4,
                       blotch=0.10, namp=0.02, extra=0.14 - depth * 0.22, smooth=6)
    cvg = Canvas(w, h); cg = cvg.c
    cg.save(); clip(cg); cg.clip()
    for _ in range(26000):
        x = rng.uniform(-20, EDGE + 40)
        top = _meadow_top(x)
        y = rng.uniform(top, h)
        k = 0.5 + 1.2 * (y - 780) / 520
        hh_ = rng.uniform(5, 12) * k
        lean = rng.uniform(-2, 2) * k
        col = lc((0.22, 0.34, 0.24), (0.66, 0.70, 0.46), rng.random() ** 1.3)
        cg.move_to(x, y)
        cg.line_to(x + lean, y - hh_)
        src(cg, col, rng.uniform(0.25, 0.55))
        cg.set_line_width(rng.uniform(1.2, 2.4) * k)
        cg.stroke()
    cg.restore()
    grass = over(grass, cvg.rgba())
    arr = over(rock, grass)
    # painted details on top: crest blades, bare stems, small flowers
    cv = Canvas(w, h); c = cv.c
    for x in np.arange(-20, EDGE + 20, 3.0):
        y = _meadow_top(x) + 4
        blade(c, x, y, rng.uniform(8, 24), rng.uniform(-5, 7), 1.7,
              lc((0.32, 0.44, 0.28), (0.95, 0.86, 0.58), rng.uniform(0, 1) ** 1.5), 0.95)
    for _ in range(190):
        x = rng.uniform(20, EDGE - 30)
        y = _meadow_top(x) + rng.uniform(4, 150)
        hgt = rng.uniform(34, 80) * (0.6 + 0.7 * (y - 780) / 420)
        lean = rng.uniform(-9, 9)
        c.move_to(x, y)
        c.curve_to(x + lean * 0.3, y - hgt * 0.5, x + lean * 0.8, y - hgt * 0.8, x + lean, y - hgt)
        strokec(c, (0.24, 0.30, 0.20), 1.8, 0.95)
        c.arc(x + lean, y - hgt, 3.0, 0, TAU)
        fillc(c, (0.70, 0.64, 0.46))
        c.arc(x + lean - 0.8, y - hgt - 1.2, 1.4, 0, TAU)
        fillc(c, (1.0, 0.92, 0.70), 0.8)
    for _ in range(320):
        x = rng.uniform(0, EDGE - 20); y = _meadow_top(x) + rng.uniform(16, 360)
        c.arc(x, y, rng.uniform(1.3, 2.6), 0, TAU)
        fillc(c, (1, 0.97, 0.88) if rng.random() < 0.7 else (0.84, 0.78, 0.96), 0.95)
    arr = over(arr, cv.rgba())
    # mist
    yy = np.arange(h, dtype=F32)[:, None]
    mist = np.exp(-((yy - 860) / 70) ** 2) * 0.28
    arr[..., :3] = arr[..., :3] * (1 - mist[..., None]) + np.array((1, 0.94, 0.84), F32) * mist[..., None] * arr[..., 3:4]
    return arr

def c1_fore(c, rng):
    for _ in range(900):
        x = rng.uniform(-50, C1W + 50)
        side = min(x, C1W - x)
        hmax = 300 if side < 600 else 120
        blade(c, x, C1H + 10, rng.uniform(40, hmax), rng.uniform(-55, 55), rng.uniform(3, 7),
              lc(TEAL_D, FOREST, rng.uniform(0, 1)), 0.95)
    for (x, hgt, lean) in ((190, 340, 20), (270, 270, -15), (2050, 310, -25), (2140, 390, 10)):
        c.move_to(x, C1H)
        c.curve_to(x + lean * 0.3, C1H - hgt * 0.5, x + lean * 0.8, C1H - hgt * 0.85, x + lean, C1H - hgt)
        strokec(c, (0.10, 0.18, 0.15), 4.5, 1)
        c.arc(x + lean, C1H - hgt, 9, 0, TAU)
        fillc(c, (0.26, 0.26, 0.20))

def c01(t, fi):
    cp = Comp(); grade(cp, WARM_GRADE)
    z = 1.0 + 0.035 * lin(0, 7, t)
    cx, cy = 1150, 650
    sky = Static('c1_sky', C1W, C1H, c1_sky)
    cl = StaticArr('c1_cl', C1W, C1H, c1_clouds)
    sea = Static('c1_sea', C1W, C1H, c1_sea)
    hd = StaticArr('c1_hd', C1W, C1H, c1_headland)
    md = StaticArr('c1_md', C1W, C1H, c1_meadow)
    fg = Static('c1_fg', C1W, C1H, c1_fore)
    cp.add(sky.view(cx, cy, z))
    cp.add(cl.view(cx - 5 * t, cy, z))
    cp.add(sea.view(cx, cy, z))
    d = dyn(); c = d.c
    rng = np.random.default_rng(int(t * 10))
    sx, sy = W / 2 + (C1_SUN[0] - cx) * z, H / 2 + (C1_SUN[1] - cy) * z
    hy = H / 2 + (C1_HORIZON - cy) * z
    for _ in range(160):
        yy = hy + 4 + rng.random() ** 1.8 * 280 * z
        xx = sx + rng.normal(0, 1) * (18 + (yy - hy) * 0.5)
        w = 3 + (yy - hy) * 0.06
        line(c, xx - w, yy, xx + w, yy, 1.5 + (yy - hy) * 0.008, (1, 0.95, 0.82), rng.uniform(0.3, 0.9))
    cp.add(d.rgba())
    cp.add(hd.view(cx, cy, z), haze=((0.95, 0.88, 0.80), 0.35))
    cp.add(md.view(cx, cy, z))
    d = dyn(); c = d.c
    for k, (bx, by, sp) in enumerate(((600, 330, 30), (650, 350, 26), (1500, 280, -20))):
        x = bx + sp * t; y = by + 6 * math.sin(t * 2 + k)
        f = math.sin(t * 12 + k * 2)
        c.move_to(x - 7, y - 3 * f); c.line_to(x, y); c.line_to(x + 7, y - 3 * f)
        strokec(c, (0.35, 0.33, 0.35), 1.6, 0.8)
    cp.add(d.rgba())
    cp.add(fg.view(cx, cy, z * 1.02, sway=(t, 9, 0, H)), blur=2.5)
    cp.glow(sx, sy, 380, (1.0, 0.90, 0.70), 0.5)
    cp.fade = sm(0, 1.6, t)
    return cp

# ================================================================== C3  ECU: dew on the last seed, the ladybug
C3_REC = (1180, 560)
C3_PAP = (870, 290)

def c3_bg(c, rng):
    vgrad(c, 0, 0, W, H, [(0, (0.98, 0.90, 0.72)), (0.45, (0.90, 0.86, 0.66)), (0.7, (0.56, 0.66, 0.42)),
                          (1, (0.30, 0.44, 0.30))])
    for _ in range(40):
        x, y = rng.uniform(0, W), rng.uniform(H * 0.5, H)
        radial(c, x, y, rng.uniform(60, 200), lc(LEAF, SAGE, rng.random()), 0.6)
    for _ in range(26):
        x, y = rng.uniform(0, W), rng.uniform(0, H * 0.7)
        r = rng.uniform(18, 60)
        c.arc(x, y, r, 0, TAU)
        fillc(c, (1, 0.96, 0.84), rng.uniform(0.15, 0.4))
        c.arc(x, y, r, 0, TAU)
        strokec(c, (1, 0.98, 0.9), 2, 0.3)

def c3_mid(c, rng):
    for (x0, y0, x1, y1) in ((300, H + 20, 420, 200), (1650, H + 20, 1560, 330), (1820, H + 20, 1900, 120)):
        c.move_to(x0, y0)
        c.curve_to(x0, (y0 + y1) / 2, x1, (y0 + y1) / 2, x1, y1)
        strokec(c, (0.35, 0.46, 0.28), 16, 1)
        c.arc(x1, y1, 34, 0, TAU)
        fillc(c, (0.70, 0.66, 0.50))

def stem_path(base, tip, bend):
    (x0, y0), (x1, y1) = base, tip
    pts = []
    for k in range(25):
        u = k / 24
        x = lerp(x0, x1, u) + bend * math.sin(math.pi * u) * 0.6 + bend * u * u * 0.4
        y = lerp(y0, y1, u)
        pts.append((x, y))
    return pts

def c03(t, fi):
    cp = Comp(); grade(cp, WARM_GRADE)
    bg = Static('c3_bg', W, H, c3_bg)
    mid = Static('c3_mid', W, H, c3_mid)
    drift = 6 * nz(t * 0.4, 1)
    cp.add(bg.view(W / 2 + drift * 0.3, H / 2), blur=26)
    cp.add(mid.view(W / 2 + drift * 0.6, H / 2), blur=10, haze=((0.95, 0.90, 0.75), 0.25))
    # ladybug climbs the stem
    u = kf(t, [(12.0, -0.15), (16.6, 0.78)])
    load = max(0.0, u) ** 2
    sway = 4 * math.sin(t * 1.3) + 26 * load + 3 * math.sin(t * 7) * load
    base = (1250, H + 40)
    tip = (C3_REC[0] + sway, C3_REC[1] + 6 * load)
    pts = stem_path(base, tip, -40 + sway * 0.4)
    d = dyn(); c = d.c
    stem(c, pts, 15)
    rng = np.random.default_rng(3)
    receptacle(c, tip[0], tip[1], 46, rng)
    # the seed: beak from the pappus down into the receptacle
    tremble = (0.02 + 0.05 * load) * math.sin(t * 13) + 0.01 * math.sin(t * 2.1)
    px, py = C3_PAP[0] + sway * 1.3, C3_PAP[1] + 4 * load
    ang = math.atan2(tip[1] - 30 - py, tip[0] - 10 - px)
    rot = ang - math.pi / 2 + tremble
    blen = math.hypot(tip[0] - 10 - px, tip[1] - 30 - py) / (1.25 * 250)
    seed(c, px, py, 250, rot=rot, t=t, dew=1.0, achene=False, beak=blen, rim=1.0, light=(1, 0.93, 0.78))
    if u > -0.1:
        k = int(max(0, min(23, u * 24)))
        (ax, ay), (bx, by) = pts[k], pts[min(24, k + 1)]
        fu = u * 24 - k
        lx, ly = lerp(ax, bx, fu), lerp(ay, by, fu)
        heading = math.atan2(by - ay, bx - ax) + math.pi / 2
        ladybug(c, lx + 14, ly, 24, ang=heading, t=t)
    cp.add(d.rgba(), tx='d', tamp=0.05)
    # blurred foreground blade
    d = dyn(); c = d.c
    c.move_to(-40, H + 40)
    c.curve_to(200, 700, 380, 520, 520, 380)
    strokec(c, (0.16, 0.28, 0.20), 60, 1)
    cp.add(d.rgba(), blur=18)
    cp.glow(1720, 110, 650, (1.0, 0.90, 0.68), 0.55)
    return cp

# ================================================================== C9  the cloud canyon (long tracking)
C9W, C9H = 3600, 4200

C9_PAL = [(0.66, 0.60, 0.76), (0.90, 0.76, 0.74), (1.0, 0.89, 0.76), (1.0, 0.97, 0.88)]

def c9_far(w, h, rng):
    circ = []
    for _ in range(90):
        x = rng.uniform(0, w); y = rng.uniform(h * 0.66, h * 0.98); r = rng.uniform(80, 220)
        circ.append((x, y, r, 0.5 + 0.5 * r / 220))
    hh, m = dome_field(w, h, circ)
    return celpaint_h(hh, m, [(0.80, 0.72, 0.80), (0.95, 0.84, 0.80), (1.0, 0.92, 0.82), (1.0, 0.97, 0.90)],
                      light=(0.55, -0.83), step=10, gain=4.0, seed=9)

def _canyon(w, h, rng, side):
    circ = []
    xs = 700 if side < 0 else w - 700
    for _ in range(170):
        y = rng.uniform(-100, h + 100)
        reach = 360 + 160 * math.sin(y * 0.0016 + side) + 90 * math.sin(y * 0.0053)
        x = xs - side * rng.uniform(-700, reach * 0.55)
        r = rng.uniform(170, 330)
        circ.append((x, y, r, 0.5 + 0.5 * r / 330))
    for _ in range(420):
        y = rng.uniform(-100, h + 100)
        reach = 360 + 160 * math.sin(y * 0.0016 + side) + 90 * math.sin(y * 0.0053)
        x = xs - side * (reach * rng.uniform(0.55, 1.05))
        r = rng.uniform(35, 120)
        circ.append((x, y, r, 0.35 + 0.4 * r / 120))
    hh, m = dome_field(w, h, circ)
    return celpaint_h(hh, m, C9_PAL, light=(0.55, -0.83), step=9, gain=4.2, cuts=(0.40, 0.53, 0.67),
                      seed=10 if side < 0 else 11, blotch=0.06, smooth=3.0)

def c9_left(w, h, rng):
    return _canyon(w, h, rng, -1)

def c9_right(w, h, rng):
    return _canyon(w, h, rng, 1)

def c9_near(w, h, rng):
    circ = []
    for _ in range(40):
        x = rng.choice([rng.uniform(800, 1400), rng.uniform(w - 1400, w - 800)])
        y = rng.uniform(0, h); r = rng.uniform(120, 260)
        circ.append((x, y, r, 0.7))
    hh, m = dome_field(w, h, circ)
    return celpaint_h(hh, m, [(0.86, 0.80, 0.86), (0.98, 0.90, 0.86), (1.0, 0.95, 0.88), (1.0, 0.99, 0.94)],
                      light=(0.55, -0.83), step=12, gain=3.5, seed=12)

def c09(t, fi):
    cp = Comp(); grade(cp, WARM_GRADE)
    d = dyn(); c = d.c
    vgrad(c, 0, 0, W, H, [(0, (0.33, 0.50, 0.70)), (0.5, (0.55, 0.69, 0.80)), (0.85, (0.88, 0.86, 0.80)),
                          (1, (0.99, 0.88, 0.72))])
    cp.add(d.rgba())
    u = t - 40
    far = StaticArr('c9_far', C9W, C9H, c9_far)
    L = StaticArr('c9_L', C9W, C9H, c9_left)
    R = StaticArr('c9_R', C9W, C9H, c9_right)
    N = StaticArr('c9_N', C9W, C9H, c9_near)
    base = C9H - 900
    cp.add(far.view(C9W / 2, 2300 - 18 * u, 0.8), haze=((0.98, 0.90, 0.80), 0.4), blur=2.0)
    sx = 30 * math.sin(u * 0.35)
    cp.add(L.view(C9W / 2 - 140 + sx, base - 70 * u, 1.0))
    cp.add(R.view(C9W / 2 + 140 + sx, base - 90 * u - 900, 1.0))
    # sun shafts
    d = dyn(); c = d.c
    for k, (x0, w) in enumerate(((1250, 160), (1520, 110), (1050, 90))):
        a = 0.10 + 0.04 * math.sin(u * 0.8 + k)
        pat = cairo.LinearGradient(x0, 0, x0 - 700, H)
        pat.add_color_stop_rgba(0, 1, 0.93, 0.75, a)
        pat.add_color_stop_rgba(1, 1, 0.93, 0.75, 0)
        c.set_source(pat)
        poly(c, [(x0, -20), (x0 + w, -20), (x0 + w - 820, H + 20), (x0 - 820, H + 20)])
        c.fill()
    cp.add(d.rgba())
    # the seed rides the thermal
    d = dyn(); c = d.c
    sxp = W * 0.53 + 40 * math.sin(u * 0.6) + 10 * nz(u, 2)
    syp = H * 0.47 + 18 * math.sin(u * 0.9)
    seed(c, sxp, syp, 85, rot=0.18 * math.sin(u * 0.7) + 0.05 * nz(u * 2, 3), t=t, light=(1, 0.95, 0.82),
         rim=1.4)
    cp.add(d.rgba())
    cp.add(N.view(C9W / 2, base - 260 * u + 500, 1.0), blur=14, alpha=0.8)
    cp.glow(1500, 40, 700, (1.0, 0.92, 0.72), 0.5)
    cp.glow(sxp, syp, 70, (1.0, 0.96, 0.85), 0.25)
    return cp

# ================================================================== C14  the long wait: ash, seasons, sprout
C14_BASE = (930, 800)

def c14_far(c, rng):
    vgrad(c, 0, 0, W, H, [(0, (0, 0, 0, 0)), (0.5, (0, 0, 0, 0)), (0.62, (0.42, 0.41, 0.42, 1)),
                          (1, (0.34, 0.33, 0.33, 1))])
    for _ in range(60):
        x = rng.uniform(-50, W + 50); y = rng.uniform(560, 720); hgt = rng.uniform(60, 320)
        w = rng.uniform(5, 14)
        line(c, x, y, x + rng.uniform(-8, 8), y - hgt, w, (0.20, 0.19, 0.20), 1)
        for _ in range(rng.integers(0, 3)):
            by = y - hgt * rng.uniform(0.4, 0.9)
            line(c, x, by, x + rng.uniform(-60, 60), by - rng.uniform(10, 50), w * 0.5, (0.20, 0.19, 0.20), 1)

def _ash_top(x):
    return 700 + 12 * math.sin(x * 0.004) + 6 * math.sin(x * 0.013)

def _ash_field(w, h, rng):
    """foreshortened lumps: draw on a tall canvas then squash vertically"""
    top = 690
    gh = h - top + 40
    S = 3
    tall = gh * S
    circ = []
    for _ in range(700):
        x = rng.uniform(-60, w + 60)
        yv = rng.uniform(0, tall)
        depth = yv / tall
        r = rng.uniform(30, 120) * (0.25 + 1.3 * depth)
        circ.append((x, yv, r, 0.3 + 0.7 * rng.random()))
    hh, _ = dome_field(w, tall, circ)
    hh = cv2.resize(hh, (w, gh), interpolation=cv2.INTER_AREA)
    H_ = np.zeros((h, w), F32)
    H_[top - 40:top - 40 + gh] = hh[:h - (top - 40)]
    m = np.zeros((h, w), F32)
    yy = np.arange(h)[:, None]
    xs = np.arange(w)[None, :]
    edge = top + 10 * np.sin(xs * 0.004) + 5 * np.sin(xs * 0.013)
    m = np.clip((yy - edge) / 2.0, 0, 1).astype(F32)
    H_ = np.maximum(H_ * 0.85, m * 0.25) * m
    return H_, m

ASH_PAL = [(0.30, 0.29, 0.29), (0.45, 0.44, 0.43), (0.59, 0.58, 0.56), (0.72, 0.70, 0.67)]
SNOW_PAL = [(0.62, 0.66, 0.74), (0.78, 0.81, 0.87), (0.90, 0.92, 0.95), (0.98, 0.99, 1.0)]

def _ash_detail(w, h, rng):
    cv = Canvas(w, h); c = cv.c
    for _ in range(260):
        x = rng.uniform(0, w); y = rng.uniform(705, h)
        a = rng.uniform(0, TAU); l = rng.uniform(2, 5) * (0.4 + (y - 700) / 300)
        line(c, x, y, x + math.cos(a) * l, y + math.sin(a) * l * 0.5, rng.uniform(1.2, 2.4), CHAR,
             rng.uniform(0.4, 0.8))
    for _ in range(9):
        x = rng.uniform(0, w); y = rng.uniform(760, h - 20)
        k = 0.4 + (y - 700) / 340
        l = rng.uniform(40, 110) * k; a = rng.uniform(-0.2, 0.2)
        x1, y1 = x + math.cos(a) * l, y + math.sin(a) * l * 0.4
        wd = rng.uniform(4, 8) * k
        line(c, x, y, x1, y1, wd, (0.13, 0.12, 0.12), 1)
        line(c, x, y - wd * 0.3, x1, y1 - wd * 0.3, wd * 0.3, (0.38, 0.35, 0.33), 0.9)
        bx, by = lerp(x, x1, 0.6), lerp(y, y1, 0.6)
        line(c, bx, by, bx + 14 * k, by - 9 * k, wd * 0.5, (0.13, 0.12, 0.12), 1)
    return cv.rgba()

def c14_ground(w, h, rng):
    hh, m = _ash_field(w, h, rng)
    yy = np.arange(h, dtype=F32)[:, None]
    far = np.clip(1 - (yy - 690) / 120, 0, 1) * 0.12
    arr = celpaint_h(hh, m, ASH_PAL, light=(0.5, -0.86), step=4, gain=4.0, seed=14, blotch=0.06, extra=far)
    return over(arr, _ash_detail(w, h, np.random.default_rng(141)))

def c14_snow(w, h, rng):
    hh, m = _ash_field(w, h, np.random.default_rng(abs(hash('c14_gr')) % (2 ** 32)))
    return celpaint_h(hh, m, SNOW_PAL, light=(0.5, -0.86), step=4, gain=3.0, seed=15, blotch=0.05,
                      cuts=(0.30, 0.45, 0.62))

def jag_leaf(c, x, y, ang, L, w, col=LEAF, ink=0.8, curl=0.0):
    """dandelion leaf: lanceolate with backward-pointing lobes, from base (x,y) toward ang"""
    if L < 2:
        return
    ca, sa = math.cos(ang), math.sin(ang)
    def P(u, v):
        return (x + ca * u * L - sa * v * w, y + sa * u * L + ca * v * w + curl * u * u * L * 0.25)
    top = []
    bot = []
    nl = 5
    for k in range(nl * 2 + 1):
        u = k / (nl * 2)
        wid = math.sin(math.pi * min(1, u * 1.05)) ** 0.8
        lobe = 0.55 if k % 2 == 1 else 1.0
        top.append(P(u, wid * lobe))
        bot.append(P(u, -wid * lobe))
    pts = top + [P(1.03, 0)] + bot[::-1]
    x0_, y0_ = P(0, 0); x1_, y1_ = P(1, 0)
    pat = cairo.LinearGradient(x0_, y0_, x1_, y1_)
    pat.add_color_stop_rgb(0, *cm(col, 0.7))
    pat.add_color_stop_rgb(0.6, *col)
    pat.add_color_stop_rgb(1, *lc(col, (0.85, 0.88, 0.55), 0.35))
    poly(c, pts)
    c.set_source(pat)
    c.fill()
    poly(c, bot[::-1] + [P(0, 0)] + [P(u / 10, 0) for u in range(11)])
    fillc(c, cm(col, 0.72), 0.55)
    poly(c, top + [P(1.03, 0)], close=False)
    strokec(c, lc(col, (1, 0.95, 0.7), 0.5), max(1.0, w * 0.05), 0.55)
    poly(c, pts)
    strokec(c, INK, max(1.0, w * 0.05), 0.55 * ink)
    c.move_to(*P(0, 0))
    c.line_to(*P(0.95, 0))
    strokec(c, lc(col, CREAM, 0.45), max(1.0, w * 0.07), 0.8)

def sprout(c, t, base, light=1.0):
    """growth driven by absolute time inside C14"""
    bx, by = base
    g_crack = sm(69.6, 70.2, t)
    g_stem = sm(70.0, 71.2, t)
    g_cot = sm(70.7, 71.5, t)
    g_leaf = sm(71.2, 73.0, t)
    g_flower = sm(72.6, 75.0, t)
    shade = lambda col: cm(col, 0.45 + 0.55 * light)
    if g_crack > 0:
        for a in (-2.6, -1.9, -1.2, -0.5):
            l = 26 * g_crack
            line(c, bx, by, bx + math.cos(a) * l * 1.6, by + math.sin(a) * l * 0.4 + 6, 2, (0.22, 0.20, 0.19), 0.8)
        c.save(); c.translate(bx, by + 2); c.scale(1, 0.35)
        c.arc(0, 0, 18 * g_crack, 0, TAU); c.restore()
        fillc(c, (0.30, 0.27, 0.24))
    # rosette leaves (behind the stem)
    if g_leaf > 0:
        for k, (a, L, w, d) in enumerate(((-2.75, 240, 34, 0.0), (-0.35, 260, 36, 0.12), (-2.2, 180, 28, 0.3),
                                          (-0.95, 200, 30, 0.42))):
            gk = sm(d, d + 0.6, g_leaf)
            jag_leaf(c, bx, by - 4, a, L * gk, w * (0.4 + 0.6 * gk), col=shade(lc(LEAF, MOSS, k * 0.2)),
                     curl=0.4)
    if g_stem > 0:
        h = 70 * g_stem
        tipx, tipy = bx + 8 * math.sin(g_stem * 2), by - h
        c.move_to(bx, by)
        c.curve_to(bx - 6, by - h * 0.4, tipx + 6, by - h * 0.7, tipx, tipy)
        strokec(c, INK, 9, 0.5)
        c.move_to(bx, by)
        c.curve_to(bx - 6, by - h * 0.4, tipx + 6, by - h * 0.7, tipx, tipy)
        strokec(c, shade((0.55, 0.70, 0.38)), 6.5)
        if g_cot > 0:
            for sg in (-1, 1):
                c.save()
                c.translate(tipx, tipy)
                c.rotate(sg * (0.3 + 0.9 * g_cot) - math.pi / 2 + math.pi / 2)
                c.scale(1, 0.45)
                c.arc(sg * 22 * g_cot, 0, 22 * g_cot, 0, TAU)
                c.restore()
                fillc(c, shade((0.62, 0.76, 0.40)))
    if g_flower > 0:
        h = 300 * g_flower
        fx, fy = bx + 14 * math.sin(g_flower * 1.5), by - 60 - h
        c.move_to(bx, by - 10)
        c.curve_to(bx + 4, by - h * 0.5, fx - 6, fy + h * 0.3, fx, fy)
        strokec(c, INK, 9, 0.55)
        c.move_to(bx, by - 10)
        c.curve_to(bx + 4, by - h * 0.5, fx - 6, fy + h * 0.3, fx, fy)
        strokec(c, shade((0.50, 0.64, 0.34)), 6)
        bud = 0.4 + 0.6 * g_flower
        c.save(); c.translate(fx, fy - 18 * bud); c.scale(1, 1.6)
        c.arc(0, 0, 14 * bud, 0, TAU); c.restore()
        fillc(c, shade((0.46, 0.60, 0.30)))
        for sg in (-1, 0, 1):
            c.move_to(fx + sg * 8 * bud, fy)
            c.curve_to(fx + sg * 14 * bud, fy - 18 * bud, fx + sg * 6 * bud, fy - 34 * bud, fx + sg * 2, fy - 44 * bud)
            strokec(c, shade((0.36, 0.50, 0.24)), 4, 0.9)
        if t > 74.6:
            o = sm(74.6, 76.0, t)
            c.arc(fx, fy - 46 * bud, 6 * o, 0, TAU)
            fillc(c, YEL)
        c.save(); c.translate(fx, fy - 18 * bud); c.scale(1, 1.6)
        c.arc(0, 0, 14 * bud, 0, TAU); c.restore()
        strokec(c, INK, 1.6, 0.5)
        return (fx, fy - 40 * bud)
    return None

def daylight(t):
    """time-lapse: overcast -> 4 fast day/night cycles -> dawn"""
    if t < 65.0:
        return 0.55
    if t < 72.5:
        ph = (t - 65.0) / 1.5
        return 0.5 + 0.5 * math.cos(ph * TAU)
    return lerp(0.15, 1.0, sm(72.5, 75.0, t))

def c14(t, fi):
    cp = Comp(); grade(cp, WARM_GRADE)
    L = daylight(t)
    dawn = sm(73.0, 75.5, t)
    snow = sm(67.2, 68.0, t) * (1 - sm(69.0, 69.9, t))
    d = dyn(); c = d.c
    day_top, day_bot = (0.62, 0.66, 0.70), (0.80, 0.79, 0.76)
    nt_top, nt_bot = (0.05, 0.07, 0.13), (0.14, 0.15, 0.22)
    dw_top, dw_bot = (0.56, 0.62, 0.76), (1.0, 0.82, 0.60)
    top = lc(lc(nt_top, day_top, L), dw_top, dawn)
    bot = lc(lc(nt_bot, day_bot, L), dw_bot, dawn)
    vgrad(c, 0, 0, W, 760, [(0, top), (1, bot)])
    if L < 0.4:
        stars(c, np.random.default_rng(5), 260, 0, W, 0, 600, a=(0.4 - L) / 0.4)
    cp.add(d.rgba())
    far = Static('c14_far', W, H, c14_far)
    gr = StaticArr('c14_gr', W, H, c14_ground)
    shade = 0.35 + 0.65 * L
    f = far.view(W / 2, H / 2)
    f[..., :3] *= F32(0.6 + 0.4 * shade)
    cp.add(f, blur=6, haze=(bot, 0.35))
    g = gr.view(W / 2, H / 2)
    g[..., :3] *= F32(shade) * np.array(lc((1, 1, 1), (1.08, 0.96, 0.86), dawn), F32)
    cp.add(g)
    if snow > 0.01:
        sn = StaticArr('c14_sn', W, H, c14_snow).view(W / 2, H / 2)
        sn[..., :3] *= F32(0.5 + 0.5 * shade)
        cp.add(sn, alpha=snow)
    d = dyn(); c = d.c
    # the fallen seed fades into the ash as seasons pass
    old = 1 - sm(66.5, 69.5, t)
    if old > 0.01:
        c.push_group()
        seed(c, C14_BASE[0] + 120, C14_BASE[1] - 18, 120, rot=1.42, wet=1.0, t=t, rim=0.0, light=(0.8, 0.8, 0.78))
        c.pop_group_to_source()
        c.paint_with_alpha(old * (0.5 + 0.5 * shade))
    tip = sprout(c, t, C14_BASE, light=shade)
    # snow cover
    if snow > 0.01:
        rng = np.random.default_rng(int(t * 24))
        for _ in range(int(220 * snow)):
            c.arc(rng.uniform(0, W), rng.uniform(0, H), rng.uniform(1.5, 3.5), 0, TAU)
            c.new_sub_path()
        fillc(c, WHITE, 0.8)
    if t < 65.5:
        rng = np.random.default_rng(int(t * 24))
        for _ in range(160):
            x, y = rng.uniform(0, W), rng.uniform(0, H)
            line(c, x, y, x - 4, y + 34, 1.4, (0.82, 0.84, 0.88), 0.35)
    cp.add(d.rgba())
    if tip is not None and dawn > 0:
        cp.glow(tip[0], tip[1], 260, (1.0, 0.85, 0.55), 0.55 * dawn)
        d = dyn(); c = d.c
        for k, (wd, a) in enumerate(((260, 0.10), (150, 0.12), (70, 0.14))):
            pat = cairo.LinearGradient(1560, 0, tip[0], tip[1])
            pat.add_color_stop_rgba(0, 1, 0.88, 0.62, a * dawn)
            pat.add_color_stop_rgba(1, 1, 0.88, 0.62, 0.0)
            c.set_source(pat)
            poly(c, [(1560 - wd, -10), (1560 + wd, -10), (tip[0] + wd * 0.25, tip[1] + 30),
                     (tip[0] - wd * 0.25, tip[1] + 30)])
            c.fill()
        cp.add(d.rgba(), blur=10)
    zp = 1.0 + 0.32 * ease(lin(64.0, 76.0, t))
    def push(img, zp=zp):
        M = np.float32([[zp, 0, C14_BASE[0] * (1 - zp)], [0, zp, (C14_BASE[1] - 150) * (1 - zp)]])
        return cv2.warpAffine(img, M, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
    cp.post.append(push)
    cp.gain = tuple(g_ * (0.55 + 0.45 * max(L, dawn)) for g_ in cp.gain)
    cp.lift = tuple(l_ * (0.4 + 0.6 * max(L, dawn)) for l_ in cp.lift)
    cp.sat = lerp(0.55, 0.95, max(dawn, 0.3 * L))
    return cp

SHOTS = {1: (0, 7, c01), 3: (12, 17, c03), 9: (40, 48, c09), 14: (64, 76, c14)}
