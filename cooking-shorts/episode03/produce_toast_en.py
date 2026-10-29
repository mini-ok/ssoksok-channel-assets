"""English localization of the final approved toast renderer, preserving the health explanation."""
import ast,types,sys,json,functools,wave,re,difflib,subprocess,os
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parent
UI={
'심장':'Heart','심장 쉐프':'Chef Heart','여성 내레이터':'Narrator',
'쏙쏙 건강백과':'Tiny Body Co.','쏙쏙 건강요리':'Healthy Cooking','오늘의 요리사 : 심장 쉐프':'Today\'s cook: Chef Heart',
'사과 땅콩버터 토스트':'Apple Peanut Butter Toast','사과땅콩버터토스트_전체레시피.png':'ApplePeanutButterToast_recipe_EN.png','사과땅콩버터토스트_한글.srt':'ApplePeanutButterToast_EN.srt','쏙쏙건강요리_사과땅콩버터토스트_한글_v2.mp4':'TinyBodyCo_ApplePeanutButterToast_EN.mp4',
'심장이 고른 지방 바꾸기':'A Heart-Friendly Swap','재료는 딱 세 가지':'Just Three Ingredients','01  사과를 얇게 썰어요':'01  Slice the Apple','02  버터 대신 땅콩버터':'02  Swap Your Spread','03  사과를 차곡차곡':'03  Add the Apple',
'왜 심장이 골랐을까요?':'Why Did Heart Choose This?','지방의 종류를 바꿔요':'Choose Unsaturated Fats','더하기보다 바꿔 먹기':'Swap It. Don\'t Just Add It.','제 간식도 남겨주세요!':'Save Some for the Chef!','캡처해서 다음 간식에!':'Screenshot Your Next Snack!',
'1인 간식 / 약 3분':'1 snack serving / about 3 minutes','재료':'Ingredients','통밀빵 1장 · 사과 1/2개':'1 slice whole-wheat bread / 1/2 apple','땅콩버터 20g':'Peanut butter 20 g','땅콩 100% · 무가당 · 무염':'100% peanuts / no added sugar or salt','만드는 법':'Method',
'1  사과는 씻어 씨를 빼고 얇게 썰어요.':'1  Wash, core and thinly slice the apple.','2  빵에 땅콩버터를 고르게 발라요.':'2  Spread peanut butter over the bread.','3  사과를 차곡차곡 올리면 완성!':'3  Layer on the apple slices. Done!',
'버터 대신 바꿔 먹는 간식이에요.':'Enjoy this in place of buttered bread.',
'땅콩':'Peanuts','통밀빵':'Whole-wheat bread','사과':'Apple','땅콩버터':'Peanut butter','1장':'1 slice','1/2개':'1/2 apple','씻어서 씨를 빼요':'Wash and core first',
'출처 · 미국심장협회':'Source: American Heart Association','지방의 종류와 콜레스테롤':'Fats in Foods / Cholesterol','포화지방 대신 불포화지방':'Unsaturated instead of saturated fat','LDL 콜레스테롤 관리에 도움':'Helps manage LDL cholesterol','버터 대신 땅콩버터':'Peanut butter instead of butter','더 먹기보다 바꿔 먹는 선택':'Make a swap, not an extra serving',
'구독은 사원증 발급!':'Subscribe for your employee badge!','좋아요는 보너스!':'Likes are your bonus!'}
DIALOGUE={
'hook':"Peanut butter instead of butter! This toast is a little treat for your heart.",
'ingredients':"One slice of whole-wheat bread, half an apple, and twenty grams of peanut butter.",
'chop':"Wash and core the apple, then slice it thinly. Keep the peel on!",
'spread':"Choose one hundred percent peanuts, with no added sugar or salt. Spread it evenly!",
'top':"Layer on the apple slices. Crunchy toast, ready to go!",
'serve':"Still rich and nutty, even without butter! Here's why I picked this snack.",
'benefit':"Replacing saturated fat with unsaturated fat can help manage LDL, the bad cholesterol.",
'swap':"So swap butter for peanut butter! It's a replacement, not an extra serving. That's the heart-friendly choice.",
'joke':"Taking care of your heart is great, but please don't eat the chef's snack too!",
'end':"Subscribe for your employee badge! Likes are your bonus!"}
source=ROOT/'produce_toast.py';tree=ast.parse(source.read_text(encoding='utf-8'))
class Translate(ast.NodeTransformer):
 def visit_Constant(self,n):
  if isinstance(n.value,str) and n.value in UI:return ast.copy_location(ast.Constant(UI[n.value]),n)
  return n
m=types.ModuleType('toast_english');m.__file__=str(source)
exec(compile(Translate().visit(tree),str(source),'exec'),m.__dict__)
p=m.p;v=m.v;r=m.r
p.OUT=ROOT/'output_toast_en';p.AUDIO=ROOT/'audio_toast_en';p.OUT.mkdir(exist_ok=True);p.AUDIO.mkdir(exist_ok=True)
p.TARGET=p.OUT/'TinyBodyCo_ApplePeanutButterToast_EN.mp4'
v.OUT=p.OUT;v.AUDIO=p.AUDIO
p.ROWS=[(sid,title,DIALOGUE[sid],speaker,act) for sid,title,text,speaker,act in p.ROWS]
v.SPEAKER={'Chef Heart':('Chef Heart',0xF0A0A8),'Narrator':('Narrator',0x9ACDB4)}
v.KEYWORDS={'hook':{'instead'},'benefit':{'Replacing','saturated','unsaturated','LDL,'},'swap':{'replacement,','not','heart-friendly'}}
font=r.font
r.font=lambda size,style='jua':font(size,'en' if style in ('jua','en') else 'heavy')
r.p.FONTS.update(jua=str(p.SOURCE/'runtime/fonts/Geist-Bold.ttf'),black=str(p.SOURCE/'runtime/fonts/Geist-Black.ttf'))
label=r.label
def fit_label(im,text,xy,size=50,fill=v.INK,style='jua',anchor='mm',maxw=None):
 text=UI.get(text,text)
 if text=='Whole-wheat bread' and anchor=='lm':maxw=440
 if maxw is None:maxw=900 if anchor=='mm' else max(150,950-xy[0]) if anchor=='lm' else 850
 return label(im,text,xy,size,fill,style,anchor,maxw)
