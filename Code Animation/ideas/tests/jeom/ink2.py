"""〈점〉 기술 시험 v2 — 연출 가능한 먹 번짐.

물의 앞전선은 '섬유를 따라 걸리는 시간'(측지 도착 시간, 섬유가 촘촘할수록 빠름)으로 미리 계산하고,
앞전선 반지름을 시간 키로 준다 → 손가락처럼 갈라진 경계 + 연출이 정한 타이밍.
먹(P, 물에 뜬 것)은 젖은 곳 안에서만 퍼지고(확산) 흐른다(의도 = 목표점 쪽 흐름).
마르면 붙고(D), 가장자리가 먼저 말라 테두리가 진해진다. 다시 젖으면 붙은 먹 일부가 녹아 나온다.
"""
import math
import numpy as np, cv2
from skimage.graph import MCP_Geometric
from ink import fbm, make_fibers, save

F32 = np.float32
W_, H_ = 1920, 1080
S = 2
SW, SH = W_ // S, H_ // S


def sstep(x, a, b):
    t = np.clip((x - a) / (b - a), 0, 1)
    return t * t * (3 - 2 * t)


class Paper:
    def __init__(self, seed=11):
        self.fib = cv2.GaussianBlur(make_fibers(W_, H_, seed, 9000, 25, 140), (0, 0), 0.6)
        self.flecks = make_fibers(W_, H_, seed + 1, 260, 3, 14, 2)
        self.mottle = fbm(W_, H_, seed + 2, 5, 3)
        fs = cv2.resize(cv2.GaussianBlur(self.fib, (0, 0), 1.0), (SW, SH), interpolation=cv2.INTER_AREA)
        fs = fs / (fs.max() + 1e-6)
        nz = fbm(SW, SH, seed + 3, 4, 7)
        speed = np.clip(0.35 + 1.1 * fs + 0.35 * nz, 0.12, 2.0)
        self.cost = (1.0 / speed).astype(F32)      # 섬유가 없는 곳은 물이 늦게 닿는다
        self._T = {}

    def arrival(self, cx, cy):
        key = (int(cx), int(cy))
        if key not in self._T:
            m = MCP_Geometric(self.cost)
            T, _ = m.find_costs([(int(cy / S), int(cx / S))])
            self._T[key] = (T * S / float(np.median(self.cost))).astype(F32)     # 화면 px 단위(중앙 속도 1)
        return self._T[key]


class Drop:
    """t0에 (cx,cy)에 떨어진 방울. 앞전선은 R(t)=Rmax*(1-exp(-(t-t0)/tau)).
    ink>0이면 먹 방울(중심에 먹을 싣고 온다)."""
    def __init__(self, t0, cx, cy, Rmax, tau=0.5, ink=0.0, ink_r=None, dry=None):
        self.t0, self.cx, self.cy, self.Rmax, self.tau = t0, cx, cy, Rmax, tau
        self.dry = dry
        self.ink = ink; self.ink_r = ink_r or Rmax * 0.55
        self.added = False

    def R(self, t):
        if t < self.t0:
            return -1
        return self.Rmax * (1 - math.exp(-(t - self.t0) / self.tau))


