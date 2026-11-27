"""nova 쇼츠를 shorts-outbox 브랜치에 넣는다(업로더가 한 번에 per_run 편씩 올림).
사용: cd /tmp && python3 outbox_nova.py <slug> [slug ...]   (slug는 아래 META 첫 칸)
영상 위치: 환경 변수 NOVA_OUT(기본 /home/claude/work/nova/out)의 <ep>.mp4.
새 편 추가: META 끝에 (slug, ep, title_en, title_ko, desc_en, desc_ko, tags) 한 줄. title_en·desc_en에 한글 금지, 제목 100자 이하.
"""
import datetime, json, os, shutil, subprocess, sys, tempfile

SIGN_EN = '\nDirected by L.S.M · Dreamloom Studio (Heosang Gongbang)\n\n#shorts #science'
SIGN_KO = '\n연출 L.S.M · 허상공방'
COMMON = ['모션그래픽', 'motion graphics', '허상공방', 'Dreamloom Studio']
OUT = os.environ.get('NOVA_OUT', '/home/claude/work/nova/out')

META = [
 ('gold_cube', 'gold',
  "All the Gold Ever Mined Fits in One 22.5 m Cube #Shorts", '인류가 캔 금을 다 모으면 한 변 22.5m 정육면체',
  "About 220,000 tonnes of gold exist above ground. Melted into one cube, it would be about 22.5 m on each side, roughly a 7-story building. Shared by everyone on Earth, that is about 27 g each.\n\nSource: World Gold Council (above-ground stocks). Per-person figure calculated with about 8.2 billion people.",
  "땅 위에 있는 금은 약 22만 톤입니다. 녹여 정육면체 하나로 만들면 한 변이 약 22.5m, 7층 건물 높이쯤입니다. 지구 사람 모두가 나누면 1인당 약 27g입니다.\n\n출처: World Gold Council(지상 금 재고). 1인당 값은 세계 인구 약 82억 명으로 계산.",
  ['금', 'gold', 'all the gold ever mined', '금 정육면체', 'gold cube', '규모 체감', 'scale comparison']),
 ('octopus_hearts', 'octopus',
  "An Octopus Has Three Hearts, and One Stops When It Swims #Shorts", '문어의 심장은 셋, 헤엄칠 땐 하나가 멈춘다',
  "Two hearts push blood through the gills; one pumps it to the body. The blood is blue because copper-based hemocyanin, not iron, carries oxygen. When an octopus swims, the body heart stops beating, which is one reason it would rather crawl.\n\nSources: Smithsonian Magazine, \"Ten Wild Facts About Octopuses\"; Shedd Aquarium; Live Science.",
  "아가미 심장 둘이 아가미로 피를 보내고, 온몸 심장 하나가 몸으로 보냅니다. 철 대신 구리 기반 헤모시아닌이 산소를 날라 피가 파랗습니다. 헤엄칠 때는 온몸 심장이 멈춰서, 문어는 헤엄보다 기어 다니기를 더 합니다.\n\n출처: Smithsonian Magazine, Shedd Aquarium, Live Science",
  ['문어', 'octopus', 'three hearts', '심장 세 개', 'blue blood', '푸른 피', '바다 생물', 'ocean animals']),
 ('earth_speed', 'spin',
  "You're Moving Faster Than Sound Right Now #Shorts", '가만히 있어도 당신은 소리보다 빠르다',
  "Earth spins at 1,674 km/h at the equator (about 1,330 km/h in Seoul), faster than sound (about 1,235 km/h). It also circles the Sun at about 107,000 km/h, roughly 30 km every second.\n\nSource: Britannica, \"What is Earth's velocity?\". Seoul value calculated from latitude 37.57°N. Speed of sound: 343 m/s at 20 °C.",
  "적도에서 지구는 시속 1,674km로 돕니다(서울은 약 1,330km). 소리(시속 약 1,235km)보다 빠릅니다. 태양 둘레는 시속 약 10만 7천km, 1초에 약 30km를 갑니다.\n\n출처: Britannica. 서울 값은 북위 37.57°로 계산. 소리 속도는 20°C에서 초속 343m.",
  ['지구 자전', 'earth rotation', '공전 속도', 'orbital speed', '소리보다 빠르다', 'faster than sound', '우주', 'space']),
 ('people_ever', 'people',
  "117 Billion People Have Ever Lived. You Are One of the 7% #Shorts", '지금까지 태어난 사람 1,170억 명, 살아 있는 건 7%',
  "About 117 billion people have been born since 190,000 BCE. Everyone alive today, about 8 billion, is roughly 7% of them. For each person alive, about 14 lived before.\n\nSource: Population Reference Bureau, Kaneda & Haub, \"How Many People Have Ever Lived on Earth?\" (2022 update). The \"about 14\" figure is calculated: (117 - 8) / 8.",
  "기원전 19만 년 이후 태어난 사람은 약 1,170억 명입니다. 지금 살아 있는 약 80억 명은 그중 7% 정도입니다. 지금 사는 한 사람마다 앞서 산 사람이 약 14명입니다.\n\n출처: Population Reference Bureau(2022 갱신). '약 14명'은 (117 − 8) ÷ 8로 계산.",
  ['인구', 'population', 'how many people have ever lived', '인류 역사', 'human history', '삶', 'life']),
 ('cells_37t', 'cells',
  "You Are Made of 37 Trillion Cells #Shorts", '나는 세포 37조 개로 이루어져 있다',
  "An adult human body has about 37.2 trillion cells, and roughly 70% of them are red blood cells. Counting one per second would take over a million years, longer than our species has existed.\n\nSources: Bianconi et al., Annals of Human Biology 2013; BioNumbers; Hublin et al., Nature 2017.",
  "성인의 몸은 세포 약 37조 2천억 개로 이루어져 있고, 그중 약 70%가 적혈구입니다. 1초에 하나씩 세면 100만 년이 넘게 걸립니다. 인류가 존재한 시간보다 깁니다.\n\n출처: Bianconi 외, Annals of Human Biology 2013; BioNumbers; Hublin 외, Nature 2017",
  ['세포', 'cells', '37 trillion cells', '인체', 'human body', '적혈구', 'biology']),
 ('sharks_trees', 'sharks',
  "Sharks Are Older Than Trees #Shorts", '상어는 나무보다 먼저 지구에 있었다',
  "Shark-like scales appear in the fossil record about 450 million years ago (debated), and undisputed shark scales about 420 million years ago. The first trees came about 385 million years ago.\n\nSources: Natural History Museum (UK); Live Science, \"Are sharks really older than trees?\"",
  "상어 비슷한 비늘 화석은 약 4억 5천만 년 전(논쟁 있음), 확실한 상어 비늘은 약 4억 2천만 년 전에 나타납니다. 최초의 나무는 약 3억 8,500만 년 전입니다.\n\n출처: 영국 자연사박물관, Live Science",
  ['상어', 'sharks', 'older than trees', '화석', 'fossils', '진화', 'evolution']),
 ('cleopatra_moon', 'cleo',
  "Cleopatra Lived Closer to the Moon Landing Than to the Pyramids #Shorts", '클레오파트라는 피라미드보다 달 착륙에 더 가깝다',
  "The Great Pyramid was built around 2560 BC. Cleopatra was born in 69 BC, about 2,490 years later. The Moon landing in 1969 came about 2,040 years after her birth.\n\nSources: Great Pyramid ~2560 BC (estimates 2580-2510 BC); Cleopatra VII 69-30 BC; Apollo 11, 1969.",
  "기자의 대피라미드는 기원전 2560년쯤 지어졌습니다. 클레오파트라는 그로부터 약 2,490년 뒤인 기원전 69년에 태어났고, 달 착륙(1969년)은 그녀가 태어난 뒤 약 2,040년 만입니다.\n\n출처: 대피라미드 기원전 2560년경(추정 2580~2510년), 클레오파트라 7세 기원전 69~30년, 아폴로 11호 1969년",
  ['클레오파트라', 'Cleopatra', '피라미드', 'pyramids', '달 착륙', 'moon landing', '역사', 'history']),
 ('stardust', 'stardust',
  "About 90% of Your Body Was Made Inside Stars #Shorts", '내 몸의 약 90%는 별에서 만들어졌다',
  "By mass your body is about 65% oxygen, 18% carbon, 10% hydrogen and 3% nitrogen. The hydrogen dates from the Big Bang; most of the rest was forged in stars.\n\nSource: NASA Chandra X-ray Observatory, \"Elements in the human body\" (2019).",
  "몸무게 기준으로 몸은 산소 약 65%, 탄소 18%, 수소 10%, 질소 3%입니다. 수소는 빅뱅 때 생겼고, 나머지 대부분은 별 속에서 만들어졌습니다.\n\n출처: NASA 찬드라 X선 관측소, \"Elements in the human body\"(2019)",
  ['별먼지', 'stardust', '원소', 'elements', '우주', 'space', '인체', 'human body']),
 ('honey_spoon', 'honey',
  "One Spoonful of Honey Is the Life of 12 Bees #Shorts", '꿀 한 숟갈은 꿀벌 12마리의 일생',
  "A worker bee makes about 1/12 of a teaspoon of honey in her whole life. One teaspoon is the life's work of about 12 bees.\n\nSource: PBS NOVA, \"The Buzz About Bees\" (approximate figure).",
  "일벌 한 마리가 평생 만드는 꿀은 약 12분의 1 티스푼입니다. 티스푼 하나는 꿀벌 약 12마리의 일생입니다.\n\n출처: PBS NOVA, \"The Buzz About Bees\"(대략적인 값)",
  ['꿀', 'honey', '꿀벌', 'bees', '자연', 'nature']),
 ('breaths', 'breath',
  "You Take About 20,000 Breaths a Day #Shorts", '나는 하루 약 2만 번 숨을 쉰다',
  "A resting adult breathes 12 to 20 times a minute: about 17,000 to 29,000 breaths a day, and 500 to 800 million in a lifetime.\n\nSources: American Lung Association; NCBI StatPearls. Daily and lifetime totals are calculated from that range.",
  "쉬고 있는 성인은 1분에 12~20번 숨을 쉽니다. 하루 약 1만 7천~2만 9천 번, 평생 5억~8억 번입니다.\n\n출처: 미국폐협회, NCBI StatPearls. 하루·평생 값은 그 범위로 계산.",
  ['호흡', 'breathing', '숨', 'breath', '명상', 'mindfulness', '인체', 'human body']),
]

