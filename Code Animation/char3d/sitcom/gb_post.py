# 시트콤 파일럿 합본: 컷 프레임(960×540) → 1920×1080 확대 + 컷별 후처리(되감기·인터뷰·화상·어둡게) + 2D 칩·자막 + 소리
# 사용: python3 gb_post.py <tl.json> <컷 프레임 폴더> <mix.wav> <out.mp4> [--still 초,초,...]
import sys, json, math, subprocess, importlib.util, numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
tl, CD, WAV, OUT = sys.argv[1:5]
STILL = [float(x) for x in sys.argv[sys.argv.index('--still') + 1].split(',')] if '--still' in sys.argv else None
HERE = __file__.rsplit('/', 1)[0]
TL = json.load(open(tl)); W, H, FPS = 1920, 1080, 24
FONT = f'{HERE}/Jua-Regular.ttf'
INK, WHITE = (38, 48, 79), (255, 255, 255)
_fc = {}
def F(sz): return _fc.setdefault(sz, ImageFont.truetype(FONT, sz))

# Jua에 없는 기호(·…→①…)는 Noto Sans CJK로 섞어 그린다(그냥 쓰면 네모로 나옴)
from fontTools.ttLib import TTFont
JUA = set(TTFont(FONT).getBestCmap()); FB = '/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc'; _fb = {}
def FBF(sz): return _fb.setdefault(sz, ImageFont.truetype(FB, int(sz * 0.9), index=1))
def runs(line, sz):
    out = []
    for ch in line:
        f = F(sz) if (ord(ch) in JUA or ch == ' ') else FBF(sz)
        if out and out[-1][1] is f: out[-1][0] += ch
        else: out.append([ch, f])
    return out
def lw(line, sz): return sum(f.getlength(t) for t, f in runs(line, sz))
def msize(s, sz): ls = s.split('\n'); return int(max(lw(l, sz) for l in ls)), int(sz * (1.25 * (len(ls) - 1) + 1.0))
def mtext(d, x, y, s, sz, fill, align='left', stroke=0, sfill=None, anchor='la'):
    ls = s.split('\n'); w, h = msize(s, sz)
    if anchor[0] == 'm': x -= w / 2
    if anchor[1] == 'm': y -= h / 2
    for i, l in enumerate(ls):
        xx = x + ((w - lw(l, sz)) / 2 if align == 'center' else 0); yb = y + i * sz * 1.25 + sz * 0.86
        for t, f in runs(l, sz):
            d.text((xx, yb), t, font=f, fill=fill, anchor='ls', stroke_width=stroke, stroke_fill=sfill); xx += f.getlength(t)
LINES = json.loads(open(f'{HERE}/lines.js').read().split('=', 1)[1].strip().rstrip(';'))
SUB = {'일일구': '119', '삼십 분': '30분', '사십 분': '40분', '한 시간에서 다섯 시간': '1시간에서 5시간', '세 시간째': '3시간째'}
def disp(t):
    for a, b in SUB.items(): t = t.replace(a, b)
    return t
COL = {2: (142, 224, 192), 3: (244, 190, 99), 5: (255, 214, 190), 1: (255, 159, 178), 0: (200, 190, 255)}
T0 = {}; t = 0.0
for c in TL: T0[c['id']] = t; t += c['dur']
TOTAL = t

def ease_out(u): u = min(1, max(0, u)); return 1 - (1 - u) ** 3
def pop(lt, dur):   # 등장·퇴장 스케일/알파
    a = ease_out(lt / 0.22) * (1 - ease_out((lt - dur + 0.2) / 0.2)) if dur < 90 else ease_out(lt / 0.22)
    s = 0.85 + 0.15 * ease_out(lt / 0.22) + 0.05 * math.sin(min(1, lt / 0.3) * math.pi)
    return max(0, min(1, a)), s
