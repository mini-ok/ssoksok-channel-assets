// 〈지도〉 3D 시험 컷 v2: 아침 거실 바닥 7cm 높이. 청소기가 다가오다 슬리퍼 앞에서 멈칫하고 비켜 간다(4초).
import * as THREE from 'three';
import { RoundedBoxGeometry } from 'three/addons/geometries/RoundedBoxGeometry.js';

export const DUR = 4.0;

// ---------------------------------------------------------------- 절차 텍스처
export function rnd(seed) { return () => { seed = (seed * 16807) % 2147483647; return (seed - 1) / 2147483646; }; }
function tex(c, srgb, rep) {
  const t = new THREE.CanvasTexture(c); t.wrapS = t.wrapT = THREE.RepeatWrapping; t.anisotropy = 8;
  if (srgb) t.colorSpace = THREE.SRGBColorSpace; if (rep) t.repeat.set(rep[0], rep[1]); return t;
}
function canvas(w, h, draw) { const c = document.createElement('canvas'); c.width = w; c.height = h; draw(c.getContext('2d'), w, h); return c; }
// 높이 캔버스 → 법선 맵
function normalFrom(hc, strength) {
  const w = hc.width, h = hc.height, src = hc.getContext('2d').getImageData(0, 0, w, h).data;
  const out = document.createElement('canvas'); out.width = w; out.height = h;
  const g = out.getContext('2d'), img = g.createImageData(w, h), d = img.data;
  const H = (x, y) => src[(((y + h) % h) * w + ((x + w) % w)) * 4] / 255;
  for (let y = 0; y < h; y++) for (let x = 0; x < w; x++) {
    const dx = (H(x + 1, y) - H(x - 1, y)) * strength, dy = (H(x, y + 1) - H(x, y - 1)) * strength;
    const l = Math.hypot(dx, dy, 1), i = (y * w + x) * 4;
    d[i] = (-dx / l * 0.5 + 0.5) * 255; d[i + 1] = (dy / l * 0.5 + 0.5) * 255; d[i + 2] = (1 / l * 0.5 + 0.5) * 255; d[i + 3] = 255;
  }
  g.putImageData(img, 0, 0); return out;
}

