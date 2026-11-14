// 몸속 주식회사 — 오늘의 판정 · 3D 파일럿(담석 편) 컷 정의
// 컷: { set, cast, lines:[[대사 id, 시작초]], tail, dur?, ov:[2D 합성 지시], post?, apply(T, ctx) → { cam, key, hemi, env, bloom } }
import * as THREE from 'three';
import { act, cut, clamp, lerp, smooth, ease, REST, walker, beat, talk } from './kit.js';
import { BUTTON } from '../sets/pumproom.js';

const STAND = v => BUTTON.top - BUTTON.press * v + 0.003;
const HOME = { gut: [-1.9, 1.15, 0.35], liver: [-0.45, 1.0, 0.1], brain: [0.85, 1.15, -0.2] };
const camB = (x, z, dx = -0.1, d = 2.5, fov = 36) => ({ pos: [x + dx, 0.9, z + d], target: [x, 0.66, z], fov });   // 관제실 자리 [x, z, turn]
const CAM = {
  brainWide: { pos: [0, 1.65, 4.7], target: [0, 1.15, -1.0], fov: 50 },
  monitor: { pos: [0, 1.7, 0.6], target: [0, 1.7, -2.95], fov: 26 },
  board: { pos: [0.42, 1.22, 1.58], target: [1.55, 1.12, 0.35], fov: 40 },
};
const night = (c, a = 0) => ({ key: 0.85 - 0.25 * a, hemi: 0.32, env: 0.28, bloom: 0.55 + 0.25 * a, ...c });
const lookAt = (from, to) => Math.atan2(to[0] - from[0], to[1] - from[1]);

// ───────── 콜드 오픈: 뇌 관제실, 밤 ─────────
const K01 = cut({ set: 'brain', cast: [], lines: [['co_n1', 1.1]], tail: 0.3,
  ov: [['cap', 0.2, 3.6, '밤 11:40'], ['q', 2.3, 99, '오른쪽 윗배가 쥐어짜듯 아파요.\n체한 거니까… 참으면 될까?']], sfx: [['alarm', 0.9]],
  apply(T, { SETS }) { const P = SETS.brain.P; P.setMonitor(T < 1.0 ? 'eat' : 'clutch', T, { clutchAt: 1.1 }); const a = P.setAlarm(T > 0.9 ? 1 : 0, T);
    const k = ease(clamp(T / 4)); return night({ cam: { pos: [0, 1.7, lerp(0.2, 1.4, k)], target: [0, 1.7, -2.95], fov: lerp(24, 30, k) } }, a); } });

const K02 = cut({ set: 'brain', cast: ['gut', 'liver', 'brain'], lines: [['co_g1', 0.55]], tail: 0.25, ov: [['name', 0.6, 2.2, '장 · 소화2팀 겸 총무']],
  apply(T, { SETS, R }) { const P = SETS.brain.P; P.setMonitor('clutch', T + 4); const a = P.setAlarm(1, T + 4); P.setBet({});
    const w = walker(T, [[0, -2.35, 1.4], [0.7, HOME.gut[0], HOME.gut[1]]]);   // 미끄러지듯 들어옴
    act(R.gut, 'gut', T, K02.lines, { x: w.x, z: w.z, turn: T < 0.75 ? (w.dir ?? 0.8) : lerp(0.9, HOME.gut[2], smooth(0.7, 1.0, T)), jump: w.jump, footL: w.footL, footR: w.footR, mood: 'smug', look: [0.3, 0], hand: 'L' });
    act(R.liver, 'liver', T, null, { x: HOME.liver[0], z: HOME.liver[1], turn: -0.5, mood: 'worry', look: [-1, 0] });
    act(R.brain, 'brain', T, null, { x: HOME.brain[0], z: HOME.brain[1], turn: HOME.brain[2], mood: 'worry', look: [-0.6, 0] });
    return night({ cam: { pos: [-1.45, 1.15, 3.6], target: [-1.2, 0.72, 0.9], fov: 38 } }, a); } });

const K03 = cut({ set: 'brain', cast: ['gut', 'liver', 'brain'], lines: [['co_l1', 0.35]], tail: 0.25, ov: [['name', 0.5, 2.2, '간 · 해독팀 과장']], sfx: [['sigh', 0.1]],
  apply(T, { SETS, R }) { const P = SETS.brain.P; P.setMonitor('clutch', T + 7); const a = P.setAlarm(1, T + 7); P.setBet({});
    act(R.gut, 'gut', T, null, { x: HOME.gut[0], z: HOME.gut[1], turn: 0.6, mood: 'smug', look: [1, 0] });
    const sigh = Math.exp(-(((T - 0.2) / 0.25) ** 2));
    act(R.liver, 'liver', T, K03.lines, { x: HOME.liver[0], z: HOME.liver[1], turn: lerp(-0.2, -0.55, smooth(0.6, 1.1, T)), mood: T < 0.5 ? 'tired' : 'serious', look: [-0.8, 0], sq: 1 - 0.06 * sigh, lean: 0.06 * sigh, armR: 1.75, elbowR: -0.9, hand: 'L' });
    R.liver.prop('papers');
    act(R.brain, 'brain', T, null, { x: HOME.brain[0], z: HOME.brain[1], turn: HOME.brain[2], mood: 'worry', look: [-0.6, 0] });
    return night({ cam: { pos: [-0.25, 1.12, 3.5], target: [-0.35, 0.74, 0.95], fov: 36 } }, a); } });

