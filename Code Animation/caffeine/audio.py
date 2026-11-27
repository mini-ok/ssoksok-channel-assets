"""〈오후 3시의 커피〉 소리(48 kHz, numpy 합성). 사건 시각은 short.py 시간표를 그대로 읽는다. python3 audio.py out.wav"""
import os, sys, wave
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, '..', 'jeom', 'audio'))
os.environ['MG_SCALE']='0.25'
import short as N
from instruments import geomungo, buk      # noqa: E402
from sketch import reverb                  # noqa: E402

SR = 48000
DUR = N.DUR
OUT = sys.argv[1] if len(sys.argv) > 1 else '/home/claude/work/caf/audio_raw.wav'
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
hh = np.interp(t, np.arange(0, DUR, 0.01), [N.hours(x) for x in np.arange(0, DUR, 0.01)])
ng = np.interp(t, np.arange(0, DUR, 0.01), [N.night(N.hours(x)) if x < N.T_S4 else (1.0 if x < N.T_END else 0.0) for x in np.arange(0, DUR, 0.01)])
# 바탕: 낮의 방 소리 → 밤의 낮은 울림
room = band(rng.standard_normal(NS), 150, 1500); amb += 0.010 * norm(room) * (1 - ng)
amb += 0.045 * (np.sin(2*np.pi*55*t)*0.5 + np.sin(2*np.pi*82.4*t)*0.3 + np.sin(2*np.pi*110.3*t)*0.15) * ng * (0.8 + 0.2*np.sin(2*np.pi*0.2*t))
def slam(tt, f=146.8, g=0.34): put(fx, tt, tok(520, 0.32)); put(mus, tt, pluck(f, 1.3, g, bright=0.45))
# 첫 장면: 차오르는 소리 → 쿵
n = int(0.75 * SR); tt = np.arange(n) / SR
pour = norm(band(rng.standard_normal(n), 300, 3500)) * (tt / 0.75) ** 2 * 0.35 + 0.18 * np.sin(2*np.pi*(180 + 520 * (tt/0.75)**2) * tt) * (tt/0.75)
put(fx, N.T_FILL[0], pour)
put(fx, 0.9, buk(0.7, 50, 1.8, 0.45, seed=1)); put(mus, 0.9, geomungo(73.4, 2.6, 0.5, seed=2))
slam(0.55, 196.0, 0.3); slam(N.T_S2 + 0.1, 146.8); slam(8.0, 164.8); slam(10.4, 130.8); slam(13.0, 146.8)
# 시계가 돈다: 30분마다 똑딱, 도착하면 북 + 높은 울림
for a, b, h0, h1 in N.SWEEPS:
    for k in range(1, int((h1 - h0) * 2)):
        hk = h0 + k * 0.5
        i = int(np.searchsorted(hh, hk)); put(fx, i / SR, tok(1500 if k % 2 else 1150, 0.16 if k % 2 else 0.24))
    put(fx, a, swoosh(b - a, 0.16, 400, 5000))
    j = [5, 10, 15].index(h1)
    put(fx, b, buk(0.55, [58, 52, 46][j], 1.6, 0.45, seed=10 + j)); put(fx, b, ping([880, 660, 495][j], 0.07, 1.6))
    put(mus, b, pluck([220.0, 164.8, 123.5][j], 1.8, 0.4, bright=0.5)); put(mus, b + 0.02, pluck([440.0, 329.6, 246.9][j], 1.4, 0.2))
# 근거 장면
put(fx, N.T_S4 - 0.3, swoosh(0.62, 0.42, 250, 6500)); slam(N.T_S4 + 0.15, 110.0)
put(fx, N.T_LINE, swoosh(0.6, 0.14, 800, 6000)); put(mus, N.T_LINE + 0.45, pluck(293.7, 1.0, 0.24))
put(fx, N.T_BAR, swoosh(0.7, 0.16, 200, 2500)); put(mus, N.T_BAR + 0.1, pluck(196.0, 1.4, 0.28))
put(fx, N.T_CUT, snap(0.85, 31, lo=600)); put(fx, N.T_CUT + 0.05, buk(0.85, 42, 2.2, 0.5, seed=21)); put(mus, N.T_CUT + 0.08, geomungo(65.4, 2.8, 0.6, bend_end=-1.0, seed=22))
put(fx, N.T_CUT + 0.1, swoosh(0.8, 0.12, 150, 1500))
slam(N.T_NOTICE, 123.5, 0.3); put(mus, N.T_NOTICE + 0.25, pluck(116.5, 1.6, 0.2))
# 결론 장면
put(fx, N.T_S5 - 0.3, swoosh(0.62, 0.42, 250, 6500)); slam(N.T_S5 + 0.2, 146.8)
n = int((N.T_ARC[1] - N.T_ARC[0]) * SR); tt = np.arange(n) / SR; u = tt / tt[-1]
put(fx, N.T_ARC[0], 0.10 * np.sin(2*np.pi*np.cumsum(220 + 440 * u**2) / SR) * np.sin(np.pi * u) ** 0.7)
put(fx, N.T_ARC[0], tok(1150, 0.3)); put(fx, N.T_ARC[0] + 0.3, buk(0.4, 60, 1.0, seed=30))
put(fx, N.T_ARC[1], buk(0.7, 48, 1.8, 0.45, seed=31)); put(fx, N.T_ARC[1], ping(990, 0.07, 1.8))
for j, f in enumerate([146.8, 220.0, 293.7, 440.0]): put(mus, N.T_ARC[1] + 0.03 * j, pluck(f, 2.2, 0.3))
# 끝 화면
put(fx, N.T_END - 0.3, swoosh(0.62, 0.42, 250, 6500))
for j, f in enumerate([293.7, 440.0, 587.3]): put(mus, N.T_END + 0.15 + 0.07 * j, pluck(f, 2.4, 0.3))
put(fx, N.T_END + 0.7, tok(300, 0.5)); put(fx, N.T_END + 0.7, snap(0.3, 41, lo=400))
put(mus, N.T_END + 1.0, geomungo(73.4, 2.0, 0.4, seed=42))

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
