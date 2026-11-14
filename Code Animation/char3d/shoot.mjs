// 사용: node shoot.mjs <out_prefix> <json shots> [w h query]   → <prefix>_<i>.png
import puppeteer from '/home/claude/pt/node_modules/puppeteer-core/lib/esm/puppeteer/puppeteer-core.js';
import fs from 'fs';
const [prefix, shotsJson, w = '960', h = '540', query = ''] = process.argv.slice(2);
const shots = JSON.parse(fs.readFileSync(shotsJson, 'utf8'));
const br = await puppeteer.launch({ executablePath: '/usr/bin/google-chrome', headless: 'new', protocolTimeout: 0,
  args: ['--no-sandbox', '--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'] });
const pg = await br.newPage();
pg.on('pageerror', e => console.log('PAGEERR', String(e).slice(0, 400)));
pg.on('console', m => { if (m.type() === 'error') console.log('CONSOLE', m.text().slice(0, 300)); });
await pg.setViewport({ width: +w, height: +h });
await pg.goto(`http://localhost:8124/look.html?w=${w}&h=${h}&${query}`);
await pg.waitForFunction('window.ready === true', { timeout: 0 });
for (let i = 0; i < shots.length; i++) {
  await pg.evaluate(s => window.shot(s), shots[i]);
  const d = await pg.evaluate(() => document.querySelector('canvas').toDataURL('image/png'));
  fs.writeFileSync(`${prefix}_${i}.png`, Buffer.from(d.split(',')[1], 'base64'));
}
await br.close(); console.log('ok', shots.length);
