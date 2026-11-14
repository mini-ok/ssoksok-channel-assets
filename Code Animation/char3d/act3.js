// 〈심장의 휴가〉 C9–C13 — 자동 펌프 퍽 → 깨어나 달림 → 쓰러지는 동료들 → 굳은 발판 → 휴가권을 못에 걸고 뛰어오름
import * as THREE from 'three';
import { BUTTON } from './sets/pumproom.js';
import { track, beat, path, steps, distAlong, clamp, lerp, smooth, ease } from './anim.js';

const P = 0.72;
const STAND = v => BUTTON.top - BUTTON.press * v + 0.003;
const L3 = (a, b, u) => a.map((v, i) => lerp(v, b[i], u));
const faceAt = (F, T) => { let m = F[0][1], l = [0, 0]; for (const f of F) if (T >= f[0]) { m = f[1]; l = [f[2] || 0, f[3] || 0]; } return [m, l]; };
const blinkAt = (B, T) => { let b = 0; for (const t of B) { const d = Math.abs(T - t); if (d < 0.07) b = Math.max(b, 1 - d / 0.07); } return b; };
function walker(T, pts, stride = 0.21) {
  const p = path(T, pts), t0 = pts[0][0];
  const st = steps(distAlong(T - t0, pts.map(([t, a, c]) => [t - t0, a, c])), p.speed, stride);
  return { x: p.x, z: p.z, dir: p.dir, moving: p.speed > 0.05, jump: st.bob, footL: st.footL, footR: st.footR, footLz: st.footLz, footRz: st.footRz };
}
const range = (a, b, step = P) => { const o = []; for (let t = a; t < b - 1e-6; t += step) o.push(+t.toFixed(3)); return o; };

// 펌프 공장 소품(연기·나사·못에 건 휴가권) — 처음 한 번만 만든다
function wreck(S) {
  if (S._wreck) return S._wreck;
  const smoke = [], sm = new THREE.MeshStandardMaterial({ color: '#8a8290', roughness: 1, transparent: true, opacity: 0.55, depthWrite: false });
  for (let k = 0; k < 10; k++) { const m = new THREE.Mesh(new THREE.SphereGeometry(0.12, 12, 8), sm.clone()); m.visible = false; S.group.add(m); smoke.push({ m, a: k * 2.39, d: 0.15 + 0.06 * (k % 3) }); }
  const screw = new THREE.Group(); screw.visible = false; S.group.add(screw);
  const sh = new THREE.Mesh(new THREE.CylinderGeometry(0.018, 0.018, 0.09, 10), new THREE.MeshStandardMaterial({ color: '#b8bcc6', metalness: 0.7, roughness: 0.3 })); screw.add(sh);
  const hd = new THREE.Mesh(new THREE.CylinderGeometry(0.035, 0.035, 0.02, 12), sh.material); hd.position.y = 0.05; screw.add(hd);
  const hung = new THREE.Mesh(new THREE.BoxGeometry(0.24, 0.156, 0.012), new THREE.MeshStandardMaterial({ color: '#FFF8EC', emissive: '#ffd9a0', emissiveIntensity: 0 })); hung.visible = false; S.group.add(hung);
  const np = new THREE.Vector3(); S.nail.getWorldPosition(np); const nq = new THREE.Quaternion(); S.nail.parent.getWorldQuaternion(nq);
  S._wreck = { smoke, screw, hung, nailPos: np, nailQ: nq }; return S._wreck;
}
const AUTO = { x: -1.08, z: 0 };
// 나사: 3.0초에 튀어나와 바닥에서 두 번 튀고 멈춤(벽·펌프에 닿지 않는 방향)
function screwAt(t) {
  if (t < 0) return null; const p0 = [AUTO.x + 0.1, 0.6, 0.18], v = [0.75, 2.0, 1.15], g = 9.8;
  let x = p0[0], y = p0[1], z = p0[2], vy = v[1], tt = t, vx = v[0], vz = v[2], spin = t * 18;
  for (let b = 0; b < 3; b++) { const tHit = (vy + Math.sqrt(vy * vy + 2 * g * (y - 0.02))) / g;
    if (tt < tHit) return { x: x + vx * tt, y: y + vy * tt - 0.5 * g * tt * tt, z: z + vz * tt, spin };
    x += vx * tHit; z += vz * tHit; y = 0.02; tt -= tHit; vy = (vy - g * tHit) * -0.38; vx *= 0.5; vz *= 0.5; }
  const slide = Math.min(tt, 0.4); return { x: x + vx * slide * (1 - slide / 0.8), y: 0.02, z: z + vz * slide * (1 - slide / 0.8), spin: 0, rest: true };
}
function setSmoke(W, t, amount) {
  W.smoke.forEach((s, k) => { const life = ((t * 0.6 + k / W.smoke.length) % 1); s.m.visible = amount > 0.02;
    s.m.position.set(AUTO.x + Math.cos(s.a) * s.d * (0.4 + life), 0.55 + life * 1.3, AUTO.z + Math.sin(s.a) * s.d * (0.4 + life)); s.m.scale.setScalar((0.6 + life * 2.2) * Math.max(0.3, amount)); s.m.material.opacity = 0.5 * (1 - life) * amount; });
}

