"""Lentil soup and spinach pasta, using the established paper cooking stage."""

def eye(cv,x,y,s=1.0,mood='happy',lt=0.0):
    cv.save();cv.translate(x,y);cv.scale(s,s)
    shadow(cv,155);feet(cv,140,0xD2E6DD,gap=52)
    limb(cv,-121,25,-157,77,0xE4EFE5);limb(cv,121,25,157,77,0xE4EFE5)
    blob(cv,oval_path(0,0,285,260),0xF1F2DF,0xFFFFF2,shade=0xDDE2CE)
    blob(cv,circle_path(0,-25,76),0x7DB6B0,0xB4DAD0,shade=0x5C8D91,ow=5)
    cv.drawCircle(0,-25,43,P(INK));cv.drawCircle(-18,-46,17,P(WHITE));cv.drawCircle(21,-9,8,P(WHITE))
    for xx in [-91,91]:cv.drawOval(skia.Rect.MakeXYWH(xx-14,53,28,14),P(0xECAFA6))
    mouth=skia.Path();mouth.moveTo(-22,69);mouth.quadTo(0,94,22,69);cv.drawPath(mouth,P(INK,'stroke',5))
    if mood=='shock':cv.drawOval(skia.Rect.MakeXYWH(-11,67,22,29),P(INK))
    cv.restore()

r.ch.eye=eye
if NUM==9:
    src=src.replace("    if name=='heart':", "    if name=='gut':\n        start=src.index('    fl = ')\n        stop=src.index('    cv.restore()',start)\n        src=src[:start]+src[stop:]\n    if name=='heart':")
    exec(src,r.__dict__)
color=0xABD7C3 if NUM==9 else 0xB7D9DB
v.SPEAKER={chef:(chef,color),narrator:(L('해설','Narrator'),0x9ACDB4)}
original_asset910=asset

@functools.lru_cache(None)
def asset(kind):
    if kind not in ('lentil','onion','pasta','spinach','garlic'):return original_asset910(kind)
    im=Image.new('RGBA',(240,240));d=ImageDraw.Draw(im)
    if kind=='lentil':
        d.ellipse((15,67,226,213),fill='#A9C6B7',outline='#435970',width=4);d.ellipse((15,52,226,165),fill='#F1D9AD')
        for j in range(37):
            a=j*2.399;rr=math.sqrt(j/37);x=120+rr*91*math.cos(a);y=108+rr*43*math.sin(a);d.ellipse((x-8,y-5,x+8,y+5),fill=['#A99365','#B49C70','#8A9270'][j%3])
    elif kind=='onion':
        d.ellipse((35,55,210,218),fill='#DDC99D',outline='#435970',width=4);d.polygon([(87,68),(111,15),(133,17),(157,71)],fill='#C4AF7D')
        for x in [85,115,145]:d.arc((x-15,67,x+40,206),70,275,fill='#B9A57C',width=3)
    elif kind=='pasta':
        for j in range(15):d.line((42+j*9,21+(j%3)*4,38+j*9,219-(j%3)*5),fill='#C9AB6C',width=7)
        for j in range(15):d.line((40+j*9,21+(j%3)*4,36+j*9,218-(j%3)*5),fill='#EBCB84',width=4)
    elif kind=='spinach':
        for j in range(6):
            x=35+j*25;y=80+(j%2)*35;d.ellipse((x,y-40,x+65,y+50),fill=['#86AC77','#6E9870','#A7BC7E'][j%3],outline='#597969',width=3);d.line((x+30,y-15,122,211),fill='#92AD76',width=5)
    else:
        for x in [55,100,143]:d.ellipse((x,65,x+55,194),fill='#FFF2CC',outline='#B0A183',width=3)
        d.polygon([(95,75),(119,26),(143,76)],fill='#E2D6B0')
    return r.paperize(im,901+len(kind))

