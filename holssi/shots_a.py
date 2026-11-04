# -*- coding: utf-8 -*-
"""홀씨 -- group A: C2 (the last seed), C3/C4 (macro: ladybug, release), C5 (lift-off tracking)."""
from shots import *

# ================================================================== C2  among bare stems, one seed remains
def c2_stems(c, rng):
    """foreground bare stems + grass, painted on a W x H canvas (screen space)"""
    for _ in range(700):
        x = rng.uniform(-40, W + 40)
        blade(c, x, H + 10, rng.uniform(60, 260), rng.uniform(-40, 40), rng.uniform(2.5, 6),
              lc((0.18, 0.30, 0.22), (0.46, 0.56, 0.34), rng.random() ** 1.4), 0.95)
    for k in range(26):
        x = rng.uniform(40, W - 40)
        if abs(x - 1120) < 260:
            continue
        top = rng.uniform(260, 700)
        lean = rng.uniform(-40, 40)
        wd = rng.uniform(4, 8)
        pts = [(x + lean * (u / 10) ** 2, H + 20 - (H + 20 - top) * u / 10) for u in range(11)]
        stem(c, pts, wd, col=(0.40, 0.50, 0.30), ink=0.6)
        receptacle(c, pts[-1][0], pts[-1][1], wd * 2.4, rng)

def c02(t, fi):
    cp = Comp(); grade(cp, WARM_GRADE)
    z = 1.0 + 0.13 * ease(lin(7, 12, t))
    focus = (1070, 560)
    def V(st, s, cx, cy, **kw):
        # push-in about the focus point
        return st.view(cx + (focus[0] - W / 2) * (1 - 1 / z) / s, cy + (focus[1] - H / 2) * (1 - 1 / z) / s,
                       s * z, **kw)
    s_bg = 1.6
    cx, cy = 1000, 640 + 100 / s_bg
    sky = Static('c2_sky', C1W, C1H, c1_sky)
    cl = StaticArr('c2_cl', C1W, C1H, c1_clouds)
    sea = Static('c2_sea', C1W, C1H, c1_sea)
    md = StaticArr('c2_md', C1W, C1H, c1_meadow)
    cp.add(V(sky, s_bg, cx, cy), blur=6)
    cp.add(V(cl, s_bg, cx - 4 * t, cy), blur=8)
    cp.add(V(sea, s_bg, cx, cy), blur=7)
    cp.add(V(md, s_bg * 1.1, cx + 40, cy + 90), blur=5)
    st = Static('c2_st', W, H, c2_stems)
    cp.add(st.view(W / 2 + (focus[0] - W / 2) * (1 - 1 / z), H / 2 + (focus[1] - H / 2) * (1 - 1 / z), z,
                   sway=(t, 7, 250, H)), blur=3.0, haze=((0.98, 0.92, 0.80), 0.15))
    # the hero stem with the last seed
    d = dyn(); c = d.c
    c.translate(focus[0], focus[1]); c.scale(z, z); c.translate(-focus[0], -focus[1])
    sway = 7 * math.sin(t * 1.4) + 3 * math.sin(t * 2.9)
    tip = (1180 + sway, 760)
    pts = stem_path((1210, H + 30), tip, -26 + sway * 0.5)
    stem(c, pts, 10)
    receptacle(c, tip[0], tip[1], 26, np.random.default_rng(4))
    px, py = tip[0] - 110 + sway * 1.25, tip[1] - 175
    ang = math.atan2(tip[1] - 12 - py, tip[0] - 6 - px)
    seed(c, px, py, 112, rot=ang - math.pi / 2 + 0.03 * math.sin(t * 9), t=t, dew=0.7, achene=False,
         beak=math.hypot(tip[0] - 6 - px, tip[1] - 12 - py) / (1.25 * 112), light=(1, 0.93, 0.78), rim=1.4)
    cp.add(d.rgba())
    sx = focus[0] + (px - focus[0]) * z
    sy = focus[1] + (py - focus[1]) * z
    cp.glow(sx, sy, 170 * z, (1, 0.95, 0.82), 0.35)
    cp.glow(1650, 120, 600, (1.0, 0.9, 0.7), 0.35)
    return cp

