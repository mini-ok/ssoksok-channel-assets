import sys, os, json, time, requests
sys.path.insert(0, "/home/claude/work/up")
from yt import *
from upload import verify, upload_video, set_thumb, load_rec, save_rec

OUT = "/home/claude/work/out/"
RES = "/home/claude/work/upload_result.json"
res = json.load(open(RES)) if os.path.exists(RES) else {}

KO_LONG_DESC = """야식 먹고 바로 누우면 속이 쓰린 이유, 몸속 회사 직원들이 보여드려요.
밤 11시 42분, 치킨 한 마리에 전 직원 야근이 시작됩니다.

이런 분께: 야식 끊기는 어렵고, 속은 쓰린 분

00:00 평화로운 퇴근 직전
00:33 치킨 대응 TF 긴급 회의
00:55 요청서 반려, 2차 입고
01:17 자정, 역류 경보
01:41 새벽 3시의 회의와 진짜 정리

핵심 포인트
- 먹고 바로 누우면 위산이 거꾸로 올라오기 쉬워요
- 미국 국립보건원(NIH, NIDDK)은 눕거나 자기 최소 3시간 전에 식사를 마치면 증상이 나아질 수 있다고 안내해요
- 정 배고프면 기름지지 않은 가벼운 걸 조금만

몸속 주식회사는 당신의 몸을 회사로 그린 직장 시트콤이에요. 뇌 팀장, 위 대리, 간 과장, 면역 경비, 멜라토닌이 야식 한 번에 밤새 야근하는 이야기예요.

구독은 사원증 발급이에요! 🪪
{LINKS}
출처
- NIDDK(미국 국립보건원) 위식도역류 식사·영양: https://www.niddk.nih.gov/health-information/digestive-diseases/acid-reflux-ger-gerd-adults/eating-diet-nutrition
- NIDDK 위식도역류 증상과 원인: https://www.niddk.nih.gov/health-information/digestive-diseases/acid-reflux-ger-gerd-adults/symptoms-causes
- NIDDK 위식도역류 치료: https://www.niddk.nih.gov/health-information/digestive-diseases/acid-reflux-ger-gerd-adults/treatment

일반 정보이며 의학적 조언이 아닙니다. 증상이 있거나 걱정되면 의료진과 상의하세요.

#몸속주식회사 #야식 #역류성식도염 #건강상식 #직장인시트콤"""

KO_A_DESC = """야식 먹고 바로 눕지 마세요. 식사 후 3시간, 이유를 30초 안에 알려드려요.
몸속 회사 뇌 팀장이 다 보고 있었대요.

핵심
- 먹고 바로 누우면 위산이 거꾸로 올라오기 쉬워요
- NIH 안내: 눕거나 자기 최소 3시간 전에 식사 마치기
- 꼭 누워야 한다면 머리 쪽을 15~20cm 높이기

구독은 사원증 발급이에요! 🪪
{LINKS}
참고: 3시간과 15~20cm는 역류 증상이 있는 분을 위한 미국 NIH(NIDDK) 생활 관리 안내예요. 증상이 없는 사람에게 같은 효과가 있는지는 확인된 바가 없어요.

출처
- https://www.niddk.nih.gov/health-information/digestive-diseases/acid-reflux-ger-gerd-adults/eating-diet-nutrition
- https://www.niddk.nih.gov/health-information/digestive-diseases/acid-reflux-ger-gerd-adults/treatment

일반 정보이며 의학적 조언이 아닙니다. 증상이 있거나 걱정되면 의료진과 상의하세요.

#Shorts #야식 #속쓰림 #쏙쏙건강백과 #건강상식"""

