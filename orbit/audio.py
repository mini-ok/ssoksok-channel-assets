#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ORBIT soundtrack -- 100% synthesized with numpy. Timeline is locked to render.py."""
import numpy as np, math
from scipy.signal import butter, sosfilt, fftconvolve
from scipy.io import wavfile

SR = 44100
DUR = 60.0
N = int(DUR * SR)
BAR = 2.25                       # 106.67 bpm; bar 16 starts exactly at the 36.0 s impact
BEAT = BAR / 4
rng = np.random.default_rng(404)

def S(a, b, t):
    x = np.clip((np.asarray(t, float) - a) / (b - a), 0, 1)
    return x * x * (3 - 2 * x)

def mf(m): return 440.0 * 2 ** ((m - 69) / 12.0)

class Bus:
    def __init__(s): s.l = np.zeros(N); s.r = np.zeros(N); s.w = np.zeros(N)
    def put(s, t0, l, r=None, send=0.0, gain=1.0):
        if r is None: r = l
        i = int(round(t0 * SR))
        if i >= N or i + len(l) <= 0: return
        a = max(0, -i); n = min(len(l) - a, N - max(i, 0)); i = max(i, 0)
        s.l[i:i + n] += l[a:a + n] * gain; s.r[i:i + n] += r[a:a + n] * gain
        if send > 0: s.w[i:i + n] += 0.5 * (l[a:a + n] + r[a:a + n]) * gain * send

MUS = Bus(); FX = Bus()

def tgrid(dur): return np.arange(int(dur * SR)) / SR

def smooth_env(tt, dur, att, rel):
    a = np.clip(tt / max(att, 1e-3), 0, 1); r = np.clip((dur - tt) / max(rel, 1e-3), 0, 1)
    return (a * a * (3 - 2 * a)) * (r * r * (3 - 2 * r))

def pan_lr(sig, pan):
    th = (pan + 1) * math.pi / 4
    return sig * math.cos(th), sig * math.sin(th)

def pad(f, dur, amp, harm=7, att=1.3, rel=1.8):
    tt = tgrid(dur); env = smooth_env(tt, dur, att, rel)
    l = np.zeros_like(tt); r = np.zeros_like(tt)
    for h in range(1, harm + 1):
        g = 1.0 / h ** 1.5
        l += g * np.sin(2 * np.pi * f * h * 1.0013 * tt + h)
        r += g * np.sin(2 * np.pi * f * h * 0.9987 * tt + 2 * h)
    sh = 0.85 + 0.15 * np.sin(2 * np.pi * 0.13 * tt + f)
    return l * env * amp * sh, r * env * amp * sh

def pluck(f, dur, amp, decay=2.4, harm=9):
    tt = tgrid(dur); sig = np.zeros_like(tt)
    for h in range(1, harm + 1):
        if f * h > 9000: break
        sig += (1.0 / h ** 1.15) * np.sin(2 * np.pi * f * h * tt) * np.exp(-tt * (decay + 0.9 * h))
    sig *= np.clip(tt / 0.004, 0, 1)
    return sig * amp

def bell(f, dur, amp):
    tt = tgrid(dur); sig = np.zeros_like(tt)
    for ratio, a, d in ((1, 1.0, 1.1), (2.0, 0.45, 1.5), (2.76, 0.5, 2.0), (5.4, 0.2, 3.2), (8.9, 0.1, 4.5)):
        if f * ratio > 15000: continue
        sig += a * np.sin(2 * np.pi * f * ratio * tt + ratio) * np.exp(-tt * d * (2.8 / max(dur, 0.5)) ** 0.5 * 1.1)
    sig *= np.clip(tt / 0.003, 0, 1)
    return sig * amp

def sine_glide(f0, f1, dur, amp, att=0.05, rel=0.2, expo=True):
    tt = tgrid(dur); u = tt / dur
    f = f0 * (f1 / f0) ** u if expo else f0 + (f1 - f0) * u
    ph = 2 * np.pi * np.cumsum(f) / SR
    return np.sin(ph) * smooth_env(tt, dur, att, rel) * amp

def boom(dur, amp):
    tt = tgrid(dur); f = 30 + 95 * np.exp(-tt / 0.22)
    ph = 2 * np.pi * np.cumsum(f) / SR
    return np.sin(ph) * np.exp(-tt / 1.0) * np.clip(tt / 0.002, 0, 1) * amp

def kick(amp, dur=0.28):
    tt = tgrid(dur); f = 44 + 70 * np.exp(-tt / 0.045)
    ph = 2 * np.pi * np.cumsum(f) / SR
    return np.sin(ph) * np.exp(-tt / 0.11) * np.clip(tt / 0.002, 0, 1) * amp

