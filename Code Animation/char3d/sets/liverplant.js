// 간의 정화 공장 — 호박색. 거대한 여과 탱크(층층 거름망), 끈적한 병 상자 더미 → 깨끗한 물병 선반, 똑똑 떨어지는 관, 천천히 도는 거름 물레방아
import * as THREE from 'three';
import { RoundedBoxGeometry } from 'three/addons/geometries/RoundedBoxGeometry.js';
import { clay } from '../chars3d.js';
import { canvasTex, mat, brass, glow, rng, setKit, makeWorld, platform, railing, onWallPos } from './common.js';

const R = 3.6;
export function buildLiverPlant() {
  const kit = setKit(), { g, SOLID, add } = kit, rnd = rng(53);
  platform(kit, R, (c, w, h) => {   // 호박색 철판 바닥(리벳 줄)
    c.fillStyle = '#8a5a2e'; c.fillRect(0, 0, w, h);
    for (let y = 0; y < h; y += 256) for (let x = 0; x < w; x += 256) { c.fillStyle = ((x + y) / 256) % 2 ? '#9a6836' : '#a37040'; c.fillRect(x + 4, y + 4, 248, 248);
      c.fillStyle = '#d9a441'; for (let k = 0; k < 4; k++) for (const [ox, oy] of [[16, 16], [240, 16], [16, 240], [240, 240]]) { c.beginPath(); c.arc(x + ox, y + oy, 7, 0, 7); c.fill(); } }
  }, '#3a2410', ['#ffd38a', '#ffae3a']);
  railing(kit, R, [[1.2, Math.PI * 2 - 1.2]], brass(), mat('#4a2e14', { roughness: 0.6 }));
  // 뒤: 여과 탱크 3개(유리 속 호박색 물 + 거름망 층) — 관으로 이어짐
  const tankGlass = new THREE.MeshPhysicalMaterial({ color: '#fff0d0', roughness: 0.03, transparent: true, opacity: 0.22, side: THREE.DoubleSide, depthWrite: false });
  const liquids = [], drips = [];
  [[-0.75, 2.6, 0.62], [0, 3.1, 0.75], [0.75, 2.4, 0.6]].forEach(([a, h, r], i) => {
    const [x, , z] = onWallPos(R - 0.85, a, 0);
    add(new THREE.Mesh(new THREE.CylinderGeometry(r + 0.06, r + 0.1, 0.25, 40), brass()), 'tank').position.set(x, 0.125, z);
    add(new THREE.Mesh(new THREE.CylinderGeometry(r, r, h, 40, 1, true), tankGlass), 'tank').position.set(x, 0.25 + h / 2, z);
    const lq = new THREE.Mesh(new THREE.CylinderGeometry(r - 0.02, r - 0.02, 1, 40), new THREE.MeshPhysicalMaterial({ color: '#ffb84a', roughness: 0.1, transparent: true, opacity: 0.45, emissive: '#c46a10', emissiveIntensity: 0.6 }));
    g.add(lq); liquids.push({ lq, x, z, h, ph: i * 1.7 });
    for (let k = 1; k < 4; k++) { const sv = new THREE.Mesh(new THREE.CylinderGeometry(r - 0.03, r - 0.03, 0.03, 40), new THREE.MeshStandardMaterial({ color: '#e8d2a6', roughness: 0.8, wireframe: k % 2 === 0 })); sv.position.set(x, 0.25 + h * k / 4, z); g.add(sv); }
    for (const y of [0.3, 0.25 + h - 0.05]) { const band = add(new THREE.Mesh(new THREE.TorusGeometry(r + 0.02, 0.04, 8, 40), brass())); band.rotation.x = Math.PI / 2; band.position.set(x, y, z); }
    add(new THREE.Mesh(new THREE.SphereGeometry(r + 0.02, 40, 16, 0, Math.PI * 2, 0, Math.PI / 2), brass()), 'tank').position.set(x, 0.25 + h, z);
    // 탱크 앞 수도꼭지 → 아래 대야로 똑똑
    const [fx, , fz] = onWallPos(R - 0.85 - r - 0.12, a, 0);
    const tap = add(new THREE.Mesh(new THREE.CylinderGeometry(0.035, 0.035, 0.22, 10), brass())); tap.rotation.x = Math.PI / 2; tap.position.set(fx, 0.85, fz);
    const basin = add(new THREE.Mesh(new THREE.CylinderGeometry(0.16, 0.12, 0.12, 24, 1, true), brass({ side: THREE.DoubleSide })), 'tank'); basin.position.set(fx, 0.06, fz);
    const d = new THREE.Mesh(new THREE.SphereGeometry(0.03, 10, 8), glow('#fff0c0', '#ffc860', 1.0)); g.add(d); drips.push({ d, x: fx, z: fz, ph: i * 0.37 });
  });
  // 거름 물레방아(오른쪽 뒤): 천천히 돌며 물을 퍼 올림
  const wheel = new THREE.Group(); const [wx, , wz] = onWallPos(R - 0.7, 1.15, 0); wheel.position.set(wx, 1.15, wz); wheel.rotation.y = -1.15 + Math.PI / 2; g.add(wheel);
  const spin = new THREE.Group(); wheel.add(spin);
  for (const zz of [-0.18, 0.18]) { const rimW = add(new THREE.Mesh(new THREE.TorusGeometry(0.95, 0.05, 10, 48), brass()), 'wheel', spin); rimW.position.z = zz; }
  for (let k = 0; k < 10; k++) { const a = k / 10 * Math.PI * 2; const pad = add(new THREE.Mesh(new RoundedBoxGeometry(0.28, 0.06, 0.4, 2, 0.02), clay('#c98f5b', { roughness: 0.6 })), 'wheel', spin); pad.position.set(Math.cos(a) * 0.95, Math.sin(a) * 0.95, 0); pad.rotation.z = a;
    const sp = add(new THREE.Mesh(new THREE.CylinderGeometry(0.02, 0.02, 0.95, 8), brass()), null, spin); sp.position.set(Math.cos(a) * 0.475, Math.sin(a) * 0.475, 0); sp.rotation.z = a + Math.PI / 2; }
  add(new THREE.Mesh(new THREE.CylinderGeometry(0.1, 0.1, 0.5, 20), brass()), 'wheel', spin).rotation.x = Math.PI / 2;
  add(new THREE.Mesh(new THREE.BoxGeometry(0.1, 1.15, 0.1), brass()), 'wheel', wheel).position.set(0, -0.575, 0.3);
  add(new THREE.Mesh(new THREE.BoxGeometry(0.1, 1.15, 0.1), brass()), 'wheel', wheel).position.set(0, -0.575, -0.3);
  // 끈적한 병 더미(왼쪽): 나무 상자 + 짙은 병들
  const crateMat = clay('#b07a45', { roughness: 0.7 }), sticky = new THREE.MeshPhysicalMaterial({ color: '#5a2a10', roughness: 0.25, clearcoat: 0.8, transparent: true, opacity: 0.92 });
  const bottleGeo = new THREE.LatheGeometry([[0, 0], [0.06, 0], [0.065, 0.01], [0.065, 0.16], [0.03, 0.21], [0.025, 0.27], [0.03, 0.28], [0, 0.28]].map(p => new THREE.Vector2(...p)), 20);
  const stacks = [[-1.7, 0.35, 0.3], [-1.35, 0.95, -0.2], [-2.0, -0.35, 0.6]];
  stacks.forEach(([x, z, ry], si) => { const cr = new THREE.Group(); cr.position.set(x, 0, z); cr.rotation.y = ry; g.add(cr);
    const levels = si === 1 ? 2 : 1;
    for (let lv = 0; lv < levels; lv++) { add(new THREE.Mesh(new RoundedBoxGeometry(0.62, 0.22, 0.46, 2, 0.02), crateMat), 'crate', cr).position.y = 0.11 + lv * 0.5;
      for (let i = 0; i < 3; i++) for (let j = 0; j < 2; j++) { const b = add(new THREE.Mesh(bottleGeo, sticky), 'crate', cr); b.position.set(-0.18 + i * 0.18, 0.22 + lv * 0.5, -0.1 + j * 0.2); } } });
  // 깨끗한 물병 선반(오른쪽 앞)
  const shelf = new THREE.Group(); shelf.position.set(2.05, 0, 0.3); shelf.rotation.y = -0.9; g.add(shelf);
  for (const y of [0.35, 0.8]) add(new THREE.Mesh(new RoundedBoxGeometry(0.9, 0.05, 0.32, 2, 0.015), clay('#c98f5b', { roughness: 0.6 })), 'shelf', shelf).position.y = y;
  for (const x of [-0.42, 0.42]) add(new THREE.Mesh(new THREE.BoxGeometry(0.04, 0.85, 0.3), brass()), 'shelf', shelf).position.set(x, 0.425, 0);
  const clean = new THREE.MeshPhysicalMaterial({ color: '#e8fbff', roughness: 0.02, transparent: true, opacity: 0.55, emissive: '#9fe8ff', emissiveIntensity: 0.25 });
  for (const y of [0.375, 0.825]) for (let i = 0; i < 5; i++) add(new THREE.Mesh(bottleGeo, clean), 'shelf', shelf).position.set(-0.32 + i * 0.16, y, 0);
  // 양동이 + 세워 둔 여분 대걸레
  const bucket = add(new THREE.Mesh(new THREE.CylinderGeometry(0.17, 0.13, 0.26, 24, 1, true), clay('#3CC7B4', { side: THREE.DoubleSide })), 'bucket'); bucket.position.set(-1.5, 0.13, 1.45);
  const water = new THREE.Mesh(new THREE.CircleGeometry(0.16, 24), new THREE.MeshPhysicalMaterial({ color: '#d8f6ff', roughness: 0.05, transparent: true, opacity: 0.7 })); water.rotation.x = -Math.PI / 2; water.position.set(-1.5, 0.22, 1.45); g.add(water);
  // 간의 작업 자리(가운데 왼쪽): 병을 붓는 깔때기 거름대
  const station = new THREE.Group(); station.position.set(0.84, 0, 0.38); g.add(station);   // 간 오른손 옆, 붓기 좋은 높이로 낮춘 깔때기
  add(new THREE.Mesh(new THREE.CylinderGeometry(0.22, 0.07, 0.24, 32, 1, true), brass({ side: THREE.DoubleSide })), 'station', station).position.y = 0.24;
  const pool = new THREE.Mesh(new THREE.CircleGeometry(0.19, 32), new THREE.MeshPhysicalMaterial({ color: '#5a2a10', roughness: 0.2, clearcoat: 0.8 })); pool.rotation.x = -Math.PI / 2; pool.position.y = 0.31; station.add(pool);
  add(new THREE.Mesh(new THREE.CylinderGeometry(0.045, 0.045, 0.12, 12), brass()), 'station', station).position.y = 0.06;
  add(new THREE.Mesh(new THREE.CylinderGeometry(0.2, 0.22, 0.03, 24), brass()), 'station', station).position.y = 0.015;

  const W = makeWorld({ sky: ['#2a1606', '#7a3e10', '#ffd27a', '#c46a1a', '#2a1404'], tube: '#fff0d0', cell: '#ffd98a', cellE: '#ffaa2a', tower: '#3a220e', win: '#ffd890', motes: '#ffe8c0', seed: 61, cellShape: 'drop' });
  g.add(W.world);
  const setTime = t => {
    W.setTime(t);
    spin.rotation.z = -t * 0.35;
    liquids.forEach(l => { const lev = 0.55 + 0.08 * Math.sin(t * 0.6 + l.ph); l.lq.scale.y = l.h * lev; l.lq.position.set(l.x, 0.26 + l.h * lev / 2, l.z); });
    drips.forEach(d => { const u = ((t * 1.3 + d.ph) % 1); d.d.position.set(d.x, 0.78 - u * u * 0.7, d.z); d.d.scale.setScalar(u < 0.05 ? u * 20 : 1); });
  };
  setTime(0);
  const stream = new THREE.Mesh(new THREE.CylinderGeometry(0.016, 0.022, 1, 10), new THREE.MeshPhysicalMaterial({ color: '#6a3212', roughness: 0.15, clearcoat: 1, transparent: true, opacity: 0.9 })); stream.visible = false; g.add(stream);
  return { group: g, SOLID, setTime, atmo: { fog: '#b0601e', near: 7, far: 55 }, station, stream };
}