# ================================================================== C3 / C4  macro: ladybug, wings, the gust
REC0 = (1180, 560)
PAP0 = (870, 290)

def macro_state(t):
    """continuous ladybug / stem / seed state across C3 (12-17) and C4 (17-20)"""
    u = kf(t, [(12.0, -0.15), (16.6, 0.80), (17.25, 0.98)])          # along the stem
    on_top = sm(17.1, 17.4, t)
    wings = sm(17.55, 17.9, t)
    fly = max(0.0, t - 17.95)
    load = max(0.0, min(1.0, u)) ** 2 * (1 - sm(17.95, 18.05, t))
    recoil = 32 * math.exp(-fly * 3.2) * math.sin(fly * 13) if t > 17.95 else 0.0
    gust = sm(18.35, 18.7, t)
    sway = 4 * math.sin(t * 1.3) + 26 * load + 3 * math.sin(t * 7) * load + recoil - 30 * gust
    release = max(0.0, t - 18.75)
    return dict(u=u, on_top=on_top, wings=wings, fly=fly, load=load, sway=sway, gust=gust, release=release)

def macro_draw(c, t, S, zoom=1.0, focus=REC0, lady_s=34):
    c.save()
    c.translate(focus[0], focus[1]); c.scale(zoom, zoom); c.translate(-focus[0], -focus[1])
    sway = S['sway']
    base = (1250, H + 40)
    tip = (REC0[0] + sway, REC0[1] + 6 * S['load'])
    pts = stem_path(base, tip, -40 + sway * 0.4)
    stem(c, pts, 15)
    receptacle(c, tip[0], tip[1], 46, np.random.default_rng(3))
    # seed: attached until release, then lifts away up-right
    tremble = (0.02 + 0.05 * S['load']) * math.sin(t * 13) + 0.01 * math.sin(t * 2.1) + 0.12 * S['gust'] * math.sin(t * 17)
    px, py = PAP0[0] + sway * 1.3, PAP0[1] + 4 * S['load']
    anchor = (tip[0] - 10, tip[1] - 30)
    ang = math.atan2(anchor[1] - py, anchor[0] - px)
    rot = ang - math.pi / 2 + tremble
    blen = math.hypot(anchor[0] - px, anchor[1] - py) / (1.25 * 250)
    r = S['release']
    if r > 0:
        px += 260 * r ** 1.6 + 60 * r
        py -= 420 * r ** 1.4
        rot += 0.9 * r
    seed(c, px, py, 250, rot=rot, t=t, dew=1.0 - 0.6 * min(1, r * 2), achene=r > 0, beak=blen if r <= 0 else 1.0,
         rim=1.0, light=(1, 0.93, 0.78))
    # ladybug
    u = S['u']
    if S['fly'] <= 0 and u > -0.1:
        if S['on_top'] < 0.01:
            k = int(max(0, min(23, u * 24)))
            (ax, ay), (bx, by) = pts[k], pts[min(24, k + 1)]
            fu = u * 24 - k
            lx, ly = lerp(ax, bx, fu) + 16, lerp(ay, by, fu)
            heading = math.atan2(by - ay, bx - ax) + math.pi / 2
        else:
            lx, ly = lerp(pts[-1][0] + 16, tip[0] + 20, S['on_top']), lerp(pts[-1][1], tip[1] - 34, S['on_top'])
            heading = lerp(0.0, 0.25, S['on_top'])
        ladybug(c, lx, ly, lady_s, ang=heading, t=t, wings=S['wings'], legs=1.0 - S['wings'])
    elif S['fly'] > 0:
        f = S['fly']
        lx = tip[0] + 20 - 520 * f - 60 * math.sin(f * 9)
        ly = tip[1] - 34 - 640 * f ** 1.2
        ladybug(c, lx, ly, lady_s * (1 + 0.4 * f), ang=-0.6 + 0.2 * math.sin(f * 30), t=t,
                wings=1.0 + 0.0 * math.sin(f * 80), legs=0.0)
        # wing blur halo
        for sg in (-1, 1):
            c.save(); c.translate(lx + sg * lady_s * 1.1, ly + lady_s * 0.2); c.scale(1, 0.5)
            c.arc(0, 0, lady_s * 1.5, 0, TAU); c.restore()
            fillc(c, (0.9, 0.95, 0.95), 0.18)
    c.restore()