const K04 = cut({ set: 'brain', cast: ['gut', 'liver', 'brain'], lines: [['co_b1', 0.3]], tail: 0.5, ov: [['name', 0.4, 2.4, '뇌 · 기획팀장']], sfx: [['marker', 0.4]],
  apply(T, { SETS, R }) { const P = SETS.brain.P; P.setMonitor('clutch', T + 10); const a = P.setAlarm(1, T + 10);
    const wr = clamp((T - 0.3) / 2.0); P.setBet({ left: wr > 0.6 ? ['장'] : [], right: wr > 0.9 ? ['간'] : [] });
    act(R.gut, 'gut', T, null, { x: HOME.gut[0], z: HOME.gut[1], turn: 0.6, mood: 'happy', look: [1, 0] });
    act(R.liver, 'liver', T, null, { x: HOME.liver[0], z: HOME.liver[1], turn: 0.3, mood: 'tired', look: [1, -0.2] });
    const scrib = T > 0.4 && T < 2.4 ? Math.sin(T * 16) : 0;
    act(R.brain, 'brain', T, K04.lines, { x: HOME.brain[0], z: HOME.brain[1], turn: lerp(HOME.brain[2], 1.5, smooth(0.1, 0.4, T)) - 1.5 * smooth(2.4, 2.8, T), mood: T < 2.5 ? 'sparkle' : 'proud', look: [0.6, 0], armR: 1.6 + 0.12 * scrib, elbowR: -0.5, gest: 0.4, hand: 'L' });
    return night({ cam: { pos: [-0.3, 1.3, 4.0], target: [0.85, 1.0, 0.7], fov: 42 } }, a); } });

const K05 = cut({ set: 'brain', cast: ['gut', 'liver', 'brain'], dur: 2.4, ov: [['title', 0.0, 2.4]], sfx: [['title', 0.0]],
  apply(T, { SETS, R }) { const P = SETS.brain.P; P.setMonitor('clutch', T + 13); const a = P.setAlarm(1, T + 13); P.setBet({ left: ['장'], right: ['간'] });
    act(R.gut, 'gut', T, null, { x: HOME.gut[0], z: HOME.gut[1], turn: 0.7, mood: 'smug' });
    act(R.liver, 'liver', T, null, { x: HOME.liver[0], z: HOME.liver[1], turn: 0, mood: 'serious' });
    act(R.brain, 'brain', T, null, { x: HOME.brain[0], z: HOME.brain[1], turn: -0.3, mood: 'happy' });
    return night({ cam: { pos: [0, 1.6, lerp(4.9, 4.5, T / 2.4)], target: [0, 1.15, -1.0], fov: 50 } }, a); } });

// ───────── 1막: 편 가르기 ─────────
const GUT0 = [-0.35, 0.05];
const K10 = cut({ set: 'gut', cast: ['gut'], lines: [['a1_g1', 0.3]], tail: 0.3,
  apply(T, { SETS, R }) { const P = SETS.gut.P; P.greasy(true);
    act(R.gut, 'gut', T, K10.lines, { x: GUT0[0], z: GUT0[1], turn: 0.25, mood: 'smug', look: [0.2, 0.2], armL: 1.9 + 0.15 * Math.sin(T * 3), elbowL: -0.3, hand: 'R' });
    return { cam: { pos: [0.6, 1.15, 3.3], target: [-0.3, 0.55, 0.2], fov: 40 }, key: 1.5 }; } });

const K11 = cut({ set: 'gut', cast: ['gut'], lines: [['a1_g2', 0.25]], tail: 0.35, sfx: [['pat', 0.35], ['pat', 0.75], ['pat', 1.15]],
  apply(T, { SETS, R }) { const P = SETS.gut.P; P.greasy(true);
    const pat = T < 1.5 ? Math.max(0, Math.sin(T * Math.PI * 2.5)) : 0;
    act(R.gut, 'gut', T, K11.lines, { x: GUT0[0], z: GUT0[1], turn: 0.05, mood: 'happy_closed', armR: 1.15 - 0.25 * pat, elbowR: -1.1, armL: 0.95 - 0.25 * pat, elbowL: -1.1, gest: 0, sq: 1 + 0.02 * pat });
    return { cam: { pos: [-0.2, 0.95, 2.2], target: [-0.35, 0.55, 0.05], fov: 38 }, key: 1.5 }; } });

const K12 = cut({ set: 'corridor', cast: ['heart'], lines: [['a1_h1', 1.25]], tail: 0.3, ov: [['name', 1.3, 2.3, '심장 · 영업1팀 에이스'], ['tag', 2.6, 1.3, '참는다 +1']], sfx: [['run', 0.0], ['skid', 0.95]],
  apply(T, { SETS, R }) { const S = SETS.corridor; S.setDoor('gut', 0, 0); S.setDoor('liver', 0, 0); S.setDoor('brain', 0, 0);
    const w = walker(T, [[0, -4.2, 0.1], [1.0, 0.2, 0.1]], 0.32);
    const H = R.heart; H.hold('none');
    const stop = smooth(0.95, 1.2, T);
    act(H, 'heart', T, K12.lines, { x: w.x, z: w.z, turn: lerp(Math.PI / 2, 0.15, stop), jump: w.jump * 1.6, footL: w.footL * 1.4, footR: w.footR * 1.4, footLz: w.footLz, footRz: w.footRz,
      lean: 0.18 * (1 - stop) - 0.1 * Math.exp(-(((T - 1.05) / 0.12) ** 2)), armL: lerp(0.4 + 0.5 * Math.sin(T * 18), 2.3, smooth(1.3, 1.5, T)), armR: lerp(0.4 - 0.5 * Math.sin(T * 18), 0.8, stop), mood: T < 1.0 ? 'happy' : 'sparkle', hand: 'R' });
    return { cam: { pos: [lerp(-2.4, -0.9, smooth(0, 1.1, T)), 1.0, 1.9], target: [lerp(-2.6, 0.2, smooth(0, 1.1, T)), 0.65, 0], fov: 46 } }; } });

const LIV0 = [0.0, -1.05];
const K13 = cut({ set: 'liver', cast: ['liver'], lines: [['a1_l1', 0.3]], tail: 0.3, ov: [['def', 1.2, 2.8, '담낭: 간이 만든 담즙을 모아 두는 주머니']], sfx: [['tap', 2.6], ['tap', 2.9]],
  apply(T, { SETS, R }) { const P = SETS.liver.P; P.setGauge(0.3 + 0.03 * Math.sin(T * 9) * smooth(2.5, 2.7, T) * (1 - smooth(3.2, 3.5, T)));
    const tapk = T > 2.5 && T < 3.2 ? Math.max(0, Math.sin((T - 2.5) * Math.PI / 0.3)) : 0;
    act(R.liver, 'liver', T, K13.lines, { x: LIV0[0], z: LIV0[1], turn: lerp(0.25, 0.95, smooth(2.0, 2.4, T)), mood: 'serious', look: T < 2 ? [0, 0] : [1, -0.2], armL: lerp(0.73, 1.6, smooth(2.2, 2.5, T)) + 0.15 * tapk, elbowL: -0.4, hand: 'R' });
    return { cam: { pos: [1.75, 1.35, 0.95], target: [0.25, 1.0, -1.45], fov: 46 } }; } });

