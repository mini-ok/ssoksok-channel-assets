# 유튜브 자동 업로드 준비 가이드 (구글 클라우드 한 번 설정)

목표: 예약이 두 채널(쏙쏙 건강백과 @ssoksok-health, Tiny Body Co. @tinybodyco)에 영상을 올릴 수 있게, 아래 4개 값을 환경에 등록한다.

| 변수 이름 | 무엇 | 얻는 곳 |
|---|---|---|
| `YT_CLIENT_ID` | OAuth 클라이언트 ID | 단계 5 |
| `YT_CLIENT_SECRET` | OAuth 클라이언트 보안 비밀 | 단계 5 |
| `YT_REFRESH_TOKEN_KO` | 쏙쏙 건강백과 채널용 리프레시 토큰 | 단계 6 |
| `YT_REFRESH_TOKEN_EN` | Tiny Body Co. 채널용 리프레시 토큰 | 단계 6 |

소요 시간은 약 20~30분이다. 화면 이름은 구글이 가끔 바꾸므로 한국어 화면에서는 아래 영어 이름과 조금 다르게 보일 수 있다.

**지켜야 할 것**: 클라이언트 보안 비밀과 리프레시 토큰은 비밀번호와 같다. 채팅에 붙여넣지 말고 단계 7의 환경 설정에만 입력한다. 유출이 의심되면 https://myaccount.google.com/permissions 에서 앱 접근을 제거하고 새로 발급한다.

---

## 단계 1. 프로젝트 만들기
1. https://console.cloud.google.com/projectcreate 로 이동한다. (영상 채널을 가진 구글 계정이 아니어도 되지만, 편하게 채널 소유 계정 하나로 하는 것을 권한다.)
2. 프로젝트 이름: `ssoksok-youtube` 등 아무 이름. 만들기.
3. 상단 프로젝트 선택기에서 방금 만든 프로젝트가 선택됐는지 확인한다.

## 단계 2. YouTube Data API v3 켜기
1. https://console.cloud.google.com/apis/library/youtube.googleapis.com 으로 이동한다.
2. **사용(Enable)** 을 누른다.

## 단계 3. 동의 화면(Google Auth Platform) 설정
1. https://console.cloud.google.com/auth/overview 로 이동해 **시작하기(Get started)** 를 누른다.
2. 앱 정보: 앱 이름(예: `쏙쏙 영상 업로더`), 사용자 지원 이메일을 입력한다.
3. 대상(Audience): **외부(External)** 를 선택한다.
4. 연락처 이메일을 입력하고 약관에 동의한 뒤 만들기.
5. 왼쪽 메뉴는 Overview / Branding / Audience / Clients / Data Access / Verification Center 로 구성된다.

## 단계 4. 권한 범위(Data Access) 추가
1. 왼쪽 **Data Access** → **범위 추가 또는 삭제(Add or remove scopes)**.
2. 아래 둘을 추가한다. (목록에서 "YouTube Data API v3"를 찾거나, 아래 주소를 "직접 범위 추가"에 붙여넣는다.)
   - `https://www.googleapis.com/auth/youtube`
   - `https://www.googleapis.com/auth/youtube.force-ssl`
3. 저장.

   각 범위의 역할: `youtube`는 영상 업로드·재생목록·썸네일 설정까지 모두 포함하고, `youtube.force-ssl`은 댓글 작성에 쓴다. `youtube.upload`만 받으면 업로드만 되고 재생목록·첫 댓글은 권한 오류로 건너뛴다.

## 단계 5. OAuth 클라이언트 만들기 (YT_CLIENT_ID, YT_CLIENT_SECRET)
1. 왼쪽 **Clients** → **클라이언트 만들기(Create client)**.
2. 애플리케이션 유형: **웹 애플리케이션(Web application)**. 이름은 아무거나.
3. **승인된 리디렉션 URI(Authorized redirect URIs)** 에 아래를 **정확히** 추가한다. (글자 하나라도 다르면 `redirect_uri_mismatch` 오류가 난다.)
   ```
   https://developers.google.com/oauthplayground
   ```
4. 만들기. 나오는 창의 **클라이언트 ID**와 **클라이언트 보안 비밀**을 안전한 곳에 복사해 둔다. (이 두 값이 `YT_CLIENT_ID`, `YT_CLIENT_SECRET`.)

## 단계 6. 프로덕션으로 전환한 뒤 리프레시 토큰 받기 (채널마다 한 번씩)

### 6-1. 반드시 먼저: 게시 상태를 "프로덕션"으로
1. 왼쪽 **Audience** → 게시 상태(Publishing status)가 "Testing"이면 **앱 게시(Publish app)** 를 눌러 "In production"으로 바꾼다.
2. 이유: 구글 공식 문서에 따르면 외부 사용자 유형 앱이 "Testing" 상태이면 리프레시 토큰이 **7일 뒤 만료**된다. 그러면 일주일 뒤 예약이 `invalid_grant` 오류로 업로드를 못 한다.
3. 검수(Verification)를 받지 않은 프로덕션 앱은 동의 화면에 "Google hasn't verified this app(확인되지 않은 앱)" 경고가 뜬다. 본인 계정으로 승인하는 것이므로 **고급(Advanced) → 앱 이름으로 이동(안전하지 않음)** 을 눌러 진행하면 된다.

### 6-2. OAuth Playground에서 토큰 받기
1. https://developers.google.com/oauthplayground 로 이동한다.
2. 오른쪽 위 톱니바퀴(설정)를 누른다.
   - **Use your own OAuth credentials** 체크.
   - 단계 5의 클라이언트 ID와 보안 비밀을 이 화면에만 입력한다.
   - Access type은 **Offline** 이어야 한다.
