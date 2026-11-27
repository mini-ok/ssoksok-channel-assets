"""허상공방 쇼츠 소리 도구(numpy 합성, 샘플 없음). 편마다 악기 조합을 달리 쓴다.

m = Mix(dur, seed); m.put('mus', t, x); ... m.write(path, rev_mus=2.0, ...)
"""
import os, sys, wave
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'jeom', 'audio'))
from instruments import geomungo, buk          # noqa: E402

SR = 48000

def band(x, lo, hi, slope=2.0):
    X = np.fft.rfft(x); f = np.fft.rfftfreq(len(x), 1 / SR)
    g = 1 / (1 + (lo / np.maximum(f, 1)) ** (2 * slope)) / (1 + (f / hi) ** (2 * slope))
    return np.fft.irfft(X * g, len(x))
def norm(x): return x / (np.abs(x).max() + 1e-9)
def env_ad(n, a, d):
    t = np.arange(n) / SR; return np.minimum(1, t / max(a, 1e-4)) * np.exp(-np.maximum(0, t - a) / d)
def T(dur): return np.arange(int(dur * SR)) / SR
_R = np.random.default_rng(5)

def reverb(x, sec=2.0, mix=0.25, seed=3):
    r = np.random.default_rng(seed); n = int(sec * SR)
    ir = r.standard_normal(n) * np.exp(-np.arange(n) / SR / (sec / 6.9)); ir[0] = 0
    wet = np.fft.irfft(np.fft.rfft(x, len(x) + n) * np.fft.rfft(ir, len(x) + n), len(x) + n)
    wet = wet / (np.abs(wet).max() + 1e-9) * (np.abs(x).max() + 1e-9)
    out = np.zeros(len(x) + n); out[:len(x)] = x * (1 - mix); out += wet * mix
    return out

# ---------------------------------------------------------------- 악기
def pluck(f0, dur=1.0, g=1.0, bright=0.6, seed=None):
    r = _R if seed is None else np.random.default_rng(seed)
    n = int(dur * SR); p = max(2, int(round(SR / f0)))
    buf = r.uniform(-1, 1, p) * np.hanning(p) ** 0.3
    k = 0.5 + 0.49 * bright; out = np.zeros(n)
    # 블록 단위 Karplus-Strong(파이썬 루프를 주기 단위로)
    i = 0
    while i < n:
        m = min(p, n - i); out[i:i + m] = buf[:m]
        buf = (k * buf + (1 - k) * np.roll(buf, -1)) * 0.996; i += p
    return g * norm(out) * np.exp(-np.arange(n) / SR / (dur * 0.35))
def guitar(f0, dur=1.6, g=1.0):
    x = pluck(f0, dur, 1.0, 0.75); h = 0.35 * pluck(f0 * 2.0, dur * 0.7, 1.0, 0.8); x[:len(h)] += h[:len(x)]
    body = band(x, 90, 5000); return g * norm(body + 0.2 * band(x, 180, 260))
def marimba(f, dur=1.2, g=1.0):
    t = T(dur); x = np.sin(2 * np.pi * f * t) * np.exp(-t / 0.35) + 0.4 * np.sin(2 * np.pi * f * 3.93 * t) * np.exp(-t / 0.06) + 0.15 * np.sin(2 * np.pi * f * 9.2 * t) * np.exp(-t / 0.02)
    return g * norm(x) * np.minimum(1, t / 0.002)
def bell(f, dur=3.0, g=1.0):
    t = T(dur); x = sum(a * np.sin(2 * np.pi * f * r * t) * np.exp(-t / (dur * d)) for r, a, d in ((1, 1, 0.35), (2.76, 0.5, 0.18), (5.4, 0.3, 0.1), (0.5, 0.35, 0.45)))
    return g * norm(x) * np.minimum(1, t / 0.002)
def ping(f=1180, g=1.0, dur=1.8):
    t = T(dur); return g * (np.sin(2 * np.pi * f * t) * np.exp(-t / 0.45) + 0.3 * np.sin(2 * np.pi * f * 2.01 * t) * np.exp(-t / 0.22))
def drop(f=900, g=1.0):
    """물방울: 위로 휘는 짧은 사인."""
    t = T(0.18); fr = f * (1 + 1.6 * t / 0.18); ph = 2 * np.pi * np.cumsum(fr) / SR
    return g * np.sin(ph) * np.exp(-t / 0.035) * np.minimum(1, t / 0.001)
