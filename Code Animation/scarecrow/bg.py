# -*- coding: utf-8 -*-
"""〈허수아비의 겨울〉 -- one field, nine seasons. Poster-colour backgrounds painted once per variant."""
from eng import *
from cel import cel, smooth_path, inkline, qcurve, Boil, INK_C
import math
import numpy as np
import cairo
import cv2

WW, WH = 2400, 1300
HOR = 600
VP = (1250, 592)                  # vanishing point of the dikes
JI_POS = (1500, 1010)             # scarecrow base in world coords
TREE = (470, 500)                 # persimmon tree base

SEASONS = {
    'dawn': dict(sky=[(0, (0.55, 0.62, 0.80)), (0.45, (0.93, 0.78, 0.76)), (0.8, (1.0, 0.86, 0.66)), (1, (1.0, 0.92, 0.72))],
                 sun=(1700, 560, (1.0, 0.94, 0.78), 46), cloud=[(0.72, 0.60, 0.70), (0.95, 0.74, 0.70), (1.0, 0.86, 0.72), (1.0, 0.95, 0.86)],
                 far=(0.70, 0.66, 0.78), near=(0.52, 0.52, 0.56), hill=[(0.36, 0.40, 0.34), (0.48, 0.52, 0.38), (0.64, 0.62, 0.42), (0.86, 0.76, 0.52)],
                 tree='kaki', field='rice', rice=[(0.70, 0.52, 0.24), (0.86, 0.68, 0.30), (0.96, 0.82, 0.42), (1.0, 0.92, 0.62)],
                 dike=(0.52, 0.56, 0.34), path=(0.84, 0.72, 0.56), fore='cosmos', haze=(1.0, 0.88, 0.74), mist=0.45, L=(0.8, -0.6)),
    'noon': dict(sky=[(0, (0.20, 0.42, 0.72)), (0.6, (0.44, 0.66, 0.86)), (1, (0.78, 0.86, 0.90))],
                 sun=None, cloud=[(0.60, 0.66, 0.80), (0.82, 0.86, 0.92), (0.94, 0.96, 0.98), (1.0, 1.0, 1.0)],
                 far=(0.52, 0.62, 0.76), near=(0.36, 0.48, 0.52), hill=[(0.22, 0.36, 0.28), (0.34, 0.50, 0.30), (0.50, 0.64, 0.32), (0.74, 0.80, 0.44)],
                 tree='kaki', field='rice', rice=[(0.72, 0.52, 0.18), (0.90, 0.70, 0.22), (0.99, 0.84, 0.34), (1.0, 0.94, 0.56)],
                 dike=(0.42, 0.56, 0.28), path=(0.88, 0.78, 0.60), fore='cosmos', haze=(0.80, 0.88, 0.94), mist=0.0, L=(-0.5, -0.86)),
    'blizzard': dict(sky=[(0, (0.06, 0.07, 0.16)), (0.6, (0.12, 0.13, 0.27)), (1, (0.22, 0.22, 0.38))],
                     sun=None, cloud=[(0.08, 0.09, 0.18), (0.13, 0.14, 0.26), (0.18, 0.19, 0.33), (0.26, 0.27, 0.42)],
                     far=(0.20, 0.21, 0.36), near=(0.16, 0.17, 0.30), hill=[(0.20, 0.21, 0.36), (0.30, 0.31, 0.48), (0.44, 0.45, 0.62), (0.60, 0.62, 0.78)],
                     tree='bare', field='snow', snow=[(0.26, 0.28, 0.46), (0.40, 0.42, 0.62), (0.58, 0.60, 0.78), (0.78, 0.80, 0.94)],
                     dike=(0.40, 0.42, 0.60), path=(0.44, 0.46, 0.64), fore='drift', haze=(0.30, 0.32, 0.50), mist=0.25, L=(-0.9, -0.44)),
    'spring': dict(sky=[(0, (0.50, 0.70, 0.88)), (0.55, (0.76, 0.86, 0.92)), (1, (0.98, 0.94, 0.86))],
                   sun=(600, 380, (1.0, 0.98, 0.90), 40), cloud=[(0.70, 0.74, 0.86), (0.90, 0.90, 0.94), (0.98, 0.97, 0.96), (1.0, 1.0, 1.0)],
                   far=(0.62, 0.72, 0.80), near=(0.46, 0.60, 0.56), hill=[(0.34, 0.52, 0.32), (0.48, 0.66, 0.36), (0.64, 0.78, 0.42), (0.84, 0.90, 0.56)],
                   tree='leaf', field='paddy', dike=(0.48, 0.68, 0.32), path=(0.86, 0.80, 0.66), fore='canola',
                   haze=(0.92, 0.94, 0.92), mist=0.2, L=(-0.6, -0.8)),
}

