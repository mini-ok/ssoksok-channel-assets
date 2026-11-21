"""렌더 검수 도구 — 결함을 숫자와 그림으로 바꾼다. (1번 스킬 vk1-qa-inspection)

  python3 -m vfx.qa sheet   <mp4> [--n 8] [--out dir]    접촉 시트(샷마다 n장, 샷이 없으면 전체에서 고르게)
  python3 -m vfx.qa cuts    <mp4> [--out dir]            컷 경계 앞뒤 띠(−0.2초, −1프레임, 컷, +0.2초)
  python3 -m vfx.qa phone   <mp4> [--out dir]            폰 폭(360px) 시트: 글자가 읽히는지
  python3 -m vfx.qa flicker <mp4> [--out dir]            16×9 칸 떨림·깜박임 지도, 3×3 움직임 점수
  python3 -m vfx.qa audio   <mp4>                        음량(LUFS)·피크·무음 구간
  python3 -m vfx.qa report  <mp4> --out <dir>            위 전부 + report.md / report.json (P0·P1 목록)

판정은 점수가 아니라 목록이다: P0(올리면 안 됨) / P1(고치면 좋아짐) / 사람이 봐야 할 것.
숫자는 듣기·보기를 대신하지 못한다 — report.md 끝의 '사람이 봐야 할 것'을 반드시 확인한다.
"""
import os, sys, json, argparse, subprocess, re
import numpy as np, cv2

GW, GH = 16, 9


def _probe(path):
    cap = cv2.VideoCapture(path)
    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    n = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    w, h = int(cap.get(3)), int(cap.get(4))
    cap.release()
    return fps, n, w, h


def _scan(path, small=(160, 90)):
    """한 번 훑어 프레임별 통계를 만든다: 칸 밝기(GH×GW), 앞 프레임과의 차이(전체·칸별)."""
    cap = cv2.VideoCapture(path)
    cells, dglob, dcell, means = [], [], [], []
    prev = None
    while True:
        ok, f = cap.read()
        if not ok: break
        g = cv2.cvtColor(cv2.resize(f, small, interpolation=cv2.INTER_AREA), cv2.COLOR_BGR2GRAY).astype(np.float32)
        c = cv2.resize(g, (GW, GH), interpolation=cv2.INTER_AREA)
        cells.append(c); means.append(float(g.mean()))
        if prev is None: dglob.append(0.0); dcell.append(np.zeros((GH, GW), np.float32))
        else:
            d = np.abs(g - prev); dglob.append(float(d.mean()))
            dcell.append(cv2.resize(d, (GW, GH), interpolation=cv2.INTER_AREA))
        prev = g
    cap.release()
    return np.array(cells), np.array(dglob), np.array(dcell), np.array(means)


def find_cuts(dglob, fps, k=6.0, floor=12.0):
    """앞뒤 이웃보다 k배 튀고 floor(0..255)보다 큰 차이 = 컷."""
    cuts = []
    for i in range(2, len(dglob) - 2):
        nb = np.median(np.r_[dglob[max(0, i - 6):i], dglob[i + 1:i + 7]]) + 0.3
        if dglob[i] > floor and dglob[i] > k * nb: cuts.append(i)
    out = []
    for c in cuts:
        if not out or c - out[-1] > fps * 0.25: out.append(c)
    return out


def _grab(path, idxs, width=None):
    cap = cv2.VideoCapture(path); out = []
    for i in idxs:
        cap.set(cv2.CAP_PROP_POS_FRAMES, max(0, int(i)))
        ok, f = cap.read()
        if not ok: f = np.zeros((90, 160, 3), np.uint8)
        if width: f = cv2.resize(f, (width, int(round(f.shape[0] * width / f.shape[1]))), interpolation=cv2.INTER_AREA)
        out.append(f)
    cap.release(); return out


def _label(img, text):
    img = img.copy()
    cv2.rectangle(img, (0, 0), (8 + 9 * len(text), 20), (0, 0, 0), -1)
    cv2.putText(img, text, (4, 15), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255, 255, 255), 1, cv2.LINE_AA)
    return img


def _grid(imgs, cols, pad=6, bg=255):
    h, w = imgs[0].shape[:2]; rows = (len(imgs) + cols - 1) // cols
    sheet = np.full((rows * (h + pad) + pad, cols * (w + pad) + pad, 3), bg, np.uint8)
    for i, im in enumerate(imgs):
        r, c = divmod(i, cols); y, x = pad + r * (h + pad), pad + c * (w + pad)
        sheet[y:y + h, x:x + w] = cv2.resize(im, (w, h))
    return sheet


