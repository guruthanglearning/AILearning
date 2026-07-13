/**
 * Deep UI inspection — checks actual data completeness on every page.
 * Reports missing fields, blank columns, and API errors per page.
 */
const { chromium } = require('@playwright/test');

const BASE = 'http://localhost:3010';
const API  = 'http://localhost:8010';

const results = [];
function pass(name, detail = '')  { results.push({ ok: true,  name, detail }); console.log(`  ✅ ${name}${detail ? ' — ' + detail : ''}`); }
function warn(name, detail = '')  { results.push({ ok: 'warn', name, detail }); console.log(`  ⚠️  ${name}${detail ? ' — ' + detail : ''}`); }
function fail(name, detail = '')  { results.push({ ok: false, name, detail }); console.log(`  ❌ ${name}${detail ? ' — ' + detail : ''}`); }

async function openPage(browser) {
  const ctx  = await browser.newContext({ viewport: { width: 1440, height: 900 } });
  const page = await ctx.newPage();
  const errors = [], notFound = [];
  page.on('console', m => { if (m.type() === 'error') errors.push(m.text()); });
  page.on('response', r => {
    if (r.status() >= 400 && r.url().includes('localhost'))
      notFound.push(`${r.status()} ${r.url()}`);
  });
  return { ctx, page, errors, notFound };
}

async function nav(page, path, wait = 'networkidle') {
  return page.goto(BASE + path, { waitUntil: wait, timeout: 20000 });
}

// ─────────────────────────────────────────────────────────────────────────────
// Helpers
// ─────────────────────────────────────────────────────────────────────────────

function corsErrors(errors)   { return errors.filter(e => e.includes('CORS') || e.includes('Access-Control')); }
function critical404s(nf)     { return nf.filter(u => !u.includes('favicon') && !u.includes('.ico') && !u.includes('_next/static')); }

// Count cells in a column that are NOT "--" or empty
async function countFilledCells(page, colIndex) {
  return page.evaluate((ci) => {
    const rows = document.querySelectorAll('tbody tr');
    let filled = 0;
    rows.forEach(row => {
      const cell = row.querySelectorAll('td')[ci];
      if (!cell) return;
      const t = cell.innerText.trim();
      if (t && t !== '--' && t !== '—') filled++;
    });
    return filled;
  }, colIndex);
}

async function countTableRows(page) {
  return page.evaluate(() => document.querySelectorAll('tbody tr').length);
}

// Fetch raw API endpoint and inspect JSON
async function apiGet(page, path) {
  const resp = await page.goto(API + path, { waitUntil: 'domcontentloaded', timeout: 15000 });
  const text = await page.locator('body').innerText();
  try { return { status: resp.status(), data: JSON.parse(text) }; }
  catch { return { status: resp.status(), data: null, raw: text.slice(0, 200) }; }
}

// ─────────────────────────────────────────────────────────────────────────────
// 1. Backend API health
// ─────────────────────────────────────────────────────────────────────────────
async function checkApiHealth(browser) {
  console.log('\n── Backend API ──');
  const { ctx, page } = await openPage(browser);
  const r = await apiGet(page, '/healthz');
  r.status === 200 ? pass('GET /healthz', JSON.stringify(r.data)) : fail('GET /healthz', `${r.status}`);

  const q = await apiGet(page, '/api/v1/quotes?symbols=AAPL,MSFT,NVDA');
  if (q.status === 200 && Array.isArray(q.data) && q.data.length > 0) {
    const sample = q.data[0];
    const fields = ['symbol','last_price','change','market_cap','week_52_high','week_52_low','pre_mkt_price','post_mkt_price','earnings_date','shares_outstanding','exchange'];
    const missing = fields.filter(f => sample[f] == null);
    missing.length === 0
      ? pass('GET /api/v1/quotes (3 symbols)', `All key fields present on ${q.data.length} rows`)
      : warn('GET /api/v1/quotes — missing fields', missing.join(', '));
    // Log per-field values for AAPL
    const aapl = q.data.find(r => r.symbol === 'AAPL') || q.data[0];
    console.log(`     AAPL sample: last=${aapl.last_price} mktcap=${aapl.market_cap} 52h=${aapl.week_52_high} 52l=${aapl.week_52_low} src=${aapl.price_source}`);
  } else {
    fail('GET /api/v1/quotes', `${q.status} — ${q.raw ?? 'empty'}`);
  }

  await ctx.close();
}

