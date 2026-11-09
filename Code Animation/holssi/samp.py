import sys, time, importlib
from PIL import Image
mods = ['shots', 'shots_a', 'shots_b', 'shots_c', 'shots_d']
F = {}
for m in mods:
    try:
        M = importlib.import_module(m)
        for k in dir(M):
            if k[:1] == 'c' and k[1:].isdigit():
                F[k] = getattr(M, k)
    except ModuleNotFoundError:
        pass
names = []
for arg in sys.argv[1:]:
    fn, ts = arg.split(':'); t = float(ts)
    t0 = time.time()
    out = F[fn](t, int(t * 24)).finish(int(t * 24))
    p = f'test/{fn}_{t:05.2f}.png'
    Image.fromarray(out).save(p); names.append(p)
    print(fn, t, f'{time.time()-t0:.2f}s', flush=True)
if len(names) > 1:
    ims = [Image.open(p).crop((0, 20, 1920, 1060)).resize((960, 520), Image.LANCZOS) for p in names]
    cols = 2; rows = (len(ims) + 1) // 2
    sh = Image.new('RGB', (1920, 520 * rows), (0, 0, 0))
    for k, im in enumerate(ims):
        sh.paste(im, ((k % 2) * 960, (k // 2) * 520))
    sh.save('test/sheet.png')
