import sys; sys.path.insert(0, "/home/claude/work/up")
from yt import *
import sys
for lang, cu in (("ko", "@ssoksok-health"), ("en", "@tinybodyco")):
    t, e = token(lang)
    if not t: print(lang, "token fail", e); continue
    s, j = api(t, "GET", "channels", params=dict(part="snippet,contentDetails", mine="true"))
    if s != 200: print(lang, s, str(j)[:300]); continue
    it = j["items"][0]; print(lang, it["snippet"]["customUrl"], it["id"], it["contentDetails"]["relatedPlaylists"]["uploads"])
    up = it["contentDetails"]["relatedPlaylists"]["uploads"]
    vids = []; pt = None
    while True:
        s, j = api(t, "GET", "playlistItems", params=dict(part="snippet", playlistId=up, maxResults=50, **({"pageToken": pt} if pt else {})))
        vids += [(x["snippet"]["resourceId"]["videoId"], x["snippet"]["title"], x["snippet"]["publishedAt"][:10]) for x in j.get("items", [])]
        pt = j.get("nextPageToken")
        if not pt: break
    print(len(vids))
    for v in vids: print(" ", *v)