@functools.lru_cache(maxsize=16)
def meal910(stage='done'):
    im=Image.new('RGBA',(900,620));d=ImageDraw.Draw(im)
    if NUM==9:
        if stage in ('onion','simmer'):
            d.rounded_rectangle((77,225,830,505),45,fill='#AAC4B7',outline='#47616B',width=7)
            d.rounded_rectangle((13,260,111,321),21,fill='#B99B76');d.rounded_rectangle((790,260,888,321),21,fill='#B99B76')
        else:d.pieslice((105,125,795,590),0,180,fill='#B3CEC1',outline='#47616B',width=7)
        d.ellipse((88,120,813,460),fill='#FDF2D9',outline='#597277',width=7)
        d.ellipse((119,145,782,427),fill='#C2AC79' if stage!='onion' else '#4B6266')
        count=70 if stage!='onion' else 0
        for j in range(count):
            a=j*2.399;rr=math.sqrt(j/count);x=450+rr*300*math.cos(a);y=287+rr*120*math.sin(a);d.ellipse((x-11,y-7,x+11,y+7),fill=['#8E8E66','#A89665','#B29C68'][j%3],outline='#8A805B',width=2)
        for j in range(23):
            x=210+(j*127)%490;y=209+(j*59)%160;d.rounded_rectangle((x,y,x+22,y+15),3,fill='#F1E5BB')
    else:
        if stage in ('garlic','toss'):
            d.rounded_rectangle((690,265,899,309),18,fill='#BA9A70');d.ellipse((57,127,823,524),fill='#6E8583');d.ellipse((75,137,805,499),fill='#344C55')
        else:d.ellipse((60,114,835,537),fill='#B2CBC1',outline='#536C77',width=6);d.ellipse((88,135,806,509),fill='#FFF6DF')
        if stage=='garlic':
            for j in range(16):
                x=250+(j*83)%380;y=237+(j*41)%130;d.ellipse((x,y,x+30,y+15),fill='#E6D3A2')
        else:
            for j in range(34):
                x=200+(j*53)%380;y=210+(j*37)%160
                d.arc((x-80,y-60,x+135,y+56),(j*41)%180,(j*41)%180+235,fill='#D0AF69',width=10)
                d.arc((x-78,y-64,x+133,y+50),(j*41)%180,(j*41)%180+235,fill='#EAD18E',width=6)
            for j in range(25):
                x=231+(j*89)%405;y=225+(j*47)%160;d.ellipse((x,y,x+47,y+23),fill=['#719574','#8EA972','#A6B982'][j%3])
            for j in range(9):
                x=290+(j*77)%300;y=245+(j*39)%100;d.ellipse((x,y,x+23,y+11),fill='#E5D2A0')
    return r.paperize(im,910+len(stage))

def evidence910(im,detail):
    r.rounded(im,(80,690,1000,1250),'#FFFCF3',38,10)
    for i,line in enumerate(C['nutrition_'+LANG][int(detail)]):
        line=line.replace('μg','mcg').replace('→',L(' / ',' → '))
        r.label(im,line,(540,765+i*99),60 if i==1 else 44 if i<4 else 42,fill='#638B77' if i==1 else v.INK,maxw=850)
    r.place(im,r.chef(C['character'],'proud'),220,1370,.4);r.place(im,meal910(),743,1385,.44)

def steam910(im,t,x=650,y=990):
    d=ImageDraw.Draw(im)
    for j in range(3):
        yy=y-((t*.26+j/3)%1)*110;d.arc((x+j*65,yy,x+34+j*65,yy+75),70,265,fill=(250,253,246,170),width=6)

