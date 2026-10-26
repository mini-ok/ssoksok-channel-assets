"""야식 습격 사건 — 대본·장면 데이터 (롱폼 + 쇼츠 A·B, 한/영)
장면 필드: id loc sid dur(무음 조각) actors props chips fx time iv
actors: name -> (x, mood, scale, opts)   opts: y, run, hop
"""
FLOOR_Y = 850
SLOTS = [380, 700, 1020, 1340, 1660]

def C(ko, en, x, y, size=100, face="black", col="coral", rot=0, t0=0.0, sticky=None):
    return dict(ko=ko, en=en, x=x, y=y, size=size, face=face, col=col, rot=rot, t0=t0, sticky=sticky)

# ───────────────────── 롱폼 장면 ─────────────────────
L = []
def add(**k): L.append(k)

# 1막: 발단 (느긋)
add(id="a1", loc="office_night", sid=0, tempo=1, time=(23, 42),
    actors=dict(melatonin=(560, "sleepy"), brain=(960, "happy"), liver=(1360, "happy_closed")),
    chips=[C("밤 11:42", "11:42 PM", 1300, 250, 110, "black", "butter", -2, 0.1, "time")],
    props=[("remote", dict(x=640, y=700, sc=0.7))])
add(id="a2", loc="office_night", sid=0, tempo=1, time=(23, 42),
    actors=dict(melatonin=(560, "sleepy"), brain=(960, "happy"), liver=(1360, "happy_closed")),
    chips=[C("밤 11:42", "11:42 PM", 1300, 250, 110, "black", "butter", -2, 0.1, "time")],
    props=[("remote", dict(x=640, y=700, sc=0.7))])
add(id="a3", loc="office_night", sid=7, tempo=1, time=(23, 43),
    actors=dict(melatonin=(620, "happy", 1.12), brain=(1000, "happy"), liver=(1380, "happy_closed")),
    chips=[C("밤 11:42", "11:42 PM", 1300, 250, 110, "black", "butter", -2, 0.1, "time")],
    props=[("remote", dict(x=700, y=700, sc=0.7))])
add(id="a4", loc="office_night", sid=5, tempo=1, time=(23, 43),
    actors=dict(melatonin=(560, "happy"), brain=(1000, "awake", 1.12), liver=(1380, "happy_closed")),
    chips=[C("밤 11:42", "11:42 PM", 1300, 250, 110, "black", "butter", -2, 0.1, "time")],
    props=[("remote", dict(x=640, y=700, sc=0.7))])
add(id="a5", loc="office_night", sid=3, tempo=1, time=(23, 44),
    actors=dict(melatonin=(560, "happy"), brain=(960, "happy"), liver=(1360, "happy_closed", 1.12)),
    chips=[C("밤 11:42", "11:42 PM", 1300, 250, 110, "black", "butter", -2, 0.1, "time")],
    props=[("remote", dict(x=640, y=700, sc=0.7))])
add(id="a6", loc="office_night", sid=0, tempo=2, time=(23, 44), fx=["alarm"],
    actors=dict(melatonin=(560, "wow", 1.0, dict(hop=1)), brain=(960, "wow", 1.0, dict(hop=1)), liver=(1360, "worry", 1.0, dict(hop=1))),
    chips=[C("사내 방송", "COMPANY PA", 1300, 250, 100, "black", "coral", 2, 0.0)],
    props=[("remote", dict(x=640, y=700, sc=0.7, drop=0.6)), ("burst", dict(x=360, y=470, txt="!", t=0.3)), ("burst", dict(x=1580, y=470, txt="!", t=0.45))])
add(id="a7", loc="office_night", sid=None, dur=1.5, tempo=2, time=(23, 44), fx=["alarm"],
    actors=dict(melatonin=(560, "wow"), brain=(960, "wow"), liver=(1360, "worry")),
    chips=[C("사내 방송", "COMPANY PA", 1300, 250, 100, "black", "coral", 2, 0.0, "pa")],
    props=[("remote", dict(x=640, y=700, sc=0.7, drop=-1, fell=1))])
add(id="a8", loc="office_night", sid=0, tempo=2, time=(23, 45),
    actors=dict(melatonin=(560, "worry"), brain=(960, "worry"), liver=(1360, "worry")),
    chips=[C("배달 앱 열림", "DELIVERY APP OPENED", 1300, 250, 80, "jua", "sky", -3, 0.1)],
    props=[("remote", dict(x=640, y=830, sc=0.7, fell=1))])

# 2막: 전개 (회의실)
add(id="b1", loc="meeting", sid=5, tempo=2,
    actors=dict(brain=(1330, "serious", 1.1)), props=[("board", dict())],
    chips=[C("치킨 대응 TF", "PIZZA RESPONSE TF", 840, 285, 110, "black", "mint", -2, 0.2, "tf")])
add(id="b2", loc="meeting", sid=10, tempo=2,
    actors=dict(brain=(1330, "serious"), stomach=(620, "wow", 1.12, dict(hop=1))), props=[("board", dict())],
    chips=[C("치킨 대응 TF", "PIZZA RESPONSE TF", 840, 285, 110, "black", "mint", -2, 0.2, "tf")])
add(id="b3", loc="meeting", sid=5, tempo=2,
    actors=dict(brain=(1330, "smug", 1.12), stomach=(620, "worry")), props=[("board", dict())],
    chips=[C("치킨 대응 TF", "PIZZA RESPONSE TF", 840, 285, 110, "black", "mint", -2, 0.2, "tf")])
add(id="b4", loc="meeting", sid=10, tempo=2,
    actors=dict(brain=(1330, "smug"), stomach=(660, "wow", 1.15, dict(hop=1))), props=[("board", dict())],
    chips=[C("치킨 대응 TF", "PIZZA RESPONSE TF", 840, 285, 110, "black", "mint", -2, 0.2, "tf")],
    fx=["sweat"])
add(id="b5", loc="iv", sid=10, tempo=2, iv=("위 대리", "소화1팀", "Stomach", "Digestion Team 1"),
    actors=dict(stomach=(960, "tired", 1.55)), props=[])
add(id="b6", loc="gate", sid=6, tempo=2,
    actors=dict(immune=(700, "serious", 1.2)),
    props=[("food1", dict(x=1300, y=760, sc=1.0, t=0.2))])
add(id="b7", loc="gate", sid=0, tempo=2,
    actors=dict(immune=(700, "serious", 1.2)),
    props=[("food1", dict(x=1300, y=760, sc=1.0, t=-1))])
