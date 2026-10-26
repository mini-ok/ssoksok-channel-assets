import os, json, requests
CID, SEC = os.environ["YT_CLIENT_ID"], os.environ["YT_CLIENT_SECRET"]
def token(lang):
    r = requests.post("https://oauth2.googleapis.com/token", data=dict(grant_type="refresh_token", client_id=CID, client_secret=SEC, refresh_token=os.environ["YT_REFRESH_TOKEN_"+lang.upper()]))
    j = r.json()
    if "access_token" not in j: return None, {k: j.get(k) for k in ("error", "error_description")}
    return j["access_token"], None
def api(tok, method, path, **kw):
    h = {"Authorization": "Bearer " + tok}
    r = requests.request(method, "https://www.googleapis.com/youtube/v3/" + path, headers=h, timeout=60, **kw)
    try: return r.status_code, r.json()
    except Exception: return r.status_code, r.text