def macro_bg(cp, t, zoom=1.0, gust=0.0):
    bg = Static('c3_bg', W, H, c3_bg)
    mid = Static('c3_mid', W, H, c3_mid)
    drift = 6 * nz(t * 0.4, 1) - 40 * gust
    cp.add(bg.view(W / 2 + drift * 0.3, H / 2, zoom ** 0.3), blur=26)
    cp.add(mid.view(W / 2 + drift * 0.6, H / 2, zoom ** 0.5, sway=(t, 10 + 60 * gust, 0, H)), blur=10,
           haze=((0.95, 0.90, 0.75), 0.25))

def c03(t, fi):
    cp = Comp(); grade(cp, WARM_GRADE)
    S = macro_state(t)
    macro_bg(cp, t)
    d = dyn()
    macro_draw(d.c, t, S)
    cp.add(d.rgba(), tx='d', tamp=0.04)
    d = dyn(); c = d.c
    c.move_to(-40, H + 40)
    c.curve_to(200, 700, 380, 520, 520, 380)
    strokec(c, (0.16, 0.28, 0.20), 60, 1)
    cp.add(d.rgba(), blur=18)
    cp.glow(1720, 110, 650, (1.0, 0.90, 0.68), 0.55)
    return cp

def c04(t, fi):
    """cut-in: closer on the receptacle; the ladybug opens its wings and flies; the gust takes the seed"""
    cp = Comp(); grade(cp, WARM_GRADE)
    S = macro_state(t)
    z = 1.45
    macro_bg(cp, t, zoom=z, gust=S['gust'])
    d = dyn()
    d.c.translate(W / 2 - REC0[0] + 40, H / 2 - REC0[1] + 140)
    macro_draw(d.c, t, S, zoom=z, focus=REC0, lady_s=40)
    cp.add(d.rgba(), tx='d', tamp=0.04)
    # pollen motes swept by the gust
    if S['gust'] > 0:
        d = dyn(); c = d.c
        rng = np.random.default_rng(44)
        n = 60
        bx = rng.uniform(-200, W, n); by = rng.uniform(0, H, n)
        g = (t - 18.35)
        for i in range(n):
            x = bx[i] + 900 * g * (0.6 + 0.4 * rng.random())
            y = by[i] - 120 * g + 20 * math.sin(g * 5 + i)
            c.arc(x, y, rng.uniform(1.5, 3.5), 0, TAU)
            fillc(c, (1, 0.96, 0.82), 0.7 * S['gust'])
        cp.add(d.rgba(), blur=1.5)
    cp.glow(1720, 110, 650, (1.0, 0.90, 0.68), 0.55)
    return cp

# ================================================================== C5  lift-off: tracking with the seed over the meadow
C5W, C5H = 6000, 1600

