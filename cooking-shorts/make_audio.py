import os, sys, json, wave, subprocess, time
from pathlib import Path
import numpy as np
import imageio_ffmpeg

ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'runtime'))
import channel_tts as tts
from episodes import EPISODES
from google.oauth2 import service_account
from google.auth.transport.requests import Request

FF=imageio_ffmpeg.get_ffmpeg_exe()
_creds=None
def token():
    global _creds
    if _creds is None:
        import google.auth
        _creds, _ = google.auth.default(scopes=['https://www.googleapis.com/auth/cloud-platform'])
    if not _creds.valid: _creds.refresh(Request())
    return _creds.token
tts.token=token

def speed(x,rate):
    # Preserve pitch while matching the channel's usual brisk delivery.
    raw=(np.clip(x,-1,1)*32767).astype(np.int16).tobytes()
    result=subprocess.run([FF,'-hide_banner','-loglevel','error','-f','s16le','-ar','24000','-ac','1','-i','pipe:0',
        '-af',f'atempo={rate}','-f','s16le','pipe:1'],input=raw,capture_output=True,check=True)
    return np.frombuffer(result.stdout,np.int16).astype(np.float32)/32768

def make():
    for topic,ep in EPISODES.items():
      for li,lang in enumerate(['ko','en']):
        folder=ROOT/'audio'/f'{topic}_{lang}'; folder.mkdir(exist_ok=True)
        manifest=[]
        for sid,mindur,mood,texts,titles in ep['scenes']:
            path=folder/f'{sid}.wav'
            text=texts[li]
            if not path.exists():
                started=time.time(); print(f'Synthesizing {topic}/{lang}/{sid}',flush=True)
                expected=len(text.replace(' ',''))/6.0 if lang=='ko' else len(text.split())/2.8
                takes=[]
                for attempt in range(3):
                    x=tts.squeeze_gaps(tts.trim_edges(tts.synth(text,ep['sid'],'ko-KR' if lang=='ko' else 'en-US',mode='none')))
                    takes.append(x)
                    if 0.55*expected<len(x)/24000<1.9*expected+0.7: break
                x=min(takes,key=lambda a:abs(len(a)/24000-expected))
                x=speed(x,1.22)
                tts.save_wav(str(path),x)
                print(f'  {len(x)/24000:.2f}s / took {time.time()-started:.0f}s',flush=True)
            with wave.open(str(path)) as w: duration=w.getnframes()/w.getframerate()
            manifest.append({'id':sid,'text':text,'title':titles[li],'mood':mood,'speech_duration':duration,
                             'duration':round(max(mindur,duration+0.55),3)})
        (folder/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
        print(f'{topic}_{lang} total {sum(x["duration"] for x in manifest):.1f}s',flush=True)
    (ROOT/'audio'/'usage.json').write_text(json.dumps({'synthesized_characters_this_run':tts.CHARS,'model':tts.MODEL,
            'voices':{'heart':'Puck','liver':'Charon'}},indent=2),encoding='utf-8')

if __name__=='__main__':
    make()
