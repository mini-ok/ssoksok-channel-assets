# -*- coding: utf-8 -*-
"""솔이 (9, 해녀의 딸) and 꾸럭이 (baby octopus): cel drawing functions + model sheet.
Uses the verified cel renderer from 〈허수아비의 겨울〉 (wobbled silhouette, pressure ink, designed shadow, colored held line)."""
import sys, math
import numpy as np, cairo
sys.path.insert(0, '/home/claude/scarecrow')
from cel import cel, smooth_path, inkline, qcurve, Boil, set_frame, INK_C, INK_W

L0 = (-0.55, -0.83)
PAL = dict(
    skin=(0.99, 0.86, 0.75), skin_s=(0.93, 0.70, 0.61),
    hair=(0.17, 0.16, 0.24), hair_s=(0.10, 0.09, 0.16), hair_h=(0.32, 0.33, 0.48),
    coat=(0.99, 0.80, 0.22), coat_s=(0.91, 0.60, 0.15), coat_h=(1.0, 0.92, 0.55),
    toggle=(0.20, 0.24, 0.40), shoe=(0.22, 0.27, 0.42), shoe_s=(0.14, 0.17, 0.30),
    jar=(0.64, 0.42, 0.27), jar_s=(0.47, 0.29, 0.19), strap=(0.50, 0.34, 0.22),
    eye=(0.20, 0.13, 0.14), iris=(0.45, 0.28, 0.20), white=(1, 1, 1),
    mouth=(0.60, 0.20, 0.23), tongue=(0.95, 0.55, 0.55), blush=(0.98, 0.56, 0.52),
)

def fill(c, col, a=1.0):
    c.set_source_rgba(*col, a); c.fill()

def ell(cc, x, y, rx, ry, rot=0.0):
    cc.save(); cc.translate(x, y); cc.rotate(rot); cc.scale(rx, ry); cc.arc(0, 0, 1, 0, math.tau); cc.restore()

def mirror(pts):
    return [(-x, y) for (x, y) in pts]

