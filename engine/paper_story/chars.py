"""몸속 회사 캐릭터 v2 — 말랑한 둥근 몸 + 큰 눈 + 역할 소품. 원점 = 몸통 중심, 기본 몸 반지름 약 150"""
import math
import skia
from lib import *

FLAGS = dict(feet=True, shadow=True, arms_up=False, lantern=True)
OUT_W = 7          # 외곽선 두께
INK = NAVY


def _p(path, col, light=None, shade=None, cx=-50, cy=-70, r=260):
    paint = P(col)
    if light:
        paint.setShader(rad_grad(cx, cy, r, light, shade or col))
    return paint


def blob(cv, path, col, light, shade=None, ow=OUT_W):
    b = path.getBounds()
    cv.drawPath(path, _p(path, col, light, shade, b.centerX() - b.width() * 0.2, b.centerY() - b.height() * 0.3, max(b.width(), b.height()) * 0.85))
    cv.drawPath(path, P(INK, "stroke", ow))


def circle_path(x, y, r):
    p = skia.Path(); p.addCircle(x, y, r); return p


def oval_path(x, y, w, h):
    p = skia.Path(); p.addOval(skia.Rect.MakeXYWH(x - w / 2, y - h / 2, w, h)); return p


def union(*paths):
    out = paths[0]
    for q in paths[1:]:
        out = skia.Op(out, q, skia.PathOp.kUnion_PathOp)
    return out


def face(cv, x, y, s=1.0, mood="happy", blush=PINK, look=(0, 0), gap=46):
    """큰 반짝 눈 + 볼터치 + 작은 입. mood: happy/tired/wow/sleepy/smug/worry/serious/awake/happy_closed"""
    cv.save(); cv.translate(x, y); cv.scale(s, s)
    for sx in (-1, 1):
        ex = sx * gap + look[0] * 6
        ey = look[1] * 5
        if mood in ("sleepy",):
            pth = skia.Path(); pth.moveTo(ex - 15, ey); pth.quadTo(ex, ey + 12, ex + 15, ey); cv.drawPath(pth, P(INK, "stroke", 6))
        elif mood == "happy_closed":
            pth = skia.Path(); pth.moveTo(ex - 15, ey + 5); pth.quadTo(ex, ey - 12, ex + 15, ey + 5); cv.drawPath(pth, P(INK, "stroke", 6))
        else:
            h = 34 if mood not in ("wow", "awake") else 40
            w = 26 if mood not in ("wow", "awake") else 30
            cv.drawOval(skia.Rect.MakeXYWH(ex - w / 2, ey - h / 2, w, h), P(INK))
            cv.drawCircle(ex - 4, ey - 8, 6.5, P(WHITE)); cv.drawCircle(ex + 5, ey + 7, 3, P(WHITE))
            if mood == "tired":
                cv.drawRect(skia.Rect.MakeLTRB(ex - 18, ey - 24, ex + 18, ey - 4), P(0, a=0))
                lid = skia.Path(); lid.moveTo(ex - 17, ey - 4); lid.lineTo(ex + 17, ey - 4)
                cv.drawPath(lid, P(INK, "stroke", 6))
            if mood == "serious":
                cv.drawLine(ex - sx * 16, ey - 30, ex + sx * 14, ey - 24, P(INK, "stroke", 6))
            if mood == "worry":
                cv.drawLine(ex - sx * 14, ey - 26, ex + sx * 14, ey - 32, P(INK, "stroke", 6))
        if mood == "tired":
            bg = skia.Path(); bg.moveTo(ex - 13, ey + 26); bg.quadTo(ex, ey + 34, ex + 13, ey + 26); cv.drawPath(bg, P(PURPLE, "stroke", 4, a=170))
    cv.drawOval(skia.Rect.MakeXYWH(-gap - 38, 22, 34, 18), P(blush, a=150))
    cv.drawOval(skia.Rect.MakeXYWH(gap + 4, 22, 34, 18), P(blush, a=150))
    my = 30
    mp = skia.Path()
    if mood == "awake":
        mp.moveTo(-16, my - 4); mp.quadTo(0, my + 20, 16, my - 4); mp.close(); cv.drawPath(mp, P(INK))
    elif mood in ("happy", "happy_closed", "sleepy"):
        mp.moveTo(-11, my - 2); mp.quadTo(-5, my + 8, 0, my); mp.quadTo(5, my + 8, 11, my - 2); cv.drawPath(mp, P(INK, "stroke", 5))
    elif mood == "wow":
        cv.drawOval(skia.Rect.MakeXYWH(-10, my - 6, 20, 22), P(INK)); cv.drawOval(skia.Rect.MakeXYWH(-6, my + 6, 12, 8), P(PINK))
    elif mood == "smug":
        mp.moveTo(-10, my + 2); mp.quadTo(4, my + 10, 14, my - 4); cv.drawPath(mp, P(INK, "stroke", 5))
    elif mood in ("tired", "worry"):
        mp.moveTo(-10, my + 4); mp.quadTo(0, my - 2, 10, my + 4); cv.drawPath(mp, P(INK, "stroke", 5))
    else:
        cv.drawLine(-9, my + 2, 9, my + 2, P(INK, "stroke", 5))
    cv.restore()


