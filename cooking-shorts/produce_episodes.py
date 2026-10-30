"""Bilingual production for approved episodes 05/06; shared paper renderer and channel voices."""
import sys,os,json,math,re,wave,subprocess,inspect,importlib.util,functools,difflib,hashlib
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw
SOURCE=Path(__file__).resolve().parent
NUM=int(sys.argv[1]);LANG=sys.argv[2];COMMAND=sys.argv[3];ROOT=SOURCE/f'episode{NUM:02}'
C=json.loads((ROOT/'production.json').read_text(encoding='utf-8'));PLAN=json.loads((ROOT/'plan.json').read_text(encoding='utf-8'))
sys.path.insert(0,str(SOURCE))
spec=importlib.util.spec_from_file_location('episode_template',SOURCE/'episode03/produce.py');p=importlib.util.module_from_spec(spec);spec.loader.exec_module(p)
r=p.r;v=p.v;p.ROOT=ROOT;p.OUT=ROOT/('output' if LANG=='ko' else 'output_en');p.AUDIO=ROOT/('audio' if LANG=='ko' else 'audio_en')
p.OUT.mkdir(exist_ok=True);p.AUDIO.mkdir(exist_ok=True);v.OUT=p.OUT;v.AUDIO=p.AUDIO;v.manifest=p.rows
chef=C['chef_'+LANG];narrator='여성 내레이터' if LANG=='ko' else 'Narrator'
L=lambda ko,en:ko if LANG=='ko' else en
p.TARGET=p.OUT/(f"쏙쏙건강요리_{C['dish_ko'].replace(' ','')}_한글_v1.mp4" if LANG=='ko' else f"TinyBodyCo_{C['slug']}_EN.mp4")
p.CARD_FILE=f"{C['slug']}_recipe_{LANG.upper()}.png";p.SRT_FILE=f"{C['slug']}_{LANG.upper()}.srt"
p.SOURCE_URL=PLAN['evidence'][0]['url'];p.RECIPE_NOTE=PLAN['evidence'][0]['conditions_and_limits']+' No real kitchen or taste test.'
p.ROWS=[(x['id'],x['title_'+LANG],x['text_'+LANG],narrator if x['narrator'] else chef,'') for x in C['scenes']]
color=0xF3B897 if NUM==5 else 0xC5D0F0
v.SPEAKER={chef:(chef,color),narrator:(L('해설','Narrator'),0x9ACDB4)}
origfont=r.font
if LANG=='en':
 r.font=lambda size,style='jua':origfont(size,'en' if style in ('jua','en') else 'heavy')
 r.p.FONTS.update(jua=str(SOURCE/'runtime/fonts/Geist-Bold.ttf'),black=str(SOURCE/'runtime/fonts/Geist-Black.ttf'))
label=r.label
def fitted(im,text,xy,size=50,fill=v.INK,style='jua',anchor='mm',maxw=None):
 if LANG=='en':text={'구독은 사원증 발급!':'Subscribe for your employee badge!','좋아요는 보너스!':'Likes are your bonus!'}.get(text,text)
 return label(im,text,xy,size,fill,style,anchor,maxw or (900 if anchor=='mm' else 630))
r.label=fitted
paper=v.sty.paper_chip
@functools.lru_cache(maxsize=128)
def chip(text,size,color,angle=0):
 limit=470 if text in ['쏙쏙 건강백과','쏙쏙 건강요리','Tiny Body Co.','Healthy Cooking'] else 965
 while r.p.tw(text,size,'black')+130>limit and size>20:size-=1
 return paper(text,size,color,angle)
v.sty.paper_chip=chip;p.chip=chip

