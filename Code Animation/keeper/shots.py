# -*- coding: utf-8 -*-
"""빛지기 (THE KEEPER) -- 18 cuts, 60 seconds."""
from engine import *
from engine import _apply_lights
import math
import numpy as np

# ------------------------------------------------------------------ global timeline
LIGHTNING = [(2.6, 0.35), (11.6, 1.0), (14.4, 0.85), (18.7, 0.5), (27.5, 0.9), (37.7, 0.45), (43.3, 0.3)]

def lflash(t):
    return lightning_amp(t, LIGHTNING)

def storm(t):
    return (0.45 + 0.55 * sm(1, 12, t)) * (1 - sm(44.5, 45.0, t))

def kf(t, keys):
    if t <= keys[0][0]:
        return keys[0][1]
    for (ta, va), (tb, vb) in zip(keys[:-1], keys[1:]):
        if t <= tb:
            u = ease_io((t - ta) / (tb - ta)) if tb > ta else 1.0
            if isinstance(va, tuple):
                return tuple(a + (b - a) * u for a, b in zip(va, vb))
            return va + (vb - va) * u
    return keys[-1][1]

def night(fr):
    fr.lift = (0.006, 0.009, 0.020)
    fr.gain = (0.93, 0.98, 1.08)
    fr.sat = 0.92

def dawn_grade(fr):
    fr.lift = (0.016, 0.010, 0.012)
    fr.gain = (1.04, 0.99, 0.94)
    fr.sat = 1.02

def darken(fr, a):
    c = fr.c
    c.save()
    c.identity_matrix()
    c.set_source_rgba(0, 0, 0, a)
    c.paint()
    c.restore()

NIGHT_SKY = [(0, (0.025, 0.03, 0.055)), (0.6, (0.06, 0.075, 0.125)), (1, (0.10, 0.12, 0.19))]
DAWN_SKY = [(0, (0.25, 0.27, 0.50)), (0.42, (0.72, 0.49, 0.62)), (0.78, (0.99, 0.72, 0.56)), (1, (1.0, 0.87, 0.66))]
CLOUD_D = (0.035, 0.04, 0.065)
CLOUD_L = (0.10, 0.11, 0.17)

SEA_ELS = Sea(520, 804, far=(0.075, 0.09, 0.145), near=(0.014, 0.018, 0.034), n=11, amp=12, speed=1.3, seed=3,
              foam_a=0.32)
SEA_DAWN = Sea(520, 804, far=(0.74, 0.55, 0.60), near=(0.22, 0.17, 0.30), n=8, amp=3.5, speed=0.6, seed=3,
               foam=(1.0, 0.88, 0.78), foam_a=0.35, choppy=0.2)
SEA_BOAT = Sea(430, 804, far=(0.06, 0.075, 0.12), near=(0.01, 0.014, 0.025), n=7, amp=52, speed=1.5, seed=8,
               foam_a=0.45, choppy=1.0, wl=2.4)
SEA_C4 = Sea(470, 804, far=(0.07, 0.085, 0.13), near=(0.015, 0.02, 0.035), n=9, amp=8, speed=1.4, seed=5,
             foam_a=0.38)
SEA_POV = Sea(270, 900, far=(0.12, 0.14, 0.21), near=(0.05, 0.06, 0.095), n=7, amp=26, speed=1.5, seed=11,
              foam=(0.75, 0.80, 0.90), foam_a=0.6, choppy=0.9, wl=1.6)

LH_X, LH_GY, LH_H = 1330, 600, 380
LEDGE_Y = 580
ROBOT_HIP = 41      # leg length in robot units (hip above ground)

def lamp_level(t):
    I = sm(0, 0.5, t)
    if t < 2.75:
        return I
    if t > 3.95:
        return 0.0
    k = int((t - 2.75) * 14)
    pat = [1, 0.2, 1, 1, 0, 0.6, 0, 0, 1, 0.1, 0, 0, 0.5, 0, 0, 0, 0.3]
    return pat[min(k, len(pat) - 1)] * (1 - lin(2.75, 3.95, t) * 0.5)

def rocks(fr, base, teeth, col, rim=None):
    c = fr.c
    for (x, w, h, sk) in teeth:
        pts = [(x - w / 2, base + 60), (x - w * 0.42, base - h * 0.35), (x - w * 0.22 + sk, base - h),
               (x - w * 0.02, base - h * 0.72), (x + w * 0.16 + sk * 0.5, base - h * 0.9),
               (x + w * 0.36, base - h * 0.3), (x + w / 2, base + 60)]
        poly(c, pts)
        fillc(c, col)
        if rim is not None:
            rc, ra = rim
            poly(c, pts[1:4], close=False)
            strokec(c, rc, 3, ra)

def tiny_tower(fr, x, base, h, col, dot=0.0, lamp=0.0):
    c = fr.c
    poly(c, [(x - h * 0.09, base), (x - h * 0.06, base - h * 0.78), (x + h * 0.06, base - h * 0.78),
             (x + h * 0.09, base)])
    fillc(c, col)
    rrect(c, x - h * 0.07, base - h * 0.92, h * 0.14, h * 0.14, 2)
    fillc(c, col)
    poly(c, [(x - h * 0.3, base + 4), (x - h * 0.1, base - h * 0.06), (x + h * 0.12, base - h * 0.05),
             (x + h * 0.32, base + 4)])
    fillc(c, col)
    if dot > 0:
        fr.blob(x, base - h * 0.86, 2.0, AMBER, 1.6 * dot)
        fr.blob(x, base - h * 0.86, 9, AMBER, 0.25 * dot)
    if lamp > 0:
        fr.blob(x, base - h * 0.86, 4, AMBER_L, 2.5 * lamp)

def blink(t, spans):
    for a, b in spans:
        if a <= t < b:
            return min(1.0, (t - a) / 0.03) * min(1.0, (b - t) / 0.03)
    return 0.0

