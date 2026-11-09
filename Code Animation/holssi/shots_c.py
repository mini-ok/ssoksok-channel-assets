# -*- coding: utf-8 -*-
"""홀씨 -- group C: C10 (the storm wall), C11 (inside the storm), C12 (the ash plain), C13 (lying in the ash)."""
from shots_b import *

STORM_PAL = [(0.16, 0.15, 0.22), (0.27, 0.25, 0.35), (0.42, 0.37, 0.48), (0.86, 0.70, 0.60)]

# ================================================================== C10  the storm wall
C10W, C10H = 3600, 1500

def c10_storm(w, h, rng):
    circ = []
    # the tower: a column that widens into an anvil
    for _ in range(170):
        yv = rng.uniform(180, 1000)
        half = 260 + 380 * math.exp(-((yv - 260) / 160) ** 2) + 160 * (yv - 180) / 820
        x = 1950 + rng.uniform(-half, half) * 0.9
        r = rng.uniform(70, 200)
        circ.append((x, yv, r, 0.5 + 0.5 * r / 200))
    for _ in range(90):
        x = rng.uniform(900, w + 200); y = rng.uniform(720, 1000); r = rng.uniform(80, 220)
        circ.append((x, y, r, 0.45))
    for _ in range(60):
        x = rng.uniform(2600, w + 200); y = rng.uniform(400, 1000); r = rng.uniform(90, 240)
        circ.append((x, y, r, 0.45))
    hh, m = dome_field(w, h, circ, clip=flat_bottom_clip(-100, w + 100, lambda xx: 1010 + 20 * math.sin(xx * 0.01)))
    return celpaint_h(hh, m, STORM_PAL, light=(-0.75, -0.66), step=10, gain=4.0, cuts=(0.42, 0.58, 0.76), seed=101,
                      blotch=0.04, namp=0.015)

def c10_sea(w, h, rng):
    circ = []
    for _ in range(160):
        x = rng.uniform(-100, w + 100); y = rng.uniform(1040, h + 60); r = rng.uniform(40, 120)
        circ.append((x, y, r, 0.5 + 0.5 * r / 120))
    hh, m = dome_field(w, h, circ)
    return celpaint_h(hh, m, [(0.62, 0.52, 0.62), (0.84, 0.70, 0.66), (0.96, 0.82, 0.70), (1.0, 0.92, 0.78)],
                      light=(-0.7, -0.7), step=10, gain=4.0, seed=102)

def c10(t, fi):
    cp = Comp(); grade(cp, WARM_GRADE)
    u = lin(48.0, 52.0, t)
    dim = ease(u)
    z = 0.62 + 0.06 * ease(u)
    d = dyn(); c = d.c
    pat = cairo.LinearGradient(0, 0, W, H * 0.4)
    pat.add_color_stop_rgb(0, *lc((0.98, 0.82, 0.60), (0.70, 0.56, 0.50), dim))
    pat.add_color_stop_rgb(0.5, *lc((0.70, 0.62, 0.66), (0.42, 0.36, 0.44), dim))
    pat.add_color_stop_rgb(1, *lc((0.36, 0.32, 0.42), (0.22, 0.20, 0.28), dim))
    c.set_source(pat)
    c.paint()
    cp.add(d.rgba())
    st = StaticArr('c10_st', C10W, C10H, c10_storm)
    sea = StaticArr('c10_sea', C10W, C10H, c10_sea)
    cx, cy = 1500 + 40 * u, 700
    # lightning inside the wall
    fl = 0.0
    for t0 in (49.8, 51.25):
        a = t - t0
        if 0 <= a < 0.5:
            fl += math.exp(-a / 0.06) + 0.6 * math.exp(-((a - 0.15) / 0.04) ** 2)
    S = st.view(cx, cy, z)
    S[..., :3] *= F32(1.0 - 0.25 * dim)
    cp.add(S)
    if fl > 0:
        cp.glow(W / 2 + (1950 - cx) * z, H / 2 + (600 - cy) * z, 300, (0.85, 0.85, 1.0), 0.75 * min(1, fl))
    # rain curtains under the storm
    d = dyn(); c = d.c
    for k in range(22):
        x0 = W / 2 + (1600 + k * 40 - cx) * z + 20 * math.sin(k * 3.1)
        y0 = H / 2 + (990 - cy) * z
        pat = cairo.LinearGradient(0, y0, 0, y0 + 260)
        pat.add_color_stop_rgba(0, 0.32, 0.30, 0.40, 0.55)
        pat.add_color_stop_rgba(1, 0.32, 0.30, 0.40, 0.0)
        c.set_source(pat)
        poly(c, [(x0, y0), (x0 + 40, y0), (x0 + 10, y0 + 260), (x0 - 30, y0 + 260)])
        c.fill()
    cp.add(d.rgba(), blur=6)
    Sea = sea.view(cx, cy, z)
    Sea[..., :3] *= F32(1.0 - 0.35 * dim)
    cp.add(Sea, haze=((0.75, 0.62, 0.66), 0.15))
    # the seed, pulled toward the storm (shrinking, drifting right)
    d = dyn(); c = d.c
    sx = lerp(W * 0.36, W * 0.52, ease(u)) + 10 * nz(t, 4)
    sy = lerp(H * 0.48, H * 0.44, u)
    s = lerp(80, 46, ease(u))
    seed(c, sx, sy, s, rot=lerp(0.1, 0.5, u) + 0.12 * math.sin(t * 3), t=t, light=(1, 0.92, 0.78), rim=1.3)
    cp.add(d.rgba())
    cp.glow(0, 0, 900, (1.0, 0.85, 0.6), 0.45 * (1 - dim))
    cp.gain = tuple(g * (1 - 0.2 * dim) for g in cp.gain)
    cp.sat = lerp(0.94, 0.75, dim)
    return cp

