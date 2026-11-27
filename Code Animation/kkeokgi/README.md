# 〈꺾기 KKEOKGI〉 — 로봇 춤 × 화풍 아홉 가지 모션그래픽

25.6초(150 BPM, 64박), 16:9, 30 fps. 정면 2D 로봇 뼈대가 팝핑·락킹·팔 물결·킥·물구나무·프리즈를 박마다 꺾어 추고,
같은 동작을 먹·셀·청사진·네온·입자·글자·만화경·글리치·분할 화면이 번갈아 그린다. 대사 없음.

## 파일
- `nums.py` — 숫자 파일: 박자표, 포즈 표(관절 각도), 동작 순서(`SEQ`), 샷 표(`SHOTS`: 시작 박·화풍·배율·넘김 방식), 색, 글자.
- `fig.py` — 포즈 보간(3프레임에 넘어가 살짝 넘쳤다 멎는 back-out)과 순운동학, 끝점 방출점(`emitters`).
- `scene.py` — `frame(t, W, H)` 시간의 순수 함수. 화풍 함수 9개(`st_ink` `st_cel` `st_blue` `st_neon` `st_part` `st_typo` `st_kal` `st_glitch` `st_grid`)와 샷 전환.
- `audio.py` — 같은 `nums.py`의 동작 순서·샷 표로 소리 합성(북·채·잔박, 거문고 가락, 동작마다 관절 소리, 전환 휙·쇳소리).
- `render.py`, `posesheet.py` — 렌더, 포즈 시트(뼈대 선화로 포즈 점검).

## 다시 만들기
```bash
cd "Code Animation/kkeokgi"
python3 posesheet.py poses.jpg                      # 포즈 점검
python3 render.py --stills out_dir 2.3 8.3 ...      # 정지 프레임(W, H 환경변수)
python3 audio.py raw.wav
python3 render.py video.mp4 1920 1080               # 540p(960 540)는 약 2분, 1080p는 약 8~10분
cd ../_kit && python3 -m vfx.loud raw.wav out.mp4 --mux video.mp4 && python3 -m vfx.qa report out.mp4 --out qa
```
필요: `jeom/audio/instruments.py`(거문고·북), `_shared/seal_baimun3.npy`, `_kit/vfx`, Noto Serif CJK Bold.

## 알려진 약점
- 14마디(52–56박)는 반 박마다 화풍이 바뀌어 초당 약 5회 화면이 통째로 바뀐다. 광과민 안전 기준(초당 3회)을 넘으므로 공개 전에 박 단위로 늦출 것.
- 만화경 구간은 어둡고 로봇이 잘 안 읽힌다. 프리즈는 구르다 멈춘 듯 어색하다. 정면 2D라 윈드밀처럼 몸이 도는 동작은 없다.
- 청사진 구간의 작은 글자는 540p에서 읽히지 않는다.
