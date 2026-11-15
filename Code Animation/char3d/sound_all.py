"""〈심장의 휴가〉 전체 임시 소리(합성). C1–C4는 sound_a1.py가 만든 a1.wav를 그대로 쓰고, C5 이후를 여기서 만든다.
사용: python3 sound_all.py a1.wav out.wav   (컷 시작 시각은 아래 CUT과 assemble 순서가 같아야 함)"""
import sys, wave, numpy as np
from scipy.signal import butter, lfilter
SR = 44100
CUT = {'A1': (0.0000, 32.0000), 'C5': (32.0000, 6.0000), 'C6': (38.0000, 6.0000), 'C7': (44.0000, 6.0000), 'C8a': (50.0000, 5.0000), 'C8': (55.0000, 7.0000), 'C9': (62.0000, 5.0000), 'C10': (67.0000, 7.0000), 'C11a': (74.0000, 2.0000), 'C11b': (76.0000, 1.5833), 'C11c': (77.5833, 1.5833), 'C11d': (79.1667, 1.5833), 'C11e': (80.7500, 1.2083), 'C12': (81.9583, 9.0000), 'C13': (90.9583, 6.0000), 'C14': (96.9583, 8.0000), 'C15a': (104.9583, 5.0000), 'C15b': (109.9583, 3.0000), 'C15c': (112.9583, 2.2083), 'C16': (115.1667, 12.0000), 'TITLE': (127.1667, 8.0000)}   # 실제 프레임 수(24fps)로 계산
DUR = 135.1667
n = int(DUR * SR); L = np.zeros(n); R = np.zeros(n); rng = np.random.default_rng(11)
def lp(x, f): b, a = butter(2, f / (SR / 2)); return lfilter(b, a, x)
def hp(x, f): b, a = butter(2, f / (SR / 2), 'high'); return lfilter(b, a, x)
def bp(x, f0, f1): b, a = butter(2, [min(f0, f1) / (SR / 2), max(f0, f1) / (SR / 2)], 'band'); return lfilter(b, a, x)
tt = lambda d: np.arange(int(d * SR)) / SR
def put(x, t, g=1.0, pan=0.0):
    i = int(t * SR)
    if i >= n or i + len(x) <= 0: return
    if i < 0: x = x[-i:]; i = 0
    j = min(n, i + len(x)); x = x[:j - i] * g; L[i:j] += x * (1 - pan) * 0.7; R[i:j] += x * (1 + pan) * 0.7
def at(cut, t): return CUT[cut][0] + t
def env(d, a=0.005, r=0.05): t = tt(d); return np.clip(t / a, 0, 1) * np.clip((d - t) / r, 0, 1)
def thump(vel=1.0, f=62):
    t = tt(0.45); body = np.sin(2 * np.pi * np.cumsum(f + 90 * np.exp(-t * 30)) / SR) * np.exp(-t * 9); air = bp(rng.normal(0, 1, len(t)), 200, 900) * np.exp(-t * 14) * 0.25
    return lp(body + air, 1200) * vel
def lub(vel=0.5): t = tt(0.25); return lp(np.sin(2 * np.pi * 85 * t) * np.exp(-t * 22), 900) * vel
def clank(vel=0.6, f=380): t = tt(0.5); return hp(sum(np.sin(2 * np.pi * f * k * t + k) * np.exp(-t * (8 + 6 * k)) for k in (1, 2.76, 5.4)), 200) * vel
def mallet(f, d=1.0, vel=0.25): t = tt(d); return lp((np.sin(2 * np.pi * f * t) + 0.3 * np.sin(2 * np.pi * f * 4 * t) * np.exp(-t * 18)) * np.exp(-t * 4.5) * np.clip(t / 0.004, 0, 1), 3200) * vel
def celesta(f, d=1.6, vel=0.2): t = tt(d); return lp((np.sin(2 * np.pi * f * t) + 0.5 * np.sin(2 * np.pi * f * 2 * t) * np.exp(-t * 3) + 0.2 * np.sin(2 * np.pi * f * 3 * t) * np.exp(-t * 6)) * np.exp(-t * 2.2) * np.clip(t / 0.003, 0, 1), 5000) * vel
def piano(f, d=2.0, vel=0.25):
    t = tt(d); x = sum(g * np.sin(2 * np.pi * f * k * t) * np.exp(-t * (1.6 + k * 0.8)) for k, g in ((1, 1), (2, 0.4), (3, 0.15), (4, 0.06)))
    return lp(x * np.clip(t / 0.004, 0, 1), 3500) * vel