def cmd_sheet(path, out, n=8, stats=None):
    fps, nf, w, h = _probe(path)
    cells, dglob, dcell, means = stats or _scan(path)
    cuts = [0] + find_cuts(dglob, fps) + [nf]
    tw = 240 if w >= h else 180
    files = []
    if len(cuts) <= 2:                                    # 컷 없음: 전체에서 고르게 2n장
        idx = np.linspace(0, nf - 1, n * 2).astype(int)
        imgs = [_label(f, f'{i / fps:5.2f}s') for f, i in zip(_grab(path, idx, tw), idx)]
        p = os.path.join(out, 'sheet.jpg'); cv2.imwrite(p, _grid(imgs, n)); files.append(p)
    else:
        rows = []
        for a, b in zip(cuts[:-1], cuts[1:]):
            idx = np.linspace(a, max(a, b - 1), n).astype(int)
            rows += [_label(f, f'{i / fps:5.2f}s') for f, i in zip(_grab(path, idx, tw), idx)]
        for k in range(0, len(rows), n * 6):               # 한 장에 샷 6개까지
            p = os.path.join(out, f'sheet_{k // (n * 6):02d}.jpg'); cv2.imwrite(p, _grid(rows[k:k + n * 6], n)); files.append(p)
    return files


def cmd_cuts(path, out, stats=None):
    fps, nf, w, h = _probe(path)
    cells, dglob, dcell, means = stats or _scan(path)
    cuts = find_cuts(dglob, fps); d = int(round(0.2 * fps)); tw = 300 if w >= h else 200
    rows = []
    for c in cuts:
        idx = [c - d, c - 1, c, c + d]
        rows += [_label(f, f'{i / fps:5.2f}s') for f, i in zip(_grab(path, idx, tw), idx)]
    files = []
    for k in range(0, len(rows), 4 * 8):
        p = os.path.join(out, f'cuts_{k // 32:02d}.jpg'); cv2.imwrite(p, _grid(rows[k:k + 32], 4)); files.append(p)
    return files, [c / fps for c in cuts]


def cmd_phone(path, out, n=6):
    fps, nf, w, h = _probe(path)
    idx = np.linspace(nf * 0.04, nf * 0.96, n).astype(int)
    tw = 360 if h > w else 640                              # 세로 영상은 폰 폭 360, 가로는 폰을 눕힌 640
    imgs = [_label(f, f'{i / fps:5.2f}s') for f, i in zip(_grab(path, idx, tw), idx)]
    p = os.path.join(out, 'phone.jpg'); cv2.imwrite(p, _grid(imgs, 3 if h > w else 2)); return [p]


