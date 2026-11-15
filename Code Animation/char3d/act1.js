// 〈심장의 휴가〉 C1–C4 (0–32초) — 펌프 공장. 한 타임라인으로 짜고 카메라만 컷마다 바꾼다.
import * as THREE from 'three';
import { BUTTON } from './sets/pumproom.js';
import { track, beat, path, steps, distAlong, clamp, lerp, smooth, ease } from './anim.js';

export const DUR = 32;
const P = 0.72;                                  // 박동 간격
const STAND = v => BUTTON.top - BUTTON.press * v + 0.003;   // 발판 위 발바닥 높이
const range = (a, b, step = P) => { const o = []; for (let t = a; t < b - 1e-6; t += step) o.push(+t.toFixed(3)); return o; };
// 심장이 발판을 밟는 쿵(심장 몸으로): C1~C3 + C4 앞부분
const LANDS = [...range(0.5, 19.9), ...range(21.62, 23.8)];
// 자동 펌프가 대신 누르는 쿵
const AUTO_LANDS = range(28.05, 40);
const ALL_LANDS = [...LANDS, ...AUTO_LANDS].sort((a, b) => a - b);
export const SOUND_CUES = { lands: LANDS, autoLands: AUTO_LANDS };

// 바닥에 내려선 구간들: [시작, 끝] — 이때 발판은 안 눌림
const HOP_OFF_A = [19.85, 20.3], HOP_ON_A = [21.05, 21.62];       // 문 쪽으로 내려섰다가 다시 올라옴
const HOP_OFF_B = [23.95, 24.45];                                  // 자동 펌프를 가지러 내려옴
const SPOT_A = [0.72, 1.28];                                       // 문 쪽 바닥 착지점
const AUTO_END = [-1.08, 0], TH0 = -1.092;                         // 자동 펌프 끝 위치·처음 방향
const BEHIND = 0.7;

// 표정·시선(시각, 표정, 시선x, 시선y)
const FACE = [[0, 'happy', 0, 0], [3.0, 'serious', 0, 0.3], [7.4, 'serious', 0.8, 0.2], [9.2, 'tired', 0, 0], [11.8, 'worry', -1, -0.2], [13.2, 'tired', -1, -0.3], [14.2, 'tired', 0, 0.4],
  [15.9, 'wow', 0.9, -0.6], [16.9, 'shock', 0.9, -0.4], [17.35, 'sparkle', 0.4, 0.2], [18.3, 'sparkle', 0.9, 0], [18.9, 'worry', -0.3, 0.3], [19.4, 'happy', 1, 0], [20.4, 'shock', -0.4, -0.5], [20.7, 'panic', -0.6, -0.3], [21.7, 'relieved', 0, 0],
  [22.4, 'tired', -0.6, 0], [22.8, 'wow', -1, -0.1], [23.3, 'sparkle', -1, 0], [24.0, 'serious', -0.8, 0], [25.2, 'angry', 0, 0], [27.05, 'worry', 0.4, -0.3], [27.45, 'angry', 0.6, 0], [28.15, 'wow', 0.6, -0.2], [28.6, 'sparkle', 0.4, 0], [29.3, 'happy_closed', 0, 0], [30.0, 'happy', 1, 0]];
const BLINKS = [2.2, 5.1, 9.8, 12.4, 18.6, 22.1, 29.9];

