쏙쏙 건강백과(한국어) / Tiny Body Co.(영어) 영상 제작 + 썸네일 + 유튜브 업로드 예약 실행. 사용자가 없으니 질문하지 말고 가장 합리적으로 판단해 끝까지 진행한다. 초반에 영상이 많이 필요하므로 사용량 초기화 시각(KST 00:30 시작, 5시간 간격)마다 실행된다. 두 채널은 유튜브 승인이 끝났고 업로드용 자격 증명 환경 변수도 점검을 통과했다. 6)에 따라 영상·썸네일·제목·설명·태그를 모두 공개로 업로드한다. 변수가 없거나 인증이 실패하면 업로드만 건너뛰고 제작·검수·전달은 그대로 한다.

0) 화풍(사용자 지시, 2026-10-25부터 기본): 모든 영상(롱폼·숏폼)과 썸네일은 '말랑한 종이 조각(paper story)' 스타일로 만든다. 기존 스킬 엔진의 2D 벡터 화풍은 더 이상 쓰지 않는다.
- 시작할 때 자료 저장소를 받는다: `git clone --depth 1 https://github.com/mini-ok/ssoksok-channel-assets /home/claude/assets` (타임아웃 10분, 실패하면 2·4·8초 간격 3회 재시도). 받은 뒤 /home/claude/assets/engine/paper_story/STYLE_GUIDE.md 를 끝까지 읽고 그대로 따른다. 이 폴더의 코드(paper.py: puff 종이 조각 렌더·낱말 칩·형광펜·별, ink.py, chars.py·lib.py 캐릭터, build2.py 스프라이트 캐시, render2.py 프레임 합성·ffmpeg 파이프, fonts/ 의 Jua·DoHyeon·BlackHanSans·Geist)를 작업 폴더로 복사해 재사용한다. 원본 저장소 파일은 고치지 않는다(실행마다 새 컨테이너이므로 복사본만 수정). 참고 영상: /home/claude/assets/style-tests/style-test-paper-story/motion_test_v2.mp4 (프레임 몇 장을 뽑아 먼저 직접 본다).
- 지금 저장소 코드는 '낮잠' 15초 테스트 장면 전용이다. 매 에피소드마다 같은 구조(요소를 스프라이트로 한 번만 그림자 포함 RGBA로 렌더해 캐시 → 프레임마다 위치·크기·회전·투명도만 바꿔 합성 → raw 파이프로 libx264 crf 20 yuv420p)와 함수(puff, puff_char, chip, highlight, 걷기·스쿼시·오버슈트 스프링)를 써서 이번 대본에 맞는 장면을 새로 짠다. 프레임마다 무거운 puff를 다시 계산하지 않는다.
- 해상도: 롱폼 1920x1080, 숏폼 1080x1920, 30fps를 목표로 한다. 렌더가 너무 오래 걸리면(롱폼 한 편 렌더가 20분 초과 예상) 롱폼 1280x720·숏폼 720x1280으로 낮추고 보고에 적는다.
- 스킬(ssoksok-health-factory·engine-code·example-episodes)은 워크플로, 대본 형식, 캐릭터 설정, 사실 확인 절차, 자막·장면 타이밍 계산 방법을 위해 읽고 따르되, 그림 그리기·장면 렌더 부분은 위 종이 스타일 코드로 바꿔 쓴다. 캐릭터(몸속 회사 9종)와 세계관은 그대로다.
- STYLE_GUIDE.md의 '다음 제작 때 보완할 점' 9가지를 이번 영상에서 반드시 보완한다(별 안쪽 여백, 슬레이트와 '액션!' 칩 함께 이동, 주연 캐릭터 몸 전체가 보이게, 소품 크기, 빈 상단 중앙 채우기, 시계 부채꼴이 숫자를 가리지 않게, 표정 변화, 배경 가장자리 여백, 효과음 강약 + 배경음악). 보완했는지 최종 보고에 항목별로 한 줄씩 적는다. 새로 발견한 어색한 점도 적는다.
- 저장소를 받지 못하면(비공개 전환·네트워크 오류) 그 사실을 보고하고, 이번 실행만 스킬 엔진의 기존 화풍으로 만든다.

0-1) 배경음악(사용자 제공, 수노 제작 연주곡): /home/claude/assets/bgm/ 의 3곡을 쓴다. main_tema.mp3(기본 설명 장면, 기본값), nimble_motifs.mp3(후크·질문·호기심·경쾌한 전환), buant_pop_groove.mp3(활기찬 장면, 엔딩·구독 멘트). 영상마다 분위기에 맞는 곡 하나를 고르고(같은 실행의 롱폼과 숏폼 A·B가 모두 같은 곡이 되지 않게 섞는다), 영상 길이보다 짧으면 1초 크로스페이드로 이어 붙여 반복한다. 믹스: 음악 기본 음량은 나레이션 없는 구간에서 통합 약 -26 LUFS, 나레이션이 나오는 동안 ffmpeg sidechaincompress(또는 볼륨 자동화)로 8~10dB 더 낮춘다(덕킹). 시작 0.5초 페이드인, 끝 1초 페이드아웃. 효과음은 음악보다 또렷하게 하되 수를 줄여 강약을 준다. 최종 영상 통합 음량 약 -14 LUFS, 트루피크 -1dB 이하로 맞추고 ffmpeg ebur128로 측정해 보고한다. 롱폼 엔딩 카드(3-5) 구간은 음악만 작게 남긴다(효과음 없음). 쓴 곡 이름을 업로드 자료 md와 최종 보고에 적는다. 저장소를 받지 못해 음악이 없으면 효과음만으로 만들고 보고한다.

0-2) 자료 백업: 예약 실행에서는 저장소에 push하지 않는다(권한 승인이 필요해 무인 실행에서는 막힌다). 결과물은 7)의 SendUserFile 전달로 남기고, 사용자가 대화 세션에서 저장소에 백업한다.

