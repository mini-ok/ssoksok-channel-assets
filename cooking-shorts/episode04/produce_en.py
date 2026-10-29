"""English localization of approved episode 04, preserving gut-health narration and music."""
import ast,types,sys,json,functools,wave,re,difflib,subprocess,os,inspect
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parent
UI={
 "장": "Gut",
 "장 쉐프": "Chef Gut",
 "여성 내레이터": "Narrator",
 "쏙쏙 건강백과": "Tiny Body Co.",
 "쏙쏙 건강요리": "Healthy Cooking",
 "오늘의 요리사 : 장 쉐프": "Today's cook: Chef Gut",
 "브로콜리 마늘볶음": "Garlic Broccoli Stir-Fry",
 "브로콜리마늘볶음_전체레시피.png": "GarlicBroccoli_recipe_EN.png",
 "브로콜리마늘볶음_한글.srt": "GarlicBroccoli_EN.srt",
 "쏙쏙건강요리_브로콜리마늘볶음_한글_v1.mp4": "TinyBodyCo_GarlicBroccoli_EN.mp4",
 "장이 고른 초록 반찬": "Greens Chosen by Gut",
 "해외에서도 쉬운 재료": "Simple, Everyday Ingredients",
 "01  줄기도 얇게 썰어요": "01  Slice the Stalk Too",
 "02  물 넣고 뚜껑 덮기": "02  Add Water and Cover",
 "03  중약불로 마늘과 볶기": "03  Gently Fry with Garlic",
 "줄기가 익으면 완성!": "Tender Stalks? Ready!",
 "왜 장 쉐프가 골랐을까요?": "Why Did Gut Choose This?",
 "조금씩 꾸준히 · 물도 함께": "Build Up Slowly. Drink Water.",
 "물컵도 챙겨주세요!": "Save Me Some Water!",
 "캡처해서 다음 반찬으로!": "Screenshot Your Next Side!",
 "1인 곁들임 / 약 7분": "1 side serving / about 7 minutes",
 "재료": "Ingredients",
 "브로콜리 150g · 마늘 1쪽": "Broccoli 150 g / 1 garlic clove",
 "식용유 1작은술 · 물 2큰술": "Oil 1 tsp / water 2 tbsp",
 "소금·후추는 선택": "Salt and pepper optional",
 "만드는 법": "Method",
 "1  작은 송이로 나누고 줄기는 얇게 썰어요.": "1  Cut into florets; thinly slice the stalk.",
 "2  물 넣고 뚜껑 덮어 중불로 약 3분.": "2  Add water. Cover on medium, about 3 min.",
 "3  물기를 날리고 중약불로 낮춰요.": "3  Let water evaporate. Turn heat down.",
 "4  기름·다진 마늘 넣고 약 1분 볶아요.": "4  Add oil and minced garlic. Fry about 1 min.",
 "줄기가 단단하면 조금 더 익혀요.": "Cook longer if the stalks are still firm.",
 "냉동 제품은 포장 가열 안내를 따라요.": "For frozen broccoli, follow package directions.",
 "출처 · 미국 NIH / NIDDK": "Source: NIH / NIDDK",
 "식이섬유·수분과 배변 안내": "Fiber, Fluids and Bowel Health",
 "브로콜리": "Broccoli",
 "마늘": "Garlic",
 "식용유": "Oil",
 "물": "Water",
 "1쪽": "1 clove",
 "1작은술": "1 tsp",
 "2큰술": "2 tbsp",
 "생 / 냉동 브로콜리 모두 가능": "Fresh or frozen broccoli both work",
 "식이섬유 + 충분한 수분": "Fiber + Enough Fluids",
 "조금씩 늘리고 · 물도 함께": "Build Up Slowly + Drink Water",
 "원활한 배변을 돕는 습관": "Habits for Easier Bowel Movements",
 "한 번에 듬뿍보다 꾸준히": "A Little More, Little by Little",
 "중불 / 약 3분": "Medium heat / about 3 min",
 "중약불 / 마늘 타지 않게": "Medium-low / do not burn garlic",
 "줄기가 단단하면 조금 더": "Firm stalks? Cook a little longer",
 "구독은 사원증 발급!": "Subscribe for your employee badge!",
 "좋아요는 보너스!": "Likes are your bonus!"
}
DIALOGUE={
 "hook": "Today, a green side dish for your gut! I'm cooking garlic broccoli!",
 "ingredients": "One hundred fifty grams of broccoli, one garlic clove, one teaspoon of oil, and two tablespoons of water.",
 "chop": "Wash and cut into bite-sized florets. Thinly slice the stalk, so you can eat that too!",
 "steam": "Put broccoli and water in the pan. Cover and cook over medium heat for about three minutes.",
 "fry": "Let the water evaporate, then turn the heat to medium-low. Add oil and minced garlic. Fry for about one minute.",
 "serve": "Once the stalks are tender, it's ready! Season lightly, just how you like it.",
 "benefit": "Broccoli adds fiber. Fiber and enough fluids help keep stools soft and easier to pass.",
 "habit": "Build up your fiber slowly, rather than all at once! And remember water. That's Chef Gut's tip!",
 "joke": "Don't just save my vegetables. Save me a glass of water too! I'm thirsty!",
 "end": "Subscribe for your employee badge! Likes are your bonus!"
}
source=ROOT/'produce.py';tree=ast.parse(source.read_text(encoding='utf-8'))
class Translate(ast.NodeTransformer):
 def visit_Constant(self,n):
  if isinstance(n.value,str) and n.value in UI:return ast.copy_location(ast.Constant(UI[n.value]),n)
  return n
