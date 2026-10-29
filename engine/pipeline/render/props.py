import sys; sys.path.insert(0, '/home/claude/work/sit')
from core import *
from core import _resize
W, H = 1920, 1080

def hands_sprite(kind):
    """시계 바늘: 중심(원점)에서 위쪽(12시)을 향함. 캔버스 중심 = 시계 중심"""
    N = 300
    def fn(img):
        L, wd = (62, 12) if kind == "hr" else (92, 8)
        m = M(N, N); m.cv.drawLine(N / 2, N / 2, N / 2, N / 2 - L, paint(wd))
        img = P_(img, m.arr(), hx(0x4A5470), 3, soft=3, sh=(2, 3), blur=3, k=0.2, depth=0.4)
        return P_(img, circ(N, N, N / 2, N / 2, 11), hx(0x4A5470), 4, soft=3, sh=(2, 2), blur=2, k=0.2, depth=0.4)
    return sprite("hand_" + kind, N, N, fn)

def clock_sprite(R=120, key="clock", num=True):
    N = int(R * 2 + 120); c = N / 2
    def fn(img):
        img = P_(img, circ(N, N, c, c, R + 16), hx(0xEE9A8E), 1, soft=10)
        img = P_(img, circ(N, N, c, c, R - 4), hx(0xFBF7EC), 2, soft=8, sh=(2, 3), blur=3, k=0.15, depth=0.5)
        for i in range(12):
            if i % 3 == 0: continue
            a = math.radians(i * 30 - 90)
            img = P_(img, circ(N, N, c + math.cos(a) * (R - 22), c + math.sin(a) * (R - 22), R * 0.03), hx(0x7C87A8), 5, soft=3, sh=(1, 1), blur=2, k=0.15, depth=0.4)
        for i, s in ((0, "12"), (3, "3"), (6, "6"), (9, "9")):
            a = math.radians(i * 30 - 90); sz = R * 0.27
            img, _ = put_text(img, N, N, s, c + math.cos(a) * (R - 40), c + math.sin(a) * (R - 40) + sz * 0.34, sz, "do", hx(0x4A5470), "c", shadow=False)
        return img
    return sprite(f"{key}{R}", N, N, fn)

def lamp(on):
    N = 260
    def fn(img):
        col = hx(0xFF5A4E) if on else hx(0xC98A86)
        img = P_(img, rr(N, N, 60, 190, 200, 230, 16), hx(0x8C93A8), 1, soft=6)
        dome = M(N, N); dome.cv.drawOval(skia.Rect(65, 70, 195, 215), paint())
        d = dome.arr(); d[:70] = 0; 
        m = M(N, N); p = skia.Path(); p.moveTo(70, 200); p.quadTo(70, 70, 130, 70); p.quadTo(190, 70, 190, 200); p.close(); m.cv.drawPath(p, paint())
        img = P_(img, m.arr(), col, 2, soft=12)
        img = P_(img, circ(N, N, 105, 120, 12), hx(0xFFD9D4) if on else hx(0xE5C9C6), 3, soft=3, sh=(1, 1), blur=2, k=0.1, depth=0.4)
        return img
    return sprite("lamp_on" if on else "lamp_off", N, N, fn)

def halo():
    N = 420
    def fn(img):
        yy, xx = np.mgrid[0:N, 0:N].astype(np.float32)
        d = np.hypot(xx - N / 2, yy - N / 2) / (N / 2)
        a = np.clip(1 - d, 0, 1) ** 1.6 * 0.55
        return img * (1 - a[..., None]) + hx(0xFF6A5E)[None, None, :] * a[..., None]
    return sprite("halo", N, N, fn)

def bucket(lang):
    N = 380
    def fn(img):
        p = skia.Path(); p.moveTo(90, 150); p.lineTo(290, 150); p.lineTo(260, 330); p.lineTo(120, 330); p.close()
        m = M(N, N); m.cv.drawPath(p, paint())
        img = P_(img, m.arr(), hx(0xFFF3EA), 1, soft=10)
        for k in range(3):
            x0 = 118 + k * 62
            q = skia.Path(); q.moveTo(x0, 150); q.lineTo(x0 + 28, 150); q.lineTo(x0 + 22 - k * 3, 330); q.lineTo(x0 - 4 + k * 0, 330); q.close()
            mm = M(N, N); mm.cv.drawPath(q, paint()); mm.cv.save()
            img = P_(img, mm.arr() * m.arr(), RED, 2 + k, soft=5, sh=(1, 2), blur=3, k=0.12, depth=0.5)
        for (cx, cy, r, c) in ((140, 130, 46, 0xE0A04C), (210, 112, 52, 0xD8923F), (265, 138, 42, 0xE5AB5A), (190, 150, 40, 0xCF8736)):
            img = P_(img, circ(N, N, cx, cy, r), hx(c), cx, soft=10, sh=(3, 5), blur=5, k=0.25)
        return img
    return sprite("bucket", N, N, fn)