# ------------------------------------------------------------------ head (front, head-local coords: face centre 0,0)
def head_front(c, P, B, L, pal, lw):
    """P: mouth 0/1/2, eyes 'open'|'blink'|'wide', look (-1..1), brow (-1 worried .. 1 happy), turn (-1..1 small 3/4 shift)"""
    tn = P.get('turn', 0.0) * 6
    # back hair
    back = [(-70, -5), (-72, -48), (-56, -86), (-24, -104), (0, -107), (24, -104), (56, -86), (72, -48), (70, -5), (73, 40), (58, 56), (0, 52), (-58, 56), (-73, 40)]
    cel(c, lambda cc: smooth_path(cc, B.jp(back, 0.4)), pal['hair'], pal['hair_s'], L, off=8, lw=lw)
    # face
    face = [(-56, -10), (-55, 28), (-38, 54), (0 + tn, 64), (38, 54), (55, 28), (56, -10), (48, -50), (0, -60), (-48, -50)]
    cel(c, lambda cc: smooth_path(cc, B.jp(face, 0.3)), pal['skin'], pal['skin_s'], L, off=5, lw=lw * 0.9)
    # blush
    for sx in (-1, 1):
        ell(c, sx * 33 + tn, 22, 10, 4.5); fill(c, pal['blush'], 0.45)
    # eyes
    ey = -2; open_ = P.get('eyes', 'open')
    for sx in (-1, 1):
        ex = sx * 22 + tn
        if open_ == 'blink':
            inkline(c, B.jp(qcurve((ex - 11, ey + 2), (ex, ey + 7), (ex + 11, ey + 2), 8), 0.2), lw * 1.3, pal['eye'], 1.0)
            continue
        ry = 13 if open_ == 'open' else 15
        ell(c, ex, ey + 1, 9.5, ry); fill(c, pal['eye'])
        lk, ld = P.get('look', 0) * 3.0, P.get('down', 0) * 3.0     # pupils shift inside the eye
        c.save(); ell(c, ex, ey + 1, 9.5, ry); c.clip()
        ell(c, ex + lk, ey + 1 + ld, 8.6, ry * 0.92); fill(c, pal['eye'])
        ell(c, ex + lk, ey + 6 + ld, 7, ry * 0.5); fill(c, pal['iris'])
        ell(c, ex + lk - 3, ey - 5 + ld, 3.6, 4.2); fill(c, pal['white'])
        ell(c, ex + lk + 3.5, ey + 7 + ld, 1.6, 1.6); fill(c, pal['white'], 0.9)
        c.restore()
        inkline(c, B.jp(qcurve((ex - 12, ey - 8), (ex, ey - 15 - (2 if open_ == 'wide' else 0)), (ex + 12, ey - 8), 8), 0.2),
                lw * 1.5, pal['eye'], 1.0)
    # brows
    bw = P.get('brow', 0.0)
    for sx in (-1, 1):
        bx = sx * 22 + tn
        inkline(c, B.jp([(bx - 9 * sx * -1 - 0, -28 + bw * 2 * sx * 0 - (bw * 3 if sx < 0 else bw * 3)),
                         (bx + 9 * sx * -1 * -1, -30 - bw * 1)], 0.2), lw * 0.9, pal['hair'], 0.9)
    # nose
    inkline(c, [(0 + tn * 1.2, 14), (1.5 + tn * 1.2, 18)], lw * 0.7, pal['skin_s'], 1.0)
    # mouth
    m = P.get('mouth', 0); mx, my = tn * 1.1, 36
    if m == 0:
        inkline(c, B.jp(qcurve((mx - 8, my), (mx, my + 2.5 + P.get('smile', 0) * 2), (mx + 8, my), 6), 0.2), lw * 0.9, pal['mouth'], 1.0)
    else:
        ry = 4.0 if m == 1 else 8.0; rx = 6.5 if m == 1 else 8.0
        def mo(cc):
            smooth_path(cc, [(mx - rx, my), (mx - rx * 0.6, my - ry * 0.55), (mx + rx * 0.6, my - ry * 0.55), (mx + rx, my),
                             (mx + rx * 0.5, my + ry), (mx - rx * 0.5, my + ry)])
        c.save(); mo(c); fill(c, pal['mouth']); c.restore()
        c.save(); mo(c); c.clip(); ell(c, mx, my + ry * 0.9, rx * 0.7, ry * 0.55); fill(c, pal['tongue']); c.restore()
        c.save(); mo(c); c.set_source_rgb(*pal['eye']); c.set_line_width(lw * 0.6); c.stroke(); c.restore()
    # bangs (straight cut with small teeth) + side locks
    bang = [(-60, -18), (-62, -54), (-44, -88), (-18, -102), (0, -104), (18, -102), (44, -88), (62, -54), (60, -18), (48, -12), (37, -18), (24, -10),
            (10, -17), (-4, -9), (-18, -16), (-32, -9), (-47, -15)]
    cel(c, lambda cc: smooth_path(cc, B.jp(bang, 0.3)), pal['hair'], pal['hair_s'], L, off=6, lw=lw)
    inkline(c, B.jp(qcurve((-36, -78), (0, -92), (32, -80), 8), 0.3), lw * 2.2, pal['hair_h'], 0.85)   # shine band
    for sx in (-1, 1):
        lock = [(sx * 57, -24), (sx * 61, 18), (sx * 54, 50), (sx * 45, 44), (sx * 47, 6)]
        cel(c, lambda cc, lock=lock: smooth_path(cc, B.jp(lock, 0.3)), pal['hair'], pal['hair_s'], L, off=4, lw=lw)

