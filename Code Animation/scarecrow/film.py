# -*- coding: utf-8 -*-
"""〈허수아비의 겨울〉 — full film, 22 cuts, ~125 s. Each cut is a function of local time u returning a Comp."""
import sys, os, time, math, subprocess
import numpy as np
import cairo
from keys_k import *
import keys_k
import motion
import eng

FPS = 24
TAUf = math.tau

def K(t, ks, inb=1):
    return keys(twos(t), ks, inb)

def wind_level(t, gusts):
    w = 0.0
    for a, b in gusts:
        if a <= t < b:
            w = max(w, min(1.0, (t - a) / 0.12) * min(1.0, (b - t) / 0.2))
    return w

def ss(x):
    x = min(1.0, max(0.0, x))
    return x * x * (3 - 2 * x)

def step(u, a, b, n=3):
    """stepped 0..1 ramp between a and b in n drawn steps (on-screen inbetweens)"""
    if u <= a:
        return 0.0
    if u >= b:
        return 1.0
    return math.ceil((u - a) / (b - a) * n) / n

GRADE = {
    'dawn': ((0.03, 0.02, 0.03), (1.02, 0.99, 0.95), 1.02, 0.97),
    'noon': ((0.02, 0.02, 0.03), (1.02, 1.0, 0.98), 1.05, 1.0),
    'autumn': ((0.03, 0.02, 0.02), (1.04, 1.0, 0.94), 1.05, 1.0),
    'sunset': ((0.03, 0.02, 0.04), (1.04, 0.97, 0.93), 1.05, 1.02),
    'rain': ((0.02, 0.02, 0.03), (0.95, 0.97, 1.0), 0.9, 1.0),
    'frost': ((0.02, 0.02, 0.04), (0.98, 0.99, 1.03), 0.95, 1.0),
    'dusk': ((0.02, 0.02, 0.05), (0.92, 0.92, 1.02), 0.95, 1.02),
    'blizzard': ((0.015, 0.015, 0.04), (0.74, 0.80, 1.0), 0.85, 1.05),
    'moon': ((0.01, 0.015, 0.04), (0.92, 0.96, 1.08), 0.9, 1.05),
    'thaw': ((0.02, 0.02, 0.03), (1.0, 1.0, 1.0), 1.0, 1.0),
    'spring': ((0.02, 0.02, 0.02), (1.02, 1.0, 0.97), 1.06, 1.0),
}
TINT = {
    'dawn': dict(mix=(1.0, 0.80, 0.66), k=0.12),
    'noon': dict(),
    'autumn': dict(mix=(1.0, 0.86, 0.66), k=0.10),
    'sunset': dict(mul=(0.80, 0.62, 0.62), mix=(0.98, 0.52, 0.30), k=0.16),
    'rain': dict(mul=(0.80, 0.84, 0.88)),
    'frost': dict(mul=(0.88, 0.92, 1.0), add=(0.02, 0.02, 0.04)),
    'dusk': dict(mul=(0.60, 0.60, 0.80), add=(0.02, 0.02, 0.05)),
    'blizzard': dict(mul=(0.62, 0.66, 0.92), add=(0.02, 0.02, 0.06)),
    'moon': dict(mul=(0.48, 0.55, 0.86), add=(0.01, 0.01, 0.05)),
    'thaw': dict(mul=(0.96, 0.96, 0.98)),
    'spring': dict(),
}
def jpal(key):
    return tint_pal(JI, **TINT[key])
def kpal(key, fem=False):
    return tint_pal(KO_F if fem else KO, **TINT[key])

class PaintedImg:
    def __init__(self, img):
        self.img = img
    view = Static.view

def frame2(key, cam, chars, u, T, fx_pre=None, fx_post=None, ccam=None, blur_bg=0.0, grade=None, mix=None, fore=True,
           vig=0.32, bgimg=None):
    set_frame(T)
    Ls = season_layers(key)
    S = Ls['S']
    cx, cy, z = cam
    cp = Comp()
    cp.lift, cp.gain, cp.sat, cp.contrast = grade or GRADE[key]
    cp.vig = vig
    cp.add((bgimg or Painted(key)).view(cx, cy, z), blur=blur_bg)
    if mix is not None and mix[1] > 0.001:
        cp.add(Painted(mix[0]).view(cx, cy, z), blur=blur_bg, alpha=mix[1])
    if fx_pre:
        d = dyn(); fx_pre(d.c); cp.add(d.rgba())
    if chars is not None:
        d = dyn(); c = d.c
        ccx, ccy, cz = ccam or cam
        c.save(); world_ctx(c, ccx, ccy, cz); chars(c, S); c.restore()
        cp.add(cel_finish(d.rgba(), T))
    if fx_post:
        d = dyn(); fx_post(d.c); cp.add(d.rgba())
    if fore:
        cp.add(Ls['fore'].view(cx, cy, z * 1.05), blur=4)
    cp.post.append(lambda img: film_post(img, T))
    return cp

_PTS = {}
def jpts(P, s=1.0):
    """world points of jiibi for pose P (cached dry draw)"""
    k = tuple(sorted(P.items())) + (s,)
    if k not in _PTS:
        sf = cairo.ImageSurface(cairo.FORMAT_ARGB32, 4, 4)
        c = cairo.Context(sf)
        jx, jy = JI_POS
        _PTS[k] = jiibi(c, jx, jy, s, dict(P), t=0.0)
    return _PTS[k]

def hat_pos(c, o):
    return c.device_to_user(*o['hat'])

def on_hat(c, o):
    hx, hy = hat_pos(c, o)
    return hx + 4, hy + 3

# ------------------------------------------------------------------ props & fx
def gift(c, x, y, kind, L, t, s=1.0):
    B = Boil(t, salt=17)
    c.save(); c.translate(x, y); c.scale(s, s)
    if kind == 'kaki':
        cel(c, lambda cc: cc.arc(0, 0, 6, 0, TAU), (0.94, 0.52, 0.16), (0.72, 0.32, 0.10), L, off=2, lw=1.2)
        cel(c, lambda cc: poly(cc, [(-4, -5), (0, -8), (4, -5), (0, -4)]), (0.42, 0.56, 0.22), (0.30, 0.40, 0.16), L, off=1, lw=0.8)
    elif kind == 'acorn':
        cel(c, lambda cc: smooth_path(cc, [(-4, -2), (4, -2), (3.5, 4), (0, 7), (-3.5, 4)]), (0.70, 0.48, 0.24), (0.50, 0.32, 0.14), L,
            off=1.5, lw=1.0)
        cel(c, lambda cc: smooth_path(cc, [(-5, -1), (-4, -5), (0, -6), (4, -5), (5, -1)]), (0.46, 0.34, 0.20), (0.32, 0.22, 0.12), L,
            off=1, lw=1.0)
    else:
        cel(c, lambda cc: poly(cc, B.jp([(0, 7), (-7, 1), (-4, -1), (-6, -7), (-2, -4), (0, -10), (2, -4), (6, -7), (4, 0), (8, 2)], 0.2)),
            (0.90, 0.24, 0.14), (0.66, 0.14, 0.10), L, off=1.5, lw=1.0)
    c.restore()

def rain_fx(c, t, alpha=0.7, n=500):
    tq = twos(t)
    rng = np.random.default_rng(9)
    x0 = rng.uniform(-200, W + 200, n); y0 = rng.uniform(0, H, n); d = rng.uniform(0.4, 1.0, n)
    for i in range(n):
        y = (y0[i] + 2600 * d[i] * tq) % (H + 200) - 100
        x = (x0[i] - 500 * d[i] * tq) % (W + 300) - 150
        L_ = 30 + 50 * d[i]
        line(c, x, y, x - L_ * 0.2, y + L_, 1.0 + 1.6 * d[i], (0.84, 0.88, 0.94), alpha * (0.35 + 0.5 * d[i]))

def snowfall(c, st, n, ang, speed, size, alpha, seed=3):
    """snow at an explicit snow-time (so it can freeze)"""
    rng = np.random.default_rng(seed)
    x0 = rng.uniform(-300, W + 300, n); y0 = rng.uniform(-200, H + 200, n); d = rng.uniform(0.4, 1.0, n)
    dx, dy = math.cos(ang), math.sin(ang)
    ph = rng.uniform(0, TAU, n)
    for i in range(n):
        x = (x0[i] + dx * speed * d[i] * st + 14 * math.sin(st * 1.3 + ph[i])) % (W + 600) - 300
        y = (y0[i] + dy * speed * d[i] * st) % (H + 400) - 200
        r = size * d[i]
        c.arc(x, y, r, 0, TAU)
        fillc(c, (0.94, 0.95, 1.0), alpha * (0.5 + 0.5 * d[i]))

def hawk_shadow(c, x, y, s, a=0.0, alpha=0.32):
    c.save(); c.translate(x, y); c.rotate(a); c.scale(s, s * 0.45)
    smooth_path(c, [(-10, 0), (-4, -3), (-2, -14), (-16, -26), (-30, -30), (-6, -34), (4, -10), (12, -2), (22, 0), (12, 2),
                    (4, 10), (-6, 34), (-30, 30), (-16, 26), (-2, 14), (-4, 3)])
    c.restore()
    fillc(c, (0.12, 0.10, 0.20), alpha)

def geese(c, t, x0, y0, n=7, s=9):
    tq = twos(t)
    for k in range(n):
        row = (k + 1) // 2
        side = 1 if k % 2 else -1
        x = x0 + tq * 60 - row * 26
        y = y0 + side * row * 14 * 0.0 + row * 10 * (1 if side > 0 else 0.5) * side
        fl = math.sin(tq * 9 + k)
        for sd in (-1, 1):
            inkline(c, [(x, y), (x - 6 * s / 9, y + sd * 0.1 - 5 * fl * s / 9 + sd * 6 * s / 9 * 0.0 - 4 * s / 9),
                        (x - 12 * s / 9, y - 2 * fl * s / 9)], 2.0 * s / 9, (0.24, 0.16, 0.24), 0.85)

def sparkles(c, t, pts, col=(1, 1, 1), seed=5):
    rng = np.random.default_rng(seed)
    tq = int(twos(t) * 12)
    for i, (x, y) in enumerate(pts):
        ph = (tq + int(rng.integers(0, 24))) % 24
        if ph < 4:
            r = (4 - abs(ph - 2)) * 3
            for a in (0, math.pi / 2):
                line(c, x - math.cos(a) * r, y - math.sin(a) * r, x + math.cos(a) * r, y + math.sin(a) * r, 1.4, col, 0.85)

DRIFT = [(-1100, 30), (-800, 14), (-560, -12), (-380, -40), (-250, -70), (-170, -94), (-120, -106), (-88, -100), (-66, -80),
         (-50, -52), (-34, -28), (-10, -12), (60, 4), (170, 30)]

