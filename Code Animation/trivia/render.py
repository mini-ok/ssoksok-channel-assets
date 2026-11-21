"""프레임 렌더(두 프로세스) → PNG.
python3 render.py <에피소드> <out_dir> <t0> <t1> [samples]
python3 render.py <에피소드> --stills <out_dir> t1 t2 ...   (정지 화면 검사용, 실제 크기 PNG)
"""
import os, sys
from multiprocessing import Pool
import numpy as np, cv2
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import engine as E

EP = None; OUT = None; SAMP = 2


def job(k):
    p = os.path.join(OUT, f'f{k:05d}.png')
    if os.path.exists(p): return
    img = E.final(EP, k / E.FPS, SAMP)
    cv2.imwrite(p, np.clip(img * 255 + 0.5, 0, 255).astype(np.uint8))


if __name__ == '__main__':
    EP = E.Episode(sys.argv[1])
    E.tex()
    if sys.argv[2] == '--stills':
        OUT = sys.argv[3]; os.makedirs(OUT, exist_ok=True)
        for ts in sys.argv[4:]:
            t = float(ts); img = E.final(EP, t, SAMP)
            cv2.imwrite(os.path.join(OUT, f't{t:05.2f}.png'), np.clip(img * 255 + 0.5, 0, 255).astype(np.uint8))
        print('stills', OUT); sys.exit(0)
    OUT = sys.argv[2]; T0, T1 = float(sys.argv[3]), float(sys.argv[4])
    SAMP = int(sys.argv[5]) if len(sys.argv) > 5 else 2
    os.makedirs(OUT, exist_ok=True)
    ks = list(range(int(round(T0 * E.FPS)), int(round(min(T1, EP.DUR) * E.FPS))))
    with Pool(2) as pool:
        for i, _ in enumerate(pool.imap(job, ks, chunksize=4)):
            if i % 90 == 0: print(i, '/', len(ks), flush=True)
    print('done', flush=True)
