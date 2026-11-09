# -*- coding: utf-8 -*-
"""〈숨비〉 soundtrack, fully synthesized and locked to the cut list: ambience beds per place, foley, 숨비소리 (breath whistles),
voices (temp TTS), the motif (ocarina + celesta + pad), big in C30, resolving under the title and credit.
writes sumbi_mix.wav (44.1 kHz stereo)."""
import numpy as np, math, json
from scipy.signal import butter, sosfilt, fftconvolve, resample_poly
from scipy.io import wavfile

CUTS = [('1', 7), ('2', 5), ('3', 4), ('4', 3), ('5', 5), ('6', 5), ('7', 3), ('8', 3), ('9', 5), ('10', 4), ('11', 4), ('12', 3), ('13', 2.8),
        ('14', 2), ('15', 6), ('16', 2), ('17', 4), ('18', 5), ('19', 4), ('20', 4), ('21', 3), ('22', 4), ('23', 4), ('24', 4), ('25', 6),
        ('26', 2), ('27', 5), ('28', 7), ('29', 8), ('30', 22), ('31', 5), ('32', 4), ('33', 6), ('34', 4), ('35', 7)]
ST = {}; acc = 0.0
for c, d in CUTS: ST[c] = acc; acc += d
DUR = acc
json.dump({'starts': ST, 'dur': DUR}, open('cuts.json', 'w'))
SR = 44100; N = int(DUR * SR); T = np.arange(N) / SR
rng = np.random.default_rng(29)
def S(a, b, t): x = np.clip((np.asarray(t, float) - a) / (b - a), 0, 1); return x * x * (3 - 2 * x)
def win(a, b, fade=0.25): return S(a - fade, a + fade, T) * (1 - S(b - fade, b + fade, T))
def bp(x, lo, hi, o=2): return sosfilt(butter(o, [lo, hi], btype='band', fs=SR, output='sos'), x)
def lp(x, fc, o=2): return sosfilt(butter(o, fc, btype='low', fs=SR, output='sos'), x)
def hp(x, fc, o=2): return sosfilt(butter(o, fc, btype='high', fs=SR, output='sos'), x)
def tg(d): return np.arange(int(d * SR)) / SR
def env(tt, d, a, r): x = np.clip(tt / max(a, 1e-3), 0, 1); y = np.clip((d - tt) / max(r, 1e-3), 0, 1); return (x * x * (3 - 2 * x)) * (y * y * (3 - 2 * y))
def pan(s, p): th = (p + 1) * math.pi / 4; return s * math.cos(th), s * math.sin(th)
def noise(d): return rng.normal(0, 1, int(d * SR))
NOTE = {'C': 0, 'C#': 1, 'D': 2, 'Eb': 3, 'E': 4, 'F': 5, 'F#': 6, 'G': 7, 'Ab': 8, 'A': 9, 'Bb': 10, 'B': 11}
def hz(s): return 440.0 * 2 ** ((12 * (int(s[-1]) + 1) + NOTE[s[:-1]] - 69) / 12)
class Bus:
    def __init__(s): s.l = np.zeros(N); s.r = np.zeros(N); s.w = np.zeros(N)
    def put(s, t0, l, r=None, send=0.0, gain=1.0):
        if r is None: r = l
        i = int(round(t0 * SR))
        if i >= N or i + len(l) <= 0: return
        a = max(0, -i); n = min(len(l) - a, N - max(i, 0)); i = max(i, 0)
        s.l[i:i + n] += l[a:a + n] * gain; s.r[i:i + n] += r[a:a + n] * gain
        if send > 0: s.w[i:i + n] += 0.5 * (l[a:a + n] + r[a:a + n]) * gain * send
MUS, SFX, AMB, VOX = Bus(), Bus(), Bus(), Bus()
def at(c, dt=0.0): return ST[c] + dt