def snowdrift(c, jx, jy, hs, L, t, pal):
    """lee drift: long tail streaming downwind (left), steep face against the pole"""
    if hs <= 0.01:
        return
    B = Boil(t, salt=61)
    pts = [(jx + x, jy + 30 + (y - 30) * hs) for (x, y) in DRIFT] + [(jx + 170, jy + 90), (jx - 1100, jy + 90)]
    def dr(cc):
        smooth_path(cc, B.jp(pts, 0.6))
    cel(c, dr, pal['snow'], pal['snow_s'], L, off=10 * hs + 2, lw=1.6)
    xs = [p[0] for p in DRIFT]; ys = [p[1] for p in DRIFT]
    for q in range(16):                                  # wind ripples following the slope
        x = -1000 + q * 58
        y0 = np.interp(x, xs, ys)
        for r in (1, 2):
            yb = jy + 30 + (y0 + 14 * r - 30) * hs
            inkline(c, B.jp(qcurve((jx + x, yb), (jx + x + 26, yb - 4 * hs), (jx + x + 50, yb + 2), 6), 0.3), 1.2,
                    pal['snow_s'], 0.45)
def butterfly(c, x, y, t, s=1.0, col=(0.98, 0.86, 0.30)):
    fl = abs(math.sin(twos(t) * 20))
    c.save(); c.translate(x, y); c.scale(s, s)
    for sd in (-1, 1):
        c.save(); c.scale(sd * (0.3 + 0.7 * fl), 1)
        smooth_path(c, [(0, 0), (8, -9), (12, -2), (6, 2), (9, 8), (2, 6)])
        c.restore()
        fillc(c, col, 0.95)
    line(c, 0, -4, 0, 6, 1.6, (0.25, 0.2, 0.15), 1)
    c.restore()

def nest_in_hat(c, hx, hy, L, t, stage=1.0, chicks=0):
    hat_at(c, hx, hy, 1.0, 0, t, L)
    if stage <= 0:
        return
    B = Boil(t, salt=71)
    w = 26 * min(1, stage)
    def nest(cc):
        smooth_path(cc, B.jp([(hx - w, hy - 28), (hx - w * 0.5, hy - 36), (hx + w * 0.5, hy - 36), (hx + w, hy - 28),
                              (hx + w * 0.7, hy - 20), (hx - w * 0.7, hy - 20)], 0.4))
    cel(c, nest, (0.66, 0.52, 0.32), (0.46, 0.34, 0.20), L, off=3, lw=2.0)
    for k in range(int(12 * min(1, stage))):
        x = hx - w + k * w / 6
        inkline(c, B.jp([(x, hy - 33), (x + 7, hy - 23)], 0.3), 1.4, (0.40, 0.30, 0.18), 0.8, taper=False)
    for k in range(chicks):
        kongi(c, hx - 11 + k * 11, hy - 32, 4.6, dict(open_beak=1.0 if (int(twos(t) * 6) + k) % 2 else 0.2, puff=1.25, feet=0,
                                                     tilt=-18 + k * 18), t=t, L=L)

def sprouts(c, base, toward, n, grow, L, t, seed=4):
    if grow <= 0:
        return
    B = Boil(t, salt=8)
    rng = np.random.default_rng(seed)
    (x0, y0), (x1, y1) = base, toward
    for k in range(n):
        u = rng.random()
        x = lerp(x0, x1, u); y = lerp(y0, y1, u) + rng.uniform(-6, 4)
        h_ = (16 + 24 * rng.random()) * grow
        inkline(c, B.jp(qcurve((x, y), (x + 3, y - h_ * 0.6), (x + 6 * rng.uniform(-1, 1), y - h_)), 0.3), 3.4, (0.62, 0.84, 0.30), 1.0)
        if grow > 0.8 and k % 4 == 0:
            c.arc(x + 4, y - h_, 4.5, 0, TAU); fillc(c, (0.99, 0.86, 0.22) if k % 8 else (1, 0.96, 0.94))

