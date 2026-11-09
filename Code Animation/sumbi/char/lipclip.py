# -*- coding: utf-8 -*-
"""2-second lip-sync test (C13): 솔이 whispers "꾸럭아, 조금만 참아." to the jar. Mouth: 3 drawings (closed/half/open),
switched only while she speaks, on twos, from a syllable track (vowel openness + closing final consonant).
Audio is a placeholder whisper synthesized from the same syllable track until the Gemini TTS key is available;
with a real WAV, mouth_from_wav() drives the same 3 drawings from loudness."""
import sys, math, subprocess, numpy as np, cairo, cv2
sys.path.insert(0, '/home/claude/sumbi/char'); sys.path.insert(0, '/home/claude/scarecrow'); sys.path.insert(0, '/home/claude/sumbi/three')
from sol import sol_front, kuruk, ell, fill, PAL, L0
from cel import set_frame, cel, smooth_path, inkline, Boil, cel_finish, film_post
from scipy.io import wavfile
from scipy.signal import butter, sosfilt

FPS, DUR = 24, 2.0
W, H = 1920, 1040
# syllable track: (start, end, open 0-2, final consonant closes the mouth?)  — 꾸 럭 아 , 조 금 만 참 아
SYL = [(0.30, 0.44, 1, False, 'u'), (0.44, 0.60, 2, False, 'eo'), (0.60, 0.80, 2, False, 'a'),
       (0.94, 1.08, 1, False, 'o'), (1.08, 1.22, 1, True, 'eu'), (1.22, 1.40, 2, False, 'a'), (1.40, 1.58, 2, True, 'a'),
       (1.58, 1.84, 2, False, 'a')]

def mouth_at(t):
    tq = math.floor(t * 12) / 12                              # on twos
    for (a, b, op, close, v) in SYL:
        if a <= tq < b:
            u = (tq - a) / (b - a)
            if close and u > 0.6:
                return 0
            if u < 0.2:
                return 1                                      # every syllable passes through 'half' on the way open
            return op
    return 0

def mouth_from_wav(env_t, env_v, t):
    """for the real TTS: loudness -> 0/1/2 on twos (thresholds relative to the line's peak)"""
    tq = math.floor(t * 12) / 12
    v = float(np.interp(tq, env_t, env_v))
    return 0 if v < 0.18 else (1 if v < 0.55 else 2)

FORM = {'a': (850, 1500), 'eo': (620, 1050), 'u': (330, 780), 'o': (450, 820), 'eu': (380, 1450)}

def whisper_wav(path):
    sr = 44100; n = int(DUR * sr); out = np.zeros(n)
    rng = np.random.default_rng(1)
    for (a, b, op, close, v) in SYL:
        i0, i1 = int(a * sr), int(b * sr); m = i1 - i0
        f1, f2 = FORM[v]
        nz = rng.normal(0, 1, m)
        s = sosfilt(butter(2, [f1 * 0.7, f1 * 1.3], btype='band', fs=sr, output='sos'), nz) * 1.0 + \
            sosfilt(butter(2, [f2 * 0.8, f2 * 1.25], btype='band', fs=sr, output='sos'), nz) * 0.7 + \
            sosfilt(butter(2, [2500, 6000], btype='band', fs=sr, output='sos'), nz) * 0.25
        tt = np.arange(m) / m
        env = np.minimum(1, tt / 0.15) * np.minimum(1, (1 - tt) / (0.45 if close else 0.3))
        out[i0:i1] += s * env * (0.8 if op == 1 else 1.0)
        if v in ('u', 'o') or (a == 0.94):                    # consonant onsets: a short breathy burst
            k = int(0.03 * sr)
            out[i0:i0 + k] += sosfilt(butter(2, [2000, 7000], btype='band', fs=sr, output='sos'), rng.normal(0, 1, k)) * 0.6
    # forest room tone + a bird far off
    tone = sosfilt(butter(2, [300, 2000], btype='band', fs=sr, output='sos'), rng.normal(0, 1, n)) * 0.03
    out = out / np.abs(out).max() * 0.6 + tone
    t = np.arange(n) / sr
    for b0 in (0.15, 1.9):
        k = (t > b0) & (t < b0 + 0.08)
        out[k] += 0.05 * np.sin(2 * np.pi * (4200 + 900 * np.sin(np.pi * (t[k] - b0) / 0.08)) * t[k])
    wavfile.write(path, sr, (np.stack([out, out], -1) * 32767).astype(np.int16))

