# Code Animation 키트

다른 Claude 계정·새 세션에서 코드 애니메이션 작업을 이어가기 위한 묶음.

## 1. 스킬 설치 (claude.ai → 설정 → Capabilities → Skills → 업로드)
- `cel-anime-direction.skill` — 셀 애니메이션 연출·제작 스킬(〈숨비〉 회고까지 반영된 최신본). **핵심.**
- `screenplay-writing.skill`, `content-plan.skill` — 대본·기획 단계에 쓴 스킬(선택).
- `skills/` 폴더는 같은 내용의 원본 SKILL.md.

## 2. 엔진·작품 소스
엔진은 별도 패키지가 아니라 각 작품 폴더 안의 코드다. GitHub `mini-ok/ssoksok-channel-assets` 의 `Code Animation/` 에 있다.
- Python 셀 엔진: `scarecrow/` (cel.py 캐릭터 셀, painter.py 포스터컬러 배경, eng.py 합성·필름 후처리, audio.py 합성 사운드) — 가장 완성도 높은 기준 구현.
- three.js 3D 셀: `sumbi/three/` (core.js 패스 렌더, finish.py 셀 마감).
- 공용 크레딧: `_shared/credit_overlay.py` (이 키트에도 사본).
- 시작점: `Code Animation/README.md`.

## 3. 환경 준비
```bash
bash setup.sh        # 저장소 clone, ffmpeg·cairo·CJK 폰트, pip 패키지, three@0.160, 경로 링크
```
필요한 것: Python 3.12+, Node 22, ffmpeg, pycairo, numpy, scipy, opencv, pillow, three@0.160.0, Playwright Chromium(숨비만), Noto CJK 폰트.

## 4. 새 세션에 줄 첫 메시지 예시
> GitHub mini-ok/ssoksok-channel-assets 의 `Code Animation/README.md` 를 읽고, cel-anime-direction 스킬을 따라 〈허수아비의 겨울〉 이어서 작업하자.