// ---------------- C9: 잘 돌던 자동 펌프가 예고 없이 퍽! ----------------
export const C9 = { dur: 5, set: 'pump', cast: [], ownTime: true, apply(T, { SETS }) {
  const S = SETS.pump, W = wreck(S);
  const lands = range(0.3, 2.95), b = beat(T, lands, { air: 0.3, h: 0.14 });
  const BOOM = 3.0, after = T - BOOM;
  let plunge = b.press > 0 ? -BUTTON.press * b.press : 0.12 * clamp(b.air / 0.14 * 1.6 + (b.since > 0.3 ? 1 : 0), 0, 1);
  if (T > BOOM - 0.25) plunge = 0.12 + (after > 0 ? 0.06 * Math.exp(-after * 3) * Math.sin(after * 40) : 0);
  const jolt = after > 0 && after < 0.25 ? Math.sin(after / 0.25 * Math.PI) : 0;
  S.setAuto({ x: AUTO.x, z: AUTO.z, rot: jolt * 0.06, armRot: after > 0 ? -1.1 * ease(smooth(0, 0.35, after)) : 0, armLen: 1.0, plunge, roll: 0 });
  S.auto.scale.set(1 + 0.08 * jolt, 1 - 0.06 * jolt, 1 + 0.08 * jolt);
  S.setPress(T < BOOM - 0.25 ? b.press : 0);
  setSmoke(W, T, after > 0 ? clamp(after * 3) * (1 - 0.3 * clamp(after - 1)) : 0);
  const sc = screwAt(after); W.screw.visible = !!sc; if (sc) { W.screw.position.set(sc.x, sc.y, sc.z); W.screw.rotation.set(sc.spin, sc.spin * 0.7, sc.rest ? Math.PI / 2 : 0); }
  W.hung.visible = false;
  const lastL = lands.filter(L => L <= T).pop() ?? -9, flash = Math.exp(-(T - lastL) / 0.18);
  const level = after < 0 ? 1 : after < 0.8 ? 0.4 + 0.6 * (Math.sin(after * 47) > 0 ? 1 : 0.2) : clamp(0.5 - (after - 0.8) * 0.3, 0.15, 1);
  S.setBeat(after < 0 ? flash : 0, 12, level); S.setECG(57 + T, lands.map(l => 57 + l), 57 + BOOM, after > 0.3); S.setTime(57 + T);
  const cam = T < 2.6 ? { pos: [0.6, 1.7, 3.6], target: [-0.4, 0.8, -0.3], fov: 50 } : { pos: [0.1, 1.05, 1.6], target: [-1.05, 0.65, -0.05], fov: 46 };
  return { cam, key: 0.35 + 0.55 * level, hemi: 0.15 + 0.25 * level, env: 0.12 + 0.25 * level };
} };