def noise_sweep(dur, f0, f1, env_fn, amp, bw=(0.6, 1.6)):
    n = int(dur * SR); x = rng.normal(0, 1, n); out = np.zeros(n)
    ch = 2048; hop = 1024; win = np.hanning(ch)
    for i in range(0, n - ch, hop):
        u = (i + ch / 2) / n
        fc = f0 * (f1 / f0) ** u
        lo = max(fc * bw[0], 25); hi = min(fc * bw[1], SR * 0.45)
        sos = butter(2, [lo, hi], btype='band', fs=SR, output='sos')
        out[i:i + ch] += sosfilt(sos, x[i:i + ch]) * win
    tt = np.arange(n) / SR
    return out * env_fn(tt) * amp * 0.8

def lp_noise(dur, fc, amp, env_fn):
    n = int(dur * SR); x = rng.normal(0, 1, n)
    sos = butter(2, fc, btype='low', fs=SR, output='sos')
    return sosfilt(sos, x) * env_fn(np.arange(n) / SR) * amp

def hat(amp):
    n = int(0.05 * SR); x = rng.normal(0, 1, n)
    sos = butter(2, 6000, btype='high', fs=SR, output='sos')
    return sosfilt(sos, x) * np.exp(-np.arange(n) / SR / 0.012) * amp

def blip(f, amp):
    n = int(0.035 * SR); tt = np.arange(n) / SR
    return np.sin(2 * np.pi * f * tt) * np.exp(-tt / 0.008) * amp

# chord voicings (midi)
CH = {
    'Am': dict(bass=45, pad=[45, 52, 57, 60, 64], arp=[57, 60, 64, 69, 72]),
    'F':  dict(bass=41, pad=[41, 48, 53, 57, 60], arp=[53, 57, 60, 65, 69]),
    'C':  dict(bass=48, pad=[48, 55, 60, 64, 67], arp=[55, 60, 64, 67, 72]),
    'G':  dict(bass=43, pad=[43, 50, 55, 59, 62], arp=[55, 59, 62, 67, 71]),
}

# ------------------------------------------------------------------ 0-11  solitude
for m, a, st in ((33, 0.07, 0.3), (45, 0.06, 0.4), (57, 0.03, 1.5)):
    l, r = pad(mf(m), 12.0, a, harm=4 if m < 40 else 6, att=3.0, rel=2.5); MUS.put(st, l, r, send=0.3)
MUS.put(0.0, lp_noise(11.5, 900, 0.020, lambda t: S(0, 3, t) * (1 - S(9, 11.5, t))), send=0.3)
FX.put(0.85, sine_glide(330, 990, 1.8, 0.035, att=0.5, rel=0.9), send=0.6)
FX.put(1.15, bell(mf(81), 4.5, 0.075), send=0.8)
for t0, m, a in ((4.2, 88, 0.03), (6.6, 81, 0.03), (8.4, 83, 0.025)):
    MUS.put(t0, bell(mf(m), 3.5, a), send=0.9)

# ------------------------------------------------------------------ 10  second light
FX.put(9.78, sine_glide(800, 3200, 0.36, 0.035, att=0.1, rel=0.1), send=0.5)
FX.put(10.0, bell(mf(76), 5.0, 0.10), send=0.8)
FX.put(10.0, bell(mf(88), 4.0, 0.045), send=0.9)
FX.put(10.0, boom(1.0, 0.05))
l, r = pad(mf(52), 11.0, 0.05, att=1.2, rel=2.2); MUS.put(9.8, l, r, send=0.35)
l, r = pad(mf(60), 9.0, 0.032, att=1.5, rel=2.0); MUS.put(10.6, l, r, send=0.35)

# ------------------------------------------------------------------ 11.25-20.25  approach (bars 5-8)
prog2 = ['Am', 'F', 'C', 'G']
for b, c in enumerate(prog2):
    t0 = 11.25 + b * BAR
    for m in CH[c]['pad'][:4]:
        l, r = pad(mf(m), BAR + 1.0, 0.040, harm=6, att=0.9, rel=1.2); MUS.put(t0 - 0.2, l, r, send=0.4)
for t0, m, a in ((12.0, 76, 0.05), (13.4, 81, 0.05), (15.1, 84, 0.05), (16.5, 79, 0.05), (18.0, 76, 0.05), (19.2, 81, 0.05)):
    MUS.put(t0, bell(mf(m), 3.0, a), send=0.8)
MUS.put(18.0, noise_sweep(2.6, 600, 3000, lambda t: S(0, 2.3, t) * (1 - S(2.3, 2.6, t)), 0.04), send=0.3)

