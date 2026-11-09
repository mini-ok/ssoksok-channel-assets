from engine import *
from PIL import Image
fr=Frame(1.0)
sky(fr,[(0,(0.05,0.06,0.10)),(1,(0.12,0.14,0.22))])
fr.camera(W/2,H/2)
c=fr.c
c.rectangle(0,700,W,200); fillc(c,(0.08,0.09,0.12))
robot(fr,260,700-41*6,6.0,dict(armF=(40,30),armB=(-15,20)),light=1.0,t=1.0)
robot(fr,620,700-41*6,6.0,dict(armF=(30,20)),light=0.9,inner='toy',t=1.0)
child(fr,900,700-21*7,7,dict(mode='stand',legF=(5,0),legB=(-5,0),armF=(80,20),fl_on=1.0,mouth=1,fl_len=120,fl_w=25),t=1)
boat(fr,1500,520,4.2,0.05,childP=dict(armF=(100,10),fl_on=1,brow=1.0,mouth=-1,fl_len=150,fl_w=30),t=1)
img=develop(fr); out=finalize(img,0)
Image.fromarray(out).save('test/charsheet2.png')
