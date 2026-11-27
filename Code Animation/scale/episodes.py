"""규모 체감 쇼츠 10편 정의. 숫자마다 출처는 각 항목의 sources(끝 화면에도 나간다).
가정이 들어간 값(심장 70회/분, 하루 8시간 수면, 종이 0.1mm 등)은 sources 줄에 가정이라고 적는다.
"""
import math
from engine import hexc, en_num, ko_num, INK, ramp, clamp

def pal(**kw):
    d = dict(card=(0.975, 0.95, 0.89), cardink=INK, hi=hexc('#e2552e'), hi2=hexc('#a5531c'),
             tag=(0.985, 0.962, 0.91), tagdisc=hexc('#203a5c'), tagicon=(0.98, 0.95, 0.88), tagink=INK,
             ground=hexc('#5b4636'), tower=hexc('#f0b23a'), tower2=hexc('#e07b39'), tick=(0.96, 0.93, 0.86),
             endbg=(0.965, 0.935, 0.87), tile=hexc('#2c3654'), fill=hexc('#f0b23a'), tileink=(0.96, 0.93, 0.86),
             ink=(0.97, 0.94, 0.88), bg0=hexc('#0f1830'), bg1=hexc('#26314d'), stars=1.0,
             sky=[hexc('#f2c46b'), hexc('#e98a4a'), hexc('#7b4a7a'), hexc('#2a2f5e'), hexc('#121a38')])
    d.update(kw); return d

def light_time(km):
    s = km / 299792.458
    if s < 60: return (f'{s:.2f} s' if s < 10 else f'{s:.0f} s'), (f'{s:.2f}초' if s < 10 else f'{s:.0f}초')
    if s < 3600: m, r = divmod(s, 60); return f'{m:.0f} min {r:.0f} s', f'{m:.0f}분 {r:.0f}초'
    if s < 86400 * 2: h, r = divmod(s, 3600); return f'{h:.0f} h {r / 60:.0f} min', f'{h:.0f}시간 {r / 60:.0f}분'
    if s < 86400 * 365.25: return f'{s / 86400:.0f} days', f'{s / 86400:.0f}일'
    return f'{s / 31557600:.1f} years', f'{s / 31557600:.1f}년'

EP = {}

# ---------------------------------------------------------------- 1. 지구의 모든 물
_R = 6371.0
def _on(ang, r): a = math.radians(ang); return (_R + r) * math.cos(a), (_R + r) * math.sin(a)
WX, WY = _on(50, 692.5); FX, FY = _on(66, 136.4); LX, LY = _on(72, 28.1)
EP['water_ball'] = dict(kind='spheres', seed=11, DUR=25.0, t_end=22.0, end_icon='drop',
    title_en_card='ALL THE WATER ON EARTH', title_ko_card='지구의 물을 공 하나로',
    pal=pal(hi=hexc('#2f7fe0'), tagdisc=hexc('#1d4f8f'), bg0=hexc('#0b1428'), bg1=hexc('#1b2a4a')),
    objs=[dict(x=0, y=0, r=_R, kind='ball', col=hexc('#cdb28a'), col2=hexc('#a98d66'), blobs=5, t_in=0.0, rmin=0,
               en='Earth (water removed)', ko='물을 뺀 지구', sen='12,742 km', sko='지름 1만 2,742km', icon='globe', side=-1, lab_out=4.4, ldist=-585, ldy=480),
          dict(x=WX, y=WY, r=692.5, kind='ball', col=hexc('#2f6fd0'), t_in=4.6, rmin=3,
               en='All water on Earth', ko='지구의 모든 물', sen='1,385 km', sko='지름 1,385km', icon='drop', side=-1, lab_out=8.6),
          dict(x=FX, y=FY, r=136.4, kind='ball', col=hexc('#4fa3f0'), t_in=8.6, rmin=3,
               en='Liquid fresh water', ko='액체 상태 민물', sen='272.8 km', sko='지름 272.8km', icon='drop', side=1, lab_out=12.8),
          dict(x=LX, y=LY, r=28.1, kind='ball', col=hexc('#8fd0ff'), t_in=12.6, rmin=4,
               en='Lakes & rivers', ko='호수와 강', sen='56.2 km', sko='지름 56.2km', icon='drop', side=1, lab_out=17.0)],
    cams=[(0, 0, 900, 15500), (3.6, 0, 900, 15500), (6.2, WX, WY, 2300), (8.8, WX, WY, 2300), (11.0, FX, FY, 470),
          (12.8, FX, FY, 470), (15.0, LX, LY, 110), (16.9, LX, LY, 110), (19.6, 600, 1900, 15500)],
    cards=[(0.3, 3.8, ["All of Earth's water", 'in one ball. *How big?*'], ['지구의 물을 전부 모으면', '*얼마나 클까?*']),
           (4.9, 8.6, ['Oceans, ice, groundwater,', 'clouds — *all of it*.'], ['바다·얼음·지하수·구름까지', '*전부* 합쳐도 이만하다']),
           (9.0, 12.8, ['Liquid fresh water:', 'just *272.8 km* across.'], ['그중 액체 상태 민물은', '지름 *272.8km*']),
           (13.0, 17.0, ['Lakes and rivers:', 'a *56 km* drop.'], ['호수와 강의 물은', '지름 *56km* 물방울 하나']),
           (17.4, 22.0, ['Most of the water we use', 'every day comes from *that speck*.'], ['우리가 매일 쓰는 물은', '대부분 *저 작은 점*에서 온다'])],
    sources=['Source: USGS Water Science School, "How Much Water is There on Earth?"'],
    yt=dict(title_en='All of Earth’s Water in One Ball — It’s Tiny #Shorts', title_ko='지구의 물을 공 하나로 모으면'))

