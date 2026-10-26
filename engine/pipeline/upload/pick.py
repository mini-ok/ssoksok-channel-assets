import sys, os, json, requests; sys.path.insert(0, "/home/claude/work/up")
from yt import *
CAND = dict(ko=["PLdJ8P8SMNR0c"], en=["PLCOvtns0oO_4"])
out = {}
os.makedirs("/home/claude/work/media", exist_ok=True)
for lang in ("ko", "en"):
    t, e = token(lang)
    s, j = api(t, "GET", "channels", params=dict(part="snippet", mine="true"))
    sn = j["items"][0]["snippet"]
    logo = sn["thumbnails"]["high"]["url"]
    lp = f"/home/claude/work/media/logo_{lang}.png"
    open(lp, "wb").write(requests.get(logo, timeout=60).content)
    vids = []
    for pid in CAND[lang]:
        s, j = api(t, "GET", "playlistItems", params=dict(part="snippet", playlistId=pid, maxResults=50))
        for x in j.get("items", []):
            vids.append((x["snippet"]["resourceId"]["videoId"], x["snippet"]["title"]))
    ids = ",".join(v[0] for v in vids)
    s, j = api(t, "GET", "videos", params=dict(part="snippet,statistics,contentDetails", id=ids))
    rows = []
    for it in j["items"]:
        dur = it["contentDetails"]["duration"]
        secs = 0
        import re
        m = re.match(r"PT(?:(\d+)M)?(?:(\d+)S)?", dur)
        if m: secs = int(m.group(1) or 0) * 60 + int(m.group(2) or 0)
        rows.append((int(it["statistics"].get("viewCount", 0)), secs, it["id"], it["snippet"]["title"], it["snippet"]["thumbnails"]["high"]["url"]))
    rows = [r for r in rows if r[1] > 70]
    rows.sort(reverse=True)
    for r in rows: print(lang, r[0], r[1], r[2], r[3])
    best = rows[0]
    tp = f"/home/claude/work/media/next_{lang}.jpg"
    open(tp, "wb").write(requests.get(best[4], timeout=60).content)
    out[lang] = dict(id=best[2], title=best[3], thumb=tp, logo=lp, views=best[0])
json.dump(out, open("/home/claude/work/endinfo.json", "w"), ensure_ascii=False, indent=1)
print(json.dumps(out, ensure_ascii=False))