m=types.ModuleType('broccoli_english');m.__file__=str(source)
exec(compile(Translate().visit(tree),str(source),'exec'),m.__dict__)
p=m.p;v=m.v;r=m.r
p.OUT=ROOT/'output_en';p.AUDIO=ROOT/'audio_en';p.OUT.mkdir(exist_ok=True);p.AUDIO.mkdir(exist_ok=True)
p.TARGET=p.OUT/'TinyBodyCo_GarlicBroccoli_EN.mp4'
v.OUT=p.OUT;v.AUDIO=p.AUDIO
p.ROWS=[(sid,title,DIALOGUE[sid],speaker,act) for sid,title,text,speaker,act in p.ROWS]
v.SPEAKER={'Chef Gut':('Chef Gut',0xA3D9C3),'Narrator':('Narrator',0x9ACDB4)}
v.KEYWORDS={'benefit':{'fiber.','fluids','soft'},'habit':{'slowly,','water.'},'steam':{'three'},'fry':{'medium-low.'}}
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

original_split=v.split_lines
def readable_lines(text,size,d):
 if len(text)<=105:return original_split(text,size,d)
 if size>48:return None
 words=text.split();best=None
 for i in range(1,len(words)-1):
  for j in range(i+1,len(words)):
   parts=[words[:i],words[i:j],words[j:]]
   widths=[d.textlength(' '.join(part),font=r.font(size)) for part in parts]
   if max(widths)<=900:
    cost=max(widths)-min(widths)
    if best is None or cost<best[0]:best=(cost,parts)
 return best[1] if best else None
v.split_lines=readable_lines
caption_source=inspect.getsource(v.wrapped_caption.__wrapped__)
caption_source=caption_source.replace('y=1665+(li-(len(lines)-1)/2)*86','y=1663+(li-(len(lines)-1)/2)*(63 if len(lines)==3 else 86)')
caption_source=caption_source.replace('y-39,x+wd+8,y+41','y-(29 if len(lines)==3 else 39),x+wd+8,y+(30 if len(lines)==3 else 41)')
exec(caption_source,v.__dict__)

def norm(s):
 s=s.lower()
 for number,word in [('150','one hundred fifty'),('3','three'),('2','two'),('1','one')]:s=re.sub(r'\b'+number+r'\b',word,s)
 s=s.replace('one hundred and fifty','one hundred fifty')
 return re.sub('[^a-z0-9]','',s)

def audio():
 p.auth();os.environ['HF_HOME']=str(p.REPO.parent/'cooking_shorts_sample/models')
 from faster_whisper import WhisperModel
 from scipy.signal import resample_poly
 import requests
 model=WhisperModel('small',device='cpu',compute_type='int8',cpu_threads=3)
 original={x['id']:x for x in json.loads((ROOT/'audio/manifest.json').read_text(encoding='utf-8'))}
 cached={x['id']:x for x in p.rows()} if (p.AUDIO/'manifest.json').exists() else {}
 reports=[];rows=[]
 for sid,title,text,speaker,_ in p.ROWS:
  path=p.AUDIO/(sid+'.wav');voice='Despina' if speaker=='Narrator' else 'Aoede'
  take=cached.get(sid,{})
  needs_take=not path.exists() or take.get('text')!=text or take.get('voice',voice)!=voice
  for attempt in range(3):
   if needs_take or attempt:
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
 assert all(p.ROWS[ids.index(s)][3]=='Narrator' for s in ('benefit','habit'))
 assert 'fiber' in DIALOGUE['benefit'].lower() and 'water' in DIALOGUE['habit'].lower()
 cmd=sys.argv[1]
 if cmd in ('audio','check'):globals()[cmd]()
 elif cmd=='verify':m.verify()
 else:getattr(p,cmd)()
