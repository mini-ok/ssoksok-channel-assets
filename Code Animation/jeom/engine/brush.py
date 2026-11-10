"""붓 획 v2 (mm 좌표). 획을 '획 좌표'(s = 획 따라 길이, v = 폭 방향 -1..1)로 펴서,
붓털 다발의 먹 양 표(s × v)를 만들어 화면에 되찍는다.

- 붓털은 폭 방향 bin 64개. 이웃끼리 상관된 먹 양(뭉침) → 젖은 동안은 서로 번져 한 덩어리로 보이고,
  먹이 떨어지면(바깥 털부터) 흰 결(비백)이 길게 생긴다. 빗살처럼 고르게 끊기지 않는다.
- 시작: 눌러 찍은 둥근 머리(press) 또는 뾰족하게 들어옴(point). 끝: 가늘게 빠짐(taper) 또는 갈라져 날림(fly).
- 젖은 획은 종이 섬유를 따라 가장자리가 번진다(합성 단계에서 fib 층으로).
"""
import math
import numpy as np, cv2
from scipy.spatial import cKDTree

F32 = np.float32
NB = 64


def catmull(pts, per=40):
    P = np.array(pts, float)
    if len(P) == 2:
        t = np.linspace(0, 1, per)[:, None]
        return P[0] * (1 - t) + P[1] * t
    P = np.vstack([2 * P[0] - P[1], P, 2 * P[-1] - P[-2]])
    out = []
    for i in range(1, len(P) - 2):
        p0, p1, p2, p3 = P[i - 1], P[i], P[i + 1], P[i + 2]
        for u in np.linspace(0, 1, per, endpoint=False):
            u2, u3 = u * u, u ** 3
            out.append(0.5 * (2 * p1 + (-p0 + p2) * u + (2 * p0 - 5 * p1 + 4 * p2 - p3) * u2 + (-p0 + 3 * p1 - 3 * p2 + p3) * u3))
    out.append(P[-2])
    return np.array(out)


def smooth_noise(n, seed, corr):
    r = np.random.default_rng(seed)
    a = r.standard_normal(n + 4 * corr)
    k = np.exp(-np.linspace(-2, 2, 4 * corr + 1) ** 2)
    a = np.convolve(a, k / k.sum(), 'same')[2 * corr:2 * corr + n]
    return a / (a.std() + 1e-9)


