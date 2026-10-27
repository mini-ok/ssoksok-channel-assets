"""회상(되감기) 화면 효과 — 장면 fx에 "flashback"을 넣으면 그 조각의 프레임 전체에 적용된다 (2026-10-27, 사용자 지시:
'타임카드를 되감기하면 화면이 회상 느낌이 있었는데 그게 사라졌다 → 그대로 살려라').
효과: 따뜻한 세피아 톤 + 채도 낮춤, 부드러운 번짐(글로), 가장자리 비네트, 필름 입자, 가끔 흔들리는 세로 줄(필름 스크래치),
조각 시작 0.55초 동안 물결치듯 일렁이는 '되감기 리플'(점점 잦아듦).
apply(arr, lt, frame_no, rewind_label=None): arr = (H, W, 4) uint8 RGBA, lt = 이 조각 시작 후 경과 초.
"""
import numpy as np
from scipy import ndimage as ndi

RIPPLE = 0.55


def _blur(a, s):
    h, w = a.shape[:2]
    sm = a[::4, ::4].astype(np.float32)
    sm = np.stack([ndi.gaussian_filter(sm[..., i], s / 4) for i in range(3)], 2)
    return np.repeat(np.repeat(sm, 4, 0), 4, 1)[:h, :w]


def apply(arr, lt, fno):
    h, w = arr.shape[:2]
    rgb = arr[..., :3].astype(np.float32)
    # 1) 되감기 리플(조각 시작): 줄마다 좌우로 일렁
    if lt < RIPPLE:
        k = 1 - lt / RIPPLE
        ys = np.arange(h, dtype=np.float32)
        shift = (np.sin(ys / 17.0 + fno * 0.9) * 26 * k + np.sin(ys / 5.0 + fno * 1.7) * 7 * k).astype(np.int32)
        idx = (np.arange(w)[None, :] + shift[:, None]) % w
        rgb = rgb[np.arange(h)[:, None], idx]
    # 2) 채도 낮춤 + 세피아 톤
    g = rgb @ np.array([0.299, 0.587, 0.114], np.float32)
    rgb = rgb * 0.55 + g[..., None] * 0.45
    rgb = rgb * np.array([1.04, 0.98, 0.86], np.float32) + np.array([6, 3, -4], np.float32)
    # 3) 부드러운 글로
    rgb = rgb * 0.78 + _blur(rgb, 10) * 0.30
    # 4) 비네트
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    d = np.sqrt(((xx - w / 2) / (w / 2)) ** 2 + ((yy - h / 2) / (h / 2)) ** 2)
    rgb = rgb * (1 - 0.30 * np.clip(d - 0.55, 0, 1) ** 1.3)[..., None]
    # 5) 필름 입자(프레임마다 다른 잡음) + 가끔 세로 스크래치
    rng = np.random.default_rng(fno)
    rgb = rgb + rng.normal(0, 4.5, (h, w, 1)).astype(np.float32)
    if fno % 23 in (0, 1):
        x0 = int(rng.integers(w // 8, w * 7 // 8)); rgb[:, x0:x0 + 2] += 22
    out = arr.copy()
    out[..., :3] = np.clip(rgb, 0, 255).astype(np.uint8)
    return out