# ------------------------------------------------------------------ instruments
def ocarina(f, d, amp, vib=0.006):
    tt = tg(d); e = env(tt, d, 0.07, min(0.3, d * 0.4)); vd = np.clip((tt - 0.25) / 0.4, 0, 1)
    ph = np.cumsum(f * (1 + vib * vd * np.sin(2 * np.pi * 5.2 * tt))) / SR
    s = np.sin(2 * np.pi * ph) + 0.12 * np.sin(4 * np.pi * ph) + 0.04 * np.sin(6 * np.pi * ph)
    br = bp(rng.normal(0, 1, len(tt)), f * 0.8, min(f * 1.5, SR * 0.45)) * 0.06 * (0.4 + 0.6 * np.exp(-tt / 0.12))
    return (s + br) * e * amp
def celesta(f, d, amp):
    tt = tg(d); s = np.zeros_like(tt)
    for ratio, a, k in ((1, 1.0, 2.2), (2.0, 0.35, 3.5), (3.0, 0.12, 5.0), (4.07, 0.08, 7.0)): s += a * np.sin(2 * np.pi * f * ratio * tt) * np.exp(-tt * k)
    return s * np.clip(tt / 0.002, 0, 1) * amp
def pad(f, d, amp, harm=6, att=1.2, rel=1.6, bright=1.6):
    tt = tg(d); e = env(tt, d, att, rel); ph = np.cumsum(1 + 0.002 * np.sin(2 * np.pi * 5 * tt)) / SR
    l = np.zeros_like(tt); r = np.zeros_like(tt)
    for h in range(1, harm + 1): g = 1.0 / h ** bright; l += g * np.sin(2 * np.pi * f * h * 1.0018 * ph + h); r += g * np.sin(2 * np.pi * f * h * 0.9982 * ph + 2 * h)
    return l * e * amp, r * e * amp
def harp(f, d, amp):
    tt = tg(d); s = np.zeros_like(tt)
    for h in range(1, 9):
        if f * h > 12000: break
        s += (1.0 / h ** 1.4) * np.sin(2 * np.pi * f * h * tt + h) * np.exp(-tt * (1.2 + 0.7 * h))
    return s * np.clip(tt / 0.003, 0, 1) * amp
def pizz(f, amp, d=0.5):
    tt = tg(d); s = np.zeros_like(tt)
    for h in range(1, 7): s += (1.0 / h ** 1.2) * np.sin(2 * np.pi * f * h * tt + h) * np.exp(-tt * (9 + 4 * h))
    return s * np.clip(tt / 0.002, 0, 1) * amp
def boom(d, amp, f0=110, f1=30, tau=0.25):
    tt = tg(d); f = f1 + (f0 - f1) * np.exp(-tt / tau)
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-tt / (d * 0.35)) * np.clip(tt / 0.003, 0, 1) * amp

# ------------------------------------------------------------------ voices of the sea
def sumbi(d=1.3, f0=2300, f1=1500, amp=1.0, breath=0.5, wob=0.0):
    """숨비소리: a long breath pushed through pursed lips — a whistle tone gliding down over hissing air"""
    tt = tg(d); u = tt / d
    f = f0 + (f1 - f0) * u ** 0.8 + 40 * np.sin(2 * np.pi * 6 * tt) * wob + 60 * np.exp(-tt / 0.08)
    ph = np.cumsum(f) / SR
    tone = np.sin(2 * np.pi * ph) + 0.18 * np.sin(4 * np.pi * ph)
    e = np.clip(tt / 0.06, 0, 1) * np.clip((d - tt) / 0.35, 0, 1) ** 1.5 * (1 - 0.25 * u)
    air = bp(rng.normal(0, 1, len(tt)), 900, 6000) * (0.6 + 0.4 * np.exp(-tt / 0.2))
    return (tone * e * (1 - breath * 0.4) + air * e * breath * 0.55) * amp