def tok(f=620, g=1.0):
    t = T(0.25); return g * (np.sin(2 * np.pi * f * t) * np.exp(-t / 0.035) + 0.5 * np.sin(2 * np.pi * f * 2.7 * t) * np.exp(-t / 0.015))
def click(g=1.0, seed=0):
    r = np.random.default_rng(seed); t = T(0.03); return g * norm(band(r.standard_normal(len(t)), 2500, 12000)) * np.exp(-t / 0.004)
def kick(f0=55, g=1.0, dur=0.5):
    t = T(dur); fr = f0 * (1 + 3 * np.exp(-t / 0.03)); ph = 2 * np.pi * np.cumsum(fr) / SR
    return g * np.sin(ph) * np.exp(-t / (dur * 0.35))
def frame_drum(g=1.0, low=True, seed=0):
    r = np.random.default_rng(seed); t = T(0.6 if low else 0.25)
    if low: x = np.sin(2 * np.pi * 78 * t * (1 + 0.15 * np.exp(-t / 0.05))) * np.exp(-t / 0.18) + 0.3 * band(r.standard_normal(len(t)), 200, 1800) * np.exp(-t / 0.02)
    else: x = band(r.standard_normal(len(t)), 900, 7000) * np.exp(-t / 0.03) + 0.4 * np.sin(2 * np.pi * 330 * t) * np.exp(-t / 0.04)
    return g * norm(x)
def shaker(dur=0.12, g=1.0, seed=0):
    r = np.random.default_rng(seed); t = T(dur); return g * norm(band(r.standard_normal(len(t)), 4000, 12000)) * np.sin(np.pi * t / dur) ** 2
def swoosh(dur, g=1.0, lo=300, hi=5000, seed=0):
    r = np.random.default_rng(seed); t = T(dur); return g * norm(band(r.standard_normal(len(t)), lo, hi)) * np.sin(np.pi * t / dur) ** 1.5
def breath(dur=3.0, g=1.0, seed=0):
    """들숨·날숨: 대역 잡음이 부풀었다 가라앉는다."""
    r = np.random.default_rng(seed); t = T(dur); x = band(r.standard_normal(len(t)), 300, 2500)
    e = np.sin(np.pi * np.clip(t / (dur * 0.45), 0, 1)) ** 2 * (t < dur * 0.45) + 0.8 * np.sin(np.pi * np.clip((t - dur * 0.5) / (dur * 0.5), 0, 1)) ** 2 * (t >= dur * 0.5)
    return g * norm(x) * e
def drone(freqs, dur, g=1.0, kind='saw', vib=0.004, seed=0):
    """지속음: saw는 첼로풍(필터), sine은 패드."""
    t = T(dur); r = np.random.default_rng(seed); out = np.zeros(len(t))
    for f in freqs:
        ph = 2 * np.pi * np.cumsum(f * (1 + vib * np.sin(2 * np.pi * (4.8 + r.uniform(-.4, .4)) * t + r.uniform(0, 6)))) / SR
        if kind == 'saw': out += sum(np.sin(k * ph) / k for k in range(1, 14))
        else: out += np.sin(ph) + 0.3 * np.sin(2 * ph) + 0.12 * np.sin(3 * ph)
    if kind == 'saw': out = band(out, 60, 2200)
    fade = np.minimum(1, t / 1.2) * np.minimum(1, (dur - t) / 1.2)
    return g * norm(out) * fade
def choir(freqs, dur, g=1.0, vowel='a', seed=0):
    """합창 같은 패드: 여러 목소리의 saw를 모음 포먼트로 거른다."""
    t = T(dur); r = np.random.default_rng(seed); src = np.zeros(len(t))
    for f in freqs:
        for v in range(4):
            fv = f * (1 + r.uniform(-0.006, 0.006)); ph = 2 * np.pi * np.cumsum(fv * (1 + 0.005 * np.sin(2 * np.pi * r.uniform(4, 6) * t))) / SR
            src += sum(np.sin(k * ph) / k for k in range(1, 18))
    F = dict(a=(800, 1150, 2900), o=(450, 800, 2830), u=(325, 700, 2530))[vowel]
    out = sum(band(src, f * 0.85, f * 1.15, 3) * w for f, w in zip(F, (1, 0.5, 0.25)))
    fade = np.minimum(1, t / 1.5) * np.minimum(1, (dur - t) / 1.5)
    return g * norm(out) * fade
