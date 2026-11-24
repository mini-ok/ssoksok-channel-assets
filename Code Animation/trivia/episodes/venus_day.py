"""금성의 하루는 1년보다 길까?
출처(2026-11-24 다시 확인)
- NASA Space Place 'All About Venus' https://spaceplace.nasa.gov/all-about-venus/en/ :
  한 바퀴 자전에 약 243 지구일, 해를 한 바퀴 도는 데 225 지구일 → 금성의 하루가 1년보다 조금 길다.
  금성은 거꾸로 돌아서 해가 서쪽에서 떠 동쪽으로 진다.
- NASA Science 'Venus: Facts' https://science.nasa.gov/venus/venus-facts/ :
  '하루' 243 지구일, 금성의 1년(해를 한 바퀴) 225 지구일. 거꾸로 돌아서 해가 서쪽에서 뜬다.
화면의 '하루'는 자전 1회(항성일) 기준. 두 출처가 117일을 서로 다르게 설명해(해 뜸→해 짐 / 해 뜸 간격) 117일은 쓰지 않는다.
비율: 243 / 225 = 1.08 → '약 18일 더 길다'(243 − 225 = 18).
"""
import math
import engine as E
from engine import S, card, text_line, smooth, ramp, clamp, spring, expo_out, BOLD

TITLE_EN, TITLE_KO = 'A Day on Venus', '금성의 하루'
PALETTE = dict(accent='#D9822B', accent2='#4F6D8F')
VEN, VEN2, VEN3 = E.hexc('#E8C07A'), E.hexc('#D9A55B'), E.hexc('#F4DBA6')
SUN = E.hexc('#F2A13B')
SOUND = dict(seed=34, root=174.6)


def venus(cr, x, y, r, t, a=1.0, spin=-0.3):
    """금성: 둥근 종이 + 구름 띠(띠가 천천히 거꾸로 흐른다)."""
    S.circle(cr, x, y, r); S.fill(cr, VEN, a)
    for k, (dy, h, col) in enumerate([(-0.55, 0.12, VEN3), (-0.2, 0.16, VEN2), (0.18, 0.11, VEN3), (0.5, 0.14, VEN2)]):
        cx = x + math.sin(t * spin + k * 1.7) * r * 0.25
        w = r * math.sqrt(max(0.0, 1 - dy * dy)) * 0.85
        S.ellipse(cr, cx, y + dy * r, w, h * r); S.fill(cr, col, 0.55 * a)
    S.circle(cr, x - r * 0.3, y - r * 0.3, r * 0.42); S.fill(cr, E.hexc('#FBEBC4'), 0.35 * a)


def sun(cr, x, y, r, t, a=1.0):
    for k in range(12):
        ang = k * math.pi / 6 + t * 0.25
        S.poly(cr, [(x + math.cos(ang - 0.12) * r * 1.12, y + math.sin(ang - 0.12) * r * 1.12),
                    (x + math.cos(ang) * r * 1.5, y + math.sin(ang) * r * 1.5),
                    (x + math.cos(ang + 0.12) * r * 1.12, y + math.sin(ang + 0.12) * r * 1.12)])
    S.fill(cr, SUN, a)
    S.circle(cr, x, y, r); S.fill(cr, E.hexc('#F7B84B'), a)
    S.circle(cr, x - r * 0.25, y - r * 0.25, r * 0.55); S.fill(cr, E.hexc('#FBD27A'), 0.6 * a)


def draw_b0(L, t, u, ep):            # 질문: 해 둘레를 도는 금성
    a = smooth(ramp(t, 0.4, 0.9))
    cx, cy = 540, 1330
    sun(L['mid'], cx, cy, 120 * (0.8 + 0.2 * spring(clamp((t - 0.4) / 0.8))), t, a)
    S.ring(L['back'], cx, cy, 330, 338); S.fill(L['back'], ep.pal['muted'], 0.45 * a)
    ang = math.pi * 0.15 - t * 0.35
    venus(L['near'], cx + math.cos(ang) * 334, cy + math.sin(ang) * 334, 92, t, a)


