"""〈점〉 애니마틱 v2 (떨리는 손). 저해상도 확인용 — 검증된 시험 장면들을 이어 붙이고, 빠진 장면은 여기서 그린다.
사용: python3 animatic2.py cut C13   (컷 하나 렌더)   /   python3 animatic2.py all   /   python3 animatic2.py encode
프레임: cache/anim2/a#####.png (12fps). 미리 렌더된 시험 장면(tests/*)의 프레임을 그대로 가져다 쓰는 컷이 있다 —
그 시험들을 먼저 돌려 둘 것: test_hand2(JEOM_RES=0.25), test_knife, test_leap, test_storm, test_tear.
"""
import sys, os, math, subprocess, glob
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, 'engine')); sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, 'tests'))
os.environ.setdefault('JEOM_RES', '0.5')
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont
from paper import View, paper_layers, paper_rgb
from look import INK_ABS, light, film, letterbox
import timeline as TL
import inkmm

F32 = np.float32
from scale import S, W, H, SUF
FPS = 12
OUT = os.path.join(HERE, 'cache', 'anim2' + SUF); os.makedirs(OUT, exist_ok=True)
C = os.path.join(HERE, 'cache')
def ease(u): return u * u * (3 - 2 * u)
def ramp(t, a, b): return float(np.clip((t - a) / (b - a), 0, 1))

# ---------------------------------------------------------------- 컷표 (이름, 그리는 방법, 시작, 길이)
CUTS = [
    ('C1', 'room_paint', 0.0, 10.0),      # 화실 원경: 떨리는 손, 벽의 큰 그림자, 바구니
    ('C2', 'hand_A', 10.0, 5.4),          # 눈자리 근접: 두 번 내려가 두 번 미끄러짐
    ('C3', 'hand_B', 15.4, 3.2),          # 구석 근접: 물리는 붓에서 방울이 털려 떨어짐
    ('C4', 'knife', 18.6, 6.0),           # 칼로 자르다 떨려 비뚤어지고 멈춤
    ('C5', 'room_sleep', 24.6, 8.4),      # 등잔을 끄고 벽에 기대 잠듦, 비가 들기 시작
    ('J', 'journey', 33.0, 52.0),         # 점의 여정(구 C4~C10, 시간 압축) = C6~C12
    ('C13', 'melt', 85.0, 12.0),          # 폭우가 그림을 지운다
    ('C14', 'room_cut', 97.0, 5.0),       # 잠든 화가의 떨리는 손
    ('C15', 'weep', 102.0, 8.0),          # 눈동자에서도 먹이 흘러내림 → 창밖을 봄
    ('C16', 'leap', 110.0, 5.5),          # 그림 속 용이 그대로 솟아오름
    ('C17', 'storm', 115.5, 8.0),         # 먹구름을 휘감아 비를 거둠
    ('C18', 'room_wake', 123.5, 10.0),    # 새벽, 깨어남
    ('C19', 'trace', 133.5, 10.0),        # 남은 그림(걸작) + 칼을 내려놓음
    ('C20', 'tear', 143.5, 7.0),          # 눈물 → 눈동자 테
    ('C21', 'title', 150.5, 7.0),         # 제목·낙관
]
TOTAL = CUTS[-1][2] + CUTS[-1][3]
J_OLD = (22.0, 88.0)                      # 여정 구간이 쓰는 구 타임라인 시각
J_NAMES = {'C4': 'C6', 'C5': 'C7', 'C6': 'C8', 'C7': 'C9', 'C8': 'C10', 'C9': 'C11', 'C10': 'C12'}