def title_card(c, alpha, alpha2):
    if alpha > 0:
        c.select_font_face('Noto Serif CJK KR', cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
        c.set_font_size(84)
        txt = '허수아비의 겨울'
        ext = c.text_extents(txt)
        x, y = W - 150 - ext.width, 330
        for dx, dy in ((-2, 0), (2, 0), (0, -2), (0, 2), (2, 3)):
            c.move_to(x + dx, y + dy); c.set_source_rgba(0.99, 0.97, 0.90, 0.75 * alpha); c.show_text(txt)
        c.move_to(x, y); c.set_source_rgba(0.16, 0.20, 0.36, alpha); c.show_text(txt)
        c.set_line_width(2); c.set_source_rgba(0.16, 0.20, 0.36, 0.7 * alpha)
        c.move_to(x + 4, y + 30); c.line_to(x + ext.width * alpha, y + 30); c.stroke()
    if alpha2 > 0:
        c.select_font_face('Noto Sans CJK KR', cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)
        c.set_font_size(28)
        txt = 'GoXoN × Claude  ·  every frame is code'
        ext = c.text_extents(txt)
        c.move_to(W - 150 - ext.width, 392); c.set_source_rgba(0.16, 0.20, 0.36, 0.9 * alpha2); c.show_text(txt)

# ================================================================== CUTS
def C1(u, T):          # 7 s  dawn ELS, slow push
    tq = twos(u)
    z = 0.86 + 0.07 * ss(tq / 7)
    pal = jpal('dawn')
    def chars(c, S):
        jx, jy = JI_POS
        o = jiibi(c, jx, jy, 1.3, dict(flapL=-0.1, flapR=0.0, wind=0.25, goreum_wind=0.2 + 0.1 * math.sin(tq * 2)), t=T, L=S['L'], pal=pal)
        rice_clump(c, jx, jy - 40, 1.2, S['rice'], T, n=70, wind=0.3)
        x, y = on_hat(c, o)
        kongi(c, x, y, 14, dict(blink=1, puff=1.18 + 0.05 * math.sin(tq * 3)), t=T, L=S['L'], pal=kpal('dawn'))
        for k, (dx, dy, a) in enumerate(((-260, -200, 0.3), (-420, -120, -0.2), (200, -260, 0.1), (380, -150, 2.9), (-80, -330, 0.7),
                                         (520, -300, 3.3), (-600, -60, 0.2))):
            dragonfly(c, jx + dx + 20 * math.sin(tq * 3 + k), jy + dy - 60 + 10 * math.cos(tq * 4 + k), 15, a, T)
    def fxp(c):
        flock(c, T, 700, 360, n=7, spread=300, s=7)
    cp = frame2('dawn', (1260, 690, z), chars, u, T, fx_post=fxp)
    cp.fade *= min(1.0, u / 1.2)
    return cp

def C2(u, T):          # 5 s  sparrows scatter, Kongi sleeps on
    tq = twos(u)
    G = [(2.0, 3.1)]
    W_ = wind_level(tq, G)
    flapR = K(u, [(0.0, -0.25), (2.06, 0.9, 0.25), (3.1, -0.45, 0.25), (3.35, -0.2, 0.15)])
    flapL = K(u, [(0.0, -0.25), (2.06, 0.85, 0.25), (3.1, -0.4, 0.25), (3.35, -0.25, 0.15)])
    pal = jpal('dawn')
    perch = [(-1, 1.0), (-1, 0.55), (1, 0.55), (1, 1.0)]
    vel = [(-300, -220), (-170, -300), (220, -260), (320, -170)]
    def chars(c, S):
        jx, jy = JI_POS
        o = jiibi(c, jx, jy, 1.0, dict(flapL=flapL, flapR=flapR, wind=W_, billow=W_, hat_tilt=10 * W_, head_tilt=6 * W_), t=T, L=S['L'],
                  pal=pal)
        x, y = on_hat(c, o)
        kongi(c, x, y, 11, dict(blink=1, puff=1.18 + 0.25 * W_ + 0.04 * math.sin(tq * 3), tilt=6 * W_), t=T, L=S['L'], pal=kpal('dawn'))
        chx, chy = c.device_to_user(*o['chest'])
        for k, (side, f) in enumerate(perch):
            cx_, cy_ = c.device_to_user(*o['cuffL' if side < 0 else 'cuffR'])
            px, py = lerp(chx, cx_, f), lerp(chy - 30, cy_, f) - 15
            if tq < 2.0 + k * 0.04:
                look = 1 if (int(tq * 2) + k) % 3 else -1
                kongi(c, px, py, 9, dict(face=look * side, tilt=(k - 1.5) * 4, puff=1.05), t=T, L=S['L'], pal=kpal('dawn', True))
            else:
                v = tq - 2.0 - k * 0.04
                kongi(c, px + vel[k][0] * v, py + vel[k][1] * v + 120 * v * v * 0, 9,
                      dict(face=1 if vel[k][0] > 0 else -1, wing=1.0 if int(tq * 12 + k) % 2 else 0.0, feet=0, tilt=-20 * side,
                           open_beak=0.6), t=T, L=S['L'], pal=kpal('dawn', True))
        rice_clump(c, jx, jy - 40, 1.0, S['rice'], T, n=70, wind=0.2 + W_)
    def fxp(c):
        if W_ > 0.05:
            wind_marks(c, T, alpha=W_)
    return frame2('dawn', (1330, 640, 1.25), chars, u, T, fx_post=fxp, ccam=(1500, 790, 2.3), blur_bg=1.4)

def C3(u, T):          # 5 s  CU Kongi wakes, yawns, stretches, dozes off again
    tq = twos(u)
    pal = jpal('dawn')
    blink = 1 if (tq < 1.0 or tq > 4.3 or 1.6 < tq < 1.95) else 0
    ob = K(u, [(0.0, 0.0), (1.3, 0.5, 0.15), (1.5, 1.0, 0.15), (2.1, 0.0, 0.15)])
    wing = K(u, [(0.0, 0.0), (2.4, 1.0, 0.1), (3.0, 0.0, 0.1)])
    sq = K(u, [(0.0, 1.0), (2.4, 1.12, 0.1), (3.05, 0.86, 0.08), (3.2, 1.0, 0.08)])
    pf = K(u, [(0.0, 1.18), (1.0, 1.1, 0.1), (3.2, 1.5, 0.1), (3.6, 1.3, 0.2)]) + 0.04 * math.sin(tq * 3)
    tilt = K(u, [(0.0, 0), (1.3, -14, 0.2), (2.1, 4, 0.2), (3.0, -6, 0.1), (3.2, 8, 0.1), (3.6, 0, 0.2), (4.3, 6, 0.3)])
    def chars(c, S):
        jx, jy = JI_POS
        o = jiibi(c, jx, jy, 1.0, dict(wind=0.12, goreum_wind=0.15), t=T, L=S['L'], pal=pal)
        x, y = on_hat(c, o)
        kongi(c, x, y, 11, dict(blink=blink, open_beak=ob, wing=wing, squash=sq, puff=pf, tilt=tilt), t=T, L=S['L'], pal=kpal('dawn'))
        if 3.2 < tq < 3.7:                        # a loose feather drifts off after the shake
            v = tq - 3.2
            B = Boil(T, salt=3)
            fx, fy = x + 14 + 40 * v, y - 24 + 30 * v
            inkline(c, B.jp(qcurve((fx, fy), (fx + 3, fy - 3), (fx + 6, fy - 1), 4), 0.2), 2.2, KO['back'], 0.9)
    return frame2('dawn', (1400, 560, 1.6), chars, u, T, ccam=(1505, 690, 5.0), blur_bg=3.0)

def C4(u, T):
    return motion.c4(u)

def C5(u, T):          # 4 s  noon ELS: the hawk's shadow sweeps over the field
    tq = twos(u)
    pal = jpal('noon')
    v = (tq - 0.4) / 2.6
    def fxpre(c):
        if 0 <= v <= 1:
            x = -300 + (W + 600) * v
            y = 820 - 140 * v
            hawk_shadow(c, x, y, 7.5 - 2 * v, a=-0.18, alpha=0.30)
    def chars(c, S):
        jx, jy = JI_POS
        o = jiibi(c, jx, jy, 1.0, dict(wind=0.2, goreum_wind=0.25), t=T, L=S['L'], pal=pal)
        x, y = on_hat(c, o)
        scared = tq > 1.9
        kongi(c, x, y, 11, dict(puff=1.55 if scared else 1.15, face=-1 if scared else 1, tilt=-18 if scared else 0,
                                blink=0), t=T, L=S['L'])
        rice_clump(c, jx, jy - 40, 1.0, S['rice'], T, n=60, wind=0.25)
    def fxp(c):
        if tq > 2.6:
            hx = 300 + (tq - 2.6) * 260
            hawk(c, hx, 150 + 20 * math.sin(tq * 2), 9, heading=0.2, flap=math.sin(tq * 6) * 0.5, L=(-0.5, -0.86))
    return frame2('noon', (1300, 620, 0.95), chars, u, T, fx_pre=fxpre, fx_post=fxp)

def C6(u, T):          # 4 s  low angle: the hawk dives at the hat
    tq = twos(u)
    pal = jpal('noon')
    v = ss(min(1, tq / 3.7))
    z = 1.5 + 0.12 * tq / 4
    def chars(c, S):
        jx, jy = JI_POS
        o = jiibi(c, jx, jy, 1.0, dict(wind=0.15, head_tilt=-4), t=T, L=S['L'], pal=pal)
        x, y = on_hat(c, o)
        kongi(c, x, y, 11, dict(puff=1.6, face=-1, tilt=-30 - 10 * v, blink=0, open_beak=0.4 if tq > 3.0 else 0), t=T, L=S['L'])
    def fxp(c):
        hx = lerp(420, 980, v); hy = lerp(120, 420, v)
        flap = 0.2 if tq < 2.4 else -0.5
        hawk(c, hx, hy, lerp(16, 74, v ** 1.6), heading=lerp(0.6, 0.95, v), flap=flap if int(tq * 6) % 2 else flap * 0.6,
             L=(-0.5, -0.86), dark=0.6)
    return frame2('noon', (1240, 380, z), chars, u, T, fx_post=fxp, ccam=(1380, 594, 4.5), blur_bg=2.2)

def feathers(c, x0, y0, tt, L, n=6, seed=11):
    """loose hawk feathers tumbling from an impact point (tt = s since impact)"""
    rng = np.random.default_rng(seed)
    for k in range(n):
        a = rng.uniform(-2.9, -0.4); sp = rng.uniform(60, 160)
        x = x0 + math.cos(a) * sp * tt + 18 * math.sin(tt * 5 + k)
        y = y0 + math.sin(a) * sp * tt + 70 * tt * tt
        r = rng.uniform(0, TAUf) + tt * rng.uniform(4, 9)
        def fe(cc, x=x, y=y, r=r):
            cc.save(); cc.translate(x, y); cc.rotate(r)
            smooth_path(cc, [(0, -13), (2.2, -5), (1.8, 7), (0, 12), (-1.8, 7), (-2.2, -5)]); cc.restore()
        cel(c, fe, (0.62, 0.48, 0.34), (0.42, 0.31, 0.22), L, off=1.5, lw=1.4)
        inkline(c, [(x - math.sin(r) * -13, y + math.cos(r) * -13), (x - math.sin(r) * 15, y + math.cos(r) * 15)], 1.0, INK_C, 0.8)

HIT = 1.25
def C6_1(u, T):        # 3 s  tighter: the hawk is on him -- a gust, the straw hand whips up and strikes it
    tq = twos(u)
    G = [(0.85, 3.2)]
    W_ = wind_level(tq, G)
    flapL = K(u, [(0.0, -0.2), (0.92, -0.2), (1.08, 0.6, 0.0), (HIT, 1.35, 0.0), (1.7, 1.05, 0.17), (2.2, 1.2, 0.17), (2.7, 1.0, 0.17)])
    whip = K(u, [(0.0, 0.0), (0.92, 0.0), (1.08, 0.5, 0.0), (HIT, 1.0, 0.0), (1.8, 0.75, 0.17), (2.6, 0.55, 0.17)])
    flapR = K(u, [(0.0, -0.2), (1.0, -0.2), (1.25, 0.8, 0.17), (2.0, 0.6, 0.17), (2.6, 0.85, 0.17)])
    pal = jpal('noon')
    def chars(c, S):
        jx, jy = JI_POS
        L = S['L']
        o = jiibi(c, jx, jy, 1.0, dict(flapL=flapL, flapR=flapR, whipL=whip, whip_dir=-1.35, wind=W_, billow=W_, lean=3 * W_,
                                       head_tilt=-4 + 5 * W_, hat_tilt=8 * W_), t=T, L=L, pal=pal)
        x, y = on_hat(c, o)
        shut = tq < 2.3
        kongi(c, x + 4, y + 2, 11, dict(puff=1.7 if shut else 1.4, face=-1, tilt=-34 if shut else -10, blink=1 if shut else 0,
                                        open_beak=0.0 if shut else 0.5, wing=0.0), t=T, L=L)
        if tq < HIT:
            # continues from the end of C6: already close, upper-left of the hat, then the strike
            v = ss(tq / HIT) ** 1.6
            hx = lerp(1350, 1392, v); hy = lerp(622, 668, v)
            hawk(c, hx, hy, lerp(27, 30, v), heading=lerp(0.62, 0.78, v), flap=-0.55 if int(tq * 8) % 2 else -0.35, L=L, dark=0.3)
            if tq > 0.0:                                           # talons forward
                for k in (-1, 1):
                    inkline(c, [(hx + 12 + k * 5, hy + 18), (hx + 30 + k * 5, hy + 34)], 2.4, (0.86, 0.70, 0.26), 1.0)
        else:
            a = tq - HIT
            if a < 0.17:                                           # the hit: held impact drawing
                hx, hy, hd = 1378, 650, -2.0
                for k in range(5):
                    an = -2.6 + k * 0.45
                    inkline(c, [(hx + math.cos(an) * 34, hy + math.sin(an) * 34), (hx + math.cos(an) * 60, hy + math.sin(an) * 60)],
                            2.2, (0.99, 0.97, 0.88), 0.95)
            else:
                v = a / 1.6
                hx = 1378 - 520 * v - 140 * v * v; hy = 650 - 300 * v + 60 * math.sin(v * 6)
                hd = -2.0 - 3.2 * v
            hawk(c, hx, hy, 28 - 8 * min(1, a), heading=hd, flap=0.9 if int(tq * 12) % 2 else -0.6, L=L, dark=0.3)
            feathers(c, 1390, 660, a, L)
    def fxp(c):
        if W_ > 0.05:
            wind_marks(c, T, alpha=W_)
        if HIT <= tq < HIT + 0.09:                                  # one white flash frame on the hit
            c.rectangle(0, 0, W, H); c.set_source_rgba(1, 0.98, 0.92, 0.22); c.fill()
    return frame2('noon', (1240, 400, 1.6), chars, u, T, fx_post=fxp, ccam=(1440, 712, 3.1), blur_bg=2.4)

def C7(u, T):          # 4 s  gust: arms fling up, hawk veers off; Kongi thinks he did it
    tq = twos(u)
    G = [(-1.0, 2.9)]
    W_ = wind_level(tq, G)
    flapR = K(u, [(0.0, 0.8), (0.3, 1.0, 0.17), (0.75, 0.7, 0.17), (1.1, 1.0, 0.17), (1.6, 0.75, 0.17), (2.0, 1.0, 0.17),
                  (2.9, -0.45, 0.25), (3.2, -0.2, 0.15)])
    flapL = K(u, [(0.0, 1.0), (0.34, 0.95, 0.17), (0.9, 0.65, 0.17), (1.3, 0.95, 0.17), (1.8, 0.7, 0.17), (2.2, 0.95, 0.17),
                  (2.9, -0.4, 0.25), (3.25, -0.25, 0.15)])
    pal = jpal('noon')
    def chars(c, S):
        jx, jy = JI_POS
        o = jiibi(c, jx, jy, 1.0, dict(flapL=flapL, flapR=flapR, wind=W_, billow=W_, lean=4 * W_, head_tilt=6 * W_, hat_tilt=10 * W_),
                  t=T, L=S['L'], pal=pal)
        x, y = on_hat(c, o)
        if tq < 3.0:
            kongi(c, x + 6, y, 11, dict(wing=1.0 if int(tq * 12) % 2 else 0.4, open_beak=1.0 * W_, tilt=24 * W_, puff=1.3, face=-1),
                  t=T, L=S['L'])
        else:
            kongi(c, x, y, 11, dict(face=-1, puff=1.45, tilt=-14, blink=1 if 3.5 < tq < 3.62 else 0), t=T, L=S['L'])
        rice_clump(c, jx, jy - 60, 0.9, S['rice'], T, n=46, wind=0.2 + W_, w=300)
        if tq < 1.9:
            v = 0.35 + tq / 1.9
            hawk(c, jx - 230 - 600 * v * v, jy - 330 - 330 * v, 38 * (1 - 0.5 * v), heading=-2.4 - 0.5 * v,
                 flap=0.4 if int(tq * 8) % 2 else -0.3, L=S['L'])
    def fxp(c):
        if W_ > 0.05:
            wind_marks(c, T, alpha=W_)
            B = Boil(T, salt=4)
            for k, (x, y, a) in enumerate(((300, 700, 0.4), (1400, 300, 1.2), (1700, 760, 2.0), (520, 260, 2.6))):
                xx = (x + twos(u) * 900 + k * 100) % (W + 200) - 100
                def lf(cc, x=xx, y=y, a=a):
                    cc.save(); cc.translate(x, y + 40 * math.sin(tq * 4 + k)); cc.rotate(a + tq * 5)
                    smooth_path(cc, B.jp([(0, 10), (-9, 0), (-5, -4), (0, -14), (5, -4), (9, 0)], 0.4)); cc.restore()
                cel(c, lf, (0.92, 0.48, 0.16), (0.70, 0.28, 0.10), (-0.5, -0.86), off=3, lw=2)
    return frame2('noon', (1350, 470, 1.25), chars, u, T, fx_post=fxp, ccam=(1440, 820, 1.9), blur_bg=1.4)

def C8(u, T):
    return motion.c8(u + 0.3)

def C9(u, T):          # 8 s  montage of three gifts
    k = min(2, int(u / (8 / 3)))
    v = u - k * 8 / 3
    vq = twos(v)
    key = ('noon', 'autumn', 'autumn')[k]
    kind = ('kaki', 'acorn', 'leaf')[k]
    target = (0.3, 0.55, 0.85)[k]
    breeze = wind_level(vq, [(1.45, 2.3)]) * 0.45
    hat_down = K(v, [(0.0, (0.0, 0.3, 0.55)[k]), (1.55, target, 0.3)])
    head_turn = K(v, [(0.0, (0.0, -0.2, -0.4)[k]), (1.6, (-0.2, -0.4, -0.6)[k], 0.3)])
    pal = jpal(key)
    pocket = k + (1 if vq >= 1.0 else 0)
    def chars(c, S):
        jx, jy = JI_POS
        o = jiibi(c, jx, jy, 1.0, dict(flapL=-0.3, flapR=-0.25, wind=breeze, hat_down=hat_down, head_turn=head_turn,
                                     head_tilt=-6 * (k + 1) * (0.5 + 0.5 * (vq > 1.6)), pocket=pocket,
                                     leaf=1.0 if (k == 2 and vq > 1.9) else 0.0), t=T, L=S['L'], pal=pal)
        hdx, hdy = c.device_to_user(*o['head'])
        px, py = c.device_to_user(*o['pocket'])
        sx, sy = hdx + 33, hdy + 42
        if vq < 0.8:
            w = vq / 0.8
            x = lerp(px + 260, px + 14, w); y = lerp(py - 120, py - 16, w) - 40 * math.sin(math.pi * w)
            kongi(c, x, y, 10, dict(face=-1, wing=1.0 if int(vq * 12) % 2 else 0.2, feet=0, tilt=8), t=T, L=S['L'], pal=kpal(key))
            gift(c, x - 13, y - 14, kind, S['L'], T, 0.9)
        elif vq < 1.15:
            kongi(c, px + 14, py - 16, 10, dict(face=-1, wing=1.0 if int(vq * 12) % 2 else 0.5, feet=0, tilt=24), t=T, L=S['L'],
                  pal=kpal(key))
            if vq < 1.0:
                gift(c, px + 1, py - 4 + 30 * (vq - 0.8), kind, S['L'], T, 0.9)
        elif vq < 1.45:
            w = (vq - 1.15) / 0.3
            kongi(c, lerp(px + 14, sx, w), lerp(py - 16, sy, w) - 30 * math.sin(math.pi * w), 10,
                  dict(face=-1, wing=1.0 if int(vq * 12) % 2 else 0.3, feet=0), t=T, L=S['L'], pal=kpal(key))
        else:
            rub = math.sin(vq * 14) if 1.5 < vq < 1.9 else 0.0
            kongi(c, sx - 3 * rub, sy, 10, dict(face=-1, puff=1.4, tilt=-10 + 7 * rub + 14 * (vq > 2.0), blink=1 if 1.5 < vq < 1.9 else 0),
                  t=T, L=S['L'], pal=kpal(key))
        if k == 2 and 1.45 < vq < 1.9:
            w = (vq - 1.45) / 0.45
            lx = hdx + 160 * (1 - w) + 12; ly = hdy - 60 * (1 - w) + 21 + 30 * math.sin(w * 6)
            gift(c, lx, ly, 'leaf', S['L'], T, 1.0)
    def fxp(c):
        if breeze > 0.05:
            wind_marks(c, T, alpha=breeze)
    grade = GRADE[key] if k < 2 else ((0.04, 0.02, 0.02), (1.06, 0.98, 0.90), 1.08, 1.0)
    return frame2(key, (1250, 520, 1.6), chars, u, T, fx_post=fxp, ccam=(1505, 790, 3.4), blur_bg=3.0, grade=grade)

def C10(u, T):         # 6 s  sunset ELS, the two of them
    tq = twos(u)
    cx = 1160 + 70 * ss(tq / 6)
    pal = jpal('sunset')
    def chars(c, S):
        jx, jy = JI_POS
        o = jiibi(c, jx, jy, 1.0, dict(wind=0.18, goreum_wind=0.2 + 0.1 * math.sin(tq * 2), pocket=3, head_tilt=-3), t=T, L=S['L'],
                  pal=pal)
        hdx, hdy = c.device_to_user(*o['head'])
        kongi(c, hdx + 33, hdy + 42, 10, dict(face=-1, puff=1.35, blink=1 if 3.0 < tq < 3.15 else 0), t=T, L=S['L'], pal=kpal('sunset'))
    def fxp(c):
        geese(c, T, 300 + 0 * u, 240, n=9, s=10)
    return frame2('sunset', (cx, 600, 0.9), chars, u, T, fx_post=fxp)

def C11(u, T):         # 5 s  late-autumn rain: the hat blows away; Kongi goes after it
    tq = twos(u)
    G = [(1.0, 2.7)]
    W_ = wind_level(tq, G)
    flapR = K(u, [(0.0, -0.3), (1.06, 0.85, 0.2), (2.7, -0.45, 0.25), (2.95, -0.3, 0.15)])
    flapL = K(u, [(0.0, -0.3), (1.1, 0.8, 0.2), (2.7, -0.4, 0.25), (3.0, -0.3, 0.15)])
    pal = jpal('rain')
    hat_off = tq >= 1.2
    def chars(c, S):
        jx, jy = JI_POS
        o = jiibi(c, jx, jy, 1.0, dict(flapL=flapL, flapR=flapR, wind=W_, billow=W_, hat_on=0.0 if hat_off else 1.0, pocket=3,
                                     hat_tilt=14 * W_, head_tilt=5 * W_), t=T, L=S['L'], pal=pal)
        hdx, hdy = c.device_to_user(*o['head'])
        if hat_off and tq < 2.6:
            v = (tq - 1.2) / 1.4
            hat_at(c, hdx + 700 * v, hdy - 62 - 120 * math.sin(math.pi * min(1, v * 1.3)) + 60 * v, 1.0, 14 + 540 * v, T, S['L'], pal=pal)
        if tq < 3.0:
            kongi(c, hdx + 33, hdy + 42, 10, dict(face=1 if tq > 1.3 else -1, puff=1.4 if tq < 1.3 else 1.25,
                                                  open_beak=0.8 if 1.3 < tq < 1.8 else 0, tilt=-10 + 30 * W_), t=T, L=S['L'],
                  pal=kpal('rain'))
        elif tq < 4.2:
            v = (tq - 3.0) / 1.2
            kongi(c, hdx + 33 + 600 * v, hdy + 42 - 200 * v, 10, dict(face=1, wing=1.0 if int(tq * 12) % 2 else 0.1, feet=0, tilt=-10),
                  t=T, L=S['L'], pal=kpal('rain'))
    def fxp(c):
        rain_fx(c, T, 0.65)
        if W_ > 0.05:
            wind_marks(c, T, alpha=W_ * 0.6)
    return frame2('rain', (1350, 470, 1.25), chars, u, T, fx_post=fxp, ccam=(1440, 800, 1.9), blur_bg=1.4)

def C12(u, T):         # 6 s  Kongi drags the hat home; the crooked hat, panting
    tq = twos(u)
    if tq < 3.2:
        # tracking shot along the stubble: the hat lurches on each tug
        pulls = int(tq / 0.5)
        frac = (tq % 0.5)
        hx = 900 + pulls * 34 + (34 if frac > 0.17 else (17 if frac > 0.08 else 0))
        hy = 1150
        sq = 0.8 if 0.0 <= frac < 0.09 else (1.1 if frac < 0.17 else 1.0)
        def chars(c, S):
            hat_at(c, hx, hy, 1.0, -6 + 4 * math.sin(pulls * 1.7), T, S['L'], pal=jpal('rain'))
            kongi(c, hx + 62, hy + 2, 11, dict(face=-1, squash=sq, open_beak=0.7, tilt=-22 if frac < 0.17 else -12, puff=0.95,
                                               wing=0.5 if frac < 0.17 else 0.0), t=T, L=S['L'], pal=kpal('rain'))
            B = Boil(T, salt=19)
            for q in range(3):                       # scrape marks
                inkline(c, B.jp([(hx - 120 - q * 50, hy + 10), (hx - 70 - q * 50, hy + 12)], 0.4), 2.0, (0.30, 0.26, 0.22), 0.5)
        camx = 900 + tq / 3.2 * 110 + 30
        cp = frame2('rain', (lerp(1000, 1060, tq / 3.2), 1000, 2.2), chars, u, T, ccam=(camx + 20, 1110, 3.2), blur_bg=2.2,
                    grade=((0.02, 0.02, 0.03), (1.0, 1.0, 1.0), 0.95, 1.0))
        return cp
    v = tq - 3.2
    pant = int(v * 6) % 2
    breeze = wind_level(v, [(1.4, 2.2)]) * 0.35
    def chars(c, S):
        jx, jy = JI_POS
        o = jiibi(c, jx, jy, 1.0, dict(hat_tilt=17 + 4 * breeze, hat_down=0.2, pocket=3, wind=breeze, flapR=K(v, [(0, -0.25), (1.45, -0.05, 0.3), (2.3, -0.2, 0.3)]),
                                     head_tilt=-4), t=T, L=S['L'], pal=jpal('rain'))
        hdx, hdy = c.device_to_user(*o['head'])
        kongi(c, hdx + 33, hdy + 42, 10, dict(face=-1, open_beak=0.8 * pant if v < 1.6 else 0, squash=1.0 + 0.05 * pant if v < 1.6 else 1.0,
                                              puff=0.95 if v < 1.6 else 1.35, blink=1 if v > 2.0 else 0, tilt=-6), t=T, L=S['L'],
              pal=kpal('rain'))
    return frame2('rain', (1350, 520, 1.6), chars, u, T, ccam=(1505, 760, 3.3), blur_bg=2.6,
                  grade=((0.03, 0.02, 0.03), (1.02, 0.99, 0.96), 0.95, 1.0))

def collar_kongi(kp, t, L, blink=1, size=9, breath=False):
    def fn(cc):
        kongi(cc, -6, -214, size, dict(face=1, puff=1.35, blink=blink, tilt=-8), t=t, L=L, pal=kp)
        def flap(c2):
            smooth_path(c2, [(-23, -221), (-12, -216), (2, -219), (14, -224), (17, -204), (-21, -203)])
        cel(cc, flap, JI['jacket'], JI['jacket_s'], L, off=4, lw=2.2)
    return fn

def C13(u, T):         # 5 s  frost: ECU on the frosted button eye, pan down to Kongi in the collar
    tq = twos(u)
    o0 = jpts(dict(frost=1.0, pocket=3))
    e = o0['eyeL']; ch = o0['chest']
    w = ss(min(1, max(0, (tq - 1.8) / 1.6)))
    ccam = (lerp(e[0] + 4, ch[0] - 6, w), lerp(e[1], ch[1] - 18, w), lerp(13.0, 5.6, w))
    pal = jpal('frost')
    def chars(c, S):
        jx, jy = JI_POS
        jiibi(c, jx, jy, 1.0, dict(frost=1.0, pocket=3, hat_tilt=12, hat_down=0.15), t=T, L=S['L'], pal=pal,
              chest_fn=collar_kongi(kpal('frost'), T, S['L'], blink=0 if 3.4 < tq < 4.3 else 1))
        rng = np.random.default_rng(2)
        hx, hy = jx, jy - 278
        for _ in range(26):                                     # rime on the burlap
            x = hx + rng.uniform(-28, 28); y = hy + rng.uniform(-26, 22)
            c.arc(x, y, rng.uniform(0.5, 1.1), 0, TAU); fillc(c, (0.95, 0.97, 1.0), 0.8)
        ph = (tq % 1.3)
        if tq > 3.2 and ph < 0.6:                              # Kongi's breath
            bx, by = jx + 4, jy - 228
            for q in range(3):
                c.arc(bx + 6 + ph * 20 + q * 4, by - 4 - ph * 16 - q * 3, 2.0 + ph * 5, 0, TAU)
                fillc(c, (0.96, 0.97, 1.0), 0.5 * (1 - ph / 0.6))
    def fxp(c):
        if tq < 2.0:
            sx = W / 2 - 26; sy = H / 2 - 40
            sparkles(c, T, [(sx, sy), (sx + 60, sy + 30), (sx - 40, sy + 50)], seed=3)
    return frame2('frost', (1450, 600, 2.0), chars, u, T, fx_post=fxp, ccam=ccam, blur_bg=3.0)

def C14(u, T):         # 5 s  dusk, first snow
    tq = twos(u)
    g = GRADE['dusk']
    dim = 1 - 0.12 * tq / 5
    pal = jpal('dusk')
    def chars(c, S):
        jx, jy = JI_POS
        jiibi(c, jx, jy, 1.0, dict(snow=0.35 * tq / 5, pocket=3, hat_tilt=12, hat_down=0.15, frost=0.4), t=T, L=S['L'], pal=pal,
              chest_fn=collar_kongi(kpal('dusk'), T, S['L']))
    def fxp(c):
        snowfall(c, twos(u), 240, 1.35, 70, 3.2, 0.75, seed=4)
    return frame2('dusk', (1280, 620, 0.95), chars, u, T, fx_post=fxp,
                  grade=(g[0], tuple(v * dim for v in g[1]), g[2], g[3]))

# --- the blizzard (wind blows right -> left)
BLZ_SNOW_ANG = math.pi - 0.22

def blz_fx(T, st, speed=1900, alpha=0.8, n=900):
    def fxp(c):
        rng = np.random.default_rng(2)
        x0 = rng.uniform(-300, W + 300, n); y0 = rng.uniform(-200, H + 200, n); d = rng.uniform(0.4, 1.0, n)
        dx, dy = math.cos(BLZ_SNOW_ANG), math.sin(BLZ_SNOW_ANG)
        B = Boil(T, amp=0.8, salt=2)
        for i in range(n):
            x = (x0[i] + dx * speed * d[i] * st) % (W + 600) - 300
            y = (y0[i] + dy * speed * d[i] * st) % (H + 400) - 200
            L_ = 14 * d[i] * (2.5 + 2 * ((i * 7919) % 100) / 100)
            if speed == 0:
                L_ = 3
            pts = B.jp([(x, y), (x + dx * L_ * 0.5, y + dy * L_ * 0.5 - 2), (x + dx * L_, y + dy * L_)], 0.5)
            inkline(c, pts, 1.2 + 3.5 * d[i], (0.90, 0.92, 1.0), alpha * (0.5 + 0.5 * d[i]))
    return fxp

def blz_spin(T):
    def fxpre(c):
        B = Boil(T, amp=3, salt=77)
        tq = twos(T)
        for k in range(4):
            y = 560 + k * 60
            off = W + 600 - ((tq * 900 + k * 400) % (W + 1200))
            pts = B.jp([(off + 600, y + 40), (off + 200, y - 20), (off - 300, y + 10), (off - 700, y - 30)], 1.0)
            bot = [(x, y_ + 70 + 20 * k) for (x, y_) in pts[::-1]]
            smooth_path(c, pts + bot)
            fillc(c, (0.80, 0.84, 0.98), 0.55 * (0.5 - k * 0.1))
    return fxpre

BLZ_POSE = dict(wind=-1.0, billow=0.6, snow=1.0, frost=0.8, lean=-3, pocket=3, hat_tilt=-10, goreum_wind=-1.0, head_tilt=-4)

def C15(u, T):         # 6 s  blizzard: Kongi is torn out of the collar and grabs the left cuff
    tq = twos(u)
    flapL = 0.85 + 0.12 * math.sin(tq * 9)
    flapR = -0.65 + 0.06 * math.sin(tq * 7)
    pal = jpal('blizzard'); kp = kpal('blizzard')
    P = dict(BLZ_POSE, flapL=flapL, flapR=flapR)
    def chars(c, S):
        jx, jy = JI_POS
        L = (-0.9, -0.44)
        o = jiibi(c, jx, jy, 1.0, P, t=T, L=L, pal=pal, chest_fn=collar_kongi(kp, T, L, blink=0) if tq < 0.7 else None)
        snowdrift(c, jx, jy, 1.0, L, T, pal)
        chx, chy = c.device_to_user(*o['chest'])
        cx_, cy_ = c.device_to_user(*o['cuffL'])
        if 0.7 <= tq < 1.3:
            v = (tq - 0.7) / 0.6
            x = lerp(chx - 6, cx_ - 30, v); y = lerp(chy - 24, cy_ - 50, v) - 50 * math.sin(math.pi * v)
            kongi(c, x, y, 11, dict(face=-1, wing=1.0 if int(tq * 12) % 2 else 0.0, feet=0, tilt=-200 * v, open_beak=1.0, puff=1.3), t=T,
                  L=L, pal=kp)
        elif tq >= 1.3:
            sw = math.sin(tq * 19)
            kongi(c, cx_ - 4, cy_ + 20, 11, dict(feet=1, tilt=150 + 18 * sw, puff=1.25, wing=1.0 if int(tq * 12) % 2 else 0.0,
                                                 open_beak=0.6), t=T, L=L, pal=kp)
    cp = frame2('blizzard', (1250, 500, 1.15), chars, u, T, fx_pre=blz_spin(T), fx_post=blz_fx(T, twos(T)), ccam=(1410, 850, 2.0),
                blur_bg=1.0, vig=0.55)
    return cp

THREAD_KEYS = [(0.0, 8), (0.7, 22, 0.1), (1.5, 38, 0.1), (2.3, 54, 0.1), (3.1, 70, 0.1)]

def thread_pts(cx_, cy_, ln, tq, B):
    pts = []
    for i in range(9):
        f = i / 8
        sway = math.sin(tq * 17 + f * 4) * 6 * f
        pts.append((cx_ - ln * 0.75 * f + sway, cy_ + ln * 0.66 * f + sway * 0.5))
    return B.jp(pts, 0.3)

def yarn(c, pts, pal, w=1.0):
    """a strand of the jacket's own yarn: jacket-coloured, outlined like the sleeve, with a twist"""
    inkline(c, pts, 4.2 * w, INK_C, 1.0, taper=False)
    inkline(c, pts, 2.8 * w, pal['jacket'], 1.0, taper=False)
    for i in range(len(pts) - 1):
        (x0, y0), (x1, y1) = pts[i], pts[i + 1]
        inkline(c, [(x0, y0), ((x0 + x1) / 2 + 1.2, (y0 + y1) / 2 + 1.2)], 1.1, pal['jacket_s2'], 0.9, taper=False)

def fray_cuff(c, cx_, cy_, ln, tq, B, pal):
    """the cuff unravels: a bitten-away notch in the hem with knit loops the same blue, the yarn leaving from it"""
    n = 3 + int(min(1.0, ln / 70) * 4)
    for q in range(n):
        a = q * 1.3 + math.sin(tq * 11 + q)
        x = cx_ - 9 + q * 3.2; y = cy_ - 3 + (q % 2) * 2
        lp = B.jp(qcurve((x, y), (x - 3 + 4 * math.cos(a), y + 7 + 2 * math.sin(a)), (x + 3, y + 1), 6), 0.3)
        inkline(c, lp, 2.6, INK_C, 0.9, taper=False)
        inkline(c, lp, 1.5, pal['jacket'], 1.0, taper=False)

def C16(u, T):         # 4 s  ECU: the cuff unravels, Kongi dangles from the thread
    tq = twos(u)
    flapL = 0.85 + 0.12 * math.sin(tq * 9)
    P = dict(BLZ_POSE, flapL=flapL, flapR=-0.65)
    pal = jpal('blizzard'); kp = kpal('blizzard')
    o0 = jpts(dict(BLZ_POSE, flapL=0.85, flapR=-0.65))
    cw = o0['cuffL']
    ln = keys(tq, THREAD_KEYS, 1)
    def chars(c, S):
        jx, jy = JI_POS
        L = (-0.9, -0.44)
        o = jiibi(c, jx, jy, 1.0, P, t=T, L=L, pal=pal)
        cx_, cy_ = c.device_to_user(*o['cuffL'])
        B = Boil(T, salt=33)
        pts = thread_pts(cx_, cy_, ln, tq, B)
        yarn(c, pts, pal)
        fray_cuff(c, cx_, cy_, ln, tq, B, pal)
        ex, ey = pts[-1]
        sw = math.sin(tq * 19)
        kongi(c, ex, ey + 2, 11, dict(feet=1, tilt=160 + 16 * sw, puff=1.2, wing=1.0 if int(tq * 12) % 2 else 0.0, open_beak=0.7), t=T,
              L=L, pal=kp)
    return frame2('blizzard', (1250, 520, 1.6), chars, u, T, fx_pre=blz_spin(T), fx_post=blz_fx(T, twos(T), alpha=0.7, n=600),
                  ccam=(cw[0] - 30, cw[1] + 40, 6.0), blur_bg=2.5, vig=0.6)

SNAP = 0.5
LAND = (JI_POS[0] - 118, JI_POS[1] - 108)

def c17_pose(tq):
    windy = tq < SNAP
    bend = K(tq, [(0.0, 0), (1.4, -8, 0.08), (2.4, -16, 0.08), (3.4, -24, 0.08)], inb=1)
    wrap = step(tq, 3.9, 4.5, 3)
    lean = -3 + (-2 * step(tq, 3.9, 4.5, 3))
    P = dict(BLZ_POSE, wind=-1.0 if windy else 0.0, billow=0.6 if windy else 0.0, goreum_wind=-1.0 if windy else -0.15,
             flapL=(0.85 + 0.12 * math.sin(tq * 9)) if windy else K(tq, [(SNAP, 0.6), (0.62, -0.2, 0.08), (0.75, -1.0, 0.08)]),
             flapR=-0.65 if windy else K(tq, [(SNAP, -0.65), (0.75, -1.0, 0.1)]), bend=bend, wrapL=wrap, lean=lean,
             head_tilt=-4 + bend * 0.5, head_turn=-0.35 * step(tq, 3.4, 3.7, 1), hat_tilt=-10 + 14 * step(tq, 0.6, 1.4, 2))
    return P

def C17(u, T):         # 6 s  the thread snaps, the wind dies; in the silence, he bends
    tq = twos(u)
    P = c17_pose(tq)
    pal = jpal('blizzard'); kp = kpal('blizzard')
    L = (-0.9, -0.44)
    o_full = jpts(dict(BLZ_POSE, flapL=0.85, flapR=-0.65))
    def chars(c, S):
        jx, jy = JI_POS
        peek = tq >= 4.5
        def nestling(cc):
            kongi(cc, -2, -199, 11, dict(puff=1.45, blink=1 if 5.2 < tq < 5.35 else 0, tilt=-16, feet=0), t=T, L=L, pal=kp)
        o = jiibi(c, jx, jy, 1.0, P, t=T, L=L, pal=pal, chest_fn=nestling if peek else None)
        snowdrift(c, jx, jy, 1.0, L, T, pal)
        cx_, cy_ = c.device_to_user(*o['cuffL'])
        B = Boil(T, salt=33)
        if tq < SNAP:
            ln = 70 + 3 * math.sin(tq * 40)
            pts = thread_pts(cx_, cy_, ln, tq, B)
            yarn(c, pts, pal); fray_cuff(c, cx_, cy_, ln, tq, B, pal)
            ex, ey = pts[-1]
            kongi(c, ex, ey + 2, 11, dict(feet=1, tilt=160 + 16 * math.sin(tq * 19), puff=1.2, wing=1.0 if int(tq * 12) % 2 else 0.0,
                                          open_beak=0.8), t=T, L=L, pal=kp)
            return
        # recoiled thread stub
        if tq < 0.9:
            inkline(c, B.jp(qcurve((cx_, cy_), (cx_ - 10, cy_ + 14), (cx_ - 4, cy_ + 22), 6), 0.3), 2.0, (0.20, 0.22, 0.40), 1.0)
        else:
            inkline(c, B.jp(qcurve((cx_, cy_), (cx_ - 3, cy_ + 8), (cx_ + 1, cy_ + 14), 6), 0.3), 2.0, (0.20, 0.22, 0.40), 1.0)
        ex0 = o_full['cuffL'][0] - 52; ey0 = o_full['cuffL'][1] + 48
        if tq < 1.0:
            v = (tq - SNAP) / 0.5
            x = lerp(ex0, LAND[0], v); y = lerp(ey0, LAND[1], v * v)
            kongi(c, x, y, 11, dict(feet=0, tilt=160 + 220 * v, puff=1.2, wing=0.5), t=T, L=L, pal=kp)
        elif tq < 3.9:
            land = tq - 1.0
            sq = 0.75 if land < 0.09 else (1.08 if land < 0.17 else 1.0)
            kongi(c, LAND[0], LAND[1], 11, dict(squash=sq, puff=0.9, tilt=-24, face=1, blink=1 if land > 0.4 else 0,
                                                feet=0), t=T, L=L, pal=kp)
        elif not peek:
            v = step(tq, 3.9, 4.5, 3)
            chx, chy = c.device_to_user(*o['chest'])
            kongi(c, lerp(LAND[0], chx, v), lerp(LAND[1], chy + 2, v), 11, dict(puff=1.0 + 0.4 * v, tilt=-24 + 8 * v, blink=1), t=T, L=L,
                  pal=kp)
    # snow: streams until the snap, then hangs frozen; at 5.0 it begins to fall again, slowly and straight down
    if tq < SNAP:
        fxp = blz_fx(T, twos(T))
    elif tq < 5.0:
        fxp = blz_fx(T, twos(T - u + SNAP), alpha=0.8)
    else:
        st0 = twos(T - u + SNAP)
        def fxp(c):
            blz_fx(T, st0, alpha=0.8 * max(0, 1 - (tq - 5.0) / 0.8))(c)
            snowfall(c, tq - 5.0, 260, 1.5, 60, 3.4, 0.8 * min(1, (tq - 5.0) / 0.5), seed=7)
    return frame2('blizzard', (1250, 500, 1.15), chars, u, T, fx_pre=blz_spin(T) if tq < SNAP else None, fx_post=fxp,
                  ccam=(1415, 845, 2.2), blur_bg=1.0, vig=0.55,
                  grade=GRADE['blizzard'] if tq < SNAP else ((0.015, 0.015, 0.04), (0.78, 0.82, 1.0), 0.85, 1.05))

# ---------------------------------------------------------------- C17 split (v2): snap -> 17-1 the freezing sparrow -> the reach
LAND2 = (1366, 906)
C17_GRADE = ((0.015, 0.015, 0.04), (0.78, 0.82, 1.0), 0.85, 1.05)

def frozen_snow(T, u):
    """the blizzard frozen at the instant of the snap (snow-time held)"""
    return blz_fx(T, twos(T - u + SNAP), alpha=0.8)

def C17a(u, T):        # 2 s  the thread snaps; Kongi drops into the snow; the world holds its breath
    tq = twos(u)
    pal = jpal('blizzard'); kp = kpal('blizzard')
    L = (-0.9, -0.44)
    windy = tq < SNAP
    P = dict(BLZ_POSE, wind=-1.0 if windy else 0.0, billow=0.6 if windy else 0.0, goreum_wind=-1.0 if windy else -0.15,
             flapL=(0.85 + 0.12 * math.sin(tq * 9)) if windy else K(tq, [(SNAP, 0.6), (0.62, -0.2, 0.08), (0.75, -0.6, 0.08)]),
             flapR=-0.65 if windy else K(tq, [(SNAP, -0.65), (0.75, -1.0, 0.1)]), lean=-3,
             hat_tilt=-10 + 14 * step(tq, 0.6, 1.4, 2))
    o_full = jpts(dict(BLZ_POSE, flapL=0.85, flapR=-0.65))
    def chars(c, S):
        jx, jy = JI_POS
        o = jiibi(c, jx, jy, 1.0, P, t=T, L=L, pal=pal)
        snowdrift(c, jx, jy, 1.0, L, T, pal)
        cx_, cy_ = c.device_to_user(*o['cuffL'])
        B = Boil(T, salt=33)
        if windy:
            ln = 70 + 3 * math.sin(tq * 40)
            pts = thread_pts(cx_, cy_, ln, tq, B)
            yarn(c, pts, pal); fray_cuff(c, cx_, cy_, ln, tq, B, pal)
            ex, ey = pts[-1]
            kongi(c, ex, ey + 2, 11, dict(feet=1, tilt=160 + 16 * math.sin(tq * 19), puff=1.2, wing=1.0 if int(tq * 12) % 2 else 0.0,
                                          open_beak=0.8), t=T, L=L, pal=kp)
            return
        stub = B.jp(qcurve((cx_, cy_), (cx_ - 10, cy_ + 14), (cx_ - 4, cy_ + 22), 6), 0.3) if tq < 0.9 else \
            B.jp(qcurve((cx_, cy_), (cx_ - 3, cy_ + 8), (cx_ + 1, cy_ + 14), 6), 0.3)
        yarn(c, stub, pal, 0.8)
        ex0 = o_full['cuffL'][0] - 52; ey0 = o_full['cuffL'][1] + 48
        if tq < 1.0:
            v = (tq - SNAP) / 0.5
            kongi(c, lerp(ex0, LAND2[0], v), lerp(ey0, LAND2[1], v * v), 11, dict(feet=0, tilt=160 + 220 * v, puff=1.2, wing=0.5),
                  t=T, L=L, pal=kp)
        else:
            land = tq - 1.0
            sq = 0.72 if land < 0.09 else (1.08 if land < 0.17 else 1.0)
            kongi(c, LAND2[0], LAND2[1], 11, dict(squash=sq * 0.84, puff=0.95, tilt=14, face=1, blink=0, feet=0), t=T, L=L, pal=kp)
            if land < 0.3:                                       # a small burst of powder where he hits
                for k in range(7):
                    a = -2.8 + k * 0.42; r = 10 + 60 * land
                    c.arc(LAND2[0] + math.cos(a) * r, LAND2[1] - 4 + math.sin(a) * r * 0.6, 3.2 * (1 - land * 2.5), 0, TAU)
                    fillc(c, (0.92, 0.94, 1.0), 0.9)
    fxp = blz_fx(T, twos(T)) if windy else frozen_snow(T, u)
    return frame2('blizzard', (1250, 500, 1.15), chars, u, T, fx_pre=blz_spin(T) if windy else None, fx_post=fxp,
                  ccam=(1415, 845, 2.2), blur_bg=1.0, vig=0.55, grade=GRADE['blizzard'] if windy else C17_GRADE)

def frost_specks(c, x, y, amt, seed=5):
    rng = np.random.default_rng(seed)
    for k in range(int(18 * amt)):
        a = rng.uniform(-3.0, -0.2); r = rng.uniform(4, 12)
        px, py = x + math.cos(a) * r * 1.2, y - 8 + math.sin(a) * r * 0.7
        c.arc(px, py, 0.35 + 0.3 * rng.random(), 0, TAU); fillc(c, (0.94, 0.97, 1.0), 0.85)

def C17_1(u, T):       # 4 s  CU: Kongi in the snow, too cold to fly; three tries, each weaker; the eyes close
    tq = twos(u)
    kp = kpal('blizzard'); pal = jpal('blizzard')
    L = (-0.9, -0.44)
    tries = [(0.5, 0.75), (1.5, 0.5), (2.5, 0.25)]
    wing = 0.0; lift = 0.0
    for t0, amp in tries:
        if t0 <= tq < t0 + 0.34:
            k = int((tq - t0) * 12)
            wing = amp * (1.0 if k % 2 == 0 else 0.35)
            lift = amp * 3.0 * (1 if k < 2 else 0)
    eyes = 1 if (tq > 3.1 or 2.05 < tq < 2.2) else 0
    def chars(c, S):
        jx, jy = JI_POS
        jiibi(c, jx, jy, 1.0, dict(BLZ_POSE, wind=0.0, billow=0.0, goreum_wind=-0.15, flapL=-0.6, flapR=-1.0, lean=-3, hat_tilt=4),
              t=T, L=L, pal=pal)
        snowdrift(c, jx, jy, 1.0, L, T, pal)
        x, y = LAND2
        kongi(c, x, y - lift, 11, dict(puff=0.95 + 0.06 * math.sin(tq * 3), tilt=14 - 10 * wing, squash=0.84, face=1, blink=eyes, feet=0,
                                     wing=wing, open_beak=0.5 if wing > 0.3 else 0.0), t=T, L=L, pal=kp)
        frost_specks(c, x - 3, y - 4, min(1.0, 0.25 + tq / 3.2))
        # breath: small puffs that get weaker, the last one barely there
        for t0, a in ((0.2, 0.7), (1.2, 0.55), (2.2, 0.35), (3.3, 0.15)):
            if t0 <= tq < t0 + 0.6:
                v = (tq - t0) / 0.6
                c.arc(x + 19 + 10 * v, y - 9 - 5 * v, 1.8 + 3.5 * v, 0, TAU)
                fillc(c, (0.92, 0.95, 1.0), a * (1 - v))
    cp = frame2('blizzard', (1250, 560, 1.7), chars, u, T, fx_post=frozen_snow(T, u), ccam=(LAND2[0] + 6, LAND2[1] - 14, 7.6 + 0.25 * tq / 4),
                blur_bg=3.0, vig=0.7, grade=C17_GRADE)
    return cp

def c17b_pose(tq):
    bend = K(tq, [(0.0, 0), (1.3, -8, 0.08), (2.0, -16, 0.08), (2.7, -24, 0.08)], inb=1)
    reach = K(tq, [(0.0, 0.0), (0.9, 0.0), (1.3, 0.4, 0.08), (2.0, 0.75, 0.08), (2.7, 1.0, 0.08)], inb=1)
    wrap = step(tq, 3.1, 3.7, 3)
    return dict(BLZ_POSE, wind=0.0, billow=0.0, goreum_wind=-0.15, flapL=lerp(-0.6, -1.0, reach), arm_len=1.0 + 0.3 * reach * (1 - wrap),
                flapR=-1.0, bend=bend, wrapL=wrap, lean=-3 - 2 * wrap, hat_tilt=4,
                head_tilt=-4 + bend * 0.5 - 6 * step(tq, 0.5, 0.7, 1), head_turn=-0.35 * step(tq, 0.5, 0.7, 1))

def C17b(u, T):        # 5 s  silence. creak by creak the pole bends, the sleeve reaches down and gathers him in
    tq = twos(u)
    P = c17b_pose(tq)
    pal = jpal('blizzard'); kp = kpal('blizzard')
    L = (-0.9, -0.44)
    def chars(c, S):
        jx, jy = JI_POS
        peek = tq >= 3.7
        def nestling(cc):
            kongi(cc, -2, -199, 11, dict(puff=1.45, blink=1 if (tq < 4.3 or 4.6 < tq < 4.75) else 0, tilt=-16, feet=0), t=T, L=L, pal=kp)
        o = jiibi(c, jx, jy, 1.0, P, t=T, L=L, pal=pal, chest_fn=nestling if peek else None)
        snowdrift(c, jx, jy, 1.0, L, T, pal)
        if tq < 3.1:
            kongi(c, LAND2[0], LAND2[1], 11, dict(puff=0.95, tilt=14, squash=0.84, face=1, blink=1, feet=0), t=T, L=L, pal=kp)
            frost_specks(c, LAND2[0] - 3, LAND2[1] - 4, 1.0)
        elif not peek:
            v = step(tq, 3.1, 3.7, 3)
            chx, chy = c.device_to_user(*o['chest'])
            kongi(c, lerp(LAND2[0], chx, v), lerp(LAND2[1], chy + 2, v), 11, dict(puff=0.95 + 0.5 * v, tilt=lerp(14, -16, v), blink=1),
                  t=T, L=L, pal=kp)
    if tq < 4.0:
        fxp = frozen_snow(T, u)
    else:
        st0 = twos(T - u + SNAP)
        def fxp(c):
            blz_fx(T, st0, alpha=0.8 * max(0, 1 - (tq - 4.0) / 0.6))(c)
            snowfall(c, tq - 4.0, 260, 1.5, 60, 3.4, 0.8 * min(1, (tq - 4.0) / 0.5), seed=7)
    return frame2('blizzard', (1250, 500, 1.15), chars, u, T, fx_post=fxp, ccam=(1405, 850, 2.2), blur_bg=1.0, vig=0.55, grade=C17_GRADE)

_HARM = {}
def harmony_img():
    if 'img' not in _HARM:
        fn = 'cache/harmony.png'
        if os.path.exists(fn):
            _HARM['img'] = np.array(Image.open(fn))
        else:
            import cv2
            from painter import paint
            raw = C17(5.9, 90 - 0.1).finish(0)
            bar = (raw.shape[0] - H) // 2
            src = raw[bar:bar + H].astype(np.float32) / 255
            src = cv2.resize(src, (2400, 1300), interpolation=cv2.INTER_CUBIC)
            out = paint(src, radii=(14, 7, 3.5, 1.8), thresh=(0, 0.05, 0.08, 0.11), maxlen=(8, 7, 5, 3), seed=12, detail=0.55)
            rgba = np.concatenate([np.clip(out * 255, 0, 255).astype(np.uint8), np.full((1300, 2400, 1), 255, np.uint8)], -1)
            Image.fromarray(rgba).save(fn)
            _HARM['img'] = rgba
    return _HARM['img']

def C18(u, T):         # 5 s  the harmony frame: the whole picture repainted as one gouache, slow push
    tq = twos(u)
    z = 0.8 + 0.07 * ss(tq / 5)
    img = PaintedImg(harmony_img())
    def fxp(c):
        snowfall(c, 0.8 + tq, 200, 1.5, 50, 3.0, 0.65, seed=7)
    cp = frame2('blizzard', (1200, 650, z), None, u, T, fx_post=fxp, bgimg=img, fore=False, vig=0.5,
                grade=((0.02, 0.02, 0.04), (1.0, 1.0, 1.0), 1.0, 1.0))
    return cp

MOON_POSE = dict(bend=-24, wrapL=1.0, lean=-5, head_tilt=-16, head_turn=-0.35, snow=1.0, frost=0.6, pocket=3, hat_tilt=4,
                 flapR=-1.0, goreum_wind=-0.1)

def C19(u, T):         # 7 s  moonlit, snow-covered, still bent
    tq = twos(u)
    z = 0.92 + 0.06 * ss(tq / 7)
    pal = jpal('moon'); kp = kpal('moon')
    def chars(c, S):
        jx, jy = JI_POS
        def nestling(cc):
            kongi(cc, -2, -199, 11, dict(puff=1.5, blink=1, tilt=-16, feet=0), t=T, L=S['L'], pal=kp)
        jiibi(c, jx, jy, 1.0, MOON_POSE, t=T, L=S['L'], pal=pal, chest_fn=nestling)
        snowdrift(c, jx, jy, 1.0, S['L'], T, dict(snow=S['snow'][2], snow_s=S['snow'][1]))
    rng = np.random.default_rng(8)
    pts = [(rng.uniform(0, W), rng.uniform(H * 0.6, H)) for _ in range(40)]
    def fxp(c):
        sparkles(c, T, pts, col=(0.92, 0.96, 1.0), seed=8)
    return frame2('moon', (1300, 650, z), chars, u, T, fx_post=fxp)

HAT_REST = (1104, 990)                  # v2: he falls to the LEFT (the side he bent toward); hat and nest by his head

def C20(u, T):         # 12 s  timelapse: moon -> thaw -> spring
    tq = twos(u)
    if tq < 4.0:
        key, mix = 'moon', ('thaw', step(tq, 0.5, 4.0, 7))
    elif tq < 8.0:
        key, mix = 'thaw', None
    else:
        key, mix = 'thaw', ('spring', step(tq, 8.0, 11.0, 6))
    phase = (tq * (2.0 if tq < 6 else 1.2))
    night = (int(phase * 2) % 2 == 0) and tq < 9.0
    snow = 1.0 - step(tq, 0.5, 5.0, 9)
    hs = 1.0 - step(tq, 1.0, 6.0, 10)
    wrap = 1.0 - step(tq, 4.6, 5.2, 3)
    opened = step(tq, 5.0, 5.8, 3)                       # the sleeve opens and stays reaching after him
    gust = -wind_level(tq, [(6.2, 8.4)]) * 0.8           # from the right, into the bend
    top = K(tq, [(0.0, 0.0), (7.0, 0.10, 0.05), (7.3, 0.32, 0.05), (7.55, 0.68, 0.05), (7.75, 1.04, 0.05), (7.9, 0.97, 0.05),
                 (8.05, 1.0, 0.05)], inb=1)
    hat_on = tq < 7.3
    pal = tint_pal(JI, mul=(0.96, 0.96, 0.98))
    def chars(c, S):
        jx, jy = JI_POS
        L = S['L']
        def nestling(cc):
            kongi(cc, -2, -199, 11, dict(puff=1.4, blink=1 if tq < 4.0 else 0, tilt=-16, feet=0), t=T, L=L)
        P = dict(MOON_POSE, snow=snow, frost=0.6 * snow, wrapL=wrap, topple=top, topple_dir=-1, hat_on=1.0 if hat_on else 0.0,
                 wind=gust, billow=-gust * 0.5, flapL=lerp(lerp(-0.2, 0.55, opened) + 0.3 * gust, -0.9, top), flapR=lerp(-1.0 - 0.3 * gust, 0.05, top),
                 head_tilt=-16 + 8 * opened, head_turn=-0.35 + 0.2 * opened, arm_len=1.0 - 0.3 * top)
        o = jiibi(c, jx, jy, 1.0, P, t=T, L=L, pal=pal, chest_fn=nestling if wrap > 0.5 else None)
        sp = SEASONS['moon']['snow']
        snowdrift(c, jx, jy, hs, L, T, dict(snow=sp[2], snow_s=sp[1]) if tq < 3 else dict(snow=(0.86, 0.88, 0.94), snow_s=(0.66, 0.70, 0.82)))
        if 4.9 <= tq < 6.2:                                  # Kongi flies out of the opened sleeve, up and away to the right
            v = (tq - 4.9) / 1.3
            kongi(c, jx - 40 + 520 * v, jy - 200 - 380 * v, 11, dict(wing=1.0 if int(tq * 12) % 2 else 0.1, feet=0, face=1), t=T, L=L)
        if not hat_on:
            if tq < 8.2:
                v = (tq - 7.3) / 0.9
                hx = lerp(jx - 330, HAT_REST[0], v); hy = lerp(jy - 120, HAT_REST[1], v) - 50 * math.sin(math.pi * v)
                hat_at(c, hx, hy, 1.0, lerp(-70, 0, v), T, L, pal=pal)
            else:
                stage = step(tq, 9.6, 11.8, 5)
                nest_in_hat(c, HAT_REST[0], HAT_REST[1], L, T, stage=stage)
                if 9.2 < tq < 12:
                    for k, fem in enumerate((False, True)):
                        ph = (tq * 1.4 + k * 0.5) % 1.0
                        if ph < 0.5:
                            x = HAT_REST[0] + (-1 if k else 1) * (300 - 560 * ph); y = HAT_REST[1] - 40 - 260 * (0.5 - ph)
                            kongi(c, x, y, 10, dict(face=1 if k else -1, wing=1.0 if int(tq * 12) % 2 else 0.1, feet=0), t=T, L=L,
                                  pal=KO_F if fem else KO)
                            inkline(c, [(x - 8, y - 18), (x + 10, y - 16)], 1.8, (0.42, 0.30, 0.18), 1.0)
                        else:
                            kongi(c, HAT_REST[0] + (-26 if k else 24), HAT_REST[1] - 36, 10, dict(face=1 if k else -1, tilt=10), t=T, L=L,
                                  pal=KO_F if fem else KO)
        if top > 0.95:
            grass_front(c, jx, jy, L, T, spring=tq > 9.5)
            hdx, hdy = c.device_to_user(*o['head'])
            sprouts(c, (jx - 40, jy - 18), (hdx + 30, hdy + 10), 22, step(tq, 8.6, 11.6, 6), L, T)
    def fxp(c):
        if gust < -0.05:
            c.save(); c.translate(W, 0); c.scale(-1, 1); wind_marks(c, T, alpha=-gust * 0.7); c.restore()
    cp = frame2(key, (1400, 770, 1.05), chars, u, T, mix=mix, fx_post=fxp, fore=tq > 9.0)
    if night:
        cp.gain = tuple(g * f for g, f in zip(cp.gain, (0.70, 0.74, 0.92)))
    return cp

def toppled_pose(t, gust=0.0):
    """v2: fallen to the left, still bent at the waist; the opened left sleeve lies reaching out"""
    return dict(topple=1.0, topple_dir=-1, bend=-24, lean=-5, hat_on=0.0, pocket=3, flapL=-0.9, flapR=0.05 + 0.6 * gust,
                arm_len=0.7, wind=gust, billow=gust * 0.4, head_tilt=-8, head_turn=-0.15)

def grass_front(c, jx, jy, L, t, spring=True, seed=6):
    """tufts in front of the fallen body so he lies IN the grass"""
    B = Boil(t, amp=0.4, salt=27)
    rng = np.random.default_rng(seed)
    base = (0.40, 0.62, 0.26) if spring else (0.46, 0.44, 0.28)
    hi = (0.74, 0.86, 0.40) if spring else (0.66, 0.62, 0.40)
    for k in range(210):
        x = jx - 600 + rng.random() * 760
        y = jy - 4 + rng.random() * 14
        h_ = 6 + 10 * rng.random()
        sw = 3 * math.sin(twos(t) * 2 + k)
        inkline(c, B.jp(qcurve((x, y), (x + 1 + sw * 0.3, y - h_ * 0.6), (x + rng.uniform(-5, 5) + sw, y - h_), 4), 0.2), 2.2,
                lc(base, hi, rng.random()), 0.95)

def sapling(c, o, L, T, grow=1.0):
    px, py = c.device_to_user(*o['pocket'])
    B = Boil(T, salt=8)
    h_ = 60 * grow
    inkline(c, B.jp(qcurve((px, py), (px + 4, py - h_ * 0.5), (px + 2, py - h_)), 0.3), 4, (0.42, 0.30, 0.20), 1.0)
    for (dx, dy, a) in ((-12, -0.95, -0.6), (12, -1.02, 0.5), (0, -1.15, 0.0)):
        def lf(cc, dx=dx, dy=dy, a=a):
            cc.save(); cc.translate(px + dx * grow, py + dy * h_); cc.rotate(a); cc.scale(grow, grow)
            smooth_path(cc, [(0, 6), (-7, -2), (0, -14), (7, -2)]); cc.restore()
        cel(c, lf, (0.52, 0.76, 0.32), (0.34, 0.56, 0.22), L, off=2, lw=1.8)

def C21(u, T):         # 4 s  CU: the nest in the hat, three chicks; the persimmon sapling from the pocket
    tq = twos(u)
    def chars(c, S):
        jx, jy = JI_POS
        L = S['L']
        o = jiibi(c, jx, jy, 1.0, toppled_pose(T), t=T, L=L)
        grass_front(c, jx, jy, L, T)
        sprouts(c, (jx - 40, jy - 18), (jx - 250, jy - 30), 22, 1.0, L, T)
        sapling(c, o, L, T)
        nest_in_hat(c, HAT_REST[0], HAT_REST[1], L, T, stage=1.0, chicks=3)
        feed = 1.2 < tq < 2.2
        kongi(c, HAT_REST[0] - 26, HAT_REST[1] - 36 + (6 if feed else 0), 10, dict(face=1, tilt=40 if feed else 8), t=T, L=L)
        kongi(c, HAT_REST[0] + 24, HAT_REST[1] - 36, 10, dict(face=-1, tilt=-6, puff=1.3, blink=1 if 2.8 < tq < 2.95 else 0), t=T, L=L,
              pal=KO_F)
        butterfly(c, HAT_REST[0] - 110 + 30 * math.sin(tq * 1.5), HAT_REST[1] - 110 + 20 * math.cos(tq * 2.1), T, 0.9)
    return frame2('spring', (1180, 930, 3.2), chars, u, T, blur_bg=1.2, fore=False)

C22_LEN, C22_CREDIT = 11.0, 4.4
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '_shared'))
import credit_overlay

