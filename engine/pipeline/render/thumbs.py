"""썸네일 6장: 롱폼 1280x720 (ko/en) + 숏폼 1080x1920 (A/B ko/en)"""
import sys, os
os.environ["KSC"] = "1.0"
sys.path.insert(0, "/home/claude/work/sit")
from core import *
import props as PR
from PIL import Image

OUT = "/home/claude/work/out"
os.makedirs(OUT, exist_ok=True)
COLS = dict(coral=CORALC, mint=MINTC, sky=SKYC, butter=BUTTER, lav=LAV, cream=CREAMC)

def char_on(img, Wd, Hh, name, mood, x, y, size):
    return puff_char(img, char_fn(name, mood), x, y, size, seed=7)

def chip_on(img, Wd, Hh, s, cx, cy, size, face, col, rot=0, tcol=None):
    img, w, h = chip(img, Wd, Hh, s, cx, cy, size, face, col, hash(s) % 83, rot, 40, 24, (TXT if tcol is None else tcol), 30)
    return img, w, h

def star_num(img, Wd, Hh, s, cx, cy, R, size, face):
    img = puff(img, star(Wd, Hh, cx, cy, R, -90, 0.62, 14), hx(0xF6CB45), 5, soft=12, shadow=(7, 10), sh_blur=10, sh_k=0.3)
    img, _ = put_text(img, Wd, Hh, s, cx, cy + size * 0.34, size, face, TXT, "c", shadow=False)
    return img

def tag_chip(img, Wd, Hh, s, x, y, size=36):
    img, w, h = chip(img, Wd, Hh, s, x, y, size, "jua" if any("가" <= c <= "힣" for c in s) else "geist", CREAMC, 3, -2, 26, 16, TXT, 20)
    return img

def long_thumb(lang):
    Wd, Hh = 1280, 720
    img = bg(Wd, Hh, hx(0xFBEADB), hx(0xF2DAE2), 21)
    for (x, y, r, c) in ((1180, 90, 46, 0xF4C3B8), (90, 640, 40, 0xCDEBDD), (640, 60, 30, 0xF4C3B8)):
        img = puff(img, circ(Wd, Hh, x, y, r), hx(c), int(x), soft=8, shadow=(4, 6), sh_blur=6, sh_k=0.2)
    fl = np.zeros((Hh, Wd), np.float32); fl[625:] = 1
    img = puff(img, fl, hx(0xE2CDB5), 22, soft=8, shadow=(0, -5), sh_blur=8, sh_k=0.15, depth=0.4)
    if lang == "ko":
        l1, l2, sub, tag = "야식 후", "3시간!", "먹고 바로 눕지 않기", "몸속 주식회사"
        s1, s2, f1, f2 = 150, 170, "black", "black"
    else:
        l1, l2, sub, tag = "ATE LATE?", "3 HOURS", "Don't lie down right after", "Tiny Body Co."
        s1, s2, f1, f2 = 120, 140, "geist", "geist"
    img, w1, h1 = chip_on(img, Wd, Hh, l1, 70 + (tw(l1, s1, f1) + 80) / 2, 250, s1, f1, COLS["butter"], -3)
    img, w2, h2 = chip_on(img, Wd, Hh, l2, 70 + (tw(l2, s2, f2) + 80) / 2, 250 + h1 * 0.62 + 92, s2, f2, COLS["coral"], 2, hx(0xFFF8EE))
    sy = 250 + h1 * 0.62 + 92 + h2 * 0.5 + 66
    img, _, _ = chip_on(img, Wd, Hh, sub, 70 + (tw(sub, 42 if lang == "ko" else 36, "jua" if lang == "ko" else "geist") + 80) / 2, sy,
                        42 if lang == "ko" else 36, "jua" if lang == "ko" else "geist", CREAMC, -1)
    # 오른쪽 캐릭터 + 소품
    img = char_on(img, Wd, Hh, "stomach", "wow", 960, 430, 650)
    fs = PR.bucket(lang) if lang == "ko" else PR.pizza()
    a = fs["arr"].astype(np.float32) / 255
    rgb, al = a[..., :3], a[..., 3]
    sc = 0.5
    ph, pw = int(rgb.shape[0] * sc), int(rgb.shape[1] * sc)
    rgb = np.stack([np.asarray(Image.fromarray(rgb[..., i], mode="F").resize((pw, ph), Image.LANCZOS)) for i in range(3)], 2)
    al = np.asarray(Image.fromarray(al, mode="F").resize((pw, ph), Image.LANCZOS))
    px, py = 1165, 590
    x0, y0 = int(px - pw / 2), int(py - ph / 2)
    sl = (slice(max(0, y0), min(Hh, y0 + ph)), slice(max(0, x0), min(Wd, x0 + pw)))
    sa = (slice(max(0, -y0), max(0, -y0) + (sl[0].stop - sl[0].start)), slice(max(0, -x0), max(0, -x0) + (sl[1].stop - sl[1].start)))
    aa = al[sa][..., None]
    img[sl] = img[sl] * (1 - aa) + rgb[sa] * aa
    img = tag_chip(img, Wd, Hh, tag, 70 + tw(tag, 36, "jua" if lang == "ko" else "geist") / 2 + 40, 78)
    return img

