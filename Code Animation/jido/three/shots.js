// 〈지도〉 애니매틱 3D 컷들. 거실(scene.js build) + 복도·계단 세트(x+20) + 새 방(x-20).
// 컷마다 { dur, light, setup(S), pose(S, t) → {cam, focus?} }
import * as THREE from 'three';
import { RoundedBoxGeometry } from 'three/addons/geometries/RoundedBoxGeometry.js';
import { animate as meetAnimate, CAM as MEET_CAM, knit, fabric, rnd } from './scene.js';

const cl = u => Math.min(1, Math.max(0, u));
const sm = u => { u = cl(u); return u * u * (3 - 2 * u); };
const ramp = (t, a, b) => cl((t - a) / (b - a));
const lerp = (a, b, u) => a + (b - a) * u;
const L3 = (a, b, u) => [lerp(a[0], b[0], u), lerp(a[1], b[1], u), lerp(a[2], b[2], u)];
const GREEN = new THREE.Color('#62ff86'), AMBER = new THREE.Color('#ffaa2e');

// ---------------------------------------------------------------- 공용 자세
export function setVac(S, x, z, yaw, t, mood = 0, y = 0) {
  S.vac.position.set(x, y, z); S.vac.rotation.y = yaw;
  S.turret.rotation.y = t * 9; S.brush.rotation.y = -t * 14;
  const blink = 0.5 + 0.5 * Math.cos(t * Math.PI * 6);
  S.led.emissive.copy(GREEN.clone().lerp(AMBER, mood));
  S.led.emissiveIntensity = lerp(6 + 1.5 * Math.sin(t * 3), 3 + 9 * blink, mood);
}
export function setFoot(L, x, z, yaw, lift = 0, pitch = 0) {
  L.g.visible = true; L.g.position.set(x, lift, z); L.g.rotation.y = yaw; L.foot.rotation.x = -pitch;
}
function hideFeet(S) { for (const L of S.legs) L.g.visible = false; }
function slippers(S, on = [true, true]) { S.legs.forEach((L, i) => { L.slm.visible = L.som.visible = on[i]; L.toe.visible = !on[i]; }); }
// 걷기: 두 발이 경로를 따라 번갈아 디딤. path(u) → [x,z], 걸음 수 n
function walk(S, path, u, n, yawOff = 0, stride = 0.09) {
  for (const L of S.legs) {
    const ph = u * n + (L.side > 0 ? 0.5 : 0), k = Math.floor(ph), f = ph - k;
    const sw = f < 0.5 ? sm(f / 0.5) : 1, uu = Math.min(1, (k + sw) / n);
    const p = path(uu), p2 = path(Math.min(1, uu + 0.01)), yaw = Math.atan2(p2[0] - p[0], p2[1] - p[1]) + yawOff;
    const sx = Math.cos(yaw) * stride * 0.5 * L.side, sz = -Math.sin(yaw) * stride * 0.5 * L.side;
    const moving = f < 0.5 && uu < 1;
    setFoot(L, p[0] + sx, p[1] + sz, yaw, moving ? Math.sin(Math.PI * f / 0.5) * 0.04 : 0, moving ? -0.3 * Math.sin(Math.PI * f / 0.5) : 0);
  }
}
function look(pos, target, fov = 36) { return { pos, target, fov }; }

