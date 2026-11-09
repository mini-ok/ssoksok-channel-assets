# -*- coding: utf-8 -*-
"""Multiplane test: three.js renders far/mid/near plates once (exact perspective & layout); each plate is repainted
once with the gouache engine and inked once; frames slide the plates at different speeds (parallax) on twos,
with a per-drawing line boil and painted light shafts. This is how cel films shot trucking shots."""
import sys, os, math, numpy as np, cv2
sys.path.insert(0, '/home/claude/scarecrow')
from painter import paint
from cel import film_post, INK_C, INK_W
from cel3d import edges as _edges, noise_field, shafts, PAPER

F32 = np.float32
H, W, PW = 1040, 1920, 3000
FOCAL = (H / 2) / math.tan(math.radians(38 / 2))
LAYERS = [('far', 17.0, (18, 9, 4.5), 0.9), ('mid', 10.0, (14, 7, 3.5), 1.3), ('near', 5.0, (12, 6, 3), 1.9)]

def rd(p, alpha=False):
    im = cv2.imread(p, cv2.IMREAD_UNCHANGED)
    if im.ndim == 3 and im.shape[2] == 4:
        rgb = im[..., [2, 1, 0]].astype(F32) / 255; a = im[..., 3].astype(F32) / 255
        return (rgb, a) if alpha else rgb
    return im[..., ::-1].astype(F32) / 255

def edges_plate(idp, nrm, dep, a):
    h, w = a.shape
    idk = (idp * 255).astype(np.int32)
    key = idk[..., 0] * 65536 + idk[..., 1] * 256 + idk[..., 2]
    e = np.zeros((h, w), bool)
    for dy, dx in ((0, 1), (1, 0), (1, 1)):
        e[:h - dy, :w - dx] |= key[:h - dy, :w - dx] != key[dy:, dx:]
    n = nrm * 2 - 1
    e[:, :-1] |= (n[:, :-1] * n[:, 1:]).sum(-1) < 0.15
    e[:-1] |= (n[:-1] * n[1:]).sum(-1) < 0.15
    am = (a > 0.5).astype(np.uint8)
    e |= cv2.morphologyEx(am, cv2.MORPH_GRADIENT, np.ones((3, 3), np.uint8)) > 0
    return e.astype(F32)

def build_plate(name, width_px):
    cache = f'plates/{name}_painted.npz'
    if os.path.exists(cache):
        z = np.load(cache); return z['rgb'], z['a'], z['ink'], z['inkc']
    rgb, a = rd(f'plates/{name}_color.png', alpha=True)
    idp = rd(f'plates/{name}_id.png')[..., :3]; nrm = rd(f'plates/{name}_normal.png')[..., :3]; dep = rd(f'plates/{name}_depth.png')[..., :3]
    # fill transparent area with a dilated colour so strokes at the edge don't pick up black
    fill = rgb.copy()
    mask = (a > 0.5).astype(np.uint8)
    inp = cv2.inpaint((rgb * 255).astype(np.uint8), 1 - mask, 5, cv2.INPAINT_TELEA).astype(F32) / 255
    radii = dict(LAYER_R)[name]
    painted = paint(inp, mask=cv2.dilate(mask, np.ones((5, 5), np.uint8)).astype(F32), radii=radii,
                    thresh=(0, 0.06, 0.10), maxlen=(7, 6, 4), seed=hash(name) % 1000, detail=0.6,
                    lenmul=np.ones(a.shape, F32) * 1.6)
    e = edges_plate(idp, nrm, dep, a)
    dt = cv2.distanceTransform((e < 0.5).astype(np.uint8), cv2.DIST_L2, 3)
    press = 1 + 0.3 * noise_field(*a.shape, 60, 7 + len(name))
    ink = np.clip(width_px * press - dt + 0.5, 0, 1)
    lum = (painted * np.array((0.3, 0.59, 0.11), F32)).sum(-1, keepdims=True)
    shade_side = np.clip(0.55 - lum, 0, 1) * 2
    inkc = painted * 0.30
    inkc = inkc * (1 - 0.5 * shade_side) + np.array(INK_C, F32) * 0.5 * shade_side
    inkc = inkc * (1 - 0.15 * (1 - shade_side)) + np.array(INK_W, F32) * 0.15 * (1 - shade_side)
    a2 = np.clip(cv2.GaussianBlur(a, (0, 0), 0.7), 0, 1)
    np.savez_compressed(cache, rgb=painted.astype(F32), a=a2.astype(F32), ink=ink.astype(F32), inkc=inkc.astype(F32))
    return painted, a2, ink, inkc

