"""〈점〉 악기 스케치(약 33초): 거문고 = 점, 대금 = 용. 모두 numpy 합성(샘플 없음).

0~16초  빗소리 + 거문고 여섯 음: 점이 번질 때마다 한 음, 갈수록 낮고 여려짐(옅어짐)
16~20초 비가 그치고 정적, 섬유 당기는 소리 셋(규칙 깨기)
20~30초 대금: 낮게 시작해 부풀며 청이 떨기 시작(눈이 뜨임) → 높은 음에서 청이 크게 울림(용이 떠남) → 흘러내림
30~33초 거문고 낮은 한 음 + 대금 여운(남은 한 획)
"""
import numpy as np, wave, sys, os

SR = 48000
rng = np.random.default_rng(3)


def env_adsr(n, a, d, s, r_len):
    e = np.ones(n)
    A = int(a * SR); D = int(d * SR); R = int(r_len * SR)
    e[:A] = np.linspace(0, 1, A) if A else 1
    e[A:A + D] = np.linspace(1, s, max(1, len(e[A:A + D])))
    e[A + D:] = s
    if R:
        e[-R:] *= np.linspace(1, 0, R)
    return e


def bandnoise(n, lo, hi):
    x = rng.standard_normal(n)
    X = np.fft.rfft(x); f = np.fft.rfftfreq(n, 1 / SR)
    X[(f < lo) | (f > hi)] = 0
    return np.fft.irfft(X, n)


def lowpass(x, fc):
    a = np.exp(-2 * np.pi * fc / SR); y = np.empty_like(x); acc = 0.0
    for i in range(len(x)):
        acc = (1 - a) * x[i] + a * acc; y[i] = acc
    return y


def geomungo(f0, dur=3.2, vel=1.0, bend_end=0.0, nonghyeon=0.35):
    """술대로 내려친 대현. 타격 때 음이 살짝 높았다 내려앉고(+35센트→0), 0.4초 뒤부터 느린 농현,
    bend_end(센트)만큼 끝에서 흘러내림(퇴성). 명주실이라 고음 배음이 빨리 죽는다."""
    n = int(dur * SR); t = np.arange(n) / SR
    cents = 35 * np.exp(-t / 0.05)
    vib = nonghyeon * 30 * np.sin(2 * np.pi * 4.2 * t) * np.clip((t - 0.4) / 0.6, 0, 1)
    cents = cents + vib + bend_end * np.clip((t - dur * 0.45) / (dur * 0.4), 0, 1)
    f = f0 * 2 ** (cents / 1200)
    ph = 2 * np.pi * np.cumsum(f) / SR
    y = np.zeros(n)
    for k in range(1, 14):
        amp = (1 / k ** 1.15) * (1.0 if k != 4 else 0.6)
        dec = 1.6 / (1 + 0.55 * (k - 1) ** 1.3)
        y += amp * np.sin(k * ph * (1 + 0.0004 * k * k)) * np.exp(-t / dec)
    # 술대 타격: 대나무가 판을 치는 딱 소리 + 몸통 울림
    click = bandnoise(int(0.025 * SR), 900, 4500) * np.exp(-np.arange(int(0.025 * SR)) / SR / 0.004)
    thump = np.sin(2 * np.pi * 85 * t[:int(0.09 * SR)]) * np.exp(-t[:int(0.09 * SR)] / 0.025)
    y[:len(click)] += 0.9 * click
    y[:len(thump)] += 0.7 * thump
    # 오동나무 울림통: 짧은 잡음 임펄스 응답
    ir = bandnoise(int(0.06 * SR), 120, 2500) * np.exp(-np.arange(int(0.06 * SR)) / SR / 0.012)
    y = y + 0.25 * np.convolve(y, ir / np.abs(ir).sum() * 6, 'same')
    y *= env_adsr(n, 0.002, 0.0, 1.0, 0.25)
    return 0.5 * vel * y


def daegeum(notes, buzz_curve):
    """notes: [(시작, 길이, 주파수, 세기)] 이어진 한 숨의 선율. buzz_curve(t)->0..1 청 울림.
    가로 부는 대나무: 기음 강함 + 숨소리(배음에 걸린 잡음) + 청(7배음 이상이 떨며 커짐) + 농음(느린 비브라토)."""
    T = max(s + d for s, d, f, v in notes) + 0.6
    n = int(T * SR); t = np.arange(n) / SR
    f = np.zeros(n); amp = np.zeros(n)
    for (s, d, fr, v) in notes:
        i0, i1 = int(s * SR), int((s + d) * SR)
        f[i0:i1] = fr; amp[i0:i1] = v
    # 음 사이를 미끄러지듯(시김새), 숨의 크기는 천천히
    k = int(0.06 * SR); f = np.convolve(np.pad(f, (k, k), 'edge'), np.ones(2 * k + 1) / (2 * k + 1), 'same')[k:-k]
    k2 = int(0.18 * SR); amp = np.convolve(amp, np.ones(k2) / k2, 'same')
    f[f == 0] = f[f > 0].min() if (f > 0).any() else 440
    vib_depth = np.clip(amp, 0, 1) * 22 * np.clip(np.sin(np.pi * np.clip(t / T, 0, 1)) * 1.3, 0, 1)
    fv = f * 2 ** (vib_depth * np.sin(2 * np.pi * 5.0 * t + 0.3 * np.sin(2 * np.pi * 0.7 * t)) / 1200)
    ph = 2 * np.pi * np.cumsum(fv) / SR
    buzz = np.array([buzz_curve(x) for x in t[::480]]); buzz = np.interp(t, t[::480], buzz)
    y = np.zeros(n)
    for h in range(1, 16):
        a = [1.0, 0.45, 0.32, 0.18, 0.14, 0.09, 0.07, 0.06, 0.05, 0.045, 0.04, 0.035, 0.03, 0.025, 0.02][h - 1]
        if h >= 7:
            # 청: 높은 배음이 거칠게 떨며 커짐
            a = a * (1 + 6 * buzz * (0.6 + 0.4 * np.sign(np.sin(ph * 0.5 + h))))
        y += a * np.sin(h * ph)
    # 숨소리: 기음 근처에 걸린 대역 잡음 + 넓은 바람
    br = bandnoise(n, 300, 6000)
    br = br / np.abs(br).max()
    breath = br * (0.10 + 0.08 * (1 - buzz))
    y = y * amp + breath * np.clip(amp * 1.4, 0, 1)
    # 청의 비선형 떨림
    y = y + buzz * 0.35 * np.tanh(3 * np.diff(y, prepend=0) * 8)
    return 0.32 * y