add(id="b8", loc="gate", sid=6, tempo=2,
    actors=dict(immune=(700, "serious", 1.25, dict(hop=1))),
    props=[("food1", dict(x=1300, y=760, sc=1.0, t=-1, shrink=0.5))],
    chips=[C("통과 불가", "NOT ALLOWED", 1450, 300, 90, "black", "coral", 4, 0.3)])

# 3막: 위기 → 절정 (긴박)
add(id="c1", loc="office_night", sid=10, tempo=3, time=(23, 58),
    actors=dict(stomach=(560, "worry", 1.12, dict(hop=1)), brain=(1060, "serious")),
    props=[("clip", dict(x=760, y=700, sc=0.85))],
    chips=[C("밤 11:58", "11:58 PM", 1300, 250, 110, "black", "butter", -2, 0.0)])
add(id="c2", loc="office_night", sid=5, tempo=3, time=(23, 58),
    actors=dict(stomach=(600, "worry"), brain=(1060, "wow", 1.12)),
    props=[("clip", dict(x=800, y=700, sc=0.85)), ("stamp", dict(x=1060, y=520, t_up=0.2))],
    chips=[C("밤 11:58", "11:58 PM", 1300, 250, 110, "black", "butter", -2, 0.0)])
add(id="c3", loc="office_night", sid=0, tempo=3, time=(23, 59), fx=["alarm"],
    actors=dict(stomach=(600, "wow", 1.0, dict(hop=1)), brain=(1060, "wow", 1.0, dict(hop=1))),
    props=[("clip", dict(x=800, y=700, sc=0.85)), ("stamp", dict(x=1060, y=520, t_up=-1, slam=0.9)), ("stampmk", dict(x=840, y=640, kind="no", t=1.0)),
           ("food2", dict(x=1560, y=600, t=1.3))],
    chips=[C("2차 입고", "2ND DELIVERY", 1300, 250, 100, "black", "coral", 2, 0.0)])
add(id="c4", loc="office_night", sid=10, tempo=3, time=(23, 59), fx=["alarm"],
    actors=dict(stomach=(600, "wow", 1.18, dict(hop=1)), brain=(1060, "worry")),
    props=[("clip", dict(x=800, y=700, sc=0.85)), ("stampmk", dict(x=840, y=640, kind="no", t=-1)), ("food2", dict(x=1560, y=600, t=-1)), ("burst", dict(x=520, y=420, txt="!", t=0.2))],
    chips=[C("2차 입고", "2ND DELIVERY", 1300, 250, 100, "black", "coral", 2, 0.0, "pa2")])
add(id="c5", loc="office_night", sid=3, tempo=3, time=(23, 59),
    actors=dict(stomach=(560, "worry"), brain=(960, "worry"), liver=(1400, "tired", 1.15)),
    props=[("sweat", dict(x=640, y=520))],
    chips=[C("기름은 간 몫", "GREASE = LIVER'S JOB", 1300, 250, 80, "jua", "lav", -3, 0.2)])
add(id="c6", loc="iv", sid=3, tempo=3, iv=("간 과장", "해독팀", "Liver", "Detox Team"),
    actors=dict(liver=(960, "happy_closed", 1.55)), props=[])
add(id="c7", loc="factory", sid=0, tempo=3, time=(0, 0),
    actors=dict(stomach=(520, "worry", 1.1)),
    props=[("belt", dict(speed=1.0)), ("clockbig", dict(t=0.2))],
    chips=[C("자정 00:00", "MIDNIGHT", 960, 285, 100, "black", "butter", -2, 0.1, "mid")])
add(id="c8", loc="factory", sid=10, tempo=4,
    actors=dict(stomach=(620, "wow", 1.2, dict(hop=1))),
    props=[("belt", dict(speed=1.6)), ("crates", dict())],
    chips=[C("누우면 위험?", "LYING DOWN?", 960, 285, 100, "black", "coral", 2, 0.1)], fx=["shake1"])
add(id="c9", loc="factory", sid=0, tempo=4, fx=["alarm", "shake2"],
    actors=dict(stomach=(620, "wow", 1.2, dict(hop=1))),
    props=[("belt", dict(speed=2.0)), ("crates", dict()), ("acid", dict())],
    chips=[C("역류 경보", "REFLUX ALERT", 960, 285, 110, "black", "coral", -2, 0.0, "reflux")])
add(id="c10", loc="factory", sid=5, tempo=4, fx=["alarm", "shake2"],
    actors=dict(stomach=(520, "wow", 1.1, dict(run=1)), brain=(1060, "wow", 1.1, dict(run=1))),
    props=[("belt", dict(speed=2.0)), ("acid", dict())],
    chips=[C("역류 경보", "REFLUX ALERT", 960, 285, 110, "black", "coral", -2, 0.0, "reflux")])
add(id="c11", loc="factory", sid=7, tempo=4, fx=["alarm", "shake2"],
    actors=dict(stomach=(460, "wow", 1.0, dict(run=1)), brain=(900, "wow", 1.0, dict(run=1)), melatonin=(1360, "worry", 1.1, dict(run=1))),
    props=[("belt", dict(speed=2.0)), ("acid", dict())],
    chips=[C("역류 경보", "REFLUX ALERT", 960, 285, 110, "black", "coral", -2, 0.0, "reflux")])
add(id="c12", loc="factory", sid=6, tempo=4, fx=["alarm", "shake2"],
    actors=dict(stomach=(420, "wow", 0.95, dict(run=1)), brain=(760, "wow", 0.95, dict(run=1)), melatonin=(1100, "worry", 0.95, dict(run=1)), immune=(1500, "serious", 1.1, dict(run=1))),
    props=[("belt", dict(speed=2.0)), ("acid", dict())],
    chips=[C("역류 경보", "REFLUX ALERT", 960, 285, 110, "black", "coral", -2, 0.0, "reflux")])
add(id="c13", loc="factory", sid=0, tempo=4, fx=["alarm", "shake2"],
    actors=dict(stomach=(380, "wow", 0.9, dict(run=1)), brain=(700, "wow", 0.9, dict(run=1)), melatonin=(1000, "worry", 0.9, dict(run=1)), immune=(1300, "serious", 0.9, dict(run=1)), liver=(1640, "tired", 0.9, dict(run=1))),
    props=[("belt", dict(speed=2.0)), ("acid", dict())],
    chips=[C("전 직원 대혼란", "TOTAL CHAOS", 960, 285, 100, "black", "coral", 2, 0.0)])

