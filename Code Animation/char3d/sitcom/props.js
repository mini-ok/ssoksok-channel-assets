// 시트콤 파일럿(담석 편) 소품: 기존 세트에 덧붙인다. 모든 단단한 소품은 SOLID에 넣어 충돌 검사를 받는다.
import * as THREE from 'three';
import { RoundedBoxGeometry } from 'three/addons/geometries/RoundedBoxGeometry.js';
import { canvasTex, mat, brass, glow } from '../sets/common.js';
import { clay } from '../chars3d.js';

const INK = '#26304F', FONT = '"Jua", "Noto Sans CJK KR", sans-serif';
const clamp = (v, a = 0, b = 1) => Math.max(a, Math.min(b, v));
function addTo(S, m, name, parent) { m.castShadow = m.receiveShadow = true; (parent || S.group).add(m); if (name) { m.name = name; S.SOLID.push(m); } return m; }
function label(text, w, h, { bg = '#fff6dc', fg = INK, size = 0.62, border = '#b07a2a' } = {}) {
  return canvasTex(w, h, c => { c.fillStyle = border; c.fillRect(0, 0, w, h); c.fillStyle = bg; c.fillRect(8, 8, w - 16, h - 16);
    c.fillStyle = fg; c.font = `${Math.round(h * size)}px ${FONT}`; c.textAlign = 'center'; c.textBaseline = 'middle';
    const lines = text.split('\n'); lines.forEach((l, i) => c.fillText(l, w / 2, h / 2 + (i - (lines.length - 1) / 2) * h * size * 1.05)); });
}

