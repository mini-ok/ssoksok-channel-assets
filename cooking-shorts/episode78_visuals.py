"""Paper assets, cooking actions and quantified evidence cards for episodes 7/8.
Executed in the shared production renderer's namespace.
"""

def bone(cv,x,y,s=1.0,mood='happy',lt=0.0):
    cv.save();cv.translate(x,y);cv.scale(s,s)
    shadow(cv,160);feet(cv,145,0xE5D9BE,gap=50)
    limb(cv,-80,25,-140,77,0xF6EBD5);limb(cv,80,25,140,77,0xF6EBD5)
    shape=union(oval_path(0,20,155,265),circle_path(-55,-90,62),circle_path(55,-90,62),circle_path(-48,118,47),circle_path(48,118,47))
    blob(cv,shape,0xEFE4CC,0xFFF9EC,shade=0xD7C5A1)
    face(cv,0,-10,.91,mood,blush=0xEBAFAA)
    cv.restore()

r.ch.bone=bone
# Keep the exact established brain character; bone is a new paper character.
color=0xE6CBA7 if NUM==7 else 0xE2DAC2
v.SPEAKER={chef:(chef,color),narrator:(L('해설','Narrator'),0x9ACDB4)}
old_asset=asset

@functools.lru_cache(None)
def asset(kind):
    if kind not in ['salmon','pepper','yogurt','strawberry']:return old_asset(kind)
    im=Image.new('RGBA',(240,240));d=ImageDraw.Draw(im)
    if kind=='salmon':
        d.rounded_rectangle((25,65,218,178),34,fill='#849795',outline='#344765',width=4)
        d.rounded_rectangle((25,45,218,154),30,fill='#E59A85',outline='#344765',width=4)
        for x in range(48,200,30):d.line((x,53,x+24,95,x,146),fill='#F8D9B7',width=7)
    elif kind=='pepper':
        d.ellipse((43,58,133,213),fill='#D9775C',outline='#344765',width=4);d.ellipse((90,51,192,214),fill='#E89B65',outline='#344765',width=4)
        d.line((116,70,123,25,154,20),fill='#71916F',width=17)
    elif kind=='yogurt':
        d.polygon([(40,67),(204,67),(182,215),(65,215)],fill='#C1D9CF',outline='#344765',width=4)
        d.ellipse((39,44,205,93),fill='#FFFAEC',outline='#344765',width=4)
        r.label(im,L('무가당','Plain'),(123,139),35,maxw=133)
    else:
        d.polygon([(45,83),(190,83),(150,194),(116,219),(83,185)],fill='#D48078',outline='#344765',width=4)
        d.ellipse((42,48,195,134),fill='#EFA49A',outline='#344765',width=4)
        for x,y in [(80,93),(125,89),(158,102),(103,137),(145,142),(121,180)]:d.ellipse((x,y,x+6,y+10),fill='#FFF0C9')
        d.polygon([(72,66),(94,39),(119,58),(145,36),(162,68),(122,88)],fill='#739576')
    return r.paperize(im,NUM*100+len(kind))

@functools.lru_cache(maxsize=24)
def dish78(stage='done'):
    im=Image.new('RGBA',(900,620));d=ImageDraw.Draw(im)
    d.rounded_rectangle((45,85,855,530),42,fill='#A8BDB8',outline='#435D67',width=8)
    d.rounded_rectangle((66,103,834,508),33,fill='#EFE7D4')
    if NUM==7:
        for j in range(10):
            x=135+(j*113)%610;y=165+(j*63)%250
            d.rounded_rectangle((x,y,x+80,y+25),12,fill=['#E7AD67','#C4775B','#B6A36F'][j%3])
        fish=asset('salmon').resize((440,360));r.place(im,fish,453,296,1.0)
        if stage in ['done','serve','joke']:
            for x,y in [(300,235),(420,290),(530,230)]:d.ellipse((x,y,x+32,y+15),fill='#C88B66')
    else:
        d.rounded_rectangle((107,146,791,471),24,fill='#FFF9EA',outline='#E1D4B9',width=5)
        if stage!='plain':
            for j in range(10):
                x=190+(j*117)%530;y=216+(j*61)%195
                # Thin strawberry cross-sections embedded in the yogurt.
                d.ellipse((x-33,y-29,x+33,y+29),fill='#D98D87',outline='#C37978',width=3)
                d.ellipse((x-22,y-19,x+22,y+19),fill='#F3C7AF')
                for dx,dy in [(-12,-5),(10,0),(0,11)]:d.ellipse((x+dx,y+dy,x+dx+4,y+dy+5),fill='#F9E3A9')
        if stage in ['done','serve','joke']:
            for pts in [[(335,148),(360,276),(300,352),(340,472)],[(545,148),(510,310),(575,472)],[(110,310),(300,352),(510,310),(790,340)]]:d.line(pts,fill='#A8BDB8',width=12)
    return r.paperize(im,781+NUM)