// ---------------- C10: 창가 — 숨이 멈추고 빛이 빠짐, 깨어나 해먹에서 떨어짐 ----------------
export const C10 = { dur: 7, set: 'nook', cast: ['heart'], ownTime: true, apply(T, { SETS, R }) {
  const S = SETS.nook, H = R.heart, HM = S.HAMMOCK;
  const breath = 1 - smooth(0.6, 1.8, T);
  S.setTime(57 + Math.min(T, 1.8) + (T > 1.8 ? (T - 1.8) * 0.05 : 0), { breath });
  const lieY = HM.a[1] - 0.05 - HM.sag - 0.06 + 0.3, LIE = { x: 0.5, y: lieY - 0.06, z: HM.a[2] };
  const LAND = { x: 0.45, z: 0.75 };
  let x = LIE.x, z = LIE.z, jump = LIE.y, turn = Math.PI / 2, lean = -Math.PI / 2, pose = { armL: 0.3, armR: 0.15, elbowR: -1.6 };
  let hold = 'ticket';
  if (T >= 2.8 && T < 3.5) { const u = clamp((T - 2.8) / 0.7), e = ease(u); x = lerp(LIE.x, LAND.x, e); z = lerp(LIE.z, LAND.z, e); jump = lerp(LIE.y, 0, e) + 0.3 * 4 * u * (1 - u); lean = lerp(-Math.PI / 2, 0, e); turn = lerp(Math.PI / 2, Math.PI * 0.15, e); pose = { armL: 2.2, armR: 2.0, elbowR: -0.3, sq: 1.05 }; hold = u > 0.5 ? 'foot' : 'ticket'; }
  else if (T >= 3.5) {
    hold = 'foot';
    if (T < 4.3) { x = LAND.x; z = LAND.z; jump = 0; lean = 0; turn = Math.PI * 0.15; const sq = T < 3.6 ? 0.8 : 1; pose = { sq, armL: 1.4, armR: 1.3, elbowR: -0.2 }; }
    else { const w = walker(T, [[4.3, LAND.x, LAND.z], [5.6, -1.85, 1.25]], 0.26); x = w.x; z = w.z; jump = w.jump; lean = 0.2; turn = w.moving ? w.dir : -Math.PI / 2; Object.assign(pose, w, { armL: 1.0 + 0.6 * Math.sin(T * 20), armR: 1.0 - 0.6 * Math.sin(T * 20), elbowR: -0.3 }); }
  }
  S.setHammock(T < 2.8 ? 1 : clamp(1 - (T - 2.8) / 0.4) + Math.max(0, Math.sin((T - 3.2) * 6)) * 0.4 * Math.exp(-(T - 3.2) * 1.2) * (T > 3.2 ? 1 : 0));
  const [mood, look] = faceAt([[0, 'sleepy'], [2.0, 'wow', 0, -0.4], [2.5, 'shock', 0.3, 0], [3.0, 'panic'], [3.6, 'shock', 0, 0.6], [4.0, 'panic', -0.6, 0]], T);
  H.hold(hold); H.setFace(mood, look, blinkAt([2.15], T));
  H.pose({ x, z, jump, turn, lean, ...pose });
  const dim = smooth(0.8, 2.6, T);
  const u = ease(clamp(T / 7));
  return { cam: { pos: L3([0.2, 1.45, 2.4], [0.6, 1.6, 3.4], ease(clamp((T - 2.6) / 2))), target: L3([0.05, 0.75, -0.35], [-0.4, 0.6, 0.3], ease(clamp((T - 2.6) / 2))), fov: lerp(46, 50, ease(clamp((T - 2.6) / 2))) }, key: 0.85 - 0.6 * dim, hemi: 0.32 - 0.22 * dim, env: 0.28 - 0.2 * dim, bloom: 0.3 };
} };

