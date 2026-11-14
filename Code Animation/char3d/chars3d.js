// 쏙쏙 직원 3D 공통 빌더(간·장·뇌…) — heart.js와 같은 리그 API: setFace / pose / meshes / allow
import * as THREE from 'three';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { RoundedBoxGeometry } from 'three/addons/geometries/RoundedBoxGeometry.js';
import { drawFace } from './face.js';

const PX = 1 / 300, TEX = 2048, SPAN = 1.6;          // 텍스처: 2D 원점 기준 ±240px
const hex = n => '#' + n.toString(16).padStart(6, '0');
export function clay(color, o = {}) { return new THREE.MeshPhysicalMaterial({ color, roughness: 0.42, clearcoat: 0.3, clearcoatRoughness: 0.35, ...o }); }
const loader = new GLTFLoader();
async function loadGeo(url) {
  const g = await loader.loadAsync(url); let geo; g.scene.traverse(o => { if (o.isMesh) geo = o.geometry; });
  geo.computeVertexNormals();
  const pos = geo.attributes.position, uv = new Float32Array(pos.count * 2);
  for (let i = 0; i < pos.count; i++) { const f = pos.getZ(i) > 0.0; uv[i * 2] = f ? pos.getX(i) / SPAN + 0.5 : 0.01; uv[i * 2 + 1] = f ? pos.getY(i) / SPAN + 0.5 : 0.99; }
  geo.setAttribute('uv', new THREE.BufferAttribute(uv, 2)); return geo;
}
// 2D px 좌표로 그리는 캔버스 텍스처(앞면 평면 투영)
function paintTex(paint) {
  const cv = document.createElement('canvas'); cv.width = cv.height = TEX; const c = cv.getContext('2d');
  const tex = new THREE.CanvasTexture(cv); tex.colorSpace = THREE.SRGBColorSpace; tex.anisotropy = 8;
  const redraw = st => { const k = TEX / SPAN; c.setTransform(k * PX, 0, 0, k * PX, TEX / 2, TEX / 2); paint(c, st); tex.needsUpdate = true; };
  return { tex, redraw };
}
function bodyFill(C0, L0, box) {
  return c => {
    c.fillStyle = hex(C0); c.fillRect(-240, -240, 480, 480);
    const [x, y, w, h] = box, gx = x + w * 0.3, gy = y + h * 0.2, r = Math.max(w, h) * 0.85;
    const g = c.createRadialGradient(gx, gy, 0, gx, gy, r); g.addColorStop(0, hex(L0)); g.addColorStop(1, hex(C0) + '00');
    c.fillStyle = g; c.fillRect(-240, -240, 480, 480);
  };
}

// 캐릭터 정의(chars.py 값 그대로 옮김)
export const DEFS = {
  brain: { C0: 0xFFE0CC, L0: 0xFFF3EA, box: [-145, -115, 290, 260], footY: 136, footC: 0xF6C9AE, gap: 56, face: [0, 0], blush: 0xFFAFA0,
    arms: [[-142, 30, 0.69], [142, 30, 0.69]],
    extra(c) { // 동그란 안경(얼굴 위에 그림)
      c.lineWidth = 5; c.strokeStyle = '#2B2D5B'; for (const sx of [-1, 1]) { c.beginPath(); c.arc(sx * 46, 0, 32, 0, Math.PI * 2); c.stroke(); }
      c.beginPath(); c.moveTo(-14, -2); c.lineTo(14, -2); c.stroke(); },
    parts: { hair: { url: 'hair', z: -0.04, paint(c) {
      c.fillStyle = '#E9C9A6'; c.fillRect(-240, -240, 480, 480);
      const g = c.createRadialGradient(-40, -170, 0, -40, -170, 160); g.addColorStop(0, '#F7E4CF'); g.addColorStop(1, '#E9C9A600'); c.fillStyle = g; c.fillRect(-240, -240, 480, 480);
      c.strokeStyle = '#C49A70'; c.lineWidth = 6; c.lineCap = 'round';
      for (const [sx, sy] of [[-40, -128], [34, -126]]) { c.beginPath(); c.moveTo(sx - 16, sy + 6); c.quadraticCurveTo(sx - 14, sy - 14, sx + 4, sy - 12); c.quadraticCurveTo(sx + 18, sy - 6, sx + 8, sy + 6); c.stroke(); } } } } },
  gut: { C0: 0x8EE0C0, L0: 0xD2F7E8, box: [-145, -130, 290, 270], footY: 138, footC: 0x7CD3B2, gap: 56, face: [0, 10], blush: 0xFF7FA8,
    arms: [[-157, 40, 0.76], [157, 30, 2.1]],
    parts: { shell_band: { url: 'shell_band', color: 0x3A3F6B, rough: 0.6 } } },
  liver: { C0: 0xF4BE63, L0: 0xFFE3A8, box: [-165, -130, 335, 265], footY: 138, footC: 0xE8AE55, gap: 56, face: [0, 10], blush: 0xFF9F7F, mood: 'happy_closed',
    arms: [[-170, 30, 0.73], [162, 10, 2.03]],
    parts: { shell_bandana: { url: 'shell_bandana', z: 0, paint(c) {
      c.fillStyle = '#3CC7B4'; c.fillRect(-240, -240, 480, 480);
      c.fillStyle = '#ffffff'; for (const [dx, dy] of [[-60, -100], [-10, -116], [44, -108]]) { c.beginPath(); c.arc(dx, dy, 6, 0, Math.PI * 2); c.fill(); } } } } },
};