META += [
 ('lightning_sun', 'lightning', "Lightning Is 5 Times Hotter Than the Sun #Shorts", '번개는 해 표면보다 5배 뜨겁다',
  "A lightning bolt heats the air to about 30,000°C, roughly five times the temperature of the Sun's surface. The air explodes outward, and that is thunder. Count the seconds from flash to thunder and divide by 3 to get the distance in kilometres.\n\nSources: NOAA SciJinks; National Weather Service. Flash-to-bang rule uses the speed of sound (~343 m/s).",
  "번개는 주변 공기를 약 3만°C까지 달굽니다. 해 표면의 약 5배입니다. 달궈진 공기가 터져 나가는 소리가 천둥이고, 번쩍인 뒤 천둥까지 초를 세어 3으로 나누면 대략의 거리(km)가 나옵니다.\n\n출처: NOAA SciJinks, 미국 기상청(NWS). 거리 계산은 소리 속도(초속 약 343m) 기준",
  ['번개', 'lightning', '천둥', 'thunder', '날씨', 'weather', '안전', 'safety']),
 ('voyager_lightday', 'voyager', "Voyager 1 Is Now One Light-Day From Earth #Shorts", '보이저 1호, 빛으로 하루 거리에 닿다',
  "Launched in 1977, Voyager 1 reached one light-day from Earth on Nov. 18, 2026, about 25.9 billion km away. A message now takes a full day to arrive and two days to get a reply. In 1990 it looked back and saw Earth as a pale blue dot.\n\nSource: NASA/JPL (Nov. 2026).",
  "1977년에 떠난 보이저 1호가 2026년 11월 18일 지구에서 빛으로 하루 거리(약 259억 km)에 닿았습니다. 말 한마디가 닿는 데 하루, 대답을 듣는 데 이틀이 걸립니다. 1990년에는 뒤돌아 지구를 '창백한 푸른 점'으로 찍었습니다.\n\n출처: NASA/JPL(2026년 11월)",
  ['보이저 1호', 'Voyager 1', '광일', 'light-day', '창백한 푸른 점', 'pale blue dot', '우주', 'space']),
 ('trees_422', 'trees', "There Are 422 Trees for Every Person on Earth #Shorts", '지구의 나무, 한 사람에 422그루',
  "Earth has about 3.04 trillion trees, roughly 422 for every person, more than the stars in our galaxy. But we lose about 15 billion trees a year, and the total has fallen by nearly half since farming began.\n\nSource: Crowther et al., Nature 525, 201-205 (2015).",
  "지구에는 나무가 약 3조 400억 그루, 한 사람에 약 422그루 있습니다. 우리 은하의 별보다 많습니다. 하지만 해마다 약 150억 그루가 사라지고, 농사가 시작된 뒤로 거의 절반이 줄었습니다.\n\n출처: Crowther 외, Nature 525 (2015)",
  ['나무', 'trees', '숲', 'forest', '환경', 'environment', '기후', 'climate']),
 ('moon_drift', 'moon', "The Moon Moves 3.8 cm Away Every Year #Shorts", '달은 해마다 3.8cm씩 멀어진다',
  "The Moon drifts about 3.8 cm farther from Earth every year, roughly as fast as fingernails grow. Over a lifetime that is about 3 metres. Scientists measure it by bouncing lasers off mirrors left on the Moon by Apollo astronauts.\n\nSources: NASA (via Live Science, EarthSky). Lifetime figure calculated for 80 years.",
  "달은 해마다 약 3.8cm씩 지구에서 멀어집니다. 손톱이 자라는 속도쯤입니다. 한평생이면 약 3m이고, 아폴로가 달에 두고 온 반사판에 레이저를 쏴서 잽니다.\n\n출처: NASA(Live Science, EarthSky 인용). 평생 값은 80년으로 계산",
  ['달', 'moon', '아폴로', 'Apollo', '천문', 'astronomy', '우주', 'space']),
 ('antarctica_58m', 'ice', "If Antarctica Melted, Seas Would Rise 58 Meters #Shorts", '남극 얼음이 다 녹으면 바다가 58m 높아진다',
  "Antarctica holds about 60% of the world's fresh water. If all its ice melted, global sea level would rise about 58 m, roughly a 19-story building. It is losing around 150 billion tonnes of ice a year.\n\nSources: NASA Sea Level Change; Shiklomanov (1993) for the fresh-water share. 19 floors assumes 3 m per floor.",
  "남극 얼음은 지구 민물의 약 60%입니다. 모두 녹으면 해수면이 약 58m, 19층 건물 높이만큼 오릅니다. 지금도 해마다 약 1,500억 톤씩 줄고 있습니다.\n\n출처: NASA 해수면 변화팀, Shiklomanov(1993). 19층은 한 층 3m 가정",
  ['남극', 'Antarctica', '해수면', 'sea level', '빙하', 'ice sheet', '기후', 'climate']),
 ('sunlight_8min', 'sunlight', "The Sunlight You See Is 8 Minutes Old #Shorts", '지금 보는 햇빛은 8분 20초 전의 빛',
  "Sunlight takes about 8 minutes 20 seconds to cross the 150 million km to Earth. Moonlight is about 1.3 seconds old, and light from the nearest star over four years old. If the Sun vanished, we would not know for about eight minutes.\n\nSources: Smithsonian How Things Fly; UCAR. Moonlight figure calculated.",
  "햇빛은 1억 5천만 km를 건너오는 데 약 8분 20초가 걸립니다. 달빛은 약 1.3초 전, 가장 가까운 별빛은 4년도 더 전의 빛입니다. 해가 사라져도 8분 동안은 모릅니다.\n\n출처: 스미소니언 How Things Fly, UCAR. 달빛 값은 계산",
  ['햇빛', 'sunlight', '빛의 속도', 'speed of light', '해', 'sun', '우주', 'space']),
 ('bluewhale_heart', 'whale', "A Blue Whale's Heart Weighs as Much as a Piano #Shorts", '흰긴수염고래의 심장은 피아노 한 대 무게',
  "The blue whale is the largest animal ever. Its heart weighs about 180 kg, as much as a piano, can be heard about 3 km away, and pushes about 227 litres with each beat. A human heart pushes about 70 mL.\n\nSource: NOAA Fisheries, Big-Hearted Blue Whale.",
  "흰긴수염고래는 역대 가장 큰 동물입니다. 심장 무게만 약 180kg으로 피아노 한 대만 하고, 심장 소리는 3km 밖에서도 들리며, 한 번 뛸 때 약 227L를 보냅니다. 사람 심장은 약 70mL입니다.\n\n출처: NOAA Fisheries",
  ['흰긴수염고래', 'blue whale', '고래', 'whale', '바다', 'ocean', '동물', 'animals']),
 ('words_16000', 'words', "You Speak About 16,000 Words a Day #Shorts", '나는 하루 1만 6천 단어를 말한다',
  "People speak about 16,000 words a day, men and women alike. That is almost 6 million words a year and about 350 million over a lifetime, roughly 450 times the length of the Bible.\n\nSource: Mehl et al., Science 2007 (396 participants). Yearly and lifetime totals calculated; King James Bible about 783,000 words.",
  "사람은 하루 약 1만 6천 단어를 말하고, 남녀 차이는 거의 없습니다. 1년이면 거의 600만, 평생이면 약 3억 5천만 단어, 성경 450권 분량입니다.\n\n출처: Mehl 외, Science 2007. 연간·평생 값은 계산(킹 제임스 성경 약 78만 단어)",
  ['말', 'words', '대화', 'conversation', '언어', 'language', '심리', 'psychology']),
 ('ocean_oxygen', 'plankton', "Half the Oxygen You Breathe Comes From the Ocean #Shorts", '숨 두 번에 한 번은 바다가 만든 산소',
  "About half of Earth's oxygen is made in the ocean, mostly by plankton too small to see. Prochlorococcus alone makes up to 20% of the biosphere's oxygen, and diatoms, algae in glass shells, supply about one in every five breaths.\n\nSources: NOAA Ocean Service; Woods Hole Oceanographic Institution (diatom estimate).",
  "지구 산소의 약 절반은 바다에서, 대부분 눈에 보이지 않는 플랑크톤이 만듭니다. 프로클로로코쿠스 하나가 생물권 산소의 최대 20%를, 유리 껍데기를 입은 규조류가 숨 다섯 번에 한 번의 산소를 만듭니다.\n\n출처: NOAA, 우즈홀 해양연구소(규조류 추정치)",
  ['산소', 'oxygen', '플랑크톤', 'plankton', '바다', 'ocean', '규조류', 'diatoms']),
 ('olympus_mons', 'olympus', "The Tallest Mountain in the Solar System Is 2.5x Everest #Shorts", '화성 올림푸스산은 에베레스트의 2.5배',
  "Olympus Mons on Mars stands 21.9 km high, about 2.5 times Mount Everest, and is roughly 600 km across, about the size of Arizona. It is so broad that standing on it would feel like a gentle slope.\n\nSources: NASA Photojournal (MOLA height); Space.com.",
  "화성의 올림푸스산은 높이 21.9km로 에베레스트의 약 2.5배, 폭은 약 600km로 미국 애리조나주만 합니다. 너무 넓어서 그 위에 서면 완만한 비탈처럼 느껴집니다.\n\n출처: NASA Photojournal(MOLA 고도), Space.com",
  ['올림푸스산', 'Olympus Mons', '화성', 'Mars', '에베레스트', 'Everest', '우주', 'space']),
]

