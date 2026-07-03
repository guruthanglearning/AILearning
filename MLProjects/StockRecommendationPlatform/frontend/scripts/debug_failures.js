const { chromium } = require('@playwright/test');

const BASE = 'http://app.stockresearch.local';

async function main() {
  const browser = await chromium.launch({ channel: 'msedge', headless: false });

  // --- Debug Momentum ---
  {
    const ctx = await browser.newContext({ viewport: { width: 1440, height: 900 } });
    const page = await ctx.newPage();
    const errors = [], notFound = [];
    page.on('console', m => { if (m.type() === 'error') errors.push(m.text()); });
    page.on('response', r => { if (r.status() >= 400 && r.url().includes('stockresearch')) notFound.push(`${r.status()} ${r.url()}`); });
    await page.goto(BASE + '/momentum', { waitUntil: 'domcontentloaded', timeout: 15000 });
    await page.waitForTimeout(6000);
    const body = await page.locator('body').innerText();
    console.log('=== Momentum page (first 600 chars) ===');
    console.log(body.slice(0, 600));
    console.log('Console errors:', errors);
    console.log('Not found:', notFound);
    await page.screenshot({ path: 'scripts/debug_momentum.png' });
    await ctx.close();
  }

  // --- Debug Market Grid data timeout ---
  {
    const ctx = await browser.newContext({ viewport: { width: 1440, height: 900 } });
    const page = await ctx.newPage();
    const errors = [], notFound = [];
    page.on('console', m => { if (m.type() === 'error') errors.push(m.text()); });
    page.on('response', r => { if (r.status() >= 400 && r.url().includes('stockresearch')) notFound.push(`${r.status()} ${r.url()}`); });
    await page.goto(BASE + '/market-grid', { waitUntil: 'domcontentloaded', timeout: 15000 });
    await page.waitForTimeout(8000);
    const tdCount = await page.locator('td').count();
    const body = await page.locator('body').innerText();
    console.log('\n=== Market Grid — td count:', tdCount);
    console.log('Body snippet (100 chars):', body.slice(0, 100));
    console.log('Console errors:', errors.slice(0, 3));
    console.log('Not found:', notFound.slice(0, 3));
    await page.screenshot({ path: 'scripts/debug_market_grid.png' });
    await ctx.close();
  }

  await browser.close();
}

main().catch(e => { console.error(e); process.exit(1); });
