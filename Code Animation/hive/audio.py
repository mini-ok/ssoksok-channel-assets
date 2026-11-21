"""〈벌집은 왜 육각형일까〉 소리 — numpy 합성.  python3 audio.py out.wav"""
import os, sys, wave
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, '..', 'jeom', 'audio'))
import scene as SC                         # noqa: E402
from instruments import geomungo, buk      # noqa: E402
from sketch import reverb                  # noqa: E402

SR = 48000
DUR = SC.DUR
OUT = sys.argv[1] if len(sys.argv) > 1 else '/home/claude/work/hive/audio.wav'
N = int(DUR * SR)
rng = np.random.default_rng(13)
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



def buzz(dur, g=1.0, f0=210):
    n = int(dur * SR); t = np.arange(n) / SR
    f = f0 * (1 + 0.04 * np.sin(2 * np.pi * 3.1 * t) + 0.02 * np.sin(2 * np.pi * 7.3 * t))
    ph = np.cumsum(f) / SR
    saw = 2 * (ph % 1) - 1
    x = band(saw, 150, 3000) * (0.7 + 0.3 * np.sin(2 * np.pi * 37 * t))
    return g * norm(x) * np.clip(t / 0.15, 0, 1) * np.clip((dur - t) / 0.3, 0, 1)

def zip_(dur, g=1.0, f0=600, f1=1500):
    n = int(dur * SR); t = np.arange(n) / SR
    f = f0 + (f1 - f0) * t / dur
    clicks = np.sin(2 * np.pi * np.cumsum(f) / SR) * (np.sin(2 * np.pi * 45 * t) > 0.6)
    return g * band(clicks + 0.3 * rng.standard_normal(n), 800, 7000) * np.sin(np.pi * t / dur)

def swoosh(dur, g=1.0):
    n = int(dur * SR); t = np.arange(n) / SR
    return g * norm(band(rng.standard_normal(n), 300, 5000)) * np.sin(np.pi * t / dur) ** 1.5

G3, A3, C4, D4, E4, G4, A4, C5, D5, E5, G5 = 196.0, 220.0, 261.6, 293.7, 329.6, 392.0, 440.0, 523.3, 587.3, 659.3, 784.0

# A 질문
put(fx, 0.2, buzz(4.5, 0.18))
put(mus, 0.4, pluck(G4, 1.6, 0.4)); put(mus, 0.65, pluck(C5, 1.6, 0.35))
put(fx, 1.25, snap(0.45, 1)); put(mus, 2.7, pluck(E5, 1.5, 0.3))
# B 원판이 떨어짐 → 빈틈
for k in range(70):
    put(fx, SC.T_B + 0.4 + 0.022 * k + 0.4, tink(0.025, 900 + 8 * k))
put(fx, 8.2, buk(0.4, 60, 1.2, 0.3, seed=2)); put(mus, 8.3, pluck(A3, 1.5, 0.35)); put(mus, 8.45, pluck(D4, 1.5, 0.3))
# C 타일이 뒤집혀 깔림
for ri in range(3):
    for k in range(40):
        put(fx, SC.T_C + 0.6 + ri * 0.9 + 0.012 * k * 2.5, snap(0.06, 100 + ri * 40 + k))
    put(mus, SC.T_C + 0.6 + ri * 0.9, pluck([E4, G4, C5][ri], 1.4, 0.35))
put(mus, SC.T_C + 4.0, pluck(G5, 1.6, 0.35))
# D 실이 감기고 풀림 → 숫자
for ri in range(3):
    put(fx, SC.T_D + 1.3 + 0.35 * ri, zip_(1.0, 0.12, 500 + 150 * ri, 1300 + 150 * ri))
    put(fx, SC.T_D + 3.2 + 0.2 * ri, swoosh(1.3, 0.15))
    put(mus, SC.T_D + 4.6 + 0.2 * ri, pluck([C4, D4, G4][ri], 1.4, 0.4))
put(fx, SC.T_D + 6.4, tink(0.08, 2600)); put(mus, SC.T_D + 6.4, pluck(C5, 2.0, 0.45)); put(mus, SC.T_D + 6.55, pluck(E5, 2.0, 0.4))
# E 연도 → 1999
for k in range(28):
    tt = SC.T_E + 1.2 + 2.4 * (1 - (1 - k / 27) ** 1.6)
    put(fx, tt, tink(0.03, 1400 + 30 * k))
put(fx, SC.T_E + 3.6, buk(0.5, 58, 1.4, 0.4, seed=5)); put(mus, SC.T_E + 3.6, geomungo(98.0, 3.5, 0.5, seed=6))
put(fx, SC.T_E + 0.5, buzz(6.0, 0.1, 240))
# F 벌집
for k in range(60):
    put(fx, SC.T_F + 0.03 * k + rng.uniform(0, 0.05), tink(0.018, 1100 + rng.uniform(0, 600)))
put(fx, SC.T_F, buzz(SC.T_END - SC.T_F, 0.14, 225))
for j, f in enumerate([G3, D4, G4, A4, D5, G5]): put(mus, SC.T_F + 2.2 + 0.14 * j, pluck(f, 2.2, 0.35))
put(mus, SC.T_F + 2.2, geomungo(98.0, 5.0, 0.55, seed=7))
put(mus, SC.T_F + 6.0, pluck(D5, 2.0, 0.3)); put(mus, SC.T_F + 6.2, pluck(G5, 2.0, 0.3))
put(mus, SC.T_END + 0.4, geomungo(73.4, 3.0, 0.45, seed=8))

amb += 0.004 * norm(band(rng.standard_normal(N), 100, 2000))
music = reverb(mus, sec=2.2, mix=0.28)[:N]
fxr = reverb(fx, sec=0.9, mix=0.14)[:N]
mix = amb + fxr + 0.8 * music
fade = int(0.2 * SR); mix[:fade] *= np.linspace(0, 1, fade)
end = int(1.4 * SR); mix[-end:] *= np.linspace(1, 0, end) ** 2
mix = mix / (np.abs(mix).max() + 1e-9) * 0.85
st = np.stack([mix, np.roll(mix, int(0.0004 * SR))], 1)
with wave.open(OUT, 'wb') as wf:
    wf.setnchannels(2); wf.setsampwidth(2); wf.setframerate(SR)
    wf.writeframes((st * 32767).astype(np.int16).tobytes())
print('WROTE', OUT)