# ------------------------------------------------------------------ 20.25-36.0  orbit (bars 9-15)
prog3 = ['Am', 'F', 'C', 'G', 'Am', 'F', 'G']
for b, c in enumerate(prog3):
    t0 = 20.25 + b * BAR
    amp = 0.050 + 0.030 * b / 6
    for m in CH[c]['pad']:
        l, r = pad(mf(m), BAR + 0.9, amp * (0.7 if m < 50 else 0.5), harm=6, att=0.5, rel=0.9); MUS.put(t0 - 0.1, l, r, send=0.35)
    # bass
    MUS.put(t0, pluck(mf(CH[c]['bass']), 1.5, 0.22 + 0.08 * b / 6, decay=1.8, harm=5))
    MUS.put(t0 + BAR / 2, pluck(mf(CH[c]['bass']), 1.2, 0.17 + 0.06 * b / 6, decay=2.0, harm=5))
    # arpeggio: 8th notes (bars 0-1), 16ths (bars 2+)
    arp = CH[c]['arp']
    if b < 2: step = BAR / 8; pat = [0, 1, 2, 3, 2, 1, 2, 4]
    else: step = BAR / 16; pat = [0, 1, 2, 3, 4, 3, 2, 1, 0, 2, 3, 4, 3, 2, 1, 2]
    lift = 12 if b >= 4 else 0
    for k, p in enumerate(pat):
        tn = t0 + k * step
        a = (0.085 + 0.045 * b / 6) * (1.0 if k % 4 == 0 else 0.7)
        l, r = pan_lr(pluck(mf(arp[p] + lift), 1.4, a, decay=3.2), math.sin(k * 0.9) * 0.5)
        MUS.put(tn, l, r, send=0.45)
    if b >= 2:
        for k in range(4):
            MUS.put(t0 + k * BEAT, kick(0.18 + 0.25 * (b - 2) / 4))
    if b >= 4:
        for k in range(16):
            if k % 2 == 1: MUS.put(t0 + k * BAR / 16, hat(0.03))
# riser into the impact
MUS.put(31.2, noise_sweep(4.7, 300, 8000, lambda t: S(0, 4.4, t) ** 2, 0.17), send=0.25)
MUS.put(31.5, sine_glide(220, 1760, 4.4, 0.06, att=1.0, rel=0.1), send=0.3)
MUS.put(34.2, sine_glide(440, 3520, 1.7, 0.035, att=0.3, rel=0.05), send=0.3)

# ------------------------------------------------------------------ 36.0  impact, then silence
FX.put(36.0, boom(3.0, 0.60))
FX.put(36.0, lp_noise(2.2, 500, 0.42, lambda t: np.exp(-t / 0.55)))
FX.put(36.0, noise_sweep(1.0, 4500, 2500, lambda t: np.exp(-t / 0.22), 0.20, bw=(0.4, 2.0)), send=0.5)
for m, a in ((57, 0.05), (64, 0.045), (69, 0.04)):
    FX.put(36.02, bell(mf(m), 5.0, a), send=0.9)
tt = tgrid(4.2)
FX.put(36.5, np.sin(2 * np.pi * 3100 * tt) * 0.010 * np.exp(-tt / 1.6) * smooth_env(tt, 4.2, 0.5, 1.5))
# particle sparkles in the silence
n_sp = 230
for tb in np.sort(36.15 + 2.9 * rng.random(n_sp) ** 1.5):
    l, r = pan_lr(blip(rng.uniform(2200, 6500), rng.uniform(0.006, 0.020)), rng.uniform(-0.9, 0.9))
    FX.put(tb, l, r, send=0.5)

# ------------------------------------------------------------------ 41-54  return, the afterglow
for m, a, st, d in ((33, 0.05, 41.0, 15.0), (45, 0.05, 41.5, 14.5), (52, 0.035, 43.0, 13.0)):
    l, r = pad(mf(m), d, a, harm=5, att=3.5, rel=2.5); MUS.put(st, l, r, send=0.4)
for t0, m, a in ((41.6, 57, 0.11), (43.5, 64, 0.10), (44.6, 60, 0.09)):
    MUS.put(t0, pluck(mf(m), 3.5, a, decay=1.1, harm=6), send=0.7)
prog5 = ['Am', 'F', 'C', 'G', 'Am']
for b, c in enumerate(prog5):
    t0 = 45.0 + b * BAR
    for m in CH[c]['pad'][:4]:
        l, r = pad(mf(m), BAR + 1.0, 0.045, harm=5, att=0.9, rel=1.2); MUS.put(t0 - 0.2, l, r, send=0.45)
    arp = CH[c]['arp']
    for k, p in enumerate([0, 1, 2, 3, 2, 1, 2, 3]):
        MUS.put(t0 + k * BAR / 8, pluck(mf(arp[p] + 12 * (b >= 2)), 2.0, 0.060 + 0.012 * (b >= 2), decay=1.6, harm=6), send=0.6)
