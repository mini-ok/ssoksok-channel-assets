"""Final episode 03: Heart chef, apple peanut-butter toast with post-cooking evidence."""
import sys,json,math,functools,wave,subprocess
import numpy as np
from PIL import Image,ImageDraw
import produce as p
r=p.r;v=p.v
p.OUT=p.ROOT/'output_toast';p.AUDIO=p.ROOT/'audio_toast'
p.OUT.mkdir(exist_ok=True);p.AUDIO.mkdir(exist_ok=True)
p.TARGET=p.OUT/'쏙쏙건강요리_사과땅콩버터토스트_한글_v2.mp4'
p.CARD_FILE='사과땅콩버터토스트_전체레시피.png';p.SRT_FILE='사과땅콩버터토스트_한글.srt'
p.RECIPE_NOTE='Original recipe illustrating a saturated-to-unsaturated fat swap; not a trial of this toast or a treatment claim. No kitchen/taste test.'
v.OUT=p.OUT;v.AUDIO=p.AUDIO
p.SOURCE_URL='https://www.heart.org/en/healthy-living/healthy-eating/eat-smart/fats/fats-in-foods'
p.ROWS=[
 ('hook','심장이 고른 지방 바꾸기','버터 대신 땅콩버터! 오늘은 제 심장을 챙기는 토스트예요.','심장 쉐프','신나고 톡톡 튀게.'),
 ('ingredients','재료는 딱 세 가지','통밀빵 한 장, 사과 반 개, 땅콩버터 이십 그램이에요.','여성 내레이터','상큼하고 경쾌하게.'),
 ('chop','01  사과를 얇게 썰어요','사과는 씻어 씨를 빼고 얇게 썰어요. 껍질은 그대로요!','여성 내레이터','밝고 친절하게.'),
 ('spread','02  버터 대신 땅콩버터','땅콩 백 퍼센트, 무가당 무염으로! 빵에 고르게 발라요.','심장 쉐프','신나게 요리하며.'),
 ('top','03  사과를 차곡차곡','사과를 차곡차곡! 아삭한 토스트, 완성이에요!','심장 쉐프','즐겁고 뿌듯하게.'),
 ('serve','왜 심장이 골랐을까요?','버터를 뺐는데도 고소하죠? 제가 이걸 고른 이유가 있어요!','심장 쉐프','기대감을 주며 신나게.'),
 ('benefit','지방의 종류를 바꿔요','포화지방을 불포화지방으로 바꿔 먹으면, 나쁜 콜레스테롤 관리에 도움이 돼요.','여성 내레이터','명랑하고 또렷하게 설명하듯.'),
 ('swap','더하기보다 바꿔 먹기','그래서 버터 대신 땅콩버터! 더 먹는 게 아니라 바꿔 먹는 게, 심장을 위한 포인트예요.','여성 내레이터','친근하고 확실하게.'),
 ('joke','제 간식도 남겨주세요!','심장 챙기는 건 좋은데, 제 간식까지 다 드시면 곤란해요!','심장 쉐프','장난스럽게 억울해하며.'),
 ('end','캡처해서 다음 간식에!','구독은 사원증 발급! 좋아요는 보너스!','심장 쉐프','밝고 신나게 웃으며.')]
v.KEYWORDS={'hook':{'대신'},'ingredients':{'한','반','이십'},'spread':{'백','퍼센트,','무가당','무염으로!'},'benefit':{'포화지방을','불포화지방으로','바꿔','콜레스테롤'},'swap':{'대신','바꿔','심장을'},'joke':{'제','간식까지'}}
PLAN=json.loads((p.ROOT/'plan.json').read_text(encoding='utf-8'))

def preflight():
 ids=[row[0] for row in p.ROWS]
 assert PLAN['chef']=='심장 쉐프' and PLAN['organ']=='심장'
 assert all(PLAN[k] for k in ['dish','main_ingredients','health_focus','reason_for_chef','evidence'])
 assert all(PLAN['review'].values())
 for evidence in PLAN['evidence']:
  assert all(evidence.get(k) for k in ['url','title','checked_at','supported_claim','conditions_and_limits'])
 assert max(ids.index(s) for s in PLAN['cooking_scene_ids'])<min(ids.index(s) for s in PLAN['health_narration_scene_ids'])
 for sid in PLAN['health_narration_scene_ids']:
  row=p.ROWS[ids.index(sid)]
  assert row[3]=='여성 내레이터' and row[2]==PLAN['health_narration_expected'][sid]
  assert sid in PLAN['source_screen_scene_ids']
 print('Organ/recipe/evidence structure preflight passed',flush=True)

