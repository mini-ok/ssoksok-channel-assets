"""vert.py name  -> name_shorts.mp4 (1080x1920). 4:5 picture window that follows each cut's subject,
blurred fill above/below, film title in the top band, 허상공방 credit typed in the bottom band at the end."""
import os, sys, json, subprocess, numpy as np, cv2
HERE = os.path.dirname(os.path.abspath(__file__))
VID = os.environ.get('VID_ROOT', '/home/claude')        # where the landscape v2 mp4s live (videos are not in git)
from PIL import Image, ImageDraw, ImageFont
sys.path.insert(0, os.path.join(HERE, '..', '_shared'))
import credit_overlay
CFG = {
 'keeper': dict(vid=VID + '/keeper/out/빛지기_THE_KEEPER_v2.mp4', tail=HERE + '/keeper_tail.mp4', tail_t=57.0,
                title='빛지기', sub='THE KEEPER', credit=59.0, end=67.0, band_out=57.4,
                keys={5: [(0, 1100)], 9: [(0, 330), (0.45, 640), (1, 1280)], 10: [(0, 935)], 11: [(0, 1320), (0.3, 1320), (1, 420)],
                      12: [(0, 1040), (0.5, 950), (1, 1165)], 14: [(0, 1150)], 16: [(0, 900)], 17: [(0, 770), (0.5, 770), (1, 1180)],
                      18: [(0, 1070), (0.12, 1090), (1, 1100)]}),
 'holssi': dict(vid=VID + '/holssi/out/홀씨_HOLSSI_v2.mp4', tail=HERE + '/holssi_tail.mp4', tail_t=86.0,
                title='홀씨', sub='HOLSSI', credit=89.2, end=97.0, band_out=87.0,
                keys={2: [(0, 780)], 5: [(0, 860)], 6: [(0, 950)], 9: [(0, 1000)], 10: [(0, 900)], 14: [(0, 800), (0.6, 800), (1, 930)],
                      18: [(0, 960)]}),
 'scarecrow': dict(vid=VID + '/scarecrow/out/허수아비의겨울_v2.mp4', tail=HERE + '/scarecrow_tail.mp4', tail_t=126.0,
                   title='허수아비의 겨울', sub='A SCARECROW\'S WINTER', credit=130.4, end=137.0,
                   keys={1: [(0, 1050)], 5: [(0, 1000)], 6: [(0, 1000), (0.5, 860), (1, 1130)], 11: [(0, 1150)], 15: [(0, 1100)],
                         19: [(0, 1000)], 23: [(0, 950), (0.62, 950), (0.75, 800), (1, 800)], 25: [(0, 1000)]}),
}
name = sys.argv[1]; C = CFG[name]
only = [float(x) for x in sys.argv[2:]]          # optional: still times -> PNGs instead of a video
d = json.load(open(f'{HERE}/{name}_track.json'))
fps, cent, cuts, y0, ph, n = d['fps'], np.array(d['cent']), d['cuts'], d['y0'], d['ph'], d['n']
cw = int(ph * 4 / 5) // 2 * 2
def sm(a, b, x):
    u = min(1.0, max(0.0, (x - a) / (b - a))); return u * u * (3 - 2 * u)
for ci, ks in C['keys'].items():
    a, b = int(round(cuts[ci - 1] * fps)), min(n, int(round(cuts[ci] * fps)))
    for i in range(a, b):
        u = (i - a) / max(1, b - a - 1); v = ks[-1][1]
        for (u0, x0), (u1, x1) in zip(ks[:-1], ks[1:]):
            if u0 <= u <= u1:
                v = x0 + (x1 - x0) * sm(u0, u1, u); break
        if u < ks[0][0]: v = ks[0][1]
        cent[i] = v
cent = np.clip(cent, cw / 2, 1920 - cw / 2)
W, H, PH = 1080, 1920, 1350; PY = (H - PH) // 2
# title plate (top band)
def text_layer():
    im = Image.new('RGBA', (W, PY), (0, 0, 0, 0)); dr = ImageDraw.Draw(im)
    f1 = ImageFont.truetype('/usr/share/fonts/opentype/noto/NotoSerifCJK-Medium.ttc', 76)
    f2 = ImageFont.truetype('/usr/share/fonts/opentype/noto/NotoSerifCJK-Light.ttc', 26)
    t = C['title']; w = dr.textlength(t, font=f1, features=None) + 10 * (len(t) - 1)
    x = (W - w) / 2
    for ch in t:
        dr.text((x + 2, 92 + 2), ch, font=f1, fill=(0, 0, 0, 120)); dr.text((x, 92), ch, font=f1, fill=(250, 244, 230, 255)); x += dr.textlength(ch, font=f1) + 10
    s = C['sub']; w = dr.textlength(s, font=f2) + 9 * (len(s) - 1); x = (W - w) / 2
    for ch in s:
        dr.text((x, 204), ch, font=f2, fill=(250, 240, 222, 215)); x += dr.textlength(ch, font=f2) + 9
    return np.asarray(im, np.float32) / 255
