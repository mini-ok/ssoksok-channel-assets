# 7편 연어 파프리카 오븐구이 · 한글/영문

사용자 승인(2026-10-31) 대본을 바탕으로 한글·영문 영상 제작과 파일·화면·음성 검수 완료. 건강근거 장면의 영양 수치 박스를 포함한다. 최종 결과는 output/verification.json, output_en/verification.json 및 encoded_speech_qa.json을 확인한다.

- 캐릭터: brain. 쉐프 음성 Orus, 여성 해설 Despina. 기본 1.3배 속도.
- 음악: nimble_motifs.mp3. 직전 편과 다른 곡.
- 건강 근거: plan.json 및 DRAFT_KO.md의 계산식·출처·조건을 따른다.
- 수치 박스는 benefit/context 두 장면으로 나누며 각 장면 최소 9초. 레시피 마지막 10초 고정.
- 실제 주방 조리·맛·냉동 식감 평가는 수행하지 않는다. 실제 유튜브 업로드는 이 제작 과정에서 실행하지 않는다.
- 8편 뼈 캐릭터는 기존 캐릭터 목록에 없어 같은 종이 질감의 새 캐릭터를 제작했다. 7편은 기존 뇌 팀장 디자인과 Orus 목소리를 사용한다.

재생성: 저장소 루트에서 `python cooking-shorts/produce_episodes.py 7 ko audio` → `preview` → `render` → `verify` → `check`. 영문은 ko를 en으로 바꾼다. 묶음은 `python cooking-shorts/package_episodes78.py`.

MP4/WAV는 로컬 폴더와 다운로드 묶음으로 제공하고, 코드·대본·검수자료·정지 이미지만 GitHub에 백업한다. 인증정보는 포함하지 않는다.
