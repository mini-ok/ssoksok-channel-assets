"""CCTV·되감기 회상 효과 — 장면 fx에 "flashback"을 넣으면 그 조각의 프레임 전체에 적용된다
(2026-10-27, 사용자 지시: '되감기 됐을 때 화면에 줄무늬가 들어갔다, 그 컷처럼' → 가로 줄무늬(스캔라인) CCTV 화면을 되살림).
구성: ① 가로 스캔라인 줄무늬 + 천천히 올라가는 밝은 띠 ② 채도 살짝 낮춤 + 회색빛 톤 ③ 약한 비네트·입자
      ④ 뷰파인더 모서리 괄호 + 'REC' 빨간 점(깜빡) + 우하단 시각 'PM 3:00' ⑤ 조각 시작 0.5초 되감기 리플.
조각 필드(선택): ch["stamp"] = "PM 3:00" 같은 우하단 문구(없으면 time=(h,m)에서 만든다). 영어는 lang="en".
apply(arr, lt, fno, stamp=None, lang="ko"): arr = (H, W, 4) uint8 RGBA.
"""
import os
import numpy as np
from scipy import ndimage as ndi
from PIL import Image, ImageDraw, ImageFont

RIPPLE = 0.5
_FONTS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "paper_story", "fonts")


def _font(name, size):
    for base in (_FONTS, "/home/claude/ps/fonts", "/home/claude/assets/engine/paper_story/fonts"):
        p = os.path.join(base, name)
        if os.path.exists(p):
            return ImageFont.truetype(p, size)
    return ImageFont.load_default()


def stamp_of(ch, lang="ko"):
    if ch.get("stamp"): return ch["stamp"]
    t = ch.get("time")
    if not t: return None
    h, m = t
    ap = "PM" if h >= 12 else "AM"
    hh = h % 12 or 12
    return f"{ap} {hh}:{m:02d}"


def apply(arr, lt, fno, stamp=None, lang="ko", ui=True):
    h, w = arr.shape[:2]
    rgb = arr[..., :3].astype(np.float32)
    # 1) 되감기 리플(조각 시작)
    if lt < RIPPLE:
        k = 1 - lt / RIPPLE
        ys = np.arange(h, dtype=np.float32)
        shift = (np.sin(ys / 15.0 + fno * 0.9) * 22 * k + np.sin(ys / 5.0 + fno * 1.7) * 6 * k).astype(np.int32)
        idx = (np.arange(w)[None, :] + shift[:, None]) % w
        rgb = rgb[np.arange(h)[:, None], idx]
    # 2) 채도 낮춤 + 회색빛 톤
    g = rgb @ np.array([0.299, 0.587, 0.114], np.float32)
    rgb = rgb * 0.72 + g[..., None] * 0.28
    rgb = rgb * np.array([0.98, 0.99, 1.0], np.float32) * 0.97 + 6
    # 3) 가로 줄무늬(스캔라인): 3행마다 1행 어둡게 + 약한 밝은 띠가 천천히 위로
    ys = np.arange(h)
    line = np.where(ys % 4 == 0, 0.84, np.where(ys % 4 == 1, 0.93, 1.0)).astype(np.float32)
    band_c = (h - (fno * 3.2) % (h * 1.4)) % (h * 1.4)
    band = 1 + 0.06 * np.exp(-((ys - band_c) / (h * 0.06)) ** 2).astype(np.float32)
    rgb = rgb * (line * band)[:, None, None]
    # 4) 약한 비네트 + 입자
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    d = np.sqrt(((xx - w / 2) / (w / 2)) ** 2 + ((yy - h / 2) / (h / 2)) ** 2)
    rgb = rgb * (1 - 0.18 * np.clip(d - 0.6, 0, 1) ** 1.3)[..., None]
    rng = np.random.default_rng(fno)
    rgb = rgb + rng.normal(0, 3.2, (h, w, 1)).astype(np.float32)
    img = Image.fromarray(np.clip(rgb, 0, 255).astype(np.uint8)).convert("RGBA")
    if not ui:
        return np.array(img)
    # 5) 뷰파인더 괄호 · REC · 시각 (ui=False면 생략: 장면이 이미 그렸을 때)
    dr = ImageDraw.Draw(img)
    s = h / 1080.0
    m, L, tw = int(0.025 * w), int(54 * s), max(3, int(5 * s))
    wh = (246, 244, 236, 235)
    for sx, sy in ((m, m), (w - m, m), (m, h - m), (w - m, h - m)):
        dx = 1 if sx < w / 2 else -1; dy = 1 if sy < h / 2 else -1
        dr.line([(sx, sy), (sx + dx * L, sy)], fill=wh, width=tw)
        dr.line([(sx, sy), (sx, sy + dy * L)], fill=wh, width=tw)
    if (fno // 15) % 2 == 0:   # 0.5초마다 깜빡
        r = int(11 * s); cx, cy = int(0.775 * w), int(0.101 * h)
        dr.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(255, 84, 60, 255))
    dr.text((int(0.788 * w), int(0.101 * h)), "REC", font=_font("Geist-Black.ttf", int(30 * s)), fill=(40, 52, 96, 255), anchor="lm")
    st = stamp
    if st:
        dr.text((int(0.918 * w), int(0.909 * h)), st, font=_font("Geist-Black.ttf", int(40 * s)), fill=(40, 52, 96, 255), anchor="rm")
    return np.array(img)
