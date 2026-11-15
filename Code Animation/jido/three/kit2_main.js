// 〈지도〉 GPU 렌더 키트 v2 — 애니매틱 3D 컷(shots.js)을 사용자 그래픽카드로 경로 추적해 PNG로 저장
import * as THREE from 'three';
import { WebGLPathTracer, PhysicalCamera } from 'three-gpu-pathtracer';
import { build } from './scene.js';
import { addProps, shotPose, SHOTS } from './shots.js';

const $ = id => document.getElementById(id);
const log = s => { $('log').textContent = s; };
const qs = new URLSearchParams(location.search);
const W = +(qs.get('w') || 1920), H = +(qs.get('h') || 1080), FPS = 24;
let dir = null, stop = false;

const renderer = new THREE.WebGLRenderer({ antialias: false, preserveDrawingBuffer: true, powerPreference: 'high-performance' });
renderer.setPixelRatio(1); renderer.setSize(W, H, false);
renderer.toneMapping = THREE.AgXToneMapping; renderer.outputColorSpace = THREE.SRGBColorSpace;
$('stage').appendChild(renderer.domElement);
const gl = renderer.getContext(); const dbg = gl.getExtension('WEBGL_debug_renderer_info');
$('gpu').textContent = dbg ? gl.getParameter(dbg.UNMASKED_RENDERER_WEBGL) : '(GPU 이름을 읽을 수 없음)';

const scene = build(); const S = scene.userData.S; const P = addProps(scene);
const sun = new THREE.DirectionalLight('#ffc884', 10); scene.add(sun, sun.target);
const hemi = new THREE.HemisphereLight('#bcd2ff', '#7a4a2a', 0.12); scene.add(hemi);
scene.background = new THREE.Color('#0d0b0a');

// anim.html 미리보기와 같은 조명표(env는 하늘 텍스처 기준으로 환산)
const LIGHTS = {
  dawn:      { sun: ['#ff9050', 9, [-1, 0.88, 0.94]], hemi: 0.025, env: 0.025, exp: 1.0 },
  morning:   { sun: ['#ffc884', 10, [-1, 1.05, -0.12]], hemi: 0.12, env: 0.12, exp: 0.85 },
  afternoon: { sun: ['#ffb36a', 9, [-1, 0.7, 0.15]], hemi: 0.1, env: 0.1, exp: 0.85 },
  night:     { sun: ['#7d95ff', 0.8, [-1, 0.8, -0.1]], hemi: 0.02, env: 0.01, exp: 0.95, lamp: 1.4 },
  door:      { sun: ['#7d95ff', 0.25, [-1, 0.8, -0.1]], hemi: 0.02, env: 0.01, exp: 1.0, doorSpot: 14 },
  corridor:  { sun: ['#000000', 0, [-1, 1, 0]], hemi: 0.006, env: 0.004, exp: 1.0, corr: 1.0, vac: 2.5 },
  corridor_home: { sun: ['#000000', 0, [-1, 1, 0]], hemi: 0.006, env: 0.004, exp: 1.0, corr: 0.7, home: 4, vac: 2.5 },
  newroom:   { sun: ['#ffe2bc', 4, [-0.6, 0.7, 0.5]], hemi: 0.05, env: 0.05, exp: 0.85, newl: 1.2 },
};
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
scene.environment = skyTex();
function applyLight(id, focusPos) {
  const L = LIGHTS[id];
  sun.color.set(L.sun[0]); sun.intensity = L.sun[1];
  const d = new THREE.Vector3(...L.sun[2]).normalize();
  sun.target.position.copy(focusPos).setY(0); sun.position.copy(sun.target.position).addScaledVector(d, 6);
  hemi.intensity = L.hemi; scene.environmentIntensity = L.env / 0.12; renderer.toneMappingExposure = L.exp;
  P.lamp.intensity = L.lamp || 0; P.doorSpot.intensity = L.doorSpot || 0; P.corrLight.intensity = L.corr || 0; P.homeDoor.intensity = L.home || 0; P.newLight.intensity = L.newl || 0; P.vacLight.intensity = L.vac || 0;
  for (const l of [P.lamp, P.doorSpot, P.corrLight, P.homeDoor, P.newLight, P.vacLight]) l.visible = l.intensity > 0;
  sun.visible = sun.intensity > 0;
}