function woodFloor() {
  const R = rnd(11), PW = 96, PL = 1024;
  const plan = [];
  for (let x = 0; x < 1024; x += PW) { const off = Math.floor(R() * PL); for (let y = -off; y < 1024; y += PL) plan.push([x, y, R(), R(), R()]); }
  const col = canvas(1024, 1024, (g) => {
    for (const [x, y, a, b, c] of plan) {
      g.fillStyle = `rgb(${Math.round(176 + a * 34)},${Math.round(112 + b * 24)},${Math.round(64 + c * 18)})`; g.fillRect(x, y, PW, PL);
      const r2 = rnd(Math.floor(a * 1e6) + 7);
      for (let k = 0; k < 70; k++) {
        const gx = x + r2() * PW; g.strokeStyle = `rgba(90,48,20,${0.04 + r2() * 0.08})`; g.lineWidth = 0.6 + r2() * 1.8;
        g.beginPath(); g.moveTo(gx, y); g.bezierCurveTo(gx + (r2() - .5) * 14, y + PL * .33, gx + (r2() - .5) * 14, y + PL * .66, gx + (r2() - .5) * 8, y + PL); g.stroke();
      }
      if (a > 0.7) { g.fillStyle = 'rgba(80,40,15,0.25)'; g.beginPath(); g.ellipse(x + PW * b, y + PL * c, 6, 14, 0, 0, 7); g.fill(); }
    }
  });
  const hgt = canvas(512, 512, (g) => {
    g.fillStyle = '#fff'; g.fillRect(0, 0, 512, 512); g.fillStyle = '#000';
    for (const [x, y] of plan) { g.fillRect(x / 2, y / 2, PW / 2, 1.2); g.fillRect(x / 2, y / 2, 1.2, PL / 2); }
  });
  const rough = canvas(256, 256, (g) => { const r = rnd(3); g.fillStyle = '#9a9a9a'; g.fillRect(0, 0, 256, 256); for (let k = 0; k < 3000; k++) { const v = Math.round(110 + r() * 110); g.fillStyle = `rgba(${v},${v},${v},0.25)`; g.fillRect(r() * 256, r() * 256, 2 + r() * 14, 1 + r() * 2); } });
  const rep = [9, 4.5];
  return new THREE.MeshPhysicalMaterial({ map: tex(col, true, rep), normalMap: tex(normalFrom(hgt, 4), false, rep), normalScale: new THREE.Vector2(0.8, 0.8),
    roughnessMap: tex(rough, false, [14, 14]), roughness: 0.6, clearcoat: 0.15, clearcoatRoughness: 0.35 });
}
// 뜨개 무늬: 슬리퍼·양말
export function knit(hex, seed, rep, sheen = 1) {
  const c = new THREE.Color(hex), R = rnd(seed);
  const hgt = canvas(256, 256, (g) => {
    g.fillStyle = '#000'; g.fillRect(0, 0, 256, 256);
    for (let y = 0; y < 256; y += 16) for (let x = 0; x < 256; x += 16) {
      for (const [ox, rot] of [[4, 0.5], [12, -0.5]]) {
        const gr = g.createRadialGradient(0, 0, 1, 0, 0, 8); gr.addColorStop(0, '#fff'); gr.addColorStop(1, '#000');
        g.save(); g.translate(x + ox, y + 8); g.rotate(rot); g.scale(0.55, 1); g.beginPath(); g.arc(0, 0, 8, 0, 7); g.fillStyle = gr; g.fill(); g.restore();
      }
    }
  });
  const col = canvas(256, 256, (g) => {
    g.fillStyle = '#' + c.getHexString(); g.fillRect(0, 0, 256, 256);
    g.globalCompositeOperation = 'multiply'; g.globalAlpha = 0.5;
    const inv = canvas(256, 256, (h) => { h.drawImage(hgt, 0, 0); h.globalCompositeOperation = 'difference'; h.fillStyle = '#fff'; h.fillRect(0, 0, 256, 256); });
    g.drawImage(inv, 0, 0); g.globalAlpha = 1; g.globalCompositeOperation = 'source-over';
    g.globalCompositeOperation = 'screen'; g.globalAlpha = 0.25; g.drawImage(hgt, 0, 0); g.globalAlpha = 1; g.globalCompositeOperation = 'source-over';
    for (let k = 0; k < 1500; k++) { g.fillStyle = `rgba(0,0,0,${R() * 0.08})`; g.fillRect(R() * 256, R() * 256, 1, 1); }
  });
  return new THREE.MeshPhysicalMaterial({ map: tex(col, true, rep), normalMap: tex(normalFrom(hgt, 3), false, rep), normalScale: new THREE.Vector2(1.2, 1.2),
    roughness: 0.95, sheen: sheen, sheenRoughness: 0.5, sheenColor: c.clone().lerp(new THREE.Color(1, 1, 1), 0.5) });
}
export function fabric(hex, seed, rep = [6, 6]) {
  const c = new THREE.Color(hex), R = rnd(seed);
  const hgt = canvas(256, 256, (g) => { g.fillStyle = '#808080'; g.fillRect(0, 0, 256, 256); for (let y = 0; y < 256; y += 2) for (let x = 0; x < 256; x += 2) { const v = Math.round(128 + (R() - .5) * 90 + ((x + y) % 4 ? 20 : -20)); g.fillStyle = `rgb(${v},${v},${v})`; g.fillRect(x, y, 2, 2); } });
  return new THREE.MeshPhysicalMaterial({ color: c, normalMap: tex(normalFrom(hgt, 1.5), false, rep), roughness: 0.92, sheen: 1, sheenRoughness: 0.55, sheenColor: c.clone().lerp(new THREE.Color(1, 1, 1), 0.45) });
}
function rugMat() {
  const col = canvas(1024, 1024, (g, w, h) => {
    g.fillStyle = '#ece0c8'; g.fillRect(0, 0, w, h);
    const cols = ['#c66f4a', '#3f6d6b', '#e2b35a'];
    for (let i = 0; i < 9; i++) { g.fillStyle = cols[i % 3]; g.fillRect(0, 60 + i * 105, w, 20 + (i % 2) * 16); }
    const R = rnd(5); for (let k = 0; k < 50000; k++) { g.fillStyle = `rgba(60,40,20,${R() * 0.06})`; g.fillRect(R() * w, R() * h, 2, 2); }
  });
  const m = fabric('#ffffff', 77, [10, 10]); m.map = tex(col, true); m.sheenColor.set('#fff1dc'); return m;
}

