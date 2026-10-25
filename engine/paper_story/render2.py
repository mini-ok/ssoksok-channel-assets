import sys, os, math, time, subprocess, wave
import numpy as np
import skia
V = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, V)
from lay import *
CACHE = V + "/cache/"
OUTMP4 = os.environ.get("OUTMP4", "motion_test_v2.mp4")
SC = 2 / 3
FPS, DUR, VW, VH = 30, 15.0, 1280, 720
SAMP = skia.SamplingOptions(skia.FilterMode.kLinear)

# ---------- 스프라이트 ----------
class Sp:
    def __init__(self, name):
        d = np.load(CACHE + name + ".npz")
        arr = np.ascontiguousarray(d["arr"])
        self.img = skia.Image.fromarray(arr, colorType=skia.kRGBA_8888_ColorType, alphaType=skia.kPremul_AlphaType)
        self.wx, self.wy, self.w, self.h = int(d["wx"]), int(d["wy"]), int(d["w"]), int(d["h"])
        self.cx, self.cy = self.wx + self.w / 2, self.wy + self.h / 2
SP = {}
def sp(name):
    if name not in SP: SP[name] = Sp(name)
    return SP[name]

# ---------- 이징 / 스프링 ----------
def clamp(u): return 0.0 if u < 0 else 1.0 if u > 1 else u
def eo(u): u = clamp(u); return 1 - (1 - u) ** 3
def ei(u): u = clamp(u); return u ** 3
def eio(u):
    u = clamp(u)
    return 4 * u ** 3 if u < 0.5 else 1 - (-2 * u + 2) ** 3 / 2
OVER = []   # (이름, 값) 오버슈트 기록
def _under(t, w, z):
    if t <= 0: return 0.0
    wd = w * math.sqrt(1 - z * z); e = math.exp(-z * w * t)
    return 1 - e * (math.cos(wd * t) + (z * w / wd) * math.sin(wd * t))
_VM = {}
def _vmax(w, z):
    if (w, z) not in _VM:
        _VM[(w, z)] = max((_under(i * 0.002 + 0.01, w, z) - _under(i * 0.002 - 0.01, w, z)) / 0.02 for i in range(300))
    return _VM[(w, z)]
def pop(t, t0, w=26.0, z=0.6, s0=0.0, k=0.10, tag=None):
    """등장 팝: 스케일 s0->1, 약한 오버슈트 1회(z=0.6 -> 약 9.5%), 속도에 따른 세로 늘임/가로 눌림"""
    tt = t - t0
    if tt <= 0: return 0.0, 0.0
    v = _under(tt, w, z); sc = s0 + (1 - s0) * v
    st = (_under(tt + 0.01, w, z) - _under(tt - 0.01, w, z)) / 0.02 / _vmax(w, z)
    if tag: OVER.append((tag, sc))
    return sc * (1 - 0.6 * k * st), sc * (1 + k * st)
def wob(t, t0, amp, freq=5.0, tau=0.25):
    tt = t - t0
    return amp * math.exp(-tt / tau) * math.sin(2 * math.pi * freq * tt) if tt > 0 else 0.0
def pulse(t, ph=0.0):
    u = ((t - ph) % 0.5) / 0.5
    return math.exp(-u * 6.0)

# ---------- 그리기 ----------
def D(cv, name, dx=0.0, dy=0.0, rot=0.0, sx=1.0, sy=1.0, al=1.0, anchor=None, clip=None, mat=None, pie=None):
    if al <= 0.003 or sx <= 0.002 or sy <= 0.002: return
    s = sp(name)
    ax, ay = anchor if anchor else (s.cx, s.cy)
    cv.save(); cv.scale(SC, SC)
    if clip is not None: cv.clipRect(skia.Rect(*clip))
    if pie is not None: cv.clipPath(pie, skia.ClipOp.kIntersect, True)
    if mat is not None:
        for op in mat:
            if op[0] == "t": cv.translate(op[1], op[2])
            elif op[0] == "r": cv.rotate(op[1])
            elif op[0] == "s": cv.scale(op[1], op[2])
    else:
        cv.translate(ax + dx, ay + dy)
        if rot: cv.rotate(rot)
        if sx != 1 or sy != 1: cv.scale(sx, sy)
        cv.translate(-ax, -ay)
    cv.translate(s.wx, s.wy); cv.scale(1 / SC, 1 / SC)
    p = skia.Paint(AntiAlias=True); p.setAlphaf(min(1.0, al))
    cv.drawImage(s.img, 0, 0, SAMP, p)
    cv.restore()

def at(cv, name, x, y, base, **kw):
    """스프라이트가 base(그릴 때의 중심) 에 그려져 있을 때 (x,y) 로 옮겨 그린다"""
    D(cv, name, dx=x - base[0], dy=y - base[1], anchor=base, **kw)

def xform_pt(p, dx, dy, rot, sx, sy, anchor):
    a = math.radians(rot); vx, vy = (p[0] - anchor[0]) * sx, (p[1] - anchor[1]) * sy
    return (anchor[0] + dx + vx * math.cos(a) - vy * math.sin(a), anchor[1] + dy + vx * math.sin(a) + vy * math.cos(a))

