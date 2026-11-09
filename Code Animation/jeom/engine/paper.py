"""화선지 — 단위 mm, 배율과 무관하게 같은 자리는 같은 섬유.

View(cx, cy, width_mm, W, H): 화면 픽셀 ↔ 종이 mm 변환.
섬유는 20mm 칸마다 칸 좌표로 시드를 정해 만든다. 배율 단계(px/mm = 3, 6, 12, 24, 48)마다
칸 타일을 그려 캐시하고, 화면에는 가장 가까운 윗단계 타일을 줄여 쓴다.
"""
import math
import numpy as np, cv2

F32 = np.float32
PAPER_W, PAPER_H = 640.0, 420.0
CELL = 20.0
LEVELS = (3, 6, 12, 24, 48)


class View:
    def __init__(self, cx, cy, width_mm, W=1920, H=1080, rot=0.0):
        self.cx, self.cy, self.wmm, self.W, self.H = cx, cy, width_mm, W, H
        self.ppm = W / width_mm
        self.rot = rot

    def grid_mm(self):
        """화면 각 픽셀의 종이 좌표(mm)."""
        yy, xx = np.mgrid[0:self.H, 0:self.W].astype(F32)
        x = (xx - self.W / 2) / self.ppm; y = (yy - self.H / 2) / self.ppm
        if self.rot:
            c, s = math.cos(self.rot), math.sin(self.rot)
            x, y = x * c - y * s, x * s + y * c
        return x + self.cx, y + self.cy

    def to_px(self, x, y):
        dx, dy = (np.asarray(x) - self.cx), (np.asarray(y) - self.cy)
        if self.rot:
            c, s = math.cos(-self.rot), math.sin(-self.rot)
            dx, dy = dx * c - dy * s, dx * s + dy * c
        return dx * self.ppm + self.W / 2, dy * self.ppm + self.H / 2

    def bbox_mm(self, pad=0.0):
        hw = self.W / 2 / self.ppm; hh = self.H / 2 / self.ppm
        r = math.hypot(hw, hh) if self.rot else None
        if r:
            return self.cx - r - pad, self.cy - r - pad, self.cx + r + pad, self.cy + r + pad
        return self.cx - hw - pad, self.cy - hh - pad, self.cx + hw + pad, self.cy + hh + pad


def _cell_fibers(ix, iy):
    """칸(ix,iy)에 속한 섬유 목록(mm): (x, y, 각, 길이, 휨, 밝기, 굵기)."""
    r = np.random.default_rng([ix + 1000, iy + 1000, 0x5eed])
    n = r.poisson(CELL * CELL * 1.2)
    x = ix * CELL + r.uniform(0, CELL, n); y = iy * CELL + r.uniform(0, CELL, n)
    a = r.normal(0.35, 0.9, n)
    L = r.lognormal(math.log(7.0), 0.55, n)           # 섬유 길이 mm
    bend = r.normal(0, 0.12, n)
    v = r.uniform(0.35, 1.0, n)
    th = r.uniform(0.03, 0.07, n)                     # 굵기 mm
    # 닥 껍질 티(짧고 어두움)
    m = r.poisson(CELL * CELL * 0.004)
    fx = ix * CELL + r.uniform(0, CELL, m); fy = iy * CELL + r.uniform(0, CELL, m)
    fa = r.uniform(0, math.pi, m); fl = r.uniform(0.3, 1.1, m)
    return (x, y, a, L, bend, v, th), (fx, fy, fa, fl)


_tiles = {}


import os
CACHE = os.environ.get('JEOM_CACHE', os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'cache', 'paper'))