def text_size(d, s, f): return msize(s, f.size)
def chip(txt, sz, bg, fg=INK, pad=(34, 20), rad=28, src=None, bar=None, align='left'):
    f = F(sz); d0 = ImageDraw.Draw(Image.new('RGBA', (8, 8))); tw, th = text_size(d0, txt, f)
    sw, sh = (0, 0)
    if src: fs = F(int(sz * 0.52)); sw, sh = text_size(d0, '출처: ' + src, fs)
    w = max(tw, sw) + pad[0] * 2 + (16 if bar else 0); h = th + pad[1] * 2 + (sh + 12 if src else 0) + 8
    im = Image.new('RGBA', (w + 24, h + 28), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    sh_im = Image.new('RGBA', im.size, (0, 0, 0, 0)); ImageDraw.Draw(sh_im).rounded_rectangle((10, 16, w + 10, h + 16), rad, fill=(20, 20, 50, 90)); im = Image.alpha_composite(im, sh_im.filter(ImageFilter.GaussianBlur(7))); d = ImageDraw.Draw(im)
    d.rounded_rectangle((4, 4, w + 4, h + 4), rad, fill=bg)
    x0 = 4 + pad[0] + (16 if bar else 0)
    if bar: d.rounded_rectangle((14, 18, 24, h - 10), 5, fill=bar)
    mtext(d, x0, 4 + pad[1], txt, sz, fg, align)
    if src: mtext(d, x0, 4 + pad[1] + th + 14, '출처: ' + src, int(sz * 0.52), (110, 110, 140))
    return im
def outlined(txt, sz, fg=WHITE, st=INK, sw=7, maxw=1700):
    f = F(sz); d0 = ImageDraw.Draw(Image.new('RGBA', (8, 8)))
    words = txt.split(' '); lines = ['']
    for w_ in words:
        cand = (lines[-1] + ' ' + w_).strip()
        if text_size(d0, cand, f)[0] > maxw and lines[-1]: lines.append(w_)
        else: lines[-1] = cand
    s = '\n'.join(lines); tw, th = text_size(d0, s, f)
    im = Image.new('RGBA', (tw + sw * 4, th + sw * 4 + 10), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    mtext(d, sw * 2, sw * 2, s, sz, fg, 'center', sw, st)
    return im
def paste(base, im, cx, cy, a=1.0, s=1.0, anchor='c'):
    if a <= 0.01: return
    if abs(s - 1) > 0.01: im = im.resize((max(1, int(im.width * s)), max(1, int(im.height * s))), Image.LANCZOS)
    if a < 0.99: al = im.getchannel('A').point(lambda v: int(v * a)); im = im.copy(); im.putalpha(al)
    x = int(cx - im.width / 2) if anchor in 'c' else int(cx) if anchor == 'l' else int(cx - im.width)
    y = int(cy - im.height / 2)
    base.alpha_composite(im, (max(0, x), max(0, y)))

_cache = {}
def C(key, fn):
    if key not in _cache: _cache[key] = fn()
    return _cache[key]

def draw_ov(base, ov, lt, cid):
    kind, at, dur = ov[0], ov[1], ov[2]
    a, s = pop(lt, dur)
    if kind == 'cap':
        im = C(('cap', ov[3]), lambda: chip('⏱ ' + ov[3] if False else ov[3], 46, (38, 48, 79, 235), WHITE, pad=(30, 14), rad=20))
        paste(base, im, 60, 90, a, 1, 'l')
    elif kind == 'q':
        im = C(('q', ov[3]), lambda: chip(ov[3], 50, (255, 255, 255, 245), INK, pad=(40, 24), rad=34, bar=(232, 80, 91)))
        paste(base, im, W / 2, 150, a, s)
    elif kind == 'name':
        sid = {'장': 2, '간': 3, '뇌': 5, '심장': 1}[ov[3].split(' ')[0]]
        im = C(('name', ov[3]), lambda: chip(ov[3], 46, COL[sid] + (245,), INK, pad=(30, 14), rad=24))
        paste(base, im, 70, 770, a, s, 'l')
    elif kind == 'tag':
        im = C(('tag', ov[3]), lambda: chip(ov[3], 40, (255, 243, 192, 240), INK, pad=(26, 12), rad=18))
        paste(base, im, W - 60, 90, a, 1, 'r')
    elif kind == 'def':
        im = C(('def', ov[3]), lambda: chip(ov[3], 46, (255, 250, 230, 245), INK, pad=(32, 16), rad=24, bar=(60, 199, 180)))
        paste(base, im, W / 2, 790, a, s)
    elif kind == 'chip':
        im = C(('chip', ov[3]), lambda: chip(ov[3], 50, (255, 255, 255, 248), INK, pad=(40, 24), rad=30, src=ov[4], bar=(90, 74, 208)))
        paste(base, im, W / 2, 175, a, s)
    elif kind == 'ans':
        def mk():
            big = outlined('30분', 150, (232, 80, 91), WHITE, 10)
            body = chip('넘게 계속되면 체기가 아닐 수 있음 → 당일 진료', 50, (255, 255, 255, 250), INK, pad=(40, 22), rad=30, src='NHS 담석 안내 · 2025년 검토', bar=(232, 80, 91))
            im = Image.new('RGBA', (max(big.width, body.width), big.height + body.height - 10), (0, 0, 0, 0))
            im.alpha_composite(big, ((im.width - big.width) // 2, 0)); im.alpha_composite(body, ((im.width - body.width) // 2, big.height - 10)); return im
        im = C(('ans',), mk); paste(base, im, W / 2, 255, a, s + 0.08 * math.exp(-lt * 6))
    elif kind == 'bullet':
        def mk():
            txt = ('담석 통증이 생기는 이유\n'
                   '• 기름진 음식이 들어오면 담낭이 담즙을 내보내려고\n   수축하는 것으로 알려져 있어요\n'
                   '• 돌이 담관을 막으면 담즙이 고여 통증(담석 산통)이 생겨요\n'
                   '• 돌이 자리를 옮기면 발작이 멎어요\n'
                   '• 몇 시간 넘게 막히면 담낭·간·췌장에 염증·감염 같은\n   합병증이 생길 수 있어요')
            return chip(txt, 38, (255, 255, 255, 245), INK, pad=(42, 24), rad=30, src='NIDDK 담석 증상·원인', bar=(90, 74, 208))
        im = C(('bullet',), mk); paste(base, im, W / 2, 800, a, s)
    elif kind == 'cards':
        items = ['열·오한', '피부·눈 흰자가 노래짐', '짙은 소변·흰 변']
        head = C(('cardh',), lambda: chip('이럴 땐 바로 병원', 50, (232, 80, 91, 250), WHITE, pad=(36, 18), rad=26))
        paste(base, head, 1450, 120, a, s)
        for i, it in enumerate(items):
            u = (lt - 0.05 - i * 0.4) / 0.35
            if u <= 0: continue
            card = C(('card', it), lambda it=it: chip(it, 50, (255, 236, 236, 250), (180, 40, 50), pad=(34, 20), rad=22, bar=(232, 80, 91)))
            y = 250 + i * 120 - 300 * (1 - ease_out(u)); paste(base, card, 1450 + (i - 1) * 30, y, a * min(1, u * 2), 1)
        src = C(('cardsrc',), lambda: chip('출처: ' + ov[3], 28, (255, 255, 255, 220), (100, 100, 130), pad=(20, 8), rad=14))
        paste(base, src, 1450, 610, a * min(1, max(0, (lt - 1.0) / 0.3)), 1)
    elif kind == 'summary':
        def mk():
            p = Image.new('RGBA', (1460, 820), (0, 0, 0, 0)); d = ImageDraw.Draw(p)
            d.rounded_rectangle((0, 0, 1460, 820), 44, fill=(255, 253, 246, 250))
            mtext(d, 730, 82, '오늘의 3가지 · 담석 신호', 64, INK, anchor='mm')
            rows = [('① 구별', '명치·오른쪽 갈비뼈 아래가 30분 넘게 계속,\n화장실·방귀·구토로 안 풀림', (60, 160, 120)),
                    ('② 행동', '30분 넘으면 당일 진료 · 극심하면 119\n열·황달·짙은 소변이면 바로 병원', (232, 80, 91)),
                    ('③ 멎어도', '또 올 수 있어요 → 진료 예약\n가슴까지 조이면 헷갈리지 말고 119', (90, 74, 208))]
            for i, (h, b, col) in enumerate(rows):
                y = 170 + i * 200; d.rounded_rectangle((60, y, 1400, y + 175), 26, fill=tuple(int(255 * 0.86 + v * 0.14) for v in col) + (255,))
                mtext(d, 100, y + 87, h, 56, col, anchor='lm'); mtext(d, 420, y + 87, b, 46, INK, anchor='lm')
            mtext(d, 730, 790, '출처: NHS · NHS 웨일스 111 · NIDDK', 28, (110, 110, 140), anchor='mm')
            return p
        im = C(('summary',), mk); paste(base, im, W / 2, H / 2, a, s)
    elif kind == 'title':
        def mk():
            a1 = outlined('몸속 주식회사', 120, WHITE, INK, 9); a2 = chip('오늘의 판정 · 치킨 먹고 오른쪽 윗배가 쥐어짠다면?', 48, (255, 214, 106, 250), INK, pad=(36, 16), rad=26)
            im = Image.new('RGBA', (max(a1.width, a2.width), a1.height + a2.height), (0, 0, 0, 0)); im.alpha_composite(a1, ((im.width - a1.width) // 2, 0)); im.alpha_composite(a2, ((im.width - a2.width) // 2, a1.height - 6)); return im
        im = C(('title',), mk); paste(base, im, W / 2, H / 2 - 40, a, s)

def post(img, kind, lt):
    if kind == 'flashback':
        g = img.convert('L').convert('RGB'); sep = Image.merge('RGB', [c.point(lambda v, k=k: min(255, int(v * k))) for c, k in zip(g.split(), (1.08, 1.0, 0.86))])
        arr = np.asarray(sep).astype(np.float32); arr[::4] *= 0.82
        yy, xx = np.mgrid[0:H, 0:W]; vig = 1 - 0.45 * (((xx - W / 2) / (W / 2)) ** 2 + ((yy - H / 2) / (H / 2)) ** 2); arr *= np.clip(vig, 0.4, 1)[..., None]
        band = int((lt * 300) % (H + 120)) - 60; arr[max(0, band):band + 40] = arr[max(0, band):band + 40] * 0.7 + 60
        out = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8)).convert('RGBA')
        d = ImageDraw.Draw(out); mtext(d, W - 70 - msize('◀◀ 되감기', 54)[0], 70, '◀◀ 되감기', 54, WHITE, stroke=5, sfill=INK)
        return out
    if kind == 'interview':
        bl = img.filter(ImageFilter.GaussianBlur(9)); m = Image.new('L', (W, H), 0); ImageDraw.Draw(m).ellipse((W * 0.22, H * 0.02, W * 0.78, H * 1.05), fill=255)
        return Image.composite(img, bl, m.filter(ImageFilter.GaussianBlur(70)))
    if kind == 'call':
        bg = Image.new('RGBA', (W, H), (30, 26, 60, 255)); inner = img.resize((int(W * 0.84), int(H * 0.84)), Image.LANCZOS)
        mk = Image.new('L', inner.size, 0); ImageDraw.Draw(mk).rounded_rectangle((0, 0, inner.width, inner.height), 40, fill=255); bg.paste(inner, ((W - inner.width) // 2, (H - inner.height) // 2 + 20), mk)
        d = ImageDraw.Draw(bg); d.ellipse((150, 52, 178, 80), fill=(90, 230, 120)); mtext(d, 195, 66, '연결됨 · 펌프 공장 ↔ 관제실', 40, WHITE, anchor='lm')
        return bg
    if kind == 'dim':
        return Image.blend(img, Image.new('RGBA', (W, H), (20, 18, 40, 255)), 0.45)
    return img

def subtitle(base, cid, lt):
    for lid, at in next(c for c in TL if c['id'] == cid)['lines']:
        L = LINES[lid]; d = lt - at
        if 0 <= d < L['dur'] - 0.15:
            im = C(('sub', lid), lambda: outlined(disp(L['text']), 54, WHITE, INK, 7))
            a = min(1, d / 0.12, (L['dur'] - 0.15 - d) / 0.12); paste(base, im, W / 2, 985, a, 1)

def frame_at(g):
    for c in TL:
        if g < T0[c['id']] + c['dur'] - 1e-6: break
    cid = c['id']; lt = g - T0[cid]; k = min(int(round(lt * FPS)), int(round(c['dur'] * FPS)) - 1)
    src = Image.open(f'{CD}/{cid}_f/{k:05d}.jpg').convert('RGB').resize((W, H), Image.LANCZOS).convert('RGBA')
    img = post(src, c['post'], lt)
    for ov in c['ov']:
        at, dur = ov[1], ov[2]
        if ov[0] == 'q':   # 질문 칩은 K03 시작 전까지 이어서 보여 줌
            if cid in ('K01', 'K02') and (cid == 'K02' or lt >= at): draw_ov(img, ov, (g - T0['K01'] - at), cid)
            continue
        if at <= lt < at + min(dur, c['dur'] - at + 0.0): draw_ov(img, ov, lt - at, cid)
    if cid == 'K02':
        for ov in next(x for x in TL if x['id'] == 'K01')['ov']:
            if ov[0] == 'q': draw_ov(img, ov, g - T0['K01'] - ov[1], 'K02')
    if cid != 'K42': subtitle(img, cid, lt)
    return img.convert('RGB')

if STILL:
    for g in STILL: frame_at(g).save(f'{OUT}_{g:.2f}.jpg', quality=90); print('still', g)
    sys.exit()
N = int(round(TOTAL * FPS))
ff = subprocess.Popen(['ffmpeg', '-y', '-v', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-', '-i', WAV,
                       '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '19', '-pix_fmt', 'yuv420p', '-af', 'loudnorm=I=-14:TP=-1.5:LRA=11', '-ar', '48000', '-c:a', 'aac', '-b:a', '192k', '-shortest', '-movflags', '+faststart', OUT], stdin=subprocess.PIPE)
for i in range(N):
    ff.stdin.write(frame_at(i / FPS + 1e-4).tobytes())
    if i % 240 == 0: print('frame', i, '/', N, flush=True)
ff.stdin.close(); ff.wait(); print('done', OUT)
