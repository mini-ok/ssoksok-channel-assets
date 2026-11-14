"""〈심장의 휴가〉 C1–C4 임시 소리(합성). 타이밍은 act1.js와 같은 값. 사용: python3 sound_a1.py out.wav"""
import sys, wave, numpy as np
from scipy.signal import butter, lfilter
SR, DUR = 44100, 32.0
n = int(DUR * SR); L = np.zeros(n); R = np.zeros(n); rng = np.random.default_rng(5)
def lp(x, f): b, a = butter(2, f / (SR / 2)); return lfilter(b, a, x)
def hp(x, f): b, a = butter(2, f / (SR / 2), 'high'); return lfilter(b, a, x)
def bp(x, f0, f1): b, a = butter(2, [f0 / (SR / 2), f1 / (SR / 2)], 'band'); return lfilter(b, a, x)
def put(x, t, g=1.0, pan=0.0):
    i = int(t * SR)
    if i >= n or i + len(x) <= 0: return
    if i < 0: x = x[-i:]; i = 0
    j = min(n, i + len(x)); x = x[:j - i] * g
    L[i:j] += x * (1 - pan) * 0.7; R[i:j] += x * (1 + pan) * 0.7
tt = lambda d: np.arange(int(d * SR)) / SR
def env(d, a=0.005, r=0.05): t = tt(d); return np.clip(t / a, 0, 1) * np.clip((d - t) / r, 0, 1)
def thump(vel=1.0, f=62):        # 쿵(심장이 발판을 밟음): 낮은 북 + 풀무 바람
    t = tt(0.45); body = np.sin(2 * np.pi * np.cumsum(f + 90 * np.exp(-t * 30)) / SR) * np.exp(-t * 9)
    air = bp(rng.normal(0, 1, len(t)), 200, 900) * np.exp(-t * 14) * 0.25
    return lp(body + air, 1200) * vel
def lub(vel=0.5):                # 박동 둘째 소리(두근의 "근")
    t = tt(0.25); return lp(np.sin(2 * np.pi * 85 * t) * np.exp(-t * 22), 900) * vel
def clank(vel=0.6, f=380):       # 쇠 부딪힘
    t = tt(0.5); x = sum(np.sin(2 * np.pi * f * k * t + k) * np.exp(-t * (8 + 6 * k)) for k in (1, 2.76, 5.4)); return hp(x, 200) * vel
def mallet(f, d=1.0, vel=0.25):
    t = tt(d); return lp((np.sin(2 * np.pi * f * t) + 0.3 * np.sin(2 * np.pi * f * 4 * t) * np.exp(-t * 18)) * np.exp(-t * 4.5) * np.clip(t / 0.004, 0, 1), 3200) * vel
def organ(freqs, d, vel=0.12, att=0.4):   # 오르간 파이프(부드러운 화음)
    t = tt(d); x = sum(np.sin(2 * np.pi * f * t) + 0.35 * np.sin(4 * np.pi * f * t) + 0.12 * np.sin(6 * np.pi * f * t) for f in freqs)
    return lp(x * np.clip(t / att, 0, 1) * np.clip((d - t) / 0.6, 0, 1), 2500) * vel / len(freqs)
