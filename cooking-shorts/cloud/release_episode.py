"""Publish verified bilingual raw assets as one GitHub Release per episode. No ZIP."""
import argparse,hashlib,json,mimetypes,os,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from github_client import GitHub
SOURCE=Path(__file__).resolve().parents[1]

def digest(value):
    h=hashlib.sha256()
    if isinstance(value,Path):
        with value.open('rb') as f:
            for chunk in iter(lambda:f.read(1024*1024),b''):h.update(chunk)
    else:h.update(value)
    return h.hexdigest()
def encoded(x):return (json.dumps(x,ensure_ascii=False,indent=2)+'\n').encode()
def source_fingerprint(num):
    root=SOURCE/f'episode{num:02}';c=json.loads((root/'production.json').read_text(encoding='utf-8'));p=json.loads((root/'plan.json').read_text(encoding='utf-8'))
    parts=[encoded(c),encoded({k:p.get(k) for k in ['health_focus','evidence','nutrition_box']})]
    if (root/'visuals.py').exists():parts.append((root/'visuals.py').read_bytes())
    return hashlib.sha256(b'\0'.join(parts)).hexdigest()
def collect(num,strict=True):
    root=SOURCE/f'episode{num:02}';c=json.loads((root/'production.json').read_text(encoding='utf-8'));plan=json.loads((root/'plan.json').read_text(encoding='utf-8'));assets={};items=[];reports=[]
    for lang in ['ko','en']:
        out=root/('output' if lang=='ko' else 'output_en');report=json.loads((out/'verification.json').read_text(encoding='utf-8'));qa=json.loads((out/'encoded_speech_qa.json').read_text(encoding='utf-8'));rows=json.loads((root/('audio' if lang=='ko' else 'audio_en')/'manifest.json').read_text(encoding='utf-8'))
        assert report['full_decode']=='passed' and report['different_music_verified']=='passed' and report['language']==lang
        assert len(qa)==len(rows)==len(c['scenes'])==10 and all(x['similarity']>.84 for x in qa)
        assert [x['expected'] for x in qa]==[x['text_'+lang] for x in c['scenes']]==[x['text'] for x in rows]
        video=out/report['file'];assert digest(video)==report['sha256']
        if strict:
            proof=json.loads((out/'speech_provenance.json').read_text(encoding='utf-8'));assert proof['video_sha256']==report['sha256'] and proof['all_passed']
        slug=c['slug'];name=f'{slug}_{lang.upper()}.mp4';assets[name]=video
        for filename in [f'{slug}_{lang.upper()}.srt',f'{slug}_recipe_{lang.upper()}.png']:assets[filename]=out/filename;assert assets[filename].is_file()
        title=c.get('upload_title_'+lang,plan.get('upload_title_ko') if lang=='ko' else None) or f"{c['chef_'+lang]}: {c['dish_'+lang]} #Shorts"
        description=c['time_'+lang]+'\n'+'\n'.join(c['recipe_'+lang])+'\n\n'+(' '.join(x['text_'+lang] for x in c['scenes'] if x['id'] in ('benefit','context')))+'\n\n'
        description+='\n'.join(' / '.join(lines) for lines in c.get('nutrition_'+lang,[]))+'\n\nSources:\n'+plan['evidence'][0]['url']+'\n'+'\n'.join(plan['nutrition_box']['source_urls'])+'\n\n#Shorts #HealthyCooking'
        assert len(title)<=100 and len(description)<=5000
        items.append(dict(language=lang,channel='@ssoksok-health' if lang=='ko' else '@tinybodyco',file=name,title=title,description=description,tags=[c['dish_'+lang],'Healthy Cooking','Shorts'],playlist_title='쏙쏙 건강요리 | 건강요리 숏츠' if lang=='ko' else 'Healthy Cooking Shorts | Tiny Body Co.',playlist_description='몸속 직원들의 건강요리 숏츠' if lang=='ko' else 'Healthy cooking with the organ chefs.',sha256=report['sha256']))
        reports.append(dict(language=lang,video=report,final_speech=qa))
    assets['metadata.json']=encoded(items);assets['verification.json']=encoded(reports);assets['nutrition_verification.json']=root/'nutrition_verification.json'
    upload=(SOURCE/'episode03/upload_template.py').read_text(encoding='utf-8').replace("record.update(done=True,privacy=check['status']['privacyStatus'],playlist_url=", "if check['status']['privacyStatus']!='public':raise RuntimeError('Video is not public; check Studio.')\n        record.update(done=True,privacy=check['status']['privacyStatus'],playlist_url=")
    compile(upload,'upload.py','exec');assets['upload.py']=upload.encode()
    assets['README.md']=(f"# Episode {num}: {c['dish_en']}\n\nRaw bilingual assets; no ZIP. Download all listed assets into an ephemeral CLOUD folder. Verify manifest.json hashes before use. Run python upload.py in the existing authorized cloud YouTube environment. Reuse the language-specific cooking playlist. Never disclose credentials.\n\nYouTube upload has NOT been executed by this production workflow.\n").encode()
    for name,value in assets.items():assert '/' not in name and '\\' not in name and (not isinstance(value,Path) or value.is_file())
    return c,assets
