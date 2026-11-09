"""〈점〉 표현 시험: 눈물 한 방울이 빈 눈자리에 떨어져 눈동자 테가 된다(7초, 960×540, 투스).
아침. 종이에는 용이 떠난 흔적(25%)과, 눈동자였던 점의 흔적도 옅게 남아 있다.
화가의 머리 그림자(창빛: 오른쪽 위)가 종이에 걸려 있고, 눈물방울은 눈자리 바로 위에서 떨어진다 —
방울은 제자리에 있고 방울 그림자가 방울로 모여드는 순간 닿는다(2장 먹방울과 같은 방식).
닿으면 물이 번지며 옅게 남은 점의 먹을 다시 녹이고, 마르면서 먹이 가장자리로 모인다(커피 테 효과) → 진한 테 = 눈동자.
"""
import sys, os, math, subprocess
HERE = os.path.dirname(os.path.abspath(__file__)); JE = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(JE, 'engine'))
import numpy as np, cv2
from paper import View, paper_layers, paper_rgb
from brush import render_strokes
from look import INK_ABS, light, film, letterbox
import dragon

F32 = np.float32
W, H = 960, 540; FPS = 12; DUR = 7.0
E = np.array(dragon.E); C = E + np.array((1.0, 0.0))        # 눈동자 중심(본편 점 자리)
V = View(E[0] + 2, E[1] + 1, 74, W, H)
CACHE = os.path.join(JE, 'cache', 'tear'); os.makedirs(CACHE, exist_ok=True)

def ease(u): return u * u * (3 - 2 * u)
def ramp(t, a, b): return float(np.clip((t - a) / (b - a), 0, 1))

fn = os.path.join(CACHE, 'plate.npz')
if os.path.exists(fn):
    z = np.load(fn); RGB, FIB, GHOST, X, Y = z['rgb'], z['fib'], z['g'], z['x'], z['y']
else:
    FIB, flk, mot, X, Y = paper_layers(V)
    RGB = paper_rgb(FIB, flk, mot).astype(F32)
    st = [s for s in dragon.strokes() if not s.name.startswith('cloud')]
    GHOST = (render_strokes(V, st, FIB) * dragon.eye_blank(X, Y) * 0.25).astype(F32)
    np.savez_compressed(fn, rgb=RGB, fib=FIB.astype(F32), g=GHOST, x=X, y=Y)
FIB = FIB.astype(F32)
R = np.hypot(X - C[0], Y - C[1]).astype(F32)
ANG = np.arctan2(Y - C[1], X - C[0])
WOB = 1 + 0.035 * np.sin(ANG * 3 + 1.1) + 0.015 * np.sin(ANG * 5 + 0.4) + 0.02 * (FIB - 0.3)       # 물 가장자리의 불규칙
# 눈동자였던 점의 흔적(섬유에 남은 25%)
OLD = (0.10 * 2.4 * np.clip((4.3 - R) / 0.8, 0, 1) * (0.85 + 0.3 * FIB)).astype(F32)

T_DROP = 2.6; FALL = 0.30; R_MAX = 4.5

def tear_state(t):
    """물이 닿은 반경 r, 젖음 w(0..1), 테로 모인 정도 g(0..1)."""
    land = T_DROP + FALL
    if t < land: return 0.0, 0.0, 0.0
    u = t - land
    r = R_MAX * (1 - math.exp(-u / 0.18))
    w = 1.0 - ramp(t, land + 1.2, land + 3.6) * 0.85
    g = ease(ramp(t, land + 0.25, land + 3.4))
    return r, w, g