# ------------------------------------------------------------------ C1  night, the light dies
def c01(t):
    fr = Frame(t); night(fr); fr.camera(W / 2, H / 2)
    fl = lflash(t)
    sky(fr, NIGHT_SKY, y0=-60, y1=530)
    clouds(fr, t, -500, W + 500, -60, 250, 70, 90, 230, CLOUD_D, CLOUD_L, seed=4, lit=fl * 0.6, drift=14)
    if fl > 0.02:
        bolt(fr, 300, 40, 360, 330, seed=2, I=fl * 0.8, width=0.7)
    SEA_ELS.draw(fr, t, 0, 6, lit=fl * 0.1)
    I = lamp_level(t)
    lamp_c, base = lighthouse(fr, LH_X, LH_GY, LH_H, t, lamp=I * 0.9, dot=sm(3.95, 4.5, t) * 0.9, lit=fl * 0.3)
    lh_beam(fr, lamp_c[0], lamp_c[1], 1.8 * t + 0.6, I * 0.9, L=1500)
    SEA_ELS.draw(fr, t, 6, None, lit=fl * 0.1)
    spray(fr, 985, 712, t, 1.2, 30, seed=3, spread=120, up=170, life=1.4, size=2.2, col=(0.42, 0.48, 0.58), alpha=0.6)
    spray(fr, 1640, 716, t, 3.3, 30, seed=6, spread=120, up=150, life=1.4, size=2.2, col=(0.42, 0.48, 0.58), alpha=0.6)
    rain(fr, t, int(900 * storm(t)), seed=7, alpha=0.12, length=30, speed=1300, ang=0.22)
    fr.flash = 0.12 * fl
    return fr

# ------------------------------------------------------------------ C2  the bulb bursts
C2_TAPS = [5.75, 6.45, 7.1]
C2_POP = 7.45

def c02(t):
    fr = Frame(t); night(fr)
    fr.camera(1300, 335, 1.42 + 0.05 * lin(5, 9, t))
    fl = lflash(t)
    if t < C2_POP:
        b = 0.75 + 0.15 * math.sin(t * 23) * math.sin(t * 7)
        for tp in C2_TAPS:
            d = t - tp
            if 0 <= d < 0.35:
                b *= 0.12 if int(d * 30) % 2 == 0 else 1.0
        broken = False
    else:
        b, broken = 0.0, True
    room(fr, t, flash=fl, rain_a=1.0, lens_light=b)
    bx, by = lens(fr, t, bulb=b, broken=broken)
    by -= 8
    ledge(fr, LEDGE_Y, -400, 2700)
    s = 3.2
    hipx, hipy = 1262, LEDGE_Y - ROBOT_HIP * s
    reach = kf(t, [(5.0, 0.0), (5.55, 1.0), (7.45, 1.0), (7.85, 0.0)])
    tapk = sum(math.exp(-((t - tp) / 0.07) ** 2) for tp in C2_TAPS)
    recoil = kf(t, [(7.45, 0.0), (7.6, 1.0), (8.7, 0.55)])
    lean = lerp(3, -10, recoil)
    sx, sy = hipx + 13 * s, hipy - 25 * s
    ang = aim(sx, sy, bx, by) - lean
    armF = (lerp(25, ang - 6 + 7 * tapk, reach), lerp(25, 6, reach))
    head = lerp(-6, -16, reach) if t < C2_POP else lerp(-16, -3, sm(7.7, 8.9, t))
    light = 1.0 if t < C2_POP else (0.42 + 0.42 * sm(7.7, 8.7, t)) * (1 + 0.12 * math.sin(t * 31))
    lights = [dev_light(fr, bx, by, 560, AMBER, 0.55 * b)]
    robot(fr, hipx, hipy, s, dict(lean=lean, head=head, armF=armF, armB=(-14, 18)), light=light, t=t,
          lights=lights, shade=0.55)
    if broken:
        spray(fr, bx, by, t, C2_POP, 45, seed=9, spread=560, up=280, life=0.9, size=2.4, col=AMBER_L, alpha=0.9,
              lit=1.2, grav=1300)
        fr.blob(bx, by, 26, FLAME_IN, 3.0 * math.exp(-(t - C2_POP) / 0.07))
    fr.flash = 0.06 * fl
    return fr

# ------------------------------------------------------------------ C3  CU: the flame flinches
def c03(t):
    fr = Frame(t); night(fr)
    fl = lflash(t)
    fr.camera(1020, 300, 1.7)
    room(fr, t, flash=fl, rain_a=1.0)
    lens(fr, t, broken=True)
    darken(fr, 0.35 * (1 - min(1.0, fl)))
    fr.identity()
    flinch = math.exp(-((t - 9.75) / 0.18) ** 2)
    light = 0.82 - 0.5 * flinch + 0.05 * math.sin(t * 29)
    head = kf(t, [(9.0, 4), (9.7, 7), (10.4, 0), (11.55, 0), (11.75, -10)])
    lights = [(-200, -200, 1700, (0.72, 0.80, 1.0), 0.65 * min(1.0, fl))]
    robot(fr, 1150, 1160, 13, dict(lean=0, head=head, armF=(5, 5), armB=(-5, 5)), light=light, facing=-1, t=t,
          lights=lights, shade=0.5)
    fr.flash = 0.10 * fl
    return fr

# ------------------------------------------------------------------ C4  ELS: storm wall, a tiny light
def c04(t):
    fr = Frame(t); night(fr)
    fl = lflash(t)
    bx = 1140
    by, _ = SEA_C4.surface(bx, 4, t)
    u = ease_io(lin(12, 16, t))
    fr.camera(lerp(960, bx, u * 0.8), lerp(402, by - 40, u * 0.8), 1 + 0.17 * u)
    sky(fr, [(0, (0.02, 0.025, 0.045)), (0.7, (0.06, 0.07, 0.11)), (1, (0.11, 0.12, 0.18))], y0=-200, y1=480)
    clouds(fr, t, -600, W + 600, -170, 150, 60, 140, 300, (0.03, 0.035, 0.055), CLOUD_L, seed=12, lit=fl, drift=-18)
    clouds(fr, t, -600, W + 600, 130, 410, 70, 90, 220, CLOUD_D, (0.11, 0.12, 0.18), seed=13, lit=fl * 0.8, drift=-30)
    if 14.35 < t < 15.0:
        bolt(fr, 760, 170, 820, 482, seed=5, I=lflash(t) * 0.9)
    fr.blob(500, 140, 180, (0.6, 0.6, 1.0), 0.12 * fl)
    SEA_C4.draw(fr, t, lit=fl * 0.2)
    # tiny boat silhouette + blinking toy flashlight
    c = fr.c
    poly(c, [(bx - 16, by - 3), (bx + 14, by - 3), (bx + 10, by + 3), (bx - 12, by + 3)])
    fillc(c, (0.01, 0.012, 0.02))
    c.arc(bx + 2, by - 7, 2.6, 0, TAU)
    fillc(c, (0.01, 0.012, 0.02))
    ph = (t - 12.2) % 1.7
    on = 1.0 if (ph < 0.16 or 0.32 < ph < 0.48 or 0.64 < ph < 0.8) else 0.0
    fr.blob(bx - 5, by - 8, 1.6, TOYLIGHT, 2.2 * on)
    fr.blob(bx - 5, by - 8, 8, TOYLIGHT, 0.4 * on)
    rain(fr, t, int(1300 * storm(t)), seed=17, alpha=0.20, length=46, speed=1700, ang=0.30)
    fr.flash = 0.16 * fl
    return fr

