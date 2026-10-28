"""1080x1920 paper-cut cooking animation, reusing the channel's original character engine."""
import sys, os, math, json, wave, subprocess, argparse, functools, inspect, re
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import imageio_ffmpeg

ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'runtime'))
import paper as p
import chars as ch
from episodes import EPISODES

W,H,FPS=1080,1920,24
FF=imageio_ffmpeg.get_ffmpeg_exe()
FONTS=ROOT/'runtime'/'fonts'
CACHE=ROOT/'cache'; CACHE.mkdir(exist_ok=True)
OUT=ROOT/'output'; OUT.mkdir(exist_ok=True)
NAVY='#26304F'; CREAM='#FFF9EB'; MINT='#8FCFB4'; CORAL='#E97786'; YELLOW='#F2D36B'

@functools.lru_cache(maxsize=128)
def font(size,style='jua'):
    file={'jua':'Jua-Regular.ttf','black':'BlackHanSans-Regular.ttf','en':'Geist-Bold.ttf','heavy':'Geist-Black.ttf'}[style]
    return ImageFont.truetype(str(FONTS/file),size)

@functools.lru_cache(maxsize=128)
def panel(width,height,fill,r,shadow):
    pad=shadow*3+5
    im=Image.new('RGBA',(width+2*pad,height+2*pad))
    box=(pad,pad,pad+width,pad+height)
    if shadow:
        layer=Image.new('RGBA',im.size); d=ImageDraw.Draw(layer)
        d.rounded_rectangle((box[0]+3,box[1]+shadow,box[2]+3,box[3]+shadow),r,fill=(45,37,39,35))
        im.alpha_composite(layer.filter(ImageFilter.GaussianBlur(shadow)))
    d=ImageDraw.Draw(im); d.rounded_rectangle(box,r,fill=fill)
    # Top-left paper edge, deliberately soft rather than outlined.
    d.arc((box[0]+2,box[1]+2,box[0]+2*r,box[1]+2*r),180,270,fill=(255,255,255,110),width=3)
    return im,pad

def rounded(im,box,fill,r=35,shadow=8):
    layer,pad=panel(round(box[2]-box[0]),round(box[3]-box[1]),fill,r,shadow)
    im.alpha_composite(layer,(round(box[0]-pad),round(box[1]-pad)))

def label(im,text,xy,size=50,fill=NAVY,style='jua',anchor='mm',maxw=None):
    text=text.replace('…','...').replace('·','/')
    if '→' in text: text=text.replace('→',' / ')
    d=ImageDraw.Draw(im)
    while maxw and d.textbbox((0,0),text,font=font(size,style))[2]>maxw and size>18: size-=1
    d.text(xy,text,font=font(size,style),fill=fill,anchor=anchor,stroke_width=0)

@functools.lru_cache(maxsize=512)
def chip(text,size=50,color=CREAM,style='jua',maxw=880):
    dummy=ImageDraw.Draw(Image.new('RGBA',(1,1)))
    while dummy.textbbox((0,0),text,font=font(size,style))[2]>maxw-60: size-=1
    b=dummy.textbbox((0,0),text,font=font(size,style))
    width=b[2]-b[0]+68; height=int(size*1.3)+40
    im=Image.new('RGBA',(width+30,height+30)); rounded(im,(10,5,width+10,height+5),color,r=23,shadow=5)
    label(im,text,(width/2+10,height/2+4),size,style=style)
    return im

def place(im,sp,x,y,scale=1,angle=0,opacity=1):
    if scale<0.01:return
    if scale!=1: sp=sp.resize((max(1,round(sp.width*scale)),max(1,round(sp.height*scale))),Image.Resampling.BICUBIC)
    if angle:sp=sp.rotate(angle,resample=Image.Resampling.BICUBIC,expand=True)
    if opacity!=1:
        sp=sp.copy(); sp.putalpha(sp.getchannel('A').point(lambda v:int(v*opacity)))
    im.alpha_composite(sp,(round(x-sp.width/2),round(y-sp.height/2)))

def ease(x):
    x=max(0,min(1,x));return 1-(1-x)**3

def pop(t):
    if t<=0:return 0.01
    if t>=.42:return 1
    x=t/.42-1;return 1+2.2*x**3+1.2*x**2

