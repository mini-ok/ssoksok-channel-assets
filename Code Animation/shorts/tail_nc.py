import sys, os
os.environ['NOCREDIT'] = '1'
d, t0, t1, out = sys.argv[1], float(sys.argv[2]), float(sys.argv[3]), sys.argv[4]
os.chdir(d); sys.path.insert(0, d)
import render as R, multiprocessing as mp
a, b = int(round(t0 * R.FPS)), int(round(t1 * R.FPS)); m = (a + b) // 2
with mp.Pool(2) as p:
    p.map(R.render_chunk, [(a, m, out + '.p1.mp4'), (m, b, out + '.p2.mp4')])
open(out + '.txt', 'w').write(f"file '{out}.p1.mp4'\nfile '{out}.p2.mp4'\n")
os.system(f"ffmpeg -loglevel error -y -f concat -safe 0 -i {out}.txt -c copy {out}")
