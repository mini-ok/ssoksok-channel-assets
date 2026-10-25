"""v2 스프라이트 빌드: 1920x1080 좌표에서 그림자 포함 RGBA로 한 번만 렌더 -> cache/*.npz (2/3 축소)"""
import sys, os, time, multiprocessing as mp
V = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, V); os.chdir(V)
from paper import *
from lay import *
CACHE = V + "/cache/"
os.makedirs(CACHE, exist_ok=True)
JOBS = {}
def job(name, fn, w=W, h=H, origin=(0, 0)): JOBS[name] = (fn, w, h, origin)

def _resize(ch, w, h):
    return np.asarray(Image.fromarray(ch.astype(np.float32), mode="F").resize((w, h), Image.LANCZOS))

def render_one(name):
    fn, w, h, origin = JOBS[name]
    path = CACHE + name + ".npz"
    t0 = time.time()
    if name.startswith("bg"):
        img = fn(None)
        sm = np.stack([_resize(img[..., i], 1280, 720) for i in range(3)], 2)
        np.save(CACHE + name + ".npy", (np.clip(sm, 0, 1) * 255 + 0.5).astype(np.uint8))
        return name, time.time() - t0
    B = fn(np.zeros((h, w, 3), np.float32)); Wt = fn(np.ones((h, w, 3), np.float32))
    a = np.clip(1 - (Wt - B).mean(2), 0, 1)
    ys, xs = np.where(a > 0.004)
    ox, oy = origin
    x0, x1, y0, y1 = xs.min() - 3, xs.max() + 4, ys.min() - 3, ys.max() + 4
    x0 = max(0, x0); y0 = max(0, y0); x1 = min(w, x1); y1 = min(h, y1)
    x0 -= (ox + x0) % 3; y0 -= (oy + y0) % 3
    while (x1 - x0) % 3: x1 += 1
    while (y1 - y0) % 3: y1 += 1
    pm = np.concatenate([np.clip(B, 0, 1)[y0:y1, x0:x1], a[y0:y1, x0:x1, None]], 2)
    cw, chh = (x1 - x0), (y1 - y0)
    out = np.stack([_resize(pm[..., i], cw * 2 // 3, chh * 2 // 3) for i in range(4)], 2)
    out = np.clip(out, 0, 1); out[..., :3] = np.minimum(out[..., :3], out[..., 3:4])
    np.savez(path, arr=(out * 255 + 0.5).astype(np.uint8), wx=ox + x0, wy=oy + y0, w=cw, h=chh)
    return name, time.time() - t0

# ================= 공통 그리기 =================
def cell(im, x, y, r, body, nuc, seed=0):
    im = puff(im, circ(W, H, x, y, r), body, seed, soft=max(6, r * 0.15), shadow=(5, 7), sh_blur=7, sh_k=0.22)
    im = puff(im, circ(W, H, x + r * 0.16, y - r * 0.1, r * 0.36), nuc, seed + 1, soft=max(4, r * 0.1), shadow=(3, 4), sh_blur=4, sh_k=0.25)
    im = puff(im, circ(W, H, x - r * 0.42, y + r * 0.36, r * 0.11), nuc, seed + 2, soft=3, shadow=(2, 2), sh_blur=3, sh_k=0.2)
    return im

def road(im, y0, amp, thick, seed=0, col=hx(0xF2B2A6)):
    xs = np.linspace(-30, W + 30, 130)
    cy = y0 + amp * np.sin(xs / 230.0)
    top = [(x, y - thick / 2) for x, y in zip(xs, cy)]; bot = [(x, y + thick / 2) for x, y in zip(xs, cy)][::-1]
    im = puff(im, poly_mask(W, H, top + bot), col, seed, soft=8, shadow=(0, 5), sh_blur=7, sh_k=0.2, depth=0.7)
    p = skia.Path(); p.moveTo(xs[0], cy[0])
    for x, y in zip(xs[1:], cy[1:]): p.lineTo(x, y)
    m = M(W, H); m.cv.drawPath(p, paint(9, dash=[38, 30]))
    return puff(im, m.arr(), hx(0xFBF4E8), seed + 1, soft=3, shadow=(1, 2), sh_blur=2, sh_k=0.15, depth=0.5)

def clock_face(im, cx, cy, R, seed=0):
    im = puff(im, circ(W, H, cx, cy, R + 16), hx(0xEE9A8E), seed, soft=11, shadow=(6, 9), sh_blur=9, sh_k=0.28)
    im = puff(im, circ(W, H, cx, cy, R - 4), hx(0xFBF7EC), seed + 1, soft=9, shadow=(2, 3), sh_blur=3, sh_k=0.15, depth=0.5)
    for i in range(12):
        a = math.radians(i * 30 - 90); big = i % 3 == 0
        if big: continue
        im = puff(im, circ(W, H, cx + math.cos(a) * (R - 24), cy + math.sin(a) * (R - 24), R * (0.045 if big else 0.028)), hx(0x7C87A8), seed + 2, soft=3, shadow=(1, 1), sh_blur=2, sh_k=0.15, depth=0.4)
    for i, s in ((0, "12"), (3, "3"), (6, "6"), (9, "9")):
        a = math.radians(i * 30 - 90); sz = R * 0.27
        im, _ = put_text(im, W, H, s, cx + math.cos(a) * (R - 56 * R / 180), cy + math.sin(a) * (R - 56 * R / 180) + sz * 0.34, sz, "do", hx(0x4A5470), "c", shadow=False)
    return im

def draw_alarm(im, cx, cy, s, seed=0):
    for sx in (-1, 1):
        im = puff(im, circ(W, H, cx + sx * 46 * s, cy - 54 * s, 27 * s), hx(0xF0B53A), seed, soft=5 * s + 2, shadow=(3, 4), sh_blur=4, sh_k=0.2)
        im = puff(im, circ(W, H, cx + sx * 42 * s, cy + 66 * s, 12 * s), hx(0xC9615A), seed + 1, soft=3, shadow=(2, 2), sh_blur=3, sh_k=0.2)
    im = puff(im, circ(W, H, cx, cy - 74 * s, 9 * s), hx(0xF0B53A), seed + 2, soft=3, shadow=(2, 2), sh_blur=2, sh_k=0.2)
    im = puff(im, circ(W, H, cx, cy, 64 * s), hx(0xEE8378), seed + 3, soft=8 * s + 2, shadow=(5, 7), sh_blur=7, sh_k=0.25)
    im = puff(im, circ(W, H, cx, cy, 48 * s), hx(0xFBF7EC), seed + 4, soft=6 * s + 2, shadow=(1, 2), sh_blur=3, sh_k=0.12, depth=0.5)
    m = M(W, H)
    m.cv.drawLine(cx, cy, cx, cy - 33 * s, paint(7 * s)); m.cv.drawLine(cx, cy, cx + 22 * s, cy + 8 * s, paint(7 * s))
    im = puff(im, m.arr(), hx(0xD9574E), seed + 5, soft=2.5, shadow=(1, 1), sh_blur=2, sh_k=0.1, depth=0.4)
    for i in (0, 3, 6, 9):
        a = math.radians(i * 30 - 90)
        im = puff(im, circ(W, H, cx + math.cos(a) * 38 * s, cy + math.sin(a) * 38 * s, 3.2 * s), hx(0x7C87A8), seed + 6, soft=2, shadow=(0, 0), sh_k=0, depth=0.3)
    return im

def stripes(l, t, r, b, period=84, c1=hx(0xF4F1EA), c2=hx(0x2F3A5C)):
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    m = (np.floor((xx + yy) / period) % 2 == 0)
    return np.where(m[..., None], c1[None, None, :], c2[None, None, :]).astype(np.float32)

def window_frame(im, l, t, r, b, seed=0):
    outer = rr(W, H, l - 24, t - 24, r + 24, b + 24, 22); inner = rr(W, H, l, t, r, b, 8)
    cx, cy = (l + r) / 2, (t + b) / 2
    bars = np.clip(rr(W, H, cx - 8, t, cx + 8, b, 3) + rr(W, H, l, cy - 8, r, cy + 8, 3), 0, 1)
    fr = np.clip(outer - inner, 0, 1); fr = np.maximum(fr, bars * inner)
    im = puff(im, fr, hx(0xFBF8F0), seed, soft=6, shadow=(5, 7), sh_blur=7, sh_k=0.25, depth=0.8)
    return puff(im, rr(W, H, l - 40, b + 6, r + 40, b + 34, 12), hx(0xF1E9DA), seed + 1, soft=5, shadow=(4, 6), sh_blur=6, sh_k=0.25, depth=0.7)

# ================= 배경 =================
def bg_office(top, bot, wains, seed, clock, win, notes):
    def fn(_):
        im = bg(W, H, top, bot, seed)
        im = puff(im, rr(W, H, -40, 650, W + 40, 1300, 0), wains, seed + 1, soft=8, shadow=(0, -7), sh_blur=8, sh_k=0.18, depth=0.5)
        im = puff(im, rr(W, H, -40, 905, W + 40, 1300, 0), hx(0xF1DAC8), seed + 2, soft=8, shadow=(0, -7), sh_blur=8, sh_k=0.2, depth=0.5)
        im = road(im, 990, 20, 74, seed + 3)
        # 세포 장식
        for k, (x, y, r, b_, n_) in enumerate(((120, 560, 58, hx(0xFBF7EC), CORAL_L), (1840, 520, 50, hx(0xFBF7EC), MINT_L), (630, 560, 38, hx(0xFFFFFF), YEL), (60, 830, 40, hx(0xFBF7EC), LAV))):
            if (x, y) == (630, 560) and notes: continue
            im = cell(im, x, y, r, b_, n_, seed + 10 + k * 3)
        # 창문 유리(구름은 동적)
        l, t, r_, b = win
        glass = bg(W, H, hx(0xB9DAF0), hx(0xDDEFF6), 3)
        im = puff_rgb(im, rr(W, H, l, t, r_, b, 8), glass, seed + 20, soft=5, shadow=(0, 0), sh_k=0, depth=0.3)
        im = clock_face(im, *clock, seed + 30)
        if notes:
            for k, (l_, t_, r2, b_, rot, c) in enumerate(((1530, 80, 1670, 220, -4, YEL), (1690, 100, 1830, 240, 5, CORAL_L))):
                im = puff(im, rr(W, H, l_, t_, r2, b_, 6, rot), c, seed + 40 + k, soft=4, shadow=(4, 6), sh_blur=5, sh_k=0.25, depth=0.6)
                m = np.clip(rr(W, H, l_ + 22, t_ + 40, r2 - 22, t_ + 50, 4, rot) + rr(W, H, l_ + 22, t_ + 70, r2 - 40, t_ + 80, 4, rot) + rr(W, H, l_ + 22, t_ + 100, r2 - 30, t_ + 110, 4, rot), 0, 1)
                im = puff(im, m, hx(0xFFFFFF) * 0.92, seed + 50 + k, soft=2, shadow=(0, 0), sh_k=0, depth=0.2)
        # 모니터(뇌 팀장 뒤)
        im = puff(im, rr(W, H, 1670, 740, 1730, 820, 6), hx(0xDAD3C4), seed + 60, soft=4, shadow=(0, 0), sh_k=0)
        im = puff(im, rr(W, H, 1540, 520, 1860, 760, 30), hx(0xF3EFE5), seed + 61, soft=8, shadow=(6, 9), sh_blur=9, sh_k=0.26)
        im = puff(im, rr(W, H, 1566, 546, 1834, 722, 16), hx(0xCBE5EE), seed + 62, soft=5, shadow=(0, 0), sh_k=0, depth=0.3)
        mm = M(W, H); p = skia.Path(); p.moveTo(1590, 640)
        for (x, y) in ((1640, 640), (1665, 590), (1700, 690), (1730, 610), (1760, 640), (1810, 640)): p.lineTo(x, y)
        mm.cv.drawPath(p, paint(10))
        im = puff(im, mm.arr(), CORALC, seed + 63, soft=3, shadow=(1, 2), sh_blur=2, sh_k=0.12, depth=0.4)
        return im
    return fn

job("bgA", bg_office(hx(0xDDEBE3), hx(0xD0E5DA), hx(0xBEDCCD), 11, CLK_A, WIN_A, True))
job("bgB", bg_office(hx(0xF8E7D2), hx(0xF3DDC6), hx(0xEBCDAF), 21, CLK_B, WIN_B, False))

def desk(im):
    im = puff(im, rr(W, H, 880, DESK_TOP, 2100, 1300, 34), hx(0xE4B38A), 70, soft=9, shadow=(-4, -8), sh_blur=10, sh_k=0.3)
    im = puff(im, rr(W, H, 880, DESK_TOP, 2100, 846, 34), hx(0xF5D4B0), 71, soft=7, shadow=(0, 4), sh_blur=5, sh_k=0.15, depth=0.6)
    im = puff(im, rr(W, H, 1000, 900, 1500, 1040, 20), hx(0xD9A57B), 72, soft=6, shadow=(3, 4), sh_blur=5, sh_k=0.2, depth=0.6)
    im = puff(im, circ(W, H, 1250, 970, 16), CORAL_L, 73, soft=4, shadow=(2, 3), sh_blur=3, sh_k=0.2)
    im = puff(im, rr(W, H, 1600, 900, 1900, 1040, 20), hx(0xD9A57B), 74, soft=6, shadow=(3, 4), sh_blur=5, sh_k=0.2, depth=0.6)
    im = puff(im, circ(W, H, 1750, 970, 16), CORAL_L, 75, soft=4, shadow=(2, 3), sh_blur=3, sh_k=0.2)
    # 서류 더미(왼쪽), 머그(오른쪽)
    for k, (l, t, r, b, c) in enumerate(((930, 778, 1110, 812, hx(0xF4F1EA)), (938, 750, 1104, 782, hx(0xFFFFFF)), (934, 722, 1098, 754, hx(0xF6E7A8)))):
        im = puff(im, rr(W, H, l, t, r, b, 7), c, 76 + k, soft=4, shadow=(3, 4), sh_blur=4, sh_k=0.22, depth=0.6)
    im = puff(im, rr(W, H, 1062, 730, 1116, 750, 6), CORAL_L, 80, soft=3, shadow=(2, 2), sh_blur=3, sh_k=0.2)
    im = puff(im, ring(W, H, 1818, 770, 20, 11), hx(0xEE9A8E), 81, soft=4, shadow=(2, 3), sh_blur=3, sh_k=0.2)
    im = puff(im, rr(W, H, 1736, 724, 1814, 812, 18), hx(0xF4B3A8), 82, soft=6, shadow=(4, 6), sh_blur=5, sh_k=0.25)
    return im
job("desk", desk)

job("winA", lambda im: window_frame(im, *WIN_A, 90))
job("winB", lambda im: window_frame(im, *WIN_B, 91))
for k, (x, y, s, nc) in enumerate(((880, 230, 0.8, CORAL_L), (1040, 180, 0.6, MINTC), (960, 310, 0.5, YEL))):
    def wc(im, x=x, y=y, s=s, nc=nc, k=k):
        im = puff(im, cloud(W, H, x, y, s), hx(0xFFFFFF), 100 + k, soft=8 * s + 3, shadow=(3, 5), sh_blur=5, sh_k=0.14)
        return puff(im, circ(W, H, x + 8 * s, y + 2 * s, 17 * s), nc, 110 + k, soft=4, shadow=(2, 2), sh_blur=3, sh_k=0.2)
    job(f"wc{k}", wc)

# 시계 바늘(회전 중심 CLK_B)
def hand(length, width, col, tail=18, cap=False):
    def fn(im):
        cx, cy = CLK_B[0], CLK_B[1]
        m = rr(W, H, cx - width / 2, cy - length, cx + width / 2, cy + tail, width / 2)
        im = puff(im, m, col, 120, soft=4, shadow=(3, 4), sh_blur=4, sh_k=0.22, depth=0.6)
        return im
    return fn
job("hand_min", hand(132, 13, CORALC)); job("hand_hr", hand(90, 18, hx(0x3B4668)))
job("hand_sec", hand(150, 6, hx(0x4A5470), 30))
job("clk_cap", lambda im: puff(im, circ(W, H, CLK_B[0], CLK_B[1], 15), hx(0x3B4668), 121, soft=4, shadow=(2, 3), sh_blur=3, sh_k=0.25))
def wedge(im):
    cx, cy = CLK_B[0], CLK_B[1]; R = 150
    p = skia.Path(); p.moveTo(cx, cy); p.arcTo(skia.Rect(cx - R, cy - R, cx + R, cy + R), -90, 120, False); p.close()
    return puff(im, path_mask(W, H, p), hx(0x82CDAA), 122, soft=6, shadow=(0, 0), sh_k=0, depth=0.5)
job("wedge", wedge)

# ================= 캐릭터 =================
BX, BY, BSZ = BRAIN
job("brain_sleepy", lambda im: puff_char(im, char_fn("brain", "sleepy", feet=False, shadow=False), BX, BY, BSZ, 20))
job("brain_happy", lambda im: puff_char(im, char_fn("brain", "happy", feet=False, shadow=False), BX, BY, BSZ, 20))
mx, my, mS = MEL
job("mel_body", lambda im: puff_char(im, char_fn("melatonin", "happy", feet=False, shadow=False, lantern=False), mx, my, mS, 21))
def foot_fn(sx, col, yy=138):
    def fn(cv, S):
        s = S / 576; cv.save(); cv.translate(S / 2, S * 0.62); cv.scale(s, s)
        r = skia.Rect.MakeXYWH(sx * 56 - 31, yy - 17, 62, 34); cv.drawOval(r, CH.P(col)); cv.drawOval(r, CH.P(CH.INK, "stroke", 6)); cv.restore()
    return fn
for nm, sx in (("L", -1), ("R", 1)):
    job(f"mel_foot{nm}", lambda im, sx=sx: puff_char(im, foot_fn(sx, 0xC4B5FF, 136), mx, my, mS, 22, soft=6))
cx_, cy_, cS = BC
job("bc_body", lambda im: puff_char(im, char_fn("brain", "happy", feet=False, shadow=False), cx_, cy_, cS, 23))
job("bc_up", lambda im: puff_char(im, char_fn("brain", "awake", feet=False, shadow=False, arms_up=True), cx_, cy_, cS, 23))
job("bc_body2", lambda im: puff_char(im, char_fn("brain", "wow", feet=False, shadow=False), cx_, cy_, cS, 23))
for nm, sx in (("L", -1), ("R", 1)):
    job(f"bc_foot{nm}", lambda im, sx=sx: puff_char(im, foot_fn(sx, 0xF6C9AE, 136), cx_, cy_, cS, 24, soft=6))
def shadow_fn(x, y, w, h, k=0.30):
    def fn(im):
        m = M(W, H); m.cv.drawOval(skia.Rect(x - w / 2, y - h / 2, x + w / 2, y + h / 2), paint()); a = ndi.gaussian_filter(m.arr(), 7) * k
        return im * (1 - a[..., None]) + 0.12 * a[..., None]
    return fn
job("sh_mel", shadow_fn(960, 925, 230, 40)); job("sh_bc", shadow_fn(1630, 944, 250, 40)); job("sh_brain", shadow_fn(1450, 940, 10, 10))
job("alarm", lambda im: draw_alarm(im, 800, 540, 1.0, 130))
def alarm_fx(im):
    m = M(W, H)
    for sx in (-1, 1):
        for k, rad in enumerate((98, 124)):
            p = skia.Path(); st = 152 if sx < 0 else -28
            p.addArc(skia.Rect(800 - rad, 540 - rad, 800 + rad, 540 + rad), st, 56); m.cv.drawPath(p, paint(10))
    return puff(im, m.arr(), hx(0xF0A33A), 131, soft=3, shadow=(2, 3), sh_blur=3, sh_k=0.18, depth=0.5)
job("alarm_fx", alarm_fx)

# ================= 장면 1 글자 =================
CH1 = [("c0", "낮잠,", "black", 150, hx(0xF6DE8C), -2.0), ("c1", "몇 분이", "jua", 140, hx(0xCFE4F2), 1.8),
       ("c2", "딱", "do", 215, hx(0xF7B8AB), -3.0), ("c3", "좋을까", "black", 150, hx(0xBFE8D4), 1.4)]
for nm, s, face, size, col, rot in CH1:
    job(f"a_{nm}", lambda im, s=s, face=face, size=size, col=col, rot=rot: chip(im, W, H, s, 960, 540, size, face, col, 30 + len(s), rot)[0])
def qmark(im):
    im = puff(im, circ(W, H, 960, 540, 88), hx(0xEE8479), 40, soft=9, shadow=(6, 9), sh_blur=8, sh_k=0.28)
    return put_text(im, W, H, "?", 960, 540 + 170 * 0.35, 170, "black", hx(0xFFF6EA), "c", shadow=True)[0]
job("a_q", qmark)
job("a_small", lambda im: put_text(im, W, H, "1분 몸속 이야기", 960, 540, 46, "jua", hx(0x4A5470), "c")[0])
for k, (ch, size, col) in enumerate((("Z", 150, hx(0xB5A9EC)), ("z", 112, hx(0xF2D36B)), ("z", 84, hx(0xF4A99E)))):
    def zz(im, ch=ch, size=size, col=col, k=k):
        t, w = text_m(W, H, ch, 960, 540 + size * 0.35, size, "black", "c")
        return puff(im, t, col, 50 + k, soft=5, shadow=(5, 7), sh_blur=6, sh_k=0.26, depth=0.8)
    job(f"a_z{k}", zz)

# ================= 슬레이트 =================
def slate_board(im):
    l, r, t, b = 460, 1460, 410, 990
    im = puff(im, rr(W, H, l, t, r, b, 24), hx(0x4B5778), 140, soft=9, shadow=(8, 12), sh_blur=12, sh_k=0.34)
    im = puff_rgb(im, rr(W, H, l, t, r, t + 78, 14), stripes(l, t, r, t + 78), 141, soft=5, shadow=(0, 0), sh_k=0, depth=0.6)
    cream = hx(0xF4EFE2)
    im, _ = put_text(im, W, H, "낮잠 편", l + 50, 600, 90, "black", cream, shadow=False)
    im, _ = put_text(im, W, H, "장면 2", l + 50, 690, 56, "jua", hx(0xBFC8E0), shadow=False)
    im, _ = put_text(im, W, H, "테이크 1", l + 50, 770, 56, "jua", hx(0xBFC8E0), shadow=False)
    for yy in (708, 788):
        im = over(im, rr(W, H, l + 50, yy, r - 50, yy + 4, 2), hx(0x6F7BA0))
    return im
job("slate_board", slate_board)
job("slate_bar", lambda im: puff_rgb(im, rr(W, H, 460, 332, 1460, 410, 14), stripes(460, 332, 1460, 410, c1=hx(0xF4F1EA), c2=hx(0x2F3A5C)), 142, soft=5, shadow=(5, 7), sh_blur=7, sh_k=0.3, depth=0.6))
job("a_action", lambda im: chip(im, W, H, "액션!", 960, 540, 230, "black", hx(0xF6CB45), 143, -4.0, padx=44, pady=22, rad=34)[0])
job("spk", lambda im: puff(im, star(W, H, 960, 540, 26, -90, 0.5, 2), STAR, 150, soft=4, shadow=(3, 4), sh_blur=3, sh_k=0.2))
job("spk2", lambda im: puff(im, circ(W, H, 960, 540, 13), CORAL_L, 151, soft=3, shadow=(2, 3), sh_blur=3, sh_k=0.2))
job("spk3", lambda im: puff(im, circ(W, H, 960, 540, 13), hx(0xA8DCC5), 152, soft=3, shadow=(2, 3), sh_blur=3, sh_k=0.2))

# ================= 장면 2 글자 =================
def star20(im):
    cx, cy, r = 960, 296, 226
    im = puff(im, star(W, H, cx, cy, r, -90, 0.64, 18), STAR, 160, soft=11, shadow=(8, 12), sh_blur=12, sh_k=0.30, depth=0.9)
    s1, s2 = 186, 98
    w1, w2, w3 = tw("20", s1, "black"), tw("분", s2, "black"), tw("!", s2, "black")
    print("star text width", w1 + w2 + w3)
    x = cx - (w1 + w2 + w3 + 4) / 2; yb = cy + 56
    im, _ = put_text(im, W, H, "20", x, yb, s1, "black", hx(0x26304F))
    im, _ = put_text(im, W, H, "분", x + w1 + 2, yb, s2, "black", hx(0x26304F))
    im, _ = put_text(im, W, H, "!", x + w1 + w2 + 4, yb, s2, "black", hx(0xE2574C))
    return im
job("b_star", star20)
def pill(im):
    cx, cy = 470, 600
    segs = [("어른 낮잠은 ", "jua", 54, TXT), ("20분", "black", 62, hx(0xE2574C)), (" 이내", "jua", 54, TXT)]
    tot = sum(tw(s, sz, f) for s, f, sz, c in segs); w = tot + 80; h = 150
    im = puff(im, rr(W, H, cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2, 40), hx(0xFFF6E6), 170, soft=8, shadow=(6, 9), sh_blur=8, sh_k=0.26, depth=0.8)
    x = cx - tot / 2
    for s, f, sz, c in segs:
        im, ww = put_text(im, W, H, s, x, cy - 6 + 0.0, sz, f, c, shadow=False); x += ww
    im, _ = put_text(im, W, H, "(NIH 권고)", cx, cy + 46, 38, "jua", hx(0x5A6690), "c", shadow=False)
    print("pill w", w)
    return im
job("b_pill", pill)

# ================= 장면 3 =================
SW, SH, SO = 1920, 1200, (0, -120)
def wave_top(base, amp, ph):
    xs = np.linspace(0, W, 90)
    return [(x, base + amp * math.sin(x / 190 + ph) + 0.4 * amp * math.sin(x / 71 + ph * 2)) for x in xs]
def sheet_mask(base, amp, ph):
    pts = wave_top(base, amp, ph); return poly_mask(SW, SH, [(0, SH + 5)] + [(x, y + 120) for x, y in pts] + [(W, SH + 5)])
def sheet_coral(im):
    rgb = bg(SW, SH, hx(0xF5B5A8), hx(0xF1AA9D), 7)
    return puff_rgb(im, sheet_mask(-112, 14, 0.6), rgb, 180, soft=9, shadow=(0, -10), sh_blur=12, sh_k=0.26, depth=0.7)
def sheet_main(im):
    rgb = bg(SW, SH, hx(0xE9E4F3), hx(0xEFE9F5), 8)
    al = sheet_mask(-70, 14, 0.2)
    im = puff_rgb(im, al, rgb, 181, soft=9, shadow=(0, -10), sh_blur=12, sh_k=0.26, depth=0.7)
    return im
SH_Y = 120   # 시트 캔버스 y = 화면 y + 120
def sheet_deco(im):
    def S(y): return y + SH_Y
    # 혈관 리본(카드 뒤)
    p = skia.Path(); p.moveTo(-60, S(820)); p.cubicTo(500, S(560), 900, S(1000), 1350, S(700)); p.cubicTo(1650, S(520), 1800, S(430), 2000, S(380))
    m = M(SW, SH); m.cv.drawPath(p, paint(100)); im = puff(im, m.arr(), hx(0xF5CBC1), 182, soft=9, shadow=(0, 6), sh_blur=8, sh_k=0.18, depth=0.7)
    m2 = M(SW, SH); m2.cv.drawPath(p, paint(8, dash=[40, 34])); im = puff(im, m2.arr(), hx(0xFBF4E8), 183, soft=3, shadow=(1, 2), sh_blur=2, sh_k=0.12, depth=0.4)
    for k, (x, y, r, b_, n_) in enumerate(((130, 250, 56, hx(0xFBF7EC), YEL), (1820, 250, 46, hx(0xFBF7EC), MINT_L), (120, 560, 38, hx(0xFFFFFF), CORAL_L), (1840, 640, 34, hx(0xFBF7EC), LAV))):
        pass
    # 턱(바닥 선반)
    im = puff(im, rr(SW, SH, -40, S(LEDGE), SW + 40, SH + 80, 0), hx(0xF2D1B8), 184, soft=8, shadow=(0, -8), sh_blur=9, sh_k=0.2, depth=0.5)
    return im
def sheet_c_all(im):
    im = sheet_main(im)
    # 장식 세포는 시트 좌표에서 직접
    for k, (x, y, r, b_, n_) in enumerate(((130, 270 + SH_Y, 54, hx(0xFBF7EC), YEL), (1830, 330 + SH_Y, 44, hx(0xFBF7EC), MINTC), (95, 600 + SH_Y, 36, hx(0xFFFFFF), CORAL_L), (1850, 760 + SH_Y, 34, hx(0xFBF7EC), LAV))):
        im = cell_s(im, x, y, r, b_, n_, 190 + k * 3)
    im = sheet_deco(im)
    return im
def cell_s(im, x, y, r, body, nuc, seed=0):
    im = puff(im, circ(SW, SH, x, y, r), body, seed, soft=max(6, r * 0.15), shadow=(5, 7), sh_blur=7, sh_k=0.22)
    im = puff(im, circ(SW, SH, x + r * 0.16, y - r * 0.1, r * 0.36), nuc, seed + 1, soft=max(4, r * 0.1), shadow=(3, 4), sh_blur=4, sh_k=0.25)
    return im
job("sheet_coral", sheet_coral, SW, SH, SO)
job("sheet_main", sheet_c_all, SW, SH, SO)

# 제목
TITLE_Y = 268
t1w, t2w = tw("낮잠 규칙", 140, "jua"), tw("3가지!", 196, "black")
TX0 = 780 - (t1w + 26 + t2w) / 2
job("c_t1", lambda im: put_text(im, W, H, "낮잠 규칙", TX0, TITLE_Y, 140, "jua", TXT)[0])
job("c_t2", lambda im: put_text(im, W, H, "3가지!", TX0 + t1w + 26, TITLE_Y, 196, "black", hx(0xE2655B))[0])
job("c_hl", lambda im: highlight(im, W, H, TX0 - 14, TX0 + t1w + 26 + t2w + 10, TITLE_Y - 70, 86, 4, hx(0xD3EC8E)))

CARDS = [("20분", "이내", hx(0xF8D4CE), hx(0xE2574C)), ("3시", "전", hx(0xF8E8B8), hx(0xD99422)), ("알람", "필수", hx(0xCFE3F1), hx(0x4B83C4))]
PRE = ["", "오후 ", ""]
def card_frame(k):
    def fn(im):
        x = CARD_X[k]; y = CARD_Y; rot = [-2.2, 1.6, -1.2][k]
        im = puff(im, rr(W, H, x - CARD_W / 2, y - CARD_H / 2, x + CARD_W / 2, y + CARD_H / 2, 12, rot), hx(0xFAF8F3), 200 + k, soft=6, shadow=(7, 11), sh_blur=11, sh_k=0.30, depth=0.6)
        return puff(im, rr(W, H, x - CARD_W / 2 + 24, y - CARD_H / 2 + 24, x + CARD_W / 2 - 24, y - CARD_H / 2 + 330, 8, rot), CARDS[k][2], 210 + k, soft=5, shadow=(0, 0), sh_k=0, depth=0.4)
    return fn
def card_content(k):
    def fn(im):
        x = CARD_X[k]; top = CARD_Y - CARD_H / 2; icy = top + 24 + 150
        if k == 0:
            im = puff(im, circ(W, H, x, icy, 84), hx(0xFBF7EC), 220, soft=8)
            m = M(W, H); m.cv.drawLine(x, icy, x, icy - 56, paint(11)); m.cv.drawLine(x, icy, x + 42, icy + 24, paint(11))
            im = puff(im, m.arr(), CORALC, 221, soft=3, shadow=(2, 2), sh_blur=2, sh_k=0.2)
        elif k == 1:
            im = puff(im, circ(W, H, x, icy, 62), SUNO, 222, soft=8)
            for a in range(0, 360, 45):
                rad = math.radians(a); im = puff(im, circ(W, H, x + math.cos(rad) * 96, icy + math.sin(rad) * 96, 12), STAR, 223 + a, soft=3)
        else:
            im = draw_alarm(im, x, icy + 6, 1.3, 224)
        pre, big, small, col = PRE[k], CARDS[k][0], CARDS[k][1], CARDS[k][3]
        szb, szs = 108, 62
        parts = []
        if pre: parts.append((pre.strip(), "jua", szs, TXT))
        parts.append((big, "black", szb, col)); parts.append((small, "jua", szs, TXT))
        gap = 12; tot = sum(tw(s, sz, f) for s, f, sz, c in parts) + gap * (len(parts) - 1)
        sc = min(1.0, 350 / tot); xx = x - tot * sc / 2; yb = top + CARD_H - 62
        for s, f, sz, c in parts:
            sz2 = sz * sc; im, ww = put_text(im, W, H, s, xx, yb, sz2, f, c); xx += ww + gap * sc
        return im
    return fn
for k in range(3):
    job(f"c_frame{k}", card_frame(k)); job(f"c_card{k}", card_content(k))
job("c_done", lambda im: chip(im, W, H, "개운!", 960, 540, 140, "black", hx(0xA6DEC3), 230, 4.0, padx=40, pady=22, rad=34)[0])
for k, (b_, n_) in enumerate(((hx(0xFBF7EC), CORAL_L), (hx(0xE3F3EA), hx(0x82CDAA)), (hx(0xFBF1D2), YEL), (hx(0xEDE8FA), LAV))):
    job(f"cell{k}", lambda im, b_=b_, n_=n_, k=k: cell(im, 900, 500, 56, b_, n_, 240 + k * 3))

if __name__ == "__main__":
    only = sys.argv[1:]
    names = [n for n in JOBS if (not only or n in only or any(n.startswith(o) for o in only if o.endswith("*")))]
    force = os.environ.get("FORCE")
    todo = [n for n in names if force or not os.path.exists(CACHE + n + (".npy" if n.startswith("bg") else ".npz"))]
    t0 = time.time()
    with mp.get_context("fork").Pool(4) as pool:
        for n, dt in pool.imap_unordered(render_one, todo):
            print(f"  {n} {dt:.1f}s", flush=True)
    print("sprites %d, total %.1fs" % (len(todo), time.time() - t0))
