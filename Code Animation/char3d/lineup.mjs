import puppeteer from '/home/claude/pt/node_modules/puppeteer-core/lib/esm/puppeteer/puppeteer-core.js';
import fs from 'fs';
const [prefix, json, w = '1920', h = '540'] = process.argv.slice(2); const shots = JSON.parse(fs.readFileSync(json, 'utf8'));
const br = await puppeteer.launch({ executablePath: '/usr/bin/google-chrome', headless: 'new', protocolTimeout: 0, args: ['--no-sandbox', '--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'] });
const pg = await br.newPage(); pg.on('pageerror', e => console.log('PAGEERR', String(e).slice(0, 400)));
await pg.setViewport({ width: +w, height: +h }); await pg.goto(`http://localhost:8124/lineup.html?w=${w}&h=${h}`); await pg.waitForFunction('window.ready === true', { timeout: 0 });
for (let i = 0; i < shots.length; i++) { await pg.evaluate(s => window.shot(s), shots[i]);
  if (i === 0) console.log('collide:', JSON.stringify(await pg.evaluate(() => window.collide())));
  fs.writeFileSync(`${prefix}_${i}.png`, Buffer.from((await pg.evaluate(() => document.querySelector('canvas').toDataURL('image/png'))).split(',')[1], 'base64')); }
await br.close(); console.log('ok');
