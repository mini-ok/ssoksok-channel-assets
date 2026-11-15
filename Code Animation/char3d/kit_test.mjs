import puppeteer from '/home/claude/pt/node_modules/puppeteer-core/lib/esm/puppeteer/puppeteer-core.js';
import fs from 'fs';
const [hash, out] = process.argv.slice(2);
const br = await puppeteer.launch({ executablePath: '/usr/bin/google-chrome', headless: 'new', protocolTimeout: 0,
  args: ['--no-sandbox', '--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'] });
const pg = await br.newPage();
pg.on('pageerror', e => console.log('PAGEERR', String(e).slice(0, 400)));
pg.on('console', m => { if (m.type() === 'error') console.log('CONSOLE', m.text().slice(0, 300)); });
await pg.setViewport({ width: 1100, height: 900 });
const t0 = Date.now();
await pg.goto(`http://localhost:8124/cache/heart_gpu_render_kit_v2.html?w=640&h=360#${hash}`);
await pg.waitForFunction('document.title === "DONE"', { timeout: 0, polling: 1000 });
const d = await pg.evaluate(() => document.querySelector('#stage canvas').toDataURL('image/png'));
fs.writeFileSync(out, Buffer.from(d.split(',')[1], 'base64')); console.log('ok', (Date.now() - t0) / 1000, 's');
await br.close();