# ---------------------------------------------------------------- 2. 지구가 사과라면, 하늘의 두께
AP = 1.0e5
EP['sky_apple'] = dict(kind='spheres', seed=12, DUR=26.4, t_end=23.4, end_icon='globe', wipes=[12.8],
    title_en_card='HOW THIN IS THE SKY?', title_ko_card='하늘은 얼마나 얇을까',
    pal=pal(hi=hexc('#3e8ee8'), tagdisc=hexc('#24507e'), bg0=hexc('#08101f'), bg1=hexc('#14203a')),
    objs=[dict(x=0, y=0, r=_R + 100, ri=_R, kind='ring', col=hexc('#9fd3ff'), t_in=0.0, t_out=12.8),
          dict(x=0, y=0, r=_R, kind='ball', col=hexc('#2c6fbf'), col2=hexc('#4f9b5a'), blobs=9, t_in=0.0, t_out=12.8),
          dict(x=0, y=_R + 8.85, r=0, kind='tick', t_in=6.4, t_out=12.8, en='Mt. Everest', ko='에베레스트', sen='8.8 km', sko='8.8km', icon='mountain', side=-1, ldy=70),
          dict(x=0, y=_R + 11, r=0, kind='tick', t_in=7.0, t_out=12.8, en='Airliners', ko='여객기', sen='~10–12 km', sko='약 10~12km', icon='plane', side=1, ldy=-60),
          dict(x=0, y=_R + 100, r=0, kind='tick', t_in=7.8, t_out=12.8, en='Edge of space', ko='우주의 경계', sen='100 km', sko='100km', icon='rocket', side=-1),
          dict(x=AP, y=0, r=40.63, ri=40.0, kind='ring', col=hexc('#9fd3ff'), t_in=12.8),
          dict(x=AP, y=0, r=40.0, kind='ball', col=hexc('#d33a2c'), col2=hexc('#e9674a'), blobs=3, t_in=12.8,
               en='Earth as an apple', ko='사과만 한 지구', sen='8 cm', sko='지름 8cm', icon='globe', side=-1, ldist=-120, lab_out=15.8),
          dict(x=AP, y=40.63, r=0, kind='tick', t_in=17.4, en='The sky', ko='하늘', sen='0.63 mm', sko='0.63mm', icon='rocket', side=1, ldy=-80)],
    cams=[(0, 0, 0, 15500), (3.8, 0, 0, 15500), (6.4, 0, _R + 45, 330), (12.79, 0, _R + 45, 330), (12.8, AP, 0, 125),
          (15.4, AP, 0, 125), (17.6, AP, 40.4, 3.2)],
    cards=[(0.3, 3.8, ['If Earth were an apple,', 'how thick is *the sky*?'], ['지구가 사과라면', '*하늘*은 얼마나 두꺼울까?']),
           (4.2, 8.4, ['By a common definition,', 'space begins at *100 km*.'], ['흔히 쓰는 기준으로', '우주는 *100km* 위부터']),
           (8.8, 12.6, ['That’s only *1.6%*', 'of Earth’s radius.'], ['지구 반지름의', '*1.6%*밖에 안 된다']),
           (13.4, 18.6, ['Shrink Earth to an *8 cm* apple:', 'the sky is *0.63 mm* thick.'], ['지구를 *8cm* 사과로 줄이면', '하늘 두께는 *0.63mm*']),
           (19.0, 23.4, ['About *6 sheets of paper*.', 'All the air we breathe is in there.'], ['종이 *6장* 두께.', '우리가 숨 쉬는 공기는 다 그 안에'])],
    sources=['Earth mean radius 6,371 km (NASA). Kármán line 100 km (FAI convention).', 'Paper assumed 0.1 mm thick.'],
    yt=dict(title_en='If Earth Were an Apple, the Sky Would Be 0.6 mm Thick #Shorts', title_ko='지구가 사과라면 하늘 두께는 0.6mm'))

