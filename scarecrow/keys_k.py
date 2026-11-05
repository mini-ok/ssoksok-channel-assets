# -*- coding: utf-8 -*-
import sys, math
import numpy as np
from bg import *
from cel import *
from PIL import Image

def world_ctx(c, cx, cy, z):
    c.translate(W / 2 - cx * z, H / 2 - cy * z)
    c.scale(z, z)

def snow_fx(c, t, n, ang, speed, size, alpha, seed=1, big=0):
    """drawn snow streaks, refreshed on twos"""
    tq = twos(t)
    rng = np.random.default_rng(seed)
    x0 = rng.uniform(-300, W + 300, n); y0 = rng.uniform(-200, H + 200, n); d = rng.uniform(0.4, 1.0, n)
    dx, dy = math.cos(ang), math.sin(ang)
    B = Boil(t, amp=0.8, salt=seed)
    for i in range(n):
        x = (x0[i] + dx * speed * d[i] * tq) % (W + 600) - 300
        y = (y0[i] + dy * speed * d[i] * tq) % (H + 400) - 200
        L_ = size * d[i] * (2.5 + 2 * rng.random())
        pts = B.jp([(x, y), (x + dx * L_ * 0.5, y + dy * L_ * 0.5 - 2), (x + dx * L_, y + dy * L_)], 0.5)
        inkline(c, pts, 1.2 + 2.5 * d[i] * size / 10, (0.90, 0.92, 1.0), alpha * (0.5 + 0.5 * d[i]))
    for i in range(big):
        x = rng.uniform(0, W); y = rng.uniform(0, H)
        x = (x + dx * speed * 0.4 * tq) % W; y = (y + dy * speed * 0.4 * tq) % H
        r = rng.uniform(5, 12)
        smooth_path(c, B.jp([(x - r, y), (x - r * 0.3, y - r * 0.8), (x + r * 0.6, y - r * 0.5), (x + r, y + r * 0.2),
                             (x + r * 0.2, y + r * 0.8), (x - r * 0.7, y + r * 0.5)], 0.6))
        fillc(c, (0.92, 0.94, 1.0), alpha)

def spindrift(c, t, ybase, alpha):
    B = Boil(t, amp=3, salt=77)
    tq = twos(t)
    for k in range(4):
        y = ybase + k * 60
        off = (tq * 900 + k * 400) % (W + 1200) - 600
        pts = B.jp([(off - 600, y + 40), (off - 200, y - 20), (off + 300, y + 10), (off + 700, y - 30)], 1.0)
        top = pts
        bot = [(x, y_ + 70 + 20 * k) for (x, y_) in pts[::-1]]
        smooth_path(c, top + bot)
        fillc(c, (0.80, 0.84, 0.98), alpha * (0.5 - k * 0.1))

def wind_marks(c, t, alpha=0.8):
    B = Boil(t, amp=1.2, salt=55)
    tq = twos(t)
    rng = np.random.default_rng(5)
    for k in range(9):
        x = (rng.uniform(-400, W) + tq * 1600) % (W + 800) - 400
        y = rng.uniform(80, H * 0.75)
        L_ = rng.uniform(220, 420)
        pts = B.jp(qcurve((x, y), (x + L_ * 0.5, y - 40 - rng.uniform(0, 40)), (x + L_, y - 10), 10), 0.6)
        inkline(c, pts, 4.5, (1, 1, 1), alpha * 0.85)

def flock(c, t, cx, cy, n=6, spread=260, s=10, seed=3):
    rng = np.random.default_rng(seed)
    tq = twos(t)
    for k in range(n):
        a = rng.uniform(0, TAU) + tq * rng.uniform(1, 2)
        x = cx + math.cos(a) * spread * rng.uniform(0.4, 1); y = cy + math.sin(a) * spread * 0.4 * rng.uniform(0.4, 1)
        f = math.sin(tq * 30 + k * 1.7)
        d_ = 1 if math.cos(a) < 0 else -1
        B = Boil(t, salt=k)
        def body(cc, x=x, y=y):
            smooth_path(cc, B.jp([(x - s * 1.2 * d_, y), (x, y - s * 0.45), (x + s * 1.3 * d_, y - s * 0.1),
                                  (x + s * 0.2 * d_, y + s * 0.45)], 0.3))
        cel(c, body, KO_F['back'], KO_F['back_s'], (-0.5, -0.8), off=1.5, lw=1.6)
        for sg in (-1, 1):
            tip = (x - s * 0.4 * d_, y - sg * s * (0.6 + 1.4 * abs(f)))
            def wing(cc, tip=tip, sg=sg):
                poly(cc, B.jp([(x + s * 0.3 * d_, y), tip, (x - s * 0.6 * d_, y - sg * s * 0.2)], 0.2))
            cel(c, wing, KO_F['wing'], KO_F['wing_s'], (-0.5, -0.8), off=1, lw=1.4)

