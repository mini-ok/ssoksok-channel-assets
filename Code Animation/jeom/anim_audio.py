"""애니마틱 임시 소리(126초): 빗소리·돌풍·천둥, 점이 번질 때마다 거문고 한 음, 정적 속 섬유 소리, 대금, 아침 새소리."""
import sys, os, math, wave
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, 'audio')); sys.path.insert(0, os.path.join(HERE, 'engine'))
import sketch as S
import timeline as TL

SR = S.SR


def put(mix, x, t):
    i = int(t * SR); j = min(len(mix), i + len(x))
    if i < len(mix):
        mix[i:j] += x[:j - i]


def thunder(dur=3.0, amp=0.5):
    n = int(dur * SR); t = np.arange(n) / SR
    x = S.bandnoise(n, 30, 400) * np.exp(-t / 0.9) * np.clip(t / 0.08, 0, 1)
    return x / (np.abs(x).max() + 1e-9) * amp


def bird(t0=0.0):
    n = int(0.35 * SR); t = np.arange(n) / SR
    f = 3200 + 900 * np.sin(2 * np.pi * 9 * t) - 1500 * t
    return 0.08 * np.sin(2 * np.pi * np.cumsum(f) / SR) * np.sin(np.pi * t / 0.35) ** 2


def build(out):
    T = TL.TOTAL; n = int(T * SR); tt = np.arange(n) / SR
    mix = np.zeros(n)
    # 등잔·바람(C1~C3)
    amb = S.bandnoise(n, 80, 900) * 0.012 * (tt < 22)
    mix += amb
    # 비: 22초부터 들어와 66.5~69초에 멎음, C10~C11에 다시(창밖 폭풍)
    rain_amt = np.clip((tt - 22.5) / 2.5, 0, 1) * (1 - np.clip((tt - 66.5) / 2.5, 0, 1))
    rain_amt += np.clip((tt - 84) / 2, 0, 1) * (1 - np.clip((tt - 101) / 2, 0, 1)) * 0.8
    mix += S.rain(n, rain_amt)
    for tf, a in TL.FLASHES:
        put(mix, thunder(3.0, 0.35 * a), tf + 0.6)
    # 붓에서 떨어지는 먹(13.0): 톡
    put(mix, S.bandnoise(int(0.04 * SR), 400, 3000) * np.exp(-np.arange(int(0.04 * SR)) / SR / 0.006) * 0.4, 13.0)
    # 거문고: 단계마다 한 음(갈수록 낮고 여리게)
    scale = [220.0, 196.0, 174.6, 164.8, 146.8, 130.8, 123.5, 110.0, 98.0, 87.3, 82.4]
    for k, st in enumerate(TL.STAGES[1:]):
        v = 0.9 - 0.06 * k
        put(mix, S.geomungo(scale[k], 2.6, v, bend_end=-50 if k >= 7 else 0), st[0] - 0.05)
    # 합류(45초): 낮은 음 하나 더
    put(mix, S.geomungo(146.8, 2.2, 0.6, nonghyeon=0.6), 45.1)
    # 정적 속 섬유 세 번
    for tg, _, _ in TL.GATHER:
        put(mix, S.fiber_tug(0.5), tg - 0.05)
    # 대금: 눈이 뜨이는 82초부터 103초까지
    notes = [(0.0, 3.0, 392.0, 0.5), (3.0, 1.6, 440.0, 0.65), (4.6, 4.4, 587.3, 1.0), (9.0, 1.4, 659.3, 0.95),
             (10.4, 3.6, 587.3, 0.85), (14.0, 1.4, 523.3, 0.7), (15.4, 4.6, 440.0, 0.5)]
    buzz = lambda x: float(np.clip((x - 2.0) / 3.0, 0, 1) * (1 - np.clip((x - 13.5) / 3.0, 0, 1)))
    put(mix, S.daegeum(notes, buzz), 82.2)
    # 아침: 새소리, 끝 거문고 한 음 + 대금 여운
    r = np.random.default_rng(2)
    for _ in range(9):
        put(mix, bird(), 103.5 + r.uniform(0, 20))
    put(mix, S.geomungo(110.0, 3.0, 0.8, nonghyeon=0.5), 110.0)
    put(mix, S.daegeum([(0.0, 4.0, 440.0, 0.35)], lambda x: 0.0), 111.0)
    put(mix, S.geomungo(82.4, 4.0, 0.55, nonghyeon=0.3, bend_end=-40), 119.5)
    mix = S.reverb(mix, 2.4, 0.28)
    # 규칙 깨기 정적: 리버브 꼬리까지 잘라 완전한 정적(섬유 소리만)
    sil = (tt > 71.0) & (tt < 81.8)
    tug_only = np.zeros(n)
    for tg, _, _ in TL.GATHER:
        put(tug_only, S.fiber_tug(0.5), tg - 0.05)
    mix[sil] = tug_only[sil] * 0.6
    mix = mix / np.abs(mix).max() * 0.85
    mix = np.tanh(mix * 1.1) / np.tanh(1.1)
    mix *= np.clip((T - tt) / 1.5, 0, 1)
    st = np.stack([mix, np.roll(mix, int(0.0007 * SR))], 1)
    with wave.open(out, 'wb') as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((st * 32767).astype(np.int16).tobytes())


if __name__ == '__main__':
    build(sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, 'cache', 'animatic.wav'))
