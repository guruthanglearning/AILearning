const { chromium } = require('@playwright/test');

async function main() {
  const browser = await chromium.launch({ channel: 'msedge', headless: false });
  const ctx = await browser.newContext({ viewport: { width: 1440, height: 900 } });
  const page = await ctx.newPage();

  const requests = [], responses = [];
  page.on('request',  r => { if (r.url().includes('stockresearch') || r.url().includes('localhost')) requests.push(r.url()); });
  page.on('response', r => {
    if (r.url().includes('stockresearch') || r.url().includes('localhost'))
      responses.push(`${r.status()} ${r.url()}`);
  });

  await page.goto('http://app.stockresearch.local/momentum', { waitUntil: 'domcontentloaded', timeout: 15000 });
  await page.waitForTimeout(15000);

  console.log('\nRequests made:');
  requests.forEach(u => console.log('  REQ:', u));
  console.log('\nResponses received:');
  responses.forEach(r => console.log('  RES:', r));

  const body = await page.locator('body').innerText();
  console.log('\nPage content (first 400 chars):');
  console.log(body.slice(0, 400));

  await page.screenshot({ path: 'scripts/debug_momentum2.png' });
  await ctx.close();
  await browser.close();
}

main().catch(e => { console.error(e); process.exit(1); });
