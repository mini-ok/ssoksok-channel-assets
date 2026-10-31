"""Package approved episodes 07/08 into separate bilingual upload folders and a combined ZIP."""
import json,hashlib,zipfile,shutil
from pathlib import Path
SOURCE=Path(__file__).resolve().parent;WORK=SOURCE.parent.parent
uploader=(SOURCE/'episode03/upload_template.py').read_text(encoding='utf-8')
uploader=uploader.replace("record.update(done=True,privacy=check['status']['privacyStatus'],playlist_url=", "if check['status']['privacyStatus']!='public':raise RuntimeError('Video is not public; check Studio before marking complete.')\n        record.update(done=True,privacy=check['status']['privacyStatus'],playlist_url=")
compile(uploader,'upload.py','exec');bundles=[]
for num in [7,8]:
 root=SOURCE/f'episode{num:02}';c=json.loads((root/'production.json').read_text(encoding='utf-8'));plan=json.loads((root/'plan.json').read_text(encoding='utf-8'))
 dest=WORK/f"{num}편_{c['dish_ko'].replace(' ','')}_업로드용";dest.mkdir(exist_ok=True)
 items=[];reports=[];names=['metadata.json','verification.json','nutrition_verification.json','upload.py','README.md']
 shutil.copy2(root/'nutrition_verification.json',dest/'nutrition_verification.json')
 for lang in ['ko','en']:
  out=root/('output' if lang=='ko' else 'output_en');report=json.loads((out/'verification.json').read_text(encoding='utf-8'));speech=json.loads((out/'encoded_speech_qa.json').read_text(encoding='utf-8'))
  assert report['full_decode']=='passed' and report['different_music_verified']=='passed' and report['language']==lang
  assert len(speech)==10 and all(x['similarity']>.84 for x in speech)
  video=out/report['file'];assert hashlib.sha256(video.read_bytes()).hexdigest()==report['sha256']
  prefix=c['slug'];target=f'{prefix}_{lang.upper()}.mp4';shutil.copy2(video,dest/target)
  for suffix in ['.srt','_recipe.png']:
   source_name=f'{prefix}_{lang.upper()}.srt' if suffix=='.srt' else f'{prefix}_recipe_{lang.upper()}.png'
   shutil.copy2(out/source_name,dest/source_name);names.append(source_name)
  if lang=='ko':
   title=plan.get('upload_title_ko',f"{c['chef_ko']}의 {c['dish_ko']} #Shorts")
   description=f"{c['chef_ko']}가 만드는 {c['dish_ko']}!\n\n{c['time_ko']}\n"+'\n'.join(c['recipe_ko'])+'\n\n건강 포인트: '+plan['health_focus']+'.\n'+plan['nutrition_box']['display']+'\n기준: '+plan['nutrition_box']['basis']+'\n재료 기준 추정치이며 제품·어종·조리에 따라 달라집니다.\n'
  else:
   title=("Chef Brain's Salmon and Pepper Bake #Shorts" if num==7 else "So Easy! Strawberry Yogurt Bark | Chef Bone #Shorts")
   description=f"{c['chef_en']} makes {c['dish_en']}!\n\n{c['time_en']}\n"+'\n'.join(c['recipe_en'])+'\n\n'+('DHA is a component of brain cell membranes. Estimated DHA: about 1,000 mg in 150 g uncooked farmed Atlantic salmon. This is an ingredient estimate, not a measured cooked amount. Fish, feed and cooking affect amounts. No U.S. daily requirement is established for DHA alone.' if num==7 else 'Calcium helps build and maintain bones. Estimated calcium: about 380 mg in the full recipe (plain low-fat yogurt 200 g + strawberries 80 g); half is about 190 mg, or 19% of the U.S. RDA of 1,000 mg for adults 19–50. Yogurt products vary; use the label to recalculate.')+'\n'
  description+='\nSources:\n'+plan['evidence'][0]['url']+'\n'+'\n'.join(plan['nutrition_box']['source_urls'])+'\n\n'+('#쏙쏙건강요리 #간단요리 #Shorts' if lang=='ko' else '#HealthyCooking #EasyRecipes #TinyBodyCo #Shorts')
  item=dict(language=lang,channel='@ssoksok-health' if lang=='ko' else '@tinybodyco',file=target,title=title,description=description,tags=['건강요리',c['dish_ko'],'간단요리'] if lang=='ko' else ['healthy cooking',c['dish_en'],'easy recipes','Tiny Body Co'],playlist_title='쏙쏙 건강요리 | 건강요리 숏츠' if lang=='ko' else 'Healthy Cooking Shorts | Tiny Body Co.',playlist_description='몸속 직원들이 직접 만드는 간단한 건강요리 숏츠입니다.' if lang=='ko' else 'Simple everyday recipes cooked by the tiny organ coworkers inside your body.',sha256=report['sha256'])
  assert len(title)<=100 and len(description)<5000
  items.append(item);names.append(target);reports.append(dict(language=lang,video_verification=report,final_speech_verification=speech))
 (dest/'metadata.json').write_text(json.dumps(items,ensure_ascii=False,indent=2),encoding='utf-8');(dest/'verification.json').write_text(json.dumps(reports,ensure_ascii=False,indent=2),encoding='utf-8');(dest/'upload.py').write_text(uploader,encoding='utf-8')
 (dest/'README.md').write_text(f'''# {num}편 {c['dish_ko']} · 한글/영문 업로드용

기존 유튜브 인증이 있는 클라우드 환경에서 실행하는 묶음입니다. 영상 두 개, 자막 두 개, 전체 레시피 이미지 두 개, 업로드 제목·설명, 검증 결과와 스크립트를 포함합니다.

> metadata.json과 upload.py를 간단히 확인한 뒤 기존 인증 환경에서 `python upload.py`를 실행해 주세요. 한글은 @ssoksok-health, 영문은 @tinybodyco에 공개 업로드하고 기존 건강요리 숏츠 재생목록을 재사용하세요. 없을 때만 만드세요. 완료 후 두 영상과 재생목록의 링크, 실제 공개 상태를 알려주세요. 키·토큰은 출력하지 마세요.

Python과 requests가 필요합니다. 기존 환경 변수 YT_CLIENT_ID, YT_CLIENT_SECRET, YT_REFRESH_TOKEN_KO, YT_REFRESH_TOKEN_EN을 사용합니다. 인증 정보는 이 폴더에 포함하지 않았습니다.

모든 영상 해시와 인증 채널을 확인합니다. 언어+파일 해시로 upload_result.json에 기록해 다른 회차와 혼동하지 않으며 완료 영상은 재실행 시 건너뜁니다. creating 상태에서 중단됐으면 Studio에서 실제 업로드 여부를 확인한 뒤 정리하세요. 실제 공개 상태가 public이 아니면 완료로 처리하지 않습니다.

원래 장기 캐릭터와 목소리, 여성 건강 근거 설명·큰 출처·전체 레시피를 유지했습니다. 사용 음악: {c['music']} (직전 편과 다른 곡). 실제 주방 조리·맛 평가는 수행하지 않았습니다.

현재 업로드 실행 전입니다. 이 PC에서 실제 유튜브 업로드나 다른 AI로의 메시지 전송은 실행하지 않았습니다.
''',encoding='utf-8')
 zip_path=WORK/f"{c['dish_ko'].replace(' ','')}_한영_클라우드업로드묶음.zip"
 with zipfile.ZipFile(zip_path,'w',zipfile.ZIP_DEFLATED) as z:
  for name in names:z.write(dest/name,name)
 with zipfile.ZipFile(zip_path) as z:
  assert z.testzip() is None
  for item in items:assert hashlib.sha256(z.read(item['file'])).hexdigest()==item['sha256']
 bundles.append((dest,names));print('Verified:',zip_path,round(zip_path.stat().st_size/1024**2,1),'MB',flush=True)
combined=WORK/'7_8편_한영_클라우드업로드묶음.zip'
with zipfile.ZipFile(combined,'w',zipfile.ZIP_DEFLATED) as z:
 z.writestr('README.md','7편과 8편을 각각 별도 폴더에 묶었습니다. 기존 인증 클라우드에서 각 폴더의 README.md를 확인하고 upload.py를 실행하세요. 총 4개 영상(회차별 한글/영문)이며 실제 업로드는 아직 실행하지 않았습니다. 인증 정보는 포함하지 않습니다.')
 for dest,names in bundles:
  for name in names:z.write(dest/name,dest.name+'/'+name)
with zipfile.ZipFile(combined) as z:assert z.testzip() is None
print('Combined ZIP verified:',combined,round(combined.stat().st_size/1024**2,1),'MB',flush=True)