def limb(cv, x0, y0, x1, y1, col, w=26, hand=True):
    if FLAGS["arms_up"] and y0 == 30 and abs(x0) > 100:
        x1, y1 = x0 * 1.5, -100
    cv.drawLine(x0, y0, x1, y1, P(INK, "stroke", w + OUT_W * 2 - 2))
    cv.drawLine(x0, y0, x1, y1, P(col, "stroke", w))
    if hand:
        cv.drawCircle(x1, y1, w * 0.62, P(col)); cv.drawCircle(x1, y1, w * 0.62, P(INK, "stroke", 5))


def feet(cv, y, col, gap=56, w=62, h=34):
    if not FLAGS["feet"]: return
    for sx in (-1, 1):
        r = skia.Rect.MakeXYWH(sx * gap - w / 2, y - h / 2, w, h)
        cv.drawOval(r, P(col)); cv.drawOval(r, P(INK, "stroke", 6))


def shadow(cv, y, w=220):
    if not FLAGS["shadow"]: return
    cv.drawOval(skia.Rect.MakeXYWH(-w / 2, y - 14, w, 28), P(INK, a=28))


# ───────── 캐릭터 ─────────
def brain(cv, x, y, s=1.0, mood="happy", lt=0.0, hair=(0xE9C9A6, 0xF7E4CF, 0xC49A70)):
    """뇌 팀장: 살구빛 피부 몸 + 머리 위 몽실 구름머리(뇌 힌트) + 동그란 안경. hair=(색, 밝은색, 소용돌이색)"""
    C0, L0 = 0xFFE0CC, 0xFFF3EA
    H0, HL, HS = hair
    cv.save(); cv.translate(x, y); cv.scale(s, s)
    shadow(cv, 150)
    feet(cv, 136, 0xF6C9AE)
    limb(cv, -118, 30, -158, 78, C0); limb(cv, 118, 30, 158, 78, C0)
    body = union(oval_path(0, 10, 290, 260))
    blob(cv, body, C0, L0, shade=0xF7CDB4)
    puffs = union(circle_path(-72, -112, 58), circle_path(-8, -140, 66), circle_path(66, -116, 58), circle_path(-34, -96, 50), circle_path(36, -98, 50))
    blob(cv, puffs, H0, HL)
    for (sx, sy) in ((-40, -128), (34, -126)):
        sp = skia.Path(); sp.moveTo(sx - 16, sy + 6); sp.quadTo(sx - 14, sy - 14, sx + 4, sy - 12); sp.quadTo(sx + 18, sy - 6, sx + 8, sy + 6)
        cv.drawPath(sp, P(HS, "stroke", 6))
    face(cv, 0, 0, 1.0, mood, blush=0xFFAFA0)
    for sx in (-1, 1):
        cv.drawCircle(sx * 46, 0, 32, P(INK, "stroke", 5))
    cv.drawLine(-14, -2, 14, -2, P(INK, "stroke", 5))
    cv.restore()


