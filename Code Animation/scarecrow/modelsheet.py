from cel import *
from PIL import Image, ImageDraw, ImageFont
cp = Comp(); cp.vig = 0.15
d = dyn(); c = d.c
vgrad(c, 0, 0, W, H, [(0, (0.95, 0.92, 0.85)), (1, (0.89, 0.85, 0.76))])
for k in range(5):
    line(c, 40, 900 - k * 0, W - 40, 900, 1.5, (0.75, 0.70, 0.60), 0.6)
cp.add(d.rgba())
d = dyn(); c = d.c
S = 1.9
jiibi(c, 220, 900, S, dict(), t=0.0)
jiibi(c, 650, 900, S, dict(wind=0.9, flapL=0.8, flapR=0.95, billow=1.0, lean=4, head_tilt=8, hat_tilt=8), t=0.3)
jiibi(c, 1090, 900, S, dict(hat_down=1.0, head_turn=-0.7, head_tilt=-10, leaf=1.0, pocket=3, flapL=-0.4, flapR=-0.3), t=0.6)
kongi(c, 1170, 900 - S * 300 + 6, 26, dict(face=-1, puff=1.25, tilt=-10), t=0.6)
def nest(cc):
    kongi(cc, -2, -199, 11, dict(puff=1.45, tilt=-16, feet=0), t=0.9)
jiibi(c, 1520, 900, S, dict(wrapL=1.0, bend=-26, lean=-5, head_tilt=-28, head_turn=-0.35, snow=1.0, frost=0.8, flapR=-0.75,
                             wind=1.0, goreum_wind=1.0), t=0.9, chest_fn=nest)
# sparrow turnaround (bottom right)
kongi(c, 1830, 520, 30, dict(), t=0.0)
kongi(c, 1830, 680, 30, dict(blink=1, puff=1.3), t=0.0)
kongi(c, 1830, 840, 30, dict(wing=1.0, open_beak=1.0), t=0.0)
hawk(c, 1760, 150, 46, heading=0.15, flap=1.2)
dragonfly(c, 1560, 120, 26, 0.2, 0.0)
cp.add(cel_finish(d.rgba(), 0.0))
cp.post.append(lambda img: film_post(img, 0.0, halo=0.15))
out = cp.finish(0)
im = Image.fromarray(out)
dr = ImageDraw.Draw(im)
f = ImageFont.truetype('/usr/share/fonts/opentype/noto/NotoSansCJK-Medium.ttc', 26, index=1)
fs = ImageFont.truetype('/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc', 19, index=1)
lab = [(220, '기본', '바람이 없으면 축 처짐'), (650, '바람', '소매·고름·짚이 펄럭임'), (1090, '민망함 (C8)', '모자 챙이 눈을 덮고 고개를 돌림, 볼에 단풍잎'),
       (1520, '바람을 거스름 (C17)', '몸을 굽혀 소매로 콩이를 감쌈')]
for x, a, b in lab:
    dr.text((x - dr.textlength(a, font=f) / 2, 958), a, font=f, fill=(60, 52, 48))
    dr.text((x - dr.textlength(b, font=fs) / 2, 994), b, font=fs, fill=(100, 90, 80))
dr.text((1760, 870), '콩이', font=f, fill=(60, 52, 48))
dr.text((1712, 906), '기본 · 졸음 · 날갯짓', font=fs, fill=(100, 90, 80))
dr.text((40, 34), '〈허수아비의 겨울〉 모델 시트', font=f, fill=(60, 52, 48))
im.save('test/modelsheet.png')
