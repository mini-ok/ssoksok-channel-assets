"""python3 render.py --stills out_dir t1 t2 ...   |   python3 render.py out.mp4 [W H] [t0 t1]"""
import sys, os, subprocess, numpy as np, cv2
import mv3 as S, nums as N
a = sys.argv[1:]
if a[0] == '--stills':
    os.makedirs(a[1], exist_ok=True)
    W, H = (int(os.environ.get('W', 960)), int(os.environ.get('H', 540)))
    for ts in a[2:]:
        t = float(ts); cv2.imwrite(f'{a[1]}/t{t:05.2f}.jpg', (S.frame(t, W, H, int(t * N.FPS)) * 255).astype(np.uint8), [cv2.IMWRITE_JPEG_QUALITY, 92])
else:
    out = a[0]; W, H = (int(a[1]), int(a[2])) if len(a) > 2 else (960, 540)
    t0, t1 = (float(a[3]), float(a[4])) if len(a) > 4 else (0.0, N.DUR)
    p = subprocess.Popen(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'bgr24', '-s', f'{W}x{H}', '-r', str(N.FPS), '-i', '-',
                          '-c:v', 'libx264', '-crf', '16', '-preset', 'medium', '-pix_fmt', 'yuv420p', out], stdin=subprocess.PIPE)
    for k in range(int(round(t0 * N.FPS)), int(round(t1 * N.FPS))):
        p.stdin.write((S.frame(k / N.FPS, W, H, k) * 255).astype(np.uint8).tobytes())
    p.stdin.close(); p.wait()