// ---------------- C11: 혈관 복도를 달리며 — 멈춰 가는 동료들(장·간·뇌) ----------------
export const C11a = { dur: 2.0, set: 'corridor', cast: ['heart'], ownTime: true, apply(T, { SETS, R }) {
  const S = SETS.corridor, H = R.heart; S.setTime(69 + T * 0.25, { flow: 0.2 }); S.setLevel(0.35); for (const d of ['gut', 'liver', 'brain']) S.setDoor(d, 0, 0);
  const w = walker(T, [[0, -6.8, 0.3], [2.0, -2.2, 0.3]], 0.3);
  H.hold('foot'); H.setFace('panic', [1, 0]); H.pose({ x: w.x, z: w.z, jump: w.jump, turn: Math.PI / 2, lean: 0.22, armL: 1.0 + 0.7 * Math.sin(T * 22), armR: 1.0 - 0.7 * Math.sin(T * 22), elbowR: -0.3, footL: w.footL, footR: w.footR, footLz: w.footLz, footRz: w.footRz });
  return { cam: { pos: [w.x + 1.0, 1.0, 1.25], target: [w.x - 0.3, 0.6, -0.2], fov: 56 }, key: 0.4, hemi: 0.2, env: 0.2 };
} };
export const C11b = { dur: 1.6, set: 'gut', cast: ['gut'], ownTime: true, apply(T, { SETS, R }) {   // 장: 컨베이어 멈춤, 털썩 주저앉음
  const S = SETS.gut, G = R.gut; S.setTime(30); S.setSofa(S.SOFA_U + 2.1 / S.beltLen);
  const u = smooth(0.2, 0.7, T);
  G.setFace(T < 0.5 ? 'worry' : 'dizzy'); G.pose({ x: 0.05, z: 2.4, turn: Math.PI + 0.25, sq: lerp(1, 0.84, u), lean: lerp(0, -0.15, u), armR: lerp(1.6, 0.4, u), elbowR: -0.2, armL: lerp(0.76, 0.35, u) });
  return { cam: { pos: [0.55, 0.95, 1.5], target: [0.05, 0.5, 2.4], fov: 46 }, key: 0.35, hemi: 0.18, env: 0.18 };
} };
export const C11c = { dur: 1.6, set: 'liver', cast: ['liver'], ownTime: true, apply(T, { SETS, R }) {   // 간: 깔때기 옆에서 병을 든 채 털썩 주저앉음
  const S = SETS.liver, Lv = R.liver; S.setTime(30); S.stream.visible = false; Lv.prop('bottle');
  const u = smooth(0.2, 0.75, T);
  Lv.setFace(T < 0.5 ? 'tired' : 'dizzy'); Lv.pose({ x: -0.05, z: 0.45, turn: lerp(0.15, -0.55, smooth(0, 0.45, T)), lean: lerp(0.08, 0.22, u), sq: lerp(1, 0.86, u), armR: lerp(1.5, 0.95, u), fwdR: lerp(-0.3, -0.05, u), elbowR: lerp(-0.9, -0.4, u), armL: lerp(0.75, 0.45, u) });
  Lv.bottleG.rotation.z = lerp(0, 0.25, u);
  return { cam: { pos: [-0.2, 1.05, 2.5], target: [0.25, 0.5, 0.45], fov: 44 }, key: 0.35, hemi: 0.18, env: 0.18 };
} };
export const C11d = { dur: 1.6, set: 'brain', cast: ['brain'], ownTime: true, apply(T, { SETS, R }) {   // 뇌: 보드 옆에서 졸던 뇌의 팔이 툭 떨어지고, 꿈 방울이 꺼짐
  const S = SETS.brain, B = R.brain; S.setTime(30); S.setBoard(1);
  const b = S.board, th = b.rotation.y, lx = -0.8, lz = 0.8, u = smooth(0.25, 0.6, T);
  const bx = b.position.x + Math.cos(th) * lx + Math.sin(th) * lz, bz = b.position.z - Math.sin(th) * lx + Math.cos(th) * lz;
  B.setFace(T < 0.4 ? 'sleepy' : 'dizzy'); B.pose({ x: bx, z: bz, turn: -0.3, lean: lerp(0.1, 0.2, u), sq: lerp(1, 0.86, u), armR: lerp(1.25, 0.45, u), fwdR: lerp(-0.25, 0, u), elbowR: lerp(-0.5, 0, u), armL: lerp(0.6, 0.4, u) });
  S.setDream(30 + T, new THREE.Vector3(bx, 1.02, bz), 1 - smooth(0.15, 0.45, T));
  return { cam: { pos: [bx - 0.55, 1.15, bz + 2.0], target: [bx + 0.35, 0.75, bz], fov: 46 }, key: 0.3, hemi: 0.15, env: 0.15 };
} };
export const C11e = { dur: 1.2, set: 'corridor', cast: ['heart'], ownTime: true, apply(T, { SETS, R }) {
  const S = SETS.corridor, H = R.heart; S.setTime(75 + T * 0.2, { flow: 0.1 }); S.setLevel(0.3);
  const w = walker(T, [[0, 3.0, 0.3], [1.2, 6.6, 0.3]], 0.3);
  H.hold('foot'); H.setFace('panic', [1, 0]); H.pose({ x: w.x, z: w.z, jump: w.jump, turn: Math.PI / 2, lean: 0.25, armL: 1.0 + 0.7 * Math.sin(T * 22), armR: 1.0 - 0.7 * Math.sin(T * 22), elbowR: -0.3, footL: w.footL, footR: w.footR, footLz: w.footLz, footRz: w.footRz });
  return { cam: { pos: [1.2, 1.1, 0.5], target: [6.5, 0.8, 0.1], fov: 54 }, key: 0.4, hemi: 0.2, env: 0.2 };
} };

