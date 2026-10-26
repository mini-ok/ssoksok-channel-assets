"""오디오 믹스: 음성 + 효과음(적게, 강약) + 배경음악(덕킹·EQ) → -14 LUFS"""
import sys, os, json, math, wave, subprocess, importlib.util
import numpy as np
from scipy import signal as sg
sys.path.insert(0, "/home/claude/work/sit")
import eps

SR = 44100
BGMDIR = "/home/claude/assets/bgm/"
VAR = sys.argv[1]
LANG, SHORT = VAR.split("_")[0], not VAR.endswith("long")
EPDIR = "/home/claude/work/ep/" + VAR
CH_LIST = eps.L if not SHORT else (eps.SA if VAR.endswith("A") else eps.SB)
MAN = {m["id"]: m for m in json.load(open(EPDIR + "/audio/manifest.json"))}
GAPS = {1: 0.30, 2: 0.18, 3: 0.08, 4: 0.03}
TAILV, LEAD = 0.35, (0.6 if SHORT else 0.5)
S_AUD, S_LEN = [], []
_t = LEAD
for i, c in enumerate(CH_LIST):
    S_AUD.append(_t)
    if c["sid"] is None:
        ln = c["dur"]
    else:
        sp_ = MAN[c["id"]]["dur"] - TAILV
        ln = sp_ + (0.22 if SHORT else GAPS.get(c.get("tempo", 1), 0.2))
    if c.get("mindur"):
        ln = max(ln + TAILV, c["mindur"])
    S_LEN.append(ln)
    _t += ln
END = _t + (0.8 if SHORT else 0.5)
S_BEG = [0.0] + [max(S_AUD[i] - 0.10, S_AUD[i - 1] + 0.05) for i in range(1, len(CH_LIST))]
N = int(END * SR)
IDX = {c["id"]: i for i, c in enumerate(CH_LIST)}