# ---------------------------------------------------------------- 3. 지구가 1cm 구슬이면 해는
SUN_D = 1392700 / 12742 * 1.0; AU_CM = 149597871 / 12742 * 1.0; MOON_D = 3474.8 / 12742; MOON_CM = 384400 / 12742
def _solar_hud(t):
    from engine import expo_in_out
    if not (9.6 < t < 22.6): return None
    cy = EP['solar_bead']['_eng'].cam(t)[1]; a = ramp(t, 9.6, 10.0) * (1 - ramp(t, 22.2, 22.6))
    return f'{cy / 100:,.1f} m from Earth' if cy < 1000 else f'{cy / 100:,.0f} m from Earth', f'지구에서 {cy / 100:,.0f}m' if cy >= 1000 else f'지구에서 {cy / 100:,.1f}m', a
EP['solar_bead'] = dict(kind='spheres', seed=13, DUR=26.0, t_end=23.0, end_icon='sun', hud=_solar_hud, screen_cy=1000,
    title_en_card='IF EARTH WERE A 1 CM BEAD', title_ko_card='지구가 1cm 구슬이라면',
    pal=pal(hi=hexc('#f08a24'), tagdisc=hexc('#7a3b12'), bg0=hexc('#120c1c'), bg1=hexc('#2a1d33')),
    objs=[dict(x=0, y=0, x2=0, y2=AU_CM - SUN_D / 2, r=0, kind='path', t_in=9.6),
          dict(x=0, y=0, r=0.5, kind='ball', col=hexc('#2c6fbf'), col2=hexc('#4f9b5a'), blobs=4, t_in=0.0, rmin=8,
               en='Earth', ko='지구', sen='a 1 cm bead', sko='1cm 구슬', icon='globe', side=1, lab_out=9.4, ldist=40),
          dict(x=0, y=MOON_CM, r=MOON_D / 2, kind='ball', col=hexc('#c9c4bb'), t_in=4.0, rmin=5,
               en='The Moon', ko='달', sen='2.7 mm · 30 cm away', sko='2.7mm · 30cm 거리', icon='moon', side=1, lab_out=9.4, ldist=40),
          dict(x=0, y=10500, r=0, kind='tick', t_in=13.6, en='Soccer pitch', ko='축구장 길이', sen='~105 m', sko='약 105m', icon='field', side=-1, lab_out=17.0),
          dict(x=0, y=AU_CM, r=SUN_D / 2, kind='ball', col=hexc('#f6b23a'), col2=hexc('#f7c95e'), blobs=8, t_in=14.6, rmin=6,
               en='The Sun', ko='해', sen='1.1 m ball · 117 m away', sko='1.1m 공 · 117m 거리', icon='sun', side=-1, ldist=40, ldy=420, lab_in=18.6)],
    cams=[(0, 0, 0, 4.5), (3.6, 0, 0, 4.5), (6.4, 0, 15, 48), (9.4, 0, 15, 48), (14.4, 0, 5900, 15000), (15.6, 0, 5900, 15000), (19.2, 0, AU_CM - 20, 230)],
    cards=[(0.3, 3.6, ['Shrink Earth to a *1 cm* bead.', 'Where is *the Sun*?'], ['지구를 *1cm* 구슬로 줄이면', '*해*는 어디에 있을까?']),
           (4.2, 9.2, ['The Moon: a *2.7 mm* crumb,', '*30 cm* away.'], ['달은 *2.7mm* 부스러기,', '*30cm* 떨어져 있다']),
           (9.6, 14.2, ['Now keep walking…'], ['이제 계속 걸어가 보자…']),
           (14.6, 18.8, ['*117 m* away —', 'longer than a soccer pitch.'], ['*117m* 떨어진 곳,', '축구장 길이보다 멀다']),
           (19.2, 23.0, ['The Sun: a *1.1 m* ball.'], ['해는 지름 *1.1m*짜리 공'])],
    sources=['NASA: Sun 1,392,700 km, Earth 12,742 km, Moon 3,475 km wide; Earth–Sun 149.6 million km, Earth–Moon 384,400 km.', 'Scaled so Earth = 1 cm.'],
    yt=dict(title_en='If Earth Were a 1 cm Bead, the Sun Would Be 117 m Away #Shorts', title_ko='지구가 1cm 구슬이면 해는 117m 밖에'))

