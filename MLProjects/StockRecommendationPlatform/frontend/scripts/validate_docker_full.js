const { chromium } = require('@playwright/test');

const BASE     = 'http://localhost:3010';
const API_DIRECT = 'http://localhost:8010';
const API_NGINX  = 'http://api.stockresearch.local:8080';

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
    if (r.status() >= 400 && (r.url().includes('localhost') || r.url().includes('stockresearch.local')))
      notFound.push(`${r.status()} ${r.url()}`);
  });
  return { ctx, page, errors, notFound };
}

async function nav(page, path) {
  return page.goto(BASE + path, { waitUntil: 'domcontentloaded', timeout: 15000 });
}

async function waitText(page, text, timeout = 10000) {
  await page.waitForFunction(t => document.body.innerText.includes(t), text, { timeout });
}

async function main() {
  const browser = await chromium.launch({ channel: 'msedge', headless: false });
  console.log('=== Full Docker UI Validation ===');
  console.log('  Frontend : http://localhost:3010');
  console.log('  API nginx: http://api.stockresearch.local:8080\n');

  // ── 1. Home page ───────────────────────────────────────────────────────────
  {
    const { ctx, page, errors } = await openPage(browser);
    try {
      const resp = await nav(page, '/');
      await waitText(page, 'Analyze Symbol');
      const ce = corsErrors(errors);
      if (ce.length) fail('Home page loads', ce[0].slice(0, 80));
      else pass('Home page loads', `HTTP ${resp.status()}`);
      await page.screenshot({ path: 'scripts/docker_ss_home.png' });
    } catch (e) { fail('Home page loads', e.message.slice(0, 80)); }
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
      if (ce.length) fail('AAPL analysis end-to-end', 'CORS: ' + ce[0].slice(0, 80));
      else pass('AAPL analysis end-to-end', `Verdict: ${verdict.toUpperCase()}`);
      await page.screenshot({ path: 'scripts/docker_ss_analysis.png' });
    } catch (e) { fail('AAPL analysis end-to-end', e.message.slice(0, 80)); }
    await ctx.close();
  }

  // ── 3. Market Grid — rows populated, no errors ────────────────────────────
  {
    const { ctx, page, errors, notFound } = await openPage(browser);
    try {
      await nav(page, '/market-grid');
      await page.waitForFunction(
        () => document.querySelectorAll('td').length >= 20,
        null,
        { timeout: 20000 }
      );
      const body = await page.locator('body').innerText();
      const hasPrices = /\$[\d,]+\.\d{2}|\d{2,}\.\d{2}/.test(body);
      const ce = corsErrors(errors);
      const nf = critical404s(notFound);
      if (ce.length) fail('Market Grid', 'CORS: ' + ce[0].slice(0, 80));
      else if (nf.length) fail('Market Grid', '404: ' + nf[0].slice(0, 80));
      else if (!hasPrices) fail('Market Grid', 'no price data in table');
      else pass('Market Grid', 'data loaded, no errors');
      await page.screenshot({ path: 'scripts/docker_ss_market_grid.png' });
    } catch (e) { fail('Market Grid', e.message.slice(0, 80)); }
    await ctx.close();
  }

  // ── 4. Momentum Sectors ──────────────────────────────────────────────────
  {
    const { ctx, page, errors } = await openPage(browser);
    try {
      await nav(page, '/momentum');
      await page.waitForFunction(
        () => /\d+ stocks across/i.test(document.body.innerText) &&
              !/^0 stocks/.test((document.body.innerText.match(/\d+ stocks across[^]*/)||[''])[0]),
        null,
        { timeout: 35000 }
      );
      const body = await page.locator('body').innerText();
      const hasSectors = /Technology|Healthcare|Energy|Financ|Consumer|Industrial/i.test(body);
      const ce = corsErrors(errors);
      if (ce.length) fail('Momentum Sectors', 'CORS: ' + ce[0].slice(0, 80));
      else if (!hasSectors) fail('Momentum Sectors', 'sector names missing');
      else pass('Momentum Sectors', 'data loaded');
      await page.screenshot({ path: 'scripts/docker_ss_momentum.png' });
    } catch (e) { fail('Momentum Sectors', e.message.slice(0, 80)); }
    await ctx.close();
  }

  // ── 5–15. Remaining pages ─────────────────────────────────────────────────
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
      else if (ce.length) fail(name + ' — CORS', ce[0].slice(0, 80));
      else if (nf.length) fail(name + ' — 404', nf[0].slice(0, 80));
      else pass(name, `HTTP ${resp.status()}`);
      await page.screenshot({ path: `scripts/docker_ss_${path.replace('/', '')}.png` });
    } catch (e) { fail(name, e.message.slice(0, 80)); }
    await ctx.close();
  }

  // ── 16. Correlation — submit AAPL vs MSFT ────────────────────────────────
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
      if (ce.length) fail('Correlation — submit', 'CORS: ' + ce[0].slice(0, 80));
      else pass('Correlation — AAPL vs MSFT submit', 'no CORS errors');
      await page.screenshot({ path: 'scripts/docker_ss_correlation_result.png' });
    } catch (e) { fail('Correlation — submit', e.message.slice(0, 80)); }
    await ctx.close();
  }

  // ── 17. Compare — submit AAPL vs GOOGL ───────────────────────────────────
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
      if (ce.length) fail('Compare — submit', 'CORS: ' + ce[0].slice(0, 80));
      else pass('Compare — AAPL vs GOOGL submit', 'no CORS errors');
      await page.screenshot({ path: 'scripts/docker_ss_compare_result.png' });
    } catch (e) { fail('Compare — submit', e.message.slice(0, 80)); }
    await ctx.close();
  }

  // ── 18. API health — direct port ─────────────────────────────────────────
  {
    const { ctx, page } = await openPage(browser);
    try {
      const resp = await page.goto(API_DIRECT + '/healthz', { waitUntil: 'domcontentloaded', timeout: 10000 });
      const body = await page.locator('body').innerText();
      if (resp.status() === 200 && body.includes('"ok"')) pass('API /healthz (direct :8010)');
      else fail('API /healthz (direct :8010)', `${resp.status()} ${body.slice(0, 40)}`);
    } catch (e) { fail('API /healthz (direct :8010)', e.message.slice(0, 80)); }
    await ctx.close();
  }

  // ── 19. API health — via nginx (api.stockresearch.local:8080) ────────────
  {
    const { ctx, page } = await openPage(browser);
    try {
      const resp = await page.goto(API_NGINX + '/healthz', { waitUntil: 'domcontentloaded', timeout: 10000 });
      const body = await page.locator('body').innerText();
      if (resp.status() === 200 && body.includes('"ok"')) pass('API /healthz (nginx api.stockresearch.local:8080)');
      else fail('API /healthz (nginx api.stockresearch.local:8080)', `${resp.status()} ${body.slice(0, 40)}`);
    } catch (e) { fail('API /healthz (nginx api.stockresearch.local:8080)', e.message.slice(0, 80)); }
    await ctx.close();
  }

  await browser.close();

  // ── Summary ───────────────────────────────────────────────────────────────
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