def background():
    import os
    here = os.getcwd(); os.chdir('/home/claude/sumbi/three')
    import multiplane as mp
    sky = mp.sky_plate()
    off = (mp.PW - W) // 2
    img = sky[:, off:off + W].copy()
    for name, depth, _, wpx in mp.LAYERS[:2]:
        rgb, a, ink, inkc = mp.build_plate(name, wpx)
        lay = rgb * (1 - ink[..., None]) + inkc * ink[..., None]
        al = np.clip(a, 0, 1)[..., None]
        img = img * (1 - al[:, off:off + W]) + lay[:, off:off + W] * al[:, off:off + W]
    os.chdir(here)
    img = cv2.GaussianBlur(img.astype(np.float32), (0, 0), 7)          # shallow depth of field for the close-up
    return np.clip(img * 1.04, 0, 1)

def jar_front(c, x, y, s, t, L, inner=None):
    """the jar seen from the front; `inner(c)` draws whatever sits in the mouth (between the dark opening and the body)"""
    B = Boil(t, salt=51)
    lw = 2.6
    c.save(); c.translate(x, y); c.scale(s, s)
    cel(c, lambda cc: ell(cc, 0, -96, 34, 10), (0.24, 0.16, 0.12), (0.24, 0.16, 0.12), L, off=0, lw=lw / s)   # opening (back)
    c.restore()
    if inner:
        inner(c)
    c.save(); c.translate(x, y); c.scale(s, s)
    body = [(-34, -96), (-60, -82), (-70, -40), (-64, 20), (-30, 60), (30, 60), (64, 20), (70, -40), (60, -82), (34, -96),
            (20, -88), (0, -86), (-20, -88)]
    cel(c, lambda cc: smooth_path(cc, B.jp(body, 0.4)), PAL['jar'], PAL['jar_s'], L, off=10, lw=lw / s)
    inkline(c, B.jp([(-40, -40), (-22, -28), (-30, -8)], 0.3), 2.0 / s, PAL['jar_s'], 1.0)             # the crack
    c.restore()

def frame(i, bg):
    t = i / FPS
    set_frame(t)
    tq = math.floor(t * 12) / 12
    m = mouth_at(t)
    speaking = 0.30 <= tq < 1.84
    bob = 2.0 * math.sin(tq * 9) if speaking else 0.0
    blink = 'blink' if 1.90 <= tq < 1.96 or 0.10 <= tq < 0.16 else 'open'
    surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H); c = cairo.Context(surf)
    # 솔이 close-up, leaning toward the jar
    sol_front(c, 760, 560 + 446 * 3.0 + bob, 3.0, dict(mouth=m, eyes=blink, look=1.0, down=1.0, tilt=10, brow=-0.5, arm=-0.6, turn=0.4), t=t, L=L0)
    kst = 'orange' if tq > 1.2 else 'grey'                    # her whisper warms him up
    jar_front(c, 1380, 1120, 2.6, t, L0,
              inner=lambda cc: kuruk(cc, 1380, 1120 - 96 * 2.6 - 4, 2.6, kst, t=t, curl=0.7, blink=(1.5 <= tq < 1.58)))
    surf.flush()
    arr = np.ndarray((H, W, 4), np.uint8, surf.get_data()).astype(np.float32) / 255
    arr = arr[..., [2, 1, 0, 3]]
    arr = cel_finish(arr, t)
    a = arr[..., 3:4]
    img = bg * (1 - a) + arr[..., :3]
    img = film_post(np.clip(img, 0, 1), t)
    full = np.zeros((1080, W, 3), np.uint8); full[20:20 + H] = (np.clip(img, 0, 1) * 255).astype(np.uint8)
    return full

if __name__ == '__main__':
    from PIL import Image
    whisper_wav('lip_placeholder.wav')
    bg = background()
    p = subprocess.Popen(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x1080', '-r', str(FPS),
                          '-i', '-', '-i', 'lip_placeholder.wav', '-c:v', 'libx264', '-crf', '17', '-pix_fmt', 'yuv420p', '-c:a', 'aac',
                          '-shortest', 'lipsync_test.mp4'], stdin=subprocess.PIPE)
    for i in range(int(DUR * FPS)):
        f = frame(i, bg)
        p.stdin.write(f.tobytes())
        if i in (12, 15, 17, 30):
            Image.fromarray(f).save(f'lip_{i:02d}.png')
    p.stdin.close(); p.wait()
    print('ok', [mouth_at(i / 24) for i in range(48)])
