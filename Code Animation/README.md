# Code Animation — 허상공방 虛像工房 Project

이상민(GoXoN)과 Claude가 **코드만으로** 만든 단편 애니메이션 포트폴리오 모음.
모델링·텍스처·음원 소스 없이 형상·채색·소리를 모두 코드로 생성한다(Python cairo/numpy, three.js).
영상(mp4)은 용량 때문에 저장소에 넣지 않는다. 소스·음악(mp3)·시트 이미지·문서만 보관한다.

> 다른 Claude 계정/세션에서 이어 작업할 때는 **이 파일 → `CLAUDE.md`(작업 규칙) → 각 작품 README → `_kit/README.md`(스킬 등록·환경) → `_shared/`** 순서로 읽으면 된다.

## 작품 목록과 상태 (2026-11-10 기준)

| 폴더 | 작품 | 길이 | 엔진 | 상태 |
|---|---|---|---|---|
| `orbit/` | 〈궤도〉 ORBIT | 짧은 시험작 | Python | 완료(초기작) |
| `keeper/` | 〈빛지기〉 THE KEEPER | 67초 | Python cairo, 2.39:1, 30fps | **v2 완료** — 엔딩 교체 |
| `holssi/` | 〈홀씨〉 HOLSSI | 97초 | Python cairo, 24fps | **v2 완료** — 엔딩 교체, C7 마을 부감 질감 수정 |
| `scarecrow/` | 〈허수아비의 겨울〉 | 137초 | Python cairo + painter.py, 24fps | **v2 완료** — 컷 수정(아래) |
| `shorts/` | 세로 숏츠 3편(빛지기·홀씨·허수아비) | 67/97/137초 | 가로 v2 재구성 | 완료(2026-11-13) — `shorts/README.md` |
| `sumbi/` | 〈숨비〉 | 172초 | three.js 3D + Python 셀 마감 | 1차 완성 후 종료. 회고 `sumbi/postmortem.md` |
| `jeom/` | 〈점〉 JEOM | 3분 11초 | Python numpy·cv2(수묵 엔진) + 합성 거문고·북 | **최종 완성(2026-11-10, 1080p)** — 떨리는 손 이야기 v3. 다시 만들기: `jeom/README.md` '다시 만들기(최종본)'. 기법 정리: `_kit/skills/ink-wash-animation`. 영상(mp4)은 저장소 제외 |
| `ideas/` | 다음 작품 기획 | — | — | 후보 검토(`2026-11-09_review_and_pitches.md`), 〈점〉·〈파루〉 스토리 확장(`2026-11-09_jeom_paru_story.md`), 무음 기술 시험(`tests/`). 〈파루〉는 다음 후보 |

### 2026-11-09 v2 변경 공통
- 엔딩의 `GoXoN × Claude · every frame is code` 문구 **전부 삭제**.
- 대신 허상공방 크레딧(`_shared/credit_overlay.py`): D2Coding 타이핑 두 줄 `Created & Coded by L.S.M.` / `허상공방 虛像工房 Project` + 白文 낙관 `虛像工房`. **타이핑 소리 없음.**
  - 빛지기·홀씨: 우측 하단. 허수아비: 좌측 하단(제목 '허수아비의 겨울'은 우상단 유지).
- 엔딩이 갑자기 끊기지 않도록 마지막 컷 연장 + 음악 꼬리 추가(빛지기 60→67s, 홀씨 90→97s, 허수아비 125→137s).

### 〈허수아비의 겨울〉 v2 컷 변경 (사용자 지시)
- **C6-1 신설(3s)**: C6에서 다가온 매가 그 자리에서 돌격 → 돌풍에 왼팔 짚단이 휘어 매를 후려침(흰 섬광 1프레임, 깃털) → C7(바람이 이미 부는 상태에서 시작).
  - 구현: `cel.py` jiibi 파라미터 `whipL`, `whip_dir`(짚단 늘어남·방향).
