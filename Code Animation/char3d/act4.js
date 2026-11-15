// 〈심장의 휴가〉 C14–C16 — 박동이 돌아옴 → 복도에서 서로 손 흔듦 → 밤, 가슴에 얹힌 손, 박동 사이의 쉼
import * as THREE from 'three';
import { BUTTON } from './sets/pumproom.js';
import { beat, path, steps, distAlong, clamp, lerp, smooth, ease } from './anim.js';

const STAND = v => BUTTON.top - BUTTON.press * v + 0.003;
const L3 = (a, b, u) => a.map((v, i) => lerp(v, b[i], u));
const faceAt = (F, T) => { let m = F[0][1], l = [0, 0]; for (const f of F) if (T >= f[0]) { m = f[1]; l = [f[2] || 0, f[3] || 0]; } return [m, l]; };
const blinkAt = (B, T) => { let b = 0; for (const t of B) { const d = Math.abs(T - t); if (d < 0.07) b = Math.max(b, 1 - d / 0.07); } return b; };
const range = (a, b, step) => { const o = []; for (let t = a; t < b - 1e-6; t += step) o.push(+t.toFixed(3)); return o; };
const AUTO = { x: -1.08, z: 0 };
function common(S, T, smokeAmt = 0.25) {   // 부서진 자동 펌프·나사·못에 걸린 휴가권 유지
  const W = S._wreck; S.setAuto({ x: AUTO.x, z: AUTO.z, rot: 0, armRot: -1.1, armLen: 1.0, plunge: 0.12 });
  if (W) { W.smoke.forEach((s, k) => { const life = ((T * 0.6 + k / W.smoke.length) % 1); s.m.visible = smokeAmt > 0.02; s.m.position.set(AUTO.x + Math.cos(s.a) * s.d * (0.4 + life), 0.55 + life * 1.3, AUTO.z + Math.sin(s.a) * s.d * (0.4 + life)); s.m.scale.setScalar((0.6 + life * 2.2) * Math.max(0.3, smokeAmt)); s.m.material.opacity = 0.5 * (1 - life) * smokeAmt; });
    W.screw.visible = true; W.hung.visible = true; W.hung.position.copy(W.nailPos).add(new THREE.Vector3(0, -0.07, 0)); W.hung.quaternion.copy(W.nailQ); W.hung.translateZ(0.04); }
  return W;
}

// ---------------- C14: 쿵! 불빛이 파도처럼 돌아옴 ----------------
const L14 = range(0, 8.5, 0.72);
export const C14 = { dur: 8, set: 'pump', cast: ['heart'], ownTime: true, apply(T, { SETS, R }) {
  const S = SETS.pump, H = R.heart; common(S, 92 + T, 0.2 * (1 - smooth(0, 4, T)));
  const b = beat(T, L14, { air: 0.3, h: 0.13 }), first = T < 0.35;
  const press = first ? Math.sin(clamp(T / 0.35) * Math.PI) : b.press;
  const lastL = L14.filter(L => L <= T).pop() ?? 0, flash = Math.exp(-(T - lastL) / 0.18);
  const wave = smooth(0, 1.3, T);
  S.setBeat(flash, Math.round(12 * smooth(0, 0.9, T)), 0.12 + 0.88 * wave);
  S.setECG(92 + T, L14.map(l => 92 + l), 1e9, T < 0.6); S.setTime(92 + T); S.setPress(press);
  const sq = first ? 1 - 0.3 * Math.sin(clamp(T / 0.35) * Math.PI) : b.sq * (1 + 0.008 * Math.sin(T * 4.5));
  const [mood, look] = faceAt([[0, 'serious', 0, -0.3], [0.5, 'wow', 0, -0.5], [1.4, 'shock', 0.6, -0.4], [2.2, 'relieved'], [3.6, 'serious', -0.4, 0], [4.6, 'happy'], [6.4, 'happy_closed']], T);
  H.hold('none'); H.setFace(mood, look, blinkAt([3.1, 6.0], T));
  H.pose({ x: 0, z: 0, jump: STAND(press) + b.air * (first ? 0 : 1), turn: lerp(0, -0.6, smooth(2, 5, T)), sq, armL: 0.75 + 0.6 * Math.exp(-T * 2), armR: 0.8 + 0.6 * Math.exp(-T * 2), elbowR: -0.4 });
  const a = lerp(0.25, 1.3, ease(clamp(T / 8))), r = lerp(2.0, 3.0, ease(clamp(T / 8)));
  const lv = 0.12 + 0.88 * wave;
  return { cam: { pos: [r * Math.sin(a), lerp(0.75, 1.6, ease(clamp(T / 8))), r * Math.cos(a)], target: [0, lerp(1.2, 0.95, ease(clamp(T / 8))), 0], fov: 48 }, key: 0.35 + 0.55 * lv, hemi: 0.15 + 0.25 * lv, env: 0.12 + 0.25 * lv, bloom: 0.5 + 0.4 * Math.exp(-T * 1.5) };
} };