# Remove work tools while preserving each character's identity accessories.
src=inspect.getsource(r.chef_fn)
src=src.replace("    if name=='heart':", "    if name=='muscle':\n        start=src.index('    rrect(cv, 196')\n        stop=src.index('    body = ',start)\n        src=src[:start]+src[stop:]\n    if name=='immune':\n        start=src.index('    rrect(cv, 160')\n        stop=src.index('    cv.restore()',start)\n        src=src[:start]+src[stop:]\n    if name=='heart':")
exec(src,r.__dict__);exec(inspect.getsource(r.chef.__wrapped__).replace('chef_v3_',f'chef_ep{NUM:02}_v1_'),r.__dict__)
exec(inspect.getsource(v.prepare_mix).replace("'buant_pop_groove.mp3'",repr(C['music'])),v.__dict__)

def preflight():
 ids=[x[0] for x in p.ROWS]
 assert NUM in (5,6) and LANG in ('ko','en') and all(PLAN['review'].values())
 assert max(ids.index(x) for x in PLAN['cooking_scene_ids'])<min(ids.index(x) for x in PLAN['health_narration_scene_ids'])
 assert all(p.ROWS[ids.index(x)][3]==narrator for x in PLAN['health_narration_scene_ids'])
 a=p.REPO/'bgm'/C['music'];b=p.REPO/'bgm'/C['previous_music']
 assert a.is_file() and hashlib.sha256(a.read_bytes()).digest()!=hashlib.sha256(b.read_bytes()).digest()

def norm(s):
 s=s.lower()
 if LANG=='en':
  for n,w in [('150','one hundred fifty'),('100','one hundred'),('80','eighty'),('50','fifty'),('12','twelve'),('4','four'),('3','three'),('2','two'),('1','one')]:s=re.sub(r'\b'+n+r'\b',w,s)
  return re.sub('[^a-z0-9]','',s.replace('one hundred and fifty','one hundred fifty'))
 for n,w in [('150','백오십'),('100','백'),('80','팔십'),('50','오십'),('12','십이')]:s=s.replace(n,w)
 s=s.replace('그램','g').replace('밀리리터','ml').replace('비타민 a','비타민에이').replace('비타민a','비타민에이')
 for n,w in [('2개','두개'),('2 개','두개'),('1큰술','한큰술'),('1 큰술','한큰술')]:s=s.replace(n,w)
 return re.sub('[^가-힣a-z0-9]','',s)

