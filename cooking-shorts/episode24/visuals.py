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


def food_piece(draw,x,y,scale,stage):
    draw.rounded_rectangle((x-19*scale,y-2*scale,x+24*scale,y+50*scale),12,fill='#E3CCA5',outline='#9A7958',width=3)
    draw.pieslice((x-64*scale,y-48*scale,x+65*scale,y+42*scale),180,360,fill='#F0DDC1' if stage=='raw' else '#BA8553',outline='#936644',width=4)
    for i in range(5):
        xx=x+(i-2)*17*scale
        draw.line((x,y+1,xx,y-10*scale),fill='#A78168',width=3)

@functools.lru_cache(None)
def asset(kind):
    im=Image.new('RGBA',(240,240))
    d=ImageDraw.Draw(im)
    if kind=='main':
        food_piece(d,120,117,1.35,'raw')
    elif kind=='oil':
        d.rounded_rectangle((74,68,170,205),17,fill='#9DA04E',outline='#5E6848',width=4)
        d.rectangle((91,39,151,76),fill='#545E48')
    elif kind=='lemon':
        d.ellipse((41,69,203,172),fill='#EED16A',outline='#B99644',width=4)
        d.arc((61,81,185,159),20,160,fill='#FFF0A9',width=6)
    elif kind=='add' and NUM==24:
        d.polygon([(74,55),(145,55),(172,89),(172,209),(74,209)],fill='#ECF1DF',outline='#7B9B92',width=4)
        d.rectangle((80,114,166,158),fill='#80AEA9')
    else:
        d.ellipse((30,83,211,194),fill='#A5BBB2',outline='#637A70',width=5)
        d.ellipse((42,82,201,147),fill='#E1AF52' if kind=='add' else '#F2E1C6')
    return r.paperize(im,NUM*37+len(kind))

@functools.lru_cache(None)
def dish(stage):
    im=Image.new('RGBA',(900,620))
    d=ImageDraw.Draw(im)
    pan=stage=='cook'
    if pan:
        d.rounded_rectangle((697,268,879,326),19,fill='#506E67')
    d.ellipse((79,103,813,530),fill='#708C83' if pan else '#A2BDB1',outline='#546C63',width=8)
    d.ellipse((116,132,780,475),fill='#B3B9A0' if pan else '#FFF4DB')
    if stage=='mix':
        d.ellipse((171,176,724,425),fill='#F6ECD5')
        d.arc((299,205,621,388),12,283,fill='#D8BC97',width=8)
        return r.paperize(im,NUM*27+len(stage))
    if stage=='done':
        d.ellipse((153,159,747,451),fill='#EBD6A4')
    for x,y in [(285,224),(462,210),(601,272),(345,336),(532,369)]:
        food_piece(d,x,y,1.25,stage)
    return r.paperize(im,NUM*27+len(stage))
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
  r.rounded(im,(421,1025,1000,1420),'#D8B98E',31,7)
  r.place(im,dish('raw'),697,1229,.66)
  r.place(im,r.prop('knife'),830,1081+19*math.cos(t*7),.39,angle=-16)
 elif sid=='mix':
  r.place(im,dish('mix'),699,1242,.73)
  arm_tool(im,678+54*math.sin(t*4),1193+17*math.cos(t*4))
 elif sid=='cook':
  r.place(im,dish('cook'),700,1254,.73)
  arm_tool(im,686+45*math.sin(t*3),1182+15*math.cos(t*3))
  for i in range(3):
   y=1111-(int(t*34)+i*21)%112
   d.arc((578+i*108,y,608+i*108,y+49),71,252,fill='#F1E4CD',width=5)
 else:
  r.place(im,dish('done'),700,1242,.74)
  if sid=='serve':
   r.place(im,asset('lemon'),854,1029,.36,angle=-25)
   for i in range(4):
    y=1081+(int(t*83)+i*19)%96
    d.ellipse((775+i*9,y,782+i*9,y+8),fill='#F0D268')
  if sid in ('hook','joke'):v.sparkles(im,t,[(509,960,21),(919,1025,19)])
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