def C22(u, T):         # 7 s  spring ELS, C1 framing; the raised sleeve waves; title
    tq = twos(u)
    gust = wind_level(tq, [(0.8, 2.4), (3.6, 5.2), (7.4, 9.0)]) * 0.6
    def chars(c, S):
        jx, jy = JI_POS
        L = S['L']
        o = jiibi(c, jx, jy, 1.0, toppled_pose(T, gust), t=T, L=L)
        grass_front(c, jx, jy, L, T)
        sprouts(c, (jx - 40, jy - 18), (jx - 250, jy - 30), 22, 1.0, L, T)
        sapling(c, o, L, T)
        nest_in_hat(c, HAT_REST[0], HAT_REST[1], L, T, stage=1.0, chicks=3)
        kongi(c, HAT_REST[0] - 26, HAT_REST[1] - 36, 10, dict(face=1, tilt=8), t=T, L=L)
        ph = (tq * 0.5) % 1.0
        kongi(c, HAT_REST[0] + 300 - 700 * ph, HAT_REST[1] - 260 + 80 * math.sin(ph * 6), 10,
              dict(face=-1, wing=1.0 if int(tq * 12) % 2 else 0.1, feet=0), t=T, L=L, pal=KO_F)
        for k in range(3):
            butterfly(c, 1200 + k * 300 + 40 * math.sin(tq * 1.3 + k), 860 - k * 30 + 25 * math.cos(tq * 1.7 + k), T + k, 0.9,
                      col=((0.98, 0.86, 0.30), (1.0, 0.98, 0.94), (0.98, 0.70, 0.40))[k])
    def fxp(c):
        if gust > 0.05:
            wind_marks(c, T, alpha=gust * 0.6)
        title_card(c, min(1, max(0, (u - 2.2) / 1.0)), 0.0)
    cp = frame2('spring', (1330, 700, 0.88), chars, u, T, fx_post=fxp)
    if u >= C22_CREDIT:
        cp.post.append(lambda img, u=u: credit_overlay.apply(img, u - C22_CREDIT, 'left'))
    cp.fade *= min(1.0, max(0.0, (C22_LEN - u) / 1.2))
    return cp

