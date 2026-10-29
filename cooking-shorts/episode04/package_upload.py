"""Assemble episode 04 KO/EN videos for the existing authenticated cloud uploader."""
from pathlib import Path
import json,shutil,hashlib,zipfile
ROOT=Path(__file__).resolve().parent;WORK=ROOT.parents[2]
DEST=WORK/'4편_브로콜리마늘볶음_업로드용';DEST.mkdir(exist_ok=True)
source='https://www.niddk.nih.gov/health-information/digestive-diseases/constipation/eating-diet-nutrition'
ko='장 쉐프가 만드는 브로콜리 마늘볶음! 해외에서도 쉽게 구할 수 있는 재료로 만드는 초록 반찬입니다.\n\n1인 곁들임 / 약 7분\n브로콜리 150g, 마늘 1쪽, 식용유 1작은술, 물 2큰술. 소금·후추는 선택.\n\n1. 브로콜리는 씻어 작은 송이로 나누고 줄기는 얇게 썰어요.\n2. 팬에 브로콜리와 물을 넣고 뚜껑을 덮어 중불로 약 3분 익혀요.\n3. 뚜껑을 열어 물기를 날리고 중약불로 낮춰요.\n4. 기름과 다진 마늘을 넣고 약 1분 볶아요. 줄기가 단단하면 조금 더 익혀요.\n\n냉동 제품도 가능하며 포장 가열 안내를 우선해 물과 시간을 조절합니다. 마늘은 생략 가능해요.\n브로콜리로 식이섬유를 보태고 충분한 수분도 함께 챙기는 습관을 소개합니다. 식이섬유는 조금씩 늘려요.\n출처: 미국 NIH 산하 NIDDK 식이섬유·수분과 배변 안내\n'+source+'\n\n#쏙쏙건강요리 #브로콜리마늘볶음 #간단요리 #Shorts'
en="Chef Gut's garlic broccoli stir-fry! A simple green side with everyday ingredients.\n\n1 side serving / about 7 minutes\nBroccoli 150 g, 1 garlic clove, oil 1 tsp, water 2 tbsp. Salt and pepper optional.\n\n1. Wash broccoli. Cut into florets and thinly slice the stalk.\n2. Put broccoli and water in a pan, cover, and cook on medium for about 3 minutes.\n3. Uncover, let water evaporate, and turn heat to medium-low.\n4. Add oil and minced garlic. Fry about 1 minute. Cook longer if stalks are still firm.\n\nFrozen broccoli works too. Follow package heating instructions and adjust water and time. Garlic is optional.\nBroccoli adds fiber. Fiber and enough fluids support softer stools and easier bowel movements. Increase fiber gradually and remember water.\nSource: NIH / NIDDK, Eating, Diet, & Nutrition for Constipation\n"+source+'\n\n#HealthyCooking #GarlicBroccoli #EasyRecipes #TinyBodyCo #Shorts'
items=[dict(language='ko',channel='@ssoksok-health',file='GarlicBroccoli_KO.mp4',title='장 쉐프의 초록 반찬! 브로콜리 마늘볶음 #Shorts',description=ko,tags=['건강요리','브로콜리마늘볶음','간단요리','쏙쏙건강백과'],playlist_title='쏙쏙 건강요리 | 건강요리 숏츠',playlist_description='몸속 직원들이 직접 만드는 간단한 건강요리 숏츠입니다.'),dict(language='en',channel='@tinybodyco',file='GarlicBroccoli_EN.mp4',title="Chef Gut's Garlic Broccoli Stir-Fry | Easy Veggie Side #Shorts",description=en,tags=['healthy cooking','garlic broccoli','easy recipes','Tiny Body Co'],playlist_title='Healthy Cooking Shorts | Tiny Body Co.',playlist_description='Simple everyday recipes cooked by the tiny organ coworkers inside your body.')]
reports=[];names=['metadata.json','verification.json','upload.py','README.md']
for item,folder in zip(items,['output','output_en']):
 report=json.loads((ROOT/folder/'verification.json').read_text(encoding='utf-8'))
 speech=json.loads((ROOT/folder/'encoded_speech_qa.json').read_text(encoding='utf-8'))
 assert report['full_decode']=='passed' and report['different_music_verified']=='passed'
 assert len(speech)==10 and all(x['similarity']>.85 for x in speech)
 video=ROOT/folder/report['file'];assert hashlib.sha256(video.read_bytes()).hexdigest()==report['sha256']
 item['sha256']=report['sha256'];shutil.copy2(video,DEST/item['file'])
 assert len(item['title'])<=100 and len(item['description'])<5000
 lang=item['language'].upper()
 srt='브로콜리마늘볶음_한글.srt' if lang=='KO' else 'GarlicBroccoli_EN.srt'
 card='브로콜리마늘볶음_전체레시피.png' if lang=='KO' else 'GarlicBroccoli_recipe_EN.png'
 shutil.copy2(ROOT/folder/srt,DEST/f'GarlicBroccoli_{lang}.srt')
 shutil.copy2(ROOT/folder/card,DEST/f'GarlicBroccoli_recipe_{lang}.png')
 names.extend([item['file'],f'GarlicBroccoli_{lang}.srt',f'GarlicBroccoli_recipe_{lang}.png'])
 reports.append(dict(language=item['language'],video_verification=report,final_speech_verification=speech))
