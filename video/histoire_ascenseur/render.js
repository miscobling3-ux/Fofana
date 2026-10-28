// Rendu image par image de index.html (1080x1920, 30 i/s) avec Chromium + ffmpeg.
// node render.js --stills 2,13,30   -> PNG d'aperçu dans build/
// node render.js                    -> build/video_muette.mp4 (4 rendus en parallèle)
const { chromium } = require('playwright');
const { spawn, execFileSync } = require('child_process');
const http = require('http');
const fs = require('fs');
const path = require('path');

const ROOT = __dirname, OUT = path.join(ROOT, 'build');
const FPS = 30, W = 1080, H = 1920;
let DUR = 84.5;
fs.mkdirSync(OUT, { recursive: true });

const TYPES = { '.html': 'text/html', '.js': 'text/javascript', '.json': 'application/json', '.svg': 'image/svg+xml', '.webp': 'image/webp', '.jpg': 'image/jpeg', '.png': 'image/png', '.ttf': 'font/ttf' };
function serve() {
  return new Promise(res => {
    const srv = http.createServer((req, rep) => {
      const f = path.join(ROOT, decodeURIComponent(req.url.split('?')[0]));
      if (!f.startsWith(ROOT) || !fs.existsSync(f) || fs.statSync(f).isDirectory()) { rep.writeHead(404); return rep.end(); }
      rep.writeHead(200, { 'Content-Type': TYPES[path.extname(f)] || 'application/octet-stream' });
      fs.createReadStream(f).pipe(rep);
    }).listen(0, () => res(srv));
  });
}

async function openPage(browser, port) {
  const page = await browser.newPage({ viewport: { width: W, height: H }, deviceScaleFactor: 1 });
  page.on('pageerror', e => console.error('ERREUR PAGE:', e.message));
  await page.goto(`http://127.0.0.1:${port}/index.html`);
  await page.evaluate(() => window.ready);
  DUR = await page.evaluate(() => window.DUR || 84.5);
  return page;
}

async function renderRange(browser, port, f0, f1, file) {
  const page = await openPage(browser, port);
  const ff = spawn('ffmpeg', ['-v', 'error', '-y', '-f', 'image2pipe', '-framerate', String(FPS), '-c:v', 'mjpeg', '-i', '-',
    '-c:v', 'libx264', '-preset', 'medium', '-crf', '17', '-pix_fmt', 'yuv420p', file], { stdio: ['pipe', 'inherit', 'inherit'] });
  for (let f = f0; f < f1; f++) {
    await page.evaluate(t => window.seek(t), f / FPS);
    const buf = await page.screenshot({ type: 'jpeg', quality: 94 });
    if (!ff.stdin.write(buf)) await new Promise(r => ff.stdin.once('drain', r));
    if (f % 150 === 0) console.log(`  image ${f}/${Math.round(DUR * FPS)}`);
  }
  ff.stdin.end();
  await new Promise(r => ff.on('close', r));
  await page.close();
}

(async () => {
  const args = process.argv.slice(2);
  const si = args.indexOf('--stills');
  const srv = await serve();
  const port = srv.address().port;
  const browser = await chromium.launch();
  if (si < 0) { const p = await openPage(browser, port); await p.close(); }

  if (si >= 0) {
    const page = await openPage(browser, port);
    for (const t of args[si + 1].split(',').map(Number)) {
      await page.evaluate(t => window.seek(t), t);
      await page.screenshot({ path: path.join(OUT, `still_${t.toFixed(2)}.png`) });
    }
  } else {
    const total = Math.round(DUR * FPS), N = 4, parts = [];
    const per = Math.ceil(total / N);
    await Promise.all(Array.from({ length: N }, (_, i) => {
      const file = path.join(OUT, `part${i}.mp4`); parts.push(file);
      return renderRange(browser, port, i * per, Math.min(total, (i + 1) * per), file);
    }));
    fs.writeFileSync(path.join(OUT, 'parts.txt'), parts.map(p => `file '${p}'`).join('\n'));
    execFileSync('ffmpeg', ['-v', 'error', '-y', '-f', 'concat', '-safe', '0', '-i', path.join(OUT, 'parts.txt'), '-c', 'copy', path.join(OUT, 'video_muette.mp4')]);
    console.log('OK -> build/video_muette.mp4');
  }
  await browser.close();
  srv.close();
})();
