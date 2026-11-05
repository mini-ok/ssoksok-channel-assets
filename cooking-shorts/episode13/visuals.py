"""Dedicated bean salad and almond pear toast cooking visuals."""
@functools.lru_cache(None)
def asset(kind):
 im=Image.new('RGBA',(240,240));d=ImageDraw.Draw(im)
 if kind=='bean':
  for j in range(16):
   x=30+(j*47)%170;y=35+(j*31)%155;d.ellipse((x,y,x+32,y+19),fill='#A86B60',outline='#675E56',width=2)
 elif kind=='cucumber':
  for j in range(9):
   x=30+(j*49)%150;y=30+(j*37)%155;d.rounded_rectangle((x,y,x+43,y+31),8,fill='#A0BA86',outline='#638965',width=3)
 elif kind=='lemon':
  d.ellipse((35,55,210,192),fill='#EAD48C',outline='#B6A56D',width=4)
 elif kind=='almond':
  for j in range(12):
   x=28+(j*43)%150;y=25+(j*37)%170;d.ellipse((x,y,x+40,y+23),fill='#B78A62',outline='#775E4D',width=2)
 elif kind=='bread':
  d.rounded_rectangle((30,35,215,215),30,fill='#AD8359');d.rounded_rectangle((44,48,201,201),24,fill='#E2C79B')
 elif kind=='pear':
  d.ellipse((43,82,198,220),fill='#D2D49D');d.ellipse((77,30,165,145),fill='#D2D49D');d.line((120,40,127,10),fill='#7A7154',width=8)
 elif kind=='oil':return r.prop('oil')
 else:
  d.polygon([(50,30),(190,30),(172,220),(68,220)],fill='#B5D3D5',outline='#526B72')
 return r.paperize(im,NUM*71+len(kind))
@functools.lru_cache(maxsize=8)
def meal(stage='done'):
 im=Image.new('RGBA',(900,620));d=ImageDraw.Draw(im)
 if NUM==13:
  d.pieslice((85,120,810,570),0,180,fill='#B2CFC0',outline='#526B72',width=6);d.ellipse((85,125,810,470),fill='#F1E6CE',outline='#526B72',width=6)
  for j in range(62):
   x=170+(j*67)%540;y=190+(j*43)%205;d.ellipse((x,y,x+35,y+20),fill='#A86B60',outline='#785E54',width=2)
  if stage!='raw':
   for j in range(24):
    x=190+(j*89)%510;y=205+(j*59)%175;d.rounded_rectangle((x,y,x+25,y+18),5,fill='#A0BA86',outline='#638965',width=2)
 else:
  d.ellipse((65,110,835,555),fill='#B6D0C4');d.ellipse((90,130,810,530),fill='#F8EED9')
  d.rounded_rectangle((210,170,690,470),48,fill='#AA7C53');d.rounded_rectangle((233,190,667,446),35,fill='#DABF90')
  if stage!='raw':
   d.rounded_rectangle((248,205,652,431),30,fill='#BA9671')
   if stage=='done':
    for j in range(6):
     x=265+j*57;d.ellipse((x,220,x+83,411),fill='#ECE7C4',outline='#B4BE88',width=4)
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
 r.place(im,r.chef(C['character'],'shock' if sid=='joke' and t>2 else 'sparkle'),225,1130,.72,angle=math.sin(t*2)*1.3)
 if sid=='prep':
  if NUM==13:
   r.rounded(im,(410,1080,1015,1390),'#D5B488',32,7);r.place(im,asset('cucumber'),700,1250,.8);r.place(im,r.prop('knife'),740,1100+20*math.cos(t*8),.48,angle=-8)
  else:
   r.rounded(im,(550,940,900,1330),'#CFDAD3',30,6);d.polygon([(570,930),(880,930),(850,1170),(600,1170)],fill='#D7E2DA',outline='#526B72')
   for j in range(25):
    x=615+(j*31)%210;y=970+(j*47+int(t*60))%155;d.ellipse((x,y,x+10,y+5),fill='#B78A62')
   r.label(im,L('곱게 갈고 물을 조금씩','Grind finely / add water gradually'),(680,825),43,maxw=720)
 elif sid=='mix' and NUM==14:
  r.rounded(im,(410,1080,1015,1390),'#D5B488',32,7);r.place(im,asset('pear'),600,1210,.6);r.place(im,r.prop('knife'),755,1090+20*math.cos(t*8),.45,angle=-8)
  r.rounded(im,(650,850,980,1020),'#BDD0C9',25,5);r.place(im,asset('bread'),805,870+12*math.sin(t*2),.35)
 elif sid in ('mix','cook'):
  r.place(im,meal('mix'),700,1245,.73);arm_tool(im,665+60*math.sin(t*2.5),1240+14*math.cos(t*2.5),'spoon')
  if NUM==14:
   r.place(im,asset('pear'),860,1010,.3,angle=-15)
   for j in range(min(6,int(t*2)+1)):
    x=560+j*35;d.ellipse((x,1180,x+40,1260),fill='#ECE7C4',outline='#B4BE88',width=2)
 else:
  r.place(im,meal(),700,1245,.73)
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
def cooking_mix():
 path=v.prepare_mix(p.rows())
 with wave.open(str(path)) as f:a=np.frombuffer(f.readframes(f.getnframes()),np.int16).astype(np.float32)/32768
 clock=0;sr=24000
 for row in p.rows():
  if row['id']==('prep' if NUM==13 else 'mix'):
   for at in np.arange(.8,row['duration']-.4,math.pi/4):
    n=int(.07*sr);tt=np.arange(n)/sr;fx=np.sin(2*np.pi*780*tt)*np.exp(-tt*70)*.035;pos=int((clock+at)*sr);a[pos:pos+n]+=fx
  clock+=row['duration']
 r.wavwrite(path,a);return path
p.mix=cooking_mix
