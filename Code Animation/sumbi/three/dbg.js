const { chromium } = require('playwright');
(async () => {
  const b = await chromium.launch({args: ['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader']});
  const p = await b.newPage({viewport: {width: 1920, height: 1040}});
  p.on('console', m => console.log('[page]', m.text()));
  p.on('pageerror', e => console.log('[err]', e.message));
  await p.goto('file://' + process.cwd() + '/' + process.argv[2]);
  console.log(await p.evaluate(process.argv[3]));
  await b.close();
})();
