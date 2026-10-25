import os
"""세 가지 잉크(PAPER 연필 / BLUEPRINT 청사진 / HOLOGRAM 홀로그램) + 몸속 회사 캐릭터 스틸컷 엔진"""
import math, sys
import numpy as np
from PIL import Image
from scipy import ndimage as ndi
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import skia
import chars as CH

FD = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fonts") + "/"
GEIST = {900: FD + "Geist-Black.ttf", 800: FD + "Geist-Bold.ttf", 600: FD + "Geist-SemiBold.ttf"}
NOTO = "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc"
TF = {}

def tf(path, idx=0):
    k = (path, idx)
    if k not in TF:
        TF[k] = skia.Typeface.MakeFromFile(path, idx)
    return TF[k]

def KO(weight=900):
    return tf(NOTO, 1 if weight >= 900 else 0)   # 1: Black, 0: Bold

def EN(weight=900):
    return tf(GEIST[weight])

def hx(h):
    return np.array([(h >> 16) & 255, (h >> 8) & 255, h & 255], np.float32) / 255

CREAM, BLUE, CYAN = hx(0xEDE6D5), hx(0x1B3ED2), hx(0x45F0DD)
BLACK, GRAPH, WHITE = hx(0x07080A), hx(0x16161A), hx(0xFFFFFF)
NAVY = hx(0x2B2D5B)
RNG = np.random.default_rng(7)

# ---------- 마스크 그리기 ----------
class Mask:
    def __init__(self, w, h):
        self.w, self.h = w, h
        self.sf = skia.Surface(w, h)
        self.cv = self.sf.getCanvas()
        self.cv.clear(skia.Color(0, 0, 0, 0))

    def arr(self):
        a = self.sf.makeImageSnapshot().toarray(colorType=skia.kRGBA_8888_ColorType, alphaType=skia.kUnpremul_AlphaType)
        return a[..., 3].astype(np.float32) / 255

def paint(stroke=0, dash=None, cap=True):
    p = skia.Paint(AntiAlias=True, Color=skia.Color(255, 255, 255, 255))
    if stroke:
        p.setStyle(skia.Paint.kStroke_Style)
        p.setStrokeWidth(stroke)
        if cap:
            p.setStrokeCap(skia.Paint.kRound_Cap)
            p.setStrokeJoin(skia.Paint.kRound_Join)
        if dash:
            p.setPathEffect(skia.DashPathEffect.Make(dash, 0))
    return p

def text_w(s, size, face, track=0.0):
    f = skia.Font(face, size)
    return sum(f.measureText(ch) for ch in s) + track * size * (len(s) - 1)

def draw_text(cv, s, x, y, size, face, track=0.0, anchor="l", stroke=0):
    f = skia.Font(face, size)
    f.setEdging(skia.Font.Edging.kAntiAlias)
    w = text_w(s, size, face, track)
    if anchor == "c":
        x -= w / 2
    elif anchor == "r":
        x -= w
    p = paint(stroke) if stroke else paint()
    for ch in s:
        cv.drawString(ch, x, y, f, p)
        x += f.measureText(ch) + track * size
    return w

def fit_size(s, width, face, track=0.0):
    return width / text_w(s, 100, face, track) * 100

def path_poly(pts, close=True):
    p = skia.Path()
    p.moveTo(*pts[0])
    for q in pts[1:]:
        p.lineTo(*q)
    if close:
        p.close()
    return p

def hexagon(cx, cy, r, rot=-90):
    return [(cx + r * math.cos(math.radians(rot + 60 * i)), cy + r * math.sin(math.radians(rot + 60 * i))) for i in range(6)]

def gear_path(cx, cy, n, r, rot=0.0):
    m = 2 * r / n
    ro, rr = r + m, r - 1.25 * m
    pts = []
    for i in range(n):
        a = 2 * math.pi * i / n + math.radians(rot)
        st = 2 * math.pi / n
        for f, rad in ((0.0, rr), (0.18, rr), (0.30, ro), (0.52, ro), (0.64, rr), (1.0, rr)):
            ang = a + f * st
            pts.append((cx + rad * math.cos(ang), cy + rad * math.sin(ang)))
    return path_poly(pts)

# ---------- 캐릭터 → 선 / 면 / 빛 ----------
def character(name, mood, size):
    S = int(size)
    sf = skia.Surface(S, S)
    cv = sf.getCanvas()
    cv.clear(skia.Color(0, 0, 0, 0))
    getattr(CH, name)(cv, S / 2, S * 0.62, S / 576, mood, 0.0)
    a = sf.makeImageSnapshot().toarray(colorType=skia.kRGBA_8888_ColorType, alphaType=skia.kUnpremul_AlphaType).astype(np.float32) / 255
    rgb, al = a[..., :3], a[..., 3]
    d = np.linalg.norm(rgb - NAVY, axis=2)
    line = al * np.clip(1 - (d - 0.10) / 0.14, 0, 1)
    fill = np.clip(al - line, 0, 1)
    # 점토 조명처럼 부풀린 높이맵에서 빛 계산(빗금 밀도, 스캔라인 두께에 씀)
    h = ndi.gaussian_filter(al, S / 30) + ndi.gaussian_filter(al, S / 90) * 0.6
    gy, gx = np.gradient(h)
    k = S / 40
    nz = 1 / np.sqrt(1 + (gx * k) ** 2 + (gy * k) ** 2)
    L = np.array([-0.5, -0.6, 0.62]); L /= np.linalg.norm(L)
    light = np.clip(-gx * k * nz * L[0] - gy * k * nz * L[1] + nz * L[2], 0, 1)
    lum = rgb.mean(2)
    return dict(line=line, fill=fill, alpha=al, light=light, lum=lum, S=S)

