"""Shared production template; mushroom draft superseded by produce_toast.py."""
import os,sys,json,math,wave,subprocess,functools,re,difflib,hashlib
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parent;SOURCE=ROOT.parent;REPO=SOURCE.parent
sys.path.insert(0,str(SOURCE))
import revision_liver as v
r=v.r;OUT=ROOT/'output';AUDIO=ROOT/'audio'
OUT.mkdir(exist_ok=True);AUDIO.mkdir(exist_ok=True)
TARGET=OUT/'쏙쏙건강요리_버섯달걀볶음_한글_v1.mp4'
CARD_FILE='버섯달걀볶음_전체레시피.png'
SRT_FILE='버섯달걀볶음_한글.srt'
RECIPE_NOTE='Superseded draft: no specific organ benefit. Do not publish.'
ROWS=[
 ('hook','팬 하나로 맛있게!','오늘은 버섯이랑 달걀! 팬 하나면 충분해요.','심장 쉐프','신나고 자신 있게.'),
 ('ingredients','주재료는 딱 두 가지','양송이 백 그램, 달걀 두 개. 식용유는 한 작은술이에요.','여성 내레이터','밝고 또랑또랑하게.'),
 ('chop','01  버섯 썰고 달걀 풀기','버섯은 손질해 얇게 썰고, 달걀은 미리 풀어둬요.','여성 내레이터','명랑하고 리듬감 있게.'),
 ('fry','02  버섯부터 볶아요','기름 두른 팬에 버섯부터! 중불로 볶아 물기를 날려요.','심장 쉐프','신나게 요리하며.'),
 ('pour','03  중약불로 낮춰요','이제 중약불! 푼 달걀을 붓고, 가장자리부터 익혀요.','심장 쉐프','경쾌하게 안내하듯.'),
 ('mix','04  살살 모아가며 익혀요','주걱으로 가장자리에서 가운데로! 살살 접어야 폭신해져요.','심장 쉐프','즐겁게 집중하며.'),
 ('done','흐르는 달걀 없이!','흐르는 달걀이 없도록 완전히 익혀요. 간은 취향껏 조금만요.','여성 내레이터','친절하고 또렷하게.'),
 ('benefit','채소와 달걀을 한 팬에','채소와 달걀을 함께 먹는 간단한 방법! 통곡물 빵을 곁들여도 좋아요.','여성 내레이터','상큼하고 다정하게.'),
 ('joke','설거지는 누가 하죠?','팬 하나라 설거지도 간단하죠? 아, 제 담당이었어요?','심장 쉐프','뿌듯하다가 끝에 코믹하게 놀라며.'),
 ('end','캡처해서 다음 끼니에!','구독은 사원증 발급! 좋아요는 보너스!','심장 쉐프','신나게 웃으며.')]
def rows():return json.loads((AUDIO/'manifest.json').read_text(encoding='utf-8'))
v.manifest=rows;v.OUT=OUT;v.AUDIO=AUDIO
v.SPEAKER={'심장 쉐프':('심장 쉐프',0xF0A0A8),'여성 내레이터':('해설',0x9ACDB4)}
v.KEYWORDS={'ingredients':{'백','두','한'},'fry':{'중불로','물기를'},'pour':{'중약불!'},'mix':{'가운데로!','살살'},'done':{'완전히'},'joke':{'제','담당이었어요?'}}
SOURCE_URL='https://www.canada.ca/en/health-canada/services/food-guide/eating-support/kitchen/recipes/egg-veggie-scramble.html'

def auth():
 from google.oauth2 import service_account
 from google.auth.transport.requests import Request
 creds=service_account.Credentials.from_service_account_file(str(next((REPO.parent/'tts').glob('*.json'))),scopes=['https://www.googleapis.com/auth/cloud-platform'])
 def token():
  if not creds.valid:creds.refresh(Request())
  return creds.token
 v.channel_tts.token=token