def failed_pu(d=0.7, amp=1.0):
    tt = tg(d); return bp(rng.normal(0, 1, len(tt)), 400, 3000) * env(tt, d, 0.04, 0.4) * amp
def whistle(t0, notes, amp, p=0.0, send=0.3):
    t = t0
    for f, d in notes:
        tt = tg(d); ff = f * (1 + 0.02 * np.sin(2 * np.pi * 6 * tt)) * (1 + 0.04 * np.exp(-tt / 0.05))
        s = np.sin(2 * np.pi * np.cumsum(ff) / SR) * env(tt, d, 0.03, 0.08) + bp(rng.normal(0, 1, len(tt)), f * 0.8, f * 1.3) * 0.05 * env(tt, d, 0.03, 0.08)
        l, r = pan(s, p); SFX.put(t, l, r, send=send, gain=amp); t += d + 0.04
def pyu(t0, amp, p=0.0):
    """꾸럭이's answer: a wet rising 'pyu-' and droplets"""
    d = 0.45; tt = tg(d); f = 700 + 1900 * (tt / d) ** 0.6
    s = np.sin(2 * np.pi * np.cumsum(f) / SR) * env(tt, d, 0.02, 0.12) * (1 + 0.4 * np.sin(2 * np.pi * 34 * tt))
    l, r = pan(s, p); SFX.put(t0, l, r, send=0.35, gain=amp)
    for k in range(5): plink(t0 + 0.35 + k * rng.uniform(0.04, 0.09), amp * 0.5, p + rng.uniform(-0.3, 0.3))
def plink(t0, amp, p, f=None):
    d = 0.18; tt = tg(d); f = f or rng.uniform(1600, 3000)
    s = np.sin(2 * np.pi * f * (1 + 0.3 * np.exp(-tt / 0.01)) * tt) * np.exp(-tt / 0.03)
    l, r = pan(s, p); SFX.put(t0, l, r, send=0.5, gain=amp)
def drip(t0, amp, p=0.0): plink(t0, amp, p, f=rng.uniform(1100, 1500))
def bubble(t0, amp, p=0.0, f=None):
    d = 0.06; tt = tg(d); f = f or rng.uniform(500, 1400)
    s = np.sin(2 * np.pi * np.cumsum(f * (1 + 2.5 * tt / d)) / SR) * env(tt, d, 0.004, 0.03)
    l, r = pan(s, p); SFX.put(t0, l, r, send=0.4, gain=amp)
def bubbles(t0, d, rate, amp, p=0.0):
    t = t0
    while t < t0 + d: bubble(t, amp * rng.uniform(0.5, 1), p + rng.uniform(-0.3, 0.3)); t += rng.exponential(1 / rate)
def splash(t0, amp, big=1.0):
    d = 0.9 * big; tt = tg(d); s = bp(rng.normal(0, 1, len(tt)), 300, 7000) * np.exp(-tt / (0.18 * big)) * np.clip(tt / 0.01, 0, 1)
    SFX.put(t0, s, s * 0.95, send=0.3, gain=amp); SFX.put(t0, boom(0.4, 0.6, 140, 50, 0.05), send=0.1, gain=amp * 0.6)
    for k in range(8): plink(t0 + 0.1 + k * 0.06, amp * 0.25, rng.uniform(-0.6, 0.6))
def steps(t0, d, rate, amp, p=0.0, wet=False):
    t = t0
    while t < t0 + d:
        dd = 0.06; tt = tg(dd); s = bp(rng.normal(0, 1, len(tt)), 200 if not wet else 400, 1800 if not wet else 5000) * np.exp(-tt / 0.02)
        l, r = pan(s, p); SFX.put(t, l, r, gain=amp * rng.uniform(0.7, 1)); t += 1 / rate
