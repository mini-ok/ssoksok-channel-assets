// 〈심장의 휴가〉 C5–C8 — 쉴 곳을 찾는 투어(장·간·뇌) + 갈비뼈 창가 해먹
import * as THREE from 'three';
import { track, path, steps, distAlong, clamp, lerp, smooth, ease } from './anim.js';

const L3 = (a, b, u) => a.map((v, i) => lerp(v, b[i], u));
const faceAt = (F, T) => { let m = F[0][1], l = [0, 0]; for (const f of F) if (T >= f[0]) { m = f[1]; l = [f[2] || 0, f[3] || 0]; } return [m, l]; };
const blinkAt = (B, T) => { let b = 0; for (const t of B) { const d = Math.abs(T - t); if (d < 0.07) b = Math.max(b, 1 - d / 0.07); } return b; };
function walker(T, pts, stride = 0.21) {   // 경로 걷기 → pose 조각
  const p = path(T, pts), t0 = pts[0][0];
  const st = steps(distAlong(T - t0, pts.map(([t, a, c]) => [t - t0, a, c])), p.speed, stride);
  return { x: p.x, z: p.z, dir: p.dir, moving: p.speed > 0.05, jump: st.bob, footL: st.footL, footR: st.footR, footLz: st.footLz, footRz: st.footRz };
}