# ---------------------------------------------------------------- 여정: 칼집 장벽과 바뀐 첫 물길
CUT = np.load(os.path.join(C, 'knife_cut.npy'))
TL.WATERS[1] = (26.0, [(58, 404)], 13, 0.30)                          # 첫 빗방울: 잘릴 조각 안, 목 쪽
TL.WATERS[2] = (31.0, inkmm.seg_seeds((74, 402), (84, 396), 1.0), 11, 0.35)   # 안 잘린 목
TL.WATERS[3] = (34.3, inkmm.seg_seeds((86, 388), (180, 285)), 4.5, 0.25)
TL.STAGES[1] = (26.6, (48, 398), 20, 0.50, 1.00, [0, 1])
TL.STAGES[2] = (32.0, (72, 401), 18, 0.55, 0.80, [1, 2])
TL.STAGES[3] = (35.6, (86, 390), 125, 0.90, 0.62, [2, 3])
import animatic as A
A.label = lambda img, t: img
_v = View((inkmm.X0 + inkmm.X1) / 2, (inkmm.Y0 + inkmm.Y1) / 2, inkmm.X1 - inkmm.X0, inkmm.GW, inkmm.GH)

def build_dot():
    fib, _, _, _, _ = paper_layers(_v)
    field = inkmm.Field(fib.astype(F32))
    gx = (CUT[:, 0] - inkmm.X0) / inkmm.RES; gy = (CUT[:, 1] - inkmm.Y0) / inkmm.RES
    m = np.zeros((inkmm.GH, inkmm.GW), np.uint8)
    cv2.polylines(m, [np.stack([gx, gy], 1).astype(np.int32)], False, 1, 2)
    field.cost[m > 0] = field.cost.max() * 400                        # 칼집은 물이 못 건넌다
    A._dot = inkmm.Dot(field, TL)

def slit(img, view):
    px, py = view.to_px(CUT[:, 0], CUT[:, 1])
    q = (np.stack([px, py], 1) * 2).astype(np.int32)
    m = np.zeros((H * 2, W * 2), F32)
    cv2.polylines(m, [q], False, 1.0, max(1, int(0.32 * view.ppm * 2)), cv2.LINE_AA)
    m = cv2.resize(m, (W, H), interpolation=cv2.INTER_AREA)
    lip = np.roll(np.roll(m, -1, 0), 1, 1)
    return img * (1 - 0.75 * m[..., None]) + 0.10 * np.clip(lip - m, 0, 1)[..., None]

_orig_draw = A.draw_objects
def _draw(img, view, t, rgbmul=1.0):
    return _orig_draw(slit(img, view), view, t, rgbmul)
A.draw_objects = _draw

# ---------------------------------------------------------------- 공통
FONT = A.FONT_K
def lab(img8, name, t):
    im = Image.fromarray(img8[..., ::-1].copy()); dr = ImageDraw.Draw(im)
    f = ImageFont.truetype(FONT, 15)
    s = f'{name}  {int(t // 60)}:{t % 60:04.1f}'
    dr.rectangle((6, H - 34, 6 + len(s) * 9 + 10, H - 12), fill=(0, 0, 0))
    dr.text((12, H - 33), s, font=f, fill=(235, 235, 235))
    return np.asarray(im)[..., ::-1]

def to8(img):
    return (np.clip(img, 0, 1)[..., ::-1] * 255 + 0.5).astype(np.uint8)

def fin(img, t, vig=0.22):
    return to8(letterbox(film(img, t, H=H, W=W, vig=vig, grain=0.012, weave=0.35)))

def borrowed(pattern, k):
    fs = sorted(glob.glob(pattern))
    return cv2.imread(fs[min(k, len(fs) - 1)])

# ---------------------------------------------------------------- 화실
_room = None
def room():
    global _room
    if _room is None:
        from room import Room
        _room = Room(W, H)
    return _room
from room import POSES, mix

def trem(t, amp, seed=3):
    q = math.floor(t * FPS) / FPS
    r = np.random.default_rng(int(q * FPS) * 17 + seed)
    return (amp * (0.6 * math.sin(2 * math.pi * 5.3 * q) + 0.4 * r.normal()), amp * 0.7 * (0.6 * math.sin(2 * math.pi * 6.1 * q + 1) + 0.4 * r.normal()))