# ------------------------------------------------------------------ C5  MS: the child signals
C5_BLINK = [(16.7, 16.9), (17.05, 17.25), (17.4, 17.6), (18.3, 19.35)]

def boat_shot_bg(fr, t, fl, lamp=0.0, dot=0.0):
    sky(fr, NIGHT_SKY, y0=-200, y1=440)
    clouds(fr, t, -600, W + 600, -200, 220, 60, 110, 260, (0.03, 0.035, 0.06), CLOUD_L, seed=21, lit=fl,
           drift=-20)
    tiny_tower(fr, 170, 433, 70, (0.012, 0.015, 0.025), dot=dot, lamp=lamp)

def c05(t):
    fr = Frame(t); night(fr)
    fl = lflash(t)
    bx = 980
    ys0, _ = SEA_BOAT.surface(bx, 4, t)
    fr.camera(bx - 120 + 8 * nz(t * 0.7, 1), lerp(ys0 - 90, 520, 0.4) + 6 * nz(t * 0.9, 2), 1.55,
              rot=0.022 * math.sin(t * 1.1))
    boat_shot_bg(fr, t, fl, dot=0.7)
    SEA_BOAT.draw(fr, t, 0, 5, lit=fl * 0.25)
    ys, sl = SEA_BOAT.surface(bx, 4, t)
    roll = sl * 0.75 + 0.03 * math.sin(t * 1.7)
    flon = blink(t, C5_BLINK)
    cp = dict(armF=(kf(t, [(16, 70), (16.5, 97), (19.35, 97), (19.85, 75)]), 4), armB=(30, 30), brow=1.1,
              mouth=-1 if flon > 0.5 else 0, fl_on=flon, fl_len=520, fl_w=70,
              head=kf(t, [(16, 6), (16.5, -6), (19.4, -6), (19.9, 9)]))
    boat(fr, bx, ys + 6, 3.4, roll, childP=cp, t=t, shade=0.55, lights=[(0, 0, 1600, (0.7, 0.78, 1.0), 0.5 * fl)])
    SEA_BOAT.draw(fr, t, 5, None, lit=fl * 0.25)
    spray(fr, bx - 240, ys - 10, t, 17.8, 60, seed=4, spread=300, up=420, life=1.2, size=3.0,
          col=(0.55, 0.62, 0.72), alpha=0.7)
    rain(fr, t, int(1400 * storm(t)), seed=27, alpha=0.22, length=48, speed=1700, ang=0.28, sparkle=1.4)
    fr.flash = 0.14 * fl
    return fr

# ------------------------------------------------------------------ C6  POV telescope: the rocks
_yy, _xx = np.mgrid[0:H, 0:W].astype(F32)
_D = np.sqrt((_xx - W / 2) ** 2 + (_yy - H / 2) ** 2)
SCOPE_R = 340
_SM = np.clip((SCOPE_R - _D) / 16, 0, 1) * (1 - 0.45 * np.clip(_D / SCOPE_R, 0, 1) ** 3)
_SR = np.exp(-((_D - SCOPE_R - 5) / 4.5) ** 2) * 0.10

def scope_post(img):
    return img * _SM[..., None] + _SR[..., None] * np.array((0.9, 0.7, 0.4), F32)

C6_ROCKS = [(1640, 150, 190, 10), (1740, 120, 280, -14), (1840, 170, 170, 8), (1930, 130, 240, -6),
            (2030, 160, 150, 12)]

def c06(t):
    fr = Frame(t); night(fr)
    fl = lflash(t)
    u = ease_io(lin(20.7, 22.2, t))
    fr.camera(lerp(830, 1830, u) + 5 * nz(t * 3, 4), 470 + 4 * nz(t * 2.7, 5), 1.3)
    sky(fr, NIGHT_SKY, y0=-300, y1=280, x1=3000)
    clouds(fr, t, -400, 2800, -200, 180, 70, 90, 220, CLOUD_D, CLOUD_L, seed=33, lit=fl, drift=-15)
    SEA_POV.x1 = 3000
    SEA_POV.draw(fr, t, 0, 4)
    bx = 830
    ys, sl = SEA_POV.surface(bx, 3, t)
    flon = blink(t, [(20.05, 20.25), (20.4, 20.6), (20.75, 20.95), (21.3, 21.6)])
    boat(fr, bx, ys + 3, 1.5, sl * 0.8, childP=dict(armF=(105, 8), brow=1.0, fl_on=flon, fl_len=300, fl_w=40),
         t=t, shade=0.5)
    base = SEA_POV.yb(4) + 10
    rocks(fr, base, C6_ROCKS, (0.008, 0.009, 0.014), rim=((0.55, 0.60, 0.72), 0.7))
    SEA_POV.draw(fr, t, 4, None)
    for k, (t0, x) in enumerate(((20.6, 1700), (21.5, 1860), (22.3, 1760))):
        spray(fr, x, base - 20, t, t0, 70, seed=40 + k, spread=260, up=520, life=1.3, size=3.2,
              col=(0.62, 0.68, 0.78), alpha=0.8)
    rain(fr, t, int(900 * storm(t)), seed=37, alpha=0.18, length=40, speed=1600, ang=0.28)
    fr.post.append(scope_post)
    fr.flash = 0.10 * fl
    return fr

# ------------------------------------------------------------------ C7  CU: decision
def c07(t):
    fr = Frame(t); night(fr)
    fl = lflash(t)
    fr.camera(720, 250, 1.5)
    room(fr, t, flash=fl, rain_a=1.0)
    darken(fr, 0.3)
    fr.identity()
    low = kf(t, [(23.0, 0.0), (23.25, 0.0), (24.0, 1.0)])
    clasp = kf(t, [(24.65, 0.0), (25.5, 1.0)])
    if clasp < 0.001:
        armF = (lerp(178, 30, low), lerp(-38, 22, low))
        armB = (lerp(128, 22, low), lerp(-12, 18, low))
    else:
        armF = (lerp(30, 176, clasp), lerp(22, 10, clasp))
        armB = (lerp(22, 170, clasp), lerp(18, -14, clasp))
    head = kf(t, [(23.0, -4), (24.0, 9), (24.7, 9), (25.5, 2)])
    resolve = math.exp(-((t - 25.45) / 0.25) ** 2)
    light = kf(t, [(23.0, 0.9), (24.0, 0.7), (24.7, 0.7), (25.6, 0.95)]) + 0.2 * resolve
    lights = [(W + 200, 100, 1500, (0.55, 0.62, 0.85), 0.35)]
    out = robot(fr, 700, 770, 8.5, dict(lean=kf(t, [(23, 0), (24, 5), (25.5, 0)]), head=head, armF=armF, armB=armB),
                light=light, t=t, lights=lights, shade=0.5)
    if clasp < 0.001:
        hx0, hy0 = out['handF']
        hdx, hdy = out['head']
        hx_ = lerp(hdx + 70, hx0, low)
        hy_ = lerp(hdy + 30, hy0, low)
        a = lerp(-0.06, 1.15, low)
        dx, dy = math.cos(a), math.sin(a)
        c = fr.c
        seg(c, hx_ - dx * 40, hy_ - dy * 40, hx_ + dx * 210, hy_ + dy * 210, 30, cm(BRASS_D, 0.6))
        seg(c, hx_ + dx * 90, hy_ + dy * 90, hx_ + dx * 210, hy_ + dy * 210, 38, cm(BRASS, 0.55))
        seg(c, hx_ + dx * 200, hy_ + dy * 200, hx_ + dx * 225, hy_ + dy * 225, 44, cm(BRASS_D, 0.6))
        seg(c, hx_ + dx * 100, hy_ + dy * 100 - 12, hx_ + dx * 200, hy_ + dy * 200 - 12, 3, (1, 0.9, 0.7), 0.3)
    fr.flash = 0.05 * fl
    return fr

