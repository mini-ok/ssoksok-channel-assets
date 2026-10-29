# 3편 · 버섯 달걀볶음 (한글)

사용자가 승인한 버섯·달걀 팬 요리. 1·2편의 주재료와 샐러드/죽 스타일을 피했다. 주재료와 비슷한 요리 스타일은 최소 10편을 사이에 두고 다시 사용하며, 부재료와 양념은 재사용 가능하다.

## 영상

- 세로 1080×1920, 24fps. 기존 종이 질감 배경·장기 캐릭터·자막판 사용.
- 심장 쉐프: Zubenelgenubi. 여성 해설: Despina. 활기찬 대사, 원음 기준 1.3배.
- 썰기·볶기·붓기·접으며 젓기 동작과 조리 효과음. 겹침과 작은 확대 전환.
- 엔딩에 제목·재료·조리법 전체를 10초 표시. 요청한 구독/좋아요 대사 유지.
- 기존 의료 안내 하단 문구 없음. 조리 참고 출처는 본문 자막 수준의 큰 글씨.

## 레시피

1인 곁들임 / 약 10분. 양송이버섯 100g, 달걀 2개, 식용유 1작은술. 소금·후추는 취향껏 약간.

1. 버섯은 손질해 얇게 썰고 달걀은 푼다.
2. 기름 두른 팬에 버섯을 중불로 볶아 물기를 날린다.
3. 중약불로 낮추고 달걀을 넣는다.
4. 가장자리에서 가운데로 살살 접으며 흐르는 달걀이 없도록 완전히 익힌다.

캐나다 보건부의 [Egg and veggie scramble](https://www.canada.ca/en/health-canada/services/food-guide/eating-support/kitchen/recipes/egg-veggie-scramble.html)에 나온 채소를 먼저 볶고 달걀을 넣어 익히는 조리 순서를 참고했다. 분량·재료를 단순화한 자체 레시피로, 원문 그대로의 공식 레시피나 영양 수치가 아니다. 실제 주방 조리·맛 평가는 수행하지 않았다.

## 재생성

저장소 루트에서 외부 Python 가상환경으로 아래 명령을 실행한다. 음성 합성 인증 파일은 저장소 밖 `K:/AI채널/tts/`에 보관하며 결과물에 포함하지 않는다.

```powershell
..\.venv-cooking\Scripts\python.exe cooking-shorts\episode03\produce.py audio
..\.venv-cooking\Scripts\python.exe cooking-shorts\episode03\produce.py preview
..\.venv-cooking\Scripts\python.exe cooking-shorts\episode03\produce.py render
..\.venv-cooking\Scripts\python.exe cooking-shorts\episode03\produce.py verify
```

음성 받아쓰기 결과는 `output/speech_qa.json`, 전체 디코딩·음량·정지 레시피 검증은 `output/verification.json`, 인코딩 후 실제 화면은 `output/encoded_review.jpg`에 저장한다. 영상과 WAV는 Git에 반복 커밋하지 않는다. 업로드는 이 제작 스크립트에서 실행하지 않는다.