// ---------------- C12: 펌프 공장 — 굳은 발판, 두 번 뛰어도 안 눌림 ----------------
export const C12 = { dur: 9, set: 'pump', cast: ['heart'], ownTime: true, apply(T, { SETS, R }) {
  const S = SETS.pump, H = R.heart, W = wreck(S);
  S.setAuto({ x: AUTO.x, z: AUTO.z, rot: 0, armRot: -1.1, armLen: 1.0, plunge: 0.12 }); S.auto.scale.set(1, 1, 1);
  setSmoke(W, 77 + T, 0.35); const sc = screwAt(5); W.screw.visible = true; W.screw.position.set(sc.x, sc.y, sc.z); W.screw.rotation.set(0, 0, Math.PI / 2); W.hung.visible = false;
  const flick = 0.12 + 0.05 * (Math.sin(T * 31) > 0.7 ? 1 : 0);
  S.setBeat(0, 12, flick); S.setECG(77 + T, [], 0, true); S.setTime(77 + T); S.setPress(0);
  // 문으로 달려 들어와(0~2.6) 발판 앞(2.6) → 뛰어오름(3.0) → 쿵! 안 눌림(3.6, 튕김) → 더 세게(4.6~5.3) 역시 안 눌림 → 주저앉아 울음
  let x, z, jump = 0, turn, lean = 0, pose = {}, sq = 1;
  const runPts = [[0, 3.3, -0.42], [0.8, 2.5, 0.75], [1.6, 1.4, 1.5], [2.5, 0.0, 1.4]];   // 문 바로 안쪽에서 시작(문틀 폭이 팔 벌린 폭보다 좁음)
  if (T < 2.5) { const w = walker(T, runPts, 0.28); x = w.x; z = w.z; jump = w.jump; turn = w.moving ? w.dir : Math.PI; lean = 0.22; const din = smooth(0.15, 0.4, T), sw = 0.7 * din * (1 - smooth(2.0, 2.4, T)), ab = lerp(0.45, 1.0, din); Object.assign(pose, w, { armL: ab + sw * Math.sin(T * 22), armR: ab - sw * Math.sin(T * 22), elbowR: lerp(-1.0, -0.3, din), elbowL: lerp(-0.8, 0, din) }); }
  else if (T < 2.9) { x = 0; z = 1.4; turn = lerp(Math.PI, Math.PI * 2, smooth(2.5, 2.85, T)); sq = 0.85; }
  else if (T < 3.45) { const u = clamp((T - 2.9) / 0.55); x = 0; z = lerp(1.4, 0, u); jump = lerp(0, STAND(0), u) + 0.55 * 4 * u * (1 - u); turn = 0; sq = 1.1; pose = { armL: 2.4, armR: 2.2 }; }
  else if (T < 4.5) { const d = T - 3.45; x = 0; z = 0; turn = 0; const reb = d < 0.45 ? 0.16 * 4 * (d / 0.45) * (1 - d / 0.45) : 0; jump = STAND(0) + reb; sq = d < 0.08 ? 0.72 : d < 0.45 ? 1.06 : 1 - 0.05 * Math.sin((d - 0.45) * 8); pose = { armL: 1.6, armR: 1.4 }; }
  else if (T < 5.25) { const u = clamp((T - 4.5) / 0.75); x = 0; z = 0; turn = 0; jump = STAND(0) + 0.5 * 4 * u * (1 - u); sq = u < 0.12 ? 0.8 : 1.12; pose = { armL: 2.6, armR: 2.5 }; }
  else { const d = T - 5.25; x = 0; z = 0; turn = 0; const reb = d < 0.5 ? 0.18 * 4 * (d / 0.5) * (1 - d / 0.5) : 0; jump = STAND(0) + reb; sq = d < 0.08 ? 0.7 : d < 0.5 ? 1.05 : lerp(1, 0.86, smooth(0.6, 1.2, d)); lean = d > 0.6 ? lerp(0, 0.15, smooth(0.6, 1.2, d)) : 0; pose = { armL: d > 0.6 ? 0.5 : 1.5, armR: d > 0.6 ? 0.45 : 1.4 }; }
  const [mood, look] = faceAt([[0, 'panic', -0.5, 0], [2.6, 'serious', 0, -0.3], [3.5, 'shock', 0, 0.5], [4.1, 'panic', 0, 0.3], [4.5, 'angry'], [5.35, 'shock', 0, 0.6], [6.0, 'cry']], T);
  H.hold('foot'); H.setFace(mood, look, blinkAt([2.7], T));
  H.pose({ x, z, jump, turn, lean, sq, elbowR: -0.3, ...pose });
  const cam = T < 2.5 ? { pos: [1.4, 1.45, 3.4], target: [lerp(3.5, 0.2, smooth(0, 2.5, T)), 0.7, lerp(0, 0.9, smooth(0, 2.5, T))], fov: 50 } : T < 6 ? { pos: [0.35, 1.25, 2.6], target: [0, 0.95, 0], fov: 44 } : { pos: [0.2, 1.05, 1.9], target: [0, 0.95, 0], fov: lerp(44, 36, smooth(6, 9, T)) };
  return { cam, key: 0.3, hemi: 0.12, env: 0.1 };
} };