1) 스킬을 먼저 끝까지 읽고 따른다: ssoksok-health-factory(워크플로), ssoksok-engine-code(lib/common/body/engine/tts 코드), ssoksok-example-episodes(캐릭터 9종 chars.py, 대본·장면 예시), 그리고 youtube-agent(후크 공식 21개·후크 점수표·제목/썸네일 기준·SEO·챕터·쇼츠 규칙). 단 그림·렌더는 0)이 우선한다. 앞의 ssoksok 스킬 3개가 없거나 읽히지 않으면 지어내지 말고 그 사실만 보고하고 끝낸다. youtube-agent가 없으면 아래 5-1)의 요약 기준만 적용한다. 옛 방식(눈동이·커피잔 마스코트, 에피소드 번호 #N, 04/09/14/19 슬롯, 스킬 안의 주제 인덱스 공식)은 폐기됐다. ssoksok 스킬에 적힌 "유튜브 업로드는 하지 않는다"와 "'풀버전 보러가기' 장면(cta)은 쓰지 않는다", youtube-agent의 "게시는 사용자가 한다"는 이 예약에서는 사용자 지시로 바뀌었다: 업로드는 아래 6)이 하고, 영상 끝의 구독·좋아요 멘트는 아래 3-4)를 따른다(단 롱폼을 보러 가라는 '풀버전·본편 보기' 광고 문구는 영상 안에서 여전히 쓰지 않는다). youtube-agent의 '사용자 목소리 영상 3개 요구'는 적용하지 않고 쏙쏙 건강백과/Tiny Body Co.의 기존 톤(귀엽고 직관적, 믿을 만하게, 유머)을 목소리로 삼는다.
2) 주제 인덱스(0부터, 스킬 후보 목록 순서) = max(0, (실행일 KST − 2026-10-24 일수) × 5 + 슬롯 + 1). 슬롯은 KST 시각으로 00시대 0, 05시대 1, 10시대 2, 15시대 3, 20시대 4 (그 밖의 시각이면 가장 가까운 슬롯). 같은 인덱스가 겹치거나 이미 만든 주제면 다음 미사용 주제를 쓴다. 후보가 부족하면 새 주제를 만든다.
3) 결과물(모두 만들어야 완료, 총 mp4 6개 + 썸네일 6장: 롱폼 2장 + 숏폼 4장): 롱폼 한국어 1 + 롱폼 영어 1 (각 75~120초 + 3-5의 엔딩 카드 6~8초, 최대 3분, 끝에 유머 뒤 구독·좋아요 멘트 포함) + 숏폼 한국어 2 + 숏폼 영어 2 (각 30~50초, 끝 멘트 포함, 서로 다른 각도, 롱폼 장면·음성 재사용, 단독 완결, 끝은 유머 뒤 짧은 멘트, 3-6의 숏폼 내용 규칙 적용). 나레이션과 쉼이 1.25배 빨라졌으므로(3-2) 같은 내용이면 길이가 이전보다 짧아진다. 길이를 맞추려고 내용을 억지로 늘리지 말고, 짧아진 대로 둔다. 롱폼이 75초보다 너무 짧을 때만 필요한 근거·한계 설명을 보강한다. 숏폼은 짧아져도 한계 설명으로 채우지 않는다(3-6). 화면 태그는 '쏙쏙 건강백과' / 'Tiny Body Co.'만, 번호 없음. 몸속 회사 세계관과 승인된 캐릭터를 그대로 쓴다. 화풍·움직임·글자는 0)과 STYLE_GUIDE.md를 따른다(통통 튀고 귀엽게, 지루하지 않게, 핵심어는 크게).

3-1) 롱폼 구성(참고 예시이며 꼭 따를 필요는 없다): 후크(유머) → 원인 짧게 → 해결·근거(연구 규모와 한계를 함께 말한다) → 어떤 부위·무엇이 어떻게 달라지는지 → 따라 하기 3가지(동작·실천 방법을 구체적으로, 횟수·시간은 '한 연구 기준'이라고 밝힌다) → 걸리는 기간 → 주의(통증이 계속되면 전문가 상담 등) → 유머 엔딩 → 구독·좋아요 멘트(3-4) → 엔딩 카드(3-5). 이 순서와 항목은 주제와 확인된 근거에 맞춰 유연하게 바꿔도 된다. 주제에 따라 빼거나 합치거나 순서를 바꾸고, 운동·스트레칭이 아닌 주제는 '따라 하기'를 생활 실천으로 바꾸거나 생략한다. 반드시 지킬 것은 세 가지다: ① 적당한 유머가 있어야 한다(시작 후크와 끝 엔딩의 유머는 필수, 흐름이 길거나 무거워질 때만 중간에 한 번 더. 웃기려고 사실을 흐리거나 과장하지 않고 억지로 넣지 않는다). ② 수치는 확인된 출처와 한계를 함께 말하고 의학적 단정·치료 권유는 하지 않는다. ③ 길이는 75~120초(최대 3분)이며 굳이 늘리지 않는다. 숏폼은 롱폼 조각 중 후크+핵심+유머를 골라 쓰되, 연구 한계·장기 효과 미상·'한 연구 기준' 같은 조각은 숏폼에 넣지 않는다(3-6).

3-2) 나레이션 쉼·속도 규칙(조각의 tts 필드): 합성 음성(Chirp 3 HD)은 쉼표와 쉼 태그를 자주 무시해서 단어가 붙어 나온다는 사용자 지적이 있었다(실측: 쉼표만 쓰면 쉼이 0~0.3초로 들쭉날쭉). 그래서 쉼은 음성에 맡기지 않고 아래 tts.py가 문장·구 단위로 따로 합성해 정해진 길이의 무음을 직접 붙인다. 사용자 지시로 나레이션과 모든 쉼(띄어 읽기 무음)을 함께 1.25배 빠르게 한다: tts.py가 조각을 말과 무음까지 모두 이어 붙인 뒤 ffmpeg atempo=1.25로 통째로 가속한다(피치 유지, 그래서 음성 속도 옵션은 건드리지 않는다). 가속 후 실제 무음은 문장 사이 약 0.44초(0.55÷1.25), 쉼표 약 0.22초, 말줄임표 약 0.56초, 조각 끝 약 0.24~0.52초이다. 대본 쪽 규칙: ① 문장이 바뀔 때는 반드시 마침표·물음표·느낌표로 끝내 문장을 나눈다. 나열형 짧은 말("화면 줄이기! 저녁엔 …")도 문장 단위로 끊어 쓴다. ② 문장 안에서 의미 단위마다 쉼표를 확실히 찍는다(주어 뒤, 숫자와 단위 사이, 강조어 앞, 나열 항목 사이). 한 문장에 쉼표는 2~4개. ③ 유머 대사·머뭇거림·여운은 말줄임표(…)로 쓴다. 대시(—, -)는 쉼표로 취급된다. ④ 한 구가 너무 길지 않게(한국어 약 15자 안팎, 영어 약 6~8단어) 쉼표로 끊는다. 속도가 빨라졌으므로 구를 너무 길게 이어 붙이지 않는다. ⑤ 맞춤법은 표준(예: "낼게요"), 숫자는 한글 읽기, 기관명은 띄어쓰기. 자막(disp)은 읽기 표기와 달라도 된다. 영어도 같은 원칙(문장 나누기·쉼표·…)이다. ⑥ 조각을 합친 뒤 롱폼이 75~120초(엔딩 카드 제외, 최대 3분), 숏폼이 30~50초 안인지 확인한다. 자막·장면 타이밍은 가속 후의 manifest 길이를 기준으로 한다.