def pizza():
    N = 340
    def fn(img):
        p = skia.Path(); p.moveTo(60, 100); p.cubicTo(150, 40, 250, 50, 290, 100); p.lineTo(176, 300); p.close()
        m = M(N, N); m.cv.drawPath(p, paint())
        img = P_(img, m.arr(), hx(0xF2C879), 1, soft=9)
        crust = M(N, N); p2 = skia.Path(); p2.moveTo(60, 100); p2.cubicTo(150, 40, 250, 50, 290, 100); crust.cv.drawPath(p2, paint(30))
        img = P_(img, crust.arr(), hx(0xDDA050), 2, soft=7, sh=(2, 3), blur=3, k=0.2)
        for (x, y, r) in ((150, 130, 24), (220, 135, 22), (180, 195, 22), (180, 118, 0)):
            if r: img = P_(img, circ(N, N, x, y, r), hx(0xD5584C), x, soft=6, sh=(2, 3), blur=3, k=0.22)
        return img
    return sprite("pizza", N, N, fn)

def food2a(lang):   # 떡볶이(ko) / 버팔로 윙(en)
    N = 360
    def fn(img):
        if lang == "ko":
            img = P_(img, circ(N, N, 180, 190, 130) * (np.mgrid[0:N, 0:N][0] > 150), hx(0xFFF3EA), 1, soft=10)
            img = P_(img, rr(N, N, 56, 150, 304, 200, 20), hx(0xFFF3EA), 2, soft=8)
            img = P_(img, rr(N, N, 74, 150, 286, 188, 18), hx(0xE9674E), 3, soft=6, sh=(1, 2), blur=3, k=0.12)
            for (x, y, rot) in ((110, 160, 20), (170, 154, -10), (230, 162, 15), (140, 175, -20), (210, 178, 8)):
                img = P_(img, rr(N, N, x - 24, y - 12, x + 24, y + 12, 12, rot), hx(0xF3C9A5), x, soft=5, sh=(2, 3), blur=3, k=0.22)
        else:
            img = P_(img, circ(N, N, 180, 220, 140), hx(0xFFF3EA), 1, soft=10)
            for (x, y, r, rot) in ((130, 200, 40, 20), (205, 190, 44, -15), (170, 245, 40, 5), (235, 245, 34, 30)):
                img = P_(img, circ(N, N, x, y, r), hx(0xE0783E), x, soft=8, sh=(3, 5), blur=5, k=0.25)
                img = P_(img, rr(N, N, x + r * 0.5, y - r * 1.5, x + r * 0.85, y - r * 0.4, 8, 20), hx(0xF5ECDD), x + 7, soft=3, sh=(1, 2), blur=2, k=0.15)
        return img
    return sprite(f"food2a_{lang}", N, N, fn)

def food2b(lang):   # 콜라(ko 1.5L) / 소다 컵(en)
    N = 300
    def fn(img):
        if lang == "ko":
            p = skia.Path(); p.moveTo(110, 70); p.lineTo(190, 70); p.lineTo(196, 110); p.quadTo(240, 140, 236, 190); p.lineTo(236, 300 - 40); p.quadTo(236, 276, 210, 276); p.lineTo(90, 276); p.quadTo(64, 276, 64, 250); p.lineTo(64, 190); p.quadTo(60, 140, 104, 110); p.close()
            m = M(N, N); m.cv.drawPath(p, paint())
            img = P_(img, m.arr(), hx(0x6B4A3C), 1, soft=10)
            img = P_(img, rr(N, N, 64, 170, 236, 232, 6), RED, 2, soft=5, sh=(1, 2), blur=2, k=0.1, depth=0.5)
            img = P_(img, rr(N, N, 112, 44, 188, 74, 10), hx(0xE9776E), 3, soft=4, sh=(1, 2), blur=2, k=0.2)
        else:
            p = skia.Path(); p.moveTo(80, 90); p.lineTo(220, 90); p.lineTo(200, 270); p.lineTo(100, 270); p.close()
            m = M(N, N); m.cv.drawPath(p, paint())
            img = P_(img, m.arr(), hx(0xFFF3EA), 1, soft=9)
            img = P_(img, rr(N, N, 92, 160, 208, 220, 8), RED, 2, soft=4, sh=(1, 2), blur=2, k=0.1, depth=0.5)
            img = P_(img, rr(N, N, 70, 70, 230, 98, 12), hx(0xD0D4E0), 3, soft=4)
            mm = M(N, N); mm.cv.drawLine(190, 70, 215, 22, paint(10))
            img = P_(img, mm.arr(), RED, 4, soft=3, sh=(1, 2), blur=2, k=0.15)
        return img
    return sprite(f"food2b_{lang}", N, N, fn)