class Ink:
    def __init__(self, paper, drops, dry_curve, target_curve=None, specks=()):
        """dry_curve(t) -> 0..1 (1 = 완전히 마름). target_curve(t) -> (x, y, speed px/s) 또는 None."""
        self.p = paper
        self.drops = drops
        self.dry_curve = dry_curve
        self.target_curve = target_curve
        self.P = np.zeros((SH, SW), F32)
        self.D = np.zeros((SH, SW), F32)
        self.m = np.zeros((SH, SW), F32)      # 젖음 0..1
        self.t = 0.0
        yy, xx = np.mgrid[0:SH, 0:SW].astype(F32)
        self.xx, self.yy = xx, yy
        for (sx, sy, sr, amt) in specks:       # 그림 그릴 때 튄, 이미 마른 먹
            d2 = ((xx - sx / S) ** 2 + (yy - sy / S) ** 2) / (sr / S) ** 2
            self.D += amt * np.exp(-d2 * 2.5) * (1 + 0.3 * np.cos(np.arctan2(yy - sy / S, xx - sx / S) * 3))

    def wet(self, t):
        m = np.zeros((SH, SW), F32)
        for d in self.drops:
            R = d.R(t)
            if R <= 0:
                continue
            T = self.p.arrival(d.cx, d.cy)
            mi = sstep(R - T, -2.0, 6.0) * sstep(R - T, -2.0, 30.0) ** 0.3
            if d.dry is not None:
                dd = d.dry(t)
                if dd > 0:
                    mi = np.clip((mi - dd) / max(1e-3, 1 - dd), 0, 1)
            m = np.maximum(m, mi)
        dry = self.dry_curve(t)
        if dry > 0:
            # 가장자리(앞전선 근처)부터 마른다: 젖음 값을 깎아 문턱 아래로
            m = np.clip((m - dry) / max(1e-3, 1 - dry), 0, 1) * (1 - dry * 0.3)
        return m

    def advance(self, t, sub=8):
        dt = t - self.t
        mnew = self.wet(t)
        # 새 먹 방울
        for d in self.drops:
            if d.ink > 0 and t >= d.t0 and t - d.t0 < 4 * d.tau:
                T = self.p.arrival(d.cx, d.cy)
                Ri = d.R(t) * d.ink_r / d.Rmax
                fill = d.ink * sstep(Ri - T, -1.5, 4.0) * (1 - 0.25 * sstep(T, 0, Ri + 1e-3))
                self.P = np.maximum(self.P, fill.astype(F32))
        m = mnew
        # 마른 곳: 먹이 붙는다. 방금 마른 곳(m이 줄어든 곳)은 많이 붙어 테두리가 진해진다
        drying = np.clip(self.m - m, 0, 1)
        dep = self.P * np.clip(1 - m / 0.22, 0, 1) + self.P * drying * 1.2 + self.P * 0.006 * m
        dep = np.minimum(dep, self.P)
        self.P -= dep; self.D += dep
        # 다시 젖은 곳: 붙은 먹 일부가 녹는다
        rewet = np.clip(m - self.m, 0, 1)
        lift = self.D * (0.06 * rewet + 0.012 * m)
        self.D -= lift; self.P += lift
        # 젖은 곳 안에서만 확산(면 젖음의 최솟값으로 흐름 제한)
        mx = np.minimum(m[:, 1:], m[:, :-1]); my = np.minimum(m[1:, :], m[:-1, :])
        for _ in range(sub):
            P = self.P
            fx = 0.22 * mx * (P[:, :-1] - P[:, 1:])
            fy = 0.22 * my * (P[:-1, :] - P[1:, :])
            P[:, :-1] -= fx; P[:, 1:] += fx
            P[:-1, :] -= fy; P[1:, :] += fy
        # 의도: 목표 쪽 흐름(젖은 곳 안에서만)
        if self.target_curve is not None:
            tc = self.target_curve(t)
            if tc is not None and tc[2] > 0:
                tx, ty, spd = tc
                P = self.P
                tot = P.sum() + 1e-6
                gx = float((P * self.xx).sum() / tot); gy = float((P * self.yy).sum() / tot)
                dx, dy = tx / S - gx, ty / S - gy
                L = math.hypot(dx, dy) + 1e-6
                ux, uy = dx / L, dy / L
                slow = min(1.0, L * S / 60.0)               # 목표 근처에서 느려짐
                w = cv2.GaussianBlur(m, (0, 0), 1.0)
                # 앞쪽(목표 방향)일수록 빨리: 뻗는 앞머리, 따라오는 꼬리
                proj = (self.xx - gx) * ux + (self.yy - gy) * uy
                front = np.clip(0.35 + proj / 40.0, 0.15, 1.6)
                sp = spd * dt / S * slow
                u = ux * sp * w * front; v = uy * sp * w * front
                self.P = cv2.remap(self.P, (self.xx - u).astype(F32), (self.yy - v).astype(F32),
                                   cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT)
        self.m = m
        self.t = t

    def gather(self, center, scale, body_r):
        """규칙 깨기: center 반경 body_r 안의 먹을 scale배로 오그린다(질량 보존). 지나온 자국은 남긴다."""
        cx, cy = center[0] / S, center[1] / S
        tot = self.D + self.P
        r = np.sqrt((self.xx - cx) ** 2 + (self.yy - cy) ** 2)
        wbody = np.clip((body_r / S - r) / (body_r / S * 0.3), 0, 1)
        body = tot * wbody
        trail = tot - body
        mx = (cx + (self.xx - cx) / scale).astype(F32); my = (cy + (self.yy - cy) / scale).astype(F32)
        nb = cv2.remap(body, mx, my, cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT) / (scale * scale)
        # 끌려간 자리에는 아주 옅은 흔적(섬유 사이에 남은 먹)
        self.D = trail + body * 0.06 + nb * 0.94
        self.P[:] = 0

    def density(self):
        return self.D + 0.85 * self.P


