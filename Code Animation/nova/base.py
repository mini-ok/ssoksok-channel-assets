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
# 규칙 2판(2026-11-28): 마무리 문장을 더 느리게·더 오래, 끝 화면에 구독·좋아요 권유, 글자는 안전 영역 안에.
STEP2 = 2.8; HOLD2 = 5.6; END2 = 7.0
SAFE_BOTTOM = 1450; SAFE_RIGHT = 930; SAFE_RIGHT_FROM = 1000     # 이 아래·오른쪽은 쇼츠 화면의 채널명·제목·버튼에 가려질 수 있다. 균형이 먼저: 조금 걸치는 것은 괜찮고, 꼭 읽혀야 하는 글자만 피한다
def coda_len(n, step=STEP, hold=HOLD): return n * step + hold
def coda(img, t, ep):
    """장면이 가라앉고 문장이 한 줄씩. style: dim(0..1), blur, ink, hi, fe, fk, y."""
    if t < ep['t_coda']: return img
    st = ep.get('coda_style', {}); t0 = ep['t_coda']; u = smooth(ramp(t, t0, t0 + 1.3))
    if st.get('blur', 12) > 0: img = cv2.GaussianBlur(img, (0, 0), max(0.1, st.get('blur', 12) * SC * u))
    tint = np.array(st.get('tint', (0, 0, 0))[::-1], np.float32)
    img = img * (1 - st.get('dim', 0.78) * u) + tint * st.get('dim', 0.78) * u
    s, cr = surf(); lines = ep['coda']; n = len(lines)
    r2 = ep.get('rules') == 2; step = ep.get('coda_step', STEP2 if r2 else STEP); fade = 1.6 if r2 else 1.0; mw = 960
    y0 = st.get('y', 960 - n * 105 + 70)                       # 배치는 1판 그대로(사용자 확인), 2판은 시간만 길다
    for i, (en, ko) in enumerate(lines):
        ti = t0 + 0.8 + i * step; a = smooth(ramp(t, ti, ti + fade)) * (1 - ramp(t, ep['t_end'] - (0.9 if r2 else 0.4), ep['t_end'] + 0.1))
        if a <= 0: continue
        last = i == n - 1; dy = (1 - expo_out(ramp(t, ti, ti + 1.3))) * 28
        col = st.get('hi', (1, 0.8, 0.4)) if last else st.get('ink', (0.97, 0.95, 0.9))
        se, sk = (74, 66) if last else (60, 54)
        yy = y0 + i * 210 + dy
        txt(cr, en, DW / 2, yy, se, col, a, fam=st.get('fe', SERIF), maxw=mw)
        txt(cr, ko, DW / 2, yy + sk + 22, sk, col, a * 0.95, fam=st.get('fk', BLK) if last else st.get('fk2', BOLD), maxw=mw)
    return over(img, s)

def wipe(img, t, t0, c1, c2):
    s, cr = surf(); drew = False
    for k, c in enumerate((c1, c2)):
        u = expo_in_out(ramp(t, t0 - 0.32 + 0.07 * k, t0 + 0.32 + 0.07 * k))
        if 0 < u < 1:
            x = lerp(-2150, 1420, u); drew = True
            cr.set_source_rgb(*c); cr.move_to(x + 260, 0); cr.line_to(x + 1960, 0); cr.line_to(x + 1700, DH); cr.line_to(x, DH); cr.close_path(); cr.fill()
    return over(img, s) if drew else img

def _heart(cr, x, y, k):
    cr.save(); cr.translate(x, y); cr.scale(k, k); cr.move_to(0, 30); cr.curve_to(-60, -10, -40, -60, 0, -30); cr.curve_to(40, -60, 60, -10, 0, 30); cr.close_path(); cr.restore()
def _bell(cr, x, y, k, rot=0.0):
    cr.save(); cr.translate(x, y - 26 * k); cr.rotate(rot); cr.translate(0, 26 * k); cr.scale(k, k)
    cr.move_to(-24, 14); cr.curve_to(-14, 6, -18, -24, 0, -26); cr.curve_to(18, -24, 14, 6, 24, 14); cr.close_path()
    cr.new_sub_path(); cr.arc(0, 21, 5.5, 0, 6.283); cr.restore()

