"""Exercise the packaged uploader with a fake YouTube API; never contacts a real service."""
import json,hashlib,tempfile,importlib.util,os,contextlib,io,sys
from pathlib import Path
from unittest.mock import patch
WORK=Path(__file__).resolve().parents[3]
SOURCE=Path(sys.argv[1]) if len(sys.argv)>1 else WORK/'toast_upload_handoff'
class Response:
 def __init__(self,body,headers=None):self.body=body;self.headers=headers or {};self.ok=True;self.status_code=200
 def json(self):return self.body
def run(wrong_channel=False,private=False):
 with tempfile.TemporaryDirectory() as tmp:
  root=Path(tmp);items=json.loads((SOURCE/'metadata.json').read_text(encoding='utf-8'))
  for item in items:
   data=('fake-video-'+item['language']).encode();(root/item['file']).write_bytes(data);item['sha256']=hashlib.sha256(data).hexdigest()
  (root/'metadata.json').write_text(json.dumps(items),encoding='utf-8')
  spec=importlib.util.spec_from_file_location('handoff_under_test',SOURCE/'upload.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
  m.ROOT=root;m.STATE=root/'upload_result.json';sessions=[];calls=[]
  class Session:
   def __init__(self):self.i=len(sessions);self.headers={};sessions.append(self)
   def request(self,method,url,**kw):
    assert url.startswith('https://www.googleapis.com/youtube/v3/');resource=url.rsplit('/',1)[-1];calls.append((method,resource,self.i))
    if resource=='channels':return Response({'items':[{'id':'channel'+str(self.i),'snippet':{'customUrl':'@wrong' if wrong_channel else items[self.i]['channel']}}]})
    if resource=='playlists':
     assert method=='GET';return Response({'items':[{'id':'playlist'+str(self.i),'snippet':{'title':items[self.i]['playlist_title']}}]})
    if resource=='playlistItems':return Response({'items':[]} if method=='GET' else {})
    if resource=='videos':return Response({'items':[{'snippet':{'channelId':'channel'+str(self.i)},'status':{'privacyStatus':'private' if private else 'public'}}]})
    raise AssertionError(resource)
   def post(self,url,**kw):
    assert url=='https://www.googleapis.com/upload/youtube/v3/videos'
    assert kw['json']['snippet']['defaultAudioLanguage']==items[self.i]['language']
    calls.append(('UPLOAD',self.i));return Response({}, {'Location':'https://www.googleapis.com/mock-upload'})
   def put(self,url,**kw):
    assert url=='https://www.googleapis.com/mock-upload';return Response({'id':'video'+str(self.i)})
  env={k:'mock-value' for k in ['YT_CLIENT_ID','YT_CLIENT_SECRET','YT_REFRESH_TOKEN_KO','YT_REFRESH_TOKEN_EN']}
  def refresh(url,**kw):assert url=='https://oauth2.googleapis.com/token';return Response({'access_token':'mock-token'})
  with patch.dict(os.environ,env),patch.object(m.requests,'post',side_effect=refresh),patch.object(m.requests,'Session',Session),contextlib.redirect_stdout(io.StringIO()):
   if wrong_channel or private:
    try:m.upload_all();raise AssertionError('Expected upload rejection')
    except RuntimeError as e:assert ('Channel mismatch' if wrong_channel else 'not public') in str(e)
    if wrong_channel:assert not any(c[0]=='UPLOAD' for c in calls)
   else:
    m.upload_all();assert len(sessions)==2
    assert len([c for c in calls if c[0]=='POST' and c[1]=='playlistItems'])==2
    m.upload_all();assert len(sessions)==2, 'repeat invocation attempted duplicate uploads'
    state=json.loads(m.STATE.read_text());assert all(state[item['language']+':'+item['sha256']]['done'] for item in items)
    (root/items[0]['file']).write_bytes(b'changed')
    try:m.upload_all();raise AssertionError('Checksum mismatch was accepted')
    except RuntimeError as e:assert 'checksum mismatch' in str(e)
run();run(wrong_channel=True);run(private=True)
print('PASS: correct channels/playlists, both languages, duplicate prevention, hash mismatch, wrong channel and non-public rejection; all API calls mocked.')
