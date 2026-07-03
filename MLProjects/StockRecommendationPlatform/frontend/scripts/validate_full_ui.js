const { chromium } = require('@playwright/test');

const BASE = 'http://app.stockresearch.local';
const API  = 'http://api.stockresearch.local';

const results = [];
function pass(name, detail = '') { results.push({ ok: true,  name, detail }); }
function fail(name, detail = '') { results.push({ ok: false, name, detail }); }

function corsErrors(errors) { return errors.filter(e => e.includes('CORS') || e.includes('Access-Control')); }
function critical404s(notFound) { return notFound.filter(u => !u.includes('favicon') && !u.includes('.ico')); }

async function openPage(browser) {
  const ctx = await browser.newContext({ viewport: { width: 1440, height: 900 } });
  const page = await ctx.newPage();
  const errors = [], notFound = [];
  page.on('console', m => { if (m.type() === 'error') errors.push(m.text()); });
  page.on('response', r => {
    if (r.status() >= 400 && r.url().includes('stockresearch'))
      notFound.push(`${r.status()} ${r.url()}`);
  });
  return { ctx, page, errors, notFound };
}

async function nav(page, path, waitFor = 'domcontentloaded') {
  return page.goto(BASE + path, { waitUntil: waitFor, timeout: 15000 });
}

// waitForFunction correct Playwright API: (fn, arg, options) — pass null for no arg
async function waitText(page, text, timeout = 10000) {
  await page.waitForFunction(t => document.body.innerText.includes(t), text, { timeout });
}
async function waitTds(page, count = 5, timeout = 20000) {
  await page.waitForFunction(n => document.querySelectorAll('td').length >= n, count, { timeout });
}

