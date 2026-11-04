"""GitHub API client. Never logs credentials or response bodies on failure."""
import os,time
import requests

class GitHub:
    def __init__(self,repo=None,token=None):
        self.repo=repo or os.environ.get('GITHUB_REPOSITORY','mini-ok/ssoksok-channel-assets')
        token=token or os.environ.get('GITHUB_TOKEN')
        if not token:raise RuntimeError('GITHUB_TOKEN is required')
        self.base='https://api.github.com/repos/'+self.repo
        self.session=requests.Session();self.session.headers.update(Authorization='Bearer '+token,Accept='application/vnd.github+json',**{'X-GitHub-Api-Version':'2022-11-28'})
    def request(self,method,path,**kwargs):
        url=path if path.startswith('https://') else self.base+path
        if not url.startswith(('https://api.github.com/','https://uploads.github.com/')):raise ValueError('Unexpected GitHub host')
        body=kwargs.get('data');position=body.tell() if hasattr(body,'tell') else None
        for attempt in range(4):
            if position is not None:body.seek(position)
            r=self.session.request(method,url,timeout=180,**kwargs)
            if r.status_code not in (429,500,502,503,504):break
            time.sleep(min(30,5*(attempt+1)))
        if r.status_code>=400 and r.status_code!=404:raise RuntimeError(f'GitHub {method} HTTP {r.status_code}')
        return r
    def release(self,tag):
        r=self.request('GET','/releases/tags/'+tag)
        return None if r.status_code==404 else r.json()
