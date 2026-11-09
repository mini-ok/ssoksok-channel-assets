// 시퀀스 1. 불턱의 새벽 (C1–C8)
(() => {
const C = window.CUTS;
// haenyeo sitting around the 불턱 fire; returns [{m, home}] — index 1 is 엄마
function bulteokGroup(F, E, opt = {}) {
  const {THREE, toon} = F, BT = E.bulteok, out = [];
  const angs = opt.angs || [0.35, 1.45, 2.45, 3.35, 4.05];
  angs.forEach((a, i) => {
    const m = makeMom(THREE, toon); F.addChar(m); m.setMask(0);
    const x = BT.x + Math.cos(a) * 1.12, z = BT.z + Math.sin(a) * 1.12, gy = E.landH(x, z);
    const st = lavaRock(F, 0.2, 0x353236, {flat: 0.9}); st.position.set(x, gy + 0.08, z); F.add(st);
    m.group.position.set(x - Math.cos(a) * 0.05, gy + 0.3 - 0.81 + 0.05, z - Math.sin(a) * 0.05);
    m.group.rotation.y = Math.atan2(-(x - BT.x), -(z - BT.z));
    m.group.scale.setScalar(0.94 + 0.04 * (i % 3));
    m.tewak.visible = !!opt.tewak;
    out.push({m, a, i});
  });
  return out;
}
function sitPose(m, extra = {}) { m.pose(Object.assign({pitch: 0.05, yaw: 0, legL: -1.45, legR: -1.4, kneeL: 1.45, kneeR: 1.5, armR: 0.05, armRx: -0.55, armL: 0.05, armLx: -0.6}, extra)); }

// C1 ◆ 7s — ELS crane down: grey horizon after the storm -> black basalt shore -> smoking 불턱
C['1'] = {env: 'coast', mode: 'dawn', dur: 7, setup(F, E) {
  const g = bulteokGroup(F, E);
  F.onFrame = (t) => { E.update(t); g.forEach(({m, i}) => { sitPose(m, {pitch: 0.1 * Math.sin(F.q2(t) * 0.8 + i)}); m.setFace({mouth: 0, eyes: 'open', smile: 0.5}); }); E.focus(4, 0, 4); };
  F.camFn = F.camKeys([[0, F.v3(9, 15, 19), F.v3(1, 13, -150), 40], [1.2, F.v3(9, 15, 19), F.v3(1, 12.5, -150), 40], [7, F.v3(8.6, 2.5, 11.2), F.v3(3.4, 0.9, 2.6), 36]]);
}};

// C2 5s — MS: haenyeo around the fire, silhouettes against the dawn; one tightens her suit, laughter
C['2'] = {env: 'coast', mode: 'dawn', dur: 5, setup(F, E) {
  const g = bulteokGroup(F, E, {angs: [3.05, 3.85, 4.3, 5.55, 6.1]}), BT = E.bulteok;
  F.onFrame = (t) => { E.update(t); E.focus(BT.x, BT.y, BT.z); const tq = F.q2(t);
    g.forEach(({m, i}) => {
      const laugh = (i === 0 || i === 3) && tq > 1.6 && tq < 3.6;
      const bob = laugh ? 0.12 * Math.abs(Math.sin(tq * 9 + i)) : 0.03 * Math.sin(tq + i);
      if (i === 2) sitPose(m, {pitch: -0.1, armR: 0.25 + 0.15 * Math.sin(tq * 5), armRx: -1.2 + 0.25 * Math.sin(tq * 5), armL: 0.2, armLx: -1.1});   // pulls her suit closed
      else sitPose(m, {pitch: -bob, yaw: laugh ? 0.2 * Math.sin(i) : 0});
      m.setFace({mouth: laugh ? (Math.floor(tq * 6 + i) % 2 ? 2 : 1) : 0, eyes: laugh ? 'blink' : 'open', smile: 1});
    }); };
  F.camFn = F.camKeys([[0, F.v3(BT.x - 0.2, BT.y + 1.15, BT.z + 2.7), F.v3(BT.x + 0.1, BT.y + 0.7, BT.z - 0.5), 36],
                       [5, F.v3(BT.x - 0.1, BT.y + 1.1, BT.z + 2.45), F.v3(BT.x + 0.1, BT.y + 0.7, BT.z - 0.5), 35]]);
}};

// C3 4s — MS side: 엄마 (kneeling) settles the 물허벅 strap on 솔이's back. 엄마: "솔아, 물 떠 오라이."
C['3'] = {env: 'coast', mode: 'dawn', dur: 4, setup(F, E) {
  const {THREE, toon} = F, BT = E.bulteok;
  const sx = BT.x - 0.3, sz = BT.z - 2.55, gy = E.landH(sx, sz);
  const sol = makeSol(THREE, toon); F.addChar(sol); sol.group.position.set(sx, gy, sz); sol.group.rotation.y = -Math.PI / 2;
  const mom = makeMom(THREE, toon); F.addChar(mom); mom.setMask(0); mom.tewak.visible = false;
  mom.group.position.set(sx + 0.3, E.landH(sx + 0.3, sz) - 0.56, sz - 0.24); mom.group.rotation.y = -Math.PI / 2 - 0.35; mom.group.rotation.y = -Math.PI / 2;
  const g = bulteokGroup(F, E);
  F.onFrame = (t) => { E.update(t); E.focus(sx, gy, sz); const tq = F.q2(t);
    g.forEach(({m, i}) => sitPose(m, {pitch: 0.05 * Math.sin(tq + i)}));
    const tug = tq < 0.9 ? 0.15 * Math.sin(tq * 10) : 0;
    mom.pose({pitch: tq < 0.9 ? 0.25 : 0.05, yaw: tq < 0.9 ? 0 : -0.15, legL: -0.6, legR: -0.6, kneeL: 2.2, kneeR: 2.2,
              armR: 0.05, armRx: -1.05 + tug, armL: 0.05, armLx: -1.0 - tug});
    mom.setFace({mouth: mouthAt('mom1', 1.0, t), eyes: tq > 3.2 && tq < 3.3 ? 'blink' : 'open', smile: 0.5});
    sol.setHood(0);
    sol.pose({pitch: tq < 1.2 ? 0.1 : 0.2, yaw: tq > 2.8 ? 0.15 : 0, armL: 0.05, armR: 0.05, armLx: 0.05, armRx: 0.05, elbowLx: 0.2, elbowRx: 0.2});
    sol.setFace({mouth: 0, eyes: tq > 2.2 && tq < 2.3 ? 'blink' : 'open', down: 0.6, look: -0.2});
  };
  F.camFn = F.camKeys([[0, F.v3(sx - 1.7, gy + 1.05, sz - 1.55), F.v3(sx + 0.18, gy + 0.92, sz), 32], [4, F.v3(sx - 1.55, gy + 1.05, sz - 1.4), F.v3(sx + 0.18, gy + 0.94, sz), 32]]);
}};

// C4 3s — CU from behind: no answer — 솔이 pulls the yellow hood down over her head
C['4'] = {env: 'coast', mode: 'dawn', dur: 3, setup(F, E) {
  const {THREE, toon} = F, BT = E.bulteok;
  const sx = BT.x - 0.3, sz = BT.z - 2.55, gy = E.landH(sx, sz);
  const sol = makeSol(THREE, toon); F.addChar(sol); sol.group.position.set(sx, gy, sz); sol.group.rotation.y = -Math.PI / 2;
  const g = bulteokGroup(F, E);
  F.onFrame = (t) => { E.update(t); E.focus(sx, gy, sz); const tq = F.q2(t);
    const up = F.ss((tq - 0.5) / 0.9), low = F.ss((tq - 1.6) / 0.4);
    const raise = F.ss((tq - 0.3) / 0.4) * (1 - F.ss((tq - 2.0) / 0.5));
    sol.setHood(up * 1.0 + low * 0.25);
    sol.pose({pitch: 0.15 + 0.15 * low, armL: 0.25 * raise, armR: 0.25 * raise, armLx: -2.5 * raise, armRx: -2.5 * raise, elbowLx: 1.2 * raise, elbowRx: 1.2 * raise});
    sol.setFace({mouth: 0, eyes: 'open', down: 0.8});
    g.forEach(({m, i}) => sitPose(m, {pitch: 0.05 * Math.sin(tq + i)}));
  };
  // behind her right shoulder (she faces -x): camera at +x side, slightly toward -z
  F.camFn = F.camKeys([[0, F.v3(sx + 0.95, gy + 1.22, sz - 0.25), F.v3(sx - 0.2, gy + 1.08, sz + 0.02), 32], [3, F.v3(sx + 0.85, gy + 1.2, sz - 0.22), F.v3(sx - 0.2, gy + 1.06, sz + 0.02), 32]]);
}};

// C5 5s — LS: haenyeo walk into the sea in a line; on a rock, the yellow dot sits with her back to the sea
C['5'] = {env: 'coast', mode: 'dawn', dur: 5, setup(F, E) {
  const {THREE, toon} = F, S = E.seat;
  const sol = makeSol(THREE, toon); F.addChar(sol); sol.group.position.set(S.x, S.y - 0.5, S.z); sol.group.rotation.y = 0.15;   // faces the land
  const hs = [];
  for (let i = 0; i < 5; i++) { const m = makeMom(THREE, toon); F.addChar(m); m.setMask(1); m.group.scale.setScalar(0.95 + 0.03 * (i % 3)); hs.push(m); }
  F.onFrame = (t) => { E.update(t); E.focus(2, 0, 0); const tq = F.q2(t);
    hs.forEach((m, i) => {
      const u = (tq + 1.8 - i * 0.9) * 0.42;                                   // walking along the line
      const x = 6.5 - u * 1.2 + i * 0.1, z = 2.4 - u * 2.6;
      const ground = E.landH(x, z), d = z - E.shoreZ(x);
      const depth = d < -0.5 ? Math.min(1.25, (-0.5 - d) * 0.32) : 0;
      m.group.position.set(x, Math.max(-0.6 - depth, d > -0.5 ? ground : -99), z); m.group.rotation.y = Math.atan2(-1.2, -2.6);
      momWalk(m, tq * 0.9 + i * 0.3, {amp: depth > 0.6 ? 0.5 : 1});
      m.tewak.position.y = depth > 0.4 ? 0.6 + Math.min(0.6, depth) : 0.6;
      m.setFace({mouth: 0, eyes: 'open', smile: 0.3});
    });
    sol.setHood(1.15);
    sol.pose({pitch: 0.35, legL: -1.4, legR: -1.35, kneeL: 1.4, kneeR: 1.45, armL: 0.05, armR: 0.05, armLx: -0.9, armRx: -0.9, elbowLx: 0.7, elbowRx: 0.7});
    sol.setFace({mouth: 0, eyes: 'open', down: 0.8});
  };
  F.camFn = F.camKeys([[0, F.v3(-2.0, 5.5, 13.5), F.v3(1.5, 0.0, -2.5), 36], [5, F.v3(-1.7, 5.3, 13.0), F.v3(1.4, 0.0, -2.5), 36]]);
}};

// C6 5s — MCU on the rock: first 숨비소리 far away; 솔이 purses her lips and tries — "푸―" — nothing
C['6'] = {env: 'coast', mode: 'dawn', dur: 5, setup(F, E) {
  const {THREE, toon} = F, S = E.seat;
  const sol = makeSol(THREE, toon); F.addChar(sol); sol.group.position.set(S.x, S.y - 0.5, S.z); sol.group.rotation.y = 0.15;
  F.onFrame = (t) => { E.update(t); E.focus(S.x, S.y, S.z); const tq = F.q2(t);
    const listen = F.ss((tq - 0.7) / 0.5) * (1 - F.ss((tq - 2.0) / 0.4));
    const blow = tq > 2.7 && tq < 3.7;
    sol.setHood(1.12);
    sol.pose({pitch: blow ? -0.1 : (tq > 3.9 ? 0.3 : 0.12), yaw: 0.45 * listen, roll: 0.08 * listen,
              legL: -1.4, legR: -1.35, kneeL: 1.4, kneeR: 1.45, armL: 0.05, armR: 0.05, armLx: -0.9, armRx: -0.9, elbowLx: 0.7, elbowRx: 0.7});
    sol.setFace({mouth: tq > 2.3 && tq < 3.7 ? 'o' : 0, eyes: tq > 4.3 && tq < 4.4 ? 'blink' : (listen > 0.5 ? 'wide' : 'open'),
                 look: 0.8 * listen, down: tq > 3.9 ? 0.8 : -0.1, smile: tq > 3.9 ? -0.6 : 0});
  };
  F.camFn = F.camKeys([[0, F.v3(S.x + 0.32, S.y + 0.5, S.z + 1.25), F.v3(S.x, S.y + 0.62, S.z), 30], [5, F.v3(S.x + 0.26, S.y + 0.5, S.z + 1.05), F.v3(S.x, S.y + 0.63, S.z), 30]]);
}};

// C7 3s — INSERT: a thin crack in the 물허벅 on her back (a bead of water)
C['7'] = {env: 'coast', mode: 'dawn', dur: 3, setup(F, E) {
  const {THREE, toon} = F, S = E.seat;
  const sol = makeSol(THREE, toon); F.addChar(sol); sol.group.position.set(S.x, S.y - 0.5, S.z); sol.group.rotation.y = 0.15;
  const cg = new THREE.Group(); cg.rotation.y = Math.PI; sol.jar.add(cg);          // the crack sits on the outer side of the jar
  const j = makeJar(F, 1); j.parts.forEach(p => { if (p !== j.body) { cg.add(p); F.reg(p, true); } });
  const drop = new THREE.Mesh(new THREE.SphereGeometry(0.006, 10, 8), new THREE.MeshBasicMaterial({color: 0xcfeef0})); cg.add(drop); F.colorOnly.push(drop);
  F.onFrame = (t) => { E.update(t); E.focus(S.x, S.y, S.z); const tq = F.q2(t);
    sol.setHood(1.12);
    sol.pose({pitch: 0.3, legL: -1.4, legR: -1.35, kneeL: 1.4, kneeR: 1.45, armL: 0.05, armR: 0.05, armLx: -0.9, armRx: -0.9, elbowLx: 0.7, elbowRx: 0.7});
    const u = (tq % 1.5) / 1.5; drop.position.set(Math.sin(0.5) * 0.088, -0.06 - u * u * 0.035, Math.cos(0.5) * 0.088); drop.scale.setScalar(0.6 + u);
  };
  sol.group.updateMatrixWorld(true);
  const jw = new THREE.Vector3(); sol.jar.getWorldPosition(jw);
  const out = new THREE.Vector3(Math.sin(0.5), 0, Math.cos(0.5)).applyAxisAngle(new THREE.Vector3(0, 1, 0), Math.PI).transformDirection(sol.jar.matrixWorld).normalize();
  F.camFn = (t) => { const tq = F.q2(t); const d = 0.4 - 0.08 * F.ss(tq / 3);
    F.cam.position.copy(jw).addScaledVector(out, d); F.cam.position.y += 0.03; F.cam.fov = 30; F.cam.updateProjectionMatrix(); F.cam.lookAt(jw.x, jw.y - 0.025, jw.z); };
}};

C['8'] = {env: 'coast', mode: 'dawn', dur: 3, setup(F, E) {
  const {THREE, toon} = F, S = E.seat;
  const sol = makeSol(THREE, toon); F.addChar(sol);
  F.onFrame = (t) => { E.update(t); const tq = F.q2(t);
    const u = tq / 3, x = S.x - 0.4 * u, z = S.z + 0.6 + u * 6.5;
    E.focus(x, 0, z);
    const bob = solRun(sol, tq * 2.4, {over: {pitch: 0.2, armL: 1.55, armR: 1.55, armLx: -0.5, armRx: -0.5, elbowL: 1.9, elbowR: 1.9, elbowLx: 0.3, elbowRx: 0.3}});
    sol.group.position.set(x, E.landH(x, z) + bob, z); sol.group.rotation.set(0.12, 0.05, 0);
    sol.setHood(1.15); sol.setFace({mouth: 0, eyes: 'blink'});
  };
  F.camFn = F.camKeys([[0, F.v3(S.x + 4.2, 1.6, S.z + 1.2), F.v3(S.x - 0.3, 0.7, S.z + 1.2), 34], [3, F.v3(S.x + 4.6, 1.8, S.z + 4.8), F.v3(S.x - 0.6, 0.8, S.z + 6.5), 34]]);
}};
})();
