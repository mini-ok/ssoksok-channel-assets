#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""〈허수아비의 겨울〉 — 125 s soundtrack, fully synthesized, locked to film.py's cut list.
Cut starts: C1 0, C2 7, C3 12, C4 17, C5 23, C6 27, C7 31, C8 35, C9 39, C10 47, C11 53, C12 58, C13 64, C14 69,
C15 74, C16 80, C17 84 (snap 84.5 -> silence until 89.0), C18 90, C19 95, C20 102, C21 114, C22 118, end 125."""
import numpy as np, math
from scipy.signal import butter, sosfilt, fftconvolve
from scipy.io import wavfile

SR = 44100
DUR = 125.0
N = int(DUR * SR)
T = np.arange(N) / SR
rng = np.random.default_rng(125)

def S(a, b, t):
    x = np.clip((np.asarray(t, float) - a) / (b - a), 0, 1)
    return x * x * (3 - 2 * x)

NOTE = {'C': 0, 'C#': 1, 'D': 2, 'Eb': 3, 'D#': 3, 'E': 4, 'F': 5, 'F#': 6, 'G': 7, 'Ab': 8, 'G#': 8, 'A': 9, 'Bb': 10, 'B': 11}
def nm(s):
    return 12 * (int(s[-1]) + 1) + NOTE[s[:-1]]
def mf(m):
    return 440.0 * 2 ** ((m - 69) / 12.0)
def hz(s):
    return mf(nm(s))

def bp(x, lo, hi, o=2):
    return sosfilt(butter(o, [lo, hi], btype='band', fs=SR, output='sos'), x)
def lp(x, fc, o=2):
    return sosfilt(butter(o, fc, btype='low', fs=SR, output='sos'), x)
def hp(x, fc, o=2):
    return sosfilt(butter(o, fc, btype='high', fs=SR, output='sos'), x)

class Bus:
    def __init__(s):
        s.l = np.zeros(N); s.r = np.zeros(N); s.w = np.zeros(N)
    def put(s, t0, l, r=None, send=0.0, gain=1.0):
        if r is None:
            r = l
        i = int(round(t0 * SR))
        if i >= N or i + len(l) <= 0:
            return
        a = max(0, -i); n = min(len(l) - a, N - max(i, 0)); i = max(i, 0)
        s.l[i:i + n] += l[a:a + n] * gain; s.r[i:i + n] += r[a:a + n] * gain
        if send > 0:
            s.w[i:i + n] += 0.5 * (l[a:a + n] + r[a:a + n]) * gain * send

MUS = Bus(); SFX = Bus(); AMB = Bus(); POST = Bus()      # POST: sounds inside the silence, added after levelling
def tg(d):
    return np.arange(int(d * SR)) / SR
def env(tt, d, att, rel):
    a = np.clip(tt / max(att, 1e-3), 0, 1); r = np.clip((d - tt) / max(rel, 1e-3), 0, 1)
    return (a * a * (3 - 2 * a)) * (r * r * (3 - 2 * r))
def pan(sig, p):
    th = (p + 1) * math.pi / 4
    return sig * math.cos(th), sig * math.sin(th)
def noise(d):
    return rng.normal(0, 1, int(d * SR))

# ------------------------------------------------------------------ instruments
def ocarina(f, d, amp, vib=0.005):
    tt = tg(d)
    e = env(tt, d, 0.07, min(0.25, d * 0.4))
    vd = np.clip((tt - 0.25) / 0.4, 0, 1)
    vm = 1 + vib * vd * np.sin(2 * np.pi * 5.2 * tt)
    ph = np.cumsum(f * vm) / SR
    s = np.sin(2 * np.pi * ph) + 0.12 * np.sin(4 * np.pi * ph) + 0.04 * np.sin(6 * np.pi * ph)
    br = bp(rng.normal(0, 1, len(tt)), f * 0.8, min(f * 1.5, SR * 0.45)) * 0.06 * (0.4 + 0.6 * np.exp(-tt / 0.12))
    return (s + br) * e * amp

def celesta(f, d, amp):
    tt = tg(d); s = np.zeros_like(tt)
    for ratio, a, k in ((1, 1.0, 2.2), (2.0, 0.35, 3.5), (3.0, 0.12, 5.0), (4.07, 0.08, 7.0)):
        s += a * np.sin(2 * np.pi * f * ratio * tt) * np.exp(-tt * k)
    return s * np.clip(tt / 0.002, 0, 1) * amp

def pad(f, d, amp, harm=6, att=1.2, rel=1.6, vib=0.002, bright=1.6, trem=0.0):
    tt = tg(d); e = env(tt, d, att, rel)
    if trem > 0:
        e = e * (1 - trem * 0.5 * (1 + np.sin(2 * np.pi * 7 * tt)))
    vm = 1 + vib * np.sin(2 * np.pi * 5.0 * tt)
    ph = np.cumsum(vm) / SR
    l = np.zeros_like(tt); r = np.zeros_like(tt)
    for h in range(1, harm + 1):
        g = 1.0 / h ** bright
        l += g * np.sin(2 * np.pi * f * h * 1.0018 * ph + h)
        r += g * np.sin(2 * np.pi * f * h * 0.9982 * ph + 2 * h)
    return l * e * amp, r * e * amp

def harp(f, d, amp):
    tt = tg(d); s = np.zeros_like(tt)
    for h in range(1, 9):
        if f * h > 12000:
            break
        s += (1.0 / h ** 1.4) * np.sin(2 * np.pi * f * h * tt + h) * np.exp(-tt * (1.2 + 0.7 * h))
    return s * np.clip(tt / 0.003, 0, 1) * amp

def pizz(f, amp, d=0.5):
    tt = tg(d); s = np.zeros_like(tt)
    for h in range(1, 7):
        s += (1.0 / h ** 1.2) * np.sin(2 * np.pi * f * h * tt + h) * np.exp(-tt * (9 + 4 * h))
    return s * np.clip(tt / 0.002, 0, 1) * amp

def piano(f, d, amp):
    tt = tg(d); s = np.zeros_like(tt)
    for h in range(1, 10):
        if f * h > 10000:
            break
        s += (1.0 / h ** 1.3) * np.sin(2 * np.pi * f * h * (1 + 0.0004 * h * h) * tt + h) * np.exp(-tt * (0.8 + 0.5 * h))
    return s * np.clip(tt / 0.002, 0, 1) * np.clip((d - tt) / 0.3, 0, 1) * amp

def boom(d, amp, f0=110, f1=30, tau=0.25):
    tt = tg(d); f = f1 + (f0 - f1) * np.exp(-tt / tau)
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-tt / (d * 0.35)) * np.clip(tt / 0.003, 0, 1) * amp

def click(amp, d=0.010, fc=3500):
    return hp(noise(d), fc) * np.exp(-tg(d) / 0.002) * amp

def whoosh(d, f0, f1, amp, peak=0.5):
    n = int(d * SR); x = rng.normal(0, 1, n); out = np.zeros(n)
    ch, hop = 2048, 1024; win = np.hanning(ch)
    for i in range(0, max(1, n - ch), hop):
        u = (i + ch / 2) / n
        fc = f0 * (f1 / f0) ** u
        out[i:i + ch] += bp(x[i:i + ch], max(fc * 0.6, 30), min(fc * 1.6, SR * 0.45)) * win
    tt = np.arange(n) / n
    e = np.where(tt < peak, (tt / peak) ** 2, ((1 - tt) / (1 - peak)) ** 1.5)
    return out * e * amp

def rustle(d, amp, dens=180):
    """dry straw: crackle grains in band-passed noise"""
    n = int(d * SR)
    x = bp(rng.normal(0, 1, n), 1500, 7000) * 0.3
    g = np.zeros(n)
    for _ in range(int(dens * d)):
        i = rng.integers(0, max(1, n - 400))
        g[i:i + 300] += rng.normal(0, 1, 300) * np.exp(-np.arange(300) / rng.uniform(20, 80))
    s = x + hp(g, 2000) * 0.8
    return s * env(np.arange(n) / SR, d, d * 0.2, d * 0.4) * amp

def chirp(t0, amp, p, f0=4200, notes=3, bus=None, send=0.35):
    bus = bus or SFX
    for k in range(notes):
        d = rng.uniform(0.05, 0.10); tt = tg(d)
        f = f0 * rng.uniform(0.9, 1.15) + 1100 * np.sin(np.pi * tt / d) * rng.choice([-1, 1])
        s = np.sin(2 * np.pi * np.cumsum(f) / SR) * env(tt, d, 0.008, 0.03)
        l, r = pan(s, p)
        bus.put(t0 + k * rng.uniform(0.08, 0.13), l, r, send=send, gain=amp)

def squeak(t0, amp, p, up=True):
    d = 0.16; tt = tg(d)
    f = (3600 + 1800 * tt / d) if up else (5200 - 2000 * tt / d)
    s = np.sin(2 * np.pi * np.cumsum(f) / SR) * env(tt, d, 0.01, 0.06)
    l, r = pan(s, p); SFX.put(t0, l, r, send=0.3, gain=amp)

def flutter(t0, d, amp, p=0.0):
    n = int(d * SR); tt = np.arange(n) / SR
    am = np.clip(np.sin(2 * np.pi * 18 * tt), 0, 1) ** 3
    s = bp(rng.normal(0, 1, n), 500, 2800) * am * env(tt, d, 0.03, 0.1)
    l, r = pan(s, p); SFX.put(t0, l, r, send=0.2, gain=amp)

def hawk_cry(t0, amp, p, dist=0.0):
    d = 1.1; tt = tg(d)
    f = 2900 - 700 * (tt / d) ** 0.7 + 60 * np.sin(2 * np.pi * 22 * tt)
    ph = np.cumsum(f) / SR
    s = np.sin(2 * np.pi * ph) + 0.4 * np.sin(4 * np.pi * ph) + 0.15 * np.sin(6 * np.pi * ph)
    s = s * env(tt, d, 0.04, 0.5)
    if dist > 0:
        s = lp(s, 4000 - 2500 * dist)
    l, r = pan(s, p); SFX.put(t0, l, r, send=0.6 + 0.3 * dist, gain=amp)

def crack(amp, d=0.45, f=180):
    tt = tg(d)
    tr = hp(noise(d), 1200) * np.exp(-tt / 0.008)
    groan = bp(noise(d), f * 0.7, f * 3) * np.exp(-tt / 0.12) * (1 + 0.6 * np.sign(np.sin(2 * np.pi * 38 * tt)))
    return (tr * 1.0 + groan * 1.4 + boom(d, 0.5, f0=140, f1=60, tau=0.05)) * amp

def creak(amp, d=0.55):
    n = int(d * SR); out = np.zeros(n); t = 0.0
    while t < d - 0.01:
        i = int(t * SR)
        out[i:i + 80] += rng.normal(0, 1, 80) * np.exp(-np.arange(80) / 15)
        t += 0.004 + 0.02 * (1 - t / d) ** 2
    return bp(out, 900, 3200) * env(np.arange(n) / SR, d, 0.05, 0.1) * amp

def goose(t0, amp, p):
    d = 0.22; tt = tg(d); f = 380 + 60 * np.sin(np.pi * tt / d)
    s = bp(np.sign(np.sin(2 * np.pi * np.cumsum(f) / SR)), 300, 2400) * env(tt, d, 0.02, 0.08)
    l, r = pan(s, p); SFX.put(t0, l, r, send=0.6, gain=amp)

def peep(t0, amp, p):
    d = 0.09; tt = tg(d); f = 4800 + 900 * tt / d
    s = np.sin(2 * np.pi * np.cumsum(f) / SR) * env(tt, d, 0.006, 0.03)
    l, r = pan(s, p); SFX.put(t0, l, r, send=0.3, gain=amp)

def plink(t0, amp, p, f=None, bus=None):
    bus = bus or SFX
    d = 0.18; tt = tg(d); f = f or rng.uniform(1600, 3000)
    s = np.sin(2 * np.pi * f * (1 + 0.3 * np.exp(-tt / 0.01)) * tt) * np.exp(-tt / 0.03)
    l, r = pan(s, p); bus.put(t0, l, r, send=0.5, gain=amp)

def stereo(fn):
    return fn(noise(DUR)), fn(noise(DUR))

# ------------------------------------------------------------------ ambience beds
def bed(lo, hi, amp, shape, mod=None):
    l, r = stereo(lambda x: bp(x, lo, hi))
    m = shape * (mod if mod is not None else 1.0)
    AMB.l += l * amp * m; AMB.r += r * amp * m

gustmod = 0.7 + 0.3 * np.sin(2 * np.pi * 0.09 * T) * np.sin(2 * np.pi * 0.05 * T + 1)
field = S(0, 1.5, T) * (1 - S(46.6, 47.2, T))                                    # autumn field
bed(250, 1400, 0.040, field, gustmod)
bed(3500, 9000, 0.010, field * (0.5 + 0.5 * np.sin(2 * np.pi * 0.4 * T) ** 2))   # insects
evening = S(47, 47.6, T) * (1 - S(52.6, 53.1, T))
bed(200, 900, 0.035, evening, gustmod)
rain = S(52.8, 53.3, T) * (1 - S(57.8, 58.2, T)) + 0.35 * S(58, 58.2, T) * (1 - S(63.6, 64.0, T))
bed(1200, 9000, 0.075, rain)
bed(150, 600, 0.05, rain)
cold = S(63.8, 64.4, T) * (1 - S(73.6, 74.0, T))
bed(180, 800, 0.03, cold, gustmod)
bliz = S(73.8, 74.2, T) * (1 - S(84.48, 84.52, T))
bmod = 0.75 + 0.25 * np.sin(2 * np.pi * 0.33 * T) * np.sin(2 * np.pi * 0.17 * T + 2)
bed(150, 1100, 0.16, bliz, bmod)
wl, wr = stereo(lambda x: bp(x, 700, 1500, 3))                                   # whistle
AMB.l += wl * 0.05 * bliz * bmod ** 3; AMB.r += wr * 0.05 * bliz * bmod ** 3
hush = S(89.0, 90.0, T) * (1 - S(101.6, 102.4, T))
bed(2500, 8000, 0.008, hush)
bed(200, 700, 0.012, hush)
spring = S(102, 106, T) * (1 - S(124, 125, T))
bed(300, 1600, 0.022, spring, gustmod)
bed(3500, 9000, 0.006, S(110, 113, T) * (1 - S(124, 125, T)))

# ------------------------------------------------------------------ sound effects
# C1-C3: morning birds, dragonflies, the sleepy sparrow
for t0, p in ((1.2, -0.6), (3.0, 0.5), (4.8, -0.2), (6.2, 0.6)):
    chirp(t0, 0.025, p, f0=3600, notes=rng.integers(2, 5))
for k in range(10):                                         # sparrows on the arms
    chirp(7.2 + k * 0.18 + rng.uniform(0, 0.1), 0.03, rng.uniform(-0.5, 0.5), notes=1)
SFX.put(8.9, whoosh(1.5, 300, 1800, 0.20, 0.25), send=0.3)  # C2 gust
SFX.put(9.0, rustle(1.2, 0.05), send=0.2)
for k in range(4):
    flutter(9.05 + k * 0.05, 0.6, 0.06, -0.6 + k * 0.4)
    chirp(9.1 + k * 0.07, 0.03, -0.6 + k * 0.4, notes=2)
squeak(13.35, 0.035, 0.0, up=False)                         # C3 yawn
flutter(14.4, 0.6, 0.05)                                    # stretch
flutter(15.0, 0.2, 0.07)                                    # shake
# C4 (17-23): two gusts
for g0, g1 in ((17.80, 18.55), (20.40, 21.35)):
    SFX.put(g0 - 0.1, whoosh(g1 - g0 + 0.6, 300, 1900, 0.22, 0.25), send=0.3)
    SFX.put(g0, rustle(g1 - g0 + 0.3, 0.06), send=0.2)
squeak(18.0, 0.05, 0.3); flutter(18.0, 0.6, 0.06, 0.4)
flutter(19.4, 0.6, 0.05, 0.5)
SFX.put(20.0, boom(0.15, 0.08, f0=300, f1=150, tau=0.02)); squeak(20.2, 0.03, 0.0)
flutter(20.45, 1.4, 0.06, 0.2); squeak(21.9, 0.04, 0.1)
# C5-C7: the hawk
SFX.put(23.4, whoosh(2.8, 120, 500, 0.10, 0.5), send=0.4)  # shadow
hawk_cry(25.5, 0.05, -0.5, dist=0.8)
hawk_cry(27.6, 0.10, -0.2, dist=0.2)
SFX.put(28.5, whoosh(2.5, 400, 3500, 0.22, 0.85), send=0.2)  # dive
SFX.put(31.15, whoosh(2.9, 250, 2000, 0.30, 0.2), send=0.3)  # C7 gust
SFX.put(31.25, rustle(2.6, 0.09, dens=260), send=0.2)
for k in range(5):
    SFX.put(31.3 + k * 0.4, lp(noise(0.15), 900) * np.exp(-tg(0.15) / 0.03) * 0.05, send=0.2)  # sleeve flaps
hawk_cry(31.9, 0.07, -0.6, dist=0.4)
hawk_cry(33.3, 0.04, -0.8, dist=0.8)
# C8: blush
SFX.put(36.45, click(0.05, fc=2500), send=0.2)
# C9 gifts
for k, b in enumerate((39.0, 41.667, 44.333)):
    flutter(b, 0.8, 0.05, 0.6)
    SFX.put(b + 1.0, boom(0.08, 0.05, f0=500 - 80 * k, f1=250, tau=0.01), send=0.2)
    chirp(b + 1.6, 0.03, 0.2, notes=2)
# C10: geese
for k in range(6):
    goose(47.5 + k * 0.6 + rng.uniform(0, 0.2), 0.012, -0.6 + k * 0.1)
# C11 rain + gust, hat flies
SFX.put(53.9, whoosh(2.2, 250, 1800, 0.25, 0.25), send=0.3)
SFX.put(54.0, rustle(1.8, 0.06), send=0.2)
SFX.put(54.2, whoosh(1.4, 800, 2600, 0.10, 0.4), send=0.3)
squeak(54.4, 0.05, 0.4)
flutter(56.0, 1.2, 0.06, 0.6)
# C12: tugs
for k in range(7):
    t0 = 58.0 + k * 0.5
    SFX.put(t0 + 0.02, bp(noise(0.16), 600, 3000) * env(tg(0.16), 0.16, 0.01, 0.08) * 0.07, send=0.15)
    squeak(t0, 0.02, 0.2, up=k % 2 == 0)
for k in range(10):                                        # panting
    SFX.put(61.2 + k * 0.17, bp(noise(0.06), 2500, 6000) * env(tg(0.06), 0.06, 0.01, 0.03) * 0.03, send=0.1)
# C13 frost
for k in range(14):
    plink(64.0 + rng.uniform(0, 3.0), 0.012, rng.uniform(-0.6, 0.6), f=rng.uniform(3500, 6500))
for b in (67.2, 68.5):
    SFX.put(b, bp(noise(0.4), 300, 1500) * env(tg(0.4), 0.4, 0.1, 0.25) * 0.012, send=0.3)
# C15-C17 blizzard: torn out, cuff, thread
squeak(74.7, 0.05, -0.3); flutter(74.7, 0.7, 0.07, -0.4)
for t0 in (80.7, 81.5, 82.3, 83.1, 84.05):
    SFX.put(t0, creak(0.10, 0.55), send=0.3)
squeak(81.0, 0.04, -0.2); squeak(82.6, 0.04, -0.2)
# the snap (last sound before the silence)
SFX.put(84.5, (hp(noise(0.05), 3000) * np.exp(-tg(0.05) / 0.004) + np.sin(2 * np.pi * 1400 * tg(0.05)) *
               np.exp(-tg(0.05) / 0.01)) * 0.25, send=0.6)
# inside the silence (POST bus: not levelled)
POST.put(85.02, boom(0.12, 0.05, f0=220, f1=120, tau=0.02), send=0.2)
POST.put(85.05, bp(noise(0.2), 2000, 6000) * env(tg(0.2), 0.2, 0.005, 0.15) * 0.04, send=0.3)
for t0, a in ((85.4, 0.11), (86.4, 0.14), (87.4, 0.17)):
    POST.put(t0, crack(a), send=0.5)
POST.put(87.9, rustle(0.7, 0.05, dens=120), send=0.3)
POST.put(87.95, bp(noise(0.6), 200, 1200) * env(tg(0.6), 0.6, 0.15, 0.3) * 0.03, send=0.3)
# C19: moonlight sparkles
for k in range(14):
    plink(95.5 + rng.uniform(0, 6.0), 0.008, rng.uniform(-0.7, 0.7), f=rng.uniform(4000, 7000))
# C20 timelapse: drips, spring gust, topple, birds
for k in range(30):
    plink(103.0 + rng.uniform(0, 5.0), 0.016, rng.uniform(-0.7, 0.7), f=rng.uniform(900, 2000))
flutter(106.9, 0.8, 0.05, 0.5)
SFX.put(107.4, whoosh(3.2, 300, 1500, 0.14, 0.3), send=0.3)
SFX.put(107.6, rustle(2.6, 0.05), send=0.2)
SFX.put(109.0, rustle(0.9, 0.07, dens=300), send=0.2)
SFX.put(109.78, boom(0.5, 0.18, f0=110, f1=45, tau=0.05), send=0.3)
SFX.put(109.78, lp(noise(0.3), 1200) * np.exp(-tg(0.3) / 0.05) * 0.12, send=0.3)
SFX.put(110.2, boom(0.2, 0.06, f0=260, f1=120, tau=0.02), send=0.2)
for k in range(8):
    chirp(111.2 + k * 0.35, 0.025, rng.uniform(-0.6, 0.6), notes=2)
# C21-C22 chicks and spring
for k in range(26):
    peep(114.0 + k * 0.14 + rng.uniform(0, 0.05), 0.02, 0.25 + rng.uniform(-0.1, 0.1))
for t0 in (119.0, 121.4, 123.0):
    chirp(t0, 0.022, rng.uniform(-0.6, 0.6), notes=3)
SFX.put(118.7, whoosh(2.0, 300, 1300, 0.08, 0.3), send=0.3)
SFX.put(121.5, whoosh(2.0, 300, 1300, 0.08, 0.3), send=0.3)

# ------------------------------------------------------------------ music
# one pentatonic motif (E G A C A G E D) re-harmonised by season: C major (autumn), A minor (winter), D major (spring)
MOTIF = ['E5', 'G5', 'A5', 'C6', 'A5', 'G5', 'E5', 'D5']
def tr(n_, k):
    return mf(nm(n_) + k)

def chord(st, notes, d, amp, att=1.0, rel=1.2, send=0.5, trem=0.0, bright=1.6):
    for j, n_ in enumerate(notes):
        l, r = pad(hz(n_), d, amp * (1.2 if j == 0 else 1.0), att=att, rel=rel, trem=trem, bright=bright)
        MUS.put(st, l, r, send=send)

def melody(t0, notes, step, amp, inst=ocarina, k=0, durf=1.6, p=0.0, send=0.5):
    t = t0
    for i, n_ in enumerate(notes):
        if n_ is None:
            t += step; continue
        st = step * (2 if n_.endswith('-') else 1)
        n2 = n_.rstrip('-')
        s = inst(tr(n2, k), st * durf, amp)
        l, r = pan(s, p + 0.15 * math.sin(i))
        MUS.put(t, l, r, send=send)
        t += st

# C1 (0-7): opening — ocarina over soft C major pads
chord(0.3, ('C3', 'G3', 'E4'), 3.6, 0.022, att=1.5)
chord(3.7, ('F2', 'C3', 'A3'), 3.6, 0.022, att=1.2)
melody(1.0, ['E5', 'G5', 'A5-', 'G5', 'E5', 'D5-'], 0.55, 0.06)
# C2-C3 (7-17): light pizzicato walking
for k, n_ in enumerate(['C4', 'G3', 'A3', 'E3', 'F3', 'C4', 'G3', 'G3'] * 2):
    MUS.put(7.2 + k * 0.6, pizz(hz(n_), 0.06), send=0.25)
for t0, n_ in ((12.4, 'E6'), (13.3, 'D6'), (14.1, 'C6'), (15.0, 'G5'), (15.6, 'A5'), (16.2, 'E5')):
    MUS.put(t0, celesta(hz(n_), 1.5, 0.035), send=0.6)
# C4 (17-23): comedy hits
for t0, n_ in ((18.0, 'G4'), (18.12, 'E4'), (19.6, 'C4'), (20.0, 'C5'), (20.2, 'G4'), (22.0, 'C5'), (22.15, 'E5'), (22.3, 'G5')):
    MUS.put(t0, pizz(hz(n_), 0.07), send=0.25)
# C5-C6 (23-31): hawk — low drone and tremolo, rising
chord(23.2, ('A1', 'E2'), 8.0, 0.04, att=2.0, rel=0.8, bright=1.2)
for st, n_ in ((24.0, 'C4'), (26.0, 'D4'), (27.5, 'Eb4'), (29.0, 'E4')):
    l, r = pad(hz(n_), 31.0 - st, 0.02, att=0.6, rel=0.3, trem=0.8); MUS.put(st, l, r, send=0.5)
# C7 end -> C8 (34-39): pizzicato "it was me?" + descending celesta blush
for t0, n_ in ((34.2, 'C5'), (34.5, 'G4'), (34.8, 'E5')):
    MUS.put(t0, pizz(hz(n_), 0.06), send=0.3)
for t0, n_ in ((36.4, 'C7'), (36.6, 'A6'), (36.8, 'G6'), (37.0, 'E6'), (37.4, 'D6'), (38.3, 'C6')):
    MUS.put(t0, celesta(hz(n_), 1.4, 0.03), send=0.6)
chord(35.2, ('F3', 'A3', 'C4', 'E4'), 3.8, 0.016, att=1.0)
# C9 (39-47): montage — motif on harp, one rising key per gift
for b, k in ((39.0, 0), (41.667, 2), (44.333, 4)):
    for i, n_ in enumerate(['E5', 'G5', 'A5', 'C6', 'A5']):
        MUS.put(b + 0.2 + i * 0.3, harp(tr(n_, k), 1.6, 0.05), send=0.5)
    chord(b, (('C3', 'G3', 'E4'), ('D3', 'A3', 'F#4'), ('E3', 'B3', 'G#4'))[k // 2], 2.7, 0.018, att=0.3, rel=0.6)
# C10 (47-53): sunset — the motif in full on ocarina
chord(47.0, ('C3', 'G3', 'E4'), 3.0, 0.025, att=1.2)
chord(50.0, ('A2', 'E3', 'C4'), 3.2, 0.025, att=1.0)
melody(47.5, MOTIF, 0.6, 0.065, durf=1.4)
# C11-C12 (53-64): rain — sparse piano; the tug walk on pizz; tender at the end
for t0, n_ in ((53.2, 'A4'), (54.8, 'E4'), (56.4, 'C5'), (57.4, 'B4')):
    MUS.put(t0, piano(hz(n_), 3.0, 0.04), send=0.6)
for k in range(7):
    MUS.put(58.0 + k * 0.5, pizz(hz(['A3', 'C4', 'D4', 'E4', 'G4', 'A4', 'C5'][k]), 0.05), send=0.25)
chord(61.3, ('F3', 'C4', 'A4'), 2.9, 0.02, att=1.0)
melody(61.8, ['C6', 'A5', 'G5-'], 0.5, 0.045, inst=celesta, durf=2.5)
# C13-C14 (64-74): frost and first snow — A minor
chord(64.0, ('A2', 'E3', 'C4'), 5.2, 0.022, att=2.0)
chord(69.0, ('F2', 'C3', 'A3'), 5.2, 0.02, att=2.0)
melody(65.0, ['E6', None, 'D6', 'C6', None, 'A5'], 0.6, 0.03, inst=celesta, durf=2.5)
melody(70.0, ['E5', 'G5', 'A5-', 'G5', 'E5-'], 0.7, 0.045)
# C15-C16 (74-84.5): blizzard — ominous low pad, tremolo cluster rising with the thread
chord(74.0, ('A1', 'E2', 'A2'), 10.5, 0.045, att=1.0, rel=0.05, bright=1.2)
for st, n_ in ((80.0, 'E4'), (80.8, 'F4'), (81.6, 'G4'), (82.4, 'G#4'), (83.2, 'A4')):
    l, r = pad(hz(n_), 84.5 - st, 0.018, att=0.3, rel=0.02, trem=0.9); MUS.put(st, l, r, send=0.4)
# 84.5-89.0: SILENCE (handled in the mix)
# C17 end -> C18 (89-95): one ocarina note out of the silence, then the motif swells in A minor -> C
l, r = pan(ocarina(hz('E5'), 2.2, 0.05), 0.0); MUS.put(89.0, l, r, send=0.7)
chord(89.6, ('A2', 'E3', 'C4'), 2.6, 0.018, att=1.5)
chord(91.2, ('F2', 'C3', 'A3', 'E4'), 2.2, 0.03, att=0.8)
chord(93.3, ('C3', 'G3', 'E4', 'G4'), 2.4, 0.032, att=0.6, rel=1.4)
melody(91.0, ['E5', 'G5', 'A5', 'C6-', 'D6', 'E6-'], 0.42, 0.07, durf=1.5)
for k, n_ in enumerate(['C4', 'E4', 'G4', 'C5', 'E5', 'G5', 'C6', 'E6']):
    MUS.put(93.2 + k * 0.08, harp(hz(n_), 2.4, 0.04), send=0.6)
# C19 (95-102): moon lullaby — celesta motif, slow
chord(95.0, ('A2', 'E3', 'C4'), 3.6, 0.018, att=1.5)
chord(98.5, ('F2', 'C3', 'A3'), 3.8, 0.018, att=1.5)
melody(95.6, MOTIF, 0.75, 0.035, inst=celesta, durf=2.5)
# C20 (102-114): timelapse — harp arpeggios, accelerating; modulation to D major
t = 102.0; step_ = 0.38; k = 0
prog = [('A2', ['A3', 'C4', 'E4', 'A4']), ('F2', ['F3', 'A3', 'C4', 'F4']), ('C3', ['C4', 'E4', 'G4', 'C5']),
        ('G2', ['G3', 'B3', 'D4', 'G4']), ('D3', ['D4', 'F#4', 'A4', 'D5']), ('A2', ['A3', 'C#4', 'E4', 'A4']),
        ('G2', ['G3', 'B3', 'D4', 'G4']), ('D3', ['D4', 'F#4', 'A4', 'D5'])]
for bi, (bass, arp) in enumerate(prog):
    dur = 1.5
    l, r = pad(hz(bass), dur + 0.4, 0.03, att=0.2, rel=0.5, harm=4); MUS.put(102.0 + bi * 1.5, l, r, send=0.4)
    for j in range(8):
        n_ = arp[j % 4] if j < 4 else arp[3 - (j % 4)]
        MUS.put(102.0 + bi * 1.5 + j * dur / 8, harp(hz(n_) * (2 if bi >= 4 else 1), 1.2, 0.035), send=0.5)
melody(108.0, ['F#5', 'A5', 'B5', 'D6-', 'B5', 'A5', 'F#5-'], 0.42, 0.05)
SFX.put(109.6, boom(0.6, 0.0, f0=1, f1=1))
# C21-C22 (114-125): warm D major ending
chord(114.0, ('D3', 'A3', 'F#4'), 4.2, 0.024, att=1.2)
for k, n_ in enumerate(['D5', 'F#5', 'A5', 'B5', 'A5', 'F#5']):
    MUS.put(114.3 + k * 0.55, celesta(hz(n_), 1.6, 0.03), send=0.6)
chord(118.0, ('G2', 'D3', 'B3', 'D4'), 2.6, 0.03, att=0.8)
chord(120.4, ('D2', 'A2', 'F#3', 'A3', 'D4'), 4.6, 0.032, att=0.6, rel=2.5)
melody(118.3, ['F#5', 'A5', 'B5', 'D6-', 'B5', 'A5', 'F#5', 'E5', 'D5-'], 0.5, 0.065, durf=1.6)
for n_ in ('D6', 'A6'):
    MUS.put(123.0, celesta(hz(n_), 2.0, 0.03), send=0.8)

# ------------------------------------------------------------------ mix
def ir():
    n = int(3.2 * SR); tt = np.arange(n) / SR; out = []
    for _ in range(2):
        x = lp(rng.normal(0, 1, n) * np.exp(-tt / 0.65), 6500)
        x[:int(0.02 * SR)] *= np.linspace(0, 1, int(0.02 * SR))
        out.append(np.concatenate([np.zeros(int(0.02 * SR)), x])[:n])
    g = 1 / math.sqrt(np.sum(out[0] ** 2))
    return out[0] * g, out[1] * g
IRL, IRR = ir()

# music ducks under the big gusts and the hawk dive
duck = 1 - 0.4 * S(31.0, 31.2, T) * (1 - S(33.6, 34.1, T))
MUS.l *= duck; MUS.r *= duck; MUS.w *= duck

def bus_out(b, wet=0.85):
    return b.l + fftconvolve(b.w, IRL)[:N] * wet, b.r + fftconvolve(b.w, IRR)[:N] * wet
ml, mr = bus_out(MUS); sl, sr = bus_out(SFX)
L = ml + sl + AMB.l; R = mr + sr + AMB.r
# THE SILENCE: everything (including reverb tails) cut at the snap, back from 89.0
sil = 1 - S(84.52, 84.62, T) * (1 - S(88.95, 89.4, T))
L *= sil; R *= sil
mono = np.abs(L) + np.abs(R)
k = int(0.35 * SR)
envl = np.sqrt(np.convolve(mono ** 2, np.ones(k) / k, mode='same')) + 1e-6
ref = np.percentile(envl, 90)
g = np.clip((envl / ref) ** -0.35, 0.6, 2.4)
g = np.convolve(g, np.ones(k) / k, mode='same')
g = np.where(sil < 0.5, 1.0, g)                 # never lift the silence
L *= g; R *= g
pl, pr = bus_out(POST, wet=0.9)                 # the cracks in the silence, at a fixed level
L += pl * 0.7; R += pr * 0.7
fade = S(0, 1.2, T) * (1 - S(123.6, 125.0, T))
L *= fade; R *= fade
pk = np.percentile(np.abs(np.concatenate([L, R])), 99.97)
L = np.tanh(L / pk * 0.9) * 0.88
R = np.tanh(R / pk * 0.9) * 0.88
wavfile.write('out/scarecrow.wav', SR, (np.stack([L, R], -1) * 32767).astype(np.int16))
print('audio ok peak_pre=%.3f' % pk)
