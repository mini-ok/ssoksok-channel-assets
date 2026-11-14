# 〈심장의 휴가〉 HEART'S DAY OFF — 3D 캐릭터 애니메이션

쏙쏙 건강백과의 2D 캐릭터(심장·장·간·뇌)를 코드로 부풀려 3D로 만들고, three.js 실시간 애니매틱 → Blender(Cycles) 최종 렌더까지 모두 코드로 만든 2분 15초 무대사 단편.

- 이야기: 한 번도 쉬어 본 적 없는 심장이 휴가권을 받고 몸속 회사를 돌아다니며 쉴 곳을 찾는다. 해먹에서 잠든 사이 몸 전체가 멈춰 가자, 휴가권을 못에 걸고 다시 뛴다. 밤이 되자 주인의 손이 가슴에 얹히고, 박동 사이에 짧은 쉼이 찾아온다.
- 상태(2026-11-14): 애니매틱 v2(17컷 + 타이틀, 960×540) 완성. **Blender 판 v1 완성**(20개 렌더 컷 + 타이틀 + 소리, 1280×720, 135.2초). 영상(mp4)은 저장소에 넣지 않음.

## 구조
| 파일 | 하는 일 |
|---|---|
| `inflate.py` | 2D 캐릭터 실루엣(chars.py 경로)을 부풀려 3D 몸 메시로 |
| `chars3d.js`, `heart.js` | 캐릭터 리그(관절 = Group 계층), 소품(휴가권·병·걸레·상자), `pose()`·`setFace()`·`hold()`·`prop()` |
| `face.js` | 표정 19종을 Canvas 2D로 그려 몸 텍스처에 합성(깜빡임·시선) |
| `anim.js` | 이징, `path()`(구간 단위 사다리꼴 속도 + 앞을 내다보는 방향, 툭툭 끊기지 않는 걷기) |
| `sets/*.js` | 공간 6곳(펌프 공장·장 연구소·간 공장·뇌 관제실·갈비뼈 휴가지·혈관 복도) + 바깥 세계(`common.js`) |
| `act1.js`~`act4.js`, `cuts.js` | 컷 정의 `{ dur, set, cast, apply(t, ctx) → { cam, key, hemi, env, bloom } }` |
| `film.html` | 컷 재생 페이지. `frame(cut, t)`, 매 프레임 충돌 검사 `window.collide`(MeshBVH), `exportCut`, `auditCut` |
| `render_film.mjs` | headless Chrome으로 렌더·검사·내보내기(아래) |
| `export_scene.js` | 컷 → GLB + JSON + 얼굴·화면 PNG (Blender용). 내보내기 전 차이 점검 `auditCut` |
| `blender/` | Blender 장면 구성·렌더(`heart_pixar.py`), PC 대기열 감시기(`run_pc.py`), 인코딩, 렌더 뒤 점검(`qa/`). **자세한 내용은 `blender/README.md`** |
| `sound_a1.py`, `sound_all.py`, `title.py` | 합성 효과음·음악, 타이틀(허상공방 인장) |
| `assemble.sh`, `assemble_blender.sh` | 애니매틱 합본 / Blender 컷 mp4 + 타이틀 + 소리 합본 |

## 실행
```bash
npm i three@0.187.0 three-mesh-bvh@0.9.18 puppeteer-core   # 스크립트는 puppeteer-core·Chrome 경로를 절대경로로 씀(필요하면 고칠 것)
python3 -m http.server 8124 &
node render_film.mjs still /tmp/s C8:3.0                 # 정지 한 장(W,H 환경변수로 크기)
NORENDER=1 node render_film.mjs check C6                 # 그리지 않고 모든 프레임 충돌만 빠르게 검사
node render_film.mjs cuts out C5 C6                      # 컷별 프레임 + mp4 + <컷>.collide.txt
node render_film.mjs eval C6:2.0 'R.heart.root.position'  # 아무 값이나 확인(출력은 grep '^\[' 로)
NORENDER=1 node render_film.mjs audit C7                 # Blender로 안 넘어가는 요소 점검
node render_film.mjs export ../export A1 C5 …            # Blender용 내보내기
./assemble.sh                                            # 애니매틱 합본
```

## 절대 규칙과 검수
- 캐릭터와 물건 사이에 물리 법칙 위배(통과·관통)가 없어야 한다. 모든 프레임에 BVH 충돌 검사를 돌리고, 검사기가 잡는 관통 0건을 확인한 뒤 완성으로 본다.
- 시간이 드는 렌더 전에 정지 샘플 → 짧은 움직임 → 컨펌 → 전체 렌더(`../CLAUDE.md`).
- Blender로 넘길 때는 차이 점검 → 보완안 의논 → 보완해서 내보내기.

## 기법 정리
스킬 `_kit/skills/code-3d-character-animation`(three.js 캐릭터 애니매틱 + Blender 최종 렌더 파이프라인, 검증된 값과 실패 사례).
