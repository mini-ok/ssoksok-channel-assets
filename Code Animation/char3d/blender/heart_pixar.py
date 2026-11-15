"""〈심장의 휴가〉 컷 → Blender(Cycles) 장면: 애니매틱에서 내보낸 GLB·JSON·얼굴 PNG를 불러와
   픽사풍(부드러운 큰 면광원 3점 조명 + 가장자리 빛, 피부 같은 속살 산란 클레이, 얕은 심도, 모션 블러, AgX 색, 빛 번짐)으로 꾸민다.

사용(Blender 4.2 이상, 5.x 확인):
  blender -b -P heart_pixar.py -- <export_dir> <CUT> [옵션]
  예) blender -b -P heart_pixar.py -- ../export C8a --res 1920x1080 --samples 256 --render
옵션
  --out DIR        결과 폴더(기본 <export_dir>/blend). <CUT>.blend 저장, --render면 DIR/<CUT>/#####.png
  --res WxH        해상도(기본 1920x1080)        --samples N   Cycles 샘플(기본 256, 적응형)
  --frames A-B     이 범위만 렌더(1부터)          --fstop F     조리개(기본 2.8, 숫자가 작을수록 배경이 더 흐림)
  --haze D         공기 원근(볼륨 안개) 밀도(기본 0 = 끔, 0.004 정도면 은은)
  --cpu            GPU 대신 CPU                    --render      저장 후 바로 렌더
내보내기(애니매틱 폴더에서): node render_film.mjs export ../export C1 C5 ...   (export_scene.js가 GLB·JSON·faces/*.png를 만듦)
"""
import bpy, sys, os, json, math
from mathutils import Vector

argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
if len(argv) < 2:
    print(__doc__); sys.exit(1)
EXP, CUT = os.path.abspath(argv[0]), argv[1]
opt = {'out': os.path.join(EXP, 'blend'), 'res': '1920x1080', 'samples': '256', 'frames': None, 'fstop': '2.8', 'haze': '0', 'gpu': '3070'}
flags = set()
i = 2
while i < len(argv):
    a = argv[i]
    if a in ('--cpu', '--render'): flags.add(a[2:]); i += 1
    else: opt[a[2:]] = argv[i + 1]; i += 2
meta = json.load(open(os.path.join(EXP, f'{CUT}.json')))
N, FPS = meta['frames'], meta['fps']

# ---------------------------------------------------------------- 장면 불러오기
bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
sc.render.fps = FPS
bpy.ops.import_scene.gltf(filepath=os.path.join(EXP, f'{CUT}.glb'))

def fcurves_of(action):
    """Blender 4.4+(슬롯 액션)과 이전 버전 모두에서 F-커브 목록."""
    if hasattr(action, 'fcurves') and len(getattr(action, 'fcurves', [])):
        return list(action.fcurves)
    out = []
    for layer in getattr(action, 'layers', []):
        for strip in layer.strips:
            for bag in getattr(strip, 'channelbags', []):
                out += list(bag.fcurves)
    return out

f0, f1 = 1e9, -1e9
for act in bpy.data.actions:
    for fc in fcurves_of(act):
        if len(fc.keyframe_points):
            f0 = min(f0, fc.keyframe_points[0].co.x); f1 = max(f1, fc.keyframe_points[-1].co.x)
F0 = int(round(f0)) if f0 < 1e9 else 1          # 0프레임(애니매틱 t=0)이 놓인 Blender 프레임
sc.frame_start, sc.frame_end = F0, F0 + N - 1
if opt['frames']:
    a, b = opt['frames'].split('-'); sc.frame_start, sc.frame_end = F0 + int(a) - 1, F0 + int(b) - 1

for act in bpy.data.actions:                    # 끊어 찍은 키(24fps) 사이가 미끄러지지 않게
    for fc in fcurves_of(act):
        for kp in fc.keyframe_points: kp.interpolation = 'LINEAR'
objs = {o.name: o for o in bpy.data.objects}

# 순간이동(파이프 끝에서 처음으로 돌아가는 혈구·먼지 등): 두 프레임 사이 한가운데서 끊어 옮겨 모션 블러에 긴 줄이 생기지 않게
def fcurves_for(o):
    """한 물체의 F-커브만(5.x 슬롯 액션은 여러 물체가 한 액션을 나눠 씀)."""
    ad = o.animation_data; act = ad.action
    slot = getattr(ad, 'action_slot', None)
    if slot is not None and hasattr(act, 'layers'):
        out = []
        for layer in act.layers:
            for strip in layer.strips:
                try:
                    bag = strip.channelbag(slot)
                except Exception:
                    bag = None
                if bag: out += list(bag.fcurves)
        return out
    return list(getattr(act, 'fcurves', []))