# ================================================================== C11  inside the storm
def c11_bg(c, rng):
    vgrad(c, 0, 0, W, H, [(0, (0.20, 0.21, 0.28)), (1, (0.12, 0.13, 0.18))])
    for _ in range(30):
        radial(c, rng.uniform(0, W), rng.uniform(0, H), rng.uniform(150, 420),
               lc((0.30, 0.30, 0.40), (0.18, 0.18, 0.24), rng.random()), 0.7)

def c11(t, fi):
    cp = Comp()
    cp.lift, cp.gain, cp.sat, cp.contrast = (0.02, 0.022, 0.03), (0.95, 0.98, 1.05), 0.55, 1.0
    u = t - 52.0
    bg = Static('c11_bg', W, H, c11_bg)
    cp.add(bg.view(W / 2 + 35 * u, H / 2 - 20 * u, 1.35), blur=20)
    flash = 0.0
    for t0, a0 in ((52.0, 1.0), (55.15, 0.8)):
        a = t - t0
        if 0 <= a < 0.6:
            flash += a0 * (math.exp(-a / 0.07) + 0.5 * math.exp(-((a - 0.2) / 0.05) ** 2))
    # rain
    d = dyn(); c = d.c
    rng = np.random.default_rng(int(t * 24))
    for _ in range(420):
        x, y = rng.uniform(-100, W + 100), rng.uniform(-100, H + 100)
        L = rng.uniform(40, 110)
        c.move_to(x, y); c.line_to(x - L * 0.35, y + L)
    strokec(c, (0.72, 0.76, 0.86), 1.5, 0.35)
    cp.add(d.rgba())
    # the seed: soaking, hit, falling
    wet = sm(52.3, 55.0, t)
    hits = (53.0, 54.1)
    jolt = sum(28 * math.exp(-max(0, t - h) / 0.12) * (t >= h) for h in hits)
    fall = max(0.0, t - 55.0)
    sx = W * 0.5 + 18 * math.sin(u * 2.3) + 6 * nz(u * 3, 1)
    sy = H * 0.42 + jolt + 700 * fall ** 1.5 + 25 * u
    rot = 0.25 * math.sin(u * 1.7) + 0.6 * fall + sum(0.3 * math.exp(-max(0, t - h) / 0.2) * (t >= h) for h in hits)
    d = dyn(); c = d.c
    seed(c, sx, sy, 150, rot=rot, wet=wet, t=t, light=(0.82, 0.84, 0.90), rim=0.4, dew=0.0)
    # the big drops that strike it
    for h in hits:
        a = t - h
        if -0.25 < a < 0:
            yy = sy - 150 + a * 2600
            c.save(); c.translate(sx + 20, yy); c.scale(1, 1.4)
            c.arc(0, 0, 18, 0, TAU); c.restore()
            fillc(c, (0.80, 0.86, 0.95), 0.75)
        elif 0 <= a < 0.5:
            r_ = np.random.default_rng(int(h * 10))
            for k in range(16):
                ang = r_.uniform(-math.pi, 0)
                v = r_.uniform(200, 520)
                px = sx + 10 + math.cos(ang) * v * a
                py = sy - 120 + math.sin(ang) * v * a + 900 * a * a
                c.arc(px, py, r_.uniform(2, 5) * (1 - a * 1.6), 0, TAU)
                fillc(c, (0.85, 0.90, 0.98), 0.8 * (1 - a * 2))
    cp.add(d.rgba())
    # near drops (out of focus)
    d = dyn(); c = d.c
    r2 = np.random.default_rng(int(t * 24) + 7)
    for _ in range(14):
        c.arc(r2.uniform(0, W), r2.uniform(0, H), r2.uniform(10, 34), 0, TAU)
        fillc(c, (0.75, 0.80, 0.92), 0.25)
    cp.add(d.rgba(), blur=9)
    if flash > 0:
        cp.glow(W * 0.7, -100, 1200, (0.85, 0.88, 1.0), 0.75 * min(1, flash))
    return cp

