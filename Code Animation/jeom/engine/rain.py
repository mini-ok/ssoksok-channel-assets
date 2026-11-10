"""붓으로 그린 비. 흰 직선(디지털 선) 대신, 마른 넓은 붓을 비스듬히 쓸어 내린 결.
세 겹:
  1) 빗발 안개(담묵): 넓게 흐린 결 — 비가 띠로 몰려오는 것이 먹 번짐처럼 보인다.
  2) 붓 쓸기(갈필): 넓은 띠 마스크 × 가는 붓털 결. 한 번의 붓질 안에 가는 줄 여러 가닥이 모여 있고, 띠 가장자리에서 끊긴다.
  3) 가까운 빗방울: 짧고 굵은 몇 획(화면 앞).
결은 빗줄기 방향으로 미끄러뜨리고(투스), 바람 때문에 가로로 살짝 휜다. 종이 섬유 골에서 끊긴다.
반환: 먹(어둡게) 밀도. 번개 때는 같은 결을 밝게 쓴다.
"""
import math
import numpy as np, cv2

F32 = np.float32


def _tex(S, seed, cross, lng, rows=2):
    """주기적(이음매 없는) 이방성 결: 주파수 공간에서 가우스 거름."""
    r = np.random.default_rng(seed)
    n = r.standard_normal((S * rows, S))
    fy = np.fft.fftfreq(S * rows)[:, None]; fx = np.fft.rfftfreq(S)[None, :]
    G = np.exp(-2 * (np.pi ** 2) * ((fx * cross) ** 2 + (fy * lng) ** 2))
    m = np.fft.irfft2(np.fft.rfft2(n) * G, s=n.shape)
    return (m / (m.std() + 1e-9)).astype(F32)