def chef_fn(name,mood):
    # Preserve the original silhouettes, faces and identity accessories; remove work tools.
    src=inspect.getsource(getattr(ch,name))
    if name=='liver':
        start=src.index('    cv.drawLine(215')
        stop=src.index('    feet(',start)
        src=src[:start]+src[stop:]
    if name=='heart':
        src='\n'.join(line for line in src.split('\n') if 'rrect(cv, 150, 40, 80' not in line and 'cv.drawLine(190, 40' not in line)
    src=src.replace('def '+name+'(', 'def chef_base(')
    scope=dict(vars(ch));exec(src,scope)
    base=scope['chef_base']
    def draw(cv,S):
        k=S/576; x=S/2; y=S*.62
        old=ch.FLAGS.copy();ch.FLAGS['shadow']=False
        base(cv,x,y,k,mood,0)
        ch.FLAGS.update(old)
        # A small apron leaves the face and characteristic body shape visible.
        cv.save();cv.translate(x,y);cv.scale(k,k)
        path=ch.skia.Path();path.moveTo(-52,65);path.lineTo(52,65);path.lineTo(80,124);path.quadTo(0,149,-80,124);path.close()
        cv.drawPath(path,ch.P(0xFFFAED));cv.drawPath(path,ch.P(0xDDD8CA,'stroke',2))
        cv.drawLine(-50,74,50,74,ch.P(0x89BCA9,'stroke',7))
        cv.drawCircle(0,104,10,ch.P(0xE97786 if name=='heart' else 0x4EAFA3))
        # Chef toque above the original cap / bandana.
        hx,hy=(66,-197) if name=='heart' else (42,-160)
        for dx,dy,r in [(-28,-12,28),(6,-28,34),(38,-7,27)]:cv.drawCircle(hx+dx,hy+dy,r,ch.P(0xFFFDF5))
        ch.rrect(cv,hx-37,hy+1,89,32,10,fill=0xFFFDF5,stroke=0xDED9CE,sw=2)
        cv.restore()
    return draw

@functools.lru_cache(maxsize=24)
def chef(name,mood='happy'):
    path=CACHE/f'chef_v3_{name}_{mood}.png'
    if path.exists():return Image.open(path).convert('RGBA')
    N,S=830,690
    fn=chef_fn(name,mood)
    def render(value):return p.puff_char(np.full((N,N,3),value,np.float32),fn,N/2,N/2,S,seed=19 if name=='heart' else 23)
    black=render(0);white=render(1)
    a=np.clip(1-(white-black).mean(2),0,1)
    rgb=np.divide(black,a[...,None],out=np.zeros_like(black),where=a[...,None]>.001)
    arr=(np.concatenate([np.clip(rgb,0,1),a[...,None]],2)*255).astype('uint8')
    im=Image.fromarray(arr); im.save(path);return im

def paperize(im,seed=3):
    arr=np.asarray(im).astype(np.float32); a=arr[:,:,3]/255
    from scipy.ndimage import gaussian_filter
    h=gaussian_filter(a,3);gy,gx=np.gradient(h)
    shade=np.clip(1.0-0.5*gx-0.7*gy,.82,1.17)
    noise=np.random.default_rng(seed).normal(0,.009,a.shape)
    arr[:,:,:3]=np.clip(arr[:,:,:3]*(shade+noise)[:,:,None],0,255)
    obj=Image.fromarray(arr.astype('uint8'))
    sh=Image.new('RGBA',im.size,(30,29,28,0));sh.putalpha(im.getchannel('A').filter(ImageFilter.GaussianBlur(5)).point(lambda x:int(x*.22)))
    result=Image.new('RGBA',im.size);result.alpha_composite(sh,(3,6));result.alpha_composite(obj)
    return result

