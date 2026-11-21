# 허상공방 유튜브 채널 운영 자료 (Dreamloom Studio)

다른 AI·새 세션이 채널 업로드를 이어서 할 때 읽는 문서. 최종 갱신 2026-11-21.

| 파일 | 내용 |
|---|---|
| `README.md` (이 파일) | 채널 설정, 제목·설명 규칙, 업로드 체크리스트, Studio 조작 메모 |
| `videos.md` | 올린 영상 전부의 제목(EN/KO)·설명(EN/KO)·태그·관련 동영상·공개 상태 |
| `shorts_playbook.md` | 쇼츠 두 갈래(작품 예고 쇼츠, 종이 지식 쇼츠) 만드는 법과 올리는 법 |
| `tools/make_teaser_short.py` | 가로 작품 → 세로 예고 쇼츠(4:3 화면 + 위아래 자막) |
| `tools/render_paper_short.sh` | 종이 지식 쇼츠(haedal·simhae·hive) 렌더·소리 합성 |

## 1. 채널 기본 정보
- 채널 ID `UCpSXDQ-M-Z6Hen-BJV60obA`, 핸들 `@dreamloom_studio`, 국가 대한민국.
- 표시 이름: 채널 페이지는 아직 "허상공방"으로 보인다. "Dreamloom Studio · 허상공방"으로 바꾸는 요청을 넣은 적 있음(이름 변경은 14일에 2번까지).
- 링크: GoXoN (goxon.kr). 재생목록: 아직 없음.
- 전화 인증 완료(번호 하나로 1년에 채널 2개까지).
- 채널 설명(한·영 같은 글):

```
허상공방 (虛像工房) · Dreamloom Studio

[KR]
존재하지 않는 것을 짓는 작은 공방, 허상공방(虛像工房)입니다.
코드로 한 프레임씩 짜낸 대사 없는 단편 애니메이션과,
알아두면 쓸모 있는 상식을 모션그래픽으로 담습니다.

▶ 롱폼 | 이야기가 있는 코드 애니메이션 — 매주 1~2편
▶ 쇼츠 | 짧고 선명한 상식 모션그래픽

[EN]
Dreamloom Studio — Heosang Gongbang (허상공방 · 虛像工房),
"a workshop of illusions."
Wordless short films woven frame by frame in code,
and everyday knowledge brought to life in motion graphics.

▶ Long-form | Story-driven code animation — 1–2 new films every week
▶ Shorts | Bite-sized knowledge, in motion

Directed by L.S.M · Produced by GoXoN — goxon.kr
```

- 채널 키워드: `허상공방 虛像工房 "Dreamloom Studio" "Heosang Gongbang" "코드 애니메이션" "code animation" "단편 애니메이션" "animated short" "대사 없는 애니메이션" "wordless animation" 모션그래픽 "motion graphics" "종이 애니메이션" "수묵 애니메이션" "상식 쇼츠" "힐링 애니메이션" "healing animation" "relaxing animation" "cozy animation" "감성 애니메이션" "animación relajante" "cortometraje animado" "animación sin diálogos" 癒しアニメ 短編アニメ`

## 2. 영상마다 지키는 규칙 (사용자 지시)
- **기본 언어는 영어.** 제목·설명 원문은 영어로 쓰고, 한국어는 Studio '언어' 탭의 번역(제목·설명)으로 넣는다. 한국 시청자에게는 한국어판이 보인다.
- **영어 설명에는 한글을 한 글자도 넣지 않는다**(ㆍ 같은 옛 글자 포함). 한글 이름이 필요하면 로마자(Heosang Gongbang, Jiibi)로.
- 설명 첫 2~3줄은 작품 소개글(이야기의 한 줄 요약 + 주제 한 줄). 첫 두 줄이 '더보기' 위와 검색 미리보기에 나온다.
- 단위: 영어판은 피트·마일을 함께 쓴다(예: 8,849 m / 29,032 ft).
- **쇼츠 화면 글자(예고·지식 쇼츠 모두)는 영어와 한글을 비슷한 크기로**, 영어를 위에 둔다. 자세한 크기는 `shorts_playbook.md` A-3·B-2a.
- 사실·숫자는 확인한 것만 쓴다. 확인 안 된 수치(예: "수백만 명")는 쓰지 않는다.
- 카테고리 `영화/애니메이션`, 동영상 언어 `영어`, 제목 및 설명 언어 `영어`, `아동용 아님`.
- 고정 댓글은 사용자가 요청할 때만 단다(초안만 있음).
- 영상 파일은 Claude가 첨부해 올릴 수 없다. 사용자가 Studio에 끌어다 놓아 초안으로 올리면, 그 뒤 메타데이터·공개는 Claude가 한다.