async function main() {
  const browser = await chromium.launch({ channel: 'msedge', headless: false });
  console.log('=== Full UI Validation: http://app.stockresearch.local ===\n');

  // ── 1. Home page load ──────────────────────────────────────────────────────
  {
    const { ctx, page, errors } = await openPage(browser);
    try {
      const resp = await nav(page, '/');
      await waitText(page, 'Analyze Symbol');
      if (corsErrors(errors).length) fail('Home page loads', corsErrors(errors)[0].slice(0,80));
      else pass('Home page loads', `HTTP ${resp.status()}`);
      await page.screenshot({ path: 'scripts/ss_home.png' });
    } catch(e) { fail('Home page loads', e.message.slice(0,80)); }
    await ctx.close();
  }

  // ── 2. AAPL analysis end-to-end ───────────────────────────────────────────
  console.log('Running AAPL end-to-end analysis...');
  {
    const { ctx, page, errors } = await openPage(browser);
    try {
      await nav(page, '/');
      await page.waitForTimeout(1000);
      await page.locator('input').first().fill('AAPL');
      await page.locator('button:has-text("Run Analysis")').click();
      await page.waitForFunction(
        () => /BUY|SELL|HOLD|STRONG/i.test(document.body.innerText),
        null,
        { timeout: 120000 }
      );
      const body = await page.locator('body').innerText();
      const verdict = (body.match(/\b(STRONG BUY|BUY|STRONG SELL|SELL|HOLD)\b/i) || [])[0] || '?';
      const ce = corsErrors(errors);
      if (ce.length) fail('AAPL analysis end-to-end', 'CORS: ' + ce[0].slice(0,80));
      else pass('AAPL analysis end-to-end', `Verdict: ${verdict.toUpperCase()}`);
      await page.screenshot({ path: 'scripts/ss_analysis.png' });
    } catch(e) { fail('AAPL analysis end-to-end', e.message.slice(0,80)); }
    await ctx.close();
  }

  // ── 3. Market Grid — page loads + rows populated ─────────────────────────
  {
    const { ctx, page, errors, notFound } = await openPage(browser);
    try {
      await nav(page, '/market-grid');
      await waitTds(page, 20, 20000);
      const body = await page.locator('body').innerText();
      const hasPrices = /\$[\d,]+\.\d{2}|\d{2,}\.\d{2}/.test(body);
      const ce = corsErrors(errors);
      const nf = critical404s(notFound);
      if (ce.length) fail('Market Grid', 'CORS: ' + ce[0].slice(0,80));
      else if (nf.length) fail('Market Grid', '404: ' + nf[0].slice(0,80));
      else if (!hasPrices) fail('Market Grid', 'no price data in table');
      else pass('Market Grid', 'data loaded, no errors');
      await page.screenshot({ path: 'scripts/ss_market_grid.png' });
    } catch(e) { fail('Market Grid', e.message.slice(0,80)); }
    await ctx.close();
  }

  // ── 4. Momentum Sectors ──────────────────────────────────────────────────
  {
    const { ctx, page, errors } = await openPage(browser);
    try {
      await nav(page, '/momentum');
      // Wait for actual data text — skeleton rows have td elements but no text content
      // "N stocks across" only appears once the API response populates the table
      await page.waitForFunction(
        () => /\d+ stocks across/i.test(document.body.innerText) &&
              !/^0 stocks/.test(document.body.innerText.match(/\d+ stocks across[^]*/)?.[0] || ''),
        null,
        { timeout: 35000 }
      );
      const body = await page.locator('body').innerText();
      const hasSectors = /Technology|Healthcare|Energy|Financ|Consumer|Industrial/i.test(body);
      const ce = corsErrors(errors);
      if (ce.length) fail('Momentum Sectors', 'CORS: ' + ce[0].slice(0,80));
      else if (!hasSectors) fail('Momentum Sectors', 'sector names missing after data loaded');
      else pass('Momentum Sectors', 'data loaded');
      await page.screenshot({ path: 'scripts/ss_momentum.png' });
    } catch(e) { fail('Momentum Sectors', e.message.slice(0,80)); }
    await ctx.close();
  }

  // ── 5–13. Remaining pages (load + no CORS) ───────────────────────────────
  const pages = [
    ['/sector-heat', 'Sector Heat'],
    ['/earnings',    'Earnings'],
    ['/compare',     'Compare'],
    ['/correlation', 'Correlation'],
    ['/portfolio',   'Portfolio'],
    ['/history',     'Analysis History'],
    ['/watchlists',  'Watchlists'],
    ['/alerts',      'Alerts'],
    ['/logs',        'Logs'],
    ['/settings',    'Settings'],
    ['/keys',        'API Keys'],
  ];

  for (const [path, name] of pages) {
    const { ctx, page, errors, notFound } = await openPage(browser);
    try {
      const resp = await nav(page, path);
      await page.waitForTimeout(2000);
      const ce = corsErrors(errors);
      const nf = critical404s(notFound);
      if (resp.status() !== 200) fail(name, `HTTP ${resp.status()}`);
      else if (ce.length) fail(name + ' — CORS', ce[0].slice(0,80));
      else if (nf.length) fail(name + ' — 404', nf[0].slice(0,80));
      else pass(name, `HTTP ${resp.status()}`);
      await page.screenshot({ path: `scripts/ss_${path.replace('/', '')}.png` });
    } catch(e) { fail(name, e.message.slice(0,80)); }
    await ctx.close();
  }

  // ── 14. Correlation — enter two symbols and compare ───────────────────────
  {
    const { ctx, page, errors } = await openPage(browser);
    try {
      await nav(page, '/correlation');
      await page.waitForTimeout(1500);
      const inputs = await page.locator('input[type="text"], input:not([type])').all();
      if (inputs.length >= 2) {
        await inputs[0].fill('AAPL');
        await inputs[1].fill('MSFT');
        const btn = page.locator('button').filter({ hasText: /compare|correlat|run|submit/i }).first();
        if (await btn.count()) { await btn.click(); await page.waitForTimeout(5000); }
      }
      const ce = corsErrors(errors);
      if (ce.length) fail('Correlation — submit', 'CORS: ' + ce[0].slice(0,80));
      else pass('Correlation — AAPL vs MSFT submit', 'no CORS errors');
      await page.screenshot({ path: 'scripts/ss_correlation_result.png' });
    } catch(e) { fail('Correlation — submit', e.message.slice(0,80)); }
    await ctx.close();
  }

  // ── 15. Compare — enter two tickers ──────────────────────────────────────
  {
    const { ctx, page, errors } = await openPage(browser);
    try {
      await nav(page, '/compare');
      await page.waitForTimeout(1500);
      const inputs = await page.locator('input').all();
      if (inputs.length >= 2) {
        await inputs[0].fill('AAPL');
        await inputs[1].fill('GOOGL');
        const btn = page.locator('button').filter({ hasText: /compare|run|submit/i }).first();
        if (await btn.count()) { await btn.click(); await page.waitForTimeout(5000); }
      }
      const ce = corsErrors(errors);
      if (ce.length) fail('Compare — submit', 'CORS: ' + ce[0].slice(0,80));
      else pass('Compare — AAPL vs GOOGL submit', 'no CORS errors');
      await page.screenshot({ path: 'scripts/ss_compare_result.png' });
    } catch(e) { fail('Compare — submit', e.message.slice(0,80)); }
    await ctx.close();
  }

  // ── 16. API health check via Ingress ─────────────────────────────────────
  {
    const { ctx, page } = await openPage(browser);
    try {
      const resp = await page.goto(API + '/healthz', { waitUntil: 'domcontentloaded', timeout: 10000 });
      const body = await page.locator('body').innerText();
      if (resp.status() === 200 && body.includes('"ok"')) pass('API /healthz via Ingress');
      else fail('API /healthz via Ingress', `${resp.status()} ${body.slice(0,40)}`);
    } catch(e) { fail('API /healthz via Ingress', e.message.slice(0,80)); }
    await ctx.close();
  }

  await browser.close();

  // ── Print summary ─────────────────────────────────────────────────────────
  console.log('\n=== Results ===\n');
  for (const r of results) {
    const d = r.detail ? `  →  ${r.detail}` : '';
    console.log(`${r.ok ? '✅' : '❌'}  ${r.name}${d}`);
  }
  const p = results.filter(r => r.ok).length;
  const f = results.filter(r => !r.ok);
  console.log(`\n${p}/${results.length} checks passed`);
  if (f.length) { console.log('\nFailed:'); f.forEach(r => console.log(`  ❌ ${r.name}: ${r.detail}`)); }
}

main().catch(e => { console.error(e); process.exit(1); });
