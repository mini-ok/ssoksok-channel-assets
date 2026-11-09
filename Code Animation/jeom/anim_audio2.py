"""애니마틱 v2 임시 소리. 시각은 animatic2.CUTS 기준(초)."""
import sys, os, math, wave
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, 'audio')); sys.path.insert(0, os.path.join(HERE, 'engine'))
import sketch as S
from anim_audio import put, thunder, bird
SR = S.SR

def tap(amp=0.35, dur=0.04, lo=400, hi=3000, tau=0.006):
    n = int(dur * SR); return S.bandnoise(n, lo, hi) * np.exp(-np.arange(n) / SR / tau) * amp

def scrape(dur, amp=0.10):
    n = int(dur * SR); t = np.arange(n) / SR
    x = S.bandnoise(n, 1500, 7000) * (0.6 + 0.4 * np.sin(2 * np.pi * 23 * t) ** 2)
    return x / (np.abs(x).max() + 1e-9) * amp * np.clip(t / 0.05, 0, 1) * np.clip((dur - t) / 0.05, 0, 1)

def build(out, T):
    n = int(T * SR); tt = np.arange(n) / SR; mix = np.zeros(n)
    # 방 공기·등잔(0~24.6)
    mix += S.bandnoise(n, 80, 900) * 0.010 * (tt < 26)
    # C1: 떨리는 두 번의 시도마다 거문고 낮은 음(술대 끝이 떨린다)
    put(mix, S.geomungo(98.0, 3.0, 0.7, nonghyeon=0.9), 2.8)
    put(mix, S.geomungo(92.5, 3.0, 0.6, nonghyeon=1.0), 7.8)
    # C2: 미끄러진 붓끝 두 번(12.0, 13.85)
    put(mix, tap(0.30), 12.0); put(mix, tap(0.30), 13.85)
    # C3: 방울이 종이에 닿음(15.4 + 1.62)
    put(mix, tap(0.45, 0.06, 300, 2500, 0.01), 17.02)
    # C4: 칼질(19.3~22.1), 비뚤어짐에서 멈춤
    put(mix, scrape(2.8), 19.3); put(mix, scrape(0.35, 0.16), 22.1)
    # C5: 등잔 끄는 숨(26.2), 비가 들어옴
    put(mix, S.bandnoise(int(0.4 * SR), 300, 2500) * np.hanning(int(0.4 * SR)) * 0.08, 26.2)
    rain_amt = np.clip((tt - 29.4) / 3.0, 0, 1) * 0.8
    rain_amt += np.clip((tt - 85) / 1.0, 0, 1) * 0.6                     # 폭우
    rain_amt *= 1 - np.clip((tt - 121.1) / 1.4, 0, 1)                    # 비가 멎는다(C17)
    mix += S.rain(n, np.clip(rain_amt, 0, 1.4))
    for tf, a in ((31.8, 0.6), (85.0, 1.0), (90.0, 0.7), (98.2, 0.8), (108.6, 0.7), (116.1, 0.8), (118.5, 0.9), (121.1, 1.0)):
        put(mix, thunder(3.0, 0.38 * a), tf + 0.3)
    # 여정: 합쳐질 때마다 거문고(구 시각 → 새 시각: 33 + (t_old-22)*52/66)
    scale = [220.0, 196.0, 174.6, 164.8, 146.8, 130.8, 123.5, 110.0, 98.0, 87.3]
    olds = [26.6, 32.0, 35.6, 43.4, 53.2, 56.3, 61.0, 63.1, 65.0, 66.7]
    for k, to in enumerate(olds):
        put(mix, S.geomungo(scale[k], 2.6, 0.9 - 0.06 * k), 33 + (to - 22) * 52 / 66)
    for tg in (73.0, 75.5, 78.0):                                        # 세 번 모임(정적 속 섬유)
        put(mix, S.fiber_tug(0.5), 33 + (tg - 22) * 52 / 66)
    # 대금: 눈이 뜨이는 순간부터 PP2, 솟아오름과 폭풍에서 청이 떤다
    notes = [(0.0, 3.0, 392.0, 0.5), (3.0, 1.6, 440.0, 0.6), (4.6, 4.0, 349.2, 0.7), (8.6, 6.0, 329.6, 0.6),
             (14.6, 5.0, 293.7, 0.55), (19.6, 3.0, 440.0, 0.8), (22.6, 4.2, 587.3, 1.0), (26.8, 3.0, 659.3, 1.0), (29.8, 5.0, 587.3, 0.8)]
    buzz = lambda x: float(np.clip((x - 21.0) / 2.0, 0, 1) * (1 - np.clip((x - 31.0) / 2.0, 0, 1)))
    put(mix, S.daegeum(notes, buzz), 85.6)
    # 비가 멎은 뒤 1초 정적 → 새벽 새소리
    mix *= np.where((tt > 122.4) & (tt < 123.5), 0.0, 1.0)
    r = np.random.default_rng(2)
    for tb in np.sort(r.uniform(125, 140, 6)):
        put(mix, bird(), tb)
    # C19 칼을 내려놓음(143.0), C20 눈물(143.5+2.9)
    put(mix, tap(0.25, 0.08, 200, 1500, 0.02), 143.0)
    put(mix, tap(0.20, 0.08, 500, 4000, 0.015), 146.4)
    put(mix, S.geomungo(130.8, 5.0, 0.8, nonghyeon=0.2), 146.5)
    put(mix, S.geomungo(196.0, 5.0, 0.6, nonghyeon=0.2), 151.3)
    mix = S.reverb(mix, 2.6, 0.30)
    mix *= 1 - np.clip((tt - (T - 1.4)) / 1.4, 0, 1)
    mix = np.tanh(mix * 1.6) * 0.8
    with wave.open(out, 'w') as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((np.clip(mix, -1, 1) * 32767).astype(np.int16).tobytes())