// ---------------- C5: 장의 발효 연구소 — 소파인 줄 알았더니 컨베이어 ----------------
export const C5 = { dur: 6, set: 'gut', cast: ['heart', 'gut'], ownTime: true, apply(T, { SETS, R }) {
  const S = SETS.gut, H = R.heart, G = R.gut;
  // 벨트: 2.4초부터 출발(가속), 그 전에는 멈춤 → 벨트 이동 거리
  const beltD = T < 2.4 ? 0 : 0.5 * Math.min(T - 2.4, 0.8) ** 2 / 0.8 * 0.6 + Math.max(0, T - 3.2) * 0.6;
  S.setTime(2 + beltD / 0.35, {});   // 기포·미생물은 시간에 맞춰, 벨트 질감·꾸러미는 벨트 거리로
  const so = S.setSofa(S.SOFA_U + beltD / S.beltLen);
  // 심장: 왼쪽에서 걸어 들어와 소파 앞에서 돌아서서 뒤로 깡충 → 앉음 → 벨트가 움직임
  const fwd = [Math.sin(so.rot), Math.cos(so.rot)];                    // 소파 앞 방향
  const seat = [so.p.x + fwd[0] * 0.22, so.p.z + fwd[1] * 0.22];        // 앉는 자리(등받이에서 띄움)
  const front = [so.p.x + fwd[0] * 1.3, so.p.z + fwd[1] * 1.3];       // 소파 앞 바닥
  let x, z, jump = 0, turn = 0, pose = {};
  if (T < 1.35) { const w = walker(T, [[0, 0.9, front[1]], [1.35, front[0], front[1]]]); x = w.x; z = w.z; turn = -Math.PI / 2; Object.assign(pose, w, { armR: 0.3, elbowR: -1.2, armL: 0.6 }); jump = w.jump; }
  else if (T < 1.75) { x = front[0]; z = front[1]; turn = lerp(-Math.PI / 2, so.rot - Math.PI * 2 * (so.rot > Math.PI / 2 ? 0 : 0), smooth(1.35, 1.7, T)); Object.assign(pose, { armR: 0.3, elbowR: -1.2, armL: 0.4 }); }
  else if (T < 2.15) { const u = (T - 1.75) / 0.4; x = lerp(front[0], seat[0], u); z = lerp(front[1], seat[1], u); jump = lerp(0, S.SEAT_Y + 0.003, u) + 0.35 * 4 * u * (1 - u); turn = so.rot; pose.sq = u < 0.15 ? 0.92 : 1.04; Object.assign(pose, { armR: 0.35, elbowR: -1.2, armL: 0.4 }); }
  else { x = seat[0]; z = seat[1]; jump = S.SEAT_Y + 0.003; turn = so.rot; }
  const k = track({ armL: 0.75, armR: 0.8, elbowR: -0.5, lean: 0, sq: 1 }, [[0, {}], [2.15, { sq: 0.94 }], [2.4, { sq: 0.97, lean: -0.12, armL: 1.15, armR: 1.1 }], [2.9, { lean: -0.16 }],
    [3.2, { lean: 0.15, armL: 0.6, armR: 0.65, sq: 1.04 }, 'back'], [3.8, { lean: 0.02, armL: 0.55, armR: 0.6 }], [5.0, { armL: 0.9 }], [6, {}]])(T);
  if (T >= 2.15) Object.assign(pose, { lean: k.lean, armL: k.armL, armR: k.armR, elbowR: k.elbowR, sq: k.sq * (1 + 0.04 * Math.sin(T * 9) * clamp(T - 3.2)) });
  const [mood, look] = faceAt([[0, 'happy', 0.6, 0], [1.0, 'sparkle', 0.4, 0.2], [2.2, 'happy_closed'], [3.05, 'shock', 0.6, 0], [3.7, 'wow', 0.8, 0], [4.6, 'dizzy']], T);
  H.hold('ticket'); H.setFace(mood, look, blinkAt([0.8], T));
  H.pose({ x, z, jump, turn, armL: 0.75, armR: 0.8, elbowR: -0.5, ...pose });
  // 장: 앞쪽에서 플라스크를 흔들며 콧노래(몸을 좌우로), 심장이 지나갈 때 손 흔들기
  const sway = Math.sin(T * 3.4);
  G.setFace(T > 3.6 && T < 5.2 ? 'happy' : 'happy_closed', [0.4, 0], blinkAt([1.2, 4.2], T));
  G.pose({ x: 0.05, z: 2.4, turn: Math.PI + 0.25, tiltZ: 0.06 * sway, sq: 1 + 0.02 * Math.sin(T * 6.8), armR: 1.6 + 0.25 * Math.sin(T * 6.8), elbowR: -0.6,
    armL: T > 3.6 && T < 5.2 ? 2.5 + 0.25 * Math.sin(T * 14) : 0.76, footL: Math.max(0, sway) * 0.03, footR: Math.max(0, -sway) * 0.03 });
  // 카메라: 컨베이어 뒤쪽 위에서 앞을 바라봄(심장 얼굴과 뒤의 장이 보임)
  const cx = clamp(x, -2.2, 1.2);
  return { cam: { pos: [cx + 0.35, 1.75, -2.25], target: [cx + 0.1, 0.7, 1.2], fov: 50 }, key: 1.0, hemi: 0.45, env: 0.4 };
} };