# ------------------------------------------------------------------ C8  low angle: the climb
C8_LENS = dict(cx=1250, top=-290, w=560, h=560)

def c08(t):
    fr = Frame(t); night(fr)
    fl = lflash(t)
    fr.camera(960, 560, 1.15, rot=0.07)
    fr.translate(0, -150)
    room(fr, t, flash=fl, rain_a=1.4)
    fr.translate(0, 150)
    lens(fr, t, broken=True, L=C8_LENS)
    ledge(fr, 270, -500, 2600, ladder_x=1000, ladder_bot=1600, ladder_w=120)
    s = 6.0
    u = ease_io(lin(26.0, 29.0, t))
    w = math.pi / 0.45
    step = abs(math.sin(w * (t - 26)))
    hipy = lerp(1250, 720, u) - 14 * step
    sw = math.sin(w * (t - 26))
    armF = (170 + 12 * sw, -18 + 16 * sw)
    armB = (168 - 12 * sw, -10 - 16 * sw)
    legF = (40 + 26 * sw, -75 - 18 * sw)
    legB = (40 - 26 * sw, -75 + 18 * sw)
    lights = [(-100, -100, 1600, (0.72, 0.80, 1.0), 0.6 * min(1.0, fl))]
    robot(fr, 905, hipy, s, dict(lean=6, head=-12, armF=armF, armB=armB, legF=legF, legB=legB), light=0.95, t=t,
          lights=lights, shade=0.5)
    fr.flash = 0.10 * fl
    return fr

# ------------------------------------------------------------------ C9  ECU: the ember is given
C9_S = (1480.0, 400.0)
C9_O0 = (150.0, 780.0 - 15.5 * 13)

def c09_orb(t):
    if t < 29.55:
        return C9_O0
    if t < 30.1:
        u = ease_io(lin(29.55, 30.1, t))
        return (lerp(C9_O0[0], 470, u), lerp(C9_O0[1], 470, u))
    if t < 31.35:
        u = ease_io(lin(30.1, 31.35, t))
        x = lerp(470, C9_S[0] - 40, u)
        y = lerp(470, C9_S[1], u) - 40 * math.sin(math.pi * u)
        return (x + 3 * math.sin(t * 47), y + 2.5 * math.cos(t * 41))
    u = ease_io(lin(31.35, 31.45, t))
    return (lerp(C9_S[0] - 40, C9_S[0], u), C9_S[1])

def robot_hand_big(fr, wx, wy, ex, ey, ox, oy, side, shade, lights):
    """forearm from elbow (ex,ey) to wrist (wx,wy); a cupped three-finger hand wraps the orb (ox,oy)"""
    c = fr.c
    c.push_group()
    seg(c, ex, ey, wx, wy, 70, cm(TIN_DD, shade))
    seg(c, ex, ey, wx, wy, 52, cm(TIN_D, shade))
    seg(c, ex - 16 * side, ey, wx - 16 * side, wy, 6, cm(TIN_L, shade), 0.45)
    for k in range(3):
        rx = ex + (wx - ex) * (0.25 + 0.2 * k)
        ry = ey + (wy - ey) * (0.25 + 0.2 * k)
        c.arc(rx, ry, 5, 0, TAU)
        fillc(c, cm(TIN_L, shade), 0.6)
    # palm
    c.arc(wx, wy, 44, 0, TAU)
    fillc(c, cm(TIN_D, shade))
    c.arc(wx, wy, 44, 0, TAU)
    strokec(c, cm(TIN_DD, shade), 4)
    # fingers curl up around the orb's side
    a = math.atan2(oy - wy, ox - wx)
    for k, spread in enumerate((-0.95, -0.25, 0.45)):
        b = a + spread * side
        k1x, k1y = wx + math.cos(b) * 44, wy + math.sin(b) * 44
        b2 = b - 0.9 * side
        k2x, k2y = k1x + math.cos(b2) * 40, k1y + math.sin(b2) * 40
        b3 = b2 - 0.7 * side
        tx, ty = k2x + math.cos(b3) * 28, k2y + math.sin(b3) * 28
        seg(c, k1x, k1y, k2x, k2y, 24, cm(TIN_D, shade))
        seg(c, k2x, k2y, tx, ty, 19, cm(TIN_D, shade))
        for jx, jy, jr in ((k1x, k1y, 13), (k2x, k2y, 11)):
            c.arc(jx, jy, jr, 0, TAU)
            fillc(c, cm(TIN_DD, shade))
    _apply_lights(fr, lights)
    c.pop_group_to_source()
    c.paint()

