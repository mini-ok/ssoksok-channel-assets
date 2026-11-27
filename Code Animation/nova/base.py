"""허상공방 지식 쇼츠 2기 공용 바탕. 편마다 화풍·소리는 ep_*.py가 직접 그린다.
여기에는 화면 크기, 글자, 카드(영어 위·한글 아래), 마무리 문장(coda), 끝 화면, 렌더 CLI만 둔다.

ep 모듈이 정의할 것: EP = dict(DUR, t_coda, coda=[(en, ko)...], coda_style, cards, card_style,
    draw(t) -> BGR float (H, W, 3), sound(path), pal(hi, endbg), end_icon, title_en_card, title_ko_card, sources, yt)
"""
import os, sys, math
import numpy as np, cv2, cairo
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.join(HERE, '..', 'scale'))
import engine as SE                                   # 끝 화면·글자·아이콘 재사용
from engine import (SC, FPS, DW, DH, W, H, clamp, ramp, smooth, expo_out, expo_in_out, back_out, lerp, mix, hexc,
                    txt, runs, rrect, icon, BLK, BOLD, SERIF, INK)

def surf():
    s = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H); cr = cairo.Context(s); cr.scale(SC, SC)
    cr.set_line_cap(cairo.LINE_CAP_ROUND); cr.set_line_join(cairo.LINE_JOIN_ROUND); return s, cr
