"""Decode every delivered frame and audio packet; inspect motion and measure final audio."""
import json,subprocess,re,wave,math
from pathlib import Path
import av
import numpy as np
from PIL import Image,ImageDraw,ImageFont
import imageio_ffmpeg
ROOT=Path(__file__).resolve().parent
OUT=ROOT/'output';FF=imageio_ffmpeg.get_ffmpeg_exe()

def audio_array(path):
    with wave.open(str(path)) as w:return np.frombuffer(w.readframes(w.getnframes()),np.int16).astype(np.float32)/32768

def main():
    results=[]
    for name in ['heart_ko','heart_en','liver_ko','liver_en']:
        path=OUT/(name+'.mp4');container=av.open(str(path));stream=container.streams.video[0]
        assert (stream.width,stream.height)==(1080,1920)
        assert abs(float(stream.average_rate)-24)<.01
        frames=0;previous=None;motion=[];thumbs=[]
        selected=[2,10,16,23,31,38]
        for frame in container.decode(video=0):
            if frames%24==0:
                thumb=frame.to_image().resize((135,240));a=np.asarray(thumb).astype(np.float32)
                assert a.mean()>25 and a.std()>8,'Blank/black frame detected'
                if previous is not None:motion.append(float(np.abs(a-previous).mean()))
                previous=a
            sec=float(frame.time)
            if selected and sec>=selected[0]:
                thumbs.append(frame.to_image().resize((270,480)));selected.pop(0)
            frames+=1
        duration=frames/24;container.close()
        container=av.open(str(path));samples=0
        for frame in container.decode(audio=0):samples+=frame.samples
        assert samples>24000*30
        container.close()
        # Decode through the FFmpeg player path as a separate end-to-end check.
        decoded=subprocess.run([FF,'-hide_banner','-v','error','-i',str(path),'-f','null','-'],capture_output=True)
        assert decoded.returncode==0 and not decoded.stderr,decoded.stderr.decode(errors='replace')
        measured=subprocess.run([FF,'-hide_banner','-nostats','-i',str(path),'-af',
             'loudnorm=I=-14:TP=-1.5:LRA=8:print_format=json','-f','null','-'],capture_output=True)
        stats=json.loads(re.findall(r'\{[^{}]+\}',measured.stderr.decode())[-1])
        assert -17<float(stats['input_i'])<-12,stats
        assert float(stats['input_tp'])<-.8,stats
        voice=audio_array(OUT/(name+'_voice.wav'));music=audio_array(OUT/(name+'_music.wav'))
        ratios=[]
        for k in range(0,len(voice)-72000,24000):
            v=voice[k:k+72000];m=music[k:k+72000];vr=np.sqrt(np.mean(v*v));mr=np.sqrt(np.mean(m*m))
            if vr>.025:ratios.append(float(20*np.log10(vr/max(mr,1e-8))))
        assert min(ratios)>12,'Music masks voice'
        assert sum(x>.2 for x in motion)>len(motion)*.8,'Too many unchanged samples'
        sheet=Image.new('RGB',(270*3,480*2),'#F3EFE5')
        for i,thumb in enumerate(thumbs):sheet.paste(thumb,((i%3)*270,(i//3)*480))
        sheet.save(OUT/(name+'_encoded_check.jpg'),quality=94)
        row=dict(file=path.name,width=1080,height=1920,fps=24,video_frames=frames,duration_seconds=duration,
                 audio_samples=samples,full_decode='passed',integrated_lufs=float(stats['input_i']),
                 true_peak_dbtp=float(stats['input_tp']),minimum_speech_music_gap_db=round(min(ratios),1),
                 moving_1_second_samples=sum(x>.2 for x in motion),total_1_second_samples=len(motion),
                 size_mb=round(path.stat().st_size/1024/1024,2))
        results.append(row);print(json.dumps(row,ensure_ascii=False),flush=True)
    (OUT/'verification.json').write_text(json.dumps(results,ensure_ascii=False,indent=2),encoding='utf-8')

if __name__=='__main__':main()