META += [
 ('body_heat', 'heat', "Your Body Gives Off About as Much Heat as a 100 W Bulb #Shorts", '사람 몸은 100W 전구만큼 열을 낸다',
  "At rest, a person gives off roughly 100 watts of heat, about as much as an old incandescent bulb. Put 500 people in a theater and that is around 50 kW. That is why standing close keeps us warm.\n\nSources: University of Illinois Physics (resting human power ~100 W); Big Think (500 people at ~100 W each = 50 kW).",
  "가만히 있어도 사람 몸은 약 100W의 열을 냅니다. 옛 백열전구 하나만큼입니다. 극장에 500명이 모이면 약 50kW. 그래서 가까이 있으면 따뜻합니다.\n\n출처: 일리노이대 물리학과(안정 시 약 100W), Big Think(500명 × 100W = 50kW)",
  ['체온', 'body heat', '열', 'heat', '와트', 'watts', '인체', 'human body']),
 ('light_laps', 'light', "Light Circles the Earth 7.5 Times in One Second #Shorts", '빛은 1초에 지구를 7.5바퀴 돈다',
  "Light travels 299,792 km every second, enough to circle Earth about 7.5 times. It reaches the Moon in 1.28 seconds and takes about 8 minutes 20 seconds to arrive from the Sun. Nothing can go faster.\n\nSources: SI definition of the speed of light; Earth circumference 40,075 km (laps calculated).",
  "빛은 1초에 299,792km를 갑니다. 지구를 약 7.5바퀴 도는 거리입니다. 달까지 1.28초, 해에서 오는 데는 약 8분 20초. 그보다 빠른 것은 없습니다.\n\n출처: SI 빛의 속도 정의, 지구 둘레 40,075km(바퀴 수는 계산)",
  ['빛의 속도', 'speed of light', '빛', 'light', '물리', 'physics', '지구', 'Earth']),
 ('pantheon_dome', 'pantheon', "This 1,900-Year-Old Concrete Dome Is Still the Largest #Shorts", '1,900년 된 판테온 돔, 아직도 세계 최대',
  "Rome's Pantheon was finished around AD 126. Its 43.3 m dome is still the largest unreinforced concrete dome in the world, and its height equals its width, so a 43 m sphere would fit perfectly inside. Sunken coffers make it lighter.\n\nSources: ENR; World History Encyclopedia.",
  "로마 판테온은 서기 126년경 완공됐습니다. 지름 43.3m의 돔은 지금도 철근 없는 콘크리트 돔 가운데 가장 크고, 높이와 폭이 같아 지름 43m 공이 꼭 들어맞습니다. 우물 같은 홈이 무게를 덜어 줍니다.\n\n출처: ENR, World History Encyclopedia",
  ['판테온', 'Pantheon', '로마', 'Rome', '건축', 'architecture', '콘크리트', 'concrete']),
 ('halley_once', 'halley', "Halley's Comet Returns Only Once in a Lifetime #Shorts", '핼리 혜성, 평생 한 번',
  "Halley's Comet comes back about every 76 years. It was last seen in 1986 and returns in July 2061. That is about the length of one human life, so most people see it only once.\n\nSources: NASA Science; Britannica.",
  "핼리 혜성은 평균 약 76년마다 돌아옵니다. 마지막은 1986년, 다음은 2061년 7월. 사람 한 평생과 비슷해 대부분은 평생 한 번 봅니다.\n\n출처: NASA Science, 브리태니커",
  ['핼리 혜성', "Halley's Comet", '혜성', 'comet', '2061', '우주', 'space', '천문', 'astronomy']),
 ('tern_moon', 'tern', "This 100 g Bird Flies to the Moon and Back Three Times #Shorts", '100g 새가 평생 달까지 세 번 왕복',
  "The Arctic tern weighs about 100 grams, yet flies from the Arctic to Antarctica and back every year, about 70,900 km. Over 30 or more years that adds up to more than 2.4 million km, about three round trips to the Moon.\n\nSource: Egevang et al. 2010, PNAS (British Antarctic Survey).",
  "북극제비갈매기는 몸무게 100g 남짓인데 해마다 북극에서 남극까지 약 70,900km를 왕복합니다. 30년 넘게 살며 평생 240만km 이상, 달까지 약 세 번 왕복하는 거리입니다.\n\n출처: Egevang 외 2010, PNAS(영국 남극조사소)",
  ['북극제비갈매기', 'Arctic tern', '철새', 'migration', '새', 'bird', '달', 'Moon']),
 ('methuselah_tree', 'bristlecone', "This Tree Is Older Than the Pyramids #Shorts", '피라미드보다 오래 산 나무, 므두셀라',
  "Methuselah, a bristlecone pine in California's White Mountains, is about 4,855 years old. It sprouted before the Great Pyramid was finished. Cold, dry, high ground makes it grow very slowly, with dense wood that resists decay.\n\nSources: Guinness World Records; Wikipedia; WorldAtlas.",
  "캘리포니아 화이트산맥의 브리슬콘소나무 므두셀라는 약 4,855살입니다. 대피라미드가 완성되기 전에 싹을 틔웠습니다. 춥고 메마른 높은 땅에서 아주 느리게 자라 썩지 않는 단단한 나무가 됐습니다.\n\n출처: 기네스 세계기록, Wikipedia, WorldAtlas",
  ['므두셀라', 'Methuselah', '브리슬콘소나무', 'bristlecone pine', '나무', 'tree', '피라미드', 'pyramid']),
 ('green_sahara', 'sahara', "The Sahara Was Green Just 6,000 Years Ago #Shorts", '사하라가 초록이던 때',
  "Between about 11,000 and 5,000 years ago, the Sahara had grasslands, lakes and rivers, with about ten times today's rain. Shifts in Earth's orbit move the monsoon, and a green Sahara returns roughly every 20,000 years.\n\nSources: deMenocal & Tierney 2012 (Nature Education); Tierney et al. 2017 (Science Advances); Eos.",
  "약 1만1천~5천 년 전 사하라에는 초원과 호수, 강이 있었고 비는 지금의 약 10배 내렸습니다. 지구 궤도가 흔들리며 몬순이 옮겨 가고, 초록 사하라는 약 2만 년마다 돌아옵니다.\n\n출처: deMenocal·Tierney 2012(Nature Education), Tierney 외 2017(Science Advances), Eos",
  ['사하라', 'Sahara', '초록 사하라', 'Green Sahara', '기후', 'climate', '사막', 'desert']),
 ('kola_hole', 'kola', "20 Years of Drilling Barely Scratched the Earth #Shorts", '인류가 판 가장 깊은 구멍, 콜라 시추공',
  "In 1970 the Soviet Union began drilling the Kola Superdeep Borehole. By 1989 it reached 12,262 m, still the deepest hole ever dug, deeper than Everest is tall. Yet it went only about a third through the crust, and on the whole Earth it is about 0.19% of the way to the center.\n\nSources: Wikipedia; Earthdate; Atlas Obscura. 0.19% calculated from Earth's radius of 6,371 km.",
  "1970년 소련이 콜라 초심부 시추공을 뚫기 시작했습니다. 1989년 12,262m, 지금도 가장 깊은 구멍이고 에베레스트 높이보다 깊습니다. 그래도 지각의 약 3분의 1, 지구 중심까지 거리로는 약 0.19%입니다.\n\n출처: Wikipedia, Earthdate, Atlas Obscura. 0.19%는 지구 반지름 6,371km로 계산",
  ['콜라 시추공', 'Kola Superdeep Borehole', '지각', 'crust', '지구', 'Earth', '시추', 'drilling']),
 ('bamboo_growth', 'bamboo', "Bamboo Can Grow 91 cm in a Single Day #Shorts", '하루에 91cm 자라는 대나무',
  "Some bamboo species grow up to 91 cm in a single day, about 3.8 cm an hour. The tallest recorded reached about 40 m. Before a new shoot appears, its underground rhizomes spend months or years storing energy.\n\nSources: Guinness World Records; Bambu Batu. Hourly rate calculated.",
  "어떤 대나무는 하루에 91cm까지, 시간당 약 3.8cm 자랍니다. 가장 큰 기록은 약 40m. 새 순이 올라오기 전, 땅속 뿌리줄기가 몇 달에서 몇 해 동안 양분을 모읍니다.\n\n출처: 기네스 세계기록, Bambu Batu. 시간당 값은 계산",
  ['대나무', 'bamboo', '식물', 'plant', '성장', 'growth', '기네스', 'Guinness']),
 ('rubik_twenty', 'rubik', "Every Rubik's Cube Can Be Solved in 20 Moves #Shorts", '어떤 루빅 큐브든 20수면 풀린다',
  "A Rubik's Cube has 43,252,003,274,489,856,000 possible states. In 2010 a team proved that every one of them can be solved in 20 moves or fewer, using about 35 years of computer time donated by Google.\n\nSources: cube20.org; MAA; Popular Science.",
  "루빅 큐브가 섞일 수 있는 상태는 43,252,003,274,489,856,000가지입니다. 2010년 연구진이 그 모두가 20수 안에 풀린다는 것을 증명했고, 구글이 내준 컴퓨터 시간 약 35년이 들었습니다.\n\n출처: cube20.org, MAA, Popular Science",
  ['루빅 큐브', "Rubik's Cube", '신의 수', "God's number", '수학', 'math', '퍼즐', 'puzzle']),
]

