// 〈심장의 휴가〉 컷 → Blender용 내보내기(페이지 안에서 실행). film.html이 만든 장면을 그대로 굽는다.
//  - 공간(set) + 출연 캐릭터 + 카메라를 한 그룹으로 묶어 glTF(GLB)로: 모든 노드의 위치·회전·크기를 프레임마다 키로 구움
//  - 보였다 숨었다 하는 물건(휴가권 등)은 숨는 프레임에 크기를 아주 작게(glTF엔 '보이기' 키가 없음)
//  - 해먹 처짐은 모프 타깃 1개 + 가중치 키로
//  - 얼굴(몸 텍스처)은 프레임마다 상태(표정·시선·깜빡임)를 기록하고, 서로 다른 상태만 PNG로 → Blender에서 이미지 시퀀스로 바꿔 끼움
//  - 카메라 화각·조명 세기·안개 색은 JSON으로
import * as THREE from 'three';
import { GLTFExporter } from 'three/addons/exporters/GLTFExporter.js';

const FPS = 24;
const q3 = v => Math.round(v * 1000) / 1000;

export async function exportCut(id, { frame, CUTS, SETS, R, scene, camera }) {
  window.NORENDER = true;
  const cut = CUTS[id], S = SETS[cut.set], n = Math.round(cut.dur * FPS);
  frame(id, 0);
  // 1) 내보낼 뿌리: 공간 + 출연진 + 카메라
  const root = new THREE.Group(); root.name = 'EXPORT_' + id; scene.add(root);
  root.add(S.group); for (const k of cut.cast) root.add(R[k].root); root.add(camera);
  // ---- 보완 1) 미리 훑기: 프레임마다 바뀌는 꼭짓점(커튼)·캔버스 화면·무늬 위치를 찾는다(0, 37%, 73%, 끝 근처 시점 비교)
  const faceMapSet = new Set(cut.cast.map(k => R[k].meshes.body.material.map));
  const meshesNow = []; root.traverse(o => { if (o.isMesh && !o.isInstancedMesh) meshesNow.push(o); });
  const texOf = m => ['map', 'emissiveMap'].map(k => m && m[k]).filter(t => t && !faceMapSet.has(t));
  const probeT = [0, 0.37, 0.73, 0.97].map(r => r * cut.dur);
  const pv = new Map(), tv = new Map(), uvv = new Map();
  probeT.forEach((t, j) => { frame(id, t);
    for (const o of meshesNow) { const a = o.geometry.attributes.position; if (!a) continue; const r = pv.get(o.geometry) || { v: a.version, ch: false, users: new Set() }; if (j && a.version !== r.v) r.ch = true; r.users.add(o); pv.set(o.geometry, r);
      for (const m of (Array.isArray(o.material) ? o.material : [o.material])) for (const tx of texOf(m)) {
        const q = tv.get(tx) || { v: tx.version, ch: false, mats: new Set() }; if (j && tx.version !== q.v) q.ch = true; q.mats.add(m); tv.set(tx, q);
        const u = uvv.get(tx) || { o: tx.offset.toArray().join(), ch: false, mats: new Set() }; if (j && tx.offset.toArray().join() !== u.o) u.ch = true; u.mats.add(m); uvv.set(tx, u); } } });
  frame(id, 0);
  const deformGeos = [...pv].filter(([g, r]) => r.ch && ![...r.users].some(o => o.name.startsWith('hammock') || (o.material && o.material.opacity === 0))).map(([g, r]) => ({ g, users: [...r.users], snaps: [] }));
  const screenTex = [...tv].filter(([t, q]) => q.ch && t.image && t.image.getContext).map(([t, q]) => ({ t, mats: [...q.mats], fps: t.image.width * t.image.height <= 128 * 96 ? 12 : 24, states: new Map(), imgs: [], idx: [] }));
  const uvTex = [...uvv].filter(([t, u]) => u.ch).map(([t, u]) => ({ t, mats: [...u.mats], off: [] }));
  // ---- 보완 2) 스프라이트(꿈 방울·해 후광) → 카메라를 향해 도는 평면(같은 그림·투명도)
  const sprites = []; root.traverse(o => { if (o.isSprite) sprites.push(o); });
  const bills = sprites.map(sp => { const sm = sp.material;
    const m = new THREE.MeshBasicMaterial({ map: sm.map, color: sm.color.clone(), transparent: true, opacity: sm.opacity, depthWrite: false, side: THREE.DoubleSide, fog: false });
    const b = new THREE.Mesh(new THREE.PlaneGeometry(1, 1), m); b.name = 'bill'; sp.parent.add(b); return { sp, b }; });
  // ---- 보완 3) 움직이는 인스턴스(혈구 흐름·먼지·미생물·거품) → 하나하나 따로 움직이는 물체
  const insts = []; root.traverse(o => { if (o.isInstancedMesh) insts.push(o); });
  const instProxies = insts.map(im => { const g = new THREE.Group(); g.name = 'inst'; im.parent.add(g); g.position.copy(im.position); g.quaternion.copy(im.quaternion); g.scale.copy(im.scale);
    const kids = []; for (let i = 0; i < im.instanceMatrix.count; i++) { const k = new THREE.Mesh(im.geometry, im.material); k.name = 'i'; g.add(k); kids.push(k); } return { im, g, kids }; });
  const _m4 = new THREE.Matrix4(), _q = new THREE.Quaternion(), _pq = new THREE.Quaternion();
  const _v = new THREE.Vector3(), _cp = new THREE.Vector3();
  const syncProxies = () => {
    camera.updateMatrixWorld(true); camera.getWorldQuaternion(_q); camera.getWorldPosition(_cp);
    for (const { sp, b } of bills) { b.position.copy(sp.position); b.scale.set(sp.scale.x, sp.scale.y, 1); b.visible = sp.visible; b.material.opacity = sp.material.opacity; b.material.color.copy(sp.material.color);
      sp.parent.updateMatrixWorld(true); sp.parent.getWorldQuaternion(_pq); b.quaternion.copy(_pq.invert().multiply(_q)); }
    for (const { im, g, kids } of instProxies) { g.visible = im.visible; g.position.copy(im.position); g.quaternion.copy(im.quaternion); g.scale.copy(im.scale);
      const small = (im.geometry.boundingSphere || (im.geometry.computeBoundingSphere(), im.geometry.boundingSphere)).radius < 0.2; g.updateMatrixWorld(true);
      kids.forEach((k, i) => { im.getMatrixAt(i, _m4); _m4.decompose(k.position, k.quaternion, k.scale); k.visible = i < im.count;
        // 렌즈 바로 앞의 작은 먼지·방울은 Blender 심도에서 화면을 덮는 큰 얼룩으로 번지므로 그 프레임엔 숨김
        if (small && k.visible) { _v.copy(k.position).applyMatrix4(g.matrixWorld); if (_v.distanceTo(_cp) < 1.0) k.visible = false; } }); }
  };
  syncProxies();
  // 이름: 캐릭터 부위는 "heart:body"처럼, 나머지는 원래 이름 + 번호(겹치지 않게)
  const charOf = new Map();
  for (const k of cut.cast) { R[k].root.name = k; R[k].root.traverse(o => charOf.set(o, k)); for (const [nm, m] of Object.entries(R[k].meshes)) m.name = `${k}:${nm}`; }
  let seq = 0; const used = new Set();
  root.traverse(o => { if (o === root) return; let nm = o.name || o.type; if (!(charOf.has(o) && o.name.includes(':')) && o !== camera) nm = `${nm}#${seq++}`; if (o === camera) nm = 'CAMERA'; while (used.has(nm)) nm += '_'; used.add(nm); o.name = nm; });
  // 2) 해먹(있으면): 처짐 0과 1.15를 모프로
  const ham = S.group.getObjectByName ? (() => { let h = null; S.group.traverse(o => { if (o.isMesh && o.name.startsWith('hammock')) h = o; }); return h; })() : null;
  let hamInfo = null;
  if (ham && S.setHammock) {
    S.setHammock(0); const p0 = ham.geometry.attributes.position.array.slice();
    S.setHammock(1.15); const p1 = ham.geometry.attributes.position.array.slice();
    let mid = 0, best = 1e9; for (let i = 0; i < p0.length / 3; i++) { const d = p1[i * 3 + 1] - p0[i * 3 + 1]; if (d < best) { best = d; mid = i; } }
    hamInfo = { p0, p1, mid, y0: p0[mid * 3 + 1], y1: p1[mid * 3 + 1], w: [] };
  }
  // 3) 프레임마다 기록
  const nodes = []; root.traverse(o => { if (o !== root) nodes.push(o); });
  const lightsRec = nodes.filter(o => o.isLight && !o.isAmbientLight && !o.isHemisphereLight).map(o => ({ o, i: [], c: [] }));
  const rec = nodes.map(() => ({ p: new Float32Array(n * 3), q: new Float32Array(n * 4), s: new Float32Array(n * 3), vis: 0 }));
  const faces = Object.fromEntries(cut.cast.map(k => [k, { states: [], idx: [] }]));
  const camInfo = [], lightInfo = [], focusInfo = [];
  const heroMesh = cut.cast.includes('heart') ? R.heart.meshes.body : cut.cast.length ? R[cut.cast[0]].meshes.body : null; const ray = new THREE.Raycaster(); ray.camera = camera;
  // 재질 애니메이션(전구·파이프 끝·경보처럼 박동·정전에 따라 빛이 바뀌는 것): 프레임마다 발광색×세기, 바탕색, 불투명도 기록
  const mats = []; root.traverse(o => { if (!o.isMesh) return; for (const m of (Array.isArray(o.material) ? o.material : [o.material])) if (m && !mats.includes(m)) mats.push(m); });
  const mrec = mats.map(() => ({ e: [], c: [], o: [] }));
  for (let f = 0; f < n; f++) {
    const out = frame(id, f / FPS) || {}; syncProxies();
    for (const d of deformGeos) d.snaps.push(Float32Array.from(d.g.attributes.position.array));
    for (const sc of screenTex) { if (f % (24 / sc.fps) === 0) { const cv = sc.t.image, W = Math.min(cv.width, 512), H = Math.round(cv.height * W / cv.width), fc = document.createElement('canvas'); fc.width = W; fc.height = H;
        const g = fc.getContext('2d'); g.translate(0, H); g.scale(1, -1); g.drawImage(cv, 0, 0, W, H); const url = fc.toDataURL('image/png');   // glTF UV(위아래 반대)에 맞게 뒤집음
        let j = sc.states.get(url); if (j === undefined) { j = sc.imgs.length; sc.imgs.push(url); sc.states.set(url, j); } sc.cur = j; } sc.idx.push(sc.cur); }
    for (const u of uvTex) u.off.push([q3(u.t.offset.x), q3(u.t.offset.y), q3(u.t.repeat.x), q3(u.t.repeat.y)]);
    lightsRec.forEach(L => { let v = L.o.visible; for (let p = L.o.parent; p && v; p = p.parent) v = p.visible; L.i.push(q3(v ? L.o.intensity : 0)); L.c.push(L.o.color.toArray().map(q3)); });
    nodes.forEach((o, i) => { const r = rec[i]; o.position.toArray(r.p, f * 3); o.quaternion.toArray(r.q, f * 4);
      const k = o.visible ? 1 : 1e-4; r.s[f * 3] = o.scale.x * k; r.s[f * 3 + 1] = o.scale.y * k; r.s[f * 3 + 2] = o.scale.z * k; if (o.visible) r.vis++; });
    camInfo.push(q3(camera.fov)); lightInfo.push(out);
    // 초점 거리: 주인공이 화면 안에 있으면 주인공까지, 없으면(소품 인서트 등) 화면 가운데에 보이는 물체까지
    { camera.updateMatrixWorld(true); const cp = camera.getWorldPosition(new THREE.Vector3()); let dist = null;
      if (heroMesh) { heroMesh.updateMatrixWorld(true); const hp = heroMesh.getWorldPosition(new THREE.Vector3()).add(new THREE.Vector3(0, 0.45, 0)); const nd = hp.clone().project(camera);
        let v = heroMesh.visible; for (let p = heroMesh.parent; p && v; p = p.parent) v = p.visible;
        if (v && nd.z < 1 && Math.abs(nd.x) < 0.95 && Math.abs(nd.y) < 0.95) { const dh = cp.distanceTo(hp);   // 벽 등에 가려 있으면 주인공이 안 보이는 것
          ray.set(cp, hp.clone().sub(cp).normalize()); ray.camera = camera; ray.far = dh; const block = ray.intersectObject(root, true).find(h => { if (charOf.has(h.object)) return false; let vv = h.object.visible; for (let p = h.object.parent; p && vv; p = p.parent) vv = p.visible; return vv && h.object.isMesh && !(h.object.material && h.object.material.transparent && h.object.material.opacity < 0.5); });
          ray.far = Infinity; if (!block || block.distance > dh - 0.4) dist = dh; } }
      if (dist === null) { ray.setFromCamera(new THREE.Vector2(0, 0), camera); const hits = ray.intersectObject(root, true).filter(h => { let v = h.object.visible; for (let p = h.object.parent; p && v; p = p.parent) v = p.visible; return v && h.object.isMesh && !(h.object.material && h.object.material.transparent && h.object.material.opacity < 0.5); });
        dist = hits.length ? hits[0].distance : 6; }
      focusInfo.push(q3(dist)); }
    mats.forEach((m, i) => { const r = mrec[i]; const e = m.emissive, k = m.emissiveIntensity ?? 1; r.e.push(e ? [q3(e.r), q3(e.g), q3(e.b), q3(k)] : null); r.c.push(m.color ? [q3(m.color.r), q3(m.color.g), q3(m.color.b)] : null); r.o.push(q3(m.opacity ?? 1)); });
    for (const k of cut.cast) { const st = R[k].st, key = [st.mood, q3(Math.round(st.look[0] * 10) / 10), q3(Math.round(st.look[1] * 10) / 10), st.blink > 0.82 ? 1 : st.blink > 0.4 ? 0.5 : 0].join('|');
      const F = faces[k]; let j = F.states.indexOf(key); if (j < 0) { j = F.states.length; F.states.push(key); } F.idx.push(j); }
    if (hamInfo) { const y = ham.geometry.attributes.position.array[hamInfo.mid * 3 + 1]; hamInfo.w.push(q3(Math.max(0, (hamInfo.y0 - y) / (hamInfo.y0 - hamInfo.y1)))); }
  }
  const same = (A) => A.every(v => JSON.stringify(v) === JSON.stringify(A[0]));
  const matAnim = {}; let mk = 0;
  mats.forEach((m, i) => { const r = mrec[i], d = {}; if (!same(r.e)) d.e = r.e; if (!same(r.c)) d.c = r.c; if (!same(r.o)) d.o = r.o;
    if (Object.keys(d).length) { m.name = `anim_${mk++}`; matAnim[m.name] = d; } });
  // 한 번도 안 보인 노드(충돌용 투명 기둥 등)는 빼고, 스프라이트·선은 glTF가 못 담으므로 뺌
  const drop = nodes.filter((o, i) => rec[i].vis === 0 || o.isSprite || o.isLine || o.isPoints || o.isInstancedMesh || (o.isMesh && !Array.isArray(o.material) && o.material.transparent && mrec[mats.indexOf(o.material)].o.every(v => v === 0)));
  const parents = drop.map(o => o.parent); drop.forEach(o => o.parent && o.parent.remove(o));
  // 4) 애니메이션 트랙(값이 변하는 것만)
  const times = Float32Array.from({ length: n }, (_, f) => f / FPS), tracks = [];
  const changes = (a, w) => { for (let f = 1; f < n; f++) for (let c = 0; c < w; c++) if (Math.abs(a[f * w + c] - a[c]) > 1e-5) return true; return false; };
  nodes.forEach((o, i) => { if (drop.includes(o)) return; const r = rec[i];
    if (changes(r.p, 3)) tracks.push(new THREE.VectorKeyframeTrack(`${o.uuid}.position`, times, r.p));
    if (changes(r.q, 4)) tracks.push(new THREE.QuaternionKeyframeTrack(`${o.uuid}.quaternion`, times, r.q));
    if (changes(r.s, 3)) tracks.push(new THREE.VectorKeyframeTrack(`${o.uuid}.scale`, times, r.s));
    // 첫 프레임 상태로 되돌림(정지 값이 0프레임과 맞게)
    o.position.fromArray(r.p, 0); o.quaternion.fromArray(r.q, 0); o.scale.fromArray(r.s, 0); o.visible = true; });
  if (hamInfo) { const g = ham.geometry; g.attributes.position.array.set(hamInfo.p0); g.attributes.position.needsUpdate = true;
    g.morphAttributes.position = [new THREE.Float32BufferAttribute(hamInfo.p1, 3)]; ham.updateMorphTargets(); ham.morphTargetInfluences[0] = hamInfo.w[0];
    if (changes(Float32Array.from(hamInfo.w), 1)) tracks.push(new THREE.NumberKeyframeTrack(`${ham.uuid}.morphTargetInfluences`, times, Float32Array.from(hamInfo.w))); }
  // 보완 4) 꼭짓점이 변하는 메시(커튼): 주성분 몇 개를 모프 타깃으로(0~1 가중치로 정규화)
  const deformInfo = [];
  for (const d of deformGeos) {
    const N3 = d.snaps[0].length, mean = new Float32Array(N3); d.snaps.forEach(sn => { for (let c = 0; c < N3; c++) mean[c] += sn[c] / n; });
    const D = d.snaps.map(sn => { const r = new Float32Array(N3); for (let c = 0; c < N3; c++) r[c] = sn[c] - mean[c]; return r; });
    const G = D.map(a => D.map(b => { let z = 0; for (let c = 0; c < N3; c++) z += a[c] * b[c]; return z; }));
    const total = G.reduce((z, r, i) => z + r[i], 0) || 1; const comps = []; let left = total;
    for (let k = 0; k < 6 && left / total > 0.004; k++) {
      let u = Array.from({ length: n }, (_, i) => Math.sin(i * 1.7 + k) + 0.5), lam = 0;
      for (let it = 0; it < 200; it++) { const w = G.map(r => r.reduce((z, x, j) => z + x * u[j], 0)); lam = Math.hypot(...w); if (!lam) break; u = w.map(x => x / lam); }
      if (!lam) break;
      for (let i = 0; i < n; i++) for (let j = 0; j < n; j++) G[i][j] -= lam * u[i] * u[j];
      const cvec = new Float32Array(N3); for (let i = 0; i < n; i++) for (let c = 0; c < N3; c++) cvec[c] += D[i][c] * u[i] / Math.sqrt(lam);
      const wts = D.map(r => { let z = 0; for (let c = 0; c < N3; c++) z += r[c] * cvec[c]; return z; });
      comps.push({ cvec, wts }); left -= lam; }
    const base = Float32Array.from(mean), targets = [], W = [];
    for (const { cvec, wts } of comps) { const lo = Math.min(...wts), hi = Math.max(...wts), sp = hi - lo || 1;
      for (let c = 0; c < N3; c++) base[c] += cvec[c] * lo;
      targets.push({ cvec, sp }); W.push(wts.map(w => q3((w - lo) / sp))); }
    const morphs = targets.map(({ cvec, sp }) => { const t = new Float32Array(N3); for (let c = 0; c < N3; c++) t[c] = base[c] + cvec[c] * sp; return new THREE.Float32BufferAttribute(t, 3); });
    d.g.attributes.position.array.set(base); d.g.attributes.position.needsUpdate = true; d.g.morphAttributes.position = morphs; d.g.computeVertexNormals();
    const times4 = []; const vals = []; for (let f = 0; f < n; f++) { times4.push(f / FPS); for (let k = 0; k < W.length; k++) vals.push(W[k][f]); }
    for (const o of d.users) { if (drop.includes(o)) continue; o.updateMorphTargets(); W.forEach((w, k) => o.morphTargetInfluences[k] = w[0]);
      tracks.push(new THREE.NumberKeyframeTrack(`${o.uuid}.morphTargetInfluences`, Float32Array.from(times4), Float32Array.from(vals))); }
    deformInfo.push({ meshes: d.users.map(o => o.name), comps: W.length, residual: q3(left / total) });
  }
  // 보완 5) 캔버스 화면·무늬 위치·점조명 → meta
  let sk = 0; const screens = {};
  for (const sc of screenTex) { for (const m of sc.mats) { if (!m.name || !m.name.startsWith('anim_')) m.name = `scr_${sk}`; }
    screens[`scr_${sk}`] = { mats: sc.mats.map(m => m.name), fps: sc.fps, idx: sc.idx, images: sc.imgs }; sk++; }
  let uk = 0; const uvAnim = {};
  for (const u of uvTex) { for (const m of u.mats) if (!m.name || !/^(anim|scr)_/.test(m.name)) m.name = `uv_${uk}`; uvAnim[`uv_${uk}`] = { mats: u.mats.map(m => m.name), off: u.off }; uk++; }
  const lightsMeta = {}; lightsRec.forEach(L => { if (drop.includes(L.o)) return; lightsMeta[L.o.name] = { type: L.o.type, i: same(L.i) ? [L.i[0]] : L.i, c: same(L.c) ? [L.c[0]] : L.c, dist: L.o.distance ?? 0 }; });
  const clip = new THREE.AnimationClip(id, cut.dur, tracks);
  // 5) 얼굴 PNG(서로 다른 상태만)
  const faceOut = {};
  for (const k of cut.cast) { const rig = R[k], F = faces[k], body = rig.meshes.body, cv = body.material.map.image, imgs = [];
    for (const key of F.states) { const [mood, lx, ly, bl] = key.split('|'); rig.setFace(mood, [+lx, +ly], +bl); if (rig.redrawNow) rig.redrawNow(); { const FS = Math.min(cv.width, +(window.FACE_RES || 1024)); const fc = document.createElement('canvas'); fc.width = FS; fc.height = Math.round(cv.height * FS / cv.width); const g = fc.getContext('2d'); g.translate(0, fc.height); g.scale(1, -1); g.drawImage(cv, 0, 0, fc.width, fc.height); imgs.push(fc.toDataURL('image/png')); } }   // glTF UV(위아래 반대)에 맞게 뒤집어 저장
    faceOut[k] = { mesh: body.name, idx: F.idx, images: imgs }; }
  // 6) GLB
  const glb = await new GLTFExporter().parseAsync(root, { binary: true, onlyVisible: false, animations: [clip], maxTextureSize: 2048, includeCustomExtensions: false });
  drop.forEach((o, i) => parents[i] && parents[i].add(o));
  const meta = { cut: id, fps: FPS, frames: n, set: cut.set, cast: cut.cast, fov: camInfo, focus: focusInfo, light: lightInfo.map(o => ({ key: o.key ?? 1.6, hemi: o.hemi ?? 0.4, env: o.env ?? 0.35, bloom: o.bloom ?? 0.5 })),
    atmo: S.atmo || null, mats: matAnim, hero: cut.cast.includes('heart') ? 'heart:body' : cut.cast.length ? `${cut.cast[0]}:body` : null, tracks: tracks.length, dropped: drop.length, lights: lightsMeta, uv: uvAnim, deform: deformInfo, bills: bills.length, insts: instProxies.reduce((z, p) => z + p.kids.length, 0) };
  return { glb: new Uint8Array(glb), meta, faces: faceOut, screens };
}

