exec("def bone(cv,x,y,s=1.0,mood='happy',lt=0.0):\n    cv.save();cv.translate(x,y);cv.scale(s,s)\n    shadow(cv,160);feet(cv,145,0xE5D9BE,gap=50)\n    limb(cv,-80,25,-140,77,0xF6EBD5);limb(cv,80,25,140,77,0xF6EBD5)\n    shape=union(oval_path(0,20,155,265),circle_path(-55,-90,62),circle_path(55,-90,62),circle_path(-48,118,47),circle_path(48,118,47))\n    blob(cv,shape,0xEFE4CC,0xFFF9EC,shade=0xD7C5A1)\n    face(cv,0,-10,.91,mood,blush=0xEBAFAA)\n    cv.restore()\n\n", r.ch.__dict__)
"""Episode-specific seed rice balls / chilled milk chia pudding."""
color=0xB6D5BB if NUM==11 else 0xD3DCE8
v.SPEAKER={chef:(chef,color),narrator:(L('해설','Narrator'),0x9ACDB4)}
@functools.lru_cache(None)
def asset(kind):
 im=Image.new('RGBA',(240,240));d=ImageDraw.Draw(im)
 if kind=='seed':
  for j in range(25):
   x=36+(j*47)%165;y=45+(j*37)%145
   d.ellipse((x,y,x+28,y+13),fill='#7B9463',outline='#4C684A',width=2)
 elif kind=='rice':
  d.pieslice((15,45,225,230),0,180,fill='#A6C8B9');d.ellipse((15,50,225,166),fill='#E1CAA0')
  for j in range(55):
   x=35+(j*31)%170;y=65+(j*23)%80;d.ellipse((x,y,x+13,y+5),fill='#C5A578')
 elif kind=='milk':
  d.polygon([(55,48),(85,17),(167,17),(194,48),(194,220),(55,220)],fill='#E7EEE5',outline='#526B72')
  d.rectangle((65,95,184,165),fill='#B4D3D8');r.label(im,L('우유','Milk'),(125,130),32,maxw=110)
 elif kind=='chia':
  d.rounded_rectangle((37,45,205,219),15,fill='#D9CDB8',outline='#526B72',width=3)
  for j in range(90):
   x=47+(j*29)%145;y=62+(j*31)%130;d.ellipse((x,y,x+4,y+6),fill='#5C5C59')
 elif kind in ('vanilla','syrup'):
  d.rounded_rectangle((73,60,171,218),14,fill='#BA986D',outline='#526B72',width=4);d.rectangle((91,21,153,61),fill='#7D8A81')
  r.label(im,'V' if kind=='vanilla' else 'M',(123,140),48,maxw=90)
 elif kind=='water':return r.prop('water') if False else original_water()
 elif kind=='oil':return r.prop('oil')
 return r.paperize(im,NUM*61+len(kind))
def original_water():
 im=Image.new('RGBA',(240,240));d=ImageDraw.Draw(im);d.polygon([(48,30),(192,30),(174,218),(66,218)],fill='#C4DDE0',outline='#526B72');d.polygon([(60,110),(180,110),(168,208),(72,208)],fill='#91C3CE');return im

