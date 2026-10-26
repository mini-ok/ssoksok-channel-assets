import sys; sys.path.insert(0, '/home/claude/work/sit')
from core import *
from core import _resize
W, H = 1920, 1080

def save_bg(name, img):
    if abs(K - 1.0) < 1e-6:
        sm = img
    else:
        ow, oh = (int(1080 * K), int(1920 * K)) if img.shape[0] > img.shape[1] else (int(1920 * K), int(1080 * K))
        sm = np.stack([_resize(img[..., i], ow, oh) for i in range(3)], 2)
    np.save(CACHE + "bg_" + name + ".npy", (np.clip(sm, 0, 1) * 255 + 0.5).astype(np.uint8))

def base(top, bot, seed, floor_y=840, floor_col=FLOOR):
    img = bg(W, H, top, bot, seed)
    fl = np.zeros((H, W), np.float32); fl[floor_y:] = 1
    img = P_(img, fl, floor_col, seed + 3, soft=10, sh=(0, -6), blur=10, k=0.18, depth=0.4)
    # 걸레받이 띠
    bd = np.zeros((H, W), np.float32); bd[floor_y - 16:floor_y + 4] = 1
    img = P_(img, bd, hx(0xF6EEE2), seed + 4, soft=4, sh=(0, 2), blur=3, k=0.1, depth=0.4)
    return img

def window(img, l, t, r, b, night, seed):
    img = P_(img, rr(W, H, l - 18, t - 18, r + 18, b + 18, 30), hx(0xFBF4E6), seed, soft=10)
    sky = hx(0x7C86B8) if night else hx(0xBFE0F2)
    sky2 = hx(0x5F6AA0) if night else hx(0xDDEFF8)
    gl = rr(W, H, l, t, r, b, 22)
    yy = np.linspace(0, 1, H)[:, None, None]
    col = (sky[None, None, :] * (1 - yy) + sky2[None, None, :] * yy)
    img = img * (1 - gl[..., None]) + col * gl[..., None]
    if night:
        img = P_(img, circ(W, H, l + (r - l) * 0.72, t + (b - t) * 0.3, 54), hx(0xFBEFB8), seed + 1, soft=12, sh=(0, 0), blur=1, k=0.0, depth=0.6)
        for (fx, fy, s) in ((0.2, 0.25, 9), (0.4, 0.55, 7), (0.55, 0.2, 8), (0.3, 0.75, 6)):
            img = P_(img, star(W, H, l + (r - l) * fx, t + (b - t) * fy, s * 1.6, -90, 0.5, 2), hx(0xFFF3B0), seed + 7, soft=3, sh=(0, 0), blur=1, k=0.0, depth=0.4)
    else:
        img = P_(img, cloud(W, H, l + (r - l) * 0.3, t + (b - t) * 0.35, 1.1), hx(0xFFFFFF), seed + 2, soft=10, sh=(3, 5), blur=5, k=0.12)
        img = P_(img, circ(W, H, l + (r - l) * 0.78, t + (b - t) * 0.28, 44), hx(0xFFE79A), seed + 1, soft=10, sh=(0, 0), blur=1, k=0.0, depth=0.6)
    mid = np.zeros((H, W), np.float32); mid[t:b, int((l + r) / 2) - 7:int((l + r) / 2) + 7] = 1
    img = P_(img, mid, hx(0xFBF4E6), seed + 5, soft=4, sh=(2, 2), blur=3, k=0.15, depth=0.5)
    return img

def clock_static(img, cx, cy, R, seed):
    sp = clock_sprite(R)
    return paste(img, sp, cx, cy)

def paste(img, sp, cx, cy):
    """스프라이트(설계 해상도로 재조합 불가) 대신 직접 그린 함수를 쓰기 위한 자리표시 — 배경에서는 사용 안 함"""
    return img

