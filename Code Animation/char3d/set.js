// 연기 샘플 세트: 뒤 벽 + 벽 선반(오른쪽 위) + 왼쪽 나무 발판. SOLID = 충돌 검사 대상
import * as THREE from 'three';
import { RoundedBoxGeometry } from 'three/addons/geometries/RoundedBoxGeometry.js';
const wood = c => new THREE.MeshPhysicalMaterial({ color: c, roughness: 0.6, clearcoat: 0.2, clearcoatRoughness: 0.5 });
export function buildSet() {
  const set = new THREE.Group(); const SOLID = [];
  { const W2 = wood('#c98d5a'), W3 = wood('#b0764a');
  const wall = new THREE.Mesh(new THREE.BoxGeometry(8, 3, 0.1), new THREE.MeshStandardMaterial({ color: '#efe3d3', roughness: 0.95 }));
  wall.position.set(0, 1.5, -0.5); wall.name = 'wall'; set.add(wall); SOLID.push(wall);
  const board = new THREE.Mesh(new RoundedBoxGeometry(0.85, 0.05, 0.5, 3, 0.012), W2); board.position.set(1.15, 1.02, -0.2); board.name = 'shelf'; set.add(board); SOLID.push(board);
  for (const sx of [-0.3, 0.3]) { const br2 = new THREE.Mesh(new RoundedBoxGeometry(0.04, 0.16, 0.2, 2, 0.008), W3); br2.position.set(1.15 + sx, 0.925, -0.35); br2.name = 'bracket'; set.add(br2); SOLID.push(br2); }
  const bx = new THREE.Mesh(new RoundedBoxGeometry(0.27, 0.215, 0.2, 3, 0.02), wood('#E8B56B')); bx.position.set(1.38, 1.153, -0.25); bx.name = 'shelfbox'; set.add(bx); SOLID.push(bx);
  const pot = new THREE.Mesh(new THREE.CylinderGeometry(0.07, 0.055, 0.12, 24), wood('#7fb7a4')); pot.position.set(0.92, 1.105, -0.25); pot.name = 'pot'; set.add(pot); SOLID.push(pot);
  const stool = new THREE.Group(); stool.position.set(-0.75, 0, -0.1); stool.rotation.y = 0.35; set.add(stool);
  const top = new THREE.Mesh(new RoundedBoxGeometry(0.42, 0.06, 0.3, 3, 0.02), W2); top.position.y = 0.27; top.name = 'stool'; stool.add(top); SOLID.push(top);
  for (const sx of [-0.17, 0.17]) { const l = new THREE.Mesh(new RoundedBoxGeometry(0.05, 0.24, 0.28, 2, 0.01), W3); l.position.set(sx, 0.12, 0); l.name = 'stool'; stool.add(l); SOLID.push(l); }
  set.traverse(o => { if (o.isMesh) { o.castShadow = o.receiveShadow = true; } });
}
  return { set, SOLID };
}
