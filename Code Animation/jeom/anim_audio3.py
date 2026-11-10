"""〈점〉 v3 소리: 거문고 + 북(물리 모형 합성, audio/instruments.py) + 비·천둥·용의 소리. 시각은 animatic3.CUTS 기준(초).
음악(music)·효과(sfx)·바탕(amb) 세 갈래로 섞고, 정적 구간은 음악 갈래만 부드러운 곡선으로 내린다(뚝 끊으면 지직거림)."""
import sys, os, wave
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, 'audio')); sys.path.insert(0, os.path.join(HERE, 'engine'))
import sketch as S
from instruments import geomungo as GM, buk, daehyeon
from anim_audio import put, thunder, bird
from anim_audio2 import tap, scrape
SR = S.SR

def roar(dur=3.6, amp=0.8, f0=(72.0, 52.0), formants=((380, 640, 1.0), (900, 1150, 0.6), (2300, 2600, 0.25)), seed=1):
    """용의 소리: 거친 성대 진동(톱니파 + 반 주파수 으르렁 + 떨림) + 숨소리를 입 모양 공명(열리며 F1이 오름)에 통과."""
    from scipy.signal import butter, lfilter
    r = np.random.default_rng(seed)
    n = int(dur * SR); t = np.arange(n) / SR
    u = t / dur
    f = f0[0] + (f0[1] - f0[0]) * u + 6 * np.sin(2 * np.pi * 5.5 * t) + np.cumsum(r.normal(0, 0.4, n)) / SR * 40
    ph = np.cumsum(f) / SR
    saw = 2 * (ph % 1.0) - 1
    sub = np.sign(np.sin(np.pi * ph)) * 0.5                               # 반 주파수: 으르렁거리는 거칠음
    src = (saw + sub) * (1 + 0.3 * r.normal(0, 1, n)) + S.bandnoise(n, 200, 5000) * 1.2
    out = np.zeros(n)
    for lo, hi, g in formants:
        fc_s = lo + (hi - lo) * np.clip(u * 2, 0, 1)                      # 입이 열리며 공명이 오른다(블록 단위로 근사)
        for k in range(8):
            a, b = int(k * n / 8), int((k + 1) * n / 8)
            fc = float(fc_s[(a + b) // 2])
            bb, aa = butter(2, [fc * 0.75 / (SR / 2), min(0.99, fc * 1.3 / (SR / 2))], btype='band')
            out[a:b] += lfilter(bb, aa, src[a:b]) * g
    env = np.clip(t / 0.35, 0, 1) ** 1.5 * np.exp(-np.clip(t - dur * 0.55, 0, None) / (dur * 0.25))
    x = out * env
    return x / (np.abs(x).max() + 1e-9) * amp

def growl(dur=3.5, amp=0.6):
    n = int(dur * SR); t = np.arange(n) / SR
    base = S.bandnoise(n, 40, 260) * (0.5 + 0.5 * np.sin(2 * np.pi * 23 * t))
    env = np.clip(t / 0.25, 0, 1) * np.exp(-np.clip(t - 1.6, 0, None) / 0.8)
    x = base * env
    return x / (np.abs(x).max() + 1e-9) * amp

def thunder(dur=3.4, amp=0.5, seed=0):
    n = int(dur * SR); t = np.arange(n) / SR
    r = np.random.default_rng(seed)
    x = S.bandnoise(n, 30, 400) * np.exp(-t / 0.9) * np.clip(t / 0.08, 0, 1)
    x *= 1 + 0.5 * np.repeat(r.standard_normal(n // 2400 + 1), 2400)[:n] * np.exp(-t / 0.6)      # 우르릉 굴러가는 덩어리
    x *= np.clip((dur - t) / 0.6, 0, 1)                                    # 꼬리를 곡선으로 닫는다(끝에서 뚝 끊기지 않게)
    return x / (np.abs(x).max() + 1e-9) * amp

def gate(tt, a, b, fall, rise):
    """a~b 구간을 0으로: a 직전 fall초 동안 코사인으로 내려가고, b 직전 rise초 동안 올라온다(b의 첫 타격은 온전히)."""
    g = np.ones_like(tt)
    d = (tt > a - fall) & (tt < a); g[d] = 0.5 + 0.5 * np.cos(np.pi * (tt[d] - (a - fall)) / fall)
    g[(tt >= a) & (tt <= b - rise)] = 0.0
    u = (tt > b - rise) & (tt < b); g[u] = 0.5 - 0.5 * np.cos(np.pi * (tt[u] - (b - rise)) / rise)
    return g

def smooth_step(tt, a, b): return np.clip((tt - a) / (b - a), 0, 1) ** 2 * (3 - 2 * np.clip((tt - a) / (b - a), 0, 1))

# 엔딩 시각(animatic3과 같게): 응시 컷 165.5~181.5 안에서 눈물이 떨어지는 시각
TEAR_LAND = 165.5 + 12.7

def build(out, T):
    n = int(T * SR); tt = np.arange(n) / SR
    mus = np.zeros(n); sfx = np.zeros(n); amb = np.zeros(n)
    amb += S.bandnoise(n, 80, 900) * 0.010 * (1 - smooth_step(tt, 25, 27))
    put(mus, GM(98.0, 3.0, 0.7, nonghyeon=0.9), 2.8); put(mus, GM(92.5, 3.0, 0.6, nonghyeon=1.0), 7.8)
    put(sfx, tap(0.30), 12.0); put(sfx, tap(0.30), 13.85); put(sfx, tap(0.45, 0.06, 300, 2500, 0.01), 17.02)
    put(sfx, scrape(2.8), 19.3); put(sfx, scrape(0.35, 0.16), 22.1)
    put(sfx, S.bandnoise(int(0.4 * SR), 300, 2500) * np.hanning(int(0.4 * SR)) * 0.08, 26.2)
    # 비: 29.4~ 들기 시작, 창틀(33~38) 크게, 여정 동안 바탕, 깨어남부터 몰아침, 폭풍, 승천에서 멎음(모두 곡선으로)
    amt = smooth_step(tt, 29.4, 32.4) * 0.8 + 0.4 * smooth_step(tt, 32.6, 33.4) * (1 - smooth_step(tt, 37.6, 38.4)) + smooth_step(tt, 82, 84) * 0.5
    amt = amt * (1 - 0.45 * smooth_step(tt, 105.2, 105.6) * (1 - smooth_step(tt, 108.4, 108.8)))   # 바닥: 빗소리만, 조금 멀어진다
    amt *= 1 - smooth_step(tt, 148.5, 151.5)
    amb += S.rain(n, np.clip(amt, 0, 1.4))
    for k, ts in enumerate(np.arange(34.0, 38.0, 0.35)):                    # 창틀에 부딪는 굵은 물방울
        put(sfx, tap(0.18, 0.05, 600, 5000, 0.008), ts + 0.07 * (k % 3))
    th = np.zeros(n)
    for i, (tf, a) in enumerate(((31.8, 0.6), (36.2, 0.7), (81.0, 1.0), (108.6, 0.9), (116.7, 0.7), (124.7, 0.8), (127.7, 0.8), (131.5, 0.6), (135.2, 1.0), (140.5, 0.7))):
        put(th, thunder(3.4, 0.38 * a, seed=i), tf + 0.3)
    # 여정: 합쳐질 때마다 거문고(구 시각 → 새 시각)
    scale = [220.0, 196.0, 174.6, 164.8, 146.8, 130.8, 123.5, 110.0, 98.0, 87.3]
    olds = [26.6, 32.0, 35.6, 43.4, 53.2, 56.3, 61.0, 63.1, 65.0, 66.7]
    m = lambda to: 38 + (to - 22) * 44 / 66
    for k, to in enumerate(olds): put(mus, GM(scale[k], 2.6, 0.9 - 0.06 * k), m(to))
    for tg in (73.0, 75.5, 78.0): put(sfx, S.fiber_tug(0.5), m(tg))
    # 눈을 뜸(여정 끝 ~80) → 거문고 호흡이 바뀐다: 같은 낮은 음의 맥박 + 북 둥. 둥.
    for k, ts in enumerate(np.arange(80.5, 97.0, 1.6)):
        put(mus, GM(73.4, 1.4, 0.55 + 0.02 * k, nonghyeon=0.1), ts)
        put(mus, buk(0.35 + 0.02 * k, 60.0, 1.6, strike=0.2), ts + 0.8)
    # 몸부림(97~111): 북이 빨라지고 대현이 두껍게 쌓인다 → 바닥(105.4~108.6) 정적 → 대현 + 큰 북
    beats = list(np.arange(97.0, 105.4, 0.55)); beats += list(np.arange(101.6, 105.4, 0.3))
    for i, ts in enumerate(sorted(beats)): put(mus, buk(0.45, 66.0, 0.9, strike=0.3 + 0.3 * (i % 2)), ts)
    for ts in (97.8, 101.6, 103.4): put(mus, daehyeon(0.7, 3.0, 0.15), ts)
    put(mus, daehyeon(1.0, 5.0, 0.4), 108.6); put(mus, buk(1.0, 50.0, 2.4, decay=0.7, strike=0.15), 108.6)
    # 벗어남(111) 북 몰아치기 → 방 안에서 돌아봄(116.5~122.5) 거의 정적, 거문고 한 구절 → 창을 넘음(122.5) 북 다시
    for i, ts in enumerate(np.arange(111.0, 116.3, 0.25)): put(mus, buk(0.55, 70.0, 0.7, strike=0.25 + 0.35 * (i % 2)), ts)
    for i, (ts, f) in enumerate(((117.8, 146.8), (119.0, 130.8), (119.8, 123.5), (121.0, 110.0))):
        put(mus, GM(f, 2.4, 0.5, nonghyeon=0.6), ts)
    # 폭풍(126.5~148.5): 북 + 대현 반복 음형, 포효(134.9) 으르렁 + 대현 긁기, 하늘 접수에서 북 몰아쳐 최고조
    for i, ts in enumerate(np.arange(122.5, 134.5, 0.45)): put(mus, buk(0.5, 64.0, 0.8, strike=0.3 + 0.3 * (i % 2)), ts)
    for ts in np.arange(124.0, 134.5, 1.8): put(mus, daehyeon(0.55, 2.0, 0.1), ts)
    put(mus, roar(3.8, 0.85), 134.9); put(mus, growl(3.5, 0.45), 134.9); put(mus, daehyeon(1.0, 4.0, 0.6), 135.0); put(mus, buk(1.0, 46.0, 2.6, decay=0.8, strike=0.15), 135.0)
    put(mus, roar(1.6, 0.45, f0=(80, 64), seed=3), 108.7)                    # 벗어나는 순간의 짧은 숨 소리
    put(mus, roar(4.0, 0.75, f0=(96, 120), formants=((500, 800, 1.0), (1100, 1500, 0.7), (2600, 3000, 0.3)), seed=5), 148.9)   # 승천: 높아지는 외침
    for i, ts in enumerate(np.arange(138.5, 153.0, 0.3)): put(mus, buk(0.5 + 0.35 * min(1, (ts - 138.5) / 12), 68.0, 0.6, strike=0.3 + 0.3 * (i % 2)), ts)
    for ts in np.arange(139.0, 153.0, 1.2): put(mus, daehyeon(0.6, 1.6, 0.15), ts)
    # 승천 중 꼬리가 화면을 '탁' 친다(C21 1.0초 = 149.5): 휙 바람 소리 → 큰 북 + 젖은 먹이 부딪는 소리
    nw = int(0.45 * SR); tw = np.arange(nw) / SR
    whoosh = S.bandnoise(nw, 150, 3000) * np.sin(np.pi * tw / 0.45) ** 2 * 0.35
    put(sfx, whoosh, 149.08)
    put(mus, buk(1.0, 44.0, 2.2, decay=0.6, strike=0.6), 149.5)
    ns = int(0.12 * SR); put(sfx, S.bandnoise(ns, 300, 6000) * np.exp(-np.arange(ns) / SR / 0.02) * 0.7, 149.5)
    # 해가 뜨는 순간 정적 1초(153~154) → 거문고 낮은 화음 길게
    for f in (55.0, 82.4, 110.0): put(mus, GM(f, 6.5, 0.5, nonghyeon=0.05), 154.0)
    r = np.random.default_rng(2)
    for tb in np.sort(r.uniform(159, 172, 6)): put(amb, bird(), tb)
    put(sfx, tap(0.20, 0.08, 500, 4000, 0.015), TEAR_LAND)                 # 눈물이 종이에 닿음
    put(mus, GM(130.8, 5.0, 0.8, nonghyeon=0.2), TEAR_LAND + 0.05)
    put(mus, GM(196.0, 4.0, 0.6, nonghyeon=0.2), 185.7); put(mus, GM(98.0, 6.0, 0.5, nonghyeon=0.1), 187.1)
    # 정적 두 곳: 음악·천둥만 내린다. 마른 소리는 40ms 곡선으로 멎고(방 울림은 자연히 사그라듦),
    # 울림까지 더한 뒤 250ms 곡선으로 완전히 닫는다. 다시 들어올 때는 첫 타격 직전 10ms 동안 연다.
    g_dry = gate(tt, 105.4, 108.6, 0.04, 0.01) * gate(tt, 153.0, 154.0, 0.04, 0.01)
    g_wet = gate(tt, 105.65, 108.6, 0.25, 0.01) * gate(tt, 153.25, 154.0, 0.25, 0.01)
    mus = S.reverb(mus * g_dry, 2.6, 0.30) * g_wet
    sfx = S.reverb(sfx, 1.2, 0.18)
    th = th * g_wet
    mix = mus + sfx + th + amb
    mix *= 1 - smooth_step(tt, T - 1.4, T)
    mix = np.tanh(mix * 1.5) * 0.8
    with wave.open(out, 'w') as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((np.clip(mix, -1, 1) * 32767).astype(np.int16).tobytes())
    return mix

def clicks(x, thr=6.0):
    """지직거림 검사: 2차 차분이 주변 수준보다 thr배 넘게 튀는 곳(초)."""
    d2 = np.abs(np.diff(x, 2))
    k = int(0.02 * SR); ref = np.convolve(d2, np.ones(k) / k, 'same') + 1e-4
    idx = np.where(d2 > thr * ref)[0]
    out = []
    for i in idx:
        if not out or i / SR - out[-1] > 0.05: out.append(i / SR)
    return out

if __name__ == '__main__':
    x = build(sys.argv[1], float(sys.argv[2]))
    c = clicks(x)
    print(len(c), 'suspects', [round(v, 2) for v in c[:60]])