// ─────────────────────────────────────────────────────────────────────────────
// 2. Market Grid — column-by-column data completeness
// ─────────────────────────────────────────────────────────────────────────────
async function checkMarketGrid(browser) {
  console.log('\n── Market Grid (/market-grid) ──');
  const { ctx, page, errors, notFound } = await openPage(browser);
  try {
    await nav(page, '/market-grid', 'domcontentloaded');
    // Wait for table rows to appear
    await page.waitForFunction(() => document.querySelectorAll('tbody tr').length >= 10, null, { timeout: 25000 });
    await page.waitForTimeout(3000); // let sparklines + data settle

    const totalRows = await countTableRows(page);
    pass('Market Grid loads', `${totalRows} rows`);

    // Inspect each visible column by index
    const colDefs = [
      { label: 'Symbol',            idx: 0,  required: true },
      { label: '30d Sparkline',      idx: 1,  required: false },
      { label: 'Open/Pre Price',     idx: 2,  required: false },
      { label: 'Open/Pre vs Prev',   idx: 3,  required: false },
      { label: 'Last Price',         idx: 4,  required: true },
      { label: 'Change',             idx: 5,  required: true },
      { label: 'AH/Post Price',      idx: 6,  required: false },
      { label: 'AH/Post vs Close',   idx: 7,  required: false },
      { label: 'Earnings Date',      idx: 8,  required: false },
      { label: 'Market Cap',         idx: 9,  required: false },
      { label: 'Div Payment Date',   idx: 10, required: false },
      { label: 'Exchange',           idx: 11, required: false },
      { label: '52-Wk High',         idx: 12, required: false },
      { label: '52-Wk Low',          idx: 13, required: false },
      { label: 'Shares Outstanding', idx: 14, required: false },
    ];

    for (const col of colDefs) {
      const filled = await countFilledCells(page, col.idx);
      const pct = totalRows > 0 ? Math.round(filled / totalRows * 100) : 0;
      const detail = `${filled}/${totalRows} rows filled (${pct}%)`;
      if (pct >= 70)       pass(`MarketGrid: ${col.label}`, detail);
      else if (pct >= 30)  warn(`MarketGrid: ${col.label}`, detail + ' — partial');
      else                 (col.required ? fail : warn)(`MarketGrid: ${col.label}`, detail + ' — mostly blank');
    }

    // Check price source breakdown
    const srcText = await page.evaluate(() => {
      const el = document.querySelector('[title*="Polygon"]') || document.querySelector('[title*="Yahoo"]');
      return el ? el.closest('span')?.innerText ?? '' : '';
    });
    const pSrc = await page.evaluate(() => {
      const spans = Array.from(document.querySelectorAll('span'));
      const p = spans.find(s => s.textContent.includes('Polygon.io'));
      const y = spans.find(s => s.textContent.includes('Yahoo Finance'));
      return { polygon: p?.textContent?.trim() ?? '', yahoo: y?.textContent?.trim() ?? '' };
    });
    pass('Price source summary', JSON.stringify(pSrc));

    // CORS / 404
    const ce = corsErrors(errors);
    const nf = critical404s(notFound);
    ce.length ? fail('MarketGrid: no CORS errors', ce[0]) : pass('MarketGrid: no CORS errors');
    nf.length ? fail('MarketGrid: no 404s', nf.slice(0,3).join(' | ')) : pass('MarketGrid: no 404s');

    await page.screenshot({ path: 'scripts/deep_market_grid.png', fullPage: true });
  } catch (e) { fail('Market Grid check', e.message.slice(0, 120)); }
  await ctx.close();
}

