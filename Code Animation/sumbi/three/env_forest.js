// 곶자왈 forest (the calm tone of the tech test): mossy lava floor, rocks, bent trees + high canopy, seaweed thrown up by
// the storm hanging from branches, fern fronds (painted alpha cards), wild flowers. A trail runs along z ≈ 1 from x = -10 to 26;
// the rock pool sits beside it at x = 1.5; the trail forks at x = 12 (left branch toward the sea glimpse); the crow tree at x = 18.
function buildForest(F, mode) {
  const {THREE, rr, toon, add} = F;
  const E = {};
  const SKY = new THREE.Color(0xb9d3c4); F.bg = SKY;
  F.scene.fog = new THREE.Fog(0xaccbbb, 9, 34); F.meta.fog = {type: 'lin', near: 9, far: 34}; F.DR = 45;
  const sun = new THREE.DirectionalLight(0xfff1d6, 2.6); sun.position.set(-8, 14, 6); sun.target.position.set(2, 0, -4); sun.castShadow = true;
  sun.shadow.mapSize.set(2048, 2048); sun.shadow.bias = -0.003; sun.shadow.normalBias = 0.12;
  Object.assign(sun.shadow.camera, {left: -18, right: 18, top: 18, bottom: -18, near: 1, far: 50});
  F.scene.add(sun, sun.target); F.scene.add(new THREE.HemisphereLight(0xcfe6ff, 0x3c4a2c, 0.9));
  E.focus = (x, y, z) => { sun.target.position.set(x, y, z - 2); sun.position.set(x - 10, y + 14, z + 6); };
  const onTrail = (x, z, w = 0.9) => {
    if (x > -11 && x < 27 && Math.abs(z - 1.0) < w) return true;
    if (x > 11 && x < 15 && Math.abs(z - (1.0 - (x - 11) * 1.6)) < w) return true;     // the left fork
    return false;
  };
  E.onTrail = onTrail;
  const gH = (x, z) => 0.25 * Math.sin(x * 0.7) * Math.cos(z * 0.9) + 0.15 * Math.sin(x * 2.3 + z * 1.7);
  E.groundH = (x, z) => gH(x, z) * (onTrail(x, z, 1.2) ? 0.35 : 1);
  { const g = new THREE.PlaneGeometry(70, 46, 160, 100); g.rotateX(-Math.PI / 2); g.translate(6, 0, -6);
    const p = g.attributes.position, col = [];
    const cG = new THREE.Color(0x5f7a3c), cT = new THREE.Color(0x8a7a55);
    for (let i = 0; i < p.count; i++) { const x = p.getX(i), z = p.getZ(i); p.setY(i, E.groundH(x, z));
      const c = onTrail(x, z, 0.55 + 0.15 * Math.sin(x * 3)) ? cT : cG; col.push(c.r, c.g, c.b); }
    g.setAttribute('color', new THREE.Float32BufferAttribute(col, 3)); g.computeVertexNormals();
    E.ground = add(new THREE.Mesh(g, toon(0xffffff, {vertexColors: true})), {cast: false}); }
  function rock(x, z, s) {
    const m = lavaRock(F, s, 0x3e3a3c); m.position.set(x, E.groundH(x, z) + s * 0.25, z); m.rotation.y = rr(0, 6.28); add(m);
    const moss = new THREE.Mesh(new THREE.SphereGeometry(s * 0.92, 10, 6, 0, 6.28, 0, 1.0), toon(0x6f8d3a));
    moss.scale.set(1.05, 0.55, 1.05); moss.position.copy(m.position); moss.position.y += s * 0.18; add(moss);
    return m;
  }
  for (let i = 0; i < 70; i++) { const x = rr(-14, 26), z = rr(-16, 3.2); if (onTrail(x, z, 1.3)) continue; rock(x, z, rr(0.25, 1.1)); }
  const branchTips = [];
  E.trees = [];
  function tree(x, z, h, lean) {
    const pts = [];
    for (let k = 0; k <= 6; k++) { const t = k / 6; pts.push(new THREE.Vector3(x + lean * t * t * 1.4 + 0.25 * Math.sin(t * 5 + x), E.groundH(x, z) + t * h, z + 0.3 * Math.sin(t * 3 + z))); }
    const curve = new THREE.CatmullRomCurve3(pts), r0 = rr(0.16, 0.3);
    const g = new THREE.TubeGeometry(curve, 24, r0, 7, false), p = g.attributes.position;
    for (let i = 0; i < p.count; i++) { const seg = Math.floor(i / 8) / 24, c = curve.getPoint(Math.min(1, seg));
      const v = new THREE.Vector3().fromBufferAttribute(p, i).sub(c).multiplyScalar(1.15 - 0.55 * seg).add(c); p.setXYZ(i, v.x, v.y, v.z); }
    g.computeVertexNormals(); add(new THREE.Mesh(g, toon(0x6a5a4e)));
    for (let k = 0; k < 3; k++) { const o = curve.getPoint(rr(0.05, 0.6));
      const iv = new THREE.Mesh(new THREE.SphereGeometry(r0 * 1.08, 9, 6, 0, rr(2.0, 3.4)), toon(k % 2 ? 0x3d5f2a : 0x4c7031));
      iv.scale.set(1, rr(2.5, 4.0), 1); iv.rotation.y = rr(0, 6.28); iv.position.copy(o); add(iv, {cast: false}); }
    for (let b = 0; b < 3; b++) { const t = rr(0.45, 0.85), o = curve.getPoint(t), a = rr(0, 6.28), L = rr(1.0, 2.2);
      const tip = o.clone().add(new THREE.Vector3(Math.cos(a) * L, rr(0.3, 0.9), Math.sin(a) * L * 0.6));
      const bc = new THREE.CatmullRomCurve3([o, o.clone().lerp(tip, 0.5).add(new THREE.Vector3(0, 0.25, 0)), tip]);
      add(new THREE.Mesh(new THREE.TubeGeometry(bc, 8, r0 * 0.35, 5, false), toon(0x6a5a4e))); branchTips.push(tip); }
    const top = curve.getPoint(1);
    for (let k = 0; k < 6; k++) { const b = new THREE.Mesh(new THREE.IcosahedronGeometry(rr(1.0, 1.9), 3), toon(k % 2 ? 0x3f6a2e : 0x4f7d34));
      b.position.set(top.x + rr(-1.6, 1.6), top.y + rr(-0.6, 1.0), top.z + rr(-1.4, 1.4)); add(b); }
    E.trees.push(curve); return curve;
  }
  for (let i = 0; i < 46; i++) { const x = rr(-14, 26), z = rr(-18, 3.0); if (onTrail(x, z, 1.6)) continue;
    if (x > 11 && x < 17 && z < -5) continue;                                  // keep the gap toward the sea open
    tree(x, z, rr(5.5, 8.5), rr(-1, 1)); }
  for (let i = 0; i < 55; i++) { const x = rr(-12, 26), z = rr(-16, 3); if (x > 11 && x < 17 && z < -6) continue; if (x > 15.5 && x < 21 && z > -3) continue;
    const b = new THREE.Mesh(new THREE.IcosahedronGeometry(rr(2, 3.5), 3), toon(i % 2 ? 0x355c27 : 0x426b2f)); b.position.set(x, rr(7.5, 9.5), z); add(b); }
  // seaweed hanging from branches (the storm threw it here)
  branchTips.forEach((tp, i) => { if (i % 2) return;
    const pts = []; const len = rr(0.6, 1.4); for (let k = 0; k <= 8; k++) pts.push(new THREE.Vector3(tp.x + 0.05 * Math.sin(k * 0.7), tp.y - k * len / 8, tp.z + 0.03 * k));
    const g = new THREE.TubeGeometry(new THREE.CatmullRomCurve3(pts), 16, 0.11, 4, false); g.scale(1, 1, 0.22);
    const m = new THREE.Mesh(g, toon(i % 4 ? 0x6b5a2a : 0x52602c)); m.position.set(tp.x * (1 - 1), 0, tp.z * 0); add(m, {recv: false}); });
  // ferns: painted pinnate frond cards, arched, in rosettes
  const frondTex = canvasTex(F, 128, 512, (x) => {
    x.clearRect(0, 0, 128, 512); x.fillStyle = '#ffffff'; x.strokeStyle = '#ffffff';
    x.lineWidth = 5; x.beginPath(); x.moveTo(64, 510); x.lineTo(64, 6); x.stroke();
    for (let k = 0; k < 24; k++) { const y = 490 - k * 20, L = 54 * Math.sin(Math.min(1, (k + 2) / 26) * Math.PI) ** 0.8;
      for (const sx of [-1, 1]) { x.beginPath(); x.moveTo(64, y); x.quadraticCurveTo(64 + sx * L * 0.6, y - 4, 64 + sx * L, y - 16);
        x.quadraticCurveTo(64 + sx * L * 0.55, y + 4, 64, y + 7); x.fill(); } }
  });
  frondTex.premultiplyAlpha = false;
  const frondGeo = (() => { const g = new THREE.PlaneGeometry(0.28, 1.0, 1, 10); g.translate(0, 0.5, 0); const p = g.attributes.position;
    for (let i = 0; i < p.count; i++) { const u = p.getY(i); p.setZ(i, -0.42 * u * u); p.setY(i, u * (1 - 0.18 * u)); } g.computeVertexNormals(); return g; })();
  const frondMats = [0x6e9a3e, 0x89ad4a, 0x5f8a36].map(c => toon(c, {map: frondTex, alphaTest: 0.5, side: THREE.DoubleSide}));
  function fern(x, z, s) {
    const n = 7 + Math.floor(rr(0, 4));
    for (let k = 0; k < n; k++) { const m = new THREE.Mesh(frondGeo, frondMats[k % 3]);
      m.rotation.set(rr(-0.25, 0.1), (k / n) * 6.28 + rr(-0.2, 0.2), 0, 'YXZ'); m.scale.setScalar(s * rr(0.8, 1.2));
      m.position.set(x, E.groundH(x, z) + 0.03, z); add(m, {recv: true}); }
  }
  for (let i = 0; i < 150; i++) { const x = rr(-14, 26), z = rr(-12, 3.6); if (onTrail(x, z, 1.1)) continue; fern(x, z, rr(0.5, 1.1)); }
  for (let i = 0; i < 260; i++) { const x = rr(-14, 26), z = rr(-12, 4); if (onTrail(x, z, 0.7)) continue;
    const f = new THREE.Mesh(new THREE.CircleGeometry(rr(0.05, 0.1), 7), toon(i % 3 ? 0xfdf6e4 : 0xffd84a));
    f.rotation.x = -Math.PI / 2 + rr(-0.3, 0.3); f.position.set(x, E.groundH(x, z) + 0.15, z); add(f, {cast: false}); }
  for (let i = 0; i < 120; i++) { const x = rr(-14, 26), z = rr(-14, 4); if (onTrail(x, z, 1.0)) continue; const s2 = rr(0.15, 0.45);
    const c = new THREE.Mesh(new THREE.SphereGeometry(s2, 8, 5), toon(i % 3 ? 0x56762f : 0x7c9a3f)); c.scale.set(1.4, 0.45, 1.2); c.position.set(x, E.groundH(x, z) + 0.05, z); add(c); }

  // ---- the rock pool (바위 웅덩이): a mossy rock with a hollow of sea water
  const PX = 1.5, PZ = -0.25; const py = E.groundH(PX, PZ);
  { const g = new THREE.TorusGeometry(0.42, 0.24, 12, 28); g.rotateX(Math.PI / 2); const p = g.attributes.position;
    for (let i = 0; i < p.count; i++) { const v = new THREE.Vector3().fromBufferAttribute(p, i); const k = 1 + 0.12 * Math.sin(v.x * 9 + v.z * 7); p.setXYZ(i, v.x * k, v.y * 0.9 + 0.03 * Math.sin(v.z * 11), v.z * k); }
    g.computeVertexNormals();
    const rim = new THREE.Mesh(g, toon(0x3e3a3c)); rim.position.set(PX, py + 0.2, PZ); add(rim);
    const mossR = new THREE.Mesh(new THREE.TorusGeometry(0.46, 0.16, 8, 24, 3.6), toon(0x6f8d3a)); mossR.rotation.set(Math.PI / 2, 0, 1.0); mossR.position.set(PX, py + 0.34, PZ); add(mossR);
    const bottom = new THREE.Mesh(new THREE.CircleGeometry(0.45, 24), toon(0x2e3a3a)); bottom.rotation.x = -Math.PI / 2; bottom.position.set(PX, py + 0.06, PZ); add(bottom);
    const water = new THREE.Mesh(new THREE.CircleGeometry(0.43, 32), new THREE.MeshToonMaterial({color: 0x7fb2b4, transparent: true, opacity: 0.55, gradientMap: F.ramp}));
    water.rotation.x = -Math.PI / 2; water.position.set(PX, py + 0.27, PZ); add(water, {colorOnly: true});
    E.poolWater = water; }
  E.pool = new THREE.Vector3(PX, py + 0.27, PZ);
  // ---- the fork sign: two trails; a little cairn of lava stones at the split
  E.fork = new THREE.Vector3(11.6, E.groundH(11.6, 1.0), 1.0);
  for (let k = 0; k < 4; k++) { const m = lavaRock(F, 0.16 - k * 0.03, 0x403b3d, {flat: 0.8}); m.position.set(12.5, E.groundH(12.5, 2.0) + 0.08 + k * 0.12, 2.0); add(m); }
  // ---- the crow tree: a bare low branch over the trail
  E.crowBranch = new THREE.Vector3(18.2, 2.3, 0.4);
  { const bc = new THREE.CatmullRomCurve3([new THREE.Vector3(19.6, 1.2, -0.6), new THREE.Vector3(18.8, 2.1, 0.0), new THREE.Vector3(17.6, 2.35, 0.6)]);
    add(new THREE.Mesh(new THREE.TubeGeometry(bc, 10, 0.06, 6, false), toon(0x5a4a40)));
    tree(19.8, -0.9, 6.5, -0.4); }
  // ---- the sea glimpse through the gap at x 12–17 (bright, beyond the fog)
  { const tex = canvasTex(F, 256, 256, (x) => { const g = x.createLinearGradient(0, 0, 0, 256); g.addColorStop(0, '#d5ebee'); g.addColorStop(0.55, '#e4f4f2');
      g.addColorStop(0.56, '#9fd0d8'); g.addColorStop(0.62, '#5aa6c4'); g.addColorStop(1, '#3f8db0'); x.fillStyle = g; x.fillRect(0, 0, 256, 256);
      x.strokeStyle = 'rgba(255,255,255,0.7)'; x.lineWidth = 2; for (let i = 0; i < 14; i++) { const y = 150 + i * 7; x.beginPath(); x.moveTo(20 + (i * 37) % 120, y); x.lineTo(60 + (i * 53) % 180, y); x.stroke(); } });
    const sea = new THREE.Mesh(new THREE.PlaneGeometry(90, 12), new THREE.MeshBasicMaterial({map: tex, fog: false})); sea.position.set(14.3, 3.2, -30); add(sea, {colorOnly: true});
    sea.userData.on = false; E.seaGlimpse = sea; }
  // a vine across the trail at x = 6 (catches the raincoat in C15)
  { const vc = new THREE.CatmullRomCurve3([new THREE.Vector3(6.2, 2.2, -0.4), new THREE.Vector3(6.0, 0.9, 0.7), new THREE.Vector3(5.9, 1.0, 1.4), new THREE.Vector3(6.1, 2.4, 2.4)]);
    E.vine = add(new THREE.Mesh(new THREE.TubeGeometry(vc, 24, 0.02, 5, false), toon(0x4c6a2c))); }
  E.update = () => {};
  return E;
}