def ramen(lang):    # 라면 컵(ko) / 아이스크림 파인트(en)
    N = 340
    def fn(img):
        if lang == "ko":
            p = skia.Path(); p.moveTo(70, 120); p.lineTo(270, 120); p.lineTo(236, 300); p.lineTo(104, 300); p.close()
            m = M(N, N); m.cv.drawPath(p, paint())
            img = P_(img, m.arr(), hx(0xFFF3EA), 1, soft=9)
            q = skia.Path(); q.moveTo(86, 200); q.lineTo(254, 200); q.lineTo(244, 252); q.lineTo(96, 252); q.close()
            mm = M(N, N); mm.cv.drawPath(q, paint())
            img = P_(img, mm.arr(), RED, 2, soft=5, sh=(1, 2), blur=2, k=0.1, depth=0.5)
            img = P_(img, rr(N, N, 60, 98, 280, 134, 14), hx(0xF2BE3C), 3, soft=6)
        else:
            p = skia.Path(); p.moveTo(90, 120); p.lineTo(250, 120); p.lineTo(236, 300); p.lineTo(104, 300); p.close()
            m = M(N, N); m.cv.drawPath(p, paint())
            img = P_(img, m.arr(), hx(0xF6C1C6), 1, soft=9)
            img = P_(img, rr(N, N, 84, 90, 256, 130, 14), hx(0xFFF3EA), 2, soft=6)
            img = P_(img, circ(N, N, 170, 215, 36), hx(0xFFF3EA), 3, soft=8, sh=(2, 3), blur=3, k=0.2)
        return img
    return sprite(f"ramen_{lang}", N, N, fn)

def clipboard(lang):
    N = 360
    def fn(img):
        img = P_(img, rr(N, N, 80, 40, 280, 320, 20), hx(0xC48F5E), 1, soft=8)
        img = P_(img, rr(N, N, 96, 74, 264, 304, 12), hx(0xFFFBF2), 2, soft=5, sh=(1, 2), blur=2, k=0.12, depth=0.4)
        img = P_(img, rr(N, N, 140, 24, 220, 66, 12), hx(0x9AA3B8), 3, soft=5)
        t1 = "요청서" if lang == "ko" else "REQUEST"
        img, _ = put_text(img, N, N, t1, 180, 130, 40, "jua", NAVYC, "c", shadow=False)
        for i, w in enumerate((130, 110, 120, 90)):
            m = M(N, N); m.cv.drawLine(120, 160 + i * 36, 120 + w, 160 + i * 36, paint(8)); img = over(img, m.arr(), hx(0xC9CCDA))
        return img
    return sprite(f"clip_{lang}", N, N, fn)

def stamp_mark(kind, lang):
    N = 300
    ko = {"no": "반려", "ok": "승인"}; en = {"no": "DENIED", "ok": "OK"}
    col = RED if kind == "no" else hx(0x5DB08C)
    s = (ko if lang == "ko" else en)[kind]
    def fn(img):
        r1 = ring(N, N, N / 2, N / 2, 112, 14); r2 = ring(N, N, N / 2, N / 2, 94, 5)
        img = over(img, np.maximum(r1, r2) * 0.9, col)
        size = 100 if lang == "ko" else 58
        img, _ = put_text(img, N, N, s, N / 2, N / 2 + size * 0.34, size, "black", col, "c", shadow=False)
        return img
    return sprite(f"stampmk_{kind}_{lang}", N, N, fn)

def stamp_tool():
    N = 260
    def fn(img):
        img = P_(img, rr(N, N, 70, 190, 190, 230, 14), hx(0x6B7BA8), 1, soft=6)
        img = P_(img, rr(N, N, 106, 120, 154, 196, 14), hx(0xD9A877), 2, soft=6)
        img = P_(img, circ(N, N, 130, 100, 36), hx(0xC48F5E), 3, soft=9)
        return img
    return sprite("stamp_tool", N, N, fn)

def remote():
    N = 200
    def fn(img):
        img = P_(img, rr(N, N, 70, 30, 130, 170, 20), hx(0x9AA3B8), 1, soft=6)
        img = P_(img, circ(N, N, 100, 70, 14), RED, 2, soft=4, sh=(1, 2), blur=2, k=0.15)
        img = P_(img, circ(N, N, 100, 115, 10), GOLD, 3, soft=3, sh=(1, 2), blur=2, k=0.15)
        return img
    return sprite("remote", N, N, fn)

def cup():
    N = 200
    def fn(img):
        p = skia.Path(); p.moveTo(56, 60); p.lineTo(144, 60); p.lineTo(130, 170); p.lineTo(70, 170); p.close()
        m = M(N, N); m.cv.drawPath(p, paint())
        img = P_(img, m.arr(), hx(0xE4F1FA), 1, soft=6)
        q = skia.Path(); q.moveTo(60, 96); q.lineTo(140, 96); q.lineTo(130, 170); q.lineTo(70, 170); q.close()
        mm = M(N, N); mm.cv.drawPath(q, paint())
        img = P_(img, mm.arr(), hx(0x9CC6E6), 2, soft=4, sh=(1, 1), blur=2, k=0.08, depth=0.4)
        return img
    return sprite("cup", N, N, fn)

