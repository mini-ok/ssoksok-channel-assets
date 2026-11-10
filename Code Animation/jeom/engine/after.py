"""폭풍이 지나간 아침의 종이 — 엔딩의 '남은 그림'. 어떤 화면(View)에서든 같은 상태를 다시 그린다(C23 전체·C24 눈 근접이 일치하도록).
= 그림 속 구름 + 지워지다 만 용(아래로 흘러내린 먹, 섬유 잔류 20%) + 점이 지나간 길(70%) + 눈동자였던 점의 흔적(10%)
  + 날며 뿌린 먹방울(솟아오름 시험의 기록) + 빗물 자국.
"""
import math
import numpy as np, cv2
from brush import render_strokes, Wash
import dragon, inkmm

F32 = np.float32


def splat(view, fib, dens, x, y, r, seed, ang):
    rr = np.random.default_rng(int(seed))
    ca, sa = math.cos(ang), math.sin(ang)
    blobs = []
    for j in range(5):
        f = j / 4
        blobs.append((x + ca * r * 1.6 * f + rr.normal(0, r * 0.12), y + sa * r * 1.6 * f + rr.normal(0, r * 0.12), r * (1.0 - 0.55 * f) * rr.uniform(0.85, 1.1)))
    for j in range(int(rr.integers(3, 8))):
        a2 = ang + rr.normal(0, 0.45); dd = r * rr.uniform(2.2, 6.0)
        blobs.append((x + math.cos(a2) * dd, y + math.sin(a2) * dd, r * rr.uniform(0.10, 0.32)))
    for j in range(int(rr.integers(4, 12))):
        a2 = rr.uniform(0, 2 * np.pi); dd = r * rr.uniform(1.5, 4.0)
        blobs.append((x + math.cos(a2) * dd, y + math.sin(a2) * dd, r * rr.uniform(0.05, 0.12)))
    Wash(blobs[:5], load=rr.uniform(1.1, 1.7), soft=0.18, seed=int(seed), rim=0.5).render(view, dens, fib)
    for j, bb in enumerate(blobs[5:]):
        Wash([bb], load=rr.uniform(0.9, 1.5), soft=0.15, seed=int(seed) + j + 1, rim=0.3).render(view, dens, fib)


def after_density(view, fib, X, Y, D, drips, wets_mm, u=0.75):
    st = dragon.strokes()
    body = [s for s in st if not s.name.startswith('cloud')]
    cloud = render_strokes(view, [s for s in st if s.name.startswith('cloud')], fib)
    drg = render_strokes(view, body, fib) * dragon.eye_blank(X, Y)
    # 빗물에 흘러내린 먹: 한 덩어리 띠가 아니라 가늘고 길이가 제각각인 줄기(종이 x(mm)에 묶인 잡음 → 어느 화면에서도 같은 줄기)
    def run_of(Lmm):
        Lp = max(1, int(Lmm * u * view.ppm))
        k = np.zeros((2 * Lp + 1, 1), F32); k[Lp:, 0] = np.exp(-np.arange(Lp + 1) / max(1, Lp * 0.45)); k /= k.sum()
        return cv2.filter2D(drg.astype(F32), -1, k[::-1], borderType=cv2.BORDER_CONSTANT)
    xs = X[0] if X.ndim == 2 else X
    rr = np.random.default_rng(7)
    def colnoise(nw, lo, hi):
        v = np.zeros_like(xs, dtype=np.float64)
        for _ in range(nw):
            lam = rr.uniform(lo, hi); v += np.sin(2 * np.pi * xs / lam + rr.uniform(0, 6.28)) / nw ** 0.5
        return v
    streak = 0.6 + 0.4 * np.clip(0.5 + 0.5 * colnoise(7, 2.5, 14.0), 0, 1)   # 줄기마다 진하기가 조금씩 다르고
    longer = np.clip(0.5 + 0.7 * colnoise(6, 4.0, 24.0), 0, 1)               # 길게 흐른 곳/짧게 멎은 곳이 섞인다(끝이 들쭉날쭉)
    run = run_of(12) * (1 - longer) + run_of(34) * longer
    run = run * streak[None, :].astype(F32)
    runs = drg * (1 - 0.55 * u) + run * 0.85 * u
    dens_g = D.density(88.0); pup = D.pupil
    trail = inkmm.sample(dens_g - (pup if pup is not None else 0), view, X, Y)
    pv = inkmm.sample(pup, view, X, Y) if pup is not None else 0 * X
    dens = (cloud + runs * 0.20 + trail * 0.7 + pv * 0.10).astype(F32)
    x0, y0, x1, y1 = view.bbox_mm(0)
    for (x, y, r, seed, ang) in drips:
        if x0 - 30 < x < x1 + 30 and y0 - 30 < y < y1 + 30:
            splat(view, fib, dens, x, y, r * 0.6, seed, ang)               # 가까이서 볼 때 너무 큰 덩어리가 되지 않게
    wm = np.zeros(X.shape, F32)
    for (x, y, r) in wets_mm:
        if x0 - 10 < x < x1 + 10 and y0 - 10 < y < y1 + 10:
            px, py = view.to_px(x, y)
            cv2.circle(wm, (int(px), int(py)), max(1, int(r * view.ppm)), 1.0, -1, cv2.LINE_AA)
    wm = np.clip(cv2.GaussianBlur(wm, (0, 0), max(0.6, 1.5 * view.ppm)), 0, 1)
    return dens + 0.022 * wm, pv
