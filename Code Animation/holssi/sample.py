import sys, time
from PIL import Image
from shots import *
for arg in sys.argv[1:]:
    sid, ts = arg.split(':'); sid = int(sid); t = float(ts)
    a, b, fn = SHOTS[sid]
    t0 = time.time()
    cp = fn(t, int(t * 24))
    out = cp.finish(int(t * 24))
    Image.fromarray(out).save(f'test/s{sid:02d}_{t:05.2f}.png')
    print(sid, t, f'{time.time()-t0:.2f}s', flush=True)
