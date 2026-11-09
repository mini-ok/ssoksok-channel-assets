// 시퀀스 2–4: 바위 웅덩이 · 새는 물허벅 · 까마귀 (C9–C24), forest
(() => {
const C = window.CUTS;
// a standalone hand for the ECU (yellow cuff, palm, thumb, pointing finger)
function makeHand(F, s = 1) {
  const {THREE, toon} = F, g = new THREE.Group(), parts = [];
  const P = (m) => { g.add(m); parts.push(m); return m; };
  const cuff = P(new THREE.Mesh(new THREE.CylinderGeometry(0.066 * s, 0.07 * s, 0.22 * s, 20, 1, true), toon(0xfccc38))); cuff.position.y = 0.16 * s; cuff.material.side = THREE.DoubleSide;
  const palm = P(new THREE.Mesh(new THREE.CapsuleGeometry(0.03 * s, 0.035 * s, 4, 12), toon(0xfddcc0))); palm.scale.set(1.15, 1, 0.75);
  const th = P(new THREE.Mesh(new THREE.CapsuleGeometry(0.012 * s, 0.024 * s, 4, 8), toon(0xfddcc0))); th.position.set(0.026 * s, 0.004 * s, 0.014 * s); th.rotation.z = -0.6;
  const fpv = new THREE.Group(); fpv.position.set(-0.008 * s, -0.04 * s, 0.006 * s); g.add(fpv);
  const fi = new THREE.Mesh(new THREE.CapsuleGeometry(0.0105 * s, 0.045 * s, 4, 8), toon(0xfddcc0)); fi.position.y = -0.03 * s; fpv.add(fi); parts.push(fi);
  parts.forEach(m => m.castShadow = true);
  return {group: g, parts, colorOnly: [], finger: fpv, tip: () => fi.localToWorld(new THREE.Vector3(0, -0.035 * s, 0))};
}
// 솔이 hugging the jar in front of her chest; returns the jar (makeJar) — the jar on her back is hidden
function hugJar(F, sol, level = 0.8) {
  sol.jar.visible = false; sol.strap.visible = false;
  const j = makeJar(F, 1.25, {level}); F.addChar(j, sol.group); j.group.position.set(0, 0.68, 0.2); j.group.rotation.set(0.25, 0, 0);
  return j;
}
const HUG = {armL: -0.12, armR: -0.12, armLx: -0.85, armRx: -0.85, elbowL: -0.9, elbowR: -0.9, elbowLx: 0.6, elbowRx: 0.6};
const hug = (o) => Object.assign({}, HUG, o || {});
function inkTex(F) { return canvasTex(F, 128, 128, (x) => { x.fillStyle = '#121018';
  for (let i = 0; i < 7; i++) { x.beginPath(); x.arc(64 + 30 * Math.sin(i * 2.4), 64 + 26 * Math.cos(i * 1.9), 24 + 10 * (i % 3), 0, 7); x.fill(); }
  x.fillStyle = '#2a2836'; x.beginPath(); x.arc(52, 48, 16, 0, 7); x.fill(); }); }
function drops(F, n, col = 0xd8f4f6) {
  const out = []; for (let i = 0; i < n; i++) { const m = new F.THREE.Mesh(new F.THREE.SphereGeometry(0.009 + 0.004 * (i % 3), 8, 6), new F.THREE.MeshBasicMaterial({color: col}));
    F.add(m, {colorOnly: true}); out.push(m); } return out;
}

// C9 ◆ 5s — LS tracking: the 곶자왈. mossy lava, ferns, seaweed on branches, light shafts; 솔이 comes in slowly along the trail
C['9'] = {env: 'forest', dur: 5, setup(F, E) {
  const sol = makeSol(F.THREE, F.toon); F.addChar(sol);
  F.onFrame = (t) => { const tq = F.q2(t); const x = -0.2 + tq * 0.62, z = 1.0;
    const bob = solWalk(sol, tq * 1.5, {over: {yaw: 0.4 * Math.sin(tq * 0.9)}}); sol.group.position.set(x, E.groundH(x, z) + bob, z); sol.group.rotation.y = Math.PI / 2 - 0.25;
    sol.setHood(1.1); sol.setFace({mouth: 0, eyes: tq % 2.4 > 2.3 ? 'blink' : 'open', look: 0.3, down: -0.2}); E.focus(x, 0, z); };
  F.camFn = (t) => { const tq = F.q2(t); const x = -1.0 + tq * 0.55; F.cam.position.set(x, 1.25 + 0.03 * Math.sin(tq * 3.1), 5.2); F.cam.fov = 38; F.cam.updateProjectionMatrix(); F.cam.lookAt(x + 1.6, 1.4, -3.0); };
}};

// C10 4s — CU: in the rock pool, a grey baby octopus
C['10'] = {env: 'forest', dur: 4, setup(F, E) {
  const ku = makeKuruk(F.THREE, F.toon, 1.0); F.addChar(ku); const Pp = E.pool;
  F.onFrame = (t) => { const tq = F.q2(t); E.focus(Pp.x, 0, Pp.z);
    ku.group.position.set(Pp.x + 0.02, Pp.y - 0.11 + 0.004 * Math.sin(tq * 2.2), Pp.z + 0.04); ku.group.rotation.set(0.15, -0.4 + 0.05 * Math.sin(tq), 0);
    ku.setState('grey'); ku.blink(tq > 2.5 && tq < 2.65); ku.group.scale.setScalar(1 + 0.02 * Math.sin(tq * 2.2)); };
  F.camFn = F.camKeys([[0, F.v3(Pp.x + 0.25, Pp.y + 0.42, Pp.z + 0.5), F.v3(Pp.x + 0.02, Pp.y - 0.08, Pp.z + 0.02), 32], [4, F.v3(Pp.x + 0.2, Pp.y + 0.34, Pp.z + 0.4), F.v3(Pp.x + 0.02, Pp.y - 0.09, Pp.z + 0.02), 32]]);
}};

// C11 4s — ECU: her finger hesitates, goes in; a sucker arm curls round it; orange spreads through the grey body
C['11'] = {env: 'forest', dur: 4, setup(F, E) {
  const ku = makeKuruk(F.THREE, F.toon, 1.0); F.addChar(ku); const Pp = E.pool;
  const h = makeHand(F); F.addChar(h);
  F.onFrame = (t) => { const tq = F.q2(t); E.focus(Pp.x, 0, Pp.z);
    // finger: down - hesitate (back up) - down into the water
    const k = [[0, 0.32], [0.6, 0.16], [1.1, 0.2], [1.4, 0.24], [2.0, 0.05], [4, 0.045]];
    let y = k[0][1]; for (let i = 0; i < k.length - 1; i++) if (tq >= k[i][0]) y = F.lerp(k[i][1], k[i + 1][1], F.ss((tq - k[i][0]) / (k[i + 1][0] - k[i][0])));
    h.group.position.set(Pp.x - 0.06, Pp.y + y, Pp.z + 0.1); h.group.rotation.set(-0.5, 0.6, 0.15); h.finger.rotation.x = 0.25;
    ku.group.position.set(Pp.x + 0.02, Pp.y - 0.11, Pp.z + 0.04); ku.group.rotation.set(0.15 + 0.25 * F.ss((tq - 1.9) / 0.4), -0.4, 0);
    const u = F.ss((tq - 2.2) / 1.2); ku.setMix('grey', 'orange', u); ku.blink(tq > 3.5 && tq < 3.6);
    ku.group.scale.setScalar(1 + 0.06 * F.ss((tq - 2.0) / 0.3) * (1 - F.ss((tq - 2.6) / 0.6)));
  };
  F.camFn = F.camKeys([[0, F.v3(Pp.x + 0.2, Pp.y + 0.18, Pp.z + 0.32), F.v3(Pp.x - 0.01, Pp.y - 0.02, Pp.z + 0.04), 30], [4, F.v3(Pp.x + 0.17, Pp.y + 0.14, Pp.z + 0.27), F.v3(Pp.x - 0.01, Pp.y - 0.04, Pp.z + 0.04), 30]]);
}};

// C12 3s — MS: she pours the jar's water away and scoops the pool water — and the octopus — into it
C['12'] = {env: 'forest', dur: 3, setup(F, E) {
  const {THREE, toon} = F, Pp = E.pool;
  const sol = makeSol(THREE, toon); F.addChar(sol); sol.jar.visible = false;
  const sx = Pp.x - 0.05, sz = Pp.z + 0.62, gy = E.groundH(sx, sz);
  sol.group.position.set(sx, gy - 0.3, sz); sol.group.rotation.y = Math.PI;                 // kneeling, facing the pool (-z)
  const j = makeJar(F, 1.25, {level: 0.8}); F.addChar(j);
  const st = drops(F, 16, 0x9fd2d6);
  F.onFrame = (t) => { const tq = F.q2(t); E.focus(sx, 0, sz);
    const pour = F.ss(tq / 0.35) * (1 - F.ss((tq - 1.15) / 0.3)), dip = F.ss((tq - 1.45) / 0.45) * (1 - F.ss((tq - 2.4) / 0.4));
    sol.setHood(1.1);
    sol.pose({pitch: 0.35 + 0.2 * dip, legL: -0.4, legR: -0.4, kneeL: 1.9, kneeR: 1.9, armL: -0.15, armR: -0.15, armLx: -1.1 - 0.3 * dip, armRx: -1.1 - 0.3 * dip, elbowL: -0.7, elbowR: -0.7, elbowLx: 0.4, elbowRx: 0.4});
    sol.setFace({mouth: 0, eyes: 'open', down: 0.8});
    sol.group.updateMatrixWorld(true);
    const hl = new THREE.Vector3(), hr = new THREE.Vector3(); sol.arms[-1].userData.hand.getWorldPosition(hl); sol.arms[1].userData.hand.getWorldPosition(hr);
    const mid = hl.add(hr).multiplyScalar(0.5);
    j.group.position.copy(mid).add(new THREE.Vector3(0, -0.02 - 0.18 * dip, -0.06 - 0.12 * dip));
    j.group.rotation.set(-1.6 * pour - 0.6 * dip, 0, 0.0);
    j.setLevel(tq < 1.2 ? 0.8 * (1 - F.ss(tq / 1.2)) : 0.15 + 0.6 * F.ss((tq - 1.6) / 0.8));
    const mouth = new THREE.Vector3(0, 0.14, 0).applyMatrix4(j.group.matrixWorld);
    st.forEach((d, i) => { const a = ((tq * 2 + i / st.length) % 1); d.userData.on = pour > 0.6;
      d.position.set(mouth.x + 0.02 * Math.sin(i), mouth.y - a * a * 0.6, mouth.z - 0.06 - a * 0.12); });
  };
  F.camFn = F.camKeys([[0, F.v3(Pp.x + 1.05, gy + 1.35, Pp.z - 0.5), F.v3(sx - 0.05, gy + 0.42, sz - 0.3), 36], [3, F.v3(Pp.x + 1.0, gy + 1.32, Pp.z - 0.46), F.v3(sx - 0.05, gy + 0.42, sz - 0.3), 36]]);
}};

// C13 ★ 2.8s — CU front: 솔이: "꾸럭아, 조금만 참아."
C['13'] = {env: 'forest', dur: 2.8, setup(F, E) {
  const {THREE, toon} = F, Pp = E.pool;
  const sol = makeSol(THREE, toon); F.addChar(sol);
  const sx = Pp.x - 0.05, sz = Pp.z + 0.75, gy = E.groundH(sx, sz);
  sol.group.position.set(sx, gy, sz); sol.group.rotation.y = 0.35;
  const j = hugJar(F, sol, 0.7);
  F.onFrame = (t) => { const tq = F.q2(t); E.focus(sx, 0, sz);
    sol.setHood(1.05);
    sol.pose(hug({pitch: 0.42 - 0.08 * Math.min(1, tq), yaw: 0.05, breath: Math.sin(tq * 3)}));
    sol.setFace({mouth: mouthAt('sol1', 0.3, t), eyes: tq > 2.55 && tq < 2.65 ? 'blink' : 'open', down: 0.9, smile: 0.3});
  };
  F.camFn = F.camKeys([[0, F.v3(sx + 0.3, gy + 1.05, sz + 1.0), F.v3(sx, gy + 1.0, sz), 30], [2.8, F.v3(sx + 0.27, gy + 1.03, sz + 0.9), F.v3(sx, gy + 1.0, sz), 30]]);
}};

// C14 2s — POV: between the trees, the sea in pieces
C['14'] = {env: 'forest', dur: 2, setup(F, E) {
  F.onFrame = () => { E.seaGlimpse.userData.on = true; };
  F.camFn = (t) => { const tq = F.q2(t); F.cam.position.set(11.2 + 0.03 * Math.sin(tq * 5), 1.15 + 0.02 * Math.sin(tq * 7), 1.0 + tq * 0.05);
    F.cam.fov = 40; F.cam.updateProjectionMatrix(); F.cam.lookAt(14.2, 1.7, -32); };
}};

// C15 ◆ 6s — tracking: she runs with the jar hugged to her chest; the raincoat catches on a vine — a tug — she pulls free
C['15'] = {env: 'forest', dur: 6, setup(F, E) {
  const sol = makeSol(F.THREE, F.toon); F.addChar(sol); const j = hugJar(F, sol, 0.75);
  const xOf = (tq) => tq < 2.9 ? 2.4 + tq * 1.25 : tq < 4.1 ? 6.0 - 0.06 * F.ss((tq - 2.9) / 0.2) : 5.94 + (tq - 4.1) * 1.3;
  F.onFrame = (t) => { const tq = F.q2(t), x = xOf(tq), z = 1.0; E.focus(x, 0, z);
    const caught = tq > 2.9 && tq < 4.1, tug = caught ? Math.sin((tq - 2.9) * 14) * (1 - (tq - 2.9) / 1.2) : 0;
    let bob = 0;
    if (caught) { sol.pose(hug({pitch: -0.1, yaw: -0.9 * F.ss((tq - 3.0) / 0.25) * (1 - F.ss((tq - 3.8) / 0.2)), legL: -0.3, legR: 0.3, kneeL: 0.3, kneeR: 0.2}));
      sol.group.rotation.set(-0.15 + 0.08 * tug, Math.PI / 2, 0.05 * tug); }
    else { bob = solRun(sol, tq * 2.3, {over: hug({pitch: 0.15})}); sol.group.rotation.set(0.12, Math.PI / 2, 0); }
    sol.group.position.set(x, E.groundH(x, z) + bob, z);
    sol.setHood(1.1); sol.setFace({mouth: caught ? 1 : 0, eyes: caught ? 'wide' : 'open', look: caught ? -0.8 : 0.4});
  };
  F.camFn = (t) => { const tq = F.q2(t), x = xOf(tq); F.cam.position.set(x + 0.9, 1.0, 3.4); F.cam.fov = 36; F.cam.updateProjectionMatrix(); F.cam.lookAt(x + 0.3, 0.75, 1.0); };
}};

// C16 2s — INSERT: through the crack, drip, drip — onto a lava stone
C['16'] = {env: 'forest', dur: 2, setup(F, E) {
  const {THREE, toon} = F;
  const x0 = 8.2, z0 = 1.0, gy = E.groundH(x0, z0);
  const sol = makeSol(THREE, F.toon); F.addChar(sol); const j = hugJar(F, sol, 0.6);
  sol.group.position.set(x0, gy, z0 - 0.2); sol.group.rotation.y = Math.PI / 2; j.group.rotation.set(0.15, -1.5, 0);
  sol.group.updateMatrixWorld(true); const jw0 = new THREE.Vector3(); j.group.getWorldPosition(jw0);
  const stone = lavaRock(F, 0.12, 0x3e3a3c, {flat: 0.6}); stone.position.set(jw0.x + 0.03, gy + 0.03, jw0.z + 0.05); F.add(stone);
  const d = drops(F, 2, 0xcfeef0), rings = [];
  for (let i = 0; i < 2; i++) { const r = new THREE.Mesh(new THREE.RingGeometry(0.01, 0.014, 20), new THREE.MeshBasicMaterial({color: 0xcfeef0, side: THREE.DoubleSide}));
    r.rotation.x = -Math.PI / 2; F.add(r, {colorOnly: true}); rings.push(r); }
  F.onFrame = (t) => { const tq = F.q2(t); E.focus(x0, 0, z0); sol.setHood(1.1); sol.pose(hug({pitch: 0.2, breath: Math.sin(tq * 6)})); sol.group.updateMatrixWorld(true);
    const tip = j.crackTip();
    d.forEach((m, i) => { const a = tq - 0.3 - i * 0.9; const fall = a > 0.25 ? (a - 0.25) : 0; m.userData.on = a > 0 && fall < 0.36;
      m.position.set(tip.x, tip.y - 4.9 * fall * fall, tip.z); m.scale.set(1, a < 0.25 ? 0.6 + a * 2 : 1.4, 1);
      const r = rings[i]; const ra = fall - 0.36; r.userData.on = ra > 0 && ra < 0.4; r.position.set(tip.x, stone.position.y + 0.06, tip.z); r.scale.setScalar(1 + ra * 9); });
  };
  F.camFn = F.camKeys([[0, F.v3(jw0.x + 0.5, gy + 0.4, jw0.z + 0.8), F.v3(jw0.x, gy + 0.42, jw0.z), 46], [2, F.v3(jw0.x + 0.46, gy + 0.4, jw0.z + 0.74), F.v3(jw0.x, gy + 0.42, jw0.z), 46]]);
}};

// C17 4s — MS: at the fork she stops and looks left, right
C['17'] = {env: 'forest', dur: 4, setup(F, E) {
  const sol = makeSol(F.THREE, F.toon); F.addChar(sol); hugJar(F, sol, 0.55); const Fk = E.fork;
  F.onFrame = (t) => { const tq = F.q2(t); E.focus(Fk.x, 0, Fk.z);
    const x = Fk.x - 0.9 + 0.5 * F.ss(tq / 0.6), arrive = F.ss(tq / 0.6);
    const look = tq < 1.0 ? 0 : tq < 2.0 ? -0.9 * F.ss((tq - 1.0) / 0.3) : tq < 3.1 ? 0.9 * F.ss((tq - 2.0) / 0.3) - 0.9 * (1 - F.ss((tq - 2.0) / 0.3)) : 0.9 * (1 - F.ss((tq - 3.1) / 0.4));
    sol.pose(hug({pitch: 0.05, yaw: look, breath: Math.sin(tq * 6) * (1 - arrive * 0.5)}));
    sol.group.position.set(x, E.groundH(x, Fk.z), Fk.z); sol.group.rotation.set(0.04 * (1 - arrive), Math.PI / 2 - 0.5, 0);
    sol.setHood(1.1); sol.setFace({mouth: tq < 0.8 ? 1 : 0, eyes: 'open', look: look * 0.8, down: -0.1});
  };
  F.camFn = F.camKeys([[0, F.v3(Fk.x + 1.5, 1.05, Fk.z + 1.6), F.v3(Fk.x - 0.4, 0.85, Fk.z), 36], [4, F.v3(Fk.x + 1.35, 1.05, Fk.z + 1.45), F.v3(Fk.x - 0.4, 0.85, Fk.z), 36]]);
}};

// C18 5s — CU: she whistles; the octopus answers "퓨―" with a little spout of drops from the jar mouth; again
C['18'] = {env: 'forest', dur: 5, setup(F, E) {
  const {THREE} = F; const sol = makeSol(THREE, F.toon); F.addChar(sol); const j = hugJar(F, sol, 0.55); const Fk = E.fork;
  const ku = makeKuruk(THREE, F.toon, 0.6); F.addChar(ku, j.group); ku.setState('orange');
  const sp = drops(F, 14);
  F.onFrame = (t) => { const tq = F.q2(t); E.focus(Fk.x, 0, Fk.z);
    const x = Fk.x - 0.4; sol.group.position.set(x, E.groundH(x, Fk.z), Fk.z); sol.group.rotation.y = Math.PI / 2 - 0.5;
    const wh = (tq > 0.5 && tq < 1.2) || (tq > 2.7 && tq < 3.3);
    const ans = (a) => tq > a && tq < a + 0.8;
    sol.pose(hug({pitch: 0.3, yaw: 0.0, breath: 0}));
    sol.setHood(1.1); sol.setFace({mouth: wh ? 'o' : 0, eyes: ans(1.5) || ans(3.5) ? 'wide' : 'open', down: 0.7, smile: tq > 4.2 ? 0.8 : 0});
    const peek = F.ss((tq - 1.25) / 0.2) * (1 - F.ss((tq - 2.3) / 0.2)) + F.ss((tq - 3.25) / 0.2) * (1 - F.ss((tq - 4.4) / 0.2));
    ku.group.position.set(0, 0.06 + 0.07 * peek, 0); ku.group.rotation.set(-0.3, 0, 0); ku.blink(tq > 2.0 && tq < 2.1);
    sol.group.updateMatrixWorld(true); const m0 = new THREE.Vector3(0, 0.16, 0).applyMatrix4(j.group.matrixWorld);
    sp.forEach((d, i) => { const a0 = i < 7 ? 1.55 : 3.55, a = tq - a0 - (i % 7) * 0.03; d.userData.on = a > 0 && a < 0.6;
      const ang = (i % 7) * 0.9; d.position.set(m0.x + Math.cos(ang) * 0.12 * a, m0.y + 1.1 * a - 2.6 * a * a, m0.z + Math.sin(ang) * 0.12 * a); });
  };
  F.camFn = F.camKeys([[0, F.v3(Fk.x + 0.35, 1.12, Fk.z + 1.1), F.v3(Fk.x - 0.36, 0.95, Fk.z + 0.1), 32], [5, F.v3(Fk.x + 0.32, 1.12, Fk.z + 1.02), F.v3(Fk.x - 0.36, 0.95, Fk.z + 0.1), 32]]);
}};

// C19 4s — LS: the drops glitter in the sun and scatter down one path — the waves can be heard at its end
C['19'] = {env: 'forest', dur: 4, setup(F, E) {
  const {THREE} = F; const sol = makeSol(THREE, F.toon); F.addChar(sol); const j = hugJar(F, sol, 0.5); const Fk = E.fork;
  const sp = drops(F, 22, 0xf6fff8);
  F.onFrame = (t) => { const tq = F.q2(t); E.focus(Fk.x, 0, Fk.z);
    const x = Fk.x - 0.4; sol.group.position.set(x, E.groundH(x, Fk.z), Fk.z); sol.group.rotation.y = Math.PI / 2 - 0.5 - 0.9 * F.ss((tq - 2.2) / 0.5);
    sol.pose(hug({pitch: 0.05, yaw: -0.4 * F.ss((tq - 1.2) / 0.4)})); sol.setHood(1.1); sol.setFace({mouth: 0, eyes: 'wide', look: -0.6});
    sol.group.updateMatrixWorld(true); const m0 = new THREE.Vector3(0, 0.16, 0).applyMatrix4(j.group.matrixWorld);
    sp.forEach((d, i) => { const a = tq - 0.2 - i * 0.05; d.userData.on = a > 0 && a < 2.4 && (Math.floor(tq * 12 + i) % 3 !== 0);
      const u = Math.min(1, a / 2.2); d.position.set(m0.x + u * 1.8 + 0.1 * Math.sin(i), m0.y + 0.4 * Math.sin(u * Math.PI) + 0.05 * Math.cos(i * 3) - u * 0.5, m0.z - u * 3.2 + 0.15 * Math.sin(i * 2));
      d.scale.setScalar(1 + 0.8 * Math.abs(Math.sin(tq * 9 + i))); });
  };
  F.camFn = F.camKeys([[0, F.v3(Fk.x + 1.9, 1.35, Fk.z + 1.7), F.v3(Fk.x - 0.1, 0.85, Fk.z - 1.2), 38], [4, F.v3(Fk.x + 1.75, 1.35, Fk.z + 1.55), F.v3(Fk.x + 0.6, 0.8, Fk.z - 2.4), 38]]);
}};

// C20 4s — INSERT (water down to half) -> LS: she runs again, down the left path
C['20'] = {env: 'forest', dur: 4, setup(F, E) {
  const {THREE} = F; const sol = makeSol(THREE, F.toon); F.addChar(sol); const j = hugJar(F, sol, 0.42); const Fk = E.fork;
  const ku = makeKuruk(THREE, F.toon, 0.6); F.addChar(ku, j.group); ku.setState('orange');
  F.onFrame = (t) => { const tq = F.q2(t);
    if (tq < 1.5) { const x = Fk.x - 0.4; sol.group.position.set(x, E.groundH(x, Fk.z), Fk.z); sol.group.rotation.y = 0.2; sol.pose(hug({pitch: 0.3})); ku.group.position.set(0, 0.0, 0); E.focus(x, 0, Fk.z); }
    else { const u = tq - 1.5, x = Fk.x + 0.2 + u * 0.75, z = 1.0 - u * 1.2; const bob = solRun(sol, tq * 2.3, {over: hug({pitch: 0.15})});
      sol.group.position.set(x, E.groundH(x, z) + bob, z); sol.group.rotation.set(0.12, Math.atan2(0.75, -1.2), 0); E.focus(x, 0, z); }
    sol.setHood(1.1); sol.setFace({mouth: 0, eyes: 'open'}); ku.blink(tq > 0.9 && tq < 1.0);
  };
  F.camFn = (t) => { const tq = F.q2(t); F.cam.fov = 34; F.cam.updateProjectionMatrix();
    if (tq < 1.5) { sol.group.updateMatrixWorld(true); const m0 = new THREE.Vector3(0, 0.15, 0).applyMatrix4(j.group.matrixWorld);
      F.cam.position.set(m0.x + 0.03, m0.y + 0.32, m0.z + 0.08); F.cam.lookAt(m0.x, m0.y - 0.05, m0.z); }
    else { F.cam.position.set(Fk.x - 1.6, 1.4, Fk.z + 1.8); F.cam.lookAt(Fk.x + 1.4, 0.6, Fk.z - 1.6); } };
}};

// C21 3s — low angle: a crow on the branch looks down at the shining jar
C['21'] = {env: 'forest', dur: 3, setup(F, E) {
  const crow = makeCrow(F); F.addChar(crow); const B = E.crowBranch;
  F.onFrame = (t) => { const tq = F.q2(t); E.focus(B.x, 0, B.z);
    crow.group.position.set(B.x, B.y + 0.2, B.z); crow.group.rotation.set(0.25, Math.PI / 2 + 0.5, 0); crow.flap(0, 1);
    const cock = tq > 1.0 ? 1 : 0; crow.head.rotation.set(0.6 * cock, 0, 0.45 * cock * Math.sin(tq * 2 + 1) + (tq > 2.2 ? -0.5 : 0)); crow.blinkEyes(tq > 1.8 && tq < 1.9); crow.setInk(0); };
  F.camFn = F.camKeys([[0, F.v3(B.x + 0.4, 0.95, B.z + 2.3), F.v3(B.x, B.y + 0.3, B.z), 34], [3, F.v3(B.x + 0.35, 0.98, B.z + 2.1), F.v3(B.x, B.y + 0.3, B.z), 31]]);
}};

// C22 4s — MS: the crow dives; 솔이 curls up; the beak goes into the jar mouth -> "푸욱": a cloud of ink
C['22'] = {env: 'forest', dur: 4, setup(F, E) {
  const {THREE} = F; const sol = makeSol(THREE, F.toon); F.addChar(sol); const j = hugJar(F, sol, 0.4); const B = E.crowBranch;
  const crow = makeCrow(F); F.addChar(crow);
  const iT = inkTex(F), clouds = [];
  for (let i = 0; i < 9; i++) { const s = new THREE.Sprite(new THREE.SpriteMaterial({map: iT, transparent: true, depthWrite: false})); F.add(s, {colorOnly: true}); clouds.push(s); }
  const sx = B.x - 0.3, sz = 0.6;
  F.onFrame = (t) => { const tq = F.q2(t); E.focus(sx, 0, sz);
    const crouch = F.ss((tq - 1.0) / 0.3);
    sol.group.position.set(sx, E.groundH(sx, sz) - 0.12 * crouch, sz); sol.group.rotation.set(0.25 * crouch, -0.4, 0);
    sol.pose(hug({pitch: 0.5 * crouch, legL: -0.6 * crouch, legR: -0.6 * crouch, kneeL: 1.1 * crouch, kneeR: 1.1 * crouch}));
    sol.setHood(1.1); sol.setFace({mouth: tq > 2.6 ? 1 : 0, eyes: crouch > 0.5 && tq < 2.6 ? 'blink' : 'wide', down: 0.5});
    sol.group.updateMatrixWorld(true); const m0 = new THREE.Vector3(0, 0.17, 0).applyMatrix4(j.group.matrixWorld);
    const dive = F.ss((tq - 0.5) / 1.3);
    const p0 = new THREE.Vector3(B.x, B.y + 0.2, B.z), p1 = m0.clone().add(new THREE.Vector3(0.05, 0.22, 0.1));
    const cp = p0.clone().lerp(p1, dive); cp.y += Math.sin(dive * Math.PI) * 0.3;
    if (tq > 1.8) cp.copy(p1).add(new THREE.Vector3(0, -0.05 * F.ss((tq - 1.8) / 0.4) + 0.04 * Math.sin(tq * 30) * (tq < 2.7 ? 1 : 0), 0));
    crow.group.position.copy(cp); crow.group.lookAt(m0); crow.group.rotateX(tq > 1.8 ? 0.6 : 0.15);
    crow.flap(tq < 1.8 ? 0.9 * Math.sin(tq * 16) : 0.4 * Math.sin(tq * 20), tq < 0.5 ? 1 : 0); crow.setInk(0);
    clouds.forEach((c, i) => { const a = tq - 2.75 - i * 0.02; c.userData.on = a > 0;
      const r = 0.05 + Math.min(1, a * 3) * (0.25 + 0.06 * (i % 3)); const ang = i * 0.7;
      c.position.set(m0.x + Math.cos(ang) * r * 0.9, m0.y + 0.15 + Math.sin(ang) * r * 0.6 + a * 0.05, m0.z + 0.1 + Math.sin(ang * 1.3) * 0.1);
      const s2 = 0.2 + Math.min(1, a * 4) * 0.35; c.scale.set(s2, s2, 1); });
  };
  F.camFn = F.camKeys([[0, F.v3(sx - 1.1, 1.25, sz + 1.9), F.v3(sx + 0.3, 1.1, sz - 0.2), 38], [2.6, F.v3(sx - 0.95, 1.1, sz + 1.6), F.v3(sx, 0.85, sz), 36], [4, F.v3(sx - 0.9, 1.05, sz + 1.5), F.v3(sx, 0.85, sz), 36]],
                      {shake: (tq) => tq > 2.75 && tq < 3.1 ? 0.012 : 0});
}};

// C23 4s — MS: an empty hold (0.8 s) -> the crow, black as ink, only its eyes blinking -> it wobbles away
C['23'] = {env: 'forest', dur: 4, setup(F, E) {
  const {THREE} = F; const sol = makeSol(THREE, F.toon); F.addChar(sol); const j = hugJar(F, sol, 0.4); const B = E.crowBranch;
  const crow = makeCrow(F); F.addChar(crow); crow.setInk(1);
  const iT = inkTex(F), clouds = [];
  for (let i = 0; i < 6; i++) { const s = new THREE.Sprite(new THREE.SpriteMaterial({map: iT, transparent: true, depthWrite: false})); F.add(s, {colorOnly: true}); clouds.push(s); }
  const sx = B.x - 0.3, sz = 0.6;
  F.onFrame = (t) => { const tq = F.q2(t); E.focus(sx, 0, sz);
    sol.group.position.set(sx, E.groundH(sx, sz) - 0.12, sz); sol.group.rotation.set(0.25, -0.4, 0);
    sol.pose(hug({pitch: tq > 2.8 ? 0.0 : 0.5, legL: -0.6, legR: -0.6, kneeL: 1.1, kneeR: 1.1}));
    sol.setHood(1.1); sol.setFace({mouth: 0, eyes: tq > 2.8 ? 'open' : 'blink', look: tq > 2.8 ? 0.5 : 0, down: tq > 2.8 ? -0.6 : 0.5});
    sol.group.updateMatrixWorld(true); const m0 = new THREE.Vector3(0, 0.17, 0).applyMatrix4(j.group.matrixWorld);
    clouds.forEach((c, i) => { c.userData.on = tq < 1.0; const ang = i * 1.1, r = 0.3 + tq * 0.1; c.position.set(m0.x + Math.cos(ang) * r, m0.y + 0.2 + Math.sin(ang) * r * 0.6, m0.z + 0.1);
      const s2 = 0.5 * (1 - tq); c.scale.set(s2, s2, 1); c.material.opacity = 1 - tq; });
    const fly = F.ss((tq - 2.2) / 1.6);
    const base = m0.clone().add(new THREE.Vector3(0.05, 0.22, 0.1));
    crow.group.position.set(base.x - fly * 1.8 + 0.12 * Math.sin(tq * 9) * fly, base.y + fly * 1.6 + 0.1 * Math.sin(tq * 13) * fly, base.z + fly * 0.4);
    crow.group.rotation.set(0.1 + 0.4 * Math.sin(tq * 11) * fly, -Math.PI / 2 - 0.4 + 0.5 * Math.sin(tq * 7) * fly, 0.5 * Math.sin(tq * 9) * fly);
    crow.flap(fly > 0 ? 1.0 * Math.sin(tq * 18) : 0, fly > 0 ? 0 : 0.6);
    crow.blinkEyes((tq > 1.1 && tq < 1.2) || (tq > 1.55 && tq < 1.65));
    crow.head.rotation.set(0, tq > 1.3 && tq < 2.0 ? 0.6 : 0, 0);
  };
  F.camFn = F.camKeys([[0, F.v3(sx - 0.9, 1.05, sz + 1.5), F.v3(sx, 0.9, sz), 36], [4, F.v3(sx - 0.85, 1.05, sz + 1.45), F.v3(sx - 0.2, 1.0, sz), 36]]);
}};

// C24 4s — CU: the inky octopus in the jar flushes orange with pride; 솔이 laughs for the first time
C['24'] = {env: 'forest', dur: 4, setup(F, E) {
  const {THREE} = F; const sol = makeSol(THREE, F.toon); F.addChar(sol); const j = hugJar(F, sol, 0.4); const B = E.crowBranch;
  const ku = makeKuruk(THREE, F.toon, 0.6); F.addChar(ku, j.group);
  const sx = B.x - 0.3, sz = 0.6;
  F.onFrame = (t) => { const tq = F.q2(t); E.focus(sx, 0, sz);
    sol.group.position.set(sx, E.groundH(sx, sz) - 0.12, sz); sol.group.rotation.set(0.25, -0.4, 0);
    sol.pose(hug({pitch: 0.5, legL: -0.6, legR: -0.6, kneeL: 1.1, kneeR: 1.1}));
    const laugh = tq > 2.2;
    sol.setHood(1.1); sol.setFace({mouth: laugh ? (Math.floor(tq * 6) % 2 ? 2 : 1) : 0, eyes: laugh ? 'blink' : 'open', down: 0.7, smile: laugh ? 1 : 0.2});
    const puff = F.ss((tq - 0.6) / 0.4);
    ku.group.position.set(0, 0.07 + 0.03 * puff, 0); ku.group.rotation.set(-0.35, 0.2 * Math.sin(tq * 2), 0);
    ku.group.scale.setScalar(1 + 0.15 * puff * (1 + 0.2 * Math.sin(tq * 10)) * (tq < 1.6 ? 1 : 0.6));
    if (tq < 0.6) ku.setHex(0x1a1820); else ku.setHex(new THREE.Color(0x1a1820).lerp(new THREE.Color(KU_COL.orange), F.ss((tq - 0.6) / 0.5)).getHex());
    ku.blink(tq > 1.7 && tq < 1.8);
  };
  F.camFn = (t) => { const tq = F.q2(t); sol.group.updateMatrixWorld(true); const m0 = new THREE.Vector3(0, 0.15, 0).applyMatrix4(j.group.matrixWorld);
    F.cam.position.set(m0.x - 0.26 - 0.02 * F.ss(tq / 4), m0.y + 0.04, m0.z + 0.5); F.cam.fov = 34; F.cam.updateProjectionMatrix(); F.cam.lookAt(m0.x + 0.03, m0.y + 0.12, m0.z - 0.05); };
}};
})();