def c09(t):
    fr = Frame(t); night(fr)
    camx = lerp(800, 1160, ease_io(lin(29.3, 31.3, t)))
    fr.camera(camx, 402, 1.0)
    O = c09_orb(t)
    c = fr.c
    # background: dark lens prisms catching the ember's light
    for i in range(-2, 16):
        y0 = -100 + i * 66
        pat = cairo.LinearGradient(0, y0, 0, y0 + 66)
        pat.add_color_stop_rgb(0, 0.05, 0.075, 0.085)
        pat.add_color_stop_rgb(0.15, 0.03, 0.045, 0.055)
        pat.add_color_stop_rgb(1, 0.015, 0.022, 0.03)
        c.set_source(pat)
        c.rectangle(-400, y0, 2800, 66)
        c.fill()
        prox = math.exp(-abs(y0 + 8 - O[1]) / 170)
        pg = cairo.LinearGradient(O[0] - 700, 0, O[0] + 700, 0)
        pg.add_color_stop_rgba(0, 1, 0.7, 0.35, 0)
        pg.add_color_stop_rgba(0.5, 1, 0.75, 0.4, min(1.0, 0.55 * prox))
        pg.add_color_stop_rgba(1, 1, 0.7, 0.35, 0)
        fr.g.set_source(pg)
        fr.g.rectangle(-400, y0 + 3, 2800, 3.5)
        fr.g.fill()
    # bullseye rings around the socket
    S = C9_S
    for r in (110, 165, 220, 275, 330, 385):
        c.arc(S[0], S[1], r, 0, TAU)
        strokec(c, (0.10, 0.15, 0.17), 16)
        d = math.hypot(O[0] - S[0], O[1] - S[1])
        fr.g.arc(S[0], S[1], r, 0, TAU)
        strokec(fr.g, AMBER, 3, min(1.0, 0.35 * math.exp(-max(0, d - r) / 260)))
    c.arc(S[0], S[1], 70, 0, TAU)
    fillc(c, cm(BRASS_D, 0.7))
    c.arc(S[0], S[1], 46, 0, TAU)
    fillc(c, (0.02, 0.02, 0.025))
    c.arc(S[0], S[1], 62, 0, TAU)
    strokec(c, cm(BRASS, 0.7), 4)
    # the robot's lantern, door open
    inside = t < 29.55
    fr.save()
    fr.translate(150, 780)
    fr.scale(13)
    lantern_head(fr, 1.0 if inside else 0.0, 'flame' if inside else 'none', t, shade=0.6, door=1.0)
    fr.restore()
    # the ember
    if not inside:
        ox, oy = O
        fl = 1 + 0.06 * math.sin(t * 19)
        c.arc(ox, oy, 30, 0, TAU)
        fillc(c, AMBER)
        c.arc(ox, oy, 20, 0, TAU)
        fillc(c, FLAME_IN)
        fr.g.arc(ox, oy, 30, 0, TAU)
        fillc(fr.g, cm(AMBER, 0.6))
        fr.blob(ox, oy, 12, FLAME_IN, 2.0 * fl)
        fr.blob(ox, oy, 45, AMBER, 0.7 * fl)
        fr.blob(ox, oy, 140, AMBER, 0.18 * fl)
    # hands
    appear = ease_io(lin(29.0, 29.5, t))
    leave = ease_io(lin(31.55, 32.0, t))
    drop = 520 * (1 - appear) + 700 * leave
    lights = [dev_light(fr, O[0], O[1], 380, AMBER, 0.5)]
    for side in (-1, 1):
        wx = O[0] + 70 * side
        wy = O[1] + 78 + drop
        ex = O[0] + 170 * side
        ey = O[1] + 700 + drop
        robot_hand_big(fr, wx, wy, ex, ey, O[0], O[1], side, 0.42, lights)
    if t >= 31.45:
        a = t - 31.45
        fr.blob(S[0], S[1], 60, FLAME_IN, 2.2 * math.exp(-a / 0.12))
        spray(fr, S[0], S[1], t, 31.45, 30, seed=91, spread=500, up=300, life=0.6, size=2.0, col=AMBER_L,
              alpha=0.9, lit=1.0, grav=600)
    return fr

# ------------------------------------------------------------------ C10  CU: the lens ignites
C10_RINGS = [58 + 46 * k for k in range(11)]

def c10(t):
    fr = Frame(t); night(fr)
    z = 1.0 + 0.12 * ease_io(lin(32, 35, t))
    rot = 0.05 * (t - 32)
    fr.camera(960, 402, z, rot=rot)
    c = fr.c
    pat = cairo.RadialGradient(960, 402, 0, 960, 402, 900)
    pat.add_color_stop_rgb(0, 0.05, 0.08, 0.09)
    pat.add_color_stop_rgb(1, 0.01, 0.015, 0.02)
    c.set_source(pat)
    c.rectangle(-600, -600, 3200, 2000)
    c.fill()
    cx, cy = 960, 402
    # outer prism bands (top / bottom)
    band_on = sm(33.8, 34.25, t)
    for i in range(9):
        for sgn in (-1, 1):
            yy = cy + sgn * (520 + i * 52)
            c.move_to(-600, yy)
            c.curve_to(400, yy - sgn * 90, 1520, yy - sgn * 90, 2520, yy)
            strokec(c, (0.10, 0.15, 0.17), 18)
            if band_on > 0:
                fr.g.move_to(-600, yy)
                fr.g.curve_to(400, yy - sgn * 90, 1520, yy - sgn * 90, 2520, yy)
                strokec(fr.g, AMBER_L, 5, min(1.0, 0.45 * band_on))
    # rings
    for k, r in enumerate(C10_RINGS):
        c.arc(cx, cy, r, 0, TAU)
        strokec(c, (0.035, 0.06, 0.07), 34)
        c.arc(cx, cy, r + 14, 0, TAU)
        strokec(c, (0.17, 0.25, 0.27), 2.6)
        tk = 32.25 + 0.16 * k
        b = sm(tk, tk + 0.3, t)
        if b > 0:
            burst = 1 + 1.6 * math.exp(-max(0, t - tk - 0.15) / 0.18)
            g = fr.g
            g.arc(cx, cy, r, 0, TAU)
            strokec(g, AMBER, 12, min(1.0, 0.42 * b * burst))
            g.arc(cx, cy, r + 8, 0, TAU)
            strokec(g, (1.0, 0.32, 0.18), 3, min(1.0, 0.25 * b * burst))
            g.arc(cx, cy, r - 8, 0, TAU)
            strokec(g, (0.35, 0.55, 1.0), 3, min(1.0, 0.18 * b * burst))
    # brass frame spokes (they rotate with the lens)
    for k in range(4):
        a = k * TAU / 4 + 0.4
        seg(c, cx + math.cos(a) * 560, cy + math.sin(a) * 560, cx + math.cos(a) * 2000, cy + math.sin(a) * 2000,
            16, cm(BRASS_D, 0.35))
    # the ember at the centre
    c.arc(cx, cy, 34, 0, TAU)
    fillc(c, FLAME_IN)
    grow = sm(32.0, 34.4, t)
    fr.blob(cx, cy, 14, FLAME_IN, 2.5 + 3 * grow)
    fr.blob(cx, cy, 60, AMBER, 0.8 + 1.4 * grow)
    fr.blob(cx, cy, 220, AMBER, 0.15 + 0.5 * grow)
    fr.streak(cx, cy, 260, 2.5, AMBER_L, 0.6 * grow)
    fr.streak(cx, cy, 140, 2.0, AMBER_L, 0.3 * grow, vertical=True)
    fr.flash = 1.4 * sm(34.35, 35.0, t) ** 2
    fr.flash_col = (1.0, 0.93, 0.82)
    return fr