def clock_bg(img, cx, cy, R, seed):
    img = P_(img, circ(W, H, cx, cy, R + 16), hx(0xEE9A8E), seed, soft=10)
    img = P_(img, circ(W, H, cx, cy, R - 4), hx(0xFBF7EC), seed + 1, soft=8, sh=(2, 3), blur=3, k=0.15, depth=0.5)
    for i in range(12):
        if i % 3 == 0: continue
        a = math.radians(i * 30 - 90)
        img = P_(img, circ(W, H, cx + math.cos(a) * (R - 22), cy + math.sin(a) * (R - 22), R * 0.03), hx(0x7C87A8), seed + 2, soft=3, sh=(1, 1), blur=2, k=0.15, depth=0.4)
    for i, s in ((0, "12"), (3, "3"), (6, "6"), (9, "9")):
        a = math.radians(i * 30 - 90); sz = R * 0.27
        img, _ = put_text(img, W, H, s, cx + math.cos(a) * (R - 40), cy + math.sin(a) * (R - 40) + sz * 0.34, sz, "do", hx(0x4A5470), "c", shadow=False)
    return img

def deco_cells(img, seed, items):
    for (x, y, r, col) in items:
        img = P_(img, circ(W, H, x, y, r), hx(col), seed + int(x), soft=max(5, r * .2), sh=(4, 6), blur=6, k=0.18, depth=0.8)
        img = P_(img, circ(W, H, x + r * .16, y - r * .1, r * .36), hx(0xF1A99E), seed + int(y), soft=4, sh=(2, 3), blur=3, k=0.2)
    return img

def office(night=True, lang="ko"):
    img = base(hx(0xF1E5DA) if night else hx(0xF8EEDC), hx(0xE9DCE6) if night else hx(0xF2E3D0), 1, 800)
    img = window(img, 140, 140, 640, 520, night, 20)
    img = clock_bg(img, 960, 230, 110, 40)
    # 책상 + 모니터 (오른쪽 구석, 캐릭터를 가리지 않게)
    img = P_(img, rr(W, H, 1440, 650, 1800, 690, 14), WOOD, 50, soft=8)
    img = P_(img, rr(W, H, 1470, 690, 1500, 800, 8), WOOD2, 51, soft=6)
    img = P_(img, rr(W, H, 1740, 690, 1770, 800, 8), WOOD2, 52, soft=6)
    img = P_(img, rr(W, H, 1500, 470, 1730, 636, 18), hx(0x8C93A8), 53, soft=8)
    img = P_(img, rr(W, H, 1516, 486, 1714, 616, 12), hx(0xBFE6D6) if night else hx(0xCDE9F6), 54, soft=5, sh=(1, 2), blur=2, k=0.12, depth=0.4)
    img = P_(img, rr(W, H, 1595, 636, 1635, 654, 4), hx(0x8C93A8), 55, soft=3)
    for i, w in enumerate((130, 100, 150)):
        m = M(W, H); m.cv.drawLine(1540, 520 + i * 30, 1540 + w, 520 + i * 30, paint(9)); img = over(img, m.arr(), hx(0xFFFFFF) * 0.85)
    img = P_(img, rr(W, H, 800, 700, 890, 800, 14), hx(0xE9776E), 60, soft=7)
    for dx, dy, rr_ in ((-34, -50, 38), (6, -78, 44), (40, -40, 36)):
        img = P_(img, circ(W, H, 845 + dx, 700 + dy, rr_), hx(0x8FCFB4), 61 + dx, soft=9, sh=(3, 5), blur=4, k=0.2)
    img = deco_cells(img, 70, ((1100, 620, 30, 0xF4C3B8), (330, 640, 24, 0xF4C3B8)))
    return img

def meeting(lang="ko"):
    img = base(hx(0xE8F0EA), hx(0xDCE6EE), 2, 806)
    img = P_(img, rr(W, H, 330, 80, 1590, 540, 28), hx(0xC9A57A), 11, soft=9)
    img = P_(img, rr(W, H, 354, 104, 1566, 516, 18), hx(0xFFFDF6), 12, soft=5, sh=(1, 2), blur=2, k=0.12, depth=0.4)
    img = P_(img, rr(W, H, 780, 530, 1140, 556, 8), hx(0xB9A27C), 13, soft=4)
    img = P_(img, rr(W, H, 360, 690, 1560, 744, 24), WOOD, 14, soft=9)
    img = P_(img, rr(W, H, 420, 744, 460, 806, 8), WOOD2, 15, soft=5); img = P_(img, rr(W, H, 1460, 744, 1500, 806, 8), WOOD2, 16, soft=5)
    img = clock_bg(img, 1760, 200, 80, 17)
    img = deco_cells(img, 70, ((220, 220, 34, 0xF4C3B8), (1740, 560, 28, 0xF4C3B8)))
    return img