def crate():
    N = 200
    def fn(img):
        img = P_(img, rr(N, N, 40, 60, 160, 160, 14), hx(0xE3BF8D), 1, soft=7)
        img = P_(img, rr(N, N, 90, 60, 110, 160, 3), hx(0xF5E6C8), 2, soft=3, sh=(1, 1), blur=2, k=0.1, depth=0.4)
        return img
    return sprite("crate", N, N, fn)

def bubble_acid():
    N = 120
    def fn(img):
        img = P_(img, circ(N, N, 60, 60, 38), hx(0xBFE6A0), 1, soft=8, sh=(2, 3), blur=3, k=0.2)
        return P_(img, circ(N, N, 48, 46, 9), hx(0xF1FAE4), 2, soft=3, sh=(0, 0), blur=1, k=0.0, depth=0.3)
    return sprite("acid", N, N, fn)

def sweat():
    N = 100
    def fn(img):
        p = skia.Path(); p.moveTo(50, 10); p.cubicTo(80, 44, 84, 64, 50, 84); p.cubicTo(16, 64, 20, 44, 50, 10); p.close()
        m = M(N, N); m.cv.drawPath(p, paint())
        return P_(img, m.arr(), hx(0x9CC6E6), 1, soft=6, sh=(2, 3), blur=3, k=0.2)
    return sprite("sweat", N, N, fn)

def burst(txt="!"):
    N = 220
    def fn(img):
        img = P_(img, star(N, N, 110, 110, 96, -90, 0.55, 5), CORALC, 1, soft=8)
        img, _ = put_text(img, N, N, txt, 110, 150, 100, "black", hx(0xFFF8EE), "c", shadow=False)
        return img
    return sprite("burst" + txt, N, N, fn)

def starsp(col=0xF6CB45, key="star", r=40):
    N = int(r * 2 + 30)
    def fn(img):
        return P_(img, star(N, N, N / 2, N / 2, r, -90, 0.5, 4), hx(col), 1, soft=5, sh=(2, 3), blur=3, k=0.2)
    return sprite(f"{key}{r}{col}", N, N, fn)

def heartsp(col=0xF58FA0, r=40):
    N = int(r * 2 + 30)
    def fn(img):
        p = skia.Path(); c = N / 2
        p.moveTo(c, c + r * 0.9); p.cubicTo(c - r * 1.5, c - r * 0.1, c - r * 0.7, c - r * 1.1, c, c - r * 0.35)
        p.cubicTo(c + r * 0.7, c - r * 1.1, c + r * 1.5, c - r * 0.1, c, c + r * 0.9); p.close()
        m = M(N, N); m.cv.drawPath(p, paint())
        return P_(img, m.arr(), hx(col), 2, soft=6, sh=(2, 3), blur=3, k=0.2)
    return sprite(f"heart{r}{col}", N, N, fn)

def zsp():
    N = 140
    def fn(img):
        img, _ = put_text(img, N, N, "Z", 70, 100, 90, "black", hx(0xA79BE6), "c", shadow=True)
        return img
    return sprite("zsp", N, N, fn)

def thumb():
    N = 360
    def fn(img):
        img = P_(img, rr(N, N, 60, 150, 140, 310, 18), hx(0x8FB5E8), 1, soft=7)
        p = skia.Path(); p.moveTo(150, 170); p.cubicTo(190, 140, 200, 90, 215, 50); p.cubicTo(250, 52, 262, 100, 244, 150)
        p.lineTo(298, 150); p.quadTo(330, 152, 322, 190); p.lineTo(310, 270); p.quadTo(300, 306, 270, 306); p.lineTo(150, 306); p.close()
        m = M(N, N); m.cv.drawPath(p, paint())
        return P_(img, m.arr(), hx(0xF9D9A0), 2, soft=10)
    return sprite("thumb", N, N, fn)

def bell():
    N = 340
    def fn(img):
        p = skia.Path(); p.moveTo(170, 50); p.cubicTo(80, 50, 80, 140, 70, 210); p.lineTo(50, 250); p.lineTo(290, 250); p.lineTo(270, 210); p.cubicTo(260, 140, 260, 50, 170, 50); p.close()
        m = M(N, N); m.cv.drawPath(p, paint())
        img = P_(img, m.arr(), hx(0xF6CB45), 1, soft=12)
        img = P_(img, circ(N, N, 170, 282, 26), hx(0xE0A82E), 2, soft=8)
        return P_(img, circ(N, N, 170, 40, 16), hx(0xE0A82E), 3, soft=5)
    return sprite("bell", N, N, fn)

def sheet(col, key):
    Wd, Hh = 520, 1200
    def fn(img):
        return P_(img, rr(Wd, Hh, 20, 0, 500, 1200, 30), col, 7, soft=14, sh=(-14, 0), blur=12, k=0.28, depth=0.6)
    return sprite("sheet" + key, Wd, Hh, fn)

