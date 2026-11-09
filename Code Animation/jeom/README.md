# 〈점〉 JEOM — 제작 중

**v2 (2026-11-09, 현재):** 손이 떨려 용의 눈을 찍지 못하는 늙은 화가. 그 떨림에서 떨어져 잘려 나갈 뻔한 먹 한 점이, 화가가 흘린 실패한 방울들을 모아 눈이 되고, 폭우에 지워져 가는 그림을 지키려 용과 함께 종이를 떠난다. 아침의 종이에는 밤사이의 흔적이 그림으로 남고, 화가의 눈물이 마지막 점을 찍는다. → `scenelist_v2.md`, `animatic2.py`

(v1: 먹 한 방울이 구석에서 눈자리까지 가는 약 2분 단편. 아래 v1 표·엔진 설명은 그대로 유효하고, v2는 그 엔진 위에 시험 장면들을 더했다.)

## 상태 (2026-11-09)
| 단계 | 상태 | 파일 |
|---|---|---|
| 제작 전 검토 | 완료 | `preproduction.md` |
| 브리프 | 완료(확인 대기) | `brief.md` |
| 씬 리스트 v1 + 종이 지도 | 완료(확인 대기) | `scenelist.md`, `sheets/ms_map.png` |
| 모델 시트 v1(용·지도·눈·발톱·점 상태) | 확인됨(형태 유지, 접사 부분만 보강) | `sheets/model_sheet_v1.png` |
| 결정 사항 | 낙관 = 허상공방, 악기 = 거문고(점)·대금(용) | `preproduction.md` 5장, `audio/sketch.py` |
| 애니마틱 v1(126초, 960×540, 임시음) | **확인 대기** | `animatic.py`, `anim_audio.py`, `sheets/animatic_v1_contact.png` |

## v3 최종 (2026-11-10) — 1차 완성
- 1920×1080, 24fps(그림은 투스 12장), 3분 11초, 소리(거문고 + 북 + 용 소리 합성 + 비·천둥) 포함. 씬 리스트 `scenelist_v3.md`, 렌더 `animatic3.py`, 소리 `anim_audio3.py`.
- 새 엔진: `engine/rain.py`(붓으로 그린 비), `engine/room.py`(화실 원경·실루엣·벽 그림자·새벽 햇살), `engine/after.py`(폭풍이 지나간 아침 종이 — 어느 화면에서든 같은 상태), `engine/scale.py`(배율).
- 다시 만들기(2코어, 약 1시간 30분):
```bash
export JEOM_SCALE=2
JEOM_RES=0.25 python3 tests/test_hand2.py      # C2·C3 (약 13분)
python3 tests/test_knife.py; python3 tests/test_leap.py   # C4, C17 + 아침 종이 기록(after.npz)
python3 animatic3.py cut C1 C2 C3 C4 C5 C6 J C14 C15 C16 &   # 메모리 8GB에서 두 개까지(세 개는 OOM)
python3 animatic3.py cut C17 C18 C19 C20 C21 C22 C23 C24 C25
# 인코딩: anim_audio3.build(wav, 191.5) 후 ffmpeg -framerate 12 -i cache/anim3_1920/a%05d.png -i wav -vf fps=24 -crf 17
```
- 캐시는 배율별 폴더(`cache/*_1920`)로 분리된다. 두 프로세스가 같은 캐시를 동시에 처음 만들면 깨진 파일을 읽을 수 있다 — 첫 렌더 전에 한 번 단독으로 import해 캐시를 만들어 둘 것.

## v2 상태
| 단계 | 상태 | 파일 |
|---|---|---|
| 씬 리스트 v2(21컷, 약 157초) | **확인 대기** | `scenelist_v2.md` |
| 애니마틱 v2(960×540, 임시음) | **확인 대기** | `animatic2.py`, `anim_audio2.py` → `cache/jeom_animatic_v2.mp4` |
| 떨리는 손(붓·그림자만) | 확인됨 | `tests/test_hand2.py` (v1 `test_hand.py`는 버린 방식) |
| 칼로 자르다 멈춤 | 시험 | `tests/test_knife.py` (칼집 자취 → `cache/knife_cut.npy`, 번짐 장벽으로도 씀) |
| 그림 속 용이 그대로 솟아오름 | 확인됨(방향) | `tests/test_leap.py` (등뼈 좌표 리그, 머리가 지나온 길, 구르는 돌아서기, 먹 뿌림) |
| 창밖 폭풍·비가 멎음 | 시험 | `tests/test_storm.py` |
| 눈물 → 눈동자 테 | 시험 | `tests/test_tear.py` |
| 화실 원경(실루엣·벽 그림자·바구니) | 시험 | `engine/room.py` |
| 비행(새 머리+새 몸) | 버림 | `tests/test_flight.py` — 붓 머리와 사실적 몸이 안 어울림, 원안 그림이 베이스여야 함 |

애니마틱 v2 다시 만들기: 시험들을 먼저 돌린 뒤(`JEOM_RES=0.25 python3 tests/test_hand2.py`, `test_knife.py`, `test_leap.py`, `test_storm.py`, `test_tear.py`)
`python3 animatic2.py cut J & python3 animatic2.py cut C1 C2 C3 C4 C5 C13 C14 C15 C16 C17 C18 C19 C20 C21` (2코어 약 8분) → `python3 animatic2.py encode`.

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
