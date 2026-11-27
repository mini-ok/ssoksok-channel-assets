"""python3 run.py <에피소드> still out.png t1 t2 ...  |  one out.png t  |  frames outdir a b  |  info"""
import os, sys
import numpy as np, cv2
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import engine as E
from episodes import EP

def get(name):
    ep = EP[name]; eng = E.KINDS[ep['kind']](ep); ep['_eng'] = eng
    return ep, eng

if __name__ == '__main__':
    name, cmd = sys.argv[1], sys.argv[2]; ep, eng = get(name)
    if cmd == 'info':
        print(name, 'DUR', ep['DUR'], 't_end', ep['t_end'], 'frames', int(ep['DUR'] * E.FPS))
    elif cmd == 'still':
        ims = []
        for tt in map(float, sys.argv[4:]):
            im = (E.render(ep, eng, tt, 1) * 255).astype(np.uint8)
            cv2.putText(im, f'{tt:.1f}', (8, int(50 * E.SC)), 0, 1.4 * E.SC, (0, 255, 0), 2); ims.append(im)
        while len(ims) % 4: ims.append(np.zeros_like(ims[0]))
        cv2.imwrite(sys.argv[3], np.vstack([np.hstack(ims[i:i + 4]) for i in range(0, len(ims), 4)]))
    elif cmd == 'one':
        cv2.imwrite(sys.argv[3], (E.render(ep, eng, float(sys.argv[4]), 2) * 255).astype(np.uint8))
    elif cmd == 'frames':
        od = sys.argv[3]; os.makedirs(od, exist_ok=True); a, b = int(sys.argv[4]), int(sys.argv[5])
        for k in range(a, b):
            fn = os.path.join(od, f'f{k:05d}.png')
            if not os.path.exists(fn):
                cv2.imwrite(fn, (E.render(ep, eng, k / E.FPS, 2) * 255 + 0.5).astype(np.uint8))