META += [
 ('fold_moon', 'fold', "Fold Paper 42 Times and It Reaches the Moon #Shorts", '종이를 42번 접으면 달에 닿는다',
  "Each fold doubles the thickness. Fold a 0.1 mm sheet 42 times and it would be about 439,805 km thick, past the Moon's average distance of 384,400 km. In reality, the record is 12 folds, set by Britney Gallivan in 2002 with about 1.2 km of tissue paper.\n\nSources: Guinness World Records (12 folds). Thickness values calculated.",
  "한 번 접을 때마다 두께는 두 배가 됩니다. 0.1mm 종이를 42번 접으면 약 439,805km, 달까지 평균 거리 384,400km를 넘습니다. 실제 기록은 12번, 2002년 브리트니 갤리번이 약 1.2km 길이 휴지로 세웠습니다.\n\n출처: 기네스 세계기록(12번). 두께 값은 계산",
  ['종이접기', 'paper folding', '지수', 'exponential', '달', 'Moon', '수학', 'math']),
 ('earth_day', 'clock', "If Earth Were One Day, Humans Showed Up 6 Seconds Ago #Shorts", '지구의 하루 중 인류는 마지막 6초',
  "Squeeze Earth's 4.54 billion years into 24 hours. Dinosaurs vanish at 23:39, Homo sapiens appears about 5.7 seconds before midnight, and all written history fits in the last 0.1 second.\n\nSources: USGS (Earth's age); Max Planck Society (Homo sapiens ~300,000 years). Clock times calculated.",
  "지구의 45억 4천만 년을 24시간으로 줄이면 공룡은 밤 11시 39분에 사라지고, 호모 사피엔스는 자정 약 5.7초 전에 나타나며, 기록된 역사 전부는 마지막 0.1초에 들어갑니다.\n\n출처: USGS(지구 나이), 막스플랑크 협회(호모 사피엔스 약 30만 년). 시각은 계산",
  ['지구 역사', 'Earth history', '인류', 'humans', '공룡', 'dinosaurs', '시간', 'time']),
 ('neutron_cube', 'neutron', "A Sugar Cube of This Star Weighs a Billion Tons #Shorts", '각설탕 하나가 10억 톤, 중성자별',
  "When a giant star dies, its core collapses into a neutron star about 20 km wide, yet heavier than the Sun. A sugar cube of that material would weigh about a billion tons on Earth, as much as a mountain. Many spin and flash like lighthouses: pulsars.\n\nSources: NASA Imagine the Universe; NASA Science; National Geographic.",
  "거대한 별이 죽으면 중심이 무너져 지름 약 20km의 중성자별이 됩니다. 그런데 질량은 해보다 큽니다. 각설탕 하나 분량이 지구에서 약 10억 톤, 산 하나만큼입니다. 많은 중성자별은 돌며 등대처럼 깜박이는 펄서입니다.\n\n출처: NASA Imagine the Universe, NASA Science, National Geographic",
  ['중성자별', 'neutron star', '펄서', 'pulsar', '우주', 'space', '밀도', 'density']),
 ('hummingbird_heart', 'hummer', "A Hummingbird's Heart Beats 1,260 Times a Minute #Shorts", '1분에 1,260번 뛰는 벌새의 심장',
  "In flight, a hummingbird's heart can beat up to about 1,260 times a minute, while its wings beat up to about 80 times a second. At night it rests in torpor and its heart slows to about 50 beats a minute.\n\nSources: San Diego Zoo Wildlife Alliance; Audubon; Ole Miss hummingbird facts.",
  "날고 있는 벌새의 심장은 분당 최대 약 1,260번, 날개는 초당 최대 약 80번 움직입니다. 밤에는 휴면에 들어 심장이 분당 약 50번으로 느려집니다.\n\n출처: 샌디에이고 동물원, Audubon, 미시시피대 벌새 자료",
  ['벌새', 'hummingbird', '심장', 'heart', '새', 'bird', '동물', 'animals']),
]