def speech_notice(key, lines, w=860, size=50, title=None, tag=None):
    """사내 공지/메신저 카드: 크림 종이 + 핀 + 줄 글"""
    h = 120 + len(lines) * int(size * 1.5) + (70 if title else 0)
    N1, N2 = w + 80, h + 80
    def fn(img):
        img = P_(img, rr(N1, N2, 40, 40, 40 + w, 40 + h, 30), hx(0xFFF8EA), 11, soft=9, sh=(8, 12), blur=10, k=0.3)
        img = P_(img, circ(N1, N2, 40 + w / 2, 52, 18), RED, 3, soft=6, sh=(2, 3), blur=3, k=0.25)
        y = 100
        if title:
            m = rr(N1, N2, 40 + 30, 40 + 30, 40 + 30 + int(tw(title, 44, "jua")) + 50, 40 + 30 + 70, 22)
            img = P_(img, m, hx(0xF4B3A8), 4, soft=5, sh=(3, 4), blur=4, k=0.2, depth=0.6)
            img, _ = put_text(img, N1, N2, title, 40 + 55, 40 + 30 + 52, 44, "jua", NAVYC, "l", shadow=False)
            y = 40 + 30 + 70 + 60
        for ln in lines:
            img, _ = put_text(img, N1, N2, ln, 40 + 48, y + 40, size, "jua", NAVYC, "l", shadow=False)
            y += int(size * 1.5)
        return img
    return sprite("notice_" + key, N1, N2, fn)

# ───────── 운동·자세 시연용 뼈대(관절) 다이어그램 (사용자 지시 2026-10-28: 캐릭터 연기만으로는
# 동작이 이해되지 않는다 → 관절점+뼈대선 진단판을 캐릭터 옆에 띄운다. P_pose(render.py)가 쓴다) ─────────
def pose_card(w, h, key):
    """진단판 종이 카드(크림색, 둥근 모서리)"""
    N1, N2 = int(w + 120), int(h + 120)
    def fn(img):
        return P_(img, rr(N1, N2, 60, 60, 60 + w, 60 + h, 38), hx(0xFFFCF3), 9, soft=9, sh=(7, 11), blur=10, k=0.26, depth=0.6)
    return sprite(f"posecard_{key}_{int(w)}_{int(h)}", N1, N2, fn)

# ───────── 사람모형(마네킹) 포즈 — 뼈대 다이어그램을 대체 (사용자 지시 2026-10-28·29: 뼈대는
# 투박해서 못 알아본다. 머리+몸통+팔다리를 가진 둥글둥글한 사람모형이 의자에 앉아 동작하는 모습으로
# 그린다. 측면(側面) 전용 — 의자도 측면, 사람도 측면. 포즈 전체를 하나의 포즈=하나의 스프라이트로
# 미리 굽는다(관절 체인을 매 프레임 합성하지 않음 — 이음매 어긋남 버그를 피하려고 2026-10-28에
# 통째로 굽는 방식으로 바꿨다). 색은 고정: 살색(목·머리·팔), 몸통 전용 초록(민트그린), 하의 네이비,
# 신발 진네이비. 자세한 검증 과정과 예시는 CHARACTER_BIBLE.md "운동·자세 동작 시연" 참고.
POSE_SKIN, POSE_SKIN_SH = 0xF6C9A0, 0xE8AE7E
POSE_SHIRT = 0x6FB6A8
POSE_PANTS = 0x4F7D8C
POSE_SHOE = 0x3E4A5E
POSE_HAIR = 0x4A3A2E
POSE_WOOD = 0xC9A877