const K14 = cut({ set: 'liver', cast: [], lines: [['a1_l2', 0.85]], tail: 0.35, sfx: [['clank', 0.05], ['clank', 0.4], ['clank', 0.75]],
  apply(T, { SETS, R }) { const P = SETS.liver.P; P.setGauge(0.45); P.setStone(1); P.setValve(T < 1.2 ? 1 : 0.4, T);
    act(R.liver, 'liver', T, K14.lines, { x: -0.3, z: -1.15, turn: 2.2, mood: T < 0.8 ? 'serious' : 'worry', look: [0.3, 0.6], gest: 0.4 });
    return { cam: { pos: [1.35, 0.8, -1.0], target: [0.95, 0.47, -2.2], fov: 50 } }; } });

const K15 = cut({ set: 'gut', cast: ['gut'], lines: [['a1_g3', 0.3]], tail: 0.4, post: 'interview', ov: [['tag', 0.2, 99, '인터뷰'], ['name', 0.5, 2.5, '장 · 무시파']],
  apply(T, { SETS, R }) { SETS.gut.P.greasy(true);
    act(R.gut, 'gut', T, K15.lines, { x: 0.3, z: 1.95, turn: 0.15, mood: T < 2 ? 'smug' : 'pity', look: [0.6, 0], hand: 'L' });
    return { cam: { pos: [0.45, 0.82, 3.45], target: [0.3, 0.62, 1.95], fov: 40 }, key: 1.1, env: 0.25 }; } });

// ───────── 2막: 장 방식대로 참아 보기 ─────────
const GL = [0.1, -0.12], GLT = 1.55;   // 레버 앞 자리
const K20 = cut({ set: 'gut', cast: ['gut'], lines: [['a2_g1', 0.2]], tail: 1.0, ov: [['cap', 0.1, 2.4, '통증 10분째']], sfx: [['lever', 1.05], ['fart', 1.25]],
  apply(T, { SETS, R }) { const P = SETS.gut.P; P.greasy(true);
    const pull = smooth(0.85, 1.1, T); P.setLever(0, pull); P.setPuff((T - 1.2) / 1.1);
    act(R.gut, 'gut', T, K20.lines, { x: GL[0], z: GL[1], turn: 0.45, mood: T < 1.3 ? 'smug' : 'happy_closed', armR: lerp(1.6, 2.6, smooth(0.5, 0.8, T)) - 0.5 * pull, elbowR: -0.3, armL: 1.3, gest: 0.3, hand: 'L', lean: 0.08 * pull });
    return { cam: { pos: [-0.1, 1.2, 2.3], target: [0.7, 0.7, -0.3], fov: 46 }, key: 1.5 }; } });

const K21 = cut({ set: 'liver', cast: [], dur: 1.75, sfx: [['tick', 0.7]],
  apply(T, { SETS }) { const P = SETS.liver.P; P.setGauge(0.55 + 0.01 * Math.sin(T * 30) * Math.exp(-(((T - 0.7) / 0.1) ** 2)));
    const G = P.GA; return { cam: { pos: [G.x - 0.3, G.y + 0.05, G.z + 1.05], target: [G.x, G.y, G.z], fov: 40 }, bloom: 0.12, key: 1.2 }; } });

const K22 = cut({ set: 'gut', cast: ['gut'], lines: [['a2_g2', 0.15]], tail: 0.6, sfx: [['lever', 0.75], ['lever', 1.75]],
  apply(T, { SETS, R }) { const P = SETS.gut.P; P.greasy(true); P.setLever(0, 1);
    const p1 = smooth(0.55, 0.8, T), p2 = smooth(1.55, 1.8, T); P.setLever(1, p1); P.setLever(2, p2);
    act(R.gut, 'gut', T, K22.lines, { x: GL[0] + 0.05, z: GL[1], turn: 0.45 - 0.05 * Math.sin(T * 6), mood: T < 1.4 ? 'worry' : 'panic', armR: 2.3 - 0.45 * (p1 - p2 * 0.5) + 0.2 * Math.sin(T * 9), armL: 1.6 + 0.6 * p2, elbowR: -0.3, gest: 0.2, lean: 0.06 });
    return { cam: { pos: [-0.25, 1.05, 2.2], target: [0.65, 0.72, -0.35], fov: 44 }, key: 1.5 }; } });

const K23 = cut({ set: 'gut', cast: ['gut'], lines: [['a2_g3', 0.7]], tail: 0.45,
  apply(T, { SETS, R }) { const P = SETS.gut.P; P.greasy(true); [0, 1, 2].forEach(i => P.setLever(i, 1));
    act(R.gut, 'gut', T, K23.lines, { x: GL[0] + 0.05, z: GL[1], turn: lerp(0.45, -0.25, smooth(0.3, 0.6, T)), mood: 'shock', look: [-0.6, 0], armR: 1.9, armL: 1.3, gest: 0.1, sq: 1 - 0.03 * smooth(0, 0.3, T) });
    return { cam: { pos: [-0.35, 0.88, 2.0], target: [0.28, 0.6, -0.2], fov: lerp(40, 32, ease(clamp(T / 2))) }, key: 1.4 }; } });

const K24 = cut({ set: 'pump', cast: ['heart'], lines: [['a2_h1', 0.25]], tail: 0.9, sfx: [['thump', 0.55], ['thump', 0.95], ['thump', 1.35], ['thump', 1.75], ['thump', 2.15], ['thump', 2.55]],
  apply(T, { SETS, R }) { const S = SETS.pump; const lands = [0.55, 0.95, 1.35, 1.75, 2.15, 2.55]; const b = beat(T, lands, { air: 0.22, h: 0.1 });
    S.setPress(b.press); S.setBeat(Math.max(0, 1 - b.since * 3)); S.setECG(5, lands.filter(l => l <= T).map(l => l * 0.6 + 0.4));
    const H = R.heart; H.hold('none');
    act(H, 'heart', T, K24.lines, { x: BUTTON.x, z: BUTTON.z, jump: STAND(b.press) + b.air, sq: b.sq, turn: 0.2, mood: T < 0.5 ? 'awake' : 'sparkle', armL: 1.9 + 0.3 * Math.sin(T * 15), armR: 1.9 - 0.3 * Math.sin(T * 15), hand: 'none' });
    return { cam: { pos: [-1.1, 1.2, 2.6], target: [0.1, 1.1, -0.4], fov: 42 }, key: 1.0 }; } });

