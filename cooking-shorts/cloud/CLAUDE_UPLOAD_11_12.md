# Claude cloud upload: episodes 11 and 12

이 작업은 사용자가 2026-11-04에 승인한 유튜브 공개 업로드다. 시금치 마늘 파스타(10편)는 이미 올라갔으므로 재업로드하지 않는다. 새 11·12편의 한글·영문 총 네 영상만 처리한다.

1. GitHub mini-ok/ssoksok-channel-assets의 Actions run https://github.com/mini-ok/ssoksok-channel-assets/actions/runs/41853937674 상태를 확인한다. 실패·진행 중이면 완성됐다고 하지 않는다.
2. 아래 정식 Release 두 개가 공개되고 manifest.json의 test_run=false, upload_ready=true인지 확인한다.
   - https://github.com/mini-ok/ssoksok-channel-assets/releases/tag/cooking-episode-0011
   - https://github.com/mini-ok/ssoksok-channel-assets/releases/tag/cooking-episode-0012
3. 각 Release의 manifest.json에 열거된 원본 자산을 이미 유튜브 인증된 클라우드의 에피소드별 임시 폴더로 받는다. ZIP·사용자 PC·별도 OpenAI API는 사용하지 않는다. 키·토큰은 읽어 보여주거나 GitHub에 저장하지 않는다.
4. manifest의 모든 파일 SHA256을 검증하고, upload.py·metadata.json을 읽어 공식 Google API 호출, 한글 @ssoksok-health / 영문 @tinybodyco, 제목·설명·재생목록이 맞는지 확인한다. 인증 변수 값은 출력하지 않는다.
5. 기존 업로드 이력·채널을 조회하여 11·12편의 동일 영상이 이미 올라가 있으면 재업로드하지 않고 링크를 재사용한다. 기존 upload_result.json은 유지하고 불확실한 이전 업로드는 Studio/API로 확인 후 처리한다.
6. 각 에피소드 폴더에서 python upload.py를 실행해 한글·영문을 해당 채널에 공개 업로드하고 기존 요리 재생목록에 추가한다. 실제 공개 상태·채널을 API로 재확인한다. 비공개 강제 제한이나 실패를 성공으로 보고하지 않는다.
7. 결과로 네 영상 URL, 채널, public 상태, 재생목록 URL을 보고한다. 비밀이 없는 episodeNN/youtube_upload_result.json에도 에피소드·언어·영상 URL/ID·채널·공개 상태·업로드 파일 SHA256·확인 시각을 저장할 수 있으면 GitHub main에 저장한다. 이 기록은 ChatGPT가 업로드 완료를 확인하고 매일 11시 Asia/Seoul 자동제작 예약을 활성화하는 근거다. ChatGPT 예약을 직접 제어할 수 있다고 가정하지 않는다.
