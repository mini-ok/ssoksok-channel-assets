"""소리는 공기와 물 중 어디서 더 빠를까?
출처(2026-11-25 다시 확인)
- OpenStax University Physics Volume 1, 17.2 Speed of Sound
  https://openstax.org/books/university-physics-volume-1/pages/17-2-speed-of-sound :
  표 17.1 'Speed of Sound in Various Media' — 액체(20 °C) 'Water, fresh' 1480 m/s.
  본문: "At 0°C, the speed of sound is 331 m/s, whereas at 20.0°C, it is 343 m/s".
  같은 절: 소리의 속도는 매질이 얼마나 잘 눌리지 않는지(체적 탄성률)와 밀도로 정해진다(v = √(B/ρ)).
환산: 343 m/s × 3.2808 = 1,125 ft/s. 1,480 m/s × 3.2808 = 4,856 ft/s → '≈ 4,860 ft/s'.
비율: 1480 / 343 = 4.31 → '약 4.3배'. 두 값 모두 20 °C(공기·민물).
"""
import math
import engine as E
from engine import S, card, text_line, smooth, ramp, clamp, spring, expo_out, BOLD

TITLE_EN, TITLE_KO = 'Sound in Water', '물속의 소리'
PALETTE = dict(accent='#2F7FB5', accent2='#E08A3B')
SEA, SEA2, FOAM = E.hexc('#3C7FAF'), E.hexc('#2C6390'), E.hexc('#BFDDEB')
WHALE, WHALE2 = E.hexc('#3D4F63'), E.hexc('#C9D3DC')
AIRC, SPK = E.hexc('#E08A3B'), E.hexc('#4A4540')
SOUND = dict(seed=47, root=164.8)


def speaker(cr, x, y, s, a=1.0):
    """종이 확성기: 몸통 사각 + 나팔 사다리꼴(오른쪽으로 소리)."""
    S.poly(cr, [(x - s * 0.55, y - s * 0.22), (x - s * 0.15, y - s * 0.22),
                (x + s * 0.35, y - s * 0.6), (x + s * 0.35, y + s * 0.6),
                (x - s * 0.15, y + s * 0.22), (x - s * 0.55, y + s * 0.22)])
    S.fill(cr, SPK, a)


def sound_rings(cr, x, y, t, speed, col, a=1.0, n=4, gap=70, rmax=420):
    """퍼지는 소리: 오른쪽으로 벌어지는 호를 작은 종이 점으로 찍는다(멀어질수록 흐려짐)."""
    for k in range(n):
        r = (t * speed - k * gap) % (n * gap) + 30
        if r < rmax:
            for j in range(9):
                ang = -0.55 + j * 0.1375
                S.circle(cr, x + math.cos(ang) * r, y + math.sin(ang) * r, 7)
            S.fill(cr, col, a * max(0.0, 1 - r / rmax))


def sea(cr, y, t, a=1.0):
    """화면 아래를 채우는 바다: 물결 위쪽 선 + 짙은 바닥."""
    S.poly(cr, [(0, y)] + [(x, y + math.sin(x / 90 + t * 1.6) * 14) for x in range(0, 1081, 30)] +
           [(1080, 1920), (0, 1920)])
    S.fill(cr, SEA, a)
    S.poly(cr, [(0, y + 260)] + [(x, y + 260 + math.sin(x / 120 - t * 1.1) * 10) for x in range(0, 1081, 30)] +
           [(1080, 1920), (0, 1920)])
    S.fill(cr, SEA2, a)


def whale(cr, x, y, s, t, a=1.0):
    sw = math.sin(t * 2.0) * 0.12
    S.poly(cr, [(x - s * 0.9, y), (x - s * 1.35, y - s * (0.32 + sw)), (x - s * 1.25, y),
                (x - s * 1.35, y + s * (0.32 - sw))])
    S.fill(cr, WHALE, a)
    S.ellipse(cr, x, y, s, s * 0.42); S.fill(cr, WHALE, a)
    S.ellipse(cr, x + s * 0.1, y + s * 0.2, s * 0.7, s * 0.16); S.fill(cr, WHALE2, 0.8 * a)
    S.circle(cr, x + s * 0.62, y - s * 0.08, s * 0.05); S.fill(cr, E.hexc('#FBF6EA'), a)


def draw_b0(L, t, u, ep):            # 질문: 위는 공기 속 확성기, 아래는 물속 고래
    a = smooth(ramp(t, 0.4, 0.9))
    sea(L['mid'], 1330, t, a)
    speaker(L['near'], 230, 1060, 150 * (0.8 + 0.2 * spring(clamp((t - 0.4) / 0.8))), a)
    sound_rings(L['back'], 290, 1060, t, 160, AIRC, 0.9 * a, rmax=520)
    whale(L['near'], 560, 1610, 170, t, a)
    sound_rings(L['near'], 740, 1610, t, 160, FOAM, 0.9 * a, rmax=330)   # 바다(mid) 위에 보이도록 near


