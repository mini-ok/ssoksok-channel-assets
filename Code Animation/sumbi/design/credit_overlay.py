# -*- coding: utf-8 -*-
"""허상공방 ending credit as a transparent overlay (no plate, no sound) for compositing over a film's last shot.
Same typing + 白文 seal as credit_anim.py (D2Coding). side='right' | 'left'."""
import os, numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont
_D = os.path.dirname(os.path.abspath(__file__))

LINES = ['Created & Coded by L.S.M.', '허상공방 虛像工房 Project']
SIZE = 29
FONT = ImageFont.truetype(os.path.join(_D, 'fonts/d2coding-full.ttf'), SIZE)
CELL = FONT.getlength('M')
GAP, MARGIN, SGAP = 50, 110, 30
COL = (246, 240, 226)

def _wide(ch):
    return ord(ch) > 0x2E7F

def _xs(line):
    xs, x = [], 0.0
    for ch in line:
        xs.append(x); x += (FONT.getlength(ch) + 1) if _wide(ch) else CELL
    return xs, x

_rng = np.random.default_rng(4)
TIMES = []
_t = 0.45
for line in LINES:
    row = []
    for ch in line:
        row.append(_t); _t += (0.055 if ch != ' ' else 0.09) + _rng.uniform(0, 0.05)
    TIMES.append(row); _t += 0.38
TYPE_END = _t - 0.38
LSM_END = TIMES[0][-1]
MAXW = max(_xs(l)[1] for l in LINES)
_BLOCK_H = GAP + SIZE + 14
_SEAL = None

def _seal():
    global _SEAL
    if _SEAL is None:
        s = np.load(os.path.join(_D, 'seal_baimun3.npy'))
        k = _BLOCK_H / s.shape[0]
        _SEAL = cv2.resize(s, (int(s.shape[1] * k), int(s.shape[0] * k)), interpolation=cv2.INTER_AREA)
    return _SEAL

def layout(W, H, side, bottom=205):
    s = _seal()
    y1 = H - bottom
    if side == 'right':
        sx = int(W - MARGIN - s.shape[1]); x0 = sx - SGAP - MAXW
    else:
        x0 = MARGIN; sx = int(x0 + MAXW + SGAP)
    return x0, y1, sx, int(y1 - 8)

def apply(img, tt, side='right', bottom=205, alpha=1.0):
    """img: float32 HxWx3 in 0..1 (picture area). tt: seconds since the credit started. Returns new image."""
    if tt <= 0 or alpha <= 0.003:
        return img
    H, W = img.shape[:2]
    x0, y1, sx, sy = layout(W, H, side, bottom)
    im = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    cur = None
    for li, line in enumerate(LINES):
        xs, lw = _xs(line); y = y1 + li * GAP; shown = 0
        for i, ch in enumerate(line):
            if tt >= TIMES[li][i]:
                dy = -4 if _wide(ch) else 0
                d.text((x0 + xs[i] + 2, y + 2 + dy), ch, font=FONT, fill=(4, 12, 20, 150))
                d.text((x0 + xs[i], y + dy), ch, font=FONT, fill=COL + (255,))
                shown = i + 1
        if shown > 0 or li == 0:
            if shown < len(line) or li == len(LINES) - 1 or tt < TIMES[li + 1][0]:
                if li == 0 or shown > 0 or tt >= TIMES[li][0] - 0.38:
                    cur = (x0 + (xs[shown] if shown < len(line) else lw), y)
    if cur is not None:
        if tt < TYPE_END + 0.1 or int((tt - TYPE_END) * 2) % 2 == 0:
            d.rectangle((cur[0] + 2, cur[1] + 4, cur[0] + CELL - 1, cur[1] + SIZE + 6), fill=COL + (215,))
    lay = np.asarray(im, np.float32) / 255
    a = lay[..., 3:4] * alpha
    out = img.astype(np.float32).copy()
    # soft dark bed so the type reads over bright skies, then a faint phosphor glow
    bed = cv2.GaussianBlur(lay[..., 3], (0, 0), 14)[..., None] * 0.35 * alpha
    out = out * (1 - bed)
    glow = cv2.GaussianBlur(lay[..., 3], (0, 0), 6)[..., None] * alpha
    out = out + glow * np.array((0.10, 0.10, 0.08), np.float32)
    out = out * (1 - a) + lay[..., :3] * a
    t0s = TIMES[0][0] + 0.4
    al = min(1.0, max(0.0, (tt - t0s) / (LSM_END - t0s))); al = al * al * (3 - 2 * al) * alpha
    if al > 0:
        s = _seal(); h, w = s.shape[:2]
        m = s[..., 3:4] * al
        sub = out[sy:sy + h, sx:sx + w]
        out[sy:sy + h, sx:sx + w] = sub * (1 - m[:sub.shape[0], :sub.shape[1]]) + s[:sub.shape[0], :sub.shape[1], :3] * m[:sub.shape[0], :sub.shape[1]]
    return np.clip(out, 0, 1)
