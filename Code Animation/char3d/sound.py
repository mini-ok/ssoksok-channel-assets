"""연기 샘플 1 임시 효과음(합성). 부드러운 음색(저역 통과) — 사용: python3 sound.py out.wav"""
import sys, wave, numpy as np
from scipy.signal import butter, lfilter
SR, DUR = 44100, 5.5
n = int(DUR * SR); L = np.zeros(n); R = np.zeros(n); rng = np.random.default_rng(3)
def lp(x, f): b, a = butter(2, f / (SR / 2)); return lfilter(b, a, x)
def bp(x, f0, f1): b, a = butter(2, [f0 / (SR / 2), f1 / (SR / 2)], 'band'); return lfilter(b, a, x)
def put(x, t, g=1.0, pan=0.0):
    i = int(t * SR); j = min(n, i + len(x)); x = x[:j - i] * g
    L[i:j] += x * (1 - pan) * 0.7; R[i:j] += x * (1 + pan) * 0.7
def env(m, a=0.01, r=0.05): tt = np.arange(m) / SR; d = m / SR; return np.clip(tt / a, 0, 1) * np.clip((d - tt) / r, 0, 1)
def glide(f0, f1, dur, vel=0.3, vib=0.0, vr=30):       # 미끄러지는 음(고무 같은 늘어남)
    m = int(dur * SR); tt = np.arange(m) / SR; f = f0 * (f1 / f0) ** (tt / dur) * (1 + vib * np.sin(2 * np.pi * vr * tt))
    ph = 2 * np.pi * np.cumsum(f) / SR; return lp((np.sin(ph) + 0.25 * np.sin(2 * ph)) * env(m, 0.02, 0.06), 2500) * vel
def mallet(f, dur=0.9, vel=0.3):                         # 마림바풍 둥근 음
    m = int(dur * SR); tt = np.arange(m) / SR
    return lp((np.sin(2 * np.pi * f * tt) + 0.3 * np.sin(2 * np.pi * f * 4 * tt) * np.exp(-tt * 18)) * np.exp(-tt * 5) * np.clip(tt / 0.004, 0, 1), 3000) * vel
def thud(vel=0.5):
    m = int(0.25 * SR); tt = np.arange(m) / SR
    return (np.sin(2 * np.pi * np.cumsum(120 * np.exp(-tt * 14) + 45) / SR) * np.exp(-tt * 16) + lp(rng.normal(0, 1, m), 500) * np.exp(-tt * 40) * 0.4) * vel
def breath(dur, vel=0.12, f=(300, 1400)):
    m = int(dur * SR); tt = np.arange(m) / SR; return bp(rng.normal(0, 1, m), *f) * np.sin(np.pi * tt / dur) ** 1.5 * vel
put(glide(260, 190, 0.22, 0.2), 0.62)                                  # 웅크림
put(glide(220, 520, 0.3, 0.26), 0.8, pan=0.2)                          # 쭉 뻗기
put(glide(520, 560, 0.42, 0.14, vib=0.03, vr=22), 1.06, pan=0.2)       # 버티며 떨림
put(glide(300, 200, 0.12, 0.2), 1.44)                                  # 점프 준비
put(breath(0.4, 0.14, (500, 2500)), 1.56); put(glide(280, 700, 0.2, 0.2), 1.56)   # 도약
put(glide(700, 380, 0.2, 0.12), 1.78)
put(thud(0.55), 1.98); put(glide(240, 150, 0.2, 0.16), 2.0)            # 착지
put(breath(0.75, 0.16, (250, 1100)), 2.3); put(glide(330, 196, 0.6, 0.13), 2.3)   # 한숨
put(mallet(587, 0.4, 0.16), 3.35, pan=-0.3); put(mallet(784, 0.5, 0.18), 3.52, pan=-0.3)   # 어? 알아챔
put(glide(240, 180, 0.15, 0.16), 3.8)
for i, f in enumerate([784, 988, 1175]): put(mallet(f, 1.2, 0.22), 4.04 + i * 0.07, pan=-0.2 + 0.2 * i)   # "아!"
put(thud(0.2), 4.32)
mx = max(np.abs(L).max(), np.abs(R).max()); L, R = L / mx * 0.8, R / mx * 0.8
with wave.open(sys.argv[1], 'w') as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes((np.stack([L, R], 1) * 32767).astype(np.int16).tobytes())