def square(f, dur, g=1.0, duty=0.5):
    t = T(dur); x = np.where((f * t) % 1 < duty, 1.0, -1.0); x = band(x, 40, 6000)
    return g * x * np.exp(-t / (dur * 0.6)) * np.minimum(1, t / 0.003)
def sonar(f=1400, g=1.0):
    t = T(2.4); return g * np.sin(2 * np.pi * f * t) * np.exp(-t / 0.5) * np.minimum(1, t / 0.01)
def bubbles(dur, rate=8, g=1.0, seed=0):
    r = np.random.default_rng(seed); n = int(dur * SR); out = np.zeros(n)
    for _ in range(int(dur * rate)):
        i = r.integers(0, n - 9000); out[i:i + 8640] += drop(r.uniform(500, 1600), r.uniform(0.2, 1))
    return g * out
def rumble(dur, g=1.0, seed=0):
    r = np.random.default_rng(seed); t = T(dur); return g * norm(band(r.standard_normal(len(t)), 25, 160)) * np.minimum(1, t / 1.5) * np.minimum(1, (dur - t) / 1.5)

# ---------------------------------------------------------------- 악기 2 (옛 6편 다시 만들기용)
def kalimba(f, dur=1.6, g=1.0):
    t = T(dur); x = np.sin(2 * np.pi * f * t) * np.exp(-t / 0.7) + 0.35 * np.sin(2 * np.pi * f * 5.93 * t) * np.exp(-t / 0.08)
    x += 0.15 * np.sin(2 * np.pi * f * 2.0 * t) * np.exp(-t / 0.3)
    return g * norm(x) * np.minimum(1, t / 0.002)
def harpsichord(f, dur=1.4, g=1.0, seed=None):
    a = pluck(f, dur, 1.0, 0.95, seed); b = pluck(f * 2.0, dur * 0.8, 1.0, 0.95, seed)
    a[:len(b)] += 0.5 * b[:len(a)]; return g * norm(band(a, 180, 9000))
def piano(f, dur=2.2, g=1.0):
    t = T(dur); x = np.zeros_like(t)
    for k in range(1, 9):
        fk = f * k * np.sqrt(1 + 0.0004 * k * k)
        if fk > 12000: break
        x += np.sin(2 * np.pi * fk * t + k) * np.exp(-t * (0.9 + 0.55 * k)) / k ** 1.1
    x += 0.15 * band(_R.standard_normal(len(t)), 800, 5000) * np.exp(-t / 0.012)
    return g * norm(x) * np.minimum(1, t / 0.003)
def celesta(f, dur=2.0, g=1.0):
    t = T(dur); x = np.sin(2 * np.pi * f * t) * np.exp(-t / 0.9) + 0.4 * np.sin(2 * np.pi * f * 4.0 * t) * np.exp(-t / 0.25)
    return g * norm(x) * np.minimum(1, t / 0.004)
def pizz(f, dur=0.6, g=1.0, seed=None):
    return g * norm(band(pluck(f, dur, 1.0, 0.35, seed), 60, 3000))
def taiko(g=1.0, f0=62):
    t = T(1.2); fr = f0 * (1 + 0.5 * np.exp(-t / 0.03))
    x = np.sin(2 * np.pi * np.cumsum(fr) / SR) * np.exp(-t / 0.35) + 0.4 * band(_R.standard_normal(len(t)), 80, 900) * np.exp(-t / 0.05)
    return g * norm(x)
def step(g=1.0, seed=0):
    r = np.random.default_rng(seed); t = T(0.25)
    return g * norm(band(r.standard_normal(len(t)), 60, 1400) * np.exp(-t / 0.035) + 0.6 * np.sin(2 * np.pi * 90 * t) * np.exp(-t / 0.05))
def chalk(dur, g=1.0, seed=0):
    r = np.random.default_rng(seed); t = T(dur); n = r.standard_normal(len(t))
    am = 0.55 + 0.45 * np.abs(np.sin(2 * np.pi * (11 + 3 * r.random()) * t)) * (0.7 + 0.3 * r.standard_normal(len(t)).clip(-1, 1))
    return g * norm(band(n, 1800, 7000)) * am * np.minimum(1, t / 0.02) * np.minimum(1, (dur - t) / 0.05)
