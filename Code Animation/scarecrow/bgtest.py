import sys, time
from bg import *
from PIL import Image
for key in sys.argv[1:]:
    t0=time.time()
    Ls = season_layers(key)
    cp = Comp()
    cx, cy, z = WW/2, 700, 0.9
    cp.add(Ls['sky'].view(cx, cy, z))
    cp.add(Ls['cloud'].view(cx, cy, z))
    cp.add(Ls['land'].view(cx, cy, z))
    cp.add(Ls['fore'].view(cx, cy, z), blur=3)
    Image.fromarray(cp.finish(0)).save(f'test/bg_{key}.png')
    print(key, f'{time.time()-t0:.1f}s', flush=True)