def crow_caw(t0, amp, p=0.0, n=2):
    for k in range(n):
        d = 0.32; tt = tg(d); f = 620 - 120 * tt / d
        s = bp(np.sign(np.sin(2 * np.pi * np.cumsum(f) / SR)) + 0.3 * rng.normal(0, 1, len(tt)), 400, 3500) * env(tt, d, 0.02, 0.12)
        l, r = pan(s, p); SFX.put(t0 + k * 0.42, l, r, send=0.6, gain=amp)
def flaps(t0, d, amp, p=0.0):
    n = int(d * SR); tt = np.arange(n) / SR; am = np.clip(np.sin(2 * np.pi * 7 * tt), 0, 1) ** 4
    s = bp(rng.normal(0, 1, n), 200, 2200) * am * env(tt, d, 0.03, 0.1); l, r = pan(s, p); SFX.put(t0, l, r, send=0.2, gain=amp)
def puuk(t0, amp):
    d = 0.6; tt = tg(d); f = 220 * np.exp(-tt / 0.12) + 70
    s = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-tt / 0.15) + bp(rng.normal(0, 1, len(tt)), 150, 1200) * np.exp(-tt / 0.08) * 0.8
    SFX.put(t0, s, send=0.25, gain=amp)
def pop(t0, amp):
    d = 0.08; tt = tg(d); s = np.sin(2 * np.pi * np.cumsum(900 + 1800 * tt / d) / SR) * np.exp(-tt / 0.015); SFX.put(t0, s, send=0.2, gain=amp)
def crackle(t0, d, rate, amp):
    t = t0
    while t < t0 + d:
        m = int(rng.uniform(0.002, 0.01) * SR); s = hp(rng.normal(0, 1, m), 1500) * np.exp(-np.arange(m) / (m / 4))
        l, r = pan(s, rng.uniform(-0.3, 0.3)); SFX.put(t, l, r, gain=amp * rng.uniform(0.3, 1)); t += rng.exponential(1 / rate)
def chirp(t0, amp, p, f0=4200, notes=3):
    for k in range(notes):
        d = rng.uniform(0.05, 0.10); tt = tg(d); f = f0 * rng.uniform(0.9, 1.15) + 1100 * np.sin(np.pi * tt / d) * rng.choice([-1, 1])
        s = np.sin(2 * np.pi * np.cumsum(f) / SR) * env(tt, d, 0.008, 0.03); l, r = pan(s, p); SFX.put(t0 + k * rng.uniform(0.08, 0.13), l, r, send=0.35, gain=amp)
def thunder(t0, amp):
    d = 2.2; tt = tg(d); s = lp(rng.normal(0, 1, len(tt)), 300) * (np.exp(-tt / 0.6) + 0.5 * np.exp(-np.maximum(0, tt - 0.25) / 0.4) * (tt > 0.25))
    s += hp(rng.normal(0, 1, len(tt)), 1500) * np.exp(-tt / 0.03) * 0.6; SFX.put(t0, s, s, send=0.4, gain=amp)
def wav(path, sr_out=SR):
    sr, a = wavfile.read(path); a = a.astype(np.float64) / 32768
    if a.ndim > 1: a = a.mean(1)
    return resample_poly(a, sr_out, sr) if sr != sr_out else a

# ------------------------------------------------------------------ ambience beds
def bed(lo, hi, amp, shape, mod=None):
    l = bp(rng.normal(0, 1, N), lo, hi); r = bp(rng.normal(0, 1, N), lo, hi); m = shape * (mod if mod is not None else 1.0)
    AMB.l += l * amp * m; AMB.r += r * amp * m
