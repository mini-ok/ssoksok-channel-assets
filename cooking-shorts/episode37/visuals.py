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



def main_art(d,x,y,k,stage):
    d.polygon([(x-8*k,y+36*k),(x+13*k,y+41*k),(x+21*k,y-8*k),(x-4*k,y-16*k)],fill='#83A25A')
    for dx,dy,rr in [(-28,-12,22),(4,-28,28),(32,-13,22),(-8,-7,26)]:
        xx=x+dx*k
        yy=y+dy*k
        d.ellipse((xx-rr*k,yy-rr*k,xx+rr*k,yy+rr*k),fill='#397857' if stage=='raw' else '#467A42',outline='#2B593C',width=3)
    if stage=='done':
        d.line((x-15*k,y-10*k,x+9*k,y-22*k),fill='#D9CE93',width=4)


def ingredient_shape(d,x,y,k,stage):
    for i in range(7):
        a=i*math.tau/7
        xx=x+17*k*math.cos(a)
        yy=y+17*k*math.sin(a)
        d.ellipse((xx-12*k,yy-12*k,xx+12*k,yy+12*k),fill='#C85170',outline='#953652',width=2)
    d.ellipse((x-9*k,y-9*k,x+9*k,y+9*k),fill='#D9637D')









def portion(d,x,y,k,stage):
    points=[(x-133*k,y-41*k),(x+67*k,y-58*k),(x+147*k,y-9*k),(x+93*k,y+51*k),(x-113*k,y+47*k)]
    d.polygon(points,fill='#E6D0B0' if stage=='raw' else '#F4E0B8',outline='#9D846B',width=5)
    for i in range(5):
        xx=x+(i-2)*42*k
        d.arc((xx-24*k,y-38*k,xx+55*k,y+47*k),52,186,fill='#CEAE86',width=5)
    if stage!='raw':
        for i in range(23):
            xx=x+((i*37)%210-107)*k
            yy=y+((i*19)%66-37)*k
            d.ellipse((xx,yy,xx+8*k,yy+5*k),fill='#6D9353' if i%3 else '#EAD067')

@functools.lru_cache(None)
def asset(kind):
    im=Image.new('RGBA',(240,240))
    d=ImageDraw.Draw(im)
    if kind=='main':
        portion(d,120,120,.68,'raw')
    elif kind=='oil':
        d.rounded_rectangle((72,64,172,206),18,fill='#A8A657',outline='#5E7669',width=4)
        d.rectangle((91,42,151,75),fill='#58716B')
    elif kind=='add':
        for x,y in [(81,110),(125,90),(150,137),(102,160)]:
            d.ellipse((x-29,y-20,x+32,y+24),fill='#7D9F62',outline='#50704D',width=3)
        d.line((69,176,163,91),fill='#A8BD79',width=5)
    else:
        d.ellipse((33,80,207,185),fill='#AAC0B2',outline='#617A6D',width=4)
        d.ellipse((45,80,196,143),fill='#EBC863')
    return r.paperize(im,NUM*27+len(kind))

@functools.lru_cache(None)
def dish(stage):
    im=Image.new('RGBA',(900,620))
    d=ImageDraw.Draw(im)
    if stage=='cook':
        d.rounded_rectangle((91,113,812,536),39,fill='#829A90',outline='#5E7C70',width=8)
        d.rounded_rectangle((128,145,778,487),24,fill='#E8D6AF')
    else:
        d.ellipse((91,112,812,537),fill='#A2BEB2',outline='#59796E',width=8)
        d.ellipse((127,145,777,481),fill='#FCEDD0')
    if stage=='mix':
        d.ellipse((181,167,727,445),fill='#AFA96C')
        for i in range(18):
            x=239+(i*71)%416
            y=202+(i*31)%180
            d.ellipse((x,y,x+15,y+7),fill='#598758' if i%3 else '#E8CD63')
    else:
        portion(d,451,297,2.15,'raw' if stage=='raw' else 'done')
    return r.paperize(im,NUM*31+len(stage))
def content(idx,t):
 sid=p.ROWS[idx][0];im=Image.new('RGBA',(1080,1920));d=ImageDraw.Draw(im)
 if sid=='end':recipe(im);return im
 if sid in ('benefit','context'):
  r.rounded(im,(80,690,1000,1250),'#FFFCF3',38,10)
  for j,line in enumerate(C['nutrition_'+LANG][int(sid=='context')]):
   r.label(im,line,(540,765+j*99),57 if j==1 else 42,fill='#638B77' if j==1 else v.INK,maxw=850)
  r.place(im,r.chef(C['character'],'proud'),220,1370,.4);r.place(im,dish('done'),750,1380,.43);return im
 if sid=='ingredients':
  r.rounded(im,(95,700,985,1280),'#FFFCF3',42,9)
  for j,(ko,en,ak,ae,kind) in enumerate(C['ingredients']):
   y=765+j*110;r.place(im,asset(kind),180,y,.34 if kind!='oil' else .17)
   r.label(im,L(ko,en),(285,y),47,anchor='lm',maxw=410);r.label(im,L(ak,ae),(930,y),42,anchor='rm',maxw=230)
  r.place(im,r.chef(C['character'],'sparkle'),230,1390,.43);return im
 r.place(im,speaking_chef(idx,t),225,1130,.72,angle=math.sin(t*2)*1.3)










 if sid=='prep':
  r.place(im,dish('raw'),702,1242,.74)
  pad_y=1084+17*math.sin(t*5)
  r.rounded(im,(789,pad_y,917,pad_y+71),'#F9EFD8',12,2)
 elif sid=='mix':
  r.place(im,dish('mix'),701,1244,.74)
  arm_tool(im,692+49*math.sin(t*3),1188+14*math.cos(t*3))
 elif sid=='cook':
  r.rounded(im,(421,967,998,1412),'#879F93',35,8)
  r.place(im,dish('cook'),707,1241,.68)
  d.line((841,1089,758,1180),fill='#56706A',width=7)
  r.rounded(im,(796,1027,925,1097),'#F5F1D5',13,2)
  r.label(im,'63°C',(858,1060),35,maxw=107)
 else:
  r.place(im,dish('done'),704,1240,.75)
  if sid in ('hook','joke'):v.sparkles(im,t,[(523,972,20),(920,1024,21)])
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
  if row['id']=='cook':
   for at in np.arange(.8,row['duration']-.4,1.25):
    n=int(.16*sr);tt=np.arange(n)/sr
    fx=rng.normal(0,.48,n)*np.exp(-tt*24)*.025
    pos=int((clock+at)*sr);a[pos:pos+n]+=fx
  clock+=row['duration']
 r.wavwrite(path,a);return path
p.mix=cooking_mix