// ---------------- C6: 간의 정화 공장 — 혼자 갈색 병을 깔때기에 붓다 지친 간, 심장을 보고 반갑게 인사 ----------------
export const C6 = { dur: 6, set: 'liver', cast: ['heart', 'liver'], apply(T, { SETS, R }) {
  const H = R.heart, Lv = R.liver, S = SETS.liver;
  // 심장: 오른쪽에서 들어와(0~1.8) 멈춰 안쓰럽게 봄 → 간의 인사에 미소·손 인사(3.0~3.7) → 화면 왼쪽 아래로 걸어 나감(3.9~6)
  const STOP = [1.5, 1.2];
  let x = STOP[0], z = STOP[1], turn = -1.05, pose = {};
  const ARR = Math.atan2(STOP[0] - 1.95, STOP[1] - 1.55);   // 도착할 때 걷던 방향(여기서 부드럽게 돌아섬)
  if (T < 1.8) { const w = walker(T, [[0, 2.45, 1.58], [0.95, 1.95, 1.55], [1.8, STOP[0], STOP[1]]]); x = w.x; z = w.z; turn = w.dir ?? Math.atan2(1.95 - 2.45, 1.55 - 1.58); Object.assign(pose, w, { armR: 0.3, elbowR: -1.2, armL: 0.5, elbowL: -0.6 }); }
  else if (T < 3.9) { turn = lerp(ARR, -1.05, smooth(1.8, 2.35, T)); }
  else { const w = walker(T, [[3.9, STOP[0], STOP[1]], [4.9, 0.45, 1.9], [6.0, -1.6, 2.3]]); x = w.x; z = w.z; turn = lerp(-1.05, w.dir ?? -1.05, smooth(3.9, 4.15, T)); Object.assign(pose, w, { armR: 0.3, elbowR: -1.2 }); }
  if (T >= 2.95 && T < 3.8) { const wv = Math.sin((T - 2.95) * 14); Object.assign(pose, { armL: 2.1 + 0.25 * wv, elbowL: -0.4 }); }
  const [mood, look] = faceAt([[0, 'happy', -0.4, 0], [1.3, 'pity', -1, 0.1], [2.85, 'relieved', -1, 0], [3.9, 'happy', -0.3, 0]], T);
  H.hold('ticket'); H.setFace(mood, look, blinkAt([1.0, 2.5, 5.2], T));
  H.pose({ x, z, turn, armL: 0.75, armR: 0.8, elbowR: -0.5, ...pose });
  // 간: 깔때기에 갈색 병을 붓는 중(지침, 2.3초쯤 한숨) → 심장을 알아봄(2.4) → 병을 세우고 돌아서서 반갑게 손 흔듦(2.9~4.2) → 다시 깔때기 쪽으로
  Lv.prop('bottle');
  const up = smooth(2.35, 2.7, T) * (1 - smooth(5.15, 5.5, T));          // 병을 세움(1) / 붓는 중(0)
  const face = smooth(2.6, 3.0, T) * (1 - smooth(4.6, 5.1, T));         // 심장 쪽으로 돎
  const sigh = Math.exp(-(((T - 1.5) / 0.35) ** 2));
  const wave = T > 2.9 && T < 4.3 ? smooth(2.9, 3.05, T) * (1 - smooth(4.1, 4.3, T)) : 0;
  Lv.pose({ x: -0.05, z: 0.45, turn: lerp(0.15, -0.2, face), lean: 0.1 * (1 - up) + 0.06 * sigh, sq: 1 - 0.06 * sigh - 0.02 * (1 - up),
    armR: lerp(1.9, 1.5, up), fwdR: lerp(-0.5, -0.3, up), elbowR: lerp(-0.3, -0.9, up),
    armL: wave > 0 ? lerp(0.75, 2.4 + 0.25 * Math.sin((T - 2.9) * 13), wave) : 0.75 - 0.15 * sigh, elbowL: -0.3 * wave });
  const upT = smooth(2.3, 2.5, T) * (1 - smooth(5.45, 5.7, T));   // 병 기울기: 내릴 땐 먼저 세우고, 다시 부을 땐 팔을 올린 뒤 기울임
  Lv.bottleG.rotation.z = lerp(-2.1 + 0.08 * Math.sin(T * 2.2), 0, upT);
  Lv.setFace(T < 2.4 ? (sigh > 0.4 ? 'tired' : 'sleepy') : T < 2.6 ? 'awake' : T < 4.4 ? 'happy' : 'happy_closed', T < 2.4 ? [0.6, -0.4] : [1, 0], blinkAt([0.8, 4.9], T));
  // 병 입구 → 깔때기로 떨어지는 끈적한 줄기
  Lv.root.updateMatrixWorld(true); const m = Lv.bottleG.localToWorld(new THREE.Vector3(0, 0.15, 0));
  const pour = upT < 0.25; S.stream.visible = pour;
  if (pour) { const y1 = 0.31, len = Math.max(0.02, m.y - y1); S.stream.position.set(m.x, y1 + len / 2, m.z); S.stream.scale.set(1, len, 1); }
  return { cam: { pos: [-0.35, 1.25, 3.1], target: [0.5, 0.55, 0.8], fov: 48 } };
} };

