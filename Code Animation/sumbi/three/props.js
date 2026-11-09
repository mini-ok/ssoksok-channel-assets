// props + creatures + motion cycles for 〈숨비〉
// 물허벅 (water jar) with an optional crack; the same profile as the one on 솔이's back, scaled by s.
function makeJar(F, s = 1, opt = {}) {
  const {THREE, toon} = F, g = new THREE.Group(), parts = [], colorOnly = [];
  const prof = [[0.0, -0.09], [0.06, -0.085], [0.085, -0.03], [0.08, 0.04], [0.05, 0.08], [0.035, 0.1], [0.04, 0.11], [0.032, 0.112], [0.028, 0.1]]
    .map(([r, y]) => new THREE.Vector2(r * s, y * s));
  const body = new THREE.Mesh(new THREE.LatheGeometry(prof, 32), toon(0xa36b45)); body.material.side = THREE.DoubleSide;
  g.add(body); parts.push(body);
  // water inside (a disc at the current level), colour only
  const water = new THREE.Mesh(new THREE.CircleGeometry(0.07 * s, 24), new THREE.MeshBasicMaterial({color: 0x5e8f9a}));
  water.rotation.x = -Math.PI / 2; g.add(water); colorOnly.push(water);
  // the crack: a thin dark zigzag tube on the surface
  const crack = [];
  if (opt.crack !== false) {
    const pts = [];
    for (let k = 0; k <= 10; k++) { const u = k / 10, y = (0.03 - u * 0.1) * s, a = 0.45 + 0.045 * Math.sin(k * 2.7) + 0.02 * Math.sin(k * 5.3) + u * 0.12;
      const r = (y > 0 ? 0.08 : 0.085 - Math.max(0, -0.03 * s - y) / s * 0.4) * s + 0.0012 * s;
      pts.push(new THREE.Vector3(Math.sin(a) * r, y, Math.cos(a) * r)); }
    const c = new THREE.Mesh(new THREE.TubeGeometry(new THREE.CatmullRomCurve3(pts), 30, 0.001 * s, 4), toon(0x2a1a14));
    g.add(c); parts.push(c); crack.push(c);
  }
  const api = {group: g, parts, colorOnly, body, water,
    setLevel(u) { water.visible = u > 0.02; const y = -0.08 + 0.15 * u; water.position.y = y * s;
      const pr = [[-0.09, 0], [-0.085, 0.06], [-0.03, 0.085], [0.04, 0.08], [0.08, 0.05], [0.1, 0.035]]; let r = 0.035;
      for (let k = 0; k < pr.length - 1; k++) if (y >= pr[k][0] && y <= pr[k + 1][0]) r = pr[k][1] + (pr[k + 1][1] - pr[k][1]) * (y - pr[k][0]) / (pr[k + 1][0] - pr[k][0]);
      water.scale.setScalar(Math.max(0.01, r * 0.92) / 0.07); },
    crackTip: () => { const v = new THREE.Vector3(Math.sin(0.55) * 0.085 * s, -0.07 * s, Math.cos(0.55) * 0.085 * s); return g.localToWorld(v); }};
  api.setLevel(opt.level ?? 0.8);
  return api;
}

