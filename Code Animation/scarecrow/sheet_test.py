from cel import *
from PIL import Image
cp = Comp()
d = dyn(); c = d.c
vgrad(c, 0, 0, W, H, [(0, (0.93, 0.90, 0.82)), (1, (0.86, 0.82, 0.72))])
cp.add(d.rgba())
d = dyn(); c = d.c
jiibi(c, 300, 960, 2.4, dict(), t=0.0)
jiibi(c, 800, 960, 2.4, dict(wind=0.8, flapL=0.7, flapR=0.9, billow=0.8, lean=4, head_tilt=8, hat_tilt=6), t=0.3)
jiibi(c, 1300, 960, 2.4, dict(hat_down=1.0, head_turn=-0.6, head_tilt=-8, leaf=1.0, pocket=3), t=0.6)
jiibi(c, 1760, 960, 2.4, dict(wrapL=1.0, bend=-14, lean=-4, snow=1.0, frost=0.8, head_tilt=-16, wind=-0.6), t=0.9)
kongi(c, 1300 + 0, 960 - 2.4 * 300, 34, dict(face=1), t=0.6)
kongi(c, 120, 980, 46, dict(puff=1.25, tilt=-8), t=0.0)
kongi(c, 520, 980, 46, dict(wing=1.0, open_beak=1.0), t=0.0)
hawk(c, 1000, 160, 60, 0.3, 1.2)
dragonfly(c, 640, 120, 30, 0.2, 0.0)
cp.add(d.rgba())
cp.post.append(lambda img: film_post(img, 0.0))
Image.fromarray(cp.finish(0)).save('test/modelsheet_v1.png')