const K25 = cut({ set: 'brain', cast: [], lines: [['a2_n1', 0.3]], tail: 0.4, ov: [['cap', 0.2, 3.3, '통증 40분째']],
  apply(T, { SETS }) { const P = SETS.brain.P; P.setMonitor('fidget', T, { stamp: 'AM 0:20' }); const a = P.setAlarm(1, T);
    return night({ cam: { pos: [0.1, 1.7, 1.0], target: [0, 1.7, -2.95], fov: 28 } }, a); } });

const K26 = cut({ set: 'brain', cast: ['brain', 'gut', 'liver'], lines: [['a2_b1', 0.25]], tail: 0.4, sfx: [['beep', 0.1], ['beep', 0.5]],
  apply(T, { SETS, R }) { const P = SETS.brain.P; P.setMonitor('shoulder', T); const a = P.setAlarm(1, T); P.setBet({ left: ['장', '심장'], right: ['간'] });
    act(R.brain, 'brain', T, K26.lines, { x: 0.35, z: 1.05, turn: lerp(Math.PI, 0.3, smooth(0.05, 0.35, T)), mood: 'panic', look: [0, 0], armL: 1.8, armR: 1.8, gest: 0.6, hand: 'both' });
    act(R.gut, 'gut', T, null, { x: -1.0, z: 1.15, turn: Math.PI - 0.3, mood: 'worry' });
    act(R.liver, 'liver', T, null, { x: 1.45, z: 1.75, turn: Math.PI + 0.4, mood: 'serious' });
    return night({ cam: { pos: [0.3, 1.25, 4.0], target: [0.1, 1.3, -1.5], fov: 44 } }, a); } });

const K27 = cut({ set: 'brain', cast: ['brain'], lines: [['a2_b2', 0.2]], tail: 0.6, ov: [['cap', 1.0, 1.6, '밤 10:10']], sfx: [['rewind', 0.6]],
  apply(T, { SETS, R }) { const P = SETS.brain.P; P.setMonitor(T < 0.6 ? 'fidget' : 'rewind', T, { stamp: T < 0.6 ? 'AM 0:20' : 'PM 10:10' }); const a = P.setAlarm(0.5, T);
    act(R.brain, 'brain', T, K27.lines, { x: 0.15, z: 0.95, turn: Math.PI - 0.15, mood: 'serious', armR: 1.5, elbowR: -0.6, fwdR: -0.4, gest: 0.2 });
    return night({ cam: { pos: [1.2, 1.35, 2.7], target: [-0.1, 1.5, -2.0], fov: 40 } }, a); } });

const K28 = cut({ set: 'liver', cast: [], dur: 4.6, post: 'flashback', ov: [['cap', 0.1, 4.4, '밤 10:10 · 되감기']], sfx: [['squish', 0.5], ['roll', 1.9], ['clack', 3.25]],
  apply(T, { SETS }) { const P = SETS.liver.P; const sq = Math.max(0, Math.sin(clamp((T - 0.4) / 1.2) * Math.PI));
    P.setHot(sq, T, '#ffd24a'); P.setSqueeze(sq);
    P.setStone(ease(clamp((T - 1.8) / 1.45)), T); P.setValve(T > 3.25 ? Math.exp(-(T - 3.25) * 6) : 0, T); P.setGauge(lerp(0.3, 0.62, smooth(3.25, 3.6, T)));
    return { cam: { pos: [lerp(1.6, 1.45, T / 4.6), 0.8, -0.85], target: [0.85, 0.5, -2.2], fov: 46 }, key: 1.4 }; } });

const K29 = cut({ set: 'liver', cast: ['liver'], lines: [['a2_n2', 0.8]], tail: 0.5, ov: [['cap', 0.3, 2.4, '통증 3시간째']], sfx: [['hiss', 0.1]],
  apply(T, { SETS, R }) { const P = SETS.liver.P; P.setHot(1, T); P.setGauge(0.93 + 0.02 * Math.sin(T * 20)); P.setStone(1); P.setValve(0.3, T);
    act(R.liver, 'liver', T, null, { x: -0.55, z: -0.6, turn: 0.6, mood: 'panic', look: [1, -0.4], sq: 0.97 });
    return { cam: { pos: [0.6, 1.3, 1.7], target: [-0.1, 1.05, -1.6], fov: 50 }, key: 1.2 }; } });

const K2A = cut({ set: 'gut', cast: ['gut'], lines: [['a2_g4', 0.2]], tail: 0.4,
  apply(T, { SETS, R }) { SETS.gut.P.greasy(true); [0, 1, 2].forEach(i => SETS.gut.P.setLever(i, 1));
    act(R.gut, 'gut', T, K2A.lines, { x: GL[0] + 0.05, z: GL[1], turn: -0.15, mood: 'panic', look: [-0.3, 0], armL: 1.0 + 0.1 * Math.sin(T * 13), armR: 2.2, elbowR: -0.5, gest: 0.5, tiltZ: 0.03 * Math.sin(T * 11) });
    return { cam: { pos: [-0.15, 0.86, 1.95], target: [0.3, 0.6, -0.2], fov: 36 }, key: 1.4 }; } });

