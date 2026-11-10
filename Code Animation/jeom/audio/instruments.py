"""거문고·북 물리 모형 합성(샘플 없음). sketch.py의 사인 합(additive) 거문고보다 실제 악기에 가깝게:
- 거문고: 줄 = 디지털 도파관(Karplus-Strong 계열, 3탭 손실 필터로 명주실의 빠른 고음 감쇠),
  술대 타격 = 줄의 친 자리(술대 위치) 빗살 필터 + 대나무가 대모(가죽 덧댐)를 치는 소리,
  울림통 = 오동나무 판의 공명(모드 몇 개를 2차 공진 필터로),
  농현·퇴성 = 만든 소리를 시간축으로 다시 표본(음높이가 바뀌는 만큼 재생 속도를 바꿈).
- 북: 원형 막의 진동 모드(베셀 함수 근의 비율) + 친 직후 장력이 높았다 내려앉는 음높이 + 통 울림 + 북채 소리.
"""
import numpy as np
from scipy.signal import lfilter, butter

SR = 48000
_rng = np.random.default_rng(17)


def _band(n, lo, hi, seed=None):
    r = _rng if seed is None else np.random.default_rng(seed)
    b, a = butter(2, [lo / (SR / 2), min(0.99, hi / (SR / 2))], btype='band')
    return lfilter(b, a, r.standard_normal(n))


def _reson(x, f, q, g=1.0):
    """2차 공진 필터(울림통 모드 하나)."""
    w = 2 * np.pi * f / SR; r = np.exp(-w / (2 * q))
    b = [1 - r, 0, -(1 - r)]; a = [1, -2 * r * np.cos(w), r * r]
    return lfilter(b, a, x) * g


def _string(f0, dur, pos=0.13, dark=0.22, decay=5.5, seed=0, force=1.0):
    """도파관 줄 하나(고정 음높이). pos: 친 자리(줄 길이 비), dark: 손실 필터 옆탭 무게(0~0.25, 클수록 어둡다),
    decay: 기본음이 60dB 줄어드는 시간(초)."""
    n = int(dur * SR)
    Lf = SR / f0 - 1.0                                    # 3탭 대칭 필터의 지연 1샘플을 뺀다
    L = int(Lf); fr = Lf - L
    g = 10 ** (-3 / (decay * f0))                          # 한 바퀴당 감쇠
    # 들뜸: 술대가 줄을 내려친 짧은 힘(낮은 대역이 많은 잡음 + 꺾인 모양), 친 자리 빗살로 배음을 깎는다
    r = np.random.default_rng(seed)
    m = max(8, int(L * 0.9))
    ex = np.zeros(n)
    w = np.hanning(m) * (0.6 + 0.4 * r.standard_normal(m) * force)
    ex[:m] = lfilter([1.0], [1, -0.55 + 0.25 * (1 - force)], w)
    p = max(1, int(pos * L)); ex[p:] -= ex[:-p].copy()
    # 손실 필터(3탭) + 분수 지연(선형 보간): y[n] = ex[n] + g*(w1*y[n-L] + w0*y[n-L-1] + w1*y[n-L-2]) 를 보간
    w1, w0 = dark, 1 - 2 * dark
    taps = np.zeros(L + 4)
    for k, c in ((L, w1), (L + 1, w0), (L + 2, w1)):      # 지연 L의 세 탭을 fr만큼 뒤로 나눠 준다
        taps[k] += g * c * (1 - fr); taps[k + 1] += g * c * fr
    a = np.concatenate([[1.0], -taps[1:]])
    return lfilter([1.0], a, ex)


def _warp(x, f0, cents):
    """음높이 곡선(센트)만큼 재생 속도를 바꿔 다시 표본(농현·퇴성)."""
    rate = 2 ** (cents / 1200)
    pos = np.cumsum(rate) - rate[0]
    pos = pos[pos < len(x) - 1]
    i = pos.astype(int); fr = pos - i
    return x[i] * (1 - fr) + x[i + 1] * fr


_BODY = ((96, 9, 1.0), (178, 12, 0.7), (262, 14, 0.55), (390, 16, 0.4), (610, 18, 0.25), (930, 20, 0.15))


def body(x, amt=0.55):
    y = sum(_reson(x, f, q, g) for f, q, g in _BODY)
    return x * (1 - amt) + y * amt * 3.0


