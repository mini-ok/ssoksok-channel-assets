# -*- coding: utf-8 -*-
"""〈숨비〉 title card + 허상공방 / L.S.M. seal mockups (1920x1080, 1.85 letterbox)."""
import json, math, numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont

W, OH, H, BAR = 1920, 1080, 1040, 20
CM = json.load(open('fonts/charmap.json'))
SERIF = '/usr/share/fonts/opentype/noto/NotoSerifCJK-Bold.ttc'
SERIF_R = '/usr/share/fonts/opentype/noto/NotoSerifCJK-Regular.ttc'
CORM_I = 'fonts/cormorant-latin-500-italic.ttf'
CORM = 'fonts/cormorant-latin-600-normal.ttf'
rng = np.random.default_rng(11)

def text_mask(txt, size, fam=None, path=None, idx=1, spacing=0, vertical=False, wh=None):
    """float mask of text; fam: fontsource family (per-char slices), else path (ttc index idx: 1=KR)"""
    fonts = []
    for ch in txt:
        if fam and ch in CM[fam]:
            fonts.append(ImageFont.truetype(CM[fam][ch], size))
        else:
            fonts.append(ImageFont.truetype(path or SERIF, size, index=idx if (path or SERIF).endswith('ttc') else 0))
    adv = [f.getbbox(ch) for ch, f in zip(txt, fonts)]
    if vertical:
        w = int(size * 1.4); h = int(len(txt) * (size + spacing) + size * 0.5)
    else:
        w = int(sum(f.getlength(ch) for ch, f in zip(txt, fonts)) + spacing * len(txt) + size); h = int(size * 1.6)
    im = Image.new('L', (w, h), 0); d = ImageDraw.Draw(im)
    x, y = size * 0.25, size * 0.15
    for ch, f in zip(txt, fonts):
        if vertical:
            d.text((size * 0.2, y), ch, font=f, fill=255); y += size + spacing
        else:
            d.text((x, y), ch, font=f, fill=255); x += f.getlength(ch) + spacing
    a = np.array(im, np.float32) / 255
    ys, xs = np.nonzero(a > 0.02)
    return a[ys.min():ys.max() + 1, xs.min():xs.max() + 1]

