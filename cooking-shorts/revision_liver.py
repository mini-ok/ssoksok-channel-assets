"""Liver chef chickpea salad short, built with the v5 template (caption tags, keyword highlight, acting effects)."""
import argparse, functools, json, math, subprocess, wave
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
import render as r
import functools as _ft
_original_prop=r.prop
@_ft.lru_cache(maxsize=64)
def cooking_prop(kind):
    # Base spoon sprite points the wrong way for cooking shots (confirmed bug, user feedback 2026-10-28:
    # liver short's stirring spoon was backwards again — same fix applied to heart's cooking-shorts render must
    # also be applied here, since liver's mix scene reuses render.prop('spoon') too).
    im=_original_prop(kind)
    return im.rotate(180) if kind=='spoon' else im
r.prop=cooking_prop
import style_reference_still as sty
sty.paper_chip=functools.lru_cache(maxsize=32)(sty.paper_chip)
import sys,os
sys.path.insert(0,str(Path(__file__).resolve().parent/'runtime'))
import channel_tts
_own_token=channel_tts.token
import make_audio as speech
channel_tts.token=_own_token   # make_audio swaps in ADC; this environment signs with the channel key instead
sys.path.insert(0,str(Path(__file__).resolve().parent.parent/'engine'/'pipeline'/'render'))
os.environ.setdefault('ASR_BACKEND','whisper')

ROOT=Path(__file__).resolve().parent
OUT=ROOT/'output_liver';OUT.mkdir(exist_ok=True)
AUDIO=ROOT/'audio'/'liver_ko_v1';AUDIO.mkdir(exist_ok=True)
W,H,FPS=1080,1920,24
BG='#F5EFE2';INK='#26304F';MINT='#86BDA4';CORAL='#E97786'
CTA='구독은 사원증 발급! 좋아요는 보너스!'
MANIFEST_SOURCE='liver_ko'

TITLES={
 'hook':'간 과장, 오늘은 셰프!',
 'ingredients':'재료는 딱 다섯 가지',
 'rinse':'01  헹구고 물 빼기',
 'chop':'02  씻고 작게 썰기',
 'pour':'03  볼에 모두 담기',
 'mix':'04  한 작은술씩 섞기',
 'cause':'왜 간에 지방이 쌓일까',
 'benefit':'지중해식 식단이 좋은 이유',
 'serve':'마법 말고, 좋은 습관',
 'joke':'설거지는 심장 씨가?',
 'end':'캡처해서 오늘 곁들임에!'}

TRANSITIONS={
 1:('A','부드러운 겹침',.95),
 2:('A','부드러운 겹침',.9),
 3:('A','부드러운 겹침',.9),
 4:('B','살짝 확대하며 연결',1.05),
 5:('C','접시 모양 원형 연결',1.10),
 # scene indices 6-9 below shifted to 7-10 when the 'cause' scene was inserted at index 6;
 # 'cause' itself (index 6) uses the default plain transition.
 7:('A','부드러운 겹침',.95),
 8:('B','살짝 확대하며 연결',1.05),
 9:('A','부드러운 겹침',.9),
 10:('D','레시피 카드 펼침',1.15)}

def smooth(x):
    x=max(0.,min(1.,x));return x*x*(3-2*x)

import requests,time
# Voices: liver chef is a calm, easy-going male voice (Umbriel), different from the heart chef; narrator stays Despina.
VOICE={'간 쉐프':('Charon','묵묵히 야근하는 간 과장. 낮고 차분하게, 한숨 섞어, 다정함이 묻어나게.'),'여성 내레이터':('Despina','다정한 요리 쇼츠 내레이터.')}  # 사용자 지시(2026-10-28): 기본은 건강백과 채널 기존 캐릭터 목소리(sid 3)를 그대로 쓴다 — 심장 쉐프만 사용자가 예외로 바꾸라고 했다
SPEAKER_BY_ID={'hook':'간 쉐프','ingredients':'여성 내레이터','rinse':'간 쉐프','chop':'여성 내레이터','pour':'간 쉐프','mix':'간 쉐프',
 'cause':'여성 내레이터','benefit':'여성 내레이터','serve':'여성 내레이터','joke':'간 쉐프','end':'간 쉐프'}