// ---------------------------------------------------------------- 추가 소품·세트
export function addProps(scene) {
  const S = scene.userData.S, P = {};
  const white = new THREE.MeshPhysicalMaterial({ color: '#efece6', roughness: 0.4, clearcoat: 0.6 });
  // 충전대
  const dock = new THREE.Group(); dock.position.set(-0.6, 0, -2.49); scene.add(dock);
  const db = new THREE.Mesh(new RoundedBoxGeometry(0.2, 0.11, 0.08, 4, 0.02), white); db.position.y = 0.055; dock.add(db);
  const dl = new THREE.Mesh(new THREE.SphereGeometry(0.005, 12, 8), new THREE.MeshStandardMaterial({ color: '#000', emissive: '#7fd3ff', emissiveIntensity: 5 })); dl.position.set(0, 0.09, 0.041); dock.add(dl);
  const ramp_ = new THREE.Mesh(new RoundedBoxGeometry(0.22, 0.008, 0.12, 2, 0.003), white); ramp_.position.set(0, 0.004, 0.08); dock.add(ramp_);
  // 과자 부스러기
  const crumbMat = new THREE.MeshPhysicalMaterial({ color: '#d9a35a', roughness: 0.8 }); const R = rnd(31);
  P.crumbs = [];
  for (let i = 0; i < 9; i++) { const c = new THREE.Mesh(new THREE.DodecahedronGeometry(0.006 + R() * 0.005, 0), crumbMat); c.userData.home = [-0.32 + (R() - .5) * 0.18, -0.2 + (R() - .5) * 0.14, R()]; c.visible = false; scene.add(c); P.crumbs.push(c); }
  // 소파 밑을 막은 둥근 쿠션
  const cush = new THREE.Mesh(new RoundedBoxGeometry(0.34, 0.13, 0.34, 6, 0.055), fabric('#a8603e', 55, [3, 3])); cush.visible = false; scene.add(cush); P.cush = cush;
  // 창가 의자
  const chair = new THREE.Group(); chair.position.set(-1.6, 0, -1.05); chair.visible = false; scene.add(chair);
  const wood = new THREE.MeshPhysicalMaterial({ color: '#8a5a34', roughness: 0.45, clearcoat: 0.3 });
  for (const [x, z] of [[-0.2, -0.2], [0.2, -0.2], [-0.2, 0.2], [0.2, 0.2]]) { const l = new THREE.Mesh(new THREE.CylinderGeometry(0.018, 0.014, 0.44, 16), wood); l.position.set(x, 0.22, z); chair.add(l); }
  const seat = new THREE.Mesh(new RoundedBoxGeometry(0.48, 0.04, 0.46, 3, 0.012), wood); seat.position.y = 0.45; chair.add(seat);
  P.chair = chair;
  // 바깥 신발(할머니, 엉뚱한 자리), 가족의 검은 구두
  const shoeG = (hex, rough) => { const g = new THREE.Group(); const m = new THREE.MeshPhysicalMaterial({ color: hex, roughness: rough, clearcoat: rough < 0.4 ? 0.8 : 0 });
    for (const sx of [-0.06, 0.06]) { const b = new THREE.Mesh(new THREE.SphereGeometry(1, 40, 20), m); b.scale.set(0.045, 0.04, 0.13); b.position.set(sx, 0.035, 0); const so = new THREE.Mesh(new RoundedBoxGeometry(0.1, 0.02, 0.27, 2, 0.008), new THREE.MeshPhysicalMaterial({ color: '#3a2a20', roughness: 0.7 })); so.position.set(sx, 0.01, 0); g.add(b, so); }
    g.visible = false; scene.add(g); return g; };
  P.outShoes = shoeG('#7b8a6a', 0.8);
  // 가족의 다리(검은 구두 + 짙은 정장 바지), 한 쌍
  P.family = [];
  for (const side of [-1, 1]) {
    const g = new THREE.Group(); g.visible = false; scene.add(g);
    const m = new THREE.MeshPhysicalMaterial({ color: '#1d1c1f', roughness: 0.25, clearcoat: 1, clearcoatRoughness: 0.1 });
    const b = new THREE.Mesh(new THREE.SphereGeometry(1, 40, 20), m); b.scale.set(0.05, 0.045, 0.15); b.position.set(0, 0.04, 0.05); g.add(b);
    const tr = new THREE.Mesh(new THREE.CylinderGeometry(0.07, 0.065, 0.7, 32), fabric('#2b3140', 61, [3, 6])); tr.position.set(0, 0.42, 0); g.add(tr);
    P.family.push({ g, side });
  }
  // 문틈에서 들어오는 복도 빛을 받는 바닥 띠(밤, 거실 왼쪽 앞)
  P.doorSpot = new THREE.SpotLight('#cfe0ff', 0, 7, 0.22, 0.35, 1.2); P.doorSpot.position.set(-2.15, 1.1, 0.0); P.doorSpot.target.position.set(-0.2, 0, -0.35); scene.add(P.doorSpot, P.doorSpot.target);
  P.lamp = new THREE.PointLight('#ffb36b', 0, 5, 1.6); P.lamp.position.set(1.7, 0.9, -1.6); scene.add(P.lamp);

  // ---- 복도·계단(x+20): 회색 타일 바닥, 벽, 계단참과 내려가는 계단, 차가운 등
  const C = new THREE.Group(); C.position.set(20, 0, 0); scene.add(C); P.corr = C;
  const tileTex = (() => { const c = document.createElement('canvas'); c.width = c.height = 256; const g = c.getContext('2d'); g.fillStyle = '#9a9a96'; g.fillRect(0, 0, 256, 256); g.fillStyle = '#7d7d79'; g.fillRect(0, 0, 256, 3); g.fillRect(0, 0, 3, 256); const r = rnd(9); for (let k = 0; k < 4000; k++) { g.fillStyle = `rgba(0,0,0,${r() * 0.08})`; g.fillRect(r() * 256, r() * 256, 2, 2); } const t = new THREE.CanvasTexture(c); t.wrapS = t.wrapT = THREE.RepeatWrapping; t.repeat.set(12, 6); t.colorSpace = THREE.SRGBColorSpace; return t; })();
  const cf = new THREE.Mesh(new THREE.PlaneGeometry(6, 3), new THREE.MeshPhysicalMaterial({ map: tileTex, roughness: 0.55 })); cf.rotation.x = -Math.PI / 2; cf.position.set(0.5, 0, -0.5); C.add(cf);
  const cw = new THREE.MeshPhysicalMaterial({ color: '#c9ccc6', roughness: 0.9 });
  const w1 = new THREE.Mesh(new THREE.BoxGeometry(6, 2.6, 0.1), cw); w1.position.set(0.5, 1.3, -1.6); C.add(w1);
  // 계단: x<-1.5 에서 아래로(계단참 끝 모서리 + 내려가는 단들)
  for (let k = 0; k < 6; k++) { const st = new THREE.Mesh(new THREE.BoxGeometry(0.28, 0.17, 1.6), new THREE.MeshPhysicalMaterial({ color: '#8f8f8b', roughness: 0.6 })); st.position.set(-2.6 - k * 0.28, -0.085 - k * 0.17, -0.7); C.add(st); }
  const nose = new THREE.Mesh(new THREE.BoxGeometry(0.03, 0.012, 1.6), new THREE.MeshPhysicalMaterial({ color: '#d9c25a', roughness: 0.5 })); nose.position.set(-2.465, 0.006, -0.7); C.add(nose);   // 계단 끝 노란 미끄럼 방지 띠
  // 바닥을 계단 앞까지만(계단 위쪽은 비움)
  cf.geometry = new THREE.PlaneGeometry(4.0, 3); cf.position.set(-0.45, 0, -0.5);
  const endW = new THREE.Mesh(new THREE.BoxGeometry(0.1, 4.0, 3.4), cw); endW.position.set(-4.6, 0.6, -0.4); C.add(endW);
  const pit = new THREE.Mesh(new THREE.PlaneGeometry(2.2, 3.4), new THREE.MeshPhysicalMaterial({ color: '#6f6f6b', roughness: 0.7 })); pit.rotation.x = -Math.PI / 2; pit.position.set(-3.5, -1.05, -0.4); C.add(pit);
  const rail = new THREE.Mesh(new THREE.CylinderGeometry(0.02, 0.02, 1.9, 12), new THREE.MeshPhysicalMaterial({ color: '#3c3f44', roughness: 0.3, metalness: 0.8 })); rail.rotation.z = 1.0; rail.position.set(-3.3, 0.35, -1.45); C.add(rail);
  P.corrLight = new THREE.PointLight('#d8e6ff', 0, 7, 1.4); P.corrLight.position.set(20 - 0.8, 2.2, -0.6); scene.add(P.corrLight);
  P.homeDoor = new THREE.PointLight('#ffc88a', 0, 4, 1.6); P.homeDoor.position.set(20 + 2.2, 0.6, -0.2); scene.add(P.homeDoor);
  P.lostSlip = new THREE.Group(); C.add(P.lostSlip); P.lostSlip.visible = false;
  { const m = S.legs[0].slm.clone(); const so = S.legs[0].som.clone(); P.lostSlip.add(m, so); P.lostSlip.position.set(-1.6, 0.02, -0.35); P.lostSlip.rotation.set(0, 0.9, 1.35); }

  // ---- 새 방(x-20): 밝은 회색 마루, 옅은 하늘색 벽
  const N = new THREE.Group(); N.position.set(-20, 0, 0); scene.add(N); P.newroom = N;
  const nf = new THREE.Mesh(new THREE.PlaneGeometry(6, 6), new THREE.MeshPhysicalMaterial({ color: '#cfc6b8', roughness: 0.6 })); nf.rotation.x = -Math.PI / 2; N.add(nf);
  const nw = new THREE.Mesh(new THREE.BoxGeometry(6, 2.6, 0.1), new THREE.MeshPhysicalMaterial({ color: '#cfdde3', roughness: 0.9 })); nw.position.set(0, 1.3, -1.8); N.add(nw);
  const nb = new THREE.Mesh(new THREE.BoxGeometry(6, 0.08, 0.02), new THREE.MeshPhysicalMaterial({ color: '#f4f4f0', roughness: 0.5 })); nb.position.set(0, 0.04, -1.74); N.add(nb);
  const bedLeg = new THREE.MeshPhysicalMaterial({ color: '#b9b2a6', roughness: 0.4, metalness: 0.6 });
  for (const [x, z] of [[0.9, -1.5], [0.9, -0.5]]) { const l = new THREE.Mesh(new THREE.CylinderGeometry(0.02, 0.02, 0.3, 16), bedLeg); l.position.set(x, 0.15, z); N.add(l); }
  // 청소기 앞 불빛(어두운 복도에서 LED가 길을 비춤)
  P.vacLight = new THREE.SpotLight('#9dffb8', 0, 3.5, 0.6, 0.6, 1.5); P.vacLight.position.set(0, 0.085, 0.16);
  P.vacLight.target.position.set(0, 0.02, 1.2); scene.userData.S.vac.add(P.vacLight, P.vacLight.target);
  P.newLight = new THREE.PointLight('#fff1e0', 0, 6, 1.2); P.newLight.position.set(-20 - 1.0, 1.8, 0.6); scene.add(P.newLight);
  P.all = [dock, ...P.crumbs, cush, chair, P.outShoes, ...P.family.map(f => f.g), P.lostSlip];
  scene.traverse(o => { if (o.isMesh) { o.castShadow = true; o.receiveShadow = true; } });
  S.P = P; return P;
}
function reset(S) {
  const P = S.P;
  for (const c of P.crumbs) c.visible = false;
  P.cush.visible = false; P.chair.visible = false; P.outShoes.visible = false; P.family.forEach(f => f.g.visible = false); P.lostSlip.visible = false;
  slippers(S, [true, true]); for (const L of S.legs) L.g.visible = true;
}

