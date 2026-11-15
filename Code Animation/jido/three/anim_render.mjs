// 사용: node anim_render.mjs <shot> <out.mp4> [fps=24] [w=960 h=540] [t1 t2 ... → 정지 화면 PNG만]
import puppeteer from '/home/claude/pt/node_modules/puppeteer-core/lib/esm/puppeteer/puppeteer-core.js';
import fs from 'fs'; import { spawn } from 'child_process';
const [shot, out, fps = '24', w = '960', h = '540', ...stills] = process.argv.slice(2);
const br = await puppeteer.launch({ executablePath: '/usr/bin/google-chrome', headless: 'new', protocolTimeout: 0,
  args: ['--no-sandbox', '--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'] });
const pg = await br.newPage();
pg.on('pageerror', e => console.log('PAGEERR', String(e).slice(0, 400)));
await pg.setViewport({ width: +w, height: +h });
await pg.goto(`http://localhost:8123/anim.html?w=${w}&h=${h}&lite=1`);
await pg.waitForFunction('window.ready === true', { timeout: 0 });
const dur = await pg.evaluate(async (id) => (await import('./shots.js')).SHOTS[id].dur, shot);
const grab = async () => Buffer.from((await pg.evaluate(() => document.querySelector('canvas').toDataURL('image/jpeg', 0.94))).split(',')[1], 'base64');
if (stills.length) {
  for (const t of stills) { await pg.evaluate((id, t) => window.renderShot(id, t), shot, +t); fs.writeFileSync(out.replace('.png', `_${t}.png`), await grab()); }
} else {
  const ff = { stdin: { end() {} } };
  const n = Math.round(dur * +fps);
  const dir = out.replace('.mp4', '_f'); fs.mkdirSync(dir, { recursive: true }); const t0 = Date.now();
  for (let k = 0; k < n; k++) { await pg.evaluate((id, t) => window.renderShot(id, t), shot, k / +fps); fs.writeFileSync(`${dir}/${String(k).padStart(4, '0')}.jpg`, await grab()); if (k % 12 === 0) console.log(shot, k, '/', n, ((Date.now() - t0) / 1000 / (k + 1)).toFixed(2) + 's/f'); }
  ff.stdin.end();
  const enc = spawn('ffmpeg', ['-y', '-loglevel', 'error', '-framerate', fps, '-i', `${dir}/%04d.jpg`, '-c:v', 'libx264', '-crf', '20', '-pix_fmt', 'yuv420p', out]); await new Promise(r => enc.on('close', r));
  console.log('done', shot, n);
}
await br.close();
