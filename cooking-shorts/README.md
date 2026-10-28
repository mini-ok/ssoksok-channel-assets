# 쏙쏙 건강요리 / Body Kitchen

## 최신 영상 v3 / 종이 질감 + 두 목소리

[종이 질감 영상 / 약 48초](output_v3/쏙쏙건강요리_바나나오트밀_종이질감_v3.mp4)

쉐프 Puck은 밝고 톡톡 튀는 연기로 조리 대사를, 여성 내레이터 Despina는 재료와 건강 설명을 맡습니다. 대사 1.3배, 전체 레시피 카드 고정 유지. 전체 디코딩·음량·전환 검수 통과.

재생성: `python cooking-shorts/revision_v3.py render`


쏙쏙 건강백과·Tiny Body Co.의 기존 장기 캐릭터로 만든 건강요리 숏츠 제작 자료입니다.

## 기존 채널 화풍에 맞춘 종이 질감 시안

- [종이 질감 적용 화면](style_reference/종이질감_요리쇼츠_스타일비교.png)
- [이전 시안과 나란히 비교](style_reference/종이질감_이전시안_비교.jpg)

첨부 참고 화면의 도톰한 산호색·하늘색 자막판, 포근한 종이 배경, 캐릭터의 질감과 그림자를
기존 채널 `paper.py`의 실제 puff 렌더로 적용한 **정지 화면 시안**입니다.
47초 영상은 아래 v2이며, 이 종이 질감 시안을 적용한 영상 전체는 아직 렌더하지 않았습니다.
재생성: `python cooking-shorts/style_reference_still.py`.

## 최신 검토본: 바나나 오트밀 v2

- [한국어 영상 / 47초 / 대사 1.3배](output_v2/쏙쏙건강요리_바나나오트밀_전환비교_v2.mp4)
- [전체 레시피 / 캡처용 PNG](output_v2/바나나오트밀_캡처용_레시피.png)
- [전환 비교 안내](output_v2/전환_비교_안내.md) / [자막 SRT](output_v2/heart_ko_v2.srt)
- [인코딩 화면 검수](output_v2/encoded_review.jpg) / [검증 수치](output_v2/verification_v2.json)

우상단 **쏙쏙 건강요리**, 상단 **오늘의 요리사 : 심장 쉐프**.
엔딩은 **구독은 사원증 발급! 좋아요는 보너스!**
마지막 약 9초 동안 요리 제목·재료 양·전체 조리법을 고정합니다.
하단 의료진 상담 안내는 화면에서 제거했습니다. 큰 글자와 일정한 자막 영역으로 정리했습니다.

전환 선택: A 00:03.2 부드러운 겹침 / B 00:17.2 살짝 확대 / C 00:21.2 접시 원형 연결 / D 00:37.4 카드 펼침.

## 첫 시안 보관

| 요리 | 한국어 | 영어 |
|---|---|---|
| 심장 / 바나나 오트밀 | [MP4](output/heart_ko.mp4) | [MP4](output/heart_en.mp4) |
| 간 / 병아리콩 샐러드 | [MP4](output/liver_ko.mp4) | [MP4](output/liver_en.mp4) |

[초기 시안 레시피·출처·검증 안내](INITIAL_SAMPLES.md).
최신 요청사항은 v2에 적용했으며 첫 시안은 변경 이력용으로 보관했습니다.

## 폴더와 코드

- `output_v2/`: 최신 샘플 한 편과 레시피·전환 안내·검증 결과.
- `output/`: 초기 한·영 샘플 네 편.
- `audio/`: 재렌더링에 사용할 캐릭터 대사 WAV와 타임라인. 인증 파일이 아닙니다.
- `revision_v2.py`: 최신 자막 배치·4가지 전환·캡처용 카드·1.3배 대사 믹싱.
- `render.py`, `episodes.py`: 공통 캐릭터·소품·조리 동작과 초기 한·영 대본.
- `runtime/`: 기존 엔진을 바탕으로 한 종이 캐릭터 렌더와 채널 폰트.
- `verify_v2.py`: 최종 MP4 전체 디코딩·음량·전환 연속성·레시피 고정 검사.

## 재생성

저장소 루트에서 Python 3.12 기준:

```bash
python -m venv .venv-cooking
# 가상환경을 활성화한 다음
python -m pip install -r cooking-shorts/requirements.txt
python cooking-shorts/revision_v2.py preview
python cooking-shorts/revision_v2.py render
python cooking-shorts/verify_v2.py
```

기존 음성 WAV를 재사용하는 렌더는 클라우드 인증이 필요 없습니다.
새 음성을 만들 때만 Google Application Default Credentials를 외부에서 설정하세요.
`GOOGLE_APPLICATION_CREDENTIALS`를 쓰는 경우 저장소 밖의 서비스 계정 JSON 경로를 지정합니다.
프로젝트는 해당 TTS API 권한·사용 설정이 있어야 합니다. 키·토큰·인증 JSON은 저장소에 넣지 않습니다.

`make_audio.py`는 WAV가 없을 때만 새로 합성합니다. 대사를 바꾸면 해당 WAV를 별도로 갱신해야 합니다.
`revision_v2.py audio`도 같은 캐시 원칙이며, `render` 단계에서 초기 음성 속도를 원음 대비 1.30배로 맞춥니다.
배경음악은 저장소 공용 `bgm/`을 참조합니다. 캐릭터·폰트·목소리 배정은 기존 채널 자산을 따릅니다.

## 검증 상태

최신 영상: 1080×1920 / 24fps / 47.417초. 1,138프레임 전체 디코딩 통과.
통합 음량 -15.44 LUFS, 트루피크 -1.18 dBTP, 음성·음악의 최소 차이 13.7dB.
새 엔딩은 최종 인코딩 파일의 1.3배 음성을 받아써 요청 문구와 일치함을 확인했습니다.
전환 중간 프레임·최종 배치와 약 8.85초의 레시피 고정을 확인했습니다.
이번 자료는 검토용 샘플이며 유튜브 업로드·예약 변경은 실행하지 않았습니다.
실제 주방 조리·맛 평가는 수행하지 않았습니다.
