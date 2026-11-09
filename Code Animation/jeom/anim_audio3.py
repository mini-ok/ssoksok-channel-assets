"""애니마틱 v3 임시 소리: 거문고 + 북(대금 없음). 시각은 animatic3.CUTS 기준(초)."""
import sys, os, wave
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, 'audio')); sys.path.insert(0, os.path.join(HERE, 'engine'))
import sketch as S
from anim_audio import put, thunder, bird
from anim_audio2 import tap, scrape
SR = S.SR

def buk(amp=0.6, f0=62.0, dur=1.2):
    """북: 가죽 울림(낮은 사인, 음높이가 살짝 내려감) + 채 소리."""
    n = int(dur * SR); t = np.arange(n) / SR
    f = f0 * (1 + 0.35 * np.exp(-t / 0.05))
    body = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / 0.35)
    stick = S.bandnoise(n, 200, 2000) * np.exp(-t / 0.012) * 0.5
    return (body + stick) * amp

def daehyeon(amp=0.8, dur=4.0, scrape_=0.0):
    """거문고 대현(가장 굵은 줄): 낮고 두꺼운 음 + 술대로 긁는 소리."""
    x = S.geomungo(55.0, dur, amp, nonghyeon=0.25)
    if scrape_ > 0:
        n = len(x); t = np.arange(n) / SR
        x = x + S.bandnoise(n, 120, 900) * np.exp(-t / 0.25) * scrape_
    return x

def growl(dur=3.5, amp=0.6):
    n = int(dur * SR); t = np.arange(n) / SR
    base = S.bandnoise(n, 40, 260) * (0.5 + 0.5 * np.sin(2 * np.pi * 23 * t))
    env = np.clip(t / 0.25, 0, 1) * np.exp(-np.clip(t - 1.6, 0, None) / 0.8)
    x = base * env
    return x / (np.abs(x).max() + 1e-9) * amp

