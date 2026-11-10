"""〈점〉 모델 시트 v1: 용 전체 / 종이 지도 / 눈 접사(C10 화각) / 발톱(C7 위치) / 점의 상태(기술 시험)."""
import sys, os, math
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.join(HERE, 'engine'))
import numpy as np, cv2
from paper import View, paper_layers
from brush import render_strokes
from look import ink_on_paper, film, light, save
import dragon

def shot(v, mode=None, t=0.0):
    fib, flk, mot, X, Y = paper_layers(v)
    d = render_strokes(v, dragon.strokes(), fib) * dragon.eye_blank(X, Y)
    img = ink_on_paper(fib, flk, mot, d)
    if mode: img = light(img, mode)
    return film(img, t)

def to8(img): return (np.clip(img, 0, 1)[..., ::-1] * 255 + 0.5).astype(np.uint8)

whole = View(320, 210, 660, 1920, 1080)
A = to8(shot(whole))
B = A.copy()
# 지도 덧그림(설명용)
def P(x, y): px, py = whole.to_px(x, y); return int(px), int(py)
cv2.line(B, P(0, 318), P(100, 420), (40, 40, 200), 2)
for x, y, lab in ((38, 392, 'S0'), (52, 376, 'S1'), (82, 352, 'S2'), (180, 285, 'S3'), (200, 268, 'S4'), (245, 238, 'S5'), (282, 190, 'S6'), (298, 128, 'S7')):
    cv2.circle(B, P(x, y), 9, (40, 40, 200), 2); cv2.putText(B, lab, (P(x, y)[0] + 12, P(x, y)[1] - 8), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (40, 40, 200), 2)
pts = [P(*p) for p in ((38, 392), (52, 376), (82, 352), (95, 340), (180, 285), (200, 268), (245, 238), (282, 190), (292, 150), (298, 128), (300, 112))]
cv2.polylines(B, [np.array(pts)], False, (40, 40, 200), 1, cv2.LINE_AA)
cv2.circle(B, P(300, 112), 22, (30, 140, 30), 2); cv2.putText(B, 'E', (P(300, 112)[0] + 26, P(300, 112)[1]), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (30, 140, 30), 2)
cv2.putText(B, 'cut line + ruler/knife', (P(10, 300)[0], P(10, 300)[1]), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (40, 40, 200), 2)
cv2.putText(B, 'window (rain) ^', (P(260, 8)[0], P(260, 8)[1] + 20), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (120, 60, 20), 2)
C = to8(shot(View(300, 114, 70, 1920, 1080)))                  # C10 화각
Dn = to8(shot(View(265, 228, 80, 1920, 1080), 'night'))       # 발톱, 밤
Dl = to8(shot(View(320, 210, 660, 1920, 1080), 'lamp'))       # 등잔 아래 전체
for im, path in ((A, 'ms_whole.png'), (B, 'ms_map.png'), (C, 'ms_eye.png'), (Dn, 'ms_claw_night.png'), (Dl, 'ms_whole_lamp.png')):
    cv2.imwrite(os.path.join(HERE, 'sheets', path), im)
half = lambda im: cv2.resize(im, (960, 540), interpolation=cv2.INTER_AREA)
def lab(im, s):
    im = im.copy(); cv2.rectangle(im, (0, 0), (len(s) * 13 + 16, 30), (20, 20, 20), -1)
    cv2.putText(im, s, (8, 21), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (240, 240, 240), 1); return im
sheet = np.vstack([np.hstack([lab(half(A), 'A whole paper 640x420mm'), lab(half(B), 'B paper map: path S0-S7, eye E')]),
                   np.hstack([lab(half(C), 'C eye ECU (C10 framing, 70mm)'), lab(half(Dn), 'D claw region, night grade (C7)')]),
                   np.hstack([lab(half(Dl), 'E whole, lamp light (C1 mood)'), lab(half(cv2.imread(os.path.join(HERE, 'sheets', 'dot_states.png'))), 'F dot states (tech test v3)')])])
cv2.imwrite(os.path.join(HERE, 'sheets', 'model_sheet_v1.png'), sheet)
print('ok')
