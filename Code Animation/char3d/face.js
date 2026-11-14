// chars.py face()를 Canvas 2D로 옮김 — 쏙쏙 건강백과 표정 18종을 그대로 쓴다.
// 좌표는 chars.py 픽셀 단위(얼굴 중심 원점, y 아래가 +). blink 0..1(1 = 완전히 감음), look=[x,y] -1..1
const INK = '#2B2D5B', WHITE = '#FFFFFF', PINK = '#FF7FA8', PURPLE = '#8E7CFF', TEAR = 'rgba(142,216,248,';

function stroke(c, w, col = INK) { c.lineWidth = w; c.strokeStyle = col; c.lineCap = 'round'; c.lineJoin = 'round'; c.stroke(); }
function line(c, x0, y0, x1, y1, w) { c.beginPath(); c.moveTo(x0, y0); c.lineTo(x1, y1); stroke(c, w); }
function oval(c, x, y, w, h, fill) { c.beginPath(); c.ellipse(x + w / 2, y + h / 2, w / 2, h / 2, 0, 0, Math.PI * 2); c.fillStyle = fill; c.fill(); }
function drop(c, x, y, s = 1) {
  c.save(); c.translate(x, y); c.scale(s, s);
  c.beginPath(); c.moveTo(0, -18); c.quadraticCurveTo(12, 2, 0, 12); c.quadraticCurveTo(-12, 2, 0, -18); c.closePath();
  c.fillStyle = '#8ED8F8'; c.fill(); stroke(c, 3.5); c.restore();
}

