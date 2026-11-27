"""규모 체감 쇼츠를 shorts-outbox에 넣는다. python3 outbox_push.py slug1 slug2 ..."""
import os, sys, json, subprocess, tempfile, datetime, shutil

META = {
 'water_ball': dict(title_en="All of Earth's Water in One Ball Is Tiny #Shorts", title_ko='지구의 물을 공 하나로 모으면',
   desc_en="If all of Earth's water were gathered into one ball, it would be about 1,385 km across. Liquid fresh water: about 272.8 km. Lakes and rivers, where most of our everyday water comes from: about 56.2 km.\n\nSource: USGS Water Science School, How Much Water is There on Earth?",
   desc_ko='지구의 물을 전부 공 하나로 모으면 지름 약 1,385km. 액체 상태 민물은 약 272.8km, 우리가 매일 쓰는 물이 주로 오는 호수와 강의 물은 약 56.2km입니다.\n\n출처: 미국 지질조사국(USGS) Water Science School',
   tags=['지구의 물', 'water on earth', 'USGS', '물 부족', 'fresh water', '민물', 'scale', '규모']),
 'earth_year': dict(title_en="Earth's History in One Year: Your Life Is Half a Second #Shorts", title_ko='지구 45억 년을 1년으로 줄이면, 내 인생은 0.56초',
   desc_en="Squeeze Earth's 4.54 billion years into one calendar year: dinosaurs vanish on Dec 26, Homo sapiens appears at 11:25 PM on Dec 31, farming in the last 83 seconds, writing in the last 35 seconds, and an 80-year life takes about 0.56 seconds.\n\nSources: USGS (age of Earth); Hublin et al., Nature 2017 (Homo sapiens ~300,000 years). Farming ~12,000 and writing ~5,000 years ago are approximate.",
   desc_ko='지구 45억 4천만 년을 1년 달력에 넣으면 공룡은 12월 26일에 사라지고, 호모 사피엔스는 12월 31일 밤 11시 25분에 등장합니다. 농사는 마지막 83초, 문자는 마지막 35초, 80년 인생은 약 0.56초입니다.\n\n출처: USGS(지구 나이), Hublin 외 Nature 2017(호모 사피엔스 약 30만 년). 농사·문자 시점은 대략값',
   tags=['지구 역사', 'earth history', 'cosmic calendar', '우주 달력', '호모 사피엔스', 'deep time', '인생', 'life is short']),
 'solar_bead': dict(title_en='If Earth Were a 1 cm Bead, the Sun Would Be 117 m Away #Shorts', title_ko='지구가 1cm 구슬이면 해는 117m 밖에',
   desc_en='Scale Earth down to a 1 cm bead: the Moon is a 2.7 mm crumb 30 cm away, and the Sun is a 1.1 m ball 117 m away, farther than a soccer pitch is long.\n\nSource: NASA (Sun 1,392,700 km, Earth 12,742 km, Moon 3,475 km wide; Earth-Sun 149.6 million km, Earth-Moon 384,400 km).',
   desc_ko='지구를 1cm 구슬로 줄이면 달은 30cm 떨어진 2.7mm 부스러기, 해는 117m 떨어진 지름 1.1m 공입니다.\n\n출처: NASA(해·지구·달 지름, 지구-해 1억 4,960만 km, 지구-달 38만 4,400km)',
   tags=['태양계 축척', 'solar system scale', '지구', '해', 'sun', 'moon', '달', 'scale model']),
 'sky_apple': dict(title_en='If Earth Were an Apple, the Sky Would Be 0.6 mm Thick #Shorts', title_ko='지구가 사과라면 하늘 두께는 0.6mm',
   desc_en="By a common definition space begins at 100 km, only 1.6% of Earth's radius. Shrink Earth to an 8 cm apple and the sky is about 0.63 mm thick, roughly six sheets of paper.\n\nEarth mean radius 6,371 km (NASA). Karman line 100 km (FAI convention). Paper assumed 0.1 mm thick.",
   desc_ko='흔히 쓰는 기준으로 우주는 100km 위부터, 지구 반지름의 1.6%입니다. 지구를 8cm 사과로 줄이면 하늘 두께는 약 0.63mm, 종이 6장 정도입니다.\n\n지구 평균 반지름 6,371km(NASA), 카르만 선 100km(FAI 기준), 종이 두께 0.1mm 가정',
   tags=['대기', 'atmosphere', '카르만 선', 'karman line', '하늘', 'sky', '지구', 'earth']),
 'heartbeats': dict(title_en='How Many Times Will Your Heart Beat? #Shorts', title_ko='내 심장은 평생 몇 번 뛸까',
   desc_en='At 70 beats per minute, your heart beats about 100,800 times a day, 36.8 million times a year, and nearly 3 billion times over 80 years.\n\nAssuming 70 bpm. Normal adult resting heart rate is 60-100 (American Heart Association). Not medical advice.',
   desc_ko='분당 70회라면 심장은 하루 약 10만 800번, 1년 3,680만 번, 80년이면 약 29억 번 뜁니다.\n\n분당 70회 가정. 성인 정상 안정 시 심박수 60~100회(미국심장협회). 의학적 조언이 아닙니다.',
   tags=['심장', 'heart', '심박수', 'heart rate', 'heartbeat', '건강', '감사', 'gratitude']),
 'sleep': dict(title_en="You'll Spend About 27 Years Asleep #Shorts", title_ko='평생 약 27년을 잠으로 보낸다',
   desc_en='Sleep 8 hours a night and a third of every day is rest. Over an 80-year life that is about 26.7 years with your eyes closed.\n\nAssuming 8 hours of sleep every night for 80 years.',
   desc_ko='하루 8시간을 자면 하루의 3분의 1이 잠입니다. 80년을 살면 약 26.7년을 눈 감고 보냅니다.\n\n80년 동안 매일 8시간 수면 가정',
   tags=['수면', 'sleep', '잠', '인생', 'life', '시간', 'time']),
}
COMMON_TAGS = ['모션그래픽', 'motion graphics', '허상공방', 'Dreamloom Studio']
SIGN_EN = '\nDirected by L.S.M · Dreamloom Studio (Heosang Gongbang)\n\n#shorts #science #scale'
SIGN_KO = '\n연출 L.S.M · 허상공방'

