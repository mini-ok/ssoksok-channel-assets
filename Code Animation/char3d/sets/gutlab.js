// 장의 발효 연구소 — 민트·유리. 꼬불꼬불 고리처럼 도는 소화 컨베이어(소파가 그 위에 있음), 빛나는 미생물 발효병, 둥근 창 타일 벽
import * as THREE from 'three';
import { RoundedBoxGeometry } from 'three/addons/geometries/RoundedBoxGeometry.js';
import { clay } from '../chars3d.js';
import { canvasTex, mat, brass, glow, rng, setKit, makeWorld, platform, railing, onWallPos } from './common.js';

const R = 3.6;
export function buildGutLab() {
  const kit = setKit(), { g, SOLID, add } = kit, rnd = rng(31);
  platform(kit, R, (c, w, h) => {   // 민트 육각 타일
    c.fillStyle = '#8fcfb8'; c.fillRect(0, 0, w, h); const s = 70;
    for (let y = 0; y < h + s; y += s * 0.87) for (let x = 0; x < w + s; x += s * 1.5) for (const ox of [0, s * 0.75]) {
      const cx = x + ox, cy = y + (ox ? s * 0.43 : 0); c.beginPath(); for (let k = 0; k < 6; k++) c.lineTo(cx + s * 0.48 * Math.cos(k * Math.PI / 3), cy + s * 0.48 * Math.sin(k * Math.PI / 3));
      c.closePath(); c.fillStyle = ((cx * 7 + cy * 3) | 0) % 5 ? '#a9dfcb' : '#86c9b0'; c.fill(); c.strokeStyle = '#7cc3a8'; c.lineWidth = 4; c.stroke(); }
  }, '#24443a', ['#c8ffe8', '#5affc0']);
  // 뒤쪽 낮은 타일 벽 + 둥근 창(창 너머로 바깥 세계)
  const W0 = -1.3, W1 = 1.3;
  const tile = canvasTex(2048, 256, (c, w, h) => { c.fillStyle = '#5fb79a'; c.fillRect(0, 0, w, h); for (let x = 0; x < w; x += 48) for (let y = 0; y < h; y += 48) { c.fillStyle = (x / 48 + y / 48) % 2 ? '#8ad8bd' : '#76cdb0'; c.fillRect(x + 2, y + 2, 44, 44); } });
  tile.wrapS = THREE.RepeatWrapping; tile.repeat.set(3, 1);
  tile.repeat.set(3, 2.2); add(new THREE.Mesh(new THREE.CylinderGeometry(R, R, 2.6, 96, 1, true, Math.PI - W1, W1 - W0), mat('#ffffff', { map: tile, side: THREE.DoubleSide, roughness: 0.4, clearcoat: 0.5 })), 'wall').position.y = 1.3;
  for (let k = 0; k < 7; k++) { const a = W0 + 0.2 + (W1 - W0 - 0.4) * k / 6, [x, , z] = onWallPos(R - 0.02, a, 0);
    const ring = add(new THREE.Mesh(new THREE.TorusGeometry(0.34, 0.07, 12, 40), brass()), 'wall'); ring.position.set(x, 1.85, z); ring.rotation.y = -a;
    const pane = new THREE.Mesh(new THREE.CircleGeometry(0.33, 32), glow('#d8fff0', '#7affc8', 0.9)); const [qx, , qz] = onWallPos(R - 0.04, a, 0); pane.position.set(qx, 1.85, qz); pane.rotation.y = -a; g.add(pane);
    for (let b = 0; b < 8; b++) { const bolt = add(new THREE.Mesh(new THREE.SphereGeometry(0.025, 8, 6), brass()), null); const ba = b / 8 * Math.PI * 2; bolt.position.set(x + Math.cos(-a) * Math.cos(ba) * 0.34, 1.85 + Math.sin(ba) * 0.34, z + Math.sin(-a) * Math.cos(ba) * 0.34 * -1); }
    const post = add(new THREE.Mesh(new THREE.BoxGeometry(0.12, 1.3, 0.12), mat('#5fb79a', { roughness: 0.4 })), 'wall'); const [px, , pz] = onWallPos(R - 0.02, a + (W1 - W0 - 0.4) / 12, 0); post.visible = false; }
  const capT = add(new THREE.Mesh(new THREE.TorusGeometry(R, 0.06, 8, 96, W1 - W0), brass())); capT.rotation.x = -Math.PI / 2; capT.rotation.z = W0 - Math.PI / 2; capT.position.y = 2.62;
  railing(kit, R, [[W1, Math.PI * 2 + W0 - 0.0]], brass(), mat('#24443a', { roughness: 0.6 }));

  // 소화 컨베이어: 무대 위를 고리 모양으로 휘감는 닫힌 길(높이 0.36), 벨트 + 롤러 + 옆 난간
  const BELT_Y = 0.36, BW = 0.62;
  const pts = [[-2.6, 1.0], [-1.6, 1.0], [-0.6, 1.0], [0.4, 1.0], [1.4, 1.0], [2.4, 0.7], [2.7, -0.3], [2.1, -1.3], [1.0, -1.55], [0.0, -1.75], [-1.0, -1.45], [-2.1, -1.6], [-2.9, -0.8], [-3.0, 0.3]];
  const curve = new THREE.CatmullRomCurve3(pts.map(([x, z]) => new THREE.Vector3(x, BELT_Y, z)), true, 'centripetal');
  const N = 600, pos = [], uvs = [], idx = [], L = curve.getLength();
  for (let i = 0; i <= N; i++) { const u = i / N, p = curve.getPointAt(u % 1), tn = curve.getTangentAt(u % 1), side = new THREE.Vector3(-tn.z, 0, tn.x).normalize();
    for (const s of [-1, 1]) { pos.push(p.x + side.x * s * BW / 2, p.y, p.z + side.z * s * BW / 2); uvs.push(s < 0 ? 0 : 1, u * L / 0.5); } }
  for (let i = 0; i < N; i++) idx.push(i * 2, i * 2 + 1, i * 2 + 2, i * 2 + 1, i * 2 + 3, i * 2 + 2);
  const bg = new THREE.BufferGeometry(); bg.setAttribute('position', new THREE.Float32BufferAttribute(pos, 3)); bg.setAttribute('uv', new THREE.Float32BufferAttribute(uvs, 2)); bg.setIndex(idx); bg.computeVertexNormals();
  const beltTex = canvasTex(128, 128, (c) => { c.fillStyle = '#3d6b5e'; c.fillRect(0, 0, 128, 128); c.fillStyle = '#4f8576'; for (let y = 0; y < 128; y += 32) c.fillRect(0, y, 128, 14); });
  beltTex.wrapS = beltTex.wrapT = THREE.RepeatWrapping;
  const belt = add(new THREE.Mesh(bg, mat('#ffffff', { map: beltTex, roughness: 0.6, side: THREE.DoubleSide })), 'belt');
  const railMat = clay('#9fe3c9', { roughness: 0.35 }), legMat = brass();
  for (const s of [-1, 1]) { const rp = []; for (let i = 0; i <= 200; i++) { const u = i / 200, p = curve.getPointAt(u % 1), tn = curve.getTangentAt(u % 1), side = new THREE.Vector3(-tn.z, 0, tn.x).normalize(); rp.push(p.clone().addScaledVector(side, s * (BW / 2 + 0.04)).setY(BELT_Y + 0.02)); }
    add(new THREE.Mesh(new THREE.TubeGeometry(new THREE.CatmullRomCurve3(rp, true), 400, 0.035, 8, true), railMat), 'beltRail'); }
  for (let k = 0; k < 40; k++) { const u = k / 40, p = curve.getPointAt(u); const leg = add(new THREE.Mesh(new THREE.CylinderGeometry(0.03, 0.04, BELT_Y - 0.02, 8), legMat), 'beltLeg'); leg.position.set(p.x, (BELT_Y - 0.02) / 2, p.z); }
  // 컨베이어 위를 흐르는 음식 꾸러미(알록달록 말랑 덩어리)
  const parcelCols = ['#ffcf6a', '#ff9f8a', '#c9a7ff', '#9fe0ff', '#ffe08a'];
  const parcels = Array.from({ length: 14 }, (_, k) => { const m = add(new THREE.Mesh(new RoundedBoxGeometry(0.24, 0.16, 0.2, 3, 0.07), clay(parcelCols[k % 5], { roughness: 0.5 }))); return { m, u0: k / 14 }; });
  // 소파(컨베이어 위에 놓여 있음, C5에서 실려 감)
  const sofa = new THREE.Group(); g.add(sofa); sofa.scale.setScalar(1.5);
  const sofaMat = clay('#ff9fb2', { roughness: 0.6 });
  add(new THREE.Mesh(new RoundedBoxGeometry(0.95, 0.16, 0.5, 4, 0.07), sofaMat), 'sofa', sofa).position.y = 0.08;
  add(new THREE.Mesh(new RoundedBoxGeometry(0.95, 0.32, 0.14, 4, 0.06), sofaMat), 'sofa', sofa).position.set(0, 0.3, -0.19);
  for (const s of [-1, 1]) add(new THREE.Mesh(new RoundedBoxGeometry(0.14, 0.24, 0.5, 4, 0.06), sofaMat), 'sofa', sofa).position.set(s * 0.47, 0.2, 0);
  let SOFA_U = 0; { let best = 9; for (let k = 0; k < 400; k++) { const q = curve.getPointAt(k / 400); const d = Math.hypot(q.x + 1.6, q.z - 1.0); if (d < best) { best = d; SOFA_U = k / 400; } } }
  // 발효병(뒤 벽 앞 선반): 빛나는 미생물 + 올라가는 기포
  const jars = [], microMat = glow('#d6ffb0', '#8cff6a', 1.4), bubMat = new THREE.MeshPhysicalMaterial({ color: '#ffffff', roughness: 0.05, transparent: true, opacity: 0.5 });
  const jarGlass = new THREE.MeshPhysicalMaterial({ color: '#d9fff0', roughness: 0.03, transparent: true, opacity: 0.25, side: THREE.DoubleSide, depthWrite: false });
  for (let k = 0; k < 6; k++) { const a = -1.05 + k * 0.42, [x, , z] = onWallPos(R - 0.55, a, 0), h = 1.0 + (k % 3) * 0.25;
    const base = add(new THREE.Mesh(new THREE.CylinderGeometry(0.32, 0.34, 0.12, 32), brass()), 'jar'); base.position.set(x, 0.06, z);
    const jar = add(new THREE.Mesh(new THREE.CylinderGeometry(0.28, 0.28, h, 32, 1, true), jarGlass), 'jar'); jar.position.set(x, 0.12 + h / 2, z);
    const liquid = new THREE.Mesh(new THREE.CylinderGeometry(0.26, 0.26, h * 0.8, 32), new THREE.MeshPhysicalMaterial({ color: '#7fe3b8', roughness: 0.1, transparent: true, opacity: 0.35, emissive: '#2a9a6a', emissiveIntensity: 0.4 })); liquid.position.set(x, 0.12 + h * 0.4, z); g.add(liquid);
    const lid = add(new THREE.Mesh(new THREE.CylinderGeometry(0.3, 0.3, 0.08, 32), brass()), 'jar'); lid.position.set(x, 0.12 + h + 0.04, z);
    const mic = new THREE.InstancedMesh(new THREE.SphereGeometry(0.028, 8, 6), microMat, 26); g.add(mic);
    const bub = new THREE.InstancedMesh(new THREE.SphereGeometry(0.02, 8, 6), bubMat, 12); g.add(bub);
    jars.push({ x, z, h, mic, bub, seeds: Array.from({ length: 38 }, () => [rnd(), rnd(), rnd() * 6]) }); }
  // 장의 실험대(왼쪽 앞)
  const bench = new THREE.Group(); bench.position.set(1.55, 0, 2.05); bench.rotation.y = Math.PI + 0.5; g.add(bench);
  add(new THREE.Mesh(new RoundedBoxGeometry(1.0, 0.08, 0.5, 3, 0.03), clay('#e9f7f0', { roughness: 0.4 })), 'bench', bench).position.y = 0.62;
  for (const [x, z] of [[-0.42, -0.18], [0.42, -0.18], [-0.42, 0.18], [0.42, 0.18]]) add(new THREE.Mesh(new THREE.CylinderGeometry(0.025, 0.025, 0.6, 8), brass()), 'bench', bench).position.set(x, 0.3, z);
  for (let k = 0; k < 4; k++) { const fl = add(new THREE.Mesh(new THREE.SphereGeometry(0.07, 16, 12), new THREE.MeshPhysicalMaterial({ color: ['#fff3a3', '#a3ffd6', '#ffb3c9', '#b3d7ff'][k], roughness: 0.1, transparent: true, opacity: 0.8, emissive: ['#ffd86a', '#5affb0', '#ff7aa0', '#7ab8ff'][k], emissiveIntensity: 0.5 })), 'bench', bench); fl.position.set(-0.3 + k * 0.2, 0.73, -0.05); }

  const W = makeWorld({ sky: ['#0f2a2a', '#1f6a5e', '#bfffd8', '#3aa88a', '#0b2422'], tube: '#d0ffe8', cell: '#c8ffd6', cellE: '#4aff9a', tower: '#173a34', win: '#a8ffcf', motes: '#d8fff0', seed: 41, cellShape: 'bubble' });
  g.add(W.world);
  const M4 = new THREE.Matrix4(), V = new THREE.Vector3(), Q = new THREE.Quaternion(), S1 = new THREE.Vector3(1, 1, 1);
  const beltAt = u => { const p = curve.getPointAt(((u % 1) + 1) % 1), tn = curve.getTangentAt(((u % 1) + 1) % 1); return { p, yaw: Math.atan2(tn.x, tn.z) }; };
  let beltOn = 1, beltT = 0;
  const setTime = (t, { belt: speed = 1 } = {}) => {
    W.setTime(t);
    beltTex.offset.y = -t * 0.35 * speed / 0.5;
    parcels.forEach(o => { const { p, yaw } = beltAt(o.u0 + t * 0.35 * speed / L); o.m.position.set(p.x, BELT_Y + 0.08, p.z); o.m.rotation.y = yaw; });
    jars.forEach(j => { j.seeds.forEach((sd, k) => { if (k < 26) { V.set(j.x + Math.cos(sd[2] + t * 0.7) * 0.18 * sd[0], 0.2 + ((sd[1] + Math.sin(t * 0.5 + sd[2]) * 0.05) % 1) * j.h * 0.75, j.z + Math.sin(sd[2] + t * 0.7) * 0.18 * sd[0]); M4.compose(V, Q, S1); j.mic.setMatrixAt(k, M4); }
      else { const kk = k - 26; V.set(j.x + (sd[0] - 0.5) * 0.3, 0.15 + ((sd[1] + t * 0.25) % 1) * j.h * 0.8, j.z + (sd[2] / 6 - 0.5) * 0.3); M4.compose(V, Q, S1); j.bub.setMatrixAt(kk, M4); } });
      j.mic.instanceMatrix.needsUpdate = true; j.bub.instanceMatrix.needsUpdate = true; });
  };
  setTime(0);
  // 소파 위치: u(컨베이어 위 위치)
  const setSofa = u => { const { p, yaw } = beltAt(u); sofa.position.set(p.x, BELT_Y + 0.003, p.z); sofa.rotation.y = yaw + Math.PI / 2; return { p, yaw, rot: yaw + Math.PI / 2 }; };
  setSofa(SOFA_U);
  return { group: g, SOLID, setTime, atmo: { fog: '#3a9a7e', near: 7, far: 55 }, beltAt, setSofa, SOFA_U, BELT_Y, beltLen: L, bench, SEAT_Y: BELT_Y + 0.003 + 0.16 * 1.5 };
}
