// 심장의 펌프 공장 — 둥근 붉은 벽돌 공장, 가운데 아코디언 풀무 펌프(심장이 위 발판을 뛰어 밟음),
// 붉은 관(내보냄)·푸른 관(들어옴), 밸브 바퀴, 박동에 튀는 압력계, 심전도 모니터, 돔 천장의 박동 전구 고리
import * as THREE from 'three';
import { RoundedBoxGeometry } from 'three/addons/geometries/RoundedBoxGeometry.js';
import { clay } from '../chars3d.js';

function canvasTex(w, h, draw) {
  const cv = document.createElement('canvas'); cv.width = w; cv.height = h; draw(cv.getContext('2d'), w, h);
  const t = new THREE.CanvasTexture(cv); t.colorSpace = THREE.SRGBColorSpace; t.anisotropy = 8; t._cv = cv; return t;
}
const mat = (c, o = {}) => new THREE.MeshPhysicalMaterial({ color: c, roughness: 0.7, ...o });
const brass = (o = {}) => clay('#D9A441', { metalness: 0.65, roughness: 0.32, clearcoat: 0.4, ...o });

export const BUTTON = { x: 0, z: 0, r: 0.5, top: 0.62, press: 0.1 };   // 풀무 위 발판 윗면 높이(누르면 top - press)
const ROOM_R = 3.8, RH = 3.2;