def rain(dur, g=1.0, seed=0):
    r = np.random.default_rng(seed); t = T(dur); x = 0.5 * band(r.standard_normal(len(t)), 400, 7000)
    for _ in range(int(dur * 25)):
        i = r.integers(0, len(t) - 2000); x[i:i + 1900] += r.uniform(0.1, 0.5) * band(r.standard_normal(1900), 2000, 9000) * np.exp(-np.arange(1900) / 300)
    return g * norm(x) * np.minimum(1, t / 2.0) * np.minimum(1, (dur - t) / 2.0)
def tick(g=1.0, hi=True):
    t = T(0.06); return g * norm(np.sin(2 * np.pi * (3200 if hi else 2400) * t) * np.exp(-t / 0.006) + 0.3 * _R.standard_normal(len(t)) * np.exp(-t / 0.003))
def stream(dur, g=1.0, seed=0):
    r = np.random.default_rng(seed); t = T(dur); x = band(r.standard_normal(len(t)), 300, 3000)
    am = 0.7 + 0.3 * np.sin(2 * np.pi * 0.3 * t) * np.sin(2 * np.pi * 1.7 * t)
    return g * norm(x) * am * np.minimum(1, t / 1.5) * np.minimum(1, (dur - t) / 1.5)

# ---------------------------------------------------------------- 악기 3 (세 번째 10편)
def organ(freqs, dur, g=1.0):
    t = T(dur); x = np.zeros_like(t)
    for f in freqs:
        for k, a in ((1, 1.0), (2, 0.5), (3, 0.3), (4, 0.25), (6, 0.12), (8, 0.1)):
            x += a * np.sin(2 * np.pi * f * k * t + k)
    x *= 1 + 0.03 * np.sin(2 * np.pi * 5.5 * t)
    return g * norm(x) * np.minimum(1, t / 0.08) * np.minimum(1, (dur - t) / 0.3)
def thunder(dur=4.0, g=1.0, seed=0):
    r = np.random.default_rng(seed); t = T(dur); n = r.standard_normal(len(t))
    x = band(n, 25, 300) * np.exp(-t / (dur * 0.35)) * (1 + 0.6 * np.abs(band(r.standard_normal(len(t)), 1, 8)))
    x[:int(0.25 * SR)] += 0.8 * band(r.standard_normal(int(0.25 * SR)), 200, 6000) * np.exp(-np.arange(int(0.25 * SR)) / SR / 0.04)
    return g * norm(x)
def static(dur, g=1.0, seed=0):
    r = np.random.default_rng(seed); t = T(dur); x = band(r.standard_normal(len(t)), 800, 7000)
    am = 0.6 + 0.4 * np.abs(band(r.standard_normal(len(t)), 0.5, 6)) * 3
    return g * norm(x * np.clip(am, 0, 1.5)) * np.minimum(1, t / 0.5) * np.minimum(1, (dur - t) / 0.5)
def beep(f=1200, dur=0.12, g=1.0):
    t = T(dur); return g * norm(np.sin(2 * np.pi * f * t)) * np.minimum(1, t / 0.005) * np.minimum(1, (dur - t) / 0.01)
def woodflute(f, dur, g=1.0, seed=0):
    r = np.random.default_rng(seed); t = T(dur)
    vib = 1 + 0.006 * np.sin(2 * np.pi * 5 * t) * np.minimum(1, t / 0.4)
    ph = 2 * np.pi * np.cumsum(f * vib) / SR
    x = np.sin(ph) + 0.12 * np.sin(2 * ph) + 0.25 * band(r.standard_normal(len(t)), f * 0.8, f * 3) * 0.3
    return g * norm(x) * np.minimum(1, t / 0.08) * np.minimum(1, (dur - t) / 0.15)
def bird(g=1.0, seed=0):
    r = np.random.default_rng(seed); out = []
    for _ in range(r.integers(2, 5)):
        d = r.uniform(0.05, 0.14); t = T(d); f0 = r.uniform(2500, 4500); f1 = f0 * r.uniform(0.7, 1.4)
        f = f0 + (f1 - f0) * t / d; out += [np.sin(2 * np.pi * np.cumsum(f) / SR) * np.sin(np.pi * t / d), np.zeros(int(r.uniform(0.02, 0.06) * SR))]
    return g * norm(np.concatenate(out))
