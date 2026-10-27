"""예약 공개 시각 계산 (사용자 지시 2026-10-26: 롱폼 하루 2번, 현지 오전 6:45·오후 4:45, 정시 회피).
한국어 채널 = Asia/Seoul 07:00·17:00, 영어 채널 = America/New_York 07:00·17:00.
쇼츠(편당 1개, 2026-10-27 개정)는 같은 편 롱폼 공개와 같은 시각에 공개(사용자 지시 2026-10-27: 새 쇼츠 시리즈 계획이 있어 우선 롱폼과 함께 올린다).
이미 예약된(비공개 + publishAt) 영상과 겹치지 않는 가장 빠른 칸을 고른다. 업로드가 끝나기까지 여유 45분 이상.
사용: python3 sched.py ko|en  → {"long":..., "S":...} (UTC ISO8601, publishAt에 그대로 쓴다)
"""
import sys, os, json, re, datetime as dt
from zoneinfo import ZoneInfo
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import yt

CFG = {"ko": ("Asia/Seoul", ((6, 45), (16, 45))), "en": ("America/New_York", ((6, 45), (16, 45)))}   # 정시를 피해 06:45·16:45(다른 채널 알림과 안 섞이게, 설정 분석 반영 2026-10-27)
OFF = {"S": dt.timedelta(hours=0)}
LEAD = dt.timedelta(minutes=45)


def scheduled(tok):
    """내 채널의 예약 공개 대기 영상: [(publishAt(UTC), is_short)]"""
    s, j = yt.api(tok, "GET", "channels", params=dict(part="contentDetails", mine="true"))
    up = j["items"][0]["contentDetails"]["relatedPlaylists"]["uploads"]
    ids, pt = [], None
    while True:
        p = dict(part="contentDetails", playlistId=up, maxResults=50)
        if pt: p["pageToken"] = pt
        s, j = yt.api(tok, "GET", "playlistItems", params=p)
        ids += [i["contentDetails"]["videoId"] for i in j.get("items", [])]
        pt = j.get("nextPageToken")
        if not pt or len(ids) >= 150: break
    out = []
    for i in range(0, len(ids), 50):
        s, j = yt.api(tok, "GET", "videos", params=dict(part="status,contentDetails", id=",".join(ids[i:i + 50])))
        for v in j.get("items", []):
            pa = v["status"].get("publishAt")
            if not pa: continue
            t = dt.datetime.fromisoformat(pa.replace("Z", "+00:00"))
            m = re.match(r"PT(?:(\d+)M)?(?:(\d+)S)?", v["contentDetails"]["duration"])
            d = int(m.group(1) or 0) * 60 + int(m.group(2) or 0)
            if t > dt.datetime.now(dt.timezone.utc): out.append((t, d <= 75))
    return out


def plan(lang, tok=None, now=None):
    tzn, hours = CFG[lang]
    tz = ZoneInfo(tzn)
    now = now or dt.datetime.now(dt.timezone.utc)
    taken = scheduled(tok) if tok else []
    tl = [t for t, sh in taken if not sh]; ts = [t for t, sh in taken if sh]
    day = now.astimezone(tz).date()
    for d in range(0, 15):
        for h, mi in hours:
            slot = dt.datetime.combine(day + dt.timedelta(days=d), dt.time(h, mi), tz).astimezone(dt.timezone.utc)
            if slot - now < LEAD: continue
            if any(abs((slot - t).total_seconds()) < 1800 for t in tl): continue
            res = {"long": slot}
            for k, off in OFF.items():
                t = slot + off
                while any(abs((t - x).total_seconds()) < 1200 for x in ts + [v for kk, v in res.items() if kk != "long"]):
                    t += dt.timedelta(minutes=30)
                res[k] = t
            return {k: v.strftime("%Y-%m-%dT%H:%M:%SZ") for k, v in res.items()}
    raise RuntimeError("no free slot in 14 days")


if __name__ == "__main__":
    lang = sys.argv[1]
    tok, err = yt.token(lang)
    print(json.dumps(plan(lang, tok), ensure_ascii=False))