# 4막: 결말
add(id="d0", loc="night", sid=None, dur=1.4, tempo=1, time=(3, 7),
    actors=dict(stomach=(640, "tired"), brain=(960, "sleepy"), liver=(1280, "tired")),
    chips=[], props=[("lights_out", dict())])
add(id="d1", loc="night", sid=0, tempo=1, time=(3, 7),
    actors=dict(stomach=(640, "tired"), brain=(960, "sleepy"), liver=(1280, "tired")),
    chips=[C("새벽 3:07", "3:07 AM", 1300, 250, 110, "black", "lav", -2, 0.1, "dawn")])
add(id="d2", loc="night", sid=10, tempo=1, time=(3, 7),
    actors=dict(stomach=(640, "tired", 1.12), brain=(960, "sleepy"), liver=(1280, "tired")),
    chips=[C("새벽 3:07", "3:07 AM", 1300, 250, 110, "black", "lav", -2, 0.1, "dawn")])
add(id="d3", loc="night", sid=3, tempo=1, time=(3, 8),
    actors=dict(stomach=(640, "tired"), brain=(960, "sleepy"), liver=(1280, "happy_closed", 1.12)),
    props=[("cups", dict(t=0.5))],
    chips=[C("새벽 3:07", "3:07 AM", 1300, 250, 110, "black", "lav", -2, 0.1, "dawn")])
add(id="d4", loc="night", sid=10, tempo=1, time=(3, 8),
    actors=dict(stomach=(660, "happy_closed", 1.15), brain=(960, "happy"), liver=(1260, "happy_closed")),
    props=[("cups", dict(t=-1)), ("hearts", dict(x=660, y=520))],
    chips=[C("새벽 3:07", "3:07 AM", 1300, 250, 110, "black", "lav", -2, 0.1, "dawn")])
add(id="d5", loc="iv", sid=5, tempo=1, iv=("뇌 팀장", "기획팀", "Brain", "Planning Team"),
    actors=dict(brain=(960, "serious", 1.55)), props=[("recap", dict())])
add(id="d6", loc="iv", sid=5, tempo=1, iv=("뇌 팀장", "기획팀", "Brain", "Planning Team"),
    actors=dict(brain=(960, "happy_closed", 1.6, dict(hop=1))), props=[("sparkles", dict(x=960, y=470))])
add(id="d6g", loc="night", sid=2, tempo=1, time=(3, 9),
    actors=dict(gut=(560, "happy", 1.1, dict(hop=1)), stomach=(1060, "happy_closed"), liver=(1400, "happy_closed")),
    chips=[C("야식 사건 소문", "BREAKING OFFICE NEWS", 1300, 250, 80, "jua", "sky", -2, 0.2)])
add(id="d7", loc="office_day", sid=0, tempo=1, time=(8, 30),
    actors=dict(brain=(520, "happy", 1.0), stomach=(880, "happy_closed", 1.0)),
    props=[("notice", dict(x=1420, y=440))], chips=[])
add(id="d8", loc="office_day", sid=0, tempo=2, time=(23, 40),
    actors=dict(brain=(520, "happy"), stomach=(880, "happy_closed")),
    props=[],
    chips=[C("다음 날 밤", "THE NEXT NIGHT", 1300, 250, 100, "black", "butter", -2, 0.0)])
add(id="d9", loc="office_night", sid=0, tempo=4, time=(23, 59), fx=["alarm"],
    actors=dict(melatonin=(480, "wow"), brain=(780, "wow"), stomach=(1100, "happy"), liver=(1380, "happy_closed"), immune=(1680, "serious")),
    props=[("food3", dict(x=1560, y=700, t=0.6))],
    chips=[C("사내 방송", "COMPANY PA", 1300, 250, 100, "black", "coral", 2, 0.0)])
add(id="d10", loc="office_night", sid=10, tempo=4, time=(23, 59), fx=["alarm", "shake2"],
    actors=dict(melatonin=(480, "wow", 1.0, dict(hop=1)), brain=(780, "wow", 1.0, dict(hop=1)), stomach=(1100, "wow", 1.2, dict(hop=1)), liver=(1380, "worry", 1.0, dict(hop=1)), immune=(1680, "wow", 1.0, dict(hop=1))),
    props=[("food3", dict(x=1560, y=700, t=-1)), ("burst", dict(x=960, y=420, txt="!!", t=0.1))],
    chips=[C("사내 방송", "COMPANY PA", 1300, 250, 100, "black", "coral", 2, 0.0, "pa3")])
add(id="d11", loc="end_thanks", sid=0, tempo=1,
    actors=dict(brain=(300, "happy", 1.05, dict(wave=1)), stomach=(640, "happy", 1.05, dict(wave=1)), liver=(1280, "happy_closed", 1.05, dict(wave=1)), melatonin=(1620, "happy", 1.05, dict(wave=1))),
    props=[("thumbup", dict(x=960, y=300, t=0.4))],
    chips=[])
add(id="d12", loc="end_thanks", sid=3, tempo=1,
    actors=dict(brain=(300, "happy", 1.0, dict(wave=1)), stomach=(640, "happy", 1.0, dict(wave=1)), liver=(1280, "happy_closed", 1.12, dict(wave=1)), melatonin=(1620, "happy", 1.0, dict(wave=1))),
    props=[("thumbup", dict(x=820, y=300, t=-1)), ("bellp", dict(x=1110, y=300, t=0.4))],
    chips=[])
add(id="e1", loc="endcard", sid=0, tempo=1, mindur=7.0,
    actors=dict(stomach=(185, "happy", 0.62, dict(wave=1)), brain=(385, "happy", 0.62, dict(wave=1)), liver=(1545, "happy_closed", 0.62, dict(wave=1)), melatonin=(1745, "happy", 0.62, dict(wave=1))),
    props=[("endcard", dict())], chips=[])

