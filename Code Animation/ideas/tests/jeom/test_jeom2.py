"""〈점〉 무음 움직임 시험 v3 — '번짐 사슬' 모델. 각 프레임은 t의 순수 함수.

점은 미끄러지지 않는다. 새 물웅덩이에 닿으면 그 속으로 피어나듯 번지고(블룸),
떠난 자리는 옅은 얼룩으로 남는다. 번질수록 옅어지고, 튄 먹과 합쳐지면 진해진다.
비가 그치면 가장자리부터 말라 테두리가 진해진다. 마지막에 물 없이 세 번에 걸쳐 스스로 모인다(규칙 깨기).
"""
import sys, os, math, subprocess
import numpy as np, cv2
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ink2 import Paper, Drop, render, sstep, S, SW, SH, W_, H_, F32
from ink import dry_stroke

pp = Paper()
from ink import fbm
NZ = fbm(SW, SH, 91, 4, 6)
yy, xx = np.mgrid[0:SH, 0:SW].astype(F32)


def ramp(t, a, b):
    return float(np.clip((t - a) / (b - a), 0, 1))


def ease(u):
    return u * u * (3 - 2 * u)


# ---- 물(젖음): 방울마다 섬유를 따라 퍼진 영역
DROPS = [Drop(-0.9, 560, 640, 72, 0.18), Drop(1.25, 690, 610, 118, 0.33), Drop(3.0, 835, 540, 108, 0.33)]
RAIN_STOP = (5.0, 5.9)


def wet_of(d, t):
    R = d.R(t)
    if R <= 0:
        return np.zeros((SH, SW), F32)
    T = pp.arrival(d.cx, d.cy)
    m = sstep(R - T, -2.0, 6.0)
    dry = 0.85 * ease(ramp(t, *RAIN_STOP))
    if d is DROPS[0]:
        dry = max(dry, 0.45 * ease(ramp(t, 0.2, 1.2)) * (1 - ramp(t, 1.25, 1.6)))
    return np.clip((m - dry) / (1 - dry), 0, 1)


def wet(t):
    m = np.zeros((SH, SW), F32)
    for d in DROPS:
        m = np.maximum(m, wet_of(d, t))
    return m


# ---- 먹: 단계(블룸)마다 접촉점에서 섬유를 따라 번진 모양
class Stage:
    def __init__(self, t0, contact, Rf, tau, level, region_drops):
        self.t0, self.contact, self.Rf, self.tau, self.level = t0, contact, Rf, tau, level
        self.T = pp.arrival(*contact)
        reg = np.zeros((SH, SW), F32)
        for d in region_drops:
            reg = np.maximum(reg, sstep(d.Rmax - pp.arrival(d.cx, d.cy), -2.0, 8.0))
        self.region = reg

    def shape(self, t):
        if t < self.t0:
            return None
        R = self.Rf * (1 - math.exp(-(t - self.t0) / self.tau))
        body = sstep(R - self.T, -1.5, 5.0) * self.region
        grad = 1 - 0.35 * np.clip(self.T / self.Rf, 0, 1)       # 접촉점 쪽이 조금 진함
        return body * grad, R


STAGES = [
    Stage(-0.9, (560, 640), 52, 0.18, 1.55, [DROPS[0]]),
    Stage(1.45, (628, 626), 128, 0.55, 0.85, [DROPS[0], DROPS[1]]),
    Stage(3.2, (760, 578), 120, 0.55, 0.40, [DROPS[1], DROPS[2]]),
]
SPECKS = [(885, 515, 14, 2.0, True), (925, 488, 7, 1.6, False)]     # (x, y, r, 진하기, 녹는가)
SPECK_REACH = 3.95


def speck_field(x, y, r, amt):
    d2 = ((xx - x / S) ** 2 + (yy - y / S) ** 2) / (r / S) ** 2
    ang = np.arctan2(yy - y / S, xx - x / S)
    return amt * np.exp(-d2 * 2.5 * (1 + 0.25 * np.cos(ang * 3 + x)))


