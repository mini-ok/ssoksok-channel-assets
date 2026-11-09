# 궤도 (ORBIT) — 1분 코드 애니메이션

GoXoN × Claude. 외부 이미지·영상·음원 없이 **전부 Python 코드**로 렌더링·합성한 60초 단편.
모든 프레임은 시간 t의 순수 함수라서 어느 프레임이든 독립적으로 다시 그릴 수 있다.

- 사양: 1920×1080, 30fps, 60초, H.264 + AAC (스테레오)
- 완성본 `ORBIT_궤도.mp4`(약 44MB)와 `orbit.wav`는 용량 때문에 이 저장소에 올리지 않았다. 아래 방법으로 재생성한다.

## 대본

**로그라인:** 우주 반대편에서 태어난 두 빛이 서로를 향해 궤적을 그리고, 만나고, 헤어지고,
남은 빛이 사라진 빛의 자리에 새 별을 남긴다.

**연출:** 대사 없이 빛·궤적·파티클로만 말하는 무성 서사. 자막은 마지막 한 줄뿐.

| 시간 | 시퀀스 | 내용 |
|---|---|---|
| 0:00–0:10 | 고독 | 어둠 속에서 푸른 빛 A가 켜지고 느리게 떠돈다. 타이틀 "궤도 · ORBIT" |
| 0:10–0:20 | 발견 | 반대편에서 주황빛 B가 켜진다. 두 궤적이 서로를 향해 휜다 |
| 0:20–0:35 | 만남 | 이중 나선 궤도. 색이 보랏빛으로 섞이고 카메라가 당겨 들어간다. 음악 상승 |
| 0:35–0:45 | 이별 | 충돌, 흰 플래시, 충격파. 소리가 끊긴다. B는 파티클로 흩어져 사라진다 |
| 0:45–0:55 | 잔향 | A가 파편 위를 돈다. 파편이 두 궤도 모양의 성좌로 모인다 |
| 0:55–1:00 | 탄생 | 중심에서 보랏빛 새 별이 켜지고 카메라가 빠지며 은하 전체가 드러난다 |

**마지막 자막:** 사라진 빛은, 다른 빛이 된다.

## 기술 요약

- 광원은 가산(additive) 스플랫 + 멀티스케일 블룸 + 애너모픽 스트릭, 톤매핑 `1 - exp(-x)`
- 궤도는 해석적 경로(`A_pos`, `B_pos`)로 정의. 파티클은 상태 없는(stateless) 수식 → 프레임 병렬 렌더 가능
- 은하는 로그 나선 팔 약 13만 개 별로 절차 생성
- 사운드는 numpy 가산 합성(패드·플럭·벨·서브 붐) + 합성 리버브. 타임라인은 `render.py`와 동기화
- 임팩트(36.0s)가 BAR=2.25s(106.67bpm)의 16번째 마디 시작과 정확히 일치

## 다시 만들기

```bash
pip install numpy opencv-python pillow scipy   # + ffmpeg 필요
python3 audio.py                  # orbit.wav 생성 (약 5초)
python3 render.py test 2 36 57.5  # 확인용 프레임 (test/*.png)
python3 render.py full            # chunks/c00~c11.mp4 렌더 (2코어 약 5분)
cd chunks && ffmpeg -f concat -safe 0 -i list.txt -i ../orbit.wav \
  -c:v copy -c:a aac -b:a 224k -movflags +faststart -shortest ../ORBIT.mp4
```

자막 폰트: Noto Serif CJK KR Light (`/usr/share/fonts/opentype/noto/NotoSerifCJK-Light.ttc`, index 1)

## 알려진 사항

- 은하 장면 하단 크레딧("GoXoN × Claude — every frame is code")이 우측에서 약간 잘려 보인다.