3-4) 엔딩 구독·좋아요 멘트(사용자 지시): 모든 롱폼과 숏폼의 맨 끝, 유머 엔딩 뒤에 귀엽고 짧은 멘트를 넣어 구독자와 조회수를 늘린다. 구걸하는 느낌이 아니라 몸속 회사 세계관의 유머로 한다. 채널 슬로건은 '하루 한 뼘 더 건강하게'(영어는 "Meet the tiny team keeping you alive.")이며 멘트마다 문구를 조금씩 바꿔 반복감을 줄이되 이 슬로건을 기본으로 삼는다.
- 롱폼(한·영): 해설자 한 문장 + 캐릭터 한 줄의 짧은 멘트, 합쳐 3~5초. 구독과 좋아요를 모두 청한다. 한국어 예: "하루 한 뼘, 더 건강해지고 싶다면, 구독!" / 뇌 팀장: "좋아요도, 꾹… 눌러 주면, 오늘 칼퇴할게요!" 영어 예: "Want to get a little healthier every day? Subscribe!" / "And a like… would make our whole team's day!" 엔딩 화면: 구독 버튼 알약(빨강), 엄지 척 또는 하트 아이콘(좋아요), 종 아이콘을 종이 조각으로 귀엽게 팝업하고 캐릭터들이 손을 흔든다. 번호·광고 문구 없음. 이 멘트 뒤에 3-5의 엔딩 카드가 이어진다.
- 숏폼 A(두 숏폼 중 먼저 만든 쪽): 같은 주제의 다음 숏폼 B로 이어 보게 한다. 3초 이내. 한국어 예: "다음 쇼츠에서, 이어서 만나요!" 영어 예: "See you in the next Short!" 화면에는 '다음 쇼츠 ▶' 칩과 화살표만(에피소드 번호 금지, 롱폼으로 유도하는 '풀버전·본편 보기' 문구 금지).
- 숏폼 B: 좋아요와 구독을 청한다. 3초 이내. 한국어 예: "좋아요 한 번이면, 뇌 팀장이 오늘 칼퇴해요! 구독도, 환영!" 영어 예: "One like, and the Brain finishes work on time! Subscribe too!" 화면에는 하트/엄지와 구독 칩.
- 멘트는 건강 효과를 약속하지 않는다("구독하면 건강해져요" 금지, 세계관 유머로만). 숏폼은 30~50초 안(멘트 포함)이고, 멘트는 유머 마지막 줄 뒤에 붙이되 영상이 반복 재생될 때 어색하지 않게 짧게 유지한다. 멘트도 3-2의 쉼 규칙을 따른다(문장 나누기·쉼표·…). 전용 장면(예: outro/cta1/cta2)을 새로 만들고 효과음(톡·뽁) 등록을 잊지 않는다.

3-5) 롱폼 엔딩 카드(사용자 지시, 홍보): 롱폼(한·영)의 맨 끝, 3-4의 구독·좋아요 멘트 뒤에 6~8초짜리 엔딩 카드 장면(endcard)을 붙인다. 숏폼에는 넣지 않는다. 유튜브 '최종 화면'(end screen)은 API로 설정할 수 없으므로(공식 문서에 방법 없음) 영상 안에 같은 자리를 미리 연출해 두고, 사용자가 Studio에서 그 위에 실제 최종 화면 요소를 올릴 수 있게 구도를 고정한다(마지막 5~20초가 최종 화면 구간이고 영상은 25초 이상이어야 한다).
- 구도(1920x1080 기준 고정, 1280x720이면 같은 비율): 왼쪽 위 큰 칸은 '다음에 볼 영상' 카드(종이 폴라로이드), 오른쪽 위 칸은 '구독' 자리(구독 칩), 아래 가운데에 채널 로고(원형)와 채널명 + 슬로건. 가장자리 5% 안쪽 안전 영역을 지킨다. 요소끼리 겹치지 않는다.
- 채널 로고: 업로드용 토큰으로 channels.list(part=snippet&mine=true)의 snippet.thumbnails.high.url(채널 프로필 이미지)을 내려받아 원형으로 잘라 쓴다. 받지 못하면 화면 태그 칩('쏙쏙 건강백과' / 'Tiny Body Co.')과 승인 캐릭터로 대신한다. 로고 이미지는 저장소나 보고에 남기지 않고 영상에만 쓴다.
- 다음에 볼 영상 고르기(롱폼 렌더 전에, 업로드 전 단계에서): 같은 채널의 uploads 재생목록·시리즈 재생목록을 API로 읽어 이번 주제와 연결성이 가장 높은 기존 롱폼 하나를 고른다(우선순위: 같은 주제 시리즈의 다른 롱폼 → 비슷한 주제 → 조회수 높은 롱폼 → 가장 최근 롱폼. 이번 영상 자신은 제외). 그 영상의 제목(원문)과 썸네일(snippet.thumbnails.high.url을 내려받아 사용)을 카드에 그대로 보여 준다. 연결성 있는 영상이 없거나 API가 실패하면 '전집 재생목록' 카드(이름만, 썸네일 없이 재생 아이콘)로 대신한다. 고른 영상 id와 이유는 업로드 자료 md와 최종 보고에 적고, 6)의 c-4·c-5에서도 쓴다.
- 나레이션: 엔딩 카드 동안 해설자 한 문장만(3초 안팎, 3-2의 쉼 규칙 적용). 한국어 예: "다음엔, '○○○'도, 이어서 보세요!" 영어 예: "Up next, watch '…' too!" 제목을 그대로 읽기에 너무 길면 핵심 주제어만 말한다. 건강 효과 약속 금지, 광고 문구('풀버전' 등) 금지. 나머지 시간은 효과음 없이(배경음악만 작게) 카드가 가만히 떠 있고 캐릭터가 손을 흔든다(최종 화면 요소를 올릴 시간).
- 이 장면은 챕터 계산에서 마지막 구간에 합친다(별도 챕터 없음). 길이와 렌더 확인은 4)와 같다.

3-6) 숏폼 내용 규칙(사용자 지시): 숏폼의 나레이션·자막에는 건강 정보, 운동·실천 방법, 지킬 점 등 시청자가 바로 써먹을 내용만 넣는다. 연구 한계·불확실성·근거 범위를 설명하는 말은 숏폼 영상 안에 넣지 않는다(시간만 잡아먹는다는 사용자 판단). 빼는 예: "하루짜리 실험이에요", "장기 효과는 아직 몰라요", "작은 연구예요", "연구에 한계가 있어요", "실험 결과는 한 연구 기준이에요", "횟수는 한 연구 기준이에요", "사람마다 다를 수 있어요", "아직 더 연구가 필요해요"와 같은 문장, 그리고 문장 안에 끼워 넣는 "한 연구 기준으로", "한 연구에선" 같은 꼬리표도 숏폼에서는 쓰지 않는다. 그 대신 같은 내용을 숏폼 설명란 맨 끝 출처 바로 위에 한 줄로 적는다(예: "참고: 횟수·시간은 한 연구 기준이며, 하루짜리 실험이라 장기 효과는 아직 확인되지 않았어요." 영어도 같은 취지). 그 결과 숏폼이 짧아져도(30초까지) 괜찮으며 다른 말로 채우지 않는다. 다만 사실을 넘어서는 단정은 여전히 하지 않는다: 공공기관 권고 수치는 기관 이름만 짧게 붙여도 된다(예: "NIH 기준, 20분 이내!"). 단일 연구 수치는 꼬리표 없이 '~래요/~했대요' 같은 전해 들은 말투나 '~하면 좋아요' 수준으로 말하고, "무조건·반드시 낫는다·확실히·100%" 같은 표현을 쓰지 않는다. 수치가 모형 추정값인 경우처럼 한계를 빼면 사실이 틀려지는 경우에만 아주 짧게(두세 단어, 예: "추정치로는") 붙인다. 롱폼은 지금처럼 연구 규모와 한계, '한 연구 기준'을 함께 말한다(3-1).

