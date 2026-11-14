"""PNG 시퀀스 → H.264 mp4 (Blender 시퀀서로). blender -b -P encode_seq.py -- <png_dir> <out.mp4> [fps]"""
import bpy, sys, os, glob
argv = sys.argv[sys.argv.index('--') + 1:]
src, out = argv[0], argv[1]; fps = int(argv[2]) if len(argv) > 2 else 24
files = sorted(glob.glob(os.path.join(src, '*.png')))
if not files: print('no frames'); sys.exit(1)
sc = bpy.context.scene
sc.render.fps = fps
img = bpy.data.images.load(files[0]); w, h = img.size; bpy.data.images.remove(img)
sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage = w, h, 100
se = sc.sequence_editor_create()
coll = se.strips if hasattr(se, 'strips') else se.sequences
st = coll.new_image(name='seq', filepath=files[0], channel=1, frame_start=1)
for f in files[1:]: st.elements.append(os.path.basename(f))
sc.frame_start, sc.frame_end = 1, len(files)
r = sc.render
if hasattr(r.image_settings, 'media_type'): r.image_settings.media_type = 'VIDEO'   # Blender 5.x
r.image_settings.file_format = 'FFMPEG'
ff = r.ffmpeg; ff.format = 'MPEG4'; ff.codec = 'H264'; ff.constant_rate_factor = 'HIGH'; ff.ffmpeg_preset = 'GOOD'; ff.audio_codec = 'NONE'
try: sc.view_settings.view_transform = 'Standard'          # 이미 색 처리된 PNG를 다시 바꾸지 않게
except Exception: pass
r.filepath = out
bpy.ops.render.render(animation=True)
print('encoded', out, len(files))