r.label=fit_label
paper=v.sty.paper_chip
@functools.lru_cache(maxsize=128)
def fit_chip(text,size,color,angle=0):
 maxw=470 if text in ['Tiny Body Co.','Healthy Cooking'] else 970
 while r.p.tw(text,size,'black')+130>maxw and size>20:size-=1
 return paper(text,size,color,angle)
v.sty.paper_chip=fit_chip

def norm(s):
 s=s.lower().replace('100%','one hundred percent').replace('100 percent','one hundred percent').replace('20','twenty')
 return re.sub('[^a-z0-9]','',s)
def audio():
 p.auth();os.environ['HF_HOME']=str(p.REPO.parent/'cooking_shorts_sample/models')
 from faster_whisper import WhisperModel
 from scipy.signal import resample_poly
 import requests
 model=WhisperModel('small',device='cpu',compute_type='int8',cpu_threads=3)
 original={x['id']:x for x in json.loads((ROOT/'audio_toast/manifest.json').read_text(encoding='utf-8'))}
 reports=[];rows=[]
 for sid,title,text,speaker,_ in p.ROWS:
  path=p.AUDIO/(sid+'.wav');voice='Despina' if speaker=='Narrator' else 'Zubenelgenubi'
  for attempt in range(3):
   if not path.exists() or attempt:
    inp={'text':text}
    if not attempt:inp['prompt']='Bright, cheerful cooking animation. Playful and lively, with clear natural delivery.'
    response=requests.post(v.channel_tts.G_URL,headers={'Authorization':'Bearer '+v.channel_tts.token(),'x-goog-user-project':v.channel_tts.PROJECT},json={'input':inp,'voice':{'languageCode':'en-US','name':voice,'modelName':v.channel_tts.MODEL},'audioConfig':{'audioEncoding':'LINEAR16','sampleRateHertz':24000}},timeout=120)
    if response.status_code!=200:raise RuntimeError('TTS HTTP '+str(response.status_code))
    x=v.channel_tts.squeeze_gaps(v.channel_tts.trim_edges(v.channel_tts.decode(response)))
    v.speech.tts.save_wav(str(path),v.speech.speed(x,1.3))
   with wave.open(str(path)) as f:x=np.frombuffer(f.readframes(f.getnframes()),np.int16).astype(np.float32)/32768
   seg,_=model.transcribe(resample_poly(x,2,3),language='en',beam_size=5,condition_on_previous_text=False)
   heard=' '.join(s.text for s in seg).strip();score=difflib.SequenceMatcher(None,norm(text),norm(heard)).ratio()
   print(sid,round(score,3),heard,flush=True)
   if score>.88:break
   if attempt==2:raise RuntimeError('Speech QA failed: '+sid)
  reports.append(dict(id=sid,expected=text,heard=heard,similarity=score))
  rows.append(dict(id=sid,title=title,text=text,speaker=speaker,voice=voice,speed=1.3,speech_duration=len(x)/24000,duration=10 if sid=='end' else round(max(original[sid]['duration'],len(x)/24000+1.4),3)))
 (p.AUDIO/'manifest.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2),encoding='utf-8')
 (p.OUT/'speech_qa.json').write_text(json.dumps(reports,indent=2),encoding='utf-8')

def check():
 os.environ['HF_HOME']=str(p.REPO.parent/'cooking_shorts_sample/models')
 from faster_whisper import WhisperModel
 model=WhisperModel('small',device='cpu',compute_type='int8',cpu_threads=3)
 raw=subprocess.run([r.FF,'-v','error','-i',str(p.TARGET),'-vn','-ac','1','-ar','16000','-f','f32le','pipe:1'],capture_output=True,check=True).stdout
 samples=np.frombuffer(raw,np.float32);clock=0;reports=[]
 for row in p.rows():
  seg,_=model.transcribe(samples[int(clock*16000):int((clock+row['duration'])*16000)],language='en',beam_size=5,condition_on_previous_text=False)
  heard=' '.join(s.text for s in seg).strip();score=difflib.SequenceMatcher(None,norm(row['text']),norm(heard)).ratio()
  print(row['id'],round(score,3),heard,flush=True);assert score>.86
  reports.append(dict(id=row['id'],expected=row['text'],heard=heard,similarity=score));clock+=row['duration']
 (p.OUT/'encoded_speech_qa.json').write_text(json.dumps(reports,indent=2),encoding='utf-8')

if __name__=='__main__':
 ids=[row[0] for row in p.ROWS]
 assert max(ids.index(s) for s in m.PLAN['cooking_scene_ids'])<min(ids.index(s) for s in m.PLAN['health_narration_scene_ids'])
 assert all(p.ROWS[ids.index(s)][3]=='Narrator' for s in ('benefit','swap'))
 assert 'Replacing saturated fat with unsaturated fat' in DIALOGUE['benefit'] and 'replacement, not an extra serving' in DIALOGUE['swap']
 cmd=sys.argv[1]
 if cmd in ('audio','check'):globals()[cmd]()
 else:getattr(p,cmd)()
