"""Run in the already authenticated cloud environment. Never prints OAuth secrets."""
import json,os,time,hashlib
from pathlib import Path
import requests

ROOT=Path(__file__).resolve().parent
STATE=ROOT/'upload_result.json'
def save(state):
    tmp=STATE.with_suffix('.tmp');tmp.write_text(json.dumps(state,ensure_ascii=False,indent=2),encoding='utf-8');tmp.replace(STATE)
def upload_all():
    items=json.loads((ROOT/'metadata.json').read_text(encoding='utf-8'))
    for item in items:
        path=ROOT/item['file']
        if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest()!=item['sha256']:
            raise RuntimeError('Video file missing or checksum mismatch: '+item['file'])
    state=json.loads(STATE.read_text(encoding='utf-8')) if STATE.exists() else {}
    for item in items:
        key=item['language'];record=state.setdefault(key+':'+item['sha256'],{})
        if record.get('done'):
            print('Already completed:',record['url']);continue
        required=['YT_CLIENT_ID','YT_CLIENT_SECRET','YT_REFRESH_TOKEN_'+key.upper()]
        missing=[n for n in required if not os.environ.get(n)]
        if missing:raise RuntimeError('Missing environment variables: '+', '.join(missing))
        response=requests.post('https://oauth2.googleapis.com/token',data={
            'grant_type':'refresh_token','client_id':os.environ['YT_CLIENT_ID'],
            'client_secret':os.environ['YT_CLIENT_SECRET'],'refresh_token':os.environ[required[-1]]},timeout=60)
        if response.status_code!=200:raise RuntimeError('OAuth refresh failed; HTTP '+str(response.status_code))
        token=response.json()['access_token'];session=requests.Session();session.headers['Authorization']='Bearer '+token
        def api(method,resource,**kwargs):
            r=session.request(method,'https://www.googleapis.com/youtube/v3/'+resource,timeout=120,**kwargs)
            if not r.ok:raise RuntimeError(f'{resource}: HTTP {r.status_code}')
            return r.json()
        channels=api('GET','channels',params={'part':'snippet','mine':'true'})['items']
        if len(channels)!=1 or channels[0]['snippet'].get('customUrl','').lower()!=item['channel']:
            raise RuntimeError('Channel mismatch. Expected '+item['channel'])
        if not record.get('playlist_id'):
            page=None;playlist_id=None
            while True:
                params={'part':'snippet','mine':'true','maxResults':50}
                if page:params['pageToken']=page
                result=api('GET','playlists',params=params)
                for playlist in result.get('items',[]):
                    if playlist['snippet']['title']==item['playlist_title']:playlist_id=playlist['id']
                page=result.get('nextPageToken')
                if not page:break
            if not playlist_id:
                result=api('POST','playlists',params={'part':'snippet,status'},json={
                    'snippet':{'title':item['playlist_title'],'description':item['playlist_description']},
                    'status':{'privacyStatus':'public'}})
                playlist_id=result['id']
            record['playlist_id']=playlist_id;save(state)
        if not record.get('video_id'):
            if record.get('creating'):raise RuntimeError('Previous upload outcome uncertain; check Studio before retrying.')
            record['creating']=True;save(state)
            path=ROOT/item['file']
            response=session.post('https://www.googleapis.com/upload/youtube/v3/videos',
                params={'uploadType':'resumable','part':'snippet,status','notifySubscribers':'false'},
                headers={'X-Upload-Content-Type':'video/mp4','X-Upload-Content-Length':str(path.stat().st_size)},
                json={'snippet':{'title':item['title'],'description':item['description'],'tags':item['tags'],
                      'categoryId':'26','defaultLanguage':key,'defaultAudioLanguage':key},
                      'status':{'privacyStatus':'public','selfDeclaredMadeForKids':False}},timeout=120)
            if response.status_code not in (200,201):raise RuntimeError('Upload session failed; HTTP '+str(response.status_code))
            location=response.headers['Location']
            with path.open('rb') as video:
                result=session.put(location,data=video,headers={'Content-Type':'video/mp4','Content-Length':str(path.stat().st_size)},timeout=900)
            if not result.ok:raise RuntimeError('Video upload failed; HTTP '+str(result.status_code))
            record['video_id']=result.json()['id'];record['url']='https://youtu.be/'+record['video_id'];save(state)
        vid=record['video_id'];playlist=record['playlist_id']
        existing=api('GET','playlistItems',params={'part':'id','playlistId':playlist,'videoId':vid,'maxResults':50})
        if not existing.get('items'):
            api('POST','playlistItems',params={'part':'snippet'},json={'snippet':{
                'playlistId':playlist,'resourceId':{'kind':'youtube#video','videoId':vid}}})
        check=api('GET','videos',params={'part':'snippet,status','id':vid})['items'][0]
        if check['snippet']['channelId']!=channels[0]['id']:raise RuntimeError('Post-upload channel mismatch')
        record.update(done=True,privacy=check['status']['privacyStatus'],playlist_url='https://www.youtube.com/playlist?list='+playlist)
        save(state);print(record['url'],record['privacy'],record['playlist_url'])

if __name__=='__main__':upload_all()
