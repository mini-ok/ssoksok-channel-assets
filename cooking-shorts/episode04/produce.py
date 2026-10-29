"""Episode 04: approved gut-chef broccoli garlic stir-fry, Korean."""
import sys,json,math,functools,inspect,importlib.util,hashlib,wave,subprocess,os,re
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT.parent));sys.path.insert(0,str(ROOT.parent/'episode03'))
spec=importlib.util.spec_from_file_location('cooking_production_base',ROOT.parent/'episode03/produce.py')
p=importlib.util.module_from_spec(spec);spec.loader.exec_module(p)
r=p.r;v=p.v;p.ROOT=ROOT;p.OUT=ROOT/'output';p.AUDIO=ROOT/'audio'
p.OUT.mkdir(exist_ok=True);p.AUDIO.mkdir(exist_ok=True)
p.TARGET=p.OUT/'쏙쏙건강요리_브로콜리마늘볶음_한글_v1.mp4'
p.CARD_FILE='브로콜리마늘볶음_전체레시피.png';p.SRT_FILE='브로콜리마늘볶음_한글.srt'
p.RECIPE_NOTE='Fiber and hydration support bowel habits; not a claim that this dish treats constipation. No kitchen or taste test.'
p.SOURCE_URL='https://www.niddk.nih.gov/health-information/digestive-diseases/constipation/eating-diet-nutrition'
v.OUT=p.OUT;v.AUDIO=p.AUDIO;v.manifest=p.rows
p.VOICE_BY_SPEAKER={'장 쉐프':'Aoede','여성 내레이터':'Despina'}
p.ROWS=[
 ('hook','장이 고른 초록 반찬','오늘은 장을 위한 초록 반찬! 브로콜리, 제가 볶아볼게요!','장 쉐프','발랄하고 신나게.'),
 ('ingredients','해외에서도 쉬운 재료','브로콜리 백오십 그램, 마늘 한 쪽, 식용유 한 작은술. 물은 두 큰술이에요.','여성 내레이터','밝고 또랑또랑하게.'),
 ('chop','01  줄기도 얇게 썰어요','씻어서 한입 크기로! 줄기도 얇게 썰면 같이 먹을 수 있어요.','장 쉐프','즐겁게 설명하며.'),
 ('steam','02  물 넣고 뚜껑 덮기','팬에 브로콜리와 물을 넣고, 뚜껑을 덮어 중불로 삼 분쯤 익혀요.','여성 내레이터','상큼하고 리듬감 있게.'),
 ('fry','03  중약불로 마늘과 볶기','물기를 날리고 중약불! 기름이랑 다진 마늘을 넣어 일 분쯤 볶아요.','장 쉐프','신나게 집중하며.'),
 ('serve','줄기가 익으면 완성!','줄기가 먹기 좋게 익으면 완성! 간은 취향껏 조금만요.','장 쉐프','뿌듯하고 경쾌하게.'),
 ('benefit','왜 장 쉐프가 골랐을까요?','브로콜리는 식이섬유를 보태줘요. 식이섬유와 충분한 수분은 변을 부드럽게 하고, 배변을 돕는 데 좋아요.','여성 내레이터','명랑하고 친절하게 설명하듯.'),
 ('habit','조금씩 꾸준히 · 물도 함께','한 번에 듬뿍보다 조금씩 꾸준히! 물도 함께 챙기는 게 장 쉐프의 포인트예요.','여성 내레이터','다정하고 발랄하게.'),
 ('joke','물컵도 챙겨주세요!','제 반찬만 챙기지 말고, 물컵도 챙겨주세요. 저도 목말라요!','장 쉐프','장난스럽고 귀엽게 투정하듯.'),
 ('end','캡처해서 다음 반찬으로!','구독은 사원증 발급! 좋아요는 보너스!','장 쉐프','신나게 웃으며.')]