[음성: Google Cloud TTS Chirp 3 HD] 스킬의 Supertonic/sherpa-onnx(모델 다운로드, 받아쓰기 검증)는 쓰지 않는다. 설치는 pip install --break-system-packages skia-python scipy numpy pillow requests 만 한다(한글 폰트 NotoSansCJK가 없으면 apt-get install -y fonts-noto-cjk libegl1, Black 굵기가 없으면 Bold로 대체. ffmpeg·ffprobe는 영상 합성에도 쓰는 필수 도구이니 없으면 apt-get install -y ffmpeg). 이 환경에는 texttospeech.googleapis.com 접속 허용과 x-goog-api-key 헤더를 자동으로 붙이는 네트워크 시크릿이 있다. 키는 직접 넣지 않고(헤더 없이 요청하면 프록시가 붙인다) 찾거나 출력하지 않는다.
a) 시작 시 연결 확인: POST https://texttospeech.googleapis.com/v1/text:synthesize 에 {"input":{"text":"테스트"},"voice":{"languageCode":"ko-KR","name":"ko-KR-Chirp3-HD-Despina"},"audioConfig":{"audioEncoding":"LINEAR16","sampleRateHertz":24000}}. HTTP 200이 아니면 상태와 본문(키 가림)만 한국어로 보고하고 끝낸다. 다른 음성으로 대체하지 않는다.
b) 음성 배정: 한국어 해설자 = ko-KR-Chirp3-HD-Despina, 영어 해설자 = en-US-Chirp3-HD-Despina. 뇌 팀장(sid 5) = Orus, 멜라토닌 = Leda, 그 밖의 캐릭터는 Chirp3-HD의 서로 다른 음성(아래 SID_VOICE 참고, 필요하면 GET https://texttospeech.googleapis.com/v1/voices?languageCode=ko-KR|en-US 로 목록 확인). 같은 sid는 에피소드·언어가 달라도 같은 이름의 음성을 쓰고 어떤 음성을 썼는지 보고한다.
c) /home/claude/shorts-health/tts.py 를 아래 코드 그대로 쓴다(engine-code의 tts.py 대신, 이미 실제 합성과 ffmpeg 가속으로 검증된 코드다). 사용법 python3 -I tts.py <episode_dir> / 숏폼은 REUSE=<롱폼폴더> python3 -I tts.py <숏폼폴더>(같은 id의 롱폼 wav를 복사해 재사용하며 이미 가속된 파일이라 다시 가속하지 않는다. 숏폼 전용 새 조각 id는 새로 합성하고 가속한다). script.py의 LANG과 CHUNKS(id, tts, sid)를 읽는다. sid가 SID_VOICE에 없는 새 캐릭터가 있으면 SID_VOICE에 항목을 추가한다. 속도는 환경 변수 TTS_SPEED(기본 1.25)로 바꿀 수 있으나 사용자 지시가 있기 전에는 바꾸지 않는다.
```python
import base64, importlib.util, io, json, os, re, shutil, subprocess, sys, tempfile, time, wave
import numpy as np
import requests

URL = "https://texttospeech.googleapis.com/v1/text:synthesize"   # 키 헤더는 프록시가 붙인다
SR = 24000
GAP_COMMA = 0.28      # 쉼표(구 사이)
GAP_SENT = 0.55       # . ? !  (문장이 바뀔 때, 반드시 줌)
GAP_ELLIPSIS = 0.70   # … (여운·머뭇거림)
TAIL = {"sent": 0.50, "ellipsis": 0.65, "other": 0.30}   # 조각 끝 쉼(다음 조각과 붙지 않게)
HEAD = 0.03
SPEED = float(os.environ.get("TTS_SPEED", "1.25"))   # 나레이션과 모든 무음을 함께 이 배속으로 빠르게(피치 유지)
EDGE = 0.02           # 합성 결과 앞뒤 무음을 이만큼만 남기고 자름
SID_VOICE = {0: "Despina", 5: "Orus", 7: "Leda", 3: "Puck", 1: "Kore", 2: "Charon", 4: "Fenrir", 6: "Aoede", 8: "Zephyr"}
CHARS = 0

def load_script(ep):
    spec = importlib.util.spec_from_file_location("ep_script", os.path.join(ep, "script.py"))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return getattr(m, "LANG", "ko"), m.CHUNKS

def normalize(s):
    s = s.replace("...", "…").replace("。", ".")
    s = re.sub(r"\s*[—–]\s*|(?<=\S)-(?=\s|$)|\s-\s", ", ", s)   # 대시·끝 하이픈은 쉼표로
    s = re.sub(r"([!?.])\1+", r"\1", s)                          # !! ?? .. → 하나
    s = re.sub(r"[~*_\[\]]", "", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s

def split_units(text):
    """[(phrase, gap_after, kind)] — 문장 끝은 GAP_SENT/GAP_ELLIPSIS, 문장 안 쉼표는 GAP_COMMA"""
    text = normalize(text)
    sentences = re.findall(r"[^.!?…]+[.!?…]*", text)
    units = []
    for sent in sentences:
        sent = sent.strip()
        if not sent:
            continue
        end = sent[-1] if sent[-1] in ".!?…" else ""
        body = sent.rstrip(".!?…").strip()
        phrases = [p.strip() for p in re.split(r"[,，、;:]", body) if p.strip()]
        for i, p in enumerate(phrases):
            last = i == len(phrases) - 1
            if not last:
                units.append((p, GAP_COMMA, "comma"))
            elif end == "…":
                units.append((p + "…", GAP_ELLIPSIS, "ellipsis"))
            elif end in ".!?":
                units.append((p + end, GAP_SENT, "sent"))
            else:
                units.append((p, GAP_SENT, "other"))
    return units

def synth(text, voice, lang):
    global CHARS
    body = {"input": {"text": text}, "voice": {"languageCode": lang, "name": f"{lang}-Chirp3-HD-{voice}"},
            "audioConfig": {"audioEncoding": "LINEAR16", "sampleRateHertz": SR, "speakingRate": 1.0}}
    for wait in (0, 2, 4, 8):
        time.sleep(wait)
        r = requests.post(URL, json=body, timeout=90)
        if r.status_code == 200:
            CHARS += len(text)
            w = wave.open(io.BytesIO(base64.b64decode(r.json()["audioContent"])))
            return np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float32) / 32768
        if r.status_code not in (429, 500, 502, 503, 504):
            break
    raise RuntimeError(f"TTS {r.status_code}: {r.text[:200]}")

def trim(x):
    win = int(0.01 * SR)
    n = len(x) // win
    e = np.sqrt((x[:n * win].reshape(n, win) ** 2).mean(1))
    idx = np.where(e > max(0.004, 0.03 * e.max()))[0]
    if len(idx) == 0:
        return x
    a = max(0, idx[0] * win - int(EDGE * SR))
    b = min(len(x), (idx[-1] + 1) * win + int(EDGE * SR))
    return x[a:b]

def silence(sec):
    return np.zeros(int(sec * SR), dtype=np.float32)

def render_chunk(text, voice, lang):
    units = split_units(text)
    parts = [silence(HEAD)]
    last_kind = "other"
    for i, (phrase, gap, kind) in enumerate(units):
        parts.append(trim(synth(phrase, voice, lang)))
        last_kind = kind
        if i < len(units) - 1:
            parts.append(silence(gap))
    tail = TAIL["sent"] if last_kind == "sent" else TAIL["ellipsis"] if last_kind == "ellipsis" else TAIL["other"]
    parts.append(silence(tail))
    return np.concatenate(parts)

def save_wav(path, x):
    w = wave.open(path, "wb")
    w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes((np.clip(x, -1, 1) * 32767).astype(np.int16).tobytes())
    w.close()

def speed_up(x, speed):
    """ffmpeg atempo로 전체(말+무음)를 speed배 빠르게. 피치는 유지된다."""
    if abs(speed - 1.0) < 1e-3:
        return x
    with tempfile.TemporaryDirectory() as d:
        a, b = os.path.join(d, "a.wav"), os.path.join(d, "b.wav")
        save_wav(a, x)
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", a, "-filter:a", f"atempo={speed}", "-ar", str(SR), "-ac", "1", b], check=True)
        w = wave.open(b)
        return np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float32) / 32768

def main(ep):
    lang_s, chunks = load_script(ep)
    lang = "en-US" if lang_s == "en" else "ko-KR"
    out = os.path.join(ep, "audio")
    os.makedirs(out, exist_ok=True)
    reuse = os.environ.get("REUSE")
    src_manifest = {}
    if reuse:
        src_manifest = {m["id"]: m for m in json.load(open(os.path.join(reuse, "audio", "manifest.json")))}
    manifest = []
    for c in chunks:
        cid = c["id"]
        dst = os.path.join(out, cid + ".wav")
        if reuse and cid in src_manifest:
            shutil.copy(os.path.join(reuse, "audio", cid + ".wav"), dst)
            manifest.append(dict(src_manifest[cid]))
            continue
        voice = SID_VOICE.get(c.get("sid", 0), "Despina")
        x = speed_up(render_chunk(c["tts"], voice, lang), SPEED)
        save_wav(dst, x)
        manifest.append({"id": cid, "dur": round(len(x) / SR, 3), "sr": SR})
        print(f"{cid:12s} {voice:9s} {len(x) / SR:6.2f}s")
    json.dump(manifest, open(os.path.join(out, "manifest.json"), "w"), ensure_ascii=False)
    total = sum(m["dur"] for m in manifest)
    print(f"total {total:.1f}s  chars_used {CHARS}  (월 무료 100만 자 대비 {CHARS / 10000:.3f}%)")

if __name__ == "__main__":
    main(sys.argv[1])
```
d) 합성 뒤 확인: 조각 길이를 출력해 비정상(0.4초 미만, 지나치게 긴 것)이 없는지 보고, 문장이 바뀌는 지점 몇 곳(롱폼에서 최소 5곳, 엔딩 멘트 포함)을 골라 해당 wav에서 에너지 기반으로 무음을 측정해 문장 경계 무음이 0.36초 이상, 쉼표 무음이 0.18초 이상인지 확인한다(1.25배 가속 후 기준이며, 부족하면 해당 조각의 tts 표기를 고쳐 다시 합성). 말이 너무 빨라 발음이 뭉개지거나 어색한 조각이 있으면 그 조각의 문장을 짧게 나누거나 표기를 고쳐 다시 합성한다. 쉼 때문에 조각 구간이 너무 끊기거나 늘어지면 문장을 합치거나 줄인다.
e) 사용한 글자 수를 세어 최종 보고에 월 무료 100만 자 대비로 적는다(tts.py가 출력).