const K2B = cut({ set: 'corridor', cast: ['liver'], lines: [['a2_l1', 1.1]], tail: 0.4, sfx: [['run', 0.0]],
  apply(T, { SETS, R }) { const S = SETS.corridor; S.setDoor('liver', 1, 1); S.setDoor('gut', 0, 0); S.setDoor('brain', 0, 0);
    const w = walker(T, [[0, -1.0, -0.55], [0.6, -0.6, 0.05], [2.9, 2.0, 0.05]], 0.3); R.liver.prop('papers');
    act(R.liver, 'liver', T, K2B.lines, { x: w.x, z: w.z, turn: w.dir ?? Math.PI / 2, jump: w.jump * 1.4, footL: w.footL, footR: w.footR, footLz: w.footLz, footRz: w.footRz, lean: 0.12, mood: 'serious', look: [0, 0], armR: 1.75, elbowR: -0.9, armL: 0.6 + 0.4 * Math.sin(T * 14), gest: 0 });
    return { cam: { pos: [2.9, 0.95, 1.55], target: [w.x, 0.62, w.z], fov: 46 } }; } });

// ───────── 3막: 판정 ─────────
const BJ = [0.5, 1.05];   // 판정할 때 뇌 자리
const K30 = cut({ set: 'brain', cast: ['brain'], lines: [['a3_b1', 1.75]], tail: 0.35, sfx: [['whoosh', 0.75], ['thunk', 1.0]],
  apply(T, { SETS, R }) { const P = SETS.brain.P; P.setMonitor('fidget', T + 20, { stamp: 'AM 2:00' }); const a = P.setAlarm(0.6, T);
    P.setCapsule((T - 0.75) / 0.25, T < 1.6); P.paper.visible = T >= 1.6;
    const reach = smooth(1.1, 1.5, T) * (1 - smooth(1.55, 1.8, T));
    act(R.brain, 'brain', T, K30.lines, { x: -0.45, z: 0.8, turn: lerp(0.4, -1.4, smooth(0.9, 1.15, T)) + 1.3 * smooth(1.6, 1.9, T), mood: T < 1 ? 'tired' : T < 1.7 ? 'awake' : 'serious', look: [-0.5, 0.3], armR: lerp(0.69, 1.7, reach) + 0.9 * smooth(1.6, 1.8, T), elbowR: -0.8 * smooth(1.6, 1.8, T), gest: 0.2 });
    return night({ cam: { pos: [0.45, 1.15, 3.1], target: [-0.8, 0.85, 0.45], fov: 44 } }, a); } });

const K31 = cut({ set: 'brain', cast: ['brain'], lines: [['a3_b2', 0.3]], tail: 1.2, ov: [['ans', 0.9, 3.4]], sfx: [['ding', 0.9]],
  apply(T, { SETS, R }) { const P = SETS.brain.P; P.setMonitor('fidget', T + 23, { stamp: 'AM 2:00' }); const a = P.setAlarm(0.6, T); P.paper.visible = true;
    act(R.brain, 'brain', T, K31.lines, { x: BJ[0], z: BJ[1], turn: 0.1, mood: 'serious', look: [0, 0], armR: 1.6, elbowR: -0.8, hand: 'L' });
    return night({ cam: camB(BJ[0], BJ[1]) }, a); } });

const BOARD_ROWS = [['자리: 명치·오른쪽 갈비뼈 밑', '#2B2D5B'], ['시간: 보통 1~5시간', '#d04050'], ['퍼짐: 오른쪽 어깨뼈·옆구리', '#5a4ad0']];
const K32 = cut({ set: 'brain', cast: ['brain'], lines: [['a3_b3', 0.2]], tail: 1.1, ov: [['chip', 0.4, 4.6, '명치·오른쪽 갈비뼈 바로 아래\n보통 1~5시간 · 오른쪽 어깨뼈·옆구리로 퍼짐', 'NHS 웨일스 111 담석 안내']], sfx: [['marker', 0.3], ['marker', 1.6]],
  apply(T, { SETS, R }) { const P = SETS.brain.P; const a = P.setAlarm(0.4, T); P.paper.visible = false;
    P.setBet({ mode: 'table', title: '담석 통증 구별표', rows: BOARD_ROWS, n: T < 0.3 ? 0 : T < 1.6 ? 1 : T < 3.0 ? 2 : 3 });
    act(R.brain, 'brain', T, K32.lines, { x: -0.45, z: 0.9, turn: lerp(1.3, 0.55, smooth(0.0, 0.3, T)), mood: 'serious', look: [0.8, -0.2], armR: 2.0 + 0.1 * Math.sin(T * 5), elbowR: -0.3, hand: 'L' });
    return night({ cam: { pos: [-0.9, 1.15, 3.25], target: [0.6, 1.0, 0.6], fov: 46 } }, a); } });

const K33 = cut({ set: 'brain', cast: [], lines: [['a3_b4', 0.2]], tail: 0.8, ov: [['chip', 0.4, 3.2, '화장실 다녀와도, 방귀·구토 뒤에도 그대로', 'NHS 웨일스 111']], sfx: [['marker', 0.5], ['marker', 1.1], ['marker', 1.7]],
  apply(T, { SETS }) { const P = SETS.brain.P; P.setAlarm(0.3, T); P.setBet({ mode: 'levers', title: '이걸로는 안 풀려요', x: clamp((T - 0.4) / 1.8) });
    return night({ cam: CAM.board }); } });

const K34 = cut({ set: 'brain', cast: [], dur: 7.2, ov: [['bullet', 0.3, 6.8]], sfx: [['clack', 1.0], ['clack', 3.4]],
  apply(T, { SETS }) { const P = SETS.brain.P; P.setMonitor('diagram', T); P.setAlarm(0.3, T);
    return night({ cam: { pos: [0.05, 1.7, lerp(1.2, 0.9, T / 7.2)], target: [0, 1.7, -2.95], fov: 30 } }); } });

const K35 = cut({ set: 'brain', cast: ['brain'], lines: [['a3_b5', 0.2]], tail: 1.9, ov: [['cards', 0.3, 3.8, 'NIDDK 담석 증상·원인']], sfx: [['card', 0.35], ['card', 0.75], ['card', 1.15]],
  apply(T, { SETS, R }) { const P = SETS.brain.P; P.setMonitor('fidget', T + 30, { stamp: 'AM 2:01' }); const a = P.setAlarm(0.7, T);
    act(R.brain, 'brain', T, K35.lines, { x: BJ[0], z: BJ[1], turn: 0.15, mood: 'angry', look: [0, 0], armL: 2.4, elbowL: -0.2, hand: 'R' });
    return night({ cam: camB(BJ[0], BJ[1], -0.5, 2.6, 38) }, a); } });

