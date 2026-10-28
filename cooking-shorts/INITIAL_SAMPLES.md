# 몸속 식당 / Body Kitchen — 건강요리 숏츠 샘플

쏙쏙 건강백과·Tiny Body Co.의 기존 캐릭터가 직접 요리하는 신규 시리즈 샘플입니다. 오전에는 심장 셰프의 아침, 오후에는 간 셰프의 간단한 곁들임을 짝으로 구성했습니다. 이번 결과물은 샘플 파일이며 유튜브 업로드·기존 예약 변경·GitHub push는 하지 않았습니다.

## 결과물

| 요리 | 한국어 | 영어 |
|---|---|---|
| 심장 셰프 / 바나나 오트밀 | output/heart_ko.mp4 | output/heart_en.mp4 |
| 간 셰프 / 병아리콩 샐러드 | output/liver_ko.mp4 | output/liver_en.mp4 |

1080×1920 / 24fps / H.264 + AAC. 각 언어의 음성·자막은 별도로 제작했습니다. 내장 자막 외에 SRT 파일, 장면별 미리보기와 스토리보드도 output 폴더에 있습니다.

## 그대로 활용한 채널 자산

- 원본: https://github.com/mini-ok/ssoksok-channel-assets
- 캐릭터·표정: engine/paper_story/chars.py. 심장의 분홍 하트 몸과 파란 모자, 간의 노란 몸과 민트 두건을 유지하고 업무용 상자·대걸레 대신 요리사 모자·앞치마를 더했습니다.
- 종이 질감·음영: engine/paper_story/paper.py의 puff_char 렌더를 재사용했습니다. 재료·도구는 같은 색감의 코드 기반 도형으로 추가했습니다.
- 폰트: 저장소의 Jua, Black Han Sans, Geist.
- 목소리: CHARACTER_BIBLE.md에 지정된 심장 Puck / 간 Charon. 기존 TTS 프로젝트를 사용했으며 인증 값은 소스·결과물에 포함하지 않았습니다.
- 음악: 오전 심장 편 nimble_motifs.mp3 / 오후 간 편 buoyant_kitchen_groove.mp3. 말소리 구간에서 음악을 낮췄습니다.

## 레시피 1 / 심장 셰프의 바나나 오트밀

1인분. 롤드 오트 40g, 물 200mL, 바나나 1/2개.

1. 작은 냄비에 귀리와 물을 넣습니다.
2. 끓기 시작하면 약불로 줄이고 저어 부드러워질 때까지 익힙니다. 약 5분을 기준으로 하되 제품 조리 안내를 따릅니다. 농도가 되직하면 물을 조금 더 넣습니다.
3. 바나나를 얇게 썰어 익힌 오트밀 위에 올립니다. 설탕은 추가하지 않습니다.

대체: 바나나 대신 잘 익은 배나 사과를 잘게 썰어 쓸 수 있습니다. 사과가 단단하면 귀리와 함께 익힙니다. 셀리악병 등으로 글루텐을 제한한다면 인증된 글루텐 프리 귀리를 선택해야 합니다.

영상의 건강 메시지: 귀리의 수용성 식이섬유가 포함된 아침 식사 아이디어. 이 한 그릇으로 심장질환을 치료하거나 특정 수치가 변한다고 주장하지 않습니다.

직접 열람한 근거: American Heart Association, “Take a fresh look at oatmeal – it's not as simple as you think”, 2022-09-01.
https://www.heart.org/en/news/2022/09/01/take-a-fresh-look-at-oatmeal-its-not-as-simple-as-you-think

## 레시피 2 / 간 셰프의 병아리콩 샐러드

1인 곁들임. 익힌 병아리콩 100g, 오이 1/4개, 작은 토마토 1개, 레몬즙 1작은술(5mL), 올리브유 1작은술(5mL). 약 3분은 익힌 콩을 사용하는 간단 조립 기준의 예상 시간입니다.