// ─────────────────────────────────────────────────────────────────────────────
// 3. Momentum page
// ─────────────────────────────────────────────────────────────────────────────
async function checkMomentum(browser) {
  console.log('\n── Momentum (/momentum) ──');
  const { ctx, page, errors } = await openPage(browser);
  try {
    await nav(page, '/momentum', 'domcontentloaded');
    await page.waitForFunction(() => /\d+ stocks across/i.test(document.body.innerText), null, { timeout: 35000 });
    await page.waitForTimeout(1000);
    const body = await page.locator('body').innerText();
    const stockCountMatch = body.match(/(\d+) stocks across (\d+) GICS/i);
    stockCountMatch
      ? pass('Momentum: stocks loaded', stockCountMatch[0])
      : warn('Momentum: stocks loaded', 'stock count text not found');
    const hasSectors = /Technology|Healthcare|Energy|Financials|Consumer|Industrial/i.test(body);
    hasSectors ? pass('Momentum: sector names present') : fail('Momentum: sector names present');
    const hasScores = /momentum score|\d+\.\d+/i.test(body);
    hasScores ? pass('Momentum: momentum scores visible') : warn('Momentum: momentum scores visible', 'no scores found');
    corsErrors(errors).length ? fail('Momentum: no CORS errors') : pass('Momentum: no CORS errors');
    await page.screenshot({ path: 'scripts/deep_momentum.png', fullPage: true });
  } catch (e) { fail('Momentum check', e.message.slice(0, 120)); }
  await ctx.close();
}

// ─────────────────────────────────────────────────────────────────────────────
// 4. Sector Heat
// ─────────────────────────────────────────────────────────────────────────────
async function checkSectorHeat(browser) {
  console.log('\n── Sector Heat (/sector-heat) ──');
  const { ctx, page, errors } = await openPage(browser);
  try {
    await nav(page, '/sector-heat', 'domcontentloaded');
    await page.waitForTimeout(4000);
    const body = await page.locator('body').innerText();
    const hasSectors = /Technology|Healthcare|Energy|Financ|Consumer|Industrial/i.test(body);
    hasSectors ? pass('Sector Heat: sector blocks visible') : fail('Sector Heat: sector blocks visible');
    const hasValues = /[+-]\d+\.\d+%|XL[BCEFIKPSUVY]/i.test(body);
    hasValues ? pass('Sector Heat: ETF values/tickers present') : warn('Sector Heat: ETF values/tickers present', 'no values found');
    corsErrors(errors).length ? fail('Sector Heat: no CORS errors') : pass('Sector Heat: no CORS errors');
    await page.screenshot({ path: 'scripts/deep_sector_heat.png', fullPage: true });
  } catch (e) { fail('Sector Heat check', e.message.slice(0, 120)); }
  await ctx.close();
}

// ─────────────────────────────────────────────────────────────────────────────
// 5. Earnings page
// ─────────────────────────────────────────────────────────────────────────────
async function checkEarnings(browser) {
  console.log('\n── Earnings (/earnings) ──');
  const { ctx, page, errors } = await openPage(browser);
  try {
    await nav(page, '/earnings', 'domcontentloaded');
    await page.waitForTimeout(4000);
    const body = await page.locator('body').innerText();
    const hasEarningsData = /EPS|Revenue|Estimate|Actual|Quarter|Q\d/i.test(body);
    hasEarningsData ? pass('Earnings: data fields visible') : warn('Earnings: data fields visible', 'EPS/Revenue/Quarter labels not found');
    const hasRows = await page.evaluate(() => document.querySelectorAll('tbody tr, [data-earnings]').length > 0);
    hasRows ? pass('Earnings: table/rows present') : warn('Earnings: table/rows present', 'no rows detected');
    corsErrors(errors).length ? fail('Earnings: no CORS errors') : pass('Earnings: no CORS errors');
    await page.screenshot({ path: 'scripts/deep_earnings.png', fullPage: true });
  } catch (e) { fail('Earnings check', e.message.slice(0, 120)); }
  await ctx.close();
}

