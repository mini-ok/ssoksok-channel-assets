"""Motion-energy based crop centres for 9:16 reframing.
usage: analyze.py name video.mp4 y0 h cuts_json   -> name_track.json  (per-frame crop centre x in source pixels)"""
import sys, json, subprocess, numpy as np, cv2
name, vid, y0, ph = sys.argv[1], sys.argv[2], int(sys.argv[3]), int(sys.argv[4])
cuts = json.loads(sys.argv[5])          # list of cut start times + [end]
SW, SH = 1920, 1080
sw, sh = 480, 270
p = subprocess.Popen(['ffmpeg', '-loglevel', 'error', '-i', vid, '-vf', f'scale={sw}:{sh}', '-f', 'rawvideo', '-pix_fmt', 'gray', '-'],
                     stdout=subprocess.PIPE)
fps = float(eval(subprocess.check_output(['ffprobe', '-v', 'error', '-select_streams', 'v', '-show_entries', 'stream=r_frame_rate',
                                          '-of', 'csv=p=0', vid]).decode().strip()))
frames = []
while True:
    b = p.stdout.read(sw * sh)
    if len(b) < sw * sh: break
    frames.append(np.frombuffer(b, np.uint8).reshape(sh, sw)[int(y0 * sh / SH):int((y0 + ph) * sh / SH)].astype(np.float32))
n = len(frames)
cw = ph * 4 / 5 * sw / SW                 # crop width in small pixels
E = np.zeros((n, sw), np.float32)
for i in range(1, n):
    d = np.abs(frames[i] - frames[i - 1])
    E[i] = d.sum(0)
# per-cut: remove global (camera) motion by subtracting the column median, smooth
cent = np.zeros(n)
cutf = [int(round(t * fps)) for t in cuts]
info = []
for a, b in zip(cutf[:-1], cutf[1:]):
    b = min(b, n)
    seg = E[a + 1:b].copy() if b - a > 2 else E[a:b].copy()
    seg = np.maximum(seg - np.median(seg, 1, keepdims=True) * 1.2, 0)
    tot = seg.sum(0)
    k = np.ones(int(cw)) / cw
    win = np.convolve(tot, k, 'same')
    lo, hi = cw / 2, sw - cw / 2
    xs = np.arange(sw)
    win[(xs < lo) | (xs > hi)] = 0
    strength = win.max() / (tot.sum() / sw + 1e-6) if tot.sum() > 0 else 0
    cx = float(np.argmax(win)) if strength > 1.15 else sw / 2
    # in-cut tracking: smoothed per-frame energy centroid, blended toward cut centre
    tr = []
    for i in range(a, b):
        j0, j1 = max(a, i - int(fps * 0.8)), min(b, i + int(fps * 0.8))
        e = np.maximum(E[j0:j1].sum(0) - np.median(E[j0:j1].sum(0)) * 1.2, 0)
        w_ = np.convolve(e, k, 'same'); w_[(xs < lo) | (xs > hi)] = 0
        tr.append(float(np.argmax(w_)) if e.sum() > 1e-3 and w_.max() > 0 else cx)
    tr = np.array(tr)
    tr = 0.5 * tr + 0.5 * cx
    tr = cv2.GaussianBlur(tr.reshape(-1, 1).astype(np.float64), (1, 0), fps * 0.6).ravel() if len(tr) > 3 else tr
    # limit pan speed inside a cut
    for i in range(1, len(tr)):
        tr[i] = tr[i - 1] + np.clip(tr[i] - tr[i - 1], -1.2, 1.2)
    cent[a:b] = tr * SW / sw
    info.append(dict(t0=a / fps, cx=round(cx * SW / sw), strength=round(float(strength), 2)))
cent[cutf[-1]:] = cent[min(cutf[-1], n) - 1] if cutf[-1] < n else cent[n - 1]
json.dump(dict(fps=fps, n=n, y0=y0, ph=ph, cent=[round(float(c), 1) for c in cent], cuts=cuts, info=info), open(f'{name}_track.json', 'w'))
for d in info: print(d)