KO_F = dict(KO, back=(0.52, 0.38, 0.27), back_s=(0.40, 0.29, 0.20))

def frame(key, cam, chars, fx_pre=None, fx_post=None, t=0.0, tintc=None, blur_bg=0.0, grade=None, ccam=None):
    set_frame(t)
    Ls = season_layers(key)
    S = Ls['S']
    cx, cy, z = cam
    cp = Comp()
    if grade:
        cp.lift, cp.gain, cp.sat, cp.contrast = grade
    else:
        cp.lift, cp.gain, cp.sat, cp.contrast = (0.0, 0.0, 0.0), (1.0, 1.0, 1.0), 1.0, 1.0
    cp.vig = 0.32
    cp.add(Painted(key).view(cx, cy, z), blur=blur_bg)
    if fx_pre:
        d = dyn(); fx_pre(d.c); cp.add(d.rgba())
    d = dyn(); c = d.c
    ccx, ccy, cz = ccam or cam
    c.save(); world_ctx(c, ccx, ccy, cz); chars(c, S); c.restore()
    cl = cel_finish(d.rgba(), t)
    if tintc is not None:
        cl[..., :3] = cl[..., :3] * np.array(tintc, F32)
    cp.add(cl)
    if fx_post:
        d = dyn(); fx_post(d.c); cp.add(d.rgba())
    cp.add(Ls['fore'].view(cx, cy, z * 1.05), blur=4)
    cp.post.append(lambda img: film_post(img, t))
    return cp

def rice_clump(c, x, y, s, pal, t, n=60, wind=0.0, w=150):
    B = Boil(t, amp=0.4, salt=21)
    rng = np.random.default_rng(int(x) + 3)
    for k in range(n):
        bx = x + rng.uniform(-w, w) * s
        L_ = rng.uniform(25, 90) * s
        sway = wind * 12 * s * (0.5 + 0.5 * math.sin(twos(t) * 6 + k))
        pts = B.jp(qcurve((bx, y + 20 * s), (bx + sway * 0.3 + rng.uniform(-6, 6) * s, y - L_ * 0.6),
                          (bx + sway + L_ * 0.3, y - L_ * 0.75)), 0.3)
        inkline(c, pts, 4.0 * s, pal[0], 0.95)
        inkline(c, pts, 2.2 * s, pal[2 + (k % 2)], 0.95)

def K1(t=4.0):
    pal = tint_pal(JI, mix=(1.0, 0.80, 0.66), k=0.12)
    def chars(c, S):
        jx, jy = JI_POS
        o = jiibi(c, jx, jy, 1.3, dict(flapL=-0.1, flapR=0.0, wind=0.25), t=t, L=S['L'], pal=pal)
        rice_clump(c, jx, jy - 40, 1.2, S['rice'], t, n=70, wind=0.3)
        hx, hy = c.device_to_user(*o['hat'])
        kongi(c, hx + 4, hy - 27, 11, dict(blink=1, puff=1.2), t=t, L=S['L'])
        for k, (dx, dy, a) in enumerate(((-260, -200, 0.3), (-420, -120, -0.2), (200, -260, 0.1), (380, -150, 2.9), (-80, -330, 0.7),
                                         (520, -300, 3.3), (-600, -60, 0.2))):
            dragonfly(c, jx + dx + 20 * math.sin(t * 3 + k), jy + dy - 60 + 10 * math.cos(t * 4 + k), 15, a, t)
    def fxp(c):
        flock(c, t, 700, 360, n=7, spread=300, s=7)
    return frame('dawn', (1260, 690, 0.86), chars, fx_post=fxp, t=t, grade=((0.03, 0.02, 0.03), (1.02, 0.99, 0.95), 1.02, 0.97))