@functools.lru_cache(maxsize=100)
def prop(kind):
    im=Image.new('RGBA',(700,600));d=ImageDraw.Draw(im)
    if kind=='banana':
        d.arc((80,-70,650,490),20,164,fill='#E8BB47',width=107)
        d.arc((102,-101,629,449),24,160,fill='#F6D772',width=66)
        d.line((100,221,78,187),fill='#8B6A41',width=20)
        d.ellipse((583,183,614,211),fill='#8B6A41')
    elif kind=='banana_slice':
        d.ellipse((200,150,490,440),fill='#ECD08A');d.ellipse((216,165,475,425),fill='#FFF0BF')
        for a in range(3):
            th=a*2*math.pi/3; x=345+44*math.cos(th);y=298+44*math.sin(th)
            d.line((345,298,x,y),fill='#CCAE75',width=13)
    elif kind=='tomato':
        d.ellipse((160,125,540,485),fill='#E87965');d.ellipse((195,145,470,415),fill='#F4997A')
        pts=[(350,145),(310,195),(343,180),(365,210),(377,172),(420,162),(380,149),(387,109),(362,137)]
        d.polygon(pts,fill='#639B6B')
    elif kind=='tomato_cube':
        d.rounded_rectangle((230,190,460,420),40,fill='#ED806A');d.rounded_rectangle((251,208,432,380),35,fill='#FAAA8D')
        for x,y in [(290,265),(380,315)]:d.ellipse((x,y,x+17,y+26),fill='#F6D59A')
    elif kind=='cucumber':
        d.rounded_rectangle((80,195,610,390),95,fill='#72A57A');d.rounded_rectangle((95,205,580,330),60,fill='#97C68C')
        for x in range(150,550,65):d.line((x,220,x-24,335),fill='#649968',width=6)
    elif kind=='cucumber_slice':
        d.ellipse((210,145,490,435),fill='#68A375');d.ellipse((233,168,467,412),fill='#D3E7B0')
        for dx,dy in [(-35,0),(35,0),(0,38),(0,-38)]:d.ellipse((339+dx,278+dy,358+dx,309+dy),fill='#A5C28A')
    elif kind=='bean':
        d.ellipse((226,163,476,413),fill='#D7B77A');d.ellipse((233,162,450,386),fill='#EFD69E')
        d.arc((313,219,409,320),70,240,fill='#C5A474',width=14)
    elif kind=='lemon':
        d.ellipse((150,160,550,440),fill='#EFCB62');d.ellipse((176,184,524,414),fill='#FFF1B4')
        for a in range(7):
            th=a*2*math.pi/7;d.line((350,300,350+160*math.cos(th),300+100*math.sin(th)),fill='#FFF9DC',width=13)
    elif kind=='oil':
        d.rounded_rectangle((230,170,470,490),40,fill='#A7B99A');d.rounded_rectangle((267,85,432,205),16,fill='#7F977A')
        d.rectangle((240,300,460,460),fill='#D5CA75');d.rounded_rectangle((254,247,445,360),15,fill='#FAF0D9')
        d.ellipse((320,271,377,332),fill='#71966A')
    elif kind=='knife':
        d.rounded_rectangle((75,234,265,309),26,fill='#B58E72')
        d.polygon([(251,236),(601,236),(555,325),(251,309)],fill='#D7E2E3')
        d.line((260,246,579,246),fill='#F8FEFE',width=13)
    elif kind=='spoon':
        d.rounded_rectangle((322,160,360,530),19,fill='#BA9877');d.ellipse((278,49,407,229),fill='#D9B68E')
        d.ellipse((295,66,392,200),fill='#CDA87F')
    elif kind=='sponge':
        d.rounded_rectangle((130,210,570,370),38,fill='#E5CB77');d.rounded_rectangle((130,200,570,260),20,fill='#6CA18B')
    return paperize(im,8)

@functools.lru_cache(maxsize=24)
def dish(topic,state='done'):
    im=Image.new('RGBA',(900,650)); d=ImageDraw.Draw(im)
    d.ellipse((90,420,810,570),fill=(65,56,40,30))
    d.pieslice((90,120,810,600),0,180,fill='#B5D4CE' if topic=='liver' else '#E5C4B2')
    d.ellipse((85,135,815,485),fill='#FFFCF1')
    d.ellipse((125,160,775,453),fill='#EBD6AE' if topic=='heart' else '#E4EBD4')
    rng=np.random.default_rng(29)
    for i in range(100 if topic=='heart' else 42):
        x=rng.uniform(150,750);y=rng.uniform(180,430)
        if ((x-450)/295)**2+((y-305)/115)**2>1:continue
        if topic=='heart':
            d.ellipse((x-9,y-5,x+11,y+5),fill=rng.choice(['#D9BD8A','#F7E6C7','#DFC59A']))
        else:
            k=['bean','bean','tomato_cube','cucumber_slice'][i%4]
            place(im,prop(k),x,y,.17 if k=='bean' else .2,angle=float(rng.uniform(-90,90)))
    if topic=='heart' and state=='done':
        for i in range(5):place(im,prop('banana_slice'),260+i*92,280+16*math.sin(i),.27,angle=i*6-20)
    return paperize(im,13)

@functools.lru_cache(maxsize=1)
def pan():
    im=Image.new('RGBA',(700,500));d=ImageDraw.Draw(im)
    d.rounded_rectangle((20,200,680,275),30,fill='#8A9C98')
    d.rounded_rectangle((108,168,595,414),70,fill='#B0C6C2')
    d.rounded_rectangle((133,189,567,369),52,fill='#C9DAD3')
    d.ellipse((105,98,595,255),fill='#7E9690');d.ellipse((126,111,574,238),fill='#EADABD')
    return paperize(im)

