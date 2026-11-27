"""〈장단 JANGDAN〉 숫자 파일 — 박자표·샷 표·사건표·색. 그림(scene.py)과 소리(audio.py)가 이 파일 하나만 읽는다.
30fps, 120 BPM(박 = 15프레임), 4/4. 16마디 = 32초. 모든 시각은 박자표에서 나온다."""
import math, os, sys
import numpy as np
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '_kit'))
from vfx.timeline import Beat, Shots

FPS = 30
B = Beat(bpm=120, beats_per_bar=4, fps=FPS)
DW, DH = 1920, 1080                       # 디자인 좌표
CX, CY = DW / 2, DH / 2

# 샷 표(마디 단위): 점 → 선 → 면(만화경) → 모임 → 제목
SHOTS = Shots([('dots', 4 * B.bar_len), ('lines', 4 * B.bar_len), ('kaleido', 4.5 * B.bar_len),
               ('collapse', 1.0 * B.bar_len), ('title', 2.5 * B.bar_len)])
T_DOTS, T_LINES, T_KAL, T_COL, T_TITLE = SHOTS.starts
DUR = SHOTS.end                            # 32.0

# 색: 흰 종이 위에서 보이는 색(RGB) — 오방색에서 고른 네 안료
PAPER = (0.935, 0.905, 0.835)
PIG = dict(sumi=(0.10, 0.09, 0.085), red=(0.80, 0.20, 0.13), blue=(0.13, 0.27, 0.50), gold=(0.90, 0.66, 0.16))
ORDER = ['sumi', 'red', 'blue', 'gold']

# ---- 사건표 -------------------------------------------------------------------------------
rng = np.random.default_rng(11)
GA = math.pi * (3 - math.sqrt(5))          # 황금각

def _spiral(i, r0=70, k=62):
    r = r0 + k * math.sqrt(i + 0.5); a = i * GA
    return CX + r * math.cos(a) * 1.25, CY + r * math.sin(a) * 0.82

# 먹 방울: (떨어지는 시각, x, y, 반지름, 안료). 1부는 박마다, 뒤로 갈수록 반 박·반의 반 박.
DROPS = []
i = 0
for bar in range(4):
    div = [1, 1, 2, 2][bar]
    for k in range(4 * div):
        x, y = _spiral(i)
        pig = 'sumi' if bar < 2 else ['sumi', 'red', 'sumi', 'blue'][i % 4]
        DROPS.append((B.t(bar, k / div), x, y, float(rng.uniform(34, 66)) * (1.25 if k % (2 * div) == 0 else 0.8), pig)); i += 1
N_INTRO = len(DROPS)

# 붓 획(원호): (시작, 길이초, 반지름, 시작각, 휩쓰는 각, 굵기, 안료)
STROKES = [
    (B.t(4, 0), 1.5, 330, -2.4, 5.6, 46, 'sumi'),
    (B.t(5, 0), 1.0, 235, 0.6, -4.4, 30, 'red'),
    (B.t(5, 2), 1.0, 430, 2.2, 3.6, 26, 'blue'),
    (B.t(6, 0), 0.75, 150, -1.0, 5.9, 34, 'sumi'),
    (B.t(6, 2), 0.75, 500, -0.4, -2.8, 20, 'gold'),
    (B.t(7, 0), 0.5, 285, 1.9, 2.6, 18, 'gold'),
    (B.t(7, 1), 0.5, 380, -2.9, -2.2, 22, 'sumi'),
]
# 살(중심에서 뻗는 직선 획): (시각, 각도, 안쪽·바깥 반지름, 굵기, 안료) — 7마디 3·4박에 반 박마다
SPOKES = [(B.t(7, 2 + k * 0.5), -math.pi / 2 + k * math.pi / 2 + 0.3, 60, 520, 16, ['red', 'blue', 'sumi', 'gold'][k]) for k in range(4)]

# 만화경: (시각, 접는 수). 접는 수가 바뀌는 순간마다 섬광.
FOLDS = [(T_KAL, 6), (B.t(10, 0), 8), (B.t(11, 0), 12), (B.t(12, 0), 16)]
# 만화경 구간의 쐐기 안 방울(반의 반 박마다)
for k in range(int((T_COL - T_KAL) / (B.beat_len / 2))):
    t = T_KAL + k * B.beat_len / 2
    r = 90 + 430 * ((k * 0.618) % 1.0); a = 0.08 + 0.42 * ((k * 0.381) % 1.0)
    DROPS.append((t, CX + r * math.cos(a), CY + r * math.sin(a), 16 + 26 * ((k * 0.27) % 1.0), ORDER[k % 4]))

FLASHES = [T_LINES, T_KAL] + [t for t, _ in FOLDS[1:]] + [T_COL + B.beat_len * 3]     # 마지막: 한 점이 찍히는 순간
T_DOT = T_COL + B.beat_len * 3            # 모인 먹이 한 점으로 찍히는 시각
T_SEAL = B.t(14, 2)                       # 낙관
N_PART = 1400                             # 금가루 수

# 카메라(디자인 좌표 중심, 배율): 키 2개 사이를 단조 보간(오버슈트 없음)
CAM = [(0.0, CX + 40, CY + 20, 1.32), (T_LINES, CX, CY, 1.12), (T_KAL, CX, CY, 1.0), (T_COL, CX, CY, 1.06), (DUR, CX, CY, 1.0)]
