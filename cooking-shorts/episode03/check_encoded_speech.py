"""Transcribe each scene from the actual final MP4, including music and cooking SFX."""
import os,re,json,difflib,subprocess
import numpy as np
import produce as p
os.environ['HF_HOME']=str(p.REPO.parent/'cooking_shorts_sample/models')
from faster_whisper import WhisperModel
model=WhisperModel('small',device='cpu',compute_type='int8',cpu_threads=3)
raw=subprocess.run([p.r.FF,'-v','error','-i',str(p.TARGET),'-vn','-ac','1','-ar','16000','-f','f32le','pipe:1'],capture_output=True,check=True).stdout
audio=np.frombuffer(raw,np.float32);clock=0;report=[]
def norm(s):
 s=s.lower().replace('100g','백그램').replace('100 g','백그램').replace('100그램','백그램').replace('2개','두개').replace('2 개','두개').replace('1 작은술','한작은술').replace('1작은술','한작은술').replace('1 작은 술','한작은술')
 return re.sub('[^가-힣a-z0-9]','',s)
for row in p.rows():
 segment=audio[int(clock*16000):int((clock+row['duration'])*16000)]
 parts,_=model.transcribe(segment,language='ko',beam_size=5,condition_on_previous_text=False)
 heard=' '.join(x.text for x in parts).strip();score=difflib.SequenceMatcher(None,norm(row['text']),norm(heard)).ratio()
 print(row['id'],round(score,3),heard,flush=True)
 report.append(dict(id=row['id'],expected=row['text'],heard=heard,similarity=score))
 assert score>.85, row['id']+' final speech not clear enough'
 clock+=row['duration']
(p.OUT/'encoded_speech_qa.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
