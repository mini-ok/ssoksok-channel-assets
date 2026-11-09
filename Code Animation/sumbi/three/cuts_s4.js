// 시퀀스 7. 숨비 (C31–C33): at the surface, day
(() => {
const C = window.CUTS;
const PX = 1.2, PZ = -9.0;                       // where they surface
function surfacePair(F, E) {
  const {THREE} = F;
  const sol = makeSol(THREE, F.toon, {underwater: true}); F.addChar(sol);
  const mom = makeMom(THREE, F.toon); F.addChar(mom);
  return {sol, mom};
}
// keep the tewak floating at a world point (it is parented to 엄마)
function floatTewak(F, mom, wp) { mom.group.updateMatrixWorld(true); const lp = mom.group.worldToLocal(wp.clone()); mom.tewak.position.copy(lp); mom.tewak.rotation.set(0, 0, 0); }

// C31 ★ 5s — MCU: 엄마 bursts up holding 솔이; 솔이 clings to the tewak. 엄마: "숨, 같이 쉬자."
C['31'] = {env: 'coast', mode: 'day', dur: 5, setup(F, E) {
  const {THREE} = F; const {sol, mom} = surfacePair(F, E);
  const drops = []; for (let i = 0; i < 26; i++) { const m = new THREE.Mesh(new THREE.SphereGeometry(0.012 + 0.006 * (i % 3), 8, 6), new THREE.MeshBasicMaterial({color: 0xf2fbfa})); F.add(m, {colorOnly: true}); drops.push(m); }
  const rings = []; for (let i = 0; i < 3; i++) { const r = new THREE.Mesh(new THREE.RingGeometry(0.3, 0.36, 40), new THREE.MeshBasicMaterial({color: 0xf0fbf8, side: THREE.DoubleSide, transparent: true})); r.rotation.x = -Math.PI / 2; F.add(r, {colorOnly: true}); rings.push(r); }
  F.onFrame = (t) => { E.update(t); const tq = F.q2(t); E.focus(PX, 0, PZ);
    const up = F.ss(tq / 0.45), h = E.seaH(PX, PZ, tq);
    mom.group.position.set(PX + 0.12, h - 1.28 - 0.6 * (1 - up) + 0.03 * Math.sin(tq * 2), PZ - 0.08); mom.group.rotation.set(0, -0.35, 0);
    mom.setMask(1 - F.ss((tq - 1.3) / 0.35));
    mom.pose({pitch: -0.05, yaw: -0.25 + 0.15 * F.ss((tq - 2.0) / 0.4), armR: 0.2, armRx: -0.3, armL: -0.15, armLx: 0.5, legL: 0.2 * Math.sin(tq * 3), legR: -0.2 * Math.sin(tq * 3), kneeL: 0.4, kneeR: 0.4});
    mom.setFace({mouth: mouthAt('mom2', 2.3, t), eyes: tq > 1.9 && tq < 2.0 ? 'blink' : 'open', smile: 1, look: -0.4});
    sol.group.position.set(PX - 0.22, h - 0.86 - 0.5 * (1 - up) + 0.03 * Math.sin(tq * 2 + 1), PZ + 0.12); sol.group.rotation.set(0.1, 0.4, 0);
    sol.floatHair(0, 0); sol.setHood && 0;
    const gasp = tq > 0.45 && tq < 1.2;
    sol.pose({pitch: gasp ? -0.25 : 0.05, yaw: tq > 2.0 ? -0.5 : 0, armL: 0.25, armLx: -1.1, armR: -0.1, armRx: -1.25, elbowL: 0.2, elbowR: -0.5, elbowLx: 0.6, elbowRx: 0.7, legL: 0.3 * Math.sin(tq * 4), legR: -0.3 * Math.sin(tq * 4), kneeL: 0.5, kneeR: 0.5});
    sol.setFace({mouth: gasp ? 2 : (tq > 1.2 && tq < 1.8 ? 1 : 0), eyes: gasp ? 'blink' : 'wide', look: tq > 2.0 ? -0.8 : 0, down: -0.1, smile: tq > 3.9 ? 0.5 : 0});
    floatTewak(F, mom, new THREE.Vector3(PX - 0.12, h + 0.06, PZ + 0.38));
    drops.forEach((d, i) => { const a = tq - 0.3 - (i % 5) * 0.03; d.userData.on = a > 0 && a < 0.8; const ang = i * 0.9;
      d.position.set(PX + Math.cos(ang) * (0.25 + a * 0.6), h + 0.2 + 2.2 * a - 4.9 * a * a, PZ + Math.sin(ang) * (0.2 + a * 0.5)); });
    rings.forEach((r, i) => { const a = tq - 0.35 - i * 0.18; r.userData.on = a > 0 && a < 1.6; r.position.set(PX, h + 0.03, PZ); r.scale.setScalar(1 + a * 2.2); r.material.opacity = Math.max(0, 1 - a * 0.7); });
  };
  F.camFn = F.camKeys([[0, F.v3(PX + 0.25, 0.3, PZ + 1.75), F.v3(PX - 0.05, 0.22, PZ), 34], [5, F.v3(PX + 0.2, 0.3, PZ + 1.55), F.v3(PX - 0.05, 0.24, PZ), 34]], {shake: (tq) => tq < 0.8 ? 0.01 : 0.002});
}};

// C32 4s — CU two-shot: 엄마's 숨비소리 — then 솔이: "호오―이." Her first.
C['32'] = {env: 'coast', mode: 'day', dur: 4, setup(F, E) {
  const {THREE} = F; const {sol, mom} = surfacePair(F, E);
  F.onFrame = (t) => { E.update(t + 5); const tq = F.q2(t); E.focus(PX, 0, PZ); const h = E.seaH(PX, PZ, tq + 5);
    mom.group.position.set(PX + 0.12, h - 1.28 + 0.03 * Math.sin(tq * 2), PZ - 0.08); mom.group.rotation.set(0, -0.35, 0); mom.setMask(0);
    const mW = tq > 0.3 && tq < 1.4, sW = tq > 1.9 && tq < 3.1, joy = tq > 3.15;
    mom.pose({pitch: mW ? -0.3 : 0.05, yaw: mW ? 0.1 : -0.35, armR: 0.2, armRx: -0.3, armL: -0.15, armLx: 0.5, legL: 0, legR: 0, kneeL: 0.4, kneeR: 0.4});
    mom.setFace({mouth: mW ? 1 : 0, eyes: mW ? 'blink' : 'open', smile: 1, look: mW ? 0 : -0.5});
    sol.group.position.set(PX - 0.22, h - 0.86 + 0.03 * Math.sin(tq * 2 + 1), PZ + 0.12); sol.group.rotation.set(0.1, 0.4, 0);
    sol.pose({pitch: sW ? -0.35 : (joy ? -0.05 : 0.05), yaw: mW ? -0.5 : (joy ? -0.45 : 0), armL: 0.25, armLx: -1.1, armR: -0.1, armRx: -1.25, elbowL: 0.2, elbowR: -0.5, elbowLx: 0.6, elbowRx: 0.7, kneeL: 0.5, kneeR: 0.5});
    sol.setFace({mouth: sW ? 'o' : (joy ? 2 : 0), eyes: joy ? 'blink' : (sW ? 'open' : 'wide'), look: mW || joy ? -0.8 : 0, down: sW ? -0.5 : 0, smile: joy ? 1 : 0});
    floatTewak(F, mom, new THREE.Vector3(PX - 0.12, h + 0.06, PZ + 0.38));
  };
  F.camFn = F.camKeys([[0, F.v3(PX - 0.05, 0.38, PZ + 1.15), F.v3(PX - 0.05, 0.32, PZ), 32], [4, F.v3(PX - 0.06, 0.36, PZ + 1.0), F.v3(PX - 0.05, 0.32, PZ), 32]]);
}};

// C33 ◆ 6s — ELS crane up: across the sea haenyeo answer with their 숨비소리; orange glints under the water;
// orange tewaks on the wide sea; on the rock, the yellow raincoat flutters
C['33'] = {env: 'coast', mode: 'day', dur: 6, setup(F, E) {
  const {THREE} = F; const {sol, mom} = surfacePair(F, E);
  const others = [];
  [[-6, -14], [7, -16], [-11, -20], [3, -22], [12, -11]].forEach(([x, z], i) => { const m = makeMom(THREE, F.toon); F.addChar(m); m.setMask(0); others.push({m, x, z, ph: i * 1.7}); });
  const glints = [];
  for (let i = 0; i < 24; i++) { const s = new THREE.Sprite(new THREE.SpriteMaterial({map: canvasTex(F, 64, 64, (x) => { const g = x.createRadialGradient(32, 32, 0, 32, 32, 32);
    g.addColorStop(0, 'rgba(255,190,90,1)'); g.addColorStop(0.4, 'rgba(255,150,60,0.5)'); g.addColorStop(1, 'rgba(255,140,40,0)'); x.fillStyle = g; x.fillRect(0, 0, 64, 64); }),
    transparent: true, depthWrite: false, blending: THREE.AdditiveBlending})); F.add(s, {colorOnly: true});
    glints.push({s, x: PX + F.rr(-6, 6), z: PZ + F.rr(-6, 4), ph: F.rr(0, 6)}); }
  const coat = (() => { const c = makeSol(THREE, F.toon); c.head.visible = false; c.jar.visible = false; c.strap.visible = false;
    c.parts.forEach(m => { const h = m.material && m.material.color && m.material.color.getHex(); if ([0xfddcc0, 0x384470, 0x2b2a3d].map(k => new THREE.Color(k).getHex()).includes(h)) m.visible = false; });
    F.addChar(c); c.group.rotation.x = -Math.PI / 2; c.group.scale.set(1, 1, 0.35); const S = E.seat; c.group.position.set(S.x, S.y + 0.12, S.z + 0.5); return c; })();
  F.onFrame = (t) => { E.update(t + 9); const tq = F.q2(t); E.focus(PX, 0, PZ); const h = E.seaH(PX, PZ, tq + 9);
    mom.group.position.set(PX + 0.12, h - 1.28, PZ - 0.08); mom.group.rotation.set(0, -0.35, 0); mom.setMask(0);
    mom.pose({pitch: 0, yaw: -0.3, armR: 0.2, armRx: -0.3, armL: -0.15, armLx: 0.5, kneeL: 0.4, kneeR: 0.4}); mom.setFace({mouth: 0, eyes: 'open', smile: 1});
    sol.group.position.set(PX - 0.22, h - 0.86, PZ + 0.12); sol.group.rotation.set(0.0, 0.1, 0);
    sol.pose({pitch: -0.2, yaw: 0.3 * Math.sin(tq * 0.8), armL: 0.25, armLx: -1.1, armR: -0.1, armRx: -1.25, elbowL: 0.2, elbowR: -0.5, elbowLx: 0.6, elbowRx: 0.7, legL: 0.15 * Math.sin(tq * 3), legR: -0.15 * Math.sin(tq * 3), kneeL: 0.3, kneeR: 0.3});
    sol.setFace({mouth: 0, eyes: 'open', smile: 1, look: 0.4});
    floatTewak(F, mom, new THREE.Vector3(PX - 0.12, h + 0.06, PZ + 0.38));
    others.forEach(({m, x, z, ph}, i) => { const hh = E.seaH(x, z, tq + 9); m.group.position.set(x, hh - 1.3, z); m.group.rotation.set(0, Math.atan2(PX - x, PZ - z), 0);
      const call = tq > 1.0 + i * 0.7 && tq < 1.8 + i * 0.7; m.pose({pitch: call ? -0.3 : 0, armL: 0.3, armLx: -0.6, armR: 0.3, armRx: -0.6}); m.setFace({mouth: call ? 1 : 0, eyes: call ? 'blink' : 'open', smile: 0.8});
      floatTewak(F, m, new THREE.Vector3(x + 0.35, hh + 0.06, z + 0.3)); });
    glints.forEach((g) => { const on = Math.sin(tq * 2.5 + g.ph) > 0.4; g.s.userData.on = on; g.s.position.set(g.x, -0.25, g.z); const s2 = 0.5 + 0.4 * Math.sin(tq * 5 + g.ph); g.s.scale.set(s2, s2 * 0.6, 1); });
    coat.pose({armL: 0.9 + 0.25 * Math.sin(tq * 7), armR: 0.7 + 0.2 * Math.sin(tq * 6 + 1), armLx: 0.2, armRx: -0.1, elbowL: 0.4 + 0.3 * Math.sin(tq * 8), elbowR: -0.2});
    coat.group.rotation.z = 0.05 * Math.sin(tq * 9);
  };
  F.camFn = F.camKeys([[0, F.v3(PX + 0.6, 0.45, PZ + 2.2), F.v3(PX, 0.3, PZ), 36], [1.2, F.v3(PX + 0.8, 1.2, PZ + 3.2), F.v3(PX, 0.2, PZ - 1), 38],
                       [6, F.v3(PX + 4, 8, PZ + 18), F.v3(PX - 1, 0, PZ - 14), 44]]);
}};
})();