def heart(cv, x, y, s=1.0, mood="happy", lt=0.0):
    """심장 배달기사: 하트 이모지형 몸 + 배달 모자 + 작은 상자"""
    C0, L0 = 0xFF7A93, 0xFFB3C1
    cv.save(); cv.translate(x, y); cv.scale(s, s)
    shadow(cv, 160)
    feet(cv, 146, C0, gap=46)
    limb(cv, -130, 10, -170, -30, C0); limb(cv, 128, 20, 170, 60, C0)
    hp = skia.Path()
    hp.moveTo(0, 150); hp.cubicTo(-210, 30, -160, -150, -60, -140); hp.cubicTo(-20, -136, 0, -110, 0, -84)
    hp.cubicTo(0, -110, 20, -136, 60, -140); hp.cubicTo(160, -150, 210, 30, 0, 150); hp.close()
    blob(cv, hp, C0, L0)
    face(cv, 0, -20, 1.0, mood, blush=0xFFD0DA)
    cv.save(); cv.translate(60, -130); cv.rotate(18)
    cap = skia.Path(); cap.moveTo(-70, 10); cap.quadTo(-66, -60, 0, -62); cap.quadTo(66, -60, 70, 10); cap.close()
    blob(cv, cap, 0x3D8BFF, 0x8FC0FF, ow=6)
    brim = skia.Path(); brim.addRRect(skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(-10, 0, 110, 22), 11, 11))
    blob(cv, brim, 0x2C6FD6, 0x5C95F0, ow=6)
    cv.drawCircle(0, -62, 9, P(WHITE)); cv.drawCircle(0, -62, 9, P(INK, "stroke", 4))
    cv.restore()
    rrect(cv, 150, 40, 80, 64, 10, fill=0xE8B56B, stroke=INK, sw=6)
    cv.drawLine(190, 40, 190, 104, P(0xC48A3C, "stroke", 6))
    cv.restore()


def gut(cv, x, y, s=1.0, mood="happy", lt=0.0):
    """장 화학자: 민트 모찌 + 꼬불 더듬이(장 힌트) + 고글 + 플라스크"""
    C0, L0 = 0x8EE0C0, 0xD2F7E8
    cv.save(); cv.translate(x, y); cv.scale(s, s)
    shadow(cv, 150)
    feet(cv, 138, C0)
    limb(cv, -130, 40, -168, 80, C0); limb(cv, 130, 30, 176, 0, C0)
    an = skia.Path(); an.moveTo(0, -120); an.cubicTo(-30, -170, 40, -190, 20, -150); an.cubicTo(5, -125, 50, -130, 40, -170)
    cv.drawPath(an, P(INK, "stroke", 16)); cv.drawPath(an, P(0x5CC79E, "stroke", 8))
    cv.drawCircle(40, -172, 14, P(0xFFD166)); cv.drawCircle(40, -172, 14, P(INK, "stroke", 5))
    body = skia.Path(); body.addRRect(skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(-145, -130, 290, 270), 130, 120))
    blob(cv, body, C0, L0)
    face(cv, 0, 10, 1.0, mood)
    rrect(cv, -110, -96, 220, 22, 11, fill=0x3A3F6B, stroke=INK, sw=4)
    for sx in (-1, 1):
        cv.drawCircle(sx * 48, -86, 30, P(0xBDE8FF)); cv.drawCircle(sx * 48, -86, 30, P(INK, "stroke", 6))
        cv.drawCircle(sx * 48 - 8, -94, 7, P(WHITE))
    fl = skia.Path(); fl.moveTo(166, -60); fl.lineTo(186, -60); fl.lineTo(186, -30); fl.lineTo(214, 20); fl.quadTo(220, 34, 204, 34)
    fl.lineTo(148, 34); fl.quadTo(132, 34, 138, 20); fl.lineTo(166, -30); fl.close()
    cv.drawPath(fl, P(0xFFF3A3)); cv.drawPath(fl, P(INK, "stroke", 6))
    cv.drawCircle(176, 12, 7, P(WHITE, a=200)); cv.drawCircle(192, -2, 5, P(WHITE, a=200))
    cv.restore()