def content(idx,t):
    sid=p.ROWS[idx][0];im=Image.new('RGBA',(1080,1920));d=ImageDraw.Draw(im)
    if sid=='end':recipe(im);return im
    if sid in ('benefit','context'):evidence910(im,sid=='context');return im
    if sid=='ingredients':
        r.rounded(im,(95,700,985,1280),'#FFFCF3',42,9)
        for j,(ko,en,ak,ae,kind) in enumerate(C['ingredients']):
            y=790+j*125;r.place(im,asset(kind),180,y,.34 if kind!='oil' else .17)
            r.label(im,L(ko,en),(285,y),48,anchor='lm',maxw=405);r.label(im,L(ak,ae),(930,y),43,anchor='rm',maxw=230)
        r.place(im,r.chef(C['character'],'sparkle'),230,1390,.43);return im
    r.place(im,r.chef(C['character'],'shock' if sid=='joke' and t>2 else 'serious' if sid in ('prep','cook') else 'sparkle'),225,1130,.72,angle=math.sin(t*2)*1.3)
    if sid=='prep':
        if NUM==9:
            r.rounded(im,(409,1080,1015,1390),'#D5B488',32,7);r.place(im,asset('onion'),535,1200,.57)
            for j in range(17):
                x=684+(j*39)%240;y=1200+(j*29)%140;d.rounded_rectangle((x,y,x+16,y+12),3,fill='#ECE1BA')
            r.place(im,r.prop('knife'),725,1090+22*math.cos(t*8),.48,angle=-8)
            r.label(im,L('양파는 잘게 · 콩은 미리 익혀요','Chop finely / lentils must be precooked'),(675,820),46,maxw=700)
        else:
            # Pasta bends into boiling water rather than appearing already plated.
            d.rounded_rectangle((425,1160,840,1420),45,fill='#AFC6BA',outline='#526C74',width=6);d.ellipse((422,1100,842,1260),fill='#D9E4D8',outline='#526C74',width=6)
            r.place(im,asset('pasta'),645,1050+65*v.smooth(t/2),.7,angle=8)
            r.place(im,asset('spinach'),935,1295,.48);steam910(im,t,530,1100)
            r.label(im,L('포장대로 익혀요 / 시금치는 물 빼고 계량','Follow packages / drain spinach, then measure'),(650,822),44,maxw=760)
    elif sid=='mix':
        r.place(im,meal910('onion' if NUM==9 else 'garlic'),700,1245,.73)
        if NUM==9:arm_tool(im,665+65*math.sin(t*2.5),1240+13*math.cos(t*2.5))
        else:
            r.place(im,asset('garlic'),895,1040,.3)
            arm_tool(im,665+55*math.sin(t*2.2),1250+15*math.cos(t*2.2),'spatula')
        r.label(im,L('중약불 · 약 3분','Medium-low / about 3 minutes') if NUM==9 else L('약불 · 약 30초 / 마늘 태우지 않기','Low heat / about 30 sec / do not burn'),(680,825),46,maxw=710)
    elif sid=='cook':
        r.rounded(im,(405,1380,1010,1465),'#D6D8CB',26,6)
        r.place(im,meal910('simmer' if NUM==9 else 'toss'),700,1250-(0 if NUM==9 else 8*math.sin(t*2)),.73)
        if NUM==9:
            if t<1.8:
                r.place(im,asset('lentil'),760,1000,.4,angle=-30)
                for j in range(7):
                    yy=1090+(t*110+j*20)%140;d.ellipse((700+j*9,yy,711+j*9,yy+7),fill='#A59465')
            else:arm_tool(im,660+65*math.sin(t*2.4),1245+13*math.cos(t*2.4))
            r.label(im,L('끓으면 약불 · 약 7분','Once boiling / simmer about 7 minutes'),(680,825),46,maxw=710)
        else:
            arm_tool(im,665+75*math.sin(t*2.4),1240+15*math.cos(t*2.4),'spatula')
            r.label(im,L('중약불 · 약 1분 / 면수 조금','Medium-low / about 1 minute / pasta water'),(675,825),45,maxw=730)
        steam910(im,t)
    else:
        if NUM==9 and sid=='serve':
            r.place(im,meal910(),550,1250,.46);r.place(im,meal910(),850,1260,.46)
            r.label(im,L('두 그릇에 나눠요','Divide into two bowls'),(690,835),49,maxw=690)
        else:r.place(im,meal910(),700,1245,.73)
        if sid=='hook':v.sparkles(im,t,[(495,930,24),(945,1030,22)])
        if sid=='joke' and t>2:v.bang(im,430,890,t)
    return im
p.content=content
base_frame910=p.frame
@functools.lru_cache(maxsize=3)
def fixed_frame910(idx):return base_frame910(idx,1.0)
def frame910(idx,t):
    if idx in (6,7,9) and t>=.85:return fixed_frame910(idx)
    return base_frame910(idx,t)
p.frame=frame910

def mix910():
    path=v.prepare_mix(p.rows());sr=24000
    with wave.open(str(path)) as f:a=np.frombuffer(f.readframes(f.getnframes()),np.int16).astype(np.float32)/32768
    from scipy.signal import butter,sosfilt
    rng=np.random.default_rng(NUM);clock=0
    for row in p.rows():
        cuts=row['id']=='prep' and NUM==9
        if cuts or row['id'] in ('mix','cook'):
            for at in np.arange(.8,row['duration']-.4,math.pi/4 if cuts else math.pi):
                n=int((.1 if cuts else .25)*sr);tt=np.arange(n)/sr;fx=sosfilt(butter(2,1600,fs=sr,output='sos'),rng.normal(0,1,n))*np.exp(-tt*(40 if cuts else 12));fx*=.048/max(np.max(abs(fx)),.001);pos=int((clock+at)*sr);a[pos:pos+n]+=fx
            if row['id']=='cook':
                n=int((row['duration']-.6)*sr);tt=np.arange(n)/sr;fx=sosfilt(butter(2,[650,3300],btype='bandpass',fs=sr,output='sos'),rng.normal(0,1,n))*np.sin(np.pi*tt/(n/sr))**.5;fx*=.003/max(np.sqrt(np.mean(fx*fx)),.001);pos=int((clock+.3)*sr);a[pos:pos+n]+=fx
        clock+=row['duration']
    r.wavwrite(path,a);return path
p.mix=mix910
