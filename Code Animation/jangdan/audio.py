"""〈장단〉 소리 — nums.py의 같은 사건표로 합성(numpy). python3 audio.py out.wav
북: 마디 장단 / 거문고: 먹 방울마다 한 음(5음계) / 붓 획: 휙 / 접는 수 바뀜: 큰 북 + 쇳소리 / 한 점: 정적 뒤 북 하나."""
import os, sys, wave
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, '..', 'jeom', 'audio')); sys.path.insert(0, os.path.join(HERE, '..', '_kit'))
import nums as N
from instruments import geomungo, buk
SR = 48000; B = N.B
rng = np.random.default_rng(7)

def band(x, lo, hi, slope=2.0):
    X = np.fft.rfft(x); f = np.fft.rfftfreq(len(x), 1 / SR)
    return np.fft.irfft(X * (1 / (1 + (lo / np.maximum(f, 1)) ** (2 * slope)) / (1 + (f / hi) ** (2 * slope))), len(x))
def norm(x): return x / (np.abs(x).max() + 1e-9)

n = int((N.DUR + 0.5) * SR)
mus = np.zeros((n, 2)); fx = np.zeros((n, 2))
def put(bus, x, t, g=1.0, pan=0.0):
    i = int(t * SR)
    if i >= n or i < 0: return
    x = x[:n - i]; bus[i:i + len(x), 0] += x * g * (1 - max(0, pan)); bus[i:i + len(x), 1] += x * g * (1 + min(0, pan))

