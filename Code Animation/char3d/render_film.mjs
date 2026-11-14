// 사용: node render_film.mjs still <out_prefix> <cut>:<t> [...]      → 정지 화면(+충돌 결과)
//       node render_film.mjs check <cut> [...]                       → 컷 전체 프레임 충돌 검사
//       node render_film.mjs video <out.mp4> <cut> [...]              → 컷들을 이어 540p mp4(소리 없음)
import puppeteer from '/home/claude/pt/node_modules/puppeteer-core/lib/esm/puppeteer/puppeteer-core.js';
import fs from 'fs'; import { execFileSync } from 'child_process';
const [mode, ...args] = process.argv.slice(2);
const W = +(process.env.W || 960), H = +(process.env.H || 540), FPS = 24;
const br = await puppeteer.launch({ executablePath: '/usr/bin/google-chrome', headless: 'new', protocolTimeout: 0,
  args: ['--no-sandbox', '--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'] });
const pg = await br.newPage(); pg.on('pageerror', e => console.log('PAGEERR', String(e).slice(0, 500)));
pg.on('console', m => { if (m.type() === 'error') console.log('CONSOLE', m.text().slice(0, 300)); });
await pg.setViewport({ width: W, height: H });
await pg.goto(`http://localhost:8124/film.html?w=${W}&h=${H}&wall=${process.env.WALL || 'C'}${process.env.DBG ? '&dbg=1' : ''}`); await pg.waitForFunction('window.ready === true', { timeout: 0 });
if (process.env.NORENDER) await pg.evaluate(() => { window.NORENDER = true; });   // 검사만(그리기 생략)
const durs = await pg.evaluate(() => window.cuts);
const grab = async (q = 'image/png') => Buffer.from((await pg.evaluate(q => document.querySelector('canvas').toDataURL(q, 0.93), q)).split(',')[1], 'base64');
if (mode === 'still') {
  const [prefix, ...shots] = args;
  for (const s of shots) { const [c, t] = s.split(':'); await pg.evaluate((c, t) => window.frame(c, t), c, +t);
    const col = await pg.evaluate(() => window.collide()); fs.writeFileSync(`${prefix}_${c}_${t}.png`, await grab()); console.log(s, col.length ? 'COLLIDE ' + col.join(' ') : 'ok'); }
} else if (mode === 'check') {
  for (const c of args) { const n = Math.round(durs[c] * FPS); const bad = [];
    for (let k = 0; k < n; k++) { const col = await pg.evaluate((c, t) => { window.frame(c, t); return window.collide(); }, c, k / FPS); if (col.length) bad.push(`${k} ${col.join(' ')}`); }
    console.log(c, n, '프레임', bad.length ? `충돌 ${bad.length}` : '충돌 없음'); for (const b of bad.slice(0, 40)) console.log('  ', b); }
} else if (mode === 'export') {   // export <outdir> <cut...> → <cut>.glb + <cut>.json + faces/<cut>_<char>_0001.png …(Blender용)
  const [dir, ...cs] = args; fs.mkdirSync(`${dir}/faces`, { recursive: true });
  for (const c of cs) { const t0 = Date.now();
    for (const p of (process.env.PRE || 'C9:4,C13:5.99').split(',').filter(Boolean)) { const [pc, pt] = p.split(':'); if (pc !== c) await pg.evaluate((pc, pt) => window.frame(pc, pt), pc, +pt); }   // 부서진 펌프·못에 건 휴가권 상태를 먼저 만듦
    const r = await pg.evaluate(c => window.exportCut(c), c);
    fs.writeFileSync(`${dir}/${c}.glb`, Buffer.from(r.glb, 'base64'));
    for (const [k, F] of Object.entries(r.faces)) { F.images.forEach((d, i) => fs.writeFileSync(`${dir}/faces/${c}_${k}_${String(i + 1).padStart(4, '0')}.png`, Buffer.from(d.split(',')[1], 'base64'))); F.count = F.images.length; delete F.images; }
    fs.mkdirSync(`${dir}/screens`, { recursive: true });
    for (const [k, S] of Object.entries(r.screens || {})) { S.images.forEach((d, i) => fs.writeFileSync(`${dir}/screens/${c}_${k}_${String(i + 1).padStart(4, '0')}.png`, Buffer.from(d.split(',')[1], 'base64'))); S.count = S.images.length; delete S.images; }
    r.meta.screens = r.screens || {};
    r.meta.faces = r.faces; fs.writeFileSync(`${dir}/${c}.json`, JSON.stringify(r.meta));
    console.log(c, 'exported', (fs.statSync(`${dir}/${c}.glb`).size / 1e6).toFixed(1) + 'MB', r.meta.tracks, 'tracks', ((Date.now() - t0) / 1000).toFixed(0) + 's');
    await pg.reload(); await pg.waitForFunction('window.ready === true', { timeout: 0 }); }   // 컷마다 새로 불러옴(내보내며 장면을 재배치하므로)
} else if (mode === 'audit') {   // audit <cut...> → glTF/Blender로 그대로 안 넘어가는 요소 목록(JSON 한 줄씩)
  for (const c of args) { for (const p of (process.env.PRE || 'C9:4,C13:5.99').split(',').filter(Boolean)) { const [pc, pt] = p.split(':'); if (pc !== c) await pg.evaluate((pc, pt) => window.frame(pc, pt), pc, +pt); }
    console.log('AUDIT ' + JSON.stringify(await pg.evaluate(c => window.auditCut(c), c))); await pg.reload(); await pg.waitForFunction('window.ready === true', { timeout: 0 }); }
} else if (mode === 'eval') {   // eval <cut:t> '<js 식>' ... → frame 뒤 식의 값(JSON)
  const [shot, ...exprs] = args; const [c, t] = shot.split(':'); await pg.evaluate((c, t) => window.frame(c, t), c, +t);
  for (const e of exprs) console.log(JSON.stringify(await pg.evaluate(e => { const v = eval(e); return v; }, e)));
} else if (mode === 'probe') {   // probe <cut:t> '<pose json>' ...  → 심장을 원점에 세우고 휴가권 위치·자기 충돌
  const [shot, ...poses] = args; const [c, t] = shot.split(':'); await pg.evaluate((c, t) => window.frame(c, t), c, +t);
  for (const p of poses) { const r = await pg.evaluate(p => { const o = window.probe(JSON.parse(p)); return [o, window.collide().filter(x => x.startsWith('heart:') && !x.includes('|') === false && x.split('|').every(y => !y.includes(':') || y.startsWith('heart:')) && !x.match(/\|[a-zA-Z]+$/) ? true : x.split('|')[1].startsWith('heart') || ['body','upL','upR','loL','loR','handL','handR','ticket','footL','footR','cap','brim'].includes(x.split('|')[1]))]; }, p);
    console.log(p, JSON.stringify(r[0]), r[1].length ? 'SELF ' + r[1].join(' ') : ''); }
} else if (mode === 'frames') {   // 일부 프레임만 다시: frames <dir> <cut> <from> <to>  (파일 번호 = 프레임 번호)
  const [dir, c, from, to] = args; fs.mkdirSync(dir, { recursive: true });
  for (let k = +from; k <= +to; k++) { const col = await pg.evaluate((c, t) => { window.frame(c, t); return window.collide(); }, c, k / FPS);
    if (col.length) console.log('COLLIDE', k, (k / FPS).toFixed(2), col.join(' '));
    fs.writeFileSync(`${dir}/${String(k).padStart(5, '0')}.jpg`, await grab('image/jpeg')); }
  console.log('frames done', from, to);
} else if (mode === 'cuts') {   // cuts <dir> <cut...> → <dir>/<cut>_f/%05d.jpg + <dir>/<cut>.mp4, 충돌은 <dir>/<cut>.collide.txt (PRE=컷:t,… 먼저 한 번 실행)
  const [dir, ...cs] = args; fs.mkdirSync(dir, { recursive: true }); const t0 = Date.now(); let i = 0;
  for (const p of (process.env.PRE || '').split(',').filter(Boolean)) { const [c, t] = p.split(':'); await pg.evaluate((c, t) => window.frame(c, t), c, +t); }
  for (const c of cs) { const n = Math.round(durs[c] * FPS), fd = `${dir}/${c}_f`; fs.rmSync(fd, { recursive: true, force: true }); fs.mkdirSync(fd, { recursive: true }); fs.rmSync(`${dir}/${c}.collide.txt`, { force: true });
    for (let k = 0; k < n; k++) { const col = await pg.evaluate((c, t) => { window.frame(c, t); return window.collide(); }, c, k / FPS);
      if (col.length) fs.appendFileSync(`${dir}/${c}.collide.txt`, `${k} ${(k / FPS).toFixed(2)} ${col.join(' ')}\n`);
      fs.writeFileSync(`${fd}/${String(k).padStart(5, '0')}.jpg`, await grab('image/jpeg')); i++; }
    execFileSync('ffmpeg', ['-y', '-loglevel', 'error', '-framerate', String(FPS), '-i', `${fd}/%05d.jpg`, '-c:v', 'libx264', '-crf', '18', '-pix_fmt', 'yuv420p', `${dir}/${c}.mp4`]);
    console.log(c, 'done', n, ((Date.now() - t0) / 1000 / i).toFixed(2) + 's/f', fs.existsSync(`${dir}/${c}.collide.txt`) ? 'COLLIDE' : 'clean'); }
} else if (mode === 'video') {
  const [out, ...cs] = args; const dir = out + '_f'; fs.rmSync(dir, { recursive: true, force: true }); fs.mkdirSync(dir, { recursive: true }); let i = 0; const t0 = Date.now();
  for (const c of cs) { const n = Math.round(durs[c] * FPS);
    for (let k = 0; k < n; k++) { const col = await pg.evaluate((c, t, chk) => { window.frame(c, t); return chk ? window.collide() : []; }, c, k / FPS, !!process.env.CHECK);
      if (col.length) fs.appendFileSync(out + '.collide.txt', `${c} ${k} ${(k / FPS).toFixed(2)} ${col.join(' ')}\n`);
      fs.writeFileSync(`${dir}/${String(i++).padStart(5, '0')}.jpg`, await grab('image/jpeg')); if (k % 48 === 0) console.log(c, k, ((Date.now() - t0) / 1000 / (i)).toFixed(2) + 's/f'); }
    console.log(c, 'done', ((Date.now() - t0) / 1000 / i).toFixed(2) + 's/f'); }
  execFileSync('ffmpeg', ['-y', '-loglevel', 'error', '-framerate', String(FPS), '-i', `${dir}/%05d.jpg`, '-c:v', 'libx264', '-crf', '18', '-pix_fmt', 'yuv420p', out]);
}
await br.close();