def handpan(f, dur=2.5, g=1.0):
    t = T(dur); x = np.sin(2 * np.pi * f * t) * np.exp(-t / 1.1) + 0.5 * np.sin(2 * np.pi * 2 * f * t) * np.exp(-t / 0.6) + 0.3 * np.sin(2 * np.pi * 3.01 * f * t) * np.exp(-t / 0.4)
    x += 0.2 * band(_R.standard_normal(len(t)), 300, 2000) * np.exp(-t / 0.01)
    return g * norm(x) * np.minimum(1, t / 0.003)
def icecrack(g=1.0, seed=0):
    r = np.random.default_rng(seed); t = T(1.2); x = np.zeros_like(t)
    for _ in range(r.integers(4, 9)):
        i = r.integers(0, int(0.6 * SR)); L = int(r.uniform(0.01, 0.05) * SR)
        x[i:i + L] += r.uniform(0.3, 1) * band(r.standard_normal(L), 1500, 9000) * np.exp(-np.arange(L) / (L / 4))
    f = 3000 * np.exp(-t / 0.3) + 200
    x += 0.4 * np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / 0.25)
    return g * norm(x)
def upright(f, dur=0.8, g=1.0):
    t = T(dur); x = np.sin(2 * np.pi * f * t) + 0.4 * np.sin(4 * np.pi * f * t) * np.exp(-t / 0.2) + 0.2 * np.sin(6 * np.pi * f * t) * np.exp(-t / 0.1)
    return g * norm(x) * np.exp(-t / 0.45) * np.minimum(1, t / 0.006)
def brush(dur=0.25, g=1.0, seed=0):
    r = np.random.default_rng(seed); t = T(dur)
    return g * norm(band(r.standard_normal(len(t)), 2500, 9000)) * np.sin(np.pi * t / dur) ** 2
def koto(f, dur=1.8, g=1.0, seed=None):
    x = pluck(f, dur, 1.0, 0.85, seed); t = T(len(x) / SR)
    bend = 1 + 0.01 * np.exp(-((t - 0.25) / 0.12) ** 2)
    return g * norm(band(x, 120, 7000))
def shakuhachi(f, dur, g=1.0, seed=0):
    r = np.random.default_rng(seed); t = T(dur)
    fr = f * (1 - 0.03 * np.exp(-t / 0.15)) * (1 + 0.008 * np.sin(2 * np.pi * 4.5 * t) * np.minimum(1, t / 0.6))
    ph = 2 * np.pi * np.cumsum(fr) / SR
    x = np.sin(ph) + 0.2 * np.sin(2 * ph) + 0.8 * band(r.standard_normal(len(t)), f, f * 4) * (0.3 + 0.7 * np.exp(-t / 0.2))
    return g * norm(x) * np.minimum(1, t / 0.12) * np.minimum(1, (dur - t) / 0.3)
def typekey(g=1.0, seed=0):
    r = np.random.default_rng(seed); t = T(0.08)
    return g * norm(band(r.standard_normal(len(t)), 900, 6000) * np.exp(-t / 0.008) + 0.5 * np.sin(2 * np.pi * r.uniform(180, 260) * t) * np.exp(-t / 0.015))
def typebell(g=1.0):
    t = T(1.2); return g * norm(np.sin(2 * np.pi * 2350 * t) * np.exp(-t / 0.4) + 0.3 * np.sin(2 * np.pi * 5600 * t) * np.exp(-t / 0.15))
def glassharp(f, dur=3.0, g=1.0):
    t = T(dur); x = np.sin(2 * np.pi * f * t) + 0.25 * np.sin(2 * np.pi * 2.0 * f * t) + 0.08 * np.sin(2 * np.pi * 3.0 * f * t)
    x *= 1 + 0.15 * np.sin(2 * np.pi * 3.2 * t)
    return g * norm(x) * np.minimum(1, t / 0.4) * np.minimum(1, (dur - t) / 0.8)
