"""Cloud-only rendering and raw Release delivery. No AI API or YouTube upload."""
import argparse,json,os,subprocess,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from github_client import GitHub
from release_episode import SOURCE,collect,publish,source_fingerprint

def ready_release(gh,num,tag):
    release=gh.release(tag)
    if release is None or release['draft']:return None
    assets=gh.request('GET',f"/releases/{release['id']}/assets",params={'per_page':100}).json()
    match=next((x for x in assets if x['name']=='manifest.json'),None)
    if not match:raise RuntimeError('Published release has no manifest')
    raw=gh.request('GET',match['url'],headers={'Accept':'application/octet-stream'})
    m=raw.json()
    if m.get('source_fingerprint')!=source_fingerprint(num):raise RuntimeError('Published release source differs; use a new version tag')
    if not m.get('upload_ready') and not m.get('test_run'):raise RuntimeError('Published release is not ready')
    return release['html_url']

def run(numbers,test=False):
    if os.environ.get('GITHUB_ACTIONS')!='true':raise RuntimeError('Cloud media production must run on GitHub Actions, not this PC')
    gh=GitHub();results=[]
    for num in numbers:
        tag=f'cooking-cloud-test-{os.environ["GITHUB_RUN_ID"]}-{num:04}' if test else f'cooking-episode-{num:04}'
        old=ready_release(gh,num,tag)
        if old:results.append(dict(episode=num,url=old,reused=True));continue
        for lang in ['ko','en']:
            try:
                collect(num)
                # collect checks BOTH languages, so an unfinished episode resumes below.
                break
            except (AssertionError,FileNotFoundError,KeyError):pass
            for command in ['audio','preview','render','verify','check']:
                print(f'EPISODE {num} {lang} {command}',flush=True)
                result=subprocess.run([sys.executable,str(SOURCE/'produce_episodes.py'),str(num),lang,command],cwd=SOURCE.parent)
                if result.returncode:raise RuntimeError(f'Episode {num} {lang} {command} failed; unpublished outputs are not upload-ready')
        collect(num)
        url=publish(num,tag,test,gh);results.append(dict(episode=num,url=url,reused=False))
    summary=Path(os.environ['RUNNER_TEMP'])/'cooking-results.json';summary.write_text(json.dumps(results,ensure_ascii=False,indent=2),encoding='utf-8')
    if os.environ.get('GITHUB_STEP_SUMMARY'):
        with open(os.environ['GITHUB_STEP_SUMMARY'],'a',encoding='utf-8') as f:
            f.write('## Verified cooking releases\n\n'+'\n'.join(f"- Episode {r['episode']}: {r['url']}" for r in results)+'\n\nNo ZIP or YouTube upload was executed.\n')
    print(json.dumps(results,ensure_ascii=False),flush=True)
if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('--episodes',required=True);a.add_argument('--test',action='store_true');args=a.parse_args()
    nums=[int(x.strip()) for x in args.episodes.split(',')];assert 1<=len(nums)<=2 and len(set(nums))==len(nums) and all(x>=5 for x in nums)
    run(nums,args.test)