coast_dawn = win(0, at('9'), 0.2)
forest = win(at('9'), at('25'), 0.15)
coast_day = win(at('25'), at('26'), 0.1) + win(at('27'), at('30'), 0.1) * 1.0 + win(at('31'), at('34'), 0.1)
storm = win(at('26'), at('27'), 0.05)
under = win(at('30'), at('31'), 0.08)
title = win(at('34'), DUR, 0.3)
waves = 0.55 + 0.45 * np.clip(np.sin(2 * np.pi * T / 7.3) * np.sin(2 * np.pi * T / 4.1 + 1), 0, 1) ** 0.7
bed(120, 900, 0.16, coast_dawn * 1.15 + coast_day + title * 0.5, waves)              # surf
bed(1500, 7000, 0.035, coast_dawn + coast_day + title * 0.4, waves ** 2)              # spray hiss
bed(200, 700, 0.05, coast_dawn, 0.7 + 0.3 * np.sin(2 * np.pi * 0.07 * T))             # wind
bed(150, 600, 0.04, forest)                                                            # forest air
bed(2500, 8000, 0.006, forest)
bed(800, 9000, 0.12, storm); bed(100, 500, 0.16, storm)                               # rain + roar
bed(60, 380, 0.08, under, 0.8 + 0.2 * np.sin(2 * np.pi * 0.2 * T))                    # underwater hum
bed(20, 120, 0.06, under)
# far surf heard from the forest when the drops point the way (C19) and as the forest ends (C24->C25)
bed(120, 800, 0.08, win(at('19', 1.5), at('20'), 0.6) + win(at('24', 2.5), at('25', 1.5), 0.6) * 1.4, waves)

# ------------------------------------------------------------------ foley + sea voices, cut by cut
crackle(0, at('5'), 18, 0.08)                                       # 불턱 fire C1–C4
for k in range(3): chirp(at('1', 4.5 + k), 0.03, -0.6 + k * 0.4, f0=2400, notes=2)           # gulls far
lv = [wav(f'/home/claude/tts/laugh{i}.wav') for i in (1, 2, 3)]
for k, (dt, sh, p) in enumerate([(1.6, 0.92, -0.4), (1.9, 1.08, 0.3), (2.6, 0.85, 0.0), (3.0, 1.15, -0.2)]):
    x = resample_poly(lv[k % 3], 100, int(100 * sh)); x = lp(x, 5000); l, r = pan(x, p); VOX.put(at('2', dt), l, r, send=0.5, gain=0.13)
