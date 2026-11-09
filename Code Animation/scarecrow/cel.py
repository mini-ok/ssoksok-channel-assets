# -*- coding: utf-8 -*-
"""〈허수아비의 겨울〉 -- cel layer: timing on twos, line boil, colored held lines, hard shadow tones, characters, film post."""
from eng import *
import math
import numpy as np
import cairo
import cv2

INK_C = (0.17, 0.20, 0.33)      # cool held line (shadow side)
INK_W = (0.52, 0.30, 0.14)      # warm held line (light side)

# ------------------------------------------------------------------ timing
def twos(t, rate=12.0):
    return math.floor(t * rate + 1e-6) / rate

def threes(t):
    return twos(t, 8.0)

def keys(t, ks, inb=2):
    """key-pose timing: holds on keys, at most `inb` stepped inbetweens per transition.
    ks: list of (time, value[, dur]) - value held from time; transition takes dur (default 0.25s)"""
    v = ks[0][1]
    for k in ks:
        t0, val = k[0], k[1]
        dur = k[2] if len(k) > 2 else 0.25
        if t < t0:
            break
        prev = v
        if t < t0 + dur:
            u = (t - t0) / dur
            step = math.floor(u * (inb + 1)) / (inb + 1)        # stepped inbetweens
            u2 = step * step * (3 - 2 * step) if inb > 0 else 0
            if isinstance(val, tuple):
                return tuple(a + (b - a) * u2 for a, b in zip(prev, val))
            return prev + (val - prev) * u2
        v = val
    return v

# ------------------------------------------------------------------ boil
class Boil:
    def __init__(self, t, amp=0.7, rate=12.0, salt=0):
        self.rng = np.random.default_rng(int(math.floor(t * rate)) * 7919 + salt)
        self.amp = amp

    def j(self, x, y, a=1.0):
        return (x + self.rng.normal(0, self.amp * a), y + self.rng.normal(0, self.amp * a))

    def jp(self, pts, a=1.0):
        return [self.j(x, y, a) for (x, y) in pts]

# ------------------------------------------------------------------ cel primitive
def smooth_path(c, pts, close=True):
    """Catmull-Rom through points"""
    n = len(pts)
    if n < 3:
        poly(c, pts, close)
        return
    P = pts + pts[:2] if close else [pts[0]] + pts + [pts[-1]]
    c.move_to(*P[1] if close else P[1])
    rng_ = range(1, n + (1 if close else -1)) if close else range(1, n)
    for i in rng_:
        p0, p1, p2, p3 = P[i - 1], P[i], P[i + 1], P[(i + 2) % len(P)] if close else P[min(i + 2, len(P) - 1)]
        c1 = (p1[0] + (p2[0] - p0[0]) / 6, p1[1] + (p2[1] - p0[1]) / 6)
        c2 = (p2[0] - (p3[0] - p1[0]) / 6, p2[1] - (p3[1] - p1[1]) / 6)
        c.curve_to(c1[0], c1[1], c2[0], c2[1], p2[0], p2[1])
    if close:
        c.close_path()

# ------------------------------------------------------------------ hand-drawn cel (v2)
_FRAME = [0]

def set_frame(t, rate=12.0):
    """line boil changes on twos: call once per frame with the shot time"""
    _FRAME[0] = int(math.floor(t * rate + 1e-6))

def _flatten(c, path):
    c.new_path()
    path(c)
    data = c.copy_path_flat()
    c.new_path()
    polys, cur = [], []
    for kind, pts in data:
        if kind == cairo.PATH_MOVE_TO:
            if len(cur) > 2:
                polys.append(cur)
            cur = [pts]
        elif kind == cairo.PATH_LINE_TO:
            cur.append(pts)
        elif kind == cairo.PATH_CLOSE_PATH:
            if len(cur) > 2:
                polys.append(cur)
            cur = []
    if len(cur) > 2:
        polys.append(cur)
    return polys

def _resample(pts, step):
    P = np.array(pts + [pts[0]], dtype=np.float64)
    seg = np.hypot(*np.diff(P, axis=0).T)
    cum = np.concatenate([[0], np.cumsum(seg)])
    tot = cum[-1]
    if tot < step * 4:
        return np.array(pts, dtype=np.float64), tot
    n = max(8, int(tot / step))
    s_ = np.linspace(0, tot, n, endpoint=False)
    return np.stack([np.interp(s_, cum, P[:, 0]), np.interp(s_, cum, P[:, 1])], -1), tot

def _arcnoise(n, perim_px, rng, amps=(0.9, 0.45, 0.22), lens=(70.0, 26.0, 10.0)):
    """low-frequency wobble along the contour, in device px; periodic around the loop"""
    s_ = np.arange(n) / n
    out = np.zeros(n)
    for a, L_ in zip(amps, lens):
        k = max(1, round(perim_px / L_))
        out += a * np.sin(TAU * k * s_ + rng.uniform(0, TAU))
    return out

def _normals(P):
    d = np.roll(P, -1, axis=0) - np.roll(P, 1, axis=0)
    n = np.stack([d[:, 1], -d[:, 0]], -1)
    n /= (np.linalg.norm(n, axis=1, keepdims=True) + 1e-9)
    area = 0.5 * np.sum(P[:, 0] * np.roll(P[:, 1], -1) - np.roll(P[:, 0], -1) * P[:, 1])
    return n if area > 0 else -n          # outward

def _poly_path(cc, P):
    cc.move_to(*P[0])
    for p in P[1:]:
        cc.line_to(*p)
    cc.close_path()

