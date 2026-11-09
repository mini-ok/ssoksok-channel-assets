#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""홀씨 (HOLSSI) -- 90 s soundtrack, fully synthesized, locked to the cut list."""
import numpy as np, math
from scipy.signal import butter, sosfilt, fftconvolve
from scipy.io import wavfile

SR = 44100
DUR = 97.0
N = int(DUR * SR)
T = np.arange(N) / SR
rng = np.random.default_rng(90)

def S(a, b, t):
    x = np.clip((np.asarray(t, float) - a) / (b - a), 0, 1)
    return x * x * (3 - 2 * x)

NOTE = {'C': 0, 'C#': 1, 'D': 2, 'Eb': 3, 'E': 4, 'F': 5, 'F#': 6, 'G': 7, 'Ab': 8, 'A': 9, 'Bb': 10, 'B': 11}
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

MUS = Bus(); SFX = Bus(); AMB = Bus()
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
def celesta(f, d, amp):
    tt = tg(d); s = np.zeros_like(tt)
    for ratio, a, k in ((1, 1.0, 2.2), (2.0, 0.35, 3.5), (3.0, 0.12, 5.0), (4.07, 0.08, 7.0)):
        s += a * np.sin(2 * np.pi * f * ratio * tt) * np.exp(-tt * k)
    s += np.sin(2 * np.pi * f * 6.1 * tt) * np.exp(-tt * 40) * 0.15
    return s * np.clip(tt / 0.002, 0, 1) * amp

def pad(f, d, amp, harm=6, att=1.2, rel=1.6, vib=0.002, bright=1.6):
    tt = tg(d); e = env(tt, d, att, rel)
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

def bird(t0, amp, p, f0=3200, notes=4):
    for k in range(notes):
        d = rng.uniform(0.06, 0.14); tt = tg(d)
        f = f0 * rng.uniform(0.85, 1.25) + 900 * np.sin(np.pi * tt / d) * rng.choice([-1, 1])
        s = np.sin(2 * np.pi * np.cumsum(f) / SR) * env(tt, d, 0.01, 0.03)
        l, r = pan(s, p)
        SFX.put(t0 + k * rng.uniform(0.09, 0.16), l, r, send=0.4, gain=amp)

def thunder(t0, amp, close=False):
    d = 5.0; tt = tg(d)
    rum = lp(noise(d), 160, 3) * 3.0 * np.clip(tt / (0.04 if close else 0.4), 0, 1) * np.exp(-tt / 1.6)
    rum *= 0.7 + 0.3 * np.sin(2 * np.pi * 2.7 * tt) * np.sin(2 * np.pi * 1.1 * tt)
    if close:
        cr = hp(noise(0.4), 800) * np.exp(-tg(0.4) / 0.07)
        rum = rum.copy(); rum[:len(cr)] += cr
    l, r = pan(rum, rng.uniform(-0.3, 0.3))
    SFX.put(t0, l, r, send=0.35, gain=amp)

# ------------------------------------------------------------------ ambience beds
def stereo(fn):
    return fn(noise(DUR)), fn(noise(DUR))

meadow = S(0, 2.0, T) * (1 - S(19.6, 20.4, T)) + 0.6 * S(20, 21, T) * (1 - S(25.6, 26.4, T))
gust = 0.7 + 0.3 * np.sin(2 * np.pi * 0.09 * T) * np.sin(2 * np.pi * 0.05 * T + 1)
wl, wr = stereo(lambda x: bp(x, 250, 1400))
AMB.l += wl * 0.05 * meadow * gust; AMB.r += wr * 0.05 * meadow * gust
gl, gr = stereo(lambda x: bp(x, 2500, 9000) * (0.6 + 0.4 * np.sin(2 * np.pi * 0.3 * T) ** 2))
AMB.l += gl * 0.012 * meadow; AMB.r += gr * 0.012 * meadow

open_air = S(25.8, 26.6, T) * (1 - S(30.8, 31.2, T)) + 0.5 * S(31, 31.4, T) * (1 - S(35.8, 36.2, T))
ol, orr = stereo(lambda x: bp(x, 120, 900))
AMB.l += ol * 0.09 * open_air; AMB.r += orr * 0.09 * open_air
sea = (S(25.8, 26.6, T) * (1 - S(35.8, 36.2, T))) * (0.5 + 0.5 * np.sin(2 * np.pi * T / 4.2) ** 2)
sl_, sr_ = stereo(lambda x: lp(x, 600) * 1.8)
AMB.l += sl_ * 0.05 * sea; AMB.r += sr_ * 0.05 * sea