# ---------- 타임라인 상수 ----------
CHIP_T = [0.5, 1.0, 1.5, 2.0]; Q_T = 2.5; SMALL_T = 0.2
ZCYC = 2.0; ZOFF = [0.15, 0.40, 0.65]
SLATE_IN0, SLATE_IN1, SLATE_CLAP, SLATE_OUT0, SLATE_OUT1 = 3.55, 4.25, 4.40, 4.70, 5.45
ACT_T, ACT_OUT = 4.42, 5.75
WALK0, WALK1 = 4.15, 6.15
TOSS0, TOSS1 = 6.20, 6.58
RING1 = 6.58; STAR_T = 6.70; PILL_T = 7.00
TICKS = [7.0, 7.5, 8.0, 8.5]; RING2 = 8.75
SHEET0 = 9.25
TITLE1, TITLE2, HL0 = 9.80, 10.00, 10.28
LAND = [11.0, 11.5, 12.0]; FALL_T = 0.34
BRAINC_T = 10.35
STR0, STR1, STR2 = 13.62, 13.95, 14.35; DONE_T = 13.72

# ---------- 공통 요소 ----------
CELLS_A = [(590, 175, .75, 1, 0.0), (1300, 300, .7, 2, 0.2), (80, 170, .5, 0, 0.1)]
CELLS_B = [(615, 190, .7, 1, 0.0), (1280, 240, .6, 2, 0.2), (1840, 215, .6, 3, 0.1), (110, 80, .5, 0, 0.3)]
CELLS_C = [(330, 175, .6, 0, 0.0), (1590, 170, .7, 3, 0.2), (1860, 420, .7, 1, 0.1), (75, 480, .65, 2, 0.3)]
def cells(cv, t, lst, t_in, clip=None):
    for i, (x, y, s, k, ph) in enumerate(lst):
        t0 = t_in + 0.05 * i
        if t < t0: continue
        sx, sy = pop(t, t0, 22, 0.6)
        p = 1 + 0.07 * pulse(t, ph)
        dy = 6 * math.sin(2 * math.pi * (0.33 * t + ph * 3))
        at(cv, f"cell{k}", x, y + dy, (900, 500), sx=s * p * sx, sy=s * p * sy, rot=6 * math.sin(2 * math.pi * 0.2 * t + i), clip=clip)

def win_clouds(cv, t, win, clip):
    L, T, R, B = win; Wd = R - L
    for i, (bx, by) in enumerate(((880, 230), (1040, 180), (960, 310))):
        px = L - 160 + ((i * 190 + 24 * t) % (Wd + 320)); py = T + (by - 100) * 0.95
        at(cv, f"wc{i}", px, py + 4 * math.sin(2 * math.pi * 0.4 * t + i), (bx, by), clip=clip)

HAND_C = (CLK_B[0], CLK_B[1])
def clock_hands(cv, t, ctr, scale, mdeg, hdeg, sec=None, clip=None):
    dx, dy = ctr[0] - HAND_C[0], ctr[1] - HAND_C[1]
    kw = dict(dx=dx, dy=dy, anchor=HAND_C, sx=scale, sy=scale, clip=clip)
    D(cv, "hand_hr", rot=hdeg, **kw); D(cv, "hand_min", rot=mdeg, **kw)
    if sec is not None: D(cv, "hand_sec", rot=sec, **kw)
    D(cv, "clk_cap", **kw)

def burst(cv, t, t0, cx, cy, n=8, R=160, dur=0.55, sc=1.0):
    u = (t - t0) / dur
    if u <= 0 or u >= 1: return
    names = ("spk", "spk2", "spk3")
    for i in range(n):
        ang = 2 * math.pi * i / n + 0.35
        d = R * eo(u) * (0.8 + 0.25 * ((i * 7) % 3) / 2)
        s = sc * (1 - u) * (1.0 if i % 2 == 0 else 0.8)
        at(cv, names[i % 3], cx + math.cos(ang) * d, cy + math.sin(ang) * d, (960, 540), sx=s, sy=s, rot=u * 120 * (1 if i % 2 else -1))

# ---------- 뇌 팀장 (책상) ----------
PIV = (BRAIN[0], DESK_TOP)
WAKE = RING1
def brain_state(t):
    if t < WAKE:
        u = t % 1.0
        d = eio(u / 0.55) if u < 0.55 else (1 - eio((u - 0.55) / 0.15) if u < 0.70 else 0.0)
        return "brain_sleepy", 7.5 * d, 10 * d, 1 + 0.025 * d, 1 - 0.04 * d
    tt = t - WAKE
    e = math.exp(-tt / 0.10) * math.cos(2 * math.pi * tt / 0.30)
    w = 2.0 * math.sin(2 * math.pi * 0.5 * tt) * clamp(tt / 0.5)
    return "brain_happy", w, 0.0, 1 - 0.07 * e + 0.012 * math.sin(2 * math.pi * 1.0 * tt), 1 + 0.12 * e + 0.015 * math.sin(2 * math.pi * 1.0 * tt + 1)

def draw_brain(cv, t, clip=None):
    n, rot, dy, sx, sy = brain_state(t)
    D(cv, n, dx=0, dy=dy, rot=rot, sx=sx, sy=sy, anchor=PIV, clip=clip)