def cel(c, path, base, shade, L=(-0.55, -0.83), off=6.0, lw=2.4, shade2=None, off2=None, line=True, warm=0.55,
        ink=INK_C, inkw=INK_W, alpha=1.0, wob=1.0):
    """hand-drawn cel: wobbled silhouette, hand-designed shadow band of varying width, pressure-inked outline
    drawn as 2-4 overlapping tapered strokes, colored held line (warm on the lit side)."""
    kx, ky = c.user_to_device_distance(1.0, 0.0)
    k = math.hypot(kx, ky) + 1e-9                     # device px per user unit
    polys = _flatten(c, path)
    if not polys:
        return
    seed0 = int(abs(polys[0][0][0] * 13.1 + polys[0][0][1] * 7.7)) % 100000
    rng = np.random.default_rng(seed0 * 31 + _FRAME[0] * 9973)
    rng_shape = np.random.default_rng(seed0 * 17 + 5)          # shadow design stays stable
    Ln = np.array(L, dtype=np.float64); Ln /= np.linalg.norm(Ln) + 1e-9
    hand, shadowP, shadow2P, norms, perims = [], [], [], [], []
    for pts in polys:
        P, tot = _resample(pts, 2.5 / k)
        per_px = tot * k
        N = _normals(P) if len(P) > 3 else np.zeros_like(P)
        wobble = (_arcnoise(len(P), per_px, rng_shape, amps=(1.1 * wob, 0.12 * wob, 0.0), lens=(140.0, 40.0, 10.0)) +
                  _arcnoise(len(P), per_px, rng, amps=(0.35 * wob, 0.10 * wob, 0.06 * wob), lens=(90.0, 30.0, 12.0))) / k
        H_ = P + N * wobble[:, None]
        var = 1.0 + 0.45 * _arcnoise(len(P), per_px, rng_shape, amps=(1.0, 0.5, 0.0), lens=(160.0, 55.0, 1.0)) / 1.5
        hand.append(H_)
        shadowP.append(H_ + Ln[None, :] * (off * var)[:, None])
        if shade2 is not None:
            o2 = off2 if off2 is not None else off * 0.45
            shadow2P.append(H_ + Ln[None, :] * (o2 * var)[:, None])
        norms.append(N)
        perims.append(per_px)
    def HP(cc):
        for H_ in hand:
            _poly_path(cc, H_)
    if alpha < 1.0:
        c.push_group()
    c.save()
    HP(c)
    src(c, base)
    c.fill_preserve()
    c.clip()
    c.new_path()
    src(c, shade)
    c.paint()
    for Sp in shadowP:
        _poly_path(c, Sp)
    src(c, base)
    c.fill()
    if shade2 is not None:
        c.push_group()
        src(c, shade2)
        c.paint()
        c.set_operator(cairo.OPERATOR_CLEAR)
        for Sp in shadow2P:
            _poly_path(c, Sp)
        c.fill()
        c.pop_group_to_source()
        c.paint()
    c.restore()
    if line and lw > 0:
        allp = np.concatenate(hand)
        x0, y0 = allp.min(0); x1, y1 = allp.max(0)
        cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
        r = max(x1 - x0, y1 - y0) * 0.6 + 1
        pat = cairo.LinearGradient(cx + Ln[0] * r, cy + Ln[1] * r, cx - Ln[0] * r, cy - Ln[1] * r)
        pat.add_color_stop_rgb(0, *lc(ink, inkw, warm))
        pat.add_color_stop_rgb(0.45, *lc(ink, inkw, warm * 0.25))
        pat.add_color_stop_rgb(1, *ink)
        for H_, N, per_px in zip(hand, norms, perims):
            n = len(H_)
            if n < 4:
                continue
            sf = np.clip(0.5 - 0.5 * (N @ Ln), 0, 1)           # 1 on the side away from the light
            press = 1.0 + 0.18 * _arcnoise(n, per_px, rng, amps=(1.0, 0.6, 0.0), lens=(90.0, 30.0, 1.0)) / 1.6
            wbase = lw * (0.45 + 0.95 * sf ** 1.3) * press
            ns = 2 if per_px < 260 else (3 if per_px < 900 else 4)
            starts = (np.sort(rng.uniform(0, 1, ns)) * n).astype(int)
            ov = max(2, int(1.6 * lw * k / 2.5))              # overlap in samples
            for i in range(ns):
                a = starts[i] - ov
                b = (starts[(i + 1) % ns] + (n if i == ns - 1 else 0)) + ov
                idx = np.arange(a, b) % n
                m = len(idx)
                if m < 3:
                    continue
                u = np.linspace(0, 1, m)
                taper = np.clip(np.minimum(u, 1 - u) / 0.07, 0.15, 1.0)
                wv = wbase[idx] * taper
                Pp = H_[idx]
                Nn = N[idx]
                left = Pp + Nn * (wv / 2)[:, None] * 0.65
                right = Pp - Nn * (wv / 2)[:, None] * 1.35        # ink sits mostly inside the edge
                c.move_to(*left[0])
                for p in left[1:]:
                    c.line_to(*p)
                for p in right[::-1]:
                    c.line_to(*p)
                c.close_path()
                c.set_source(pat)
                c.fill()
    if alpha < 1.0:
        c.pop_group_to_source()
        c.paint_with_alpha(alpha)

def inkline(c, pts, w, col=INK_C, a=1.0, taper=True):
    """hand-inked open stroke with swell in the middle (drawn as filled ribbon)"""
    if len(pts) < 2:
        return
    n = len(pts)
    left, right = [], []
    for i, (x, y) in enumerate(pts):
        x0, y0 = pts[max(0, i - 1)]
        x1, y1 = pts[min(n - 1, i + 1)]
        dx, dy = x1 - x0, y1 - y0
        L = math.hypot(dx, dy) + 1e-6
        nx, ny = -dy / L, dx / L
        u = i / (n - 1)
        ww = w * (0.35 + 0.65 * math.sin(math.pi * u)) if taper else w
        left.append((x + nx * ww / 2, y + ny * ww / 2))
        right.append((x - nx * ww / 2, y - ny * ww / 2))
    poly(c, left + right[::-1])
    fillc(c, col, a)