### 롱폼 제목 형식
- EN: `Name | 한 줄 훅 — Animated Short`
- KO: `한글명 | 한 줄 — 대사 없는 단편 애니메이션`

### 롱폼 설명 형식
```
(소개글 3~4줄)

NAME · 길이 · wordless · made with code
(필요하면 기법 한 줄)
Directed by L.S.M · Dreamloom Studio (Heosang Gongbang)

#animation #shortfilm #wordless
```
KO:
```
(소개글 3~4줄)

한글명 ENGLISH NAME · 길이 · 대사 없음 · 코드로 만든 애니메이션
Directed by L.S.M · 허상공방 (虛像工房) Dreamloom Studio

#단편애니메이션 #애니메이션 #animation
```
- 태그: 작품명(한·영), 소재어(한·영), `단편 애니메이션, animated short, 대사 없는 애니메이션, wordless animation, 코드 애니메이션(또는 기법), 허상공방, Dreamloom Studio`. 15개 안팎, 관련 없는 태그는 넣지 않는다.
- 소개글의 출처: 작품 폴더 README의 '로그라인'과 '주제'(예: `keeper/README.md`). 새 작품도 README 로그라인을 다듬어 소개글로 쓴다.

### 쇼츠 제목·설명 형식 → `shorts_playbook.md`

## 3. 업로드 체크리스트 (초안 → 공개)
1. 사용자가 파일을 올려 초안이 생기면, Studio 콘텐츠 목록에서 동영상 ID를 확인한다.
2. `/video/ID/edit`에서 제목·설명(영어), '자세히 보기' → 태그, 제목 및 설명 언어 `영어`, 카테고리 확인, `아니요, 아동용이 아닙니다` → 저장.
3. 쇼츠는 오른쪽 '관련 동영상'에 이어 볼 롱폼을 고른다(쇼츠에서 누를 수 있는 유일한 링크).
4. `/video/ID/translations` → 언어 추가 `한국어` → 제목·설명 입력 → 업데이트(게시됨 확인).
5. 상단 '초안 수정'으로 업로드 창을 열고 '공개 상태' 단계로 가서 `공개` 또는 `예약` → 게시/예약.
6. 확인: youtube.com에서 `/watch?v=ID&hl=ko` 페이지 HTML의 제목·설명이 바뀌었는지 본다.

## 4. Studio 조작 메모 (브라우저 자동화용)
- 제목 편집기 `[contenteditable=true][aria-label^="동영상을 설명하는 제목"]`, 설명 `[aria-label^="시청자에게 동영상"]`. 내용 전체를 Range로 선택한 뒤 키보드 입력(type)으로 덮어쓴다(이 방법으로 저장까지 확인함).
- 태그 입력 `input[aria-label="태그"]`: 쉼표로 이어 쓰고 Enter.
- 저장 버튼 `#save`: 저장이 끝나면 `aria-disabled="true"`로 돌아간다.
- 드롭다운 항목은 `tp-yt-paper-item` 중 보이는 것(offsetParent≠null)을 innerText로 찾아 클릭.
- 번역 창: 표의 '한국어' 행 왼쪽(언어 이름)을 누르면 편집 창이 열린다(오른쪽 화살표는 '삭제'만 나옴). 창의 '업데이트' 버튼 위치는 상단 알림 띠(초안 표시) 유무에 따라 위아래로 바뀌니 누르기 전 화면을 다시 본다.
- 예약: 공개 상태 단계 → '예약' 펼치기 → 날짜 달력에서 날짜, 시간 칸을 눌러 목록에서 `오후 2:00` 같은 항목 선택(시간 칸에 직접 타자는 안 먹음).
- 쇼츠 설명란·댓글의 링크는 눌리지 않는다. 롱폼으로 보내는 길은 '관련 동영상' 하나.

## 5. 지금까지의 업로드 일정
- 2026-11-19: 롱폼 3편 공개(빛지기, 홀씨, 허수아비의 겨울).
- 2026-11-20: 예고 쇼츠 4편, 4시간 간격 예약 공개(허수아비② → 빛지기 → 홀씨 → 허수아비①).
- 2026-11-21: 〈스물여덟 자〉 공개. 지식 쇼츠: 해의 달력 공개(오전), 얼마나 깊을까 14:00, 벌집 18:00 예약(KST).
- 초안 대기: 〈심장의 하루〉(XJ885MNReHI), 〈종이 나방〉(xrDw1BNhQ_g). 〈점〉(Zj7nsXlh_Ts)은 일부 공개 상태.
- 하루에 여러 편이면 4시간 간격으로 나눠 예약한다.
