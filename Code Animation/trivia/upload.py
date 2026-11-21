"""지식 쇼츠를 허상공방 채널(@dreamloom_studio)에 올린다 — YouTube Data API v3.

python3 upload.py <에피소드 slug> <mp4> [--publish-at 2026-11-22T09:00:00+09:00] [--dry-run]

필요한 환경 변수(값은 출력·로그·커밋에 남기지 않는다):
  YT_CLIENT_ID, YT_CLIENT_SECRET   OAuth 클라이언트(쏙쏙 채널과 같은 값)
  YT_REFRESH_TOKEN_DREAMLOOM       허상공방 채널을 골라 받은 리프레시 토큰(docs/youtube_api_setup_guide.md 단계 6-2)
에피소드 파일의 YT = dict(title_en, title_ko, desc_en, desc_ko, tags)를 쓴다.
- 업로드 전에 channels.list(mine=true)로 채널 주소가 @dreamloom_studio인지 확인하고, 다르면 올리지 않는다.
- 영어 원문(defaultLanguage=en) + 한국어 번역(localizations.ko), 카테고리 1(영화/애니메이션), 아동용 아님, 구독자 알림 끔.
- 영어 제목·설명에 한글이 섞이면 멈춘다(채널 규칙).
- 결과를 uploads.json에 한 줄 덧붙이고 영상 ID를 출력한다.
쇼츠의 '관련 동영상'은 API로 지정할 수 없다(Studio에서 따로).
"""
import os, sys, json, re, time, datetime, argparse
import requests

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
CHANNEL = '@dreamloom_studio'
REC = os.path.join(HERE, 'uploads.json')
HANGUL = re.compile(r'[ᄀ-ᇿ㄰-㆏가-힣ㆍᆞ]')


def token():
    need = ['YT_CLIENT_ID', 'YT_CLIENT_SECRET', 'YT_REFRESH_TOKEN_DREAMLOOM']
    miss = [k for k in need if not os.environ.get(k)]
    if miss: sys.exit('환경 변수 없음: ' + ', '.join(miss))
    r = requests.post('https://oauth2.googleapis.com/token', data=dict(
        grant_type='refresh_token', client_id=os.environ['YT_CLIENT_ID'],
        client_secret=os.environ['YT_CLIENT_SECRET'], refresh_token=os.environ['YT_REFRESH_TOKEN_DREAMLOOM']), timeout=30)
    if r.status_code != 200: sys.exit(f'토큰 발급 실패 {r.status_code}: {r.text[:200]}')
    return r.json()['access_token']


def api(tok, method, path, **kw):
    r = requests.request(method, 'https://www.googleapis.com/youtube/v3/' + path,
                         headers={'Authorization': 'Bearer ' + tok}, timeout=60, **kw)
    return r.status_code, (r.json() if r.text else {})


def check_channel(tok):
    s, j = api(tok, 'GET', 'channels', params=dict(part='snippet', mine='true'))
    if s != 200 or not j.get('items'): sys.exit(f'채널 조회 실패 {s} {str(j)[:200]}')
    cu = j['items'][0]['snippet'].get('customUrl', '')
    if cu.lower() != CHANNEL: sys.exit(f'채널이 다름: {cu} (기대 {CHANNEL}) — 올리지 않음')
    return j['items'][0]['id']


def build_body(yt, publish_at=None):
    for k in ('title_en', 'desc_en'):
        if HANGUL.search(yt[k]): sys.exit(f'{k}에 한글이 섞여 있음 — 채널 규칙 위반')
    if len(yt['title_en']) > 100 or len(yt['title_ko']) > 100: sys.exit('제목이 100자를 넘음')
    body = {
        'snippet': {'title': yt['title_en'], 'description': yt['desc_en'], 'tags': yt.get('tags', []),
                    'categoryId': '1', 'defaultLanguage': 'en'},
        'status': {'privacyStatus': 'public', 'selfDeclaredMadeForKids': False, 'embeddable': True, 'publicStatsViewable': True},
        'localizations': {'ko': {'title': yt['title_ko'], 'description': yt['desc_ko']}},
    }
    if publish_at:
        body['status']['privacyStatus'] = 'private'; body['status']['publishAt'] = publish_at
    return body


def upload(tok, path, body):
    size = os.path.getsize(path)
    h = {'Authorization': 'Bearer ' + tok, 'X-Upload-Content-Type': 'video/mp4', 'X-Upload-Content-Length': str(size),
         'Content-Type': 'application/json; charset=UTF-8'}
    r = requests.post('https://www.googleapis.com/upload/youtube/v3/videos?uploadType=resumable'
                      '&part=snippet,status,localizations&notifySubscribers=false', headers=h, json=body, timeout=60)
    if r.status_code != 200: sys.exit(f'업로드 시작 실패 {r.status_code}: {r.text[:300]}')
    loc = r.headers['Location']; data = open(path, 'rb').read()
    for wait in (0, 3, 8, 20):
        if wait: time.sleep(wait)
        try:
            r2 = requests.put(loc, headers={'Content-Type': 'video/mp4', 'Content-Length': str(size)}, data=data, timeout=900)
        except Exception:
            continue
        if r2.status_code in (200, 201): return r2.json()
        if r2.status_code < 500: sys.exit(f'업로드 실패 {r2.status_code}: {r2.text[:300]}')
    sys.exit('업로드 실패(재시도 끝)')


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('slug'); ap.add_argument('mp4')
    ap.add_argument('--publish-at'); ap.add_argument('--dry-run', action='store_true')
    a = ap.parse_args()
    import engine as E
    ep = E.Episode(a.slug)
    yt = getattr(ep.m, 'YT', None)
    if not yt: sys.exit('에피소드 파일에 YT 메타데이터가 없음')
    body = build_body(yt, a.publish_at)
    if a.dry_run:
        print(json.dumps(body, ensure_ascii=False, indent=1)); sys.exit(0)
    tok = token(); ch = check_channel(tok)
    j = upload(tok, a.mp4, body)
    vid = j['id']; st = j.get('status', {})
    rec = json.load(open(REC)) if os.path.exists(REC) else []
    rec.append(dict(slug=a.slug, id=vid, url=f'https://youtube.com/shorts/{vid}', privacy=st.get('privacyStatus'),
                    publishAt=st.get('publishAt'), uploaded=datetime.datetime.now(datetime.timezone.utc).isoformat(timespec='seconds')))
    json.dump(rec, open(REC, 'w'), ensure_ascii=False, indent=1)
    print('UPLOADED', vid, st.get('privacyStatus'), st.get('publishAt') or '')
