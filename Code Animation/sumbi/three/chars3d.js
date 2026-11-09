// 〈숨비〉 3D cast: shared face decal, 꾸럭이 (baby octopus), 엄마 (해녀). Same build style as sol3d.js.
function makeFaceDecal(THREE, R, style) {
  // painted canvas on a front patch of a sphere; style: {eyeW, eyeH, eyeY, eyeX, iris, lash, brow, mouthY, blush, skinLine}
  const S = Object.assign({eyeW: 54, eyeH: 74, eyeY: 1.68, eyeX: 0.37, iris: '#7a4a30', lash: 13, brow: false, mouthY: 2.08,
                           blush: 0.45, nose: '#d99a86', lineCol: '#2a1b1d', lip: '#9c3a3c'}, style || {});
  const PHI0 = Math.PI / 2 - 1.22, PHIL = 2.44, TH0 = 0.75, THL = 1.5;
  const cv = document.createElement('canvas'); cv.width = 512; cv.height = 512;
  const tex = new THREE.CanvasTexture(cv); tex.colorSpace = THREE.SRGBColorSpace; tex.anisotropy = 4;
  const mesh = new THREE.Mesh(new THREE.SphereGeometry(R * 1.006, 48, 32, PHI0, PHIL, TH0, THL),
                              new THREE.MeshBasicMaterial({map: tex, transparent: true, depthWrite: false}));
  const ux = (az) => 256 + (az / PHIL) * 512, vy = (th) => ((th - TH0) / THL) * 512;
  const E = (ctx, x, y, rx, ry, col) => { ctx.beginPath(); ctx.ellipse(x, y, rx, ry, 0, 0, 2 * Math.PI); ctx.fillStyle = col; ctx.fill(); };
  function draw(f) {
    const ctx = cv.getContext('2d'); ctx.clearRect(0, 0, 512, 512); ctx.lineCap = 'round';
    if (S.blush > 0) for (const sx of [-1, 1]) { ctx.globalAlpha = S.blush; E(ctx, ux(sx * 0.6), vy(S.eyeY + 0.29), 34, 14, '#f98f84'); ctx.globalAlpha = 1; }
    const ey = vy(S.eyeY), lk = (f.look || 0) * S.eyeW * 0.2, ld = (f.down || 0) * S.eyeW * 0.2;
    for (const sx of [-1, 1]) {
      const ex = ux(sx * S.eyeX);
      if (S.brow) {
        const bl = (f.brow || 0) * 6;
        ctx.beginPath(); ctx.moveTo(ex - S.eyeW * 0.9, ey - S.eyeH - 18 + (sx < 0 ? bl : -bl) * 0 + bl);
        ctx.quadraticCurveTo(ex, ey - S.eyeH - 30 - bl, ex + S.eyeW * 0.9, ey - S.eyeH - 20 + bl * 0.3);
        ctx.lineWidth = S.browW || 9; ctx.strokeStyle = '#5a3a30'; ctx.stroke();
      }
      if (f.eyes === 'blink') {
        ctx.beginPath(); ctx.moveTo(ex - S.eyeW, ey + 8); ctx.quadraticCurveTo(ex, ey + 8 + S.eyeH * 0.35, ex + S.eyeW, ey + 8);
        ctx.lineWidth = S.lash * 0.7; ctx.strokeStyle = S.lineCol; ctx.stroke(); continue;
      }
      const ry = S.eyeH * (f.eyes === 'wide' ? 1.1 : 1.0), rx = S.eyeW;
      ctx.save(); ctx.beginPath(); ctx.ellipse(ex, ey, rx, ry, 0, 0, 2 * Math.PI); ctx.clip();
      E(ctx, ex, ey, rx, ry, '#fffaf4');
      E(ctx, ex + lk, ey + ld + ry * 0.05, rx * 0.86, ry * 0.94, '#33201f');
      E(ctx, ex + lk, ey + ld + ry * 0.43, rx * 0.68, ry * 0.5, S.iris);
      E(ctx, ex + lk - rx * 0.3, ey + ld - ry * 0.35, rx * 0.31, ry * 0.27, '#ffffff');
      E(ctx, ex + lk + rx * 0.3, ey + ld + ry * 0.45, rx * 0.15, rx * 0.15, 'rgba(255,255,255,0.9)');
      ctx.restore();
      ctx.beginPath(); ctx.moveTo(ex - rx * 1.07, ey - ry * 0.46); ctx.quadraticCurveTo(ex, ey - ry * 1.19, ex + rx * 1.07, ey - ry * 0.46);
      ctx.lineWidth = S.lash; ctx.strokeStyle = S.lineCol; ctx.stroke();
    }
    ctx.beginPath(); ctx.moveTo(ux(0), vy(S.mouthY - 0.22)); ctx.lineTo(ux(0.01), vy(S.mouthY - 0.18));
    ctx.lineWidth = 3; ctx.strokeStyle = S.nose; ctx.stroke();
    const mx = ux(0), my = vy(S.mouthY);
    if (!f.mouth) {
      ctx.beginPath(); ctx.moveTo(mx - 16, my); ctx.quadraticCurveTo(mx, my + 6 + (f.smile || 0) * 6, mx + 16, my);
      ctx.lineWidth = 4.5; ctx.strokeStyle = S.lip; ctx.stroke();
    } else {
      const rx = f.mouth === 1 ? 18 : 23, ry = f.mouth === 1 ? 12 : 24;
      ctx.save(); ctx.beginPath(); ctx.ellipse(mx, my + ry * 0.35, rx, ry, 0, 0, 2 * Math.PI); ctx.fillStyle = '#9c3036'; ctx.fill(); ctx.clip();
      E(ctx, mx, my + ry, rx * 0.75, ry * 0.55, '#f08a8a'); ctx.restore();
      ctx.beginPath(); ctx.ellipse(mx, my + ry * 0.35, rx, ry, 0, 0, 2 * Math.PI); ctx.lineWidth = 3; ctx.strokeStyle = '#4a1d22'; ctx.stroke();
    }
    tex.needsUpdate = true;
  }
  return {mesh, draw};
}

