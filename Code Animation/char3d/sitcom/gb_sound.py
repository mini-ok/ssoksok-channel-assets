# 시트콤 파일럿 소리: 대사(TTS) + 합성 효과음 + 배경음악(채널 bgm) → 48kHz 스테레오 wav
# 사용: python3 gb_sound.py <tl.json> <대사 audio 폴더> <bgm 폴더> <out.wav>
import sys, json, wave, subprocess, numpy as np
from scipy.signal import butter, lfilter
tl, AUD, BGM, OUT = sys.argv[1:5]
TL = json.load(open(tl)); SR = 48000; rng = np.random.default_rng(7)
T0 = {}; t = 0.0
for c in TL: T0[c['id']] = t; t += c['dur']
TOTAL = t + 0.6; mix = np.zeros((int(TOTAL * SR), 2), np.float32)
tt = lambda d: np.arange(int(d * SR)) / SR
def lp(x, f): b, a = butter(2, f / (SR / 2)); return lfilter(b, a, x)
def hp(x, f): b, a = butter(2, f / (SR / 2), 'high'); return lfilter(b, a, x)
def bp(x, f0, f1): b, a = butter(2, [f0 / (SR / 2), f1 / (SR / 2)], 'band'); return lfilter(b, a, x)
def env(d, a=0.005, r=0.05): x = tt(d); return np.clip(x / a, 0, 1) * np.clip((d - x) / r, 0, 1)
def put(x, at, g=1.0, pan=0.0):
    i = int(at * SR); x = np.asarray(x, np.float32) * g; n = min(len(x), len(mix) - i)
    if n <= 0 or i < 0: return
    mix[i:i + n, 0] += x[:n] * (1 - max(0, pan)); mix[i:i + n, 1] += x[:n] * (1 + min(0, pan))
def S(*xs):
    n = max(len(x) for x in xs); o = np.zeros(n, np.float32)
    for x in xs: o[:len(x)] += x
    return o
def noise(d): return rng.normal(0, 1, int(d * SR))
def tone(f, d, vel=0.2, dec=6): x = tt(d); return np.sin(2 * np.pi * f * x) * np.exp(-x * dec) * np.clip(x / 0.004, 0, 1) * vel
def glide(f0, f1, d, vel=0.2): x = tt(d); f = f0 * (f1 / f0) ** (x / d); return np.sin(2 * np.pi * np.cumsum(f) / SR) * env(d, 0.01, 0.05) * vel

SFX = {
  'alarm': lambda: np.concatenate([np.sign(np.sin(2 * np.pi * (880 if k % 2 == 0 else 660) * tt(0.32))) * env(0.32, 0.01, 0.03) for k in range(6)]) * 0.05,
  'sigh': lambda: np.zeros(10),
  'marker': lambda: bp(noise(0.55), 2500, 6000) * (0.5 + 0.5 * np.sin(2 * np.pi * 9 * tt(0.55))) * env(0.55, 0.02, 0.08) * 0.05,
  'pat': lambda: lp(np.sin(2 * np.pi * 120 * tt(0.15)) * np.exp(-tt(0.15) * 30), 600) * 0.35,
  'skid': lambda: bp(noise(0.35), 1500, 4500) * env(0.35, 0.01, 0.15) * 0.08,
  'tap': lambda: S(tone(2400, 0.12, 0.12, 40), tone(3600, 0.1, 0.05, 50)),
  'clank': lambda: hp(sum(np.sin(2 * np.pi * 380 * k * tt(0.45) + k) * np.exp(-tt(0.45) * (8 + 6 * k)) for k in (1, 2.76, 5.4)), 200) * 0.18,
  'lever': lambda: S(lp(noise(0.12) * np.exp(-tt(0.12) * 35), 900) * 0.4, tone(160, 0.2, 0.25, 18)),
  'fart': lambda: lp(np.sign(np.sin(2 * np.pi * np.cumsum(95 + 25 * np.sin(2 * np.pi * 13 * tt(0.7)) - 30 * tt(0.7)) / SR)) * env(0.7, 0.02, 0.2), 700) * 0.22,
  'tick': lambda: tone(1800, 0.06, 0.15, 60),
  'thump': lambda: lp(np.sin(2 * np.pi * np.cumsum(70 - 30 * tt(0.3)) / SR) * np.exp(-tt(0.3) * 14), 300) * 0.6,
  'beep': lambda: np.sin(2 * np.pi * 1320 * tt(0.14)) * env(0.14, 0.005, 0.02) * 0.08,
  'rewind': lambda: bp(np.sign(np.sin(2 * np.pi * np.cumsum(900 + 700 * np.sin(2 * np.pi * 7 * tt(1.0))) / SR)), 600, 4000) * env(1.0, 0.05, 0.2) * 0.05,
  'squish': lambda: lp(np.sin(2 * np.pi * np.cumsum(260 - 180 * tt(0.5)) / SR) * env(0.5, 0.03, 0.2), 900) * 0.25,
  'roll': lambda: bp(noise(1.3), 300, 1500) * (0.6 + 0.4 * np.abs(np.sin(2 * np.pi * 11 * tt(1.3)))) * env(1.3, 0.1, 0.2) * 0.12,
  'clack': lambda: S(hp(noise(0.05) * np.exp(-tt(0.05) * 90), 1200) * 0.5, tone(900, 0.15, 0.2, 30)),
  'hiss': lambda: hp(noise(2.2), 3000) * env(2.2, 0.3, 0.6) * 0.025,
  'whoosh': lambda: bp(noise(0.35), 400, 3000) * np.sin(np.pi * tt(0.35) / 0.35) ** 2 * 0.15,
  'thunk': lambda: lp(np.sin(2 * np.pi * 140 * tt(0.25)) * np.exp(-tt(0.25) * 20), 800) * 0.5,
  'ding': lambda: S(tone(1568, 1.2, 0.12, 3), tone(2093, 1.0, 0.06, 4)),
  'card': lambda: bp(noise(0.25), 1500, 6000) * np.sin(np.pi * tt(0.25) / 0.25) * 0.08,
  'siren': lambda: np.concatenate([np.sin(2 * np.pi * np.cumsum(np.full(int(0.4 * SR), f)) / SR) * env(0.4, 0.02, 0.04) for f in (960, 770, 960, 770, 960, 770)]) * 0.05,
  'stamp': lambda: lp(noise(0.12) * np.exp(-tt(0.12) * 30), 600) * 0.6,
  'flop': lambda: lp(np.sin(2 * np.pi * np.cumsum(180 - 120 * tt(0.4)) / SR) * env(0.4, 0.01, 0.2), 700) * 0.3,
  'relief': lambda: S(*[tone(f, 1.6, 0.06, 2) for f in (392, 494, 587)]),
  'chime': lambda: S(tone(1318, 0.9, 0.08, 4), tone(1760, 0.7, 0.05, 5)),
  'glove': lambda: bp(noise(0.08), 800, 3000) * np.exp(-tt(0.08) * 40) * 0.3,
  'sparkle': lambda: S(*[np.pad(tone(f, 0.4, 0.05, 10), (int(k * 0.06 * SR), 0)) for k, f in enumerate((1568, 2093, 2637, 3136))]),
  'step': lambda: lp(noise(0.05) * np.exp(-tt(0.05) * 60), 1000) * 0.15,
  'scrub': lambda: bp(noise(1.6), 1800, 5000) * (0.5 + 0.5 * np.sin(2 * np.pi * 6 * tt(1.6))) * env(1.6, 0.1, 0.3) * 0.05,
}
def sfx(name):
    if name == 'title': return sum(tone(f, 1.6, 0.07, 2.2) for f in (523, 659, 784, 1046))
    return SFX[name]()

