#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""빛지기 (THE KEEPER) -- soundtrack and sound design, fully synthesized, locked to the cut list."""
import numpy as np, math
from scipy.signal import butter, sosfilt, fftconvolve
from scipy.io import wavfile

SR = 44100
DUR = 60.0
N = int(DUR * SR)
T = np.arange(N) / SR
rng = np.random.default_rng(1104)

def S(a, b, t):
    x = np.clip((np.asarray(t, float) - a) / (b - a), 0, 1)
    return x * x * (3 - 2 * x)

def mf(m):
    return 440.0 * 2 ** ((m - 69) / 12.0)

NOTE = {'C': 0, 'C#': 1, 'D': 2, 'Eb': 3, 'E': 4, 'F': 5, 'F#': 6, 'G': 7, 'Ab': 8, 'A': 9, 'Bb': 10, 'B': 11}
def nm(s):
    name, octv = s[:-1], int(s[-1])
    return 12 * (octv + 1) + NOTE[name]

def bp(x, lo, hi, order=2):
    return sosfilt(butter(order, [lo, hi], btype='band', fs=SR, output='sos'), x)

def lp(x, fc, order=2):
    return sosfilt(butter(order, fc, btype='low', fs=SR, output='sos'), x)

def hp(x, fc, order=2):
    return sosfilt(butter(order, fc, btype='high', fs=SR, output='sos'), x)

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
        s.l[i:i + n] += l[a:a + n] * gain
        s.r[i:i + n] += r[a:a + n] * gain
        if send > 0:
            s.w[i:i + n] += 0.5 * (l[a:a + n] + r[a:a + n]) * gain * send

MUS = Bus(); SFX = Bus(); AMB = Bus()

def tg(d):
    return np.arange(int(d * SR)) / SR

def env(tt, d, att, rel):
    a = np.clip(tt / max(att, 1e-3), 0, 1)
    r = np.clip((d - tt) / max(rel, 1e-3), 0, 1)
    return (a * a * (3 - 2 * a)) * (r * r * (3 - 2 * r))

def pan(sig, p):
    th = (p + 1) * math.pi / 4
    return sig * math.cos(th), sig * math.sin(th)

# ------------------------------------------------------------------ instruments
def pad(f, d, amp, harm=6, att=1.2, rel=1.6, vib=0.0, bright=1.5):
    tt = tg(d); e = env(tt, d, att, rel)
    l = np.zeros_like(tt); r = np.zeros_like(tt)
    vm = 1 + vib * np.sin(2 * np.pi * 5.2 * tt)
    for h in range(1, harm + 1):
        g = 1.0 / h ** bright
        l += g * np.sin(2 * np.pi * f * h * 1.0016 * np.cumsum(vm) / SR + h)
        r += g * np.sin(2 * np.pi * f * h * 0.9984 * np.cumsum(vm) / SR + 2 * h)
    return l * e * amp, r * e * amp

def piano(f, d, amp):
    tt = tg(d); sig = np.zeros_like(tt)
    for h in range(1, 10):
        if f * h > 10000:
            break
        inh = h * (1 + 0.0004 * h * h)
        sig += (1.0 / h ** 1.3) * np.sin(2 * np.pi * f * inh * tt + h) * np.exp(-tt * (0.9 + 0.55 * h))
    ham = np.exp(-tt / 0.004) * rng.normal(0, 1, len(tt)) * 0.03
    sig = (sig + ham) * np.clip(tt / 0.002, 0, 1) * np.clip((d - tt) / 0.3, 0, 1)
    return sig * amp

def bell(f, d, amp, dec=1.0):
    tt = tg(d); sig = np.zeros_like(tt)
    for ratio, a, k in ((1, 1.0, 1.0), (2.0, 0.5, 1.4), (2.76, 0.45, 1.9), (5.4, 0.2, 3.0), (8.9, 0.08, 4.4)):
        if f * ratio > 15000:
            continue
        sig += a * np.sin(2 * np.pi * f * ratio * tt + ratio) * np.exp(-tt * k * dec * 1.2)
    return sig * np.clip(tt / 0.002, 0, 1) * amp