class InkRain:
    def __init__(self, W, H, angle=-14.0, seed=5, fib=None, scale=1.0):
        self.W, self.H, self.angle, self.fib = W, H, angle, fib
        S = int(math.hypot(H, W) * 1.05) + 32
        self.S = S
        k = scale
        self.haze = _tex(S, seed + 1, 4 * k, 120 * k)
        self.band = _tex(S, seed + 2, 5 * k, 100 * k)
        self.hair = _tex(S, seed + 3, 0.55 * k, 30 * k)
        self.near = _tex(S, seed + 4, 1.3 * k, 14 * k)
        r = np.random.default_rng(seed + 9)
        g = r.standard_normal((H // 90 + 3, W // 90 + 3)).astype(F32)
        self.gust = cv2.resize(g, (W * 3, H * 3), interpolation=cv2.INTER_CUBIC)
        w = r.standard_normal((1, S // 200 + 3)).astype(F32)
        self.wob = cv2.resize(w, (S * 2, 1), interpolation=cv2.INTER_CUBIC)[0]
        yy, xx = np.mgrid[0:H, 0:W].astype(F32)
        self.xx, self.yy = xx, yy

    def _sample(self, tex, u, v, off):
        S = self.S
        mx = (u + S / 2) % (S - 1); my = (v + S / 2 - off) % (S * 2 - 1)
        return cv2.remap(tex, mx.astype(F32), my.astype(F32), cv2.INTER_LINEAR, borderMode=cv2.BORDER_WRAP)

    def render(self, t, amount=1.0, gust=0.6, flow=None, fps=12, light=False):
        if amount <= 0:
            return np.zeros((self.H, self.W), F32)
        q = math.floor(t * fps) / fps
        W, H = self.W, self.H
        a = math.radians(self.angle); ca, sa = math.cos(a), math.sin(a)
        xx, yy = self.xx, self.yy
        if flow is not None:
            xx = xx - flow[0]; yy = yy - flow[1]
        u = (xx - W / 2) * ca - (yy - H / 2) * sa
        v = (xx - W / 2) * sa + (yy - H / 2) * ca
        vi = np.clip(((v + self.S / 2) * 0.5).astype(int), 0, len(self.wob) - 1)
        u = u + 9.0 * self.wob[vi]                                              # 바람에 살짝 휜 빗줄기
        gx = ((xx * 0.33 + q * 40) % (W * 3 - 1)).astype(F32); gy = ((yy * 0.33 - q * 150) % (H * 3 - 1)).astype(F32)
        gm = cv2.remap(self.gust, gx, gy, cv2.INTER_LINEAR)                    # 빗발(몰려오는 띠)
        dens_amt = np.clip(amount * (1 + gust * 0.6 * gm), 0, 1.6)
        haze = self._sample(self.haze, u, v, q * 520)
        haze = np.clip((haze - 0.6) * 0.6, 0, 1) * 0.30
        band = self._sample(self.band, u, v, q * 780)
        hair = self._sample(self.hair, u, v, q * 780)
        sweep = np.clip((band - 1.15 + 0.9 * (1 - dens_amt)) * 1.6, 0, 1) * np.clip((hair + 0.2) * 1.4, 0, 1)
        near = self._sample(self.near, u * 0.9, v, q * 1250)
        near = np.clip((near - 2.5 + 1.0 * (1 - dens_amt)) * 2.0, 0, 1)
        out = haze * dens_amt + sweep * 0.75 + near * 0.9
        if self.fib is not None:
            out = out * np.clip(0.55 + 1.2 * self.fib, 0, 1.2)
        return out


class RadialRain(InkRain):
    """원근이 있는 붓 비: 같은 붓 결(InkRain)을 극좌표(각도 × log 반지름)에 감아, 빗줄기가 소실점(vp)으로 모이게 한다.
    toward=True: 하늘을 올려다봄 — 비가 소실점에서 카메라 쪽(바깥)으로 쏟아진다.
    toward=False: 내려다봄 — 비가 카메라 뒤에서 와 소실점(땅) 쪽으로 빨려 들어간다.
    가까운(바깥) 빗줄기일수록 굵고 길며, 소실점 가까이는 가늘고 짧다(로그 반지름이라 저절로)."""
    def __init__(self, W, H, vp, seed=5, fib=None, scale=1.0, toward=True, K=None):
        super().__init__(W, H, angle=0.0, seed=seed, fib=fib, scale=scale)
        self.vp, self.toward = vp, toward
        self.K = K if K is not None else 470.0 * scale
        k = scale                                                              # 앞쪽 비는 짧고 넓게(소실점으로 꽂히는 선처럼 보이지 않게)
        self.band = _tex(self.S, seed + 12, 6 * k, 75 * k)
        self.hair = _tex(self.S, seed + 13, 0.7 * k, 22 * k)
        self.near = _tex(self.S, seed + 14, 1.8 * k, 11 * k)
        dx, dy = self.xx - vp[0], self.yy - vp[1]
        self.R = np.hypot(dx, dy) + 1e-3
        self.TH = np.arctan2(dy, dx)

    def render(self, t, amount=1.0, gust=0.6, flow=None, fps=12, light=False, speed=1.0):
        if amount <= 0:
            return np.zeros((self.H, self.W), F32)
        q = math.floor(t * fps) / fps
        S = self.S
        u = (self.TH / (2 * math.pi)) * (S - 1)                                 # 둘레 = 결 한 주기(이음매 없음)
        v = self.K * np.log(self.R / (60.0 * self.K / 380.0))
        if flow is not None:
            v = v - flow
        sgn = 1.0 if self.toward else -1.0
        W, H = self.W, self.H
        gx = ((self.xx * 0.33 + q * 40) % (W * 3 - 1)).astype(F32); gy = ((self.yy * 0.33 - q * 150) % (H * 3 - 1)).astype(F32)
        gm = cv2.remap(self.gust, gx, gy, cv2.INTER_LINEAR)
        dens_amt = np.clip(amount * (1 + gust * 0.6 * gm), 0, 1.6)
        sp = speed * sgn
        haze = self._sample(self.haze, u, v, q * 380 * sp)
        haze = np.clip((haze - 0.6) * 0.6, 0, 1) * 0.30
        band = self._sample(self.band, u, v, q * 560 * sp)
        hair = self._sample(self.hair, u, v, q * 560 * sp)
        sweep = np.clip((band - 1.15 + 0.9 * (1 - dens_amt)) * 1.6, 0, 1) * np.clip((hair + 0.2) * 1.4, 0, 1)
        near = self._sample(self.near, u * 0.9, v, q * 900 * sp)
        near = np.clip((near - 2.5 + 1.0 * (1 - dens_amt)) * 2.0, 0, 1)
        fade = np.clip((self.R - 30.0 * self.K / 380.0) / (120.0 * self.K / 380.0), 0, 1)   # 소실점 가까이는 비가 안개처럼 사라진다
        far = np.clip(self.R / (0.30 * min(W, H)), 0, 1)                          # 굵은 앞쪽 방울은 화면 가장자리 쪽에만
        out = (haze * dens_amt * 1.25 + sweep * 0.7 * fade + near * 0.35 * fade ** 2 * far)
        if self.fib is not None:
            out = out * np.clip(0.55 + 1.2 * self.fib, 0, 1.2)
        return out
