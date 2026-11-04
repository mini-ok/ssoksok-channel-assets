"""Exercise release readiness, integrity checks and idempotency without a network."""
import hashlib,sys,unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parent))
import release_episode as m

class Response:
    def __init__(self,code,data):self.status_code=code;self.data=data
    def json(self):return self.data
class FakeGitHub:
    repo='mini-ok/ssoksok-channel-assets'
    def __init__(self):self.record=None;self.assets={};self.actions=[];self.corrupt=False
    def release(self,tag):return self.record
    def request(self,method,path,**kw):
        self.actions.append((method,path))
        if method=='POST' and path=='/releases':
            self.record=dict(id=1,draft=True,upload_url='https://uploads.github.com/repos/test/assets{?name}',html_url='https://github.com/test/release');return Response(201,self.record)
        if method=='GET' and path=='/releases/1/assets':return Response(200,list(self.assets.values()))
        if method=='POST':
            name=kw['params']['name'];data=kw['data'];sha=hashlib.sha256(data).hexdigest();asset=dict(id=len(self.assets)+1,name=name,digest='sha256:'+('0'*64 if self.corrupt else sha));self.assets[name]=asset;return Response(201,asset)
        if method=='PATCH':self.record['draft']=False;return Response(200,self.record)
        raise AssertionError((method,path))
class Tests(unittest.TestCase):
    def publish(self,gh):
        with patch.object(m,'collect',return_value=({'dish_ko':'검증','dish_en':'Test'},{'video.mp4':b'test-media','metadata.json':b'[]'})),patch.object(m,'source_fingerprint',return_value='source'):
            return m.publish(11,gh=gh)
    def test_publish_only_after_all_assets_verified(self):
        gh=FakeGitHub();self.publish(gh)
        self.assertFalse(gh.record['draft']);self.assertIn('manifest.json',gh.assets);self.assertEqual(gh.actions[-1],('PATCH','/releases/1'))
        count=len(gh.assets);gh.actions=[];self.publish(gh)
        self.assertEqual(len(gh.assets),count);self.assertTrue(all(x[0]=='GET' for x in gh.actions))
    def test_corruption_keeps_release_draft(self):
        gh=FakeGitHub();gh.corrupt=True
        with self.assertRaisesRegex(RuntimeError,'verification failed'):self.publish(gh)
        self.assertTrue(gh.record['draft']);self.assertFalse(any(x[0]=='PATCH' for x in gh.actions))
    def test_published_assets_cannot_be_overwritten(self):
        gh=FakeGitHub();self.publish(gh);gh.assets['video.mp4']['digest']='sha256:'+'0'*64;gh.actions=[]
        with self.assertRaisesRegex(RuntimeError,'refusing overwrite'):self.publish(gh)
        self.assertFalse(any(x[0] in ('POST','PATCH','DELETE') for x in gh.actions))
if __name__=='__main__':unittest.main()
