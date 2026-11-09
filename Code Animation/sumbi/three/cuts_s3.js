// 시퀀스 5–6: 바다 앞 · 미역 숲 (C25–C30)
(() => {
const C = window.CUTS;
const HUG = {armL: -0.12, armR: -0.12, armLx: -0.85, armRx: -0.85, elbowL: -0.9, elbowR: -0.9, elbowLx: 0.6, elbowRx: 0.6};
const hug = (o) => Object.assign({}, HUG, o || {});
function hugJar(F, sol, level = 0.8, s = 1.25) {
  sol.jar.visible = false; if (sol.strap) sol.strap.visible = false;
  const j = makeJar(F, s, {level}); F.addChar(j, sol.group); j.group.position.set(0, 0.68, 0.2); j.group.rotation.set(0.25, 0, 0); return j;
}
function seaDepthY(E, x, z) { const d = z - E.shoreZ(x); return d > -0.5 ? E.landH(x, z) : -0.6 - Math.min(1.6, (-0.5 - d) * 0.35); }
// the raincoat left on the rock: a flattened coat + hood, lying down
function coatProp(F) {
  const c = makeSol(F.THREE, F.toon); c.head.visible = false; c.jar.visible = false; c.strap.visible = false;
  c.parts.forEach(m => { const h = m.material && m.material.color && m.material.color.getHex(); if (h === new F.THREE.Color(0xfddcc0).getHex() || h === new F.THREE.Color(0x384470).getHex() || h === new F.THREE.Color(0x2b2a3d).getHex()) m.visible = false; });
  c.pose({armL: 0.9, armR: 0.7, armLx: 0.2, armRx: -0.1, elbowL: 0.4, elbowR: -0.2});
  const g = new F.THREE.Group(); c.group.rotation.x = -Math.PI / 2; c.group.position.set(0, 0.04, 0.55); c.group.scale.set(1, 1, 0.35); g.add(c.group);
  return {group: g, parts: c.parts.filter(m => m.visible), colorOnly: []};
}

// C25 ◆ 6s — dolly zoom: the forest ends abruptly; the sea fills the frame; 솔이 freezes
C['25'] = {env: 'coast', mode: 'day', dur: 6, setup(F, E) {
  const {THREE} = F; const sol = makeSol(THREE, F.toon); F.addChar(sol); const j = hugJar(F, sol, 0.25);
  const x0 = -6, z0 = 23.5;
  F.onFrame = (t) => { E.update(t); const tq = F.q2(t); E.focus(x0, 0, z0);
    const stop = F.ss((tq - 0.5) / 0.6), z = z0 + 1.2 * (1 - stop);
    const bob = stop < 0.95 ? solRun(sol, tq * 2.2, {amp: 1 - stop, over: hug({pitch: 0.1})}) : (sol.pose(hug({pitch: -0.15 - 0.1 * F.ss((tq - 2) / 1), breath: Math.sin(tq * 5)})), 0);
    sol.group.position.set(x0, E.landH(x0, z) + bob, z); sol.group.rotation.set(0, Math.PI, 0); C['25']._z = z;
    sol.setHood(1.1); sol.setFace({mouth: 0, eyes: 'wide', look: 0});
  };
  // camera behind her moves in while widening (dolly zoom): her size holds, the sea grows behind her
  F.camFn = (t) => { const tq = F.q2(t); const u = F.ss((tq - 1.0) / 4.5);
    const fov = F.lerp(60, 17, u), size = 2.3;                          // keep the frame height at her ~size m
    const dist = (size / 2) / Math.tan((fov * Math.PI / 180) / 2);
    F.cam.fov = fov; F.cam.updateProjectionMatrix();
    const zs = C['25']._z || z0; F.cam.position.set(x0 + 0.25, E.landH(x0, z0) + 1.35 + 0.05 * dist, zs + dist); F.cam.lookAt(x0, E.landH(x0, z0) + 0.6, zs - 3); };
}};

// C26 2s — flash: the storm night: a smaller 솔이 in her raincoat watches the sea all night
C['26'] = {env: 'coast', mode: 'storm', dur: 2, finish: 'coast', setup(F, E) {
  const {THREE} = F; const S = E.seat; F.meta.flash = [0.55];
  const sol = makeSol(THREE, F.toon); F.addChar(sol); sol.group.scale.setScalar(0.82);
  sol.group.position.set(S.x, S.y - 0.5 * 0.82, S.z); sol.group.rotation.y = Math.PI;                 // faces the sea
  F.onFrame = (t) => { E.update(t * 1.4); const tq = F.q2(t); E.focus(S.x, 0, S.z);
    sol.setHood(1.2); sol.pose({pitch: 0.1, legL: -1.4, legR: -1.35, kneeL: 1.4, kneeR: 1.45, armL: 0.05, armR: 0.05, armLx: -1.1, armRx: -1.1, elbowLx: 1.0, elbowRx: 1.0}); };
  F.camFn = F.camKeys([[0, F.v3(S.x + 0.6, S.y + 0.6, S.z + 2.4), F.v3(S.x - 0.2, S.y + 0.2, S.z - 6), 40], [2, F.v3(S.x + 0.55, S.y + 0.58, S.z + 2.2), F.v3(S.x - 0.2, S.y + 0.2, S.z - 6), 40]]);
}};

// C27 5s — CU -> INSERT: barely any water left at the bottom of the jar; the octopus, grey and limp
C['27'] = {env: 'coast', mode: 'day', dur: 5, setup(F, E) {
  const {THREE} = F; const S = E.seat;
  const sol = makeSol(THREE, F.toon); F.addChar(sol); sol.group.position.set(S.x, S.y - 0.5, S.z); sol.group.rotation.y = Math.PI;
  const j = hugJar(F, sol, 0.08); j.group.position.set(0, 0.52, 0.33); j.group.rotation.set(-0.35, 0, 0);
  const ku = makeKuruk(THREE, F.toon, 0.7); F.addChar(ku, j.group);
  const jl = new THREE.PointLight(0xfff2dc, 0.12, 0.3, 1.5); jl.position.set(0, 0.05, 0); j.group.add(jl);
  F.onFrame = (t) => { E.update(t); const tq = F.q2(t); E.focus(S.x, 0, S.z);
    sol.setHood(1.1); sol.pose({pitch: 0.55, legL: -1.4, legR: -1.35, kneeL: 1.4, kneeR: 1.45, armL: 0.0, armR: 0.0, armLx: -0.7, armRx: -0.7, elbowL: -0.5, elbowR: -0.5, elbowLx: 0.5, elbowRx: 0.5});
    sol.setFace({mouth: 0, eyes: tq > 3.2 && tq < 3.35 ? 'blink' : 'open', down: 1.0, smile: -0.5});
    ku.group.position.set(0.005, 0.085, 0.01); ku.group.rotation.set(1.15, 0.2, 0.35); ku.setHex(0x8f8590); ku.blink(true);
    ku.group.scale.set(1, 0.85 + 0.03 * Math.sin(tq * 1.2), 1);
  };
  F.camFn = (t) => { const tq = F.q2(t); sol.group.updateMatrixWorld(true); const m0 = new THREE.Vector3(0, 0.14, 0).applyMatrix4(j.group.matrixWorld);
    const face = new THREE.Vector3(); sol.head.getWorldPosition(face);
    const u = F.ss((tq - 1.8) / 1.0);                                     // CU on her face -> down into the jar
    const look = face.clone().lerp(m0.clone().add(new THREE.Vector3(0, -0.06, 0)), u);
    const pos = face.clone().add(new THREE.Vector3(0.15, 0.02, -0.75)).lerp(m0.clone().add(new THREE.Vector3(0.01, 0.36, -0.1)), u);
    F.cam.position.copy(pos); F.cam.fov = 32; F.cam.updateProjectionMatrix(); F.cam.lookAt(look); };
}};

// C28 7s — MCU: she whistles — no answer — once more — only the waves. She grips the brim of her hood
C['28'] = {env: 'coast', mode: 'day', dur: 7, setup(F, E) {
  const {THREE} = F; const S = E.seat;
  const sol = makeSol(THREE, F.toon); F.addChar(sol); sol.group.position.set(S.x, S.y - 0.5, S.z); sol.group.rotation.y = Math.PI;
  const j = hugJar(F, sol, 0.08); j.group.position.set(0, 0.6, 0.24); j.group.rotation.set(-0.1, 0, 0);
  F.onFrame = (t) => { E.update(t); const tq = F.q2(t); E.focus(S.x, 0, S.z);
    const wh = (tq > 0.8 && tq < 1.6) || (tq > 3.3 && tq < 4.0);
    const grip = F.ss((tq - 5.0) / 0.4);
    sol.setHood(1.1 + 0.15 * grip);
    sol.pose(Object.assign(hug({pitch: wh ? 0.2 : (tq > 4.4 ? 0.45 : 0.3), legL: -1.4, legR: -1.35, kneeL: 1.4, kneeR: 1.45}),
      grip > 0 ? {armL: 0.3 * grip, armR: 0.3 * grip, armLx: -0.85 - 1.4 * grip, armRx: -0.85 - 1.4 * grip, elbowL: -0.9 * (1 - grip), elbowR: -0.9 * (1 - grip), elbowLx: 0.6 + 1.2 * grip, elbowRx: 0.6 + 1.2 * grip} : {}));
    sol.setFace({mouth: wh ? 'o' : 0, eyes: grip > 0.5 ? 'blink' : 'open', down: wh ? 0.6 : (tq > 2 && tq < 3.2) || (tq > 4.1) ? -0.2 : 0.4, look: (tq > 2 && tq < 3.2) ? 0.3 : 0, smile: tq > 4.2 ? -0.7 : 0});
  };
  F.camFn = F.camKeys([[0, F.v3(S.x - 0.25, S.y + 0.55, S.z - 1.2), F.v3(S.x, S.y + 0.6, S.z), 30], [7, F.v3(S.x - 0.2, S.y + 0.55, S.z - 0.95), F.v3(S.x, S.y + 0.62, S.z), 30]]);
}};

// C29 8s — she takes off the raincoat, lays it on the rock; with the jar in her arms she walks in — knees, waist, chest — breathes in, dives
C['29'] = {env: 'coast', mode: 'day', dur: 8, setup(F, E) {
  const {THREE} = F; const S = E.seat;
  const solA = makeSol(THREE, F.toon); F.addChar(solA); hugJar(F, solA, 0.08);                      // still in the raincoat
  const solB = makeSol(THREE, F.toon, {underwater: true}); F.addChar(solB); const jB = makeJar(F, 1.25, {level: 0.08}); F.addChar(jB, solB.group);
  jB.group.position.set(0, 0.68, 0.2); jB.group.rotation.set(0.25, 0, 0);
  const coat = coatProp(F); F.addChar(coat); coat.group.position.set(S.x, S.y + 0.08, S.z); coat.group.rotation.y = 2.6;
  const rings = [];
  for (let i = 0; i < 3; i++) { const r = new THREE.Mesh(new THREE.RingGeometry(0.2, 0.26, 32), new THREE.MeshBasicMaterial({color: 0xf0fbf8, side: THREE.DoubleSide, transparent: true}));
    r.rotation.x = -Math.PI / 2; F.add(r, {colorOnly: true}); rings.push(r); }
  const start = new THREE.Vector3(S.x + 0.5, 0, S.z - 0.3);
  F.onFrame = (t) => { E.update(t); const tq = F.q2(t);
    const A = tq < 1.6;
    solA.group.visible = A; solB.group.visible = !A; coat.group.visible = !A;
    if (A) { const x = start.x, z = start.z; E.focus(x, 0, z);
      solA.group.position.set(x, E.landH(x, z), z); solA.group.rotation.y = 0.4;
      solA.setHood(F.lerp(1.1, 0, F.ss((tq - 0.2) / 0.5))); solA.pose(hug({pitch: 0.2, armLx: -0.85 - 0.6 * F.ss((tq - 0.2) / 0.4) * (1 - F.ss((tq - 0.8) / 0.4))}));
      solA.setFace({mouth: 0, eyes: 'open', down: 0.4}); }
    else { const u = F.ss((tq - 2.6) / 4.3);                                 // walks from the rock into the sea
      const x = start.x + 1.1 * u, z = start.z - 3.4 * u;
      const d = z - E.shoreZ(x), ground = Math.max(-0.8, Math.min(E.landH(x, z), -0.38 + d * 0.25)), dive = F.ss((tq - 7.1) / 0.6);
      C['29']._p = new THREE.Vector3(x, ground, z);
      solB.group.position.set(x, ground - dive * 1.3, z - dive * 0.4); solB.group.rotation.set(dive * 1.1, Math.PI, 0); E.focus(x, 0, z);
      const breath = F.ss((tq - 6.6) / 0.3) * (1 - dive);
      const bob = tq < 2.6 ? (solB.pose(hug({pitch: 0.4})), 0) : solWalk(solB, tq * 1.4, {amp: 1 - 0.5 * u, over: hug({pitch: 0.1 - 0.3 * breath})});
      solB.group.position.y += bob;
      solB.setFace({mouth: breath > 0.3 && breath < 0.9 ? 1 : 0, eyes: breath > 0.5 ? 'blink' : 'open', down: u < 0.2 ? 0.5 : -0.1});
      rings.forEach((r, i) => { const a = tq - 7.35 - i * 0.12; r.userData.on = a > 0; r.position.set(x, 0.03, z - 0.4); r.scale.setScalar(1 + a * 3); r.material.opacity = Math.max(0, 1 - a * 1.3); });
    }
  };
  F.camFn = (t) => { const tq = F.q2(t); F.cam.fov = 34; F.cam.updateProjectionMatrix();
    if (tq < 1.6) { F.cam.position.set(start.x + 0.9, E.landH(start.x, start.z) + 1.0, start.z + 1.6); F.cam.lookAt(start.x, E.landH(start.x, start.z) + 0.75, start.z); }
    else if (tq < 2.6) { F.cam.position.set(S.x + 0.35, S.y + 0.35, S.z + 1.1); F.cam.lookAt(S.x + 0.1, S.y + 0.15, S.z - 1.4); }
    else { const p = C['29']._p || start; F.cam.position.set(start.x + 2.4, 1.45, start.z + 0.6); F.cam.lookAt(p.x, Math.max(-0.2, p.y + 0.55), p.z); } };
}};

// C30 ◆ 22s — the long take under the sea
C['30'] = {env: 'under', dur: 22, finish: 'under', setup(F, E) {
  const {THREE} = F, SEA = E.SEA;
  const sol = makeSol(THREE, F.toon, {underwater: true}); F.addChar(sol);
  const jar = makeJar(F, 1.25, {level: 1.0}); F.addChar(jar); jar.water.visible = false;
  const mom = makeMom(THREE, F.toon); F.addChar(mom); mom.tewak.visible = false; mom.setMask(1);
  const ku = makeKuruk(THREE, F.toon, 1.3); F.addChar(ku);
  const kuGlow = E.glow(0.8);
  const family = [], FCOL = ['orange', 'pink', 'white', 'orange', 'pink', 'orange'];
  for (let i = 0; i < 40; i++) { const k = makeKuruk(THREE, F.toon, F.rr(0.9, 1.8)); F.addChar(k);
    k.home = new THREE.Vector3(F.rr(-3.2, 3.6), SEA + F.rr(0.8, 3.2), F.rr(-3.6, -0.9)); k.ph = F.rr(0, 6.28); k.glow = E.glow(0.85); family.push(k); }
  [[-0.9, -1.2, -1.6, 2.1], [-1.6, -0.6, -2.2, 1.9], [0.3, -1.7, -1.2, 2.0], [2.2, -1.1, -1.4, 2.0], [1.0, -0.4, -2.4, 1.8]].forEach(([x, y, z, sz], i) => {
    const k = makeKuruk(THREE, F.toon, sz); F.addChar(k); k.home = new THREE.Vector3(x, y, z); k.ph = i * 1.3; k.hero = true; k.glow = E.glow(0.6); family.push(k); });
  const ab = makeAbalone(F, 1.3); F.addChar(ab); ab.group.position.set(E.abRock.position.x - 0.05, E.abRock.position.y + 0.3, E.abRock.position.z + 0.12); ab.group.rotation.set(0.25, 0.4, 0);
  const tu = makeTurtle(F, 1.0); F.addChar(tu);
  // Sol's path (key, position) — on twos
  const SP = [[0, [0.4, 1.15, -0.4]], [4.0, [0.4, 0.45, -0.4]], [9.5, [0.35, 0.3, -0.35]], [13.5, [0.35, 0.25, -0.3]], [18.0, [1.25, -1.15, -0.15]], [22, [1.3, -1.2, -0.1]]];
  const path = (tq) => { let i = 0; while (i < SP.length - 2 && tq > SP[i + 1][0]) i++; const a = SP[i], b = SP[i + 1]; const u = F.ss((tq - a[0]) / (b[0] - a[0]));
    return new THREE.Vector3().fromArray(a[1]).lerp(new THREE.Vector3().fromArray(b[1]), u); };
  // bubbles: Sol's leak (8–9.5 s burst), 엄마… (19.3 s burst), 엄마's breath every 1.6 s after arriving
  const solMouth = () => sol.head.localToWorld(new THREE.Vector3(0, -0.075, 0.16));
  E.stream(() => solMouth(), {n: 10, period: 0.2, burst: 1, size: [0.02, 0.045], speed: [0.45, 0.65], life: 2.6, t0: 1.0, t1: 4.0});
  E.stream(() => solMouth(), {n: 14, period: 0.12, burst: 1, size: [0.025, 0.06], speed: [0.5, 0.75], life: 2.8, t0: 8.0, t1: 9.6});
  E.stream(() => solMouth(), {n: 12, period: 0.06, burst: 1, size: [0.03, 0.07], speed: [0.5, 0.8], life: 2.6, t0: 19.3, t1: 19.95});
  E.stream(() => mom.head.localToWorld(new THREE.Vector3(0, -0.06, 0.14)), {n: 30, period: 1.6, burst: 15, size: [0.025, 0.075], speed: [0.5, 0.8], life: 3.0, t0: 11.0, t1: 22});
  E.stream((tt) => new THREE.Vector3(1.6 + 1.5 * Math.sin(tt), SEA + 0.6, 1.6), {n: 7, period: 0.9, burst: 1, size: [0.06, 0.12], speed: [0.35, 0.55], life: 6.5});
  F.onFrame = (t) => { const tq = F.q2(t); E.update(t);
    const sp = path(tq); E.light(sp.x, sp.y, sp.z);
    const take = F.ss((tq - 9.9) / 0.7), lead = F.ss((tq - 13.5) / 4.5), sink = 1 - F.ss((tq - 0.2) / 3.8);
    // 솔이
    sol.group.position.copy(sp).add(new THREE.Vector3(0, 0.04 * Math.sin(tq * 1.6), 0));
    sol.group.rotation.set(F.lerp(-0.2, 0.3, 1 - sink) + 0.25 * lead, F.lerp(0.2, 0.35, 1 - sink) - 0.9 * lead, 0.05);
    sol.floatHair(tq, 0.9);
    const hold = tq < 4.4;                                                    // jar in both hands until 꾸럭이 leaves
    const jarLet = F.ss((tq - 4.4) / 0.8);
    sol.pose(hold ? hug({pitch: 0.2, legL: 0.25 + 0.2 * Math.sin(tq * 3.2), legR: 0.1 - 0.2 * Math.sin(tq * 3.2), kneeL: 0.5, kneeR: 0.35, spread: 0.12}) : {
      pitch: F.lerp(0.25, -0.1, take) + (tq > 18.5 ? -0.25 : 0), yaw: F.lerp(0.3, -0.7, take) * (1 - lead * 0.6), roll: 0,
      armL: F.lerp(0.5 + 0.14 * Math.sin(tq * 1.4 + 1.0), 0.75, take), armLx: F.lerp(0.15, -0.55, take), armR: 0.6 + 0.16 * Math.sin(tq * 1.4), armRx: 0.2 + 0.1 * Math.sin(tq * 0.9),
      elbowL: F.lerp(0.65 + 0.25 * Math.sin(tq * 1.4 + 0.1), 0.15, take), elbowR: 0.7 + 0.28 * Math.sin(tq * 1.4 - 0.9), spread: 0.14,
      wristL: F.lerp(0.4 * Math.sin(tq * 1.4 - 0.8), 0, take), wristR: 0.45 * Math.sin(tq * 1.4 - 1.8),
      legL: 0.25 + 0.2 * Math.sin(F.q3(tq) * 3.2), legR: 0.1 - 0.2 * Math.sin(F.q3(tq) * 3.2), kneeL: 0.55 + 0.25 * Math.sin(F.q3(tq) * 3.2 + 0.8), kneeR: 0.35 - 0.25 * Math.sin(F.q3(tq) * 3.2 + 0.8)});
    const worried = tq > 8.0 && tq < 10.2;
    sol.setFace({mouth: tq > 19.3 ? mouthAt('sol2', 19.3, t) : (worried && tq < 9.6 ? 1 : 0), eyes: (tq > 2.6 && tq < 2.7) || (tq > 15.2 && tq < 15.3) ? 'blink' : (worried || (tq > 4.3 && tq < 8) ? 'wide' : 'open'),
                 look: tq < 8 ? -0.3 : F.lerp(0.4, -0.9, take), down: tq < 4 ? -0.4 : (tq < 8 ? 0.5 : F.lerp(0.3, -0.2, take)), smile: tq > 11 ? 0.6 : 0});
    // jar: in her arms, then let go — it drifts down slowly
    sol.group.updateMatrixWorld(true);
    const hl = new THREE.Vector3(), hr = new THREE.Vector3(); sol.arms[-1].userData.hand.getWorldPosition(hl); sol.arms[1].userData.hand.getWorldPosition(hr);
    const jp = hl.clone().add(hr).multiplyScalar(0.5);
    if (!C['30']._jar0 || tq < 4.4) C['30']._jar0 = jp.clone();
    const j0 = C['30']._jar0, jt = new THREE.Vector3(j0.x - 0.9, SEA + 0.12, j0.z - 0.7);
    jar.group.position.copy(hold ? jp : j0.clone().lerp(jt, F.ss((tq - 4.4) / 5.0)).add(new THREE.Vector3(0.12 * Math.sin((tq - 4.4) * 1.3) * (1 - F.ss((tq - 4.4) / 5.0)), 0, 0)));
    jar.group.rotation.set(0.3 + 0.6 * jarLet, 0, 0.4 * jarLet);
    // 꾸럭이: leaves the jar mouth at 4.0, glows, swims down to the family; looks back once at 6.6–7.2
    jar.group.updateMatrixWorld(true); const jm = new THREE.Vector3(0, 0.15, 0).applyMatrix4(jar.group.matrixWorld);
    const kt = F.ss((tq - 4.0) / 3.6), target = new THREE.Vector3(-1.0, -1.0, -1.7);
    const kp = jm.clone().lerp(target, kt); kp.y += Math.sin(kt * Math.PI) * 0.25 + 0.04 * Math.sin(tq * 4);
    if (tq > 7.6) kp.copy(target).add(new THREE.Vector3(0.2 * Math.sin(tq * 0.8), 0.15 * Math.sin(tq * 1.1), 0));
    ku.group.position.copy(kp); ku.group.visible = tq > 3.9;
    ku.group.rotation.set(0.3, (tq > 6.6 && tq < 7.2) ? 0.2 : -2.2, 0); ku.setMix('grey', 'orange', F.ss((tq - 4.0) / 0.6)); ku.blink(tq > 7.0 && tq < 7.1);
    kuGlow.position.copy(kp); kuGlow.material.color.set(E.GLOWC.orange); kuGlow.material.opacity = tq > 4.2 ? 0.9 * (0.7 + 0.3 * Math.sin(tq * 3)) : 0; kuGlow.userData.on = tq > 4.2;
    // family: rise from the kelp 3.5–8 s, flicker their colours like a signal; heroes greet them later
    family.forEach((k, i) => { let p;
      if (k.hero) { const r2 = F.ss((tq - 6.5 - i % 5 * 0.4) / 2.0); p = new THREE.Vector3(k.home.x + 0.15 * Math.sin(tq * 1.3 + k.ph), F.lerp(SEA, k.home.y, r2) + 0.07 * Math.sin(tq * 2.2 + k.ph), k.home.z + 0.1 * Math.cos(tq + k.ph));
        if (tq > 14) p.lerp(new THREE.Vector3(sp.x + Math.cos(i * 1.3) * 0.9, sp.y - 0.2 + Math.sin(i * 2.1) * 0.5, sp.z + Math.sin(i * 1.3) * 0.7), F.ss((tq - 14) / 4) * 0.8); }
      else { const rise = F.ss((tq - 3.5 - (i % 9) * 0.25) / 2.4); p = new THREE.Vector3(k.home.x + 0.15 * Math.sin(tq * 1.1 + k.ph), F.lerp(SEA - 0.1, k.home.y, rise) + 0.06 * Math.sin(tq * 2 + k.ph), k.home.z); }
      k.group.position.copy(p); k.group.rotation.set(0.2 * Math.sin(tq + k.ph), k.ph + tq * 0.2, 0);
      const st = FCOL[(i + Math.floor(tq * 1.5 + k.ph)) % FCOL.length]; k.setState(st);
      k.glow.position.copy(p); k.glow.material.color.set(E.GLOWC[st]); k.glow.material.opacity = (0.6 + 0.4 * Math.sin(tq * 3 + k.ph)) * F.ss((tq - 3.5) / 2); k.glow.userData.on = tq > 3.5; });
    // 엄마: glides in (9.6–10.6), takes her left hand; leads her down to the abalone; smiles behind the mask
    mom.setFace({mouth: 0, eyes: (tq > 12.3 && tq < 12.45) || (tq > 17 && tq < 17.15) ? 'blink' : 'open', smile: 1, look: 0.6});
    const kq = F.q3(tq), kk = 0.3 * Math.sin(kq * 3.6) * (1 - 0.6 * take);
    mom.group.rotation.set(F.lerp(0.95, 0.55, take) + 0.3 * lead, 0.85 - 0.6 * lead, -0.1);
    mom.pose({pitch: F.lerp(-0.45, -0.2, take), yaw: 0.25, roll: 0, armR: F.lerp(0.3, 0.75, take), armRx: F.lerp(-1.4, -0.9, take), armL: 0.15, armLx: F.lerp(0.9, 0.4, take),
              legL: -0.3 + kk, legR: -0.3 - kk, kneeL: 0.45 + kk, kneeR: 0.45 - kk});
    mom.group.position.set(0, 0, 0); mom.group.updateMatrixWorld(true);
    const mh = new THREE.Vector3(); mom.arms[1].userData.hand.getWorldPosition(mh);
    const sh = new THREE.Vector3(); sol.arms[-1].userData.hand.getWorldPosition(sh);
    const away = new THREE.Vector3(-1.4, 1.2, -1.6).multiplyScalar(1 - F.ss((tq - 8.6) / 1.9));
    mom.group.position.copy(sh.sub(mh).add(away)); mom.group.visible = tq > 8.4;
    // abalone glints, turtle crosses behind (14.5–19 s)
    const tt = F.ss((tq - 14.2) / 5.2); tu.group.position.set(F.lerp(-3.0, 4.4, tt), 0.15 + 0.2 * Math.sin(tt * 3), -1.9); tu.group.rotation.set(0.1 * Math.sin(tq), Math.PI / 2 - 0.15, 0.1 * Math.sin(tq * 1.3));
    tu.row(tq); tu.group.visible = tq > 14 && tq < 19.6;
  };
  // camera: aim points follow the actors; offsets keyed in time (one continuous take, on twos)
  const head = (c) => { const v = new THREE.Vector3(); c.head.getWorldPosition(v); return v; };
  const solC = () => sol.group.localToWorld(new THREE.Vector3(0, 0.75, 0));
  const AIM = [
    [0, () => solC().add(F.v3(0, 0.1, 0)), F.v3(1.2, -0.7, 2.6), 40], [3.6, () => solC(), F.v3(0.9, -0.3, 2.3), 40],
    [5.0, () => solC().lerp(ku.group.position, 0.5), F.v3(0.6, -0.2, 2.3), 42], [7.4, () => ku.group.position.clone().lerp(solC(), 0.35), F.v3(0.3, 0.1, 2.4), 42],
    [9.4, () => solC().add(F.v3(-0.4, 0, 0)), F.v3(1.2, 0.15, 2.4), 40], [11.0, () => solC().lerp(head(mom), 0.4), F.v3(1.0, 0.1, 2.0), 38],
    [12.2, () => head(mom), F.v3(0.5, 0.05, 0.85), 34], [13.4, () => head(mom), F.v3(0.45, 0.05, 0.8), 34],
    [15.0, () => solC().add(F.v3(0.1, -0.2, -0.3)), F.v3(1.7, 0.35, 2.4), 42], [17.8, () => solC().add(F.v3(0.1, -0.25, -0.4)), F.v3(1.5, 0.3, 2.2), 42],
    [18.9, () => head(sol), F.v3(0.35, 0.02, 0.85), 34], [20.2, () => head(sol), F.v3(0.33, 0.02, 0.8), 34],
    [22, () => solC().add(F.v3(-0.2, 0, -0.4)), F.v3(2.6, 1.6, 4.6), 46]];
  F.camFn = (t) => { const tq = F.q2(t);
    let i = 0; while (i < AIM.length - 2 && tq > AIM[i + 1][0]) i++;
    const A = AIM[i], B = AIM[i + 1], u = F.ss((tq - A[0]) / (B[0] - A[0]));
    sol.group.updateMatrixWorld(true); mom.group.updateMatrixWorld(true);
    const aim = A[1]().lerp(B[1](), u), off = A[2].clone().lerp(B[2], u);
    F.cam.position.copy(aim).add(off); F.cam.fov = F.lerp(A[3], B[3], u); F.cam.updateProjectionMatrix(); F.cam.lookAt(aim); };
}};
})();