v.SPEAKER={'장 쉐프':('장 쉐프',0xA3D9C3),'여성 내레이터':('해설',0x9ACDB4)}
v.KEYWORDS={'ingredients':{'백오십','두'},'chop':{'줄기도'},'steam':{'중불로','삼'},'fry':{'중약불!','일'},'benefit':{'식이섬유와','수분은','배변을'},'habit':{'조금씩','물도'},'joke':{'물컵도'}}
normalize=p.speech_normalize
def norm(s):
 s=s.replace('150g','백오십그램').replace('150 g','백오십그램').replace('150그램','백오십그램').replace('150 그램','백오십그램').replace('1쪽','한쪽').replace('한 조각','한쪽').replace('2큰술','두큰술').replace('2 큰술','두큰술').replace('3분','삼분').replace('3 분','삼분').replace('1분','일분').replace('1 분','일분')
 return normalize(s)
p.speech_normalize=norm
p.SPEECH_ACCEPT=lambda sid,heard:bool(re.search(r'(3|삼)\s*분',heard)) if sid=='steam' else bool(re.search(r'(1|일)\s*분',heard)) if sid=='fry' else True
PLAN=json.loads((ROOT/'plan.json').read_text(encoding='utf-8'))

# Preserve the original gut identity, goggles and antenna; exchange the lab flask for cooking tools.
chef_src=inspect.getsource(r.chef_fn).replace("    if name=='heart':", "    if name=='gut':\n        start=src.index('    fl = ')\n        stop=src.index('    cv.restore()',start)\n        src=src[:start]+src[stop:]\n    if name=='heart':")
exec(chef_src,r.__dict__)
exec(inspect.getsource(r.chef.__wrapped__).replace('chef_v3_','chef_ep04_v1_'),r.__dict__)
# Change only this episode's selected music; do not overwrite any shared audio asset.
exec(inspect.getsource(v.prepare_mix).replace("'buant_pop_groove.mp3'","'buoyant_kitchen_groove.mp3'"),v.__dict__)

def preflight():
 ids=[x[0] for x in p.ROWS]
 assert PLAN['organ']=='장' and PLAN['chef']=='장 쉐프' and all(PLAN['review'].values())
 assert max(ids.index(s) for s in PLAN['cooking_scene_ids'])<min(ids.index(s) for s in PLAN['health_narration_scene_ids'])
 assert all(p.ROWS[ids.index(s)][3]=='여성 내레이터' for s in PLAN['health_narration_scene_ids'])
 music=p.REPO/'bgm'/PLAN['music']['file'];old=p.REPO/'bgm'/PLAN['music']['previous_episode_file']
 assert music.is_file() and hashlib.sha256(music.read_bytes()).digest()!=hashlib.sha256(old.read_bytes()).digest()
 print('Gut/recipe/health narration and different-music preflight passed',flush=True)

@functools.lru_cache(None)
def broccoli():
 im=Image.new('RGBA',(240,250));d=ImageDraw.Draw(im)
 d.polygon([(87,228),(150,228),(140,133),(189,100),(175,83),(125,127),(72,88),(55,108),(100,150)],fill='#91B977')
 for x,y,rad in [(62,83,41),(106,56,48),(157,67,48),(183,105,38),(123,106,51),(74,119,33)]:
  d.ellipse((x-rad,y-rad,x+rad,y+rad),fill='#6F9F6B')
  d.arc((x-rad+8,y-rad+7,x+rad-10,y+rad-8),190,300,fill='#91B77C',width=6)
 return r.paperize(im,94)

@functools.lru_cache(None)
def garlic():
 im=Image.new('RGBA',(160,180));d=ImageDraw.Draw(im)
 d.pieslice((20,5,147,165),60,285,fill='#E3D2AD');d.pieslice((31,12,140,157),65,280,fill='#FFF0D2')
 return r.paperize(im,95)

@functools.lru_cache(None)
def glass():
 im=Image.new('RGBA',(190,250));d=ImageDraw.Draw(im)
 d.polygon([(29,35),(161,35),(146,224),(44,224)],fill='#D4E8E8',outline='#A6C4C5',width=6)
 d.polygon([(39,101),(153,101),(140,215),(49,215)],fill='#9ACCD8');d.line((58,55,67,165),fill='#F0FAF8',width=9)
 return r.paperize(im,96)

