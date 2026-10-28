"""장면 합성 렌더러: 스프라이트(그림자 포함 RGBA) 캐시 → 프레임마다 위치·크기·회전·투명도만 바꿔 합성 → ffmpeg 파이프
사용: python3 -I render.py <variant> <out_dir> [preview t1 t2 ...]  variant: ko_long en_long ko_A ko_B en_A en_B"""
import sys, os, json, math, wave, subprocess, zlib
sys.path.insert(0, "/home/claude/work/sit")
from core import *
from core import _resize
import props as PR
import bgs
import eps
import skia

VARIANT = sys.argv[1] if len(sys.argv) > 1 else "ko_long"
LANG, KIND = VARIANT.split("_")[0], ("long" if VARIANT.endswith("long") else "short")
SHORT = KIND == "short"
DW, DH = (1080, 1920) if SHORT else (1920, 1080)
RW, RH = (int(DW * K), int(DH * K))
FPS = 30
EPDIR = "/home/claude/work/ep/" + VARIANT
SAMP = skia.SamplingOptions(skia.FilterMode.kLinear)
NAME = dict(ko=dict(brain="뇌 팀장", stomach="위 대리", liver="간 과장", melatonin="멜라토닌", immune="면역 경비", gut="장 연구원"),
            en=dict(brain="Brain", stomach="Stomach", liver="Liver", melatonin="Melatonin", immune="Immune", gut="Gut"))
SIDNAME = {5: "brain", 10: "stomach", 3: "liver", 7: "melatonin", 6: "immune", 2: "gut", 1: "heart", 4: "muscle", 9: "caffeine", 8: "adenosine"}
COLS = dict(coral=CORALC, mint=MINTC, sky=SKYC, butter=BUTTER, lav=LAV, yellow=YEL, cream=CREAMC, lime=LIME, ice=ICE, coral_l=CORAL_L)
FACE_EN = dict(black="geist", jua="geist", do="geist")
FLOOR_Y = 806 if not SHORT else 1255
LOC_FLOOR = dict(office_night=806, office_day=806, meeting=808, gate=812, factory=812, night=810, iv=806, end=800, end_thanks=800, endcard=1010, s_a=1255, s_b=1255)

# ───────── 스프링/이징 ─────────
def clamp01(u): return 0.0 if u < 0 else 1.0 if u > 1 else u
def eo(u): u = clamp01(u); return 1 - (1 - u) ** 3
def eio(u):
    u = clamp01(u); return 4 * u ** 3 if u < 0.5 else 1 - (-2 * u + 2) ** 3 / 2
def _under(t, w, z):
    if t <= 0: return 0.0
    wd = w * math.sqrt(1 - z * z); e = math.exp(-z * w * t)
    return 1 - e * (math.cos(wd * t) + (z * w / wd) * math.sin(wd * t))
def pop(t, t0, w=26.0, z=0.6, k=0.10):
    """등장 팝: 0→1 오버슈트 1회 + 속도에 따른 세로 늘임/가로 눌림. (sx, sy)"""
    tt = t - t0
    if tt <= 0: return 0.0, 0.0
    v = _under(tt, w, z)
    st = (_under(tt + 0.01, w, z) - _under(tt - 0.01, w, z)) / 0.02 / 6.0
    st = max(-1.0, min(1.0, st))
    return max(0.0, v * (1 - 0.6 * k * st)), max(0.0, v * (1 + k * st))

# ───────── 스프라이트 그리기 ─────────
def _img(sp):
    if "img" not in sp:
        a = np.ascontiguousarray(sp["arr"])
        sp["img"] = skia.Image.fromarray(a, colorType=skia.kRGBA_8888_ColorType, alphaType=skia.kPremul_AlphaType)
    return sp["img"]

def blit(cv, sp, x, y, sc=1.0, rot=0.0, sx=1.0, sy=1.0, al=1.0, anchor=None):
    if sp is None or al <= 0.003 or sx <= 0.002 or sy <= 0.002 or sc <= 0.002: return
    ax, ay = anchor if anchor else (sp["cw"] / 2, sp["ch"] / 2)
    cv.save()
    cv.translate(x, y)
    if rot: cv.rotate(rot)
    cv.scale(sc * sx, sc * sy)
    cv.translate(sp["wx"] - ax, sp["wy"] - ay)
    cv.scale(1 / K, 1 / K)
    p = skia.Paint(AntiAlias=True); p.setAlphaf(min(1.0, al))
    cv.drawImage(_img(sp), 0, 0, SAMP, p)
    cv.restore()

# ───────── 캐릭터 ─────────
CH_N = CHAR_S + 140
CH_ANCHOR = (CH_N / 2, 554)
_CHSP = {}
def chsp(name, mood):
    k = (name, mood)
    if k not in _CHSP: _CHSP[k] = char_sprite(name, mood)
    return _CHSP[k]

# ───────── 타임라인 ─────────
CH_LIST = eps.L if not SHORT else (eps.SA if VARIANT.endswith("A") else eps.SB)
MAN = {m["id"]: m for m in json.load(open(EPDIR + "/audio/manifest.json"))}
TX = (eps.KO if LANG == "ko" else eps.EN) if not SHORT else ((eps.SKO_A if LANG == "ko" else eps.SEN_A) if VARIANT.endswith("A") else (eps.SKO_B if LANG == "ko" else eps.SEN_B))
GAPS = {1: 0.30, 2: 0.18, 3: 0.08, 4: 0.03}
TAILV = 0.35
LEAD = 0.6 if SHORT else 0.5
S_START, S_AUD, S_LEN = [], [], []
_t = LEAD
for i, c in enumerate(CH_LIST):
    S_START.append(_t if i else 0.0)
    S_AUD.append(_t)
    if c["sid"] is None:
        ln = c["dur"]
    else:
        sp_ = MAN[c["id"]]["dur"] - TAILV
        ln = sp_ + GAPS.get(c.get("tempo", 1), 0.2)
        if SHORT: ln = sp_ + 0.22
    if c.get("mindur"): ln = max(ln + TAILV, c["mindur"])
    S_LEN.append(ln)
    _t += ln
END = _t + (0.8 if SHORT else 0.5)
# 장면 구간: [S_START[i], S_START[i+1])
S_BEG = [0.0] + [max(S_AUD[i] - 0.10, S_AUD[i-1] + 0.05) for i in range(1, len(CH_LIST))]

def chunk_at(tm):
    i = 0
    for k, s in enumerate(S_BEG):
        if tm >= s: i = k
    return i