# ───────────────────── 롱폼 대본 (한국어) ─────────────────────
KO = {
 "a1": ("주인님, 야식 한 번에 직원들이 밤새 야근하는 거, 아세요? 사건은 밤 열한 시 사십이 분에, 시작됐어요.", "야식 한 번에\n직원들이 [[밤새 야근]]한다는 거, 아세요?", "호기심을 건드리듯 살짝 속닥이며 시작해서 점점 밝고 신나게"),
 "a2": ("그날 몸속 주식회사는, 드디어 퇴근 준비 중이었어요.", "그날 [[몸속 주식회사]]는\n드디어 퇴근 준비 중!", "느긋하고 포근하게, 다정한 다큐 내레이션처럼"),
 "a3": ("하암… 이제 셔터, 내려도 되죠? 저 오늘 처음으로, 제시간에 퇴근해요…!", "멜라토닌: \"이제 [[셔터]] 내려도 되죠?\n저 오늘 처음으로 제시간 퇴근…!\"", "하품 섞어 졸리지만 설레는 목소리로, 천천히"),
 "a4": ("자, 정리해 보면! 오늘 업무, 전부 끝! 다들 수고했어요!", "뇌 팀장: \"자, 정리해 보면!\n오늘 업무 [[전부 끝]]!\"", "뿌듯하고 흐뭇하게, 박수 치듯 신나게"),
 "a5": ("…오랜만에, 집에 가네요.", "간 과장: \"…[[오랜만에]] 집에 가네요.\"", "작게 웃으며, 피곤하지만 행복하게 낮고 조용하게"),
 "a6": ("긴급! 긴급! 정문으로, 후라이드 치킨 한 마리, 입고 중!", "[[긴급!]] 정문으로\n후라이드 치킨 한 마리 입고 중!", "사내 방송 앵커처럼 크고 다급하게 또박또박, 경보음 같은 느낌"),
 "a8": ("어머, 주인님이 배달 앱을 여셨네요.", "어머, 주인님이\n[[배달 앱]]을 여셨네요", "구경꾼처럼 놀라서 속삭이듯, 어머 하는 느낌"),
 "b1": ("긴급 회의! 소화1팀, 위 대리! 이 치킨, 지금 바로 처리하세요!", "뇌 팀장: \"긴급 회의! 위 대리!\n이 치킨, [[지금 바로]] 처리하세요!\"", "다급하고 빠르게, 팀장답게 단호하게"),
 "b2": ("지금요?! 저 저녁 삼겹살도, 아직 정리 중인데요?!", "위 대리: \"[[지금요?!]]\n저 저녁 삼겹살도 아직 정리 중인데요?!\"", "억울하고 호들갑스럽게 빠르고 높게"),
 "b3": ("자, 정리해 보면… 일단, 해 주세요!", "뇌 팀장: \"자, 정리해 보면…\n[[일단]], 해 주세요!\"", "당당한 척하다가 얼버무리듯"),
 "b4": ("그게 정리예요?!", "위 대리: \"그게 [[정리]]예요?!\"", "황당해서 빠르게 따지듯"),
 "b5": ("팀장님은 항상 일단이래요. 일단은… 제 퇴근 시간이에요.", "위 대리: \"팀장님은 항상 '일단'이래요.\n일단은… [[제 퇴근 시간]]이에요.\"", "카메라를 보며 지치고 푸념하듯, 마지막은 힘 빠져서"),
 "b6": ("신분증 보여주세요.", "면역 경비: \"[[신분증]] 보여주세요.\"", "또박또박 단호하고 진지하게"),
 "b7": ("치킨한테요…?", "치킨한테요…?", "어이없다는 듯 작게 중얼거리며"),
 "b8": ("규칙은 규칙입니다. …양념이면, 통과 안 돼요.", "면역 경비: \"규칙은 규칙입니다.\n…[[양념]]이면 통과 안 돼요.\"", "비장하게 시작해서 마지막에 살짝 진지한 농담처럼"),
 "c1": ("팀장님, 요청서예요! 정 배고프시면, 기름지지 않은 가벼운 걸, 조금만 보내 달라고 해 주세요!", "위 대리: \"요청서예요! 정 배고프면\n[[기름지지 않은 가벼운 걸, 조금만]]!\"", "간절하고 빠르게 매달리듯, 다급하게"),
 "c2": ("좋아요, 승인… 할 뻔했는데—", "뇌 팀장: \"좋아요, 승인… 할 뻔했는데—\"", "도장을 들며 흐뭇하다가 끊기듯 빠르게"),
 "c3": ("2차 입고! 떡볶이 일 인분, 콜라 일 점 오 리터!", "[[2차 입고!]] 떡볶이 1인분,\n콜라 1.5리터!", "사내 방송처럼 다급하고 크게 빠르게"),
 "c4": ("으아아악! 제 요청서가아!", "위 대리: \"으아아악!\n[[제 요청서]]가아!\"", "절규하듯 빠르고 높게 과장되게"),
 "c5": ("휴우… 기름은 제가 맡을게요. …제가 할게요.", "간 과장: \"…기름은 제가 맡을게요.\n[[제가 할게요.]]\"", "깊은 한숨을 쉬고, 소매를 걷듯 낮고 담담하게"),
 "c6": ("이번 주만, 세 번째예요. 괜찮아요. 저는, 원래 조용히 일하니까요.", "간 과장: \"이번 주만 세 번째예요.\n괜찮아요. 저는 [[조용히]] 일하니까요.\"", "카메라를 보며 담담하고 쓸쓸하게, 천천히"),
 "c7": ("그리고 자정. 주인님이… 누우셨어요.", "그리고 자정.\n주인님이… [[누우셨어요]]", "긴장감 있게 낮게 속삭이다가 마지막에 놀라듯"),
 "c8": ("안 돼요! 지금 누우시면, 위산이 거꾸로 올라온다고요!", "위 대리: \"안 돼요! 지금 누우시면\n[[위산]]이 거꾸로 올라온다고요!\"", "비명처럼 다급하고 빠르게"),
 "c9": ("역류 경보! 역류 경보! 식도 쪽으로, 위산 상승 중!", "[[역류 경보!]] 역류 경보!\n식도 쪽으로 위산 상승 중!", "사내 방송 앵커처럼 크고 다급하게 빠르게"),
 "c10": ("자, 정리, 정리해 보면… 정리가 안 돼요!", "뇌 팀장: \"자, 정리, 정리해 보면…\n[[정리가 안 돼요!]]\"", "패닉에 빠져 말이 꼬이며 빠르게"),
 "c11": ("셔터가… 셔터가 안 내려가요! 잠이 안 와요!", "멜라토닌: \"[[셔터]]가 안 내려가요!\n잠이 안 와요!\"", "울먹이며 빠르게 다급하게"),
 "c12": ("신분증! …아니, 일단 대피부터요!", "면역 경비: \"신분증! …아니,\n[[대피]]부터요!\"", "평소 말버릇이 튀어나왔다가 당황해서 빠르게"),
 "c13": ("전 직원이 뛰어다녀요! 이건 정말, 큰일이에요!", "전 직원이 [[뛰어다녀요]]!\n이건 정말 큰일이에요!", "구경꾼처럼 빠르고 숨 가쁘게 중계하듯"),
 "d1": ("새벽 세 시. 겨우… 불이 꺼졌어요.", "새벽 3시.\n겨우… [[불이 꺼졌어요]]", "한숨 돌리듯 조용하고 느리게, 정적 뒤의 안도"),
 "d2": ("다들… 살아 있어요?", "위 대리: \"다들… [[살아 있어요]]?\"", "기진맥진해서 힘없이 작게"),
 "d3": ("물이라도 드세요. 오늘, 다들 잘했어요.", "간 과장: \"[[물이라도]] 드세요.\n오늘, 다들 잘했어요.\"", "조용히 컵을 내밀며 다정하게 천천히"),
 "d4": ("…과장님, 고마워요.", "위 대리: \"…[[과장님]], 고마워요.\"", "울컥해서 목이 메인 채 작게"),
 "d5": ("자, 진짜로 정리해 보면요. 하나, 잠자리에 들기 세 시간 전엔, 식사 끝내기. 둘, 먹고 바로, 눕지 않기. 셋, 정 배고프면, 가볍게 조금만.", "[[1. 자기 3시간 전엔 식사 끝]]\n[[2. 먹고 바로 눕지 않기]]\n[[3. 배고프면 가볍게, 조금만]]", "진지하게 또박또박, 하나씩 짚듯 천천히"),
 "d6": ("…처음으로, 정리가 됐네요.", "뇌 팀장: \"…처음으로, [[정리가 됐네요]].\"", "믿기지 않는 듯 뿌듯하게 작게 웃으며"),
 "d6g": ("그거 들었어요? 위 대리 이야기, 사내 신문 일 면에 실렸대요!", "장 연구원: \"그거 들었어요?\n위 대리 이야기, [[사내 신문 1면]]!\"", "소문 전하듯 신나고 호들갑스럽게"),
 "d7": ("다음 날 아침, 사내 공지예요. 야식은 일찍, 가볍게! 미국 국립보건원, 엔아이에이치 안내예요. 역류 증상이 있는 분께 하는 안내라, 계속되면 병원 상담도 하세요!", "사내 공지: 야식은 [[일찍, 가볍게]]!\n(NIH 안내, 증상이 계속되면 병원 상담)", "아침 방송처럼 밝고 또렷하게, 마지막은 다정하게 당부"),
 "d8": ("그리고, 다음 날 밤.", "그리고, [[다음 날 밤]].", "일부러 뜸 들이며 장난스럽게 낮게"),
 "d9": ("긴급! 라면, 입고 중!", "[[긴급!]] 라면, 입고 중!", "사내 방송 앵커처럼 크고 다급하게"),
 "d10": ("안 돼애애애!", "[[안 돼애애애!]]", "전 직원이 합창하듯 목청껏 절규하며"),
 "d11": ("오늘 야근 수당은, 좋아요 한 번이면 충분해요!", "오늘 야근 수당은\n[[좋아요 한 번]]이면 충분해요!", "밝고 장난스럽게, 윙크하듯"),
 "d12": ("알림 설정도 딸깍… 해 주시면, 다음 야근엔 미리 준비할게요.", "간 과장: \"[[알림 설정]]도 딸깍…\n해 주시면 다음 야근엔 미리 준비할게요.\"", "쑥스러워하며 조용히 다정하게"),
 "e1": ("다음엔, 물 여덟 잔 규칙의 진실, 이 영상도 이어서 보세요!", "", "밝고 또렷하게 다정하게 안내"),
}

