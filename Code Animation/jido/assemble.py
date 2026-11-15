"""〈지도〉 애니매틱 조립: 컷 이어 붙이기 + 임시 소리 + 타이틀. 사용: python3 assemble.py [title|audio|video|all]"""
import os, sys, math, subprocess, wave
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont

D = os.path.dirname(os.path.abspath(__file__)); A = os.path.join(D, 'cache', 'anim')
W, H, FPS, SR = 960, 540, 24, 44100
# (종류, 이름, 길이) — 3d: three/shots.js, map: map_shots.py
EDIT = [('3d', 'wake', 7), ('map', 'firstmap', 6), ('3d', 'meet', 4), ('3d', 'crumbs', 5), ('map', 'play', 8), ('3d', 'under', 6),
        ('map', 'routine', 16), ('3d', 'afternoon', 6), ('map', 'loops', 10), ('3d', 'circle', 6), ('map', 'ghost', 8), ('3d', 'family', 6),
        ('map', 'reset', 5), ('3d', 'door', 6), ('map', 'exit', 8), ('map', 'search', 12), ('3d', 'stairs', 8), ('3d', 'homeward', 6),
        ('map', 'return', 5), ('3d', 'newroom', 6), ('map', 'firstdot', 4), ('title', 'title', 7)]
T0 = {}; acc = 0.0
for k, n, d in EDIT: T0[n] = acc; acc += d
DUR = acc

def title():
    out = os.path.join(A, 'title.mp4')
    seal = np.load(os.path.join(D, '..', '_shared', 'seal_baimun3.npy')).astype(np.float32)
    sz = 46; seal = cv2.resize(seal, (sz, sz), interpolation=cv2.INTER_AREA)
    f1 = ImageFont.truetype('/usr/share/fonts/opentype/noto/NotoSerifCJK-Bold.ttc', 64, index=1)
    f2 = ImageFont.truetype('/usr/share/fonts/opentype/noto/NotoSerifCJK-Regular.ttc', 22, index=1)
    f3 = ImageFont.truetype('/usr/share/fonts/opentype/noto/NotoSerifCJK-Regular.ttc', 13, index=1)
    ff = subprocess.Popen(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-',
                           '-c:v', 'libx264', '-crf', '18', '-pix_fmt', 'yuv420p', out], stdin=subprocess.PIPE)
    for k in range(7 * FPS):
        t = k / FPS; a1 = min(1, max(0, (t - 0.3) / 1.2)); a2 = min(1, max(0, (t - 1.4) / 1.0)); a3 = min(1, max(0, (t - 2.6) / 0.6))
        fade = 1 - min(1, max(0, (t - 6.2) / 0.8))
        im = Image.new('RGB', (W, H), (10, 11, 14)); d = ImageDraw.Draw(im)
        d.text((W / 2, H / 2 - 18), 'THE MAP', font=f1, fill=tuple(int(c * a1 * fade) for c in (236, 230, 218)), anchor='mm')
        d.text((W / 2, H / 2 + 38), '지도', font=f2, fill=tuple(int(c * a2 * fade) for c in (150, 175, 150)), anchor='mm')
        cx, cy = W - 58 - sz, H - 52 - sz
        tx = cx - 12
        d.text((tx, cy + 4), 'Created & Coded by L.S.M.', font=f3, fill=tuple(int(c * a3 * fade) for c in (200, 195, 185)), anchor='ra')
        d.text((tx, cy + sz - 16), '허상공방 虛像工房 Project', font=f3, fill=tuple(int(c * a3 * fade) for c in (200, 195, 185)), anchor='ra')
        arr = np.asarray(im).astype(np.float32) / 255
        al = seal[..., 3:4] * np.clip((seal[..., 0:1] - seal[..., 1:2]) * 4, 0, 1) * a3 * fade
        arr[cy:cy + sz, cx:cx + sz] = arr[cy:cy + sz, cx:cx + sz] * (1 - al) + seal[..., :3] * al
        # 지도 점 하나(첫 점이 제목 옆에 남음)
        cv2.circle(arr, (int(W / 2 + 172), int(H / 2 - 4)), 4, (0.55 * a1 * fade, 1.0 * a1 * fade, 0.62 * a1 * fade), -1, cv2.LINE_AA)
        ff.stdin.write((np.clip(arr, 0, 1) * 255).astype(np.uint8).tobytes())
    ff.stdin.close(); ff.wait(); print('title done')