def qcurve(p0, p1, p2, n=12):
    out = []
    for k in range(n + 1):
        u = k / n
        out.append(((1 - u) ** 2 * p0[0] + 2 * (1 - u) * u * p1[0] + u * u * p2[0],
                    (1 - u) ** 2 * p0[1] + 2 * (1 - u) * u * p1[1] + u * u * p2[1]))
    return out

# ------------------------------------------------------------------ palettes (per-scene light tint applied by caller)
JI = dict(
    pole=(0.50, 0.36, 0.24), pole_s=(0.34, 0.24, 0.17),
    jacket=(0.33, 0.43, 0.58), jacket_s=(0.22, 0.29, 0.42), jacket_s2=(0.16, 0.21, 0.32),
    patch=(0.78, 0.44, 0.24), patch_s=(0.56, 0.30, 0.17),
    goreum=(0.74, 0.30, 0.24), goreum_s=(0.52, 0.19, 0.16),
    sack=(0.84, 0.74, 0.56), sack_s=(0.66, 0.55, 0.40), sack_s2=(0.52, 0.43, 0.31),
    straw=(0.92, 0.78, 0.44), straw_s=(0.70, 0.55, 0.28), straw_d=(0.55, 0.40, 0.20),
    hat=(0.93, 0.82, 0.52), hat_s=(0.72, 0.60, 0.36), band=(0.56, 0.22, 0.18),
    rope=(0.62, 0.50, 0.32), btn_k=(0.12, 0.11, 0.12), btn_r=(0.80, 0.20, 0.17), thread=(0.95, 0.90, 0.78),
    snow=(0.95, 0.96, 1.0), snow_s=(0.72, 0.76, 0.92),
)

def tint_pal(pal, mul=(1, 1, 1), add=(0, 0, 0), mix=None, k=0.0):
    out = {}
    for key, col in pal.items():
        c2 = tuple(min(1.0, max(0.0, col[i] * mul[i] + add[i])) for i in range(3))
        if mix is not None:
            c2 = lc(c2, mix, k)
        out[key] = c2
    return out

JI_DEF = dict(arm_len=1.0, lean=0.0, head_tilt=0.0, head_turn=0.0, hat_down=0.0, hat_tilt=0.0, flapL=-0.2, flapR=-0.2,
              billow=0.0, wind=0.0, wrapL=0.0, bend=0.0, pocket=0, leaf=0.0, snow=0.0, frost=0.0, hat_on=1.0,
              topple=0.0, goreum_wind=None, topple_dir=1, whipL=0.0, whip_dir=0.0)

