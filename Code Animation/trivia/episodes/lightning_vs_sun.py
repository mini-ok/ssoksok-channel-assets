"""번개와 태양 표면, 어느 쪽이 더 뜨거울까?
출처
- NWS(미국 국립기상청) https://www.weather.gov/safety/lightning-temperature :
  번개는 지나가는 공기를 50,000 °F까지 데운다(태양 표면의 약 5배).
- NOAA NSSL https://www.nssl.noaa.gov/education/svrwx101/lightning/ :
  번개 통로의 에너지가 공기를 순간 약 50,000 °F로 데우고, 공기가 바깥으로 터지듯 퍼지며 천둥이 난다.
- 태양 표면(광구) 약 10,000 °F(≈ 5,500 °C): NWS의 '5배' 비교 기준과 같은 값.
환산: 50,000 °F = 27,760 °C → 화면 '약 27,800 °C'. 10,000 °F = 5,538 °C → '약 5,500 °C'.
"""
import math
import engine as E
from engine import S, card, text_line, smooth, ramp, clamp, spring, expo_out, BOLD

TITLE_EN, TITLE_KO = 'Lightning vs the Sun', '번개 vs 태양'
PALETTE = dict(accent='#E0442E', accent2='#F2A13B')
SUN, BOLT, CLOUD = E.hexc('#F2A13B'), E.hexc('#FFD23F'), E.hexc('#4A5568')
SOUND = dict(seed=21, root=196.0)


def sun(cr, x, y, r, t, a=1.0):
    for k in range(12):
        ang = k * math.pi / 6 + t * 0.25
        S.poly(cr, [(x + math.cos(ang - 0.12) * r * 1.12, y + math.sin(ang - 0.12) * r * 1.12),
                    (x + math.cos(ang) * r * 1.5, y + math.sin(ang) * r * 1.5),
                    (x + math.cos(ang + 0.12) * r * 1.12, y + math.sin(ang + 0.12) * r * 1.12)])
    S.fill(cr, SUN, a)
    S.circle(cr, x, y, r); S.fill(cr, E.hexc('#F7B84B'), a)
    S.circle(cr, x - r * 0.25, y - r * 0.25, r * 0.55); S.fill(cr, E.hexc('#FBD27A'), 0.6 * a)


def bolt(cr, x, y, s, a=1.0, col=BOLT):
    pts = [(0.15, -1.0), (-0.45, 0.1), (-0.02, 0.1), (-0.28, 1.0), (0.48, -0.22), (0.05, -0.22), (0.35, -1.0)]
    S.poly(cr, [(x + px * s, y + py * s) for px, py in pts]); S.fill(cr, col, a)


def cloud(cr, x, y, s, a=1.0):
    for dx, dy, r in [(-0.6, 0.1, 0.42), (-0.15, -0.15, 0.55), (0.4, 0, 0.45), (0.05, 0.2, 0.45)]:
        S.circle(cr, x + dx * s, y + dy * s, r * s)
    S.fill(cr, CLOUD, a)


def draw_b0(L, t, u, ep):            # 질문: 태양 vs 번개
    a = smooth(ramp(t, 0.4, 0.9))
    sun(L['near'], 290, 1330, 150 * (0.8 + 0.2 * spring(clamp((t - 0.4) / 0.8))), t, a)
    cloud(L['mid'], 790, 1170, 230, a)
    b = smooth(ramp(t, 0.9, 1.1)) * (0.75 + 0.25 * (math.sin(t * 23) > -0.3))
    bolt(L['near'], 800, 1440, 260, b)
    text_line(L['type'], 'VS', 545, 1370, 96, ep.pal['ink'], smooth(ramp(t, 1.2, 1.6)), BOLD)


def draw_b1(L, t, u, ep):            # 태양 표면 숫자: 아래에 큰 해가 떠오름
    rise = expo_out(clamp((t - 0.2) / 1.2))
    sun(L['mid'], 540, 2080 - 320 * rise, 300, t)


def draw_b3(L, t, u, ep):            # 천둥: 번개 + 퍼지는 공기 고리
    cloud(L['mid'], 540, 760, 260)
    bolt(L['near'], 540, 1090, 300, 0.85 + 0.15 * (math.sin(t * 29) > 0))
    cr = L['mid']
    for k in range(4):
        r = ((t - 0.5) * 260 - k * 120)
        if r > 20:
            S.ring(cr, 540, 1150, r, r + 14); S.fill(cr, ep.pal['accent'], max(0, 0.55 - r / 1100))


