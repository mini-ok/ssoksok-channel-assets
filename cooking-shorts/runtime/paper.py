"""v2 종이 조각 도우미 (v1 story.py 기반 + 폰트 선택, 둥근 별, 모양 도형)"""
import sys, math, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ink import *
import chars as CH

FD2 = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fonts") + "/"
FONTS = {"jua": FD2 + "Jua-Regular.ttf", "do": FD2 + "DoHyeon-Regular.ttf", "black": FD2 + "BlackHanSans-Regular.ttf"}
def F(name): return tf(FONTS[name])

TXT = hx(0x26304F)
BUTTER, ICE, CREAMC, LIME = hx(0xEFE2B4), hx(0xD5E3EC), hx(0xF4F1EA), hx(0xD6EA9C)
SUNO, CLOUD, STAR = hx(0xEE8A4E), hx(0xFAFAF8), hx(0xF6CB45)
CORALC, MINTC, SKYC = hx(0xE9776E), hx(0x8FCFB4), hx(0x9CC6E6)
CORAL_L, MINT_L, LAV, YEL = hx(0xF4B3A8), hx(0xCDEBDD), hx(0xC9C0EC), hx(0xF2D36B)

def grain(shape, seed, k1=1.0, k2=7):
    r = np.random.default_rng(seed)
    n = ndi.gaussian_filter(r.normal(0, 1, shape), k1) * 0.6 + ndi.gaussian_filter(r.normal(0, 1, shape), k2) * 1.4
    return n / (np.abs(n).max() + 1e-6)

def bg(W, H, top=hx(0xECE8EC), bot=hx(0xE4E0E6), seed=1):
    yy = np.linspace(0, 1, H)[:, None, None]
    img = top[None, None, :] * (1 - yy) + bot[None, None, :] * yy
    img = np.repeat(img, W, axis=1)
    n = grain((H, W), seed, 0.8, 9)
    f = ndi.gaussian_filter(np.random.default_rng(seed + 1).normal(0, 1, (H, W)), 3.0)
    return np.clip(img * (1 + 0.03 * n[..., None] + 0.012 * (f / f.std())[..., None]), 0, 1)

def puff_rgb(img, al, rgb, seed=0, soft=None, shadow=(7, 9), sh_blur=9, sh_k=0.30, depth=1.0):
    H, W = al.shape
    soft = soft or 7
    s = ndi.gaussian_filter(ndi.shift(al, shadow, order=1), sh_blur) * sh_k
    img = img * (1 - s[..., None]) + 0.12 * s[..., None]
    h = ndi.gaussian_filter(al, soft)
    gy, gx = np.gradient(h)
    k = 9.0 * depth
    nz = 1 / np.sqrt(1 + (gx * k * soft) ** 2 + (gy * k * soft) ** 2)
    nx, ny = -gx * k * soft * nz, -gy * k * soft * nz
    L = np.array([-0.45, -0.65, 0.62]); L /= np.linalg.norm(L)
    diff = np.clip(nx * L[0] + ny * L[1] + nz * L[2], 0, 1)
    shade = 0.80 + 0.30 * diff
    n = grain((H, W), seed)
    col = np.clip(rgb * shade[..., None] * (1 + 0.05 * n[..., None]), 0, 1)
    a = al[..., None]
    return img * (1 - a) + col * a

def puff(img, mask, col, seed=0, **kw):
    H, W = mask.shape
    return puff_rgb(img, mask, np.zeros((H, W, 3), np.float32) + col[None, None, :], seed, **kw)

def place_rgb(shape, rgb, x, y):
    return np.stack([place(shape, rgb[..., i], x, y) for i in range(3)], 2)

