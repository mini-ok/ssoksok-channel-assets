// Jeju basalt coast: sky, clouds, moving sea with foam, black lava shore, 불턱 (stone ring + fire + smoke), green land, forest edge.
// Coordinates: sea level y = 0, the sea lies toward -z (horizon), land toward +z; shoreline wiggles around z = 0.
function buildCoast(F, mode = 'dawn') {
  const {THREE, rr, toon, add} = F;
  const P = {
    dawn:  {sky: [[-0.1, 0x8d9aa2], [0.0, 0xd9b8a0], [0.05, 0xc9b6aa], [0.25, 0x8f9aa8], [0.7, 0x5d6b7e]], fog: 0xb3aea8, fogN: 30, fogF: 220,
            sea: 0x3f5f6e, seaHi: 0x8fa8ad, foam: 0xe8e6de, sun: [0xffd2a8, 1.6, [-60, 18, -120]], hemi: [0xc8cdd6, 0x3a3630, 1.2], amp: 0.22, cloud: 0x9aa0a8, cloudHi: 0xe8c9b0},
    day:   {sky: [[-0.1, 0x9cc6d2], [0.0, 0xd8eef0], [0.08, 0xbfe0ec], [0.35, 0x7fb6dc], [0.8, 0x4f8fcf]], fog: 0xc6e2e6, fogN: 40, fogF: 260,
            sea: 0x2f7f98, seaHi: 0x6fc4c8, foam: 0xf4fbf8, sun: [0xfff4dc, 2.4, [-40, 60, -60]], hemi: [0xd8eeff, 0x40504a, 1.25], amp: 0.12, cloud: 0xe8f1f6, cloudHi: 0xffffff},
    storm: {sky: [[-0.1, 0x10161e], [0.0, 0x26303c], [0.1, 0x1a222c], [0.5, 0x0d1218], [0.9, 0x080b10]], fog: 0x1c242e, fogN: 10, fogF: 90,
            sea: 0x16222c, seaHi: 0x3c5260, foam: 0x9aa6ae, sun: [0x9fb4cc, 0.9, [30, 40, -20]], hemi: [0x4a5a70, 0x101418, 0.9], amp: 0.6, cloud: 0x1e2630, cloudHi: 0x3a4656},
  }[mode];
  const E = {mode, P};
  F.scene.fog = new THREE.Fog(P.fog, P.fogN, P.fogF);
  F.meta.fog = {type: 'lin', near: P.fogN, far: P.fogF}; F.DR = 200;
  skyDome(F, P.sky);
  const sun = new THREE.DirectionalLight(P.sun[0], P.sun[1]); sun.position.set(...P.sun[2]); sun.castShadow = true;
  sun.shadow.mapSize.set(2048, 2048); sun.shadow.bias = -0.002; sun.shadow.normalBias = 0.06;
  Object.assign(sun.shadow.camera, {left: -14, right: 14, top: 14, bottom: -14, near: 1, far: 400});
  F.scene.add(sun, sun.target); E.sun = sun;
  F.scene.add(new THREE.HemisphereLight(P.hemi[0], P.hemi[1], P.hemi[2]));
  E.focus = (x, y, z) => { sun.target.position.set(x, y, z); sun.position.set(x + P.sun[2][0] * 0.2, y + P.sun[2][1] * 0.6, z + P.sun[2][2] * 0.2); };
  E.focus(0, 0, 2);

  // ---- clouds: painted cel cloud cards on the horizon (colour only)
  const cloudTex = (k) => canvasTex(F, 1024, 256, (x, w, h) => {
    let sd = 100 + k * 17; const r = () => { sd = (sd * 16807) % 2147483647; return (sd - 1) / 2147483646; };
    const shade = '#' + new THREE.Color(P.cloud).getHexString(), hi = '#' + new THREE.Color(P.cloudHi).getHexString();
    // a long band: flat-ish bottom, a top of small round lumps (bigger in the middle), lit from the dawn side
    const y0 = 175, L = 100 + r() * 90, R2 = 920 - r() * 90, lumps = [];
    for (let px = L; px <= R2; px += 22 + r() * 16) { const u = (px - L) / (R2 - L); lumps.push([px, y0 - 18 - 48 * Math.sin(u * Math.PI) ** 0.8 * (0.6 + 0.5 * r()), 16 + 30 * Math.sin(u * Math.PI) * (0.6 + 0.6 * r())]); }
    x.fillStyle = shade;
    for (const [cx, cy, cr] of lumps) { x.beginPath(); x.arc(cx, cy, cr, 0, 7); x.fill(); }
    x.beginPath(); x.moveTo(L, y0); for (const [cx, cy] of lumps) x.lineTo(cx, cy + 4); x.lineTo(R2, y0); x.quadraticCurveTo((L + R2) / 2, y0 + 12, L, y0); x.fill();
    x.globalCompositeOperation = 'source-atop'; x.fillStyle = hi;
    for (const [cx, cy, cr] of lumps) { x.beginPath(); x.arc(cx - cr * 0.25, cy - cr * 0.35, cr * 0.82, 0, 7); x.fill(); }
    x.globalCompositeOperation = 'source-over';
  });
  const cloudTex0 = cloudTex; const cloudTexP = (k) => { const t = cloudTex0(k); t.premultiplyAlpha = true; return t; };
  E.clouds = [];
  for (let i = 0; i < 14; i++) {
    const m = new THREE.Mesh(new THREE.PlaneGeometry(1, 0.25), new THREE.MeshBasicMaterial({map: cloudTexP(i), premultipliedAlpha: true, transparent: true, fog: false, depthWrite: false,
      opacity: mode === 'storm' ? 0.9 : 0.92}));
    const a = rr(-1.4, 1.4), d = rr(210, 270), s = rr(120, 230);
    m.scale.set(s, s * rr(0.6, 1.0), 1); m.position.set(Math.sin(a) * d, rr(18, mode === 'day' ? 80 : 70), -Math.cos(a) * d); m.lookAt(0, m.position.y, 0);
    m.renderOrder = -9; add(m, {colorOnly: true}); E.clouds.push(m);
  }
  // ---- distant headlands / 오름 silhouettes
  for (const [x, z, s, c] of [[-150, -150, 30, 0x4e5d63], [-95, -180, 18, 0x5a6870], [170, -140, 26, 0x4a585e], [120, -190, 14, 0x5d6b72]]) {
    const g = new THREE.SphereGeometry(s, 24, 12, 0, 6.28, 0, 1.2); g.scale(2.2, 0.55, 1.2);
    const m = new THREE.Mesh(g, toon(mode === 'day' ? 0x5f7f6a : c)); m.position.set(x, -2, z); add(m, {cast: false});
  }

  // ---- sea: displaced grid near the shore + flat far plane
  const SN = 260, SW = 140;
  const sg = new THREE.PlaneGeometry(SW, SW, SN, SN); sg.rotateX(-Math.PI / 2); sg.translate(0, 0, -SW / 2 + 12);
  const sc = new Float32Array(sg.attributes.position.count * 3); sg.setAttribute('color', new THREE.BufferAttribute(sc, 3));
  const seaMat = toon(0xffffff, {vertexColors: true}); seaMat.side = THREE.DoubleSide;
  const sea = add(new THREE.Mesh(sg, seaMat), {cast: false}); sea.userData.noLine = true;
  const far = new THREE.Mesh(new THREE.PlaneGeometry(1200, 1200), toon(P.sea)); far.rotation.x = -Math.PI / 2; far.position.set(0, -0.05, -600);
  add(far, {cast: false}); far.userData.noLine = true;
  const base = Float32Array.from(sg.attributes.position.array);
  const cSea = new THREE.Color(P.sea), cHi = new THREE.Color(P.seaHi), cFoam = new THREE.Color(P.foam), tmp = new THREE.Color();
  const shoreZ = (x) => 0.6 * Math.sin(x * 0.23) + 0.35 * Math.sin(x * 0.61 + 1.3);
  E.shoreZ = shoreZ;
  const WAVES = [[0.93, -0.37, 0.6, 0.41, 0], [0.31, 0.95, 0.55, 0.67, 1.7], [-0.62, 0.78, 0.45, 1.13, 4.1], [0.12, 0.99, 0.3, 1.87, 2.3], [0.81, 0.59, 0.22, 2.71, 5.5], [-0.97, 0.24, 0.15, 3.9, 0.9]];
  E.seaH = (x, z, t) => {
    let h = 0; for (const [dx, dz, a, k, ph] of WAVES) h += a * Math.sin((x * dx + z * dz) * k - t * (0.9 + 0.55 * Math.sqrt(k) * 1.4) + ph);
    return h * P.amp * Math.min(1, 0.35 + Math.max(0, -z) * 0.08);
  };
  E.updateSea = (t) => {
    const p = sg.attributes.position;
    for (let i = 0; i < p.count; i++) {
      const x = base[i * 3], z = base[i * 3 + 2];
      const h = E.seaH(x, z, t); p.setY(i, h);
      const nz = Math.sin(x * 0.37 + z * 0.23 + t * 0.2) * Math.sin(x * 0.11 - z * 0.41 + 1.3) + 0.5 * Math.sin(x * 1.3 + z * 0.7 - t * 0.5);
      const crest = Math.max(0, h / (P.amp * 1.4) - 0.45 + 0.45 * nz);
      const dShore = z - shoreZ(x);                                  // < 0 in the sea
      const surge = 0.5 + 0.5 * Math.sin(t * 1.3 + x * 0.3);
      const foam = (dShore > -0.25 - surge * 0.4 + 0.2 * Math.sin(x * 1.7 + z * 2.9) ? 1 : 0) * (Math.sin(x * 3.1 + z * 2.3 + t * 2) * Math.sin(x * 0.9 - z * 1.7) > 0.05 ? 1 : 0);
      tmp.copy(cSea).lerp(cHi, Math.min(1, crest * 1.2)); if (crest > 0.95 || foam) tmp.copy(cFoam);
      const fd = Math.min(1, Math.max(0, -z) / 90); tmp.lerp(new THREE.Color(P.fog), fd * 0.35);
      sc[i * 3] = tmp.r; sc[i * 3 + 1] = tmp.g; sc[i * 3 + 2] = tmp.b;
    }
    p.needsUpdate = true; sg.attributes.color.needsUpdate = true; sg.computeVertexNormals();
  };

  // ---- black lava shore: a land shelf + rocks along the waterline
  const lg = new THREE.PlaneGeometry(160, 70, 200, 90); lg.rotateX(-Math.PI / 2); lg.translate(0, 0, 35);
  { const p = lg.attributes.position;
    for (let i = 0; i < p.count; i++) { const x = p.getX(i), z = p.getZ(i), d = z - shoreZ(x);
      const rise = Math.min(1, Math.max(0, d / 6));
      p.setY(i, -0.6 + 1.1 * Math.min(1, Math.max(0, (d + 0.5) / 2.5)) + 0.25 * rise * Math.sin(x * 0.9) * Math.cos(z * 1.1) + 0.12 * Math.sin(x * 3.1 + z * 2.7) + Math.max(0, d - 14) * 0.08); } }
  lg.computeVertexNormals();
  const landCol = new Float32Array(lg.attributes.position.count * 3);
  { const p = lg.attributes.position, cB = new THREE.Color(0x2d2b2e), cG = new THREE.Color(mode === 'storm' ? 0x1e2a22 : 0x5d7a3e), cG2 = new THREE.Color(mode === 'storm' ? 0x223024 : 0x6f8a45);
    for (let i = 0; i < p.count; i++) { const d = p.getZ(i) - shoreZ(p.getX(i)); const g2 = Math.min(1, Math.max(0, (d - 9 + 2 * Math.sin(p.getX(i) * 0.4)) / 3));
      const c = cB.clone().lerp(Math.sin(p.getX(i) * 1.7 + p.getZ(i)) > 0 ? cG : cG2, g2); landCol[i * 3] = c.r; landCol[i * 3 + 1] = c.g; landCol[i * 3 + 2] = c.b; } }
  lg.setAttribute('color', new THREE.BufferAttribute(landCol, 3));
  const land = add(new THREE.Mesh(lg, toon(0xffffff, {vertexColors: true})), {cast: false});
  E.landH = (x, z) => { const d = z - shoreZ(x); const rise = Math.min(1, Math.max(0, d / 6));
    return -0.6 + 1.1 * Math.min(1, Math.max(0, (d + 0.5) / 2.5)) + 0.25 * rise * Math.sin(x * 0.9) * Math.cos(z * 1.1) + 0.12 * Math.sin(x * 3.1 + z * 2.7) + Math.max(0, d - 14) * 0.08; };
  const rockCols = [0x2a282b, 0x333034, 0x242226];
  E.rocks = [];
  for (let i = 0; i < 150; i++) {
    const x = rr(-45, 45), d = rr(-3.2, 5.5), z = shoreZ(x) + d, s = rr(0.25, 1.3) * (d < 0 ? 1.1 : 0.9);
    if (Math.abs(x - 4) < 2.6 && Math.abs(z - 5) < 2.6) continue;              // keep the 불턱 clear
    if (Math.abs(x + 1.5) < 1.2 && Math.abs(d - 1.2) < 1.0) continue;          // 솔이's rock seat stays clean
    const m = lavaRock(F, s, rockCols[i % 3], {flat: rr(0.45, 0.8)}); m.position.set(x, E.landH(x, z) * (d > 0 ? 1 : 0) + (d < 0 ? -0.15 : 0.05), z);
    m.rotation.y = rr(0, 6.28); add(m); E.rocks.push(m);
  }
  // big black cliffs at both ends of the cove
  for (const [x, z, s] of [[-30, 2, 9], [-22, -4, 6], [34, 1, 10], [26, -5, 5.5]]) {
    const m = lavaRock(F, s, 0x262427, {flat: 0.9, detail: 2}); m.position.set(x, s * 0.25, z); add(m);
  }
  // 솔이's rock (where she sits facing away from the sea, C5–7, and later C27–29)
  const seat = lavaRock(F, 0.75, 0x302e31, {flat: 0.5}); seat.position.set(-1.5, E.landH(-1.5, shoreZ(-1.5) + 1.2) + 0.05, shoreZ(-1.5) + 1.2); add(seat);
  E.seat = new THREE.Vector3(-1.5, seat.position.y + 0.32, seat.position.z);

  // ---- 불턱: ring of stacked basalt stones, fire and smoke
  const BT = new THREE.Vector3(4, E.landH(4, 5), 5); E.bulteok = BT;
  for (let ring = 0; ring < 3; ring++) for (let k = 0; k < 22; k++) {
    const a = (k / 22) * 6.28 + ring * 0.14; if (a > 4.5 && a < 5.3) continue;     // the opening faces the sea
    const s = rr(0.2, 0.3), m = lavaRock(F, s, rockCols[(k + ring) % 3], {flat: 0.75});
    m.position.set(BT.x + Math.cos(a) * 1.75, BT.y + 0.12 + ring * 0.24, BT.z + Math.sin(a) * 1.75); m.rotation.y = rr(0, 6); add(m);
  }
  for (let k = 0; k < 7; k++) { const a = k / 7 * 6.28, m = lavaRock(F, 0.13, 0x3a3430); m.position.set(BT.x + Math.cos(a) * 0.38, BT.y + 0.05, BT.z + Math.sin(a) * 0.38); add(m); }
  for (let k = 0; k < 5; k++) { const lg2 = new THREE.Mesh(new THREE.CylinderGeometry(0.04, 0.05, 0.7, 6), toon(0x4a3426)); lg2.position.set(BT.x, BT.y + 0.12, BT.z);
    lg2.rotation.set(1.3, k * 1.25, 0); add(lg2); }
  const flameCv = document.createElement('canvas'); flameCv.width = 128; flameCv.height = 256;
  const flameTex = new THREE.CanvasTexture(flameCv); flameTex.colorSpace = THREE.SRGBColorSpace;
  const flame = new THREE.Sprite(new THREE.SpriteMaterial({map: flameTex, transparent: true, depthWrite: false, fog: false}));
  flame.scale.set(0.5, 0.95, 1); flame.position.set(BT.x, BT.y + 0.5, BT.z); add(flame, {colorOnly: true});
  const fireLight = new THREE.PointLight(0xff9a48, mode === 'dawn' ? 6 : 0, 7, 1.6); fireLight.position.set(BT.x, BT.y + 0.8, BT.z); F.scene.add(fireLight);
  function drawFlame(t) {
    const x = flameCv.getContext('2d'); x.clearRect(0, 0, 128, 256);
    let s = Math.floor(t * 12) * 7 + 3; const r = () => { s = (s * 16807) % 2147483647; return (s - 1) / 2147483646; };
    for (const [col, k] of [['#e8562a', 1.0], ['#ffa23a', 0.72], ['#ffe9a0', 0.42]]) {
      x.fillStyle = col; x.beginPath(); x.moveTo(64 - 52 * k, 250);
      const n = 4; for (let i = 0; i <= n; i++) { const u = i / n, tx = 64 - 52 * k + u * 104 * k, ty = 250 - (150 + 80 * r()) * k * (1 - Math.abs(u - 0.5) * 0.9);
        x.quadraticCurveTo(tx - 10 + 20 * r(), ty + 40, tx, ty); }
      x.lineTo(64 + 52 * k, 250); x.closePath(); x.fill();
    }
    flameTex.needsUpdate = true;
  }
  E.fireLight = fireLight; E.flame = flame;
  const smokeTex = canvasTex(F, 128, 128, (x) => { const g = x.createRadialGradient(64, 64, 4, 64, 64, 62);
    g.addColorStop(0, 'rgba(200,196,190,0.85)'); g.addColorStop(0.6, 'rgba(170,168,166,0.5)'); g.addColorStop(1, 'rgba(160,160,160,0)'); x.fillStyle = g; x.fillRect(0, 0, 128, 128); });
  const smoke = [];
  for (let i = 0; i < 14; i++) { const s = new THREE.Sprite(new THREE.SpriteMaterial({map: smokeTex, transparent: true, depthWrite: false})); add(s, {colorOnly: true}); smoke.push(s); }
  E.updateFire = (t) => {
    const tq = F.q2(t); drawFlame(tq);
    fireLight.intensity = (mode === 'dawn' ? 6 : 0) * (0.85 + 0.15 * Math.sin(tq * 19));
    smoke.forEach((s, i) => { const a = (tq * 0.35 + i / smoke.length) % 1;
      s.position.set(BT.x + 0.6 * a * a * 4 + 0.15 * Math.sin(i + tq), BT.y + 1.2 + a * 7, BT.z - 0.4 * a * 3);
      const sz = 0.5 + a * 3.2; s.scale.set(sz, sz, 1); s.material.opacity = 0.75 * (1 - a) * Math.min(1, a * 6); });
    flame.userData.on = mode === 'dawn'; smoke.forEach(s => s.userData.on = mode !== 'storm');
  };

  // ---- green land: stone walls (밭담) and the forest edge (곶자왈 entrance) beyond
  for (let i = 0; i < 6; i++) {
    const z0 = 14 + i * 3.2 + rr(-1, 1), x0 = rr(-30, 10), len = rr(8, 20);
    for (let x = x0; x < x0 + len; x += 0.42) { const z = z0 + 0.4 * Math.sin(x * 0.3); const m = lavaRock(F, rr(0.2, 0.28), rockCols[((Math.floor(x * 10) % 3) + 3) % 3], {flat: 0.8});
      m.position.set(x, E.landH(x, z) + 0.2, z); add(m); }
  }
  E.forestEdge = new THREE.Vector3(-6, 0, 26);
  for (let i = 0; i < 70; i++) {
    const x = rr(-40, 30), z = rr(25, 44), h = rr(4, 7), y0 = E.landH(x, z);
    const tr = new THREE.Mesh(new THREE.CylinderGeometry(0.12, 0.22, h, 6), toon(0x5a4a40)); tr.position.set(x, y0 + h / 2, z); add(tr);
    for (let k = 0; k < 3; k++) { const b = new THREE.Mesh(new THREE.IcosahedronGeometry(rr(1.4, 2.4), 2), toon(k % 2 ? 0x3f6a2e : 0x4f7d34));
      b.position.set(x + rr(-1.2, 1.2), y0 + h + rr(-0.5, 0.8), z + rr(-1, 1)); add(b); }
  }
  E.update = (t) => { E.updateSea(F.q2(t)); E.updateFire(t); };
  return E;
}