# ------------------------------------------------------------------ C11  ELS: the beam cuts the storm
C11_BOAT = (300, 600)

def c11(t):
    fr = Frame(t); night(fr)
    fl = lflash(t)
    u = ease_io(lin(35, 39, t))
    fr.camera(lerp(960, 900, u), lerp(402, 420, u), 1 + 0.06 * u)
    sky(fr, NIGHT_SKY, y0=-60, y1=530)
    lamp = (LH_X, LH_GY - 0.74 * LH_H - 0.018 * LH_H - 0.06 * LH_H)
    ang = math.pi - lerp(0.03, 0.36, ease_io(lin(35.2, 38.4, t)))
    clouds(fr, t, -500, W + 500, -60, 250, 70, 90, 230, CLOUD_D, CLOUD_L, seed=4, lit=fl * 0.6, drift=14,
           underlit=(lamp[0] - 500, lamp[1] - 120, 1100, AMBER, 0.12))
    if 37.65 < t < 38.2:
        bolt(fr, 1750, 30, 1700, 300, seed=8, I=fl * 0.6, width=0.6)
    SEA_ELS.draw(fr, t, 0, 6, lit=fl * 0.1)
    lamp_c, base = lighthouse(fr, LH_X, LH_GY, LH_H, t, lamp=1.0, lit=fl * 0.3)
    I = 1.0 + 0.15 * math.sin(t * 5)
    cone(fr, lamp_c[0], lamp_c[1], ang, 1700, 8, 230, AMBER_L, I)
    cone(fr, lamp_c[0], lamp_c[1], 0.02, 700, 6, 90, AMBER_L, 0.35)
    fr.blob(lamp_c[0], lamp_c[1], 14, FLAME_IN, 3.0)
    fr.blob(lamp_c[0], lamp_c[1], 70, AMBER_L, 0.8)
    fr.streak(lamp_c[0], lamp_c[1], 160, 2.5, AMBER_L, 0.8)
    # light pool on the water where the beam lands
    lx = lamp_c[0] + math.cos(ang) * 1100
    ly = max(560, lamp_c[1] + math.sin(ang) * 1100)
    glow(fr, lx, ly, 260, AMBER, 0.18 * sm(36, 37.5, t))
    SEA_ELS.draw(fr, t, 6, None, lit=fl * 0.1)
    bxp, byp = C11_BOAT
    ys, sl = SEA_ELS.surface(bxp, 7, t)
    bb = beam_light(fr, *[np.array([v]) for v in fr.dev(bxp, ys - 10)])[0].max()
    boat(fr, bxp, ys + 2, 1.1, sl, childP=dict(armF=(150, 40), brow=1.0), t=t, shade=0.4,
         lights=[dev_light(fr, lamp_c[0], lamp_c[1], 2200, AMBER_L, min(1.0, 0.9 * bb))])
    rain(fr, t, int(1300 * storm(t)), seed=47, alpha=0.13, length=34, speed=1400, ang=0.24, sparkle=1.5)
    fr.flash = 1.3 * math.exp(-max(0, t - 35.0) / 0.22) + 0.12 * fl
    fr.flash_col = (1.0, 0.93, 0.82)
    return fr

# ------------------------------------------------------------------ C12  MS: the rocks revealed, the turn
C12_ROCKS = [(120, 220, 330, 18), (300, 170, 250, -10), (450, 160, 180, 8), (40, 200, 220, -14)]

def c12(t):
    fr = Frame(t); night(fr)
    fl = lflash(t)
    shake = 10 * math.exp(-max(0, t - 41.0) / 0.3) if t > 41.0 else 0
    fr.camera(960 + 8 * nz(t * 0.7, 1) + shake * math.sin(t * 60), 402 + 6 * nz(t * 0.9, 2) + shake * math.cos(t * 53),
              1.0, rot=0.02 * math.sin(t * 1.1))
    fr.camera(1000 + 8 * nz(t * 0.7, 1) + shake * math.sin(t * 60), 470 + 6 * nz(t * 0.9, 2) + shake * math.cos(t * 53),
              1.3, rot=0.02 * math.sin(t * 1.1))
    boat_shot_bg(fr, t, fl, lamp=1.0)
    SEA_BOAT.draw(fr, t, 0, 4, lit=0.12)
    # the beam from the lighthouse, over the rocks
    I = 0.85 + 0.15 * math.sin(t * 6)
    cone(fr, 170, 370, 0.18 + 0.04 * math.sin(t * 0.9), 2100, 10, 380, AMBER_L, I)
    rocks(fr, 640, C12_ROCKS, (0.02, 0.022, 0.03), rim=(AMBER_L, 0.6))
    SEA_BOAT.draw(fr, t, 4, 5, lit=0.15)
    turn = ease_io(lin(40.2, 41.6, t))
    bx = lerp(1080, 980, ease_io(lin(39, 40.3, t))) + 220 * turn
    ys, sl = SEA_BOAT.surface(bx, 4, t)
    roll = sl * 0.75 + 0.03 * math.sin(t * 1.7) - 0.16 * math.sin(math.pi * turn)
    shield = kf(t, [(39.0, 1.0), (39.5, 1.0), (39.95, 0.0)])
    cp = dict(armF=(lerp(108, 168, shield), lerp(8, 40, shield)),
              armB=kf(t, [(40.1, (30, 30)), (40.5, (70, 50)), (41.8, (60, 40))]),
              brow=1.3, mouth=-1, eyes=0.0 if shield > 0.6 else 1.0, fl_on=0.0,
              head=kf(t, [(39.0, -14), (39.6, -14), (40.0, -4)]))
    light_on = [(-300, 150, 2300, AMBER_L, 0.65 * I)]
    boat(fr, bx, ys + 6, 3.4, roll, childP=cp, t=t, shade=0.5, lights=light_on, tiller=kf(t, [(40.2, 0), (40.6, 28)]))
    SEA_BOAT.draw(fr, t, 5, None, lit=0.15)
    spray(fr, 360, 440, t, 40.95, 260, seed=12, spread=560, up=900, life=1.6, size=2.4, col=(0.80, 0.74, 0.64),
          alpha=0.75, lit=0.5)
    spray(fr, 300, 470, t, 41.1, 160, seed=14, spread=380, up=600, life=1.4, size=1.6, col=(0.85, 0.80, 0.70),
          alpha=0.7, lit=0.4)
    spray(fr, 600, 470, t, 39.4, 60, seed=13, spread=300, up=500, life=1.3, size=3.0, col=(0.7, 0.66, 0.6),
          alpha=0.8, lit=0.4)
    rain(fr, t, int(1100 * storm(t)), seed=57, alpha=0.18, length=48, speed=1700, ang=0.28, sparkle=0.9)
    fr.flash = 0.10 * fl
    return fr

