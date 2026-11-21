"""지식 쇼츠 소리 — 에피소드의 장면 시각표로 자동 합성(numpy).
python3 audio.py <에피소드> out.wav
- 바탕: 느린 5음계 가야금풍 튕김(4박 고리) + 낮은 거문고 한 음씩(장면 시작마다)
- 효과: 장면 넘김 종이 휙, 글자 붙을 때 '탁', 막대가 자랄 때 올라가는 실소리, 숫자 셀 때 똑딱, 정답에 북, 끝 낙관에 거문고
에피소드에 SOUND = dict(seed=…, root=…) 를 두면 음 높이·무작위를 바꾼다. EXTRA_SOUND(put, lib, ep) 함수가 있으면 추가 효과를 넣는다.
"""
import os, sys, wave
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(os.path.dirname(HERE), 'jeom', 'audio'))
import engine as E                          # noqa: E402
from instruments import geomungo, buk       # noqa: E402
from sketch import reverb                   # noqa: E402

SR = 48000


def band(x, lo, hi, slope=2.0):
    X = np.fft.rfft(x); f = np.fft.rfftfreq(len(x), 1 / SR)
    g = 1 / (1 + (lo / np.maximum(f, 1)) ** (2 * slope)) / (1 + (f / hi) ** (2 * slope))
    return np.fft.irfft(X * g, len(x))


def norm(x): return x / (np.abs(x).max() + 1e-9)


class Lib:
    def __init__(self, seed):
        self.rng = np.random.default_rng(seed)

    def swoosh(self, dur, g=1.0):
        n = int(dur * SR); t = np.arange(n) / SR
        return g * norm(band(self.rng.standard_normal(n), 300, 5000)) * np.sin(np.pi * t / dur) ** 1.5

    def rustle(self, dur, g=1.0, crisp=0.5):
        r = self.rng; n = int(dur * SR); t = np.arange(n) / SR
        base = band(r.standard_normal(n), 900, 7000)
        ticks = np.zeros(n); k = r.random(n) < (0.004 + 0.02 * crisp); ticks[k] = r.standard_normal(k.sum())
        ticks = band(ticks, 2000, 11000)
        env = np.sin(np.pi * np.clip(t / dur, 0, 1)) ** 1.5
        return g * (0.5 * norm(base) + crisp * norm(ticks)) * env

    def snap(self, g=1.0):
        r = self.rng; n = int(0.09 * SR); t = np.arange(n) / SR
        x = band(r.standard_normal(n), 1500, 9000) * np.exp(-t / 0.012) + 0.4 * band(r.standard_normal(n), 200, 900) * np.exp(-t / 0.02)
        return g * norm(x)

    def tink(self, g=1.0, f0=2650):
        n = int(0.5 * SR); t = np.arange(n) / SR
        x = sum(a * np.sin(2 * np.pi * f0 * m * t) * np.exp(-t / (0.12 / m)) for m, a in [(1, 1), (2.31, 0.4), (3.9, 0.2)])
        return g * norm(x)

    def rise(self, dur, g=1.0, f0=300, f1=900):
        n = int(dur * SR); t = np.arange(n) / SR
        f = f0 + (f1 - f0) * (t / dur) ** 0.8
        x = np.sin(2 * np.pi * np.cumsum(f) / SR) * (0.6 + 0.4 * np.sin(2 * np.pi * 30 * t))
        return g * band(x, 200, 4000) * np.sin(np.pi * t / dur) ** 0.8

    def pluck(self, f0, dur=1.2, g=1.0, bright=0.6):
        n = int(dur * SR); p = max(2, int(SR / f0))
        buf = self.rng.uniform(-1, 1, p) * np.hanning(p) ** 0.3
        out = np.zeros(n); k = 0.5 + 0.49 * bright
        for i in range(n):
            x = buf[i % p]; out[i] = x
            buf[i % p] = (k * x + (1 - k) * buf[(i + 1) % p]) * 0.996
        return g * norm(out) * np.exp(-np.arange(n) / SR / (dur * 0.35))


