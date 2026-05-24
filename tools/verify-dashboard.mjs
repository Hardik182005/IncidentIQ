// Smoke-test the compiled Command Center: serve the repo, load dashboard.html in
// real Chrome, and assert it renders with no JS errors (no in-browser Babel).
import http from 'node:http';
import { readFileSync, existsSync } from 'node:fs';
import { join, extname, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';
import { chromium } from 'playwright';

const root = join(dirname(fileURLToPath(import.meta.url)), '..');
const types = { '.html':'text/html', '.js':'text/javascript', '.jsx':'text/javascript', '.css':'text/css', '.json':'application/json' };

const server = http.createServer((req, res) => {
  let p = join(root, decodeURIComponent(req.url.split('?')[0]));
  if (!existsSync(p)) { res.writeHead(404); return res.end('nf'); }
  res.writeHead(200, { 'Content-Type': types[extname(p)] || 'application/octet-stream' });
  res.end(readFileSync(p));
});

await new Promise(r => server.listen(0, r));
const port = server.address().port;

const browser = await chromium.launch({ channel: 'chrome' });
const page = await browser.newPage();
const errors = [];
page.on('console', m => { if (m.type() === 'error') errors.push(m.text()); });
page.on('pageerror', e => errors.push('PAGEERROR: ' + e.message));
const failedUrls = [];
page.on('response', r => { if (r.status() >= 400) failedUrls.push(r.status() + ' ' + r.url()); });

await page.goto(`http://localhost:${port}/screens/dashboard.html`, { waitUntil: 'networkidle' });
await page.waitForTimeout(1500);

const rootChildren = await page.evaluate(() => document.getElementById('root').children.length);
const hasFeed = await page.evaluate(() => document.body.innerText.includes('Live Incident Feed'));
const hasOrb = await page.evaluate(() => document.body.innerText.includes('ASK IQ-SENTRY'));
const hasSidebar = await page.evaluate(() => document.body.innerText.includes('Command Center'));

// network-error console noise (no backend) is expected; filter it out
// Only /api/* and favicon 404s are expected without a backend; anything else is real.
const unexpected404 = failedUrls.filter(u => !/\/api\/|favicon/i.test(u));
const realErrors = errors.filter(e =>
  !/Failed to fetch|fetch incidents|WebSocket|ws:\/\/|net::ERR|Failed to load resource/i.test(e));

console.log(JSON.stringify({ rootChildren, hasFeed, hasOrb, hasSidebar, failedUrls, unexpected404, realErrors }, null, 2));

await browser.close();
server.close();

if (rootChildren === 0 || realErrors.length || unexpected404.length) {
  console.error('VERIFY FAILED');
  process.exit(1);
}
console.log('VERIFY OK');