def liver(cv, x, y, s=1.0, mood="happy_closed", lt=0.0):
    """간 청소반장: 호박빛 강낭콩 몸 + 청록 두건 + 대걸레"""
    C0, L0 = 0xF4BE63, 0xFFE3A8
    cv.save(); cv.translate(x, y); cv.scale(s, s)
    shadow(cv, 150)
    cv.drawLine(215, -150, 185, 140, P(INK, "stroke", 16)); cv.drawLine(215, -150, 185, 140, P(0xC98F5B, "stroke", 8))
    for k in range(6):
        cv.drawLine(185, 140, 157 + k * 11, 182, P(INK, "stroke", 12)); cv.drawLine(185, 140, 157 + k * 11, 182, P(0xF5F0E6, "stroke", 6))
    feet(cv, 138, C0)
    limb(cv, -150, 30, -186, 70, C0); limb(cv, 140, 10, 200, -20, C0)
    body = skia.Path()
    body.moveTo(-160, 10); body.cubicTo(-170, -110, -40, -140, 40, -120); body.cubicTo(140, -100, 175, -30, 150, 40)
    body.cubicTo(125, 120, 30, 140, -40, 130); body.cubicTo(-120, 120, -155, 80, -160, 10); body.close()
    blob(cv, body, C0, L0)
    face(cv, 0, 10, 1.0, mood, blush=0xFF9F7F)
    bd = skia.Path(); bd.moveTo(-120, -86); bd.quadTo(-20, -170, 110, -96); bd.lineTo(98, -70); bd.quadTo(-10, -126, -110, -62); bd.close()
    blob(cv, bd, 0x3CC7B4, 0x8EE6DA, ow=6)
    for (dx, dy) in ((-60, -100), (-10, -116), (44, -108)):
        cv.drawCircle(dx, dy, 6, P(WHITE))
    kt = skia.Path(); kt.moveTo(-118, -76); kt.lineTo(-160, -100); kt.lineTo(-150, -60); kt.close()
    cv.drawPath(kt, P(0x3CC7B4)); cv.drawPath(kt, P(INK, "stroke", 5))
    cv.restore()


def muscle(cv, x, y, s=1.0, mood="happy", lt=0.0):
    """근육 체육부장: 복숭아색 둥근 몸 + 빨간 머리띠 + 알통 팔 + 아령"""
    C0, L0 = 0xFFB08A, 0xFFDCC8
    cv.save(); cv.translate(x, y); cv.scale(s, s)
    shadow(cv, 150)
    feet(cv, 138, C0)
    for sx in (-1, 1):
        arm = union(circle_path(sx * 168, -20, 44), circle_path(sx * 138, 30, 32))
        blob(cv, arm, C0, L0, ow=6)
    rrect(cv, 196, -96, 14, 90, 7, fill=0x9AA3B8, stroke=INK, sw=4)
    for dy in (-104, -14):
        rrect(cv, 180, dy, 46, 26, 9, fill=0x5B647D, stroke=INK, sw=5)
    body = circle_path(0, 6, 140)
    blob(cv, body, C0, L0)
    face(cv, 0, 14, 1.0, mood, blush=0xFF7F7F)
    hb = skia.Path(); hb.addRRect(skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(-130, -88, 260, 34), 17, 17))
    cv.save(); cv.clipPath(circle_path(0, 6, 146), doAntiAlias=True)
    cv.drawPath(hb, P(0xFF5A5F)); cv.drawLine(-140, -71, 140, -71, P(WHITE, "stroke", 5, a=200))
    cv.restore()
    cv.drawPath(hb, P(INK, "stroke", 5))
    tail = skia.Path(); tail.moveTo(120, -80); tail.lineTo(170, -110); tail.lineTo(160, -66); tail.close()
    cv.drawPath(tail, P(0xFF5A5F)); cv.drawPath(tail, P(INK, "stroke", 5))
    cv.restore()