@functools.lru_cache(None)
def apple():
 im=Image.new('RGBA',(240,240));d=ImageDraw.Draw(im)
 d.ellipse((29,53,211,219),fill='#D87968');d.ellipse((51,62,187,201),fill='#EA9680')
 d.line((119,70,133,24),fill='#8B7355',width=10);d.ellipse((139,27,199,55),fill='#91B881')
 return r.paperize(im,74)

@functools.lru_cache(None)
def slice_apple():
 im=Image.new('RGBA',(180,210));d=ImageDraw.Draw(im)
 d.pieslice((16,10,170,200),65,295,fill='#CF7665');d.pieslice((24,17,163,194),65,295,fill='#F9ECC7')
 return r.paperize(im,75)

@functools.lru_cache(None)
def jar():
 im=Image.new('RGBA',(240,280));d=ImageDraw.Draw(im)
 d.rounded_rectangle((38,58,202,256),28,fill='#BB8D5C');d.rounded_rectangle((31,23,209,77),13,fill='#8FB09A')
 d.rounded_rectangle((47,110,193,213),12,fill='#FFF3DA')
 r.label(im,'땅콩',(120,144),32);r.label(im,'100%',(120,187),34,style='en')
 return r.paperize(im,76)

@functools.lru_cache(maxsize=40)
def toast(spread=10,apples=5):
 im=Image.new('RGBA',(900,650));d=ImageDraw.Draw(im)
 d.ellipse((60,150,840,620),fill=(60,70,65,35));d.ellipse((60,130,840,590),fill='#F5F1DE')
 d.ellipse((95,160,805,555),outline='#C2D6C4',width=10)
 d.rounded_rectangle((226,95,675,520),60,fill='#BA8955');d.rounded_rectangle((247,114,655,499),48,fill='#E4C996')
 # PB coverage grows from the left as the knife spreads it across the bread.
 if spread:
  lay=Image.new('RGBA',im.size);dl=ImageDraw.Draw(lay)
  dl.rounded_rectangle((268,143,632,474),40,fill='#BB8958')
  for j in range(4):dl.arc((285,165+j*63,610,230+j*63),0,155,fill='#D3A578',width=5)
  lay.putalpha(lay.getchannel('A').point(lambda a:a));lay=lay.crop((0,0,round(268+364*spread/10),650))
  im.alpha_composite(lay,(0,0))
 for i in range(apples):r.place(im,slice_apple(),335+i*49,285+i*20,.82,angle=15)
 return r.paperize(im,77)

def recipe(im):
 r.rounded(im,(72,285,1008,1510),'#FFFCF3',45,11)
 entries=[
 ('사과 땅콩버터 토스트',385,65),('1인 간식 / 약 3분',480,44),('재료',595,54),
 ('통밀빵 1장 · 사과 1/2개',680,49),('땅콩버터 20g',760,51),('땅콩 100% · 무가당 · 무염',833,43),
 ('만드는 법',960,54),('1  사과는 씻어 씨를 빼고 얇게 썰어요.',1055,43),
 ('2  빵에 땅콩버터를 고르게 발라요.',1145,46),('3  사과를 차곡차곡 올리면 완성!',1235,46),
 ('버터 대신 바꿔 먹는 간식이에요.',1370,43)]
 for text,y,size in entries:r.label(im,text,(540,y),size,fill='#638B77' if text in ['재료','만드는 법'] or y==1370 else v.INK,maxw=850)
p.recipe=recipe

def header(im,end):
 r.place(im,p.chip('쏙쏙 건강백과',38,0xFFF9EA),235,108)
 r.place(im,p.chip('쏙쏙 건강요리',44,0xE2F3EC),815,108)
 r.place(im,p.chip('오늘의 요리사 : 심장 쉐프',48,0xF0DBA0),540,222)
 if not end:r.place(im,v.sty.paper_chip('사과 땅콩버터 토스트',64,0x5BB8AA,-2),540,365)
p.header=header

def tool(im,t):
 x=615+72*math.sin(t*2.7);y=1180+25*math.cos(t*2.7)
 d=ImageDraw.Draw(im);grip=(x-45,y-72)
 arm=[(345,1190),(445,1235),grip]
 d.line(arm,fill='#374969',width=22,joint='curve');d.line(arm,fill='#EDABA5',width=15,joint='curve')
 d.line((grip[0]-12,grip[1]-25,x,y),fill='#A98667',width=23)
 d.rounded_rectangle((x-18,y-10,x+18,y+83),16,fill='#CCD9D8')
 d.ellipse((grip[0]-15,grip[1]-15,grip[0]+15,grip[1]+15),fill='#EDABA5',outline='#374969',width=3)

