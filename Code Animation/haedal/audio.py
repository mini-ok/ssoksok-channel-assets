"""〈해의 달력〉 소리 — numpy 합성(샘플 없음). 시각은 scene.py 시간표에서 그대로 가져온다.
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
OUT = sys.argv[1] if len(sys.argv) > 1 else '/home/claude/work/haedal/audio.wav'
N = int(DUR * SR)
rng = np.random.default_rng(5)
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


def knife(dur, g=1.0):
    """칼끝이 종이를 가르는 소리: 섬유가 끊기는 잔 틱 + 칼날의 가는 울림(조금씩 올라감)."""
    n = int(dur * SR); t = np.arange(n) / SR
    scrape = band(rng.standard_normal(n), 3000, 9500) * (0.6 + 0.4 * band(rng.standard_normal(n), 8, 40) * 10)
    ticks = np.zeros(n); k = rng.random(n) < 0.03; ticks[k] = rng.standard_normal(k.sum()); ticks = band(ticks, 2500, 12000)
    f = 4700 + 500 * t / dur
    sing = np.sin(2 * np.pi * np.cumsum(f) / SR) * (0.5 + 0.5 * np.sin(2 * np.pi * 11 * t))
    env = np.clip(t / 0.06, 0, 1) * np.clip((dur - t) / 0.08, 0, 1)
    return g * (0.45 * norm(scrape) + 0.6 * norm(ticks) + 0.08 * sing) * env



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


SCALE = [196.0, 220.0, 261.6, 293.7, 329.6, 392.0, 440.0, 523.3, 587.3, 659.3]   # G A C D E 두 옥타브

# ---- 처음
put(fx, 0.15, swoosh(1.3, 0.35))                       # 달이 미끄러져 들어옴
put(fx, 1.2, tink(0.05, 2400))
put(fx, 1.9, bloop(0.5))                               # 해가 솟음
put(fx, 2.55, snap(0.6, 3)); put(fx, 2.55, buk(0.35, 70, 0.8, 0.25, seed=1))   # 달을 밀어냄
put(fx, 2.6, swoosh(0.7, 0.3))
put(fx, 3.0, buk(0.5, 58, 1.4, 0.4, seed=2)); put(mus, 3.0, geomungo(98.0, 3.5, 0.6, seed=10))   # 해의 달력
put(fx, 4.0, knife(1.6, 0.35))                         # 해가 고리를 긋는다
put(mus, 5.6, geomungo(146.8, 2.5, 0.4, seed=11))
for j in range(24):                                    # 눈금 24개
    put(fx, SC.T_RULE + 0.25 + 0.055 * j, tink(0.03 + 0.03 * (j in SC.KEY), 1800 + 60 * j))
put(fx, SC.T_RULE + 1.6, snap(0.5, 5)); put(mus, SC.T_RULE + 1.6, pluck(392.0, 1.4, 0.5))

# ---- 절기마다: 해가 톡 뛰어 자리 잡음 → 그림이 튀어나옴 → 자리로 날아감
for k in range(24):
    tl = SC.T0[k] + SC.HOP * 0.7
    put(fx, SC.T0[k], swoosh(0.35, 0.12))
    put(fx, tl, snap(0.45 if k in SC.KEY else 0.32, 30 + k))
    put(fx, tl, buk(0.28 if k in SC.KEY else 0.16, 66, 0.7, 0.2, seed=40 + k))
    s = k // 6
    base = [0, 1, 2, 1][s]                           # 계절마다 음 자리를 조금씩
    note = SCALE[min(9, base + (k % 6) + (2 if s == 1 else 0))]
    if k in SC.KEY:
        put(mus, tl, geomungo(note / 2, 3.0, 0.65, seed=60 + k))
        put(mus, tl + 0.12, pluck(note, 1.6, 0.35)); put(mus, tl + 0.24, pluck(note * 1.5 if note < 400 else note * 0.75, 1.6, 0.3))
    else:
        put(mus, tl, pluck(note, 1.3, 0.45 if s != 3 else 0.32, 0.75 if s != 3 else 0.45))
    tf = (SC.T0[k + 1] if k < 23 else SC.T_PAY) - 0.35
    put(fx, tf, rustle(0.4, 0.12, 0.5, 80 + k))
    if k % 6 == 0:
        put(fx, SC.T0[k], swoosh(1.0, 0.45))           # 계절 종이가 넘어감
        put(mus, SC.T0[k], geomungo([98.0, 110.0, 130.8, 73.4][s], 4.0, 0.55, seed=90 + s))
    if k == 9:                                         # 하지 햇살
        for j in range(6): put(fx, tl + 0.05 * j, tink(0.03, 3000 + 300 * j))
    if k == 21:
        put(fx, tl, buk(0.4, 52, 1.8, 0.5, seed=99))

# ---- 한 바퀴 → 꽃
tp = SC.T_PAY
put(fx, tp, snap(0.6, 120)); put(fx, tp, buk(0.5, 60, 1.6, 0.4, seed=121))
put(fx, tp + 0.7, swoosh(1.3, 0.4)); put(fx, tp + 0.8, rustle(1.0, 0.25, 0.4, 122))
for j, f in enumerate([196.0, 293.7, 392.0, 440.0, 587.3, 659.3]):
    put(mus, tp + 0.7 + 0.11 * j, pluck(f, 2.2, 0.4))
put(mus, tp + 0.7, geomungo(98.0, 5.0, 0.7, seed=130)); put(mus, tp + 2.4, geomungo(146.8, 4.0, 0.5, seed=131))
put(fx, tp + 2.4, buk(0.35, 58, 1.4, 0.4, seed=132))
put(mus, SC.T_END + 0.2, geomungo(73.4, 4.0, 0.45, seed=133))

# ---- 바탕: 아주 옅은 방 공기
t = np.arange(N) / SR
amb += 0.006 * norm(band(rng.standard_normal(N), 80, 900))

music = reverb(mus, sec=2.4, mix=0.3)[:N]
fxr = reverb(fx, sec=1.0, mix=0.15)[:N]
mix = amb + fxr + 0.8 * music
fade = int(0.2 * SR); mix[:fade] *= np.linspace(0, 1, fade)
end = int(1.5 * SR); mix[-end:] *= np.linspace(1, 0, end) ** 2
mix = mix / (np.abs(mix).max() + 1e-9) * 0.85
st = np.stack([mix, np.roll(mix, int(0.0004 * SR))], 1)
with wave.open(OUT, 'wb') as wf:
    wf.setnchannels(2); wf.setsampwidth(2); wf.setframerate(SR)
    wf.writeframes((st * 32767).astype(np.int16).tobytes())
print('WROTE', OUT)