CTA_DEFAULT = ('If this stayed with you, stay with us.', '마음에 남았다면, 곁에 머물러 주세요')
def end_card2(img, t, ep):
    """끝 화면 2판: 화면 가운데에 균형 있게 놓는다(위 510 ~ 아래 1510). 권유 칸이 가려지는 영역에 조금 걸치는 것은 괜찮다(사용자 지시: 균형이 먼저). 제목 → 인장 → 크레딧 → 출처 → 구독·좋아요 권유.
    ep['cta'] = (영어, 한글)로 편마다 이야기와 이어지는 권유 문장을 준다. t_cta_like / t_cta_sub는 소리 맞춤용."""
    t_end = ep['t_end']
    if t < t_end: return img
    pal = ep['pal']; ink = pal.get('endink', INK); hi = pal['hi']; bg = pal['endbg']
    s, cr = surf(); u = smooth(ramp(t, t_end, t_end + 0.5))
    cr.set_source_rgba(*bg, u); cr.paint()
    a = ramp(t, t_end + 0.25, t_end + 0.7); k = 1 + 0.12 * (1 - expo_out(ramp(t, t_end + 0.25, t_end + 0.8)))
    cr.save(); cr.translate(DW / 2, 660); cr.scale(k, k)
    icon(cr, ep['end_icon'], 0, -150, 110, hi, bg)
    txt(cr, ep['title_en_card'], 0, 20, 76, ink, a, maxw=900)
    txt(cr, ep['title_ko_card'], 0, 112, 70, ink, a, maxw=900)
    cr.restore()
    b = ramp(t, t_end + 0.9, t_end + 1.4)
    txt(cr, 'Created & Coded by L.S.M.', DW / 2, 1050, 30, ink, 0.9 * b, fam=SERIF)
    txt(cr, '허상공방 虛像工房 Project', DW / 2, 1094, 30, ink, 0.9 * b, fam=SERIF)
    c = ramp(t, t_end + 1.3, t_end + 1.8)
    for i, src in enumerate(ep['sources']): txt(cr, src, DW / 2, 1152 + i * 32, 22, ink, 0.6 * c, fam=BOLD, maxw=840)
    # 구독·좋아요 권유: 문장이 먼저 스미고, 좋아요 → 구독 순서로 칸이 채워진다
    en, ko = ep.get('cta', CTA_DEFAULT); tl, ts = t_end + ep.get('cta_like', 3.2), t_end + ep.get('cta_sub', 4.0)
    d = smooth(ramp(t, t_end + 2.0, t_end + 3.0)); dy = (1 - expo_out(ramp(t, t_end + 2.0, t_end + 3.2))) * 18
    cr.set_source_rgba(*hi, 0.5 * d); cr.set_line_width(2); cr.move_to(DW / 2 - 60, 1256); cr.line_to(DW / 2 + 60, 1256); cr.stroke()
    txt(cr, en, DW / 2, 1322 + dy, 36, ink, 0.92 * d, fam=SERIF, maxw=700)
    txt(cr, ko, DW / 2, 1382 + dy, 44, ink, d, fam=BLK, maxw=700)
    for j, (lab, tt) in enumerate((('좋아요', tl), ('구독', ts))):
        on = smooth(ramp(t, tt, tt + 0.35)); pw, ph = 236, 74; x0 = DW / 2 - pw - 14 + j * (pw + 28); y0 = 1432 + dy
        pop = 1 + 0.10 * math.sin(min(1.0, max(0.0, (t - tt) / 0.5)) * math.pi)
        cr.save(); cr.translate(x0 + pw / 2, y0 + ph / 2); cr.scale(pop, pop); cr.translate(-pw / 2, -ph / 2)
        rrect(cr, 0, 0, pw, ph, ph / 2); cr.set_source_rgba(*hi, on * d); cr.fill_preserve(); cr.set_source_rgba(*hi, d); cr.set_line_width(3); cr.stroke()
        col = tuple(lerp(hi[q], bg[q], on) for q in range(3))
        if j == 0:
            beat = 1 + 0.16 * max(0.0, math.sin((t - tt) * 5.2)) * math.exp(-max(0.0, t - tt) * 0.9) if t > tt else 1
            _heart(cr, 56, ph / 2 + 2, 0.36 * beat); cr.set_source_rgba(*col, d); cr.fill()
        else:
            sw = 0.35 * math.sin((t - tt) * 13) * math.exp(-max(0.0, t - tt) * 2.2) if t > tt else 0
            _bell(cr, 56, ph / 2 - 2, 0.82, sw); cr.set_source_rgba(*col, d); cr.fill()
        txt(cr, lab, 142, ph / 2 + 13, 36, col, d, fam=BLK)
        cr.restore()
    img = over(img, s)
    if t >= t_end + 0.6:                                             # 낙관(곱하기)
        if 'v2' not in SE._SEAL:
            sz = int(round(104 * SC)); sl = np.load(os.path.join(HERE, '..', '_shared', 'seal_baimun3.npy')).astype(np.float32)
            SE._SEAL['v2'] = (cv2.resize(sl, (sz, sz), interpolation=cv2.INTER_AREA)[..., [2, 1, 0, 3]], sz)
        sl, sz = SE._SEAL['v2']; a1 = smooth(ramp(t, t_end + 0.6, t_end + 0.8))
        xs, ys = int(round(DW / 2 * SC)) - sz // 2, int(round(860 * SC))
        red = np.clip((sl[..., 2:3] - sl[..., 1:2]) * 4, 0, 1); al = sl[..., 3:4] * a1 * red
        sub = img[ys:ys + sz, xs:xs + sz]; img[ys:ys + sz, xs:xs + sz] = sub * (1 - al + al * sl[..., :3])
    return img