def place(canvas_shape, arr, x, y):
    """arr(정사각) 중심을 (x, y)에 두고 화면 크기 배열로 붙인다"""
    H, W = canvas_shape
    out = np.zeros((H, W), np.float32)
    S = arr.shape[0]
    x0, y0 = int(x - S / 2), int(y - S / 2)
    sx0, sy0 = max(0, -x0), max(0, -y0)
    dx0, dy0 = max(0, x0), max(0, y0)
    w = min(S - sx0, W - dx0)
    h = min(S - sy0, H - dy0)
    if w > 0 and h > 0:
        out[dy0:dy0 + h, dx0:dx0 + w] = arr[sy0:sy0 + h, sx0:sx0 + w]
    return out

# ---------- 공통 효과 ----------
def hatch(shape, spacing, width, angle=45, wobble=0.0, seed=0):
    H, W = shape
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    a = math.radians(angle)
    u = xx * math.cos(a) + yy * math.sin(a)
    v = -xx * math.sin(a) + yy * math.cos(a)
    if wobble:
        r = np.random.default_rng(seed)
        ph = r.uniform(0, 6.28, 3)
        u = u + wobble * (np.sin(v / 41 + ph[0]) + 0.6 * np.sin(v / 13 + ph[1]) + 0.4 * np.sin(u / 29 + ph[2]))
    t = u / spacing
    dist = np.abs(t - np.round(t)) * spacing
    return np.clip(width / 2 + 0.5 - dist, 0, 1)

def hatch_progress(shape, angle, spacing, frac):
    """빗금을 한 줄씩 그리는 중인 상태: 앞쪽 frac 비율의 줄만 남긴다"""
    H, W = shape
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    a = math.radians(angle)
    u = xx * math.cos(a) + yy * math.sin(a)
    lo, hi = u.min(), u.max()
    return (u < lo + (hi - lo) * frac).astype(np.float32)

def wobble(mask, amp, scale=1.0, seed=0):
    H, W = mask.shape
    r = np.random.default_rng(seed)
    ph = r.uniform(0, 6.28, 4)
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    dx = amp * (np.sin(yy / (47 * scale) + ph[0]) + 0.5 * np.sin(yy / (17 * scale) + ph[1]))
    dy = amp * (np.sin(xx / (53 * scale) + ph[2]) + 0.5 * np.sin(xx / (19 * scale) + ph[3]))
    return ndi.map_coordinates(mask, [yy + dy, xx + dx], order=1, mode="constant")

def paper_bg(W, H):
    n1 = ndi.gaussian_filter(RNG.normal(0, 1, (H, W)), 0.7)
    n2 = ndi.gaussian_filter(RNG.normal(0, 1, (H, W)), 5)
    fib = ndi.gaussian_filter(RNG.normal(0, 1, (H, W)), (0.6, 9))
    g = 1 + 0.018 * n1 / n1.std() + 0.012 * n2 / n2.std() + 0.01 * fib / fib.std()
    img = CREAM[None, None, :] * g[..., None]
    tooth = (n1 / n1.std() > 0.55).astype(np.float32)   # 종이 결(연필이 안 묻는 곳)
    return np.clip(img, 0, 1), tooth

def grid_mask(W, H, step=60, ox=None, oy=None):
    ox = (W % step) / 2 if ox is None else ox
    oy = (H % step) / 2 if oy is None else oy
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    def lines(c, o, major):
        k = (c - o) / step
        d = np.abs(k - np.round(k)) * step
        on = np.clip(1.6 - d, 0, 1)
        isMaj = (np.round(k).astype(int) % 5 == 0)
        return on * (isMaj if major else ~isMaj)
    minor = np.maximum(lines(xx, ox, False), lines(yy, oy, False))
    major = np.maximum(lines(xx, ox, True), lines(yy, oy, True))
    return minor, major

def mul(img, m, col):
    return img * (1 - m[..., None] * (1 - col[None, None, :]))

def over(img, m, col):
    m = np.clip(m, 0, 1)[..., None]
    return img * (1 - m) + col[None, None, :] * m

def pencil(img, m, col, tooth, seed=0, amp=1.4):
    """연필 선: 사인파로 비틀고 두 번 긋고(굵게 90%, 반 굵기 40%) 종이 결을 빼고 곱하기"""
    s1 = wobble(m, amp, 1.0, seed) * 0.9
    thin = ndi.grey_erosion(m, size=(3, 3))
    s2 = wobble(thin, amp * 2.2, 0.7, seed + 11) * 0.4
    s = np.clip(np.maximum(s1, s2) + s2 * 0.3, 0, 1)
    s = s * (1 - 0.55 * tooth)
    return mul(img, s, col)

def holo_line(img, m, width_px):
    img = over(img, m, CYAN)
    core = ndi.grey_erosion(m, size=(max(1, int(width_px * 0.7)),) * 2)
    return over(img, core, WHITE)

def scanlines(shape, light, pitch=8, tmin=0.6, tmax=6.0, oy=0):
    H, W = shape
    yy = np.mgrid[0:H, 0:W][0].astype(np.float32)
    t = (yy - oy) / pitch
    d = np.abs(t - np.round(t)) * pitch
    th = tmin + (tmax - tmin) * light
    return np.clip(th / 2 + 0.5 - d, 0, 1)

def save(img, path):
    Image.fromarray((np.clip(img, 0, 1) * 255).astype(np.uint8)).save(path)