# ---------------------------------------------------------------- 4. 백만 초 · 10억 초 · 1조 초
EP['seconds'] = dict(kind='ladder', seed=14, v0=1, seg=2.4, end_icon='clock',
    title_en_card='MILLION · BILLION · TRILLION', title_ko_card='백만 초 · 10억 초 · 1조 초',
    pal=pal(hi=hexc('#e2552e')),
    steps=[(60, 'clock', '1 minute', '1분', '60 s', '60초'), (3600, 'clock', '1 hour', '1시간', '3,600 s', '3,600초'),
           (86400, 'sun', '1 day', '하루', '86,400 s', '8만 6,400초'), (1e6, 'calendar', '1 MILLION seconds', '100만 초', '≈ 11.6 days', '약 11.6일'),
           (31557600, 'calendar', '1 year', '1년', '31.6 million s', '약 3,156만 초'), (1e9, 'person', '1 BILLION seconds', '10억 초', '≈ 31.7 years', '약 31.7년'),
           (1e12, 'scroll', '1 TRILLION seconds', '1조 초', '≈ 31,700 years', '약 3만 1,700년')],
    hud=lambda v: (f'{en_num(v)} seconds', f'{ko_num(v)}초'),
    sources=['1 year = 365.25 days. 1 million s = 11.6 days; 1 billion s = 31.7 years; 1 trillion s = 31,688 years.'],
    yt=dict(title_en='A Million Seconds vs a Billion Seconds #Shorts', title_ko='100만 초와 10억 초는 얼마나 다를까'))

# ---------------------------------------------------------------- 5. 뇌 신경세포 860억 개 세기
EP['neurons'] = dict(kind='ladder', seed=15, v0=1, seg=2.8, end_icon='brain',
    title_en_card='COUNT YOUR NEURONS', title_ko_card='내 뇌세포 세어 보기',
    pal=pal(hi=hexc('#d94f8a'), tower=hexc('#e98ab4'), tower2=hexc('#b3507e'), tagdisc=hexc('#5a2346'),
            sky=[hexc('#f3c6c9'), hexc('#d98aa6'), hexc('#8a4f86'), hexc('#3c2b5c'), hexc('#171533')]),
    steps=[(86400, 'sun', '1 day, nonstop', '하루 꼬박', '86,400', '8만 6,400개'), (1e6, 'calendar', '11.6 days', '11.6일', '1 million', '100만 개'),
           (31557600, 'calendar', '1 year, nonstop', '1년 꼬박', '31.6 million', '약 3,156만 개'),
           (2.52e9, 'person', 'Your whole life (80 y)', '평생 80년', '2.5 billion · 3%', '약 25억 개 · 3%'),
           (8.6e10, 'brain', 'All your neurons', '내 뇌의 신경세포', '86 billion', '860억 개')],
    hud=lambda v: (f'{en_num(v)} counted', f'{ko_num(v)}개 셈'),
    sources=['Azevedo et al., J Comp Neurol 2009: adult human brain ≈ 86 billion neurons (average of adult male brains).', 'Counting 1 per second, nonstop.'],
    yt=dict(title_en='Counting Your Brain Cells, One per Second #Shorts', title_ko='뇌 신경세포를 1초에 하나씩 센다면'))