3-3) 후크와 숏폼 설계(조회수 기준, youtube-agent): ① 대본을 쓰기 전에 제목 후보를 먼저 정하고(5-1 참고), 롱폼의 첫 문장이 그 제목의 약속을 바로 확인하게 한다. 첫 15초 안에 시청자가 닫을 수 없는 질문을 열고, 자기소개·구독 요청·"시작하기 전에"로 시작하지 않는다(구독 멘트는 맨 끝에만). ② 후크는 공식 21개 중 맞는 것으로 5개를 써서 후크 점수표(구체성·호명·판돈·호기심·간결성, 총점=평균×0.6+최저점×0.4)로 채점하고 가장 높은 것을 쓴다. 72 미만이면 가장 낮은 속성을 고쳐 다시 쓴다. 단, 우리 채널은 귀여운 유머 톤이므로 유머를 해치지 않는 범위에서 구체적 숫자·질문을 앞세우고, 공포 조장·과장·지어낸 수치는 어떤 점수가 높아도 쓰지 않는다. ③ 숏폼 각각: 원 롱폼 첫 줄이 앞 맥락을 전제하면 단독으로 이해되는 새 첫 줄을 쓰고(후크 점수표로 채점), 첫 2초 화면 자막은 말과 다른 단어로 넣고(큰 칩으로 팝), 숏폼의 첫 프레임(0~0.3초)은 그 숏폼 썸네일과 같은 구도·문구의 표지 화면으로 만들어(큰 칩 제목 + 캐릭터가 이미 화면에 있는 상태에서 시작) 피드에서 첫 장면이 썸네일 역할도 하게 하고, 마지막 줄(유머)이 첫 줄에 대한 답이 되도록 루프 포인트를 만든다(그 뒤에 3-4의 3초 이내 멘트). 숏폼 본문은 3-6에 따라 써먹을 정보만 남긴다. ④ 롱폼은 각 구간이 약속하는 내용이 바뀌는 지점을 기록해 5-1의 챕터에 쓴다.

4) 수치는 공신력 있는 출처를 WebFetch로 직접 확인해 사실표에 적은 뒤에만 쓴다. 의학적 단정·치료 권유 금지. 렌더 후 모든 장면에서 프레임을 뽑아 직접 보고(전환 중 프레임, 큰 숫자 팝 최대 순간, 착지 스쿼시 순간 포함) 자막 잘림, 요소 겹침, 빈 화면, 그림자 끊김, 글자 깨짐을 고치고, 1초 넘게 아무것도 안 움직이는 구간이 없는지 프레임 차이로 확인하고, ffprobe로 길이·해상도를 검증한다(엔딩 멘트 장면과 3-5 엔딩 카드 포함: 로고·카드 썸네일·제목 글자가 잘리지 않고 안전 영역 안인지 확인). 속도가 빨라져 자막이 말보다 늦게 사라지거나 너무 빨리 넘어가지 않는지 확인한다.

