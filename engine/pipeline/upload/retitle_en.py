"""영어 채널 제목 일괄 변경(사용자 지시 2026-10-28: 더 자극적·호기심형, 내용에 맞게). 이전 제목은 docs/title_changes_en_20261028.json에 기록.
쿼터 오류(403)가 나면 중단하고 다음 실행에서 이어 한다(이미 바뀐 건 건너뜀)."""
import sys, time, json, os
sys.path.insert(0, os.path.dirname(__file__))
import yt
from retitle_en_newtitles import NEW
LOG = os.path.join(os.path.dirname(__file__), "../../../docs/title_changes_en_20261028.json")
log = json.load(open(LOG)) if os.path.exists(LOG) else []
done = {l[0] for l in log if l[1] == "ok"}
tok, _ = yt.token("en")

def call(*a, **k):
    """quotaExceeded(403)가 요청의 절반쯤에 간헐적으로 나므로(2026-10-28 확인) 바로 재시도한다."""
    for i in range(12):
        c, j = yt.api(tok, *a, **k)
        if c != 403: return c, j
        time.sleep(3)
    return c, j
for vid, new in NEW.items():
    if vid in done: continue
    c, j = call("GET", "videos", params=dict(part="snippet", id=vid))
    if c != 200 or not j.get("items"): print("stop", vid, c, str(j)[:100]); break
    sn = j["items"][0]["snippet"]; old = sn["title"]
    if old == new: continue
    sn["title"] = new
    body = {"id": vid, "snippet": {k: sn[k] for k in ("title", "description", "categoryId", "tags", "defaultLanguage", "defaultAudioLanguage") if k in sn}}
    c, j2 = call("PUT", "videos", params=dict(part="snippet"), json=body)
    if c != 200: print("stop", vid, c, str(j2)[:100]); break
    log.append([vid, "ok", old, new]); json.dump(log, open(LOG, "w"), ensure_ascii=False, indent=1)
print(len([l for l in log if l[1] == "ok"]), "of", len(NEW), "done")
