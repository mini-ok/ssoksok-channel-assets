def eye(cv,x,y,s=1.0,mood='happy',lt=0.0):
    cv.save();cv.translate(x,y);cv.scale(s,s)
    shadow(cv,155);feet(cv,140,0xD2E6DD,gap=52)
    limb(cv,-121,25,-157,77,0xE4EFE5);limb(cv,121,25,157,77,0xE4EFE5)
    blob(cv,oval_path(0,0,285,260),0xF1F2DF,0xFFFFF2,shade=0xDDE2CE)
    blob(cv,circle_path(0,-25,76),0x7DB6B0,0xB4DAD0,shade=0x5C8D91,ow=5)
    cv.drawCircle(0,-25,43,P(INK));cv.drawCircle(-18,-46,17,P(WHITE));cv.drawCircle(21,-9,8,P(WHITE))
    for xx in [-91,91]:cv.drawOval(skia.Rect.MakeXYWH(xx-14,53,28,14),P(0xECAFA6))
    mouth=skia.Path();mouth.moveTo(-22,43);mouth.quadTo(0,57,22,43);cv.drawPath(mouth,P(INK,'stroke',5))
    if mood=='shock':cv.drawOval(skia.Rect.MakeXYWH(-11,40,22,19),P(INK))
    if lt:
        size=(3,8,18)[int(lt)%3]
        cv.drawOval(skia.Rect.MakeXYWH(-size,46-size/2,size*2,size),P(INK))
    cv.restore()


r.ch.eye=eye
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
    box=(x-94*k,y-40*k,x+94*k,y+40*k)
    d.ellipse(box,fill='#9C5547',outline='#723D34',width=4)
    if stage!='raw':
        d.ellipse((x-81*k,y-33*k,x+81*k,y+23*k),fill='#EA9B48')
        for j in range(12):
            xx=x+((j*37)%134-67)*k
            yy=y+((j*19)%30-19)*k
            d.ellipse((xx,yy,xx+7*k,yy+3*k),fill='#B86A35')

@functools.lru_cache(None)
def asset(kind):
    im=Image.new('RGBA',(240,240))
    d=ImageDraw.Draw(im)
    if kind=='main':
        main_art(d,120,120,1,'raw')
    elif kind=='oil':
        d.rounded_rectangle((70,67,170,209),20,fill='#A3A552',outline='#656F47',width=5)
        d.rectangle((94,37,145,79),fill='#6B6B48')
        d.rectangle((78,121,163,159),fill='#F3E5B5')
    elif kind=='lemon':
        d.ellipse((40,69,197,175),fill='#EFD061',outline='#BD933C',width=4)
        d.arc((64,82,165,160),20,155,fill='#FFF3BC',width=7)
    else:
        d.ellipse((31,93,210,204),fill='#B6D4CB',outline='#647F74',width=5)
        d.ellipse((38,83,203,153),fill='#A97646')
    return r.paperize(im,NUM*71+len(kind))

@functools.lru_cache(maxsize=8)
def meal(stage='done'):
    im=Image.new('RGBA',(900,620))
    d=ImageDraw.Draw(im)
    if stage=='cook':
        d.rounded_rectangle((681,284,870,338),18,fill='#526B66')
        d.ellipse((105,120,778,530),fill='#69817A',outline='#3F5955',width=12)
        d.ellipse((143,151,745,485),fill='#A9B5A3')
    elif stage=='mix':
        d.ellipse((119,151,781,529),fill='#8CAFA9')
        d.ellipse((145,159,754,450),fill='#EBA659')
    else:
        d.ellipse((77,117,827,535),fill='#9EBCB0')
        d.ellipse((105,141,800,504),fill='#FFF4DA')
    if stage!='mix':
        for x,y in [(338,260),(563,364)]:
            main_art(d,x,y,1.6,stage)
    else:
        for j in range(13):
            x=254+(j*63)%376
            y=236+(j*41)%157
            d.ellipse((x,y,x+19,y+9),fill='#B07B50')
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

 if sid=='prep':
  r.rounded(im,(450,960,980,1390),'#829894',34,8)
  r.rounded(im,(485,1030,944,1320),'#B8AFA0',26,6)
  r.place(im,asset('main'),698,1170,.77)
  for j in range(3):
   y=1090-(int(t*27)+j*19)%94
   d.arc((630+j*53,y,662+j*53,y+45),70,245,fill='#F7E3C2',width=5)
 elif sid=='mix':
  r.place(im,meal('mix'),702,1244,.73)
  arm_tool(im,680+48*math.sin(t*3),1210+16*math.cos(t*3))
 elif sid=='cook':
  r.rounded(im,(439,959,980,1400),'#829894',34,8)
  r.place(im,meal('cook'),712,1220+19*math.sin(t*2),.64)
  v.sparkles(im,t,[(599,1010,17),(820,1085,22)])
 else:
  r.place(im,meal(),700,1230,.76)
  if sid in ('hook','joke'):
   v.sparkles(im,t,[(519,974,21),(904,1012,18)])
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
  if row['id']=='mix':
   for at in np.arange(.8,row['duration']-.4,1.25):
    n=int(.16*sr);tt=np.arange(n)/sr
    fx=(np.sin(2*np.pi*260*tt)*.42)*np.exp(-tt*24)*.025
    pos=int((clock+at)*sr);a[pos:pos+n]+=fx
  clock+=row['duration']
 r.wavwrite(path,a);return path
p.mix=cooking_mix