def theremin(freqs, dur, g=1.0):
    """freqs: [(시각, 주파수)...]를 미끄러지듯 잇는다."""
    t = T(dur); ts = np.array([a for a, _ in freqs]); fs = np.array([b for _, b in freqs])
    f = np.interp(t, ts, fs); sm = int(0.08 * SR); f = np.convolve(f, np.ones(sm) / sm, 'same')
    f *= 1 + 0.012 * np.sin(2 * np.pi * 6 * t)
    ph = 2 * np.pi * np.cumsum(f) / SR
    return g * norm(np.sin(ph) + 0.15 * np.sin(2 * ph)) * np.minimum(1, t / 0.2) * np.minimum(1, (dur - t) / 0.4)

# ---------------------------------------------------------------- 악기 4 (네 번째 10편)
def fm(f, dur, g=1.0, ratio=2.0, index=3.0, decay=1.0):
    t = T(dur); env = np.exp(-t / decay)
    x = np.sin(2 * np.pi * f * t + index * env * np.sin(2 * np.pi * f * ratio * t))
    return g * norm(x) * env * np.minimum(1, t / 0.004)
def modem(dur=1.2, g=1.0, seed=0):
    r = np.random.default_rng(seed); t = T(dur); x = np.zeros_like(t); n = len(t); k = 0
    while k < n:
        L = int(r.uniform(0.03, 0.12) * SR); f = r.choice([1200, 2200, 980, 1650, 2400]); tt = np.arange(min(L, n - k)) / SR
        x[k:k + len(tt)] = np.sin(2 * np.pi * f * tt) * (0.6 if r.random() < 0.7 else 0.0); k += L
    x += 0.3 * band(r.standard_normal(n), 1000, 4000)
    return g * norm(x) * np.minimum(1, t / 0.02) * np.minimum(1, (dur - t) / 0.05)
def dulcimer(f, dur=1.8, g=1.0):
    t = T(dur); x = np.zeros_like(t)
    for d in (0.0, 0.8, -0.6):
        ff = f * (1 + d / 1200)
        x += np.sin(2 * np.pi * ff * t) * np.exp(-t / 0.9) + 0.4 * np.sin(4 * np.pi * ff * t) * np.exp(-t / 0.35) + 0.15 * np.sin(6 * np.pi * ff * t) * np.exp(-t / 0.15)
    x += 0.2 * band(_R.standard_normal(len(t)), 1500, 6000) * np.exp(-t / 0.006)
    return g * norm(x) * np.minimum(1, t / 0.002)
def lute(f, dur=1.6, g=1.0, seed=None):
    return g * norm(band(pluck(f, dur, 1.0, 0.6, seed), 90, 4500))
def gurdy(freqs, dur, g=1.0):
    t = T(dur); x = np.zeros_like(t)
    for f in freqs:
        ph = 2 * np.pi * f * t; x += np.sign(np.sin(ph)) * 0.3 + np.sin(ph)
    x = band(x, 80, 3000) * (1 + 0.15 * np.sin(2 * np.pi * 6.5 * t))
    return g * norm(x) * np.minimum(1, t / 0.4) * np.minimum(1, (dur - t) / 0.5)
def musicbox(f, dur=2.2, g=1.0):
    t = T(dur); x = np.sin(2 * np.pi * f * t) * np.exp(-t / 0.8) + 0.5 * np.sin(2 * np.pi * f * 3.0 * t) * np.exp(-t / 0.25) + 0.25 * np.sin(2 * np.pi * f * 5.4 * t) * np.exp(-t / 0.1)
    x += 0.3 * band(_R.standard_normal(len(t)), 3000, 9000) * np.exp(-t / 0.003)
    return g * norm(x) * np.minimum(1, t / 0.001)
def bowed(f, dur, g=1.0, seed=0):
    r = np.random.default_rng(seed); t = T(dur)
    vib = 1 + 0.005 * np.sin(2 * np.pi * 5.2 * t) * np.minimum(1, t / 0.8)
    ph = 2 * np.pi * np.cumsum(f * vib) / SR
    x = sum(np.sin(k * ph) / k ** 1.3 for k in range(1, 12)) + 0.05 * band(r.standard_normal(len(t)), f, f * 6)
    x = band(x, 60, 5000)
    return g * norm(x) * np.minimum(1, t / 0.35) * np.minimum(1, (dur - t) / 0.4)
