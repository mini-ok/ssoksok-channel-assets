# 컷 mp4의 프레임별 선명도(라플라시안 분산)를 이웃 프레임 중앙값과 비교해 통째로 번진 프레임을 찾는다.
# 사용: python3 sharp_frames.py <mp4…>
import subprocess, numpy as np, sys, os
W,H=320,180
def frames(p):
    pr=subprocess.run(['ffmpeg','-v','error','-i',p,'-vf',f'scale={W}:{H},format=gray','-f','rawvideo','-'],capture_output=True)
    a=np.frombuffer(pr.stdout,np.uint8); return a.reshape(-1,H,W).astype(np.float32)
for p in sys.argv[1:]:
    F=frames(p)
    lap=lambda g: (g[1:-1,2:]+g[1:-1,:-2]+g[2:,1:-1]+g[:-2,1:-1]-4*g[1:-1,1:-1]).var()
    s=np.array([lap(g) for g in F]); n=len(s)
    bad=[]
    for i in range(n):
        lo,hi=max(0,i-12),min(n,i+13); med=np.median(s[lo:hi])
        if s[i]<0.35*med: bad.append(i)
    print(os.path.basename(p), n, 'med', round(float(np.median(s)),1), 'blurry frames:', bad[:40])