def immune(cv, x, y, s=1.0, mood="serious", lt=0.0):
    """면역세포 경비원: 하얀 뭉게 몸 + 경비 모자(별 배지) + 무전기"""
    C0, L0 = 0xF4F6FF, 0xFFFFFF
    cv.save(); cv.translate(x, y); cv.scale(s, s)
    shadow(cv, 150)
    feet(cv, 138, 0xDDE3F5)
    limb(cv, -140, 30, -180, 70, C0); limb(cv, 140, 20, 172, -20, C0)
    pts = []
    for k in range(12):
        a = k / 12 * 2 * math.pi
        pts.append(circle_path(math.cos(a) * 112, 10 + math.sin(a) * 104, 46))
    body = union(oval_path(0, 10, 250, 236), *pts)
    blob(cv, body, C0, L0, shade=0xDCE2F6)
    face(cv, 0, 18, 1.0, mood, blush=0xFFB3C1)
    cp = skia.Path(); cp.moveTo(-100, -70); cp.quadTo(-96, -150, 0, -156); cp.quadTo(96, -150, 100, -70); cp.close()
    blob(cv, cp, 0x2F3D7A, 0x5566AA, ow=6)
    brim = skia.Path(); brim.addRRect(skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(-112, -80, 224, 24), 12, 12))
    blob(cv, brim, 0x232E61, 0x3B4A8C, ow=6)
    sparkle(cv, 0, -118, 22, YELLOW)
    rrect(cv, 160, -60, 34, 56, 8, fill=0x3A3F55, stroke=INK, sw=5); cv.drawLine(186, -60, 186, -88, P(INK, "stroke", 6))
    cv.drawCircle(177, -40, 6, P(0x7CF0A0))
    cv.restore()


def melatonin(cv, x, y, s=1.0, mood="sleepy", lt=0.0):
    """멜라토닌 수면관리자: 라벤더 몸 + 늘어진 수면모자 + 별 랜턴"""
    C0, L0 = 0xC4B5FF, 0xE8E1FF
    cv.save(); cv.translate(x, y); cv.scale(s, s)
    shadow(cv, 150)
    feet(cv, 138, C0)
    limb(cv, -138, 30, -176, 70, C0)
    limb(cv, 136, 20, 172, -24, C0)
    if FLAGS["lantern"]:
        cv.drawLine(172, -24, 172, 10, P(INK, "stroke", 5))
        rrect(cv, 150, 10, 46, 56, 14, fill=0xFFE9A0, stroke=INK, sw=5)
        sparkle(cv, 173, 38, 13, 0xFFC93C)
    body = oval_path(0, 10, 280, 262)
    blob(cv, body, C0, L0)
    face(cv, 0, 16, 1.0, mood, blush=0xFFB3D9)
    hat = skia.Path(); hat.moveTo(-120, -70); hat.cubicTo(-90, -190, 60, -200, 130, -150); hat.cubicTo(190, -110, 200, -40, 170, -20)
    hat.cubicTo(150, -60, 120, -90, 110, -70); hat.close()
    blob(cv, hat, 0x6F5BD6, 0x9C8CF0, ow=6)
    band = skia.Path(); band.addRRect(skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(-130, -84, 250, 30), 15, 15))
    blob(cv, band, WHITE, WHITE, ow=5)
    cv.drawCircle(172, -14, 18, P(YELLOW)); cv.drawCircle(172, -14, 18, P(INK, "stroke", 5))
    for (sx, sy) in ((-30, -130), (40, -150)):
        sparkle(cv, sx, sy, 10, YELLOW)
    cv.restore()


def adenosine(cv, x, y, s=1.0, mood="sleepy", lt=0.0):
    """아데노신(졸음이): 작은 보라 모찌 + 졸린 눈 + Z 꼬리표"""
    C0, L0 = 0xB59CF5, 0xDCCEFF
    cv.save(); cv.translate(x, y); cv.scale(s, s)
    shadow(cv, 96, 150)
    body = skia.Path(); body.addRRect(skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(-90, -70, 180, 160), 80, 74))
    blob(cv, body, C0, L0)
    face(cv, 0, 14, 0.8, mood, blush=0xFF9FCF, gap=40)
    draw_text(cv, "z", 62, -60, 50, 0x7E62E0, outline=WHITE, ow=8)
    draw_text(cv, "z", 92, -98, 36, 0x7E62E0, outline=WHITE, ow=7)
    cv.restore()