# ------------------------------------------------------------------ 짚이
def jiibi(c, x, y, s, P=None, t=0.0, L=(-0.55, -0.83), pal=None, boil=None, lw=3.0, chest_fn=None):
    """scarecrow, pole base at (x, y). returns dict of device points (head, chest, hat, cuffL, cuffR)"""
    P = dict(JI_DEF, **(P or {}))
    pal = pal or JI
    B = boil or Boil(t)
    out = {}
    W_ = P['wind']
    c.save()
    c.translate(x, y)
    c.scale(s, s)
    c.rotate(math.radians(P['lean'] + P['topple'] * (84 if P['topple_dir'] > 0 else 84 + P['bend']) * P['topple_dir']))
    lws = lw / s
    # ---- pole (lower part)
    def pole_low(cc):
        poly(cc, B.jp([(-5, 2), (5, 2), (4.5, -112), (-4.5, -112)], 0.4))
    cel(c, pole_low, pal['pole'], pal['pole_s'], L, off=3, lw=lws)
    # bend pivot
    c.translate(0, -110)
    c.rotate(math.radians(P['bend']))
    c.translate(0, 110)
    def pole_up(cc):
        poly(cc, B.jp([(-4.5, -108), (4.5, -108), (4, -290), (-4, -290)], 0.4))
    cel(c, pole_up, pal['pole'], pal['pole_s'], L, off=3, lw=lws)
    if P['bend'] != 0:
        for k in range(5):
            a = k * 0.9
            inkline(c, [(-6, -110 + k * 2), (6 + 2 * math.sin(a), -112 + k * 2)], 1.4, INK_C, 0.7)
    # ---- straw hem (behind jacket)
    hem = 0.0 + P['billow'] * 10
    for k in range(16):
        u = k / 15
        bx = -34 - hem + (68 + 2 * hem) * u
        L_ = 16 + 9 * math.sin(k * 2.7) ** 2
        sway = W_ * (10 + 6 * math.sin(t * 9 + k)) if abs(W_) > 0.05 else 0
        pts = B.jp(qcurve((bx, -142), (bx + sway * 0.4, -142 + L_ * 0.5), (bx + sway, -142 + L_)), 0.5)
        inkline(c, pts, 3.2, pal['straw_s'] if k % 3 else pal['straw_d'], 1.0, taper=False)
        inkline(c, pts, 1.6, pal['straw'], 1.0, taper=False)
    # ---- sleeves
    def sleeve_geom(side, flap, wrap):
        sx, sy = side * 26, -228
        al = P['arm_len']
        hang = (side * (26 + 62 * al), -200 - (1 - al) * 20)        # cuff when hanging
        up = (side * (26 + 84 * al), -248)
        f = (flap + 1) / 2
        cx_, cy_ = lerp(hang[0], up[0], f), lerp(hang[1], up[1], f)
        if wrap > 0:
            wc = (side * -14, -186)
            cx_, cy_ = lerp(cx_, wc[0], wrap), lerp(cy_, wc[1], wrap)
        mid = ((sx + cx_) / 2 + side * wrap * 34, (sy + cy_) / 2 + (1 - f) * 14 - wrap * 6)
        return (sx, sy), mid, (cx_, cy_)
    cuffs = {}
    def draw_sleeve(side, flap, wrap):
        a, m, b = sleeve_geom(side, flap, wrap)
        cen = qcurve(a, m, b, 10)
        top, bot = [], []
        for i, (px, py) in enumerate(cen):
            u = i / 10
            x0, y0 = cen[max(0, i - 1)]
            x1, y1 = cen[min(10, i + 1)]
            dx, dy = x1 - x0, y1 - y0
            Ln = math.hypot(dx, dy) + 1e-6
            nx, ny = -dy / Ln, dx / Ln
            wd = 17 - 4 * u
            flut = (math.sin(t * 13 + u * 6 + side) * 3.5 * abs(W_)) if abs(W_) > 0.05 else 0
            top.append((px - nx * wd * side, py - ny * wd * side))
            bot.append((px + nx * (wd + flut) * side, py + ny * (wd + flut) * side))
        pts = B.jp(top + bot[::-1], 0.6)
        def sp(cc):
            smooth_path(cc, pts)
        cel(c, sp, pal['jacket'], pal['jacket_s'], L, off=7, lw=lws, shade2=pal['jacket_s2'], off2=3)
        # folds
        for k in (0.35, 0.62):
            i = int(k * 10)
            inkline(c, B.jp([top[i], ((top[i][0] + bot[i][0]) / 2 + 3, (top[i][1] + bot[i][1]) / 2)], 0.5), 1.6,
                    INK_C, 0.7)
        if side < 0:
            # elbow patch on the left sleeve
            i = 5
            pc = ((top[i][0] + bot[i][0]) / 2, (top[i][1] + bot[i][1]) / 2)
            def pp(cc):
                poly(cc, B.jp([(pc[0] - 7, pc[1] - 6), (pc[0] + 7, pc[1] - 7), (pc[0] + 8, pc[1] + 6),
                               (pc[0] - 6, pc[1] + 7)], 0.4))
            cel(c, pp, pal['patch'], pal['patch_s'], L, off=3, lw=lws * 0.7)
            for k in range(4):
                inkline(c, [(pc[0] - 7 + k * 4.5, pc[1] - 8), (pc[0] - 7 + k * 4.5, pc[1] - 5)], 0.9, INK_C, 0.8,
                        taper=False)
        cuffs[side] = (b, (top[-1], bot[-1]))
        return b
    # straw hands (behind cuffs)
    def straw_hand(side):
        b, (tp, bt) = cuffs[side]
        dirx = side
        for k in range(9):
            u = k / 8
            sx_, sy_ = lerp(tp[0], bt[0], u), lerp(tp[1], bt[1], u)
            L_ = 18 + 8 * math.sin(k * 1.9) ** 2
            ang = math.atan2(bt[1] - tp[1], bt[0] - tp[0]) - math.pi / 2 * side
            ang += (u - 0.5) * 0.9 + W_ * 0.25 * math.sin(t * 11 + k)
            if side < 0 and P['whipL'] > 0:            # the straw bundle whips out in a gust (C6-1 swat)
                wl = P['whipL']
                L_ *= 1 + 1.6 * wl * (0.7 + 0.3 * math.sin(k * 2.3))
                ang = ang * (1 - wl) + (math.pi + P['whip_dir'] + (u - 0.5) * 0.7) * wl
            ex, ey = sx_ + math.cos(ang) * L_ * dirx * side, sy_ + math.sin(ang) * L_ * side
            if side < 0:
                ex, ey = sx_ - math.cos(ang) * L_, sy_ - math.sin(ang) * L_
            else:
                ex, ey = sx_ + math.cos(ang) * L_, sy_ + math.sin(ang) * L_
            pts = B.jp([(sx_, sy_), ((sx_ + ex) / 2, (sy_ + ey) / 2 + 2), (ex, ey)], 0.5)
            inkline(c, pts, 3.0, pal['straw_d'] if k % 4 == 0 else pal['straw_s'], 1.0, taper=False)
            inkline(c, pts, 1.5, pal['straw'], 1.0, taper=False)
    # back sleeve first (right side drawn behind body? both in front of crossbar)
    draw_sleeve(1, P['flapR'], 0.0)
    straw_hand(1)
    if P['wrapL'] < 0.5:
        draw_sleeve(-1, P['flapL'], P['wrapL'])
        straw_hand(-1)
    # ---- jacket body
    bl = P['billow']
    def body(cc):
        pts = [(-24, -238), (24, -238), (32 + bl * 6, -200), (36 + bl * 14 + W_ * 6, -142 + bl * 2),
               (8, -138 + bl * 4), (-36 - bl * 14 + W_ * 6, -142 + bl * 2), (-32 - bl * 6, -200)]
        smooth_path(cc, B.jp(pts, 0.6))
    cel(c, body, pal['jacket'], pal['jacket_s'], L, off=10, lw=lws, shade2=pal['jacket_s2'], off2=4)
    # collar (저고리 깃) and overlap line
    inkline(c, B.jp([(-18, -238), (-4, -214), (10, -190), (18, -150)], 0.5), 2.2, INK_C, 0.9)
    def collar(cc):
        poly(cc, B.jp([(-21, -239), (-14, -239), (-3, -222), (-9, -219)], 0.3))
    cel(c, collar, lc(pal['jacket'], (0.97, 0.94, 0.86), 0.85), lc(pal['jacket_s'], (0.95, 0.93, 0.86), 0.6), L, off=2,
        lw=lws * 0.7)
    # 고름 (ribbon tie) -- overlapping motion
    gw = P['goreum_wind'] if P['goreum_wind'] is not None else W_
    gx, gy = 4, -206
    for k, (ln, ph) in enumerate(((34, 0.0), (26, 1.3))):
        sway = gw * 18 + 4 * math.sin(t * 7 + ph) * (abs(gw) + 0.15)
        p1 = (gx + 6 + sway * 0.5, gy + ln * 0.5)
        p2 = (gx + 3 + sway, gy + ln)
        pts = B.jp(qcurve((gx, gy), p1, p2, 8), 0.4)
        inkline(c, pts, 9.5, pal['goreum_s'], 1.0, taper=False)
        inkline(c, pts, 6.0, pal['goreum'], 1.0, taper=False)
    def knot(cc):
        smooth_path(cc, [(gx - 9, gy - 4), (gx - 2, gy - 5), (gx + 3, gy - 2), (gx + 2, gy + 4), (gx - 6, gy + 3)])
    cel(c, knot, pal['goreum'], pal['goreum_s'], L, off=2, lw=lws * 0.8)
    # pocket + gifts
    def pocket(cc):
        poly(cc, B.jp([(10, -172), (30, -172), (31, -152), (12, -151)], 0.4))
    if P['pocket'] > 0:
        items = [((0.92, 0.50, 0.18), (0.70, 0.32, 0.10), 'kaki'), ((0.62, 0.42, 0.22), (0.42, 0.27, 0.13), 'acorn'),
                 ((0.86, 0.22, 0.14), (0.60, 0.13, 0.10), 'leaf')]
        for k in range(min(3, int(P['pocket']))):
            col, sh, kind = items[k]
            px_, py_ = 15 + k * 6, -176 - (k % 2) * 4
            if kind == 'leaf':
                def lf(cc, px_=px_, py_=py_):
                    poly(cc, B.jp([(px_, py_ + 4), (px_ - 5, py_ - 2), (px_ - 2, py_ - 4), (px_, py_ - 9),
                                   (px_ + 2, py_ - 4), (px_ + 6, py_ - 3), (px_ + 1, py_ + 4)], 0.3))
            else:
                def lf(cc, px_=px_, py_=py_):
                    cc.arc(px_, py_, 5, 0, TAU)
            cel(c, lf, col, sh, L, off=2, lw=lws * 0.7)
    cel(c, pocket, pal['jacket_s'], pal['jacket_s2'], L, off=3, lw=lws * 0.8)
    out['chest'] = c.user_to_device(-4, -200)
    out['pocket'] = c.user_to_device(20, -170)
    if chest_fn is not None:
        chest_fn(c)
    # wrapped left sleeve in front of the chest
    if P['wrapL'] >= 0.5:
        draw_sleeve(-1, P['flapL'], P['wrapL'])
        straw_hand(-1)
    b = cuffs[-1][0]
    out['cuffL'] = c.user_to_device(*b)
    out['cuffR'] = c.user_to_device(*cuffs[1][0])
    # ---- head
    c.save()
    c.translate(0, -244)
    c.rotate(math.radians(P['head_tilt']))
    turn = P['head_turn']
    # rope collar
    rope = B.jp([(-15, 1), (-5, 3), (5, 3), (15, 1)], 0.4)
    def head(cc):
        pts = [(-14, 0), (-27, -14), (-31, -34), (-24, -56), (-8, -66), (10, -66), (25, -56), (31, -34), (27, -14),
               (14, 0)]
        smooth_path(cc, B.jp(pts, 0.5))
    cel(c, head, pal['sack'], pal['sack_s'], L, off=9, lw=lws, shade2=pal['sack_s2'], off2=3)
    # burlap weave
    c.save()
    head(c)
    c.clip()
    for k in range(-6, 7):
        inkline(c, [(k * 5 - 3, -70), (k * 5 + 3, 4)], 0.7, pal['sack_s'], 0.45, taper=False)
    for k in range(0, 14):
        inkline(c, [(-34, -66 + k * 5), (34, -66 + k * 5 + 2)], 0.6, pal['sack_s'], 0.35, taper=False)
    # seam stitches (moves with turn)
    sx_ = 18 + turn * 10
    for k in range(6):
        yy = -58 + k * 9
        inkline(c, [(sx_ - 2, yy), (sx_ + 2, yy + 4)], 1.1, INK_C, 0.75, taper=False)
    c.restore()
    for k in range(4):
        inkline(c, B.jp([(-16 + k * 8, -1), (-12 + k * 8, 4)], 0.3), 2.2, pal['rope'], 1.0, taper=False)
    inkline(c, rope, 3.5, INK_C, 0.5, taper=False)
    # button eyes
    ex = 11
    for k, (dx0, col) in enumerate(((-ex, pal['btn_k']), (ex, pal['btn_r']))):
        dx = dx0 + turn * 12
        sq = 1.0 - 0.35 * abs(turn) * (1 if (dx0 < 0) == (turn > 0) else 0.2)
        ey = -36
        c.save()
        c.translate(dx, ey)
        c.scale(sq, 1.0)
        def btn(cc):
            cc.arc(0, 0, 6.2, 0, TAU)
        cel(c, btn, col, cm(col, 0.6), L, off=2, lw=lws * 0.8)
        for hx, hy in ((-1.9, -1.9), (1.9, -1.9), (-1.9, 1.9), (1.9, 1.9)):
            c.arc(hx, hy, 0.9, 0, TAU)
            fillc(c, cm(col, 0.45))
        inkline(c, [(-2.6, -2.6), (2.6, 2.6)], 1.2, pal['thread'], 1.0, taper=False)
        inkline(c, [(2.6, -2.6), (-2.6, 2.6)], 1.2, pal['thread'], 1.0, taper=False)
        c.arc(-2.4, -2.6, 1.2, 0, TAU)
        fillc(c, (1, 1, 1), 0.55)
        if P['frost'] > 0:
            for a in range(6):
                an = a * TAU / 6
                inkline(c, [(0, 0), (math.cos(an) * 6.5, math.sin(an) * 6.5)], 0.8, (0.92, 0.96, 1.0),
                        P['frost'], taper=False)
        c.restore()
    out['head'] = c.user_to_device(0, -34)
    out['eyeL'] = c.user_to_device(-ex + turn * 12, -36)
    # ---- hat
    if P['hat_on'] > 0.5:
        c.save()
        hd = P['hat_down']
        c.translate(0, -52 + hd * 18)
        c.rotate(math.radians(P['hat_tilt'] + hd * 8))
        straw_hat(c, pal, L, B, lws, hd, P['snow'])
        out['hat'] = c.user_to_device(0, -30)
        c.restore()
    # cheek leaf (blush)
    if P['leaf'] > 0.01:
        lx, ly = 12 + turn * 14, -13
        def leaf(cc):
            pts = [(lx, ly + 7), (lx - 8, ly + 1), (lx - 5, ly - 2), (lx - 7, ly - 8), (lx - 2, ly - 5),
                   (lx, ly - 11), (lx + 2, ly - 5), (lx + 8, ly - 7), (lx + 5, ly), (lx + 9, ly + 3)]
            poly(cc, B.jp(pts, 0.3))
        cel(c, leaf, (0.90, 0.26, 0.15), (0.66, 0.15, 0.10), L, off=2, lw=lws * 0.7, alpha=min(1, P['leaf']))
    c.restore()
    if P['snow'] > 0:
        for side in (-1, 1):
            if side < 0 and P['wrapL'] > 0.3:
                continue
            a, m, b_ = sleeve_geom(side, P['flapL'] if side < 0 else P['flapR'], 0.0)
            pts = qcurve(a, m, b_, 6)
            def sc(cc, pts=pts):
                top = [(px, py - 21) for (px, py) in pts]
                smooth_path(cc, B.jp(top + [(px, py - 14) for (px, py) in pts[::-1]], 0.6))
            cel(c, sc, pal['snow'], pal['snow_s'], L, off=3, lw=lws * 0.7, alpha=P['snow'])
    c.restore()
    return out