// ------------------------------------------------------------------ 꾸럭이
const KU_COL = {grey: 0xa8a3aa, orange: 0xfa8e3c, white: 0xfaf4ee, pink: 0xfa9ea8};
function makeKuruk(THREE, toon, size = 1.0) {
  const g = new THREE.Group(), parts = [], colorOnly = [];
  const P = (m, parent = g) => { parent.add(m); parts.push(m); m.castShadow = true; m.receiveShadow = false; return m; };
  const body = toon(KU_COL.orange), sucker = toon(0xffd2b0);
  const s = 0.05 * size;                              // mantle radius (a palm-sized octopus ~ 12 cm across)
  // mantle: a soft bulb, tilted back a little
  const prof = [[0.001, 2.1], [0.45, 2.02], [0.8, 1.78], [0.98, 1.4], [1.0, 1.0], [0.9, 0.6], [0.72, 0.35], [0.6, 0.2]]
    .map(([r, y]) => new THREE.Vector2(r * s, y * s));
  const mantle = P(new THREE.Mesh(new THREE.LatheGeometry(prof, 28), body));
  mantle.rotation.x = -0.25;
  // head ring (where the eyes sit) and eyes
  const headR = P(new THREE.Mesh(new THREE.SphereGeometry(s * 0.72, 24, 16), body));
  headR.position.set(0, s * 0.35, 0); headR.scale.set(1.15, 0.8, 1.05);
  const eyes = [];
  for (const sx of [-1, 1]) {
    const e = new THREE.Group(); e.position.set(sx * s * 0.42, s * 0.48, s * 0.62); g.add(e);
    const ball = P(new THREE.Mesh(new THREE.SphereGeometry(s * 0.2, 14, 10), toon(0x24202a)), e); ball.scale.set(0.85, 1.05, 0.6);
    const hl = new THREE.Mesh(new THREE.SphereGeometry(s * 0.07, 8, 6), new THREE.MeshBasicMaterial({color: 0xffffff}));
    hl.position.set(-s * 0.05, s * 0.07, s * 0.1); e.add(hl); colorOnly.push(hl);
    eyes.push(e);
  }
  // eight arms: tapered tubes along curls that roll outward at the tips
  const arms = [];
  for (let k = 0; k < 8; k++) {
    const a = (k / 8) * Math.PI * 2 + Math.PI / 8;
    const pts = [];
    for (let j = 0; j <= 12; j++) {
      const u = j / 12, w = Math.max(0, (u - 0.55) / 0.45);
      const aa = a + 0.25 * Math.sin(u * 2.5 + k);
      const rr = s * (0.5 + 1.3 * u) - s * 0.75 * w * w;
      const y = s * (0.15 - 0.55 * Math.sin(Math.min(u, 0.6) * Math.PI * 0.85)) + s * 0.75 * w;
      pts.push(new THREE.Vector3(Math.cos(aa) * rr, y, Math.sin(aa) * rr));
    }
    const curve = new THREE.CatmullRomCurve3(pts);
    const tg = new THREE.TubeGeometry(curve, 30, s * 0.26, 8, false);
    const p = tg.attributes.position;
    for (let i = 0; i < p.count; i++) {                   // taper to a point
      const seg = Math.floor(i / 9) / 30;
      const c = curve.getPoint(Math.min(1, seg));
      const v = new THREE.Vector3().fromBufferAttribute(p, i).sub(c).multiplyScalar(1.0 - 0.78 * seg).add(c);
      p.setXYZ(i, v.x, v.y, v.z);
    }
    tg.computeVertexNormals();
    arms.push(P(new THREE.Mesh(tg, body)));
    for (const u of [0.3, 0.45, 0.6, 0.72]) {             // suckers on the underside
      const c = curve.getPoint(u);
      const sk = P(new THREE.Mesh(new THREE.SphereGeometry(s * 0.075 * (1 - u * 0.6), 6, 5), sucker));
      sk.position.copy(c).add(new THREE.Vector3(0, -s * 0.13 * (1 - u * 0.7), 0));
    }
  }
  return {
    group: g, parts, colorOnly, eyes,
    setState(st) { body.color.set(KU_COL[st] || KU_COL.orange); },
    setMix(a, b, u) { body.color.set(KU_COL[a]).lerp(new THREE.Color(KU_COL[b]), Math.min(1, Math.max(0, u))); },
    setHex(h) { body.color.set(h); },
    blink(on) { eyes.forEach(e => e.scale.y = on ? 0.15 : 1); }
  };
}

