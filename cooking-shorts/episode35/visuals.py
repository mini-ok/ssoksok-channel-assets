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








def draw_piece(d,x,y,k,stage):
    if stage=='raw':
        d.rounded_rectangle((x-23*k,y-17*k,x+25*k,y+19*k),6,fill='#D66955',outline='#AE5041',width=3)
        return
    d.arc((x-58*k,y-52*k,x+54*k,y+46*k),8,300,fill='#D87B62',width=max(1,int(26*k)))
    for i in range(4):
        a=(62+i*52)*math.pi/180
        xx=x+43*k*math.cos(a)
        yy=y+37*k*math.sin(a)
        d.ellipse((xx-6*k,yy-4*k,xx+8*k,yy+4*k),fill='#F3AF8D')
    d.polygon([(x+36*k,y+27*k),(x+69*k,y+22*k),(x+59*k,y+49*k)],fill='#BC5F52')

@functools.lru_cache(None)
def asset(kind):
    im=Image.new('RGBA',(240,240))
    d=ImageDraw.Draw(im)
    if kind=='main':
        draw_piece(d,120,119,1.54,'done')
    elif kind=='add':
        d.ellipse((45,63,201,179),fill='#D26A50',outline='#5C7460',width=5)
        d.line((62,121,184,97),fill='#A1B179',width=5)
    elif kind in ('oil','water'):
        d.rounded_rectangle((72,65,171,206),17,fill='#ABA653' if kind=='oil' else '#A0C4D0',outline='#5E756D',width=4)
        d.rectangle((92,41,151,75),fill='#577267')
    else:
        d.ellipse((32,80,208,185),fill='#A8BEB3',outline='#697D70',width=4)
        d.ellipse((45,81,194,145),fill='#F0DBAD')
    return r.paperize(im,NUM*27+len(kind))

@functools.lru_cache(None)
def dish(stage):
    im=Image.new('RGBA',(900,620))
    d=ImageDraw.Draw(im)
    if stage in ('mix','cook'):
        d.rounded_rectangle((683,258,880,321),18,fill='#55756A')
    d.ellipse((90,110,811,537),fill='#94AFA7',outline='#586F68',width=8)
    d.ellipse((127,143,775,480),fill='#F7E6C8' if stage=='raw' else '#B6644C')
    for i in range(12 if stage in ('raw','mix') else 6):
        draw_piece(d,230+(i*93)%444,203+(i*57)%190,1.2,'raw' if stage in ('raw','mix') else 'done')
    if stage!='raw':
        d.arc((215,175,727,447),15,143,fill='#E1986E',width=9)
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
  r.rounded(im,(415,1029,995,1425),'#D7B88C',32,7)
  r.place(im,dish('raw'),702,1241,.66)
  r.place(im,r.prop('knife'),834,1072+17*math.cos(t*7),.39,angle=-15)
 elif sid in ('mix','cook'):
  r.place(im,dish(sid),701,1244,.74)
  arm_tool(im,687+46*math.sin(t*3),1188+13*math.cos(t*3))
  for i in range(4):
   y=1128-(int(t*34)+i*23)%116
   d.arc((556+i*88,y,586+i*88,y+51),77,245,fill='#F2DFC3',width=5)
 else:
  r.place(im,dish('done'),703,1242,.75)
  if sid=='serve':arm_tool(im,703+42*math.sin(t*2),1158)
  if sid=='joke':v.sparkles(im,t,[(523,971,20),(913,1023,19)])
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