# 음성 포락선
_ENV = {}
def env_of(i, lt_audio):
    c = CH_LIST[i]
    if c["sid"] is None or lt_audio < 0: return 0.0
    if i not in _ENV:
        if not os.path.exists(f"{EPDIR}/audio/{c['id']}.wav"):
            _ENV[i] = np.zeros(1)
            return 0.0
        w = wave.open(f"{EPDIR}/audio/{c['id']}.wav"); sr = w.getframerate()
        x = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float32) / 32768; w.close()
        hop = sr // FPS; n = len(x) // hop
        e = np.sqrt((x[:n * hop].reshape(n, hop) ** 2).mean(1)) if n else np.zeros(1)
        e = e / (np.percentile(e, 92) + 1e-6); e = np.clip(e, 0, 1)
        e = np.convolve(e, np.ones(3) / 3, mode="same"); _ENV[i] = e
    e = _ENV[i]; k = int(lt_audio * FPS)
    return float(e[k]) if 0 <= k < len(e) else 0.0

# ───────── 배경 ─────────
_BG = {}
def bgimg(name):
    if name not in _BG:
        a = np.load(CACHE + f"bg_{name}.npy")
        if name == "iv":
            pass
        rgba = np.concatenate([a, np.full(a.shape[:2] + (1,), 255, np.uint8)], 2)
        _BG[name] = skia.Image.fromarray(np.ascontiguousarray(rgba), colorType=skia.kRGBA_8888_ColorType, alphaType=skia.kOpaque_AlphaType)
    return _BG[name]

def make_iv_bg():
    from scipy import ndimage as ndi
    p = CACHE + "bg_iv.npy"
    if not os.path.exists(p):
        a = np.load(CACHE + "bg_office_night.npy").astype(np.float32) / 255
        a = np.stack([ndi.gaussian_filter(a[..., i], 11) for i in range(3)], 2) * 0.93 + 0.05
        np.save(p, (np.clip(a, 0, 1) * 255).astype(np.uint8))
make_iv_bg()

def bg_name(loc):
    if loc in ("office_night", "office_day", "iv"): return loc
    if loc == "end_thanks": return "end"
    if loc == "endcard": return "end"
    if loc == "night": return "night_ko"
    if loc in ("meeting", "gate", "factory"): return f"{loc}_{LANG}"
    return loc

def draw_bg(cv, loc):
    img = bgimg(bg_name(loc))
    cv.save(); cv.scale(1 / K, 1 / K)
    cv.drawImage(img, 0, 0, SAMP, None); cv.restore()

# ───────── 문자 스프라이트 ─────────
def face_for(face):
    return FACE_EN.get(face, face) if LANG == "en" else face

CHIP_MAXW = 880 if SHORT else 1480

def chip_sp(ch, maxw=None):
    text = ch[LANG]
    face = face_for(ch["face"]); col = COLS[ch["col"]]
    size = ch["size"]
    mw = maxw or CHIP_MAXW
    wpx = tw(text, size, face) + 68
    if wpx > mw:
        size = size * mw / wpx
    key = f"{LANG}_{text}_{size:.1f}_{face}_{ch['col']}_{ch['rot']}"
    return chip_sprite(key, text, size, face, col, ch["rot"], tcol=TXT)

def parse_segs(line):
    segs, i = [], 0
    while i < len(line):
        j = line.find("[[", i)
        if j < 0: segs.append((line[i:], False)); break
        if j > i: segs.append((line[i:j], False))
        k = line.find("]]", j); segs.append((line[j + 2:k], True)); i = k + 2
    return segs

def cap_sp(disp, size, maxw):
    disp = disp.replace("…", "...")
    lines = disp.split("\n")
    nf, hf = ("geist", "geist") if LANG == "en" else ("jua", "black")
    segl = [parse_segs(l) for l in lines]
    def lw(sg, s): return sum(tw(t, s * (1.1 if hi else 1.0), hf if hi else nf) for t, hi in sg)
    widest = max(lw(sg, size) for sg in segl)
    if widest > maxw: size = size * maxw / widest; widest = maxw
    lh = size * 1.32
    # 상하 여백을 같게: 첫 줄 위 여백 ≈ 마지막 줄 아래 여백(글자 아래 끝이 박스에 닿던 문제, 사용자 지시 2026-10-26)
    bot = 22 + size * 0.22
    w = int(widest + 140); h = int(62 + size * 0.98 + lh * (len(lines) - 1) + bot + 40)
    key = f"cap_{LANG}_{disp}_{size:.1f}"
    def fn(img):
        pad = 34
        m = rr(w, h, 40, 40, w - 40, h - 40, 34)
        img = P_(img, m, CREAMC, 77, soft=8, sh=(5, 8), blur=8, k=0.26, depth=0.6)
        y = 40 + 22 + size * 0.98
        for sg in segl:
            x = w / 2 - lw(sg, size) / 2
            for t, hi in sg:
                s = size * (1.1 if hi else 1.0)
                img, wd = put_text(img, w, h, t, x, y + (0 if not hi else size * 0.03), s, hf if hi else nf, CORALC if hi else TXT, "l", shadow=False)
                if hi:
                    img = highlight(img, w, h, x - 2, x + wd + 2, y + size * 0.12, h=int(size * 0.22), seed=int(x), col=LIME) if False else img
                x += wd
            y += lh
        return img
    sp = sprite(key, w, h, fn)
    if sp is not None: sp["cap_h"] = h
    return sp

def txt_chip(key, text, size, face, col, rot=0, tcol=None):
    return chip_sprite(key, text, size, face_for(face), COLS[col] if isinstance(col, str) else col, rot, tcol=tcol or TXT)

# ───────── 소품 스프라이트 접근 ─────────
def SPR(name, *a):
    return getattr(PR, name)(*a)

# ───────── 장면 그리기 ─────────
def actor_state(ch, name):
    a = ch["actors"].get(name)
    if a is None: return None
    x, mood = a[0], a[1]
    sc = a[2] if len(a) > 2 else 1.0
    opts = a[3] if len(a) > 3 else {}
    return dict(x=x, mood=mood, sc=sc, opts=opts, y=opts.get("y", LOC_FLOOR.get(ch["loc"], FLOOR_Y)))