def speech_normalize(s):
 s=s.lower().replace('100g','백그램').replace('100 g','백그램').replace('100그램','백그램').replace('2개','두개').replace('2 개','두개').replace('1 작은술','한작은술').replace('1작은술','한작은술').replace('1 작은 술','한작은술')
 s=s.replace('100%','백퍼센트').replace('100 %','백퍼센트').replace('20g','이십그램').replace('20 g','이십그램').replace('20그램','이십그램').replace('20 그램','이십그램').replace('1장','한장').replace('1 장','한장').replace('1/2개','반개').replace('1/2 개','반개')
 return re.sub('[^가-힣a-z0-9]','',s)

VOICE_BY_SPEAKER={'심장 쉐프':'Zubenelgenubi','여성 내레이터':'Despina'}
SPEECH_ACCEPT=lambda sid,heard:True

def audio():
 auth();os.environ['HF_HOME']=str(REPO.parent/'cooking_shorts_sample/models')
 from faster_whisper import WhisperModel
 from scipy.signal import resample_poly
 model=WhisperModel('small',device='cpu',compute_type='int8',cpu_threads=3)
 report=[];manifest=[]
 cached={x['id']:x for x in rows()} if (AUDIO/'manifest.json').exists() else {}
 for sid,title,text,speaker,act in ROWS:
  path=AUDIO/(sid+'.wav');voice=VOICE_BY_SPEAKER.get(speaker,'Zubenelgenubi')
  cached_take=cached.get(sid,{})
  needs_take=not path.exists() or cached_take.get('text')!=text or cached_take.get('voice',voice)!=voice
  for attempt in range(3):
   if needs_take or attempt:
    prompt=('밝고 명랑한 요리 애니메이션. '+act) if attempt==0 else ''
    x=v.gsynth(text,voice,prompt);x=v.speech.speed(v.speech.tts.squeeze_gaps(v.speech.tts.trim_edges(x)),1.3)
    v.speech.tts.save_wav(str(path),x)
   with wave.open(str(path)) as f:x=np.frombuffer(f.readframes(f.getnframes()),np.int16).astype(np.float32)/32768
   seg,_=model.transcribe(resample_poly(x,2,3),language='ko',beam_size=5,condition_on_previous_text=False)
   heard=' '.join(s.text for s in seg).strip()
   norm=speech_normalize
   score=difflib.SequenceMatcher(None,norm(text),norm(heard)).ratio()
   print(sid,round(score,3),heard,flush=True)
   if score>.87 and (sid!='end' or '보너스' in heard) and SPEECH_ACCEPT(sid,heard):break
   if attempt==2:raise RuntimeError('Speech QA failed: '+sid)
  report.append(dict(id=sid,heard=heard,expected=text,similarity=round(score,3)))
  manifest.append(dict(id=sid,title=title,text=text,speaker=speaker,voice=voice,speed=1.3,speech_duration=len(x)/24000,duration=10.0 if sid=='end' else round(max(3.4,len(x)/24000+1.4),3)))
 (AUDIO/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
 (OUT/'speech_qa.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')

@functools.lru_cache(None)
def mushroom():
 im=Image.new('RGBA',(220,210));d=ImageDraw.Draw(im)
 d.rounded_rectangle((88,90,136,186),13,fill='#E6D5BC')
 d.pieslice((22,20,198,160),180,360,fill='#B4967A');d.ellipse((34,75,186,120),fill='#CBB49B')
 d.line((48,106,174,106),fill='#99816B',width=5)
 return r.paperize(im,61)

@functools.lru_cache(None)
def egg():
 im=Image.new('RGBA',(190,230));d=ImageDraw.Draw(im)
 d.ellipse((25,15,165,213),fill='#EBD8B9');d.ellipse((38,28,146,197),fill='#F8EBD6')
 return r.paperize(im,62)

@functools.lru_cache(maxsize=96)
def pan(stage,phase=0):
 im=Image.new('RGBA',(900,650));d=ImageDraw.Draw(im)
 d.rounded_rectangle((680,280,895,335),22,fill='#A77C59')
 d.ellipse((75,140,805,555),fill='#687B7D');d.ellipse((95,153,785,520),fill='#34474A')
 if stage=='pour':d.ellipse((170,215,710,475),fill='#F6D673')
 if stage in ('mix','done'):
  for i in range(42):
   a=i*2.399+phase*.035;rr=math.sqrt(i/42);x=440+rr*272*math.cos(a);y=330+rr*120*math.sin(a)
   d.rounded_rectangle((x-36,y-20,x+37,y+20),16,fill=['#F5D877','#FFE69C','#E9BF59'][i%3])
 for i in range(12):
  a=i*2.399+phase*.035;x=440+235*math.cos(a);y=325+95*math.sin(a)
  r.place(im,mushroom(),x,y,.45,angle=20*math.sin(a))
 return r.paperize(im,51)

def spatula(im,t):
 x=550+45*math.sin(t*3);y=1220+20*math.cos(t*3)
 d=ImageDraw.Draw(im)
 # Connect the chef's outstretched hand to the tool grip, with the head over the food.
 grip=(x+45,y-95)
 arm=[(346,1192),(450,1240),(grip[0],grip[1])]
 d.line(arm,fill='#374969',width=22,joint='curve')
 d.line(arm,fill='#EDABA5',width=15,joint='curve')
 d.line((x+60,y-125,x,y),fill='#BB916C',width=24)
 d.rounded_rectangle((x-43,y-25,x+43,y+48),20,fill='#D8AF7F')
 for k in [-18,0,18]:d.line((x+k,y-8,x+k,y+31),fill='#B58B62',width=5)
 d.ellipse((grip[0]-17,grip[1]-17,grip[0]+17,grip[1]+17),fill='#EDABA5',outline='#374969',width=3)

def recipe(im):
 r.rounded(im,(72,285,1008,1510),'#FFFCF3',45,11)
 entries=[('버섯 달걀볶음',390,76),('1인 곁들임 / 약 10분',490,44),('재료',610,54),
 ('양송이버섯 100g · 달걀 2개',700,51),('식용유 1작은술',780,48),('소금·후추 약간 (선택)',860,48),('만드는 법',980,54),
 ('1  버섯은 얇게 썰고 달걀은 풀어요.',1070,46),('2  기름 두른 팬에 버섯부터 볶아요.',1160,46),
 ('3  중약불로 낮추고 달걀을 넣어요.',1250,46),('4  살살 접으며 흐르는 달걀 없이 익혀요.',1340,43)]
 for text,y,size in entries:r.label(im,text,(540,y),size,fill='#638B77' if text in ('재료','만드는 법') else v.INK,maxw=850)

@functools.lru_cache(None)
def chip(text,size,color):return v.sty.paper_chip(text,size,color)

def header(im,end):
 r.place(im,chip('쏙쏙 건강백과',38,0xFFF9EA),235,108)
 r.place(im,chip('쏙쏙 건강요리',44,0xE2F3EC),815,108)
 r.place(im,chip('오늘의 요리사 : 심장 쉐프',48,0xF0DBA0),540,222)
 if not end:r.place(im,v.sty.paper_chip('버섯 달걀볶음',80,0x5BB8AA,-2),540,365)

def content(idx,t):
 sid=ROWS[idx][0];im=Image.new('RGBA',(1080,1920));d=ImageDraw.Draw(im)
 if sid=='end':recipe(im);return im
 if sid=='ingredients':
  r.rounded(im,(95,710,985,1185),'#FFFCF3',42,9)
  for j,(name,amount,sp) in enumerate([('양송이버섯','100g',mushroom()),('달걀','2개',egg()),('식용유','1작은술',r.prop('oil'))]):
   y=800+j*135;r.place(im,sp,190,y,.55 if j<2 else .26)
   r.label(im,name,(300,y),60,anchor='lm');r.label(im,amount,(925,y),57,anchor='rm',fill='#638B77')
  r.place(im,r.chef('heart','sparkle'),260,1350,.5)
 elif sid=='chop':
  r.place(im,r.chef('heart','serious'),220,1075,.62)
  r.rounded(im,(410,1055,1020,1330),'#D6B184',35,8)
  for j in range(5):r.place(im,mushroom(),520+j*85,1180,.42,angle=8*j)
  r.place(im,r.prop('knife'),710,1040+26*math.cos(t*10),.58,angle=-8)
  r.rounded(im,(580,1360,965,1450),'#FFFCF3',25,5)
  r.label(im,'달걀은 미리 풀어두기',(770,1405),37)
 elif sid=='benefit':
  r.label(im,'버섯의 식감 + 달걀의 든든함',(540,785),54,fill='#638B77')
  r.rounded(im,(100,900,980,1110),'#FFFCF3',35,9)
  r.label(im,'조리 참고 · 캐나다 보건부',(540,965),53)
  r.label(im,'채소 달걀볶음 레시피',(540,1048),54,fill='#638B77')
  r.place(im,r.chef('heart','proud'),230,1320,.58);r.place(im,pan('done'),735,1340,.65)
 else:
  mood='sparkle' if sid in ('hook','done') else 'shock' if sid=='joke' and t>1.8 else 'happy'
  r.place(im,r.chef('heart',mood),235,1120,.74,angle=math.sin(t*2)*1.5)
  stage='fry' if sid=='fry' else 'pour' if sid=='pour' and t<2.7 else 'mix' if sid=='mix' else 'done'
  phase=round((math.sin(t*3)+1)*7) if sid in ('mix','fry') else 0
  r.place(im,pan(stage,phase),690,1255,.88)
  if sid in ('fry','mix'):spatula(im,t)
  if sid=='fry':
   for j in range(3):
    y=1020-((t*.5+j/3)%1)*170;d.arc((570+j*85,y,610+j*85,y+90),80,260,fill=(255,255,255,150),width=6)
  if sid=='pour':
   r.rounded(im,(700,800,930,910),'#FFF7DD',30,5)
   if .7<t<2.5:d.line((805,910,730,1180),fill='#F6D673',width=25)
  if sid in ('hook','done'):v.sparkles(im,t,[(510,930,25),(930,1080,22)])
  if sid=='joke' and t>1.8:v.sweat(im,390,1010,t);v.bang(im,440,880,t)
 return im

@functools.lru_cache(None)
def previous(idx):return content(idx,rows()[idx]['duration']-.01)

def frame(idx,t):
 end=ROWS[idx][0]=='end';im=v.background().copy();new=content(idx,t)
 if idx and t<.85:
  old=v.background().copy();old.alpha_composite(previous(idx-1))
  flat=v.background().copy();flat.alpha_composite(new);u=v.smooth(t/.85)
  if idx in (3,5,9):flat=v.zoom_layer(flat,.98+.02*u)
  im=Image.blend(old,flat,u)
 else:im.alpha_composite(new)
 header(im,end)
 if end:
  r.label(im,'구독은 사원증 발급!',(540,1630),59);r.label(im,'좋아요는 보너스!',(540,1725),67,fill='#638B77')
 else:
  h=Image.new('RGBA',(1080,1920));r.place(h,chip(ROWS[idx][1],62,0x9DC7DE),540,565)
  if idx and t<.85:h.putalpha(h.getchannel('A').point(lambda a:round(a*v.smooth(t/.85))))
  im.alpha_composite(h);im.alpha_composite(v.wrapped_caption(idx))
 return im.convert('RGB')

def mix():
 path=v.prepare_mix(rows());sr=24000
 with wave.open(str(path)) as f:a=np.frombuffer(f.readframes(f.getnframes()),np.int16).astype(np.float32)/32768
 from scipy.signal import butter,sosfilt
 rng=np.random.default_rng(303);clock=0
 for row in rows():
  if row['id'] in ('fry','pour','mix'):
   count=int((row['duration']-.6)*sr);t=np.arange(count)/sr
   fx=sosfilt(butter(2,[700,4500],btype='bandpass',fs=sr,output='sos'),rng.normal(0,1,count))
   fx*=np.sin(np.pi*np.arange(count)/count)**.5
   fx*=.009/max(np.sqrt(np.mean(fx*fx)),.001)
   at=int((clock+.3)*sr);a[at:at+count]+=fx
  clock+=row['duration']
 r.wavwrite(path,a);return path

def preview():
 sheet=Image.new('RGB',(1080,768))
 for i in range(len(ROWS)):
  image=frame(i,2.1);image.save(OUT/f'scene_{i:02}.png');sheet.paste(image.resize((216,384)),((i%5)*216,(i//5)*384))
 sheet.save(OUT/'storyboard.jpg',quality=95)
 frame(9,3).save(OUT/CARD_FILE)

def render():
 manifest=rows();duration=sum(x['duration'] for x in manifest);audio=mix()
 cmd=[r.FF,'-y','-v','error','-f','rawvideo','-pix_fmt','rgb24','-s','1080x1920','-r','24','-i','pipe:0','-i',str(audio),'-c:v','libx264','-preset','fast','-threads','4','-crf','19','-pix_fmt','yuv420p','-af','loudnorm=I=-14:TP=-1.5:LRA=8,alimiter=limit=0.5:attack=1:release=50:level=disabled','-c:a','aac','-b:a','192k','-t',str(duration),'-movflags','+faststart',str(TARGET)]
 with (OUT/'encode.log').open('wb') as log:
  p=subprocess.Popen(cmd,stdin=subprocess.PIPE,stderr=log);idx=0;start=0
  try:
   for n in range(math.ceil(duration*24)):
    t=n/24
    while idx<len(manifest)-1 and t>=start+manifest[idx]['duration']:start+=manifest[idx]['duration'];idx+=1
    p.stdin.write(frame(idx,t-start).tobytes())
    if n%120==0:print(f'Render {t:.0f}/{duration:.1f}s',flush=True)
  finally:p.stdin.close()
  assert p.wait()==0
 print('FINISHED',TARGET,flush=True)

def verify():
 import av
 import shutil
 c=av.open(str(TARGET));s=c.streams.video[0];assert(s.width,s.height)==(1080,1920)
 duration=sum(x['duration'] for x in rows());times=[sum(x['duration'] for x in rows()[:i])+2 for i in range(10)]
 sheet=Image.new('RGB',(1080,768));n=0;i=0
 for f in c.decode(video=0):
  if i<len(times) and f.time>=times[i]:
   im=f.to_image();im.save(OUT/f'encoded_{i:02}.jpg',quality=95);sheet.paste(im.resize((216,384)),((i%5)*216,(i//5)*384));i+=1
  n+=1
 c.close();assert abs(n/24-duration)<.1
 p=subprocess.run([r.FF,'-v','error','-i',str(TARGET),'-f','null','-'],capture_output=True);assert p.returncode==0 and not p.stderr
 p=subprocess.run([r.FF,'-hide_banner','-nostats','-i',str(TARGET),'-af','loudnorm=I=-14:TP=-1.5:LRA=8:print_format=json','-f','null','-'],capture_output=True)
 stats=json.loads(re.findall(r'\{[^{}]+\}',p.stderr.decode())[-1]);assert float(stats['input_tp'])<-.8
 assert np.array_equal(np.asarray(frame(9,2)),np.asarray(frame(9,9)))
 sheet.save(OUT/'encoded_review.jpg',quality=95)
 report=dict(file=TARGET.name,seconds=n/24,frames_decoded=n,resolution=[1080,1920],fps=24,full_decode='passed',integrated_lufs=float(stats['input_i']),true_peak=float(stats['input_tp']),static_recipe_card='passed',speech_qa='passed',sha256=hashlib.sha256(TARGET.read_bytes()).hexdigest(),evidence_reference=SOURCE_URL,recipe_note=RECIPE_NOTE)
 (OUT/'verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps(report,ensure_ascii=False),flush=True)
 shutil.copy2(OUT/'liver_ko.srt',OUT/SRT_FILE)
 shutil.copy2(TARGET,REPO.parent/TARGET.name)

if __name__=='__main__':raise SystemExit('Superseded mushroom draft. Use episode03/produce_toast.py for the final episode.')