SEASONS.update({
    'autumn': dict(sky=[(0, (0.34, 0.52, 0.76)), (0.6, (0.68, 0.76, 0.84)), (1, (0.98, 0.88, 0.70))],
                   sun=None, cloud=[(0.66, 0.66, 0.78), (0.88, 0.86, 0.88), (0.98, 0.95, 0.92), (1.0, 1.0, 0.98)],
                   far=(0.58, 0.60, 0.74), near=(0.52, 0.42, 0.40),
                   hill=[(0.42, 0.24, 0.16), (0.62, 0.34, 0.18), (0.80, 0.50, 0.22), (0.96, 0.72, 0.38)],
                   tree='red', field='rice', rice=[(0.66, 0.40, 0.14), (0.84, 0.56, 0.18), (0.94, 0.70, 0.28), (1.0, 0.84, 0.48)],
                   dike=(0.50, 0.46, 0.24), path=(0.86, 0.74, 0.58), fore='cosmos', haze=(0.96, 0.88, 0.76), mist=0.15, L=(0.6, -0.8)),
    'sunset': dict(sky=[(0, (0.26, 0.22, 0.44)), (0.45, (0.66, 0.36, 0.46)), (0.8, (0.98, 0.54, 0.30)), (1, (1.0, 0.74, 0.42))],
                   sun=(860, 515, (1.0, 0.82, 0.52), 52), cloud=[(0.38, 0.24, 0.40), (0.62, 0.34, 0.42), (0.90, 0.50, 0.42), (1.0, 0.72, 0.50)],
                   far=(0.52, 0.34, 0.48), near=(0.38, 0.24, 0.36),
                   hill=[(0.22, 0.16, 0.24), (0.34, 0.24, 0.30), (0.52, 0.34, 0.34), (0.86, 0.52, 0.36)],
                   tree='red', field='stubble', stub=[(0.42, 0.26, 0.22), (0.62, 0.40, 0.28), (0.82, 0.56, 0.34), (0.98, 0.74, 0.46)],
                   dike=(0.40, 0.30, 0.26), path=(0.78, 0.56, 0.44), fore='none', haze=(0.98, 0.66, 0.46), mist=0.35, L=(-0.95, -0.3),
                   caps=0.0),
    'rain': dict(sky=[(0, (0.34, 0.37, 0.40)), (0.7, (0.52, 0.55, 0.56)), (1, (0.66, 0.68, 0.66))],
                 sun=None, cloud=[(0.30, 0.32, 0.36), (0.40, 0.42, 0.45), (0.50, 0.52, 0.54), (0.60, 0.62, 0.62)],
                 far=(0.48, 0.52, 0.54), near=(0.38, 0.42, 0.40),
                 hill=[(0.24, 0.28, 0.22), (0.34, 0.38, 0.28), (0.46, 0.48, 0.34), (0.58, 0.58, 0.44)],
                 tree='sparse', field='stubble', stub=[(0.26, 0.22, 0.18), (0.38, 0.32, 0.24), (0.50, 0.44, 0.32), (0.62, 0.56, 0.42)],
                 dike=(0.34, 0.38, 0.26), path=(0.52, 0.46, 0.38), fore='none', haze=(0.64, 0.66, 0.66), mist=0.55, L=(-0.5, -0.86),
                 caps=0.0),
    'frost': dict(sky=[(0, (0.50, 0.60, 0.78)), (0.6, (0.80, 0.84, 0.90)), (1, (0.98, 0.90, 0.84))],
                  sun=(1720, 578, (1.0, 0.92, 0.82), 36), cloud=[(0.62, 0.66, 0.80), (0.80, 0.82, 0.90), (0.92, 0.92, 0.95), (1.0, 0.98, 0.96)],
                  far=(0.66, 0.70, 0.82), near=(0.56, 0.60, 0.70),
                  hill=[(0.40, 0.44, 0.50), (0.54, 0.58, 0.64), (0.70, 0.74, 0.80), (0.90, 0.92, 0.96)],
                  tree='bare', field='stubble', stub=[(0.50, 0.50, 0.56), (0.66, 0.66, 0.72), (0.80, 0.82, 0.88), (0.94, 0.95, 0.98)],
                  dike=(0.60, 0.64, 0.66), path=(0.82, 0.82, 0.86), fore='none', haze=(0.92, 0.92, 0.96), mist=0.55, L=(0.8, -0.6),
                  caps=0.5),
    'dusk': dict(sky=[(0, (0.12, 0.13, 0.28)), (0.6, (0.28, 0.26, 0.44)), (1, (0.50, 0.42, 0.54))],
                 sun=None, cloud=[(0.16, 0.16, 0.30), (0.24, 0.23, 0.38), (0.34, 0.31, 0.46), (0.46, 0.40, 0.54)],
                 far=(0.28, 0.27, 0.42), near=(0.22, 0.21, 0.34),
                 hill=[(0.20, 0.20, 0.32), (0.30, 0.30, 0.44), (0.44, 0.44, 0.58), (0.62, 0.62, 0.76)],
                 tree='bare', field='stubble', stub=[(0.28, 0.27, 0.40), (0.40, 0.39, 0.54), (0.56, 0.55, 0.70), (0.74, 0.74, 0.88)],
                 dike=(0.34, 0.34, 0.48), path=(0.50, 0.50, 0.64), fore='none', haze=(0.40, 0.38, 0.54), mist=0.35, L=(-0.6, -0.8),
                 caps=1.0),
    'moon': dict(sky=[(0, (0.04, 0.06, 0.15)), (0.7, (0.10, 0.14, 0.28)), (1, (0.20, 0.24, 0.40))],
                 sun=None, moon=(880, 230, 44), stars=True,
                 cloud=[(0.08, 0.10, 0.20), (0.14, 0.16, 0.28), (0.22, 0.26, 0.40), (0.42, 0.48, 0.64)],
                 far=(0.20, 0.24, 0.40), near=(0.16, 0.20, 0.34),
                 hill=[(0.22, 0.26, 0.42), (0.34, 0.40, 0.58), (0.52, 0.58, 0.76), (0.76, 0.82, 0.96)],
                 tree='bare', field='snow', snow=[(0.26, 0.32, 0.50), (0.42, 0.50, 0.70), (0.62, 0.70, 0.88), (0.84, 0.90, 1.0)],
                 dike=(0.42, 0.48, 0.66), path=(0.48, 0.54, 0.72), fore='none', haze=(0.24, 0.28, 0.46), mist=0.2, L=(-0.7, -0.7)),
    'thaw': dict(sky=[(0, (0.54, 0.64, 0.78)), (0.6, (0.78, 0.82, 0.86)), (1, (0.92, 0.90, 0.84))],
                 sun=None, cloud=[(0.66, 0.68, 0.78), (0.84, 0.84, 0.88), (0.94, 0.94, 0.94), (1.0, 1.0, 0.98)],
                 far=(0.62, 0.66, 0.76), near=(0.48, 0.52, 0.52),
                 hill=[(0.34, 0.32, 0.26), (0.46, 0.44, 0.32), (0.60, 0.58, 0.40), (0.80, 0.78, 0.60)],
                 tree='bare', field='thaw', dike=(0.46, 0.46, 0.30), path=(0.70, 0.62, 0.50), fore='none',
                 haze=(0.86, 0.86, 0.86), mist=0.3, L=(-0.6, -0.8)),
})

def _ridge(w, rng, base, amp, freq, seed):
    xs = np.arange(w)
    n = fbm(w, 8, seed=seed, octaves=5, base=2)[4]
    return base - amp * (0.5 + 0.5 * np.sin(xs * freq + seed)) * 0.4 - n * amp * 0.5

def _dikes():
    """horizontal dike y positions and converging dike endpoints (world)"""
    hs = [HOR + 6 + 720 * (k / 9) ** 1.9 for k in range(1, 10)]
    ds = [(-600, WH), (300, WH), (1150, WH), (2050, WH), (3200, WH)]
    return hs, ds

def paint_sky(S):
    def p(c, rng):
        vgrad(c, 0, 0, WW, HOR + 20, S['sky'])
        if S['sun'] is not None:
            x, y, col, r = S['sun']
            radial(c, x, y, r * 9, col, 0.45)
            radial(c, x, y, r * 3, col, 0.5)
            c.arc(x, y, r, 0, TAU)
            fillc(c, lc(col, (1, 1, 1), 0.5))
        if S.get('stars'):
            for _ in range(420):
                x, y = rng.uniform(0, WW), rng.uniform(0, HOR - 60) ** 1.0
                r = rng.uniform(0.8, 2.2) * (2.0 if rng.random() < 0.03 else 1)
                c.arc(x, y * (0.6 + 0.4 * rng.random()), r, 0, TAU)
                fillc(c, (0.92, 0.94, 1.0), rng.uniform(0.4, 1.0))
        if S.get('moon'):
            x, y, r = S['moon']
            radial(c, x, y, r * 7, (0.70, 0.76, 0.96), 0.25)
            radial(c, x, y, r * 2.4, (0.86, 0.90, 1.0), 0.35)
            c.arc(x, y, r, 0, TAU)
            fillc(c, (0.97, 0.96, 0.88))
            for (dx, dy, rr) in ((-12, -8, 9), (10, 12, 7), (14, -14, 5)):
                c.arc(x + dx, y + dy, rr, 0, TAU)
                fillc(c, (0.86, 0.85, 0.80), 0.7)
    return p

