// 모든 프레임 충돌 검사: node check_act.mjs
import puppeteer from '/home/claude/pt/node_modules/puppeteer-core/lib/esm/puppeteer/puppeteer-core.js';
const br = await puppeteer.launch({ executablePath: '/usr/bin/google-chrome', headless: 'new', protocolTimeout: 0,
  args: ['--no-sandbox', '--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'] });
const pg = await br.newPage(); pg.on('pageerror', e => console.log('PAGEERR', String(e).slice(0, 400)));
await pg.setViewport({ width: 320, height: 180 });
await pg.goto('http://localhost:8124/look.html?w=320&h=180&lite=1&set=1');
await pg.waitForFunction('window.ready === true', { timeout: 0 });
const res = await pg.evaluate(async () => { const { poseAt, DUR } = await import('./act.js'); const r = [];
  for (let k = 0; k < DUR * 24; k++) { const a = poseAt(k / 24); window.rigPose(a); const c = window.collide(); if (c.length) r.push([k, (k / 24).toFixed(2), c.join(' ')]); } return r; });
if (!res.length) console.log('충돌 없음'); else { console.log('충돌 프레임', res.length); for (const r of res) console.log(r.join('  ')); }
await br.close();
