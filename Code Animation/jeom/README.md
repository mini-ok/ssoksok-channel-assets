# 〈점〉 JEOM — 제작 중

먹 한 방울이 화선지 구석에서 눈 없는 용의 눈동자 자리까지 가는 약 2분 단편. 결말 (c): 용은 날아가고 점이 지나온 길이 한 획 그림으로 남는다.

## 상태 (2026-11-09)
| 단계 | 상태 | 파일 |
|---|---|---|
| 제작 전 검토 | 완료 | `preproduction.md` |
| 브리프 | 완료(확인 대기) | `brief.md` |
| 씬 리스트 v1 + 종이 지도 | 완료(확인 대기) | `scenelist.md`, `sheets/ms_map.png` |
| 모델 시트 v1(용·지도·눈·발톱·점 상태) | **확인 대기** | `sheets/model_sheet_v1.png` |
| 애니마틱 | 다음 | — |

## 엔진 (`engine/`)
- `paper.py`: 화선지. mm 좌표, 20mm 칸 시드로 섬유를 만들어 배율과 무관하게 같은 자리 = 같은 섬유. 칸 타일은 `cache/paper/`에 저장(첫 전체 화면 약 45초, 이후 몇 초).
- `brush.py`: 붓 획 v2(`Stroke`)와 발묵 덩어리(`Wash`). 붓털 64가닥의 먹 양 표를 획 좌표로 펴서 찍음. 젖으면 한 덩어리, 마르면 바깥 털부터 끊겨 비백. 가장자리는 섬유로 거칠게, 젖은 획은 섬유를 따라 번짐.
- `dragon.py`: 눈 없는 용. 모든 획이 여기서만 나온다. 몸통은 척추 곡선 매개변수로 정의(C11에서 몸 선을 따라 밀기 위함). 눈자리 `E = (300, 112)`, `eye_blank()`가 눈 안쪽을 비운다.
- `look.py`: 먹 흡수 합성, 조명(등잔·밤·번개·은빛·아침), 필름 마감, 레터박스.
- 번짐(점) 엔진은 `ideas/tests/jeom/`의 번짐 사슬 모델을 mm 좌표로 옮겨 애니마틱 단계에서 붙인다.

## 다시 만들기
```bash
pip install pycairo numpy scipy opencv-python-headless pillow scikit-image --break-system-packages
python3 model_sheet.py        # sheets/ 에 모델 시트
```