INK_ABS = np.array((1.0, 1.02, 1.07), F32) * 1.9


def render(paper, ink_state, extra=None, grade='day', t=0.0, beads=()):
    dens, m = ink_state
    up = np.maximum(cv2.resize(dens, (W_, H_), interpolation=cv2.INTER_CUBIC), 0)
    wet = cv2.resize(m, (W_, H_), interpolation=cv2.INTER_LINEAR)
    halo = cv2.GaussianBlur(up, (0, 0), 6)
    feather = np.clip(halo - up, 0, 0.6) * paper.fib * 1.5
    d = up * (1 + 0.05 * paper.mottle) + feather
    if extra is not None:
        d = d + extra
    base = np.array((0.925, 0.895, 0.825), F32)
    pap = base * (1 + 0.025 * paper.mottle[..., None]) \
        + 0.035 * paper.fib[..., None] * np.array((1, 1, 0.95), F32) \
        - 0.10 * paper.flecks[..., None] * np.array((0.6, 0.75, 0.9), F32)
    # 젖은 한지: 어둡고 살짝 차갑고, 섬유가 더 비친다
    wv = np.clip(wet, 0, 1)[..., None]
    pap = pap * (1 - 0.06 * wv) * np.array((0.985, 0.995, 1.01), F32) ** wv \
        + 0.03 * wv * paper.fib[..., None]
    # 젖은 경계선: 물이 멈춘 자리의 옅은 선
    we = np.abs(cv2.Laplacian(cv2.GaussianBlur(wet, (0, 0), 1.2), cv2.CV_32F))
    pap = pap * (1 - np.clip(we * 2.5, 0, 0.06)[..., None])
    img = pap * np.exp(-d[..., None] * INK_ABS)
    for (bx, by, br, alpha) in beads:          # 떨어지는 순간의 물방울(볼록한 렌즈)
        yy, xx = np.mgrid[0:H_, 0:W_].astype(F32)
        rr = np.sqrt((xx - bx) ** 2 + (yy - by) ** 2) / br
        inside = np.clip(1 - rr, 0, 1)
        shade = np.clip(1 - rr, 0, 1) ** 0.5
        hl = np.exp(-(((xx - bx + br * 0.35) ** 2 + (yy - by + br * 0.35) ** 2) / (br * 0.18) ** 2))
        a = (inside > 0) * alpha
        img = img * (1 - a[..., None] * 0.15 * (1 - shade[..., None])) + a[..., None] * hl[..., None] * 0.55
        ring = np.exp(-((rr - 1) / 0.06) ** 2) * alpha
        img = img * (1 - 0.18 * ring[..., None])
    if grade == 'night':
        img = img * np.array((0.40, 0.48, 0.66), F32) + np.array((0.0, 0.008, 0.025), F32)
    yy, xx = np.mgrid[0:H_, 0:W_].astype(F32)
    v = 1 - 0.20 * (((xx - W_ / 2) / (W_ / 2)) ** 2 + ((yy - H_ / 2) / (H_ / 2)) ** 2)
    img = img * v[..., None]
    rg = np.random.default_rng(int(math.floor(t * 12)) * 7 + 3)
    gr = cv2.resize(rg.standard_normal((H_ // 2, W_ // 2)).astype(F32), (W_, H_))
    img = img + 0.011 * gr[..., None]
    # 게이트 흔들림(투스)
    r2 = np.random.default_rng(int(math.floor(t * 12)) * 31 + 5)
    M = np.float32([[1, 0, r2.normal(0, 0.5)], [0, 1, r2.normal(0, 0.35)]])
    img = cv2.warpAffine(img, M, (W_, H_), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
    return np.clip(img, 0, 1)
