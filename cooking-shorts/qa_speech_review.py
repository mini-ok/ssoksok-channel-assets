"""Second pass for Korean ingredient names and numbers that the small ASR can confuse."""
import os,json,wave,re
from pathlib import Path
import numpy as np
from scipy.signal import resample_poly
ROOT=Path(__file__).resolve().parent
os.environ['HF_HOME']=str(ROOT/'models');os.environ['HF_HUB_DISABLE_SYMLINKS_WARNING']='1'
from faster_whisper import WhisperModel
model=WhisperModel('small',device='cpu',compute_type='int8',cpu_threads=3)
rows=json.loads((ROOT/'output'/'speech_qa.json').read_text(encoding='utf-8'))
for row in rows:
    if row['similarity']>=.95 or not row['variant'].endswith('_ko'):continue
    path=ROOT/'audio'/row['variant']/(row['id']+'.wav')
    with wave.open(str(path)) as w:a=np.frombuffer(w.readframes(w.getnframes()),np.int16).astype(np.float32)/32768
    a=resample_poly(a,2,3)
    segments,_=model.transcribe(a,language='ko',beam_size=5,condition_on_previous_text=False,
                               initial_prompt='요리, 귀리, 오트밀, 병아리콩, 오이, 토마토, 식이섬유, 야근 수당')
    heard=' '.join(s.text for s in segments).strip()
    row['review_heard']=heard;print(row['variant'],row['id'],heard,flush=True)
(ROOT/'output'/'speech_qa_reviewed.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2),encoding='utf-8')