1. 통조림 콩은 헹구고 물기를 뺍니다. 가능하면 무염 제품을 선택합니다. 마른 콩을 그대로 넣지 않습니다.
2. 씻은 오이·토마토를 한입 크기로 작게 썹니다.
3. 볼에 모두 넣고 레몬즙·올리브유를 더해 부드럽게 섞습니다.

대체: 병아리콩 대신 완전히 익힌 흰콩이나 렌틸콩을 쓸 수 있습니다. 레몬이 없으면 식초를 소량씩 더해 맛을 조절합니다. 이 샐러드는 곁들임이며 한 끼 전체의 영양을 보장하지 않습니다.

영상의 건강 메시지: 콩·채소·불포화지방을 활용한 식사 패턴. 특정 음식의 간 해독 효과나 지방간 치료 효과를 주장하지 않으며 “해독 마법은 없다”는 대사를 넣었습니다.

직접 열람한 근거:

- Cambridge University Hospitals NHS, Nutritional Information for MASLD. 콩류·채소·통곡물·불포화지방을 포함하는 지중해식 식사 패턴을 설명합니다.
https://www.cuh.nhs.uk/patient-information/metabolic-dysfunction-associated-steatotic-liver-disease-masld/
- NIDDK, Eating, Diet, & Nutrition for NAFLD & NASH. 건강한 식사·적절한 양·건강한 체중 관리에 관한 일반 안내입니다.
https://www.niddk.nih.gov/health-information/liver-disease/nafld-nash/eating-diet-nutrition

특정 질환·알레르기·식사 제한이 있는 사람의 개인 식단 처방은 아닙니다. 실제 주방 조리·맛 평가는 수행하지 않았고, 위 재료와 조리법으로 구성한 애니메이션 샘플입니다.

## 완성 파일 검증 결과

- 최종 MP4 4편을 PyAV와 FFmpeg로 끝까지 디코딩했습니다. 1080×1920, 24fps, 영상·음성 스트림을 확인했고 디코딩 오류는 없었습니다.
- 길이: 심장 한국어 41.92초 / 영어 42.29초, 간 한국어 43.58초 / 영어 43.92초.
- 최종 통합 음량: 약 -15.4 LUFS. 트루피크 약 -1.3 dBTP. 말소리가 있는 3초 구간에서 음성·음악의 최소 차이 12.9~14.4dB를 확인했습니다. 영어 간 편은 검수 후 음악을 추가로 3.1dB 낮췄습니다.
- 대사 40개를 다국어 음성 인식으로 대조했습니다. 한국어 재료명·수량 등은 더 큰 모델로 재확인했습니다. 숫자 표기·동음어·일부 조사에 인식 차이가 있으므로 사람이 직접 청취한 전사 검수와 동일하다고 주장하지 않습니다. speech_qa_reviewed.json에 예상 대사와 인식 결과가 있습니다.
- 장면별 스토리보드와 실제 인코딩 파일에서 뽑은 화면을 열어 한·영 배치·조리 도구·자막 줄바꿈을 확인했습니다.
- 원본 캐릭터 엔진에 덧붙인 손과 도구의 연결을 수정했고, 완성 영상에서 다시 확인했습니다.
- 상세 수치: output/verification.json. 주방에서 직접 조리하거나 맛을 평가한 결과는 아닙니다.

## 재생성 명령

워크스페이스의 `.venv-cooking/Scripts/python.exe`로 실행합니다.

```powershell
.\.venv-cooking\Scripts\python.exe cooking_shorts_sample\make_audio.py
.\.venv-cooking\Scripts\python.exe cooking_shorts_sample\render.py preview heart ko
.\.venv-cooking\Scripts\python.exe cooking_shorts_sample\render.py render heart ko
```

topic은 heart/liver, lang은 ko/en입니다. 대본·계량·현지화는 episodes.py, 조리 움직임은 render.py에 있습니다. 기존 자산 저장소는 읽기용으로 복제했고 원격 저장소를 변경하지 않았습니다.