// ─────────────────────────────────────────────────────────────────────────────
// 6. Compare page
// ─────────────────────────────────────────────────────────────────────────────
async function checkCompare(browser) {
  console.log('\n── Compare (/compare) ──');
  const { ctx, page, errors } = await openPage(browser);
  try {
    await nav(page, '/compare', 'domcontentloaded');
    await page.waitForTimeout(1500);
    const inputs = await page.locator('input').all();
    if (inputs.length >= 2) {
      await inputs[0].fill('AAPL');
      await inputs[1].fill('MSFT');
      const btn = page.locator('button').filter({ hasText: /compare|run|submit/i }).first();
      if (await btn.count()) {
        await btn.click();
        await page.waitForTimeout(8000);
      }
    }
    const body = await page.locator('body').innerText();
    const hasCompareData = /P\/E|Market Cap|Revenue|Beta|Sector|EPS/i.test(body);
    hasCompareData ? pass('Compare: comparison data loaded', 'AAPL vs MSFT') : warn('Compare: comparison data loaded', 'no financial metrics found');
    corsErrors(errors).length ? fail('Compare: no CORS errors', corsErrors(errors)[0]) : pass('Compare: no CORS errors');
    await page.screenshot({ path: 'scripts/deep_compare.png', fullPage: true });
  } catch (e) { fail('Compare check', e.message.slice(0, 120)); }
  await ctx.close();
}

// ─────────────────────────────────────────────────────────────────────────────
// 7. Correlation page
// ─────────────────────────────────────────────────────────────────────────────
async function checkCorrelation(browser) {
  console.log('\n── Correlation (/correlation) ──');
  const { ctx, page, errors } = await openPage(browser);
  try {
    await nav(page, '/correlation', 'domcontentloaded');
    await page.waitForTimeout(1500);
    const inputs = await page.locator('input[type="text"], input:not([type])').all();
    if (inputs.length >= 2) {
      await inputs[0].fill('AAPL');
      await inputs[1].fill('NVDA');
      const btn = page.locator('button').filter({ hasText: /compare|correlat|run|submit/i }).first();
      if (await btn.count()) {
        await btn.click();
        await page.waitForTimeout(8000);
      }
    }
    const body = await page.locator('body').innerText();
    const hasCorr = /correlation|coefficient|0\.\d+|-0\.\d+|chart|price/i.test(body);
    hasCorr ? pass('Correlation: result data present', 'AAPL vs NVDA') : warn('Correlation: result data present', 'no correlation values found');
    corsErrors(errors).length ? fail('Correlation: no CORS errors', corsErrors(errors)[0]) : pass('Correlation: no CORS errors');
    await page.screenshot({ path: 'scripts/deep_correlation.png', fullPage: true });
  } catch (e) { fail('Correlation check', e.message.slice(0, 120)); }
  await ctx.close();
}

// ─────────────────────────────────────────────────────────────────────────────
// 8. Portfolio page
// ─────────────────────────────────────────────────────────────────────────────
async function checkPortfolio(browser) {
  console.log('\n── Portfolio (/portfolio) ──');
  const { ctx, page, errors } = await openPage(browser);
  try {
    await nav(page, '/portfolio', 'domcontentloaded');
    await page.waitForTimeout(3000);
    const body = await page.locator('body').innerText();
    const hasPortfolioUI = /portfolio|add position|total value|P&L|holdings/i.test(body);
    hasPortfolioUI ? pass('Portfolio: UI elements present') : warn('Portfolio: UI elements present', 'core UI labels not found');
    corsErrors(errors).length ? fail('Portfolio: no CORS errors', corsErrors(errors)[0]) : pass('Portfolio: no CORS errors');
    await page.screenshot({ path: 'scripts/deep_portfolio.png', fullPage: true });
  } catch (e) { fail('Portfolio check', e.message.slice(0, 120)); }
  await ctx.close();
}

