"""〈점〉 표현 시험: 창밖 폭풍 속 — 용이 먹구름을 휘감아 비를 거둔다(8초, 960×540, 투스).
용은 솟아오름 시험(test_leap)과 같은 '그림 그대로의 획' 리그. 머리 길만 이 장면용으로 바꾼다.
행동: 아래 왼쪽에서 솟아 들어와 → 화면 가운데를 축으로 나선을 그리며 멀어지고 → 그 움직임이 구름을 소용돌이로 끌어들인다 →
용이 소용돌이 눈으로 들어가면 구름이 안으로 빨려 닫힌다 → 빗줄기가 줄어 멎고 → 하늘이 은빛으로 갠다(마지막 빗방울 몇 개).
"""
import sys, os, math, subprocess
HERE = os.path.dirname(os.path.abspath(__file__)); JE = os.path.dirname(HERE)
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(JE, 'engine'))
import numpy as np, cv2
import test_leap as L
import test_flight as TF
from brush import render_strokes
from look import INK_ABS, light, film, letterbox

F32 = np.float32
W, H, FPS, DUR = L.W, L.H, 12, 8.0
CACHE = os.path.join(JE, 'cache', 'storm'); os.makedirs(CACHE, exist_ok=True)
def ease(u): return u * u * (3 - 2 * u)
def ramp(t, a, b): return float(np.clip((t - a) / (b - a), 0, 1))

# ---------------------------------------------------------------- 머리 길(카메라는 원점, +z를 봄)
KEYS = np.array([(-16, -12, 8), (-10, -7.5, 7.2), (-6, -5, 7), (-3, -2.6, 6.2), (1.5, -1.9, 6.6), (3.1, 0.4, 7.6), (0.6, 2.3, 8.6),
                 (-2.5, 0.9, 9.4), (-1.3, -1.0, 10.5), (0.9, -0.3, 11.5), (0.3, 0.5, 12.8), (0.0, 0.3, 15.0), (0.0, 0.3, 22.0), (0.0, 0.3, 40.0)], float)
KT = np.array([-3.0, -1.5, 0.0, 1.0, 2.0, 2.7, 3.4, 4.1, 4.8, 5.4, 5.9, 6.3, 6.8, 7.6])
def head_path(tau):
    tau = np.atleast_1d(np.asarray(tau, float))
    P = np.vstack([KEYS[:1] * 2 - KEYS[1:2], KEYS, KEYS[-1:] * 2 - KEYS[-2:-1]])
    i = np.clip(np.searchsorted(KT, tau, side='right') - 1, 0, len(KT) - 2)
    u = np.clip((tau - KT[i]) / (KT[i + 1] - KT[i]), 0, 1.5)[:, None]
    p0, p1, p2, p3 = P[i], P[i + 1], P[i + 2], P[i + 3]
    return 0.5 * ((2 * p1) + (-p0 + p2) * u + (2 * p0 - 5 * p1 + 4 * p2 - p3) * u ** 2 + (-p0 + 3 * p1 - 3 * p2 + p3) * u ** 3)

def trail(t):
    taus = np.linspace(t - 4.5, t, 500)
    pts = head_path(taus)
    seg = np.linalg.norm(np.diff(pts, axis=0), axis=1); cum = np.concatenate([[0], np.cumsum(seg)])
    return pts, cum
L.trail = trail                                      # 리그는 그대로, 길만 바꾼다
L.CAM['pos'] = np.zeros(3); L.CAM['tilt'] = 0.0

# ---------------------------------------------------------------- 하늘·구름 소용돌이
CL1, CL2 = TF.CL1, TF.CL2
VC = np.array((W * 0.5, H * 0.45))                   # 소용돌이 눈(화면)
yy, xx = np.mgrid[0:H, 0:W].astype(F32)
DX, DY = xx - VC[0], yy - VC[1]
RR = np.hypot(DX, DY) + 1e-3; TH = np.arctan2(DY, DX)

