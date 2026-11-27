"""관문 ① 정지 화면 3장: 사람 비례 실루엣 + 그림자 + 모션 그래픽. python3 still.py A|B|C [out.png]
색은 RGB float(0..1), 마지막에 BGR로. 고정 시드."""
import sys, math, numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont
sys.path.insert(0, '.')
import hum

W, H = 1920, 1080
KR = '/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc'; KRB = '/usr/share/fonts/opentype/noto/NotoSansCJK-Black.ttc'
rng = np.random.default_rng(7)
V = lambda *c: np.array(c, np.float32)


def grad(c0, c1, vertical=True, n=None):
    t = np.linspace(0, 1, H if vertical else W, dtype=np.float32)
    g = V(*c0)[None] * (1 - t[:, None]) + V(*c1)[None] * t[:, None]
    return np.repeat(g[:, None, :], W, 1) if vertical else np.repeat(g[None], H, 0)


def text(s, px, font=KRB, track=0):
    f = ImageFont.truetype(font, int(px), index=1); ws = [f.getlength(c) + track for c in s]
    im = Image.new('L', (int(sum(ws)) + 16, int(px * 1.45)), 0); d = ImageDraw.Draw(im); x = 8
    for c, cw in zip(s, ws): d.text((x, 0), c, 255, font=f); x += cw
    return np.asarray(im, np.float32) / 255


def put(img, m, x, y, col, a=1.0):
    h, w = m.shape; x0, y0 = int(x), int(y)
    xa, ya = max(0, x0), max(0, y0); xb, yb = min(W, x0 + w), min(H, y0 + h)
    if xb <= xa or yb <= ya: return
    mm = m[ya - y0:yb - y0, xa - x0:xb - x0, None] * a
    img[ya:yb, xa:xb] = img[ya:yb, xa:xb] * (1 - mm) + V(*col) * mm


def lerp(img, tgt, a): return img * (1 - a[..., None]) + tgt * a[..., None]
def vig(img, k=0.55):
    y, x = np.mgrid[0:H, 0:W].astype(np.float32); r = ((x - W / 2) / (W / 2)) ** 2 + ((y - H / 2) / (H / 2)) ** 2
    return img * (1 - k * np.clip(r - 0.25, 0, 1.2) ** 1.2)[..., None]
def grain(img, k=0.018): return img + rng.normal(0, k, img.shape).astype(np.float32)
def rim(mask, d, col, blur=2.2, k=1.0):
    sh = np.roll(np.roll(mask, d[1], 0), d[0], 1); r = np.clip(mask - sh, 0, 1); return cv2.GaussianBlur(r, (0, 0), blur) * k
def addc(img, a, col): return img + a[..., None] * V(*col)


def layer_draw(fn):
    L = np.zeros((H, W, 3), np.uint8); fn(L); return L.astype(np.float32) / 255


def streaks(n, vec, lenr, thick, col, seed, spread=(0, W, 0, H)):
    r = np.random.default_rng(seed)
    def f(L):
        for _ in range(n):
            x = r.uniform(spread[0], spread[1]); y = r.uniform(spread[2], spread[3]); l = r.uniform(*lenr)
            c = tuple(int(255 * v * r.uniform(0.4, 1)) for v in col)
            cv2.line(L, (int(x), int(y)), (int(x + vec[0] * l), int(y + vec[1] * l)), c, int(r.integers(thick[0], thick[1] + 1)), cv2.LINE_AA)
    return layer_draw(f)


