import sys, os, json
sys.path.insert(0, "/home/claude/work/up")
from yt import *
from upload import verify
import run_upload as RU

res = json.load(open(RU.RES))
out = res.setdefault("post", {})

def save(): json.dump(res, open(RU.RES, "w"), ensure_ascii=False, indent=1)

def pl_items(tok, pid):
    ids, pt = [], None
    while True:
        s, j = api(tok, "GET", "playlistItems", params=dict(part="snippet", playlistId=pid, maxResults=50, **({"pageToken": pt} if pt else {})))
        if s != 200: return ids, f"{s} {str(j)[:150]}"
        ids += [x["snippet"]["resourceId"]["videoId"] for x in j.get("items", [])]
        pt = j.get("nextPageToken")
        if not pt: return ids, None

def add(tok, pid, vid):
    have, err = pl_items(tok, pid)
    if err: return f"list fail {err}"
    if vid in have: return "already"
    s, j = api(tok, "POST", "playlistItems", params=dict(part="snippet"),
               json={"snippet": {"playlistId": pid, "resourceId": {"kind": "youtube#video", "videoId": vid}}})
    return "ok" if s == 200 else f"{s} {str(j)[:200]}"

for lang in ("ko", "en"):
    tok, err = verify(lang)
    if not tok:
        out[lang] = {"verify": err}; save(); continue
    o = out.setdefault(lang, {})
    V = res[lang]
    L, A, B = V[lang + "_long"], V[lang + "_A"], V[lang + "_B"]
    # 재생목록
    for vid, pls in ((L, ["series", "sitcom"]), (A, ["series", "shorts"]), (B, ["series", "shorts"])):
        for p in pls:
            o[f"pl_{p}_{vid}"] = add(tok, RU.PL[lang][p], vid)
    save()
    # 설명 링크 업데이트
    for j in RU.JOBS[lang]:
        vid = V[j["key"]]
        sn = RU.snippet_of(lang, j, True)
        s, r = api(tok, "PUT", "videos", params=dict(part="snippet"), json={"id": vid, "snippet": sn})
        o[f"desc_{j['key']}"] = "ok" if s == 200 else f"{s} {str(r)[:200]}"
        if s == 200 and r.get("snippet", {}).get("title") != j["title"]:
            o[f"desc_{j['key']}"] = "title changed!"
    save()
    # 첫 댓글(롱폼)
    if lang == "ko":
        txt = "여러분은 야식 마지노선이 몇 시예요? 🍗\n다음엔 이 영상도 어때요? https://youtu.be/" + RU.NEXTV["ko"]
    else:
        txt = "What time is your personal late-snack cutoff? 🍕\nWatch this next: https://youtu.be/" + RU.NEXTV["en"]
    s, r = api(tok, "POST", "commentThreads", params=dict(part="snippet"),
               json={"snippet": {"videoId": L, "topLevelComment": {"snippet": {"textOriginal": txt}}}})
    o["comment"] = "ok" if s == 200 else f"{s} {str(r)[:200]}"
    save()
    # 이전 영상 쪽 연결(c-6)
    prev = RU.NEXTV[lang]
    s, r = api(tok, "GET", "videos", params=dict(part="snippet", id=prev))
    if s == 200 and r.get("items"):
        sn = r["items"][0]["snippet"]
        line = ("함께 보면 좋은 영상: https://youtu.be/" + L) if lang == "ko" else ("Related: https://youtu.be/" + L)
        if L not in sn.get("description", ""):
            new = dict(title=sn["title"], description=sn["description"].rstrip() + "\n\n" + line,
                       tags=sn.get("tags", []), categoryId=sn.get("categoryId", "27"),
                       defaultLanguage=sn.get("defaultLanguage", lang), defaultAudioLanguage=sn.get("defaultAudioLanguage", lang))
            s2, r2 = api(tok, "PUT", "videos", params=dict(part="snippet"), json={"id": prev, "snippet": new})
            o["backlink"] = "ok" if s2 == 200 and r2["snippet"]["title"] == sn["title"] else f"{s2} {str(r2)[:150]}"
        else:
            o["backlink"] = "already"
    else:
        o["backlink"] = f"get {s}"
    save()
print(json.dumps(out, ensure_ascii=False, indent=1))