def fbm(h, w, scale, seed, oct=4):
    r = np.random.default_rng(seed); out = np.zeros((h, w), np.float32); amp = 1
    for o in range(oct):
        s = max(2, int(scale / 2 ** o))
        n = r.random(((h // s) + 2, (w // s) + 2)).astype(np.float32)
        out += amp * cv2.resize(n, (w, h), interpolation=cv2.INTER_CUBIC); amp *= 0.5
    return out / 1.9

def dry_brush(m, seed=1, amt=0.45, streak=True):
    h, w = m.shape
    n = fbm(h, w, 18, seed)
    if streak:
        st = cv2.blur(np.random.default_rng(seed).random((h, w)).astype(np.float32), (41, 3))
        n = n * 0.6 + st * 0.8
    mb = cv2.GaussianBlur(m, (0, 0), 1.0)
    return np.clip((mb + (n - 0.55) * amt - 0.5) * 5 + 0.5, 0, 1) * (mb > 0.02)

def put(canvas, mask, x, y, col, alpha=1.0):
    """composite colour through mask at top-left x,y (canvas float RGB)"""
    h, w = mask.shape
    x0, y0 = max(0, x), max(0, y); x1, y1 = min(canvas.shape[1], x + w), min(canvas.shape[0], y + h)
    if x1 <= x0 or y1 <= y0:
        return
    m = mask[y0 - y:y1 - y, x0 - x:x1 - x, None] * alpha
    canvas[y0:y1, x0:x1] = canvas[y0:y1, x0:x1] * (1 - m) + np.array(col, np.float32) * m

def put_rgba(canvas, rgba, x, y):
    put_mask = rgba[..., 3]
    h, w = put_mask.shape
    x0, y0 = max(0, x), max(0, y); x1, y1 = min(canvas.shape[1], x + w), min(canvas.shape[0], y + h)
    m = put_mask[y0 - y:y1 - y, x0 - x:x1 - x, None]
    canvas[y0:y1, x0:x1] = canvas[y0:y1, x0:x1] * (1 - m) + rgba[y0 - y:y1 - y, x0 - x:x1 - x, :3] * m

def finish(canvas, name):
    out = np.zeros((OH, W, 3), np.float32)
    g = np.random.default_rng(5).normal(0, 0.012, canvas.shape[:2]).astype(np.float32)[..., None]
    out[BAR:BAR + H] = np.clip(canvas + g, 0, 1)
    Image.fromarray((out * 255).astype(np.uint8)).save(name)

def load(p):
    return np.array(Image.open(p).convert('RGB'), np.float32) / 255

# ------------------------------------------------------------------ seals
RED = (0.78, 0.14, 0.10)

def stamp_texture(alpha, seed):
    """uneven ink: speckles where ink missed, darker pooling, soft edge bleed"""
    h, w = alpha.shape
    n = fbm(h, w, 40, seed)
    speck = np.random.default_rng(seed).random((h, w)).astype(np.float32)
    speck = cv2.GaussianBlur(speck, (0, 0), 1.2)
    miss = (speck > 0.62) * (n > 0.55)
    a = cv2.GaussianBlur(alpha, (0, 0), 0.8)
    a = a * (1 - miss * 0.9) * (0.82 + 0.18 * n)
    return np.clip(a, 0, 1)

def rough_rect(h, w, r, seed, inset=0):
    m = np.zeros((h, w), np.float32)
    cv2.rectangle(m, (inset, inset), (w - 1 - inset, h - 1 - inset), 1.0, -1, lineType=cv2.LINE_AA)
    n = fbm(h, w, 30, seed) - 0.5
    mb = cv2.GaussianBlur(m, (0, 0), r)
    return np.clip((mb - 0.5 + n * 0.35) * 8 + 0.5, 0, 1)

def seal_baimun(chars='虛像工房', size=520, seed=3):
    """白文: characters carved out of a red block. Reading order: right column top->bottom, then left."""
    block = rough_rect(size, size, 6, seed, inset=8)
    cut = np.zeros((size, size), np.float32)
    cell = (size - 70) // 2
    order = [(1, 0), (1, 1), (0, 0), (0, 1)]                 # (col, row): 虛 top-right, 像 bottom-right, 工 top-left, 房 bottom-left
    for ch, (cx, cy) in zip(chars, order):
        m = text_mask(ch, int(cell * 1.05), path=SERIF, idx=1)
        m = cv2.resize(m, (cell - 6, cell - 6))
        x = 30 + cx * (cell + 10) + 3; y = 30 + cy * (cell + 10) + 3
        cut[y:y + m.shape[0], x:x + m.shape[1]] = np.maximum(cut[y:y + m.shape[0], x:x + m.shape[1]], m)
    cut = dry_brush(cut, seed, amt=0.25, streak=False)
    a = stamp_texture(block * (1 - cut), seed)
    rgba = np.zeros((size, size, 4), np.float32); rgba[..., :3] = RED; rgba[..., 3] = a
    return rgba

def seal_zhuwen(chars='虛像工房', size=520, seed=4):
    """朱文: red characters with a red border on white paper."""
    border = rough_rect(size, size, 4, seed) - rough_rect(size, size, 4, seed + 1, inset=26)
    ink = np.clip(border, 0, 1)
    cell = (size - 90) // 2
    order = [(1, 0), (1, 1), (0, 0), (0, 1)]
    for ch, (cx, cy) in zip(chars, order):
        m = text_mask(ch, int(cell * 1.05), path=SERIF, idx=1)
        m = cv2.resize(m, (cell - 4, cell - 4))
        x = 42 + cx * (cell + 6); y = 42 + cy * (cell + 6)
        ink[y:y + m.shape[0], x:x + m.shape[1]] = np.maximum(ink[y:y + m.shape[0], x:x + m.shape[1]], m)
    a = stamp_texture(ink, seed)
    rgba = np.zeros((size, size, 4), np.float32); rgba[..., :3] = RED; rgba[..., 3] = a
    return rgba

PIX = {  # 5x7 pixel letters
    'L': ["10000", "10000", "10000", "10000", "10000", "10000", "11111"],
    'S': ["01111", "10000", "10000", "01110", "00001", "00001", "11110"],
    'M': ["10001", "11011", "10101", "10101", "10001", "10001", "10001"],
    '.': ["00000", "00000", "00000", "00000", "00000", "00000", "00100"],
}

def seal_pixel(word='LSM', size=520, seed=5, dots=True):
    """digital 인장: pixel letters carved (白文) out of a red block, a 1px-grid feel"""
    block = rough_rect(size, size, 5, seed, inset=8)
    cut = np.zeros((size, size), np.float32)
    letters = list(word)
    if dots:
        seq = []
        for i, ch in enumerate(letters):
            seq.append(ch)
            seq.append('.')
        letters = seq
    cols = sum(3 if ch == '.' else 5 for ch in letters) + (len(letters) - 1)
    px = int((size - 90) / cols)
    tot = px * cols
    x = (size - tot) // 2; y0 = (size - px * 7) // 2
    r2 = np.random.default_rng(seed)
    for ch in letters:
        g = PIX[ch]
        wcol = 3 if ch == '.' else 5
        for j, row in enumerate(g):
            for i in range(wcol):
                bit = row[i + (1 if ch == '.' else 0)] if ch == '.' else row[i]
                if bit == '1':
                    jx, jy = r2.uniform(-1.5, 1.5, 2)
                    cv2.rectangle(cut, (int(x + i * px + 3 + jx), int(y0 + j * px + 3 + jy)),
                                  (int(x + (i + 1) * px - 3 + jx), int(y0 + (j + 1) * px - 3 + jy)), 1.0, -1)
        x += (wcol + 1) * px
    # a thin carved frame line inside the block
    fr = np.zeros_like(cut); cv2.rectangle(fr, (28, 28), (size - 29, size - 29), 1.0, 5)
    cut = np.maximum(cut, fr)
    a = stamp_texture(block * (1 - cut), seed)
    rgba = np.zeros((size, size, 4), np.float32); rgba[..., :3] = RED; rgba[..., 3] = a
    return rgba

def pix_glyph(ch, n=9):
    m = text_mask(ch, 200, path=SERIF, idx=1)
    m = cv2.resize(m, (n, n), interpolation=cv2.INTER_AREA)
    return (m > 0.33).astype(np.uint8)

def seal_pixel2(size=520, seed=7, n=14):
    """digital 인장: L S / M 印 on one 14x14 pixel grid per cell (letters = 5x7 at 2x), carved from a red block"""
    block = rough_rect(size, size, 5, seed, inset=8)
    cut = np.zeros((size, size), np.float32)
    cells = {}
    for ch in 'LSM':
        g = np.zeros((n, n), np.uint8)
        P = PIX[ch]
        for j in range(7):
            for i in range(5):
                if P[j][i] == '1':
                    g[j * 2:j * 2 + 2, 2 + i * 2:2 + i * 2 + 2] = 1
        cells[ch] = g
    cells['印'] = pix_glyph('印', n)
    order = [('L', 0, 0), ('S', 1, 0), ('M', 0, 1), ('印', 1, 1)]
    cell = (size - 70) // 2
    px = cell // (n + 1)
    r2 = np.random.default_rng(seed)
    for ch, cx, cy in order:
        g = cells[ch]
        ox = 35 + cx * cell + (cell - n * px) // 2; oy = 35 + cy * cell + (cell - n * px) // 2
        for j in range(n):
            for i in range(n):
                if g[j, i]:
                    jx, jy = r2.uniform(-0.8, 0.8, 2)
                    cv2.rectangle(cut, (int(ox + i * px + 1 + jx), int(oy + j * px + 1 + jy)),
                                  (int(ox + (i + 1) * px - 2 + jx), int(oy + (j + 1) * px - 2 + jy)), 1.0, -1)
    a = stamp_texture(block * (1 - cut), seed)
    rgba = np.zeros((size, size, 4), np.float32); rgba[..., :3] = RED; rgba[..., 3] = a
    return rgba

def seal_combo(size=520, seed=6):
    """虛像 vertical (白文) + LSM pixel row below — one tall seal"""
    h, w = int(size * 1.72), size
    block = rough_rect(h, w, 6, seed, inset=8)
    cut = np.zeros((h, w), np.float32)
    for k, ch in enumerate('虛像'):
        m = text_mask(ch, 300, path=SERIF, idx=1)
        m = cv2.resize(m, (w - 120, 300))
        y = 40 + k * 314
        cut[y:y + m.shape[0], 60:60 + m.shape[1]] = np.maximum(cut[y:y + m.shape[0], 60:60 + m.shape[1]], m)
    yb = 40 + 2 * 314 + 6
    cv2.line(cut, (40, yb), (w - 40, yb), 1.0, 4)
    px = 20
    letters = 'LSM'
    x = (w - (17 * px)) // 2; y0 = yb + 22
    for ch in letters:
        for j, row in enumerate(PIX[ch]):
            for i, b in enumerate(row):
                if b == '1':
                    cv2.rectangle(cut, (x + i * px + 2, y0 + j * px + 2), (x + (i + 1) * px - 2, y0 + (j + 1) * px - 2), 1.0, -1)
        x += 6 * px
    cut = cut[:h]
    a = stamp_texture(block * (1 - cut), seed)
    rgba = np.zeros((h, w, 4), np.float32); rgba[..., :3] = RED; rgba[..., 3] = a
    return rgba

def on_paper(rgba, seed=1, col=(0.96, 0.93, 0.85)):
    """a stamped tag: paper behind the seal so carved strokes read as paper, not as the background"""
    h, w = rgba.shape[:2]
    pad = int(0.10 * w)
    paper = rough_rect(h + 2 * pad, w + 2 * pad, 4, seed + 50, inset=2)
    out = np.zeros((h + 2 * pad, w + 2 * pad, 4), np.float32)
    out[..., :3] = col; out[..., 3] = paper
    a = rgba[..., 3:4]
    out[pad:pad + h, pad:pad + w, :3] = out[pad:pad + h, pad:pad + w, :3] * (1 - a) + rgba[..., :3] * a
    return out

def scale_rgba(r, s):
    return cv2.resize(r, (int(r.shape[1] * s), int(r.shape[0] * s)), interpolation=cv2.INTER_AREA)

def hanji(h, w, seed=2):
    base = np.ones((h, w, 3), np.float32) * np.array((0.95, 0.92, 0.85), np.float32)
    fib = cv2.blur(np.random.default_rng(seed).random((h, w)).astype(np.float32), (25, 2))
    n = fbm(h, w, 120, seed)
    return np.clip(base * (0.94 + 0.06 * n[..., None]) - (fib[..., None] - 0.5) * 0.05, 0, 1)

# ------------------------------------------------------------------ title A: the waterline
def title_A():
    cv = load('plate2.png')
    surf = int(560 / 1300 * 1040)
    m = text_mask('숨비', 330, fam='song-myung')
    h, w = m.shape
    x = (W - w) // 2; y = surf - int(h * 0.62)
    cut = surf - y
    above = m.copy(); above[cut:] = 0
    below = m.copy(); below[:cut] = 0
    # refraction: rows shifted by a slow sine, slightly stretched
    bel = np.zeros_like(below)
    for r in range(cut, h):
        sh = int(7 * math.sin(r * 0.11) + 3 * math.sin(r * 0.37))
        bel[r] = np.roll(below[r], sh)
    put(cv, cv2.GaussianBlur(above, (0, 0), 6), x + 4, y + 6, (0.20, 0.30, 0.36), 0.25)
    put(cv, above, x, y, (0.99, 0.97, 0.90))
    put(cv, cv2.GaussianBlur(bel, (0, 0), 1.0), x, y, (0.70, 0.92, 0.90), 0.75)
    # bubbles rising from the 비 stem
    for k in range(9):
        bx = x + int(w * 0.83) + int(18 * math.sin(k)); by = y + h + 40 + k * 26
        r = 3 + (k % 3) * 3
        cv2.circle(cv, (bx, by), r, (0.85, 0.97, 0.96), 2, lineType=cv2.LINE_AA)
    sub = text_mask('S U M B I', 44, path=CORM)
    put(cv, sub, (W - sub.shape[1]) // 2, y + h + 70, (0.90, 0.97, 0.96), 0.85)
    finish(cv, 'title_A_waterline.png')

# ------------------------------------------------------------------ title B: brush + breath line + seal
def title_B():
    cv = load('plate.png')
    m = text_mask('숨비', 330, fam='east-sea-dokdo')
    m = dry_brush(m, 7, amt=0.35)
    h, w = m.shape
    x, y = 210, 70
    put(cv, cv2.GaussianBlur(m, (0, 0), 10), x + 6, y + 10, (0.98, 0.96, 0.90), 0.55)   # soft paper halo
    put(cv, m, x, y, (0.10, 0.16, 0.30))
    # breath line: one brush stroke leaving the last letter, rising and falling like 숨비소리
    L = np.zeros((H, W), np.float32)
    x0, y0 = x + w + 10, y + int(h * 0.55)
    pts = []
    for i in range(160):
        t = i / 159
        pts.append((int(x0 + t * 760), int(y0 - 60 * math.sin(t * math.pi * 1.2) * (1 - t * 0.5) + 30 * t)))
    for i in range(len(pts) - 1):
        wd = max(1, int(14 * (1 - i / len(pts)) ** 1.4))
        cv2.line(L, pts[i], pts[i + 1], 1.0, wd, lineType=cv2.LINE_AA)
    L = dry_brush(L, 9, amt=0.6)
    put(cv, L, 0, 0, (0.10, 0.16, 0.30), 0.9)
    ex, ey = pts[-1]
    cv2.circle(cv, (ex + 22, ey), 13, (0.96, 0.46, 0.12), -1, lineType=cv2.LINE_AA)      # a tiny 테왁 at the end of the breath
    finish(cv, 'title_B_brush.png')

# ------------------------------------------------------------------ title C: the 테왁
def title_C():
    """a single 테왁 floating close to camera; the title sits beside it like a buoy-tag"""
    cv = load('plate.png')
    cx, cy, R = 760, 690, 150
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    ball = (((xx - cx) / R) ** 2 + ((yy - cy) / R) ** 2 <= 1).astype(np.float32)
    water = (yy > cy + R * 0.25).astype(np.float32)
    top = ball * (1 - water)
    sub = ball * water
    # ripples around the waterline
    for k in range(4):
        rr = R * (1.15 + 0.22 * k)
        cv2.ellipse(cv, (cx, int(cy + R * 0.25)), (int(rr), int(rr * 0.18)), 0, 0, 360, (0.92, 0.96, 0.94), 3 - k // 2, lineType=cv2.LINE_AA)
    # submerged half: refracted, greener, net faintly below
    put(cv, cv2.GaussianBlur(sub, (0, 0), 2), 0, 0, (0.55, 0.42, 0.20), 0.65)
    net = np.zeros((H, W), np.float32)
    for k in range(-4, 5):
        cv2.line(net, (cx + k * 30, int(cy + R * 0.6)), (cx + k * 18, int(cy + R * 0.6) + 170), 1.0, 2, lineType=cv2.LINE_AA)
    for j in range(4):
        cv2.ellipse(net, (cx, int(cy + R * 0.7) + j * 42), (int(130 - j * 14), 8), 0, 0, 180, 1.0, 2, lineType=cv2.LINE_AA)
    rows = np.arange(H)
    for r in range(int(cy + R * 0.3), min(H, int(cy + R * 0.3) + 260)):
        net[r] = np.roll(net[r], int(5 * math.sin(r * 0.12)))
    put(cv, cv2.GaussianBlur(net, (0, 0), 1.2), 0, 0, (0.70, 0.86, 0.82), 0.45)
    # floating half: orange cel with lit rim and core shadow
    put(cv, top, 0, 0, (0.96, 0.47, 0.12))
    shade = top * ((((xx - cx - 50) / R) ** 2 + ((yy - cy - 40) / R) ** 2) > 0.85)
    put(cv, top - top * (((xx - cx + 40) / R) ** 2 + ((yy - cy + 50) / R) ** 2 > 0.7), 0, 0, (0.99, 0.70, 0.36), 0.0)
    put(cv, shade, 0, 0, (0.78, 0.30, 0.10), 0.7)
    hl = top * ((((xx - cx + 60) / (R * 0.28)) ** 2 + ((yy - cy + 70) / (R * 0.16)) ** 2) <= 1)
    put(cv, hl, 0, 0, (1.0, 0.86, 0.62), 0.9)
    m = text_mask('숨비', 210, fam='gowun-batang')
    tx, ty = cx + R + 110, cy - m.shape[0] - 60
    put(cv, cv2.GaussianBlur(m, (0, 0), 7), tx + 4, ty + 6, (0.02, 0.10, 0.16), 0.55)
    put(cv, m, tx, ty, (1.0, 0.98, 0.93))
    sub_t = text_mask('S U M B I', 40, path=CORM)
    put(cv, cv2.GaussianBlur(sub_t, (0, 0), 5), tx + 8, ty + m.shape[0] + 30, (0.02, 0.10, 0.16), 0.5)
    put(cv, sub_t, tx + 6, ty + m.shape[0] + 28, (0.98, 0.96, 0.90), 0.95)
    finish(cv, 'title_C_tewak.png')

# ------------------------------------------------------------------ seal sheet
def seal_sheet():
    cv = hanji(H, W)
    seals = [('① 虛像工房 白文', seal_baimun(seed=3)), ('② 虛像工房 朱文', seal_zhuwen(seed=4)),
             ('③ LSM印 디지털 인장', seal_pixel2(seed=7)), ('④ 虛像 + LSM 합인', seal_combo(seed=6))]
    for k, (lab, s) in enumerate(seals):
        sc = 340 / max(s.shape[:2])
        s2 = scale_rgba(s, sc)
        x = 120 + k * 440 + (340 - s2.shape[1]) // 2; y = 250 + (480 - s2.shape[0]) // 2 - 30
        put_rgba(cv, s2, x, y)
        t = text_mask(lab, 30, path=SERIF_R, idx=1)
        put(cv, t, 120 + k * 440 + (340 - t.shape[1]) // 2, 800, (0.25, 0.22, 0.20), 0.9)
    t = text_mask('허상공방 인장 시안', 44, path=SERIF, idx=1)
    put(cv, t, 120, 120, (0.20, 0.18, 0.16))
    finish(cv, 'seal_sheet.png')

# ------------------------------------------------------------------ end credit layouts
def credit_D():
    cv = np.ones((H, W, 3), np.float32) * np.array((0.05, 0.10, 0.16), np.float32)
    cv = cv * (0.85 + 0.3 * fbm(H, W, 300, 3)[..., None])
    a = text_mask('Created & Coded by', 46, path=CORM_I)
    b = text_mask('L.S.M.', 74, path=CORM)
    put(cv, a, (W - a.shape[1]) // 2, 300, (0.86, 0.88, 0.86))
    put(cv, b, (W - b.shape[1]) // 2, 372, (0.97, 0.95, 0.88))
    s = scale_rgba(on_paper(seal_pixel2(seed=7), 7), 0.30)
    put_rgba(cv, s, (W - s.shape[1]) // 2, 500)
    c = text_mask('허상공방  虛像工房  Project', 40, path=SERIF_R, idx=1)
    put(cv, c, (W - c.shape[1]) // 2, 760, (0.86, 0.88, 0.86))
    finish(cv, 'credit_D_night.png')

def credit_E():
    cv = load('plate.png')
    dim = np.linspace(0, 1, H, dtype=np.float32)[:, None, None]
    cv = cv * (1 - 0.6 * np.clip((dim - 0.35) / 0.65, 0, 1))
    s = scale_rgba(on_paper(seal_combo(seed=6), 6), 0.30)
    put_rgba(cv, s, W - 120 - s.shape[1], H - 110 - s.shape[0])
    a = text_mask('Created & Coded by  L.S.M.', 50, path=CORM_I)
    c = text_mask('허상공방  虛像工房  Project', 38, path=SERIF_R, idx=1)
    xr = W - 160 - s.shape[1]
    for m, y in ((a, H - 300), (c, H - 220)):
        put(cv, cv2.GaussianBlur(m, (0, 0), 8), xr - m.shape[1], y + 3, (0.02, 0.06, 0.10), 0.6)
        put(cv, m, xr - m.shape[1], y, (0.98, 0.96, 0.90))
    finish(cv, 'credit_E_sea.png')

if __name__ == '__main__':
    title_A(); title_B(); title_C(); seal_sheet(); credit_D(); credit_E()
    print('ok')
