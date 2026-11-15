// 사용: node render_act.mjs <out.mp4> [w h] [stills t...]
import puppeteer from '/home/claude/pt/node_modules/puppeteer-core/lib/esm/puppeteer/puppeteer-core.js';
import fs from 'fs'; import { execFileSync } from 'child_process';
const [out, w = '960', h = '540', ...stills] = process.argv.slice(2);
const br = await puppeteer.launch({ executablePath: '/usr/bin/google-chrome', headless: 'new', protocolTimeout: 0,
  args: ['--no-sandbox', '--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'] });
const pg = await br.newPage();
pg.on('pageerror', e => console.log('PAGEERR', String(e).slice(0, 400)));
await pg.setViewport({ width: +w, height: +h });
await pg.goto(`http://localhost:8124/look.html?w=${w}&h=${h}&lite=1&set=1`);
await pg.waitForFunction('window.ready === true', { timeout: 0 });
const grab = async () => Buffer.from((await pg.evaluate(() => document.querySelector('canvas').toDataURL('image/jpeg', 0.94))).split(',')[1], 'base64');
if (stills.length) { for (const t of stills) { await pg.evaluate(t => window.frame(t), +t); fs.writeFileSync(out.replace('.png', `_${t}.png`), await grab()); } }
else {
  const dir = out + '_f'; fs.mkdirSync(dir, { recursive: true }); const n = Math.round(5.5 * 24), t0 = Date.now();
  for (let k = 0; k < n; k++) { await pg.evaluate(t => window.frame(t), k / 24); fs.writeFileSync(`${dir}/${String(k).padStart(4, '0')}.jpg`, await grab()); if (k % 24 === 0) console.log(k, ((Date.now() - t0) / 1000 / (k + 1)).toFixed(2) + 's/f'); }
  execFileSync('ffmpeg', ['-y', '-loglevel', 'error', '-framerate', '24', '-i', `${dir}/%04d.jpg`, '-c:v', 'libx264', '-crf', '18', '-pix_fmt', 'yuv420p', out]);
}
await br.close(); console.log('done');
