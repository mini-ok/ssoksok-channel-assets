# 9편 렌틸콩 양파 수프 · 한글/영문

2026-11-02 사용자가 한글·영문 영상과 업로드 묶음까지 제작하도록 지시했다. 한글·영문 제작과 파일·화면·음성 검수를 완료했다. 상세 검수 결과는 output/verification.json, output_en/verification.json, 각 encoded_speech_qa.json을 확인한다.

- 요리사: 장 쉐프 / Chef Gut. 음성 Aoede, 여성 해설 Despina. 1.3배 속도.
- 9편은 기존 장 캐릭터에서 실험 플라스크만 제거. 10편은 동일한 종이 질감·외곽선·앞치마의 새 눈 쉐프.
- 건강 설명은 조리 뒤 여성 해설. 영양 수치 박스 2화면 각각 최소 9초, 마지막 전체 레시피 10초 고정.
- 수치 범위: 각 그릇에 든 렌틸콩만 계산, 다른 재료의 식이섬유는 미포함. 전체 요리 영양성분이나 개인별 치료 효과의 실측값이 아니다.
- 계산: 7.8 g per 1/2 cup cooked lentils; full recipe 2 x 7.8 = 15.6 g; 7.8 / 28 x 100 = 27.86%
- 일일 비교: 미국 FDA 영양표시 DV 28g/일(2,000kcal 기준), 개인별 권장량과 구분.
- 음악 nimble_motifs.mp3; 직전 편 buoyant_kitchen_groove.mp3와 다름.

재생성: 저장소 루트에서 `python cooking-shorts/produce_episodes.py 9 ko audio`, `preview`, `render`, `verify`, `check`. 영문은 ko를 en으로 바꾼다. 네 편 검수가 끝난 뒤 `python cooking-shorts/package_episodes910.py`로 묶는다.

수치의 근거·조건·단위·URL은 plan.json, nutrition_verification.json, DRAFT_KO.md와 DRAFT_EN.md에 기록했다. 미국 계량컵(약 240mL) 기준을 화면에 표시한다. 통조림·다른 제품·생시금치로 바꾸면 영양 수치는 다시 계산한다.

실제 주방 조리·맛 평가는 수행하지 않았다. 유튜브 업로드나 다른 AI로의 메시지 전송은 이 제작 과정에서 실행하지 않는다. 기존 인증이 있는 클라우드에 전달할 업로드 묶음으로 제공한다. 인증정보는 포함하지 않는다.

MP4/WAV는 로컬 업로드 폴더에 제공하며, 코드·대본·검수자료·정지 이미지·자막만 GitHub에 백업한다.

최종 음성 검수에서 오프닝의 재료 이름이 덜 또렷해져, 뜻을 유지한 ‘따뜻한 수프 나갑니다! 콩으로 식이섬유를 챙겨볼게요!’로 정리했다. 재료·레시피·건강 근거와 수치는 유지했다.