// ---------------------------------------------------------------- 모양 도우미
export function lathe(points, seg = 64) { return new THREE.LatheGeometry(points.map(p => new THREE.Vector2(p[0], p[1])), seg); }
export function smoothPts(P, n = 8) {
  const out = [];
  for (let i = 0; i < P.length - 1; i++) {
    const a = P[Math.max(0, i - 1)], b = P[i], c = P[i + 1], d = P[Math.min(P.length - 1, i + 2)];
    for (let k = 0; k < n; k++) { const u = k / n; out.push([0, 1].map(j => 0.5 * (2 * b[j] + (-a[j] + c[j]) * u + (2 * a[j] - 5 * b[j] + 4 * c[j] - d[j]) * u * u + (-a[j] + 3 * b[j] - 3 * c[j] + d[j]) * u ** 3))); }
  }
  out.push(P[P.length - 1]); return out;
}
// 슬리퍼: 발 모양으로 부풀린 몸통(뒤꿈치 낮고 발등 볼록)
export function slipperGeo() {
  const g = new THREE.SphereGeometry(1, 72, 40), p = g.attributes.position, v = new THREE.Vector3();
  for (let i = 0; i < p.count; i++) {
    v.fromBufferAttribute(p, i);
    const z = v.z;
    const wid = 0.044 * (0.86 + 0.18 * Math.sin((z + 1) * 1.45)) * (z > 0.75 ? 1 - (z - 0.75) * 0.8 : 1);
    const top = 0.034 * (1 - 0.65 * Math.max(0, -z)) * (z > 0.3 ? 1 - (z - 0.3) * 0.55 : 1);
    const y = v.y > 0 ? v.y * top : v.y * 0.012;
    p.setXYZ(i, v.x * wid, y + 0.014, z * 0.125);
  }
  g.computeVertexNormals(); return g;
}
export function soleGeo() {
  const s = new THREE.Shape(); const N = 40;
  for (let i = 0; i <= N; i++) { const a = i / N * Math.PI * 2, z = Math.sin(a), w = 0.048 * (0.86 + 0.18 * Math.sin((z + 1) * 1.45)); const x = Math.cos(a) * w, y = z * 0.13; i ? s.lineTo(x, y) : s.moveTo(x, y); }
  const g = new THREE.ExtrudeGeometry(s, { depth: 0.01, bevelEnabled: true, bevelSize: 0.004, bevelThickness: 0.004, bevelSegments: 4, curveSegments: 40 });
  g.rotateX(Math.PI / 2); g.translate(0, 0.014, 0); return g;
}
// 바지 통: 단 주름 + 천의 출렁임
function trouserGeo() {
  const prof = smoothPts([[0.051, 0.0], [0.058, 0.004], [0.06, 0.03], [0.064, 0.12], [0.07, 0.26], [0.078, 0.42], [0.085, 0.6]]);
  const g = lathe(prof, 56), p = g.attributes.position, v = new THREE.Vector3();
  for (let i = 0; i < p.count; i++) {
    v.fromBufferAttribute(p, i); const a = Math.atan2(v.z, v.x), h = v.y;
    const fold = 0.0045 * Math.sin(a * 5 + h * 18) * Math.exp(-h * 6) + 0.002 * Math.sin(a * 3 + h * 7);
    const r = Math.hypot(v.x, v.z) + fold; p.setXYZ(i, Math.cos(a) * r, h, Math.sin(a) * r);
  }
  g.computeVertexNormals(); return g;
}

