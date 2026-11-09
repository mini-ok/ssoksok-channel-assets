# -*- coding: utf-8 -*-
"""솔이 / 꾸럭이 model sheet (1920x1080)"""
import sys, math, numpy as np, cairo
sys.path.insert(0, '/home/claude/sumbi/char')
from sol import sol_front, sol_side, head_front, kuruk, PAL, L0
from cel import set_frame, Boil
from PIL import Image, ImageDraw, ImageFont

W, H = 1920, 1080
surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H); c = cairo.Context(surf)
c.set_source_rgb(0.95, 0.93, 0.87); c.paint()
set_frame(0.0)
sol_front(c, 330, 990, 1.55, dict(), t=0)
sol_side(c, 760, 990, 1.55, dict(), t=0)
# head CUs: three mouth shapes + blink + wide
B = Boil(0, salt=31)
for k, (lab, P) in enumerate((('닫힘', dict(mouth=0)), ('반', dict(mouth=1)), ('열림', dict(mouth=2)),
                              ('깜빡', dict(eyes='blink', mouth=0)), ('놀람', dict(eyes='wide', mouth=2, brow=1)),
                              ('웃음', dict(mouth=0, smile=1, eyes='blink')))):
    cx, cy = 1150 + (k % 3) * 250, 250 + (k // 3) * 300
    c.save(); c.translate(cx, cy); c.scale(1.45, 1.45)
    head_front(c, P, B, L0, PAL, 2.6 / 1.45)
    c.restore()
for k, st in enumerate(('grey', 'orange', 'white', 'pink')):
    kuruk(c, 1170 + k * 170, 890, 2.0, st, t=0)
surf.flush()
img = np.ndarray((H, W, 4), np.uint8, surf.get_data())[..., [2, 1, 0]].copy()
im = Image.fromarray(img); d = ImageDraw.Draw(im)
f = ImageFont.truetype('/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc', 26, index=1)
fb = ImageFont.truetype('/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc', 34, index=1)
d.text((60, 36), '솔이 (9) · 꾸럭이 — 모델 시트 v1', font=fb, fill=(40, 36, 34))
for (x, y, s) in ((250, 1010, '정면'), (700, 1010, '옆'), (1130, 82, '입모양 · 표정')):
    d.text((x, y), s, font=f, fill=(70, 64, 60))
for k, s in enumerate(('닫힘', '반', '열림', '깜빡', '놀람', '웃음')):
    d.text((1120 + (k % 3) * 250, 360 + (k // 3) * 300), s, font=f, fill=(70, 64, 60))
for k, s in enumerate(('마름(잿빛)', '기쁨(주황)', '겁(하양)', '반가움(분홍)')):
    d.text((1120 + k * 170, 970), s, font=f, fill=(70, 64, 60))
im.save('/home/claude/sumbi/char/model_sheet_v1.png')
print('ok')