def straw_hat(c, pal, L, B, lws, hd=0.0, snow=0.0):
    """the torn straw hat drawn in its own frame (crown base at origin)"""
    # crown back
    def brim(cc):
        pts = []
        for k in range(28):
            a = TAU * k / 28
            r = 1.0
            if 0.2 < a < 0.65:
                r = 0.86                     # torn notch
            pts.append((math.cos(a) * 54 * r, math.sin(a) * 13 * r + (hd * 5 if math.sin(a) > 0 else 0)))
        smooth_path(cc, B.jp(pts, 0.5))
    def crown(cc):
        pts = [(-29, 0), (-28, -12), (-20, -23), (0, -26), (20, -23), (28, -12), (29, 0), (15, 5), (-15, 5)]
        smooth_path(cc, B.jp(pts, 0.4))
    cel(c, brim, pal['hat'], pal['hat_s'], L, off=4, lw=lws)
    c.save()
    brim(c)
    c.clip()
    for k in range(18):
        a = TAU * k / 18
        inkline(c, [(math.cos(a) * 30, math.sin(a) * 6), (math.cos(a) * 54, math.sin(a) * 13)], 0.8, pal['hat_s'],
                0.6, taper=False)
    c.restore()
    cel(c, crown, pal['hat'], pal['hat_s'], L, off=7, lw=lws)
    def band(cc):
        poly(cc, B.jp([(-29, -2), (29, -2), (28.5, -8), (-28.5, -8)], 0.3))
    cel(c, band, pal['band'], cm(pal['band'], 0.7), L, off=2, lw=lws * 0.7)
    if snow > 0:
        def snowcap(cc):
            pts = [(-50, -1), (-34, -6), (-26, -18), (-6, -28), (16, -24), (28, -12), (48, -2), (30, 1), (-30, 1)]
            smooth_path(cc, B.jp(pts, 0.8))
        cel(c, snowcap, pal['snow'], pal['snow_s'], L, off=5, lw=lws * 0.8, alpha=snow)

