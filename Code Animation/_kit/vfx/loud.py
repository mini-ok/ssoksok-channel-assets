"""음량 맞추기: 통합 음량 −14 LUFS, 트루 피크 −1.5 dBFS 이하로(유튜브 기준). 짧은 곡에서 loudnorm 한 번 돌리기는 피크를 넘긴다
(2026-11-21 검수: 기존 영상 4편 모두 트루 피크 +1.4~+4.0 dBFS) → 측정 → 선형 이득 + 리미터 → 다시 측정.

  python3 -m vfx.loud <in.wav|mp4> <out.wav> [--I -14] [--TP -1.5]
"""
import sys, re, subprocess, argparse


def measure(path):
    r = subprocess.run(['ffmpeg', '-nostats', '-i', path, '-af', 'ebur128=peak=true', '-f', 'null', '-'], capture_output=True, text=True)
    t = r.stderr[r.stderr.rfind('Summary:'):]
    g = lambda p: float(re.search(p, t).group(1))
    return g(r'I:\s+(-?[\d.]+) LUFS'), g(r'Peak:\s+(-?[\d.]+) dBFS')


def _limit(x, sr, ceil_db):
    """미리 보기 리미터(numpy): 4배 올려 잰 봉우리 포락선으로 이득을 줄인다(트루 피크 기준)."""
    import numpy as np
    from scipy.signal import resample_poly
    from scipy.ndimage import maximum_filter1d, uniform_filter1d
    lim = 10 ** (ceil_db / 20)
    up = resample_poly(x, 4, 1, axis=0)
    pk = np.abs(up).reshape(len(x), 4, -1).max(1).max(-1)            # 표본마다 채널·하위 표본 최댓값
    win = int(sr * 0.005) | 1
    env = maximum_filter1d(pk, win)                                   # 5ms 앞뒤 최댓값
    g = np.minimum(1.0, lim / np.maximum(env, 1e-9))
    g = uniform_filter1d(g, win)                                      # 이득 변화 부드럽게
    g = np.minimum(g, lim / np.maximum(pk, 1e-9))                     # 부드럽게 한 뒤에도 넘지 않게
    return x * g[:, None]


def normalize(src, dst, I=-14.0, TP=-1.5, passes=4):
    import numpy as np
    sr = 48000
    raw = subprocess.run(['ffmpeg', '-loglevel', 'error', '-i', src, '-vn', '-ar', str(sr), '-ac', '2', '-f', 'f32le', '-'],
                         capture_output=True, check=True).stdout
    x = np.frombuffer(raw, np.float32).reshape(-1, 2)
    cur_I, cur_tp = measure(src); gain = 0.0
    for _ in range(passes):
        gain += I - cur_I
        y = _limit(x * 10 ** (gain / 20), sr, TP - 0.3).astype(np.float32)
        subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'f32le', '-ar', str(sr), '-ac', '2', '-i', '-', '-c:a', 'pcm_s24le', dst],
                       input=y.tobytes(), check=True)
        cur_I, cur_tp = measure(dst)
        if abs(cur_I - I) <= 0.4: break
    return cur_I, cur_tp


def mux(video, audio_src, out, I=-14.0, TP=-1.5, tries=4):
    """소리를 맞춰 영상에 붙인다. AAC 인코딩이 날카로운 타격에서 피크를 올리므로(실측 +4 dB) 인코딩 뒤에 다시 재고,
    넘으면 넘은 만큼 리미터 천장을 낮춰 다시 만든다."""
    import os
    wav = out + '.norm.wav'; ceil = TP
    for _ in range(tries):
        normalize(audio_src, wav, I, ceil)
        subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-i', video, '-i', wav, '-map', '0:v', '-map', '1:a', '-c:v', 'copy',
                        '-c:a', 'aac', '-b:a', '256k', '-shortest', '-movflags', '+faststart', out], check=True)
        cur_I, cur_tp = measure(out)
        if cur_tp <= TP + 0.3: break
        ceil -= (cur_tp - TP) + 0.3
    os.remove(wav)
    return cur_I, cur_tp


if __name__ == '__main__':
    ap = argparse.ArgumentParser(); ap.add_argument('src'); ap.add_argument('dst')
    ap.add_argument('--I', type=float, default=-14.0); ap.add_argument('--TP', type=float, default=-1.5)
    ap.add_argument('--mux', help='이 영상(mp4)에 소리를 붙여 dst(mp4)로 낸다')
    a = ap.parse_args()
    i, tp = mux(a.mux, a.src, a.dst, a.I, a.TP) if a.mux else normalize(a.src, a.dst, a.I, a.TP)
    print(f'{a.dst}: {i:.1f} LUFS, true peak {tp:.1f} dBFS')
