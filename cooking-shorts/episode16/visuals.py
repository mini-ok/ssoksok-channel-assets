"""Porridge and grill scenes with speech-gated chef sprites."""
@functools.lru_cache(None)
def speech_envelope(sid):
 path=p.AUDIO/(sid+'.wav')
 if not path.exists():
  return np.zeros(0,dtype=bool)
 with wave.open(str(path)) as f:
  rate=f.getframerate()
  samples=np.frombuffer(f.readframes(f.getnframes()),np.int16).astype(np.float32)/32768
 step=rate//50
 count=(len(samples)+step-1)//step
 if not count:
  return np.zeros(0,dtype=bool)
 blocks=np.pad(samples,(0,count*step-len(samples))).reshape(count,step)
 rms=np.sqrt(np.mean(blocks**2,axis=1))
 voiced=rms>max(.0025,float(rms.max())*.055)
 return np.convolve(voiced.astype(int),np.ones(5,dtype=int),'full')[2:2+count]>0

@functools.lru_cache(None)
def speech_row(idx):
 return p.rows()[idx]

def mouth_state(idx,t):
 row=speech_row(idx)
 elapsed=t-(.18 if idx==0 else 1.0)
 if row['speaker']!=chef or not 0<=elapsed<row.get('speech_duration',0):
  return None
 activity=speech_envelope(row['id'])
 frame=int(elapsed*50)
 if frame>=len(activity) or not activity[frame]:
  return None
 return int(elapsed*8)%3

def speaking_chef(idx,t):
 talk=mouth_state(idx,t)
 mood='shock' if p.ROWS[idx][0]=='joke' and t>2 and talk is None else 'sparkle'
 return r.chef(C['character'],mood,talk=talk)

@functools.lru_cache(None)
def asset(kind):
 im=Image.new('RGBA',(240,240));d=ImageDraw.Draw(im)
 if kind=='barley':
  d.ellipse((18,65,221,202),fill='#C0D3C6');d.ellipse((25,53,215,157),fill='#E8D9B5')
  for j in range(44):
   x=39+(j*43)%155;y=67+(j*23)%69;d.ellipse((x,y,x+15,y+7),fill='#BA9D72')
 elif kind=='pumpkin':
  d.polygon([(37,69),(177,42),(208,96),(151,200),(45,176)],fill='#EAB06F',outline='#9D7349',width=4)
  d.line((46,176,151,200,208,96),fill='#8D9C65',width=10)
 elif kind=='chicken':
  d.polygon([(31,139),(50,82),(108,50),(184,68),(215,114),(188,175),(107,205),(59,178)],fill='#DCA6A1',outline='#A57874',width=4)
 elif kind=='lemon':
  d.pieslice((30,45,210,208),0,180,fill='#E9CD6B',outline='#BD9D4A',width=5)
  for x in [70,115,160]:d.line((120,126,x,183),fill='#F9E5A0',width=5)
 elif kind=='oil':
  return r.prop('oil')
 else:
  d.polygon([(50,30),(190,30),(172,220),(68,220)],fill='#B5D3D5',outline='#526B72')
 return r.paperize(im,NUM*71+len(kind))

@functools.lru_cache(maxsize=8)
def meal(stage='done'):
 im=Image.new('RGBA',(900,620));d=ImageDraw.Draw(im)
 if NUM==15:
  if stage!='done':
   d.rounded_rectangle((74,241,162,307),20,fill='#789994')
   d.rounded_rectangle((738,241,826,307),20,fill='#789994')
  d.pieslice((112,130,788,570),0,180,fill='#A9C7BA',outline='#526B72',width=6)
  d.ellipse((112,137,788,471),fill='#E6AB69',outline='#526B72',width=6)
  for j in range(62):
   x=195+(j*67)%490;y=196+(j*43)%218
   if ((x-450)/255)**2+((y-304)/112)**2<1:
    d.ellipse((x,y,x+19,y+8),fill='#EED29E')
 else:
  d.ellipse((65,110,835,555),fill='#50666A' if stage!='done' else '#B6D0C4')
  if stage!='done':
   for x in range(162,746,52):d.line((x,217,x,437),fill='#789092',width=9)
  d.polygon([(237,343),(258,243),(385,183),(548,203),(659,275),(602,398),(424,460),(293,416)],fill='#DCA6A1' if stage=='raw' else '#CEA16F',outline='#87654D',width=7)
  if stage!='raw':
   for j in range(5):
    x=300+j*59;d.line((x,270,x-20,380),fill='#916B49',width=10)
  if stage=='done':r.place(im,asset('lemon'),690,420,.7,angle=-10)
 return r.paperize(im,NUM*31+len(stage))

