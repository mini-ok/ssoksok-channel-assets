"""프레임 렌더(두 프로세스) → PNG.  python3 render.py out_dir t0 t1 [samples]"""
import os, sys
from multiprocessing import Pool
import numpy as np, cv2
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import scene as S

def job(k):
    p = os.path.join(OUT, f'f{k:05d}.png')
    if os.path.exists(p): return
    img = S.final(k / S.FPS, SAMP)
    cv2.imwrite(p, np.clip(img * 255 + 0.5, 0, 255).astype(np.uint8))

OUT = sys.argv[1]; T0, T1 = float(sys.argv[2]), float(sys.argv[3]); SAMP = int(sys.argv[4]) if len(sys.argv) > 4 else 3
if __name__ == '__main__':
    os.makedirs(OUT, exist_ok=True)
    S.tex()
    ks = list(range(int(round(T0 * S.FPS)), int(round(T1 * S.FPS))))
    with Pool(2) as pool:
        for i, _ in enumerate(pool.imap(job, ks, chunksize=4)):
            if i % 60 == 0: print(i, '/', len(ks), flush=True)
    print('done', flush=True)
