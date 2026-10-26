"""야식 습격 사건 — 종이 스타일 스프라이트 코어 (저장소 paper_story 코드 복사본 위에서 동작)"""
import sys, os, math, hashlib
sys.path.insert(0, "/home/claude/work/ps")
os.chdir("/home/claude/work/ps")
from paper import *          # puff, chip, put_text, highlight, star, cloud, rr, circ, ... + ink 함수
import chars as CH
from PIL import Image

K = float(os.environ.get("KSC", 2 / 3))   # 설계 좌표 → 렌더 해상도(썸네일은 1.0)
CACHE = "/home/claude/work/cache/"
os.makedirs(CACHE, exist_ok=True)
NAVYC = hx(0x26304F)
PEACH, PINKC, SALMON = hx(0xF9D9C8), hx(0xF6C1C6), hx(0xF59A8E)
WALL_A, WALL_B = hx(0xF3E6D8), hx(0xEBDDE6)
FLOOR = hx(0xE2CDB5)
RED, GOLD, BLUEC, GRAY = hx(0xE9776E), hx(0xF2BE3C), hx(0x7FB2E6), hx(0xB9BCC9)
WOOD, WOOD2 = hx(0xD9A877), hx(0xC48F5E)
CHAR_S = 520
import paper as _paper
_paper.FONTS["geist"] = _paper.FD2 + "Geist-Black.ttf"


def _resize(ch, w, h):
    return np.asarray(Image.fromarray(ch.astype(np.float32), mode="F").resize((w, h), Image.LANCZOS))


def make_sprite(fn, w, h):
    """fn(img)->img. 검정/흰 바탕에 두 번 그려 알파를 얻고, 설계 좌표 위치와 함께 2/3 축소한 RGBA(프리멀티)로 반환"""
    B = fn(np.zeros((h, w, 3), np.float32)); Wt = fn(np.ones((h, w, 3), np.float32))
    a = np.clip(1 - (Wt - B).mean(2), 0, 1)
    ys, xs = np.where(a > 0.004)
    if len(xs) == 0:
        return None
    x0, x1, y0, y1 = max(0, xs.min() - 3), min(w, xs.max() + 4), max(0, ys.min() - 3), min(h, ys.max() + 4)
    x0 -= x0 % 3; y0 -= y0 % 3
    while (x1 - x0) % 3: x1 += 1
    while (y1 - y0) % 3: y1 += 1
    x1 = min(x1, w + 2); y1 = min(y1, h + 2)
    pm = np.concatenate([np.clip(B, 0, 1)[y0:y1, x0:x1], a[y0:y1, x0:x1, None]], 2)
    cw, chh = pm.shape[1], pm.shape[0]
    cw3, ch3 = cw - cw % 3, chh - chh % 3
    pm = pm[:ch3, :cw3]
    if K == 1.0:
        out = pm.copy()
    else:
        out = np.stack([_resize(pm[..., i], cw3 * 2 // 3, ch3 * 2 // 3) for i in range(4)], 2)
    out = np.clip(out, 0, 1); out[..., :3] = np.minimum(out[..., :3], out[..., 3:4])
    return dict(arr=(out * 255 + 0.5).astype(np.uint8), wx=x0, wy=y0, w=cw3, h=ch3, cw=w, ch=h)


_MEM = {}


def sprite(key, w, h, fn):
    """디스크 캐시 + 메모리 캐시. 반환: dict(arr, wx, wy, w, h)"""
    if key in _MEM:
        return _MEM[key]
    safe = hashlib.md5((key + str(round(K, 3))).encode()).hexdigest()[:16] + "_" + "".join(c for c in key if c.isalnum())[:30]
    path = CACHE + safe + ".npz"
    if os.path.exists(path):
        try:
            d = np.load(path)
            _MEM[key] = dict(arr=d["arr"], wx=int(d["wx"]), wy=int(d["wy"]), w=int(d["w"]), h=int(d["h"]), cw=int(d["cw"]), ch=int(d["ch"]))
            return _MEM[key]
        except Exception:
            pass
    s = make_sprite(fn, w, h)
    if s is None:
        _MEM[key] = None
        return None
    tmp = path + ".%d.tmp.npz" % os.getpid()
    np.savez(tmp, **s)
    os.replace(tmp, path)
    _MEM[key] = s
    return s


# ───────── 재료 ─────────
def P_(img, mask, col, seed=0, soft=7, sh=(6, 9), blur=8, k=0.28, depth=1.0):
    return puff(img, mask, col, seed, soft=soft, shadow=sh, sh_blur=blur, sh_k=k, depth=depth)


def flat(img, mask, col, a=1.0):
    return over(img, mask * a, col)


def char_sprite(name, mood, flags=None):
    S = CHAR_S; pad = 70; N = S + pad * 2

    def fn(img):
        return puff_char(img, char_fn(name, mood, **(flags or {})), N / 2, N / 2, S, seed=hash(name) % 97)
    return sprite(f"ch_{name}_{mood}_{sorted((flags or {}).items())}", N, N, fn)


# 캐릭터 발 위치(스프라이트 중심 기준 오프셋, 설계 px): 발 중심선 ≈ 몸 중심 + 138*S/576
def char_feet_off():
    S = CHAR_S
    return (0.62 - 0.5) * S + 138 * S / 576   # y 오프셋(스프라이트 정사각 중심에서 발 아래 끝까지)


def txt_sprite(key, s, size, face="jua", col=None, pad=20, shadow=True):
    col = TXT if col is None else col
    w = int(tw(s, size, face)) + pad * 2 + 20; h = int(size * 1.5) + pad

    def fn(img):
        im, _ = put_text(img, w, h, s, pad + 10, size * 1.05, size, face, col, "l", shadow=shadow)
        return im
    return sprite("tx_" + key, w, h, fn)


def chip_sprite(key, s, size, face, col, rot=0.0, padx=34, pady=18, tcol=None, rad=26):
    tcol = TXT if tcol is None else tcol
    w = int(tw(s, size, face)) + padx * 2 + 90
    h = int(size * 1.0 + pady * 2) + 110 + int(abs(math.sin(math.radians(rot))) * (w * 0.6))
    cx, cy = w / 2, h / 2

    def fn(img):
        im, _, _ = chip(img, w, h, s, cx, cy, size, face, col, hash(s) % 91, rot, padx, pady, tcol, rad)
        return im
    return sprite("chip_" + key, w, h, fn)


def center_off(sp):
    return sp["wx"] + sp["w"] / 2, sp["wy"] + sp["h"] / 2