def pose_mannequin_chin_tuck(key, neck_lean):
    """측면으로 의자에 앉은 사람모형 — 턱 당기기 등 '목이 앞뒤로 기우는' 동작용.
    neck_lean: 목이 앞으로 기운 정도(양수=턱이 앞으로 나옴/목 폄, 음수=턱을 당김). P_pose가
    neck_lean_from→neck_lean_to 두 값으로 이 함수를 두 번 불러 전/후(ghost+now)를 겹쳐 보여준다.
    검증된 값: turtle-neck(기본 자세) neck_lean=70, 턱 당긴 자세 neck_lean=-20."""
    N1, N2 = 560, 700
    def fn(img):
        m = M(N1, N2)
        ox, oy = 50, 500
        m.cv.drawRect(skia.Rect(ox + 170, oy + 34, ox + 190, oy + 176), paint())
        m.cv.drawRect(skia.Rect(ox, oy + 34, ox + 20, oy + 176), paint())
        seat = skia.Path(); seat.moveTo(ox, oy); seat.lineTo(ox + 190, oy); seat.lineTo(ox + 178, oy + 34); seat.lineTo(ox + 12, oy + 34); seat.close()
        m.cv.drawPath(seat, paint())
        m.cv.drawRoundRect(skia.Rect(ox - 8, oy - 260, ox + 26, oy + 10), 10, 10, paint())
        img = P_(img, m.arr(), hx(POSE_WOOD), 3, soft=5, sh=(3, 4), blur=5, k=0.16, depth=0.42)

        hipx, hipy = 290, oy - 4
        # 다리(먼저 그려 몸통 뒤에 깔림): 엉덩이→무릎(앞쪽)→바닥에 닿은 발까지
        mleg = M(N1, N2)
        kneex, kneey = hipx + 150, hipy - 14
        mleg.cv.drawLine(hipx - 10, hipy - 20, kneex, kneey, paint(66))
        footx, footy = kneex - 6, hipy + 176
        mleg.cv.drawLine(kneex, kneey, footx, footy, paint(52))
        img = P_(img, mleg.arr(), hx(POSE_PANTS), 4, soft=5, sh=(3, 4), blur=5, k=0.18, depth=0.5)
        mfoot = M(N1, N2)
        foot = skia.Path(); foot.moveTo(footx - 28, footy - 18); foot.lineTo(footx + 14, footy - 18); foot.quadTo(footx + 58, footy - 18, footx + 58, footy + 6)
        foot.quadTo(footx + 58, footy + 26, footx + 18, footy + 26); foot.lineTo(footx - 28, footy + 26); foot.close()
        mfoot.cv.drawPath(foot, paint())
        img = P_(img, mfoot.arr(), hx(POSE_SHOE), 4, soft=3, sh=(1, 2), blur=3, k=0.14, depth=0.4)

        # 몸통: 초록색 자체가 몸통(밑에 살색 레이어 없음 — 겹쳐서 삐져나오는 문제를 원천 차단)
        mtorso = M(N1, N2)
        torso_top = hipy - 205
        mtorso.cv.drawRRect(skia.RRect.MakeRectXY(skia.Rect(hipx - 95, torso_top, hipx + 95, hipy), 44, 70), paint())
        img = P_(img, mtorso.arr(), hx(POSE_SHIRT), 5, soft=5, sh=(3, 5), blur=5, k=0.2, depth=0.56)

        # 팔(무릎 위에 걸쳐 쉬는 자세), 몸통 위에 그림
        marm = M(N1, N2); marm.cv.drawLine(hipx - 84, torso_top + 34, hipx - 10, hipy - 34, paint(30))
        img = P_(img, marm.arr(), hx(POSE_SKIN), 6, soft=4, sh=(2, 3), blur=4, k=0.18, depth=0.5)

        # 목+머리를 하나의 도형으로 합쳐 그림(union) — 목 아래쪽이 몸통 속으로 파고들게 해서
        # 이음매 틈이 절대 생기지 않는다. neck_lean으로 목이 앞뒤로 기우는 각도 조절.
        shoulderx, shouldery = hipx + 6, torso_top + 40
        neck_tip_x, neck_tip_y = shoulderx + neck_lean * 0.62, shouldery - 78
        nw = 30
        neck = skia.Path()
        neck.moveTo(shoulderx - nw, shouldery + 34); neck.lineTo(neck_tip_x - nw, neck_tip_y)
        neck.arcTo(skia.Rect(neck_tip_x - nw, neck_tip_y - nw, neck_tip_x + nw, neck_tip_y + nw), 180, 180, False)
        neck.lineTo(shoulderx + nw, shouldery + 34); neck.close()
        headR = 58
        head_cx, head_cy = neck_tip_x + neck_lean * 0.30, neck_tip_y - headR * 0.55
        head = skia.Path(); head.addCircle(head_cx, head_cy, headR)
        union = skia.Op(neck, head, skia.PathOp.kUnion_PathOp)
        mhead = M(N1, N2); mhead.cv.drawPath(union, paint())
        img = P_(img, mhead.arr(), hx(POSE_SKIN), 7, soft=5, sh=(4, 6), blur=6, k=0.2, depth=0.56)

        # 귀(머리 위쪽 뒤편, 목 이음매와 겹치지 않는 자리)
        mear = M(N1, N2); mear.cv.drawCircle(head_cx - headR * 0.74, head_cy + headR * 0.1, headR * 0.19, paint())
        img = P_(img, mear.arr(), hx(POSE_SKIN), 8, soft=3, sh=(1, 2), blur=2, k=0.12)
        # 머리카락
        mhair = M(N1, N2); mhair.cv.drawArc(skia.Rect(head_cx - headR * 1.02, head_cy - headR * 1.08, head_cx + headR * 1.02, head_cy + headR * 0.35), 195, 170, True, paint())
        img = P_(img, mhair.arr(), hx(POSE_HAIR), 9, soft=3, sh=(1, 2), blur=2, k=0.1, depth=0.38)
        # 얼굴: 눈, 코, 입
        mface = M(N1, N2)
        mface.cv.drawCircle(head_cx + headR * 0.26, head_cy - headR * 0.06, headR * 0.09, paint())
        nose = skia.Path(); nose.moveTo(head_cx + headR * 0.48, head_cy - headR * 0.02); nose.quadTo(head_cx + headR * 0.62, head_cy + headR * 0.1, head_cx + headR * 0.46, head_cy + headR * 0.16)
        mface.cv.drawPath(nose, paint(headR * 0.05))
        a = mface.arr()[..., None]; img = img * (1 - a) + hx(0x26304F)[None, None, :] * a
        mmouth = M(N1, N2); sm = skia.Path(); sm.moveTo(head_cx + headR * 0.1, head_cy + headR * 0.22); sm.quadTo(head_cx + headR * 0.30, head_cy + headR * 0.34, head_cx + headR * 0.46, head_cy + headR * 0.2)
        mmouth.cv.drawPath(sm, paint(headR * 0.045)); a2 = mmouth.arr()[..., None]; img = img * (1 - a2) + hx(0xB5583F)[None, None, :] * a2
        return img
    return sprite(f"posemannequin_{key}_{neck_lean}", N1, N2, fn)