GATHER = [(6.0, 0.62), (6.62, 0.6), (7.24, 0.5)]   # (시각, 배율)
SWELL = 1.05                                        # 예비 동작: 2프레임(투스 1장) 부풀었다가
_center = {}


def gather_scale(t):
    s = 1.0
    for tg, sc in GATHER:
        if t >= tg:
            s *= sc
        elif t >= tg - 1 / 12:
            s *= SWELL
            break
        else:
            break
    return s


def density(t):
    dens = np.zeros((SH, SW), F32)
    live = None
    for k, st in enumerate(STAGES):
        r = st.shape(t)
        if r is None:
            continue
        body, R = r
        lvl = st.level
        # 다음 단계가 먹을 끌어가면 이 자리는 옅은 얼룩으로 남는다
        if k + 1 < len(STAGES):
            lvl *= 1 - 0.62 * ease(ramp(t, STAGES[k + 1].t0, STAGES[k + 1].t0 + 0.9))
        # 튄 먹과 합쳐지면 진해진다
        if k == 2:
            lvl += 0.22 * ease(ramp(t, SPECK_REACH, SPECK_REACH + 0.7))
        # 마르면 테두리가 진해진다
        dry = ease(ramp(t, *RAIN_STOP)) if k > 0 else max(ease(ramp(t, 0.2, 1.2)) * 0.7, ease(ramp(t, *RAIN_STOP)))
        rim = sstep(R - st.T, -1.0, 2.0) * (1 - sstep(R - st.T, 2.0, 7.0)) * st.region
        f = body * lvl * (1 + 0.08 * NZ) + rim * lvl * 0.55 * dry
        if k == len(STAGES) - 1:
            live = f
        else:
            dens += f
    for (x, y, r, amt, melts) in SPECKS:
        a = amt * (1 - ease(ramp(t, SPECK_REACH, SPECK_REACH + 0.5))) if melts else amt
        dens += speck_field(x, y, r, a)
    if live is not None:
        s = gather_scale(t)
        if s != 1.0:
            if 'c' not in _center:
                w = live
                _center['c'] = (float((w * xx).sum() / w.sum()), float((w * yy).sum() / w.sum()))
            cx, cy = _center['c']
            mx = (cx + (xx - cx) / s).astype(F32); my = (cy + (yy - cy) / s).astype(F32)
            g = cv2.remap(live, mx, my, cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT) / (s * s)
            g = cv2.GaussianBlur(g, (0, 0), 0.7)
            g = 3.2 * np.tanh(g / 3.2)
            # 모이는 동안 섬유에 걸린 먹이 아주 옅게 남는다
            live = live * 0.07 + g * 0.93
        dens += live
    return dens


from brush import stroke as brush_stroke
stroke = brush_stroke([(1120, -80), (1330, 90), (1540, 230), (1780, 300), (2020, 290)], 170, 4, 1.7)


def frame(t):
    th = math.floor(t * 12) / 12
    beads = []
    for d in DROPS[1:]:
        if d.t0 - 1 / 12 <= th < d.t0 + 1 / 12:
            beads.append((d.cx, d.cy, 30 if th < d.t0 else 21, 1.0 if th < d.t0 else 0.5))
    return render(pp, (density(th), wet(th)), extra=stroke, t=th, beads=beads)


if __name__ == '__main__':
    out = sys.argv[1] if len(sys.argv) > 1 else 'jeom_test_8s.mp4'
    os.makedirs('frames', exist_ok=True)
    FPS, DUR = 24, 8.0
    last = None
    for fi in range(int(DUR * FPS)):
        t = fi / FPS; th = math.floor(t * 12) / 12
        if last is None or last[0] != th:
            img = frame(t)
            last = (th, (img[..., ::-1] * 255 + 0.5).astype(np.uint8))
        cv2.imwrite(f'frames/f{fi:04d}.png', last[1])
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-framerate', '24', '-i', 'frames/f%04d.png',
                    '-c:v', 'libx264', '-crf', '18', '-pix_fmt', 'yuv420p',
                    '-vf', 'colorspace=all=bt709:iall=bt709', out])