def nutrition78(im,detail=False):
    box=(80,690,1000,1250);r.rounded(im,box,'#FFFCF3',38,10)
    if NUM==7:
        lines=([L('연어 150g · 조리 전 재료 기준','150 g salmon · before cooking'),L('DHA 약 1,000mg','About 1,000 mg DHA'),L('뇌세포막의 구성 성분','A component of brain cell membranes'),L('양식 대서양연어 기준 추정','Estimate for farmed Atlantic salmon'),L('출처: 노르웨이 식품성분표 · NIH ODS','Sources: Norwegian Food Table / NIH ODS')] if not detail else [L('DHA 약 1,000mg · 생연어 150g','About 1,000 mg DHA / 150 g raw salmon'),L('DHA 단독 일일 권장량','Daily requirement for DHA alone'),L('미국 기준 미설정','Not established in the U.S.'),L('어종·사료·조리에 따라 함량 차이','Varies with fish, feed, and cooking'),L('출처: 노르웨이 식품성분표 · NIH ODS','Sources: Norwegian Food Table / NIH ODS')])
    else:
        lines=([L('요거트 200g + 딸기 80g · 전체 분량','Yogurt 200 g + strawberries 80 g / full recipe'),L('칼슘 약 380mg','About 380 mg calcium'),L('두 번 나눠 먹는 간식이에요','Makes two snack servings'),L('저지방 일반 요거트 기준 추정','Estimate using plain low-fat yogurt'),L('출처: NIH ODS · 노르웨이 식품성분표','Sources: NIH ODS / Norwegian Food Table')] if not detail else [L('반씩 먹으면 칼슘 약 190mg','Half the recipe: about 190 mg calcium'),L('하루 권장량의 약 19%','About 19% of the daily requirement'),L('미국 19~50세 성인 · 하루 1,000mg 기준','U.S. adults 19–50 / 1,000 mg per day'),L('저지방 일반 요거트 기준 · 제품별 차이','Plain low-fat yogurt / products vary'),L('출처: NIH ODS · 노르웨이 식품성분표','Sources: NIH ODS / Norwegian Food Table')])
    for i,line in enumerate(lines):
        size=63 if i==1 else 46 if i!=4 else 42
        r.label(im,line,(540,765+i*99),size,fill='#638B77' if i==1 else v.INK,maxw=855)
    r.place(im,r.chef(C['character'],'proud'),225,1372,.40);r.place(im,dish78(),740,1384,.43)