// ───────────── 주인님 CCTV(2D 그림) ─────────────
// mode: eat | clutch | fidget | rewind | hospital | diagram | shoulder | ambulance | gauge | logo
function drawOwner(c, x, y, s, { pose = 'sit', hand = 0, sweat = 0, face = 'happy', t = 0 } = {}) {
  c.save(); c.translate(x, y); c.scale(s, s); c.lineWidth = 5; c.strokeStyle = INK; c.lineJoin = c.lineCap = 'round';
  const bodyY = pose === 'stand' ? -40 : 0;
  c.fillStyle = '#7a9bd6'; c.beginPath(); c.ellipse(0, 40 + bodyY, 46, 56, 0, 0, 7); c.fill(); c.stroke();          // 몸(파란 티)
  if (pose === 'stand') { c.fillStyle = '#4a5a8a'; c.fillRect(-30, 86, 24, 50); c.fillRect(6, 86, 24, 50); c.strokeRect(-30, 86, 24, 50); c.strokeRect(6, 86, 24, 50); }
  c.fillStyle = '#ffd9bf'; c.beginPath(); c.arc(0, -42 + bodyY, 40, 0, 7); c.fill(); c.stroke();                    // 머리
  c.fillStyle = '#3a2a22'; c.beginPath(); c.arc(0, -52 + bodyY, 40, Math.PI * 1.05, Math.PI * 1.95); c.fill();       // 머리카락
  c.fillStyle = INK; const ey = -42 + bodyY;
  if (face === 'pain') { for (const sx of [-1, 1]) { c.beginPath(); c.moveTo(sx * 22, ey - 6); c.lineTo(sx * 10, ey); c.lineTo(sx * 22, ey + 6); c.stroke(); }
    c.beginPath(); c.moveTo(-12, ey + 22); c.quadraticCurveTo(0, ey + 14, 12, ey + 22); c.stroke(); }
  else { for (const sx of [-1, 1]) { c.beginPath(); c.arc(sx * 15, ey, 5, 0, 7); c.fill(); }
    c.beginPath(); c.arc(0, ey + 14, 10, 0.2, Math.PI - 0.2); c.stroke(); }
  // 팔: hand 0=무릎, 1=오른쪽 윗배(화면 왼쪽 = 인물의 오른쪽)
  c.fillStyle = '#ffd9bf';
  const hx = -18 - 10 * hand, hy = 20 + bodyY - 6 * hand;
  c.beginPath(); c.moveTo(-40, 10 + bodyY); c.quadraticCurveTo(-58, 40 + bodyY - 30 * hand, hx, hy + 30 * (1 - hand)); c.stroke();
  c.beginPath(); c.arc(hx, hy + 30 * (1 - hand), 11, 0, 7); c.fill(); c.stroke();
  c.beginPath(); c.moveTo(40, 10 + bodyY); c.quadraticCurveTo(58, 50 + bodyY, 30, 70 + bodyY); c.stroke();
  if (sweat > 0) { c.fillStyle = '#8ED8F8'; for (const [dx, dy] of [[44, -70], [-48, -58]]) { const yy = dy + bodyY + ((t * 40) % 20) * sweat; c.beginPath(); c.moveTo(dx, yy - 12); c.quadraticCurveTo(dx + 9, yy + 2, dx, yy + 8); c.quadraticCurveTo(dx - 9, yy + 2, dx, yy - 12); c.fill(); c.stroke(); } }
  if (hand > 0.5) { c.strokeStyle = '#e8505b'; c.lineWidth = 4; for (let k = 0; k < 3; k++) { c.beginPath(); c.arc(-32, 18 + bodyY, 18 + k * 9 + (t * 30) % 9, 2.2, 4.0); c.stroke(); } }
  c.restore();
}
function livingRoom(c, w, h) {
  c.fillStyle = '#f3e3c8'; c.fillRect(0, 0, w, h); c.fillStyle = '#d9b98a'; c.fillRect(0, h * 0.72, w, h * 0.28);
  c.fillStyle = '#c9e4f6'; c.fillRect(w * 0.62, h * 0.12, w * 0.26, h * 0.3); c.strokeStyle = '#8a6a4a'; c.lineWidth = 6; c.strokeRect(w * 0.62, h * 0.12, w * 0.26, h * 0.3);
  c.fillStyle = '#ffe9a0'; c.beginPath(); c.arc(w * 0.82, h * 0.2, 14, 0, 7); c.fill();                                // 창밖 달
  c.fillStyle = '#e07a6a'; c.beginPath(); c.roundRect(w * 0.18, h * 0.46, w * 0.42, h * 0.3, 24); c.fill();              // 소파
  c.fillStyle = '#c9614f'; c.beginPath(); c.roundRect(w * 0.14, h * 0.4, w * 0.08, h * 0.38, 14); c.fill(); c.beginPath(); c.roundRect(w * 0.56, h * 0.4, w * 0.08, h * 0.38, 14); c.fill();
}
function food(c, w, h, left = 1) {
  c.save(); c.translate(w * 0.36, h * 0.83);
  c.fillStyle = '#fff'; c.fillRect(-140, -6, 280, 12);                                                                   // 상
  if (left > 0) { c.fillStyle = '#e0a040'; c.beginPath(); c.roundRect(-120, -60, 90, 54, 8); c.fill(); c.strokeStyle = INK; c.lineWidth = 4; c.stroke();   // 치킨 상자
    c.fillStyle = '#b5651d'; for (let k = 0; k < 3 * left; k++) { c.beginPath(); c.ellipse(-100 + k * 25, -64, 14, 10, 0.4, 0, 7); c.fill(); }
    c.fillStyle = '#fff5dc'; c.beginPath(); c.ellipse(60, -14, 50, 14, 0, 0, 7); c.fill(); c.stroke();                 // 크림 파스타
    c.strokeStyle = '#f0d27a'; c.lineWidth = 5; for (let k = 0; k < 4 * left; k++) { c.beginPath(); c.arc(45 + k * 10, -22, 9, 0, Math.PI); c.stroke(); } }
  c.restore();
}
function recHud(c, w, h, stamp, t, { rewind = false } = {}) {
  c.fillStyle = 'rgba(0,0,0,0.25)'; for (let y = 0; y < h; y += 4) c.fillRect(0, y, w, 1);                                // 주사선
  c.font = `30px ${FONT}`; c.textBaseline = 'top'; c.fillStyle = '#fff'; c.textAlign = 'left';
  if (rewind) { c.fillText('◀◀ 되감기', 20, 16); } else { if ((t * 2 | 0) % 2 === 0) { c.fillStyle = '#ff3a3a'; c.beginPath(); c.arc(32, 32, 10, 0, 7); c.fill(); } c.fillStyle = '#fff'; c.fillText('REC', 48, 16); }
  c.textAlign = 'right'; c.fillText(stamp, w - 20, 16); c.textAlign = 'left'; c.fillText('CAM 1 · 거실', 20, h - 46);
}
export function drawMonitor(c, w, h, mode, t, o = {}) {
  c.save();
  if (['eat', 'clutch', 'fidget', 'rewind', 'hospital'].includes(mode)) {
    if (mode === 'hospital') {
      c.fillStyle = '#dff1ff'; c.fillRect(0, 0, w, h); c.fillStyle = '#c8e8c0'; c.fillRect(0, h * 0.75, w, h * 0.25);
      c.fillStyle = '#ffffff'; c.fillRect(w * 0.55, h * 0.22, w * 0.34, h * 0.53); c.strokeStyle = INK; c.lineWidth = 5; c.strokeRect(w * 0.55, h * 0.22, w * 0.34, h * 0.53);
      c.fillStyle = '#e8505b'; c.fillRect(w * 0.705, h * 0.28, w * 0.03, h * 0.14); c.fillRect(w * 0.675, h * 0.33, w * 0.09, h * 0.045);
      c.fillStyle = INK; c.font = `34px ${FONT}`; c.textAlign = 'center'; c.fillText('병원', w * 0.72, h * 0.56);
      drawOwner(c, w * (0.18 + 0.2 * clamp(t / 2.5)), h * 0.5, 0.75, { pose: 'stand', hand: 0.6, face: 'pain', t });
      recHud(c, w, h, o.stamp || 'AM 2:10', t);
    } else {
      livingRoom(c, w, h); food(c, w, h, mode === 'eat' ? 1 - clamp(t / 3) * 0.6 : 0.3);
      let pose = 'sit', hand = 0, face = 'happy', sweat = 0;
      if (mode === 'clutch') { hand = clamp((t - (o.clutchAt ?? 0.6)) / 0.4); face = hand > 0.3 ? 'pain' : 'happy'; sweat = hand; }
      if (mode === 'fidget') { pose = (t * 0.9 | 0) % 2 ? 'stand' : 'sit'; hand = 1; face = 'pain'; sweat = 1; }
      if (mode === 'rewind') { hand = 0; face = 'happy'; }
      drawOwner(c, w * 0.39, h * 0.47, 0.9, { pose, hand, face, sweat, t });
      if (mode === 'eat') { c.fillStyle = '#b5651d'; const k = Math.sin(t * 6); c.beginPath(); c.ellipse(w * 0.33, h * 0.4 + 10 * k, 14, 10, 0.4, 0, 7); c.fill(); }
      if (mode === 'rewind') { c.globalCompositeOperation = 'saturation'; c.fillStyle = 'hsl(0,0%,50%)'; c.fillRect(0, 0, w, h); c.globalCompositeOperation = 'source-over';
        c.fillStyle = 'rgba(255,255,255,0.12)'; c.fillRect(0, ((t * 260) % (h + 80)) - 40, w, 40); }
      recHud(c, w, h, o.stamp || 'PM 11:40', t, { rewind: mode === 'rewind' });
    }
  } else if (mode === 'diagram') {   // 담낭 단면: 담즙 탱크 → 출구 관에 돌이 낌
    c.fillStyle = '#10203a'; c.fillRect(0, 0, w, h); c.strokeStyle = '#9fd8ff'; c.lineWidth = 2; for (let x = 0; x < w; x += 40) { c.globalAlpha = 0.15; c.beginPath(); c.moveTo(x, 0); c.lineTo(x, h); c.stroke(); } for (let y = 0; y < h; y += 40) { c.beginPath(); c.moveTo(0, y); c.lineTo(w, y); c.stroke(); } c.globalAlpha = 1;
    const sq = 1 + 0.06 * Math.sin(t * 5);
    c.save(); c.translate(w * 0.32, h * 0.52); c.scale(1 / sq, sq); c.fillStyle = '#9ad86a'; c.strokeStyle = '#ffffff'; c.lineWidth = 6;
    c.beginPath(); c.ellipse(0, 0, 110, 70, -0.3, 0, 7); c.fill(); c.stroke(); c.restore();
    c.fillStyle = '#9ad86a'; c.strokeStyle = '#fff'; c.lineWidth = 6; c.beginPath(); c.moveTo(w * 0.47, h * 0.42); c.lineTo(w * 0.86, h * 0.42); c.lineTo(w * 0.86, h * 0.5); c.lineTo(w * 0.47, h * 0.5); c.fill(); c.stroke();
    c.fillStyle = '#e8c070'; c.strokeStyle = INK; c.lineWidth = 4; c.beginPath(); c.arc(w * 0.555, h * 0.46, 22, 0, 7); c.fill(); c.stroke();
    if ((t * 3 | 0) % 2 === 0) { c.strokeStyle = '#ff4a4a'; c.lineWidth = 7; c.beginPath(); c.arc(w * 0.555, h * 0.46, 40, 0, 7); c.stroke(); }
    c.fillStyle = '#fff'; c.font = `34px ${FONT}`; c.textAlign = 'center'; c.fillText('담낭(담즙 탱크)', w * 0.3, h * 0.22); c.fillText('담석이 출구를 막음', w * 0.7, h * 0.72);
  } else if (mode === 'shoulder') {   // 뒷모습 실루엣, 오른쪽 어깨뼈(화면 오른쪽) 깜빡
    c.fillStyle = '#1a1440'; c.fillRect(0, 0, w, h); c.fillStyle = '#5a50a0'; c.beginPath(); c.arc(w / 2, h * 0.28, 50, 0, 7); c.fill();
    c.beginPath(); c.roundRect(w / 2 - 120, h * 0.42, 240, h * 0.6, 60); c.fill();
    c.fillStyle = (t * 4 | 0) % 2 ? '#ff4a4a' : '#ffb0b0'; c.beginPath(); c.ellipse(w / 2 + 60, h * 0.58, 34, 46, 0.2, 0, 7); c.fill();
    c.fillStyle = '#fff'; c.font = `36px ${FONT}`; c.textAlign = 'center'; c.fillText('오른쪽 어깨뼈 신고!', w / 2, h * 0.14);
  } else if (mode === 'ambulance') {
    c.fillStyle = (t * 3 | 0) % 2 ? '#e8c8c8' : '#d8d8e0'; c.fillRect(0, 0, w, h);
    const x = w * 0.5 + 18 * Math.sin(t * 9); c.fillStyle = '#ffffff'; c.strokeStyle = INK; c.lineWidth = 7;
    c.beginPath(); c.roundRect(x - 170, h * 0.38, 300, 130, 18); c.fill(); c.stroke(); c.beginPath(); c.roundRect(x + 120, h * 0.48, 80, 90, 14); c.fill(); c.stroke();
    c.fillStyle = '#e8505b'; c.fillRect(x - 60, h * 0.45, 26, 80); c.fillRect(x - 87, h * 0.45 + 27, 80, 26);
    c.fillStyle = (t * 6 | 0) % 2 ? '#ff2a2a' : '#4a7aff'; c.fillRect(x - 40, h * 0.32, 60, 26);
    c.fillStyle = INK; for (const dx of [-110, 110]) { c.beginPath(); c.arc(x + dx, h * 0.38 + 140, 30, 0, 7); c.fill(); }
    c.font = `64px ${FONT}`; c.textAlign = 'center'; c.fillStyle = '#e8505b'; c.fillText('119', w / 2, h * 0.2);
  } else if (mode === 'gauge') {   // 멎었다 다시 오는 통증: 바늘이 초록 → 다시 빨강
    c.fillStyle = '#2a1a10'; c.fillRect(0, 0, w, h); const cx = w / 2, cy = h * 0.68, r = 150;
    const seg = [['#5ad87a', Math.PI, Math.PI * 1.45], ['#ffd24a', Math.PI * 1.45, Math.PI * 1.7], ['#ff4a4a', Math.PI * 1.7, Math.PI * 2]];
    for (const [col, a0, a1] of seg) { c.strokeStyle = col; c.lineWidth = 34; c.beginPath(); c.arc(cx, cy, r, a0, a1); c.stroke(); }
    const v = t < 1.6 ? 0.2 : clamp(0.2 + (t - 1.6) * 0.9, 0.2, 0.92);
    const a = Math.PI + Math.PI * v; c.strokeStyle = '#fff'; c.lineWidth = 9; c.beginPath(); c.moveTo(cx, cy); c.lineTo(cx + Math.cos(a) * (r - 20), cy + Math.sin(a) * (r - 20)); c.stroke();
    c.fillStyle = '#fff'; c.beginPath(); c.arc(cx, cy, 14, 0, 7); c.fill(); c.font = `38px ${FONT}`; c.textAlign = 'center';
    c.fillText(t < 1.6 ? '멎음…' : '또 올 수 있어요', cx, h * 0.16);
  } else {   // logo / idle
    c.fillStyle = '#16123a'; c.fillRect(0, 0, w, h); c.fillStyle = '#c8b8ff'; c.font = `46px ${FONT}`; c.textAlign = 'center'; c.textBaseline = 'middle';
    c.fillText('몸속 주식회사 관제실', w / 2, h / 2);
  }
  c.restore();
}

