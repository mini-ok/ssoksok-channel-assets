"""가로 애니메이션 → 세로 예고 쇼츠 (4:3 크롭을 9:16 위에 앉힘).
python3 make_teaser_short.py <key> [still_t]   still_t가 있으면 그 시점 정지 화면만 만든다.

환경 변수
  TEASER_SRC  원본 가로 영상(mp4)이 있는 폴더 (기본: /mnt/user-data/uploads/AI자동화애니메이션테스트)
  TEASER_OUT  결과 폴더 (기본: ./out)
새 작품을 쇼츠로 만들 때는 CLIPS에 항목 하나를 더한다(사용법: ../shorts_playbook.md).
"""
import sys, subprocess, os
from PIL import Image, ImageDraw, ImageFont, ImageFilter

U = os.environ.get('TEASER_SRC', '/mnt/user-data/uploads/AI자동화애니메이션테스트')
OUT = os.environ.get('TEASER_OUT', os.path.join(os.getcwd(), 'out'))
os.makedirs(OUT, exist_ok=True)
FB = '/usr/share/fonts/opentype/noto/NotoSerifCJK-Bold.ttc'
FR = '/usr/share/fonts/opentype/noto/NotoSerifCJK-Regular.ttc'

W, H = 1080, 1920
VY = 520            # 영상 윗변
VH = 810            # 1080 x 810 = 4:3

# 소스 1920x1080. 허수아비는 위아래 20px 검은 띠(1920x1040)
CLIPS = {
    'keeper': dict(src='빛지기_THE_KEEPER_v2.mp4', ss=0.0, t=35.0, box=(1440, 1080, 0),
                   x="if(gte(t\\,29)*lt(t\\,32)\\,60\\,240)",
                   ko='등대 불이 꺼졌다.\n저 바다엔 아직 배가 있다', en='The lighthouse went dark.\nA boat is still out there.',
                   title='빛지기', title_en='The Keeper'),
    'holssi': dict(src='홀씨_HOLSSI_v2.mp4', ss=7.0, t=40.5, box=(1440, 1080, 0), x='240',
                   ko='들판에 남은\n마지막 홀씨 하나', en='The last dandelion seed\nin the field.',
                   title='홀씨', title_en='Holssi'),
    'scare_climax': dict(src='허수아비의겨울_v2.mp4', ss=72.0, t=25.0, box=(1386, 1040, 20),
                   x="if(gte(t\\,11)*lt(t\\,15)+gte(t\\,17)*lt(t\\,21)\\,534\\,300)",
                   ko='바람이 불 때만\n움직이는 허수아비', en='He only moves\nwhen the wind blows.',
                   title='허수아비의 겨울', title_en="The Scarecrow's Winter"),
    'scare_open': dict(src='허수아비의겨울_v2.mp4', ss=0.5, t=41.5, box=(1386, 1040, 20), x='267',
                   ko='참새는 이 허수아비가\n영웅인 줄 안다', en='The sparrow thinks\nthis scarecrow is a hero.',
                   title='허수아비의 겨울', title_en="The Scarecrow's Winter"),
}


def font(path, size):
    return ImageFont.truetype(path, size, index=1)


def centered(d, y, text, f, fill, shadow=True, spacing=10):
    lines = text.split('\n')
    for ln in lines:
        w = d.textlength(ln, font=f)
        x = (W - w) / 2
        if shadow:
            d.text((x + 2, y + 3), ln, font=f, fill=(0, 0, 0, 150))
        d.text((x, y), ln, font=f, fill=fill)
        y += f.size + spacing
    return y


def fit(d, text, path, size, maxw):
    while size > 20:
        f = font(path, size)
        if max(d.textlength(l, font=f) for l in text.split('\n')) <= maxw:
            return f
        size -= 2
    return font(path, size)


