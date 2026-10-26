# 공개 직후 마무리 작업 (예약 공개 영상용)

대상 채널: 호출 때 지정(ko = @ssoksok-health, en = @tinybodyco). 사용자가 없으니 질문하지 말고 끝까지 진행한다. 저장소에 push하지 않는다. 자격 증명 값은 출력하지 않는다(존재 여부만).
도구: 저장소의 `engine/pipeline/upload/yt.py`(token, api). 작업 폴더에 `cp -r /home/claude/assets/engine/pipeline/upload /home/claude/work/up`로 복사해 쓰고 `pip install --break-system-packages requests` 정도만 설치한다.

## 1. 첫 댓글 올리기 (예약 공개 영상은 공개 전에 댓글을 달 수 없어 여기서 한다)
1. 해당 채널 uploads 재생목록에서 최근 영상을 읽고, **공개 상태이고 길이 75초 초과(롱폼)이며 snippet.publishedAt이 최근 4시간 안**인 영상을 찾는다. 없으면 "해당 없음"으로 끝낸다.
2. 각 영상에 대해 `commentThreads.list(part=snippet, videoId=…)`로 이미 채널 본인(채널 id) 댓글이 있는지 본다. 있으면 건너뛴다.
3. 없으면 commentThreads.insert로 첫 댓글을 올린다: 영상 주제를 아는 사람이 궁금해할 **질문 한 문장**(한국어 영상은 한국어, 영어는 영어; 예: "여러분은 하루에 커피 몇 잔 드세요? ☕") + 다음 줄에 **다음에 볼 영상** 링크. 다음에 볼 영상 = 시트콤 롱폼 목록('몸속 주식회사 시트콤' / 'Tiny Body Co. — The Office Sitcom')에서 이 영상 바로 앞(직전) 롱폼의 https://youtu.be/<id> (없으면 줄 생략). 문구 예: "다음엔 이 영상도 어때요? https://youtu.be/…" / "Up next: https://youtu.be/…". 광고성·구독 구걸·AI 고지 문구 금지.
4. 댓글 고정은 API로 못 하므로 보고에 "고정은 사용자가 수동"이라고 적는다. 실패하면 이유(HTTP 코드·reason)만 보고한다.

## 2. 공개 시간대 성과 기록 (전략 조정용, 읽기 전용)
최근 7일 동안 공개된 이 채널의 영상(롱폼·쇼츠 따로)을 videos.list(part=snippet,statistics,contentDetails)로 읽어, 공개 시각(현지 시각 시)별로 **공개 후 경과 시간당 조회수**(views ÷ 경과 시간)와 좋아요를 표로 적는다(롱폼/쇼츠 구분, 영상 제목 일부, 공개 현지 시각, 경과 시간, 조회수, 시간당 조회수). 표본이 적으면 적다고 쓴다. 판단은 하지 말고 표만 최종 보고에 붙인다(사용자·대화 세션이 분석한다).

## 3. 보고
3~6줄: 올린 첫 댓글(영상 링크·문구), 건너뛴 영상, 오류, 성과 표.
