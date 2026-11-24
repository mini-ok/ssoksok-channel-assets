"""〈42번〉 소리 — numpy 합성(샘플 없음). 시각은 nums.py에서 가져온다(그림과 같은 표).
  python3 audio.py out.wav
"""
import os, sys, wave
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, '..', 'jeom', 'audio'))
import nums as N                           # noqa: E402
from instruments import geomungo, buk      # noqa: E402
from sketch import reverb                  # noqa: E402

SR = 48000
DUR = N.DUR
OUT = sys.argv[1] if len(sys.argv) > 1 else '/home/claude/work/f42/audio.wav'
NS = int(DUR * SR)
rng = np.random.default_rng(42)
fx = np.zeros(NS); mus = np.zeros(NS); amb = np.zeros(NS)


def band(x, lo, hi, slope=2.0):
    X = np.fft.rfft(x); f = np.fft.rfftfreq(len(x), 1 / SR)
    g = 1 / (1 + (lo / np.maximum(f, 1)) ** (2 * slope)) / (1 + (f / hi) ** (2 * slope))
    return np.fft.irfft(X * g, len(x))
def norm(x): return x / (np.abs(x).max() + 1e-9)
def put(buf, t, x, g=1.0):
    i = int(round(t * SR)); j = min(NS, i + len(x))
    if 0 <= i < NS: buf[i:j] += g * x[:j - i]

def rustle(dur, g=1.0, crisp=0.5, seed=0):
    r = np.random.default_rng(seed); n = int(dur * SR); t = np.arange(n) / SR
    base = band(r.standard_normal(n), 900, 7000)
    ticks = np.zeros(n); k = r.random(n) < (0.004 + 0.02 * crisp); ticks[k] = r.standard_normal(k.sum())
    ticks = band(ticks, 2000, 11000)
    env = np.sin(np.pi * np.clip(t / dur, 0, 1)) ** 1.5
    return g * (0.5 * norm(base) + crisp * norm(ticks)) * env
def snap(g=1.0, seed=0, lo=1500):
    """접는 선이 '탁' 서는 소리. 정점은 첫 1ms 안."""
    r = np.random.default_rng(seed); n = int(0.09 * SR); t = np.arange(n) / SR
    x = band(r.standard_normal(n), lo, 9000) * np.exp(-t / 0.012) + 0.5 * band(r.standard_normal(n), 180, 900) * np.exp(-t / 0.022)
    return g * norm(x)
def pluck(f0, dur=1.0, g=1.0, bright=0.6):
    n = int(dur * SR); p = max(2, int(round(SR / f0)))
    buf = rng.uniform(-1, 1, p) * np.hanning(p) ** 0.3
    out = np.zeros(n); k = 0.5 + 0.49 * bright
    for i in range(n):
        x = buf[i % p]; out[i] = x
        buf[i % p] = (k * x + (1 - k) * buf[(i + 1) % p]) * 0.996
    return g * norm(out) * np.exp(-np.arange(n) / SR / (dur * 0.35))
def ping(f=1180, g=1.0, dur=1.8):
    n = int(dur * SR); t = np.arange(n) / SR
    return g * (np.sin(2 * np.pi * f * t) * np.exp(-t / 0.45) + 0.3 * np.sin(2 * np.pi * f * 2.01 * t) * np.exp(-t / 0.22))
def swoosh(dur, g=1.0, lo=300, hi=5000):
    n = int(dur * SR); t = np.arange(n) / SR
    return g * norm(band(rng.standard_normal(n), lo, hi)) * np.sin(np.pi * t / dur) ** 1.5
def tok(f=620, g=1.0):
    n = int(0.25 * SR); t = np.arange(n) / SR
    return g * (np.sin(2 * np.pi * f * t) * np.exp(-t / 0.035) + 0.5 * np.sin(2 * np.pi * f * 2.7 * t) * np.exp(-t / 0.015))

t = np.arange(NS) / SR
TF = N.TF
# 접은 횟수(연속) — 바탕 소리가 높이에 따라 바뀐다
kk = np.zeros(NS)
for k in range(1, 43): kk += np.clip((t - TF[k]) / 0.3, 0, 1)