KO_B_DESC = """야식 마감 시간, 몇 시가 좋을까요? 자기 3시간 전에 끝내는 게 좋아요.
기름진 음식이 왜 문제인지도 30초에 알려드려요.

핵심
- NIH 안내: 눕거나 자기 최소 3시간 전에 식사 마치기
- NIH가 꼽은 흔한 자극 음식: 기름진 음식, 초콜릿, 커피와 카페인, 매운 음식, 신 과일과 토마토, 민트, 술
- 정 배고프면 기름지지 않은 가벼운 걸 조금만

구독은 사원증 발급이에요! 🪪
{LINKS}
참고: 3시간과 자극 음식 목록은 역류 증상이 있는 분을 위한 미국 NIH(NIDDK) 생활 관리 안내예요. 자극 음식은 사람에 따라 다를 수 있다고 안내하고 있어요.

출처
- https://www.niddk.nih.gov/health-information/digestive-diseases/acid-reflux-ger-gerd-adults/eating-diet-nutrition

일반 정보이며 의학적 조언이 아닙니다. 증상이 있거나 걱정되면 의료진과 상의하세요.

#Shorts #야식 #야식시간 #쏙쏙건강백과 #소화"""

EN_LONG_DESC = """Lying down right after a late-night snack? Here's what happens inside, told by the staff who work the night shift.
11:42 PM, one pepperoni pizza, and the whole company is back on overtime.

Good for: anyone who eats late and wakes up with heartburn

00:00 Almost clocking out
00:40 Emergency pizza task force
01:00 Request denied, second delivery
01:24 Midnight, reflux alert
01:50 3 AM, and a real recap

Key points
- Lie down right after eating and stomach acid can flow backward more easily
- The U.S. NIH (NIDDK) says eating at least 3 hours before you lie down or go to bed may improve symptoms
- Still hungry? Go light, not greasy, and keep it small

Tiny Body Co. is an office sitcom set inside your body. Brain the team lead, Stomach the junior, Liver the quiet manager, Immune security and Melatonin all pull an all-nighter over one snack.

Subscribe = your employee badge. 🪪
{LINKS}
Sources
- NIDDK (NIH), Eating, Diet & Nutrition for GER & GERD: https://www.niddk.nih.gov/health-information/digestive-diseases/acid-reflux-ger-gerd-adults/eating-diet-nutrition
- NIDDK, Symptoms & Causes of GER & GERD: https://www.niddk.nih.gov/health-information/digestive-diseases/acid-reflux-ger-gerd-adults/symptoms-causes
- NIDDK, Treatment of GER & GERD: https://www.niddk.nih.gov/health-information/digestive-diseases/acid-reflux-ger-gerd-adults/treatment

This is general information, not medical advice. If you have symptoms or concerns, talk to a healthcare professional.

#TinyBodyCo #LateNightSnack #AcidReflux #HealthTips #OfficeSitcom"""

EN_A_DESC = """Lying down right after a late snack? Wait 3 hours, and here's why, in under a minute.
Brain the team lead says he saw everything.

Key points
- Lie down right after eating and acid can flow backward more easily
- NIH guidance: finish eating at least 3 hours before lying down or bed
- If you must lie down, raising the head of the bed 6 to 8 inches can help

Subscribe = your employee badge. 🪪
{LINKS}
Note: the 3 hours and the 6-to-8-inch tip are U.S. NIH (NIDDK) self-care guidance for people with reflux symptoms; the same effect in people without symptoms has not been established.

Sources
- https://www.niddk.nih.gov/health-information/digestive-diseases/acid-reflux-ger-gerd-adults/eating-diet-nutrition
- https://www.niddk.nih.gov/health-information/digestive-diseases/acid-reflux-ger-gerd-adults/treatment

This is general information, not medical advice. If you have symptoms or concerns, talk to a healthcare professional.

#Shorts #AcidReflux #LateNightSnack #TinyBodyCo #HealthTips"""