# ---------------------------------------------------------------- 6. 평생 심장 박동
EP['heartbeats'] = dict(kind='ladder', seed=16, v0=1, seg=2.7, end_icon='heart',
    title_en_card='HOW MANY HEARTBEATS?', title_ko_card='평생 심장은 몇 번 뛸까',
    pal=pal(hi=hexc('#e0343a'), tower=hexc('#f06a5a'), tower2=hexc('#b8323a'), tagdisc=hexc('#6e1a22'),
            sky=[hexc('#f6c9a8'), hexc('#ec8f74'), hexc('#a8475a'), hexc('#4a2440'), hexc('#1a1226')]),
    steps=[(70, 'heart', '1 minute', '1분', '70 beats', '70번'), (4200, 'clock', '1 hour', '1시간', '4,200', '4,200번'),
           (100800, 'sun', '1 day', '하루', '100,800', '10만 800번'), (36.8e6, 'calendar', '1 year', '1년', '36.8 million', '3,680만 번'),
           (2.95e9, 'person', '80 years', '80년', '2.9 billion', '약 29억 번')],
    hud=lambda v: (f'{en_num(v)} beats', f'{ko_num(v)}번'),
    sources=['Assuming 70 beats per minute. Normal adult resting heart rate: 60–100 (American Heart Association).'],
    yt=dict(title_en='How Many Times Will Your Heart Beat? #Shorts', title_ko='내 심장은 평생 몇 번 뛸까'))

# ---------------------------------------------------------------- 7. 빛의 속도
EP['light'] = dict(kind='ladder', seed=17, v0=1, seg=2.7, end_icon='bolt',
    title_en_card='HOW FAST IS LIGHT?', title_ko_card='빛은 얼마나 빠를까',
    pal=pal(hi=hexc('#f2b632'), tower=hexc('#ffe08a'), tower2=hexc('#f0b23a'), tagdisc=hexc('#2a2f5e'),
            sky=[hexc('#2a3a6e'), hexc('#1d2752'), hexc('#141b3d'), hexc('#0c1128'), hexc('#05070f')]),
    steps=[(40075, 'globe', 'Around Earth', '지구 한 바퀴', '0.13 s · 7.5 laps/s', '0.13초 · 1초에 7.5바퀴'),
           (384400, 'moon', 'The Moon', '달', '1.3 s', '1.3초'), (1.496e8, 'sun', 'The Sun', '해', '8 min 19 s', '8분 19초'),
           (4.5e9, 'star', 'Neptune', '해왕성', '≈ 4 h 10 min', '약 4시간 10분'),
           (4.01e13, 'star', 'Nearest star', '가장 가까운 별', 'Proxima · 4.2 years', '프록시마 · 4.2년')],
    hud=lambda v: (f'{en_num(v)} km · {light_time(v)[0]}', f'{ko_num(v)}km · {light_time(v)[1]}'),
    sources=['Speed of light 299,792 km/s. Distances: NASA (Moon, Sun, Neptune average; Proxima Centauri 4.24 light-years).'],
    yt=dict(title_en='The Sunlight You See Left the Sun 8 Minutes Ago #Shorts', title_ko='지금 보는 햇빛은 8분 전에 출발했다'))