def safe_overlay(im):
    """정지 확인용: 쇼츠 화면에서 가려질 수 있는 곳을 붉게 표시(MG_SAFE=1)."""
    yb, xr, yr = int(SAFE_BOTTOM * SC), int(SAFE_RIGHT * SC), int(SAFE_RIGHT_FROM * SC)
    im[yb:] = im[yb:] * 0.6 + np.array([0, 0, 0.4], np.float32); im[yr:yb, xr:] = im[yr:yb, xr:] * 0.6 + np.array([0, 0, 0.4], np.float32)
    return im

def grain(img, t, amt=0.008):
    r = np.random.default_rng(int(t * FPS) + 3); return img + r.standard_normal((H, W, 1)).astype(np.float32) * amt

def frame(ep, t):
    img = ep['draw'](t)
    s, cr = surf()
    for c in ep.get('cards', []): card(cr, t, c, ep['card_style'])
    img = over(img, s)
    img = coda(img, t, ep)
    img = wipe(img, t, ep['t_end'], ep['pal']['hi'], ep['pal']['endbg'])
    img = end_card2(img, t, ep) if ep.get('rules') == 2 else SE.end_card(img, t, ep, ep['t_end'])
    img = np.clip(grain(img, t, ep.get('grain', 0.007)), 0, 1)
    return safe_overlay(img) if os.environ.get('MG_SAFE') else img

def finalize(ep):
    """t_coda·coda로 t_end·DUR을 채운다. rules=2면 새 규칙(긴 여운, 구독·좋아요 끝 화면, 전체 30~70초)."""
    if ep.get('rules') == 2:
        ep['t_end'] = ep['t_coda'] + coda_len(len(ep['coda']), ep.get('coda_step', STEP2), ep.get('coda_hold', HOLD2)); ep['DUR'] = ep['t_end'] + ep.get('end_len', END2)
        assert 30.0 <= ep['DUR'] <= 70.0, f"길이 {ep['DUR']:.1f}초: 30초 이상 1분 10초 이하로"
    else:
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
