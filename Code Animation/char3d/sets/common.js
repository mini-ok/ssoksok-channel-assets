// 세트 공통: 캔버스 텍스처, 재질, 공중에 뜬 원형 무대, 장기별 바깥 세계(노을 안개 + 흐르는 투명 관 + 먼 탑 + 빛 입자)
import * as THREE from 'three';
import { clay } from '../chars3d.js';

export function canvasTex(w, h, draw) {
  const cv = document.createElement('canvas'); cv.width = w; cv.height = h; draw(cv.getContext('2d'), w, h);
  const t = new THREE.CanvasTexture(cv); t.colorSpace = THREE.SRGBColorSpace; t.anisotropy = 8; t._cv = cv; return t;
}
export const mat = (c, o = {}) => new THREE.MeshPhysicalMaterial({ color: c, roughness: 0.7, ...o });
export const brass = (o = {}) => clay('#D9A441', { metalness: 0.65, roughness: 0.32, clearcoat: 0.4, ...o });
export const glow = (c, e, i = 1.2) => new THREE.MeshStandardMaterial({ color: c, emissive: e, emissiveIntensity: i });
export const rng = seed => { let k = seed; return () => (k = (k * 16807) % 2147483647) / 2147483647; };

export function setKit() {
  const g = new THREE.Group(), SOLID = [];
  const add = (m, name, parent = g) => { m.castShadow = m.receiveShadow = true; parent.add(m); if (name) { m.name = name; SOLID.push(m); } return m; };
  return { g, SOLID, add };
}

// 바깥 세계. o: { sky:[top, mid, horizon, low, bottom], tube, cell, cellE, tower, win, motes, seed, cellShape:'disc'|'bubble'|'drop'|'spark' }
export function makeWorld(o) {
  const world = new THREE.Group(), R = rng(o.seed || 7);
  const sky = new THREE.Mesh(new THREE.SphereGeometry(60, 48, 24), new THREE.MeshBasicMaterial({ side: THREE.BackSide, fog: false, map: canvasTex(16, 512, (c, w, h) => {
    const gr = c.createLinearGradient(0, 0, 0, h); const s = o.sky; gr.addColorStop(0, s[0]); gr.addColorStop(0.42, s[1]); gr.addColorStop(0.5, s[2]); gr.addColorStop(0.56, s[3]); gr.addColorStop(1, s[4]);
    c.fillStyle = gr; c.fillRect(0, 0, w, h); }) }));
  world.add(sky);
  const geo = { disc: new THREE.TorusGeometry(0.16, 0.09, 10, 20), bubble: new THREE.SphereGeometry(0.16, 14, 10), drop: new THREE.SphereGeometry(0.14, 12, 10), spark: new THREE.OctahedronGeometry(0.14) }[o.cellShape || 'disc'];
  const cellMat = new THREE.MeshStandardMaterial({ color: o.cell, emissive: o.cellE, emissiveIntensity: 1.6, roughness: 0.4, transparent: o.cellShape === 'bubble', opacity: o.cellShape === 'bubble' ? 0.8 : 1 });
  const glassMat = new THREE.MeshPhysicalMaterial({ color: o.tube, roughness: 0.05, transparent: true, opacity: 0.16, side: THREE.DoubleSide, depthWrite: false });
  const flows = [];
  const defs = o.tubes || [
    [[-30, 6, -14], [-8, 4.5, -10], [8, 5.5, -12], [30, 8, -16]], [[-28, -1, -9], [-6, 1.5, -11], [12, 0.5, -9], [32, 2.5, -13]],
    [[-20, 12, -22], [0, 9, -20], [22, 11, -24]], [[18, -4, -6], [10, 2, -10], [6, 9, -14], [10, 16, -18]],
    [[-16, -5, 6], [-11, 1.5, -2], [-14, 7, -10], [-20, 12, -16]], [[-36, 3, -26], [-10, 6, -30], [20, 4, -32], [40, 7, -28]]];
  for (const pts of defs) {
    const curve = new THREE.CatmullRomCurve3(pts.map(p => new THREE.Vector3(...p))), len = curve.getLength(), r = 0.55;
    world.add(new THREE.Mesh(new THREE.TubeGeometry(curve, 160, r, 20), glassMat));
    const nr = Math.floor(len / 3);
    for (let k = 0; k < nr; k++) { const ring = new THREE.Mesh(new THREE.TorusGeometry(r + 0.02, 0.05, 6, 24), brass({ emissive: o.cellE, emissiveIntensity: 0.3 })); const u = (k + 0.5) / nr; ring.position.copy(curve.getPointAt(u)); ring.quaternion.setFromUnitVectors(new THREE.Vector3(0, 0, 1), curve.getTangentAt(u)); world.add(ring); }
    const n = Math.floor(len * 1.4), inst = new THREE.InstancedMesh(geo, cellMat, n); world.add(inst);
    flows.push({ curve, inst, n, len, off: Array.from({ length: n }, () => [R(), (R() - 0.5) * 0.5, (R() - 0.5) * 0.5, R() * 6]) });
  }
  const towerMat = mat(o.tower, { roughness: 0.8 }), winMat = glow('#ffffff', o.win, 1.5);
  for (const [x, z, h, r] of o.towers || [[-14, -18, 14, 2.2], [-6, -24, 18, 2.8], [9, -20, 12, 2.0], [17, -15, 9, 1.6], [24, -26, 16, 2.6], [-22, -10, 10, 1.8]]) {
    const tw = new THREE.Mesh(new THREE.CylinderGeometry(r * 0.85, r, h, 24), towerMat); tw.position.set(x, h / 2 - 6, z); world.add(tw);
    const cap = new THREE.Mesh(new THREE.SphereGeometry(r * 0.85, 24, 12, 0, Math.PI * 2, 0, Math.PI / 2), towerMat); cap.position.set(x, h - 6, z); world.add(cap);
    for (let k = 0; k < 10; k++) { const w = new THREE.Mesh(new THREE.CircleGeometry(0.22, 12), winMat); const a = R() * 2 - 1, yy = -5 + R() * (h - 1); w.position.set(x + Math.sin(a) * r * 0.93, yy, z + Math.cos(a) * r * 0.93); w.rotation.y = a; world.add(w); }
  }
  const motes = new THREE.InstancedMesh(new THREE.SphereGeometry(0.012, 6, 4), new THREE.MeshBasicMaterial({ color: o.motes || '#ffd8b0', transparent: true, opacity: 0.5 }), 140); world.add(motes);
  const moteP = Array.from({ length: 140 }, () => [(R() - 0.5) * 9, R() * 3.2, (R() - 0.5) * 7, R() * 6]);
  const M4 = new THREE.Matrix4(), Q = new THREE.Quaternion(), V = new THREE.Vector3(), S1 = new THREE.Vector3(1, 1, 1), E = new THREE.Euler();
  const setTime = (t, speed = 1) => {
    for (const f of flows) { for (let k = 0; k < f.n; k++) { const of = f.off[k]; const u = ((of[0] + t * 2.2 * speed / f.len) % 1 + 1) % 1;
      V.copy(f.curve.getPointAt(u)); V.x += of[1]; V.y += of[2]; Q.setFromEuler(E.set(of[3] + t * 0.8, of[3] * 2, 0)); M4.compose(V, Q, S1); f.inst.setMatrixAt(k, M4); } f.inst.instanceMatrix.needsUpdate = true; }
    moteP.forEach((p, k) => { V.set(p[0] + Math.sin(t * 0.3 + p[3]) * 0.3, (p[1] + t * 0.08) % 3.2, p[2] + Math.cos(t * 0.25 + p[3]) * 0.3); M4.compose(V, Q.identity(), S1); motes.setMatrixAt(k, M4); });
    motes.instanceMatrix.needsUpdate = true;
  };
  setTime(0);
  return { world, setTime, cellMat };
}