sky = S(36, 37, T) * (1 - S(47.8, 48.4, T))
kl, kr = stereo(lambda x: bp(x, 400, 2600))
AMB.l += kl * 0.030 * sky; AMB.r += kr * 0.030 * sky

storm = S(48, 51.5, T) * (1 - S(55.8, 56.2, T))
sw_l, sw_r = stereo(lambda x: bp(x, 150, 1100))
AMB.l += sw_l * 0.14 * storm; AMB.r += sw_r * 0.14 * storm
rain = S(51.5, 52.1, T) * (1 - S(55.8, 56.1, T))
rl, rr = stereo(lambda x: bp(x, 1200, 9000))
AMB.l += rl * 0.08 * rain; AMB.r += rr * 0.08 * rain

bleak = S(55.9, 56.4, T) * (1 - S(63.6, 64.3, T))
bl, br = stereo(lambda x: bp(x, 200, 700))
AMB.l += bl * 0.06 * bleak; AMB.r += br * 0.06 * bleak
drz = S(55.9, 56.4, T) * (1 - S(63.6, 64.3, T)) + S(64, 64.3, T) * (1 - S(65.4, 66.0, T))
dl, dr = stereo(lambda x: bp(x, 2000, 8000))
AMB.l += dl * 0.018 * drz; AMB.r += dr * 0.018 * drz

dawn = S(75.0, 77.0, T) * (1 - S(95.6, 97.0, T))
al, ar = stereo(lambda x: bp(x, 300, 1600))
AMB.l += al * 0.025 * dawn; AMB.r += ar * 0.025 * dawn

# ------------------------------------------------------------------ sound effects
for t0, a, p in ((1.4, 0.05, -0.6), (3.2, 0.04, 0.5), (5.1, 0.045, -0.2), (9.0, 0.04, 0.6), (11.0, 0.035, -0.5),
                 (14.5, 0.03, 0.3), (21.5, 0.04, -0.4), (24.0, 0.03, 0.6)):
    bird(t0, a, p, notes=rng.integers(3, 7))
for k in range(26):                     # ladybug footsteps C3
    SFX.put(12.4 + k * 0.17 + rng.uniform(-0.02, 0.02), click(0.05, fc=5000), send=0.1)
tt = tg(0.6)                            # wing buzz C4
buzz = np.sin(2 * np.pi * (190 + 20 * np.sin(2 * np.pi * 9 * tt)) * tt) * env(tt, 0.6, 0.05, 0.2)
SFX.put(17.6, bp(buzz + 0.3 * np.sign(buzz), 150, 3000) * 0.05, send=0.2)
SFX.put(18.3, whoosh(1.4, 300, 1800, 0.22, 0.3), send=0.3)        # the gust
SFX.put(25.8, whoosh(1.6, 200, 900, 0.12, 0.4), send=0.3)         # over the edge
for t0, p in ((32.6, 0.5), (33.1, 0.5), (34.6, -0.4)):           # distant dog
    tt = tg(0.18); f = 520 - 200 * tt / 0.18
    s = bp(np.sign(np.sin(2 * np.pi * np.cumsum(f) / SR)) * env(tt, 0.18, 0.01, 0.08), 300, 2200)
    l, r = pan(s, p); SFX.put(t0, l, r, send=0.6, gain=0.018)
for t0 in (36.3, 36.7, 37.1):                                       # swallows pass
    SFX.put(t0, whoosh(0.7, 600, 2500, 0.06, 0.5), send=0.2)
    bird(t0 + 0.1, 0.03, rng.uniform(-0.6, 0.6), f0=4200, notes=2)
SFX.put(37.35, whoosh(0.8, 400, 3000, 0.30, 0.35), send=0.2)       # the near miss
SFX.put(48.0, boom(4.0, 0.12, f0=60, f1=28, tau=1.0), send=0.3)    # storm presence
for t0, a, close in ((49.8, 0.25, False), (51.25, 0.3, False), (52.0, 0.55, True), (55.15, 0.5, True),
                     (58.5, 0.15, False)):
    thunder(t0, a, close)
for h in (53.0, 54.1):                                              # big drops hit the seed
    SFX.put(h, lp(noise(0.25), 1800) * np.exp(-tg(0.25) / 0.04) * 0.35, send=0.3)
    SFX.put(h, boom(0.3, 0.12, f0=180, f1=70, tau=0.03))