// ---------------------------------------------------------------- 장면
export function build() {
  const scene = new THREE.Scene(); const S = {};
  const floor = new THREE.Mesh(new THREE.PlaneGeometry(9, 9), woodFloor()); floor.rotation.x = -Math.PI / 2; scene.add(floor);
  const wallMat = new THREE.MeshPhysicalMaterial({ color: '#f1e7d6', roughness: 0.92 });
  const back = new THREE.Mesh(new THREE.BoxGeometry(9, 3, 0.1), wallMat); back.position.set(0, 1.5, -2.6); scene.add(back);
  const trim = new THREE.MeshPhysicalMaterial({ color: '#fbf6ee', roughness: 0.45 });
  const base = new THREE.Mesh(new THREE.BoxGeometry(9, 0.09, 0.02), trim); base.position.set(0, 0.045, -2.54); scene.add(base);
  // 왼쪽 벽과 창
  const wy0 = 0.85, wy1 = 2.0, wz0 = -1.55, wz1 = -0.45, X = -2.2;
  const seg = (y0, y1, z0, z1) => { const m = new THREE.Mesh(new THREE.BoxGeometry(0.12, y1 - y0, z1 - z0), wallMat); m.position.set(X, (y0 + y1) / 2, (z0 + z1) / 2); scene.add(m); };
  seg(0, wy0, -2.6, 2.5); seg(wy1, 3, -2.6, 2.5); seg(wy0, wy1, -2.6, wz0); seg(wy0, wy1, wz1, 2.5);
  const mull = new THREE.Mesh(new THREE.BoxGeometry(0.06, wy1 - wy0, 0.04), trim); mull.position.set(X, (wy0 + wy1) / 2, (wz0 + wz1) / 2); scene.add(mull);
  const bar = new THREE.Mesh(new THREE.BoxGeometry(0.06, 0.04, wz1 - wz0), trim); bar.position.set(X, (wy0 + wy1) / 2, (wz0 + wz1) / 2); scene.add(bar);

  // 소파(뒤 오른쪽)
  const sofaMat = fabric('#5f8b86', 3);
  const sofa = new THREE.Group(); sofa.position.set(1.0, 0, -2.0); scene.add(sofa);
  const seat = new THREE.Mesh(new RoundedBoxGeometry(2.0, 0.3, 0.85, 8, 0.1), sofaMat); seat.position.y = 0.3; sofa.add(seat);
  for (const sx of [-0.5, 0.5]) { const cu = new THREE.Mesh(new RoundedBoxGeometry(0.98, 0.12, 0.75, 8, 0.055), sofaMat); cu.position.set(sx, 0.5, 0.03); sofa.add(cu); }
  const backr = new THREE.Mesh(new RoundedBoxGeometry(2.0, 0.55, 0.22, 8, 0.1), sofaMat); backr.position.set(0, 0.68, -0.32); sofa.add(backr);
  for (const sx of [-1, 1]) { const arm = new THREE.Mesh(new RoundedBoxGeometry(0.2, 0.48, 0.85, 8, 0.09), sofaMat); arm.position.set(sx, 0.42, 0); sofa.add(arm); }
  const legMat = new THREE.MeshPhysicalMaterial({ color: '#5a3820', roughness: 0.4, clearcoat: 0.4 });
  for (const sx of [-0.9, 0.9]) for (const sz of [-0.32, 0.32]) { const l = new THREE.Mesh(new THREE.CylinderGeometry(0.022, 0.014, 0.15, 20), legMat); l.position.set(sx, 0.075, sz); l.rotation.z = sx * 0.08; sofa.add(l); }
  // 러그
  const rug = new THREE.Mesh(new RoundedBoxGeometry(2.6, 0.012, 1.8, 2, 0.006), rugMat()); rug.position.set(0.5, 0.006, -1.45); scene.add(rug);
  // 화분(뒤 왼쪽, 창 아래)
  const pot = new THREE.Mesh(lathe(smoothPts([[0, 0], [0.11, 0], [0.13, 0.02], [0.155, 0.26], [0.17, 0.28], [0.165, 0.3], [0.14, 0.29]]), 48),
    new THREE.MeshPhysicalMaterial({ color: '#c06642', roughness: 0.85 }));
  pot.position.set(-1.65, 0, -2.15); scene.add(pot);
  const leafMat = new THREE.MeshPhysicalMaterial({ color: '#4a7a36', roughness: 0.5, side: THREE.DoubleSide, sheen: 0.5, sheenColor: new THREE.Color('#b7e08a') });
  const R = rnd(21);
  for (let i = 0; i < 16; i++) {
    const s = new THREE.Shape(); s.moveTo(0, 0); s.bezierCurveTo(0.06, 0.08, 0.05, 0.22, 0, 0.3); s.bezierCurveTo(-0.05, 0.22, -0.06, 0.08, 0, 0);
    const lf = new THREE.Mesh(new THREE.ShapeGeometry(s, 16), leafMat);
    const a = R() * Math.PI * 2, tilt = 0.25 + R() * 0.6;
    lf.position.set(-1.65 + Math.cos(a) * 0.03, 0.29, -2.15 + Math.sin(a) * 0.03);
    lf.rotation.set(0, -a + Math.PI / 2, 0); lf.rotateX(-tilt); lf.scale.setScalar(0.8 + R() * 0.7); scene.add(lf);
  }
  // 낮은 탁자 다리(왼쪽 앞)
  for (const [x, z] of [[-1.05, -0.6], [-1.05, 0.1]]) { const l = new THREE.Mesh(new THREE.CylinderGeometry(0.03, 0.022, 0.42, 24), legMat); l.position.set(x, 0.21, z); scene.add(l); }

  // ------------------------------------------------ 로봇청소기(흰 몸통, 검은 뚜껑, 앞쪽 LED 한 점)
  const vac = new THREE.Group(); scene.add(vac);
  const bodyMat = new THREE.MeshPhysicalMaterial({ color: '#f2efe9', roughness: 0.35, clearcoat: 0.8, clearcoatRoughness: 0.12 });
  const darkMat = new THREE.MeshPhysicalMaterial({ color: '#2a2b2f', roughness: 0.3, clearcoat: 1, clearcoatRoughness: 0.08 });
  vac.add(new THREE.Mesh(lathe(smoothPts([[0, 0.012], [0.16, 0.012], [0.172, 0.022], [0.175, 0.05], [0.17, 0.072], [0.155, 0.082], [0, 0.084]], 6), 96), bodyMat));
  const lid = new THREE.Mesh(new THREE.CylinderGeometry(0.13, 0.13, 0.004, 80), darkMat); lid.position.y = 0.085; vac.add(lid);
  const turret = new THREE.Group(); turret.position.set(0, 0.087, -0.045); vac.add(turret);
  turret.add(new THREE.Mesh(lathe(smoothPts([[0, 0], [0.043, 0], [0.046, 0.006], [0.046, 0.022], [0.04, 0.028], [0, 0.029]], 4), 48), bodyMat));
  const slit = new THREE.Mesh(new THREE.BoxGeometry(0.03, 0.008, 0.004), darkMat); slit.position.set(0, 0.014, 0.046); turret.add(slit);
  const bumper = new THREE.Mesh(new THREE.TorusGeometry(0.173, 0.009, 16, 80, Math.PI * 1.05), darkMat);
  bumper.rotation.x = Math.PI / 2; bumper.rotation.z = -Math.PI * 0.025; bumper.position.y = 0.04; vac.add(bumper);
  const ledMat = new THREE.MeshStandardMaterial({ color: '#000', emissive: new THREE.Color('#62ff86'), emissiveIntensity: 8 });
  const led = new THREE.Mesh(new THREE.SphereGeometry(0.0075, 20, 14), ledMat); led.position.set(0, 0.078, 0.135); vac.add(led);
  const brush = new THREE.Group(); brush.position.set(0.12, 0.006, 0.11); vac.add(brush);
  const bristle = new THREE.MeshPhysicalMaterial({ color: '#3a3d44', roughness: 0.6 });
  for (let k = 0; k < 3; k++) { const b = new THREE.Mesh(new THREE.CylinderGeometry(0.0018, 0.0012, 0.075, 6), bristle); b.rotation.z = Math.PI / 2 - 0.12; b.position.x = 0.035; const arm = new THREE.Group(); arm.rotation.y = k * Math.PI * 2 / 3; arm.add(b); brush.add(arm); }
  S.vac = vac; S.turret = turret; S.led = ledMat; S.brush = brush; S.room = scene.children.slice();

  // ------------------------------------------------ 할머니의 발: 바지 단, 겨자색 양말, 뜨개 슬리퍼
  const pants = fabric('#8d8a86', 41, [3, 6]);
  const sock = knit('#d9a441', 13, [3, 3], 0.8);
  const slip = knit('#d98a7c', 9, [2.5, 2.5]);
  const soleMat = new THREE.MeshPhysicalMaterial({ color: '#efe3cf', roughness: 0.85 });
  const legs = [];
  for (const side of [-1, 1]) {
    const g = new THREE.Group(); scene.add(g);
    const foot = new THREE.Group(); foot.position.z = -0.06; g.add(foot);         // 회전점 = 뒤꿈치
    const fz = new THREE.Group(); fz.position.z = 0.09; foot.add(fz);
    const slm = new THREE.Mesh(slipperGeo(), slip), som = new THREE.Mesh(soleGeo(), soleMat); fz.add(slm, som);
    const toe = new THREE.Mesh(new THREE.SphereGeometry(1, 32, 20), sock); toe.scale.set(0.036, 0.026, 0.1); toe.position.set(0, 0.024, 0.0); toe.visible = false; fz.add(toe);
    const ank = new THREE.Mesh(lathe(smoothPts([[0.034, 0.0], [0.036, 0.04], [0.033, 0.09], [0.036, 0.15]], 4), 32), sock); ank.position.set(0, 0.035, -0.03); g.add(ank);
    const tr = new THREE.Mesh(trouserGeo(), pants); tr.position.set(0, 0.15, -0.03); g.add(tr);
    legs.push({ g, foot, side, slm, som, toe });
  }
  S.legs = legs;
  scene.traverse(o => { if (o.isMesh) { o.castShadow = true; o.receiveShadow = true; } });
  scene.userData.S = S;
  return scene;
}