def overlay(c, png):
    im = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    # 글자 뒤 어두운 띠(위·아래, 부드럽게)
    import numpy as np
    a = np.zeros((H,), np.float32)
    yy = np.arange(H)
    a += np.clip(1 - np.abs(yy - 360) / 260, 0, 1) ** 0.8 * 120
    a += np.clip(1 - np.abs(yy - (VY + VH + 120)) / 230, 0, 1) ** 0.8 * 110
    scrim = np.zeros((H, W, 4), np.uint8); scrim[..., 3] = np.clip(a, 0, 255)[:, None]
    im = Image.alpha_composite(im, Image.fromarray(scrim, 'RGBA'))
    d = ImageDraw.Draw(im)
    # 글자 크기 원칙(사용자 지시 2026-11-21): 한국 전용 채널처럼 보이지 않게 영어와 한글을 비슷한 크기로.
    # 영어를 위(주), 한글을 바로 아래에 두고, 둘 다 굵게·거의 같은 크기(EN 48 / KO 42 — 한글 굵은 글꼴이 같은 크기면 더 커 보여서 조금 작게).
    # 위: 공방 표지 + 첫 자막(영·한)
    centered(d, 160, 'Dreamloom Studio · 허상공방', font(FR, 28), (255, 255, 255, 190), spacing=6)
    fe = fit(d, c['en'], FB, 48, 980)
    fk = fit(d, c['ko'], FB, 42, 960)
    ne, nk = c['en'].count('\n') + 1, c['ko'].count('\n') + 1
    y0 = VY - 50 - ne * (fe.size + 10) - nk * (fk.size + 10) - 14
    y = centered(d, y0, c['en'], fe, (255, 255, 255, 255), spacing=10)
    centered(d, y + 14, c['ko'], fk, (255, 255, 255, 235), spacing=10)
    # 아래: 전체 영상 안내(영·한 같은 크기)
    yb = VY + VH + 56
    centered(d, yb, f'{c["title_en"]} · {c["title"]}', fit(d, f'{c["title_en"]} · {c["title"]}', FB, 40, 980),
             (255, 236, 200, 255))
    centered(d, yb + 60, 'Watch the full film — tap the related video ↓', font(FR, 30), (255, 255, 255, 220))
    centered(d, yb + 102, "전체 이야기는 아래 '관련 동영상'에서 ↓", font(FR, 28), (255, 255, 255, 200))
    im.save(png)


def build(key, still=None):
    c = CLIPS[key]
    png = f'{OUT}/{key}_ov.png'
    overlay(c, png)
    cw, ch, cy = c['box']
    src = f'{U}/{c["src"]}'
    D = c['t']
    fc = (f"[0:v]crop={cw}:{ch}:'{c['x']}':{cy},setsar=1,split[a][b];"
          f"[a]scale=1080:810:flags=lanczos[fg];"
          f"[b]scale=2560:1920,crop=1080:1920,boxblur=40:2,eq=brightness=-0.30:saturation=0.8[bg];"
          f"[bg][fg]overlay=0:{VY}[m];[m][1:v]overlay=0:0")
    if still is not None:
        cmd = ['ffmpeg', '-y', '-loglevel', 'error', '-ss', str(c['ss'] + still), '-i', src, '-i', png,
               '-filter_complex', fc.replace("(t\\,", f"(t+{still}\\,"), '-frames:v', '1', f'{OUT}/{key}_still_{still}.png']
    else:
        fc += f",fade=in:st=0:d=0.3,fade=out:st={D - 0.7}:d=0.7[v]"
        cmd = ['ffmpeg', '-y', '-loglevel', 'error', '-ss', str(c['ss']), '-t', str(D), '-i', src, '-i', png,
               '-filter_complex', fc, '-map', '[v]', '-map', '0:a',
               '-af', f'afade=in:st=0:d=0.3,afade=out:st={D - 1.0}:d=1.0,loudnorm=I=-14:TP=-1.5:LRA=11',
               '-ar', '48000', '-c:v', 'libx264', '-preset', 'slow', '-crf', '18', '-pix_fmt', 'yuv420p',
               '-c:a', 'aac', '-b:a', '192k', '-movflags', '+faststart', f'{OUT}/{key}_short.mp4']
    subprocess.run(cmd, check=True)


if __name__ == '__main__':
    build(sys.argv[1], float(sys.argv[2]) if len(sys.argv) > 2 else None)
