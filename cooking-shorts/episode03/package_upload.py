"""Build a credential-free, checksum-verified KO/EN handoff for the existing cloud uploader."""
from pathlib import Path
import json,shutil,hashlib,zipfile
ROOT=Path(__file__).resolve().parent;WORK=ROOT.parents[2]
DEST=WORK/'toast_upload_handoff';DEST.mkdir(exist_ok=True)
SOURCE='https://www.heart.org/en/healthy-living/healthy-eating/eat-smart/fats/fats-in-foods'
ko='심장 쉐프가 버터 대신 땅콩버터를 선택한 이유!\n\n1인 간식 / 약 3분\n통밀빵 1장, 사과 1/2개, 땅콩 100% 무가당·무염 땅콩버터 20g.\n\n1. 사과는 씻어 씨를 빼고 얇게 썰어요.\n2. 빵에 땅콩버터를 고르게 발라요.\n3. 사과를 차곡차곡 올리면 완성! 빵은 취향껏 미리 구워도 좋아요.\n\n포화지방을 불포화지방으로 대체하는 식습관은 LDL 콜레스테롤 관리에 도움이 될 수 있어요. 버터에 더해 먹는 것이 아니라 대신 먹는 선택입니다. 이 토스트 한 번의 수치 개선이나 치료 효과를 보장하는 뜻은 아닙니다.\n출처: 미국심장협회 Fats in Foods\n'+SOURCE+'\n\n#쏙쏙건강요리 #사과땅콩버터토스트 #간단요리 #Shorts'
en="Why Chef Heart swaps butter for peanut butter!\n\n1 snack serving / about 3 minutes\n1 slice whole-wheat bread, 1/2 apple, 20 g peanut butter made from 100% peanuts, with no added sugar or salt.\n\n1. Wash and core the apple, then slice it thinly.\n2. Spread peanut butter evenly over the bread.\n3. Layer on the apple slices. Toast the bread first if you prefer.\n\nReplacing saturated fat with unsaturated fat can help manage LDL cholesterol. This is a replacement for butter, not an extra serving on top of it. No claim that one serving of this toast changes cholesterol or treats disease.\nSource: American Heart Association, Fats in Foods\n"+SOURCE+'\n\n#HealthyCooking #ApplePeanutButterToast #EasyRecipes #TinyBodyCo #Shorts'
items=[dict(language='ko',channel='@ssoksok-health',file='ApplePeanutButterToast_KO.mp4',title='이건 너무 쉽다~ 사과 땅콩버터 토스트 | 심장 쉐프 #Shorts',description=ko,tags=['건강요리','사과땅콩버터토스트','간단요리','쏙쏙건강백과'],playlist_title='쏙쏙 건강요리 | 건강요리 숏츠',playlist_description='몸속 직원들이 직접 만드는 간단한 건강요리 숏츠입니다.'),
dict(language='en',channel='@tinybodyco',file='ApplePeanutButterToast_EN.mp4',title="This Is Too Easy! Apple Peanut Butter Toast | Chef Heart #Shorts",description=en,tags=['healthy cooking','apple peanut butter toast','easy recipes','Tiny Body Co'],playlist_title='Healthy Cooking Shorts | Tiny Body Co.',playlist_description='Simple everyday recipes cooked by the tiny organ coworkers inside your body.')]
reports=[]
for item,folder in zip(items,['output_toast','output_toast_en']):
 report=json.loads((ROOT/folder/'verification.json').read_text(encoding='utf-8'))
 speech=json.loads((ROOT/folder/'encoded_speech_qa.json').read_text(encoding='utf-8'))
 assert len(speech)==10 and all(x['similarity']>.85 for x in speech)
 path=ROOT/folder/report['file'];assert hashlib.sha256(path.read_bytes()).hexdigest()==report['sha256']
 shutil.copy2(path,DEST/item['file']);item['sha256']=report['sha256']
 assert len(item['title'])<=100 and len(item['description'])<5000
 srt='사과땅콩버터토스트_한글.srt' if item['language']=='ko' else 'ApplePeanutButterToast_EN.srt'
 card='사과땅콩버터토스트_전체레시피.png' if item['language']=='ko' else 'ApplePeanutButterToast_recipe_EN.png'
 shutil.copy2(ROOT/folder/srt,DEST/('ApplePeanutButterToast_'+item['language'].upper()+'.srt'))
 shutil.copy2(ROOT/folder/card,DEST/('ApplePeanutButterToast_recipe_'+item['language'].upper()+'.png'))
 reports.append(dict(language=item['language'],video_verification=report,final_speech_verification=speech))
