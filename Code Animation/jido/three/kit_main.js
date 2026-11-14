// 〈지도〉 GPU 렌더 키트: 사용자의 컴퓨터 브라우저(GPU)로 프레임을 그려 고른 폴더에 PNG로 저장한다.
import * as THREE from 'three';
import { RoomEnvironment } from 'three/addons/environments/RoomEnvironment.js';
import { EffectComposer } from 'three/addons/postprocessing/EffectComposer.js';
import { RenderPass } from 'three/addons/postprocessing/RenderPass.js';
import { GTAOPass } from 'three/addons/postprocessing/GTAOPass.js';
import { BokehPass } from 'three/addons/postprocessing/BokehPass.js';
import { UnrealBloomPass } from 'three/addons/postprocessing/UnrealBloomPass.js';
import { OutputPass } from 'three/addons/postprocessing/OutputPass.js';
import { WebGLPathTracer, PhysicalCamera } from 'three-gpu-pathtracer';
import { build, animate, CAM, SUN, focusAt, DUR } from './scene.js';

const $ = id => document.getElementById(id);
const log = s => { $('log').textContent = s; };
let dir = null;

const W = 1920, H = 1080, FPS = 24;
const renderer = new THREE.WebGLRenderer({ antialias: true, preserveDrawingBuffer: true, powerPreference: 'high-performance' });
renderer.setPixelRatio(1); renderer.setSize(W, H, false);
renderer.toneMapping = THREE.AgXToneMapping; renderer.toneMappingExposure = 0.85;
renderer.outputColorSpace = THREE.SRGBColorSpace;
renderer.domElement.id = 'view'; $('stage').appendChild(renderer.domElement);
const gl = renderer.getContext(); const dbg = gl.getExtension('WEBGL_debug_renderer_info');
$('gpu').textContent = dbg ? gl.getParameter(dbg.UNMASKED_RENDERER_WEBGL) : '(GPU 이름을 읽을 수 없음)';

const scene = build();
const camera = new THREE.PerspectiveCamera(CAM.fov, W / H, 0.02, 30);
camera.position.set(...CAM.pos); camera.lookAt(...CAM.target);
const sunDir = new THREE.Vector3(...SUN.dir).normalize();
const sun = new THREE.DirectionalLight(SUN.color, SUN.intensity);
sun.target.position.set(-0.9, 0, -0.9); sun.position.copy(sun.target.position).addScaledVector(sunDir, 6);
scene.add(sun, sun.target);

function skyTex() {
  const w = 512, h = 256, data = new Float32Array(w * h * 4);
  for (let y = 0; y < h; y++) for (let x = 0; x < w; x++) {
    const v = 1 - y / h, el = (v - 0.5) * Math.PI, i = (y * w + x) * 4; let c;
    if (el > 0) { const k = Math.pow(1 - el / (Math.PI / 2), 3); c = [0.55 + 0.45 * k, 0.72 + 0.25 * k, 1.0].map(q => q * (1.2 + 0.8 * k)); }
    else c = [0.42, 0.34, 0.26];
    data.set([c[0], c[1], c[2], 1], i);
  }
  const t = new THREE.DataTexture(data, w, h, THREE.RGBAFormat, THREE.FloatType);
  t.mapping = THREE.EquirectangularReflectionMapping; t.needsUpdate = true; return t;
}

// ---------------- 실시간 고급
let comp = null, bokeh = null, rasterExtras = null;
function setupRaster() {
  const pm = new THREE.PMREMGenerator(renderer);
  scene.environment = pm.fromScene(new RoomEnvironment(), 0.04).texture; scene.environmentIntensity = 0.12;
  scene.background = new THREE.Color('#0d0b0a');
  renderer.shadowMap.enabled = true; renderer.shadowMap.type = THREE.VSMShadowMap;
  sun.castShadow = true; sun.shadow.mapSize.set(4096, 4096); sun.shadow.radius = 6; sun.shadow.blurSamples = 16; sun.shadow.bias = -0.0003;
  const sc = sun.shadow.camera; sc.left = -3; sc.right = 3; sc.top = 3; sc.bottom = -3; sc.near = 0.5; sc.far = 14;
  if (!rasterExtras) { rasterExtras = [new THREE.HemisphereLight('#bcd2ff', '#7a4a2a', 0.12)]; rasterExtras.forEach(l => scene.add(l)); }
  comp = new EffectComposer(renderer); comp.setSize(W, H);
  comp.addPass(new RenderPass(scene, camera));
  const ao = new GTAOPass(scene, camera, W, H);
  ao.updateGtaoMaterial({ radius: 0.25, distanceExponent: 1.2, thickness: 2.5, scale: 1.6, samples: 16 }); comp.addPass(ao);
  comp.addPass(new UnrealBloomPass(new THREE.Vector2(W, H), 0.35, 0.6, 0.85));
  bokeh = new BokehPass(scene, camera, { focus: CAM.focus, aperture: 0.0025, maxblur: 0.006 }); comp.addPass(bokeh);
  comp.addPass(new OutputPass());
}
async function frameRaster(t) { animate(scene, t); bokeh.uniforms.focus.value = focusAt(scene, camera); comp.render(); }

