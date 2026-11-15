// 심장 연기 샘플 GPU 렌더 키트 — 사용자 그래픽카드로 경로 추적해 PNG 저장
import * as THREE from 'three';
import { WebGLPathTracer, PhysicalCamera } from 'three-gpu-pathtracer';
import { buildHeart } from './heart.js';
import { buildSet } from './set.js';
import { poseAt, DUR } from './act.js';

const $ = id => document.getElementById(id);
const log = s => { $('log').textContent = s; };
const qs = new URLSearchParams(location.search);
const W = +(qs.get('w') || 1920), H = +(qs.get('h') || 1080), FPS = 24;
let dir = null, stop = false;

const renderer = new THREE.WebGLRenderer({ antialias: false, preserveDrawingBuffer: true, powerPreference: 'high-performance' });
renderer.setPixelRatio(1); renderer.setSize(W, H, false);
renderer.toneMapping = THREE.NeutralToneMapping; renderer.toneMappingExposure = 1.0; renderer.outputColorSpace = THREE.SRGBColorSpace;
$('stage').appendChild(renderer.domElement);
const gl = renderer.getContext(); const dbg = gl.getExtension('WEBGL_debug_renderer_info');
$('gpu').textContent = dbg ? gl.getParameter(dbg.UNMASKED_RENDERER_WEBGL) : '(GPU 이름을 읽을 수 없음)';

const scene = new THREE.Scene(); scene.background = new THREE.Color('#D8D0F0');
const floor = new THREE.Mesh(new THREE.PlaneGeometry(60, 60), new THREE.MeshStandardMaterial({ color: '#D8D0F0', roughness: 0.95 }));
floor.rotation.x = -Math.PI / 2; scene.add(floor);
const { set } = buildSet(); scene.add(set);
// 하늘빛(부드러운 채움) + 따뜻한 키 + 차가운 림
{ const w = 256, h = 128, data = new Float32Array(w * h * 4);
  for (let y = 0; y < h; y++) for (let x = 0; x < w; x++) { const up = y / h, i = (y * w + x) * 4; const c = up > 0.5 ? [0.96, 0.94, 1.0] : [0.73, 0.66, 0.85]; data.set([c[0], c[1], c[2], 1], i); }
  const t = new THREE.DataTexture(data, w, h, THREE.RGBAFormat, THREE.FloatType); t.mapping = THREE.EquirectangularReflectionMapping; t.needsUpdate = true;
  scene.environment = t; scene.environmentIntensity = 0.75; }
const key = new THREE.DirectionalLight('#fff1e2', 2.6); key.position.set(-2.2, 3.4, 3.0); scene.add(key);
const rim = new THREE.DirectionalLight('#cfe0ff', 1.6); rim.position.set(2.5, 2.2, -2.5); scene.add(rim);

const rig = await buildHeart({ bodyUrl: window.HEART_GLB }); scene.add(rig.root);
const pc = new PhysicalCamera(30, W / H, 0.05, 60); pc.position.set(0.3, 0.95, 4.2); pc.lookAt(0.3, 0.66, 0);
pc.fStop = 5.6; pc.focusDistance = 3.85; pc.apertureBlades = 6;
const pt = new WebGLPathTracer(renderer);
pt.tiles.set(2, 2); pt.minSamples = 1; pt.renderDelay = 0; pt.fadeDuration = 0; pt.bounces = 6; pt.filterGlossyFactor = 0.5; pt.renderToCanvas = true;

async function frame(t, samples) {
  const a = poseAt(t); rig.setFace(a.mood, a.look, a.blink); rig.pose(a.pose);
  renderer.setSize(W, H, false); pc.aspect = W / H; pc.updateProjectionMatrix(); scene.updateMatrixWorld(true);
  pt.setScene(scene, pc);
  while (pt.samples < samples) { pt.renderSample(); if (Math.floor(pt.samples) % 4 === 0) await new Promise(r => requestAnimationFrame(r)); }
}
async function exists(d, name) { try { return (await (await d.getFileHandle(name)).getFile()).size > 0; } catch { return false; } }
async function save(d, name) {
  const blob = await new Promise(r => renderer.domElement.toBlob(r, 'image/png'));
  const fh = await d.getFileHandle(name, { create: true }); const w = await fh.createWritable(); await w.write(blob); await w.close();
}
$('pick').onclick = async () => {
  try { dir = await window.showDirectoryPicker({ mode: 'readwrite' }); $('dirname').textContent = dir.name; $('go1').disabled = $('go2').disabled = false; }
  catch (e) { log('폴더를 고르지 않았습니다: ' + e.message); }
};
$('stop').onclick = () => { stop = true; log('이번 프레임까지 그리고 멈춥니다…'); };
async function run(frames, label) {
  $('go1').disabled = $('go2').disabled = true; $('stop').disabled = false; stop = false;
  const samples = +$('spp').value, d = await (await dir.getDirectoryHandle('heart_v2_pt' + samples, { create: true })).getDirectoryHandle(label, { create: true });
  let done = 0, ms = 0, drawn = 0;
  for (const k of frames) {
    if (stop) break; const name = `f${String(k).padStart(4, '0')}.png`;
    if (await exists(d, name)) { done++; continue; }
    const t0 = performance.now(); await frame(k / FPS, samples); await save(d, name); ms += performance.now() - t0; drawn++; done++;
    log(`${done}/${frames.length} 프레임 · 이번 ${((performance.now() - t0) / 1000).toFixed(1)}초 · 남은 시간 약 ${((frames.length - done) * ms / drawn / 60000).toFixed(0)}분`);
  }
  log(stop ? `멈췄습니다(${done}/${frames.length}). 다시 누르면 이어서 그립니다.` : `끝났습니다. "${dir.name}/heart_v2_pt${samples}/${label}" 폴더에 ${frames.length}장. 평균 ${drawn ? (ms / drawn / 1000).toFixed(1) : '-'}초/프레임.`);
  $('go1').disabled = $('go2').disabled = false; $('stop').disabled = true;
}
// 정지 화면 4장: 기본 / 발끝 뻗기 / 점프 꼭대기 / "아!"
$('go1').onclick = () => run([7, 29, 43, 100], 'stills');
$('go2').onclick = () => run([...Array(Math.round(DUR * FPS)).keys()], 'clip');
if (!window.showDirectoryPicker) log('이 브라우저는 폴더 저장을 지원하지 않습니다. Chrome이나 Edge로 열어 주세요.');
const m = location.hash.match(/#test-([\d.]+)-(\d+)/);   // 시험용: #test-<t>-<spp>
if (m) { await frame(+m[1], +m[2]); document.title = 'DONE'; }