def paint_clouds(S, key):
    def p(w, h, rng):
        groups = []
        spec = {'dawn': ((380, 230, 640, 90), (1180, 160, 760, 110), (1980, 260, 560, 80), (760, 400, 620, 56),
                         (1600, 430, 560, 46), (2200, 470, 380, 34)),
                'noon': ((300, 280, 520, 170), (1100, 240, 700, 210), (1950, 300, 560, 180), (700, 470, 380, 70),
                         (1600, 500, 420, 60)),
                'blizzard': ((200, 200, 900, 260), (1100, 160, 1100, 300), (2100, 220, 900, 260), (700, 420, 900, 160),
                             (1700, 440, 900, 150)),
                'autumn': ((300, 260, 560, 120), (1150, 200, 700, 140), (2000, 280, 560, 110), (750, 440, 500, 50),
                           (1650, 470, 460, 44)),
                'sunset': ((300, 250, 520, 120), (1500, 210, 620, 130), (2150, 300, 420, 100), (1350, 470, 380, 46),
                           (1950, 500, 340, 40)),
                'rain': ((200, 180, 1000, 230), (1150, 150, 1100, 260), (2150, 200, 1000, 230), (700, 400, 1000, 150),
                         (1700, 420, 1000, 140)),
                'frost': ((500, 240, 520, 60), (1350, 200, 640, 70), (2100, 280, 520, 50)),
                'dusk': ((200, 200, 900, 180), (1150, 160, 1000, 200), (2150, 220, 900, 180), (700, 420, 900, 90)),
                'moon': ((300, 380, 600, 50), (1700, 340, 700, 60), (2200, 450, 500, 36)),
                'thaw': ((450, 240, 560, 90), (1300, 190, 700, 110), (2100, 270, 560, 80), (900, 430, 520, 44)),
                'spring': ((500, 220, 520, 80), (1300, 170, 640, 96), (2050, 250, 520, 70), (950, 400, 500, 44),
                           (1800, 420, 460, 40))}[key]
        for (x, y, cw, ch) in spec:
            groups.append((cloud_circles(rng, x, y, cw, ch, rows=3), flat_bottom_clip(x - cw, x + cw,
                                                                                   lambda xx, y=y: y + 4 * math.sin(xx * 0.02))))
        H_ = np.zeros((h, w), F32)
        for circles, clip in groups:
            hh, _ = dome_field(w, h, circles, clip=clip)
            H_ = np.maximum(H_, hh)
        m = np.clip(H_ / 0.04, 0, 1)
        Lx, Ly = S['L']
        arr = celpaint_h(H_, m, S['cloud'], light=(Lx, Ly), step=9, gain=5.0, cuts=(0.40, 0.54, 0.68), seed=7)
        far = np.clip((np.arange(h, dtype=F32)[:, None] - 200) / 380, 0, 1)
        hz = np.array(S['haze'], F32)
        arr[..., :3] = arr[..., :3] * (1 - 0.45 * far[..., None]) + hz * arr[..., 3:4] * 0.45 * far[..., None]
        return arr
    return p