def hat_at(c, x, y, s, rot, t, L, pal=None, hd=0.0, snow=0.0, lw=3.0):
    pal = pal or JI
    B = Boil(t, salt=13)
    c.save(); c.translate(x, y); c.scale(s, s); c.rotate(math.radians(rot))
    straw_hat(c, pal, L, B, lw / s, hd, snow)
    c.restore()

# ------------------------------------------------------------------ 콩이
KO = dict(back=(0.58, 0.40, 0.25), back_s=(0.42, 0.28, 0.18), belly=(0.97, 0.90, 0.74), belly_s=(0.82, 0.72, 0.56),
          cap=(0.48, 0.30, 0.18), beak=(0.98, 0.76, 0.24), beak_s=(0.80, 0.56, 0.14), eye=(0.08, 0.07, 0.08),
          cheek=(0.30, 0.22, 0.18), wing=(0.50, 0.33, 0.20), wing_s=(0.36, 0.23, 0.14), feet=(0.80, 0.52, 0.36))
KO_DEF = dict(puff=1.0, tilt=0.0, face=1, wing=0.0, blink=0.0, squash=1.0, feet=1.0, rub=0.0, open_beak=0.0)

def kongi(c, x, y, s, P=None, t=0.0, L=(-0.55, -0.83), pal=None, boil=None, lw=2.4):
    """sparrow standing at feet point (x, y). s = body radius in px"""
    P = dict(KO_DEF, **(P or {}))
    pal = pal or KO
    B = boil or Boil(t, salt=3)
    c.save()
    c.translate(x, y)
    c.scale(s / 10.0 * P['face'], s / 10.0)
    c.rotate(math.radians(P['tilt']))
    lws = lw / (s / 10.0)
    sq = P['squash']
    pf = P['puff']
    # feet
    if P['feet'] > 0:
        for fx in (-2.5, 2.5):
            inkline(c, [(fx, -3), (fx, 0)], 1.4, pal['feet'], 1.0, taper=False)
            inkline(c, [(fx - 2, 0), (fx + 2.5, 0)], 1.0, pal['feet'], 1.0, taper=False)
    # tail
    def tail(cc):
        poly(cc, B.jp([(-7, -8), (-17, -12), (-16, -8), (-7, -5)], 0.25))
    cel(c, tail, pal['back'], pal['back_s'], L, off=1.5, lw=lws)
    # body
    def body(cc):
        r = 10 * pf
        pts = []
        for k in range(14):
            a = TAU * k / 14
            pts.append((math.cos(a) * r * 1.05 / sq ** 0.5, -10 * sq + math.sin(a) * r * sq))
        smooth_path(cc, B.jp(pts, 0.25))
    cel(c, body, pal['back'], pal['back_s'], L, off=3, lw=lws)
    def belly(cc):
        r = 8 * pf
        pts = []
        for k in range(12):
            a = TAU * k / 12
            pts.append((2.5 + math.cos(a) * r * 0.9, -7.5 * sq + math.sin(a) * r * 0.8 * sq))
        smooth_path(cc, B.jp(pts, 0.2))
    cel(c, belly, pal['belly'], pal['belly_s'], L, off=2.5, lw=0)
    # wing
    w = P['wing']
    c.save()
    c.translate(-1, -12 * sq)
    c.rotate(-w * 1.6)
    def wing(cc):
        pts = [(-2, -2), (5, -3), (2, 3 + w * 4), (-8, 4 + w * 6), (-9, 1)]
        smooth_path(cc, B.jp(pts, 0.25))
    cel(c, wing, pal['wing'], pal['wing_s'], L, off=1.5, lw=lws)
    for k in range(3):
        inkline(c, [(-6 + k * 2.5, 2), (-4 + k * 2.5, 4 + w * 3)], 0.7, pal['wing_s'], 0.9, taper=False)
    c.restore()
    # head
    hx, hy = 5, -19 * sq
    def head(cc):
        cc.arc(hx, hy, 6.5 * (0.9 + 0.1 * pf), 0, TAU)
    cel(c, head, pal['back'], pal['back_s'], L, off=2, lw=lws)
    def capf(cc):
        cc.arc(hx - 0.5, hy - 1.8, 5.2, math.pi * 1.05, math.pi * 1.95)
        cc.close_path()
    cel(c, capf, pal['cap'], pal['cap'], L, off=0, lw=0)
    # cheek + eye
    c.arc(hx + 2.6, hy + 2.2, 1.9, 0, TAU)
    fillc(c, pal['cheek'], 0.8)
    if P['blink'] > 0.5:
        inkline(c, [(hx + 1.2, hy - 0.6), (hx + 3.8, hy - 0.2)], 1.0, pal['eye'], 1.0, taper=False)
    else:
        c.arc(hx + 2.5, hy - 0.6, 1.5, 0, TAU)
        fillc(c, pal['eye'])
        c.arc(hx + 2.0, hy - 1.2, 0.5, 0, TAU)
        fillc(c, (1, 1, 1))
    # beak
    ob = P['open_beak']
    def beak(cc):
        poly(cc, B.jp([(hx + 5.6, hy - 1), (hx + 10, hy + 0.5 - ob * 1.5), (hx + 5.8, hy + 1.6)], 0.15))
    cel(c, beak, pal['beak'], pal['beak_s'], L, off=0.8, lw=lws * 0.6)
    if ob > 0.1:
        def beak2(cc):
            poly(cc, [(hx + 5.6, hy + 1.6), (hx + 9, hy + 2 + ob * 2), (hx + 5.8, hy + 2.6)])
        cel(c, beak2, pal['beak'], pal['beak_s'], L, off=0.5, lw=lws * 0.6)
    # tuft
    inkline(c, B.jp(qcurve((hx - 1, hy - 6), (hx - 2, hy - 10), (hx + 2, hy - 12), 5), 0.2), 1.5, pal['cap'], 1.0,
            taper=True)
    c.restore()