CUTS = [(C1, 7), (C2, 5), (C3, 5), (C4, 6), (C5, 4), (C6, 4), (C6_1, 3), (C7, 4), (C8, 4), (C9, 8), (C10, 6), (C11, 5), (C12, 6), (C13, 5),
        (C14, 5), (C15, 6), (C16, 4), (C17a, 2), (C17_1, 4), (C17b, 5), (C18, 5), (C19, 7), (C20, 12), (C21, 4), (C22, C22_LEN)]
STARTS = []
_a = 0.0
for fn, d in CUTS:
    STARTS.append(_a); _a += d
TOTAL = _a
NF = int(round(TOTAL * FPS))

def comp_at(T):
    for (fn, d), a in zip(CUTS, STARTS):
        if T < a + d:
            return fn(T - a, T)
    fn, d = CUTS[-1]
    return fn(d - 1e-3, TOTAL - 1e-3)

def render_frame(i):
    return comp_at(i / FPS).finish(i)

def chunk(args):
    i0, i1, path = args
    cmd = ['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{eng.W}x{eng.OH}', '-r', str(FPS),
           '-i', '-', '-c:v', 'libx264', '-preset', 'medium', '-crf', '17', '-pix_fmt', 'yuv420p', path]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    for i in range(i0, i1):
        p.stdin.write(render_frame(i).tobytes())
    p.stdin.close(); p.wait()
    return path