// ---------------------------------------------------------------- 움직임
const cl = (u) => Math.min(1, Math.max(0, u));
const sm = u => { u = cl(u); return u * u * (3 - 2 * u); };
const ramp = (t, a, b) => cl((t - a) / (b - a));
const lerp = (a, b, u) => a + (b - a) * u;
export function animate(scene, t) {
  const S = scene.userData.S;
  // 청소기: 오른쪽에서 왼쪽으로 → 1.9초 왼발 앞에서 멈칫(살짝 물러남, 호박색 깜빡임)
  //         → 2.6초 카메라 쪽으로 돌아 발 앞을 돌아 나감(가까워지며 LED가 보임)
  const P0 = [0.95, -0.55], P1 = [0.2, -0.36];
  const a1 = sm(ramp(t, 0, 1.9)) * 0.8 + ramp(t, 0, 1.9) * 0.2;
  let x = lerp(P0[0], P1[0], a1), z = lerp(P0[1], P1[1], a1), yaw = Math.atan2(P1[0] - P0[0], P1[1] - P0[1]);
  const back = Math.sin(Math.PI * ramp(t, 1.9, 2.25)) * 0.03;
  x -= Math.sin(yaw) * back; z -= Math.cos(yaw) * back;
  yaw += 0.06 * Math.sin(ramp(t, 2.2, 2.6) * Math.PI * 4);                           // 망설이는 좌우 흔들림
  // 돌아 나가기: 원호(발 앞, 카메라 쪽)
  const g = ramp(t, 2.6, DUR), ge = sm(g) * 0.75 + g * 0.25;
  if (g > 0) {
    const cx = -0.05, cz = -0.33, r0 = Math.hypot(P1[0] - cx, P1[1] - cz), a0 = Math.atan2(P1[1] - cz, P1[0] - cx);
    const ang = a0 + ge * 2.1, r = r0 + 0.06 * Math.sin(Math.PI * ge);
    const nx = cx + r * Math.cos(ang), nz = cz + r * Math.sin(ang);
    const tx = -Math.sin(ang), tz = Math.cos(ang);                                     // 원을 도는 방향(+각)
    const yawArc = Math.atan2(tx, tz);
    const blend = sm(ramp(t, 2.6, 2.9));
    x = nx; z = nz; yaw = yaw + (((yawArc - yaw + Math.PI * 3) % (Math.PI * 2)) - Math.PI) * blend;
  }
  S.vac.position.set(x, 0, z); S.vac.rotation.y = yaw;
  S.turret.rotation.y = t * 9;
  S.brush.rotation.y = -t * 14;
  const alarm = ramp(t, 1.9, 2.0) - ramp(t, 2.7, 2.9);
  const blink = 0.5 + 0.5 * Math.cos((t - 1.9) * Math.PI * 2 * 3);
  S.led.emissive.copy(new THREE.Color('#62ff86').lerp(new THREE.Color('#ffaa2e'), alarm));
  S.led.emissiveIntensity = lerp(6 + 1.5 * Math.sin(t * 3), 3 + 9 * blink, alarm);
  // 발: 할머니는 왼쪽을 향해 서 있다(발끝이 왼쪽 뒤). 오른발은 뒤에 디딘 채,
  //     왼발이 1.15–1.75초에 청소기 앞길로 내려앉음 → 2.0–2.6 발끝 까딱 → 3.3 오른발이 한 걸음
  const yawF = -1.95;
  const fwd = [Math.sin(yawF), Math.cos(yawF)], side = [Math.cos(yawF), -Math.sin(yawF)];
  for (const L of S.legs) {
    let bx, bz, lift = 0, pitch = 0;
    if (L.side > 0) {
      bx = 0.02; bz = -0.62;
      const u = ramp(t, 3.3, 3.85); bx += fwd[0] * 0.32 * sm(u); bz += fwd[1] * 0.32 * sm(u); lift = Math.sin(Math.PI * u) * 0.045; pitch = -0.3 * Math.sin(Math.PI * u);
    } else {
      const u = ramp(t, 1.15, 1.75); bx = lerp(0.12, -0.08, sm(u)); bz = lerp(-0.62, -0.34, sm(u));
      lift = (t < 1.15 ? 0.45 : 0) + Math.sin(Math.PI * u) * 0.05 + (t >= 1.15 ? (1 - sm(ramp(t, 1.15, 1.45))) * 0.12 : 0); pitch = -0.35 * Math.sin(Math.PI * u);
      const tap = ramp(t, 2.0, 2.6); if (tap > 0 && tap < 1) pitch += 0.28 * Math.max(0, Math.sin(tap * Math.PI * 3));
    }
    L.g.position.set(bx + side[0] * 0.0, lift, bz + side[1] * 0.0);
    L.g.rotation.y = yawF + (L.side > 0 ? 0.12 : -0.08);
    L.foot.rotation.x = -pitch;
  }
}

// ---------------------------------------------------------------- 카메라·빛
export const CAM = { pos: [0.18, 0.075, 0.62], target: [0.02, 0.07, -0.4], fov: 36, fStop: 2.8, focus: 1.0 };
export const SUN = { dir: [-1.0, 1.05, -0.12], color: '#ffc884', intensity: 10.0 };
export function focusAt(scene, cam) { return scene.userData.S.vac.position.clone().setY(0.06).distanceTo(cam.position); }