# ------------------------------------------------------------------ full body, front (feet at origin, 1 unit = 1 px at s=1)
def sol_front(c, x, y, s, P=None, t=0.0, L=L0, pal=None, lw=2.6):
    P = P or {}; pal = pal or PAL
    B = Boil(t, salt=31)
    c.save(); c.translate(x, y); c.scale(s, s)
    lwu = lw / s
    # legs + shoes
    for sx in (-1, 1):
        leg = [(sx * 10, -170), (sx * 32, -170), (sx * 30, -30), (sx * 12, -30)]
        cel(c, lambda cc, p=leg: smooth_path(cc, B.jp(p, 0.3)), pal['skin'], pal['skin_s'], L, off=4, lw=lwu * 0.9)
        shoe = [(sx * 6, -30), (sx * 34, -34), (sx * 46, -16), (sx * 42, 0), (sx * 6, 2), (sx * 2, -14)]
        cel(c, lambda cc, p=shoe: smooth_path(cc, B.jp(p, 0.3)), pal['shoe'], pal['shoe_s'], L, off=4, lw=lwu)
    # hood bunched behind the neck
    hood = [(-58, -368), (-40, -392), (0, -398), (40, -392), (58, -368), (30, -356), (-30, -356)]
    cel(c, lambda cc: smooth_path(cc, B.jp(hood, 0.4)), pal['coat_s'], pal['coat_s'], L, off=0, lw=lwu)
    # sleeves (behind coat body edges) + hands
    arm = P.get('arm', 0.0)
    for sx in (-1, 1):
        sl = [(sx * 40, -372), (sx * 58, -360), (sx * (74 + 6 * arm), -262), (sx * (56 + 6 * arm), -252), (sx * 40, -320)]
        cel(c, lambda cc, p=sl: smooth_path(cc, B.jp(p, 0.4)), pal['coat'], pal['coat_s'], L, off=7, lw=lwu)
        ell(c, sx * (66 + 6 * arm), -244, 10, 11)
        cel(c, lambda cc, hx=sx * (66 + 6 * arm): ell(cc, hx, -244, 10, 11), pal['skin'], pal['skin_s'], L, off=3, lw=lwu * 0.9)
    # coat body (A-line)
    body = [(-44, -372), (-30, -380), (0, -382), (30, -380), (44, -372), (62, -290), (84, -166), (42, -156), (0, -152),
            (-42, -156), (-84, -166), (-62, -290)]
    cel(c, lambda cc: smooth_path(cc, B.jp(body, 0.4)), pal['coat'], pal['coat_s'], L, off=12, lw=lwu)
    inkline(c, B.jp([(4, -376), (6, -270), (8, -156)], 0.3), lwu * 0.9, pal['coat_s'], 0.9)            # front opening
    for k, yy in enumerate((-350, -312, -274)):                                                       # toggles
        c.save(); c.translate(14, yy); c.rotate(0.2); c.rectangle(-7, -3, 14, 6); c.restore(); fill(c, pal['toggle'])
    # 물허벅 strap across the chest
    inkline(c, B.jp([(38, -372), (0, -320), (-52, -262)], 0.3), lwu * 4.2, pal['strap'], 1.0, taper=False)
    # neck + head
    neck = [(-11, -386), (11, -386), (10, -370), (-10, -370)]
    cel(c, lambda cc: smooth_path(cc, neck), pal['skin_s'], pal['skin_s'], L, off=0, lw=0)
    c.save(); c.translate(0, -446); c.rotate(math.radians(P.get('tilt', 0)))
    head_front(c, P, B, L, pal, lwu)
    c.restore()
    c.restore()

def sol_side(c, x, y, s, P=None, t=0.0, L=L0, pal=None, lw=2.6):
    """profile facing right, 물허벅 on the back"""
    P = P or {}; pal = pal or PAL
    B = Boil(t, salt=37)
    c.save(); c.translate(x, y); c.scale(s, s); lwu = lw / s
    # jar on the back
    jar = [(-62, -360), (-50, -372), (-36, -366), (-30, -340), (-34, -300), (-48, -286), (-70, -292), (-78, -324)]
    cel(c, lambda cc: smooth_path(cc, B.jp(jar, 0.3)), pal['jar'], pal['jar_s'], L, off=6, lw=lwu)
    inkline(c, B.jp([(-60, -332), (-46, -328)], 0.2), lwu * 0.8, pal['jar_s'], 0.9)                   # the crack
    # legs/shoes
    for dx, sh in ((-6, 0.8), (8, 1.0)):
        leg = [(dx - 10, -170), (dx + 10, -170), (dx + 9, -30), (dx - 9, -30)]
        cel(c, lambda cc, p=leg: smooth_path(cc, B.jp(p, 0.3)), tuple(v * sh + (1 - sh) * 0.7 for v in pal['skin']), pal['skin_s'], L, off=3, lw=lwu * 0.9)
        shoe = [(dx - 14, -30), (dx + 14, -32), (dx + 32, -10), (dx + 28, 2), (dx - 14, 2)]
        cel(c, lambda cc, p=shoe: smooth_path(cc, B.jp(p, 0.3)), pal['shoe'], pal['shoe_s'], L, off=3, lw=lwu)
    body = [(-28, -376), (16, -380), (30, -360), (42, -270), (60, -166), (0, -154), (-54, -162), (-42, -290)]
    cel(c, lambda cc: smooth_path(cc, B.jp(body, 0.4)), pal['coat'], pal['coat_s'], L, off=10, lw=lwu)
    hood = [(-40, -372), (-30, -396), (-6, -398), (4, -378), (-20, -364)]
    cel(c, lambda cc: smooth_path(cc, B.jp(hood, 0.4)), pal['coat_s'], pal['coat_s'], L, off=0, lw=lwu)
    sl = [(-4, -370), (16, -366), (30, -270), (12, -262), (-6, -320)]
    cel(c, lambda cc: smooth_path(cc, B.jp(sl, 0.4)), pal['coat'], pal['coat_s'], L, off=6, lw=lwu)
    cel(c, lambda cc: ell(cc, 22, -254, 10, 11), pal['skin'], pal['skin_s'], L, off=3, lw=lwu * 0.9)
    inkline(c, B.jp([(-26, -366), (-44, -312)], 0.3), lwu * 4, pal['strap'], 1.0, taper=False)
    # head profile
    c.save(); c.translate(0, -446)
    back = [(-62, -50), (-40, -88), (10, -94), (46, -66), (50, -30), (40, 30), (20, 52), (-40, 54), (-68, 30), (-72, -10)]
    cel(c, lambda cc: smooth_path(cc, B.jp(back, 0.4)), pal['hair'], pal['hair_s'], L, off=8, lw=lwu)
    face = [(-6, -40), (40, -50), (54, -20), (57, 6), (62, 13), (57, 20), (55, 36), (46, 52), (24, 64), (2, 58), (-10, 20)]
    cel(c, lambda cc: smooth_path(cc, B.jp(face, 0.3)), pal['skin'], pal['skin_s'], L, off=4, lw=lwu * 0.9)
    ell(c, 30, 24, 9, 4.5); fill(c, pal['blush'], 0.45)
    ell(c, 38, -2, 6, 12); fill(c, pal['eye']); ell(c, 36, -7, 2.6, 3.4); fill(c, pal['white'])
    inkline(c, B.jp(qcurve((30, -12), (40, -17), (46, -10), 6), 0.2), lwu * 1.4, pal['eye'], 1.0)
    inkline(c, B.jp([(48, 38), (56, 37)], 0.2), lwu * 0.9, pal['mouth'], 1.0)
    bang = [(-20, -60), (8, -92), (46, -70), (54, -30), (46, -16), (40, -24), (30, -14), (18, -22), (0, -30)]
    cel(c, lambda cc: smooth_path(cc, B.jp(bang, 0.3)), pal['hair'], pal['hair_s'], L, off=5, lw=lwu)
    lock = [(-6, -30), (10, 10), (6, 50), (-10, 46), (-14, 0)]
    cel(c, lambda cc: smooth_path(cc, B.jp(lock, 0.3)), pal['hair'], pal['hair_s'], L, off=4, lw=lwu)
    inkline(c, B.jp(qcurve((-30, -72), (6, -84), (34, -66), 8), 0.3), lwu * 2.2, pal['hair_h'], 0.85)
    c.restore()
    c.restore()

