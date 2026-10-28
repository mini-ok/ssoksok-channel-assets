"""User-directed revision: one Korean cooking short with four gentle transition options."""
import argparse, functools, json, math, subprocess, wave
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
import render as r
import style_reference_still as sty
sty.paper_chip=functools.lru_cache(maxsize=32)(sty.paper_chip)
import make_audio as speech

ROOT=Path(__file__).resolve().parent
OUT=ROOT/'output_v3';OUT.mkdir(exist_ok=True)
AUDIO=ROOT/'audio'/'heart_ko_v3';AUDIO.mkdir(exist_ok=True)
W,H,FPS=1080,1920,24
BG='#F5EFE2';INK='#26304F';MINT='#86BDA4';CORAL='#E97786'
CTA='구독은 사원증 발급! 좋아요는 보너스!'

TITLES={
 'hook':'아침도 없이 뛰라고요?',
 'ingredients':'재료는 딱 세 가지',
 'pour':'01  귀리와 물을 넣어요',
 'cook':'02  약불로 저어 익혀요',
 'chop':'03  바나나를 얇게 썰어요',
 'top':'그릇에 담고, 바나나 톡!',
 'benefit':'귀리의 식이섬유로 든든하게',
 'serve':'단맛은 바나나로 충분해요',
 'joke':'제 아침밥인데요?!',
 'end':'캡처해서 내일 아침에!'}

TRANSITIONS={
 1:('A','부드러운 겹침',.95),
 2:('A','부드러운 겹침',.9),
 3:('A','부드러운 겹침',.9),
 4:('B','살짝 확대하며 연결',1.05),
 5:('C','접시 모양 원형 연결',1.10),
 6:('A','부드러운 겹침',.95),
 7:('B','살짝 확대하며 연결',1.05),
 8:('A','부드러운 겹침',.9),
 9:('D','레시피 카드 펼침',1.15)}

def smooth(x):
    x=max(0.,min(1.,x));return x*x*(3-2*x)

