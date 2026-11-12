# 세로 숏츠 (1080×1920) — 빛지기 · 홀씨 · 허수아비의 겨울

가로 v2 완성본(1920×1080)을 세로로 다시 짠다. 다시 그리지 않고 **잘라서 재구성**한다.

## 화면 구성
- 가운데 **4:5 그림 창**(1080×1350): 컷마다 주인공·사건이 있는 쪽으로 창이 옮겨 가고, 컷 안에서는 천천히 따라간다.
- 위·아래 띠: 같은 장면을 흐리게 깔고, 위 띠에 작품 제목(한글 + 영문), 아래 띠에 엔딩 크레딧.
- 엔딩 크레딧: `_shared/credit_overlay.py`의 `side='center'` — 두 줄 문장 + 낙관 **전체 묶음이 가운데**. 타이핑 소리 없음.
- 가로판의 크레딧은 세로 창에서 잘리므로, 엔딩 구간만 **크레딧 없이 다시 렌더**(`NOCREDIT=1`)해서 쓴다.
  - 빛지기는 `TITLE_X=1010`으로 제목을 옮겨 제목과 등대가 한 창에 들어오게 렌더.
  - 허수아비는 `NOCREDIT=1`이면 가로판 제목 자막도 빠지고, 위 띠 제목이 대신한다.
- 길이·음악은 가로 v2와 같다(67s / 97s / 137s).

## 순서
```bash
# 0) 가로 v2 mp4가 $VID_ROOT/<작품>/out/ 에 있어야 한다(영상은 git에 없음 → 각 작품 폴더에서 렌더)
# 1) 컷별 창 위치 분석(움직임 에너지) → <name>_track.json   (저장소에 결과 포함)
python3 analyze.py keeper  <keeper_v2.mp4>  138 804  "[0,5,9,12,16,20,23,26,29,32,35,39,42,45,49,52,55,57,67]"
python3 analyze.py holssi  <holssi_v2.mp4>  0 1080   "[0,7,12,17,20,26,31,36,40,48,52,56,60,64,76,80,83,86,97]"
python3 analyze.py scarecrow <scarecrow_v2.mp4> 0 1080 "[0,7,12,17,23,27,31,34,38,42,50,56,61,67,72,77,83,87,89,93,98,103,110,122,126,137]"
# 2) 검수 시트(컷마다 3프레임 + 창 표시) → <name>_sheet.png
python3 sheet.py keeper <keeper_v2.mp4>
# 3) 크레딧 없는 엔딩 구간
TITLE_X=1010 python3 tail_nc.py <repo>/Code\ Animation/keeper 57 67 $PWD/keeper_tail.mp4
python3 tail_nc.py <repo>/Code\ Animation/holssi 86 97 $PWD/holssi_tail.mp4
(cd ../scarecrow && NOCREDIT=1 python3 film.py range 126 137 ../shorts/scarecrow_tail.mp4)
# 4) 정지 확인 → 전체
python3 vert.py holssi 14 46 93        # 지정 시각 PNG
python3 vert.py holssi                 # holssi_shorts.mp4
```
- 자동 분석이 틀린 컷은 `vert.py`의 `CFG[name]['keys']`에 **컷 번호 → [(컷 내 진행 0~1, 창 중심 x), …]**로 손으로 고정한다.
- 빛지기는 2.39:1 레터박스라(그림 높이 804) 확대가 약 1.7배, 나머지는 약 1.25배.