def oven78(im,t,freezer=False):
    d=ImageDraw.Draw(im);x0,y0,x1,y1=425,880,1000,1425
    d.rounded_rectangle((x0,y0,x1,y1),32,fill='#B5D3E0' if freezer else '#B5C8C2',outline='#455D6A',width=7)
    d.rounded_rectangle((455,960,970,1365),18,fill='#4B6267',outline='#F5EBD3',width=9)
    if not freezer:
        for x in [490,560,630]:d.ellipse((x,902,x+28,930),fill='#FFFAE6',outline='#647F7E',width=3)
    else:
        # Snowflake and upright handle distinguish the freezer from the oven.
        for angle in [0,math.pi/3,2*math.pi/3]:
            dx=25*math.cos(angle);dy=25*math.sin(angle);d.line((517-dx,922-dy,517+dx,922+dy),fill='#F6FCFF',width=6)
        for x,y in [(505,1020),(918,1303)]:
            for angle in [0,math.pi/3,2*math.pi/3]:
                dx=16*math.cos(angle);dy=16*math.sin(angle);d.line((x-dx,y-dy,x+dx,y+dy),fill='#C2E6EE',width=4)
    d.rounded_rectangle((754,900,950,940),8,fill='#F8F1DC')
    r.label(im,L('냉동실','FREEZER') if freezer else '200°C',(850,921),26,maxw=180)
    slide=v.smooth((t-.7)/1.4);r.place(im,dish78('raw' if NUM==7 else 'freeze'),710,1190,.55)
    # Translucent glass door closes slowly, with visible food remaining behind it.
    glass=Image.new('RGBA',(520,415));dg=ImageDraw.Draw(glass);dg.rounded_rectangle((0,0,519,414),15,fill=(170,206,211,85),outline='#DEEBE4',width=8)
    dg.rounded_rectangle((467,90,491,290) if freezer else (60,18,460,42),11,fill='#E3D8BB')
    glass=glass.resize((520,max(2,int(415*slide))));r.place(im,glass,713,968+glass.height/2,1)
    r.label(im,L('3~4시간 이상 · 단단해질 때까지','3–4+ hours / until firm') if freezer else L('200°C · 약 15~20분','200°C / 392°F · about 15–20 min'),(700,808),46,maxw=635)

def content(idx,t):
    sid=p.ROWS[idx][0];im=Image.new('RGBA',(1080,1920));d=ImageDraw.Draw(im)
    if sid=='end':recipe(im);return im
    if sid in ('benefit','context'):nutrition78(im,sid=='context');return im
    if sid=='ingredients':
        r.rounded(im,(95,700,985,1235),'#FFFCF3',42,9)
        for j,(ko,en,ak,ae,kind) in enumerate(C['ingredients']):
            y=790+j*140;r.place(im,asset(kind),180,y,.37 if kind!='oil' else .18)
            r.label(im,L(ko,en),(285,y),49,anchor='lm',maxw=410);r.label(im,L(ak,ae),(925,y),44,anchor='rm',maxw=220)
        r.place(im,r.chef(C['character'],'sparkle'),235,1380,.46);return im
    mood='shock' if sid=='joke' and t>2 else 'serious' if sid in ('prep','cook') else 'sparkle'
    r.place(im,r.chef(C['character'],mood),225,1135,.72,angle=math.sin(t*2)*1.4)
    if sid=='prep':
        r.rounded(im,(405,1070,1010,1400),'#D7B78A',35,7)
        if NUM==7:
            r.place(im,asset('salmon'),520,1200,.6);r.place(im,asset('pepper'),780,1200,.5)
            for j in range(6):d.rounded_rectangle((820+j*21,1220,831+j*21,1330),5,fill='#D88A64')
            r.place(im,r.prop('knife'),820,1100+20*math.cos(t*8),.46,angle=-8)
        else:
            for j in range(3):r.place(im,asset('strawberry'),520+j*115,1200,.5)
            for j in range(4):d.ellipse((790+j*28,1270,825+j*28,1310),fill='#E4A299',outline='#BC7772',width=3)
            r.place(im,r.prop('knife'),780,1110+19*math.cos(t*8),.46,angle=-8)
        r.label(im,L('물기 닦고 손질하기','Dry and prepare the ingredients'),(680,840),47,maxw=680)
    elif sid=='mix':
        r.place(im,dish78('raw' if NUM==7 else 'plain'),700,1245,.72)
        if NUM==7:
            # Oil falls from a tilted bottle onto the tray.
            r.place(im,asset('oil'),740,952,.25,angle=-45)
            for j in range(3):
                y=1030+(t*70+j*35)%120;d.ellipse((702,y,712,y+17),fill='#DCC186')
        else:
            arm_tool(im,675+85*math.sin(t*2),1240+12*math.cos(t*2))
            r.label(im,L('厚さ 5~7mm','5–7 mm thick') if LANG=='en' else '두께 5~7mm',(700,844),49,maxw=640)
    elif sid=='cook':
        if NUM==8:
            food_layer=Image.new('RGBA',im.size);r.place(food_layer,dish78('freeze'),700,1250,.72)
            u=v.smooth(t/1.6);r.place(food_layer,asset('strawberry'),765,945+190*u,.29)
            cold_layer=Image.new('RGBA',im.size);oven78(cold_layer,max(0,t-2.4),True)
            im.alpha_composite(Image.blend(food_layer,cold_layer,v.smooth((t-2.4)/.85)))
        else:oven78(im,t,False)
    else:
        r.place(im,dish78('serve' if sid=='serve' else 'done'),700,1245,.72)
        if sid=='serve':
            if NUM==7:
                d.line((728,1220,800,1045),fill='#C2D4CF',width=15)
                d.rounded_rectangle((780,1015,875,1090),14,fill='#F6F1DE',outline='#718F87',width=4)
                r.label(im,'63°C',(827,1051),30,maxw=88)
                r.label(im,L('연어 중심 63°C 확인','Fish center: 63°C / 145°F'),(700,843),47,maxw=660)
            else:
                r.label(im,L('2~5분 두고 작게 나누기','Soften 2–5 min; divide into small pieces'),(675,842),44,maxw=700)
                # One small piece lifts gently, never bitten while rock-hard.
                piece=Image.new('RGBA',(160,110));dp=ImageDraw.Draw(piece);dp.polygon([(5,10),(155,4),(139,100),(20,106)],fill='#FFF6DF',outline='#D6C9AF',width=4);dp.ellipse((50,25,100,70),fill='#E29F98');r.place(im,piece,795,1100-18*math.sin(t*2),.85)
        if sid=='hook':v.sparkles(im,t,[(490,930,23),(950,1030,20)])
        if sid=='joke' and t>2:v.bang(im,430,875,t)
    return im