// ---------------- C13: 발에 붙은 휴가권을 떼어 보고, 못에 걸고, 온몸으로 뛰어오름 ----------------
export const C13 = { dur: 6, set: 'pump', cast: ['heart'], ownTime: true, apply(T, { SETS, R }) {
  const S = SETS.pump, H = R.heart, W = wreck(S);
  S.setAuto({ x: AUTO.x, z: AUTO.z, rot: 0, armRot: -1.1, armLen: 1.0, plunge: 0.12 });
  setSmoke(W, 86 + T, 0.3); const sc = screwAt(5); W.screw.visible = true; W.screw.position.set(sc.x, sc.y, sc.z); W.screw.rotation.set(0, 0, Math.PI / 2);
  S.setBeat(0, 12, 0.12); S.setECG(86 + T, [], 0, true); S.setTime(86 + T);
  // 못 앞에 설 자리: 못 각(-0.55) 방향 반지름 3.0
  const NA = -0.55, NR = 2.95, spot = [NR * Math.sin(NA), -NR * Math.cos(NA)], faceWall = Math.atan2(Math.sin(NA), -Math.cos(NA));
  let x = 0, z = 0, jump = STAND(0), turn = 0, sq = 0.86, lean = 0.12, pose = { armL: 0.5, armR: 0.45 }, hold = 'foot';
  if (T < 1.6) {   // 발을 들어 휴가권을 떼어 손에
    const u = smooth(0.4, 1.0, T), dn = smooth(1.2, 1.5, T);
    pose = { armR: lerp(0.45, 0.3, u), fwdR: lerp(0, -0.5, u), elbowR: lerp(0, -0.6, u), footR: 0.18 * u * (1 - dn), footRz: 0.12 * u * (1 - dn), armL: 0.6 }; lean = lerp(0.12, 0.25, u) * (1 - dn);
    hold = T > 1.05 ? 'ticket' : 'foot';
  } else if (T < 2.4) { hold = 'ticket'; pose = { armR: 0.35, fwdR: -0.9, elbowR: -0.9, armL: 0.5 }; lean = 0.18; }
  else if (T < 3.6) { hold = 'ticket';   // 내려와 못 앞으로 달려감
    const pts = [[2.4, 0, 0], [2.75, 0.58, -1.65], [3.15, 0.1, -2.2], [3.6, spot[0], spot[1]]];
    if (T < 2.75) { const u = (T - 2.4) / 0.35; x = lerp(0, 0.58, u); z = lerp(0, -1.65, u); jump = lerp(STAND(0), 0, u) + 0.4 * 4 * u * (1 - u); turn = Math.PI - 0.2; sq = 1.05; pose = { armL: 0.6, elbowL: -1.0, armR: 0.4, elbowR: -1.2 }; }
    else { const w = walker(T, pts.slice(1), 0.26); x = w.x; z = w.z; jump = w.jump; turn = faceWall; lean = 0.2; Object.assign(pose, w, { armL: 1.0 + 0.6 * Math.sin(T * 20), armR: 0.9, elbowR: -0.6 }); sq = 1; }
  } else if (T < 4.3) {   // 뛰어올라 못에 휴가권을 걺
    const u = clamp((T - 3.6) / 0.6); x = spot[0]; z = spot[1]; turn = faceWall; jump = 0.5 * 4 * u * (1 - u); sq = u < 0.1 ? 0.85 : 1.05; lean = -0.1;
    pose = { armR: 2.3, fwdR: -1.0, elbowR: 0, armL: 1.6 }; hold = u > 0.48 ? 'none' : 'ticket';
  } else {   // 펌프로 달려가 온몸으로 도약(6.0에 착지 = C14 시작)
    hold = 'none';
    if (T < 5.2) { const w = walker(T, [[4.3, spot[0], spot[1]], [4.75, 0.1, -2.15], [5.2, 0.38, -1.45]], 0.3); x = w.x; z = w.z; jump = w.jump; turn = w.moving ? w.dir : Math.PI; lean = 0.25; const tk = smooth(4.85, 5.0, T); Object.assign(pose, w, { armL: lerp(1.0 + 0.7 * Math.sin(T * 22), 0.4, tk), elbowL: -0.8 * tk, armR: lerp(1.0 - 0.7 * Math.sin(T * 22), 0.5, tk) }); sq = 1; }
    else if (T < 5.4) { x = 0.38; z = -1.45; turn = Math.atan2(-0.38, 1.45); sq = lerp(1, 0.75, smooth(5.2, 5.4, T)); pose = { armL: 0.4, armR: 0.4 }; lean = 0.2; }
    else { const u = clamp((T - 5.4) / 0.6); x = lerp(0.38, 0, u); z = lerp(-1.45, 0, u); jump = lerp(0, STAND(0), u) + 0.9 * 4 * u * (1 - u); turn = lerp(Math.atan2(-0.38, 1.45), 0, u); sq = 1.15; pose = { armL: 2.45, armR: 2.4 }; lean = 0; }
  }
  // 못에 걸린 휴가권(4.0~)
  W.hung.visible = T >= 3.9; if (W.hung.visible) { W.hung.position.copy(W.nailPos).add(new THREE.Vector3(0, -0.07, 0)); W.hung.quaternion.copy(W.nailQ); W.hung.translateZ(0.04); if (!W.hung.userData.tex) { W.hung.material = H.ticket.material.map(m => m.clone()); W.hung.userData.tex = true; } }
  S.setPress(0);
  const [mood, look] = faceAt([[0, 'cry', 0, 0.6], [0.6, 'worry', 0.4, 0.8], [1.6, 'cry', 0.3, 0.5], [2.3, 'serious', -0.6, 0], [3.7, 'serious'], [4.2, 'relieved'], [4.4, 'angry', 0, 0], [5.4, 'serious', 0, -0.4]], T);
  H.hold(hold); H.setFace(mood, look, blinkAt([2.0], T));
  H.pose({ x, z, jump, turn, lean, sq, elbowR: -0.3, ...pose });
  const cam = T < 2.4 ? { pos: [0.25, 1.0, 1.6], target: [0.05, 0.85, 0], fov: 42 } : T < 4.3 ? { pos: [1.05, 1.45, -3.0], target: [-0.7, 0.85, -1.9], fov: 54 } : { pos: [1.4, 2.3, 1.9], target: [0.1, lerp(0.6, 0.9, smooth(5.3, 5.8, T)), -1.1], fov: 54 };
  return { cam, key: 0.3, hemi: 0.12, env: 0.1 };
} };