// ---------------- C15: 복도 — 문마다 동료들이 고개를 내밀고, 심장과 손을 흔듦 ----------------
const peek = (T, t0) => smooth(t0, t0 + 0.6, T);
export const C15a = { dur: 5, set: 'corridor', cast: ['gut', 'liver', 'brain'], ownTime: true, apply(T, { SETS, R }) {
  const S = SETS.corridor; S.setTime(100 + T, { flow: 1 }); S.setLevel(1);
  const D = S.DOORS, DZ = S.DOOR_Z;
  [['gut', 0.4], ['liver', 1.2], ['brain', 2.0]].forEach(([id, t0]) => {
    const u = peek(T, t0 + 0.5), c = R[id]; if (c.prop) c.prop('mop'); S.setDoor(id, peek(T, t0) * 1.3, peek(T, t0) * 2);
    c.setFace(T < t0 + 0.9 ? 'wow' : id === 'liver' ? 'happy_closed' : 'happy', [1, 0], blinkAt([t0 + 2], T));
    const z0 = -0.5; c.root.visible = peek(T, t0) > 0.85;   /* 문이 열리기 전엔 안 보임(반투명 터널 너머로 비치지 않게) */ c.pose({ x: D[id] + (id === 'liver' ? 0.15 : 0.05), z: -DZ + z0 + (0.3 - z0) * u, turn: Math.PI / 2 * u, lean: -0.05 * u, armL: lerp(id === 'brain' ? 0.45 : 0.2, 0.76, smooth(0.85, 1, u)), elbowL: id === 'brain' ? 0 : -0.6 * (1 - smooth(0.85, 1, u)), armR: id === 'liver' ? 0.85 : lerp(0.45, 0.8, smooth(0.85, 1, u)) });
  });
  return { cam: { pos: [6.0, 1.15, 0.55], target: [-1.5, 0.75, -0.9], fov: 46 }, key: 1.0, hemi: 0.45, env: 0.4 };
} };
const L15 = range(0.2, 3.5, 0.72);
export const C15b = { dur: 3, set: 'pump', cast: ['heart'], ownTime: true, apply(T, { SETS, R }) {
  const S = SETS.pump, H = R.heart; common(S, 105 + T, 0.05);
  const b = beat(T, L15, { air: 0.3, h: 0.13 }); const lastL = L15.filter(L => L <= T).pop() ?? -1, flash = Math.exp(-(T - lastL) / 0.18);
  S.setBeat(flash, 12, 1); S.setECG(105 + T, L15.map(l => 105 + l)); S.setTime(105 + T); S.setPress(b.press);
  const doorDir = Math.atan2(Math.sin(S.DOOR_ANG), -Math.cos(S.DOOR_ANG));
  H.hold('none'); H.setFace(T < 0.6 ? 'wow' : 'sparkle', [0.6, 0], blinkAt([2.4], T));
  // 디자인 그대로의 인사 자세: 왼팔을 높이 들어 흔듦
  H.pose({ x: 0, z: 0, jump: STAND(b.press) + b.air, turn: lerp(-0.6, doorDir - 0.35, smooth(0, 0.6, T)), sq: b.sq, armL: 2.35 + 0.25 * Math.sin(T * 11) * smooth(0.5, 0.8, T), elbowL: -0.2, armR: 0.75, elbowR: -0.5 });
  const dp = [S.ROOM_R * Math.sin(S.DOOR_ANG) - 0.6, S.ROOM_R * -Math.cos(S.DOOR_ANG)];
  return { cam: { pos: [dp[0] - 0.9, 1.25, dp[1] + 0.9], target: [0, 1.05, 0], fov: 38 }, key: 0.9, hemi: 0.4, env: 0.37 };
} };
export const C15c = { dur: 2.2, set: 'corridor', cast: ['gut', 'liver', 'brain'], ownTime: true, apply(T, { SETS, R }) {
  const S = SETS.corridor; S.setTime(108 + T, { flow: 1 }); S.setLevel(1);
  const D = S.DOORS, DZ = S.DOOR_Z;
  [['gut', 0.0], ['liver', 0.15], ['brain', 0.3]].forEach(([id, t0]) => {
    const c = R[id]; if (c.prop) c.prop('mop'); const w = Math.sin((T - t0) * 12) * smooth(t0, t0 + 0.2, T) * (1 - smooth(1.3, 1.6, T));
    const back = smooth(1.5, 2.1, T);   // 손 흔들고 다시 일하러(뒤돌아 문 안으로 반 걸음)
    S.setDoor(id, 1.3, 2);
    c.setFace(back > 0.3 ? 'happy_closed' : 'sparkle', [1, 0]);
    c.pose({ x: D[id] + (id === 'liver' ? 0.15 : 0.05), z: -DZ + 0.3, turn: lerp(Math.PI / 2, Math.PI * 0.68, back), armR: id === 'liver' ? 0.85 : lerp(0.8, 0.5, back), armL: lerp(0.76, id === 'brain' ? 1.9 : 2.3, smooth(t0, t0 + 0.2, T)) * (1 - back) + 0.76 * back + (id === 'brain' ? 0.15 : 0.25) * w });
  });
  return { cam: { pos: [6.0, 1.15, 0.55], target: [-1.5, 0.75, -0.9], fov: 46 }, key: 1.0, hemi: 0.45, env: 0.4 };
} };