def draw_b2(L, t, u, ep):            # 거꾸로 돌기: 서쪽 지평선에서 해가 뜬다
    rise = expo_out(clamp((t - 0.4) / 2.2))
    sun(L['mid'], 250, 1580 - 480 * rise, 95, t)               # 지평선 아래에서 올라온다(땅이 같은 층에서 뒤에 그려져 가림)
    venus(L['mid'], 540, 2380, 1000, t * 0.4, spin=-0.15)    # 아래를 채우는 금성의 땅(큰 원의 윗부분)   # 아래를 채우는 금성의 땅(큰 원의 윗부분)
    a = smooth(ramp(t, 0.8, 1.3))
    text_line(L['type'], 'WEST · 서', 250, 1530, 44, ep.pal['ink'], a, BOLD)
    text_line(L['type'], 'EAST · 동', 830, 1530, 44, ep.pal['muted'], a, BOLD)


def draw_b3(L, t, u, ep):            # 정답 아래 그림
    venus(L['near'], 540, 1450, 230, t)
    sun(L['mid'], 200, 1700, 80, t, 0.9)


def fmt_d(v): return f'{v:,.0f} days'


BEATS = [
    dict(type='hook', dur=5.0, q_en='Is a day on Venus longer than its year?',
         q_ko='금성의 하루는 1년보다 길까?'),
    dict(type='compare', dur=8.0, cap_en='Measured in Earth days', cap_ko='지구의 날수로 재 보면',
         items=[dict(en='One trip around the Sun (1 year)', ko='해를 한 바퀴(1년)', value=225, alt='225 Earth days',
                     color='#4F6D8F'),
                dict(en='One spin on its axis (1 day)', ko='제자리 한 바퀴(하루)', value=243, alt='243 Earth days',
                     color='#D9822B')],
         fmt='{:,.0f}', stagger=1.5, note_en='The day is 18 days longer', note_ko='하루가 18일 더 길다',
         note_t=5.0, base_y=1440),
    dict(type='fact', dur=6.5, cap_en='Venus spins backward, so the Sun rises in the west.',
         cap_ko='금성은 거꾸로 돌아 해가 서쪽에서 뜬다.',
         sub_en='And it sets in the east.', sub_ko='그리고 동쪽으로 진다.', sub_t=2.2, sub_y=1640),
    dict(type='answer', dur=5.0, a_en='Yes, the day is longer!', a_ko='정답은 하루가 더 길다!',
         sub_en='Source: NASA', sub_ko='출처: 미국 항공우주국(NASA)'),
]

YT = dict(
    title_en='Is a day on Venus longer than its year? #shorts',
    title_ko='금성의 하루는 1년보다 길까? #shorts',
    desc_en=("Venus takes about 243 Earth days to spin once on its axis, but only 225 Earth days to go around the Sun. "
             "So one Venus day is longer than one Venus year.\n"
             "Venus also spins backward, so the Sun rises in the west and sets in the east.\n"
             "Paper cut-outs, moved entirely with code. For a wordless short film from the same studio, tap the related video below.\n\n"
             "Source: NASA Space Place (spaceplace.nasa.gov/all-about-venus), NASA Science (science.nasa.gov/venus/venus-facts)\n\n"
             "A Day on Venus · Dreamloom Studio (Heosang Gongbang)\n\n#venus #space #shorts"),
    desc_ko=("금성은 제자리에서 한 바퀴 도는 데 약 243 지구일, 해를 한 바퀴 도는 데는 225 지구일이 걸립니다. "
             "그래서 금성의 하루가 1년보다 깁니다.\n"
             "게다가 금성은 거꾸로 돌아서 해가 서쪽에서 떠 동쪽으로 집니다.\n"
             "종이 오림을 코드로 움직였습니다. 같은 공방의 대사 없는 단편은 아래 '관련 동영상'에서 볼 수 있어요.\n\n"
             "출처: NASA Space Place, NASA Science\n\n"
             "〈금성의 하루〉 · 허상공방 (虛像工房) Dreamloom Studio\n\n#금성 #우주 #과학상식 #shorts"),
    tags=['금성', 'venus', '금성의 하루', 'day on venus', '자전', '공전', 'rotation', 'orbit', '우주', 'space facts',
          '과학 상식', 'science facts', '종이 애니메이션', 'paper animation', '허상공방', 'Dreamloom Studio'],
    related='ONNdFZnFpvw',   # 관련 동영상(Studio에서 수동): 빛지기 — 밤하늘·등대 불빛(우주·하늘 주제에 가장 가깝다)
)
