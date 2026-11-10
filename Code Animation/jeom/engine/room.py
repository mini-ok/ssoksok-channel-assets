"""화실 원경(옆에서 본 방). 화가는 실루엣으로만 — 손가락·표정 연기 없음.
구도: 오른쪽 벽에 창(열림), 창 아래 서안과 그 위 종이, 서안 왼쪽 바닥에 앉은 화가, 그 사이 바닥에 등잔대,
앞쪽 왼편 바닥에 잘라 낸 귀퉁이들이 담긴 대바구니. 등잔이 화가의 큰 그림자를 뒤 벽에 던진다(떨림이 벽에서 크게 보인다).
light: 'lamp'(밤, 등잔) / 'dark'(등잔 끈 밤, 창빛만) / 'dawn'(새벽빛). flash: 번개 0..1.
pose: 키포인트 dict(정규 좌표 0..1, x 오른쪽, y 아래) — POSES의 것을 섞어 쓴다.
"""
import math
import numpy as np, cv2

F32 = np.float32
import os
SS = 1 if float(os.environ.get('JEOM_SCALE', '1')) >= 2 else 2   # 슈퍼샘플(1080p에서는 불필요)

POSES = {
    # 서안 쪽으로 몸을 기울여 붓을 든 자세(붓끝 hand가 종이 위)
    'paint': dict(hip=(0.355, 0.80), sho=(0.385, 0.585), head=(0.405, 0.535), elb=(0.47, 0.62), hand=(0.555, 0.600),
                  knee=(0.45, 0.80), brush=1.0, lean=0.0),
    # 붓을 거두고 허리를 편 자세
    'rest': dict(hip=(0.355, 0.80), sho=(0.370, 0.585), head=(0.378, 0.530), elb=(0.42, 0.66), hand=(0.455, 0.70),
                 knee=(0.45, 0.80), brush=1.0, lean=0.0),
    # 벽에 기대 잠듦: 상체가 뒤(왼쪽)로, 고개는 앞으로 떨굼, 손은 무릎
    'sleep': dict(hip=(0.345, 0.80), sho=(0.318, 0.600), head=(0.338, 0.560), elb=(0.36, 0.70), hand=(0.42, 0.745),
                  knee=(0.44, 0.80), brush=0.0, lean=1.0),
    # 깨어 고개를 듦(창 쪽)
    'wake': dict(hip=(0.345, 0.80), sho=(0.335, 0.592), head=(0.350, 0.538), elb=(0.37, 0.69), hand=(0.43, 0.74),
                 knee=(0.44, 0.80), brush=0.0, lean=0.6),
    # 일어나 서안 쪽으로 무릎걸음으로 옮겨 가는 중
    'move': dict(hip=(0.430, 0.80), sho=(0.452, 0.598), head=(0.474, 0.548), elb=(0.478, 0.680), hand=(0.505, 0.715),
                 knee=(0.520, 0.80), brush=0.0, lean=0.2),
    'peer': dict(hip=(0.480, 0.80), sho=(0.515, 0.585), head=(0.540, 0.535), elb=(0.545, 0.650), hand=(0.575, 0.652),
                 knee=(0.565, 0.80), brush=0.0, lean=0.0),                 # 서안 앞에 다가앉아 허리를 조금 굽히고 그림을 내려다봄(고개는 많이 숙이지 않음)
}


def mix(a, b, u):
    out = {}
    for k in a:
        va, vb = a[k], b[k]
        if isinstance(va, tuple):
            out[k] = (va[0] + (vb[0] - va[0]) * u, va[1] + (vb[1] - va[1]) * u)
        else:
            out[k] = va + (vb - va) * u
    return out