@functools.lru_cache(maxsize=4)
def background(topic):
    ep=EPISODES[topic];base=np.array(Image.new('RGB',(W,H),ep['bg'])).astype(np.float32)
    from scipy.ndimage import gaussian_filter
    rng=np.random.default_rng(8)
    n=gaussian_filter(rng.normal(0,1,(H,W)),2);n/=n.std()
    grad=np.linspace(4,-6,H)[:,None,None]
    base=np.clip(base+grad+n[:,:,None]*1.2,0,255).astype('uint8')
    im=Image.fromarray(base).convert('RGBA');d=ImageDraw.Draw(im)
    # The organs' office has a tiny pantry: quiet, useful details without visual clutter.
    for x in [80,790]:
        rounded(im,(x,440,x+200,700),'#E6DDCB' if topic=='heart' else '#D6E0CC',r=26,shadow=5)
        d=ImageDraw.Draw(im);d.line((x+100,455,x+100,678),fill='#CBC7B6',width=3)
        d.ellipse((x+80,560,x+91,571),fill='#AFAC9D');d.ellipse((x+111,560,x+122,571),fill='#AFAC9D')
    d.line((100,735,980,735),fill='#D3CCBB',width=13)
    for x in range(125,1000,125):d.line((x,775,x,1240),fill=(210,205,188,90),width=2)
    for y in range(825,1250,115):d.line((40,y,1040,y),fill=(210,205,188,90),width=2)
    rounded(im,(32,1235,1048,1390),'#D6B28B',r=30,shadow=8)
    d=ImageDraw.Draw(im);d.line((67,1250,1010,1250),fill='#F1D2AB',width=9)
    return im

def steam(im,t,x=690,y=1000):
    d=ImageDraw.Draw(im)
    for i in range(3):
        pts=[]
        for k in range(18):pts.append((x+(i-1)*57+math.sin(t*2+k*.3+i)*14,y-k*7-20*math.sin(t+i)))
        d.line(pts,fill=(255,253,239,180),width=9)

def arm(im,start,end,color):
    d=ImageDraw.Draw(im);d.line([start,end],fill='#BAA38F',width=35)
    d.line([start,end],fill=color,width=29)
    d.ellipse((start[0]-14,start[1]-14,start[0]+14,start[1]+14),fill=color)
    x,y=end;d.ellipse((x-25,y-25,x+25,y+25),fill='#FFF9ED',outline='#D9CDBB',width=3)

@functools.lru_cache(maxsize=64)
def subtitle_sprite(text,lang):
    im=Image.new('RGBA',(W,H))
    maxw=850;size=49 if lang=='ko' else 46;style='jua' if lang=='ko' else 'en'
    d=ImageDraw.Draw(im);lines=[]
    units=text.split(' ')
    line=''
    for unit in units:
        candidate=line+(' ' if line else '')+unit
        if d.textlength(candidate,font=font(size,style))>maxw and line:
            lines.append(line.strip());line=unit
        else:line=candidate
    if line:lines.append(line.strip())
    if len(lines)==2:
        # Balance two lines at a word boundary; never strand one Korean syllable or punctuation.
        options=[]
        for k in range(1,len(units)):
            a,b=' '.join(units[:k]),' '.join(units[k:])
            wa=d.textlength(a,font=font(size,style));wb=d.textlength(b,font=font(size,style))
            if max(wa,wb)<=maxw:options.append((abs(wa-wb),[a,b]))
        if options:lines=min(options,key=lambda x:x[0])[1]
    if len(lines)>2:
        size=43 if lang=='ko' else 39
        # Last scene has the longest CTA; 3 readable lines still fit the reserved area.
    height=48+len(lines)*(size+15)
    rounded(im,(65,1452,1015,1452+height),'#FFFCF2',r=30,shadow=4)
    for i,line in enumerate(lines):label(im,line,(540,1484+size/2+i*(size+15)),size,style=style,maxw=880)
    box=im.getbbox()
    return im.crop(box),box[:2]

def subtitles(im,text,lang):
    sp,xy=subtitle_sprite(text,lang);im.alpha_composite(sp,xy)