// ---------------------------------------------------------------- 컷
export const SHOTS = {
  // 1. 새벽: 충전대에서 깨어나 첫 출발
  wake: { dur: 7, light: 'dawn', pose(S, t) {
    hideFeet(S);
    const out = sm(ramp(t, 4.0, 5.2)), turn = sm(ramp(t, 4.9, 5.7)), go = ramp(t, 5.4, 7);
    let x = -0.6, z = -2.33 + 0.28 * out, yaw = 0 + turn * 1.4;
    x += Math.sin(yaw) * go * 0.9; z += Math.cos(yaw) * go * 0.9;
    setVac(S, x, z, yaw, t * ramp(t, 2.6, 3.6));
    S.led.emissiveIntensity *= sm(ramp(t, 2.5, 2.8)) * (t < 3.2 ? (Math.sin(t * 30) > 0 ? 1 : 0.2) : 1);
    return { cam: look([-0.2, 0.07, -1.5], L3([-0.6, 0.06, -2.4], [-0.1, 0.05, -2.0], sm(ramp(t, 4.5, 7))), 34) };
  } },
  // 2. 만남: 슬리퍼 앞에서 멈칫(시험 컷)
  meet: { dur: 4, light: 'morning', pose(S, t) { meetAnimate({ userData: { S } }, t); return { cam: look(MEET_CAM.pos, MEET_CAM.target, MEET_CAM.fov) }; } },
  // 3. 부스러기: 할머니가 흘려 준 과자를 청소기가 먹고, 발끝이 까딱
  crumbs: { dur: 5, light: 'morning', pose(S, t) {
    const yawF = -1.75;
    setFoot(S.legs[0], -0.62, -0.28, yawF, 0, ramp(t, 3.4, 4.6) > 0 && ramp(t, 3.4, 4.6) < 1 ? 0.25 * Math.max(0, Math.sin(ramp(t, 3.4, 4.6) * Math.PI * 4)) : 0);
    setFoot(S.legs[1], -0.6, -0.12, yawF + 0.1, 0, 0);
    const vx = lerp(0.6, -0.42, sm(ramp(t, 1.4, 4.2))), vz = -0.2 + 0.05 * Math.sin(t * 2);
    setVac(S, vx, vz, -Math.PI / 2, t, 0);
    for (const c of S.P.crumbs) {
      const [hx, hz, d] = c.userData.home, tf = 0.4 + d * 0.8, fall = ramp(t, tf, tf + 0.35);
      c.visible = t > tf && vx > hx + 0.05; c.position.set(hx, 0.006 + (1 - fall * fall) * 0.35, hz); c.rotation.set(d * 9, d * 7 + t, 0);
    }
    return { cam: look([0.22, 0.07, 0.42], [-0.35, 0.05, -0.25], 36) };
  } },
  // 4. 소파 밑: 발이 쿠션을 밀어 주고, 청소기가 마지막 빈칸으로 들어감
  under: { dur: 6, light: 'morning', pose(S, t) {
    S.P.cush.visible = true;
    const push = sm(ramp(t, 1.2, 2.4));
    S.P.cush.position.set(0.55 + 0.32 * push, 0.065, -1.62 + 0.18 * push); S.P.cush.rotation.set(0, 0, -push * 1.2);
    setFoot(S.legs[0], lerp(0.2, 0.42, sm(ramp(t, 0.6, 1.2))) + 0.12 * push, -1.35 + 0.08 * push, 1.9, Math.sin(Math.PI * ramp(t, 0.6, 1.2)) * 0.04, -0.15 * Math.sin(Math.PI * ramp(t, 1.2, 2.4)));
    setFoot(S.legs[1], 0.15, -1.15, 1.75, 0, 0);
    const a = sm(ramp(t, 2.6, 3.4)), go = sm(ramp(t, 3.6, 6));
    setVac(S, lerp(-0.1, 0.35, a) + 0.25 * go, lerp(-1.0, -1.25, a) - 0.55 * go, lerp(1.6, 2.6, a), t, ramp(t, 2.3, 2.6) - ramp(t, 3.2, 3.5));
    return { cam: look([0.15, 0.06, -0.55], [0.6, 0.06, -1.75], 38) };
  } },
  // 5. 오후: 창가 의자 앞 쉬는 발, 옆에 멈춘 청소기(햇빛이 천천히 옮겨 감)
  afternoon: { dur: 6, light: 'afternoon', pose(S, t) {
    S.P.chair.visible = true;
    setFoot(S.legs[0], -1.66, -0.78, 0.3, 0, -0.1 * Math.sin(t * 1.2)); setFoot(S.legs[1], -1.5, -0.82, 0.15, 0, 0);
    setVac(S, -1.0, -0.78, -2.2, t * 0.1, 0); S.led.emissiveIntensity = 2 + 2 * (0.5 + 0.5 * Math.sin(t * 1.6));
    return { cam: look(L3([-0.75, 0.07, -0.05], [-0.85, 0.075, -0.15], t / 6), [-1.45, 0.1, -0.9], 36) };
  } },
  // 6. 밤: 같은 자리를 세 번 맴도는 발
  circle: { dur: 6, light: 'night', pose(S, t) {
    walk(S, u => [0.05 + 0.3 * Math.cos(u * Math.PI * 2 * 3), -0.75 + 0.22 * Math.sin(u * Math.PI * 2 * 3)], t / 6, 18);
    setVac(S, 1.2, -1.6, -2.4 + 0.25 * Math.sin(t * 0.8), t * 0.2, 0.15);
    return { cam: look([0.55, 0.08, 0.45], [0.1, 0.12, -0.75], 38) };
  } },
  // 7. 가족: 엉뚱한 자리의 바깥 신발, 검은 구두가 다가와 청소기를 들어 올림
  family: { dur: 6, light: 'afternoon', pose(S, t) {
    hideFeet(S); S.P.outShoes.visible = true; S.P.outShoes.position.set(-0.35, 0, -0.55); S.P.outShoes.rotation.y = 2.3;
    const u = ramp(t, 0.8, 3.0);
    S.P.family.forEach((f, i) => { f.g.visible = true; const ph = cl(u * 4 + (i ? 0.5 : 0) - 0.5), k = Math.floor(u * 4), fr = u * 4 - k;
      f.g.position.set(lerp(1.3, 0.38, sm(u)) + f.side * 0.0, (fr < 0.5 && u < 1) ? Math.sin(Math.PI * fr * 2) * 0.03 : 0, lerp(-0.1, -0.35, sm(u)) + f.side * 0.11); f.g.rotation.y = -1.9; });
    const lift = sm(ramp(t, 3.8, 5.6));
    setVac(S, 0.05, -0.42, 0.4, t, ramp(t, 3.4, 3.8), lift * 0.9);
    return { cam: look([0.28, 0.07, 0.62], [0.0, 0.08, -0.4], 38) };
  } },
  // 8. 밤의 문틈: 복도 빛이 바닥에 드리우고, 청소기가 그 빛으로 향함(지도는 지워진 뒤)
  door: { dur: 6, light: 'door', pose(S, t) {
    hideFeet(S);
    const turn = sm(ramp(t, 1.2, 2.4)), go = ramp(t, 2.6, 6);
    const yaw = lerp(2.6, -1.75, turn); const x = 0.35 + Math.sin(yaw) * go * 0.8, z = -0.7 + Math.cos(yaw) * go * 0.8;
    setVac(S, x, z, yaw, t, 0.3 * (1 - ramp(t, 2.4, 3)));
    return { cam: look([0.85, 0.07, 0.3], [-0.35, 0.06, -0.5], 38) };
  } },
  // 9. 계단참: 떨어진 슬리퍼, 계단 끝에 선 발, 청소기가 그 사이로 들어가 불을 비춤
  stairs: { dur: 8, light: 'corridor', pose(S, t) {
    S.P.lostSlip.visible = true; slippers(S, [false, true]);
    const ox = 20, yawF = -1.57 + 0.15 * Math.sin(t * 0.7) * (1 - ramp(t, 5.5, 6.5));
    const turnBack = sm(ramp(t, 5.6, 7.2));
    setFoot(S.legs[0], ox - 2.18 + 0.12 * turnBack, -0.82, yawF + turnBack * 3.0, (t > 5.6 && t < 7.2) ? Math.sin(Math.PI * ramp(t, 5.6, 7.2)) * 0.03 : 0, 0);
    setFoot(S.legs[1], ox - 2.15 + 0.1 * turnBack, -0.62, yawF + turnBack * 3.0 + 0.1, 0, 0);
    const a = sm(ramp(t, 0, 3.0)), b = sm(ramp(t, 3.4, 5.0));
    setVac(S, ox + lerp(0.8, -1.25, a) - 0.55 * b, lerp(-0.4, -0.45, a) - 0.25 * b, -Math.PI / 2 - 0.4 * b, t, ramp(t, 3.0, 3.3) - ramp(t, 5.2, 5.8));
    return { cam: look([ox - 0.2, 0.08, 0.35], [ox - 1.9, 0.12, -0.65], 38) };
  } },
  // 10. 돌아오는 길: 청소기가 앞장서고 발이 따라옴, 오른쪽 문에서 따뜻한 빛
  homeward: { dur: 6, light: 'corridor_home', pose(S, t) {
    slippers(S, [false, true]); const ox = 20;
    setVac(S, ox + lerp(-1.0, 1.4, t / 6), -0.35, Math.PI / 2, t, 0);
    walk(S, u => [ox + lerp(-1.9, 0.75, u), -0.5], cl((t - 0.4) / 5.6), 9, 0, 0.1);
    return { cam: look([ox + lerp(-0.1, 0.9, t / 6), 0.08, 0.55], [ox + lerp(-0.7, 0.6, t / 6), 0.1, -0.45], 38) };
  } },
  // 11. 새 방: 위에서 내려앉는 청소기, LED가 켜짐
  newroom: { dur: 6, light: 'newroom', pose(S, t) {
    hideFeet(S); const ox = -20;
    const down = sm(ramp(t, 0.6, 2.2));
    setVac(S, ox + 0.0, -0.6, 0.3, t * ramp(t, 3.6, 4.4), 0, lerp(0.5, 0, down));
    S.led.emissiveIntensity *= sm(ramp(t, 3.0, 3.3));
    if (t > 4.6) { const g = ramp(t, 4.6, 6); S.vac.position.x += Math.sin(0.3) * g * 0.25; S.vac.position.z += Math.cos(0.3) * g * 0.25; }
    return { cam: look([ox + 0.35, 0.07, 0.35], [ox + 0.0, 0.08, -0.6], 38) };
  } },
};
export function shotPose(S, id, t) { reset(S); return SHOTS[id].pose(S, t); }