// ---------------- C7: 뇌의 관제실 — 간이침대인 줄 알았는데 뇌는 자면서도 그림을 그림 ----------------
export const C7 = { dur: 6, set: 'brain', cast: ['heart', 'brain'], apply(T, { SETS, R }) {
  const H = R.heart, B = R.brain, cot = SETS.brain.cot;
  const cotFront = [cot.position.x + Math.sin(cot.rotation.y) * 1.0, cot.position.z + Math.cos(cot.rotation.y) * 1.0];
  let x, z, turn, pose = {};
  if (T < 2.0) { const w = walker(T, [[0, -2.25, 1.6], [0.9, -1.5, 2.2], [1.5, -0.75, 1.95], [2.0, cotFront[0], cotFront[1]]]); x = w.x; z = w.z; turn = w.moving ? w.dir : Math.PI; Object.assign(pose, w, { armR: 0.5, elbowR: -0.9 }); }
  else if (T < 4.0) { x = cotFront[0]; z = cotFront[1]; turn = lerp(cot.rotation.y + Math.PI, 0.9 + Math.PI * 2, smooth(2.6, 2.9, T)); }
  else { const w = walker(T, [[4.0, cotFront[0], cotFront[1]], [5.0, -1.65, 2.0], [6.0, -2.25, 1.75]], 0.16); x = w.x; z = w.z; turn = w.moving ? w.dir : 0.4; Object.assign(pose, w, { armR: 0.4, elbowR: -1.0, armL: 0.45, elbowL: -0.8 }); }
  const k = track({ armL: 0.75, armR: 0.8, sq: 1 }, [[0, {}], [2.0, {}], [2.3, { armL: 2.4, armR: 1.0, sq: 1.05 }, 'back'], [2.55, { armL: 0.75, armR: 1.6, sq: 1 }], [3.0, { armR: 1.6 }], [3.2, { sq: 0.95, armR: 1.0 }], [3.35, { sq: 1.03 }], [3.5, { sq: 1 }], [4, {}]])(T);
  if (T >= 2.0 && T < 4.0) Object.assign(pose, k);
  // 심장: 침대를 보고 반짝 → 돌아서다 꿈꾸는 뇌를 봄(2.7) → 피식(3.1, 어깨 들썩) → 살금살금 나감
  const [mood, look] = faceAt([[0, 'happy', -0.3, 0], [1.6, 'sparkle', -0.6, 0.2], [2.7, 'wow', 1, -0.2], [3.1, 'smug', 1, -0.1], [4.0, 'happy_closed', 0.5, 0]], T);
  H.hold('ticket'); H.setFace(mood, look, blinkAt([1.2], T));
  H.pose({ x, z, turn, armL: 0.75, armR: 0.8, elbowR: -0.5, ...pose });
  // 뇌: 화이트보드 옆(보드를 가리지 않음)에서 정면을 보고 서서 조는 중 — 고개가 끄덕, 몸이 살랑. 보드엔 꿈(DREAM·해변)이 번져 나오고, 머리 위엔 꿈 방울
  const S = SETS.brain, b = S.board, th = b.rotation.y, lx = -0.8, lz = 0.8;
  const bx = b.position.x + Math.cos(th) * lx + Math.sin(th) * lz, bz = b.position.z - Math.sin(th) * lx + Math.cos(th) * lz;
  const nod = Math.max(0, Math.sin(T * 1.3)) ** 3, sway = Math.sin(T * 0.9);
  B.setFace('sleepy', [0, 0.3]);
  B.pose({ x: bx, z: bz, turn: -0.3, lean: 0.06 + 0.16 * nod, tiltZ: 0.06 * sway, sq: 1 - 0.03 * nod + 0.015 * Math.sin(T * 1.8),
    armR: 1.25 + 0.12 * Math.sin(T * 1.1), fwdR: -0.25 + 0.1 * Math.cos(T * 1.1), elbowR: -0.5, armL: 0.6 + 0.05 * sway });
  S.setBoard(clamp(0.12 + T / 4.2));
  B.root.updateMatrixWorld(true); S.setDream(T, new THREE.Vector3(bx, 1.02 + 0.03 * nod, bz), smooth(0.2, 0.8, T));
  return { cam: { pos: [-0.25, 1.35, 3.3], target: [0.0, 0.85, 0.5], fov: 64 } };
} };

