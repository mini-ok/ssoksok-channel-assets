import time, numpy as np, cv2
from bg import *
from painter import paint
from PIL import Image
key='dawn'
Ls = season_layers(key)
def full(st):
    return st.view(WW/2, WH/2, 1.0) if False else None
# composite world-size underpainting
canvas = np.zeros((WH, WW, 3), F32)
sky = Ls['sky'].img.astype(F32)/255; cl = Ls['cloud'].img.astype(F32)/255; ld = Ls['land'].img.astype(F32)/255
for L_ in (sky, cl, ld):
    a = L_[..., 3:4]; canvas = L_[..., :3] + canvas * (1 - a)
hint = np.zeros((WH, WW), F32)        # horizontal by default
yy = np.arange(WH, dtype=F32)[:, None] * np.ones((1, WW), F32)
lenmul = np.where(yy < HOR - 160, 2.6, np.where(yy < HOR + 10, 1.4, 2.0)).astype(F32)
bal = np.where(yy < HOR - 160, 0.18, 0.45).astype(F32)
t0=time.time()
out = paint(canvas, hint=hint, seed=3, lenmul=lenmul, balpha_map=bal)
print('paint', time.time()-t0)
Image.fromarray((np.clip(canvas,0,1)*255).astype(np.uint8)).save('test/under.png')
Image.fromarray((np.clip(out,0,1)*255).astype(np.uint8)).save('test/painted.png')
