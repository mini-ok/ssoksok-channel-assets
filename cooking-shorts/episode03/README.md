# 3편 최종 수정 · 심장 쉐프의 사과 땅콩버터 토스트

**버섯 달걀볶음은 장기 선정 이유가 부족해 미채택 초안이다. `output/`의 버섯 영상은 공개용 최종본으로 사용하지 않는다.**
최종 제작 경로는 `produce_toast.py`, `plan.json`, `audio_toast/`, `output_toast/`다.

## 장기와 건강 포인트

버터의 포화지방 대신 땅콩의 불포화지방을 선택하는 토스트다. 건강 포인트는 LDL 콜레스테롤 관리와 심장·혈관 건강을 위한 식습관이며, 따라서 심장 쉐프가 요리한다. 단순한 일반 영양 설명으로 캐릭터 선정 이유를 대신하지 않는다.

**쉐프 등장·선정 이유 → 재료 → 사과 썰기·스프레드 바르기·올리기 → 여성 해설의 건강 근거 설명 → 유머 → 캡처용 전체 레시피와 엔딩**

조리 후 여성 나레이션 두 장면:

> 포화지방을 불포화지방으로 바꿔 먹으면, 나쁜 콜레스테롤 관리에 도움이 돼요.
>
> 그래서 버터 대신 땅콩버터! 더 먹는 게 아니라 바꿔 먹는 게, 심장을 위한 포인트예요.

두 장면 모두 미국심장협회와 자료 주제를 본문 자막 수준의 큰 글씨로 표시한다. 근거는 [미국심장협회 Fats in Foods](https://www.heart.org/en/healthy-living/healthy-eating/eat-smart/fats/fats-in-foods)이며 2026-10-29 확인했다. 포화지방을 불포화지방으로 **대체**하는 식습관에 관한 근거이지, 토스트 1회 또는 땅콩버터 20g이 수치 개선을 보장한다는 의미가 아니다. 사과의 단독 효능을 주장하지 않는다.

## 레시피

1인 간식 / 약 3분. 통밀빵 1장, 사과 1/2개, 땅콩 100% 무가당·무염 땅콩버터 20g.

1. 사과는 씻어 씨를 빼고 얇게 썬다.
2. 빵에 땅콩버터를 고르게 바른다.
3. 사과를 차곡차곡 올린다.

빵은 취향에 따라 미리 구워도 된다. 실제 주방 조리·맛 평가는 수행하지 않았다.

## 영상·검증

1080×1920 / 24fps. 기존 종이 질감과 큰 자막, 밝은 심장 쉐프 Zubenelgenubi와 여성 해설 Despina, 1.3배 대사, 조리 효과음, 부드러운 전환, 10초 레시피 고정.

`produce_toast.py`는 기획서·장기 선정 이유·근거 필드·조리 후 여성 설명 순서를 합성/렌더 전에 점검한다. 건강 해설 누락을 실제로 거부하는 것도 시험했다. 이 점검은 구조 누락을 찾는 용도이며 근거의 의학적 타당성을 자동 판정하지 않는다.

최종 MP4 전체 디코딩·음량·피크·레시피 고정은 `output_toast/verification.json`, 원음 받아쓰기는 `speech_qa.json`, 최종 MP4 받아쓰기는 `encoded_speech_qa.json`, 실제 인코딩 화면은 `encoded_review.jpg`에 저장한다.

```powershell
..\.venv-cooking\Scripts\python.exe cooking-shorts\episode03\produce_toast.py audio
..\.venv-cooking\Scripts\python.exe cooking-shorts\episode03\produce_toast.py preview
..\.venv-cooking\Scripts\python.exe cooking-shorts\episode03\produce_toast.py render
..\.venv-cooking\Scripts\python.exe cooking-shorts\episode03\produce_toast.py verify
..\.venv-cooking\Scripts\python.exe cooking-shorts\episode03\check_encoded_speech.py toast
```

인증 파일은 저장소 밖에 두며 결과물에 포함하지 않는다. MP4·WAV는 반복 커밋하지 않는다. 업로드는 실행하지 않는다.

이번 3편은 심장으로 마무리하라는 사용자 지시를 따랐다. 다음 편부터는 가능한 한 다른 장기를 우선하며 건강 근거 적합성을 우선한다.
