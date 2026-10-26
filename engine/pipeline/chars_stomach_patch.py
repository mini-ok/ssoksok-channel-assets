"""위 대리(stomach) 캐릭터 패치 — 2026-10-26 「야식 습격 사건」에서 추가.

적용: 자료 저장소 engine/paper_story/chars.py **맨 끝에** 아래 함수를 붙인다(그게 전부다).
      이번 실행에서 chars.py에 가한 변경은 이 추가 하나뿐이고, 기존 함수는 한 줄도 건드리지 않았다.
      (같은 폴더의 chars_stomach.diff / ps_changes.diff가 원본 대비 실제 차이 전부다.
       paper.py·ink.py·lib.py·lay.py·build2.py·render2.py는 원본과 완전히 동일하다.)

호출: chars.py의 다른 캐릭터와 똑같다. 별도 등록이나 매핑은 필요 없다.
      - 직접:            CH.stomach(cv, x, y, s, mood, lt)
      - 종이 조각으로:    paper.puff_char(img, paper.char_fn("stomach", mood), x, y, size)
      - 이 파이프라인:    render.py의 chsp("stomach", mood) → core.char_sprite()가 char_fn에 이름만 넘긴다.
      char_fn은 getattr(CH, name)으로 찾으므로 모듈에 함수만 있으면 되고, 고칠 매핑 표가 없다.

mood: chars.py의 face()가 받는 값 그대로 — happy / happy_closed / tired / wow / sleepy / smug / worry / serious / awake.
      이번 편에서 자주 쓴 조합은 worry(투정), wow(비명), tired(기진맥진), happy_closed(안도).

좌표: 다른 캐릭터와 같은 규약. 원점 = 몸통 중심, 기본 몸 반지름 약 150.
      발바닥 선은 몸 중심에서 아래로 약 179*s (feet(cv, 162, ...) + 발 타원 높이의 절반).
      다른 캐릭터는 138이라 조금 더 짧다 — 위 대리는 몸이 아래로 처진 주머니 모양이라 발을 내렸다.

디자인 근거(CHARACTER_BIBLE: 장기의 실제 모양 단순화 + 직장인 소품 1개):
      주머니 모양 연어빛 몸(위), 왼쪽 위로 뻗은 식도 꼬리, 파란 넥타이와 목에 건 사원증.

목소리: tts.py SID 표의 sid 10 'Achird'. 말버릇 "지금요?!" / "Right NOW?!".
"""
import math
import skia
from lib import *


def stomach(cv, x, y, s=1.0, mood="happy", lt=0.0):
    """위 대리(소화1팀): 주머니 모양 연어빛 몸 + 위쪽 식도 꼬리 + 파란 넥타이 + 사원증"""
    C0, L0 = 0xF59A8E, 0xFFD4CA
    cv.save(); cv.translate(x, y); cv.scale(s, s)
    shadow(cv, 150)
    feet(cv, 162, 0xE88A80)
    limb(cv, -138, 40, -176, 84, C0); limb(cv, 138, 30, 178, -6, C0)
    body = union(circle_path(14, 22, 136), circle_path(-62, -56, 78), oval_path(-44, -120, 70, 70))
    blob(cv, body, C0, L0, shade=0xF1A89C)
    # 식도 꼬리 끝
    cv.drawOval(skia.Rect.MakeXYWH(-80, -158, 52, 30), P(0xE88A80, a=170))
    face(cv, 14, 18, 1.0, mood, blush=0xFFB3C1)
    # 넥타이 + 사원증
    tie = skia.Path(); tie.moveTo(0, 88); tie.lineTo(30, 88); tie.lineTo(38, 112); tie.lineTo(15, 146); tie.lineTo(-8, 112); tie.close()
    cv.drawPath(tie, P(0x3D8BFF)); cv.drawPath(tie, P(INK, "stroke", 5))
    cv.drawRect(skia.Rect.MakeXYWH(2, 78, 26, 16), P(0x2C6FD6)); cv.drawRect(skia.Rect.MakeXYWH(2, 78, 26, 16), P(INK, "stroke", 4))
    cv.drawLine(-60, 58, -92, 100, P(INK, "stroke", 5))
    rrect(cv, -122, 96, 54, 66, 10, fill=WHITE, stroke=INK, sw=5)
    cv.drawCircle(-95, 120, 11, P(0xF5C842)); cv.drawLine(-112, 143, -78, 143, P(INK, "stroke", 4))
    cv.restore()


# ── CAST 등록은 이번 실행에서 하지 않았다 ──────────────────────────────
# chars.py 끝의 CAST 리스트는 캐릭터 소개용이고 렌더 경로가 읽지 않아 그대로 두었다.
# 저장소에 반영할 때 표를 채우고 싶으면 CAST에 아래 한 줄을 더한다(동작에는 영향 없음):
#     ("stomach", stomach, "위 대리", "Stomach · Digestion Team 1", "야식이 오면 제일 먼저 야근"),