def caffeine(cv, x, y, s=1.0, mood="smug", lt=0.0):
    """카페인 요원: 커피콩 몸 + 선글라스 + 이어피스"""
    C0, L0 = 0x9C6644, 0xC79A72
    cv.save(); cv.translate(x, y); cv.scale(s, s)
    shadow(cv, 110, 170)
    feet(cv, 100, 0x6E4A33, gap=40, w=52, h=28)
    limb(cv, -96, 20, -130, 54, C0, w=22); limb(cv, 96, 10, 128, -30, C0, w=22)
    body = oval_path(0, 0, 200, 220)
    blob(cv, body, C0, L0, shade=0x7A4E33)
    cr = skia.Path(); cr.moveTo(-6, -104); cr.cubicTo(36, -60, -36, -10, 6, 40); cv.drawPath(cr, P(0x6E4A33, "stroke", 8, a=150))
    face(cv, 0, 30, 0.85, mood, blush=0xE88A7A, gap=40)
    for sx in (-1, 1):
        rrect(cv, sx * 40 - 30, -2, 60, 34, 14, fill=0x1E2236, stroke=INK, sw=4)
        cv.drawLine(sx * 40 - 18, 6, sx * 40 - 4, 6, P(WHITE, "stroke", 4, a=170))
    cv.drawLine(-10, 10, 10, 10, P(INK, "stroke", 5))
    cv.drawLine(96, 6, 108, 34, P(INK, "stroke", 4)); cv.drawCircle(98, 2, 8, P(0x1E2236))
    cv.restore()


CAST = [
    ("brain", brain, "뇌 팀장", "Brain · Team Lead", "모든 걸 챙기지만 늘 피곤"),
    ("heart", heart, "심장 배달기사", "Heart · Courier", "성격 급한 피 배달 담당"),
    ("gut", gut, "장 연구원", "Gut · Chemist", "먹는 것에 예민한 화학자"),
    ("liver", liver, "간 청소반장", "Liver · Cleanup Chief", "묵묵히 야근하는 청소 담당"),
    ("muscle", muscle, "근육 체육부장", "Muscle · Coach", "움직이고 싶어 안달"),
    ("immune", immune, "면역 경비원", "Immune Cell · Security", "의심 많은 보안 요원"),
    ("melatonin", melatonin, "멜라토닌 매니저", "Melatonin · Night Manager", "밤마다 뇌를 재우는 관리자"),
    ("adenosine", adenosine, "아데노신(졸음이)", "Adenosine · Sleepy Signal", "깨어 있을수록 늘어나는 졸음"),
    ("caffeine", caffeine, "카페인 요원", "Caffeine · Agent", "졸음이 자리를 가로채는 요원"),
]


def stomach(cv, x, y, s=1.0, mood="happy", lt=0.0):
    """위 대리(소화1팀): 주머니 모양 연어빛 몸 + 위쪽 식도 꼬리 + 파란 넥타이 + 사원증"""
    C0, L0 = 0xF59A8E, 0xFFD4CA
    cv.save(); cv.translate(x, y); cv.scale(s, s)
    shadow(cv, 150)
    feet(cv, 162, 0xE88A80)
    limb(cv, -138, 40, -176, 84, C0); limb(cv, 138, 30, 178, -6, C0)
    body = union(circle_path(14, 22, 136), circle_path(-62, -56, 78), oval_path(-44, -120, 70, 70))
    blob(cv, body, C0, L0, shade=0xF1A89C)
    # 식도 꼬리 끝
    cv.drawOval(skia.Rect.MakeXYWH(-80, -158, 52, 30), P(0xE88A80, a=170))
    face(cv, 14, 18, 1.0, mood, blush=0xFFB3C1)
    # 넥타이 + 사원증
    tie = skia.Path(); tie.moveTo(0, 88); tie.lineTo(30, 88); tie.lineTo(38, 112); tie.lineTo(15, 146); tie.lineTo(-8, 112); tie.close()
    cv.drawPath(tie, P(0x3D8BFF)); cv.drawPath(tie, P(INK, "stroke", 5))
    cv.drawRect(skia.Rect.MakeXYWH(2, 78, 26, 16), P(0x2C6FD6)); cv.drawRect(skia.Rect.MakeXYWH(2, 78, 26, 16), P(INK, "stroke", 4))
    cv.drawLine(-60, 58, -92, 100, P(INK, "stroke", 5))
    rrect(cv, -122, 96, 54, 66, 10, fill=WHITE, stroke=INK, sw=5)
    cv.drawCircle(-95, 120, 11, P(0xF5C842)); cv.drawLine(-112, 143, -78, 143, P(INK, "stroke", 4))
    cv.restore()