def c5_mid(c, rng):
    """grass tips and wildflowers in a long strip (bottom part of a tall canvas)"""
    top = 900
    for _ in range(9000):
        x = rng.uniform(0, C5W)
        y = rng.uniform(top, C5H)
        k = 0.6 + (y - top) / 700
        blade(c, x, y + 30, rng.uniform(20, 70) * k, rng.uniform(-14, 14), rng.uniform(1.5, 3.2) * k,
              lc((0.30, 0.44, 0.28), (0.78, 0.78, 0.50), rng.random() ** 1.4), 0.9)
    for _ in range(900):
        x = rng.uniform(0, C5W); y = rng.uniform(top - 30, C5H - 100)
        k = 0.6 + (y - top) / 700
        r = rng.uniform(4, 8) * k
        col = (1, 0.97, 0.88) if rng.random() < 0.65 else ((0.84, 0.76, 0.96) if rng.random() < 0.6 else YEL)
        for p in range(6):
            a = p * TAU / 6 + rng.uniform(0, 0.4)
            c.save(); c.translate(x + math.cos(a) * r * 0.7, y + math.sin(a) * r * 0.7); c.rotate(a)
            c.scale(1, 0.5); c.arc(0, 0, r * 0.6, 0, TAU); c.restore()
            fillc(c, col, 0.95)
        c.arc(x, y, r * 0.35, 0, TAU)
        fillc(c, (0.98, 0.78, 0.25))
    for _ in range(60):
        x = rng.uniform(0, C5W); y = rng.uniform(top + 20, C5H - 40)
        k = 0.6 + (y - top) / 700
        hgt = rng.uniform(80, 160) * k
        pts = [(x + 6 * (u / 6) ** 2, y - hgt * u / 6) for u in range(7)]
        stem(c, pts, 3 * k, col=(0.36, 0.46, 0.27), ink=0.5)
        receptacle(c, pts[-1][0], pts[-1][1], 6 * k, rng)

def c5_near(c, rng):
    for _ in range(260):
        x = rng.uniform(0, C5W)
        blade(c, x, C5H + 20, rng.uniform(120, 560) * (1 if rng.random() < 0.7 else 0.4), rng.uniform(-160, 160),
              rng.uniform(6, 18), lc(TEAL_D, (0.30, 0.42, 0.28), rng.random()), 0.95)

def c05(t, fi):
    cp = Comp(); grade(cp, WARM_GRADE)
    u = t - 20.0
    rise = 640 * ease(lin(20.0, 23.2, t)) + 40 * u
    d = dyn(); c = d.c
    vgrad(c, 0, 0, W, H, [(0, (0.56, 0.69, 0.79)), (0.55, (0.86, 0.86, 0.80)), (1, (0.99, 0.87, 0.68))])
    cp.add(d.rgba())
    cl = StaticArr('c5_cl', C1W, C1H, c1_clouds)
    cp.add(cl.view(1150 + 25 * u, 600 + rise * 0.15, 1.1), blur=1.0)
    sea = Static('c5_sea', C1W, C1H, c1_sea)
    cp.add(sea.view(1000 + 30 * u, 520 + rise * 0.25, 1.2), blur=2.5)
    mid = Static('c5_mid', C5W, C5H, c5_mid)
    cp.add(mid.view(1200 + 260 * u, 900 - rise * 0.9 + 60, 1.0, sway=(t, 10, 0, H)), blur=1.2)
    # the seed
    d = dyn(); c = d.c
    sx = W * 0.42 + 60 * math.sin(u * 0.5) + 12 * nz(u * 1.3, 2)
    sy = H * 0.52 - 20 * math.sin(u * 0.8)
    seed(c, sx, sy, 100, rot=0.16 * math.sin(u * 0.9) + 0.06 * nz(u * 2.3, 1), t=t, light=(1, 0.94, 0.80), rim=1.4)
    cp.add(d.rgba())
    near = Static('c5_near', C5W, C5H, c5_near)
    cp.add(near.view(1000 + 700 * u, C5H - 380 - rise * 1.6 + 100, 1.0, sway=(t, 18, 0, H)), blur=14)
    cp.glow(1700, 80, 700, (1.0, 0.9, 0.7), 0.45)
    cp.glow(sx, sy, 90, (1, 0.96, 0.85), 0.25)
    return cp