def whoosh(d=0.4, f0=300, f1=2000, vel=0.2):
    t = tt(d); x = rng.normal(0, 1, len(t)); out = np.zeros_like(x)
    for k, (a, b) in enumerate(zip(np.linspace(f0, f1, 6)[:-1], np.linspace(f0, f1, 6)[1:])): seg = slice(k * len(t) // 5, (k + 1) * len(t) // 5); out[seg] = bp(x, min(a, b), max(a, b))[seg]
    return out * np.sin(np.pi * t / d) * vel
def glide(f0, f1, d, vel=0.2):
    t = tt(d); f = f0 * (f1 / f0) ** (t / d); return lp(np.sin(2 * np.pi * np.cumsum(f) / SR) * env(d, 0.02, 0.06), 2500) * vel
def step(vel=0.12):   # 말랑한 발소리
    t = tt(0.12); return lp(np.sin(2 * np.pi * np.cumsum(180 - 600 * t) / SR) * np.exp(-t * 40), 1500) * vel

P = 0.72
rngs = lambda a, b: list(np.arange(a, b - 1e-6, P))
LANDS = rngs(0.5, 19.9) + rngs(21.62, 23.8)
AUTO = rngs(28.05, 32)
for k, t in enumerate(LANDS): put(thump(0.9 if t > 1 else 0.6), t); put(lub(0.35), t + 0.22)
for t in AUTO: put(thump(0.8, 58), t); put(clank(0.22, 300), t); put(lub(0.3), t + 0.22)
# C1: 박동마다 전구가 켜짐 — 작은 "팅"이 하나씩(점점 높아짐)
for k, t in enumerate(LANDS[:8]): put(mallet(523.3 * 2 ** (k / 12 * 2), 0.6, 0.12), t + 0.03, pan=-0.5 + k * 0.13)
# 오르간: 박동마다 화음 한 숨(C1 끝~C2), 어두울 때는 꺼짐
for t in [x for x in LANDS if 4.0 < x < 15]: put(organ([261.6, 329.6, 392.0], 0.65, 0.07, 0.05), t, pan=0.2)
# 음악: 마림바 동기 — 성실한 일상(C1·C2), 휴가권(반짝), 어둠(정적), 자동 펌프 작동(밝게), 걸어 나감(통통)
M = [392.0, 440.0, 523.3, 440.0]
for t0 in np.arange(5.8, 15.0, P * 4):
    for i, f in enumerate(M): put(mallet(f, 0.9, 0.16), t0 + i * P, pan=-0.2)
put(organ([220.0, 261.6, 329.6], 1.6, 0.12, 0.6), 13.0)                       # 포스터를 볼 때 그리움
# 상자: 휙 + 투입구 속 "뽀옹"
put(whoosh(0.35, 400, 1600, 0.15), 8.05, pan=0.4); put(glide(600, 180, 0.3, 0.18), 8.55, pan=0.4)
# 캡슐: 관 속 "슈우욱" + 받침에 "탁"
put(whoosh(0.5, 2500, 500, 0.25), 15.6, pan=0.4); put(clank(0.35, 700), 16.1, pan=0.4)
put(glide(400, 900, 0.18, 0.15), 16.75, pan=0.4)                               # 뚜껑 퐁
for i, f in enumerate([1046.5, 1318.5, 1568.0, 2093.0]): put(mallet(f, 1.2, 0.16), 16.95 + i * 0.07, pan=0.2)   # 휴가권 반짝
for t0 in [17.6, 18.32, 19.04]:
    for i, f in enumerate([523.3, 659.3]): put(mallet(f, 0.5, 0.12), t0 + i * 0.18)   # 들뜬 고민
# 내려섬 → 어두워짐: 전원 내려가는 소리 + 정적, 다시 올라감
put(step(0.2), 20.3); put(glide(330, 110, 1.0, 0.22), 20.45); put(glide(220, 70, 1.2, 0.12), 20.6)
put(whoosh(0.3, 500, 2500, 0.15), 21.05); put(mallet(784, 0.8, 0.12), 21.7)
# 자동 펌프 발견 → 내려서 달려감(어두워짐) → 밀기(바퀴 끼익)
for i, f in enumerate([659.3, 784.0, 987.8]): put(mallet(f, 0.6, 0.15), 22.8 + i * 0.09, pan=-0.3)
put(step(0.2), 24.45); put(glide(330, 100, 1.4, 0.2), 24.5)
for t in np.arange(24.5, 25.35, 0.13): put(step(0.13), t, pan=-0.4)
t = tt(1.5); put(lp(np.sin(2 * np.pi * (900 + 120 * np.sin(t * 9)) * t) * 0.05 * np.sin(np.pi * t / 1.5), 2500), 25.35, pan=-0.4)   # 바퀴 끼익
for tt0 in np.arange(25.35, 26.85, 0.17): put(step(0.1), tt0, pan=-0.4)
# 첫 누름 덜컹 걸림(27.0~27.6) → 발차기 "통" → 작동
put(clank(0.5, 250), 27.25); t = tt(0.35); put(hp(rng.normal(0, 1, len(t)) * np.exp(-t * 6), 1500) * 0.08 * (np.sin(t * 2 * np.pi * 30) > 0), 27.25)
put(clank(0.6, 180), 27.85); put(thump(0.4, 120), 27.85)
for i, f in enumerate([523.3, 659.3, 784.0, 1046.5]): put(mallet(f, 1.0, 0.2), 28.1 + i * 0.1, pan=0.0)
put(organ([261.6, 329.6, 392.0, 523.3], 2.4, 0.16, 0.3), 28.1)
# 기쁨 깡충 + 걸어 나감(통통한 발소리, 경쾌한 동기)
put(glide(400, 800, 0.2, 0.15), 28.5); put(step(0.18), 28.85)
for tt0 in np.arange(29.05, 32, 0.36): put(step(0.14), tt0, pan=0.3)
for t0 in np.arange(29.0, 32, P * 2):
    for i, f in enumerate([523.3, 659.3, 784.0, 659.3]): put(mallet(f, 0.4, 0.14), t0 + i * P / 2, pan=0.1)
# 공장 바탕 소리: 낮은 웅웅(어두울 때 줄어듦)
amb = lp(rng.normal(0, 1, n), 180) * 0.05; level = np.ones(n)
for a, b2 in [(20.2, 21.6), (24.4, 28.05)]: i0, i1 = int(a * SR), int(b2 * SR); level[i0:i1] = 0.25
level = lp(level, 4); L += amb * level; R += amb * level
mx = max(np.abs(L).max(), np.abs(R).max()); L, R = L / mx * 0.85, R / mx * 0.85
with wave.open(sys.argv[1], 'w') as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes((np.stack([L, R], 1) * 32767).astype(np.int16).tobytes())
print('ok')
