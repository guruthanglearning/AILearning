const { chromium } = require('@playwright/test');

const BASE = 'http://localhost:3001';
const API  = 'http://localhost:8024';
const results = [];

function pass(name, detail = '') { results.push({ ok: true,  name, detail }); console.log(`  ✅ ${name}${detail ? ' → ' + detail : ''}`); }
function fail(name, detail = '') { results.push({ ok: false, name, detail }); console.log(`  ❌ ${name}${detail ? ' → ' + detail : ''}`); }
function warn(name, detail = '') { results.push({ ok: null,  name, detail }); console.log(`  ⚠️  ${name}${detail ? ' → ' + detail : ''}`); }

async function openPage(browser) {
  const ctx = await browser.newContext({ viewport: { width: 1440, height: 900 } });
  const page = await ctx.newPage();
  const errors = [], notFound = [];
  page.on('console', m => { if (m.type() === 'error') errors.push(m.text()); });
  page.on('response', r => {
    if (r.status() >= 400 && r.url().includes('localhost'))
      notFound.push(`${r.status()} ${r.url()}`);
  });
  return { ctx, page, errors, notFound };
}

async function nav(page, path, timeout = 15000) {
  return page.goto(BASE + path, { waitUntil: 'domcontentloaded', timeout });
}

function corsErrors(e) { return e.filter(x => x.includes('CORS') || x.includes('Access-Control')); }
function critical404s(n) { return n.filter(u => !u.includes('favicon') && !u.includes('.ico')); }

