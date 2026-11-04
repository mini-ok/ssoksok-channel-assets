# 구독 클라우드 예약 → GitHub 렌더링 → Release

사용자 지시(2026-11-04): PC가 꺼져 있어도 매일 새 요리 두 편을 한·영으로 제작하고 GitHub에 직접 저장. 로컬 영상 저장·ZIP·별도 OpenAI API 실행은 사용하지 않는다. 유튜브 업로드는 별도 예약으로 분리한다.

1. 웹 ChatGPT Work의 구독 클라우드 작업이 `WEB_SCHEDULE_PROMPT.md`와 시리즈 규칙을 읽어 새 에피소드 source를 만든다.
2. 연결된 GitHub 도구로 source를 main에 저장한 후 queue JSON 하나를 마지막에 커밋한다.
3. GitHub의 표준 Ubuntu Actions runner가 음성·장면·한영 영상을 제작하고 전체 디코딩·최종 대사·음량·음악·레시피 고정을 검수한다. 별도 OpenAI API는 호출하지 않는다.
4. `release_episode.py`가 에피소드별 MP4·SRT·레시피 PNG·업로드 자료를 ZIP 없이 Release에 저장한다. SHA256 검증을 끝낸 뒤에만 draft를 공개한다. `manifest.json`의 `upload_ready=true`가 실제 업로드용 완료 신호다.

## Queue 형식

`cooking-shorts/cloud/queue/2026-11-05.json`:

```json
{"schema":1,"episodes":[11,12],"test_run":false}
```

새 회차의 production.json, plan.json, nutrition_verification.json, visuals.py, 대본·README가 먼저 main에 있어야 한다. 계정 보안 인증·GitHub 연결은 사용자 계정에서 한 번 완료해야 한다. 기존 실패는 원인을 수정한 뒤 같은 queue의 attempt를 늘려 재시도한다. 이미 검증·공개된 Release는 source fingerprint가 같으면 재사용하고 다르면 덮어쓰지 않는다.

## 인증과 비용

GitHub Secret `GCP_TTS_SA_KEY_B64`에 기존 Google TTS 서비스 계정을 암호화해 등록한다. 키 값은 source·Release·로그에 기록하지 않는다. GitHub의 `GITHUB_TOKEN`은 해당 job에서만 받는다. `OPENAI_API_KEY`는 필요하지 않다.

기획·코딩은 웹 구독 사용량을 쓰고, 공개 저장소의 표준 Actions runner를 사용한다. 기존 Google 음성 합성 사용량은 별도로 적용된다. 유료 대형 runner, 별도 AI API, 추가 크레딧 구매로 자동 전환하지 않는다.

## 검증

`python cooking-shorts/cloud/test_release.py`는 실패한 자산이 공개되지 않는지, 완성 Release가 덮어써지지 않는지, 재실행 중복이 없는지 네트워크 없이 검증한다.

실제 클라우드 시험은 기존 회차를 `test_run=true`로 queue에 넣는다. 시험 Release는 prerelease이며 `upload_ready=false`이므로 유튜브 업로드 대기열에서 제외한다. 시험도 한·영 전체 렌더·대사·파일·업로드 자산 hash를 검증한다.

웹 클라우드가 파일 생성과 queue 커밋을 실제로 수행하는지 먼저 시험한 뒤 매일 06:00 Asia/Seoul 예약을 활성화한다. 이 문서를 저장한 것만으로 예약 완료라고 보고하지 않는다.
