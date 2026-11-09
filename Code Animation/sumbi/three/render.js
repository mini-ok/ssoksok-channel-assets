// headless render of a three.js page: node render.js page.html outdir t0 t1 [fps]
// writes outdir/{color,id,normal,depth}_NNNN.png, only on twos (12 unique drawings per second)
const { chromium } = require('playwright');
const fs = require('fs');
(async () => {
  const [page, out, t0, t1, fpsArg, view] = process.argv.slice(2);
  const fps = +(fpsArg || 24);
  fs.mkdirSync(out, {recursive: true});
  const b = await chromium.launch({args: ['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader']});
  const p = await b.newPage({viewport: {width: 1920, height: 1040}});
  p.on('console', m => console.log('[page]', m.text()));
  await p.goto('file://' + process.cwd() + '/' + page);
  console.log('meshes', await p.evaluate(() => window.info()));
  try { fs.writeFileSync(`${out}/meta.json`, JSON.stringify(await p.evaluate(() => window.meta ? window.meta() : {}))); } catch (e) {}
  if (view) await p.evaluate(v => { window.VIEW = JSON.parse(v); }, view);
  const st = Date.now(); let n = 0;
  const only = process.env.FRAMES ? process.env.FRAMES.split(',').map(Number) : null;
  for (let i = Math.round(+t0 * fps); i < Math.round(+t1 * fps); i += 2) {
    if (only && !only.includes(i)) continue;
    for (const pass of (process.env.PASSES || 'color,id,normal,depth').split(',')) {
      await p.evaluate(([t, ps]) => window.renderAt(t, ps), [i / fps, pass]);
      await p.screenshot({path: `${out}/${pass}_${String(i).padStart(4, '0')}.png`, clip: {x: 0, y: 0, width: 1920, height: 1040}});
    }
    n++;
  }
  console.log('drawings', n, 'ms/drawing (4 passes)', ((Date.now() - st) / n).toFixed(0));
  await b.close();
})();
