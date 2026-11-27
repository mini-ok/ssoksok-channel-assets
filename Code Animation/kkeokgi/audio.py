"""〈꺾기〉 소리 — nums.py의 동작 순서·샷 표로 합성. python3 audio.py out.wav
북(쿵)·채(딱)·잔박 / 거문고 낮은 가락 / 동작마다 관절 '찍' / 화풍 바뀔 때 휙·쇳소리 / 끝 정적 뒤 한 방."""
import os, sys, wave
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, '..', 'jeom', 'audio')); sys.path.insert(0, os.path.join(HERE, '..', '_kit'))
import nums as N
from instruments import geomungo, buk
SR = 48000; B = N.B; BL = N.BL; rng = np.random.default_rng(7)
def band(x, lo, hi, slope=2.0):
    X = np.fft.rfft(x); f = np.fft.rfftfreq(len(x), 1 / SR)
    return np.fft.irfft(X * (1 / (1 + (lo / np.maximum(f, 1)) ** (2 * slope)) / (1 + (f / hi) ** (2 * slope))), len(x))
def norm(x): return x / (np.abs(x).max() + 1e-9)
n = int((N.DUR + 0.5) * SR); mus = np.zeros((n, 2)); fx = np.zeros((n, 2)); tail = np.zeros((n, 2))
def put(bus, x, t, g=1.0, pan=0.0):
    i = int(t * SR)
    if 0 <= i < n: x = x[:n - i]; bus[i:i + len(x), 0] += x * g * (1 - max(0, pan)); bus[i:i + len(x), 1] += x * g * (1 + min(0, pan))