def puff_char(img, drawfn, x, y, size, seed=0, soften_outline=True, soft=None):
    H, W = img.shape[:2]; S = int(size)
    sf = skia.Surface(S, S); cv = sf.getCanvas(); cv.clear(skia.Color(0, 0, 0, 0)); drawfn(cv, S)
    a = sf.makeImageSnapshot().toarray(colorType=skia.kRGBA_8888_ColorType, alphaType=skia.kUnpremul_AlphaType).astype(np.float32) / 255
    rgb, al = a[..., :3], a[..., 3]
    if soften_outline:
        d = np.linalg.norm(rgb - NAVY, axis=2)
        line = al * np.clip(1 - (d - 0.10) / 0.14, 0, 1)
        body = ndi.grey_dilation(rgb * (1 - line[..., None]), size=(9, 9, 1))
        inner = ndi.binary_erosion(al > 0.5, iterations=max(3, S // 60))
        outer_line = line * (1 - inner)
        rgb = rgb * (1 - outer_line[..., None]) + np.clip(body * 0.72, 0, 1) * outer_line[..., None]
    al_f = place((H, W), al, x, y)
    rgb_f = place_rgb((H, W), rgb, x, y)
    return puff_rgb(img, al_f, rgb_f, seed, soft=soft or max(5, S // 45), shadow=(S // 40 + 4, S // 30 + 5), sh_blur=S // 40 + 5, sh_k=0.32)

def char_fn(name, mood, **flags):
    def fn(cv, S):
        old = dict(CH.FLAGS); CH.FLAGS.update(flags)
        getattr(CH, name)(cv, S / 2, S * 0.62, S / 576, mood, 0.0)
        CH.FLAGS.clear(); CH.FLAGS.update(old)
    return fn

def M(W, H): return Mask(W, H)

def rr(W, H, l, t, r, b, rad=14, rot=0.0):
    m = M(W, H); cv = m.cv
    cv.save(); cv.translate((l + r) / 2, (t + b) / 2); cv.rotate(rot); cv.translate(-(l + r) / 2, -(t + b) / 2)
    cv.drawRRect(skia.RRect.MakeRectXY(skia.Rect(l, t, r, b), rad, rad), paint()); cv.restore()
    return m.arr()

def circ(W, H, x, y, r):
    m = M(W, H); m.cv.drawCircle(x, y, r, paint()); return m.arr()

def ring(W, H, x, y, r, w):
    m = M(W, H); m.cv.drawCircle(x, y, r, paint(w)); return m.arr()

def cloud(W, H, x, y, s):
    m = M(W, H)
    for dx, dy, r in ((-60, 10, 38), (-20, -18, 50), (30, -8, 44), (66, 14, 32), (0, 20, 40)):
        m.cv.drawCircle(x + dx * s, y + dy * s, r * s, paint())
    return m.arr()

def poly_mask(W, H, pts):
    m = M(W, H); m.cv.drawPath(path_poly(pts), paint()); return m.arr()

def round_mask(a, r):
    """뾰족한 모서리를 둥글게(블러 후 문턱)"""
    b = ndi.gaussian_filter(a, r)
    return np.clip((b - 0.5) * 6 + 0.5, 0, 1)

def star(W, H, x, y, r, rot=-90, inner=0.45, rnd=0):
    pts = []
    for i in range(10):
        rr_ = r if i % 2 == 0 else r * inner
        a = math.radians(rot + 36 * i); pts.append((x + math.cos(a) * rr_, y + math.sin(a) * rr_))
    m = poly_mask(W, H, pts)
    return round_mask(m, rnd) if rnd else m

def path_mask(W, H, p, stroke=0):
    m = M(W, H); m.cv.drawPath(p, paint(stroke)); return m.arr()

def text_m(W, H, s, x, y, size, face, anchor="l", track=0.0):
    m = M(W, H); w = draw_text(m.cv, s, x, y, size, F(face), track=track, anchor=anchor); return m.arr(), w

def tw(s, size, face): return text_w(s, size, F(face))

def put_text(img, W, H, s, x, y, size, face="jua", col=TXT, anchor="l", track=0.0, shadow=True):
    t, w = text_m(W, H, s, x, y, size, face, anchor, track)
    if shadow:
        sh = ndi.gaussian_filter(ndi.shift(t, (3, 3), order=1), 1.8) * 0.28
        img = img * (1 - sh[..., None]) + 0.1 * sh[..., None]
    return over(img, t, col), w

def highlight(img, W, H, x0, x1, y, h=26, seed=0, col=None):
    m = M(W, H)
    p = skia.Path(); p.moveTo(x0, y); p.lineTo(x1, y - 5); p.lineTo(x1 + 6, y + h - 7); p.lineTo(x0 - 3, y + h); p.close(); m.cv.drawPath(p, paint())
    mm = wobble(m.arr(), 1.4, 1.0, seed)
    col = LIME if col is None else col
    return img * (1 - 0.8 * mm[..., None]) + col[None, None, :] * 0.8 * mm[..., None]

def chip(img, W, H, s, cx, cy, size, face, col, seed, rot=0.0, padx=34, pady=18, tcol=TXT, rad=26):
    """칩 중심 (cx,cy). 회전은 칩과 글자가 함께. 반환: img, 폭, 높이"""
    w = text_w(s, size, F(face)) + padx * 2
    h = size * 0.98 + pady * 2
    l, t, r_, b = cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2
    img = puff(img, rr(W, H, l, t, r_, b, rad, rot), col, seed, soft=6, shadow=(6, 9), sh_blur=8, sh_k=0.28, depth=0.7)
    tm = M(W, H); tm.cv.save(); tm.cv.translate(cx, cy); tm.cv.rotate(rot); tm.cv.translate(-cx, -cy)
    draw_text(tm.cv, s, cx - w / 2 + padx, cy + size * 0.34, size, F(face), anchor="l")
    tm.cv.restore()
    t = tm.arr()
    sh = ndi.gaussian_filter(ndi.shift(t, (3, 3), order=1), 1.8) * 0.25
    img = img * (1 - sh[..., None]) + 0.1 * sh[..., None]
    return over(img, t, tcol), w, h
