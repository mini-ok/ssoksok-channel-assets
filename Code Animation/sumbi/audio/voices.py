# temp voices (offline KSS TTS) -> pitch/formant shaping per character, lip tracks (12 fps) -> ../three/lips.js
import numpy as np, json, subprocess, sys
from scipy.io import wavfile
from scipy.signal import resample_poly, butter, sosfilt
SR = 44100
TTS = '/home/claude/tts'
def tts(text, speed, out):
    subprocess.run(['python3', 'say.py', text, out, str(speed)], cwd=TTS, check=True, capture_output=True)
    sr, a = wavfile.read(f'{TTS}/{out}'); a = a.astype(np.float64) / 32768
    return resample_poly(a, SR, sr)
def wsola(x, rate, win=1024, hop=256):
    # time-stretch by 1/rate keeping pitch (rate>1 = faster)
    w = np.hanning(win); out = np.zeros(int(len(x) / rate) + win * 2); norm = np.zeros_like(out)
    ipos, opos, tol = 0.0, 0, 200; prev = None
    while int(ipos) + win + tol < len(x) and opos + win < len(out):
        i = int(ipos)
        if prev is not None:
            best, bc = 0, -1e9
            for d in range(-tol, tol + 1, 8):
                j = i + d
                if j < 0: continue
                c = np.dot(x[j:j + win // 2], prev)
                if c > bc: bc, best = c, d
            i += best
        seg = x[i:i + win] * w
        out[opos:opos + win] += seg; norm[opos:opos + win] += w
        prev = x[i + hop:i + hop + win // 2]
        ipos += hop * rate; opos += hop
    return out[:opos] / np.maximum(norm[:opos], 1e-3)
def shift(x, semis):
    r = 2 ** (semis / 12)
    up = resample_poly(x, 1000, int(round(1000 * r)))      # faster+higher
    return wsola(up, 1 / r)
def lp(x, fc): return sosfilt(butter(2, fc, btype='low', fs=SR, output='sos'), x)
def hp(x, fc): return sosfilt(butter(2, fc, btype='high', fs=SR, output='sos'), x)
def norm(x, peak=0.9): return x / (np.abs(x).max() + 1e-9) * peak
def trim(x, th=0.01):
    idx = np.where(np.abs(x) > th)[0]; return x[max(0, idx[0] - 400): idx[-1] + 2000]
lines = {   # segments joined with pauses (s): emotional pacing the TTS can't do on its own
  'mom1': ([('솔아.', 0.72), 0.32, ('물 떠 오라이.', 0.8)], -1.0),
  'sol1': ([('꾸럭아.', 0.8), 0.25, ('조금만 참아.', 0.82)], 3.5),
  'sol2': ([('엄마.', 0.6)], 3.5),
  'mom2': ([('숨.', 0.6), 0.45, ('같이 쉬자.', 0.68)], -1.0),
}
LIPS = {}
# Gemini Flash TTS takes (gemini/run.py): mom = Sulafat, 솔이 = Zephyr (+1.5 semitones for a 9-year-old)
GEM = {'mom1': ('mom1_take1', 0), 'sol1': ('sol1_take3', 1.5), 'sol2': ('sol2_take3', 1.5), 'mom2': ('mom2_take1', 0)}
for k, (take, semis) in GEM.items():
    sr0, a0 = wavfile.read(f'gemini/sumbi_voices/{take}.wav'); x = resample_poly(a0.astype(np.float64) / 32768, SR, sr0)
    x = trim(x, 0.015)
    if semis: x = shift(x, semis)
    if k == 'sol2':
        x = lp(x, 1100) * (1 + 0.3 * np.sin(2 * np.pi * 9 * np.arange(len(x)) / SR))
    x = norm(hp(x, 90), 0.85)
    wavfile.write(f'{k}.wav', SR, (x * 32767).astype(np.int16))
    # lip track at 12 drawings/s from RMS
    n = int(len(x) / SR * 12) + 1; env = []
    for i in range(n):
        seg = x[int(i * SR / 12): int((i + 1) * SR / 12)]
        env.append(np.sqrt(np.mean(seg ** 2)) if len(seg) else 0)
    env = np.array(env); env /= env.max() + 1e-9
    track = [0 if e < 0.18 else (1 if e < 0.55 else 2) for e in env]
    track[-1] = 0
    LIPS[k] = track
    print(k, round(len(x) / SR, 2), 's', ''.join(map(str, track)))
open('/home/claude/sumbi/three/lips.js', 'w').write('window.LIPS = ' + json.dumps(LIPS) + ';\nwindow.LIPDUR = ' +
    json.dumps({k: round(len(v) / 12, 2) for k, v in LIPS.items()}) + ';\n')