// ---------------- C8a: 혈관 복도 끝이 환해지며 바다와 분홍 갈빗대 휴가지가 보임 — 하이앵글 와이드, 신나서 통통 뛰어감 ----------------
export const C8a = { dur: 5, set: 'nook', cast: ['heart'], ownTime: true, apply(T, { SETS, R }) {
  const S = SETS.nook, H = R.heart; S.setTime(45 + T, { breath: 1 }); S.setHammock(0);
  const r = T < 1.7 ? lerp(11.0, 5.5, T / 1.7) : T < 2.15 ? 5.5 : 0;      // 관 속을 걸어 나옴 → 관 끝에서 멈춰 봄
  let p, jump = 0, sq = 1, pose = {}, lean = 0;
  if (T < 2.15) { p = S.along(r); const st = steps(lerp(0, 5.4, Math.min(T, 1.7) / 1.7), T < 1.7 ? 3.2 : 0, 0.22); Object.assign(pose, st, { armR: 0.35, elbowR: -1.1 }); jump = st.bob;
    if (T >= 1.7) { const u = smooth(1.7, 1.95, T); sq = 1 + 0.06 * Math.sin(u * Math.PI); Object.assign(pose, { armL: lerp(0.75, 1.7, u), armR: lerp(0.35, 1.3, u), elbowR: -0.4 }); } }
  else { // 통통: 0.45초마다 한 번씩 뛰며 휴가지 입구로(6.1 → 2.95)
    const HOP = 0.45, k = Math.floor((T - 2.15) / HOP), u = ((T - 2.15) % HOP) / HOP, n = Math.ceil((5.0 - 2.15) / HOP);
    const r0 = lerp(5.5, 2.95, k / n), r1 = lerp(5.5, 2.95, Math.min(n, k + 1) / n); p = S.along(lerp(r0, r1, u));
    jump = 0.2 * 4 * u * (1 - u); sq = u < 0.1 ? 0.88 : u > 0.92 ? 0.9 : 1.05;
    const sw = Math.sin((T - 2.15) / HOP * Math.PI * 2); Object.assign(pose, { armL: 1.9 + 0.35 * sw, armR: 1.5 - 0.3 * sw, elbowR: -0.4, footL: 0.05 * u * (1 - u) * 4, footR: 0.05 * u * (1 - u) * 4 }); lean = 0.05; }
  const turn = Math.atan2(-S.along(1).x, -S.along(1).z);                  // 휴가지 쪽(관에서 섬으로)
  const [mood, look] = faceAt([[0, 'awake', 0, 0], [1.6, 'wow', 0, -0.2], [2.1, 'sparkle', 0, 0], [3.3, 'happy_closed'], [4.2, 'sparkle']], T);
  H.hold('ticket'); H.setFace(mood, look, blinkAt([0.9], T));
  H.pose({ x: p.x, z: p.z, jump, turn, lean, sq, armL: 0.75, armR: 0.8, elbowR: -0.5, ...pose });
  // 카메라: 다리 옆 높은 곳에서 관 끝·다리·섬·바다를 함께 → 천천히 내려오며 다가감
  const u = ease(clamp(T / 5)), side = new THREE.Vector3(S.along(1).z, 0, -S.along(1).x);
  const base = S.along(lerp(5.2, 3.9, u)).add(side.clone().multiplyScalar(lerp(5.8, 3.9, u)));
  const tgt = S.along(lerp(3.4, 2.4, u));
  return { cam: { pos: [base.x, lerp(5.6, 3.0, u), base.z], target: [tgt.x, lerp(0.2, 0.5, u), tgt.z], fov: lerp(58, 50, u) }, key: 0.85, hemi: 0.32, env: 0.28, bloom: 0.3 };
} };