// ─────────────────────────────────────────────────────────────────────────────
// 9. History page
// ─────────────────────────────────────────────────────────────────────────────
async function checkHistory(browser) {
  console.log('\n── Analysis History (/history) ──');
  const { ctx, page, errors } = await openPage(browser);
  try {
    await nav(page, '/history', 'domcontentloaded');
    await page.waitForTimeout(3000);
    const body = await page.locator('body').innerText();
    const hasHistory = /analysis|history|symbol|recommendation|BUY|SELL|HOLD/i.test(body);
    hasHistory ? pass('History: page content loaded') : warn('History: page content loaded', 'no analysis records found');
    corsErrors(errors).length ? fail('History: no CORS errors', corsErrors(errors)[0]) : pass('History: no CORS errors');
    await page.screenshot({ path: 'scripts/deep_history.png', fullPage: true });
  } catch (e) { fail('History check', e.message.slice(0, 120)); }
  await ctx.close();
}

// ─────────────────────────────────────────────────────────────────────────────
// 10. Remaining pages — Watchlists, Alerts, Logs, Settings, API Keys
// ─────────────────────────────────────────────────────────────────────────────
async function checkRemainingPages(browser) {
  const pages = [
    { path: '/watchlists', name: 'Watchlists', keywords: /watchlist|add symbol|create/i },
    { path: '/alerts',     name: 'Alerts',     keywords: /alert|notification|price|trigger/i },
    { path: '/logs',       name: 'Logs',       keywords: /log|error|agent|event|timestamp/i },
    { path: '/settings',   name: 'Settings',   keywords: /setting|preference|theme|model/i },
    { path: '/keys',       name: 'API Keys',   keywords: /api key|polygon|finnhub|anthropic/i },
  ];

  for (const { path, name, keywords } of pages) {
    console.log(`\n── ${name} (${path}) ──`);
    const { ctx, page, errors, notFound } = await openPage(browser);
    try {
      const resp = await nav(page, path, 'domcontentloaded');
      await page.waitForTimeout(2500);
      const body = await page.locator('body').innerText();
      resp.status() === 200 ? pass(`${name}: HTTP 200`) : fail(`${name}: HTTP`, String(resp.status()));
      keywords.test(body) ? pass(`${name}: content loaded`) : warn(`${name}: content loaded`, 'expected keywords not found');
      corsErrors(errors).length  ? fail(`${name}: no CORS errors`, corsErrors(errors)[0]) : pass(`${name}: no CORS errors`);
      critical404s(notFound).length ? fail(`${name}: no API 404s`, critical404s(notFound)[0]) : pass(`${name}: no API 404s`);
      await page.screenshot({ path: `scripts/deep_${path.replace('/', '')}.png`, fullPage: true });
    } catch (e) { fail(`${name} check`, e.message.slice(0, 120)); }
    await ctx.close();
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// Main
// ─────────────────────────────────────────────────────────────────────────────
async function main() {
  console.log('=== Deep UI Inspection: http://localhost:3010 ===');
  console.log('Checking data completeness on every page...\n');

  const browser = await chromium.launch({ channel: 'msedge', headless: false });
  try {
    await checkApiHealth(browser);
    await checkMarketGrid(browser);
    await checkMomentum(browser);
    await checkSectorHeat(browser);
    await checkEarnings(browser);
    await checkCompare(browser);
    await checkCorrelation(browser);
    await checkPortfolio(browser);
    await checkHistory(browser);
    await checkRemainingPages(browser);
  } finally {
    await browser.close();
  }

  // ── Summary ──
  const passed = results.filter(r => r.ok === true).length;
  const warned = results.filter(r => r.ok === 'warn').length;
  const failed = results.filter(r => r.ok === false).length;

  console.log('\n═══════════════════════════════════════');
  console.log(`SUMMARY: ${passed} passed  ${warned} warnings  ${failed} failed  (${results.length} total)`);
  console.log('═══════════════════════════════════════');
  if (warned > 0) {
    console.log('\nWarnings:');
    results.filter(r => r.ok === 'warn').forEach(r => console.log(`  ⚠️  ${r.name}: ${r.detail}`));
  }
  if (failed > 0) {
    console.log('\nFailures:');
    results.filter(r => r.ok === false).forEach(r => console.log(`  ❌ ${r.name}: ${r.detail}`));
  }
}

main().catch(e => { console.error(e); process.exit(1); });
