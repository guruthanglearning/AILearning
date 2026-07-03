const { chromium } = require('@playwright/test');

async function main() {
  const browser = await chromium.launch({ channel: 'msedge', headless: false });
  const ctx = await browser.newContext({ viewport: { width: 1280, height: 900 } });
  const page = await ctx.newPage();

  console.log('Navigating to home page...');
  await page.goto('http://localhost:3010/', { waitUntil: 'networkidle', timeout: 15000 });
  await page.waitForTimeout(1500);

  const textInput = page.locator('input').first();
  await textInput.fill('AAPL');

  const analyzeBtn = page.locator('button:has-text("Run Analysis")');
  await analyzeBtn.click();
  console.log('Clicked Run Analysis for AAPL — waiting up to 180s for verdict...');

  const start = Date.now();
  try {
    await page.waitForFunction(
      () => document.body.innerText.match(/BUY|SELL|HOLD|Verdict|verdict|STRONG/i),
      { timeout: 180000 }
    );
    const elapsed = ((Date.now() - start) / 1000).toFixed(1);
    console.log(`✅ Analysis verdict appeared in ${elapsed}s`);
    await page.screenshot({ path: 'scripts/analysis_result.png', fullPage: false });
    console.log('Screenshot: scripts/analysis_result.png');

    const bodyText = await page.locator('body').innerText();
    const match = bodyText.match(/\b(STRONG BUY|BUY|SELL|STRONG SELL|HOLD)\b/i);
    if (match) console.log(`   Verdict: ${match[0].toUpperCase()}`);
  } catch (e) {
    const elapsed = ((Date.now() - start) / 1000).toFixed(1);
    const snippet = (await page.locator('body').innerText()).slice(0, 600);
    console.log(`❌ Verdict not found after ${elapsed}s. Page content:\n${snippet}`);
    await page.screenshot({ path: 'scripts/analysis_fail.png', fullPage: false });
  }

  await browser.close();
}

main().catch(e => { console.error(e); process.exit(1); });
