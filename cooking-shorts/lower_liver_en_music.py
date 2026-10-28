"""Audio-only correction after QA; preserves the verified encoded video frames."""
from pathlib import Path
import wave,subprocess,os
import numpy as np
import imageio_ffmpeg
ROOT=Path(__file__).resolve().parent;OUT=ROOT/'output';name='liver_en'
def load(p):
    with wave.open(str(p)) as w:return np.frombuffer(w.readframes(w.getnframes()),np.int16).astype(np.float32)/32768
def save(p,x):
    with wave.open(str(p),'wb') as w:
        w.setnchannels(1);w.setsampwidth(2);w.setframerate(24000);w.writeframes((np.clip(x,-1,1)*32767).astype(np.int16).tobytes())
music=load(OUT/(name+'_music.wav'));mix=load(OUT/(name+'_mix.wav'))
save(OUT/(name+'_mix.wav'),mix-.3*music);save(OUT/(name+'_music.wav'),music*.7)
target=OUT/(name+'.mp4');temp=OUT/(name+'_audio_fixed.mp4')
subprocess.run([imageio_ffmpeg.get_ffmpeg_exe(),'-y','-hide_banner','-loglevel','error','-i',str(target),'-i',str(OUT/(name+'_mix.wav')),
    '-map','0:v:0','-map','1:a:0','-c:v','copy','-af','loudnorm=I=-14:TP=-1.5:LRA=8','-c:a','aac','-b:a','192k',
    '-shortest','-movflags','+faststart',str(temp)],check=True)
os.replace(temp,target)
print('Liver English music lowered by 3.1 dB; video copied without re-encoding.')