# ---------- 장면 A ----------
def chip_layout():
    import paper
    tw = paper.tw
    x0 = 150; gap = 22
    row1 = [("a_c0", "낮잠,", "black", 150), ("a_c1", "몇 분이", "jua", 140)]
    row2 = [("a_c2", "딱", "do", 215), ("a_c3", "좋을까", "black", 150)]
    L = {}
    x = x0
    for n, s, f, sz in row1:
        w = tw(s, sz, f) + 68; L[n] = (x + w / 2, 516); x += w + gap
    x = x0
    for n, s, f, sz in row2:
        w = tw(s, sz, f) + 68; L[n] = (x + w / 2, 742 if n == "a_c2" else 738); x += w + gap
    L["a_q"] = (x + 88 + 4, 738)
    L["a_small"] = (x0 + tw("1분 몸속 이야기", 46, "jua") / 2, 394)
    return L
CL = None

def scene_A(cv, t):
    global CL
    if CL is None: CL = chip_layout()
    cells(cv, t, CELLS_A, 0.0)
    win_clouds(cv, t, WIN_A, WIN_A)
    D(cv, "winA")
    sec = (math.floor(t * 2) * 12 + 12 * eo((t * 2 % 1) / 0.25)) % 360 if False else (math.floor(t * 2) * 12 + 12 * eo(((t * 2) % 1) / 0.3)) % 360
    clock_hands(cv, t, CLK_A[:2], CLK_A[2] / CLK_B[2], 0.0, 60.0, sec=sec)
    draw_brain(cv, t)
    # Zzz (2초 주기로 차례로 튀어 오름)
    zpos = [(1590, 440), (1672, 352), (1735, 280)]
    for i in range(3):
        c = int(max(0, (t - ZOFF[i])) // ZCYC); t0 = ZOFF[i] + c * ZCYC
        if t < ZOFF[i]: continue
        age = t - t0
        al = 1.0 if age < 1.7 else clamp(1 - (age - 1.7) / 0.2)
        sx, sy = pop(t, t0, 26, 0.6, tag="zzz")
        x, y = zpos[i]; rise = -14 * eo(age / 1.7)
        at(cv, f"a_z{i}", x + 6 * math.sin(2 * math.pi * 0.7 * age), y + rise, (960, 540), sx=sx, sy=sy, rot=(-10 + 8 * i) + 6 * math.sin(2 * math.pi * 0.8 * age + i), al=al)
    D(cv, "desk")
    # 칩
    def chip_pop(name, t0, rot0):
        sx, sy = pop(t, t0, 26, 0.6, tag="chip")
        x, y = CL[name]
        v = 1 - clamp((t - t0) / 0.3)
        at(cv, name, x, y, (960, 540), sx=sx, sy=sy, rot=rot0 * v)
    at_t = SMALL_T
    if t >= at_t:
        sx, sy = pop(t, at_t, 22, 0.6); x, y = CL["a_small"]; at(cv, "a_small", x, y + 8 * (1 - clamp((t - at_t) / 0.3)), (960, 540), sx=sx, sy=sy)
    for n, t0, r0 in (("a_c0", CHIP_T[0], 9), ("a_c1", CHIP_T[1], -9), ("a_c2", CHIP_T[2], 9), ("a_c3", CHIP_T[3], -9)):
        if t >= t0: chip_pop(n, t0, r0)
    if t >= Q_T:
        x, y = CL["a_q"]
        tt = t - Q_T; T = 0.42
        sx, sy = pop(t, Q_T, 26, 0.6, tag="q")
        if tt < T:
            u = tt / T; jump = -80 * (1 - (2 * u - 1) ** 2); st = 1 + 0.10 * (1 - u) if u < 0.2 else 1.0
            ssx, ssy = 1.0, st
        else:
            q = math.exp(-(tt - T) / 0.07) * math.cos(2 * math.pi * (tt - T) / 0.24); jump = 0; ssx, ssy = 1 + 0.12 * q, 1 - 0.16 * q
        rot = wob(t, Q_T + T, 16, 4.5, 0.45) + 3 * math.sin(2 * math.pi * 1.0 * (t - Q_T)) * clamp((tt - 1.0) / 0.5)
        mat = [("t", x, y + 88 + jump), ("s", sx * ssx, sy * ssy), ("t", -960, -(540 + 88))]
        # 아래 중심 기준 스케일 + 회전은 중심에서
        mat = [("t", x, y + 88 + jump), ("s", sx * ssx, sy * ssy), ("t", 0, -88), ("r", rot), ("t", -960, -540)]
        D(cv, "a_q", mat=mat)

# ---------- 슬레이트 ----------
def slate_c(t):
    if t < SLATE_IN0: return -600.0
    if t < SLATE_IN1: return -600 + 1400 * eo((t - SLATE_IN0) / (SLATE_IN1 - SLATE_IN0))
    if t < SLATE_OUT0: return 800 + 20 * (t - SLATE_IN1) / (SLATE_OUT0 - SLATE_IN1)
    return 820 + 1800 * eio((t - SLATE_OUT0) / (SLATE_OUT1 - SLATE_OUT0)) ** 1.0 * 1.0
def scene_slate(cv, t):
    if t < SLATE_IN0 or t > SLATE_OUT1 + 0.05: return
    c = slate_c(t); dx = c - 960
    bob = 6 * math.sin(2 * math.pi * 2.0 * t) * (1 - clamp((t - SLATE_IN1) / 0.2)) if t < SLATE_IN1 + 0.2 else 0.0
    # 박수(탁)
    if t < SLATE_CLAP: ang = -27.0 + 2 * math.sin(2 * math.pi * 3 * t) * 0
    else:
        tt = t - SLATE_CLAP
        ang = -27.0 * (1 - ei(tt / 0.06)) if tt < 0.06 else 3.0 * math.exp(-(tt - 0.06) / 0.08) * math.sin(2 * math.pi * (tt - 0.06) / 0.2)
    sq = 0.0
    if t >= SLATE_CLAP:
        tt = t - SLATE_CLAP; sq = math.exp(-tt / 0.08) * math.cos(2 * math.pi * tt / 0.28)
    sy = 1 - 0.05 * sq; sx = 1 + 0.025 * sq
    rot = 4.0 * (1 - eo((t - SLATE_IN0) / 0.5)) if t < SLATE_IN0 + 0.5 else 0.0
    mat = [("t", c, 990 + bob), ("s", sx, sy), ("r", rot), ("t", -960, -990)]
    D(cv, "slate_board", mat=mat)
    mat_b = [("t", c, 990 + bob), ("s", sx, sy), ("r", rot), ("t", 0, 0), ("t", -960 + 0, -990)]
    # 경첩(470,400)을 기준으로 막대 회전
    hinge = (470, 402)
    mat_b = [("t", c, 990 + bob), ("s", sx, sy), ("r", rot), ("t", -960 + hinge[0], -990 + hinge[1]), ("r", ang), ("t", -hinge[0], -hinge[1])]
    D(cv, "slate_bar", mat=mat_b)

def scene_action(cv, t):
    if t < ACT_T or t > ACT_OUT + 0.25: return
    sx, sy = pop(t, ACT_T, 20, 0.57, tag="action")
    out = 1 - ei((t - ACT_OUT) / 0.22) if t > ACT_OUT else 1.0
    rot = wob(t, ACT_T, 10, 4, 0.3)
    at(cv, "a_action", 960, 215, (960, 540), sx=sx * out, sy=sy * out, rot=rot + 1.5 * math.sin(2 * math.pi * 1.0 * t))
    burst(cv, t, ACT_T + 0.02, 960, 215, n=8, R=330, dur=0.6)

# ---------- 장면 B ----------
MEL_X0, MEL_X1 = -215.0, 960.0
def walk_x(t):
    T = WALK1 - WALK0; v0 = (MEL_X1 - MEL_X0) / (0.85 * T)
    u = clamp((t - WALK0) / T)
    if u <= 0.7: return MEL_X0 + v0 * u * T, v0
    r = u - 0.7
    return MEL_X0 + v0 * 0.7 * T + v0 * T * (r - r * r / 0.6), v0 * (1 - r / 0.3)

HAND_LOCAL = (1135, 704)       # 알람 시계 중심(멜라토닌 오른손 위, x=960 기준)
BRAIN_HAND = (1252, 692)
def mel_state(t):
    """멜라토닌 몸 상태: 걷기(통통 점프+좌우 기울기+발 교차) / 도착 후 숨쉬기"""
    Th = (WALK1 - WALK0) / 7.0
    x, v = walk_x(t)
    st = dict(x=x, dy=0.0, rot=0.0, sx=1.0, sy=1.0, shadow=1.0, fl=0.0, fr=0.0, fxl=0.0, fxr=0.0)
    if t < WALK1:
        ph = math.pi * (t - WALK0) / Th
        amp = 1.0
        s = abs(math.sin(ph)); sg = math.sin(ph)
        st["dy"] = -30 * amp * s
        st["rot"] = -6.5 * sg
        near = 1 - clamp(s / 0.3)
        st["sy"] = 1 - 0.08 * near; st["sx"] = 1 + 0.06 * near
        st["shadow"] = 1 - 0.2 * s
        F = 0.9 * v * Th / math.pi
        st["fxl"] = F * math.cos(ph); st["fxr"] = -F * math.cos(ph)
        st["fl"] = 24 * max(0.0, -sg); st["fr"] = 24 * max(0.0, sg)
    else:
        tt = t - WALK1
        q = math.exp(-tt / 0.08) * math.cos(2 * math.pi * tt / 0.26)
        st["sy"] = 1 - 0.08 * q + 0.012 * math.sin(2 * math.pi * 1.0 * tt); st["sx"] = 1 + 0.06 * q
        st["rot"] = 1.8 * math.sin(2 * math.pi * 0.5 * tt)
        if t > TOSS0:
            k = math.sin(math.pi * clamp((t - TOSS0) / (TOSS1 - TOSS0)))
            st["rot"] += 6 * k; st["dy"] -= 10 * k
    return st

MEL_ANCH_Y = MEL_FOOT_Y
def draw_mel(cv, t, clip):
    st = mel_state(t)
    if t < WALK0 - 0.05: return
    dx = st["x"] - 960
    # 그림자
    D(cv, "sh_mel", dx=dx, sx=st["shadow"], sy=st["shadow"], al=0.9 * st["shadow"] ** 2, clip=clip)
    for nm, fx, fl in (("L", st["fxl"], st["fl"]), ("R", st["fxr"], st["fr"])):
        D(cv, f"mel_foot{nm}", dx=dx + fx, dy=-fl, clip=clip)
    anchor = (960, MEL_ANCH_Y)
    D(cv, "mel_body", dx=dx, dy=st["dy"], rot=st["rot"], sx=st["sx"], sy=st["sy"], anchor=anchor, clip=clip)
    return dict(dx=dx, dy=st["dy"], rot=st["rot"], sx=st["sx"], sy=st["sy"], anchor=anchor)

def alarm_pose(t, mel):
    """(x, y, rot, sc, visible)"""
    if t < WALK0 - 0.05: return None
    if t < TOSS0:
        p = xform_pt(HAND_LOCAL, mel["dx"], mel["dy"], mel["rot"], mel["sx"], mel["sy"], mel["anchor"])
        return p[0], p[1], mel["rot"], 1.0
    if t < TOSS1:
        u = (t - TOSS0) / (TOSS1 - TOSS0)
        p0 = xform_pt(HAND_LOCAL, mel["dx"], mel["dy"], mel["rot"], mel["sx"], mel["sy"], mel["anchor"])
        e = eio(u)
        x = p0[0] + (BRAIN_HAND[0] - p0[0]) * e; y = p0[1] + (BRAIN_HAND[1] - p0[1]) * e - 95 * math.sin(math.pi * u)
        return x, y, -25 * math.sin(math.pi * u) + 12 * u, 1.0 + 0.12 * math.sin(math.pi * u)
    return BRAIN_HAND[0], BRAIN_HAND[1], 0.0, 1.0

def ring_env(t):
    e = 0.0
    for r0 in (RING1, RING2):
        if t > r0: e = max(e, math.exp(-(t - r0) / 0.45))
    return e

MIN_ANG = lambda t: 30.0 * sum(eo((t - tk) / 0.28) for tk in TICKS)
def scene_B(cv, t, clip):
    cells(cv, t, CELLS_B, 4.3 if clip is not None else 0.0, clip)
    win_clouds(cv, t, WIN_B, (WIN_B[0], WIN_B[1], WIN_B[2], WIN_B[3]) if clip is None else (WIN_B[0], WIN_B[1], min(WIN_B[2], clip[2]), WIN_B[3]))
    D(cv, "winB", clip=clip)
    mdeg = MIN_ANG(t); hdeg = 60.0 + mdeg / 12.0
    # 부채꼴
    if mdeg > 0.5:
        cx, cy = CLK_B[0], CLK_B[1]; R = 150
        p = skia.Path(); p.moveTo(cx * SC, cy * SC)
        rect = skia.Rect((cx - R * 1.3) * SC, (cy - R * 1.3) * SC, (cx + R * 1.3) * SC, (cy + R * 1.3) * SC)
        p2 = skia.Path(); p2.moveTo(cx, cy); p2.arcTo(skia.Rect(cx - 400, cy - 400, cx + 400, cy + 400), -90, mdeg + 0.5, False); p2.close()
        done = t - (TICKS[-1] + 0.28)
        k = 1 + (0.05 * math.exp(-done / 0.12) * math.cos(2 * math.pi * done / 0.3) if done > 0 else 0.0)
        D(cv, "wedge", pie=p2, anchor=(cx, cy), sx=k, sy=k, al=0.9, clip=clip)
    sec = (math.floor(t * 2) * 12 + 12 * eo(((t * 2) % 1) / 0.3)) % 360 if t < TICKS[0] else None
    clock_hands(cv, t, (CLK_B[0], CLK_B[1]), 1.0, mdeg, hdeg, sec=sec, clip=clip)
    burst(cv, t, TICKS[-1] + 0.3, CLK_B[0], CLK_B[1], n=8, R=230, dur=0.6)
    draw_brain(cv, t, clip)
    D(cv, "desk", clip=clip)
    mel = draw_mel(cv, t, clip)
    ap = alarm_pose(t, mel) if mel else None
    if ap:
        x, y, rot, sc = ap
        env = ring_env(t)
        shake = 11 * env * math.sin(2 * math.pi * 13 * t) + 3.0 * pulse(t, 0.0) * math.sin(2 * math.pi * 9 * t) * (1 if t > TOSS1 else 0)
        at(cv, "alarm", x, y, (800, 540), rot=rot + shake, sx=sc, sy=sc, clip=clip)
        if env > 0.18 and int(t * 14) % 2 == 0:
            at(cv, "alarm_fx", x, y, (800, 540), rot=shake * 0.3, al=min(1.0, env * 1.6), clip=clip)
    # 큰 숫자 별
    if t >= STAR_T:
        sx, sy = pop(t, STAR_T, 19, 0.57, tag="star", k=0.10)
        tt = t - STAR_T
        rot = -4.0 + (-24.0 * (1 - eo(tt / 0.4))) + 1.8 * math.sin(2 * math.pi * 0.8 * tt) * clamp(tt / 0.6)
        br = 1 + 0.035 * pulse(t, STAR_T) * clamp(tt / 0.5)
        ring_s = 1 + 0.05 * ring_env(t) * math.sin(2 * math.pi * 11 * t)
        at(cv, "b_star", 960, 296, (960, 296), sx=sx * br * ring_s, sy=sy * br * ring_s, rot=rot, clip=clip)
        burst(cv, t, STAR_T + 0.05, 960, 296, n=10, R=330, dur=0.65)
    if t >= PILL_T:
        sx, sy = pop(t, PILL_T, 24, 0.6, tag="pill")
        v = 1 - clamp((t - PILL_T) / 0.3)
        at(cv, "b_pill", 470, 600, (470, 600), sx=sx, sy=sy, rot=-1.2 + 4 * v, clip=clip)

# ---------- 장면 C ----------
CARD_TILT = [-2.2, 1.6, -1.2]; CARD_R0 = [-10, 9, -8]
def sheets(cv, t):
    for name, t0 in (("sheet_coral", SHEET0), ("sheet_main", SHEET0 + 0.05)):
        u = (t - t0) / 0.62
        dy = 1260 * (1 - eo(u))
        if u > 0: D(cv, name, dy=dy, anchor=(0, 0))

def scene_C(cv, t):
    sheets(cv, t)
    if t < SHEET0 + 0.45: return
    cells(cv, t, CELLS_C, SHEET0 + 0.5)
    # 형광펜(제목 뒤)
    if t >= HL0:
        h = sp("c_hl"); f = eo((t - HL0) / 0.45)
        D(cv, "c_hl", clip=(0, 0, h.wx + h.w * f + 2, 1080))
    for i, (n, t0) in enumerate((("c_t1", TITLE1), ("c_t2", TITLE2))):
        if t >= t0:
            sx, sy = pop(t, t0, 22, 0.6, tag="title"); s = sp(n)
            D(cv, n, rot=-2.0 * (1 - clamp((t - t0) / 0.3)) * (1 if i == 0 else -1) + (0.6 * math.sin(2 * math.pi * 0.6 * t + i)), sx=sx, sy=sy, anchor=(s.cx, s.wy + s.h * 0.85))
    # 카드
    for k in range(3):
        tl = LAND[k]; sp0 = tl - FALL_T
        if t < sp0: continue
        xk = CARD_X[k]; yb = LEDGE
        if t < tl:
            u = (t - sp0) / FALL_T
            yo = -150 * (1 - u * u); ssx, ssy = 1 - 0.03 * u, 1 + 0.05 * u; r = CARD_R0[k] * (1 - u); al = clamp((t - sp0) / 0.07)
        else:
            tt = t - tl; q = math.exp(-tt / 0.07) * math.cos(2 * math.pi * tt / 0.24)
            yo = 0.0; ssx, ssy = 1 + 0.10 * q, 1 - 0.16 * q
            r = -CARD_R0[k] * 0.3 * math.exp(-tt / 0.10) * math.sin(2 * math.pi * tt / 0.25); al = 1.0
            OVER.append(("cardstretch", ssy))
        common = [("t", xk, yb + yo), ("s", ssx, ssy), ("t", -xk, -yb)]
        D(cv, f"c_frame{k}", mat=common + [("t", xk, CARD_Y), ("r", r), ("t", -xk, -CARD_Y)], al=al)
        D(cv, f"c_card{k}", mat=common, al=al)
    # 뇌 팀장
    draw_brain_c(cv, t)

BC_ANCH = (BC[0], BC_FOOT_Y)
def draw_brain_c(cv, t):
    if t < BRAINC_T: return
    sx, sy = pop(t, BRAINC_T, 22, 0.6, tag="brainc")
    D(cv, "sh_bc", sx=0.6 + 0.4 * min(1.0, sx), sy=1.0, al=clamp((t - BRAINC_T) / 0.2))
    for nm in "LR": D(cv, f"bc_foot{nm}", sx=sx, sy=sy, anchor=BC_ANCH)
    name = "bc_body"
    bsx, bsy, rot = 1.0, 1.0, 0.0
    tt = t - BRAINC_T
    if t < STR0:
        # 박자에 맞춰 살짝 몸을 흔드는 아이들(통통 튀는 건 아님)
        bsy = 1 + 0.02 * math.sin(2 * math.pi * 1.0 * tt) + 0.03 * pulse(t, BRAINC_T); bsx = 1 - 0.015 * pulse(t, BRAINC_T)
        rot = 2.5 * math.sin(2 * math.pi * 0.5 * tt) * clamp(tt / 0.4)
    elif t < STR2 + 0.35:
        name = "bc_up"
        if t < STR1: e = eo((t - STR0) / (STR1 - STR0)); bsy = 1 + 0.30 * e
        elif t < 14.10: bsy = 1.30; rot = 1.8 * math.sin(2 * math.pi * 9 * (t - STR1))
        else:
            u = (t - 14.10) / (STR2 - 14.10)
            bsy = 1 + 0.30 * (1 - eio(u)) - 0.04 * math.sin(math.pi * clamp(u)) * (1 if u > 0.5 else 0) if u < 1.0 else 1 + 0.045 * math.exp(-(t - STR2) / 0.12) * math.cos(2 * math.pi * (t - STR2) / 0.28) * -1
        bsx = 1 / (bsy ** 0.55)
        OVER.append(("stretch", bsy))
        if t >= STR2 + 0.35: name = "bc_body"
    else:
        tt2 = t - (STR2 + 0.35)
        bsy = 1 + 0.018 * math.sin(2 * math.pi * 1.0 * tt2); bsx = 1 - 0.01 * math.sin(2 * math.pi * 1.0 * tt2)
        rot = 1.2 * math.sin(2 * math.pi * 0.5 * tt2)
    D(cv, name, sx=sx * bsx, sy=sy * bsy, rot=rot, anchor=BC_ANCH)
    if t >= DONE_T:
        cx, cy = 1575, 362
        sx2, sy2 = pop(t, DONE_T, 20, 0.57, tag="done")
        at(cv, "c_done", cx, cy, (960, 540), sx=sx2, sy=sy2, rot=wob(t, DONE_T, 9, 4, 0.3) + 1.2 * math.sin(2 * math.pi * 1.0 * t))
        burst(cv, t, DONE_T + 0.02, cx, cy, n=8, R=210, dur=0.6, sc=0.9)

# ---------- 오디오 ----------
SR = 44100
def synth_audio(path):
    n = int(SR * DUR); y = np.zeros(n, np.float32)
    rng = np.random.default_rng(5)
    def add(t0, sig, g=1.0):
        i = int(t0 * SR); j = min(n, i + len(sig))
        if 0 <= i < n: y[i:j] += g * sig[: j - i]
    def tt(l): return np.arange(int(SR * l)) / SR
    def tok(f0, f1, decay, length, amp, noise=0.0):
        x = tt(length); f = f1 + (f0 - f1) * np.exp(-x / 0.03)
        ph = 2 * np.pi * np.cumsum(f) / SR
        env = np.exp(-x / decay) * (1 - np.exp(-x / 0.0015))
        s = (np.sin(ph) + 0.25 * np.sin(2 * ph)) * env
        if noise:
            r = rng.normal(0, 1, len(x)); r = np.convolve(r, np.ones(24) / 24, "same"); s = s + noise * r * np.exp(-x / 0.006)
        return (amp * s).astype(np.float32)
    def bubble(f0, f1, length=0.16, amp=0.3):   # 뽁: 올라가는 짧은 소리
        x = tt(length); f = f0 + (f1 - f0) * (x / length) ** 0.6
        ph = 2 * np.pi * np.cumsum(f) / SR
        env = np.sin(np.pi * np.clip(x / length, 0, 1)) ** 0.7 * np.exp(-x / 0.08)
        return (amp * np.sin(ph) * env).astype(np.float32)
    def clap(amp=0.7):   # 탁
        x = tt(0.22); r = rng.normal(0, 1, len(x)); r = r - np.convolve(r, np.ones(40) / 40, "same")
        s = r * np.exp(-x / 0.012) * 0.8 + np.sin(2 * np.pi * 150 * x) * np.exp(-x / 0.05) * 0.8
        return (amp * s).astype(np.float32)
    def ding(amp=0.35):  # 띠링
        out = np.zeros(int(SR * 0.5), np.float32)
        for k, (st, f) in enumerate(((0.0, 1568), (0.11, 2093))):
            x = tt(0.38); s = (np.sin(2 * np.pi * f * x) + 0.4 * np.sin(2 * np.pi * f * 2.76 * x)) * np.exp(-x / 0.12) * (1 - np.exp(-x / 0.002))
            i = int(st * SR); out[i:i + len(s)] += (amp * s[: len(out) - i]).astype(np.float32)
        return out
    def whoosh(length, amp=0.18):
        x = tt(length); r = rng.normal(0, 1, len(x)); k = 60
        r = np.convolve(r, np.ones(k) / k, "same"); env = np.sin(np.pi * x / length) ** 2
        return (amp * r * env * 6).astype(np.float32)
    def rise(length, amp=0.14):
        x = tt(length); f = 300 + 900 * (x / length) ** 1.5
        ph = 2 * np.pi * np.cumsum(f) / SR
        return (amp * np.sin(ph) * np.sin(np.pi * x / length) ** 0.8).astype(np.float32)
    ev = []
    def E(name, t0): ev.append((name, round(t0, 3)))
    for tc in CHIP_T: add(tc + 0.04, tok(780, 430, 0.05, 0.22, 0.34)); E("chip", tc + 0.04)
    add(SMALL_T + 0.03, tok(900, 520, 0.04, 0.18, 0.2)); E("small", SMALL_T)
    for c in range(3):
        for i in range(3):
            t0 = ZOFF[i] + c * ZCYC
            if t0 < SLATE_OUT0: add(t0 + 0.02, bubble(520 + 90 * i, 900 + 100 * i, 0.14, 0.16)); E("zzz", t0)
    add(Q_T + 0.04, bubble(500, 1000, 0.18, 0.3)); E("q-pop", Q_T)
    add(Q_T + 0.42 + 0.02, tok(520, 300, 0.07, 0.2, 0.3)); E("q-land", Q_T + 0.44)
    add(SLATE_IN0 + 0.1, whoosh(0.5, 0.12)); E("slate-in", SLATE_IN0)
    add(SLATE_CLAP, clap(0.75)); E("clap", SLATE_CLAP)
    add(ACT_T + 0.02, bubble(380, 780, 0.2, 0.36)); E("action", ACT_T)
    add(SLATE_OUT0, whoosh(0.8, 0.2)); E("slate-out", SLATE_OUT0)
    Th = (WALK1 - WALK0) / 7.0
    for i in range(1, 8):
        add(WALK0 + i * Th, tok(300, 180, 0.04, 0.12, 0.13)); E("step", WALK0 + i * Th)
    add(TOSS0, whoosh(0.35, 0.09)); E("toss", TOSS0)
    add(RING1, ding(0.34)); E("ding1", RING1)
    add(STAR_T + 0.02, bubble(300, 760, 0.24, 0.42)); E("star-pop", STAR_T)
    add(PILL_T + 0.03, tok(700, 420, 0.05, 0.2, 0.3)); E("pill", PILL_T)
    for tk in TICKS: add(tk + 0.02, tok(1500, 900, 0.015, 0.06, 0.16)); E("tick", tk)
    add(RING2, ding(0.34)); E("ding2", RING2)
    add(SHEET0 - 0.05, whoosh(0.8, 0.16)); E("sheet", SHEET0)
    add(TITLE1 + 0.02, bubble(420, 860, 0.18, 0.34)); E("title1", TITLE1)
    add(TITLE2 + 0.02, bubble(480, 960, 0.18, 0.34)); E("title2", TITLE2)
    add(HL0, whoosh(0.4, 0.07)); E("hl", HL0)
    add(BRAINC_T + 0.02, bubble(360, 740, 0.2, 0.34)); E("brainc", BRAINC_T)
    for tl in LAND:
        add(tl, tok(210, 115, 0.075, 0.30, 0.5, 0.25)); E("card", tl)
    add(STR0, rise(0.35, 0.16)); E("stretch", STR0)
    add(DONE_T + 0.02, bubble(420, 900, 0.2, 0.38)); E("done", DONE_T)
    add(14.35, tok(420, 260, 0.06, 0.18, 0.2)); E("settle", 14.35)
    y = (0.8 * np.tanh(y * 0.8)).astype(np.float32)
    with wave.open(path, "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes((y * 32767).astype(np.int16).tobytes())
    return ev

# ---------- 합성 ----------
def load_bg(name):
    b = np.load(CACHE + name + ".npy")
    return skia.Image.fromarray(np.dstack([b, np.full(b.shape[:2], 255, np.uint8)]), colorType=skia.kRGBA_8888_ColorType, alphaType=skia.kPremul_AlphaType)
BGS = {}
def frame(cv, t):
    if not BGS: BGS["A"] = load_bg("bgA"); BGS["B"] = load_bg("bgB")
    # 장면 A (슬레이트가 완전히 지나갈 때까지)
    c = slate_c(t)
    if t < SLATE_OUT1 + 0.02:
        cv.drawImage(BGS["A"], 0, 0)
        scene_A(cv, t)
    if t >= SLATE_IN0:
        # B: 슬레이트 중심선 왼쪽만 드러남
        cv.save(); cv.clipRect(skia.Rect(0, 0, max(0.0, c) * SC, VH))
        cv.drawImage(BGS["B"], 0, 0)
        scene_B(cv, t, (0, 0, max(0.0, c), 1080))
        cv.restore()
    if t >= SLATE_OUT1 + 0.02 and t < SHEET0 + 1.0:
        pass
    scene_slate(cv, t)
    scene_action(cv, t)
    if t >= SLATE_OUT1 + 0.02:
        pass
    if t >= SHEET0 - 0.02:
        scene_C(cv, t)

def frame_full(cv, t):
    if t >= SLATE_OUT1 + 0.02:
        if not BGS: BGS["A"] = load_bg("bgA"); BGS["B"] = load_bg("bgB")
        cv.drawImage(BGS["B"], 0, 0)
        if t < SHEET0 + 1.1: scene_B(cv, t, None)
        scene_action(cv, t)
        if t >= SHEET0 - 0.02: scene_C(cv, t)
    else:
        frame(cv, t)

def main():
    args = sys.argv[1:]
    surf = skia.Surface(VW, VH); cv = surf.getCanvas()
    def snap(i):
        t = i / FPS; cv.clear(skia.ColorBLACK); frame_full(cv, t)
        return surf.makeImageSnapshot().toarray(colorType=skia.kRGBA_8888_ColorType, alphaType=skia.kUnpremul_AlphaType)
    if args:
        from PIL import Image
        os.makedirs(V + "/prev", exist_ok=True)
        for a in args:
            i = int(round(float(a) * FPS)) if "." in a else int(a)
            Image.fromarray(snap(i)[..., :3]).save(V + f"/prev/f{i:03d}.png")
        return
    ev = synth_audio(V + "/sfx.wav")
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{VW}x{VH}", "-r", str(FPS), "-i", "-",
           "-i", V + "/sfx.wav", "-map", "0:v", "-map", "1:a", "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-pix_fmt", "yuv420p",
           "-c:a", "aac", "-b:a", "128k", "-t", str(DUR), "-movflags", "+faststart", OUTMP4]
    os.makedirs(os.path.dirname(OUTMP4), exist_ok=True)
    pr = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    t0 = time.time()
    for i in range(int(round(FPS * DUR))):
        pr.stdin.write(np.ascontiguousarray(snap(i)[..., :3]).tobytes())
    pr.stdin.close(); pr.wait()
    print("프레임 렌더+인코딩 %.1fs" % (time.time() - t0))
    ov = {}
    for tag, v in OVER: ov[tag] = max(ov.get(tag, 0), v)
    print("최대 스케일/늘임:", {k: round(v, 3) for k, v in ov.items()})
    print("효과음", len(ev), "개")

if __name__ == "__main__":
    main()