META += [
 ('walk_earth', 'walk', "How Long Would It Take to Walk Around the Earth? #Shorts", '걸어서 지구 한 바퀴, 얼마나 걸릴까',
  "The equator is 40,075 km around. Walking nonstop at 5 km/h would take about 334 days. Walking 8 hours a day, about 2.7 years. And just 10,000 steps a day would get you around in about 14.6 years.\n\nSource: NASA Earth Fact Sheet (circumference). Times calculated (10,000 steps assumes a 0.75 m stride).",
  "적도 한 바퀴는 40,075km입니다. 시속 5km로 쉬지 않고 걸으면 약 334일, 하루 8시간씩이면 약 2.7년, 하루 1만 보씩이면 약 14.6년이 걸립니다.\n\n출처: NASA 지구 자료(둘레). 시간은 계산(1만 보는 보폭 0.75m 가정)",
  ['걷기', 'walking', '지구 둘레', 'Earth circumference', '만보', '10000 steps', '건강', 'health']),
]

META += [
 ('saturn_float', 'saturn', "Saturn Would Float in a Giant Bathtub #Shorts", '물에 뜨는 행성, 토성',
  "Saturn has about 95 times Earth's mass, but it is spread over more than 750 times the volume. Its average density is just 0.687 g/cm3, lower than water. In a big enough bathtub it would float, though only as a thought experiment.\n\nSources: BBC Sky at Night; Universe Today; NASA; IFLScience.",
  "토성의 질량은 지구의 약 95배지만 부피는 750배가 넘습니다. 평균 밀도는 0.687g/cm³로 물보다 낮아, 아주 큰 욕조가 있다면 뜹니다. 물론 사고 실험일 뿐입니다.\n\n출처: BBC Sky at Night, Universe Today, NASA, IFLScience",
  ['토성', 'Saturn', '밀도', 'density', '행성', 'planet', '우주', 'space']),
 ('baby_bones', 'bones', "Babies Have Almost 100 More Bones Than Adults #Shorts", '아기는 어른보다 뼈가 100개 가까이 많다',
  "A newborn has about 275 to 300 bones. As we grow, small bones fuse together, and most adults end up with 206. Bones make up about 15% of body weight and store about 99% of the body's calcium.\n\nSources: Cleveland Clinic; Britannica; Healthline.",
  "갓난아기의 뼈는 약 275~300개입니다. 자라면서 작은 뼈들이 붙어 어른은 보통 206개가 됩니다. 뼈는 몸무게의 약 15%, 몸속 칼슘의 약 99%를 품고 있습니다.\n\n출처: 클리블랜드 클리닉, 브리태니커, Healthline",
  ['뼈', 'bones', '아기', 'baby', '인체', 'human body', '골격', 'skeleton']),
]