def reverb(x, sec=2.6, mix=0.32):
    n = int(sec * SR)
    ir = rng.standard_normal(n) * np.exp(-np.arange(n) / SR / (sec / 6.9))
    ir = lowpass(ir, 5000)
    ir[:int(0.012 * SR)] = 0
    wet = np.fft.irfft(np.fft.rfft(x, len(x) + n) * np.fft.rfft(ir, len(x) + n))[:len(x)]
    wet = wet / (np.abs(wet).max() + 1e-9) * np.abs(x).max()
    return x * (1 - mix) + wet * mix


def rain(n, amount):
    base = bandnoise(n, 400, 9000) * 0.05
    hiss = bandnoise(n, 3000, 12000) * 0.03
    y = (base + hiss) * amount
    # 종이·창호에 떨어지는 굵은 방울
    m = int(n / SR * 7)
    for _ in range(m):
        i = rng.integers(0, n - 2000)
        if amount[i] < 0.05:
            continue
        d = bandnoise(1600, 1500, 7000) * np.exp(-np.arange(1600) / SR / 0.004)
        y[i:i + 1600] += d * 0.12 * amount[i]
    return y


def fiber_tug(n_len=0.5):
    """종이 섬유가 당겨지는 소리: 가속하는 미세한 크래클 + 낮은 신음."""
    n = int(n_len * SR); t = np.arange(n) / SR
    y = np.zeros(n)
    tt = 0.0
    while tt < n_len * 0.9:
        i = int(tt * SR)
        if i + 300 < n:
            y[i:i + 300] += bandnoise(300, 2000, 9000) * np.exp(-np.arange(300) / SR / 0.0015) * 0.5
        tt += 0.05 * (1 - tt / n_len) + 0.004
    y += 0.25 * np.sin(2 * np.pi * 70 * t) * np.exp(-t / 0.15) * np.clip(t / 0.02, 0, 1)
    return y * 0.4


def main(out):
    T = 33.0; n = int(T * SR); t = np.arange(n) / SR
    mix = np.zeros(n)
    amt = np.clip(t / 2.0, 0, 1) * (1 - np.clip((t - 15.0) / 2.5, 0, 1))
    mix += rain(n, amt)
    # 거문고: 점이 번질 때마다 한 음, 낮아지고 여려짐(5음 음계, 라-솔-미-레-도-라)
    steps = [(2.0, 220.0, 1.0), (5.4, 196.0, 0.85), (8.4, 164.8, 0.72), (11.0, 146.8, 0.6), (13.2, 130.8, 0.5), (14.8, 110.0, 0.4)]
    for (s, f0, v) in steps:
        g = geomungo(f0, 3.0, v, bend_end=-60 if s > 12 else 0)
        i = int(s * SR); mix[i:i + len(g)] += g[:n - i]
    # 정적 속 섬유 세 번
    for s in (17.2, 18.1, 19.0):
        g = fiber_tug(); i = int(s * SR); mix[i:i + len(g)] += g
    # 대금: 솔 → 라 → 레(높게, 청) → 도 → 라(흘러내림)
    notes = [(0.0, 3.0, 392.0, 0.55), (3.0, 1.4, 440.0, 0.7), (4.4, 3.2, 587.3, 1.0), (7.6, 1.0, 523.3, 0.75), (8.6, 2.4, 440.0, 0.5)]
    buzz = lambda x: float(np.clip((x - 1.5) / 3.0, 0, 1) * (1 - np.clip((x - 7.8) / 2.0, 0, 1)))
    d = daegeum(notes, buzz)
    i = int(20.0 * SR); mix[i:i + len(d)] += d[:n - i]
    # 끝: 거문고 낮은 한 음
    g = geomungo(110.0, 3.0, 0.8, nonghyeon=0.5)
    i = int(29.8 * SR); mix[i:i + len(g)] += g[:n - i]
    mix = reverb(mix)
    mix = mix / np.abs(mix).max() * 0.85
    mix = np.tanh(mix * 1.1) / np.tanh(1.1)
    st = np.stack([mix, np.roll(mix, int(0.0007 * SR))], 1)
    with wave.open(out, 'wb') as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((st * 32767).astype(np.int16).tobytes())


if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else 'jeom_instrument_sketch.wav')
