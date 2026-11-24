"""〈42번〉 FOLD 42 — 숫자 파일. 시각(초)·높이(m)·색은 여기서만 고친다. 다른 파일은 가져다 쓰기만 한다.
세로 눈금: 접은 횟수 n(= 로그 눈금). 두께 = T0 × 2^n. 화면에서 한 번 접기 = U 픽셀(디자인 1080×1920).
"""
import math

FPS = 30
T0_M = 1e-4                                   # 종이 한 장 0.1 mm (가정 — 화면에 밝힌다)
def thick(n): return T0_M * 2.0 ** n
def level(h): return math.log2(h / T0_M)

# ---- 시간표(0.1초 격자 = 3프레임). TF[k] = k번째 접는 시각
T_XF = (2.5, 2.95)                            # 첫 물음 → 책상 옆모습
T_FOLD1 = 3.0
SEG = [(2, 6, 0.4), (7, 10, 0.3), (11, 14, 0.3), (15, 21, 0.2), (22, 23, 0.3), (24, 27, 0.3),
       (28, 30, 0.3), (31, 32, 0.3), (33, 37, 0.2), (38, 41, 0.3), (42, 42, 0.7)]     # (처음, 끝, 앞 접기와의 간격)
HOLD = {10: 0.3, 14: 0.7, 23: 0.7, 27: 0.8, 30: 0.5, 32: 0.6, 37: 0.6}                # 그 접기 뒤 머무는 시간
def _table():
    TF = {1: T_FOLD1}
    for a, b, d in SEG:
        for k in range(a, b + 1): TF[k] = round(TF[k - 1] + HOLD.get(k - 1, 0.0) + d, 3)
    return TF
TF = _table()
T_MOON = TF[42]                                # 달을 지나는 순간
T_TWIST = T_MOON + 3.2                         # 실제 기록
T_END = T_TWIST + 4.0                          # 낙관
DUR = T_END + 2.2

# ---- 화면 배치
U = 300.0                                      # 한 번 접기의 화면 높이
ANCH = 820.0                                   # 탑 꼭대기가 머무는 화면 y
CAM0 = 2.0                                     # 시작 때 카메라 높이(접기 단위)
TX, TW = 540.0, 128.0                          # 종이 탑 가운데 x, 폭

# ---- 이정표: 키, 높이(m), 영어, 한글, 미터, 야드파운드, 쪽(L/R)
MARKS = [
    ('pencil', 0.007, 'a pencil', '연필 굵기', '7 mm', '0.28 in', 'L'),
    ('cup', 0.10, 'a coffee cup', '커피잔', '10 cm', '4 in', 'R'),
    ('person', 1.7, 'a person', '사람 키', '1.7 m', '5 ft 7 in', 'L'),
    ('eiffel', 330.0, 'Eiffel Tower', '에펠탑', '330 m', '1,083 ft', 'R'),
    ('burj', 828.0, 'Burj Khalifa', '부르즈 할리파', '828 m', '2,717 ft', 'L'),
    ('everest', 8849.0, 'Mt. Everest', '에베레스트', '8,849 m', '29,032 ft', 'R'),
    ('jet', 11000.0, 'airliners', '여객기', '11 km', '36,000 ft', 'L'),
    ('karman', 100e3, 'edge of space', '우주의 시작', '100 km', '62 mi', 'R'),
    ('iss', 400e3, 'Space Station', '국제우주정거장', '400 km', '250 mi', 'L'),
    ('geo', 35786e3, 'weather satellites', '정지궤도 위성', '35,786 km', '22,236 mi', 'R'),
    ('moon', 384400e3, 'the Moon', '달', '384,400 km', '238,855 mi', 'L'),
]
MK = {m[0]: m for m in MARKS}
def mlev(key): return level(MK[key][1])

# ---- 하늘빛(접기 높이별)
SKY = [(-3, '#F3E4C6'), (7, '#F6EBD3'), (11, '#DDEBDD'), (14, '#A9D8E8'), (20, '#7CC0E8'), (25, '#4D95D6'),
       (27.5, '#2C63B4'), (29.5, '#152F78'), (31.5, '#0A1646'), (35, '#060C2B'), (42, '#03061A'), (46, '#03061A')]


def fmt_metric(h):
    if h < 0.01: return f'{h * 1000:.1f} mm'
    if h < 1:
        v = h * 100; return f'{v:.1f} cm' if v < 10 else f'{v:.0f} cm'
    if h < 1000: return f'{h:.1f} m' if h < 10 else f'{h:.0f} m'
    v = h / 1000
    return f'{v:.1f} km' if v < 100 else f'{v:,.0f} km'

def fmt_imperial(h):
    inch = h / 0.0254; ft = h / 0.3048; mi = h / 1609.344
    if ft < 1: return f'{inch:.3f} in' if inch < 0.1 else (f'{inch:.2f} in' if inch < 1 else f'{inch:.1f} in')
    if mi < 1: return f'{ft:.1f} ft' if ft < 10 else f'{ft:,.0f} ft'
    return f'{mi:.1f} mi' if mi < 100 else f'{mi:,.0f} mi'


if __name__ == '__main__':
    for k in range(0, 43): print(k, TF.get(k, '-'), fmt_metric(thick(k)), '|', fmt_imperial(thick(k)))
    for m in MARKS: print(m[0], round(level(m[1]), 2))
    print('moon', T_MOON, 'twist', T_TWIST, 'end', T_END, 'dur', DUR)