// ───────────── 뇌 관제실 ─────────────
export function brainProps(S) {
  const g = new THREE.Group(); S.group.add(g); const P = {};
  // 큰 CCTV 모니터(모니터 벽 가운데 앞)
  const MON = { x: 0, y: 1.7, z: -2.95, w: 2.3, h: 1.29 };
  const frame = addTo(S, new THREE.Mesh(new RoundedBoxGeometry(MON.w + 0.12, MON.h + 0.12, 0.1, 3, 0.03), clay('#2a2450', { roughness: 0.4 })), 'bigMonitor', g); frame.position.set(MON.x, MON.y, MON.z);
  const monTex = canvasTex(640, 360, c => drawMonitor(c, 640, 360, 'logo', 0));
  const screen = new THREE.Mesh(new THREE.PlaneGeometry(MON.w, MON.h), new THREE.MeshBasicMaterial({ map: monTex, toneMapped: false })); screen.position.set(MON.x, MON.y, MON.z + 0.052); g.add(screen);
  P.MON = MON; P.screen = screen;
  let lastKey = '';
  P.setMonitor = (mode, t, o = {}) => { const key = mode + '|' + Math.round(t * 12) + '|' + JSON.stringify(o); if (key === lastKey) return; lastKey = key;
    drawMonitor(monTex._cv.getContext('2d'), 640, 360, mode, t, o); monTex.needsUpdate = true; };
  // 빨간 경보등(모니터 위)
  const beaconBase = addTo(S, new THREE.Mesh(new THREE.CylinderGeometry(0.12, 0.14, 0.08, 24), brass()), 'beacon', g); beaconBase.position.set(0, MON.y + MON.h / 2 + 0.1, MON.z);
  const beaconMat = new THREE.MeshStandardMaterial({ color: '#ff4040', emissive: '#ff1010', emissiveIntensity: 0.2, transparent: true, opacity: 0.9 });
  const beacon = addTo(S, new THREE.Mesh(new THREE.SphereGeometry(0.11, 24, 16, 0, Math.PI * 2, 0, Math.PI / 2), beaconMat), 'beacon', g); beacon.position.set(0, MON.y + MON.h / 2 + 0.14, MON.z);
  const redLight = new THREE.PointLight('#ff2a2a', 0, 9, 1.4); redLight.position.set(0, 2.6, -2.2); g.add(redLight);
  P.setAlarm = (on, t) => { const p = on * (0.5 + 0.5 * Math.sin(t * 9)); beaconMat.emissiveIntensity = 0.2 + 3.5 * p; redLight.intensity = 9 * p; return p; };
  // 기송관 출구(왼쪽 앞) + 받침 쟁반 + 캡슐
  const TUBE = { x: -1.3, z: 0.25 };
  const pipe = addTo(S, new THREE.Mesh(new THREE.CylinderGeometry(0.09, 0.09, 1.7, 20, 1, true), brass({ side: THREE.DoubleSide })), 'tube', g); pipe.position.set(TUBE.x, 2.45, TUBE.z);
  const mouth = addTo(S, new THREE.Mesh(new THREE.CylinderGeometry(0.15, 0.09, 0.14, 24, 1, true), brass({ side: THREE.DoubleSide })), 'tube', g); mouth.position.set(TUBE.x, 1.55, TUBE.z);
  const stand = addTo(S, new THREE.Mesh(new THREE.CylinderGeometry(0.035, 0.05, 0.86, 12), brass()), 'tubeTray', g); stand.position.set(TUBE.x, 0.43, TUBE.z);
  const tray = addTo(S, new THREE.Mesh(new THREE.CylinderGeometry(0.22, 0.2, 0.05, 28), brass()), 'tubeTray', g); tray.position.set(TUBE.x, 0.885, TUBE.z);
  const capsule = new THREE.Mesh(new THREE.CapsuleGeometry(0.055, 0.14, 8, 16), new THREE.MeshPhysicalMaterial({ color: '#c8f0ff', roughness: 0.05, clearcoat: 1, transparent: true, opacity: 0.8 }));
  capsule.rotation.z = Math.PI / 2; g.add(capsule);
  const capPaper = new THREE.Mesh(new THREE.CylinderGeometry(0.035, 0.035, 0.13, 12), mat('#fff8e8')); capPaper.rotation.z = Math.PI / 2; capsule.add(capPaper); capPaper.rotation.set(0, 0, 0);
  P.TUBE = TUBE;
  // 캡슐: u<0 관 속(안 보임), 0..1 떨어짐, 1 이후 쟁반 위에서 통통
  P.setCapsule = (u, visible = true) => { capsule.visible = visible && u >= 0; const y0 = 1.55, y1 = 0.91 + 0.055;
    if (u < 1) capsule.position.set(TUBE.x, y0 - (y0 - y1) * u * u, TUBE.z);
    else { const d = u - 1; capsule.position.set(TUBE.x, y1 + 0.06 * Math.abs(Math.sin(d * 9)) * Math.exp(-d * 5), TUBE.z); } };
  P.setCapsule(-1);
  // 화이트보드 = 내기 현황판
  const boardMesh = S.board.children[0], boardTex = boardMesh.material[4].map;
  P.setBet = (st = {}) => { const c = boardTex._cv.getContext('2d'), w = 800, h = 520; c.fillStyle = '#fbfbff'; c.fillRect(0, 0, w, h);
    c.fillStyle = INK; c.font = `64px ${FONT}`; c.textAlign = 'center'; c.textBaseline = 'middle'; c.fillText(st.title || '내기 현황판', w / 2, 64);
    c.strokeStyle = '#5a4ad0'; c.lineWidth = 6; c.beginPath(); c.moveTo(w / 2, 120); c.lineTo(w / 2, 470); c.stroke();
    if (st.mode === 'table') {   // 구별표
      c.textAlign = 'left'; c.font = `46px ${FONT}`; const rows = st.rows || []; rows.forEach((r, i) => { if (i >= (st.n ?? 9)) return; c.fillStyle = r[1] || INK; c.fillText(r[0], 60, 160 + i * 84); });
      c.strokeStyle = '#fbfbff'; c.lineWidth = 12; c.beginPath(); c.moveTo(w / 2, 120); c.lineTo(w / 2, 470); c.stroke();
    } else if (st.mode === 'levers') {   // 레버 3개 그림 + 가위표
      ['가스', '화장실', '역류'].forEach((n, i) => { const x = 150 + i * 250; c.strokeStyle = INK; c.lineWidth = 8; c.beginPath(); c.moveTo(x, 360); c.lineTo(x + 40, 220); c.stroke(); c.fillStyle = '#e8505b'; c.beginPath(); c.arc(x + 40, 215, 24, 0, 7); c.fill();
        c.fillStyle = INK; c.font = `44px ${FONT}`; c.textAlign = 'center'; c.fillText(n, x + 20, 420);
        const k = clamp((st.x ?? 0) * 3 - i); if (k > 0) { c.strokeStyle = '#e8505b'; c.lineWidth = 12; c.beginPath(); c.moveTo(x - 50, 200); c.lineTo(x - 50 + 160 * k, 200 + 200 * k); c.stroke(); if (k > 0.5) { c.beginPath(); c.moveTo(x + 110, 200); c.lineTo(x + 110 - 160 * (k - 0.5) * 2, 200 + 200 * (k - 0.5) * 2); c.stroke(); } } });
      c.strokeStyle = '#fbfbff'; c.lineWidth = 12; c.beginPath(); c.moveTo(w / 2, 120); c.lineTo(w / 2, 180); c.stroke();
    } else {
      c.font = `54px ${FONT}`; c.fillStyle = '#3a8a5a'; c.fillText('참는다', w * 0.25, 170); c.fillStyle = '#d04050'; c.fillText('신고한다', w * 0.75, 170);
      c.font = `44px ${FONT}`; c.fillStyle = INK; const L = st.left || [], Rr = st.right || [];
      L.forEach((n, i) => c.fillText(n, w * 0.25, 260 + i * 66)); Rr.forEach((n, i) => c.fillText(n, w * 0.75, 260 + i * 66));
      if (st.win) { c.save(); c.translate(w * 0.75, 420); c.rotate(-0.15); c.strokeStyle = '#d04050'; c.lineWidth = 9; c.strokeRect(-110, -44, 220, 88); c.fillStyle = '#d04050'; c.font = `66px ${FONT}`; c.fillText('승!', 0, 2); c.restore(); }
      if (st.penalty) { c.fillStyle = '#fff3c0'; c.fillRect(30, 380, w - 60, 110); c.fillStyle = INK; c.font = `42px ${FONT}`; c.fillText('벌칙: 회식 뒷정리 한 달 — 장', w / 2, 435); }
    }
    boardTex.needsUpdate = true; };
  // 판정 서류(뇌가 손에 듦)
  P.paper = new THREE.Mesh(new THREE.PlaneGeometry(0.2, 0.27), new THREE.MeshStandardMaterial({ map: label('판정서\n─────\n담석 신호', 200, 270, { bg: '#fffdf4', border: '#e8dcc0', size: 0.18 }), side: THREE.DoubleSide }));
  P.paper.visible = false;
  return P;
}