def sh(*a, cwd=None):
    r = subprocess.run(a, cwd=cwd, capture_output=True, text=True)
    if r.returncode: sys.exit(f'FAIL {a[:3]} {r.stderr[-300:]}')
    return r.stdout

d = tempfile.mkdtemp()
sh('git', 'clone', '-q', '--depth', '1', '--branch', 'shorts-outbox', 'https://github.com/mini-ok/ssoksok-channel-assets', d)
idx = json.load(open(f'{d}/index.json'))
for slug in sys.argv[1:]:
    if any(i['slug'] == slug for i in idx['items']): print('skip', slug); continue
    m = META[slug]; now = datetime.datetime.now(datetime.timezone.utc).isoformat(timespec='seconds')
    od = f'{d}/shorts/{slug}'; os.makedirs(od)
    shutil.copy(f'/home/claude/work/scale/out/{slug}.mp4', f'{od}/video.mp4')
    meta = dict(slug=slug, title_en=m['title_en'], title_ko=m['title_ko'], desc_en=m['desc_en'] + SIGN_EN, desc_ko=m['desc_ko'] + SIGN_KO,
                tags=m['tags'] + COMMON_TAGS, related=None, file='video.mp4', created=now)
    json.dump(meta, open(f'{od}/meta.json', 'w'), ensure_ascii=False, indent=1)
    idx['items'].append(dict(slug=slug, dir=f'shorts/{slug}', created=now)); print('add', slug, len(m['title_en']))
json.dump(idx, open(f'{d}/index.json', 'w'), indent=1)
sh('git', 'add', '-A', cwd=d)
sh('git', '-c', 'user.name=claude', '-c', 'user.email=noreply@anthropic.com', 'commit', '-qm', 'outbox: ' + ' '.join(sys.argv[1:]), cwd=d)
sh('git', 'push', '-q', 'origin', 'shorts-outbox', cwd=d)
print('PUSHED'); print(open(f'{d}/index.json').read().count('slug'), 'items')