# ───────────────────── 롱폼 대본 (영어) ─────────────────────
EN = {
 "a1": ("Did you know one late-night snack keeps your organs working all night long? It all started at eleven forty-two p.m.", "One late-night snack =\nyour organs on an [[ALL-NIGHT SHIFT]]?", "Start with a curious half-whisper, getting brighter and more excited"),
 "a2": ("That night, Tiny Body Co. was finally getting ready to go home.", "That night, [[Tiny Body Co.]]\nwas finally packing up to go home", "Slow, cozy, gentle documentary narrator"),
 "a3": ("Yaaawn… can I pull the shutter down now? It's my first on-time clock-out, ever…!", "Melatonin: \"Can I pull the [[shutter]] down?\nMy first on-time clock-out ever…!\"", "Sleepy with yawns but secretly thrilled, slow"),
 "a4": ("Okay, let's recap! All tasks, done! Great work, everyone!", "Brain: \"Okay, let's recap!\nAll tasks [[DONE]]!\"", "Proud and delighted, cheerful like applauding"),
 "a5": ("…Going home on time. It's been a while.", "Liver: \"…Going home [[on time]].\nIt's been a while.\"", "Small tired smile, low and quiet, quietly happy"),
 "a6": ("Attention! Attention! One pepperoni pizza, arriving at the front gate!", "[[ATTENTION!]] One pepperoni pizza\narriving at the front gate!", "Loud urgent office PA announcer, crisp, like a siren"),
 "a8": ("Oh no… the boss just opened a delivery app.", "Oh no… the boss just opened\na [[delivery app]]", "A bystander whispering in shock, 'oh no'"),
 "b1": ("Emergency meeting! Digestion Team One, Stomach! Handle this pizza, right now!", "Brain: \"Emergency meeting! Stomach!\nHandle this pizza [[RIGHT NOW]]!\"", "Urgent and fast, a firm team lead"),
 "b2": ("Right NOW?! I'm still digesting dinner!", "Stomach: \"[[Right NOW?!]]\nI'm still digesting dinner!\"", "Wounded and dramatic, fast and high-pitched"),
 "b3": ("Okay, let's recap… just, uh, do it!", "Brain: \"Okay, let's recap…\nJust, uh, [[do it]]!\"", "Pretending to be confident, then mumbling"),
 "b4": ("That's your recap?!", "Stomach: \"That's your [[recap]]?!\"", "Stunned and quick, accusing"),
 "b5": ("He always says, let's just handle it for now. For now… is my clock-out time.", "Stomach: \"He always says 'for now.'\nFor now… is [[my clock-out time]].\"", "To the camera, weary and venting, trailing off at the end"),
 "b6": ("ID, please.", "Immune: \"[[ID]], please.\"", "Crisp, firm and deadly serious"),
 "b7": ("To a pizza…?", "To a [[pizza]]…?", "Deadpan, muttering in disbelief"),
 "b8": ("Rules are rules. …Extra cheese? Doesn't get through.", "Immune: \"Rules are rules.\n…[[Extra cheese]]? Doesn't get through.\"", "Grand and solemn, then a dry joke at the end"),
 "c1": ("Boss, here's my request! If they're really hungry, ask for something light, not greasy, just a little!", "Stomach: \"Here's my request!\nIf hungry: [[light, not greasy, just a little]]!\"", "Pleading, fast and desperate"),
 "c2": ("Okay, approved… I almost approved it, but—", "Brain: \"Okay, approved…\nI [[almost]] approved it, but—\"", "Happily raising the stamp, then cut off, fast"),
 "c3": ("Second delivery! Buffalo wings and a big soda!", "[[2nd delivery!]] Buffalo wings\nand a big soda!", "Loud urgent office PA announcer, fast"),
 "c4": ("Noooo! My request!", "Stomach: \"Noooo!\n[[My request!]]\"", "Screaming, fast, high and exaggerated"),
 "c5": ("Sigh… I'll take the grease. …I'll handle it.", "Liver: \"…I'll take the grease.\n[[I'll handle it.]]\"", "A deep sigh, rolling up sleeves, low and steady"),
 "c6": ("That's the third time this week. It's fine. I work quietly… that's just who I am.", "Liver: \"Third time this week. It's fine.\nI work [[quietly]]. That's who I am.\"", "To the camera, calm and a little lonely, slow"),
 "c7": ("And then, midnight. The boss… lay down.", "And then, midnight.\nThe boss… [[lay down]]", "Tense low whisper, with a gasp on the last word"),
 "c8": ("No! If they lie down now, the acid flows backward!", "Stomach: \"No! If they lie down now,\nthe [[acid]] flows backward!\"", "Screaming urgently and fast"),
 "c9": ("Reflux alert! Reflux alert! Stomach acid rising toward the esophagus!", "[[REFLUX ALERT!]] Reflux alert!\nAcid rising toward the esophagus!", "Loud urgent office PA announcer, fast"),
 "c10": ("Okay, recap, recap… I can't recap!", "Brain: \"Okay, recap, recap…\n[[I can't recap!]]\"", "Panicking and stumbling over words, fast"),
 "c11": ("The shutter… the shutter won't come down! I can't make them sleep!", "Melatonin: \"The [[shutter]] won't come down!\nI can't make them sleep!\"", "Tearful, fast and frantic"),
 "c12": ("ID! …No wait, evacuate first!", "Immune: \"ID! …No wait,\n[[evacuate]] first!\"", "Catchphrase slips out, then flustered, fast"),
 "c13": ("Everyone's running around! This is a real mess!", "Everyone's [[running around]]!\nThis is a real mess!", "Breathless sports-commentator excitement, fast"),
 "d1": ("Three a.m. Finally… the lights went out.", "Three a.m.\nFinally… [[the lights went out]]", "Letting out a breath, quiet and slow, relief after silence"),
 "d2": ("Everyone… still alive?", "Stomach: \"Everyone… [[still alive]]?\"", "Exhausted, weak and small"),
 "d3": ("Here, have some water. You all did great today.", "Liver: \"Here, have some [[water]].\nYou all did great today.\"", "Quietly handing over a cup, gentle and slow"),
 "d4": ("…Thank you, Liver.", "Stomach: \"…[[Thank you]], Liver.\"", "Choked up, voice trembling, small"),
 "d5": ("Okay, a REAL recap this time. One: finish eating three hours before bed. Two: don't lie down right after a meal. Three: if you're really hungry, go light and small.", "[[1. Finish eating 3 hours before bed]]\n[[2. Don't lie down right after eating]]\n[[3. Hungry? Go light and small]]", "Serious and crisp, counting off each point slowly"),
 "d6": ("…My first successful recap.", "Brain: \"…My first [[successful recap]].\"", "Amazed and proud, small smile"),
 "d6g": ("Did you hear? Stomach's story made the front page of the office paper!", "Gut: \"Did you hear? Stomach's story\nmade the [[front page]]!\"", "Gossiping excitedly, dramatic"),
 "d7": ("Next morning, a company notice: eat late snacks early and light! That's guidance from the U.S. NIH. It's for people with reflux symptoms, so if they keep up, talk to a doctor!", "Notice: Late snack? [[Early and light]]!\n(NIH guidance. Symptoms persist? See a doctor.)", "Bright morning announcer, clear, with a gentle reminder at the end"),
 "d8": ("And then, the next night.", "And then, [[the next night]].", "Pausing on purpose, playful and low"),
 "d9": ("Attention! A pint of ice cream, incoming!", "[[ATTENTION!]] A pint of ice cream,\nincoming!", "Loud urgent office PA announcer"),
 "d10": ("Noooooo!", "[[NOOOOO!]]", "Everyone screaming together at the top of their lungs"),
 "d11": ("Our overtime pay? Just one like!", "Our overtime pay?\nJust [[one like]]!", "Bright and playful, as if winking"),
 "d12": ("Hit the bell too… so we're ready for the next late shift.", "Liver: \"Hit the [[bell]] too…\nso we're ready for the next late shift.\"", "Shy, quiet and warm"),
 "e1": ("Up next: do you really need eight glasses of water a day? Watch that one too!", "", "Bright, clear and friendly"),
}

