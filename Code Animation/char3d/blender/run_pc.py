"""PC의 Blender(GUI) 파이썬 콘솔에서 한 번 실행해 두는 작업 감시기.
   MODE 없이:  exec(open(r'C:\\Users\\<사용자>\\Videos\\heart_blender\\run_pc.py', encoding='utf-8').read())
   - BASE/queue/*.json 작업 파일을 차례로 집어 백그라운드 Blender(blender -b)로 처리하고, 결과·진행 상황을 BASE/status.json·log.txt에 남긴다.
   - 작업 파일 형식(하나에 여러 단계 가능, 순서대로):
     {"id": "s1", "steps": [
        {"unzip": "bundle.zip"},                                    # BASE/bundle.zip → BASE/export
        {"render": "C8a", "frames": "80-80", "res": "1920x1080", "samples": 128, "extra": ["--fstop", "2.8"]},
        {"encode": "C8a"} ]}                                         # BASE/out/C8a/*.png → BASE/mp4/C8a.mp4
   - 끝난 작업 파일은 queue/done/ 으로 옮긴다. GUI는 그대로 쓸 수 있다(감시는 별도 스레드).
"""
import os, sys, json, time, glob, shutil, zipfile, threading, subprocess, traceback
import bpy

BASE = os.path.join(os.path.expanduser('~'), 'Videos', 'heart_blender')
EXP, OUT, MP4, Q = (os.path.join(BASE, d) for d in ('export', 'out', 'mp4', 'queue'))
for d in (EXP, OUT, MP4, Q, os.path.join(Q, 'done')): os.makedirs(d, exist_ok=True)
BLENDER = bpy.app.binary_path
LOG = os.path.join(BASE, 'log.txt')
state = {'started': time.strftime('%Y-%m-%d %H:%M:%S'), 'job': None, 'step': None, 'history': [], 'alive': time.time()}

def log(*a):
    line = time.strftime('%H:%M:%S ') + ' '.join(str(x) for x in a)
    with open(LOG, 'a', encoding='utf-8') as f: f.write(line + '\n')
    print(line)

def save_state():
    state['alive'] = time.time()
    with open(os.path.join(BASE, 'status.json'), 'w', encoding='utf-8') as f: json.dump(state, f, ensure_ascii=False, indent=1)

def run(cmd, tag):
    t0 = time.time(); log('RUN', tag, ' '.join(cmd[3:]))
    with open(os.path.join(BASE, f'last_{tag}.txt'), 'w', encoding='utf-8', errors='replace') as f:
        p = subprocess.Popen(cmd, stdout=f, stderr=subprocess.STDOUT, creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
        while p.poll() is None: time.sleep(2); save_state()
    dt = time.time() - t0; log('END', tag, 'code', p.returncode, f'{dt:.0f}s'); return p.returncode, dt

def step_do(s):
    if 'unzip' in s:
        z = os.path.join(BASE, s['unzip']); log('UNZIP', z)
        with zipfile.ZipFile(z) as zz: zz.extractall(EXP)
        return {'ok': True}
    if 'render' in s:
        cut = s['render']; cmd = [BLENDER, '-b', '--factory-startup', '-P', os.path.join(BASE, 'heart_pixar.py'), '--', EXP, cut,
                                  '--out', OUT, '--res', s.get('res', '1920x1080'), '--samples', str(s.get('samples', 128)), '--render']
        if s.get('frames'): cmd += ['--frames', s['frames']]
        cmd += [str(x) for x in s.get('extra', [])]
        code, dt = run(cmd, 'render')
        n = len(glob.glob(os.path.join(OUT, cut, '*.png')))
        return {'ok': code == 0, 'sec': round(dt), 'pngs': n}
    if 'encode' in s:
        cut = s['encode']; code, dt = run([BLENDER, '-b', '--factory-startup', '-P', os.path.join(BASE, 'encode_seq.py'), '--',
                                           os.path.join(OUT, cut), os.path.join(MP4, f'{cut}.mp4')], 'encode')
        return {'ok': code == 0 and os.path.exists(os.path.join(MP4, f'{cut}.mp4')), 'sec': round(dt)}
    return {'ok': False, 'err': 'unknown step'}

def bg_blenders():
    # 지금 돌고 있는 백그라운드 Blender(blender -b) 수. 로그 파일 수정 시각은 Windows에서 열린 채로는 잘 안 바뀌어 믿을 수 없으므로 프로세스 명령줄로 본다.
    try:
        out = subprocess.run(['powershell', '-NoProfile', '-Command',
                              "Get-CimInstance Win32_Process -Filter \"name='blender.exe'\" | ForEach-Object { $_.CommandLine }"],
                             capture_output=True, text=True, timeout=30, creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0)).stdout
        return sum(1 for ln in out.splitlines() if ' -b ' in ln)
    except Exception:
        return 0

def wait_orphan():
    # 감시기(GUI Blender)가 꺼져도 이미 띄운 백그라운드 렌더는 계속 돈다. 다시 켰을 때 그 렌더가 아직 돌고 있으면 끝날 때까지 기다려 GPU를 겹쳐 쓰지 않는다.
    while bg_blenders() > 0:
        state['step'] = '이전 백그라운드 렌더가 아직 도는 중 — 끝나길 기다림'; save_state(); time.sleep(15)

def loop():
    log('감시 시작', BASE, BLENDER)
    wait_orphan()
    while True:
        try:
            jobs = sorted(glob.glob(os.path.join(Q, '*.json')))
            if not jobs: save_state(); time.sleep(5); continue
            jf = jobs[0]; job = json.load(open(jf, encoding='utf-8')); state['job'] = job.get('id', os.path.basename(jf)); res = []
            for i, s in enumerate(job.get('steps', [])):
                state['step'] = f'{i + 1}/{len(job["steps"])} {json.dumps(s, ensure_ascii=False)}'; save_state()
                try: r = step_do(s)
                except Exception as e: r = {'ok': False, 'err': repr(e)}; log(traceback.format_exc())
                res.append(r); log('STEP', state['job'], i + 1, r)
            state['history'].append({'job': state['job'], 'results': res, 'at': time.strftime('%H:%M:%S')}); state['job'] = state['step'] = None
            shutil.move(jf, os.path.join(Q, 'done', os.path.basename(jf))); save_state()
        except Exception:
            log(traceback.format_exc()); time.sleep(5)

ns = bpy.app.driver_namespace
if not ns.get('_heart_watch'):
    th = threading.Thread(target=loop, daemon=True); th.start(); ns['_heart_watch'] = th
    print('heart_blender 감시기 실행 중 — queue 폴더를 봅니다:', Q)
else:
    print('이미 실행 중')
