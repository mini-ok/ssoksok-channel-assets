# -*- coding: utf-8 -*-
"""〈숨비〉 대사 4줄을 Gemini Flash TTS(Google Cloud Text-to-Speech)로 녹음합니다. 내 컴퓨터에서 실행하세요.
준비:  pip install requests google-auth
실행:  python sumbi_voices_gemini.py  서비스계정키.json
결과:  sumbi_voices/ 폴더에 줄마다 3테이크씩 wav (예: mom1_take1.wav). 폴더를 압축하거나 wav를 그대로 첨부해 주세요."""
import base64, json, os, sys, time, wave
import requests
from google.oauth2 import service_account
import google.auth.transport.requests as tr

KEY = sys.argv[1] if len(sys.argv) > 1 else 'key.json'
MODEL = 'gemini-2.5-flash-tts'
URLS = ['https://us-texttospeech.googleapis.com/v1/text:synthesize', 'https://texttospeech.googleapis.com/v1/text:synthesize']
SR = 24000
info = json.load(open(KEY, encoding='utf-8'))
cred = service_account.Credentials.from_service_account_info(info, scopes=['https://www.googleapis.com/auth/cloud-platform'])
cred.refresh(tr.Request())

# (파일명, 대사, 음성, 연기 지시) — 한 줄당 음성 후보를 바꿔 3테이크
LINES = [
  ('mom1', '솔아, 물 떠 오라이.', ['Sulafat', 'Kore', 'Gacrux'],
   '제주 해녀인 삼십대 엄마. 새벽 불턱에서 바다에 들기 직전, 아홉 살 딸에게 심부름을 시킨다. 다정하지만 담담하고 짧게, 제주 사투리 억양. "솔아," 뒤에 살짝 쉬고 "물 떠 오라이"는 부드럽게 끝을 올린다.'),
  ('sol1', '꾸럭아, 조금만 참아.', ['Leda', 'Achernar', 'Zephyr'],
   '아홉 살 여자아이. 물허벅 속 아기 문어에게 속삭이듯 말한다. 겁이 나지만 단단하게, 숨이 조금 찬 상태. "꾸럭아," 뒤에 쉬고 "조금만 참아"는 작고 다정하게.'),
  ('sol2', '엄마…', ['Leda', 'Achernar', 'Zephyr'],
   '아홉 살 여자아이가 물속에서 엄마를 알아보고 터지듯 부르는 한마디. 놀라움과 안도가 섞인, 숨 섞인 작은 목소리. 끝을 길게 흐린다.'),
  ('mom2', '숨, 같이 쉬자.', ['Sulafat', 'Kore', 'Gacrux'],
   '해녀 엄마가 딸을 안고 막 물 위로 올라와 숨을 고르며 하는 말. 낮고 따뜻하게, 미소가 묻어나게. "숨," 뒤에 한 박자 쉬고 "같이 쉬자"는 천천히.'),
]
os.makedirs('sumbi_voices', exist_ok=True)
for name, text, voices, prompt in LINES:
    for k, voice in enumerate(voices, 1):
        body = {'input': {'text': text, 'prompt': prompt}, 'voice': {'languageCode': 'ko-KR', 'name': voice, 'modelName': MODEL},
                'audioConfig': {'audioEncoding': 'LINEAR16', 'sampleRateHertz': SR}}
        hd = {'Authorization': 'Bearer ' + cred.token, 'x-goog-user-project': info['project_id'], 'Content-Type': 'application/json'}
        for url in URLS:
            r = requests.post(url, headers=hd, json=body, timeout=60)
            if r.ok: break
        if not r.ok:
            print('실패', name, voice, r.status_code, r.text[:300]); continue
        pcm = base64.b64decode(r.json()['audioContent'])
        if pcm[:4] == b'RIFF': pcm = pcm[44:]
        out = f'sumbi_voices/{name}_take{k}.wav'
        with wave.open(out, 'wb') as w:
            w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes(pcm)
        print('저장', out, voice); time.sleep(0.5)
print('완료 — sumbi_voices 폴더의 wav를 첨부해 주세요.')