def frame(t):
    r, w, g = tear_state(t)
    inside = np.clip((r * WOB - R) / 0.25, 0, 1) if r > 0 else np.zeros_like(R)
    # 물 안의 먹은 녹아 가장자리로 옮겨 간다(총량 보존)
    mass = float((OLD * inside).sum())
    remain = OLD * (1 - inside * g * 0.8)
    if r > 0:
        q = np.clip(R / (r * WOB), 0, 1.2)
        prof = inside * q ** 7 + 0.55 * np.exp(-((R - r * WOB) / 0.28) ** 2)      # 가장자리로 갈수록 진하고, 테에 고인다
        prof = prof * (0.75 + 0.5 * FIB)
        ring = prof * (mass * 0.8 * g / (float(prof.sum()) + 1e-6)) + prof * 0.75 * g
        ring = cv2.GaussianBlur(ring.astype(F32), (0, 0), 0.6)
    else:
        ring = 0 * R
    dens = GHOST + remain + ring
    img = RGB * np.exp(-dens[..., None] * INK_ABS)
    img = img * (1 - 0.05 * (inside * w)[..., None])                             # 젖은 종이는 살짝 어둡다
    # 머리 그림자(창빛: 오른쪽 위 → 그림자는 왼쪽 아래로 드리운다; 머리는 화면 위·오른쪽)
    breathe = 0.6 * math.sin(t * 1.3)
    hx, hy = C[0] + 13 + breathe, C[1] - 15
    sh = np.exp(-(((X - hx) / 15) ** 2 + ((Y - hy) / 12) ** 2) * 1.5)
    sh = sh + np.exp(-(((X - hx - 14) / 20) ** 2 + ((Y - hy + 12) / 18) ** 2) * 1.5)      # 어깨
    img = img * (1 - 0.30 * np.clip(sh, 0, 1)[..., None])
    # 눈물방울: 제자리, 그림자가 오른쪽 위에서 방울로 모여든다
    if T_DROP - 0.6 <= t < T_DROP + FALL:
        hgt = 40.0 if t < T_DROP else 40.0 * (1 - ((t - T_DROP) / FALL) ** 2)
        sxm, sym = C[0] + 0.55 * hgt * 0.5, C[1] - 0.85 * hgt * 0.5
        sm = np.exp(-(((X - sxm) ** 2 + (Y - sym) ** 2) / (1.1 + 0.03 * hgt) ** 2))
        img = img * (1 - 0.35 * sm[..., None])
        if t >= T_DROP:                                                          # 떨어지는 방울(맑은 물: 가장자리만 어둡고 속은 밝게)
            rr = 1.3 * (1 + 0.15 * (1 - (t - T_DROP) / FALL))
            dd = np.hypot(X - C[0], Y - C[1])
            edge = np.exp(-((dd - rr) / 0.25) ** 2); core = np.clip((rr - dd) / 0.4, 0, 1)
            img = img * (1 - 0.25 * edge[..., None]) + 0.12 * core[..., None] * np.exp(-((X - C[0] + 0.4) ** 2 + (Y - C[1] + 0.4) ** 2) / 0.3)[..., None]
    # 물기 반사광(젖어 있는 동안)
    if r > 0:
        hl = np.exp(-(((X - C[0] + 0.35 * r) ** 2 + (Y - C[1] + 0.35 * r) ** 2) / (0.35 * r + 0.3) ** 2)) * w * inside
        img = img + (hl * 0.35)[..., None]
    img = light(img, 'morning')
    img = film(img, t, H=H, W=W, vig=0.22, grain=0.011, weave=0.3)
    img = letterbox(img)
    return (np.clip(img, 0, 1)[..., ::-1] * 255 + 0.5).astype(np.uint8)

if __name__ == '__main__':
    out = os.path.join(CACHE, 'f'); os.makedirs(out, exist_ok=True)
    FR = []
    for k in range(int(DUR * FPS)):
        f = frame(k / FPS); FR.append(f); cv2.imwrite(os.path.join(out, f't{k:04d}.png'), f)
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-framerate', str(FPS), '-i', os.path.join(out, 't%04d.png'),
                    '-vf', 'fps=24', '-c:v', 'libx264', '-crf', '18', '-pix_fmt', 'yuv420p', os.path.join(JE, 'cache', 'tear_test.mp4')])
    pick = [12, 29, 33, 36, 50, 83]
    cv2.imwrite(os.path.join(JE, 'cache', 'tear_test_sheet.jpg'),
                cv2.resize(np.vstack([np.hstack([FR[i] for i in pick[:3]]), np.hstack([FR[i] for i in pick[3:]])]), (1440, 540)), [cv2.IMWRITE_JPEG_QUALITY, 90])
    print('ok')