def paint_land(S, key):
    """mountains, hill, tree, field, dikes, path -- one RGBA array"""
    def p(w, h, rng):
        cv = Canvas(w, h); c = cv.c
        # far ridges: three soft layers (aerial perspective)
        xs = np.arange(-20, w + 21, 8)
        ridge_cols = [lc(S['far'], S['haze'], 0.35), S['far'], S['near']]
        for k, (base, amp) in enumerate(((HOR - 70, 120), (HOR - 30, 110), (HOR - 4, 70))):
            ph = [1.3 + k * 2.1, 0.4 + k, 2.2 - k]
            pts = [(-20, HOR + 20)]
            for x in xs:
                yv = (0.55 * math.sin(x * 0.0019 + ph[0]) + 0.30 * math.sin(x * 0.0047 + ph[1]) +
                      0.15 * math.sin(x * 0.011 + ph[2]))
                pts.append((x, base - amp * (0.55 + 0.5 * yv)))
            pts.append((w + 20, HOR + 20))
            col = ridge_cols[k]
            poly(c, pts)
            fillc(c, col)
            # light-side band along the ridge line
            c.save(); poly(c, pts); c.clip()
            for x in range(0, w, 3):
                i = int((x + 20) / 8)
                y0 = pts[min(i + 1, len(pts) - 2)][1]
                line(c, x, y0 + 3, x + 2, y0 + 12 + 8 * math.sin(x * 0.03), 3, lc(col, S['haze'], 0.30), 0.22)
            c.restore()
            if key == 'spring' and k == 2:
                for _ in range(220):
                    x = rng.uniform(0, w); y = rng.uniform(HOR - 60, HOR)
                    c.arc(x, y, rng.uniform(2, 5), 0, TAU)
                    fillc(c, (0.92, 0.50, 0.66) if rng.random() < 0.7 else (1.0, 0.86, 0.90), 0.85)
            if key in ('dawn', 'noon') and k == 2:
                for _ in range(200):
                    x = rng.uniform(0, w); y = rng.uniform(HOR - 50, HOR)
                    c.arc(x, y, rng.uniform(2, 5), 0, TAU)
                    fillc(c, (0.86, 0.42, 0.20) if rng.random() < 0.6 else (0.92, 0.70, 0.24), 0.55)
        arr = cv.rgba()
        # hill on the left (cel volume)
        def hill(cc, r):
            cc.move_to(-40, HOR + 40)
            cc.curve_to(100, HOR - 60, 300, HOR - 120, 520, HOR - 96)
            cc.curve_to(760, HOR - 70, 900, HOR - 10, 1040, HOR + 40)
            cc.close_path()
            cc.fill()
        hm = mask_draw(w, h, hill, rng)
        hh = cv2.GaussianBlur(hm, (0, 0), 60) * hm
        ha = celpaint_h(hh, hm, S['hill'], light=S['L'], step=30, gain=3.0, cuts=(0.33, 0.48, 0.64), seed=31, blotch=0.10)
        arr = over(arr, ha)
        cv = Canvas(w, h); c = cv.c
        c.save(); hill(c, rng) if False else None
        def hillp(cc):
            cc.move_to(-40, HOR + 40)
            cc.curve_to(100, HOR - 60, 300, HOR - 120, 520, HOR - 96)
            cc.curve_to(760, HOR - 70, 900, HOR - 10, 1040, HOR + 40)
            cc.close_path()
        hillp(c); c.clip()
        hcol = S['hill'][2]
        for _ in range(2600):
            x = rng.uniform(0, 1040); y = rng.uniform(HOR - 130, HOR + 30)
            line(c, x, y, x + rng.uniform(-2, 2), y - rng.uniform(4, 10), 2, lc(hcol, S['hill'][3] if rng.random() < 0.4 else S['hill'][1], 0.5), 0.5)
        for (bx, by, br) in ((140, HOR - 10, 52), (700, HOR - 40, 44), (880, HOR + 6, 36)):
            def bush(cc, bx=bx, by=by, br=br):
                smooth_path(cc, [(bx - br, by), (bx - br * 0.9, by - br * 0.6), (bx - br * 0.3, by - br), (bx + br * 0.4, by - br * 0.9),
                                 (bx + br, by - br * 0.3), (bx + br, by)])
            cel(c, bush, S['hill'][1], S['hill'][0], S['L'], off=6, lw=2)
        c.restore()
        if key == 'spring':
            for _ in range(140):
                x = rng.uniform(20, 1000); y = rng.uniform(HOR - 90, HOR + 20)
                if y < HOR - 100 + abs(x - 520) * 0.12:
                    continue
                c.arc(x, y, rng.uniform(3, 7), 0, TAU)
                fillc(c, (0.92, 0.48, 0.66) if rng.random() < 0.6 else (1.0, 0.92, 0.94), 0.9)
        if key == 'blizzard':
            for _ in range(300):
                x = rng.uniform(0, 1000); y = rng.uniform(HOR - 110, HOR + 30)
                line(c, x - 9, y, x + 9, y - 1, 3, (0.70, 0.72, 0.88), 0.45)
        arr = over(arr, cv.rgba())
        # ---- field
        hs, ds = _dikes()
        fm = np.zeros((h, w), F32); fm[HOR:] = 1
        yy = np.arange(h, dtype=F32)[:, None] * np.ones((1, w), F32)
        depth = np.clip((yy - HOR) / (h - HOR), 0, 1)
        if S['field'] in ('rice',):
            pal = S['rice']
            wave = fbm(w, h, seed=41, octaves=5, base=3) * 0.16
            ex = 0.12 - depth * 0.18 + wave
            fa = celpaint_h(fm * 0.5, fm, pal, light=S['L'], step=1, gain=0.0, seed=42, blotch=0.0, namp=0.0, extra=ex,
                            cuts=(0.36, 0.50, 0.64), soft=0.04)
        elif S['field'] == 'snow':
            pal = S['snow']
            wave = fbm(w, h, seed=43, octaves=5, base=4) * 0.05
            fa = celpaint_h(fm * 0.5, fm, pal, light=S['L'], step=1, gain=0.0, seed=44, blotch=0.0, namp=0.0,
                            extra=0.10 - depth * 0.12 + wave, cuts=(0.34, 0.48, 0.62), soft=0.03)
        elif S['field'] == 'stubble':
            pal = S['stub']
            wave = fbm(w, h, seed=46, octaves=5, base=3) * 0.12
            fa = celpaint_h(fm * 0.5, fm, pal, light=S['L'], step=1, gain=0.0, seed=47, blotch=0.0, namp=0.0,
                            extra=0.10 - depth * 0.16 + wave, cuts=(0.36, 0.50, 0.64), soft=0.04)
        elif S['field'] == 'thaw':
            pal = [(0.30, 0.26, 0.20), (0.44, 0.38, 0.28), (0.58, 0.52, 0.38), (0.72, 0.68, 0.54)]
            wave = fbm(w, h, seed=48, octaves=5, base=3) * 0.14
            fa = celpaint_h(fm * 0.5, fm, pal, light=S['L'], step=1, gain=0.0, seed=49, blotch=0.0, namp=0.0,
                            extra=0.10 - depth * 0.14 + wave, cuts=(0.36, 0.50, 0.64), soft=0.04)
        else:
            sky = np.zeros((h, w, 3), F32)
            for k in range(3):
                sky[..., k] = np.interp(depth, [0, 0.3, 1], [0.86, 0.66, 0.44] if k == 0 else
                                        ([0.90, 0.78, 0.62] if k == 1 else [0.92, 0.88, 0.82]))
            wave = fbm(w, h, seed=45, octaves=4, base=6)[..., None] * 0.03
            fa = np.dstack([(sky + wave) * fm[..., None], fm]).astype(F32)
        arr = over(arr, fa)
        cv = Canvas(w, h); c = cv.c
        dcol = S['dike']
        hy = [HOR + 8 + 700 * (k / 6) ** 1.85 for k in range(1, 7)]
        rows = [HOR + 4] + hy + [h + 40]
        def dike_y(y0, x):
            k = (y0 - HOR) / (h - HOR)
            return y0 + (6 + 30 * k) * math.sin(x * 0.0021 + y0 * 0.05) + (3 + 12 * k) * math.sin(x * 0.007 + y0)
        # plot tints
        tints = {'rice': [((0.95, 0.62, 0.20), 0.20), ((1.0, 0.92, 0.55), 0.22), ((0.70, 0.66, 0.24), 0.18),
                          ((0.86, 0.46, 0.16), 0.14), ((1.0, 0.86, 0.40), 0.0)],
                 'snow': [((0.86, 0.88, 1.0), 0.18), ((0.40, 0.42, 0.64), 0.14), ((1, 1, 1), 0.0), ((0.70, 0.72, 0.92), 0.12)],
                 'paddy': [((0.70, 0.86, 0.94), 0.16), ((0.98, 0.92, 0.78), 0.18), ((0.62, 0.80, 0.56), 0.14),
                           ((1, 1, 1), 0.0)],
                 'stubble': [((0.95, 0.70, 0.40), 0.14), ((0.40, 0.30, 0.24), 0.12), ((1, 1, 1), 0.0), ((0.80, 0.60, 0.36), 0.10)],
                 'thaw': [((0.92, 0.94, 0.98), 0.35), ((0.30, 0.26, 0.20), 0.14), ((0.60, 0.70, 0.40), 0.10), ((1, 1, 1), 0.0)]}[S['field']]
        cuts_all = []
        for r_ in range(len(rows) - 1):
            ya, yb = rows[r_], rows[r_ + 1]
            k = (ya - HOR) / (h - HOR)
            ncut = rng.integers(2, 5)
            xs_ = sorted(rng.uniform(-300, w + 300, ncut))
            cuts_all.append(xs_)
            bounds = [-800] + list(xs_) + [w + 800]
            for i in range(len(bounds) - 1):
                tcol, ta = tints[rng.integers(0, len(tints))]
                xa, xb = bounds[i], bounds[i + 1]
                def lean(x, y):          # shift x toward the vanishing point with depth
                    return VP[0] + (x - VP[0]) * (y - VP[1]) / max(1, (ya - VP[1]))
                pts = [(x, dike_y(ya, x)) for x in np.linspace(xa, xb, 20)]
                pts += [(lean(x, yb), dike_y(yb, lean(x, yb)) if yb < h else yb) for x in np.linspace(xb, xa, 20)]
                poly(c, pts)
                src(c, tcol, ta * (0.6 + 0.4 * k))
                c.fill()
                # brush strokes following the rows inside each plot
                c.save(); poly(c, pts); c.clip()
                nb = int(40 + 220 * k)
                for _ in range(nb):
                    yy0 = rng.uniform(ya, yb); kk = (yy0 - HOR) / (h - HOR)
                    xx0 = rng.uniform(min(xa, xb) - 50, max(xa, xb) + 50)
                    Lb = 30 + 220 * kk
                    line(c, xx0, yy0, xx0 + Lb, yy0 + rng.uniform(-2, 2) * kk, 2 + 9 * kk,
                         lc(tcol, (1, 1, 1), rng.uniform(0, 0.4)), rng.uniform(0.05, 0.14))
                c.restore()
        # dikes: curving horizontal ridges + short dividers aimed at the vanishing point
        for y0 in hy:
            k = (y0 - HOR) / (h - HOR)
            wd = 3 + 30 * k
            xs_d = list(range(-40, w + 41, 20))
            wv = [wd * (0.7 + 0.6 * (0.5 + 0.5 * math.sin(x * 0.006 + y0) * math.sin(x * 0.0023 + 1.7 * y0))) for x in xs_d]
            top = [(x, dike_y(y0, x)) for x in xs_d]
            poly(c, top + [(px, py + ww) for (px, py), ww in zip(top[::-1], wv[::-1])])
            fillc(c, dcol)
            poly(c, [(px, py + ww * 0.5) for (px, py), ww in zip(top, wv)] + [(px, py + ww) for (px, py), ww in zip(top[::-1], wv[::-1])])
            fillc(c, cm(dcol, 0.70))
            # brushwork along the ridge + grass tufts on top
            for _ in range(int(80 + 500 * k)):
                x = rng.uniform(-40, w + 40)
                yt = dike_y(y0, x)
                Lb = 6 + 40 * k
                line(c, x, yt + rng.uniform(0, wd * 0.45), x + Lb, yt + rng.uniform(0, wd * 0.45), 1.5 + 4 * k,
                     lc(dcol, (1, 1, 0.8) if rng.random() < 0.5 else (0.1, 0.15, 0.05), rng.uniform(0.1, 0.35)), 0.55)
            for _ in range(int(30 + 260 * k)):
                x = rng.uniform(-40, w + 40)
                yt = dike_y(y0, x) + 1
                hh_ = 3 + 18 * k
                for j in range(3):
                    line(c, x + j * 2 * k, yt, x + (j - 1) * 3 * k + rng.uniform(-1, 1), yt - hh_ * rng.uniform(0.6, 1.1),
                         0.8 + 1.6 * k, lc(dcol, (0.9, 0.95, 0.6), rng.uniform(0.0, 0.5)), 0.9)
            inkline(c, [(px, py) for (px, py) in top], 1.0 + 1.2 * k, lc(dcol, (1, 1, 1), 0.4), 0.55, taper=False)
            if key == 'spring':
                for _ in range(int(60 + 200 * k)):
                    x = rng.uniform(0, w)
                    c.arc(x, dike_y(y0, x) + rng.uniform(0, wd * 0.5), 1.5 + 6 * k, 0, TAU)
                    fillc(c, (0.98, 0.86, 0.20) if rng.random() < 0.8 else (1, 0.98, 0.9), 0.95)
            if key == 'blizzard':
                for _ in range(int(20 + 80 * k)):
                    x = rng.uniform(0, w)
                    yy0 = dike_y(y0, x) + wd * 0.3
                    line(c, x, yy0, x + rng.uniform(-2, 2), yy0 - 4 - 10 * k, 1 + 2 * k, (0.30, 0.28, 0.36), 0.8)
        for r_ in range(len(rows) - 2):
            ya, yb = rows[r_], rows[r_ + 1]
            for x in cuts_all[r_]:
                k0 = (ya - HOR) / (h - HOR); k1 = (yb - HOR) / (h - HOR)
                xb_ = VP[0] + (x - VP[0]) * (yb - VP[1]) / max(1, (ya - VP[1]))
                y0_, y1_ = dike_y(ya, x), dike_y(yb, xb_)
                c.move_to(x - (2 + 15 * k0), y0_); c.line_to(x + (2 + 15 * k0), y0_)
                c.line_to(xb_ + (2 + 15 * k1), y1_); c.line_to(xb_ - (2 + 15 * k1), y1_); c.close_path()
                fillc(c, cm(dcol, 0.85))
        # dirt path
        def path(cc):
            pts = []
            for u in np.linspace(0, 1, 30):
                x = lerp(1180, 380, u ** 1.1) + 220 * math.sin(u * 3.4)
                y = HOR + 4 + (h - HOR) * u ** 1.9
                pts.append((x, y, 3 + 260 * u ** 2))
            L_ = [(x - wd / 2, y) for x, y, wd in pts]
            R_ = [(x + wd / 2, y) for x, y, wd in pts]
            poly(cc, L_ + R_[::-1])
        def pathfill(cc):
            path(cc)
        cel(c, pathfill, S['path'], cm(S['path'], 0.80), S['L'], off=12, lw=1.6)
        arr = over(arr, cv.rgba())
        # ---- field texture (rice heads / stubble / snow / seedlings)
        cv = Canvas(w, h); c = cv.c
        if S['field'] == 'rice':
            pal = S['rice']
            for _ in range(42000):
                y = HOR + (rng.random() ** 1.7) * (h - HOR)
                k = (y - HOR) / (h - HOR)
                x = rng.uniform(0, w)
                L_ = 2 + 22 * k
                lean = rng.uniform(-0.3, 0.5)
                col = pal[rng.integers(1, 4)]
                line(c, x, y, x + lean * L_, y - L_, 0.8 + 2.4 * k, col, rng.uniform(0.35, 0.8))
            for _ in range(2600):                      # drooping heads in the foreground
                y = HOR + (0.55 + 0.45 * rng.random()) * (h - HOR)
                k = (y - HOR) / (h - HOR)
                x = rng.uniform(0, w)
                L_ = 14 + 26 * k
                pts = qcurve((x, y), (x + L_ * 0.4, y - L_), (x + L_ * 0.75, y - L_ * 0.55), 6)
                inkline(c, pts, 2 + 4 * k, pal[0], 0.9, taper=True)
                inkline(c, pts, 1 + 2.4 * k, pal[3], 0.9, taper=True)
        elif S['field'] == 'snow':
            for _ in range(5000):
                y = HOR + (rng.random() ** 1.5) * (h - HOR)
                k = (y - HOR) / (h - HOR)
                x = rng.uniform(0, w)
                line(c, x, y, x + rng.uniform(-1, 1), y - 3 - 12 * k, 0.8 + 2 * k, (0.34, 0.30, 0.38), 0.75)
            # snow-capped straw stacks
            for (sx, sy, sz) in ((520, 760, 0.9), (880, 700, 0.6), (2050, 820, 1.2), (1900, 690, 0.55), (300, 980, 1.5),
                                 (2250, 1120, 1.9)):
                def stack(cc, sx=sx, sy=sy, sz=sz):
                    smooth_path(cc, [(sx - 40 * sz, sy), (sx - 34 * sz, sy - 40 * sz), (sx - 10 * sz, sy - 78 * sz),
                                     (sx + 12 * sz, sy - 80 * sz), (sx + 36 * sz, sy - 42 * sz), (sx + 40 * sz, sy)])
                cel(c, stack, (0.56, 0.50, 0.50), (0.36, 0.32, 0.40), S['L'], off=8 * sz, lw=2.2)
                def cap(cc, sx=sx, sy=sy, sz=sz):
                    smooth_path(cc, [(sx - 36 * sz, sy - 30 * sz), (sx - 12 * sz, sy - 78 * sz), (sx + 14 * sz, sy - 82 * sz),
                                     (sx + 40 * sz, sy - 30 * sz), (sx + 10 * sz, sy - 46 * sz), (sx - 14 * sz, sy - 40 * sz)])
                cel(c, cap, (0.86, 0.88, 0.98), (0.56, 0.58, 0.80), S['L'], off=6 * sz, lw=2.0)
                def base(cc, sx=sx, sy=sy, sz=sz):
                    c.save(); cc.translate(sx, sy); cc.scale(1, 0.25); cc.arc(0, 0, 60 * sz, 0, TAU); c.restore()
                cel(c, base, (0.70, 0.72, 0.90), (0.46, 0.48, 0.70), S['L'], off=3, lw=0)
        if S['field'] in ('stubble', 'thaw'):
            pal = S.get('stub', [(0.30, 0.26, 0.20), (0.44, 0.38, 0.28), (0.58, 0.52, 0.38), (0.72, 0.68, 0.54)])
            for r_ in range(-60, 61):                 # cut stubble rows converging to the vanishing point
                bx = VP[0] + r_ * 60
                for u in np.linspace(0.03, 1, 40) ** 1.7:
                    x = lerp(VP[0], bx, u) + rng.uniform(-3, 3); y = lerp(VP[1] + 12, WH, u)
                    k = (y - HOR) / (h - HOR)
                    if x < -20 or x > w + 20:
                        continue
                    hgt = 2 + 14 * k
                    for j in (-1, 0, 1):
                        line(c, x + j * hgt * 0.3, y, x + j * hgt * 0.45, y - hgt, 0.8 + 1.4 * k, pal[3] if j == 0 else pal[1], 0.9)
            if S['field'] == 'thaw':
                # snow lingers in the shade just below each dike, and in a few hollows; puddles mirror the sky
                for k_ in range(1, 7):
                    yb = HOR + 8 + 700 * (k_ / 6) ** 1.85
                    k = (yb - HOR) / (h - HOR)
                    x = rng.uniform(-200, 0)
                    while x < w + 100:
                        L_ = (60 + 520 * k) * rng.uniform(0.3, 1.0)
                        th = (3 + 26 * k) * rng.uniform(0.5, 1.1)
                        n_ = 9
                        top = [(x + L_ * i / (n_ - 1), yb + 2 + rng.uniform(-1, 1) * th * 0.15) for i in range(n_)]
                        bot = [(x + L_ * (1 - i / (n_ - 1)) + rng.uniform(-6, 6) * k, yb + th * (0.4 + 0.9 * math.sin(math.pi * (1 - i / (n_ - 1))) * rng.uniform(0.6, 1.2))) for i in range(n_)]
                        def band(cc, P=top + bot):
                            smooth_path(cc, P)
                        cel(c, band, (0.90, 0.92, 0.96), (0.70, 0.74, 0.86), S['L'], off=1 + 4 * k, lw=0)
                        x += L_ + rng.uniform(40, 400) * (0.3 + k)
                for _ in range(26):
                    y = HOR + 30 + (rng.random() ** 1.1) * (h - HOR - 30)
                    k = (y - HOR) / (h - HOR)
                    x = rng.uniform(0, w)
                    rx, ry = (30 + 200 * k) * rng.uniform(0.5, 1.2), (3 + 18 * k) * rng.uniform(0.6, 1.0)
                    P = [(x + rx * math.cos(a) * rng.uniform(0.7, 1.15), y + ry * math.sin(a) * rng.uniform(0.6, 1.2))
                         for a in np.linspace(0, TAU, 12, endpoint=False)]
                    def pud(cc, P=P):
                        smooth_path(cc, P)
                    snow_ = rng.random() < 0.35
                    cel(c, pud, (0.90, 0.92, 0.96) if snow_ else (0.70, 0.78, 0.86),
                        (0.70, 0.74, 0.86) if snow_ else (0.52, 0.60, 0.70), S['L'], off=1 + 3 * k, lw=0)
                    if not snow_:
                        line(c, x - rx * 0.4, y - ry * 0.1, x + rx * 0.2, y - ry * 0.1, 1 + 2 * k, (0.92, 0.94, 0.96), 0.7)
            caps = S.get('caps', 0.0)
            for (sx, sy, sz) in ((520, 760, 0.9), (880, 700, 0.6), (2050, 820, 1.2), (1900, 690, 0.55), (300, 980, 1.5),
                                 (2250, 1120, 1.9), (1150, 650, 0.4), (700, 860, 1.1)):
                scol = lc((0.86, 0.70, 0.40), pal[2], 0.5)
                def stack(cc, sx=sx, sy=sy, sz=sz):
                    smooth_path(cc, [(sx - 40 * sz, sy), (sx - 34 * sz, sy - 40 * sz), (sx - 10 * sz, sy - 78 * sz),
                                     (sx + 12 * sz, sy - 80 * sz), (sx + 36 * sz, sy - 42 * sz), (sx + 40 * sz, sy)])
                cel(c, stack, scol, cm(scol, 0.68), S['L'], off=9 * sz, lw=2.2)
                for q in range(int(8 * sz) + 3):
                    yq = sy - 10 * sz - q * 8
                    if yq < sy - 74 * sz:
                        break
                    inkline(c, [(sx - 30 * sz, yq), (sx + 30 * sz, yq - 3)], 1.0 + sz, cm(scol, 0.8), 0.5)
                line(c, sx - 36 * sz, sy - 40 * sz, sx + 36 * sz, sy - 42 * sz, 3 * sz, (0.50, 0.30, 0.18), 0.9)
                if caps > 0:
                    def cap(cc, sx=sx, sy=sy, sz=sz):
                        smooth_path(cc, [(sx - 28 * sz, sy - 46 * sz), (sx - 12 * sz, sy - 78 * sz), (sx + 14 * sz, sy - 82 * sz),
                                         (sx + 32 * sz, sy - 46 * sz), (sx + 10 * sz, sy - 56 * sz), (sx - 14 * sz, sy - 52 * sz)])
                    cel(c, cap, (0.90, 0.92, 1.0), (0.62, 0.64, 0.84), S['L'], off=5 * sz, lw=1.8, alpha=caps)
            if caps > 0.6:
                for _ in range(1600):
                    y = HOR + (rng.random() ** 1.4) * (h - HOR)
                    k = (y - HOR) / (h - HOR)
                    x = rng.uniform(0, w)
                    line(c, x, y, x + 6 + 40 * k, y, 1 + 3 * k, (0.80, 0.82, 0.96), 0.35 * caps)
        if S['field'] == 'snow':
            for _ in range(900):                      # wind-carved ridges
                y = HOR + (rng.random() ** 1.4) * (h - HOR)
                k = (y - HOR) / (h - HOR)
                x = rng.uniform(-100, w)
                L_ = 20 + 160 * k
                pts = qcurve((x, y), (x + L_ * 0.5, y - 3 - 8 * k), (x + L_, y + 2), 8)
                inkline(c, pts, 1 + 3 * k, (0.82, 0.84, 0.98), 0.55)
                inkline(c, [(px, py + 2 + 4 * k) for px, py in pts], 0.8 + 2 * k, (0.30, 0.32, 0.52), 0.45)
        if S['field'] == 'paddy':
            for _ in range(500):
                y = HOR + (rng.random() ** 1.4) * (h - HOR)
                k = (y - HOR) / (h - HOR)
                x = rng.uniform(0, w)
                line(c, x, y, x + 10 + 60 * k, y, 1 + 2 * k, (1, 1, 1), 0.35)
        elif S['field'] == 'paddy':
            # seedling rows converging, with reflections
            for r_ in range(-40, 41):
                bx = VP[0] + r_ * 70
                for u in np.linspace(0.02, 1, 46) ** 1.6:
                    x = lerp(VP[0], bx, u); y = lerp(VP[1] + 10, WH, u)
                    k = (y - HOR) / (h - HOR)
                    if x < -20 or x > w + 20:
                        continue
                    hgt = 3 + 26 * k
                    for j in (-1, 0, 1):
                        line(c, x + j * hgt * 0.15, y, x + j * hgt * 0.35, y - hgt, 0.8 + 1.8 * k,
                             (0.42, 0.66, 0.28) if j else (0.56, 0.78, 0.34), 0.95)
                    line(c, x, y + 1, x, y + hgt * 0.5, 0.6 + 1.2 * k, (0.40, 0.58, 0.42), 0.35)
        arr = over(arr, cv.rgba())
        # ---- persimmon tree
        tv = Canvas(w, h); c = tv.c
        tx, ty = TREE
        def trunk(cc):
            smooth_path(cc, [(tx - 12, ty + 6), (tx - 10, ty - 60), (tx - 30, ty - 120), (tx - 22, ty - 126), (tx - 2, ty - 80),
                             (tx + 18, ty - 140), (tx + 28, ty - 134), (tx + 10, ty - 70), (tx + 12, ty + 6)])
        cel(c, trunk, (0.36, 0.26, 0.22), (0.24, 0.17, 0.15), S['L'], off=5, lw=2.4)
        for (bx, by, ex_, ey_) in ((tx - 26, ty - 122, tx - 90, ty - 170), (tx + 24, ty - 136, tx + 90, ty - 190),
                                   (tx - 4, ty - 90, tx + 10, ty - 200)):
            inkline(c, qcurve((bx, by), ((bx + ex_) / 2, (by + ey_) / 2 - 20), (ex_, ey_), 8), 7, (0.28, 0.20, 0.17), 1.0)
        arr = over(arr, tv.rgba())
        if S['tree'] in ('kaki', 'leaf', 'red', 'sparse'):
            circ = []
            for _ in range(46):
                a = rng.uniform(0, TAU); d = rng.uniform(0, 1) ** 0.7
                circ.append((tx + math.cos(a) * 95 * d, ty - 175 + math.sin(a) * 58 * d, rng.uniform(34, 52), 0.75 + 0.25 * (1 - d)))
            hh, mm = dome_field(w, h, circ)
            pal = ([(0.24, 0.34, 0.20), (0.36, 0.48, 0.24), (0.52, 0.60, 0.28), (0.74, 0.74, 0.40)] if S['tree'] == 'kaki'
                   else [(0.30, 0.50, 0.24), (0.44, 0.66, 0.30), (0.62, 0.80, 0.38), (0.84, 0.92, 0.56)])
            if key in ('dawn', 'noon'):
                pal = [(0.50, 0.26, 0.16), (0.72, 0.38, 0.18), (0.88, 0.54, 0.22), (0.98, 0.76, 0.40)]
            if S['tree'] == 'red':
                pal = [(0.46, 0.12, 0.10), (0.70, 0.20, 0.12), (0.88, 0.36, 0.16), (0.98, 0.60, 0.28)]
            if S['tree'] == 'sparse':
                pal = [(0.30, 0.22, 0.16), (0.46, 0.30, 0.18), (0.60, 0.40, 0.22), (0.74, 0.54, 0.32)]
                circ = circ[::3]
                hh, mm = dome_field(w, h, circ)
            ca = celpaint_h(hh, mm, pal, light=S['L'], step=8, gain=5.0, seed=33)
            arr = over(arr, ca)
        tv = Canvas(w, h); c = tv.c
        if S['tree'] in ('kaki', 'bare', 'red', 'sparse'):
            n_f = {'kaki': 34, 'bare': 3, 'red': 18, 'sparse': 8}[S['tree']]
            for _ in range(n_f):
                a = rng.uniform(0, TAU); d = rng.uniform(0.2, 1) ** 0.6
                fx, fy = tx + math.cos(a) * 92 * d, ty - 172 + math.sin(a) * 58 * d
                def kaki(cc, fx=fx, fy=fy):
                    cc.arc(fx, fy, 6.5, 0, TAU)
                cel(c, kaki, (0.98, 0.52, 0.16), (0.78, 0.32, 0.10), S['L'], off=2.5, lw=1.4)
                line(c, fx - 2, fy - 6, fx + 2, fy - 6, 2, (0.26, 0.36, 0.18))
            if S['tree'] in ('bare', 'sparse'):
                snowy = key in ('moon', 'dusk', 'frost')
                for k in range(16):
                    a = -math.pi / 2 + rng.uniform(-1.1, 1.1)
                    L_ = rng.uniform(60, 120)
                    bx, by = tx + rng.normal(0, 30), ty - 140 + rng.normal(0, 30)
                    inkline(c, [(bx, by), (bx + math.cos(a) * L_, by + math.sin(a) * L_)], 3.5, (0.14, 0.12, 0.18), 1.0)
                    if snowy or key == 'blizzard':
                        line(c, bx, by - 3, bx + math.cos(a) * L_, by + math.sin(a) * L_ - 3, 3, (0.80, 0.82, 0.96), 0.7)
        arr = over(arr, tv.rgba())
        if key in ('spring', 'thaw'):
            mv = Canvas(w, h); c = mv.c
            jx, jy = JI_POS
            mcol = (0.44, 0.58, 0.30) if key == 'spring' else (0.46, 0.42, 0.30)
            def mound(cc):
                cc.move_to(500, h + 40)
                cc.curve_to(700, jy - 10, 1100, jy - 34, jx, jy - 36)
                cc.curve_to(1900, jy - 38, 2200, jy - 10, w + 40, jy + 10)
                cc.line_to(w + 40, h + 40)
                cc.close_path()
            cel(c, mound, mcol, cm(mcol, 0.72), S['L'], off=26, lw=2.0)
            c.save(); mound(c); c.clip()
            # value bands: lighter crest, darker toward the camera
            for i in range(5):
                yb_ = jy - 30 + i * 70
                c.rectangle(0, yb_, w, h); fillc(c, cm(mcol, 0.93), 0.35)
            hi = lc(mcol, (0.86, 0.92, 0.50) if key == 'spring' else (0.76, 0.70, 0.50), 0.45)
            for _ in range(9000):
                x = rng.uniform(500, w); y = jy - 40 + (rng.random() ** 1.5) * (h - jy + 40)
                k = (y - jy + 40) / (h - jy + 40)
                gcol = lc(cm(mcol, 0.8 + 0.1 * rng.random()), hi, rng.random() ** 2)
                ln = 8 + 26 * k
                line(c, x, y, x + rng.uniform(-4, 4) * (1 + k), y - ln, 1.6 + 2.6 * k, gcol, 0.9)
            if key == 'spring':
                for _ in range(220):                      # dandelions and violets
                    x = rng.uniform(560, w); y = jy - 30 + rng.random() ** 1.3 * (h - jy + 30)
                    k = (y - jy + 30) / (h - jy + 30)
                    fc = (0.98, 0.84, 0.24) if rng.random() < 0.7 else (0.66, 0.52, 0.86)
                    c.arc(x, y, 2.5 + 5 * k, 0, TAU); fillc(c, fc, 0.95)
            c.restore()
            # tufted crest silhouette
            for _ in range(700):
                x = rng.uniform(560, w)
                u = (x - 500) / (w - 500)
                yc = jy - 36 + 30 * (1 - u) ** 6 + 46 * max(0, u - 0.6) ** 2 * 6
                line(c, x, yc + 4, x + rng.uniform(-6, 6), yc - rng.uniform(6, 20), 2.2, lc(mcol, hi, rng.random() * 0.6), 0.9)
            if key == 'thaw':
                c.save(); mound(c); c.clip()
                for _ in range(14):
                    x = rng.uniform(600, w); y = rng.uniform(jy + 10, h)
                    rx, ry = rng.uniform(40, 120), rng.uniform(8, 20)
                    P = [(x + rx * math.cos(a) * rng.uniform(0.6, 1.2), y + ry * math.sin(a) * rng.uniform(0.6, 1.2))
                         for a in np.linspace(0, TAU, 11, endpoint=False)]
                    def sp(cc, P=P):
                        smooth_path(cc, P)
                    cel(c, sp, (0.92, 0.94, 0.98), (0.72, 0.76, 0.86), S['L'], off=4, lw=0)
                c.restore()
            arr = over(arr, mv.rgba())
        # haze / mist toward the horizon
        hz = np.array(S['haze'], F32)
        k = np.exp(-((yy - HOR) / 70) ** 2) * S['mist'] + np.clip((HOR - yy) / 260, 0, 1) * 0.0
        k = k + np.clip(1 - np.abs(yy - HOR) / 90, 0, 1) * 0.10
        arr[..., :3] = arr[..., :3] * (1 - k[..., None]) + hz * arr[..., 3:4] * k[..., None]
        # paper texture
        T = noise_tile(w, h, 'd')
        arr[..., :3] *= (1 + 0.012 * T)[..., None]
        return arr
    return p