META += [
 ('cloud_weight', 'cloud', "A Fluffy Cloud Weighs as Much as 100 Elephants #Shorts", '뭉게구름 하나가 코끼리 100마리 무게',
  "A cumulus cloud about 1 km on each side holds roughly 0.5 g of water per cubic metre, which adds up to about 500,000 kg, around the weight of 100 elephants. It stays up because the droplets are tiny and spread far apart.\n\nSources: USGS Water Science School; EarthDate; Smithsonian How Things Fly.",
  "가로·세로·높이 1km 뭉게구름에는 1m³당 약 0.5g의 물이 있어 모두 약 50만 kg, 코끼리 100마리 무게쯤입니다. 그래도 떠 있는 것은 물방울이 아주 작고 멀리 흩어져 있기 때문입니다.\n\n출처: USGS 물 과학 학교, EarthDate, 스미스소니언",
  ['구름', 'cloud', '날씨', 'weather', '물', 'water', '과학', 'science']),
]

META += [
 ('pistol_shrimp', 'shrimp', "This Shrimp Makes a Bubble Nearly as Hot as the Sun #Shorts", '해만큼 뜨거운 거품을 만드는 딱총새우',
  "When a pistol shrimp snaps its claw, a bubble forms in the fast water jet and collapses with a bang and a flash of light. For a split second it reaches at least 5,000 K (about 4,700 C) inside, close to the Sun's surface. In WWII their crackling even interfered with submarine sonar.\n\nSources: Versluis et al. 2000 (Science); Lohse et al. 2001 (Nature); Scientific American; NASA (Sun's surface ~5,500 C).",
  "딱총새우가 집게를 닫으면 빠른 물줄기 속에 거품이 생겼다가 큰 소리와 빛을 내며 무너집니다. 그 순간 거품 속은 최소 5,000K(약 4,700°C)로 해 표면에 가깝습니다. 2차 대전 때는 이 소리가 잠수함 음파 탐지를 방해하기도 했습니다.\n\n출처: Versluis 외 2000(Science), Lohse 외 2001(Nature), Scientific American, NASA",
  ['딱총새우', 'pistol shrimp', '캐비테이션', 'cavitation', '바다', 'ocean', '동물', 'animals']),
]

