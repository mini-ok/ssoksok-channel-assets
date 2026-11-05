# -*- coding: utf-8 -*-
"""Poster-colour repaint: re-paints an underpainting with curved brush strokes that follow the form.
Coarse-to-fine layers (Hertzmann-style), direction field from the structure tensor + per-region hints,
strokes stop at colour edges, each stroke a flat opaque gouache mark with bristle streaks and dry tail."""
import math
import numpy as np
import cv2
import cairo

F32 = np.float32

def direction_field(ref, hint_angle=None, sigma=3.0, rho=14.0, coh_w=None):
    """returns (angle, coherence). angle = stroke direction (along edges)."""
    lum = cv2.GaussianBlur((ref * np.array((0.3, 0.59, 0.11), F32)).sum(-1), (0, 0), sigma)
    gx = cv2.Sobel(lum, cv2.CV_32F, 1, 0, ksize=3)
    gy = cv2.Sobel(lum, cv2.CV_32F, 0, 1, ksize=3)
    jxx = cv2.GaussianBlur(gx * gx, (0, 0), rho)
    jxy = cv2.GaussianBlur(gx * gy, (0, 0), rho)
    jyy = cv2.GaussianBlur(gy * gy, (0, 0), rho)
    tr = jxx + jyy + 1e-9
    disc = np.sqrt((jxx - jyy) ** 2 + 4 * jxy ** 2)
    coh = (disc / tr) ** 2
    ang = 0.5 * np.arctan2(2 * jxy, jxx - jyy) + np.pi / 2       # perpendicular to gradient
    if hint_angle is not None:
        # blend as doubled-angle vectors so 0 and pi are the same direction
        w = np.clip(coh * 3.0, 0, 1) * (1.0 if coh_w is None else coh_w)
        vx = w * np.cos(2 * ang) + (1 - w) * np.cos(2 * hint_angle)
        vy = w * np.sin(2 * ang) + (1 - w) * np.sin(2 * hint_angle)
        ang = 0.5 * np.arctan2(vy, vx)
    return ang.astype(F32), coh.astype(F32)

