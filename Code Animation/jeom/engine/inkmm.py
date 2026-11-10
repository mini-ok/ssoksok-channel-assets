"""점(먹 한 방울)의 번짐 사슬 — 종이 mm 좌표, t의 순수 함수.

물: 방울(둥근 것 / 바람에 길게 그어진 물줄기)마다 섬유 따라 걸리는 시간(측지 거리)을 미리 계산하고,
    앞전선 반지름을 시간 키로 준다. 비가 그치면 가장자리부터 마른다.
먹: 단계(블룸)마다 접촉점에서 그 단계의 물 영역 안으로 피어난다. 다음 단계가 먹을 끌어가면 옅은 얼룩으로 남는다.
    튄 먹과 합쳐지면 진해진다. 마르면 테두리가 진해진다.
규칙 깨기: 마지막 단계의 먹을 세 번에 걸쳐 눈자리 E로 끌어모은다(질량 보존, 지나온 자리에는 아주 옅은 흔적).
"""
import math
import numpy as np, cv2
from skimage.graph import MCP_Geometric

F32 = np.float32
import os
RES = float(os.environ.get('JEOM_RES', '0.25'))   # mm / 칸 (애니마틱은 0.5)
X0, Y0, X1, Y1 = 0.0, 90.0, 340.0, 420.0
GW, GH = int((X1 - X0) / RES), int((Y1 - Y0) / RES)
yy, xx = np.mgrid[0:GH, 0:GW].astype(F32)
XM = X0 + xx * RES; YM = Y0 + yy * RES


def sstep(x, a, b):
    t = np.clip((x - a) / (b - a), 0, 1)
    return t * t * (3 - 2 * t)


def ramp(t, a, b):
    return float(np.clip((t - a) / (b - a), 0, 1))


def ease(u):
    return u * u * (3 - 2 * u)