(DEST/'metadata.json').write_text(json.dumps(items,ensure_ascii=False,indent=2),encoding='utf-8')
(DEST/'verification.json').write_text(json.dumps(reports,ensure_ascii=False,indent=2),encoding='utf-8')
uploader=(ROOT/'upload_template.py').read_text(encoding='utf-8')
uploader=uploader.replace("record.update(done=True,privacy=check['status']['privacyStatus'],playlist_url=", "if check['status']['privacyStatus']!='public':raise RuntimeError('Video is not public; check Studio before marking complete.')\n        record.update(done=True,privacy=check['status']['privacyStatus'],playlist_url=")
compile(uploader,'upload.py','exec');(DEST/'upload.py').write_text(uploader,encoding='utf-8')
(DEST/'README.md').write_text('''# 사과 땅콩버터 토스트 · 한글/영문 클라우드 업로드 묶음

기존 인증이 있는 클라우드 AI에 아래 내용과 이 ZIP을 전달하세요.

> ZIP을 별도 폴더에 풀고 metadata.json과 upload.py를 간단히 확인한 뒤, 기존 유튜브 인증 환경에서 `python upload.py`를 실행해 주세요. 한국어 영상은 @ssoksok-health, 영어 영상은 @tinybodyco에 각각 공개 업로드하세요. 기존 건강요리 숏츠 재생목록을 재사용하고, 없을 때만 만드세요. 완료 후 영상 두 개와 재생목록 링크, 실제 공개 상태를 보고해 주세요. 키·토큰은 출력하지 마세요.

기존 환경 변수 YT_CLIENT_ID, YT_CLIENT_SECRET, YT_REFRESH_TOKEN_KO, YT_REFRESH_TOKEN_EN을 사용합니다. Python과 requests가 필요합니다. 인증 파일·토큰은 이 묶음에 넣지 않았습니다.

파일 SHA-256 → 인증 채널 확인 → 기존 재생목록 찾기 → 공개 업로드 → 재생목록 추가 → 실제 채널·공개 상태 확인 순서입니다. upload_result.json은 언어+영상 해시별로 저장하므로 이전 영상의 결과와 혼동하지 않습니다. 재실행 시 완료 영상은 건너뜁니다. creating 상태에서 중단되면 Studio에서 실제 업로드 여부를 확인한 뒤 정리하세요.

한글/영문 MP4, 자막, 캡처용 레시피, 업로드 문구, 검증 결과를 포함합니다. 영어도 조리 후 여성 건강 근거 설명과 큰 출처 표기를 유지했습니다. 출처는 미국심장협회 Fats in Foods이며 포화지방을 불포화지방으로 대체하는 식습관에 관한 설명입니다.

이 묶음은 업로드 실행 전입니다. 다른 AI에게 직접 메시지를 보내거나 유튜브 업로드를 실행하지 않았습니다.
''',encoding='utf-8')
zip_path=WORK/'사과땅콩버터토스트_한영_클라우드업로드묶음.zip'
names=['metadata.json','verification.json','upload.py','README.md']
for lang in ['KO','EN']:
 names.extend(['ApplePeanutButterToast_'+lang+'.mp4','ApplePeanutButterToast_'+lang+'.srt','ApplePeanutButterToast_recipe_'+lang+'.png'])
with zipfile.ZipFile(zip_path,'w',zipfile.ZIP_DEFLATED) as z:
 for name in names:z.write(DEST/name,name)
with zipfile.ZipFile(zip_path) as z:
 assert z.testzip() is None and set(z.namelist())==set(names)
 for item in items:assert hashlib.sha256(z.read(item['file'])).hexdigest()==item['sha256']
print('Verified ZIP:',zip_path,round(zip_path.stat().st_size/1024**2,1),'MB')