(DEST/'metadata.json').write_text(json.dumps(items,ensure_ascii=False,indent=2),encoding='utf-8')
(DEST/'verification.json').write_text(json.dumps(reports,ensure_ascii=False,indent=2),encoding='utf-8')
uploader=(ROOT.parent/'episode03/upload_template.py').read_text(encoding='utf-8')
uploader=uploader.replace("record.update(done=True,privacy=check['status']['privacyStatus'],playlist_url=", "if check['status']['privacyStatus']!='public':raise RuntimeError('Video is not public; check Studio before marking complete.')\n        record.update(done=True,privacy=check['status']['privacyStatus'],playlist_url=")
compile(uploader,'upload.py','exec');(DEST/'upload.py').write_text(uploader,encoding='utf-8')
(DEST/'README.md').write_text('''# 4편 브로콜리 마늘볶음 · 한글/영문 클라우드 업로드용

기존 인증이 있는 클라우드 AI에 이 폴더 또는 ZIP과 아래 내용을 전달하세요.

> 별도 폴더에 풀고 metadata.json과 upload.py를 빠르게 확인한 뒤 기존 유튜브 인증 환경에서 `python upload.py`를 실행해 주세요. 한국어는 @ssoksok-health, 영어는 @tinybodyco에 각각 공개 업로드하고 기존 건강요리 숏츠 재생목록에 넣어 주세요. 같은 제목의 재생목록은 재사용하고 없을 때만 만드세요. 완료 후 두 영상·재생목록의 링크와 실제 공개 상태를 보고해 주세요. 키와 토큰은 출력하지 마세요.

기존 환경 변수 YT_CLIENT_ID, YT_CLIENT_SECRET, YT_REFRESH_TOKEN_KO, YT_REFRESH_TOKEN_EN을 사용합니다. Python과 requests가 필요합니다. 인증 파일과 토큰은 포함하지 않았습니다.

해시와 인증 채널을 확인한 뒤 업로드합니다. upload_result.json은 언어+파일 해시별 결과를 저장하여 다른 회차와 혼동하지 않으며 완료 영상은 재실행 시 건너뜁니다. creating 상태에서 중단됐다면 Studio에서 실제 업로드 여부를 먼저 확인하세요. 실제 공개 상태가 public이 아니면 완료로 처리하지 않습니다.

한글/영문 영상·자막·전체 레시피 이미지·업로드 제목과 설명·검증 결과가 포함되어 있습니다. 두 언어 모두 4편의 음악 Buoyant Kitchen Groove를 사용하며, 3편과 다른 음악입니다. 조리 뒤 여성 해설의 식이섬유·수분과 배변 건강 설명, 큰 NIH/NIDDK 출처 표기를 유지했습니다.

현재 이 묶음은 업로드 실행 전입니다. 다른 AI에게 직접 메시지를 보내거나 실제 유튜브 업로드를 실행하지 않았습니다.
''',encoding='utf-8')
zip_path=WORK/'브로콜리마늘볶음_한영_클라우드업로드묶음.zip'
with zipfile.ZipFile(zip_path,'w',zipfile.ZIP_DEFLATED) as z:
 for name in names:z.write(DEST/name,name)
with zipfile.ZipFile(zip_path) as z:
 assert z.testzip() is None and set(z.namelist())==set(names)
 for item in items:assert hashlib.sha256(z.read(item['file'])).hexdigest()==item['sha256']
print('Folder:',DEST);print('Verified ZIP:',zip_path,round(zip_path.stat().st_size/1024**2,1),'MB')
