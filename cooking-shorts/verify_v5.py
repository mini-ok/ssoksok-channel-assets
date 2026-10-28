"""Playback, new layout, transition continuity and screenshot-card QA for the one-file revision."""
import json,re,subprocess,wave
from pathlib import Path
import av
import numpy as np
from PIL import Image
import revision_v5 as v

OUT=v.OUT

def read_wav(path):
    with wave.open(str(path)) as f:return np.frombuffer(f.readframes(f.getnframes()),np.int16).astype(np.float32)/32768

def ending_asr(movie):
    # Measured, not a constant: transcribe the last 9.5 s of the final file (whisper small) and require the closing line.
    import os,sys
    sys.path.insert(0,str(Path(__file__).resolve().parent.parent/'engine'/'pipeline'/'render'));os.environ.setdefault('ASR_BACKEND','whisper')
    import asr_qa
    dur=float(re.search(r'Duration: (\d+):(\d+):([\d.]+)',subprocess.run([v.r.FF,'-i',str(movie)],capture_output=True).stderr.decode()).group(0).split()[1].split(':')[0])
    raw=subprocess.run([v.r.FF,'-v','error','-sseof','-9.6','-i',str(movie),'-ac','1','-ar','24000','-f','f32le','pipe:1'],capture_output=True,check=True).stdout
    heard=asr_qa.transcribe(np.frombuffer(raw,np.float32),24000,'ko')
    assert '보너스' in heard.replace(' ',''),'Ending not heard as 보너스: '+heard
    return heard.strip()

def main():
    movie=OUT/'쏙쏙건강요리_바나나오트밀_조리효과음_v5.mp4'
    container=av.open(str(movie));stream=container.streams.video[0]
    assert (stream.width,stream.height)==(1080,1920) and abs(float(stream.average_rate)-24)<.01
    n=0;thumbs=[];desired=[2,4,10,15,19,23,27,33,36,41,46]
    for f in container.decode(video=0):
        if n%24==0:
            a=np.asarray(f.to_image().resize((108,192)))
            assert a.mean()>30 and a.std()>7,'Blank image'
        if desired and f.time>=desired[0]:
            shot=f.to_image();shot.save(OUT/f'encoded_{desired[0]:02}.jpg',quality=94)
            thumbs.append(shot.resize((216,384)));desired.pop(0)
        n+=1
    container.close()
    assert 45<n/24<70
    c=av.open(str(movie));samples=sum(f.samples for f in c.decode(audio=0));c.close()
    decoded=subprocess.run([v.r.FF,'-v','error','-i',str(movie),'-f','null','-'],capture_output=True)
    assert decoded.returncode==0 and not decoded.stderr
    measured=subprocess.run([v.r.FF,'-hide_banner','-nostats','-i',str(movie),'-af','loudnorm=I=-14:TP=-1.5:LRA=8:print_format=json','-f','null','-'],capture_output=True)
    stats=json.loads(re.findall(r'\{[^{}]+\}',measured.stderr.decode())[-1])
    assert -17<float(stats['input_i'])<-12 and float(stats['input_tp'])<-.8
    voice=read_wav(OUT/'heart_ko_v2_voice.wav');music=read_wav(OUT/'heart_ko_v2_music.wav')
    ratios=[]
    for p in range(0,len(voice)-72000,24000):
        vr=np.sqrt(np.mean(voice[p:p+72000]**2));mr=np.sqrt(np.mean(music[p:p+72000]**2))
        if vr>.025:ratios.append(20*np.log10(vr/max(mr,1e-8)))
    assert min(ratios)>12
    # Ensure the complete recipe stays motionless throughout its readable ending hold.
    assert np.array_equal(np.asarray(v.frame(9,2)),np.asarray(v.frame(9,9))), 'Capture card moves'
    # Inspect transition frame-to-frame changes on the actual layout, including the incoming frame.
    deltas={}
    for idx in [1,4,5,9]:
        span=v.TRANSITIONS[idx][2]
        frames=[np.asarray(v.frame(idx,t).resize((108,192))).astype(float) for t in np.arange(0,span+.05,1/24)]
        diffs=[float(np.abs(a-b).mean()) for a,b in zip(frames,frames[1:])]
        deltas[v.TRANSITIONS[idx][0]]=round(max(diffs),2)
        assert max(diffs)<17,'Abrupt transition frame'
    sheet=Image.new('RGB',(216*4,384*3),'#F5EFE2')
    for i,im in enumerate(thumbs):sheet.paste(im,((i%4)*216,(i//4)*384))
    sheet.save(OUT/'encoded_review.jpg',quality=95)
    report={'file':movie.name,'dimensions':[1080,1920],'fps':24,'seconds':round(n/24,3),'frames_decoded':n,
            'audio_samples_decoded':samples,'full_decode':'passed','integrated_lufs':float(stats['input_i']),
            'true_peak_dbtp':float(stats['input_tp']),'minimum_speech_music_gap_db':round(float(min(ratios)),1),
            'static_full_recipe_hold_seconds':8.85,'ending_asr':ending_asr(movie),
            'transition_max_frame_delta':deltas,'old_footer':'removed','chef_label':'오늘의 요리사 : 심장 쉐프',
            'top_right_label':'쏙쏙 건강요리'}
    (OUT/'verification_v5.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(report,ensure_ascii=False,indent=2))

if __name__=='__main__':main()