def boom(d, amp, f0=120, f1=32, tau=0.25):
    tt = tg(d); f = f1 + (f0 - f1) * np.exp(-tt / tau)
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-tt / (d * 0.35)) * np.clip(tt / 0.003, 0, 1) * amp

def noise(d):
    return rng.normal(0, 1, int(d * SR))

def click(amp, d=0.012, fc=3000):
    x = hp(noise(d), fc) * np.exp(-tg(d) / 0.0025)
    return x * amp

def metal(f, d, amp):
    tt = tg(d); sig = np.zeros_like(tt)
    for ratio, a in ((1, 1), (1.47, 0.7), (2.09, 0.5), (2.93, 0.35), (3.97, 0.2)):
        sig += a * np.sin(2 * np.pi * f * ratio * tt + ratio * 3) * np.exp(-tt * (6 + 4 * ratio))
    sig += hp(noise(d), 2000) * np.exp(-tt / 0.006) * 0.4
    return sig * amp

def sweep_noise(d, f0, f1, envf, amp, bw=(0.6, 1.6)):
    n = int(d * SR); x = rng.normal(0, 1, n); out = np.zeros(n)
    ch, hop = 2048, 1024; win = np.hanning(ch)
    for i in range(0, max(1, n - ch), hop):
        u = (i + ch / 2) / n
        fc = f0 * (f1 / f0) ** u
        out[i:i + ch] += bp(x[i:i + ch], max(fc * bw[0], 25), min(fc * bw[1], SR * 0.45)) * win
    return out * envf(np.arange(n) / SR) * amp

# ------------------------------------------------------------------ cut map / sound perspective
CUTS = [(0, 5, 'ext'), (5, 9, 'int'), (9, 12, 'int'), (12, 16, 'ext'), (16, 20, 'boat'), (20, 23, 'scope'),
        (23, 26, 'int'), (26, 29, 'int'), (29, 32, 'int'), (32, 35, 'int'), (35, 39, 'ext'), (39, 42, 'boat'),
        (42, 45, 'int'), (45, 49, 'ext'), (49, 52, 'int'), (52, 55, 'int'), (55, 57, 'int'), (57, 60.1, 'ext')]

def persp(kind_vals):
    """per-sample gain from a dict kind->gain, 15 ms crossfades at cuts"""
    g = np.zeros(N)
    for a, b, k in CUTS:
        i0, i1 = int(a * SR), min(int(b * SR), N)
        g[i0:i1] = kind_vals.get(k, 0.0)
    w = int(0.015 * SR)
    return np.convolve(g, np.ones(w) / w, mode='same')

storm = (0.45 + 0.55 * S(1, 12, T)) * (1 - S(44.4, 45.4, T))
dawn = S(44.6, 45.6, T)

# ------------------------------------------------------------------ ambience beds
def stereo_bed(fn):
    return fn(noise(DUR)), fn(noise(DUR))

rl, rr = stereo_bed(lambda x: bp(x, 1400, 9000) * (1 + 0.25 * np.sin(2 * np.pi * 0.13 * T)))
g_rain_ext = persp({'ext': 0.55, 'boat': 1.0, 'scope': 0.45}) * storm
AMB.l += rl * 0.050 * g_rain_ext; AMB.r += rr * 0.050 * g_rain_ext

il, ir = stereo_bed(lambda x: lp(x, 900) * 1.6)
drip = np.zeros(N)
for tb in np.sort(rng.random(2600) * DUR):
    i = int(tb * SR)
    k = click(rng.uniform(0.2, 1.0), d=0.008, fc=2500)
    drip[i:i + len(k)] += k[:max(0, N - i)]