// ───────────── 간 공장 ─────────────
export function liverProps(S) {
  const g = new THREE.Group(); S.group.add(g); const P = {};
  // 가운데 탱크(0, z=-2.75, r 0.75) 앞 명패
  const plate = addTo(S, new THREE.Mesh(new RoundedBoxGeometry(1.25, 0.4, 0.04, 2, 0.01), [brass(), brass(), brass(), brass(), new THREE.MeshStandardMaterial({ map: label('담즙 탱크 (담낭)', 750, 240, { size: 0.46 }) }), brass()]), 'plate', g);
  plate.position.set(0, 1.5, -2.75 + 0.8); plate.rotation.x = -0.05;
  // 탱크가 달아오름: 붉은 고리 + 빛
  const hotMat = new THREE.MeshStandardMaterial({ color: '#ff5a3a', emissive: '#ff2a10', emissiveIntensity: 0, transparent: true, opacity: 0 });
  const hot = new THREE.Mesh(new THREE.TorusGeometry(0.84, 0.05, 10, 48), hotMat); hot.rotation.x = Math.PI / 2; hot.position.set(0, 0.9, -2.75); g.add(hot);
  const hot2 = hot.clone(); hot2.position.y = 2.2; g.add(hot2);
  const hotLight = new THREE.PointLight('#ff3a1a', 0, 6, 1.5); hotLight.position.set(0, 1.4, -1.7); g.add(hotLight);
  P.setHot = (v, t, col = '#ff5a3a') => { const p = v * (0.75 + 0.25 * Math.sin(t * 7)); hotMat.color.set(col); hotMat.emissive.set(col); hotLight.color.set(col);
    hotMat.opacity = Math.min(1, v * 1.4); hotMat.emissiveIntensity = 2.5 * p; hotLight.intensity = 6 * p; hot.visible = hot2.visible = v > 0.01; };
  P.setSqueeze = v => { for (const h of [hot, hot2]) h.scale.set(1 - 0.12 * v, 1 - 0.12 * v, 1); };
  // 압력계(받침대 위, 탱크 오른쪽 앞)
  const GA = { x: 0.7, z: -1.55, y: 1.12 };
  const post = addTo(S, new THREE.Mesh(new THREE.CylinderGeometry(0.035, 0.06, GA.y - 0.12, 12), brass()), 'gauge', g); post.position.set(GA.x, (GA.y - 0.12) / 2, GA.z);
  const foot = addTo(S, new THREE.Mesh(new THREE.CylinderGeometry(0.14, 0.16, 0.04, 20), brass()), 'gauge', g); foot.position.set(GA.x, 0.02, GA.z);
  const dialG = new THREE.Group(); dialG.position.set(GA.x, GA.y, GA.z); dialG.rotation.y = -0.35; g.add(dialG);
  addTo(S, new THREE.Mesh(new THREE.CylinderGeometry(0.25, 0.25, 0.06, 32), brass()), 'gauge', dialG).rotation.x = Math.PI / 2;
  const faceTex = canvasTex(256, 256, c => { c.fillStyle = '#e9dcc0'; c.beginPath(); c.arc(128, 128, 124, 0, 7); c.fill();
    for (const [col, a0, a1] of [['#5ad87a', 0.75 * Math.PI, 1.35 * Math.PI], ['#ffd24a', 1.35 * Math.PI, 1.75 * Math.PI], ['#ff4a4a', 1.75 * Math.PI, 2.25 * Math.PI]]) { c.strokeStyle = col; c.lineWidth = 26; c.beginPath(); c.arc(128, 128, 92, a0, a1); c.stroke(); }
    c.fillStyle = INK; c.font = `30px ${FONT}`; c.textAlign = 'center'; c.fillText('압력', 128, 200); });
  const dface = new THREE.Mesh(new THREE.CircleGeometry(0.225, 32), new THREE.MeshStandardMaterial({ map: faceTex })); dface.position.z = 0.032; dialG.add(dface);
  const needle = new THREE.Mesh(new THREE.BoxGeometry(0.018, 0.18, 0.01), mat('#2B2D5B')); needle.geometry.translate(0, 0.075, 0); needle.position.z = 0.04; dialG.add(needle);
  P.GA = GA; P.dialG = dialG;
  P.setGauge = v => { needle.rotation.z = 0.75 * Math.PI - 1.5 * Math.PI * clamp(v); };
  // 출구 관(탱크 오른쪽 아래, 유리) + 밸브 손잡이 + 담석
  const PIPE = { y: 0.42, z: -2.2, x0: 0.55, x1: 1.75 };
  const glass = new THREE.MeshPhysicalMaterial({ color: '#fff4dc', roughness: 0.03, transparent: true, opacity: 0.3, side: THREE.DoubleSide, depthWrite: false });
  const tube = addTo(S, new THREE.Mesh(new THREE.CylinderGeometry(0.1, 0.1, PIPE.x1 - PIPE.x0, 24, 1, true), glass), 'outletPipe', g); tube.rotation.z = Math.PI / 2; tube.position.set((PIPE.x0 + PIPE.x1) / 2, PIPE.y, PIPE.z);
  for (const x of [PIPE.x0, 1.15, PIPE.x1]) { const ring = addTo(S, new THREE.Mesh(new THREE.TorusGeometry(0.105, 0.03, 8, 24), brass()), 'outletPipe', g); ring.rotation.y = Math.PI / 2; ring.position.set(x, PIPE.y, PIPE.z); }
  for (const x of [0.8, 1.5]) { const leg = addTo(S, new THREE.Mesh(new THREE.CylinderGeometry(0.025, 0.025, PIPE.y - 0.1, 8), brass()), 'outletPipe', g); leg.position.set(x, (PIPE.y - 0.1) / 2, PIPE.z); }
  const valve = new THREE.Group(); valve.position.set(1.15, PIPE.y + 0.2, PIPE.z); g.add(valve);
  addTo(S, new THREE.Mesh(new THREE.CylinderGeometry(0.02, 0.02, 0.1, 8), brass()), 'valve', g).position.set(1.15, PIPE.y + 0.14, PIPE.z);
  const wheel = addTo(S, new THREE.Mesh(new THREE.TorusGeometry(0.09, 0.018, 8, 24), clay('#d04050', { roughness: 0.4 })), 'valve', valve); wheel.rotation.x = Math.PI / 2;
  for (let k = 0; k < 2; k++) { const sp = addTo(S, new THREE.Mesh(new THREE.BoxGeometry(0.17, 0.014, 0.014), clay('#d04050')), 'valve', valve); sp.rotation.y = k * Math.PI / 2; }
  P.setValve = (rattle, t) => { valve.rotation.y = rattle * 0.25 * Math.sin(t * 38); valve.position.y = PIPE.y + 0.2 + rattle * 0.008 * Math.sin(t * 51); };
  const stone = new THREE.Mesh(new THREE.DodecahedronGeometry(0.075, 1), clay('#c9a25a', { roughness: 0.8 })); g.add(stone); stone.castShadow = true;
  // 담석: u 0(탱크 안 = 안 보임) → 1(관 좁은 곳에 끼임)
  P.setStone = (u, t = 0) => { stone.visible = u > 0.02; const x = PIPE.x0 + (1.15 - 0.09 - PIPE.x0) * clamp(u); stone.position.set(x, PIPE.y - 0.02, PIPE.z); stone.rotation.z = -x * 12; };
  P.setStone(0);
  P.PIPE = PIPE;
  // 회식 그릇 더미 + 개수대(오른쪽 앞, 4막)
  const dish = new THREE.Group(); dish.position.set(-0.55, 0, 1.25); dish.visible = false; g.add(dish); P.dish = dish;
  const tbl = addTo(S, new THREE.Mesh(new RoundedBoxGeometry(1.5, 0.08, 0.6, 2, 0.02), clay('#e9f7f0', { roughness: 0.4 })), 'dishTable', dish); tbl.position.y = 0.41;
  for (const [x, z] of [[-0.68, -0.25], [0.68, -0.25], [-0.68, 0.25], [0.68, 0.25]]) addTo(S, new THREE.Mesh(new THREE.CylinderGeometry(0.025, 0.025, 0.38, 8), brass()), 'dishTable', dish).position.set(x, 0.19, z);
  const plateMat = clay('#ffffff', { roughness: 0.25, clearcoat: 0.8 }), plateGeo = new THREE.CylinderGeometry(0.13, 0.1, 0.022, 28);
  const stacks = [[-0.5, 0.08, 9], [-0.2, 0.1, 12], [0.12, 0.08, 10], [0.45, 0.1, 7]];
  P.plates = [];
  stacks.forEach(([x, z, n], si) => { for (let k = 0; k < n; k++) { const pl = addTo(S, new THREE.Mesh(plateGeo, plateMat), 'plates', dish); pl.position.set(x + 0.008 * Math.sin(k * 2.1 + si), 0.462 + k * 0.024, z + 0.008 * Math.cos(k * 1.7)); P.plates.push(pl); } });
  P.washed = new THREE.Mesh(plateGeo, plateMat); P.washed.castShadow = true; P.washed.visible = false; g.add(P.washed);
  const bubbles = new THREE.InstancedMesh(new THREE.SphereGeometry(0.025, 8, 6), new THREE.MeshPhysicalMaterial({ color: '#ffffff', roughness: 0.05, transparent: true, opacity: 0.7 }), 30); dish.add(bubbles);
  { const M = new THREE.Matrix4(); for (let k = 0; k < 30; k++) { M.makeTranslation(0.62 + 0.1 * Math.sin(k * 2.3), 0.47 + 0.02 * (k % 4), 0.1 * Math.cos(k * 1.7)); bubbles.setMatrixAt(k, M); } }
  return P;
}

