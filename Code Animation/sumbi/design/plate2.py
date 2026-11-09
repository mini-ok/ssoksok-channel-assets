# split-level plate: air above, underwater below (the film's motif: the surface)
import sys, math, numpy as np, cairo, cv2
sys.path.insert(0, '/home/claude/scarecrow')
from painter import paint
W, H = 2400, 1300; SURF = 560
rng = np.random.default_rng(8)
s = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H); c = cairo.Context(s)
g = cairo.LinearGradient(0, 0, 0, SURF)
for o, col in ((0, (0.62, 0.78, 0.90)), (1, (0.96, 0.93, 0.86))):
    g.add_color_stop_rgb(o, *col)
c.rectangle(0, 0, W, SURF); c.set_source(g); c.fill()
g = cairo.LinearGradient(0, SURF, 0, H)
for o, col in ((0, (0.30, 0.66, 0.70)), (0.4, (0.10, 0.42, 0.56)), (1, (0.03, 0.14, 0.28))):
    g.add_color_stop_rgb(o, *col)
c.rectangle(0, SURF, W, H - SURF); c.set_source(g); c.fill()
for k in range(14):                       # light shafts
    x = rng.uniform(0, W); w = rng.uniform(30, 120); sk = rng.uniform(-200, 200)
    c.move_to(x, SURF); c.line_to(x + w, SURF); c.line_to(x + w + sk + 80, H); c.line_to(x + sk - 40, H); c.close_path()
    c.set_source_rgba(0.80, 0.95, 0.92, 0.10); c.fill()
for k in range(9):                        # kelp
    x = 150 + k * 260 + rng.uniform(-60, 60)
    c.move_to(x, H)
    for j in range(8):
        c.line_to(x + 40 * math.sin(j * 0.9 + k), H - j * 70 - 40)
    c.set_line_width(26); c.set_source_rgba(0.10, 0.30, 0.22, 0.9); c.stroke()
# surface band (silver ceiling seen from both sides)
for x in range(0, W, 6):
    y = SURF + 10 * math.sin(x * 0.012) + 5 * math.sin(x * 0.041)
    c.rectangle(x, y - 3, 6, 9); c.set_source_rgba(0.95, 0.98, 0.96, 0.9); c.fill()
buf = np.ndarray((H, W, 4), np.uint8, s.get_data())[..., [2, 1, 0]].astype(np.float32) / 255
out = paint(buf, hint=np.zeros((H, W), np.float32), lenmul=np.ones((H, W), np.float32) * 2.0, seed=9, coh_w=np.ones((H, W), np.float32) * 0.4)
cv2.imwrite('plate2.png', (cv2.resize(out, (1920, 1040), interpolation=cv2.INTER_AREA)[..., ::-1] * 255).astype(np.uint8))
print('ok')
