# 6편 · 면역 쉐프의 당근 달걀찜 / Carrot Steamed Eggs

사용자가 2026-10-30 승인한 대본으로 만든 한글·영문 영상. 기존 장기 캐릭터의 정체성을 유지하고 작업 도구를 제거한 뒤 요리 모자·앞치마를 적용했다. 쉐프 목소리는 Kore, 여성 해설은 Despina, 원음 기준 1.3배다.

## 구성과 근거

장기 쉐프·선정 이유 → 재료 → 손질·조리 → 여성 건강 근거 설명·큰 출처 → 조건 설명 → 캐릭터 유머 → 10초 고정 전체 레시피·엔딩.

건강 포인트: 비타민 A와 정상적인 면역 기능.

선정 이유: 당근의 베타카로틴이 비타민 A 공급에 기여하며 비타민 A는 정상 면역 기능에 필요하므로 면역 쉐프가 요리한다.

근거: [NIH ODS · Vitamin A and Carotenoids](https://ods.od.nih.gov/factsheets/VitaminA-Consumer/), 2026-10-30 확인. 더 먹을수록 면역력이 강해지거나 감염이 예방된다는 뜻이 아니다. 레시피 자체의 임상 효과나 정확한 전환량을 주장하지 않는다.

주재료: 당근, 달걀. 조리법·분량은 승인 대본 DRAFT_KO.md와 production.json을 따른다. 해외에서 구할 수 있는 일반 재료와 기본 도구를 사용한다. 실제 주방 조리·맛 평가는 수행하지 않았고 임상 효능을 보장하지 않는다.

## 음악·검증

사용 곡: `buant_pop_groove.mp3`. 직전 편의 `nimble_motifs.mp3`와 다른 곡이다. 실제 음악 스템과 원곡의 파형 상관을 비교한다.

1080×1920 / 24fps. output/은 한국어, output_en/은 영어다. 각 폴더의 verification.json에 전체 디코딩·음량·피크·레시피 고정·음악 검사, speech_qa.json에 원음 받아쓰기, encoded_speech_qa.json에 최종 MP4 받아쓰기를 저장한다. encoded_review.jpg는 실제 인코딩 화면이다.

## 재생성

저장소 루트에서 다음 명령을 사용한다. 언어는 ko 또는 en, 명령은 audio / preview / render / verify / check다.

```powershell
..\.venv-cooking\Scripts\python.exe cooking-shorts\produce_episodes.py 6 ko audio
..\.venv-cooking\Scripts\python.exe cooking-shorts\produce_episodes.py 6 ko preview
..\.venv-cooking\Scripts\python.exe cooking-shorts\produce_episodes.py 6 ko render
..\.venv-cooking\Scripts\python.exe cooking-shorts\produce_episodes.py 6 ko verify
..\.venv-cooking\Scripts\python.exe cooking-shorts\produce_episodes.py 6 ko check
```

package_episodes.py가 5·6편의 한글·영문 영상을 각각 업로드 폴더와 ZIP으로 만든다. 회차별 폴더는 `K:/AI채널/6편_당근달걀찜_업로드용`이다. 영상·자막·전체 레시피 이미지·업로드 문구·검증 결과·업로드 스크립트·안내를 포함한다. 기존 @ssoksok-health / @tinybodyco 인증과 건강요리 숏츠 재생목록을 사용한다.

인증 정보·MP4·WAV는 Git에 올리지 않는다. 실제 유튜브 업로드나 다른 AI에게 메시지 전송은 수행하지 않았다.

연기·발음 검수 과정에서 첫 대사만 "당근, 통과! 면역팀을 위한 달걀찜, 제가 만들게요!"로 다듬었다. 조리법과 건강 근거 설명은 승인 내용 그대로다.