def short_thumb(lang, which):
    Wd, Hh = 1080, 1920
    pal = (0xFBE9DC, 0xF3D9E2, 23) if which == "A" else (0xE6F0F2, 0xEEE2F2, 24)
    img = bg(Wd, Hh, hx(pal[0]), hx(pal[1]), pal[2])
    fl = np.zeros((Hh, Wd), np.float32); fl[1500:] = 1
    img = puff(img, fl, hx(0xE2CDB5), 25, soft=8, shadow=(0, -5), sh_blur=8, sh_k=0.15, depth=0.4)
    for (x, y, r, c) in ((930, 300, 48, 0xF4C3B8), (120, 1420, 42, 0xCDEBDD)):
        img = puff(img, circ(Wd, Hh, x, y, r), hx(c), int(x), soft=8, shadow=(4, 6), sh_blur=6, sh_k=0.2)
    if which == "A":
        if lang == "ko":
            l1, l2, sub, num, unit = "야식 후", "바로 눕기?", "식사 후 3시간은 눕지 않기", "3", "시간"
            s1, s2, f = 150, 150, "black"
        else:
            l1, l2, sub, num, unit = "SNACK, THEN", "LIE DOWN?", "Stay upright for 3 hours", "3", "HRS"
            s1, s2, f = 110, 118, "geist"
        cname, cmood, c1, c2 = "brain", "wow", COLS["butter"], COLS["coral"]
    else:
        if lang == "ko":
            l1, l2, sub, num, unit = "야식 먹어야", "이렇게!", "자기 3시간 전엔 끝내기", "3", "시간"
            s1, s2, f = 130, 160, "black"
        else:
            l1, l2, sub, num, unit = "MUST EAT LATE?", "DO THIS", "Finish 3 hours before bed", "3", "HRS"
            s1, s2, f = 84, 136, "geist"
        cname, cmood, c1, c2 = "stomach", "worry", COLS["mint"], COLS["coral"]
    img, w1, h1 = chip_on(img, Wd, Hh, l1, Wd / 2 - 20, 420, s1, f, c1, -3)
    img, w2, h2 = chip_on(img, Wd, Hh, l2, Wd / 2 - 10, 420 + h1 * 0.6 + 100, s2, f, c2, 2, hx(0xFFF8EE))
    ty = 420 + h1 * 0.6 + 100 + h2 * 0.5 + 72
    sf = "jua" if lang == "ko" else "geist"
    img, _, _ = chip_on(img, Wd, Hh, sub, Wd / 2 - 30, ty, 54 if lang == "ko" else 44, sf, CREAMC, -1)
    img = star_num(img, Wd, Hh, num + unit, 240, 1110, 230, 120 if lang == "ko" else 104, "black" if lang == "ko" else "geist")
    img = char_on(img, Wd, Hh, cname, cmood, 715, 1250, 900)
    tag = "쏙쏙 건강백과" if lang == "ko" else "Tiny Body Co."
    img = tag_chip(img, Wd, Hh, tag, 90 + tw(tag, 38, sf) / 2 + 40, 250, 38)
    return img

def save(img, path):
    Image.fromarray((np.clip(img, 0, 1) * 255).astype(np.uint8)).save(path)

if __name__ == "__main__":
    import multiprocessing as mp
    jobs = [("thumb_yasik_long_ko.png", lambda: long_thumb("ko")), ("thumb_yasik_long_en.png", lambda: long_thumb("en")),
            ("thumb_yasik_short_A_ko.png", lambda: short_thumb("ko", "A")), ("thumb_yasik_short_B_ko.png", lambda: short_thumb("ko", "B")),
            ("thumb_yasik_short_A_en.png", lambda: short_thumb("en", "A")), ("thumb_yasik_short_B_en.png", lambda: short_thumb("en", "B"))]
    def run(i):
        n, f = jobs[i]; save(f(), OUT + "/" + n); return n
    with mp.Pool(3) as p:
        for n in p.imap_unordered(run, range(len(jobs))): print(n, flush=True)