EN_B_DESC = """What time should you stop eating at night? About 3 hours before bed.
And here's which foods are most often linked to reflux.

Key points
- NIH guidance: finish eating at least 3 hours before lying down or bed
- Common triggers per the NIH: greasy foods, chocolate, coffee and caffeine, spicy foods, citrus and tomato, mint, alcohol
- Still hungry? Go light, not greasy, and keep it small

Subscribe = your employee badge. 🪪
{LINKS}
Note: the 3-hour tip and the trigger list are U.S. NIH (NIDDK) self-care guidance for people with reflux symptoms, and the NIH notes triggers vary from person to person.

Sources
- https://www.niddk.nih.gov/health-information/digestive-diseases/acid-reflux-ger-gerd-adults/eating-diet-nutrition

This is general information, not medical advice. If you have symptoms or concerns, talk to a healthcare professional.

#Shorts #LateNightSnack #AcidReflux #TinyBodyCo #Digestion"""

JOBS = {
 "ko": [
  dict(key="ko_long", file="몸속주식회사_야식습격사건_롱폼.mp4", thumb="thumb_yasik_long_ko.png",
       title="야식 먹고 바로 누우면? 몸속 회사 야근 실화", desc=KO_LONG_DESC,
       tags=["야식", "야식 습관", "먹고 바로 눕기", "위산 역류", "역류성 식도염", "속쓰림", "소화", "몸속 주식회사", "몸속회사", "쏙쏙 건강백과", "직장인 시트콤", "건강 애니메이션", "위 건강", "수면과 식사", "밤에 먹기"]),
  dict(key="ko_A", file="쏙쏙건강백과_야식_쇼츠A.mp4", thumb="thumb_yasik_short_A_ko.png",
       title="야식 먹고 바로 누우면 생기는 일 #Shorts", desc=KO_A_DESC,
       tags=["야식", "먹고 바로 눕기", "위산 역류", "속쓰림", "식후 3시간", "쏙쏙 건강백과", "몸속 주식회사", "건강 쇼츠", "소화", "수면 자세", "베개 높이", "역류성 식도염", "건강 상식", "뇌 팀장"]),
  dict(key="ko_B", file="쏙쏙건강백과_야식_쇼츠B.mp4", thumb="thumb_yasik_short_B_ko.png",
       title="야식 몇 시까지? 자기 3시간 전 끝내기 #Shorts", desc=KO_B_DESC,
       tags=["야식", "야식 시간", "야식 마감", "자기 3시간 전", "기름진 음식", "속쓰림", "위산 역류", "쏙쏙 건강백과", "몸속 주식회사", "위 대리", "건강 쇼츠", "소화", "간 과장", "건강 상식"]),
 ],
 "en": [
  dict(key="en_long", file="TinyBodyCo_LateNightSnack_long.mp4", thumb="thumb_yasik_long_en.png",
       title="Lying Down After a Late Snack? Inside Your Body's Night Shift", desc=EN_LONG_DESC,
       tags=["late night snack", "eating before bed", "lying down after eating", "acid reflux", "heartburn", "GERD", "digestion", "tiny body co", "tiny body company", "office sitcom", "health animation", "stomach health", "sleep and food", "night eating", "NIH guidance"]),
  dict(key="en_A", file="TinyBodyCo_LateSnack_shortA.mp4", thumb="thumb_yasik_short_A_en.png",
       title="What Happens If You Lie Down Right After Eating #Shorts", desc=EN_A_DESC,
       tags=["lying down after eating", "late night snack", "acid reflux", "heartburn", "3 hours before bed", "tiny body co", "health shorts", "digestion", "bed wedge", "raise head of bed", "GERD", "stomach", "health tips", "brain team lead"]),
  dict(key="en_B", file="TinyBodyCo_LateSnack_shortB.mp4", thumb="thumb_yasik_short_B_en.png",
       title="Late Snack Cutoff: Stop Eating 3 Hours Before Bed #Shorts", desc=EN_B_DESC,
       tags=["late snack cutoff", "what time to stop eating", "eating before bed", "acid reflux triggers", "greasy food heartburn", "tiny body co", "health shorts", "digestion", "stomach", "GERD diet", "chocolate coffee reflux", "night eating", "health tips", "liver"]),
 ],
}