SC = [0, 3, 5, 7, 10]
def hz(k, root=55.0): return root * 2 ** ((SC[k % 5] + 12 * (k // 5)) / 12)
_g = {}
def gm(f, dur):
    if (f, dur) not in _g: _g[(f, dur)] = norm(geomungo(f, dur=dur, vel=1.0, nonghyeon=0.15, seed=int(f)))
    return _g[(f, dur)]
KICK = norm(buk(amp=0.6, f0=58, dur=0.7, decay=0.22, seed=1))
def snare():
    m = int(0.22 * SR); t = np.arange(m) / SR
    return norm(band(rng.standard_normal(m), 900, 8000) * np.exp(-t / 0.045) + 0.5 * np.sin(2 * np.pi * 190 * t) * np.exp(-t / 0.03))
def hat(d=0.02): m = int(0.08 * SR); t = np.arange(m) / SR; return norm(band(rng.standard_normal(m), 6000, 14000) * np.exp(-t / d))
def servo(up=True, d=0.09):
    m = int(d * SR); t = np.arange(m) / SR; f = (500 + 1500 * t / d) if up else (2000 - 1400 * t / d)
    return norm(np.sign(np.sin(2 * np.pi * np.cumsum(f) / SR)) * 0.5 + np.sin(2 * np.pi * np.cumsum(f * 2.01) / SR)) * np.sin(np.pi * t / d) ** 0.7
def clack(): m = int(0.05 * SR); t = np.arange(m) / SR; return norm(band(rng.standard_normal(m), 1500, 9000) * np.exp(-t / 0.006) + 0.6 * np.sin(2 * np.pi * 320 * t) * np.exp(-t / 0.012))
def swoosh(d, lo=400, hi=8000): m = int(d * SR); t = np.arange(m) / SR; return norm(band(rng.standard_normal(m), lo, hi)) * (t / d) ** 2
def metal():
    m = int(1.2 * SR); t = np.arange(m) / SR
    return norm(sum(a * np.sin(2 * np.pi * f * t + p) * np.exp(-t / d_) for f, a, d_, p in [(412, 1, .6, 0), (617, .7, .5, 1), (1033, .5, .35, 2), (1490, .35, .25, 3), (2210, .2, .15, 4)]))
SN, HT, HO, CL, ME = snare(), hat(), hat(0.06), clack(), metal()
END = 56                                             # 56박에 멎는다
for b in range(END):
    bar, q = divmod(b, 4); t = b * BL; dense = bar >= 2
    if q in (0, 2) or (q == 3 and bar % 2 == 1 and dense): put(mus, KICK, B.hit(t), 0.95)
    if q == 2 and dense: put(mus, KICK, B.hit(t + BL * 0.75), 0.5)
    if q in (1, 3) and bar >= 1: put(mus, SN, B.hit(t), 0.5)
    if bar >= 2:
        put(mus, HT, B.hit(t), 0.16); put(mus, HO if q == 3 else HT, B.hit(t + BL / 2), 0.2)
        if bar >= 8: put(mus, HT, B.hit(t + BL / 4), 0.09); put(mus, HT, B.hit(t + BL * 3 / 4), 0.09)
    if bar >= 12: put(mus, SN, B.hit(t + BL / 2), 0.22)
RIFF = [0, 0, 3, 0, 2, 0, 4, 3]
for h in range(END * 2):                             # 거문고 낮은 가락(반 박)
    bar = h // 8
    if bar < 1: continue
    k = RIFF[h % 8] + (5 if (bar % 4 == 3 and h % 8 >= 4) else 0)
    if h % 8 in (0, 3, 4, 6) or bar >= 8: put(mus, gm(hz(k), 0.9), B.hit(h * BL / 2), 0.42 if h % 8 == 0 else 0.3)
for i, (b, name, D, spin) in enumerate(N.SEQ):       # 동작마다 관절 소리(한 프레임 뒤)
    if i == 0: continue
    t = b * BL; pan = 0.35 * (1 if i % 2 else -1)
    put(fx, servo(i % 2 == 0, max(0.07, D)), t, 0.16, pan); put(fx, CL, B.hit(t + D - 0.03), 0.3, -pan)
    if spin: put(fx, swoosh(D, 300, 5000)[::-1] * 0 + swoosh(D), t, 0.3)
for si, sh in enumerate(N.SHOTS):                    # 화풍이 바뀌는 순간
    if si == 0: continue
    t = sh[0] * BL; big = sh[6] != 'cut'
    put(fx, swoosh(0.22 if big else 0.1), t - (0.22 if big else 0.1), 0.34 if big else 0.2)
    if big: put(fx, ME, B.hit(t), 0.2 + 0.1 * (sh[6] == 'flash'))
t_end = END * BL
gate = np.ones(n); i1 = int(t_end * SR); i0 = i1 - int(0.03 * SR); gate[i0:i1] = np.cos(np.linspace(0, np.pi / 2, i1 - i0)) ** 2; gate[i1:] = 0
mus *= gate[:, None]
put(tail, norm(buk(amp=0.6, f0=50, dur=1.6, seed=3)), B.hit(t_end), 1.0); put(tail, gm(hz(0, 36.71), 4.0), B.hit(t_end), 0.7); put(tail, ME, B.hit(t_end), 0.35)
put(tail, gm(hz(2, 110.0), 2.5), B.hit(N.T_TITLE), 0.35); put(tail, CL, B.hit(N.T_SEAL), 0.5); put(tail, gm(hz(4, 110.0), 3.0), B.hit(N.T_SEAL), 0.4)
mix = mus + fx + tail
m = int(1.0 * SR); ir = rng.standard_normal((m, 2)) * np.exp(-np.arange(m) / SR / 0.18)[:, None]; ir[:int(0.01 * SR)] = 0
wet = np.stack([np.fft.irfft(np.fft.rfft(mix[:, c], n + m) * np.fft.rfft(band(ir[:, c], 250, 6000), n + m))[:n] for c in (0, 1)], 1)
mix = mix + 0.10 * wet / (np.abs(wet).max() + 1e-9) * np.abs(mix).max()
mix = np.tanh(mix / np.abs(mix).max() * 1.6) / np.tanh(1.6)       # 살짝 눌러 단단하게
fo = int(0.6 * SR); mix = mix[:int(N.DUR * SR)]; mix[-fo:] *= np.cos(np.linspace(0, np.pi / 2, fo))[:, None] ** 2
mix = mix / np.abs(mix).max() * 0.7
with wave.open(sys.argv[1], 'wb') as w: w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes((mix * 32767).astype('<i2').tobytes())
print('ok', len(mix) / SR)
