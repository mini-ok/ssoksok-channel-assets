// 〈심장의 휴가〉 컷 정의: { dur, set, cast, apply(t, ctx) → { cam:{pos,target,fov}, key, hemi, env } }
import { BUTTON } from './sets/pumproom.js';
import * as A1 from './act1.js';
import * as A2 from './act2.js';
import * as A3 from './act3.js';
import * as A4 from './act4.js';
const STAND = BUTTON.top + 0.003;   // 버튼 위에 선 발바닥 높이(맞닿기만, 파고들지 않게)

export const CUTS = {
  A1: { dur: A1.DUR, set: 'pump', cast: ['heart'], ownTime: true, apply: A1.apply },
  C5: A2.C5, C6: A2.C6, C7: A2.C7, C8a: A2.C8a, C8: A2.C8,
  C9: A3.C9, C10: A3.C10, C11a: A3.C11a, C11b: A3.C11b, C11c: A3.C11c, C11d: A3.C11d, C11e: A3.C11e, C12: A3.C12, C13: A3.C13,
  C14: A4.C14, C15a: A4.C15a, C15b: A4.C15b, C15c: A4.C15c, C16: A4.C16,
  look_gut: { dur: 1, set: 'gut', cast: ['gut', 'heart'], apply(t, { SETS, R }) {
    R.gut.setFace('happy'); R.gut.pose({ x: -2.2, z: 0.1, turn: 2.6 });
    const so = SETS.gut.setSofa(SETS.gut.SOFA_U); R.heart.setFace('happy_closed' in {} ? 'happy' : 'sleepy'); R.heart.hold('box'); R.heart.pose({ x: so.p.x, z: so.p.z, jump: SETS.gut.BELT_Y + 0.17, turn: so.yaw + Math.PI / 2 });
    return { cam: { pos: [0.6, 1.9, 4.6], target: [0, 0.6, -0.5], fov: 50 } };
  } },
  look_liver: { dur: 1, set: 'liver', cast: ['liver'], apply(t, { R }) {
    R.liver.setFace('tired'); R.liver.pose({ x: -0.05, z: 0.2, turn: -0.4 });
    return { cam: { pos: [0.4, 1.6, 4.3], target: [0, 0.9, -1.0], fov: 52 } };
  } },
  look_brain: { dur: 1, set: 'brain', cast: ['brain'], apply(t, { R }) {
    R.brain.setFace('sleepy'); R.brain.pose({ x: 0.95, z: 0.85, turn: -0.75 + Math.PI });
    return { cam: { pos: [-0.3, 1.5, 4.2], target: [0.1, 1.0, -0.8], fov: 54 } };
  } },
  look_nook: { dur: 1, set: 'nook', cast: [], apply(t, { SETS }) {
    SETS.nook.setHammock(0);
    return { cam: { pos: [0.3, 1.25, 2.9], target: [0, 1.0, -0.6], fov: 55 } };
  } },
  look_corr: { dur: 1, set: 'corridor', cast: ['liver', 'gut'], apply(t, { SETS, R }) {
    SETS.corridor.setDoor('gut', 0.8, 2); SETS.corridor.setDoor('liver', 0, 0); SETS.corridor.setDoor('brain', 0.5, 1.5);
    R.gut.setFace('wow'); R.gut.pose({ x: -4.5, z: -0.65 }); R.liver.setFace('happy_closed'); R.liver.pose({ x: 4.5, z: 0.3, turn: -Math.PI / 2 });
    return { cam: { pos: [-1.2, 1.0, 1.1], target: [1.5, 0.85, -0.6], fov: 62 } };
  } },
  look_wide: { dur: 1, set: 'pump', cast: ['heart'], apply(t, { SETS, R }) {
    const S = SETS.pump; S.setPress(0); S.setBeat(0.6); S.setECG(3, [0.9, 1.65, 2.4]);
    R.heart.setFace('happy'); R.heart.pose({ x: BUTTON.x, z: BUTTON.z, jump: STAND });
    return { cam: { pos: [0.4, 1.5, 3.4], target: [0.0, 1.25, -1.0], fov: 58 }, key: 0.9 };
  } },
  look_med: { dur: 1, set: 'pump', cast: ['heart'], apply(t, { SETS, R }) {
    const S = SETS.pump; S.setPress(0); S.setBeat(1.0); S.setECG(3, [1.2, 1.95, 2.7]);
    R.heart.setFace('tired', [0.9, -0.4]); R.heart.pose({ x: BUTTON.x, z: BUTTON.z, jump: STAND, turn: 0.35 });
    return { cam: { pos: [-1.3, 1.15, 2.4], target: [0.3, 1.15, -0.8], fov: 40 }, key: 0.9 };
  } },
};
