# 허상공방 쇼츠 업로더 인수인계 (영상을 만드는 쪽 → 유튜브에 올리는 쪽)

이 문서는 유튜브 업로드 키를 가진 쪽 Claude 계정(업로더)이 읽는다. 영상 제작은 다른 계정이 하고, 12시간마다 GitHub 공개 릴리스로 영상을 올린다. 업로더는 그 릴리스를 가져와 허상공방 채널(@dreamloom_studio)에 올린다.

## 흐름
1. 제작 쪽이 12시간마다 쇼츠 한 편을 만들어 공개 저장소 `mini-ok/ssoksok-channel-assets`의 **`shorts-outbox` 브랜치**에 넣는다(릴리스가 아니라 브랜치 파일).
2. 업로더가 `index.json`을 읽어 아직 올리지 않은 slug를 찾는다.
3. 그 폴더의 `video.mp4`와 `meta.json`을 내려받아 유튜브에 올린다.
4. 올린 slug와 영상 ID를 업로더 쪽 기록(예: `uploads.json`)에 남겨 중복을 막는다.

## 주소 (로그인 없이 읽힘)
- 목록: `https://raw.githubusercontent.com/mini-ok/ssoksok-channel-assets/shorts-outbox/index.json`
  - 형식: `{"items":[{"slug","dir","created"}, ...]}` — 오래된 것부터.
- 영상: `https://raw.githubusercontent.com/mini-ok/ssoksok-channel-assets/shorts-outbox/<dir>/video.mp4`
- 메타: `https://raw.githubusercontent.com/mini-ok/ssoksok-channel-assets/shorts-outbox/<dir>/meta.json`
- `meta.json` 항목: `slug`, `title_en`, `title_ko`, `desc_en`, `desc_ko`, `tags`, `related`(없으면 null), `file`, `created`(UTC).
- 영상은 GitHub 파일 한도(100MB) 안으로 다시 인코딩해 넣는다(1080×1920, H.264).
- 공개 저장소라 올라오는 순간 누구나 내려받을 수 있다.

## 가져오는 규칙
- 업로더 기록에 없는 slug만, `created` 순서대로 올린다.
- `video.mp4` 크기가 0이거나 `meta.json`이 없으면 올리지 않고 보고한다.
- 첫 항목 `fold42`(〈42번〉, 2026-11-24)부터 시작한다.

## 유튜브에 올릴 때 (채널 규칙)
- 채널: `@dreamloom_studio`. 올리기 전에 `channels.list(mine=true)`로 주소를 확인하고, 다르면 올리지 않는다.
- 기본 언어는 영어다. 영어 제목·설명에는 한글을 섞지 않는다. 한글 번역은 `localizations.ko`에 넣는다.
- 카테고리 1(영화/애니메이션), 아동용 아님, 구독자 알림 끔.
- 제목은 100자를 넘기지 않는다.
- 쇼츠의 '관련 동영상'은 API로 지정할 수 없다. 사람이 Studio에서 따로 연결한다.

## 이 저장소의 업로더 코드
같은 저장소의 `Code Animation/trivia/upload.py`가 위 규칙대로 올리는 스크립트다. `python3 upload.py <slug> <mp4> [--publish-at ...] [--dry-run]`로 쓴다. 이 스크립트를 그대로 써도 되고, 업로더 쪽에 이미 있는 코드를 써도 된다. 어느 쪽이든 위 규칙은 지킨다.

## 필요한 키 (업로더 쪽 환경에 이미 있거나 새로 만들어야 하는 것)
| 변수 | 비고 |
|---|---|
| `YT_CLIENT_ID`, `YT_CLIENT_SECRET` | 쏙쏙 채널에서 쓰는 값과 같다 |
| `YT_REFRESH_TOKEN_DREAMLOOM` | 허상공방 채널 전용. 쏙쏙 채널용 토큰은 쓸 수 없다. 새로 받아야 한다 |

토큰은 `docs/youtube_api_setup_guide.md` 단계 6-2를 다시 하되, 구글 로그인에서 채널(브랜드 계정) 선택 화면이 나오면 **허상공방(Dreamloom Studio)** 을 고른다. 받은 뒤 `channels.list(mine=true)` 응답의 `customUrl`이 `@dreamloom_studio`인지 확인한다.
키 값은 채팅, 로그, 커밋에 남기지 않는다.

## 쓰지 말 것 / 지킬 것
- 영상 제작 방법이나 작품 기획 내용을 공개 저장소에 옮겨 적지 않는다. 이 문서는 업로드에 필요한 것만 다룬다.
- 올리다 실패하면(쿼터, 토큰 만료 `invalid_grant`, 403) 같은 태그를 다시 시도하지 말고 이유를 보고한다.
- 제작 쪽은 이미 올라간 태그를 덮어쓰지 않는다(같은 slug는 다시 만들지 않음).