# ------------------------------------------------------------------ 매
def hawk(c, x, y, s, heading=0.0, flap=0.0, L=(-0.55, -0.83), boil=None, lw=2.4, dark=0.0):
    """hawk from below: fingered primaries, barred tail, hooked beak, dark eye stripe. beak toward +x"""
    B = boil or Boil(0, salt=9)
    c.save()
    c.translate(x, y)
    c.rotate(heading)
    c.scale(s / 10, s / 10)
    lws = lw / (s / 10)
    w = math.sin(flap)
    up, mid, dk, pale = (0.62, 0.50, 0.40), (0.44, 0.34, 0.27), (0.27, 0.21, 0.18), (0.90, 0.84, 0.72)
    if dark > 0:
        sil = (0.24, 0.20, 0.30)
        up, mid, dk, pale = (lc(up, sil, dark), lc(mid, sil, dark), lc(dk, sil, dark * 0.6), lc(pale, sil, dark))
    span = 34 * (0.5 + 0.5 * abs(w))
    fold = 0.15 + 0.85 * abs(w)
    for sg in (-1, 1):
        # primaries: five separated "fingers"
        for kf_ in range(5):
            ang = math.radians(-8 - kf_ * 17)                 # fan from outward to backward
            bx, by = 1.0 - kf_ * 2.4, sg * span * (0.80 - kf_ * 0.035)
            Lf = (8.5 - kf_ * 0.6) * (0.6 + 0.4 * fold)
            dx, dy = math.sin(-ang) * -1, math.cos(ang)
            tx, ty = bx + math.sin(ang) * Lf, by + sg * math.cos(ang) * Lf
            nx, ny = (ty - by), -(tx - bx)
            nl = math.hypot(nx, ny) + 1e-6; nx, ny = nx / nl, ny / nl
            def feather(cc, bx=bx, by=by, tx=tx, ty=ty, nx=nx, ny=ny):
                wd = 1.5
                smooth_path(cc, B.jp([(bx + nx * wd, by + ny * wd), (tx + nx * 0.7, ty + ny * 0.7),
                                      (tx + (tx - bx) * 0.06, ty + (ty - by) * 0.06), (tx - nx * 0.7, ty - ny * 0.7),
                                      (bx - nx * wd, by - ny * wd)], 0.12))
            cel(c, feather, mid, dk, L, off=0.7, lw=lws * 0.75)
        def wing(cc, sg=sg):
            pts = [(5, sg * 2), (4.5, sg * span * 0.35), (2.5, sg * span * 0.62), (1.5, sg * span * 0.80), (-1.5, sg * span * 0.86),
                   (-9, sg * span * 0.70), (-11, sg * span * 0.45), (-10.5, sg * span * 0.22), (-7, sg * 3)]
            smooth_path(cc, B.jp(pts, 0.2))
        cel(c, wing, pale, mid, L, off=1.6, lw=lws, shade2=dk, off2=0.6)
        # leading-edge coverts band + bars
        inkline(c, B.jp([(4.5, sg * 3), (3.5, sg * span * 0.4), (0.5, sg * span * 0.7), (-2, sg * span * 0.82)], 0.15), 2.6, up, 1.0)
        for kb in range(4):
            u = 0.3 + 0.14 * kb
            inkline(c, [(-2 - kb * 0.5, sg * span * u), (-8.5, sg * span * (u + 0.02))], 0.7, mid, 0.8)
    def tail(cc):
        smooth_path(cc, B.jp([(-11, -3.2), (-21, -5.5), (-23.5, -2), (-23.5, 2), (-21, 5.5), (-11, 3.2)], 0.15))
    cel(c, tail, pale, mid, L, off=1.2, lw=lws)
    for kb in range(3):
        xx = -14.5 - kb * 3
        inkline(c, [(xx, -3.8 - kb * 0.7), (xx, 3.8 + kb * 0.7)], 1.1, mid, 0.9, taper=False)
    inkline(c, [(-23.2, -3), (-23.2, 3)], 1.4, dk, 0.9, taper=False)
    def body(cc):
        smooth_path(cc, B.jp([(12, -2.6), (8, -4.2), (0, -4.6), (-8, -4), (-12.5, 0), (-8, 4), (0, 4.6), (8, 4.2), (12, 2.6)], 0.15))
    cel(c, body, pale, mid, L, off=1.4, lw=lws)
    for kb in range(6):                          # streaked breast
        xx = 6 - kb * 2.6
        inkline(c, [(xx, -2.4 + (kb % 2)), (xx - 1.2, -0.4 + (kb % 2))], 0.7, mid, 0.8)
        inkline(c, [(xx - 0.6, 1.0 - (kb % 2)), (xx - 1.8, 2.8 - (kb % 2))], 0.7, mid, 0.8)
    def head(cc):
        smooth_path(cc, B.jp([(16, -0.6), (14.5, -3), (10.5, -3.6), (8.5, 0), (10.5, 3.6), (14.5, 3)], 0.12))
    cel(c, head, up, mid, L, off=1.0, lw=lws)
    inkline(c, [(15, -1.6), (11, -2.6)], 1.2, dk, 1.0)                 # eye stripe
    def beak(cc):
        smooth_path(cc, [(15.8, -1.4), (18.4, -0.8), (19.2, 0.6), (18.0, 0.2), (15.8, 1.4)])
    cel(c, beak, (0.30, 0.30, 0.34), (0.16, 0.16, 0.20), L, off=0.4, lw=lws * 0.5)
    c.arc(15.4, -1.4, 0.75, 0, TAU)
    fillc(c, (0.98, 0.80, 0.20))
    c.arc(15.5, -1.5, 0.35, 0, TAU)
    fillc(c, (0.05, 0.05, 0.05))
    c.restore()