def organ(freqs, d, vel=0.12, att=0.4):
    t = tt(d); x = sum(np.sin(2 * np.pi * f * t) + 0.35 * np.sin(4 * np.pi * f * t) + 0.12 * np.sin(6 * np.pi * f * t) for f in freqs)
    return lp(x * np.clip(t / att, 0, 1) * np.clip((d - t) / 0.6, 0, 1), 2500) * vel / len(freqs)
def pad(freqs, d, vel=0.1, att=1.0):   # 부드러운 현 패드(약간 어긋난 톱니 → 저역 통과)
    t = tt(d); x = sum(sum(((t * f * (1 + dt)) % 1) * 2 - 1 for dt in (-0.004, 0.0, 0.005)) for f in freqs)
    return lp(x * np.clip(t / att, 0, 1) * np.clip((d - t) / 1.0, 0, 1), 1400) * vel / len(freqs) / 3
def glide(f0, f1, d, vel=0.2): t = tt(d); f = f0 * (f1 / f0) ** (t / d); return lp(np.sin(2 * np.pi * np.cumsum(f) / SR) * env(d, 0.02, 0.06), 2500) * vel
def whoosh(d=0.4, f0=300, f1=2000, vel=0.2):
    t = tt(d); x = rng.normal(0, 1, len(t)); out = np.zeros_like(x); fs = np.linspace(f0, f1, 6)
    for k in range(5): seg = slice(k * len(t) // 5, (k + 1) * len(t) // 5); out[seg] = bp(x, fs[k], fs[k + 1])[seg]
    return out * np.sin(np.pi * t / d) * vel
def step(vel=0.12): t = tt(0.12); return lp(np.sin(2 * np.pi * np.cumsum(180 - 600 * t) / SR) * np.exp(-t * 40), 1500) * vel
def tiptoe(vel=0.08): t = tt(0.06); return hp(rng.normal(0, 1, len(t)) * np.exp(-t * 80), 1500) * vel
def breath(d, vel=0.12, f=(300, 1400)): t = tt(d); return bp(rng.normal(0, 1, len(t)), *f) * np.sin(np.pi * t / d) ** 1.5 * vel
def plip(vel=0.12): t = tt(0.15); return np.sin(2 * np.pi * np.cumsum(1400 - 5000 * t) / SR) * np.exp(-t * 35) * vel
def beep(f, d=0.12, vel=0.15): t = tt(d); return np.sin(2 * np.pi * f * t) * env(d, 0.005, 0.02) * vel
def boom(vel=0.9):
    t = tt(1.4); x = np.sin(2 * np.pi * np.cumsum(45 + 120 * np.exp(-t * 8)) / SR) * np.exp(-t * 3) + lp(rng.normal(0, 1, len(t)), 1800) * np.exp(-t * 6) * 0.8
    return x * vel
def ping(f=2400, vel=0.15): t = tt(0.4); return (np.sin(2 * np.pi * f * t) + 0.5 * np.sin(2 * np.pi * f * 2.7 * t)) * np.exp(-t * 12) * vel
def creak(d=0.6, vel=0.06, f=180): t = tt(d); return bp(((t * (f + 40 * np.sin(t * 30))) % 1) * 2 - 1, 300, 1500) * np.sin(np.pi * t / d) * vel
def hum(notes, t0, step_t=0.4, vel=0.07):   # 콧노래(비브라토 사인)
    for i, f in enumerate(notes): t = tt(step_t * 0.95); put(lp(np.sin(2 * np.pi * f * t + 3 * np.sin(2 * np.pi * 5.5 * t) / 5.5) * env(step_t * 0.95, 0.04, 0.08), 1500) * vel, t0 + i * step_t, pan=-0.2)
M = [392.0, 440.0, 523.3, 440.0]   # 주제 동기(솔·라·도·라)

# ---- C5 장 ----
for k in range(6): put(step(0.12), at('C5', 0.05 + k * 0.22), pan=0.3)
put(thump(0.35, 110), at('C5', 2.15)); put(breath(0.6, 0.1, (300, 1200)), at('C5', 2.2))
t = tt(3.6); put(lp(rng.normal(0, 1, len(t)), 300) * 0.05 * np.clip(t / 0.8, 0, 1) + np.sin(2 * np.pi * (60 + 20 * np.clip(t / 0.8, 0, 1)) * t) * 0.04, at('C5', 2.4))   # 벨트 모터
put(glide(300, 900, 0.25, 0.15), at('C5', 3.05)); put(mallet(1046.5, 0.5, 0.12), at('C5', 3.3))
hum([523.3, 587.3, 659.3, 587.3, 523.3, 659.3, 784.0, 659.3, 587.3, 523.3], at('C5', 0.4), 0.45, 0.06)
for i, f in enumerate([392, 494, 587, 494] * 3): put(mallet(f, 0.5, 0.09), at('C5', 0.2 + i * 0.45), pan=0.2)
# ---- C6 간: 갈색 병을 깔때기에 붓다 지침 → 심장을 보고 반가운 인사 ----
def glug(d, vel=0.07):   # 끈적한 액체가 꿀렁꿀렁 떨어지는 소리
    t = tt(d); x = np.zeros_like(t)
    for k in range(int(d * 7)): t0 = k / 7 + rng.uniform(0, 0.05); i = int(t0 * SR); seg = tt(0.09); b = np.sin(2 * np.pi * np.cumsum(220 + 380 * seg / 0.09) / SR) * np.exp(-seg * 35); x[i:i + len(seg)] += b[:max(0, min(len(seg), len(x) - i))]
    return lp(x, 1600) * vel
put(glug(2.3, 0.08), at('C6', 0.05), pan=-0.15)
for k in range(14): put(plip(0.06), at('C6', 0.2 + k * 0.42 + 0.05 * (k % 3)), pan=-0.4 + 0.1 * (k % 4))
for k in range(8): put(step(0.1), at('C6', 0.05 + k * 0.22), pan=0.4)
put(breath(1.0, 0.13, (250, 1000)), at('C6', 1.15), pan=-0.2)                 # 간의 한숨
put(glide(500, 900, 0.18, 0.12), at('C6', 2.45), pan=-0.2); put(mallet(1046.5, 0.6, 0.13), at('C6', 2.65)); put(mallet(1318.5, 0.6, 0.11), at('C6', 2.78))   # 알아봄·반가움
for k in range(4): put(glide(700 + 60 * k, 900 + 60 * k, 0.1, 0.05), at('C6', 2.95 + k * 0.23), pan=-0.2)   # 손 흔드는 경쾌한 소리
put(glide(600, 760, 0.15, 0.08), at('C6', 3.0), pan=0.3)
for k in range(9): put(step(0.1), at('C6', 3.95 + k * 0.22), pan=0.1 - 0.06 * k)
for i, f in enumerate([349.2, 329.6, 293.7, 329.6, 392.0, 440.0, 523.3]): put(piano(f, 1.3, 0.08), at('C6', 0.3 + i * 0.8))
# ---- C7 뇌: 꾸벅꾸벅 졸며 꿈(DREAM·해변)이 보드에 번짐 → 심장 피식 ----
for k in range(5): put(breath(0.7, 0.07, (120, 500)), at('C7', 0.3 + k * 1.2), pan=0.3)   # 코골이
for k in range(10): put(beep(1800 + 300 * (k % 3), 0.05, 0.02), at('C7', 0.3 + k * 0.57), pan=0.5 - 0.1 * k)
for i in range(10): put(celesta([1046.5, 1174.7, 1318.5, 1568.0, 1760.0, 1568.0, 1318.5, 1174.7, 1046.5, 1318.5][i], 1.0, 0.06), at('C7', max(0, (i + 1) / 10 - 0.12) * 4.2 + 0.05), pan=0.45)   # 꿈 그림이 하나씩 번질 때 반짝
for k in range(8): put(step(0.1), at('C7', 0.05 + k * 0.25), pan=-0.3)
put(mallet(1318.5, 0.5, 0.11), at('C7', 1.6)); put(breath(0.22, 0.09, (600, 2500)), at('C7', 3.12)); put(glide(500, 650, 0.12, 0.06), at('C7', 3.14))   # 피식
for k in range(8): put(tiptoe(0.08), at('C7', 4.0 + k * 0.24), pan=-0.4)
put(pad([261.6, 329.6, 392.0, 493.9], 6.0, 0.06, 1.5), at('C7', 0.0))
for i, f in enumerate([523.3, 659.3, 784.0, 659.3, 587.3, 523.3]): put(celesta(f, 1.2, 0.07), at('C7', 0.4 + i * 0.9))
# ---- C8a 관 끝이 환해지며 바다와 휴가지 → 통통 ----
def waves(d, vel=0.05):   # 잔잔한 파도(느리게 밀려왔다 빠지는 잡음)
    t = tt(d); return lp(rng.normal(0, 1, len(t)), 900) * (0.6 + 0.4 * np.sin(2 * np.pi * t / 5.5) ** 2) * vel * np.clip(t / 1.0, 0, 1) * np.clip((d - t) / 1.0, 0, 1)
for k in range(8): put(step(0.11), at('C8a', 0.05 + k * 0.21), pan=0.2)
put(waves(12.5, 0.06), at('C8a', 0.6))
t = tt(2.2); put(lp(rng.normal(0, 1, len(t)), 2500) * np.clip(t / 1.4, 0, 1) * np.clip((2.2 - t) / 0.4, 0, 1) * 0.05, at('C8a', 0.2))   # 관 끝 빛이 밀려오는 쏴아
put(pad([392.0, 493.9, 587.3, 784.0], 4.8, 0.12, 1.2), at('C8a', 1.4))
for i, f in enumerate([784.0, 987.8, 1174.7, 1568.0]): put(celesta(f, 1.4, 0.12), at('C8a', 1.65 + i * 0.07), pan=0.2)
for k in range(7): put(glide(330 + 40 * (k % 3), 620 + 40 * (k % 3), 0.12, 0.08), at('C8a', 2.15 + k * 0.45), pan=0.1); put(step(0.08), at('C8a', 2.15 + k * 0.45 + 0.43))   # 통통
for i, f in enumerate([523.3, 587.3, 659.3, 784.0, 659.3, 784.0, 880.0]): put(mallet(f, 0.5, 0.1), at('C8a', 2.2 + i * 0.4), pan=0.2)
# ---- C8 창가(자장가) ----
for k in range(2): put(breath(3.6, 0.07, (200, 900)), at('C8', 0.2 + k * 4.0))
for k in range(9): put(step(0.1), at('C8', 0.05 + k * 0.24), pan=-0.3)
put(whoosh(0.5, 400, 1200, 0.12), at('C8', 2.6)); put(creak(1.5, 0.05, 140), at('C8', 3.2)); put(breath(1.2, 0.12, (250, 900)), at('C8', 3.6))
lull = [523.3, 659.3, 784.0, 659.3, 698.5, 659.3, 587.3, 523.3]
for i, f in enumerate(lull): put(celesta(f, 2.0, 0.12), at('C8', 0.8 + i * 0.75), pan=-0.2 + 0.05 * i)
put(pad([261.6, 329.6, 392.0], 7.0, 0.1, 2.0), at('C8', 0.2))
# ---- C9 자동 펌프 퍽 ----
for t0 in np.arange(0.3, 2.95, 0.72): put(thump(0.75, 58), at('C9', t0)); put(clank(0.2, 300), at('C9', t0))
put(clank(0.5, 220), at('C9', 2.85)); put(boom(0.9), at('C9', 3.0)); put(whoosh(0.8, 3000, 600, 0.25), at('C9', 3.0))
for tb, v in [(3.62, 0.15), (3.9, 0.08), (4.05, 0.05)]: put(ping(2600, v), at('C9', tb), pan=0.3)
put(glide(330, 70, 1.6, 0.2), at('C9', 3.2))
for k in range(4): put(beep(880, 0.15, 0.1), at('C9', 3.5 + k * 0.4)); put(beep(660, 0.15, 0.1), at('C9', 3.7 + k * 0.4))
# ---- C10 창가: 숨이 멎고 깸 ----
put(breath(2.0, 0.07, (200, 900)), at('C10', 0.0))
for i, f in enumerate([523.3, 659.3, 784.0]): put(celesta(f * (1 - 0.03 * i), 1.6, 0.1 - 0.025 * i), at('C10', 0.2 + i * 0.75))
put(pad([130.8, 155.6, 196.0], 2.5, 0.08, 0.8), at('C10', 1.6))
put(glide(1200, 2400, 0.15, 0.12), at('C10', 2.45)); put(whoosh(0.5, 500, 2500, 0.18), at('C10', 2.85)); put(thump(0.5, 120), at('C10', 3.5))
for k in range(8): put(step(0.16), at('C10', 4.35 + k * 0.17), pan=-0.3)
# ---- C11 복도 + 쓰러지는 동료들 ----
put(pad([110.0, 116.5, 164.8], 8.0, 0.12, 0.6), at('C11a', 0.0))
for k in range(int(2.0 / 0.16)): put(step(0.15), at('C11a', k * 0.16), pan=0.2)
for i in range(4): put(beep(660, 0.12, 0.06), at('C11a', 0.3 + i * 0.5))
t = tt(1.2); put(lp(rng.normal(0, 1, len(t)), 300) * 0.06 * np.exp(-t * 2.5) + np.sin(2 * np.pi * np.cumsum(80 - 50 * t) / SR) * 0.05 * np.exp(-t * 2), at('C11b', 0.1))   # 벨트 멈춤
put(thump(0.3, 140), at('C11b', 0.55)); put(creak(1.0, 0.06, 90), at('C11c', 0.1)); put(thump(0.3, 130), at('C11c', 0.6))
put(glide(900, 120, 0.9, 0.1), at('C11d', 0.2)); put(thump(0.25, 150), at('C11d', 0.5))
for k in range(int(1.2 / 0.16)): put(step(0.15), at('C11e', k * 0.16), pan=-0.2)
# ---- C12 굳은 발판 ----
for k in range(10): put(beep(880, 0.15, 0.07), at('C12', 0.2 + k * 0.85)); put(beep(660, 0.15, 0.07), at('C12', 0.4 + k * 0.85))
for k in range(int(2.5 / 0.16)): put(step(0.15), at('C12', k * 0.16), pan=0.3)
put(whoosh(0.5, 400, 1800, 0.15), at('C12', 2.9)); put(thump(0.6, 150), at('C12', 3.45)); put(glide(400, 250, 0.3, 0.1), at('C12', 3.55))
put(whoosh(0.7, 400, 2200, 0.18), at('C12', 4.5)); put(thump(0.8, 140), at('C12', 5.25)); put(glide(350, 180, 0.5, 0.12), at('C12', 5.35))
for i, f in enumerate([523.3, 466.2, 392.0, 349.2, 311.1]): put(piano(f, 2.0, 0.12), at('C12', 6.0 + i * 0.55))
for k in range(3): put(breath(0.25, 0.08, (500, 2500)), at('C12', 6.6 + k * 0.7))
# ---- C13 휴가권을 걸고 ----
put(hp(rng.normal(0, 1, int(0.25 * SR)), 1500) * np.linspace(0.08, 0, int(0.25 * SR)), at('C13', 1.0))   # 종이 떼는 소리
for i, f in enumerate([392.0, 440.0, 523.3, 440.0]): put(piano(f, 2.4, 0.13), at('C13', 1.4 + i * 0.6))   # 주제 동기를 느리게
for k in range(6): put(step(0.15), at('C13', 2.8 + k * 0.15), pan=-0.3)
put(whoosh(0.4, 500, 1600, 0.12), at('C13', 3.6)); put(ping(3200, 0.1), at('C13', 3.9)); put(mallet(784.0, 0.8, 0.12), at('C13', 4.0))
for k in range(6): put(step(0.15), at('C13', 4.35 + k * 0.15), pan=0.3)
put(pad([196.0, 246.9, 293.7], 2.0, 0.1, 1.0), at('C13', 4.2)); put(whoosh(0.7, 300, 3000, 0.25), at('C13', 5.35))
# ---- C14 쿵! 박동이 돌아옴 ----
put(thump(1.0, 50), at('C14', 0.0)); put(boom(0.5), at('C14', 0.0))
put(organ([261.6, 329.6, 392.0, 523.3], 4.0, 0.2, 0.15), at('C14', 0.05)); put(organ([349.2, 440.0, 523.3, 698.5], 3.0, 0.16, 0.3), at('C14', 4.0))
for i, f in enumerate([523.3, 659.3, 784.0, 1046.5, 1318.5, 1568.0]): put(mallet(f, 1.2, 0.16), at('C14', 0.1 + i * 0.09), pan=-0.5 + 0.2 * i)
for t0 in np.arange(0.72, 8.0, 0.72): put(thump(0.85), at('C14', t0)); put(lub(0.35), at('C14', t0 + 0.22))
for k, t0 in enumerate(np.arange(1.4, 8.0, 0.72 * 4)):
    for i, f in enumerate(M): put(mallet(f * 2, 0.9, 0.14), at('C14', t0 + i * 0.72), pan=0.2)
# ---- C15 복도에서 손 흔들기 ----
for i, tdoor in enumerate([0.4, 1.2, 2.0]): put(creak(0.6, 0.06, 200 + 40 * i), at('C15a', tdoor)); put(mallet([659.3, 784.0, 987.8][i], 0.8, 0.14), at('C15a', tdoor + 0.5), pan=-0.4 + 0.4 * i)
put(pad([261.6, 329.6, 392.0], 5.0, 0.1, 1.0), at('C15a', 0.0))
for i, f in enumerate(M + [523.3]): put(celesta(f * 2, 1.5, 0.12), at('C15a', 2.6 + i * 0.45))
for t0 in np.arange(0.2, 3.0, 0.72): put(thump(0.7), at('C15b', t0))
for i, f in enumerate([1046.5, 1318.5, 1568.0]): put(mallet(f, 1.0, 0.14), at('C15b', 0.6 + i * 0.08))
for i in range(3): put(mallet([784.0, 880.0, 1046.5][i], 0.9, 0.14), at('C15c', 0.1 + i * 0.15), pan=-0.3 + 0.3 * i)
put(pad([349.2, 440.0, 523.3], 2.2, 0.1, 0.5), at('C15c', 0.0))
# ---- C16 밤, 손, 쉼 ----
lands = []; t0 = 0.3
while t0 < 12.0:
    lands.append(t0); u = min(1, max(0, (t0 - 2) / 4)); u = u * u * (3 - 2 * u); t0 += 0.9 + 0.8 * u
for l in lands: put(thump(0.55, 55), at('C16', l)); put(lub(0.2), at('C16', l + 0.25))
put(pad([174.6, 220.0, 261.6, 349.2], 9.0, 0.14, 3.0), at('C16', 1.2))
for i, f in enumerate([392.0, 440.0, 523.3, 440.0, 392.0, 329.6, 392.0]): put(celesta(f, 2.6, 0.12), at('C16', 4.5 + i * 1.05))
# ---- 타이틀 ----
for k, tb in enumerate([0.4, 2.2]): put(thump(0.6, 52), at('TITLE', tb)); put(lub(0.25), at('TITLE', tb + 0.28))
put(celesta(523.3, 4.0, 0.12), at('TITLE', 3.6)); put(celesta(392.0, 4.0, 0.1), at('TITLE', 3.62)); put(pad([130.8, 196.0, 261.6], 4.4, 0.08, 1.5), at('TITLE', 3.4))

# C1–C4
with wave.open(sys.argv[1]) as w:
    a = np.frombuffer(w.readframes(w.getnframes()), np.int16).reshape(-1, 2).astype(np.float64) / 32767
k = min(len(a), n); L[:k] += a[:k, 0] / 0.85 * 0.6; R[:k] += a[:k, 1] / 0.85 * 0.6
# 바탕 공장 웅웅(펌프 공장 컷에서만)
amb = lp(rng.normal(0, 1, n), 180) * 0.04
for c in ('C9', 'C12', 'C13', 'C14', 'C15b', 'C16'):
    s0, d = CUT[c]; i0, i1 = int(s0 * SR), int((s0 + d) * SR); g = 0.4 if c in ('C12', 'C13') else 1.0; L[i0:i1] += amb[i0:i1] * g; R[i0:i1] += amb[i0:i1] * g
mx = max(np.abs(L).max(), np.abs(R).max()); L, R = L / mx * 0.85, R / mx * 0.85
with wave.open(sys.argv[2], 'w') as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes((np.stack([L, R], 1) * 32767).astype(np.int16).tobytes())
print('ok', DUR)