# 대사
for c in TL:
    for lid, at in c['lines']:
        w = wave.open(f'{AUD}/{lid}.wav'); x = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32) / 32768
        x = np.interp(np.arange(int(len(x) * SR / w.getframerate())) * w.getframerate() / SR, np.arange(len(x)), x)
        put(x, T0[c['id']] + at, 0.95)
    for name, at in c['sfx']:
        g0 = T0[c['id']] + at
        if name == 'run':   # 달리는 발소리 여러 번
            for k in range(9): put(lp(noise(0.05) * np.exp(-tt(0.05) * 60), 1200) * 0.22, g0 + k * 0.11, 1, 0.2 * (-1) ** k)
            continue
        put(sfx(name), g0, 1.0)
voice_end = mix.copy()

# 배경음악: 콜드 오픈~2막 = nimble_motifs, 3막 = main_tema, 4막 = buant_pop_groove (대사 구간 덕킹)
def load_mp3(f, d):
    raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', f'{BGM}/{f}', '-t', str(d), '-f', 's16le', '-ac', '2', '-ar', str(SR), '-'], capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.int16).astype(np.float32).reshape(-1, 2) / 32768
ids = [c['id'] for c in TL]
segs = [('nimble_motifs.mp3', T0['K01'], T0['K30']), ('main_tema.mp3', T0['K30'], T0['K40']), ('buant_pop_groove.mp3', T0['K40'], TOTAL)]
bg = np.zeros_like(mix)
for f, a, b in segs:
    x = load_mp3(f, b - a + 1.0); n = min(len(x), len(bg) - int(a * SR)); fade = np.ones(n, np.float32)
    k = int(0.6 * SR); fade[:k] = np.linspace(0, 1, k); fade[-k:] = np.linspace(1, 0, k)
    bg[int(a * SR):int(a * SR) + n] += x[:n] * fade[:, None]
# 덕킹: 대사가 있는 구간은 배경음악을 낮춤
vo = np.abs(voice_end).max(1); win = int(0.25 * SR)
from scipy.ndimage import maximum_filter1d, uniform_filter1d
act = uniform_filter1d(maximum_filter1d((vo > 0.02).astype(np.float32), win), win)
gain = 0.16 - 0.09 * act
mix += bg * gain[:, None]
# 마무리: 피크 정규화(-1 dBFS)
pk = np.abs(mix).max(); mix *= 0.89 / max(pk, 1e-6)
w = wave.open(OUT, 'wb'); w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes((np.clip(mix, -1, 1) * 32767).astype(np.int16).tobytes()); w.close()
print('sound', OUT, round(TOTAL, 2), 's')
