import sys; sys.path.insert(0, "/home/claude/work/up")
from yt import *
for lang in ("ko", "en"):
    t, e = token(lang)
    print("==", lang)
    pt = None
    while True:
        s, j = api(t, "GET", "playlists", params=dict(part="snippet,contentDetails", mine="true", maxResults=50, **({"pageToken": pt} if pt else {})))
        for x in j.get("items", []):
            print(" ", x["id"], x["contentDetails"]["itemCount"], x["snippet"]["title"])
        pt = j.get("nextPageToken")
        if not pt: break
