"""완성된 쇼츠를 공개 저장소의 shorts-outbox 브랜치에 넣는다 — 업로더 계정이 가져가 유튜브에 올린다.

python3 publish_outbox.py <slug> <mp4> [--dry-run]

- 업로더 쪽 규칙·주소는 shorts-outbox 브랜치의 README.md(= docs/uploader_handoff.md).
- 영상은 GitHub 파일 한도(100MB) 안으로 다시 인코딩한다(H.264 CRF 20, 최대 12Mbps, faststart). 90MB를 넘으면 CRF를 올려 다시.
- shorts/<slug>/video.mp4 + meta.json, 맨 위 index.json에 항목 추가. 이미 있는 slug면 멈춘다.
- 이 세션의 git 자격으로 push한다(GH_TOKEN 불필요). 실패하면 이유를 출력하고 종료 코드 1.
"""
import os, sys, json, re, subprocess, tempfile, datetime, argparse, shutil

HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
URL = 'https://github.com/mini-ok/ssoksok-channel-assets'
BR = 'shorts-outbox'
HANGUL = re.compile(r'[ᄀ-ᇿ㄰-㆏가-힣ㆍᆞ]')


def sh(*a, cwd=None):
    r = subprocess.run(a, cwd=cwd, capture_output=True, text=True)
    if r.returncode: sys.exit(f'실패: {" ".join(a[:3])}… {r.stderr[-400:]}')
    return r.stdout


def encode(src, dst):
    for crf in (20, 23, 26):
        sh('ffmpeg', '-y', '-loglevel', 'error', '-i', src, '-c:v', 'libx264', '-preset', 'slow', '-crf', str(crf),
           '-maxrate', '12M', '-bufsize', '24M', '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-b:a', '192k',
           '-movflags', '+faststart', dst)
        if os.path.getsize(dst) < 90e6: return
    sys.exit('90MB 아래로 못 줄임')


if __name__ == '__main__':
    ap = argparse.ArgumentParser(); ap.add_argument('slug'); ap.add_argument('mp4'); ap.add_argument('--dry-run', action='store_true')
    a = ap.parse_args()
    import engine as E
    yt = getattr(E.Episode(a.slug).m, 'YT', None)
    if not yt: sys.exit('에피소드 파일에 YT 메타데이터가 없음')
    for k in ('title_en', 'desc_en'):
        if HANGUL.search(yt[k]): sys.exit(f'{k}에 한글 — 채널 규칙 위반')
    if len(yt['title_en']) > 100: sys.exit('제목 100자 초과')
    now = datetime.datetime.now(datetime.timezone.utc).isoformat(timespec='seconds')
    meta = dict(slug=a.slug, title_en=yt['title_en'], title_ko=yt['title_ko'], desc_en=yt['desc_en'], desc_ko=yt['desc_ko'],
                tags=yt.get('tags', []), related=yt.get('related'), file='video.mp4', created=now)
    d = tempfile.mkdtemp()
    sh('git', 'clone', '-q', '--depth', '1', '--branch', BR, URL, d)
    idx_p = os.path.join(d, 'index.json'); idx = json.load(open(idx_p))
    if any(i['slug'] == a.slug for i in idx['items']): sys.exit(f'이미 있는 slug: {a.slug}')
    od = os.path.join(d, 'shorts', a.slug); os.makedirs(od)
    encode(a.mp4, os.path.join(od, 'video.mp4'))
    json.dump(meta, open(os.path.join(od, 'meta.json'), 'w'), ensure_ascii=False, indent=1)
    idx['items'].append(dict(slug=a.slug, dir=f'shorts/{a.slug}', created=now)); json.dump(idx, open(idx_p, 'w'), indent=1)
    mb = os.path.getsize(os.path.join(od, 'video.mp4')) / 1e6
    if a.dry_run:
        print(f'[dry-run] {a.slug} {mb:.1f}MB'); print(json.dumps(meta, ensure_ascii=False, indent=1)); shutil.rmtree(d); sys.exit(0)
    sh('git', 'add', '-A', cwd=d)
    sh('git', '-c', 'user.name=claude', '-c', 'user.email=noreply@anthropic.com', 'commit', '-qm', f'outbox: {a.slug}', cwd=d)
    sh('git', 'push', 'origin', BR, cwd=d)
    print('PUBLISHED', a.slug, f'{mb:.1f}MB', f'https://raw.githubusercontent.com/mini-ok/ssoksok-channel-assets/{BR}/shorts/{a.slug}/video.mp4')