def _draw_stroke(c, pts, col, wd, rng, bristle=True, balpha=0.55):
    if len(pts) < 2:
        return
    c.set_line_cap(cairo.LINE_CAP_ROUND)
    c.set_line_join(cairo.LINE_JOIN_ROUND)
    c.move_to(*pts[0])
    for p in pts[1:]:
        c.line_to(*p)
    c.set_source_rgb(*col)
    c.set_line_width(wd)
    c.stroke()
    if not bristle or wd < 3:
        return
    # bristle streaks: thin lighter/darker lines inside the stroke, offset along the normal
    P = np.array(pts)
    d = np.gradient(P, axis=0)
    n = np.stack([-d[:, 1], d[:, 0]], -1)
    n /= (np.linalg.norm(n, axis=1, keepdims=True) + 1e-9)
    for _ in range(2 if wd < 8 else 3):
        off = rng.uniform(-0.38, 0.38) * wd
        k = rng.uniform(-0.07, 0.07)
        cc = tuple(min(1, max(0, v * (1 + k))) for v in col)
        start = rng.integers(0, max(1, len(P) // 3))
        Q = P[start:] + n[start:] * off
        if len(Q) < 2:
            continue
        c.move_to(*Q[0])
        for q in Q[1:]:
            c.line_to(*q)
        c.set_source_rgba(cc[0], cc[1], cc[2], balpha)
        c.set_line_width(max(1.0, wd * rng.uniform(0.10, 0.22)))
        c.stroke()

def paint(src, mask=None, hint=None, radii=(26, 13, 6, 3), thresh=(0.0, 0.06, 0.09, 0.13), maxlen=(8, 7, 5, 3),
          seed=1, jitter=0.025, lenmul=None, detail=0.7, detail_sigma=2.2, balpha_map=None, coh_w=None):
    """src: float RGB (H,W,3) underpainting. mask: optional (H,W) region to paint (1) - strokes are clipped to it.
    hint: optional (H,W) preferred angle field. lenmul: optional (H,W) multiplier for stroke length."""
    h, w = src.shape[:2]
    rng = np.random.default_rng(seed)
    surf = cairo.ImageSurface(cairo.FORMAT_RGB24, w, h)
    c = cairo.Context(surf)
    base = cv2.GaussianBlur(src, (0, 0), radii[0])
    # start from a flat wash of the coarsest blur
    img8 = np.clip(base * 255, 0, 255).astype(np.uint8)
    buf = np.ndarray((h, w, 4), np.uint8, surf.get_data())
    buf[..., 0] = img8[..., 2]; buf[..., 1] = img8[..., 1]; buf[..., 2] = img8[..., 0]
    surf.mark_dirty()
    ang, coh = direction_field(src, hint, coh_w=coh_w)
    for li, R in enumerate(radii):
        ref = cv2.GaussianBlur(src, (0, 0), max(0.6, R * 0.45))
        surf.flush()
        cur = np.ndarray((h, w, 4), np.uint8, surf.get_data())[..., [2, 1, 0]].astype(F32) / 255
        err = np.abs(cur - ref).sum(-1)
        err = cv2.blur(err, (int(R) * 2 + 1, int(R) * 2 + 1))
        step = max(2, int(R * 0.9))
        ys, xs = np.mgrid[step // 2:h:step, step // 2:w:step]
        ys = ys + rng.integers(-step // 2, step // 2 + 1, ys.shape)
        xs = xs + rng.integers(-step // 2, step // 2 + 1, xs.shape)
        ys = np.clip(ys, 0, h - 1); xs = np.clip(xs, 0, w - 1)
        sel = err[ys, xs] > thresh[li]
        if mask is not None:
            sel &= mask[ys, xs] > 0.5
        pts0 = np.stack([xs[sel], ys[sel]], -1)
        rng.shuffle(pts0)
        for (x0, y0) in pts0:
            col = ref[y0, x0]
            v = 1 + rng.normal(0, jitter)
            col = np.clip(col * v + rng.normal(0, jitter * 0.25, 3), 0, 1)
            L = maxlen[li] * (lenmul[y0, x0] if lenmul is not None else 1.0)
            pts = [(float(x0), float(y0))]
            for direction in (1, -1):
                x, y = float(x0), float(y0)
                prev = None
                n = int(L * (0.5 + rng.random()) / 2) + 1
                for _ in range(n):
                    a = ang[int(y), int(x)]
                    dx, dy = math.cos(a), math.sin(a)
                    if prev is not None and dx * prev[0] + dy * prev[1] < 0:
                        dx, dy = -dx, -dy
                    if prev is None and direction < 0:
                        dx, dy = -dx, -dy
                    prev = (dx, dy)
                    x += dx * R * 0.9; y += dy * R * 0.9
                    if not (0 <= x < w - 1 and 0 <= y < h - 1):
                        break
                    if mask is not None and mask[int(y), int(x)] < 0.5:
                        break
                    if np.abs(ref[int(y), int(x)] - col).sum() > 0.16:
                        break
                    if direction > 0:
                        pts.append((x, y))
                    else:
                        pts.insert(0, (x, y))
            wd = R * 2 * (0.85 + 0.3 * rng.random())
            ba = 0.45 if balpha_map is None else float(balpha_map[y0, x0])
            _draw_stroke(c, pts, tuple(float(v) for v in col), wd, rng, balpha=ba)
    surf.flush()
    out = np.ndarray((h, w, 4), np.uint8, surf.get_data())[..., [2, 1, 0]].astype(F32) / 255
    if detail > 0:
        # drawn detail over the washes: put back the underpainting's fine line work
        hi = src - cv2.GaussianBlur(src, (0, 0), detail_sigma)
        out = np.clip(out + hi * F32(detail), 0, 1)
    return out