5) 업로드 자료: 한·영 각각 md 파일에 영상 6개 전체(롱폼 1 + 숏폼 2씩)의 제목, 설명, 태그, 챕터(롱폼), 첫 댓글 문구, 소속 시리즈(재생목록), 엔딩 카드에서 추천한 영상(롱폼), 쓴 배경음악을 만든다.
- 설명: 첫 두 줄(…더보기 위, 검색 스니펫)에 시청자가 실제로 칠 검색어와 이 영상이 주는 것을 쓴다 → (롱폼) 이 영상이 필요한 사람 한 줄('이런 분께: …', 영어 'Good for: …') → 챕터(롱폼만, 5-1) → 핵심 포인트 2~3줄 → 한두 문장 요약(영상 속 '몸속 회사' 설정 소개 포함) → 구독 안내 한 줄(예: "하루 한 뼘 더 건강해지고 싶다면, 구독! 👍" / 영어 "Want to get a little healthier every day? Subscribe!") → 연결 링크 줄(아래 6의 c-5가 업로드 뒤 채운다: 이 시리즈 정주행 재생목록 링크, 전집 링크, 롱폼은 '다음에 볼 영상' 링크, 숏폼은 같은 주제의 긴 영상 링크, 숏폼 A는 다음 숏폼 B 링크) → (숏폼) 3-6의 연구 한계 '참고:' 한 줄 → 출처 URL(실제로 WebFetch한 것만) → "일반 정보이며 의학적 조언이 아닙니다. 증상이 있거나 걱정되면 의료진과 상의하세요."(영어는 같은 취지 문장) → 해시태그 3~5개(숏폼은 #Shorts 포함). 영상에 없는 내용·수치를 쓰지 않는다(단, 숏폼의 '참고:' 한계 문장은 롱폼에서 다룬 사실이므로 넣어도 된다). 사용자 지시에 따라 영상 내용·제목·설명·태그·보고 어디에도 'AI로 제작', 'AI 생성', '합성 음성' 같은 AI 제작 고지 문구를 넣지 않는다(영상은 애니메이션이라 해당 없음). 업로드 API 요청에도 합성 콘텐츠 표시(containsSyntheticMedia) 필드를 넣지 않는다.
- 태그(tags) 10~15개(전체 500자 이하), categoryId 27(Education; 26과 비교한 조사에서 순위 영향 근거가 없어 유지), 한국어 영상 defaultLanguage/defaultAudioLanguage=ko, 영어=en. 태그는 구분용으로만 쓴다: 주제어, 철자·띄어쓰기 변형, 사람들이 실제로 치는 약어·동의어, 채널·세계관 이름(예: 쏙쏙 건강백과, 몸속 회사, 뇌 팀장 / Tiny Body Co, tiny body company). 영상과 관련 없는 인기 태그를 채우지 않는다(약관 위반).
- 썸네일(롱폼 한국어 1장 + 롱폼 영어 1장, 1280x720 PNG, 2MB 이하): 0)의 종이 스타일 코드(paper.py puff·chip·puff_char, fonts/)로 직접 그린다. 규칙: ① 배경은 주제에 맞는 파스텔 종이 결 배경 + 몸속 회사 세계관 소품 1~2개(작게, 가장자리 여백 유지). ② 왼쪽에 아주 큰 낱말 칩 2줄(BlackHanSans, 칩마다 다른 파스텔 색, 살짝 기울기, 남색 글자, 글자 크기 150~220). 핵심 숫자는 별·말풍선 종이 위에 크게. 전체 3단어 이하, 호기심을 끄는 수치·질문형(예: "낮잠 20분?", "목이 27kg?", 영어 "NAP: 20 MIN?")이며 영상에서 실제로 다룬 사실만 쓴다. 제목과 같은 말을 반복하지 말고 같은 약속을 다른 단어로 쓴다. ③ 그 아래 작은 크림색 칩 부제 1줄(한국어 12자 안팎, 영어 3~4단어, Jua). 수치가 모형 추정이거나 한계가 있으면 부제에 반드시 밝힌다(예: "모형 추정치예요"). ④ 오른쪽에 주제와 관련된 승인 캐릭터 1명(puff_char, 썸네일 높이의 45~60%, 표정은 주제에 맞게)과 큰 소품 1개를 종이 조각으로 배치하고 글자와 겹치지 않게 한다(영어는 글자가 길어 크기를 줄이거나 캐릭터를 오른쪽으로 옮겨 겹침을 피한다). ⑤ 왼쪽 위에 채널 태그 칩('쏙쏙 건강백과' / 'Tiny Body Co.', 번호 없음). 한국어와 영어는 같은 구도에 글자만 바꾼다. ⑥ 그린 뒤 반드시 이미지를 직접 열어 글자·캐릭터 겹침, 글자 잘림, 깨짐을 확인하고 고친다. 추가로 320x180으로 줄여 본 피드 크기에서도 큰 글자와 캐릭터가 읽히는지 확인한다. 파일명은 thumb_<주제>_long_ko.png / _en.png.
- 숏폼 썸네일(사용자 지시, 클릭 수 늘리기: 숏폼 4개 각각 1장, 1080x1920 세로 PNG, 2MB 이하): 롱폼 썸네일과 같은 종이 스타일·같은 규칙(①~⑥)을 세로 구도로 적용한다. 위쪽 1/3에 그 숏폼의 각도에 맞는 큰 낱말 칩 2줄(3단어 이하, 숏폼 첫 줄 후크의 약속을 다른 단어로), 가운데에 핵심 숫자 별·말풍선(있으면), 아래쪽에 캐릭터와 소품을 크게. 쇼츠 화면의 위·아래 UI(위 10%, 아래 20%)와 오른쪽 버튼 줄(오른쪽 15%)에는 글자를 두지 않는다. A와 B는 같은 주제라도 문구·색·캐릭터 표정을 다르게 한다. 270x480으로 줄여서도 큰 글자가 읽히는지 확인한다. 파일명은 thumb_<주제>_short_A_ko.png / _B_ko.png / _A_en.png / _B_en.png.

5-1) 조회수 최적화(youtube-agent 기준 적용):
- 제목: 후보 10개를 쓰고 기준으로 검사해 상위 하나를 고른다. 기준: 모바일 홈 피드에서 잘리는 40자 안에 주제와 핵심 약속이 들어갈 것(최대 60자, 하드 한도 100자), 앞 3단어에 주제를 앞세울 것, 형용사보다 숫자·이름·날짜, '대박·최고의·완벽한·모든 것' 같은 막연한 단어 금지, 영문은 전부 대문자 단어 2개 이하, 썸네일 문구와 다른 단어. 과장·공포 조장·낚시 금지(영상이 약속을 실제로 지켜야 한다). 숏폼 제목은 검색어를 앞에 두고 끝에 ' #Shorts'.
- 검색어 테스트: 이 영상이 이겨야 할 검색어 3개를 정하고(한국어는 "낮잠 몇 분", 영어는 "how long should a nap be" 같은 시청자가 실제로 칠 문장) 제목과 설명 첫 두 줄에 그 단어가 들어 있는지 확인한다. 없으면 설명이 아니라 제목을 고친다.
- 챕터(롱폼만): 00:00으로 시작, 3개 이상, 각 구간 최소 10초, 각 줄은 그 구간의 약속을 3~5단어로. 타임스탬프는 audio/manifest.json의 조각 길이(가속 후 값)와 장면 순서로 계산해 설명란에 넣는다. 75~120초 영상이라 구간이 3~5개가 되도록 조각을 묶고, 엔딩 멘트와 엔딩 카드는 마지막 구간에 합친다.
- 첫 댓글(롱폼만): 다른 시청자도 궁금해할 질문 하나를 채널이 쓴다(예: "여러분은 낮잠 몇 분 주무세요? 😴" 같은 영상 주제의 질문, 한 문장). 그 아래 줄에 '다음에 볼 영상' 링크를 붙인다(엔딩 카드에서 추천한 영상, 예: "다음엔 이 영상도 어때요? https://youtu.be/<id>"). 광고성·구독 구걸 금지.
- 점수 기록: 한·영 md에 선택한 후크의 공식과 점수, 선택한 제목과 40자 내 여부, 검색어 3개, 엔딩 멘트 문구(영상별), 엔딩 카드 추천 영상, 쓴 배경음악을 한 줄씩 적는다.

