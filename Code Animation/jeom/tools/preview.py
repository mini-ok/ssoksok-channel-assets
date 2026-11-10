"""컨펌용 짧은 미리보기: 지정 구간을 (기본 960×540으로) 렌더하고 최종 소리를 붙인 mp4를 만든다.
사용: JEOM_SCALE=1 python3 tools/preview.py <시작초> <끝초> <out.mp4> [wav]
- 상태가 있는 컷(유체·번짐)은 구간 시작이 컷 중간이면 상태가 비어 조금 다르게 보인다(미리보기 용도로는 충분).
- C17은 tests/test_leap.py가 만든 cache/leap_1920 프레임을 줄여 쓴다(없으면 해당 배율 leap 폴더).
"""
import os, sys, subprocess, tempfile
J = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('JEOM_SCALE', '1')
sys.path[:0] = [J, os.path.join(J, 'engine'), os.path.join(J, 'tests')]
import animatic3 as A, cv2

t0, t1, out = float(sys.argv[1]), float(sys.argv[2]), sys.argv[3]
wav = sys.argv[4] if len(sys.argv) > 4 else os.path.join(J, 'cache', 'jeom_final.wav')
A.A2.build_dot()
tmp = tempfile.mkdtemp(prefix='jeom_prev_')
k0, k1 = int(round(t0 * A.FPS)), int(round(t1 * A.FPS))
for k in range(k0, k1):
    t = k / A.FPS
    leap = os.path.join(J, 'cache', 'leap_1920')
    if 111.0 <= t < 116.5 and os.path.isdir(leap):
        kk = int(round((t - 111.0) * A.FPS))
        f8 = cv2.resize(cv2.imread(os.path.join(leap, f'f{12 + kk:04d}.png')), (A.W, A.H), interpolation=cv2.INTER_AREA)
    else:
        f8 = A.frame(k)
    cv2.imwrite(os.path.join(tmp, f'p{k:05d}.png'), f8)
cmd = ['ffmpeg', '-y', '-loglevel', 'error', '-framerate', str(A.FPS), '-start_number', str(k0), '-i', os.path.join(tmp, 'p%05d.png')]
if os.path.exists(wav): cmd += ['-ss', str(t0), '-t', str(t1 - t0), '-i', wav, '-c:a', 'aac', '-b:a', '192k', '-shortest']
cmd += ['-vf', 'fps=24', '-c:v', 'libx264', '-crf', '20', '-pix_fmt', 'yuv420p', out]
subprocess.run(cmd, check=True)
print('done', out)