def draw_actor(cv, name, i, lt, tm, wipe_off):
    ch = CH_LIST[i]
    st = actor_state(ch, name)
    prev = CH_LIST[i - 1] if i > 0 else None
    pst = actor_state(prev, name) if prev and prev["loc"] == ch["loc"] else None
    nact = len(ch["actors"])
    mul = 1.0 if ch["loc"] in ("iv", "endcard") else {1: 1.5, 2: 1.42, 3: 1.28, 4: 1.1, 5: 0.95}.get(nact, 1.0)
    x, y, sc = st["x"], st["y"], st["sc"] * mul
    sx = sy = 1.0; hop = 0.0; rot = 0.0; al = 1.0
    ph = (zlib.crc32(name.encode()) % 100) / 100.0 * 6.28
    lt_e = lt - wipe_off
    if pst is None:
        idx = list(ch["actors"]).index(name)
        if i == 0 and SHORT: sx = sy = 1.0
        else:
            sx, sy = pop(lt_e, 0.05 + 0.07 * idx, 24, 0.55, 0.14)
            if lt_e < 0: return
    else:
        MV = 0.32
        u = eio(lt / MV)
        pmul = 1.0 if prev["loc"] in ("iv", "endcard") else {1: 1.5, 2: 1.42, 3: 1.28, 4: 1.1, 5: 0.95}.get(len(prev["actors"]), 1.0)
        psc = pst["sc"] * pmul
        if abs(pst["x"] - x) > 4 or abs(psc - sc) > 0.01:
            x = pst["x"] + (x - pst["x"]) * u; sc = psc + (sc - psc) * u
            hop += abs(math.sin(math.pi * u * 2)) * 22 * (1 if u < 1 else 0)
            rot += 6 * math.sin(math.pi * u * 3) * (1 if u < 1 else 0)
    o = st["opts"]
    if o.get("run"):
        amp = 85
        x += amp * math.sin(2 * math.pi * 0.62 * tm + ph)
        hop += abs(math.sin(2 * math.pi * 2.6 * tm + ph)) * 34
        rot += 7 * math.cos(2 * math.pi * 0.62 * tm + ph) * (1 if True else 0)
    elif o.get("hop"):
        hop += abs(math.sin(2 * math.pi * 1.7 * lt + ph)) * 20
    elif o.get("wave"):
        rot += 7 * math.sin(2 * math.pi * 1.4 * tm + ph); hop += abs(math.sin(2 * math.pi * 1.4 * tm + ph)) * 8
    else:
        rot += 1.8 * math.sin(2 * math.pi * 0.55 * tm + ph)
        sy *= 1 + 0.012 * math.sin(2 * math.pi * 0.9 * tm + ph)
    spk = SIDNAME.get(ch["sid"]) if ch["sid"] is not None else None
    if spk == name:
        e = env_of(i, tm - S_AUD[i])
        sy *= 1 + 0.06 * e; sx *= 1 - 0.035 * e; hop += 9 * e
    sp = chsp(name, st["mood"])
    # 그림자는 스프라이트에 포함 → 점프할 때 몸만 올라가는 대신 같이 올라감(작은 높이라 허용)
    blit(cv, sp, x, y - hop, sc, rot, sx, sy, al, CH_ANCHOR)

def draw_exit(cv, i, lt, wipe_off):
    """이전 조각에 있었고 지금은 없는 캐릭터: 0.25초 동안 줄어들며 사라짐"""
    if i == 0 or lt - wipe_off > 0.25 or SHORT: return
    ch, prev = CH_LIST[i], CH_LIST[i - 1]
    if prev["loc"] != ch["loc"]: return
    for name in prev["actors"]:
        if name in ch["actors"]: continue
        st = actor_state(prev, name); u = clamp01((lt - wipe_off) / 0.25)
        pm = {1: 1.5, 2: 1.42, 3: 1.28, 4: 1.1, 5: 0.95}.get(len(prev["actors"]), 1.0)
        blit(cv, chsp(name, st["mood"]), st["x"], st["y"], st["sc"] * pm * (1 - 0.3 * u), 0, 1, 1, 1 - u, CH_ANCHOR)

_FALLBACK_WARN = set()

def draw_chips(cv, i, lt, wipe_off):
    ch = CH_LIST[i]; prev = CH_LIST[i - 1] if i > 0 else None
    for c in ch.get("chips", []):
        same = prev is not None and prev["loc"] == ch["loc"] and any(p.get("sticky") and p.get("sticky") == c.get("sticky") for p in prev.get("chips", []))
        sp = chip_sp(c)
        cx = c["x"] + (0 if not SHORT else 0)
        if same or (SHORT and i == 0 and c["t0"] == 0.0):
            sx = sy = 1.0
        else:
            sx, sy = pop(lt - wipe_off, c["t0"], 26, 0.6, 0.12)
        wob = math.sin(2 * math.pi * 0.5 * lt) * 1.2
        blit(cv, sp, cx, c["y"], 1.0, c["rot"] * 0 + wob, sx, sy)

# ───────── 소품 ─────────
def hands(cv, i, lt, loc):
    tmap = dict(office_night=(960, 230, 110), office_day=(960, 230, 110), meeting=(1760, 200, 80), night=(960, 220, 100))
    if loc not in tmap: return
    ch = CH_LIST[i]
    if "time" not in ch: return
    cx, cy, R = tmap[loc]
    def hm(t): return t[0] % 12 * 30 + t[1] * 0.5, t[1] * 6
    h1, m1 = hm(ch["time"])
    prev = CH_LIST[i - 1] if i > 0 else None
    if prev and "time" in prev and prev["loc"] == loc:
        h0, m0 = hm(prev["time"]); u = eio(lt / 0.6)
        dm = ((m1 - m0) % 360) * u; mm = m0 + dm; hh = h0 + (((h1 - h0) % 360)) * u
    else:
        mm, hh = m1, h1
    sc = R / 110
    blit(cv, PR.hands_sprite("hr"), cx, cy, sc, hh); blit(cv, PR.hands_sprite("min"), cx, cy, sc, mm)

def draw_props(cv, i, lt, tm, wipe_off):
    ch = CH_LIST[i]
    lt_e = lt - wipe_off
    for (name, a) in ch.get("props", []):
        f = PROPS.get(name)
        if f: f(cv, i, lt, lt_e, tm, a)

def P_remote(cv, i, lt, lte, tm, a):
    sp = PR.remote(); x, y, sc = a["x"], a["y"], a["sc"]
    if a.get("fell"): blit(cv, sp, x + 40, 825, sc, 80)
    elif a.get("drop") is not None and a.get("drop", -1) >= 0:
        d = lte - a["drop"]
        if d < 0: blit(cv, sp, x, y, sc, -10)
        else:
            u = min(d / 0.45, 1); blit(cv, sp, x + 40 * u, y + (825 - y) * u * u, sc, -10 + 90 * u)
    else: blit(cv, sp, x, y, sc, -10 + 3 * math.sin(tm * 2))

def P_burst(cv, i, lt, lte, tm, a):
    if a["t"] < 0: return
    sx, sy = pop(lte, a["t"], 30, 0.5, 0.2)
    blit(cv, PR.burst(a["txt"]), a["x"] + 3 * math.sin(tm * 40), a["y"], 1.0, 8 * math.sin(tm * 30), sx, sy)

def P_board(cv, i, lt, lte, tm, a): pass

