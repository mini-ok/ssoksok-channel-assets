"""Transcribe the delivered voice tracks and compare each utterance against its source."""
import os,json,sys,wave,re,difflib
from pathlib import Path
ROOT=Path(__file__).resolve().parent
os.environ.setdefault('HF_HOME',str(ROOT/'models'))
os.environ.setdefault('HF_HUB_DISABLE_SYMLINKS_WARNING','1')
from faster_whisper import WhisperModel
import numpy as np
from scipy.signal import resample_poly

def norm(t):return re.sub(r'[^a-z0-9가-힣]','',t.lower())

def main():
    print('Loading multilingual ASR model...',flush=True)
    model=WhisperModel('base',device='cpu',compute_type='int8',cpu_threads=4)
    result=[]
    for folder in sorted((ROOT/'audio').iterdir()):
        if not folder.is_dir():continue
        lang=folder.name.split('_')[-1]
        for row in json.loads((folder/'manifest.json').read_text(encoding='utf-8')):
            with wave.open(str(folder/(row['id']+'.wav'))) as f:
                sr=f.getframerate();a=np.frombuffer(f.readframes(f.getnframes()),np.int16).astype(np.float32)/32768
            a=resample_poly(a,2,3) if sr==24000 else a
            segments,info=model.transcribe(a,language=lang,beam_size=5,vad_filter=False,condition_on_previous_text=False)
            heard=' '.join(s.text for s in segments).strip()
            score=difflib.SequenceMatcher(None,norm(row['text']),norm(heard)).ratio()
            result.append(dict(variant=folder.name,id=row['id'],expected=row['text'],heard=heard,similarity=round(score,3)))
            print(f'{folder.name}/{row["id"]}: {score:.2f} {heard}',flush=True)
    (ROOT/'output'/'speech_qa.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')

if __name__=='__main__':main()