def cmd_flicker(path, out, stats=None):
    fps, nf, w, h = _probe(path)
    cells, dglob, dcell, means = stats or _scan(path)
    cuts = set(find_cuts(dglob, fps)); mask = np.ones(len(dglob), bool)
    for c in cuts: mask[max(0, c - 1):c + 2] = False
    # 깜박임: 칸 밝기의 2차 차분(앞뒤 평균에서 튀는 정도). 매끄러운 움직임·페이드는 작고, 프레임마다 오르내리면 크다.
    sec = np.zeros_like(cells)
    sec[1:-1] = np.abs(cells[1:-1] - 0.5 * (cells[:-2] + cells[2:]))
    m2 = mask.copy(); m2[:-1] &= mask[1:]; m2[1:] &= mask[:-1]
    flick = sec[m2].mean(0) if m2.any() else sec.mean(0)                 # (GH,GW) 평균 깜박임(0..255)
    # 전체 화면 밝기 깜박임(노출 펌핑)
    gsec = np.zeros_like(means); gsec[1:-1] = np.abs(means[1:-1] - 0.5 * (means[:-2] + means[2:]))
    gsec[~m2] = 0
    # 떨림: 칸별 프레임 차이 평균 / 3×3 움직임 점수(움직인 시간 비율)
    jitter = dcell[mask].mean(0)
    moving = (dcell[mask] > 1.0)                                        # 칸이 움직인 프레임
    z = moving.reshape(-1, 3, GH // 3, GW).mean(2)                      # 세로 3구역
    zw = [slice(0, 5), slice(5, 11), slice(11, 16)]
    score = np.array([[float(z[:, r, s].mean()) for s in zw] for r in range(3)])
    # 최악 구간(1초 창)
    win = int(fps); per = sec.reshape(len(sec), -1).max(1); per[~m2] = 0
    worst = [(float(per[i:i + win].mean()), i / fps) for i in range(0, max(1, len(per) - win), max(1, win // 2))]
    worst.sort(reverse=True)
    # 멈춘 구간(홀드)과 그 안의 PSNR(결·압축 때문에 흔들리는 정도)
    holds, i = [], 0
    still = (dglob < 0.6) & mask
    while i < len(still):
        if still[i]:
            j = i
            while j < len(still) and still[j]: j += 1
            if (j - i) / fps >= 0.5:
                mse = float((dglob[i:j] ** 2).mean()) + 1e-6
                holds.append(dict(t0=i / fps, t1=j / fps, psnr=float(10 * np.log10(255 ** 2 / mse))))
            i = j
        else: i += 1
    # 그림: 깜박임 지도
    hm = cv2.resize(np.clip(flick / 3.0, 0, 1), (GW * 40, GH * 40), interpolation=cv2.INTER_NEAREST)
    hm = cv2.applyColorMap((hm * 255).astype(np.uint8), cv2.COLORMAP_INFERNO)
    for r in range(GH):
        for c in range(GW):
            cv2.putText(hm, f'{flick[r, c]:.1f}', (c * 40 + 4, r * 40 + 24), cv2.FONT_HERSHEY_SIMPLEX, 0.36, (255, 255, 255), 1, cv2.LINE_AA)
    p = os.path.join(out, 'flicker_map.png'); cv2.imwrite(p, hm)
    res = dict(flicker_mean=float(flick.mean()), flicker_max_cell=float(flick.max()),
               flicker_max_cell_rc=[int(x) for x in np.unravel_index(flick.argmax(), flick.shape)],
               exposure_pump=float(gsec.mean()), exposure_pump_max=float(gsec.max()),
               exposure_pump_at=float(gsec.argmax() / fps),
               jitter_mean=float(jitter.mean()), motion_3x3=np.round(score, 2).tolist(),
               worst_windows=[dict(v=round(v, 2), t=round(t, 2)) for v, t in worst[:5]], holds=holds[:20],
               black_frames=[round(i / fps, 2) for i in np.where(means < 3.0)[0][:50]],
               frozen_total=float(sum(h['t1'] - h['t0'] for h in holds)))
    return [p], res


def cmd_audio(path):
    r = subprocess.run(['ffmpeg', '-nostats', '-i', path, '-af', 'ebur128=peak=true', '-f', 'null', '-'],
                       capture_output=True, text=True)
    txt = r.stderr; tail = txt[txt.rfind('Summary:'):] if 'Summary:' in txt else ''
    def g(pat):
        m = re.search(pat, tail); return float(m.group(1)) if m else None
    res = dict(lufs=g(r'I:\s+(-?[\d.]+) LUFS'), lra=g(r'LRA:\s+(-?[\d.]+) LU'), true_peak=g(r'Peak:\s+(-?[\d.]+) dBFS'))
    if res['lufs'] is None: res['error'] = '소리 줄기 없음 또는 측정 실패'
    r2 = subprocess.run(['ffmpeg', '-nostats', '-i', path, '-af', 'silencedetect=noise=-50dB:d=1.0', '-f', 'null', '-'],
                        capture_output=True, text=True)
    res['silences'] = [dict(start=float(a), dur=float(b)) for a, b in
                       zip(re.findall(r'silence_start: ([\d.]+)', r2.stderr), re.findall(r'silence_duration: ([\d.]+)', r2.stderr))]
    return res


def cmd_report(path, out):
    os.makedirs(out, exist_ok=True)
    fps, nf, w, h = _probe(path); dur = nf / fps
    stats = _scan(path)
    files = cmd_sheet(path, out, stats=stats)
    cf, cut_times = cmd_cuts(path, out, stats=stats)
    pf = cmd_phone(path, out)
    ff, fl = cmd_flicker(path, out, stats=stats)
    au = cmd_audio(path)
    P0, P1, HUMAN = [], [], []
    mid_black = [t for t in fl['black_frames'] if 0.5 < t < dur - 0.5]
    if mid_black: P0.append(f'중간에 검은 프레임 {len(mid_black)}개 (첫 {mid_black[0]}초)')
    if au.get('error'): P0.append(au['error'])
    else:
        if abs(au['lufs'] + 14) > 1.5: P1.append(f"음량 {au['lufs']} LUFS (기준 -14 ±1.5)")
        if au['true_peak'] is not None and au['true_peak'] > -1.0: P1.append(f"트루 피크 {au['true_peak']} dBFS (기준 -1 이하)")
        for s in au['silences']:
            if 0.5 < s['start'] < dur - 1.5: HUMAN.append(f"무음 {s['start']:.1f}초부터 {s['dur']:.1f}초 — 의도한 정적인지")
    if fl['flicker_max_cell'] > 2.0:
        r, c = fl['flicker_max_cell_rc']
        P1.append(f"깜박임 큰 칸: 행 {r}·열 {c} 평균 {fl['flicker_max_cell']:.1f} (기준 2.0) — flicker_map.png, 최악 구간 {fl['worst_windows'][0]['t']}초")
    if fl['exposure_pump_max'] > 4.0: HUMAN.append(f"화면 전체 밝기 튐 {fl['exposure_pump_max']:.1f} @ {fl['exposure_pump_at']:.2f}초 — 섬광·페이드 연출이 아니면 결함")
    dead = [(r, c) for r in range(3) for c in range(3) if fl['motion_3x3'][r][c] < 0.03]
    if len(dead) >= 5: HUMAN.append(f'3×3 구역 중 {len(dead)}곳이 거의 안 움직임 — 화면이 비어 보이지 않는지')
    for hd in fl['holds']:
        if hd['t1'] - hd['t0'] > 2.5 and hd['t1'] < dur - 0.5: HUMAN.append(f"{hd['t0']:.1f}~{hd['t1']:.1f}초 정지 — 의도한 멈춤인지")
    HUMAN += ['phone.jpg: 폰 크기에서 글자가 읽히는가', 'cuts_*.jpg: 컷 앞뒤로 위치·크기·상태가 이어지는가',
              'sheet*.jpg: 각 샷을 낯선 사람에게 한 문장으로 설명할 수 있는가', '소리를 실제로 들어 보았는가(숫자는 듣기를 대신하지 못한다)']
    rep = dict(file=os.path.basename(path), fps=fps, frames=nf, size=[w, h], duration=round(dur, 2), cuts=[round(t, 2) for t in cut_times],
               flicker=fl, audio=au, P0=P0, P1=P1, human=HUMAN, images=[os.path.basename(x) for x in files + cf + pf + ff])
    json.dump(rep, open(os.path.join(out, 'report.json'), 'w'), ensure_ascii=False, indent=1)
    md = [f'# 검수 보고: {rep["file"]}', '', f'- {w}×{h}, {fps:.0f}fps, {dur:.1f}초, 컷 {len(cut_times)}개',
          f'- 음량 {au.get("lufs")} LUFS, 트루 피크 {au.get("true_peak")} dBFS',
          f'- 깜박임 평균 {fl["flicker_mean"]:.2f} / 최대 칸 {fl["flicker_max_cell"]:.2f}, 떨림 평균 {fl["jitter_mean"]:.2f}', '',
          '## P0 (올리면 안 됨)'] + [f'- {x}' for x in P0 or ['없음']] + ['', '## P1 (고치면 좋아짐)'] + [f'- {x}' for x in P1 or ['없음']] + \
         ['', '## 사람이 봐야 할 것'] + [f'- {x}' for x in HUMAN] + ['', '## 그림'] + [f'- {x}' for x in rep['images']]
    open(os.path.join(out, 'report.md'), 'w').write('\n'.join(md) + '\n')
    return rep


def main():
    ap = argparse.ArgumentParser(prog='vfx.qa')
    ap.add_argument('cmd', choices=['sheet', 'cuts', 'phone', 'flicker', 'audio', 'report'])
    ap.add_argument('mp4'); ap.add_argument('--out', default='qa_out'); ap.add_argument('--n', type=int, default=8)
    a = ap.parse_args()
    if a.cmd != 'audio': os.makedirs(a.out, exist_ok=True)
    if a.cmd == 'sheet': print(cmd_sheet(a.mp4, a.out, a.n))
    elif a.cmd == 'cuts': print(cmd_cuts(a.mp4, a.out))
    elif a.cmd == 'phone': print(cmd_phone(a.mp4, a.out))
    elif a.cmd == 'flicker': print(json.dumps(cmd_flicker(a.mp4, a.out)[1], ensure_ascii=False, indent=1))
    elif a.cmd == 'audio': print(json.dumps(cmd_audio(a.mp4), ensure_ascii=False, indent=1))
    else:
        r = cmd_report(a.mp4, a.out)
        print(open(os.path.join(a.out, 'report.md')).read())


if __name__ == '__main__':
    main()