def food_sprite(kind):
    if kind == "food1": return PR.bucket(LANG) if LANG == "ko" else PR.pizza()
    if kind == "food3": return PR.ramen(LANG)
def P_food(kind):
    def f(cv, i, lt, lte, tm, a):
        t0 = a.get("t", 0.0)
        if kind == "food2":
            sa, sb = PR.food2a(LANG), PR.food2b(LANG)
            if t0 < 0: dy = 0; sx = sy = 1.0
            else:
                u = clamp01((lte - t0) / 0.4); dy = -500 * (1 - eo(u)) ; sx = sy = 1
                if lte < t0: return
            blit(cv, sa, a["x"] - 90, a["y"] + dy, 0.8, 0); blit(cv, sb, a["x"] + 110, a["y"] + dy - 10, 0.8, 8)
            return
        sp = food_sprite(kind)
        if t0 < 0:
            dy = 0; sc = a.get("sc", 1.0) * a.get("shrink", 1.0); rot = 4 * math.sin(tm * 3) if not a.get("shrink") else 8 * math.sin(tm * 14)
        else:
            if lte < t0: return
            u = clamp01((lte - t0) / 0.42); dy = -520 * (1 - eo(u)); sc = a.get("sc", 1.0); rot = 0
            if lte > t0 + 0.42:
                sxx, syy = pop(lte, t0 + 0.42, 30, 0.45, 0.2)
                blit(cv, sp, a["x"], a["y"], sc, 0, 1 + 0.15 * (1 - syy), 1 - 0.15 * (1 - syy)); return
        blit(cv, sp, a["x"], a["y"] + dy, sc, rot)
    return f

def P_clip(cv, i, lt, lte, tm, a):
    blit(cv, PR.clipboard(LANG), a["x"], a["y"] + 4 * math.sin(tm * 3), a["sc"], -6 + 3 * math.sin(tm * 2))

def P_stamp(cv, i, lt, lte, tm, a):
    sp = PR.stamp_tool()
    if a.get("slam") is not None and a.get("t_up", 0) < 0:
        d = lte - a["slam"]; y = a["y"] - 70 + (110 if d > 0 else 0)
        if 0 < d < 0.12: y = a["y"] - 70 + 110 * (d / 0.12)
        blit(cv, sp, a["x"], y, 1.0, 0)
    else:
        blit(cv, sp, a["x"], a["y"] - 70 - 20 * eo(lte / 0.3), 1.0, -8 + 3 * math.sin(tm * 6))

def P_stampmk(cv, i, lt, lte, tm, a):
    if a["t"] < 0:
        blit(cv, PR.stamp_mark(a["kind"], LANG), a["x"], a["y"], 1.0, -12); return
    if lte < a["t"]: return
    sx, sy = pop(lte, a["t"], 34, 0.5, 0.2)
    blit(cv, PR.stamp_mark(a["kind"], LANG), a["x"], a["y"], 1.0, -12, sx * 1.1, sy * 1.1)

def P_sweat(cv, i, lt, lte, tm, a):
    for k in range(3):
        u = ((tm * 1.4 + k * 0.33) % 1.0)
        blit(cv, PR.sweat(), a["x"] + (k - 1) * 46, a["y"] + u * 70 - 20, 0.6, 0, 1, 1, 1 - u * 0.8)

def P_belt(cv, i, lt, lte, tm, a):
    sp = PR.crate()
    spd = a.get("speed", 1.0)
    if "dash" not in _MEM_DASH:
        def fn(img): return P_(img, rr(120, 40, 20, 8, 100, 32, 12), hx(0xF1ECF6), 3, soft=3, sh=(1, 2), blur=2, k=0.12, depth=0.4)
        _MEM_DASH["dash"] = sprite("dash", 120, 40, fn)
    d = _MEM_DASH["dash"]
    ofs = (tm * 170 * spd) % 150
    for k in range(-1, 13):
        blit(cv, d, 180 + k * 150 + ofs, 836, 1.0, 0)
_MEM_DASH = {}

def P_crates(cv, i, lt, lte, tm, a):
    sp = PR.crate()
    for k in range(5):
        x = ((tm * 230 + k * 440) % 2200) - 150
        blit(cv, sp, x, 782, 1.0, 0)

def P_acid(cv, i, lt, lte, tm, a):
    sp = PR.bubble_acid()
    if a.get("short"):
        for k in range(10):
            u = ((tm * 0.35 + k * 0.1) % 1.0)
            blit(cv, sp, a["sx"] + 180 * math.sin(k * 2.1 + tm * 1.5) * (0.4 + u * 0.6), a["sy"] - u * 520, 0.6 + 0.5 * u, 0, 1, 1, 1 - u * u)
        return
    for k in range(14):
        u = ((tm * 0.42 + k * 0.071) % 1.0)
        bx = 300 + (k * 137) % 1100 + 40 * math.sin(tm * 2 + k)
        blit(cv, sp, bx, 640 - u * 520, 0.55 + 0.6 * u, 0, 1, 1, min(1, (1 - u) * 1.5))

def P_cups(cv, i, lt, lte, tm, a):
    sp = PR.cup()
    t0 = a.get("t", 0.0)
    if t0 < 0:
        for k, x in enumerate((600, 700, 1000)): blit(cv, sp, x + 40, 720, 0.8, 0)
        return
    if lte < t0: return
    u = eio((lte - t0) / 0.9)
    for k, (x0, x1) in enumerate(((1280, 760), (1280, 1000))):
        blit(cv, sp, x0 + (x1 - x0) * u, 700 - 40 * math.sin(math.pi * u), 0.8, -10 + 20 * u)

def P_hearts(cv, i, lt, lte, tm, a):
    sp = PR.heartsp(0xF58FA0, 28)
    for k in range(5):
        u = ((tm * 0.5 + k * 0.2) % 1.0)
        blit(cv, sp, a["x"] + 70 * math.sin(k * 2 + tm * 2), a["y"] - u * 160, 0.6 + 0.5 * u, 0, 1, 1, 1 - u)

def P_sparkles(cv, i, lt, lte, tm, a):
    sp = PR.starsp(0xF6CB45, "star", 34)
    for k in range(6):
        ang = k * 1.047 + tm * 0.8; r = 300 + 20 * math.sin(tm * 3 + k)
        sx, sy = pop(lte, 0.1 + 0.06 * k, 26, 0.55, 0.1)
        blit(cv, sp, a["x"] + r * math.cos(ang), a["y"] + r * 0.7 * math.sin(ang), 0.9, tm * 60, sx, sy)

def P_lights_out(cv, i, lt, lte, tm, a):
    al = 0.55 * (1 - clamp01(lt / (S_LEN[i] + 0.2)) ** 3)
    cv.save(); p = skia.Paint(); p.setColor(skia.Color(20, 24, 60, int(255 * al))); cv.drawRect(skia.Rect(0, 0, DW, DH), p); cv.restore()

