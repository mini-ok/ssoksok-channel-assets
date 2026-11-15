// 연기 샘플 1 "닿지 않는 선반" (5초) — 포즈 투 포즈 키프레임 + 겹침(팔은 몸보다 늦게) + 흔들림
export const DUR = 5.5;
const ease = u => u < 0.5 ? 4 * u * u * u : 1 - Math.pow(-2 * u + 2, 3) / 2;          // 천천히-빠르게-천천히
const back = u => { const c = 1.6; return 1 + (c + 1) * Math.pow(u - 1, 3) + c * Math.pow(u - 1, 2); };  // 살짝 넘쳤다 돌아옴

// 키 포즈(시간, 값). 지정 안 한 채널은 앞 포즈 값을 이어 감. e: 'back'이면 그 포즈로 들어갈 때 오버슈트
const BASE = { x: 0.3, z: 0.4, armL: 0.7, armR: 0.8, elbowL: -0.2, elbowR: -0.5, fwdL: 0, fwdR: 0, lean: -0.06, tiltZ: 0, turn: 0, sq: 1, hop: 0, lookX: 0.8, lookY: -1 };
const KEYS = [
  [0.0, {}],
  [0.45, {}],                                                                              // 올려다보며 가늠
  [0.75, { sq: 0.88, lean: 0.1, armR: 0.9, elbowR: -0.6, armL: 0.75, lookY: -0.6 }],         // 예비 동작
  [1.0, { sq: 1.15, lean: -0.1, tiltZ: -0.12, armR: 2.4, fwdR: -0.25, elbowR: -0.1, armL: 1.3, elbowL: -0.3, hop: 0.02, lookX: 0.6, lookY: -1 }, 'back'],  // 발끝으로 쭉 뻗기
  [1.3, { sq: 1.16, armR: 2.45, tiltZ: -0.13 }],                                            // 버팀(떨림)
  [1.5, { sq: 0.84, lean: 0.12, tiltZ: -0.04, hop: 0, armL: 0.9, lookY: -0.8 }],             // 점프 준비: 웅크림
  [1.62, { sq: 1.18, lean: -0.12, tiltZ: -0.1, armR: 2.5, armL: 1.6 }],                      // 도약(공중에서 늘어남)
  [1.9, { sq: 1.08, armL: 1.4 }],                                                           // 꼭대기 지나 떨어짐
  [2.02, { sq: 0.8, lean: 0.16, tiltZ: 0, armR: 1.3, armL: 1.0, lookY: -0.2 }],              // 착지 찌그러짐
  [2.25, { sq: 1.02, lean: 0.06, armR: 0.9, elbowR: -0.4, fwdR: 0, armL: 0.78, elbowL: -0.1, lookY: 0.2 }],
  [2.85, { sq: 0.95, lean: 0.22, armR: 0.7, armL: 0.68, elbowR: -0.1, lookX: 0, lookY: 0.9 }], // 축 처짐(한숨)
  [3.3, { lean: 0.18, lookX: -1, lookY: 0.4, turn: -0.12 }],                                 // 곁눈질 → 발판
  [3.6, { lean: 0.05, turn: -0.28, lookX: -1, lookY: 0.2, sq: 1.02 }],                      // 알아챔
  [3.85, { sq: 0.88, lean: 0.1, armL: 0.72 }],                                              // 예비 동작
  [4.1, { sq: 1.12, lean: -0.08, hop: 0.03, armL: 2.3, fwdL: -0.3, elbowL: -0.6, turn: -0.2, armR: 0.9, elbowR: -0.7 }, 'back'],  // "아!"
  [4.5, { sq: 0.97, hop: 0, armL: 2.2 }],
  [5.5, { sq: 1.0, lean: -0.04 }],
];
const MOODS = [[0, 'happy'], [0.7, 'serious'], [1.15, 'panic'], [2.0, 'worry'], [2.6, 'tired'], [3.55, 'wow'], [4.0, 'sparkle']];
const BLINKS = [0.35, 3.1, 5.0];
const JUMPS = [[1.56, 1.98, 0.13], [4.02, 4.32, 0.035]];   // [이륙, 착지, 높이] — 발까지 통째로 뜸(포물선)
const LAG = { armL: 0.05, armR: 0.05, elbowL: 0.09, elbowR: 0.09 };   // 겹침: 팔·팔꿈치가 몸보다 늦게

const filled = []; { let cur = { ...BASE }; for (const [t, k, e] of KEYS) { cur = { ...cur, ...k }; filled.push([t, cur, e]); } }
function sample(ch, t) {
  if (t <= filled[0][0]) return filled[0][1][ch];
  for (let i = 1; i < filled.length; i++) {
    const [t1, p1, e] = filled[i], [t0, p0] = filled[i - 1];
    if (t <= t1) { const u = (t - t0) / (t1 - t0); const w = e === 'back' ? back(u) : ease(u); return p0[ch] + (p1[ch] - p0[ch]) * w; }
  }
  return filled[filled.length - 1][1][ch];
}
export function poseAt(t) {
  const P = {};
  for (const ch of Object.keys(BASE)) P[ch] = sample(ch, t - (LAG[ch] || 0));
  P.jump = 0; for (const [a, b, h] of JUMPS) if (t > a && t < b) { const u = (t - a) / (b - a); P.jump = 4 * h * u * (1 - u); }
  // 버티는 동안 떨림(1.05~1.45초)
  const tr = Math.max(0, Math.min(1, (t - 1.05) / 0.12)) * Math.max(0, Math.min(1, (1.45 - t) / 0.08));
  P.armR += tr * 0.05 * Math.sin(t * 70); P.tiltZ += tr * 0.02 * Math.sin(t * 53 + 1); P.sq += tr * 0.01 * Math.sin(t * 61);
  // 숨쉬기
  P.sq += 0.008 * Math.sin(t * 2 * Math.PI / 1.6);
  let mood = MOODS[0][1]; for (const [mt, m] of MOODS) if (t >= mt) mood = m;
  let blink = 0; for (const b of BLINKS) { const d = Math.abs(t - b); if (d < 0.07) blink = Math.max(blink, 1 - d / 0.07); }
  const look = [P.lookX, P.lookY]; delete P.lookX; delete P.lookY;
  return { pose: P, mood, look, blink };
}
