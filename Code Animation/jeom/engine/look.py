"""종이 + 먹 합성, 조명, 필름 마감."""
import math
import numpy as np, cv2
from paper import paper_rgb

F32 = np.float32
INK_ABS = np.array((1.0, 1.02, 1.07), F32) * 1.9     # 묽으면 살짝 차가운 회색, 진하면 검정


def ink_on_paper(fib, flk, mot, dens, wet=None):
    pap = paper_rgb(fib, flk, mot)
    if wet is not None:
        wv = np.clip(wet, 0, 1)[..., None]
        pap = pap * (1 - 0.06 * wv) + 0.03 * wv * fib[..., None]
    # 진한 먹일수록 종이 결이 덜 비친다(먹이 섬유를 덮음)
    d = dens * (1 + 0.06 * mot)
    return pap * np.exp(-d[..., None] * INK_ABS)


def light(img, mode, t=0.0, extra=None):
    """mode: 'lamp' 등잔 호박색, 'night' 창의 푸른빛, 'flash' 번개(0..1 = extra), 'silver' 비 그친 은빛, 'morning'."""
    if mode == 'lamp':
        img = img * np.array((1.02, 0.86, 0.62), F32) * 0.92
    elif mode == 'night':
        img = img * np.array((0.42, 0.50, 0.66), F32) + np.array((0.005, 0.01, 0.025), F32)
    elif mode == 'silver':
        img = img * np.array((0.55, 0.60, 0.70), F32) + np.array((0.01, 0.012, 0.02), F32)
    elif mode == 'morning':
        img = img * np.array((1.04, 0.98, 0.88), F32)
    if extra is not None and mode in ('night', 'silver'):
        f = float(extra)          # 번개 세기 0..1, 상한 0.7(화면을 날리지 않음)
        base = img
        img = base * (1 - 0.7 * f) + (base / np.array((0.42, 0.50, 0.66), F32)) * np.array((0.80, 0.86, 0.98), F32) * 0.7 * f
    return img


def film(img, t, H=1080, W=1920, vig=0.20, grain=0.011, weave=0.5):
    yy, xx = np.mgrid[0:H, 0:W].astype(F32)
    v = 1 - vig * (((xx - W / 2) / (W / 2)) ** 2 + ((yy - H / 2) / (H / 2)) ** 2)
    img = img * v[..., None]
    k = int(math.floor(t * 12))
    rg = np.random.default_rng(k * 7 + 3)
    gr = cv2.resize(rg.standard_normal((H // 2, W // 2)).astype(F32), (W, H))
    img = img + grain * gr[..., None]
    img = 0.03 + img * 0.97                                   # 들뜬 검정
    r2 = np.random.default_rng(k * 31 + 5)
    M = np.float32([[1, 0, r2.normal(0, weave)], [0, 1, r2.normal(0, weave * 0.7)]])
    img = cv2.warpAffine(img, M, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
    return np.clip(img, 0, 1)


def letterbox(img, ratio=1.85):
    H, W = img.shape[:2]
    h = int(round(W / ratio)); b = (H - h) // 2
    img = img.copy(); img[:b] = 0; img[H - b:] = 0
    return img


def save(img, path):
    cv2.imwrite(path, (np.clip(img, 0, 1)[..., ::-1] * 255 + 0.5).astype(np.uint8))