export function apply(T, { SETS, R }) {
  const S = SETS.pump, H = R.heart;
  // --- 박동·조명 ---
  const b = beat(T, LANDS), ba = beat(T, AUTO_LANDS, { air: 0.3, h: 0.14 });
  const lastAny = ALL_LANDS.filter(L => L <= T).pop() ?? -9, since = T - lastAny;
  const flash = Math.exp(-since / 0.18);
  const gap = Math.max(0, since - 0.9), level = T < 0.5 ? 0.05 : clamp(1 - gap / 1.6, 0.12, 1) * (T > 27.0 && T < 28.05 ? 0.6 + 0.4 * Math.abs(Math.sin(T * 40)) * (T < 27.6 ? 1 : 0.4) : 1);
  const on = T < 6 ? Math.min(12, Math.floor(LANDS.filter(L => L <= T).length * 1.6)) : 12;
  S.setBeat(flash, on, level);
  const flatFrom = (T > 20.0 && T < 21.62) ? 20.0 : (T > 24.0 && T < 28.05) ? 24.4 : 1e9;
  S.setECG(T, ALL_LANDS, flatFrom, level < 0.5);
  S.setTime(T);

  // --- 자동 펌프 ---
  let autoX = S.AUTO0.x, autoZ = S.AUTO0.z, autoRot = TH0, plunge = 0.12, roll = 0;
  const pushU = smooth(25.45, 26.85, T);
  autoX = lerp(S.AUTO0.x, AUTO_END[0], pushU); autoZ = lerp(S.AUTO0.z, AUTO_END[1], pushU); autoRot = lerp(TH0, 0, smooth(26.2, 26.95, T)); roll = pushU * 1.6 / 0.045;
  if (T > 27.0 && T < 27.65) plunge = 0.12 - 0.13 * smooth(27.0, 27.25, T) + 0.015 * Math.sin(T * 60) * (T > 27.25 ? 1 : 0);     // 첫 누름: 덜컹 걸림
  else if (T >= 27.65 && T < 27.95) plunge = lerp(-0.01, 0.12, smooth(27.65, 27.95, T));
  else if (T >= 27.95) plunge = ba.press > 0 ? -BUTTON.press * ba.press : 0.12 * clamp(ba.air / 0.14 * 1.6 + (ba.since > 0.3 ? 1 : 0), 0, 1);
  const armLen = lerp(0.3, 1.0, smooth(26.9, 27.0, T));
  S.setAuto({ x: autoX, z: autoZ, rot: autoRot, armRot: 0, armLen, plunge, roll });
  const autoPress = T >= 27.95 ? ba.press : (T > 27.15 && T < 27.65 ? 0.1 : 0);

  // --- 심장 위치·높이 ---
  let x = 0, z = 0, jump = STAND(b.press), turn = 0, onFloor = false, extraSq = 1, hold = T < 8.05 ? 'box' : (T >= 17.4 ? 'ticket' : 'none');
  let lean = 0, tiltZ = 0, armL = 0.8, armR = 0.8, elbowL = -0.2, elbowR = -0.4, fwdL = 0, fwdR = 0, footL = 0, footR = 0, footLz = 0, footRz = 0;
  const arc = (t0, t1, from, to, h) => { const u = clamp((T - t0) / (t1 - t0)); return { x: lerp(from[0], to[0], u), z: lerp(from[1], to[1], u), y: lerp(from[2], to[2], u) + h * 4 * u * (1 - u), u }; };
  if (T >= HOP_OFF_A[0] && T < HOP_ON_A[1]) {
    if (T < HOP_OFF_A[1]) { const a = arc(HOP_OFF_A[0], HOP_OFF_A[1], [0, 0, STAND(0)], [SPOT_A[0], SPOT_A[1], 0], 0.5); x = a.x; z = a.z; jump = a.y; }
    else if (T < HOP_ON_A[0]) { x = SPOT_A[0]; z = SPOT_A[1]; jump = 0; onFloor = true; }
    else { const a = arc(HOP_ON_A[0], HOP_ON_A[1], [SPOT_A[0], SPOT_A[1], 0], [0, 0, STAND(0)], 0.5); x = a.x; z = a.z; jump = a.y; }
    turn = Math.atan2(SPOT_A[0], SPOT_A[1]) * (T < HOP_ON_A[0] ? 1 : 1 - smooth(HOP_ON_A[0], HOP_ON_A[1], T));
  } else if (T >= HOP_OFF_B[0]) {
    const land = [-1.5, 0.3];
    const xa = [Math.cos(TH0), -Math.sin(TH0)];                                       // 자동 펌프 진행 방향(밀 때)
    const behind0 = [S.AUTO0.x - xa[0] * BEHIND, S.AUTO0.z - xa[1] * BEHIND];
    const runPts = [[24.5, land[0], land[1]], [24.8, -2.5, -0.45], [25.05, -2.42, -1.3], [25.25, -2.12, -1.92], [25.45, behind0[0], behind0[1]]];
    if (T < HOP_OFF_B[1]) { const a = arc(HOP_OFF_B[0], HOP_OFF_B[1], [0, 0, STAND(0)], [land[0], land[1], 0], 0.6); x = a.x; z = a.z; jump = a.y; turn = Math.atan2(land[0], land[1]); }
    else if (T < 25.45) { const p = path(T, runPts); x = p.x; z = p.z; jump = 0; onFloor = true; turn = p.speed > 0.05 ? p.dir : TH0 + Math.PI / 2;
      const st = steps(distAlong(T - 24.5, runPts.map(([t, a, c]) => [t - 24.5, a, c])), p.speed, 0.2); footL = st.footL; footR = st.footR; footLz = st.footLz; footRz = st.footRz; jump += st.bob;
      lean = 0.18; armL = 0.35 + 0.12 * Math.sin(T * 18); elbowL = -1.0; armR = 0.3; elbowR = -1.4;
      // 자동 펌프와 벽 사이 좁은 틈: 펌프 쪽을 보고 게걸음으로 비집고 지나감(몸 두께만큼만 차지)
      const face = Math.atan2(S.AUTO0.x - x, S.AUTO0.z - z); let d = face - turn; d = Math.atan2(Math.sin(d), Math.cos(d));
      const w = smooth(24.72, 24.92, T); turn += d * w; if (w > 0) { lean = 0.18 * (1 - w); armL = lerp(armL, 0.25, w); fwdL = -0.4 * w; armR = lerp(armR, 0.25, w); elbowR = lerp(-1.4, -0.5, w); } }
    else if (T < 27.0) { const xr = [Math.cos(autoRot), -Math.sin(autoRot)]; x = autoX - xr[0] * BEHIND; z = autoZ - xr[1] * BEHIND; turn = autoRot + Math.PI / 2; onFloor = true; jump = 0;
      const pushing = T < 26.95; lean = pushing ? 0.22 : 0.05; armL = 0.35; armR = 0.35; fwdL = pushing ? -1.25 : -0.3; fwdR = fwdL; elbowL = elbowR = -0.1;
      const st = steps(pushU * 1.75, pushing ? 0.6 : 0, 0.17); footL = st.footL; footR = st.footR; footLz = st.footLz; footRz = st.footRz; }
    else { x = AUTO_END[0] - BEHIND; z = 0; turn = Math.PI / 2; onFloor = true; jump = 0; }
    // 발차기(27.6~28.0) → 기쁨 깡충(28.6) → 문으로 걸어 나감(29.0~)
    if (T >= 27.55 && T < 28.05) { const k = Math.sin(clamp((T - 27.55) / 0.5) * Math.PI); footR = 0.06 * k; footRz = 0.19 * k; lean = -0.12 * k; armL = 1.2; armR = 1.2 + 0.4 * k; }
    if (T >= 28.5 && T < 28.85) { const u = (T - 28.5) / 0.35; jump = 0.12 * 4 * u * (1 - u); extraSq = u < 0.1 || u > 0.9 ? 0.9 : 1.06; armL = 2.4; armR = 2.6; }
    if (T >= 29.0) {
      const ex = [[29.0, AUTO_END[0] - BEHIND, 0], [29.3, -2.3, -0.2], [29.65, -2.58, 0.6], [30.0, -2.45, 1.6], [30.35, -2.0, 2.2], [30.75, -0.9, 2.0], [31.1, 0.8, 1.65], [31.4, 2.4, 0.6], [31.8, 3.2, -0.38], [33.0, 4.4, -0.5]];
      const p = path(T, ex); x = p.x; z = p.z; turn = p.speed > 0.05 ? p.dir : turn; jump = 0; onFloor = true;
      const st = steps(distAlong(T - 29.0, ex.map(([t, a, c]) => [t - 29.0, a, c])), p.speed, 0.21); footL = st.footL; footR = st.footR; footLz = st.footLz; footRz = st.footRz; jump += st.bob;
      armL = T < 31.1 ? 2.2 + 0.25 * Math.sin(T * 14) : lerp(2.2, 0.2, smooth(31.1, 31.45, T)); elbowL = T < 31.1 ? 0 : -0.9 * smooth(31.1, 31.45, T); armR = T < 30.0 ? 0.3 : 0.9; elbowR = T < 30.0 ? -1.4 : -0.9; lean = -0.05;   // 왼손 흔들며, 오른손엔 휴가권
    }
  }

  // --- 위에 올라 박동하는 동안의 상체 연기(키 포즈) ---
  if (!onFloor && !(T >= HOP_OFF_A[0] && T < HOP_ON_A[1]) && T < HOP_OFF_B[0]) {
    const k = track({ armL: 0.75, armR: 0.8, elbowL: -0.2, elbowR: -0.45, lean: 0.03, tiltZ: 0, turn: 0 }, [
      [0, {}], [6.0, {}], [7.4, { turn: 0.25 }], [7.75, { armR: 0.55, elbowR: -0.9 }], [8.05, { armR: 1.35, elbowR: -0.2, tiltZ: -0.08 }, 'back'], [8.6, { armR: 0.8, elbowR: -0.4, tiltZ: 0 }],
      [9.2, { lean: 0.1, turn: 0 }], [11.6, { turn: -0.35 }], [13.4, { lean: 0.16, armL: 0.6, armR: 0.65 }], [14.6, { lean: 0.08 }],
      [15.9, { turn: 0.55, lean: -0.05 }], [16.75, { armR: 1.0, elbowR: -0.3 }], [17.15, { armR: 1.75, fwdR: 0, elbowR: -0.5, tiltZ: -0.06 }, 'back'], [17.5, { armR: 1.0, elbowR: -1.3, tiltZ: 0, turn: 0.2 }],
      [18.3, { turn: 0.6 }], [18.9, { turn: -0.3 }], [19.4, { turn: 0.6 }],
      [21.7, { turn: 0, armL: 1.6, armR: 1.0, elbowR: -1.3 }], [22.3, { armL: 0.75 }], [22.8, { turn: -0.6 }], [23.3, { armL: 1.8 }], [23.8, { armL: 0.8, turn: -0.75 }],
    ], { armL: 0.05, armR: 0.05, elbowR: 0.08 })(T);
    armL = k.armL; armR = k.armR; elbowL = k.elbowL; elbowR = k.elbowR; lean = k.lean; tiltZ = k.tiltZ; turn = k.turn;
  } else if (T >= HOP_OFF_A[1] && T < HOP_ON_A[0]) {   // 문 쪽 바닥에서: 한 발짝 → 어두워짐 → 깜짝
    const u = smooth(20.3, 20.6, T); armL = lerp(0.8, 2.0, u); armR = lerp(1.0, 0.7, u); elbowR = -1.4; lean = lerp(-0.05, -0.15, u);
    turn = Math.atan2(SPOT_A[0], SPOT_A[1]) - lerp(0, Math.PI * 0.75, smooth(20.55, 20.85, T));   // 펌프 쪽으로 홱(휴가권 든 손이 바깥쪽)   // 펌프 쪽으로 홱 돌아봄
  }

  const sq = (onFloor ? 1 : b.sq) * extraSq * (1 + 0.008 * Math.sin(T * 2 * Math.PI / 1.4));
  H.hold(hold);
  let mood = FACE[0][1], look = [0, 0]; for (const f of FACE) if (T >= f[0]) { mood = f[1]; look = [f[2], f[3]]; }
  let blink = 0; for (const bt of BLINKS) { const d = Math.abs(T - bt); if (d < 0.07) blink = Math.max(blink, 1 - d / 0.07); }
  H.setFace(mood, look, blink);
  H.pose({ x, z, jump, turn, lean, tiltZ, sq, armL, armR, elbowL, elbowR, fwdL, fwdR, footL, footR, footLz, footRz });
  S.setPress(onFloor || (T >= HOP_OFF_A[0] && T < HOP_ON_A[1]) || T >= HOP_OFF_B[0] ? autoPress : b.press);

  // --- 떨어지는 상자(8.05~8.6): 손에서 투입구로 ---
  S.freeBox.visible = false;
  if (T >= 8.05 && T < 8.75) {
    if (!apply._box0) { const pre = H.boxMesh.getWorldPosition(new THREE.Vector3()); apply._box0 = pre; }
    const p0 = apply._box0, u = clamp((T - 8.05) / 0.55), top = S.FUN.top;
    const p = new THREE.Vector3(lerp(p0.x, S.FUN.x, u), lerp(p0.y, top - 0.35, u * u) + 0.25 * Math.sin(u * Math.PI) * (1 - u), lerp(p0.z, S.FUN.z, u));
    S.freeBox.position.copy(p); S.freeBox.rotation.set(0, 0.6 * u, 0.4 * Math.sin(u * Math.PI)); S.freeBox.visible = p.y > top - 0.22;
  }
  // --- 캡슐(15.6~16.1 관 속으로 떨어짐) + 휴가권(16.9~17.4 튀어 올라 손으로) ---
  const Tr = S.TRAY; S.capsule.visible = T >= 15.6 && T < 32; S.freeTicket.visible = false;
  if (S.capsule.visible) { const u = clamp((T - 15.6) / 0.5); const restY = Tr.y + 0.06 + 0.155; S.capsule.position.set(Tr.x, lerp(S.RH + 0.1, restY, u * u) + (T > 16.1 && T < 16.3 ? 0.03 * Math.sin((T - 16.1) / 0.2 * Math.PI) : 0), Tr.z); }
  if (T >= 16.9 && T < 17.4) {
    const hp = new THREE.Vector3(); H.ticket.getWorldPosition(hp);
    const u = clamp((T - 16.9) / 0.5), p0 = new THREE.Vector3(Tr.x, Tr.y + 0.3, Tr.z);
    S.freeTicket.visible = true; S.freeTicket.position.set(lerp(p0.x, hp.x, u), lerp(p0.y, hp.y, u) + 0.35 * 4 * u * (1 - u), lerp(p0.z, hp.z, u)); S.freeTicket.rotation.set(u * 6, u * 2, 0);
    H.hold(u > 0.95 ? 'ticket' : 'none');
  }

  // --- 카메라 ---
  const cam = camAt(T, x, z);
  return { cam, key: 0.35 + 0.55 * level, hemi: 0.15 + 0.25 * level, env: 0.12 + 0.25 * level, bloom: 0.5 };
}

