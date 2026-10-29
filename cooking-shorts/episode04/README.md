# 4편 · 장 쉐프의 브로콜리 마늘볶음 (한글)

2026-10-29 사용자가 대본을 승인하고 즉시 제작을 요청한 한글판. [승인 대본](DRAFT_KO.md)과 [기획서](plan.json)에 따른다.

장 연구원(gut)의 고글·민트색 몸·더듬이를 유지하고 실험용 플라스크를 제거한 뒤 요리 모자와 앞치마를 적용했다. 장 쉐프는 기존 장 캐릭터 목소리 Aoede로 밝고 발랄하게, 여성 해설은 Despina로 녹음했다. 원음 기준 1.3배 속도다.

조리 뒤 여성 해설이 식이섬유와 충분한 수분이 원활한 배변을 돕는 이유를 설명하고, 미국 NIH·NIDDK 출처를 큰 글씨로 표시한다. 한 번 먹어서 변비가 치료된다고 주장하지 않는다. 출처: https://www.niddk.nih.gov/health-information/digestive-diseases/constipation/eating-diet-nutrition (2026-10-29 확인).

## 레시피

1인 곁들임 / 약 7분. 브로콜리 150g, 마늘 1쪽, 식용유 1작은술, 물 2큰술. 소금·후추는 선택.

1. 브로콜리는 씻어 작은 송이로 나누고 줄기는 얇게 썬다.
2. 팬에 브로콜리와 물을 넣고 뚜껑을 덮어 중불로 약 3분 익힌다.
3. 뚜껑을 열어 물기를 날리고 중약불로 낮춘다.
4. 기름과 다진 마늘을 넣고 약 1분 볶는다. 줄기가 단단하면 더 익힌다.

생브로콜리 대신 냉동 제품 사용 가능. 냉동 제품의 가열 안내를 우선하고 물과 시간을 조절한다. 마늘은 생략 가능하다. 해외에서도 구하기 쉬운 재료와 팬·뚜껑·칼을 사용한다. 실제 주방 조리·맛 평가는 수행하지 않았다.

## 음악과 출력

사용자 지시로 직전 편과 다른 `bgm/buoyant_kitchen_groove.mp3`를 사용했다. 3편은 `bgm/buant_pop_groove.mp3`였다. 파일 해시 비교에 더해 실제 혼합용 음악 스템과 원곡의 파형 상관을 비교해 선택한 곡이 사용됐는지 확인한다. 대사 구간에는 음악을 낮춘다.

- 1080×1920, 24fps. 종이 질감·큰 자막·조리 효과음·부드러운 전환.
- 엔딩의 전체 레시피 카드를 약 10초 고정한다.
- 영상: `output/쏙쏙건강요리_브로콜리마늘볶음_한글_v1.mp4`.
- 자막: `output/브로콜리마늘볶음_한글.srt`.
- 캡처용 레시피: `output/브로콜리마늘볶음_전체레시피.png`.
- 원음/최종 MP4 받아쓰기, 전체 프레임 디코딩·음량·레시피 고정·음악 검증 결과는 `output/` JSON에 저장한다.
- 다운로드 묶음: `K:/AI채널/쏙쏙건강요리_4편_한글_다운로드묶음.zip`.

```powershell
..\.venv-cooking\Scripts\python.exe cooking-shorts\episode04\produce.py audio
..\.venv-cooking\Scripts\python.exe cooking-shorts\episode04\produce.py preview
..\.venv-cooking\Scripts\python.exe cooking-shorts\episode04\produce.py render
..\.venv-cooking\Scripts\python.exe cooking-shorts\episode04\produce.py verify
..\.venv-cooking\Scripts\python.exe cooking-shorts\episode04\produce.py check
..\.venv-cooking\Scripts\python.exe cooking-shorts\episode04\package_download.py
```

MP4·WAV와 인증 파일은 저장소에 올리지 않는다. GitHub에는 코드·대본·기획서·자막·검증 결과·검수 정지화면을 저장한다. 한국어·영어 영상을 제작했으며 실제 유튜브 업로드는 실행하지 않았다.

## 영어판과 업로드 폴더

- `produce_en.py`가 승인한 4편 그림·동작·음악·건강 해설을 현지화한다. 장 쉐프 Aoede와 여성 해설 Despina, 1.3배 속도를 유지한다.
- 영어의 긴 자막은 3줄 배치로 글자 크기를 확보하고 이름표·자막판과 겹치지 않게 조정했다.
- 영어 제작: `produce_en.py audio`, `preview`, `render`, `verify`, `check`.
- 결과: `output_en/TinyBodyCo_GarlicBroccoli_EN.mp4`, 영어 자막·레시피 이미지·검증 JSON.
- `package_upload.py`가 `K:/AI채널/4편_브로콜리마늘볶음_업로드용` 폴더와 `K:/AI채널/브로콜리마늘볶음_한영_클라우드업로드묶음.zip`을 만든다.
- 두 언어 영상·자막·레시피·검증 결과·업로드 메타데이터·실행 스크립트·안내를 포함한다. 인증 정보는 포함하지 않는다.
- 한국어 @ssoksok-health, 영어 @tinybodyco와 기존 건강요리 숏츠 재생목록을 사용한다. 업로드 완료 기록은 언어+파일 해시별로 구분하며 채널·실제 공개 상태를 확인한다.
- 업로드 스크립트는 `episode03/test_upload_package.py`에 이 폴더 경로를 넘겨 API 모의 테스트한다. 실제 인증·업로드 결과 검증과 구분한다.