// 까마귀 (crow): ovoid body, head, cone beak, wings that fold/flap, fan tail; setInk(u) turns it ink black
function makeCrow(F) {
  const {THREE, toon} = F, g = new THREE.Group(), parts = [], colorOnly = [];
  const P = (m, p = g) => { p.add(m); parts.push(m); m.castShadow = true; return m; };
  const feather = toon(0x2c3140), ink = toon(0x08080c);
  const body = P(new THREE.Mesh(new THREE.SphereGeometry(0.14, 20, 14), feather)); body.scale.set(0.85, 0.8, 1.35);
  const head = new THREE.Group(); head.position.set(0, 0.1, 0.16); g.add(head);
  const sk = P(new THREE.Mesh(new THREE.SphereGeometry(0.075, 18, 12), feather), head);
  const beak = P(new THREE.Mesh(new THREE.ConeGeometry(0.03, 0.11, 10), toon(0x1d1d22)), head); beak.rotation.x = Math.PI / 2; beak.position.set(0, -0.01, 0.1);
  const eyes = [];
  for (const sx of [-1, 1]) {
    const e = new THREE.Mesh(new THREE.SphereGeometry(0.016, 10, 8), new THREE.MeshBasicMaterial({color: 0xf2efe6})); e.position.set(sx * 0.05, 0.02, 0.045); head.add(e); colorOnly.push(e);
    const pu = new THREE.Mesh(new THREE.SphereGeometry(0.009, 8, 6), new THREE.MeshBasicMaterial({color: 0x101010})); pu.position.set(sx * 0.058, 0.022, 0.056); head.add(pu); colorOnly.push(pu);
    eyes.push(e, pu);
  }
  const wings = {};
  for (const sx of [-1, 1]) {
    const pv = new THREE.Group(); pv.position.set(sx * 0.09, 0.05, 0.02); g.add(pv);
    const sh = new THREE.Shape(); sh.moveTo(0, 0); sh.lineTo(0.38, 0.03); sh.lineTo(0.42, -0.02); sh.lineTo(0.36, -0.06); sh.lineTo(0.3, -0.05);
    sh.lineTo(0.26, -0.11); sh.lineTo(0.2, -0.1); sh.lineTo(0.15, -0.16); sh.lineTo(0.08, -0.14); sh.lineTo(0, -0.12); sh.lineTo(0, 0);
    const wg = new THREE.ShapeGeometry(sh); wg.rotateX(Math.PI / 2); if (sx < 0) wg.scale(-1, 1, 1);
    const w = P(new THREE.Mesh(wg, feather), pv); w.material = feather; w.material.side = THREE.DoubleSide;
    wings[sx] = pv;
  }
  const tail = P(new THREE.Mesh(new THREE.ConeGeometry(0.08, 0.22, 4, 1, true), feather)); tail.rotation.x = -Math.PI / 2 - 0.2; tail.position.set(0, 0.0, -0.24); tail.scale.set(1, 1, 0.3);
  for (const sx of [-1, 1]) { const l = P(new THREE.Mesh(new THREE.CylinderGeometry(0.008, 0.008, 0.12, 5), toon(0x1a1a1e))); l.position.set(sx * 0.04, -0.15, 0.02); }
  const inkBlobs = [];
  for (let i = 0; i < 6; i++) { const b = new THREE.Mesh(new THREE.SphereGeometry(0.03 + 0.02 * (i % 3), 8, 6), ink); b.position.set(Math.sin(i * 2.3) * 0.11, Math.cos(i * 1.7) * 0.08, 0.05 + Math.sin(i) * 0.12);
    g.add(b); colorOnly.push(b); b.userData.on = false; inkBlobs.push(b); }
  return {group: g, parts, colorOnly, head, wings, eyes,
    flap(a, fold = 0) {               // a: wing angle (rad, up +), fold 0..1 = folded against the body
      for (const sx of [-1, 1]) { wings[sx].rotation.set(0, sx * fold * 1.3, sx * a * (1 - fold * 0.8)); wings[sx].scale.setScalar(1 - 0.45 * fold); }
    },
    setInk(u) { const c = new THREE.Color(0x2c3140).lerp(new THREE.Color(0x060608), u); feather.color.copy(c); inkBlobs.forEach(b => b.userData.on = u > 0.5); },
    blinkEyes(on) { eyes.forEach((e, i) => e.scale.setScalar(on ? (i % 2 ? 0.2 : 1) : 1)); eyes.forEach((e, i) => { if (i % 2 === 0) e.scale.set(1, on ? 0.15 : 1, 1); }); }};
}

// 바다거북 (sea turtle): domed shell with plates, flippers that row
function makeTurtle(F, s = 1) {
  const {THREE, toon} = F, g = new THREE.Group(), parts = [];
  const P = (m, p = g) => { p.add(m); parts.push(m); return m; };
  const shell = P(new THREE.Mesh(new THREE.SphereGeometry(0.45 * s, 24, 14, 0, 6.28, 0, 1.45), toon(0x6b5a3a))); shell.scale.set(1, 0.42, 1.25);
  const belly = P(new THREE.Mesh(new THREE.CircleGeometry(0.44 * s, 24), toon(0xd9c48e))); belly.rotation.x = Math.PI / 2; belly.scale.set(1, 1.25, 1); belly.position.y = 0.02 * s;
  for (let i = 0; i < 9; i++) { const a = (i / 9) * 6.28, r = i === 0 ? 0 : 0.27 * s;
    const pl = P(new THREE.Mesh(new THREE.CircleGeometry(0.11 * s, 6), toon(0x8a7448))); pl.position.set(Math.cos(a) * r * 0.9, 0.17 * s - (r > 0 ? 0.05 * s : 0), Math.sin(a) * r * 1.15);
    pl.lookAt(pl.position.clone().multiplyScalar(2).add(new THREE.Vector3(0, 0.6 * s, 0))); }
  const head = P(new THREE.Mesh(new THREE.SphereGeometry(0.12 * s, 14, 10), toon(0x9a9a6a))); head.scale.set(0.9, 0.75, 1.3); head.position.set(0, 0.03 * s, 0.62 * s);
  const fl = {};
  for (const [k, z, L] of [['fl', 0.3, 0.55], ['fr', 0.3, 0.55], ['bl', -0.38, 0.25], ['br', -0.38, 0.25]]) {
    const sx = k[1] === 'l' ? -1 : 1, pv = new THREE.Group(); pv.position.set(sx * 0.32 * s, 0.0, z * s); g.add(pv);
    const sh = new THREE.Shape(); sh.moveTo(0, -0.06 * s); sh.quadraticCurveTo(L * 0.6 * s, -0.12 * s, L * s, -0.18 * s); sh.quadraticCurveTo(L * 0.7 * s, 0.02 * s, 0, 0.06 * s);
    const gg = new THREE.ShapeGeometry(sh); gg.rotateX(Math.PI / 2); if (sx < 0) gg.scale(-1, 1, 1);
    const m = P(new THREE.Mesh(gg, toon(0x9a9a6a)), pv); m.material.side = THREE.DoubleSide; fl[k] = pv;
  }
  return {group: g, parts, colorOnly: [], row(t) { const a = Math.sin(t * 2.2); fl.fl.rotation.set(0, 0.4 * a, -0.5 * a); fl.fr.rotation.set(0, -0.4 * a, 0.5 * a);
    fl.bl.rotation.y = 0.3 * Math.sin(t * 2.2 + 1); fl.br.rotation.y = -0.3 * Math.sin(t * 2.2 + 1); }};
}