PL = dict(ko=dict(series="PLdJ8P8SMNR0c", sitcom="PLVGrX73QZbiA", shorts="PLbR2H6AaPNzo"),
          en=dict(series="PLCOvtns0oO_4", sitcom="PLMqs4yksTex4", shorts="PLT-1LPHSJBmA"))
NEXTV = dict(ko="NlhUs7RgJgI", en="ggqUJCAukbA")


def save():
    json.dump(res, open(RES, "w"), ensure_ascii=False, indent=1)


def links(lang, key):
    s = PL[lang]["series"]; sc = PL[lang]["sitcom"]
    L = res.get(lang, {})
    lg, a, b = L.get("ko_long" if lang == "ko" else "en_long"), L.get(lang + "_A"), L.get(lang + "_B")
    out = []
    if lang == "ko":
        out.append(f"이 시리즈 이어서 보기: https://www.youtube.com/playlist?list={s}")
        if key.endswith("long"):
            out.append(f"몸속 주식회사 시트콤 전체 보기: https://www.youtube.com/playlist?list={sc}")
            out.append(f"다음에 볼 영상: https://youtu.be/{NEXTV['ko']}")
            if a and b: out.append(f"이 주제의 쇼츠: https://youtu.be/{a} · https://youtu.be/{b}")
        else:
            if lg: out.append(f"같은 주제의 긴 영상: https://youtu.be/{lg}")
            if key.endswith("_A") and b: out.append(f"다음 쇼츠: https://youtu.be/{b}")
    else:
        out.append(f"Keep watching this series: https://www.youtube.com/playlist?list={s}")
        if key.endswith("long"):
            out.append(f"The whole office sitcom: https://www.youtube.com/playlist?list={sc}")
            out.append(f"Watch next: https://youtu.be/{NEXTV['en']}")
            if a and b: out.append(f"Shorts on this topic: https://youtu.be/{a} | https://youtu.be/{b}")
        else:
            if lg: out.append(f"Full video: https://youtu.be/{lg}")
            if key.endswith("_A") and b: out.append(f"Next Short: https://youtu.be/{b}")
    return "\n" + "\n".join(out) + "\n"


def snippet_of(lang, j, with_links):
    d = j["desc"].replace("{LINKS}", links(lang, j["key"]) if with_links else "")
    return {"title": j["title"], "description": d, "tags": j["tags"], "categoryId": "27",
            "defaultLanguage": lang, "defaultAudioLanguage": lang}


def main():
    log = res.setdefault("log", [])
    for lang in ("ko", "en"):
        tok, err = verify(lang)
        if not tok:
            log.append(f"{lang}: {err}"); print(lang, "VERIFY FAIL", err); save(); continue
        res.setdefault(lang, {})
        for j in JOBS[lang]:
            if res[lang].get(j["key"]):
                print("skip", j["key"], res[lang][j["key"]]); continue
            path = OUT + j["file"]
            if not os.path.exists(path):
                log.append(f"{j['key']}: file missing"); continue
            v, err = upload_video(tok, path, snippet_of(lang, j, False))
            if err:
                log.append(f"{j['key']} upload: {err}"); print("FAIL", j["key"], err); save(); continue
            vid = v["id"]; res[lang][j["key"]] = vid
            res.setdefault("status", {})[j["key"]] = v["status"]["privacyStatus"]
            print("uploaded", j["key"], vid, v["status"]["privacyStatus"], flush=True)
            save()
            ok, msg = set_thumb(tok, vid, OUT + j["thumb"])
            res.setdefault("thumb", {})[j["key"]] = "ok" if ok else msg
            print("  thumb", ok, "" if ok else msg, flush=True)
            save()
    save()


if __name__ == "__main__":
    main()