// ---------------- C8: 갈비뼈 창가 — 해먹에 누워 처음으로 눈을 감음 ----------------
export const C8 = { dur: 7, set: 'nook', cast: ['heart'], ownTime: true, apply(T, { SETS, R }) {
  const S = SETS.nook, H = R.heart, HM = S.HAMMOCK;
  S.setTime(50 + T, { breath: 1 });
  // 걸어 들어옴(0~2.2) → 해먹 앞에서 돌아섬(2.2~2.6) → 뒤로 몸을 던져 누움(2.6~3.3) → 휴가권을 가슴에(3.5~4.3) → 눈 감음(4.6)
  const lieY = HM.a[1] - 0.05 - HM.sag - 0.06 + 0.3;     // 누운 몸 중심 높이(해먹 가운데 + 등 두께)
  const LIE = { x: 0.5, y: lieY - 0.06, z: HM.a[2] };    // 누웠을 때 root(엉덩이 피벗 아래)
  let x, z, jump = 0, turn, lean = 0, pose = {};
  if (T < 2.2) { const p0 = S.along(2.95); const w = walker(T, [[0, p0.x, p0.z], [2.2, 0.35, 0.55]]); x = w.x; z = w.z; turn = w.moving ? w.dir : Math.PI / 2; Object.assign(pose, w); jump = w.jump; }
  else if (T < 2.6) { x = 0.35; z = 0.55; turn = Math.PI / 2; }
  else { const u = clamp((T - 2.6) / 0.7), e = ease(u); x = lerp(0.35, LIE.x, e); z = lerp(0.55, LIE.z, e); jump = lerp(0, LIE.y, e) + 0.25 * 4 * u * (1 - u); turn = Math.PI / 2; lean = -Math.PI / 2 * e; pose.sq = u < 0.15 ? 0.9 : 1; }
  S.setHammock(clamp((T - 3.1) / 0.3) * (1 + 0.15 * Math.max(0, Math.sin((T - 3.3) * 9)) * Math.exp(-(T - 3.3) * 3)));
  const settle = T > 3.3 ? 0.03 * Math.sin((T - 3.3) * 2 * Math.PI / 4) : 0;   // 해먹 흔들
  const k = track({ armL: 0.75, armR: 0.8, elbowR: -0.5 }, [[0, {}], [3.3, {}], [3.6, { armL: 0.3, armR: 0.25, elbowR: -1.3 }], [4.3, { armR: 0.15, elbowR: -1.6 }], [7, {}]])(T);
  const [mood, look] = faceAt([[0, 'wow', 0, 0.2], [1.0, 'sparkle', 0, 0], [2.6, 'happy'], [3.6, 'relieved'], [4.6, 'sleepy']], T);
  H.hold('ticket'); H.setFace(mood, look, blinkAt([1.5], T));
  H.pose({ x, z: z + settle, jump, turn, lean, armL: T > 3.3 ? k.armL : 0.75, armR: T > 3.3 ? k.armR : 0.8, elbowR: T > 3.3 ? k.elbowR : -0.5, ...pose });
  const u = ease(clamp((T - 3.0) / 4));
  return { cam: { pos: L3([0.6, 1.8, 4.3], [0.2, 1.45, 2.4], u), target: L3([-0.1, 0.8, -0.3], [0.05, 0.75, -0.35], u), fov: lerp(60, 46, u) }, key: 0.85, hemi: 0.32, env: 0.28, bloom: 0.3 };
} };
