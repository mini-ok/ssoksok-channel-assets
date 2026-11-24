"""지식 쇼츠를 GitHub 공개 릴리스로 올린다 — 다른 업로더(다른 API)가 가져가 유튜브에 올리는 방식.

python3 publish_release.py <에피소드 slug> <mp4> [--dry-run]

한 편 = 릴리스 하나. 태그 `short-<slug>`, 첨부 파일 `<slug>.mp4` + `meta.json`.
meta.json 항목: slug, title_en, title_ko, desc_en, desc_ko, tags, mp4(내려받기 주소), created(UTC).
가져가는 쪽: https://api.github.com/repos/mini-ok/ssoksok-channel-assets/releases (로그인 없이 읽힘, 시간당 60회)
  → 태그가 `short-`로 시작하고, 자기가 이미 올린 태그 기록에 없는 것만 가져간다(중복 업로드 방지).
공개 저장소이므로 올리는 순간 누구나 영상을 내려받을 수 있다(유튜브 공개 전에도).
gh CLI 로그인(GH_TOKEN)이 필요하다. 값은 출력·로그·커밋에 남기지 않는다.
"""
import os, sys, json, re, subprocess, tempfile, datetime, argparse

HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
REPO = 'mini-ok/ssoksok-channel-assets'
HANGUL = re.compile(r'[ᄀ-ᇿ㄰-㆏가-힣ㆍᆞ]')

def build_meta(slug, yt):
    for k in ('title_en', 'desc_en'):
        if HANGUL.search(yt[k]): sys.exit(f'{k}에 한글이 섞여 있음 — 채널 규칙 위반')
    if len(yt['title_en']) > 100 or len(yt['title_ko']) > 100: sys.exit('제목이 100자를 넘음')
    tag = f'short-{slug}'
    return tag, dict(slug=slug, title_en=yt['title_en'], title_ko=yt['title_ko'], desc_en=yt['desc_en'], desc_ko=yt['desc_ko'],
                     tags=yt.get('tags', []), related=yt.get('related'),
                     mp4=f'https://github.com/{REPO}/releases/download/{tag}/{slug}.mp4',
                     created=datetime.datetime.now(datetime.timezone.utc).isoformat(timespec='seconds'))

if __name__ == '__main__':
    ap = argparse.ArgumentParser(); ap.add_argument('slug'); ap.add_argument('mp4'); ap.add_argument('--dry-run', action='store_true')
    a = ap.parse_args()
    import engine as E
    yt = getattr(E.Episode(a.slug).m, 'YT', None)
    if not yt: sys.exit('에피소드 파일에 YT 메타데이터가 없음')
    tag, meta = build_meta(a.slug, yt)
    if not os.path.isfile(a.mp4): sys.exit(f'mp4 없음: {a.mp4}')
    mb = os.path.getsize(a.mp4) / 1e6
    if a.dry_run:
        print(f'[dry-run] tag={tag} mp4={mb:.1f}MB'); print(json.dumps(meta, ensure_ascii=False, indent=1)); sys.exit(0)
    d = tempfile.mkdtemp(); mp = os.path.join(d, 'meta.json'); json.dump(meta, open(mp, 'w'), ensure_ascii=False, indent=1)
    if subprocess.run(['gh', 'release', 'view', tag, '--repo', REPO], capture_output=True).returncode == 0:
        sys.exit(f'이미 있는 태그: {tag} — 올리지 않음')
    notes = f"{yt['title_en']}\n\n{yt['title_ko']}\n\n(업로더용 자동 게시. 메타데이터는 meta.json)"
    r = subprocess.run(['gh', 'release', 'create', tag, a.mp4, mp, '--repo', REPO, '--title', yt['title_en'], '--notes', notes, '--latest=false'],
                       capture_output=True, text=True)
    if r.returncode != 0: sys.exit('릴리스 실패: ' + r.stderr[-300:])
    print('PUBLISHED', tag, meta['mp4'])