steps(at('5', 0.2), 4.5, 3.2, 0.04, 0.3, wet=True)
SFX.put(at('6', 0.6), *pan(lp(sumbi(1.5, 2200, 1500, 1, 0.5), 3500), 0.5), send=0.9, gain=0.10)        # first 숨비소리 (far)
SFX.put(at('6', 2.75), *pan(failed_pu(0.8), 0), send=0.1, gain=0.12)                                   # 솔이: "푸―"
drip(at('7', 0.9), 0.08); drip(at('7', 2.4), 0.07)
SFX.put(at('8', 0.3), *pan(lp(sumbi(1.6, 2100, 1400, 1, 0.5), 2600), -0.6), send=0.9, gain=0.06)     # second, receding
steps(at('8', 0.1), 2.9, 5.0, 0.07, 0.0)
for k in range(12): chirp(at('9') + rng.uniform(0, 15.5) + k * 1.2, 0.035, rng.uniform(-0.8, 0.8), f0=rng.uniform(3200, 5200), notes=rng.integers(2, 5))
for k in range(10): drip(at('9') + rng.uniform(0, 30), 0.03, rng.uniform(-0.7, 0.7))
steps(at('9', 0.0), 5.0, 2.2, 0.035, -0.3)
pop(at('11', 2.05), 0.12)                                                                              # "뽁"
SFX.put(at('12', 0.1), bp(noise(1.1), 300, 4000) * env(tg(1.1), 1.1, 0.1, 0.3), send=0.2, gain=0.06)   # pour
SFX.put(at('12', 1.5), bp(noise(0.9), 400, 3500) * env(tg(0.9), 0.9, 0.05, 0.3), send=0.2, gain=0.05)  # scoop
steps(at('15', 0.0), 2.9, 5.2, 0.07, 0.2); steps(at('15', 4.1), 1.9, 5.2, 0.07, 0.2)
SFX.put(at('15', 2.95), bp(noise(0.5), 600, 5000) * env(tg(0.5), 0.5, 0.02, 0.2), send=0.1, gain=0.08)  # snag + tug
for k, dt in enumerate([0.85, 1.75]): drip(at('16', dt), 0.12, 0)
whistle(at('18', 0.5), [(hz('E6'), 0.25), (hz('A6'), 0.35)], 0.06); pyu(at('18', 1.55), 0.07)
whistle(at('18', 2.7), [(hz('E6'), 0.22), (hz('B6'), 0.32)], 0.06); pyu(at('18', 3.55), 0.07)
for k in range(9): plink(at('19', 0.3 + k * 0.17), 0.05, -0.2 + k * 0.08, f=2600 + k * 120)           # glitter
drip(at('20', 0.6), 0.08); steps(at('20', 1.5), 2.5, 5.2, 0.06, 0.3)
crow_caw(at('21', 0.6), 0.09, 0.4, 2)
flaps(at('22', 0.5), 1.4, 0.12, 0.3); puuk(at('22', 2.78), 0.25)
for k, f in enumerate(['G4', 'E4', 'C4']): MUS.put(at('23', 1.15 + k * 0.32), pizz(hz(f), 0.25), send=0.2)     # comedy pizzicato
flaps(at('23', 2.2), 1.6, 0.09, -0.5); crow_caw(at('23', 3.0), 0.04, -0.7, 1)
for k in range(3): plink(at('24', 0.7 + k * 0.12), 0.06, 0, f=1800 + 300 * k)
steps(at('25', 0.0), 1.0, 5, 0.06)
SFX.put(at('25', 1.6), bp(noise(3.5), 100, 900) * env(tg(3.5), 3.5, 1.2, 1.5), send=0.3, gain=0.12)     # the sea surges
thunder(at('26', 0.5), 0.5)
drip(at('27', 2.6), 0.05)
whistle(at('28', 0.8), [(hz('E6'), 0.25), (hz('A6'), 0.4)], 0.06, send=0.6)
whistle(at('28', 3.3), [(hz('E6'), 0.25), (hz('A6'), 0.45)], 0.05, send=0.7)
steps(at('29', 2.6), 4.0, 2.0, 0.05, 0, wet=True)
SFX.put(at('29', 6.6), bp(noise(0.5), 300, 2500) * env(tg(0.5), 0.5, 0.15, 0.2), gain=0.08)            # breath in
splash(at('29', 7.3), 0.12)
# C30 under the sea
bubbles(at('30', 0.0), 4.0, 6, 0.05); bubbles(at('30', 8.0), 1.6, 14, 0.06); bubbles(at('30', 19.3), 0.7, 18, 0.07)
for k in range(7): bubbles(at('30', 11 + k * 1.6), 0.4, 20, 0.04, -0.3)
for k in range(30): plink(at('30') + rng.uniform(3.5, 22), 0.02, rng.uniform(-0.9, 0.9), f=rng.uniform(2200, 4200))       # octopus signals
# C31–C33 at the surface
splash(at('31', 0.3), 0.18, 1.3)
SFX.put(at('31', 0.5), bp(noise(0.6), 300, 3000) * env(tg(0.6), 0.6, 0.02, 0.3), gain=0.1)              # gasp
SFX.put(at('32', 0.3), sumbi(1.2, 2400, 1600, 1, 0.45), send=0.5, gain=0.13)                            # 엄마's 숨비소리
SFX.put(at('32', 1.9), sumbi(1.1, 2700, 1900, 1, 0.55, wob=0.6), send=0.5, gain=0.12)                   # 솔이: "호오―이." first
for k, (dt, p, f0) in enumerate([(1.0, -0.7, 2250), (1.7, 0.6, 2350), (2.4, -0.2, 2150)]):               # haenyeo answer
    SFX.put(at('33', dt), *pan(lp(sumbi(1.4, f0, f0 - 700, 1, 0.5), 3800), p), send=0.9, gain=0.07)