def fr_dummy(c):
    return None

# ================================================================== C12  the ash plain (falling)
C12W, C12H = 2400, 1600
C12_HOR = 420

def c12_sky(c, rng):
    vgrad(c, 0, 0, C12W, C12_HOR + 20, [(0, (0.36, 0.38, 0.44)), (1, (0.62, 0.62, 0.64))])

def c12_clouds(w, h, rng):
    groups = []
    for (x, y, cw, ch) in ((300, 170, 700, 110), (1200, 120, 900, 130), (2000, 200, 700, 100), (800, 330, 800, 60),
                           (1700, 360, 700, 50)):
        groups.append((cloud_circles(rng, x, y, cw, ch), rect_clip(x - cw, x + cw, y, ch * 0.04, x)))
    hh, m = domes_union(w, h, groups)
    return celpaint_h(hh, m, [(0.30, 0.31, 0.36), (0.40, 0.41, 0.46), (0.52, 0.53, 0.57), (0.66, 0.66, 0.68)],
                      light=(-0.3, -0.95), step=9, gain=4.0, seed=121)

def c12_plain(w, h, rng):
    gh = h - C12_HOR
    # perspective noise: build tall, then squash rows toward the horizon
    tall = gh * 4
    n1 = fbm(w, tall, seed=31, octaves=6, base=5)
    n2 = fbm(w, tall, seed=32, octaves=4, base=3)
    ys = np.arange(gh, dtype=F32)
    v = (ys / gh) ** 1.8 * (tall - 1)
    mapy = np.tile(v[:, None], (1, w)).astype(F32)
    mapx = np.tile(np.arange(w, dtype=F32)[None, :], (gh, 1))
    p1 = cv2.remap(n1, mapx, mapy, cv2.INTER_LINEAR)
    p2 = cv2.remap(n2, mapx, mapy, cv2.INTER_LINEAR)
    m = np.zeros((h, w), F32); m[C12_HOR:] = 1
    ex = np.zeros((h, w), F32)
    yy = np.arange(h, dtype=F32)[:, None]
    far = np.clip(1 - (yy - C12_HOR) / 260, 0, 1)
    ex[C12_HOR:] = p1 * 0.05 + p2 * 0.05 - (ys[:, None] / gh) * 0.12
    arr = celpaint_h(m * 0.5, m, ASH_PAL, light=(0.4, -0.9), step=1, gain=0.0, seed=122, blotch=0.0, namp=0.0,
                     extra=ex * 1.6 + far * 0.22, cuts=(0.38, 0.50, 0.63), soft=0.05)
    cv = Canvas(w, h); c = cv.c
    # horizontal brush strokes, scaled with depth
    for _ in range(5000):
        y = C12_HOR + (rng.random() ** 1.6) * gh
        k = 0.1 + 1.5 * ((y - C12_HOR) / gh) ** 1.2
        x = rng.uniform(0, w)
        line(c, x - 14 * k, y, x + 14 * k, y, max(0.6, 2.2 * k), lc(ASH_D, (0.70, 0.69, 0.66), rng.random()),
             rng.uniform(0.06, 0.18))
    # charred stands
    for _ in range(60):
        gx = rng.uniform(0, w); gy = C12_HOR + 6 + (rng.random() ** 1.3) * (gh - 60)
        k = 0.12 + 1.6 * ((gy - C12_HOR) / gh) ** 1.3
        for j in range(rng.integers(5, 26)):
            x = gx + rng.normal(0, 60 * k); y = gy + rng.normal(0, 10 * k)
            ht = rng.uniform(30, 90) * k
            line(c, x, y, x + rng.uniform(-3, 3) * k, y - ht, max(0.8, 2.8 * k), (0.15, 0.14, 0.14), 0.95)
            if rng.random() < 0.5:
                by = y - ht * rng.uniform(0.5, 0.85)
                line(c, x, by, x + rng.uniform(-12, 12) * k, by - 8 * k, max(0.6, 1.4 * k), (0.15, 0.14, 0.14), 0.9)
    arr = over(arr, cv.rgba())
    hz = np.exp(-((yy - C12_HOR) / 120) ** 2) * 0.55
    arr[..., :3] = arr[..., :3] * (1 - hz[..., None]) + np.array((0.62, 0.62, 0.64), F32) * hz[..., None] * arr[..., 3:4]
    return arr

