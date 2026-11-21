"""종이 오림 합성: 층(level)마다 cairo로 색 조각을 그리고, numpy로 한지 결·두께(가장자리 빛)·그림자를 입힌다.
좌표는 디자인 픽셀(가로 1920×1080 / 세로 HD_ORIENT=v 1080×1920), 출력 배율 HD_SCALE.
"""
import os, math
import numpy as np, cv2, cairo

SC = float(os.environ.get('HD_SCALE', '1'))
VERT = os.environ.get('HD_ORIENT', 'h') == 'v'          # v: 세로 숏폼(1080×1920 디자인 픽셀)
DW_, DH_ = (1080, 1920) if VERT else (1920, 1080)
W, H = int(round(DW_ * SC)), int(round(DH_ * SC))
HERE = os.path.dirname(os.path.abspath(__file__))
CACHE = os.path.join(HERE, 'cache'); os.makedirs(CACHE, exist_ok=True)


def hexc(h):
    h = h.lstrip('#'); return tuple(int(h[i:i + 2], 16) / 255 for i in (0, 2, 4))


# ---------------------------------------------------------------- 한지 결(한 번 만들어 둠)
def paper_tex():
    p = os.path.join(CACHE, f'paper_{W}x{H}.npy')
    if os.path.exists(p): return np.load(p)
    rng = np.random.default_rng(11)
    T = np.zeros((H, W), np.float32)
    # 큰 얼룩(뜬 종이의 고르지 않은 두께)
    for s, a in [(260, 0.014), (70, 0.010), (18, 0.008)]:     # 얼룩은 옅게 — 결은 섬유가 만든다
        n = rng.standard_normal((H // s + 3, W // s + 3)).astype(np.float32)
        T += a * cv2.resize(n, (W, H), interpolation=cv2.INTER_CUBIC)
    # 섬유: 휘어진 가는 선(밝은 것·어두운 것)
    fib = np.zeros((H * 2, W * 2), np.float32)
    for k in range(int(5200 * SC * SC)):
        x, y = rng.uniform(0, W * 2), rng.uniform(0, H * 2)
        L = rng.uniform(30, 140) * SC; a0 = rng.uniform(0, math.pi); bend = rng.normal(0, 0.6)
        pts = []
        for j in range(9):
            u = j / 8; a = a0 + bend * (u - 0.5)
            pts.append((x + math.cos(a) * L * (u - 0.5) * 2, y + math.sin(a) * L * (u - 0.5) * 2))
        cv2.polylines(fib, [np.int32(pts)], False, float(rng.choice([1, -0.7])), 1, cv2.LINE_AA)
    fib = cv2.resize(fib, (W, H), interpolation=cv2.INTER_AREA)
    T += 0.065 * fib
    T += 0.008 * rng.standard_normal((H, W)).astype(np.float32)
    T = 1.0 + T
    np.save(p, T.astype(np.float32))
    return T


TEX = None
def tex():
    global TEX
    if TEX is None: TEX = paper_tex()
    return TEX


# ---------------------------------------------------------------- 층
class Level:
    """한 깊이의 종이 조각들. depth: 바닥 종이에서 떠 있는 높이(그림자 거리·흐림)."""
    def __init__(self, depth=1.0, shadow=0.34, edge=1.0):
        self.depth, self.shadow, self.edge = depth, shadow, edge
        self.surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H)
        self.cr = cairo.Context(self.surf)
        self.cr.scale(SC, SC)

    def array(self):
        self.surf.flush()
        a = np.ndarray((H, W, 4), np.uint8, self.surf.get_data(), strides=(self.surf.get_stride(), 4, 1))
        return a.astype(np.float32) / 255.0        # BGRA, premultiplied


def _shift(img, dx, dy):
    M = np.float32([[1, 0, dx], [0, 1, dy]])
    return cv2.warpAffine(img, M, (img.shape[1], img.shape[0]), borderMode=cv2.BORDER_CONSTANT)


def composite(base, rgba, depth, shadow=0.34, edge=1.0, light=(-0.6, -0.8)):
    """base(BGR, 0..1) 위에 한 층(premultiplied BGRA)을 종이로 얹는다."""
    a = rgba[..., 3]
    if a.max() < 1e-4: return base
    # 그림자: 반 해상도에서 흐리고 빛 반대쪽으로 민다
    if shadow > 0 and depth > 0:
        h2 = cv2.resize(a, (W // 2, H // 2), interpolation=cv2.INTER_AREA)
        s = cv2.GaussianBlur(h2, (0, 0), (2.0 + 5.0 * depth) * SC)
        s = _shift(s, -light[0] * (3 + 7 * depth) * SC / 2, -light[1] * (3 + 7 * depth) * SC / 2)
        s = cv2.resize(s, (W, H), interpolation=cv2.INTER_LINEAR)
        base = base * (1 - shadow * s[..., None])
    # 조각 색(premultiplied → 원색) × 한지 결
    col = rgba[..., :3] / np.maximum(a[..., None], 1e-4)
    col = col * tex()[..., None]
    # 두께: 빛 쪽 가장자리는 밝게, 반대쪽은 어둡게(살짝)
    if edge > 0:
        e = cv2.GaussianBlur(a, (0, 0), 1.3 * SC)
        d = _shift(e, light[0] * 2 * SC, light[1] * 2 * SC) - e     # 빛 쪽 가장자리에서 음수
        col = col + edge * (np.clip(-d, 0, 1)[..., None] * 0.22 - np.clip(d, 0, 1)[..., None] * 0.18)
    return base * (1 - a[..., None]) + np.clip(col, 0, 1.2) * a[..., None]


def groove(base, mask, depth=1.0, light=(-0.6, -0.8)):
    """칼로 그은 홈(바닥 종이에 새김): 어두운 선 + 빛 쪽 비낀 밝은 선."""
    m = cv2.GaussianBlur(mask, (0, 0), 0.7 * SC)
    hi = _shift(m, -light[0] * 1.6 * SC, -light[1] * 1.6 * SC)
    base = base * (1 - 0.45 * m[..., None])
    return np.clip(base + 0.10 * np.clip(hi - m, 0, 1)[..., None], 0, 1)


def grain(img, k, amt=0.01):
    rng = np.random.default_rng(k * 7 + 3)
    n = rng.standard_normal((H // 2 + 1, W // 2 + 1)).astype(np.float32)
    n = cv2.resize(n, (W, H), interpolation=cv2.INTER_NEAREST)
    return np.clip(img + amt * n[..., None], 0, 1)