g_rain_int = persp({'int': 1.0}) * storm
AMB.l += (il * 0.040 + drip * 0.05) * g_rain_int
AMB.r += (ir * 0.040 + np.roll(drip, 900) * 0.05) * g_rain_int

def wind_fn(x):
    out = np.zeros(N); ch = 4096; win = np.hanning(ch)
    for i in range(0, N - ch, ch // 2):
        u = (i + ch / 2) / SR
        fc = 430 + 200 * math.sin(u * 0.7) + 100 * math.sin(u * 1.9 + 1)
        out[i:i + ch] += bp(x[i:i + ch], fc * 0.6, fc * 1.5) * win
    return out
wl, wr = stereo_bed(wind_fn)
gust = 0.6 + 0.4 * np.sin(2 * np.pi * 0.11 * T) * np.sin(2 * np.pi * 0.07 * T + 1)
g_wind = persp({'ext': 0.9, 'boat': 1.0, 'scope': 0.7, 'int': 0.30}) * storm * gust
AMB.l += wl * 0.10 * g_wind; AMB.r += wr * 0.10 * g_wind

swell = 0.55 + 0.45 * np.sin(2 * np.pi * T / 3.4) ** 2
vl, vr = stereo_bed(lambda x: lp(x, 420) * 2.0)
g_wave = persp({'ext': 0.45, 'boat': 1.0, 'scope': 0.5, 'int': 0.06}) * storm * swell
AMB.l += vl * 0.10 * g_wave; AMB.r += vr * 0.10 * g_wave

dl, dr = stereo_bed(lambda x: bp(x, 150, 1800))
dswell = 0.4 + 0.6 * np.sin(2 * np.pi * T / 5.0) ** 4
g_dawn = persp({'ext': 0.7, 'int': 0.12}) * dawn * dswell
AMB.l += dl * 0.035 * g_dawn; AMB.r += dr * 0.035 * g_dawn

# lens hum + rotation whoosh (C13), lamp hum (C1 before it dies)
lens_on = S(31.4, 31.6, T) * (1 - S(45.2, 47.8, T))
hum = (np.sin(2 * np.pi * 55 * T) + 0.4 * np.sin(2 * np.pi * 110 * T)) * 0.012
rot = np.abs(np.cos(2.1 * T)) ** 6
whoosh = bp(noise(DUR), 300, 1400) * rot * 0.05
g_lens = persp({'int': 1.0, 'ext': 0.15, 'boat': 0.1}) * lens_on
AMB.l += (hum + whoosh) * g_lens; AMB.r += (hum + np.roll(whoosh, 400)) * g_lens

# ------------------------------------------------------------------ thunder
def thunder(t0, amp, close):
    d = 4.5
    tt = tg(d)
    rumble = lp(noise(d), 180, order=3) * 3.0
    rumble *= (np.clip(tt / (0.05 if close else 0.4), 0, 1) * np.exp(-tt / (1.4 if close else 1.9))
               * (0.7 + 0.3 * np.sin(2 * np.pi * 3.1 * tt) * np.sin(2 * np.pi * 1.3 * tt)))
    sig = rumble
    if close:
        crack = hp(noise(0.4), 900) * np.exp(-tg(0.4) / 0.06) * 0.9
        sig = sig.copy(); sig[:len(crack)] += crack
    l, r = pan(sig, rng.uniform(-0.4, 0.4))
    SFX.put(t0, l, r, send=0.35, gain=amp)

for t0, a, delay, close in ((2.6, 0.35, 1.2, False), (9.5, 0.3, 0.0, False), (11.6, 1.0, 0.05, True),
                            (14.4, 0.85, 0.35, True), (18.7, 0.5, 0.9, False), (27.5, 0.9, 0.05, True),
                            (37.7, 0.45, 1.0, False), (43.3, 0.3, 1.1, False)):
    thunder(t0 + delay, 0.32 * a, close)

# ------------------------------------------------------------------ sound effects
# C1 lamp sputter: buzz gated by the same flicker pattern as the picture
pat = [1, 0.2, 1, 1, 0, 0.6, 0, 0, 1, 0.1, 0, 0, 0.5, 0, 0, 0, 0.3]
bz_t = tg(1.25)
buzz = np.sign(np.sin(2 * np.pi * 120 * bz_t)) * 0.4 + np.sin(2 * np.pi * 240 * bz_t) * 0.3
gate = np.array([pat[min(int(x * 14), len(pat) - 1)] for x in bz_t])
gate = np.convolve(gate, np.ones(200) / 200, mode='same')
crack_n = hp(noise(1.25), 3000) * (rng.random(len(bz_t)) < 0.004) * 3
SFX.put(2.72, lp(buzz * gate, 2500) * 0.035 + crack_n * 0.05, send=0.2)
SFX.put(3.95, boom(0.6, 0.05, f0=90, f1=40, tau=0.05))
# C2 taps, pop, glass
for tp in (5.75, 6.45, 7.1):
    SFX.put(tp, metal(2600, 0.35, 0.10), send=0.4)
    SFX.put(tp + 0.02, hp(noise(0.25), 3000) * np.exp(-tg(0.25) / 0.03) * 0.03 * (rng.random() + 0.5))
SFX.put(7.45, boom(0.5, 0.25, f0=160, f1=50, tau=0.03))
SFX.put(7.45, hp(noise(0.3), 1500) * np.exp(-tg(0.3) / 0.04) * 0.30, send=0.3)
for k in range(26):
    tb = 7.47 + rng.random() ** 1.6 * 0.9
    l, r = pan(bell(rng.uniform(3500, 7500), 0.25, rng.uniform(0.01, 0.03), dec=4), rng.uniform(-0.8, 0.8))
    SFX.put(tb, l, r, send=0.4)
# C3 flame flinch: a soft breathy dip
SFX.put(9.62, sweep_noise(0.6, 1800, 500, lambda x: np.sin(np.pi * np.clip(x / 0.6, 0, 1)), 0.05), send=0.3)
# C5 flashlight clicks
for a, b in ((16.7, 16.9), (17.05, 17.25), (17.4, 17.6), (18.3, 19.35)):
    SFX.put(a, click(0.22), send=0.1)
    SFX.put(b, click(0.14), send=0.1)
SFX.put(17.8, lp(noise(1.6), 1600) * np.exp(-tg(1.6) / 0.35) * 0.22, send=0.3)
# C6 heartbeat (accelerating)
for tb in (20.15, 20.85, 21.5, 22.05, 22.55):
    for dt, a in ((0, 1.0), (0.17, 0.7)):
        SFX.put(tb + dt, boom(0.3, 0.30 * a, f0=70, f1=38, tau=0.05))
for t0 in (20.6, 21.5, 22.3):
    SFX.put(t0, lp(noise(1.3), 1200) * np.exp(-tg(1.3) / 0.3) * 0.07, send=0.3)
# C8 ladder clanks
for k in range(7):
    tb = 26.12 + k * 0.45
    SFX.put(tb, metal(rng.uniform(380, 520), 0.5, 0.09), send=0.35)
# C9 ember carried: tremolo hum, then socket clunk
tt = tg(2.5)
ember = (np.sin(2 * np.pi * 220 * tt) + 0.5 * np.sin(2 * np.pi * 330.7 * tt) + 0.3 * np.sin(2 * np.pi * 441.3 * tt))
ember *= env(tt, 2.5, 0.4, 0.3) * (0.7 + 0.3 * np.sin(2 * np.pi * 7 * tt)) * 0.03
SFX.put(29.4, ember, send=0.5)
SFX.put(31.45, boom(0.5, 0.25, f0=130, f1=55, tau=0.04))
SFX.put(31.45, metal(900, 0.8, 0.14), send=0.5)
# C10 -> C11 flare
SFX.put(33.6, sweep_noise(1.45, 300, 9000, lambda x: S(0, 1.4, x) ** 2.2, 0.20), send=0.3)
SFX.put(35.0, boom(3.0, 0.55, f0=110, f1=30, tau=0.3), send=0.2)
SFX.put(35.0, lp(noise(2.5), 700) * np.exp(-tg(2.5) / 0.6) * 0.18, send=0.4)
# C12 tiller creak, wave crash
tt = tg(0.45)
creak = np.sin(2 * np.pi * (280 + 60 * np.sin(2 * np.pi * 23 * tt)) * tt) * env(tt, 0.45, 0.05, 0.1)
SFX.put(40.25, bp(creak, 200, 1500) * 0.08, send=0.2)
SFX.put(40.95, lp(noise(2.6), 2500) * np.exp(-tg(2.6) / 0.55) * np.clip(tg(2.6) / 0.03, 0, 1) * 0.45, send=0.35)
SFX.put(40.95, boom(1.5, 0.30, f0=80, f1=35, tau=0.12))
SFX.put(39.4, lp(noise(1.4), 1800) * np.exp(-tg(1.4) / 0.3) * 0.16, send=0.3)
# C15 ladder + footsteps
for tb in (49.15, 49.45, 49.75):
    SFX.put(tb, metal(rng.uniform(420, 520), 0.35, 0.05), send=0.3)
for k in range(4):
    SFX.put(50.05 + 0.34 * k, lp(noise(0.12), 600) * np.exp(-tg(0.12) / 0.025) * 0.20, send=0.25)
# C16 the toy clicks on
SFX.put(53.5, metal(1500, 0.3, 0.05), send=0.3)
SFX.put(54.17, click(0.35, fc=2500), send=0.2)
SFX.put(54.19, click(0.18, fc=4000), send=0.2)
# C17 flicker ticks + warm bloom
for tb in (55.12, 55.42):
    SFX.put(tb, click(0.12, d=0.02, fc=1800), send=0.2)
tt = tg(2.0)
SFX.put(55.85, (np.sin(2 * np.pi * 293.66 * tt) + 0.5 * np.sin(2 * np.pi * 440 * tt)) * env(tt, 2.0, 0.2, 1.4) * 0.03,
        send=0.5)
# gulls
def gull(t0, amp, p):
    d = 0.42; tt = tg(d)
    f = 1900 - 700 * (tt / d) + 90 * np.sin(2 * np.pi * 24 * tt)
    sig = np.sin(2 * np.pi * np.cumsum(f) / SR) * env(tt, d, 0.03, 0.15)
    sig = bp(sig + 0.3 * np.sin(2 * np.pi * np.cumsum(2 * f) / SR) * env(tt, d, 0.03, 0.15), 800, 5000)
    l, r = pan(sig, p)
    SFX.put(t0, l, r, send=0.5, gain=amp)
for t0, a, p in ((45.7, 0.05, -0.5), (46.3, 0.035, -0.4), (47.9, 0.04, 0.6), (57.7, 0.04, -0.3), (58.9, 0.03, 0.5)):
    gull(t0, a, p)

# ------------------------------------------------------------------ music
D2, D3 = nm('D2'), nm('D3')
# opening: drone + three piano notes, broken off when the lamp dies
for m, a, st, d in ((D2, 0.05, 0.3, 12.5), (nm('A2'), 0.03, 1.0, 11.5)):
    l, r = pad(mf(m), d, a, harm=4, att=2.5, rel=2.5); MUS.put(st, l, r, send=0.4)
for t0, n_ in ((0.9, 'A4'), (1.7, 'D5'), (2.45, 'E5')):
    l, r = pan(piano(mf(nm(n_)), 3.0, 0.12), -0.2); MUS.put(t0, l, r, send=0.6)
MUS.put(2.95, piano(mf(nm('F5')), 0.25, 0.05), send=0.6)          # cut short by the sputter
# tension under C2-C3
for m, a in ((nm('D3'), 0.025), (nm('Eb3'), 0.018), (nm('A3'), 0.016)):
    l, r = pad(mf(m), 7.5, a, harm=5, att=2.0, rel=1.5, vib=0.002); MUS.put(5.0, l, r, send=0.4)
# storm build C4-C5: low pulse ostinato + rising strings
beat = 60 / 104
k = 0
tb = 12.0
while tb < 20.0:
    a = 0.10 + 0.10 * (tb - 12) / 8
    MUS.put(tb, piano(mf(nm('D2')), 0.5, a) + piano(mf(nm('D3')), 0.5, a * 0.5), send=0.2)
    tb += beat / 2
for st, ch, d in ((12.0, ('D3', 'F3', 'A3'), 4.0), (16.0, ('Bb2', 'F3', 'D4'), 4.0)):
    for n_ in ch:
        l, r = pad(mf(nm(n_)), d + 0.5, 0.030 + 0.01 * (st > 14), harm=6, att=1.5, rel=0.6, vib=0.003)
        MUS.put(st, l, r, send=0.4)
for t0 in (14.4, 18.7):
    MUS.put(t0 + 0.3, boom(1.6, 0.18, f0=90, f1=40, tau=0.15), send=0.2)
# C6: high tension tone
l, r = pad(mf(nm('A5')), 3.2, 0.012, harm=3, att=0.8, rel=0.4, vib=0.006); MUS.put(20.0, l, r, send=0.5)
# C7: silence 24.0-25.3, then the resolve
l, r = pad(mf(nm('D3')), 4.4, 0.05, harm=6, att=0.8, rel=1.2, vib=0.003); MUS.put(25.3, l, r, send=0.5)
l, r = pad(mf(nm('A3')), 4.0, 0.035, harm=6, att=1.0, rel=1.2, vib=0.003); MUS.put(25.6, l, r, send=0.5)
for t0, n_ in ((25.35, 'D4'), (26.25, 'F4'), (27.15, 'A4'), (28.05, 'G4')):
    MUS.put(t0, piano(mf(nm(n_)), 2.5, 0.09), send=0.6)
# C9: suspended bells
for t0, n_ in ((29.5, 'A5'), (30.4, 'D6'), (31.2, 'E6')):
    l, r = pan(bell(mf(nm(n_)), 3.0, 0.035), 0.3); MUS.put(t0, l, r, send=0.8)
# C10: ring chimes climbing D-minor pentatonic
pent = ['D5', 'F5', 'G5', 'A5', 'C6', 'D6', 'F6', 'G6', 'A6', 'C7', 'D7']
for k_, n_ in enumerate(pent):
    l, r = pan(bell(mf(nm(n_)), 2.5, 0.05), -0.6 + 0.12 * k_); MUS.put(32.25 + 0.16 * k_, l, r, send=0.8)
for n_ in ('D3', 'A3', 'D4', 'F4'):
    l, r = pad(mf(nm(n_)), 3.2, 0.03, harm=6, att=2.2, rel=0.2, vib=0.003); MUS.put(32.0, l, r, send=0.4)
# C11-C12: main theme  Bb - F - C - Dm
prog = [(35.0, ('Bb1', 'Bb2', 'F3', 'D4', 'F4')), (36.75, ('F1', 'F2', 'C4', 'F4', 'A4')),
        (38.5, ('C2', 'C3', 'G3', 'E4', 'G4')), (40.25, ('D2', 'D3', 'A3', 'F4', 'A4'))]
for st, ch in prog:
    for j, n_ in enumerate(ch):
        a = (0.07 if j < 2 else 0.045)
        l, r = pad(mf(nm(n_)), 1.9 + (0.6 if st > 40 else 0), a, harm=7, att=0.25, rel=0.8, vib=0.004, bright=1.3)
        MUS.put(st, l, r, send=0.45)
    MUS.put(st, boom(1.2, 0.20, f0=100, f1=40, tau=0.1), send=0.2)
theme = [(35.0, 'D5'), (35.44, 'F5'), (35.88, 'A5'), (36.32, 'G5'), (36.75, 'F5'), (37.6, 'C5'), (38.5, 'E5'),
         (38.94, 'G5'), (39.38, 'C6'), (39.82, 'Bb5'), (40.25, 'A5'), (41.1, 'F5')]
for t0, n_ in theme:
    l, r = pan(bell(mf(nm(n_)), 2.2, 0.075), 0.2); MUS.put(t0, l, r, send=0.6)
    MUS.put(t0, piano(mf(nm(n_) - 12), 1.6, 0.10), send=0.5)
# C13: music drops out at 42.0 (only the lens drone remains)
# C14: dawn pad (D major add9)
for n_, a in (('D3', 0.035), ('A3', 0.028), ('F#4', 0.022), ('E5', 0.012)):
    l, r = pad(mf(nm(n_)), 10.5, a, harm=5, att=2.5, rel=2.0, vib=0.002); MUS.put(44.8, l, r, send=0.6)
for t0, n_ in ((46.2, 'A4'), (47.6, 'F#4'), (50.2, 'E4'), (51.6, 'D4')):
    MUS.put(t0, piano(mf(nm(n_)), 3.0, 0.07), send=0.7)
# C17-C18: the motif returns, now in D major
for t0, n_ in ((55.85, 'A4'), (56.35, 'D5'), (56.85, 'E5'), (57.35, 'F#5'), (58.1, 'E5'), (58.75, 'D5')):
    l, r = pan(piano(mf(nm(n_)), 3.2, 0.13), -0.1); MUS.put(t0, l, r, send=0.65)
for n_, a in (('D2', 0.05), ('D3', 0.04), ('A3', 0.032), ('F#4', 0.026), ('A4', 0.018)):
    l, r = pad(mf(nm(n_)), 4.6, a, harm=6, att=1.2, rel=1.8, vib=0.002); MUS.put(55.8, l, r, send=0.55)
for n_ in ('D6', 'A6'):
    l, r = pan(bell(mf(nm(n_)), 2.5, 0.03), 0.4); MUS.put(58.75, l, r, send=0.9)

# ------------------------------------------------------------------ mix
def ir():
    n = int(3.0 * SR); tt = np.arange(n) / SR; out = []
    for _ in range(2):
        x = lp(rng.normal(0, 1, n) * np.exp(-tt / 0.6), 6000)
        x[:int(0.02 * SR)] *= np.linspace(0, 1, int(0.02 * SR))
        out.append(np.concatenate([np.zeros(int(0.02 * SR)), x])[:n])
    g = 1 / math.sqrt(np.sum(out[0] ** 2))
    return out[0] * g, out[1] * g
IRL, IRR = ir()

duck = 1 - (S(23.95, 24.05, T) * (1 - S(25.2, 25.4, T)))      # C7 silence
duck *= 1 - (S(41.8, 42.1, T) * (1 - S(44.6, 45.2, T)))       # C13 music drops out
MUS.l *= duck; MUS.r *= duck; MUS.w *= duck

def bus_out(b, wet=0.8):
    wl_ = fftconvolve(b.w, IRL)[:N]; wr_ = fftconvolve(b.w, IRR)[:N]
    return b.l + wl_ * wet, b.r + wr_ * wet

ml, mr = bus_out(MUS)
sl, sr_ = bus_out(SFX)
L = ml + sl + AMB.l
R = mr + sr_ + AMB.r
fade = S(0, 0.6, T) * (1 - S(59.0, 60.0, T))
L *= fade; R *= fade
pk = max(np.abs(L).max(), np.abs(R).max())
L = np.tanh(L / pk * 1.6) / np.tanh(1.6) * 0.89
R = np.tanh(R / pk * 1.6) / np.tanh(1.6) * 0.89
wavfile.write('keeper.wav', SR, (np.stack([L, R], -1) * 32767).astype(np.int16))
print('audio ok  peak_pre=%.3f' % pk)
