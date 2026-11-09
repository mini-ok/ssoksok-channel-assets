// render multiplane plates: node plates.js page.html outdir
const { chromium } = require('playwright');
const fs = require('fs');
(async () => {
  const [page, out] = process.argv.slice(2);
  fs.mkdirSync(out, {recursive: true});
  const PW = 3000, H = 1040;
  const b = await chromium.launch({args: ['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader']});
  const p = await b.newPage({viewport: {width: PW, height: H}});
  await p.goto('file://' + process.cwd() + '/' + page);
  // layers: name, zmin, zmax, include ground
  const layers = [['sky', -999, -999, false], ['far', -99, -9, true], ['mid', -9, -2.5, false], ['near', -2.5, 99, false]];
  await p.evaluate(() => { window.PLATE_ALPHA = true; document.getElementById('c').width = 3000; });
  for (const [name, z0, z1, g] of layers) {
    for (const pass of ['color', 'id', 'normal', 'depth']) {
      if (name === 'sky' && pass !== 'color') continue;
      await p.evaluate(([ps, a, bb, gg]) => window.renderLayer(ps, a, bb, 3000, gg, 1.5), [pass, z0, z1, g]);
      await p.screenshot({path: `${out}/${name}_${pass}.png`, clip: {x: 0, y: 0, width: PW, height: H}, omitBackground: true});
    }
    console.log('layer', name);
  }
  await b.close();
})();
