"""〈점〉 기술 시험 — 화선지 위 먹 번짐 시뮬레이션.

상태(시뮬레이션 격자, 화면의 1/3 해상도):
  W  물(젖음 0..1+)       — 비선형 확산(다공질 매질): 섬유 전도도 K를 따라 앞전선이 손가락처럼 번진다
  P  물에 떠 있는 먹       — 물 흐름을 따라 이동(상류 농도), 마르면 종이에 붙는다
  D  종이에 붙은 먹        — 다시 젖으면 일부 녹아 나온다(이야기용 허구)
화면(전체 해상도):
  밀도를 키워 올린 뒤 전체 해상도 섬유 무늬로 가장자리를 흔들고, 한지 색에 흡수(Beer-Lambert)로 얹는다.

시뮬레이션은 상태를 가진다. 같은 시드면 같은 결과(결정론적)이므로 프레임별 상태를 순서대로 계산해 캐시한다.
"""
import math, sys, os
import numpy as np, cv2

F32 = np.float32
W_, H_ = 1920, 1080
S = 3                                   # 시뮬레이션 축소 배율
SW, SH = W_ // S, H_ // S               # 640 x 360
FPS = 24


# ---------------------------------------------------------------- 종이
def fbm(w, h, seed, octaves=5, base=6):
    r = np.random.default_rng(seed)
    out = np.zeros((h, w), F32); amp = 1.0; tot = 0
    for o in range(octaves):
        n = base * 2 ** o
        g = r.standard_normal((n * h // w + 2, n + 2)).astype(F32)
        out += amp * cv2.resize(g, (w, h), interpolation=cv2.INTER_CUBIC)
        tot += amp; amp *= 0.55
    out /= tot
    return out / (np.abs(out).max() + 1e-6)


def make_fibers(w, h, seed, n, lmin, lmax, thick=1):
    """한지 섬유: 살짝 휜 짧은 선들. 방향은 대체로 한쪽(초지 방향)으로 기운다."""
    r = np.random.default_rng(seed)
    img = np.zeros((h, w), F32)
    for _ in range(n):
        x, y = r.uniform(-40, w + 40), r.uniform(-40, h + 40)
        a = r.normal(0.35, 0.9)
        L = r.uniform(lmin, lmax)
        bend = r.normal(0, 0.012)
        pts = []
        for k in range(9):
            s = (k / 8 - 0.5) * L
            aa = a + bend * s
            pts.append((x + math.cos(aa) * s, y + math.sin(aa) * s))
        pts = np.array(pts, np.float32)
        v = float(r.uniform(0.35, 1.0))
        cv2.polylines(img, [np.round(pts * 4).astype(np.int32)], False, v, thick, cv2.LINE_AA, shift=2)
    return img


class Paper:
    def __init__(self, seed=11):
        # 전체 해상도 섬유(화면용)
        self.fib = make_fibers(W_, H_, seed, 9000, 25, 140)
        self.fib = cv2.GaussianBlur(self.fib, (0, 0), 0.6)
        self.flecks = make_fibers(W_, H_, seed + 1, 260, 3, 14, 2)        # 닥나무 껍질 티
        self.mottle = fbm(W_, H_, seed + 2, 5, 3)
        # 시뮬레이션용 전도도: 섬유가 촘촘한 곳일수록 물이 잘 스민다
        fs = cv2.resize(cv2.GaussianBlur(self.fib, (0, 0), 1.2), (SW, SH), interpolation=cv2.INTER_AREA)
        fs = fs / (fs.max() + 1e-6)
        nz = fbm(SW, SH, seed + 3, 4, 5)
        self.K = np.clip(0.05 + 0.17 * fs + 0.04 * nz, 0.02, 0.24).astype(F32)


# ---------------------------------------------------------------- 시뮬레이션
class Ink:
    def __init__(self, paper):
        self.p = paper
        self.W = np.zeros((SH, SW), F32)
        self.P = np.zeros((SH, SW), F32)
        self.D = np.zeros((SH, SW), F32)
        self.evap = 0.0006
        self.bias = np.zeros(2, F32)          # 번짐 방향 편향(연기)
        self.Kx = (0.5 * (paper.K[:, 1:] + paper.K[:, :-1])).astype(F32)
        self.Ky = (0.5 * (paper.K[1:, :] + paper.K[:-1, :])).astype(F32)

    def drop(self, cx, cy, r, water, ink):
        """화면 좌표(px)에 방울을 떨군다."""
        yy, xx = np.mgrid[0:SH, 0:SW].astype(F32)
        d2 = ((xx - cx / S) ** 2 + (yy - cy / S) ** 2) / (r / S) ** 2
        m = np.exp(-d2 * 2.2).astype(F32)
        self.W += water * m
        self.P += ink * m

    def step(self):
        W, P, D = self.W, self.P, self.D
        # 비선형 확산 계수(앞전선을 날카롭게)
        Wf = np.clip(W, 0, 1.5)
        # x 방향 면
        wl, wr = Wf[:, :-1], Wf[:, 1:]
        mob = (0.5 * (wl + wr)) ** 1.6
        fx = self.Kx * mob * (wl - wr)
        # 편향: 앞전선(얇은 물)에서만 한쪽으로 조금 더 흐름
        if self.bias[0] != 0:
            front = np.clip(1 - 2 * (0.5 * (wl + wr)), 0, 1) * (np.maximum(wl, wr) > 0.02)
            fx += self.Kx * 0.05 * self.bias[0] * front * np.maximum(wl, wr)
        wu, wd = Wf[:-1, :], Wf[1:, :]
        mob = (0.5 * (wu + wd)) ** 1.6
        fy = self.Ky * mob * (wu - wd)
        if self.bias[1] != 0:
            front = np.clip(1 - 2 * (0.5 * (wu + wd)), 0, 1) * (np.maximum(wu, wd) > 0.02)
            fy += self.Ky * 0.05 * self.bias[1] * front * np.maximum(wu, wd)
        # 먹은 상류의 농도로 실려 간다
        c = P / (W + 1e-4)
        c = np.clip(c, 0, 6)
        px = np.where(fx > 0, c[:, :-1], c[:, 1:]) * fx
        py = np.where(fy > 0, c[:-1, :], c[1:, :]) * fy
        dW = np.zeros_like(W); dP = np.zeros_like(P)
        dW[:, :-1] -= fx; dW[:, 1:] += fx
        dW[:-1, :] -= fy; dW[1:, :] += fy
        dP[:, :-1] -= px; dP[:, 1:] += px
        dP[:-1, :] -= py; dP[1:, :] += py
        W += dW; P += dP
        # 마름: 얇은 곳(가장자리)이 먼저 마른다 → 가장자리로 먹이 몰려 붙는다
        thin = np.clip(1 - W * 3, 0, 1)
        W -= self.evap * (0.6 + 1.4 * thin)
        np.maximum(W, 0, out=W)
        dry = np.clip(1 - W * 6, 0, 1)
        dep = P * (0.0008 + 0.02 * dry ** 2)
        P -= dep; D += dep
        # 다시 젖으면 붙은 먹이 조금 녹아 나온다
        wet = np.clip(W * 2 - 0.3, 0, 1)
        lift = D * 0.0009 * wet
        D -= lift; P += lift

    def density(self):
        return self.D + 0.9 * self.P

    def advect(self, target, speed, water_frac=0.6, dt=1.0):
        """의도(연기): 젖은 곳 안에서만 먹이 목표 쪽으로 흐른다. 마른 종이 위로는 못 간다.
        target: 화면 좌표, speed: 프레임당 화면 px."""
        if speed <= 0:
            return
        yy, xx = np.mgrid[0:SH, 0:SW].astype(F32)
        dx = target[0] / S - xx; dy = target[1] / S - yy
        n = np.sqrt(dx * dx + dy * dy) + 3.0
        wet = np.clip((cv2.GaussianBlur(self.W, (0, 0), 1.5) - 0.02) / 0.12, 0, 1)
        sp = speed / S * dt
        u = dx / n * sp * wet; v = dy / n * sp * wet
        mx = (xx - u).astype(F32); my = (yy - v).astype(F32)
        self.P = cv2.remap(self.P, mx, my, cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT)
        Wa = cv2.remap(self.W, mx, my, cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT)
        self.W = (1 - water_frac) * self.W + water_frac * Wa

    def gather(self, center, scale, mask_r):
        """규칙 깨기: 반경 mask_r 안의 먹(붙은 것 포함)을 center 쪽으로 scale배로 오그린다. 질량 보존."""
        cx, cy = center[0] / S, center[1] / S
        tot = self.D + self.P
        yy, xx = np.mgrid[0:SH, 0:SW].astype(F32)
        r = np.sqrt((xx - cx) ** 2 + (yy - cy) ** 2)
        body = tot * np.clip((mask_r / S - r) / (mask_r / S * 0.25), 0, 1)
        trail = tot - body
        mx = (cx + (xx - cx) / scale).astype(F32); my = (cy + (yy - cy) / scale).astype(F32)
        nb = cv2.remap(body, mx, my, cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT) / (scale * scale)
        self.D = trail + nb; self.P[:] = 0


# ---------------------------------------------------------------- 마른 붓 획(용의 몸, 움직이지 않음)
def dry_stroke(pts, width, seed, density=2.2):
    """굵은 붓 한 획: 중심선 + 붓털 줄무늬(비백) + 끝으로 갈수록 갈라짐. 전체 해상도 밀도."""
    r = np.random.default_rng(seed)
    img = np.zeros((H_, W_), F32)
    pts = np.array(pts, F32)
    # 촘촘히 재샘플
    seg = np.linalg.norm(np.diff(pts, axis=0), axis=1)
    s = np.concatenate([[0], np.cumsum(seg)]); L = s[-1]
    t = np.linspace(0, L, int(L / 1.5))
    xs = np.interp(t, s, pts[:, 0]); ys = np.interp(t, s, pts[:, 1])
    tx = np.gradient(xs); ty = np.gradient(ys); nn = np.hypot(tx, ty) + 1e-6
    nx, ny = -ty / nn, tx / nn
    nb = 70
    offs = r.uniform(-0.5, 0.5, nb)
    ink0 = r.uniform(0.6, 1.0, nb)
    dry_at = r.uniform(0.55, 1.15, nb)           # 붓털마다 먹이 떨어지는 지점
    for b in range(nb):
        u = t / L
        press = np.sin(np.clip(u, 0, 1) * math.pi) ** 0.5 * 0.85 + 0.15
        wv = width * press
        bx = xs + nx * offs[b] * wv; by = ys + ny * offs[b] * wv
        amt = ink0[b] * np.clip((dry_at[b] - u) / 0.15, 0, 1)
        for i in range(0, len(t) - 1, 2):
            if amt[i] < 0.05:
                continue
            cv2.line(img, (int(bx[i] * 4), int(by[i] * 4)), (int(bx[i + 2 if i + 2 < len(t) else i + 1] * 4),
                     int(by[i + 2 if i + 2 < len(t) else i + 1] * 4)), float(amt[i]), 3, cv2.LINE_AA, shift=2)
    img = cv2.GaussianBlur(img, (0, 0), 0.9)
    return np.clip(img, 0, 1.3) * density


# ---------------------------------------------------------------- 화면
INK_ABS = np.array((1.0, 1.02, 1.07), F32) * 1.9      # 묽으면 살짝 차가운 회색, 진하면 검정


def render(paper, dens_sim, wet_sim, extra_dens=None, grade='day', t=0.0):
    up = cv2.resize(dens_sim, (W_, H_), interpolation=cv2.INTER_CUBIC)
    up = np.maximum(up, 0)
    wet = cv2.resize(wet_sim, (W_, H_), interpolation=cv2.INTER_LINEAR)
    # 가장자리 섬유 디테일: 밀도 기울기가 큰 곳에서 섬유 무늬로 경계를 흔든다
    # 섬유가 가장자리 밖으로 먹을 끌고 나가는 솜털 번짐(안쪽에는 섬유 줄을 긋지 않는다)
    halo = cv2.GaussianBlur(up, (0, 0), 7)
    feather = np.clip(halo - up, 0, None) * paper.fib * 1.6
    d = up * (1 + 0.05 * paper.mottle) + feather
    d = np.maximum(d, 0)
    if extra_dens is not None:
        d = d + extra_dens * (0.85 + 0.3 * paper.fib[..., ])
    # 한지
    base = np.array((0.925, 0.895, 0.825), F32)
    paper_rgb = base[None, None, :] * (1 + 0.025 * paper.mottle[..., None]) \
        + 0.035 * paper.fib[..., None] * np.array((1, 1, 0.95), F32) \
        - 0.10 * paper.flecks[..., None] * np.array((0.6, 0.75, 0.9), F32)
    # 젖은 종이는 조금 어둡고 투명해진다
    paper_rgb = paper_rgb * (1 - 0.07 * np.clip(wet * 2, 0, 1)[..., None])
    img = paper_rgb * np.exp(-d[..., None] * INK_ABS[None, None, :])
    if grade == 'night':
        img = img * np.array((0.42, 0.50, 0.68), F32) + np.array((0.0, 0.01, 0.03), F32)
    # 비네트 + 그레인
    yy, xx = np.mgrid[0:H_, 0:W_].astype(F32)
    v = 1 - 0.22 * (((xx - W_ / 2) / (W_ / 2)) ** 2 + ((yy - H_ / 2) / (H_ / 2)) ** 2)
    img = img * v[..., None]
    rg = np.random.default_rng(int(math.floor(t * 12)) * 7 + 3)
    gr = rg.standard_normal((H_ // 2, W_ // 2)).astype(F32)
    gr = cv2.resize(gr, (W_, H_), interpolation=cv2.INTER_LINEAR)
    img = img + 0.012 * gr[..., None]
    return np.clip(img, 0, 1)


def save(img, path):
    cv2.imwrite(path, (np.clip(img, 0, 1)[..., ::-1] * 255 + 0.5).astype(np.uint8))