const K36 = cut({ set: 'brain', cast: ['brain'], lines: [['a3_b6', 0.2]], tail: 1.0, ov: [['chip', 0.4, 3.0, '갑자기 극심한 통증 → 119\n응급실은 직접 운전 X', 'NHS 담석 안내']], sfx: [['siren', 0.0]],
  apply(T, { SETS, R }) { const P = SETS.brain.P; P.setMonitor('ambulance', T); const a = P.setAlarm(1, T);
    act(R.brain, 'brain', T, K36.lines, { x: 0.35, z: 0.95, turn: 0.35, mood: 'panic', look: [-0.4, 0], armL: 1.8, armR: 1.8, gest: 0.6, hand: 'both' });
    return night({ cam: { pos: [-0.75, 1.3, 3.6], target: [0.1, 1.3, -1.2], fov: 44 }, bloom: 0.3 }, a); } });

const K37 = cut({ set: 'brain', cast: ['gut', 'brain', 'liver'], lines: [['a3_g1', 0.75]], tail: 0.45, sfx: [['stamp', 0.1], ['flop', 0.55]],
  apply(T, { SETS, R }) { const P = SETS.brain.P; P.setAlarm(0.3, T); P.setBet({ left: ['장', '심장'], right: ['간'], win: T > 0.1 });
    const flop = smooth(0.4, 0.7, T);
    act(R.gut, 'gut', T, K37.lines, { x: -0.35, z: 1.05, turn: 0.2, mood: flop > 0.5 ? 'dizzy' : 'shock', sq: 1 - 0.12 * flop, jump: 0, lean: 0.12 * flop, armL: lerp(0.76, 0.4, flop), armR: lerp(2.1, 2.5, flop), gest: 0.2 });
    act(R.brain, 'brain', T, null, { x: 0.85, z: 1.55, turn: -0.5, mood: 'pity', look: [-1, 0.2] });
    act(R.liver, 'liver', T, null, { x: -1.8, z: 1.45, turn: 0.6, mood: 'pity', look: [1, 0] });
    return night({ cam: { pos: [0.0, 1.35, 4.7], target: [-0.1, 0.95, 0.6], fov: 44 } }); } });

const K38 = cut({ set: 'pump', cast: ['heart'], lines: [['a3_h1', 0.35]], tail: 0.4, post: 'call', ov: [['tag', 0.0, 99, '화상 연결 · 펌프 공장']],
  apply(T, { SETS, R }) { const S = SETS.pump; S.setPress(0); S.setBeat(0.4); S.setECG(3, [0.9, 1.65, 2.4]); R.heart.hold('none');
    act(R.heart, 'heart', T, K38.lines, { x: BUTTON.x, z: BUTTON.z, jump: STAND(0), turn: 0, mood: 'worry', look: [0, 0.1], armL: 1.2, elbowL: -1.0, hand: 'R' });
    return { cam: { pos: [0.05, 1.3, 2.15], target: [0, 1.0, 0], fov: 38 }, key: 1.0 }; } });

const K39 = cut({ set: 'brain', cast: ['brain'], lines: [['a3_b7', 0.3]], tail: 0.6, ov: [['chip', 0.6, 3.2, '심장마비와 비슷할 수 있음\n가슴까지 조이면 헷갈리지 말고 119', 'NIDDK']],
  apply(T, { SETS, R }) { const P = SETS.brain.P; P.setMonitor('logo', T); const a = P.setAlarm(0.3, T);
    const nod = Math.max(0, Math.sin(clamp((T - 0.2) / 0.6) * Math.PI * 2));
    act(R.brain, 'brain', T, K39.lines, { x: BJ[0], z: BJ[1], turn: -0.25, mood: 'serious', look: [0, 0.2], lean: 0.08 * nod, hand: 'R' });
    return night({ cam: camB(BJ[0], BJ[1], 0.5, 2.5, 36) }, a); } });

const K3A = cut({ set: 'brain', cast: ['brain'], lines: [['a3_b8', 0.2]], tail: 0.6, ov: [['chip', 0.5, 3.0, '한 번 발작 → 다음 발작 가능성 큼\n멎어도 진료 예약', 'NIDDK']],
  apply(T, { SETS, R }) { const P = SETS.brain.P; P.setMonitor('gauge', T); P.setAlarm(0, T);
    act(R.brain, 'brain', T, K3A.lines, { x: -0.6, z: 0.9, turn: lerp(-2.5, -2.75, smooth(0, 1, T)), mood: 'serious', look: [0, -0.3], armL: 2.3, elbowL: -0.1, fwdL: -0.3, gest: 0.3, hand: 'R' });
    return night({ cam: { pos: [1.0, 1.5, 3.4], target: [-0.15, 1.45, -1.6], fov: 44 } }); } });

const K3B = cut({ set: 'brain', cast: ['brain'], lines: [['a3_b9', 0.25]], tail: 0.5, post: 'interview', ov: [['tag', 0.0, 99, '인터뷰'], ['chip', 0.5, 2.6, '증상 없는 담석 = 대개 치료 불필요', 'NIDDK']],
  apply(T, { SETS, R }) { const P = SETS.brain.P; P.setMonitor('logo', T); P.setAlarm(0, T);
    act(R.brain, 'brain', T, K3B.lines, { x: -0.2, z: 1.6, turn: 0.35, mood: 'relieved', look: [0.5, 0], hand: 'L' });
    return night({ cam: { pos: [0.05, 0.88, 3.4], target: [-0.2, 0.66, 1.6], fov: 40 }, key: 0.7 }); } });

// ───────── 4막: 실행과 벌칙 ─────────
const K40 = cut({ set: 'brain', cast: [], lines: [['a4_n1', 0.5]], tail: 0.5, sfx: [['relief', 1.6]],
  apply(T, { SETS }) { const P = SETS.brain.P; P.setMonitor('hospital', T); const off = smooth(1.5, 2.2, T); P.setAlarm(1 - off, T);
    const k = ease(clamp(T / 3.6)); return { cam: { pos: [0, 1.7, lerp(1.0, 3.2, k)], target: [0, lerp(1.7, 1.5, k), -2.95], fov: lerp(28, 40, k) }, key: lerp(0.8, 1.6, off), hemi: lerp(0.3, 0.45, off), env: 0.35 }; } });

