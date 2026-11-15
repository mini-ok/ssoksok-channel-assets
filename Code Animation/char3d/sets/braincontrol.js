// 뇌의 관제실 — 보라·남색 별빛. 작은 모니터 벽, 반달 조종 책상, 뉴런처럼 얽힌 전선을 달리는 빛, 화이트보드, 낮잠용 간이침대
import * as THREE from 'three';
import { RoundedBoxGeometry } from 'three/addons/geometries/RoundedBoxGeometry.js';
import { clay } from '../chars3d.js';
import { canvasTex, mat, brass, glow, rng, setKit, makeWorld, platform, railing, onWallPos } from './common.js';

const R = 3.6;
export function buildBrainControl() {
  const kit = setKit(), { g, SOLID, add } = kit, rnd = rng(77);
  platform(kit, R, (c, w, h) => {   // 남색 바닥 + 회로 무늬
    c.fillStyle = '#1e1a3e'; c.fillRect(0, 0, w, h);
    c.strokeStyle = 'rgba(160,140,255,0.35)'; c.lineWidth = 5; const r2 = rng(5);
    for (let k = 0; k < 70; k++) { let x = r2() * w, y = r2() * h; c.beginPath(); c.moveTo(x, y); for (let s = 0; s < 4; s++) { if (r2() > 0.5) x += (r2() - 0.5) * 400; else y += (r2() - 0.5) * 400; c.lineTo(x, y); } c.stroke(); c.fillStyle = 'rgba(200,180,255,0.6)'; c.beginPath(); c.arc(x, y, 9, 0, 7); c.fill(); }
  }, '#14102a', ['#c8b8ff', '#8a6aff']);
  railing(kit, R, [[1.25, Math.PI * 2 - 1.25]], brass(), mat('#221c44', { roughness: 0.6 }));
  // 모니터 벽(뒤 곡면): 작은 화면 격자, 화면마다 다른 그림(파형·별·전구·하트·눈·물결)
  const screens = [], icons = ['wave', 'star', 'bulb', 'heart', 'eye', 'ripple', 'bars', 'dots'];
  const frameMat = clay('#3a3366', { roughness: 0.4 });
  for (let row = 0; row < 4; row++) for (let col = 0; col < 13; col++) {
    const a = -1.15 + col * 0.19, y = 0.75 + row * 0.5, [x, , z] = onWallPos(R - 0.25, a, y);
    const fr = add(new THREE.Mesh(new RoundedBoxGeometry(0.62, 0.44, 0.12, 2, 0.03), frameMat), 'monitorWall'); fr.position.set(x, y, z); fr.rotation.y = -a;
    const kind = icons[(row * 5 + col * 3) % icons.length];
    const tex = canvasTex(128, 96, () => {}); const sc = new THREE.Mesh(new THREE.PlaneGeometry(0.54, 0.36), new THREE.MeshBasicMaterial({ map: tex, toneMapped: false }));
    const [sx, , sz] = onWallPos(R - 0.32, a, y); sc.position.set(sx, y, sz); sc.rotation.y = -a; g.add(sc); screens.push({ tex, kind, ph: rnd() * 6, hue: rnd() });
  }
  const drawScreen = (s, t) => { const c = s.tex._cv.getContext('2d'); c.fillStyle = '#0e0b26'; c.fillRect(0, 0, 128, 96);
    const col = `hsl(${250 + s.hue * 80},90%,72%)`; c.strokeStyle = col; c.fillStyle = col; c.lineWidth = 4; const p = t + s.ph;
    if (s.kind === 'wave') { c.beginPath(); for (let x = 0; x < 128; x += 4) c.lineTo(x, 48 + Math.sin(x * 0.12 + p * 3) * 20); c.stroke(); }
    else if (s.kind === 'star') { for (let k = 0; k < 6; k++) { c.globalAlpha = 0.4 + 0.6 * Math.abs(Math.sin(p * 2 + k)); c.beginPath(); c.arc(16 + k * 19, 30 + (k % 3) * 18, 4, 0, 7); c.fill(); } c.globalAlpha = 1; }
    else if (s.kind === 'bulb') { c.globalAlpha = 0.5 + 0.5 * Math.abs(Math.sin(p)); c.beginPath(); c.arc(64, 42, 20, 0, 7); c.fill(); c.globalAlpha = 1; c.fillRect(56, 62, 16, 14); }
    else if (s.kind === 'heart') { const k = 1 + 0.15 * Math.max(0, Math.sin(p * 4)); c.save(); c.translate(64, 50); c.scale(k, k); c.beginPath(); c.moveTo(0, 18); c.bezierCurveTo(-30, 0, -18, -24, 0, -10); c.bezierCurveTo(18, -24, 30, 0, 0, 18); c.fill(); c.restore(); }
    else if (s.kind === 'eye') { c.beginPath(); c.ellipse(64, 48, 34, 16 * Math.abs(Math.cos(p * 0.7)) + 2, 0, 0, 7); c.stroke(); c.beginPath(); c.arc(64 + Math.sin(p) * 10, 48, 7, 0, 7); c.fill(); }
    else if (s.kind === 'ripple') { for (let k = 0; k < 3; k++) { c.globalAlpha = 1 - ((p * 0.5 + k / 3) % 1); c.beginPath(); c.arc(64, 48, ((p * 0.5 + k / 3) % 1) * 40, 0, 7); c.stroke(); } c.globalAlpha = 1; }
    else if (s.kind === 'bars') { for (let k = 0; k < 7; k++) { const hh = 10 + 30 * Math.abs(Math.sin(p * 2 + k * 0.8)); c.fillRect(10 + k * 16, 80 - hh, 10, hh); } }
    else { for (let k = 0; k < 12; k++) { c.beginPath(); c.arc(10 + (k * 37 + p * 20) % 110, 15 + (k * 23) % 70, 3, 0, 7); c.fill(); } }
    s.tex.needsUpdate = true; };
  // 반달 조종 책상(모니터 벽 앞) + 버튼·레버
  const desk = add(new THREE.Mesh(new THREE.CylinderGeometry(R - 0.9, R - 0.9, 0.7, 64, 1, false, Math.PI - 0.9, 1.8), clay('#4a3f8a', { roughness: 0.45 })), 'desk'); desk.position.y = 0.35;
  const deskIn = add(new THREE.Mesh(new THREE.CylinderGeometry(R - 1.55, R - 1.55, 0.72, 64, 1, false, Math.PI - 0.9, 1.8), clay('#4a3f8a')), null); deskIn.position.y = 0.35; deskIn.visible = false;
  const btnCols = ['#ff7a9a', '#7affc8', '#ffd86a', '#7ab8ff', '#c79aff'], buttons = [];
  for (let k = 0; k < 26; k++) { const a = -0.82 + k * 0.064, [x, , z] = onWallPos(R - 1.2 - (k % 2) * 0.18, a, 0.72);
    const m = new THREE.MeshStandardMaterial({ color: btnCols[k % 5], emissive: btnCols[k % 5], emissiveIntensity: 0.6 });
    const b = add(new THREE.Mesh(new THREE.CylinderGeometry(0.035, 0.035, 0.03, 12), m), null); b.position.set(x, 0.715, z); buttons.push({ m, ph: rnd() * 6 }); }
  // 뉴런 전선(천장 쪽): 굽은 관들을 따라 빛 방울이 달림
  const cableMat = clay('#6a5ad0', { roughness: 0.4 }), pulseMat = glow('#f0e8ff', '#c8a8ff', 2.0), cables = [];
  for (let k = 0; k < 9; k++) { const a0 = -1.2 + k * 0.3, p0 = new THREE.Vector3(...onWallPos(R - 0.2, a0, 2.8)), p3 = new THREE.Vector3(...onWallPos(R - 0.3, a0 + (rnd() - 0.5) * 2.5, 2.6 + rnd() * 0.4));
    const mid = new THREE.Vector3(rnd() * 2 - 1, 3.2 + rnd() * 0.6, rnd() * 2 - 1.2);
    const curve = new THREE.CatmullRomCurve3([p0, p0.clone().lerp(mid, 0.5).setY(3.0), mid, mid.clone().lerp(p3, 0.5).setY(3.0), p3]);
    g.add(new THREE.Mesh(new THREE.TubeGeometry(curve, 80, 0.03, 8), cableMat));
    const node = new THREE.Mesh(new THREE.SphereGeometry(0.09, 16, 12), glow('#d8c8ff', '#9a7aff', 1.0)); node.position.copy(mid); g.add(node);
    const pul = new THREE.Mesh(new THREE.SphereGeometry(0.05, 10, 8), pulseMat); g.add(pul); cables.push({ curve, pul, ph: rnd() }); }
  // 화이트보드(오른쪽 앞, 이젤) — 낙서: 별·전구·화살표·하트
  const board = new THREE.Group(); board.position.set(1.55, 0, 0.35); board.rotation.y = -0.75; g.add(board);
  const boardTex = canvasTex(800, 520, (c, w, h) => { c.fillStyle = '#fbfbff'; c.fillRect(0, 0, w, h); c.lineCap = 'round'; c.lineWidth = 7;
    c.strokeStyle = '#5a4ad0'; c.beginPath(); for (let k = 0; k < 5; k++) { const a = -Math.PI / 2 + k * 4 * Math.PI / 5; c.lineTo(140 + 60 * Math.cos(a), 150 + 60 * Math.sin(a)); } c.closePath(); c.stroke();
    c.strokeStyle = '#e8505b'; c.beginPath(); c.moveTo(400, 210); c.bezierCurveTo(330, 160, 360, 90, 400, 125); c.bezierCurveTo(440, 90, 470, 160, 400, 210); c.stroke();
    c.strokeStyle = '#2b2d5b'; c.beginPath(); c.arc(640, 140, 50, 0, 7); c.stroke(); c.strokeRect(622, 190, 36, 30);
    c.beginPath(); c.moveTo(210, 150); c.lineTo(320, 150); c.moveTo(300, 135); c.lineTo(320, 150); c.lineTo(300, 165); c.stroke();
    c.beginPath(); c.moveTo(480, 150); c.lineTo(580, 150); c.moveTo(560, 135); c.lineTo(580, 150); c.lineTo(560, 165); c.stroke();
    c.strokeStyle = '#3CC7B4'; c.beginPath(); for (let x = 80; x < 720; x += 8) c.lineTo(x, 380 + Math.sin(x * 0.04) * 40); c.stroke(); });
  const boardMesh = add(new THREE.Mesh(new RoundedBoxGeometry(1.2, 0.8, 0.04, 2, 0.015), [clay('#ddd'), clay('#ddd'), clay('#ddd'), clay('#ddd'), mat('#ffffff', { map: boardTex, roughness: 0.3 }), clay('#ddd')]), 'board', board); boardMesh.position.y = 1.15;
  for (const sx of [-0.5, 0.5]) { const leg = add(new THREE.Mesh(new THREE.CylinderGeometry(0.025, 0.025, 1.6, 8), brass()), 'board', board); leg.position.set(sx, 0.78, -0.08); leg.rotation.x = -0.12; }
  // 간이침대(왼쪽 앞)
  const cot = new THREE.Group(); cot.position.set(-1.65, 0, 0.55); cot.rotation.y = 0.55; g.add(cot);
  add(new THREE.Mesh(new RoundedBoxGeometry(1.25, 0.14, 0.62, 4, 0.06), clay('#b8a8ff', { roughness: 0.6 })), 'cot', cot).position.y = 0.38;
  add(new THREE.Mesh(new RoundedBoxGeometry(0.34, 0.1, 0.44, 4, 0.05), clay('#fff6e8', { roughness: 0.7 })), 'cot', cot).position.set(-0.42, 0.5, 0);
  for (const [x, z] of [[-0.55, -0.25], [0.55, -0.25], [-0.55, 0.25], [0.55, 0.25]]) add(new THREE.Mesh(new THREE.CylinderGeometry(0.025, 0.025, 0.32, 8), brass()), 'cot', cot).position.set(x, 0.16, z);

  const W = makeWorld({ sky: ['#05051a', '#1a1450', '#8a7aff', '#3a2a9a', '#08061e'], tube: '#d8d0ff', cell: '#e8e0ff', cellE: '#9a7aff', tower: '#18143a', win: '#c8b8ff', motes: '#e8e0ff', seed: 83, cellShape: 'spark' });
  g.add(W.world);
  const stars = new THREE.InstancedMesh(new THREE.SphereGeometry(0.08, 6, 4), new THREE.MeshBasicMaterial({ color: '#ffffff', fog: false }), 300); g.add(stars);
  { const M = new THREE.Matrix4(), r2 = rng(9); for (let k = 0; k < 300; k++) { const th = r2() * Math.PI * 2, ph = 0.15 + r2() * 1.2; M.makeTranslation(50 * Math.cos(th) * Math.cos(ph), 50 * Math.sin(ph) - 4, 50 * Math.sin(th) * Math.cos(ph)); stars.setMatrixAt(k, M); } }
  const setTime = t => {
    W.setTime(t);
    if (Math.round(t * 24) % 2 === 0) screens.forEach(s => drawScreen(s, t));
    buttons.forEach(b => { b.m.emissiveIntensity = 0.3 + 0.7 * (Math.sin(t * 3 + b.ph) > 0.6 ? 1 : 0); });
    cables.forEach(c => { c.pul.position.copy(c.curve.getPointAt((t * 0.4 + c.ph) % 1)); });
  };
  setTime(0);
  // 꿈 그림(C7·C11d): 조는 뇌의 꿈이 보드에 번져 나옴 — DREAM 글자 → 해 → 바다 → 모래 → 야자수 → 파라솔. p: 0(빈 보드)~1(완성)
  const drawDream = (p) => { const c = boardTex._cv.getContext('2d'), w = 800, h = 520; c.globalAlpha = 1; c.fillStyle = '#fbfbff'; c.fillRect(0, 0, w, h);
    const seg = (i, n) => Math.max(0, Math.min(1, (p * n - i)));        // i번째 요소의 진행(0~1)
    const N = 10; c.lineCap = 'round'; c.lineJoin = 'round';
    c.font = 'bold 150px "Noto Sans CJK KR", sans-serif'; c.textBaseline = 'middle';
    'DREAM'.split('').forEach((ch, i) => { const a = seg(i, N); if (a <= 0) return; c.globalAlpha = a; c.fillStyle = '#5a4ad0'; c.fillText(ch, 95 + i * 118 + (ch === 'M' ? -10 : 0), 118 + 7 * Math.sin(i * 1.7)); });
    let a = seg(5, N); if (a > 0) { c.globalAlpha = a; c.fillStyle = '#ffcf3a'; c.beginPath(); c.arc(680, 245, 46, 0, 7); c.fill(); c.strokeStyle = '#ffb020'; c.lineWidth = 7;
      for (let k = 0; k < 8; k++) { const t = k / 8 * 6.283; c.beginPath(); c.moveTo(680 + 58 * Math.cos(t), 245 + 58 * Math.sin(t)); c.lineTo(680 + 76 * Math.cos(t), 245 + 76 * Math.sin(t)); c.stroke(); } }
    a = seg(6, N); if (a > 0) { c.globalAlpha = a; c.fillStyle = '#7fd6ee'; c.fillRect(30, 330, 740, 70); c.strokeStyle = '#2c8fd0'; c.lineWidth = 7;
      for (const yy of [330, 362, 392]) { c.beginPath(); for (let x = 30; x <= 770; x += 6) c.lineTo(x, yy + 8 * Math.sin(x * 0.05 + yy)); c.stroke(); } }
    a = seg(7, N); if (a > 0) { c.globalAlpha = a; c.fillStyle = '#f5dca8'; c.beginPath(); c.moveTo(30, 400); c.quadraticCurveTo(400, 380, 770, 405); c.lineTo(770, 480); c.lineTo(30, 480); c.closePath(); c.fill(); }
    a = seg(8, N); if (a > 0) { c.globalAlpha = a; c.strokeStyle = '#8a5a2e'; c.lineWidth = 14; c.beginPath(); c.moveTo(150, 440); c.quadraticCurveTo(130, 330, 175, 235); c.stroke();
      c.strokeStyle = '#2fae6a'; c.lineWidth = 12; for (const [dx, dy] of [[-80, 20], [-60, -35], [10, -55], [70, -25], [85, 25]]) { c.beginPath(); c.moveTo(175, 235); c.quadraticCurveTo(175 + dx * 0.5, 235 + dy - 25, 175 + dx, 235 + dy); c.stroke(); } }
    a = seg(9, N); if (a > 0) { c.globalAlpha = a; c.strokeStyle = '#6a4a3a'; c.lineWidth = 7; c.beginPath(); c.moveTo(530, 450); c.lineTo(545, 315); c.stroke();
      for (let k = 0; k < 4; k++) { c.fillStyle = k % 2 ? '#ffffff' : '#e8505b'; c.beginPath(); c.moveTo(545, 300); c.arc(545, 318, 95, Math.PI + k * Math.PI / 4, Math.PI + (k + 1) * Math.PI / 4); c.closePath(); c.fill(); } }
    c.globalAlpha = 1; boardTex.needsUpdate = true; };
  let dreamP = -1; const setBoard = (p) => { const q = Math.round(p * 120) / 120; if (q === dreamP) return; dreamP = q; drawDream(q); };
  // 꿈 방울: 머리 위로 떠오르는 비눗방울 셋, 마지막 큰 방울엔 바다 그림
  const dream = new THREE.Group(); dream.visible = false; g.add(dream);
  const bubTex = canvasTex(256, 256, (c, w, h) => { c.clearRect(0, 0, w, h); c.save(); c.beginPath(); c.arc(128, 128, 112, 0, 7); c.clip();
    const gr = c.createLinearGradient(0, 30, 0, 230); gr.addColorStop(0, '#8fd8f8'); gr.addColorStop(0.55, '#e8fbff'); gr.addColorStop(0.56, '#3cb8d8'); gr.addColorStop(0.75, '#7fd6ee'); gr.addColorStop(0.76, '#f5dca8'); gr.addColorStop(1, '#f5dca8');
    c.fillStyle = gr; c.fillRect(0, 0, w, h); c.fillStyle = '#ffd23a'; c.beginPath(); c.arc(170, 85, 26, 0, 7); c.fill(); c.restore();
    c.strokeStyle = 'rgba(255,255,255,0.95)'; c.lineWidth = 10; c.beginPath(); c.arc(128, 128, 112, 0, 7); c.stroke(); c.fillStyle = 'rgba(255,255,255,0.85)'; c.beginPath(); c.ellipse(85, 75, 22, 12, -0.6, 0, 7); c.fill(); });
  const ringTex = canvasTex(128, 128, (c, w, h) => { c.clearRect(0, 0, w, h); const gr = c.createRadialGradient(64, 64, 30, 64, 64, 60); gr.addColorStop(0, 'rgba(255,255,255,0.08)'); gr.addColorStop(0.8, 'rgba(220,240,255,0.5)'); gr.addColorStop(1, 'rgba(255,255,255,0)');
    c.fillStyle = gr; c.beginPath(); c.arc(64, 64, 60, 0, 7); c.fill(); c.fillStyle = 'rgba(255,255,255,0.9)'; c.beginPath(); c.ellipse(46, 42, 10, 6, -0.6, 0, 7); c.fill(); });
  const bubs = [0, 1, 2].map(k => { const sp = new THREE.Sprite(new THREE.SpriteMaterial({ map: k < 2 ? ringTex : bubTex, transparent: true, depthWrite: false, fog: false })); dream.add(sp); return sp; });
  const setDream = (t, head, on = 1) => { dream.visible = on > 0.01; if (!dream.visible) return;
    bubs.forEach((b, k) => { const sz = [0.08, 0.13, 0.5][k], off = [[0.15, 0.1], [0.27, 0.28], [0.42, 0.62]][k], bob = 0.02 * Math.sin(t * 2 + k);
      b.position.set(head.x - off[0] * 1.1, head.y + off[1] + bob, head.z + off[0] * 0.2); b.scale.setScalar(sz * (1 + 0.04 * Math.sin(t * 3 + k))); b.material.opacity = on * (k < 2 ? 0.9 : 0.95); }); };
  drawDream(0); boardTex.needsUpdate = true;
  let screensOn = 1; const setScreens = v => { screensOn = v; };
  return { group: g, SOLID, setTime, atmo: { fog: '#2a2270', near: 7, far: 55 }, board, cot, setBoard, setDream, setScreens };
}