def room_paint(lt):
    # 쉬었다 → 뻗어 떨림 → 거둠 → 다시 뻗음 → 거둠(심지가 줄어든다)
    keys = [(0, 0.0), (1.5, 0.0), (3.0, 1.0), (5.0, 1.0), (5.8, 0.0), (6.8, 0.0), (8.0, 1.0), (9.0, 1.0), (10, 0.3)]
    u = np.interp(lt, [k[0] for k in keys], [k[1] for k in keys]); u = math.floor(u * 6) / 6
    pose = mix(POSES['rest'], POSES['paint'], ease(u))
    tr = trem(lt, 0.0045 * u)
    img = room().render(lt, pose, tremor=tr, rain=0.0, lamp_on=1.0 - 0.15 * ramp(lt, 0, 10))
    return img * ease(ramp(lt, 0, 1.2))

def room_sleep(lt):
    lamp = 1.0 - ramp(lt, 1.6, 1.9)                                        # 등잔을 끈다
    u = ease(ramp(lt, 2.2, 5.0)); u = math.floor(u * 6) / 6
    pose = mix(POSES['rest'], POSES['sleep'], u)
    fx = math.exp(-(lt - 7.2) / 0.12) if lt >= 7.2 else 0.0
    return room().render(lt, pose, lamp_on=lamp, rain=ramp(lt, 4.8, 6.5), flash=fx)

def room_cut(lt):
    fx = max(math.exp(-(lt - 1.2) / 0.12) if lt >= 1.2 else 0, 0.6 * math.exp(-(lt - 1.35) / 0.12) if lt >= 1.35 else 0)
    pose = dict(POSES['sleep']); tr = trem(lt, 0.0035)
    return room().render(lt + 50, pose, lamp_on=0.0, rain=1.0, flash=fx, tremor=tr)

def room_wake(lt):
    dawn = 0.35 + 0.65 * ease(ramp(lt, 0, 4))
    u1 = ease(ramp(lt, 2.5, 5.5)); u2 = ease(ramp(lt, 6.5, 9.0))
    look = dict(POSES['paint']); look['brush'] = 0.0
    pose = mix(mix(POSES['sleep'], POSES['wake'], math.floor(u1 * 6) / 6), look, math.floor(u2 * 6) / 6)
    return room().render(lt + 90, pose, lamp_on=0.0, rain=0.0, dawn=dawn)

# ---------------------------------------------------------------- 여정(구 애니마틱 엔진)
def journey(lt):
    t_old = J_OLD[0] + lt * (J_OLD[1] - J_OLD[0]) / 52.0
    img = A.frame(t_old)                                                   # 필름·레터박스까지 된 float
    name = TL.cut_at(math.floor(t_old * 12) / 12)[0]
    return to8(img), J_NAMES.get(name, name)

# ---------------------------------------------------------------- 지워지는 그림(폭우)
_melt = {}
def melt_state(u, view):
    key = (view.cx, view.cy, view.width_mm if hasattr(view, 'width_mm') else 0, round(u, 3))
    X, Y = view.grid_mm()
    p = A.plate_for('C5')
    rgb, fib, drg = p.sample(X, Y)
    D = A.dot(); dens_g = D.density(88.0); pup = D.pupil
    trail = inkmm.sample(dens_g - (pup if pup is not None else 0), view, X, Y)
    pv = inkmm.sample(pup, view, X, Y) if pup is not None else 0 * X
    L = max(1, int(30 * u * view.ppm))                                    # 아래로 흘러내린 길이(px)
    k = np.zeros((2 * L + 1, 1), F32); k[L:, 0] = np.exp(-np.arange(L + 1) / max(1, L * 0.45)); k /= k.sum()
    run = cv2.filter2D(drg, -1, k[::-1], borderType=cv2.BORDER_CONSTANT)
    runs = drg * (1 - 0.55 * u) + run * 0.9 * u
    return rgb, fib, runs, trail, pv, X, Y