const K41 = cut({ set: 'liver', cast: [], dur: 1.5, sfx: [['chime', 0.2]],
  apply(T, { SETS }) { const P = SETS.liver.P; P.setGauge(lerp(0.75, 0.25, smooth(0.0, 0.9, T))); P.setHot(1 - smooth(0, 0.9, T), T); P.setStone(0);
    const G = P.GA; return { cam: { pos: [G.x - 0.35, G.y + 0.1, G.z + 1.2], target: [G.x, G.y, G.z], fov: 42 }, bloom: 0.12, key: 1.2 }; } });

const K42 = cut({ set: 'brain', cast: ['gut', 'liver', 'brain'], dur: 6.8, ov: [['summary', 0.2, 6.6]], post: 'dim',
  apply(T, { SETS, R }) { const P = SETS.brain.P; P.setMonitor('logo', T); P.setAlarm(0, T); P.setBet({ left: ['장', '심장'], right: ['간'], win: true });
    act(R.gut, 'gut', T, null, { x: HOME.gut[0], z: HOME.gut[1], turn: 0.7, mood: 'tired' });
    act(R.liver, 'liver', T, null, { x: HOME.liver[0], z: HOME.liver[1], turn: 0, mood: 'relieved' });
    act(R.brain, 'brain', T, null, { x: HOME.brain[0], z: HOME.brain[1], turn: -0.3, mood: 'happy' });
    return { cam: { pos: [0, 1.6, lerp(4.6, 4.3, T / 6.8)], target: [0, 1.15, -1.0], fov: 50 }, key: 1.5, hemi: 0.42 }; } });

const DISH = [0.0, 1.35];   // 그릇 탁자 중심(높이 0.45, 캐릭터는 탁자 뒤)
const GUTW = [-0.28, 0.45], LIVW = [1.0, 0.5];
const K43 = cut({ set: 'liver', cast: ['gut'], lines: [['a4_g1', 0.45]], tail: 0.45, ov: [['tag', 0.2, 2.2, '벌칙: 회식 뒷정리 한 달 — 장']], sfx: [['glove', 0.1]],
  apply(T, { SETS, R }) { const P = SETS.liver.P; P.dish.visible = true; SETS.liver.station.visible = false; shelfOf(SETS.liver).visible = false; R.gut.gloves(true);
    act(R.gut, 'gut', T, K43.lines, { x: GUTW[0], z: GUTW[1], turn: 0, mood: 'cry', look: [0, -0.4], armL: 1.05, armR: 2.4, elbowL: -0.6, elbowR: -0.6, gest: 0.3, sq: 0.97 });
    return { cam: { pos: [-0.2, 1.2, 3.4], target: [-0.35, 0.7, 0.8], fov: 36 }, key: 1.5 }; } });

const K44 = cut({ set: 'liver', cast: ['gut', 'liver'], lines: [['a4_l1', 0.35]], tail: 0.4, sfx: [['sparkle', 0.2]],
  apply(T, { SETS, R }) { const P = SETS.liver.P; P.dish.visible = true; SETS.liver.station.visible = false; shelfOf(SETS.liver).visible = false; R.gut.gloves(true);
    act(R.gut, 'gut', T, null, { x: GUTW[0], z: GUTW[1], turn: 0.2, mood: 'cry', look: [1, 0], armL: 1.05, armR: 2.4, elbowL: -0.6, elbowR: -0.6 });
    act(R.liver, 'liver', T, K44.lines, { x: 1.4, z: 0.55, turn: -0.5, mood: T < 0.4 ? 'awake' : 'sparkle', look: [-0.6, 0], hand: 'L', gest: 0.5 });
    return { cam: { pos: [1.2, 1.0, 2.95], target: [1.35, 0.66, 0.55], fov: 34 }, key: 1.5 }; } });

const K45 = cut({ set: 'liver', cast: ['gut', 'liver'], lines: [['a4_l2', 2.75], ['a4_g2', 4.15]], tail: 0.6, sfx: [['step', 0.3], ['scrub', 3.3]],
  apply(T, { SETS, R }) { const P = SETS.liver.P; P.dish.visible = true; SETS.liver.station.visible = false; shelfOf(SETS.liver).visible = false; R.gut.gloves(true);
    // 간: 문 쪽으로 몇 걸음(0.2~1.4) → 멈춰 돌아봄(1.6) → 돌아와 장 옆(1.9~2.7) → 한숨 "…제가 할게요" → 같이 닦음
    const w = walker(T, [[0.2, 1.4, 0.55], [1.4, 1.0, -0.55], [1.6, 1.0, -0.55], [2.7, LIVW[0], LIVW[1]]], 0.24);
    const back = smooth(1.45, 1.75, T), wash = smooth(2.9, 3.3, T), sc = Math.sin(T * 9) * wash;
    let turn = T < 0.35 ? lerp(-0.5, 3.0, smooth(0, 0.35, T)) : T < 1.45 ? (w.dir ?? 3.0) : T < 1.9 ? lerp(3.0, 0.2, back) : T < 2.75 ? (w.dir ?? 0.2) : lerp(0.0, -0.3, smooth(2.7, 3.0, T));
    act(R.liver, 'liver', T, K45.lines, { x: w.x, z: w.z, turn, jump: w.jump, footL: w.footL, footR: w.footR, footLz: w.footLz, footRz: w.footRz, mood: T < 1.5 ? 'happy_closed' : T < 2.75 ? 'pity' : T < 3.9 ? 'tired' : 'happy_closed', look: [-0.8, 0], armL: 0.73 + 0.08 * sc, armR: lerp(2.03, 1.5, wash) - 0.15 * sc, gest: 0.2, hand: 'R' });
    const gk = talk(K45.lines, 'gut', T).on;
    act(R.gut, 'gut', T, K45.lines, { x: GUTW[0], z: GUTW[1], turn: lerp(0.0, 0.5, smooth(1.5, 1.8, T)) + 0.3 * smooth(3.9, 4.2, T), mood: T < 3.9 ? (T < 1.6 ? 'cry' : 'wow') : 'sparkle', look: [1, 0], armL: 0.76, armR: 2.0 - 0.15 * Math.sin(T * 8) * (1 - gk), elbowL: 0, elbowR: -0.6, gest: 0.5, hand: 'R' });
    return { cam: { pos: [lerp(0.9, 0.1, smooth(2.5, 3.3, T)), 1.2, 3.9], target: [lerp(1.0, 0.05, smooth(1.2, 3.0, T)), 0.7, 0.6], fov: 44 }, key: 1.5 }; } });