def K2(t=33.0):
    def chars(c, S):
        jx, jy = JI_POS
        o = jiibi(c, jx, jy, 1.0, dict(flapL=0.95, flapR=1.0, wind=1.0, billow=1.0, lean=4, head_tilt=6, hat_tilt=10), t=t,
                  L=S['L'])
        hx, hy = c.device_to_user(*o['hat'])
        kongi(c, hx + 44, hy - 4, 11, dict(wing=1.0, open_beak=1.0, tilt=28, puff=1.3, face=-1), t=t, L=S['L'])
        rice_clump(c, jx, jy - 60, 0.9, S['rice'], t, n=46, wind=1.0, w=300)
        hawk(c, jx - 230, jy - 420, 36, heading=-2.4, flap=0.4, L=S['L'])
    def fxp(c):
        wind_marks(c, t)
        B = Boil(t, salt=4)
        for (x, y, a) in ((300, 700, 0.4), (1400, 300, 1.2), (1700, 760, 2.0), (520, 260, 2.6)):
            def lf(cc, x=x, y=y, a=a):
                cc.save(); cc.translate(x, y); cc.rotate(a)
                smooth_path(cc, B.jp([(0, 10), (-9, 0), (-5, -4), (0, -14), (5, -4), (9, 0)], 0.4)); cc.restore()
            cel(c, lf, (0.92, 0.48, 0.16), (0.70, 0.28, 0.10), (-0.5, -0.86), off=3, lw=2)
    return frame('noon', (1350, 470, 1.25), chars, fx_post=fxp, t=t, blur_bg=1.4, ccam=(1440, 820, 1.9),
                 grade=((0.02, 0.02, 0.03), (1.02, 1.0, 0.98), 1.05, 1.0))

def K3(t=86.0):
    pal = tint_pal(JI, mul=(0.62, 0.66, 0.92), add=(0.02, 0.02, 0.06))
    kpal = tint_pal(KO, mul=(0.70, 0.72, 0.95), add=(0.02, 0.02, 0.05))
    def fxpre(c):
        spindrift(c, t, 560, 0.55)
    def chars(c, S):
        jx, jy = JI_POS
        def nestling(cc):
            kongi(cc, -2, -199, 11, dict(puff=1.45, blink=0.0, tilt=-16, feet=0), t=t, L=(-0.9, -0.44), pal=kpal)
        B0 = Boil(t, salt=41)
        def drift(cc):
            smooth_path(cc, B0.jp([(jx - 110, jy + 22), (jx - 70, jy + 2), (jx - 20, jy - 14), (jx + 30, jy - 8),
                                   (jx + 90, jy + 6), (jx + 150, jy + 22)], 1.0))
        o = jiibi(c, jx, jy, 1.0, dict(wrapL=1.0, bend=-30, lean=-6, head_tilt=-30, head_turn=-0.35, snow=1.0, frost=0.8,
                                     flapR=-0.75, wind=1.0, hat_tilt=-8, goreum_wind=1.0), t=t, L=(-0.9, -0.44), pal=pal,
                  chest_fn=nestling)
        cel(c, drift, (0.60, 0.62, 0.84), (0.36, 0.38, 0.62), (-0.9, -0.44), off=8, lw=2.4)
        for q in range(6):
            inkline(c, qcurve((jx - 80 + q * 34, jy + 4), (jx - 64 + q * 34, jy - 2), (jx - 46 + q * 34, jy + 6), 6), 2.0,
                    (0.80, 0.82, 0.98), 0.7)
    def fxp(c):
        snow_fx(c, t, 900, 0.20, 1900, 14, 0.8, seed=2, big=40)
    cp = frame('blizzard', (1250, 500, 1.15), chars, fx_pre=fxpre, fx_post=fxp, t=t, blur_bg=1.0, ccam=(1400, 860, 2.0),
               grade=((0.015, 0.015, 0.04), (0.74, 0.80, 1.0), 0.85, 1.05))
    cp.vig = 0.55
    return cp