SFX.put(55.0, whoosh(1.2, 1500, 300, 0.12, 0.2), send=0.3)        # falling
r2 = np.random.default_rng(13)                                      # C13 plinks (synced to picture)
for k in range(18):
    t0 = 60.0 + r2.uniform(0, 4.0); r2.uniform(); r2.uniform()
    tt = tg(0.12)
    s = np.sin(2 * np.pi * rng.uniform(1800, 3200) * tt) * np.exp(-tt / 0.02) + click(1.0, d=0.12) * 0.3
    l, r = pan(s, rng.uniform(-0.7, 0.7)); SFX.put(t0, l, r, send=0.5, gain=0.02)
SFX.put(67.2, whoosh(2.8, 2000, 4000, 0.03, 0.5), send=0.6)        # snow hush
SFX.put(69.6, lp(noise(0.5), 900) * np.exp(-tg(0.5) / 0.1) * 0.06)  # crack of soil
tt = tg(0.7)                                                        # ladybug lands C15
buzz = np.sin(2 * np.pi * (200 + 25 * np.sin(2 * np.pi * 9 * tt)) * tt) * env(tt, 0.7, 0.1, 0.15)
SFX.put(78.0, bp(buzz + 0.3 * np.sign(buzz), 150, 3000) * 0.04, send=0.2)
SFX.put(83.3, whoosh(2.6, 250, 2200, 0.20, 0.3), send=0.35)       # the wind returns
for t0, p in ((86.8, -0.4), (87.2, 0.3)):
    SFX.put(t0, whoosh(0.7, 600, 2500, 0.04, 0.5), send=0.3)
    bird(t0 + 0.1, 0.025, p, f0=4200, notes=3)

# ------------------------------------------------------------------ music
MOTIF = ['D5', 'F#5', 'A5', 'B5', 'A5', 'F#5', 'E5', 'D5']
BEAT = 0.42
# C5-C8: the motif enters on celesta (sparse, then fuller)
def play_motif(t0, oct_shift=0, amp=0.10, pan_=0.0, step=BEAT, notes=None):
    for k, n_ in enumerate(notes or MOTIF):
        f = mf(nm(n_) + 12 * oct_shift)
        l, r = pan(celesta(f, 2.0, amp), pan_ + 0.2 * math.sin(k))
        MUS.put(t0 + k * step, l, r, send=0.55)

play_motif(20.3, amp=0.08, step=0.55)
play_motif(25.0, amp=0.09, step=0.5, notes=['A5', 'B5', 'D6', 'E6', 'D6', 'B5', 'A5', 'F#5'])
for st, ch in ((20.0, ('D3', 'A3', 'F#4')), (24.4, ('B2', 'F#3', 'D4')), (28.8, ('G2', 'D3', 'B3')),
               (33.2, ('A2', 'E3', 'C#4'))):
    for n_ in ch:
        l, r = pad(hz(n_), 4.8, 0.030, att=1.5, rel=1.4); MUS.put(st, l, r, send=0.45)
play_motif(30.0, amp=0.085, step=0.5)
play_motif(34.0, amp=0.08, step=0.45, notes=['F#5', 'E5', 'D5', 'E5', 'F#5', 'A5'])
# C8: music ducks for the near miss, resumes
# C9: the motif in full (celesta + harp + strings)
for st, ch in ((40.0, ('D2', 'D3', 'A3', 'F#4', 'A4')), (42.0, ('B1', 'B2', 'F#3', 'D4', 'F#4')),
               (44.0, ('G1', 'G2', 'D3', 'B3', 'D4')), (46.0, ('A1', 'A2', 'E3', 'C#4', 'E4'))):
    for j, n_ in enumerate(ch):
        l, r = pad(hz(n_), 2.4, 0.045 if j < 2 else 0.032, att=0.4, rel=0.8, bright=1.4); MUS.put(st, l, r, send=0.5)
    for k in range(8):
        n_ = ch[2 + k % 3]
        l, r = pan(harp(mf(nm(n_) + 12), 2.0, 0.06), -0.5 + k * 0.12); MUS.put(st + k * 0.25, l, r, send=0.5)
play_motif(40.0, amp=0.11, step=0.5)
play_motif(44.0, oct_shift=0, amp=0.11, step=0.5, notes=['A5', 'B5', 'D6', 'E6', 'F#6', 'E6', 'D6', 'A5'])
# C14: the long wait — a single note, then chords stack
l, r = pad(hz('A4'), 12.2, 0.025, harm=3, att=2.5, rel=1.0); MUS.put(64.0, l, r, send=0.6)
for st, n_, a in ((66.8, 'D3', 0.030), (68.6, 'F#3', 0.024), (70.4, 'A3', 0.024), (72.0, 'E4', 0.018),
                  (73.4, 'D2', 0.040)):
    l, r = pad(hz(n_), 76.3 - st, a, att=2.0, rel=0.6); MUS.put(st, l, r, send=0.55)