def rainstick(dur, g=1.0, seed=0):
    r = np.random.default_rng(seed); t = T(dur); x = np.zeros_like(t)
    for _ in range(int(dur * 400)):
        i = r.integers(0, len(t) - 400); x[i:i + 300] += r.uniform(0.2, 1) * band(r.standard_normal(300), 2500, 9000) * np.exp(-np.arange(300) / 40)
    env = np.sin(np.pi * np.clip(t / dur, 0, 1)) ** 0.7
    return g * norm(x) * env
def ney(f, dur, g=1.0, seed=0):
    r = np.random.default_rng(seed); t = T(dur)
    fr = f * (1 + 0.007 * np.sin(2 * np.pi * 4.8 * t) * np.minimum(1, t / 0.5))
    ph = 2 * np.pi * np.cumsum(fr) / SR
    x = np.sin(ph) + 0.15 * np.sin(2 * ph) + 1.2 * band(r.standard_normal(len(t)), f * 0.9, f * 5)
    return g * norm(x) * np.minimum(1, t / 0.25) * np.minimum(1, (dur - t) / 0.35)
def metaldrone(dur, g=1.0, seed=0):
    r = np.random.default_rng(seed); t = T(dur); x = np.zeros_like(t)
    for f in (73.0, 146.5, 219.8, 311.0, 467.0, 701.0):
        x += np.sin(2 * np.pi * f * t + r.uniform(0, 6)) * (1 + 0.3 * np.sin(2 * np.pi * r.uniform(0.05, 0.3) * t)) / (1 + f / 200)
    return g * norm(x) * np.minimum(1, t / 1.0) * np.minimum(1, (dur - t) / 1.0)
def drill(dur, g=1.0, seed=0):
    r = np.random.default_rng(seed); t = T(dur)
    x = band(r.standard_normal(len(t)), 120, 1800) * (0.6 + 0.4 * np.sin(2 * np.pi * 23 * t)) + 0.4 * np.sin(2 * np.pi * 55 * t)
    return g * norm(x) * np.minimum(1, t / 0.2) * np.minimum(1, (dur - t) / 0.3)
def hihat(g=1.0, seed=0, open_=False):
    r = np.random.default_rng(seed); d = 0.25 if open_ else 0.05; t = T(d)
    return g * norm(band(r.standard_normal(len(t)), 7000, 15000)) * np.exp(-t / (d / 3))
def steeldrum(f, dur=1.4, g=1.0):
    t = T(dur); x = np.sin(2 * np.pi * f * t) * np.exp(-t / 0.7) + 0.6 * np.sin(2 * np.pi * 2.0 * f * t) * np.exp(-t / 0.4) + 0.35 * np.sin(2 * np.pi * 3.0 * f * t) * np.exp(-t / 0.2) + 0.2 * np.sin(2 * np.pi * 4.95 * f * t) * np.exp(-t / 0.1)
    return g * norm(x) * np.minimum(1, t / 0.003)

# ---------------------------------------------------------------- 믹스
class Mix:
    def __init__(self, dur, seed=0):
        self.n = int(dur * SR); self.dur = dur
        self.b = dict(mus=np.zeros(self.n), fx=np.zeros(self.n), amb=np.zeros(self.n))
    def put(self, k, t, x, g=1.0):
        i = int(round(t * SR)); j = min(self.n, i + len(x))
        if 0 <= i < self.n and j > i: self.b[k][i:j] += g * x[:j - i]
    def write(self, path, rev_mus=2.0, rev_fx=1.2, wet_mus=0.26, wet_fx=0.18, amb_g=1.0, mus_g=0.85):
        n = self.n
        music = reverb(self.b['mus'], rev_mus, wet_mus)[:n]; fxr = reverb(self.b['fx'], rev_fx, wet_fx)[:n]
        mix = amb_g * self.b['amb'] + fxr + mus_g * music
        f = int(0.05 * SR); mix[:f] *= np.linspace(0, 1, f); e = int(1.2 * SR); mix[-e:] *= np.linspace(1, 0, e) ** 2
        mix = mix / (np.abs(mix).max() + 1e-9); mix = np.tanh(mix * 2.2) / np.tanh(2.2) * 0.85
        st = np.stack([mix, np.roll(mix, int(0.0004 * SR))], 1)
        with wave.open(path, 'wb') as wf:
            wf.setnchannels(2); wf.setsampwidth(2); wf.setframerate(SR); wf.writeframes((st * 32767).astype(np.int16).tobytes())
        return path