LAYER_R = [(n, r) for n, _, r, _ in LAYERS]

def sky_plate():
    cache = 'plates/sky_painted.npy'
    if os.path.exists(cache):
        return np.load(cache)
    yy = np.linspace(0, 1, H, dtype=F32)[:, None, None]
    top, mid, bot = np.array((0.80, 0.88, 0.80), F32), np.array((0.95, 0.96, 0.86), F32), np.array((0.74, 0.84, 0.74), F32)
    g = np.where(yy < 0.55, top + (mid - top) * (yy / 0.55), mid + (bot - mid) * ((yy - 0.55) / 0.45))
    g = np.broadcast_to(g, (H, PW, 3)).copy()
    glow = np.exp(-(((np.arange(PW)[None, :] - 1700) / 600.0) ** 2 + ((np.arange(H)[:, None] - 380) / 300.0) ** 2))[..., None]
    g = g + glow * np.array((0.06, 0.05, 0.0), F32)
    p = paint(np.clip(g, 0, 1).astype(F32), radii=(26, 13), thresh=(0, 0.04), maxlen=(8, 6), seed=5, detail=0.0,
              lenmul=np.ones((H, PW), F32) * 2.4, coh_w=np.ones((H, PW), F32) * 0.2)
    np.save(cache, p)
    return p

def cam_dx(t):
    tq = math.floor(t * 12) / 12
    return (tq - 1.5) * 0.55

def frame(t):
    dx = cam_dx(t)
    tq = int(t * 12)
    sky = sky_plate()
    off0 = (PW - W) // 2
    sh_far = dx * FOCAL / 30.0
    img = sky[:, int(off0 + sh_far):int(off0 + sh_far) + W].copy()
    mx, my = np.meshgrid(np.arange(W, dtype=F32), np.arange(H, dtype=F32))
    for li, (name, depth, _, wpx) in enumerate(LAYERS):
        rgb, a, ink, inkc = build_plate(name, wpx)
        sh = dx * FOCAL / depth
        x0 = off0 + sh
        ix = int(math.floor(x0)); fx = x0 - ix
        sl = (slice(None), slice(ix, ix + W + 1))
        def crop(arr):
            c = arr[sl]
            return c[:, :W] * (1 - fx) + c[:, 1:W + 1] * fx
        rgb_c, a_c, ink_c, inkc_c = crop(rgb), crop(a), crop(ink), crop(inkc)
        # line boil: ink only, new jitter every drawing (twos)
        jx = noise_field(H, W, 40, 300 + tq + li * 50) * 0.45; jy = noise_field(H, W, 40, 400 + tq + li * 50) * 0.45
        ink_c = cv2.remap(ink_c, mx + jx, my + jy, cv2.INTER_LINEAR)
        lay = rgb_c * (1 - ink_c[..., None]) + inkc_c * ink_c[..., None]
        al = np.clip(np.maximum(a_c, ink_c * (a_c > 0.02)), 0, 1)[..., None]
        img = img * (1 - al) + lay * al
        if name == 'mid':
            sv = shafts(t, 0.20)[..., None]
            img = img + sv * np.array((1.0, 0.95, 0.78), F32)
    img = np.clip(img * PAPER[..., None], 0, 1)
    out = film_post(img, t)
    full = np.zeros((1080, W, 3), np.uint8)
    full[20:20 + H] = (np.clip(out, 0, 1) * 255).astype(np.uint8)
    return full

if __name__ == '__main__':
    from PIL import Image
    mode = sys.argv[1]
    if mode == 'still':
        for a in sys.argv[2:]:
            Image.fromarray(frame(float(a))).save(f'mp_{float(a):04.2f}.png'); print(a, flush=True)
    else:
        import subprocess
        p = subprocess.Popen(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x1080', '-r', '24',
                              '-i', '-', '-c:v', 'libx264', '-crf', '18', '-pix_fmt', 'yuv420p', 'forest_multiplane.mp4'], stdin=subprocess.PIPE)
        for i in range(72):
            p.stdin.write(frame(i / 24).tobytes())
        p.stdin.close(); p.wait(); print('done')
