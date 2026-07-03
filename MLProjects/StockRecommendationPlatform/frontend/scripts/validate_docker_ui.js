const { chromium } = require('@playwright/test');

const BASE = 'http://localhost:3010';

const PAGES = [
  { path: '/', name: 'Home / Analysis' },
  { path: '/momentum', name: 'Momentum Sectors' },
  { path: '/compare', name: 'Compare' },
  { path: '/correlation', name: 'Correlation' },
  { path: '/portfolio', name: 'Portfolio' },
  { path: '/history', name: 'Analysis History' },
  { path: '/settings', name: 'Settings' },
  { path: '/logs', name: 'Logs' },
];

async function main() {
  const browser = await chromium.launch({ channel: 'msedge', headless: false });
  const ctx = await browser.newContext({ viewport: { width: 1280, height: 900 } });
  const page = await ctx.newPage();

  const results = [];

  for (const { path, name } of PAGES) {
    try {
      const resp = await page.goto(BASE + path, { waitUntil: 'networkidle', timeout: 15000 });
      const status = resp ? resp.status() : 0;
      const title = await page.title();
      const body = await page.locator('body').innerText({ timeout: 5000 }).catch(() => '');
      const hasError = /error|not found|404/i.test(body.slice(0, 200));
      results.push({ name, path, status, title, ok: status === 200 && !hasError });
    } catch (e) {
      results.push({ name, path, status: 0, title: '', ok: false, err: e.message.slice(0, 80) });
    }
  }

  await page.goto(BASE + '/', { waitUntil: 'domcontentloaded' });
  await page.waitForTimeout(1000);

  let analysisOk = false;
  try {
    const input = page.locator('input[placeholder*="ticker" i], input[placeholder*="symbol" i], input[type="text"]').first();
    await input.fill('AAPL');
    const btn = page.locator('button:has-text("Analyze"), button:has-text("Run"), button[type="submit"]').first();
    await btn.click();
    await page.waitForSelector('[data-testid="analysis-result"], .analysis-result, text=Verdict, text=BUY, text=SELL, text=HOLD', { timeout: 60000 });
    analysisOk = true;
  } catch (e) {
    analysisOk = false;
  }

  await browser.close();

  console.log('\n=== Docker UI Validation Results ===\n');
  for (const r of results) {
    const icon = r.ok ? '✅' : '❌';
    const detail = r.err ? ` (${r.err})` : ` [HTTP ${r.status}]`;
    console.log(`${icon} ${r.name.padEnd(25)} ${r.path}${detail}`);
  }
  console.log(`\n${analysisOk ? '✅' : '❌'} AAPL Analysis end-to-end (Verdict rendered)`);

  const passed = results.filter(r => r.ok).length;
  const total = results.length;
  console.log(`\nPages: ${passed}/${total} passed`);
}

main().catch(e => { console.error(e); process.exit(1); });