def _noise(h, w, seed, s):
    r = np.random.default_rng(seed)
    n = r.standard_normal((h // s + 3, w // s + 3)).astype(F32)
    return cv2.resize(n, (w + 3 * s, h + 3 * s), interpolation=cv2.INTER_CUBIC)[:h, :w]


class Room:
    def __init__(self, W=960, H=540, seed=3):
        self.W, self.H = W, H
        w, h = W * SS, H * SS
        self.w, self.h = w, h
        yy, xx = np.mgrid[0:h, 0:w].astype(F32)
        self.xx, self.yy = xx / w, yy / h
        self.grain = (0.6 * _noise(h, w, seed, 64) + 0.4 * _noise(h, w, seed + 1, 12))
        self.fiber = np.abs(_noise(h, w, seed + 2, 3)) * 0.5
        self.rain_rng = np.random.default_rng(seed + 9)
        self.rain = self.rain_rng.uniform(0, 1, (220, 3))
        self.scraps = np.random.default_rng(seed + 5).uniform(0, 1, (16, 5))
        self.edge_n = (_noise(h, w, seed + 21, 28), _noise(h, w, seed + 22, 28))

    # -------- 도형 도우미 (정규 좌표 → 슈퍼샘플 픽셀)
    def P(self, pts):
        return (np.array(pts, float) * (self.w, self.h)).astype(np.int32)

    def poly(self, m, pts, v=1.0):
        cv2.fillPoly(m, [self.P(pts)], v, cv2.LINE_AA)

    def line(self, m, a, b, wid, v=1.0):
        pa, pb = self.P([a, b])
        cv2.line(m, tuple(pa), tuple(pb), v, max(1, int(wid * self.w)), cv2.LINE_AA)

    def circle(self, m, c, r, v=1.0):
        pc = self.P([c])[0]
        cv2.circle(m, tuple(pc), max(1, int(r * self.w)), v, -1, cv2.LINE_AA)

    # -------- 화가 실루엣
    def figure(self, pose, tremor=(0.0, 0.0)):
        """늙은 선비의 앉은 실루엣: 작은 머리(상투), 굽은 등, 넓은 도포 소매. 가장자리는 붓으로 그린 듯 거칠게."""
        m = np.zeros((self.h, self.w), F32)
        hip, sho, head, elb, hand, knee = (pose[k] for k in ('hip', 'sho', 'head', 'elb', 'hand', 'knee'))
        tx, ty = tremor
        hand = (hand[0] + tx, hand[1] + ty); elb = (elb[0] + tx * 0.4, elb[1] + ty * 0.4)
        sx, sy = sho; hx, hy = hip
        # 도포 아랫자락
        self.poly(m, [(hx - 0.050, 0.812), (knee[0] + 0.028, 0.812), (knee[0] + 0.012, knee[1] - 0.038),
                      ((hx + knee[0]) / 2 + 0.01, hy - 0.062), (hx - 0.035, hy - 0.075)])
        # 굽은 등과 몸통: 어깨 둥글게, 등은 바깥으로 불룩
        bx = min(sx, hx) - 0.046 - 0.012 * pose['lean']
        body = [(sx + 0.026, sy + 0.012), (hx + 0.040, hy - 0.058), (hx - 0.040, hy - 0.040),
                (bx, (sy + hy) / 2 + 0.03), (bx + 0.004, (sy + hy) / 2 - 0.035), (sx - 0.030, sy + 0.004), (sx - 0.010, sy - 0.012)]
        self.poly(m, body)
        # 목(짧고 앞으로 나옴)·머리·상투
        self.line(m, (sx - 0.006, sy + 0.004), (head[0] - 0.002, head[1] + 0.006), 0.022)
        self.circle(m, head, 0.0175)
        hc = self.P([head])[0]
        cv2.ellipse(m, tuple(hc), (int(0.0185 * self.w), int(0.0155 * self.w)), 0, 0, 360, 1.0, -1, cv2.LINE_AA)
        # 상투: 정수리에 솟은 뚜렷한 틀어 올린 머리 + 가로로 꽂은 동곳(실루엣에서도 읽히게)
        ang = math.atan2(head[1] - sy, head[0] - sx)
        ca, sa = math.cos(ang), math.sin(ang)
        base = (head[0] + 0.015 * ca, head[1] + 0.015 * sa)
        knot = (head[0] + 0.026 * ca, head[1] + 0.026 * sa)
        self.line(m, base, knot, 0.011)
        kc = self.P([knot])[0]
        cv2.ellipse(m, tuple(kc), (int(0.0078 * self.w), int(0.0098 * self.w)), math.degrees(ang) + 90, 0, 360, 1.0, -1, cv2.LINE_AA)
        pa = (knot[0] - 0.013 * sa, knot[1] + 0.013 * ca); pb = (knot[0] + 0.013 * sa, knot[1] - 0.013 * ca)
        self.line(m, pa, pb, 0.0026)
        # 팔: 소매가 넓게 늘어진다
        self.line(m, (sx + 0.008, sy + 0.018), elb, 0.024)
        self.line(m, elb, hand, 0.014)
        self.poly(m, [(elb[0] - 0.012, elb[1] - 0.006), (elb[0] + 0.014, elb[1] + 0.05), ((elb[0] + hand[0]) / 2 + 0.01, (elb[1] + hand[1]) / 2 + 0.052),
                      (hand[0] - 0.006, hand[1] + 0.018), hand])
        self.circle(m, hand, 0.0068)
        if pose['brush'] > 0.5:
            self.line(m, hand, (hand[0] + 0.003, hand[1] + 0.040), 0.0028)
        # 붓 자국처럼 거친 가장자리: 노이즈로 밀어낸다
        dx = self.edge_n[0] * 1.3 * SS; dy = self.edge_n[1] * 1.3 * SS
        gx, gy = np.meshgrid(np.arange(self.w, dtype=F32), np.arange(self.h, dtype=F32))
        m = cv2.remap(m, gx + dx, gy + dy, cv2.INTER_LINEAR)
        return cv2.GaussianBlur(m, (0, 0), 0.8 * SS)

    # -------- 한 장
    def render(self, t, pose, light='lamp', flash=0.0, tremor=(0.0, 0.0), lamp_on=1.0, dawn=0.0, rain=1.0,
               paper_ink=None, basket=True):
        w, h, X, Y = self.w, self.h, self.xx, self.yy
        img = np.zeros((h, w, 3), F32)
        # 벽·바닥(먹빛 갈색, 종이 결)
        wall = np.array((0.085, 0.070, 0.058), F32) * (1 + 0.08 * self.grain[..., None])
        img[:] = wall
        floor = Y > 0.80
        img[floor] = np.array((0.050, 0.040, 0.032), F32)
        img[floor] *= (1 + 0.1 * self.grain[floor])[:, None]
        # 창(열린 창): 하늘 + 비
        win = (X > 0.56) & (X < 0.84) & (Y > 0.14) & (Y < 0.50)
        sky_night = np.array((0.17, 0.19, 0.25), F32); sky_dawn = np.array((0.95, 0.80, 0.55), F32)   # 해가 뜬 뒤: 금빛
        sky = sky_night * (1 - dawn) + sky_dawn * dawn
        cl = np.clip(0.5 + 0.6 * _noise(h, w, 77, 90) * (1 - 0.6 * dawn), 0, 1)
        skyimg = sky[None, None, :] * (0.75 + 0.35 * cl[..., None]) * (1 - 0.25 * dawn * (1 - np.clip((Y - 0.14) / 0.36, 0, 1)))[..., None] + flash * 0.9
        img[win] = skyimg[win]
        if rain > 0:                                                         # 붓으로 그린 비(창 안쪽만)
            if not hasattr(self, 'inkrain'):
                from rain import InkRain
                x0, x1, y0, y1 = int(0.56 * w), int(0.84 * w), int(0.14 * h), int(0.50 * h)
                self.win_box = (x0, x1, y0, y1)
                self.inkrain = InkRain(x1 - x0, y1 - y0, angle=-16, seed=13, fib=self.fiber[y0:y1, x0:x1] * 2, scale=1.4)
            x0, x1, y0, y1 = self.win_box
            rn = self.inkrain.render(t, amount=rain, gust=0.8)
            sub = img[y0:y1, x0:x1]
            img[y0:y1, x0:x1] = sub * np.exp(-(rn * 0.9 * rain * (1 - 0.6 * dawn))[..., None] * np.array((1.0, 1.0, 0.95), F32))
        # 창틀·문살·열린 창짝
        fr = np.zeros((h, w), F32)
        for (a, b) in (((0.555, 0.135), (0.845, 0.135)), ((0.555, 0.505), (0.845, 0.505)), ((0.557, 0.135), (0.557, 0.505)), ((0.843, 0.135), (0.843, 0.505))):
            self.line(fr, a, b, 0.010)
        self.poly(fr, [(0.845, 0.135), (0.905, 0.10), (0.905, 0.545), (0.845, 0.505)])          # 바깥으로 열린 창짝(옆면)
        jang = np.zeros((h, w), F32)
        self.poly(jang, [(0.851, 0.15), (0.899, 0.125), (0.899, 0.52), (0.851, 0.49)])
        img = img * (1 - fr[..., None]) + fr[..., None] * np.array((0.035, 0.028, 0.022), F32)
        lat = ((np.abs(((X - 0.851) / 0.012) % 1 - 0.5) < 0.12) | (np.abs(((Y - 0.12) / 0.04) % 1 - 0.5) < 0.06)).astype(F32)
        jcol = np.array((0.30, 0.27, 0.22), F32) * (0.4 + 0.6 * lamp_on) + sky * 0.3 + flash * 0.5
        img = img * (1 - jang[..., None]) + jang[..., None] * (jcol * (1 - 0.6 * lat[..., None]))
        # 서안과 종이
        dk = np.zeros((h, w), F32)
        self.poly(dk, [(0.53, 0.655), (0.86, 0.655), (0.86, 0.672), (0.53, 0.672)])
        for lx in (0.545, 0.845):
            self.poly(dk, [(lx - 0.006, 0.672), (lx + 0.006, 0.672), (lx + 0.006, 0.80), (lx - 0.006, 0.80)])
        img = img * (1 - dk[..., None]) + dk[..., None] * np.array((0.07, 0.045, 0.03), F32)
        pp = np.zeros((h, w), F32)
        self.poly(pp, [(0.545, 0.655), (0.845, 0.655), (0.835, 0.643), (0.553, 0.643)])
        pcol = np.array((0.78, 0.72, 0.60), F32)
        if paper_ink is not None:
            pcol = pcol * (1 - 0.15 * paper_ink)
        img = img * (1 - pp[..., None]) + pp[..., None] * pcol
        # 바구니(잘라 낸 귀퉁이들)
        if basket:
            bk = np.zeros((h, w), F32)
            self.poly(bk, [(0.12, 0.755), (0.255, 0.755), (0.24, 0.86), (0.135, 0.86)])
            sc = np.zeros((h, w), F32); dots = np.zeros((h, w), F32)
            for (a, b, c, d, e) in self.scraps:
                cx, cy = 0.13 + a * 0.115, 0.742 + b * 0.025
                ang = (c - 0.5) * 1.8; s = 0.012 + 0.012 * d
                tri = [(cx + s * math.cos(ang + k * 2.1) * (1.4 if k == 0 else 1), cy + s * 0.55 * math.sin(ang + k * 2.1)) for k in range(3)]
                self.poly(sc, tri)
                self.circle(dots, (cx + (e - 0.5) * s * 0.6, cy), 0.0028 + 0.002 * e)
            weave = (np.abs(((Y - 0.755) / 0.012) % 1 - 0.5) < 0.18).astype(F32) * 0.5 + (np.abs(((X - 0.12) / 0.01) % 1 - 0.5) < 0.12).astype(F32) * 0.3
            img = img * (1 - bk[..., None]) + bk[..., None] * (np.array((0.16, 0.11, 0.06), F32) * (1 - 0.4 * weave[..., None]))
            sc = sc * (1 - bk * 0.0)
            img = img * (1 - sc[..., None]) + sc[..., None] * np.array((0.72, 0.66, 0.55), F32)
            img = img * (1 - 0.85 * (dots * sc)[..., None])
        # 등잔대
        lp = np.zeros((h, w), F32)
        self.line(lp, (0.495, 0.80), (0.495, 0.585), 0.004)
        self.poly(lp, [(0.478, 0.585), (0.512, 0.585), (0.505, 0.592), (0.485, 0.592)])
        self.poly(lp, [(0.482, 0.80), (0.508, 0.80), (0.502, 0.79), (0.488, 0.79)])
        img = img * (1 - lp[..., None]) + lp[..., None] * np.array((0.05, 0.035, 0.025), F32)
        # 화가
        fig = self.figure(pose, tremor)
        # 등잔 빛: 화가 그림자를 뒤 벽에 크게 던진다
        lx, ly = 0.495, 0.575
        fl = 1 + 0.06 * math.sin(t * 23) + 0.04 * math.sin(t * 37)
        if lamp_on > 0:
            S = 1.9
            M = np.array([[S, 0, (1 - S) * lx * w], [0, S, (1 - S) * ly * h]], F32)
            shadow = cv2.warpAffine(fig, M, (w, h))
            shadow = cv2.GaussianBlur(shadow, (0, 0), 6 * SS) * (Y < 0.80)
            r = np.hypot((X - lx) * 1.7, Y - ly)
            glow = np.exp(-(r / 0.42) ** 2) * 2.2 + np.exp(-(r / 0.05) ** 2) * 1.5
            warm = np.array((1.0, 0.70, 0.38), F32)
            lit = 1 + glow[..., None] * warm * lamp_on * fl * (1 - 0.9 * np.clip(shadow * 1.4, 0, 1)[..., None])
            img = img * lit
        # 창빛(밤 푸른빛 / 새벽)
        r2 = np.hypot((X - 0.70) * 0.9, (Y - 0.40) * 1.2)
        wl = np.exp(-(r2 / 0.45) ** 2) * (0.35 + 1.2 * dawn + 2.0 * flash)
        wl = wl * (1 - win)
        img = img * (1 + wl[..., None] * (sky / max(sky.max(), 1e-3)) * 0.8)
        # 새벽 햇살: 창에서 왼쪽 아래로 들어오는 빛기둥 + 바닥·벽에 떨어진 창 모양 빛
        if dawn > 0:
            dx, dy = -0.30, 0.50
            win_pts = [(0.56, 0.14), (0.84, 0.14), (0.84, 0.50), (0.56, 0.50)]
            beam = np.zeros((h, w), F32)
            hull = cv2.convexHull(self.P(win_pts + [(x + dx, y + dy) for x, y in win_pts]))
            cv2.fillConvexPoly(beam, hull, 1.0, cv2.LINE_AA)
            fade = np.clip(1.0 - np.hypot(X - 0.70, Y - 0.32) / 0.75, 0, 1)
            beam = cv2.GaussianBlur(beam, (0, 0), 14 * SS) * fade
            patch = np.zeros((h, w), F32)                                    # 바닥에 떨어진 창 모양 빛(원근으로 납작한 사다리꼴)
            self.poly(patch, [(0.31, 0.83), (0.57, 0.83), (0.51, 0.95), (0.23, 0.95)])
            patch = cv2.GaussianBlur(patch, (0, 0), 7 * SS) * 0.6
            warm = np.array((1.0, 0.82, 0.55), F32)
            img = img * (1 + (beam * 0.9 * dawn)[..., None] * warm) + (beam * 0.05 * dawn)[..., None] * warm
            img = img + (patch * 0.30 * dawn)[..., None] * warm
            fig_lit = fig * 0                                                 # (화가는 빛 속 실루엣)
        # 화가는 검은 실루엣 + 등잔/창 쪽 가장자리 빛
        edge = np.clip(fig - cv2.GaussianBlur(np.roll(fig, -3 * SS, 1), (0, 0), 1.2 * SS), 0, 1)
        figcol = np.array((0.018, 0.015, 0.014), F32)[None, None, :] + edge[..., None] * (
            np.array((0.55, 0.32, 0.12), F32) * lamp_on + np.array((0.35, 0.33, 0.30), F32) * dawn + flash * 0.6)
        img = img * (1 - fig[..., None]) + figcol * fig[..., None]
        # 불꽃
        if lamp_on > 0:
            fcm = np.zeros((h, w), F32)
            self.poly(fcm, [(lx - 0.004, 0.583), (lx + 0.004, 0.583), (lx + 0.001 * math.sin(t * 17), 0.562)])
            img = img + cv2.GaussianBlur(fcm, (0, 0), 1.5 * SS)[..., None] * np.array((1.0, 0.85, 0.5), F32) * lamp_on * 1.5
        # 종이 결·그레인 → 축소
        img = img * (1 + 0.05 * (self.fiber[..., None] - 0.25))
        img = cv2.resize(img, (self.W, self.H), interpolation=cv2.INTER_AREA)
        return np.clip(img, 0, 1.2)
