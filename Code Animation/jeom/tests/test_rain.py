"""붓으로 그린 비 시험: 폭풍 하늘 위(먹색 빗줄기)와 번개 순간(밝은 빗줄기)."""
import sys, os, math
HERE = os.path.dirname(os.path.abspath(__file__)); JE = os.path.dirname(HERE)
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(JE, 'engine'))
import numpy as np, cv2
import test_flight as TF
from rain import InkRain
from look import INK_ABS, light, film, letterbox
W, H = 960, 540
R = InkRain(W, H, fib=TF.FIB)
out = []
for t, fx in ((1.0, 0.0), (1.0 + 1 / 12, 0.0), (2.0, 1.0)):
    d = TF.sky(t)
    rn = R.render(t, amount=1.0, gust=0.7)
    dens = d * (1 - 0.6 * fx) + rn * 0.55 * (1 - fx)
    img = TF.PAPER * np.exp(-dens[..., None] * INK_ABS)
    img = img + (rn * 0.35 * fx)[..., None]
    img = light(img, 'night', extra=fx) * 0.45 + light(img, 'silver', extra=fx) * 0.75
    img = letterbox(film(img, t, H=H, W=W, vig=0.25, grain=0.012, weave=0.3))
    out.append((np.clip(img, 0, 1)[..., ::-1] * 255).astype(np.uint8))
cv2.imwrite(os.path.join(JE, 'cache', 'rain_a.png'), out[0])
cv2.imwrite(os.path.join(JE, 'cache', 'rain_sheet.png'), np.vstack([np.hstack(out[:2]), np.hstack([out[2], out[2] * 0])]))