def melt(lt):
    view = View(330, 215, 600, W, H)
    u = ease(ramp(lt, 0.8, 11.0))
    rgb, fib, runs, trail, pv, X, Y = melt_state(u, view)
    dens = runs + trail * (1 - 0.3 * u) + pv
    # 폭우: 굵은 빗줄기와 종이에 튀는 물
    rr = np.random.default_rng(int(lt * FPS))
    img = rgb * np.exp(-dens[..., None] * INK_ABS)
    sp = np.zeros((H, W), F32)
    for j in range(140):
        x, y = rr.uniform(0, W), rr.uniform(0, H)
        cv2.circle(sp, (int(x), int(y)), int(rr.uniform(1, 3)), 1.0, 1, cv2.LINE_AA)
    img = img * (1 - 0.18 * sp[..., None])
    fx = max(math.exp(-lt / 0.15), 0.7 * math.exp(-(lt - 5.0) / 0.12) if lt >= 5.0 else 0)
    img = light(img, 'night', extra=fx)
    return img

def weep(lt):
    view = View(306, 128, 120, W, H)
    u = 0.75 + 0.25 * ease(ramp(lt, 0, 8))
    rgb, fib, runs, trail, pv, X, Y = melt_state(u, view)
    # 눈동자에서 한 줄 흘러내림
    E = np.array(TL.E) if hasattr(TL, 'E') else np.array((300.0, 112.0))
    Lr = 22 * ease(ramp(lt, 1.0, 5.5))
    line = np.exp(-((X - E[0] - 1.0 - 0.08 * (Y - E[1])) / 0.9) ** 2) * ((Y > E[1]) & (Y < E[1] + Lr)) * (1 - (Y - E[1]) / (Lr + 1e-3) * 0.6)
    dens = runs + trail * 0.7 + pv + line * 1.4
    img = rgb * np.exp(-dens[..., None] * INK_ABS)
    # 마지막 2.5초: 눈 반사광이 창 쪽(오른쪽 위)으로 옮겨 감 = 창밖을 본다
    ex, ey = view.to_px(E[0] + 1.0, E[1])
    sh = ease(ramp(lt, 5.5, 6.5))
    gx, gy = ex - 4 + 6 * sh, ey - 4 - 2 * sh
    yy, xx = np.mgrid[0:H, 0:W].astype(F32)
    g = np.exp(-((xx - gx) ** 2 + (yy - gy) ** 2) / (0.7 * view.ppm) ** 2)
    fx = 0.8 * math.exp(-(lt - 6.6) / 0.12) if lt >= 6.6 else 0
    img = light(img, 'night', extra=fx) + (g * 0.8)[..., None]
    return img

