"""종이 오림 모양(cairo 경로) — 단위 좌표(그림 반지름 1 안팎)."""
import math
import cairo


def circle(cr, x, y, r):
    cr.new_sub_path(); cr.arc(x, y, max(r, 1e-4), 0, 2 * math.pi)


def ellipse(cr, x, y, rx, ry, ang=0.0):
    cr.save(); cr.translate(x, y); cr.rotate(ang); cr.scale(max(rx, 1e-4), max(ry, 1e-4))
    cr.new_sub_path(); cr.arc(0, 0, 1, 0, 2 * math.pi); cr.restore()


def leaf(cr, x, y, L, w, ang):
    """잎/꽃잎: 밑동 (x,y)에서 ang 방향으로 길이 L, 폭 w."""
    cr.save(); cr.translate(x, y); cr.rotate(ang)
    cr.new_sub_path(); cr.move_to(0, 0)
    cr.curve_to(L * 0.3, -w, L * 0.75, -w * 0.8, L, 0)
    cr.curve_to(L * 0.75, w * 0.8, L * 0.3, w, 0, 0)
    cr.close_path(); cr.restore()


def drop(cr, x, y, s):
    cr.new_sub_path(); cr.move_to(x, y - s * 1.6)
    cr.curve_to(x + s * 0.9, y - s * 0.4, x + s, y + s * 0.2, x, y + s)
    cr.curve_to(x - s, y + s * 0.2, x - s * 0.9, y - s * 0.4, x, y - s * 1.6)
    cr.close_path()


def bar(cr, x0, y0, x1, y1, w):
    """두께 w의 곧은 띠(가지·줄기)."""
    dx, dy = x1 - x0, y1 - y0; L = math.hypot(dx, dy) or 1e-6
    nx, ny = -dy / L * w / 2, dx / L * w / 2
    cr.new_sub_path(); cr.move_to(x0 + nx, y0 + ny); cr.line_to(x1 + nx, y1 + ny)
    cr.line_to(x1 - nx, y1 - ny); cr.line_to(x0 - nx, y0 - ny); cr.close_path()


def flake(cr, x, y, r, w, rot=0.0):
    """눈송이: 6팔 + 곁가지."""
    for k in range(6):
        a = rot + k * math.pi / 3
        ex, ey = x + math.cos(a) * r, y + math.sin(a) * r
        bar(cr, x, y, ex, ey, w)
        for f in (0.55,):
            mx, my = x + math.cos(a) * r * f, y + math.sin(a) * r * f
            for s in (-1, 1):
                b = a + s * 0.7
                bar(cr, mx, my, mx + math.cos(b) * r * 0.35, my + math.sin(b) * r * 0.35, w * 0.8)


def wave(cr, x0, x1, y, amp, wl, th, ph=0.0, n=40):
    """물결 띠."""
    pts_t = [(x0 + (x1 - x0) * i / n, y + amp * math.sin((i / n) * (x1 - x0) / wl * 2 * math.pi + ph) - th / 2) for i in range(n + 1)]
    pts_b = [(x, yy + th) for x, yy in pts_t[::-1]]
    cr.new_sub_path(); cr.move_to(*pts_t[0])
    for p in pts_t[1:] + pts_b: cr.line_to(*p)
    cr.close_path()


def poly(cr, pts):
    cr.new_sub_path(); cr.move_to(*pts[0])
    for p in pts[1:]: cr.line_to(*p)
    cr.close_path()


def ring(cr, x, y, r0, r1):
    cr.new_sub_path(); cr.arc(x, y, r1, 0, 2 * math.pi)
    cr.new_sub_path(); cr.arc_negative(x, y, r0, 2 * math.pi, 0)   # 반대 방향 → 감김 규칙에서도 구멍


def sector(cr, x, y, r, a0, a1):
    """화면 각도(라디안, 반시계 = 수학 방향, y는 위가 +)로 부채꼴."""
    cr.new_sub_path(); cr.move_to(x, y)
    n = max(4, int(abs(a1 - a0) / 0.05))
    for i in range(n + 1):
        a = a0 + (a1 - a0) * i / n
        cr.line_to(x + r * math.cos(a), y - r * math.sin(a))
    cr.close_path()


def fill(cr, rgb, a=1.0, holes=False):
    """겹친 조각은 합쳐 칠한다(holes=True면 겹친 곳이 오려진 구멍)."""
    cr.set_source_rgba(rgb[0], rgb[1], rgb[2], a)
    cr.set_fill_rule(cairo.FILL_RULE_EVEN_ODD if holes else cairo.FILL_RULE_WINDING); cr.fill()