# ───────────── A: 무중력 근접 ─────────────
def still_A():
    img = grad((0.02, 0.03, 0.09), (0.07, 0.05, 0.17))
    y, x = np.mgrid[0:H, 0:W].astype(np.float32)
    img += np.exp(-(((x - 1000) / 760) ** 2 + ((y - 520) / 440) ** 2))[..., None] * V(0.05, 0.03, 0.12)
    C = (1000, 560); TILT = -22
    def rings(L, th, alpha=1.0, planets=True, col=(0.85, 0.92, 1.0), radii=(250, 360, 500, 660, 850, 1070, 1320)):
        ca, sa = math.cos(math.radians(TILT)), math.sin(math.radians(TILT))
        for i, a in enumerate(radii):
            cv2.ellipse(L, C, (a, int(a * 0.30)), TILT, 0, 360, tuple(int(255 * v * alpha) for v in col), th, cv2.LINE_AA)
            if planets:
                ang = math.radians(40 + i * 53); px, py = a * math.cos(ang), a * 0.30 * math.sin(ang)
                cv2.circle(L, (int(C[0] + px * ca - py * sa), int(C[1] + px * sa + py * ca)), 5 + (i % 3) * 3, (255, int(210 * alpha), int(120 * alpha)), -1, cv2.LINE_AA)
    img = img + layer_draw(lambda L: rings(L, 1, 0.5)) * 0.30
    # 몸: 느슨하게 뜬 자세(위를 보고 누운 듯, 팔은 벌어지고 다리는 접힘)
    pose = dict(lean=5, nb=-4, hd=-8, uaN=48, faN=70, uaF=-24, faF=-4, thN=32, shN=-10, thF=-6, shF=-24, ftN=112, ftF=126)
    s = 4.6
    m, J, T = hum.sil(pose, W, H, 990, 560, s, rot=-14, rc=(0, 30), face=1)
    # 창 안: 우주에서 본 지구 한쪽 + 밝은 궤도선 + 별. 대각 그라데이션이 바탕
    gx = np.clip((x * 0.6 + (H - y) * 0.9) / (W * 0.6 + H * 0.9), 0, 1)[..., None]
    win = V(0.05, 0.75, 1.0)[None, None] * (1 - gx) + V(1.0, 0.25, 0.55)[None, None] * gx
    win = win * 0.95 + 0.10 * V(1, 0.9, 0.7)
    earth = ((x - 1000) ** 2 + (y - 1890) ** 2 < 1330 ** 2).astype(np.float32); earth = cv2.GaussianBlur(earth, (0, 0), 2)
    d = np.sqrt((x - 1000) ** 2 + (y - 1890) ** 2); limb = np.exp(-np.clip(d - 1330, 0, None) / 26) * (d >= 1330) + np.exp(-np.clip(1330 - d, 0, None) / 14) * (d < 1330)
    cl = cv2.GaussianBlur(rng.normal(0, 1, (H, W)).astype(np.float32), (0, 0), 14); eb = V(0.20, 0.55, 0.98)[None, None] * (0.95 + 0.30 * np.clip(cl * 14, -1, 1))[..., None]
    win = lerp(win, eb, earth * 0.95); win = addc(win, limb * 0.9, (0.35, 0.85, 1.0))
    win = np.clip(win, 0, 1)
    inL = layer_draw(lambda L: rings(L, 3, 1.0, True, (1.0, 1.0, 1.0), (430, 760, 1250))); inL = inL + cv2.GaussianBlur(inL, (0, 0), 6) * 0.8
    win = np.clip(win + inL * 0.9, 0, 1)
    star = layer_draw(lambda L: [cv2.circle(L, (int(rng.uniform(0, W)), int(rng.uniform(0, H * 0.7))), int(rng.integers(1, 4)), (255, 255, 255), -1, cv2.LINE_AA) for _ in range(220)])
    win = np.clip(win + star, 0, 1)
    img = lerp(img, win, m)
    g = cv2.GaussianBlur(m, (0, 0), 22) * (1 - m); img = addc(img, g, (0.04, 0.38, 0.62))
    img = addc(img, rim(m, (4, -4), None, 2.0, 1.0), (0.9, 0.95, 1.0))
    img += streaks(70, (math.cos(math.radians(TILT)), math.sin(math.radians(TILT))), (20, 80), (1, 2), (0.8, 0.9, 1.0), 3) * 0.55
    t = text('안전하고 고요한 진공 속에서', 60, KR, 3); put(img, t, 110, 930, (0.96, 0.96, 1.0))
    put(img, np.ones((3, 520), np.float32), 120, 1005, (1.0, 0.35, 0.30))
    return img


