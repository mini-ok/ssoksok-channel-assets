# 몸속 주식회사 / Tiny Body Co. 제작 파이프라인 인수인계
2026-10-26 「야식 습격 사건」 실행에서 새로 짠 코드와 설정. 다음 실행은 이 파일들을 복사해 쓰고 **대본(eps.py)만 새로 쓰면 된다.**

## 0. 전제
- 화풍 코드는 자료 저장소의 `engine/paper_story/`(paper.py·ink.py·chars.py·lib.py·fonts)를 그대로 쓴다.
  이 번들은 그 위에 얹는 **장면·타이밍·오디오·업로드 층**이다.
- `chars.py`에 이번 실행에서 **위 대리(stomach)** 함수를 추가했다. 저장소 원본에는 없으므로
  다음 실행에서도 같은 함수를 추가하거나, 저장소 chars.py에 반영해 두어야 한다(아래 6번).

## 1. 환경 (새 컨테이너마다, 약 3분)
```bash
git clone --depth 1 https://github.com/mini-ok/ssoksok-channel-assets /home/claude/assets
pip install --break-system-packages skia-python scipy numpy pillow requests google-auth
apt-get update -q && apt-get install -y -q libegl1 fonts-noto-cjk
```
**함정 1 — 파이썬 버전이 둘이다.** `python3`는 3.11, `pip`는 3.13에 설치한다.
모든 실행은 반드시 `/usr/bin/python3`(3.13)로 한다. 그냥 `python3`를 쓰면 `ModuleNotFoundError: numpy`.
**함정 2 — skia는 libEGL을 찾는다.** `libegl1`이 없으면 `import skia`가 `ImportError: libEGL.so.1`.
**함정 3 — ink.py는 NotoSansCJK 경로를 직접 참조한다.** `fonts-noto-cjk`가 없으면 임포트 단계에서 죽는다.
**함정 4 — `-I` 모드에서는 cwd가 sys.path에 없다.** 스크립트 첫 줄에 `sys.path.insert(0, "<폴더>")`를 넣어 둔다.

## 2. 실행 순서
| 단계 | 명령 | 걸린 시간 |
|---|---|---|
| ① 대본 | `eps.py`를 새로 쓴다(장면 리스트 + KO/EN 대사 딕셔너리) | 사람 작업 |
| ② 대본→TTS 입력 | `/usr/bin/python3 -I gen_scripts.py` | 1초 |
| ③ 음성 | `/usr/bin/python3 -I run_tts.py /home/claude/work/ep/<변형>` × 6 (**순차**) | **약 40분** |
| ④ 배경 | `KSC=1.0 /usr/bin/python3 -I bgs.py` (4프로세스) | 71초 |
| ⑤ 썸네일 | `KSC=1.0 /usr/bin/python3 -I thumbs.py` | 40초 |
| ⑥ 영상 | `KSC=1.0 /usr/bin/python3 -I render.py <변형> <출력폴더> <파트> <전체파트>` | 롱폼 4파트 약 4분 |
| ⑦ 합치기+오디오 | `bash finish.sh <변형> <파일명.mp4>` / 숏폼은 `finish_short.sh` | 20초 |
| ⑧ 업로드 | `/usr/bin/python3 -I run_upload.py` → `post.py` | 8분 |

③은 네트워크, ④~⑦은 CPU. **③을 먼저 백그라운드로 걸고 ④⑤를 동시에 돌리면 40분을 벌 수 있다.**

## 3. 각 스크립트 역할과 인자
### render/
- **core.py** — 스프라이트 캐시 엔진. `sprite(key, w, h, fn)`이 핵심: `fn(img)->img`를 검정/흰 배경에
  두 번 그려 알파를 뽑고, 그림자 포함 RGBA로 잘라 `cache/*.npz`에 저장한다. 같은 key면 디스크에서 재사용.
  환경변수 `KSC`가 1.0이면 풀 해상도, 2/3이면 축소본(빠른 시험용). **key에 KSC가 섞여 들어가므로 해상도를 바꾸면 캐시가 자동으로 갈린다.**
