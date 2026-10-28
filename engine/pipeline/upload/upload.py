import sys, os, json, time, requests
sys.path.insert(0, "/home/claude/work/up")
from yt import *
REC = "/home/claude/shorts-health/uploads.json"
def load_rec():
    return json.load(open(REC)) if os.path.exists(REC) else []
def save_rec(r): json.dump(r, open(REC, "w"), ensure_ascii=False, indent=1)

def verify(lang):
    t, e = token(lang)
    if not t: return None, f"token fail {e}"
    s, j = api(t, "GET", "channels", params=dict(part="snippet", mine="true"))
    if s != 200: return None, f"channels {s} {str(j)[:200]}"
    cu = j["items"][0]["snippet"].get("customUrl", "")
    want = "@ssoksok-health" if lang == "ko" else "@tinybodyco"
    if cu.lower() != want: return None, f"channel mismatch {cu}"
    return t, None

def upload_video(tok, path, snippet, publish_at=None):
    size = os.path.getsize(path)
    h = {"Authorization": "Bearer " + tok, "X-Upload-Content-Type": "video/mp4", "X-Upload-Content-Length": str(size), "Content-Type": "application/json; charset=UTF-8"}
    body = {"snippet": snippet, "status": {"privacyStatus": "public", "selfDeclaredMadeForKids": False, "embeddable": True, "publicStatsViewable": True}}
    if publish_at:   # 예약 공개: 비공개로 올리고 publishAt(UTC ISO8601)에 자동 공개(sched.py가 시각을 정한다)
        body["status"]["privacyStatus"] = "private"; body["status"]["publishAt"] = publish_at
    # 구독자 알림 폭주 방지(사용자 허락 2026-10-26, 설정 분석 반영): 숏폼은 알림을 보내지 않고 롱폼만 보낸다
    notify = "false" if "#shorts" in snippet.get("title", "").lower() else "true"
    r = requests.post(f"https://www.googleapis.com/upload/youtube/v3/videos?uploadType=resumable&part=snippet,status&notifySubscribers={notify}", headers=h, json=body, timeout=60)
    if r.status_code != 200:
        return None, f"init {r.status_code} {r.text[:300]}"
    loc = r.headers["Location"]
    data = open(path, "rb").read()
    for wait in (0, 2, 4, 8):
        if wait: time.sleep(wait)
        try:
            r2 = requests.put(loc, headers={"Content-Type": "video/mp4", "Content-Length": str(size)}, data=data, timeout=900)
        except Exception as ex:
            continue
        if r2.status_code in (200, 201):
            j = r2.json(); return j, None
        if r2.status_code < 500: return None, f"put {r2.status_code} {r2.text[:300]}"
    return None, "put failed after retries"

def _thumb_jpeg(path, limit=1_900_000):
    """썸네일을 JPEG로 변환하고 2MB 안쪽으로 맞춘다(쇼츠 맞춤 썸네일은 용량·형식에 까다롭다는 사용자 지시, 2026-10-28)."""
    import io
    from PIL import Image
    im = Image.open(path).convert("RGB")
    for q in (92, 88, 84, 80, 75, 70):
        b = io.BytesIO(); im.save(b, "JPEG", quality=q, optimize=True, subsampling=0 if q >= 88 else 2)
        if b.tell() <= limit: return b.getvalue()
    im = im.resize((im.width * 3 // 4, im.height * 3 // 4), Image.LANCZOS)
    b = io.BytesIO(); im.save(b, "JPEG", quality=80, optimize=True); return b.getvalue()

def set_thumb(tok, vid, path):
    r = requests.post(f"https://www.googleapis.com/upload/youtube/v3/thumbnails/set?videoId={vid}",
                      headers={"Authorization": "Bearer " + tok, "Content-Type": "image/jpeg"}, data=_thumb_jpeg(path), timeout=300)
    return r.status_code == 200, f"{r.status_code} {r.text[:200]}"