// 내보내기 전 차이 점검: glTF/Blender로 그대로 안 넘어가는 것을 컷마다 찾아 목록으로(내보내기 규칙: 점검 → 의논 → 보완 → 내보내기)
export function auditCut(id, { frame, CUTS, SETS, R, scene, camera }) {
  window.NORENDER = true;
  const cut = CUTS[id], S = SETS[cut.set], n = Math.round(cut.dur * FPS);
  frame(id, 0);
  const mine = new Set(); S.group.traverse(o => mine.add(o)); for (const k of cut.cast) R[k].root.traverse(o => mine.add(o));
  const faceMaps = new Set(cut.cast.map(k => R[k].meshes.body.material.map));
  const label = o => { const p = []; let x = o; while (x && x !== scene && p.length < 4) { p.unshift(x.name || x.type); x = x.parent; } const g = o.geometry ? '<' + o.geometry.type.replace('Geometry', '') + '>' : ''; const w = new THREE.Vector3(); o.getWorldPosition(w); return p.join('/') + g + '@' + [w.x, w.y, w.z].map(v => v.toFixed(1)).join(','); };
  const all = []; scene.traverse(o => all.push(o));
  const st = new Map();   // 객체별 관찰값
  const texSeen = new Map(), matSeen = new Map();
  const fog0 = scene.fog ? [scene.fog.color.getHexString(), scene.fog.near, scene.fog.far] : null; let fogVar = false;
  const bg0 = scene.background && scene.background.isColor ? scene.background.getHexString() : null; let bgVar = false;
  const bl = new Set();
  for (let f = 0; f < n; f++) {
    const out = frame(id, f / FPS) || {}; bl.add(q3(out.bloom ?? 0.5));
    if (scene.fog && fog0 && JSON.stringify([scene.fog.color.getHexString(), scene.fog.near, scene.fog.far]) !== JSON.stringify(fog0)) fogVar = true;
    if (bg0 && scene.background.getHexString() !== bg0) bgVar = true;
    scene.traverse(o => {
      let s = st.get(o); if (!s) { s = { iv: o.isInstancedMesh ? o.instanceMatrix.version : 0, inst: false, vis: 0, gv: null, geo: o.geometry, pv: o.geometry?.attributes?.position?.version, deform: false, geoswap: false, li: [] }; st.set(o, s); }
      let v = o.visible; for (let p = o.parent; p && v; p = p.parent) v = p.visible; if (v) s.vis++;
      if (o.geometry) { if (o.geometry !== s.geo) s.geoswap = true; else if (o.geometry.attributes?.position?.version !== s.pv) s.deform = true; }
      if (o.isInstancedMesh && o.instanceMatrix.version !== s.iv) s.inst = true;
      if (o.isLight) s.li.push(q3(v ? o.intensity : 0));
      if (v && (o.isMesh || o.isSprite)) for (const m of (Array.isArray(o.material) ? o.material : [o.material])) { if (!m) continue;
        let ms = matSeen.get(m); if (!ms) { ms = { vis: new Set(), users: new Set(), type: m.type, obc: m.onBeforeCompile !== THREE.Material.prototype.onBeforeCompile }; matSeen.set(m, ms); }
        ms.vis.add(m.visible); ms.users.add(o);
        for (const key of ['map', 'emissiveMap', 'alphaMap']) { const t = m[key]; if (!t) continue; let ts = texSeen.get(t); if (!ts) { ts = { v: t.version, off: t.offset.toArray().join(), rot: t.rotation, ver: false, uv: false, users: new Set(), slot: key }; texSeen.set(t, ts); }
          if (t.version !== ts.v) ts.ver = true; if (t.offset.toArray().join() !== ts.off || t.rotation !== ts.rot) ts.uv = true; ts.users.add(o); } }
    });
  }
  const rep = { cut: id, frames: n, instAnim: [], sprites: [], linesPoints: [], deform: [], geoswap: [], canvasAnim: [], uvAnim: [], lights: [], matVisible: [], shader: [], outside: [], fogVar, bgVar, bloom: [...bl].sort() };
  for (const o of all) { const s = st.get(o); if (!s || !s.vis) continue; const L = label(o), inside = mine.has(o);
    if (!inside && !o.isLight && !o.isCamera && (o.isMesh || o.isSprite || o.isLine || o.isPoints)) rep.outside.push(L);
    if (o.isSprite) rep.sprites.push(L + (inside ? '' : ' [밖]'));
    if (o.isLine || o.isPoints) rep.linesPoints.push(L);
    if (s.deform && o.isMesh) rep.deform.push(L + ` (${o.geometry.attributes.position.count}점)`);
    if (s.geoswap) rep.geoswap.push(L);
    if (s.inst) rep.instAnim.push(L + ` (${o.count}개)`);
    if (o.isLight && inside) rep.lights.push(`${L} ${o.type} ${Math.min(...s.li)}~${Math.max(...s.li)}`);
  }
  for (const [t, ts] of texSeen) { if (faceMaps.has(t)) continue; const u = [...ts.users].map(label).slice(0, 3).join(', ');
    if (ts.ver) rep.canvasAnim.push(`${ts.slot}: ${u}`); if (ts.uv) rep.uvAnim.push(`${ts.slot}: ${u}`); }
  for (const [m, ms] of matSeen) { const u = [...ms.users].map(label).slice(0, 2).join(', ');
    if (ms.vis.size > 1 || ms.vis.has(false)) rep.matVisible.push(u);
    if (/Shader|Toon|Lambert|Phong|Matcap|Normal|Depth/.test(ms.type) || ms.obc) rep.shader.push(`${ms.type}${ms.obc ? '+onBeforeCompile' : ''}: ${u}`); }
  return rep;
}