- **props.py** — 소품 스프라이트(시계·시계바늘·경보등·후광·치킨통/피자·떡볶이/윙·콜라/소다·라면/아이스크림·결재판·도장·반려 도장·물컵·상자·위산 방울·땀·종이 와이프 시트·엄지·종·공지 카드). 전부 `sprite()` 캐시를 탄다.
- **bgs.py** — 배경 10종(사무실 밤/낮, 회의실, 정문, 위장 공장, 야간 당직실, 엔딩, 숏폼 세로 2종 — 회의실/정문/공장은 한·영 2벌). `run(i)`를 멀티프로세스로 돈다. 결과는 `cache/bg_*.npy`.
- **eps.py** — **유일하게 매번 새로 쓰는 파일.** 장면 리스트(`L`, `SA`, `SB`)와 대사 딕셔너리(`KO`,`EN`,`SKO_A`…).
  장면 한 칸 = `dict(id, loc, sid, tempo, actors, props, chips, fx, time, iv, dur, mindur)`.
  `actors`는 `{이름: (x, 표정, 배율, 옵션)}`, 옵션은 `run`/`hop`/`wave`/`y`.
- **gen_scripts.py** — `eps.py`를 읽어 6개 폴더에 `script.py`(TTS 입력: `id, tts, sid, act`)를 쓴다.
- **run_tts.py** — 저장소 `tts.py`를 불러 조각별로 합성. **길이 자동 검수·재합성 포함**(아래 4번).
- **audit.py** — 이미 만든 wav들의 길이/글자수 비를 점검해 이상한 조각 목록을 `/home/claude/work/bad.json`에 쓴다.
- **render.py** — 프레임 합성기. 인자: `<변형> <출력폴더> [preview t1 t2 …| info | <파트> <전체파트>]`.
  `info`는 장면별 시작시각·길이를 출력(챕터 타임스탬프 계산에 사용), `preview`는 해당 초의 PNG만 뽑는다.
  파트 분할 렌더이므로 4코어면 `0 4 / 1 4 / 2 4 / 3 4`를 동시에 돌리고 ⑦에서 concat한다.
- **mix.py** — 음성 + 효과음 + BGM 믹스. 덕킹·EQ·크로스페이드·측정까지 numpy로 한다. 결과 `ep/<변형>/mix.wav`와 검수용 `stem_voice.wav`/`stem_music.wav`, 표준출력으로 측정 JSON.
- **thumbs.py** — 썸네일 6장. `KSC=1.0` 고정(파일 맨 위에서 직접 설정).
- **finish.sh / finish_short.sh** — concat → mix.py → loudnorm → mp4.

### upload/
- **yt.py** — 토큰 발급과 REST 래퍼. 환경변수만 읽고 값은 절대 출력하지 않는다.
- **upload.py** — 채널 검증(customUrl 대조), resumable 업로드, 썸네일 설정.
- **run_upload.py** — 제목·설명·태그 본문이 들어 있는 메인 업로더. **다음 실행에서 이 파일의 설명 문자열만 갈아끼우면 된다.** 결과를 `upload_result.json`에 적어 재실행해도 중복 업로드하지 않는다.
- **post.py** — 재생목록 추가, 설명 연결 링크 채우기(c-5), 첫 댓글, 이전 영상 역링크(c-6).
- **pick.py** — 채널 로고와 '다음에 볼 영상'을 골라 `endinfo.json`으로 저장(엔딩 카드가 읽는다). **롱폼 렌더 전에 돌려야 한다.**
- **probe.py / pl.py** — 채널·업로드 목록·재생목록 조회(조사용).

## 4. 막혔던 문제와 해결 (같은 함정을 두 번 밟지 말 것)
1. **폰트에 글리프가 없다.** Jua·BlackHanSans·DoHyeon에 `…`와 `·`가 없어 □로 깨진다.
   → 화면에 그리는 모든 문자열에서 `…`→`...`, `·`→`/`로 치환. (`render.py`의 `cap_sp`, 엔딩 카드 제목)
2. **영어 칩이 화면 밖으로 나간다.** 한국어 기준 크기(150)를 영어에 그대로 쓰면 1080px을 넘긴다.
   → `chip_sp()`에 `CHIP_MAXW`(숏폼 880 / 롱폼 1480) 자동 축소를 넣었다. **영어 텍스트는 반드시 이 경로로 그린다.**
3. **엔딩 카드 썸네일에 검은 띠.** YouTube `thumbnails.high`는 480x360(4:3)이다. → 중앙 16:9 크롭 후 리사이즈.
4. **Gemini TTS가 연기 지시에 과하게 반응한다.** `act`가 길면 숨·뜸을 길게 연기해 예상의 4~10배(최대 17초)가 나온다.
   → `run_tts.py`가 글자수 기준 기대 길이(한국어 7.4자/초, 영어 3단어/초)와 비교해 0.55~1.6배 밖이면 재시도.
     3회까지는 `act`를 유지하고, 그 뒤에는 **`act`를 빼고** 합성하며, 가장 기대치에 가까운 테이크를 고른다.
     이번 실행에서 **142개 조각을 재합성**했다(전체 약 110개 중 중복 포함).