def make(ep, out):
    snd = getattr(ep.m, 'SOUND', {})
    lib = Lib(snd.get('seed', 7))
    root = snd.get('root', 196.0)                 # G3
    scale = [1, 9 / 8, 5 / 4, 3 / 2, 5 / 3, 2, 9 / 4, 5 / 2, 3, 10 / 3]   # 5음계(두 옥타브)
    N = int(ep.DUR * SR)
    fx, mus, amb = np.zeros(N), np.zeros(N), np.zeros(N)

    def put(buf, t, x, g=1.0):
        i = int(t * SR); j = min(N, i + len(x))
        if 0 <= i < N: buf[i:j] += g * x[:j - i]

    # 바탕 고리: 0.5초 간격 튕김, 4마디마다 무늬를 바꿈
    pat = [[0, 2, 4, 2], [0, 3, 5, 3], [1, 3, 5, 4], [0, 2, 4, 6]]
    step = snd.get('step', 0.5)
    t = 0.3
    while t < ep.T_END - 0.3:
        bar = int(t / (step * 4)); p = pat[bar % len(pat)]; j = int(round((t - 0.3) / step)) % 4
        put(mus, t, lib.pluck(root * scale[p[j]], 1.1, 0.22 if j else 0.3, 0.55))
        t += step
    # 장면 사건
    for tm, kind, b in E.beat_marks(ep):
        if kind == 'in':
            put(fx, max(0, tm - 0.05), lib.swoosh(0.5, 0.16)); put(fx, tm + 0.35, lib.snap(0.3))
            put(mus, tm, geomungo(root / 2, 2.6, 0.32, seed=int(tm * 10)))
        elif kind == 'grow':
            put(fx, tm, lib.rise(1.1, 0.12)); put(mus, tm + 0.9, lib.pluck(root * 2, 1.4, 0.32))
        elif kind == 'count':
            cnt = b.get('count', 1.8); n = 14
            for k in range(n):
                put(fx, tm + cnt * (1 - (1 - k / n) ** 2), lib.tink(0.035, 1500 + 60 * k))
            put(fx, tm + cnt, lib.tink(0.09, 2600))
        elif kind == 'tick':
            put(fx, tm, lib.snap(0.35)); put(mus, tm + 0.05, lib.pluck(root * scale[5], 1.0, 0.25))
        elif kind == 'hit':
            put(fx, tm, buk(0.45, 60, 1.3, 0.35, seed=int(tm * 7)))
            for jx, k in enumerate([0, 2, 4, 5]): put(mus, tm + 0.12 * jx, lib.pluck(root * scale[k] * 2, 1.6, 0.3))
        elif kind == 'seal':
            put(fx, tm, lib.snap(0.5)); put(mus, tm, geomungo(root / 2 * 0.75, 3.0, 0.45, seed=9))
    extra = getattr(ep.m, 'EXTRA_SOUND', None)
    if extra: extra(lambda t, x, g=1.0, bus='fx': put({'fx': fx, 'mus': mus, 'amb': amb}[bus], t, x, g), lib, ep)

    amb += 0.004 * norm(band(lib.rng.standard_normal(N), 100, 2000))
    music = reverb(mus, sec=2.0, mix=0.26)[:N]
    fxr = reverb(fx, sec=0.8, mix=0.12)[:N]
    mix = amb + fxr + 0.75 * music
    fade = int(0.15 * SR); mix[:fade] *= np.linspace(0, 1, fade)
    end = int(1.2 * SR); mix[-end:] *= np.linspace(1, 0, end) ** 2
    mix = mix / (np.abs(mix).max() + 1e-9) * 0.85
    st = np.stack([mix, np.roll(mix, int(0.0004 * SR))], 1)
    with wave.open(out, 'wb') as wf:
        wf.setnchannels(2); wf.setsampwidth(2); wf.setframerate(SR)
        wf.writeframes((st * 32767).astype(np.int16).tobytes())
    print('WROTE', out)


if __name__ == '__main__':
    make(E.Episode(sys.argv[1]), sys.argv[2])
