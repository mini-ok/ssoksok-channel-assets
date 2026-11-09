# -*- coding: utf-8 -*-
"""Motion test: C4 (the gust knocks Kongi off twice) and C8 (the embarrassment beat). Timing on twos, key poses + holds."""
import sys, os, time, math, subprocess
import numpy as np
from keys_k import *
import eng

FPS = 24

def K(t, ks, inb=1):
    return keys(twos(t), ks, inb)

def wind_level(t, gusts):
    w = 0.0
    for a, b in gusts:
        if a <= t < b:
            w = max(w, min(1.0, (t - a) / 0.12) * min(1.0, (b - t) / 0.2))
    return w

# ------------------------------------------------------------------ C4  (local time 0..6)
G4 = [(0.80, 1.55), (3.40, 4.35)]

def c4(t):
    tq = twos(t)
    W_ = wind_level(tq, G4)
    flapR = K(t, [(0.0, -0.25), (0.86, 1.0, 0.25), (1.55, -0.45, 0.25), (1.80, -0.2, 0.15),
                  (3.46, 1.0, 0.25), (4.35, 0.55, 0.3), (4.9, -0.1, 0.5)], inb=1)
    flapL = K(t, [(0.0, -0.25), (0.86, 0.35, 0.3), (1.55, -0.35, 0.3), (1.85, -0.25, 0.2),
                  (3.46, 0.35, 0.3), (4.35, -0.25, 0.4)], inb=1)
    head_tilt = K(t, [(0.0, 0.0), (0.86, 9, 0.2), (1.6, -4, 0.2), (1.9, 0, 0.2), (3.46, 9, 0.2), (4.4, 3, 0.3), (5.0, 0, 0.3)])
    hat_tilt = K(t, [(0.0, 0.0), (0.86, 12, 0.2), (1.6, -5, 0.2), (1.9, 0, 0.2), (3.46, 12, 0.2), (4.4, 0, 0.4)])
    billow = W_
    pal = tint_pal(JI, mix=(1.0, 0.86, 0.70), k=0.08)
    kpal = KO
    def chars(c, S):
        jx, jy = JI_POS
        o = jiibi(c, jx, jy, 1.0, dict(flapL=flapL, flapR=flapR, wind=W_, billow=billow, head_tilt=head_tilt,
                                     hat_tilt=hat_tilt, goreum_wind=W_ * 0.9 + 0.1 * math.sin(tq * 3)), t=t, L=S['L'], pal=pal)
        hx, hy = c.device_to_user(*o['hat'])
        cx_, cy_ = c.device_to_user(*o['cuffR'])
        breathe = 1.15 + 0.06 * math.sin(tq * 3.0)
        # --- Kongi: doze -> knocked off -> returns -> clings to the cuff
        if tq < 1.0:
            kongi(c, hx + 4, hy + 3, 11, dict(blink=1, puff=breathe, tilt=hat_tilt * 0.6), t=t, L=S['L'], pal=kpal)
        elif tq < 1.6:
            u = (tq - 1.0) / 0.6
            x = hx + 4 + 520 * u; y = hy + 3 - 160 * math.sin(math.pi * min(1, u * 1.2)) + 260 * u * u
            kongi(c, x, y, 11, dict(blink=0, open_beak=1.0, puff=1.3, wing=1.0 if int(tq * 12) % 2 else 0.0,
                                    tilt=-360 * u * 1.5, feet=0), t=t, L=S['L'], pal=kpal)
        elif tq < 2.4:
            pass                                                    # out of frame: the hold on Jiibi
        elif tq < 3.0:
            u = (tq - 2.4) / 0.6
            x = hx + 4 + 480 * (1 - u); y = hy + 3 - 120 * math.sin(math.pi * u)
            kongi(c, x, y, 11, dict(wing=1.0 if int(tq * 12) % 2 else 0.2, feet=0, face=-1, tilt=10, puff=1.15),
                  t=t, L=S['L'], pal=kpal)
        elif tq < 3.5:
            land = tq - 3.0
            sq = 0.78 if land < 0.09 else (1.12 if land < 0.17 else 1.0)
            pf = 1.45 if 0.2 < land < 0.42 else 1.15
            kongi(c, hx + 4, hy + 3, 11, dict(squash=sq, puff=pf, face=-1, blink=1 if 0.25 < land < 0.4 else 0),
                  t=t, L=S['L'], pal=kpal)
        else:
            # second gust: she grabs the cuff and dangles, wings beating; afterwards perches on it, proud
            if tq < 4.9:
                kongi(c, cx_ + 2, cy_ + 22, 11, dict(feet=1, tilt=180 + 25 * math.sin(tq * 20) * W_, puff=1.2,
                                                     wing=1.0 if int(tq * 12) % 2 else 0.0, open_beak=0.6), t=t,
                      L=S['L'], pal=kpal)
            else:
                pf = 1.5 if tq > 5.3 else 1.2
                kongi(c, cx_ - 4, cy_ - 16, 11, dict(puff=pf, face=-1, tilt=-6, blink=1 if 5.4 < tq < 5.6 else 0),
                      t=t, L=S['L'], pal=kpal)
        rice_clump(c, jx, jy - 40, 1.2, S['rice'], t, n=70, wind=0.25 + W_)
    def fxp(c):
        if W_ > 0.05:
            wind_marks(c, t, alpha=W_)
    return frame('dawn', (1330, 640, 1.25), chars, fx_post=fxp, t=t, blur_bg=1.4, ccam=(1520, 700, 3.0),
                 grade=((0.03, 0.02, 0.03), (1.02, 0.99, 0.95), 1.02, 0.97))