export function buildPumpRoom({ wall: WALL = 'C' } = {}) {
  const g = new THREE.Group(), SOLID = [];
  const add = (m, name, parent = g) => { m.castShadow = m.receiveShadow = true; parent.add(m); if (name) { m.name = name; SOLID.push(m); } return m; };
  const onWall = (obj, ang, y, inset = 0) => { const r = ROOM_R - inset; obj.position.set(r * Math.sin(ang), y, -r * Math.cos(ang)); obj.rotation.y = -ang; g.add(obj); return obj; };

  // 바닥: 짙은 자두빛 타일 + 펌프를 두른 황동 원 상감
  const floorTex = canvasTex(2048, 2048, (c, w, h) => {
    c.fillStyle = '#6E3A4E'; c.fillRect(0, 0, w, h);
    const cx = w / 2, cy = h / 2, s = w / (ROOM_R * 2.4);
    for (let r = 1; r < 12; r++) { c.strokeStyle = r % 3 ? 'rgba(40,15,25,0.55)' : 'rgba(217,164,65,0.9)'; c.lineWidth = r % 3 ? 5 : 12; c.beginPath(); c.arc(cx, cy, r * 0.42 * s, 0, Math.PI * 2); c.stroke(); }
    for (let a = 0; a < 32; a++) { c.strokeStyle = 'rgba(40,15,25,0.45)'; c.lineWidth = 4; c.beginPath(); c.moveTo(cx + Math.cos(a / 32 * 6.283) * 0.42 * s, cy + Math.sin(a / 32 * 6.283) * 0.42 * s); c.lineTo(cx + Math.cos(a / 32 * 6.283) * w, cy + Math.sin(a / 32 * 6.283) * w); c.stroke(); }
    const rg = c.createRadialGradient(cx, cy, 0, cx, cy, w * 0.6); rg.addColorStop(0, 'rgba(255,200,170,0.18)'); rg.addColorStop(1, 'rgba(0,0,0,0.25)'); c.fillStyle = rg; c.fillRect(0, 0, w, h);
  });
  const floor = add(new THREE.Mesh(new THREE.CircleGeometry(ROOM_R + 0.05, 96), mat('#ffffff', { map: floorTex, roughness: 0.55, clearcoat: 0.25 }))); floor.rotation.x = -Math.PI / 2;

  // 둥근 벽: 붉은 벽돌 + 황동 띠. +x 쪽에 문
  const brick = canvasTex(2048, 512, (c, w, h) => {
    c.fillStyle = '#2e1620'; c.fillRect(0, 0, w, h);
    const bh = 34, bw = 92;
    for (let r = 0; r * bh < h; r++) for (let k = -1; k * bw < w; k++) {
      const x = k * bw + (r % 2 ? bw / 2 : 0), y = r * bh, v = ((r * 31 + k * 17) % 7) / 7;
      c.fillStyle = `rgb(${92 + v * 22},${44 + v * 12},${58 + v * 12})`; c.fillRect(x + 3, y + 3, bw - 6, bh - 6);
    }
  }); brick.wrapS = brick.wrapT = THREE.RepeatWrapping; brick.repeat.set(5, 1.6);
  // onWall 각 a의 점 = (r·sin a, -r·cos a). three 원기둥 각 θ의 점 = (r·sin θ, r·cos θ) → θ = π - a
  const DOOR_ANG = 1.45, DOOR_W = 0.3;
  const W_A0 = -1.35, W_A1 = 0.85;                       // 남길 벽 각 범위(onWall 각)
  const TH0 = Math.PI - W_A1, TH = W_A1 - W_A0;
  const wallSeam = [];                                   // 박동에 빛나는 재질들(A·C)
  if (WALL === 'brick') {
    const wallMat = mat('#ffffff', { map: brick, roughness: 0.85, side: THREE.DoubleSide });
    add(new THREE.Mesh(new THREE.CylinderGeometry(ROOM_R, ROOM_R, RH, 96, 1, true, TH0, TH), wallMat), 'wall').position.y = RH / 2;
  } else if (WALL === 'A') {   // 근육 쿠션 벽: 누빈 산호색 판 + 빛나는 이음새
    const cells = (c, w, h, glow) => { const nx = 22, ny = 6, cw = w / nx, ch = h / ny;
      c.fillStyle = glow ? '#000' : '#7a2a3c'; c.fillRect(0, 0, w, h);
      for (let j = 0; j < ny; j++) for (let i = 0; i < nx; i++) { const x = i * cw + (j % 2 ? cw / 2 : 0), y = j * ch;
        if (glow) continue;
        const gr = c.createRadialGradient(x + cw * 0.42, y + ch * 0.38, 2, x + cw / 2, y + ch / 2, cw * 0.62); gr.addColorStop(0, '#ffb1a6'); gr.addColorStop(0.6, '#e2697a'); gr.addColorStop(1, '#a8394f');
        c.fillStyle = gr; c.beginPath(); c.roundRect(x + 5, y + 5, cw - 10, ch - 10, 26); c.fill(); c.fillStyle = '#7a2a3c'; c.beginPath(); c.arc(x, y, 6, 0, 7); c.fill(); }
      if (glow) { c.strokeStyle = '#ffd0a0'; c.lineWidth = 7; for (let j = 0; j <= ny; j++) { c.beginPath(); c.moveTo(0, j * ch); c.lineTo(w, j * ch); c.stroke(); }
        for (let j = 0; j < ny; j++) for (let i = 0; i <= nx; i++) { const x = i * cw + (j % 2 ? cw / 2 : 0); c.beginPath(); c.moveTo(x, j * ch); c.lineTo(x, (j + 1) * ch); c.stroke(); } } };
    const map = canvasTex(2048, 640, (c, w, h) => cells(c, w, h, false)), em = canvasTex(2048, 640, (c, w, h) => cells(c, w, h, true));
    const wm = mat('#ffffff', { map, emissiveMap: em, emissive: '#ff8a6a', emissiveIntensity: 0.4, roughness: 0.55, sheen: 0, clearcoat: 0.25, side: THREE.DoubleSide });
    // 쿠션 볼록함: 반지름을 칸마다 살짝 부풀린 원통
    const geo = new THREE.CylinderGeometry(ROOM_R, ROOM_R, RH, 352, 48, true, TH0, TH), pa = geo.attributes.position, uv = geo.attributes.uv;
    for (let i = 0; i < pa.count; i++) { const u = uv.getX(i) * 22, v = uv.getY(i) * 6, jj = Math.floor(v), uu = u - (jj % 2 ? 0.5 : 0);
      const bump = Math.pow(Math.max(0, Math.sin((uu % 1 + 1) % 1 * Math.PI) * Math.sin((v % 1) * Math.PI)), 0.6) * 0.07;
      const x = pa.getX(i), z = pa.getZ(i), r = Math.hypot(x, z), k = (r - bump) / r; pa.setX(i, x * k); pa.setZ(i, z * k); }
    geo.computeVertexNormals();
    add(new THREE.Mesh(geo, wm), 'wall').position.y = RH / 2; wallSeam.push(wm);
  } else if (WALL === 'B') {   // 황동 유리 온실 벽: 아치 창틀 + 유리, 바깥 세계가 비침
    const glass = new THREE.MeshPhysicalMaterial({ color: '#ffd8e4', roughness: 0.05, transparent: true, opacity: 0.18, side: THREE.DoubleSide, depthWrite: false });
    add(new THREE.Mesh(new THREE.CylinderGeometry(ROOM_R, ROOM_R, RH, 96, 1, true, TH0, TH), glass)).position.y = RH / 2;
    SOLID.push(Object.assign(new THREE.Mesh(new THREE.CylinderGeometry(ROOM_R, ROOM_R, RH, 48, 1, true, TH0, TH)), { name: 'wall', visible: false }));
    const nV = 11;
    for (let k = 0; k <= nV; k++) { const a = W_A0 + (W_A1 - W_A0) * k / nV; const m = add(new THREE.Mesh(new THREE.BoxGeometry(0.07, RH, 0.07), brass()), 'wall'); m.position.set(ROOM_R * Math.sin(a), RH / 2, -ROOM_R * Math.cos(a)); m.rotation.y = -a; }
    for (const y of [0.5, 1.6]) { const t = add(new THREE.Mesh(new THREE.TorusGeometry(ROOM_R, 0.03, 6, 96, TH), brass()), 'wall'); t.rotation.x = -Math.PI / 2; t.rotation.z = W_A0 - Math.PI / 2; t.position.y = y; }
    for (let k = 0; k < nV; k++) { const a = W_A0 + (W_A1 - W_A0) * (k + 0.5) / nV, half = (W_A1 - W_A0) / nV / 2 * ROOM_R;   // 창마다 위쪽 반원 아치
      const arc = add(new THREE.Mesh(new THREE.TorusGeometry(half, 0.025, 6, 24, Math.PI), brass()), null); arc.position.set(ROOM_R * Math.sin(a), 2.6, -ROOM_R * Math.cos(a)); arc.rotation.y = -a; }
    // 아래쪽 벽 밑동(판넬)
    add(new THREE.Mesh(new THREE.CylinderGeometry(ROOM_R, ROOM_R, 0.5, 96, 1, true, TH0, TH), mat('#4a2232', { roughness: 0.6, side: THREE.DoubleSide })), 'wall').position.y = 0.25;
  } else if (WALL === 'C') {   // 리듬 파이프 오르간 벽: 매끈한 자두빛 벽 + 높낮이 다른 황동 파이프, 끝이 박동에 빛남
    const glassC = new THREE.MeshPhysicalMaterial({ color: '#ffe0ea', roughness: 0.05, transparent: true, opacity: 0.1, side: THREE.DoubleSide, depthWrite: false });
    add(new THREE.Mesh(new THREE.CylinderGeometry(ROOM_R, ROOM_R, RH, 96, 1, true, TH0, TH), glassC)).position.y = RH / 2;
    const inv = new THREE.Mesh(new THREE.CylinderGeometry(ROOM_R, ROOM_R, RH, 48, 1, true, TH0, TH)); inv.visible = false; inv.position.y = RH / 2; inv.name = 'wall'; g.add(inv); SOLID.push(inv);
    for (let k = 0; k <= 6; k++) { const a = W_A0 + (W_A1 - W_A0) * k / 6; const m = add(new THREE.Mesh(new THREE.BoxGeometry(0.05, RH, 0.05), brass()), 'wall'); m.position.set(ROOM_R * Math.sin(a), RH / 2, -ROOM_R * Math.cos(a)); m.rotation.y = -a; }
    const tipMat = new THREE.MeshStandardMaterial({ color: '#ffe2b0', emissive: '#ffae5a', emissiveIntensity: 0.4 }); wallSeam.push(tipMat);
    const n = 46;
    for (let k = 0; k < n; k++) { const a = W_A0 + 0.04 + (W_A1 - W_A0 - 0.08) * k / (n - 1); const h = 1.2 + 1.5 * (0.5 + 0.5 * Math.sin(k * 0.55)) * (0.6 + 0.4 * Math.cos(k * 0.17)); const r = 0.075 + 0.03 * Math.sin(k * 1.3) ** 2;
      const rr = ROOM_R - 0.17; const pp = add(new THREE.Mesh(new THREE.CylinderGeometry(r, r, h, 20), brass()), 'wall'); pp.position.set(rr * Math.sin(a), 0.3 + h / 2, -rr * Math.cos(a));
      const mouth = add(new THREE.Mesh(new THREE.BoxGeometry(r * 1.2, 0.07, 0.02), new THREE.MeshStandardMaterial({ color: '#2a0f18' })), null); mouth.position.set((rr - r) * Math.sin(a), 0.55, -(rr - r) * Math.cos(a)); mouth.rotation.y = -a;
      const tip = new THREE.Mesh(new THREE.SphereGeometry(r * 0.9, 16, 10), tipMat); tip.position.set(rr * Math.sin(a), 0.3 + h + r * 0.4, -rr * Math.cos(a)); g.add(tip); }
    const plinth = add(new THREE.Mesh(new THREE.CylinderGeometry(ROOM_R - 0.02, ROOM_R - 0.02, 0.3, 96, 1, true, TH0, TH), mat('#6a2f40', { roughness: 0.6, side: THREE.DoubleSide })), 'wall'); plinth.position.y = 0.15;
  }
  const capR = add(new THREE.Mesh(new THREE.CylinderGeometry(ROOM_R + 0.06, ROOM_R + 0.06, 0.12, 96, 1, true, TH0, TH), brass({ side: THREE.DoubleSide }))); capR.position.y = RH;
  for (const a of [W_A0, W_A1]) { const col = add(new THREE.Mesh(new THREE.CylinderGeometry(0.16, 0.2, RH + 0.3, 24), brass()), 'wall'); col.position.set(ROOM_R * Math.sin(a), (RH + 0.3) / 2, -ROOM_R * Math.cos(a)); }
  // 낮은 난간(나머지 둘레, 문 자리만 비움)
  const railMat = brass(), parMat = mat('#4a2232', { roughness: 0.6 });
  const segs = [[W_A1, DOOR_ANG - DOOR_W / 2], [DOOR_ANG + DOOR_W / 2, Math.PI * 2 + W_A0]];
  for (const [a0, a1] of segs) {
    const par = add(new THREE.Mesh(new THREE.CylinderGeometry(ROOM_R, ROOM_R, 0.45, 64, 1, true, Math.PI - a1, a1 - a0), parMat), 'wall'); par.position.y = 0.225; par.material.side = THREE.DoubleSide;
    const rail = add(new THREE.Mesh(new THREE.TorusGeometry(ROOM_R, 0.035, 8, 64, a1 - a0), railMat), 'wall'); rail.rotation.x = Math.PI / 2; rail.rotation.z = a0 - Math.PI / 2; rail.position.y = 0.95;   // (+π/2: 문 자리를 비우도록 각도 맞춤)
    for (let a = a0; a <= a1 + 1e-6; a += (a1 - a0) / Math.max(2, Math.round((a1 - a0) / 0.22))) { const post = add(new THREE.Mesh(new THREE.CylinderGeometry(0.025, 0.025, 0.5, 8), railMat), 'wall'); post.position.set(ROOM_R * Math.sin(a), 0.7, -ROOM_R * Math.cos(a)); }
  }
  // 발판 밑동(공중에 뜬 원형 무대) + 테두리 빛 띠
  const under = add(new THREE.Mesh(new THREE.CylinderGeometry(ROOM_R + 0.05, ROOM_R * 0.55, 2.2, 64), mat('#3a1a28', { roughness: 0.8 }))); under.position.y = -1.12;
  const rimGlow = new THREE.Mesh(new THREE.TorusGeometry(ROOM_R + 0.05, 0.04, 8, 120), new THREE.MeshStandardMaterial({ color: '#ffb38a', emissive: '#ff8a5a', emissiveIntensity: 1.2 })); rimGlow.rotation.x = Math.PI / 2; rimGlow.position.y = -0.02; g.add(rimGlow);
  // 문 밖 다리(빛나는 관 통로로 이어짐)
  { const br = add(new THREE.Mesh(new RoundedBoxGeometry(1.0, 0.1, 4.0, 2, 0.04), mat('#5a2a3a', { roughness: 0.6 })), 'bridge'); const r = ROOM_R + 2.0;
    br.position.set(r * Math.sin(DOOR_ANG), -0.065, -r * Math.cos(DOOR_ANG)); br.rotation.y = -DOOR_ANG;
    const tunnel = new THREE.Mesh(new THREE.CylinderGeometry(0.95, 0.95, 4.0, 32, 1, true), new THREE.MeshPhysicalMaterial({ color: '#ffd6e0', roughness: 0.1, transparent: true, opacity: 0.22, side: THREE.DoubleSide }));
    tunnel.rotation.z = Math.PI / 2; const tg = new THREE.Group(); tg.add(tunnel); tg.position.set(r * Math.sin(DOOR_ANG), 0.85, -r * Math.cos(DOOR_ANG)); tg.rotation.y = -DOOR_ANG + Math.PI / 2; g.add(tg);
    for (let k = 0; k < 6; k++) { const ring = new THREE.Mesh(new THREE.TorusGeometry(0.97, 0.03, 8, 40), new THREE.MeshStandardMaterial({ color: '#ffe0c8', emissive: '#ff9a7a', emissiveIntensity: 0.3 })); ring.rotation.y = Math.PI / 2; ring.position.x = -1.7 + k * 0.68; tg.add(ring); } }
  // 돔 천장 + 박동 전구 고리(철망 씌운 노란 전구)
  const hoop = add(new THREE.Mesh(new THREE.TorusGeometry(2.3, 0.05, 10, 96), brass())); hoop.rotation.x = Math.PI / 2; hoop.position.y = RH - 0.05;
  for (let k = 0; k < 3; k++) { const a = k / 3 * Math.PI * 2 + 0.5; const rod = add(new THREE.Mesh(new THREE.CylinderGeometry(0.025, 0.025, 6, 8), brass())); rod.position.set(2.3 * Math.sin(a), RH + 2.95, -2.3 * Math.cos(a)); }
  const bulbs = [];
  for (let i = 0; i < 12; i++) {
    const a = i / 12 * Math.PI * 2, r = 2.3, x = r * Math.sin(a), z = -r * Math.cos(a);
    const bm = new THREE.MeshStandardMaterial({ color: '#fff0c8', emissive: '#ffcf7a', emissiveIntensity: 0 });
    const b = new THREE.Mesh(new THREE.SphereGeometry(0.1, 20, 14), bm); b.position.set(x, RH - 0.05, z); g.add(b);
    const cage = new THREE.Mesh(new THREE.SphereGeometry(0.13, 10, 6), new THREE.MeshStandardMaterial({ color: '#5a3a2a', wireframe: true })); cage.position.copy(b.position); g.add(cage);
    const L = new THREE.PointLight('#ffc98a', 0, 5, 1.5); L.position.set(x, RH - 0.25, z); g.add(L); bulbs.push({ bm, L, a });
  }

  // 가운데 풀무 펌프: 황동 받침 드럼 → 붉은 주름 4겹 → 황동 발판(가운데 빨간 패드)
  const pump = new THREE.Group(); pump.position.set(BUTTON.x, 0, BUTTON.z); g.add(pump);
  add(new THREE.Mesh(new THREE.CylinderGeometry(0.72, 0.8, 0.2, 64), brass()), 'pump', pump).position.y = 0.1;
  for (let k = 0; k < 18; k++) { const a = k / 18 * Math.PI * 2; add(new THREE.Mesh(new THREE.SphereGeometry(0.025, 10, 8), brass()), null, pump).position.set(0.76 * Math.cos(a), 0.12, 0.76 * Math.sin(a)); }
  const bellows = new THREE.Group(); bellows.position.y = 0.2; pump.add(bellows);
  const foldMat = clay('#C8343F', { roughness: 0.45 }), folds = [];
  for (let k = 0; k < 4; k++) { const f = add(new THREE.Mesh(new THREE.TorusGeometry(0.5, 0.06, 16, 48), foldMat), 'pump', bellows); f.rotation.x = Math.PI / 2; folds.push(f); }
  const core = add(new THREE.Mesh(new THREE.CylinderGeometry(0.48, 0.48, 1, 48), clay('#9E2532', { roughness: 0.5 })), 'pump', bellows);
  const plate = new THREE.Group(); pump.add(plate);
  add(new THREE.Mesh(new THREE.CylinderGeometry(0.6, 0.6, 0.06, 64), brass()), 'pumpPad', plate).position.y = -0.03;
  add(new THREE.Mesh(new THREE.CylinderGeometry(0.42, 0.42, 0.012, 48), clay('#E8505B', { roughness: 0.35 })), 'pumpPad', plate).position.y = -0.004;
  const setPress = v => {
    const top = BUTTON.top - BUTTON.press * v, h = top - 0.06 - 0.2;   // 발판 윗면 = top
    plate.position.y = top - 0.002;
    core.scale.set(1, h, 1); core.position.y = h / 2;
    folds.forEach((f, k) => { f.position.y = 0.06 + (h - 0.12) * k / 3; f.scale.set(1 + 0.04 * v, 1 + 0.04 * v, 1); });
  };
  setPress(0);

  // 관: 붉은 관(펌프 오른쪽 → 위로 → 천장 가로질러), 푸른 관(천장 → 펌프 왼쪽). 박동 때 빛나는 띠
  const glowMat = new THREE.MeshStandardMaterial({ color: '#ffe0b0', emissive: '#ff9a5a', emissiveIntensity: 0.2 });
  const glowMatB = new THREE.MeshStandardMaterial({ color: '#d8ecff', emissive: '#7ab8ff', emissiveIntensity: 0.2 });
  const pipe = (pts, color, r, gm, name) => {
    const curve = new THREE.CatmullRomCurve3(pts.map(p => new THREE.Vector3(...p)), false, 'catmullrom', 0.2);
    add(new THREE.Mesh(new THREE.TubeGeometry(curve, 120, r, 24), clay(color, { roughness: 0.4 })), name);
    for (let k = 1; k < 7; k++) { const u = k / 7, p = curve.getPointAt(u), tn = curve.getTangentAt(u); const b = new THREE.Mesh(new THREE.TorusGeometry(r + 0.012, 0.02, 8, 28), gm); b.position.copy(p); b.quaternion.setFromUnitVectors(new THREE.Vector3(0, 0, 1), tn); g.add(b); }
    return curve;
  };
  pipe([[0.62, 0.32, -0.35], [1.4, 0.4, -1.4], [1.9, 1.6, -2.4], [1.2, RH - 0.35, -2.9], [-1.5, RH + 0.1, -2.9], [-4.5, RH + 0.6, -2.0], [-12, RH + 2.5, -6]], '#D93A44', 0.17, glowMat, 'pipe');
  pipe([[-12, RH + 1.0, 4.0], [-5.0, RH - 0.2, 1.5], [-2.4, RH - 0.4, -1.2], [-1.1, 2.1, -2.3], [-0.45, 0.75, -1.35], [-0.3, 0.32, -0.52]], '#4E7FD6', 0.15, glowMatB, 'pipe');
  // 밸브 바퀴
  for (const [x, y, z, ry] of [[1.66, 1.1, -2.0, 0.6], [-0.66, 1.25, -1.75, -0.2]]) {
    const vw = new THREE.Group(); vw.position.set(x, y, z); vw.rotation.y = ry; g.add(vw);
    add(new THREE.Mesh(new THREE.TorusGeometry(0.2, 0.025, 10, 32), brass()), null, vw).position.z = 0.26;
    for (let k = 0; k < 3; k++) { const sp = add(new THREE.Mesh(new THREE.CylinderGeometry(0.012, 0.012, 0.4, 8), brass()), null, vw); sp.rotation.z = k * Math.PI / 3; sp.position.z = 0.26; }
  }
  // 압력계 3개(벽): 바늘이 박동에 튐
  const needles = [];
  const GR = 0.27;
  { const bar = add(new THREE.Mesh(new THREE.TorusGeometry(ROOM_R - 0.42, 0.025, 8, 48, 0.62), brass())); bar.rotation.x = -Math.PI / 2; bar.rotation.z = -0.31 - Math.PI / 2; bar.position.y = 2.88; }
  [-0.22, 0, 0.22].forEach((ang, i) => {
    const gg = new THREE.Group(); gg.scale.setScalar(GR / 0.17);
    const hang = add(new THREE.Mesh(new THREE.CylinderGeometry(0.01, 0.01, 0.2, 8), brass()), null, gg); hang.position.y = 0.25;
    const face = add(new THREE.Mesh(new THREE.CylinderGeometry(0.17, 0.17, 0.04, 40), mat('#ffffff', { map: canvasTex(256, 256, (c) => {
      c.fillStyle = '#d9cbb0'; c.beginPath(); c.arc(128, 128, 126, 0, 7); c.fill(); c.strokeStyle = '#3a2a2a'; c.lineWidth = 6;
      for (let k = 0; k <= 8; k++) { const a = Math.PI * (0.8 + 1.4 * k / 8); c.beginPath(); c.moveTo(128 + 92 * Math.cos(a), 128 + 92 * Math.sin(a)); c.lineTo(128 + 112 * Math.cos(a), 128 + 112 * Math.sin(a)); c.stroke(); }
      c.strokeStyle = '#E8505B'; c.lineWidth = 14; c.beginPath(); c.arc(128, 128, 104, Math.PI * 1.85, Math.PI * 2.2); c.stroke(); }), roughness: 0.4 })), null, gg);
    face.rotation.x = Math.PI / 2;
    add(new THREE.Mesh(new THREE.TorusGeometry(0.17, 0.025, 10, 40), brass()), null, gg).position.z = 0.02;
    const nd = new THREE.Group(); nd.position.z = 0.03; gg.add(nd);
    const nm = new THREE.Mesh(new THREE.BoxGeometry(0.012, 0.13, 0.008), clay('#2B2D5B')); nm.position.y = 0.055; nd.add(nm);
    onWall(gg, ang, 2.5, 0.42); needles.push(nd);
  });
  // 심전도 모니터: 벽걸이 팔 + 둥근 브라운관 상자, 화면은 매 프레임 그림
  const ecgTex = canvasTex(512, 320, () => {});
  const mon = new THREE.Group();
  add(new THREE.Mesh(new RoundedBoxGeometry(0.95, 0.66, 0.42, 4, 0.08), clay('#E9DCC4', { roughness: 0.5 })), 'monitor', mon);
  const scr = new THREE.Mesh(new THREE.PlaneGeometry(0.76, 0.48), new THREE.MeshBasicMaterial({ map: ecgTex, toneMapped: false })); scr.position.z = 0.212; mon.add(scr);
  add(new THREE.Mesh(new THREE.CylinderGeometry(0.03, 0.03, 0.5, 12), brass()), null, mon).rotation.x = Math.PI / 2;
  mon.children[mon.children.length - 1].position.set(0, 0, -0.42);
  onWall(mon, 0.42, 1.65, 0.68);
  const setECG = (t, lands, flat = 1e9, alarm = false) => {   // lands: 쿵 시각들, flat 이후는 일자
    const c = ecgTex._cv.getContext('2d'), w = 512, h = 320;
    c.fillStyle = alarm ? '#2a0a0e' : '#062418'; c.fillRect(0, 0, w, h);
    c.strokeStyle = 'rgba(80,200,140,0.18)'; c.lineWidth = 1; for (let x = 0; x < w; x += 32) { c.beginPath(); c.moveTo(x, 0); c.lineTo(x, h); c.stroke(); } for (let y = 0; y < h; y += 32) { c.beginPath(); c.moveTo(0, y); c.lineTo(w, y); c.stroke(); }
    const span = 3.0, col = alarm ? '#ff6a6a' : '#6dffb0';
    c.strokeStyle = col; c.lineWidth = 6; c.shadowColor = col; c.shadowBlur = 14; c.beginPath();
    for (let x = 0; x <= w; x += 2) {
      const tt = t - span + span * x / w; let y = 0;
      if (tt < flat) for (const L of lands) { const d = tt - L; if (d > -0.06 && d < 0.14) y += d < 0 ? -0.2 * Math.sin((d + 0.06) / 0.06 * Math.PI) : (d < 0.04 ? Math.sin(d / 0.04 * Math.PI) : -0.25 * Math.sin((d - 0.04) / 0.1 * Math.PI)); }
      const py = h * 0.58 - y * h * 0.38; x ? c.lineTo(x, py) : c.moveTo(x, py);
    }
    c.stroke(); c.shadowBlur = 0;
    c.fillStyle = col; c.globalAlpha = alarm ? (Math.sin(t * 12) > 0 ? 1 : 0.2) : 0.6; c.beginPath(); c.arc(w - 18, 30, 10, 0, 7); c.fill(); c.globalAlpha = 1;
    ecgTex.needsUpdate = true;
  };
  setECG(0, []);

  // 달력(모든 칸에 X) + 색 바랜 해변 포스터 + 못
  const poster = new THREE.Mesh(new THREE.BoxGeometry(1.45, 1.0, 0.02), mat('#ffffff', { map: canvasTex(900, 620, (c, w, h) => {
    const sky = c.createLinearGradient(0, 0, 0, h * 0.55); sky.addColorStop(0, '#9fd3e6'); sky.addColorStop(1, '#d9eef0'); c.fillStyle = sky; c.fillRect(0, 0, w, h);
    c.fillStyle = '#ffd98a'; c.beginPath(); c.arc(w * 0.72, h * 0.25, 70, 0, Math.PI * 2); c.fill();
    c.fillStyle = '#5fb7c9'; c.fillRect(0, h * 0.5, w, h * 0.2); c.fillStyle = '#86cbd6'; for (let i = 0; i < 6; i++) c.fillRect(i * 160 + 20, h * 0.58, 90, 6);
    c.fillStyle = '#f2dcae'; c.fillRect(0, h * 0.7, w, h * 0.3);
    c.fillStyle = '#7b5a3a'; c.fillRect(w * 0.2, h * 0.38, 12, h * 0.4); c.fillStyle = '#5c9e6a';
    for (let a = 0; a < 5; a++) { c.save(); c.translate(w * 0.2 + 6, h * 0.38); c.rotate(-1.3 + a * 0.6); c.beginPath(); c.ellipse(55, 0, 60, 14, 0, 0, Math.PI * 2); c.fill(); c.restore(); }
    c.fillStyle = '#f36f6f'; c.beginPath(); c.moveTo(w * 0.55, h * 0.82); c.lineTo(w * 0.62, h * 0.62); c.lineTo(w * 0.69, h * 0.82); c.fill();
    c.globalCompositeOperation = 'saturation'; c.fillStyle = 'rgba(128,128,128,0.55)'; c.fillRect(0, 0, w, h);
    c.globalCompositeOperation = 'source-over'; c.fillStyle = 'rgba(255,248,235,0.25)'; c.fillRect(0, 0, w, h);
  }), roughness: 0.85 })); poster.name = 'wall'; SOLID.push(poster); onWall(poster, -0.8, 1.45, 0.3);
  { const fr = new THREE.Mesh(new THREE.BoxGeometry(1.53, 1.08, 0.015), brass()); fr.name = 'wall'; SOLID.push(fr); onWall(fr, -0.8, 1.45, 0.29); }
  const nail = new THREE.Mesh(new THREE.CylinderGeometry(0.012, 0.012, 0.06, 10), clay('#8a8f99', { metalness: 0.6, roughness: 0.3 })); nail.name = 'nail'; SOLID.push(nail);
  const nailG = new THREE.Group(); nail.rotation.x = Math.PI / 2; nail.position.z = 0.03; nailG.add(nail); onWall(nailG, -0.55, 1.12, 0.3);
  { const plank = new THREE.Mesh(new RoundedBoxGeometry(0.16, 0.16, 0.03, 2, 0.01), brass()); plank.name = 'wall'; SOLID.push(plank); onWall(plank, -0.55, 1.12, 0.29); }

  // 기송관 + 받침대 + 캡슐
  const TX = 1.15, TZ = -0.55, TY = 1.12, TL = RH - TY - 0.06;
  add(new THREE.Mesh(new THREE.CylinderGeometry(0.11, 0.11, TL, 32, 1, true), new THREE.MeshPhysicalMaterial({ color: '#dff4ff', roughness: 0.05, transparent: true, opacity: 0.35 }))).position.set(TX, TY + 0.06 + TL / 2, TZ);
  const collar = add(new THREE.Mesh(new THREE.TorusGeometry(0.115, 0.022, 10, 32), brass())); collar.rotation.x = Math.PI / 2; collar.position.set(TX, TY + 0.08, TZ);
  add(new THREE.Mesh(new THREE.CylinderGeometry(0.03, 0.05, TY - 0.06, 16), brass()), 'tray').position.set(TX, (TY - 0.06) / 2, TZ);
  add(new THREE.Mesh(new RoundedBoxGeometry(0.42, 0.12, 0.34, 3, 0.03), clay('#E9DCC4', { roughness: 0.5 })), 'tray').position.set(TX, TY, TZ);
  const capsule = new THREE.Group(); g.add(capsule); capsule.visible = false;
  add(new THREE.Mesh(new THREE.CapsuleGeometry(0.075, 0.16, 8, 20), new THREE.MeshPhysicalMaterial({ color: '#cfe9ff', roughness: 0.1, transparent: true, opacity: 0.6 })), null, capsule);
  // 상자 투입구(펌프 오른쪽 앞) + 떨어지는 상자
  const FUN = { x: 1.05, z: 0.3, top: 0.62 };
  const funMat = clay('#D93A44', { side: THREE.DoubleSide, roughness: 0.4 });
  add(new THREE.Mesh(new THREE.CylinderGeometry(0.25, 0.21, 0.14, 40, 1, true), funMat), 'funnel').position.set(FUN.x, FUN.top - 0.07, FUN.z);
  add(new THREE.Mesh(new THREE.CylinderGeometry(0.21, 0.21, FUN.top - 0.14, 40, 1, true), funMat), 'funnel').position.set(FUN.x, (FUN.top - 0.14) / 2, FUN.z);
  const funRim = add(new THREE.Mesh(new THREE.TorusGeometry(0.25, 0.024, 10, 40), brass()), 'funnel'); funRim.rotation.x = Math.PI / 2; funRim.position.set(FUN.x, FUN.top, FUN.z);
  const funDark = new THREE.Mesh(new THREE.CircleGeometry(0.21, 32), new THREE.MeshBasicMaterial({ color: '#2a0f18' })); funDark.rotation.x = -Math.PI / 2; funDark.position.set(FUN.x, FUN.top - 0.12, FUN.z); g.add(funDark);
  const freeBox = new THREE.Group(); g.add(freeBox); freeBox.visible = false;
  { const fb = new THREE.Mesh(new RoundedBoxGeometry(0.27, 0.215, 0.2, 3, 0.03), clay('#E8B56B', { roughness: 0.7, clearcoat: 0.05 })); fb.castShadow = true; freeBox.add(fb);
    freeBox.add(new THREE.Mesh(new THREE.BoxGeometry(0.03, 0.218, 0.203), clay('#C48A3C', { roughness: 0.6 }))); }
  const freeTicket = new THREE.Group(); g.add(freeTicket); freeTicket.visible = false;
  freeTicket.add(new THREE.Mesh(new RoundedBoxGeometry(0.24, 0.156, 0.012, 2, 0.005), clay('#FFF8EC')));
  const boxMat = clay('#E8B56B', { roughness: 0.7, clearcoat: 0.05 });
  [[-1.75, 0.1075, 0.9, 0.2], [-1.45, 0.1075, 1.1, -0.15], [-1.62, 0.3225, 0.98, 0.1]].forEach(([x, y, z, r]) => { const b = add(new THREE.Mesh(new RoundedBoxGeometry(0.27, 0.215, 0.2, 3, 0.03), boxMat), 'box'); b.position.set(x, y, z); b.rotation.y = r; });

  // 자동 펌프(왼쪽 뒤 구석): 먼지 낀 낡은 기계 + 회전 팔 끝 누름판
  const auto = new THREE.Group(); g.add(auto);
  const dust = clay('#A79C8F', { roughness: 0.85, clearcoat: 0 }), steel = clay('#8a8f99', { metalness: 0.5, roughness: 0.35 });
  add(new THREE.Mesh(new RoundedBoxGeometry(0.5, 0.42, 0.4, 3, 0.05), dust), 'auto', auto).position.y = 0.29;
  const wheels = [];
  for (const [x, z] of [[-0.18, 0.15], [0.18, 0.15], [-0.18, -0.15], [0.18, -0.15]]) { const w = add(new THREE.Mesh(new THREE.CylinderGeometry(0.045, 0.045, 0.04, 20), clay('#4a4550')), 'auto', auto); w.rotation.x = Math.PI / 2; w.position.set(x, 0.045, z); wheels.push(w); }
  const gauge = add(new THREE.Mesh(new THREE.CylinderGeometry(0.07, 0.07, 0.02, 24), clay('#F2EDE4')), 'auto', auto); gauge.rotation.x = Math.PI / 2; gauge.position.set(0.12, 0.33, 0.205);
  const ARM_Y = 0.98, ARM_L = 1.0;
  add(new THREE.Mesh(new THREE.CylinderGeometry(0.04, 0.04, ARM_Y - 0.5, 16), steel), 'auto', auto).position.y = (ARM_Y + 0.5) / 2;
  const arm = new THREE.Group(); arm.position.y = ARM_Y; auto.add(arm);
  const beam = add(new THREE.Mesh(new RoundedBoxGeometry(ARM_L + 0.08, 0.06, 0.08, 2, 0.02), steel), 'auto', arm); beam.position.x = ARM_L / 2;
  const plunger = new THREE.Group(); plunger.position.x = ARM_L; arm.add(plunger);
  add(new THREE.Mesh(new THREE.CylinderGeometry(0.03, 0.03, 0.4, 16), steel), 'auto', plunger).position.y = -0.2;
  add(new THREE.Mesh(new THREE.CylinderGeometry(0.22, 0.22, 0.05, 32), clay('#6b6370')), 'auto', plunger).position.y = -0.4;
  const PLUNGE_TOUCH = BUTTON.top - (ARM_Y - 0.425);
  const AUTO0 = { x: -1.6, z: -1.0, rot: -1.092 };
  const setAuto = ({ x = AUTO0.x, z = AUTO0.z, rot = AUTO0.rot, armRot = 0, armLen = 0.3, plunge = 0.12, roll = 0 } = {}) => {
    beam.scale.x = (armLen + 0.08) / (ARM_L + 0.08); beam.position.x = armLen / 2; plunger.position.x = armLen;   // 접이식 팔
    auto.position.set(x, 0, z); auto.rotation.y = rot; arm.rotation.y = armRot; plunger.position.y = PLUNGE_TOUCH + plunge; wheels.forEach(w => { w.rotation.y = roll; });
  };
  setAuto();

  // ---- 바깥 세계 ----
  const world = new THREE.Group(); g.add(world);
  const sky = new THREE.Mesh(new THREE.SphereGeometry(60, 48, 24), new THREE.MeshBasicMaterial({ side: THREE.BackSide, fog: false, map: canvasTex(16, 512, (c, w, h) => {
    const gr = c.createLinearGradient(0, 0, 0, h); gr.addColorStop(0, '#2a1438'); gr.addColorStop(0.42, '#7a2a5a'); gr.addColorStop(0.5, '#ff9a7a'); gr.addColorStop(0.56, '#c2457a'); gr.addColorStop(1, '#2a0f24');
    c.fillStyle = gr; c.fillRect(0, 0, w, h); }) })); world.add(sky);
  // 투명 관 + 그 안을 흐르는 빛나는 적혈구(인스턴스)
  const flows = [], cellGeo = new THREE.TorusGeometry(0.16, 0.09, 10, 20), cellMat = new THREE.MeshStandardMaterial({ color: '#ff6a6a', emissive: '#ff3a4a', emissiveIntensity: 1.6, roughness: 0.4 });
  const glassMat = new THREE.MeshPhysicalMaterial({ color: '#ffd0dc', roughness: 0.05, transparent: true, opacity: 0.16, side: THREE.DoubleSide, depthWrite: false });
  const rnd = (k => () => (k = (k * 16807) % 2147483647) / 2147483647)(7);
  const tubesDef = [
    [[-30, 6, -14], [-8, 4.5, -10], [8, 5.5, -12], [30, 8, -16]], [[-28, -1, -9], [-6, 1.5, -11], [12, 0.5, -9], [32, 2.5, -13]],
    [[-20, 12, -22], [0, 9, -20], [22, 11, -24]], [[18, -4, -6], [10, 2, -10], [6, 9, -14], [10, 16, -18]],
    [[-16, -5, 6], [-11, 1.5, -2], [-14, 7, -10], [-20, 12, -16]], [[26, 4, 4], [14, 3, -3], [6, 4.5, -7], [-6, 6, -8], [-24, 9, -4]],
    [[-36, 3, -26], [-10, 6, -30], [20, 4, -32], [40, 7, -28]]];
  for (const pts of tubesDef) {
    const curve = new THREE.CatmullRomCurve3(pts.map(p => new THREE.Vector3(...p)));
    const len = curve.getLength(), R = 0.55;
    world.add(new THREE.Mesh(new THREE.TubeGeometry(curve, 160, R, 20), glassMat));
    for (let k = 0; k < Math.floor(len / 3); k++) { const ring = new THREE.Mesh(new THREE.TorusGeometry(R + 0.02, 0.05, 6, 24), brass({ emissive: '#ff9a5a', emissiveIntensity: 0.4 })); const u = (k + 0.5) / Math.floor(len / 3); ring.position.copy(curve.getPointAt(u)); ring.quaternion.setFromUnitVectors(new THREE.Vector3(0, 0, 1), curve.getTangentAt(u)); world.add(ring); }
    const n = Math.floor(len * 1.6), inst = new THREE.InstancedMesh(cellGeo, cellMat, n); world.add(inst);
    flows.push({ curve, inst, n, len, off: Array.from({ length: n }, () => [rnd(), (rnd() - 0.5) * 0.5, (rnd() - 0.5) * 0.5, rnd() * 6]) });
  }
  // 먼 펌프탑들(불 켜진 둥근 창)
  const towerMat = mat('#3a1830', { roughness: 0.8 }), winMat = new THREE.MeshStandardMaterial({ color: '#ffd9a0', emissive: '#ffb070', emissiveIntensity: 1.5 });
  for (const [x, z, h, r] of [[-14, -18, 14, 2.2], [-6, -24, 18, 2.8], [9, -20, 12, 2.0], [17, -15, 9, 1.6], [24, -26, 16, 2.6], [-22, -10, 10, 1.8]]) {
    const tw = new THREE.Mesh(new THREE.CylinderGeometry(r * 0.85, r, h, 24), towerMat); tw.position.set(x, h / 2 - 6, z); world.add(tw);
    const capm = new THREE.Mesh(new THREE.SphereGeometry(r * 0.85, 24, 12, 0, Math.PI * 2, 0, Math.PI / 2), towerMat); capm.position.set(x, h - 6, z); world.add(capm);
    for (let k = 0; k < 10; k++) { const w = new THREE.Mesh(new THREE.CircleGeometry(0.22, 12), winMat); const a = rnd() * 2 - 1, yy = -5 + rnd() * (h - 1);
      w.position.set(x + Math.sin(a) * r * 0.93, yy, z + Math.cos(a) * r * 0.93); w.rotation.y = a; world.add(w); }
  }
  // 떠다니는 빛 입자(가까운 공기)
  const motes = new THREE.InstancedMesh(new THREE.SphereGeometry(0.012, 6, 4), new THREE.MeshBasicMaterial({ color: '#ffd8b0', transparent: true, opacity: 0.5 }), 140); g.add(motes);
  const moteP = Array.from({ length: 140 }, () => [(rnd() - 0.5) * 9, rnd() * 3.2, (rnd() - 0.5) * 7, rnd() * 6]);
  const M4 = new THREE.Matrix4(), Q = new THREE.Quaternion(), V = new THREE.Vector3(), Sx = new THREE.Vector3(1, 1, 1);
  const setTime = t => {
    for (const f of flows) for (let k = 0; k < f.n; k++) { const o = f.off[k]; const u = ((o[0] + t * 2.2 / f.len) % 1 + 1) % 1;
      V.copy(f.curve.getPointAt(u)); V.x += o[1]; V.y += o[2]; Q.setFromEuler(new THREE.Euler(o[3] + t * 0.8, o[3] * 2, 0)); M4.compose(V, Q, Sx); f.inst.setMatrixAt(k, M4); }
    flows.forEach(f => { f.inst.instanceMatrix.needsUpdate = true; });
    moteP.forEach((p, k) => { V.set(p[0] + Math.sin(t * 0.3 + p[3]) * 0.3, (p[1] + t * 0.08) % 3.2, p[2] + Math.cos(t * 0.25 + p[3]) * 0.3); M4.compose(V, Q.identity(), Sx); motes.setMatrixAt(k, M4); });
    motes.instanceMatrix.needsUpdate = true;
  };
  setTime(0);
  const atmo = { fog: '#b4416e', near: 7, far: 55 };

  // 박동: v 0..1(쿵 순간 1), on = 켜진 전구 수(C1), level = 전체 밝기(박동이 끊기면 내려감)
  const setBeat = (v, on = 12, level = 1) => {
    bulbs.forEach((b, i) => { const k = (i < on ? 1 : 0) * level; b.bm.emissiveIntensity = k * (0.5 + 1.4 * v); b.L.intensity = k * (0.7 + 1.5 * v); });
    wallSeam.forEach(m => { m.emissiveIntensity = (0.25 + 1.6 * v) * level; });
    glowMat.emissiveIntensity = (0.15 + 2.0 * v) * level; glowMatB.emissiveIntensity = (0.15 + 1.6 * v) * level;
    needles.forEach((n, i) => { n.rotation.z = level > 0.05 ? (1.1 - 2.0 * v * level - 0.25 * i) : 1.3; });
  };
  setBeat(0.3);
  return { group: g, auto, setTime, atmo, SOLID, AUTO0, PLUNGE_TOUCH, setBeat, setPress, setECG, setAuto, capsule, freeBox, freeTicket, FUN, TRAY: { x: TX, y: TY, z: TZ }, nail, ARM_L, DOOR_ANG, ROOM_R, RH };
}