def gate(lang="ko"):
    img = base(hx(0xF6E9DC), hx(0xEBDDE0), 3, 806)
    img = P_(img, rr(W, H, 690, 90, 1230, 820, 26), hx(0xFBF4E6), 21, soft=10)
    img = P_(img, rr(W, H, 722, 122, 1198, 820, 18), hx(0xBFD7E8), 22, soft=8, sh=(2, 4), blur=4, k=0.18)
    img = P_(img, rr(W, H, 944, 122, 976, 820, 4), hx(0xFBF4E6), 23, soft=4)
    for x in (900, 1020):
        img = P_(img, circ(W, H, x, 470, 14), GOLD, 24, soft=5, sh=(2, 3), blur=3, k=0.2)
    img = P_(img, rr(W, H, 760, 826, 1160, 876, 20), hx(0xB6D8C4), 25, soft=7)
    s = "정문" if lang == "ko" else "ENTRANCE"
    wsz = tw(s, 46, "jua") + 90
    img = P_(img, rr(W, H, 960 - wsz / 2, 26, 960 + wsz / 2, 88, 26), hx(0xF2D36B), 26, soft=7)
    img, _ = put_text(img, W, H, s, 960, 72, 44, "jua", NAVYC, "c", shadow=False)
    img = deco_cells(img, 70, ((300, 300, 40, 0xF4C3B8), (1620, 560, 34, 0xF4C3B8)))
    return img

def factory(lang="ko"):
    img = base(hx(0xF7E0D2), hx(0xF1CFC4), 4, 740, hx(0xD9BFA6))
    for (y, c) in ((150, 0xE9B7A9), (220, 0xE9B7A9)):
        img = P_(img, rr(W, H, 0, y, W, y + 34, 17), hx(c), y, soft=8)
    for x in (300, 900, 1500):
        img = P_(img, rr(W, H, x, 150, x + 40, 300, 10), hx(0xDCA595), x, soft=6)
    for (cx, cy, r) in ((1560, 440, 100), (1700, 540, 62)):
        gm = M(W, H); gm.cv.drawPath(gear_path(cx, cy, 10, r), paint()); g = gm.arr()
        hole = circ(W, H, cx, cy, r * 0.35)
        img = P_(img, np.clip(g - hole, 0, 1), hx(0xF0B9A8), cx, soft=8)
    s = "소화1팀 위장 공장" if lang == "ko" else "Digestion Team 1 - Stomach Line"
    wsz = tw(s, 42, "jua") + 100
    img = P_(img, rr(W, H, 960 - wsz / 2, 40, 960 + wsz / 2, 110, 28), hx(0xF2D36B), 30, soft=7)
    img, _ = put_text(img, W, H, s, 960, 88, 40, "jua", NAVYC, "c", shadow=False)
    img = P_(img, rr(W, H, 100, 806, 1820, 886, 40), hx(0x7C87A8), 31, soft=12)
    img = P_(img, rr(W, H, 128, 820, 1792, 856, 18), hx(0x9AA3C0), 32, soft=5, sh=(1, 2), blur=2, k=0.1, depth=0.4)
    for x in range(180, 1760, 150):
        img = P_(img, circ(W, H, x, 871, 12), hx(0x5D6788), 33 + x, soft=4, sh=(1, 2), blur=2, k=0.15)
    return img