# ------------------------------------------------------------------ 꾸럭이
KU = {'grey': ((0.66, 0.64, 0.66), (0.50, 0.48, 0.52)), 'orange': ((0.98, 0.56, 0.24), (0.86, 0.38, 0.16)),
      'white': ((0.98, 0.96, 0.94), (0.82, 0.82, 0.86)), 'pink': ((0.98, 0.62, 0.66), (0.86, 0.44, 0.50))}

def kuruk(c, x, y, s, state='orange', t=0.0, L=L0, curl=1.0, lw=2.2, blink=False):
    base, sh = KU[state]
    B = Boil(t, salt=41)
    c.save(); c.translate(x, y); c.scale(s, s); lwu = lw / s
    for k in range(8):                                      # arms: eight separate curls, tips rolled outward
        side = -1 if k < 4 else 1
        kk = k if k < 4 else 7 - k                          # 0 outer .. 3 inner
        x0 = side * (4 + kk * 4.0); y0 = 10
        ang0 = math.pi / 2 + side * (0.25 + 0.32 * (3 - kk))
        pts = []; x_, y_ = x0, y0; ang = ang0
        for j in range(9):
            pts.append((x_, y_))
            step = 4.6 - 0.25 * j
            ang += side * -curl * 0.05 * j * (0.6 + 0.15 * kk)
            x_ += step * math.cos(ang); y_ += step * math.sin(ang)
        inkline(c, B.jp(pts, 0.3), lwu * 7.0, sh, 1.0)
        inkline(c, B.jp(pts, 0.3), lwu * 4.6, base, 1.0)
        for j in (3, 5, 7):                                 # suckers
            px, py = pts[j]
            ell(c, px + side * 1.2, py + 1.2, 1.1, 1.1); fill(c, sh, 0.9)
    mantle = [(-17, 8), (-22, -10), (-18, -30), (0, -40), (18, -30), (22, -10), (17, 8), (0, 12)]
    cel(c, lambda cc: smooth_path(cc, B.jp(mantle, 0.3)), base, sh, L, off=5, lw=lwu)
    for sx in (-1, 1):
        if blink:
            inkline(c, [(sx * 9 - 4, 3), (sx * 9 + 4, 3)], lwu * 1.2, (0.15, 0.12, 0.16), 1.0)
        else:
            ell(c, sx * 9, 2, 3.6, 4.6); fill(c, (0.15, 0.12, 0.16)); ell(c, sx * 9 - 1, 0.2, 1.3, 1.6); fill(c, (1, 1, 1))
    c.restore()
