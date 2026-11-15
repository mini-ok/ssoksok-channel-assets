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
    for i in range(3):
        offset=i*11*k
        points=[(x-57*k,y+17*k+offset),(x-28*k,y-22*k+offset),(x+1*k,y-17*k+offset),(x+34*k,y-28*k+offset),(x+61*k,y-4*k+offset),(x+22*k,y+11*k+offset),(x-14*k,y+5*k+offset),(x-42*k,y+30*k+offset)]
        d.polygon(points,fill=['#EA8A44','#F3A156','#DC7440'][i],outline='#AE623E',width=3)
        d.line(points[:5],fill='#FFD18B',width=3)

@functools.lru_cache(None)
def asset(kind):
    im=Image.new('RGBA',(240,240))
    d=ImageDraw.Draw(im)
    if kind=='main':
        draw_piece(d,120,107,1.55,'raw')
    elif kind in ('oil','water'):
        d.rounded_rectangle((73,65,168,207),16,fill='#A7BEA2' if kind=='oil' else '#99C4D0',outline='#5C7373',width=4)
        d.rectangle((92,41,151,75),fill='#597372')
    else:
        d.ellipse((31,80,206,186),fill='#A3BDAF',outline='#6B8271',width=4)
        d.ellipse((43,80,195,145),fill='#EFE0BC')
    return r.paperize(im,NUM*21+len(kind))

@functools.lru_cache(None)
def dish(stage):
    im=Image.new('RGBA',(900,620))
    d=ImageDraw.Draw(im)
    if stage=='mix':
        d.rounded_rectangle((679,259,882,323),19,fill='#587669')
    d.ellipse((89,111,814,536),fill='#98BDB7',outline='#597C74',width=8)
    d.ellipse((124,143,780,488),fill='#ECD4A5' if stage in ('mix','cook') else '#FFF0D1')
    if stage=='mix':
        for i in range(12):
            x=281+(i*61)%312
            y=210+(i*31)%180
            d.ellipse((x,y,x+15,y+8),fill='#B58E65')
    else:
        for x,y in [(288,227),(505,221),(612,315),(348,340),(501,389)]:
            draw_piece(d,x,y,1.42,stage)
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
  r.rounded(im,(414,1031,994,1421),'#D5B58B',31,7)
  r.place(im,dish('raw'),702,1241,.66)
  x=806+28*math.sin(t*3)
  d.rounded_rectangle((x,1042,x+21,1134),8,fill='#507C73')
  d.rectangle((x-18,1123,x+38,1143),fill='#A3B5A9',outline='#516E65',width=3)
 elif sid=='mix':
  r.place(im,dish('mix'),701,1244,.73)
  arm_tool(im,686+46*math.sin(t*3),1181+14*math.cos(t*3))
 elif sid=='cook':
  r.place(im,dish('cook'),701,1244,.74)
  r.place(im,asset('oil'),852,1023,.34,angle=-31)
  for i in range(5):
   y=1081+(int(t*74)+i*22)%105
   d.ellipse((780+i*8,y,786+i*8,y+8),fill='#D4B374')
 else:
  r.place(im,dish('done'),704,1237,.75)
  if sid in ('serve','joke'):v.sparkles(im,t,[(526,973,19),(912,1024,20)])
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