// ---------------- 경로 추적
let pt = null, pc = null;
function setupPT() {
  if (rasterExtras) { rasterExtras.forEach(l => scene.remove(l)); rasterExtras = null; }
  renderer.shadowMap.enabled = false;
  pc = new PhysicalCamera(CAM.fov, W / H, 0.02, 30);
  pc.position.copy(camera.position); pc.quaternion.copy(camera.quaternion); pc.updateProjectionMatrix();
  pc.fStop = CAM.fStop; pc.apertureBlades = 6;
  scene.environment = skyTex(); scene.environmentIntensity = 1.0; scene.background = new THREE.Color('#0d0b0a');
  pt = new WebGLPathTracer(renderer);
  pt.tiles.set(2, 2); pt.minSamples = 1; pt.renderDelay = 0; pt.fadeDuration = 0; pt.bounces = 6; pt.filterGlossyFactor = 0.5;
  pt.renderToCanvas = true;
}
async function framePT(t, samples) {
  animate(scene, t); scene.updateMatrixWorld(true); pc.focusDistance = focusAt(scene, pc);
  renderer.setSize(W, H, false); pc.aspect = W / H; pc.updateProjectionMatrix();
  pt.setScene(scene, pc);
  while (pt.samples < samples) { pt.renderSample(); if (Math.floor(pt.samples) % 4 === 0) await new Promise(r => requestAnimationFrame(r)); }
}

async function save(sub, name) {
  const d = await dir.getDirectoryHandle(sub, { create: true });
  const blob = await new Promise(r => renderer.domElement.toBlob(r, 'image/png'));
  const fh = await d.getFileHandle(name, { create: true }); const w = await fh.createWritable(); await w.write(blob); await w.close();
}
async function writeText(name, text) { const fh = await dir.getFileHandle(name, { create: true }); const w = await fh.createWritable(); await w.write(text); await w.close(); }

$('pick').onclick = async () => {
  try { dir = await window.showDirectoryPicker({ mode: 'readwrite' }); $('dirname').textContent = dir.name; $('go1').disabled = $('go2').disabled = false; }
  catch (e) { log('폴더를 고르지 않았습니다: ' + e.message); }
};
async function run(kind) {
  $('go1').disabled = $('go2').disabled = true;
  const samples = +$('spp').value, n = Math.round(DUR * FPS), times = [];
  if (kind === 'raster') setupRaster(); else setupPT();
  for (let k = 0; k < n; k++) {
    const t0 = performance.now();
    if (kind === 'raster') await frameRaster(k / FPS); else await framePT(k / FPS, samples);
    await save(kind, `f${String(k).padStart(4, '0')}.png`);
    const ms = performance.now() - t0; times.push(ms);
    log(`${kind === 'raster' ? '실시간' : '경로 추적 ' + samples + '샘플'}: ${k + 1}/${n} 프레임, 이번 프레임 ${(ms / 1000).toFixed(1)}초`);
  }
  await writeText(`${kind}_timing.json`, JSON.stringify({ gpu: $('gpu').textContent, kind, samples, frames: n, ms: times }, null, 1));
  log(`끝났습니다. "${dir.name}" 폴더의 ${kind} 폴더에 ${n}장이 저장됐습니다. 평균 ${(times.reduce((a, b) => a + b, 0) / n / 1000).toFixed(1)}초/프레임. 페이지를 새로 고친 뒤 다른 방식도 돌릴 수 있습니다.`);
}
$('go1').onclick = () => run('raster');
$('go2').onclick = () => run('pt');
if (!window.showDirectoryPicker) log('이 브라우저는 폴더 저장을 지원하지 않습니다. Chrome이나 Edge로 열어 주세요.');
// 시험용: 주소 끝에 #test-raster 또는 #test-pt-8 을 붙이면 1.6초 프레임 한 장만 그린다(저장 없음)
if (location.hash.startsWith('#test-')) (async () => {
  const pts = location.hash.match(/#test-pt-(\d+)/);
  if (pts) { setupPT(); await framePT(1.6, +pts[1]); } else { setupRaster(); await frameRaster(1.6); }
  document.title = 'DONE';
})();