def content(idx,t):
 sid=p.ROWS[idx][0];im=Image.new('RGBA',(1080,1920));d=ImageDraw.Draw(im)
 if sid=='end':recipe(im);return im
 if sid in ('benefit','context'):
  r.rounded(im,(80,690,1000,1250),'#FFFCF3',38,10)
  for j,line in enumerate(C['nutrition_'+LANG][int(sid=='context')]):
   r.label(im,line,(540,765+j*99),57 if j==1 else 42,fill='#638B77' if j==1 else v.INK,maxw=850)
  r.place(im,r.chef(C['character'],'proud'),220,1370,.4);r.place(im,meal(),750,1380,.43);return im
 if sid=='ingredients':
  r.rounded(im,(95,700,985,1280),'#FFFCF3',42,9)
  for j,(ko,en,ak,ae,kind) in enumerate(C['ingredients']):
   y=790+j*125;r.place(im,asset(kind),180,y,.34 if kind!='oil' else .17)
   r.label(im,L(ko,en),(285,y),47,anchor='lm',maxw=410);r.label(im,L(ak,ae),(930,y),42,anchor='rm',maxw=230)
  r.place(im,r.chef(C['character'],'sparkle'),230,1390,.43);return im
 r.place(im,speaking_chef(idx,t),225,1130,.72,angle=math.sin(t*2)*1.3)
 if sid=='prep' and NUM==15:
  r.rounded(im,(415,1050,1000,1390),'#D5B488',30,7);r.place(im,asset('pumpkin'),706,1225,.85)
  y=1210+22*math.cos(t*7)
  d.line((793,y-180,720,y),fill='#A9BAB9',width=17)
  for x in range(702,748,12):d.line((x,y-13,x,y+24),fill='#819395',width=6)
 elif sid=='prep':
  r.rounded(im,(415,1050,1000,1390),'#D5B488',30,7);r.place(im,asset('chicken'),688,1235,.95)
  x=713+56*math.sin(t*3);d.line((x+82,1090,x,1215),fill='#A98564',width=14);d.rounded_rectangle((x-25,1202,x+21,1233),7,fill='#E4C48D')
 elif sid in ('mix','cook'):
  r.place(im,meal('raw' if sid=='mix' and NUM==16 and t<1.5 else 'mix'),700,1245,.73)
  if NUM==15:
   arm_tool(im,665+60*math.sin(t*2.5),1240+14*math.cos(t*2.5),'spoon')
   if sid=='mix':r.place(im,asset('barley'),872,1020,.32,angle=-20)
   else:
    for j in range(3):
     yy=1035-((t*.35+j/3)%1)*100;d.arc((620+j*70,yy,660+j*70,yy+65),65,265,fill='#D5DED2',width=6)
  elif sid=='mix':
   x=679+35*math.sin(t*2)
   for dy in [-12,12]:d.line((x+123,1060,x,1230+dy),fill='#AAB8B8',width=11)
  else:
   d.line((744,1132,695,1237),fill='#9DB0B1',width=9)
   r.rounded(im,(724,1030,895,1145),'#DDE9E1',18,4)
   r.label(im,L('74°C','165°F / 74°C'),(810,1085),32,maxw=151)
 else:
  r.place(im,meal(),700,1245,.73)
  if sid=='serve' and NUM==16:
   r.place(im,asset('lemon'),791,1005,.46,angle=-20)
   for j in range(4):
    y=1085+(int(t*125)+j*22)%125;d.ellipse((762+j*8,y,768+j*8,y+9),fill='#D8BB61')
  if sid=='hook':v.sparkles(im,t,[(495,930,24),(945,1030,22)])
  if sid=='joke' and t>2:v.bang(im,430,890,t)
 return im
p.content=content
_base_frame=p.frame
@functools.lru_cache(maxsize=3)
def _fixed_frame(idx):return _base_frame(idx,1.0)
def _frame(idx,t):
 if idx in (6,7,9) and t>=.85:return _fixed_frame(idx)
 return _base_frame(idx,t)
p.frame=_frame

_base_preview=p.preview
def preview_with_mouth_check():
 _base_preview()
 if not (p.AUDIO/'hook.wav').exists():
  return
 states=[mouth_state(0,i/24) for i in range(int(24*speech_row(0)['duration']))]
 assert {0,1,2}.issubset(set(states)), 'Hook did not use all three mouth states'
 assert mouth_state(0,0) is None and mouth_state(0,speech_row(0)['duration']) is None
 assert mouth_state(6,2) is None, 'Narration must not animate the chef mouth'
 sprites=[r.chef(C['character'],'sparkle',talk=k) for k in [None,0,1,2]]
 assert len({im.tobytes() for im in sprites[1:]})==3, 'Mouth sprites must differ'
 for k,im in enumerate(sprites):
  im.save(p.OUT/f'mouth_preview_{k}.png')
 print(f'MOUTH_QA {NUM} {LANG}: three distinct sprites; silence and narration gated',flush=True)
p.preview=preview_with_mouth_check

def cooking_mix():
 path=v.prepare_mix(p.rows())
 with wave.open(str(path)) as f:a=np.frombuffer(f.readframes(f.getnframes()),np.int16).astype(np.float32)/32768
 clock=0;sr=24000;rng=np.random.default_rng(NUM)
 for row in p.rows():
  if row['id']==('cook' if NUM==15 else 'mix'):
   for at in np.arange(.8,row['duration']-.4,1.25):
    n=int(.16*sr);tt=np.arange(n)/sr
    fx=(np.sin(2*np.pi*320*tt) if NUM==15 else rng.normal(0,.55,n))*np.exp(-tt*24)*.025
    pos=int((clock+at)*sr);a[pos:pos+n]+=fx
  clock+=row['duration']
 r.wavwrite(path,a);return path
p.mix=cooking_mix