def pose_mannequin_knee_hug(key):
    """측면으로 의자에 앉아 한쪽 무릎을 가슴 쪽으로 당겨 안은 사람모형 — 정적 유지 동작(예: 무릎 당기기)용.
    다리는 하나만 그린다(들어 올린 쪽) — 바닥에 닿은 다른 쪽 다리까지 같이 그리면 둘이 겹쳐 보여
    '무릎만 당긴' 모양이 아니라 '다리 전체가 그대로 바닥에 있는' 것처럼 보인다(2026-10-29 확인).
    허벅지만 가슴 높이까지 들어 올리고, 무릎 아래(정강이+발)는 짧게 접어 바닥에서 뚜렷이 떨어뜨린다
    (처음엔 자연스럽게 늘어뜨렸더니 발이 다시 바닥 높이까지 내려와 '보통 앉은 다리'처럼 보였다 — 작은
    카드 크기에서 뚜렷이 읽히려면 다리 전체를 압축해 몸 쪽에 바짝 붙여야 한다)."""
    N1, N2 = 560, 700
    def fn(img):
        m = M(N1, N2)
        ox, oy = 50, 500
        m.cv.drawRect(skia.Rect(ox + 170, oy + 34, ox + 190, oy + 176), paint())
        m.cv.drawRect(skia.Rect(ox, oy + 34, ox + 20, oy + 176), paint())
        seat = skia.Path(); seat.moveTo(ox, oy); seat.lineTo(ox + 190, oy); seat.lineTo(ox + 178, oy + 34); seat.lineTo(ox + 12, oy + 34); seat.close()
        m.cv.drawPath(seat, paint())
        m.cv.drawRoundRect(skia.Rect(ox - 8, oy - 260, ox + 26, oy + 10), 10, 10, paint())
        img = P_(img, m.arr(), hx(POSE_WOOD), 3, soft=5, sh=(3, 4), blur=5, k=0.16, depth=0.42)

        hipx, hipy = 290, oy - 4
        # 몸통
        mtorso = M(N1, N2)
        torso_top = hipy - 205
        mtorso.cv.drawRRect(skia.RRect.MakeRectXY(skia.Rect(hipx - 95, torso_top, hipx + 95, hipy), 44, 70), paint())
        img = P_(img, mtorso.arr(), hx(POSE_SHIRT), 5, soft=5, sh=(3, 5), blur=5, k=0.2, depth=0.56)

        # 목+머리(곧게, 턱당기기 기울임 없음) — chin_tuck과 같은 유니언 기법
        shoulderx, shouldery = hipx + 6, torso_top + 40
        neck_tip_x, neck_tip_y = shoulderx, shouldery - 78
        nw = 30
        neck = skia.Path()
        neck.moveTo(shoulderx - nw, shouldery + 34); neck.lineTo(neck_tip_x - nw, neck_tip_y)
        neck.arcTo(skia.Rect(neck_tip_x - nw, neck_tip_y - nw, neck_tip_x + nw, neck_tip_y + nw), 180, 180, False)
        neck.lineTo(shoulderx + nw, shouldery + 34); neck.close()
        headR = 58
        head_cx, head_cy = neck_tip_x, neck_tip_y - headR * 0.55
        head = skia.Path(); head.addCircle(head_cx, head_cy, headR)
        union = skia.Op(neck, head, skia.PathOp.kUnion_PathOp)
        mhead = M(N1, N2); mhead.cv.drawPath(union, paint())
        img = P_(img, mhead.arr(), hx(POSE_SKIN), 7, soft=5, sh=(4, 6), blur=6, k=0.2, depth=0.56)
        mear = M(N1, N2); mear.cv.drawCircle(head_cx - headR * 0.74, head_cy + headR * 0.1, headR * 0.19, paint())
        img = P_(img, mear.arr(), hx(POSE_SKIN), 8, soft=3, sh=(1, 2), blur=2, k=0.12)
        mhair = M(N1, N2); mhair.cv.drawArc(skia.Rect(head_cx - headR * 1.02, head_cy - headR * 1.08, head_cx + headR * 1.02, head_cy + headR * 0.35), 195, 170, True, paint())
        img = P_(img, mhair.arr(), hx(POSE_HAIR), 9, soft=3, sh=(1, 2), blur=2, k=0.1, depth=0.38)
        mface = M(N1, N2)
        mface.cv.drawCircle(head_cx + headR * 0.26, head_cy - headR * 0.06, headR * 0.09, paint())
        nose = skia.Path(); nose.moveTo(head_cx + headR * 0.48, head_cy - headR * 0.02); nose.quadTo(head_cx + headR * 0.62, head_cy + headR * 0.1, head_cx + headR * 0.46, head_cy + headR * 0.16)
        mface.cv.drawPath(nose, paint(headR * 0.05))
        a = mface.arr()[..., None]; img = img * (1 - a) + hx(0x26304F)[None, None, :] * a
        mmouth = M(N1, N2); sm = skia.Path(); sm.moveTo(head_cx + headR * 0.1, head_cy + headR * 0.22); sm.quadTo(head_cx + headR * 0.30, head_cy + headR * 0.34, head_cx + headR * 0.46, head_cy + headR * 0.2)
        mmouth.cv.drawPath(sm, paint(headR * 0.045)); a2 = mmouth.arr()[..., None]; img = img * (1 - a2) + hx(0xB5583F)[None, None, :] * a2

        # 들어 올린 다리: 허벅지만 가슴 쪽으로(hipx+70, torso_top+30), 무릎 아래는 짧게 접어
        # 몸 쪽에 붙임 — 몸통/머리보다 나중에 그려 앞쪽에 겹쳐 보이게 한다.
        kneex, kneey = hipx + 70, torso_top + 30
        mleg = M(N1, N2); mleg.cv.drawLine(hipx - 10, hipy - 20, kneex, kneey, paint(66))
        footx, footy = kneex - 6, kneey + 85
        mleg.cv.drawLine(kneex, kneey, footx, footy, paint(50))
        img = P_(img, mleg.arr(), hx(POSE_PANTS), 10, soft=5, sh=(3, 4), blur=5, k=0.18, depth=0.5)
        mfoot = M(N1, N2)
        foot = skia.Path(); foot.moveTo(footx - 20, footy - 14); foot.lineTo(footx + 22, footy - 14); foot.quadTo(footx + 46, footy - 14, footx + 46, footy + 6)
        foot.quadTo(footx + 46, footy + 22, footx + 10, footy + 22); foot.lineTo(footx - 20, footy + 22); foot.close()
        mfoot.cv.drawPath(foot, paint())
        img = P_(img, mfoot.arr(), hx(POSE_SHOE), 10, soft=3, sh=(1, 2), blur=3, k=0.14, depth=0.4)

        # 양팔로 허벅지/무릎을 감싸 안음 — 다리보다 더 나중에 그려 맨 앞에 보이게 한다.
        marm = M(N1, N2)
        marm.cv.drawLine(hipx - 84, torso_top + 34, kneex - 16, kneey + 36, paint(30))
        marm.cv.drawLine(hipx - 70, torso_top + 60, kneex + 18, kneey + 30, paint(28))
        img = P_(img, marm.arr(), hx(POSE_SKIN), 11, soft=4, sh=(2, 3), blur=4, k=0.18, depth=0.5)
        return img
    return sprite(f"posemannequinknee_{key}", N1, N2, fn)

