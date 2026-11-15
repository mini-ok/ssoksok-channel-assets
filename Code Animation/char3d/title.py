"""〈심장의 휴가〉 끝 타이틀(8초, 960×540): 어둠 속 박동 두 번 → 제목 → 허상공방 白文 인장 + 크레딧(오른쪽 아래).
사용: python3 title.py out.mp4"""
import os, sys, subprocess, numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont
D = os.path.dirname(os.path.abspath(__file__))
K = float(os.environ.get('TITLE_SCALE', '1'))   # 1 = 960×540, 1.3333 = 1280×720
W, H, FPS, DUR = int(960 * K), int(540 * K), 24, 8.0
BG = np.array([16, 8, 18], np.float32) / 255          # BGR, 아주 어두운 자두색
WARM = np.array([120, 110, 255], np.float32) / 255     # BGR, 심장빛
CREAM = np.array([226, 240, 246], np.float32) / 255
SERIF_B = '/usr/share/fonts/opentype/noto/NotoSerifCJK-Bold.ttc'; SERIF_R = '/usr/share/fonts/opentype/noto/NotoSerifCJK-Regular.ttc'
smooth = lambda u: (lambda v: v * v * (3 - 2 * v))(np.clip(u, 0, 1))
ramp = lambda t, a, b: (t - a) / (b - a)

def text_mask(lines):
    im = Image.new('L', (W, H), 0); d = ImageDraw.Draw(im)
    for s, x, y, size, path, anchor in lines:
        d.text((x, y), s, font=ImageFont.truetype(path, size, index=1), fill=255, anchor=anchor)
    return cv2.GaussianBlur(np.asarray(im, np.float32) / 255, (0, 0), 0.4)

TITLE = text_mask([('심장의 휴가', W / 2, 246 * K, int(44 * K), SERIF_B, 'mm')])
SUB = text_mask([('The Heart Takes a Day Off', W / 2, 300 * K, int(26 * K), SERIF_R, 'mm')])
SZ = int(52 * K); XS, YS = int(W - 40 * K - SZ), int(H - 36 * K - SZ)
CRED = text_mask([('Created & Coded by L.S.M.', XS - 12 * K, YS + 1 * K, int(13 * K), SERIF_R, 'ra'), ('허상공방 虛像工房 Project', XS - 12 * K, YS + SZ - 16 * K, int(13 * K), SERIF_R, 'ra')])
_s = np.load(os.path.join(D, '..', '_shared', 'seal_baimun3.npy')).astype(np.float32)
_r = np.argwhere((_s[..., 0] - _s[..., 1] > 0.25) & (_s[..., 3] > 0.5)); (_y0, _x0), (_y1, _x1) = _r.min(0), _r.max(0)   # 인주 묻은 네모만(바깥 종이 테두리는 뺌)
seal = cv2.resize(_s[_y0:_y1 + 1, _x0:_x1 + 1], (SZ, SZ), interpolation=cv2.INTER_AREA)[..., [2, 1, 0, 3]]
yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
GLOW = np.exp(-(((xx - W / 2) / (260 * K)) ** 2 + ((yy - 250 * K) / (170 * K)) ** 2))[..., None]

def frame(t):
    img = np.broadcast_to(BG, (H, W, 3)).copy()
    beat = sum(np.exp(-max(0, t - tb) / 0.35) * (t >= tb) for tb in (0.4, 2.2))      # 박동 두 번에 따뜻한 빛이 번짐
    img += GLOW * WARM * (0.22 * beat + 0.10 * smooth(ramp(t, 3.2, 4.4)))
    a = smooth(ramp(t, 3.4, 4.6)); img = img * (1 - TITLE[..., None] * a) + CREAM * TITLE[..., None] * a
    a = smooth(ramp(t, 4.0, 5.0)) * 0.8; img = img * (1 - SUB[..., None] * a) + CREAM * SUB[..., None] * a
    a = smooth(ramp(t, 5.2, 5.4))                                                   # 낙관: 찍힌다
    al = seal[..., 3:4] * a; sub = img[YS:YS + SZ, XS:XS + SZ]; img[YS:YS + SZ, XS:XS + SZ] = sub * (1 - al) + seal[..., :3] * al
    a = smooth(ramp(t, 5.7, 6.6)) * 0.85; img = img * (1 - CRED[..., None] * a) + CREAM * CRED[..., None] * a
    return (np.clip(img, 0, 1) * 255).astype(np.uint8)

if __name__ == '__main__':
    out = sys.argv[1]
    p = subprocess.Popen(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'bgr24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-', '-c:v', 'libx264', '-crf', '18', '-pix_fmt', 'yuv420p', out], stdin=subprocess.PIPE)
    for k in range(int(DUR * FPS)): p.stdin.write(frame(k / FPS).tobytes())
    p.stdin.close(); p.wait()
    cv2.imwrite(out.replace('.mp4', '_still.png'), frame(7.0)); print('ok')