function camAt(T, hx, hz) {
  const L = (a, b, u) => a.map((v, i) => lerp(v, b[i], u));
  if (T < 6) { const u = ease(clamp((T - 0.8) / 4.6)); return { pos: L([0.6, 1.0, 1.9], [0.5, 1.55, 3.9], u), target: L([0.1, 3.0, -1.2], [0, 1.05, -0.6], u), fov: lerp(62, 50, u) }; }
  if (T < 9) return { pos: [1.9, 1.35, 2.3], target: [0.55, 1.05, 0.05], fov: 42 };                                  // 상자 넣기
  if (T < 11.5) { const u = (T - 9) / 2.5; return { pos: L([0.2, 1.6, 0.7], [0.0, 1.8, 0.4], u), target: [1.3, 1.9, -2.6], fov: 42 }; }   // 심전도·압력계
  if (T < 12.6) return { pos: [1.6, 1.2, 2.2], target: [-0.1, 1.15, -0.3], fov: 40 };                               // 포스터 보는 심장
  if (T < 14.0) { const u = (T - 12.6) / 1.4; return { pos: L([-0.3, 1.45, 0.2], [-0.4, 1.45, 0.05], u), target: [-2.55, 1.42, -2.55], fov: 34 }; }  // 포스터(심장 시점)
  if (T < 15.6) return { pos: [1.6, 1.2, 2.2], target: [-0.1, 1.15, -0.3], fov: 40 };
  if (T < 17.6) return { pos: [-0.6, 1.45, 2.4], target: [0.6, 1.3, -0.4], fov: 46 };                               // 캡슐·휴가권
  if (T < 19.8) return { pos: [0.2, 1.25, 2.1], target: [0.1, 1.15, 0], fov: 40 };                                  // 휴가권과 문 사이
  if (T < 22.3) return { pos: [0.3, 1.4, 3.6], target: [0.35, 0.8, 0.3], fov: 48 };                                 // 내려섰다가 어두워짐 → 다시 올라감
  if (T < 24.0) return { pos: [0.9, 1.3, 2.4], target: [-0.9, 0.95, -0.7], fov: 46 };                               // 자동 펌프 발견
  if (T < 27.0) return { pos: [-0.2, 1.45, 1.9], target: [-1.7, 0.6, -0.9], fov: 52 };                                // 달려가 밀기
  if (T < 29.0) return { pos: [-0.4, 1.2, 2.2], target: [-0.9, 0.75, 0], fov: 46 };                                 // 덜컹 → 발차기 → 작동
  { const u = ease(clamp((T - 29) / 3)); return { pos: L([1.2, 1.6, 4.2], [2.2, 1.5, 3.3], u), target: [hx * 0.8 + 0.4, 0.8, hz * 0.6], fov: 52 }; }   // 문으로 나감
}