def build(out, T):
    n = int(T * SR); tt = np.arange(n) / SR; mix = np.zeros(n)
    mix += S.bandnoise(n, 80, 900) * 0.010 * (tt < 26)
    put(mix, S.geomungo(98.0, 3.0, 0.7, nonghyeon=0.9), 2.8); put(mix, S.geomungo(92.5, 3.0, 0.6, nonghyeon=1.0), 7.8)
    put(mix, tap(0.30), 12.0); put(mix, tap(0.30), 13.85); put(mix, tap(0.45, 0.06, 300, 2500, 0.01), 17.02)
    put(mix, scrape(2.8), 19.3); put(mix, scrape(0.35, 0.16), 22.1)
    put(mix, S.bandnoise(int(0.4 * SR), 300, 2500) * np.hanning(int(0.4 * SR)) * 0.08, 26.2)
    # 비: 29.4~ 들기 시작, 창틀(33~38) 크게, 여정 동안 바탕, 깨어남부터 몰아침, 폭풍, 승천에서 멎음
    amt = np.clip((tt - 29.4) / 3.0, 0, 1) * 0.8 + 0.4 * ((tt > 33) & (tt < 38)) + np.clip((tt - 82) / 2, 0, 1) * 0.5
    amt *= 1 - np.clip((tt - 148.5) / 3.0, 0, 1)
    mix += S.rain(n, np.clip(amt, 0, 1.4))
    for k, ts in enumerate(np.arange(34.0, 38.0, 0.35)):                    # 창틀에 부딪는 굵은 물방울
        put(mix, tap(0.18, 0.05, 600, 5000, 0.008), ts + 0.07 * (k % 3))
    for tf, a in ((31.8, 0.6), (36.2, 0.7), (81.0, 1.0), (108.6, 0.9), (124.7, 0.8), (127.7, 0.8), (131.5, 0.6), (135.2, 1.0), (140.5, 0.7)):
        put(mix, thunder(3.0, 0.38 * a), tf + 0.3)
    # 여정: 합쳐질 때마다 거문고(구 시각 → 새 시각)
    scale = [220.0, 196.0, 174.6, 164.8, 146.8, 130.8, 123.5, 110.0, 98.0, 87.3]
    olds = [26.6, 32.0, 35.6, 43.4, 53.2, 56.3, 61.0, 63.1, 65.0, 66.7]
    m = lambda to: 38 + (to - 22) * 44 / 66
    for k, to in enumerate(olds): put(mix, S.geomungo(scale[k], 2.6, 0.9 - 0.06 * k), m(to))
    for tg in (73.0, 75.5, 78.0): put(mix, S.fiber_tug(0.5), m(tg))
    # 눈을 뜸(여정 끝 ~80) → 거문고 호흡이 바뀐다: 같은 낮은 음의 맥박 + 북 둥. 둥.
    for k, ts in enumerate(np.arange(80.5, 97.0, 1.6)):
        put(mix, S.geomungo(73.4, 1.4, 0.55 + 0.02 * k, nonghyeon=0.1), ts)
        put(mix, buk(0.35 + 0.02 * k), ts + 0.8)
    # 몸부림(97~111): 북이 빨라지고 대현이 두껍게 쌓인다 → 바닥(105.4~108.6) 정적 → 대현 + 큰 북
    beats = list(np.arange(97.0, 105.4, 0.55)); beats += list(np.arange(101.6, 105.4, 0.3))
    for ts in sorted(beats): put(mix, buk(0.45, 66.0, 0.8), ts)
    for ts in (97.8, 101.6, 103.4): put(mix, daehyeon(0.7, 3.0, 0.15), ts)
    mute = (tt > 105.4) & (tt < 108.6)
    put(mix, daehyeon(1.0, 5.0, 0.4), 108.6); put(mix, buk(1.0, 52.0, 2.0), 108.6)
    # 벗어남(111) 북 몰아치기 → 창가(116.5~122.5) 거의 정적, 거문고 한 구절 → 창을 넘음(122.5) 북 다시
    for ts in np.arange(111.0, 116.3, 0.25): put(mix, buk(0.55, 70.0, 0.6), ts)
    for i, (ts, f) in enumerate(((117.4, 146.8), (118.6, 130.8), (119.4, 123.5), (120.6, 110.0))):
        put(mix, S.geomungo(f, 2.4, 0.5, nonghyeon=0.6), ts)
    # 폭풍(126.5~148.5): 북 + 대현 반복 음형, 포효(134.7) 으르렁 + 대현 긁기, 하늘 접수에서 북 몰아쳐 최고조
    for ts in np.arange(122.5, 134.5, 0.45): put(mix, buk(0.5, 64.0, 0.7), ts)
    for ts in np.arange(124.0, 134.5, 1.8): put(mix, daehyeon(0.55, 2.0, 0.1), ts)
    put(mix, growl(3.5, 0.7), 134.7); put(mix, daehyeon(1.0, 4.0, 0.6), 134.8); put(mix, buk(1.0, 48.0, 2.2), 134.8)
    for ts in np.arange(138.5, 153.0, 0.3): put(mix, buk(0.5 + 0.35 * min(1, (ts - 138.5) / 12), 68.0, 0.5), ts)
    for ts in np.arange(139.0, 153.0, 1.2): put(mix, daehyeon(0.6, 1.6, 0.15), ts)
    # 해가 뜨는 순간(151.6) 정적 1초 → 거문고 낮은 화음 길게
    mute2 = (tt > 153.0) & (tt < 154.0)
    for f in (55.0, 82.4, 110.0): put(mix, S.geomungo(f, 6.5, 0.5, nonghyeon=0.05), 154.0)
    r = np.random.default_rng(2)
    for tb in np.sort(r.uniform(159, 172, 6)): put(mix, bird(), tb)
    put(mix, tap(0.25, 0.08, 200, 1500, 0.02), 173.2)
    put(mix, tap(0.20, 0.08, 500, 4000, 0.015), 177.4)
    put(mix, S.geomungo(130.8, 5.0, 0.8, nonghyeon=0.2), 177.5)
    put(mix, S.geomungo(196.0, 4.0, 0.6, nonghyeon=0.2), 182.3)
    mix = S.reverb(mix, 2.6, 0.30)
    mix[mute | mute2] *= 0.0
    mix[(tt > 105.4) & (tt < 108.6)] += S.rain(int(mute.sum()), np.full(int(mute.sum()), 0.6))[:int(mute.sum())] * 1.0   # 바닥: 빗소리만
    mix *= 1 - np.clip((tt - (T - 1.4)) / 1.4, 0, 1)
    mix = np.tanh(mix * 1.5) * 0.8
    with wave.open(out, 'w') as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((np.clip(mix, -1, 1) * 32767).astype(np.int16).tobytes())