def _tile(ix, iy, lev):
    key = (ix, iy, lev)
    if key in _tiles:
        return _tiles[key]
    fn = os.path.join(CACHE, f'{lev}_{ix}_{iy}.npz')
    if os.path.exists(fn):
        z = np.load(fn); out = (z['f'], z['k']); _tiles[key] = out
        return out
    pad = 8.0   # 이웃 칸의 긴 섬유가 넘어오도록 여유
    n = int(round((CELL + 2 * pad) * lev))
    fib = np.zeros((n, n), F32); flk = np.zeros((n, n), F32)
    ox, oy = ix * CELL - pad, iy * CELL - pad
    for jx in (ix - 1, ix, ix + 1):
        for jy in (iy - 1, iy, iy + 1):
            (x, y, a, L, bend, v, th), (fx, fy, fa, fl) = _cell_fibers(jx, jy)
            for k in range(len(x)):
                pts = []
                for q in range(7):
                    s = (q / 6 - 0.5) * L[k]
                    aa = a[k] + bend[k] * s
                    pts.append(((x[k] + math.cos(aa) * s - ox) * lev, (y[k] + math.sin(aa) * s - oy) * lev))
                p = np.round(np.array(pts) * 4).astype(np.int32)
                w = max(1, int(round(th[k] * lev)))
                cv2.polylines(fib, [p], False, float(v[k] * min(1.0, th[k] * lev * 1.6)), w, cv2.LINE_AA, shift=2)
            for k in range(len(fx)):
                c, s = math.cos(fa[k]) * fl[k] / 2, math.sin(fa[k]) * fl[k] / 2
                p1 = (int((fx[k] - c - ox) * lev * 4), int((fy[k] - s - oy) * lev * 4))
                p2 = (int((fx[k] + c - ox) * lev * 4), int((fy[k] + s - oy) * lev * 4))
                cv2.line(flk, p1, p2, 1.0, max(1, int(0.15 * lev)), cv2.LINE_AA, shift=2)
    sig = max(0.4, 0.012 * lev)
    fib = cv2.GaussianBlur(fib, (0, 0), sig)
    cut = int(round(pad * lev)); m = int(round(CELL * lev))
    out = (np.clip(fib[cut:cut + m, cut:cut + m], 0, 1.4).astype(np.float16).astype(F32),
           np.clip(flk[cut:cut + m, cut:cut + m], 0, 1).astype(np.float16).astype(F32))
    os.makedirs(CACHE, exist_ok=True)
    np.savez_compressed(fn, f=out[0].astype(np.float16), k=out[1].astype(np.float16))
    _tiles[key] = out
    return out


def _lowfreq(x, y, seed, scale):
    """종이 얼룩(저주파, mm 좌표 함수). 여러 주파수의 사인 합 — 어디서나 같은 값."""
    r = np.random.default_rng(seed)
    out = np.zeros_like(x)
    for k in range(7):
        f = r.uniform(0.6, 1.6) / scale * (1.7 ** (k % 4))
        a = r.uniform(0, math.pi)
        ph = r.uniform(0, 6.28)
        out += np.sin((x * math.cos(a) + y * math.sin(a)) * f + ph) / (1 + k * 0.6)
    return out / 3.0


def paper_layers(view):
    """화면 해상도의 섬유(fib), 티(flk), 얼룩(mot) 층."""
    lev = next((l for l in LEVELS if l >= view.ppm * 0.95), LEVELS[-1])
    x0, y0, x1, y1 = view.bbox_mm(1.0)
    ix0, iy0 = int(math.floor(x0 / CELL)), int(math.floor(y0 / CELL))
    ix1, iy1 = int(math.floor(x1 / CELL)), int(math.floor(y1 / CELL))
    m = int(round(CELL * lev))
    big_f = np.zeros(((iy1 - iy0 + 1) * m, (ix1 - ix0 + 1) * m), F32)
    big_k = np.zeros_like(big_f)
    for iy in range(iy0, iy1 + 1):
        for ix in range(ix0, ix1 + 1):
            f, k = _tile(ix, iy, lev)
            big_f[(iy - iy0) * m:(iy - iy0 + 1) * m, (ix - ix0) * m:(ix - ix0 + 1) * m] = f
            big_k[(iy - iy0) * m:(iy - iy0 + 1) * m, (ix - ix0) * m:(ix - ix0 + 1) * m] = k
    X, Y = view.grid_mm()
    mx = ((X - ix0 * CELL) * lev).astype(F32); my = ((Y - iy0 * CELL) * lev).astype(F32)
    fib = cv2.remap(big_f, mx, my, cv2.INTER_AREA if lev > view.ppm * 1.5 else cv2.INTER_LINEAR)
    if lev > view.ppm * 1.5:      # 줄일 때 계단 방지
        fib = cv2.remap(cv2.GaussianBlur(big_f, (0, 0), lev / view.ppm * 0.5), mx, my, cv2.INTER_LINEAR)
    flk = cv2.remap(big_k, mx, my, cv2.INTER_LINEAR)
    mot = _lowfreq(X, Y, 7, 18.0) + 0.5 * _lowfreq(X, Y, 8, 4.0)
    return fib, flk, mot.astype(F32), X, Y


PAPER_RGB = np.array((0.925, 0.893, 0.818), F32)


def paper_rgb(fib, flk, mot):
    base = PAPER_RGB * (1 + 0.022 * mot[..., None])
    return (base + 0.04 * fib[..., None] * np.array((1, 1, 0.95), F32)
            - 0.10 * flk[..., None] * np.array((0.55, 0.7, 0.9), F32))