const pc = new PhysicalCamera(36, W / H, 0.02, 40); pc.fStop = 2.8; pc.apertureBlades = 6;
const pt = new WebGLPathTracer(renderer);
pt.tiles.set(2, 2); pt.minSamples = 1; pt.renderDelay = 0; pt.fadeDuration = 0; pt.bounces = 6; pt.filterGlossyFactor = 0.5; pt.renderToCanvas = true;

async function frame(id, t, samples) {
  const r = shotPose(S, id, t);
  pc.fov = r.cam.fov; pc.position.set(...r.cam.pos); pc.lookAt(...r.cam.target);
  renderer.setSize(W, H, false); pc.aspect = W / H; pc.updateProjectionMatrix();
  applyLight(SHOTS[id].light, new THREE.Vector3(...r.cam.target));
  scene.updateMatrixWorld(true);
  pc.focusDistance = S.vac.position.clone().setY(0.06).distanceTo(pc.position);
  pt.setScene(scene, pc);
  while (pt.samples < samples) { pt.renderSample(); if (Math.floor(pt.samples) % 4 === 0) await new Promise(r => requestAnimationFrame(r)); }
}
async function exists(d, name) { try { const f = await (await d.getFileHandle(name)).getFile(); return f.size > 0; } catch { return false; } }
async function save(d, name) {
  const blob = await new Promise(r => renderer.domElement.toBlob(r, 'image/png'));
  const fh = await d.getFileHandle(name, { create: true }); const w = await fh.createWritable(); await w.write(blob); await w.close();
}

const ORDER = Object.keys(SHOTS);
for (const id of ORDER) { const o = document.createElement('option'); o.value = id; o.textContent = `${id} (${SHOTS[id].dur}초, ${SHOTS[id].dur * FPS}프레임)`; $('shot').appendChild(o); }
const total = ORDER.reduce((a, id) => a + SHOTS[id].dur * FPS, 0);
$('allopt').textContent = `전체 ${ORDER.length}컷 순서대로 (${total}프레임)`;

$('pick').onclick = async () => {
  try { dir = await window.showDirectoryPicker({ mode: 'readwrite' }); $('dirname').textContent = dir.name; $('go').disabled = false; }
  catch (e) { log('폴더를 고르지 않았습니다: ' + e.message); }
};
$('stop').onclick = () => { stop = true; log('이번 프레임까지 그리고 멈춥니다…'); };
$('go').onclick = async () => {
  $('go').disabled = true; $('stop').disabled = false; stop = false;
  const samples = +$('spp').value, sel = $('shot').value, list = sel === 'all' ? ORDER : [sel];
  const root = await dir.getDirectoryHandle(`pt${samples}`, { create: true });
  let done = 0, skipped = 0, msSum = 0, nDrawn = 0;
  const need = list.reduce((a, id) => a + SHOTS[id].dur * FPS, 0);
  for (const id of list) {
    const d = await root.getDirectoryHandle(id, { create: true }), n = SHOTS[id].dur * FPS;
    for (let k = 0; k < n; k++) {
      if (stop) break;
      const name = `f${String(k).padStart(4, '0')}.png`;
      if (await exists(d, name)) { done++; skipped++; continue; }
      const t0 = performance.now();
      await frame(id, k / FPS, samples); await save(d, name);
      const ms = performance.now() - t0; msSum += ms; nDrawn++; done++;
      const left = (need - done) * msSum / nDrawn / 3.6e6;
      log(`${id} ${k + 1}/${n} · 전체 ${done}/${need} · 이번 ${(ms / 1000).toFixed(1)}초 · 남은 시간 약 ${left.toFixed(1)}시간`);
    }
    if (stop) break;
  }
  log(stop ? `멈췄습니다(${done}/${need}). 다시 누르면 이어서 그립니다.` : `끝났습니다. "${dir.name}/pt${samples}" 폴더에 컷별로 저장됐습니다${skipped ? ` (이미 있던 ${skipped}장은 건너뜀)` : ''}.`);
  $('go').disabled = false; $('stop').disabled = true;
};
if (!window.showDirectoryPicker) log('이 브라우저는 폴더 저장을 지원하지 않습니다. Chrome이나 Edge로 열어 주세요.');
// 시험용: #test-<shot>-<t>-<spp>  (저장 없음)
const m = location.hash.match(/#test-(\w+)-([\d.]+)-(\d+)/);
if (m) (async () => { await frame(m[1], +m[2], +m[3]); document.title = 'DONE'; })();