# ------------------------------------------------------------------ C13  MS: the keeper, spent
ROBOT_SIT = dict(lean=-12, head=30, armF=(8, 8), armB=(4, 10), legF=(86, -6), legB=(80, -10))

def c13(t, dawnk=0.0):
    fr = Frame(t); night(fr)
    fl = lflash(t)
    fr.camera(1170, 395, 1.28 + 0.06 * lin(42, 45.3, t))
    sweep = 2.1 * t
    room(fr, t, flash=fl, rain_a=0.8, lens_light=0.6)
    lc_ = lens(fr, t, on=0.55, orb=0.6, sweep=sweep)
    ledge(fr, LEDGE_Y, -400, 2700)
    # rotating beams inside the room
    for k in (0, 1):
        p = sweep + k * math.pi
        cxp = math.cos(p)
        L = 1500 * abs(cxp) ** 0.85
        if L > 15:
            cone(fr, lc_[0], lc_[1], 0.0 if cxp > 0 else math.pi, L, 20, 260 * (0.35 + 0.65 * abs(cxp)), AMBER_L,
                 0.30 * (0.5 + 0.5 * abs(cxp)))
    rb = beam_light(fr, *[np.array([v]) for v in fr.dev(1010, 440)])[0].max()
    lights = [dev_light(fr, lc_[0], lc_[1], 700, AMBER, 0.25 + 0.4 * min(1.0, rb))]
    robot(fr, 1020, LEDGE_Y - 4, 3.2, ROBOT_SIT, light=0.0, inner='none', facing=-1, t=t, lights=lights, shade=0.45)
    fr.flash = 0.05 * fl
    return fr

# ------------------------------------------------------------------ C14  ELS dawn: after the storm
GULLS = [(400, 230, 14, 0.0, 18), (520, 260, 10, 1.7, 22), (1650, 180, 12, 3.1, -15), (900, 140, 9, 2.2, 12)]

def dawn_exterior(fr, t, sun_y, lamp=0.0, figures=None, boat_on=True):
    sky(fr, DAWN_SKY, y0=-60, y1=530)
    fr.blob(430, sun_y, 50, (1.0, 0.9, 0.7), 1.4)
    fr.blob(430, sun_y, 230, (1.0, 0.62, 0.42), 0.45)
    c = fr.c
    c.arc(430, sun_y, 34, 0, TAU)
    fillc(c, (1.0, 0.93, 0.78))
    clouds(fr, t, -400, W + 400, 40, 300, 22, 50, 130, (0.62, 0.42, 0.55), (1.0, 0.82, 0.72), seed=61, drift=6,
           alpha=0.85)
    SEA_DAWN.draw(fr, t, 0, 5, foam_scale=1.0)
    # sun glitter
    rng = np.random.default_rng(int(t * 12))
    n = 120
    gx = 430 + rng.normal(0, 70, n) * (1 + rng.random(n))
    gy = 525 + rng.random(n) ** 1.6 * 270
    g = fr.g
    for i in range(n):
        w = 4 + 14 * (gy[i] - 520) / 270
        g.move_to(gx[i] - w, gy[i])
        g.line_to(gx[i] + w, gy[i])
    g.set_source_rgba(1.0, 0.85, 0.6, 0.55)
    g.set_line_width(2)
    g.stroke()
    lamp_c, base = lighthouse(fr, LH_X, LH_GY, LH_H, t, lamp=lamp, dawn=1.0, figures=figures)
    if boat_on:
        boat(fr, 990, 700, 1.05, -0.12, with_child=False, shade=0.85,
             lights=[(0, 400, 1500, (1.0, 0.7, 0.5), 0.35)])
    SEA_DAWN.draw(fr, t, 5, None)
    gulls(fr, t, GULLS)
    return lamp_c

def c14(t):
    fr = Frame(t); dawn_grade(fr)
    u = lin(45, 49, t)
    fr.camera(lerp(960, 1040, u), 402, 1.0 + 0.05 * u)
    lamp = (1 - sm(45.3, 47.8, t)) * (0.75 + 0.25 * math.sin(t * 23) * math.sin(t * 9))
    lamp_c = dawn_exterior(fr, t, lerp(528, 505, u), lamp=lamp)
    if lamp > 0.01:
        fr.blob(lamp_c[0], lamp_c[1], 30, AMBER_L, 0.8 * lamp)
    return fr

# ------------------------------------------------------------------ C15  MS dawn: she finds him
def c15(t):
    fr = Frame(t); dawn_grade(fr)
    fr.camera(980, 400, 1.3)
    room(fr, t, dawn=1.0, rain_a=0.0, sun=1.0)
    lens(fr, t, on=0.0, dawn=1.0)
    ledge(fr, LEDGE_Y, -400, 2700, dawn=1.0, ladder_x=700, ladder_bot=1400)
    warm = [(-200, 0, 1900, (1.0, 0.72, 0.50), 0.32)]
    robot(fr, 1020, LEDGE_Y - 4, 3.2, ROBOT_SIT, light=0.0, inner='none', facing=-1, t=t, lights=warm, shade=0.8)
    s = 4.0
    standy = LEDGE_Y - 21 * s
    rise = ease_io(lin(49.0, 49.9, t))
    walk = ease_io(lin(50.0, 51.35, t))
    x = lerp(700, 850, walk)
    y = lerp(LEDGE_Y + 160, standy, rise)
    ph = (t - 50.0) / 0.36 * math.pi
    sw = math.sin(ph) if 50.0 < t < 51.35 else 0.0
    crouch = ease_io(lin(51.3, 51.9, t))
    if t < 49.9:
        legs = dict(legF=(40 * (1 - rise), -60 * (1 - rise)), legB=(-10, -10))
        arms = dict(armF=(lerp(170, 20, rise), 10), armB=(lerp(160, 15, rise), 10))
    else:
        legs = dict(legF=(lerp(28 * sw, 55, crouch), lerp(-8 - 10 * max(0, -sw), -95, crouch)),
                    legB=(lerp(-28 * sw, 40, crouch), lerp(-8 - 10 * max(0, sw), -100, crouch)))
        arms = dict(armF=(lerp(20 + 20 * sw, 75, crouch), lerp(10, 30, crouch)), armB=(15 - 20 * sw, 10))
    y += 6 * abs(sw) * 0 + crouch * 30
    P = dict(mode='stand', lean=lerp(0, 18, crouch), head=lerp(0, 16, crouch), brow=0.8, mouth=0, **legs, **arms)
    child(fr, x, y, s, P, facing=1, t=t, shade=0.85, lights=warm, flashlight=True)
    return fr

