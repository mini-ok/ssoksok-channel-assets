// 혈관 복도 — 둥근 반투명 분홍 터널, 빛나는 고리, 바닥 통로 옆으로 굴러가는 적혈구, 부서별 둥근 문 3개(장=민트 기포, 간=호박 물방울, 뇌=보라 별), 끝에 펌프 공장 문
import * as THREE from 'three';
import { RoundedBoxGeometry } from 'three/addons/geometries/RoundedBoxGeometry.js';
import { clay } from '../chars3d.js';
import { canvasTex, mat, brass, glow, rng, setKit, makeWorld } from './common.js';

const LEN = 16, TR = 1.7;
export const DOORS = { gut: -4.5, liver: -1.0, brain: 2.5 };   // 문 중심 x(문은 뒤쪽 z = -DOOR_Z)
export const DOOR_Z = 1.25;
export function buildCorridor() {
  const kit = setKit(), { g, SOLID, add } = kit, rnd = rng(19);
  // 바닥 통로
  const floorTex = canvasTex(1024, 256, (c, w, h) => { c.fillStyle = '#c9707e'; c.fillRect(0, 0, w, h); for (let x = 0; x < w; x += 64) { c.fillStyle = (x / 64) % 2 ? '#d47f8c' : '#be6674'; c.fillRect(x + 2, 4, 60, h - 8); } c.fillStyle = '#ffd0a8'; c.fillRect(0, 0, w, 6); c.fillRect(0, h - 6, w, 6); });
  floorTex.wrapS = THREE.RepeatWrapping; floorTex.repeat.set(LEN / 4, 1);
  const floor = add(new THREE.Mesh(new THREE.PlaneGeometry(LEN, 2.4), mat('#ffffff', { map: floorTex, roughness: 0.5, clearcoat: 0.3 }))); floor.rotation.x = -Math.PI / 2;
  // 터널: 반투명 분홍 관(위·옆) + 빛 고리
  const tube = new THREE.Mesh(new THREE.CylinderGeometry(TR, TR, LEN, 48, 1, true, Math.PI * 0.5, Math.PI), new THREE.MeshPhysicalMaterial({ color: '#ffc8d4', roughness: 0.15, transparent: true, opacity: 0.32, side: THREE.DoubleSide, depthWrite: false }));
  tube.rotation.z = Math.PI / 2; tube.position.y = 0.0; g.add(tube);
  const inv = new THREE.Mesh(new THREE.CylinderGeometry(TR, TR, LEN, 24, 1, true, Math.PI * 0.5, Math.PI)); inv.rotation.z = Math.PI / 2; inv.visible = false; inv.name = 'wall'; g.add(inv); SOLID.push(inv);
  const ringMat = glow('#ffe0d0', '#ff8a8a', 0.4), rings = [];
  for (let k = 0; k <= 16; k++) { const r = new THREE.Mesh(new THREE.TorusGeometry(TR, 0.03, 8, 48, Math.PI), ringMat); r.rotation.y = Math.PI / 2; r.position.x = -LEN / 2 + k; g.add(r); rings.push(r); }
  // 문 3개(뒤쪽 벽 대신 둥근 문틀이 터널 벽에 박힘)
  const doors = {};
  const emblem = { gut: ['#5affc0', 'bubble'], liver: ['#ffae3a', 'drop'], brain: ['#a88aff', 'star'] };
  for (const [id, x] of Object.entries(DOORS)) {
    const fr = new THREE.Group(); fr.position.set(x, 0, -DOOR_Z); g.add(fr);
    const [col, kind] = emblem[id];
    const arch = add(new THREE.Mesh(new THREE.TorusGeometry(0.62, 0.08, 12, 40, Math.PI), brass()), 'doorframe', fr); arch.position.y = 1.0;
    for (const sx of [-1, 1]) add(new THREE.Mesh(new THREE.BoxGeometry(0.16, 1.0, 0.16), brass()), 'doorframe', fr).position.set(sx * 0.62, 0.5, 0);
    const hole = new THREE.Mesh(new THREE.CircleGeometry(0.6, 32, 0, Math.PI), new THREE.MeshBasicMaterial({ color: '#2a0f18' })); hole.position.set(0, 1.0, -0.06); fr.add(hole);
    const holeB = new THREE.Mesh(new THREE.PlaneGeometry(1.2, 1.0), new THREE.MeshBasicMaterial({ color: '#2a0f18' })); holeB.position.set(0, 0.5, -0.06); fr.add(holeB);
    const lit = new THREE.PointLight(col, 0, 3, 1.5); lit.position.set(0, 1.0, 0.4); fr.add(lit);
    // 문짝(왼쪽 경첩으로 열림)
    const hinge = new THREE.Group(); hinge.position.set(-0.6, 0, 0.02); fr.add(hinge);
    const leafShape = new THREE.Shape(); leafShape.moveTo(0, 0); leafShape.lineTo(1.2, 0); leafShape.lineTo(1.2, 1.0); leafShape.absarc(0.6, 1.0, 0.6, 0, Math.PI, false); leafShape.lineTo(0, 0);
    const leaf = add(new THREE.Mesh(new THREE.ExtrudeGeometry(leafShape, { depth: 0.06, bevelEnabled: true, bevelSize: 0.015, bevelThickness: 0.015, bevelSegments: 2 }), clay(col, { roughness: 0.4 })), 'door', hinge);
    const em = new THREE.Mesh(new THREE.CircleGeometry(0.22, 32), new THREE.MeshBasicMaterial({ map: canvasTex(128, 128, c => { c.fillStyle = '#fff8ee'; c.beginPath(); c.arc(64, 64, 62, 0, 7); c.fill(); c.fillStyle = col; c.strokeStyle = col; c.lineWidth = 8;
      if (kind === 'bubble') { for (const [x2, y2, r2] of [[52, 70, 22], [82, 46, 14], [84, 84, 10]]) { c.beginPath(); c.arc(x2, y2, r2, 0, 7); c.stroke(); } }
      else if (kind === 'drop') { c.beginPath(); c.moveTo(64, 20); c.quadraticCurveTo(100, 70, 64, 104); c.quadraticCurveTo(28, 70, 64, 20); c.fill(); }
      else { c.beginPath(); for (let k = 0; k < 5; k++) { const a = -Math.PI / 2 + k * 4 * Math.PI / 5; c.lineTo(64 + 42 * Math.cos(a), 66 + 42 * Math.sin(a)); } c.closePath(); c.fill(); } }) }));
    em.position.set(0.6, 1.0, 0.085); hinge.add(em);
    const knob = add(new THREE.Mesh(new THREE.SphereGeometry(0.045, 12, 8), brass()), null, hinge); knob.position.set(1.05, 0.65, 0.1);
    doors[id] = { hinge, lit, x };
  }
  // 오른쪽 끝: 펌프 공장 문(따뜻한 빛)
  const endGlow = new THREE.Mesh(new THREE.CircleGeometry(1.3, 40), new THREE.MeshBasicMaterial({ color: '#ffb08a' })); endGlow.rotation.y = -Math.PI / 2; endGlow.position.set(LEN / 2 - 0.05, 0.9, 0); g.add(endGlow);
  const endL = new THREE.PointLight('#ffb070', 3, 8, 1.4); endL.position.set(LEN / 2 - 0.8, 1.2, 0); g.add(endL);
  // 굴러가는 적혈구(통로 양옆 홈)
  const cells = new THREE.InstancedMesh(new THREE.TorusGeometry(0.11, 0.06, 10, 18), clay('#ff5a6a', { roughness: 0.45, emissive: '#ff2a3a', emissiveIntensity: 0.3 }), 40); g.add(cells);
  const cellP = Array.from({ length: 40 }, (_, k) => [rnd(), k % 2 ? 1.05 : -1.05, rnd() * 6]);
  // 천장 쪽 표지 빛줄(펌프 공장 방향 화살표 대신 흐르는 빛)
  const stream = new THREE.InstancedMesh(new THREE.SphereGeometry(0.035, 8, 6), glow('#fff0e0', '#ffb08a', 2), 30); g.add(stream);
  const W = makeWorld({ sky: ['#2a1028', '#6a2448', '#ff9ab0', '#a0386a', '#1e0a1a'], tube: '#ffd8e4', cell: '#ff7a8a', cellE: '#ff3a5a', tower: '#3a1428', win: '#ffc8b0', motes: '#ffd8e0', seed: 23 });
  g.add(W.world);
  const M4 = new THREE.Matrix4(), V = new THREE.Vector3(), Q = new THREE.Quaternion(), S1 = new THREE.Vector3(1, 1, 1), E = new THREE.Euler();
  let level = 1;
  const setTime = (t, { flow = 1 } = {}) => {
    W.setTime(t, flow);
    cellP.forEach((p, k) => { const x = -LEN / 2 + ((p[0] * LEN + t * 1.6 * flow) % LEN); V.set(x, 0.1, p[1] * (k % 4 < 2 ? 1 : 1)); Q.setFromEuler(E.set(0, 0, -(t * 1.6 * flow) / 0.11 + p[2])); M4.compose(V, Q, S1); cells.setMatrixAt(k, M4); });
    cells.instanceMatrix.needsUpdate = true;
    for (let k = 0; k < 30; k++) { const x = -LEN / 2 + ((k / 30 * LEN + t * 2.5 * flow) % LEN); V.set(x, TR - 0.15, 0); M4.compose(V, Q.identity(), S1); stream.setMatrixAt(k, M4); }
    stream.instanceMatrix.needsUpdate = true;
  };
  const setDoor = (id, open = 0, light = 0) => { doors[id].hinge.rotation.y = open * 1.6; doors[id].lit.intensity = light; };
  const setLevel = v => { ringMat.emissiveIntensity = 0.4 * v; endL.intensity = 3 * v; endGlow.material.color.set(v > 0.3 ? '#ffb08a' : '#5a2a30'); };
  setTime(0);
  return { group: g, SOLID, setTime, setDoor, setLevel, atmo: { fog: '#8a3058', near: 6, far: 50 }, DOORS, DOOR_Z, LEN };
}