# ───────────────────── 쇼츠 (1080x1920 설계) ─────────────────────
def SC(ko, en, x, y, size=150, face="black", col="coral", rot=0, t0=0.0, sticky=None):
    return dict(ko=ko, en=en, x=x, y=y, size=size, face=face, col=col, rot=rot, t0=t0, sticky=sticky)

SA = []
def sa(**k): SA.append(k)
SB = []
def sb(**k): SB.append(k)

CA = [SC("야식 후", "SNACK, THEN", 470, 330, 180, "black", "coral", -3, 0, "t1"), SC("바로 눕기?", "LIE DOWN?", 470, 540, 160, "black", "butter", 2, 0, "t2")]
sa(id="sa1", sid=5, loc="s_a", actors=dict(brain=(780, "smug", 1.25)), chips=CA, props=[("sstar", dict(x=330, y=1010, txt="?", txt_en="?", size=170))])
sa(id="sa2", sid=0, loc="s_a", actors=dict(brain=(780, "worry", 1.25), stomach=(330, "wow", 0.9)), chips=CA, props=[("sstar", dict(x=330, y=1010, txt="?", txt_en="?", size=170, keep=1)), ("acid", dict(sx=330, sy=1220, short=1))])
sa(id="sa3", sid=0, loc="s_a", actors=dict(brain=(780, "happy", 1.25)),
   chips=[SC("식후 3시간", "3 HOURS", 470, 330, 170, "black", "mint", -3, 0.0, "t1"), SC("눕지 않기", "STAY UP", 470, 540, 160, "black", "butter", 2, 0.0, "t2")],
   props=[("sclock", dict(x=330, y=1010, txt="3", txt_en="3", unit="시간", unit_en="HRS"))])
