"""다시 만든 옛 6편을 새 slug(_v2)로 shorts-outbox에 넣는다. 사용: cd /tmp && python3 outbox_remake.py water_ball earth_year ..."""
import datetime, json, os, shutil, subprocess, sys, tempfile
src = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'scale', 'outbox_push.py')).read(); ns = {}
exec(src[:src.index('def sh(')], ns)
META, COMMON, SIGN_EN, SIGN_KO = ns['META'], ns['COMMON_TAGS'], ns['SIGN_EN'], ns['SIGN_KO']
FILE = dict(water_ball='water', earth_year='year', solar_bead='bead', sky_apple='skyapple', heartbeats='heart', sleep='sleep')
META['sleep'] = dict(META['sleep'], title_en="You'll Spend About 27 Years Asleep #Shorts")

def sh(*a, cwd=None):
    r = subprocess.run(a, cwd=cwd, capture_output=True, text=True)
    if r.returncode: sys.exit(f'FAIL {a[:3]} {r.stderr[-300:]}')
    return r.stdout

d = tempfile.mkdtemp()
sh('git', 'clone', '-q', '--depth', '1', '--branch', 'shorts-outbox', 'https://github.com/mini-ok/ssoksok-channel-assets', d)
idx = json.load(open(f'{d}/index.json')); base = datetime.datetime.now(datetime.timezone.utc).replace(microsecond=0)
for k, old in enumerate(sys.argv[1:]):
    slug = old + '_v2'
    if any(i['slug'] == slug for i in idx['items']): print('skip', slug); continue
    m = META[old]; now = (base + datetime.timedelta(seconds=k)).isoformat()
    od = f'{d}/shorts/{slug}'; os.makedirs(od); shutil.copy(f'/home/claude/work/nova/out/{FILE[old]}.mp4', f'{od}/video.mp4')
    json.dump(dict(slug=slug, title_en=m['title_en'], title_ko=m['title_ko'], desc_en=m['desc_en'] + SIGN_EN, desc_ko=m['desc_ko'] + SIGN_KO,
                   tags=m['tags'] + COMMON, related=None, file='video.mp4', created=now), open(f'{od}/meta.json', 'w'), ensure_ascii=False, indent=1)
    idx['items'].append(dict(slug=slug, dir=f'shorts/{slug}', created=now)); print('add', slug)
json.dump(idx, open(f'{d}/index.json', 'w'), indent=1, ensure_ascii=False)
sh('git', 'add', '-A', cwd=d)
sh('git', '-c', 'user.name=claude', '-c', 'user.email=noreply@anthropic.com', 'commit', '-qm', 'outbox: restyled ' + ' '.join(sys.argv[1:]), cwd=d)
sh('git', 'push', '-q', 'origin', 'shorts-outbox', cwd=d)
print('PUSHED', len(idx['items']), 'items')
