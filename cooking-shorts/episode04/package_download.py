"""Package the verified Korean episode 04 for download; no upload or credentials."""
from pathlib import Path
import json,hashlib,zipfile
ROOT=Path(__file__).resolve().parent;OUT=ROOT/'output';WORK=ROOT.parents[2]
report=json.loads((OUT/'verification.json').read_text(encoding='utf-8'))
speech=json.loads((OUT/'encoded_speech_qa.json').read_text(encoding='utf-8'))
assert report['full_decode']=='passed' and report['different_music_verified']=='passed'
assert len(speech)==10 and all(x['similarity']>.85 for x in speech)
video=OUT/report['file'];assert hashlib.sha256(video.read_bytes()).hexdigest()==report['sha256']
path=WORK/'쏙쏙건강요리_4편_한글_다운로드묶음.zip'
files=[report['file'],'브로콜리마늘볶음_한글.srt','브로콜리마늘볶음_전체레시피.png','verification.json','encoded_speech_qa.json']
with zipfile.ZipFile(path,'w',zipfile.ZIP_DEFLATED) as z:
 for name in files:z.write(OUT/name,name)
 z.write(ROOT/'README.md','README.md')
with zipfile.ZipFile(path) as z:
 assert z.testzip() is None
 assert hashlib.sha256(z.read(report['file'])).hexdigest()==report['sha256']
print('Download ZIP verified:',path,round(path.stat().st_size/1024**2,1),'MB')
