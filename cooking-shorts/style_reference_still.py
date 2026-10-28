"""Code-native paper-material style study using the channel's original puff renderer."""
from pathlib import Path
import numpy as np
from PIL import Image
from scipy.ndimage import gaussian_filter
import render as r
p=r.p
OUT=r.ROOT/'style_reference';OUT.mkdir(exist_ok=True)

def sprite(fn,w,h):
    b=fn(np.zeros((h,w,3),np.float32));wt=fn(np.ones((h,w,3),np.float32))
    a=np.clip(1-(wt-b).mean(2),0,1)
    rgb=np.divide(b,a[...,None],out=np.zeros_like(b),where=a[...,None]>.001)
    return Image.fromarray((np.concatenate([np.clip(rgb,0,1),a[...,None]],2)*255).astype('uint8'))

def paper_chip(text,size,color,angle=0):
    w=int(p.tw(text,size,'black'))+130;h=int(size*1.5)+90
    def fn(im):return p.chip(im,w,h,text,w/2,h/2,size,'black',p.hx(color),22,rot=angle,padx=43,pady=25)[0]
    return sprite(fn,w,h)

def caption():
    w,h=1010,266
    def fn(im):
        im=p.puff(im,p.rr(w,h,25,15,w-25,h-25,28),p.hx(0xFFFCF2),15,soft=9,shadow=(7,12),sh_blur=11,sh_k=.23,depth=.85)
        prefix='심장: 끓으면 ';focus='약불로!'
        size=62;x=(w-p.tw(prefix+focus,size,'jua'))/2
        im,_=p.put_text(im,w,h,prefix,x,101,size,'jua',p.TXT,shadow=False)
        im,_=p.put_text(im,w,h,focus,x+p.tw(prefix,size,'jua'),101,size,'jua',p.hx(0xE9776E),shadow=False)
        im,_=p.put_text(im,w,h,'저으면서 부드럽게 익혀요.',w/2,194,58,'jua',p.TXT,'c',shadow=False)
        return im
    return sprite(fn,w,h)

def ornament(color):
    def fn(im):
        im=p.puff(im,p.circ(140,140,65,62,45),p.hx(color),23,soft=6,shadow=(6,8),sh_blur=8,depth=.8)
        return p.puff(im,p.circ(140,140,65,60,16),p.hx(color)*.91,24,soft=4,shadow=(2,3),sh_blur=4,depth=.7)
    return sprite(fn,140,140)

def main():
    arr=p.bg(1080,1920,top=p.hx(0xE5EFEE),bot=p.hx(0xEBE6ED),seed=17)
    floor=p.bg(1080,450,top=p.hx(0xE2CFB1),bot=p.hx(0xE9D9C1),seed=31)
    arr[1470:]=floor
    im=Image.fromarray((arr*255).astype('uint8')).convert('RGBA')
    # Only two main message boards, as in the supplied channel reference.
    r.place(im,paper_chip('쏙쏙 건강백과',32,0xFFF9EA),225,111)
    r.place(im,paper_chip('쏙쏙 건강요리',37,0xFFF9EA),828,111)
    r.label(im,'오늘의 요리사 : 심장 쉐프',(540,224),49)
    r.place(im,paper_chip('바나나 오트밀',91,0xE98979,-2.5),540,371)
    r.place(im,paper_chip('재료 3개 / 5분',82,0x9DC7DE,1.5),540,556)
    def star_fn(img):
        return p.puff(img,p.star(460,460,220,215,195,rot=-82,inner=.56,rnd=13),p.hx(0xF2C341),14,
                      soft=14,shadow=(12,18),sh_blur=17,sh_k=.27,depth=1.1)
    r.place(im,sprite(star_fn,460,460),239,938,.86,angle=-8)
    r.label(im,'!',(236,936),148,style='heavy')
    # Strengthen visible material grain on the existing character without changing its design.
    character=r.chef('heart','happy').copy()
    a=np.asarray(character).astype(np.float32)
    texture=gaussian_filter(np.random.default_rng(29).normal(0,1,a.shape[:2]),.8)
    texture=texture/(texture.std()+1e-6)
    a[:,:,:3]=np.clip(a[:,:,:3]*(1+texture[:,:,None]*.014),0,255)
    character=Image.fromarray(a.astype('uint8'))
    r.place(im,character,700,1094,1.27,angle=-2)
    r.place(im,r.dish('heart'),330,1409,.69,angle=-3)
    r.place(im,r.prop('spoon'),947,1246,.56,angle=-12)
    for x,y,col,scale in [(934,746,0xE9A291,.68),(103,1224,0xEAA08A,.7),(949,1460,0x9DCDB9,.58)]:
        r.place(im,ornament(col),x,y,scale)
    r.place(im,caption(),540,1641)
    target=OUT/'종이질감_요리쇼츠_스타일비교.png';im.convert('RGB').save(target)
    print(target)
    # Compare the exact same cooking subject with the previous flat layout.
    import revision_v2 as v
    previous=v.frame(3,2.1).resize((540,960))
    after=im.convert('RGB').resize((540,960))
    board=Image.new('RGB',(1080,1024),'#F4F1EA');board.paste(previous,(0,64));board.paste(after,(540,64))
    r.label(board,'이전 시안',(270,32),31)
    r.label(board,'기존 채널 종이 질감 적용',(810,32),31)
    board.save(OUT/'종이질감_이전시안_비교.jpg',quality=95)

if __name__=='__main__':main()
