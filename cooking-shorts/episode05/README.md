# 5편 · 근육 쉐프의 참치 감자전 / Tuna Potato Pancakes

사용자가 2026-10-30 승인한 대본으로 만든 한글·영문 영상. 기존 장기 캐릭터의 정체성을 유지하고 작업 도구를 제거한 뒤 요리 모자·앞치마를 적용했다. 쉐프 목소리는 Fenrir, 여성 해설은 Despina, 원음 기준 1.3배다.

## 구성과 근거

장기 쉐프·선정 이유 → 재료 → 손질·조리 → 여성 건강 근거 설명·큰 출처 → 조건 설명 → 캐릭터 유머 → 10초 고정 전체 레시피·엔딩.

건강 포인트: 근육 유지·보수에 필요한 단백질을 식사로 보태기.

선정 이유: 참치의 단백질이 근육 조직을 유지·보수하는 재료를 제공하므로 근육 쉐프가 요리한다.

근거: [NIH ODS · Protein and Muscle](https://ods.od.nih.gov/factsheets/ExerciseAndAthleticPerformance-Consumer/), 2026-10-30 확인. 이 요리 한 번의 근육 증가를 입증한 자료가 아니다. 운동과 충분한 식사도 필요하다.

주재료: 참치, 감자. 조리법·분량은 승인 대본 DRAFT_KO.md와 production.json을 따른다. 해외에서 구할 수 있는 일반 재료와 기본 도구를 사용한다. 실제 주방 조리·맛 평가는 수행하지 않았고 임상 효능을 보장하지 않는다.

## 음악·검증

사용 곡: `nimble_motifs.mp3`. 직전 편의 `buoyant_kitchen_groove.mp3`와 다른 곡이다. 실제 음악 스템과 원곡의 파형 상관을 비교한다.

1080×1920 / 24fps. output/은 한국어, output_en/은 영어다. 각 폴더의 verification.json에 전체 디코딩·음량·피크·레시피 고정·음악 검사, speech_qa.json에 원음 받아쓰기, encoded_speech_qa.json에 최종 MP4 받아쓰기를 저장한다. encoded_review.jpg는 실제 인코딩 화면이다.

## 재생성

저장소 루트에서 다음 명령을 사용한다. 언어는 ko 또는 en, 명령은 audio / preview / render / verify / check다.

```powershell
..\.venv-cooking\Scripts\python.exe cooking-shorts\produce_episodes.py 5 ko audio
..\.venv-cooking\Scripts\python.exe cooking-shorts\produce_episodes.py 5 ko preview
..\.venv-cooking\Scripts\python.exe cooking-shorts\produce_episodes.py 5 ko render
..\.venv-cooking\Scripts\python.exe cooking-shorts\produce_episodes.py 5 ko verify
..\.venv-cooking\Scripts\python.exe cooking-shorts\produce_episodes.py 5 ko check
```

package_episodes.py가 5·6편의 한글·영문 영상을 각각 업로드 폴더와 ZIP으로 만든다. 회차별 폴더는 `K:/AI채널/5편_참치감자전_업로드용`이다. 영상·자막·전체 레시피 이미지·업로드 문구·검증 결과·업로드 스크립트·안내를 포함한다. 기존 @ssoksok-health / @tinybodyco 인증과 건강요리 숏츠 재생목록을 사용한다.

인증 정보·MP4·WAV는 Git에 올리지 않는다. 실제 유튜브 업로드나 다른 AI에게 메시지 전송은 수행하지 않았다.