def kitchen(im,topic,mood,t,action):
    color='#FF9BAD' if topic=='heart' else '#E7C37D'
    place(im,chef(topic,mood),330,905+math.sin(t*3)*4,.94,angle=math.sin(t*2)*1.4)
    hand=(521,1050) if topic=='heart' else (555,960)
    if action in ['hook','joke','end']:
        place(im,dish(topic),690,1160,.7,angle=math.sin(t*2)*1.5)
        if action=='joke':
            other='liver' if topic=='heart' else 'heart'
            place(im,chef(other,'wow'),840,860,.43,angle=math.sin(t*7)*4)
            if topic=='liver':place(im,prop('sponge'),825,1190,.32,angle=math.sin(t*4)*8)
    elif topic=='heart' and action in ['pour','cook']:
        place(im,pan(),700,1160,.84)
        if action=='pour':
            d=ImageDraw.Draw(im)
            if t%4<2:
                # A tilted measuring cup of oat flakes, not a generic food icon.
                d.polygon([(532,760),(655,802),(636,907),(555,879)],fill='#F1E9D6')
                d.ellipse((532,748,654,807),fill='#DCC498')
                for j in range(11):
                    xx=553+(j%4)*24;yy=769+(j//4)*7
                    d.ellipse((xx,yy,xx+15,yy+6),fill='#F9E6BE')
                arm(im,hand,(565,861),color)
                for i in range(10):
                    y=900+((t*170+i*35)%210);x=667+math.sin(i*4)*35
                    d.ellipse((x,y,x+13,y+7),fill='#D1B582')
            else:
                arm(im,hand,(582,838),color)
                d.rounded_rectangle((555,730,650,892),15,fill='#D6E8E4')
                d.line([(634,858),(698,940),(704,1070)],fill='#A3D6DD',width=22)
        else:
            sx=700+55*math.cos(t*3.8);sy=1055+15*math.sin(t*3.8)
            arm(im,hand,(sx-15,sy-107),color)
            place(im,prop('spoon'),sx,sy,.6,angle=23*math.sin(t*3.8)-35)
            steam(im,t)
    elif action=='mix' or action=='pour':
        place(im,dish('liver'),700,1160,.74)
        if action=='mix':
            sx=700+55*math.cos(t*4);sy=1060+22*math.sin(t*4)
            arm(im,hand,(sx-12,sy-120),color)
            place(im,prop('spoon'),sx,sy,.65,angle=25*math.sin(t*4)-30)
            for i in range(5):
                place(im,prop(['bean','tomato_cube','cucumber_slice'][i%3]),700+math.cos(t*2+i)*115,1114+math.sin(t*2+i)*29,.16)
        else:
            arm(im,hand,(570,858),color)
            d=ImageDraw.Draw(im)
            d.polygon([(520,809),(628,814),(610,873),(540,871)],fill='#F4EDD8')
            d.ellipse((515,789,632,836),fill='#EAD8AA')
            for i in range(7):
                elapsed=(t+i*.26)%1.7
                place(im,prop(['bean','tomato_cube','cucumber_slice'][i%3]),660+math.sin(i)*90,830+elapsed**2*105,.17,angle=t*50)
    elif action=='top':
        place(im,dish('heart','plain'),690,1160,.75)
        arm(im,hand,(605,867),color)
        for i in range(5):
            u=max(0,min(1,(t-i*.38)/.65))
            place(im,prop('banana_slice'),550+i*62,740+u*384,.2,angle=12*i)
    else:place(im,dish(topic),690,1160,.72)

def board(im,topic,t):
    rounded(im,(75,730,1005,1285),'#D8B98F',r=50,shadow=12)
    d=ImageDraw.Draw(im)
    for y in range(770,1250,37):d.line((110,y,963,y+8),fill='#D0AF84',width=3)
    d.ellipse((112,947,150,1000),fill='#AA8C66')
    if topic=='heart':
        place(im,prop('banana'),420,991,.77,angle=-18)
        for i in range(5):place(im,prop('banana_slice'),450+i*90,1100+math.sin(i)*17,.27*pop(t-i*.42),angle=i*12)
    else:
        place(im,prop('cucumber'),330,980,.67,angle=-16)
        place(im,prop('tomato'),780,926,.51)
        for i in range(5):
            place(im,prop('cucumber_slice'),335+i*69,1100+math.sin(i)*30,.2*pop(t-i*.4),angle=i*12)
            place(im,prop('tomato_cube'),680+(i%3)*66,1060+(i//3)*82,.19*pop(t-i*.43),angle=i*15)
    cutx=490+math.sin(t*.8)*55;cuty=914+abs(math.sin(t*5))*83
    color='#FF9BAD' if topic=='heart' else '#E7C37D'
    arm(im,(260,698),(322,950),color)
    arm(im,(658,698),(cutx-44,cuty-113),color)
    place(im,prop('knife'),cutx,cuty,.63,angle=-60)
    place(im,chef(topic,'serious'),200,602,.37,angle=math.sin(t*5)*3)
    tip='따라 하기 쉬운 얇은 조각' if topic=='heart' else '마른 콩 말고, 익힌 콩을 사용해요'

def rinse(im,t):
    d=ImageDraw.Draw(im)
    rounded(im,(160,830,920,1270),'#B6CFCE',r=90,shadow=10)
    d.arc((414,626,700,950),180,355,fill='#9BB8B7',width=48)
    d.rounded_rectangle((414,761,461,861),18,fill='#9BB8B7')
    for i in range(12):
        yy=856+((t*300+i*37)%260);xx=434+math.sin(i*5)*25
        d.line((xx,yy,xx,yy+25),fill='#D4F1F3',width=8)
    d.pieslice((292,916,808,1260),0,180,fill='#E2D9BF');d.ellipse((288,912,812,1110),fill='#F6EACF')
    for i in range(22):
        xx=367+(i%6)*57; yy=964+(i//6)*24
        place(im,prop('bean'),xx,yy,.14,angle=i*20)
    d=ImageDraw.Draw(im)
    for xx in range(365,780,65):d.ellipse((xx,1128,xx+12,1140),fill='#A8AC97')
    place(im,chef('liver','serious'),200,630,.35,angle=math.sin(t*3)*3)
    arm(im,(241,756),(313,1068),'#E7C37D')

def frame(topic,lang,idx,t,progress=0):
    ep=EPISODES[topic]; loc=ep[lang]; li=0 if lang=='ko' else 1
    action,mindur,mood,texts,titles=ep['scenes'][idx]
    im=background(topic).copy();d=ImageDraw.Draw(im)
    # Brand and title live inside the Shorts safe region.
    label(im,loc['brand'],(80,107),36,style='jua' if lang=='ko' else 'en',anchor='lm')
    label(im,'BODY KITCHEN',(980,107),25,fill=ep['color'],style='heavy',anchor='rm')
    d.line((80,156,1000,156),fill='#D5CFBE',width=3)
    d.rounded_rectangle((80,151,80+int(920*progress),161),5,fill=ep['color'])
    label(im,loc['series'],(540,204),31,style='jua' if lang=='ko' else 'en',maxw=890)
    titlelines=titles[li].split('\n')
    if action=='hook':
        for j,line in enumerate(titlelines):place(im,chip(line,91 if lang=='ko' else 79,YELLOW if j==0 else CREAM,'black' if lang=='ko' else 'heavy'),540+int((1-ease(t/.5))*900),326+j*116)
    else:
        place(im,chip(titles[li],64 if lang=='ko' else 57,CREAM,'black' if lang=='ko' else 'heavy'),540+int((1-ease(t/.38))*900),324)
        label(im,loc['dish'],(540,423),43,fill=ep['color'],style='jua' if lang=='ko' else 'en',maxw=850)
    if action=='ingredients':
        rounded(im,(90,505,990,970),'#FFFCF3',r=44,shadow=10)
        label(im,'1인분' if lang=='ko' else '1 SERVING',(153,556),32,fill=ep['color'],anchor='lm',style='jua' if lang=='ko' else 'en')
        for i,line in enumerate(loc['ingredients']):
            y=632+i*(77 if topic=='liver' else 100)
            d=ImageDraw.Draw(im);d.ellipse((140,y-9,158,y+9),fill=ep['color'])
            label(im,line,(184,y),51 if lang=='ko' else 44,anchor='lm',style='jua' if lang=='ko' else 'en',maxw=730)
        place(im,chef(topic,'happy'),280,1095,.48,angle=math.sin(t*2)*3)
        if topic=='heart':
            place(im,prop('banana'),735,1115,.58,angle=12)
        else:
            place(im,prop('tomato'),730,1125,.5,angle=10)
            place(im,prop('cucumber'),690,1212,.45,angle=-10)
    elif action=='chop':board(im,topic,t)
    elif action=='rinse':rinse(im,t)
    elif action in ['benefit','serve','end']:
        if action=='benefit':
            for i,line in enumerate(loc['benefit']):
                place(im,chip(line,49 if lang=='ko' else 41,MINT if i==0 else CREAM,'jua' if lang=='ko' else 'en'),540,572+i*105,scale=pop(t-i*.18))
            place(im,chef(topic,'proud'),255,1030,.67,angle=math.sin(t*2)*2)
            place(im,dish(topic),695,1180,.77)
            label(im,loc['source'],(540,1365),24,style='jua' if lang=='ko' else 'en',maxw=930)
        elif action=='serve':
            rounded(im,(85,514,995,850),'#FFFCF1',r=35,shadow=8)
            for i,line in enumerate(loc['recipe']):label(im,line,(540,583+i*97),46 if lang=='ko' else 39,style='jua' if lang=='ko' else 'en',maxw=830)
            place(im,dish(topic),540,1140,1.05,angle=math.sin(t*1.5)*1)
            for i in range(4):
                x=235+i*200;y=945+math.sin(t*3+i)*23
                label(im,'+', (x,y),48,fill=YELLOW,style='heavy')
        else:
            place(im,chip(loc['dish'],68 if lang=='ko' else 54,YELLOW,'black' if lang=='ko' else 'heavy'),540,550,scale=pop(t))
            place(im,chef(topic,'happy_closed'),340,905,.88,angle=math.sin(t*3)*3)
            place(im,dish(topic),700,1170,.75)
            place(im,chip('구독 + 좋아요' if lang=='ko' else 'SUBSCRIBE + LIKE',48,MINT,'jua' if lang=='ko' else 'en'),540,1325)
    else:
        kitchen(im,topic,mood,t,action)
        badge=loc['badge']
        if action=='cook':badge='약 5분 / 제품 조리시간 확인' if lang=='ko' else '~5 MIN / CHECK PACK DIRECTIONS'
        if action=='mix':badge='레몬즙 + 올리브유' if lang=='ko' else 'LEMON JUICE + OLIVE OIL'
        place(im,chip(badge,36 if lang=='ko' else 29,MINT,'jua' if lang=='ko' else 'en'),540,555 if action!='hook' else 580)
        if action=='mix':
            place(im,prop('lemon'),690,761,.32,angle=20)
            place(im,prop('oil'),853,790,.31,angle=-10)
    subtitles(im,texts[li],lang)
    disclaimer='일반 식사 아이디어 / 질환별 식단은 의료진과 상의하세요' if lang=='ko' else 'Everyday food ideas / Ask your clinician about medical diets'
    label(im,disclaimer,(540,1745),25 if lang=='ko' else 23,fill='#7A8076',style='jua' if lang=='ko' else 'en',maxw=930)
    # Page turn: an outgoing paper strip, with content continuously visible underneath.
    if idx and t<.25:
        x=int(-W+W*ease(t/.25));d=ImageDraw.Draw(im)
        d.polygon([(x,170),(x+W,170),(x+W-100,1425),(x-100,1425)],fill=ep['bg'])
    return im.convert('RGB')

def timeline(topic,lang):
    f=ROOT/'audio'/f'{topic}_{lang}'/'manifest.json'
    if f.exists():return json.loads(f.read_text(encoding='utf-8'))
    return [{'id':s[0],'duration':s[1],'text':s[3][0 if lang=='ko' else 1]} for s in EPISODES[topic]['scenes']]

def wavwrite(path,x,sr=24000):
    with wave.open(str(path),'wb') as f:
        f.setnchannels(1);f.setsampwidth(2);f.setframerate(sr);f.writeframes((np.clip(x,-1,1)*32767).astype(np.int16).tobytes())

def audio_mix(topic,lang,manifest):
    sr=24000;dur=sum(s['duration'] for s in manifest);N=math.ceil(dur*sr)
    voice=np.zeros(N,np.float32);sound=np.zeros(N,np.float32);clock=0
    rng=np.random.default_rng(22)
    for idx,scene in enumerate(manifest):
        with wave.open(str(ROOT/'audio'/f'{topic}_{lang}'/(scene['id']+'.wav'))) as f:
            x=np.frombuffer(f.readframes(f.getnframes()),np.int16).astype(np.float32)/32768
        rms=np.sqrt(np.mean(x*x));x=x*(.14/max(rms,.001))
        st=int((clock+.2)*sr);take=min(len(x),N-st);voice[st:st+take]=x[:take]
        # Soft wooden taps, a pour splash and a gentle finish chime, all synthesized locally.
        ts=[clock+.15]
        if scene['id']=='chop':ts += [clock+i*.46 for i in range(1,8)]
        for pos in ts:
            nn=int(sr*.13);t=np.arange(nn)/sr
            noise=rng.normal(0,1,nn)*np.exp(-t*42)*.04
            tap=np.sin(2*np.pi*740*t)*np.exp(-t*40)*.025+noise
            k=int(pos*sr);end=min(N,k+nn);sound[k:end]+=tap[:end-k]
        if scene['id'] in ['serve','top']:
            nn=int(sr*.7);t=np.arange(nn)/sr;x=(np.sin(2*np.pi*880*t)+.4*np.sin(2*np.pi*1320*t))*np.exp(-t*7)*.025
            k=int((clock+.3)*sr);end=min(N,k+nn);sound[k:end]+=x[:end-k]
        clock+=scene['duration']
    song='nimble_motifs.mp3' if topic=='heart' else 'buoyant_kitchen_groove.mp3'
    musicfile=ROOT.parent/'bgm'/song
    res=subprocess.run([FF,'-v','error','-i',str(musicfile),'-t',str(dur),'-ac','1','-ar',str(sr),'-f','f32le','pipe:1'],capture_output=True,check=True)
    music=np.frombuffer(res.stdout,np.float32).copy();music=np.pad(music,(0,max(0,N-len(music))))[:N]
    # Keep the original channel music comfortably behind the spoken recipe.
    music*=.018/max(np.sqrt(np.mean(music*music)),.001)
    from scipy.ndimage import maximum_filter1d,gaussian_filter1d
    energy=maximum_filter1d(np.abs(voice[::240]),size=18)
    duck=gaussian_filter1d((energy>.035).astype(np.float32),2)
    envelope=np.interp(np.arange(N),np.arange(len(duck))*240,1-duck*.67)
    music*=envelope
    fade=np.minimum(np.arange(N)/sr/.35,1)*np.minimum((N-np.arange(N))/sr/.8,1)
    music*=fade
    wavwrite(OUT/f'{topic}_{lang}_voice.wav',voice)
    wavwrite(OUT/f'{topic}_{lang}_music.wav',music)
    wavwrite(OUT/f'{topic}_{lang}_mix.wav',voice+music+sound)
    return OUT/f'{topic}_{lang}_mix.wav'

def subtitles_srt(topic,lang,manifest):
    def stamp(t):
        ms=round(t*1000);return f'{ms//3600000:02}:{ms//60000%60:02}:{ms//1000%60:02},{ms%1000:03}'
    rows=[];clock=0
    for i,s in enumerate(manifest):
        rows.append(f'{i+1}\n{stamp(clock+.2)} --> {stamp(clock+s["duration"])}\n{s["text"]}\n');clock+=s['duration']
    (OUT/f'{topic}_{lang}.srt').write_text('\n'.join(rows),encoding='utf-8-sig')

def preview(topic,lang):
    manifest=timeline(topic,lang);thumbs=[]
    for idx,s in enumerate(manifest):
        im=frame(topic,lang,idx,min(2,s['duration']/2),idx/len(manifest))
        im.save(OUT/f'{topic}_{lang}_scene_{idx:02}.png')
        thumb=im.resize((270,480));thumbs.append(thumb)
    sheet=Image.new('RGB',(270*5,520*2),'#E9E5DC')
    for i,im in enumerate(thumbs):
        sheet.paste(im,((i%5)*270,(i//5)*520));d=ImageDraw.Draw(sheet);d.text(((i%5)*270+8,(i//5)*520+485),manifest[i]['id'],font=font(21,'en'),fill=NAVY)
    sheet.save(OUT/f'{topic}_{lang}_storyboard.jpg',quality=94)
    frame(topic,lang,0,1.5).save(OUT/f'{topic}_{lang}_cover.png')
    print(f'Preview {topic}_{lang} ready',flush=True)

def render(topic,lang):
    manifest=timeline(topic,lang);dur=sum(s['duration'] for s in manifest)
    subtitles_srt(topic,lang,manifest);mix=audio_mix(topic,lang,manifest)
    filename=OUT/f'{topic}_{lang}.mp4'
    cmd=[FF,'-y','-hide_banner','-loglevel','error','-f','rawvideo','-pix_fmt','rgb24','-s',f'{W}x{H}',
         '-r',str(FPS),'-i','pipe:0','-i',str(mix),'-map','0:v:0','-map','1:a:0','-c:v','libx264','-preset','fast',
         '-crf','19','-pix_fmt','yuv420p','-threads','4','-af','loudnorm=I=-14:TP=-1.5:LRA=8','-c:a','aac','-b:a','192k',
         '-t',str(dur),'-movflags','+faststart',str(filename)]
    log=(OUT/f'{topic}_{lang}_encode.log').open('wb');proc=subprocess.Popen(cmd,stdin=subprocess.PIPE,stderr=log)
    nframes=math.ceil(dur*FPS);idx=0;start=0
    try:
        for f in range(nframes):
            time=f/FPS
            while idx<len(manifest)-1 and time>=start+manifest[idx]['duration']:
                start+=manifest[idx]['duration'];idx+=1
            im=frame(topic,lang,idx,time-start,time/dur)
            proc.stdin.write(im.tobytes())
            if f%(FPS*5)==0:print(f'{topic}_{lang} {time:.0f}/{dur:.1f}s',flush=True)
    finally:proc.stdin.close()
    if proc.wait()!=0:raise RuntimeError(f'FFmpeg failed: {filename}')
    log.close();print(f'FINISHED {filename} {dur:.1f}s',flush=True)

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('command',choices=['preview','render']);ap.add_argument('topic',choices=EPISODES);ap.add_argument('lang',choices=['ko','en'])
    args=ap.parse_args();globals()[args.command](args.topic,args.lang)