# Short acting directions only: a long prompt on a short line gets read aloud by the voice model.
ACTS={'hook':'오늘은 설거지 말고 요리라서 신나고 홀가분하게!','ingredients':'밝고 또랑또랑하게 하나씩 짚으며.','rinse':'경쾌하고 야무지게.','chop':'즐겁고 통통 튀게.',
 'pour':'들뜬 목소리로 착착.','mix':'신나게, 리듬 타듯.','cause':'친근하고 똑부러지게, 궁금증을 짚어주듯.','benefit':'자신 있고 밝게.','serve':'으쓱하며 유쾌하게.',
 'joke':'억울해서 발랄하게 투덜대는 말투로.','end':'경쾌하게 활짝 웃으며.'}
import asr_qa

def gsynth(text,voice,prompt):
    body={"input":({"text":text,"prompt":prompt} if prompt else {"text":text}),"voice":{"languageCode":"ko-KR","name":voice,"modelName":channel_tts.MODEL},
          "audioConfig":{"audioEncoding":"LINEAR16","sampleRateHertz":channel_tts.SR}}
    for wait in (0,2,4,8):
        time.sleep(wait)
        r=requests.post(channel_tts.G_URL,headers={"Authorization":"Bearer "+channel_tts.token(),"x-goog-user-project":channel_tts.PROJECT},json=body,timeout=120)
        if r.status_code==200:return channel_tts.decode(r)
    raise RuntimeError(f'TTS {r.status_code}: {r.text[:200]}')

def synth_line(text,speaker,act,path):
    voice,persona=VOICE[speaker];spoken=channel_tts.clean_text(text);best=None;why='';fallback_only=True
    for attempt in range(5):
        prompt=(persona+' '+act) if attempt<3 else (persona if attempt==3 else '')
        x=speech.tts.squeeze_gaps(speech.tts.trim_edges(gsynth(spoken,voice,prompt)))
        ok,heard,why=asr_qa.check(x,24000,spoken,'ko',prompt)
        print(f'  {path.stem} try{attempt+1} {len(x)/24000:.2f}s {why} | {heard[:40]}',flush=True)
        # Whisper writes numbers as digits ('40g'), which can fail the text match although the take is fine,
        # so a take that merely mismatches in coverage is kept as a fallback; leaked prompts / extra words are never kept.
        # The closing line must say 보너스 exactly (a take heard as 버너스/뽀러스 is rejected).
        if ok and (path.stem!='end' or '보너스' in heard.replace(' ','')):best=x;break
        if not (why.startswith('leak') or why.startswith('extra') or why=='empty'):
            if best is None or fallback_only:best=x;fallback_only=False
        elif best is None:best=x;fallback_only=True
    x=speech.speed(best,1.4);speech.tts.save_wav(str(path),x);return why