def source_card(im):
 r.rounded(im,(100,910,980,1115),'#FFFCF3',35,9)
 r.label(im,'출처 · 미국심장협회',(540,973),57)
 r.label(im,'지방의 종류와 콜레스테롤',(540,1054),51,fill='#638B77')

def content(idx,t):
 sid=p.ROWS[idx][0];im=Image.new('RGBA',(1080,1920));d=ImageDraw.Draw(im)
 if sid=='end':recipe(im);return im
 if sid=='ingredients':
  r.rounded(im,(95,710,985,1200),'#FFFCF3',42,9)
  for j,(name,amount,sp) in enumerate([('통밀빵','1장',toast(0,0)),('사과','1/2개',apple()),('땅콩버터','20g',jar())]):
   y=795+j*135;r.place(im,sp,190,y,.15 if j==0 else .42)
   r.label(im,name,(300,y),56,anchor='lm');r.label(im,amount,(925,y),54,anchor='rm',fill='#638B77')
  r.label(im,'땅콩 100% · 무가당 · 무염',(540,1255),44,fill='#638B77')
  r.place(im,r.chef('heart','sparkle'),245,1400,.48)
 elif sid=='chop':
  r.place(im,r.chef('heart','serious'),220,1100,.66)
  r.rounded(im,(410,1050,1020,1370),'#D6B184',35,8)
  for i in range(4):r.place(im,slice_apple(),525+i*105,1230,.65,angle=12)
  r.place(im,r.prop('knife'),720,1080+25*math.cos(t*10),.59,angle=-8)
  r.label(im,'씻어서 씨를 빼요',(715,1440),44,fill='#638B77')
 elif sid in ('benefit','swap'):
  if sid=='benefit':
   r.label(im,'포화지방 대신 불포화지방',(540,763),53,fill='#638B77')
   r.label(im,'LDL 콜레스테롤 관리에 도움',(540,845),50)
  else:
   r.label(im,'버터 대신 땅콩버터',(540,763),60,fill='#638B77')
   r.label(im,'더 먹기보다 바꿔 먹는 선택',(540,845),52)
  source_card(im)
  r.place(im,r.chef('heart','proud'),230,1335,.56);r.place(im,toast(),745,1350,.63)
 else:
  mood='shock' if sid=='joke' and t>1.8 else 'serious' if sid=='spread' else 'sparkle'
  r.place(im,r.chef('heart',mood),235,1120,.74,angle=math.sin(t*2)*1.5)
  coverage=max(1,min(10,int(t/2.8*10))) if sid=='spread' else 10
  count=0 if sid=='spread' else max(0,min(5,int((t-.2)*2))) if sid=='top' else 5
  r.place(im,toast(coverage,count),700,1250,.85)
  if sid=='spread':tool(im,t)
  if sid=='top' and count<5:
   u=(t*2)%1;r.place(im,slice_apple(),720+count*20,940+u*190,.55,angle=15)
  if sid in ('hook','serve'):v.sparkles(im,t,[(500,930,24),(925,1060,22)])
  if sid=='joke' and t>1.8:v.sweat(im,390,1010,t);v.bang(im,440,880,t)
 return im
p.content=content

def mix():
 path=v.prepare_mix(p.rows());sr=24000
 with wave.open(str(path)) as f:a=np.frombuffer(f.readframes(f.getnframes()),np.int16).astype(np.float32)/32768
 from scipy.signal import butter,sosfilt
 rng=np.random.default_rng(330);clock=0
 for row in p.rows():
  if row['id']=='spread':
   for at in [1.2,2.3,3.4]:
    count=int(.5*sr);tt=np.arange(count)/sr
    fx=sosfilt(butter(2,1900,fs=sr,output='sos'),rng.normal(0,1,count))*np.sin(np.pi*tt/.5)**2
    fx*=.015/max(np.max(np.abs(fx)),.001);pos=int((clock+at)*sr)
    if at+.5<row['duration']:a[pos:pos+count]+=fx
  if row['id']=='top':
   for at in [.5,1.0,1.5,2.0,2.5]:
    n=int(.07*sr);tt=np.arange(n)/sr;fx=np.sin(2*np.pi*320*tt)*np.exp(-tt*80)*.025
    pos=int((clock+at)*sr);a[pos:pos+n]+=fx
  clock+=row['duration']
 r.wavwrite(path,a);return path
p.mix=mix

if __name__=='__main__':
 preflight()
 if sys.argv[1]=='preflight':pass
 else:getattr(p,sys.argv[1])()