def night(lang="ko"):
    img = base(hx(0xC5CBEA), hx(0xB9BDDF), 5, 806, hx(0xA9AACB))
    img = window(img, 1220, 140, 1700, 500, True, 40)
    img = P_(img, rr(W, H, 150, 270, 420, 806, 24), hx(0xDDE5F3), 41, soft=10)
    img = P_(img, rr(W, H, 180, 310, 390, 590, 14), hx(0xF7FBFF), 42, soft=5, sh=(1, 2), blur=2, k=0.12, depth=0.4)
    for i, c in enumerate((0xE9776E, 0xF2BE3C, 0x8FCFB4, 0x9CC6E6)):
        img = P_(img, rr(W, H, 200 + (i % 2) * 96, 330 + (i // 2) * 120, 266 + (i % 2) * 96, 400 + (i // 2) * 120, 12), hx(c), 43 + i, soft=5, sh=(2, 3), blur=3, k=0.2)
    img = P_(img, rr(W, H, 200, 640, 370, 680, 10), hx(0x9AA3B8), 48, soft=5)
    img = P_(img, rr(W, H, 760, 696, 1160, 746, 22), hx(0xCBB097), 44, soft=8)
    img = P_(img, rr(W, H, 800, 746, 830, 806, 8), hx(0xB69A80), 45, soft=5); img = P_(img, rr(W, H, 1090, 746, 1120, 806, 8), hx(0xB69A80), 46, soft=5)
    img = clock_bg(img, 960, 220, 100, 47)
    return img

def endbg(lang="ko"):
    img = bg(W, H, hx(0xF3E6D8), hx(0xE6E0EF), 6)
    img = deco_cells(img, 80, ((180, 180, 56, 0xF4C3B8), (1760, 880, 70, 0xF4C3B8), (1700, 160, 40, 0xCDEBDD), (150, 900, 44, 0xCDEBDD), (960, 1000, 30, 0xF4C3B8)))
    return img

def short_bg(top, bot, seed, cells, floor=1380):
    """세로 1080x1920 배경"""
    Wv, Hv = 1080, 1920
    img = bg(Wv, Hv, hx(top), hx(bot), seed)
    fl = np.zeros((Hv, Wv), np.float32); fl[floor:] = 1
    img = puff(img, fl, FLOOR, seed + 3, soft=10, shadow=(0, -6), sh_blur=10, sh_k=0.18, depth=0.4)
    for (x, y, r, col) in cells:
        img = puff(img, circ(Wv, Hv, x, y, r), hx(col), seed + int(x), soft=max(5, r * .2), shadow=(4, 6), sh_blur=6, sh_k=0.18, depth=0.8)
        img = puff(img, circ(Wv, Hv, x + r * .16, y - r * .1, r * .36), hx(0xF1A99E), seed + int(y), soft=4, shadow=(2, 3), sh_blur=3, sh_k=0.2)
    return img

def short_bg2(top, bot, seed, cells, floor=1380):
    return short_bg(top, bot, seed, cells, floor)

def build_all():
    import multiprocessing as mp
    jobs = [("s_a", lambda: short_bg(0xFBE9DC, 0xF3D9E2, 11, ((140, 170, 56, 0xF4C3B8), (940, 880, 44, 0xCDEBDD), (900, 1250, 60, 0xF4C3B8), (150, 1180, 40, 0xCDEBDD)))),
            ("s_b", lambda: short_bg(0xE6F0F2, 0xEEE2F2, 12, ((920, 160, 50, 0xF4C3B8), (130, 900, 46, 0xF4C3B8), (950, 1230, 52, 0xCDEBDD), (140, 1250, 38, 0xF4C3B8)))),
            ("office_night", lambda: office(True)), ("office_day", lambda: office(False)), ("meeting_ko", lambda: meeting("ko")), ("meeting_en", lambda: meeting("en")),
            ("gate_ko", lambda: gate("ko")), ("gate_en", lambda: gate("en")), ("factory_ko", lambda: factory("ko")), ("factory_en", lambda: factory("en")),
            ("night_ko", lambda: night("ko")), ("end", lambda: endbg())]
    return jobs

def run(i):
    jobs = build_all(); name, fn = jobs[i]
    save_bg(name, fn()); return name

if __name__ == "__main__":
    import multiprocessing as mp, time
    t = time.time()
    with mp.Pool(4) as p:
        for n in p.imap_unordered(run, range(len(build_all()))): print(n, round(time.time() - t, 1), flush=True)
