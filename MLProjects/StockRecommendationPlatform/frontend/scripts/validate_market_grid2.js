const { chromium } = require('@playwright/test');

async function main() {
  const browser = await chromium.launch({ channel: 'msedge', headless: false });
  const ctx = await browser.newContext({ viewport: { width: 1440, height: 900 } });
  const page = await ctx.newPage();

  const errors = [];
  page.on('console', msg => { if (msg.type() === 'error') errors.push(msg.text()); });

  await page.goto('http://app.stockresearch.local/market-grid', { waitUntil: 'domcontentloaded', timeout: 20000 });

  console.log('Waiting for price data to appear in the table (up to 20s)...');
  try {
    await page.waitForFunction(
      () => {
        const cells = document.querySelectorAll('td');
        return cells.length > 5;
      },
      { timeout: 20000 }
    );
    console.log('✅ Table rows populated');
  } catch (e) {
    console.log('⚠️  Table still empty after 20s — checking why');
  }

  await page.waitForTimeout(2000);

  const bodyText = await page.locator('body').innerText();
  const hasPrices = /\$[\d,]+\.\d+|\d+\.\d{2}/.test(bodyText);
  const hasError = /error|failed|blocked/i.test(bodyText);
  console.log(`Has price numbers: ${hasPrices}`);
  console.log(`Has error text:    ${hasError}`);
  console.log(`Console errors:    ${errors.length}`);
  if (errors.length) errors.slice(0, 5).forEach(e => console.log('  ERR: ' + e));

  await page.screenshot({ path: 'scripts/market_grid_populated.png', fullPage: false });
  console.log('Screenshot: scripts/market_grid_populated.png');

  await browser.close();
}

main().catch(e => { console.error(e); process.exit(1); });
