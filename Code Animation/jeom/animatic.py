"""〈점〉 애니마틱 v1 — 960×540, 투스(12장/초), 실제 카메라·타이밍 + 임시 소리.
C1(화실)·C11b(창밖)·C2의 붓은 자리표시(회색 상자 수준). 나머지는 실제 종이·용·번짐 엔진을 저해상도로.

python3 animatic.py frames 0 126     # frames/f%05d.png (2코어면 구간을 나눠 두 번 실행)
python3 animatic.py still 45.0 73.5  # 확인용 정지
python3 animatic.py encode           # frames + temp audio → animatic.mp4
"""
import sys, os, math, subprocess
HERE = os.path.dirname(os.path.abspath(__file__))
os.environ.setdefault('JEOM_RES', '0.5')
sys.path.insert(0, os.path.join(HERE, 'engine')); sys.path.insert(0, os.path.join(HERE, '..', '_shared'))
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont
from paper import View, paper_layers, paper_rgb
from brush import render_strokes
from look import INK_ABS, light, film, letterbox
import dragon, inkmm
import timeline as TL

from scale import S, W, H, SUF
F32 = np.float32
FONT_K = '/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc'
FONT_T = '/usr/share/fonts/opentype/noto/NotoSerifCJK-Bold.ttc'
CACHE = os.path.join(HERE, 'cache', 'animatic'); os.makedirs(CACHE, exist_ok=True)


def ramp(t, a, b):
    return float(np.clip((t - a) / (b - a), 0, 1))


def ease(u):
    return u * u * (3 - 2 * u)


# ---------------------------------------------------------------- 카메라 (중심 mm, 화폭 mm)
def lerp3(a, b, u):
    return tuple(a[i] + (b[i] - a[i]) * u for i in range(3))


CAMS = {
    'C2': lambda u: (60, 382, 110),
    'C3': lambda u: (62, 372, 170),
    'C4': lambda u: lerp3((46, 386, 72), (52, 380, 80), u),
    'C5': lambda u: lerp3((320, 210, 660), (150, 318, 430), ease(u)),
    'C6': lambda u: lerp3((196, 270, 95), (205, 264, 88), u),
    'C7': lambda u: lerp3((236, 246, 120), (252, 232, 110), u),     # 원근 변환 전 위에서 본 화면
    'C8': lambda u: lerp3((278, 178, 130), (294, 150, 110), ease(u)),
    'C9': lambda u: lerp3((300, 118, 62), (300, 113, 48), ease(u)),
    'C10': lambda u: (300, 113, 70),
    'C11a': lambda u: lerp3((300, 200, 520), (320, 210, 660), u),
    'C12': lambda u: lerp3((308, 254, 620), (318, 254, 650), u),
    'CR': lambda u: (318, 254, 650),
}


def cam_at(t):
    name, lt, d = TL.cut_at(t)
    u = lt / d
    q = math.floor(u * d * 12) / (d * 12)            # 카메라도 투스
    return name, CAMS[name](q) if name in CAMS else None


