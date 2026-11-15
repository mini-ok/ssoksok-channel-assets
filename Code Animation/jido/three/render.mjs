// 사용: node render.mjs raster out_dir t0 t1 fps [w h]      → 프레임 PNG
//       node render.mjs pt out.png t samples [w h]          → 경로 추적 한 장
import puppeteer from '/home/claude/pt/node_modules/puppeteer-core/lib/esm/puppeteer/puppeteer-core.js';
import fs from 'fs';
const [mode, out, a, b, c, w = '1920', h = '1080'] = process.argv.slice(2);
const br = await puppeteer.launch({ executablePath: '/usr/bin/google-chrome', headless: 'new', protocolTimeout: 0,
  args: ['--no-sandbox', '--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'] });
const pg = await br.newPage();
pg.on('pageerror', e => console.log('PAGEERR', String(e).slice(0, 400)));
pg.on('console', m => { if (m.type() === 'error' || m.type() === 'warning') console.log('CONSOLE', m.text().slice(0, 300)); });
await pg.setViewport({ width: +w, height: +h });
await pg.goto(`http://localhost:8123/page.html?mode=${mode}&w=${w}&h=${h}`);
await pg.waitForFunction('window.ready === true', { timeout: 0 });
const grab = async (file) => { const d = await pg.evaluate(() => document.querySelector('canvas').toDataURL('image/png')); fs.writeFileSync(file, Buffer.from(d.split(',')[1], 'base64')); };
if (mode === 'raster') {
  fs.mkdirSync(out, { recursive: true });
  const t0 = +a, t1 = +b, fps = +c; let k = 0;
  for (let t = t0; t < t1 - 1e-6; t += 1 / fps, k++) {
    const ms = await pg.evaluate(t => window.renderAt(t), t);
    await grab(`${out}/f${String(k).padStart(4, '0')}.png`);
    if (k % 12 === 0) console.log('frame', k, 't', t.toFixed(2), Math.round(ms) + 'ms');
  }
} else {
  const ms = await pg.evaluate((t, s) => window.renderAt(t, s), +a, +b);
  await grab(out); console.log('pt', b, 'samples', Math.round(ms / 1000) + 's');
}
await br.close();