# ---------------------------------------------------------------- 8. 개미 2경 마리
EP['ants'] = dict(kind='ladder', seed=18, v0=1, seg=3.2, end_icon='ant',
    title_en_card='20 QUADRILLION ANTS', title_ko_card='개미 2경 마리',
    pal=pal(hi=hexc('#d9822b'), tower=hexc('#8a5a3c'), tower2=hexc('#5e3b27'), tagdisc=hexc('#3b2516'),
            sky=[hexc('#cfe3a8'), hexc('#8fbf6a'), hexc('#4f7f4a'), hexc('#2a4a33'), hexc('#13221a')]),
    steps=[(2.5e6, 'ant', 'Ants per person', '사람 한 명당 개미', '2.5 million', '250만 마리'),
           (8e9, 'people', 'All people', '세계 인구', '8 billion+', '80억 명 이상'),
           (2e16, 'ant', 'All ants on Earth', '지구의 모든 개미', '20 quadrillion', '2경 마리')],
    hud=lambda v: (en_num(v), ko_num(v)),
    sources=['Schultheiss et al., PNAS 2022: at least 20 quadrillion ants; 12 megatons of carbon,', 'more than wild birds and mammals combined.'],
    yt=dict(title_en='20 Quadrillion Ants Outweigh All Wild Birds and Mammals #Shorts', title_ko='개미 2경 마리, 야생 새와 포유류보다 무겁다'))

# ---------------------------------------------------------------- 9. 지구 45억 년을 1년 달력에
MON = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
EAGE = 4.54e9
def _pos_year(ya):          # ya년 전 → 1년 달력에서의 위치(0..1)
    return 1 - ya / EAGE
DINO = _pos_year(66e6) * 12
SAP_MIN = 60 - 300000 / EAGE * 365 * 24 * 60            # 마지막 한 시간 안의 분
FARM_MIN = 60 - 12000 / EAGE * 365 * 24 * 60
WRIT_S = 60 - 5000 / EAGE * 365 * 24 * 3600
LIFE_S = 60 - 80 / EAGE * 365 * 24 * 3600
EP['earth_year'] = dict(kind='tiles', seed=19, DUR=32.0, t_end=29.0, end_icon='calendar',
    title_en_card="EARTH'S HISTORY IN ONE YEAR", title_ko_card='지구 45억 년을 1년 달력에',
    pal=pal(hi=hexc('#e2552e'), fill=hexc('#e9a23b'), tile=hexc('#2c3654')),
    levels=[dict(t0=0.0, t1=9.0, cols=3, rows=4, labels=MON, lab_k=0.30, title_en="4.54 billion years = 1 year", title_ko='45억 4천만 년 = 1년',
                 pins=[(0.02, 'globe', 'Earth forms', '지구 탄생', 'Jan 1', '1월 1일'), (DINO, 'dino', 'Dinosaurs gone', '공룡 멸종', 'Dec 26', '12월 26일')]),
            dict(t0=9.0, t1=15.0, cols=4, rows=6, labels=[f'{h:02d}' for h in range(24)], lab_k=0.36, zoom_from=11, title_en='December 31', title_ko='12월 31일',
                 pins=[(23 + SAP_MIN / 60, 'person', 'Homo sapiens', '호모 사피엔스', '11:25 PM', '밤 11시 25분')]),
            dict(t0=15.0, t1=21.0, cols=6, rows=10, labels=[f':{m:02d}' for m in range(60)], lab_k=0.30, zoom_from=23, title_en='11 PM → midnight', title_ko='밤 11시 → 자정',
                 pins=[(SAP_MIN, 'person', 'Homo sapiens', '호모 사피엔스', '23:25', '밤 11시 25분'), (FARM_MIN, 'wheat', 'Farming begins', '농사 시작', '23:58:37', '밤 11시 58분 37초')]),
            dict(t0=21.0, t1=28.0, cols=6, rows=10, labels=[f'{s}s' for s in range(60)], lab_k=0.28, zoom_from=59, title_en='The last minute', title_ko='마지막 1분',
                 pins=[(WRIT_S, 'scroll', 'Writing', '문자', 'last 35 s', '마지막 35초'), (LIFE_S, 'person', 'Your 80-year life', '나의 80년 인생', 'last 0.56 s', '마지막 0.56초')])],
    cards=[(0.3, 3.8, ["Squeeze Earth's *4.54 billion years*", 'into one calendar year.'], ['지구 *45억 4천만 년*을', '1년 달력에 넣으면']),
           (9.2, 14.8, ['Humans appear on', '*Dec 31, 11:25 PM*.'], ['인류는 *12월 31일*', '*밤 11시 25분*에 등장']),
           (15.2, 20.8, ['Farming: the last *83 seconds*.'], ['농사는 마지막 *83초*']),
           (21.2, 26.4, ['Writing: the last *35 seconds*.'], ['문자는 마지막 *35초*']),
           (26.6, 29.0, ['Your whole life:', '*half a second*.'], ['나의 80년 인생은', '*0.56초*'])],
    sources=['USGS: Earth ≈ 4.54 billion years old. Hublin et al., Nature 2017: Homo sapiens ≈ 300,000 years.', 'Farming ≈ 12,000 and writing ≈ 5,000 years ago (approximate).'],
    yt=dict(title_en='Earth’s History in One Year: Your Life Is Half a Second #Shorts', title_ko='지구 45억 년을 1년으로: 내 인생은 0.56초'))