# ---------------------------------------------------------------- 남은 그림 + 칼을 내려놓음
_trace = None
def trace(lt):
    global _trace
    import test_leap as Lp                                                 # 종이 판(PV)과 떠난 뒤 남은 것
    if _trace is None:
        z = np.load(os.path.join(C, 'leap', 'after.npz'))
        PVv = Lp.PV; X, Y = PVv.grid_mm()
        p = A.plate_for('C5')
        # 지워지다 만 용(흘러내림 0.75) 의 섬유 잔류 25% + 점이 지나간 길 + 비가 흘린 결 + 날며 뿌린 먹
        u = 0.75
        rgb, fib, runs, trail, pv, _, _ = melt_state(u, PVv)
        dens = Lp.CLOUD + runs * 0.20 + trail * 0.7 + z['splat'] + 0.05 * np.clip(cv2.GaussianBlur(z['wets'], (0, 0), 1.2), 0, 1)
        dens = dens * (1 - 0.0)
        _trace = (Lp.RGB * np.exp(-dens[..., None] * INK_ABS)).astype(F32)
    pap = _trace
    # 카메라: 0~4초 종이 전체(걸작이 드러남) → 4~10초 귀퉁이 쪽으로 다가감
    u = ease(ramp(lt, 4.0, 9.5))
    cx, cy, wmm = 320 + (110 - 320) * u, 215 + (360 - 215) * u, 700 + (260 - 700) * u
    PVv = Lp.PV
    s = PVv.ppm * wmm / W                                                  # 출력 1px당 판 px
    M = np.array([[s, 0, (cx - PVv.cx) * PVv.ppm + PVv.W / 2 - s * W / 2], [0, s, (cy - PVv.cy) * PVv.ppm + PVv.H / 2 - s * H / 2]], F32)
    img = cv2.warpAffine(pap, M, (W, H), flags=cv2.WARP_INVERSE_MAP | cv2.INTER_LINEAR, borderValue=(0.12, 0.08, 0.055))
    view = View(cx, cy, wmm, W, H)
    img = slit(img, view)
    # 칼: 자 위에서 들어 올려(그림자가 커짐) 목 위에서 떨며 머뭇 → 거둬 종이 밖에 내려놓음
    P0 = np.array((0.0, 318.0)); Uu = np.array((1.0, 1.0)) / math.sqrt(2); N = np.array((1.0, -1.0)) / math.sqrt(2)
    base = P0 + Uu * 110 + N * 8
    hover = P0 + Uu * 112 - N * 3
    away = np.array((-60.0, 470.0))
    if lt < 5.0: pos, h = base, 0.0
    elif lt < 6.2: pos, h = base + (hover - base) * ease(ramp(lt, 5.0, 6.2)), 12 * ease(ramp(lt, 5.0, 6.2))
    elif lt < 8.0:
        tr = trem(lt, 0.9); pos, h = hover + np.array(tr), 12.0
    else: pos, h = hover + (away - hover) * ease(ramp(lt, 8.0, 9.6)), 12 + 10 * ease(ramp(lt, 8.0, 9.6))
    d = np.array((0.25, 1.0)); d /= np.linalg.norm(d); e = np.array((-d[1], d[0]))
    blade = [pos, pos + d * 26 + e * 3.2, pos + d * 26 - e * 3.2]
    handle = [pos + d * 26 + e * 4.2, pos + d * 120 + e * 5.0, pos + d * 120 - e * 5.0, pos + d * 26 - e * 4.2]
    def pp(pts, off=(0, 0)):
        a = np.array(pts) + np.array(off); x, y = view.to_px(a[:, 0], a[:, 1]); return np.stack([x, y], 1).astype(np.int32)
    sh = np.zeros((H, W), F32); off = np.array((-0.6, 0.5)) * (h + 4)            # 아침 창빛(오른쪽 위) → 그림자는 왼쪽 아래
    cv2.fillPoly(sh, [pp(blade, off)], 1.0); cv2.fillPoly(sh, [pp(handle, off * 1.2)], 1.0)
    img = img * (1 - 0.4 * cv2.GaussianBlur(sh, (0, 0), 1 + 0.15 * h * view.ppm)[..., None])
    lay = np.zeros_like(img); m = np.zeros((H, W), F32)
    cv2.fillPoly(lay, [pp(handle)], (0.30, 0.19, 0.12)); cv2.fillPoly(m, [pp(handle)], 1.0)
    cv2.fillPoly(lay, [pp(blade)], (0.68, 0.70, 0.72)); cv2.fillPoly(m, [pp(blade)], 1.0)
    m = cv2.GaussianBlur(m, (0, 0), 0.7)[..., None]
    img = img * (1 - m) + lay * m
    return light(img, 'morning')

