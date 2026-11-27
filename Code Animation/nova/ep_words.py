"""〈하루 1만 6천 단어〉 — 타자기 원고(크림 종이, 글자마다 다른 잉크 농도와 들쭉날쭉한 줄, 리본 얼룩), 소리는 타자 소리·캐리지 종·낮은 업라이트 베이스.
사실(Mehl et al., Science 2007, 대학생 396명 녹음): 남녀 모두 하루 약 16,000단어.
1년 약 584만 단어, 60년이면 약 3억 5천만 단어(계산). 킹 제임스 성경 약 78만 단어 → 약 450권 분량(계산).
"""
import math, numpy as np, cv2, cairo
from base import *
import sfx as S

MONO = 'Courier 10 Pitch'
PAPER = (0.95, 0.92, 0.84); INK = (0.10, 0.09, 0.12); RIB = (0.62, 0.12, 0.10)
T_DAY = 3.8; T_YEAR = 8.8; T_LIFE = 13.6; T_CODA = 18.8
WORDS = 'yes okay thanks sorry wait what really sure fine hello no maybe right love later see you good night eat now'.split()
_r = np.random.default_rng(23)
_n = cv2.GaussianBlur(_r.random((H, W)).astype(np.float32), (0, 0), 0.8 * SC)
INKTEX = np.clip(0.75 + 0.5 * _n, 0, 1)
_p = cv2.GaussianBlur(_r.random((H, W)).astype(np.float32), (0, 0), 30 * SC)
PAPER_IMG = (np.array(PAPER[::-1], np.float32) * (0.95 + 0.08 * _p[..., None])).astype(np.float32)

def typed(cr, text, x, y, size, n_chars, seed=0, col=INK, fam=MONO, anchor='l'):
    """한 글자씩 쳐 넣은 글씨: 글자마다 위아래로 조금 튀고 진하기가 다르다."""
    r = np.random.default_rng(seed)
    cr.select_font_face(fam, cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD if fam != MONO else cairo.FONT_WEIGHT_NORMAL); cr.set_font_size(size)
    w = cr.text_extents(text).x_advance
    cx = x - w / 2 if anchor == 'c' else x
    for i, ch in enumerate(text[:max(0, int(n_chars))]):
        cr.set_source_rgba(*col, r.uniform(0.6, 1.0)); cr.move_to(cx, y + r.normal(0, size * 0.03)); cr.show_text(ch)
        cx += cr.text_extents(ch).x_advance

