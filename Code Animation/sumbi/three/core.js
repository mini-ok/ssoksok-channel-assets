// 〈숨비〉 production core: renderer, toon materials, object registry, render passes, camera keys.
// Pages: film.html?cut=N builds an environment + a cut, then render.js calls window.renderAt(t, pass).
// Passes: color (toon) / id (flat per object) / normal / depth (LINEAR: 1 - dist/DR) / char (character silhouette).
function makeCore(o = {}) {
  const W = 1920, H = 1040;
  const renderer = new THREE.WebGLRenderer({canvas: document.getElementById('c'), antialias: true, alpha: true, preserveDrawingBuffer: true});
  renderer.setPixelRatio(1); renderer.shadowMap.enabled = true; renderer.shadowMap.type = THREE.BasicShadowMap;
  renderer.outputColorSpace = THREE.SRGBColorSpace;
  const scene = new THREE.Scene();
  const cam = new THREE.PerspectiveCamera(o.fov || 38, W / H, o.near || 0.05, o.far || 400);
  let seed = o.seed || 7;
  const rnd = () => { seed = (seed * 16807) % 2147483647; return (seed - 1) / 2147483646; };
  const rr = (a, b) => a + (b - a) * rnd();
  const ramp = new THREE.DataTexture(new Uint8Array(o.ramp || [75, 75, 75, 255, 155, 155, 155, 255, 255, 255, 255, 255]), (o.ramp || [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]).length / 4, 1);
  ramp.minFilter = ramp.magFilter = THREE.NearestFilter; ramp.needsUpdate = true;
  const toon = (hex, extra) => Object.assign(new THREE.MeshToonMaterial({color: hex, gradientMap: ramp}), extra || {});
  const objects = [], charSet = new Set(), colorOnly = [], idKeys = {};
  let nextId = 1;
  function reg(m, isChar) {
    if (m.userData.id) return m;
    const k = m.userData.idKey; m.userData.id = k ? (idKeys[k] = idKeys[k] || nextId++) : nextId++;
    m.userData.colorMat = m.material; objects.push(m); if (isChar) charSet.add(m); return m;
  }
  function add(m, opt = {}) {
    m.castShadow = opt.cast !== false; m.receiveShadow = opt.recv !== false;
    (opt.parent || scene).add(m);
    if (opt.colorOnly) { colorOnly.push(m); return m; }
    return reg(m, !!opt.char);
  }
  function addChar(c, parent) {               // c from makeSol / makeMom / makeKuruk / makeCrow...
    (parent || scene).add(c.group); c.parts.forEach(m => reg(m, true)); colorOnly.push(...(c.colorOnly || [])); return c;
  }
  const ss = x => { x = Math.min(1, Math.max(0, x)); return x * x * (3 - 2 * x); };
  const lerp = (a, b, u) => a + (b - a) * u;
  const v3 = (x, y, z) => new THREE.Vector3(x, y, z);
  const q2 = t => Math.floor(t * 12 + 1e-6) / 12;          // on twos
  const q3 = t => Math.floor(t * 8 + 1e-6) / 8;            // on threes
  // camera keys: [[t, pos, look, fov?], ...]; smoothstep inside each segment, evaluated on twos
  function camKeys(keys, opt = {}) {
    return (t) => {
      const tq = opt.ones ? t : q2(t);
      let i = 0; while (i < keys.length - 2 && tq > keys[i + 1][0]) i++;
      const a = keys[i], b = keys[Math.min(i + 1, keys.length - 1)];
      const u = b === a ? 0 : (opt.linear ? Math.min(1, Math.max(0, (tq - a[0]) / (b[0] - a[0]))) : ss((tq - a[0]) / (b[0] - a[0])));
      cam.position.lerpVectors(a[1], b[1], u);
      const look = new THREE.Vector3().lerpVectors(a[2], b[2], u);
      if (a[3] || b[3]) { cam.fov = lerp(a[3] || cam.fov, b[3] || a[3], u); cam.updateProjectionMatrix(); }
      if (opt.shake) { const s = opt.shake(tq); cam.position.x += s * Math.sin(tq * 37); cam.position.y += s * Math.cos(tq * 29); }
      cam.lookAt(look);
      if (opt.roll) cam.rotateZ(opt.roll(tq));
    };
  }
  const F = {THREE, W, H, renderer, scene, cam, rnd, rr, ramp, toon, objects, charSet, colorOnly, reg, add, addChar, ss, lerp, v3, q2, q3, camKeys,
             DR: o.DR || 30, bg: o.bg || new THREE.Color(0x000000), onFrame: null, camFn: null, meta: {}};
  let built = false;
  function build() {
    const normalMat = new THREE.MeshNormalMaterial({side: THREE.DoubleSide});
    const depthMat = new THREE.ShaderMaterial({side: THREE.DoubleSide, uniforms: {DR: {value: F.DR}},
      vertexShader: 'varying float vD; void main(){ vec4 mv = modelViewMatrix * vec4(position, 1.0); vD = -mv.z; gl_Position = projectionMatrix * mv; }',
      fragmentShader: 'uniform float DR; varying float vD; void main(){ float v = clamp(1.0 - vD / DR, 0.0, 1.0); gl_FragColor = vec4(v, v, v, 1.0); }'});
    const white = new THREE.MeshBasicMaterial({color: 0xffffff, side: THREE.DoubleSide}), black = new THREE.MeshBasicMaterial({color: 0, side: THREE.DoubleSide});
    F._pm = {normalMat, depthMat, white, black};
    built = true;
  }
  function idMatOf(o2) {
    if (!o2.userData.idMat) { const id = o2.userData.id;
      o2.userData.idMat = new THREE.MeshBasicMaterial({color: new THREE.Color(((id * 97) % 256) / 255, ((id * 57 + 40) % 256) / 255, ((id * 23 + 90) % 256) / 255), side: THREE.DoubleSide}); }
    return o2.userData.idMat;
  }
  window.renderAt = (t, pass) => {
    if (!built) build();
    if (F.onFrame) F.onFrame(t);
    if (F.camFn) F.camFn(t);
    colorOnly.forEach(m => m.visible = pass === 'color' && m.userData.on !== false);
    const fog = scene.fog;
    if (pass === 'color') { scene.background = F.bg; objects.forEach(m => m.material = m.userData.colorMat); }
    else {
      scene.background = new THREE.Color(0); scene.fog = null;
      const {normalMat, depthMat, white, black} = F._pm;
      objects.forEach(m => {
        if (m.userData.noLine && pass !== 'char') { m.material = black; return; }
        let mat = pass === 'id' ? idMatOf(m) : pass === 'normal' ? normalMat : pass === 'depth' ? depthMat : (charSet.has(m) ? white : black);
        const cm = m.userData.colorMat;
        if (cm && cm.alphaTest > 0 && cm.map) {
          m.userData.pm = m.userData.pm || {};
          if (!m.userData.pm[pass]) {
            const k = mat.clone(); k.alphaTest = cm.alphaTest;
            if (k.isShaderMaterial) { k.uniforms = Object.assign({}, k.uniforms, {map: {value: cm.map}, at: {value: cm.alphaTest}});
              k.vertexShader = 'varying float vD; varying vec2 vU; void main(){ vU = uv; vec4 mv = modelViewMatrix * vec4(position, 1.0); vD = -mv.z; gl_Position = projectionMatrix * mv; }';
              k.fragmentShader = 'uniform float DR; uniform sampler2D map; uniform float at; varying float vD; varying vec2 vU; void main(){ if (texture2D(map, vU).a < at) discard; float v = clamp(1.0 - vD / DR, 0.0, 1.0); gl_FragColor = vec4(v, v, v, 1.0); }'; }
            else if (pass === 'normal') {
              mat = new THREE.ShaderMaterial({side: THREE.DoubleSide, uniforms: {map: {value: cm.map}, at: {value: cm.alphaTest}},
                vertexShader: 'varying vec3 vN; varying vec2 vU; void main(){ vU = uv; vN = normalize(normalMatrix * normal); gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0); }',
                fragmentShader: 'uniform sampler2D map; uniform float at; varying vec3 vN; varying vec2 vU; void main(){ if (texture2D(map, vU).a < at) discard; vec3 n = normalize(vN); if (!gl_FrontFacing) n = -n; gl_FragColor = vec4(n * 0.5 + 0.5, 1.0); }'});
              m.userData.pm[pass] = mat; m.material = mat; return; }
            else { k.alphaMap = null; k.map = cm.map; if (k.color) k.color = k.color.clone(); if (pass !== 'normal') { k.onBeforeCompile = (sh) => { sh.fragmentShader = sh.fragmentShader.replace('#include <map_fragment>', '#include <map_fragment>\n diffuseColor.rgb = diffuse;'); }; } }
            m.userData.pm[pass] = k;
          }
          mat = m.userData.pm[pass];
        }
        m.material = mat;
      });
    }
    renderer.render(scene, cam); scene.fog = fog; return true;
  };
  window.info = () => objects.length;
  window.meta = () => Object.assign({DR: F.DR}, F.meta);
  return F;
}
// sky dome: vertical gradient, colour pass only
function skyDome(F, stops, R = 300) {
  const THREE = F.THREE, g = new THREE.SphereGeometry(R, 48, 24), p = g.attributes.position, col = [];
  const cs = stops.map(([y, h]) => [y, new THREE.Color(h)]);
  for (let i = 0; i < p.count; i++) {
    const y = p.getY(i) / R; let c = cs[0][1].clone();
    for (let k = 0; k < cs.length - 1; k++) if (y >= cs[k][0]) c = cs[k][1].clone().lerp(cs[k + 1][1], Math.min(1, (y - cs[k][0]) / (cs[k + 1][0] - cs[k][0])));
    col.push(c.r, c.g, c.b);
  }
  g.setAttribute('color', new THREE.Float32BufferAttribute(col, 3));
  const m = new THREE.Mesh(g, new THREE.MeshBasicMaterial({vertexColors: true, side: THREE.BackSide, fog: false, depthWrite: false}));
  m.renderOrder = -10; F.add(m, {colorOnly: true}); return m;
}
// canvas texture helper
function canvasTex(F, w, h, draw) {
  const c = document.createElement('canvas'); c.width = w; c.height = h; draw(c.getContext('2d'), w, h);
  const t = new F.THREE.CanvasTexture(c); t.colorSpace = F.THREE.SRGBColorSpace; return t;
}
// deformed lava rock
function lavaRock(F, s, col, opt = {}) {
  const THREE = F.THREE, g = new THREE.IcosahedronGeometry(s, opt.detail || 1), p = g.attributes.position;
  const a = F.rr(0, 9), b = F.rr(0, 9);
  for (let i = 0; i < p.count; i++) {
    const v = new THREE.Vector3().fromBufferAttribute(p, i);
    const k = 1 + 0.24 * Math.sin(v.x / s * 5.1 + a) * Math.cos(v.z / s * 3.7 + b) + 0.14 * Math.cos(v.y / s * 6.3 + a);
    v.multiplyScalar(k); v.y *= (opt.flat || 0.62); p.setXYZ(i, v.x, v.y, v.z);
  }
  g.computeVertexNormals();
  return new THREE.Mesh(g, F.toon(col));
}