if __name__ == '__main__':
    from PIL import Image
    if sys.argv[1] == 'still':                      # film.py still C5:1.5 C6:2 ...
        for a in sys.argv[2:]:
            name, lt = a.split(':')
            idx = int(name[1:]) - 1
            T = STARTS[idx] + float(lt)
            Image.fromarray(render_frame(int(round(T * FPS)))).save(f'test/f_{name}_{float(lt):04.1f}.png'); print(a, flush=True)
    elif sys.argv[1] == 'range':                    # film.py range t0 t1 out.mp4
        import multiprocessing as mp
        t0, t1, out = float(sys.argv[2]), float(sys.argv[3]), sys.argv[4]
        i0, i1 = int(t0 * FPS), int(t1 * FPS)
        nproc = int(os.environ.get('NPROC', '2'))
        os.makedirs('chunks', exist_ok=True)
        edges = np.linspace(i0, i1, nproc * 3 + 1).astype(int)
        jobs = [(int(edges[k]), int(edges[k + 1]), f'chunks/{os.path.basename(out)}_{k:03d}.mp4') for k in range(len(edges) - 1)]
        st = time.time()
        with mp.Pool(nproc) as pool:
            paths = sorted(pool.map(chunk, jobs))
        open('chunks/list.txt', 'w').write(''.join(f"file '{os.path.basename(p)}'\n" for p in paths))
        subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'concat', '-safe', '0', '-i', 'chunks/list.txt', '-c', 'copy', out])
        print('done', out, time.time() - st)