def c12(t, fi):
    cp = Comp()
    cp.lift, cp.gain, cp.sat, cp.contrast = (0.03, 0.03, 0.035), (0.98, 0.99, 1.02), 0.45, 0.95
    u = lin(56.0, 60.0, t)
    cx, cy = 1200, lerp(700, 860, ease(u))
    sky = Static('c12_sky', C12W, C12H, c12_sky)
    cl = StaticArr('c12_cl', C12W, C12H, c12_clouds)
    pl = StaticArr('c12_pl', C12W, C12H, c12_plain)
    cp.add(sky.view(cx, cy, 1.0))
    cp.add(cl.view(cx - 8 * (t - 56), cy, 1.0))
    cp.add(pl.view(cx, cy, 1.0))
    # drizzle
    d = dyn(); c = d.c
    rng = np.random.default_rng(int(t * 24))
    for _ in range(260):
        x, y = rng.uniform(0, W), rng.uniform(0, H)
        c.move_to(x, y); c.line_to(x - 6, y + 30)
    strokec(c, (0.82, 0.83, 0.86), 1.2, 0.25)
    # the falling seed: a small pale dot spiralling down
    sx = W * 0.5 + 40 * math.sin(u * 7) * (1 - u)
    sy = lerp(80, H * 0.80, ease(min(1, u * 1.05)))
    tiny_seed(c, sx, sy, lerp(26, 13, u), rot=u * 9, col=(0.95, 0.95, 0.93), a=1.0)
    cp.add(d.rgba())
    cp.glow(sx, sy, 40, (0.95, 0.95, 0.92), 0.35)
    return cp

# ================================================================== C13  lying in the ash
OLD = (C14_BASE[0] + 120, C14_BASE[1] - 18)

def c13(t, fi):
    cp = Comp()
    cp.lift, cp.gain, cp.sat, cp.contrast = (0.02, 0.022, 0.03), (0.90, 0.93, 0.98), 0.5, 0.98
    u = lin(60.0, 64.0, t)
    z = 1.75 + 0.15 * ease(u)
    fx, fy = OLD[0] - 20, OLD[1] - 30
    d = dyn(); c = d.c
    vgrad(c, 0, 0, W, H, [(0, (0.36, 0.38, 0.44)), (1, (0.56, 0.56, 0.58))])
    cp.add(d.rgba())
    far = Static('c14_far', W, H, c14_far)
    gr = StaticArr('c14_gr', W, H, c14_ground)
    f = far.view(fx, fy - 40, z * 0.6)
    f[..., :3] *= F32(0.7)
    cp.add(f, blur=14, haze=((0.5, 0.5, 0.54), 0.4))
    g = gr.view(fx, fy, z)
    g[..., :3] *= F32(0.62)
    cp.add(g)
    d = dyn(); c = d.c
    c.translate(W / 2 - fx * z, H / 2 - fy * z); c.scale(z, z)
    seed(c, OLD[0], OLD[1], 120, rot=1.42, wet=1.0, t=t, rim=0.0, light=(0.8, 0.8, 0.78))
    cp.add(d.rgba())
    # raindrops: streaks and splash crowns around it
    d = dyn(); c = d.c
    rng = np.random.default_rng(int(t * 24))
    for _ in range(90):
        x, y = rng.uniform(0, W), rng.uniform(0, H)
        c.move_to(x, y); c.line_to(x - 3, y + 46)
    strokec(c, (0.80, 0.82, 0.88), 1.6, 0.3)
    r2 = np.random.default_rng(13)
    for k in range(18):
        t0 = 60.0 + r2.uniform(0, 4.0)
        a = (t - t0)
        if 0 <= a < 0.35:
            x = r2.uniform(100, W - 100); y = r2.uniform(H * 0.62, H * 0.98)
            rr = 8 + 50 * a
            c.save(); c.translate(x, y); c.scale(1, 0.32)
            c.arc(0, 0, rr, 0, TAU); c.restore()
            strokec(c, (0.85, 0.88, 0.94), 2.2, 0.7 * (1 - a / 0.35))
            for j in range(6):
                ang = -math.pi * (0.15 + 0.7 * j / 5)
                c.arc(x + math.cos(ang) * rr, y + math.sin(ang) * rr * 0.9 - 60 * a, 2.5, 0, TAU)
                fillc(c, (0.85, 0.88, 0.94), 0.7 * (1 - a / 0.35))
        else:
            r2.uniform(100, W - 100); r2.uniform(H * 0.62, H * 0.98)
    cp.add(d.rgba())
    return cp
