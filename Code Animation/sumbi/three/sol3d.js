// 솔이 (9) as a three.js character. Built from lathes/tubes/spheres with toon materials; the face is a painted
// decal shell (CanvasTexture) so eyes and the 3 mouth drawings stay hand-drawn and can be swapped per drawing.
// API: const sol = makeSol(THREE, toonFn); sol.group, sol.setFace({mouth, eyes, look, down}), sol.pose({...})
function makeSol(THREE, toon, opts = {}) {
  const C = Object.assign({
    skin: 0xfddcc0, hair: 0x2b2a3d, coat: 0xfccc38, toggle: 0x333d66, shoe: 0x384470, jar: 0xa36b45, strap: 0x80573a
  }, opts.colors || {});
  const g = new THREE.Group();
  const parts = [];           // meshes for the id/normal/depth passes
  const colorOnly = [];       // decals: drawn only in the colour pass
  const P = (m, parent = g) => { parent.add(m); parts.push(m); m.castShadow = true; m.receiveShadow = true; return m; };
  const coatParts = [];
  const CP = (m, parent) => { coatParts.push(m); return P(m, parent); };

  // ---------- body (raincoat A-line lathe)
  const coatProf = [[0.0, 0.985], [0.055, 0.98], [0.12, 0.955], [0.158, 0.88], [0.172, 0.75], [0.195, 0.6], [0.228, 0.44],
    [0.236, 0.415], [0.225, 0.405]].map(([r, y]) => new THREE.Vector2(r, y));
  const coat = CP(new THREE.Mesh(new THREE.LatheGeometry(coatProf, 40), toon(C.coat)));
  coat.material.side = THREE.DoubleSide; coat.receiveShadow = false;
  // front opening seam + toggles
  for (let k = 0; k < 3; k++) {
    const t = CP(new THREE.Mesh(new THREE.BoxGeometry(0.05, 0.016, 0.02), toon(C.toggle)));
    const y = 0.86 - k * 0.12; const r = 0.172 + (0.86 - y) * 0.16;
    t.position.set(0.02, y, r + 0.005); t.rotation.z = 0.25;
  }
  // hood bunched behind the neck
  const hood = CP(new THREE.Mesh(new THREE.TorusGeometry(0.085, 0.045, 10, 24, Math.PI * 1.3), toon(0xe9a52a)));
  hood.position.set(0, 0.975, -0.03); hood.rotation.set(Math.PI / 2 - 0.25, 0, Math.PI * 0.85);
  // strap across the chest (right shoulder -> left hip)
  const strapPts = [];
  for (let k = 0; k <= 12; k++) {
    const u = k / 12, y = 0.96 - u * 0.36, a = 0.9 - u * 2.1;       // angle around the body
    const r = 0.175 + (0.96 - y) * 0.17 + 0.012;
    strapPts.push(new THREE.Vector3(Math.sin(a) * r, y, Math.cos(a) * r));
  }
  const strap = CP(new THREE.Mesh(new THREE.TubeGeometry(new THREE.CatmullRomCurve3(strapPts), 24, 0.012, 5), toon(C.strap)));
  // 물허벅 on the back
  const jarProf = [[0.0, -0.09], [0.06, -0.085], [0.085, -0.03], [0.08, 0.04], [0.05, 0.08], [0.035, 0.1], [0.04, 0.11]]
    .map(([r, y]) => new THREE.Vector2(r, y));
  const jar = CP(new THREE.Mesh(new THREE.LatheGeometry(jarProf, 24), toon(C.jar)));
  jar.position.set(-0.04, 0.66, -0.25); jar.rotation.z = 0.35; jar.rotation.x = -0.1;

  // ---------- legs + shoes
  const legs = {};
  for (const sx of [-1, 1]) {                       // hip pivots so the legs can kick
    const lp = new THREE.Group(); lp.position.set(sx * 0.065, 0.5, 0); g.add(lp); legs[sx] = lp;
    const thigh = P(new THREE.Mesh(new THREE.CylinderGeometry(0.046, 0.036, 0.24, 12), toon(C.skin)), lp); thigh.position.y = -0.12; thigh.userData.idKey = 'solLeg' + sx;
    const kn = new THREE.Group(); kn.position.y = -0.235; lp.add(kn); lp.userData.knee = kn;
    const kc = P(new THREE.Mesh(new THREE.SphereGeometry(0.037, 12, 8), toon(C.skin)), kn); kc.userData.idKey = 'solLeg' + sx;
    const shin = P(new THREE.Mesh(new THREE.LatheGeometry([[0, 0.01], [0.035, 0.0], [0.04, -0.06], [0.034, -0.15], [0.026, -0.215], [0, -0.23]].map(([r, y]) => new THREE.Vector2(r, y)), 12), toon(C.skin)), kn); shin.userData.idKey = 'solLeg' + sx;
    const shoe = P(new THREE.Mesh(new THREE.SphereGeometry(0.06, 16, 10), toon(C.shoe)), kn);
    shoe.scale.set(0.85, 0.6, 1.45); shoe.position.set(sx * 0.003, -0.23, 0.025); kn.userData.foot = shoe;
  }

  // ---------- arms (shoulder pivots so they can pose)
  const arms = {};
  for (const sx of [-1, 1]) {
    const pivot = new THREE.Group(); pivot.position.set(sx * 0.14, 0.9, 0); g.add(pivot);
    const lathO = (pts, seg) => new THREE.LatheGeometry(pts.map(([r, y]) => new THREE.Vector2(r, y)), seg || 20);
    const upS = CP(new THREE.Mesh(lathO([[0.0, 0.02], [0.045, 0.015], [0.05, -0.04], [0.051, -0.2]]), toon(C.coat)), pivot);
    upS.material.side = THREE.DoubleSide; upS.scale.set(1, 1, 0.9); upS.receiveShadow = false; upS.userData.idKey = 'solSleeve' + sx;
    const elbow = new THREE.Group(); elbow.position.y = -0.185; pivot.add(elbow); pivot.userData.elbow = elbow;
    const elS = CP(new THREE.Mesh(new THREE.SphereGeometry(0.05, 14, 10), toon(C.coat)), elbow); elS.scale.set(1, 1, 0.9); elS.userData.idKey = 'solSleeve' + sx;
    const loS = CP(new THREE.Mesh(lathO([[0.049, 0.01], [0.051, -0.02], [0.064, -0.145], [0.068, -0.16], [0.05, -0.165]]), toon(C.coat)), elbow);
    loS.material.side = THREE.DoubleSide; loS.scale.set(1, 1, 0.9); loS.receiveShadow = false; loS.userData.idKey = 'solSleeve' + sx;
    // hand: palm + thumb (mitten shape) so it reads as a hand, not a ball
    const hand = new THREE.Group(); hand.position.set(0, -0.185, 0.01); elbow.add(hand);
    const palm = P(new THREE.Mesh(new THREE.CapsuleGeometry(0.026, 0.03, 4, 10), toon(C.skin)), hand);
    palm.scale.set(1.15, 1, 0.75);
    const thumb = P(new THREE.Mesh(new THREE.CapsuleGeometry(0.011, 0.022, 3, 8), toon(C.skin)), hand);
    thumb.position.set(-sx * 0.022, 0.006, 0.014); thumb.rotation.z = sx * 0.6;
    pivot.rotation.z = sx * 0.16;
    arms[sx] = pivot; pivot.userData.hand = hand;
  }

  // ---------- head
  const head = new THREE.Group(); head.position.set(0, 1.135, 0.005); head.scale.setScalar(1.0); g.add(head);
  const neck = P(new THREE.Mesh(new THREE.CylinderGeometry(0.035, 0.04, 0.08, 10), toon(C.skin)));
  neck.position.set(0, 1.0, 0);
  const R = 0.152;
  const skull = P(new THREE.Mesh(new THREE.SphereGeometry(R, 40, 28), toon(C.skin)), head);
  skull.scale.set(1.0, 1.0, 0.97); skull.receiveShadow = false;
  skull.material.emissive = new THREE.Color(C.skin).multiplyScalar(0.55);
  // face decal shell: a front patch of a slightly larger sphere, painted on a canvas
  const PHI0 = Math.PI / 2 - 1.22, PHIL = 2.44, TH0 = 0.75, THL = 1.5;
  const cv = document.createElement('canvas'); cv.width = 512; cv.height = 512;
  const tex = new THREE.CanvasTexture(cv); tex.colorSpace = THREE.SRGBColorSpace; tex.anisotropy = 4;
  const faceMat = new THREE.MeshBasicMaterial({map: tex, transparent: true, depthWrite: false});
  const face = new THREE.Mesh(new THREE.SphereGeometry(R * 1.006, 48, 32, PHI0, PHIL, TH0, THL), faceMat);
  face.scale.copy(skull.scale); head.add(face); colorOnly.push(face);
  const ux = (az) => 256 + (az / PHIL) * 512;          // azimuth from the front (rad) -> canvas x
  const vy = (th) => ((th - TH0) / THL) * 512;          // polar angle from the top -> canvas y
  function ellipse(ctx, x, y, rx, ry, col) { ctx.beginPath(); ctx.ellipse(x, y, rx, ry, 0, 0, 2 * Math.PI); ctx.fillStyle = col; ctx.fill(); }
  function drawFace(f) {
    const ctx = cv.getContext('2d'); ctx.clearRect(0, 0, 512, 512);
    // blush
    for (const sx of [-1, 1]) { ctx.globalAlpha = 0.45; ellipse(ctx, ux(sx * 0.6), vy(1.97), 34, 14, '#f98f84'); ctx.globalAlpha = 1; }
    // eyes
    const ey = vy(1.68), lk = (f.look || 0) * 11, ld = (f.down || 0) * 11;
    for (const sx of [-1, 1]) {
      const ex = ux(sx * 0.37);
      if (f.eyes === 'blink') {
        ctx.beginPath(); ctx.moveTo(ex - 54, ey + 8); ctx.quadraticCurveTo(ex, ey + 36, ex + 54, ey + 8);
        ctx.lineWidth = 9; ctx.strokeStyle = '#33201f'; ctx.lineCap = 'round'; ctx.stroke(); continue;
      }
      const ry = f.eyes === 'wide' ? 82 : 74;
      ctx.save(); ctx.beginPath(); ctx.ellipse(ex, ey, 54, ry, 0, 0, 2 * Math.PI); ctx.clip();
      ellipse(ctx, ex, ey, 54, ry, '#fffaf4');
      ellipse(ctx, ex + lk, ey + ld + 4, 47, ry * 0.94, '#33201f');
      ellipse(ctx, ex + lk, ey + ld + 32, 37, ry * 0.5, '#7a4a30');
      ellipse(ctx, ex + lk - 16, ey + ld - 26, 17, 20, '#ffffff');
      ellipse(ctx, ex + lk + 17, ey + ld + 33, 8, 8, 'rgba(255,255,255,0.9)');
      ctx.restore();
      ctx.beginPath(); ctx.moveTo(ex - 58, ey - 34); ctx.quadraticCurveTo(ex, ey - ry - 14, ex + 58, ey - 34);   // upper lash line
      ctx.lineWidth = 13; ctx.strokeStyle = '#2a1b1d'; ctx.lineCap = 'round'; ctx.stroke();
    }
    // nose
    ctx.beginPath(); ctx.moveTo(ux(0), vy(1.86)); ctx.lineTo(ux(0.01), vy(1.9)); ctx.lineWidth = 3; ctx.strokeStyle = '#d99a86'; ctx.stroke();
    // mouth: 0 closed / 1 half / 2 open
    const mx = ux(0), my = vy(2.08);
    if (f.mouth === 'o') {
      ctx.beginPath(); ctx.ellipse(mx, my + 3, 7, 8, 0, 0, 6.3); ctx.fillStyle = '#9c3036'; ctx.fill(); ctx.lineWidth = 3; ctx.strokeStyle = '#4a1d22'; ctx.stroke();
    } else if (!f.mouth) {
      ctx.beginPath(); ctx.moveTo(mx - 16, my); ctx.quadraticCurveTo(mx, my + 7 + (f.smile || 0) * 5, mx + 16, my);
      ctx.lineWidth = 4.5; ctx.strokeStyle = '#9c3a3c'; ctx.lineCap = 'round'; ctx.stroke();
    } else {
      const rx = f.mouth === 1 ? 18 : 23, ry = f.mouth === 1 ? 12 : 24;
      ctx.save(); ctx.beginPath(); ctx.ellipse(mx, my + ry * 0.35, rx, ry, 0, 0, 2 * Math.PI); ctx.fillStyle = '#9c3036'; ctx.fill(); ctx.clip();
      ellipse(ctx, mx, my + ry * 1.0, rx * 0.75, ry * 0.55, '#f08a8a'); ctx.restore();
      ctx.beginPath(); ctx.ellipse(mx, my + ry * 0.35, rx, ry, 0, 0, 2 * Math.PI); ctx.lineWidth = 3; ctx.strokeStyle = '#4a1d22'; ctx.stroke();
    }
    tex.needsUpdate = true;
  }
  // hair v2: one sculpted shell over the skull — bob that curves in at the hem, scalloped clump ends,
  // straight-cut bangs ending above the eyes, side locks in front of the ears, clump ridges and a crown parting.
  const hm = toon(C.hair); hm.side = THREE.DoubleSide;
  const NPh = 96, NV = 40;
  const hpos = [], hidx = [], hmeta = [];
  const sm2 = (a, b, x) => { const t = Math.min(1, Math.max(0, (x - a) / (b - a))); return t * t * (3 - 2 * t); };
  function hairEnd(phi) {                     // polar angle where the hair stops, phi = 0 at the front
    const ap = Math.abs(Math.atan2(Math.sin(phi), Math.cos(phi)));
    const bang = 1.30 + 0.035 * Math.abs(Math.sin(phi * 9.0)) * (ap < 0.8 ? 1 : 0);       // little teeth along the cut
    const bob = 2.30 + 0.07 * Math.sin(phi * 7.0 + 0.6) + 0.05 * Math.sin(phi * 13.0) + 0.42 * Math.max(0, -Math.cos(phi)) ** 2;   // uneven clump ends, longer at the nape
    const lock = 2.42;                                                                        // locks in front of the ears
    const toSide = sm2(0.78, 0.98, ap);
    const lockW = sm2(0.92, 1.05, ap) * (1 - sm2(1.25, 1.45, ap));
    return bang * (1 - toSide) + bob * toSide + (lock - bob) * lockW;
  }
  for (let i = 0; i <= NPh; i++) {
    const phi = (i / NPh) * Math.PI * 2;
    const th1 = hairEnd(phi);
    for (let j = 0; j <= NV; j++) {
      const v = j / NV, th = v * th1;
      const ap = Math.abs(Math.atan2(Math.sin(phi), Math.cos(phi)));
      let r = R * 1.075;
      r += R * 0.02 * Math.sin(phi * 14 + v * 2.0) * sm2(0.25, 0.8, v);                    // clump ridges
      const below = sm2(1.45, 2.0, th) * sm2(0.85, 1.1, ap);                                // bob volume at the sides/back
      r += R * 0.16 * below;
      r -= R * 0.13 * sm2(0.86, 1.0, v) * sm2(0.85, 1.1, ap) * (1 - 0.7 * Math.max(0, -Math.cos(phi)));   // hem curls inward (less at the back)
      r += R * 0.04 * sm2(0.0, 0.25, th) * Math.max(0, Math.cos(phi - 2.6)) * 0;            // (crown kept round)
      const x = r * Math.sin(th) * Math.sin(phi), y = r * Math.cos(th), z = r * Math.sin(th) * Math.cos(phi);
      hpos.push(x, y * 1.0, z * 0.97); hmeta.push(phi, th, th1, ap);
    }
  }
  for (let i = 0; i < NPh; i++) for (let j = 0; j < NV; j++) {
    const a0 = i * (NV + 1) + j, b0 = (i + 1) * (NV + 1) + j;
    hidx.push(a0, b0, a0 + 1, b0, b0 + 1, a0 + 1);
  }
  const hg = new THREE.BufferGeometry();
  hg.setAttribute('position', new THREE.Float32BufferAttribute(hpos, 3)); hg.setIndex(hidx); hg.computeVertexNormals();
  const hairMesh = P(new THREE.Mesh(hg, hm), head);
  hairMesh.receiveShadow = false;
  const hbase = Float32Array.from(hpos);
  function floatHair(t, amt) {
    // underwater: the bob fans out and up like a slow halo, ends split into clumps that sway with a lag
    const p = hg.attributes.position;
    for (let k = 0; k < p.count; k++) {
      const phi = hmeta[k * 4], th = hmeta[k * 4 + 1], th1 = hmeta[k * 4 + 2], ap = hmeta[k * 4 + 3];
      let x = hbase[k * 3], y = hbase[k * 3 + 1], z = hbase[k * 3 + 2];
      const side = sm2(0.75, 1.05, ap);
      const f = sm2(1.25, th1, th) * side;                         // lower hair moves, crown stays on the head
      const clump = 0.65 + 0.35 * Math.sin(phi * 9.0 + 0.5);       // strands separate at the tips
      const wave = Math.sin(phi * 4.0 + t * 1.7 - th * 2.0);
      const hr = Math.hypot(x, z) || 1;
      const out = R * amt * (0.62 * f * f * clump + 0.10 * f * wave);
      x += x / hr * out; z += z / hr * out;
      y += R * amt * (0.22 * f * f * f * clump + 0.08 * f * Math.sin(phi * 3.0 + t * 1.3));
      const fb = (1 - side) * sm2(0.9, 1.3, th);                   // bangs lift a little off the brow
      y += R * amt * 0.10 * fb * (1 + 0.5 * Math.sin(phi * 9 + t * 2)); z += R * amt * 0.06 * fb;
      p.setXYZ(k, x, y, z);
    }
    p.needsUpdate = true; hg.computeVertexNormals();
  }

  const hoodG = new THREE.Group(); head.add(hoodG);
  { const hp2 = [], hi2 = []; const NP2 = 120, NT2 = 60, TH = 2.35;
    const inF = (phi, th) => { const a = Math.atan2(Math.sin(phi), Math.cos(phi)); return (a / 1.12) ** 2 + ((th - 1.85) / 0.98) ** 2 < 1; };
    for (let i = 0; i <= NP2; i++) for (let j = 0; j <= NT2; j++) {
      const phi = i / NP2 * Math.PI * 2, th = j / NT2 * TH;
      const r = R * (1.36 + 0.1 * Math.max(0, (th - 1.6) / 0.75)) * (1 + 0.04 * Math.sin(phi * 5 + th * 3));
      hp2.push(r * Math.sin(th) * Math.sin(phi), r * Math.cos(th) * 1.04 + 0.01, r * Math.sin(th) * Math.cos(phi) - 0.012);
    }
    for (let i = 0; i < NP2; i++) for (let j = 0; j < NT2; j++) {
      if (inF((i + 0.5) / NP2 * Math.PI * 2, (j + 0.5) / NT2 * TH)) continue;
      const a0 = i * (NT2 + 1) + j, b0 = (i + 1) * (NT2 + 1) + j; hi2.push(a0, b0, a0 + 1, b0, b0 + 1, a0 + 1);
    }
    const hg2 = new THREE.BufferGeometry(); hg2.setAttribute('position', new THREE.Float32BufferAttribute(hp2, 3)); hg2.setIndex(hi2); hg2.computeVertexNormals();
    const hoodUp = CP(new THREE.Mesh(hg2, toon(C.coat)), hoodG); hoodUp.material.side = THREE.DoubleSide; hoodUp.receiveShadow = false;
  }
  hoodG.visible = false;
  function setHood(u) {          // 0 = down (collar), 1 = pulled up over the head, >1 = pulled low over the eyes
    hoodG.visible = u > 0.02; hood.visible = u < 0.6;
    hoodG.rotation.x = -2.2 * (1 - Math.min(1, u)) + 0.22 * Math.max(0, u - 1);
  }

  if (opts.underwater) {
    coatParts.forEach(m => { m.visible = false; m.parent.remove(m); parts.splice(parts.indexOf(m), 1); });
    const sc = document.createElement('canvas'); sc.width = 8; sc.height = 64; const sx2 = sc.getContext('2d');
    for (let k = 0; k < 16; k++) { sx2.fillStyle = k % 2 ? '#2f4f8a' : '#fbf7ee'; sx2.fillRect(0, k * 4, 8, 4); }
    const stripe = new THREE.CanvasTexture(sc); stripe.colorSpace = THREE.SRGBColorSpace; stripe.magFilter = THREE.NearestFilter;
    const shirtM = new THREE.MeshToonMaterial({map: stripe, gradientMap: toon(0xffffff).gradientMap}); shirtM.side = THREE.DoubleSide;
    const shirtProf = [[0.0, 0.985], [0.06, 0.98], [0.13, 0.955], [0.158, 0.9], [0.155, 0.8], [0.15, 0.7], [0.152, 0.63], [0.13, 0.615]]
      .map(([r, y]) => new THREE.Vector2(r, y));
    P(new THREE.Mesh(new THREE.LatheGeometry(shirtProf, 36), shirtM));
    const shortsProf = [[0.13, 0.66], [0.145, 0.6], [0.148, 0.54], [0.12, 0.5], [0.0, 0.48]].map(([r, y]) => new THREE.Vector2(r, y));
    P(new THREE.Mesh(new THREE.LatheGeometry(shortsProf, 30), toon(0x2b3a66))).material.side = THREE.DoubleSide;
    for (const k of [-1, 1]) {
      const sl = P(new THREE.Mesh(new THREE.CylinderGeometry(0.066, 0.07, 0.13, 14), toon(0x2b3a66)), legs[k]); sl.position.y = -0.03;
    }
    for (const k of [-1, 1]) {
      const pv = arms[k];
      const ss2 = P(new THREE.Mesh(new THREE.CylinderGeometry(0.05, 0.056, 0.1, 12, 1, true), shirtM), pv); ss2.position.y = -0.02;
      const lath = (pts) => new THREE.LatheGeometry(pts.map(([r, y]) => new THREE.Vector2(r, y)), 14);
      const up = P(new THREE.Mesh(lath([[0, 0.02], [0.03, 0.01], [0.034, -0.04], [0.031, -0.13], [0.028, -0.185], [0, -0.2]]), toon(C.skin)), pv); up.userData.idKey = 'solArm' + k;
      const el = pv.userData.elbow;
      const fore = P(new THREE.Mesh(lath([[0, 0.02], [0.028, 0.0], [0.029, -0.05], [0.024, -0.13], [0.021, -0.165], [0, -0.18]]), toon(C.skin)), el); fore.userData.idKey = 'solArm' + k;
      P(new THREE.Mesh(new THREE.SphereGeometry(0.028, 10, 8), toon(C.skin)), el).userData.idKey = 'solArm' + k;
    }
  }

  const api = {
    floatHair, setHood, jar, coat, strap,
    group: g, parts, colorOnly, head, arms,
    setFace(f) { drawFace(f); },
    pose(p) {
      head.rotation.set(p.pitch || 0, p.yaw || 0, p.roll || 0);
      arms[-1].rotation.set(p.armLx || 0, 0, -0.16 - (p.armL || 0));
      arms[1].rotation.set(p.armRx || 0, 0, 0.16 + (p.armR || 0));
      legs[-1].rotation.set(p.legL || 0, 0, -(p.spread || 0)); legs[1].rotation.set(p.legR || 0, 0, (p.spread || 0));
      legs[-1].userData.knee.rotation.x = p.kneeL || 0; legs[1].userData.knee.rotation.x = p.kneeR || 0;
      legs[-1].userData.knee.userData.foot.rotation.x = 0.6 * (p.kneeL || 0); legs[1].userData.knee.userData.foot.rotation.x = 0.6 * (p.kneeR || 0);
      arms[-1].userData.hand.rotation.set(p.wristL || 0, 0, -(p.wristL || 0) * 0.5); arms[1].userData.hand.rotation.set(p.wristR || 0, 0, (p.wristR || 0) * 0.5);
      arms[-1].userData.elbow.rotation.set(-0.5 * (p.elbowL || 0) - (p.elbowLx || 0), 0, -(p.elbowL || 0)); arms[1].userData.elbow.rotation.set(-0.5 * (p.elbowR || 0) - (p.elbowRx || 0), 0, (p.elbowR || 0));
      const b = 1 + 0.012 * (p.breath || 0);
      coat.scale.set(b, 1, b);
    }
  };
  drawFace({mouth: 0});
  return api;
}
