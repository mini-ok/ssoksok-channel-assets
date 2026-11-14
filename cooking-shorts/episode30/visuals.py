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





def draw_piece(d,x,y,scale,kind):
    k=scale
    if kind=='cube':
        d.polygon([(x-29*k,y-13*k),(x+3*k,y-25*k),(x+31*k,y-9*k),(x+27*k,y+23*k),(x-3*k,y+30*k),(x-29*k,y+13*k)],fill='#EDAD4B',outline='#B37D35',width=4)
        d.line((x-29*k,y-13*k,x-4*k,y+2*k,x+31*k,y-9*k),fill='#FFDA78',width=4)
    else:
        d.polygon([(x-22*k,y+12*k),(x-10*k,y-17*k),(x+11*k,y-22*k),(x+25*k,y+7*k),(x+4*k,y+23*k)],fill='#F5BC55',outline='#D39045',width=3)
        d.line((x-10*k,y-17*k,x+4*k,y+23*k),fill='#FFE8A3',width=3)

@functools.lru_cache(None)
def asset(kind):
    im=Image.new('RGBA',(240,240))
    d=ImageDraw.Draw(im)
    if kind=='main':
        for x,y in [(79,113),(140,97),(157,150),(103,159)]:
            draw_piece(d,x,y,1.05,'cube')
    elif kind=='oil':
        d.rounded_rectangle((72,65,170,203),17,fill='#A8C0CF',outline='#5C7373',width=4)
        d.rectangle((92,42,151,74),fill='#5C7373')
    else:
        d.ellipse((31,79,206,187),fill='#A3BDAF',outline='#6B8271',width=4)
        d.ellipse((43,77,195,145),fill='#C5CE78')
    return r.paperize(im,NUM*21+len(kind))

@functools.lru_cache(None)
def dish(stage):
    im=Image.new('RGBA',(900,620))
    d=ImageDraw.Draw(im)
    if stage=='done':
        d.polygon([(244,238),(655,238),(568,483),(334,483)],fill='#B4D0D0',outline='#64878A',width=8)
        d.ellipse((245,193,655,303),fill='#F7D98A',outline='#8DA9A1',width=7)
        coords=[(282+(i*83)%333,213+(i*31)%157) for i in range(21)]
    else:
        d.rounded_rectangle((92,121,812,525),38,fill='#95B5AE',outline='#607F76',width=8)
        d.rounded_rectangle((127,154,778,489),24,fill='#F8D174' if stage=='mix' else '#FAEDCD')
        coords=[(206+(i*99)%477,217+(i*37)%192) for i in range(18)]
    for x,y in coords:
        if stage!='mix':
            draw_piece(d,x,y,1.14,'cube' if stage=='raw' else 'ice')
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
  r.rounded(im,(418,1031,994,1421),'#D5B68C',31,7)
  r.place(im,dish('raw'),701,1241,.66)
  r.place(im,r.prop('knife'),836,1085+17*math.cos(t*7),.39,angle=-16)
 elif sid=='mix':
  r.place(im,dish('mix'),701,1244,.73)
  r.place(im,asset('add'),856,1022,.36,angle=-25)
 elif sid=='cook':
  r.place(im,dish('cook'),700,1244,.74)
  arm_tool(im,690+54*math.sin(t*3),1187+12*math.cos(t*3))
  v.sparkles(im,t,[(561,1130,12),(787,1160,17),(854,1255,12)])
 else:
  r.place(im,dish('done'),704,1236,.77)
  if sid in ('serve','joke'):v.sparkles(im,t,[(527,972,20),(911,1024,21)])
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
