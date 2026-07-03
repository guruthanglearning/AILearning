const { chromium } = require('@playwright/test');

async function main() {
  const browser = await chromium.launch({ channel: 'msedge', headless: true });
  const ctx = await browser.newContext({ viewport: { width: 1440, height: 900 } });
  const page = await ctx.newPage();

  const failed = [];
  page.on('response', resp => {
    if (resp.status() >= 400) failed.push(`HTTP ${resp.status()} ${resp.url()}`);
  });

  await page.goto('http://app.stockresearch.local/market-grid', { waitUntil: 'domcontentloaded', timeout: 20000 });
  await page.waitForFunction(() => document.querySelectorAll('td').length > 5, { timeout: 20000 });
  await page.waitForTimeout(3000);

  console.log('Failed requests:');
  failed.forEach(f => console.log(' ', f));
  await browser.close();
}

main().catch(e => { console.error(e); process.exit(1); });
