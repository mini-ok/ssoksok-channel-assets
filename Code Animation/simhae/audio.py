"""〈얼마나 깊을까〉 소리 — numpy 합성(샘플 없음). 시각은 scene.py에서 가져온다.
  python3 audio.py out.wav
"""
import os, sys, wave
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, '..', 'jeom', 'audio'))
import scene as SC                         # noqa: E402
from instruments import geomungo, buk      # noqa: E402
from sketch import reverb                  # noqa: E402

SR = 48000
DUR = SC.DUR
OUT = sys.argv[1] if len(sys.argv) > 1 else '/home/claude/work/simhae/audio.wav'
N = int(DUR * SR)
rng = np.random.default_rng(9)
fx = np.zeros(N); mus = np.zeros(N); amb = np.zeros(N)


def band(x, lo, hi, slope=2.0):
    X = np.fft.rfft(x); f = np.fft.rfftfreq(len(x), 1 / SR)
    g = 1 / (1 + (lo / np.maximum(f, 1)) ** (2 * slope)) / (1 + (f / hi) ** (2 * slope))
    return np.fft.irfft(X * g, len(x))


def norm(x): return x / (np.abs(x).max() + 1e-9)


def put(buf, t, x, g=1.0):
    i = int(t * SR); j = min(N, i + len(x))
    if i < N: buf[i:j] += g * x[:j - i]


def rustle(dur, g=1.0, crisp=0.5, seed=0):
    """종이 접힘·스침: 띠 잡음 + 섬유가 꺾이는 잔 틱. 모양은 앞뒤가 둥근 봉우리."""
    r = np.random.default_rng(seed); n = int(dur * SR); t = np.arange(n) / SR
    base = band(r.standard_normal(n), 900, 7000)
    ticks = np.zeros(n); k = r.random(n) < (0.004 + 0.02 * crisp); ticks[k] = r.standard_normal(k.sum())
    ticks = band(ticks, 2000, 11000)
    env = np.sin(np.pi * np.clip(t / dur, 0, 1)) ** 1.5 * (0.6 + 0.4 * band(r.standard_normal(n), 3, 25) * 8)
    return g * (0.5 * norm(base) + crisp * norm(ticks)) * np.clip(env, 0, None)


def snap(g=1.0, seed=0):
    """접는 선이 '탁' 서는 소리."""
    r = np.random.default_rng(seed); n = int(0.09 * SR); t = np.arange(n) / SR
    x = band(r.standard_normal(n), 1500, 9000) * np.exp(-t / 0.012) + 0.4 * band(r.standard_normal(n), 200, 900) * np.exp(-t / 0.02)
    return g * norm(x)


def plop(g=1.0):
    n = int(0.25 * SR); t = np.arange(n) / SR
    f = 900 * np.exp(-t / 0.05) + 380
    x = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / 0.045) + 0.5 * band(rng.standard_normal(n), 2000, 8000) * np.exp(-t / 0.004)
    return g * norm(x)


def tink(g=1.0, f0=2650):
    n = int(0.5 * SR); t = np.arange(n) / SR
    x = sum(a * np.sin(2 * np.pi * f0 * m * t) * np.exp(-t / (0.12 / m)) for m, a in [(1, 1), (2.31, 0.4), (3.9, 0.2)])
    return g * norm(x)


def hollow(dur, g=1.0):
    """빈 연적 속 공기의 울림(낮은 공명)."""
    n = int(dur * SR); t = np.arange(n) / SR
    x = band(rng.standard_normal(n), 380, 470, slope=6) + 0.4 * band(rng.standard_normal(n), 820, 900, slope=6)
    return g * norm(x) * np.sin(np.pi * t / dur) ** 2


def hiss(dur, g=1.0, lo=2500, hi=9000):
    n = int(dur * SR); t = np.arange(n) / SR
    return g * norm(band(rng.standard_normal(n), lo, hi)) * np.sin(np.pi * t / dur) ** 1.2


def pluck(f0, dur=1.2, g=1.0, bright=0.6):
    """밝게 튕긴 줄(가야금 결): 카플러스-스트롱."""
    n = int(dur * SR); p = max(2, int(SR / f0))
    buf = rng.uniform(-1, 1, p) * np.hanning(p) ** 0.3
    out = np.zeros(n); k = 0.5 + 0.49 * bright
    for i in range(n):
        x = buf[i % p]; out[i] = x
        buf[i % p] = (k * x + (1 - k) * buf[(i + 1) % p]) * 0.996
    env = np.exp(-np.arange(n) / SR / (dur * 0.35))
    return g * norm(out) * env


def bloop(g=1.0):
    n = int(0.5 * SR); t = np.arange(n) / SR
    f = 90 + 260 * np.exp(-t / 0.06)
    return g * np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / 0.18)


def swoosh(dur, g=1.0):
    n = int(dur * SR); t = np.arange(n) / SR
    x = band(rng.standard_normal(n), 300, 5000)
    return g * norm(x) * np.sin(np.pi * t / dur) ** 1.5



def lowpass_var(x, fc_curve):
    """깊어질수록 소리가 먹먹해진다: 시간에 따라 바뀌는 1차 저역 통과."""
    y = np.zeros_like(x); s = 0.0
    a = 1 - np.exp(-2 * np.pi * fc_curve / SR)
    for i in range(len(x)):
        s += a[i] * (x[i] - s); y[i] = s
    return y

def ping(f=1180, g=1.0):
    n = int(2.2 * SR); t = np.arange(n) / SR
    return g * (np.sin(2 * np.pi * f * t) * np.exp(-t / 0.5) + 0.3 * np.sin(2 * np.pi * f * 2.01 * t) * np.exp(-t / 0.25))