def draw(t):
    s, cr = surf()
    cps = 22                                                         # 글자/초
    if t < T_DAY:
        for k, line in enumerate(['"Good morning."', '"Yes, I\'m fine."', '"Thank you."', '"See you later."']):
            typed(cr, line, 120, 700 + k * 110, 66, (t - 0.3 - k * 0.7) * cps, k + 1)
    elif t < T_YEAR:                                                 # 종이를 채우는 하루치 말
        n = int(16000 * smooth(ramp(t, T_DAY + 0.3, T_YEAR - 0.6)))
        per = 70; rows = min(56, n // (per * 4) + 1)
        r = np.random.default_rng(5); cr.select_font_face(MONO); cr.set_font_size(15)
        for row in range(rows):
            line = ' '.join(WORDS[(row * 7 + k) % len(WORDS)] for k in range(12))
            cr.set_source_rgba(*INK, 0.55 + 0.3 * r.random()); cr.move_to(90, 520 + row * 19); cr.show_text(line[:74])
        typed(cr, f'{n:,} words', 540, 1680, 90, 99, 7, anchor='c')
    elif t < T_LIFE:                                                 # 1년치 원고 더미
        u = smooth(ramp(t, T_YEAR + 0.3, T_YEAR + 3.0)); k = int(365 * u)
        for i in range(0, k, 3):
            y = 1450 - i * 2.4; cr.set_source_rgba(*(0.88, 0.85, 0.76), 1); cr.rectangle(300 + (i % 7), y, 480, 6); cr.fill()
            cr.set_source_rgba(*INK, 0.5); cr.rectangle(300 + (i % 7), y, 480, 1.5); cr.fill()
        typed(cr, f'{k} days · {k * 16000 / 1e6:.1f} million words', 540, 1620, 46, 99, 8, anchor='c')
        typed(cr, f'{k}일 · {k * 16000 / 1e4:,.0f}만 단어', 540, 1690, 44, 99, 9, anchor='c', fam=BOLD)
    else:                                                            # 평생: 성경 450권
        u = smooth(ramp(t, T_LIFE + 0.3, T_LIFE + 3.4)); nb = int(450 * u)
        for i in range(nb):
            x = 120 + (i % 30) * 28; y = 1420 - (i // 30) * 52
            cr.set_source_rgba(*(0.25 + 0.1 * (i % 3), 0.12, 0.10), 1); cr.rectangle(x, y - 46, 24, 46); cr.fill()
            cr.set_source_rgba(*(0.85, 0.70, 0.35), 1); cr.rectangle(x + 4, y - 38, 16, 2); cr.fill()
        typed(cr, f'≈ {350 * u:,.0f} million words', 540, 1560, 60, 99, 10, anchor='c')
        typed(cr, f'약 {3.5 * u:.1f}억 단어 · 성경 {nb}권 분량', 540, 1640, 48, 99, 11, anchor='c', fam=BOLD)
    a = arr(s) * INKTEX[..., None]
    img = PAPER_IMG * (1 - a[..., 3:4]) + a[..., :3]
    return img

def sound(path):
    m = S.Mix(EP['DUR'], 191); tc = EP['t_coda']; r = np.random.default_rng(3)
    t = 0.3
    while t < T_DAY - 0.3: m.put('fx', t, S.typekey(0.35, int(t * 100))); t += 1 / 22 * r.uniform(0.7, 1.6)
    m.put('fx', 1.0, S.typebell(0.25)); m.put('fx', T_DAY - 0.4, S.typebell(0.3))
    t = T_DAY
    while t < T_YEAR - 0.6: m.put('fx', t, S.typekey(0.25, int(t * 100))); t += r.uniform(0.03, 0.07)
    for k in range(10): m.put('fx', T_YEAR + 0.3 + k * 0.27, S.tok(400 + 15 * k, 0.15))
    m.put('fx', T_LIFE, S.typebell(0.35))
    b = 60 / 92; walk = [110.0, 130.8, 146.8, 164.8, 146.8, 130.8, 123.5, 110.0]
    t = T_DAY; k = 0
    while t < tc - 0.2: m.put('mus', t, S.upright(walk[k % 8], 0.6, 0.35)); t += b; k += 1
    m.put('amb', tc, S.drone([110.0, 164.8, 220.0], EP['t_end'] - tc, 0.14, 'sine'))
    for i in range(3): m.put('fx', tc + 0.6 + i * STEP, S.typekey(0.3, i)); m.put('mus', tc + 0.8 + i * STEP, S.upright([110.0, 98.0, 82.4][i], 1.6, 0.4))
    m.put('fx', EP['t_end'] + 0.1, S.typebell(0.3))
    m.write(path, rev_mus=1.6, wet_mus=0.22)

EP = finalize(dict(t_coda=T_CODA, draw=draw, sound=sound, end_icon='star', grain=0.0,
    title_en_card='16,000 WORDS A DAY', title_ko_card='하루 1만 6천 단어',
    pal=dict(hi=RIB, endbg=PAPER),
    card_style=dict(box=None, ink=INK, hi=RIB, y=150, fe=BLK, fk=BLK),
    cards=[(0.3, 3.6, ['How many words', 'do you say in a day?'], ['나는 하루에', '몇 단어를 말할까?']),
           (3.8, 8.6, ['About *16,000*.', 'Men and women alike.'], ['약 *1만 6천* 단어,', '남녀 차이도 거의 없다']),
           (8.8, 13.4, ['In a year:', 'almost *6 million*.'], ['1년이면', '거의 *600만* 단어']),
           (13.6, 18.6, ['In a lifetime: about *350 million*,', 'the Bible *450 times* over.'], ['평생 약 *3억 5천만* 단어,', '성경 *450권* 분량'])],
    coda=[('Sixteen thousand words a day.', '하루 1만 6천 단어'), ('Most are forgotten by evening.', '대부분은 저녁이면 잊힌다'), ('Make the ones that stay kind.', '남는 말은 다정한 말이 되게 하자')],
    coda_style=dict(dim=0.7, blur=10, tint=PAPER, ink=INK, hi=RIB),
    sources=['Mehl et al., “Are Women Really More Talkative Than Men?”, Science 2007: about 16,000 words per day for both sexes (396 participants).', 'Year/lifetime totals calculated (60 years of talking). King James Bible ≈ 783,000 words.'],
    yt=dict(title_en='You Speak About 16,000 Words a Day #Shorts', title_ko='나는 하루 1만 6천 단어를 말한다')))

if __name__ == '__main__': main(EP)
