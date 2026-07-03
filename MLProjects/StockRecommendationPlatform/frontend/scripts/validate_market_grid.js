const { chromium } = require('@playwright/test');

async function main() {
  const browser = await chromium.launch({ channel: 'msedge', headless: false });
  const ctx = await browser.newContext({ viewport: { width: 1440, height: 900 } });
  const page = await ctx.newPage();

  const errors = [];
  page.on('console', msg => { if (msg.type() === 'error') errors.push(msg.text()); });
  page.on('pageerror', e => errors.push('PAGE ERROR: ' + e.message));
  page.on('response', resp => {
    if (!resp.ok() && resp.url().includes('stockresearch')) {
      errors.push(`HTTP ${resp.status()} ${resp.url()}`);
    }
  });

  console.log('Navigating to http://app.stockresearch.local/market-grid ...');
  const resp = await page.goto('http://app.stockresearch.local/market-grid', {
    waitUntil: 'domcontentloaded',
    timeout: 20000,
  });
  console.log(`HTTP status: ${resp.status()}`);

  await page.waitForTimeout(3000);

  const bodyText = await page.locator('body').innerText();
  const snippet = bodyText.slice(0, 800);
  console.log('\n--- Page text (first 800 chars) ---');
  console.log(snippet);

  const hasTable = await page.locator('table, [role="grid"], [role="table"]').count();
  const hasRows  = await page.locator('tr, [role="row"]').count();
  const hasError = /error|not found|404|failed/i.test(snippet);
  const hasData  = /AAPL|NVDA|MSFT|GOOG|AMZN|price|volume/i.test(snippet);

  console.log(`\n--- Checks ---`);
  console.log(`Table/grid elements: ${hasTable}`);
  console.log(`Row elements:        ${hasRows}`);
  console.log(`Has stock data:      ${hasData}`);
  console.log(`Has error text:      ${hasError}`);
  console.log(`Console errors:      ${errors.length}`);
  if (errors.length) errors.slice(0, 5).forEach(e => console.log('  ' + e));

  const ok = resp.status() === 200 && hasData && !hasError;
  console.log(`\nResult: ${ok ? '✅ PASS' : '❌ FAIL'}`);

  await page.screenshot({ path: 'scripts/market_grid_k8s.png', fullPage: false });
  console.log('Screenshot: scripts/market_grid_k8s.png');

  await browser.close();
}

main().catch(e => { console.error(e); process.exit(1); });
