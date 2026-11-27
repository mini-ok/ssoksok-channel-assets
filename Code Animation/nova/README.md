# nova — 허상공방 지식 쇼츠 2기 (규모 체감 모션그래픽)

다른 Claude 계정·새 세션이 이 폴더만 보고 같은 방식으로 쇼츠를 이어 만들 수 있게 정리한 문서다.
1기(같은 화풍의 규모 체감 쇼츠)는 `../scale/`, 종이 지식 쇼츠는 `../trivia/`, 채널 운영 규칙은 `../_channel/`.

- 형식: 세로 1080×1920, 30fps, 약 32초(본편 약 20초 + 마무리 문장 약 9초 + 끝 화면 3초), 대사 없음, 영·한 자막.
- 2026-11-26 기준 45편(`ep_*.py`). 영상(mp4)은 저장소에 넣지 않는다(코드로 다시 만든다). 사용자 PC 사본: `K:\AI\AI자동화애니메이션테스트\shorts\nova\`.

## 1. 지키는 규칙 (사용자 지시)
1. **편마다 화풍과 소리를 다르게**, 이야기·소재에 어울리게 고른다. 이미 쓴 화풍·악기와 겹치지 않는다(아래 4장 목록을 먼저 본다).
2. **주제**: 규모가 체감되고, 궁금증을 일으키고, 살면서 쓸모 있는 것. 이미 다룬 주제 반복 금지(5장). 금성·물속 소리는 쓰지 않는다.
3. **사실은 웹으로 확인**하고 출처를 끝 화면(`sources`)과 설명란에 쓴다. 직접 계산한 값은 화면과 출처에 "calculated / 계산"이라고 밝힌다. 가정(보폭 0.75m, 종이 0.1mm 등)도 출처 줄에 적는다.
4. **마무리 문장(coda)**: 불교·기독교·철학의 울림이 있는 짧은 3줄(영·한). 편마다 다르게, 앞 편과 같은 말 반복 금지.
5. **자막은 영·한 비슷한 크기**(영어 위, 한글 아래). 강조어는 `*별표*`로 감싸면 색이 바뀐다.
6. **길이를 채우려고 같은 장면을 반복하지 않는다.**
7. 공개 저장소이므로 사용자 고유 작법 용어를 쓰지 않는다. 비밀값(토큰·키)은 파일·대화에 넣지 않는다.

## 2. 한 편 만드는 순서
1. 주제 고르기 → 사실 2~4개를 웹에서 확인(출처 기록).
2. 화풍·소리 고르기(4장 목록과 겹치지 않게).
3. `ep_<이름>.py` 작성(3장 틀). 장면은 보통 4개(0–4초, 4–9.6초, 9.8–15초, 15–20.6초) + coda.
4. **정지 화면 확인**: `python3 ep_<이름>.py still /tmp/x.png 2 7 12 18` → 실제 크기(또는 절반)로 직접 열어 본다. 글자 겹침, 카드(위쪽 약 180~470px)와 그림 겹침, t=0 오류를 고친다.
5. 대기열에 넣고 렌더: `echo "nova <이름>" >> $NOVA_WORK/queue.txt` (대기열은 `tools/queue.sh` 하나만 돌린다).
6. 검수 보고 읽기: `$NOVA_WORK/qa_<이름>/report.md`와 `sheet_00.jpg`. P0가 있으면 고치고 다시 렌더.
7. 사용자에게 보내기 → 사용자 PC에 저장 → `tools/outbox_nova.py`로 업로드 대기열(shorts-outbox)에 넣기.

렌더는 한 편에 약 2~5분(2코어). 무거운 후처리(median blur, 큰 가우시안)를 프레임마다 하면 느려진다.

## 3. 코드 틀
`base.py`가 화면 크기, 카드, coda, 끝 화면, CLI를 맡는다. 편 파일은 그림(`draw`)과 소리(`sound`)만 직접 만든다.

```python
from base import *          # DW, DH(1080x1920), W, H(배율 적용), SC, ramp, smooth, txt, surf, arr, over, BLK, BOLD, SERIF ...
import sfx as S

def draw(t):                # 시각 t의 순수 함수. BGR float(H, W, 3) 0..1 을 돌려준다
    s, cr = surf()          # cairo 투명 판(좌표는 1080x1920 기준)
    ...                     # 장면별로 a = ramp(...) * (1 - ramp(...)) 로 들어오고 나간다
    return over(BG, s)      # 또는 np.ascontiguousarray(arr(s)[..., :3])

def sound(path):
    m = S.Mix(EP['DUR'], seed); tc = EP['t_coda']
    m.put('mus', t, S.piano(f, dur, g)); m.put('fx', t, S.bell(...)); m.put('amb', 0, S.drone(...))
    m.write(path, rev_mus=2.4, wet_mus=0.4)