def whale_call(dur=3.5, g=1.0):
    n = int(dur * SR); t = np.arange(n) / SR
    f = 150 - 70 * (t / dur) + 15 * np.sin(2 * np.pi * 0.6 * t)
    ph = 2 * np.pi * np.cumsum(f) / SR
    x = np.sin(ph) + 0.5 * np.sin(2 * ph) + 0.25 * np.sin(3 * ph)
    return g * x * np.sin(np.pi * t / dur) ** 1.2

def bubbles(dur, n_b, g=1.0):
    out = np.zeros(int(dur * SR))
    for _ in range(n_b):
        st = int(rng.uniform(0, dur - 0.1) * SR); L = int(0.05 * SR); tt = np.arange(L) / SR
        f0 = rng.uniform(500, 1600); f = f0 * (1 + 2.5 * tt / 0.05)
        b = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-tt / 0.015)
        out[st:st + L] += b[:len(out) - st] * rng.uniform(0.3, 1)
    return g * out

def swoosh(dur, g=1.0):
    n = int(dur * SR); t = np.arange(n) / SR
    return g * norm(band(rng.standard_normal(n), 300, 5000)) * np.sin(np.pi * t / dur) ** 1.5

t = np.arange(N) / SR
depth = np.array([SC.depth_now(x) for x in np.arange(0, DUR, 0.05)])
dcurve = np.interp(t, np.arange(0, DUR, 0.05), depth)

# ---- 바다 위: 파도 / 물속: 웅웅대는 물 — 깊을수록 낮고 먹먹하게
waves = band(rng.standard_normal(N), 200, 3000) * (0.6 + 0.4 * np.sin(2 * np.pi * 0.12 * t) ** 2)
amb += 0.05 * norm(waves) * np.clip((SC.T_DIVE - t) / 0.4, 0, 1)
under = band(rng.standard_normal(N), 40, 900)
fc = 900 * np.exp(-dcurve / 1200) + 90
under = lowpass_var(under, fc)
inside = np.clip((t - SC.T_DIVE) / 0.3, 0, 1) * np.clip((SC.T_PAY - t) / 0.8, 0, 1)
amb += 0.06 * norm(under) * inside * (0.8 + 0.4 * np.clip(dcurve / 6000, 0, 1))
drone = np.sin(2 * np.pi * 49 * t) * 0.5 + np.sin(2 * np.pi * 73.4 * t) * 0.3
amb += 0.02 * drone * inside * np.clip(dcurve / 3000, 0, 1)

# ---- 사건
put(mus, 0.3, geomungo(98.0, 3.2, 0.5, seed=1))
put(fx, SC.T_DIVE - 0.2, swoosh(0.5, 0.4))
put(fx, SC.T_DIVE, snap(0.5, 2)); put(fx, SC.T_DIVE, plop(0.6))
put(fx, SC.T_DIVE + 0.05, bubbles(2.0, 60, 0.35))
for i, zt in enumerate(SC.ZT):
    put(fx, (SC.ZT0_TITLE if i == 0 else zt), ping(1180 - 120 * i, 0.22))
put(fx, 13.5, whale_call(4.0, 0.25))
put(fx, 21.5, tink(0.05, 2200)); put(fx, 22.0, tink(0.04, 2900))
put(fx, 38.6, bubbles(1.0, 8, 0.15))
for k in range(6): put(fx, 30.5 + 0.18 * k, tink(0.02, 2600 + 200 * k))
put(fx, SC.T_FLOOR, buk(0.45, 48, 1.8, 0.5, seed=3))
put(mus, SC.T_FLOOR + 0.2, geomungo(73.4, 3.5, 0.5, seed=4))

# ---- 정답
tp = SC.T_PAY
put(fx, tp, swoosh(1.3, 0.35))
for j, f in enumerate([196.0, 293.7, 392.0]): put(mus, tp + 1.2 + 0.12 * j, pluck(f, 1.8, 0.35))
put(fx, tp + 3.0, band(rng.standard_normal(int(1.4 * SR)), 40, 400) * np.linspace(0, 1, int(1.4 * SR)) ** 2 * 0.25)
put(fx, tp + 4.4, buk(0.55, 52, 1.6, 0.45, seed=5)); put(fx, tp + 4.4, snap(0.4, 6))
put(mus, tp + 4.9, pluck(587.3, 1.8, 0.4)); put(mus, tp + 5.0, pluck(784.0, 1.8, 0.35))
put(mus, tp + 5.6, geomungo(98.0, 4.0, 0.6, seed=7)); put(mus, tp + 5.7, pluck(392.0, 2.0, 0.3))
put(mus, SC.T_END + 0.3, geomungo(73.4, 3.5, 0.45, seed=8))

music = reverb(mus, sec=2.4, mix=0.3)[:N]
fxr = reverb(fx, sec=1.6, mix=0.25)[:N]
mix = amb + fxr + 0.8 * music
fade = int(0.3 * SR); mix[:fade] *= np.linspace(0, 1, fade)
end = int(1.5 * SR); mix[-end:] *= np.linspace(1, 0, end) ** 2
mix = mix / (np.abs(mix).max() + 1e-9) * 0.85
st = np.stack([mix, np.roll(mix, int(0.0004 * SR))], 1)
with wave.open(OUT, 'wb') as wf:
    wf.setnchannels(2); wf.setsampwidth(2); wf.setframerate(SR)
    wf.writeframes((st * 32767).astype(np.int16).tobytes())
print('WROTE', OUT)