def paint_fore(S, key):
    def p(c, rng):
        if S['fore'] == 'cosmos':
            for _ in range(70):
                side = rng.random() < 0.5
                x = rng.uniform(-40, 520) if side else rng.uniform(1900, WW + 40)
                base = WH + 20
                hgt = rng.uniform(140, 420)
                lean = rng.uniform(-60, 60)
                pts = qcurve((x, base), (x + lean * 0.3, base - hgt * 0.6), (x + lean, base - hgt), 8)
                inkline(c, pts, 3.5, (0.22, 0.38, 0.22), 1.0, taper=False)
                fx, fy = pts[-1]
                r = rng.uniform(12, 22)
                col = [(0.98, 0.62, 0.78), (1.0, 0.96, 0.96), (0.86, 0.30, 0.58)][rng.integers(0, 3)]
                for k in range(8):
                    a = k * TAU / 8 + rng.uniform(0, 0.3)
                    c.save(); c.translate(fx + math.cos(a) * r * 0.62, fy + math.sin(a) * r * 0.5)
                    c.rotate(a); c.scale(1, 0.48); c.arc(0, 0, r * 0.55, 0, TAU); c.restore()
                    fillc(c, col)
                    c.save(); c.translate(fx + math.cos(a) * r * 0.62, fy + math.sin(a) * r * 0.5)
                    c.rotate(a); c.scale(1, 0.48); c.arc(0, 0, r * 0.55, 0, TAU); c.restore()
                    strokec(c, cm(col, 0.7), 1.2, 0.8)
                c.arc(fx, fy, r * 0.25, 0, TAU)
                fillc(c, (0.98, 0.78, 0.18))
        elif S['fore'] == 'canola':
            for _ in range(90):
                side = rng.random() < 0.5
                x = rng.uniform(-40, 560) if side else rng.uniform(1860, WW + 40)
                hgt = rng.uniform(120, 380)
                pts = qcurve((x, WH + 20), (x + rng.uniform(-20, 20), WH - hgt * 0.6), (x + rng.uniform(-40, 40), WH - hgt), 8)
                inkline(c, pts, 4, (0.36, 0.56, 0.24), 1.0, taper=False)
                fx, fy = pts[-1]
                for k in range(14):
                    c.arc(fx + rng.normal(0, 14), fy + rng.normal(0, 18), rng.uniform(4, 8), 0, TAU)
                    fillc(c, (0.99, 0.86, 0.16) if rng.random() < 0.8 else (1.0, 0.95, 0.5))
        elif S['fore'] == 'none':
            pass
        elif S['fore'] == 'drift':
            def drift(cc, r):
                cc.move_to(-40, WH + 40)
                cc.curve_to(200, WH - 160, 600, WH - 60, 900, WH - 20)
                cc.line_to(900, WH + 40)
                cc.close_path()
                cc.move_to(1700, WH + 40)
                cc.curve_to(1900, WH - 80, 2200, WH - 190, WW + 40, WH - 120)
                cc.line_to(WW + 40, WH + 40)
                cc.close_path()
            cel(c, lambda cc: drift(cc, rng), (0.62, 0.64, 0.84), (0.38, 0.40, 0.62), S['L'], off=26, lw=3)
    return p

