// 갈비뼈 창가(빈 구석) — 하늘색·복숭아빛. 하얀 갈비뼈 아치 지붕의 작은 발코니, 숨에 맞춰 부풀었다 가라앉는 커튼, 해먹 기둥 두 개
import * as THREE from 'three';
import { RoundedBoxGeometry } from 'three/addons/geometries/RoundedBoxGeometry.js';
import { clay } from '../chars3d.js';
import { canvasTex, mat, brass, glow, rng, setKit, makeWorld, platform, railing } from './common.js';

const R = 2.6;
export const HAMMOCK = { a: [-0.95, 1.05, -0.35], b: [0.95, 1.05, -0.35], sag: 0.62 };   // 매단 두 점과 처짐(가운데 높이 = 1.05 - sag)
export function buildRibNook() {
  const kit = setKit(), { g, SOLID, add } = kit;
  platform(kit, R, (c, w, h) => {   // 복숭아빛 나무 원형 마루
    c.fillStyle = '#f2c9a8'; c.fillRect(0, 0, w, h); const cx = w / 2, cy = h / 2;
    for (let r = 60; r < w; r += 90) { c.strokeStyle = 'rgba(190,130,100,0.35)'; c.lineWidth = 6; c.beginPath(); c.arc(cx, cy, r, 0, 7); c.stroke(); }
    for (let a = 0; a < 24; a++) { c.strokeStyle = 'rgba(190,130,100,0.25)'; c.lineWidth = 4; c.beginPath(); c.moveTo(cx, cy); c.lineTo(cx + Math.cos(a / 24 * 6.283) * w, cy + Math.sin(a / 24 * 6.283) * w); c.stroke(); }
  }, '#6a4a5a', ['#ffe8d0', '#ffc8a0']);
  railing(kit, R, [[-1.7, Math.PI * 2 - 2.5]], clay('#fff6ee', { roughness: 0.4 }), mat('#e8d6ee', { roughness: 0.6 }));
  // 갈비뼈 아치 7개(뒤에서 앞으로 둥글게 덮음) + 등뼈 들보
  const bone = clay('#f3dcc8', { roughness: 0.45, clearcoat: 0.4 });
  for (let k = 0; k < 4; k++) { const z = -2.2 + k * 0.62, w = 2.3 - Math.abs(k - 3) * 0.12;
    const arc = add(new THREE.Mesh(new THREE.TorusGeometry(w, 0.075 + 0.015 * Math.sin(k), 14, 48, Math.PI), bone), 'rib'); arc.position.set(0, 0.0, z); arc.scale.y = 1.35; }
  const spine = add(new THREE.Mesh(new THREE.CylinderGeometry(0.12, 0.12, 4.0, 16), bone), 'rib'); spine.rotation.x = Math.PI / 2; spine.scale.y = 0.5; spine.position.set(0, 2.3 * 1.35 - 0.05, -1.27);
  for (let k = 0; k < 4; k++) add(new THREE.Mesh(new THREE.SphereGeometry(0.17, 16, 12), bone), 'rib').position.set(0, 3.06, -2.2 + k * 0.62);
  // 커튼: 갈비뼈 사이 뒤쪽에 늘어뜨린 천 4장(숨에 맞춰 바깥으로 부풀었다 가라앉음)
  const curtains = [], cMat = new THREE.MeshPhysicalMaterial({ color: '#ffb8c8', roughness: 0.8, transparent: true, opacity: 0.8, side: THREE.DoubleSide, sheen: 0.3, sheenColor: new THREE.Color('#ffe8f0') });
  for (const [x, z, ry] of [[-1.85, -1.3, 0.9], [1.85, -1.3, -0.9], [-2.2, 0.2, 1.45], [2.2, 0.2, -1.45]]) {
    const geo = new THREE.PlaneGeometry(1.0, 2.4, 20, 30); const m = new THREE.Mesh(geo, cMat); m.position.set(x, 1.45, z); m.rotation.y = ry; g.add(m);
    curtains.push({ m, base: geo.attributes.position.array.slice(), ph: x * 0.7 }); const rod = add(new THREE.Mesh(new THREE.CylinderGeometry(0.02, 0.02, 1.1, 8), brass())); rod.rotation.z = Math.PI / 2; rod.position.set(x, 2.66, z); rod.rotation.y = ry; }
  // 해먹 기둥 두 개 + 해먹(천 곡면, 처짐 조절)
  for (const p of [HAMMOCK.a, HAMMOCK.b]) { const post = add(new THREE.Mesh(new THREE.CylinderGeometry(0.06, 0.08, 1.2, 16), bone), 'post'); post.position.set(p[0] * 1.12, 0.6, p[2]);
    add(new THREE.Mesh(new THREE.SphereGeometry(0.09, 16, 12), bone), 'post').position.set(p[0] * 1.12, 1.22, p[2]); }
  const hamMat = clay('#ffb36b', { roughness: 0.75, side: THREE.DoubleSide });
  const hamGeo = new THREE.PlaneGeometry(1, 1, 40, 10); const hammock = new THREE.Mesh(hamGeo, hamMat); hammock.castShadow = hammock.receiveShadow = true; hammock.name = 'hammock'; g.add(hammock); SOLID.push(hammock);
  const stripes = new THREE.Mesh(hamGeo, new THREE.MeshPhysicalMaterial({ color: '#ffffff', transparent: true, opacity: 0, side: THREE.DoubleSide })); g.add(stripes);
  const ropes = [];
  for (let k = 0; k < 2; k++) { const r = new THREE.Mesh(new THREE.CylinderGeometry(0.012, 0.012, 1, 6), clay('#c98f5b')); g.add(r); ropes.push(r); }
  // 해먹 모양: sag(처짐), press(누가 누우면 가운데가 더 처짐) — 길이 방향 포물선, 폭 방향 오목
  const setHammock = (press = 0) => { const A = HAMMOCK.a, B = HAMMOCK.b, pa = hamGeo.attributes.position, span = B[0] - A[0] - 0.3, wid = 0.62, sag = HAMMOCK.sag + press * 0.06;
    for (let i = 0; i < pa.count; i++) { const u = hamGeo.attributes.uv.getX(i), v = hamGeo.attributes.uv.getY(i);
      const x = A[0] + 0.15 + span * u, y = A[1] - 0.05 - sag * 4 * u * (1 - u) + 0.1 * Math.pow(2 * v - 1, 2) * (4 * u * (1 - u)), z = A[2] + (v - 0.5) * wid * (0.35 + 0.65 * Math.sin(Math.PI * u));
      pa.setXYZ(i, x, y, z); }
    pa.needsUpdate = true; hamGeo.computeVertexNormals(); hamGeo.computeBoundingSphere(); hamGeo.computeBoundingBox();
    [[A[0] * 1.12, A[0] + 0.15], [B[0] * 1.12, B[0] - 0.15]].forEach(([px, hx], k) => { const p0 = new THREE.Vector3(px, 1.15, A[2]), p1 = new THREE.Vector3(hx, A[1] - 0.05, A[2]); ropes[k].position.copy(p0).lerp(p1, 0.5); ropes[k].scale.y = p0.distanceTo(p1); ropes[k].quaternion.setFromUnitVectors(new THREE.Vector3(0, 1, 0), p1.clone().sub(p0).normalize()); });
  };
  setHammock(0);
  // 쿠션 두 개, 작은 화분
  add(new THREE.Mesh(new RoundedBoxGeometry(0.42, 0.18, 0.42, 4, 0.08), clay('#9fd8ff', { roughness: 0.7 })), 'cushion').position.set(-1.65, 0.09, -0.95);
  add(new THREE.Mesh(new RoundedBoxGeometry(0.38, 0.16, 0.38, 4, 0.07), clay('#ffd0e0', { roughness: 0.7 })), 'cushion').position.set(-1.25, 0.08, -1.45);
  add(new THREE.Mesh(new THREE.CylinderGeometry(0.16, 0.12, 0.26, 20), clay('#7fb7a4')), 'pot').position.set(1.4, 0.13, 0.9);
  for (let k = 0; k < 6; k++) { const leaf = add(new THREE.Mesh(new THREE.SphereGeometry(0.12, 12, 8), clay('#5cc79e')), null); leaf.scale.set(0.5, 1.4, 0.25); leaf.position.set(1.4 + Math.cos(k) * 0.08, 0.42, 0.9 + Math.sin(k) * 0.08); leaf.rotation.set(Math.sin(k) * 0.5, k, Math.cos(k) * 0.5); }

  // 휴가지 바다(포스터 색: 하늘색 하늘, 청록 바다, 모래, 노란 해) — 공중 마루는 바다 위 작은 섬
  const W = makeWorld({ sky: ['#4f9fe6', '#9ad6f6', '#fff6de', '#8fe0ea', '#3fb0c8'], tube: '#f0f8ff', cell: '#ffffff', cellE: '#bfe0ff', tower: '#7a8ac8', win: '#fff0d0', motes: '#ffffff', seed: 97, cellShape: 'bubble', towers: [] });
  const SEA_Y = -1.3;
  const seaTex = canvasTex(512, 512, (c, w, h) => { c.fillStyle = '#2fb8cc'; c.fillRect(0, 0, w, h); const rr = rng(5);
    for (let k = 0; k < 90; k++) { const x = rr() * w, y = rr() * h, l = 20 + rr() * 50; c.strokeStyle = `rgba(255,255,255,${0.25 + rr() * 0.4})`; c.lineWidth = 3 + rr() * 3; c.beginPath(); c.moveTo(x, y); c.quadraticCurveTo(x + l / 2, y - 6, x + l, y); c.stroke(); }
    for (let k = 0; k < 140; k++) { c.fillStyle = 'rgba(160,240,250,0.35)'; c.beginPath(); c.ellipse(rr() * w, rr() * h, 10 + rr() * 30, 3 + rr() * 6, 0, 0, 7); c.fill(); } });
  seaTex.wrapS = seaTex.wrapT = THREE.RepeatWrapping; seaTex.repeat.set(40, 40);
  const sea = new THREE.Mesh(new THREE.CircleGeometry(56, 96), new THREE.MeshPhysicalMaterial({ map: seaTex, roughness: 0.12, clearcoat: 1, clearcoatRoughness: 0.08, emissive: '#0f6f88', emissiveIntensity: 0.25 }));
  sea.rotation.x = -Math.PI / 2; sea.position.y = SEA_Y; sea.receiveShadow = true; g.add(sea);
  const beach = new THREE.Mesh(new THREE.CylinderGeometry(2.75, 3.3, 0.16, 64), clay('#f5dca8', { roughness: 0.9 })); beach.position.y = SEA_Y + 0.02; beach.receiveShadow = true; g.add(beach);
  const shore = new THREE.Mesh(new THREE.TorusGeometry(3.3, 0.06, 8, 96), new THREE.MeshStandardMaterial({ color: '#ffffff', emissive: '#e8ffff', emissiveIntensity: 0.4, roughness: 0.6 })); shore.rotation.x = Math.PI / 2; shore.position.y = SEA_Y + 0.02; g.add(shore);
  const sun = new THREE.Mesh(new THREE.SphereGeometry(3.2, 32, 16), new THREE.MeshBasicMaterial({ color: '#fff3b0', fog: false })); sun.position.set(10, 13, -50); g.add(sun);
  const sunHalo = new THREE.Sprite(new THREE.SpriteMaterial({ map: canvasTex(128, 128, (c, w, h) => { const gr = c.createRadialGradient(64, 64, 10, 64, 64, 64); gr.addColorStop(0, 'rgba(255,240,170,0.9)'); gr.addColorStop(1, 'rgba(255,240,170,0)'); c.fillStyle = gr; c.fillRect(0, 0, w, h); }), transparent: true, depthWrite: false, fog: false }));
  sunHalo.position.copy(sun.position); sunHalo.scale.setScalar(22); g.add(sunHalo);
  // 혈관 복도 끝 → 휴가지 입구(각 -2.1)로 이어지는 다리 + 반투명 관(C8a)
  const ENT = -2.1, dir = new THREE.Vector3(Math.sin(ENT), 0, -Math.cos(ENT));
  const along = (r, y = 0) => new THREE.Vector3(dir.x * r, y, dir.z * r);
  const deck = new THREE.Mesh(new RoundedBoxGeometry(1.25, 0.12, 9.5, 2, 0.04), clay('#f6c9b4', { roughness: 0.6 })); deck.position.copy(along(2.55 + 4.75, -0.072)); deck.rotation.y = Math.atan2(dir.x, dir.z); deck.receiveShadow = deck.castShadow = true; g.add(deck);
  for (let r = 3.4; r < 12; r += 1.6) for (const sd of [-1, 1]) { const pl = new THREE.Mesh(new THREE.CylinderGeometry(0.06, 0.07, 1.25, 10), bone); const side = new THREE.Vector3(dir.z, 0, -dir.x).multiplyScalar(0.5 * sd); pl.position.copy(along(r, -0.75)).add(side); g.add(pl); }
  const tubeG = new THREE.Group(); tubeG.position.copy(along(9.0, 0.85)); tubeG.rotation.y = Math.atan2(dir.x, dir.z); g.add(tubeG);
  const tubeMat = new THREE.MeshPhysicalMaterial({ color: '#ffd6e0', roughness: 0.1, transparent: true, opacity: 0.22, side: THREE.DoubleSide, depthWrite: false });
  const tube = new THREE.Mesh(new THREE.CylinderGeometry(0.95, 0.95, 6.5, 32, 1, true), tubeMat); tube.rotation.x = Math.PI / 2; tubeG.add(tube);
  for (let k = 0; k <= 10; k++) { const ring = add(new THREE.Mesh(new THREE.TorusGeometry(0.97, 0.045, 8, 32), new THREE.MeshStandardMaterial({ color: '#ffe6ec', emissive: '#ffb0c4', emissiveIntensity: 0.6 })), 'tube', tubeG); ring.position.z = -3.25 + k * 0.65; }

  g.add(W.world);
  const clouds = new THREE.Group(); g.add(clouds); const r2 = rng(13);
  for (let k = 0; k < 14; k++) { const cl = new THREE.Group(); for (let j = 0; j < 5; j++) { const s = new THREE.Mesh(new THREE.SphereGeometry(1, 16, 12), new THREE.MeshStandardMaterial({ color: '#ffffff', emissive: '#ffe8f0', emissiveIntensity: 0.3, roughness: 1 })); s.position.set(j * 1.3 - 2.6, Math.sin(j) * 0.4, (r2() - 0.5)); s.scale.setScalar(1 + r2()); cl.add(s); }
    const a = r2() * Math.PI * 2; cl.position.set(Math.cos(a) * 25, -3 + r2() * 10, Math.sin(a) * 25 - 5); cl.scale.setScalar(0.8 + r2()); clouds.add(cl); }
  let breathRate = 1;
  const setTime = (t, { breath = 1 } = {}) => {
    W.setTime(t, 0.6); clouds.rotation.y = t * 0.01; seaTex.offset.set(t * 0.004, t * 0.002);
    const b = Math.sin(t * 2 * Math.PI / 4.0) * breath;   // 숨 4초 주기
    curtains.forEach(c => { const pa = c.m.geometry.attributes.position; for (let i = 0; i < pa.count; i++) { const bx = c.base[i * 3], by = c.base[i * 3 + 1]; const fall = (1.2 - by) / 2.4;
      pa.setZ(i, (0.18 + 0.16 * b) * fall * fall * (1 + 0.3 * Math.sin(bx * 6 + t * 1.5 + c.ph)) + 0.03 * Math.sin(bx * 9 + t * 2)); } pa.needsUpdate = true; c.m.geometry.computeVertexNormals(); });
  };
  setTime(0);
  return { group: g, SOLID, setTime, atmo: { fog: '#d6f0f6', near: 14, far: 70 }, setHammock, HAMMOCK, along, ENT };
}