# constellation chimes (synced with star activations in render.py)
C_T = np.zeros(24); order = [0, 12, 1, 13, 2, 14, 3, 15, 4, 16, 5, 17, 6, 18, 7, 19, 8, 20, 9, 21, 10, 22, 11, 23]
for k, idx in enumerate(order): C_T[idx] = 46.0 + 0.32 * k
pent = [81, 84, 86, 88, 91, 93]
for k, idx in enumerate(order):
    m = pent[(k * 2 + int(rng.integers(0, 3))) % len(pent)]
    l, r = pan_lr(bell(mf(m), 3.0, 0.040), rng.uniform(-0.7, 0.7))
    MUS.put(C_T[idx], l, r, send=0.9)

# ------------------------------------------------------------------ 54-55.5  gathering
MUS.put(54.2, noise_sweep(1.25, 1500, 9000, lambda t: S(0, 1.1, t) ** 2 * (1 - S(1.15, 1.25, t)), 0.08), send=0.3)
for m in (45, 52, 64):
    l, r = pad(mf(m), 1.6, 0.05, harm=5, att=1.2, rel=0.15); MUS.put(54.0, l, r, send=0.4)

# ------------------------------------------------------------------ 55.5  the new star (never ducked)
for m, a in ((33, 0.10), (45, 0.11), (52, 0.09), (57, 0.08), (61, 0.07), (64, 0.065), (71, 0.045), (73, 0.04)):
    l, r = pad(mf(m), 5.3, a, harm=6, att=0.35, rel=1.7); FX.put(55.45, l, r, send=0.5)
FX.put(55.5, boom(3.5, 0.28))
for i, m in enumerate((81, 85, 88, 93, 97)):
    l, r = pan_lr(bell(mf(m), 4.5, 0.075 - 0.008 * i), -0.5 + 0.25 * i)
    FX.put(55.5 + 0.075 * i, l, r, send=0.9)
for i in range(14):
    fq = rng.uniform(2400, 7000)
    tt = tgrid(4.0)
    l, r = pan_lr(np.sin(2 * np.pi * fq * tt) * 0.006 * smooth_env(tt, 4.0, 0.3, 2.5) * (0.6 + 0.4 * np.sin(2 * np.pi * rng.uniform(3, 7) * tt)), rng.uniform(-1, 1))
    FX.put(55.6 + 0.05 * i, l, r, send=0.6)
# pull-out whoosh
FX.put(55.85, noise_sweep(3.4, 7500, 260, lambda t: np.sin(np.pi * np.clip(t / 3.3, 0, 1)) ** 1.4, 0.17, bw=(0.55, 1.7)), send=0.35)
FX.put(56.0, sine_glide(1400, 180, 3.0, 0.03, att=0.6, rel=1.5), send=0.4)
for k in range(3):
    FX.put(57.4 + k * 1.15, bell(mf(93), 3.5, 0.05 * (1 - 0.25 * k)), send=0.95)

# ------------------------------------------------------------------ reverb, ducking, master
def make_ir():
    n = int(3.2 * SR); tt = np.arange(n) / SR
    irs = []
    for _ in range(2):
        x = rng.normal(0, 1, n) * np.exp(-tt / 0.55)
        x = sosfilt(butter(2, 5500, btype='low', fs=SR, output='sos'), x)
        x[:int(0.02 * SR)] *= np.linspace(0, 1, int(0.02 * SR))
        irs.append(np.concatenate([np.zeros(int(0.025 * SR)), x])[:n])
    g = 1.0 / math.sqrt(np.sum(irs[0] ** 2))
    return irs[0] * g, irs[1] * g
IRL, IRR = make_ir()

tt = np.arange(N) / SR
duck = np.ones(N)
duck *= 1 - S(35.88, 36.02, tt) * (1 - S(40.8, 41.6, tt))
for bus, d in ((MUS, duck), (FX, np.ones(N))):
    bus.l *= d; bus.r *= d; bus.w *= d

def render_bus(bus):
    wl = fftconvolve(bus.w, IRL)[:N]; wr = fftconvolve(bus.w, IRR)[:N]
    return bus.l + wl * 0.85, bus.r + wr * 0.85
ml, mr = render_bus(MUS); fl, fr = render_bus(FX)
L = ml + fl; R = mr + fr
# gentle master
fade = S(0, 0.8, tt) * (1 - S(59.0, 60.0, tt))
L *= fade; R *= fade
pk = max(np.abs(L).max(), np.abs(R).max())
L = np.tanh(L / pk * 1.35) / np.tanh(1.35) * 0.89
R = np.tanh(R / pk * 1.35) / np.tanh(1.35) * 0.89
wavfile.write('orbit.wav', SR, (np.stack([L, R], -1) * 32767).astype(np.int16))
print('audio ok, peak(before norm)=%.3f  rms=%.4f' % (pk, float(np.sqrt(np.mean(L ** 2)))))
