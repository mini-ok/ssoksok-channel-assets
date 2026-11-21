"""후처리 사슬(numpy, BGR float 0..1). 순서 고정: 노출 → 톤 매핑 → 채도 → 분할 톤 → S 곡선 → 비네트 → 결.
(출처: Fable 5.2 화제작 분석 — 18위·28위의 고정 후처리 순서. 수치 기본값은 우리 종이 화면에 맞춰 약하게 잡음.)

    out = grade(img, exposure=0.0, tonemap=None, sat=1.05, split=((0.06,0.02,-0.02),(-0.02,0.01,0.05),0.5),
                s_curve=0.15, vignette=0.12, grain=0.008, seed=frame_index)
    img = subframes(lambda tt: render(tt), t, fps=30, n=8, shutter=0.5)   # 하위 프레임 평균 = AA + 모션 블러
"""
import numpy as np

_LUMA = np.array([0.114, 0.587, 0.299], np.float32)   # BGR


def aces(x):
    a, b, c, d, e = 2.51, 0.03, 2.43, 0.59, 0.14
    return np.clip((x * (a * x + b)) / (x * (c * x + d) + e), 0, 1)


def agx_like(x):
    """AgX 느낌의 부드러운 어깨(정식 AgX 변환은 아님: 로그 압축 + 시그모이드)."""
    x = np.maximum(x, 1e-6)
    l = np.clip((np.log2(x) + 12.47) / 16.5, 0, 1)
    return np.clip(l * l * (3 - 2 * l), 0, 1) ** 1.6


def grade(img, exposure=0.0, tonemap=None, sat=1.0, split=None, s_curve=0.0, vignette=0.0, grain=0.0, seed=0):
    x = img.astype(np.float32)
    if exposure: x = x * (2.0 ** exposure)
    if tonemap == 'aces': x = aces(x)
    elif tonemap == 'agx': x = agx_like(x)
    else: x = np.clip(x, 0, 1)
    luma = (x @ _LUMA)[..., None]
    if sat != 1.0: x = luma + (x - luma) * sat
    if split:                                   # ((그늘 RGB 치우침), (밝은 곳 RGB 치우침), 세기)
        sh, hi, amt = split
        sh = np.array(sh[::-1], np.float32); hi = np.array(hi[::-1], np.float32)
        w = luma * luma * (3 - 2 * luma)
        x = x + amt * ((1 - w) * sh + w * hi)
    if s_curve:
        s = np.clip(x, 0, 1); x = s + s_curve * (s * s * (3 - 2 * s) - s)
    if vignette:
        h, w_ = x.shape[:2]
        yy, xx = np.mgrid[0:h, 0:w_].astype(np.float32)
        r = np.hypot((xx - w_ / 2) / (w_ / 2), (yy - h / 2) / (h / 2))
        x = x * (1 - vignette * np.clip(r - 0.55, 0, 1) ** 1.4)[..., None]
    if grain:
        rng = np.random.default_rng(seed)
        x = x + rng.normal(0, grain, x.shape[:2]).astype(np.float32)[..., None]
    return np.clip(x, 0, 1)


def subframes(render, t, fps=30, n=8, shutter=0.5):
    """프레임 하나를 n개 하위 시각의 평균으로(셔터 0.5 = 180°). render(t)->float 이미지."""
    acc = None
    for i in range(n):
        tt = t + ((i + 0.5) / n - 0.5) * shutter / fps
        f = render(tt).astype(np.float32)
        acc = f if acc is None else acc + f
    return acc / n


def flash_dip(t, t_flash, dip=-0.28, lead=0.10, hold=0.11):
    """섬광 직전 노출을 잠깐 낮췄다가 터뜨리는 노출 곡선(EV). 섬광 lead초 전부터 dip, 섬광 뒤 hold초에 재섬광 여지."""
    if t_flash - lead <= t < t_flash: return dip * (t - (t_flash - lead)) / lead
    if t_flash <= t < t_flash + hold: return 0.6 * (1 - (t - t_flash) / hold)
    return 0.0