def pose_angle_badge(text, key):
    """각도/횟수 등 작은 숫자 배지(글자 길이에 맞춰 너비 자동, 별도 함수로 둬 chip_sprite와 캐시 키가 겹치지 않게 한다)"""
    size = 42
    N1, N2 = int(tw(text, size, "black") + 70), 104
    def fn(img):
        img = P_(img, rr(N1, N2, 10, 10, N1 - 10, N2 - 10, 24), hx(0x26304F), 3, soft=4, sh=(3, 4), blur=4, k=0.22)
        img, _ = put_text(img, N1, N2, text, N1 / 2, N2 / 2 + 16, size, "black", hx(0xFFF8EE), "c", shadow=False)
        return img
    return sprite(f"poseangle_{key}_{text}", N1, N2, fn)

def pose_part_tag(text, color, key):
    """다이어그램 안에 붙이는 신체 부위 이름표('목', '허리' 등, 사용자 지시 2026-10-28:
    스틸컷만 봐도 어디가 목이고 어디가 허리인지 알 수 있어야 한다). 작은 색 점 + 글자."""
    size = 40
    N1, N2 = int(tw(text, size, "black") + 90), 92
    def fn(img):
        img = P_(img, rr(N1, N2, 8, 8, N1 - 8, N2 - 8, 22), hx(0xFFFFFF), 4, soft=3, sh=(2, 3), blur=3, k=0.18)
        img = P_(img, circ(N1, N2, 46, N2 / 2, 14), hx(color), 2, soft=2, sh=(1, 1), blur=2, k=0.1)
        img, _ = put_text(img, N1, N2, text, 74, N2 / 2 + 14, size, "black", hx(0x26304F), "l", shadow=False)
        return img
    return sprite(f"posepart_{key}_{text}_{color}", N1, N2, fn)