# ---------------------------------------------------------------- 제목
def title(lt):
    base = cv2.imread(sorted(glob.glob(os.path.join(C, 'tear', 'f', 't*.png')))[-1]).astype(F32)[..., ::-1] / 255
    tm = A.text_mask('점', 120)
    a = ease(ramp(lt, 0.8, 1.6))
    img = base * np.exp(-(tm * 2.4 * a)[..., None] * INK_ABS)
    # 낙관(허상공방) 오른쪽 아래
    rgba = A.seal_rgba()
    if lt > 2.6:
        s = 70; sm = cv2.resize(rgba, (s, s), interpolation=cv2.INTER_AREA)
        al = sm[..., 3:4] * ease(ramp(lt, 2.6, 3.0)); y0, x0 = H - 140, W - 170
        sub = img[y0:y0 + s, x0:x0 + s]; img[y0:y0 + s, x0:x0 + s] = sub * (1 - al) + sub * sm[..., :3] * 1.15 * al   # 인주는 종이에 곱해진다
    return img * (1 - ease(ramp(lt, 5.6, 7.0)))

# ---------------------------------------------------------------- 렌더
def frame(k):
    t = k / FPS
    for name, kind, t0, d in CUTS:
        if t0 <= t < t0 + d: break
    lt = t - t0; kk = int(round(lt * FPS))
    if kind == 'room_paint': f8 = fin(room_paint(lt), t)
    elif kind == 'room_sleep': f8 = fin(room_sleep(lt), t)
    elif kind == 'room_cut': f8 = fin(room_cut(lt), t)
    elif kind == 'room_wake': f8 = fin(room_wake(lt), t)
    elif kind == 'hand_A': f8 = borrowed(os.path.join(C, 'hand_test2', 'h*.png'), kk)
    elif kind == 'hand_B': f8 = borrowed(os.path.join(C, 'hand_test2', 'h*.png'), 65 + kk)
    elif kind == 'knife': f8 = borrowed(os.path.join(C, 'knife_test', 'k*.png'), kk)
    elif kind == 'journey':
        f8, name = journey(lt)
    elif kind == 'melt': f8 = fin(melt(lt), t)
    elif kind == 'weep': f8 = fin(weep(lt), t)
    elif kind == 'leap': f8 = borrowed(os.path.join(C, 'leap', 'f*.png'), kk)
    elif kind == 'storm': f8 = borrowed(os.path.join(C, 'storm', 's*.png'), kk)
    elif kind == 'trace': f8 = fin(trace(lt), t)
    elif kind == 'tear': f8 = borrowed(os.path.join(C, 'tear', 'f', 't*.png'), kk)
    elif kind == 'title': f8 = fin(title(lt), t, vig=0.15)
    return lab(f8, name, t)

def run(names):
    if any(c[1] in ('journey', 'melt', 'weep', 'trace') for c in CUTS if c[0] in names):
        build_dot()
    for name, kind, t0, d in CUTS:
        if name not in names: continue
        for k in range(int(round(t0 * FPS)), int(round((t0 + d) * FPS))):
            fn = os.path.join(OUT, f'a{k:05d}.png')
            if os.path.exists(fn): continue
            cv2.imwrite(fn, frame(k))
        print('done', name, flush=True)

def encode():
    import anim_audio2
    wav = os.path.join(C, 'animatic2.wav'); anim_audio2.build(wav, TOTAL)
    n = int(round(TOTAL * FPS))
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-framerate', str(FPS), '-i', os.path.join(OUT, 'a%05d.png'), '-i', wav,
                    '-vf', 'fps=24', '-c:v', 'libx264', '-crf', '22', '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-b:a', '192k',
                    '-shortest', os.path.join(C, 'jeom_animatic_v2.mp4')])

if __name__ == '__main__':
    cmd = sys.argv[1]
    if cmd == 'cut': run(sys.argv[2:])
    elif cmd == 'all': run([c[0] for c in CUTS])
    elif cmd == 'encode': encode()
    elif cmd == 'still':
        build_dot()
        for t in map(float, sys.argv[2:]):
            cv2.imwrite(os.path.join(C, f'a2_still_{t:06.2f}.png'), frame(int(round(t * FPS))))
