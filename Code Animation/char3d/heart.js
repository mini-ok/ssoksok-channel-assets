// 심장(배달기사) 3D 캐릭터 — 쏙쏙 건강백과 2D 디자인(chars.py heart)을 부풀린 몸 + 관절 그룹 리그
import * as THREE from 'three';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { RoundedBoxGeometry } from 'three/addons/geometries/RoundedBoxGeometry.js';
import { drawFace } from './face.js';

const PX = 1 / 300;                      // chars.py 1px → 3D 단위
const p2 = (x, y) => [x * PX, -y * PX];   // 2D(y 아래 +) → 3D(y 위 +)
export const INK = '#2B2D5B';

function clay(color, o = {}) {
  return new THREE.MeshPhysicalMaterial({ color, roughness: 0.42, sheen: 0.0, sheenRoughness: 0.6, sheenColor: new THREE.Color(color).lerp(new THREE.Color('#fff'), 0.5),
    clearcoat: 0.3, clearcoatRoughness: 0.35, ...o });
}
function outlineOf(mesh, w) {
  const m = new THREE.MeshBasicMaterial({ color: INK, side: THREE.BackSide });
  m.onBeforeCompile = s => { s.vertexShader = s.vertexShader.replace('#include <begin_vertex>', `vec3 transformed = position + normal * ${w.toFixed(4)};`); };
  const o = new THREE.Mesh(mesh.geometry, m); o.userData.outline = true; o.castShadow = false; mesh.add(o); return o;
}

// 얼굴+몸색 캔버스(앞면에 평면 투영)
const TEX = 2048, SPAN = 1.2;            // 텍스처가 덮는 범위 [-0.6, 0.6]
function makeBodyCanvas() { const cv = document.createElement('canvas'); cv.width = cv.height = TEX; return cv; }
function paintBody(cv, st) {
  const c = cv.getContext('2d'), k = TEX / SPAN;   // 3D 단위 → 캔버스 px
  c.setTransform(1, 0, 0, 1, 0, 0);
  c.fillStyle = '#FF7A93'; c.fillRect(0, 0, TEX, TEX);
  const g = c.createRadialGradient(TEX * 0.38, TEX * 0.3, 0, TEX * 0.38, TEX * 0.3, TEX * 0.5);
  g.addColorStop(0, '#FFB3C1'); g.addColorStop(1, 'rgba(255,122,147,0)'); c.fillStyle = g; c.fillRect(0, 0, TEX, TEX);
  // 얼굴: chars.py heart의 face(cv, 0, -20) → 3D (0, 0.0667)
  const [fx, fy] = p2(0, -20);
  c.setTransform(k * PX, 0, 0, k * PX, TEX / 2 + fx * k, TEX / 2 - fy * k);
  drawFace(c, st.mood, { blush: '#FFD0DA', look: st.look, blink: st.blink });
}