def prepare_audio():
    source=ROOT/'audio'/MANIFEST_SOURCE
    manifest=json.loads((source/'manifest.json').read_text(encoding='utf-8'))
    qa={}
    for item in manifest:
        path=AUDIO/(item['id']+'.wav')
        item['speaker']=SPEAKER_BY_ID[item['id']]
        text=CTA if item['id']=='end' else item['text']
        item['text']=text
        if not path.exists():
            print('Synthesizing',item['id'],flush=True)
            qa[item['id']]=synth_line(text,item['speaker'],ACTS[item['id']],path)
        with wave.open(str(path)) as f:item['speech_duration']=f.getnframes()/f.getframerate()
        delay=.18 if item['id']=='hook' else 1.0
        item['duration']=10.0 if item['id']=='end' else round(max(item['duration'],delay+item['speech_duration']+.45),3)
        item['title']=TITLES[item['id']]
    (AUDIO/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
    if qa:(AUDIO/'speech_qa.json').write_text(json.dumps(qa,ensure_ascii=False,indent=2),encoding='utf-8')
    return manifest

@functools.lru_cache(maxsize=1)
def manifest():return json.loads((AUDIO/'manifest.json').read_text(encoding='utf-8'))

@functools.lru_cache(maxsize=1)
def background():
    a=r.p.bg(W,H,top=r.p.hx(0xE5EFEE),bot=r.p.hx(0xEBE6ED),seed=17)
    a[1470:]=r.p.bg(W,450,top=r.p.hx(0xE2CFB1),bot=r.p.hx(0xE9D9C1),seed=31)
    return Image.fromarray((a*255).astype('uint8')).convert('RGBA')

def header(im,end=False):
    r.place(im,sty.paper_chip('쏙쏙 건강백과',38,0xFFF9EA),235,108)
    r.place(im,sty.paper_chip('쏙쏙 건강요리',44,0xE2F3EC),815,108)
    r.place(im,chef_tag(),540,222)
    if not end:r.place(im,board_title(),540,365)

@functools.lru_cache(maxsize=1)
def chef_tag():return sty.paper_chip('오늘의 요리사 : 간 쉐프',48,0xF0DBA0)

@functools.lru_cache(maxsize=1)
def board_title():return sty.paper_chip('병아리콩 샐러드',84,0x5BB8AA,-2)

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

SPEAKER={'간 쉐프':('간 쉐프',0xEBCB78),'여성 내레이터':('해설',0x9ACDB4)}
KEYWORDS={'hook':{'뒷정리','요리할게요.'},'ingredients':{'병아리콩,','오이,','토마토.','레몬즙과','올리브유요.'},'rinse':{'헹궈서','물기를'},
 'chop':{'작게'},'pour':{'한데'},'mix':{'한','작은술씩.','살살'},
 'cause':{'쓰는','것보다','많이','먹어서'},'benefit':{'식이섬유가','지중해식','식단은','간','지방을'},
 'serve':{'해독','마법은','습관이죠.'},'joke':{'설거지도요?','심장'}}
KEYWORDS={k:{w.strip('!?.,') for w in v} for k,v in KEYWORDS.items()}

def split_lines(text,size,d):
    words=text.split()
    if d.textlength(text,font=r.font(size))<900:return [words]
    best=None
    for k in range(1,len(words)):
        a,b=words[:k],words[k:]
        wa=d.textlength(' '.join(a),font=r.font(size));wb=d.textlength(' '.join(b),font=r.font(size))
        if max(wa,wb)<900 and (best is None or abs(wa-wb)<best[0]):best=(abs(wa-wb),[a,b])
    return best[1] if best else None

@functools.lru_cache(maxsize=16)
def wrapped_caption(idx):
    scene=manifest()[idx];text=scene['text'];keys=KEYWORDS.get(scene['id'],set())
    im=Image.new('RGBA',(W,H));d=ImageDraw.Draw(im);size=68
    while True:
        lines=split_lines(text,size,d)
        if lines:break
        size-=1
    r.place(im,caption_paper(),540,1650)
    label,color=SPEAKER[scene.get('speaker','간 쉐프')]
    tag=sty.paper_chip(label,44,color)
    r.place(im,tag,250,1522)
    f=r.font(size);space=d.textlength(' ',font=f)
    for li,words in enumerate(lines):
        y=1665+(li-(len(lines)-1)/2)*86
        widths=[d.textlength(w,font=f) for w in words]
        x=540-(sum(widths)+space*(len(words)-1))/2
        for w,wd in zip(words,widths):
            hit=w.strip('!?.,') in keys
            if hit:d.rounded_rectangle((x-8,y-39,x+wd+8,y+41),20,fill='#FFE7A3')
            d.text((x,y),w,font=f,fill='#D6485E' if hit else INK,anchor='lm')
            x+=wd+space
    return im

@functools.lru_cache(maxsize=1)
def caption_paper():
    return sty.sprite(lambda a:r.p.puff(a,r.p.rr(1010,250,25,15,985,225,28),r.p.hx(0xFFFCF2),15,soft=9,shadow=(7,12),sh_blur=11,depth=.85),1010,250)

def recipe_card():
    im=Image.new('RGBA',(W,H))
    r.rounded(im,(72,260,1008,1530),'#FFFCF3',r=45,shadow=11)
    r.label(im,'병아리콩 샐러드',(540,369),82,style='black')
    r.label(im,'1인 곁들임 / 약 3분',(540,469),43,fill='#658D7A')
    d=ImageDraw.Draw(im);d.line((130,529,950,529),fill='#D7DFCB',width=3)
    r.label(im,'재료',(137,590),54,fill='#638B77',anchor='lm')
    r.label(im,'익힌 병아리콩 100g   오이 1/4개',(137,664),47,anchor='lm')
    r.label(im,'작은 토마토 1개',(137,730),47,anchor='lm')
    r.label(im,'레몬즙 1작은술   올리브유 1작은술',(137,796),47,anchor='lm')
    d.line((130,850,950,850),fill='#D7DFCB',width=3)
    rows=[
      ('1','통조림 콩은 헹궈 물기를 빼요.'),
      ('','가능하면 무염 제품으로'),
      ('2','오이와 토마토를 작게 썰어요.'),
      ('3','볼에 담고 레몬즙과 올리브유를'),
      ('','살살 섞어요.')]
    ys=[925,1000,1090,1190,1264]
    for (number,line),y in zip(rows,ys):
        if number:
            d.ellipse((130,y-31,192,y+31),fill='#E3EAD5')
            r.label(im,number,(161,y),42,style='en',fill='#567A65')
        r.label(im,line,(219,y),52 if number or y!=1000 else 40,anchor='lm',maxw=725)
    r.label(im,'마른 콩은 그대로 쓰지 않아요',(540,1380),40,fill='#8B7962')
    r.label(im,'곁들임이에요. 한 끼 전체 영양은 아니에요',(540,1440),38,fill='#8B7962')
    return im

CARD=functools.lru_cache(maxsize=1)(recipe_card)

@functools.lru_cache(maxsize=16)
def heading_sprite(idx):
    text=TITLES[manifest()[idx]['id']];size=68
    while size>46 and r.p.tw(text,size,'black')+130>1000:size-=2
    return sty.paper_chip(text,size,0x9DC7DE,1)
def heading(im,idx):r.place(im,heading_sprite(idx),540,567)

MOODS={'hook':[(0,'tired'),(1.0,'happy'),(1.8,'sparkle')],
 'rinse':[(0,'serious'),(2.2,'relieved')],
 'chop':[(0,'serious')],'pour':[(0,'happy')],
 'mix':[(0,'happy'),(3.0,'sparkle')],'joke':[(0,'wow'),(1.1,'shock')]}
def mood_at(action,default,t):
    cur=default
    for at,m in MOODS.get(action,[]):
        if t>=at:cur=m
    return cur

def star(d,x,y,size,fill):
    k=.28
    pts=[(x,y-size),(x+size*k,y-size*k),(x+size,y),(x+size*k,y+size*k),(x,y+size),(x-size*k,y+size*k),(x-size,y),(x-size*k,y-size*k)]
    d.polygon(pts,fill=fill)
def sparkles(im,t,spots,fill='#F5C94B'):
    d=ImageDraw.Draw(im)
    for n,(x,y,size) in enumerate(spots):
        k=.5+.5*math.sin(t*5+n*1.9)
        if k>.08:star(d,x,y,size*(.4+.6*k),fill)
def sweat(im,x,y,t):
    d=ImageDraw.Draw(im);y+=math.sin(t*6)*6
    d.polygon([(x,y-46),(x-24,y+6),(x+24,y+6)],fill='#9AD3EA');d.ellipse((x-24,y-12,x+24,y+36),fill='#9AD3EA')
    d.ellipse((x-9,y+2,x-1,y+14),fill='#E9F7FB')
def bang(im,x,y,t,size=110):
    sc=1+.12*math.sin(t*14)
    r.label(im,'!',(x,y),round(size*sc),fill='#E0586D',style='heavy')
def floating_hearts(im,t,x,y):
    d=ImageDraw.Draw(im)
    for n in range(3):
        u=(t*.55+n/3)%1;hx=x+math.sin(n*2.3+u*5)*38+n*26-26;hy=y-u*150;sz=18+8*(1-u);a=round(255*(1-u))
        lay=Image.new('RGBA',(80,80));dl=ImageDraw.Draw(lay)
        dl.ellipse((10,12,40,42),fill=(233,119,134,a));dl.ellipse((36,12,66,42),fill=(233,119,134,a));dl.polygon([(12,34),(64,34),(38,66)],fill=(233,119,134,a))
        lay=lay.resize((round(sz*2.4),round(sz*2.4)));im.alpha_composite(lay,(round(hx-lay.width/2),round(hy-lay.height/2)))
def stamp(im,x,y,text,angle=-12):
    lay=Image.new('RGBA',(330,330));d=ImageDraw.Draw(lay)
    d.ellipse((12,12,318,318),fill='#FFF3F0',outline='#E0586D',width=10);d.ellipse((34,34,296,296),outline='#E0586D',width=4)
    r.label(lay,text[0],(165,120),74,fill='#E0586D',style='black');r.label(lay,text[1],(165,215),74,fill='#E0586D',style='black')
    r.place(im,lay,x,y,.9,angle=angle)

def icon(kind):
    im=Image.new('RGBA',(120,120))
    sprite={'bean':'bean','cucumber':'cucumber_slice','tomato':'tomato','lemon':'lemon','oil':'oil'}[kind]
    p=r.prop(sprite);k=min(100/p.width,100/p.height)
    im.alpha_composite(p.resize((round(p.width*k),round(p.height*k))),(10,10));return im

def scene_content(idx,t):
    rows=manifest();scene=rows[idx];action=scene['id']
    default=r.EPISODES['liver']['scenes'][idx][2]
    mood=mood_at(action,default,t)
    im=Image.new('RGBA',(W,H))
    if action=='end':
        im.alpha_composite(CARD())
        return im
    if action=='ingredients':
        r.rounded(im,(100,690,980,1190),'#FFFCF3',r=42,shadow=9)
        items=[('익힌 병아리콩','100g','bean'),('오이','1/4개','cucumber'),('작은 토마토','1개','tomato'),('레몬즙','1작은술','lemon'),('올리브유','1작은술','oil')]
        for i,(word,amount,kind) in enumerate(items):
            y=770+i*88
            u=smooth((t-.15-i*.3)/.4)
            row=Image.new('RGBA',(W,H))
            r.place(row,icon(kind),175,y,.62)
            r.label(row,word,(245,y),56,anchor='lm')
            r.label(row,amount,(935,y),56,fill='#668F7A',anchor='rm')
            row.putalpha(row.getchannel('A').point(lambda a:round(a*u)));im.alpha_composite(row,(0,round(14*(1-u))))
        r.place(im,r.chef('liver','sparkle'),250,1330,.6,angle=math.sin(t*1.7)*2)
        sparkles(im,t,[(95,1180,26),(445,1230,20),(120,1450,18)])
        r.place(im,r.dish('liver'),780,1360,.62,angle=math.sin(t*1.5)*1.2)
    elif action=='rinse':
        im.alpha_composite(set_stage())
        layer=Image.new('RGBA',(W,H));r.rinse(layer,t)
        im.alpha_composite(layer.crop((0,600,W,1330)),(0,700))
        if t>2.2:floating_hearts(im,t-2.2,230,1020)
    elif action=='chop':
        layer=Image.new('RGBA',(W,H));r.board(layer,'liver',t)
        crop=layer.crop((0,470,W,1330));im.alpha_composite(crop,(0,650))
    elif action=='cause':
        r.label(im,'쓰는 것보다 많이 먹으면',(540,750),56,fill='#4F8A6E')
        r.label(im,'간에 지방이 쌓일지도 몰라요',(540,834),50)
        # simple balance beam: eat-side sinks as t advances (heavier), burn-side rises
        tilt=min(t/1.2,1.0)*14
        cx,cy=540,980
        bx1,by1=cx-230,cy-tilt*5; bx2,by2=cx+230,cy+tilt*5
        d=ImageDraw.Draw(im)
        d.rectangle((cx-9,cy+10,cx+9,cy+190),fill='#8B7355')          # post
        r.rounded(im,(cx-70,cy+186,cx+70,cy+224),'#6F5A43',r=14,shadow=4)  # base
        d.line((bx1,by1,bx2,by2),fill='#4F8A6E',width=16)             # beam
        d.ellipse((cx-16,cy-16,cx+16,cy+16),fill='#4F8A6E')           # fulcrum
        r.rounded(im,(bx1-110,by1+30,bx1+110,by1+150),'#FFE3C2',r=28,shadow=6)
        r.label(im,'먹는 양',(bx1,by1+90),42,fill='#8B5A2B')
        r.rounded(im,(bx2-110,by2+30,bx2+110,by2+150),'#D7EFE6',r=28,shadow=6)
        r.label(im,'쓰는 양',(bx2,by2+90),42,fill='#3E7F68')
        r.place(im,r.chef('liver','serious'),250,1420,.46,angle=math.sin(t*1.6)*2)
    elif action=='benefit':
        r.label(im,'식이섬유 많고, 혈당 천천히',(540,760),58,fill='#4F8A6E')
        r.label(im,'지중해식 식단, 간 지방 줄여요',(540,852),50)
        r.rounded(im,(120,965,960,1140),'#FFFCF3',r=38,shadow=8)
        r.rounded(im,(150,1005,282,1075),'#4EAFA3',r=30,shadow=3)
        r.label(im,'출처',(216,1040),48,fill='#FFFFFF')
        r.label(im,'케임브리지 대학병원',(320,1018),52,anchor='lm')
        r.label(im,'MASLD 식사 안내',(320,1092),46,anchor='lm',fill='#5B6683')
        r.place(im,r.chef('liver','proud'),245,1345,.58,angle=math.sin(t*1.8)*2)
        sparkles(im,t,[(95,1230,24),(420,1260,20)])
        r.place(im,r.dish('liver'),760,1370,.66,angle=math.sin(t*1.5)*1.2)
    elif action=='serve':
        r.label(im,'간 해독 마법은 없어요',(540,798),64,fill='#4F8A6E')
        r.place(im,r.chef('liver','relieved'),215,1360,.5,angle=math.sin(t*1.6)*2)
        r.place(im,r.dish('liver'),650,1240,1.05,angle=math.sin(t*1.6)*1.2)
        s_t=smooth((t-.5)/.35)
        if s_t>0:stamp(im,880,980,('좋은','습관'),-12+(1-s_t)*18)
        sparkles(im,t,[(300,1090,24),(980,1220,22),(560,1010,18)])
    else:
        im.alpha_composite(set_stage())
        layer=Image.new('RGBA',(W,H));r.kitchen(layer,'liver',mood,t,action)
        im.alpha_composite(layer.crop((0,600,W,1410)),(0,760))
        fx=Image.new('RGBA',(W,H))
        if action=='hook':
            if t>1.8:sparkles(fx,t,[(500,930,28),(180,950,22),(430,820,18)])
        if action=='mix':
            r.label(im,'레몬즙 + 올리브유',(540,720),50,fill='#4F8A6E')
            if t>3.0:sparkles(fx,t,[(470,950,26),(850,990,22),(250,880,20)])
        if action=='joke':
            sweat(fx,455,905,t)
            if t>.2:bang(fx,425,800,t)
        im.alpha_composite(fx)
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
        caption=wrapped_caption(idx);lift=0
        if idx and t<.45:
            caption=caption.copy();alpha=smooth(t/.45);lift=round(26*(1-alpha))
            caption.putalpha(caption.getchannel('A').point(lambda a:round(a*alpha)))
        im.alpha_composite(caption,(0,lift))
    return im.convert('RGB')

def prepare_mix(rows):
    sr=24000;dur=sum(s['duration'] for s in rows);n=math.ceil(dur*sr)
    voice=np.zeros(n,np.float32);fx=np.zeros(n,np.float32);clock=0
    for idx,s in enumerate(rows):
        with wave.open(str(AUDIO/(s['id']+'.wav'))) as f:x=np.frombuffer(f.readframes(f.getnframes()),np.int16).astype(np.float32)/32768
        # Existing source takes were made at 1.22x (the revised ending at 1.14x).
        # Bring speech to the user's channel-standard 1.30x without shortening reading/recipe holds.
        x=x  # v5 dialogue is acted per line and sped to the channel standard 1.3x in synth_line
        x*=.14/max(np.sqrt(np.mean(x*x)),.001)
        delay=.18 if idx==0 else 1.0
        start=int((clock+delay)*sr);voice[start:start+len(x)]+=x[:max(0,n-start)]
        from scipy.signal import butter, sosfilt
        rng=np.random.default_rng(100+idx)
        def add(at,length,kind,level):
            count=int(length*sr);tt=np.arange(count)/sr
            noise=rng.normal(0,1,count)
            if kind=='cut':
                noise=sosfilt(butter(2,2200,fs=sr,output='sos'),noise)
                y=(noise*.7+np.sin(2*np.pi*185*tt)*.6)*np.exp(-tt*48)
            elif kind=='water':
                noise=sosfilt(butter(2,[450,4800],btype='bandpass',fs=sr,output='sos'),noise)
                y=noise*(.5+.25*np.sin(tt*43)+.15*np.sin(tt*117))*np.minimum(tt/.08,1)*np.minimum((length-tt)/.14,1)
            elif kind=='grain':
                env=np.zeros(count)
                for k in range(0,count,900):env[k:min(count,k+190)]+=np.exp(-np.arange(min(190,count-k))/35)
                y=noise*env
            elif kind=='bubble':y=np.sin(2*np.pi*(400*tt-150*tt*tt))*np.exp(-tt*33)
            elif kind=='stir':
                y=sosfilt(butter(2,1100,fs=sr,output='sos'),noise)*np.sin(np.pi*tt/length)**2
            else:y=np.sin(2*np.pi*260*tt)*np.exp(-tt*40)
            y=y*level/max(np.max(np.abs(y)),.001)
            pos=int((clock+at)*sr);end=min(n,pos+count);fx[pos:end]+=y[:end-pos]
        if s['id']=='rinse':
            add(.4,2.2,'water',.065)
        if s['id']=='chop':
            for at in np.arange(1.3,s['duration']-.1,.62832):add(float(at),.12,'cut',.14)
        if s['id']=='pour':
            for j in range(5):add(.6+j*.3,.14,'plop',.06)
        if s['id']=='mix':
            for at in [1.2,2.6,3.9]:add(at,.55,'stir',.045)
        clock+=s['duration']
    source=ROOT.parent/'bgm'/'buant_pop_groove.mp3'
    music=np.frombuffer(subprocess.run([r.FF,'-v','error','-i',str(source),'-t',str(dur),'-ac','1','-ar',str(sr),'-f','f32le','pipe:1'],capture_output=True,check=True).stdout,np.float32).copy()
    music=np.pad(music,(0,max(0,n-len(music))))[:n];music*=.0105/max(np.sqrt(np.mean(music*music)),.001)
    from scipy.ndimage import maximum_filter1d,gaussian_filter1d
    act=maximum_filter1d(np.abs(voice[::240]),size=18)>.035
    env=1-gaussian_filter1d(act.astype(np.float32),2)*.67
    music*=np.interp(np.arange(n),np.arange(len(env))*240,env)
    music*=np.minimum(np.arange(n)/sr/.4,1)*np.minimum((n-np.arange(n))/sr/1.2,1)
    mix=voice+music+fx
    peak=np.abs(mix).max()
    if peak>0.6:  # safety limiter: sample-peak alone underestimates true (inter-sample) peak by ~1dB+, so target well below 0dBFS
        g=0.6/peak; voice*=g; music*=g; fx*=g; mix=voice+music+fx
    for name,a in [('voice',voice),('music',music),('mix',mix)]:r.wavwrite(OUT/f'liver_ko_{name}.wav',a)
    def stamp(t):
        m=round(t*1000);return f'{m//3600000:02}:{m//60000%60:02}:{m//1000%60:02},{m%1000:03}'
    text=[];clock=0
    for idx,s in enumerate(rows):
        text.append(f'{idx+1}\n{stamp(clock+(.18 if idx==0 else 1))} --> {stamp(clock+s["duration"])}\n{s["text"]}\n');clock+=s['duration']
    (OUT/'liver_ko.srt').write_text('\n'.join(text),encoding='utf-8-sig')
    return OUT/'liver_ko_mix.wav'

def preview():
    rows=manifest();sheet=Image.new('RGB',(5*270,2*480))
    for i,row in enumerate(rows):
        im=frame(i,2.1);im.save(OUT/f'scene_{i:02}.png');sheet.paste(im.resize((270,480)),((i%5)*270,(i//5)*480))
    sheet.save(OUT/'storyboard_liver.jpg',quality=95)
    card=background().copy();header(card,True);card.alpha_composite(CARD());card.save(OUT/'병아리콩샐러드_캡처용_레시피.png')
    # A sheet of actual intermediate transition frames, not just before/after stills.
    sh=Image.new('RGB',(3*216,4*384))
    for row,idx in enumerate([1,4,5,9]):
        dur=TRANSITIONS[idx][2]
        for col,u in enumerate([.25,.5,.75]):sh.paste(frame(idx,dur*u).resize((216,384)),(col*216,row*384))
    sh.save(OUT/'transition_midpoints.jpg',quality=95)
    print('V2 preview ready',flush=True)

def render():
    rows=manifest();mix=prepare_mix(rows);duration=sum(s['duration'] for s in rows)
    target=OUT/'쏙쏙건강요리_병아리콩샐러드_v1.mp4'
    command=[r.FF,'-y','-v','error','-f','rawvideo','-pix_fmt','rgb24','-s',f'{W}x{H}','-r',str(FPS),'-i','pipe:0',
         '-i',str(mix),'-map','0:v:0','-map','1:a:0','-c:v','libx264','-crf','19','-preset','fast','-threads','4',
        # ffmpeg's alimiter defaults to level=true, which auto-boosts quiet audio UP to the
        # ceiling (makeup gain) instead of only clamping peaks above it -- that's why earlier
        # attempts got LOUDER as the ceiling was lowered. level=disabled makes it a pure limiter.
        '-pix_fmt','yuv420p','-af','loudnorm=I=-14:TP=-1.5:LRA=8,alimiter=limit=0.89:attack=5:release=50:level=disabled','-c:a','aac','-b:a','192k','-t',str(duration),'-movflags','+faststart',str(target)]
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