def P_notice(cv, i, lt, lte, tm, a):
    if LANG == "ko":
        lines = ["야식은 일찍, 가볍게!", "자기 3시간 전엔 식사 끝", "(NIH 안내)", "증상이 계속되면 병원 상담"]; title = "사내 공지"
    else:
        lines = ["Late snack? Early & light!", "Finish 3 hours before bed", "(NIH guidance)", "Symptoms persist? See a doctor"]; title = "NOTICE"
    sp = PR.speech_notice(LANG + "1", lines, 860 if LANG == "ko" else 980, 46 if LANG == "ko" else 40, title)
    sx, sy = pop(lte, 0.2, 24, 0.6, 0.1)
    blit(cv, sp, a["x"], a["y"], 0.62, -3 + math.sin(tm * 1.5), sx, sy)

def P_thumbup(cv, i, lt, lte, tm, a):
    if a["t"] < 0:
        blit(cv, PR.thumb(), a["x"], a["y"], 0.95 * a.get("sc", 1.0), -6 + 6 * math.sin(tm * 3))
        return
    sx, sy = pop(lte, a["t"], 24, 0.5, 0.2)
    sc = a.get("sc", 1.0)
    sp2 = PR.starsp(0xF6CB45, "star", 30)
    blit(cv, PR.thumb(), a["x"], a["y"], 0.95 * sc, -6 + 6 * math.sin(tm * 3), sx, sy)
    for k in range(4):
        ang = k * 1.57 + 0.7
        u = clamp01((lte - a["t"] - 0.1) / 0.5)
        if 0 < u < 1: blit(cv, sp2, a["x"] + math.cos(ang) * 190 * eo(u), a["y"] + math.sin(ang) * 190 * eo(u), 0.8 * (1 - u), tm * 90, 1, 1, 1 - u)

def P_bellp(cv, i, lt, lte, tm, a):
    if a["t"] < 0: return
    sx, sy = pop(lte, a["t"], 24, 0.5, 0.2)
    blit(cv, PR.bell(), a["x"], a["y"], 0.8, 14 * math.sin(tm * 12) * math.exp(-(lte - a["t"]) * 0.6), sx, sy)

def P_pillow(cv, i, lt, lte, tm, a):
    def fn(img):
        N = 520
        img = P_(img, rr(N, N, 40, 360, 480, 420, 20), hx(0xE9776E), 3, soft=8)
        p = skia.Path(); p.moveTo(70, 350); p.lineTo(450, 350); p.lineTo(450, 250); p.close()
        m = M(N, N); m.cv.drawPath(p, paint())
        img = P_(img, m.arr(), hx(0xCDEBDD), 4, soft=9)
        img = P_(img, rr(N, N, 60, 220, 250, 340, 50, -14), hx(0xFBF4E6), 5, soft=12)
        return img
    sp = sprite("wedge", 520, 520, fn)
    sx, sy = pop(lte, 0.1, 24, 0.6, 0.1)
    blit(cv, sp, a["x"], a["y"], 1.0, 0, sx, sy)

def P_sstar(cv, i, lt, lte, tm, a):
    size = a.get("size", 150); txt = a["txt"] if LANG == "ko" else a["txt_en"]
    R = 310
    N = 2 * R + 80
    def fn(img):
        m = star(N, N, N / 2, N / 2, R, -90, 0.62, 16)
        img = P_(img, m, GOLD, 5, soft=14)
        img, _ = put_text(img, N, N, txt, N / 2, N / 2 + size * 0.34, size, "black" if LANG == "ko" else "geist", NAVYC, "c", shadow=False)
        return img
    sp = sprite(f"sstar_{LANG}_{txt}_{size}", N, N, fn)
    if a.get("keep") or (SHORT and i == 0): sx = sy = 1.0
    else: sx, sy = pop(lte, 0.15, 22, 0.55, 0.12)
    blit(cv, sp, a["x"], a["y"], 0.86, -4 + 3 * math.sin(tm * 2), sx, sy)

def P_sclock(cv, i, lt, lte, tm, a):
    txt = a["txt"]; unit = a["unit"] if LANG == "ko" else a["unit_en"]
    R = 200
    sp = PR.clock_sprite(R, "sclk")
    sx, sy = (1.0, 1.0) if (a.get("keep") or (SHORT and i == 0)) else pop(lte, 0.1, 22, 0.55, 0.12)
    cx, cy = a["x"], a["y"]
    blit(cv, sp, cx, cy - 20, 1.0, 0, sx, sy)
    # 부채꼴(숫자 링 안쪽까지만) + 바늘
    ang = 360 * 3 / 12 * clamp01((lte - 0.3) / 1.2) if not a.get("keep") else 90
    ph = PR.hands_sprite("min")
    blit(cv, PR.hands_sprite("hr"), cx, cy - 20, 200 / 110, 0 + 0, sx, sy)
    blit(cv, ph, cx, cy - 20, 200 / 110, ang, sx, sy)
    def fnb(img):
        N = 560
        img = P_(img, rr(N, N, 60, 200, 500, 360, 70), CORALC, 6, soft=10)
        s = f"{txt}{unit}"
        img, _ = put_text(img, N, N, s, N / 2, 318, 120, "black" if LANG == "ko" else "geist", hx(0xFFF8EE), "c", shadow=False)
        return img
    badge = sprite(f"sbadge_{LANG}_{txt}{unit}", 560, 560, fnb)
    bx, by = pop(lte, 0.45, 26, 0.55, 0.12) if not (a.get("keep") or (SHORT and i == 0)) else (1.0, 1.0)
    blit(cv, badge, cx + 20, cy + 250, 0.8, -4, bx, by)

def P_sclock1(cv, i, lt, lte, tm, a):
    R = 200
    sp = PR.clock_sprite(R, "sclk")
    sx, sy = (1.0, 1.0) if (SHORT and i == 0) else pop(lte, 0.1, 22, 0.55, 0.12)
    cx, cy = a["x"], a["y"]
    blit(cv, sp, cx, cy - 20, 1.0, 0, sx, sy)
    blit(cv, PR.hands_sprite("hr"), cx, cy - 20, 200 / 110, 30, sx, sy); blit(cv, PR.hands_sprite("min"), cx, cy - 20, 200 / 110, 0, sx, sy)