# ---------------------------------------------------------------- 10. 평생 잠
NIGHT_H = {23, 0, 1, 2, 3, 4, 5, 6}
def _day_col(p):
    return lambda i: p['fill2'] if i in NIGHT_H else p['tile']
_P10 = pal(hi=hexc('#7d8cf0'), fill=hexc('#3b4bb8'), tile=hexc('#e8c87a'), tileink=INK, bg0=hexc('#121633'), bg1=hexc('#262c56'))
_P10['fill2'] = hexc('#3b4bb8')
EP['sleep'] = dict(kind='tiles', seed=20, DUR=25.0, t_end=22.0, end_icon='bed',
    title_en_card='YEARS OF SLEEP', title_ko_card='평생 잠자는 시간', pal=_P10,
    levels=[dict(t0=0.0, t1=8.0, cols=4, rows=6, labels=[f'{h:02d}' for h in range(24)], lab_k=0.36, fill=(0, 0), cell_col=_day_col(_P10),
                 title_en='One day: 8 of 24 hours', title_ko='하루 24시간 중 8시간'),
            dict(t0=8.0, t1=18.0, cols=8, rows=10, labels=[str(y + 1) if (y + 1) % 10 == 0 else '' for y in range(80)], lab_k=0.40, fill=(0, 1 / 3),
                 title_en='An 80-year life', title_ko='80년 인생',
                 pins=[(26.6, 'bed', 'Asleep', '잠든 시간', '26.7 years', '26.7년')])],
    cards=[(0.3, 3.8, ['Sleep *8 hours* a night.', 'How much of your life is that?'], ['하루 *8시간* 잔다면,', '인생에서 얼마일까?']),
           (4.2, 8.0, ['That’s *1/3* of every day.'], ['하루의 *3분의 1*']),
           (8.4, 17.8, ['Over 80 years…'], ['80년을 살면…']),
           (18.0, 22.0, ['*26.7 years*', 'with your eyes closed.'], ['*26.7년*을', '눈 감고 보낸다'])],
    sources=['Assuming 8 hours of sleep every night for 80 years.'],
    yt=dict(title_en='You’ll Spend 26 Years Asleep #Shorts', title_ko='평생 26년을 잠으로 보낸다'))

