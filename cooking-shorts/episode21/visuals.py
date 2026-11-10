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

@functools.lru_cache(None)
def asset(kind):
    im=Image.new('RGBA',(240,240))
    d=ImageDraw.Draw(im)
    if kind=='main':
        ingredient_shape(d,120,120,.91,'raw')
    elif kind=='leaf':
        d.ellipse((34,46,210,192),fill='#89AA70',outline='#527956',width=5)
        d.line((52,159,188,71),fill='#C2D5A0',width=8)
    elif kind=='water':
        d.rounded_rectangle((66,58,176,209),18,fill='#98BDC9',outline='#536A6A',width=5)
        d.rectangle((87,40,156,71),fill='#536A6A')
    elif kind=='lemon':
        d.ellipse((40,69,197,175),fill='#EFD061',outline='#BD933C',width=4)
    else:
        d.ellipse((35,80,205,180),fill='#C3AB90',outline='#8D7662',width=5)
        d.ellipse((55,92,187,142),fill='#775340')
    return r.paperize(im,NUM*37+len(kind))

@functools.lru_cache(None)
def dish(stage):
    im=Image.new('RGBA',(900,620))
    d=ImageDraw.Draw(im)
    if stage in ('raw','mix','cook'):
        d.rounded_rectangle((687,256,881,319),18,fill='#4E6763')
    d.ellipse((91,103,803,530),fill='#89A8A4',outline='#516E69',width=9)
    d.ellipse((127,135,766,468),fill='#FFF3D9')
    if stage in ('mix','cook','done'):
        d.ellipse((144,155,750,447),fill='#A64465')
    for i in range(12 if stage=='raw' else 8):
        x=226+(i*91)%448
        y=196+(i*59)%190
        ingredient_shape(d,x,y,1.25,stage)
    if stage in ('cook','done'):
        d.arc((202,194,698,420),20,162,fill='#E287A0',width=10)
    return r.paperize(im,NUM*23+len(stage))
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
   y=790+j*125;r.place(im,asset(kind),180,y,.34 if kind!='oil' else .17)
   r.label(im,L(ko,en),(285,y),47,anchor='lm',maxw=410);r.label(im,L(ak,ae),(930,y),42,anchor='rm',maxw=230)
  r.place(im,r.chef(C['character'],'sparkle'),230,1390,.43);return im
 r.place(im,speaking_chef(idx,t),225,1130,.72,angle=math.sin(t*2)*1.3)


 if sid=='prep':
  r.place(im,dish('raw'),699,1224,.72)
  for i in range(5):
   y=1055+(int(t*88)+i*23)%106
   d.ellipse((756+i*7,y,763+i*7,y+8),fill='#9CC5CC')
 elif sid in ('mix','cook'):
  r.place(im,dish(sid),695,1224,.75)
  arm_tool(im,668+58*math.sin(t*3),1174+17*math.cos(t*3))
  if sid=='cook':
   for i in range(6):
    x=550+i*63
    y=1125+(i*19)%96
    rr=4+(i+int(t*7))%9
    d.ellipse((x-rr,y-rr,x+rr,y+rr),outline='#DB7994',width=3)
 else:
  r.place(im,dish('done'),700,1237,.74)
  if sid=='serve':r.place(im,asset('lemon'),862,1022,.34,angle=-22)
  if sid=='joke':v.sparkles(im,t,[(510,958,22),(903,1018,18)])
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