def clouds(t, swirl, suck, clear):
    """swirl: 소용돌이 회전량(라디안), suck: 안으로 빨림(0..1), clear: 갬(0..1)."""
    rot = swirl * np.exp(-RR / 210.0) * (1 + 0.25 * cv2.resize(CL2[:60, :100], (W, H)))
    rs = RR * (1 + 1.4 * suck * np.exp(-RR / 400.0))            # 바깥 것을 안으로 끌어들인다
    sx = VC[0] + rs * np.cos(TH + rot) + 30 * t; sy = VC[1] + rs * np.sin(TH + rot) + 10 * t
    a = cv2.remap(CL1, (sx + 200).astype(F32), (sy + 100).astype(F32), cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
    b = cv2.remap(CL2, (sx * 0.8 + 200).astype(F32), (sy * 0.8 + 100).astype(F32), cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
    yv = yy / H
    base = 0.10 + 0.12 * yv
    far = TF.wash(b + 0.35, 0.40) * 0.55
    near = TF.wash(a + 0.25 * b + 0.25, 0.55) * 0.95
    eye = np.exp(-(RR / (60 + 160 * suck)) ** 2) * 0.9 * min(1.0, swirl / 3) * (1 - clear)   # 소용돌이 눈의 짙은 먹
    d = base + (far + near) * (0.75 + 0.5 * np.clip(TF.FIB * 1.3, 0, 1.3)) * (1 - 0.85 * clear) + eye
    return d * (1 - 0.7 * clear) + 0.03 * clear

def flash(t):
    f = 0.0
    for tf, a in ((0.6, 0.9), (0.75, 0.5), (3.0, 0.8), (5.6, 1.0), (5.72, 0.5)):
        if t >= tf: f = max(f, a * math.exp(-(t - tf) / 0.12))
    return f

def render():
    fl = TF.Fluid(); FR = []; prev = None
    for k in range(int(DUR * FPS)):
        t = k / FPS
        swirl = 4.2 * ease(ramp(t, 2.2, 6.2))
        suck = ease(ramp(t, 5.3, 6.6))
        clear = ease(ramp(t, 6.4, 7.8))
        rain_amt = 1.0 - ease(ramp(t, 5.6, 6.9))
        fx = flash(t)
        # 용
        sts, pts, cum, bodyw = L.live_strokes(t)
        live = render_strokes(L.SV, sts, L.SFIB)
        S2, Z = L.project(pts[-60::4])
        vis = 1.0 - ease(ramp(t, 6.2, 6.9))                     # 소용돌이 눈으로 들어가 사라짐
        live = live * vis
        # 몸의 움직임이 공기를 끈다(빗줄기가 휜다) + 몸에서 풀린 먹
        if prev is not None:
            v = (S2[-1] - prev) * FPS
            for j in range(0, len(S2), 2):
                fl.splat(S2[j][0], S2[j][1], 0.03 * vis, v[0] * 0.6, v[1] * 0.6, 26)
        prev = S2[-1].copy()
        # 소용돌이 바람(유체에 회전 속도를 넣는다)
        if swirl > 0:
            wv = 60 * min(1.0, swirl / 4) * (1 - clear)
            u_s = (-DY / RR) * wv * np.exp(-RR / 300); v_s = (DX / RR) * wv * np.exp(-RR / 300)
            fl.u += cv2.resize(u_s, (TF.GW, TF.GH)) / TF.GS * 0.02; fl.v += cv2.resize(v_s, (TF.GW, TF.GH)) / TF.GS * 0.02
        for _ in range(2):
            fl.step(1 / (FPS * 2))
        smoke = cv2.resize(fl.d, (W, H), interpolation=cv2.INTER_CUBIC)
        smoke = 0.8 * np.tanh(np.clip(smoke, 0, None) * 1.2)
        dens = clouds(t, swirl, suck, clear) * (1 - 0.6 * fx) + smoke
        rn = TF.rain(t, fl)
        keep = (TF.rng.random(TF.NR) < rain_amt) if False else None
        dens = dens + rn * 0.30 * rain_amt * (1 - fx)
        a = np.clip(live * 1.5, 0, 1)
        dens = dens * (1 - a) + live * a
        img = TF.PAPER * np.exp(-dens[..., None] * INK_ABS)
        # 마지막 빗방울 몇 개(갠 하늘에 떨어지는 굵은 방울)
        if 6.6 < t < 7.8:
            rr2 = np.random.default_rng(int(t * 3))
            for j in range(3):
                x0 = rr2.uniform(100, W - 100); y0 = ((t - 6.6) * 500 + rr2.uniform(0, H)) % H
                cv2.line(img, (int(x0), int(y0)), (int(x0 - 3), int(y0 - 22)), (0.35, 0.36, 0.40), 1, cv2.LINE_AA)
        img = img * (1 + 0.35 * fx)
        night = light(img, 'night', extra=fx) * 0.45 + light(img, 'silver', extra=fx) * 0.75; silver = light(img, 'silver')
        img = night * (1 - clear) + silver * clear * 1.25
        # 갠 하늘: 구름 사이로 은빛이 번진다
        img = img + (clear * 0.10 * np.exp(-(RR / 380) ** 2))[..., None] * np.array((0.9, 0.92, 1.0), F32)
        img = film(img, t, H=H, W=W, vig=0.26, grain=0.013, weave=0.5)
        img = letterbox(img)
        f8 = (np.clip(img, 0, 1)[..., ::-1] * 255 + 0.5).astype(np.uint8)
        FR.append(f8); cv2.imwrite(os.path.join(CACHE, f's{k:04d}.png'), f8)
    return FR

if __name__ == '__main__':
    FR = render()
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-framerate', str(FPS), '-i', os.path.join(CACHE, 's%04d.png'),
                    '-vf', 'fps=24', '-c:v', 'libx264', '-crf', '18', '-pix_fmt', 'yuv420p', os.path.join(JE, 'cache', 'storm_test.mp4')])
    pick = [6, 18, 30, 42, 54, 66, 74, 82, 94]
    rows = [np.hstack([FR[i] for i in pick[r * 3:(r + 1) * 3]]) for r in range(3)]
    cv2.imwrite(os.path.join(JE, 'cache', 'storm_test_sheet.jpg'), cv2.resize(np.vstack(rows), (1440, 810)), [cv2.IMWRITE_JPEG_QUALITY, 90])
    print('ok', len(FR))
