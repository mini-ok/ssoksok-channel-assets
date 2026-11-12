"""sheet.py name video  -> name_sheet.png : per cut 3 frames with the crop window drawn"""
import sys, json, subprocess, numpy as np, cv2
name, vid = sys.argv[1], sys.argv[2]
d = json.load(open(f'{name}_track.json'))
fps, cent, cuts, y0, ph = d['fps'], d['cent'], d['cuts'], d['y0'], d['ph']
cw = ph * 4 / 5
tiles = []
for ci, (a, b) in enumerate(zip(cuts[:-1], cuts[1:])):
    row = []
    for t in (a + 0.3, (a + b) / 2, b - 0.3):
        i = min(int(t * fps), len(cent) - 1)
        img = np.frombuffer(subprocess.check_output(['ffmpeg', '-loglevel', 'error', '-ss', str(t), '-i', vid, '-frames:v', '1',
                                                     '-f', 'rawvideo', '-pix_fmt', 'bgr24', '-']), np.uint8).reshape(1080, 1920, 3).copy()
        x0 = int(cent[i] - cw / 2)
        img = (img * 0.45).astype(np.uint8) if False else img
        dark = (img * 0.4).astype(np.uint8); dark[y0:y0 + ph, x0:x0 + int(cw)] = img[y0:y0 + ph, x0:x0 + int(cw)]
        cv2.rectangle(dark, (x0, y0), (x0 + int(cw), y0 + ph), (0, 255, 255), 6)
        row.append(cv2.resize(dark, (480, 270)))
    r = np.hstack(row)
    cv2.putText(r, f'#{ci + 1} {a:g}s', (8, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 0, 255), 2)
    tiles.append(r)
# two columns of rows
half = (len(tiles) + 1) // 2
L = np.vstack(tiles[:half]); Rr = np.vstack(tiles[half:] + [np.zeros_like(tiles[0])] * (half - len(tiles[half:])))
cv2.imwrite(f'{name}_sheet.png', np.hstack([L, np.full((L.shape[0], 12, 3), 255, np.uint8), Rr]))