cr = wav('/home/claude/sumbi/design/credit.wav'); cr2 = cr[:min(len(cr), N - int(at('35') * SR))]       # typing ticks
SFX.put(at('35'), cr2, cr2, gain=0.5)

# ------------------------------------------------------------------ voices (temp TTS; Gemini later)
for name, c, dt, p in [('mom1', '3', 1.0, 0.15), ('sol1', '13', 0.3, 0.0), ('sol2', '30', 19.3, 0.0), ('mom2', '31', 2.3, 0.1)]:
    x = wav(f'{name}.wav'); l, r = pan(x, p); VOX.put(at(c, dt), l, r, send=0.12 if c != '30' else 0.5, gain=0.5)

# ------------------------------------------------------------------ music: the motif
MOT = [('E5', 0.5), ('G5', 0.5), ('A5', 1.0), ('G5', 0.5), ('E5', 0.5), ('D5', 1.5)]          # "숨비" motif (pentatonic)
MOT2 = [('E5', 0.5), ('G5', 0.5), ('A5', 0.75), ('C6', 0.75), ('B5', 0.5), ('A5', 1.5)]
def melody(t0, notes, inst, amp, oct=1.0, send=0.4):
    t = t0
    for n, d in notes:
        if n: MUS.put(t, inst(hz(n) * oct, d * 1.05, amp), send=send)
        t += d
def chord(t0, d, names, amp, att=1.2, rel=1.6):
    for n in names: l, r = pad(hz(n), d, amp, att=att, rel=rel); MUS.put(t0, l, r, send=0.5)
# dawn: sparse celesta motif over the crane down
melody(at('1', 2.0), MOT, celesta, 0.05)
chord(at('1', 0.5), 6.5, ['A3', 'E4'], 0.02)
# the rock: a lonely ocarina phrase after the failed breath
melody(at('6', 3.9), [('E5', 0.6), ('D5', 1.2)], ocarina, 0.05)
# forest: harp arpeggio while she finds the octopus, the motif on ocarina when she names him
for k, n in enumerate(['A3', 'E4', 'A4', 'C5', 'E5', 'C5', 'A4', 'E4'] * 2): MUS.put(at('10', 0.2 + k * 0.42), harp(hz(n), 1.6, 0.045), send=0.4)
melody(at('13', 0.4), MOT[:3], ocarina, 0.05)
chord(at('13'), 4.5, ['A3', 'E4', 'C5'], 0.018)
# running music C15–C20: light harp ostinato
for k in range(int(9 / 0.25)):
    n = ['A4', 'C5', 'E5', 'A5'][k % 4]; MUS.put(at('15') + k * 0.25, harp(hz(n), 0.5, 0.03), send=0.3)
for k in range(int(4 / 0.25)):
    n = ['A4', 'C5', 'E5', 'G5'][k % 4]; MUS.put(at('20', 1.5) + k * 0.25, harp(hz(n), 0.5, 0.03), send=0.3)