class Stroke:
    def __init__(self, pts, width, load=1.0, dry=0.5, seed=0, head='press', tail='taper',
                 press=None, wet=0.3, name=''):
        """pts: mm 좌표 제어점, width: 최대 폭 mm, load: 먹 진하기(농묵 1, 담묵 0.3),
        dry: 0(흥건) ~ 1(바싹 마른 붓), press: u→압력 함수(없으면 기본), wet: 가장자리 번짐 정도."""
        self.c = catmull(pts, 60)
        seg = np.linalg.norm(np.diff(self.c, axis=0), axis=1)
        self.s = np.concatenate([[0], np.cumsum(seg)]); self.L = float(self.s[-1])
        self.width, self.load, self.dry, self.seed = width, load, dry, seed
        self.head, self.tail, self.wet, self.name = head, tail, wet, name
        self.press = press
        r = np.random.default_rng(seed)
        # 붓털별 먹 양(뭉침), 마르는 지점(바깥부터)
        v = np.linspace(-1, 1, NB)
        clump = 0.6 * smooth_noise(NB, seed + 1, 2) + 0.4 * smooth_noise(NB, seed + 11, 6)
        self.bload = np.clip(0.85 + 0.2 * clump, 0.3, 1.25)
        jitter = smooth_noise(NB, seed + 2, 2) * 0.12
        self.dry_at = (1.25 - dry * 0.75) - np.abs(v) ** 1.6 * (0.25 + 0.55 * dry) + jitter
        self.v = v

    def pressure(self, u):
        if self.press is not None:
            return self.press(u)
        # 눌러 시작 → 조금 들림 → 끝으로 빠짐
        p = np.ones_like(u)
        if self.head == 'press':
            p *= np.where(u < 0.06, 0.75 + 0.25 * np.sqrt(np.clip(u / 0.06, 0, 1)) + 0.1 * (1 - u / 0.06), 1)
        else:
            p *= np.clip(u / 0.12, 0.08, 1) ** 0.7
        if self.tail == 'taper':
            p *= np.clip((1 - u) / 0.28, 0.02, 1) ** 0.8
        else:
            p *= np.clip((1 - u) / 0.15, 0.35, 1) ** 0.5
        p *= 1 - 0.18 * u
        return p

    def table(self, ns):
        """(ns × NB) 먹 표, 반폭(mm) 배열."""
        u = np.linspace(0, 1, ns)
        hw = 0.5 * self.width * self.pressure(u) * (1 + 0.07 * smooth_noise(ns, self.seed + 3, max(2, ns // 30)))
        # 먹이 떨어짐: 붓털마다 dry_at에서 꺼짐, 그 앞에서 깜빡이며(마른 붓의 끊김) 약해짐
        fade = 0.10 + 0.10 * (1 - self.dry)
        U = u[:, None]
        amt = self.bload[None, :] * np.clip((self.dry_at[None, :] - U) / fade, 0, 1)
        flick = smooth_noise(ns * 3, self.seed + 4, 6).reshape(ns, 3).mean(1)[:, None]
        sk = np.clip(1 - (U - (self.dry_at[None, :] - fade * 2.5)) / (fade * 3), 0, 1)
        amt *= np.clip(1 - (1 - sk) * (0.5 + 0.5 * np.sin(np.arange(NB)[None, :] * 0.9 + flick * 3)) * 0.7, 0, 1)
        if self.tail == 'fly':
            amt *= np.clip(1 - np.clip(U - 0.8, 0, 1) * 3.5 * (0.6 + 0.4 * np.cos(np.arange(NB)[None, :] * 1.7)), 0, 1)
        # 젖은 동안 붓털끼리 번져 하나로(폭 방향 흐림), 마를수록 덜 번짐
        # 길이 방향 먹 양 출렁임(붓에서 먹이 고르게 나오지 않음)
        amt *= (1 + 0.10 * smooth_noise(ns, self.seed + 5, max(2, ns // 12)))[:, None]
        out = np.empty_like(amt)
        for i in range(ns):
            wetness = float(np.clip(1 - u[i] * (0.5 + self.dry) - self.dry * 0.35, 0.0, 1))
            row = cv2.GaussianBlur(amt[i][None, :].astype(F32), (0, 0), 0.5 + 1.6 * wetness)[0]
            # 마를수록 붓털 경계가 날카롭다: 흰 결이 선명한 끊김으로
            k = 1 - wetness
            lo, hi = 0.35 * k, 1 - 0.45 * k
            sh = np.clip((row - lo) / max(hi - lo, 1e-3), 0, 1.3)
            out[i] = row * (1 - k) + sh * k
        self.wetness = np.clip(1 - u * (0.5 + self.dry) - self.dry * 0.35, 0, 1)
        return out * self.load, hw

    def render(self, view, dens, fib=None):
        """view 위에 이 획의 먹 밀도를 더한다."""
        ppm = view.ppm
        px, py = view.to_px(self.c[:, 0], self.c[:, 1])
        P = np.stack([px, py], 1)
        x0, y0 = P.min(0) - self.width * ppm; x1, y1 = P.max(0) + self.width * ppm
        x0, y0 = max(0, int(x0)), max(0, int(y0)); x1, y1 = min(view.W, int(x1) + 1), min(view.H, int(y1) + 1)
        if x1 <= x0 or y1 <= y0:
            return
        # 화면 기준 촘촘한 척추
        ns = int(min(4000, max(30, self.L * ppm / 0.7)))
        si = np.linspace(0, self.L, ns)
        cx = np.interp(si, self.s, self.c[:, 0]); cy = np.interp(si, self.s, self.c[:, 1])
        sx, sy = view.to_px(cx, cy)
        tx, ty = np.gradient(sx), np.gradient(sy); tn = np.hypot(tx, ty) + 1e-9; tx /= tn; ty /= tn
        tab, hw = self.table(ns)
        hwp = hw * ppm
        tree = cKDTree(np.stack([sx, sy], 1))
        yy, xx = np.mgrid[y0:y1, x0:x1].astype(F32)
        d, idx = tree.query(np.stack([xx.ravel(), yy.ravel()], 1), k=1, distance_upper_bound=float(hwp.max() + 3))
        ok = np.isfinite(d)
        if not ok.any():
            return
        idx = np.where(ok, idx, 0)
        dx = xx.ravel() - sx[idx]; dy = yy.ravel() - sy[idx]
        sd = dx * (-ty[idx]) + dy * tx[idx]
        along = dx * tx[idx] + dy * ty[idx]
        h = hwp[idx]
        v = sd / np.maximum(h, 0.3)
        # 머리·꼬리: 척추 끝 너머는 둥글게 닫음
        slant = 0.22 if self.head == 'press' else 0.0           # 비스듬히 눌러 들어간 머리
        a0 = (along + v * h * slant) / np.maximum(h, 0.3)
        endcap = np.where((idx == 0) & (a0 < 0), np.abs(a0) * (1.08 if self.head == 'press' else 1.0), 0)
        endcap = np.where((idx == ns - 1) & (along > 0), np.abs(along) / np.maximum(h, 0.3), endcap)
        r = np.sqrt(v * v + endcap * endcap)
        if fib is not None:                                       # 가장자리를 섬유 결로 거칠게
            fz = fib[y0:y1, x0:x1].ravel()
            r = r + (0.5 - fz) * np.clip(2.5 / np.maximum(h, 1), 0.02, 0.25)
        edge = np.clip((1 - r) * h / 0.7 + 0.5, 0, 1)
        bi = np.clip((v + 1) * 0.5 * (NB - 1), 0, NB - 1)
        b0 = np.floor(bi).astype(int); fb = bi - b0; b1 = np.minimum(b0 + 1, NB - 1)
        val = tab[idx, b0] * (1 - fb) + tab[idx, b1] * fb
        if fib is not None:                                       # 마른 붓은 섬유 골을 건너뛴다
            dryk = 1 - self.wetness[idx]
            val = val * (1 - dryk * 0.55 * np.clip(fz * 1.4 - 0.2, 0, 1))
        out = np.where(ok, val * edge, 0).reshape(yy.shape).astype(F32)
        dens[y0:y1, x0:x1] += out


def render_strokes(view, strokes, fib):
    """여러 획 → 먹 밀도. 젖은 획은 섬유 따라 가장자리 번짐."""
    dens = np.zeros((view.H, view.W), F32)
    wetd = np.zeros_like(dens)
    for st in strokes:
        tmp = np.zeros_like(dens)
        st.render(view, tmp, fib)
        dens += tmp
        if st.wet > 0:
            wetd += tmp * st.wet
    if wetd.max() > 0:
        sig = max(0.8, 0.45 * view.ppm)                       # 약 0.45mm 번짐
        halo = cv2.GaussianBlur(wetd, (0, 0), sig)
        fe = np.clip(fib * 1.6 - 0.25, 0, 1.5) ** 1.5          # 섬유를 따라서만 스민다
        dens += np.clip(halo - wetd, 0, None) * fe * 1.3
        # 젖은 획 가장자리에 먹이 고여 테두리가 살짝 진하다
        rim = np.clip(wetd - cv2.GaussianBlur(wetd, (0, 0), sig * 1.5), 0, None)
        dens += rim * 0.35
    return dens


class Wash:
    """발묵 덩어리(구름·음영). 점들(mm, 반지름 mm)의 부드러운 합 → 문턱을 노이즈로 흔들어 가장자리를 만들고,
    섬유를 따라 바깥으로 스미게 한다. 가장자리에 먹이 살짝 고인다."""
    def __init__(self, blobs, load=0.2, soft=0.35, seed=0, rim=0.25, name='wash'):
        self.blobs, self.load, self.soft, self.seed, self.rim, self.name = blobs, load, soft, seed, rim, name
        self.wet = 0

    def render(self, view, dens, fib=None):
        X0, Y0, X1, Y1 = view.bbox_mm(0)
        xs = [b[0] for b in self.blobs]; ys = [b[1] for b in self.blobs]; rs = [b[2] for b in self.blobs]
        bx0, by0 = min(xs) - 3 * max(rs), min(ys) - 3 * max(rs); bx1, by1 = max(xs) + 3 * max(rs), max(ys) + 3 * max(rs)
        px0, py0 = view.to_px(bx0, by0); px1, py1 = view.to_px(bx1, by1)
        x0, y0 = max(0, int(min(px0, px1))), max(0, int(min(py0, py1)))
        x1, y1 = min(view.W, int(max(px0, px1)) + 1), min(view.H, int(max(py0, py1)) + 1)
        if x1 <= x0 or y1 <= y0:
            return
        X, Y = view.grid_mm_crop(x0, y0, x1, y1)
        f = np.zeros_like(X)
        for (bx, by, br) in self.blobs:
            f += np.exp(-((X - bx) ** 2 + (Y - by) ** 2) / (br * br))
        r = np.random.default_rng(self.seed)
        nz = np.zeros_like(X)
        for k in range(5):                                    # mm 좌표 위의 저주파 노이즈(배율 무관)
            fq = r.uniform(0.6, 1.4) * (0.08 * 1.8 ** k); a = r.uniform(0, 3.14); ph = r.uniform(0, 6.28)
            nz += np.sin((X * math.cos(a) + Y * math.sin(a)) * fq + ph) / (1 + k)
        g = f * (1 + 0.35 * nz) - 0.5                     # 곱셈 노이즈: 멀리서는 0으로 사라짐
        body = np.clip(g / self.soft + 0.5, 0, 1)
        body = body * body * (3 - 2 * body)
        edge = np.exp(-(g / (self.soft * 0.35)) ** 2) * (g < 0.15)
        val = body * (0.75 + 0.25 * np.clip(f, 0, 1.5)) + edge * self.rim
        if fib is not None:
            fz = fib[y0:y1, x0:x1]
            fzs = cv2.GaussianBlur(fz, (0, 0), max(0.6, view.ppm * 0.08))   # 섬유를 뭉개 거미줄 무늬 방지
            halo = np.exp(-((g + 0.07) / 0.05) ** 2) * (1 - body)
            val = val + halo * np.clip(fzs * 1.6 - 0.35, 0, 1) * 0.45
        dens[y0:y1, x0:x1] += (val * self.load).astype(F32)
