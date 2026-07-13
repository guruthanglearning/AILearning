const { chromium } = require('@playwright/test');
(async () => {
  const browser = await chromium.launch({ channel: 'msedge', headless: true });
  const ctx = await browser.newContext({ viewport: { width: 1440, height: 900 } });
  const page = await ctx.newPage();

  await page.goto('http://localhost:3010/earnings', { waitUntil: 'domcontentloaded' });

  // Wait for either: upcoming earnings header, no-data message, or error
  try {
    await page.waitForFunction(
      () => {
        const text = document.body.innerText;
        return text.includes('Upcoming Earnings') || text.includes('No earnings dates') || text.includes('No upcoming earnings') || text.includes('Failed to load');
      },
      null, { timeout: 20000 }
    );
  } catch (e) {
    console.log('⚠️  Timed out waiting for earnings content');
  }

  await page.waitForTimeout(500);

  const content = await page.evaluate(() => {
    const body = document.body.innerText;
    const cards = document.querySelectorAll('.grid > div').length;
    const sections = Array.from(document.querySelectorAll('h2')).map(h => h.innerText);
    return { body: body.slice(0, 1000), cards, sections };
  });

  console.log('Sections found:', content.sections);
  console.log('Symbol cards found:', content.cards);
  console.log('\nPage text (first 1000 chars):');
  console.log(content.body);

  await page.screenshot({ path: 'scripts/earnings_check.png', fullPage: false });
  await browser.close();
  console.log('\nDone. Screenshot saved.');
})().catch(e => { console.error('Error:', e.message); process.exit(1); });