def rd(path):
    w = wave.open(path); sr = w.getframerate()
    x = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float64) / 32768; w.close()
    if sr != SR:
        from math import gcd
        g = gcd(SR, sr); x = sg.resample_poly(x, SR // g, sr // g)
    return x


def mp3(path, dur):
    """mp3 → 모노 44.1k numpy, dur초까지 1초 크로스페이드 반복"""
    p = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-ac", "1", "-ar", str(SR), "-f", "f32le", "-"], capture_output=True)
    x = np.frombuffer(p.stdout, dtype=np.float32).astype(np.float64)
    need = int(dur * SR)
    if len(x) >= need:
        return x[:need]
    xf = int(1.0 * SR)
    out = x.copy()
    while len(out) < need:
        ramp = np.linspace(0, 1, xf)
        tail = out[-xf:] * (1 - ramp) + x[:xf] * ramp
        out = np.concatenate([out[:-xf], tail, x[xf:]])
    return out[:need]


def xfade(a, b, at):
    """at초 지점에서 1초 크로스페이드"""
    k = int(at * SR); xf = int(1.0 * SR)
    out = a.copy()
    ramp = np.linspace(0, 1, xf)
    out[k:k + xf] = a[k:k + xf] * (1 - ramp) + b[k:k + xf] * ramp
    out[k + xf:] = b[k + xf:]
    return out


# ───── 음성 ─────
voice = np.zeros(N)
speech = np.zeros(N, bool)
for i, c in enumerate(CH_LIST):
    if c["sid"] is None: continue
    x = rd(f"{EPDIR}/audio/{c['id']}.wav")
    o = int(S_AUD[i] * SR)
    voice[o:o + len(x)] += x[:max(0, N - o)]
    speech[o:min(N, o + len(x) - int(TAILV * SR))] = True
voice /= (np.abs(voice).max() + 1e-9)
voice *= 0.92

# ───── 효과음(수를 줄여 강약) ─────
def tone(f, d, dec=8, vol=1.0, kind="sine"):
    n = int(SR * d); t = np.arange(n) / SR
    w = np.sin(2 * np.pi * f * t) + (0.25 * np.sin(4 * np.pi * f * t) if kind == "sine" else 0)
    return vol * w * np.exp(-t * dec) * np.minimum(1, t / 0.004)

def pop_(f0=520, f1=980, d=0.13, vol=0.5):
    n = int(SR * d); t = np.arange(n) / SR
    ph = 2 * np.pi * np.cumsum(np.linspace(f0, f1, n)) / SR
    return vol * np.sin(ph) * np.exp(-t * 22) * np.minimum(1, t / 0.003)

def whoosh(d=0.4, vol=0.3):
    n = int(SR * d); nz = np.random.default_rng(3).standard_normal(n)
    b, a = sg.butter(2, [500 / (SR / 2), 3500 / (SR / 2)], btype="band")
    return vol * sg.lfilter(b, a, nz) * np.sin(np.pi * np.linspace(0, 1, n)) ** 2

def siren(d=0.9, vol=0.42):
    n = int(SR * d); t = np.arange(n) / SR
    f = 620 + 180 * np.sin(2 * np.pi * 2.6 * t)
    ph = 2 * np.pi * np.cumsum(f) / SR
    env = np.minimum(1, t / 0.02) * np.minimum(1, (d - t) / 0.15)
    return vol * np.sin(ph) * env

def thud(vol=0.65):
    n = int(SR * 0.3); t = np.arange(n) / SR
    return vol * np.sin(2 * np.pi * (120 - 70 * t) * t) * np.exp(-t * 13)

def ding(f=1040, d=0.7, vol=0.34):
    return vol * (tone(f, d, 5) + 0.5 * tone(f * 1.5, d, 6))

def sparkle(vol=0.2):
    out = np.zeros(int(SR * 0.8))
    for k, f in enumerate((1318, 1568, 1976, 2349)):
        s = tone(f, 0.32, 9, vol=vol); o = int(SR * 0.06 * k); out[o:o + len(s)] += s[:len(out) - o]
    return out

ev = []
def at(cid, off, s):
    if cid in IDX: ev.append((S_BEG[IDX[cid]] + off, s))

prev_loc = None
for i, c in enumerate(CH_LIST):
    if not SHORT and prev_loc is not None and c["loc"] != prev_loc:
        ev.append((S_BEG[i], whoosh(0.45, 0.26)))
    prev_loc = c["loc"]

if not SHORT:
    for cid in ("a6", "c3", "c9", "d9"):
        at(cid, 0.02, siren(1.0, 0.40))
    at("a6", 0.9, thud(0.5))
    at("a8", 0.1, pop_(700, 300, 0.18, 0.35))
    at("c3", 0.95, thud(0.75))
    at("c4", 0.1, pop_(300, 180, 0.3, 0.4))
    at("c8", 0.1, pop_(420, 900, 0.14, 0.4))
    at("d0", 0.25, pop_(560, 220, 0.3, 0.32))
    at("d4", 0.3, sparkle(0.16))
    at("d6", 0.2, ding(1180, 0.8, 0.3))
    at("d7", 0.15, ding(880, 0.7, 0.26))
    at("d10", 0.05, thud(0.8))
    at("d11", 0.45, pop_(600, 1100, 0.14, 0.42))
    at("d12", 0.45, ding(1320, 0.7, 0.3))
    at("e1", 0.12, sparkle(0.14))
else:
    first = CH_LIST[0]["id"]; last = CH_LIST[-1]["id"]
    at(first, 0.05, pop_(620, 1150, 0.14, 0.42))
    mid = CH_LIST[2]["id"]
    at(mid, 0.12, ding(1040, 0.6, 0.3))
    at(CH_LIST[-2]["id"], 0.1, pop_(420, 880, 0.14, 0.34))
    at(last, 0.15, sparkle(0.17))

fx = np.zeros(N)
for t0, s in ev:
    o = int(t0 * SR)
    if o >= N: continue
    fx[o:o + len(s)] += s[:N - o]

# ───── 배경음악 ─────
if SHORT:
    tracks = [("nimble_motifs.mp3" if VAR.endswith("A") else "buoyant_kitchen_groove.mp3", 0.0)]
else:
    c7 = S_BEG[IDX["c7"]] if "c7" in IDX else END / 2
    d0 = S_BEG[IDX["d0"]] if "d0" in IDX else END * 0.75
    tracks = [("첫 만남 허밍송 (1).mp3", 0.0), ("rising_octaves.mp3", c7 - 0.5), ("la_silla_vacia.mp3", d0 - 0.5)]
music = mp3(BGMDIR + tracks[0][0], END)
for name, at_s in tracks[1:]:
    music = xfade(music, mp3(BGMDIR + name, END), at_s)
# 말소리 대역 EQ 컷 (1~4kHz, 약 -5dB)
b, a = sg.iirpeak(2000 / (SR / 2), 1.1)
w, h = sg.freqz(b, a, worN=8)
bq = sg.iirfilter(2, [1000 / (SR / 2), 4000 / (SR / 2)], btype="bandpass", ftype="butter", output="sos")
band = sg.sosfilt(bq, music)
music = music - band * (1 - 10 ** (-5 / 20))
# 덕킹: 말하는 동안 -14dB(롱폼) / -12dB(숏폼), 부드럽게
env = np.zeros(N)
hop = 441
sp = speech.astype(float)
k = np.ones(int(0.05 * SR)) / int(0.05 * SR)
sm = np.convolve(sp, k, mode="same")
sm = (sm > 0.02).astype(float)
# 어택 60ms / 릴리즈 350ms
duck_db = 14.0 if not SHORT else 12.0
g = np.ones(N)
target = 10 ** (-duck_db / 20)
cur = 1.0
atk = math.exp(-1 / (0.06 * SR)); rel = math.exp(-1 / (0.35 * SR))
step = 64
gs = np.ones(N // step + 2)
for n in range(len(gs)):
    want = target if sm[min(N - 1, n * step)] > 0.5 else 1.0
    co = atk if want < cur else rel
    cur = want + (cur - want) * (co ** step)
    gs[n] = cur
g = np.interp(np.arange(N), np.arange(len(gs)) * step, gs)
music = music * g
# 음악 레벨: 말하는 구간에서 음성보다 14dB 이상 아래
def rms(x, m):
    v = x[m]
    return math.sqrt((v ** 2).mean() + 1e-12) if m.any() else 1e-6
vr, mr = rms(voice, speech), rms(music, speech)
want_db = -15.0 if not SHORT else -14.0
scale = (vr * 10 ** (want_db / 20)) / (mr + 1e-9)
music = music * scale
# 페이드 인/아웃
fi, fo = int(0.5 * SR), int(1.0 * SR)
music[:fi] *= np.linspace(0, 1, fi); music[-fo:] *= np.linspace(1, 0, fo)
# 롱폼 엔딩 카드: 효과음 없음(이미 e1에 sparkle 하나만) → 음악만 작게
if not SHORT and "e1" in IDX:
    o = int(S_BEG[IDX["e1"]] * SR)
    fx[o + int(0.9 * SR):] = 0
    music[o:] *= 0.85

mix = voice + 0.55 * fx + music
mix = np.clip(mix / max(1.0, np.abs(mix).max() / 0.98), -1, 1)
out = EPDIR + "/mix.wav"
w = wave.open(out, "wb"); w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
w.writeframes((mix * 32767).astype(np.int16).tobytes()); w.close()

# 검수용 스템
for nm, arr in (("voice", voice), ("music", music)):
    p = EPDIR + f"/stem_{nm}.wav"
    ww = wave.open(p, "wb"); ww.setnchannels(1); ww.setsampwidth(2); ww.setframerate(SR)
    ww.writeframes((np.clip(arr, -1, 1) * 32767).astype(np.int16).tobytes()); ww.close()
print(json.dumps(dict(variant=VAR, end=round(END, 2), tracks=[t[0] for t in tracks],
                      voice_music_db=round(20 * math.log10(rms(voice, speech) / (rms(music, speech) + 1e-12)), 1),
                      speech_ratio=round(float(speech.mean()), 2)), ensure_ascii=False))