def K4(t=121.0):
    def chars(c, S):
        jx, jy = JI_POS
        # fallen scarecrow lying in the grass, sprouts through the straw
        B0 = Boil(0, salt=31)
        def mound(cc):
            smooth_path(cc, B0.jp([(jx - 900, jy + 300), (jx - 900, jy + 30), (jx - 500, jy - 20), (jx, jy - 30),
                                   (jx + 500, jy - 10), (jx + 900, jy + 30), (jx + 900, jy + 300)], 1.0))
        cel(c, mound, (0.50, 0.70, 0.34), (0.36, 0.54, 0.26), S['L'], off=16, lw=3)
        rng = np.random.default_rng(4)
        for _ in range(420):
            x = rng.uniform(jx - 880, jx + 880); y = rng.uniform(jy - 24, jy + 260)
            inkline(c, [(x, y), (x + rng.uniform(-4, 4), y - rng.uniform(8, 20))], 2.4, lc((0.40, 0.62, 0.28), (0.70, 0.84, 0.42),
                    rng.random()), 0.9, taper=False)
        for _ in range(60):
            x = rng.uniform(jx - 860, jx + 860); y = rng.uniform(jy - 10, jy + 240)
            c.arc(x, y, rng.uniform(4, 8), 0, TAU)
            fillc(c, (0.99, 0.86, 0.18) if rng.random() < 0.6 else (1, 0.98, 0.94))
        jiibi(c, jx - 180, jy - 10, 1.0, dict(topple=1.0, hat_on=0.0, flapL=-0.2, flapR=-0.2, arm_len=0.45, wind=0.4, pocket=3,
                                            head_tilt=6), t=t, L=S['L'])
        B = Boil(t, salt=8)
        for k in range(16):
            x = jx - 260 + k * 22 + 6 * math.sin(k * 3)
            h_ = 18 + 22 * math.sin(k * 1.7) ** 2
            inkline(c, B.jp(qcurve((x, jy - 4), (x + 3, jy - h_ * 0.6), (x + 6, jy - h_)), 0.3), 4, (0.36, 0.62, 0.26), 1.0)
        # persimmon sapling from the pocket
        px, py = jx - 30, jy - 40
        inkline(c, B.jp(qcurve((px, py), (px + 4, py - 30), (px + 2, py - 60)), 0.3), 4, (0.42, 0.30, 0.20), 1.0)
        for (dx, dy, a) in ((-12, -58, -0.6), (12, -62, 0.5), (0, -70, 0.0)):
            def lf(cc, dx=dx, dy=dy, a=a):
                cc.save(); cc.translate(px + dx, py + dy); cc.rotate(a)
                smooth_path(cc, [(0, 6), (-7, -2), (0, -14), (7, -2)]); cc.restore()
            cel(c, lf, (0.52, 0.76, 0.32), (0.34, 0.56, 0.22), S['L'], off=2, lw=1.8)
        # the hat on the ground with the nest, Kongi and her mate
        hx, hy = jx + 170, jy - 6
        c.save(); c.translate(hx, hy)
        def brim(cc):
            cc.save(); cc.scale(1, 0.3); cc.arc(0, 0, 60, 0, TAU); cc.restore()
        cel(c, brim, JI['hat'], JI['hat_s'], S['L'], off=4, lw=2.6)
        def crown(cc):
            smooth_path(cc, [(-32, 0), (-31, -16), (-20, -28), (0, -31), (20, -28), (31, -16), (32, 0), (16, 6), (-16, 6)])
        cel(c, crown, JI['hat'], JI['hat_s'], S['L'], off=6, lw=2.6)
        def nest(cc):
            smooth_path(cc, [(-30, -26), (-14, -34), (14, -34), (30, -26), (20, -16), (-20, -16)])
        cel(c, nest, (0.66, 0.52, 0.32), (0.46, 0.34, 0.20), S['L'], off=4, lw=2.2)
        for k in range(10):
            inkline(c, [(-28 + k * 6, -30), (-22 + k * 6, -20)], 1.5, (0.40, 0.30, 0.18), 0.8, taper=False)
        c.restore()
        for k, dx in enumerate((-12, 0, 12)):
            kongi(c, hx + dx, hy - 36, 5, dict(open_beak=1.0 if k != 1 else 0.3, puff=1.2, feet=0, tilt=-20 + k * 14), t=t,
                  L=S['L'])
        kongi(c, hx - 46, hy - 40, 10, dict(face=1, tilt=10), t=t, L=S['L'])
        kongi(c, hx + 46, hy - 42, 10, dict(face=-1, tilt=-6), t=t, L=S['L'], pal=KO_F)
    def fxp(c):
        B = Boil(t, salt=12)
        rng = np.random.default_rng(9)
        for k in range(30):
            x = (rng.uniform(0, W) + twos(t) * 120) % W; y = rng.uniform(0, H * 0.8)
            def petal(cc, x=x, y=y, a=rng.uniform(0, 3)):
                cc.save(); cc.translate(x, y); cc.rotate(a); cc.scale(1, 0.55); cc.arc(0, 0, 6, 0, TAU); cc.restore()
            cel(c, petal, (1.0, 0.80, 0.86), (0.90, 0.58, 0.70), (-0.6, -0.8), off=1.5, lw=0)
    return frame('spring', (1250, 620, 0.95), chars, fx_post=fxp, t=t, blur_bg=1.2, ccam=(1440, 930, 1.55),
                 grade=((0.02, 0.02, 0.02), (1.02, 1.0, 0.97), 1.04, 0.98))

if __name__ == '__main__':
    for name in sys.argv[1:]:
        cp = globals()[name]()
        Image.fromarray(cp.finish(1)).save(f'test/{name}.png')
        print(name, flush=True)
