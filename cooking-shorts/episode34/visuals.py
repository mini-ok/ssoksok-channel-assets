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







def draw_piece(d,x,y,k,stage):
    d.polygon([(x-102*k,y-36*k),(x+100*k,y-22*k),(x+24*k,y+74*k)],fill='#D1A769',outline='#925F3B',width=5)
    d.line((x-95*k,y-24*k,x+92*k,y-11*k),fill='#F4D495',width=8)
    for i in range(9):
        xx=x+((i*29)%121-58)*k
        yy=y+((i*7)%25-21)*k
        d.ellipse((xx,yy,xx+8*k,yy+3*k),fill='#AE7949')

@functools.lru_cache(None)
def asset(kind):
    im=Image.new('RGBA',(240,240))
    d=ImageDraw.Draw(im)
    if kind=='main':
        d.polygon([(37,147),(74,80),(173,62),(207,143),(159,188),(45,186)],fill='#F3E3B7',outline='#C0A87D',width=5)
        d.line((43,149,202,142),fill='#DDC69D',width=7)
    elif kind in ('oil','water'):
        d.rounded_rectangle((68,64,173,206),17,fill='#B69F53' if kind=='oil' else '#BC8252',outline='#5E765F',width=4)
        d.rectangle((90,41,150,77),fill='#637561')
    else:
        d.ellipse((33,82,208,181),fill='#D67859',outline='#8B6A47',width=5)
    return r.paperize(im,NUM*27+len(kind))

@functools.lru_cache(None)
def dish(stage):
    im=Image.new('RGBA',(900,620))
    d=ImageDraw.Draw(im)
    if stage=='cook':
        d.rounded_rectangle((680,261,889,320),20,fill='#56776C')
    d.ellipse((91,109,811,538),fill='#78958A',outline='#59756B',width=9)
    d.ellipse((127,142,775,485),fill='#E5D4AD' if stage=='cook' else '#FFF1D1')
    if stage=='raw':
        for i in range(15):
            x=246+(i*67)%396
            y=194+(i*31)%219
            d.rounded_rectangle((x,y,x+42,y+30),7,fill='#D97A59' if i%2 else '#F3E3BD')
    elif stage in ('mix','cook'):
        d.pieslice((141,141,748,520),180,360,fill='#D5AD70',outline='#956542',width=8)
        d.line((154,329,739,329),fill='#F5D894',width=12)
        for i in range(9):
            x=206+(i*53)%470
            d.line((x,330,x+18,338),fill='#F7DEA5',width=4)
    else:
        for x,y in [(303,226),(525,242),(436,354)]:
            draw_piece(d,x,y,1.19,'done')
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
  r.rounded(im,(415,1029,995,1425),'#D9BA8E',32,7)
  r.place(im,dish('raw'),702,1241,.66)
  r.place(im,r.prop('knife'),834,1072+17*math.cos(t*7),.39,angle=-15)
 elif sid=='mix':
  r.place(im,dish('mix'),701,1244,.73)
  r.place(im,asset('main'),855,1013,.31,angle=-24)
  for i in range(6):
   y=1071+(int(t*66)+i*23)%145
   d.rounded_rectangle((761+i*8,y,773+i*8,y+7),2,fill='#F3E3BF')
 elif sid=='cook':
  r.place(im,dish('cook'),702,1243+15*math.sin(t*3),.73,angle=2*math.sin(t*3))
  arm_tool(im,686+43*math.sin(t*3),1185,'spatula')
 else:
  r.place(im,dish('done'),703,1242,.75)
  if sid in ('serve','joke'):v.sparkles(im,t,[(524,973,20),(913,1024,19)])
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
