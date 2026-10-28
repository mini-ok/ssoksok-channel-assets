"""Update only the dialogue speed; retain the already rendered visual pacing and capture hold."""
import subprocess,os
import revision_v2 as v
mix=v.prepare_mix(v.manifest())
target=v.OUT/'쏙쏙건강요리_바나나오트밀_전환비교_v2.mp4'
temp=v.OUT/'v2_130_audio_update.mp4'
subprocess.run([v.r.FF,'-y','-v','error','-i',str(target),'-i',str(mix),'-map','0:v:0','-map','1:a:0',
                '-c:v','copy','-af','loudnorm=I=-14:TP=-1.5:LRA=8','-c:a','aac','-b:a','192k',
                '-t',str(sum(s['duration'] for s in v.manifest())),'-movflags','+faststart',str(temp)],check=True)
os.replace(temp,target)
print('Dialogue set to 1.30x. Visual timing and recipe hold retained.')
