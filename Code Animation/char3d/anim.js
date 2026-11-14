// 연기 도구: 키 포즈 트랙, 점프 박동, 걷기/달리기 경로
export const ease = u => u < 0.5 ? 4 * u * u * u : 1 - Math.pow(-2 * u + 2, 3) / 2;
export const back = u => { const c = 1.6; return 1 + (c + 1) * Math.pow(u - 1, 3) + c * Math.pow(u - 1, 2); };
export const clamp = (v, a = 0, b = 1) => Math.max(a, Math.min(b, v));
export const lerp = (a, b, u) => a + (b - a) * u;
export const smooth = (a, b, t) => { const u = clamp((t - a) / (b - a)); return u * u * (3 - 2 * u); };

// keys: [[t, {ch: v}, 'back'?], ...] — 지정 안 한 채널은 앞 값을 이어 감. lag: {ch: 초}(겹침 동작)
export function track(base, keys, lag = {}) {
  const filled = []; let cur = { ...base }; for (const [t, k, e] of keys) { cur = { ...cur, ...k }; filled.push([t, cur, e]); }
  const one = (ch, t) => {
    if (t <= filled[0][0]) return filled[0][1][ch];
    for (let i = 1; i < filled.length; i++) { const [t1, p1, e] = filled[i], [t0, p0] = filled[i - 1];
      if (t <= t1) { const u = (t - t0) / (t1 - t0); const w = e === 'back' ? back(u) : e === 'lin' ? u : ease(u); return p0[ch] + (p1[ch] - p0[ch]) * w; } }
    return filled[filled.length - 1][1][ch];
  };
  return t => { const o = {}; for (const ch of Object.keys(cur)) o[ch] = one(ch, t - (lag[ch] || 0)); return o; };
}
// 박동 점프: lands = 착지(쿵) 시각들. 반환 {air: 발 높이 추가, sq, press(0..1 버튼 눌림), since: 마지막 쿵 뒤 경과}
export function beat(t, lands, { air = 0.3, h = 0.13 } = {}) {
  let o = { air: 0, sq: 1, press: 0, since: 99, last: -1 };
  for (let i = 0; i < lands.length; i++) {
    const L = lands[i], d = t - L;
    if (d >= 0) { o.since = d; o.last = i; }
    if (t > L - air - 0.12 && t <= L - air) { const u = (t - (L - air - 0.12)) / 0.12; o.sq = 1 - 0.12 * Math.sin(u * Math.PI / 2); o.press = 0; }   // 웅크림
    else if (t > L - air && t <= L) { const u = (t - (L - air)) / air; o.air = h * 4 * u * (1 - u); o.sq = 1.08 - 0.08 * Math.abs(2 * u - 1); }      // 공중
    else if (d > 0 && d <= 0.3) { const p = Math.sin(clamp(d / 0.24) * Math.PI); o.press = Math.max(o.press, p); o.sq = Math.min(o.sq, 1 - 0.17 * p); } // 쿵(버튼 눌림·찌그러짐)
  }
  return o;
}
// 경로 이동: pts [[t, x, z], ...] 사이를 부드럽게. 반환 {x, z, turn(진행 방향), speed}
// 경로 이동: 같은 자리에 머무는 구간(길이 0)으로 나뉜 '한 번의 걸음'마다 처음·끝만 부드럽게 가감속하고
// 중간 경유점에서는 멈추지 않는다(예전 방식은 경유점마다 섰다 가서 툭툭 끊겨 보였음). 길은 경유점을 잇는 꺾은선 그대로(충돌 검사한 길과 같음).
// 방향(dir)은 0.3m 앞을 보고 정해 모퉁이에서 몸이 확 돌지 않게 한다.
const _legCache = new WeakMap();
function legsOf(pts) {
  let L = _legCache.get(pts); if (L) return L; L = []; let cur = [pts[0]];
  for (let i = 1; i < pts.length; i++) { const a = pts[i - 1], b = pts[i]; if (Math.hypot(b[1] - a[1], b[2] - a[2]) < 1e-6) { if (cur.length > 1) L.push(cur); cur = [b]; } else cur.push(b); }
  if (cur.length > 1) L.push(cur);
  for (const g of L) { g.cum = [0]; for (let i = 1; i < g.length; i++) g.cum.push(g.cum[i - 1] + Math.hypot(g[i][1] - g[i - 1][1], g[i][2] - g[i - 1][2])); g.len = g.cum[g.length - 1]; }
  _legCache.set(pts, L); return L;
}
function atDist(g, d) { d = clamp(d, 0, g.len); let i = 1; while (i < g.length - 1 && g.cum[i] < d) i++; const u = (d - g.cum[i - 1]) / Math.max(1e-9, g.cum[i] - g.cum[i - 1]);
  return [lerp(g[i - 1][1], g[i][1], u), lerp(g[i - 1][2], g[i][2], u)]; }
function warp(u, a) {   // 사다리꼴 속도: 처음 a만큼 가속, 끝 a만큼 감속, 가운데 일정. 반환 [진행률, 속도배율]
  const v = 1 / (1 - a); if (u < a) return [v * u * u / (2 * a), v * u / a]; if (u > 1 - a) { const w = 1 - u; return [1 - v * w * w / (2 * a), v * w / a]; } return [v * (a / 2 + (u - a)), v];
}
export function path(t, pts) {
  const legs = legsOf(pts); if (!legs.length) return { x: pts[0][1], z: pts[0][2], speed: 0 };
  let g = legs[0]; if (t <= g[0][0]) return { x: g[0][1], z: g[0][2], speed: 0 };
  for (const L of legs) { if (t < L[0][0]) { const pv = g[g.length - 1]; return { x: pv[1], z: pv[2], speed: 0 }; } g = L; if (t <= L[L.length - 1][0]) break; }
  const t0 = g[0][0], t1 = g[g.length - 1][0];
  if (t >= t1) { const l = g[g.length - 1]; return { x: l[1], z: l[2], speed: 0 }; }
  const T = t1 - t0, a = Math.min(0.45, 0.4 / T), [k, vk] = warp((t - t0) / T, a), d = k * g.len, [x, z] = atDist(g, d), [xa, za] = atDist(g, d + 0.3), [xb, zb] = atDist(g, d - 0.05);
  return { x, z, speed: vk * g.len / T, dir: Math.atan2(xa - xb, za - zb) };
}
// 걸음: 이동 거리 dist에 따라 발이 번갈아 들림. 반환 {footL, footR, footLz, footRz, bob}
export function steps(dist, speed, stride = 0.22) {
  const ph = dist / stride * Math.PI, k = clamp(speed / 0.4);
  return { footL: Math.max(0, Math.sin(ph)) * 0.06 * k, footR: Math.max(0, -Math.sin(ph)) * 0.06 * k,
    footLz: Math.cos(ph) * 0.07 * k, footRz: -Math.cos(ph) * 0.07 * k, bob: Math.abs(Math.sin(ph)) * 0.025 * k };
}
// 경로를 따라 간 거리(적분 근사)
export function distAlong(t, pts, dt = 1 / 48) { let d = 0, p = path(0, pts); for (let s = dt; s <= t; s += dt) { const q = path(s, pts); d += Math.hypot(q.x - p.x, q.z - p.z); p = q; } return d; }