5. **Gemini 분당 쿼터.** `generate_content_requests_per_minute_per_project_per_base_model` 429.
   → 변형 6개를 **병렬로 돌리면 전부 실패한다.** 순차 + 20초 이상 백오프.
6. **ffmpeg `alimiter`가 이 빌드에서 동작하지 않는다.** `limit=0.5`를 줘도 피크가 0 dBFS 그대로였다.
   → 리미터를 쓰지 말고 `loudnorm=I=…:TP=-1.5`만 쓴다. loudnorm 1패스는 요청값보다 약 1.4 LU 낮게 떨어지므로
     **I=-13.2를 요청해야 실측 -14.6 LUFS**가 나온다.
7. **ffmpeg가 엉뚱한 오디오를 고른다.** `-i 영상.mp4 -i 소리.wav`만 주면 입력 0의 오디오를 쓴다(이미 정규화된 소리를 또 정규화).
   → 항상 `-map 0:v:0 -map 1:a:0`.
8. **캐릭터가 바닥에서 떠 있다.** `CHAR_S=520`일 때 발바닥 선은 스프라이트 캔버스의 y=554다(`CH_ANCHOR`).
   추정하지 말고 이 값을 쓴다. 장소별 바닥 y는 `LOC_FLOOR`.
9. **배경 파일이 없다고 죽는다.** 야간 당직실은 글자가 없어 `night_ko` 하나만 만든다 → `bg_name()`에서 `night`는 항상 `night_ko`로 보낸다.
10. **빈 화면 장면.** 무음 비트(`sid=None`)에 `actors`를 비워 두면 1.4초 동안 아무도 없는 방이 나온다(스타일 가이드 위반). **무음 비트에도 캐릭터를 둔다.**
11. **소품이 다음 장면에서 사라진다.** `t=-1`(이미 등장함)로 넘긴 소품은 그리기 함수에 **정적 분기**가 있어야 한다(`P_thumbup` 참고).
12. **설명란 특수문자.** API 거부는 없었지만, 안전을 위해 업로드 본문에는 `·` 대신 `-`를 썼다. md 문서에만 `·`를 쓴다.

## 5. 시간·사용량이 컸던 구간과 다음에 줄이는 법
- **TTS 40분이 전체의 대부분.** 재합성 142건이 큰 몫이다. 줄이는 법:
  `act`를 **짧게**(상황+감정 한 덩어리, 15자 이내) 쓰고, 감탄사·말줄임표가 많은 줄에는 `act`를 아예 붙이지 않는다.
- **렌더를 두 번 돌렸다.** 처음에 2/3 해상도로 시험 렌더를 했다가 풀 해상도로 다시 돌렸고,
  그 뒤 시각 수정(빈 장면·엄지 아이콘) 때문에 롱폼 2편을 또 돌렸다. 약 15분 손해.
  → **처음부터 `KSC=1.0`으로 가고, `preview`로 대표 프레임 10장 정도를 먼저 눈으로 본 뒤 전체 렌더를 시작한다.**
- 스프라이트·배경 캐시는 `/home/claude/work/cache`에 남는다. 같은 컨테이너에서 재렌더는 캐시 덕에 훨씬 빠르다.
  **캐시를 지우지 말 것**(지우면 배경 71초 + 스프라이트 수십 초를 다시 쓴다).
- 업로드는 영상 6개에 약 8분. 쿼터 문제는 없었다.

## 6. 다음 실행 때 할 일
1. `chars.py`에 `stomach()`(위 대리) 함수가 있는지 확인하고 없으면 추가한다.
2. `eps.py`만 새 주제로 새로 쓴다. 나머지 파일은 그대로 둔다.
3. `pick.py`를 **롱폼 렌더 전에** 돌려 `endinfo.json`을 만든다.
4. `run_upload.py`의 제목·설명·태그 문자열과 `post.py`의 첫 댓글 문구를 새 주제로 바꾼다.
5. 재생목록 id는 바뀌지 않았다면 `run_upload.py`의 `PL` 딕셔너리를 그대로 쓸 수 있다(실행 전 `pl.py`로 확인).

## 위 대리(stomach) 병합 (2026-10-26)
`stomach()`(위 대리, sid 10)는 이제 `engine/paper_story/chars.py` 맨 끝에 병합되어 있다. setup.sh가 ps/로 복사하므로 별도 패치 불필요
(`engine/pipeline/chars_stomach_patch.py`는 참고용 원본). 호출: `chsp("stomach", mood)` / `paper.char_fn("stomach", mood)`.