// 공중에 뜬 원형 무대(바닥 + 밑동 + 테두리 빛) — 반지름 r, 바닥 텍스처 그리기 함수
export function platform(kit, r, floorDraw, under = '#3a1a28', rim = ['#ffb38a', '#ff8a5a']) {
  const { g, add } = kit;
  const floor = add(new THREE.Mesh(new THREE.CircleGeometry(r + 0.05, 96), mat('#ffffff', { map: canvasTex(2048, 2048, floorDraw), roughness: 0.55, clearcoat: 0.25 }))); floor.rotation.x = -Math.PI / 2;
  add(new THREE.Mesh(new THREE.CylinderGeometry(r + 0.05, r * 0.55, 2.2, 64), mat(under, { roughness: 0.8 }))).position.y = -1.12;
  const rimG = new THREE.Mesh(new THREE.TorusGeometry(r + 0.05, 0.04, 8, 120), glow(rim[0], rim[1], 1.2)); rimG.rotation.x = Math.PI / 2; rimG.position.y = -0.02; g.add(rimG);
  return floor;
}
// 난간(각 범위 목록) — onWall 각(0 = 뒤 -z, +는 오른쪽)
export function railing(kit, r, segs, railMat, parMat) {
  const { add } = kit;
  for (const [a0, a1] of segs) {
    const par = add(new THREE.Mesh(new THREE.CylinderGeometry(r, r, 0.45, 64, 1, true, Math.PI - a1, a1 - a0), parMat), 'wall'); par.position.y = 0.225; par.material.side = THREE.DoubleSide;
    const rail = add(new THREE.Mesh(new THREE.TorusGeometry(r, 0.035, 8, 64, a1 - a0), railMat), 'wall'); rail.rotation.x = Math.PI / 2; rail.rotation.z = a0 - Math.PI / 2; rail.position.y = 0.95;
    const n = Math.max(2, Math.round((a1 - a0) / 0.22));
    for (let k = 0; k <= n; k++) { const a = a0 + (a1 - a0) * k / n; const post = add(new THREE.Mesh(new THREE.CylinderGeometry(0.025, 0.025, 0.5, 8), railMat), 'wall'); post.position.set(r * Math.sin(a), 0.7, -r * Math.cos(a)); }
  }
}
export const onWallPos = (r, ang, y) => [r * Math.sin(ang), y, -r * Math.cos(ang)];