def prepare_audio():
    source=ROOT/'audio'/'heart_ko'
    manifest=json.loads((source/'manifest.json').read_text(encoding='utf-8'))
    for item in manifest:
        path=AUDIO/(item['id']+'.wav')
        if item['id']!='end':
            if not path.exists():path.write_bytes((source/path.name).read_bytes())
        else:
            if not path.exists():
                print('Synthesizing revised ending...',flush=True)
                x=speech.tts.squeeze_gaps(speech.tts.trim_edges(speech.tts.synth(CTA,1,'ko-KR',mode='none')))
                x=speech.speed(x,1.14);speech.tts.save_wav(str(path),x)
            item['text']=CTA;item['duration']=10.0
        with wave.open(str(path)) as f:item['speech_duration']=f.getnframes()/f.getframerate()
        item['title']=TITLES[item['id']]
    (AUDIO/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
    return manifest

@functools.lru_cache(maxsize=1)
def manifest():return json.loads((AUDIO/'manifest.json').read_text(encoding='utf-8'))

@functools.lru_cache(maxsize=1)
def background():
    a=r.p.bg(W,H,top=r.p.hx(0xE5EFEE),bot=r.p.hx(0xEBE6ED),seed=17)
    a[1470:]=r.p.bg(W,450,top=r.p.hx(0xE2CFB1),bot=r.p.hx(0xE9D9C1),seed=31)
    return Image.fromarray((a*255).astype('uint8')).convert('RGBA')

def header(im,end=False):
    r.place(im,sty.paper_chip('쏙쏙 건강백과',32,0xFFF9EA),225,111)
    r.place(im,sty.paper_chip('쏙쏙 건강요리',37,0xFFF9EA),828,111)
    r.label(im,'오늘의 요리사 : 심장 쉐프',(540,219),55)
    if not end:r.place(im,board_title(),540,365)

@functools.lru_cache(maxsize=1)
def board_title():return sty.paper_chip('바나나 오트밀',91,0xE98979,-2)

@functools.lru_cache(maxsize=1)
def set_stage():
    im=Image.new('RGBA',(W,H));d=ImageDraw.Draw(im)
    # A quiet single shelf replaces the grid of cabinets and tiles.
    d.line((100,1000,980,1000),fill='#DED7C7',width=10)
    d.rounded_rectangle((123,833,260,990),24,fill='#E1DEC5')
    d.rectangle((160,848,222,886),fill='#FCF7E9')
    d.rounded_rectangle((833,874,941,991),30,fill='#DBE5D5')
    d.line((873,875,857,822),fill='#91AC8E',width=9)
    d.line((897,875,923,829),fill='#91AC8E',width=9)
    r.rounded(im,(45,1440,1035,1528),'#D2B08A',r=30,shadow=8)
    return im

@functools.lru_cache(maxsize=16)
def wrapped_caption(text):
    im=Image.new('RGBA',(W,H));d=ImageDraw.Draw(im);size=62;words=text.split()
    while True:
        options=[]
        if d.textlength(text,font=r.font(size))<910:lines=[text];break
        for k in range(1,len(words)):
            a,b=' '.join(words[:k]),' '.join(words[k:])
            wa=d.textlength(a,font=r.font(size));wb=d.textlength(b,font=r.font(size))
            if max(wa,wb)<910:options.append((abs(wa-wb),[a,b]))
        if options:lines=min(options,key=lambda x:x[0])[1];break
        size-=1
    # One stable subtitle area, larger and lower after the unwanted footer was removed.
    r.place(im,caption_paper(),540,1650)
    for i,line in enumerate(lines):
        r.label(im,line,(540,1650+(i-(len(lines)-1)/2)*82),size)
    return im

@functools.lru_cache(maxsize=1)
def caption_paper():
    return sty.sprite(lambda a:r.p.puff(a,r.p.rr(1010,250,25,15,985,225,28),r.p.hx(0xFFFCF2),15,soft=9,shadow=(7,12),sh_blur=11,depth=.85),1010,250)

def recipe_card():
    im=Image.new('RGBA',(W,H))
    r.rounded(im,(72,260,1008,1530),'#FFFCF3',r=45,shadow=11)
    r.label(im,'바나나 오트밀',(540,369),89,style='black')
    r.label(im,'1인분 / 약 5분',(540,469),43,fill='#658D7A')
    d=ImageDraw.Draw(im);d.line((130,529,950,529),fill='#D7DFCB',width=3)
    r.label(im,'재료',(137,603),54,fill='#638B77',anchor='lm')
    r.label(im,'귀리 40g   물 200mL',(137,684),55,anchor='lm')
    r.label(im,'바나나 1/2개',(137,761),55,anchor='lm')
    d.line((130,826,950,826),fill='#D7DFCB',width=3)
    rows=[
      ('1','냄비에 귀리와 물을 넣어요.'),
      ('2','끓으면 약불로 줄이고'),
      ('','저으며 부드럽게 익혀요.'),
      ('','약 5분 / 제품 조리시간 확인'),
      ('3','바나나를 얇게 썰어 올려요.')]
    ys=[908,1018,1096,1174,1293]
    for (number,line),y in zip(rows,ys):
        if number:
            d.ellipse((130,y-31,192,y+31),fill='#E3EAD5')
            r.label(im,number,(161,y),42,style='en',fill='#567A65')
        r.label(im,line,(219,y),52 if y!=1174 else 38,anchor='lm',maxw=725)
    r.label(im,'설탕 없이, 바나나로 달콤하게',(540,1425),43,fill='#8B7962')
    return im

CARD=functools.lru_cache(maxsize=1)(recipe_card)

@functools.lru_cache(maxsize=16)
def heading_sprite(idx):return sty.paper_chip(TITLES[manifest()[idx]['id']],55,0x9DC7DE,1)
def heading(im,idx):r.place(im,heading_sprite(idx),540,567)

def scene_content(idx,t):
    rows=manifest();scene=rows[idx];action=scene['id']
    mood=r.EPISODES['heart']['scenes'][idx][2]
    im=Image.new('RGBA',(W,H))
    if action=='end':
        im.alpha_composite(CARD())
        return im
    if action=='ingredients':
        r.rounded(im,(100,717,980,1205),'#FFFCF3',r=42,shadow=9)
        for i,(word,amount) in enumerate([('롤드 오트','40g'),('물','200mL'),('바나나','1/2개')]):
            y=819+i*135
            r.label(im,word,(170,y),67,anchor='lm')
            r.label(im,amount,(910,y),67,fill='#668F7A',anchor='rm')
        r.place(im,r.chef('heart','happy'),275,1344,.41,angle=math.sin(t*1.7)*1.5)
        r.place(im,r.prop('banana'),765,1350,.53,angle=-8)
    elif action=='chop':
        layer=Image.new('RGBA',(W,H));r.board(layer,'heart',t)
        # Keep the cutting close-up lower; its mini chef is introduced together with the board.
        crop=layer.crop((0,470,W,1330));im.alpha_composite(crop,(0,650))
    elif action in ['benefit','serve']:
        if action=='benefit':
            r.label(im,'귀리의 수용성 식이섬유',(540,774),66,fill='#618B75')
            r.label(im,'심장 건강을 챙기는 식습관',(540,871),56)
            r.place(im,r.chef('heart','proud'),260,1198,.65,angle=math.sin(t*1.7)*1.2)
            r.place(im,r.dish('heart'),697,1355,.78)
            r.label(im,'출처: 미국심장협회 / 귀리와 심장 건강',(540,1510),27,fill='#808576')
        else:
            r.label(im,'설탕은 넣지 않았어요',(540,798),62,fill='#638B77')
            r.place(im,r.dish('heart'),540,1237,1.15,angle=math.sin(t*1.6)*1.2)
    else:
        im.alpha_composite(set_stage())
        layer=Image.new('RGBA',(W,H));r.kitchen(layer,'heart',mood,t,action)
        im.alpha_composite(layer.crop((0,600,W,1410)),(0,760))
        if action=='cook':
            r.label(im,'약 5분 / 제품 조리시간에 맞춰요',(540,746),43,fill='#638B77')
    return im

@functools.lru_cache(maxsize=12)
def previous_content(idx):
    return scene_content(idx,manifest()[idx]['duration']-.01)

def zoom_layer(im,scale,center=(540,1050)):
    cx,cy=center
    # Inverse affine map keeps the point of action fixed, without a lateral swoosh.
    return im.transform((W,H),Image.Transform.AFFINE,
          (1/scale,0,cx-cx/scale,0,1/scale,cy-cy/scale),Image.Resampling.BICUBIC)

@functools.lru_cache(maxsize=64)
def circle_mask(step):
    u=step/60
    mask=Image.new('L',(W,H));d=ImageDraw.Draw(mask)
    # Slow plate-shaped reveal; the preceding shot remains visible outside the plate.
    rad=30+u*1680;cx,cy=680,1260
    d.ellipse((cx-rad,cy-rad,cx+rad,cy+rad),fill=255)
    return mask.filter(ImageFilter.GaussianBlur(20))

def transition(idx,t,new):
    if idx not in TRANSITIONS:return new
    kind,_,duration=TRANSITIONS[idx]
    if t>=duration:return new
    u=smooth(t/duration);old=previous_content(idx-1)
    # Flatten before blending: straight-alpha interpolation otherwise makes white paper turn gray.
    old_flat=background().copy();old_flat.alpha_composite(old)
    new_flat=background().copy();new_flat.alpha_composite(new)
    old,new=old_flat,new_flat
    if kind=='A':return Image.blend(old,new,u)
    if kind=='B':
        return Image.blend(zoom_layer(old,1+.035*u),zoom_layer(new,.965+.035*u),u)
    if kind=='C':return Image.composite(new,old,circle_mask(round(u*60)))
    if kind=='D':
        # Paper card unfolds only 3% in size, rather than flying across the screen.
        return Image.blend(old,zoom_layer(new,.97+.03*u,center=(540,920)),u)
    return new

def frame(idx,t):
    im=background().copy();end=idx==9
    im.alpha_composite(transition(idx,t,scene_content(idx,t)))
    header(im,end)
    if end and t<1.15:
        # Keep the old title briefly while the recipe card settles into the same title position.
        h=Image.new('RGBA',(W,H));header(h,False)
        crop=h.crop((0,275,W,465));alpha=1-smooth(t/.65)
        crop.putalpha(crop.getchannel('A').point(lambda a:round(a*alpha)))
        im.alpha_composite(crop,(0,275))
    # Headings dissolve through the paper background, so two different sentences never overlap.
    duration=TRANSITIONS.get(idx,('', '',0))[2]
    if duration and t<duration:
        old_h=Image.new('RGBA',(W,H));heading(old_h,idx-1)
        alpha=1-smooth(t/(duration*.42))
        old_h.putalpha(old_h.getchannel('A').point(lambda a:round(a*alpha)));im.alpha_composite(old_h)
        if not end:
            new_h=Image.new('RGBA',(W,H));heading(new_h,idx)
            alpha=smooth((t/duration-.38)/.62)
            new_h.putalpha(new_h.getchannel('A').point(lambda a:round(a*alpha)));im.alpha_composite(new_h)
    elif not end:heading(im,idx)
    if end:
        # The full recipe stays still for the whole ending; CTA sits outside the capture card.
        if t>1.15:
            r.label(im,'구독은 사원증 발급!',(540,1632),59)
            r.label(im,'좋아요는 보너스!',(540,1723),67,fill='#638B77')
    else:
        caption=wrapped_caption(manifest()[idx]['text'])
        if idx and t<.7:
            caption=caption.copy();alpha=smooth(t/.7)
            caption.putalpha(caption.getchannel('A').point(lambda a:round(a*alpha)))
        im.alpha_composite(caption)
    return im.convert('RGB')

def prepare_mix(rows):
    sr=24000;dur=sum(s['duration'] for s in rows);n=math.ceil(dur*sr)
    voice=np.zeros(n,np.float32);fx=np.zeros(n,np.float32);clock=0
    for idx,s in enumerate(rows):
        with wave.open(str(AUDIO/(s['id']+'.wav'))) as f:x=np.frombuffer(f.readframes(f.getnframes()),np.int16).astype(np.float32)/32768
        # Existing source takes were made at 1.22x (the revised ending at 1.14x).
        # Bring speech to the user's channel-standard 1.30x without shortening reading/recipe holds.
        x=x  # V3 dialogue already performed and mastered at 1.3x
        x*=.14/max(np.sqrt(np.mean(x*x)),.001)
        delay=.18 if idx==0 else 1.0
        start=int((clock+delay)*sr);voice[start:start+len(x)]+=x[:max(0,n-start)]
        if s['id']=='chop':
            for j in range(5):
                pos=int((clock+1+j*.44)*sr);tt=np.arange(2400)/sr
                fx[pos:pos+2400]+=(np.sin(tt*2*np.pi*620)*np.exp(-tt*45)*.022).astype(np.float32)
        clock+=s['duration']
    source=ROOT.parent/'bgm'/'nimble_motifs.mp3'
    music=np.frombuffer(subprocess.run([r.FF,'-v','error','-i',str(source),'-t',str(dur),'-ac','1','-ar',str(sr),'-f','f32le','pipe:1'],capture_output=True,check=True).stdout,np.float32).copy()
    music=np.pad(music,(0,max(0,n-len(music))))[:n];music*=.0105/max(np.sqrt(np.mean(music*music)),.001)
    from scipy.ndimage import maximum_filter1d,gaussian_filter1d
    act=maximum_filter1d(np.abs(voice[::240]),size=18)>.035
    env=1-gaussian_filter1d(act.astype(np.float32),2)*.67
    music*=np.interp(np.arange(n),np.arange(len(env))*240,env)
    music*=np.minimum(np.arange(n)/sr/.4,1)*np.minimum((n-np.arange(n))/sr/1.2,1)
    for name,a in [('voice',voice),('music',music),('mix',voice+music+fx)]:r.wavwrite(OUT/f'heart_ko_v2_{name}.wav',a)
    def stamp(t):
        m=round(t*1000);return f'{m//3600000:02}:{m//60000%60:02}:{m//1000%60:02},{m%1000:03}'
    text=[];clock=0
    for idx,s in enumerate(rows):
        text.append(f'{idx+1}\n{stamp(clock+(.18 if idx==0 else 1))} --> {stamp(clock+s["duration"])}\n{s["text"]}\n');clock+=s['duration']
    (OUT/'heart_ko_v2.srt').write_text('\n'.join(text),encoding='utf-8-sig')
    return OUT/'heart_ko_v2_mix.wav'

def preview():
    rows=manifest();sheet=Image.new('RGB',(5*270,2*480))
    for i,row in enumerate(rows):
        im=frame(i,2.1);im.save(OUT/f'scene_{i:02}.png');sheet.paste(im.resize((270,480)),((i%5)*270,(i//5)*480))
    sheet.save(OUT/'storyboard_v2.jpg',quality=95)
    card=background().copy();header(card,True);card.alpha_composite(CARD());card.save(OUT/'바나나오트밀_캡처용_레시피.png')
    # A sheet of actual intermediate transition frames, not just before/after stills.
    sh=Image.new('RGB',(3*216,4*384))
    for row,idx in enumerate([1,4,5,9]):
        dur=TRANSITIONS[idx][2]
        for col,u in enumerate([.25,.5,.75]):sh.paste(frame(idx,dur*u).resize((216,384)),(col*216,row*384))
    sh.save(OUT/'transition_midpoints.jpg',quality=95)
    print('V2 preview ready',flush=True)

def render():
    rows=manifest();mix=prepare_mix(rows);duration=sum(s['duration'] for s in rows)
    target=OUT/'쏙쏙건강요리_바나나오트밀_종이질감_v3.mp4'
    command=[r.FF,'-y','-v','error','-f','rawvideo','-pix_fmt','rgb24','-s',f'{W}x{H}','-r',str(FPS),'-i','pipe:0',
         '-i',str(mix),'-map','0:v:0','-map','1:a:0','-c:v','libx264','-crf','19','-preset','fast','-threads','4',
        '-pix_fmt','yuv420p','-af','loudnorm=I=-14:TP=-1.5:LRA=8','-c:a','aac','-b:a','192k','-t',str(duration),'-movflags','+faststart',str(target)]
    with (OUT/'encode.log').open('wb') as log:
        proc=subprocess.Popen(command,stdin=subprocess.PIPE,stderr=log)
        idx=0;start=0
        try:
            for f in range(math.ceil(duration*FPS)):
                t=f/FPS
                while idx<len(rows)-1 and t>=start+rows[idx]['duration']:
                    start+=rows[idx]['duration'];idx+=1
                proc.stdin.write(frame(idx,t-start).tobytes())
                if f%(FPS*5)==0:print(f'V2 {t:.0f}/{duration:.1f}s',flush=True)
        finally:proc.stdin.close()
        if proc.wait()!=0:raise RuntimeError('Encoding failed')
    guide=[];clock=0
    for idx,row in enumerate(rows):
        if idx in TRANSITIONS:
            kind,title,span=TRANSITIONS[idx];guide.append({'at_seconds':round(clock,2),'type':kind,'name':title,'duration':span})
        clock+=row['duration']
    (OUT/'transition_timestamps.json').write_text(json.dumps(guide,ensure_ascii=False,indent=2),encoding='utf-8')
    print(f'FINISHED {target} / {duration:.1f}s',flush=True)

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('command',choices=['audio','preview','render']);a=ap.parse_args()
    if a.command=='audio':prepare_audio()
    else:globals()[a.command]()