// ---------------- C16: 밤 — 가슴에 얹힌 큰 손, 느려진 박동, 그 사이의 쉼 ----------------
function hand(S) {
  if (S._hand) return S._hand;
  const cv = document.createElement('canvas'); cv.width = cv.height = 512; const c = cv.getContext('2d');
  const g = c.createRadialGradient(256, 300, 20, 256, 300, 250); g.addColorStop(0, 'rgba(255,214,170,0.95)'); g.addColorStop(1, 'rgba(255,170,120,0.0)');
  c.fillStyle = g; c.filter = 'blur(10px)';
  c.beginPath(); c.ellipse(256, 330, 120, 140, 0, 0, Math.PI * 2); c.fill();                                // 손바닥
  [[-95, -40, -0.35, 150], [-45, -120, -0.12, 190], [10, -135, 0.0, 205], [62, -118, 0.12, 185], [130, 10, 0.75, 140]].forEach(([dx, dy, a, L]) => {
    c.save(); c.translate(256 + dx, 300 + dy); c.rotate(a); c.beginPath(); c.ellipse(0, -L / 2 + 40, 34, L / 2, 0, 0, Math.PI * 2); c.fill(); c.restore(); });
  const tex = new THREE.CanvasTexture(cv); tex.colorSpace = THREE.SRGBColorSpace;
  const m = new THREE.Mesh(new THREE.PlaneGeometry(9, 9), new THREE.MeshBasicMaterial({ map: tex, transparent: true, opacity: 0, depthWrite: false, fog: false, toneMapped: false }));
  m.rotation.x = Math.PI / 2 - 0.35; m.position.set(0.5, 8.5, -3.5); S.group.add(m);
  const warm = new THREE.PointLight('#ffb27a', 0, 14, 1.2); warm.position.set(0, 5, -1); S.group.add(warm);
  S._hand = { m, warm }; return S._hand;
}
export const C16 = { dur: 12, set: 'pump', cast: ['heart'], ownTime: true, apply(T, { SETS, R }) {
  const S = SETS.pump, H = R.heart; common(S, 110 + T, 0);
  const Hd = hand(S), hu = smooth(1.2, 4.0, T);
  Hd.m.material.opacity = 0.85 * hu; Hd.m.position.y = lerp(10, 7.6, hu); Hd.warm.intensity = 6 * hu;
  // 박동: 처음 0.9초 간격 → 손이 얹히면 1.7초 간격으로 느려짐
  const lands = []; { let t = 0.3; while (t < 12.5) { lands.push(+t.toFixed(3)); t += lerp(0.9, 1.7, smooth(2, 6, t)); } }
  const b = beat(T, lands, { air: 0.32, h: 0.06 }); const lastL = lands.filter(L => L <= T).pop() ?? -1, since = T - lastL, flash = Math.exp(-since / 0.25);
  S.setBeat(flash * 0.7, 12, 0.55); S.setECG(110 + T, lands.map(l => 110 + l)); S.setTime(110 + T * 0.6); S.setPress(b.press);
  // 박동 사이에는 눈을 감고 졸고, 쿵 할 때만 살짝 뛰어 밟음
  const doze = T > 5 ? clamp(since / 0.35) * clamp((lands.find(L => L > T) ?? 99) - T > 0.3 ? 1 : 0) : 0;
  const mood = T < 1.5 ? 'tired' : T < 3 ? 'wow' : T < 5 ? 'relieved' : (doze > 0.5 ? 'sleepy' : 'happy_closed');
  H.hold('none'); H.setFace(mood, T > 1.5 && T < 3.5 ? [0, -1] : [0, 0]);
  H.pose({ x: 0, z: 0, jump: STAND(b.press) + b.air, turn: -0.35, sq: b.sq * (0.9 + 0.02 * Math.sin(T * 2)), lean: 0.08 + 0.1 * doze, armL: 0.55 + 0.1 * (1 - doze), armR: 0.6, elbowR: -0.3, tiltZ: 0.05 * doze });
  // 카메라: 아래에서 하늘(손)과 심장을 함께 → 못에 걸린 휴가권 → 졸고 있는 심장
  let cam;
  if (T < 5) { const u = ease(clamp(T / 5)); cam = { pos: L3([1.2, 0.5, 2.4], [1.1, 0.6, 2.2], u), target: L3([0, 1.0, 0], [0, 2.6, -1.0], u), fov: 58 }; }
  else if (T < 8) { const W = S._wreck; const np = W.nailPos; cam = { pos: [np.x + 2.3, 1.35, np.z + 0.95], target: [np.x + 0.02, np.y + 0.05, np.z], fov: 24 }; }
  else { const u = ease(clamp((T - 8) / 4)); cam = { pos: L3([1.3, 1.2, 2.4], [0.9, 1.1, 1.8], u), target: [0, 0.95, 0], fov: lerp(42, 36, u) }; }
  return { cam, key: 0.25 + 0.35 * hu, hemi: 0.12 + 0.15 * hu, env: 0.1 + 0.12 * hu, bloom: 0.6 };
} };