META += [
 ('new_skin', 'skin', "You Wear a Brand-New Skin Every Month #Shorts", '한 달마다 새 피부를 입는다',
  "Your skin looks the same every day, but it sheds roughly 30,000 to 40,000 dead cells every minute. New cells rise from below and reach the surface in about a month, so over 80 years you wear close to 1,000 new skins.\n\nSources: KidsHealth (Nemours); Skin Cancer Foundation (about a month, slower with age). The 1,000 figure is calculated: 80 years divided by about one month.",
  "피부는 날마다 그대로인 것 같지만 1분마다 죽은 세포 약 3만~4만 개가 떨어져 나갑니다. 새 세포가 아래에서 올라와 약 한 달이면 겉에 닿으니, 80년이면 새 피부를 천 번 가까이 입는 셈입니다.\n\n출처: KidsHealth(Nemours), Skin Cancer Foundation(약 한 달, 나이가 들면 느려짐). 천 번은 80년 ÷ 약 한 달로 계산",
  ['피부', 'skin', '세포', 'cells', '인체', 'human body', '조각보', 'jogakbo']),
]

def sh(*a, cwd=None):
    r = subprocess.run(a, cwd=cwd, capture_output=True, text=True)
    if r.returncode: sys.exit(f'FAIL {a[:3]} {r.stderr[-300:]}')
    return r.stdout

