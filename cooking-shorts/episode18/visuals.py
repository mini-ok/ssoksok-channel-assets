def bone(cv,x,y,s=1.0,mood='happy',lt=0.0):
    cv.save();cv.translate(x,y);cv.scale(s,s)
    shadow(cv,160);feet(cv,145,0xE5D9BE,gap=50)
    limb(cv,-80,25,-140,77,0xF6EBD5);limb(cv,80,25,140,77,0xF6EBD5)
    shape=union(oval_path(0,20,155,265),circle_path(-55,-90,62),circle_path(55,-90,62),circle_path(-48,118,47),circle_path(48,118,47))
    blob(cv,shape,0xEFE4CC,0xFFF9EC,shade=0xD7C5A1)
    face(cv,0,-10,.91,mood,blush=0xEBAFAA,talk=(lt if lt else None))
    cv.restore()


r.ch.bone=bone
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
 if kind=='tofu':
  d.polygon([(32,91),(104,52),(203,82),(203,175),(133,211),(32,183)],fill='#E9E2C7',outline='#A6987E',width=4)
  d.polygon([(32,91),(104,52),(203,82),(133,124)],fill='#FFF8E3')
  d.line((133,124,133,211),fill='#BAAF91',width=5)
 elif kind=='egg':
  d.ellipse((50,24,192,217),fill='#F5E7CC',outline='#B9A788',width=5)
 elif kind=='ginger':
  for x,y in [(63,73),(128,58),(151,112),(92,139)]:d.ellipse((x-37,y-19,x+49,y+48),fill='#D6A96F',outline='#9E7D55',width=4)
 elif kind in ('paprika','sauce'):
  d.ellipse((25,69,216,205),fill='#C6D6CE');d.ellipse((30,62,211,163),fill='#AF5240' if kind=='paprika' else '#8F5C45')
 else:
  d.polygon([(50,30),(190,30),(172,220),(68,220)],fill='#B5D3D5',outline='#526B72')
 return r.paperize(im,NUM*71+len(kind))

@functools.lru_cache(maxsize=8)
def meal(stage='done'):
 im=Image.new('RGBA',(900,620));d=ImageDraw.Draw(im)
 if NUM==17:
  d.ellipse((77,117,827,535),fill='#AFCEC1');d.ellipse((100,135,807,503),fill='#FFF4DF')
  for x,y in [(255,270),(436,228),(598,272),(356,374),(545,384)]:
   d.polygon([(x-72,y-24),(x+24,y-57),(x+72,y-25),(x+72,y+42),(x-22,y+74),(x-72,y+39)],fill='#E8DCC2',outline='#AF9C7E',width=4)
   d.polygon([(x-72,y-24),(x+24,y-57),(x+72,y-25),(x-22,y+8)],fill='#FFF4DC')
   if stage=='done':d.ellipse((x-36,y-22,x+27,y+3),fill='#AA7652')
 elif stage=='pot':
  d.rounded_rectangle((75,248,163,309),17,fill='#7B9694');d.rounded_rectangle((740,248,825,309),17,fill='#7B9694')
  d.pieslice((105,140,795,561),0,180,fill='#AAC7C3',outline='#526B72',width=6)
  d.ellipse((105,140,795,453),fill='#AACDD0',outline='#526B72',width=6)
  r.place(im,asset('egg'),450,297,1.05,angle=-22)
 else:
  d.ellipse((77,117,827,535),fill='#AAC7BB');d.ellipse((104,140,803,505),fill='#FFF4DE')
  for x in (316,595):
   d.ellipse((x-99,190,x+99,431),fill='#FFF9E8',outline='#C5B79E',width=5)
   d.ellipse((x-56,251,x+56,373),fill='#EDBB54',outline='#CF9D47',width=4)
   if stage=='done':
    for j in range(15):
     xx=x-37+(j*31)%76;y=272+(j*19)%81;d.ellipse((xx,y,xx+5,y+5),fill='#A75742')
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
 if sid=='prep' and NUM==17:
  r.rounded(im,(415,1050,1000,1390),'#D5B488',30,7);r.place(im,asset('tofu'),694,1225,.85)
  r.place(im,r.prop('knife'),763,1090+22*math.cos(t*8),.49,angle=-9)
 elif sid in ('prep','mix') and NUM==18:
  r.place(im,meal('pot'),700,1245,.73)
  if sid=='prep':
   r.place(im,asset('water'),828,1030,.40,angle=-27)
   d.line((779,1080,740,1150),fill='#B5D6DA',width=11)
  else:
   for j in range(8):
    x=552+(j*43)%299;y=1168+(j*19)%76
    rr=4+(int(t*9)+j)%8;d.ellipse((x-rr,y-rr,x+rr,y+rr),outline='#EEF2E6',width=3)
 elif sid=='mix':
  r.rounded(im,(438,980,989,1415),'#B6CEC8',34,8);r.rounded(im,(475,1030,857,1345),'#E5E8D9',20,5)
  r.place(im,meal('plain'),663,1181,.46);d.ellipse((893,1072,942,1121),fill='#6D8F88')
 elif sid=='cook':
  r.place(im,meal('plain'),700,1245,.73)
  if NUM==17:
   r.place(im,asset('sauce'),853,1018,.38,angle=-24)
   arm_tool(im,656+52*math.sin(t*2.2),1200+10*math.cos(t*2.2),'spoon')
   for j in range(5):
    y=1115+(int(t*98)+j*22)%92;d.ellipse((728+j*8,y,737+j*8,y+10),fill='#956347')
  else:
   r.place(im,r.prop('knife'),778,1045+20*math.cos(t*7),.40,angle=-10)
 else:
  r.place(im,meal(),700,1245,.73)
  if sid=='serve' and NUM==18:
   r.place(im,asset('paprika'),834,1020,.31,angle=-18)
   for j in range(8):
    y=1080+(int(t*99)+j*21)%120;d.ellipse((757+j*6,y,762+j*6,y+5),fill='#AF5944')
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
  if row['id']==('prep' if NUM==17 else 'mix'):
   for at in np.arange(.8,row['duration']-.4,1.25):
    n=int(.16*sr);tt=np.arange(n)/sr
    fx=(np.sin(2*np.pi*320*tt) if NUM==18 else rng.normal(0,.55,n))*np.exp(-tt*24)*.025
    pos=int((clock+at)*sr);a[pos:pos+n]+=fx
  clock+=row['duration']
 r.wavwrite(path,a);return path
p.mix=cooking_mix