export async function buildHeart({ outline = false, bodyUrl = 'cache/heart_body.glb' } = {}) {
  const C0 = '#FF7A93', OUT = 0.019;
  const root = new THREE.Group();                       // 바닥 기준(발바닥 = y 0)
  const squash = new THREE.Group(); root.add(squash);   // 스쿼시·스트레치(발 높이가 피벗)
  const hip = new THREE.Group(); hip.position.y = 0.06; squash.add(hip);         // 기울기 피벗(발 바로 위)
  const body = new THREE.Group(); body.position.y = 0.497; hip.add(body);   // 몸 중심

  const gl = await new GLTFLoader().loadAsync(bodyUrl);
  let bodyGeo; gl.scene.traverse(o => { if (o.isMesh) bodyGeo = o.geometry; });
  bodyGeo.computeVertexNormals();
  const pos = bodyGeo.attributes.position, uv = new Float32Array(pos.count * 2);
  for (let i = 0; i < pos.count; i++) {
    const front = pos.getZ(i) > 0.02;
    uv[i * 2] = front ? pos.getX(i) / SPAN + 0.5 : 0.02; uv[i * 2 + 1] = front ? pos.getY(i) / SPAN + 0.5 : 0.98;
  }
  bodyGeo.setAttribute('uv', new THREE.BufferAttribute(uv, 2));
  const cv = makeBodyCanvas(); const tex = new THREE.CanvasTexture(cv); tex.colorSpace = THREE.SRGBColorSpace; tex.anisotropy = 8;
  const bodyMat = clay('#ffffff', { map: tex });
  const bodyMesh = new THREE.Mesh(bodyGeo, bodyMat); bodyMesh.name = 'body'; bodyMesh.castShadow = bodyMesh.receiveShadow = true; body.add(bodyMesh);

  const parts = [bodyMesh];
  // 팔: 어깨 피벗 → 아래(-Y)로 뻗은 캡슐 + 손
  const armMat = clay(C0);
  function arm(sx, sy) {
    // 어깨 피벗 → 위팔 → 팔꿈치 피벗 → 아래팔 → 손 (팔꿈치는 앞쪽으로 굽힘)
    const piv = new THREE.Group(); const [x, y] = p2(sx, sy); piv.position.set(x, y, 0.0); body.add(piv);
    const L1 = 0.1, L2 = 0.1, r = 0.05;
    const up = new THREE.Mesh(new THREE.CapsuleGeometry(r, L1, 8, 20), armMat); up.position.y = -L1 / 2; piv.add(up);
    const elbow = new THREE.Group(); elbow.position.y = -L1; piv.add(elbow);
    const lo = new THREE.Mesh(new THREE.CapsuleGeometry(r * 0.98, L2, 8, 20), armMat); lo.position.y = -L2 / 2; elbow.add(lo);
    const hand = new THREE.Mesh(new THREE.SphereGeometry(0.062, 32, 20), armMat); hand.position.y = -L2 - 0.01; elbow.add(hand);
    const tag = sx < 0 ? 'L' : 'R'; up.name = 'up' + tag; lo.name = 'lo' + tag; hand.name = 'hand' + tag;
    [up, lo, hand].forEach(m => { m.castShadow = true; parts.push(m); });
    return { piv, elbow, hand };
  }
  const armL = arm(-148, 12), armR = arm(148, 14);   // 어깨를 몸 테두리 살짝 바깥에(팔을 들어도 윗볼을 통과하지 않게)
  // 발: 바닥에 붙은 납작한 타원체(스쿼시 영향 안 받음)
  const footMat = clay('#F06A85');
  const feet = [-1, 1].map(s => {
    const g = new THREE.Group(); g.position.set(s * 46 * PX, 0, 0.04); root.add(g);
    const m = new THREE.Mesh(new THREE.SphereGeometry(1, 32, 20), footMat); m.scale.set(0.105, 0.058, 0.115); m.position.y = 0.058;
    m.name = s < 0 ? 'footL' : 'footR'; m.castShadow = m.receiveShadow = true; g.add(m); parts.push(m); return g;
  });
  // 모자: chars.py translate(60,-130) rotate(18°)
  const cap = new THREE.Group(); { const [x, y] = p2(60, -128); cap.position.set(x, y, 0.02); cap.rotation.z = -18 * Math.PI / 180; } body.add(cap);
  const capMat = clay('#3D8BFF'), brimMat = clay('#2C6FD6');
  const dome = new THREE.Mesh(new THREE.SphereGeometry(1, 40, 20, 0, Math.PI * 2, 0, Math.PI / 2), capMat); dome.scale.set(0.235, 0.2, 0.22); cap.add(dome);
  const domeBase = new THREE.Mesh(new THREE.CircleGeometry(1, 40), capMat); domeBase.rotation.x = Math.PI / 2; domeBase.scale.set(0.235, 0.22, 1); cap.add(domeBase);
  const brim = new THREE.Mesh(new RoundedBoxGeometry(0.34, 0.06, 0.22, 4, 0.028), brimMat); brim.position.set(0.15, 0.015, 0.03); cap.add(brim);
  const btn = new THREE.Mesh(new THREE.SphereGeometry(0.032, 20, 12), clay('#ffffff')); btn.position.y = 0.2; cap.add(btn);
  dome.name = 'cap'; brim.name = 'brim'; btn.name = 'btn';
  [dome, brim, btn].forEach(m => { m.castShadow = true; parts.push(m); });
  // 상자(오른손)
  const box = new THREE.Group(); armR.hand.add(box);
  const bm = new THREE.Mesh(new RoundedBoxGeometry(0.27, 0.215, 0.2, 4, 0.03), clay('#E8B56B', { roughness: 0.7, clearcoat: 0.05 })); bm.position.set(0.062 + 0.135 - 0.012, -0.03, 0.0); bm.name = 'box';
  const tape = new THREE.Mesh(new THREE.BoxGeometry(0.03, 0.218, 0.203), clay('#C48A3C', { roughness: 0.6 })); tape.position.copy(bm.position);
  box.add(bm, tape); bm.castShadow = true; parts.push(bm);
  const boxGroup = new THREE.Group(); box.add(boxGroup); boxGroup.add(bm, tape);
  // 휴가권(오른손, 처음엔 숨김): 해변 그림 카드
  const tcv = document.createElement('canvas'); tcv.width = 400; tcv.height = 260; { const c = tcv.getContext('2d');
    c.fillStyle = '#FFF8EC'; c.fillRect(0, 0, 400, 260); const g = c.createLinearGradient(0, 20, 0, 150); g.addColorStop(0, '#7fd0ee'); g.addColorStop(1, '#c9eef6');
    c.fillStyle = g; c.fillRect(18, 18, 364, 140); c.fillStyle = '#ffcf5a'; c.beginPath(); c.arc(300, 60, 30, 0, Math.PI * 2); c.fill();
    c.fillStyle = '#39a9c9'; c.fillRect(18, 120, 364, 38); c.fillStyle = '#f5dca8'; c.fillRect(18, 158, 364, 30);
    c.fillStyle = '#F2C14E'; for (let i = 0; i < 9; i++) { c.beginPath(); c.arc(40 + i * 40, 222, 9, 0, Math.PI * 2); c.fill(); } }
  const ttex = new THREE.CanvasTexture(tcv); ttex.colorSpace = THREE.SRGBColorSpace;
  const ticket = new THREE.Mesh(new RoundedBoxGeometry(0.24, 0.156, 0.012, 2, 0.005), [clay('#FFF8EC'), clay('#FFF8EC'), clay('#FFF8EC'), clay('#FFF8EC'), clay('#ffffff', { map: ttex }), clay('#FFF8EC')]);
  ticket.name = 'ticket'; ticket.position.set(0.07, 0.0, 0.13); ticket.rotation.y = -Math.PI / 2; ticket.castShadow = true; box.add(ticket); parts.push(ticket); ticket.visible = false;

  if (outline) parts.forEach(m => outlineOf(m, m === bodyMesh ? OUT : OUT * 0.8));

  const footTicket = new THREE.Mesh(new RoundedBoxGeometry(0.2, 0.012, 0.13, 2, 0.004), [clay('#FFF8EC'), clay('#FFF8EC'), clay('#ffffff', { map: ttex }), clay('#FFF8EC'), clay('#FFF8EC'), clay('#FFF8EC')]);
  footTicket.name = 'footTicket'; footTicket.position.set(0.02, 0.122, 0.03); footTicket.rotation.y = 0.4; footTicket.visible = false; feet[1].add(footTicket); parts.push(footTicket);
  const st = { mood: 'happy', look: [0, 0], blink: 0 };
  const meshes = {}; parts.forEach(m => { if (m.name) meshes[m.name] = m; });
  const rig = {
    root, squash, body, armL, armR, feet, cap, box, st, meshes, boxGroup, ticket, boxMesh: bm,
    hold(what) { boxGroup.visible = what === 'box'; ticket.visible = what === 'ticket'; footTicket.visible = what === 'foot'; },
    setFace(mood, look = [0, 0], blink = 0) {
      if (st.mood === mood && st.look[0] === look[0] && st.look[1] === look[1] && st.blink === blink && rig._painted) return;
      Object.assign(st, { mood, look, blink }); paintBody(cv, st); tex.needsUpdate = true; rig._painted = true;
    },
    // 기본 자세 값(디자인 그대로): 왼팔 흔들기, 오른팔 상자
    pose({ armL: aL = 2.35, armR: aR = 0.75, elbowL = 0, elbowR = 0, fwdL = 0, fwdR = 0, lean = 0, turn = 0, sq = 1, hop = 0, tiltZ = 0, footL = 0, footR = 0, footLz = 0, footRz = 0, x = 0, z = 0, jump = 0 } = {}) {
      root.position.set(x, jump, z);
      armL.piv.rotation.set(fwdL, 0, -aL); armR.piv.rotation.set(fwdR, 0, aR);
      armL.elbow.rotation.x = elbowL; armR.elbow.rotation.x = elbowR;
      hip.rotation.set(lean, 0, tiltZ); root.rotation.y = turn;
      squash.scale.set(1 / Math.sqrt(sq), sq, 1 / Math.sqrt(sq)); squash.position.y = hop;
      feet[0].position.y = footL; feet[1].position.y = footR; feet[0].position.z = 0.04 + footLz; feet[1].position.z = 0.04 + footRz;
      // 상자는 몸통 방향 그대로(손 회전을 정확히 상쇄)
      root.updateMatrixWorld(true); box.quaternion.identity(); box.updateMatrixWorld(true);
      const qh = new THREE.Quaternion(), qb = new THREE.Quaternion(); armR.hand.getWorldQuaternion(qh); hip.getWorldQuaternion(qb);
      box.quaternion.copy(qh.invert().multiply(qb));
    },
  };
  rig.setFace('happy'); rig.pose();
  return rig;
}
