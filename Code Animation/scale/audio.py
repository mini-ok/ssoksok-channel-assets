"""규모 체감 쇼츠 소리(numpy 합성). python3 audio.py <에피소드> out.wav — 사건 시각은 엔진 events·카드 시각을 읽는다."""
import os, sys, wave
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, '..', 'jeom', 'audio'))
os.environ['MG_SCALE'] = '0.25'
from run import get as _get
EPN = sys.argv[1]; ep, eng = _get(EPN)
class N: DUR = ep['DUR']
from instruments import geomungo, buk      # noqa: E402
from sketch import reverb                  # noqa: E402

SR = 48000
DUR = N.DUR
OUT = sys.argv[2]
NS = int(DUR * SR)
rng = np.random.default_rng(ep['seed'])
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
PENTA = [0, 2, 4, 7, 9]
def deg(i, base=146.83): return base * 2 ** ((12 * (i // 5) + PENTA[i % 5]) / 12)
T_END = ep['t_end']
amb += 0.012 * norm(band(rng.standard_normal(NS), 120, 900)) * (0.7 + 0.3 * np.sin(2 * np.pi * 0.11 * t))
amb += 0.035 * (np.sin(2 * np.pi * 55 * t) * 0.5 + np.sin(2 * np.pi * 82.4 * t) * 0.3) * np.clip(t / 2, 0, 1) * (t < T_END)
put(mus, 0.0, geomungo(73.4, 3.0, 0.45, seed=1)); put(fx, 0.25, tok(700, 0.4))
pops = sorted([e for e in eng.events if e[1] == 'pop']); moves = sorted([e for e in eng.events if e[1] == 'move'])
for k, (te, _, i) in enumerate(moves):
    if 0.5 < te < T_END: put(fx, te, swoosh(0.9, 0.14, 300, 4500))
for k, (te, _, i) in enumerate(pops):
    if te < 0.3 or te > T_END: continue
    put(fx, te, tok(560 + 40 * k, 0.4)); put(fx, te, snap(0.35, 10 + k, lo=900))
    put(mus, te, pluck(deg(k + 2), 1.4, 0.34, bright=0.55))
    if k % 2 == 1: put(fx, te, buk(0.35, 62, 1.1, seed=20 + k))
last = max([te for te, _, _ in pops if te < T_END] + [1.0])
put(fx, last, buk(0.7, 48, 1.8, 0.45, seed=40)); put(fx, last, ping(990, 0.06, 1.6))
for c in ep['cards']:
    if c[0] > 0.5: put(fx, c[0], rustle(0.35, 0.10, seed=int(c[0] * 10)))
for w in ep.get('wipes', []): put(fx, w - 0.3, swoosh(0.62, 0.4, 250, 6500)); put(fx, w, buk(0.5, 55, 1.2, seed=60))
TC = ep['t_coda']
n_ = int(SR * (T_END - TC)); tt_ = np.arange(n_) / SR
pad = sum(np.sin(2 * np.pi * f * tt_) * g for f, g in ((110.0, 0.5), (164.8, 0.35), (220.0, 0.25), (277.2, 0.12)))
put(mus, TC, 0.06 * pad * np.clip(tt_ / 1.5, 0, 1) * np.clip((T_END - TC - tt_) / 1.0, 0, 1))
for i in range(len(ep['coda'])):
    lt = TC + 0.7 + i * 1.9
    put(mus, lt, pluck([440.0, 493.9, 587.3][i % 3], 2.6, 0.24, bright=0.4)); put(fx, lt, ping([880, 988, 1175][i % 3], 0.03, 2.0))
put(fx, TC, swoosh(1.2, 0.10, 150, 2000))
put(fx, T_END - 0.3, swoosh(0.62, 0.42, 250, 6500))
for j, f in enumerate([293.7, 440.0, 587.3]): put(mus, T_END + 0.15 + 0.07 * j, pluck(f, 2.4, 0.3))
put(fx, T_END + 0.6, tok(300, 0.5)); put(fx, T_END + 0.6, snap(0.3, 41, lo=400))
put(mus, T_END + 0.9, geomungo(73.4, 2.0, 0.4, seed=42))

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