sa(id="sa4", sid=10, loc="s_a", actors=dict(stomach=(780, "happy", 1.25)),
   chips=[SC("식후 3시간", "3 HOURS", 470, 330, 170, "black", "mint", -3, 0.0, "t1"), SC("눕지 않기", "STAY UP", 470, 540, 160, "black", "butter", 2, 0.0, "t2")],
   props=[("sclock", dict(x=330, y=1010, txt="3", txt_en="3", unit="시간", unit_en="HRS", keep=1))])
sa(id="sa5", sid=0, loc="s_a", actors=dict(brain=(780, "serious", 1.25)),
   chips=[SC("머리 높이기", "RAISE HEAD", 470, 330, 150, "black", "lav", -3, 0.0), SC("15~20cm", "6-8 INCHES", 470, 540, 150, "black", "sky", 2, 0.0)],
   props=[("pillow", dict(x=330, y=1090))])
sa(id="sa6", sid=7, loc="s_a", actors=dict(melatonin=(780, "sleepy", 1.25)),
   chips=[SC("근데…", "BUT…", 470, 330, 190, "black", "coral", -3, 0.0), SC("새벽 1시?", "IT'S 1 AM?", 470, 540, 160, "black", "butter", 2, 0.0)],
   props=[("sclock1", dict(x=330, y=1010))])
sa(id="sa7", sid=0, loc="s_a", actors=dict(brain=(760, "happy", 1.15)),
   chips=[SC("좋아요 + 구독", "LIKE + SUB", 470, 330, 150, "black", "coral", -2, 0.0)],
   props=[("thumbup", dict(x=300, y=780, t=0.2, sc=0.8)), ("subchip", dict(x=300, y=1090, t=0.45))])

CB = [SC("야식 먹어야", "MUST EAT LATE?", 470, 330, 150, "black", "butter", -3, 0, "t1"), SC("이렇게!", "DO THIS", 470, 540, 190, "black", "coral", 2, 0, "t2")]
sb(id="sb1", sid=10, loc="s_b", actors=dict(stomach=(780, "wow", 1.25, dict(hop=1))), chips=CB, props=[("food1", dict(x=330, y=1050, sc=1.0, t=-1))])
sb(id="sb2", sid=0, loc="s_b", actors=dict(stomach=(780, "happy", 1.25)),
   chips=[SC("자기 3시간 전", "3 HRS BEFORE BED", 470, 330, 150, "black", "mint", -3, 0, "t1"), SC("식사 끝!", "STOP EATING", 470, 540, 160, "black", "butter", 2, 0, "t2")],
   props=[("sclock", dict(x=330, y=1010, txt="3", txt_en="3", unit="시간", unit_en="HRS"))])
sb(id="sb3", sid=0, loc="s_b", actors=dict(stomach=(780, "smug", 1.25)),
   chips=[SC("기름진 음식", "GREASY FOOD", 470, 330, 150, "black", "coral", -3, 0, "t1"), SC("역류와 관련", "LINKED TO REFLUX", 470, 540, 140, "black", "lav", 2, 0, "t2")],
   props=[("food1", dict(x=330, y=1050, sc=1.0, t=0.0))])
sb(id="sb3b", sid=0, loc="s_b", actors=dict(stomach=(780, "worry", 1.25)),
   chips=[SC("자극 음식", "COMMON TRIGGERS", 470, 330, 160, "black", "coral", -3, 0, "t1"), SC("기름, 커피, 초콜릿", "FAT, COFFEE, CHOCOLATE", 470, 540, 86, "black", "lav", 2, 0, "t2")],
   props=[("sstar", dict(x=330, y=1010, txt="NIH", txt_en="NIH", size=120))])
sb(id="sb4", sid=6, loc="s_b", actors=dict(immune=(780, "serious", 1.3)),
   chips=[SC("기름진 음식", "GREASY FOOD", 470, 330, 150, "black", "coral", -3, 0, "t1"), SC("신분증 확인", "ID CHECK", 470, 540, 150, "black", "sky", 2, 0, "t2")],
   props=[("food1", dict(x=330, y=1050, sc=1.0, t=-1, shrink=0.5))])
sb(id="sb5", sid=0, loc="s_b", actors=dict(stomach=(780, "happy", 1.25)),
   chips=[SC("배고프면", "STILL HUNGRY?", 470, 330, 160, "black", "butter", -3, 0, "t1"), SC("가볍게 조금", "LIGHT & SMALL", 470, 540, 150, "black", "mint", 2, 0, "t2")],
   props=[("sstar", dict(x=330, y=1010, txt="조금", txt_en="LITE", size=120))])
sb(id="sb6", sid=3, loc="s_b", actors=dict(liver=(780, "tired", 1.25)),
   chips=[SC("결국 또…", "AND AGAIN…", 470, 330, 170, "black", "lav", -3, 0, "t1"), SC("간이 한다", "LIVER'S ON IT", 470, 540, 150, "black", "coral", 2, 0, "t2")],
   props=[("sweat", dict(x=620, y=900))])
sb(id="sb7", sid=0, loc="s_b", actors=dict(liver=(700, "happy_closed", 1.12)),
   chips=[SC("구독 + 좋아요", "SUB + LIKE", 470, 330, 150, "black", "mint", -2, 0.0)],
   props=[("subchip", dict(x=300, y=780, t=0.2)), ("thumbup", dict(x=300, y=1100, t=0.5, sc=0.8))])