def P_subchip(cv, i, lt, lte, tm, a):
    c = dict(ko="구독", en="SUBSCRIBE", x=0, y=0, size=120, face="black", col="coral", rot=-3)
    sp = chip_sp(c, 460)
    sx, sy = pop(lte, a.get("t", 0.2), 24, 0.5, 0.12)
    blit(cv, sp, a["x"], a["y"], 0.95, -3 + 3 * math.sin(tm * 4), sx, sy)
    sx2, sy2 = pop(lte, a.get("t", 0.2) + 0.2, 24, 0.5, 0.12)
    blit(cv, PR.bell(), a["x"] + (150 if LANG == "ko" else 80), a["y"] - 150, 0.34, 14 * math.sin(tm * 12) * math.exp(-(lte - 0.5) * 0.7), sx2, sy2)

ENDINFO = {}
if os.path.exists("/home/claude/work/endinfo.json"):
    ENDINFO = json.load(open("/home/claude/work/endinfo.json"))

def P_endcard(cv, i, lt, lte, tm, a):
    inf = ENDINFO.get(LANG, {})
    title = inf.get("title", "다음 영상" if LANG == "ko" else "Next video")
    thumb = inf.get("thumb"); logo = inf.get("logo")
    # 폴라로이드(왼쪽 위 큰 칸): 프레임 800x520 @ (140,100)
    def fnp(img):
        N1, N2 = 860, 600
        img = P_(img, rr(N1, N2, 30, 30, 830, 570, 28), hx(0xFFFBF2), 7, soft=9, sh=(8, 12), blur=10, k=0.3)
        if thumb and os.path.exists(thumb):
            _im = Image.open(thumb).convert("RGB")
            _w, _h = _im.size
            _ch = int(_w * 9 / 16)
            if _h > _ch + 2: _im = _im.crop((0, (_h - _ch) // 2, _w, (_h - _ch) // 2 + _ch))
            t = np.asarray(_im.resize((720, 405), Image.LANCZOS)).astype(np.float32) / 255
            m = rr(N1, N2, 70, 62, 790, 467, 14)
            full = np.zeros((N2, N1, 3), np.float32); full[62:467, 70:790] = t
            img = P_(img, m, hx(0xE4E4E4), 8, soft=4, sh=(2, 3), blur=3, k=0.2, depth=0.3)
            img = img * (1 - m[..., None]) + full * m[..., None]
        else:
            m = rr(N1, N2, 70, 62, 790, 467, 14)
            img = P_(img, m, hx(0xCDEBDD), 8, soft=6)
            tri = poly_mask(N1, N2, [(380, 190), (380, 340), (500, 265)])
            img = P_(img, tri, hx(0xFBF4E6), 9, soft=5)
        return img
    pol = sprite("polaroid_" + LANG + str(bool(thumb)), 860, 600, fnp)
    sx, sy = pop(lte, 0.1, 22, 0.6, 0.08)
    blit(cv, pol, 570, 330, 1.0, -2, sx, sy)
    # 제목 (한 줄 또는 두 줄)
    face = "jua" if LANG == "ko" else "geist"
    title = title.replace("·", "/").replace("…", "..").replace("★", "").strip()
    words = title if tw(title, 34, face) < 720 else title[:28] + ".."
    ts = txt_sprite("ttl_" + LANG + words, words, 34, face)
    blit(cv, ts, 570, 572, 1.0, 0, sx, sy)
    # 구독 자리(오른쪽 위)
    def fns(img):
        img = P_(img, rr(640, 480, 30, 30, 610, 450, 60), hx(0xFFF3EA), 10, soft=10, sh=(6, 9), blur=8, k=0.26)
        return img
    slot = sprite("subslot", 640, 480, fns)
    blit(cv, slot, 1470, 285, 1.0, 2, *pop(lte, 0.25, 22, 0.6, 0.08))
    c = dict(ko="구독", en="SUBSCRIBE", x=0, y=0, size=110, face="black", col="coral", rot=0)
    blit(cv, chip_sp(c, 500), 1470, 290, 1.0, -3, *pop(lte, 0.45, 24, 0.5, 0.12))
    blit(cv, PR.bell(), 1470, 175, 0.3, 12 * math.sin(tm * 10), *pop(lte, 0.6, 24, 0.5, 0.12))
    # 로고 + 채널명 + 슬로건 (아래 가운데)
    def fnl(img):
        N = 300
        m = circ(N, N, N / 2, N / 2, 110)
        img = P_(img, circ(N, N, N / 2, N / 2, 122), hx(0xFFF8EE), 12, soft=8)
        if logo and os.path.exists(logo):
            t = np.asarray(Image.open(logo).convert("RGB").resize((220, 220), Image.LANCZOS)).astype(np.float32) / 255
            full = np.zeros((N, N, 3), np.float32); full[40:260, 40:260] = t
            img = img * (1 - m[..., None]) + full * m[..., None]
        else:
            img = P_(img, m, hx(0xF4B3A8), 13, soft=8)
            img, _ = put_text(img, N, N, "TB" if LANG == "en" else "몸", N / 2, N / 2 + 26, 80, "black", hx(0xFFF8EE), "c", shadow=False)
        return img
    lg = sprite("logo_" + LANG + str(bool(logo)), 300, 300, fnl)
    blit(cv, lg, 960, 690, 1.0, 0, *pop(lte, 0.3, 22, 0.6, 0.08))
    nm = "몸속 주식회사" if LANG == "ko" else "Tiny Body Co."
    blit(cv, chip_sp(dict(ko=nm, en=nm, x=0, y=0, size=64, face="black", col="mint", rot=0)), 960, 848, 1.0, 0, *pop(lte, 0.4, 22, 0.6, 0.1))
    slg = "오늘도 야근 중! 내 몸속 직원들의 건강 시트콤" if LANG == "ko" else "The office sitcom inside your body."
    blit(cv, txt_sprite("slg_" + LANG, slg, 36, face), 960, 938, 1.0, 0, *pop(lte, 0.5, 22, 0.6, 0.06))


def P_pose(cv, i, lt, lte, tm, a):
    """운동·자세 동작 시연용 뼈대(관절) 다이어그램(사용자 지시 2026-10-28: 캐릭터 연기만으로는 동작이
    이해되지 않는다 → 캐릭터 옆에 관절점+뼈대선 진단판을 띄워 자세 변화를 명확히 보여준다).
    a 필드:
      x, y: 진단판(카드) 중심. sc: 전체 배율(기본 1). card_w/card_h: 카드 크기(기본 420x520).
      key: 캐시 키(장면마다 다르게). title_ko/title_en: 카드 위쪽 제목칩(선택).
      root: 관절 체인 시작점, 카드 중심 기준 상대좌표 (x,y)(기본 (0, card_h*0.22)).
      bones: [{length, width, color, frm, to, key(선택, 뼈 이름), joint_r(선택)}, ...] 순서대로 이어 그리는 관절 체인.
             frm/to는 수직(12시) 기준 시계방향 각도(도). 이전 뼈의 끝점이 다음 뼈의 시작점이 된다.
      hold: 전환이 시작되는 시각(초, lte 기준). dur: frm→to 전환 길이(초).
      loop: True면 sin으로 frm↔to를 왕복(반복 동작, 기본 False=한 번만 전환해 유지).
      loop_speed: loop일 때 왕복 속도(기본 1.6).
      ghost: True(기본)면 시작 자세를 옅게 겹쳐 보여줘(전/후 비교) 변화가 뚜렷해진다.
      badge: "10번" 같은 작은 숫자 배지 문구(선택, 카드 아래쪽에 표시).
    """
    cx, cy = a["x"], a["y"]; sc = a.get("sc", 1.0)
    cw, chh = a.get("card_w", 420), a.get("card_h", 520)
    key = a.get("key", "pose")
    appear_sx, appear_sy = pop(lte, a.get("hold", 0.0) - 0.2, 24, 0.55, 0.12)
    blit(cv, PR.pose_card(cw, chh, key), cx, cy, sc, 0, appear_sx, appear_sy)
    title = a.get("title_ko") if LANG == "ko" else a.get("title_en")
    if title:
        tsp = chip_sprite(f"posetitle_{LANG}_{title}", title, 38, "jua" if LANG == "ko" else "geist", MINTC, 0, tcol=NAVYC)
        blit(cv, tsp, cx, cy - chh * sc / 2 + 50 * sc, sc, 0, appear_sx, appear_sy)
    if a.get("loop"):
        u = (math.sin(lte * a.get("loop_speed", 1.6)) + 1) / 2
    else:
        u = eo(clamp01((lte - a.get("hold", 0.0)) / max(a.get("dur", 1.0), 0.01)))
    rootx, rooty = a.get("root", (0, chh * 0.22))
    px0, py0 = cx + rootx * sc, cy + rooty * sc
    bones = a["bones"]
    if a.get("ghost", True) and not a.get("loop"):
        px, py = px0, py0
        for b in bones:
            ang = b["frm"]
            blit(cv, PR.pose_bone(b["length"], b["width"], b["color"], key + "_" + b.get("key", "b")), px, py, sc, ang, 1, 1, 0.28 * appear_sx)
            px, py = px + sc * b["length"] * math.sin(math.radians(ang)), py - sc * b["length"] * math.cos(math.radians(ang))
    px, py = px0, py0
    for b in bones:
        ang = b["frm"] + (b["to"] - b["frm"]) * u
        blit(cv, PR.pose_bone(b["length"], b["width"], b["color"], key + "_" + b.get("key", "b")), px, py, sc, ang, 1, 1, appear_sx)
        blit(cv, PR.pose_joint(b.get("joint_r", b["width"] * 0.55), 0x26304F, key), px, py, sc, 0, 1, 1, appear_sx)
        px, py = px + sc * b["length"] * math.sin(math.radians(ang)), py - sc * b["length"] * math.cos(math.radians(ang))
    blit(cv, PR.pose_joint(bones[-1].get("joint_r", bones[-1]["width"] * 0.55), 0x26304F, key + "_tip"), px, py, sc, 0, 1, 1, appear_sx)
    if a.get("badge"):
        blit(cv, PR.pose_angle_badge(a["badge"], key), cx, cy + chh * sc / 2 - 60 * sc, sc, 0, appear_sx, appear_sy)

PROPS = dict(remote=P_remote, burst=P_burst, board=P_board, food1=P_food("food1"), food2=P_food("food2"), food3=P_food("food3"), clip=P_clip, stamp=P_stamp,
             stampmk=P_stampmk, sweat=P_sweat, belt=P_belt, crates=P_crates, acid=P_acid, cups=P_cups, hearts=P_hearts, sparkles=P_sparkles, lights_out=P_lights_out,
             notice=P_notice, thumbup=P_thumbup, bellp=P_bellp, pillow=P_pillow, sstar=P_sstar, sclock=P_sclock, sclock1=P_sclock1, subchip=P_subchip, endcard=P_endcard, pose=P_pose)

# ───────── 효과 ─────────
def alarm_fx(cv, tm, loc):
    on = int(tm * 4) % 2 == 0
    pulse = 0.5 + 0.5 * math.sin(tm * 12)
    # 붉은 비네팅(가장자리)
    cv.save(); p = skia.Paint(); p.setShader(skia.GradientShader.MakeRadial((DW / 2, DH / 2), max(DW, DH) * 0.75, [skia.Color(255, 60, 50, 0), skia.Color(255, 60, 50, int(90 * pulse + 20))], [0.55, 1.0]))
    cv.drawRect(skia.Rect(0, 0, DW, DH), p); cv.restore()
    lx, ly = (DW - 150, 150) if not SHORT else (DW - 150, 260)
    blit(cv, PR.halo(), lx, ly - 20, 0.9 + 0.3 * pulse, 0, 1, 1, 0.8 if on else 0.3)
    blit(cv, PR.lamp(on), lx, ly, 0.8, 0)

def siren_fx_chunk(ch): return "alarm" in ch.get("fx", [])

def draw_scene(cv, i, lt, tm, wipe_off=0.0, wiped=False):
    """한 조각의 화면(배경+캐릭터+소품+칩). 자막과 전환은 호출하는 쪽."""
    ch = CH_LIST[i]; loc = ch["loc"]
    shake = 0.0
    for f in ch.get("fx", []):
        if f == "shake1": shake = 5
        if f == "shake2": shake = 11
    cv.save()
    cv.scale(K, K)
    if shake: cv.translate(shake * math.sin(tm * 61), shake * 0.7 * math.cos(tm * 53))
    if loc in ("s_a", "s_b", "iv", "end", "end_thanks"): pass
    draw_bg(cv, loc if loc not in ("s_a", "s_b") else loc)
    hands(cv, i, lt, loc)
    # 소품 중 뒤쪽(벨트, 크레이트, 공지)
    props_back = [p for p in ch.get("props", []) if p[0] in ("belt", "crates", "board", "sstar", "sclock", "sclock1", "pillow")]
    props_front = [p for p in ch.get("props", []) if p[0] not in ("belt", "crates", "board", "sstar", "sclock", "sclock1", "pillow")]
    chb = dict(ch); chb["props"] = props_back
    old = CH_LIST[i]; CH_LIST[i] = chb
    draw_props(cv, i, lt, tm, wipe_off)
    CH_LIST[i] = old
    draw_chips(cv, i, lt, wipe_off)
    draw_exit(cv, i, lt, wipe_off)
    order = sorted(ch["actors"], key=lambda n: ch["actors"][n][0])
    for n in order:
        draw_actor(cv, n, i, lt, tm, wipe_off)
    chf = dict(ch); chf["props"] = props_front
    CH_LIST[i] = chf
    draw_props(cv, i, lt, tm, wipe_off)
    CH_LIST[i] = old
    if loc == "iv":
        iv = ch["iv"]
        nm = iv[0] if LANG == "ko" else iv[2]; dp = iv[1] if LANG == "ko" else iv[3]
        face = "black" if LANG == "ko" else "geist"
        sx, sy = pop(lt - wipe_off, 0.3, 22, 0.6, 0.1)
        blit(cv, chip_sprite(f"iv_{LANG}_{nm}_{dp}", f"{nm} ({dp})", 56, face, CORAL_L if False else hx(0xF4B3A8), -2), 520, 700, 1.0, 0, sx, sy)
        # REC 표시
        blink = int(tm * 1.6) % 2 == 0
        rc = chip_sprite("rec", "REC", 40, "geist", hx(0xFFF8EE), 0)
        blit(cv, rc, 150, 110, 1.0, 0)
        if blink: blit(cv, PR.starsp(0xE9534A, "rec", 16), 90, 106, 0.7, 0)
    if siren_fx_chunk(ch): alarm_fx(cv, tm, loc)
    cv.restore()

TAGTXT = dict(ko="몸속 주식회사" if not SHORT else "쏙쏙 건강백과", en="Tiny Body Co.")

def draw_tag(cv):
    s = TAGTXT[LANG]
    sp = chip_sprite(f"tag_{LANG}_{s}", s, 44 if not SHORT else 46, "jua" if LANG == "ko" else "geist", CREAMC, -2, 28, 16, TXT, 22)
    x = 70 + sp["cw"] / 2 - 0
    blit(cv, sp, 70 + (tw(s, 44 if not SHORT else 46, "jua" if LANG == "ko" else "geist") + 56) / 2 + 20, 86 if not SHORT else 150, 1.0, 0)

def draw_caption(cv, i, tm):
    ch = CH_LIST[i]
    if ch["sid"] is None: return
    disp = TX[ch["id"]][1]
    if not disp: return
    lt = tm - S_AUD[i]
    if lt < -0.02: return
    if SHORT:
        size, maxw, cy = 60, 910, 1596
    else:
        nl = disp.count("\n") + 1
        size, maxw, cy = (54 if nl < 3 else 42), 1680, 1056
        if ch["loc"] == "iv" and nl >= 3: size = 40
    sp = cap_sp(disp, size, maxw)
    if sp is None: return
    sx, sy = pop(lt, 0.0, 30, 0.6, 0.06)
    blit(cv, sp, DW / 2, cy - 30 if True else cy, 1.0, 0, sx, sy, 1.0, (sp["cw"] / 2, sp["ch"] - 40))

def render_frame(cv, tm):
    cv.clear(skia.ColorWHITE)
    i = chunk_at(tm)
    ch = CH_LIST[i]; lt = tm - S_BEG[i]
    WIPE = 0.45
    wipe = (not SHORT) and i > 0 and CH_LIST[i - 1]["loc"] != ch["loc"] and lt < WIPE
    if wipe:
        pi = i - 1
        draw_scene(cv, pi, tm - S_BEG[pi], tm, 0.0)
        edge = DW * (1 - eio(lt / WIPE))
        cv.save(); cv.scale(K, K); cv.clipRect(skia.Rect(edge, 0, DW + 10, DH)); cv.scale(1 / K, 1 / K)
        draw_scene(cv, i, lt, tm, WIPE * 0.45)
        cv.restore()
        sh = PR.sheet(hx(0xF8EFE0), "w")
        blit(cv, sh, edge - 10, DH / 2, DH / 1200, 0, 1, 1, 1, (480, 600))
        if CH_LIST[pi]["sid"] is not None:
            pass
        # 이전 조각 자막은 전환 중 사라짐
    else:
        wo = 0.0
        draw_scene(cv, i, lt, tm, wo)
    cv.save(); cv.scale(K, K); draw_tag(cv); draw_caption(cv, i, tm); cv.restore()
    if tm > END - 0.5:
        a = clamp01((tm - (END - 0.5)) / 0.5) if not SHORT else 0.0
        if a > 0:
            p = skia.Paint(); p.setColor(skia.Color(255, 248, 238, int(255 * a))); cv.drawRect(skia.Rect(0, 0, RW, RH), p)

# ───────── 메인 ─────────
def surface_arr(s):
    return s.makeImageSnapshot().toarray(colorType=skia.kRGBA_8888_ColorType, alphaType=skia.kUnpremul_AlphaType)

def finish_arr(s, tm, fno):
    """프레임 배열을 만들고, 조각 fx에 'flashback'(회상·타임카드 되감기)이 있으면 회상 효과를 입힌다(flashfx.py)."""
    arr = surface_arr(s)
    i = chunk_at(tm)
    if "flashback" in CH_LIST[i].get("fx", []):
        import flashfx
        arr = flashfx.apply(arr, tm - S_BEG[i], fno, stamp=flashfx.stamp_of(CH_LIST[i]), lang=LANG, ui=not CH_LIST[i].get("no_cctv_ui", False))
    return arr

def main():
    out = sys.argv[2]; os.makedirs(out, exist_ok=True)
    if len(sys.argv) > 3 and sys.argv[3] == "preview":
        for t in sys.argv[4:]:
            s = skia.Surface(RW, RH); render_frame(s.getCanvas(), float(t))
            from PIL import Image
            Image.fromarray(finish_arr(s, float(t), int(float(t) * FPS))).save(f"{out}/prev_{VARIANT}_{float(t):06.2f}.png")
        print("END", round(END, 2)); return
    if len(sys.argv) > 3 and sys.argv[3] == "info":
        print("END", round(END, 2)); [print(i, c["id"], round(S_BEG[i], 2), round(S_LEN[i], 2)) for i, c in enumerate(CH_LIST)]; return
    # 분할 렌더: part k/n → 프레임 범위
    part, nparts = (int(sys.argv[3]), int(sys.argv[4])) if len(sys.argv) > 4 else (0, 1)
    nfr = int(END * FPS)
    a0, a1 = nfr * part // nparts, nfr * (part + 1) // nparts
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgba", "-s", f"{RW}x{RH}", "-r", str(FPS), "-i", "-",
           "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-pix_fmt", "yuv420p", f"{out}/v_{VARIANT}_{part}.mp4"]
    pr = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    s = skia.Surface(RW, RH); cv = s.getCanvas()
    for f in range(a0, a1):
        render_frame(cv, f / FPS)
        pr.stdin.write(np.ascontiguousarray(finish_arr(s, f / FPS, f)).tobytes())
        if f % 300 == 0: print("frame", f, "/", a1, flush=True)
    pr.stdin.close(); pr.wait(); print("part done", part)

main()
