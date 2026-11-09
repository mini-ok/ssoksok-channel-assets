# three.js 기술 시험 1 — 곶자왈 숲 트래킹 (C9, 3초) 2026-11-06

## 파이프라인
- forest.html (three 0.160, three.min.js) — 장면: 땅(노이즈), 용암석+이끼 뚜껑, 굽은 나무(Tube+테이퍼)+가지+담쟁이, 수관 덩어리, 높은 수관층, 미역 리본, 고사리(ShapeGeometry frond, z-rot로 들어올림), 이끼 덩이. MeshToonMaterial 3단 램프(Nearest), BasicShadowMap(딱딱한 그림자), bias -0.003 / normalBias 0.12(줄무늬 그림자 해결), fog.
- 패스 4종: color / id(객체별 단색) / normal / depth → render.js (playwright, swiftshader) 투스로만 렌더, 4패스 약 2.1초/장.
- 방식 A cel3d.py (프레임별): id·normal(<0.15)·depth 경계 → 저주파 흔들림 + 투스마다 미세 보일 → 깊이에 따른 굵기, 컬러 홀드 라인, 그린 빛기둥, 종이, cel_finish, film_post. 마감 약 1초/장.
- 방식 B multiplane.py: plates.js가 3000px 넓은 판을 층별(far z<-9 + 땅 / mid -9~-2.5 / near >-2.5)로 투명 배경 렌더(body 배경 transparent + omitBackground 필수) → 층마다 painter로 한 번 칠하고 잉크도 한 번(npz 캐시) → 프레임마다 시차(초점거리 1510px, 깊이 17/10/5, 하늘 30)로 밀기 + 잉크만 보일.
## 교훈
- 매 프레임 painter(21초/장)는 너무 느리고 붓질이 매번 바뀌어 들끓을 위험 → 배경은 '한 번 칠해 밀기'(멀티플레인)가 정답에 가깝다.
- 기본 툰 + 얇은 선 = 로우폴리 게임처럼 보임. 선은 굵고(1.0~2.4px) 진하게(로컬색×0.28).
- 구 메시의 면 경계가 모서리 선으로 잡히면 스테인드글라스 → 법선 기준 0.15로 엄격하게.
- 고사리 톱니(주파수 높음)는 앨리어싱처럼 보임 → 잎 갈래는 큼직하게(sin 16), antialias true.
- 남은 과제: 식물 디자인(고사리·덤불)이 별 모양 오려 붙인 판 같음 → 셀 배경 화가처럼 갈래·잎맥 디자인 필요. 앞으로 나아가는 카메라(C25)는 멀티플레인 불가 → 프레임별 3D 또는 층 확대.