@functools.lru_cache(maxsize=40)
def pan(phase=0,water=False,garlicky=True):
 im=Image.new('RGBA',(900,650));d=ImageDraw.Draw(im)
 d.rounded_rectangle((675,285,895,345),22,fill='#A77C59')
 d.ellipse((75,135,805,555),fill='#687B7D');d.ellipse((95,150,785,520),fill='#34474A')
 if water:d.ellipse((160,205,730,465),fill='#7FA1A3')
 for i in range(9):
  a=i*2.399+phase*.035;rr=.48 if i<3 else .84;x=440+rr*290*math.cos(a);y=330+rr*135*math.sin(a)
  r.place(im,broccoli(),x,y,.62,angle=15*math.sin(a))
 if garlicky:
  for i in range(12):
   a=i*2.399;x=440+240*math.cos(a);y=330+105*math.sin(a)
   d.rounded_rectangle((x-8,y-5,x+8,y+6),4,fill='#F2D8A8')
 return r.paperize(im,97)

@functools.lru_cache(None)
def lid():
 im=Image.new('RGBA',(900,650));d=ImageDraw.Draw(im)
 d.ellipse((80,140,800,530),fill=(209,231,225,210),outline='#B0CBC7',width=13)
 d.arc((105,163,773,495),190,300,fill='#F1F8EE',width=10)
 d.rounded_rectangle((375,280,505,335),23,fill='#B49778')
 return im

def spatula(im,t):
 x=600+65*math.sin(t*2.8);y=1240+23*math.cos(t*2.8);d=ImageDraw.Draw(im)
 grip=(x+45,y-110);arm=[(345,1190),(450,1250),grip]
 d.line(arm,fill='#374969',width=22,joint='curve');d.line(arm,fill='#A3DCC4',width=15,joint='curve')
 d.line((x+57,y-142,x,y),fill='#BD9974',width=23)
 d.rounded_rectangle((x-39,y-20,x+39,y+48),19,fill='#D7B58B')
 for a in [-17,0,17]:d.line((x+a,y-3,x+a,y+28),fill='#AD8761',width=5)
 d.ellipse((grip[0]-16,grip[1]-16,grip[0]+16,grip[1]+16),fill='#A3DCC4',outline='#374969',width=3)

def recipe(im):
 r.rounded(im,(72,285,1008,1510),'#FFFCF3',45,11)
 entries=[('브로콜리 마늘볶음',385,72),('1인 곁들임 / 약 7분',480,44),('재료',585,54),
 ('브로콜리 150g · 마늘 1쪽',660,50),('식용유 1작은술 · 물 2큰술',735,49),('소금·후추는 선택',805,43),('만드는 법',910,54),
 ('1  작은 송이로 나누고 줄기는 얇게 썰어요.',1000,43),('2  물 넣고 뚜껑 덮어 중불로 약 3분.',1080,44),
 ('3  물기를 날리고 중약불로 낮춰요.',1160,45),('4  기름·다진 마늘 넣고 약 1분 볶아요.',1240,43),
 ('줄기가 단단하면 조금 더 익혀요.',1345,42),('냉동 제품은 포장 가열 안내를 따라요.',1415,39)]
 for text,y,size in entries:r.label(im,text,(540,y),size,fill='#638B77' if text in ['재료','만드는 법'] or y>1300 else v.INK,maxw=855)
p.recipe=recipe

def header(im,end):
 r.place(im,p.chip('쏙쏙 건강백과',38,0xFFF9EA),235,108);r.place(im,p.chip('쏙쏙 건강요리',44,0xE2F3EC),815,108)
 r.place(im,p.chip('오늘의 요리사 : 장 쉐프',48,0xF0DBA0),540,222)
 if not end:r.place(im,v.sty.paper_chip('브로콜리 마늘볶음',75,0x5BB8AA,-2),540,365)
p.header=header