# ------------------------------------------------------------------ C16  ECU: her light, given back
def c16(t):
    fr = Frame(t); dawn_grade(fr)
    fr.camera(960, 402, 1.0)
    c = fr.c
    pat = cairo.LinearGradient(0, 0, W, 0)
    pat.add_color_stop_rgb(0, 0.20, 0.13, 0.15)
    pat.add_color_stop_rgb(1, 0.55, 0.36, 0.30)
    c.set_source(pat)
    c.paint()
    for k, (bx, by, br) in enumerate(((1500, 200, 90), (1700, 520, 60), (300, 120, 70), (1250, 650, 50))):
        fr.blob(bx, by, br, (1.0, 0.75, 0.5), 0.12)
    placed = t >= 53.55
    click = 54.2
    lit = 0.0 if t < click else min(1.0, (t - click) / 0.08) * (1 - 0.6 * math.exp(-((t - click - 0.25) / 0.05) ** 2))
    fr.save()
    fr.translate(820, 760)
    fr.scale(16)
    lantern_head(fr, lit, 'toy' if placed else 'none', t, shade=0.85, door=1.0)
    fr.restore()
    # the child's hand + toy flashlight
    u = ease_io(lin(52.3, 53.55, t))
    back = ease_io(lin(54.5, 55.0, t))
    tx = lerp(1720, 820, u) + 900 * back
    ty = lerp(600, 760 - 14 * 16, u) + 60 * back
    rot = lerp(-0.25, -math.pi / 2, u)   # flashlight axis angle (pointing up when placed)
    if not placed:
        dx, dy = math.cos(rot), math.sin(rot)
        L = 13.5 * 16 * 0.5
        seg(c, tx - dx * L, ty - dy * L, tx + dx * L, ty + dy * L, 6.4 * 16, TOY)
        seg(c, tx + dx * L, ty + dy * L, tx + dx * (L + 30), ty + dy * (L + 30), 7.6 * 16, RED)
    # hand: sleeve from the right edge to the wrist
    hx_ = tx + 70 if not placed else lerp(890, 1700, back)
    hy_ = ty + 40 if not placed else lerp(560, 640, back)
    if placed and t < 54.5:
        press = math.exp(-((t - click + 0.05) / 0.12) ** 2)
        hx_ = 900 - 20 * press
        hy_ = 470 + 30 * press
    c.push_group()
    seg(c, hx_ + 140, hy_ + 120, W + 300, hy_ + 330, 170, COAT)
    seg(c, hx_ + 120, hy_ + 100, hx_ + 160, hy_ + 135, 180, COAT_D)
    c.arc(hx_, hy_, 72, 0, TAU)
    fillc(c, SKIN)
    for k in range(4):
        a = -2.4 + k * 0.32
        seg(c, hx_ + math.cos(a) * 40, hy_ + math.sin(a) * 40, hx_ + math.cos(a) * 96, hy_ + math.sin(a) * 96, 30,
            SKIN)
    seg(c, hx_ - 20, hy_ + 50, hx_ - 80, hy_ + 30, 30, SKIN_D)
    _apply_lights(fr, [(W + 200, 0, 1500, (1.0, 0.78, 0.55), 0.35)] +
                  ([dev_light(fr, 820, 760 - 21 * 16, 500, TOYLIGHT, 0.5 * lit)] if lit > 0 else []))
    c.pop_group_to_source()
    c.paint()
    return fr

# ------------------------------------------------------------------ C17  CU: he wakes
def c17(t):
    fr = Frame(t); dawn_grade(fr)
    fr.camera(1130, 300, 1.75)
    room(fr, t, dawn=1.0, rain_a=0.0, sun=1.0)
    darken(fr, 0.25)
    fr.identity()
    flick = blink(t, [(55.12, 55.22), (55.42, 55.5)])
    on = sm(55.85, 56.1, t)
    light = max(flick * 0.8, on * (1 + 0.25 * math.exp(-((t - 56.05) / 0.12) ** 2)))
    head = kf(t, [(55.0, 30), (56.0, 30), (56.8, -6)])
    warm = [(W + 200, 0, 1800, (1.0, 0.72, 0.50), 0.30)]
    robot(fr, 720, 1185, 12, dict(lean=-8, head=head, armF=(8, 8), armB=(4, 10)), light=light, inner='toy', t=t,
          lights=warm, shade=0.8)
    smile = t > 56.4
    child(fr, 1650, 880, 10, dict(mode='sit', lean=20, head=8, brow=0.0 if smile else 0.8, mouth=1 if smile else 0,
                                   eyes=0.0 if t > 56.6 else 1.0, armF=(60, 30), armB=(40, 20)),
          facing=-1, t=t, shade=0.85, lights=warm + ([(720, 300, 900, TOYLIGHT, 0.4 * light)] if light > 0 else []),
          flashlight=False)
    return fr

# ------------------------------------------------------------------ C18  ELS dawn: two small lights
def figures_on_gallery(fr, x, gal_y, h):
    out = robot(fr, x - 18, gal_y - ROBOT_HIP * 0.42, 0.42, dict(armF=(20, 15)), light=1.0, inner='toy', t=fr.t,
                shade=0.6, self_light=0.0)
    fx, fy = fr.c.device_to_user(*out['flame'])
    fr.blob(fx, fy, 1.6, FLAME_IN, 1.6)
    fr.blob(fx, fy, 6, TOYLIGHT, 0.45)
    child(fr, x + 16, gal_y - 21 * 0.5, 0.5, dict(mode='stand', legF=(3, 0), legB=(-3, 0), armF=(40, 30)),
          facing=-1, t=fr.t, shade=0.7, flashlight=False)

def c18(t):
    fr = Frame(t); dawn_grade(fr)
    u = ease_io(lin(57.0, 59.4, t))
    z = math.exp(math.log(3.2) * (1 - u))
    fr.camera(lerp(LH_X, 960, u), lerp(LH_GY - 0.80 * LH_H, 402, u), z)
    dawn_exterior(fr, t, lerp(470, 455, u), lamp=0.0, figures=figures_on_gallery)
    return fr

CUTS = [(0, 5, c01), (5, 9, c02), (9, 12, c03), (12, 16, c04), (16, 20, c05), (20, 23, c06), (23, 26, c07),
        (26, 29, c08), (29, 32, c09), (32, 35, c10), (35, 39, c11), (39, 42, c12), (42, 45, c13), (45, 49, c14),
        (49, 52, c15), (52, 55, c16), (55, 57, c17), (57, 60.01, c18)]

def shot_at(t):
    for a, b, f in CUTS:
        if a <= t < b:
            return f
    return CUTS[-1][2]