# ───────────── B: 추락 한가운데 ─────────────
def still_B():
    y, x = np.mgrid[0:H, 0:W].astype(np.float32)
    D = (260, 190)                                              # 문(빛의 근원)
    d = np.sqrt((x - D[0]) ** 2 + (y - D[1]) ** 2)
    img = grad((0.07, 0.05, 0.20), (0.04, 0.03, 0.12))
    nz = cv2.GaussianBlur(rng.normal(0, 1, (H, W)).astype(np.float32), (0, 0), 2.5)
    lit = (0.52 + 0.48 * np.exp(-d / 760))[..., None]
    img = img * 0.4 + lit * V(1.0, 0.60, 0.42) * (1 + 0.05 * nz[..., None]) * 0.92
    # 빛줄기(문에서 퍼짐)
    def rays(L):
        r = np.random.default_rng(4)
        for _ in range(46):
            a = math.radians(r.uniform(-20, 80)); l = r.uniform(900, 2200); w = r.uniform(0.01, 0.045)
            p0 = (int(D[0]), int(D[1])); p1 = (int(D[0] + math.cos(a - w) * l), int(D[1] + math.sin(a - w) * l)); p2 = (int(D[0] + math.cos(a + w) * l), int(D[1] + math.sin(a + w) * l))
            cv2.fillConvexPoly(L, np.array([p0, p1, p2], np.int32), (int(255 * r.uniform(0.3, 1)),) * 3, cv2.LINE_AA)
    rl = cv2.GaussianBlur(layer_draw(rays), (0, 0), 4).max(2) * np.exp(-d / 1300)
    img = addc(img, rl * 0.28, (1.0, 0.85, 0.55))
    # 문: 밝은 사각형 + 열린 문짝
    def door(L):
        cv2.fillConvexPoly(L, np.array([[130, 60], [400, 40], [410, 340], [120, 330]], np.int32), (255, 255, 255), cv2.LINE_AA)
    dm = layer_draw(door).max(2)
    img = addc(img, cv2.GaussianBlur(dm, (0, 0), 38) * 0.9, (1.0, 0.7, 0.35))
    img = lerp(img, V(1.0, 0.97, 0.88) * np.ones_like(img), dm)
    leaf = layer_draw(lambda L: cv2.fillConvexPoly(L, np.array([[130, 60], [20, 110], [10, 400], [120, 330]], np.int32), (255, 255, 255), cv2.LINE_AA)).max(2)
    img = lerp(img, V(0.12, 0.07, 0.14) * np.ones_like(img), leaf)
    # 몸: 문을 막 빠져나와 머리부터 떨어진다
    bp = dict(lean=-4, nb=-6, hd=8, uaN=165, faN=148, uaF=128, faF=104, thN=-12, shN=-46, thF=16, shF=-22, ftN=-80, ftF=-60)
    s = 3.5; ox, oy = 930, 610
    m, J, T = hum.sil(bp, W, H, ox, oy, s, rot=146, rc=(0, -30), face=1)
    # 그림자: 문의 빛이 만든 것. 벽 아래쪽에 더 크게 선 채로, 두 팔을 들어 올려 몸을 붙잡으려 한다
    sp = dict(lean=-6, nb=-6, hd=-10, uaN=166, faN=172, uaF=170, faF=177, thN=4, shN=2, thF=-4, shF=-2, ftN=90, ftF=90)
    ms, Js, Ts = hum.sil(sp, W, H, 1500, 880, 4.4, rot=0, rc=(0, 0), face=-1)
    sh1 = cv2.GaussianBlur(ms, (0, 0), 6); sh2 = cv2.GaussianBlur(ms, (0, 0), 40) * 0.45
    wf = np.clip(1.25 - d / 2200, 0.7, 1)                      # 문에서 멀수록 조금 옅게
    a = np.clip((sh1 * 0.85 + sh2) * wf, 0, 0.95)
    img = img * (1 - a[..., None]) + a[..., None] * V(0.03, 0.01, 0.07)
    # 몸이 만드는 작은 그림자(바로 뒤 벽, 더 진하고 가깝다)
    near = hum.wall_shadow(m, (ox, oy), 1.12, 46, 38, 7) * 0.5
    img = img * (1 - near[..., None]) + near[..., None] * V(0.03, 0.01, 0.07)
    # 속도선(몸이 떨어지는 방향의 반대로)
    img += streaks(50, (-0.62, -0.78), (160, 520), (1, 2), (1.0, 0.85, 0.65), 11, (500, W, 300, H)) * 0.38
    # 유리 조각(문 부근에서 흩어져 나옴)
    def shards(L):
        r = np.random.default_rng(5)
        for _ in range(16):
            cx, cy = D[0] + r.uniform(60, 1000), D[1] + r.uniform(-20, 680) * r.uniform(0.2, 1); sz = r.uniform(24, 86)
            pts = np.array([[cx + r.uniform(-1, 1) * sz, cy + r.uniform(-1, 1) * sz * 0.6] for _ in range(3)], np.int32)
            cv2.fillConvexPoly(L, pts, (255, 245, 225), cv2.LINE_AA)
    shl = cv2.GaussianBlur(layer_draw(shards), (0, 0), 0.7); img = img * (1 - shl.max(2, keepdims=True) * 0.6) + shl * 0.6
    body = V(0.03, 0.025, 0.07)
    img = lerp(img, np.broadcast_to(body, img.shape), m)
    img = addc(img, rim(m, (-5, -5), None, 2.2, 1.3), (1.0, 0.72, 0.40))
    t1 = text('이제 문을 열고', 74, KR, 3); t2 = text('떨어져 내려', 168, KRB, 2)
    ghost = cv2.GaussianBlur(t2, (0, 0), sigmaX=1, sigmaY=22); ghost = np.maximum(ghost, cv2.GaussianBlur(np.roll(t2, 70, 0), (0, 0), sigmaX=1, sigmaY=26) * 0.85)
    put(img, t1, 92, 700, (1.0, 0.98, 0.92)); put(img, ghost, 84, 770 - 30, (1.0, 0.82, 0.25), 0.7); put(img, t2, 84, 770, (1.0, 0.82, 0.25))
    return img