def fcurves_for_data(idb):
    ad = idb.animation_data; act = ad.action
    if act is None: return []
    slot = getattr(ad, 'action_slot', None)
    if slot is not None and hasattr(act, 'layers'):
        out = []
        for layer in act.layers:
            for strip in layer.strips:
                try: bag = strip.channelbag(slot)
                except Exception: bag = None
                if bag: out += list(bag.fcurves)
        return out
    return list(getattr(act, 'fcurves', []))

def fix_jumps():
    nfix = 0
    for o in bpy.data.objects:
        ad = o.animation_data
        if not ad or not ad.action: continue
        loc = sorted([fc for fc in fcurves_for(o) if fc.data_path == 'location'], key=lambda fc: fc.array_index)
        if len(loc) != 3 or len(loc[0].keyframe_points) < 3: continue
        P = [[kp.co.y for kp in fc.keyframe_points] for fc in loc]; X = [kp.co.x for kp in loc[0].keyframe_points]; n = len(X)
        if any(len(fc.keyframe_points) != n for fc in loc): continue
        d = [math.dist((P[0][i], P[1][i], P[2][i]), (P[0][i - 1], P[1][i - 1], P[2][i - 1])) for i in range(1, n)]
        med = sorted(d)[len(d) // 2]
        jumps = [i for i in range(1, n) if d[i - 1] > max(0.25, 6 * med)]
        for i in reversed(jumps):                 # 뒤에서부터(삽입으로 번호가 밀리지 않게)
            for c, fc in enumerate(loc):
                fc.keyframe_points[i - 1].interpolation = 'CONSTANT'
                kp = fc.keyframe_points.insert(X[i] - 0.5, P[c][i], options={'FAST'}); kp.interpolation = 'LINEAR'
            nfix += 1
        for fc in loc: fc.update()
    return nfix
def fix_rot_scale():
    """회전 사원수 부호 뒤집힘(같은 자세인데 보간이 한 바퀴 돎)과 보였다 숨는 크기 변화(1e-4↔1)를 정리 — 모션 블러에 유령 줄이 생기지 않게."""
    nq = ns = 0
    for o in bpy.data.objects:
        ad = o.animation_data
        if not ad or not ad.action: continue
        fcs = fcurves_for(o)
        q = sorted([fc for fc in fcs if fc.data_path == 'rotation_quaternion'], key=lambda fc: fc.array_index)
        if len(q) == 4 and all(len(fc.keyframe_points) == len(q[0].keyframe_points) for fc in q):
            n = len(q[0].keyframe_points)
            for i in range(1, n):
                a_ = [fc.keyframe_points[i - 1].co.y for fc in q]; b_ = [fc.keyframe_points[i].co.y for fc in q]
                if sum(x * y for x, y in zip(a_, b_)) < 0:
                    for fc in q: fc.keyframe_points[i].co.y *= -1
                    nq += 1
            for fc in q: fc.update()
        sc_ = sorted([fc for fc in fcs if fc.data_path == 'scale'], key=lambda fc: fc.array_index)
        if len(sc_) == 3 and all(len(fc.keyframe_points) == len(sc_[0].keyframe_points) for fc in sc_):
            X = [kp.co.x for kp in sc_[0].keyframe_points]; V = [[kp.co.y for kp in fc.keyframe_points] for fc in sc_]
            togg = [i for i in range(1, len(X)) if (min(abs(V[0][i]), abs(V[0][i - 1])) < 1e-3) != (max(abs(V[0][i]), abs(V[0][i - 1])) < 1e-3)]
            for i in reversed(togg):
                for c, fc in enumerate(sc_):
                    fc.keyframe_points[i - 1].interpolation = 'CONSTANT'
                    kp = fc.keyframe_points.insert(X[i] - 0.5, V[c][i], options={'FAST'}); kp.interpolation = 'LINEAR'
                ns += 1
            for fc in sc_: fc.update()
    return nq, ns
print('순간이동 끊기:', fix_jumps(), ' 회전 뒤집힘·보이기 전환:', fix_rot_scale())
def find(prefix):
    for nm, o in objs.items():
        if nm == prefix or nm.startswith(prefix + '.') or nm.startswith(prefix): return o
    return None

def set_in(node, names, val):
    for nm in names:
        if nm in node.inputs:
            try: node.inputs[nm].default_value = val; return True
            except Exception: pass
    return False

# ---------------------------------------------------------------- 재질: 캐릭터는 속살 산란 클레이, 소품은 살짝 거칠게
CHARS = ('heart:', 'gut:', 'liver:', 'brain:')
done = set()
for o in bpy.data.objects:
    if o.type != 'MESH': continue
    is_char = o.name.startswith(CHARS)
    for slot in o.material_slots:
        m = slot.material
        if not m or not m.node_tree or (m.name, is_char) in done: continue
        done.add((m.name, is_char))
        for nd in m.node_tree.nodes:
            if nd.type != 'BSDF_PRINCIPLED': continue
            if is_char:
                set_in(nd, ['Subsurface Weight', 'Subsurface'], 0.2)
                set_in(nd, ['Subsurface Radius'], (1.0, 0.45, 0.3))
                set_in(nd, ['Subsurface Scale'], 0.06)
                set_in(nd, ['Roughness'], 0.5)
                set_in(nd, ['Coat Weight', 'Clearcoat'], 0.12); set_in(nd, ['Coat Roughness', 'Clearcoat Roughness'], 0.35)
                set_in(nd, ['Sheen Weight', 'Sheen'], 0.08); set_in(nd, ['Sheen Roughness'], 0.6)
            else:
                r = nd.inputs['Roughness'].default_value if 'Roughness' in nd.inputs else 0.5
                set_in(nd, ['Roughness'], min(1.0, r + 0.05))
            es = nd.inputs.get('Emission Strength')
            if es is not None and es.default_value > 0: es.default_value *= 2.5   # 안에서 빛나는 재료(전구·세포·파이프 끝)

# ---------------------------------------------------------------- 재질 애니메이션(전구·파이프 끝·경보 등): 발광색·세기, 바탕색, 불투명도 키
EMI_BOOST = 3.0
def unlit_alpha(m, ops):
    """glTF unlit 재질의 투명도 키: 투명 셰이더와 섞는 노드를 끝에 하나 두고 그 비율을 키로."""
    nt_ = m.node_tree; out = next((n for n in nt_.nodes if n.type == 'OUTPUT_MATERIAL'), None)
    if not out or not out.inputs['Surface'].is_linked: return
    src = out.inputs['Surface'].links[0].from_socket
    tr = nt_.nodes.new('ShaderNodeBsdfTransparent'); mx = nt_.nodes.new('ShaderNodeMixShader'); mx.name = 'OPACITY'
    nt_.links.new(tr.outputs[0], mx.inputs[1]); nt_.links.new(src, mx.inputs[2]); nt_.links.new(mx.outputs[0], out.inputs['Surface'])
    for f, v in enumerate(ops):
        mx.inputs['Fac'].default_value = v; mx.inputs['Fac'].keyframe_insert('default_value', frame=F0 + f)
for mname, d in (meta.get('mats') or {}).items():
    m = bpy.data.materials.get(mname)
    if not m or not m.node_tree: continue
    bs = next((n for n in m.node_tree.nodes if n.type == 'BSDF_PRINCIPLED'), None)
    if not bs:                                   # 그림자 없는 평면(꿈 방울·해 후광 등, glTF unlit): 투명도만 키로
        if 'o' in d: unlit_alpha(m, d['o'])
        continue
    ec, es, bc, al = bs.inputs.get('Emission Color'), bs.inputs.get('Emission Strength'), bs.inputs.get('Base Color'), bs.inputs.get('Alpha')
    for f in range(N):
        sf = F0 + f
        if 'e' in d and d['e'][f] and ec is not None and es is not None:
            r, g, b, k = d['e'][f]; mx = max(r, g, b, 1e-4)
            ec.default_value = (r / mx, g / mx, b / mx, 1); es.default_value = k * mx * EMI_BOOST
            ec.keyframe_insert('default_value', frame=sf); es.keyframe_insert('default_value', frame=sf)
        if 'c' in d and d['c'][f] and bc is not None and not bc.is_linked:
            bc.default_value = (*d['c'][f], 1); bc.keyframe_insert('default_value', frame=sf)
        if 'o' in d and al is not None and not al.is_linked:
            al.default_value = d['o'][f]; al.keyframe_insert('default_value', frame=sf)
    ad = m.node_tree.animation_data
    if ad and ad.action:
        for fc in fcurves_of(ad.action):
            for kp in fc.keyframe_points: kp.interpolation = 'LINEAR'

# ---------------------------------------------------------------- 얼굴: 상태별 PNG를 이미지 시퀀스로, 프레임마다 offset 키
for ch, F in meta.get('faces', {}).items():
    o = find(F['mesh'])
    if not o or not F.get('count'): continue
    first = os.path.join(EXP, 'faces', f'{CUT}_{ch}_0001.png')
    img = bpy.data.images.load(first); img.source = 'SEQUENCE'; img.colorspace_settings.name = 'sRGB'
    for slot in o.material_slots:
        m = slot.material
        if not m or not m.node_tree: continue
        for nd in m.node_tree.nodes:
            if nd.type == 'TEX_IMAGE':
                nd.image = img; iu = nd.image_user
                iu.frame_start, iu.frame_duration, iu.use_auto_refresh, iu.use_cyclic = 1, max(F0 + N + 5, F['count']), True, False   # 길게 둬야 offset 전에 잘리지 않음
                for f, j in enumerate(F['idx']):
                    sf = F0 + f; iu.frame_offset = (j + 1) - sf   # 보이는 번호 = sf + offset
                    m.node_tree.keyframe_insert(f'nodes["{nd.name}"].image_user.frame_offset', frame=sf)
                ad = m.node_tree.animation_data
                if ad and ad.action:
                    for fc in fcurves_of(ad.action):
                        for kp in fc.keyframe_points: kp.interpolation = 'CONSTANT'

# ---------------------------------------------------------------- 한쪽 면만 그리는 재질(three.js 기본): 카메라에서 뒷면이 보이면 투명하게
# (애니매틱은 벽 바깥에 둔 카메라가 벽 뒷면을 투과해 방 안을 봄. Blender는 양면을 다 그려 화면이 벽 뒷면으로 막힘 — 조명·그림자는 그대로 두고 카메라 광선만)
def camera_backface_clear(m):
    nt_ = m.node_tree; out = next((n for n in nt_.nodes if n.type == 'OUTPUT_MATERIAL'), None)
    if not out or not out.inputs['Surface'].is_linked or 'BACKCLEAR' in nt_.nodes: return False
    src = out.inputs['Surface'].links[0].from_socket
    geo = nt_.nodes.new('ShaderNodeNewGeometry'); lp = nt_.nodes.new('ShaderNodeLightPath')
    mul = nt_.nodes.new('ShaderNodeMath'); mul.operation = 'MULTIPLY'
    nt_.links.new(geo.outputs['Backfacing'], mul.inputs[0]); nt_.links.new(lp.outputs['Is Camera Ray'], mul.inputs[1])
    tr = nt_.nodes.new('ShaderNodeBsdfTransparent'); mx = nt_.nodes.new('ShaderNodeMixShader'); mx.name = 'BACKCLEAR'
    nt_.links.new(mul.outputs[0], mx.inputs['Fac']); nt_.links.new(src, mx.inputs[1]); nt_.links.new(tr.outputs[0], mx.inputs[2])
    nt_.links.new(mx.outputs[0], out.inputs['Surface']); return True
nbf = sum(camera_backface_clear(m) for m in bpy.data.materials if m.node_tree and getattr(m, 'use_backface_culling', False))
print('뒷면 투과 재질:', nbf)

# ---------------------------------------------------------------- 화면(심전도·상황실 모니터·화이트보드): 프레임별 그림을 이미지 시퀀스로
def seq_on_material(m, first, idx, count):
    """재질 m의 이미지 노드를 그림 시퀀스로 바꾸고, 프레임마다 보일 번호(idx[f], 0부터)를 offset 키로."""
    if not m or not m.node_tree: return 0
    img = bpy.data.images.load(first, check_existing=True); img.source = 'SEQUENCE'; img.colorspace_settings.name = 'sRGB'
    n = 0
    for nd in m.node_tree.nodes:
        if nd.type != 'TEX_IMAGE': continue
        nd.image = img; iu = nd.image_user
        iu.frame_start, iu.frame_duration, iu.use_auto_refresh, iu.use_cyclic = 1, max(F0 + N + 5, count), True, False
        for f, j in enumerate(idx):
            sf = F0 + f; iu.frame_offset = (j + 1) - sf
            m.node_tree.keyframe_insert(f'nodes["{nd.name}"].image_user.frame_offset', frame=sf)
        n += 1
    ad = m.node_tree.animation_data
    if ad and ad.action:
        for fc in fcurves_of(ad.action):
            if 'frame_offset' in fc.data_path:
                for kp in fc.keyframe_points: kp.interpolation = 'CONSTANT'
    return n

nscr = 0
for key, S in (meta.get('screens') or {}).items():
    first = os.path.join(EXP, 'screens', f'{CUT}_{key}_0001.png')
    if not os.path.exists(first): continue
    for mn in S['mats']:
        nscr += seq_on_material(bpy.data.materials.get(mn), first, S['idx'], S['count'])
print('화면 시퀀스 노드:', nscr)

# ---------------------------------------------------------------- 무늬 흐름(컨베이어 벨트·바다): 텍스처 좌표 이동 키
for key, U in (meta.get('uv') or {}).items():
    for mn in U['mats']:
        m = bpy.data.materials.get(mn)
        if not m or not m.node_tree: continue
        nt_ = m.node_tree
        for tex in [nd for nd in nt_.nodes if nd.type == 'TEX_IMAGE']:
            vin = tex.inputs['Vector']
            mp = vin.links[0].from_node if vin.is_linked and vin.links[0].from_node.type == 'MAPPING' else None
            if mp is None:
                mp = nt_.nodes.new('ShaderNodeMapping'); uvn = nt_.nodes.new('ShaderNodeUVMap')
                nt_.links.new(uvn.outputs['UV'], mp.inputs['Vector']); nt_.links.new(mp.outputs['Vector'], vin)
            for f, (ox, oy, rx, ry) in enumerate(U['off']):
                mp.inputs['Location'].default_value = (ox, 1 - oy - ry, 0); mp.inputs['Scale'].default_value = (rx, ry, 1)
                mp.inputs['Location'].keyframe_insert('default_value', frame=F0 + f); mp.inputs['Scale'].keyframe_insert('default_value', frame=F0 + f)
        ad = nt_.animation_data
        if ad and ad.action:
            for fc in fcurves_of(ad.action):
                if 'inputs' in fc.data_path:
                    for kp in fc.keyframe_points: kp.interpolation = 'LINEAR'

# ---------------------------------------------------------------- 점조명(펌프실 천장등·복도 문 안쪽 빛·손의 빛): 프레임별 세기·색 키
LIGHT_K = float(opt.get('lightk', '30'))       # three.js 점조명 세기(cd) → Blender W. 애니매틱과 나란히 비교해 맞춘 값
nl = 0
for lname, L in (meta.get('lights') or {}).items():
    o = find(lname)
    if not o or o.type != 'LIGHT': continue
    ld = o.data; ld.shadow_soft_size = 0.15; nl += 1
    try: o.visible_camera = False                # 빛 자체(둥근 발광체)는 화면에 안 보이게 — 렌즈 앞에서 큰 분홍 얼룩으로 번짐
    except Exception: pass
    for f in range(N if len(L['i']) > 1 or len(L['c']) > 1 else 1):
        i_ = L['i'][min(f, len(L['i']) - 1)]; c_ = L['c'][min(f, len(L['c']) - 1)]
        ld.energy = i_ * LIGHT_K; ld.color = c_
        if len(L['i']) > 1: ld.keyframe_insert('energy', frame=F0 + f)
        if len(L['c']) > 1: ld.keyframe_insert('color', frame=F0 + f)
print('점조명:', nl)

# ---------------------------------------------------------------- 카메라: 화각 키, 얕은 심도(주인공에 초점), 모션 블러
cam = objs.get('CAMERA') or next((o for o in bpy.data.objects if o.type == 'CAMERA'), None)
hero = find(meta['hero']) if meta.get('hero') else None
if hero is None:                                   # 주인공이 없는 컷(자동 펌프 퍽 등): 공간 가운데를 조명·초점 기준으로
    hero = bpy.data.objects.new('AIM', None); bpy.context.collection.objects.link(hero); hero.location = (0, 0, 0.5)
if cam:
    sc.camera = cam; cd = cam.data
    cd.sensor_fit, cd.sensor_height, cd.clip_start, cd.clip_end = 'VERTICAL', 24.0, 0.03, 300
    for f, fov in enumerate(meta['fov']):
        cd.lens = 12.0 / math.tan(math.radians(fov) / 2); cd.keyframe_insert('lens', frame=F0 + f)
    cd.dof.use_dof = True; cd.dof.aperture_fstop = float(opt['fstop']) if opt['fstop'] != '2.8' or meta.get('set') != 'nook' else 4.0   # 바닷가 원경: 조리개를 조금 조여 하늘의 방울이 큰 원으로 번지지 않게; cd.dof.aperture_blades = 7
    if meta.get('focus'):                          # 초점 거리 키(주인공이 화면 밖이면 화면 가운데 물체 — 인서트 컷이 통째로 흐려지지 않게)
        cd.dof.focus_object = None
        for f, dd in enumerate(meta['focus']):
            cd.dof.focus_distance = max(0.2, dd); cd.dof.keyframe_insert('focus_distance', frame=F0 + f)
    elif hero:
        foc = bpy.data.objects.new('FOCUS', None); bpy.context.collection.objects.link(foc)
        foc.parent = hero; foc.location = (0, 0, 0); cd.dof.focus_object = foc

# ---------------------------------------------------------------- 조명: 큰 면광원 3점(키·필·림) + 바닥 반사광 — 카메라와 주인공 위치를 따라 프레임마다
def area(name, size, color, power):
    ld = bpy.data.lights.new(name, 'AREA'); ld.shape = 'DISK'; ld.size = size; ld.color = color; ld.energy = power
    ob = bpy.data.objects.new(name, ld); bpy.context.collection.objects.link(ob)
    try: ob.visible_camera = False
    except Exception: pass
    return ob
atmo = meta.get('atmo') or {}
def hexrgb(h, k=1.0):
    h = (h or '#ffd8c0').lstrip('#'); return tuple(min(1.0, int(h[i:i + 2], 16) / 255 * k) for i in (0, 2, 4))
tint = hexrgb(atmo.get('fog'))
KEY = area('KEY', 3.0, (1.0, 0.9, 0.78), 260)
FILL = area('FILL', 4.0, (0.72 + 0.2 * tint[0], 0.8 + 0.15 * tint[1], 1.0), 70)
RIM = area('RIM', 1.6, (1.0, 0.86, 0.8), 450)
BOUNCE = area('BOUNCE', 3.0, tuple(0.5 + 0.5 * c for c in tint), 45)
for L in (KEY, FILL, RIM, BOUNCE):
    if hero:
        tc = L.constraints.new('TRACK_TO'); tc.target = hero; tc.track_axis = 'TRACK_NEGATIVE_Z'; tc.up_axis = 'UP_Y'

def rotz(v, a):
    c, s = math.cos(a), math.sin(a); return Vector((v.x * c - v.y * s, v.x * s + v.y * c, 0))
DIM = []
if cam and hero:
    for f in range(N):
        sf = F0 + f; sc.frame_set(sf)
        h = hero.matrix_world.translation + Vector((0, 0, 0.45)); c = cam.matrix_world.translation
        d = Vector((c.x - h.x, c.y - h.y, 0)); d = d.normalized() if d.length > 1e-4 else Vector((0, -1, 0))
        KEY.location = h + rotz(d, math.radians(48)) * 3.2 + Vector((0, 0, 2.6))
        FILL.location = h + rotz(d, math.radians(-62)) * 3.4 + Vector((0, 0, 0.9))
        RIM.location = h - d * 2.6 + rotz(d, math.radians(90)) * 0.8 + Vector((0, 0, 1.9))
        BOUNCE.location = h + d * 1.2 + Vector((0, 0, -0.35))
        Lf = meta['light'][f]; k = Lf['key'] / 1.0
        lum = 0.5 * Lf['key'] + 0.3 * Lf['hemi'] / 0.4 + 0.2 * Lf['env'] / 0.35
        dimf = max(0.05, min(1.0, lum / 0.9)) ** float(opt.get('dimpow', '1.0'))                 # (평상시 컷의 밝기 ≈0.9 기준) 정전·빛이 빠지는 장면: 조명만 낮춤(애니매틱처럼 스스로 빛나는 하늘·전구·화면은 그대로)
        DIM.append(dimf)
        KEY.data.energy = 260 * dimf; FILL.data.energy = 70 * dimf
        RIM.data.energy = 450 * dimf; BOUNCE.data.energy = 45 * dimf
        for L in (KEY, FILL, RIM, BOUNCE):
            L.keyframe_insert('location', frame=sf); L.data.keyframe_insert('energy', frame=sf)
# 컷 안의 카메라 전환(와이드 → 인서트 등): 이전 화면이 모션 블러로 겹쳐 번지지 않게 전환 프레임 한가운데서 끊음
def mid_cut(fcs, idxs):
    for fc in fcs:
        if not fc or len(fc.keyframe_points) < 2: continue
        for i in reversed(idxs):
            sf = F0 + i
            # 삽입하면 키 배열이 다시 잡혀 앞서 얻은 키 참조가 무효가 되므로 매번 새로 찾음
            vals = {round(kp.co.x, 3): kp.co.y for kp in fc.keyframe_points}
            if sf not in vals or (sf - 1) not in vals: continue
            kp = fc.keyframe_points.insert(sf - 0.5, vals[sf], options={'FAST'}); kp.interpolation = 'LINEAR'
            for kp in fc.keyframe_points:
                if abs(kp.co.x - (sf - 1)) < 1e-3: kp.interpolation = 'CONSTANT'
        fc.update()
if cam:
    cfc = fcurves_for(cam) if cam.animation_data and cam.animation_data.action else []
    sc.frame_set(F0); prevM = cam.matrix_world.copy(); dl, da = [0.0], [0.0]
    for f in range(1, N):
        sc.frame_set(F0 + f); M = cam.matrix_world.copy()
        dl.append((M.translation - prevM.translation).length); da.append(math.degrees(M.to_quaternion().rotation_difference(prevM.to_quaternion()).angle)); prevM = M
    dfv = [0.0] + [abs(meta['fov'][f] - meta['fov'][f - 1]) for f in range(1, N)]
    med = lambda L: sorted(L)[len(L) // 2]
    ml, ma, mf = med(dl), med(da), med(dfv)
    def spike(L, f, floor):                        # 앞뒤 이웃 프레임보다 훨씬 큰 한 번의 변화만 전환으로 봄(서서히 빨라지는 달리 이동은 제외)
        nb = [L[k] for k in (f - 2, f - 1, f + 1, f + 2) if 1 <= k < N]
        return L[f] > floor and L[f] > 4 * max(nb + [1e-9])
    cuts = [f for f in range(1, N) if spike(dl, f, 0.05) or spike(da, f, 2.0) or spike(dfv, f, 1.0)]
    if cuts:
        lens_fc = [fc for fc in (fcurves_for_data(cd) if cd.animation_data else []) if fc.data_path in ('lens', 'dof.focus_distance')]
        mid_cut([fc for fc in cfc if fc.data_path in ('location', 'rotation_quaternion', 'rotation_euler')] + lens_fc, cuts)
        for L in (KEY, FILL, RIM, BOUNCE):
            if L.animation_data and L.animation_data.action: mid_cut([fc for fc in fcurves_for(L) if fc.data_path == 'location'], cuts)
    print('카메라 전환 프레임:', cuts)
sc.frame_set(sc.frame_start)

# ---------------------------------------------------------------- 세계: 공간 색으로 은은한 주변광(보이는 하늘은 내보낸 하늘 구가 그대로), 원하면 공기 원근
world = bpy.data.worlds.new('World'); sc.world = world
try: world.use_nodes = True
except Exception: pass
nt = world.node_tree; bg = nt.nodes.get('Background')
bg.inputs['Color'].default_value = (*hexrgb(atmo.get('fog'), 0.9), 1); bg.inputs['Strength'].default_value = 0.35
for f, dv in enumerate(DIM):
    bg.inputs['Strength'].default_value = 0.35 * dv; bg.inputs['Strength'].keyframe_insert('default_value', frame=F0 + f)
haze = float(opt['haze'])
if haze > 0:
    vol = nt.nodes.new('ShaderNodeVolumePrincipled'); vol.inputs['Density'].default_value = haze
    vol.inputs['Color'].default_value = (*hexrgb(atmo.get('fog')), 1)
    nt.links.new(vol.outputs['Volume'], nt.nodes['World Output'].inputs['Volume'])

# ---------------------------------------------------------------- 렌더 설정
r = sc.render
r.engine = 'CYCLES'
cy = sc.cycles
if 'cpu' not in flags:
    try:
        prefs = bpy.context.preferences.addons['cycles'].preferences
        for dev in ('OPTIX', 'CUDA', 'HIP', 'METAL', 'ONEAPI'):
            try:
                prefs.compute_device_type = dev; prefs.get_devices()
                devs = [d for d in prefs.devices if d.type == dev]
                if devs:
                    want = opt.get('gpu', '3070')                  # 기본: RTX 3070만(GTX 1050처럼 약한 카드가 섞이면 오히려 느리고 메모리가 모자람)
                    pick = [d for d in devs if want and want.lower() in d.name.lower()] or devs
                    for d in prefs.devices: d.use = d in pick
                    cy.device = 'GPU'; print('GPU:', dev, [d.name for d in pick]); break
            except Exception: continue
    except Exception as e: print('GPU 설정 실패, CPU로:', e)
cy.samples = int(opt['samples']); cy.use_adaptive_sampling = True; cy.adaptive_threshold = 0.01
cy.use_denoising = True
cy.max_bounces, cy.diffuse_bounces, cy.glossy_bounces, cy.transmission_bounces, cy.transparent_max_bounces = 8, 4, 4, 8, 16
cy.sample_clamp_indirect = 8.0; cy.caustics_reflective = cy.caustics_refractive = False
w, h = map(int, opt['res'].lower().split('x')); r.resolution_x, r.resolution_y, r.resolution_percentage = w, h, 100
r.use_motion_blur = True; r.motion_blur_shutter = 0.5
r.film_transparent = False; r.filter_size = 1.5
vs = sc.view_settings
VIEW = opt.get('view', 'neutral')                 # neutral(기본, 사용자 확정 2026-11-14): 애니매틱과 같은 Khronos PBR Neutral / agx: AgX Punchy
if VIEW == 'neutral':
    try: vs.view_transform = 'Khronos PBR Neutral'; vs.look = 'None'
    except Exception: VIEW = 'agx'
if VIEW != 'neutral':
    for vt in ('AgX', 'Filmic'):
        try: vs.view_transform = vt; break
        except Exception: pass
    for look in ('AgX - Punchy', 'AgX - Medium High Contrast', 'Medium High Contrast'):
        try: vs.look = look; break
        except Exception: pass
vs.exposure = -0.25
# 애니매틱의 밝기 변화(정전·빛이 빠짐·밤)를 노출 키로: 애니매틱 기본값(키 1.6·반구 0.4·환경 0.35)을 0으로
# (밝기 변화는 노출이 아니라 조명 세기로 — 노출로 하면 하늘·화면처럼 스스로 빛나는 것까지 어두워짐)
print('색:', vs.view_transform, vs.look)
# 빛 번짐(글레어) — 버전에 따라 API가 달라, 실패하면 합성 없이 그대로
def glare_setup():
    if hasattr(sc, 'compositing_node_group'):                     # Blender 5.x: 합성은 노드 그룹
        ng = bpy.data.node_groups.new('HeartComp', 'CompositorNodeTree')
        ng.interface.new_socket('Image', in_out='OUTPUT', socket_type='NodeSocketColor')
        rl = ng.nodes.new('CompositorNodeRLayers'); gl = ng.nodes.new('CompositorNodeGlare'); out = ng.nodes.new('NodeGroupOutput')
        if 'Type' in gl.inputs: gl.inputs['Type'].default_value = 'Bloom'
        for nm, v in (('Threshold', 0.85), ('Strength', 0.6), ('Size', 0.7)):   # 애니매틱(UnrealBloom 0.92 문턱, 넓은 번짐)에 가깝게
            if nm in gl.inputs:
                try: gl.inputs[nm].default_value = v
                except Exception: pass
        src = rl.outputs['Image']
        fogk = float(opt.get('fog', '0.6' if meta.get('set') == 'nook' else '0.15'))   # 공기 원근: 애니매틱과 같은 거리(near~far). 바깥(갈빗대 휴가지)은 60%로 먼 바다 끝이 하늘에 녹게, 실내는 15%만(짙으면 뿌옇게 바램)
        if fogk > 0 and atmo.get('near') is not None:
            sc.view_layers[0].use_pass_mist = True
            ms = sc.world.mist_settings; ms.start = atmo['near']; ms.depth = atmo['far'] - atmo['near']; ms.falloff = 'LINEAR'
            fc_ = hexrgb(atmo.get('fog'))
            mul = ng.nodes.new('ShaderNodeMath'); mul.operation = 'MULTIPLY'; mul.inputs[1].default_value = fogk
            ng.links.new(rl.outputs['Mist'], mul.inputs[0])
            mix = ng.nodes.new('ShaderNodeMix'); mix.data_type = 'RGBA'
            ng.links.new(mul.outputs[0], mix.inputs['Factor']); ng.links.new(src, mix.inputs[6]); mix.inputs[7].default_value = (*fc_, 1)
            src = mix.outputs[2]
        ng.links.new(src, gl.inputs['Image']); ng.links.new(gl.outputs['Image'], out.inputs['Image'])
        sc.compositing_node_group = ng
        if 'Strength' in gl.inputs:                                # 애니매틱 빛 번짐 세기 변화(경보 등)를 키로
            for f, L in enumerate(meta['light']):
                gl.inputs['Strength'].default_value = 0.6 * L.get('bloom', 0.5) / 0.5
                gl.inputs['Strength'].keyframe_insert('default_value', frame=F0 + f)
    else:                                                          # 4.x
        sc.use_nodes = True; tr = sc.node_tree; rl = tr.nodes.get('Render Layers'); co = tr.nodes.get('Composite')
        gl = tr.nodes.new('CompositorNodeGlare')
        try: gl.glare_type = 'BLOOM'
        except Exception: gl.glare_type = 'FOG_GLOW'
        gl.threshold = 1.0; tr.links.new(rl.outputs['Image'], gl.inputs['Image']); tr.links.new(gl.outputs['Image'], co.inputs['Image'])
try: glare_setup()
except Exception as e:
    print('글레어 건너뜀:', e)
    try: sc.compositing_node_group = None
    except Exception: pass

os.makedirs(opt['out'], exist_ok=True)
r.filepath = os.path.join(opt['out'], CUT, '')
r.image_settings.file_format = 'PNG'
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(opt['out'], f'{CUT}.blend'))
print(f'saved {CUT}.blend  frames {sc.frame_start}-{sc.frame_end}  (애니매틱 0프레임 = Blender {F0})')
if 'render' in flags:
    if opt.get('framelist'):                       # 몇 프레임만 골라 다시 그리기(애니매틱 프레임 번호, 0부터, 쉼표로)
        for f in [int(x) for x in opt['framelist'].split(',') if x.strip()]:
            sc.frame_set(F0 + f); r.filepath = os.path.join(opt['out'], CUT, f'{F0 + f:04d}.png')
            bpy.ops.render.render(write_still=True); print('saved frame', F0 + f)
    else:
        bpy.ops.render.render(animation=True)