# ------------------------------------------------------------------ C8  (local time 0..4.5)
def c8(t):
    tq = twos(t)
    breeze = wind_level(tq, [(1.2, 2.3), (3.3, 3.9)]) * 0.4
    hat_down = K(t, [(0.0, 0.0), (1.3, 0.55, 0.35), (2.3, 0.6, 0.2), (3.35, 1.0, 0.3)], inb=2)
    head_turn = K(t, [(0.0, 0.0), (1.4, -0.45, 0.4), (3.4, -0.7, 0.3)], inb=2)
    head_tilt = K(t, [(0.0, 0.0), (1.4, -7, 0.4), (3.4, -11, 0.3)], inb=2)
    leaf_t = 1.75
    leaf = 1.0 if tq >= leaf_t else 0.0
    def chars(c, S):
        jx, jy = JI_POS
        o = jiibi(c, jx, jy, 1.0, dict(flapL=-0.3, flapR=-0.25, wind=breeze, hat_down=hat_down, head_turn=head_turn,
                                     head_tilt=head_tilt, leaf=leaf, pocket=0, hat_tilt=-2), t=t, L=S['L'])
        hdx, hdy = c.device_to_user(*o['head'])
        # Kongi perched on the shoulder seam, rubbing her head against his cheek, then gazing up
        rub = math.sin(tq * 14) if 0.3 < tq < 1.1 else 0.0
        tilt = K(t, [(0.0, -12), (1.2, 8, 0.2), (2.0, 18, 0.3)], inb=1) + 7 * rub
        pf = K(t, [(0.0, 1.25), (1.2, 1.25), (1.3, 1.45, 0.15), (2.6, 1.3, 0.3)], inb=1)
        kongi(c, hdx + 33 - 3 * rub, hdy + 42, 10, dict(face=-1, tilt=tilt, puff=pf, blink=1 if (0.3 < tq < 1.1 or 2.9 < tq < 3.05) else 0),
              t=t, L=S['L'])
        # the leaf flying in before it sticks
        if leaf_t - 0.5 < tq < leaf_t:
            u = (tq - (leaf_t - 0.5)) / 0.5
            lx = hdx + 160 * (1 - u) + 12; ly = hdy - 60 * (1 - u) + 21 + 30 * math.sin(u * 6)
            B = Boil(t, salt=5)
            def lf(cc):
                cc.save(); cc.translate(lx, ly); cc.rotate(u * 9)
                smooth_path(cc, B.jp([(0, 7), (-8, 1), (-5, -2), (-7, -8), (-2, -5), (0, -11), (2, -5), (8, -7), (5, 0), (9, 3)], 0.3))
                cc.restore()
            cel(c, lf, (0.90, 0.26, 0.15), (0.66, 0.15, 0.10), S['L'], off=2, lw=1.6)
    def fxp(c):
        if breeze > 0.05:
            wind_marks(c, t, alpha=breeze)
    return frame('noon', (1200, 520, 1.6), chars, fx_post=fxp, t=t, blur_bg=3.0, ccam=(1520, 742, 5.2),
                 grade=((0.02, 0.02, 0.03), (1.02, 1.0, 0.98), 1.04, 1.0))

SEG = [(c4, 6.0), (c8, 4.5)]
TOTAL = sum(d for _, d in SEG)
NF = int(TOTAL * FPS)

def render_frame(i):
    t = i / FPS
    acc = 0.0
    for fn, d in SEG:
        if t < acc + d:
            cp = fn(t - acc)
            lt = t - acc
            cp.fade *= min(1.0, lt / 0.25 + 0.0) if fn is c4 else 1.0
            return cp.finish(i)
        acc += d
    return SEG[-1][0](SEG[-1][1] - 0.01).finish(i)

def chunk(args):
    i0, i1, path = args
    cmd = ['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{eng.W}x{eng.OH}', '-r', str(FPS),
           '-i', '-', '-c:v', 'libx264', '-preset', 'medium', '-crf', '18', '-pix_fmt', 'yuv420p', path]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    for i in range(i0, i1):
        p.stdin.write(render_frame(i).tobytes())
    p.stdin.close(); p.wait()
    return i0

if __name__ == '__main__':
    if sys.argv[1] == 'test':
        from PIL import Image
        for a in sys.argv[2:]:
            i = int(float(a) * FPS)
            Image.fromarray(render_frame(i)).save(f'test/m_{float(a):05.2f}.png'); print(a, flush=True)
    else:
        import multiprocessing as mp
        os.makedirs('mchunks', exist_ok=True)
        half = NF // 2
        jobs = [(0, half, 'mchunks/a.mp4'), (half, NF, 'mchunks/b.mp4')]
        t0 = time.time()
        with mp.Pool(2) as pool:
            list(pool.imap_unordered(chunk, jobs))
        open('mchunks/list.txt', 'w').write("file 'a.mp4'\nfile 'b.mp4'\n")
        subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'concat', '-safe', '0', '-i', 'mchunks/list.txt', '-c', 'copy',
                        'out/허수아비_움직임시험.mp4'])
        print('done', time.time() - t0)
