// 시트콤 연기 도구: 대사 입 움직임, 자동 깜빡임, 말할 때 손짓, 숨쉬기
import { LINES } from './lines.js';
export { LINES };
export const SPK = { 2: 'gut', 3: 'liver', 5: 'brain', 1: 'heart' };
export const clamp = (v, a = 0, b = 1) => Math.max(a, Math.min(b, v));
export const lerp = (a, b, u) => a + (b - a) * u;
export const smooth = (a, b, t) => { const u = clamp((t - a) / (b - a)); return u * u * (3 - 2 * u); };
export const ease = u => u < 0.5 ? 4 * u * u * u : 1 - Math.pow(-2 * u + 2, 3) / 2;
export const FPS = 24;

// 컷의 대사 목록 lines = [[id, at], ...] 에서 who가 T에 말하는 입 벌림(0..1)과 '말하는 중' 정도
export function talk(lines, who, T) {
  let v = 0, on = 0;
  for (const [id, at] of lines) { const L = LINES[id]; if (SPK[L.sid] !== who) continue; const d = T - at;
    if (d >= 0 && d < L.dur) { const k = Math.floor(d * FPS); v = Math.max(v, L.v[k] || 0); on = Math.max(on, smooth(0, 0.15, d) * (1 - smooth(L.dur - 0.45, L.dur - 0.2, d))); } }
  return { v, on };
}
// 자동 깜빡임: 캐릭터마다 다른 간격
const PER = { gut: 2.9, liver: 3.7, brain: 3.3, heart: 2.6 }, PH = { gut: 0.4, liver: 1.3, brain: 2.1, heart: 0.9 };
export function blink(who, T) { const p = PER[who], u = ((T + PH[who]) % p) / p * p; const d = Math.abs(u - p + 0.1); return d < 0.07 ? 1 - d / 0.07 : 0; }

// 한 번에 세우기: o = { x, z, turn, mood, look, talkOn, gest(손짓 세기), ...pose 채널 }
// 말하는 동안 팔이 리듬을 타고(gest), 몸이 살짝 들썩인다. 쉬는 동안은 숨쉬기만.
export function act(r, who, T, lines, o = {}) {
  const { mood = 'happy', look = [0, 0], gest = 1, hand = 'R', ...pose } = o;
  const tk = lines ? talk(lines, who, T) : { v: 0, on: 0 };
  const g = tk.on * gest, w = Math.sin(T * 7.3 + PH[who] * 3), w2 = Math.sin(T * 4.1 + 1);
  const P = { ...pose };
  P.sq = (P.sq ?? 1) + 0.008 * Math.sin(T * 2 * Math.PI / 1.7 + PH[who]) + 0.012 * tk.v;
  if (g > 0) {
    if (hand === 'R' || hand === 'both') { P.armR = (P.armR ?? REST[who][1]) + g * (0.35 + 0.15 * w); P.elbowR = (P.elbowR ?? 0) - g * (0.35 + 0.2 * w2); }
    if (hand === 'L' || hand === 'both') { P.armL = (P.armL ?? REST[who][0]) + g * (0.3 + 0.15 * w2); P.elbowL = (P.elbowL ?? 0) - g * (0.3 + 0.2 * w); }
    P.lean = (P.lean ?? 0) - 0.03 * g * w2; P.tiltZ = (P.tiltZ ?? 0) + 0.025 * g * w;
  }
  r.setFace(mood, look, blink(who, T), tk.v);
  r.pose(P);
  return tk;
}
// 팔 쉬는 각(캐릭터별 기본값)
export const REST = { gut: [0.76, 2.1], liver: [0.73, 2.03], brain: [0.69, 0.69], heart: [0.75, 0.8] };
// 컷 정의 정리: dur 없으면 마지막 대사 끝 + tail
export function cut(def) { if (def.dur == null) { let e = 0; for (const [id, at] of def.lines || []) e = Math.max(e, at + LINES[id].dur); def.dur = Math.round((e + (def.tail ?? 0.4)) * FPS) / FPS; } def.lines = def.lines || []; return def; }
import { path, steps, distAlong, beat } from '../anim.js';
export { beat };
export function walker(T, pts, stride = 0.21) {
  const p = path(T, pts), t0 = pts[0][0];
  const st = steps(distAlong(T - t0, pts.map(([t, a, c]) => [t - t0, a, c])), p.speed, stride);
  return { x: p.x, z: p.z, dir: p.dir, moving: p.speed > 0.05, jump: st.bob, footL: st.footL, footR: st.footR, footLz: st.footLz, footRz: st.footRz };
}