def draw_b2(L, t, u, ep):            # 왜? 같은 '밀기'가 공기 줄보다 물 줄에서 4.3배 빨리 건너간다
    cr = L['mid']
    rows = [(1050, 'AIR · 공기', AIRC, 343), (1330, 'WATER · 물', SEA, 1480)]
    a = smooth(ramp(t, 0.3, 0.8))
    for y, lab, col, v in rows:
        text_line(L['type'], lab, 540, y - 95, 44, ep.pal['ink'], a, BOLD)
        card(L['back'], 90, y - 50, 900, 100, col, r=50, a=0.18 * a)
        # 펄스: 1.0초에 함께 출발, 물 줄은 1,480/343 배 빠르게(물 약 2.0초, 공기 약 5.4초에 끝 도착)
        px = 120 + min(max(0.0, t - 1.0) * 196 * v / 343, 840)
        for k in range(16):
            x0 = 120 + k * 56
            d = math.exp(-((x0 - px) / 55) ** 2)
            S.circle(L['near'], x0 + d * 16, y + math.sin(t * 3 + k) * 3, 16 + 8 * d)
        S.fill(L['near'], col, a)


def draw_b3(L, t, u, ep):            # 정답 아래 그림: 바다와 노래하는 고래
    sea(L['mid'], 1380, t)
    whale(L['near'], 560, 1640, 190, t)
    sound_rings(L['near'], 760, 1640, t, 260, FOAM, 0.9, rmax=320)


def fmt_ms(v): return f'{v:,.0f} m/s'


BEATS = [
    dict(type='hook', dur=5.0, q_en='Does sound travel faster in air or in water?',
         q_ko='소리는 공기와 물 중 어디서 더 빠를까?'),
    dict(type='compare', dur=8.0, cap_en='Speed of sound at 20 °C (68 °F)', cap_ko='섭씨 20도에서 소리의 속도',
         items=[dict(en='Air', ko='공기', value=343, alt='≈ 1,125 ft/s', color='#E08A3B'),
                dict(en='Water', ko='물', value=1480, alt='≈ 4,860 ft/s', color='#2F7FB5')],
         fmt=fmt_ms, stagger=1.5, note_en='About 4.3 times faster in water', note_ko='물속에서 약 4.3배 빠르다',
         note_t=5.0, base_y=1440),
    dict(type='fact', dur=7.0, cap_en='Water is much harder to squeeze than air.',
         cap_ko='물은 공기보다 훨씬 덜 눌린다.',
         sub_en='So each push is passed along faster.', sub_ko='그래서 떨림이 더 빨리 전해진다.', sub_t=2.4, sub_y=1600),
    dict(type='answer', dur=5.0, a_en='Water wins!', a_ko='정답은 물!',
         sub_en='Source: OpenStax University Physics', sub_ko='출처: OpenStax 대학 물리학'),
]

YT = dict(
    title_en='Does sound travel faster in air or in water? #shorts',
    title_ko='소리는 공기와 물 중 어디서 더 빠를까? #shorts',
    desc_en=("At 20 °C (68 °F), sound moves through air at about 343 m/s (≈1,125 ft/s). "
             "In fresh water it moves at about 1,480 m/s (≈4,860 ft/s): roughly 4.3 times faster.\n"
             "Water is much harder to squeeze than air, so each push of a sound wave is passed along faster.\n"
             "Paper cut-outs, moved entirely with code. For a wordless short film from the same studio, tap the related video below.\n\n"
             "Source: OpenStax University Physics Volume 1, 17.2 Speed of Sound "
             "(openstax.org/books/university-physics-volume-1/pages/17-2-speed-of-sound)\n\n"
             "Sound in Water · Dreamloom Studio (Heosang Gongbang)\n\n#sound #physics #shorts"),
    desc_ko=("섭씨 20도에서 소리는 공기 속을 초속 약 343 m(약 1,125 ft/s)로 갑니다. "
             "민물 속에서는 초속 약 1,480 m(약 4,860 ft/s), 약 4.3배 빠르죠.\n"
             "물은 공기보다 훨씬 덜 눌려서, 소리의 떨림이 더 빨리 전해집니다.\n"
             "종이 오림을 코드로 움직였습니다. 같은 공방의 대사 없는 단편은 아래 '관련 동영상'에서 볼 수 있어요.\n\n"
             "출처: OpenStax University Physics 1권, 17.2 소리의 속도\n\n"
             "〈물속의 소리〉 · 허상공방 (虛像工房) Dreamloom Studio\n\n#소리 #물리 #과학상식 #shorts"),
    tags=['소리', '음속', 'sound', 'speed of sound', '물속 소리', 'sound in water', '고래', 'whale', '물리', 'physics',
          '과학 상식', 'science facts', '종이 애니메이션', 'paper animation', '허상공방', 'Dreamloom Studio'],
    related='ONNdFZnFpvw',   # 관련 동영상(Studio에서 수동): 빛지기 — 바다·등대
)