def source_card(im):
 r.rounded(im,(95,910,985,1115),'#FFFCF3',35,9)
 r.label(im,'출처 · 미국 NIH / NIDDK',(540,974),52)
 r.label(im,'식이섬유·수분과 배변 안내',(540,1056),50,fill='#638B77')

def content(idx,t):
 sid=p.ROWS[idx][0];im=Image.new('RGBA',(1080,1920));d=ImageDraw.Draw(im)
 if sid=='end':recipe(im);return im
 if sid=='ingredients':
  r.rounded(im,(95,690,985,1235),'#FFFCF3',42,9)
  for j,(name,amount,sp,scale) in enumerate([('브로콜리','150g',broccoli(),.4),('마늘','1쪽',garlic(),.47),('식용유','1작은술',r.prop('oil'),.2),('물','2큰술',glass(),.36)]):
   y=770+j*119;r.place(im,sp,180,y,scale);r.label(im,name,(285,y),57,anchor='lm');r.label(im,amount,(925,y),56,anchor='rm',fill='#638B77')
  r.label(im,'생 / 냉동 브로콜리 모두 가능',(540,1315),43,fill='#638B77');r.place(im,r.chef('gut','sparkle'),240,1415,.42)
 elif sid=='chop':
  r.place(im,r.chef('gut','serious'),220,1100,.66);r.rounded(im,(410,1040,1020,1360),'#D6B184',35,8)
  for i in range(3):r.place(im,broccoli(),535+i*155,1180,.52,angle=i*12-10)
  for i in range(4):d.rounded_rectangle((550+i*55,1300,583+i*55,1316),6,fill='#A9C68D')
  r.place(im,r.prop('knife'),720,1030+25*math.cos(t*10),.6,angle=-8)
 elif sid in ('benefit','habit'):
  r.label(im,'식이섬유 + 충분한 수분' if sid=='benefit' else '조금씩 늘리고 · 물도 함께',(540,755),57,fill='#638B77')
  r.label(im,'원활한 배변을 돕는 습관' if sid=='benefit' else '한 번에 듬뿍보다 꾸준히',(540,844),52)
  source_card(im);r.place(im,r.chef('gut','proud'),220,1350,.56);r.place(im,pan(),715,1340,.57);r.place(im,glass(),910,1260,.55)
 else:
  mood='shock' if sid=='joke' and t>1.8 else 'serious' if sid=='fry' else 'sparkle'
  r.place(im,r.chef('gut',mood),235,1120,.74,angle=math.sin(t*2)*1.5)
  if sid in ('steam','fry'):
   r.rounded(im,(395,1370,1015,1460),'#D7D8CC',28,7);d.ellipse((650,1400,693,1438),fill='#7CA49A')
  phase=round((math.sin(t*2.8)+1)*7) if sid=='fry' else 0
  r.place(im,pan(phase,sid=='steam',sid!='steam'),690,1225,.84)
  if sid=='steam':
   u=v.smooth((t-.35)/1.0);r.place(im,lid(),690,1005+220*u,.84,opacity=min(1,u+.4))
   for j in range(3):
    y=1050-((t*.35+j/3)%1)*160;d.arc((590+j*70,y,625+j*70,y+85),80,260,fill=(250,255,250,150),width=6)
   r.label(im,'중불 / 약 3분',(735,830),49,fill='#638B77')
  if sid=='fry':spatula(im,t);r.label(im,'중약불 / 마늘 타지 않게',(650,830),43,fill='#638B77')
  if sid=='serve':
   x=760+12*math.sin(t*2);y=1160+12*math.cos(t*3)
   d.line((x+60,y-140,x,y),fill='#B3C8C9',width=18)
   for dx in [-18,-6,6,18]:d.line((x+dx,y,x+dx-8,y+45),fill='#B3C8C9',width=7)
   r.label(im,'줄기가 단단하면 조금 더',(610,850),45,fill='#638B77')
  if sid=='joke':
   r.place(im,glass(),450-45*v.smooth(t/2),1285,.65)
   if t>1.8:v.sweat(im,390,1010,t)
  if sid=='hook':r.place(im,broccoli(),790,870,.6,angle=math.sin(t*2)*7);v.sparkles(im,t,[(500,930,24),(925,1020,22)])
 return im