melody(at('24', 2.2), [('E5', 0.3), ('G5', 0.3), ('A5', 0.8)], celesta, 0.06)                    # her first laugh
# the lowest point: one low pad, silence around the whistles
chord(at('27', 0.5), 4.5, ['A2', 'E3'], 0.02, att=2.0, rel=2.0)
chord(at('29', 2.0), 6.0, ['A3', 'C4', 'E4'], 0.018, att=2.5, rel=1.5)
melody(at('29', 3.0), [('E5', 1.0), ('D5', 1.0), ('C5', 2.0)], ocarina, 0.045)
# C30: the harmony — the motif opens up, full pad, celesta answers, a big resolution on '엄마…'
chord(at('30', 0.0), 9.5, ['A2', 'E3', 'A3', 'C4', 'E4'], 0.02, att=3.0, rel=2.0)
chord(at('30', 9.5), 6.5, ['F2', 'C3', 'A3', 'C4', 'F4'], 0.022, att=1.5, rel=2.0)
chord(at('30', 16.0), 6.5, ['C3', 'G3', 'C4', 'E4', 'G4'], 0.024, att=1.5, rel=2.5)
melody(at('30', 4.2), MOT, ocarina, 0.06)
melody(at('30', 10.8), MOT2, ocarina, 0.065)
for k, n in enumerate(['A5', 'C6', 'E6', 'G6', 'E6', 'C6'] * 3): MUS.put(at('30', 11.0 + k * 0.5), celesta(hz(n), 1.4, 0.03), send=0.5)
melody(at('30', 16.4), MOT, ocarina, 0.06, oct=1.0)
for k, n in enumerate(['C5', 'E5', 'G5', 'C6', 'E6']): MUS.put(at('30', 19.4 + k * 0.12), harp(hz(n), 2.5, 0.05), send=0.6)
# surface + ending: the motif resolves; title and credit under it
chord(at('31', 2.0), 3.5, ['C3', 'G3', 'E4'], 0.015)
chord(at('33', 0.0), 6.5, ['C3', 'G3', 'C4', 'E4'], 0.02, att=1.5, rel=1.0)
melody(at('33', 2.6), MOT2, ocarina, 0.06)
chord(at('34', 0.0), 4.2, ['F2', 'C3', 'A3', 'C4'], 0.02, att=0.5, rel=1.5)
melody(at('34', 0.6), [('A5', 0.6), ('G5', 0.6), ('E5', 0.6), ('G5', 1.4)], celesta, 0.06)
chord(at('35', 0.0), 6.5, ['C3', 'G3', 'C4', 'E4', 'G4'], 0.02, att=0.6, rel=3.5)
melody(at('35', 0.3), [('E5', 0.5), ('G5', 0.5), ('A5', 1.0), ('G5', 0.5), ('E5', 0.5), ('C5', 2.5)], ocarina, 0.05)

# ------------------------------------------------------------------ mix
def rev_ir(d=2.4, seed=3):
    r = np.random.default_rng(seed); n = int(d * SR); tt = np.arange(n) / SR
    return lp(r.normal(0, 1, n), 7000) * np.exp(-tt / (d / 6.5)) * 0.06, lp(r.normal(0, 1, n), 7000) * np.exp(-tt / (d / 6.5)) * 0.06
IRL, IRR = rev_ir()
def mixdown(b, wet=1.0): return b.l + fftconvolve(b.w, IRL)[:N] * wet, b.r + fftconvolve(b.w, IRR)[:N] * wet
L = np.zeros(N); R = np.zeros(N)
uw = under                                                                                         # underwater: everything muffled
for b, g in ((AMB, 1.0), (SFX, 1.0), (MUS, 1.0), (VOX, 1.0)):
    l, r = mixdown(b)
    if b is not MUS and b is not VOX:
        l = l * (1 - uw) + lp(l, 700) * uw * 1.4; r = r * (1 - uw) + lp(r, 700) * uw * 1.4
    L += l * g; R += r * g
fade = np.clip((DUR - T) / 1.2, 0, 1) * np.clip(T / 0.8, 0, 1)
L *= fade; R *= fade
# loudness: bring the body up (~-20 dBFS rms), soft-limit the peaks (thunder, splashes)
rms = np.sqrt(np.mean(((L + R) / 2) ** 2)); g = 0.085 / rms
L, R = np.tanh(L * g * 1.1) / 1.1, np.tanh(R * g * 1.1) / 1.1
pk = max(np.abs(L).max(), np.abs(R).max()); L, R = L / max(pk, 0.95) * 0.95, R / max(pk, 0.95) * 0.95
wavfile.write('sumbi_mix.wav', SR, (np.stack([L, R], -1) * 32767).astype(np.int16))
print('ok', round(DUR, 2), 's')
