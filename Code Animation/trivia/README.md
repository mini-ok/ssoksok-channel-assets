# trivia — 허상공방 지식 쇼츠(알쓸신잡풍) 자동 제작

에피소드 파일 하나(`episodes/<slug>.py`)만 쓰면 세로 쇼츠 한 편이 나온다. 12시간마다 예약 작업이 이 폴더로 한 편씩 만들어 올린다.

| 파일 | 하는 일 |
|---|---|
| `engine.py` | 장면 틀(hook·number·compare·steps·fact·answer), 영·한 글자 배치(`bi_layout`: 영어 위, 한글 아래, 크기 비슷), 종이 질감 합성, 장면 넘김, 끝 낙관 카드 |
| `audio.py` | 장면 시각표로 소리 자동 합성(가야금풍 튕김 고리, 거문고, 종이 휙, 막대 자랄 때 실소리, 숫자 셀 때 똑딱, 정답 북) |
| `render.py` | 프레임 PNG(두 프로세스). `--stills`로 검사용 정지 화면 |
| `make.sh` | 4초 구간 렌더 → mp4 → 소리 → `vfx.loud`로 음량 맞춰 붙이기 → `vfx.qa report` 검수 보고 |
| `upload.py` | YouTube Data API로 업로드(영어 원문 + 한국어 번역, 채널 확인, 기록) |
| `topics.md` | 출처를 확인한 주제 목록과 진행 상태 |
| `episodes/lightning_vs_sun.py` | **검증된 예시**(첫 편). 새 편은 이 파일을 본떠 쓴다 |
| `uploads.json` | 올린 기록(업로드 때 자동으로 덧붙음) |

## 새 편 만드는 순서
```bash
cd "Code Animation/trivia"
# 1) topics.md에서 다음 '대기' 주제 → 출처 다시 확인
# 2) episodes/<slug>.py 작성 (lightning_vs_sun.py 형식: 출처 docstring, BEATS, draw_<id> 함수, YT 메타데이터)
# 3) 정지 화면 검사: 장면마다 한두 장, 실제 크기(1080×1920)로 열어 본다
python3 render.py <slug> --stills /tmp/st 0.5 3 6 ...
# 4) 영상
./make.sh <slug> /home/claude/work/trivia/<slug>
# 5) 업로드(즉시 공개) — 환경 변수 YT_CLIENT_ID, YT_CLIENT_SECRET, YT_REFRESH_TOKEN_DREAMLOOM 필요
python3 upload.py <slug> /home/claude/work/trivia/<slug>/<slug>.mp4
```

## 에피소드 파일 쓰는 법
- docstring에 **출처 URL과 환산 계산**을 적는다(화면 숫자의 근거).
- `BEATS`: 장면 dict 목록. 종류별 필드는 `engine.py` 맨 위 설명. 장면 길이(dur)는 읽을 시간 기준: 질문 4~5초, 숫자 5~6초, 막대 비교 7~8초, 정답 5초.
- 글자는 항상 영·한 둘 다(`*_en`, `*_ko`). 크기를 따로 키우지 않는다 — `bi_layout`이 영어 = 한글 + 4px로 맞춘다.
- 영어판 숫자는 미터·피트(섭씨·화씨) 함께. `alt` 필드에 둘째 단위.
- 그림은 `draw_b<번호>(L, t, u, ep)` 함수로 cairo 도형(`S.circle`, `S.poly`, `S.ellipse`, `S.ring`, `card`)을 그린다. 층: `back`(뒤, 흐린 장식) · `mid` · `card` · `near`(앞) · `type`(글자).
  화면 아래쪽 1/3(y 1300~1900)이 비지 않게 그림을 둔다. 글자 카드(y 230~700 부근)와 겹치지 않게.
- `YT` dict: `title_en`(질문형 + ` #shorts`, 100자 이하, **한글 금지**), `title_ko`, `desc_en`(한글 금지, 답 2~3문장 + 'Paper cut-outs…' 줄 + Source 줄 + 제목 줄 + 해시태그), `desc_ko`, `tags`(15개 안팎), `related`(Studio에서 걸 롱폼 ID).
- 관련 동영상 고르는 기준: 빛지기(ONNdFZnFpvw: 바다·등대·폭풍), 홀씨(hMFAMtZduEg: 식물·바람·여행), 허수아비의 겨울(MaUM3k6Ltnk: 겨울·새·들판), 스물여덟 자(WXl74zoyXVg: 글자·한국 문화).

## 검사 기준(올리기 전)
- 모든 장면에서 글자가 화면 밖으로 나가거나 그림과 겹치지 않는다.
- 영어와 한글 크기가 비슷하고 영어가 위.
- 숫자·단위가 docstring의 출처와 같다. 막대 비교는 비율이 맞다.
- 길이 25~58초, 소리 있음, 1080×1920.