- **C16**: 풀리는 실을 옷과 같은 파란 실로(`yarn()`, `fray_cuff()`). 이전엔 흰빛 실이라 옷에서 나온 실로 안 읽혔음.
- **C17 → 17a(2s) / 17-1(4s, 콩이 CU) / 17b(5s)**: 끊기자마자 구하지 않고, 얼어서 날갯짓을 못 하는 콩이(세 번 시도, 점점 약하게, 입김·서리, 눈 감음)로 긴장 → 허수아비가 고개 돌리고 팔 뻗으며 막대가 세 번 삐걱 꺾여 닿고 품에 안음 → 그제야 눈이 다시 내림. 정적(snap 이후 무음)은 17b 끝까지 유지.
- **C20**: 다시 일어나지 않고 허리 꺾인 채 콩이가 날 때 **팔만 펴짐**. 오른쪽에서 부는 돌풍에 꺾인 무게를 못 이겨 **왼쪽(꺾인 쪽)으로 쓰러짐**. `cel.py` `topple_dir=-1`.
- **C21·C22**: 쓰러진 방향에 맞춰 모자 둥지·콩이 가족·새싹을 머리 쪽(왼쪽)으로 재배치(`HAT_REST=(1104,990)`).
- 오디오: `audio.py`는 옛 125s 시각표로 쓰여 있고 `WARP_OLD/WARP_NEW` 구간 선형 맵으로 새 137s에 맞춤. 새 효과음은 `raw=True`로 새 시각에 직접 배치.
- 수정 전 코드: `scarecrow/v1_backup/`. 수정 샘플 시트: `scarecrow/v2_revision_samples.png`.

## 재현(렌더) 방법
원래 작업 경로는 `/home/claude/<작품>/` 이었다. 일부 스크립트(특히 `sumbi/`)는 절대경로를 쓰므로 그대로 쓰려면:
```bash
for d in orbit keeper holssi scarecrow sumbi; do ln -s "$PWD/$d" /home/claude/$d; done
pip install pycairo numpy scipy opencv-python pillow --break-system-packages
# 폰트: Noto Serif/Sans CJK (시스템), D2Coding은 _shared/fonts
```
- 빛지기: `cd keeper && python3 audio.py && python3 render.py full` → `chunks/list.txt` concat + `keeper.wav` mux.
- 홀씨: `cd holssi && python3 audio.py && python3 render.py full` (동일).
- 허수아비: `cd scarecrow && python3 audio.py` (→ `out/scarecrow.wav`), `python3 film.py range 0 137 out/v.mp4`, 그다음 ffmpeg로 mux.
  - 정지 확인: `python3 film.py still C17:1.0`(CUTS 인덱스 주의: C6_1, C17a/17_1/17b가 끼어 번호가 밀림).
  - 첫 실행 시 포스터컬러 배경과 하모니 프레임을 `cache/`에 새로 칠함(수 분).
- 숨비: `sumbi/three/NOTES.md`, `sumbi/story-bible.md` 참고(three@0.160, Playwright Chromium 헤드리스, `assemble.py`).

## 작업 규칙 (사용자 지시)
- 시간이 드는 전체 렌더 전에 **정지 샘플 → 짧은 무음 움직임 시험 → 컨펌 → 전체 렌더**.
- 샘플은 실제 크기로 확인하고 보낸다. 컷 경계 앞뒤(위치·크기 연결)를 반드시 확인 — v2에서 6→6-1 매 위치 불연속을 사용자가 지적함.
- 노하우 누적: Claude 스킬 `cel-anime-direction`(셀), `ink-wash-animation`(수묵) — 사본 `_kit/skills/`, 다른 계정에서는 `_kit/README.md`대로 등록. 그 밖에 `scarecrow/knowhow.md`, `sumbi/postmortem.md`, `jeom/preproduction.md`.

## 공용 자산 `_shared/`
- `credit_overlay.py` — `apply(img, t_since_start, side='right'|'left', bottom=px)`. 그림 영역(float 0..1) 위에 합성.
- `seal_baimun3.npy` — 낙관 RGBA 캐시, `fonts/d2coding-full.ttf`.
