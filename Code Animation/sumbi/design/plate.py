# painterly Jeju sea plate for the title/credit mockups (ending wide shot)
import sys, math, numpy as np, cairo, cv2
sys.path.insert(0, '/home/claude/scarecrow')
from painter import paint
W, H = 2400, 1300; HOR = 430
rng = np.random.default_rng(3)
s = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H); c = cairo.Context(s)
g = cairo.LinearGradient(0, 0, 0, HOR)
for o, col in ((0, (0.47, 0.66, 0.86)), (0.7, (0.78, 0.86, 0.92)), (1, (0.98, 0.92, 0.82))):
    g.add_color_stop_rgb(o, *col)
c.rectangle(0, 0, W, HOR); c.set_source(g); c.fill()
for (x, y, w, h) in ((400, 200, 520, 70), (1300, 150, 700, 90), (2000, 250, 480, 60), (900, 330, 400, 34)):
    for k in range(9):
        cx = x + rng.uniform(-w / 2, w / 2); r = h * rng.uniform(0.5, 1.0)
        c.arc(cx, y + rng.uniform(-h * 0.2, h * 0.2), r, 0, 6.3); c.set_source_rgba(1, 0.99, 0.97, 0.9); c.fill()
# Hallasan + coastline silhouette
c.move_to(0, HOR); 
pts = [(0, HOR - 20), (300, HOR - 40), (700, HOR - 120), (950, HOR - 150), (1200, HOR - 115), (1500, HOR - 50), (1800, HOR - 30), (2400, HOR - 18)]
for p in pts: c.line_to(*p)
c.line_to(2400, HOR); c.close_path(); c.set_source_rgb(0.52, 0.62, 0.70); c.fill()
g = cairo.LinearGradient(0, HOR, 0, H)
for o, col in ((0, (0.30, 0.52, 0.66)), (0.35, (0.16, 0.42, 0.58)), (1, (0.10, 0.48, 0.56))):
    g.add_color_stop_rgb(o, *col)
c.rectangle(0, HOR, W, H - HOR); c.set_source(g); c.fill()
for _ in range(2600):                      # wave strokes / glitter
    y = HOR + (rng.random() ** 1.6) * (H - HOR); k = (y - HOR) / (H - HOR)
    x = rng.uniform(0, W); L = 10 + 120 * k
    near_sun = math.exp(-((x - 1500) / 380) ** 2) * (1 - k * 0.6)
    col = (0.96, 0.94, 0.86) if rng.random() < 0.15 + 0.6 * near_sun else ((0.22, 0.56, 0.68) if rng.random() < 0.5 else (0.08, 0.32, 0.46))
    c.move_to(x, y); c.line_to(x + L, y + rng.uniform(-1, 1)); c.set_line_width(1 + 5 * k); c.set_source_rgba(*col, 0.85); c.stroke()
for (x, y, r) in ((900, 820, 26), (1250, 700, 18), (1600, 900, 30), (1950, 760, 20), (600, 1000, 34), (1420, 1080, 38)):
    c.save(); c.translate(x, y); c.scale(1, 0.55); c.arc(0, 0, r, 0, 6.3); c.restore(); c.set_source_rgb(0.96, 0.46, 0.12); c.fill()
    c.save(); c.translate(x, y + r * 0.2); c.scale(1.3, 0.35); c.arc(0, 0, r, 0, 6.3); c.restore(); c.set_source_rgba(1, 1, 1, 0.5); c.set_line_width(2); c.stroke()
    c.arc(x - r * 1.3, y - r * 0.15, r * 0.42, 0, 6.3); c.set_source_rgb(0.08, 0.08, 0.10); c.fill()
buf = np.ndarray((H, W, 4), np.uint8, s.get_data())[..., [2, 1, 0]].astype(np.float32) / 255
hint = np.zeros((H, W), np.float32)
lm = np.ones((H, W), np.float32) * 2.0
out = paint(buf, hint=hint, lenmul=lm, seed=5, coh_w=np.where(np.arange(H)[:, None] < HOR, 0.25, 0.6).astype(np.float32) * np.ones((1, W), np.float32))
img = cv2.resize(out, (1920, 1040), interpolation=cv2.INTER_AREA)
cv2.imwrite('plate.png', (img[..., ::-1] * 255).astype(np.uint8))
print('ok')