async function main() {
  const browser = await chromium.launch({ channel: 'msedge', headless: true });
  console.log('=== Deep Page Content Validation — Local Dev ===');
  console.log(`  Frontend : ${BASE}`);
  console.log(`  Backend  : ${API}\n`);

  // ── 1. Home ────────────────────────────────────────────────────────────────
  console.log('\n[1] Home / Analysis page');
  {
    const { ctx, page, errors } = await openPage(browser);
    try {
      await nav(page, '/');
      await page.waitForFunction(() => document.body.innerText.includes('Analyze Symbol'), null, { timeout: 10000 });
      const body = await page.locator('body').innerText();
      if (body.includes('Analyze Symbol')) pass('Home — analysis form visible');
      else fail('Home — analysis form visible');
      if (/not investment advice/i.test(body)) pass('Home — disclaimer present');
      else warn('Home — disclaimer present');
      if (corsErrors(errors).length) fail('Home — no CORS errors', corsErrors(errors)[0].slice(0,80));
      else pass('Home — no CORS errors');
    } catch (e) { fail('Home page', e.message.slice(0,80)); }
    await ctx.close();
  }

  // ── 2. Market Grid ─────────────────────────────────────────────────────────
  console.log('\n[2] Market Grid page');
  {
    const { ctx, page, errors, notFound } = await openPage(browser);
    try {
      await nav(page, '/market-grid');
      await page.waitForFunction(
        () => /[\d.]+T|[\d.]+B/.test(document.querySelector('tbody')?.innerText || ''),
        null, { timeout: 30000 }
      );
      await page.waitForTimeout(1000);
      const stats = await page.evaluate(() => {
        const rows = Array.from(document.querySelectorAll('tbody tr'));
        let priceRows = 0;
        rows.forEach(r => { if (/\d{2,}\.\d{2}/.test(r.innerText)) priceRows++; });
        return { rowCount: rows.length, colCount: rows[0]?.querySelectorAll('td').length || 0, priceRows };
      });
      if (stats.rowCount >= 30) pass('Market Grid — rows loaded', `${stats.rowCount} rows, ${stats.colCount} cols`);
      else fail('Market Grid — rows loaded', `only ${stats.rowCount} rows`);
      if (stats.priceRows >= 20) pass('Market Grid — price data present', `${stats.priceRows} rows with prices`);
      else fail('Market Grid — price data present', `only ${stats.priceRows}`);
      if (corsErrors(errors).length) fail('Market Grid — no CORS errors', corsErrors(errors)[0].slice(0,80));
      else pass('Market Grid — no CORS errors');
      if (critical404s(notFound).length) fail('Market Grid — no 404s', critical404s(notFound)[0].slice(0,60));
      else pass('Market Grid — no 404s');
    } catch (e) { fail('Market Grid', e.message.slice(0,80)); }
    await ctx.close();
  }

  // ── 3. Momentum ────────────────────────────────────────────────────────────
  console.log('\n[3] Momentum page');
  {
    const { ctx, page, errors } = await openPage(browser);
    try {
      await nav(page, '/momentum');
      await page.waitForFunction(
        () => /[1-9]\d* stocks across/i.test(document.body.innerText),
        null, { timeout: 35000 }
      );
      const body = await page.locator('body').innerText();
      const stocksMatch = body.match(/(\d+) stocks across/i);
      const stockCount = stocksMatch ? parseInt(stocksMatch[1]) : 0;
      if (stockCount >= 50) pass('Momentum — stock count', `${stockCount} stocks`);
      else fail('Momentum — stock count', `only ${stockCount}`);
      if (/Technology|Healthcare|Energy|Financ|Consumer/i.test(body)) pass('Momentum — sector names present');
      else fail('Momentum — sector names present');
      if (/\d+\.\d+/.test(body)) pass('Momentum — momentum scores present');
      else fail('Momentum — momentum scores present');
      if (corsErrors(errors).length) fail('Momentum — no CORS errors');
      else pass('Momentum — no CORS errors');
    } catch (e) { fail('Momentum', e.message.slice(0,80)); }
    await ctx.close();
  }

  // ── 4. Sector Heat ─────────────────────────────────────────────────────────
  console.log('\n[4] Sector Heat page');
  {
    const { ctx, page, errors } = await openPage(browser);
    try {
      await nav(page, '/sector-heat');
      await page.waitForTimeout(5000);
      const body = await page.locator('body').innerText();
      if (/Technology|Healthcare|Energy|Financ|Consumer/i.test(body)) pass('Sector Heat — sector names present');
      else fail('Sector Heat — sector names present');
      if (/[+-]\d+\.\d+%/.test(body)) pass('Sector Heat — change percentages present');
      else warn('Sector Heat — change percentages present', 'no % values found');
      if (corsErrors(errors).length) fail('Sector Heat — no CORS errors');
      else pass('Sector Heat — no CORS errors');
    } catch (e) { fail('Sector Heat', e.message.slice(0,80)); }
    await ctx.close();
  }

  // ── 5. Earnings ────────────────────────────────────────────────────────────
  console.log('\n[5] Earnings page');
  {
    const { ctx, page, errors } = await openPage(browser);
    try {
      await nav(page, '/earnings');
      await page.waitForTimeout(2000);
      await page.waitForFunction(
        () => document.body.innerText.includes('Upcoming Earnings') ||
              (document.body.innerText.includes('No earnings') && !document.body.innerText.includes('Loading')),
        null, { timeout: 25000 }
      );
      const body = await page.locator('body').innerText();
      const cards = await page.locator('.grid > div').count();
      if (body.includes('Upcoming Earnings') && cards >= 5) pass('Earnings — upcoming dates loaded', `${cards} company cards`);
      else if (body.includes('Upcoming Earnings')) warn('Earnings — upcoming dates loaded', `only ${cards} cards`);
      else fail('Earnings — upcoming dates loaded');
      if (/NVDA|MSFT|AAPL|GOOG|TSLA/i.test(body)) pass('Earnings — tracked symbols present');
      else warn('Earnings — tracked symbols present');
      if (corsErrors(errors).length) fail('Earnings — no CORS errors');
      else pass('Earnings — no CORS errors');
    } catch (e) { fail('Earnings', e.message.slice(0,80)); }
    await ctx.close();
  }

  // ── 6. Compare ─────────────────────────────────────────────────────────────
  console.log('\n[6] Compare page');
  {
    const { ctx, page, errors } = await openPage(browser);
    try {
      await nav(page, '/compare');
      await page.waitForTimeout(2000);
      const body = await page.locator('body').innerText();
      if (await page.locator('input').count() >= 1) pass('Compare — symbol input present');
      else fail('Compare — symbol input present');
      if (/compare|multi.symbol/i.test(body)) pass('Compare — page title present');
      else warn('Compare — page title present');
      const symbolInput = page.locator('input').first();
      if (await symbolInput.count()) {
        await symbolInput.fill('AAPL');
        await symbolInput.press('Enter');
        await page.waitForTimeout(500);
        await symbolInput.fill('GOOGL');
        await symbolInput.press('Enter');
        await page.waitForTimeout(8000);
        const bodyAfter = await page.locator('body').innerText();
        if (/AAPL|GOOGL|normaliz|price|change/i.test(bodyAfter)) pass('Compare — AAPL+GOOGL result loaded');
        else warn('Compare — AAPL+GOOGL result loaded', 'no data visible');
      }
      if (corsErrors(errors).length) fail('Compare — no CORS errors', corsErrors(errors)[0].slice(0,80));
      else pass('Compare — no CORS errors');
    } catch (e) { fail('Compare', e.message.slice(0,80)); }
    await ctx.close();
  }

  // ── 7. Correlation ─────────────────────────────────────────────────────────
  console.log('\n[7] Correlation page');
  {
    const { ctx, page, errors } = await openPage(browser);
    try {
      await nav(page, '/correlation');
      await page.waitForTimeout(2000);
      const inputs = await page.locator('input').all();
      if (inputs.length >= 1) pass('Correlation — symbol inputs present', `${inputs.length} inputs`);
      else fail('Correlation — symbol inputs present');
      if (inputs.length >= 2) {
        await inputs[0].fill('AAPL');
        await inputs[1].fill('MSFT');
        const btn = page.locator('button').filter({ hasText: /compare|correlat|run|submit/i }).first();
        if (await btn.count()) {
          await btn.click();
          await page.waitForTimeout(8000);
          const bodyAfter = await page.locator('body').innerText();
          if (/correlation|AAPL|MSFT|\d\.\d{2}/i.test(bodyAfter)) pass('Correlation — matrix result loaded');
          else warn('Correlation — matrix result loaded', 'no matrix visible');
        }
      }
      if (corsErrors(errors).length) fail('Correlation — no CORS errors', corsErrors(errors)[0].slice(0,80));
      else pass('Correlation — no CORS errors');
    } catch (e) { fail('Correlation', e.message.slice(0,80)); }
    await ctx.close();
  }

  // ── 8–14. Remaining pages ──────────────────────────────────────────────────
  const pages = [
    ['/portfolio',  'Portfolio',  /portfolio|position|holding|add/i],
    ['/history',    'History',    /history|analysis|symbol|recent|no.analysis/i],
    ['/watchlists', 'Watchlists', /watchlist|create|new|symbol|no watchlist/i],
    ['/alerts',     'Alerts',     /alert|create|price|condition|trigger|no alert/i],
    ['/logs',       'Logs',       /log|error|event|timestamp|no error|clear/i],
    ['/settings',   'Settings',   /setting|preference|portfolio|risk|model|save/i],
    ['/keys',       'API Keys',   /api key|create|generate|key|token|no key/i],
  ];

  for (let pi = 0; pi < pages.length; pi++) {
    const [path, name, pattern] = pages[pi];
    console.log(`\n[${pi + 8}] ${name} page`);
    const { ctx, page, errors } = await openPage(browser);
    try {
      await nav(page, path);
      await page.waitForTimeout(3000);
      const body = await page.locator('body').innerText();
      if (pattern.test(body)) pass(`${name} — page content present`);
      else fail(`${name} — page content present`);
      if (corsErrors(errors).length) fail(`${name} — no CORS errors`, corsErrors(errors)[0].slice(0,80));
      else pass(`${name} — no CORS errors`);
    } catch (e) { fail(name, e.message.slice(0,80)); }
    await ctx.close();
  }

  // ── API health ─────────────────────────────────────────────────────────────
  console.log('\n[15] API health check');
  {
    const { ctx, page } = await openPage(browser);
    try {
      const resp = await page.goto(API + '/healthz', { waitUntil: 'domcontentloaded', timeout: 10000 });
      const body = await page.locator('body').innerText();
      if (resp.status() === 200 && body.includes('"ok"')) pass('API /healthz (local :8024)');
      else fail('API /healthz (local :8024)', `${resp.status()} ${body.slice(0,40)}`);
    } catch (e) { fail('API /healthz', e.message.slice(0,80)); }
    await ctx.close();
  }

  await browser.close();

  // ── Summary ────────────────────────────────────────────────────────────────
  const passed = results.filter(r => r.ok === true).length;
  const warned = results.filter(r => r.ok === null).length;
  const failed = results.filter(r => r.ok === false).length;
  console.log('\n══════════════════════════════════════════');
  console.log(`SUMMARY: ${passed} passed  |  ${warned} warnings  |  ${failed} failed  (total ${results.length})`);
  console.log('══════════════════════════════════════════');
  if (failed > 0) {
    console.log('\nFailed:');
    results.filter(r => r.ok === false).forEach(r => console.log(`  ❌ ${r.name}: ${r.detail}`));
  }
  if (warned > 0) {
    console.log('\nWarnings:');
    results.filter(r => r.ok === null).forEach(r => console.log(`  ⚠️  ${r.name}: ${r.detail}`));
  }
}

main().catch(e => { console.error(e); process.exit(1); });