want = set(sys.argv[1:])
d = tempfile.mkdtemp()
sh('git', 'clone', '-q', '--depth', '1', '--branch', 'shorts-outbox', 'https://github.com/mini-ok/ssoksok-channel-assets', d)
idx = json.load(open(f'{d}/index.json')); base = datetime.datetime.now(datetime.timezone.utc).replace(microsecond=0)
for k, (slug, ep, ten, tko, den, dko, tags) in enumerate(META):
    if want and slug not in want: continue
    if any(i['slug'] == slug for i in idx['items']): print('skip', slug); continue
    now = (base + datetime.timedelta(seconds=k)).isoformat()
    od = f'{d}/shorts/{slug}'; os.makedirs(od); shutil.copy(f'{OUT}/{ep}.mp4', f'{od}/video.mp4')
    assert len(ten) <= 100 and not any('가' <= c <= '힣' for c in ten + den)
    json.dump(dict(slug=slug, title_en=ten, title_ko=tko, desc_en=den + SIGN_EN, desc_ko=dko + SIGN_KO, tags=tags + COMMON,
                   related=None, file='video.mp4', created=now), open(f'{od}/meta.json', 'w'), ensure_ascii=False, indent=1)
    idx['items'].append(dict(slug=slug, dir=f'shorts/{slug}', created=now)); print('add', slug)
idx['per_run'] = 2
json.dump(idx, open(f'{d}/index.json', 'w'), indent=1, ensure_ascii=False)
rd = open(f'{d}/README.md').read()
if '## 한 번에 올리는 개수' not in rd:
    rd = rd.replace('## 유튜브에 올릴 때', '## 한 번에 올리는 개수\n- 예약 실행 한 번에 **최대 2편**만 올린다(`index.json`의 `per_run` 값). 업로더 기록에 없는 slug 중 `created`가 오래된 것부터 2편.\n- 남은 것은 다음 예약 실행에서 이어서 올린다. 한 번에 몰아서 올리지 않는다.\n\n## 유튜브에 올릴 때', 1)
    open(f'{d}/README.md', 'w').write(rd)
sh('git', 'add', '-A', cwd=d)
sh('git', '-c', 'user.name=claude', '-c', 'user.email=noreply@anthropic.com', 'commit', '-qm', 'outbox: nova shorts (' + ' '.join(sys.argv[1:])[:60] + ')', cwd=d)
sh('git', 'push', '-q', 'origin', 'shorts-outbox', cwd=d)
print('PUSHED', len(idx['items']), 'items')