p.content=content

def mix():
 path=v.prepare_mix(p.rows());sr=24000
 with wave.open(str(path)) as f:a=np.frombuffer(f.readframes(f.getnframes()),np.int16).astype(np.float32)/32768
 from scipy.signal import butter,sosfilt
 rng=np.random.default_rng(404);clock=0
 for row in p.rows():
  if row['id'] in ('steam','fry'):
   n=int((row['duration']-.7)*sr);tt=np.arange(n)/sr
   fx=sosfilt(butter(2,[700,4300],btype='bandpass',fs=sr,output='sos'),rng.normal(0,1,n))*np.sin(np.pi*tt/(n/sr))**.5
   fx*=.009/max(np.sqrt(np.mean(fx*fx)),.001);pos=int((clock+.3)*sr);a[pos:pos+n]+=fx
   if row['id']=='steam':
    tt=np.arange(int(.1*sr))/sr;clink=np.sin(2*np.pi*740*tt)*np.exp(-tt*60)*.05;pos=int((clock+1.35)*sr);a[pos:pos+len(clink)]+=clink
  clock+=row['duration']
 r.wavwrite(path,a);return path
p.mix=mix

def verify():
 p.verify()
 def pcm(path):
  raw=subprocess.run([r.FF,'-v','error','-i',str(path),'-t','25','-ac','1','-ar','8000','-f','f32le','pipe:1'],capture_output=True,check=True).stdout
  return np.frombuffer(raw,np.float32).astype(np.float64)
 selected=p.REPO/'bgm'/PLAN['music']['file'];previous=p.REPO/'bgm'/PLAN['music']['previous_episode_file']
 stem=pcm(p.OUT/'liver_ko_music.wav');new=pcm(selected);old=pcm(previous)
 n=min(len(stem),len(new),len(old));stem,new,old=stem[:n],new[:n],old[:n]
 similarity=lambda a,b:float(np.dot(a,b)/(np.linalg.norm(a)*np.linalg.norm(b)))
 new_score=similarity(stem,new);old_score=similarity(stem,old)
 assert new_score>.6 and new_score>abs(old_score)*2
 path=p.OUT/'verification.json';report=json.loads(path.read_text(encoding='utf-8'))
 report.update(music=PLAN['music']['file'],previous_episode_music=PLAN['music']['previous_episode_file'],selected_music_stem_correlation=round(new_score,4),previous_music_stem_correlation=round(old_score,4),different_music_verified='passed',chef_voice='Aoede',narrator_voice='Despina')
 path.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
 print('Actual music stem matches selected track, differs from episode 03:',round(new_score,3),round(old_score,3),flush=True)

def check():
 os.environ['HF_HOME']=str(p.REPO.parent/'cooking_shorts_sample/models')
 from faster_whisper import WhisperModel
 model=WhisperModel('small',device='cpu',compute_type='int8',cpu_threads=3)
 raw=subprocess.run([r.FF,'-v','error','-i',str(p.TARGET),'-vn','-ar','16000','-ac','1','-f','f32le','pipe:1'],capture_output=True,check=True).stdout
 samples=np.frombuffer(raw,np.float32);clock=0;report=[]
 for row in p.rows():
  seg,_=model.transcribe(samples[int(clock*16000):int((clock+row['duration'])*16000)],language='ko',beam_size=5,condition_on_previous_text=False)
  heard=' '.join(s.text for s in seg).strip();score=p.difflib.SequenceMatcher(None,norm(row['text']),norm(heard)).ratio()
  print(row['id'],round(score,3),heard,flush=True);assert score>.85
  report.append(dict(id=row['id'],expected=row['text'],heard=heard,similarity=score));clock+=row['duration']
 (p.OUT/'encoded_speech_qa.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')

if __name__=='__main__':
 preflight()
 if sys.argv[1]=='check':check()
 elif sys.argv[1]=='verify':verify()
 elif sys.argv[1]=='preflight':pass
 else:getattr(p,sys.argv[1])()