def draw_b4(L, t, u, ep):            # 정답 아래 그림
    bolt(L['near'], 540, 1420, 260)
    sun(L['mid'], 240, 1620, 90, t, 0.9)


def fmt_c(v): return f'{round(v / 100) * 100:,.0f} °C'


BEATS = [
    dict(type='hook', dur=4.5, q_en='Which is hotter: lightning or the surface of the Sun?',
         q_ko='번개와 태양 표면, 어느 쪽이 더 뜨거울까?'),
    dict(type='number', dur=5.5, cap_en="The Sun's surface", cap_ko='태양의 표면 온도',
         value=5500, fmt=lambda v: f'≈{round(v / 100) * 100:,.0f}', unit_en='degrees Celsius', unit_ko='섭씨(°C)',
         alt='≈ 10,000 °F', y=1080),
    dict(type='compare', dur=8.0, cap_en='Now, the air around a lightning bolt', cap_ko='그럼 번개가 지나가는 공기는?',
         items=[dict(en='Sun surface', ko='태양 표면', value=5500, alt='≈ 10,000 °F', color='#F2A13B'),
                dict(en='Lightning', ko='번개', value=27800, alt='≈ 50,000 °F', color='#5B5FD6')],
         fmt=fmt_c, stagger=1.6, note_en='About 5 times hotter', note_ko='약 5배 더 뜨겁다', note_t=5.0, base_y=1480),
    dict(type='fact', dur=6.0, cap_en='The air heats so fast it bursts outward.',
         cap_ko='공기가 순식간에 달아올라 터지듯 퍼진다.',
         sub_en='That blast is the thunder you hear.', sub_ko='그 소리가 바로 천둥이다.', sub_t=2.2, sub_y=1500),
    dict(type='answer', dur=5.0, a_en='Lightning wins!', a_ko='정답은 번개!',
         sub_en='Source: U.S. National Weather Service', sub_ko='출처: 미국 국립기상청(NWS)'),
]

YT = dict(
    title_en='Lightning vs the Sun: which is hotter? #shorts',
    title_ko='번개 vs 태양 표면, 어느 쪽이 더 뜨거울까? #shorts',
    desc_en=("The Sun's surface is about 10,000 °F (≈5,500 °C). The air around a lightning bolt can reach about 50,000 °F "
             "(≈27,800 °C): roughly five times hotter.\n"
             "That sudden heat makes the air burst outward, and the blast is the thunder you hear.\n"
             "Paper cut-outs, moved entirely with code. For a wordless short film from the same studio, tap the related video below.\n\n"
             "Source: U.S. National Weather Service (weather.gov/safety/lightning-temperature), NOAA NSSL\n\n"
             "Lightning vs the Sun · Dreamloom Studio (Heosang Gongbang)\n\n#lightning #science #shorts"),
    desc_ko=("태양 표면은 약 5,500 °C(약 10,000 °F). 번개가 지나가는 공기는 약 27,800 °C(약 50,000 °F)까지 달아오릅니다. 약 5배죠.\n"
             "순식간에 달아오른 공기가 터지듯 퍼지는 소리, 그게 바로 천둥입니다.\n"
             "종이 오림을 코드로 움직였습니다. 같은 공방의 대사 없는 단편은 아래 '관련 동영상'에서 볼 수 있어요.\n\n"
             "출처: 미국 국립기상청(NWS), NOAA 국립악기상연구소(NSSL)\n\n"
             "〈번개 vs 태양〉 · 허상공방 (虛像工房) Dreamloom Studio\n\n#번개 #과학상식 #상식 #shorts"),
    tags=['번개', '태양', 'lightning', 'sun', '번개 온도', 'lightning temperature', '천둥', 'thunder', '상식', '과학 상식',
          'science facts', '모션그래픽', 'motion graphics', '종이 애니메이션', 'paper animation', '허상공방', 'Dreamloom Studio'],
    related='ONNdFZnFpvw',   # 관련 동영상(Studio에서 수동): 빛지기 — 폭풍·번개 치는 밤
)
