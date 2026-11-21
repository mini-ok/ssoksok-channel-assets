# vfx — 허상공방 공용 비주얼 엔진

2026-11-21, Claude Fable 5.2 화제작 분석에서 "남들이 먼저 만들어 두던 도구"를 우리 엔진으로 옮긴 것. 작품 엔진(수묵·종이·3D·지식 쇼츠)이 함께 쓴다.
실행 위치는 `Code Animation/_kit/`. 필요한 것: numpy, opencv, scipy, ffmpeg.

| 모듈 | 하는 일 | 쓰는 법 |
|---|---|---|
| `qa.py` | 렌더 검수: 접촉 시트, 컷 띠, 폰 폭 시트, 16×9 칸 깜박임 지도, 3×3 움직임 점수, 정지 구간, 음량 → P0/P1/사람이 볼 것 | `python3 -m vfx.qa report <mp4> --out <dir>` (낱개: `sheet` `cuts` `phone` `flicker` `audio`) |
| `loud.py` | 음량 −14 LUFS·트루 피크 −1.5 이하. 인코딩 뒤 다시 재서 넘으면 천장을 낮춤 | `python3 -m vfx.loud <in> <out.wav>` / `python3 -m vfx.loud <audio> <out.mp4> --mux <video.mp4>` |
| `timeline.py` | 박자표 `Beat`, 샷 표 `Shots`: 그림·소리가 같은 표를 읽는다. `Beat.hit()` = 사건 + 1프레임 | `from vfx.timeline import Beat, Shots` |
| `post.py` | 후처리 사슬(순서 고정) `grade()`, 하위 프레임 평균 `subframes()`, 섬광 노출 곡선 `flash_dip()` | `from vfx import post` |
| `ink.py` | 먹·물감 합성 `종이 × exp(−흡광도)`, 과다 검사, 섬유, 마름 | `from vfx import ink` |

## 2026-11-21 기존 결과물에 돌려 본 값 (검수 기준선)
| 영상 | 깜박임 평균 / 최대 칸 | 음량 LUFS | 트루 피크 dBFS |
|---|---|---|---|
| 빛지기 v2 | 0.44 / 3.0 | −15.1 | +2.4 |
| 홀씨 v2 | 0.24 / 0.42 | −14.0 | +4.0 |
| 허수아비의 겨울 v2 | 0.40 / 0.74 | −12.4 | +1.4 |
| 지식 쇼츠 견본(적용 전) | 0.23 / 0.9 | −15.6 | +2.5 |
| 지식 쇼츠 견본(적용 후) | 0.33 / 1.09 | −14.8 | −5.4 |

- 네 편 모두 트루 피크가 0을 넘었다(`loudnorm` 한 번 돌리기 + AAC 인코딩이 날카로운 타격에서 피크를 올림). 앞으로는 `vfx.loud --mux`로 붙인다.
- 빛지기의 깜박임 큰 칸(행 4·열 8, 6.5초 부근)과 화면 전체 밝기 튐은 번개·등대 불빛 연출일 수 있어 사람이 확인해야 한다.
- 깜박임 값은 결(그레인)과 압축에도 반응한다. 같은 작품의 앞뒤 판을 비교하는 데 쓰고, 작품끼리 절대 비교는 하지 않는다.

스킬: 비공개 키트 `heosang-kit`의 `vk0-visual-kit`(길잡이)와 `vk1`~`vk6`.