def season_layers(key):
    S = SEASONS[key]
    return dict(
        sky=Static(f'{key}_sky', WW, WH, paint_sky(S)),
        cloud=StaticArr(f'{key}_cl', WW, WH, paint_clouds(S, key)),
        land=StaticArr(f'{key}_land', WW, WH, paint_land(S, key)),
        fore=Static(f'{key}_fore', WW, WH, paint_fore(S, key)),
        S=S)


# ------------------------------------------------------------------ poster-colour repaint (cached on disk)
import os
def painted(key):
    path = f'cache/paint_{key}.png'
    if os.path.exists(path):
        from PIL import Image
        return np.asarray(Image.open(path), dtype=np.uint8)
    from painter import paint
    from PIL import Image
    Ls = season_layers(key)
    canvas = np.zeros((WH, WW, 3), F32)
    for st in (Ls['sky'], Ls['cloud'], Ls['land']):
        L_ = st.img.astype(F32) / 255
        a = L_[..., 3:4]
        canvas = L_[..., :3] + canvas * (1 - a)
    yy = np.arange(WH, dtype=F32)[:, None] * np.ones((1, WW), F32)
    sky = yy < HOR - 160
    lenmul = np.where(sky, 2.6, np.where(yy < HOR + 10, 1.4, 2.0)).astype(F32)
    bal = np.where(sky, 0.18, 0.45).astype(F32)
    cohw = np.where(sky, 0.25, 1.0).astype(F32)
    out = paint(canvas, hint=np.zeros((WH, WW), F32), seed=3, lenmul=lenmul, balpha_map=bal, coh_w=cohw)
    arr = np.dstack([np.clip(out * 255 + 0.5, 0, 255).astype(np.uint8), np.full((WH, WW), 255, np.uint8)])
    Image.fromarray(arr).save(path)
    return arr

class Painted:
    def __init__(self, key):
        self.img = painted(key)
    view = Static.view