6) 유튜브 업로드 (YouTube Data API v3, 직접 REST 호출)
- 채널: 한국어 영상 → 쏙쏙 건강백과 https://www.youtube.com/@ssoksok-health , 영어 영상 → Tiny Body Co. https://www.youtube.com/@tinybodyco . 한국어 영상을 영어 채널에 올리거나 그 반대로 올리는 일이 없도록 파일명·언어를 확인하고 올린다.
- 공개 설정: 사용자 지시에 따라 모든 영상을 항상 공개(privacyStatus="public")로 올린다. 비공개·일부공개로 바꾸는 환경 변수나 옵션은 쓰지 않는다.
- 자격 증명은 환경 변수에서 읽는다: YT_CLIENT_ID, YT_CLIENT_SECRET, YT_REFRESH_TOKEN_KO(쏙쏙 건강백과 채널용), YT_REFRESH_TOKEN_EN(Tiny Body Co. 채널용). 값은 출력·로그·보고에 절대 남기지 않고 존재 여부(set/unset)만 확인한다.
- 필수 변수가 하나라도 없으면 해당 언어의 업로드를 건너뛰고 "어떤 변수가 없어서 업로드 못 함"만 보고한다(영상·썸네일 제작과 SendUserFile 전달은 그대로 한다). 있으면 이렇게 올린다.
  a) POST https://oauth2.googleapis.com/token (grant_type=refresh_token, client_id, client_secret, refresh_token)로 access_token을 받는다.
  b) 검증: GET https://www.googleapis.com/youtube/v3/channels?part=snippet&mine=true (Bearer)로 반환된 채널의 customUrl이 한국어=@ssoksok-health, 영어=@tinybodyco 인지 확인한다. 다르면 그 언어는 업로드하지 않고 보고한다. (3-5의 채널 로고·추천 영상 조회도 이 토큰으로 영상 제작 전에 미리 한다. 그 시점에 토큰이 없거나 실패하면 3-5의 대체 방식을 쓴다.)
  c) 영상마다 resumable upload: POST https://www.googleapis.com/upload/youtube/v3/videos?uploadType=resumable&part=snippet,status (헤더 X-Upload-Content-Type: video/mp4, X-Upload-Content-Length) 본문 {"snippet":{"title","description"(챕터·해시태그 포함 최종 설명),"tags","categoryId":"27","defaultLanguage","defaultAudioLanguage"},"status":{"privacyStatus":"public","selfDeclaredMadeForKids":false,"embeddable":true,"publicStatsViewable":true}}. 응답 Location URL에 mp4를 PUT(청크 재개 가능, 5xx·네트워크 오류는 2·4·8초 간격 최대 3회 재시도). 성공 응답의 video id로 https://youtu.be/<id> 를 기록한다.
  c-2) 썸네일: 롱폼 업로드 직후 POST https://www.googleapis.com/upload/youtube/v3/thumbnails/set?videoId=<id> (Bearer, Content-Type: image/png, 본문은 PNG 바이트)로 해당 언어 썸네일을 설정한다. 실패(채널 전화번호 인증 필요 403 등)해도 영상 업로드는 유효하니 이유만 보고하고 넘어간다. 숏폼도 업로드 직후 같은 방법으로 해당 숏폼 썸네일(세로 PNG)을 설정한다. 유튜브가 쇼츠 피드에서는 영상 프레임을 쓰고 맞춤 썸네일은 검색·채널 페이지 등 일부에만 보일 수 있으므로, 숏폼 첫 프레임 표지(3-3 ③)와 맞춤 썸네일을 둘 다 준비한다. 숏폼 썸네일 설정이 거부되면(API 오류) 이유를 보고하고 넘어간다. 설정 성공 여부를 숏폼마다 보고한다.
  c-3) 재생목록(정주행용, 사용자 지시): 영상이 끝나면 다음 영상이 이어서 재생되도록 주제별 시리즈 재생목록으로 묶는다.
   · 가장 중요한 규칙(사용자 지시): 롱폼 모음 재생목록은 채널마다 단 하나, 한국어 "쏙쏙 건강백과 전집", 영어 "Tiny Body Co. Office Life (Full Series)" 뿐이다. '롱폼 전체', '풀 비디오', 'Full Video', 'All Full Videos', 'Long' 등 이름의 다른 롱폼 모음 목록을 절대 새로 만들지 않는다. 롱폼은 반드시 이 전집 목록(과 주제 시리즈 목록)에만 넣는다.
   · 분류: 이번 주제를 아래 시리즈 하나로 분류한다. 비슷한 주제는 반드시 같은 시리즈로 모으고, 목록이 불필요하게 늘어나지 않게 한다. 한국어 기본 시리즈: 수면·휴식 / 자세·목·허리 / 눈 건강 / 손씻기·위생·면역 / 물·음식·영양 / 운동·활동 / 마음·스트레스. 영어: Sleep & Rest / Posture, Neck & Back / Eye Health / Hygiene & Immunity / Water, Food & Nutrition / Move & Exercise / Mind & Stress. 위 이름을 우선 쓰고, 어디에도 안 맞는 새 주제일 때만 짧은 새 시리즈 이름을 만든다.
   · 시리즈 이름 다듬기(사용자 허락): 시리즈 목록에 든 영상들이 늘어나 이름이 실제 내용과 더 이상 맞지 않거나 더 맞는 이름이 있으면 playlists.update로 목록 제목(과 설명)을 영상들에 맞게 바꿔도 된다(예: "눈 건강"에 스마트폰·화면 주제가 모이면 "눈·화면 건강"). 단 ① 새 이름도 짧고(한국어 약 10자, 영어 약 4단어) 제목 형식 "<시리즈명> | 몸속 회사 정주행"(영어 "<Series> | Tiny Body Co. Binge")을 지킨다 ② 목록 id와 항목은 그대로 두고 이름만 바꾼다(새로 만들지 않는다) ③ 바꾼 뒤에는 새 이름을 그 시리즈의 기준 이름으로 삼아 다음부터 그 이름으로 찾는다 ④ 이름만 보고 다른 목록과 겹치는 이름이 되지 않게 하고 전집·쇼츠 목록의 이름은 바꾸지 않는다 ⑤ 꼭 필요할 때만 바꾸고(한 실행에 시리즈당 최대 1번) 바꾼 이전 이름→새 이름을 최종 보고에 적는다. 이름이 바뀐 시리즈 목록의 링크가 들어간 영상 설명은 id 기반 링크라 그대로 유효하다.
   · 각 영상은 최대 3곳에 넣는다: ① 주제 시리즈(롱폼과 숏폼 모두, 같은 시리즈 안에서 롱폼 → 숏폼 A → 숏폼 B 순서로 끝에 추가해 이어 보게 한다) ② 전집 재생목록(위 규칙의 그 하나) — 롱폼만 ③ 쇼츠 재생목록(한국어 "쇼츠 모음", 영어 "Shorts") — 숏폼만.
   · 목록 찾기: 먼저 playlists.list(mine=true, 전체 페이지)로 전체를 읽고, 제목이 정확히 일치하거나 이름 다듬기로 바뀐 기준 이름인 목록, 또는 내용(들어 있는 영상들의 주제)이 맞는 시리즈 목록을 쓴다. 전집은 제목이 일치하는 것이 없고 롱폼만 모아 둔 옛 이름 목록(예: "몸속 회사 정주행 · 롱폼 전체", "Tiny Body Co. · All Full Videos", '풀 비디오' 계열)이 있으면 새로 만들지 말고 playlists.update로 그 목록의 제목을 전집 이름으로 바꿔 쓴다. 전집과 옛 이름 목록이 둘 다 있으면 옛 목록의 롱폼을 전집으로 옮겨 넣고(삭제는 하지 않고 보고에 목록 제목·링크만 적는다) 이후 전집만 쓴다.
   · 시리즈 재생목록 제목: "<시리즈명> | 몸속 회사 정주행"(영어 "<Series> | Tiny Body Co. Binge"). 설명은 2~3문장(이 시리즈가 다루는 것, 몸속 회사 캐릭터들이 알려 준다는 소개, "처음부터 이어서 보세요"/"Watch in order, one after another", 검색어 1~2개, 일반 정보이며 의학적 조언이 아니라는 한 줄). 영상에 없는 내용을 지어내지 않는다.
   · 맞는 시리즈 목록이 없을 때만 playlists.insert(공개, snippet.defaultLanguage=ko 또는 en)로 만든다(실행마다 새 컨테이너). 사용자가 직접 만든 다른 재생목록은 건드리지 않는다. 같은 영상이 이미 들어 있으면 다시 넣지 않는다. 재생목록 id는 반드시 API 응답으로 받은 값만 쓰고 추측하거나 줄여 쓰지 않는다.
   · 정리 보충: 해당 채널의 uploads 재생목록에 아직 어떤 시리즈에도 안 들어간 기존 영상이 있으면(한 번에 최대 10개) 같은 방식으로 분류해 넣는다. 쇼츠 재생목록과 전집에 빠진 영상도 같이 채운다.
   · 실패하면 이유만 보고하고 넘어간다. 업로드 쿼터가 부족해 보이면 영상 업로드를 우선하고 재생목록은 건너뛴다.
  c-4) 첫 댓글: 롱폼 업로드 직후 commentThreads.insert(part=snippet)로 5-1의 첫 댓글(질문 한 문장 + 다음에 볼 영상 링크 줄)을 올린다. API로는 댓글을 고정할 수 없으니 보고에 "고정은 사용자가 수동"이라고 적는다. 실패하면 이유만 보고하고 넘어간다.
  c-5) 연결 링크(조회수·홍보): 같은 언어의 롱폼, 숏폼 A, 숏폼 B를 모두 올리고 재생목록에 넣은 뒤 videos.update(part=snippet)로 설명의 연결 링크 줄을 채운다. 롱폼·숏폼 A·B 모두에 "이 시리즈 이어서 보기: https://www.youtube.com/playlist?list=<시리즈 재생목록 id>"(영어 "Keep watching this series: ...")를 넣고, 롱폼에는 추가로 "전집 보기: <전집 재생목록 링크>"(영어 "Full series: ...")와 "다음에 볼 영상: https://youtu.be/<엔딩 카드 추천 영상 id>"(영어 "Watch next: ...") 줄을 넣는다. 숏폼 A와 B 설명에는 "같은 주제의 긴 영상: https://youtu.be/<롱폼 id>"(영어 "Full video: ...")를, 숏폼 A에는 추가로 "다음 쇼츠: https://youtu.be/<B id>"(영어 "Next Short: ...")를 넣는다. 롱폼 설명에는 두 숏폼 링크를 "이 주제의 쇼츠"(영어 "Shorts on this topic") 줄로 넣는다. videos.update는 snippet을 통째로 바꾸므로 반드시 기존 title, description(링크 줄만 채운 것), tags, categoryId, defaultLanguage, defaultAudioLanguage를 모두 다시 보낸다(빠뜨리면 태그가 지워진다). 실패하면 이유만 보고하고 넘어간다.
  c-6) 이전 영상 쪽 연결(홍보, 쿼터 여유가 있을 때만): 엔딩 카드에서 추천한 기존 롱폼의 설명에 이번 새 롱폼 링크가 아직 없으면 videos.update로 "함께 보면 좋은 영상: https://youtu.be/<새 롱폼 id>"(영어 "Related: ...") 한 줄을 설명 링크 영역에 추가한다(기존 title·description·tags·categoryId·defaultLanguage·defaultAudioLanguage를 videos.list로 읽어 모두 다시 보낸다. 설명을 바꾸기 전과 후 제목이 동일한지 확인). 실패하면 이유만 보고하고 넘어간다.
  d) 순서: 한국어 롱폼 → 한국어 숏폼 A → 한국어 숏폼 B → 한국어 재생목록(c-3) → 한국어 링크 업데이트(c-5, c-6) → 영어 롱폼 → 영어 숏폼 A → 영어 숏폼 B → 영어 재생목록 → 영어 링크 업데이트. 같은 영상을 중복 업로드하지 않도록 업로드 직후 /home/claude/shorts-health/uploads.json 에 {파일, 채널, video id}를 적고, 실패 후 재시도 전에 먼저 이 기록과 해당 채널의 최근 업로드 목록(playlistItems, uploads 플레이리스트)에서 같은 제목이 있는지 확인한다.
  e) 오류 처리: quotaExceeded/uploadLimitExceeded면 즉시 중단하고 못 올린 영상 목록과 원인을 보고한다(수동 업로드용 자료는 이미 전달됨). 업로드 쿼터가 부족해 보이면 영상 업로드를 우선하고 재생목록·첫 댓글·링크 업데이트는 건너뛴다. 401/403(권한·토큰 만료·invalid_grant, 권한 범위 부족 포함)이면 해당 기능만 중단하고 원인만 보고한다(토큰 값은 가리고). 다른 방법으로 우회하거나 다른 계정·채널에 올리지 않는다.
  f) 응답의 status.privacyStatus가 실제로 public인지 확인해 보고에 적는다(공식 문서상 검수 전 프로젝트도 비공개로 제한되지 않지만 실제 상태를 사실대로 보고한다).