# ---------------------------------------------------------------- 사다리 공통: 카드·시간표
for k, e in EP.items():
    if e['kind'] != 'ladder': continue
    n = len(e['steps']); t0 = 3.2; tl = t0 + n * e['seg']
    e.setdefault('t_start', t0)
    hook = dict(seconds=(['1 million seconds vs', '*1 billion* seconds?'], ['100만 초와 *10억 초*,', '얼마나 다를까?']),
                neurons=(['Count your brain cells,', '*one per second*.'], ['뇌 신경세포를', '*1초에 하나씩* 센다면?']),
                heartbeats=(['How many times will', 'your heart *beat*?'], ['내 심장은 평생', '*몇 번* 뛸까?']),
                light=(['Light: the fastest thing', 'in the universe.'], ['우주에서 가장 빠른 *빛*,', '얼마나 빠를까?']),
                ants=(['How many *ants*', 'live on Earth?'], ['지구에 *개미*는', '몇 마리나 살까?']))[k]
    punch = dict(seconds=[(['1 million s ≈ *11.6 days*', '1 billion s ≈ *31.7 years*'], ['100만 초는 *11.6일*,', '10억 초는 *31.7년*']),
                          (['1 trillion s ≈ *31,700 years*'], ['1조 초는 *3만 1,700년*'])],
                 neurons=[(['86 billion, one per second:', '*2,700+ years*.'], ['860억 개를 1초에 하나씩:', '*2,700년 넘게*'])],
                 heartbeats=[(['About *3 billion* beats,', 'never a day off.'], ['평생 약 *30억 번*,', '하루도 쉬지 않는다'])],
                 light=[(['The sunlight on your face', 'left the Sun *8 minutes* ago.'], ['지금 얼굴에 닿은 햇빛은', '*8분 전*에 해를 떠났다'])],
                 ants=[(['*20 quadrillion* —', '2.5 million for each of us.'], ['*2경 마리*,', '사람 한 명당 *250만 마리*']),
                       (['Together they outweigh', 'all wild birds and mammals.'], ['모두 합치면 야생 새와', '포유류를 합친 것보다 *무겁다*'])])[k]
    cards = [(0.3, t0 + 0.2, hook[0], hook[1])]
    tp = tl
    for (en, ko) in punch:
        cards.append((tp, tp + 4.0, en, ko)); tp += 4.0
    e['cards'] = cards; e['t_end'] = tp + 0.2; e['DUR'] = tp + 3.2

CODA = {
 'water_ball': [("Eight billion people", "80억 명이"), ("share that one small drop.", "저 작은 물방울 하나를 나눠 마신다"), ("Every glass of water is a gift.", "물 한 잔은 선물이다")],
 'sky_apple': [("Every breath you have ever taken", "당신이 쉰 모든 숨은"), ("came from a sky thinner than paper.", "종이보다 얇은 하늘에서 왔다"), ("Breathe slowly. It is borrowed.", "천천히 쉬자, 빌려 쉬는 숨이니까")],
 'solar_bead': [("Between us and the Sun:", "해와 우리 사이에는"), ("almost nothing but empty space.", "거의 텅 빈 공간뿐"), ("That we are here at all is a miracle.", "우리가 여기 있다는 것 자체가 기적이다")],
 'seconds': [("A billion seconds is about 31 years.", "10억 초는 약 31년"), ("Nobody gets many billions.", "누구에게도 많이 주어지지 않는다"), ("Spend this second well.", "지금 이 1초를 아껴 쓰자")],
 'neurons': [("You could count for a lifetime", "평생을 세어도"), ("and never finish counting yourself.", "나를 다 셀 수 없다"), ("There is a universe inside you.", "당신 안에 우주가 있다")],
 'heartbeats': [("Three billion beats,", "30억 번을 뛰는 동안"), ("and it never once asked for thanks.", "한 번도 고맙다는 말을 바라지 않았다"), ("Tonight, put a hand on your chest.", "오늘 밤, 가슴에 손을 얹어 보자")],
 'light': [("Every star you see tonight", "오늘 밤 보이는 별빛은"), ("is light from the past.", "모두 지나간 시간의 빛이다"), ("Love the people beside you now.", "곁에 있는 사람은 지금 사랑하자")],
 'ants': [("The smallest things, together,", "가장 작은 것들이 모이면"), ("carry the greatest weight.", "가장 무거운 것이 된다"), ("Never underestimate a small kindness.", "작은 친절을 얕보지 말자")],
 'earth_year': [("Half a second", "1년 중 0.56초"), ("out of a whole year.", "그것이 우리의 한평생"), ("Life is short. Spend it on what matters.", "삶은 짧다, 소중한 것에 쓰자")],
 'sleep': [("We give a third of life to rest,", "인생의 3분의 1을 쉼에 내어주고"), ("and wake each morning, given another day.", "매일 아침 하루를 다시 선물 받는다"), ("Every morning is a second chance.", "아침은 날마다 오는 두 번째 기회다")],
}
from engine import coda_len
for k, e in EP.items():
    e.setdefault('flash', [])
    e['coda'] = CODA[k]; e['t_coda'] = e['t_end']
    L = coda_len(e); e['t_end'] += L; e['DUR'] += L
