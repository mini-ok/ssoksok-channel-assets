"""Episode 03: approved mushroom and egg scramble visual sample."""
import sys, math, json, subprocess
from pathlib import Path
from functools import lru_cache
from PIL import Image, ImageDraw
ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT.parent))
import revision_liver as v
r=v.r
OUT=ROOT/'preview_mushroom';OUT.mkdir(parents=True,exist_ok=True)
ROWS=[
 ('hook','오늘은 팬 잡는 날!','오늘은 버섯이랑 달걀! 팬 하나면 충분해요.','심장 쉐프'),
 ('mash','02  달걀을 살살 저어요','버섯을 먼저 볶고, 달걀을 넣어 완전히 익혀요.','심장 쉐프'),
 ('serve','팬 하나로 간단하게!','버섯의 감칠맛에 폭신한 달걀! 한 접시 완성!','심장 쉐프'),
 ('end','캡처해서 간식으로!','구독은 사원증 발급! 좋아요는 보너스!','심장 쉐프')]
v.SPEAKER={'심장 쉐프':('심장 쉐프',0xF0A0A8)}
v.manifest=lambda:[dict(id=a,title=b,text=c,speaker=d,duration=5) for a,b,c,d in ROWS]
v.KEYWORDS={'mash':{'꾹꾹!','포크로'},'serve':{'콕!'}}

@lru_cache(None)
def dip():
 im=Image.new('RGBA',(900,650));d=ImageDraw.Draw(im)
 d.rounded_rectangle((680,280,895,335),22,fill='#A77C59')
 d.ellipse((75,140,805,555),fill='#687B7D');d.ellipse((95,153,785,520),fill='#34474A')
 for i in range(42):
  a=i*2.399;rr=math.sqrt(i/42);x=440+rr*285*math.cos(a);y=330+rr*130*math.sin(a)
  d.rounded_rectangle((x-40,y-23,x+42,y+23),18,fill=['#F5D877','#FFE69C','#E9BF59'][i%3])
 for i in range(9):
  a=i*2.399;x=440+235*math.cos(a);y=325+95*math.sin(a)
  d.pieslice((x-46,y-37,x+46,y+37),180,360,fill='#B69B80')
  d.rectangle((x-12,y-5,x+12,y+32),fill='#E4D4BA')
 return r.paperize(im,seed=51)

def fork(im,t):
 x=650+65*math.sin(t*3);y=1170+22*math.cos(t*3)
 d=ImageDraw.Draw(im)
 d.line((x+90,y-190,x,y),fill='#BB916C',width=24)
 d.rounded_rectangle((x-45,y-30,x+45,y+50),20,fill='#D8AF7F')
 for k in [-18,0,18]:d.line((x+k,y-10,x+k,y+34),fill='#B58B62',width=5)

def card(im):
 r.rounded(im,(72,285,1008,1510),'#FFFCF3',45,11)
 entries=[('버섯 달걀볶음',390,76),('1인 곁들임 / 약 5분',490,44),
 ('재료',610,54),('양송이버섯 100g · 달걀 2개',700,51),('식용유 1작은술',780,45),
 ('소금·후추 약간 (선택)',860,48),('만드는 법',980,54),
 ('1  버섯을 손질해 얇게 썰어요.',1070,49),('2  팬에 기름을 두르고 버섯을 볶아요.',1160,44),
 ('3  푼 달걀을 넣고 중약불로 저어요.',1250,45),('4  흐르는 달걀 없이 익히면 완성!',1340,47)]
 for text,y,size in entries:r.label(im,text,(540,y),size,fill='#638B77' if text in ['재료','만드는 법'] else v.INK,maxw=850)

def frame(idx,t):
 im=v.background().copy()
 r.place(im,v.sty.paper_chip('쏙쏙 건강백과',38,0xFFF9EA),235,108)
 r.place(im,v.sty.paper_chip('쏙쏙 건강요리',44,0xE2F3EC),815,108)
 r.place(im,v.sty.paper_chip('오늘의 요리사 : 심장 쉐프',48,0xF0DBA0),540,222)
 if idx==3:
  card(im);r.label(im,'구독은 사원증 발급!',(540,1630),59);r.label(im,'좋아요는 보너스!',(540,1725),67,fill='#638B77')
 else:
  r.place(im,v.sty.paper_chip('버섯 달걀볶음',80,0x5BB8AA,-2),540,365)
  r.place(im,v.sty.paper_chip(ROWS[idx][1],64,0x9DC7DE,1),540,565)
  r.place(im,r.chef('heart','sparkle' if idx!=1 else 'serious'),235,1110,.74,angle=math.sin(t*2)*2)
  r.place(im,dip(),690,1255,.88)
  if idx==1:fork(im,t)
  else:
   r.place(im,r.prop('oil'),850,980,.46,angle=math.sin(t*2)*8)
   v.sparkles(im,t,[(510,930,25),(900,1140,22)])
  im.alpha_composite(v.wrapped_caption(idx))
 return im.convert('RGB')

if __name__=='__main__':
 sheet=Image.new('RGB',(1080,960))
 for i in range(4):
  image=frame(i,2.1);image.save(OUT/f'scene_{i}.png');sheet.paste(image.resize((270,480)),(270*i,0))
 # Single horizontal storyboard, keeping source stills available at full size.
 sheet=sheet.crop((0,0,1080,480));sheet.save(OUT/'storyboard.jpg',quality=95)
 command=[r.FF,'-y','-v','error','-f','rawvideo','-pix_fmt','rgb24','-s','1080x1920','-r','24','-i','pipe:0','-an','-c:v','libx264','-preset','ultrafast','-crf','23','-pix_fmt','yuv420p','-movflags','+faststart',str(OUT/'버섯달걀볶음_동작시안_무음.mp4')]
 p=subprocess.Popen(command,stdin=subprocess.PIPE)
 for n in range(72):p.stdin.write(frame(1,n/24).tobytes())
 p.stdin.close();assert p.wait()==0
 subprocess.run([r.FF,'-v','error','-i',str(OUT/'버섯달걀볶음_동작시안_무음.mp4'),'-f','null','-'],check=True)
 print('Sample rendered and fully decoded',flush=True)