// 전복 (abalone) on a rock: ear-shaped shell with a row of holes, mother-of-pearl rim (colour only sheen)
function makeAbalone(F, s = 1) {
  const {THREE, toon} = F, g = new THREE.Group(), parts = [];
  const sh = new THREE.Mesh(new THREE.SphereGeometry(0.1 * s, 18, 10, 0, 6.28, 0, 1.2), toon(0x7a6450)); sh.scale.set(1, 0.38, 1.35); g.add(sh); parts.push(sh);
  for (let i = 0; i < 5; i++) { const h = new THREE.Mesh(new THREE.SphereGeometry(0.009 * s, 6, 4), toon(0x2a2018)); const a = -0.6 + i * 0.28;
    h.position.set(0.07 * s * Math.cos(a), 0.03 * s, 0.09 * s * Math.sin(a) + 0.01 * s); g.add(h); parts.push(h); }
  const rim = new THREE.Mesh(new THREE.TorusGeometry(0.098 * s, 0.008 * s, 5, 24), toon(0xb8d8d0)); rim.rotation.x = Math.PI / 2; rim.scale.set(1, 1.35, 1); g.add(rim); parts.push(rim);
  return {group: g, parts, colorOnly: []};
}

// ---- motion cycles (call every drawing; ph = phase in cycles)
// 솔이 run: legs swing, knees fold on the back swing, arms counter-swing, body bob + lean (returns y offset)
function solRun(sol, ph, opt = {}) {
  const a = Math.sin(ph * Math.PI * 2), c = Math.cos(ph * Math.PI * 2), amp = opt.amp ?? 1;
  const p = Object.assign({pitch: 0.05, legL: 0.75 * a * amp, legR: -0.75 * a * amp, kneeL: (0.25 + 0.9 * Math.max(0, -a)) * amp, kneeR: (0.25 + 0.9 * Math.max(0, a)) * amp,
    armLx: -0.7 * a * amp, armRx: 0.7 * a * amp, armL: 0.15, armR: 0.15, elbowLx: 0.9, elbowRx: 0.9}, opt.over || {});
  sol.pose(p);
  return 0.035 * Math.abs(c) * amp;
}
function solWalk(sol, ph, opt = {}) {
  const a = Math.sin(ph * Math.PI * 2), c = Math.cos(ph * Math.PI * 2), amp = opt.amp ?? 1;
  sol.pose(Object.assign({pitch: 0.02, legL: 0.4 * a * amp, legR: -0.4 * a * amp, kneeL: (0.1 + 0.45 * Math.max(0, -a)) * amp, kneeR: (0.1 + 0.45 * Math.max(0, a)) * amp,
    armLx: -0.3 * a * amp, armRx: 0.3 * a * amp, armL: 0.08, armR: 0.08, elbowLx: 0.3, elbowRx: 0.3}, opt.over || {}));
  return 0.012 * Math.abs(c) * amp;
}
function momWalk(mom, ph, opt = {}) {
  const a = Math.sin(ph * Math.PI * 2), amp = opt.amp ?? 1;
  mom.pose(Object.assign({pitch: 0, yaw: 0, legL: 0.38 * a * amp, legR: -0.38 * a * amp, kneeL: (0.1 + 0.4 * Math.max(0, -a)) * amp, kneeR: (0.1 + 0.4 * Math.max(0, a)) * amp,
    armR: 0.1, armRx: 0.3 * a * amp, armL: 0.1, armLx: -0.3 * a * amp}, opt.over || {}));
}