7) 결과물(mp4 6개, 썸네일 PNG 6장(롱폼 2 + 숏폼 4), 한·영 업로드 자료 md)을 SendUserFile로 보낸다(업로드 성공 여부와 관계없이 항상). 막히면 억지로 만들지 말고 무엇이 막혔는지만 짧게 보고한다. 최종 보고는 파일 목록, 주제, 화풍(종이 스타일 적용 여부·해상도), STYLE_GUIDE 보완 9항목 결과와 새로 발견한 어색한 점, 쓴 배경음악과 측정 음량(LUFS), 선택한 후크 점수·제목, 영상별 엔딩 멘트 문구, 엔딩 카드에서 추천한 영상(제목·링크·고른 이유), 출처, 사용 음성, 글자 수 사용량, 나레이션 속도(1.25배)와 쉼 검증 결과(확인한 문장 경계 수와 측정 무음), 영상별 길이, 렌더 시간, 유튜브 업로드 결과(영상별 링크·공개 상태·썸네일 설정 여부·소속 재생목록 이름과 API가 돌려준 실제 링크·바뀐 재생목록 이름(이전→새)·첫 댓글·링크 업데이트·실패 사유), 사용자가 Studio에서 직접 할 일(롱폼 마지막 구간에 최종 화면 요소 올리기, 댓글 고정)을 한 줄로, 특이사항만 간단히.