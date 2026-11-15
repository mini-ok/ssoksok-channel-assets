# 컷 mp4에서 검은 프레임(평균 밝기 < 8)·평평한 프레임(표준편차 < 4)을 찾는다(벽 뒷면에 카메라가 막힌 경우 등).
# 사용: python3 black_frames.py <mp4…>
import subprocess, numpy as np, sys, os
for p in sys.argv[1:]:
    pr=subprocess.run(['ffmpeg','-v','error','-i',p,'-vf','scale=64:36,format=gray','-f','rawvideo','-'],capture_output=True)
    a=np.frombuffer(pr.stdout,np.uint8).reshape(-1,36,64).astype(np.float32)
    m=a.mean((1,2)); dark=[i for i,v in enumerate(m) if v<8]
    # also "mostly flat" frames (std small)
    flat=[i for i in range(len(a)) if a[i].std()<4 and i not in dark]
    def rng(L):
        out=[];
        for i in L:
            if out and i==out[-1][1]+1: out[-1][1]=i
            else: out.append([i,i])
        return out
    print(os.path.basename(p), 'dark', rng(dark), 'flat', rng(flat))