3. 왼쪽 맨 아래 "Input your own scopes" 칸에 아래를 한 줄로 넣고 **Authorize APIs**.
   ```
   https://www.googleapis.com/auth/youtube https://www.googleapis.com/auth/youtube.force-ssl
   ```
4. 구글 로그인 화면:
   - 계정은 **그 채널의 소유 계정**을 고른다.
   - 채널이 "브랜드 계정"이면 계정 선택 뒤에 **채널(브랜드 계정) 선택 화면**이 한 번 더 나온다. 이때 올리고 싶은 채널(예: 쏙쏙 건강백과)을 정확히 고른다. 여기서 고른 채널이 토큰의 대상이 된다.
   - 경고가 뜨면 고급 → 이동. 권한 체크박스는 모두 허용.
5. Playground 단계 2에서 **Exchange authorization code for tokens** 를 누르고, 나오는 **Refresh token** 값을 복사한다. 이것이 `YT_REFRESH_TOKEN_KO`.
6. (선택, 권장) 채널이 맞는지 확인: Playground 단계 3에서 아래를 요청해 응답의 `customUrl`이 `@ssoksok-health` 인지 본다.
   ```
   GET https://www.googleapis.com/youtube/v3/channels?part=snippet&mine=true
   ```
7. **Tiny Body Co.** 도 같은 방법으로 반복한다. 다른 채널을 고르려면 시크릿(Incognito) 창이나 다른 브라우저 프로필에서 하는 것이 헷갈리지 않는다. 받은 리프레시 토큰이 `YT_REFRESH_TOKEN_EN`.

> 예약은 업로드 직전에 `channels.list(mine=true)`로 채널 주소를 다시 확인하고, 다르면(한국어 토큰이 영어 채널을 가리키는 등) 업로드하지 않고 보고한다.

## 단계 7. 환경에 등록하기
1. 이 세션 화면 제목줄의 **클라우드 환경 메뉴 → Edit(편집)**.
2. 환경 변수(또는 "Network secrets / API credentials" 칸이 있으면 그곳)에 아래 4개를 이름 그대로 입력한다. 이름이 다르면 예약이 변수를 못 찾는다.
   ```
   YT_CLIENT_ID
   YT_CLIENT_SECRET
   YT_REFRESH_TOKEN_KO
   YT_REFRESH_TOKEN_EN
   ```
3. 저장. **새로 시작되는 세션부터** 적용된다(이미 돌고 있는 실행에는 적용되지 않는다).
4. 등록 후 첫 예약 실행의 최종 보고에서 "업로드 결과(링크·공개 상태·썸네일·재생목록·첫 댓글)"를 확인한다. 변수가 없거나 틀리면 어떤 변수가 문제인지 보고에 적힌다.

---

## 쿼터와 공개 상태 (공식 문서 기준, 직접 확인한 내용)
- 영상 업로드(`videos.insert`)는 하루 **100회**의 **별도 한도**를 쓰고 호출 1건당 1이다. 하루 30개 업로드 계획이면 충분하다.
- 그 밖의 호출은 하루 **10,000 단위**를 같이 쓴다. 썸네일 설정(50), 재생목록 추가(50), 댓글 작성(50), 조회(1) 정도라서 한 번의 실행(영상 6개)은 약 500 단위, 하루 다섯 번이면 약 2,500 단위로 여유가 있다.
- 구글 문서는 "검수 전 API 프로젝트로 올린 영상은 비공개로 제한되지 않는다"고 적고 있다. 예약은 업로드 응답의 공개 상태를 확인해서 실제 상태를 보고한다. 만약 비공개로 올라간다면 아래 신청서를 제출한다.
  - 감사·쿼터 확대 신청서: https://support.google.com/youtube/contact/yt_api_form

> 정정: 앞서 대화에서 "하루 약 6개만 올릴 수 있고, 검수 전에는 비공개로 고정될 수 있다"고 안내했는데, 이는 예전 규칙이었다. 위 내용이 현재 공식 문서 기준이다.

## 자주 나는 문제
| 증상 | 원인과 해결 |
|---|---|
| `redirect_uri_mismatch` | 단계 5의 리디렉션 URI가 `https://developers.google.com/oauthplayground` 와 정확히 일치하지 않음 |
| `invalid_grant` | 토큰 만료·취소. 게시 상태가 Testing이면 7일 뒤 만료, 6개월간 안 쓴 토큰, 접근 권한 제거 등. 단계 6을 다시 해 새 토큰을 받는다 |
| 403 권한 범위 부족 | 단계 4/6에서 `youtube.force-ssl` 또는 `youtube`를 빼먹음. 재발급 필요 |
| 썸네일 설정만 403 | 채널의 전화번호 인증(중급 기능) 필요. 영상 업로드는 정상이고 썸네일만 건너뜀 |
| 토큰이 갑자기 무효화됨 | 같은 클라이언트 ID로 계정당 리프레시 토큰은 100개까지이며, 넘으면 가장 오래된 것이 무효화됨 |
| 영상이 엉뚱한 채널로 감 | 단계 6-2의 4번에서 채널(브랜드 계정) 선택을 잘못함. 예약이 업로드 전 채널 주소를 확인해 막지만, 토큰을 다시 받는 것이 정답 |

## 공식 문서
- 인증 개요: https://developers.google.com/identity/protocols/oauth2
- 웹 서버 앱 인증 가이드(범위 주소, offline 접근): https://developers.google.com/youtube/v3/guides/auth/server-side-web-apps
- 쿼터 비용: https://developers.google.com/youtube/v3/determine_quota_cost
- `videos.insert`: https://developers.google.com/youtube/v3/docs/videos/insert
- 감사·쿼터 확대 신청서: https://support.google.com/youtube/contact/yt_api_form