SCALE = [0, 2, 5, 7, 9]                                                     # 5음계(황·태·중·임·남 꼴)
def hz(k, root=73.42): return root * 2 ** ((SCALE[k % 5] + 12 * (k // 5)) / 12)
_g = {}
def gm(f, dur, vel):
    key = (round(f, 1), dur)
    if key not in _g: _g[key] = norm(geomungo(f, dur=dur, vel=1.0, nonghyeon=0.25, seed=int(f)))
    return _g[key] * vel
def swoosh(dur, lo=300, hi=5000):
    m = int(dur * SR); t = np.arange(m) / SR
    return norm(band(rng.standard_normal(m), lo, hi)) * np.sin(np.pi * t / dur) ** 1.5
def metal(dur=1.6):
    m = int(dur * SR); t = np.arange(m) / SR
    x = sum(a * np.sin(2 * np.pi * f * t + p) * np.exp(-t / d) for f, a, d, p in [(412, 1, .9, 0), (617, .7, .7, 1), (1033, .5, .5, 2), (1490, .35, .35, 3), (2210, .2, .22, 4)])
    return norm(x + 0.3 * band(rng.standard_normal(m), 3000, 9000) * np.exp(-t / 0.06))
BUK = norm(buk(amp=0.6, f0=62, dur=1.4, seed=1)); BUK_HI = norm(buk(amp=0.5, f0=96, dur=0.6, decay=0.2, seed=2))

# 방울: 한 음씩. 처음엔 낮고 느리게, 뒤로 갈수록 높게.
for i, (t0, x, y, R, pg) in enumerate(N.DROPS):
    th = B.hit(t0); pan = (x - N.CX) / N.CX * 0.6
    if i < N.N_INTRO:
        put(mus, gm(hz((i * 3) % 10 + (0 if R > 50 else 5)), 2.0, 0.55 + 0.25 * (R > 50)), th, 0.5, pan)
    else:
        put(mus, gm(hz((i * 2) % 7 + 10), 0.7, 0.4), th, 0.26, pan)
# 북 장단: 1부는 마디 첫 박만, 2부는 덩-쿵, 만화경은 박마다 + 엇박
for bar in range(16):
    t = B.t(bar, 0)
    if t >= N.T_COL: break
    put(mus, BUK, B.hit(t), 0.55 if bar < 4 else 0.75)
    if bar >= 4: put(mus, BUK_HI, B.hit(B.t(bar, 2)), 0.4); put(mus, BUK_HI, B.hit(B.t(bar, 3.5)), 0.25)
    if bar >= 8:
        for b in (1, 3): put(mus, BUK, B.hit(B.t(bar, b)), 0.45)
        for b in (0.5, 1.5, 2.5): put(mus, BUK_HI, B.hit(B.t(bar, b)), 0.22)
# 붓 획·살
for (t0, dur, R, a0, sw, wd, pg) in N.STROKES: put(fx, swoosh(dur * 0.9, 250 + 2 * (520 - R), 4200), t0 + 1 / N.FPS, 0.30 + wd / 150, np.cos(a0) * 0.4)
for (t0, ang, r0, r1, wd, pg) in N.SPOKES: put(fx, swoosh(0.22, 900, 8000), t0 + 1 / N.FPS, 0.3, np.cos(ang) * 0.5)
# 접는 수가 바뀌는 순간: 쇳소리 + 큰 북, 낮은 거문고
for j, (tf, k) in enumerate(N.FOLDS):
    put(fx, metal(), B.hit(tf), 0.32); put(mus, BUK, B.hit(tf), 0.9); put(mus, gm(hz(j), 3.0, 1.0), B.hit(tf), 0.6)
put(fx, swoosh(0.5, 500, 9000), N.T_KAL - 0.45, 0.4)
# 모임: 빨려 드는 소리 → 정적 → 한 점
m = int((N.T_DOT - N.T_COL) * SR); t = np.arange(m) / SR; u = t / t[-1]
suck = norm(band(rng.standard_normal(m), 200, 6000) * u ** 2.5 + 0.5 * np.sin(2 * np.pi * np.cumsum(120 + 900 * u ** 3) / SR) * u ** 2)
suck[-int(0.03 * SR):] *= np.cos(np.linspace(0, np.pi / 2, int(0.03 * SR))) ** 2
put(fx, suck, N.T_COL, 0.42)
gate = np.ones(n); i0, i1 = int((N.T_DOT - 0.12) * SR), int(N.T_DOT * SR)      # 한 점 직전 음악만 곡선으로 닫는다
gate[i0:i1] = np.cos(np.linspace(0, np.pi / 2, i1 - i0)) ** 2; gate[i1:] = 0
mus *= gate[:, None]
tail = np.zeros((n, 2))
put(tail, BUK, B.hit(N.T_DOT), 1.0); put(tail, gm(hz(0, 36.71 * 2), 4.0, 1.0), B.hit(N.T_DOT), 0.7)
put(tail, gm(hz(2), 3.0, 0.6), B.hit(N.T_TITLE + B.beat_len * 2), 0.4); put(tail, gm(hz(4), 3.0, 0.6), B.hit(N.T_TITLE + B.beat_len * 3), 0.35)
put(tail, norm(band(rng.standard_normal(4000), 300, 3000) * np.exp(-np.arange(4000) / SR / 0.02)), B.hit(N.T_SEAL), 0.35)   # 낙관 '탁'
put(tail, gm(hz(5), 3.5, 0.8), B.hit(N.T_SEAL), 0.45)
mix = mus + fx + tail
# 울림(짧은 방)
m = int(1.8 * SR); ir = rng.standard_normal((m, 2)) * np.exp(-np.arange(m) / SR / 0.32)[:, None]; ir[:int(0.012 * SR)] = 0
wet = np.stack([np.fft.irfft(np.fft.rfft(mix[:, c], n + m) * np.fft.rfft(band(ir[:, c], 200, 5000), n + m))[:n] for c in (0, 1)], 1)
mix = mix + 0.16 * wet / (np.abs(wet).max() + 1e-9) * np.abs(mix).max()
fo = int(0.7 * SR); mix[-fo:] *= np.cos(np.linspace(0, np.pi / 2, fo))[:, None] ** 2; mix[:int(0.01 * SR)] *= np.linspace(0, 1, int(0.01 * SR))[:, None]
mix = mix[:int(N.DUR * SR)] / np.abs(mix).max() * 0.7
with wave.open(sys.argv[1], 'wb') as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes((mix * 32767).astype('<i2').tobytes())
print('ok', len(mix) / SR)