p.content=content

# Evidence and screenshot cards are intentionally static. Cache complete frames
# after the transition, preserving exact output while avoiding repeated typesetting.
base_frame78=p.frame
@functools.lru_cache(maxsize=3)
def fixed_frame78(idx):return base_frame78(idx,1.0)
def frame78(idx,t):
    if idx in (6,7,9) and t>=.85:return fixed_frame78(idx)
    return base_frame78(idx,t)
p.frame=frame78

def mix78():
    path=v.prepare_mix(p.rows());sr=24000
    with wave.open(str(path)) as f:a=np.frombuffer(f.readframes(f.getnframes()),np.int16).astype(np.float32)/32768
    rng=np.random.default_rng(NUM);clock=0
    from scipy.signal import butter,sosfilt
    for row in p.rows():
        events=[]
        if row['id']=='prep':events=[(float(t),.09,'chop') for t in np.arange(.8,row['duration']-.3,math.pi/4)]
        if row['id']=='mix':events=[(float(t),.25,'stir') for t in np.arange(.8,row['duration']-.5,math.pi)]
        if row['id']=='cook':events=[(1.7 if NUM==7 else 4.1,.18,'close')]
        if row['id']=='serve' and NUM==8:events=[(2.1,.1,'snap')]
        for at,length,kind in events:
            n=int(length*sr);tt=np.arange(n)/sr
            fx=sosfilt(butter(2,1500,fs=sr,output='sos'),rng.normal(0,1,n))*np.exp(-tt*(40 if kind in ['chop','snap','close'] else 10))
            fx*=.055/max(np.max(np.abs(fx)),.001);pos=int((clock+at)*sr)
            if pos+n<len(a):a[pos:pos+n]+=fx
        clock+=row['duration']
    r.wavwrite(path,a);return path
p.mix=mix78
