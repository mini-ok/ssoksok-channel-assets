"""마른 붓 한 획(용의 몸). 곡선 보간 + 붓털 수십 가닥 + 비백(먹이 떨어지며 갈라짐) + 시작 눌림·끝 삐침."""
import math, numpy as np, cv2
from ink import fbm
F32 = np.float32
W_, H_ = 1920, 1080

def catmull(pts, n=400):
    P = np.array(pts, F32); P = np.vstack([P[0], P, P[-1]])
    out = []
    for i in range(1, len(P) - 2):
        p0, p1, p2, p3 = P[i - 1], P[i], P[i + 1], P[i + 2]
        for u in np.linspace(0, 1, n // (len(P) - 3), endpoint=False):
            u2, u3 = u * u, u * u * u
            out.append(0.5 * ((2 * p1) + (-p0 + p2) * u + (2 * p0 - 5 * p1 + 4 * p2 - p3) * u2 + (-p0 + 3 * p1 - 3 * p2 + p3) * u3))
    out.append(P[-2]); return np.array(out, F32)

def stroke(pts, width, seed, density=1.6):
    r = np.random.default_rng(seed)
    c = catmull(pts, 900)
    seg = np.linalg.norm(np.diff(c, axis=0), axis=1); s = np.concatenate([[0], np.cumsum(seg)]); L = s[-1]
    t = np.linspace(0, L, int(L / 1.2)); xs = np.interp(t, s, c[:, 0]); ys = np.interp(t, s, c[:, 1])
    tx, ty = np.gradient(xs), np.gradient(ys); nn = np.hypot(tx, ty) + 1e-6; nx, ny = -ty / nn, tx / nn
    u = t / L
    press = np.clip(np.minimum(u / 0.08, 1) ** 0.6 * (1 - 0.55 * u) + 0.05, 0, 1)    # 눌러 시작해 가늘어짐
    img = np.zeros((H_, W_), F32)
    nb = 220
    noise1d = fbm(len(t), 8, seed + 5, 4, 6)[4]          # 길이 방향 먹 양 변화
    for b in range(nb):
        off = r.uniform(-0.5, 0.5)
        ink = r.uniform(0.5, 1.0)
        dry_at = r.uniform(0.45, 1.1) - abs(off) * 0.5    # 바깥 털부터 먹이 마른다
        gap_f = r.uniform(0.02, 0.06); gap_ph = r.uniform(0, 6.28)
        amt = ink * np.clip((dry_at - u) / 0.12, 0, 1) * (0.8 + 0.2 * noise1d)
        # 비백: 털마다 아주 느린 먹 변화 → 획 뒤쪽에서만 긴 흰 결로 끊긴다
        slow = np.sin(t * gap_f * 0.12 + gap_ph) + 0.6 * np.sin(t * gap_f * 0.31 + gap_ph * 2.1)
        cut = np.clip((slow + 1.2 - 2.4 * np.clip(u - 0.25, 0, 1)) * 2.0, 0, 1)
        amt *= cut
        bx = xs + nx * off * width * press; by = ys + ny * off * width * press
        P = np.stack([bx, by], 1)
        for i in range(0, len(t) - 2, 2):
            a = float(amt[i])
            if a < 0.04: continue
            cv2.line(img, tuple(np.round(P[i] * 4).astype(int)), tuple(np.round(P[i + 2] * 4).astype(int)), a, 4, cv2.LINE_AA, shift=2)
    img = cv2.GaussianBlur(img, (0, 0), 1.0)
    img = 1 - np.exp(-img * 1.6)                           # 겹친 털이 포화
    return img * density