def remote_digest(gh,asset):
    if asset.get('digest','').startswith('sha256:'):return asset['digest'][7:]
    r=gh.request('GET',asset['url'],headers={'Accept':'application/octet-stream'},stream=True)
    if r.status_code!=200:raise RuntimeError('Cannot verify uploaded release asset')
    h=hashlib.sha256()
    for block in r.iter_content(1024*1024):h.update(block)
    return h.hexdigest()
def publish(num,tag=None,test=False,gh=None):
    gh=gh or GitHub();c,assets=collect(num);tag=tag or f'cooking-episode-{num:04}'
    entries={name:dict(sha256=digest(value),bytes=value.stat().st_size if isinstance(value,Path) else len(value),url=f'https://github.com/{gh.repo}/releases/download/{tag}/{name}') for name,value in assets.items()}
    manifest=dict(schema=1,episode=num,source_fingerprint=source_fingerprint(num),test_run=test,upload_ready=not test,assets=entries)
    assets['manifest.json']=encoded(manifest)
    release=gh.release(tag)
    if release is None:
        r=gh.request('POST','/releases',json=dict(tag_name=tag,target_commitish=os.environ.get('GITHUB_SHA','main'),name=f"{num}편 {c['dish_ko']} | {c['dish_en']}",draft=True,prerelease=test,body='Verified bilingual cooking videos and raw upload assets. No ZIP. YouTube upload is a separate job.'))
        if r.status_code!=201:raise RuntimeError('Could not create draft release')
        release=r.json()
    rid=release['id'];remote={};page=1
    while True:
        rows=gh.request('GET',f'/releases/{rid}/assets',params={'per_page':100,'page':page}).json()
        remote.update({a['name']:a for a in rows})
        if len(rows)<100:break
        page+=1
    for name,value in assets.items():
        sha=digest(value)
        if name in remote:
            if remote_digest(gh,remote[name])==sha:continue
            if not release['draft']:raise RuntimeError('Published release differs; refusing overwrite: '+name)
            gh.request('DELETE',f"/releases/assets/{remote[name]['id']}")
        if not release['draft']:raise RuntimeError('Published release is incomplete; refusing mutation')
        kwargs=dict(params={'name':name},headers={'Content-Type':mimetypes.guess_type(name)[0] or 'application/octet-stream'})
        url=release['upload_url'].split('{')[0]
        if isinstance(value,Path):
            with value.open('rb') as f:r=gh.request('POST',url,data=f,**kwargs)
        else:r=gh.request('POST',url,data=value,**kwargs)
        if r.status_code!=201 or remote_digest(gh,r.json())!=sha:raise RuntimeError('Release asset verification failed: '+name)
    if release['draft']:
        r=gh.request('PATCH',f'/releases/{rid}',json={'draft':False})
        if r.status_code!=200:raise RuntimeError('Could not publish verified release')
        release=r.json()
    print('VERIFIED RELEASE',release['html_url'],flush=True);return release['html_url']
if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('--episode',type=int,required=True);a.add_argument('--tag');a.add_argument('--test',action='store_true');a.add_argument('--dry-run',action='store_true');args=a.parse_args()
    if args.dry_run:
        c,assets=collect(args.episode,strict=False);print(json.dumps(dict(episode=args.episode,assets=list(assets),creates_zip=False,local_media_written=False),indent=2))
    else:publish(args.episode,args.tag,args.test)
