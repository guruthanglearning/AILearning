const { chromium } = require('@playwright/test');

const BASE = 'http://localhost:3010';
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
    if (r.status() >= 400 && (r.url().includes('localhost') || r.url().includes('stockresearch.local')))
      notFound.push(`${r.status()} ${r.url()}`);
  });
  return { ctx, page, errors, notFound };
}

async function nav(page, path, timeout = 15000) {
  return page.goto(BASE + path, { waitUntil: 'domcontentloaded', timeout });
}

function corsErrors(errors) { return errors.filter(e => e.includes('CORS') || e.includes('Access-Control')); }
function critical404s(notFound) { return notFound.filter(u => !u.includes('favicon') && !u.includes('.ico')); }

async function main() {
  const browser = await chromium.launch({ channel: 'msedge', headless: true });
  console.log('=== Deep Page Content Validation — Docker UI ===\n');

  // ── 1. Home / Analysis ─────────────────────────────────────────────────────
  console.log('\n[1] Home / Analysis page');
  {
    const { ctx, page, errors } = await openPage(browser);
    try {
      await nav(page, '/');
      await page.waitForFunction(() => document.body.innerText.includes('Analyze Symbol'), null, { timeout: 10000 });
      const body = await page.locator('body').innerText();
      const hasForm = body.includes('Analyze Symbol');
      const hasDisclaimer = /not investment advice/i.test(body);
      if (!hasForm) fail('Home — analysis form visible', 'form not found');
      else pass('Home — analysis form visible');
      if (!hasDisclaimer) warn('Home — disclaimer present', 'not found');
      else pass('Home — disclaimer present');
      if (corsErrors(errors).length) fail('Home — no CORS errors', corsErrors(errors)[0].slice(0,80));
      else pass('Home — no CORS errors');
    } catch (e) { fail('Home page', e.message.slice(0, 80)); }
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
        const colCount = rows[0]?.querySelectorAll('td').length || 0;
        let priceRows = 0;
        rows.forEach(r => {
          const t = r.innerText;
          if (/\d{2,}\.\d{2}/.test(t)) priceRows++;
        });
        return { rowCount: rows.length, colCount, priceRows };
      });
      if (stats.rowCount >= 30) pass(`Market Grid — rows loaded`, `${stats.rowCount} rows, ${stats.colCount} cols`);
      else fail('Market Grid — rows loaded', `only ${stats.rowCount} rows`);
      if (stats.priceRows >= 20) pass('Market Grid — price data present', `${stats.priceRows} rows with prices`);
      else fail('Market Grid — price data present', `only ${stats.priceRows} rows with prices`);
      if (corsErrors(errors).length) fail('Market Grid — no CORS errors', corsErrors(errors)[0].slice(0,80));
      else pass('Market Grid — no CORS errors');
      if (critical404s(notFound).length) fail('Market Grid — no 404s', critical404s(notFound)[0].slice(0,60));
      else pass('Market Grid — no 404s');
    } catch (e) { fail('Market Grid', e.message.slice(0, 80)); }
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
      const hasSectors = /Technology|Healthcare|Energy|Financ|Consumer/i.test(body);
      const hasScores = /\d+\.\d+/.test(body);
      if (stockCount >= 50) pass('Momentum — stock count', `${stockCount} stocks`);
      else fail('Momentum — stock count', `only ${stockCount} stocks`);
      if (hasSectors) pass('Momentum — sector names present');
      else fail('Momentum — sector names present');
      if (hasScores) pass('Momentum — momentum scores present');
      else fail('Momentum — momentum scores present');
      if (corsErrors(errors).length) fail('Momentum — no CORS errors');
      else pass('Momentum — no CORS errors');
    } catch (e) { fail('Momentum', e.message.slice(0, 80)); }
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
      const hasSectors = /Technology|Healthcare|Energy|Financ|Consumer/i.test(body);
      const hasNumbers = /[+-]\d+\.\d+%/.test(body);
      if (hasSectors) pass('Sector Heat — sector names present');
      else fail('Sector Heat — sector names present');
      if (hasNumbers) pass('Sector Heat — change percentages present');
      else warn('Sector Heat — change percentages present', 'no % values found');
      if (corsErrors(errors).length) fail('Sector Heat — no CORS errors');
      else pass('Sector Heat — no CORS errors');
    } catch (e) { fail('Sector Heat', e.message.slice(0, 80)); }
    await ctx.close();
  }

  // ── 5. Earnings ────────────────────────────────────────────────────────────
  console.log('\n[5] Earnings page');
  {
    const { ctx, page, errors } = await openPage(browser);
    try {
      await nav(page, '/earnings');
      await page.waitForFunction(
        () => document.body.innerText.includes('Upcoming Earnings') || document.body.innerText.includes('No earnings'),
        null, { timeout: 20000 }
      );
      const body = await page.locator('body').innerText();
      const hasUpcoming = body.includes('Upcoming Earnings');
      const cards = await page.locator('.grid > div').count();
      if (hasUpcoming && cards >= 5) pass('Earnings — upcoming dates loaded', `${cards} company cards`);
      else if (hasUpcoming) warn('Earnings — upcoming dates loaded', `only ${cards} cards`);
      else fail('Earnings — upcoming dates loaded', 'no upcoming section');
      const hasSymbols = /NVDA|MSFT|AAPL|GOOG|TSLA/i.test(body);
      if (hasSymbols) pass('Earnings — tracked symbols present');
      else warn('Earnings — tracked symbols present', 'common symbols not found');
      if (corsErrors(errors).length) fail('Earnings — no CORS errors');
      else pass('Earnings — no CORS errors');
    } catch (e) { fail('Earnings', e.message.slice(0, 80)); }
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
      // Compare uses a single tag-input (type symbol + Enter to add up to 6)
      const hasInput = await page.locator('input').count() >= 1;
      const hasTitle = /compare|multi.symbol/i.test(body);
      if (hasInput) pass('Compare — symbol input present');
      else fail('Compare — symbol input present');
      if (hasTitle) pass('Compare — page title present');
      else warn('Compare — page title present', 'no compare label found');
      const symbolInput = page.locator('input').first();
      if (await symbolInput.count()) {
        await symbolInput.fill('AAPL');
        await symbolInput.press('Enter');
        await page.waitForTimeout(500);
        await symbolInput.fill('GOOGL');
        await symbolInput.press('Enter');
        await page.waitForTimeout(8000);
        const bodyAfter = await page.locator('body').innerText();
        const hasData = /AAPL|GOOGL|normaliz|price|change/i.test(bodyAfter);
        if (hasData) pass('Compare — AAPL+GOOGL result loaded');
        else warn('Compare — AAPL+GOOGL result loaded', 'no chart/data visible');
      }
      if (corsErrors(errors).length) fail('Compare — no CORS errors', corsErrors(errors)[0].slice(0,80));
      else pass('Compare — no CORS errors');
    } catch (e) { fail('Compare', e.message.slice(0, 80)); }
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
          const hasMatrix = /correlation|AAPL|MSFT|\d\.\d{2}/i.test(bodyAfter);
          if (hasMatrix) pass('Correlation — matrix result loaded');
          else warn('Correlation — matrix result loaded', 'no matrix data visible');
        }
      }
      if (corsErrors(errors).length) fail('Correlation — no CORS errors', corsErrors(errors)[0].slice(0,80));
      else pass('Correlation — no CORS errors');
    } catch (e) { fail('Correlation', e.message.slice(0, 80)); }
    await ctx.close();
  }

  // ── 8. Portfolio ───────────────────────────────────────────────────────────
  console.log('\n[8] Portfolio page');
  {
    const { ctx, page, errors } = await openPage(browser);
    try {
      await nav(page, '/portfolio');
      await page.waitForTimeout(3000);
      const body = await page.locator('body').innerText();
      const hasPortfolioContent = /portfolio|position|holding|symbol|add/i.test(body);
      if (hasPortfolioContent) pass('Portfolio — page content present');
      else fail('Portfolio — page content present');
      if (corsErrors(errors).length) fail('Portfolio — no CORS errors', corsErrors(errors)[0].slice(0,80));
      else pass('Portfolio — no CORS errors');
    } catch (e) { fail('Portfolio', e.message.slice(0, 80)); }
    await ctx.close();
  }

  // ── 9. History ─────────────────────────────────────────────────────────────
  console.log('\n[9] Analysis History page');
  {
    const { ctx, page, errors } = await openPage(browser);
    try {
      await nav(page, '/history');
      await page.waitForTimeout(3000);
      const body = await page.locator('body').innerText();
      const hasHistoryContent = /history|analysis|symbol|recent|no.analysis/i.test(body);
      if (hasHistoryContent) pass('History — page content present');
      else fail('History — page content present');
      const hasAAPL = /AAPL/i.test(body);
      if (hasAAPL) pass('History — recent AAPL analysis present');
      else warn('History — recent AAPL analysis present', 'AAPL not in history (may not have run yet)');
      if (corsErrors(errors).length) fail('History — no CORS errors', corsErrors(errors)[0].slice(0,80));
      else pass('History — no CORS errors');
    } catch (e) { fail('History', e.message.slice(0, 80)); }
    await ctx.close();
  }

  // ── 10. Watchlists ─────────────────────────────────────────────────────────
  console.log('\n[10] Watchlists page');
  {
    const { ctx, page, errors } = await openPage(browser);
    try {
      await nav(page, '/watchlists');
      await page.waitForTimeout(3000);
      const body = await page.locator('body').innerText();
      const hasContent = /watchlist|create|new|symbol|no watchlist/i.test(body);
      if (hasContent) pass('Watchlists — page content present');
      else fail('Watchlists — page content present');
      if (corsErrors(errors).length) fail('Watchlists — no CORS errors', corsErrors(errors)[0].slice(0,80));
      else pass('Watchlists — no CORS errors');
    } catch (e) { fail('Watchlists', e.message.slice(0, 80)); }
    await ctx.close();
  }

  // ── 11. Alerts ─────────────────────────────────────────────────────────────
  console.log('\n[11] Alerts page');
  {
    const { ctx, page, errors } = await openPage(browser);
    try {
      await nav(page, '/alerts');
      await page.waitForTimeout(3000);
      const body = await page.locator('body').innerText();
      const hasContent = /alert|create|price|condition|trigger|no alert/i.test(body);
      if (hasContent) pass('Alerts — page content present');
      else fail('Alerts — page content present');
      if (corsErrors(errors).length) fail('Alerts — no CORS errors', corsErrors(errors)[0].slice(0,80));
      else pass('Alerts — no CORS errors');
    } catch (e) { fail('Alerts', e.message.slice(0, 80)); }
    await ctx.close();
  }

  // ── 12. Logs ───────────────────────────────────────────────────────────────
  console.log('\n[12] Logs page');
  {
    const { ctx, page, errors } = await openPage(browser);
    try {
      await nav(page, '/logs');
      await page.waitForTimeout(3000);
      const body = await page.locator('body').innerText();
      const hasContent = /log|error|event|timestamp|no error|clear/i.test(body);
      if (hasContent) pass('Logs — page content present');
      else fail('Logs — page content present');
      if (corsErrors(errors).length) fail('Logs — no CORS errors', corsErrors(errors)[0].slice(0,80));
      else pass('Logs — no CORS errors');
    } catch (e) { fail('Logs', e.message.slice(0, 80)); }
    await ctx.close();
  }

  // ── 13. Settings ───────────────────────────────────────────────────────────
  console.log('\n[13] Settings page');
  {
    const { ctx, page, errors } = await openPage(browser);
    try {
      await nav(page, '/settings');
      await page.waitForTimeout(3000);
      const body = await page.locator('body').innerText();
      const hasContent = /setting|preference|portfolio|risk|model|save/i.test(body);
      if (hasContent) pass('Settings — page content present');
      else fail('Settings — page content present');
      if (corsErrors(errors).length) fail('Settings — no CORS errors', corsErrors(errors)[0].slice(0,80));
      else pass('Settings — no CORS errors');
    } catch (e) { fail('Settings', e.message.slice(0, 80)); }
    await ctx.close();
  }

  // ── 14. API Keys ───────────────────────────────────────────────────────────
  console.log('\n[14] API Keys page');
  {
    const { ctx, page, errors } = await openPage(browser);
    try {
      await nav(page, '/keys');
      await page.waitForTimeout(3000);
      const body = await page.locator('body').innerText();
      const hasContent = /api key|create|generate|key|token|no key/i.test(body);
      if (hasContent) pass('API Keys — page content present');
      else fail('API Keys — page content present');
      if (corsErrors(errors).length) fail('API Keys — no CORS errors', corsErrors(errors)[0].slice(0,80));
      else pass('API Keys — no CORS errors');
    } catch (e) { fail('API Keys', e.message.slice(0, 80)); }
    await ctx.close();
  }

  await browser.close();

  // ── Summary ────────────────────────────────────────────────────────────────
  const passed  = results.filter(r => r.ok === true).length;
  const warned  = results.filter(r => r.ok === null).length;
  const failed  = results.filter(r => r.ok === false).length;

  console.log('\n══════════════════════════════════════════');
  console.log(`SUMMARY: ${passed} passed  |  ${warned} warnings  |  ${failed} failed  (total ${results.length})`);
  console.log('══════════════════════════════════════════');

  if (failed > 0) {
    console.log('\nFailed checks:');
    results.filter(r => r.ok === false).forEach(r => console.log(`  ❌ ${r.name}: ${r.detail}`));
  }
  if (warned > 0) {
    console.log('\nWarnings:');
    results.filter(r => r.ok === null).forEach(r => console.log(`  ⚠️  ${r.name}: ${r.detail}`));
  }
}

main().catch(e => { console.error(e); process.exit(1); });