# ------------------------------------------------------------------ dragonfly (고추잠자리)
def dragonfly(c, x, y, s, ang, t, boil=None):
    B = boil or Boil(t, salt=11)
    c.save()
    c.translate(x, y)
    c.rotate(ang)
    c.scale(s / 10, s / 10)
    for sg in (-1, 1):
        for k, off in enumerate((-1.5, 2.0)):
            c.save()
            c.translate(off, 0)
            c.rotate(sg * (1.35 + 0.25 * math.sin(t * 60 + k)))
            c.scale(1, 0.32)
            c.arc(0, 7, 7, 0, TAU)
            c.restore()
            fillc(c, (0.92, 0.94, 0.95), 0.5)
    inkline(c, B.jp([(4, 0), (-14, 0)], 0.2), 2.4, (0.86, 0.22, 0.12), 1.0, taper=False)
    c.arc(5, 0, 2.2, 0, TAU)
    fillc(c, (0.60, 0.14, 0.08))
    c.restore()

# ------------------------------------------------------------------ film post
_GXf = np.tile(np.arange(W, dtype=F32), (H, 1))
_GYf = np.tile(np.arange(H, dtype=F32)[:, None], (1, W))

def film_post(img, t, halo=0.35, weave=0.6, lift=0.035):
    # halation: bright cores bleed warm
    br = np.clip(img.max(axis=2) - 0.72, 0, 1)
    if halo > 0 and br.max() > 0.01:
        d = cv2.resize(br, (W // 4, H // 4), interpolation=cv2.INTER_AREA)
        d = cv2.GaussianBlur(d, (0, 0), 6)
        hb = cv2.resize(d, (W, H), interpolation=cv2.INTER_LINEAR)
        img = img + hb[..., None] * np.array((1.0, 0.55, 0.32), F32) * F32(halo)
    # lifted blacks
    img = F32(lift) + img * F32(1 - lift)
    # gate weave on twos
    r = np.random.default_rng(int(math.floor(t * 12)) * 31 + 5)
    dx, dy = r.normal(0, weave), r.normal(0, weave * 0.7)
    M = np.float32([[1, 0, dx], [0, 1, dy]])
    img = cv2.warpAffine(img, M, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
    return img


def cel_finish(arr, t, soften=0.5, mottle=0.018, sep=(1.0, 0.985, 0.97)):
    """photographed-cel look for the character layer (premultiplied RGBA float):
    slight optical softness, faint paint mottling, and a small colour offset from the background art."""
    a = arr[..., 3:4]
    if mottle > 0:
        n = fbm(W, H, seed=77, octaves=4, base=10)
        arr[..., :3] = arr[..., :3] * (1 + F32(mottle) * n[..., None])
    arr[..., :3] = arr[..., :3] * np.array(sep, F32)
    if soften > 0:
        arr = cv2.GaussianBlur(arr, (0, 0), soften)
    return arr