# ---- 바탕: 방 → 바람(밖·높은 하늘) → 우주(낮고 먹먹한 울림)
room = band(rng.standard_normal(NS), 120, 1200)
amb += 0.012 * norm(room) * np.clip((13 - kk) / 3, 0, 1)
wind = band(rng.standard_normal(NS), 250, 2600) * (0.65 + 0.35 * np.sin(2 * np.pi * 0.23 * t + 1) ** 2)
amb += 0.055 * norm(wind) * np.clip((kk - 12.5) / 3, 0, 1) * np.clip((30.5 - kk) / 3, 0, 1)
space = np.sin(2 * np.pi * 55 * t) * 0.5 + np.sin(2 * np.pi * 82.4 * t) * 0.35 + np.sin(2 * np.pi * 110.2 * t) * 0.2
space *= 0.8 + 0.2 * np.sin(2 * np.pi * 0.17 * t)
amb += 0.05 * space * np.clip((kk - 28.5) / 3, 0, 1)
amb *= np.clip((t - N.T_XF[0]) / 0.5, 0, 1) * np.clip((N.T_TWIST + 0.3 - t) / 0.5, 0, 1)
amb += 0.010 * norm(room) * (np.clip((N.T_XF[1] - t) / 0.4, 0, 1) + np.clip((t - N.T_TWIST) / 0.5, 0, 1))      # 책상 위(처음·끝)의 방 소리

# ---- 첫 물음: 책상 위에서 세 번 접는다
put(mus, 0.05, geomungo(98.0, 2.6, 0.5, seed=1))
for j, tf in enumerate((0.55, 1.15, 1.75)):
    put(fx, tf, rustle(0.34, 0.5, 0.6, seed=10 + j)); put(fx, tf + 0.30, snap(0.6, 20 + j)); put(mus, tf + 0.30, pluck([196.0, 220.0, 293.7][j], 0.8, 0.22))
put(fx, N.T_XF[0] - 0.05, swoosh(0.5, 0.3))

# ---- 접기 42번: '탁' + 한 음씩 올라가는 줄 소리(5음 음계, 두 번에 한 계단 + 홀수 번은 위로 건너뛴 음)
PENTA = [0, 2, 4, 7, 9]
def deg(i): return 98.0 * 2 ** ((12 * (i // 5) + PENTA[i % 5]) / 12)
BIG = (14, 23, 27, 30, 32, 37)
for k in range(1, 43):
    tk = TF[k]; i = (k - 1) // 2 + (2 if k % 2 == 0 else 0)
    put(fx, tk, snap(0.42 + 0.004 * k, 100 + k, lo=1500 - 12 * k))
    put(mus, tk, pluck(deg(i), 0.9, 0.30 if k not in BIG else 0.42, bright=0.55 + 0.008 * k))
    if k in BIG:
        put(fx, tk + 0.02, ping(deg(i) * 4 if deg(i) < 500 else deg(i) * 2, 0.10))
        put(fx, tk, buk(0.28, 60, 1.2, 0.5, seed=200 + k))
# 마지막 한 번: 숨 고르고 → 달
tm = N.T_MOON
put(fx, tm - 0.62, swoosh(0.6, 0.22, 500, 7000))
put(fx, tm, buk(0.6, 46, 2.2, 0.5, seed=7)); put(fx, tm, snap(0.6, 8))
for j, f in enumerate([392.0, 587.3, 784.0, 1174.7]): put(mus, tm + 0.04 + 0.07 * j, pluck(f, 2.4, 0.34))
put(mus, tm + 0.5, geomungo(98.0, 3.0, 0.5, seed=9))
put(fx, tm + 0.5, ping(1568.0, 0.06, 2.2))

# ---- 실제 기록: 종이가 내려 덮고, '12'
tt = N.T_TWIST
put(fx, tt, swoosh(0.55, 0.4)); put(fx, tt + 0.42, snap(0.4, 31, lo=700))
put(fx, tt + 0.82, tok(520, 0.5)); put(fx, tt + 0.82, snap(0.5, 32)); put(mus, tt + 0.82, pluck(146.8, 1.6, 0.4, bright=0.4))
put(mus, tt + 1.6, pluck(293.7, 1.4, 0.25)); put(mus, tt + 1.75, pluck(220.0, 1.6, 0.25))
put(fx, tt + 2.25, rustle(0.5, 0.25, 0.4, seed=40)); put(mus, tt + 2.9, pluck(196.0, 1.6, 0.16))
put(mus, N.T_END + 0.3, geomungo(73.4, 2.4, 0.42, seed=11))

music = reverb(mus, sec=2.0, mix=0.26)[:NS]
fxr = reverb(fx, sec=1.2, mix=0.18)[:NS]
mix = amb + fxr + 0.85 * music
fade = int(0.05 * SR); mix[:fade] *= np.linspace(0, 1, fade)
end = int(1.2 * SR); mix[-end:] *= np.linspace(1, 0, end) ** 2
mix = mix / (np.abs(mix).max() + 1e-9)
mix = np.tanh(mix * 2.2) / np.tanh(2.2) * 0.85            # 타격 정점을 눌러 둔다(AAC로 바꿀 때 피크가 넘지 않게)
st = np.stack([mix, np.roll(mix, int(0.0004 * SR))], 1)
with wave.open(OUT, 'wb') as wf:
    wf.setnchannels(2); wf.setsampwidth(2); wf.setframerate(SR)
    wf.writeframes((st * 32767).astype(np.int16).tobytes())
print('WROTE', OUT)