# ---------------------------------------------------------------- 판(plate): 컷마다 한 번 그린 종이 + 용
class Plate:
    def __init__(self, key, cx, cy, wmm, ppm, strokes_filter=None, with_dragon=True):
        self.v = View(cx, cy, wmm, int(wmm * ppm), int(wmm * ppm * 0.75))
        fn = os.path.join(CACHE, f'plate_{key}{SUF}.npz')
        if os.path.exists(fn):
            z = np.load(fn); self.rgb, self.fib, self.drg = z['rgb'], z['fib'], z['drg']
        else:
            fib, flk, mot, X, Y = paper_layers(self.v)
            self.rgb = paper_rgb(fib, flk, mot).astype(F32); self.fib = fib.astype(F32)
            if with_dragon:
                st = dragon.strokes()
                if strokes_filter:
                    st = [s for s in st if strokes_filter(s)]
                self.drg = (render_strokes(self.v, st, fib) * dragon.eye_blank(X, Y)).astype(F32)
            else:
                self.drg = np.zeros_like(fib)
            np.savez_compressed(fn, rgb=self.rgb.astype(np.float16), fib=self.fib.astype(np.float16), drg=self.drg.astype(np.float16))
        self.rgb = self.rgb.astype(F32); self.fib = self.fib.astype(F32); self.drg = self.drg.astype(F32)

    def sample(self, X, Y, dy=None):
        v = self.v
        mx = ((X - v.cx) * v.ppm + v.W / 2).astype(F32); my = ((Y - v.cy) * v.ppm + v.H / 2).astype(F32)
        rgb = cv2.remap(self.rgb, mx, my, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
        fib = cv2.remap(self.fib, mx, my, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
        if dy is not None:
            my2 = ((Y + dy - v.cy) * v.ppm + v.H / 2).astype(F32)
            drg = cv2.remap(self.drg, mx, my2, cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT)
        else:
            drg = cv2.remap(self.drg, mx, my, cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT)
        return rgb, fib, drg


_plates = {}


def plate_for(name):
    if name in _plates:
        return _plates[name]
    if name in ('C5', 'C11a', 'C1', 'C11b'):
        p = Plate('whole', 320, 210, 680, 2.4 * S)
    elif name in ('C12', 'CR'):
        p = Plate('morning', 320, 210, 680, 2.4 * S, strokes_filter=lambda s: s.name.startswith('cloud'))
    elif name in ('C2', 'C3', 'C4'):
        p = Plate('corner', 60, 378, 190, W / 72 * 1.05)
    elif name in ('C6',):
        p = Plate('c6', 200, 267, 110, W / 88 * 1.05)
    elif name in ('C7',):
        p = Plate('c7', 245, 238, 150, W / 110 * 1.05)
    elif name in ('C8',):
        p = Plate('c8', 286, 164, 160, W / 110 * 1.05)
    else:                                                             # C9, C10
        p = Plate('eye', 300, 115, 80, W / 48 * 1.0)
    _plates[name] = p
    return p


# ---------------------------------------------------------------- 점
_dot = None


def dot():
    global _dot
    if _dot is None:
        v = View((inkmm.X0 + inkmm.X1) / 2, (inkmm.Y0 + inkmm.Y1) / 2, inkmm.X1 - inkmm.X0, inkmm.GW, inkmm.GH)
        fib, _, _, _, _ = paper_layers(v)
        _dot = inkmm.Dot(inkmm.Field(fib.astype(F32)), TL)
    return _dot


# ---------------------------------------------------------------- 사물: 자·칼, 손 그림자
U = np.array((1, 1), F32) / math.sqrt(2); NRM = np.array((1, -1), F32) / math.sqrt(2)
P0 = np.array((0, 318), F32)


def ruler_offset(t):
    if t < TL.RULER_IN[0]:
        return None
    u = ease(ramp(t, *TL.RULER_IN))
    return np.array((-140, 140), F32) * (1 - u)


def draw_objects(img, view, t, rgbmul=1.0):
    off = ruler_offset(t)
    if off is None or t >= TL.RULER_OUT:
        return img
    def poly(pts):
        px, py = view.to_px(np.array([p[0] for p in pts]) + off[0], np.array([p[1] for p in pts]) + off[1])
        return np.stack([px, py], 1).astype(np.int32)
    ruler = [P0 + U * -40, P0 + U * 200, P0 + U * 200 + NRM * 24, P0 + U * -40 + NRM * 24]
    knife = [P0 + U * 110 + NRM * 6, P0 + U * 168 + NRM * 9, P0 + U * 168 + NRM * 16, P0 + U * 110 + NRM * 15]
    handle = [P0 + U * 168 + NRM * 8, P0 + U * 212 + NRM * 8, P0 + U * 212 + NRM * 17, P0 + U * 168 + NRM * 17]
    sh = np.zeros(img.shape[:2], F32)
    shoff = np.array((1.6, 2.4))
    for pts in (ruler,):
        cv2.fillPoly(sh, [poly([p + shoff for p in pts])], 1.0)
    sh = cv2.GaussianBlur(sh, (0, 0), max(1.0, view.ppm * 1.2))
    img = img * (1 - 0.45 * sh[..., None])
    lay = np.zeros_like(img); m = np.zeros(img.shape[:2], F32)
    cv2.fillPoly(lay, [poly(ruler)], (0.74, 0.62, 0.40)); cv2.fillPoly(m, [poly(ruler)], 1.0)
    # 대나무 마디
    for s in range(-20, 200, 46):
        a, b = P0 + U * s, P0 + U * s + NRM * 24
        cv2.line(lay, tuple(poly([a])[0]), tuple(poly([b])[0]), (0.52, 0.40, 0.24), max(1, int(view.ppm * 0.8)))
    cv2.fillPoly(lay, [poly(knife)], (0.62, 0.64, 0.66)); cv2.fillPoly(m, [poly(knife)], 1.0)
    cv2.fillPoly(lay, [poly(handle)], (0.32, 0.20, 0.13)); cv2.fillPoly(m, [poly(handle)], 1.0)
    m = cv2.GaussianBlur(m, (0, 0), 0.7)[..., None]
    return img * (1 - m) + lay * rgbmul * m


def hand_shadow(img, view, t, t0, t1, a, b, strength=0.4):
    """손 그림자: t0~t1 동안 a(mm)에서 b로 지나가는 흐린 그림자."""
    if not (t0 <= t < t1):
        return img
    u = ease((t - t0) / (t1 - t0))
    cx, cy = a[0] + (b[0] - a[0]) * u, a[1] + (b[1] - a[1]) * u
    X, Y = view.grid_mm()
    d = ((X - cx) / 55) ** 2 + ((Y - cy) / 26) ** 2
    s = np.exp(-d * 1.4) * math.sin(math.pi * min(1, u * 1.2)) * strength
    return img * (1 - s[..., None])


# ---------------------------------------------------------------- 낙관·제목·라벨
_seal = None


def seal_rgba():
    global _seal
    if _seal is None:
        _seal = np.load(os.path.join(HERE, '..', '_shared', 'seal_baimun3.npy')).astype(F32)
    return _seal


def stamp_seal(img, view, t):
    if t < TL.SEAL_T:
        return img
    s = seal_rgba(); size = int(14 * view.ppm)
    if size < 4:
        return img
    sr = cv2.resize(s, (size, size), interpolation=cv2.INTER_AREA)
    px, py = view.to_px(*TL.SEAL_AT); x0, y0 = int(px - size / 2), int(py - size / 2)
    a = sr[..., 3:4] * 0.92 * ease(ramp(t, TL.SEAL_T, TL.SEAL_T + 0.17))
    sub = img[y0:y0 + size, x0:x0 + size]
    if sub.shape[:2] != (size, size):
        return img
    img[y0:y0 + size, x0:x0 + size] = sub * (1 - a) + sub * sr[..., :3] * 1.15 * a     # 인주는 종이에 곱해진다
    return img


def text_mask(txt, size, font=FONT_T):
    f = ImageFont.truetype(font, size)
    im = Image.new('L', (W, H), 0); d = ImageDraw.Draw(im)
    d.text((W * 0.66, H * 0.10), txt, font=f, fill=255)
    return np.asarray(im, F32) / 255


_title = None


def label(img, t):
    name, lt, d = TL.cut_at(t)
    im = Image.fromarray((np.clip(img, 0, 1) * 255).astype(np.uint8)); dr = ImageDraw.Draw(im)
    f = ImageFont.truetype(FONT_K, 15)
    s = f'{name}  {int(t // 60)}:{t % 60:04.1f}'
    dr.rectangle((6, H - 34, 6 + len(s) * 9 + 10, H - 12), fill=(0, 0, 0))
    dr.text((12, H - 33), s, font=f, fill=(235, 235, 235))
    return np.asarray(im, F32) / 255


# ---------------------------------------------------------------- 자리표시 컷
def c1_room(t):
    """화실(자리표시): 창호지 벽, 등잔, 바닥의 화선지(실제 용 판을 원근으로), 창호지 위 화가 그림자."""
    img = np.zeros((H, W, 3), F32) + np.array((0.10, 0.07, 0.05), F32)
    yy = np.linspace(0, 1, H)[:, None, None]
    img = img + (yy > 0.45) * np.array((0.10, 0.07, 0.045), F32) * (yy - 0.45) * 1.6
    # 창호지 벽
    wx0, wx1, wy0, wy1 = 260, 900, 20, 250
    img[wy0:wy1, wx0:wx1] = np.array((0.62, 0.52, 0.36), F32)
    for x in range(wx0, wx1, 40):
        img[wy0:wy1, x:x + 3] = (0.25, 0.17, 0.10)
    for y in range(wy0, wy1, 46):
        img[y:y + 3, wx0:wx1] = (0.25, 0.17, 0.10)
    # 화가 그림자(창호지 위): 앉은 몸 + 팔 + 붓
    sh = np.zeros((H, W), F32)
    cv2.ellipse(sh, (460, 205), (70, 60), 0, 180, 360, 1.0, -1)
    cv2.circle(sh, (460, 118), 28, 1.0, -1)
    cv2.rectangle(sh, (390, 205), (530, 250), 1.0, -1)
    a = -0.15 - 0.55 * ease(ramp(t, 2.5, 4.0)) + 0.55 * ease(ramp(t, 6.2, 7.6))
    sx, sy = 500, 165
    ex, ey = int(sx + math.cos(a) * 90), int(sy - math.sin(a) * 90)
    cv2.line(sh, (sx, sy), (ex, ey), 1.0, 16)
    cv2.line(sh, (ex, ey), (int(ex + 50), int(ey + 18)), 1.0, 4)
    sh = cv2.GaussianBlur(sh, (0, 0), 5) * (np.arange(W)[None, :] >= wx0) * (np.arange(W)[None, :] < wx1) * \
        (np.arange(H)[:, None] >= wy0) * (np.arange(H)[:, None] < wy1)
    img = img * (1 - 0.55 * sh[..., None])
    # 바닥의 화선지(실제 판을 원근으로)
    p = plate_for('C1'); v = View(320, 210, 640, 640, 420)
    X, Y = v.grid_mm(); rgb, fib, drg = p.sample(X, Y)
    pap = rgb * np.exp(-drg[..., None] * INK_ABS)
    src = np.float32([[0, 0], [640, 0], [640, 420], [0, 420]])
    dst = np.float32([[230, 300], [790, 300], [930, 520], [90, 520]])
    M = cv2.getPerspectiveTransform(src, dst)
    warped = cv2.warpPerspective(pap.astype(F32), M, (W, H))
    mk = cv2.warpPerspective(np.ones((420, 640), F32), M, (W, H))[..., None]
    img = img * (1 - mk) + warped * mk * 0.9
    # 등잔
    yy, xx = np.mgrid[0:H, 0:W].astype(F32)
    flick = 1 + 0.06 * math.sin(t * 9.1) + 0.04 * math.sin(t * 23.0)
    glow = np.exp(-((xx - 150) ** 2 + (yy - 360) ** 2) / (2 * 260 ** 2)) * 0.55 * flick
    img = img * (0.55 + glow[..., None] * np.array((1.3, 1.0, 0.6), F32))
    cv2.circle(img, (150, 360), 7, (1.0, 0.85, 0.45), -1)
    return img


def c11b_sky(t, lt):
    yy, xx = np.mgrid[0:H, 0:W].astype(F32)
    img = np.zeros((H, W, 3), F32) + (0.10 + 0.14 * yy[..., None] / H) * np.array((0.55, 0.62, 0.78), F32)
    r = np.random.default_rng(5)
    cl = np.zeros((H, W), F32)
    for k in range(4):
        g = r.standard_normal((H // (40 // (k + 1)) + 2, W // (40 // (k + 1)) + 2)).astype(F32)
        cl += cv2.resize(g, (W, H), interpolation=cv2.INTER_CUBIC) / (k + 1)
    cl = np.clip(cl * 0.5 + 0.2 + 0.03 * math.sin(lt), 0, 1)
    img = img * (1 - 0.5 * cl[..., None])
    # 용 실루엣(실제 용 판을 줄여) 왼쪽 아래 → 오른쪽 위로 사라짐
    p = plate_for('C11b'); v = View(420, 210, 440, 480, 290)
    X, Y = v.grid_mm(); _, _, drg = p.sample(X, Y)
    u = lt / 6.0
    M = np.float32([[0.9, -0.2, 120 + 520 * u], [0.2, 0.9, 260 - 300 * u]])
    sil = cv2.warpAffine(drg, M, (W, H)) * (1 - ease(ramp(u, 0.55, 1.0)))
    sil = sil * (1 - 0.6 * cl)
    img = img * np.exp(-sil[..., None] * 1.6)
    # 빗줄기
    rr = np.random.default_rng(int(lt * 12))
    for _ in range(140):
        x, y = rr.integers(0, W), rr.integers(0, H)
        cv2.line(img, (int(x), int(y)), (int(x - 6), int(y + 26)), (0.55, 0.6, 0.7), 1)
    f = TL.flash(t)
    return img * (1 + 1.4 * f)


# ---------------------------------------------------------------- 한 장
def frame(t):
    th = math.floor(t * 12) / 12
    name, cam = cam_at(th)
    lt = th - [c[1] for c in TL.CUTS if c[0] == name][0]
    if name == 'C1':
        img = c1_room(th)
    elif name == 'C11b':
        img = c11b_sky(th, lt)
    else:
        cx, cy, wmm = cam
        view = View(cx, cy, wmm, W, H)
        X, Y = view.grid_mm()
        p = plate_for(name)
        dy = None
        if name == 'C11a':
            d = 280 * ease(ramp(lt, 1.6, 8.0)) ** 1.5
            dy = np.full_like(Y, d)
        rgb, fib, drg = p.sample(X, Y, dy)
        if name == 'C11a' and lt > 1.6:
            sg = 0.5 + 9.0 * ramp(lt, 1.6, 6.0)            # 젖은 먹이 몸 선을 따라 끌림(세로 흐림)
            drg = cv2.GaussianBlur(drg, (0, 0), sigmaX=0.6, sigmaY=sg)
        # 점
        D = dot()
        dens_g, live = D.density(th, want_live=True)
        wet_g = D.wet(th)
        pup = D.pupil
        if pup is not None:
            dens_g = dens_g - pup                              # 눈동자는 용과 함께 움직이고, 용이 떠나면 사라진다
            if name == 'C11a':
                pv = inkmm.sample(pup, view, X, Y + dy)
            elif name in ('C9', 'C10'):
                pv = inkmm.sample(pup, view, X, Y)
            else:
                pv = 0
        else:
            pv = 0
        dd = inkmm.sample(dens_g, view, X, Y) + pv
        wv = inkmm.sample(wet_g, view, X, Y)
        sig = max(0.6, 0.3 * view.ppm)
        halo = cv2.GaussianBlur(dd, (0, 0), sig)
        dd = dd + np.clip(halo - dd, 0, 0.6) * np.clip(fib * 1.5 - 0.2, 0, 1.3) * 1.4
        dens = drg + dd
        pap = rgb * (1 - 0.06 * np.clip(wv, 0, 1)[..., None]) + 0.03 * np.clip(wv, 0, 1)[..., None] * fib[..., None]
        img = pap * np.exp(-dens[..., None] * INK_ABS)
        # 젖은 몸의 윤기(반사광 한 점) — 지금의 몸에만
        if live is not None and live.sum() > 0 and name not in ('C12', 'CR'):
            gx = float((live * inkmm.XM).sum() / live.sum()); gy = float((live * inkmm.YM).sum() / live.sum())
            if th >= 79.0:
                gx, gy = TL.E
                if name == 'C11a':
                    gy -= float(dy[0, 0])
            wet_here = float(inkmm.sample(wet_g, view, np.array([[gx]], F32), np.array([[gy]], F32))[0, 0])
            on = wet_here > 0.25 or th >= 79.0
            if on:
                px, py = view.to_px(gx - 0.6, gy - 0.6)
                r = max(1.5, 0.7 * view.ppm)
                yy, xx = np.mgrid[0:H, 0:W].astype(F32)
                gl = np.exp(-((xx - px) ** 2 + (yy - py) ** 2) / (r * r)) * (0.55 if th < 79 else 0.8)
                img = img + gl[..., None] * np.array((0.9, 0.92, 1.0), F32)
        img = draw_objects(img, view, th, rgbmul=1.0)
        if name == 'C3':
            img = hand_shadow(img, view, th, 17.0, 19.6, (-60, 470), (40, 380), 0.45)
        if name == 'C12':
            img = hand_shadow(img, view, th, 108.6, 110.6, (-20, 420), (200, 300), 0.35)
            img = stamp_seal(img, view, th)
        if name == 'CR':
            img = stamp_seal(img, view, th)
        # 조명
        if name in ('C2',):
            img = light(img, 'lamp')
        elif name == 'C3':
            u = ease(ramp(th, 20.4, 21.4))
            img = light(img, 'lamp') * (1 - u) + light(img, 'night') * u
        elif name in ('C4', 'C5', 'C6', 'C7', 'C8', 'C10', 'C11a'):
            img = light(img, 'night', extra=TL.flash(th))
        elif name == 'C9':
            u = ease(ramp(th, 70.0, 71.5))
            img = light(img, 'night') * (1 - u) + light(img, 'silver') * u
        elif name in ('C12', 'CR'):
            img = light(img, 'morning')
            # 창호 너머 아침 빛줄기
            yy, xx = np.mgrid[0:H, 0:W].astype(F32)
            img = img * (0.92 + 0.10 * (0.5 + 0.5 * np.sin((xx * 0.9 - yy * 0.5) / 60.0)))[..., None]
        if name == 'C7':                                        # 낮은 앵글: 종이 평면 원근 변환
            src = np.float32([[0, 0], [W, 0], [W, H], [0, H]])
            dst = np.float32([[W * 0.30, H * 0.30], [W * 0.70, H * 0.30], [W * 1.25, H * 1.0], [-W * 0.25, H * 1.0]])
            M = cv2.getPerspectiveTransform(src, dst)
            img = cv2.warpPerspective(img.astype(F32), M, (W, H), borderMode=cv2.BORDER_REPLICATE)
            yy = np.linspace(0, 1, H)[:, None, None]
            haze = np.clip((0.42 - yy) / 0.12, 0, 1)
            img = img * (1 - haze) + haze * np.array((0.06, 0.08, 0.12), F32) * (1 + 3 * TL.flash(th))
        # 제목
        if name == 'C12' and th >= TL.TITLE_T[0]:
            global _title
            if _title is None:
                _title = text_mask('점', 120)
            a = ease(ramp(th, TL.TITLE_T[0], TL.TITLE_T[0] + 0.5))
            img = img * np.exp(-(_title * 2.4 * a)[..., None] * INK_ABS)
    if name == 'C2':
        img = c2_brush(img, th, lt)
    # 컷 시작·끝 페이드
    if name == 'C1':
        img = img * ease(ramp(th, 0, 1.5))
    if name == 'C12' and lt < 0.6:
        img = img * ease(ramp(lt, 0, 0.6))
    img = film(img, th, H=H, W=W, vig=0.18, grain=0.012, weave=0.35)
    if name == 'CR':
        import credit_overlay
        img = credit_overlay.apply(img, th - 118.0, side='right', bottom=90)
        img = img * (1 - ease(ramp(th, 124.5, 126.0)))
    img = letterbox(img)
    return label(img, th)


def c2_brush(img, th, lt):
    """붓끝(자리표시): 오른쪽 위에서 들어와 구석 위에서 멈추고, 먹이 맺혀 떨어지고, 나간다."""
    view = View(*CAMS['C2'](0), W, H)
    if lt < 0.6:
        pos = (160, 300)
    elif lt < 1.8:
        pos = (160 + (38 - 160) * ease((lt - 0.6) / 1.2), 300 + (392 - 300) * ease((lt - 0.6) / 1.2))
    elif lt < 3.2:
        pos = (38, 392)
    else:
        pos = (38 + 140 * ease(min(1, (lt - 3.2) / 1.6)), 392 - 120 * ease(min(1, (lt - 3.2) / 1.6)))
    px, py = view.to_px(*pos)
    sh = np.zeros((H, W), F32)
    # 붓끝 그림자(위에서 내려다본 붓은 화면 위로 빠져나가는 대)
    cv2.ellipse(sh, (int(px + 6), int(py - 6)), (int(view.ppm * 6), int(view.ppm * 3)), -40, 0, 360, 1.0, -1)
    cv2.line(sh, (int(px + 10), int(py - 10)), (int(px + 400), int(py - 400)), 1.0, int(view.ppm * 3.5))
    sh = cv2.GaussianBlur(sh, (0, 0), 2)
    img = img * (1 - 0.8 * sh[..., None]) + sh[..., None] * np.array((0.04, 0.03, 0.03), F32) * 0.8
    # 맺힌 먹 방울
    if 1.8 <= lt < 3.0:
        r = view.ppm * (1.2 + 1.6 * ramp(lt, 1.8, 2.7))
        cv2.circle(img, (int(px), int(py)), int(r), (0.03, 0.03, 0.04), -1)
        cv2.circle(img, (int(px - r * 0.3), int(py - r * 0.3)), max(1, int(r * 0.25)), (0.6, 0.55, 0.45), -1)
    return img


def run_frames(t0, t1):
    os.makedirs(os.path.join(HERE, 'frames'), exist_ok=True)
    for k in range(int(round(t0 * 12)), int(round(t1 * 12))):
        t = k / 12
        fn = os.path.join(HERE, 'frames', f'g{k:05d}.png')
        if os.path.exists(fn):
            continue
        img = frame(t)
        cv2.imwrite(fn, (np.clip(img, 0, 1)[..., ::-1] * 255 + 0.5).astype(np.uint8))
        if k % 60 == 0:
            print('t', t, flush=True)


def encode():
    import anim_audio
    wav = os.path.join(HERE, 'cache', 'animatic.wav'); anim_audio.build(wav)
    lst = os.path.join(HERE, 'cache', 'frames.txt')
    n = int(TL.TOTAL * 12)
    with open(lst, 'w') as f:
        for k in range(n):
            f.write(f"file '{os.path.join(HERE, 'frames', f'g{k:05d}.png')}'\nduration {1/12}\n")
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'concat', '-safe', '0', '-i', lst, '-i', wav,
                    '-vf', 'fps=24,colorspace=all=bt709:iall=bt709', '-c:v', 'libx264', '-crf', '22', '-pix_fmt', 'yuv420p',
                    '-c:a', 'aac', '-b:a', '192k', '-shortest', os.path.join(HERE, 'cache', 'jeom_animatic_v1.mp4')])


if __name__ == '__main__':
    cmd = sys.argv[1]
    if cmd == 'frames':
        run_frames(float(sys.argv[2]), float(sys.argv[3]))
    elif cmd == 'still':
        for s in sys.argv[2:]:
            img = frame(float(s))
            cv2.imwrite(os.path.join(HERE, 'cache', f'still_{s}.png'), (np.clip(img, 0, 1)[..., ::-1] * 255 + 0.5).astype(np.uint8))
    elif cmd == 'encode':
        encode()