def audio():
 p.auth();os.environ['HF_HOME']=str(p.REPO.parent/'cooking_shorts_sample/models')
 from faster_whisper import WhisperModel
 from scipy.signal import resample_poly
 import requests
 model=WhisperModel('small',device='cpu',compute_type='int8',cpu_threads=3)
 cached={x['id']:x for x in p.rows()} if (p.AUDIO/'manifest.json').exists() else {};reports=[];rows=[]
 for sid,title,text,speaker,_ in p.ROWS:
  path=p.AUDIO/(sid+'.wav');voice='Despina' if speaker==narrator else C['voice'];take=cached.get(sid,{})
  for attempt in range(4):
   if not path.exists() or take.get('text')!=text or take.get('voice',voice)!=voice or attempt:
    inp={'text':text}
    if not attempt:inp['prompt']=L('밝고 신나는 요리 애니메이션. 또렷하고 경쾌하게.','Bright, lively cooking animation. Cheerful and clear, with playful energy.')
    response=requests.post(v.channel_tts.G_URL,headers={'Authorization':'Bearer '+v.channel_tts.token(),'x-goog-user-project':v.channel_tts.PROJECT},json={'input':inp,'voice':{'languageCode':'ko-KR' if LANG=='ko' else 'en-US','name':voice,'modelName':v.channel_tts.MODEL},'audioConfig':{'audioEncoding':'LINEAR16','sampleRateHertz':24000}},timeout=120)
    if response.status_code!=200:raise RuntimeError('TTS HTTP '+str(response.status_code))
    x=v.channel_tts.squeeze_gaps(v.channel_tts.trim_edges(v.channel_tts.decode(response)));v.speech.tts.save_wav(str(path),v.speech.speed(x,1.3))
   with wave.open(str(path)) as f:x=np.frombuffer(f.readframes(f.getnframes()),np.int16).astype(np.float32)/32768
   seg,_=model.transcribe(resample_poly(x,2,3),language=LANG,beam_size=5,condition_on_previous_text=False)
   heard=' '.join(y.text for y in seg).strip();score=difflib.SequenceMatcher(None,norm(text),norm(heard)).ratio()
   print(NUM,LANG,sid,round(score,3),heard,flush=True)
   if score>.86 and (LANG!='ko' or sid!='end' or '보너스' in heard):break
   if attempt==3:raise RuntimeError('Speech QA failed: '+sid)
  reports.append(dict(id=sid,expected=text,heard=heard,similarity=score));rows.append(dict(id=sid,title=title,text=text,speaker=speaker,voice=voice,speed=1.3,speech_duration=len(x)/24000,duration=10 if sid=='end' else round(max(3.8,len(x)/24000+1.4),3)))
 (p.AUDIO/'manifest.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2),encoding='utf-8');(p.OUT/'speech_qa.json').write_text(json.dumps(reports,ensure_ascii=False,indent=2),encoding='utf-8')

@functools.lru_cache(None)
def asset(kind):
 im=Image.new('RGBA',(240,240));d=ImageDraw.Draw(im)
 if kind=='potato':
  d.ellipse((25,45,218,198),fill='#CEAE78');d.ellipse((40,55,207,181),fill='#E2C695')
  for x,y in [(70,90),(145,80),(177,144),(98,153)]:d.arc((x,y,x+12,y+9),0,180,fill='#AB8756',width=3)
 elif kind=='tuna':
  d.rounded_rectangle((27,60,213,194),20,fill='#B5C9C5');d.rectangle((31,100,209,162),fill='#E8C896');d.ellipse((27,35,213,93),fill='#D6DECC')
  for i in range(12):
   x=53+(i*43)%135;y=49+(i*13)%25;d.ellipse((x,y,x+33,y+11),fill='#D4A18A')
 elif kind=='carrot':
  d.polygon([(49,75),(191,75),(111,223)],fill='#DF965F');d.polygon([(60,83),(164,83),(112,209)],fill='#F3B072')
  for dx in [-20,0,20]:d.line((120,80,120+dx,20),fill='#8EAD75',width=14)
  for y in [108,143,174]:d.line((89,y,130,y-4),fill='#D48B54',width=5)
 elif kind=='egg':d.ellipse((48,15,191,222),fill='#EDDDC2');d.ellipse((60,28,175,205),fill='#FFF1D6')
 elif kind=='flour':
  d.rounded_rectangle((36,34,204,212),18,fill='#E5D0A9');d.rounded_rectangle((49,80,190,169),12,fill='#FFF7E7');r.label(im,L('밀가루','Flour'),(120,125),33,maxw=135)
 elif kind=='water':
  d.polygon([(44,34),(197,34),(176,217),(63,217)],fill='#D6E9E7',outline='#A7C8C9',width=5);d.polygon([(55,104),(185,104),(171,207),(68,207)],fill='#9ECCD7')
 elif kind=='oil':return r.prop('oil')
 return r.paperize(im,NUM*31+len(kind))

@functools.lru_cache(maxsize=32)
def pancake(golden=True):
 im=Image.new('RGBA',(220,160));d=ImageDraw.Draw(im);d.ellipse((8,15,213,145),fill='#C19758' if golden else '#D4C3A0');d.ellipse((15,14,206,130),fill='#E2BC76' if golden else '#EEE1BC')
 for j in range(18):
  x=35+(j*39)%146;y=30+(j*23)%80;d.line((x,y,x+22,y+4),fill='#B98E57' if j%3==0 and golden else '#F3D797',width=5)
 for x,y in [(70,60),(125,45),(140,90),(66,95)]:d.ellipse((x,y,x+21,y+7),fill='#C98F78')
 return r.paperize(im,145)

@functools.lru_cache(maxsize=32)
def food(mode='done',phase=0):
 im=Image.new('RGBA',(900,650));d=ImageDraw.Draw(im)
 if NUM==5 and mode!='mix':
  d.rounded_rectangle((680,285,895,340),23,fill='#A98765');d.ellipse((75,135,805,555),fill='#6B7F80');d.ellipse((95,150,785,520),fill='#35494B')
  for j,(x,y) in enumerate([(290,260),(570,260),(300,415),(580,415)]):
   if mode=='cook' and j==1:continue
   r.place(im,pancake(mode!='raw'),x,y,1.05,angle=7*j-8)
 elif NUM==5:
  d.pieslice((95,130,805,600),0,180,fill='#A6C7BE');d.ellipse((85,140,815,480),fill='#FFF6DF');d.ellipse((122,170,778,447),fill='#D9C69F')
  for j in range(50):
   x=180+(j*77)%535;y=210+(j*43)%200;d.line((x,y,x+30,y-8),fill='#EDD69E',width=10)
  for j in range(15):
   x=220+(j*89)%430;y=230+(j*37)%150;d.ellipse((x,y,x+25,y+10),fill='#D3A18A')
 else:
  if mode=='cook':
   d.rounded_rectangle((80,240,825,590),65,fill='#AAC3BF');d.ellipse((75,130,830,445),fill='#587977');d.ellipse((100,145,805,420),fill='#C8D8D0')
  d.pieslice((175,180,725,590),0,180,fill='#C3D7D4');d.ellipse((165,175,735,480),fill='#FFF8E9');d.ellipse((197,202,703,452),fill='#EEDB9C')
  if mode=='mix' and phase<4:
   for x in [350,520]:d.ellipse((x-55,265,x+55,355),fill='#E9B94F')
  for j in range(55):
   a=j*2.399;rr=math.sqrt(j/55);x=450+rr*230*math.cos(a);y=326+rr*100*math.sin(a);d.rounded_rectangle((x-6,y-4,x+7,y+5),2,fill='#DA9563')
  if mode=='done':d.arc((236,235,650,428),20,150,fill='#D7C086',width=6)
 return r.paperize(im,NUM*37+7)

def arm_tool(im,x,y,kind='spoon'):
 d=ImageDraw.Draw(im);grip=(x+40,y-110);arm=[(345,1190),(450,1250),grip];skin='#F6BA97' if NUM==5 else '#F3F5FF'
 d.line(arm,fill='#374969',width=22,joint='curve');d.line(arm,fill=skin,width=15,joint='curve');d.line((x+53,y-140,x,y),fill='#B89674',width=23)
 if kind=='spoon':d.ellipse((x-35,y-16,x+35,y+70),fill='#D6B58D')
 else:
  d.rounded_rectangle((x-46,y-18,x+46,y+47),16,fill='#D6B58D')
  for a in [-20,0,20]:d.line((x+a,y-2,x+a,y+30),fill='#AA8560',width=5)
 d.ellipse((grip[0]-16,grip[1]-16,grip[0]+16,grip[1]+16),fill=skin,outline='#374969',width=3)

def recipe(im):
 r.rounded(im,(72,285,1008,1510),'#FFFCF3',45,11);r.label(im,C['dish_'+LANG],(540,385),70,maxw=855);r.label(im,C['time_'+LANG],(540,480),44,maxw=855)
 r.label(im,L('재료','Ingredients'),(540,585),53,fill='#638B77')
 lines=C['recipe_'+LANG]
 for i in range(2):r.label(im,lines[i],(540,675+i*85),46,maxw=850)
 r.label(im,L('만드는 법','Method'),(540,905),53,fill='#638B77')
 for i,text in enumerate(lines[2:6]):r.label(im,text,(540,1000+i*87),45,maxw=850)
 r.label(im,lines[6],(540,1400),40,fill='#638B77',maxw=850)
p.recipe=recipe
def header(im,end):
 r.place(im,chip(L('쏙쏙 건강백과','Tiny Body Co.'),38,0xFFF9EA),235,108);r.place(im,chip(L('쏙쏙 건강요리','Healthy Cooking'),44,0xE2F3EC),815,108)
 r.place(im,chip(L('오늘의 요리사 : ',"Today's cook: ")+chef,48,0xF0DBA0),540,222)
 if not end:r.place(im,chip(C['dish_'+LANG],76,0x5BB8AA,-2),540,365)
p.header=header

@functools.lru_cache(maxsize=16)
def caption(idx):
 text=p.rows()[idx]['text'];im=Image.new('RGBA',(1080,1920));d=ImageDraw.Draw(im);words=text.split();chosen=None
 for size in range(64,35,-2):
  f=r.font(size)
  for count in [2,3]:
   if count==3 and size>48:continue
   for i in range(1,len(words)):
    candidates=[(words[:i],words[i:])] if count==2 else [(words[:i],words[i:j],words[j:]) for j in range(i+1,len(words))]
    best=[]
    for parts in candidates:
     widths=[d.textlength(' '.join(part),font=f) for part in parts]
     if max(widths)<=900:best.append((max(widths)-min(widths),parts))
    if best:
     result=min(best,key=lambda x:x[0]);chosen=(size,result[1]);break
   if chosen:break
  if chosen:break
 assert chosen is not None
 size,parts=chosen;r.place(im,v.caption_paper(),540,1650)
 speaker=p.rows()[idx]['speaker'];tag=chef if speaker==chef else L('해설','Narrator');r.place(im,chip(tag,44,color if speaker==chef else 0x9ACDB4),250,1522)
 for i,part in enumerate(parts):
  text=' '.join(part);y=1663+(i-(len(parts)-1)/2)*(63 if len(parts)==3 else 86);r.label(im,text,(540,y),size,maxw=900)
 return im
v.wrapped_caption=caption

def source_card(im):
 r.rounded(im,(95,910,985,1115),'#FFFCF3',35,9);r.label(im,L('출처 · 미국 NIH / ODS','Source: NIH / ODS'),(540,973),55,maxw=855);r.label(im,C['source_'+LANG],(540,1056),48,fill='#638B77',maxw=850)

def content(idx,t):
 sid=p.ROWS[idx][0];im=Image.new('RGBA',(1080,1920));d=ImageDraw.Draw(im)
 if sid=='end':recipe(im);return im
 mood='shock' if sid=='joke' and t>1.8 else 'serious' if sid in ('prep','cook') else 'sparkle'
 if sid=='ingredients':
  r.rounded(im,(95,700,985,1235),'#FFFCF3',42,9)
  for j,(ko,en,amtko,amten,kind) in enumerate(C['ingredients']):
   y=790+j*118;sp=asset(kind);r.place(im,sp,180,y,.35 if kind!='oil' else .18);r.label(im,L(ko,en),(285,y),54,anchor='lm',maxw=450);r.label(im,L(amtko,amten),(925,y),50,anchor='rm',fill='#638B77',maxw=245)
  r.place(im,r.chef(C['character'],'sparkle'),230,1385,.48)
 elif sid=='prep':
  r.place(im,r.chef(C['character'],'serious'),220,1100,.66);r.rounded(im,(410,1045,1020,1370),'#D6B184',35,8)
  if NUM==5:r.place(im,asset('potato'),540,1170,.68)
  else:
   d.rounded_rectangle((675,950,865,1270),20,fill='#B9CBCB',outline='#849DA2',width=6)
   d.rounded_rectangle((724,912,816,963),15,outline='#849DA2',width=13)
   for xx in range(705,850,37):
    for yy in range(990,1250,40):d.ellipse((xx,yy,xx+17,yy+9),fill='#7F999B')
   r.place(im,asset('carrot'),730,1010+46*math.sin(t*8),.58,angle=55)
  for j in range(12):
   x=690+(j*43)%250;y=1160+(j*17)%155;d.line((x,y,x+35,y-6),fill='#E9D197' if NUM==5 else '#DA9664',width=6 if NUM==5 else 4)
  if NUM==5:r.place(im,r.prop('knife'),720,1030+24*math.cos(t*10),.6,angle=-8)
 elif sid in ('benefit','context'):
  lines=([L('단백질 → 아미노산','Protein → Amino Acids'),L('근육 유지·보수에 필요한 재료','Materials for Muscle Maintenance')] if NUM==5 else [L('베타카로틴 → 비타민 A','Beta-Carotene → Vitamin A'),L('면역 체계의 정상적인 기능','Normal Immune Function')]) if sid=='benefit' else ([L('운동 + 충분한 식사 + 단백질','Exercise + Enough Food + Protein'),L('한 접시로 근육이 뿅 생기진 않아요','One Plate Is Not a Magic Muscle Builder')] if NUM==5 else [L('필요한 영양을 다양한 음식으로','Get Nutrients from Varied Foods'),L('많이 먹는다고 무적이 되진 않아요','More Does Not Make You Invincible')])
  for text,y in zip(lines,[755,844]):r.label(im,text.replace('→',L('에서','to')),(540,y),55 if y==755 else 49,fill='#638B77' if y==755 else v.INK,maxw=900)
  source_card(im);r.place(im,r.chef(C['character'],'proud'),225,1350,.56);r.place(im,food(),745,1330,.61)
 else:
  r.place(im,r.chef(C['character'],mood),235,1120,.74,angle=math.sin(t*2)*1.5)
  if sid=='mix':
   r.place(im,food('mix',min(8,int(t*3))),690,1225,.84);arm_tool(im,660+65*math.sin(t*3),1230+20*math.cos(t*3))
  elif sid=='cook':
   r.rounded(im,(395,1370,1015,1460),'#D7D8CC',28,7);r.place(im,food('cook'),690,1225,.84)
   if NUM==5:
    u=(t%2.4)/2.4;lift=math.sin(math.pi*u)*110;sp=pancake(u>.5);sp=sp.resize((220,max(9,int(160*abs(math.cos(math.pi*u))))))
    r.place(im,sp,775,1180-lift,1.0);arm_tool(im,745,1230-lift,'spatula');r.label(im,L('앞뒤 약 3~4분씩 / 속까지 익혀요','About 3–4 min per side / cook through'),(620,830),45,maxw=900)
   else:
    d.ellipse((470,1118,910,1330),fill='#F2F2E5',outline='#C8D8CF',width=8)
    u=v.smooth((t-.3)/.9);lay=Image.new('RGBA',(800,420));dl=ImageDraw.Draw(lay);dl.ellipse((10,20,790,400),fill=(210,230,225,220),outline='#B5CFCA',width=12);dl.rounded_rectangle((335,145,465,190),23,fill='#B49879');r.place(im,lay,690,1040+160*u,.8)
    for j in range(3):
     y=1040-((t*.35+j/3)%1)*150;d.arc((560+j*75,y,600+j*75,y+85),80,260,fill=(250,255,250,165),width=6)
    r.label(im,L('김 오른 뒤 / 중약불 약 12~15분','Once steaming / medium-low 12–15 min'),(640,825),45,maxw=900)
  else:
   r.place(im,food(),690,1230,.84)
   if sid=='serve':
    if NUM==6:
     arm_tool(im,660+12*math.sin(t*2),1180)
     scoop=Image.new('RGBA',(75,65));ds=ImageDraw.Draw(scoop);ds.ellipse((3,8,72,60),fill='#ECD99D');ds.ellipse((19,23,29,31),fill='#D6986B');r.place(im,scoop,670,1158-10*math.sin(t*2),.7)
    else:r.label(im,L('감자 속까지 부드럽게','Cook Until the Potato Is Tender'),(660,850),47,maxw=900)
   if sid=='joke' and t>1.8:v.sweat(im,390,1010,t);v.bang(im,440,880,t)
   if sid=='hook':v.sparkles(im,t,[(500,930,24),(925,1020,22)])
 return im
p.content=content

def mix():
 path=v.prepare_mix(p.rows());sr=24000
 with wave.open(str(path)) as f:a=np.frombuffer(f.readframes(f.getnframes()),np.int16).astype(np.float32)/32768
 from scipy.signal import butter,sosfilt
 rng=np.random.default_rng(NUM);clock=0
 for row in p.rows():
  if row['id'] in ('prep','mix','cook'):
   for at in np.arange(.8,row['duration']-.4,.62832 if row['id']=='prep' else 1.1):
    length=.12 if row['id']=='prep' else .4;n=int(length*sr);tt=np.arange(n)/sr;fx=sosfilt(butter(2,1800,fs=sr,output='sos'),rng.normal(0,1,n))*np.exp(-tt*(40 if row['id']=='prep' else 8));fx*=.055/max(abs(fx).max(),.001);pos=int((clock+at)*sr);a[pos:pos+n]+=fx
   if row['id']=='cook':
    n=int((row['duration']-.5)*sr);tt=np.arange(n)/sr;fx=sosfilt(butter(2,[700,4300],btype='bandpass',fs=sr,output='sos'),rng.normal(0,1,n))*np.sin(np.pi*tt/(n/sr))**.5;fx*=.008/max(np.sqrt(np.mean(fx*fx)),.001);pos=int((clock+.2)*sr);a[pos:pos+n]+=fx
  clock+=row['duration']
 r.wavwrite(path,a);return path
p.mix=mix

def verify():
 p.verify()
 def pcm(path):return np.frombuffer(subprocess.run([r.FF,'-v','error','-i',str(path),'-t','25','-ac','1','-ar','8000','-f','f32le','pipe:1'],capture_output=True,check=True).stdout,np.float32).astype(np.float64)
 stem=pcm(p.OUT/'liver_ko_music.wav');new=pcm(p.REPO/'bgm'/C['music']);old=pcm(p.REPO/'bgm'/C['previous_music']);n=min(map(len,[stem,new,old]));stem,new,old=stem[:n],new[:n],old[:n]
 corr=lambda x:float(np.dot(stem,x)/(np.linalg.norm(stem)*np.linalg.norm(x)))
 assert corr(new)>.6 and corr(new)>abs(corr(old))*2
 path=p.OUT/'verification.json';report=json.loads(path.read_text(encoding='utf-8'));report.update(language=LANG,chef_voice=C['voice'],narrator_voice='Despina',music=C['music'],different_music_verified='passed',selected_music_correlation=round(corr(new),4),previous_music_correlation=round(corr(old),4));path.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
 print(NUM,LANG,'music verified',round(corr(new),3),round(corr(old),3),flush=True)

def check():
 os.environ['HF_HOME']=str(p.REPO.parent/'cooking_shorts_sample/models')
 from faster_whisper import WhisperModel
 model=WhisperModel('small',device='cpu',compute_type='int8',cpu_threads=3)
 samples=np.frombuffer(subprocess.run([r.FF,'-v','error','-i',str(p.TARGET),'-vn','-ar','16000','-ac','1','-f','f32le','pipe:1'],capture_output=True,check=True).stdout,np.float32);clock=0;report=[]
 for row in p.rows():
  seg,_=model.transcribe(samples[int(clock*16000):int((clock+row['duration'])*16000)],language=LANG,beam_size=5,condition_on_previous_text=False);heard=' '.join(x.text for x in seg).strip();score=difflib.SequenceMatcher(None,norm(row['text']),norm(heard)).ratio();print(NUM,LANG,row['id'],round(score,3),heard,flush=True);assert score>.84
  report.append(dict(id=row['id'],expected=row['text'],heard=heard,similarity=score));clock+=row['duration']
 (p.OUT/'encoded_speech_qa.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')

preflight()
if COMMAND in ('audio','verify','check'):globals()[COMMAND]()
elif COMMAND=='preview':
 if not (p.AUDIO/'manifest.json').exists():(p.AUDIO/'manifest.json').write_text(json.dumps([dict(id=a,title=b,text=c,speaker=d,duration=5) for a,b,c,d,e in p.ROWS],ensure_ascii=False),encoding='utf-8')
 p.preview()
elif COMMAND=='render':p.render()