const K46 = cut({ set: 'pump', cast: ['heart'], lines: [['a4_h1', 0.3]], tail: 0.35, sfx: [['thump', 1.2], ['thump', 1.6]],
  apply(T, { SETS, R }) { const S = SETS.pump; const lands = [1.2, 1.6, 2.0]; const b = beat(T, lands, { air: 0.22, h: 0.12 });
    S.setPress(b.press); S.setBeat(Math.max(0, 1 - b.since * 3)); S.setECG(3, [0.9, 1.65, 2.4]); R.heart.hold('none');
    act(R.heart, 'heart', T, K46.lines, { x: BUTTON.x, z: BUTTON.z, jump: STAND(b.press) + b.air, sq: b.sq, turn: 0, mood: 'sparkle', look: [0, 0], armL: 2.4, armR: 0.8, hand: 'R' });
    return { cam: { pos: [0.2, 1.3, 2.9], target: [0, 1.05, 0], fov: 42 }, key: 1.0 }; } });

const K47 = cut({ set: 'brain', cast: ['brain'], lines: [['a4_b1', 0.3]], tail: 1.2,
  apply(T, { SETS, R }) { const P = SETS.brain.P; P.setMonitor('logo', T); P.setAlarm(0, T); P.setBet({ left: ['장', '심장'], right: ['간'], win: true, penalty: true });
    act(R.brain, 'brain', T, K47.lines, { x: BJ[0], z: BJ[1], turn: 0.1, mood: T < 2.2 ? 'proud' : 'happy_closed', look: [0, 0], armR: 1.6, elbowR: -0.9, hand: 'L' });
    return { cam: camB(BJ[0], BJ[1], -0.2, 2.6, 38), key: 1.5, hemi: 0.42 }; } });

export const ORDER = ['K01', 'K02', 'K03', 'K04', 'K05', 'K10', 'K11', 'K12', 'K13', 'K14', 'K15',
  'K20', 'K21', 'K22', 'K23', 'K24', 'K25', 'K26', 'K27', 'K28', 'K29', 'K2A', 'K2B',
  'K30', 'K31', 'K32', 'K33', 'K34', 'K35', 'K36', 'K37', 'K38', 'K39', 'K3A', 'K3B',
  'K40', 'K41', 'K42', 'K43', 'K44', 'K45', 'K46', 'K47'];
export const CUTS = { K01, K02, K03, K04, K05, K10, K11, K12, K13, K14, K15, K20, K21, K22, K23, K24, K25, K26, K27, K28, K29, K2A, K2B,
  K30, K31, K32, K33, K34, K35, K36, K37, K38, K39, K3A, K3B, K40, K41, K42, K43, K44, K45, K46, K47 };
// 2D 합성·소리용 시간표(브라우저에서 window.TL로 꺼냄)
export const TL = ORDER.map(id => ({ id, dur: CUTS[id].dur, lines: CUTS[id].lines, ov: CUTS[id].ov || [], sfx: CUTS[id].sfx || [], post: CUTS[id].post || null }));

// 컷마다 소품·상태를 기본으로 되돌림(앞 컷 상태가 새지 않게)
let papersMade = false;
const shelfOf = S => S.SOLID.find(m => m.name === 'shelf').parent;   // 4막 설거지 장면에서 물병 선반을 치움(간 동선)
Object.defineProperty(CUTS, '__reset', { enumerable: false, value: ({ SETS, R }) => {
  const B = SETS.brain.P, L = SETS.liver.P, G = SETS.gut.P;
  SETS.brain.cot.visible = false; B.setAlarm(0, 0); B.setCapsule(-1); B.setMonitor('logo', 0); B.setBet({});
  L.setHot(0, 0); L.setSqueeze(0); SETS.liver.station.visible = true; shelfOf(SETS.liver).visible = true; L.setGauge(0.3); L.setStone(0); L.setValve(0, 0); L.dish.visible = false;
  G.greasy(true); [0, 1, 2].forEach(i => G.setLever(i, 0)); G.setPuff(-1);
  if (!papersMade) { papersMade = true;
    R.brain.hold.add(B.paper); B.paper.position.set(0.05, 0.04, 0.09); B.paper.rotation.set(-0.3, 0.2, 0);
    const pp = new THREE.Mesh(new THREE.BoxGeometry(0.2, 0.05, 0.26), new THREE.MeshStandardMaterial({ color: '#fffaf0', roughness: 0.8 })); pp.name = 'papers';
    R.liver.hold.add(pp); pp.position.set(0.02, 0.0, 0.12); R.liver.meshes.papers = pp; R.liver._pp = pp;
    const ALLOW = ['handR|papers', 'loR|papers'].map(k => k.split('|').sort().join('|')); ALLOW.forEach(k => R.liver.allow.add(k));
    const prop0 = R.liver.prop.bind(R.liver); R.liver.prop = w => { prop0(w); pp.visible = w === 'papers'; };
    const yellow = new THREE.MeshPhysicalMaterial({ color: '#ffd84a', roughness: 0.3, clearcoat: 0.6 });
    R.gut.gloves = on => { ['handL', 'handR'].forEach(n => { const m = R.gut.meshes[n]; if (!m) return; if (!m.userData.m0) m.userData.m0 = m.material; m.material = on ? yellow : m.userData.m0; }); if (R.gut.meshes.flask) R.gut.meshes.flask.visible = !on; };
  }
  B.paper.visible = false; R.liver.prop('none'); R.gut.gloves(false); if (R.gut.meshes.flask) R.gut.meshes.flask.visible = false;   // 이번 편은 플라스크 없이(레버·설거지에 두 손)
} });