def arr(s):
    s.flush(); st = s.get_stride()
    return np.frombuffer(s.get_data(), np.uint8).reshape(H, st // 4, 4)[:, :W].astype(np.float32) / 255
def over(img, s):
    a = arr(s); return img * (1 - a[..., 3:4]) + a[..., :3]
def solid(c): return np.ones((H, W, 3), np.float32) * np.array(c[::-1], np.float32)   # RGB → BGR

# ---------------------------------------------------------------- 카드
def card(cr, t, c, st):
    """c = (t0, t1, [en], [ko], y?). st: box(None|'paper'|'line'|'glow'), font, ink, hi, bg."""
    t0, t1, en, ko = c[:4]; y = c[4] if len(c) > 4 else st.get('y', 190)
    a = ramp(t, t0, t0 + 0.25) * (1 - ramp(t, t1 - 0.25, t1))
    if a <= 0: return
    se, sk = st.get('se', 62), st.get('sk', 56)
    if len(en) == 1: se += 4
    if len(ko) == 1: sk += 4
    hgt = 40 + len(en) * se * 1.18 + 12 + len(ko) * sk * 1.22
    k = expo_out(ramp(t, t0, t0 + 0.45)); dy = (1 - k) * st.get('drop', -30)
    cr.save(); cr.translate(0, dy)
    box = st.get('box')
    if box == 'paper':
        cr.set_source_rgba(*st['bg'], 0.93 * a); rrect(cr, 50, y - 4, DW - 100, hgt, st.get('r', 24)); cr.fill()
    elif box == 'line':
        cr.set_source_rgba(*st['hi'], a); cr.rectangle(80, y - 4, 10, hgt); cr.fill()
    elif box == 'band':
        cr.set_source_rgba(*st['bg'], 0.9 * a); cr.rectangle(0, y - 4, DW, hgt); cr.fill()
    yy = y + se + 12
    fe, fk = st.get('fe', BLK), st.get('fk', BLK)
    mw = st.get('maxw', 960)
    for ln in en: runs(cr, ln, DW / 2 + st.get('dx', 0), yy, se, st['ink'], st['hi'], a, fam=fe, maxw=mw); yy += se * 1.18
    yy += 8
    for ln in ko: runs(cr, ln, DW / 2 + st.get('dx', 0), yy, sk, st['ink'], st['hi'], a, fam=fk, maxw=mw); yy += sk * 1.22
    cr.restore()

# ---------------------------------------------------------------- 마무리 문장
STEP = 2.0; HOLD = 3.0
def coda_len(n): return n * STEP + HOLD
def coda(img, t, ep):
    """장면이 가라앉고 문장이 한 줄씩. style: dim(0..1), blur, ink, hi, fe, fk, y."""
    if t < ep['t_coda']: return img
    st = ep.get('coda_style', {}); t0 = ep['t_coda']; u = smooth(ramp(t, t0, t0 + 1.3))
    if st.get('blur', 12) > 0: img = cv2.GaussianBlur(img, (0, 0), max(0.1, st.get('blur', 12) * SC * u))
    tint = np.array(st.get('tint', (0, 0, 0))[::-1], np.float32)
    img = img * (1 - st.get('dim', 0.78) * u) + tint * st.get('dim', 0.78) * u
    s, cr = surf(); lines = ep['coda']; n = len(lines)
    y0 = st.get('y', 960 - n * 105 + 70)
    for i, (en, ko) in enumerate(lines):
        ti = t0 + 0.8 + i * STEP; a = smooth(ramp(t, ti, ti + 1.0)) * (1 - ramp(t, ep['t_end'] - 0.4, ep['t_end'] + 0.1))
        if a <= 0: continue
        last = i == n - 1; dy = (1 - expo_out(ramp(t, ti, ti + 1.3))) * 28
        col = st.get('hi', (1, 0.8, 0.4)) if last else st.get('ink', (0.97, 0.95, 0.9))
        se, sk = (74, 66) if last else (60, 54)
        yy = y0 + i * 210 + dy
        txt(cr, en, DW / 2, yy, se, col, a, fam=st.get('fe', SERIF), maxw=960)
        txt(cr, ko, DW / 2, yy + sk + 22, sk, col, a * 0.95, fam=st.get('fk', BLK) if last else st.get('fk2', BOLD), maxw=960)
    return over(img, s)

def wipe(img, t, t0, c1, c2):
    s, cr = surf(); drew = False
    for k, c in enumerate((c1, c2)):
        u = expo_in_out(ramp(t, t0 - 0.32 + 0.07 * k, t0 + 0.32 + 0.07 * k))
        if 0 < u < 1:
            x = lerp(-2150, 1420, u); drew = True
            cr.set_source_rgb(*c); cr.move_to(x + 260, 0); cr.line_to(x + 1960, 0); cr.line_to(x + 1700, DH); cr.line_to(x, DH); cr.close_path(); cr.fill()
    return over(img, s) if drew else img

def grain(img, t, amt=0.008):
    r = np.random.default_rng(int(t * FPS) + 3); return img + r.standard_normal((H, W, 1)).astype(np.float32) * amt

def frame(ep, t):
    img = ep['draw'](t)
    s, cr = surf()
    for c in ep.get('cards', []): card(cr, t, c, ep['card_style'])
    img = over(img, s)
    img = coda(img, t, ep)
    img = wipe(img, t, ep['t_end'], ep['pal']['hi'], ep['pal']['endbg'])
    img = SE.end_card(img, t, ep, ep['t_end'])
    return np.clip(grain(img, t, ep.get('grain', 0.007)), 0, 1)

def finalize(ep):
    """t_coda·coda로 t_end·DUR을 채운다."""
    ep['t_end'] = ep['t_coda'] + coda_len(len(ep['coda'])); ep['DUR'] = ep['t_end'] + 3.0
    return ep

def main(ep):
    cmd = sys.argv[1]
    if cmd == 'info': print('DUR', ep['DUR'], 'frames', int(ep['DUR'] * FPS))
    elif cmd == 'still':
        ims = []
        for tt in map(float, sys.argv[3:]):
            im = (frame(ep, tt) * 255).astype(np.uint8); cv2.putText(im, f'{tt:.1f}', (8, int(50 * SC)), 0, 1.4 * SC, (0, 255, 0), 2); ims.append(im)
        while len(ims) % 4: ims.append(np.zeros_like(ims[0]))
        cv2.imwrite(sys.argv[2], np.vstack([np.hstack(ims[i:i + 4]) for i in range(0, len(ims), 4)]))
    elif cmd == 'one': cv2.imwrite(sys.argv[2], (frame(ep, float(sys.argv[3])) * 255).astype(np.uint8))
    elif cmd == 'frames':
        od = sys.argv[2]; os.makedirs(od, exist_ok=True)
        for k in range(int(sys.argv[3]), int(sys.argv[4])):
            fn = os.path.join(od, f'f{k:05d}.png')
            if not os.path.exists(fn): cv2.imwrite(fn, (frame(ep, k / FPS) * 255 + 0.5).astype(np.uint8))
    elif cmd == 'sound': ep['sound'](sys.argv[2]); print('WROTE', sys.argv[2])
