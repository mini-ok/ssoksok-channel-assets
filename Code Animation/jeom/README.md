# 〈점〉 JEOM — 제작 중

먹 한 방울이 화선지 구석에서 눈 없는 용의 눈동자 자리까지 가는 약 2분 단편. 결말 (c): 용은 날아가고 점이 지나온 길이 한 획 그림으로 남는다.

## 상태 (2026-11-09)
| 단계 | 상태 | 파일 |
|---|---|---|
| 제작 전 검토 | 완료 | `preproduction.md` |
| 브리프 | 완료(확인 대기) | `brief.md` |
| 씬 리스트 v1 + 종이 지도 | 완료(확인 대기) | `scenelist.md`, `sheets/ms_map.png` |
| 모델 시트 v1(용·지도·눈·발톱·점 상태) | 확인됨(형태 유지, 접사 부분만 보강) | `sheets/model_sheet_v1.png` |
| 결정 사항 | 낙관 = 허상공방, 악기 = 거문고(점)·대금(용) | `preproduction.md` 5장, `audio/sketch.py` |
| 애니마틱 v1(126초, 960×540, 임시음) | **확인 대기** | `animatic.py`, `anim_audio.py`, `sheets/animatic_v1_contact.png` |

## 엔진 (`engine/`)
- `paper.py`: 화선지. mm 좌표, 20mm 칸 시드로 섬유를 만들어 배율과 무관하게 같은 자리 = 같은 섬유. 칸 타일은 `cache/paper/`에 저장(첫 전체 화면 약 45초, 이후 몇 초).
- `brush.py`: 붓 획 v2(`Stroke`)와 발묵 덩어리(`Wash`). 붓털 64가닥의 먹 양 표를 획 좌표로 펴서 찍음. 젖으면 한 덩어리, 마르면 바깥 털부터 끊겨 비백. 가장자리는 섬유로 거칠게, 젖은 획은 섬유를 따라 번짐.
- `dragon.py`: 눈 없는 용. 모든 획이 여기서만 나온다. 몸통은 척추 곡선 매개변수로 정의(C11에서 몸 선을 따라 밀기 위함). 눈자리 `E = (300, 112)`, `eye_blank()`가 눈 안쪽을 비운다.
- `look.py`: 먹 흡수 합성, 조명(등잔·밤·번개·은빛·아침), 필름 마감, 레터박스.
- `inkmm.py`: 점의 번짐 사슬(mm 격자, t의 순수 함수). 물(둥근 방울·길쭉한 방울·바람 물줄기), 단계별 블룸, 이어지는 가는 물줄기, 튄 먹 합류, 건조 테두리, 규칙 깨기(E로 세 번 모임), 눈동자(`pupil`).
- `timeline.py`: 컷 시각표, 물·단계·튄 먹·번개·자·낙관·제목의 위치(mm)와 시각. scenelist.md와 같은 숫자.

## 다시 만들기
```bash
pip install pycairo numpy scipy opencv-python-headless pillow scikit-image --break-system-packages
python3 model_sheet.py        # sheets/ 에 모델 시트
python3 animatic.py frames 0 63 & python3 animatic.py frames 63 126   # 2코어 약 5분
python3 animatic.py encode    # cache/jeom_animatic_v1.mp4 (임시음 포함)
```
애니마틱 자리표시: C1 화실, C2 붓, C11b 창밖은 회색 상자 수준. 본 제작에서 다시 그린다.