EP = finalize(dict(t_coda=20.6, draw=draw, sound=sound, end_icon='star', grain=0.0,
    title_en_card='...', title_ko_card='...', pal=dict(hi=..., endbg=...),
    card_style=dict(box='paper', bg=..., ink=..., hi=..., y=180, fe=BOLD, fk=BLK),
    cards=[(0.3, 4.0, ['영어 1줄', '*강조* 2줄'], ['한글 1줄', '*강조* 2줄']), ...],
    coda=[('en', 'ko'), ('en', 'ko'), ('en', 'ko')],
    coda_style=dict(dim=0.5, blur=8, tint=..., ink=..., hi=..., fe=BOLD),
    sources=['출처 1', '출처 2 (calculated 표시)'],
    yt=dict(title_en='... #Shorts', title_ko='...')))

if __name__ == '__main__': main(EP)
```

CLI: `info` / `still <png> t1 t2 ...` / `one <png> t` / `frames <dir> k0 k1` / `sound <wav>`.
`make.sh <이름>`: 프레임(2프로세스) → 인코딩 → 소리 → `_kit/vfx.loud`(−14 LUFS) → `_kit/vfx.qa report` → 정리.

`sfx.py` 악기: piano, upright, organ, harpsichord, celesta, kalimba, pizz, pluck, koto, shakuhachi, ney, lute, gurdy, dulcimer, bowed, glassharp, theremin, steeldrum, handpan, musicbox, fm, taiko, kick, hihat, brush, tok, bell, beep, tick, modem, static, thunder, rain, rainstick, stream, swoosh, icecrack, metaldrone, drill, drone, typekey, typebell, bird, woodflute, chalk, step 등. 서명은 `grep -n "^def " sfx.py`.

## 4. 이미 쓴 화풍·소리 (새 편은 여기와 겹치지 않게)
| 편 | 화풍 | 소리 |
|---|---|---|
| cells | 현미경 염색 조직(H&E) | 물방울·마림바 |
| cleo | 파피루스 벽화 | 프레임드럼·현(히자즈) |
| sharks | 목판화 화석 도감 | 첼로 드론·낮은 북 |
| stardust | 우주 빛 입자 | 앰비언트 패드·종 |
| honey | 그림책 과슈 | 어쿠스틱 기타·셰이커 |
| breath | 한지 수묵 | 거문고·북·숨소리 |
| gold | 아이소메트릭 3D | 미니멀 전자음 |
| octopus | 심해 생물발광 선화 | 수중 저음·소나 |
| spin | 1970년대 옵셋 인쇄 | 사각파 신스 |
| people | 점묘화 | 합창 패드 |
| water | 수채화 | 시냇물·칼림바 |
| skyapple | 백과사전 동판화 | 하프시코드·바람 |
| bead | 칠판 분필 | 분필·발걸음·업라이트 피아노 |
| heart | 마티스 색종이 | 큰북·피치카토 |
| year | 시아노타입 청사진 | 초침·낮은 피아노 |
| sleep | 크레파스 | 첼레스타 자장가·빗소리 |
| lightning | 스테인드글라스 | 파이프오르간·천둥 |
| voyager | 골든 레코드 금선 도면 | 전파 잡음·신호음 |
| trees | 십자수 | 나무피리·새소리 |
| moon | 그림자극 | 핸드팬 |
| ice | 픽셀아트 | 바람·얼음 갈라짐 |
| sunlight | 아르데코 포스터 | 업라이트 베이스·브러시 |
| whale | 우키요에 | 고토·샤쿠하치 |
| words | 타자기 원고 | 타자 소리 |
| plankton | 규조류 만화경 | 글라스 하모니카 |
| olympus | 클레이 애니메이션 | 테레민 |
| heat | 열화상 카메라 | FM 패드·맥박 |
| light | 초록 CRT 터미널 | 모뎀음·FM 삑 |
| pantheon | 로마 모자이크 | 해머 덜시머 |
| halley | 중세 채색 필사본 | 류트·허디거디 |
| tern | 종이접기 | 오르골 |
| bristlecone | 유화 임파스토 | 활 현악 |
| sahara | 샌드 아트(빛 상자) | 레인스틱·네이 |
| kola | 스크래치보드 | 금속 드론·드릴 |
| bamboo | 스위스 국제주의 포스터 | 미니멀 테크노 |
| rubik | 바우하우스 | 스틸 드럼 |
| fold | 청사진 도면 | FM 아르페지오 |
| clock | 무성영화 | 래그타임 피아노·영사기 |
| neutron | 리소그래프 | 펄서 삑·FM 종 |
| hummer | 아르누보 | 뜯는 현·심장 박 |
| walk | 스텐실 그라피티 | 붐뱁 비트 |
| saturn | 60년대 사이키델릭 포스터 | 오르간 그루브 |
| cloud | 로코코 천장화 | 하프시코드 미뉴에트 |
| shrimp | 만화책(스크린톤) | 타이코·딱 |
| bones | 엑스레이 필름 | 유리 하프·웅웅 |

아직 안 쓴 후보 예: 네온사인, 레트로 신스웨이브, 리노컷 2색, 펠트 아플리케, 팝업북, 에브루(마블링), 수태극 자수, 빈티지 지도, 회로 기판, 와이어프레임 벡터, 조선 민화, 비잔틴 이콘.

## 5. 이미 다룬 주제 (반복 금지)
세포 37조, 클레오파트라와 달 착륙, 상어가 나무보다 먼저, 별에서 온 몸, 꿀 한 숟갈, 하루 2만 번 숨, 인류가 캔 금 정육면체, 문어 심장 셋, 지구 자전 속도, 지금까지 태어난 사람, 지구의 물 공, 하늘(대기) 두께, 태양계를 구슬로, 평생 심장 박동, 지구 역사 1년 달력, 평생 잠자는 시간, 번개 온도, 보이저 1호, 나무 3조 그루, 달이 멀어짐, 남극 얼음이 녹으면, 햇빛 8분 20초, 흰긴수염고래 심장, 하루 1만 6천 단어, 플랑크톤 산소, 올림푸스산, 체온 100W, 빛의 속도, 판테온 돔, 핼리 혜성, 북극제비갈매기, 므두셀라 나무, 초록 사하라, 콜라 시추공, 대나무 성장, 루빅 큐브 20수, 종이 42번 접기, 지구의 하루 중 인류, 중성자별 각설탕, 벌새 심장, 걸어서 지구 한 바퀴, 토성 밀도, 구름 무게, 딱총새우, 아기 뼈 300개.
(1기에서 버린 주제: 초 단위, 빛, 뉴런, 개미.)

## 6. 업로드 대기열(shorts-outbox)과 PC 저장
- 공개 저장소의 `shorts-outbox` 브랜치에 `index.json`({items:[{slug,dir,created}], per_run:2})과 `shorts/<slug>/video.mp4`·`meta.json`이 쌓인다. 업로더(예약 실행)가 **한 번에 2편(per_run 2)**씩 올린다. 업로드 쪽 안내: `../trivia/` 의 handoff 문서와 `../_channel/shorts_playbook.md`.
- 넣기: `tools/outbox_nova.py`의 META에 한 줄 추가(slug, ep, 영어 제목, 한글 제목, 영어 설명(출처 포함), 한글 설명, 태그) → `cd /tmp && NOVA_OUT=<mp4 폴더> python3 <경로>/tools/outbox_nova.py <slug> ...`. 영어 제목·설명에는 한글을 넣지 않는다. 제목 100자 이하.
- 이 스크립트는 `/tmp`에 outbox를 clone한다. 쌓이면 디스크가 찬다 — 쓸 때마다 `/tmp/tmp*`(index.json이 든 clone) 정리.
- 옛 1기 편을 새 화풍으로 다시 만들었을 때는 `tools/outbox_remake.py`(slug 뒤에 `_v2`).
- 사용자 PC 저장: 세션이 PC와 연결돼 있으면 보낸 파일을 `device_commit_files`로 `K:\AI\AI자동화애니메이션테스트\shorts\nova\<이름>.mp4`에 쓴다(한 번에 1024MB·50개 이하).

## 7. 겪은 함정
- `make.sh`는 `out/<이름>.mp4`가 있으면 **건너뛴다(SKIP)**. 고쳐서 다시 렌더할 때는 먼저 옛 mp4를 옮기거나 지운다.
- `make.sh`의 `info`는 `MG_SCALE=0.25`로 모듈을 불러온다. 모듈을 불러올 때 계산하는 마스크·표본이 작은 해상도에서도 돌아가야 한다(예: `rng.choice`에 `min(len, n)`).
- t=0에서 cairo `scale(0)`이 나면 죽는다 → `max(s, 1e-3)`. 정지 확인 때 t=0을 꼭 넣는다.
- 알파를 무시하는 도형 함수(예: 불투명 fill)는 장면 경계·coda 배경에 남는다 → 모든 그리기에 장면 알파를 곱한다.
- 큰 글리프(⅓ 등)가 글꼴에 없으면 빈칸 → `1/3`처럼 ASCII로.
- 작은 크기의 `~`는 빼기표처럼 보인다 → `≈`.
- 장면 경계 글자가 카드 영역(위 180~470px)과 겹치지 않게, 아래쪽 1500px 이하로는 끝 화면 출처와 안 겹치게.
- 검수 보고의 "끝 화면 밝기 튐", "정지 구간", "끝 무음"은 의도된 것. 필름 결처럼 일부러 넣은 깜박임은 P1로 나올 수 있다(사용자에게 알린다).
- 대화 세션의 백그라운드 프로세스는 턴이 끝나면 죽을 수 있다. 렌더를 기다릴 때는 턴 안에서 `sleep` 후 확인하고, `pgrep -af queue.sh`로 하나만 도는지 본다.

## 8. 새 세션 첫 메시지 예시
> GitHub mini-ok/ssoksok-channel-assets 의 `Code Animation/nova/README.md`, `Code Animation/CLAUDE.md`, `Code Animation/_channel/shorts_playbook.md` 를 읽고, nova 방식으로 새 지식 쇼츠 5편을 만들자. 화풍·소리·주제는 README 4·5장과 겹치지 않게.

환경: `../_kit/setup.sh`(ffmpeg, pycairo, numpy, opencv, CJK 글꼴). nova는 `../scale/engine.py`와 `../_kit/vfx`를 함께 쓴다.