export function drawFace(c, mood = 'happy', { blush = PINK, look = [0, 0], gap = 46, blink = 0 } = {}) {
  for (const sx of [-1, 1]) {
    const ex = sx * gap + look[0] * 6, ey = look[1] * 5;
    let m = mood;
    // 깜빡임: 뜬 눈 종류는 세로로 눌렀다가, 거의 감기면 감은 선으로
    const openKinds = !['sleepy', 'yawn', 'happy_closed', 'relieved', 'proud', 'dizzy'].includes(m);
    if (openKinds && blink > 0.82) { c.beginPath(); c.moveTo(ex - 15, ey + 2); c.quadraticCurveTo(ex, ey + 8, ex + 15, ey + 2); stroke(c, 6); }
    else if (m === 'sleepy' || m === 'yawn') { c.beginPath(); c.moveTo(ex - 15, ey); c.quadraticCurveTo(ex, ey + 12, ex + 15, ey); stroke(c, 6); }
    else if (m === 'happy_closed' || m === 'relieved' || m === 'proud') {
      c.beginPath(); c.moveTo(ex - 15, ey + 5); c.quadraticCurveTo(ex, ey - 12, ex + 15, ey + 5); stroke(c, 6);
      if (m === 'proud') line(c, ex - sx * 14, ey - 24, ex + sx * 14, ey - 28, 5);
    } else if (m === 'dizzy') {
      for (const [r, w] of [[16, 5], [8, 4]]) { c.beginPath(); c.arc(ex, ey, r, 0, Math.PI * 2); stroke(c, w); }
    } else {
      c.save(); c.translate(ex, ey); c.scale(1, 1 - 0.85 * Math.min(blink / 0.82, 1)); c.translate(-ex, -ey);
      if (m === 'shock' || m === 'panic') {
        oval(c, ex - 19, ey - 23, 38, 46, WHITE); c.beginPath(); c.ellipse(ex, ey, 19, 23, 0, 0, Math.PI * 2); stroke(c, 5);
        c.beginPath(); c.arc(ex + look[0] * 3, ey + look[1] * 3, m === 'shock' ? 5.5 : 4.5, 0, Math.PI * 2); c.fillStyle = INK; c.fill();
      } else {
        const big = ['wow', 'awake', 'sparkle', 'cry'].includes(m);
        let h = big ? 40 : 34, w = big ? 30 : 26; if (m === 'sparkle') { h = 46; w = 34; }
        oval(c, ex - w / 2, ey - h / 2, w, h, INK);
        c.beginPath(); c.arc(ex - 4, ey - 8, 6.5, 0, Math.PI * 2); c.fillStyle = WHITE; c.fill();
        c.beginPath(); c.arc(ex + 5, ey + 7, 3, 0, Math.PI * 2); c.fill();
        if (m === 'sparkle') { c.beginPath(); c.arc(ex + 7, ey - 12, 3.5, 0, Math.PI * 2); c.fill(); c.beginPath(); c.arc(ex - 8, ey + 10, 2.5, 0, Math.PI * 2); c.fill(); }
        if (m === 'cry') oval(c, ex - w / 2 + 3, ey + h / 2 - 12, w - 6, 9, TEAR + '0.78)');
      }
      c.restore();
      if (m === 'panic') line(c, ex - sx * 14, ey - 30, ex + sx * 14, ey - 38, 6);
      if (m === 'cry') {
        c.beginPath(); c.moveTo(ex + sx * 8, ey + 20); c.quadraticCurveTo(ex + sx * 14, ey + 40, ex + sx * 10, ey + 60); stroke(c, 7, TEAR + '0.82)');
        line(c, ex - sx * 14, ey - 26, ex + sx * 14, ey - 34, 6);
      }
      if (m === 'angry') line(c, ex + sx * 17, ey - 38, ex - sx * 14, ey - 22, 8);
      if (m === 'tired') line(c, ex - 17, ey - 4, ex + 17, ey - 4, 6);
      if (m === 'serious') line(c, ex - sx * 16, ey - 30, ex + sx * 14, ey - 24, 6);
      if (m === 'worry') line(c, ex - sx * 14, ey - 26, ex + sx * 14, ey - 32, 6);
      if (m === 'pity') line(c, ex - sx * 15, ey - 35, ex + sx * 13, ey - 26, 6);   // 안쓰러움: 눈썹 안쪽이 올라감
    }
    if (mood === 'tired') { c.beginPath(); c.moveTo(ex - 13, ey + 26); c.quadraticCurveTo(ex, ey + 34, ex + 13, ey + 26); stroke(c, 4, 'rgba(142,124,255,0.67)'); }
  }
  const bl = ['proud', 'sparkle', 'relieved'].includes(mood) ? 0.9 : 0.6;
  c.save(); c.globalAlpha = bl; c.filter = 'blur(3px)';
  oval(c, -gap - 38, 22, 34, 18, blush); oval(c, gap + 4, 22, 34, 18, blush); c.restore();
  const my = 30; c.beginPath();
  const m = mood;
  if (m === 'awake' || m === 'sparkle') {
    c.moveTo(-16, my - 4); c.quadraticCurveTo(0, my + 20, 16, my - 4); c.closePath(); c.fillStyle = INK; c.fill();
    if (m === 'sparkle') oval(c, -7, my + 6, 14, 7, PINK);
  } else if (['happy', 'happy_closed', 'sleepy', 'relieved'].includes(m)) {
    c.moveTo(-11, my - 2); c.quadraticCurveTo(-5, my + 8, 0, my); c.quadraticCurveTo(5, my + 8, 11, my - 2); stroke(c, 5);
  } else if (m === 'proud') { c.moveTo(-14, my - 4); c.quadraticCurveTo(0, my + 14, 14, my - 4); stroke(c, 5); }
  else if (m === 'wow') { oval(c, -10, my - 6, 20, 22, INK); oval(c, -6, my + 6, 12, 8, PINK); }
  else if (m === 'shock') oval(c, -8, my - 6, 16, 24, INK);
  else if (m === 'yawn') { oval(c, -14, my - 8, 28, 32, INK); oval(c, -9, my + 8, 18, 12, PINK); }
  else if (m === 'smug') { c.moveTo(-10, my + 2); c.quadraticCurveTo(4, my + 10, 14, my - 4); stroke(c, 5); }
  else if (m === 'pity') { c.moveTo(-8, my + 3); c.quadraticCurveTo(0, my - 1, 8, my + 3); stroke(c, 5); }
  else if (m === 'tired' || m === 'worry') { c.moveTo(-10, my + 4); c.quadraticCurveTo(0, my - 2, 10, my + 4); stroke(c, 5); }
  else if (m === 'angry') { c.moveTo(-13, my + 8); c.quadraticCurveTo(0, my - 8, 13, my + 8); stroke(c, 6); }
  else if (m === 'cry') { c.moveTo(-12, my + 8); c.quadraticCurveTo(-6, my - 4, 0, my + 6); c.quadraticCurveTo(6, my - 4, 12, my + 8); stroke(c, 5); }
  else if (m === 'panic') { c.moveTo(-12, my + 4); c.lineTo(-6, my - 2); c.lineTo(0, my + 6); c.lineTo(6, my - 2); c.lineTo(12, my + 4); stroke(c, 5); }
  else if (m === 'dizzy') { c.moveTo(-12, my + 2); c.quadraticCurveTo(-6, my - 6, 0, my + 2); c.quadraticCurveTo(6, my + 10, 12, my + 2); stroke(c, 5); }
  else line(c, -9, my + 2, 9, my + 2, 5);
  if (m === 'panic' || m === 'relieved') drop(c, gap + 52, -30);
  if (m === 'panic') drop(c, -gap - 56, -14, 0.8);
}
export const MOODS = ['happy', 'tired', 'wow', 'sleepy', 'smug', 'worry', 'serious', 'awake', 'happy_closed',
  'angry', 'cry', 'shock', 'panic', 'relieved', 'dizzy', 'sparkle', 'yawn', 'proud', 'pity'];
