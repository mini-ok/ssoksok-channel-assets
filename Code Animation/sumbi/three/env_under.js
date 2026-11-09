// Under the Jeju sea (from the C30 tech test v3): water volume gradient, sand + basalt reefs with pink crust, twisting kelp,
// silver surface from below, seabed caustics, caustic spotlight over bodies, the light window overhead, cel bubbles,
// octopus glows. Surface y = +2.6, seabed y = -2.6.
function buildUnder(F, mode) {
  const {THREE, rr, toon, add} = F;
  const E = {SEA: -2.6, TOP: 2.6};
  const SEA = E.SEA;
  F.bg = new THREE.Color(0x1b6f84);
  F.scene.fog = new THREE.FogExp2(0x1b6f84, 0.16); F.meta.fog = {type: 'exp2', density: 0.16}; F.DR = 10;
  const sun = new THREE.DirectionalLight(0xd8fff6, 1.7); sun.position.set(1.5, 12, 2); sun.castShadow = true;
  sun.shadow.mapSize.set(2048, 2048); sun.shadow.bias = -0.002; sun.shadow.normalBias = 0.05;
  Object.assign(sun.shadow.camera, {left: -6, right: 6, top: 6, bottom: -6, near: 1, far: 30});
  F.scene.add(sun, sun.target); F.scene.add(new THREE.HemisphereLight(0x9ff2ee, 0x0b3550, 1.6));
  { const g = new THREE.PlaneGeometry(60, 60, 120, 120); g.rotateX(-Math.PI / 2); const p = g.attributes.position;
    for (let i = 0; i < p.count; i++) { const x = p.getX(i), z = p.getZ(i); p.setY(i, SEA + 0.18 * Math.sin(x * 0.9) * Math.cos(z * 0.7) + 0.08 * Math.sin(x * 2.7 + z * 1.9)); }
    g.computeVertexNormals(); add(new THREE.Mesh(g, toon(0xc9c08e)), {cast: false}); }
  E.reefs = [];
  for (let i = 0; i < 40; i++) {
    const s = rr(0.3, 1.3), x = rr(-12, 12), z = rr(-12, 5); if (Math.hypot(x - 0.5, z + 0.5) < 1.6) continue;
    const m = lavaRock(F, s, 0x3c4250, {flat: 0.7}); m.position.set(x, SEA + s * 0.2, z); add(m);
    const crust = new THREE.Mesh(new THREE.SphereGeometry(s * 0.9, 10, 6, 0, 6.28, 0, 0.9), toon(i % 3 ? 0xd98b9a : 0xe8a77a));
    crust.position.copy(m.position); crust.position.y += s * 0.15; crust.scale.set(1.05, 0.5, 1.05); add(crust); E.reefs.push(m);
  }
  // the abalone rock (C30 14–18 s)
  E.abRock = lavaRock(F, 0.55, 0x3c4250, {flat: 0.75}); E.abRock.position.set(1.6, SEA + 0.25, -0.9); add(E.abRock);
  // kelp
  const kelpTex = canvasTex(F, 64, 256, (x) => { const g = x.createLinearGradient(0, 0, 64, 0);
    g.addColorStop(0, '#d8e6a0'); g.addColorStop(0.12, '#ffffff'); g.addColorStop(0.42, '#e8efd0'); g.addColorStop(0.5, '#8a9a60');
    g.addColorStop(0.58, '#e8efd0'); g.addColorStop(0.88, '#ffffff'); g.addColorStop(1, '#d8e6a0'); x.fillStyle = g; x.fillRect(0, 0, 64, 256);
    x.strokeStyle = 'rgba(120,140,80,0.55)'; x.lineWidth = 1.5;
    for (let y = 10; y < 256; y += 14) { x.beginPath(); x.moveTo(32, y); x.quadraticCurveTo(18, y - 4, 4, y - 12); x.moveTo(32, y + 6); x.quadraticCurveTo(46, y + 2, 60, y - 6); x.stroke(); } });
  const kelpMats = [0x6f7a2c, 0x8a8a34, 0x566c2a].map(c => toon(c, {map: kelpTex, side: THREE.DoubleSide}));
  const kelps = [];
  for (let i = 0; i < 150; i++) {
    const x = rr(-10, 10), z = rr(-11, 3.5); if (Math.hypot(x - 0.4, z + 0.4) < 1.7) continue;
    const h = rr(2.2, 4.6), w = rr(0.12, 0.24);
    const g = new THREE.PlaneGeometry(w, h, 2, 24); g.translate(0, h / 2, 0);
    { const p = g.attributes.position; for (let q = 0; q < p.count; q++) { const u = p.getY(q) / h; p.setX(q, p.getX(q) * (0.45 + 1.1 * Math.sin(Math.min(1, u * 1.25) * Math.PI * 0.55)) * (1 - u ** 6)); } }
    const m = add(new THREE.Mesh(g, kelpMats[i % 3]), {cast: true}); m.position.set(x, SEA, z); m.rotation.y = rr(0, 6.28);
    m.userData.base = Float32Array.from(g.attributes.position.array); m.userData.ph = rr(0, 6.28); m.userData.h = h; m.userData.twist = rr(-2.2, 2.2);
    kelps.push(m);
  }
  E.kelps = kelps;
  function swayKelp(t) {
    for (const k of kelps) { const p = k.geometry.attributes.position, b = k.userData.base;
      for (let i = 0; i < p.count; i++) { const y = b[i * 3 + 1], u = y / k.userData.h;
        const sw = 0.35 * u * u * Math.sin(t * 1.3 + k.userData.ph + u * 2.2);
        const tw = u * k.userData.twist + 0.25 * Math.sin(t * 0.9 + k.userData.ph + u * 3);
        const bx = b[i * 3] * Math.cos(tw), bz = b[i * 3] * Math.sin(tw);
        p.setX(i, bx + sw + (b[i * 3] > 0 ? 1 : -1) * 0.02 * Math.sin(y * 9 + t * 2)); p.setZ(i, bz + 0.18 * u * u * Math.cos(t * 1.1 + k.userData.ph)); }
      p.needsUpdate = true; k.geometry.computeVertexNormals(); }
  }
  // water volume
  { const g = new THREE.SphereGeometry(40, 32, 16), p = g.attributes.position, col = [];
    for (let i = 0; i < p.count; i++) { const y = p.getY(i) / 40; const c = new THREE.Color().lerpColors(new THREE.Color(0x14607e), new THREE.Color(0xa8f0e0), Math.max(0, Math.min(1, y * 1.5)) ** 1.3); col.push(c.r, c.g, c.b); }
    g.setAttribute('color', new THREE.Float32BufferAttribute(col, 3));
    const vol = new THREE.Mesh(g, new THREE.MeshBasicMaterial({vertexColors: true, side: THREE.BackSide, fog: false, depthWrite: false})); vol.renderOrder = -1; add(vol, {colorOnly: true}); }
  function cellNet(cv, t, bright, back) {
    const ctx = cv.getContext('2d'); ctx.fillStyle = back; ctx.fillRect(0, 0, 512, 512); ctx.strokeStyle = bright; ctx.lineCap = 'round';
    let s2 = 5; const r2 = () => { s2 = (s2 * 16807) % 2147483647; return (s2 - 1) / 2147483646; };
    const pts = []; for (let i = 0; i < 46; i++) pts.push([r2() * 512 + 18 * Math.sin(t * 1.4 + i), r2() * 512 + 18 * Math.cos(t * 1.1 + i * 1.7)]);
    for (const [x, y] of pts) for (const [x2, y2] of pts) { const d = Math.hypot(x - x2, y - y2);
      if (d > 20 && d < 95 && x < x2) { ctx.lineWidth = 1.5 + 3.5 * (1 - d / 95); ctx.beginPath(); ctx.moveTo(x, y);
        ctx.quadraticCurveTo((x + x2) / 2 + 10 * Math.sin(t + x), (y + y2) / 2 + 10 * Math.cos(t + y), x2, y2); ctx.stroke(); } }
  }
  const surfCv = document.createElement('canvas'); surfCv.width = surfCv.height = 512;
  const surfTex = new THREE.CanvasTexture(surfCv); surfTex.wrapS = surfTex.wrapT = THREE.RepeatWrapping; surfTex.repeat.set(14, 14);
  const surface = new THREE.Mesh(new THREE.PlaneGeometry(80, 80), new THREE.MeshBasicMaterial({map: surfTex, fog: true, side: THREE.DoubleSide}));
  surface.rotation.x = Math.PI / 2; surface.position.y = E.TOP; add(surface, {cast: false}); surface.userData.noLine = true;
  const causCv = document.createElement('canvas'); causCv.width = causCv.height = 512;
  const causTex = new THREE.CanvasTexture(causCv); causTex.wrapS = causTex.wrapT = THREE.RepeatWrapping; causTex.repeat.set(2, 2);
  const causG = new THREE.CircleGeometry(9, 48);
  { const p = causG.attributes.position, col = []; for (let i = 0; i < p.count; i++) { const f = Math.max(0, 1 - Math.hypot(p.getX(i), p.getY(i)) / 9) ** 1.5; col.push(f, f, f); }
    causG.setAttribute('color', new THREE.Float32BufferAttribute(col, 3)); }
  const caus = new THREE.Mesh(causG, new THREE.MeshBasicMaterial({map: causTex, vertexColors: true, transparent: true, blending: THREE.AdditiveBlending, depthWrite: false, opacity: 0.28, fog: false}));
  caus.rotation.x = -Math.PI / 2; caus.position.y = SEA + 0.22; add(caus, {colorOnly: true});
  const causLCv = document.createElement('canvas'); causLCv.width = causLCv.height = 512;
  const causLTex = new THREE.CanvasTexture(causLCv); causLTex.wrapS = causLTex.wrapT = THREE.RepeatWrapping;
  const causSpot = new THREE.SpotLight(0xe8fff4, 140, 30, 0.75, 0.5, 1.2); causSpot.position.set(0.3, 9, 0.6); causSpot.target.position.set(0, 0, -0.5);
  causSpot.castShadow = true; causSpot.map = causLTex; causSpot.shadow.mapSize.set(1024, 1024); causSpot.shadow.bias = -0.002;
  F.scene.add(causSpot, causSpot.target);
  E.light = (x, y, z) => { causSpot.position.set(x + 0.3, 9, z + 0.6); causSpot.target.position.set(x, y, z - 0.5); sun.position.set(x + 1.5, 12, z + 2); sun.target.position.set(x, y, z); };
  { const c = document.createElement('canvas'); c.width = c.height = 256; const x = c.getContext('2d');
    const g = x.createRadialGradient(128, 128, 0, 128, 128, 128); g.addColorStop(0, 'rgba(255,255,235,1)'); g.addColorStop(0.35, 'rgba(210,255,240,0.65)'); g.addColorStop(1, 'rgba(0,0,0,0)');
    x.fillStyle = g; x.fillRect(0, 0, 256, 256);
    E.window = new THREE.Mesh(new THREE.CircleGeometry(5.5, 48), new THREE.MeshBasicMaterial({map: new THREE.CanvasTexture(c), transparent: true, blending: THREE.AdditiveBlending, depthWrite: false, fog: false, side: THREE.DoubleSide, opacity: 0.16}));
    E.window.rotation.x = Math.PI / 2; E.window.position.set(0.8, E.TOP - 0.1, -1.2); add(E.window, {colorOnly: true}); }
  // ---- cel bubbles: streams of sprites
  const bubTex = canvasTex(F, 128, 128, (x) => {
    x.fillStyle = 'rgba(190,250,245,0.18)'; x.beginPath(); x.arc(64, 64, 54, 0, 7); x.fill();
    x.strokeStyle = 'rgba(245,255,252,0.95)'; x.lineWidth = 7; x.beginPath(); x.arc(64, 64, 54, 0, 7); x.stroke();
    x.strokeStyle = '#fff'; x.lineWidth = 9; x.lineCap = 'round'; x.beginPath(); x.arc(64, 64, 36, 3.6, 4.5); x.stroke();
    x.fillStyle = '#fff'; x.beginPath(); x.arc(84, 86, 6, 0, 7); x.fill(); });
  const bubMat = new THREE.SpriteMaterial({map: bubTex, transparent: true, depthWrite: false, fog: true});
  const streams = [];
  // get(t) -> Vector3 source (or null = off); period: seconds between bursts; burst: bubbles per burst (spread 0.05 s)
  E.stream = (get, o = {}) => {
    const st = Object.assign({n: 12, period: 1.6, burst: 1, size: [0.02, 0.05], speed: [0.5, 0.8], life: 3, t0: -99, t1: 99, drift: 0.03}, o, {get, b: []});
    for (let i = 0; i < st.n; i++) { const s = new THREE.Sprite(bubMat); add(s, {colorOnly: true});
      st.b.push({s, ph: Math.floor(i / st.burst) * st.period + (i % st.burst) * 0.05, size: rr(...st.size), speed: rr(...st.speed), rnd: rr(0, 6.28)}); }
    streams.push(st); return st;
  };
  function updBubbles(t) {
    for (const st of streams) for (const b of st.b) {
      const L = st.period * Math.ceil(st.n / st.burst);
      let age = (t - b.ph) % L; if (age < 0) age += L;
      const born = t - age;
      const src = (born >= st.t0 && born <= st.t1) ? st.get(born) : null;
      if (!src || age > st.life) { b.s.userData.on = false; continue; }
      const rise = age * b.speed * (1 + 0.35 * age), wob = st.drift * (1 + age) * Math.sin(age * 9 + b.rnd);
      b.s.position.set(src.x + wob, src.y + 0.02 + rise, src.z + 0.6 * wob);
      const sz = b.size * (1 + 0.25 * age) * (1 + 0.12 * Math.sin(age * 14 + b.rnd)); b.s.scale.set(sz * (1 + 0.1 * Math.sin(age * 11)), sz, 1);
      b.s.userData.on = b.s.position.y < E.TOP - 0.05;
    }
  }
  // seabed vents (always)
  [[-1.6, -1.2], [1.5, -1.6], [-0.4, -2.4], [2.4, -0.6], [-2.6, -0.2], [0.7, -0.9], [-3.5, -3.0], [3.4, -2.6]].forEach(([x, z], k) => {
    const v = new THREE.Vector3(x, SEA + 0.1, z); E.stream(() => v, {n: 18, period: 0.3, burst: 1, size: [0.03, 0.09], speed: [0.6, 0.95], life: 6.5}); });
  // glows for octopi
  const glowTex = canvasTex(F, 128, 128, (x) => { const g = x.createRadialGradient(64, 64, 0, 64, 64, 64); g.addColorStop(0, 'rgba(255,255,255,0.9)'); g.addColorStop(0.3, 'rgba(255,255,255,0.35)'); g.addColorStop(1, 'rgba(255,255,255,0)'); x.fillStyle = g; x.fillRect(0, 0, 128, 128); });
  E.GLOWC = {orange: 0xffb050, pink: 0xff8fd0, white: 0xc8fbff, grey: 0x8899aa};
  E.glow = (scale) => { const s = new THREE.Sprite(new THREE.SpriteMaterial({map: glowTex, transparent: true, blending: THREE.AdditiveBlending, depthWrite: false, fog: true, opacity: 0}));
    s.scale.setScalar(scale); add(s, {colorOnly: true}); return s; };
  E.update = (t) => {
    const tq = F.q2(t); swayKelp(tq);
    cellNet(surfCv, tq, 'rgba(235,255,250,0.55)', '#8fdcd8'); surfTex.needsUpdate = true;
    cellNet(causCv, tq * 1.2, 'rgba(230,255,240,0.9)', 'rgba(0,0,0,0)'); causTex.needsUpdate = true;
    cellNet(causLCv, tq * 1.1, 'rgba(255,255,255,1)', '#000000'); causLTex.needsUpdate = true; causLTex.offset.set(tq * 0.03, tq * 0.017); causLTex.repeat.set(3, 3);
    updBubbles(tq);
  };
  return E;
}
