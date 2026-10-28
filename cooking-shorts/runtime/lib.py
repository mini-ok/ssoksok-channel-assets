"""그리기 도우미: skia 기반 2D 벡터 캐릭터/도형/자막"""
import math, os
import skia

W, H, FPS = 1080, 1920, 30
FONT_PATH = os.path.join(os.path.dirname(__file__), "fonts", "Jua-Regular.ttf")
TF = skia.Typeface.MakeFromFile(FONT_PATH, 0)  # Noto Sans CJK KR Black

NAVY = 0x2B2D5B
WHITE = 0xFFFFFF
SKY = 0x5CC8FF
SKY_D = 0x2F8FE0
PINK = 0xFF7FA8
YELLOW = 0xFFD93D
RED = 0xFF5A5F
MINT = 0x4FD1A5
PEACH = 0xFFC8B8
ORANGE = 0xFF9F43
GRAY = 0x9AA3B8
PURPLE = 0x8E7CFF


def C(hexv, a=255):
    return skia.Color((hexv >> 16) & 255, (hexv >> 8) & 255, hexv & 255, int(a))


def P(color, style="fill", w=0, a=255):
    p = skia.Paint(AntiAlias=True, Color=C(color, a))
    if style == "stroke":
        p.setStyle(skia.Paint.kStroke_Style)
        p.setStrokeWidth(w)
        p.setStrokeCap(skia.Paint.kRound_Cap)
        p.setStrokeJoin(skia.Paint.kRound_Join)
    return p


def font(size):
    f = skia.Font(TF, size)
    f.setEdging(skia.Font.Edging.kAntiAlias)
    return f


def clamp(x, a=0.0, b=1.0):
    return max(a, min(b, x))


def lerp(a, b, t):
    return a + (b - a) * t


def ease_out_cubic(x):
    x = clamp(x)
    return 1 - (1 - x) ** 3


def ease_in_out(x):
    x = clamp(x)
    return x * x * (3 - 2 * x)


def ease_out_back(x, k=1.9):
    x = clamp(x)
    return 1 + (k + 1) * (x - 1) ** 3 + k * (x - 1) ** 2


def pop(t, start, dur=0.32):
    """등장 스케일 (0→오버슈트→1)"""
    if t < start:
        return 0.0
    return ease_out_back((t - start) / dur)


def text_w(s, size):
    return font(size).measureText(s)


def draw_text(cv, s, x, y, size, color=NAVY, anchor="c", outline=None, ow=10, a=255):
    f = font(size)
    w = f.measureText(s)
    if anchor == "c":
        x -= w / 2
    elif anchor == "r":
        x -= w
    if outline is not None:
        cv.drawString(s, x, y, f, P(outline, "stroke", ow))
    cv.drawString(s, x, y, f, P(color, a=a))
    return w


def pill(cv, cx, cy, w, h, fill=WHITE, stroke=NAVY, sw=6, a=255):
    r = skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(cx - w / 2, cy - h / 2, w, h), h / 2, h / 2)
    cv.drawRRect(r, P(fill, a=a))
    if stroke is not None:
        cv.drawRRect(r, P(stroke, "stroke", sw))


def rrect(cv, x, y, w, h, rad, fill=None, stroke=None, sw=6, a=255):
    r = skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(x, y, w, h), rad, rad)
    if fill is not None:
        cv.drawRRect(r, P(fill, a=a))
    if stroke is not None:
        cv.drawRRect(r, P(stroke, "stroke", sw))


def lin_grad(x0, y0, x1, y1, c0, c1):
    return skia.GradientShader.MakeLinear([(x0, y0), (x1, y1)], [C(c0), C(c1)])


def rad_grad(cx, cy, r, c0, c1, a0=255, a1=255):
    return skia.GradientShader.MakeRadial((cx, cy), r, [C(c0, a0), C(c1, a1)], [0, 1])


def sparkle(cv, x, y, r, color=YELLOW, rot=0, a=255):
    p = skia.Path()
    for i in range(8):
        ang = math.pi / 4 * i + rot
        rr = r if i % 2 == 0 else r * 0.28
        px, py = x + math.cos(ang) * rr, y + math.sin(ang) * rr
        if i == 0:
            p.moveTo(px, py)
        else:
            p.lineTo(px, py)
    p.close()
    cv.drawPath(p, P(color, a=a))
    cv.drawPath(p, P(NAVY, "stroke", 3, a=a))


def heart(cv, x, y, s, color=PINK, a=255):
    p = skia.Path()
    p.moveTo(x, y + s * 0.9)
    p.cubicTo(x - s * 1.4, y - s * 0.1, x - s * 0.6, y - s * 1.1, x, y - s * 0.35)
    p.cubicTo(x + s * 0.6, y - s * 1.1, x + s * 1.4, y - s * 0.1, x, y + s * 0.9)
    cv.drawPath(p, P(color, a=a))
    cv.drawPath(p, P(NAVY, "stroke", 4, a=a))


def draw_subtitle(cv, disp, lt, cy=1385, size=84, cx=None, maxw=940):
    """자막: 흰 글자 + 남색 외곽선, [[강조]]는 노랑. 아래쪽 쇼츠 UI 안전영역 위에 배치"""
    lines = disp.split("\n")
    # 한 줄 대사("이름: 대사")가 너무 길면 이름과 대사를 두 줄로 나눠 글자가 작아지지 않게
    _plain = lambda t: t.replace("[[", "").replace("]]", "")
    out = []
    for ln in lines:
        if ": " in ln and text_w(_plain(ln), size) > maxw:
            a, b = ln.split(": ", 1)
            out += [a, b]
        else:
            out.append(ln)
    lines = out
    if sum(ch.isascii() for ch in disp) > 0.8 * len(disp):   # 영문 자막: 두꺼운 외곽선에 묻히지 않게 띄어쓰기 넓히기
        lines = [ln.replace(" ", "  ") for ln in lines]
    parsed = []
    for ln in lines:
        segs, i = [], 0
        while i < len(ln):
            j = ln.find("[[", i)
            if j < 0:
                segs.append((ln[i:], False))
                break
            if j > i:
                segs.append((ln[i:j], False))
            k = ln.find("]]", j)
            segs.append((ln[j + 2:k], True))
            i = k + 2
        parsed.append(segs)
    # 폭에 맞춰 글자 크기 자동 조절
    widest = max(sum(text_w(t, size) for t, _ in segs) for segs in parsed)
    cx = W / 2 if cx is None else cx
    if widest > maxw:
        size = size * maxw / widest
    lh = size * 1.28
    total_h = lh * len(parsed)
    top = cy - total_h / 2 + size * 0.95
    k = ease_out_back(clamp(lt / 0.2), 1.4)
    a = 255 * clamp(lt / 0.12)
    cv.save()
    cv.translate(cx, cy)
    cv.scale(0.88 + 0.12 * k, 0.88 + 0.12 * k)
    cv.translate(-cx, -cy)
    for li, segs in enumerate(parsed):
        wtot = sum(text_w(t, size) for t, _ in segs)
        x = cx - wtot / 2
        y = top + li * lh
        for t, hi in segs:
            f = font(size)
            cv.drawString(t, x, y, f, P(NAVY, "stroke", size * 0.26, a=a))
            cv.drawString(t, x, y, f, P(YELLOW if hi else WHITE, a=a))
            x += f.measureText(t)
    cv.restore()