SKO_A = {
 "sa1": ("야식 먹고 바로 누우셨죠? …다 보고 있었어요.", "뇌 팀장: \"야식 먹고 바로 누우셨죠?\n…다 [[보고 있었어요]].\"", "능글맞게 속삭이듯 놀리며"),
 "sa2": ("먹고 바로 누우면, 위산이 거꾸로 올라오기 쉬워요.", "먹고 바로 누우면\n[[위산]]이 거꾸로 올라오기 쉬워요", "걱정스럽지만 귀엽게 또렷하게"),
 "sa3": ("그래서 식사 후 세 시간은, 눕지 않는 게 좋아요! 미국 국립보건원, 엔아이에이치 기준이에요.", "식사 후 [[3시간]]은 눕지 않기!\n(NIH 기준)", "또박또박 밝고 자신 있게"),
 "sa4": ("타이머 맞춰 두세요! 삼 시간, 땡!", "위 대리: \"[[타이머]] 맞춰 두세요!\n3시간, 땡!\"", "신나고 빠르게 호들갑스럽게"),
 "sa5": ("정 누워야 한다면, 머리 쪽을 십오에서 이십 센티미터, 높이는 방법도 있어요.", "꼭 누워야 한다면\n머리 쪽 [[15~20cm]] 높이기", "차분하게 알려 주듯 또렷하게"),
 "sa6": ("근데… 지금, 새벽 한 시인데요?", "멜라토닌: \"근데… 지금 [[새벽 1시]]인데요?\"", "하품 섞어 졸린 목소리로 허무한 한마디"),
 "sa7": ("좋아요 한 번이면, 뇌 팀장이 오늘 칼퇴해요! 구독도 환영!", "[[좋아요]] 한 번이면 뇌 팀장이 칼퇴!\n[[구독]]도 환영!", "밝고 장난스럽게"),
}
SEN_A = {
 "sa1": ("You ate a late snack, then went straight to bed, right? …We saw everything.", "Brain: \"Late snack, then straight to bed?\n…We [[saw everything]].\"", "Teasing in a smug whisper"),
 "sa2": ("Lie down right after eating, and stomach acid can flow backward more easily.", "Lie down right after eating\nand [[acid]] can flow backward more easily", "Worried but cute, clear"),
 "sa3": ("So after a meal, stay upright for three hours. That's guidance from the U.S. NIH.", "After a meal, wait [[3 hours]] to lie down!\n(NIH guidance)", "Crisp, bright and confident"),
 "sa4": ("Set a timer! Three hours, ding!", "Stomach: \"Set a [[timer]]!\nThree hours, ding!\"", "Excited, fast, dramatic"),
 "sa5": ("If you must lie down, raising the head of the bed six to eight inches can help too.", "Must lie down?\nRaise the head [[6 to 8 inches]]", "Calm and explanatory, clear"),
 "sa6": ("But… it's already one a.m.?", "Melatonin: \"But… it's already [[1 a.m.]]?\"", "Sleepy and yawning, a deflated last line"),
 "sa7": ("One like, and the Brain clocks out on time! Subscribe too!", "One [[like]] and the Brain clocks out on time!\n[[Subscribe]] too!", "Bright and playful"),
}
SKO_B = {
 "sb1": ("사장님! 치킨은… 저녁 여덟 시 전에 주세요!", "위 대리: \"사장님! 치킨은…\n[[저녁 8시 전]]에 주세요!\"", "절규하듯 빠르고 높게"),
 "sb2": ("자기 세 시간 전엔, 식사를 끝내는 게 좋아요. 엔아이에이치 안내예요.", "자기 [[3시간 전]]엔 식사 끝!\n(NIH 안내)", "밝고 또렷하게"),
 "sb3": ("튀김처럼 기름진 음식은, 역류 증상과 관련 있다고 알려져 있어요.", "[[기름진 음식]]은\n역류 증상과 관련 있다고 알려져 있어요", "걱정스럽게 알려 주듯"),
 "sb3b": ("엔아이에이치는 기름진 음식, 초콜릿, 커피, 매운 음식을 흔한 자극 음식으로 꼽아요.", "NIH가 꼽은 [[흔한 자극 음식]]\n기름진 음식, 초콜릿, 커피, 매운 음식", "또박또박 세어 주듯 밝고 빠르게"),
 "sb4": ("기름진 건, 신분증 확인합니다.", "면역 경비: \"기름진 건,\n[[신분증]] 확인합니다.\"", "또박또박 단호하게 진지하게"),
 "sb5": ("정 배고프면? 기름지지 않은 가벼운 걸, 조금만!", "배고프면? [[가볍게, 조금만]]!", "밝고 신나게 제안하듯"),
 "sb6": ("…결국 또, 제가 하겠죠.", "간 과장: \"…결국 또, [[제가]] 하겠죠.\"", "깊은 한숨을 쉬며 낮고 쓸쓸하게"),
 "sb7": ("구독은 사원증 발급! 좋아요는 야근 수당이에요!", "[[구독]]은 사원증 발급!\n[[좋아요]]는 야근 수당!", "밝고 장난스럽게"),
}
SEN_B = {
 "sb1": ("Boss! Deliver the pizza… before eight p.m., please!", "Stomach: \"Boss! Pizza…\n[[before 8 p.m.]], please!\"", "Screaming, fast and high-pitched"),
 "sb2": ("Finish eating at least three hours before bed. That's NIH guidance.", "Finish eating [[3 hours]] before bed!\n(NIH guidance)", "Bright and clear"),
 "sb3": ("Greasy foods, like fried stuff, are linked to reflux symptoms.", "[[Greasy food]] is linked\nto reflux symptoms", "Concerned, informative"),
 "sb3b": ("The NIH lists greasy foods, chocolate, coffee and spicy foods as common triggers.", "NIH's [[common triggers]]:\ngreasy food, chocolate, coffee, spicy food", "Counting them off, bright and quick"),
 "sb4": ("Greasy stuff? ID check.", "Immune: \"Greasy stuff?\n[[ID]] check.\"", "Crisp, firm, deadly serious"),
 "sb5": ("Still hungry? Go light, and just a little!", "Hungry? [[Light and small]]!", "Bright and cheerful, suggesting"),
 "sb6": ("…And I'll handle it again, won't I.", "Liver: \"…[[I'll]] handle it again,\nwon't I.\"", "A deep sigh, low and lonely"),
 "sb7": ("Subscribe for your employee badge, and like for overtime pay!", "[[Subscribe]] = employee badge!\n[[Like]] = overtime pay!", "Bright and playful"),
}