class Field:
    """섬유 전도도와 측지 도착 시간."""
    def __init__(self, fib_grid):
        fs = cv2.GaussianBlur(fib_grid, (0, 0), 1.5)
        fs = fs / (np.percentile(fs, 99) + 1e-6)
        r = np.random.default_rng(31)
        nz = cv2.resize(r.standard_normal((GH // 24 + 2, GW // 24 + 2)).astype(F32), (GW, GH), interpolation=cv2.INTER_CUBIC)
        speed = np.clip(0.35 + 1.1 * fs + 0.25 * nz, 0.12, 2.2)
        self.cost = (1.0 / speed).astype(F32)
        self.med = float(np.median(self.cost))
        self._T = {}

    def arrival(self, seeds):
        key = tuple((round(x, 1), round(y, 1)) for x, y in seeds)
        if key not in self._T:
            m = MCP_Geometric(self.cost)
            pts = [(int((y - Y0) / RES), int((x - X0) / RES)) for x, y in seeds]
            T, _ = m.find_costs(pts)
            self._T[key] = (T * RES / self.med).astype(F32)       # mm
        return self._T[key]


def seg_seeds(a, b, step=1.0):
    n = max(2, int(math.hypot(b[0] - a[0], b[1] - a[1]) / step))
    return [(a[0] + (b[0] - a[0]) * i / (n - 1), a[1] + (b[1] - a[1]) * i / (n - 1)) for i in range(n)]


class Water:
    def __init__(self, field, t0, seeds, Rmax, tau=0.35):
        self.t0, self.Rmax, self.tau = t0, Rmax, tau
        self.T = field.arrival(seeds)

    def R(self, t):
        return -1 if t < self.t0 else self.Rmax * (1 - math.exp(-(t - self.t0) / self.tau))


class Stage:
    def __init__(self, field, t0, contact, Rf, tau, level, waters, pre=0.3):
        """pre: 번지기 전 예비 동작(살짝 오그라듦) 길이(초)."""
        self.t0, self.Rf, self.tau, self.level, self.pre = t0, Rf, tau, level, pre
        self.contact = contact
        self.T = field.arrival([contact])
        reg = np.zeros((GH, GW), F32)
        for w in waters:
            reg = np.maximum(reg, sstep(w.Rmax - w.T, -1.0, 2.0))
        self.region = reg

    def R(self, t):
        return -1 if t < self.t0 else self.Rf * (1 - math.exp(-(t - self.t0) / self.tau))


class Dot:
    def __init__(self, field, story):
        """story: timeline 모듈(물·단계·튄 먹·건조·모임 시각을 가진 객체)."""
        self.f = field; self.s = story
        self.waters = [Water(field, *w) for w in story.WATERS]
        self.decor = [Water(field, *w) for w in getattr(story, 'DECOR', [])]
        self.stages = []
        self.connectors = []
        for k, (t0, contact, Rf, tau, level, widx) in enumerate(story.STAGES):
            ws = [self.waters[i] for i in widx]
            if k >= 1 and len(widx) >= 2:
                # 앞 물웅덩이와 다음 물웅덩이를 잇는 가는 물줄기(바람에 그어진 자국): 먹이 선으로 이어지게
                a = story.WATERS[widx[0]][1][-1]; b = story.WATERS[widx[-1]][1][0]
                c = Water(field, t0 - 0.25, seg_seeds(a, b, 0.8), 3.6, 0.25)
                self.connectors.append(c); ws = ws + [c]
            self.stages.append(Stage(field, t0, contact, Rf, tau, level, ws))
        r = np.random.default_rng(91)
        self.nz = cv2.resize(r.standard_normal((GH // 40 + 2, GW // 40 + 2)).astype(F32), (GW, GH), interpolation=cv2.INTER_CUBIC)
        self._c = None

    # ---- 물
    def wet(self, t):
        m = np.zeros((GH, GW), F32)
        dry = 0.9 * ease(ramp(t, *self.s.RAIN_STOP))
        for i, w in enumerate(self.waters):
            R = w.R(t)
            if R <= 0:
                continue
            mi = sstep(R - w.T, -0.5, 1.5)
            d = dry
            if i == 0:
                d = max(d, 0.5 * ease(ramp(t, *self.s.BLOT_DRY)) * (1 - ramp(t, self.waters[1].t0, self.waters[1].t0 + 0.5)))
            if d > 0:
                mi = np.clip((mi - d) / (1 - d), 0, 1)
            m = np.maximum(m, mi)
        for w in self.connectors:
            R = w.R(t)
            if R <= 0:
                continue
            mi = sstep(R - w.T, -0.5, 1.5)
            m = np.maximum(m, np.clip((mi - dry) / (1 - dry), 0, 1) if dry > 0 else mi)
        for w in self.decor:
            R = w.R(t)
            if R <= 0:
                continue
            mi = sstep(R - w.T, -0.5, 1.5)
            d = max(dry, 0.9 * ease(ramp(t, w.t0 + 6.0, w.t0 + 12.0)))      # 작은 물방울은 먼저 마른다
            m = np.maximum(m, np.clip((mi - d) / (1 - d), 0, 1) if d > 0 else mi)
        return m

    # ---- 먹
    def _speck(self, x, y, r, amt):
        d2 = ((XM - x) ** 2 + (YM - y) ** 2) / (r * r)
        ang = np.arctan2(YM - y, XM - x)
        return amt * np.exp(-d2 * 2.5 * (1 + 0.25 * np.cos(ang * 3 + x)))

    def density(self, t, want_live=False):
        S = self.s
        self.pupil = None
        dens = np.zeros((GH, GW), F32)
        live = None; live_k = -1
        for k, st in enumerate(self.stages):
            R = st.R(t)
            if R <= 0:
                continue
            body = sstep(R - st.T, -0.4, 1.2) * st.region
            grad = 1 - 0.3 * np.clip(st.T / st.Rf, 0, 1)
            lvl = st.level
            if k + 1 < len(self.stages):
                nx = self.stages[k + 1]
                lvl *= 1 - S.LEAVE * ease(ramp(t, nx.t0, nx.t0 + 0.9))
            for (km, tm, add) in S.MERGES:
                if km == k:
                    lvl += add * ease(ramp(t, tm, tm + 0.7))
            dry = ease(ramp(t, *S.RAIN_STOP)) if k > 0 else max(0.7 * ease(ramp(t, *S.BLOT_DRY)), ease(ramp(t, *S.RAIN_STOP)))
            if k + 1 < len(self.stages):
                dry = max(dry, 0.8 * ease(ramp(t, self.stages[k + 1].t0, self.stages[k + 1].t0 + 2.0)))
            rim = sstep(R - st.T, -0.3, 0.5) * (1 - sstep(R - st.T, 0.5, 1.8)) * st.region
            f = body * grad * lvl * (1 + 0.08 * self.nz) + rim * lvl * 0.55 * dry
            # 예비 동작: 다음 단계 직전, 지금의 몸이 살짝 오그라들며 진해짐
            if k + 1 < len(self.stages):
                nx = self.stages[k + 1]
                if nx.t0 - nx.pre <= t < nx.t0:
                    u = (t - (nx.t0 - nx.pre)) / nx.pre
                    f = f * (1 + 0.12 * math.sin(math.pi * u))
            if k == len(self.stages) - 1 or (k + 1 < len(self.stages) and self.stages[k + 1].R(t) <= 0):
                live, live_k = f, k
            dens += f
        for (x, y, r, amt, melt_t) in S.SPECKS:
            a = amt * (1 - ease(ramp(t, melt_t, melt_t + 0.5))) if melt_t else amt
            dens += self._speck(x, y, r, a)
        # 규칙 깨기: 마지막 단계의 먹을 E로 모은다
        if live is not None and live_k == len(self.stages) - 1:
            sc, frac = S.gather_scale(t)
            if sc != 1.0:
                if self._c is None:
                    w = live; self._c = (float((w * XM).sum() / w.sum()), float((w * YM).sum() / w.sum()))
                cx, cy = self._c
                ex, ey = S.E
                ncx, ncy = cx + (ex - cx) * frac, cy + (ey - cy) * frac        # 모일수록 중심이 눈자리로
                srcx = cx + (XM - ncx) / sc; srcy = cy + (YM - ncy) / sc
                mx = ((srcx - X0) / RES).astype(F32); my = ((srcy - Y0) / RES).astype(F32)
                g = cv2.remap(live, mx, my, cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT) / (sc * sc)
                g = 3.4 * np.tanh(cv2.GaussianBlur(g, (0, 0), 0.8) / 3.4)
                dens = dens - live + live * 0.07 + g * 0.93
                if frac >= 1.0:
                    self.pupil = (g * 0.93).astype(F32)
        if want_live:
            return dens, live
        return dens


def sample(grid, view, Xv=None, Yv=None):
    """mm 격자 값을 화면으로."""
    if Xv is None:
        Xv, Yv = view.grid_mm()
    mx = ((Xv - X0) / RES).astype(F32); my = ((Yv - Y0) / RES).astype(F32)
    interp = cv2.INTER_LINEAR if view.ppm / (1 / RES) < 1.5 else cv2.INTER_CUBIC
    return cv2.remap(grid, mx, my, interp, borderMode=cv2.BORDER_CONSTANT)