TL = text_layer()
feather = np.ones((H, 1, 1), np.float32)          # 1 inside the picture, fades over 36 px at its top/bottom edges
for k in range(36):
    feather[PY + k] = feather[PY + PH - 1 - k] = (k + 0.5) / 36
feather[:PY] = 0; feather[PY + PH:] = 0
def compose(src, i):
    t = i / fps
    x0 = int(round(cent[min(i, n - 1)] - cw / 2))
    crop = src[y0:y0 + ph, x0:x0 + cw]
    pic = cv2.resize(crop, (W, PH), interpolation=cv2.INTER_LANCZOS4)
    pic = cv2.addWeighted(pic, 1.35, cv2.GaussianBlur(pic, (0, 0), 1.6), -0.35, 0)
    small = cv2.resize(crop, (54, 96), interpolation=cv2.INTER_AREA)
    bg = cv2.GaussianBlur(cv2.resize(small, (W, H), interpolation=cv2.INTER_CUBIC), (0, 0), 30).astype(np.float32) * 0.5
    out = bg
    out[PY:PY + PH] = out[PY:PY + PH] * (1 - feather[PY:PY + PH]) + pic.astype(np.float32) * feather[PY:PY + PH]
    out /= 255
    fade = sm(0.3, 1.5, t) * (1 - sm(C['end'] - 1.2, C['end'] - 0.2, t))
    bo = C.get('band_out')
    a = TL[..., 3:4] * 0.92 * fade * ((1 - sm(bo, bo + 0.8, t)) if bo else 1.0)
    out[:PY] = out[:PY] * (1 - a) + TL[..., 2::-1] * a
    if t >= C['credit']:
        rgb = credit_overlay.apply(out[..., ::-1], t - C['credit'], 'center', bottom=196, alpha=fade)
        out = rgb[..., ::-1]
    return np.clip(out * 255, 0, 255).astype(np.uint8)
def reader(path, ss=None):
    cmd = ['ffmpeg', '-loglevel', 'error'] + (['-ss', str(ss)] if ss else []) + ['-i', path, '-f', 'rawvideo', '-pix_fmt', 'bgr24', '-']
    return subprocess.Popen(cmd, stdout=subprocess.PIPE, bufsize=1920 * 1080 * 3)
if only:
    for t in only:
        src_path, ss = (C['tail'], t - C['tail_t']) if t >= C['tail_t'] else (C['vid'], t)
        raw = subprocess.check_output(['ffmpeg', '-loglevel', 'error', '-ss', str(max(0, ss)), '-i', src_path, '-frames:v', '1', '-f', 'rawvideo', '-pix_fmt', 'bgr24', '-'])
        cv2.imwrite(f'{HERE}/{name}_v_{t:06.2f}.png', compose(np.frombuffer(raw, np.uint8).reshape(1080, 1920, 3), int(round(t * fps))))
    sys.exit()
outp = f'{HERE}/{name}_shorts.mp4'
enc = subprocess.Popen(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'bgr24', '-s', f'{W}x{H}', '-r', str(fps), '-i', '-',
                        '-i', C['vid'], '-map', '0:v', '-map', '1:a', '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '17', '-pix_fmt', 'yuv420p',
                        '-c:a', 'copy', '-shortest', '-movflags', '+faststart', outp], stdin=subprocess.PIPE)
tailf = int(round(C['tail_t'] * fps))
r = reader(C['vid']); i = 0; sz = 1920 * 1080 * 3
while i < n:
    if i == tailf:
        r.kill(); r = reader(C['tail'])
    b = r.stdout.read(sz)
    if len(b) < sz: break
    enc.stdin.write(compose(np.frombuffer(b, np.uint8).reshape(1080, 1920, 3), i).tobytes()); i += 1
    if i % 240 == 0: print(name, i, n, flush=True)
enc.stdin.close(); enc.wait(); print('done', outp, i)