# ───────────── C: 착지 ─────────────
def still_C():
    img = grad((0.99, 0.55, 0.42), (1.0, 0.92, 0.72))        # 위=붉은 새벽, 아래=지평선 근처 밝음
    y, x = np.mgrid[0:H, 0:W].astype(np.float32); yf = 735
    sun = np.exp(-(((x - 1530) / 330) ** 2 + ((y - 640) / 260) ** 2)); img = addc(img, sun, (0.35, 0.28, 0.15))
    # 바닥
    fl = (y > yf).astype(np.float32); t = np.clip((y - yf) / (H - yf), 0, 1)
    ground = V(0.62, 0.34, 0.26)[None, None] * (1 - t[..., None]) + V(0.30, 0.15, 0.14)[None, None] * t[..., None]
    gn = cv2.GaussianBlur(rng.normal(0, 1, (H, W)).astype(np.float32), (0, 0), 2.2); ground = ground * (1 + 0.5 * gn[..., None])
    img = lerp(img, ground, cv2.GaussianBlur(fl, (0, 0), 1.2))
    cx = 930
    # 균열: 접촉점에서 퍼지는 갈라진 금 + 속에서 새는 열
    def cracks(L, glow):
        r = np.random.default_rng(21)
        for k in range(15):
            ang = math.radians(r.uniform(-12, 192)) if k < 12 else math.radians(r.uniform(160, 380))
            pts = []; px, py = cx, yf + 22
            for j in range(10):
                step = r.uniform(60, 150) * (1 + j * 0.12); ang += r.uniform(-0.28, 0.28)
                px += math.cos(ang) * step; py += math.sin(ang) * step * 0.22
                pts.append([px, py])
            pts = np.array([[cx, yf + 22]] + pts, np.int32)
            col = (255, 150, 60) if glow else (255, 255, 255)
            cv2.polylines(L, [pts], False, col, 3 if glow else 1, cv2.LINE_AA)
    cg = layer_draw(lambda L: cracks(L, True)); cg = cv2.GaussianBlur(cg, (0, 0), 2.2) + cv2.GaussianBlur(cg, (0, 0), 9) * 0.6
    img = img + cg * (fl[..., None]) * 0.95
    cd = layer_draw(lambda L: cracks(L, False)).max(2); img = img * (1 - cd[..., None] * 0.7 * fl[..., None])
    # 충격파 고리
    def ring(L):
        for R, th, c in [(520, 7, (255, 245, 220)), (430, 3, (255, 160, 80)), (610, 2, (255, 200, 140))]:
            cv2.ellipse(L, (cx, yf + 22), (R, int(R * 0.17)), 0, 190, 350, c, th, cv2.LINE_AA)
            cv2.ellipse(L, (cx, yf + 22), (R, int(R * 0.17)), 0, 10, 170, c, th, cv2.LINE_AA)
    rg = layer_draw(ring); img = img + cv2.GaussianBlur(rg, (0, 0), 6) * 0.9 + rg * 0.9
    # 몸(착지 자세): 발바닥이 yf에 닿게 oy 계산
    cp = dict(lean=38, nb=-14, hd=6, uaN=75, faN=105, uaF=-22, faF=-10, thN=74, shN=-22, thF=62, shF=-30, ftN=90, ftF=90)
    s = 4.9; J0 = hum.fk(cp, 1); low = max(J0['ON'][1], J0['OF'][1], J0['HN'][1], J0['HF'][1]) + 3.0; oy = yf + 22 - low * s
    m, J, T = hum.sil(cp, W, H, cx - 40, oy, s, face=1)
    # 그림자: 해 쪽(오른쪽 뒤)에서 와 왼쪽·앞으로 길게 눕는다. 접촉점에서 멀수록 번진다
    sp = dict(lean=-3, nb=-4, hd=-10, uaN=34, faN=52, uaF=-30, faF=-40, thN=1, shN=0, thF=-2, shF=0, ftN=90, ftF=90)
    J1 = hum.fk(sp, 1); oy1 = yf + 22 - (max(J1['ON'][1], J1['OF'][1]) + 3.0) * s
    m2, _, _ = hum.sil(sp, W, H, cx - 40, oy1, s, face=1)
    shd = hum.floor_shadow(m2, yf + 22, -0.95, 0.40, cx - 20, soft=(3.0, 20), reach=700.0)
    shd = shd * fl; img = img * (1 - shd[..., None] * 0.88) + shd[..., None] * 0.88 * V(0.06, 0.015, 0.10)
    # 그림자 위에 얹히는 글자(바닥에 눕는다)
    t = text('거칠게 부딪힌 내 세상의 바닥', 118, KRB, 2); th, tw = t.shape
    A = np.float32([[1, -0.55, 0.55 * 0], [0, 0.40, 0]]); tt = cv2.warpAffine(t, np.float32([[1, 0.0, 0], [0, 0.34, 0]]), (tw, int(th * 0.34) + 1))
    tt = cv2.warpAffine(tt, np.float32([[1, -0.42, 0.42 * tt.shape[0]], [0, 1, 0]]), (tw + 200, tt.shape[0]))
    put(img, cv2.GaussianBlur(tt, (0, 0), 7), 70, 880, (1.0, 0.55, 0.25), 0.55); put(img, tt, 70, 880, (1.0, 0.95, 0.80))
    # 몸
    img = lerp(img, np.broadcast_to(V(0.03, 0.02, 0.06), img.shape), m)
    img = addc(img, rim(m, (6, -3), None, 2.0, 1.1), (1.0, 0.85, 0.55))
    # 파편
    def deb(L):
        r = np.random.default_rng(9)
        for _ in range(80):
            px = cx + r.normal(0, 340); py = yf - abs(r.normal(0, 190)) ; l = r.uniform(5, 26)
            cv2.line(L, (int(px), int(py)), (int(px + r.uniform(-0.4, 0.4) * l), int(py + l)), (255, int(170 * r.uniform(0.5, 1)), 70), int(r.integers(2, 6)), cv2.LINE_AA)
    img = img + layer_draw(deb) * 0.9
    return img


if __name__ == '__main__':
    k = sys.argv[1]; out = sys.argv[2] if len(sys.argv) > 2 else f'/home/claude/work/gv/h/still_{k}.png'
    img = {'A': still_A, 'B': still_B, 'C': still_C}[k]()
    img = grain(vig(img, 0.5 if k != 'C' else 0.42))
    cv2.imwrite(out, np.clip(img[..., ::-1] * 255, 0, 255).astype(np.uint8))