@functools.lru_cache(maxsize=8)
def meal(stage='done'):
 im=Image.new('RGBA',(900,620));d=ImageDraw.Draw(im)
 if NUM==11:
  if stage in ('mix','raw'):
   d.pieslice((85,120,810,570),0,180,fill='#B2CFC0',outline='#526B72',width=6);d.ellipse((85,125,810,470),fill='#EFE2BB',outline='#526B72',width=6)
   for j in range(130):
    x=170+(j*67)%550;y=190+(j*43)%210;d.ellipse((x,y,x+18,y+7),fill='#C5AD85')
   if stage=='mix':
    for j in range(55):
     x=190+(j*89)%510;y=200+(j*59)%190;d.ellipse((x,y,x+15,y+7),fill='#748B5E')
  else:
   d.ellipse((65,160,835,535),fill='#A7CBBB',outline='#526B72',width=7);d.ellipse((90,180,810,505),fill='#F6EED9')
   for x in [300,595]:
    d.polygon([(x-115,400),(x,185),(x+120,400)],fill='#E4D2AA',outline='#8C8A70',width=6)
    for j in range(60):
     xx=x-80+(j*37)%160;yy=265+(j*29)%115
     if abs(xx-x)<(yy-190)*.5:d.ellipse((xx,yy,xx+13,yy+5),fill='#789260' if j%4==0 else '#C6AC82')
 else:
  if stage in ('raw','mix'):
   d.pieslice((95,120,805,570),0,180,fill='#B1CDCA',outline='#526B72',width=6);d.ellipse((95,125,805,465),fill='#F4EEDD',outline='#526B72',width=6)
   if stage=='mix':
    for j in range(150):
     x=170+(j*47)%550;y=185+(j*31)%220;d.ellipse((x,y,x+5,y+7),fill='#6C6A60')
  else:
   for x in [295,605]:
    d.rounded_rectangle((x-118,185,x+118,500),24,fill='#C2D8D1',outline='#526B72',width=6)
    d.rectangle((x-102,230,x+102,460),fill='#E0D8C4');d.ellipse((x-102,210,x+102,270),fill='#EAE2CF')
    for j in range(100):
     xx=x-90+(j*31)%175;yy=240+(j*43)%205;d.ellipse((xx,yy,xx+4,yy+6),fill='#6B6A61')
 return r.paperize(im,NUM*41+len(stage))

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
 r.place(im,r.chef(C['character'],'shock' if sid=='joke' and t>2 else 'sparkle'),225,1130,.72,angle=math.sin(t*2)*1.3)
 if sid=='prep' and NUM==11:
  r.rounded(im,(410,1080,1015,1390),'#D5B488',32,7);r.place(im,asset('seed'),700,1240,.8)
  r.place(im,r.prop('knife'),740,1100+20*math.cos(t*8),.48,angle=-8)
  r.label(im,L('볶은 무염 씨앗을 잘게 다져요','Finely chop roasted unsalted seeds'),(680,820),46,maxw=720)
 elif sid in ('prep','mix'):
  r.place(im,meal('raw' if sid=='prep' else 'mix'),700,1245,.73)
  if sid=='prep':
   r.place(im,asset('chia'),840,1000,.36,angle=-20)
   for j in range(8):
    yy=1080+(t*95+j*19)%145;d.ellipse((730+j*6,yy,734+j*6,yy+6),fill='#65665C')
  else:arm_tool(im,665+60*math.sin(t*2.5),1240+14*math.cos(t*2.5))
  r.label(im,L('골고루 섞어요','Mix evenly') if NUM==11 else L('5분 뒤 다시 섞어요','Rest 5 min, then stir again'),(680,825),46,maxw=710)
 elif sid=='cook' and NUM==11:
  r.place(im,meal(),700,1250,.73)
  # Clean hands press the two portions; no frying pan or flames.
  for x,angle in [(565,-18),(830,18)]:
   yy=1180+10*math.sin(t*3);d.ellipse((x-35,yy-60,x+35,yy+35),fill='#EFF1F4',outline='#526B72',width=4)
  r.label(im,L('깨끗한 손을 적셔 / 두 개로 뭉쳐요','Wet clean hands / shape two balls'),(680,820),45,maxw=720)
 elif sid=='cook':
  # A refrigerator, not a freezer or stove.
  r.rounded(im,(455,790,965,1440),'#C3D8D2',35,8);r.rounded(im,(482,828,938,1405),'#E7EEE6',20,4)
  d.line((495,1125,925,1125),fill='#8BA89F',width=8)
  r.place(im,meal(),710,1070,.43)
  r.label(im,L('냉장 4시간 이상','Refrigerate 4+ hours'),(710,1280),47,maxw=430)
 else:
  r.place(im,meal(),700,1245,.73)
  if sid=='serve':r.label(im,L('한 번에 삼키지 말고 꼭꼭 씹어요','Small bites / chew well') if NUM==11 else L('충분히 불려 두 컵으로 나눠요','Fully hydrated / two equal servings'),(675,825),44,maxw=740)
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
def quiet_mix():
 path=v.prepare_mix(p.rows())
 # Cold assembly has no frying or boiling sound.
 with wave.open(str(path)) as f:a=np.frombuffer(f.readframes(f.getnframes()),np.int16).astype(np.float32)/32768
 clock=0;sr=24000
 for row in p.rows():
  if NUM==11 and row['id']=='prep':
   for at in np.arange(.8,row['duration']-.4,math.pi/4):
    n=int(.07*sr);tt=np.arange(n)/sr;fx=np.sin(2*np.pi*780*tt)*np.exp(-tt*70)*.035;pos=int((clock+at)*sr);a[pos:pos+n]+=fx
  clock+=row['duration']
 r.wavwrite(path,a);return path
p.mix=quiet_mix