# ---------------------------------------------------------------- 임시 소리
def audio():
    from scipy.signal import butter, lfilter
    n = int((DUR + 1) * SR); L = np.zeros(n); R = np.zeros(n); rng = np.random.default_rng(1)
    def lp(x, f): b, a = butter(2, f / (SR / 2)); return lfilter(b, a, x)
    def bp(x, f0, f1): b, a = butter(2, [f0 / (SR / 2), f1 / (SR / 2)], 'band'); return lfilter(b, a, x)
    def put(x, t, g=1.0, pan=0.0):
        i = int(t * SR); j = min(n, i + len(x)); x = x[:j - i] * g
        L[i:j] += x * (1 - pan) * 0.5 * 2 ** 0.5; R[i:j] += x * (1 + pan) * 0.5 * 2 ** 0.5
    def piano(f, dur=2.5, vel=0.5):
        tt = np.arange(int(dur * SR)) / SR
        env = np.exp(-tt * 2.2) * np.clip(tt / 0.004, 0, 1)
        x = sum(g * np.sin(2 * np.pi * f * k * tt + 0.3 * np.sin(2 * np.pi * f * tt) * np.exp(-tt * 6)) * np.exp(-tt * (1.5 + k)) for k, g in ((1, 1), (2, 0.35), (3, 0.12), (4, 0.05)))
        return lp(x * env, 3500) * vel
    def beep(f, dur=0.09, vel=0.25):
        tt = np.arange(int(dur * SR)) / SR; return np.sin(2 * np.pi * f * tt) * np.clip(tt / 0.005, 0, 1) * np.clip((dur - tt) / 0.02, 0, 1) * vel
    def hum(dur, vel=0.05):
        m = int(dur * SR); tt = np.arange(m) / SR
        x = 0.6 * np.sin(2 * np.pi * 118 * tt) + 0.3 * np.sin(2 * np.pi * 236 * tt) + bp(rng.normal(0, 1, m), 300, 1800) * 0.5
        return x * vel * np.clip(tt / 0.3, 0, 1) * np.clip((dur - tt) / 0.3, 0, 1)
    def tick(vel=0.03):
        m = int(0.02 * SR); return bp(rng.normal(0, 1, m), 3000, 7000) * np.exp(-np.arange(m) / SR / 0.003) * vel
    # 음악: 4음 동기(솔·라·도·미) — 따뜻한 장(0~58), 흔들리는 장(58~101), 정적(101~106), 밤(106~132), 돌아옴(132~)
    M = [392.0, 440.0, 523.3, 659.3]; Mm = [392.0, 415.3, 523.3, 622.3]
    def motif(t0, notes, step=0.6, vel=0.4, oct=1.0):
        for i, f in enumerate(notes): put(piano(f * oct, 3.0, vel), t0 + i * step, pan=-0.2 + 0.13 * i)
    for t in np.arange(2.5, 58, 7.0): motif(t, M + [M[1]], 0.62, 0.32)
    for t in np.arange(58, 98, 6.0): motif(t, [Mm[0], Mm[1], Mm[2], Mm[1]], 0.75, 0.26, 0.5 if t > 80 else 1.0)
    for t in np.arange(106, 132, 1.6): put(piano(98.0, 1.5, 0.22), t)                                     # 밤의 낮은 맥박
    for t in np.arange(118, 132, 0.8): put(piano(146.8, 1.0, 0.12), t)
    motif(T0['stairs'] + 4.5, [M[2], M[1], M[0]], 0.8, 0.3)
    for t in np.arange(T0['homeward'], DUR - 2, 5.2): motif(t, M + [M[2] * 2], 0.55, 0.3)
    put(piano(M[0] / 2, 6, 0.3), T0['title']); put(piano(M[2], 6, 0.25), T0['title'] + 0.05); put(piano(M[3], 6, 0.2), T0['title'] + 0.1)
    # 효과음
    for k, nme, d in EDIT:
        t0 = T0[nme]
        if k == 'map':
            for t in np.arange(t0 + 0.2, t0 + d - 0.2, 0.18): put(tick(0.012), t, pan=rng.uniform(-0.6, 0.6))
        if nme in ('wake', 'meet', 'crumbs', 'under', 'family', 'door', 'stairs', 'homeward'): put(hum(d - 0.2, 0.035), t0 + 0.1)
    put(beep(880), T0['wake'] + 2.6); put(beep(1175), T0['wake'] + 2.75)
    put(beep(660, 0.08), T0['meet'] + 1.9); put(beep(660, 0.08), T0['meet'] + 2.05)
    for i in range(6): put(tick(0.08) * 3, T0['crumbs'] + 1.6 + i * 0.4)
    put(beep(990), T0['under'] + 3.5)
    put(beep(784, 0.12), T0['routine'] + 13.4); put(beep(1047, 0.12), T0['routine'] + 13.55); put(beep(1319, 0.3), T0['routine'] + 13.7)
    put(beep(523, 0.15, 0.2), T0['family'] + 3.6)
    sw = np.arange(int(2.8 * SR)) / SR; put(np.sin(2 * np.pi * np.cumsum(900 * np.exp(-sw * 1.6)) / SR) * np.exp(-sw * 0.9) * 0.18, T0['reset'] + 0.6)
    put(beep(880), T0['door'] + 1.2)
    put(beep(660, 0.1), T0['search'] + 10.0); put(beep(880, 0.1), T0['search'] + 10.15)
    put(beep(880), T0['newroom'] + 3.0); put(beep(1175), T0['newroom'] + 3.15)
    put(beep(1568, 0.25, 0.15), T0['firstdot'] + 1.0)
    # 정적 구간(초기화 뒤)은 음악을 걷어냄
    g = np.ones(n); a, b = int((T0['reset'] + 3.0) * SR), int((T0['door'] + 0.5) * SR); g[a:b] = 0.0
    g = lp(g, 3); L *= g; R *= g
    mx = max(np.abs(L).max(), np.abs(R).max()); L, R = L / mx * 0.85, R / mx * 0.85
    with wave.open(os.path.join(A, 'anim.wav'), 'w') as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((np.stack([L, R], 1) * 32767).astype(np.int16).tobytes())
    print('audio done', round(DUR, 1))

def video():
    lst = os.path.join(A, 'concat.txt')
    with open(lst, 'w') as f:
        for k, nme, d in EDIT:
            p = os.path.join(A, f'3d_{nme}.mp4' if k == '3d' else (f'map_{nme}.mp4' if k == 'map' else 'title.mp4'))
            assert os.path.exists(p), p
            f.write(f"file '{p}'\n")
    out = os.path.join(A, 'jido_animatic_v1.mp4')
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'concat', '-safe', '0', '-i', lst, '-i', os.path.join(A, 'anim.wav'),
                    '-map', '0:v', '-map', '1:a', '-c:v', 'libx264', '-crf', '20', '-pix_fmt', 'yuv420p', '-r', str(FPS), '-c:a', 'aac', '-b:a', '192k', '-shortest', out], check=True)
    print('video', out)

if __name__ == '__main__':
    c = sys.argv[1] if len(sys.argv) > 1 else 'all'
    if c in ('title', 'all'): title()
    if c in ('audio', 'all'): audio()
    if c in ('video', 'all'): video()