for t0, n_ in ((70.2, 'D5'), (72.2, 'F#5'), (74.0, 'A5'), (75.2, 'B5')):
    MUS.put(t0, piano(hz(n_), 3.0, 0.07), send=0.6)
# C15: theme climax in D major
for st, ch in ((76.0, ('D2', 'D3', 'A3', 'F#4', 'A4', 'D5')), (78.0, ('G1', 'G2', 'D3', 'B3', 'D4', 'G4'))):
    for j, n_ in enumerate(ch):
        l, r = pad(hz(n_), 2.5, 0.05 if j < 2 else 0.034, att=0.25, rel=0.9, bright=1.3); MUS.put(st, l, r, send=0.5)
play_motif(76.0, amp=0.13, step=0.5)
for k, n_ in enumerate(MOTIF):
    MUS.put(76.0 + k * 0.5, piano(mf(nm(n_) - 12), 1.8, 0.09), send=0.5)
# C16: breath
for n_ in ('A2', 'E3', 'C#4', 'E4'):
    l, r = pad(hz(n_), 3.4, 0.032, att=0.6, rel=1.0); MUS.put(80.0, l, r, send=0.6)
MUS.put(81.6, celesta(hz('A5'), 2.0, 0.06), send=0.7)
# C17: harp glissando as the seeds go
for k, n_ in enumerate(['D4', 'E4', 'F#4', 'A4', 'B4', 'D5', 'E5', 'F#5', 'A5', 'B5', 'D6', 'E6', 'F#6', 'A6', 'B6', 'D7']):
    l, r = pan(harp(hz(n_), 2.4, 0.07), -0.7 + k * 0.09); MUS.put(83.5 + k * 0.07, l, r, send=0.6)
for n_ in ('D3', 'A3', 'D4', 'F#4'):
    l, r = pad(hz(n_), 3.0, 0.03, att=0.8, rel=0.8); MUS.put(83.4, l, r, send=0.5)
# C18: ending
for n_, a in (('D2', 0.05), ('D3', 0.04), ('A3', 0.032), ('F#4', 0.026), ('A4', 0.02), ('E5', 0.012)):
    l, r = pad(hz(n_), 10.6, a, att=0.6, rel=3.2); MUS.put(86.0, l, r, send=0.6)
play_motif(86.1, amp=0.10, step=0.42, notes=['D5', 'F#5', 'A5', 'B5', 'A5', 'D6'])
for n_ in ('D6', 'A6'):
    MUS.put(88.6, celesta(hz(n_), 2.0, 0.05), send=0.8)
play_motif(91.4, amp=0.06, step=0.55, notes=['A5', 'B5', 'A5', 'F#5', 'D5'])
for n_ in ('D6', 'A6'):
    MUS.put(94.4, celesta(hz(n_), 2.4, 0.04), send=0.85)

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

duck = 1 - 0.75 * S(37.2, 37.4, T) * (1 - S(38.4, 39.4, T))       # near miss
duck *= 1 - S(48.0, 48.4, T) * (1 - S(63.8, 64.0, T))              # storm .. ash: no music
MUS.l *= duck; MUS.r *= duck; MUS.w *= duck

def out(b, wet=0.85):
    return b.l + fftconvolve(b.w, IRL)[:N] * wet, b.r + fftconvolve(b.w, IRR)[:N] * wet
ml, mr = out(MUS); sl, sr = out(SFX)
L = ml + sl + AMB.l; R = mr + sr + AMB.r
# slow leveller: lift quiet passages, tame the thunder
mono = np.abs(L) + np.abs(R)
k = int(0.35 * SR)
envl = np.sqrt(np.convolve(mono ** 2, np.ones(k) / k, mode='same')) + 1e-6
ref = np.percentile(envl, 90)
g = np.clip((envl / ref) ** -0.35, 0.6, 2.4)
g = np.convolve(g, np.ones(k) / k, mode='same')
L *= g; R *= g
fade = S(0, 1.2, T) * (1 - S(95.6, 97.0, T))
L *= fade; R *= fade
pk = np.percentile(np.abs(np.concatenate([L, R])), 99.97)
L = np.tanh(L / pk * 0.9) * 0.88
R = np.tanh(R / pk * 0.9) * 0.88
wavfile.write('holssi.wav', SR, (np.stack([L, R], -1) * 32767).astype(np.int16))
print('audio ok peak_pre=%.3f' % pk)