def geomungo(f0, dur=3.2, vel=1.0, nonghyeon=0.35, bend_end=0.0, pos=0.12, dark=0.20, decay=None, seed=None):
    """술대로 내려친 거문고 한 음. 타격 순간 음이 조금 높았다 내려앉고(+30센트), 0.35초 뒤부터 느린 농현."""
    seed = int(f0 * 10 + dur * 7) if seed is None else seed
    decay = decay if decay is not None else (6.5 if f0 < 90 else 4.5)
    pad = 0.5
    x = _string(f0, dur + pad, pos=pos, dark=dark, decay=decay, seed=seed, force=min(1.0, vel))
    n = int((dur + pad) * SR); t = np.arange(n) / SR
    cents = 30 * np.exp(-t / 0.06) + nonghyeon * 28 * np.sin(2 * np.pi * 4.0 * t + 0.3) * np.clip((t - 0.35) / 0.6, 0, 1) \
        + bend_end * np.clip((t - dur * 0.45) / (dur * 0.4), 0, 1)
    x = _warp(x, f0, cents)[:int(dur * SR)]
    n = len(x); t = np.arange(n) / SR
    # 괘(높은 받침)에 줄이 닿아 나는 거친 울림: 큰 진폭에서만 살짝 비틀린다
    x = x / (np.abs(x).max() + 1e-9)
    x = x + 0.12 * np.tanh(3 * x) * np.exp(-t / 0.4)
    # 술대가 대모를 치는 '딱' + 판의 '덕'
    k = int(0.03 * SR)
    hit = _band(k, 700, 4200, seed + 1) * np.exp(-np.arange(k) / SR / 0.004) * 0.9
    thud = _band(int(0.12 * SR), 60, 300, seed + 2) * np.exp(-np.arange(int(0.12 * SR)) / SR / 0.03) * 1.2
    x[:k] += hit; x[:len(thud)] += thud
    x = body(x)
    env = np.clip(t / 0.0015, 0, 1) * np.clip((dur - t) / 0.25, 0, 1)
    return 0.42 * vel * x * env / (np.abs(x).max() + 1e-9)


# 원형 막 모드: (베셀 근 비율, 세기, 감쇠 배율). 북 가죽에 공기가 실려 아래 모드는 조화음 쪽으로 당겨진다.
_MODES = ((1.00, 1.00, 1.0), (1.52, 0.55, 0.65), (1.98, 0.42, 0.50), (2.20, 0.30, 0.45), (2.48, 0.26, 0.38),
          (2.78, 0.20, 0.32), (3.02, 0.16, 0.28), (3.38, 0.12, 0.24), (3.60, 0.10, 0.22), (4.10, 0.07, 0.18))


def buk(amp=0.6, f0=62.0, dur=1.4, decay=0.42, strike=0.35, seed=None):
    """북 한 번. strike: 가장자리 쪽으로 칠수록(0 → 1) 높은 모드가 살아난다."""
    seed = int(f0 * 13 + amp * 100) if seed is None else seed
    r = np.random.default_rng(seed)
    n = int(dur * SR); t = np.arange(n) / SR
    glide = 1 + 0.22 * amp * np.exp(-t / 0.07)                   # 세게 칠수록 처음 음이 높다
    y = np.zeros(n)
    for k, (ratio, g, dk) in enumerate(_MODES):
        f = f0 * ratio * glide * (1 + r.normal(0, 0.004))
        ph = 2 * np.pi * np.cumsum(f) / SR + r.uniform(0, 6.28)
        gg = g * (1.0 if k == 0 else (0.35 + strike) ** (0.5 + 0.15 * k))
        y += gg * np.sin(ph) * np.exp(-t / (decay * dk))
    # 북채가 가죽에 닿는 소리 + 통 안의 공기 울림
    k = int(0.04 * SR)
    stick = _band(k, 150, 2500, seed + 3) * np.exp(-np.arange(k) / SR / (0.006 + 0.004 * (1 - amp)))
    y[:k] += 0.9 * stick
    shell = _reson(_band(n, 80, 900, seed + 4) * np.exp(-t / 0.05), f0 * 2.6, 6, 1.0)
    y += 0.5 * shell / (np.abs(shell).max() + 1e-9) * np.exp(-t / 0.18)
    y *= np.clip(t / 0.0008, 0, 1) * np.clip((dur - t) / 0.12, 0, 1)
    return amp * y / (np.abs(y).max() + 1e-9)


def daehyeon(amp=0.8, dur=4.0, scrape_=0.0, f0=55.0):
    """거문고 대현(가장 굵은 줄): 낮고 두꺼운 음 + 술대로 긁는 소리(술대를 줄에 댄 채 밀어냄)."""
    x = geomungo(f0, dur, amp, nonghyeon=0.25, dark=0.17, pos=0.10, decay=7.0)
    if scrape_ > 0:
        n = len(x); t = np.arange(n) / SR
        sc = _band(n, 140, 1100) * np.exp(-t / 0.22) * (1 + 0.6 * np.sin(2 * np.pi * 37 * t))
        x = x + sc * scrape_ * 0.5
    return x