// ------------------------------------------------------------------ 엄마 (해녀, 41)
function makeMom(THREE, toon, opts = {}) {
  const C = Object.assign({suit: 0x262a36, suitHi: 0x3a4152, skin: 0xe2a882, tewak: 0xf2781e, net: 0xe8e2cc, mask: 0x8a96a4,
                           lens: 0xbfe0ea, belt: 0x4a3a30}, opts.colors || {});
  const g = new THREE.Group(), parts = [], colorOnly = [];
  const P = (m, parent = g) => { parent.add(m); parts.push(m); m.castShadow = true; m.receiveShadow = true; return m; };
  const rubberRamp = new THREE.DataTexture(new Uint8Array([55,55,55,255, 120,120,120,255, 120,120,120,255, 135,135,135,255,
    135,135,135,255, 150,150,150,255, 150,150,150,255, 255,255,255,255]), 8, 1);
  rubberRamp.minFilter = rubberRamp.magFilter = THREE.NearestFilter; rubberRamp.needsUpdate = true;
  const suit = new THREE.MeshToonMaterial({color: 0x2e3546, gradientMap: rubberRamp}), skin = toon(C.skin);
  suit.side = THREE.DoubleSide;
  // torso: fitted wetsuit, broad shoulders, solid working body
  const torso = [[0.0, 1.38], [0.07, 1.375], [0.13, 1.35], [0.165, 1.31], [0.172, 1.24], [0.16, 1.16], [0.132, 1.04], [0.145, 0.95],
                 [0.172, 0.86], [0.17, 0.8], [0.14, 0.74]].map(([r, y]) => new THREE.Vector2(r, y));
  const body = P(new THREE.Mesh(new THREE.LatheGeometry(torso, 40), suit)); body.scale.set(1, 1, 0.74);
  // a light seam line down the front and an orange-lined zip (colour accents read in silhouette)
  const seam = P(new THREE.Mesh(new THREE.BoxGeometry(0.012, 0.5, 0.012), toon(C.suitHi)));
  seam.position.set(0, 1.1, 0.135);
  // weight belt with lead blocks, and the 빗창 (abalone pick) tucked in it
  const belt = P(new THREE.Mesh(new THREE.TorusGeometry(0.142, 0.018, 6, 30), toon(C.belt)));
  belt.position.y = 0.97; belt.rotation.x = Math.PI / 2; belt.scale.set(1, 0.72, 1);
  for (let k = 0; k < 4; k++) {
    const a = -0.9 + k * 0.6;
    const lead = P(new THREE.Mesh(new THREE.BoxGeometry(0.05, 0.04, 0.025), toon(0x6a6e78)));
    lead.position.set(Math.sin(a) * 0.145, 0.97, Math.cos(a) * 0.105); lead.rotation.y = a;
  }
  const pick = P(new THREE.Mesh(new THREE.CylinderGeometry(0.006, 0.004, 0.26, 6), toon(0x8a8d94)));
  pick.position.set(0.13, 0.93, 0.07); pick.rotation.z = 0.25;
  // legs + booties
  const legs = {};
  for (const sx of [-1, 1]) {
    const lp = new THREE.Group(); lp.position.set(sx * 0.082, 0.81, 0); g.add(lp); legs[sx] = lp;
    const th = P(new THREE.Mesh(new THREE.CylinderGeometry(0.072, 0.056, 0.4, 16), suit), lp); th.position.y = -0.2; th.userData.idKey = 'momLeg' + sx;
    const kn = new THREE.Group(); kn.position.y = -0.39; lp.add(kn); lp.userData.knee = kn;
    P(new THREE.Mesh(new THREE.SphereGeometry(0.056, 14, 10), suit), kn).userData.idKey = 'momLeg' + sx;
    const shin = P(new THREE.Mesh(new THREE.CylinderGeometry(0.056, 0.042, 0.37, 16), suit), kn); shin.position.y = -0.185; shin.userData.idKey = 'momLeg' + sx;
    const foot = P(new THREE.Mesh(new THREE.SphereGeometry(0.06, 14, 10), suit), kn);
    foot.scale.set(0.8, 0.55, 1.6); foot.position.set(sx * 0.006, -0.385, 0.035); kn.userData.foot = foot;
  }
  // arms
  const arms = {};
  for (const sx of [-1, 1]) {
    const pv = new THREE.Group(); pv.position.set(sx * 0.178, 1.3, 0); g.add(pv);
    const ac = new THREE.CatmullRomCurve3([new THREE.Vector3(0, 0.03, 0), new THREE.Vector3(0, -0.15, 0), new THREE.Vector3(0, -0.29, 0.015),
                                           new THREE.Vector3(0, -0.43, 0.05), new THREE.Vector3(0, -0.55, 0.08)]);
    const ag = new THREE.TubeGeometry(ac, 24, 0.05, 12, false);
    const ap = ag.attributes.position;
    for (let i = 0; i < ap.count; i++) {
      const seg = Math.floor(i / 13) / 24, c = ac.getPoint(Math.min(1, seg));
      const k = seg < 0.08 ? 1.0 : 1.0 - 0.3 * seg;
      const v = new THREE.Vector3().fromBufferAttribute(ap, i).sub(c).multiplyScalar(k).add(c); ap.setXYZ(i, v.x, v.y, v.z);
    }
    ag.computeVertexNormals();
    P(new THREE.Mesh(ag, suit), pv);
    const cap = P(new THREE.Mesh(new THREE.SphereGeometry(0.05, 14, 10), suit), pv); cap.position.y = 0.03;
    const hand = new THREE.Group(); hand.position.set(0, -0.59, 0.085); pv.add(hand);
    const palm = P(new THREE.Mesh(new THREE.CapsuleGeometry(0.03, 0.04, 4, 10), skin), hand); palm.scale.set(1.15, 1, 0.75);
    const thumb = P(new THREE.Mesh(new THREE.CapsuleGeometry(0.013, 0.026, 3, 8), skin), hand);
    thumb.position.set(-sx * 0.026, 0.008, 0.016); thumb.rotation.z = sx * 0.6;
    pv.rotation.z = sx * 0.12;
    arms[sx] = pv; pv.userData.hand = hand;
  }
  // head + hood
  const head = new THREE.Group(); head.position.set(0, 1.545, 0.01); g.add(head);
  const R = 0.13;
  const neck = P(new THREE.Mesh(new THREE.CylinderGeometry(0.06, 0.075, 0.12, 14), suit)); neck.position.y = 1.42;
  const skull = P(new THREE.Mesh(new THREE.SphereGeometry(R, 36, 26), skin), head);
  skull.scale.set(0.95, 1.06, 0.98); skull.receiveShadow = false;
  skull.material.emissive = new THREE.Color(C.skin).multiplyScalar(0.45);
  const face = makeFaceDecal(THREE, R, {eyeW: 48, eyeH: 58, eyeY: 1.66, eyeX: 0.36, lash: 15, brow: true, browW: 4.5, mouthY: 2.06,
                                        blush: 0.4, iris: '#5c3a26', lip: '#b8504a', nose: '#b9785c'});
  face.mesh.scale.copy(skull.scale); head.add(face.mesh); colorOnly.push(face.mesh);
  // hood: a shell over the skull with an oval face opening, flowing into the neck
  const hp = [], hi = []; const NP = 160, NT = 80;
  const inFace = (phi, th) => { const a = Math.atan2(Math.sin(phi), Math.cos(phi)); return (a / 1.0) ** 2 + ((th - 1.76) / 0.74) ** 2 < 1; };
  for (let i = 0; i <= NP; i++) for (let j = 0; j <= NT; j++) {
    const phi = i / NP * Math.PI * 2, th = j / NT * 2.75;
    const r = R * 1.09 + R * 0.12 * Math.max(0, (th - 2.2) / 0.55);
    hp.push(r * Math.sin(th) * Math.sin(phi) * 0.95, r * Math.cos(th) * 1.06, r * Math.sin(th) * Math.cos(phi) * 0.98);
  }
  for (let i = 0; i < NP; i++) for (let j = 0; j < NT; j++) {
    const phi = (i + 0.5) / NP * Math.PI * 2, th = (j + 0.5) / NT * 2.75;
    if (inFace(phi, th)) continue;
    const a0 = i * (NT + 1) + j, b0 = (i + 1) * (NT + 1) + j;
    hi.push(a0, b0, a0 + 1, b0, b0 + 1, a0 + 1);
  }
  const hg = new THREE.BufferGeometry(); hg.setAttribute('position', new THREE.Float32BufferAttribute(hp, 3)); hg.setIndex(hi);
  hg.computeVertexNormals();
  const hood = P(new THREE.Mesh(hg, suit), head); hood.receiveShadow = false;
  // 왕눈 mask: one big round lens in a grey rim, pushed up on the forehead (setMask(1) pulls it down over the eyes)
  const maskG = new THREE.Group(); head.add(maskG);
  const rim = P(new THREE.Mesh(new THREE.TorusGeometry(0.068, 0.012, 8, 32), toon(C.mask)), maskG);
  const lens = new THREE.Mesh(new THREE.CircleGeometry(0.066, 32), new THREE.MeshToonMaterial({color: C.lens, transparent: true, opacity: 0.45}));
  lens.position.z = 0.002; maskG.add(lens); colorOnly.push(lens);
  const strap = P(new THREE.Mesh(new THREE.TorusGeometry(R * 1.12, 0.008, 5, 40), toon(0x30343e)), head);
  function setMask(u) {                              // 0 = up on the forehead, 1 = over the eyes
    const th = 0.9 + 0.68 * u;
    maskG.position.set(0, Math.cos(th) * R * 1.13, Math.sin(th) * R * 1.13);
    maskG.rotation.x = -(Math.PI / 2 - th);
    strap.rotation.x = Math.PI / 2 - (Math.PI / 2 - th) * 0.9;
    face.mesh.visible = true;
  }
  setMask(0);
  // 테왁 + 망사리 (float with a net bag), hung from a rope in her left hand
  const tw = new THREE.Group(); g.add(tw);
  const ball = P(new THREE.Mesh(new THREE.SphereGeometry(0.15, 28, 20), toon(C.tewak)), tw); ball.scale.set(1, 0.88, 1);
  const band = P(new THREE.Mesh(new THREE.TorusGeometry(0.15, 0.008, 5, 36), toon(0x3a2a20)), tw); band.rotation.x = Math.PI / 2;
  const netM = toon(C.net);
  for (let k = 0; k < 7; k++) {                        // the net bag: ribs hanging under the float
    const a = k / 7 * Math.PI * 2 + 0.3 * Math.sin(k * 2.1);
    const c = new THREE.QuadraticBezierCurve3(new THREE.Vector3(Math.cos(a) * 0.12, -0.08, Math.sin(a) * 0.12),
      new THREE.Vector3(Math.cos(a) * 0.17, -0.24 - 0.03 * Math.sin(k), Math.sin(a) * 0.17), new THREE.Vector3(Math.cos(a) * 0.04, -0.4, Math.sin(a) * 0.04));
    P(new THREE.Mesh(new THREE.TubeGeometry(c, 10, 0.0028, 4), netM), tw);
  }
  for (let j = 1; j <= 2; j++) {
    const y = -0.08 - j * 0.08, r = 0.13 + 0.03 * Math.sin(j * 1.2) - (j === 3 ? 0.05 : 0);
    const ring = P(new THREE.Mesh(new THREE.TorusGeometry(r, 0.0028, 4, 30), netM), tw); ring.scale.set(1, 1, 1); ring.position.y = y; ring.rotation.x = Math.PI / 2;
  }
  tw.position.set(-0.33, 0.6, 0.18);
  const rope = P(new THREE.Mesh(new THREE.TubeGeometry(new THREE.QuadraticBezierCurve3(
    new THREE.Vector3(-0.24, 0.76, 0.12), new THREE.Vector3(-0.3, 0.77, 0.16), new THREE.Vector3(-0.33, 0.74, 0.18)), 8, 0.006, 4), toon(0xb8a888)));
  arms[-1].rotation.set(-0.15, 0, -0.2);

  return {
    group: g, parts, colorOnly, head, arms, tewak: tw,
    setFace(f) { face.draw(f); }, setMask,
    pose(p) {
      head.rotation.set(p.pitch || 0, p.yaw || 0, p.roll || 0);
      if (p.armR !== undefined) arms[1].rotation.set(p.armRx || 0, 0, 0.12 + p.armR);
      if (p.armL !== undefined) arms[-1].rotation.set(p.armLx || 0, 0, -0.12 - p.armL);
      if (p.legL !== undefined) { legs[-1].rotation.set(p.legL, 0, 0); legs[1].rotation.set(p.legR, 0, 0); }
      for (const [k, v] of [[-1, p.kneeL], [1, p.kneeR]]) if (v !== undefined) { legs[k].userData.knee.rotation.x = v; legs[k].userData.knee.userData.foot.rotation.x = 0.8 * v; }
    }
  };
}
