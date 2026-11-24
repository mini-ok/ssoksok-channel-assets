import os, sys, json, requests
slug, outdir = sys.argv[1], sys.argv[2]
m = json.load(open(os.path.join(outdir, 'meta.json'))); path = os.path.join(outdir, 'video.mp4')
assert m['slug'] == slug and os.path.getsize(path) > 0
assert len(m['title_en']) <= 100 and not any('가' <= c <= '힣' for c in m['title_en'] + m['desc_en'])
r = requests.post('https://oauth2.googleapis.com/token', data={'grant_type':'refresh_token','client_id':os.environ['YT_CLIENT_ID'],'client_secret':os.environ['YT_CLIENT_SECRET'],'refresh_token':os.environ['YT_REFRESH_TOKEN_DREAMLOOM']}, timeout=60)
if r.status_code != 200: sys.exit('OAuth refresh failed HTTP %d' % r.status_code)
s = requests.Session(); s.headers['Authorization'] = 'Bearer ' + r.json()['access_token']
ch = s.get('https://www.googleapis.com/youtube/v3/channels', params={'part':'snippet,contentDetails','mine':'true'}, timeout=60).json()['items']
assert len(ch) == 1 and ch[0]['snippet'].get('customUrl','').lower() == '@dreamloom_studio', 'channel mismatch: %s' % [c['snippet'].get('customUrl') for c in ch]
print('channel ok', ch[0]['snippet']['customUrl'], ch[0]['id'])
if '--check' in sys.argv: sys.exit()
up = ch[0]['contentDetails']['relatedPlaylists']['uploads']
for i in s.get('https://www.googleapis.com/youtube/v3/playlistItems', params={'part':'snippet','playlistId':up,'maxResults':50}, timeout=60).json().get('items', []):
    if i['snippet']['title'] == m['title_en']: sys.exit('already uploaded: ' + i['snippet']['resourceId']['videoId'])
body = {'snippet': {'title': m['title_en'], 'description': m['desc_en'], 'tags': m['tags'], 'categoryId': '1', 'defaultLanguage': 'en', 'defaultAudioLanguage': 'en'},
        'status': {'privacyStatus': 'public', 'selfDeclaredMadeForKids': False},
        'localizations': {'ko': {'title': m['title_ko'], 'description': m['desc_ko']}}}
h = s.post('https://www.googleapis.com/upload/youtube/v3/videos', params={'uploadType':'resumable','part':'snippet,status,localizations','notifySubscribers':'false'},
           headers={'X-Upload-Content-Type':'video/mp4','X-Upload-Content-Length':str(os.path.getsize(path))}, json=body, timeout=120)
if h.status_code not in (200, 201): sys.exit('session failed HTTP %d %s' % (h.status_code, h.text[:300]))
with open(path, 'rb') as f:
    u = s.put(h.headers['Location'], data=f, headers={'Content-Type':'video/mp4'}, timeout=900)
if not u.ok: sys.exit('upload failed HTTP %d %s' % (u.status_code, u.text[:300]))
vid = u.json()['id']
v = s.get('https://www.googleapis.com/youtube/v3/videos', params={'part':'snippet,status,localizations','id':vid}, timeout=60).json()['items'][0]
assert v['snippet']['channelId'] == ch[0]['id']
print(json.dumps({'slug': slug, 'video_id': vid, 'url': 'https://youtube.com/shorts/' + vid, 'privacy': v['status']['privacyStatus'], 'category': v['snippet']['categoryId'], 'lang': v['snippet'].get('defaultLanguage'), 'ko_localized': 'ko' in v.get('localizations', {})}, ensure_ascii=False))
