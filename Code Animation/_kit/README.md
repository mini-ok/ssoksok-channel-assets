# Code Animation 키트

다른 Claude 계정·새 세션에서 코드 애니메이션 작업을 이어가기 위한 묶음.

## 1. 스킬 설치 (claude.ai → 설정 → Capabilities → Skills → 업로드)
- `cel-anime-direction.skill` — 셀 애니메이션 연출·제작 스킬(〈숨비〉 회고까지 반영된 최신본). 셀 작품의 **핵심.**
- `ink-wash-animation.skill` — 수묵·먹 번짐 코드 애니메이션 스킬(〈점〉 최종본까지의 검증 기법·작업 순서·체크리스트). 수묵 작품의 **핵심.**
- `code-3d-character-animation.skill` — three.js 3D 캐릭터 애니매틱 + Blender 최종 렌더 스킬(〈심장의 휴가〉 검증: 충돌 검사, Blender 차이 보완, PC 대기열 렌더, 렌더 뒤 점검). 3D 작품의 **핵심.**
- `screenplay-writing.skill`, `content-plan.skill` — 대본·기획 단계에 쓴 스킬(선택).
- `skills/` 폴더는 같은 내용의 원본 SKILL.md.

## 2. 엔진·작품 소스
엔진은 별도 패키지가 아니라 각 작품 폴더 안의 코드다. GitHub `mini-ok/ssoksok-channel-assets` 의 `Code Animation/` 에 있다.
- Python 셀 엔진: `scarecrow/` (cel.py 캐릭터 셀, painter.py 포스터컬러 배경, eng.py 합성·필름 후처리, audio.py 합성 사운드) — 가장 완성도 높은 기준 구현.
- three.js 3D 셀: `sumbi/three/` (core.js 패스 렌더, finish.py 셀 마감).
- 수묵 엔진: `jeom/engine/` (paper·brush·inkmm 먹 번짐·rain 붓 비·room 화실·after 아침 종이) + `jeom/animatic3.py`(컷 렌더)·`jeom/anim_audio3.py`·`jeom/audio/instruments.py`(거문고·북 물리 모형). 다시 만들기: `jeom/README.md`.
- 3D 캐릭터: `char3d/`(three.js 애니매틱·`export_scene.js`·`blender/heart_pixar.py`·`blender/run_pc.py`). 다시 만들기: `char3d/README.md`.
- 공용 크레딧: `_shared/credit_overlay.py` (이 키트에도 사본).
- 시작점: `Code Animation/README.md`.

## 3. 환경 준비
```bash
bash setup.sh        # 저장소 clone, ffmpeg·cairo·CJK 폰트, pip 패키지, three@0.160, 경로 링크
```
필요한 것: Python 3.12+, Node 22, ffmpeg, pycairo, numpy, scipy, opencv, pillow, three@0.160.0, Playwright Chromium(숨비만), Noto CJK 폰트.

## 4. 새 세션에 줄 첫 메시지 예시
> GitHub mini-ok/ssoksok-channel-assets 의 `Code Animation/README.md` 를 읽고, cel-anime-direction 스킬을 따라 〈허수아비의 겨울〉 이어서 작업하자.
> GitHub mini-ok/ssoksok-channel-assets 의 `Code Animation/README.md`·`CLAUDE.md` 를 읽고, ink-wash-animation 스킬로 〈점〉 엔진을 이어 다음 수묵 작품을 시작하자.

작업 규칙은 `Code Animation/CLAUDE.md`(샘플 → 컨펌 → 전체 렌더, 실제 크기 확인, 공개 저장소에 작법 용어 금지).