// ───────────── 장 연구소 ─────────────
export function gutProps(S) {
  const g = new THREE.Group(); S.group.add(g); const P = {};
  // 기름진 상자: 컨베이어 꾸러미 무늬를 치킨·크림 파스타로
  const tex = (kind) => canvasTex(256, 256, c => { c.fillStyle = kind ? '#fff1cf' : '#e8a24a'; c.fillRect(0, 0, 256, 256);
    c.fillStyle = 'rgba(255,255,210,0.9)'; for (let k = 0; k < 14; k++) { c.beginPath(); c.ellipse((k * 73) % 256, (k * 131) % 256, 10 + (k % 3) * 6, 7 + (k % 2) * 5, 0.5, 0, 7); c.fill(); }
    c.fillStyle = INK; c.font = `58px ${FONT}`; c.textAlign = 'center'; c.textBaseline = 'middle'; c.fillText(kind ? '크림' : '치킨', 128, 128); });
  const gm = [tex(0), tex(1)].map(t => clay('#ffffff', { map: t, roughness: 0.25, clearcoat: 0.9 }));
  P.greasy = on => S.parcels.forEach((o, k) => { if (!o.m.userData.m0) o.m.userData.m0 = o.m.material; o.m.material = on ? gm[k % 2] : o.m.userData.m0; });
  // 레버 판(고리 안쪽 오른쪽): 가스 배출 · 화장실 출구 · 역류
  const PANEL = { x: 1.2, z: -0.35, ry: -Math.PI / 2 + 0.75 };   // 앞면이 왼쪽(-x)을 봄
  const pan = new THREE.Group(); pan.position.set(PANEL.x, 0, PANEL.z); pan.rotation.y = PANEL.ry; g.add(pan); P.PANEL = PANEL; P.panel = pan;
  addTo(S, new THREE.Mesh(new RoundedBoxGeometry(0.95, 0.8, 0.32, 3, 0.04), clay('#3d6b5e', { roughness: 0.4 })), 'leverPanel', pan).position.set(0, 0.4, 0);
  const labels = ['가스 배출', '화장실 출구', '역류'], lev = [];
  labels.forEach((n, i) => { const x = -0.3 + i * 0.3;
    const lb = new THREE.Mesh(new THREE.PlaneGeometry(0.29, 0.13), new THREE.MeshStandardMaterial({ map: label(n, 290, 130, { size: 0.36 }) })); lb.position.set(x, 0.62, 0.162); pan.add(lb);
    const piv = new THREE.Group(); piv.position.set(x, 0.82, 0.04); pan.add(piv);
    addTo(S, new THREE.Mesh(new THREE.CylinderGeometry(0.018, 0.018, 0.3, 10), brass()), 'lever', piv).position.y = 0.15;
    addTo(S, new THREE.Mesh(new THREE.SphereGeometry(0.045, 16, 12), clay(['#ffd24a', '#7ab8ff', '#e8505b'][i])), 'lever', piv).position.y = 0.32;
    lev.push(piv); });
  P.setLever = (i, v) => { lev[i].rotation.x = -0.5 + 1.1 * v; };   // 0: 뒤로 젖힘(대기) 1: 앞으로 당김
  [0, 1, 2].forEach(i => P.setLever(i, 0));
  // 손잡이 공의 월드 위치(손 맞춤용)
  P.leverKnob = i => { pan.updateMatrixWorld(true); return lev[i].localToWorld(new THREE.Vector3(0, 0.32, 0)); };
  // 가스 배출 굴뚝 + 뿌웁 구름
  const chim = addTo(S, new THREE.Mesh(new THREE.CylinderGeometry(0.06, 0.08, 0.5, 16), brass()), 'leverPanel', pan); chim.position.set(0.38, 1.05, -0.08);
  const puffTex = canvasTex(256, 256, c => { c.clearRect(0, 0, 256, 256); c.fillStyle = 'rgba(200,240,190,0.95)'; for (const [x, y, r] of [[128, 140, 70], [80, 120, 50], [176, 118, 54], [120, 80, 46], [170, 170, 44]]) { c.beginPath(); c.arc(x, y, r, 0, 7); c.fill(); } });
  const puff = new THREE.Sprite(new THREE.SpriteMaterial({ map: puffTex, transparent: true, depthWrite: false })); g.add(puff); puff.visible = false;
  P.setPuff = u => { puff.visible = u > 0 && u < 1; if (!puff.visible) return; pan.updateMatrixWorld(true); const p = chim.localToWorld(new THREE.Vector3(0, 0.3 + u * 0.6, 0)); puff.position.copy(p); puff.scale.setScalar(0.25 + u * 0.9); puff.material.opacity = 1 - u * u; };
  return P;
}