export async function buildChar(id, base = 'cache/chars/') {
  const D = DEFS[id], parts = [], meshes = {};
  const root = new THREE.Group(); root.name = id;
  const squash = new THREE.Group(); root.add(squash);
  const hip = new THREE.Group(); hip.position.y = 0.06; squash.add(hip);
  const body = new THREE.Group(); body.position.y = 0.058 + D.footY * PX - 0.06; hip.add(body);
  const add = (m, name, parent) => { m.name = name; m.castShadow = m.receiveShadow = true; parent.add(m); parts.push(m); meshes[name] = m; return m; };

  // 몸 + 얼굴 텍스처
  const fill = bodyFill(D.C0, D.L0, D.box);
  const T = paintTex((c, st) => { fill(c); c.save(); c.translate(D.face[0], D.face[1]); drawFace(c, st.mood, { blush: hex(D.blush), look: st.look, blink: st.blink }); if (D.extra) D.extra(c); c.restore(); });
  add(new THREE.Mesh(await loadGeo(`${base}${id}_body.glb`), clay('#ffffff', { map: T.tex })), 'body', body);
  for (const [name, p] of Object.entries(D.parts || {})) {
    let mat;
    if (p.paint) { const t = paintTex(c => p.paint(c)); t.redraw({}); mat = clay('#ffffff', { map: t.tex, side: THREE.DoubleSide }); }
    else mat = clay(hex(p.color), { roughness: p.rough ?? 0.42, side: THREE.DoubleSide });
    const m = add(new THREE.Mesh(await loadGeo(`${base}${id}_${p.url}.glb`), mat), name, body); m.position.z = p.z || 0;
  }
  // 몸 표면 위 점 찾기(앞에서 쏜 광선): 2D px → 3D
  const ray = new THREE.Raycaster(); body.updateMatrixWorld(true);
  const surf = (px, py, dir = [0, 0, -1]) => { const o = meshes.body.localToWorld(new THREE.Vector3(px * PX, -py * PX, 0).addScaledVector(new THREE.Vector3(...dir), -2));
    ray.set(o, new THREE.Vector3(...dir)); const h = ray.intersectObject(meshes.body, false)[0]; return h ? meshes.body.worldToLocal(h.point.clone()) : null; };
  if (id === 'gut') {   // 고글 렌즈 2개(끈 위) + 꼬불 더듬이
    const lensMat = new THREE.MeshPhysicalMaterial({ color: '#BDE8FF', roughness: 0.05, clearcoat: 1, metalness: 0 });
    const rimMat = clay('#3A3F6B', { roughness: 0.5 });
    for (const sx of [-1, 1]) {
      const p = surf(sx * 48, -86); const g = new THREE.Group(); g.position.copy(p); body.add(g);
      const n = new THREE.Vector3(sx * 0.35, 0.25, 1).normalize(); g.quaternion.setFromUnitVectors(new THREE.Vector3(0, 0, 1), n);
      const rim = add(new THREE.Mesh(new THREE.TorusGeometry(0.1, 0.022, 14, 40), rimMat), 'goggle' + (sx < 0 ? 'L' : 'R'), g); rim.position.z = 0.045;
      const lens = new THREE.Mesh(new THREE.SphereGeometry(0.1, 32, 12, 0, Math.PI * 2, 0, 0.6), lensMat); lens.rotation.x = Math.PI / 2; lens.scale.set(1, 0.5, 1); lens.position.z = -0.03; rim.add(lens);
      lens.castShadow = true;
    }
    const top = surf(0, -150, [0, -1, 0]) || new THREE.Vector3(0, 0.44, 0);   // 머리 꼭대기
    const P2 = (x, y) => new THREE.Vector3(x * PX, top.y + (-120 - y) * PX - 0.01, 0);
    const curve = new THREE.CubicBezierCurve3(P2(0, -120), P2(-30, -170), P2(40, -190), P2(20, -150));
    const curve2 = new THREE.CubicBezierCurve3(P2(20, -150), P2(5, -125), P2(50, -130), P2(40, -170));
    const cp = new THREE.CurvePath(); cp.add(curve); cp.add(curve2);
    add(new THREE.Mesh(new THREE.TubeGeometry(cp, 60, 0.016, 10, false), clay('#5CC79E')), 'antenna', body);
    const ball = add(new THREE.Mesh(new THREE.SphereGeometry(0.047, 24, 16), clay('#FFD166')), 'antennaBall', body); ball.position.copy(P2(40, -170));
  }
  // 팔(어깨 → 위팔 → 팔꿈치 → 아래팔 → 손)
  const armMat = clay(hex(D.C0)), arms = [];
  D.arms.forEach(([sx, sy, rest], i) => {
    const tag = i ? 'R' : 'L', piv = new THREE.Group(); piv.position.set(sx * PX, -sy * PX, 0); body.add(piv);
    const L1 = 0.1, L2 = 0.1, r = 0.05;
    const up = add(new THREE.Mesh(new THREE.CapsuleGeometry(r, L1, 8, 20), armMat), 'up' + tag, piv); up.position.y = -L1 / 2;
    const elbow = new THREE.Group(); elbow.position.y = -L1; piv.add(elbow);
    const lo = add(new THREE.Mesh(new THREE.CapsuleGeometry(r * 0.98, L2, 8, 20), armMat), 'lo' + tag, elbow); lo.position.y = -L2 / 2;
    const hand = add(new THREE.Mesh(new THREE.SphereGeometry(0.062, 32, 20), armMat), 'hand' + tag, elbow); hand.position.y = -L2 - 0.01;
    arms.push({ piv, elbow, hand, rest });
  });
  // 발
  const footMat = clay(hex(D.footC));
  const feet = [-1, 1].map((s, i) => {
    const g = new THREE.Group(); g.position.set(s * D.gap * PX, 0, 0.04); root.add(g);
    const m = add(new THREE.Mesh(new THREE.SphereGeometry(1, 32, 20), footMat), i ? 'footR' : 'footL', g); m.scale.set(0.105, 0.058, 0.115); m.position.y = 0.058; return g;
  });
  // 손에 드는 소품: hold(그룹, 몸통 방향 유지)
  const hold = new THREE.Group(); arms[1].hand.add(hold);
  const rigExtra = {};
  if (id === 'gut') {   // 플라스크(오른손)
    const glass = new THREE.MeshPhysicalMaterial({ color: '#FFF3A3', roughness: 0.15, transmission: 0.0, transparent: true, opacity: 0.85, clearcoat: 1 });
    const pts = [[0, 0], [0.075, 0], [0.085, 0.012], [0.03, 0.12], [0.026, 0.19], [0.03, 0.2]].map(p => new THREE.Vector2(p[0], p[1]));
    const fl = add(new THREE.Mesh(new THREE.LatheGeometry(pts, 40), glass), 'flask', hold); fl.position.set(0.062 + 0.086 - 0.012, -0.09, 0);
  }
  if (id === 'liver') { // 대걸레(오른손): 자루 + 걸레 뭉치. 자루 아래끝 = 손에서 0.5 아래
    const stick = add(new THREE.Mesh(new THREE.CylinderGeometry(0.016, 0.016, 0.52, 16), clay('#C98F5B', { roughness: 0.6 })), 'mop', hold);
    stick.position.set(0.0, -0.03, 0.09);
    const head = add(new THREE.Mesh(new THREE.SphereGeometry(1, 24, 12, 0, Math.PI * 2, 0, Math.PI / 2), clay('#F5F0E6', { roughness: 0.9 })), 'mophead', hold);
    head.scale.set(0.1, 0.07, 0.07); head.rotation.x = Math.PI; head.position.set(0.0, -0.27, 0.09);
    // 끈적한 갈색 병(C6: 깔때기에 부음) — 기울이기 그룹 bottleG(rotation.z<0 이면 병 입구가 바깥쪽으로 숙여짐)
    const bottleG = new THREE.Group(); bottleG.position.set(0.05, -0.01, 0.08); bottleG.visible = false; hold.add(bottleG);
    const bpts = [[0, 0], [0.055, 0], [0.06, 0.01], [0.06, 0.15], [0.028, 0.2], [0.022, 0.25], [0.027, 0.26], [0, 0.26]].map(p => new THREE.Vector2(...p));
    const bot = add(new THREE.Mesh(new THREE.LatheGeometry(bpts, 24), new THREE.MeshPhysicalMaterial({ color: '#6a3212', roughness: 0.22, clearcoat: 0.9, transparent: true, opacity: 0.93 })), 'bottle', bottleG); bot.position.y = -0.11;
    rigExtra.bottleG = bottleG; rigExtra.mopParts = [stick, head];
  }
  // 브레인 안경·간 두건 등은 위 parts/texture. 서로 붙어 있어 겹쳐도 되는 쌍
  const allow = new Set(['body|upL', 'body|upR', 'upL|loL', 'upR|loR', 'loL|handL', 'loR|handR', 'upL|handL', 'upR|handR', 'body|footL', 'body|footR',
    'body|hair', 'body|shell_band', 'body|goggleL', 'body|goggleR', 'shell_band|goggleL', 'shell_band|goggleR', 'body|antenna', 'antenna|antennaBall', 'body|shell_bandana', 'handR|flask', 'handR|mop', 'mop|mophead', 'handR|mophead', 'handR|bottle', 'loR|bottle'].map(k => k.split('|').sort().join('|')));

  const st = { mood: D.mood || 'happy', look: [0, 0], blink: 0 }; let painted = false;
  const rig = {
    id, root, hip, body, arms, feet, hold, meshes, allow, st,
    ...rigExtra,
    prop(which) { if (rigExtra.bottleG) { rigExtra.bottleG.visible = which === 'bottle'; rigExtra.mopParts.forEach(m => { m.visible = which === 'mop'; }); } },
    setFace(mood, look = [0, 0], blink = 0) {
      if (painted && st.mood === mood && st.look[0] === look[0] && st.look[1] === look[1] && st.blink === blink) return;
      Object.assign(st, { mood, look, blink }); T.redraw(st); painted = true;
    },
    // armL/armR: 아래로부터 벌린 각(라디안). 생략하면 디자인 기본 자세
    pose({ armL = arms[0].rest, armR = arms[1].rest, elbowL = 0, elbowR = 0, fwdL = 0, fwdR = 0, lean = 0, turn = 0, sq = 1, hop = 0, tiltZ = 0, footL = 0, footR = 0, footLz = 0, footRz = 0, x = 0, z = 0, jump = 0 } = {}) {
      root.position.set(x, jump, z); root.rotation.y = turn;
      arms[0].piv.rotation.set(fwdL, 0, -armL); arms[1].piv.rotation.set(fwdR, 0, armR);
      arms[0].elbow.rotation.x = elbowL; arms[1].elbow.rotation.x = elbowR;
      hip.rotation.set(lean, 0, tiltZ);
      squash.scale.set(1 / Math.sqrt(sq), sq, 1 / Math.sqrt(sq)); squash.position.y = hop;
      feet[0].position.y = footL; feet[1].position.y = footR; feet[0].position.z = 0.04 + footLz; feet[1].position.z = 0.04 + footRz;
      root.updateMatrixWorld(true); hold.quaternion.identity(); hold.updateMatrixWorld(true);
      const qh = new THREE.Quaternion(), qb = new THREE.Quaternion(); arms[1].hand.getWorldQuaternion(qh); hip.getWorldQuaternion(qb);
      hold.quaternion.copy(qh.invert().multiply(qb));
    },
  };
  rig.setFace(st.mood); rig.pose();
  return rig;
}
