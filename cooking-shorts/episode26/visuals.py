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



def piece(d,x,y,k,kind):
    if kind=='ball':
        d.ellipse((x-53*k,y-51*k,x+53*k,y+51*k),fill='#704C3E',outline='#52362F',width=4)
        for i in range(16):
            dx=((i*37)%72-36)*k
            dy=((i*21)%66-33)*k
            d.ellipse((x+dx,y+dy,x+dx+9*k,y+dy+4*k),fill='#D7BC82')
    elif kind=='date':
        d.ellipse((x-34*k,y-19*k,x+34*k,y+19*k),fill='#A5664F',outline='#704839',width=3)
        d.arc((x-27*k,y-11*k,x+22*k,y+11*k),189,327,fill='#D29267',width=3)
    else:
        d.ellipse((x-18*k,y-7*k,x+18*k,y+7*k),fill='#E3C692',outline='#A48C62',width=2)

@functools.lru_cache(None)
def asset(kind):
    im=Image.new('RGBA',(240,240))
    d=ImageDraw.Draw(im)
    if kind=='main':
        for x,y in [(76,104),(121,127),(168,100),(99,156),(157,153)]:
            piece(d,x,y,1.2,'seed')
    elif kind=='oil':
        d.rounded_rectangle((71,65,170,204),17,fill='#A6C9D3',outline='#5C7373',width=4)
        d.rectangle((91,41,150,73),fill='#637B70')
    elif kind=='lemon':
        d.ellipse((38,71,203,174),fill='#EFCE65',outline='#BB9446',width=4)
        d.arc((61,85,174,154),28,157,fill='#FFF1A7',width=6)
    elif kind=='add':
        piece(d,99,113,1.2,'date')
        piece(d,141,146,1.2,'date')
    else:
        d.ellipse((34,82,208,185),fill='#9EB8A7')
        d.ellipse((50,81,194,148),fill='#885C48')
    return r.paperize(im,NUM*29+len(kind))

@functools.lru_cache(None)
def dish(stage):
    im=Image.new('RGBA',(900,620))
    d=ImageDraw.Draw(im)
    if stage=='mix' and NUM==25:
        d.rounded_rectangle((677,262,873,322),18,fill='#56736B')
    d.ellipse((89,111,811,536),fill='#819F97',outline='#4C6B65',width=9)
    d.ellipse((121,137,778,476),fill='#F6E9CB')
    if stage=='raw':
        for i in range(16):
            piece(d,226+(i*73)%405,196+(i*39)%198,1.1,'seed' if i%3 else 'date')
    elif stage=='mix':
        d.ellipse((163,168,737,443),fill='#80513F')
        d.arc((215,199,682,410),29,298,fill='#B37B5C',width=15)
    else:
        for x,y in [(304,261),(550,257),(451,367)]:
            piece(d,x,y,1.35,'ball')
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
  r.place(im,dish('raw'),703,1244,.75)
  arm_tool(im,681+29*math.sin(t*4),1190+16*math.cos(t*7))
 elif sid=='mix':
  r.place(im,dish('mix'),703,1244,.75)
  arm_tool(im,684+51*math.sin(t*4),1190+16*math.cos(t*4))
 elif sid=='cook':
  r.place(im,dish('done'),703,1244,.75)
  r.place(im,asset('main'),866,1017,.34,angle=-20)
  for i in range(7):
   y=1077+(int(t*83)+i*19)%123
   d.ellipse((780+i*9,y,788+i*9,y+5),fill='#D7BC82')
 else:
  r.place(im,dish('done'),703,1244,.75,angle=2*math.sin(t*3) if sid=='joke' else 0)
  if sid in ('serve','joke'):v.sparkles(im,t,[(515,976,18),(925,1028,22)])
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
